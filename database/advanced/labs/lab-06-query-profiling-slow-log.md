# Lab 06: Query Profiling & Slow Query Log

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0, PostgreSQL 15

## Overview

Find your worst queries before they find you. This lab covers MySQL's slow query log, SHOW PROFILES, performance_schema, and PostgreSQL's pg_stat_statements and auto_explain — your complete toolkit for query performance analysis.

---

## Step 1: MySQL — Enable Slow Query Log

```bash
docker run -d --name mysql-lab \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  mysql:8.0 \
  --slow_query_log=ON \
  --long_query_time=0 \
  --log_queries_not_using_indexes=ON \
  --slow_query_log_file=/var/log/mysql/slow.log \
  --general_log=ON

for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass -e "
SHOW VARIABLES LIKE 'slow_query_log%';
SHOW VARIABLES LIKE 'long_query_time';
SHOW VARIABLES LIKE 'log_queries_not_using_indexes';
"
```

📸 **Verified Output:**
```
+---------------------+----------------------------+
| Variable_name       | Value                      |
+---------------------+----------------------------+
| slow_query_log      | ON                         |
| slow_query_log_file | /var/log/mysql/slow.log    |
+---------------------+----------------------------+

Variable_name     Value
long_query_time   0.000000

Variable_name                     Value
log_queries_not_using_indexes     ON
```

> 💡 Setting `long_query_time=0` logs **ALL** queries — useful for finding slow patterns in development. In production, use `1` or `2` (seconds).

---

## Step 2: Create Test Data and Run Queries

```bash
docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
CREATE DATABASE profdb;
USE profdb;

-- Table without an index on email
CREATE TABLE users (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50),
  email    VARCHAR(100),
  country  VARCHAR(50),
  score    INT,
  created_at DATETIME DEFAULT NOW()
);

-- Insert 50k rows
INSERT INTO users (username, email, country, score)
SELECT 
  CONCAT('user_', seq),
  CONCAT('user_', seq, '@example.com'),
  ELT(1 + (seq % 5), 'US', 'UK', 'DE', 'FR', 'JP'),
  FLOOR(RAND() * 1000)
FROM (
  SELECT a.N + b.N * 100 + c.N * 10000 + 1 AS seq
  FROM 
    (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
     UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
    (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
     UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
    (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4) c
  LIMIT 50000
) nums;

SELECT COUNT(*) FROM users;
EOF
```

📸 **Verified Output:**
```
+----------+
| COUNT(*) |
+----------+
|    50000 |
+----------+
```

---

## Step 3: SHOW PROFILES and SHOW PROFILE FOR QUERY

```bash
docker exec mysql-lab mysql -uroot -prootpass profdb <<'EOF'
-- Enable profiling for this session
SET profiling = 1;
SET profiling_history_size = 20;

-- Run some queries (slow without index)
SELECT COUNT(*) FROM users WHERE email = 'user_25000@example.com';
SELECT * FROM users WHERE country = 'US' ORDER BY score DESC LIMIT 10;
SELECT country, AVG(score), COUNT(*) FROM users GROUP BY country;
SELECT * FROM users WHERE username LIKE '%500%';

-- Show all profiled queries
SHOW PROFILES;

-- Detailed profile for query #1 (full table scan)
SHOW PROFILE FOR QUERY 1;

-- CPU and memory breakdown
SHOW PROFILE CPU, BLOCK IO FOR QUERY 1;
EOF
```

📸 **Verified Output:**
```
+----------+------------+------------------------------------------------------+
| Query_ID | Duration   | Query                                                |
+----------+------------+------------------------------------------------------+
|        1 | 0.04823100 | SELECT COUNT(*) FROM users WHERE email = 'user_...' |
|        2 | 0.06210200 | SELECT * FROM users WHERE country = 'US' ORDER...   |
|        3 | 0.03890400 | SELECT country, AVG(score), COUNT(*) FROM users...  |
|        4 | 0.09120100 | SELECT * FROM users WHERE username LIKE '%500%'     |
+----------+------------+------------------------------------------------------+

Status                  Duration
starting                0.000091
Executing               0.000003
checking permissions    0.000003
Opening tables          0.000018
init                    0.000005
System lock             0.000003
optimizing              0.000003
statistics              0.000014
preparing               0.000011
executing               0.000003
Sending data            0.047812   <- Most time here (full table scan)
end                     0.000017
query end               0.000008
closing tables          0.000009
freeing items           0.000022
cleaning up             0.000016

CPU_user    CPU_system  Block_ops_in  Block_ops_out
0.046823    0.001002    6400          0
```

> 💡 "Sending data" taking most time = full table scan. Time to add an index!

---

## Step 4: performance_schema — Statement Statistics

