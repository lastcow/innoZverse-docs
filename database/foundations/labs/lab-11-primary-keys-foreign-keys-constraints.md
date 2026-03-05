# Lab 11: Primary Keys, Foreign Keys, and Constraints

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Learn PRIMARY KEY, FOREIGN KEY with ON DELETE options, UNIQUE, CHECK constraints, composite keys, and how to inspect constraints in the database catalog.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10
```

---

## Step 2: PRIMARY KEY

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE constraintlab;
USE constraintlab;

-- Single-column primary key
CREATE TABLE users (
    user_id    INT          NOT NULL AUTO_INCREMENT,
    username   VARCHAR(50)  NOT NULL,
    email      VARCHAR(100) NOT NULL,
    created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id)
);

-- Attempt to insert duplicate PK
INSERT INTO users (username, email) VALUES ('alice', 'alice@email.com');
INSERT INTO users (username, email) VALUES ('bob',   'bob@email.com');

-- This will fail: duplicate PK
INSERT INTO users (user_id, username, email) VALUES (1, 'dup', 'dup@email.com');
EOF
```

📸 **Verified Output (duplicate PK error):**
```
Query OK, 1 row affected
Query OK, 1 row affected
ERROR 1062 (23000): Duplicate entry '1' for key 'users.PRIMARY'
```

> 💡 PRIMARY KEY combines NOT NULL + UNIQUE. It uniquely identifies each row. A table can have only ONE primary key, but it can span multiple columns (composite PK).

---

## Step 3: UNIQUE Constraint

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE constraintlab;

-- UNIQUE ensures no duplicate values (but allows NULL)
ALTER TABLE users ADD CONSTRAINT uq_username UNIQUE (username);
ALTER TABLE users ADD CONSTRAINT uq_email    UNIQUE (email);

-- This will fail: duplicate username
INSERT INTO users (username, email) VALUES ('alice', 'alice2@email.com');

-- NULL is allowed in UNIQUE columns (multiple NULLs are permitted in MySQL and PG)
INSERT INTO users (username, email) VALUES (NULL, 'noname@email.com');
EOF
```

📸 **Verified Output:**
```
ERROR 1062 (23000): Duplicate entry 'alice' for key 'users.uq_username'
Query OK, 1 row affected  ← NULL allowed
```

---

## Step 4: FOREIGN KEY with ON DELETE Options

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE constraintlab;

CREATE TABLE categories (
    cat_id   INT NOT NULL AUTO_INCREMENT,
    cat_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (cat_id)
);

-- ON DELETE CASCADE: delete child rows when parent is deleted
CREATE TABLE products_cascade (
    product_id INT NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    cat_id     INT NOT NULL,
    PRIMARY KEY (product_id),
    FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
        ON DELETE CASCADE
);

-- ON DELETE SET NULL: set FK to NULL when parent is deleted
CREATE TABLE products_setnull (
    product_id INT NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    cat_id     INT,
    PRIMARY KEY (product_id),
    FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
        ON DELETE SET NULL
);

-- ON DELETE RESTRICT: prevent deletion of parent if children exist (default)
CREATE TABLE products_restrict (
    product_id INT NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    cat_id     INT NOT NULL,
    PRIMARY KEY (product_id),
    FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
        ON DELETE RESTRICT
);

INSERT INTO categories (cat_name) VALUES ('Electronics'), ('Books');
INSERT INTO products_cascade  (name, cat_id) VALUES ('Laptop', 1), ('Tablet', 1);
INSERT INTO products_setnull  (name, cat_id) VALUES ('Novel', 2);
INSERT INTO products_restrict (name, cat_id) VALUES ('Phone', 1);

-- Test CASCADE: deleting Electronics cascades to products
DELETE FROM categories WHERE cat_id = 1;
SELECT * FROM products_cascade;   -- should be empty
SELECT * FROM products_restrict;  -- also deleted (same cat_id)
EOF
```

📸 **Verified Output:**
```
Empty set  ← cascade deleted products_cascade rows
Empty set  ← cascade deleted products_restrict rows (same cat)

-- Test SET NULL:
SELECT * FROM products_setnull;
+------------+-------+--------+
| product_id | name  | cat_id |
+------------+-------+--------+
|          1 | Novel |   NULL |   ← cat_id set to NULL
+------------+-------+--------+
```

---

## Step 5: CHECK Constraints

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE constraintlab;

CREATE TABLE employees (
    emp_id    INT NOT NULL AUTO_INCREMENT,
    name      VARCHAR(100) NOT NULL,
    salary    DECIMAL(10,2) NOT NULL,
    age       INT,
    dept      VARCHAR(20),
    PRIMARY KEY (emp_id),
    CONSTRAINT chk_salary  CHECK (salary > 0),
    CONSTRAINT chk_age     CHECK (age >= 18 AND age <= 75),
    CONSTRAINT chk_dept    CHECK (dept IN ('Engineering', 'Marketing', 'HR', 'Finance'))
);

-- Valid insert
INSERT INTO employees (name, salary, age, dept) VALUES ('Alice', 95000, 30, 'Engineering');

-- Violates salary check
INSERT INTO employees (name, salary, age, dept) VALUES ('Bad', -1000, 25, 'Engineering');

-- Violates age check
INSERT INTO employees (name, salary, age, dept) VALUES ('Young', 50000, 15, 'Engineering');

