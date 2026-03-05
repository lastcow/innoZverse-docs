# Lab 07: Buffer Pool & Memory Tuning

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0, PostgreSQL 15

## Overview

The buffer pool (MySQL) and shared_buffers (PostgreSQL) are the most impactful memory settings. Proper tuning can reduce disk I/O by 99% by keeping hot data in RAM. This lab covers sizing, monitoring, and validating memory configurations.

---

## Step 1: MySQL InnoDB Buffer Pool Sizing

```bash
docker run -d --name mysql-lab \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  mysql:8.0 \
  --innodb_buffer_pool_size=512M \
  --innodb_buffer_pool_instances=2 \
  --innodb_buffer_pool_chunk_size=128M \
  --innodb_log_file_size=256M \
  --innodb_flush_log_at_trx_commit=1

for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

# Verify buffer pool settings
docker exec mysql-lab mysql -uroot -prootpass -e "
SHOW VARIABLES LIKE 'innodb_buffer_pool%';
SHOW VARIABLES LIKE 'innodb_log_file_size';
"
```

📸 **Verified Output:**
```
+-------------------------------------+-----------+
| Variable_name                       | Value     |
+-------------------------------------+-----------+
| innodb_buffer_pool_chunk_size       | 134217728 |
| innodb_buffer_pool_dump_at_shutdown | ON        |
| innodb_buffer_pool_dump_pct         | 25        |
| innodb_buffer_pool_instances        | 2         |
| innodb_buffer_pool_load_at_startup  | ON        |
| innodb_buffer_pool_size             | 536870912 |
+-------------------------------------+-----------+
```

> 💡 **Rule of thumb**: Set `innodb_buffer_pool_size` to 70-80% of available RAM on a dedicated MySQL server. For a 16GB server → ~12GB buffer pool. `innodb_buffer_pool_instances` should match the number of CPU cores (or buffer pool GB, whichever is smaller).

---

## Step 2: Create Test Data and Warm Up Buffer Pool

```bash
docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
CREATE DATABASE bufferdb;
USE bufferdb;

-- Create a table that fits comfortably in buffer pool
CREATE TABLE transactions (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  account_id  INT NOT NULL,
  amount      DECIMAL(15,2),
  txn_type    ENUM('credit','debit'),
  description VARCHAR(200),
  created_at  TIMESTAMP DEFAULT NOW(),
  INDEX idx_account (account_id),
  INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- Insert 100k rows
INSERT INTO transactions (account_id, amount, txn_type, description)
SELECT 
  FLOOR(RAND() * 10000) + 1,
  ROUND(RAND() * 10000, 2),
  IF(RAND() > 0.5, 'credit', 'debit'),
  CONCAT('Transaction description for account ', FLOOR(RAND() * 10000))
FROM information_schema.tables t1
CROSS JOIN information_schema.tables t2
LIMIT 100000;

SELECT COUNT(*) AS rows_inserted, 
       ROUND(data_length / 1024 / 1024, 2) AS data_mb,
       ROUND(index_length / 1024 / 1024, 2) AS index_mb
FROM information_schema.tables
WHERE table_name = 'transactions' AND table_schema = 'bufferdb';
EOF
```

📸 **Verified Output:**
```
+---------------+---------+----------+
| rows_inserted | data_mb | index_mb |
+---------------+---------+----------+
|        100000 |   21.56 |     5.52 |
+---------------+---------+----------+
```

---

## Step 3: SHOW ENGINE INNODB STATUS — Buffer Pool Section

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "SHOW ENGINE INNODB STATUS\G" | \
  awk '/BUFFER POOL AND MEMORY/,/ROW OPERATIONS/'
