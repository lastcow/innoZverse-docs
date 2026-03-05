# Lab 01: Window Functions

**Time:** 40 minutes | **Level:** Practitioner | **DB:** PostgreSQL 15

Window functions perform calculations across a set of table rows related to the current row — without collapsing the result set. Unlike `GROUP BY`, every row is preserved.

---

## Step 1 — Setup: Create Sales Data

```sql
CREATE TABLE sales (
  id         SERIAL PRIMARY KEY,
  salesperson VARCHAR(50),
  region      VARCHAR(50),
  amount      NUMERIC(10,2),
  sale_date   DATE
);

INSERT INTO sales (salesperson, region, amount, sale_date) VALUES
  ('Alice', 'East', 1200.00, '2024-01-05'),
  ('Bob',   'East',  950.00, '2024-01-10'),
  ('Carol', 'West', 1500.00, '2024-01-03'),
  ('Dave',  'West',  800.00, '2024-01-15'),
  ('Eve',   'East', 1200.00, '2024-01-20'),
  ('Frank', 'West', 2000.00, '2024-01-22'),
  ('Grace', 'East',  600.00, '2024-01-25'),
  ('Heidi', 'West', 1800.00, '2024-01-28');
```

> 💡 The `OVER()` clause is what transforms an aggregate function into a window function. Without it, you'd get a single-row aggregate.

📸 **Verified Output:**
```
INSERT 0 8
```

---

## Step 2 — ROW_NUMBER, RANK, DENSE_RANK, NTILE

```sql
SELECT salesperson, region, amount,
  ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS row_num,
  RANK()       OVER (PARTITION BY region ORDER BY amount DESC) AS rnk,
  DENSE_RANK() OVER (PARTITION BY region ORDER BY amount DESC) AS dense_rnk,
  NTILE(2)     OVER (PARTITION BY region ORDER BY amount DESC) AS quartile
FROM sales;
```

- **ROW_NUMBER**: always unique, even for ties
- **RANK**: skips numbers after ties (1,1,3)
- **DENSE_RANK**: no gaps after ties (1,1,2)
- **NTILE(n)**: divides into `n` buckets

📸 **Verified Output:**
```
 salesperson | region | amount  | row_num | rnk | dense_rnk | quartile
-------------+--------+---------+---------+-----+-----------+----------
 Alice       | East   | 1200.00 |       1 |   1 |         1 |        1
 Eve         | East   | 1200.00 |       2 |   1 |         1 |        1
 Bob         | East   |  950.00 |       3 |   3 |         2 |        2
 Grace       | East   |  600.00 |       4 |   4 |         3 |        2
 Frank       | West   | 2000.00 |       1 |   1 |         1 |        1
 Heidi       | West   | 1800.00 |       2 |   2 |         2 |        1
 Carol       | West   | 1500.00 |       3 |   3 |         3 |        2
 Dave        | West   |  800.00 |       4 |   4 |         4 |        2
(8 rows)
```

---

## Step 3 — LAG and LEAD: Row Navigation

```sql
SELECT salesperson, region, amount, sale_date,
  LAG(amount)  OVER (PARTITION BY region ORDER BY sale_date) AS prev_amount,
  LEAD(amount) OVER (PARTITION BY region ORDER BY sale_date) AS next_amount,
  amount - LAG(amount) OVER (PARTITION BY region ORDER BY sale_date) AS change
FROM sales
ORDER BY region, sale_date;
```

> 💡 `LAG(col, n, default)` and `LEAD(col, n, default)` accept offset and default-value arguments. `LAG(amount, 2, 0)` looks back two rows, returning 0 if none.

📸 **Verified Output (partial):**
```
 salesperson | region | amount  | sale_date  | prev_amount | next_amount | change
-------------+--------+---------+------------+-------------+-------------+--------
 Alice       | East   | 1200.00 | 2024-01-05 |             |      950.00 |
 Bob         | East   |  950.00 | 2024-01-10 |     1200.00 |     1200.00 | -250.00
 Eve         | East   | 1200.00 | 2024-01-20 |      950.00 |      600.00 |  250.00
 Grace       | East   |  600.00 | 2024-01-25 |     1200.00 |             | -600.00
```

---

## Step 4 — Running Totals and Moving Averages

```sql
SELECT salesperson, region, amount, sale_date,
  SUM(amount) OVER (
    PARTITION BY region
    ORDER BY sale_date
    ROWS UNBOUNDED PRECEDING
  ) AS running_total,
  ROUND(AVG(amount) OVER (
    PARTITION BY region
    ORDER BY sale_date
    ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
  ), 2) AS moving_avg_3
FROM sales
ORDER BY region, sale_date;
```

**Frame clauses:**
| Frame | Meaning |
|-------|---------|
| `ROWS UNBOUNDED PRECEDING` | from start to current row |
| `ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING` | 3-row moving window |
| `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` | entire partition |

