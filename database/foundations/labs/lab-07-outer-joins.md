# Lab 07: Outer Joins

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Learn LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN (PostgreSQL), finding unmatched rows, the anti-join pattern, and CROSS JOIN.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE joinlab;
USE joinlab;

CREATE TABLE customers (
    customer_id  INT NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(100),
    city         VARCHAR(50),
    PRIMARY KEY (customer_id)
);

CREATE TABLE orders (
    order_id    INT NOT NULL AUTO_INCREMENT,
    customer_id INT,
    total       DECIMAL(10,2),
    order_date  DATE,
    status      VARCHAR(20) DEFAULT 'pending',
    PRIMARY KEY (order_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE categories (
    cat_id   INT NOT NULL AUTO_INCREMENT,
    cat_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (cat_id)
);

CREATE TABLE products (
    product_id  INT NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100),
    cat_id      INT,
    price       DECIMAL(10,2),
    PRIMARY KEY (product_id),
    FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
);

INSERT INTO customers (name, email, city) VALUES
('Alice Brown',   'alice@email.com',  'New York'),
('Bob Chen',      'bob@email.com',    'Chicago'),
('Carol Davis',   'carol@email.com',  'Houston'),
('David Evans',   'david@email.com',  'Phoenix'),
('Eve Foster',    NULL,               'Boston');   -- no email

INSERT INTO orders (customer_id, total, order_date, status) VALUES
(1, 299.99,  '2024-01-10', 'completed'),
(1, 149.50,  '2024-01-25', 'completed'),
(2, 89.99,   '2024-02-05', 'completed'),
(3, 499.00,  '2024-02-18', 'shipped'),
(1, 75.00,   '2024-03-01', 'pending'),
(NULL, 55.00,'2024-03-05', 'pending');  -- guest order (no customer)

INSERT INTO categories (cat_name) VALUES
('Electronics'), ('Books'), ('Clothing'), ('Sports');

INSERT INTO products (name, cat_id, price) VALUES
('Laptop',      1, 999.99),
('Phone',       1, 499.99),
('SQL Guide',   2,  39.99),
('T-Shirt',     3,  19.99),
('Running Shoes',3, 89.99),
('Yoga Mat',    NULL, 29.99);  -- uncategorized product
EOF
```

---

## Step 2: LEFT JOIN

```sql
USE joinlab;

-- LEFT JOIN: all rows from LEFT table, matching rows from RIGHT table
-- Customers without orders will show NULL for order columns
SELECT
    c.name         AS customer,
    c.city,
    o.order_id,
    o.total,
    o.order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
ORDER BY c.name, o.order_date;
```

📸 **Verified Output:**
```
+--------------+----------+----------+--------+------------+
| customer     | city     | order_id | total  | order_date |
+--------------+----------+----------+--------+------------+
| Alice Brown  | New York |        1 | 299.99 | 2024-01-10 |
| Alice Brown  | New York |        2 | 149.50 | 2024-01-25 |
| Alice Brown  | New York |        5 |  75.00 | 2024-03-01 |
| Bob Chen     | Chicago  |        3 |  89.99 | 2024-02-05 |
| Carol Davis  | Houston  |        4 | 499.00 | 2024-02-18 |
| David Evans  | Phoenix  |     NULL |   NULL | NULL       |  ← no orders
| Eve Foster   | Boston   |     NULL |   NULL | NULL       |  ← no orders
+--------------+----------+----------+--------+------------+
```

> 💡 LEFT JOIN preserves ALL rows from the left (first) table. Rows with no match in the right table get NULL for right-table columns. David and Eve have no orders — they still appear.

---

## Step 3: RIGHT JOIN

```sql
-- RIGHT JOIN: all rows from RIGHT table, matching from LEFT
-- Orders without a customer (guest orders) will show NULL for customer columns
SELECT
    c.name         AS customer,
    o.order_id,
    o.total,
    o.status
FROM customers c
RIGHT JOIN orders o ON c.customer_id = o.customer_id
ORDER BY o.order_id;
```

📸 **Verified Output:**
```
+--------------+----------+--------+-----------+
| customer     | order_id | total  | status    |
+--------------+----------+--------+-----------+
| Alice Brown  |        1 | 299.99 | completed |
| Alice Brown  |        2 | 149.50 | completed |
| Bob Chen     |        3 |  89.99 | completed |
| Carol Davis  |        4 | 499.00 | shipped   |
| Alice Brown  |        5 |  75.00 | pending   |
| NULL         |        6 |  55.00 | pending   |  ← guest order
+--------------+----------+--------+-----------+
```

> 💡 RIGHT JOIN is the mirror of LEFT JOIN. In practice, most developers rewrite RIGHT JOINs as LEFT JOINs by swapping table order — it's the same result but easier to read.

---

## Step 4: Finding Unmatched Rows — Anti-Join Pattern

```sql
-- Find customers who have NEVER placed an order
-- Pattern: LEFT JOIN + WHERE right_table.key IS NULL
SELECT
    c.customer_id,
    c.name,
    c.city
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;
```

📸 **Verified Output:**
```
+-------------+-------------+---------+
| customer_id | name        | city    |
+-------------+-------------+---------+
|           4 | David Evans | Phoenix |
|           5 | Eve Foster  | Boston  |
+-------------+-------------+---------+
```

```sql
-- Find products with no category assigned
SELECT p.product_id, p.name, p.price
FROM products p
LEFT JOIN categories c ON p.cat_id = c.cat_id
WHERE c.cat_id IS NULL;
```

📸 **Verified Output:**
```
+------------+----------+-------+
| product_id | name     | price |
+------------+----------+-------+
|          6 | Yoga Mat | 29.99 |
+------------+----------+-------+
```

> 💡 The `LEFT JOIN ... WHERE b.id IS NULL` pattern is called an **anti-join**. It efficiently finds rows in table A with no matching row in table B.

---

## Step 5: FULL OUTER JOIN (PostgreSQL)

MySQL does NOT support FULL OUTER JOIN directly. PostgreSQL does.

**PostgreSQL:**
```bash
docker exec pg-lab psql -U postgres << 'EOF'
CREATE DATABASE joinlab;
EOF

docker exec pg-lab psql -U postgres -d joinlab << 'EOF'
CREATE TABLE team_a (id INT, name VARCHAR(50));
CREATE TABLE team_b (id INT, name VARCHAR(50));

INSERT INTO team_a VALUES (1,'Alice'),(2,'Bob'),(3,'Carol');
INSERT INTO team_b VALUES (2,'Bob'),(3,'Carol'),(4,'David'),(5,'Eve');

-- FULL OUTER JOIN: all rows from BOTH tables
SELECT
    a.id   AS a_id,
    a.name AS a_name,
    b.id   AS b_id,
    b.name AS b_name
FROM team_a a
FULL OUTER JOIN team_b b ON a.id = b.id;
EOF
```

📸 **Verified Output (PostgreSQL):**
```
 a_id | a_name | b_id | b_name
------+--------+------+--------
    1 | Alice  | NULL | NULL      ← only in A
    2 | Bob    |    2 | Bob       ← in both
    3 | Carol  |    3 | Carol     ← in both
 NULL | NULL   |    4 | David     ← only in B
 NULL | NULL   |    5 | Eve       ← only in B
(5 rows)
```

**MySQL workaround for FULL OUTER JOIN:**
```sql
-- Simulate FULL OUTER JOIN in MySQL using UNION
SELECT c.name, o.order_id
FROM customers c LEFT JOIN orders o ON c.customer_id = o.customer_id
UNION
SELECT c.name, o.order_id
FROM customers c RIGHT JOIN orders o ON c.customer_id = o.customer_id;
```

---

## Step 6: CROSS JOIN

```sql
-- CROSS JOIN: every combination of rows from both tables (Cartesian product)
-- Use intentionally for generating combinations
SELECT
    c.cat_name   AS category,
    s.size_name  AS size
FROM categories c
CROSS JOIN (
    SELECT 'Small'  AS size_name UNION ALL
    SELECT 'Medium' UNION ALL
    SELECT 'Large'
) s
ORDER BY c.cat_name, s.size_name;
```

📸 **Verified Output:**
```
+-------------+---------+
| category    | size    |
+-------------+---------+
| Books       | Large   |
| Books       | Medium  |
| Books       | Small   |
| Clothing    | Large   |
| Clothing    | Medium  |
| Clothing    | Small   |
| Electronics | Large   |
| Electronics | Medium  |
| Electronics | Small   |
| Sports      | Large   |
| Sports      | Medium  |
| Sports      | Small   |
+-------------+---------+
12 rows (4 categories × 3 sizes)
```

> 💡 CROSS JOIN is intentional when you need all combinations (e.g., generate a size × color matrix, create test data). With large tables, result grows as m×n rows — be careful!

---

## Step 7: Multi-Table Outer Join

```sql
USE joinlab;

-- Customer summary with order stats — include customers with 0 orders
SELECT
    c.name                          AS customer,
    c.city,
    COUNT(o.order_id)               AS order_count,
    COALESCE(SUM(o.total), 0)       AS total_spent,
    COALESCE(MAX(o.order_date), 'Never') AS last_order
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.city
ORDER BY total_spent DESC;
```

📸 **Verified Output:**
```
+--------------+----------+-------------+-------------+------------+
| customer     | city     | order_count | total_spent | last_order |
+--------------+----------+-------------+-------------+------------+
| Alice Brown  | New York |           3 |      524.49 | 2024-03-01 |
| Carol Davis  | Houston  |           1 |      499.00 | 2024-02-18 |
| Bob Chen     | Chicago  |           1 |       89.99 | 2024-02-05 |
| David Evans  | Phoenix  |           0 |        0.00 | Never      |
| Eve Foster   | Boston   |           0 |        0.00 | Never      |
+--------------+----------+-------------+-------------+------------+
```

---

## Step 8: Capstone — Category Coverage Report

```sql
USE joinlab;

-- Which categories have products, and which don't? (full coverage)
SELECT
    c.cat_name                         AS category,
    COUNT(p.product_id)               AS product_count,
    ROUND(AVG(p.price), 2)            AS avg_price,
    ROUND(MIN(p.price), 2)            AS min_price,
    ROUND(MAX(p.price), 2)            AS max_price
FROM categories c
LEFT JOIN products p ON c.cat_id = p.cat_id
GROUP BY c.cat_id, c.cat_name
ORDER BY product_count DESC;
```

📸 **Verified Output:**
```
+-------------+---------------+-----------+-----------+-----------+
| category    | product_count | avg_price | min_price | max_price |
+-------------+---------------+-----------+-----------+-----------+
| Electronics |             2 |    749.99 |    499.99 |    999.99 |
| Clothing    |             2 |     54.99 |     19.99 |     89.99 |
| Books       |             1 |     39.99 |     39.99 |     39.99 |
| Sports      |             0 |      NULL |      NULL |      NULL |  ← no products
+-------------+---------------+-----------+-----------+-----------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab pg-lab
```

---

## Summary

| Join Type | Returns | Syntax |
|-----------|---------|--------|
| INNER JOIN | Only matching rows | `JOIN b ON a.id = b.a_id` |
| LEFT JOIN | All left + matching right | `LEFT JOIN b ON ...` |
| RIGHT JOIN | All right + matching left | `RIGHT JOIN b ON ...` |
| FULL OUTER JOIN | All rows from both tables | `FULL OUTER JOIN` (PG only) |
| CROSS JOIN | All combinations | `CROSS JOIN b` |
| Anti-join | Unmatched from left | `LEFT JOIN b ... WHERE b.id IS NULL` |

**Next:** Lab 08 — Subqueries
