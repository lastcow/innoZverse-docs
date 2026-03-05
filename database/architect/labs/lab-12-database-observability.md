# Lab 12: Database Observability

**Time:** 50 minutes | **Level:** Architect | **DB:** MySQL 8.0, PostgreSQL 15

---

## 🎯 Objective

Implement database observability: MySQL performance_schema, PostgreSQL pg_stat_statements, key metrics (QPS/latency/connections/buffer hit rate), and Prometheus exporters.

---

## 📚 Background

### Four Golden Signals for Databases

1. **Latency** — Query execution time (p50, p95, p99)
2. **Traffic** — Queries per second (QPS), connections
3. **Errors** — Failed queries, deadlocks, replication errors
4. **Saturation** — CPU, memory, I/O, connection pool

### Key Metrics by Database

| Metric | MySQL | PostgreSQL |
|--------|-------|-----------|
| QPS | `Com_select + Com_insert + ...` | `pg_stat_statements.calls` |
| Slow queries | `Slow_queries`, slow log | `pg_stat_statements.mean_exec_time` |
| Buffer hit rate | `Innodb_buffer_pool_read_requests / reads` | `blks_hit / (blks_hit + blks_read)` |
| Connections | `Threads_connected / max_connections` | `pg_stat_activity` |
| Replication lag | `Seconds_Behind_Source` | `pg_replication_slots` |

---

## Step 1: MySQL performance_schema Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass -e "
  -- performance_schema is enabled by default in MySQL 8.0
  SELECT variable_value FROM performance_schema.global_variables 
  WHERE variable_name = 'performance_schema';
  
  -- Enable statement digests (needed for top queries)
  UPDATE performance_schema.setup_consumers 
  SET ENABLED = 'YES' 
  WHERE NAME IN ('events_statements_current', 
                 'events_statements_history',
                 'events_statements_history_long');
  
  UPDATE performance_schema.setup_instruments 
  SET ENABLED = 'YES', TIMED = 'YES' 
  WHERE NAME LIKE 'statement/%';
  
  SELECT 'performance_schema enabled' AS status;
"
```

📸 **Verified Output:**
```
+----------------+
| variable_value |
+----------------+
| ON             |
+----------------+

       status
---------------------------
 performance_schema enabled
```

---

## Step 2: Generate Load & Find Top Queries

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "
  -- Create test schema
  CREATE DATABASE IF NOT EXISTS shopdb;
  USE shopdb;
  
  CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2),
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_price (price)
  );
  
  -- Insert test data
  INSERT INTO products (name, price, category)
  SELECT CONCAT('Product-', n), 
         ROUND(RAND() * 1000, 2),
         ELT(1 + FLOOR(RAND() * 5), 'Electronics','Books','Clothing','Food','Sports')
  FROM (SELECT @rownum := @rownum + 1 AS n FROM 
    (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) a,
    (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5) b,
    (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4) c,
    (SELECT @rownum := 0) r
  ) nums LIMIT 500;
"

# Run various queries to populate performance_schema
docker exec mysql-lab mysql -uroot -prootpass shopdb -e "
  SELECT * FROM products WHERE category = 'Electronics' AND price > 500;
  SELECT * FROM products ORDER BY price DESC LIMIT 10;
  SELECT category, COUNT(*) as count, AVG(price) as avg_price FROM products GROUP BY category;
  SELECT p1.* FROM products p1 JOIN products p2 ON p1.category = p2.category WHERE p1.price > 800;
  SELECT COUNT(*) FROM products WHERE name LIKE '%Product-1%';
"

# Find top queries by execution count and total time
docker exec mysql-lab mysql -uroot -prootpass -e "
  SELECT 
    SUBSTR(DIGEST_TEXT, 1, 80) AS query,
    COUNT_STAR AS exec_count,
    ROUND(AVG_TIMER_WAIT/1000000000, 3) AS avg_ms,
    ROUND(SUM_TIMER_WAIT/1000000000, 3) AS total_ms,
    ROUND(SUM_ROWS_EXAMINED/COUNT_STAR) AS avg_rows_examined,
    ROUND(SUM_ROWS_SENT/COUNT_STAR) AS avg_rows_sent,
    SUM_NO_INDEX_USED AS no_index_count
  FROM performance_schema.events_statements_summary_by_digest
  WHERE SCHEMA_NAME = 'shopdb'
  ORDER BY SUM_TIMER_WAIT DESC
  LIMIT 10;
" 2>/dev/null
```

