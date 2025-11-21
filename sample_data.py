# sample_data.py
"""Insert sample orders into the configured database.

This script uses the same `create_order` function so it will work for both
local SQLite and Supabase as long as `DATABASE_URL` is configured.
"""
from crud import create_order

SAMPLES = [
    ("Alice", "Margherita Pizza", "+15550001111"),
    ("Bob", "Cheeseburger", "+15550002222"),
    ("Carol", "Caesar Salad", "+15550003333"),
]


def insert_samples():
    for name, item, phone in SAMPLES:
        order = create_order(name, item, phone)
        print(f"Inserted order id={order.id} name={order.name} item={order.item}")


if __name__ == "__main__":
    insert_samples()
