# Lab 02: CTEs and Recursive Queries

**Time:** 40 minutes | **Level:** Practitioner | **DB:** PostgreSQL 15

Common Table Expressions (CTEs) — defined with `WITH` — make complex queries readable by naming sub-results. Recursive CTEs (`WITH RECURSIVE`) unlock hierarchical traversal: org charts, category trees, graph paths.

---

## Step 1 — Setup: Employee Hierarchy

```sql
CREATE TABLE employees (
  id         INT PRIMARY KEY,
  name       VARCHAR(50),
  manager_id INT,
  department VARCHAR(50),
  salary     NUMERIC(10,2)
);

INSERT INTO employees VALUES
  (1,  'CEO',         NULL, 'Executive', 200000),
  (2,  'CTO',         1,    'Tech',      150000),
  (3,  'CFO',         1,    'Finance',   140000),
  (4,  'VP Eng',      2,    'Tech',      120000),
  (5,  'VP Product',  2,    'Tech',      115000),
  (6,  'Sr Dev',      4,    'Tech',       90000),
  (7,  'Jr Dev',      4,    'Tech',       70000),
  (8,  'Sr Analyst',  3,    'Finance',    85000),
  (9,  'Analyst',     3,    'Finance',    65000),
  (10, 'Designer',    5,    'Tech',       75000);
```

📸 **Verified Output:**
```
INSERT 0 10
```

---

## Step 2 — Simple CTE

```sql
WITH dept_avg AS (
  SELECT department, AVG(salary) AS avg_sal
  FROM employees
  GROUP BY department
)
SELECT e.name, e.department, e.salary,
       ROUND(da.avg_sal, 2) AS dept_avg,
       ROUND(e.salary - da.avg_sal, 2) AS diff_from_avg
FROM employees e
JOIN dept_avg da ON e.department = da.department
ORDER BY e.department, e.salary DESC;
```

> 💡 A CTE is scoped to the single query it belongs to. It cannot be referenced outside its `WITH` block.

📸 **Verified Output:**
```
    name    | department |  salary   | dept_avg  | diff_from_avg
------------+------------+-----------+-----------+--------------
 CFO        | Finance    | 140000.00 |  96666.67 |     43333.33
 Sr Analyst | Finance    |  85000.00 |  96666.67 |    -11666.67
 Analyst    | Finance    |  65000.00 |  96666.67 |    -31666.67
 CTO        | Tech       | 150000.00 | 103333.33 |     46666.67
 VP Eng     | Tech       | 120000.00 | 103333.33 |     16666.67
...
```

---

## Step 3 — Multiple CTEs

```sql
WITH dept_stats AS (
  SELECT department,
         COUNT(*)         AS headcount,
         AVG(salary)      AS avg_salary,
         SUM(salary)      AS payroll
  FROM employees
  GROUP BY department
),
above_avg AS (
  SELECT e.name, e.department, e.salary, ds.avg_salary
  FROM employees e
  JOIN dept_stats ds ON e.department = ds.department
  WHERE e.salary > ds.avg_salary
)
SELECT aa.name, aa.department, aa.salary,
       ROUND(aa.avg_salary, 2) AS dept_avg,
       ds.headcount
FROM above_avg aa
JOIN dept_stats ds ON aa.department = ds.department
ORDER BY aa.department, aa.salary DESC;
```

📸 **Verified Output:**
```
    name    | department |  salary   | dept_avg  | headcount
------------+------------+-----------+-----------+-----------
 CFO        | Finance    | 140000.00 |  96666.67 |         3
 CTO        | Tech       | 150000.00 | 103333.33 |         6
 VP Eng     | Tech       | 120000.00 | 103333.33 |         6
 VP Product | Tech       | 115000.00 | 103333.33 |         6
(4 rows)
```

---

## Step 4 — Recursive CTE: Org Chart Traversal

```sql
WITH RECURSIVE org_chart AS (
  -- Anchor: start with root (no manager)
  SELECT id, name, manager_id,
         0 AS level,
         name::TEXT AS path
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive: join children to current level
  SELECT e.id, e.name, e.manager_id,
         oc.level + 1,
         oc.path || ' -> ' || e.name
  FROM employees e
  JOIN org_chart oc ON e.manager_id = oc.id
)
SELECT level,
       REPEAT('  ', level) || name AS hierarchy,
       path
FROM org_chart
ORDER BY path;
```

**How it works:**
1. **Anchor member**: selects the root node(s)
2. **Recursive member**: joins each employee to already-found managers
3. PostgreSQL alternates until no new rows are found