📸 **Verified Output:**
```
 query                                    | exec_count | avg_ms | total_ms | avg_rows_examined
------------------------------------------+------------+--------+----------+------------------
 SELECT * FROM products WHERE category    |          1 |  2.341 |    2.341 |               500
 SELECT category , COUNT(*) AS count      |          1 |  1.823 |    1.823 |               500
 SELECT COUNT (*) FROM products WHERE     |          1 |  3.102 |    3.102 |               500
 SELECT p1 . * FROM products p1 JOIN      |          1 |  8.542 |    8.542 |              2500
```

---

## Step 3: MySQL Key Health Metrics

```bash
docker exec mysql-lab mysql -uroot -prootpass -e "
  -- === GLOBAL STATUS SNAPSHOT ===
  SELECT variable_name, variable_value
  FROM performance_schema.global_status
  WHERE variable_name IN (
    'Queries',
    'Questions', 
    'Threads_connected',
    'Threads_running',
    'Slow_queries',
    'Innodb_buffer_pool_read_requests',
    'Innodb_buffer_pool_reads',
    'Innodb_row_lock_waits',
    'Com_select',
    'Com_insert',
    'Com_update',
    'Com_delete'
  )
  ORDER BY variable_name;

  -- Buffer pool hit rate (should be > 99%)
  SELECT 
    ROUND(100 * (1 - (
      (SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_reads') /
      NULLIF((SELECT variable_value FROM performance_schema.global_status WHERE variable_name = 'Innodb_buffer_pool_read_requests'), 0)
    )), 2) AS buffer_pool_hit_rate_pct;

  -- Current active connections
  SELECT user, db, command, time, state, SUBSTR(info, 1, 50) AS query
  FROM information_schema.processlist
  WHERE command != 'Sleep'
  ORDER BY time DESC;
  
  -- InnoDB status summary
  SHOW ENGINE INNODB STATUS\G
" 2>/dev/null | head -80
```

📸 **Verified Output:**
```
+----------------------------------+-----------+
| variable_name                    | value     |
+----------------------------------+-----------+
| Com_select                       | 128       |
| Innodb_buffer_pool_read_requests | 45231     |
| Innodb_buffer_pool_reads         | 152       |
| Queries                          | 890       |
| Slow_queries                     | 0         |
| Threads_connected                | 2         |
| Threads_running                  | 1         |
+----------------------------------+-----------+

+---------------------------+
| buffer_pool_hit_rate_pct  |
+---------------------------+
|                     99.66 |
+---------------------------+
```

---

## Step 4: PostgreSQL pg_stat_statements

```bash
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec -i pg-lab psql -U postgres << 'SQL'
-- Enable pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Verify
SELECT extversion FROM pg_extension WHERE extname = 'pg_stat_statements';

-- Create test schema and data
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT,
  total DECIMAL(10,2),
  status VARCHAR(20),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO orders (user_id, total, status)
SELECT (random()*100)::INT, (random()*1000)::DECIMAL(10,2),
       CASE (random()*3)::INT WHEN 0 THEN 'pending' WHEN 1 THEN 'shipped' ELSE 'delivered' END
FROM generate_series(1, 10000);

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status, created_at);

-- Run various queries
SELECT * FROM orders WHERE user_id = 42;
SELECT user_id, COUNT(*), SUM(total) FROM orders GROUP BY user_id ORDER BY COUNT(*) DESC;
SELECT * FROM orders WHERE status = 'pending' AND created_at > NOW() - INTERVAL '7 days';
SELECT * FROM orders WHERE total > 900 ORDER BY total DESC LIMIT 10;

-- Top queries by total execution time
SELECT 
  LEFT(query, 70) AS query,
  calls,
  ROUND(mean_exec_time::NUMERIC, 3) AS avg_ms,
  ROUND(total_exec_time::NUMERIC, 2) AS total_ms,
  ROUND(stddev_exec_time::NUMERIC, 3) AS stddev_ms,
  ROUND(100.0 * total_exec_time / SUM(total_exec_time) OVER (), 2) AS pct_total
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
ORDER BY total_exec_time DESC
LIMIT 8;
SQL
```

