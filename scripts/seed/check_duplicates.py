import csv
from pathlib import Path

DATA_DIR = Path("data/raw/olist")

CHECKS = [
    ("olist_customers_dataset.csv", ["customer_id"]),
    ("olist_orders_dataset.csv", ["order_id"]),
    ("olist_products_dataset.csv", ["product_id"]),
    ("olist_order_items_dataset.csv", ["order_id", "order_item_id"]),
    ("olist_order_payments_dataset.csv", ["order_id", "payment_sequential"]),
]

for filename, columns in CHECKS:

    seen = set()
    duplicates = 0
    total = 0

    with (DATA_DIR / filename).open(
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:
            total += 1

            key = tuple(row[column] for column in columns)

            if key in seen:
                duplicates += 1
            else:
                seen.add(key)

    print(f"\nFichier : {filename}")
    print(f"Clé vérifiée : {', '.join(columns)}")
    print(f"Nombre de lignes : {total}")
    print(f"Clés distinctes : {len(seen)}")
    print(f"Lignes avec clé dupliquée : {duplicates}")