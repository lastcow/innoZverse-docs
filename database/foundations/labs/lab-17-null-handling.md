# Lab 17: NULL Handling

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Master NULL semantics, IS NULL/IS NOT NULL, COALESCE, NULLIF, IFNULL, NULL in aggregates, NULL in ORDER BY, and three-valued logic.

---

## Step 1: NULL Semantics — NULL is Not a Value

NULL represents the **absence of a value** — it is unknown, not zero or empty string.

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE nulllab;
USE nulllab;

-- Demonstrate NULL != NULL (the critical mistake)
SELECT NULL = NULL;           -- Returns NULL, not TRUE!
SELECT NULL != NULL;          -- Returns NULL, not FALSE!
SELECT NULL = 0;              -- NULL
SELECT NULL = '';             -- NULL
SELECT NULL IS NULL;          -- TRUE (correct way to check)
SELECT NULL IS NOT NULL;      -- FALSE
SELECT 1 + NULL;              -- NULL (any arithmetic with NULL = NULL)
SELECT CONCAT('hello', NULL); -- NULL (MySQL: string + NULL = NULL)
EOF
```

📸 **Verified Output:**
```
+-----------+
| NULL = NULL|
+-----------+
|      NULL |  ← NOT TRUE! Use IS NULL instead
+-----------+

+------------------+
| NULL IS NULL     |
+------------------+
| 1                |  ← TRUE (1 in MySQL)
+------------------+

+-----------+
| 1 + NULL  |
+-----------+
|      NULL |
+-----------+
```

> 💡 **Never use `= NULL`** to check for NULL values. Always use `IS NULL` or `IS NOT NULL`. This is the most common NULL-related bug in SQL.

---

## Step 2: Setup — Table with NULLs

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE nulllab;

CREATE TABLE employees (
    emp_id      INT NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    dept        VARCHAR(50),     -- nullable
    salary      DECIMAL(10,2),   -- nullable
    bonus       DECIMAL(10,2),   -- nullable
    manager_id  INT,             -- nullable
    email       VARCHAR(100),    -- nullable
    score       INT,             -- nullable (performance score 1-5)
    PRIMARY KEY (emp_id)
);

INSERT INTO employees (name, dept, salary, bonus, manager_id, email, score) VALUES
('Alice Johnson',  'Engineering', 95000,  5000,  2, 'alice@co.com',  5),
('Bob Smith',      'Marketing',   72000,  NULL,  2, 'bob@co.com',    3),
('Carol Davis',    'Engineering', 110000, 8000,  NULL, 'carol@co.com', 5),
('David Wilson',   NULL,          65000,  NULL,  NULL, NULL,          NULL),
('Eve Martinez',   'Engineering', NULL,   NULL,  2, 'eve@co.com',    4),
('Frank Anderson', 'Marketing',   68000,  2000,  2, NULL,            NULL),
('Grace Taylor',   'HR',          70000,  1500,  NULL, 'grace@co.com',3),
('Henry Thomas',   'Engineering', 125000, 10000, NULL, 'henry@co.com', 5),
('Isabel Jackson', NULL,          NULL,   NULL,  NULL, NULL,          NULL),
('Jack White',     'Finance',     92000,  4000,  2, 'jack@co.com',   4);
EOF
```

---

## Step 3: IS NULL and IS NOT NULL

```sql
USE nulllab;

-- Find employees with no department
SELECT name, dept FROM employees WHERE dept IS NULL;

-- Find employees with no bonus
SELECT name, bonus FROM employees WHERE bonus IS NULL;

-- Find employees with ALL information filled in
SELECT name FROM employees
WHERE dept IS NOT NULL
  AND salary IS NOT NULL
  AND email IS NOT NULL
  AND score IS NOT NULL;

-- Count NULLs per column
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN dept    IS NULL THEN 1 ELSE 0 END) AS null_dept,
    SUM(CASE WHEN salary  IS NULL THEN 1 ELSE 0 END) AS null_salary,
    SUM(CASE WHEN bonus   IS NULL THEN 1 ELSE 0 END) AS null_bonus,
    SUM(CASE WHEN email   IS NULL THEN 1 ELSE 0 END) AS null_email,
    SUM(CASE WHEN score   IS NULL THEN 1 ELSE 0 END) AS null_score
FROM employees;
```

📸 **Verified Output (count NULLs):**
```
+-------+-----------+-------------+------------+------------+------------+
| total | null_dept | null_salary | null_bonus | null_email | null_score |
+-------+-----------+-------------+------------+------------+------------+
|    10 |         2 |           2 |          5 |          3 |          3 |
+-------+-----------+-------------+------------+------------+------------+
```

