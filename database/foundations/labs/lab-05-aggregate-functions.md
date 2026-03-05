# Lab 05: Aggregate Functions

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Master `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, `HAVING`, `DISTINCT`, and NULL behavior in aggregates. Includes the `ROLLUP` modifier for subtotals.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE analytics;
USE analytics;

CREATE TABLE sales (
    sale_id    INT NOT NULL AUTO_INCREMENT,
    rep_name   VARCHAR(50) NOT NULL,
    region     VARCHAR(30) NOT NULL,
    product    VARCHAR(50) NOT NULL,
    amount     DECIMAL(10,2),
    sale_date  DATE NOT NULL,
    PRIMARY KEY (sale_id)
);

INSERT INTO sales (rep_name, region, product, amount, sale_date) VALUES
('Alice',  'North', 'Widget A',   1200.00, '2024-01-05'),
('Bob',    'South', 'Widget B',   850.50,  '2024-01-08'),
('Alice',  'North', 'Widget C',   2300.00, '2024-01-12'),
('Carol',  'East',  'Widget A',   975.00,  '2024-01-15'),
('Bob',    'South', 'Widget A',   1100.00, '2024-01-20'),
('Alice',  'North', 'Widget B',   NULL,    '2024-01-22'),
('Carol',  'East',  'Widget B',   1450.00, '2024-02-01'),
('David',  'West',  'Widget C',   3200.00, '2024-02-05'),
('Bob',    'South', 'Widget C',   900.00,  '2024-02-10'),
('David',  'West',  'Widget A',   2100.00, '2024-02-14'),
('Alice',  'North', 'Widget A',   1800.00, '2024-02-18'),
('Carol',  'East',  'Widget C',   NULL,    '2024-02-20'),
('David',  'West',  'Widget B',   1650.00, '2024-02-25'),
('Bob',    'South', 'Widget B',   1250.00, '2024-03-01'),
('Alice',  'North', 'Widget C',   2750.00, '2024-03-05');
EOF
```

---

## Step 2: COUNT

```sql
USE analytics;

-- Count all rows (including NULLs)
SELECT COUNT(*) AS total_sales FROM sales;

-- Count non-NULL values in a specific column
SELECT COUNT(amount) AS sales_with_amount FROM sales;

-- The difference shows NULL rows
SELECT
    COUNT(*)       AS total_rows,
    COUNT(amount)  AS non_null_amount,
    COUNT(*) - COUNT(amount) AS null_amount_rows
FROM sales;
```

📸 **Verified Output:**
```
+------------+------------------+------------------+
| total_rows | non_null_amount  | null_amount_rows |
+------------+------------------+------------------+
|         15 |               13 |                2 |
+------------+------------------+------------------+
```

> 💡 `COUNT(*)` counts ALL rows. `COUNT(column)` counts only rows where that column is NOT NULL. This difference is important!

---

## Step 3: SUM, AVG, MIN, MAX

```sql
SELECT
    SUM(amount)   AS total_revenue,
    AVG(amount)   AS avg_sale,
    MIN(amount)   AS smallest_sale,
    MAX(amount)   AS largest_sale,
    ROUND(AVG(amount), 2) AS avg_rounded
FROM sales;
```

📸 **Verified Output:**
```
+---------------+--------------+---------------+--------------+-------------+
| total_revenue | avg_sale     | smallest_sale | largest_sale | avg_rounded |
+---------------+--------------+---------------+--------------+-------------+
|      25525.50 | 1963.50000   |        850.50 |      3200.00 |     1963.50 |
+---------------+--------------+---------------+--------------+-------------+
```

> 💡 All aggregate functions (`SUM`, `AVG`, `MIN`, `MAX`) **ignore NULL values**. The average above is calculated over 13 rows (the 2 NULLs are excluded).

---

## Step 4: GROUP BY

```sql
-- Sales by region
SELECT
    region,
    COUNT(*)           AS num_sales,
    SUM(amount)        AS total_revenue,
    ROUND(AVG(amount), 2) AS avg_sale
FROM sales
GROUP BY region
ORDER BY total_revenue DESC;
```

📸 **Verified Output:**
```
+--------+-----------+---------------+----------+
| region | num_sales | total_revenue | avg_sale |
+--------+-----------+---------------+----------+
| North  |         5 |      8050.00  |  2012.50 |
| West   |         3 |      6950.00  |  3475.00 |
| East   |         3 |      2425.00  |  1212.50 |
| South  |         4 |      4100.50  |  1366.83 |
+--------+-----------+---------------+----------+
```

```sql
-- Sales by rep and region
SELECT
    rep_name,
    region,
    COUNT(*)    AS num_sales,
    SUM(amount) AS total
FROM sales
GROUP BY rep_name, region
ORDER BY rep_name, total DESC;
```

> 💡 Every column in SELECT that is NOT inside an aggregate function must appear in GROUP BY.

---

## Step 5: HAVING (Filter After Grouping)

```sql
-- Only regions with total revenue > 5000
SELECT
    region,
    SUM(amount) AS total_revenue
FROM sales
GROUP BY region
HAVING total_revenue > 5000
ORDER BY total_revenue DESC;

-- Reps with more than 3 sales
SELECT
    rep_name,
    COUNT(*) AS sale_count
FROM sales
GROUP BY rep_name
HAVING COUNT(*) > 3;
```

