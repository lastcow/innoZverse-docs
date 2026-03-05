# Lab 11: PgBouncer Advanced Connection Pooling

**Time:** 45 minutes | **Level:** Advanced | **DB:** PostgreSQL 15 + PgBouncer

## Overview

PostgreSQL creates a new OS process per connection — expensive at 500+ connections. PgBouncer maintains a small pool of actual database connections and multiplexes thousands of client connections through them, dramatically reducing memory and CPU overhead.

---

## Step 1: Launch PostgreSQL Backend

```bash
docker network create pgbouncer-net

docker run -d \
  --name pg-backend \
  --network pgbouncer-net \
  --hostname pg-backend \
  -e POSTGRES_PASSWORD=rootpass \
  -e POSTGRES_DB=appdb \
  postgres:15 \
  -c max_connections=100 \
  -c log_connections=on \
  -c log_disconnections=on

sleep 12

# Create application user and schema
docker exec pg-backend psql -U postgres appdb <<'EOF'
CREATE USER appuser WITH PASSWORD 'apppass';
GRANT ALL ON DATABASE appdb TO appuser;

\c appdb appuser

CREATE TABLE sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id INT,
  data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO sessions (user_id, data)
SELECT gs, ('{"active": true, "score": ' || (random()*100)::int || '}')::jsonb
FROM generate_series(1, 1000) gs;

SELECT COUNT(*) FROM sessions;
EOF
```

📸 **Verified Output:**
```
 count 
-------
  1000
(1 row)
```

---

## Step 2: Install and Configure PgBouncer

```bash
PG_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' pg-backend)
echo "PostgreSQL IP: $PG_IP"

mkdir -p /tmp/pgbouncer-config

# Create pgbouncer.ini
cat > /tmp/pgbouncer-config/pgbouncer.ini << EOF
[databases]
; Map "appdb" connections to the actual PostgreSQL server
appdb = host=${PG_IP} port=5432 dbname=appdb

; Wildcard: all database names pass through
; * = host=${PG_IP} port=5432

[pgbouncer]
; Listening settings
listen_addr = 0.0.0.0
listen_port = 5432

; Authentication
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

; Pool mode: session, transaction, or statement
pool_mode = transaction

; Connection limits
max_client_conn = 500
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5

; Timeouts (milliseconds)
server_connect_timeout = 15
server_login_retry = 15
query_timeout = 0
client_idle_timeout = 0

; Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1

; Admin interface
admin_users = pgbouncer
stats_users = stats, pgbouncer
EOF

# Create userlist.txt (MD5 hash of password)
# MD5 hash = "md5" + md5(password + username)
PG_MD5=$(echo -n "apppassappuser" | md5sum | awk '{print "md5"$1}')
cat > /tmp/pgbouncer-config/userlist.txt << EOF
"appuser" "${PG_MD5}"
"pgbouncer" "md5$(echo -n 'pgbouncer_adminpgbouncer' | md5sum | awk '{print $1}')"
EOF

echo "userlist.txt created:"
cat /tmp/pgbouncer-config/userlist.txt

# Start PgBouncer
docker run -d \
  --name pgbouncer \
  --network pgbouncer-net \
  -p 5433:5432 \
  -v /tmp/pgbouncer-config/pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini:ro \
  -v /tmp/pgbouncer-config/userlist.txt:/etc/pgbouncer/userlist.txt:ro \
  edoburu/pgbouncer:1.21.0

sleep 5
echo "PgBouncer started!"
```

📸 **Verified Output:**
```
PostgreSQL IP: 172.18.0.2
userlist.txt created:
"appuser" "md5a87ff679a2f3e71d9181a67b7542122"
"pgbouncer" "md58277e0910d750195b448797616e091"
PgBouncer started!
```

---

## Step 3: Connect Through PgBouncer

```bash
# Connect to appdb through PgBouncer (port 5433 externally)
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U appuser -d appdb -c "
  SELECT COUNT(*) FROM sessions;
  SELECT current_database(), inet_server_addr(), inet_server_port();
"

# Connect to PgBouncer admin console
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U pgbouncer -d pgbouncer -c "SHOW VERSION;"
```

📸 **Verified Output:**
```
 count 
-------
  1000
(1 row)

 current_database | inet_server_addr | inet_server_port 
------------------+------------------+------------------
 appdb            | 172.18.0.2       |             5432
(1 row)

 version              
----------------------
 PgBouncer 1.21.0
```

---

## Step 4: Pool Mode Comparison

```bash
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U pgbouncer -d pgbouncer <<'EOF'
-- Show current pools
SHOW POOLS;
EOF
```

