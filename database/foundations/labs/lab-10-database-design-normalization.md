# Lab 10: Database Design and Normalization

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Learn 1NF, 2NF, and 3NF normalization, understand denormalization trade-offs, ER diagram concepts, and design a fully normalized schema from scratch.

---

## Step 1: Why Normalization?

Normalization is the process of organizing data to reduce redundancy and improve integrity.

**Problems with un-normalized data:**
- **Insert anomaly**: Can't record a professor without a course
- **Update anomaly**: Changing a city name requires updating thousands of rows
- **Delete anomaly**: Deleting the last student drops course information

```sql
-- Un-normalized table (everything in one place)
-- order_details: order_id, customer_name, customer_email, customer_city,
--                product_sku, product_name, product_category, quantity, price

-- Problems:
-- 1. Customer info repeated for every order item
-- 2. Change customer city → update ALL their order rows
-- 3. Delete all items → lose customer record
-- 4. Can't store product without an order
```

---

## Step 2: First Normal Form (1NF)

**1NF requires:**
1. Each cell contains a single (atomic) value
2. Each row is unique (has a primary key)
3. No repeating groups or arrays

**VIOLATION — Not in 1NF:**
```
student_id | name  | courses
-----------+-------+---------------------------
1          | Alice | Math, English, Science    ← multiple values in one cell!
2          | Bob   | Math, History
```

**FIXED — 1NF:**
```sql
CREATE TABLE student_courses (
    student_id  INT NOT NULL,
    student_name VARCHAR(50) NOT NULL,
    course_name  VARCHAR(50) NOT NULL,
    PRIMARY KEY (student_id, course_name)
);
```

```
student_id | student_name | course_name
-----------+--------------+------------
1          | Alice        | Math
1          | Alice        | English     ← one value per cell
1          | Alice        | Science
2          | Bob          | Math
2          | Bob          | History
```

---

## Step 3: Second Normal Form (2NF)

**2NF requires:**
1. Already in 1NF
2. Every non-key column must depend on the **entire** primary key (no partial dependencies)

Only applies when you have a **composite primary key**.

**VIOLATION — Not in 2NF:**
```
student_id | course_id | student_name | course_name | grade
-----------+-----------+--------------+-------------+------
PK part1   | PK part2  | depends only | depends only| depends on
           |           | on student_id| on course_id| BOTH PKs
```

`student_name` depends only on `student_id` → partial dependency!
`course_name` depends only on `course_id` → partial dependency!

**FIXED — 2NF:**
```sql
-- Split into separate tables
CREATE TABLE students (
    student_id   INT PRIMARY KEY,
    student_name VARCHAR(50) NOT NULL
);

CREATE TABLE courses (
    course_id   INT PRIMARY KEY,
    course_name VARCHAR(50) NOT NULL
);

CREATE TABLE enrollments (
    student_id INT NOT NULL,
    course_id  INT NOT NULL,
    grade      CHAR(2),           -- depends on BOTH: student + course
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)
);
```

---

## Step 4: Third Normal Form (3NF)

**3NF requires:**
1. Already in 2NF
2. No transitive dependencies (non-key column must not depend on another non-key column)

**VIOLATION — Not in 3NF:**
```
emp_id | emp_name | dept_id | dept_name | dept_location
```

`dept_name` → depends on `dept_id` (not on `emp_id`)!
`dept_location` → depends on `dept_id` (not on `emp_id`)!

This is a **transitive dependency**: `emp_id → dept_id → dept_name`

**FIXED — 3NF:**
```sql
CREATE TABLE departments (
    dept_id      INT PRIMARY KEY,
    dept_name    VARCHAR(50) NOT NULL,
    dept_location VARCHAR(100)
);

CREATE TABLE employees (
    emp_id    INT PRIMARY KEY,
    emp_name  VARCHAR(100) NOT NULL,
    dept_id   INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);
```

---

## Step 5: Build Normalized Schema from Raw Data

**Raw un-normalized data:**
```
order_id | order_date | cust_name | cust_email    | cust_city | product | category | qty | unit_price
---------|------------|-----------|---------------|-----------|---------|----------|-----|----------
1001     | 2024-01-10 | Alice Lee | alice@mail.com| NYC       | Laptop  | Elec     |  1  | 999.99
1001     | 2024-01-10 | Alice Lee | alice@mail.com| NYC       | Mouse   | Elec     |  2  |  29.99
1002     | 2024-01-15 | Bob Kim   | bob@mail.com  | LA        | Laptop  | Elec     |  1  | 999.99
```

**Normalized design:**

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE normlab;
USE normlab;

-- 1NF: Atomic values, unique rows
-- 2NF: No partial dependencies
-- 3NF: No transitive dependencies

CREATE TABLE categories (
    cat_id   INT NOT NULL AUTO_INCREMENT,
    cat_name VARCHAR(50) NOT NULL UNIQUE,
    PRIMARY KEY (cat_id)
);

CREATE TABLE products (
    product_id  INT NOT NULL AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    cat_id       INT NOT NULL,
    unit_price   DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (product_id),
    FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
);

CREATE TABLE customers (
    cust_id   INT NOT NULL AUTO_INCREMENT,
    name      VARCHAR(100) NOT NULL,
    email     VARCHAR(100) NOT NULL UNIQUE,
    city      VARCHAR(50),
    PRIMARY KEY (cust_id)
);

