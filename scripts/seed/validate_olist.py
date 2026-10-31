import csv
from pathlib import Path

DATA_DIR = Path("data/raw/olist")


def load_ids(filename, column):
    with (DATA_DIR / filename).open(
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return {
            row[column]
            for row in csv.DictReader(file)
        }


def check_relationship(
    source_file,
    source_column,
    target_ids
):
    total = 0
    invalid = 0

    with (DATA_DIR / source_file).open(
        encoding="utf-8-sig",
        newline=""
    ) as file:

        for row in csv.DictReader(file):
            total += 1

            if row[source_column] not in target_ids:
                invalid += 1

    print(f"\nRelation : {source_file}")
    print(f"Nombre de lignes : {total}")
    print(f"Références inexistantes : {invalid}")


customers = load_ids(
    "olist_customers_dataset.csv",
    "customer_id"
)

orders = load_ids(
    "olist_orders_dataset.csv",
    "order_id"
)

products = load_ids(
    "olist_products_dataset.csv",
    "product_id"
)

print("=== VALIDATION DES RELATIONS OLIST ===")

check_relationship(
    "olist_orders_dataset.csv",
    "customer_id",
    customers
)

check_relationship(
    "olist_order_items_dataset.csv",
    "order_id",
    orders
)

check_relationship(
    "olist_order_items_dataset.csv",
    "product_id",
    products
)

check_relationship(
    "olist_order_payments_dataset.csv",
    "order_id",
    orders
)