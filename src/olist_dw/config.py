"""Settings for the Olist replay: where files live and how each table arrives."""

from __future__ import annotations

from datetime import date
from pathlib import Path

# Folders, relative to the project root (override with --source / --landing)
SOURCE_DIR = Path("data/olist")
LANDING_DIR = Path("data/landing")

# The shop "goes live" here. Sep-Dec 2016 is thin: replay it as history if needed.
FIRST_BUSINESS_DATE = date(2017, 1, 1)

# Source CSV for each table
FILES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
    "geolocation": "olist_geolocation_dataset.csv",
}

# All date columns are stored as text in the CSVs; these get parsed on load
DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

# Tables that arrive every day, based on what happened that day
DAILY_TABLES = ("orders", "order_items", "payments", "customers", "reviews")

# Reference tables: sent once (on the first business date, or with --reference)
REFERENCE_TABLES = ("products", "sellers", "category_translation", "geolocation")

# Order lifecycle events, in the order they normally happen, with the status
# an order has once that event has happened
ORDER_EVENTS = [
    ("order_purchase_timestamp", "created"),
    ("order_approved_at", "approved"),
    ("order_delivered_carrier_date", "shipped"),
    ("order_delivered_customer_date", "delivered"),
]
