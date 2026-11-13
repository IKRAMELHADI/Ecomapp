"""PG-T06: disposable PostgreSQL 16 validation. No existing database is contacted.

Run from the repository: python artifacts/validation/PG-T06/validate.py
Requires Docker Desktop and host psql. Passwords exist only in process memory.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
RUN = OUT / ("run-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
RUN.mkdir(parents=True, exist_ok=False)
NAME = "validation-pg-t06-" + secrets.token_hex(5)
SECRET = secrets.token_urlsafe(32)
ADMIN_SECRET = secrets.token_urlsafe(32)
PSQL = shutil.which("psql")
RESULTS = []
PROTECTED = ["docker-compose.yml", ".env", "database/postgres/00_schema_snapshot.sql",
             "database/postgres/03_create_roles.sql", "database/postgres/05_partitioning.sql"]
BEFORE = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in PROTECTED}
META = {"started_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "container": NAME,
        "storage": "tmpfs /var/lib/postgresql/data: no project volume or bind mount",
        "hashes_before": BEFORE}


def redact(value):
    return value.replace(SECRET, "<secret temporaire masqué>").replace(ADMIN_SECRET, "<secret temporaire masqué>")


def execute(args, data=None, env=None):
    p = subprocess.run(args, input=data, text=True, encoding="utf-8", errors="replace",
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=ROOT)
    return p.returncode, redact(p.stdout), redact(p.stderr)


def record(key, command, expected, result, ok, kind="vérification"):
    code, stdout, stderr = result
    row = dict(id=key, commande=command, attendu=expected, code_retour=code,
               observe=stdout, erreur=stderr, statut="OK" if ok else "ÉCHEC", nature=kind)
    RESULTS.append(row)
    (RUN / (key + ".log")).write_text(
        f"Commande: {command}\nAttendu: {expected}\nCode: {code}\nStatut: {row['statut']}\n"
        f"Nature: {kind}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}", encoding="utf-8")
    print(f"{key}: {row['statut']}", flush=True)
    return ok


def admin(sql):
    return execute(["docker", "exec", "-i", NAME, "psql", "-X", "-U", "aquasave", "-d", "aquasave",
                    "-v", "ON_ERROR_STOP=1", "-v", "VERBOSITY=verbose", "-A", "-t"], sql)


def check(key, sql, expected, predicate=None, reject=None, service=False):
    if service:
        env = os.environ.copy()
        env["PGPASSWORD"] = SECRET
        env["PGSSLMODE"] = "disable"
        args = [PSQL, "-X", "-h", "127.0.0.1", "-p", str(META["port"]), "-U", "inventory_service",
                "-d", "aquasave", "-v", "ON_ERROR_STOP=1", "-v", "VERBOSITY=verbose", "-A", "-t"]
        result = execute(args, sql, env)
        command = f"psql -X -h 127.0.0.1 -p {META['port']} -U inventory_service -d aquasave -v ON_ERROR_STOP=1 -v VERBOSITY=verbose -A -t < SQL (PGPASSWORD en mémoire)\n{sql}"
    else:
        result = admin(sql)
        command = f"docker exec -i {NAME} psql -X -U aquasave -d aquasave -v ON_ERROR_STOP=1 -v VERBOSITY=verbose -A -t < SQL\n{sql}"
    ok = (result[0] == 3 and all(s in result[2] for s in reject)) if reject else (
        result[0] == 0 and (predicate(result[1].strip()) if predicate else True))
    record(key, command, expected, result, ok, "rejet attendu" if reject else "vérification")
    return ok


created = False
try:
    if not PSQL:
        raise RuntimeError("Host psql not available")
    rc, stdout, stderr = execute(["docker", "ps", "-a", "--format", "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"])
    (RUN / "docker-before.txt").write_text(stdout + stderr, encoding="utf-8")
    if rc:
        raise RuntimeError(stderr)
    image = execute(["docker", "image", "inspect", "postgres:16", "--format", "{{.Id}}|{{json .RepoDigests}}"])
    META["image"] = image[1].strip()
    env = os.environ.copy()
    env["POSTGRES_PASSWORD"] = ADMIN_SECRET
    args = ["docker", "run", "-d", "--name", NAME, "--label", "purpose=validation-pg-t06",
            "--mount", "type=tmpfs,destination=/var/lib/postgresql/data,tmpfs-size=536870912",
            "-p", "127.0.0.1::5432", "-e", "POSTGRES_DB=aquasave", "-e", "POSTGRES_USER=aquasave",
            "-e", "POSTGRES_PASSWORD", "-e", "POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256",
            "postgres:16", "-c", "log_statement=none", "-c", "log_min_error_statement=panic"]
    result = execute(args, env=env)
    if not record("01-instance", " ".join(args) + " (POSTGRES_PASSWORD généré en mémoire)",
                  "Nouveau conteneur PostgreSQL 16, port localhost attribué par Docker, stockage tmpfs distinct", result, result[0] == 0):
        raise RuntimeError("Cannot create isolated container")
    created = True
    for _ in range(45):
        ready = execute(["docker", "exec", NAME, "pg_isready", "-U", "aquasave", "-d", "aquasave"])
        if ready[0] == 0:
            # pg_isready may see the temporary initialization server. Wait for host port.
            port = execute(["docker", "port", NAME, "5432/tcp"])[1].strip()
            META["port"] = int(port.rsplit(":", 1)[1])
            tcp = execute(["docker", "exec", NAME, "pg_isready", "-h", "127.0.0.1", "-U", "aquasave", "-d", "aquasave"])
            if tcp[0] == 0:
                break
        time.sleep(1)
    else:
        raise RuntimeError("PostgreSQL not ready after 45 seconds")
    inspect = execute(["docker", "inspect", NAME, "--format", "{{json .Mounts}}|{{json .NetworkSettings.Ports}}"])
    record("02-isolation", f"docker inspect {NAME} --format '{{{{json .Mounts}}}}|{{{{json .NetworkSettings.Ports}}}}'",
           "Stockage tmpfs et port lié uniquement à 127.0.0.1", inspect,
           inspect[0] == 0 and '"Type":"tmpfs"' in inspect[1] and '"HostIp":"127.0.0.1"' in inspect[1])
    check("03-version-owner", "SELECT current_database(), current_user, pg_get_userbyid(datdba), current_setting('server_version') FROM pg_database WHERE datname=current_database();",
          "aquasave|aquasave|aquasave|16.x", lambda s: s.startswith("aquasave|aquasave|aquasave|16."))
    for number, filename in [("04", "00_schema_snapshot.sql"), ("05", "03_create_roles.sql"), ("06", "05_partitioning.sql")]:
        sql = (ROOT / "database/postgres" / filename).read_text(encoding="utf-8")
        result = admin(sql)
        if not record(number + "-" + filename, f"docker exec -i {NAME} psql -X -U aquasave -d aquasave -v ON_ERROR_STOP=1 -v VERBOSITY=verbose -A -t < database/postgres/{filename}",
                      "Code 0, script intégral appliqué sans modification avant toute donnée métier", result, result[0] == 0):
            raise RuntimeError(f"Script failed: database/postgres/{filename}; see exact error in log")
    schemas = ["auth", "inventory", "orders", "payments"]
    tables = ["auth.roles", "auth.user_roles", "auth.users", "inventory.stock", "inventory.stock_reservations",
              "inventory.warehouses", "orders.customers", "orders.order_items", "orders.orders", "payments.payments"]
    check("07-schemas", "SELECT nspname FROM pg_namespace WHERE nspname IN ('auth','inventory','orders','payments') ORDER BY 1;",
          "Exactement quatre schémas métier", lambda s: s.splitlines() == schemas)
    check("08-tables", "SELECT n.nspname || '.' || c.relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('auth','inventory','orders','payments') AND c.relkind IN ('r','p') AND NOT c.relispartition ORDER BY 1;",
          "Exactement dix tables métier hors partitions", lambda s: s.splitlines() == tables)
    check("09-partitions", "SELECT count(*), count(*) FILTER (WHERE pg_get_expr(c.relpartbound,c.oid)='DEFAULT') FROM pg_inherits i JOIN pg_class c ON c.oid=i.inhrelid WHERE i.inhparent='orders.orders'::regclass;",
          "25 partitions dont une DEFAULT (24 mois 2026-2027)", lambda s: s == "25|1")
    check("10-stock-valid", "INSERT INTO inventory.warehouses(id,name,capacity_units) VALUES (1,'PG-T06 test',100);\nINSERT INTO inventory.stock(product_id,warehouse_id,quantity,reserved_quantity) VALUES (101,1,10,2);\nSELECT product_id,warehouse_id,quantity,reserved_quantity FROM inventory.stock;",
          "Entrepôt et stock acceptés : 101|1|10|2", lambda s: "101|1|10|2" in s)
    # Two negative quantities isolate the quantity check from reserved<=quantity;
    # PostgreSQL checks stock_quantity_check before stock_reserved_quantity_check.
    check("11-negative-quantity", "INSERT INTO inventory.stock VALUES (102,1,-1,-1);", "Rejet CHECK 23514 stock_quantity_check",
          reject=["23514", '"stock_quantity_check"'])
    check("12-reserved-too-high", "INSERT INTO inventory.stock VALUES (103,1,10,11);", "Rejet CHECK 23514 chk_reserved_quantity",
          reject=["23514", '"chk_reserved_quantity"'])
    check("13-unknown-warehouse", "INSERT INTO inventory.stock VALUES (104,999999,10,0);", "Rejet FK 23503 fk_stock_warehouse",
          reject=["23503", '"fk_stock_warehouse"'])
    result = admin("ALTER ROLE inventory_service PASSWORD '" + SECRET + "';")
    if not record("14-temporary-login", "ALTER ROLE inventory_service PASSWORD <secret temporaire généré en mémoire>;", "Mot de passe temporaire installé sans journalisation du secret", result, result[0] == 0):
        raise RuntimeError("Cannot set temporary password")
    check("15-auth-method", "SELECT type,auth_method FROM pg_hba_file_rules WHERE type='host' ORDER BY rule_number;",
          "Toutes les règles TCP utilisent scram-sha-256", lambda s: bool(s) and all(l == "host|scram-sha-256" for l in s.splitlines()))
    check("16-inventory-read", "SELECT current_user, current_database();\nSELECT product_id,warehouse_id,quantity,reserved_quantity FROM inventory.stock ORDER BY product_id;",
          "Connexion TCP réelle inventory_service ; stock lisible 101|1|10|2", lambda s: "inventory_service|aquasave" in s and "101|1|10|2" in s, service=True)
    check("17-payments-denied", "SELECT * FROM payments.payments;", "Rejet privilèges 42501 permission denied for schema payments",
          reject=["42501", "permission denied for schema payments"], service=True)
    check("18-orders-routing", "INSERT INTO orders.customers(id,name,email) VALUES (1,'PG-T06 client','pg-t06@example.invalid');\nINSERT INTO orders.orders(id,customer_id,total_cents,created_at) VALUES (202601,1,1000,'2026-06-15 12:00:00+00'),(201801,1,1000,'2018-06-15 12:00:00+00');\nSELECT id,tableoid::regclass FROM orders.orders ORDER BY id;",
          "201801|orders.orders_default et 202601|orders.orders_2026_06",
          lambda s: "201801|orders.orders_default" in s and "202601|orders.orders_2026_06" in s)
    check("19-item-valid", "INSERT INTO orders.order_items(order_id,order_created_at,product_id,quantity,unit_price_cents) VALUES (202601,'2026-06-15 12:00:00+00',101,1,1000);\nSELECT order_id,order_created_at,quantity FROM orders.order_items;",
          "Article accepté pour le couple (202601, 2026-06-15 12:00:00+00)", lambda s: "202601|2026-06-15 12:00:00+00|1" in s)
    check("20-item-wrong-date", "INSERT INTO orders.order_items(order_id,order_created_at,product_id,quantity,unit_price_cents) VALUES (202601,'2026-06-16 12:00:00+00',101,1,1000);",
          "Rejet FK composite 23503 fk_order_items_order", reject=["23503", '"fk_order_items_order"'])
    check("21-final-data", "SELECT (SELECT count(*) FROM inventory.warehouses),(SELECT count(*) FROM inventory.stock),(SELECT count(*) FROM orders.orders),(SELECT count(*) FROM orders.order_items);",
          "1|1|2|1 : aucune insertion invalide persistée", lambda s: s == "1|1|2|1")
except Exception as exc:
    META["unexpected_error"] = redact(str(exc))
    print("ERREUR INATTENDUE: " + META["unexpected_error"], flush=True)
finally:
    if created:
        result = admin("ALTER ROLE inventory_service NOLOGIN PASSWORD NULL;")
        record("22-revoke-test-login", "ALTER ROLE inventory_service NOLOGIN PASSWORD NULL;", "Identifiants temporaires révoqués", result, result[0] == 0)
        result = execute(["docker", "rm", "-f", NAME])
        record("23-cleanup", f"docker rm -f {NAME}", "Seul le conteneur de test supprimé ; stockage tmpfs libéré", result, result[0] == 0)
    META["hashes_after"] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in PROTECTED}
    record("24-source-integrity", "SHA256 avant/après : Compose, .env, scripts 00/03/05 (aucun contenu .env journalisé)",
           "Tous les fichiers protégés inchangés", (0, json.dumps({p: BEFORE[p] == META['hashes_after'][p] for p in PROTECTED}, indent=2), ""),
           BEFORE == META["hashes_after"])
    META["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
    (RUN / "results.json").write_text(json.dumps({"metadata": META, "checks": RESULTS}, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# PG-T06 — Preuves C1.1 / EC1", "", f"Exécution UTC : {META['started_utc']}",
             f"Instance : `{NAME}` ; base et propriétaire : `aquasave` ; port : `{META.get('port', 'non attribué')}`.",
             "Stockage : tmpfs indépendant, supprimé avec le conteneur. Aucun volume existant monté.", "",
             "Prérequis : Docker, image postgres:16, client psql comprenant les commandes \\restrict/\\unrestrict ; rôle aquasave propriétaire/créateur des objets et capable de créer les rôles techniques. Les mots de passe ne sont pas fournis par 03. Exécuter 00 → 03 → 05 sur une base vide avant insertion. 05 détruit et recrée orders.orders et orders.order_items. Les privilèges par défaut de 03 concernent les objets créés par aquasave.", "",
             "Compose utilise des variables POSTGRES_DB/USER/PASSWORD, le port 5433 et le volume postgres_data. Aucune de ces ressources n'a été utilisée pour les tests. .env uniquement haché pour contrôle d'intégrité.", "",
             "Chaque fichier .log contient la commande exacte (SQL inclus), le résultat attendu, stdout/stderr, SQLSTATE et statut. Les rejets attendus ont un code psql 3 et le SQLSTATE/la contrainte attendus ; ils sont classés OK, sans masquer les erreurs inattendues.", "",
             "| Vérification | Attendu | Statut | Nature |", "|---|---|---|---|"]
    for row in RESULTS:
        lines.append(f"| [{row['id']}]({row['id']}.log) | {row['attendu'].replace('|', '/')} | {row['statut']} | {row['nature']} |")
    required = [f"{i:02}" for i in range(1, 22)]
    missing = [i for i in required if not any(r['id'].startswith(i + '-') for r in RESULTS)]
    for i in missing:
        lines.append(f"| {i} | Étape non atteinte | NON EXÉCUTÉ | erreur bloquante en amont |")
    passed = not missing and not META.get("unexpected_error") and all(r['statut'] == "OK" for r in RESULTS)
    lines += ["", f"INV-01 : {'OUI, prérequis PostgreSQL Inventory validés sur cette instance isolée.' if passed else 'NON validé : consulter les échecs et étapes non exécutées.'}",
              f"PG-T06 : {'peut passer en Terminé pour le périmètre demandé.' if passed else 'ne peut pas passer en Terminé.'}",
              "Les identifiants temporaires ont été révoqués et l'instance supprimée. Pour INV-01, provisionner un nouveau secret inventory_service sur la base de développement reconstruite ; aucune validation de la base existante n'est revendiquée.",
              "Hors périmètre : backend Spring Boot, tests de charge, évaluation des index et restauration. Aucun commit/push."]
    if META.get("unexpected_error"):
        lines += ["", "Erreur inattendue : " + META["unexpected_error"], "Correction proposée : consulter le journal de l'étape en échec et corriger le prérequis/script concerné avant une nouvelle exécution isolée."]
    (RUN / "rapport.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Preuves : " + str(RUN), flush=True)