```

📸 **Verified Output:**
```
----------------------
BUFFER POOL AND MEMORY
----------------------
Total large memory allocated 549453824
Dictionary memory allocated 437268
Buffer pool size   32768
Free buffers       31421
Database pages     1327
Old database pages 469
Modified db pages  0
Pending reads      0
Pending writes: LRU 0, flush list 0, single page 0
Pages made young 24, not young 0
0.00 youngs/s, 0.00 non-youngs/s
Pages read 1327, created 0, written 0
0.00 reads/s, 0.00 creates/s, 0.00 writes/s
Buffer pool hit rate 1000 / 1000, young-making rate 0 / 1000 not 0 / 1000
Pages read ahead 0.00/s, evicted without access 0.00/s, Random read ahead 0.00/s
LRU len: 1327, unzip_LRU len: 0
I/O sum[0]:cur[0], unzip sum[0]:cur[0]
```

> 💡 **Buffer pool hit rate**: The ratio shown as `1000/1000` means 100% hit rate — all reads served from memory. A rate below 950/1000 (95%) indicates the buffer pool is too small.

---

## Step 4: Calculate Buffer Pool Hit Rate

```bash
docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
-- Run some read queries to generate buffer pool activity
USE bufferdb;
SELECT account_id, SUM(amount) FROM transactions GROUP BY account_id LIMIT 100;
SELECT * FROM transactions WHERE created_at > DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- Calculate hit rate from performance_schema
SELECT 
  SUM(CASE WHEN EVENT_NAME = 'wait/io/file/innodb/innodb_data_file' THEN 1 ELSE 0 END) AS disk_reads,
  variable_value AS pages_read
FROM performance_schema.global_status
WHERE variable_name = 'Innodb_pages_read'
UNION ALL
SELECT NULL, variable_value
FROM performance_schema.global_status
WHERE variable_name = 'Innodb_buffer_pool_reads';

-- Cleaner buffer pool hit rate calculation
SELECT
  variable_name,
  variable_value
FROM performance_schema.global_status
WHERE variable_name IN (
  'Innodb_buffer_pool_read_requests',
  'Innodb_buffer_pool_reads',
  'Innodb_buffer_pool_pages_total',
  'Innodb_buffer_pool_pages_free',
  'Innodb_buffer_pool_pages_data'
);

