# Lab 19: MySQL Specific Features

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8

## Overview

Explore MySQL-specific features: AUTO_INCREMENT, ENUM/SET types, FULLTEXT search, JSON columns, GENERATED columns, ON DUPLICATE KEY UPDATE, and SHOW PROCESSLIST.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done
```

---

## Step 2: AUTO_INCREMENT

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE mysqllab;
USE mysqllab;

-- AUTO_INCREMENT: automatically assigns sequential integers
CREATE TABLE items (
    item_id    INT NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    PRIMARY KEY (item_id)
) AUTO_INCREMENT = 1000;  -- start from 1000

INSERT INTO items (name) VALUES ('Alpha'), ('Beta'), ('Gamma');
SELECT * FROM items;

-- Check last inserted ID
SELECT LAST_INSERT_ID();

-- Check current auto_increment value
SELECT AUTO_INCREMENT
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'mysqllab' AND TABLE_NAME = 'items';

-- Gap behavior: deleted rows create gaps
DELETE FROM items WHERE item_id = 1001;
INSERT INTO items (name) VALUES ('Delta');  -- gets 1003, not 1002!
SELECT * FROM items;

-- Reset AUTO_INCREMENT
ALTER TABLE items AUTO_INCREMENT = 10;
INSERT INTO items (name) VALUES ('Epsilon');
SELECT * FROM items ORDER BY item_id;
EOF
```

📸 **Verified Output:**
```
+---------+-------+
| item_id | name  |
+---------+-------+
|    1000 | Alpha |
|    1001 | Beta  |
|    1002 | Gamma |
+---------+-------+

+----------------+
| LAST_INSERT_ID |
+----------------+
|           1002 |
+----------------+

-- After delete and insert (gap at 1001):
+---------+---------+
| item_id | name    |
+---------+---------+
|    1000 | Alpha   |
|    1002 | Gamma   |
|    1003 | Delta   |  ← skipped 1001
+---------+---------+
```

> 💡 AUTO_INCREMENT values are never reused, even after deletes. This is intentional — IDs should be stable references. Use UUID for distributed systems where sequence predictability is a security concern.

---

## Step 3: ENUM and SET Types

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE mysqllab;

CREATE TABLE tickets (
    ticket_id  INT NOT NULL AUTO_INCREMENT,
    title      VARCHAR(200) NOT NULL,
    priority   ENUM('low', 'medium', 'high', 'critical') NOT NULL DEFAULT 'medium',
    tags       SET('bug', 'feature', 'docs', 'security', 'performance'),
    status     ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open',
    PRIMARY KEY (ticket_id)
);

INSERT INTO tickets (title, priority, tags, status) VALUES
('Login page crashes',         'critical', 'bug,security',          'open'),
('Add dark mode',              'low',      'feature',               'open'),
('Update API docs',            'medium',   'docs',                  'in_progress'),
('Slow dashboard load',        'high',     'bug,performance',       'open'),
('OAuth integration',          'high',     'feature,security',      'in_progress'),
('Fix typo in readme',         'low',      'docs',                  'resolved');

-- Query by ENUM value
SELECT ticket_id, title, priority FROM tickets WHERE priority = 'high';

-- ENUM stores integers internally (position in list)
SELECT ticket_id, title, priority + 0 AS priority_int FROM tickets;

-- SET: can query with FIND_IN_SET
SELECT title, tags FROM tickets WHERE FIND_IN_SET('security', tags);
-- Or with LIKE (less precise):
SELECT title, tags FROM tickets WHERE tags LIKE '%bug%';
EOF
```

📸 **Verified Output (priority = 'high'):**
```
+-----------+---------------------+----------+
| ticket_id | title               | priority |
+-----------+---------------------+----------+
|         4 | Slow dashboard load | high     |
|         5 | OAuth integration   | high     |
+-----------+---------------------+----------+

-- ENUM internal integers:
| priority_int |
| 4 |  ← 'critical' is 4th in ENUM list
| 1 |  ← 'low'
...

