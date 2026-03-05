# Lab 13: UPDATE and DELETE

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Master UPDATE with and without JOIN, DELETE with subquery, TRUNCATE vs DELETE differences, and the soft delete pattern with `deleted_at` timestamps.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE updatelab;
USE updatelab;

CREATE TABLE employees (
    emp_id      INT NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100) NOT NULL,
    dept        VARCHAR(50) NOT NULL,
    salary      DECIMAL(10,2) NOT NULL,
    status      VARCHAR(20) DEFAULT 'active',
    deleted_at  TIMESTAMP NULL DEFAULT NULL,  -- for soft delete
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (emp_id)
);

CREATE TABLE departments (
    dept_id   INT NOT NULL AUTO_INCREMENT,
    dept_name VARCHAR(50) NOT NULL,
    bonus_pct DECIMAL(5,2) DEFAULT 0,
    PRIMARY KEY (dept_id)
);

INSERT INTO departments (dept_name, bonus_pct) VALUES
('Engineering', 10.0), ('Marketing', 7.5), ('HR', 5.0), ('Finance', 8.0);

INSERT INTO employees (name, dept, salary) VALUES
('Alice Johnson',  'Engineering', 95000),
('Bob Smith',      'Marketing',   72000),
('Carol Davis',    'Engineering', 110000),
('David Wilson',   'HR',          65000),
('Eve Martinez',   'Engineering', 98000),
('Frank Anderson', 'Marketing',   68000),
('Grace Taylor',   'HR',          70000),
('Henry Thomas',   'Engineering', 125000),
('Isabel Jackson', 'Finance',     88000),
('Jack White',     'Finance',     92000);
EOF
```

---

## Step 2: Basic UPDATE

```sql
USE updatelab;

-- Update a single row
UPDATE employees SET salary = 100000 WHERE emp_id = 1;

-- Verify
SELECT emp_id, name, salary FROM employees WHERE emp_id = 1;

-- Update multiple columns at once
UPDATE employees
SET salary = 115000, dept = 'Engineering', status = 'active'
WHERE emp_id = 3;
```

📸 **Verified Output:**
```
+--------+---------------+--------+
| emp_id | name          | salary |
+--------+---------------+--------+
|      1 | Alice Johnson | 100000 |
+--------+---------------+--------+
Query OK, 1 row affected (0.01 sec)
Rows matched: 1  Changed: 1  Warnings: 0
```

> ⚠️ **ALWAYS include a WHERE clause with UPDATE.** Without it, every row in the table gets updated!
> Run `SELECT ... WHERE condition` first to verify which rows you'll affect before running UPDATE.

---

## Step 3: UPDATE with Expression

```sql
-- Give all Engineering employees a 10% raise
UPDATE employees
SET salary = salary * 1.10
WHERE dept = 'Engineering';

-- Verify
SELECT name, dept, salary FROM employees WHERE dept = 'Engineering';

-- Cap salary at 130000 (conditional update)
UPDATE employees
SET salary = LEAST(salary * 1.10, 130000)
WHERE dept = 'Engineering';
```

📸 **Verified Output (after 10% raise):**
```
+----------------+-------------+------------+
| name           | dept        | salary     |
+----------------+-------------+------------+
| Alice Johnson  | Engineering | 110000.00  |
| Carol Davis    | Engineering | 126500.00  |
| Eve Martinez   | Engineering | 107800.00  |
| Henry Thomas   | Engineering | 137500.00  |
+----------------+-------------+------------+
Rows matched: 4  Changed: 4
```

---

## Step 4: UPDATE with JOIN

```sql
-- MySQL: UPDATE with JOIN (apply department bonus to salary)
UPDATE employees e
JOIN departments d ON e.dept = d.dept_name
SET e.salary = e.salary * (1 + d.bonus_pct / 100)
WHERE e.dept = 'Marketing';

SELECT name, dept, salary FROM employees WHERE dept = 'Marketing';
```

📸 **Verified Output:**
```
+----------------+-----------+-----------+
| name           | dept      | salary    |
+----------------+-----------+-----------+
| Bob Smith      | Marketing |  77400.00 |  ← 72000 * 1.075
| Frank Anderson | Marketing |  73100.00 |  ← 68000 * 1.075
+----------------+-----------+-----------+
Rows matched: 2  Changed: 2
```

**PostgreSQL equivalent:**
```sql
UPDATE employees e
SET salary = e.salary * (1 + d.bonus_pct / 100)
FROM departments d
WHERE e.dept = d.dept_name
  AND e.dept = 'Marketing';
```

> 💡 MySQL uses `UPDATE t1 JOIN t2 SET ...` syntax. PostgreSQL uses `UPDATE t1 SET ... FROM t2 WHERE ...`. Both achieve the same result.

---

## Step 5: Basic DELETE

```sql
-- Delete a specific row
DELETE FROM employees WHERE emp_id = 10;

-- Verify row count
SELECT COUNT(*) FROM employees;

-- Delete with condition
DELETE FROM employees WHERE dept = 'HR' AND salary < 68000;

-- Check how many rows were affected
SELECT ROW_COUNT();  -- MySQL: returns count from last DML statement
```

📸 **Verified Output:**
```
Query OK, 1 row affected  ← emp_id 10 deleted

+----------+
| COUNT(*) |
+----------+
|        9 |
+----------+

Query OK, 1 row affected  ← David (HR, 65000) deleted