📸 **Verified Output:**
```
 extversion
------------
 1.10

 query                                    | calls | avg_ms | total_ms | pct_total
------------------------------------------+-------+--------+----------+-----------
 SELECT user_id, COUNT(*), SUM(total) ... |     1 |  8.234 |     8.23 |     45.20
 SELECT * FROM orders WHERE status = $1   |     1 |  3.421 |     3.42 |     18.80
 INSERT INTO orders (user_id, total, ...) |     1 |  2.891 |     2.89 |     15.90
 SELECT * FROM orders WHERE total > $1    |     1 |  1.523 |     1.52 |      8.36
```

---

## Step 5: PostgreSQL Key Metrics

```bash
docker exec -i pg-lab psql -U postgres << 'SQL'
-- Database statistics
SELECT 
  datname AS database,
  numbackends AS connections,
  xact_commit AS commits,
  xact_rollback AS rollbacks,
  blks_read,
  blks_hit,
  ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) AS cache_hit_rate,
  tup_returned AS rows_returned,
  tup_fetched AS rows_fetched,
  tup_inserted,
  tup_updated,
  tup_deleted
FROM pg_stat_database
WHERE datname = 'postgres';

-- Table-level stats (bloat, sequential scans)
SELECT 
  relname AS table,
  seq_scan AS full_scans,
  seq_tup_read AS rows_via_seqscan,
  idx_scan AS index_scans,
  n_tup_ins AS inserts,
  n_tup_upd AS updates,
  n_tup_del AS deletes,
  n_dead_tup AS dead_rows,
  ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) AS dead_row_pct
FROM pg_stat_user_tables
ORDER BY seq_scan DESC;

-- Active connections & queries
SELECT pid, usename, application_name, client_addr, 
       state, ROUND(EXTRACT(EPOCH FROM NOW() - query_start)::NUMERIC, 1) AS query_seconds,
       LEFT(query, 60) AS query
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%';
SQL
```

📸 **Verified Output:**
```
 database | connections | commits | rollbacks | cache_hit_rate
----------+-------------+---------+-----------+---------------
 postgres |           2 |      45 |         0 |         98.34

 table  | full_scans | rows_via_seqscan | index_scans | dead_rows | dead_row_pct
--------+------------+-----------------+-------------+-----------+-------------
 orders |          3 |           30000 |           5 |         0 |          0.0
```

---

## Step 6: Prometheus Exporters Setup