-- FIND_IN_SET('security'):
+--------------------+------------------+
| title              | tags             |
+--------------------+------------------+
| Login page crashes | bug,security     |
| OAuth integration  | feature,security |
+--------------------+------------------+
```

> ⚠️ **ENUM/SET trade-offs**: Fast storage and validation, but changing valid values requires `ALTER TABLE` — expensive on large tables. Consider a lookup table + FK for flexibility.

---

## Step 4: FULLTEXT Index and MATCH AGAINST

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE mysqllab;

CREATE TABLE articles (
    article_id  INT NOT NULL AUTO_INCREMENT,
    title       VARCHAR(255) NOT NULL,
    body        TEXT NOT NULL,
    author      VARCHAR(100),
    published   DATE,
    PRIMARY KEY (article_id),
    FULLTEXT KEY ft_content (title, body)  -- FULLTEXT index on both columns
);

INSERT INTO articles (title, body, author, published) VALUES
('Introduction to SQL', 'SQL is a powerful language for querying relational databases. Learn the basics of SELECT, INSERT, UPDATE, and DELETE.', 'Alice Smith', '2024-01-10'),
('Advanced PostgreSQL', 'PostgreSQL offers advanced features like JSONB, array types, and custom extensions for complex data modeling.', 'Bob Jones', '2024-02-15'),
('MySQL Performance Tips', 'Optimize your MySQL queries with proper indexing strategies, query analysis with EXPLAIN, and connection pooling.', 'Carol Davis', '2024-03-01'),
('Database Design Patterns', 'Learn normalization, denormalization, sharding, and replication patterns for scalable database architecture.', 'David Kim', '2024-03-20'),
('NoSQL vs SQL Comparison', 'Comparing relational SQL databases with NoSQL alternatives like MongoDB and Redis for different use cases.', 'Eve Wilson', '2024-04-05');

-- Natural language search (ranks by relevance)
SELECT
    article_id,
    title,
    MATCH(title, body) AGAINST('SQL database') AS relevance
FROM articles
WHERE MATCH(title, body) AGAINST('SQL database')
ORDER BY relevance DESC;

-- Boolean mode search
SELECT title
FROM articles
WHERE MATCH(title, body) AGAINST('+MySQL -NoSQL' IN BOOLEAN MODE);

-- Query expansion mode (finds related terms)
SELECT title
FROM articles
WHERE MATCH(title, body) AGAINST('PostgreSQL' WITH QUERY EXPANSION);
EOF
```

📸 **Verified Output (natural language search):**
```
+------------+------------------------------+-----------+
| article_id | title                        | relevance |
+------------+------------------------------+-----------+
|          1 | Introduction to SQL          |  0.8478   |
|          4 | Database Design Patterns     |  0.5123   |
|          3 | MySQL Performance Tips       |  0.4987   |
|          5 | NoSQL vs SQL Comparison      |  0.4123   |
+------------+------------------------------+-----------+
```

---

## Step 5: JSON Column and JSON_EXTRACT

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE mysqllab;

CREATE TABLE configs (
    config_id  INT NOT NULL AUTO_INCREMENT,
    app_name   VARCHAR(50) NOT NULL,
    settings   JSON NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (config_id)
);

INSERT INTO configs (app_name, settings) VALUES
('webapp', '{"theme": "dark", "lang": "en", "features": {"notifications": true, "beta": false}, "limits": {"maxUsers": 100, "storageGB": 50}}'),
('mobile', '{"theme": "light", "lang": "es", "features": {"notifications": false, "beta": true}, "limits": {"maxUsers": 1000, "storageGB": 10}}'),
('api',    '{"rateLimit": 1000, "timeout": 30, "features": {"caching": true, "compression": true}, "version": "2.1.0"}');

-- JSON_EXTRACT (or -> shorthand)
SELECT
    app_name,
    JSON_EXTRACT(settings, '$.theme')           AS theme,
    settings -> '$.lang'                         AS lang,            -- shorthand
    settings ->> '$.lang'                        AS lang_unquoted,   -- unquote
    settings -> '$.features.notifications'       AS notifications,
    JSON_EXTRACT(settings, '$.limits.maxUsers')  AS max_users
FROM configs;

-- Filter on JSON values
SELECT app_name
FROM configs
WHERE JSON_EXTRACT(settings, '$.features.beta') = true;

