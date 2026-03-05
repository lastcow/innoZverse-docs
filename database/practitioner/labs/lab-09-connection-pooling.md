# Lab 09: Connection Pooling

**Time:** 40 minutes | **Level:** Practitioner | **DB:** PostgreSQL 15 (PgBouncer) + MySQL 8.0 (ProxySQL)

Each new database connection spawns a process/thread and costs ~2-10ms + ~5MB RAM. Connection pooling reuses connections, enabling thousands of app connections through a handful of database connections.

---

## Step 1 — The Connection Cost Problem

```sql
-- PostgreSQL: each connection = a backend process
SELECT count(*) AS active_connections FROM pg_stat_activity;
SELECT setting AS max_connections FROM pg_settings WHERE name = 'max_connections';

-- Check connection overhead
SELECT pid, usename, application_name, state, wait_event_type,
       ROUND(EXTRACT(EPOCH FROM (NOW() - backend_start))) AS age_seconds
FROM pg_stat_activity
WHERE pid != pg_backend_pid()
ORDER BY backend_start;
```

**Why pooling matters:**
- PostgreSQL default: `max_connections = 100`
- Each connection: ~5MB RAM + fork overhead
- 1000 app servers × 10 connections each = 10,000 connections needed
- Solution: app connects to pooler, pooler maintains small pool to DB

---

## Step 2 — PgBouncer: Install and Configure

```bash
# Install (Ubuntu/Debian)
apt-get install -y pgbouncer

# Or run via Docker
docker run -d --name pgbouncer \
  -e DATABASE_URL="postgresql://postgres:rootpass@pg-host:5432/postgres" \
  -p 5432:5432 \
  bitnami/pgbouncer:latest
```

**pgbouncer.ini** — the core configuration file:
```ini
[databases]
# Format: alias = host=... port=... dbname=...
myapp = host=127.0.0.1 port=5432 dbname=postgres

[pgbouncer]
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid

# Network
listen_addr = *
listen_port = 6432

# Authentication
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool configuration
pool_mode = transaction        # session | transaction | statement
max_client_conn = 1000         # max app connections to pgbouncer
default_pool_size = 20         # connections pgbouncer maintains to DB
min_pool_size = 5              # keep at least 5 connections ready
reserve_pool_size = 5          # extra connections for burst
reserve_pool_timeout = 5       # seconds before using reserve pool
max_db_connections = 50        # cap per database

# Timeouts
server_idle_timeout = 600      # close idle server connections after 10min
client_idle_timeout = 0        # 0 = no timeout
query_timeout = 0              # 0 = no timeout
```

```bash
# userlist.txt format (md5 hash of "md5" + password + username)
# Generate: echo -n "md5$(echo -n 'passwordusername' | md5sum | cut -d' ' -f1)"
echo '"postgres" "md5<hash>"' > /etc/pgbouncer/userlist.txt
pgbouncer -d /etc/pgbouncer/pgbouncer.ini
```

---

## Step 3 — PgBouncer Pooling Modes

| Mode | Connection reuse | Transaction behavior | Use case |
|------|-----------------|---------------------|----------|
| **session** | Per-session lifetime | Full ACID, SET vars persist | Legacy apps, prepared statements |
| **transaction** | Released after each transaction | Cannot use session-level SET | Most web apps, REST APIs |
| **statement** | Released after each statement | No multi-statement transactions | Read-only analytics |

> 💡 **Transaction mode** is the sweet spot for web applications: a pool of 20 DB connections can serve thousands of concurrent app connections because each request only holds a connection during a transaction.

```ini
# For Django/Rails/typical web apps:
pool_mode = transaction
default_pool_size = 25

# For apps using prepared statements:
pool_mode = session
default_pool_size = 50
```

---

## Step 4 — PgBouncer: SHOW Commands

```sql
-- Connect to PgBouncer admin console
psql -h 127.0.0.1 -p 6432 -U pgbouncer pgbouncer

-- Pool statistics
SHOW POOLS;
```

**SHOW POOLS output:**
```
 database |   user   | cl_active | cl_waiting | sv_active | sv_idle | sv_used | maxwait
----------+----------+-----------+------------+-----------+---------+---------+---------
 myapp    | postgres |        15 |          0 |        15 |         5 |       0 |       0
```

| Column | Meaning |
|--------|---------|
| `cl_active` | Client connections actively using a server connection |
| `cl_waiting` | Client connections waiting for a free server connection |
| `sv_active` | Server connections actively serving a client |
| `sv_idle` | Server connections idle and ready |
| `maxwait` | Longest wait time (seconds) — high = pool too small |

```sql
SHOW STATS;    -- Per-database query/data throughput
SHOW CLIENTS;  -- All client connections
SHOW SERVERS;  -- All server (DB) connections
SHOW CONFIG;   -- Current configuration

-- Reload config without restart
RELOAD;

-- Pause/resume for maintenance
PAUSE myapp;
RESUME myapp;
```

---

## Step 5 — ProxySQL for MySQL

```bash
# Run ProxySQL
docker run -d --name proxysql \
  -p 6033:6033 -p 6032:6032 \
  proxysql/proxysql
```

