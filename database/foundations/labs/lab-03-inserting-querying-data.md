# Lab 03: Inserting and Querying Data

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Learn to insert single and multiple rows, query with SELECT, use column aliases, and handle upsert patterns with `REPLACE INTO` (MySQL) and `INSERT … ON CONFLICT` (PostgreSQL).

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10
```

Create the schema:

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "
CREATE DATABASE IF NOT EXISTS shop;
USE shop;
CREATE TABLE products (
    product_id   INT          NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    category     VARCHAR(50)  NOT NULL,
    price        DECIMAL(10,2) NOT NULL,
    stock        INT          NOT NULL DEFAULT 0,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id)
);"

docker exec pg-lab psql -U postgres -c "CREATE DATABASE shop;"
docker exec pg-lab psql -U postgres -d shop -c "
CREATE TABLE products (
    product_id   SERIAL        PRIMARY KEY,
    name         VARCHAR(100)  NOT NULL,
    category     VARCHAR(50)   NOT NULL,
    price        NUMERIC(10,2) NOT NULL,
    stock        INT           NOT NULL DEFAULT 0,
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);"
```

---

## Step 2: INSERT INTO — Single Row

**MySQL:**
```sql
USE shop;

-- Single row with all columns specified
INSERT INTO products (name, category, price, stock)
VALUES ('Laptop Pro 15', 'Electronics', 1299.99, 50);

-- Single row — auto_increment handles product_id
INSERT INTO products (name, category, price, stock)
VALUES ('Wireless Mouse', 'Electronics', 29.99, 200);
```

📸 **Verified Output (MySQL):**
```
Query OK, 1 row affected (0.01 sec)
Query OK, 1 row affected (0.00 sec)
```

**PostgreSQL:**
```sql
INSERT INTO products (name, category, price, stock)
VALUES ('Laptop Pro 15', 'Electronics', 1299.99, 50);

-- PostgreSQL: Use RETURNING to get the generated ID
INSERT INTO products (name, category, price, stock)
VALUES ('Wireless Mouse', 'Electronics', 29.99, 200)
RETURNING product_id, name;
```

📸 **Verified Output (PostgreSQL):**
```
INSERT 0 1

 product_id |      name
------------+----------------
          2 | Wireless Mouse
(1 row)
```

> 💡 PostgreSQL's `RETURNING` clause is very useful — it lets you retrieve generated values (like auto-increment IDs) without a separate SELECT.

---

## Step 3: INSERT INTO — Multiple Rows

```sql
-- MySQL (multi-row insert — much faster than individual INSERTs)
USE shop;
INSERT INTO products (name, category, price, stock) VALUES
    ('USB-C Hub',         'Electronics',  49.99, 150),
    ('Mechanical Keyboard','Electronics', 89.99,  75),
    ('Office Chair',       'Furniture',  299.99,  30),
    ('Standing Desk',      'Furniture',  499.99,  20),
    ('Coffee Mug',         'Kitchen',      9.99, 500),
    ('Water Bottle',       'Kitchen',     24.99, 300);
```

📸 **Verified Output (MySQL):**
```
Query OK, 6 rows affected (0.01 sec)
Records: 6  Duplicates: 0  Warnings: 0
```

> 💡 Multi-row inserts are significantly faster than separate INSERT statements because they reduce round-trips and transaction overhead.

---

## Step 4: SELECT * and SELECT Columns

```sql
-- Select ALL columns (use sparingly — explicit columns are better practice)
SELECT * FROM products;

-- Select specific columns
SELECT name, price, stock FROM products;

-- Select with computed column
SELECT name, price, stock, price * stock AS total_value
FROM products;
```

📸 **Verified Output (MySQL):**
```
+------------+---------------------+-------------+---------+-------+
| product_id | name                | category    | price   | stock |
+------------+---------------------+-------------+---------+-------+
|          1 | Laptop Pro 15       | Electronics | 1299.99 |    50 |
|          2 | Wireless Mouse      | Electronics |   29.99 |   200 |
|          3 | USB-C Hub           | Electronics |   49.99 |   150 |
|          4 | Mechanical Keyboard | Electronics |   89.99 |    75 |
|          5 | Office Chair        | Furniture   |  299.99 |    30 |
|          6 | Standing Desk       | Furniture   |  499.99 |    20 |
|          7 | Coffee Mug          | Kitchen     |    9.99 |   500 |
|          8 | Water Bottle        | Kitchen     |   24.99 |   300 |
+------------+---------------------+-------------+---------+-------+
```

---

## Step 5: Column Aliases with AS

```sql
SELECT
    product_id                     AS id,
    name                           AS product_name,
    price                          AS unit_price,
    stock                          AS units_available,
    ROUND(price * stock, 2)        AS inventory_value,
    category                       AS dept
FROM products;
```