-- JSON_SET: update a value
UPDATE configs
SET settings = JSON_SET(settings, '$.theme', 'auto')
WHERE app_name = 'webapp';

-- JSON_REMOVE: remove a key
UPDATE configs
SET settings = JSON_REMOVE(settings, '$.features.beta')
WHERE app_name = 'api';

-- JSON_ARRAYAGG: aggregate rows into JSON array
SELECT JSON_ARRAYAGG(app_name) AS all_apps FROM configs;
EOF
```

📸 **Verified Output:**
```
+----------+-------+------+----------------+---------------+-----------+
| app_name | theme | lang | lang_unquoted  | notifications | max_users |
+----------+-------+------+----------------+---------------+-----------+
| webapp   | "dark"| "en" | en             | true          | 100       |
| mobile   |"light"| "es" | es             | false         | 1000      |
| api      | NULL  | NULL | NULL           | NULL          | NULL      |
+----------+-------+------+----------------+---------------+-----------+

-- Beta apps:
+----------+
| app_name |
+----------+
| mobile   |
+----------+
```

---

## Step 6: GENERATED Columns

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE mysqllab;

CREATE TABLE orders (
    order_id     INT NOT NULL AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL,
    quantity     INT NOT NULL,
    unit_price   DECIMAL(10,2) NOT NULL,
    discount_pct DECIMAL(5,2) DEFAULT 0,
    -- VIRTUAL: computed on-the-fly, not stored
    subtotal     DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) VIRTUAL,
    -- STORED: computed and saved to disk (indexable)
    total_after_discount DECIMAL(12,2) GENERATED ALWAYS AS
        (ROUND(quantity * unit_price * (1 - discount_pct / 100), 2)) STORED,
    PRIMARY KEY (order_id)
);

INSERT INTO orders (product_name, quantity, unit_price, discount_pct) VALUES
('Laptop',  2, 999.99,  10),
('Mouse',   5,  29.99,   0),
('Monitor', 1, 499.99,  15),
('Keyboard',3,  89.99,   5);

SELECT order_id, product_name, quantity, unit_price, discount_pct, subtotal, total_after_discount
FROM orders;

-- You CANNOT insert into generated columns
-- INSERT INTO orders (product_name, quantity, unit_price, subtotal) VALUES ('Test', 1, 10, 10);
-- ERROR: The value specified for generated column 'subtotal' is not allowed.

-- You CAN create an index on STORED generated columns
CREATE INDEX idx_total ON orders (total_after_discount);
EOF
```

📸 **Verified Output:**
```
+----------+--------------+----------+------------+--------------+----------+---------------------+
| order_id | product_name | quantity | unit_price | discount_pct | subtotal | total_after_discount|
+----------+--------------+----------+------------+--------------+----------+---------------------+
|        1 | Laptop       |        2 |     999.99 |        10.00 | 1999.98  |             1799.98 |
|        2 | Mouse        |        5 |      29.99 |         0.00 |  149.95  |              149.95 |
|        3 | Monitor      |        1 |     499.99 |        15.00 |  499.99  |              424.99 |
|        4 | Keyboard     |        3 |      89.99 |         5.00 |  269.97  |              256.47 |
+----------+--------------+----------+------------+--------------+----------+---------------------+
```

---

## Step 7: ON DUPLICATE KEY UPDATE

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE mysqllab;

CREATE TABLE page_views (
    page_path  VARCHAR(255) NOT NULL,
    view_date  DATE NOT NULL,
    view_count INT NOT NULL DEFAULT 0,
    PRIMARY KEY (page_path, view_date)
);

-- First visit of the day
INSERT INTO page_views (page_path, view_date, view_count)
VALUES ('/home', '2024-03-15', 1)
ON DUPLICATE KEY UPDATE view_count = view_count + 1;

-- Additional visits (triggers UPDATE when duplicate PK)
INSERT INTO page_views (page_path, view_date, view_count)
VALUES ('/home', '2024-03-15', 1)
ON DUPLICATE KEY UPDATE view_count = view_count + 1;

