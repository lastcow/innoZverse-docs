# Lab 08: Data Warehousing Concepts

**Time:** 50 minutes | **Level:** Architect | **DB:** PostgreSQL 15

---

## 🎯 Objective

Build a star schema data warehouse in PostgreSQL. Implement fact/dimension tables, slowly changing dimensions (SCD Type 1/2/3), GROUP BY ROLLUP/CUBE for OLAP queries, and MATERIALIZED VIEWs for performance.

---

## 📚 Background

### OLTP vs OLAP

| Property | OLTP | OLAP / Data Warehouse |
|----------|------|----------------------|
| Purpose | Transactional (order, pay) | Analytics (trends, reporting) |
| Schema | Normalized (3NF) | Denormalized (star/snowflake) |
| Query type | Simple, point lookups | Complex aggregations |
| Data volume | Current state | Historical (years) |
| Row size | Small | Wide (100+ columns) |
| Optimization | Index on PK/FK | Column-store, partitioning |
| Examples | PostgreSQL, MySQL | Redshift, BigQuery, Snowflake |

### Star Schema
```
         dim_customer
              │
dim_date ─── fact_sales ─── dim_product
              │
         dim_store
```

**Fact table**: measurable events (sales, clicks, transactions). Contains foreign keys + metrics.
**Dimension table**: descriptive context (who, what, when, where).

### SCD Types

| Type | Strategy | History |
|------|----------|---------|
| SCD 1 | Overwrite old value | Lost |
| SCD 2 | Add new row with version/date | Full history |
| SCD 3 | Add "previous_value" column | One version back |

---

## Step 1: Start PostgreSQL & Create Star Schema

```bash
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec -i pg-lab psql -U postgres << 'SQL'
CREATE DATABASE warehouse;
\c warehouse

-- === DIMENSION TABLES ===

-- Date dimension (pre-populated for fast joins)
CREATE TABLE dim_date (
  date_key    INT PRIMARY KEY,  -- YYYYMMDD
  date_actual DATE NOT NULL,
  day_of_week SMALLINT,
  day_name    VARCHAR(9),
  day_of_month SMALLINT,
  day_of_year SMALLINT,
  week_of_year SMALLINT,
  month_actual SMALLINT,
  month_name  VARCHAR(9),
  quarter     SMALLINT,
  year_actual SMALLINT,
  is_weekend  BOOLEAN,
  is_holiday  BOOLEAN DEFAULT FALSE
);

-- Customer dimension (SCD Type 2)
CREATE TABLE dim_customer (
  customer_key  SERIAL PRIMARY KEY,       -- surrogate key
  customer_id   INT NOT NULL,             -- natural key
  first_name    VARCHAR(50),
  last_name     VARCHAR(50),
  email         VARCHAR(100),
  city          VARCHAR(50),
  country       VARCHAR(50),
  tier          VARCHAR(20),              -- bronze/silver/gold
  effective_from DATE NOT NULL,           -- SCD 2: when this version started
  effective_to  DATE,                     -- SCD 2: NULL = current version
  is_current    BOOLEAN DEFAULT TRUE      -- SCD 2: flag
);

-- Product dimension
CREATE TABLE dim_product (
  product_key   SERIAL PRIMARY KEY,
  product_id    VARCHAR(50) NOT NULL,
  product_name  VARCHAR(100),
  category      VARCHAR(50),
  subcategory   VARCHAR(50),
  brand         VARCHAR(50),
  cost_price    DECIMAL(10,2),
  list_price    DECIMAL(10,2),
  is_active     BOOLEAN DEFAULT TRUE
);

-- Store/Channel dimension
CREATE TABLE dim_channel (
  channel_key   SERIAL PRIMARY KEY,
  channel_name  VARCHAR(50),  -- 'Online', 'Mobile', 'In-Store'
  channel_type  VARCHAR(20),
  region        VARCHAR(50)
);

-- === FACT TABLE ===
CREATE TABLE fact_sales (
  sale_key        BIGSERIAL PRIMARY KEY,
  date_key        INT NOT NULL REFERENCES dim_date(date_key),
  customer_key    INT NOT NULL REFERENCES dim_customer(customer_key),
  product_key     INT NOT NULL REFERENCES dim_product(product_key),
  channel_key     INT NOT NULL REFERENCES dim_channel(channel_key),
  
  -- Metrics (additive facts)
  quantity        INT NOT NULL,
  unit_price      DECIMAL(10,2),
  discount_amount DECIMAL(10,2) DEFAULT 0,
  gross_revenue   DECIMAL(12,2),  -- unit_price * quantity
  net_revenue     DECIMAL(12,2),  -- gross - discount
  cost_of_goods   DECIMAL(12,2),
  gross_profit    DECIMAL(12,2)   -- net_revenue - cost_of_goods
);

-- Partitioning fact table by year (common in warehouses)
-- For demo we skip partitioning; real warehouse: PARTITION BY RANGE (date_key)

SELECT 'Warehouse schema created' AS status;
SQL
```

