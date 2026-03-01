# Advanced Query Optimization

## Query Planning Deep Dive

```sql
-- PostgreSQL: Full EXPLAIN output
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT u.name, COUNT(o.id) as order_count, SUM(o.total) as revenue
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2026-01-01'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 5
ORDER BY revenue DESC
LIMIT 20;

-- Key metrics to watch:
-- actual time=X.X..Y.Y  → execution time per node
-- rows=N               → actual rows vs estimated
-- Buffers: hit=N        → cache hits (good)
-- Buffers: read=N       → disk reads (expensive)
```

## Partitioning

```sql
-- PostgreSQL table partitioning (by date)
CREATE TABLE orders (
    id BIGINT,
    user_id INT,
    total DECIMAL(10,2),
    created_at TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2026_01 PARTITION OF orders
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

CREATE TABLE orders_2026_02 PARTITION OF orders
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

-- Query automatically uses correct partition
SELECT * FROM orders WHERE created_at >= '2026-01-15';
-- → Only scans orders_2026_01 partition
```

## Connection Pooling (PgBouncer)

```ini
# pgbouncer.ini
[databases]
mydb = host=127.0.0.1 port=5432 dbname=mydb

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
pool_mode = transaction      # transaction-level pooling
max_client_conn = 10000
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5

# With pooling: 10,000 app connections → 20 actual DB connections
```

## Materialized Views

```sql
-- Pre-compute expensive aggregations
CREATE MATERIALIZED VIEW daily_revenue AS
SELECT
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as orders,
    SUM(total) as revenue,
    AVG(total) as avg_order
FROM orders
GROUP BY 1;

CREATE UNIQUE INDEX ON daily_revenue(date);

-- Fast query
SELECT * FROM daily_revenue
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date;

-- Refresh (schedule with cron)
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_revenue;
```
