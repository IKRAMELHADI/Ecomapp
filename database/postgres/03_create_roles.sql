-- ============================================
-- AquaSave - Rôles techniques PostgreSQL
-- ============================================

-- Création des rôles sans mots de passe codés en dur.
-- Les mots de passe sont configurés séparément.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'orders_service'
    ) THEN
        CREATE ROLE orders_service LOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'inventory_service'
    ) THEN
        CREATE ROLE inventory_service LOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'payments_service'
    ) THEN
        CREATE ROLE payments_service LOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'auth_service'
    ) THEN
        CREATE ROLE auth_service LOGIN;
    END IF;
END
$$;

-- Connexion à la base
GRANT CONNECT ON DATABASE aquasave
TO orders_service, inventory_service,
   payments_service, auth_service;

-- Isolation des schémas
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

GRANT USAGE ON SCHEMA orders TO orders_service;
GRANT USAGE ON SCHEMA inventory TO inventory_service;
GRANT USAGE ON SCHEMA payments TO payments_service;
GRANT USAGE ON SCHEMA auth TO auth_service;

-- Permissions sur les tables existantes
GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA orders
TO orders_service;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA inventory
TO inventory_service;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA payments
TO payments_service;

GRANT SELECT, INSERT, UPDATE, DELETE
ON ALL TABLES IN SCHEMA auth
TO auth_service;

-- Permissions sur les séquences SERIAL
GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA orders
TO orders_service;

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA inventory
TO inventory_service;

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA payments
TO payments_service;

GRANT USAGE, SELECT
ON ALL SEQUENCES IN SCHEMA auth
TO auth_service;

-- Permissions pour les futures tables créées
-- par le propriétaire actuel des objets.

ALTER DEFAULT PRIVILEGES FOR ROLE aquasave
IN SCHEMA orders
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO orders_service;

ALTER DEFAULT PRIVILEGES FOR ROLE aquasave
IN SCHEMA inventory
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO inventory_service;

ALTER DEFAULT PRIVILEGES FOR ROLE aquasave
IN SCHEMA payments
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO payments_service;

ALTER DEFAULT PRIVILEGES FOR ROLE aquasave
IN SCHEMA auth
GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLES TO auth_service;

ALTER DEFAULT PRIVILEGES FOR ROLE aquasave
IN SCHEMA orders
GRANT USAGE, SELECT
ON SEQUENCES TO orders_service;

ALTER DEFAULT PRIVILEGES FOR ROLE aquasave
IN SCHEMA inventory
GRANT USAGE, SELECT
ON SEQUENCES TO inventory_service;

ALTER DEFAULT PRIVILEGES FOR ROLE aquasave
IN SCHEMA payments
GRANT USAGE, SELECT
ON SEQUENCES TO payments_service;

ALTER DEFAULT PRIVILEGES FOR ROLE aquasave
IN SCHEMA auth
GRANT USAGE, SELECT
ON SEQUENCES TO auth_service;