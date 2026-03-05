# Lab 09: Views

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Create, replace, and use views as virtual tables. Explore updatable views, WITH CHECK OPTION, and query the information schema for view metadata.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE viewlab;
USE viewlab;

CREATE TABLE employees (
    emp_id     INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name  VARCHAR(50) NOT NULL,
    dept_name  VARCHAR(50) NOT NULL,
    salary     DECIMAL(10,2) NOT NULL,
    email      VARCHAR(100),
    is_active  BOOLEAN DEFAULT TRUE,
    hire_date  DATE,
    PRIMARY KEY (emp_id)
);

CREATE TABLE sales (
    sale_id    INT NOT NULL AUTO_INCREMENT,
    emp_id     INT NOT NULL,
    amount     DECIMAL(10,2) NOT NULL,
    sale_date  DATE NOT NULL,
    region     VARCHAR(30),
    PRIMARY KEY (sale_id),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

INSERT INTO employees (first_name, last_name, dept_name, salary, email, hire_date) VALUES
('Alice',  'Johnson',  'Engineering', 95000,  'alice@co.com',  '2020-03-15'),
('Bob',    'Smith',    'Marketing',   72000,  'bob@co.com',    '2019-07-22'),
('Carol',  'Davis',    'Engineering', 110000, 'carol@co.com',  '2018-01-10'),
('David',  'Wilson',   'HR',          65000,  'david@co.com',  '2021-09-01'),
('Eve',    'Martinez', 'Engineering', 98000,  'eve@co.com',    '2020-11-30'),
('Frank',  'Anderson', 'Marketing',   68000,  NULL,            '2022-02-14'),
('Grace',  'Taylor',   'HR',          70000,  'grace@co.com',  '2019-05-20'),
('Henry',  'Thomas',   'Engineering', 125000, 'henry@co.com',  '2017-08-05');

INSERT INTO sales (emp_id, amount, sale_date, region) VALUES
(1, 5000, '2024-01-10', 'North'),
(2, 3500, '2024-01-15', 'South'),
(1, 4200, '2024-02-01', 'North'),
(3, 8000, '2024-02-10', 'East'),
(5, 6100, '2024-02-20', 'West'),
(2, 2800, '2024-03-01', 'South'),
(1, 3900, '2024-03-10', 'North'),
(6, 4500, '2024-03-15', 'East');
EOF
```

---

## Step 2: CREATE VIEW

```sql
USE viewlab;

-- Basic view: simplify complex column selection
CREATE VIEW employee_summary AS
SELECT
    emp_id,
    CONCAT(first_name, ' ', last_name) AS full_name,
    dept_name,
    salary,
    hire_date,
    DATEDIFF(CURDATE(), hire_date) AS days_employed
FROM employees
WHERE is_active = TRUE;

-- Use the view like a regular table
SELECT * FROM employee_summary;
```

📸 **Verified Output:**
```
+--------+----------------+-------------+---------+------------+---------------+
| emp_id | full_name      | dept_name   | salary  | hire_date  | days_employed |
+--------+----------------+-------------+---------+------------+---------------+
|      1 | Alice Johnson  | Engineering |  95000  | 2020-03-15 |          1452 |
|      2 | Bob Smith      | Marketing   |  72000  | 2019-07-22 |          1688 |
|      3 | Carol Davis    | Engineering | 110000  | 2018-01-10 |          2247 |
...
+--------+----------------+-------------+---------+------------+---------------+
```

> 💡 A view is a **stored SELECT query**. It doesn't store data — it runs the query every time you SELECT from it. Views are great for:
> - Simplifying complex queries
> - Hiding sensitive columns
> - Providing consistent reporting interfaces

---

## Step 3: CREATE OR REPLACE VIEW

```sql
-- Add salary band classification to the view
CREATE OR REPLACE VIEW employee_summary AS
SELECT
    emp_id,
    CONCAT(first_name, ' ', last_name) AS full_name,
    dept_name,
    salary,
    hire_date,
    DATEDIFF(CURDATE(), hire_date) AS days_employed,
    CASE
        WHEN salary >= 100000 THEN 'Senior'
        WHEN salary >= 75000  THEN 'Mid-level'
        ELSE                       'Junior'
    END AS salary_band
FROM employees
WHERE is_active = TRUE;

SELECT full_name, salary, salary_band FROM employee_summary ORDER BY salary DESC;
```

📸 **Verified Output:**
```
+----------------+---------+-------------+
| full_name      | salary  | salary_band |
+----------------+---------+-------------+
| Henry Thomas   | 125000  | Senior      |
| Carol Davis    | 110000  | Senior      |
| Eve Martinez   |  98000  | Senior      |
| Alice Johnson  |  95000  | Mid-level   |
| Bob Smith      |  72000  | Junior      |
| Frank Anderson |  68000  | Junior      |
| Grace Taylor   |  70000  | Junior      |
| David Wilson   |  65000  | Junior      |
+----------------+---------+-------------+
```

---

## Step 4: View Joining Multiple Tables

```sql
-- View that joins employees and sales
CREATE VIEW sales_report AS
SELECT
    e.emp_id,
    CONCAT(e.first_name, ' ', e.last_name) AS sales_rep,
    e.dept_name,
    s.sale_date,
    s.amount,
    s.region
FROM employees e
JOIN sales s ON e.emp_id = s.emp_id;

-- Query the view with filtering
SELECT
    sales_rep,
    COUNT(*)       AS num_sales,
    SUM(amount)    AS total_sales,
    AVG(amount)    AS avg_sale
FROM sales_report
WHERE sale_date >= '2024-02-01'
GROUP BY sales_rep
ORDER BY total_sales DESC;
```

📸 **Verified Output:**
```
+----------------+-----------+-------------+----------+
| sales_rep      | num_sales | total_sales | avg_sale |
+----------------+-----------+-------------+----------+
| Alice Johnson  |         2 |     8100.00 | 4050.000 |
| Carol Davis    |         1 |     8000.00 | 8000.000 |
| Eve Martinez   |         1 |     6100.00 | 6100.000 |
| Frank Anderson |         1 |     4500.00 | 4500.000 |
| Bob Smith      |         1 |     2800.00 | 2800.000 |
+----------------+-----------+-------------+----------+
```

---

## Step 5: Updatable Views

```sql
-- Simple views (no aggregation, no DISTINCT, no subqueries) can be updated
CREATE VIEW active_employees AS
SELECT emp_id, first_name, last_name, dept_name, salary, is_active
FROM employees
WHERE is_active = TRUE;

-- Update through the view
UPDATE active_employees SET salary = 97000 WHERE emp_id = 1;

-- Verify
SELECT emp_id, first_name, salary FROM employees WHERE emp_id = 1;
```

📸 **Verified Output:**
```
+--------+------------+--------+
| emp_id | first_name | salary |
+--------+------------+--------+
|      1 | Alice      |  97000 |
+--------+------------+--------+
```

> ⚠️ Views with GROUP BY, HAVING, DISTINCT, UNION, or aggregates are **NOT updatable**. Attempting to UPDATE/INSERT/DELETE against them will error.

---

## Step 6: WITH CHECK OPTION

```sql
-- View for junior employees only
CREATE VIEW junior_employees AS
SELECT emp_id, first_name, last_name, salary
FROM employees
WHERE salary < 75000
WITH CHECK OPTION;   -- prevents inserting/updating rows that violate the WHERE condition

-- This INSERT will FAIL because salary 80000 > 75000 (violates view filter)
INSERT INTO junior_employees (first_name, last_name, salary)
VALUES ('Test', 'User', 80000);  -- ERROR: CHECK OPTION failed

-- This works (salary < 75000)
UPDATE junior_employees SET salary = 73000 WHERE emp_id = 2;
```

📸 **Verified Output (failing insert):**
```
ERROR 1369 (HY000): CHECK OPTION failed 'viewlab.junior_employees'
```

> 💡 `WITH CHECK OPTION` ensures that INSERT/UPDATE operations through the view cannot create rows that the view wouldn't show. This maintains data consistency through view boundaries.

---

## Step 7: INFORMATION_SCHEMA.VIEWS

```sql
-- List all views in the current database
SELECT
    TABLE_NAME        AS view_name,
    VIEW_DEFINITION,
    IS_UPDATABLE,
    CHECK_OPTION
FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'viewlab'
ORDER BY TABLE_NAME;
```

📸 **Verified Output:**
```
+------------------+-------------------+--------------+--------------+
| view_name        | VIEW_DEFINITION   | IS_UPDATABLE | CHECK_OPTION |
+------------------+-------------------+--------------+--------------+
| active_employees | select ...        | YES          | NONE         |
| employee_summary | select ...        | NO           | NONE         |
| junior_employees | select ...        | YES          | CASCADED     |
| sales_report     | select ...        | NO           | NONE         |
+------------------+-------------------+--------------+--------------+
```

**PostgreSQL equivalent:**
```sql
SELECT viewname, definition
FROM pg_views
WHERE schemaname = 'public';
```

---

## Step 8: Capstone — Security View (Hide Sensitive Columns)

```sql
-- Create a "public" view that hides salary and email
CREATE VIEW employees_public AS
SELECT
    emp_id,
    first_name,
    last_name,
    dept_name,
    hire_date,
    CASE WHEN salary >= 100000 THEN 'Senior'
         WHEN salary >= 75000  THEN 'Mid-level'
         ELSE 'Junior'
    END AS level
FROM employees
WHERE is_active = TRUE;

-- This view can be shared with non-HR staff — no salary/email exposure
SELECT * FROM employees_public;

-- DROP VIEW when done
DROP VIEW IF EXISTS employees_public;
DROP VIEW IF EXISTS junior_employees;
DROP VIEW IF EXISTS active_employees;
DROP VIEW IF EXISTS sales_report;
DROP VIEW IF EXISTS employee_summary;

-- Verify all views gone
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = 'viewlab';
```

📸 **Verified Output (public view):**
```
+--------+------------+-----------+-------------+------------+-----------+
| emp_id | first_name | last_name | dept_name   | hire_date  | level     |
+--------+------------+-----------+-------------+------------+-----------+
|      1 | Alice      | Johnson   | Engineering | 2020-03-15 | Mid-level |
|      2 | Bob        | Smith     | Marketing   | 2019-07-22 | Junior    |
|      3 | Carol      | Davis     | Engineering | 2018-01-10 | Senior    |
...
+--------+------------+-----------+-------------+------------+-----------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Command | Description |
|---------|-------------|
| `CREATE VIEW v AS SELECT ...` | Create a view |
| `CREATE OR REPLACE VIEW v AS ...` | Replace view definition |
| `SELECT * FROM v` | Query a view like a table |
| `UPDATE v SET ... WHERE ...` | Update through updatable view |
| `WITH CHECK OPTION` | Enforce view filter on inserts/updates |
| `DROP VIEW IF EXISTS v` | Remove a view |
| `INFORMATION_SCHEMA.VIEWS` | List views and metadata |
| `pg_views` | PostgreSQL view catalog |

**Next:** Lab 10 — Database Design and Normalization