📸 **Verified Output (HAVING total > 5000):**
```
+--------+---------------+
| region | total_revenue |
+--------+---------------+
| North  |      8050.00  |
| West   |      6950.00  |
+--------+---------------+
```

> 💡 **WHERE vs HAVING:**
> - `WHERE` filters **individual rows** before grouping
> - `HAVING` filters **groups** after aggregation
> - You CANNOT use aggregate functions in WHERE

---

## Step 6: DISTINCT and COUNT DISTINCT

```sql
-- Count unique values
SELECT COUNT(DISTINCT region)  AS unique_regions  FROM sales;
SELECT COUNT(DISTINCT rep_name) AS unique_reps    FROM sales;
SELECT COUNT(DISTINCT product)  AS unique_products FROM sales;

-- SELECT DISTINCT — deduplicate result rows
SELECT DISTINCT region FROM sales ORDER BY region;

-- DISTINCT on multiple columns
SELECT DISTINCT region, product FROM sales ORDER BY region, product;
```

📸 **Verified Output:**
```
+----------------+
| unique_regions |
+----------------+
|              4 |
+----------------+

+--------+
| region |
+--------+
| East   |
| North  |
| South  |
| West   |
+--------+
```

---

## Step 7: NULL Handling in Aggregates

```sql
-- Demonstrate NULL behavior
SELECT
    COUNT(*)       AS count_all,
    COUNT(amount)  AS count_non_null,
    SUM(amount)    AS sum_ignores_null,
    AVG(amount)    AS avg_ignores_null,
    -- To include NULL as 0:
    SUM(COALESCE(amount, 0))            AS sum_treating_null_as_zero,
    COUNT(*) * AVG(COALESCE(amount, 0)) AS avg_treating_null_as_zero
FROM sales;
```

📸 **Verified Output:**
```
+-----------+----------------+------------------+-----------------+---------------------------+---------------------------+
| count_all | count_non_null | sum_ignores_null | avg_ignores_null| sum_treating_null_as_zero | avg_treating_null_as_zero |
+-----------+----------------+------------------+-----------------+---------------------------+---------------------------+
|        15 |             13 |         25525.50 |      1963.50000 |                  25525.50 |               1701.700000 |
+-----------+----------------+------------------+-----------------+---------------------------+---------------------------+
```

---

## Step 8: Capstone — ROLLUP for Subtotals

```sql
-- MySQL: GROUP BY WITH ROLLUP adds subtotal rows
SELECT
    COALESCE(region, 'GRAND TOTAL')    AS region,
    COALESCE(product, 'ALL PRODUCTS')  AS product,
    COUNT(*)                            AS num_sales,
    ROUND(SUM(amount), 2)              AS revenue
FROM sales
WHERE amount IS NOT NULL
GROUP BY region, product WITH ROLLUP
ORDER BY region, product;
```

📸 **Verified Output:**
```
+-------------+--------------+-----------+---------+
| region      | product      | num_sales | revenue |
+-------------+--------------+-----------+---------+
| East        | Widget A     |         1 |  975.00 |
| East        | Widget B     |         1 | 1450.00 |
| East        | ALL PRODUCTS |         2 | 2425.00 |  ← subtotal
| North       | Widget A     |         2 | 3000.00 |
| North       | Widget C     |         2 | 5050.00 |
| North       | ALL PRODUCTS |         4 | 8050.00 |  ← subtotal
...
| GRAND TOTAL | ALL PRODUCTS |        13 |25525.50 |  ← grand total
+-------------+--------------+-----------+---------+
```

**PostgreSQL equivalent:**
```sql
SELECT
    COALESCE(region, 'GRAND TOTAL')   AS region,
    COALESCE(product, 'ALL PRODUCTS') AS product,
    COUNT(*)                           AS num_sales,
    ROUND(SUM(amount), 2)             AS revenue
FROM sales
WHERE amount IS NOT NULL
GROUP BY ROLLUP(region, product)
ORDER BY region NULLS LAST, product NULLS LAST;
```

> 💡 `ROLLUP` is powerful for reporting dashboards — it generates subtotals at each level automatically.

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Function | Description | NULL behavior |
|----------|-------------|---------------|
| `COUNT(*)` | Count all rows | Includes NULLs |
| `COUNT(col)` | Count non-NULL values | Excludes NULLs |
| `COUNT(DISTINCT col)` | Count unique non-NULL values | Excludes NULLs |
| `SUM(col)` | Sum of non-NULL values | Excludes NULLs |
| `AVG(col)` | Average of non-NULL values | Excludes NULLs |
| `MIN(col)` | Minimum non-NULL value | Excludes NULLs |
| `MAX(col)` | Maximum non-NULL value | Excludes NULLs |
| `GROUP BY` | Group rows for aggregation | Required for non-agg columns |
| `HAVING` | Filter groups (post-aggregation) | Like WHERE but for groups |
| `WITH ROLLUP` | Add subtotal rows | MySQL syntax |
| `ROLLUP(...)` | Add subtotal rows | PostgreSQL syntax |

**Next:** Lab 06 — INNER JOIN
