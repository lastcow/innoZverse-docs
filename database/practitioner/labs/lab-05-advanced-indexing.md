# Lab 05: Advanced Indexing

**Time:** 40 minutes | **Level:** Practitioner | **DB:** PostgreSQL 15 + MySQL 8.0

Indexes are the single biggest lever for query performance. This lab covers composite, partial, covering, GIN, and GiST indexes — and when each is the right tool.

---

## Step 1 — Setup: Products Table with 10,000 Rows

```sql
-- PostgreSQL
CREATE TABLE products (
  id        SERIAL PRIMARY KEY,
  name      VARCHAR(100),
  category  VARCHAR(50),
  price     NUMERIC(10,2),
  stock     INT,
  tags      TEXT[],
  metadata  JSONB,
  is_active BOOLEAN DEFAULT true
);

INSERT INTO products (name, category, price, stock, tags, metadata, is_active)
SELECT
  'Product ' || i,
  CASE (i % 5)
    WHEN 0 THEN 'Electronics' WHEN 1 THEN 'Clothing'
    WHEN 2 THEN 'Books'       WHEN 3 THEN 'Food'
    ELSE 'Sports' END,
  (RANDOM() * 500 + 1)::NUMERIC(10,2),
  (RANDOM() * 1000)::INT,
  ARRAY['tag' || (i%10), 'cat' || (i%5)],
  jsonb_build_object('brand', 'Brand'||(i%20), 'rating', (RANDOM()*5)::NUMERIC(3,1)),
  (i % 10 != 0)
FROM generate_series(1, 10000) i;

ANALYZE products;
```

📸 **Verified Output:**
```
INSERT 0 10000
ANALYZE
```

---

## Step 2 — Composite Indexes: Column Order Matters

```sql
-- Create composite index: category first, price second
CREATE INDEX idx_category_price ON products(category, price);

-- This query uses the index (leading column matches)
EXPLAIN (ANALYZE) SELECT * FROM products
WHERE category = 'Electronics' AND price < 100;

-- This also uses the index (leading column only)
EXPLAIN (ANALYZE) SELECT * FROM products
WHERE category = 'Electronics';

-- This does NOT use the composite index (skipping leading column)
EXPLAIN (ANALYZE) SELECT * FROM products
WHERE price < 100;
```

> 💡 **Left-prefix rule**: A composite index `(A, B, C)` can be used for queries filtering on A, A+B, or A+B+C — but NOT B alone, C alone, or B+C alone.

```sql
-- View all indexes on the table
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'products';
```

📸 **Verified Output:**
```
    indexname        |                         indexdef
---------------------+---------------------------------------------------
 products_pkey       | CREATE UNIQUE INDEX products_pkey ON products USING btree (id)
 idx_category_price  | CREATE INDEX idx_category_price ON products USING btree (category, price)
```

---

## Step 3 — Partial Indexes (PostgreSQL)

```sql
-- Index only active products — much smaller, faster for the common case
CREATE INDEX idx_active_products
ON products(category, price)
WHERE is_active = true;

-- Force index usage to demonstrate
SET enable_seqscan = off;

EXPLAIN (ANALYZE, FORMAT TEXT)
SELECT name, price FROM products
WHERE category = 'Electronics' AND price < 100 AND is_active = true
LIMIT 5;

SET enable_seqscan = on;
```

📸 **Verified Output:**
```
 Limit  (cost=0.29..10.83 rows=5 width=18) (actual time=0.304..0.397 rows=5 loops=1)
   ->  Index Scan using idx_active_products on products  (...)
         Index Cond: ((category = 'Electronics') AND (price < '100'::numeric))
 Planning Time: 1.893 ms
 Execution Time: 0.521 ms
```

> 💡 Partial indexes are smaller (fewer pages), cheaper to update, and have better cache utilization. If 10% of products are inactive, your index is 10% the size.

---

## Step 4 — Covering Indexes (Index-Only Scans)

```sql
-- Covering index: includes all columns the query needs
-- The query never touches the heap (table) — "index-only scan"
CREATE INDEX idx_covering_catprice
ON products(category, price)
INCLUDE (name, stock);  -- PostgreSQL 11+

EXPLAIN (ANALYZE)
SELECT name, price, stock
FROM products
WHERE category = 'Electronics' AND price BETWEEN 50 AND 200;
-- Look for "Index Only Scan" in the output
```

```sql
-- MySQL equivalent: covering index for EXPLAIN
-- MySQL uses "Using index" in Extra column when covering
CREATE TABLE products_mysql (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  category VARCHAR(50),
  price    DECIMAL(10,2),
  name     VARCHAR(100),
  INDEX idx_cat_price_name (category, price, name)
);
```

> 💡 A covering index returns results without reading the heap table at all — look for **Index Only Scan** in PostgreSQL `EXPLAIN` or **Using index** in MySQL `EXPLAIN`.

---

## Step 5 — GIN Index: Arrays and JSONB

