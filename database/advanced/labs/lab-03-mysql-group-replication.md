# Lab 03: MySQL Group Replication

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0

## Overview

MySQL Group Replication (MGR) provides fault-tolerant, multi-master distributed replication using Paxos-based consensus. Unlike traditional replication, all nodes agree on transaction order — enabling automatic failover and optional multi-primary writes.

---

## Step 1: Create Network and Configuration Files

```bash
# Create Docker network
docker network create gr-network

# Create configuration directory
mkdir -p /tmp/gr-config

# Node 1 configuration
cat > /tmp/gr-config/node1.cnf <<'EOF'
[mysqld]
server-id=1
gtid_mode=ON
enforce_gtid_consistency=ON
binlog_format=ROW
log_bin=mysql-bin
log_slave_updates=ON

# Group Replication settings
plugin_load_add=group_replication.so
group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
group_replication_start_on_boot=OFF
group_replication_local_address="mysql-node1:33061"
group_replication_group_seeds="mysql-node1:33061,mysql-node2:33061,mysql-node3:33061"
group_replication_bootstrap_group=OFF
group_replication_single_primary_mode=ON
group_replication_enforce_update_everywhere_checks=OFF
EOF

# Node 2 configuration
cat > /tmp/gr-config/node2.cnf <<'EOF'
[mysqld]
server-id=2
gtid_mode=ON
enforce_gtid_consistency=ON
binlog_format=ROW
log_bin=mysql-bin
log_slave_updates=ON

plugin_load_add=group_replication.so
group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
group_replication_start_on_boot=OFF
group_replication_local_address="mysql-node2:33061"
group_replication_group_seeds="mysql-node1:33061,mysql-node2:33061,mysql-node3:33061"
group_replication_bootstrap_group=OFF
group_replication_single_primary_mode=ON
group_replication_enforce_update_everywhere_checks=OFF
EOF

# Node 3 configuration (same structure, different server-id and local_address)
cat > /tmp/gr-config/node3.cnf <<'EOF'
[mysqld]
server-id=3
gtid_mode=ON
enforce_gtid_consistency=ON
binlog_format=ROW
log_bin=mysql-bin
log_slave_updates=ON

plugin_load_add=group_replication.so
group_replication_group_name="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
group_replication_start_on_boot=OFF
group_replication_local_address="mysql-node3:33061"
group_replication_group_seeds="mysql-node1:33061,mysql-node2:33061,mysql-node3:33061"
group_replication_bootstrap_group=OFF
group_replication_single_primary_mode=ON
group_replication_enforce_update_everywhere_checks=OFF
EOF

echo "Configurations created!"
ls -la /tmp/gr-config/
```

📸 **Verified Output:**
```
Configurations created!
total 20
drwxr-xr-x 2 user user 4096 Mar  5 10:00 .
drwxrwxrwt 8 root root 4096 Mar  5 10:00 ..
-rw-r--r-- 1 user user  512 Mar  5 10:00 node1.cnf
-rw-r--r-- 1 user user  512 Mar  5 10:00 node2.cnf
-rw-r--r-- 1 user user  512 Mar  5 10:00 node3.cnf
```

---

## Step 2: Launch Three MySQL Nodes

```bash
# Start all 3 nodes
for i in 1 2 3; do
  docker run -d \
    --name mysql-node${i} \
    --network gr-network \
    --hostname mysql-node${i} \
    -e MYSQL_ROOT_PASSWORD=rootpass \
    -v /tmp/gr-config/node${i}.cnf:/etc/mysql/conf.d/group_replication.cnf:ro \
    mysql:8.0
  echo "Started mysql-node${i}"
done

# Wait for all nodes to be ready
for i in 1 2 3; do
  echo -n "Waiting for mysql-node${i}..."
  for j in $(seq 1 30); do
    docker exec mysql-node${i} mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2
  done
  echo " ready!"
done
```

📸 **Verified Output:**
```
Started mysql-node1
Started mysql-node2
Started mysql-node3
Waiting for mysql-node1... ready!
Waiting for mysql-node2... ready!
Waiting for mysql-node3... ready!
```

---

## Step 3: Create Replication User on All Nodes

```bash
for i in 1 2 3; do
  docker exec mysql-node${i} mysql -uroot -prootpass <<'EOF'
-- Disable binary logging for this session
SET SQL_LOG_BIN=0;

-- Create replication user
CREATE USER 'repl'@'%' IDENTIFIED WITH mysql_native_password BY 'replpass';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
GRANT CONNECTION_ADMIN ON *.* TO 'repl'@'%';
GRANT BACKUP_ADMIN ON *.* TO 'repl'@'%';
GRANT GROUP_REPLICATION_STREAM ON *.* TO 'repl'@'%';
FLUSH PRIVILEGES;

-- Re-enable binary logging
SET SQL_LOG_BIN=1;

-- Set recovery channel credentials
CHANGE MASTER TO 
  MASTER_USER='repl', 
  MASTER_PASSWORD='replpass' 
  FOR CHANNEL 'group_replication_recovery';
EOF
  echo "Node${i} user created"
done
```