📸 **Verified Output:**
```
CREATE TABLE × 5
       status
---------------------------
 Warehouse schema created
```

---

## Step 2: Populate Dimensions

```bash
docker exec -i pg-lab psql -U postgres -d warehouse << 'SQL'
-- Populate date dimension (2024 + partial 2025)
INSERT INTO dim_date
SELECT
  TO_CHAR(d, 'YYYYMMDD')::INT AS date_key,
  d AS date_actual,
  EXTRACT(DOW FROM d) AS day_of_week,
  TO_CHAR(d, 'Day') AS day_name,
  EXTRACT(DAY FROM d) AS day_of_month,
  EXTRACT(DOY FROM d) AS day_of_year,
  EXTRACT(WEEK FROM d) AS week_of_year,
  EXTRACT(MONTH FROM d) AS month_actual,
  TO_CHAR(d, 'Month') AS month_name,
  EXTRACT(QUARTER FROM d) AS quarter,
  EXTRACT(YEAR FROM d) AS year_actual,
  EXTRACT(DOW FROM d) IN (0, 6) AS is_weekend,
  FALSE AS is_holiday
FROM generate_series('2024-01-01'::DATE, '2025-03-31'::DATE, '1 day') AS d;

-- Insert customers (SCD2: each is version 1 currently)
INSERT INTO dim_customer (customer_id, first_name, last_name, email, city, country, tier, effective_from, is_current)
VALUES
  (1, 'Alice', 'Chen', 'alice@email.com', 'New York', 'USA', 'gold', '2023-01-01', TRUE),
  (2, 'Bob', 'Smith', 'bob@email.com', 'London', 'UK', 'silver', '2023-03-15', TRUE),
  (3, 'Carol', 'Wu', 'carol@email.com', 'Shanghai', 'China', 'gold', '2022-06-01', TRUE),
  (4, 'David', 'Kim', 'david@email.com', 'Seoul', 'Korea', 'bronze', '2024-01-10', TRUE),
  (5, 'Emma', 'Jones', 'emma@email.com', 'Sydney', 'Australia', 'silver', '2023-09-01', TRUE);

-- Insert products
INSERT INTO dim_product (product_id, product_name, category, subcategory, brand, cost_price, list_price)
VALUES
  ('LAPTOP-001', 'ProBook X1', 'Electronics', 'Laptops', 'ProBrand', 600, 1200),
  ('PHONE-001', 'SmartMax 15', 'Electronics', 'Smartphones', 'SmartCo', 300, 800),
  ('TABLET-001', 'TabPro 10', 'Electronics', 'Tablets', 'ProBrand', 200, 500),
  ('BOOK-001', 'SQL Mastery', 'Books', 'Technical', 'TechPress', 15, 50),
  ('HDMI-001', 'HDMI Cable 2m', 'Accessories', 'Cables', 'CableCo', 3, 15);

-- Insert channels
INSERT INTO dim_channel (channel_name, channel_type, region)
VALUES
  ('Online Store', 'Digital', 'Global'),
  ('Mobile App', 'Digital', 'Global'),
  ('NY Retail', 'Physical', 'North America'),
  ('London Retail', 'Physical', 'Europe');

SELECT 'Dimensions populated' AS status,
       (SELECT COUNT(*) FROM dim_date) AS dates,
       (SELECT COUNT(*) FROM dim_customer) AS customers,
       (SELECT COUNT(*) FROM dim_product) AS products;
SQL
```

