import csv
from pathlib import Path
from collections import Counter

DATA_DIR = Path("data/raw/olist")

# Identifiants des commandes possédant des articles
with (DATA_DIR / "olist_order_items_dataset.csv").open(
    encoding="utf-8-sig",
    newline=""
) as file:

    orders_with_items = {
        row["order_id"]
        for row in csv.DictReader(file)
    }

# Statuts des commandes sans articles
status_counts = Counter()

with (DATA_DIR / "olist_orders_dataset.csv").open(
    encoding="utf-8-sig",
    newline=""
) as file:

    for row in csv.DictReader(file):

        if row["order_id"] not in orders_with_items:
            status_counts[row["order_status"]] += 1

print("=== STATUTS DES COMMANDES SANS ARTICLES ===")

for status, count in status_counts.most_common():
    print(f"{status:20} : {count}")

print(f"\nTotal : {sum(status_counts.values())}")