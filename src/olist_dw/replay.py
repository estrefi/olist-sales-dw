"""Daily replay: pretend to be Olist's shop system exporting one business day.

For a business date D, the replay writes what the shop would have exported
that night:

- orders:      every order with an event on D (placed, approved, handed to the
               carrier or delivered), as it looked at the end of D: later
               timestamps blank and the status matching the latest event
- order_items, payments, customers: for orders placed on D
- reviews:     reviews created on D
- reference tables (products, sellers, ...): only on the first business date
               or with --reference

Files land in <landing>/<table>/business_date=YYYY-MM-DD/part.jsonl.
Re-running a date replaces that date's folders, so the result is the same
(idempotent).

Usage:
    python -m olist_dw.replay --date 2017-03-01
    python -m olist_dw.replay --start 2017-01-01 --end 2017-01-31
"""

from __future__ import annotations

import argparse
import shutil
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from olist_dw.config import (
    DAILY_TABLES,
    DATE_COLUMNS,
    FILES,
    FIRST_BUSINESS_DATE,
    LANDING_DIR,
    ORDER_EVENTS,
    REFERENCE_TABLES,
    SOURCE_DIR,
)

# Final statuses that are set by the timestamps themselves; any other final
# status (canceled, unavailable, invoiced, ...) is applied on the last event day
_TIMESTAMP_STATUSES = {"created", "approved", "shipped", "delivered"}


# ---------------------------------------------------------------- loading


def load_source(source_dir: Path, tables: tuple[str, ...]) -> dict[str, pd.DataFrame]:
    """Read the requested CSVs and turn their text date columns into timestamps."""
    data = {}
    for table in tables:
        df = pd.read_csv(Path(source_dir) / FILES[table])
        for col in DATE_COLUMNS.get(table, []):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        data[table] = df
    return data


# ---------------------------------------------------------------- selecting


def _on_day(series: pd.Series, day: date) -> pd.Series:
    """True where a timestamp falls on the given calendar day."""
    return series.dt.date == day


def orders_placed_on(orders: pd.DataFrame, day: date) -> pd.DataFrame:
    return orders[_on_day(orders["order_purchase_timestamp"], day)]


def orders_as_of(orders: pd.DataFrame, day: date) -> pd.DataFrame:
    """Orders with any lifecycle event on `day`, as they looked at the end of it."""
    event_cols = [col for col, _ in ORDER_EVENTS]
    has_event = pd.concat([_on_day(orders[c], day) for c in event_cols], axis=1).any(
        axis=1
    )
    snap = orders[has_event].copy()
    if snap.empty:
        return snap

    end_of_day = pd.Timestamp(day) + pd.Timedelta(days=1)

    # Hide what hadn't happened yet. The estimated delivery date is known at
    # purchase, so it stays.
    for col in event_cols:
        snap.loc[snap[col] >= end_of_day, col] = pd.NaT

    # Status from the latest event that has happened (by lifecycle step, which
    # also handles orders whose timestamps are out of order in the source)
    status = pd.Series("created", index=snap.index)
    for col, step_status in ORDER_EVENTS:
        status = status.mask(snap[col].notna(), step_status)

    # Final statuses not expressed by timestamps (canceled, unavailable, ...)
    # apply from the order's last known event onwards
    last_event = orders.loc[snap.index, event_cols].max(axis=1)
    final = snap["order_status"]
    apply_final = (~final.isin(_TIMESTAMP_STATUSES)) & (last_event < end_of_day)
    status = status.mask(apply_final, final)

    snap["order_status"] = status
    return snap


def rows_for_date(data: dict[str, pd.DataFrame], day: date) -> dict[str, pd.DataFrame]:
    """Everything the shop exports for one business day."""
    orders = data["orders"]
    placed = orders_placed_on(orders, day)
    placed_ids = set(placed["order_id"])

    out = {
        "orders": orders_as_of(orders, day),
        "order_items": data["order_items"][
            data["order_items"]["order_id"].isin(placed_ids)
        ],
        "payments": data["payments"][data["payments"]["order_id"].isin(placed_ids)],
        "customers": data["customers"][
            data["customers"]["customer_id"].isin(set(placed["customer_id"]))
        ],
        "reviews": data["reviews"][
            _on_day(data["reviews"]["review_creation_date"], day)
        ],
    }
    for table in REFERENCE_TABLES:
        if table in data:
            out[table] = data[table]
    return out


# ---------------------------------------------------------------- writing


def write_day(
    rows: dict[str, pd.DataFrame], day: date, landing_dir: Path
) -> dict[str, int]:
    """Write each table's rows to its dated folder, replacing any earlier run."""
    counts = {}
    for table, df in rows.items():
        folder = Path(landing_dir) / table / f"business_date={day.isoformat()}"
        if folder.exists():
            shutil.rmtree(folder)  # idempotent: same date, same result
        if df.empty:
            counts[table] = 0
            continue
        folder.mkdir(parents=True)
        df.to_json(
            folder / "part.jsonl", orient="records", lines=True, date_format="iso"
        )
        counts[table] = len(df)
    return counts


def replay(
    start: date,
    end: date,
    source_dir: Path = SOURCE_DIR,
    landing_dir: Path = LANDING_DIR,
    reference: bool | None = None,
) -> None:
    """Replay every business date from start to end (inclusive).

    Reference tables go out once: on the first day of the range when
    `reference` is True, or automatically on FIRST_BUSINESS_DATE.
    """
    reference_day = start if reference else FIRST_BUSINESS_DATE
    send_reference = start <= reference_day <= end
    tables = DAILY_TABLES + (REFERENCE_TABLES if send_reference else ())
    data = load_source(source_dir, tables)
    daily_only = {t: df for t, df in data.items() if t not in REFERENCE_TABLES}

    day = start
    while day <= end:
        day_data = data if (send_reference and day == reference_day) else daily_only
        counts = write_day(rows_for_date(day_data, day), day, landing_dir)
        summary = ", ".join(f"{t} {n}" for t, n in counts.items() if n)
        print(f"{day}: {summary or 'no activity'}")
        day += timedelta(days=1)


# ---------------------------------------------------------------- command line


def _parse_date(text: str) -> date:
    return date.fromisoformat(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replay Olist business days into a landing folder."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--date", type=_parse_date, help="one business date, YYYY-MM-DD")
    group.add_argument(
        "--start", type=_parse_date, help="first date of a range, YYYY-MM-DD"
    )
    parser.add_argument(
        "--end", type=_parse_date, help="last date of a range (with --start)"
    )
    parser.add_argument(
        "--source", type=Path, default=SOURCE_DIR, help="folder with the Olist CSVs"
    )
    parser.add_argument(
        "--landing", type=Path, default=LANDING_DIR, help="output folder"
    )
    parser.add_argument(
        "--reference",
        action="store_true",
        default=None,
        help="also send products, sellers, categories and geolocation",
    )
    args = parser.parse_args()

    if args.date:
        start = end = args.date
    else:
        if not args.end:
            parser.error("--start needs --end")
        start, end = args.start, args.end
        if end < start:
            parser.error("--end must not be before --start")

    replay(start, end, args.source, args.landing, args.reference)


if __name__ == "__main__":
    main()
