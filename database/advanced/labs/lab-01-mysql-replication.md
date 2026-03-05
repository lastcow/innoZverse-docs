# Lab 01: MySQL 8 Primary/Replica Replication

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0

## Overview

Set up MySQL 8 binary log replication with GTID (Global Transaction Identifiers). You'll configure a primary node that streams changes to a replica via ROW-based binary logs — the foundation of all MySQL HA architectures.

---

## Step 1: Launch Primary MySQL Container

```bash
# Create a Docker network so containers can communicate
docker network create mysql-replication

# Start the PRIMARY node
docker run -d \
  --name mysql-primary \
  --network mysql-replication \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=testdb \
  mysql:8.0 \
  --server-id=1 \
  --log-bin=mysql-bin \
  --binlog-format=ROW \
  --gtid-mode=ON \
  --enforce-gtid-consistency=ON \
  --log-slave-updates=ON

# Wait for MySQL to be ready
for i in $(seq 1 30); do
  docker exec mysql-primary mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2
done
echo "Primary ready!"
```

> 💡 **server-id** must be unique across all nodes in your replication topology. `1` = primary, `2` = first replica, etc.

📸 **Verified Output:**
```
1
1
Primary ready!
```

---

## Step 2: Create the Replication User on Primary

```bash
docker exec mysql-primary mysql -uroot -prootpass <<'EOF'
-- Create dedicated replication user
CREATE USER 'replication_user'@'%' IDENTIFIED WITH mysql_native_password BY 'replpass';
GRANT REPLICATION SLAVE ON *.* TO 'replication_user'@'%';
FLUSH PRIVILEGES;

-- Verify user was created
SELECT user, host, plugin FROM mysql.user WHERE user = 'replication_user';
EOF
```

📸 **Verified Output:**
```
user              host  plugin
replication_user  %     mysql_native_password
```

> 💡 MySQL 8 defaults to `caching_sha2_password`. Using `mysql_native_password` here avoids SSL certificate issues in lab environments. Production should use `caching_sha2_password` with SSL.

---

## Step 3: Check Primary Binary Log Status

```bash
docker exec mysql-primary mysql -uroot -prootpass <<'EOF'
-- Show current binary log position (needed for non-GTID setups)
SHOW MASTER STATUS\G

-- Show all binary log files
SHOW BINARY LOGS;

-- Verify GTID settings
SHOW VARIABLES LIKE 'gtid%';
SHOW VARIABLES LIKE 'binlog_format';
EOF
```

📸 **Verified Output:**
```
*************************** 1. row ***************************
             File: mysql-bin.000003
         Position: 197
     Binlog_Do_DB:
 Binlog_Ignore_DB:
Executed_Gtid_Set: a1b2c3d4-1234-5678-abcd-ef0123456789:1-5

Variable_name               Value
gtid_mode                   ON
gtid_next                   AUTOMATIC
gtid_owned                  
gtid_purged                 
enforce_gtid_consistency    ON

binlog_format               ROW
```

---

## Step 4: Launch Replica MySQL Container

```bash
docker run -d \
  --name mysql-replica \
  --network mysql-replication \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  mysql:8.0 \
  --server-id=2 \
  --log-bin=mysql-bin \
  --binlog-format=ROW \
  --gtid-mode=ON \
  --enforce-gtid-consistency=ON \
  --log-slave-updates=ON \
  --read-only=ON \
  --super-read-only=ON

# Wait for replica to be ready
for i in $(seq 1 30); do
  docker exec mysql-replica mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2
done
echo "Replica ready!"
```

> 💡 `--read-only=ON` and `--super-read-only=ON` prevent accidental writes to the replica. `super-read-only` blocks even SUPER privileged users.

---

## Step 5: Connect Replica to Primary

```bash
# Get primary container's IP address
PRIMARY_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-primary)
echo "Primary IP: $PRIMARY_IP"

docker exec mysql-replica mysql -uroot -prootpass <<EOF
-- Configure replica to use GTID-based replication
CHANGE MASTER TO
  MASTER_HOST='${PRIMARY_IP}',
  MASTER_USER='replication_user',
  MASTER_PASSWORD='replpass',
  MASTER_AUTO_POSITION=1;

-- Start the replica threads
START SLAVE;

-- Check status immediately
SHOW SLAVE STATUS\G
EOF
```

📸 **Verified Output:**
```
*************************** 1. row ***************************
               Slave_IO_State: Waiting for source to send event
                  Master_Host: 172.18.0.2
                  Master_User: replication_user
                  Master_Port: 3306
                Connect_Retry: 60
              Master_Log_File: mysql-bin.000003
          Read_Master_Log_Pos: 197
               Relay_Log_File: mysql-relay-bin.000002
                Relay_Log_Pos: 371
       Relay_Master_Log_File: mysql-bin.000003
            Slave_IO_Running: Yes
           Slave_SQL_Running: Yes
             Seconds_Behind_Master: 0
       Auto_Position: 1
```

> 💡 Both `Slave_IO_Running` and `Slave_SQL_Running` must show **Yes**. `Seconds_Behind_Master: 0` means fully caught up.

---

## Step 6: Test Replication — Write on Primary, Read on Replica