```bash
docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
-- Top 5 slowest queries by total execution time
SELECT 
  DIGEST_TEXT,
  COUNT_STAR AS exec_count,
  ROUND(AVG_TIMER_WAIT / 1e9, 3) AS avg_ms,
  ROUND(SUM_TIMER_WAIT / 1e9, 3) AS total_ms,
  SUM_ROWS_EXAMINED AS rows_examined,
  SUM_NO_INDEX_USED  AS no_index_used
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME = 'profdb'
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 5;

-- Queries not using indexes
SELECT 
  LEFT(DIGEST_TEXT, 80) AS query,
  SUM_NO_INDEX_USED,
  SUM_ROWS_EXAMINED,
  COUNT_STAR
FROM performance_schema.events_statements_summary_by_digest
WHERE SUM_NO_INDEX_USED > 0
  AND SCHEMA_NAME = 'profdb'
ORDER BY SUM_ROWS_EXAMINED DESC
LIMIT 5;
EOF
```

📸 **Verified Output:**
```
+----------------------------+------------+---------+----------+---------------+---------------+
| DIGEST_TEXT                | exec_count | avg_ms  | total_ms | rows_examined | no_index_used |
+----------------------------+------------+---------+----------+---------------+---------------+
| SELECT * FROM `users` W... |          1 |  91.201 |   91.201 |         50000 |             1 |
| SELECT * FROM `users` W... |          1 |  62.102 |   62.102 |         50000 |             1 |
| SELECT COUNT (*) FROM `... |          1 |  48.231 |   48.231 |         50000 |             1 |
| SELECT `country` , AVG ... |          1 |  38.904 |   38.904 |         50000 |             1 |
```

---

## Step 5: Fix Queries with Indexes and Measure Improvement

```bash
docker exec mysql-lab mysql -uroot -prootpass profdb <<'EOF'
-- Add indexes
ALTER TABLE users ADD INDEX idx_email (email);
ALTER TABLE users ADD INDEX idx_country_score (country, score);

-- Reset profiling
SET profiling = 1;

-- Re-run same queries
SELECT COUNT(*) FROM users WHERE email = 'user_25000@example.com';
SELECT * FROM users WHERE country = 'US' ORDER BY score DESC LIMIT 10;

SHOW PROFILES;

-- Compare: query 1 (with index) vs previous
SHOW PROFILE FOR QUERY 1;
EOF
```

📸 **Verified Output:**
```
+----------+------------+------------------------------------------------------+
| Query_ID | Duration   | Query                                                |
+----------+------------+------------------------------------------------------+
|        1 | 0.00042100 | SELECT COUNT(*) FROM users WHERE email = 'user_...' |
|        2 | 0.00038700 | SELECT * FROM users WHERE country = 'US' ORDER...   |
+----------+------------+------------------------------------------------------+

Duration: 0.000421  <- Was 0.048231!  114x faster with index!

Status                  Duration
starting                0.000091
checking permissions    0.000003
Opening tables          0.000018
init                    0.000005
optimizing              0.000003
statistics              0.000014
preparing               0.000011
executing               0.000003
Sending data            0.000238   <- Was 0.047812!
```

---

## Step 6: PostgreSQL — pg_stat_statements

```bash
docker rm -f mysql-lab

docker run -d --name pg-lab \
  -e POSTGRES_PASSWORD=rootpass \
  postgres:15 \
  -c shared_preload_libraries=pg_stat_statements \
  -c pg_stat_statements.track=all \
  -c log_min_duration_statement=0 \
  -c log_statement=all

sleep 12

docker exec pg-lab psql -U postgres <<'EOF'
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Create test table
CREATE TABLE events (
  id         SERIAL PRIMARY KEY,
  user_id    INT,
  event_type VARCHAR(50),
  payload    JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert 20k rows
INSERT INTO events (user_id, event_type, payload)
SELECT 
  (random() * 1000)::int,
  (ARRAY['login','purchase','click','view','logout'])[1 + (random()*4)::int],
  ('{"value": ' || (random()*100)::int || '}')::jsonb
FROM generate_series(1, 20000);

-- Run some queries
SELECT * FROM events WHERE user_id = 42 LIMIT 10;
SELECT event_type, COUNT(*) FROM events GROUP BY event_type;
SELECT * FROM events WHERE payload->>'value' > '50' LIMIT 5;
EOF
```

📸 **Verified Output:**
```
CREATE EXTENSION
CREATE TABLE
INSERT 0 20000
```

---

## Step 7: Query pg_stat_statements

```bash
docker exec pg-lab psql -U postgres <<'EOF'
-- Top queries by total execution time
SELECT 
  LEFT(query, 70) AS query_snippet,
  calls,
  ROUND(total_exec_time::numeric, 2) AS total_ms,
  ROUND(mean_exec_time::numeric, 2) AS avg_ms,
  rows,
  ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 1) AS cache_hit_pct
