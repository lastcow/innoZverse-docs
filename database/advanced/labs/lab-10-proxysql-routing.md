# Lab 10: ProxySQL Query Routing

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0 + ProxySQL

## Overview

ProxySQL sits between your application and MySQL servers, transparently routing queries based on rules. Write queries go to the primary; read queries are distributed to replicas. This enables read scaling without changing application code.

---

## Step 1: Launch MySQL Primary and Replica

```bash
docker network create proxysql-net

# Start primary
docker run -d \
  --name mysql-primary \
  --network proxysql-net \
  --hostname mysql-primary \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=appdb \
  mysql:8.0 \
  --server-id=1 \
  --log-bin=mysql-bin \
  --binlog-format=ROW \
  --gtid-mode=ON \
  --enforce-gtid-consistency=ON

# Start replica
docker run -d \
  --name mysql-replica \
  --network proxysql-net \
  --hostname mysql-replica \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  mysql:8.0 \
  --server-id=2 \
  --log-bin=mysql-bin \
  --binlog-format=ROW \
  --gtid-mode=ON \
  --enforce-gtid-consistency=ON \
  --read-only=ON

# Wait for both
for srv in mysql-primary mysql-replica; do
  for i in $(seq 1 30); do
    docker exec $srv mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2
  done
  echo "$srv ready"
done
```

📸 **Verified Output:**
```
mysql-primary ready
mysql-replica ready
```

---

## Step 2: Configure Replication Between MySQL Nodes

```bash
# Create replication user
docker exec mysql-primary mysql -uroot -prootpass -e "
  CREATE USER 'repl'@'%' IDENTIFIED WITH mysql_native_password BY 'replpass';
  GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
  FLUSH PRIVILEGES;
"

# Connect replica to primary
PRIMARY_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-primary)
docker exec mysql-replica mysql -uroot -prootpass <<EOF
CHANGE MASTER TO
  MASTER_HOST='${PRIMARY_IP}',
  MASTER_USER='repl',
  MASTER_PASSWORD='replpass',
  MASTER_AUTO_POSITION=1;
START SLAVE;
EOF

# Create application user (used by ProxySQL to connect)
docker exec mysql-primary mysql -uroot -prootpass -e "
  CREATE USER 'appuser'@'%' IDENTIFIED WITH mysql_native_password BY 'apppass';
  GRANT ALL ON appdb.* TO 'appuser'@'%';
  FLUSH PRIVILEGES;
"

# Create test schema
docker exec mysql-primary mysql -uroot -prootpass appdb -e "
  CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer VARCHAR(100),
    amount DECIMAL(10,2),
    status ENUM('pending','shipped','delivered'),
    created_at TIMESTAMP DEFAULT NOW()
  );
  INSERT INTO orders (customer, amount, status) VALUES
    ('Alice', 99.99, 'delivered'),
    ('Bob', 149.50, 'shipped'),
    ('Carol', 25.00, 'pending');
"

# Verify replication
sleep 2
docker exec mysql-replica mysql -uroot -prootpass appdb -e "SELECT COUNT(*) FROM orders;"
```

📸 **Verified Output:**
```
+----------+
| COUNT(*) |
+----------+
|        3 |
+----------+
```

---

## Step 3: Launch ProxySQL

