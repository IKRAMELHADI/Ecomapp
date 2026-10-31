import csv
from pathlib import Path
from decimal import Decimal
from collections import defaultdict

DATA_DIR = Path("data/raw/olist")

items_totals = defaultdict(lambda: Decimal("0.00"))
payments_totals = defaultdict(lambda: Decimal("0.00"))

# 1. Calculer le montant des articles et des livraisons
with (DATA_DIR / "olist_order_items_dataset.csv").open(
    encoding="utf-8-sig", newline=""
) as file:

    for row in csv.DictReader(file):
        order_id = row["order_id"]

        price = Decimal(row["price"])
        freight = Decimal(row["freight_value"])

        items_totals[order_id] += price + freight


# 2. Calculer le montant des paiements
with (DATA_DIR / "olist_order_payments_dataset.csv").open(
    encoding="utf-8-sig", newline=""
) as file:

    for row in csv.DictReader(file):
        order_id = row["order_id"]

        payment = Decimal(row["payment_value"])

        payments_totals[order_id] += payment


# 3. Comparer les montants
all_orders = set(items_totals) | set(payments_totals)

matching = 0
different = 0
missing_items = 0
missing_payments = 0

examples = []

for order_id in all_orders:

    if order_id not in items_totals:
        missing_items += 1
        continue

    if order_id not in payments_totals:
        missing_payments += 1
        continue

    items_amount = items_totals[order_id]
    payment_amount = payments_totals[order_id]

    difference = payment_amount - items_amount

    if abs(difference) <= Decimal("0.01"):
        matching += 1
    else:
        different += 1

        if len(examples) < 5:
            examples.append(
                (order_id, items_amount, payment_amount, difference)
            )


print("=== VALIDATION FINANCIERE OLIST ===")

print(f"Commandes avec articles ou paiements : {len(all_orders)}")
print(f"Montants correspondants : {matching}")
print(f"Montants differents : {different}")
print(f"Commandes sans articles : {missing_items}")
print(f"Commandes sans paiements : {missing_payments}")

print("\nExemples d'ecarts :")

for order_id, items, payments, difference in examples:
    print(
        f"Commande : {order_id} | "
        f"Articles + livraison : {items} BRL | "
        f"Paiements : {payments} BRL | "
        f"Ecart : {difference} BRL"
    )