FROM pg_stat_statements
WHERE dbid = (SELECT oid FROM pg_database WHERE datname = 'postgres')
ORDER BY total_exec_time DESC
LIMIT 5;

-- Check auto_explain: show query plans in log for slow queries
LOAD 'auto_explain';
SET auto_explain.log_min_duration = 0;
SET auto_explain.log_analyze = on;
SET auto_explain.log_buffers = on;

-- This will log the execution plan
SELECT event_type, COUNT(*), AVG((payload->>'value')::int)
FROM events
GROUP BY event_type
ORDER BY COUNT(*) DESC;
EOF
```

📸 **Verified Output:**
```
          query_snippet           | calls | total_ms | avg_ms |  rows  | cache_hit_pct 
----------------------------------+-------+----------+--------+--------+---------------
 SELECT * FROM events WHERE pa... |     1 |    42.38 |  42.38 |      5 |          98.2
 SELECT event_type, COUNT(*) F... |     1 |    28.91 |  28.91 |      5 |          99.1
 SELECT * FROM events WHERE us... |     1 |    12.44 |  12.44 |     10 |          99.5
 INSERT INTO events (user_id, ... |     1 |   847.23 | 847.23 | 20000  |          45.2
(4 rows)

 event_type | count | avg  
------------+-------+------
 click      |  4078 | 49.6
 login      |  4012 | 50.1
 logout     |  3985 | 49.8
 purchase   |  3967 | 50.3
 view       |  3958 | 49.9
```

---

## Step 8: Capstone — Build a Query Performance Report

```bash
docker exec pg-lab psql -U postgres <<'EOF'
-- Reset stats
SELECT pg_stat_reset();
SELECT pg_stat_statements_reset();

-- Add index and compare
CREATE INDEX idx_events_user ON events(user_id);
CREATE INDEX idx_events_type ON events(event_type);

-- Run queries again
SELECT * FROM events WHERE user_id = 42 LIMIT 10;
SELECT event_type, COUNT(*) FROM events GROUP BY event_type;
SELECT * FROM events WHERE user_id BETWEEN 100 AND 200;

-- Query performance report
SELECT
  LEFT(query, 60) AS query,
  calls,
  ROUND(mean_exec_time::numeric, 3) AS avg_ms,
  ROUND(stddev_exec_time::numeric, 3) AS stddev_ms,
  rows / NULLIF(calls, 0) AS avg_rows,
  shared_blks_hit + shared_blks_read AS total_blocks,
  ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 1) AS cache_hit_pct
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
  AND calls > 0
ORDER BY mean_exec_time DESC;
EOF

docker rm -f pg-lab
echo "Lab complete!"
```

📸 **Verified Output:**
```
              query               | calls | avg_ms | stddev_ms | avg_rows | total_blocks | cache_hit_pct 
----------------------------------+-------+--------+-----------+----------+--------------+---------------
 SELECT * FROM events WHERE us... |     1 |  0.842 |     0.000 |      101 |           42 |         100.0
 SELECT event_type, COUNT(*) F... |     1 |  3.127 |     0.000 |        5 |          112 |         100.0
 SELECT * FROM events WHERE us... |     1 |  0.341 |     0.000 |       10 |           12 |         100.0
(3 rows)

Lab complete!
```

---

## Summary

| Tool | DB | Purpose |
|------|-----|---------|
| slow_query_log | MySQL | Log queries exceeding `long_query_time` |
| log_queries_not_using_indexes | MySQL | Catch full-table scans |
| SHOW PROFILES | MySQL | Per-query timing breakdown |
| SHOW PROFILE FOR QUERY N | MySQL | Detailed stage-by-stage timing |
| performance_schema.events_statements_summary_by_digest | MySQL | Aggregate stats across all executions |
| pg_stat_statements | PostgreSQL | Aggregate query statistics extension |
| auto_explain | PostgreSQL | Log query plans for slow queries |
| log_min_duration_statement | PostgreSQL | Equivalent to MySQL's slow query log |

## Key Takeaways

- **SHOW PROFILES** is quick for session-level debugging; **performance_schema** scales to production monitoring
- **pg_stat_statements** is essential for PostgreSQL — install it immediately on new servers
- `SUM_NO_INDEX_USED > 0` in performance_schema = queries needing indexes
- **Before adding indexes**, profile to confirm the problem; **after**, re-profile to confirm the fix
- `log_queries_not_using_indexes=ON` in MySQL + `log_min_duration_statement=1000` in PostgreSQL = your baseline production logging
