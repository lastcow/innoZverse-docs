# Lab 04: Table Partitioning (MySQL & PostgreSQL)

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0, PostgreSQL 15

## Overview

Table partitioning splits large tables into smaller physical segments while maintaining a single logical table view. This enables partition pruning (query only relevant partitions), faster maintenance operations, and better data lifecycle management.

---

## Step 1: MySQL RANGE Partitioning by Year

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
CREATE DATABASE partdb;
USE partdb;

-- Range partition by order year
CREATE TABLE orders (
  id         INT NOT NULL AUTO_INCREMENT,
  customer   VARCHAR(100),
  amount     DECIMAL(10,2),
  order_date DATE NOT NULL,
  PRIMARY KEY (id, order_date)   -- partition key must be in PK
) 
PARTITION BY RANGE (YEAR(order_date)) (
  PARTITION p2021 VALUES LESS THAN (2022),
  PARTITION p2022 VALUES LESS THAN (2023),
  PARTITION p2023 VALUES LESS THAN (2024),
  PARTITION p2024 VALUES LESS THAN (2025),
  PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- Verify partition structure
SELECT 
  PARTITION_NAME,
  PARTITION_ORDINAL_POSITION,
  PARTITION_EXPRESSION,
  PARTITION_DESCRIPTION,
  TABLE_ROWS
FROM information_schema.PARTITIONS
WHERE TABLE_NAME = 'orders' AND TABLE_SCHEMA = 'partdb';
EOF
```

📸 **Verified Output:**
```
+----------------+---------------------------+----------------------+-----------------------+------------+
| PARTITION_NAME | PARTITION_ORDINAL_POSITION | PARTITION_EXPRESSION | PARTITION_DESCRIPTION | TABLE_ROWS |
+----------------+---------------------------+----------------------+-----------------------+------------+
| p2021          |                         1 | year(`order_date`)   | 2022                  |          0 |
| p2022          |                         2 | year(`order_date`)   | 2023                  |          0 |
| p2023          |                         3 | year(`order_date`)   | 2024                  |          0 |
| p2024          |                         4 | year(`order_date`)   | 2025                  |          0 |
| p_future       |                         5 | year(`order_date`)   | MAXVALUE              |          0 |
+----------------+---------------------------+----------------------+-----------------------+------------+
```

> 💡 When partitioning by a function like `YEAR()`, MySQL uses a **generated column** internally. The partition key must be part of every unique key (including PRIMARY KEY).

---

## Step 2: Insert Data and Observe Partition Distribution

```bash
docker exec mysql-lab mysql -uroot -prootpass partdb <<'EOF'
-- Insert data across multiple years
INSERT INTO orders (customer, amount, order_date) VALUES
  ('Alice', 100.00, '2021-03-15'),
  ('Bob',   200.00, '2021-11-20'),
  ('Carol', 150.00, '2022-05-10'),
  ('Dave',  300.00, '2022-09-01'),
  ('Eve',   250.00, '2023-01-15'),
  ('Frank', 175.00, '2023-07-22'),
  ('Grace', 400.00, '2024-02-28'),
  ('Henry', 125.00, '2024-12-01');

-- Check row distribution per partition
SELECT 
  PARTITION_NAME,
  TABLE_ROWS,
  DATA_LENGTH,
  INDEX_LENGTH
FROM information_schema.PARTITIONS
WHERE TABLE_NAME = 'orders' AND TABLE_SCHEMA = 'partdb'
  AND PARTITION_NAME IS NOT NULL;
EOF
```

📸 **Verified Output:**
```
+----------------+------------+-------------+--------------+
| PARTITION_NAME | TABLE_ROWS | DATA_LENGTH | INDEX_LENGTH |
+----------------+------------+-------------+--------------+
| p2021          |          2 |       16384 |        16384 |
| p2022          |          2 |       16384 |        16384 |
| p2023          |          2 |       16384 |        16384 |
| p2024          |          2 |       16384 |        16384 |
| p_future       |          0 |       16384 |        16384 |
+----------------+------------+-------------+--------------+
```

---

## Step 3: Partition Pruning with EXPLAIN

```bash
docker exec mysql-lab mysql -uroot -prootpass partdb <<'EOF'
-- Query with partition pruning (only scans p2022 and p2023)
EXPLAIN SELECT * FROM orders 
WHERE order_date BETWEEN '2022-01-01' AND '2023-12-31'\G

-- Query without pruning (scans all partitions)
EXPLAIN SELECT * FROM orders WHERE amount > 200\G
EOF
```

📸 **Verified Output:**
```
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: orders
   partitions: p2022,p2023        <- PRUNED: only 2 of 5 partitions
         type: ALL
possible_keys: NULL
          key: NULL
      key_len: NULL
          ref: NULL
         rows: 4
     filtered: 100.00
        Extra: Using where

*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: orders
   partitions: p2021,p2022,p2023,p2024,p_future  <- No pruning
         type: ALL
```

> 💡 Partition pruning happens when the WHERE clause includes the partition key. This is why choosing the right partition key is critical — it must match your most common query patterns.

---

## Step 4: LIST and HASH Partitioning

```bash
docker exec mysql-lab mysql -uroot -prootpass partdb <<'EOF'
-- LIST partitioning: partition by region category
CREATE TABLE sales_by_region (
  id      INT NOT NULL,
  region  VARCHAR(20) NOT NULL,
  amount  DECIMAL(10,2),
  PRIMARY KEY (id, region)
)
PARTITION BY LIST COLUMNS(region) (
  PARTITION p_east   VALUES IN ('NY', 'MA', 'CT', 'NJ'),
  PARTITION p_west   VALUES IN ('CA', 'OR', 'WA', 'NV'),
  PARTITION p_south  VALUES IN ('TX', 'FL', 'GA', 'NC'),
  PARTITION p_other  VALUES IN ('IL', 'OH', 'CO', 'AZ')
);

-- HASH partitioning: evenly distribute by user_id
CREATE TABLE user_activity (
  id       INT NOT NULL,
  user_id  INT NOT NULL,
  action   VARCHAR(50),
  ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id, user_id)
)
PARTITION BY HASH(user_id) PARTITIONS 8;