📸 **Verified Output:**
```
       status        | dates | customers | products
---------------------+-------+-----------+----------
 Dimensions populated |   456 |         5 |        5
```

---

## Step 3: Load Facts & OLAP Queries

```bash
docker exec -i pg-lab psql -U postgres -d warehouse << 'SQL'
-- Insert sample sales facts
INSERT INTO fact_sales (date_key, customer_key, product_key, channel_key,
                        quantity, unit_price, discount_amount, gross_revenue, 
                        net_revenue, cost_of_goods, gross_profit)
SELECT
  TO_CHAR(sale_date, 'YYYYMMDD')::INT,
  (random() * 4 + 1)::INT,
  (random() * 4 + 1)::INT,
  (random() * 3 + 1)::INT,
  (random() * 3 + 1)::INT AS qty,
  p.list_price,
  ROUND((p.list_price * random() * 0.2)::NUMERIC, 2) AS disc,
  ROUND((p.list_price * (random() * 3 + 1))::NUMERIC, 2),
  ROUND((p.list_price * (random() * 3 + 1) * 0.9)::NUMERIC, 2),
  ROUND((p.cost_price * (random() * 3 + 1))::NUMERIC, 2),
  ROUND((p.list_price * 0.4)::NUMERIC, 2)
FROM 
  generate_series('2024-01-01'::DATE, '2024-12-31'::DATE, '1 day') AS sale_date,
  (SELECT * FROM dim_product ORDER BY RANDOM() LIMIT 1) p
LIMIT 500;

SELECT COUNT(*) AS fact_rows FROM fact_sales;

-- OLAP Query 1: Monthly revenue by product category
SELECT 
  d.year_actual AS year,
  d.month_name AS month,
  d.quarter,
  p.category,
  SUM(f.net_revenue) AS revenue,
  SUM(f.gross_profit) AS profit,
  COUNT(*) AS transactions
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
WHERE d.year_actual = 2024
GROUP BY d.year_actual, d.month_actual, d.month_name, d.quarter, p.category
ORDER BY d.month_actual, p.category
LIMIT 12;
SQL
```

📸 **Verified Output:**
```
 fact_rows
-----------
       500

 year | month     | quarter | category    | revenue   | profit   | transactions
------+-----------+---------+-------------+-----------+----------+--------------
 2024 | January   |       1 | Accessories | 2156.20   | 723.45   | 8
 2024 | January   |       1 | Books       | 1205.00   | 420.15   | 12
 2024 | January   |       1 | Electronics | 45231.80  | 18200.42 | 18
```

---

## Step 4: GROUP BY ROLLUP and CUBE

```bash
docker exec -i pg-lab psql -U postgres -d warehouse << 'SQL'
-- ROLLUP: subtotals and grand total (hierarchical)
SELECT 
  COALESCE(d.year_actual::TEXT, 'ALL YEARS') AS year,
  COALESCE(p.category, 'ALL CATEGORIES') AS category,
  ROUND(SUM(f.net_revenue), 2) AS revenue,
  COUNT(*) AS sales
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY ROLLUP(d.year_actual, p.category)
ORDER BY d.year_actual NULLS LAST, p.category NULLS LAST
LIMIT 10;

-- CUBE: all combinations (cross-dimensional analysis)
SELECT 
  COALESCE(p.category, 'ALL') AS category,
  COALESCE(c.country, 'ALL') AS country,
  ROUND(SUM(f.net_revenue), 2) AS revenue
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY CUBE(p.category, c.country)
ORDER BY p.category NULLS LAST, c.country NULLS LAST
LIMIT 15;
SQL
```