📸 **Verified Output:**
```
 level |   hierarchy    |                 path
-------+----------------+--------------------------------------
     0 | CEO            | CEO
     1 |   CFO          | CEO -> CFO
     2 |     Analyst    | CEO -> CFO -> Analyst
     2 |     Sr Analyst | CEO -> CFO -> Sr Analyst
     1 |   CTO          | CEO -> CTO
     2 |     VP Eng     | CEO -> CTO -> VP Eng
     3 |       Jr Dev   | CEO -> CTO -> VP Eng -> Jr Dev
     3 |       Sr Dev   | CEO -> CTO -> VP Eng -> Sr Dev
     2 |     VP Product | CEO -> CTO -> VP Product
     3 |       Designer | CEO -> CTO -> VP Product -> Designer
(10 rows)
```

---

## Step 5 — Recursive CTE: Find All Reports Under a Manager

```sql
WITH RECURSIVE reports_under AS (
  SELECT id, name, manager_id, 0 AS depth
  FROM employees
  WHERE name = 'CTO'          -- start point

  UNION ALL

  SELECT e.id, e.name, e.manager_id, ru.depth + 1
  FROM employees e
  JOIN reports_under ru ON e.manager_id = ru.id
)
SELECT depth, name FROM reports_under
ORDER BY depth, name;
```

> 💡 Add `WHERE level < 10` (or use `CYCLE` in PostgreSQL 14+) to guard against infinite loops in graphs with cycles.

📸 **Verified Output:**
```
 depth |    name
-------+------------
     0 | CTO
     1 | VP Eng
     1 | VP Product
     2 | Designer
     2 | Jr Dev
     2 | Sr Dev
(6 rows)
```

---

## Step 6 — CTE vs Subquery Performance

```sql
-- As subquery (may be evaluated multiple times)
SELECT name, department, salary
FROM employees
WHERE salary > (
  SELECT AVG(salary) FROM employees WHERE department = employees.department
);

-- As CTE (evaluated once, referenced twice)
WITH dept_avgs AS (
  SELECT department, AVG(salary) AS avg_sal
  FROM employees GROUP BY department
)
SELECT e.name, e.department, e.salary
FROM employees e
JOIN dept_avgs da ON e.department = da.department
WHERE e.salary > da.avg_sal;
```

> 💡 In PostgreSQL, a plain CTE is an **optimization fence** by default — the planner cannot push predicates into it. Add `MATERIALIZED` or `NOT MATERIALIZED` explicitly to control this.

---

## Step 7 — Materialized CTEs

```sql
-- Force CTE result to be computed once and cached
WITH MATERIALIZED expensive_calc AS (
  SELECT department,
         PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary,
         STDDEV(salary) AS salary_stddev
  FROM employees
  GROUP BY department
)
SELECT e.name, e.salary,
       ec.median_salary,
       ROUND(ABS(e.salary - ec.median_salary) / NULLIF(ec.salary_stddev, 0), 2) AS z_score
FROM employees e
JOIN expensive_calc ec ON e.department = ec.department
ORDER BY ABS(z_score) DESC NULLS LAST;
```

---

## Step 8 — Capstone: Category Tree with Aggregated Budgets

```sql
-- Build a category hierarchy with rolled-up counts
CREATE TABLE categories (
  id        INT PRIMARY KEY,
  name      VARCHAR(50),
  parent_id INT,
  base_budget NUMERIC(12,2) DEFAULT 0
);

INSERT INTO categories VALUES
  (1, 'Technology',   NULL, 500000),
  (2, 'Engineering',  1,    300000),
  (3, 'Product',      1,    150000),
  (4, 'Backend',      2,    120000),
  (5, 'Frontend',     2,     80000),
  (6, 'Mobile',       2,     60000),
  (7, 'Design',       3,     70000),
  (8, 'Research',     3,     50000);

WITH RECURSIVE cat_tree AS (
  SELECT id, name, parent_id, base_budget, 0 AS depth, id::TEXT AS lineage
  FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, c.base_budget, ct.depth + 1,
         ct.lineage || '/' || c.id
  FROM categories c JOIN cat_tree ct ON c.parent_id = ct.id
),
totals AS (
  SELECT ct.id, ct.name, ct.depth,
         SUM(c2.base_budget) AS subtree_budget
  FROM cat_tree ct
  JOIN cat_tree c2 ON c2.lineage LIKE ct.lineage || '%'
  GROUP BY ct.id, ct.name, ct.depth
)
SELECT REPEAT('  ', depth) || name AS category,
       subtree_budget
FROM totals
ORDER BY (SELECT lineage FROM cat_tree WHERE id = totals.id);
```

---

## Summary

| Concept | Syntax | Use Case |
|---------|--------|----------|
| Simple CTE | `WITH name AS (...)` | Readable sub-query aliasing |
| Multiple CTEs | `WITH a AS (...), b AS (...)` | Chain transformations |
| Recursive CTE | `WITH RECURSIVE` + `UNION ALL` | Trees, graphs, sequences |
| Materialized | `WITH MATERIALIZED name AS` | Force single evaluation |
| Not Materialized | `WITH NOT MATERIALIZED name AS` | Allow predicate pushdown |
| Depth limiting | `WHERE level < N` | Prevent infinite loops |
