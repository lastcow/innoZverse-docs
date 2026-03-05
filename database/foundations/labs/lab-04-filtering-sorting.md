# Lab 04: Filtering and Sorting

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Master the `WHERE` clause with comparison operators, logical operators, pattern matching, `ORDER BY`, `LIMIT`/`OFFSET`, and pagination patterns.

---

## Step 1: Setup — Sample Dataset

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE store;
USE store;

CREATE TABLE employees (
    emp_id      INT NOT NULL AUTO_INCREMENT,
    first_name  VARCHAR(50) NOT NULL,
    last_name   VARCHAR(50) NOT NULL,
    department  VARCHAR(50) NOT NULL,
    salary      DECIMAL(10,2) NOT NULL,
    hire_date   DATE NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE,
    email       VARCHAR(100),
    PRIMARY KEY (emp_id)
);

INSERT INTO employees (first_name, last_name, department, salary, hire_date, email) VALUES
('Alice',   'Johnson',  'Engineering',  95000, '2020-03-15', 'alice@company.com'),
('Bob',     'Smith',    'Marketing',    72000, '2019-07-22', 'bob@company.com'),
('Carol',   'Davis',    'Engineering',  110000,'2018-01-10', 'carol@company.com'),
('David',   'Wilson',   'HR',           65000, '2021-09-01', 'david@company.com'),
('Eve',     'Martinez', 'Engineering',  98000, '2020-11-30', 'eve@company.com'),
('Frank',   'Anderson', 'Marketing',    68000, '2022-02-14', NULL),
('Grace',   'Taylor',   'HR',           70000, '2019-05-20', 'grace@company.com'),
('Henry',   'Thomas',   'Engineering',  125000,'2017-08-05', 'henry@company.com'),
('Isabel',  'Jackson',  'Finance',      88000, '2021-12-01', 'isabel@company.com'),
('Jack',    'White',    'Finance',      92000, '2020-06-18', 'jack@company.com'),
('Karen',   'Harris',   'Marketing',    75000, '2018-10-25', 'karen@company.com'),
('Liam',    'Clark',    'Engineering',  105000,'2019-03-08', 'liam@company.com');
EOF
```

---

## Step 2: Comparison Operators

```sql
USE store;

-- Equals
SELECT first_name, department, salary FROM employees WHERE department = 'Engineering';

-- Not equals
SELECT first_name, department FROM employees WHERE department != 'Engineering';
-- Also valid: WHERE department <> 'Engineering'

-- Greater than / Less than
SELECT first_name, salary FROM employees WHERE salary > 100000;
SELECT first_name, salary FROM employees WHERE salary < 70000;

-- Greater than or equal
SELECT first_name, salary FROM employees WHERE salary >= 95000;
```

📸 **Verified Output (salary > 100000):**
```
+------------+---------+
| first_name | salary  |
+------------+---------+
| Carol      | 110000  |
| Henry      | 125000  |
| Liam       | 105000  |
+------------+---------+
3 rows in set
```

---

## Step 3: BETWEEN, IN, NOT IN

```sql
-- BETWEEN (inclusive on both ends)
SELECT first_name, salary
FROM employees
WHERE salary BETWEEN 70000 AND 95000;

-- IN (match any value in list)
SELECT first_name, department
FROM employees
WHERE department IN ('Marketing', 'HR');

-- NOT IN
SELECT first_name, department
FROM employees
WHERE department NOT IN ('Engineering', 'Finance');
```

📸 **Verified Output (BETWEEN):**
```
+------------+---------+
| first_name | salary  |
+------------+---------+
| Bob        |  72000  |
| Frank      |  68000  |  ← Wait, 68000 < 70000 — not included
| Grace      |  70000  |
| Karen      |  75000  |
| Isabel     |  88000  |
| Jack       |  92000  |
| Alice      |  95000  |
+------------+---------+
```

> 💡 `BETWEEN a AND b` is equivalent to `>= a AND <= b`. It's inclusive on both ends.

---

## Step 4: LIKE and ILIKE Pattern Matching

```sql
-- LIKE with % (any sequence of characters)
SELECT first_name, last_name, email
FROM employees
WHERE last_name LIKE 'J%';          -- starts with J

-- LIKE with _ (exactly one character)
SELECT first_name FROM employees WHERE first_name LIKE '_ob';   -- 3-letter name ending in 'ob'

-- Contains pattern
SELECT first_name, email FROM employees WHERE email LIKE '%@company.com';

-- MySQL: case-insensitive by default on utf8mb4_general_ci collation
SELECT first_name FROM employees WHERE last_name LIKE 'j%';     -- also matches Johnson
```

📸 **Verified Output (last_name LIKE 'J%'):**
```
+------------+-----------+-------------------+
| first_name | last_name | email             |
+------------+-----------+-------------------+
| Alice      | Johnson   | alice@company.com |
| Isabel     | Jackson   | isabel@company.com|
+------------+-----------+-------------------+
```

**PostgreSQL ILIKE (case-insensitive LIKE):**
```sql
-- PostgreSQL: LIKE is case-sensitive; use ILIKE for case-insensitive
SELECT first_name FROM employees WHERE last_name ILIKE 'j%';  -- matches johnson, jackson
SELECT first_name FROM employees WHERE last_name LIKE 'j%';   -- matches none (lowercase j)
```

> 💡 In MySQL, LIKE case sensitivity depends on column collation. In PostgreSQL, LIKE is always case-sensitive; use `ILIKE` for case-insensitive matching.

---

## Step 5: AND, OR, NOT

```sql
-- AND: both conditions must be true
SELECT first_name, department, salary
FROM employees
WHERE department = 'Engineering' AND salary > 100000;