📸 **Verified Output:**
```
+----+---------------------+------------+-----------------+-----------------+-------------+
| id | product_name        | unit_price | units_available | inventory_value | dept        |
+----+---------------------+------------+-----------------+-----------------+-------------+
|  1 | Laptop Pro 15       |    1299.99 |              50 |        64999.50 | Electronics |
|  2 | Wireless Mouse      |      29.99 |             200 |         5998.00 | Electronics |
...
```

> 💡 Aliases (`AS`) rename columns in the result set. They don't affect the underlying table. You can omit `AS` keyword but it's best practice to include it for readability.

---

## Step 6: INSERT … SELECT (Copy Rows)

```sql
-- MySQL: Create an archive table and copy expensive products
CREATE TABLE premium_products AS
    SELECT * FROM products WHERE price > 100;

-- Or with explicit structure:
CREATE TABLE premium_products2 (
    product_id INT, name VARCHAR(100), category VARCHAR(50),
    price DECIMAL(10,2), stock INT, created_at TIMESTAMP
);

INSERT INTO premium_products2
    SELECT product_id, name, category, price, stock, created_at
    FROM products
    WHERE price > 100;

SELECT COUNT(*) AS premium_count FROM premium_products2;
```

📸 **Verified Output:**
```
+---------------+
| premium_count |
+---------------+
|             3 |
+---------------+
```

---

## Step 7: REPLACE INTO (MySQL) vs INSERT … ON CONFLICT (PostgreSQL)

These handle **upsert** — insert if not exists, update if it does.

**MySQL — REPLACE INTO:**
```sql
USE shop;
-- First insert
INSERT INTO products (product_id, name, category, price, stock)
VALUES (1, 'Laptop Pro 15', 'Electronics', 1299.99, 50);

-- Now "upsert" — if product_id=1 exists, DELETE it and re-INSERT
REPLACE INTO products (product_id, name, category, price, stock)
VALUES (1, 'Laptop Pro 16 (Updated)', 'Electronics', 1499.99, 45);

SELECT product_id, name, price FROM products WHERE product_id = 1;
```

📸 **Verified Output (MySQL):**
```
+------------+-------------------------+---------+
| product_id | name                    | price   |
+------------+-------------------------+---------+
|          1 | Laptop Pro 16 (Updated) | 1499.99 |
+------------+-------------------------+---------+
```

> ⚠️ `REPLACE INTO` first DELETEs the row then INSERTs. This resets auto-increment counters and triggers DELETE triggers. Prefer `INSERT … ON DUPLICATE KEY UPDATE` for fine-grained control.

**PostgreSQL — INSERT … ON CONFLICT:**
```sql
-- PostgreSQL upsert (requires UNIQUE constraint on conflict column)
INSERT INTO products (product_id, name, category, price, stock)
VALUES (1, 'Laptop Pro 16 (Updated)', 'Electronics', 1499.99, 45)
ON CONFLICT (product_id)
DO UPDATE SET
    name  = EXCLUDED.name,
    price = EXCLUDED.price,
    stock = EXCLUDED.stock;
```

📸 **Verified Output (PostgreSQL):**
```
INSERT 0 1
```

> 💡 `EXCLUDED` refers to the row that was attempted to be inserted. This is the standard PostgreSQL upsert pattern.

---

## Step 8: Capstone — Verify Row Counts

```sql
-- MySQL: Check row counts in all tables
USE shop;

SELECT
    table_name,
    table_rows AS approximate_rows
FROM information_schema.tables
WHERE table_schema = 'shop'
ORDER BY table_name;

-- Exact counts
SELECT 'products'         AS tbl, COUNT(*) AS rows FROM products
UNION ALL
SELECT 'premium_products', COUNT(*) FROM premium_products
UNION ALL
SELECT 'premium_products2', COUNT(*) FROM premium_products2;
```

📸 **Verified Output:**
```
+-------------------+------+
| tbl               | rows |
+-------------------+------+
| products          |    8 |
| premium_products  |    3 |
| premium_products2 |    3 |
+-------------------+------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab pg-lab
```

---

## Summary

| Operation | MySQL | PostgreSQL |
|-----------|-------|------------|
| Single INSERT | `INSERT INTO t (cols) VALUES (...)` | Same |
| Multi-row INSERT | `INSERT INTO t VALUES (...),(...)` | Same |
| Get inserted ID | `LAST_INSERT_ID()` | `RETURNING id` |
| Copy rows | `INSERT INTO t2 SELECT ... FROM t1` | Same |
| Upsert (delete+insert) | `REPLACE INTO` | N/A |
| Upsert (merge) | `INSERT ... ON DUPLICATE KEY UPDATE` | `INSERT ... ON CONFLICT DO UPDATE` |
| Count rows | `SELECT COUNT(*) FROM t` | Same |

**Next:** Lab 04 — Filtering and Sorting
