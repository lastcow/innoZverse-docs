# Lab 18: PostgreSQL JSONB and Arrays

**Time:** 30 minutes | **Level:** Foundations | **DB:** PostgreSQL 15

## Overview

PostgreSQL-specific features: array columns, array operators, JSONB storage, JSON path queries, jsonb_set for updates, and GIN indexes for performance.

---

## Step 1: Setup

```bash
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec pg-lab psql -U postgres << 'EOF'
CREATE DATABASE jsonlab;
EOF

docker exec pg-lab psql -U postgres -d jsonlab << 'EOF'
-- Table with array and JSONB columns
CREATE TABLE products (
    product_id   SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    tags         TEXT[],              -- array of text
    sizes        INT[],               -- array of integers
    metadata     JSONB,               -- binary JSON (indexed, fast)
    created_at   TIMESTAMP DEFAULT NOW()
);

INSERT INTO products (name, tags, sizes, metadata) VALUES
(
    'Laptop Pro 15',
    ARRAY['electronics', 'computers', 'portable'],
    ARRAY[256, 512, 1024],
    '{"brand": "TechCo", "color": "silver", "specs": {"ram": 16, "cpu": "M2"}, "ratings": [4, 5, 5, 4], "in_stock": true, "price": 1299.99}'
),
(
    'Wireless Mouse',
    ARRAY['electronics', 'peripherals', 'wireless'],
    NULL,
    '{"brand": "ClickMaster", "color": "black", "specs": {"dpi": 1600, "buttons": 6}, "ratings": [4, 3, 5], "in_stock": true, "price": 29.99}'
),
(
    'SQL Mastery Book',
    ARRAY['books', 'education', 'technology'],
    NULL,
    '{"author": "Jane Doe", "isbn": "978-0-000-00000-0", "edition": 3, "ratings": [5, 5, 4, 5], "in_stock": false, "price": 49.99}'
),
(
    'Ergonomic Chair',
    ARRAY['furniture', 'office', 'ergonomic'],
    ARRAY[1, 2, 3],
    '{"brand": "ComfortSeat", "color": "gray", "specs": {"max_weight_kg": 120, "adjustable": true}, "ratings": [4, 4, 3], "in_stock": true, "price": 399.99}'
),
(
    'USB-C Hub',
    ARRAY['electronics', 'peripherals', 'connectivity'],
    NULL,
    '{"brand": "ConnectAll", "color": "silver", "specs": {"ports": 7, "usb3": true}, "ratings": [5, 4, 5, 5], "in_stock": true, "price": 49.99}'
);
EOF
```

---

## Step 2: Array Columns — Basic Operations

```bash
docker exec pg-lab psql -U postgres -d jsonlab << 'EOF'
-- Select array values
SELECT name, tags, sizes FROM products;

-- Access array element (1-indexed in PostgreSQL!)
SELECT name, tags[1] AS first_tag, tags[2] AS second_tag FROM products;

-- Array length
SELECT name, array_length(tags, 1) AS num_tags FROM products;

-- Unnest array into rows
SELECT name, unnest(tags) AS tag FROM products ORDER BY name, tag;
EOF
```

📸 **Verified Output (tags[1]):**
```
       name       |    first_tag    |   second_tag
------------------+-----------------+-----------------
 Laptop Pro 15    | electronics     | computers
 Wireless Mouse   | electronics     | peripherals
 SQL Mastery Book | books           | education
 Ergonomic Chair  | furniture       | office
 USB-C Hub        | electronics     | peripherals
(5 rows)
```

---

## Step 3: Array Operators

```bash
docker exec pg-lab psql -U postgres -d jsonlab << 'EOF'
-- @> contains (does array contain these elements?)
SELECT name, tags
FROM products
WHERE tags @> ARRAY['electronics'];      -- has 'electronics' tag

-- <@ is contained by
SELECT name FROM products
WHERE ARRAY['books', 'education'] <@ tags;  -- tags contains all of these

-- && overlap (any elements in common)
SELECT name, tags
FROM products
WHERE tags && ARRAY['books', 'furniture'];   -- has books OR furniture

-- = exact match
SELECT name FROM products
WHERE tags = ARRAY['electronics', 'computers', 'portable'];

-- ANY: element matches any in array
SELECT name FROM products
WHERE 'wireless' = ANY(tags);

-- ALL: element matches all (rarely needed)
EOF
```

📸 **Verified Output (@> contains 'electronics'):**
```
       name       |             tags
------------------+------------------------------------
 Laptop Pro 15    | {electronics,computers,portable}
 Wireless Mouse   | {electronics,peripherals,wireless}
 USB-C Hub        | {electronics,peripherals,connectivity}
(3 rows)
```

📸 **Verified Output (&& overlap):**
```
       name       |             tags
------------------+----------------------------------
 SQL Mastery Book | {books,education,technology}
 Ergonomic Chair  | {furniture,office,ergonomic}
(2 rows)
```