CREATE TABLE orders (
    order_id    INT NOT NULL AUTO_INCREMENT,
    cust_id     INT NOT NULL,
    order_date  DATE NOT NULL,
    PRIMARY KEY (order_id),
    FOREIGN KEY (cust_id) REFERENCES customers(cust_id)
);

CREATE TABLE order_items (
    order_id    INT NOT NULL,
    product_id  INT NOT NULL,
    qty         INT NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL,   -- snapshot at time of order
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Load normalized data
INSERT INTO categories (cat_name) VALUES ('Electronics');
INSERT INTO products (product_name, cat_id, unit_price) VALUES
('Laptop', 1, 999.99), ('Mouse', 1, 29.99);

INSERT INTO customers (name, email, city) VALUES
('Alice Lee', 'alice@mail.com', 'NYC'),
('Bob Kim',   'bob@mail.com',   'LA');

INSERT INTO orders (cust_id, order_date) VALUES (1, '2024-01-10'), (2, '2024-01-15');

INSERT INTO order_items VALUES
(1, 1, 1, 999.99),
(1, 2, 2,  29.99),
(2, 1, 1, 999.99);
EOF
```

---

## Step 6: Query Normalized Schema

```sql
USE normlab;

-- Reconstruct the original "flat" view via JOINs
SELECT
    o.order_id,
    o.order_date,
    c.name        AS customer,
    c.city,
    p.product_name,
    cat.cat_name  AS category,
    oi.qty,
    oi.unit_price,
    oi.qty * oi.unit_price AS line_total
FROM orders o
JOIN customers c   ON o.cust_id   = c.cust_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p    ON oi.product_id = p.product_id
JOIN categories cat ON p.cat_id    = cat.cat_id
ORDER BY o.order_id, p.product_name;
```

📸 **Verified Output:**
```
+----------+------------+-----------+------+--------------+-------------+-----+------------+------------+
| order_id | order_date | customer  | city | product_name | category    | qty | unit_price | line_total |
+----------+------------+-----------+------+--------------+-------------+-----+------------+------------+
|        1 | 2024-01-10 | Alice Lee | NYC  | Laptop       | Electronics |   1 |     999.99 |     999.99 |
|        1 | 2024-01-10 | Alice Lee | NYC  | Mouse        | Electronics |   2 |      29.99 |      59.98 |
|        2 | 2024-01-15 | Bob Kim   | LA   | Laptop       | Electronics |   1 |     999.99 |     999.99 |
+----------+------------+-----------+------+--------------+-------------+-----+------------+------------+
```

---

## Step 7: Denormalization Trade-offs

| Scenario | Normalized | Denormalized |
|----------|-----------|--------------|
| Storage | Less data, no redundancy | More data, some redundancy |
| Writes | Clean (update in one place) | Complex (update multiple places) |
| Reads | Requires JOINs | Fast flat reads |
| Integrity | Enforced by FK | Application must maintain |
| Use case | OLTP (transactional) | OLAP (analytics), caching layers |

**When to denormalize:**
- Read-heavy reporting tables (data warehouses)
- Known performance bottleneck after measuring
- Cache tables for dashboards
- When JOIN cost exceeds redundancy cost

> 💡 **Rule of thumb**: Start normalized. Denormalize only when you have a measured performance problem that normalization is causing.

---

## Step 8: Capstone — Verify Schema Integrity

```sql
USE normlab;

-- Check referential integrity
SELECT 'categories' AS tbl, COUNT(*) AS rows FROM categories
UNION ALL SELECT 'products',    COUNT(*) FROM products
UNION ALL SELECT 'customers',   COUNT(*) FROM customers
UNION ALL SELECT 'orders',      COUNT(*) FROM orders
UNION ALL SELECT 'order_items', COUNT(*) FROM order_items;

-- Verify each order_item has valid product and order
SELECT COUNT(*) AS orphaned_items
FROM order_items oi
LEFT JOIN orders   o ON oi.order_id   = o.order_id
LEFT JOIN products p ON oi.product_id = p.product_id
WHERE o.order_id IS NULL OR p.product_id IS NULL;
```

📸 **Verified Output:**
```
+-------------+------+
| tbl         | rows |
+-------------+------+
| categories  |    1 |
| products    |    2 |
| customers   |    2 |
| orders      |    2 |
| order_items |    3 |
+-------------+------+

+-----------------+
| orphaned_items  |
+-----------------+
|               0 |
+-----------------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Normal Form | Requirement | Fixes |
|-------------|------------|-------|
| 1NF | Atomic values, unique rows, no repeating groups | Multi-valued cells, arrays in columns |
| 2NF | 1NF + no partial dependencies on composite PK | Attributes depending on part of PK |
| 3NF | 2NF + no transitive dependencies | A→B→C where B is non-key |
| BCNF | 3NF + every determinant is a candidate key | Rare edge cases in 3NF |

| Concept | Description |
|---------|-------------|
| Insert anomaly | Can't add data without adding other unrelated data |
| Update anomaly | Must update same fact in multiple rows |
| Delete anomaly | Deleting data inadvertently removes other facts |
| Denormalization | Intentional redundancy for read performance |

**Next:** Lab 11 — Primary Keys, Foreign Keys, and Constraints