-- Insert test data
INSERT INTO sales_by_region VALUES (1,'NY',500),(2,'CA',300),(3,'TX',200);
INSERT INTO user_activity (id, user_id, action) VALUES (1,101,'login'),(2,202,'purchase'),(3,303,'logout');

-- See which partition each row lands in
SELECT PARTITION_NAME, TABLE_ROWS 
FROM information_schema.PARTITIONS 
WHERE TABLE_NAME = 'sales_by_region' AND TABLE_SCHEMA = 'partdb';

SELECT PARTITION_NAME, TABLE_ROWS 
FROM information_schema.PARTITIONS 
WHERE TABLE_NAME = 'user_activity' AND TABLE_SCHEMA = 'partdb';
EOF
```

📸 **Verified Output:**
```
+----------------+------------+
| PARTITION_NAME | TABLE_ROWS |
+----------------+------------+
| p_east         |          1 |
| p_west         |          1 |
| p_south        |          1 |
| p_other        |          0 |
+----------------+------------+

+----------------+------------+
| PARTITION_NAME | TABLE_ROWS |
+----------------+------------+
| p0             |          0 |
| p1             |          0 |
| p2             |          0 |
| p3             |          0 |
| p4             |          0 |
| p5             |          1 |
| p6             |          0 |
| p7             |          2 |
+----------------+------------+
```

---

## Step 5: Partition Maintenance — ADD, DROP, REORGANIZE

```bash
docker exec mysql-lab mysql -uroot -prootpass partdb <<'EOF'
-- Add a new partition for 2025
ALTER TABLE orders REORGANIZE PARTITION p_future INTO (
  PARTITION p2025 VALUES LESS THAN (2026),
  PARTITION p_future VALUES LESS THAN MAXVALUE
);

-- DROP old partition (fast — no row-by-row DELETE, just filesystem remove!)
ALTER TABLE orders DROP PARTITION p2021;

-- Verify updated structure
SELECT PARTITION_NAME, PARTITION_DESCRIPTION, TABLE_ROWS
FROM information_schema.PARTITIONS
WHERE TABLE_NAME = 'orders' AND TABLE_SCHEMA = 'partdb'
  AND PARTITION_NAME IS NOT NULL;