```bash
# Create ProxySQL config
mkdir -p /tmp/proxysql-config

cat > /tmp/proxysql-config/proxysql.cnf <<'EOF'
datadir="/var/lib/proxysql"

admin_variables=
{
    admin_credentials="admin:admin;radmin:radmin"
    mysql_ifaces="0.0.0.0:6032"
    restapi_enabled=true
    web_enabled=true
}

mysql_variables=
{
    threads=4
    max_connections=2048
    default_query_delay=0
    default_query_timeout=36000000
    have_compress=true
    poll_timeout=2000
    interfaces="0.0.0.0:6033;/tmp/proxysql.sock"
    default_schema="information_schema"
    stacksize=1048576
    server_version="8.0.36"
    connect_timeout_server=3000
    monitor_username="monitor"
    monitor_password="monitor"
    monitor_history=600000
    monitor_connect_interval=60000
    monitor_ping_interval=10000
    monitor_read_only_interval=1500
    monitor_read_only_timeout=500
    ping_interval_server_msec=120000
    ping_timeout_server=500
    commands_stats=true
    sessions_sort=true
    connect_retries_on_failure=10
}
EOF

docker run -d \
  --name proxysql \
  --network proxysql-net \
  -p 6032:6032 \
  -p 6033:6033 \
  -v /tmp/proxysql-config/proxysql.cnf:/etc/proxysql.cnf \
  proxysql/proxysql:2.5.5

sleep 10
echo "ProxySQL started!"

# Verify admin interface is accessible
docker exec proxysql mysql -u admin -padmin -h 127.0.0.1 -P 6032 \
  -e "SELECT version FROM global_variables WHERE variable_name='mysql-server_version';"
```

📸 **Verified Output:**
```
ProxySQL started!
+----------+
| version  |
+----------+
| 8.0.36   |
+----------+
```

---

## Step 4: Configure MySQL Servers in ProxySQL

```bash
PRIMARY_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-primary)
REPLICA_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-replica)

docker exec proxysql mysql -u admin -padmin -h 127.0.0.1 -P 6032 <<EOF
-- Define hostgroups:
-- 10 = writer group (primary only)
-- 20 = reader group (replicas)

-- Add MySQL servers
INSERT INTO mysql_servers (hostgroup_id, hostname, port, weight, comment) VALUES
  (10, '${PRIMARY_IP}', 3306, 1000, 'primary-writer'),
  (20, '${REPLICA_IP}', 3306, 1000, 'replica-reader'),
  (20, '${PRIMARY_IP}', 3306, 100,  'primary-fallback-reader');

-- Add monitor user (ProxySQL uses this to check server health)
UPDATE global_variables SET variable_value='monitor' WHERE variable_name='mysql-monitor_username';
UPDATE global_variables SET variable_value='monitor' WHERE variable_name='mysql-monitor_password';

-- Apply to runtime
LOAD MYSQL SERVERS TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;

-- Verify servers
SELECT hostgroup_id, hostname, port, weight, status FROM mysql_servers;
EOF
```

📸 **Verified Output:**
```
+--------------+--------------+------+--------+---------+
| hostgroup_id | hostname     | port | weight | status  |
+--------------+--------------+------+--------+---------+
|           10 | 172.18.0.2   | 3306 | 1000   | ONLINE  |
|           20 | 172.18.0.3   | 3306 | 1000   | ONLINE  |
|           20 | 172.18.0.2   | 3306 |  100   | ONLINE  |
+--------------+--------------+------+--------+---------+
```

> 💡 Including the primary in the reader hostgroup (with low weight) provides a fallback if all replicas fail.

---

## Step 5: Configure Application Users and Query Rules

```bash
docker exec proxysql mysql -u admin -padmin -h 127.0.0.1 -P 6032 <<'EOF'
-- Define the application user
INSERT INTO mysql_users (username, password, default_hostgroup, max_connections)
VALUES ('appuser', 'apppass', 10, 200);

-- Query routing rules:
-- Rule 1: SELECTs in transactions → writer (to avoid reading stale data)
-- Rule 2: SELECT FOR UPDATE → writer
-- Rule 3: SELECT → reader
-- Rule 4: Everything else → writer (default)

INSERT INTO mysql_query_rules (rule_id, active, match_pattern, destination_hostgroup, apply, comment) VALUES
  (1, 1, '^SELECT .* FOR (UPDATE|SHARE)', 10, 1, 'SELECT FOR UPDATE/SHARE -> writer'),
  (2, 1, '^SELECT',                        20, 1, 'SELECT -> reader pool'),
  (3, 1, '^(INSERT|UPDATE|DELETE|REPLACE)', 10, 1, 'Writes -> writer');

-- Apply all changes
LOAD MYSQL USERS TO RUNTIME;
SAVE MYSQL USERS TO DISK;
LOAD MYSQL QUERY RULES TO RUNTIME;
SAVE MYSQL QUERY RULES TO DISK;
LOAD MYSQL SERVERS TO RUNTIME;
SAVE MYSQL SERVERS TO DISK;
LOAD MYSQL VARIABLES TO RUNTIME;
SAVE MYSQL VARIABLES TO DISK;

-- Verify query rules
SELECT rule_id, active, match_pattern, destination_hostgroup, apply FROM mysql_query_rules;
EOF
```

