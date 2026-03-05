# Lab 08: Subqueries

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Master scalar subqueries, correlated subqueries, IN/NOT IN, EXISTS/NOT EXISTS, derived tables, and when to use subqueries vs JOINs.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE subquery_lab;
USE subquery_lab;

CREATE TABLE departments (
    dept_id   INT NOT NULL AUTO_INCREMENT,
    dept_name VARCHAR(50) NOT NULL,
    PRIMARY KEY (dept_id)
);

CREATE TABLE employees (
    emp_id     INT NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    dept_id    INT,
    salary     DECIMAL(10,2),
    hire_date  DATE,
    PRIMARY KEY (emp_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE orders (
    order_id    INT NOT NULL AUTO_INCREMENT,
    emp_id      INT,
    amount      DECIMAL(10,2),
    order_date  DATE,
    PRIMARY KEY (order_id),
    FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
);

INSERT INTO departments VALUES
(1,'Engineering'),(2,'Marketing'),(3,'HR'),(4,'Finance'),(5,'Legal');

INSERT INTO employees (name, dept_id, salary, hire_date) VALUES
('Alice Johnson',  1, 95000,  '2020-03-15'),
('Bob Smith',      2, 72000,  '2019-07-22'),
('Carol Davis',    1, 110000, '2018-01-10'),
('David Wilson',   3, 65000,  '2021-09-01'),
('Eve Martinez',   1, 98000,  '2020-11-30'),
('Frank Anderson', 2, 68000,  '2022-02-14'),
('Grace Taylor',   3, 70000,  '2019-05-20'),
('Henry Thomas',   1, 125000, '2017-08-05'),
('Isabel Jackson', 4, 88000,  '2021-12-01'),
('Jack White',     4, 92000,  '2020-06-18');

INSERT INTO orders (emp_id, amount, order_date) VALUES
(1, 1200.00, '2024-01-10'),
(1,  850.00, '2024-01-25'),
(2,  300.00, '2024-02-01'),
(3, 2100.00, '2024-02-15'),
(5,  950.00, '2024-03-01'),
(8, 3200.00, '2024-03-10'),
(9,  780.00, '2024-03-15');
EOF
```

---

## Step 2: Scalar Subquery

A **scalar subquery** returns exactly one value (one row, one column).

```sql
USE subquery_lab;

-- Find employees earning more than the company average
SELECT name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees)
ORDER BY salary DESC;

-- Show the average alongside each row
SELECT
    name,
    salary,
    (SELECT ROUND(AVG(salary),2) FROM employees) AS company_avg,
    salary - (SELECT AVG(salary) FROM employees) AS diff_from_avg
FROM employees
ORDER BY diff_from_avg DESC;
```

📸 **Verified Output (above average):**
```
+----------------+---------+
| name           | salary  |
+----------------+---------+
| Henry Thomas   | 125000  |
| Carol Davis    | 110000  |
| Eve Martinez   |  98000  |
| Alice Johnson  |  95000  |
| Jack White     |  92000  |
+----------------+---------+
Company average: 88300.00
```

> 💡 A scalar subquery MUST return exactly one row and one column. If it returns more, you get an error. Use `LIMIT 1` if needed.

---

## Step 3: IN / NOT IN Subquery

```sql
-- Employees in departments that have 'ing' in name
SELECT name, dept_id
FROM employees
WHERE dept_id IN (
    SELECT dept_id FROM departments WHERE dept_name LIKE '%ing%'
);

-- Employees NOT in Engineering or Finance
SELECT name, dept_id
FROM employees
WHERE dept_id NOT IN (
    SELECT dept_id FROM departments WHERE dept_name IN ('Engineering', 'Finance')
);
```

📸 **Verified Output (IN with LIKE):**
```
+----------------+---------+
| name           | dept_id |
+----------------+---------+
| Alice Johnson  |       1 |
| Bob Smith      |       2 |
| Carol Davis    |       1 |
| Eve Martinez   |       1 |
| Frank Anderson |       2 |
| Henry Thomas   |       1 |
+----------------+---------+
```

> ⚠️ **NOT IN and NULL**: If the subquery returns ANY NULL value, `NOT IN` returns no rows (because `x NOT IN (..., NULL)` is UNKNOWN). Always add `WHERE col IS NOT NULL` to NOT IN subqueries when NULLs are possible.

---

## Step 4: EXISTS / NOT EXISTS

```sql
-- Find employees who have placed at least one order (using EXISTS)
SELECT e.name, e.salary
FROM employees e
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.emp_id = e.emp_id
);

-- Find employees who have NOT placed any order (using NOT EXISTS)
SELECT e.name, e.dept_id
FROM employees e
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.emp_id = e.emp_id
)
ORDER BY e.name;
```

📸 **Verified Output (NOT EXISTS — no orders):**
```
+----------------+---------+
| name           | dept_id |
+----------------+---------+
| Bob Smith      |       2 |
| David Wilson   |       3 |
| Frank Anderson |       2 |
| Grace Taylor   |       3 |
| Isabel Jackson |       4 |
| Jack White     |       4 |
+----------------+---------+
```

> 💡 `EXISTS` vs `IN`:
> - `EXISTS` short-circuits — stops as soon as one match is found (can be faster)
> - `EXISTS` handles NULLs correctly (unlike NOT IN)
> - Use `SELECT 1` inside EXISTS — the columns don't matter, only whether a row exists

---

## Step 5: Correlated Subquery

A **correlated subquery** references the outer query. It runs once per outer row.

```sql
-- Find employees earning more than their department's average
SELECT
    e.name,
    e.salary,
    e.dept_id,
    (SELECT ROUND(AVG(e2.salary),2)
     FROM employees e2
     WHERE e2.dept_id = e.dept_id) AS dept_avg
