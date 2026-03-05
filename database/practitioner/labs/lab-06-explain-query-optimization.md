# Lab 06: EXPLAIN and Query Optimization

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MySQL 8.0 + PostgreSQL 15

`EXPLAIN` reveals how the query planner executes your SQL. Reading execution plans is a core skill — it shows whether indexes are used, where time is spent, and which joins are expensive.

---

## Step 1 — MySQL: Basic EXPLAIN

```sql
USE labdb;

-- Create a meaningful dataset
CREATE INDEX idx_customer ON orders(customer);
CREATE INDEX idx_product  ON orders(product);

-- Basic EXPLAIN
EXPLAIN
SELECT customer, COUNT(*) AS cnt, SUM(total) AS total_spent
FROM orders
WHERE customer = 'Alice'
GROUP BY customer;
```

📸 **Verified Output:**
```
id  select_type  table   partitions  type  possible_keys  key           key_len  ref    rows  filtered  Extra
1   SIMPLE       orders  NULL        ref   idx_customer   idx_customer  403      const  2     100.00    NULL
```

**Key columns to read:**
| Column | Meaning |
|--------|---------|
| `type` | Join type: `const` > `eq_ref` > `ref` > `range` > `index` > `ALL` |
| `key` | Index actually used (NULL = full scan) |
| `rows` | Estimated rows examined |
| `filtered` | % of rows after WHERE filter |
| `Extra` | `Using index` = covering index; `Using filesort` = expensive sort |

> 💡 `type=ALL` means full table scan — usually bad. `type=ref` or `type=range` means index is used.

---

## Step 2 — MySQL: EXPLAIN FORMAT=JSON

```sql
EXPLAIN FORMAT=JSON
SELECT o.customer, o.product, o.total
FROM orders o
WHERE o.customer IN ('Alice', 'Bob')
  AND o.total > 40
ORDER BY o.total DESC\G
```

The JSON format reveals:
- `cost_info`: estimated cost per node
- `used_columns`: which columns are read
- `attached_condition`: pushed-down filters
- `ordering_operation`: whether filesort is needed

> 💡 Add `EXPLAIN ANALYZE` in MySQL 8.0.18+ to get **actual** execution statistics alongside estimates.

---

## Step 3 — PostgreSQL: EXPLAIN ANALYZE

```sql
-- Basic plan
EXPLAIN SELECT * FROM products WHERE category = 'Electronics';

-- Full analysis with actual timings
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT p.category, COUNT(*) AS cnt, AVG(p.price) AS avg_price
FROM products p
WHERE p.is_active = true
  AND 'tag1' = ANY(p.tags)
GROUP BY p.category
ORDER BY cnt DESC;
```

📸 **Verified Output:**
```
 Sort  (cost=427.87..427.88 rows=5 width=47) (actual time=8.066..8.068 rows=1 loops=1)
   Sort Key: (count(*)) DESC
   Sort Method: quicksort  Memory: 25kB
   Buffers: shared hit=199
   ->  HashAggregate  (cost=427.75..427.81 ...) (actual time=7.916..7.918 rows=1 loops=1)
         ->  Seq Scan on products p  (cost=0.00..421.00 ...) (actual time=0.033..7.123 rows=1000 loops=1)
               Filter: (is_active AND ('tag1'::text = ANY (tags)))
               Rows Removed by Filter: 9000
 Planning Time: 2.140 ms
 Execution Time: 8.437 ms
```

---

## Step 4 — Reading PostgreSQL Execution Plans

**Node types and what they mean:**

| Node | Meaning |
|------|---------|
| **Seq Scan** | Full table scan — reads every row |
| **Index Scan** | Follows index to heap; good for selective queries |
| **Index Only Scan** | Never touches heap — all data in index |
| **Bitmap Index Scan + Bitmap Heap Scan** | Batches index lookups, then reads heap |
| **Hash Join** | Builds hash table from smaller relation |
| **Nested Loop** | For each outer row, scans inner — good for small tables |
| **Merge Join** | Requires both inputs sorted; good for large sorted data |
| **Sort** | Explicit sort (memory or disk) |
| **HashAggregate** | GROUP BY via hash map |

```sql
-- Force seq scan vs index scan comparison
SET enable_seqscan = off;
EXPLAIN (ANALYZE)
SELECT name, price FROM products
WHERE category = 'Electronics' AND price < 100 AND is_active = true
LIMIT 5;
SET enable_seqscan = on;
```

📸 **Verified Output (with index):**
```
 Limit  (cost=0.29..10.83 rows=5 width=18) (actual time=0.304..0.397 rows=5 loops=1)
   ->  Index Scan using idx_active_products on products
         Index Cond: ((category = 'Electronics') AND (price < '100'::numeric))
 Planning Time: 1.893 ms
 Execution Time: 0.521 ms
```