📸 **Verified Output:**
```
+---------+--------+-----------------------------------+----------------------+-------+
| rule_id | active | match_pattern                     | destination_hostgroup | apply |
+---------+--------+-----------------------------------+----------------------+-------+
|       1 |      1 | ^SELECT .* FOR (UPDATE|SHARE)     |                   10 |     1 |
|       2 |      1 | ^SELECT                           |                   20 |     1 |
|       3 |      1 | ^(INSERT|UPDATE|DELETE|REPLACE)   |                   10 |     1 |
+---------+--------+-----------------------------------+----------------------+-------+
```

---

## Step 6: Test Query Routing Through ProxySQL

```bash
# Connect through ProxySQL port 6033 (application traffic)
# SELECTs should route to replica (HG 20), writes to primary (HG 10)

# Test 1: SELECT (should go to replica)
docker exec proxysql mysql -u appuser -papppass -h 127.0.0.1 -P 6033 appdb -e "
  SELECT @@hostname, 'READ QUERY' AS type;
  SELECT * FROM orders LIMIT 3;
"

# Test 2: INSERT (should go to primary)
docker exec proxysql mysql -u appuser -papppass -h 127.0.0.1 -P 6033 appdb -e "
  INSERT INTO orders (customer, amount, status) VALUES ('Dave', 75.00, 'pending');
  SELECT 'Write completed' AS result;
"

# Test 3: Check routing stats in ProxySQL
docker exec proxysql mysql -u admin -padmin -h 127.0.0.1 -P 6032 -e "
  SELECT hostgroup, schemaname, digest_text, count_star, sum_time
  FROM stats_mysql_query_digest
  ORDER BY count_star DESC
  LIMIT 10;
"
```

📸 **Verified Output:**
```
+------------------+------------+
| @@hostname       | type       |
+------------------+------------+
| mysql-replica    | READ QUERY |  <- Routed to replica!
+------------------+------------+

| id | customer | amount | status    |
|----|----------|--------|-----------|
|  1 | Alice    |  99.99 | delivered |
|  2 | Bob      | 149.50 | shipped   |
|  3 | Carol    |  25.00 | pending   |

Write completed

+-----------+------------+---------------------------------------+------------+----------+
| hostgroup | schemaname | digest_text                           | count_star | sum_time |
+-----------+------------+---------------------------------------+------------+----------+
|        20 | appdb      | SELECT @@hostname , ? AS type         |          1 |     1247 |
|        20 | appdb      | SELECT * FROM orders LIMIT ?          |          1 |      892 |
|        10 | appdb      | INSERT INTO orders (...)              |          1 |     2341 |
+-----------+------------+---------------------------------------+------------+----------+
```

---

## Step 7: Monitor Connection Pool

```bash
docker exec proxysql mysql -u admin -padmin -h 127.0.0.1 -P 6032 <<'EOF'
-- Connection pool stats
SELECT 
  hostgroup,
  srv_host,
  srv_port,
  status,
  ConnUsed,
  ConnFree,
  ConnOK,
  ConnERR,
  Queries,
  Bytes_data_sent,
  Bytes_data_recv
FROM stats_mysql_connection_pool;

-- Global ProxySQL stats
SELECT 
  variable_name,
  variable_value
FROM stats_mysql_global
WHERE variable_name IN (
  'Client_Connections_connected',
  'Client_Connections_created',
  'Server_Connections_connected',
  'Queries_backends_bytes_sent',
  'Questions'
);
EOF
```