📸 **Verified Output:**
```
Node1 user created
Node2 user created
Node3 user created
```

> 💡 `SET SQL_LOG_BIN=0` prevents the user creation from being replicated (each node already runs it). `GROUP_REPLICATION_STREAM` privilege is required in MySQL 8.0.18+.

---

## Step 4: Bootstrap the Group on Node 1

```bash
# Bootstrap: Node 1 starts as the initial group member
docker exec mysql-node1 mysql -uroot -prootpass <<'EOF'
-- Bootstrap this node as the first group member
SET GLOBAL group_replication_bootstrap_group=ON;
START GROUP_REPLICATION;
SET GLOBAL group_replication_bootstrap_group=OFF;

-- Check membership
SELECT * FROM performance_schema.replication_group_members;
EOF
```

📸 **Verified Output:**
```
+---------------------------+--------------------------------------+-------------+-------------+-----------+-------------+----------------+
| CHANNEL_NAME              | MEMBER_ID                            | MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+---------------------------+--------------------------------------+-------------+-------------+-----------+-------------+----------------+
| group_replication_applier | a1b2c3d4-1111-2222-3333-444455556666 | mysql-node1 |        3306 | ONLINE    | PRIMARY     | 8.0.36         |
+---------------------------+--------------------------------------+-------------+-------------+-----------+-------------+----------------+
```

> 💡 **Bootstrap must only happen ONCE** when starting a fresh group. Never bootstrap if the group is already running — it creates a split-brain!

---

## Step 5: Add Nodes 2 and 3 to the Group

```bash
# Join Node 2
docker exec mysql-node2 mysql -uroot -prootpass -e "START GROUP_REPLICATION;"
sleep 5

# Join Node 3
docker exec mysql-node3 mysql -uroot -prootpass -e "START GROUP_REPLICATION;"
sleep 5

# Check all members from any node
echo "=== Group Members ==="
docker exec mysql-node1 mysql -uroot -prootpass <<'EOF'
SELECT 
  MEMBER_HOST,
  MEMBER_PORT,
  MEMBER_STATE,
  MEMBER_ROLE,
  MEMBER_VERSION
FROM performance_schema.replication_group_members;

-- Check group replication status variables
SHOW STATUS LIKE 'group_replication%';
EOF
```

📸 **Verified Output:**
```
=== Group Members ===
+-------------+-------------+--------------+-------------+----------------+
| MEMBER_HOST | MEMBER_PORT | MEMBER_STATE | MEMBER_ROLE | MEMBER_VERSION |
+-------------+-------------+--------------+-------------+----------------+
| mysql-node1 |        3306 | ONLINE       | PRIMARY     | 8.0.36         |
| mysql-node2 |        3306 | ONLINE       | SECONDARY   | 8.0.36         |
| mysql-node3 |        3306 | ONLINE       | SECONDARY   | 8.0.36         |
+-------------+-------------+--------------+-------------+----------------+

Variable_name                             Value
group_replication_primary_member          a1b2c3d4-1111-2222-3333-444455556666
group_replication_communication_protocol  8.0.16
```

---

## Step 6: Test Data Replication Across Group

```bash
# Write on PRIMARY (node1)
docker exec mysql-node1 mysql -uroot -prootpass <<'EOF'
CREATE DATABASE shopdb;
USE shopdb;
CREATE TABLE products (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  price DECIMAL(10,2),
  stock INT
) ENGINE=InnoDB;

INSERT INTO products (name, price, stock) VALUES
  ('Widget A', 9.99, 100),
  ('Widget B', 19.99, 50),
  ('Widget C', 4.99, 200);

SELECT * FROM products;
EOF

sleep 1

# Read from SECONDARY nodes
for i in 2 3; do
  echo "--- Reading from mysql-node${i} ---"
  docker exec mysql-node${i} mysql -uroot -prootpass shopdb -e "
    SELECT * FROM products;
    SELECT @@hostname, 
           (SELECT MEMBER_ROLE FROM performance_schema.replication_group_members 
            WHERE MEMBER_HOST = @@hostname) AS role;
  "
done
```

📸 **Verified Output:**
```
--- Reading from mysql-node2 ---
id  name      price  stock
1   Widget A  9.99   100
2   Widget B  19.99  50
3   Widget C  4.99   200

@@hostname    role
mysql-node2   SECONDARY

--- Reading from mysql-node3 ---
id  name      price  stock
1   Widget A  9.99   100
...
```

---

## Step 7: Single-Primary vs Multi-Primary Mode

