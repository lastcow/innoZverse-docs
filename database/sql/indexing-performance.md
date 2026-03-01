# Indexing & Performance

## Why Indexes Matter

```sql
-- Without index: Full table scan (slow on large tables)
SELECT * FROM orders WHERE user_id = 12345;
-- → MySQL scans every row

-- With index: B-tree lookup (fast)
CREATE INDEX idx_user_id ON orders(user_id);
-- → MySQL jumps directly to matching rows
```

## Index Types

```sql
-- Single column index
CREATE INDEX idx_email ON users(email);

-- Composite index (order matters!)
CREATE INDEX idx_user_date ON orders(user_id, created_at);
-- ✅ Efficient: WHERE user_id = 1 AND created_at > '2026-01-01'
-- ✅ Efficient: WHERE user_id = 1
-- ❌ Inefficient: WHERE created_at > '2026-01-01' (missing leading column)

-- Unique index
CREATE UNIQUE INDEX idx_unique_email ON users(email);

-- Partial index (PostgreSQL)
CREATE INDEX idx_active_users ON users(email) WHERE status = 'active';
```

## EXPLAIN — Analyze Query Performance

```sql
-- MySQL
EXPLAIN SELECT * FROM orders WHERE user_id = 100;
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 100;

-- PostgreSQL
EXPLAIN SELECT * FROM orders WHERE user_id = 100;
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM orders WHERE user_id = 100;

-- Look for:
-- ✅ index scan / index seek (fast)
-- ❌ full table scan / seq scan on large tables (slow)
-- ❌ high row estimates vs actual rows (stale statistics)
```

## Common Performance Issues

```sql
-- ❌ SELECT * (fetches unnecessary columns)
SELECT * FROM users;
-- ✅ Select only what you need
SELECT id, name, email FROM users;

-- ❌ N+1 query problem
-- Fetching orders, then querying user for each order separately
-- ✅ Use JOIN instead
SELECT u.name, o.total FROM orders o JOIN users u ON o.user_id = u.id;

-- ❌ Function on indexed column (prevents index use)
WHERE YEAR(created_at) = 2026
-- ✅ Range query (uses index)
WHERE created_at >= '2026-01-01' AND created_at < '2027-01-01'

-- ❌ Leading wildcard (can't use index)
WHERE name LIKE '%Surface%'
-- ✅ Prefix search (uses index)
WHERE name LIKE 'Surface%'
```