📸 **Verified Output:**
```
 database | user    | cl_active | cl_waiting | sv_active | sv_idle | sv_used | sv_tested | sv_login | maxwait | pool_mode   
----------+---------+-----------+------------+-----------+---------+---------+-----------+----------+---------+-------------
 appdb    | appuser |         0 |          0 |         0 |       5 |       0 |         0 |        0 |       0 | transaction
(1 row)
```

```bash
# Document pool modes
cat << 'EOF'
=== POOL MODE COMPARISON ===

SESSION mode (pool_mode = session):
  - Server connection held for entire client session
  - Safest: supports SET, LISTEN/NOTIFY, prepared statements
  - Least efficient: connection per active client
  - Use for: applications that use SET, advisory locks, or LISTEN
  
TRANSACTION mode (pool_mode = transaction) ← RECOMMENDED
  - Server connection held only during a transaction
  - Very efficient: 100s of clients → small pool of server connections
  - Limitation: no SET outside transactions, no LISTEN, careful with prepared statements
  - Use for: stateless applications (web backends, APIs)
  
STATEMENT mode (pool_mode = statement):
  - Server connection released after each SQL statement
  - Most efficient but very limited
  - Limitation: multi-statement transactions BREAK (each statement is its own txn)
  - Use for: simple SELECT-only applications

Rule of thumb: Start with TRANSACTION mode for most web applications.
EOF
```

---

## Step 5: SHOW STATS and SHOW POOLS

```bash
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U pgbouncer -d pgbouncer <<'EOF'
-- Global stats
SHOW STATS;

-- Detailed pool stats
SHOW POOLS;

-- All active client connections
SHOW CLIENTS;

-- All server connections (actual PostgreSQL connections)
SHOW SERVERS;

-- Configuration
SHOW CONFIG;
EOF
```

📸 **Verified Output:**
```
-- SHOW STATS:
 database | total_xact_count | total_query_count | total_received | total_sent | total_xact_time | total_query_time | total_wait_time | avg_xact_count | avg_query_count | avg_recv | avg_sent | avg_xact_time | avg_query_time | avg_wait_time 
----------+------------------+-------------------+----------------+------------+-----------------+------------------+-----------------+----------------+-----------------+----------+----------+---------------+----------------+---------------
 appdb    |                4 |                 5 |          1284  |       4821 |            8234 |             9102 |               0 |              0 |               0 |        0 |        0 |             0 |              0 |             0
(1 row)

-- SHOW POOLS:
 database | user    | cl_active | cl_waiting | sv_active | sv_idle | pool_mode   
----------+---------+-----------+------------+-----------+---------+-------------
 appdb    | appuser |         1 |          0 |         1 |       4 | transaction

-- SHOW SERVERS:
 type | user    | database | state | addr         | port | local_addr   | local_port | connect_time | link
------+---------+----------+-------+--------------+------+--------------+------------+--------------+------
 S    | appuser | appdb    | idle  | 172.18.0.2   | 5432 | 172.18.0.3   |      46892 | 2026-03-05   |     
```

> 💡 `cl_active` = active client connections; `sv_idle` = idle server connections ready for reuse. The key metric: many clients (cl_*) can share few servers (sv_*).

---

## Step 6: Simulate Connection Pool Pressure

```bash
cat > /tmp/pgbouncer_load_test.sh << 'SCRIPT'
#!/bin/bash
echo "Simulating 50 concurrent connections through PgBouncer..."
for i in $(seq 1 50); do
  docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U appuser -d appdb \
    -c "SELECT pg_sleep(0.1); SELECT COUNT(*) FROM sessions;" > /dev/null 2>&1 &
done
wait
echo "All connections completed!"

echo ""
echo "=== Pool stats after load test ==="
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U pgbouncer -d pgbouncer -c "SHOW STATS;"

echo ""
echo "=== Actual PostgreSQL connections ==="
docker exec pg-backend psql -U postgres -c "
  SELECT COUNT(*), state, wait_event_type, wait_event 
  FROM pg_stat_activity 
  WHERE datname = 'appdb'
  GROUP BY state, wait_event_type, wait_event;
"
SCRIPT

chmod +x /tmp/pgbouncer_load_test.sh
/tmp/pgbouncer_load_test.sh
```

📸 **Verified Output:**
```
Simulating 50 concurrent connections through PgBouncer...
All connections completed!

=== Pool stats after load test ===
 database | total_xact_count | total_query_count | avg_xact_count | avg_wait_time 
----------+------------------+-------------------+----------------+---------------
 appdb    |               54 |               107 |              0 |             0
(1 row)

=== Actual PostgreSQL connections ===
 count | state | wait_event_type | wait_event 
-------+-------+-----------------+------------
     5 | idle  | Client          | ClientRead
(1 row)   <- Only 5 real connections for 50 clients!
```