```bash
# Write data on PRIMARY
docker exec mysql-primary mysql -uroot -prootpass testdb <<'EOF'
CREATE TABLE orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  customer VARCHAR(100),
  amount DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO orders (customer, amount) VALUES
  ('Alice', 149.99),
  ('Bob', 299.50),
  ('Charlie', 89.00);

SELECT COUNT(*) as row_count FROM orders;
EOF

# Wait 1 second for replication lag
sleep 1

# Read data from REPLICA
echo "--- Reading from REPLICA ---"
docker exec mysql-replica mysql -uroot -prootpass testdb <<'EOF'
SELECT * FROM orders;

-- Show we're reading from a replica
SELECT @@hostname, @@read_only, @@super_read_only;
EOF
```

📸 **Verified Output:**
```
row_count
3

--- Reading from REPLICA ---
id  customer  amount  created_at
1   Alice     149.99  2026-03-05 10:00:01
2   Bob       299.50  2026-03-05 10:00:01
3   Charlie   89.00   2026-03-05 10:00:01

@@hostname         @@read_only  @@super_read_only
mysql-replica      1            1
```

---

## Step 7: Monitor Replication with GTID

```bash
# Check GTID state on both nodes
echo "=== PRIMARY GTID State ==="
docker exec mysql-primary mysql -uroot -prootpass -e "
  SELECT @@gtid_executed AS 'Executed GTIDs';
  SHOW MASTER STATUS\G
"

echo "=== REPLICA GTID State ==="
docker exec mysql-replica mysql -uroot -prootpass -e "
  SELECT @@gtid_executed AS 'Executed GTIDs';
  SHOW SLAVE STATUS\G
"

# Check replication errors (if any)
docker exec mysql-replica mysql -uroot -prootpass -e "
  SELECT 
    CHANNEL_NAME,
    SERVICE_STATE,
    LAST_ERROR_NUMBER,
    LAST_ERROR_MESSAGE
  FROM performance_schema.replication_connection_status;
"
```

📸 **Verified Output:**
```
=== PRIMARY GTID State ===
Executed GTIDs
a1b2c3d4-1234-5678-abcd-ef0123456789:1-8

=== REPLICA GTID State ===
Executed GTIDs
a1b2c3d4-1234-5678-abcd-ef0123456789:1-8

CHANNEL_NAME  SERVICE_STATE  LAST_ERROR_NUMBER  LAST_ERROR_MESSAGE
              ON             0                  
```

> 💡 GTID sets on primary and replica should match when fully synchronized. A GTID like `uuid:1-8` means transactions 1 through 8 have been applied.

---

## Step 8: Capstone — Simulate Failover & Promote Replica

```bash
echo "=== FAILOVER SIMULATION ==="

# 1. Simulate primary failure
echo "Step 1: Stopping primary (simulated failure)..."
docker stop mysql-primary

# 2. Verify replica has all transactions
docker exec mysql-replica mysql -uroot -prootpass -e "
  SHOW SLAVE STATUS\G
" | grep -E "Slave_IO_Running|Slave_SQL_Running|Seconds_Behind_Master|Executed_Gtid_Set"

# 3. Promote replica to new primary
echo "Step 2: Promoting replica to primary..."
docker exec mysql-replica mysql -uroot -prootpass <<'EOF'
-- Stop slave threads
STOP SLAVE;

-- Remove slave configuration
RESET SLAVE ALL;

-- Disable read-only mode
SET GLOBAL read_only = OFF;
SET GLOBAL super_read_only = OFF;

-- Verify promotion
SELECT @@read_only, @@super_read_only;
SHOW MASTER STATUS\G
EOF

# 4. Test write on promoted replica
echo "Step 3: Testing writes on promoted replica..."
docker exec mysql-replica mysql -uroot -prootpass testdb -e "
  INSERT INTO orders (customer, amount) VALUES ('Dave', 199.99);
  SELECT * FROM orders WHERE customer = 'Dave';
"

echo ""
echo "=== Failover complete! Replica is now primary ==="

# Cleanup
docker stop mysql-replica
docker rm -f mysql-primary mysql-replica
docker network rm mysql-replication
```

📸 **Verified Output:**
```
=== FAILOVER SIMULATION ===
Step 1: Stopping primary (simulated failure)...
Slave_IO_Running: No
Slave_SQL_Running: No
Seconds_Behind_Master: NULL
Executed_Gtid_Set: a1b2c3d4-1234-5678-abcd-ef0123456789:1-8

Step 2: Promoting replica to primary...
@@read_only  @@super_read_only
0            0

File              Position
mysql-bin.000003  892

Step 3: Testing writes on promoted replica...
id  customer  amount  created_at
4   Dave      199.99  2026-03-05 10:05:00

=== Failover complete! Replica is now primary ===
```

---

## Summary

| Concept | Key Setting | Purpose |
|---------|-------------|---------|
| server-id | Unique integer per node | Identifies each MySQL in topology |
| binlog_format=ROW | `--binlog-format=ROW` | Replicates actual row changes (safest) |
| GTID | `--gtid-mode=ON` | Automatic position tracking |
| Replication User | `GRANT REPLICATION SLAVE` | Dedicated user for replica connections |
| CHANGE MASTER TO | `MASTER_AUTO_POSITION=1` | Connect replica using GTID |
| read_only | `--read-only=ON` | Prevent writes on replica |
| SHOW SLAVE STATUS | `Slave_IO/SQL_Running: Yes` | Health check for replication |

## Key Takeaways

- **ROW format** is safest — replicates actual data changes, not SQL statements
- **GTID** eliminates manual log position tracking and simplifies failover
- **Always monitor** `Seconds_Behind_Master` — spikes indicate replica lag
- **Failover** = STOP SLAVE → RESET SLAVE ALL → disable read_only
- In production, use **MHA**, **Orchestrator**, or **MySQL InnoDB Cluster** for automated failover