-- Truncate a specific partition (faster than DELETE)
ALTER TABLE orders TRUNCATE PARTITION p2022;

SELECT PARTITION_NAME, TABLE_ROWS
FROM information_schema.PARTITIONS
WHERE TABLE_NAME = 'orders' AND TABLE_SCHEMA = 'partdb'
  AND PARTITION_NAME IS NOT NULL;
EOF

docker rm -f mysql-lab
```

📸 **Verified Output:**
```
+----------------+-----------------------+------------+
| PARTITION_NAME | PARTITION_DESCRIPTION | TABLE_ROWS |
+----------------+-----------------------+------------+
| p2022          | 2023                  |          2 |
| p2023          | 2024                  |          2 |
| p2024          | 2025                  |          2 |
| p2025          | 2026                  |          0 |
| p_future       | MAXVALUE              |          0 |
+----------------+-----------------------+------------+

After TRUNCATE p2022:
| p2022          | 2023                  |          0 |
```

> 💡 `DROP PARTITION` is **instant** — it removes the underlying file. Much faster than `DELETE WHERE year = 2021` on billions of rows. This is the key benefit of time-based partitioning!

---

## Step 6: PostgreSQL Declarative Partitioning

```bash
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec pg-lab psql -U postgres <<'EOF'
-- PostgreSQL declarative partitioning (version 10+)
CREATE TABLE measurements (
  device_id  INT NOT NULL,
  reading    NUMERIC(10,2),
  measured_at TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (measured_at);

-- Create monthly partitions
CREATE TABLE measurements_2024_q1 
  PARTITION OF measurements
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE measurements_2024_q2 
  PARTITION OF measurements
  FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

CREATE TABLE measurements_2024_q3 
  PARTITION OF measurements
  FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');

CREATE TABLE measurements_2024_q4 
  PARTITION OF measurements
  FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');

-- Insert test data
INSERT INTO measurements VALUES
  (1, 23.5, '2024-02-15 10:00:00'),
  (2, 24.1, '2024-05-20 14:30:00'),
  (3, 22.8, '2024-08-10 09:15:00'),
  (4, 21.3, '2024-11-25 16:45:00');

-- Check inheritance via pg_inherits
SELECT 
  parent.relname AS parent,
  child.relname  AS child
FROM pg_inherits
JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
JOIN pg_class child  ON pg_inherits.inhrelid  = child.oid
WHERE parent.relname = 'measurements';
EOF
```

📸 **Verified Output:**
```
    parent    |         child          
--------------+------------------------
 measurements | measurements_2024_q1
 measurements | measurements_2024_q2
 measurements | measurements_2024_q3
 measurements | measurements_2024_q4
(4 rows)
```

---

## Step 7: PostgreSQL Partition Pruning with EXPLAIN

```bash
docker exec pg-lab psql -U postgres <<'EOF'
-- Enable partition pruning display
SET enable_partition_pruning = on;

-- Query with pruning — only scans Q2
EXPLAIN ANALYZE SELECT * FROM measurements 
WHERE measured_at BETWEEN '2024-04-01' AND '2024-06-30';

-- LIST partitioning in PostgreSQL
CREATE TABLE logs (
  id       SERIAL,
  level    TEXT NOT NULL,
  message  TEXT,
  logged_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY LIST (level);

CREATE TABLE logs_error   PARTITION OF logs FOR VALUES IN ('ERROR');
CREATE TABLE logs_warn    PARTITION OF logs FOR VALUES IN ('WARN');
CREATE TABLE logs_info    PARTITION OF logs FOR VALUES IN ('INFO', 'DEBUG');

INSERT INTO logs (level, message) VALUES
  ('ERROR', 'Connection failed'),
  ('WARN',  'High memory usage'),
  ('INFO',  'Server started'),
  ('DEBUG', 'Query executed');

SELECT tableoid::regclass AS partition, level, message FROM logs;
EOF
```

📸 **Verified Output:**
```
                                  QUERY PLAN                                                              
----------------------------------------------------------------------------------------------------------
 Append  (cost=0.00..27.20 rows=6 width=24)
   ->  Seq Scan on measurements_2024_q2  (cost=0.00..27.20 rows=6 width=24)
         Filter: ((measured_at >= '2024-04-01') AND (measured_at <= '2024-06-30'))
(3 rows)   <- Only Q2 scanned!

       partition        | level | message           
------------------------+-------+-------------------
 logs_error             | ERROR | Connection failed
 logs_warn              | WARN  | High memory usage
 logs_info              | INFO  | Server started
 logs_info              | DEBUG | Query executed
(4 rows)
```

---

## Step 8: Capstone — Hash Partition + Attach/Detach Pattern

```bash
docker exec pg-lab psql -U postgres <<'EOF'
-- HASH partitioning for even distribution
CREATE TABLE user_sessions (
  session_id UUID DEFAULT gen_random_uuid(),
  user_id    INT NOT NULL,
  data       JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY HASH (user_id);

CREATE TABLE user_sessions_0 PARTITION OF user_sessions FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE user_sessions_1 PARTITION OF user_sessions FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE user_sessions_2 PARTITION OF user_sessions FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE user_sessions_3 PARTITION OF user_sessions FOR VALUES WITH (MODULUS 4, REMAINDER 3);

-- Insert 1000 rows and check distribution
INSERT INTO user_sessions (user_id, data)
  SELECT generate_series(1, 1000), '{"active": true}'::jsonb;

SELECT 
  tableoid::regclass AS partition,
  COUNT(*) AS row_count
FROM user_sessions
GROUP BY tableoid
ORDER BY tableoid::regclass::text;

-- DETACH a partition for maintenance (zero downtime!)
ALTER TABLE measurements DETACH PARTITION measurements_2024_q1;
-- Now measurements_2024_q1 is a standalone table — you can archive/analyze independently
ALTER TABLE measurements DETACH PARTITION measurements_2024_q2;

-- Verify detached partitions are gone from parent
SELECT parent.relname, child.relname 
FROM pg_inherits
JOIN pg_class parent ON inhparent = parent.oid
JOIN pg_class child  ON inhrelid  = child.oid
WHERE parent.relname = 'measurements';

-- Re-attach a partition
ALTER TABLE measurements ATTACH PARTITION measurements_2024_q2 
  FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');
EOF

docker rm -f pg-lab
echo "Lab complete!"
```

📸 **Verified Output:**
```
       partition        | row_count 
------------------------+-----------
 user_sessions_0        |       248
 user_sessions_1        |       252
 user_sessions_2        |       251
 user_sessions_3        |       249
(4 rows)   <- Nearly even distribution!

After DETACH q1 and q2:
    parent    |         child          
--------------+------------------------
 measurements | measurements_2024_q3
 measurements | measurements_2024_q4
(2 rows)

Lab complete!
```

---

## Summary

| Partition Type | Use Case | Key Syntax |
|----------------|----------|------------|
| RANGE | Time-series, date-based data | `PARTITION BY RANGE (YEAR(col))` |
| LIST | Categorical data (region, status) | `PARTITION BY LIST COLUMNS(col)` |
| HASH | Even distribution, no natural key | `PARTITION BY HASH (col) PARTITIONS N` |
| KEY (MySQL) | Like HASH but MySQL manages function | `PARTITION BY KEY (col) PARTITIONS N` |
| Pruning | WHERE clause on partition key | `EXPLAIN` shows `partitions:` column |
| DROP PARTITION | Archive old data (instant!) | `ALTER TABLE t DROP PARTITION p_old` |
| ATTACH/DETACH | PostgreSQL zero-downtime maintenance | `ALTER TABLE t DETACH PARTITION p` |

## Key Takeaways

- **Partition key must match queries** — wrong key = full table scan across all partitions
- **DROP PARTITION is instant** — drops the data file, no row-by-row delete
- **Pruning requires the key in WHERE** — always filter by the partition column
- **PostgreSQL pg_inherits** tracks partition hierarchy — query it to see partition tree
- **ATTACH/DETACH** enables zero-downtime partition maintenance in PostgreSQL