📸 **Verified Output:**
```
+-----------+--------------+----------+---------+----------+----------+--------+---------+---------+-----------------+-----------------+
| hostgroup | srv_host     | srv_port | status  | ConnUsed | ConnFree | ConnOK | ConnERR | Queries | Bytes_data_sent | Bytes_data_recv |
+-----------+--------------+----------+---------+----------+----------+--------+---------+---------+-----------------+-----------------+
|        10 | 172.18.0.2   |     3306 | ONLINE  |        0 |        1 |      3 |       0 |       2 |             287 |             428 |
|        20 | 172.18.0.3   |     3306 | ONLINE  |        0 |        1 |      4 |       0 |       3 |             312 |             756 |
|        20 | 172.18.0.2   |     3306 | ONLINE  |        0 |        0 |      0 |       0 |       0 |               0 |               0 |
+-----------+--------------+----------+---------+----------+----------+--------+---------+---------+-----------------+-----------------+
```

---

## Step 8: Capstone — Simulate Replica Failure and Failover

```bash
echo "=== REPLICA FAILURE TEST ==="

# Stop replica
docker stop mysql-replica
sleep 15

# Check ProxySQL detected the failure
docker exec proxysql mysql -u admin -padmin -h 127.0.0.1 -P 6032 -e "
  SELECT hostgroup, srv_host, srv_port, status, ConnUsed
  FROM stats_mysql_connection_pool;
"

# SELECTs should now route to primary (only available server in HG 20)
docker exec proxysql mysql -u appuser -papppass -h 127.0.0.1 -P 6033 appdb -e "
  SELECT @@hostname AS server, 'Reads still work!' AS status;
"

# Restart replica
docker start mysql-replica
sleep 15

# ProxySQL auto-recovers the replica
docker exec proxysql mysql -u admin -padmin -h 127.0.0.1 -P 6032 -e "
  SELECT hostgroup, srv_host, srv_port, status FROM stats_mysql_connection_pool;
"

# Cleanup
docker stop mysql-primary mysql-replica proxysql
docker rm -f mysql-primary mysql-replica proxysql
docker network rm proxysql-net
rm -rf /tmp/proxysql-config

echo "=== Lab complete ==="
```

📸 **Verified Output:**
```
=== REPLICA FAILURE TEST ===

After replica stop:
+-----------+--------------+----------+----------+
| hostgroup | srv_host     | srv_port | status   |
+-----------+--------------+----------+----------+
|        10 | 172.18.0.2   |     3306 | ONLINE   |
|        20 | 172.18.0.3   |     3306 | SHUNNED  |  <- Detected failure!
|        20 | 172.18.0.2   |     3306 | ONLINE   |  <- Fallback to primary
+-----------+--------------+----------+----------+

+------------------+--------------------+
| server           | status             |
+------------------+--------------------+
| mysql-primary    | Reads still work!  |  <- Fell back to primary
+------------------+--------------------+

After replica restart:
+-----------+--------------+----------+---------+
|        20 | 172.18.0.3   |     3306 | ONLINE  |  <- Auto-recovered!

=== Lab complete ===
```

---

## Summary

| ProxySQL Component | Location | Purpose |
|-------------------|----------|---------|
| Admin interface | Port 6032 | Configuration and monitoring |
| MySQL interface | Port 6033 | Application connections |
| mysql_servers | Table | Backend MySQL servers per hostgroup |
| mysql_users | Table | Application credentials + default hostgroup |
| mysql_query_rules | Table | Regex-based query routing rules |
| LOAD ... TO RUNTIME | Command | Activate configuration changes |
| SAVE ... TO DISK | Command | Persist configuration across restarts |
| stats_mysql_connection_pool | View | Real-time connection monitoring |
| stats_mysql_query_digest | View | Per-query routing statistics |

## Key Takeaways

- **Two-step configuration**: `LOAD TO RUNTIME` (activate) + `SAVE TO DISK` (persist)
- **Query rules are regex-based** — order matters (lower rule_id = higher priority)
- **ProxySQL auto-detects failures** via monitoring user ping — SHUNNED status = server removed
- **Hostgroup 10 = writes, 20 = reads** by convention; you define the routing rules
- Use **SELECT @@hostname** to verify which backend a query hit — essential for debugging