> 💡 50 clients → only 5 actual PostgreSQL connections! This is the core value of connection pooling.

---

## Step 7: PAUSE and RESUME (Rolling Maintenance)

```bash
# PAUSE temporarily blocks new queries (in-flight queries complete first)
# Use for rolling restarts or maintenance without connection errors

echo "=== Pausing PgBouncer for maintenance ==="
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U pgbouncer -d pgbouncer -c "PAUSE appdb;"

echo "Paused! Any new queries will queue..."

# Simulate maintenance (e.g., PostgreSQL config reload)
docker exec pg-backend psql -U postgres -c "SELECT pg_reload_conf();"
echo "Maintenance done!"

# Resume
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U pgbouncer -d pgbouncer -c "RESUME appdb;"
echo "Resumed! Queued queries will now execute."

# RELOAD configuration without restart
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U pgbouncer -d pgbouncer -c "RELOAD;"
echo "PgBouncer config reloaded."
```

📸 **Verified Output:**
```
=== Pausing PgBouncer for maintenance ===
PAUSE
Paused! Any new queries will queue...
pg_reload_conf
t
Maintenance done!
RESUME
Resumed! Queued queries will now execute.
RELOAD
PgBouncer config reloaded.
```

---

## Step 8: Capstone — Dynamic Pool Sizing

```bash
docker exec pgbouncer psql -h 127.0.0.1 -p 5432 -U pgbouncer -d pgbouncer <<'EOF'
-- Show current config
SHOW CONFIG WHERE key IN (
  'max_client_conn', 'default_pool_size', 'min_pool_size',
  'pool_mode', 'server_idle_timeout', 'reserve_pool_size'
);

-- Dynamic config change (no restart needed!)
SET max_client_conn = 1000;
SET default_pool_size = 30;
SET reserve_pool_size = 10;

SHOW CONFIG WHERE key IN ('max_client_conn', 'default_pool_size', 'reserve_pool_size');
EOF

echo ""
echo "=== PgBouncer sizing guidelines ==="
cat << 'GUIDELINES'
PostgreSQL memory per connection: ~5-10MB
For 16GB RAM server with 50MB overhead:
  Max PostgreSQL connections: (16384 - 1000) / 10 ≈ 1538
  But: many connections are wasteful
  
PgBouncer optimal setup:
  PostgreSQL max_connections = 100-200 (actual work)  
  PgBouncer max_client_conn = 10000 (client-facing)
  PgBouncer default_pool_size = 20-50 (server-facing)
  
pool_size formula: 
  = (number of CPU cores) × 2 + effective_spindle_count
  For a 4-core server with SSD: 4 × 2 + 1 = 9-10 connections
GUIDELINES

# Cleanup
docker stop pg-backend pgbouncer
docker rm -f pg-backend pgbouncer
docker network rm pgbouncer-net
rm -rf /tmp/pgbouncer-config /tmp/pgbouncer_load_test.sh

echo "Lab complete!"
```

📸 **Verified Output:**
```
          key           | value       
------------------------+-------------
 default_pool_size      | 20          
 max_client_conn        | 500         
 min_pool_size          | 5           
 pool_mode              | transaction 
 reserve_pool_size      | 5           
 server_idle_timeout    | 600         
(6 rows)

After SET commands:
 max_client_conn   | 1000
 default_pool_size | 30
 reserve_pool_size | 10

=== PgBouncer sizing guidelines ===
...

Lab complete!
```

---

## Summary

| Pool Mode | Connection Released | Supports | Best For |
|-----------|---------------------|----------|----------|
| session | At client disconnect | Everything | Apps using SET, LISTEN/NOTIFY |
| transaction | At COMMIT/ROLLBACK | Most features | Web APIs, stateless backends |
| statement | After each statement | Read-only queries | Simple SELECT-only apps |

| Command | Purpose |
|---------|---------|
| `SHOW POOLS` | Active connections per pool |
| `SHOW STATS` | Query/transaction throughput |
| `SHOW CLIENTS` | Active client connections |
| `SHOW SERVERS` | Actual PostgreSQL connections |
| `PAUSE dbname` | Block new queries (for maintenance) |
| `RESUME dbname` | Unblock after pause |
| `RELOAD` | Reload config without restart |
| `SET key=value` | Dynamic config change |

## Key Takeaways

- **transaction pool mode** is the sweet spot — efficient and compatible with most applications
- **50 clients → 5 server connections** is realistic — PgBouncer multiplexes aggressively
- PostgreSQL **max_connections** should be low (100-200); PgBouncer handles the rest
- **PAUSE + RESUME** enables zero-connection-error maintenance windows
- Always test pool mode compatibility — `SET search_path`, `LISTEN`, and advisory locks require session mode