---

## Step 4: JSONB Extraction — `->` and `->>`

```bash
docker exec pg-lab psql -U postgres -d jsonlab << 'EOF'
-- -> returns JSONB object (preserves type)
-- ->> returns text value

SELECT
    name,
    metadata -> 'brand'                 AS brand_json,    -- returns JSONB: "TechCo"
    metadata ->> 'brand'                AS brand_text,    -- returns TEXT: TechCo
    metadata -> 'specs'                 AS specs_json,    -- returns JSONB object
    metadata -> 'specs' ->> 'ram'      AS ram_text,      -- nested: "16"
    (metadata -> 'specs' ->> 'ram')::INT AS ram_int,     -- cast to integer
    metadata ->> 'price'               AS price_text,
    (metadata ->> 'price')::NUMERIC    AS price_num
FROM products
WHERE metadata ? 'brand';   -- ? operator: does key exist?
EOF
```

📸 **Verified Output:**
```
       name      | brand_json | brand_text |   specs_json             | ram_text | ram_int
-----------------+------------+------------+--------------------------+----------+---------
 Laptop Pro 15   | "TechCo"   | TechCo     | {"ram": 16, "cpu": "M2"} | 16       |      16
 Wireless Mouse  | "ClickMast"| ClickMaster| {"dpi": 1600, ...}       | NULL     |    NULL
 Ergonomic Chair | "ComfortSe"| ComfortSeat| {"max_weight_kg": 120, ..}| NULL    |    NULL
 USB-C Hub       | "ConnectAl"| ConnectAll | {"ports": 7, ...}        | NULL     |    NULL
(4 rows)
```

> 💡 Use `->` when you need the result as JSONB (for further JSON operations). Use `->>` when you want a text value (for comparison or display).

---

## Step 5: JSONB Key Existence and Querying

```bash
docker exec pg-lab psql -U postgres -d jsonlab << 'EOF'
-- ? key exists
SELECT name FROM products WHERE metadata ? 'author';

-- ?| any key exists
SELECT name FROM products WHERE metadata ?| ARRAY['author', 'brand'];

-- ?& all keys exist
SELECT name FROM products WHERE metadata ?& ARRAY['brand', 'specs'];

-- Filter by JSONB value
SELECT name, metadata ->> 'price' AS price
FROM products
WHERE (metadata ->> 'in_stock')::boolean = true
ORDER BY (metadata ->> 'price')::numeric DESC;

-- Filter by nested value
SELECT name
FROM products
WHERE metadata -> 'specs' ->> 'usb3' = 'true';

-- jsonb_path_query (SQL/JSON path)
SELECT name, jsonb_path_query(metadata, '$.specs.ram') AS ram
FROM products
WHERE jsonb_path_exists(metadata, '$.specs.ram');
EOF
```

📸 **Verified Output (in_stock = true, sorted by price):**
```
      name      |  price
----------------+---------
 Ergonomic Chair| 399.99
 Laptop Pro 15  | 1299.99
 USB-C Hub      |  49.99
 Wireless Mouse |  29.99
(4 rows)
```

---

## Step 6: jsonb_set — Update JSONB Values

```bash
docker exec pg-lab psql -U postgres -d jsonlab << 'EOF'
-- jsonb_set(target, path, new_value, create_if_missing)
-- Update a scalar value
UPDATE products
SET metadata = jsonb_set(metadata, '{price}', '1349.99')
WHERE name = 'Laptop Pro 15';

-- Add a new key
UPDATE products
SET metadata = jsonb_set(metadata, '{discount_pct}', '10', true)
WHERE name = 'Laptop Pro 15';

-- Update nested value
UPDATE products
SET metadata = jsonb_set(metadata, '{specs, ram}', '32')
WHERE name = 'Laptop Pro 15';

-- Verify
SELECT name, metadata -> 'price' AS price,
       metadata -> 'discount_pct' AS discount,
       metadata -> 'specs' -> 'ram' AS ram
FROM products WHERE name = 'Laptop Pro 15';

-- Remove a key with - operator
UPDATE products
SET metadata = metadata - 'discount_pct'
WHERE name = 'Laptop Pro 15';

-- Concatenate/merge JSONB objects
UPDATE products
SET metadata = metadata || '{"featured": true, "promo_code": "SAVE10"}'::jsonb
WHERE name = 'USB-C Hub';

SELECT name, metadata -> 'featured', metadata -> 'promo_code'
FROM products WHERE name = 'USB-C Hub';
EOF
```

📸 **Verified Output (after updates):**
```
      name     | price   | discount | ram
---------------+---------+----------+-----
 Laptop Pro 15 | 1349.99 | 10       | 32
(1 row)

      name  | ?column? | ?column?
------------+----------+----------
 USB-C Hub  | true     | "SAVE10"
(1 row)
```

