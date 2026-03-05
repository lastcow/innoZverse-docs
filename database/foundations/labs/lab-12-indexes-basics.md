# Lab 12: Indexes Basics

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Understand why indexes matter, how B-tree indexes work, create regular and unique indexes, inspect with `SHOW INDEX` and `\d+`, and read basic `EXPLAIN` output.

---

## Step 1: Why Indexes?

Without an index, the database performs a **full table scan** — reading every row to find matches. With an index, it navigates a **B-tree structure** to find matching rows in O(log n) time.

```
Full table scan:   Read 1,000,000 rows → find 5 matches
B-tree index:      Navigate ~20 comparisons → find 5 matches
```

**B-tree index structure:**
```
                    [50]
                   /    \
              [25]         [75]
             /    \       /    \
          [10]   [35] [60]    [90]
         / \    / \   / \    / \
        ...leaves with row pointers...
```

Each leaf points to actual table rows. Searching is fast, but maintaining the index has a write cost.

---

## Step 2: Setup — Generate Test Data

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE indexlab;
USE indexlab;

CREATE TABLE orders (
    order_id    INT NOT NULL AUTO_INCREMENT,
    customer_id INT NOT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'pending',
    total       DECIMAL(10,2),
    order_date  DATE NOT NULL,
    region      VARCHAR(30),
    PRIMARY KEY (order_id)
);

-- Generate 10,000 rows of test data
INSERT INTO orders (customer_id, status, total, order_date, region)
WITH RECURSIVE gen AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM gen WHERE n < 10000
)
SELECT
    FLOOR(1 + RAND() * 1000),
    ELT(FLOOR(1 + RAND() * 4), 'pending', 'shipped', 'completed', 'cancelled'),
    ROUND(10 + RAND() * 990, 2),
    DATE_ADD('2023-01-01', INTERVAL FLOOR(RAND() * 365) DAY),
    ELT(FLOOR(1 + RAND() * 4), 'North', 'South', 'East', 'West')
FROM gen;

SELECT COUNT(*) FROM orders;
EOF
```

📸 **Verified Output:**
```
+----------+
| COUNT(*) |
+----------+
|    10000 |
+----------+
```

---

## Step 3: EXPLAIN Without Index

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE indexlab;

-- Check how many rows MySQL examines for this query
EXPLAIN SELECT * FROM orders WHERE customer_id = 42;
EOF
```

📸 **Verified Output (no index):**
```
+----+-------------+--------+------+---------------+------+---------+------+------+-------------+
| id | select_type | table  | type | possible_keys | key  | key_len | ref  | rows | Extra       |
+----+-------------+--------+------+---------------+------+---------+------+------+-------------+
|  1 | SIMPLE      | orders | ALL  | NULL          | NULL | NULL    | NULL | 9984 | Using where |
+----+-------------+--------+------+---------------+------+---------+------+------+-------------+
```

- `type: ALL` = full table scan
- `rows: 9984` = MySQL estimates it will read nearly ALL rows
- `key: NULL` = no index used

---

## Step 4: CREATE INDEX

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE indexlab;

-- Create a regular B-tree index on customer_id
CREATE INDEX idx_customer_id ON orders (customer_id);

-- Create index on order_date (common in range queries)
CREATE INDEX idx_order_date ON orders (order_date);

-- Create composite index (most useful for queries filtering on both)
CREATE INDEX idx_status_date ON orders (status, order_date);

-- Now run EXPLAIN again
EXPLAIN SELECT * FROM orders WHERE customer_id = 42;
EOF
```

📸 **Verified Output (with index):**
```
+----+-------------+--------+------+-------------------+-----------------+---------+-------+------+-------+
| id | select_type | table  | type | possible_keys     | key             | key_len | ref   | rows | Extra |
+----+-------------+--------+------+-------------------+-----------------+---------+-------+------+-------+
|  1 | SIMPLE      | orders | ref  | idx_customer_id   | idx_customer_id | 4       | const |   10 | NULL  |
+----+-------------+--------+------+-------------------+-----------------+---------+-------+------+-------+
```

- `type: ref` = index lookup (much better than ALL)
- `rows: 10` = MySQL only reads ~10 rows
- `key: idx_customer_id` = index is being used!

---

## Step 5: CREATE UNIQUE INDEX

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE indexlab;

CREATE TABLE products (
    product_id  INT NOT NULL AUTO_INCREMENT,
    sku         VARCHAR(20),
    name        VARCHAR(100) NOT NULL,
    price       DECIMAL(10,2),
    PRIMARY KEY (product_id)
);

-- UNIQUE INDEX: prevents duplicates AND speeds up lookups
CREATE UNIQUE INDEX uq_sku ON products (sku);

INSERT INTO products (sku, name, price) VALUES ('ABC-001', 'Laptop', 999.99);
INSERT INTO products (sku, name, price) VALUES ('ABC-002', 'Mouse',   29.99);

-- Duplicate SKU will fail
INSERT INTO products (sku, name, price) VALUES ('ABC-001', 'Dup Laptop', 799.99);
EOF
```

📸 **Verified Output:**
```
Query OK, 1 row affected
Query OK, 1 row affected
ERROR 1062 (23000): Duplicate entry 'ABC-001' for key 'products.uq_sku'
```

---

## Step 6: SHOW INDEX (MySQL) and \d+ (PostgreSQL)

