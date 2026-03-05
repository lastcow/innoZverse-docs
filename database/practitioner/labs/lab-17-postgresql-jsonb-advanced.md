# Lab 17: PostgreSQL JSONB — Advanced

**Time:** 40 minutes | **Level:** Practitioner | **DB:** PostgreSQL 15

PostgreSQL's `JSONB` stores JSON in a binary, indexed form. It enables rich document queries inside a relational database — with the full power of SQL, transactions, and joins.

---

## Step 1 — JSON vs JSONB

```sql
-- JSON: stores exact text (preserves whitespace, duplicate keys)
-- JSONB: binary format, deduplicates keys, supports indexing

CREATE TABLE comparison (
  id       SERIAL PRIMARY KEY,
  raw_json JSON,
  bin_json JSONB
);

INSERT INTO comparison (raw_json, bin_json) VALUES (
  '{"name": "Alice", "age": 28, "name": "Alice Updated"}',  -- duplicate key
  '{"name": "Alice", "age": 28, "name": "Alice Updated"}'
);

-- JSON preserves duplicate keys and whitespace
SELECT raw_json FROM comparison;
-- {"name": "Alice", "age": 28, "name": "Alice Updated"}

-- JSONB deduplicates (last value wins) and normalizes
SELECT bin_json FROM comparison;
-- {"age": 28, "name": "Alice Updated"}
```

> 💡 Use `JSONB` for almost everything — it supports indexing and is faster to query. Use `JSON` only when you need to preserve exact text representation (e.g., audit logs).

---

## Step 2 — Setup: User Profiles with JSONB

```sql
CREATE TABLE user_profiles (
  id       SERIAL PRIMARY KEY,
  username VARCHAR(50),
  profile  JSONB
);

INSERT INTO user_profiles (username, profile) VALUES
  ('alice', '{
    "name": "Alice Smith",
    "age": 28,
    "email": "alice@example.com",
    "skills": ["Python", "SQL", "Docker"],
    "address": {"city": "New York", "country": "US"},
    "score": 95.5,
    "active": true
  }'),
  ('bob', '{
    "name": "Bob Jones",
    "age": 35,
    "email": "bob@example.com",
    "skills": ["Java", "Kubernetes", "SQL"],
    "address": {"city": "London", "country": "UK"},
    "score": 87.2,
    "active": true
  }'),
  ('carol', '{
    "name": "Carol Lee",
    "age": 24,
    "email": "carol@example.com",
    "skills": ["Python", "React", "PostgreSQL"],
    "address": {"city": "San Francisco", "country": "US"},
    "score": 91.8,
    "active": false
  }');
```

---

## Step 3 — Navigation Operators: -> and ->>

```sql
-- -> returns JSONB (preserves type)
-- ->> returns TEXT (always text)

SELECT username,
  profile -> 'name'             AS name_json,   -- JSONB: "Alice Smith"
  profile ->> 'name'            AS name_text,   -- TEXT:  Alice Smith
  profile -> 'age'              AS age_json,    -- JSONB: 28
  (profile ->> 'age')::INT      AS age_int,     -- INT:   28
  profile -> 'address' -> 'city' AS city_json,  -- nested JSONB
  profile -> 'address' ->> 'city' AS city_text  -- nested TEXT
FROM user_profiles;
```

📸 **Verified Output:**
```
 username |    name_json    |    name_text    | age_json | age_int |  city_json   |  city_text
----------+-----------------+-----------------+----------+---------+--------------+-------------
 alice    | "Alice Smith"   | Alice Smith     | 28       |      28 | "New York"   | New York
 bob      | "Bob Jones"     | Bob Jones       | 35       |      35 | "London"     | London
 carol    | "Carol Lee"     | Carol Lee       | 24       |      24 | "San Francisco" | San Francisco
(3 rows)
```

```sql
-- #> and #>> for path navigation
SELECT username,
  profile #> '{address,city}'   AS city_json,
  profile #>> '{address,city}'  AS city_text,
  profile #>> '{skills,0}'      AS first_skill  -- array index
FROM user_profiles;
```

