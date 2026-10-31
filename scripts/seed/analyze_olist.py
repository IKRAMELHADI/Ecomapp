import csv
from pathlib import Path
from collections import Counter

DATA_DIR = Path("data/raw/olist")

FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_products_dataset.csv",
]

for filename in FILES:

    path = DATA_DIR / filename

    print(f"\n{'=' * 60}")
    print(f"FICHIER : {filename}")
    print(f"{'=' * 60}")

    missing = Counter()
    total_rows = 0

    with path.open(encoding="utf-8-sig", newline="") as file:

        reader = csv.DictReader(file)

        columns = reader.fieldnames

        for row in reader:
            total_rows += 1

            for column in columns:
                if row[column] is None or row[column].strip() == "":
                    missing[column] += 1

    print(f"Nombre de lignes : {total_rows}")

    print("\nValeurs manquantes par colonne :")

    for column in columns:

        count = missing[column]

        percentage = (
            count / total_rows * 100
            if total_rows > 0
            else 0
        )

        print(
            f"{column:40} "
            f"{count:8} "
            f"({percentage:.2f} %)"
        )