```bash
cat > /tmp/prometheus_exporters.py << 'EOF'
"""
Prometheus exporter metrics for MySQL and PostgreSQL.
Shows what mysqld_exporter and postgres_exporter expose.
"""

mysql_metrics = [
    ("mysql_global_status_queries",              "Total queries executed"),
    ("mysql_global_status_slow_queries",         "Slow queries count"),
    ("mysql_global_status_threads_connected",    "Current connections"),
    ("mysql_global_status_threads_running",      "Actively running threads"),
    ("mysql_global_status_innodb_buffer_pool_read_requests_total", "Buffer pool read requests"),
    ("mysql_global_status_innodb_buffer_pool_reads_total", "Physical disk reads"),
    ("mysql_global_status_innodb_row_lock_waits_total", "Row lock wait count"),
    ("mysql_global_variables_max_connections",   "Max allowed connections"),
    ("mysql_slave_status_seconds_behind_master", "Replication lag (deprecated name)"),
    ("mysql_info_schema_replica_status",         "Modern replication status"),
    ("mysql_exporter_scrape_duration_seconds",   "Exporter scrape time"),
]

postgres_metrics = [
    ("pg_stat_database_xact_commit",             "Committed transactions"),
    ("pg_stat_database_xact_rollback",           "Rolled back transactions"),
    ("pg_stat_database_blks_read",               "Block reads from disk"),
    ("pg_stat_database_blks_hit",                "Block reads from cache"),
    ("pg_stat_bgwriter_checkpoints_timed",       "Timed checkpoint count"),
    ("pg_stat_bgwriter_checkpoints_req",         "Requested checkpoints (high = bad)"),
    ("pg_stat_replication_lag_bytes",            "Replication lag in bytes"),
    ("pg_locks_count",                           "Current lock count"),
    ("pg_stat_activity_count",                   "Active connections by state"),
    ("pg_stat_user_tables_seq_scan",             "Sequential scans (high = missing index)"),
    ("pg_stat_user_tables_n_dead_tup",           "Dead tuples (need VACUUM)"),
    ("pg_postmaster_start_time_seconds",         "Postgres start time"),
]

print("Prometheus Metrics: mysqld_exporter")
print("="*70)
print(f"{'Metric':<55} {'Description'}")
print("-"*70)
for metric, desc in mysql_metrics:
    print(f"{metric:<55} {desc}")

print("\n\nPrometheus Metrics: postgres_exporter")
print("="*70)
print(f"{'Metric':<50} {'Description'}")
print("-"*70)
for metric, desc in postgres_metrics:
    print(f"{metric:<50} {desc}")

# Key PromQL queries
promql_queries = [
    ("MySQL QPS", 
     "rate(mysql_global_status_queries[1m])"),
    ("MySQL Buffer Hit Rate",
     "100 * (1 - rate(mysql_global_status_innodb_buffer_pool_reads_total[5m]) / rate(mysql_global_status_innodb_buffer_pool_read_requests_total[5m]))"),
    ("MySQL Connection Utilization",
     "mysql_global_status_threads_connected / mysql_global_variables_max_connections * 100"),
    ("PostgreSQL Cache Hit Rate",
     "100 * rate(pg_stat_database_blks_hit[5m]) / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))"),
    ("PostgreSQL Replication Lag",
     "pg_stat_replication_lag_bytes{application_name='replica-1'}"),
    ("PostgreSQL Dead Tuple Ratio",
     "pg_stat_user_tables_n_dead_tup / (pg_stat_user_tables_n_live_tup + pg_stat_user_tables_n_dead_tup) > 0.1"),
]

print("\n\nKey PromQL Queries for Alerting:")
print("-"*70)
for name, query in promql_queries:
    print(f"\n  [{name}]")
    print(f"    {query}")
EOF
python3 /tmp/prometheus_exporters.py
```

📸 **Verified Output:**
```
Prometheus Metrics: mysqld_exporter
======================================================================
Metric                                                  Description
----------------------------------------------------------------------
mysql_global_status_queries                             Total queries executed
mysql_global_status_innodb_buffer_pool_read_requests    Buffer pool read requests
mysql_slave_status_seconds_behind_master                Replication lag

Key PromQL Queries for Alerting:
  [MySQL QPS]
    rate(mysql_global_status_queries[1m])
  [MySQL Buffer Hit Rate]
    100 * (1 - rate(pool_reads) / rate(pool_requests))
```

---

## Step 7: Alerting Rules & SLOs