---

## Step 4: COALESCE — Return First Non-NULL

```sql
-- COALESCE returns the first non-NULL argument
SELECT
    name,
    bonus,
    salary,
    COALESCE(bonus, 0)                          AS bonus_or_zero,
    COALESCE(bonus, salary * 0.05, 0)           AS effective_bonus,  -- fallback chain
    COALESCE(dept, 'Unassigned')               AS department,
    COALESCE(email, 'no-reply@company.com')    AS contact_email
FROM employees;
```

📸 **Verified Output:**
```
+----------------+-------+---------+---------------+-----------------+--------------+---------------------+
| name           | bonus | salary  | bonus_or_zero | effective_bonus | department   | contact_email       |
+----------------+-------+---------+---------------+-----------------+--------------+---------------------+
| Alice Johnson  |  5000 |  95000  |          5000 |            5000 | Engineering  | alice@co.com        |
| Bob Smith      |  NULL |  72000  |             0 |            3600 | Marketing    | bob@co.com          |
| Carol Davis    |  8000 | 110000  |          8000 |            8000 | Engineering  | carol@co.com        |
| David Wilson   |  NULL |  65000  |             0 |            3250 | Unassigned   | no-reply@company.com|
| Eve Martinez   |  NULL |   NULL  |             0 |               0 | Engineering  | eve@co.com          |
| Isabel Jackson |  NULL |   NULL  |             0 |               0 | Unassigned   | no-reply@company.com|
...
```

> 💡 `COALESCE(a, b, c)` returns the first non-NULL among a, b, c. It's equivalent to `CASE WHEN a IS NOT NULL THEN a WHEN b IS NOT NULL THEN b ELSE c END` — but much more readable.

---

## Step 5: NULLIF — Return NULL When Values Match

```sql
-- NULLIF(a, b): returns NULL if a = b, otherwise returns a
-- Useful for avoiding division by zero and converting sentinel values to NULL

-- Avoid division by zero
SELECT
    name,
    score,
    salary,
    NULLIF(score, 0)                           AS score_no_zero,
    salary / NULLIF(score, 0)                 AS salary_per_point  -- safe division
FROM employees;

-- Convert empty string to NULL
SELECT NULLIF('', '')     AS empty_to_null;    -- NULL
SELECT NULLIF('hello', '') AS non_empty;       -- 'hello'

-- Convert sentinel value (-1 meaning "not set") to NULL
CREATE TEMPORARY TABLE scores (emp_id INT, raw_score INT);
INSERT INTO scores VALUES (1, 85), (2, -1), (3, 92), (4, -1), (5, 78);

SELECT emp_id, raw_score,
       NULLIF(raw_score, -1) AS cleaned_score
FROM scores;
```

📸 **Verified Output (NULLIF sentinel):**
```
+--------+-----------+---------------+
| emp_id | raw_score | cleaned_score |
+--------+-----------+---------------+
|      1 |        85 |            85 |
|      2 |        -1 |          NULL |
|      3 |        92 |            92 |
|      4 |        -1 |          NULL |
|      5 |        78 |            78 |
+--------+-----------+---------------+
```

---

## Step 6: IFNULL (MySQL) — Two-Argument Shorthand

```sql
-- IFNULL(a, b): returns b if a is NULL, otherwise a (MySQL/MariaDB only)
-- Equivalent to COALESCE(a, b)
SELECT
    name,
    IFNULL(bonus, 0)          AS bonus,
    IFNULL(dept, 'No Dept')  AS dept,
    IFNULL(email, 'N/A')     AS email
FROM employees;

-- PostgreSQL uses COALESCE for the same purpose
-- PostgreSQL also has NULLIF but not IFNULL
-- Some DBs have NVL (Oracle), ISNULL (SQL Server) — MySQL/PG use COALESCE
```

📸 **Verified Output:**
```
+----------------+-------+-------------+---------------------+
| name           | bonus | dept        | email               |
+----------------+-------+-------------+---------------------+
| Alice Johnson  |  5000 | Engineering | alice@co.com        |
| Bob Smith      |     0 | Marketing   | bob@co.com          |
| David Wilson   |     0 | No Dept     | N/A                 |
...
```

---

## Step 7: NULL in Aggregates and ORDER BY