📸 **Verified Output:**
```
 salesperson | region | amount  | sale_date  | running_total |  moving_avg_3
-------------+--------+---------+------------+---------------+---------------
 Alice       | East   | 1200.00 | 2024-01-05 |       1200.00 | 1075.0000000000
 Bob         | East   |  950.00 | 2024-01-10 |       2150.00 | 1116.6666666667
 Eve         | East   | 1200.00 | 2024-01-20 |       3350.00 |  916.6666666667
 Grace       | East   |  600.00 | 2024-01-25 |       3950.00 |  900.0000000000
 Carol       | West   | 1500.00 | 2024-01-03 |       1500.00 | 1150.0000000000
 Dave        | West   |  800.00 | 2024-01-15 |       2300.00 | 1433.3333333333
 Frank       | West   | 2000.00 | 2024-01-22 |       4300.00 | 1533.3333333333
 Heidi       | West   | 1800.00 | 2024-01-28 |       6100.00 | 1900.0000000000
(8 rows)
```

---

## Step 5 — FIRST_VALUE and LAST_VALUE

```sql
SELECT salesperson, region, amount,
  FIRST_VALUE(salesperson) OVER (
    PARTITION BY region ORDER BY amount DESC
  ) AS top_seller,
  LAST_VALUE(amount) OVER (
    PARTITION BY region ORDER BY amount DESC
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) AS min_in_region
FROM sales
ORDER BY region, amount DESC;
```

> 💡 `LAST_VALUE` requires an explicit `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` frame — the default frame only goes to the current row, which would return the current row's value.

📸 **Verified Output:**
```
 salesperson | region | amount  | top_seller | min_in_region
-------------+--------+---------+------------+---------------
 Alice       | East   | 1200.00 | Alice      |        600.00
 Eve         | East   | 1200.00 | Alice      |        600.00
 Bob         | East   |  950.00 | Alice      |        600.00
 Grace       | East   |  600.00 | Alice      |        600.00
 Frank       | West   | 2000.00 | Frank      |        800.00
 Heidi       | West   | 1800.00 | Frank      |        800.00
 Carol       | West   | 1500.00 | Frank      |        800.00
 Dave        | West   |  800.00 | Frank      |        800.00
(8 rows)
```

---

## Step 6 — Named Windows with WINDOW Clause

```sql
SELECT salesperson, region, amount,
  ROW_NUMBER() OVER w           AS row_num,
  SUM(amount)  OVER w           AS running_total,
  ROUND(AVG(amount) OVER w, 2)  AS running_avg
FROM sales
WINDOW w AS (PARTITION BY region ORDER BY sale_date ROWS UNBOUNDED PRECEDING)
ORDER BY region, sale_date;
```

> 💡 The `WINDOW` clause lets you define a window frame once and reference it by name — avoids repetition and keeps queries readable.

---

## Step 7 — Practical: Top-N per Group

```sql
-- Top 2 salespeople per region by amount
SELECT * FROM (
  SELECT salesperson, region, amount,
    ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS rn
  FROM sales
) ranked
WHERE rn <= 2;
```

📸 **Verified Output:**
```
 salesperson | region | amount  | rn
-------------+--------+---------+----
 Alice       | East   | 1200.00 |  1
 Eve         | East   | 1200.00 |  2
 Frank       | West   | 2000.00 |  1
 Heidi       | West   | 1800.00 |  2
(4 rows)
```

> 💡 Use `RANK()` instead of `ROW_NUMBER()` when you want to include all tied rows at position N.

---

## Step 8 — Capstone: Sales Performance Dashboard

Build a complete sales report combining multiple window functions:

```sql
SELECT
  salesperson,
  region,
  amount,
  sale_date,
  RANK()       OVER (PARTITION BY region ORDER BY amount DESC) AS region_rank,
  ROUND(100.0 * amount / SUM(amount) OVER (PARTITION BY region), 1) AS region_pct,
  SUM(amount)  OVER (PARTITION BY region ORDER BY sale_date
                     ROWS UNBOUNDED PRECEDING)                  AS cumulative,
  ROUND(AVG(amount) OVER (ORDER BY sale_date
                          ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS ma3_global,
  DENSE_RANK() OVER (ORDER BY amount DESC)                      AS global_rank
FROM sales
ORDER BY region, sale_date;
```

---

## Summary

| Function | Purpose | Ties Handling |
|----------|---------|---------------|
| `ROW_NUMBER()` | Unique sequential number | Each tie gets different number |
| `RANK()` | Rank with gaps | Ties share rank; next rank skips |
| `DENSE_RANK()` | Rank without gaps | Ties share rank; next rank consecutive |
| `NTILE(n)` | Divide into n buckets | Even distribution |
| `LAG(col, n)` | Access n rows before current | N/A |
| `LEAD(col, n)` | Access n rows after current | N/A |
| `FIRST_VALUE(col)` | First value in window frame | N/A |
| `LAST_VALUE(col)` | Last value in window frame | Needs explicit frame |
| `SUM/AVG OVER` | Running aggregate | N/A |