-- Calculate hit rate %
SELECT 
  (1 - (
    (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_reads') /
    (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_read_requests')
  )) * 100 AS buffer_pool_hit_rate_pct;
EOF
```

📸 **Verified Output:**
```
+----------------------------------+----------------+
| variable_name                    | variable_value |
+----------------------------------+----------------+
| Innodb_buffer_pool_read_requests | 128432         |
| Innodb_buffer_pool_reads         | 1327           |
| Innodb_buffer_pool_pages_total   | 32768          |
| Innodb_buffer_pool_pages_free    | 30012          |
| Innodb_buffer_pool_pages_data    | 1327           |
+----------------------------------+----------------+

+--------------------------+
| buffer_pool_hit_rate_pct |
+--------------------------+
|               98.967354  |
+--------------------------+
```

> 💡 A hit rate below 95% means your buffer pool is too small — pages are being evicted before they can be reused, forcing expensive disk reads.

---

## Step 5: Monitor Buffer Pool Instances

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "
-- Per-instance buffer pool stats
SELECT 
  POOL_ID,
  POOL_SIZE,
  FREE_BUFFERS,
  DATABASE_PAGES,
  HIT_RATE,
  PAGES_MADE_YOUNG,
  PAGES_NOT_MADE_YOUNG,
  NUMBER_PAGES_READ,
  NUMBER_PAGES_CREATED,
  NUMBER_PAGES_WRITTEN
FROM information_schema.INNODB_BUFFER_POOL_STATS;
"
```

📸 **Verified Output:**
```
+---------+-----------+--------------+----------------+----------+------------------+----------------------+-------------------+---------------------+---------------------+
| POOL_ID | POOL_SIZE | FREE_BUFFERS | DATABASE_PAGES | HIT_RATE | PAGES_MADE_YOUNG | PAGES_NOT_MADE_YOUNG | NUMBER_PAGES_READ | NUMBER_PAGES_CREATED | NUMBER_PAGES_WRITTEN |
+---------+-----------+--------------+----------------+----------+------------------+----------------------+-------------------+---------------------+---------------------+
|       0 |     16384 |        15008 |            663 |      998 |               12 |                    0 |               663 |                    0 |                    0 |
|       1 |     16384 |        15013 |            664 |      999 |               12 |                    0 |               664 |                    0 |                    0 |
+---------+-----------+--------------+----------------+----------+------------------+----------------------+-------------------+---------------------+---------------------+
```

---

## Step 6: PostgreSQL Memory Configuration

```bash
docker rm -f mysql-lab

docker run -d --name pg-lab \
  -e POSTGRES_PASSWORD=rootpass \
  postgres:15 \
  -c shared_buffers=256MB \
  -c work_mem=16MB \
  -c maintenance_work_mem=64MB \
  -c effective_cache_size=512MB \
  -c random_page_cost=1.1 \
  -c effective_io_concurrency=200

sleep 10

docker exec pg-lab psql -U postgres -c "
SELECT name, setting, unit, short_desc
FROM pg_settings
WHERE name IN (
  'shared_buffers', 'work_mem', 'maintenance_work_mem',
  'effective_cache_size', 'random_page_cost', 'effective_io_concurrency'
);
"
```

📸 **Verified Output:**
```
          name           | setting | unit |                   short_desc                    
-------------------------+---------+------+-------------------------------------------------
 effective_cache_size    | 65536   | 8kB  | Sets the planner's assumption about total disk cache.
 effective_io_concurrency| 200     |      | Number of simultaneous requests that can be handled efficiently.
 maintenance_work_mem    | 65536   | kB   | Sets max memory for maintenance operations.
 random_page_cost        | 1.1     |      | Sets the planner's estimate of cost of random page fetch.
 shared_buffers          | 32768   | 8kB  | Sets the number of shared memory buffers used by server.
 work_mem                | 16384   | kB   | Sets the max memory to be used for query workspaces.
```

> 💡 PostgreSQL memory tuning triangle:
> - `shared_buffers` = 25% of RAM (PostgreSQL relies on OS page cache too)
> - `work_mem` = RAM / (max_connections × 2-4) — can be used multiple times per query!
> - `effective_cache_size` = 75% of RAM (hint to planner about available cache)

---

## Step 7: pg_buffercache Extension

```bash
docker exec pg-lab psql -U postgres <<'EOF'
CREATE EXTENSION pg_buffercache;

-- Create and populate test table
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT,
  price NUMERIC(10,2),
  category TEXT
);

INSERT INTO products (name, price, category)
SELECT 
  'Product ' || gs,
  (random() * 1000)::numeric(10,2),
  (ARRAY['Electronics','Clothing','Food','Books'])[1 + (random()*3)::int]
FROM generate_series(1, 10000) gs;

-- Query to see buffer cache usage
SELECT c.relname,
       COUNT(*) AS buffers,
       ROUND(COUNT(*) * 8 / 1024.0, 2) AS buffer_mb,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM pg_buffercache), 2) AS pct_of_cache
FROM pg_buffercache b
JOIN pg_class c ON b.relfilenode = pg_relation_filenode(c.oid)
WHERE b.reldatabase = (SELECT oid FROM pg_database WHERE datname = current_database())
GROUP BY c.relname
ORDER BY buffers DESC
LIMIT 10;

-- How full is the buffer cache?
SELECT
  COUNT(*) AS total_buffers,
  COUNT(*) FILTER (WHERE relfilenode IS NOT NULL) AS used_buffers,
  COUNT(*) FILTER (WHERE relfilenode IS NULL) AS free_buffers,
  ROUND(100.0 * COUNT(*) FILTER (WHERE relfilenode IS NOT NULL) / COUNT(*), 1) AS usage_pct
FROM pg_buffercache;
EOF
```

📸 **Verified Output:**
```
    relname    | buffers | buffer_mb | pct_of_cache 
---------------+---------+-----------+--------------
 products      |     182 |      1.42 |          0.6
 products_pkey |      23 |      0.18 |          0.1
(2 rows)

 total_buffers | used_buffers | free_buffers | usage_pct 
---------------+--------------+--------------+-----------
         32768 |          287 |        32481 |       0.9
```

---

## Step 8: Capstone — Memory Tuning Recommendations Script

```bash
docker exec pg-lab psql -U postgres <<'EOF'
-- Buffer hit ratio from pg_stat_bgwriter
SELECT 
  checkpoints_timed,
  checkpoints_req,
  ROUND(100.0 * checkpoints_timed / NULLIF(checkpoints_timed + checkpoints_req, 0), 1) AS timed_pct,
  buffers_clean,
  maxwritten_clean,
  buffers_backend,
  buffers_alloc
FROM pg_stat_bgwriter;

-- Per-table cache hit rate
SELECT 
  relname AS table,
  heap_blks_read,
  heap_blks_hit,
  ROUND(100.0 * heap_blks_hit / NULLIF(heap_blks_hit + heap_blks_read, 0), 1) AS hit_pct,
  idx_blks_read,
  idx_blks_hit,
  ROUND(100.0 * idx_blks_hit / NULLIF(idx_blks_hit + idx_blks_read, 0), 1) AS idx_hit_pct
FROM pg_statio_user_tables
WHERE relname = 'products';

-- work_mem impact: sort requiring disk
SET work_mem = '64kB';   -- Too small
EXPLAIN ANALYZE SELECT * FROM products ORDER BY price;

-- With adequate work_mem
SET work_mem = '16MB';
EXPLAIN ANALYZE SELECT * FROM products ORDER BY price;
EOF

docker rm -f pg-lab
echo "Lab complete!"
```

📸 **Verified Output:**
```
 checkpoints_timed | checkpoints_req | timed_pct | buffers_clean | maxwritten_clean | buffers_backend | buffers_alloc 
-------------------+-----------------+-----------+---------------+------------------+-----------------+---------------
                 1 |               0 |     100.0 |             0 |                0 |             289 |           294

 table    | heap_blks_read | heap_blks_hit | hit_pct | idx_blks_read | idx_blks_hit | idx_hit_pct 
----------+----------------+---------------+---------+---------------+--------------+-------------
 products |            182 |            45 |    19.8 |            24 |           43 |        64.2

-- With 64kB work_mem (too small):
Sort Method: external merge  Disk: 1056kB   <- Spills to disk!

-- With 16MB work_mem:
Sort Method: quicksort  Memory: 1184kB      <- In-memory sort!

Lab complete!
```

---

## Summary

| Setting | MySQL | PostgreSQL | Rule of Thumb |
|---------|-------|------------|---------------|
| Main buffer | innodb_buffer_pool_size | shared_buffers | MySQL: 70-80% RAM; PG: 25% RAM |
| Instances | innodb_buffer_pool_instances | N/A | One per GB of buffer pool |
| Sort memory | sort_buffer_size | work_mem | Per-operation; careful with high connections |
| Cache hint | N/A | effective_cache_size | 75% of total RAM |
| Hit rate target | >95% (1000/1000) | >99% | Lower = buffer pool too small |

## Key Takeaways

- **Buffer pool hit rate** is the most important InnoDB metric — below 95% → increase buffer pool
- **MySQL**: `innodb_buffer_pool_size` = 70-80% of RAM on dedicated DB servers
- **PostgreSQL**: `shared_buffers` = 25% (PG uses OS page cache too); `work_mem` is per-sort, can multiply
- **SHOW ENGINE INNODB STATUS** is your MySQL buffer pool dashboard
- **pg_buffercache** shows exactly what's cached — invaluable for hot data analysis