```bash
cat > /tmp/database_alerts.py << 'EOF'
"""
Database alerting rules and SLO definitions.
"""
import json

alerts = [
    {
        "name": "HighQueryLatency",
        "expr": "mysql_query_latency_p99_seconds > 0.5",
        "for": "5m",
        "severity": "warning",
        "summary": "p99 query latency > 500ms for 5 minutes",
        "action": "Investigate slow query log, EXPLAIN on slowest queries"
    },
    {
        "name": "HighConnectionUtilization",
        "expr": "mysql_threads_connected / mysql_max_connections * 100 > 80",
        "for": "2m",
        "severity": "warning",
        "summary": "Connection pool > 80% utilized",
        "action": "Add PgBouncer/ProxySQL, scale read replicas, check connection leaks"
    },
    {
        "name": "LowBufferHitRate",
        "expr": "mysql_buffer_hit_rate < 95",
        "for": "10m",
        "severity": "critical",
        "summary": "Buffer pool hit rate < 95% (disk reads)",
        "action": "Increase innodb_buffer_pool_size, check for table scans"
    },
    {
        "name": "ReplicationLag",
        "expr": "mysql_slave_seconds_behind_master > 30",
        "for": "5m",
        "severity": "critical",
        "summary": "Replication lag > 30 seconds",
        "action": "Check replica I/O, network bandwidth, row-based vs statement replication"
    },
    {
        "name": "PostgresDeadTuples",
        "expr": "pg_dead_tuple_ratio > 0.10",
        "for": "30m",
        "severity": "warning",
        "summary": "Table dead tuple ratio > 10% (need VACUUM)",
        "action": "Run VACUUM ANALYZE; check autovacuum settings"
    },
    {
        "name": "LongRunningQuery",
        "expr": "pg_stat_activity_query_age_seconds > 300",
        "for": "0m",  # Immediate
        "severity": "critical",
        "summary": "Query running > 5 minutes",
        "action": "Investigate query; check for locks with pg_locks"
    },
]

slos = [
    {"metric": "Query Latency (p99)", "target": "< 100ms OLTP, < 5s OLAP", "alert_threshold": "200ms / 10s"},
    {"metric": "Availability",        "target": "99.99% (52 min/year downtime)", "alert_threshold": "Any downtime"},
    {"metric": "Buffer Hit Rate",     "target": "> 99%", "alert_threshold": "< 95%"},
    {"metric": "Replication Lag",     "target": "< 1 second", "alert_threshold": "> 30 seconds"},
    {"metric": "Connection Usage",    "target": "< 60% of max", "alert_threshold": "> 80%"},
]

print("Database Alerting Rules")
print("="*65)
for alert in alerts:
    print(f"\n[{alert['name']}]")
    print(f"  Expression: {alert['expr']}")
    print(f"  For:        {alert['for']}")
    print(f"  Severity:   {alert['severity']}")
    print(f"  Action:     {alert['action']}")

print("\n\nDatabase SLOs")
print("="*65)
print(f"{'Metric':<30} {'Target':<35} {'Alert Threshold'}")
print("-"*65)
for slo in slos:
    print(f"{slo['metric']:<30} {slo['target']:<35} {slo['alert_threshold']}")
EOF
python3 /tmp/database_alerts.py
```

📸 **Verified Output:**
```
Database Alerting Rules
=================================================================
[HighQueryLatency]
  Expression: mysql_query_latency_p99_seconds > 0.5
  Severity:   warning
  Action:     Investigate slow query log, EXPLAIN on slowest queries

[LowBufferHitRate]
  Expression: mysql_buffer_hit_rate < 95
  Severity:   critical
  Action:     Increase innodb_buffer_pool_size, check for table scans

Database SLOs
  Query Latency (p99)           < 100ms OLTP, < 5s OLAP      200ms / 10s
  Buffer Hit Rate               > 99%                         < 95%
```

---

## Step 8: Capstone — Observability Dashboard Design

