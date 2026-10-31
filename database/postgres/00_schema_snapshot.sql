--
-- PostgreSQL database dump
--

\restrict Cv54ylDZNuKrsaJmwFQFOcRPcCMo8cvTFvRUrRCh4icVdVKOnreTMpboanBMhtr

-- Dumped from database version 16.14 (Debian 16.14-1.pgdg13+1)
-- Dumped by pg_dump version 16.14 (Debian 16.14-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: auth; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA auth;


--
-- Name: inventory; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA inventory;


--
-- Name: orders; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA orders;


--
-- Name: payments; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA payments;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: roles; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.roles (
    id integer NOT NULL,
    name text NOT NULL,
    description text
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: auth; Owner: -
--

CREATE SEQUENCE auth.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: -
--

ALTER SEQUENCE auth.roles_id_seq OWNED BY auth.roles.id;


--
-- Name: user_roles; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.user_roles (
    user_id integer NOT NULL,
    role_id integer NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: auth; Owner: -
--

CREATE TABLE auth.users (
    id integer NOT NULL,
    email text NOT NULL,
    password_hash text NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: auth; Owner: -
--

CREATE SEQUENCE auth.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: auth; Owner: -
--

ALTER SEQUENCE auth.users_id_seq OWNED BY auth.users.id;


--
-- Name: stock; Type: TABLE; Schema: inventory; Owner: -
--

CREATE TABLE inventory.stock (
    product_id integer NOT NULL,
    warehouse_id integer NOT NULL,
    quantity integer DEFAULT 0 NOT NULL,
    reserved_quantity integer DEFAULT 0 NOT NULL,
    CONSTRAINT chk_reserved_quantity CHECK ((reserved_quantity <= quantity)),
    CONSTRAINT stock_quantity_check CHECK ((quantity >= 0)),
    CONSTRAINT stock_reserved_quantity_check CHECK ((reserved_quantity >= 0))
);


--
-- Name: stock_reservations; Type: TABLE; Schema: inventory; Owner: -
--

CREATE TABLE inventory.stock_reservations (
    id uuid NOT NULL,
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    warehouse_id integer NOT NULL,
    quantity integer NOT NULL,
    status text DEFAULT 'reserved'::text NOT NULL,
    idempotency_key text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_reservation_status CHECK ((status = ANY (ARRAY['reserved'::text, 'confirmed'::text, 'released'::text]))),
    CONSTRAINT stock_reservations_quantity_check CHECK ((quantity > 0))
);


--
-- Name: warehouses; Type: TABLE; Schema: inventory; Owner: -
--

CREATE TABLE inventory.warehouses (
    id integer NOT NULL,
    name text NOT NULL,
    capacity_units integer NOT NULL,
    CONSTRAINT warehouses_capacity_units_check CHECK ((capacity_units > 0))
);


--
-- Name: warehouses_id_seq; Type: SEQUENCE; Schema: inventory; Owner: -
--

CREATE SEQUENCE inventory.warehouses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: warehouses_id_seq; Type: SEQUENCE OWNED BY; Schema: inventory; Owner: -
--

ALTER SEQUENCE inventory.warehouses_id_seq OWNED BY inventory.warehouses.id;


--
-- Name: customers; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.customers (
    id integer NOT NULL,
    name text NOT NULL,
    email text NOT NULL
);


--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: orders; Owner: -
--

CREATE SEQUENCE orders.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: orders; Owner: -
--

ALTER SEQUENCE orders.customers_id_seq OWNED BY orders.customers.id;


--
-- Name: order_items; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.order_items (
    id integer NOT NULL,
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity integer NOT NULL,
    unit_price_cents integer NOT NULL,
    CONSTRAINT order_items_quantity_check CHECK ((quantity > 0)),
    CONSTRAINT order_items_unit_price_cents_check CHECK ((unit_price_cents >= 0))
);


--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: orders; Owner: -
--

CREATE SEQUENCE orders.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: orders; Owner: -
--

ALTER SEQUENCE orders.order_items_id_seq OWNED BY orders.order_items.id;


--
-- Name: orders; Type: TABLE; Schema: orders; Owner: -
--

CREATE TABLE orders.orders (
    id integer NOT NULL,
    customer_id integer NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    total_cents integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_order_status CHECK ((status = ANY (ARRAY['pending'::text, 'paid'::text, 'preparing'::text, 'shipped'::text, 'delivered'::text, 'payment_failed'::text, 'cancelled'::text]))),
    CONSTRAINT orders_total_cents_check CHECK ((total_cents >= 0))
);


--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: orders; Owner: -
--

CREATE SEQUENCE orders.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: orders; Owner: -
--

ALTER SEQUENCE orders.orders_id_seq OWNED BY orders.orders.id;


--
-- Name: payments; Type: TABLE; Schema: payments; Owner: -
--

CREATE TABLE payments.payments (
    id integer NOT NULL,
    order_id integer NOT NULL,
    amount_cents integer NOT NULL,
    status text DEFAULT 'pending'::text NOT NULL,
    idempotency_key text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_payment_status CHECK ((status = ANY (ARRAY['pending'::text, 'succeeded'::text, 'failed'::text, 'refunded'::text]))),
    CONSTRAINT payments_amount_cents_check CHECK ((amount_cents >= 0))
);


--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: payments; Owner: -
--

CREATE SEQUENCE payments.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: payments; Owner: -
--

ALTER SEQUENCE payments.payments_id_seq OWNED BY payments.payments.id;


--
-- Name: roles id; Type: DEFAULT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.roles ALTER COLUMN id SET DEFAULT nextval('auth.roles_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users ALTER COLUMN id SET DEFAULT nextval('auth.users_id_seq'::regclass);


--
-- Name: warehouses id; Type: DEFAULT; Schema: inventory; Owner: -
--

ALTER TABLE ONLY inventory.warehouses ALTER COLUMN id SET DEFAULT nextval('inventory.warehouses_id_seq'::regclass);


--
-- Name: customers id; Type: DEFAULT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.customers ALTER COLUMN id SET DEFAULT nextval('orders.customers_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_items ALTER COLUMN id SET DEFAULT nextval('orders.order_items_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.orders ALTER COLUMN id SET DEFAULT nextval('orders.orders_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: payments; Owner: -
--

ALTER TABLE ONLY payments.payments ALTER COLUMN id SET DEFAULT nextval('payments.payments_id_seq'::regclass);


--
-- Name: roles roles_name_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: stock pk_stock; Type: CONSTRAINT; Schema: inventory; Owner: -
--

ALTER TABLE ONLY inventory.stock
    ADD CONSTRAINT pk_stock PRIMARY KEY (product_id, warehouse_id);


--
-- Name: stock_reservations stock_reservations_idempotency_key_key; Type: CONSTRAINT; Schema: inventory; Owner: -
--

ALTER TABLE ONLY inventory.stock_reservations
    ADD CONSTRAINT stock_reservations_idempotency_key_key UNIQUE (idempotency_key);


--
-- Name: stock_reservations stock_reservations_pkey; Type: CONSTRAINT; Schema: inventory; Owner: -
--

ALTER TABLE ONLY inventory.stock_reservations
    ADD CONSTRAINT stock_reservations_pkey PRIMARY KEY (id);


--
-- Name: warehouses warehouses_name_key; Type: CONSTRAINT; Schema: inventory; Owner: -
--

ALTER TABLE ONLY inventory.warehouses
    ADD CONSTRAINT warehouses_name_key UNIQUE (name);


--
-- Name: warehouses warehouses_pkey; Type: CONSTRAINT; Schema: inventory; Owner: -
--

ALTER TABLE ONLY inventory.warehouses
    ADD CONSTRAINT warehouses_pkey PRIMARY KEY (id);


--
-- Name: customers customers_email_key; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.customers
    ADD CONSTRAINT customers_email_key UNIQUE (email);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: payments payments_idempotency_key_key; Type: CONSTRAINT; Schema: payments; Owner: -
--

ALTER TABLE ONLY payments.payments
    ADD CONSTRAINT payments_idempotency_key_key UNIQUE (idempotency_key);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: payments; Owner: -
--

ALTER TABLE ONLY payments.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: idx_reservations_active; Type: INDEX; Schema: inventory; Owner: -
--

CREATE INDEX idx_reservations_active ON inventory.stock_reservations USING btree (product_id, warehouse_id) WHERE (status = 'reserved'::text);


--
-- Name: idx_reservations_order; Type: INDEX; Schema: inventory; Owner: -
--

CREATE INDEX idx_reservations_order ON inventory.stock_reservations USING btree (order_id);


--
-- Name: idx_stock_warehouse; Type: INDEX; Schema: inventory; Owner: -
--

CREATE INDEX idx_stock_warehouse ON inventory.stock USING btree (warehouse_id);


--
-- Name: idx_order_items_order; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX idx_order_items_order ON orders.order_items USING btree (order_id);


--
-- Name: idx_orders_customer_date; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX idx_orders_customer_date ON orders.orders USING btree (customer_id, created_at DESC);


--
-- Name: idx_orders_status_date; Type: INDEX; Schema: orders; Owner: -
--

CREATE INDEX idx_orders_status_date ON orders.orders USING btree (status, created_at DESC);


--
-- Name: idx_payments_order; Type: INDEX; Schema: payments; Owner: -
--

CREATE INDEX idx_payments_order ON payments.payments USING btree (order_id);


--
-- Name: user_roles fk_user_roles_role; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.user_roles
    ADD CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES auth.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles fk_user_roles_user; Type: FK CONSTRAINT; Schema: auth; Owner: -
--

ALTER TABLE ONLY auth.user_roles
    ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;


--
-- Name: stock_reservations fk_reservation_stock; Type: FK CONSTRAINT; Schema: inventory; Owner: -
--

ALTER TABLE ONLY inventory.stock_reservations
    ADD CONSTRAINT fk_reservation_stock FOREIGN KEY (product_id, warehouse_id) REFERENCES inventory.stock(product_id, warehouse_id);


--
-- Name: stock fk_stock_warehouse; Type: FK CONSTRAINT; Schema: inventory; Owner: -
--

ALTER TABLE ONLY inventory.stock
    ADD CONSTRAINT fk_stock_warehouse FOREIGN KEY (warehouse_id) REFERENCES inventory.warehouses(id);


--
-- Name: order_items fk_order_items_order; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.order_items
    ADD CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders.orders(id) ON DELETE CASCADE;


--
-- Name: orders fk_orders_customer; Type: FK CONSTRAINT; Schema: orders; Owner: -
--

ALTER TABLE ONLY orders.orders
    ADD CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES orders.customers(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Cv54ylDZNuKrsaJmwFQFOcRPcCMo8cvTFvRUrRCh4icVdVKOnreTMpboanBMhtr