**ProxySQL key concepts:**
- **Hostgroups**: groups of MySQL servers (e.g., 10 = writes, 20 = reads)
- **Query Rules**: route queries to hostgroups based on regex patterns

```sql
-- Connect to ProxySQL admin
mysql -h 127.0.0.1 -P 6032 -u admin -padmin

-- Add MySQL backend servers
INSERT INTO mysql_servers (hostgroup_id, hostname, port, weight)
VALUES
  (10, 'mysql-primary',  3306, 1000),  -- write hostgroup
  (20, 'mysql-replica1', 3306, 1000),  -- read hostgroup
  (20, 'mysql-replica2', 3306, 500);   -- lower weight

-- Add MySQL user
INSERT INTO mysql_users (username, password, default_hostgroup)
VALUES ('app_user', 'AppPass123!', 10);

-- Query routing rules
INSERT INTO mysql_query_rules (rule_id, active, match_pattern, destination_hostgroup, apply)
VALUES
  (1, 1, '^SELECT.*FOR UPDATE', 10, 1),  -- SELECT FOR UPDATE → primary
  (2, 1, '^SELECT',             20, 1),  -- All other SELECT → replicas
  (3, 1, '.*',                  10, 1);  -- Everything else → primary

-- Apply changes
LOAD MYSQL SERVERS TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
LOAD MYSQL USERS TO RUNTIME;
SAVE MYSQL USERS TO DISK;
LOAD MYSQL QUERY RULES TO RUNTIME;
SAVE MYSQL QUERY RULES TO DISK;
```

---

## Step 6 — ProxySQL: SHOW POOLS and SHOW STATS

```sql
-- Connection pool status
SHOW MYSQL CONNECTION POOL\G
```

```
hostgroup | srv_host       | srv_port | status | connused | connfree | connok | connERR | queries
----------+----------------+----------+--------+----------+----------+--------+---------+--------
       10 | mysql-primary  |     3306 | ONLINE |        5 |       15 |    423 |       0 |    1250
       20 | mysql-replica1 |     3306 | ONLINE |        3 |       17 |    312 |       0 |    3420
```

```sql
-- Query digest / slow queries
SELECT hostgroup, sum_time/count_star AS avg_time_us,
       count_star, digest_text
FROM stats_mysql_query_digest
ORDER BY sum_time DESC
LIMIT 10;
```

---

## Step 7 — Connection Pool Tuning

```sql
-- PostgreSQL: find optimal pool size
-- Rule of thumb: pool_size = num_cores * 2 + spindle_count
-- For 4-core, SSD: pool_size ≈ 9-10

-- Monitor wait time
SELECT * FROM pg_stat_activity
WHERE wait_event_type = 'Client'
  AND wait_event = 'ClientRead';

-- PgBouncer alert: if maxwait > 1s, increase pool size
-- Check:
-- SHOW STATS; -- look at avg_wait_time
```

**Connection string changes for PgBouncer:**
```python
# Before (direct to PostgreSQL):
DATABASE_URL = "postgresql://user:pass@db-host:5432/myapp"

# After (via PgBouncer):
DATABASE_URL = "postgresql://user:pass@pgbouncer-host:6432/myapp"
# Application sees no difference!
```

> 💡 In **transaction mode**, avoid session-level features: `SET LOCAL` variables, `PREPARE`/`EXECUTE` statements, advisory locks, and `LISTEN`/`NOTIFY`. Use `session` mode for these.

---

## Step 8 — Capstone: Sizing a Connection Pool

Simulate load to find the right pool size:

```bash
# Install pgbench
apt-get install postgresql-client

# Initialize test data (scale=10 = ~1.5M rows)
pgbench -h pg-host -U postgres -i -s 10 postgres

# Benchmark with 50 clients, 4 threads, 60 seconds
pgbench -h pgbouncer-host -p 6432 -U postgres \
  -c 50 -j 4 -T 60 postgres

# Output shows:
# tps = 1234 (including connections establishment)
# latency average = 40.5 ms

# Compare: direct to PostgreSQL
pgbench -h pg-host -p 5432 -U postgres \
  -c 50 -j 4 -T 60 postgres
```

```sql
-- Formula for pool_size (Hikari/PgBouncer recommendation):
-- pool_size = (core_count * 2) + effective_spindle_count
-- For 8-core + NVMe SSD: pool_size = 17

-- Calculate your application's connection needs:
SELECT
  10 AS app_servers,
  50 AS connections_per_server,
  20 AS pgbouncer_pool_size,
  (10 * 50) AS total_app_connections,    -- 500
  20 AS actual_db_connections,           -- 20
  (10.0 * 50 / 20) AS multiplier;       -- 25x reduction
```

---

## Summary

| Feature | PgBouncer | ProxySQL |
|---------|-----------|----------|
| Database | PostgreSQL | MySQL |
| Pool modes | session / transaction / statement | Connection pooling |
| Read/write split | No (use HAProxy) | Yes (hostgroups + query rules) |
| Admin interface | `psql` on port 6432 | `mysql` on port 6032 |
| Config reload | `RELOAD;` | `LOAD ... TO RUNTIME;` |
| Key metric | `maxwait` in SHOW POOLS | `avg_time_us` in query digest |