---

## Step 4 — Containment and Existence Operators

```sql
-- @>: left contains right (containment)
SELECT username FROM user_profiles
WHERE profile @> '{"skills": ["Python"]}';
-- alice, carol (have Python in skills array)

-- <@: right contains left
SELECT username FROM user_profiles
WHERE '{"age": 28}' <@ profile;
-- alice

-- ?: key exists at top level
SELECT username FROM user_profiles
WHERE profile ? 'email';
-- alice, bob, carol (all have email field)

-- ?|: any of the keys exist
SELECT username FROM user_profiles
WHERE profile ?| ARRAY['phone', 'email'];
-- alice, bob, carol

-- ?&: all keys must exist
SELECT username FROM user_profiles
WHERE profile ?& ARRAY['email', 'skills'];
-- alice, bob, carol (all have both)
```

📸 **Verified Output (@> Python):**
```
 username
----------
 alice
 carol
(2 rows)
```

---

## Step 5 — Modifying JSONB: jsonb_set, jsonb_insert

```sql
-- jsonb_set(target, path, new_value, create_missing)
UPDATE user_profiles
SET profile = jsonb_set(profile, '{score}', '99.0')
WHERE username = 'alice';

-- Set nested field
UPDATE user_profiles
SET profile = jsonb_set(profile, '{address, zip}', '"10001"', true)
WHERE username = 'alice';

-- jsonb_insert: insert without overwriting
UPDATE user_profiles
SET profile = jsonb_insert(profile, '{skills, 0}', '"PostgreSQL"')
WHERE username = 'alice';
-- Inserts "PostgreSQL" at position 0 in skills array

-- Remove a field: use - operator
UPDATE user_profiles
SET profile = profile - 'active'  -- remove 'active' key
WHERE username = 'carol';

-- Remove nested: use #- path operator
UPDATE user_profiles
SET profile = profile #- '{address, zip}'
WHERE username = 'alice';

-- Concatenate / merge JSONB
UPDATE user_profiles
SET profile = profile || '{"verified": true, "tier": "premium"}'
WHERE username = 'bob';

SELECT username, profile FROM user_profiles WHERE username = 'bob';
```

---

## Step 6 — GIN Index and Query Performance

```sql
-- Without index: Seq Scan
EXPLAIN (FORMAT TEXT)
SELECT * FROM user_profiles WHERE profile @> '{"skills": ["SQL"]}';
-- Seq Scan on user_profiles

-- Create GIN index
CREATE INDEX idx_profile_gin ON user_profiles USING GIN(profile);

-- With GIN index (small table, force with seqscan off)
SET enable_seqscan = off;
EXPLAIN (FORMAT TEXT)
SELECT * FROM user_profiles WHERE profile @> '{"skills": ["SQL"]}';
SET enable_seqscan = on;
```

📸 **Verified Output (with GIN):**
```
 Bitmap Heap Scan on user_profiles  (cost=12.00..16.01 rows=1 width=154)
   Recheck Cond: (profile @> '{"skills": ["SQL"]}'::jsonb)
   ->  Bitmap Index Scan on idx_profile_gin  (cost=0.00..12.00 rows=1 width=0)
         Index Cond: (profile @> '{"skills": ["SQL"]}'::jsonb)
(4 rows)
```

```sql
-- Partial index on JSONB field (active users only)
CREATE INDEX idx_active_users ON user_profiles((profile->>'active'))
WHERE (profile->>'active')::BOOLEAN = true;

-- Expression index on a JSONB path
CREATE INDEX idx_user_score ON user_profiles((( profile->>'score')::NUMERIC));

-- Use the expression index
EXPLAIN (ANALYZE)
SELECT username FROM user_profiles
WHERE (profile->>'score')::NUMERIC > 90;
```

---

## Step 7 — jsonb_path_query and JSONB Aggregation