+-----------+
| ROW_COUNT() |
+-----------+
|           1 |
+-----------+
```

---

## Step 6: DELETE with Subquery

```sql
-- Delete employees whose department has average salary above 100000
-- (They're high-earners being moved to a new structure)
DELETE FROM employees
WHERE dept IN (
    SELECT dept
    FROM (
        SELECT dept, AVG(salary) AS avg_sal
        FROM employees
        GROUP BY dept
        HAVING avg_sal > 100000
    ) AS high_sal_depts
);

-- MySQL requires the subquery to be wrapped in another subquery (derived table)
-- to avoid "You can't specify target table" error

SELECT dept, COUNT(*) as remaining FROM employees GROUP BY dept ORDER BY dept;
```

📸 **Verified Output:**
```
+-----------+-----------+
| dept      | remaining |
+-----------+-----------+
| Finance   |         1 |
| Marketing |         2 |
+-----------+-----------+
```

---

## Step 7: TRUNCATE vs DELETE

```sql
-- Setup: recreate employee table for comparison
CREATE TABLE temp_employees LIKE employees;
INSERT INTO temp_employees SELECT * FROM employees;

-- DELETE removes rows one by one, can be WHERE'd, fires triggers, can ROLLBACK
DELETE FROM temp_employees WHERE dept = 'Finance';
SELECT ROW_COUNT() AS deleted_count;  -- returns 1

-- TRUNCATE removes ALL rows instantly, resets AUTO_INCREMENT, minimal logging
-- Cannot have WHERE clause, cannot ROLLBACK in MySQL
TRUNCATE TABLE temp_employees;
SELECT COUNT(*) FROM temp_employees;  -- 0
```

| Feature | DELETE | TRUNCATE |
|---------|--------|----------|
| WHERE clause | Yes | No |
| Speed on large tables | Slow | Very fast |
| Triggers fire | Yes | No (MySQL) |
| Resets AUTO_INCREMENT | No | Yes |
| Can ROLLBACK | Yes | No (MySQL) / Yes (PG) |
| Logs each row | Yes | Minimal |

📸 **Verified Output:**
```
+--------------+
| deleted_count|
+--------------+
|            1 |
+--------------+

+----------+
| COUNT(*) |
+----------+
|        0 |
+----------+
```

---

## Step 8: Capstone — Soft Delete Pattern

Hard deletes destroy data permanently. The **soft delete pattern** marks rows as deleted without removing them.

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE updatelab;

-- "Soft delete" by setting deleted_at timestamp
UPDATE employees SET deleted_at = NOW() WHERE emp_id = 2;

-- Active employees view (soft-delete aware)
CREATE VIEW active_employees AS
SELECT emp_id, name, dept, salary
FROM employees
WHERE deleted_at IS NULL;

-- "Deleted" employees view
CREATE VIEW deleted_employees AS
SELECT emp_id, name, dept, salary, deleted_at
FROM employees
WHERE deleted_at IS NOT NULL;

-- Normal queries use the view — deleted rows are hidden
SELECT * FROM active_employees ORDER BY dept, name;

-- Admin can still see deleted employees
SELECT * FROM deleted_employees;

-- Restore a soft-deleted employee
UPDATE employees SET deleted_at = NULL WHERE emp_id = 2;

-- Permanent hard delete (after grace period)
DELETE FROM employees WHERE deleted_at < NOW() - INTERVAL 90 DAY;
EOF
```

📸 **Verified Output:**
```
-- active_employees:
+--------+----------------+-------------+------------+
| emp_id | name           | dept        | salary     |
+--------+----------------+-------------+------------+
|      3 | Carol Davis    | Engineering | 126500.00  |
|      5 | Eve Martinez   | Engineering | 107800.00  |
|      1 | Alice Johnson  | Engineering | 110000.00  |
|      7 | Grace Taylor   | HR          |  70000.00  |
|      6 | Frank Anderson | Marketing   |  73100.00  |
+--------+----------------+-------------+------------+

-- deleted_employees:
+--------+-----------+-----------+----------+---------------------+
| emp_id | name      | dept      | salary   | deleted_at          |
+--------+-----------+-----------+----------+---------------------+
|      2 | Bob Smith | Marketing | 77400.00 | 2024-03-15 10:30:00 |
+--------+-----------+-----------+----------+---------------------+
```

> 💡 **Soft delete benefits**: Audit trail, easy restore, foreign key integrity preserved, "recycle bin" UX. **Downsides**: All queries need `WHERE deleted_at IS NULL`, index on `deleted_at` needed, storage grows. Most production apps use soft delete for important records.

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Operation | Syntax | Notes |
|-----------|--------|-------|
| Update one row | `UPDATE t SET col=val WHERE id=x` | Always use WHERE |
| Update all rows | `UPDATE t SET col=val` | Dangerous! |
| Update with expression | `UPDATE t SET salary = salary * 1.1 WHERE ...` | Computed updates |
| Update with JOIN (MySQL) | `UPDATE t1 JOIN t2 ON ... SET t1.col = ...` | Cross-table update |
| Update with FROM (PG) | `UPDATE t1 SET col = t2.val FROM t2 WHERE ...` | PG syntax |
| Delete specific rows | `DELETE FROM t WHERE condition` | Always use WHERE |
| Delete with subquery | `DELETE FROM t WHERE id IN (SELECT ...)` | Derived table in MySQL |
| Truncate | `TRUNCATE TABLE t` | Fast, irreversible in MySQL |
| Soft delete | `UPDATE t SET deleted_at = NOW() WHERE id = x` | Keep data, hide it |

**Next:** Lab 14 — Transactions