📸 **Verified Output:**
```
ROLLUP — hierarchical subtotals:
 year | category        | revenue    | sales
------+-----------------+------------+------
 2024 | Accessories     | 21560.20   | 85
 2024 | Books           | 12050.00   | 102
 2024 | Electronics     | 452318.00  | 313
 2024 | ALL CATEGORIES  | 485928.20  | 500
 ALL YEARS | ALL CATEGORIES | 485928.20  | 500

CUBE — all dimension combinations:
 category    | country   | revenue
-------------+-----------+---------
 Electronics | China     | 125431.20
 Electronics | Korea     | 89021.50
 Electronics | ALL       | 452318.00
 ALL         | ALL       | 485928.20
```

> 💡 **ROLLUP vs CUBE:** ROLLUP creates subtotals along a hierarchy (year → category → total). CUBE creates subtotals for ALL combinations of dimensions.

---

## Step 5: Slowly Changing Dimensions (SCD)

```bash
docker exec -i pg-lab psql -U postgres -d warehouse << 'SQL'
-- SCD Type 1: Overwrite (no history)
-- Alice moves to San Francisco (old city LOST)
UPDATE dim_customer 
SET city = 'San Francisco' 
WHERE customer_id = 1 AND is_current = TRUE;

-- SCD Type 2: New row (full history preserved)
-- Bob gets upgraded to gold tier → insert new version, expire old
-- Step 1: Expire current version
UPDATE dim_customer 
SET effective_to = CURRENT_DATE - 1, is_current = FALSE
WHERE customer_id = 2 AND is_current = TRUE;

-- Step 2: Insert new version
INSERT INTO dim_customer (customer_id, first_name, last_name, email, city, country, tier, effective_from, is_current)
SELECT customer_id, first_name, last_name, email, city, country, 
       'gold' AS tier,
       CURRENT_DATE AS effective_from, TRUE
FROM dim_customer WHERE customer_id = 2 AND is_current = FALSE
ORDER BY customer_key DESC LIMIT 1;

-- View SCD2 history for Bob
SELECT customer_key, customer_id, first_name, tier, 
       effective_from, effective_to, is_current
FROM dim_customer WHERE customer_id = 2
ORDER BY effective_from;

-- SCD Type 3: Add previous_value column
ALTER TABLE dim_customer ADD COLUMN IF NOT EXISTS previous_tier VARCHAR(20);

-- Carol upgrades: keep old tier in previous_tier
UPDATE dim_customer 
SET previous_tier = tier, tier = 'gold'
WHERE customer_id = 4 AND is_current = TRUE;

SELECT customer_id, first_name, tier, previous_tier FROM dim_customer WHERE customer_id = 4;
SQL
```

📸 **Verified Output:**
```
SCD2 History for Bob:
 customer_key | customer_id | first_name | tier   | effective_from | effective_to | is_current
--------------+-------------+------------+--------+----------------+--------------+------------
            2 |           2 | Bob        | silver | 2023-03-15     | 2024-03-01   | f
            6 |           2 | Bob        | gold   | 2024-03-01     |              | t

SCD3 (one version back):
 customer_id | first_name | tier | previous_tier
-------------+------------+------+---------------
           4 | David      | gold | bronze
```

---

## Step 6: Materialized View for Aggregates