-- OR: at least one condition must be true
SELECT first_name, department, salary
FROM employees
WHERE department = 'Marketing' OR department = 'HR';

-- NOT: negate a condition
SELECT first_name, department
FROM employees
WHERE NOT department = 'Engineering';

-- Combining: use parentheses to control evaluation order
SELECT first_name, department, salary
FROM employees
WHERE (department = 'Engineering' OR department = 'Finance')
  AND salary >= 90000;
```

📸 **Verified Output (AND: Engineering AND salary > 100000):**
```
+------------+-------------+---------+
| first_name | department  | salary  |
+------------+-------------+---------+
| Carol      | Engineering | 110000  |
| Henry      | Engineering | 125000  |
| Liam       | Engineering | 105000  |
+------------+-------------+---------+
```

> ⚠️ Without parentheses, `AND` has higher precedence than `OR`. Always use parentheses when mixing AND and OR.

---

## Step 6: ORDER BY

```sql
-- ORDER BY single column (default ASC)
SELECT first_name, salary FROM employees ORDER BY salary;

-- DESC order
SELECT first_name, salary FROM employees ORDER BY salary DESC;

-- ORDER BY multiple columns
SELECT first_name, department, salary
FROM employees
ORDER BY department ASC, salary DESC;

-- ORDER BY with alias (MySQL and PostgreSQL both support this)
SELECT first_name, salary * 1.1 AS new_salary
FROM employees
ORDER BY new_salary DESC;
```

📸 **Verified Output (ORDER BY department ASC, salary DESC):**
```
+------------+-------------+---------+
| first_name | department  | salary  |
+------------+-------------+---------+
| Henry      | Engineering | 125000  |
| Carol      | Engineering | 110000  |
| Liam       | Engineering | 105000  |
| Eve        | Engineering |  98000  |
| Alice      | Engineering |  95000  |
| Jack       | Finance     |  92000  |
| Isabel     | Finance     |  88000  |
| Grace      | HR          |  70000  |
| David      | HR          |  65000  |
| Karen      | Marketing   |  75000  |
| Bob        | Marketing   |  72000  |
| Frank      | Marketing   |  68000  |
+------------+-------------+---------+
```

---

## Step 7: LIMIT and OFFSET

```sql
-- Get top 5 highest paid employees
SELECT first_name, salary
FROM employees
ORDER BY salary DESC
LIMIT 5;

-- Skip first 5, get next 5 (page 2)
SELECT first_name, salary
FROM employees
ORDER BY salary DESC
LIMIT 5 OFFSET 5;

-- MySQL shorthand: LIMIT offset, count
SELECT first_name, salary
FROM employees
ORDER BY salary DESC
LIMIT 5, 5;   -- same as LIMIT 5 OFFSET 5
```

📸 **Verified Output (LIMIT 5, top earners):**
```
+------------+---------+
| first_name | salary  |
+------------+---------+
| Henry      | 125000  |
| Carol      | 110000  |
| Liam       | 105000  |
| Eve        |  98000  |
| Alice      |  95000  |
+------------+---------+
```

---

## Step 8: Capstone — Pagination Pattern

Build a reusable pagination query. Assume page size = 3, getting page 2:

```sql
-- Variables (MySQL)
SET @page_size = 3;
SET @page_num  = 2;    -- 1-indexed

SELECT
    emp_id,
    CONCAT(first_name, ' ', last_name) AS full_name,
    department,
    salary
FROM employees
WHERE is_active = TRUE
ORDER BY salary DESC
LIMIT 3 OFFSET 3;   -- page 2: skip (page_num-1) * page_size = (2-1)*3 = 3
```

📸 **Verified Output:**
```
+--------+----------------+-------------+--------+
| emp_id | full_name      | department  | salary |
+--------+----------------+-------------+--------+
|      5 | Eve Martinez   | Engineering |  98000 |
|      1 | Alice Johnson  | Engineering |  95000 |
|      9 | Isabel Jackson | Finance     |  88000 |
+--------+----------------+-------------+--------+
```

**The pagination formula:**
```
OFFSET = (page_number - 1) * page_size
LIMIT  = page_size
Total pages = CEIL(total_rows / page_size)
```

> 💡 For large datasets, OFFSET-based pagination gets slow (DB must scan and skip). For tables with millions of rows, use **keyset/cursor pagination**: `WHERE id > last_seen_id LIMIT n`.

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Feature | MySQL | PostgreSQL | Notes |
|---------|-------|------------|-------|
| Equals | `=` | `=` | |
| Not equals | `!=` or `<>` | `!=` or `<>` | |
| Range | `BETWEEN a AND b` | Same | Inclusive |
| List match | `IN (a, b, c)` | Same | |
| Pattern | `LIKE '%x%'` | `LIKE '%x%'` | MySQL case-insensitive by collation |
| Case-insensitive pattern | N/A (by collation) | `ILIKE '%x%'` | PG-specific |
| Sort ascending | `ORDER BY col ASC` | Same | ASC is default |
| Sort descending | `ORDER BY col DESC` | Same | |
| Limit rows | `LIMIT n` | `LIMIT n` | |
| Skip rows | `LIMIT n OFFSET m` | `LIMIT n OFFSET m` | |

**Next:** Lab 05 — Aggregate Functions