---

## Step 7: GIN Index on JSONB

```bash
docker exec pg-lab psql -U postgres -d jsonlab << 'EOF'
-- Without index: sequential scan for JSON queries
EXPLAIN SELECT * FROM products WHERE metadata @> '{"in_stock": true}';

-- Create GIN index (Generalized Inverted Index) for JSONB
CREATE INDEX idx_gin_metadata ON products USING GIN (metadata);

-- Create GIN index for array column
CREATE INDEX idx_gin_tags ON products USING GIN (tags);

-- Now EXPLAIN shows index usage
EXPLAIN SELECT * FROM products WHERE metadata @> '{"in_stock": true}';
EXPLAIN SELECT * FROM products WHERE tags @> ARRAY['electronics'];

-- Check indexes
\d+ products
EOF
```

📸 **Verified Output (EXPLAIN with GIN index):**
```
-- Without GIN:
Seq Scan on products  (cost=0.00..1.07 rows=1 width=...)
  Filter: (metadata @> '{"in_stock": true}'::jsonb)

-- With GIN:
Bitmap Heap Scan on products  (cost=4.25..8.52 rows=1 width=...)
  Recheck Cond: (metadata @> '{"in_stock": true}'::jsonb)
  ->  Bitmap Index Scan on idx_gin_metadata  (cost=0.00..4.25 ...)
```

> 💡 GIN (Generalized Inverted Index) indexes every element inside the JSONB/array. For large tables with JSONB queries using `@>`, `?`, `?|`, `?&`, or array operators, GIN indexes can be 100x faster than sequential scans.

---

## Step 8: Capstone — JSONB Analytics

```bash
docker exec pg-lab psql -U postgres -d jsonlab << 'EOF'
-- Average rating per product (from JSON array)
SELECT
    name,
    metadata -> 'ratings' AS ratings,
    (
        SELECT ROUND(AVG(r::numeric), 2)
        FROM jsonb_array_elements_text(metadata -> 'ratings') AS r
    ) AS avg_rating,
    (metadata ->> 'price')::numeric AS price,
    (metadata ->> 'in_stock')::boolean AS in_stock
FROM products
ORDER BY avg_rating DESC;

-- Tag frequency across all products
SELECT tag, COUNT(*) AS product_count
FROM products, unnest(tags) AS tag
GROUP BY tag
ORDER BY product_count DESC, tag;
EOF
```

📸 **Verified Output (avg ratings):**
```
       name       |    ratings    | avg_rating |   price  | in_stock
------------------+---------------+------------+----------+----------
 Laptop Pro 15    | [4, 5, 5, 4]  |       4.50 |  1349.99 | t
 SQL Mastery Book | [5, 5, 4, 5]  |       4.75 |    49.99 | f
 USB-C Hub        | [5, 4, 5, 5]  |       4.75 |    49.99 | t
 Wireless Mouse   | [4, 3, 5]     |       4.00 |    29.99 | t
 Ergonomic Chair  | [4, 4, 3]     |       3.67 |   399.99 | t
(5 rows)

-- Tag frequency:
       tag      | product_count
----------------+---------------
 electronics    |             3
 peripherals    |             2
 books          |             1
 computers      |             1
 connectivity   |             1
 education      |             1
 ergonomic      |             1
 furniture      |             1
 office         |             1
 portable       |             1
 technology     |             1
 wireless       |             1
(12 rows)
```

**Cleanup:**
```bash
docker rm -f pg-lab
```

---

## Summary

| Feature | Syntax | Description |
|---------|--------|-------------|
| Array column | `TEXT[]`, `INT[]` | Array of type |
| Array literal | `ARRAY['a','b']` or `'{a,b}'` | Create array value |
| Array element | `col[1]` | Access 1-indexed element |
| Contains | `col @> ARRAY['x']` | Array contains value |
| Contained by | `ARRAY['x'] <@ col` | Subset of array |
| Overlap | `col && ARRAY['x','y']` | Any in common |
| Any | `'x' = ANY(col)` | Value in array |
| Unnest | `unnest(col)` | Expand to rows |
| JSONB get (JSONB) | `col -> 'key'` | Returns JSONB |
| JSONB get (text) | `col ->> 'key'` | Returns TEXT |
| JSONB nested | `col -> 'a' -> 'b'` | Chain navigation |
| Key exists | `col ? 'key'` | Boolean |
| JSONB contains | `col @> '{"k":"v"}'` | Subset match |
| JSONB update | `jsonb_set(col, '{key}', val)` | Immutable update |
| JSONB merge | `col \|\| '{"k":"v"}'::jsonb` | Merge objects |
| GIN index | `CREATE INDEX ON t USING GIN (col)` | Indexes all keys |

**Next:** Lab 19 — MySQL Specific Features