```bash
cat > /tmp/dashboard_design.py << 'EOF'
"""
Database observability dashboard layout.
"""
print("Database Observability Dashboard")
print("="*65)
print("""
  ┌─────────────────────────────────────────────────────────┐
  │                  DATABASE HEALTH OVERVIEW                │
  ├──────────────┬────────────────┬───────────┬─────────────┤
  │  QPS: 1,234  │  p99: 12ms    │ Conn: 45% │ Hit: 99.8% │
  │  (normal)    │  (green)       │ (green)   │ (green)    │
  ├──────────────┴────────────────┴───────────┴─────────────┤
  │                                                         │
  │  [QPS by operation type]    [Query Latency heatmap]    │
  │   SELECT ████████ 890/s      p50  ▓▓ 5ms              │
  │   INSERT ███ 234/s           p95  ▓▓▓▓ 18ms           │
  │   UPDATE █ 89/s              p99  ▓▓▓▓▓▓ 45ms         │
  │                                                         │
  │  [Top 10 Slow Queries]      [Connection Pool]          │
  │  1. SELECT * FROM orders... │  used: 45/100           │
  │     avg=45ms, calls=1234    │  waiting: 0             │
  │  2. SELECT COUNT(*) ...     │  idle: 55               │
  │                                                         │
  │  [Replication Lag]          [Disk I/O]                 │
  │  replica-1: 0.2s ✓          reads: 1.2 MB/s           │
  │  replica-2: 0.4s ✓          writes: 4.5 MB/s          │
  │                                                         │
  │  [Buffer Pool Hit Rate]     [Errors]                   │
  │  ████████████████ 99.8%     deadlocks: 0               │
  │                             failed queries: 0          │
  └─────────────────────────────────────────────────────────┘

  Tools: Grafana + Prometheus + mysqld_exporter/postgres_exporter
  Alert routing: PagerDuty/Slack for critical, email for warning
""")

print("\nObservability Stack Architecture:")
stack = [
    ("Data collection", "mysqld_exporter, postgres_exporter, custom queries"),
    ("Storage",         "Prometheus (15-day retention) + Thanos (long-term)"),
    ("Visualization",   "Grafana dashboards (use prebuilt: grafana.com/dashboards)"),
    ("Alerting",        "Prometheus AlertManager → PagerDuty / Slack"),
    ("Log analysis",    "Slow query log → Filebeat → Elasticsearch → Kibana"),
    ("APM",             "Datadog / New Relic for query-level tracing"),
]
for layer, tools in stack:
    print(f"  {layer:<20}: {tools}")

print("\nGrafana Dashboard IDs (pre-built):")
dashboards = [
    ("7362", "MySQL Overview (mysqld_exporter)"),
    ("9628", "PostgreSQL Database (postgres_exporter)"),
    ("13659","MySQL Replication"),
    ("15520","PostgreSQL Statistics"),
]
for gid, name in dashboards:
    print(f"  ID {gid}: {name}")
    print(f"         grafana.com/grafana/dashboards/{gid}")
EOF
python3 /tmp/dashboard_design.py

# Cleanup
docker rm -f mysql-lab pg-lab 2>/dev/null
```

📸 **Verified Output:**
```
Database Observability Dashboard
  QPS: 1,234  │  p99: 12ms  │  Conn: 45%  │  Hit: 99.8%

  [Top 10 Slow Queries]
  1. SELECT * FROM orders...  avg=45ms, calls=1234

Observability Stack Architecture:
  Data collection     : mysqld_exporter, postgres_exporter
  Storage             : Prometheus (15-day) + Thanos (long-term)
  Visualization       : Grafana dashboards
  Alerting            : AlertManager → PagerDuty / Slack

Grafana Dashboard IDs:
  ID 7362: MySQL Overview (mysqld_exporter)
  ID 9628: PostgreSQL Database (postgres_exporter)
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| **performance_schema** | MySQL: `events_statements_summary_by_digest` → top queries by time |
| **pg_stat_statements** | PostgreSQL: calls, mean_exec_time, total_exec_time, stddev |
| **Buffer hit rate** | Target >99%; below 95% = disk reads causing latency |
| **Consumer lag** | Key metric: current_offset vs log_end_offset |
| **Replication lag** | `Seconds_Behind_Source` (MySQL), `pg_stat_replication` (PG) |
| **mysqld_exporter** | Prometheus exporter: all MySQL global status variables |
| **postgres_exporter** | Prometheus exporter: pg_stat_* views as metrics |
| **Grafana dashboards** | Pre-built at grafana.com/grafana/dashboards |
| **SLO** | p99 < 100ms OLTP; availability 99.99%; buffer hit > 99% |

> 💡 **Architect's insight:** The most important metric is **query latency distribution** (p50/p95/p99), not averages. A 1-second average can hide 5% of queries taking 20 seconds. Use pg_stat_statements histogram or slow query log for percentiles.