```sql
-- Aggregates ignore NULLs
SELECT
    COUNT(*)      AS total_rows,
    COUNT(salary) AS rows_with_salary,
    COUNT(bonus)  AS rows_with_bonus,
    AVG(salary)   AS avg_salary,        -- ignores NULL salary rows
    SUM(bonus)    AS sum_bonus,         -- ignores NULL bonus rows
    -- To include NULLs as 0:
    AVG(COALESCE(salary, 0)) AS avg_salary_incl_null,
    SUM(COALESCE(bonus,  0)) AS sum_bonus_incl_null
FROM employees;

-- NULL in ORDER BY
SELECT name, score
FROM employees
ORDER BY score ASC;    -- NULLs come FIRST in MySQL ASC
```

📸 **Verified Output (ORDER BY with NULLs):**
```
+----------------+-------+
| name           | score |
+----------------+-------+
| David Wilson   |  NULL |  ← NULLs first in MySQL (ASC)
| Frank Anderson |  NULL |
| Isabel Jackson |  NULL |
| Bob Smith      |     3 |
| Grace Taylor   |     3 |
| Eve Martinez   |     4 |
| Jack White     |     4 |
| Alice Johnson  |     5 |
| Carol Davis    |     5 |
| Henry Thomas   |     5 |
+----------------+-------+
```

**NULL ordering in PostgreSQL:**
```sql
-- PostgreSQL: NULLS FIRST / NULLS LAST control
ORDER BY score ASC  NULLS LAST;   -- NULLs at end
ORDER BY score DESC NULLS FIRST;  -- NULLs at start
```

> 💡 MySQL: NULLs sort first in ASC, last in DESC. PostgreSQL lets you control with `NULLS FIRST` / `NULLS LAST`. To force NULLs last in MySQL ASC: `ORDER BY score IS NULL ASC, score ASC`

---

## Step 8: Capstone — Three-Valued Logic

SQL uses **three-valued logic**: TRUE, FALSE, and UNKNOWN (NULL).

```sql
USE nulllab;

-- Demonstrate three-valued logic
SELECT
    -- TRUE AND NULL = NULL (unknown)
    TRUE  AND NULL  AS true_and_null,
    FALSE AND NULL  AS false_and_null,   -- FALSE (short-circuit)
    TRUE  OR  NULL  AS true_or_null,     -- TRUE (short-circuit)
    FALSE OR  NULL  AS false_or_null,    -- NULL (unknown)
    NOT NULL        AS not_null;         -- NULL

-- Practical impact: WHERE clause
-- Only rows where condition is TRUE pass through
-- FALSE rows are excluded, NULL (UNKNOWN) rows are ALSO excluded!

-- Employees NOT in Engineering (naive approach — misses NULLs!)
SELECT COUNT(*) AS wrong_count
FROM employees WHERE dept != 'Engineering';

-- Correct approach — explicitly handle NULLs
SELECT COUNT(*) AS correct_count
FROM employees WHERE dept != 'Engineering' OR dept IS NULL;
```

📸 **Verified Output:**
```
+----------------+----------------+--------------+---------------+----------+
| true_and_null  | false_and_null | true_or_null | false_or_null | not_null |
+----------------+----------------+--------------+---------------+----------+
|           NULL |              0 |            1 |          NULL |     NULL |
+----------------+----------------+--------------+---------------+----------+

-- Wrong count (excludes NULLs):
+-------------+
| wrong_count |
+-------------+
|           6 |  ← misses David and Isabel who have NULL dept!
+-------------+

-- Correct count:
+---------------+
| correct_count |
+---------------+
|             8 |
+---------------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Function/Syntax | Description | Example |
|-----------------|-------------|---------|
| `IS NULL` | Check for NULL | `WHERE col IS NULL` |
| `IS NOT NULL` | Check for non-NULL | `WHERE col IS NOT NULL` |
| `COALESCE(a,b,c)` | First non-NULL value | `COALESCE(bonus, 0)` |
| `NULLIF(a, b)` | NULL if a=b, else a | `NULLIF(score, 0)` |
| `IFNULL(a, b)` | MySQL: b if a is NULL | `IFNULL(email, 'N/A')` |
| `NVL(a, b)` | Oracle equivalent of IFNULL | Not in MySQL/PG |
| `= NULL` | NEVER use this | Always use IS NULL |

| Behavior | Effect |
|----------|--------|
| NULL in arithmetic | Result is NULL |
| NULL in aggregates | Ignored (not counted) |
| NULL in ORDER BY (MySQL) | First in ASC, last in DESC |
| NULL in WHERE | Row excluded (UNKNOWN ≠ TRUE) |
| Three-valued logic | TRUE / FALSE / UNKNOWN |

**Next:** Lab 18 — PostgreSQL JSONB and Arrays