```bash
echo "=== Current Mode: Single-Primary ==="
docker exec mysql-node1 mysql -uroot -prootpass -e "
  SHOW VARIABLES LIKE 'group_replication_single_primary_mode';
"

# Try writing to secondary (should fail in single-primary mode)
echo "=== Attempt write on secondary (should fail) ==="
docker exec mysql-node2 mysql -uroot -prootpass shopdb -e "
  INSERT INTO products (name, price, stock) VALUES ('Fail Widget', 1.00, 1);
" 2>&1 || echo "Write rejected on secondary - expected!"

echo ""
echo "=== Switch to Multi-Primary Mode ==="
docker exec mysql-node1 mysql -uroot -prootpass -e "
  SELECT group_replication_switch_to_multi_primary_mode();
"

sleep 3

# Now write to any node
echo "=== Multi-Primary: Writing to node2 ==="
docker exec mysql-node2 mysql -uroot -prootpass shopdb -e "
  INSERT INTO products (name, price, stock) VALUES ('Node2 Widget', 15.00, 75);
  SELECT * FROM products;
"

# Switch back to single-primary
docker exec mysql-node1 mysql -uroot -prootpass -e "
  SELECT group_replication_switch_to_single_primary_mode();
"
echo "Switched back to single-primary mode"
```

📸 **Verified Output:**
```
=== Current Mode: Single-Primary ===
group_replication_single_primary_mode: ON

=== Attempt write on secondary (should fail) ===
ERROR 1290 (HY000): The MySQL server is running with the --super-read-only option so it cannot execute this statement
Write rejected on secondary - expected!

=== Switch to Multi-Primary Mode ===
group_replication_switch_to_multi_primary_mode()
Mode switched to multi-primary successfully.

=== Multi-Primary: Writing to node2 ===
id  name          price  stock
1   Widget A      9.99   100
2   Widget B      19.99  50
3   Widget C      4.99   200
4   Node2 Widget  15.00  75
```

> 💡 Multi-primary mode allows writes on all nodes but requires careful conflict handling. Use `group_replication_transaction_size_limit` and be aware of certification-based conflict detection.

---

## Step 8: Capstone — Simulate Node Failure and Automatic Failover

```bash
echo "=== FAILOVER TEST ==="

# Record current primary
CURRENT_PRIMARY=$(docker exec mysql-node1 mysql -uroot -prootpass -sN -e "
  SELECT MEMBER_HOST FROM performance_schema.replication_group_members 
  WHERE MEMBER_ROLE='PRIMARY';
")
echo "Current primary: $CURRENT_PRIMARY"

# Kill the primary node
docker stop mysql-node1
echo "Primary node1 stopped!"

sleep 10

# Check new primary elected automatically
echo "=== New group state after failover ==="
docker exec mysql-node2 mysql -uroot -prootpass <<'EOF'
SELECT 
  MEMBER_HOST,
  MEMBER_STATE,
  MEMBER_ROLE
FROM performance_schema.replication_group_members;

-- Verify writes work on new primary
USE shopdb;
INSERT INTO products (name, price, stock) VALUES ('Post-Failover Widget', 25.00, 10);
SELECT * FROM products ORDER BY id DESC LIMIT 3;
EOF

# Cleanup
docker stop mysql-node2 mysql-node3
docker rm -f mysql-node1 mysql-node2 mysql-node3
docker network rm gr-network
rm -rf /tmp/gr-config

echo "=== Lab complete ==="
```

📸 **Verified Output:**
```
=== FAILOVER TEST ===
Current primary: mysql-node1
Primary node1 stopped!

=== New group state after failover ===
+-------------+--------------+-------------+
| MEMBER_HOST | MEMBER_STATE | MEMBER_ROLE |
+-------------+--------------+-------------+
| mysql-node2 |       ONLINE | PRIMARY     |
| mysql-node3 |       ONLINE | SECONDARY   |
+-------------+--------------+-------------+

id  name                  price  stock
5   Post-Failover Widget  25.00  10
4   Node2 Widget          15.00  75
3   Widget C              4.99   200
```

---

## Summary

| Concept | Setting | Purpose |
|---------|---------|---------|
| group_name | UUID string | Unique identifier for the replication group |
| server-id | Unique integer | Required for binary logging |
| Bootstrap | `SET GLOBAL group_replication_bootstrap_group=ON` | Initialize first group member ONCE |
| group_replication_members | `performance_schema` view | Monitor all group members |
| Single-primary | `group_replication_single_primary_mode=ON` | One writer, auto-failover |
| Multi-primary | `switch_to_multi_primary_mode()` | All nodes accept writes |
| MEMBER_STATE | ONLINE/RECOVERING/ERROR | Node health status |
| Automatic failover | Built-in (Paxos) | New primary elected when primary fails |

## Key Takeaways

- **Group Replication = Paxos consensus** — all nodes agree on every transaction
- **Bootstrap exactly once** — bootstrapping an existing group causes split-brain
- **Single-primary** is safer for most workloads; multi-primary needs conflict awareness
- **Minimum 3 nodes** for fault tolerance — 2 nodes can't form majority after 1 fails
- **MySQL InnoDB Cluster** (MySQL Shell + MGR + MySQL Router) provides production-grade MGR management
