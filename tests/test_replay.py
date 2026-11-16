"""Tests for the daily replay, using tiny hand-made tables (no real CSVs)."""

from datetime import date

import pandas as pd

from olist_dw.replay import orders_as_of, rows_for_date, write_day

TS = pd.Timestamp


def make_data() -> dict[str, pd.DataFrame]:
    orders = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "customer_id": ["c1", "c2", "c3"],
            "order_status": ["delivered", "canceled", "delivered"],
            "order_purchase_timestamp": [
                TS("2017-03-01 10:00"),
                TS("2017-03-01 11:00"),
                TS("2017-02-20 09:00"),
            ],
            "order_approved_at": [
                TS("2017-03-01 12:00"),
                pd.NaT,
                TS("2017-02-20 10:00"),
            ],
            "order_delivered_carrier_date": [
                TS("2017-03-03 08:00"),
                pd.NaT,
                TS("2017-02-25 08:00"),
            ],
            "order_delivered_customer_date": [
                TS("2017-03-10 15:00"),
                pd.NaT,
                TS("2017-03-01 16:00"),
            ],
            "order_estimated_delivery_date": [
                TS("2017-03-20"),
                TS("2017-03-15"),
                TS("2017-03-05"),
            ],
        }
    )
    return {
        "orders": orders,
        "order_items": pd.DataFrame(
            {
                "order_id": ["o1", "o1", "o3"],
                "order_item_id": [1, 2, 1],
                "price": [10.0, 5.0, 20.0],
            }
        ),
        "payments": pd.DataFrame(
            {"order_id": ["o1", "o2", "o3"], "payment_value": [15.0, 8.0, 20.0]}
        ),
        "customers": pd.DataFrame(
            {
                "customer_id": ["c1", "c2", "c3"],
                "customer_unique_id": ["p1", "p2", "p1"],
            }
        ),
        "reviews": pd.DataFrame(
            {
                "review_id": ["r3"],
                "order_id": ["o3"],
                "review_score": [5],
                "review_creation_date": [TS("2017-03-01 00:00")],
            }
        ),
    }


def test_new_orders_and_their_details_arrive_on_purchase_day():
    rows = rows_for_date(make_data(), date(2017, 3, 1))
    assert set(rows["order_items"]["order_id"]) == {"o1"}
    assert set(rows["payments"]["order_id"]) == {"o1", "o2"}
    assert set(rows["customers"]["customer_id"]) == {"c1", "c2"}


def test_order_is_sent_as_it_looked_that_day():
    snap = orders_as_of(make_data()["orders"], date(2017, 3, 1)).set_index("order_id")
    # o1 was placed and approved that day; shipping and delivery hadn't happened yet
    assert snap.loc["o1", "order_status"] == "approved"
    assert pd.isna(snap.loc["o1", "order_delivered_carrier_date"])
    assert pd.isna(snap.loc["o1", "order_delivered_customer_date"])
    # the estimated delivery date is known at purchase, so it stays
    assert snap.loc["o1", "order_estimated_delivery_date"] == TS("2017-03-20")


def test_older_order_arrives_again_when_delivered():
    snap = orders_as_of(make_data()["orders"], date(2017, 3, 1)).set_index("order_id")
    assert snap.loc["o3", "order_status"] == "delivered"


def test_final_status_applies_from_last_event():
    snap = orders_as_of(make_data()["orders"], date(2017, 3, 1)).set_index("order_id")
    assert snap.loc["o2", "order_status"] == "canceled"


def test_day_without_events_sends_nothing():
    snap = orders_as_of(make_data()["orders"], date(2017, 3, 5))
    assert snap.empty


def test_reviews_arrive_on_creation_day():
    rows = rows_for_date(make_data(), date(2017, 3, 1))
    assert list(rows["reviews"]["review_id"]) == ["r3"]


def test_writing_the_same_day_twice_gives_the_same_files(tmp_path):
    day = date(2017, 3, 1)
    rows = rows_for_date(make_data(), day)
    write_day(rows, day, tmp_path)
    first = (
        tmp_path / "orders" / "business_date=2017-03-01" / "part.jsonl"
    ).read_text()
    write_day(rows, day, tmp_path)
    second = (
        tmp_path / "orders" / "business_date=2017-03-01" / "part.jsonl"
    ).read_text()
    assert first == second
    assert len(first.strip().splitlines()) == 3  # o1, o2 and o3