```sql
-- jsonb_path_query: JSONPath expressions (PostgreSQL 12+)
SELECT username,
  jsonb_path_query(profile, '$.skills[*]') AS skill
FROM user_profiles
WHERE jsonb_path_exists(profile, '$.skills[*] ? (@ == "Python")');

-- jsonb_path_query_array: returns as array
SELECT username,
  jsonb_path_query_array(profile, '$.skills[*]') AS all_skills
FROM user_profiles;

-- JSONB aggregation functions
SELECT
  jsonb_agg(profile -> 'name')                    AS all_names,
  jsonb_agg(DISTINCT profile ->> 'address' ->> 'country') AS countries,
  jsonb_object_agg(username, profile -> 'score')  AS score_map
FROM user_profiles;

-- Build JSONB from query results
SELECT json_build_object(
  'total', COUNT(*),
  'avg_score', ROUND(AVG((profile->>'score')::NUMERIC), 2),
  'top_skills', jsonb_agg(DISTINCT skill.value)
) AS summary
FROM user_profiles,
     jsonb_array_elements(profile->'skills') AS skill(value);
```

---

## Step 8 — Capstone: Product Catalog with JSONB Specs

```sql
CREATE TABLE catalog (
  id       SERIAL PRIMARY KEY,
  sku      VARCHAR(50) UNIQUE,
  name     TEXT,
  category TEXT,
  price    NUMERIC(10,2),
  specs    JSONB,
  tags     TEXT[],
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_catalog_specs ON catalog USING GIN(specs);
CREATE INDEX idx_catalog_tags  ON catalog USING GIN(tags);

INSERT INTO catalog (sku, name, category, price, specs, tags) VALUES
  ('ELEC-001', 'Laptop Pro 16',    'Electronics', 1299.99,
   '{"ram":"16GB","storage":"512GB SSD","cpu":"M3","os":"macOS","weight":"1.4kg","ports":["USB-C","HDMI","SD"]}',
   ARRAY['laptop','portable','premium']),
  ('ELEC-002', 'Gaming Monitor',   'Electronics',  449.99,
   '{"size":"27in","resolution":"2560x1440","refresh_rate":165,"hdr":true,"panel":"IPS"}',
   ARRAY['monitor','gaming','display']),
  ('BOOK-001', 'PostgreSQL Guide', 'Books',          49.99,
   '{"pages":450,"format":"paperback","edition":3,"isbn":"978-1234567890"}',
   ARRAY['programming','database','learning']);

-- Query: Find all products with HDR support
SELECT sku, name, price
FROM catalog
WHERE specs @> '{"hdr": true}';

-- Query: Find by spec value range using jsonb_path_query
SELECT sku, name, specs->>'refresh_rate' AS hz
FROM catalog
WHERE (specs->>'refresh_rate')::INT >= 120;

-- Aggregate: count by top-level spec keys
SELECT key, COUNT(*) AS products_with_key
FROM catalog, jsonb_object_keys(specs) AS key
GROUP BY key
ORDER BY products_with_key DESC;

-- Update: add a spec field
UPDATE catalog
SET specs = jsonb_set(specs, '{warranty_years}', '2')
WHERE category = 'Electronics';

SELECT sku, specs->>'warranty_years' AS warranty
FROM catalog
WHERE category = 'Electronics';
```

---

## Summary

| Operator | Input | Output | Use |
|----------|-------|--------|-----|
| `->` | key/index | JSONB | Navigate, preserves type |
| `->>` | key/index | TEXT | Extract as text |
| `#>` | path array | JSONB | Deep navigation |
| `#>>` | path array | TEXT | Deep extract as text |
| `@>` | JSONB | boolean | Containment (GIN indexable) |
| `<@` | JSONB | boolean | Is contained by |
| `?` | key | boolean | Key exists |
| `?|` | key array | boolean | Any key exists |
| `?&` | key array | boolean | All keys exist |
| `\|\|` | JSONB | JSONB | Merge/concatenate |
| `-` | key | JSONB | Remove key |
| `#-` | path | JSONB | Remove by path |