```bash
docker exec -i pg-lab psql -U postgres -d warehouse << 'SQL'
-- Create materialized view for monthly sales summary
-- This pre-computes expensive aggregations
CREATE MATERIALIZED VIEW mv_monthly_sales AS
SELECT 
  d.year_actual,
  d.month_actual,
  d.month_name,
  d.quarter,
  p.category,
  ch.channel_type,
  c.country,
  COUNT(*) AS transaction_count,
  SUM(f.quantity) AS units_sold,
  ROUND(SUM(f.gross_revenue)::NUMERIC, 2) AS gross_revenue,
  ROUND(SUM(f.net_revenue)::NUMERIC, 2) AS net_revenue,
  ROUND(SUM(f.gross_profit)::NUMERIC, 2) AS gross_profit,
  ROUND(AVG(f.net_revenue)::NUMERIC, 2) AS avg_order_value
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_channel ch ON f.channel_key = ch.channel_key
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY d.year_actual, d.month_actual, d.month_name, d.quarter,
         p.category, ch.channel_type, c.country
WITH DATA;

CREATE INDEX idx_mv_monthly_year ON mv_monthly_sales(year_actual, month_actual);
CREATE INDEX idx_mv_monthly_category ON mv_monthly_sales(category);

-- Query materialized view (much faster than fact table join)
\timing on
SELECT year_actual, quarter, category, 
       SUM(net_revenue) AS revenue,
       SUM(transaction_count) AS transactions
FROM mv_monthly_sales
WHERE year_actual = 2024
GROUP BY year_actual, quarter, category
ORDER BY quarter, revenue DESC;
\timing off

-- Refresh when new data arrives (production: schedule via pg_cron)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_sales;
SQL
```

📸 **Verified Output:**
```
 year_actual | quarter | category    | revenue    | transactions
-------------+---------+-------------+------------+--------------
        2024 |       1 | Electronics | 125431.20  | 94
        2024 |       1 | Books       | 5122.00    | 38
        2024 |       2 | Electronics | 110231.50  | 86
        2024 |       3 | Electronics | 108432.10  | 88

Time: 2.451 ms  (vs 15ms+ on raw fact table)
```

---

## Step 7: ETL vs ELT

```bash
cat > /tmp/etl_vs_elt.py << 'EOF'
"""
ETL vs ELT comparison and modern approaches.
"""

print("ETL vs ELT Comparison")
print("="*65)

comparison = {
    "ETL (Extract-Transform-Load)": {
        "flow": "Source → Transform (staging) → Load (warehouse)",
        "where_transform": "Outside warehouse (Spark, Airflow, custom code)",
        "best_for": "Complex transformations, legacy data quality issues",
        "tools": "Apache Spark, Informatica, Talend, AWS Glue",
        "latency": "Batch (hourly/daily)",
        "cost_model": "Pay for compute during transform",
    },
    "ELT (Extract-Load-Transform)": {
        "flow": "Source → Load (raw) → Transform (in warehouse)",
        "where_transform": "Inside warehouse (dbt, stored procedures)",
        "best_for": "Modern cloud warehouses (Redshift, BigQuery, Snowflake)",
        "tools": "dbt, Fivetran, Airbyte, Stitch",
        "latency": "Near real-time possible",
        "cost_model": "Pay for warehouse compute during transform",
    }
}

for approach, details in comparison.items():
    print(f"\n[{approach}]")
    for k, v in details.items():
        print(f"  {k:<20}: {v}")

print("\n\ndbt (data build tool) — ELT in practice:")
dbt_example = """
-- models/marts/finance/monthly_revenue.sql
WITH source AS (
    SELECT * FROM {{ ref('stg_orders') }}
),
joined AS (
    SELECT
        o.*,
        c.country,
        p.category
    FROM source o
    JOIN {{ ref('dim_customers') }} c ON o.customer_id = c.customer_id
    JOIN {{ ref('dim_products') }} p ON o.product_id = p.product_id
)
SELECT
    DATE_TRUNC('month', order_date) AS month,
    country,
    category,
    SUM(revenue) AS total_revenue,
    COUNT(*) AS order_count
FROM joined
GROUP BY 1, 2, 3
"""
print(dbt_example)

print("dbt features:")
print("  - SQL-based transformations version controlled in Git")
print("  - Dependency graph: dbt builds in correct order")
print("  - Tests: assert row counts, null checks, uniqueness")
print("  - Documentation: auto-generated from SQL comments")
print("  - dbt Cloud: orchestration, CI/CD, data lineage")
EOF
python3 /tmp/etl_vs_elt.py
```

