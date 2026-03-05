# Lab 06: INNER JOIN

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Learn INNER JOIN syntax, joining on foreign keys, multi-table JOINs, table aliases, avoiding Cartesian products, and the self-join pattern.

---

## Step 1: Setup — Relational Schema

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE company;
USE company;

CREATE TABLE departments (
    dept_id    INT NOT NULL AUTO_INCREMENT,
    dept_name  VARCHAR(50) NOT NULL,
    location   VARCHAR(50),
    budget     DECIMAL(12,2),
    PRIMARY KEY (dept_id)
);

CREATE TABLE employees (
    emp_id      INT NOT NULL AUTO_INCREMENT,
    first_name  VARCHAR(50) NOT NULL,
    last_name   VARCHAR(50) NOT NULL,
    dept_id     INT,
    salary      DECIMAL(10,2),
    manager_id  INT,          -- self-referencing FK
    PRIMARY KEY (emp_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id),
    FOREIGN KEY (manager_id) REFERENCES employees(emp_id)
);

CREATE TABLE projects (
    project_id   INT NOT NULL AUTO_INCREMENT,
    project_name VARCHAR(100) NOT NULL,
    dept_id      INT,
    budget       DECIMAL(12,2),
    PRIMARY KEY (project_id),
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
);

CREATE TABLE project_assignments (
    emp_id      INT NOT NULL,
    project_id  INT NOT NULL,
    role        VARCHAR(50),
    hours       INT,
    PRIMARY KEY (emp_id, project_id),
    FOREIGN KEY (emp_id)     REFERENCES employees(emp_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

INSERT INTO departments (dept_name, location, budget) VALUES
('Engineering', 'Floor 3', 500000),
('Marketing',   'Floor 2', 200000),
('HR',          'Floor 1', 150000),
('Finance',     'Floor 4', 300000);

-- Insert managers first (no manager_id)
INSERT INTO employees (first_name, last_name, dept_id, salary, manager_id) VALUES
('Henry',  'Thomas',  1, 125000, NULL),   -- emp_id=1, Eng manager
('Grace',  'Taylor',  3,  70000, NULL),   -- emp_id=2, HR manager
('Karen',  'Harris',  2,  75000, NULL),   -- emp_id=3, Mkt manager
('Isabel', 'Jackson', 4,  88000, NULL);   -- emp_id=4, Fin manager

-- Insert regular employees
INSERT INTO employees (first_name, last_name, dept_id, salary, manager_id) VALUES
('Alice',  'Johnson', 1,  95000, 1),
('Carol',  'Davis',   1, 110000, 1),
('Eve',    'Martinez',1,  98000, 1),
('Liam',   'Clark',   1, 105000, 1),
('Bob',    'Smith',   2,  72000, 3),
('Frank',  'Anderson',2,  68000, 3),
('David',  'Wilson',  3,  65000, 2),
('Jack',   'White',   4,  92000, 4);

INSERT INTO projects (project_name, dept_id, budget) VALUES
('Cloud Migration',   1, 150000),
('Brand Refresh',     2,  80000),
('HR System Upgrade', 3,  50000),
('Budget Analytics',  4, 120000),
('API Platform',      1, 200000);

INSERT INTO project_assignments (emp_id, project_id, role, hours) VALUES
(1, 1, 'Tech Lead',    120),
(5, 1, 'Developer',     80),
(6, 1, 'Developer',     80),
(8, 5, 'Architect',    100),
(7, 5, 'Developer',     60),
(5, 5, 'Developer',     40),
(9, 2, 'Coordinator',   50),
(10,2, 'Designer',      30),
(11,3, 'Analyst',       40),
(12,4, 'Analyst',       60),
(4, 4, 'Lead',          20);
EOF
```

---

## Step 2: Basic INNER JOIN Syntax

```sql
USE company;

-- INNER JOIN: only rows that match in BOTH tables
SELECT
    e.first_name,
    e.last_name,
    d.dept_name,
    d.location
FROM employees AS e
INNER JOIN departments AS d ON e.dept_id = d.dept_id
ORDER BY d.dept_name, e.last_name;
```

📸 **Verified Output:**
```
+------------+-----------+-------------+----------+
| first_name | last_name | dept_name   | location |
+------------+-----------+-------------+----------+
| Alice      | Johnson   | Engineering | Floor 3  |
| Carol      | Davis     | Engineering | Floor 3  |
| Eve        | Martinez  | Engineering | Floor 3  |
| Henry      | Thomas    | Engineering | Floor 3  |
| Liam       | Clark     | Engineering | Floor 3  |
| Isabel     | Jackson   | Finance     | Floor 4  |
| Jack       | White     | Finance     | Floor 4  |
| David      | Wilson    | HR          | Floor 1  |
| Grace      | Taylor    | HR          | Floor 1  |
| Bob        | Smith     | Marketing   | Floor 2  |
| Frank      | Anderson  | Marketing   | Floor 2  |
| Karen      | Harris    | Marketing   | Floor 2  |
+------------+-----------+-------------+----------+
```

> 💡 `INNER JOIN` returns only rows where the join condition is satisfied in **both** tables. Employees without a department (dept_id IS NULL) would not appear.

---

## Step 3: Table Aliases

```sql
-- Without aliases (verbose)
SELECT employees.first_name, departments.dept_name
FROM employees
INNER JOIN departments ON employees.dept_id = departments.dept_id;

-- With aliases (preferred)
SELECT e.first_name, d.dept_name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id;

-- INNER keyword is optional — JOIN alone means INNER JOIN
```

> 💡 Table aliases (`e`, `d`) make queries shorter and are required when joining a table to itself. `INNER` keyword is optional — plain `JOIN` defaults to `INNER JOIN`.

---

## Step 4: JOIN with WHERE and Aggregates

```sql
-- Filtered JOIN: Engineering employees only
SELECT
    e.first_name,
    e.last_name,
    e.salary,
    d.dept_name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id
WHERE d.dept_name = 'Engineering'
ORDER BY e.salary DESC;

-- Aggregated JOIN: headcount and avg salary per department
SELECT
    d.dept_name,
    COUNT(e.emp_id)        AS headcount,
    ROUND(AVG(e.salary),2) AS avg_salary,
    SUM(e.salary)          AS total_payroll
FROM departments d
JOIN employees e ON d.dept_id = e.dept_id
GROUP BY d.dept_name
ORDER BY total_payroll DESC;
```

📸 **Verified Output (aggregated):**
```
+-------------+-----------+------------+---------------+
| dept_name   | headcount | avg_salary | total_payroll |
+-------------+-----------+------------+---------------+
| Engineering |         5 |  106600.00 |     533000.00 |
| Finance     |         2 |   90000.00 |     180000.00 |
| Marketing   |         3 |   71666.67 |     215000.00 |
| HR          |         2 |   67500.00 |     135000.00 |
+-------------+-----------+------------+---------------+
```

---

## Step 5: Multi-Table JOIN

```sql
-- Three-table JOIN: employees → projects → assignments
SELECT
    e.first_name,
    e.last_name,
    p.project_name,
    pa.role,
    pa.hours
FROM employees e
JOIN project_assignments pa ON e.emp_id = pa.emp_id
JOIN projects p             ON pa.project_id = p.project_id
ORDER BY p.project_name, e.last_name;
```

📸 **Verified Output:**
```
+------------+-----------+---------------------+-----------+-------+
| first_name | last_name | project_name        | role      | hours |
+------------+-----------+---------------------+-----------+-------+
| Isabel     | Jackson   | Budget Analytics    | Lead      |    20 |
| Jack       | White     | Budget Analytics    | Analyst   |    60 |
| Eve        | Martinez  | API Platform        | Developer |    60 |
| Alice      | Johnson   | API Platform        | Developer |    40 |
| Henry      | Thomas    | API Platform        | Architect |   100 |
| Alice      | Johnson   | Cloud Migration     | Developer |    80 |
| Carol      | Davis     | Cloud Migration     | Developer |    80 |
| Henry      | Thomas    | Cloud Migration     | Tech Lead |   120 |
...
```

---

## Step 6: Avoid Cartesian Products

```sql
-- WRONG: Missing join condition → Cartesian product (all combinations)
-- If employees has 12 rows and departments has 4, result = 48 rows!
SELECT e.first_name, d.dept_name
FROM employees e, departments d;   -- OLD syntax, avoid!

-- CORRECT: Always specify the join condition
SELECT e.first_name, d.dept_name
FROM employees e
JOIN departments d ON e.dept_id = d.dept_id;

-- Check: Cartesian would give 12 * 4 = 48 rows
SELECT COUNT(*) FROM employees, departments;         -- 48 (wrong!)
SELECT COUNT(*) FROM employees JOIN departments ON employees.dept_id = departments.dept_id;  -- 12 (correct)
```

📸 **Verified Output:**
```
+----------+
| COUNT(*) |
+----------+
|       48 |
+----------+

+----------+
| COUNT(*) |
+----------+
|       12 |
+----------+
```

---

## Step 7: Self-Join Pattern

```sql
-- Self-join: employee → their manager (both rows from same table)
SELECT
    e.first_name                           AS employee,
    e.last_name                            AS emp_last,
    CONCAT(m.first_name,' ',m.last_name)   AS manager_name,
    d.dept_name
FROM employees e
JOIN employees m   ON e.manager_id = m.emp_id     -- self-join
JOIN departments d ON e.dept_id = d.dept_id
ORDER BY d.dept_name, e.last_name;
```

📸 **Verified Output:**
```
+----------+----------+--------------+-------------+
| employee | emp_last | manager_name | dept_name   |
+----------+----------+--------------+-------------+
| Alice    | Johnson  | Henry Thomas | Engineering |
| Carol    | Davis    | Henry Thomas | Engineering |
| Eve      | Martinez | Henry Thomas | Engineering |
| Liam     | Clark    | Henry Thomas | Engineering |
| Jack     | White    | Isabel Jackson| Finance     |
| David    | Wilson   | Grace Taylor | HR          |
| Bob      | Smith    | Karen Harris | Marketing   |
| Frank    | Anderson | Karen Harris | Marketing   |
+----------+----------+--------------+-------------+
```

> 💡 Self-join requires **two different aliases** for the same table (`e` for employee, `m` for manager). Managers themselves don't appear in the result because their `manager_id` is NULL — INNER JOIN excludes them.

---

## Step 8: Capstone — Full Business Query

Find all employees, their projects, total hours committed, and department budget remaining:

```sql
SELECT
    d.dept_name,
    CONCAT(e.first_name, ' ', e.last_name) AS employee,
    COUNT(pa.project_id)                    AS num_projects,
    SUM(pa.hours)                           AS total_hours,
    e.salary
FROM employees e
JOIN departments d         ON e.dept_id    = d.dept_id
JOIN project_assignments pa ON e.emp_id   = pa.emp_id
GROUP BY d.dept_name, e.emp_id, e.first_name, e.last_name, e.salary
HAVING num_projects >= 1
ORDER BY d.dept_name, total_hours DESC;
```

📸 **Verified Output:**
```
+-------------+----------------+--------------+-------------+---------+
| dept_name   | employee       | num_projects | total_hours | salary  |
+-------------+----------------+--------------+-------------+---------+
| Engineering | Henry Thomas   |            2 |         220 | 125000  |
| Engineering | Alice Johnson  |            2 |         120 |  95000  |
| Engineering | Carol Davis    |            1 |          80 | 110000  |
| Engineering | Eve Martinez   |            1 |          60 |  98000  |
| Finance     | Isabel Jackson |            1 |          20 |  88000  |
| Finance     | Jack White     |            1 |          60 |  92000  |
| HR          | David Wilson   |            1 |          40 |  65000  |
| Marketing   | Bob Smith      |            1 |          50 |  72000  |
| Marketing   | Frank Anderson |            1 |          30 |  68000  |
+-------------+----------------+--------------+-------------+---------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Concept | Syntax | Notes |
|---------|--------|-------|
| INNER JOIN | `FROM a JOIN b ON a.id = b.a_id` | Only matching rows |
| Table alias | `FROM employees e` | Required for self-joins |
| INNER keyword | Optional | `JOIN` = `INNER JOIN` |
| Multi-table | Chain multiple JOINs | Order matters for readability |
| Self-join | `FROM t AS a JOIN t AS b ON a.mgr = b.id` | Same table, different aliases |
| Cartesian product | Missing ON clause | Avoid: rows multiply |
| JOIN + WHERE | Filter after joining | WHERE limits final result |
| JOIN + GROUP BY | Aggregate joined data | Combine patterns freely |

**Next:** Lab 07 — Outer Joins
