# PG-T06 — Preuves C1.1 / EC1

Exécution UTC : 2026-11-13T20:34:03.279749+00:00
Instance : `validation-pg-t06-a26c4fb21f` ; base et propriétaire : `aquasave` ; port : `62418`.
Stockage : tmpfs indépendant, supprimé avec le conteneur. Aucun volume existant monté.

Prérequis : Docker, image postgres:16, client psql comprenant les commandes \restrict/\unrestrict ; rôle aquasave propriétaire/créateur des objets et capable de créer les rôles techniques. Les mots de passe ne sont pas fournis par 03. Exécuter 00 → 03 → 05 sur une base vide avant insertion. 05 détruit et recrée orders.orders et orders.order_items. Les privilèges par défaut de 03 concernent les objets créés par aquasave.

Compose utilise des variables POSTGRES_DB/USER/PASSWORD, le port 5433 et le volume postgres_data. Aucune de ces ressources n'a été utilisée pour les tests. .env uniquement haché pour contrôle d'intégrité.

Chaque fichier .log contient la commande exacte (SQL inclus), le résultat attendu, stdout/stderr, SQLSTATE et statut. Les rejets attendus ont un code psql 3 et le SQLSTATE/la contrainte attendus ; ils sont classés OK, sans masquer les erreurs inattendues.

| Vérification | Attendu | Statut | Nature |
|---|---|---|---|
| [01-instance](01-instance.log) | Nouveau conteneur PostgreSQL 16, port localhost attribué par Docker, stockage tmpfs distinct | OK | vérification |
| [02-isolation](02-isolation.log) | Stockage tmpfs et port lié uniquement à 127.0.0.1 | OK | vérification |
| [03-version-owner](03-version-owner.log) | aquasave/aquasave/aquasave/16.x | OK | vérification |
| [04-00_schema_snapshot.sql](04-00_schema_snapshot.sql.log) | Code 0, script intégral appliqué sans modification avant toute donnée métier | OK | vérification |
| [05-03_create_roles.sql](05-03_create_roles.sql.log) | Code 0, script intégral appliqué sans modification avant toute donnée métier | OK | vérification |
| [06-05_partitioning.sql](06-05_partitioning.sql.log) | Code 0, script intégral appliqué sans modification avant toute donnée métier | OK | vérification |
| [07-schemas](07-schemas.log) | Exactement quatre schémas métier | OK | vérification |
| [08-tables](08-tables.log) | Exactement dix tables métier hors partitions | OK | vérification |
| [09-partitions](09-partitions.log) | 25 partitions dont une DEFAULT (24 mois 2026-2027) | OK | vérification |
| [10-stock-valid](10-stock-valid.log) | Entrepôt et stock acceptés : 101/1/10/2 | OK | vérification |
| [11-negative-quantity](11-negative-quantity.log) | Rejet CHECK 23514 stock_quantity_check | OK | rejet attendu |
| [12-reserved-too-high](12-reserved-too-high.log) | Rejet CHECK 23514 chk_reserved_quantity | OK | rejet attendu |
| [13-unknown-warehouse](13-unknown-warehouse.log) | Rejet FK 23503 fk_stock_warehouse | OK | rejet attendu |
| [14-temporary-login](14-temporary-login.log) | Mot de passe temporaire installé sans journalisation du secret | OK | vérification |
| [15-auth-method](15-auth-method.log) | Toutes les règles TCP utilisent scram-sha-256 | OK | vérification |
| [16-inventory-read](16-inventory-read.log) | Connexion TCP réelle inventory_service ; stock lisible 101/1/10/2 | OK | vérification |
| [17-payments-denied](17-payments-denied.log) | Rejet privilèges 42501 permission denied for schema payments | OK | rejet attendu |
| [18-orders-routing](18-orders-routing.log) | 201801/orders.orders_default et 202601/orders.orders_2026_06 | OK | vérification |
| [19-item-valid](19-item-valid.log) | Article accepté pour le couple (202601, 2026-06-15 12:00:00+00) | OK | vérification |
| [20-item-wrong-date](20-item-wrong-date.log) | Rejet FK composite 23503 fk_order_items_order | OK | rejet attendu |
| [21-final-data](21-final-data.log) | 1/1/2/1 : aucune insertion invalide persistée | OK | vérification |
| [22-revoke-test-login](22-revoke-test-login.log) | Identifiants temporaires révoqués | OK | vérification |
| [23-cleanup](23-cleanup.log) | Seul le conteneur de test supprimé ; stockage tmpfs libéré | OK | vérification |
| [24-source-integrity](24-source-integrity.log) | Tous les fichiers protégés inchangés | OK | vérification |

INV-01 : OUI, prérequis PostgreSQL Inventory validés sur cette instance isolée.
PG-T06 : peut passer en Terminé pour le périmètre demandé.
Les identifiants temporaires ont été révoqués et l'instance supprimée. Pour INV-01, provisionner un nouveau secret inventory_service sur la base de développement reconstruite ; aucune validation de la base existante n'est revendiquée.
Hors périmètre : backend Spring Boot, tests de charge, évaluation des index et restauration. Aucun commit/push.