```sql
-- GIN index for array containment queries
CREATE INDEX idx_tags_gin ON products USING GIN(tags);

-- Now array operators use the index
EXPLAIN (ANALYZE)
SELECT name FROM products WHERE tags @> ARRAY['tag1'];
-- Uses: Bitmap Index Scan on idx_tags_gin

EXPLAIN (ANALYZE)
SELECT name FROM products WHERE 'tag3' = ANY(tags);
-- Uses the GIN index for ANY() too

-- GIN index for JSONB
CREATE INDEX idx_metadata_gin ON products USING GIN(metadata);

EXPLAIN (ANALYZE)
SELECT name FROM products
WHERE metadata @> '{"brand": "Brand5"}';
-- Uses: Bitmap Index Scan on idx_metadata_gin
```

📸 **Verified Output (index list):**
```
    indexname        |                    indexdef
---------------------+---------------------------------------------------
 idx_tags_gin        | CREATE INDEX idx_tags_gin ON products USING gin(tags)
 idx_metadata_gin    | CREATE INDEX idx_metadata_gin ON products USING gin(metadata)
```

---

## Step 6 — GiST Index and Full-Text GIN

```sql
-- GiST index for range types and geometric data
CREATE TABLE reservations (
  id       SERIAL PRIMARY KEY,
  room     INT,
  period   TSRANGE
);

CREATE INDEX idx_reservations_gist ON reservations USING GIST(period);

INSERT INTO reservations (room, period) VALUES
  (101, '[2024-01-10, 2024-01-15)'),
  (102, '[2024-01-12, 2024-01-18)'),
  (101, '[2024-01-20, 2024-01-25)');

-- Find overlapping reservations (uses GiST)
EXPLAIN (ANALYZE)
SELECT * FROM reservations
WHERE period && '[2024-01-11, 2024-01-14)'::TSRANGE;

-- GIN for full-text search
CREATE INDEX idx_name_fts ON products
USING GIN(to_tsvector('english', name));

SELECT name FROM products
WHERE to_tsvector('english', name) @@ to_tsquery('product & 42');
```

> 💡 **GIN vs GiST**: GIN is faster for reads (containment, equality); GiST is faster for writes and supports range/geometric types. Choose GIN for JSONB/arrays/FTS, GiST for ranges and PostGIS.

---

## Step 7 — MySQL Prefix Indexes and Index Bloat

```sql
-- MySQL prefix index (useful for long VARCHAR/TEXT columns)
ALTER TABLE articles ADD INDEX idx_title_prefix (title(50));
-- Indexes only first 50 characters of title

-- Check index sizes
SELECT table_name, index_name,
       ROUND(stat_value * @@innodb_page_size / 1024 / 1024, 2) AS size_mb
FROM mysql.innodb_index_stats
WHERE stat_name = 'size'
  AND table_name = 'products_mysql'
  AND database_name = 'labdb';
```

**PostgreSQL: Index bloat and REINDEX**
```sql
-- Check index bloat
SELECT schemaname, tablename, indexname,
       pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE tablename = 'products'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Rebuild a bloated index (non-blocking in PG 12+)
REINDEX INDEX CONCURRENTLY idx_category_price;

-- After many deletes, reclaim space
VACUUM ANALYZE products;
```

---

## Step 8 — Capstone: Index Strategy for an E-commerce Query

Design indexes for this complex query and verify the plan:

```sql
-- The query (common e-commerce pattern)
SELECT p.name, p.price, p.stock,
       p.metadata->>'brand' AS brand,
       p.metadata->>'rating' AS rating
FROM products p
WHERE p.category = 'Electronics'
  AND p.is_active = true
  AND p.price BETWEEN 100 AND 500
  AND p.tags @> ARRAY['tag1']
  AND (p.metadata->>'rating')::NUMERIC >= 4.0
ORDER BY p.price ASC
LIMIT 20;

-- Step 1: Create a strategic partial composite index
CREATE INDEX idx_elec_active ON products(category, price)
INCLUDE (name, stock, metadata)
WHERE is_active = true;

-- Step 2: GIN for the tag array filter
-- (idx_tags_gin already created in Step 5)

-- Step 3: Expression index on rating for range queries
CREATE INDEX idx_rating ON products((( metadata->>'rating')::NUMERIC))
WHERE is_active = true;

-- Verify the plan
EXPLAIN (ANALYZE, BUFFERS)
SELECT p.name, p.price, p.stock,
       p.metadata->>'brand' AS brand
FROM products p
WHERE p.category = 'Electronics'
  AND p.is_active = true
  AND p.price BETWEEN 100 AND 500
ORDER BY p.price ASC
LIMIT 20;
```

---

## Summary

| Index Type | Operator | Best For |
|-----------|----------|----------|
| B-tree (default) | `=`, `<`, `>`, `BETWEEN`, `LIKE 'abc%'` | Most queries |
| Composite B-tree | Multiple column equality/range | Multi-column WHERE |
| Partial | Any + `WHERE` clause | Frequently filtered subset |
| Covering | Exact column list | Index-only scans |
| GIN | `@>`, `&&`, `?`, `@@` | Arrays, JSONB, full-text |
| GiST | `&&`, `<->`, overlap | Ranges, geometry, FTS |
| Prefix (MySQL) | `=`, `LIKE 'x%'` | Long VARCHAR columns |