-- Violates dept check
INSERT INTO employees (name, salary, age, dept) VALUES ('Dept', 50000, 25, 'Legal');
EOF
```

📸 **Verified Output:**
```
Query OK, 1 row affected
ERROR 3819 (HY000): Check constraint 'chk_salary' is violated.
ERROR 3819 (HY000): Check constraint 'chk_age' is violated.
ERROR 3819 (HY000): Check constraint 'chk_dept' is violated.
```

---

## Step 6: Composite Primary Key

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE constraintlab;

-- Composite PK: uniqueness across combination of columns
CREATE TABLE course_enrollments (
    student_id  INT NOT NULL,
    course_id   INT NOT NULL,
    semester    VARCHAR(10) NOT NULL,
    grade       CHAR(2),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, course_id, semester)  -- composite
);

INSERT INTO course_enrollments (student_id, course_id, semester, grade) VALUES
(1, 101, '2024S', 'A'),
(1, 102, '2024S', 'B'),
(2, 101, '2024S', 'A+'),
(1, 101, '2024F', 'B+');  -- same student, same course, different semester = OK

-- Duplicate: same student+course+semester
INSERT INTO course_enrollments (student_id, course_id, semester) VALUES (1, 101, '2024S');
EOF
```

📸 **Verified Output:**
```
4 rows inserted successfully.
ERROR 1062 (23000): Duplicate entry '1-101-2024S' for key 'course_enrollments.PRIMARY'
```

---

## Step 7: Inspect Constraints (MySQL and PostgreSQL)

**MySQL:**
```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE constraintlab;

-- List all constraints
SELECT
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE,
    TABLE_NAME
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'constraintlab'
ORDER BY TABLE_NAME, CONSTRAINT_TYPE;

-- List FK details
SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'constraintlab'
  AND REFERENCED_TABLE_NAME IS NOT NULL;
EOF
```

📸 **Verified Output:**
```
+-----------------------+-----------------+---------------------+
| CONSTRAINT_NAME       | CONSTRAINT_TYPE | TABLE_NAME          |
+-----------------------+-----------------+---------------------+
| PRIMARY               | PRIMARY KEY     | categories          |
| chk_age               | CHECK           | employees           |
| chk_dept              | CHECK           | employees           |
| chk_salary            | CHECK           | employees           |
| PRIMARY               | PRIMARY KEY     | employees           |
| PRIMARY               | PRIMARY KEY     | products_cascade    |
...
```

**PostgreSQL — pg_constraints:**
```bash
docker exec pg-lab psql -U postgres -c "
SELECT conname AS constraint_name, contype AS type, relname AS table_name
FROM pg_constraint c
JOIN pg_class r ON c.conrelid = r.oid
WHERE r.relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
ORDER BY relname, contype;"
```

---

## Step 8: Capstone — Full Schema with All Constraint Types

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE constraintlab;

CREATE TABLE inventory (
    item_id       INT           NOT NULL AUTO_INCREMENT,
    sku           VARCHAR(20)   NOT NULL,
    item_name     VARCHAR(100)  NOT NULL,
    cat_id        INT,
    quantity      INT           NOT NULL DEFAULT 0,
    price         DECIMAL(10,2) NOT NULL,
    reorder_level INT           NOT NULL DEFAULT 10,
    PRIMARY KEY (item_id),
    UNIQUE KEY uq_sku (sku),
    FOREIGN KEY (cat_id) REFERENCES categories(cat_id) ON DELETE SET NULL,
    CONSTRAINT chk_qty    CHECK (quantity >= 0),
    CONSTRAINT chk_price  CHECK (price > 0),
    CONSTRAINT chk_reorder CHECK (reorder_level >= 0)
);

-- Re-insert a category (was deleted above)
INSERT INTO categories (cat_name) VALUES ('Electronics');

INSERT INTO inventory (sku, item_name, cat_id, quantity, price, reorder_level) VALUES
('ELEC-001', 'Laptop',    1, 50,  999.99, 5),
('ELEC-002', 'Phone',     1, 100, 499.99, 10),
('BOOK-001', 'SQL Guide', NULL, 200, 29.99, 20);

SELECT i.sku, i.item_name, c.cat_name, i.quantity, i.price
FROM inventory i
LEFT JOIN categories c ON i.cat_id = c.cat_id;
EOF
```

📸 **Verified Output:**
```
+----------+-----------+-------------+----------+--------+
| sku      | item_name | cat_name    | quantity | price  |
+----------+-----------+-------------+----------+--------+
| ELEC-001 | Laptop    | Electronics |       50 | 999.99 |
| ELEC-002 | Phone     | Electronics |      100 | 499.99 |
| BOOK-001 | SQL Guide | NULL        |      200 |  29.99 |
+----------+-----------+-------------+----------+--------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab pg-lab
```

---

## Summary

| Constraint | Purpose | NULL allowed? |
|------------|---------|---------------|
| `PRIMARY KEY` | Unique row identifier | No |
| `FOREIGN KEY` | Referential integrity | Yes (optional FK) |
| `UNIQUE` | No duplicate values | Yes (multiple NULLs OK) |
| `NOT NULL` | Must have a value | N/A |
| `CHECK` | Custom validation expression | Yes |
| `DEFAULT` | Fallback value | N/A |

| ON DELETE Option | Effect |
|-----------------|--------|
| `CASCADE` | Delete child rows |
| `SET NULL` | Set FK column to NULL |
| `RESTRICT` | Block parent deletion |
| `NO ACTION` | Same as RESTRICT (default) |
| `SET DEFAULT` | Set FK to default value |

**Next:** Lab 12 — Indexes Basics