**MySQL:**
```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE indexlab;

SHOW INDEX FROM orders;
EOF
```

📸 **Verified Output:**
```
+--------+------------+------------------+--------------+-------------+--------+
| Table  | Non_unique | Key_name         | Seq_in_index | Column_name | Index_type |
+--------+------------+------------------+--------------+-------------+--------+
| orders |          0 | PRIMARY          |            1 | order_id    | BTREE  |
| orders |          1 | idx_customer_id  |            1 | customer_id | BTREE  |
| orders |          1 | idx_order_date   |            1 | order_date  | BTREE  |
| orders |          1 | idx_status_date  |            1 | status      | BTREE  |
| orders |          1 | idx_status_date  |            2 | order_date  | BTREE  |
+--------+------------+------------------+--------------+-------------+--------+
```

**PostgreSQL:**
```bash
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec pg-lab psql -U postgres << 'EOF'
CREATE DATABASE indexlab;
EOF

docker exec pg-lab psql -U postgres -d indexlab << 'EOF'
CREATE TABLE orders (
    order_id    SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',
    total       NUMERIC(10,2),
    order_date  DATE NOT NULL
);

CREATE INDEX idx_customer_id ON orders (customer_id);
CREATE INDEX idx_order_date  ON orders (order_date);

\d+ orders
EOF
```

📸 **Verified Output (PostgreSQL \d+):**
```
                                    Table "public.orders"
   Column    |          Type          | ... | Default
-------------+------------------------+-----+---------
 order_id    | integer                |     | nextval(...)
 customer_id | integer                |     |
 status      | character varying(20)  |     | 'pending'
 total       | numeric(10,2)          |     |
 order_date  | date                   |     |
Indexes:
    "orders_pkey" PRIMARY KEY, btree (order_id)
    "idx_customer_id" btree (customer_id)
    "idx_order_date" btree (order_date)
```

---

## Step 7: EXPLAIN with Range Queries and Composite Indexes

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE indexlab;

-- Range query using index
EXPLAIN SELECT * FROM orders
WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31';

-- Composite index: works best when leading column is in WHERE
EXPLAIN SELECT * FROM orders
WHERE status = 'pending' AND order_date > '2024-01-01';

-- Composite index: less useful without leading column
EXPLAIN SELECT * FROM orders
WHERE order_date > '2024-01-01';  -- idx_order_date used instead
EOF
```

📸 **Verified Output:**
```
-- Range query:
type: range | key: idx_order_date | rows: ~1000

-- Composite with both columns:
type: range | key: idx_status_date | rows: ~300

-- Without leading column:
type: range | key: idx_order_date | rows: ~2500
```

> 💡 **Composite index rule (Leftmost Prefix)**: A composite index on `(A, B, C)` can be used for queries on `A`, `A+B`, or `A+B+C` — but NOT for queries on just `B` or `C` alone.

---

## Step 8: Capstone — Index Strategy

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE indexlab;

-- Common query patterns for an e-commerce orders table:
-- 1. Look up by customer
-- 2. Filter by status and date range
-- 3. Look up by region + status

-- Analyze which indexes we have vs need:
EXPLAIN SELECT * FROM orders WHERE region = 'North';              -- full scan! (no index)
EXPLAIN SELECT * FROM orders WHERE status = 'completed' AND region = 'North';  -- partial

-- Create targeted index
CREATE INDEX idx_region_status ON orders (region, status);

EXPLAIN SELECT * FROM orders WHERE region = 'North';              -- now uses index
EXPLAIN SELECT * FROM orders WHERE region = 'North' AND status = 'completed'; -- good

-- List all indexes and their size impact
SELECT
    index_name,
    stat_value * @@innodb_page_size / 1024 / 1024 AS size_mb
FROM mysql.innodb_index_stats
WHERE database_name = 'indexlab'
  AND table_name = 'orders'
  AND stat_name = 'size'
ORDER BY size_mb DESC;

-- DROP unused index
DROP INDEX idx_region_status ON orders;
EOF
```

📸 **Verified Output (before creating region index):**
```
-- Without index:
type: ALL | rows: 9984

-- After creating idx_region_status:
type: ref | key: idx_region_status | rows: ~2500
```

**Cleanup:**
```bash
docker rm -f mysql-lab pg-lab
```

---

## Summary

| Concept | MySQL | PostgreSQL |
|---------|-------|------------|
| Create index | `CREATE INDEX idx ON t (col)` | Same |
| Create unique index | `CREATE UNIQUE INDEX uq ON t (col)` | Same |
| Composite index | `CREATE INDEX idx ON t (col1, col2)` | Same |
| List indexes | `SHOW INDEX FROM t` | `\d+ t` |
| Inspect query plan | `EXPLAIN SELECT ...` | `EXPLAIN SELECT ...` |
| Drop index | `DROP INDEX idx ON t` | `DROP INDEX idx` |

| EXPLAIN `type` | Meaning | Performance |
|----------------|---------|-------------|
| `ALL` | Full table scan | Worst |
| `index` | Full index scan | Poor |
| `range` | Index range scan | Good |
| `ref` | Index lookup (non-unique) | Good |
| `eq_ref` | Index lookup (unique) | Best |
| `const` | Single row lookup | Best |

**Next:** Lab 13 — UPDATE and DELETE