---

## Step 5 — Cost Model and Statistics

```sql
-- PostgreSQL cost parameters
SHOW seq_page_cost;        -- default 1.0
SHOW random_page_cost;     -- default 4.0 (SSD: set to 1.1)
SHOW cpu_tuple_cost;       -- default 0.01

-- View table statistics used by planner
SELECT attname, n_distinct, correlation, most_common_vals
FROM pg_stats
WHERE tablename = 'products' AND attname = 'category';

-- Update statistics after bulk load
ANALYZE products;
ANALYZE products(category, price);  -- specific columns
```

> 💡 If your planner makes bad choices, statistics may be stale. Always `ANALYZE` after bulk inserts/updates. Increase `default_statistics_target` for high-cardinality columns.

```sql
-- Increase statistics target for better estimates on a skewed column
ALTER TABLE products
  ALTER COLUMN category SET STATISTICS 500;
ANALYZE products;
```

---

## Step 6 — Identifying Slow Queries

**MySQL slow query log:**
```sql
-- Enable slow query log
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 1;   -- log queries > 1 second
SET GLOBAL slow_query_log_file = '/var/log/mysql/slow.log';

-- Check slow query variables
SHOW VARIABLES LIKE 'slow_query%';
SHOW VARIABLES LIKE 'long_query_time';

-- View in performance_schema
SELECT digest_text, count_star, avg_timer_wait/1e12 AS avg_sec
FROM performance_schema.events_statements_summary_by_digest
ORDER BY avg_timer_wait DESC
LIMIT 5;
```

**PostgreSQL:**
```sql
-- In postgresql.conf:
-- log_min_duration_statement = 1000   # log queries > 1s
-- log_statement = 'all'               # log all (dev only)

-- pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

SELECT query, calls, total_exec_time/calls AS avg_ms,
       rows/calls AS avg_rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 5;
```

---

## Step 7 — N+1 Pattern Detection

The N+1 anti-pattern: execute one query to get N records, then execute N more queries for related data.

```sql
-- BAD: N+1 pattern (would be done in app code)
-- Query 1: get all orders
SELECT id, customer FROM orders;

-- For each order (N queries):
-- SELECT * FROM products WHERE product = ? (repeated N times)

-- GOOD: Use JOIN instead
SELECT o.id, o.customer, o.product, o.total
FROM orders o
WHERE o.total > 40
ORDER BY o.total DESC;

-- BETTER: Use EXISTS for existence check
SELECT o.customer, COUNT(*) AS expensive_orders
FROM orders o
WHERE EXISTS (
  SELECT 1 FROM orders o2
  WHERE o2.customer = o.customer AND o2.total > 50
)
GROUP BY o.customer;
```

> 💡 In PostgreSQL, use `pg_stat_activity` to catch long-running queries in real-time: `SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active';`

---

## Step 8 — Capstone: Query Tuning Workflow

Apply the full optimization workflow to a slow query:

```sql
-- Step 1: Identify the query
EXPLAIN (ANALYZE, BUFFERS)
SELECT u.username,
       COUNT(p.id) AS post_count,
       SUM(pa.views) AS total_views,
       ROUND(AVG(pa.engagement_rate), 2) AS avg_engagement
FROM social_users u
LEFT JOIN social_posts p ON p.user_id = u.id
LEFT JOIN post_analytics pa ON pa.post_id = p.id
WHERE u.created_at > NOW() - INTERVAL '90 days'
GROUP BY u.id, u.username
HAVING SUM(pa.views) > 1000
ORDER BY total_views DESC;

-- Step 2: Add targeted indexes
CREATE INDEX idx_posts_user_id ON social_posts(user_id);
CREATE INDEX idx_analytics_post_id ON post_analytics(post_id);
CREATE INDEX idx_users_created ON social_users(created_at);

-- Step 3: Re-run EXPLAIN to verify improvement
-- Step 4: Check if covering index helps further
CREATE INDEX idx_posts_covering ON social_posts(user_id)
INCLUDE (id);
```

---

## Summary

| Tool | Purpose |
|------|---------|
| `EXPLAIN` | Show estimated plan (no execution) |
| `EXPLAIN ANALYZE` | Execute and show actual vs estimated |
| `EXPLAIN (BUFFERS)` | Add buffer cache hit/miss info |
| `EXPLAIN FORMAT=JSON` | Machine-readable plan |
| `pg_stats` | Planner statistics per column |
| `ANALYZE` | Refresh table statistics |
| `pg_stat_statements` | Aggregate slow query tracking |
| `performance_schema` (MySQL) | Query digest and timing |