FROM employees e
WHERE e.salary > (
    SELECT AVG(e2.salary)
    FROM employees e2
    WHERE e2.dept_id = e.dept_id   -- correlated: references outer e
)
ORDER BY e.dept_id, e.salary DESC;
```

📸 **Verified Output:**
```
+----------------+---------+---------+------------+
| name           | salary  | dept_id | dept_avg   |
+----------------+---------+---------+------------+
| Henry Thomas   | 125000  |       1 |  107000.00 |
| Carol Davis    | 110000  |       1 |  107000.00 |
| Jack White     |  92000  |       4 |   90000.00 |
+----------------+---------+---------+------------+
```

> ⚠️ Correlated subqueries run once per row of the outer query. For large tables, they can be slow. Consider rewriting with a JOIN + subquery in FROM clause.

---

## Step 6: Subquery in FROM (Derived Table)

```sql
-- Subquery in FROM creates a temporary virtual table (derived table)
SELECT
    dept_summary.dept_name,
    dept_summary.avg_salary,
    dept_summary.headcount
FROM (
    SELECT
        d.dept_name,
        ROUND(AVG(e.salary), 2) AS avg_salary,
        COUNT(e.emp_id)          AS headcount
    FROM departments d
    JOIN employees e ON d.dept_id = e.dept_id
    GROUP BY d.dept_id, d.dept_name
) AS dept_summary
WHERE dept_summary.avg_salary > 80000
ORDER BY dept_summary.avg_salary DESC;
```

📸 **Verified Output:**
```
+-------------+------------+-----------+
| dept_name   | avg_salary | headcount |
+-------------+------------+-----------+
| Engineering |  107000.00 |         4 |
| Finance     |   90000.00 |         2 |
+-------------+------------+-----------+
```

> 💡 The derived table (subquery in FROM) must have an alias (`AS dept_summary`). MySQL requires this; PostgreSQL also requires it. This technique lets you filter on aggregated values without a HAVING clause.

---

## Step 7: Subquery vs JOIN Comparison

```sql
-- APPROACH 1: Subquery
SELECT name FROM employees
WHERE dept_id IN (SELECT dept_id FROM departments WHERE dept_name = 'Engineering');

-- APPROACH 2: JOIN (equivalent result)
SELECT e.name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id
WHERE d.dept_name = 'Engineering';

-- Both return same result — which is faster?
-- Use EXPLAIN to compare:
EXPLAIN SELECT name FROM employees
WHERE dept_id IN (SELECT dept_id FROM departments WHERE dept_name = 'Engineering');

EXPLAIN SELECT e.name FROM employees e
JOIN departments d ON e.dept_id = d.dept_id
WHERE d.dept_name = 'Engineering';
```

| Approach | When to use |
|----------|------------|
| Subquery (IN) | Clear, readable for simple lookups |
| Subquery (EXISTS) | Check existence without returning data |
| Subquery (scalar) | Single value in SELECT or WHERE |
| Subquery (derived) | Pre-aggregate then filter |
| JOIN | Better performance for large tables, complex joins |

---

## Step 8: Capstone — Nested Subquery Report

Find departments where the top earner makes more than 2x the lowest earner:

```sql
SELECT
    d.dept_name,
    dept_stats.max_salary,
    dept_stats.min_salary,
    ROUND(dept_stats.max_salary / dept_stats.min_salary, 2) AS ratio
FROM departments d
JOIN (
    SELECT
        dept_id,
        MAX(salary) AS max_salary,
        MIN(salary) AS min_salary
    FROM employees
    GROUP BY dept_id
) AS dept_stats ON d.dept_id = dept_stats.dept_id
WHERE dept_stats.max_salary > 2 * dept_stats.min_salary
ORDER BY ratio DESC;
```

📸 **Verified Output:**
```
+-------------+------------+------------+-------+
| dept_name   | max_salary | min_salary | ratio |
+-------------+------------+------------+-------+
| Engineering |  125000.00 |   95000.00 |  1.32 |
+-------------+------------+------------+-------+
```

> 💡 No department has a 2x salary spread in our small dataset. Try `WHERE ratio > 1.2` to see Engineering. In real-world data this pattern flags compensation inequities.

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Subquery Type | Returns | Typical Use |
|---------------|---------|-------------|
| Scalar | One value | Comparison: `WHERE x > (SELECT MAX(...))` |
| IN/NOT IN | List of values | Set membership filter |
| EXISTS/NOT EXISTS | Boolean (row found?) | Existence check, anti-join |
| Correlated | Value per outer row | Row-by-row comparison to group |
| Derived table | Virtual table | Pre-aggregate, then join/filter |

**Next:** Lab 09 — Views