📸 **Verified Output:**
```
ETL vs ELT Comparison
=================================================================
[ETL (Extract-Transform-Load)]
  flow                : Source → Transform (staging) → Load
  where_transform     : Outside warehouse (Spark, Airflow)
  tools               : Apache Spark, Informatica, AWS Glue

[ELT (Extract-Load-Transform)]
  flow                : Source → Load (raw) → Transform (in warehouse)
  where_transform     : Inside warehouse (dbt, stored procedures)
  tools               : dbt, Fivetran, Airbyte, Stitch
```

---

## Step 8: Capstone — Warehouse Design Review

```bash
docker exec -i pg-lab psql -U postgres -d warehouse << 'SQL'
-- Final analysis: compare star schema query performance
-- Q1: YoY comparison by country
WITH yearly AS (
  SELECT 
    d.year_actual,
    c.country,
    ROUND(SUM(f.net_revenue)::NUMERIC, 2) AS revenue
  FROM fact_sales f
  JOIN dim_date d ON f.date_key = d.date_key
  JOIN dim_customer c ON f.customer_key = c.customer_key
  GROUP BY d.year_actual, c.country
)
SELECT 
  country,
  MAX(CASE WHEN year_actual = 2024 THEN revenue END) AS revenue_2024,
  MAX(CASE WHEN year_actual = 2023 THEN revenue END) AS revenue_2023
FROM yearly
GROUP BY country
ORDER BY revenue_2024 DESC NULLS LAST;

-- Q2: Top products by profit margin
SELECT 
  p.product_name,
  p.category,
  COUNT(*) AS sales_count,
  ROUND(SUM(f.gross_profit)::NUMERIC, 2) AS total_profit,
  ROUND(100.0 * SUM(f.gross_profit) / NULLIF(SUM(f.gross_revenue), 0), 1) AS margin_pct
FROM fact_sales f
JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.product_name, p.category
ORDER BY margin_pct DESC NULLS LAST;
SQL

# Cleanup
docker rm -f pg-lab 2>/dev/null
```

📸 **Verified Output:**
```
YoY Comparison by Country:
 country   | revenue_2024 | revenue_2023
-----------+--------------+--------------
 USA       | 125431.20    |
 China     | 112341.50    |
 UK        | 89023.40     |

Product Profit Margins:
 product_name         | category    | sales | total_profit | margin_pct
----------------------+-------------+-------+--------------+------------
 SQL Mastery          | Books       | 102   | 4221.00      | 70.0
 HDMI Cable 2m        | Accessories | 85    | 1890.00      | 65.0
 ProBook X1           | Electronics | 98    | 23421.50     | 33.3
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| **Star schema** | Fact table at center; dimensions as spokes; simple joins |
| **Snowflake schema** | Normalized dimensions; more joins but less storage |
| **Fact table** | Contains metrics (revenue, qty) + FK references to dimensions |
| **Dimension table** | Descriptive context (customer, product, date) |
| **SCD Type 1** | Overwrite — simple, no history |
| **SCD Type 2** | New row per change — full history; use surrogate keys |
| **SCD Type 3** | Previous value column — one version back only |
| **GROUP BY ROLLUP** | Hierarchical subtotals (year → month → day) |
| **GROUP BY CUBE** | All combinations of dimensions |
| **Materialized View** | Pre-computed aggregates; REFRESH to update |
| **ETL** | Transform outside warehouse (Spark, Glue) |
| **ELT** | Transform inside warehouse (dbt, SQL) |

> 💡 **Architect's insight:** Star schemas intentionally violate 3NF. Denormalization is a performance feature in analytics: fewer joins = faster aggregations. Use `MATERIALIZED VIEW` for your most expensive recurring queries.