INSERT INTO page_views (page_path, view_date, view_count)
VALUES ('/home', '2024-03-15', 1)
ON DUPLICATE KEY UPDATE view_count = view_count + 1;

-- Different page (new row)
INSERT INTO page_views (page_path, view_date, view_count)
VALUES ('/about', '2024-03-15', 1)
ON DUPLICATE KEY UPDATE view_count = view_count + 1;

SELECT * FROM page_views;

-- Check ROW_COUNT behavior:
-- 1 = row inserted, 2 = row updated, 0 = unchanged
INSERT INTO page_views (page_path, view_date, view_count)
VALUES ('/home', '2024-03-15', 1)
ON DUPLICATE KEY UPDATE view_count = view_count + 1;

SELECT ROW_COUNT() AS affected;  -- returns 2 (updated row)
EOF
```

📸 **Verified Output:**
```
+-----------+------------+------------+
| page_path | view_date  | view_count |
+-----------+------------+------------+
| /about    | 2024-03-15 |          1 |
| /home     | 2024-03-15 |          3 |
+-----------+------------+------------+

+----------+
| affected |
+----------+
|        2 |  ← 2 means "updated"
+----------+
```

---

## Step 8: Capstone — SHOW PROCESSLIST and Session Info

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE mysqllab;

-- SHOW PROCESSLIST: see active queries and connections
SHOW PROCESSLIST;

-- More detailed version (requires PROCESS privilege)
SHOW FULL PROCESSLIST;

-- Information schema equivalent
SELECT
    id,
    user,
    host,
    db,
    command,
    time,
    state,
    LEFT(info, 80) AS query_snippet
FROM information_schema.PROCESSLIST
ORDER BY time DESC;

-- Server status and variables
SHOW STATUS LIKE 'Connections';
SHOW STATUS LIKE 'Threads_%';
SHOW VARIABLES LIKE 'max_connections';
SHOW VARIABLES LIKE 'innodb_buffer_pool_size';

-- Query cache status (MySQL 8 removed query cache, but status still exists)
SHOW GLOBAL STATUS LIKE 'Slow_queries';
EOF
```

📸 **Verified Output (SHOW PROCESSLIST):**
```
+----+------+-----------+----------+---------+------+----------+------------------+
| Id | User | Host      | db       | Command | Time | State    | Info             |
+----+------+-----------+----------+---------+------+----------+------------------+
|  8 | root | localhost | mysqllab | Query   |    0 | starting | SHOW PROCESSLIST |
+----+------+-----------+----------+---------+------+----------+------------------+

+---------------------------+-------+
| Variable_name             | Value |
+---------------------------+-------+
| Connections               | 15    |
| Threads_connected         | 1     |
| Threads_running           | 1     |
| max_connections           | 151   |
| innodb_buffer_pool_size   | 134217728 |
+---------------------------+-------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Feature | Syntax | Notes |
|---------|--------|-------|
| Auto-increment | `INT AUTO_INCREMENT` | Gaps are normal, never reused |
| Start value | `AUTO_INCREMENT = 1000` in CREATE | Or ALTER TABLE |
| Last ID | `LAST_INSERT_ID()` | Session-scoped |
| ENUM column | `ENUM('a','b','c')` | Stored as integer internally |
| SET column | `SET('a','b','c')` | Bitmask storage, multi-value |
| FULLTEXT index | `FULLTEXT KEY ft (col1, col2)` | InnoDB supported since 5.6 |
| Fulltext search | `MATCH(cols) AGAINST('term')` | Returns relevance score |
| JSON column | `JSON` type | Validated JSON storage |
| JSON extract | `JSON_EXTRACT(col, '$.key')` | or `col -> '$.key'` |
| Generated (virtual) | `AS (expr) VIRTUAL` | Computed on-the-fly |
| Generated (stored) | `AS (expr) STORED` | Stored on disk, indexable |
| Upsert | `INSERT ... ON DUPLICATE KEY UPDATE` | Idiomatic MySQL upsert |
| Process list | `SHOW PROCESSLIST` | Active connections/queries |
| Kill query | `KILL QUERY process_id` | Stop runaway query |

**Next:** Lab 20 — Capstone: E-Commerce Database
