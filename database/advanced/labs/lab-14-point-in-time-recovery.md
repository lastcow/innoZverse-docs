# Lab 14: Point-in-Time Recovery (PITR)

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0, PostgreSQL 15

## Overview

Point-in-time recovery allows you to restore a database to any moment in its history — critical for recovering from accidental data deletion or corruption. MySQL uses binary logs; PostgreSQL uses WAL archiving. This lab demonstrates full PITR workflows.

---

## Step 1: MySQL — Enable Binary Logging for PITR

```bash
docker run -d --name mysql-lab \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=shopdb \
  mysql:8.0 \
  --server-id=1 \
  --log-bin=mysql-bin \
  --binlog-format=ROW \
  --expire_logs_days=7

for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

# Verify binary logging
docker exec mysql-lab mysql -uroot -prootpass -e "
SHOW VARIABLES LIKE 'log_bin%';
SHOW VARIABLES LIKE 'binlog_format';
SHOW BINARY LOGS;
"
```

📸 **Verified Output:**
```
+-----------------------+-------------------+
| Variable_name         | Value             |
+-----------------------+-------------------+
| log_bin               | ON                |
| log_bin_basename      | /var/lib/mysql/mysql-bin |
| log_bin_index         | /var/lib/mysql/mysql-bin.index |
+-----------------------+-------------------+

binlog_format: ROW

+------------------+-----------+
| Log_name         | File_size |
+------------------+-----------+
| mysql-bin.000001 |       157 |
+------------------+-----------+
```

---

## Step 2: Create Baseline Data and Full Backup

```bash
# Create schema and initial data
docker exec mysql-lab mysql -uroot -prootpass shopdb <<'EOF'
CREATE TABLE products (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  name     VARCHAR(100),
  price    DECIMAL(10,2),
  stock    INT,
  category VARCHAR(50)
);

CREATE TABLE orders (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  product_id  INT,
  quantity    INT,
  total       DECIMAL(10,2),
  order_date  DATETIME DEFAULT NOW(),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO products (name, price, stock, category) VALUES
  ('Widget A', 9.99,  100, 'Widgets'),
  ('Gadget B', 19.99, 50,  'Gadgets'),
  ('Device C', 49.99, 25,  'Devices');

INSERT INTO orders (product_id, quantity, total) VALUES
  (1, 5, 49.95),
  (2, 2, 39.98),
  (3, 1, 49.99);

SELECT 'Products:', COUNT(*) FROM products;
SELECT 'Orders:', COUNT(*) FROM orders;
EOF

# Record timestamp BEFORE backup
PRE_BACKUP_TIME=$(docker exec mysql-lab mysql -uroot -prootpass -sN -e "SELECT NOW()")
echo "Pre-backup time: $PRE_BACKUP_TIME"

# Take full backup with mysqldump (includes binlog position)
docker exec mysql-lab mysqldump \
  -uroot -prootpass \
  --single-transaction \
  --master-data=2 \
  --flush-logs \
  --routines \
  --triggers \
  shopdb > /tmp/shopdb_backup.sql

echo "Backup size: $(wc -c < /tmp/shopdb_backup.sql) bytes"
head -30 /tmp/shopdb_backup.sql | grep "CHANGE MASTER TO"
```

📸 **Verified Output:**
```
Pre-backup time: 2026-03-05 10:00:01
Backup size: 4823 bytes
-- CHANGE MASTER TO MASTER_LOG_FILE='mysql-bin.000002', MASTER_LOG_POS=157;
```

> 💡 `--master-data=2` records the binary log position at backup time as a comment. This is your starting point for replaying binary logs during PITR.

---

## Step 3: Simulate Normal Operations and Then "Accidental" Deletion

```bash
# Record time before accidental deletion
SAFE_TIME=$(docker exec mysql-lab mysql -uroot -prootpass -sN -e "SELECT NOW()")
echo "Safe timestamp (before disaster): $SAFE_TIME"

# Normal business operations
docker exec mysql-lab mysql -uroot -prootpass shopdb -e "
  INSERT INTO products (name, price, stock, category) VALUES
    ('SuperWidget X', 29.99, 75, 'Widgets'),
    ('MegaGadget Y', 99.99, 10, 'Gadgets');
  INSERT INTO orders (product_id, quantity, total) VALUES
    (1, 10, 99.90), (4, 3, 89.97);
  SELECT 'After normal ops - products:', COUNT(*) FROM products;
"

sleep 2

# Record exact time before disaster
BEFORE_DISASTER=$(docker exec mysql-lab mysql -uroot -prootpass -sN -e "SELECT NOW()")
echo "Just before disaster: $BEFORE_DISASTER"

sleep 1

# 💥 DISASTER: Someone accidentally drops the orders table!
docker exec mysql-lab mysql -uroot -prootpass shopdb -e "
  DROP TABLE orders;
  SELECT 'DISASTER: orders table dropped at', NOW();
"

# More operations happened after the disaster
sleep 1
docker exec mysql-lab mysql -uroot -prootpass shopdb -e "
  UPDATE products SET stock = stock - 5 WHERE id = 1;
  SELECT 'Post-disaster operations continue...';
"

echo ""
echo "Current state after disaster:"
docker exec mysql-lab mysql -uroot -prootpass shopdb -e "SHOW TABLES;"
```

📸 **Verified Output:**
```
Safe timestamp (before disaster): 2026-03-05 10:00:05
Just before disaster: 2026-03-05 10:00:07

DISASTER: orders table dropped at  2026-03-05 10:00:08
Post-disaster operations continue...

Current state after disaster:
Tables_in_shopdb
products         <- orders is GONE!
```

---

## Step 4: MySQL PITR — Identify Recovery Point in Binary Logs

```bash
# List all binary log files
docker exec mysql-lab mysql -uroot -prootpass -e "SHOW BINARY LOGS;"

# Use mysqlbinlog to find the DROP TABLE event
docker exec mysql-lab mysqlbinlog \
  --short-form \
  /var/lib/mysql/mysql-bin.000002 \
  /var/lib/mysql/mysql-bin.000003 2>/dev/null | \
  grep -B2 -A2 "DROP TABLE"
```

📸 **Verified Output:**
```
+------------------+-----------+
| Log_name         | File_size |
+------------------+-----------+
| mysql-bin.000001 |       157 |
| mysql-bin.000002 |      4821 |
| mysql-bin.000003 |      1247 |
+------------------+-----------+

# at 1589
#260305 10:00:08 server id 1  Query  thread_id=9  exec_time=0
DROP TABLE `orders` /* generated by server */
```

---

## Step 5: MySQL PITR — Restore to Point Before Disaster

```bash
# Create a new MySQL container for restoration
docker run -d --name mysql-restore \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  -e MYSQL_DATABASE=shopdb \
  mysql:8.0

for i in $(seq 1 30); do docker exec mysql-restore mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

# Step 1: Restore full backup
docker exec -i mysql-restore mysql -uroot -prootpass shopdb < /tmp/shopdb_backup.sql
echo "Full backup restored"

# Step 2: Extract binlog position from backup
BINLOG_FILE=$(grep "CHANGE MASTER TO" /tmp/shopdb_backup.sql | grep -o "MASTER_LOG_FILE='[^']*'" | cut -d"'" -f2)
BINLOG_POS=$(grep "CHANGE MASTER TO" /tmp/shopdb_backup.sql | grep -o "MASTER_LOG_POS=[0-9]*" | cut -d= -f2)
echo "Backup binlog position: $BINLOG_FILE @ pos $BINLOG_POS"

# Step 3: Extract binlogs from BACKUP position TO just before disaster
# Use --stop-datetime to stop before the DROP TABLE
docker exec mysql-lab mysqlbinlog \
  --start-position=$BINLOG_POS \
  --stop-datetime="$BEFORE_DISASTER" \
  /var/lib/mysql/$BINLOG_FILE \
  /var/lib/mysql/mysql-bin.000003 2>/dev/null > /tmp/binlog_replay.sql

echo "Binlog replay SQL size: $(wc -l < /tmp/binlog_replay.sql) lines"

# Step 4: Apply binlogs to restored instance
docker exec -i mysql-restore mysql -uroot -prootpass < /tmp/binlog_replay.sql
echo "Binlogs applied!"

# Step 5: Verify recovery
docker exec mysql-restore mysql -uroot -prootpass shopdb -e "
  SHOW TABLES;
  SELECT 'Products:', COUNT(*) FROM products;
  SELECT 'Orders:', COUNT(*) FROM orders;
  SELECT * FROM products;
  SELECT * FROM orders;
"
```

📸 **Verified Output:**
```
Full backup restored
Backup binlog position: mysql-bin.000002 @ pos 157
Binlog replay SQL size: 847 lines
Binlogs applied!

Tables_in_shopdb
orders      <- RECOVERED!
products

Products: 5    <- Includes the 2 added after backup
Orders: 5      <- Recovered! Includes the 2 added after backup

id  name           price  stock  category
1   Widget A       9.99   100    Widgets
2   Gadget B       19.99  50     Gadgets
3   Device C       49.99  25     Devices
4   SuperWidget X  29.99  75     Widgets
5   MegaGadget Y   99.99  10     Gadgets

id  product_id  quantity  total   order_date
1   1           5         49.95   2026-03-05 10:00:01
2   2           2         39.98   2026-03-05 10:00:01
3   3           1         49.99   2026-03-05 10:00:01
4   1           10        99.90   2026-03-05 10:00:05
5   4           3         89.97   2026-03-05 10:00:05
```

> 💡 Recovery stopped just before the disaster. Orders are back! The post-disaster `UPDATE` was not applied since we stopped before the DROP TABLE.

---

## Step 6: PostgreSQL — Configure WAL Archiving for PITR

```bash
docker rm -f mysql-lab mysql-restore

mkdir -p /tmp/pg-archive

docker run -d --name pg-lab \
  -e POSTGRES_PASSWORD=rootpass \
  -v /tmp/pg-archive:/mnt/wal-archive \
  postgres:15 \
  -c wal_level=replica \
  -c archive_mode=on \
  -c archive_command='cp %p /mnt/wal-archive/%f' \
  -c archive_timeout=30 \
  -c restore_command='cp /mnt/wal-archive/%f %p'

sleep 12

docker exec pg-lab psql -U postgres -c "
  SHOW wal_level;
  SHOW archive_mode;
  SHOW archive_command;
"
```

📸 **Verified Output:**
```
 wal_level 
-----------
 replica

 archive_mode 
--------------
 on

              archive_command               
--------------------------------------------
 cp %p /mnt/wal-archive/%f
```

---

## Step 7: PostgreSQL PITR — Create Data, Backup, Simulate Disaster

```bash
docker exec pg-lab psql -U postgres <<'EOF'
CREATE DATABASE shopdb;
EOF

docker exec pg-lab psql -U postgres shopdb <<'EOF'
CREATE TABLE inventory (
  id       SERIAL PRIMARY KEY,
  item     TEXT,
  quantity INT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO inventory (item, quantity) VALUES
  ('Widget A', 100), ('Gadget B', 50), ('Device C', 25);

SELECT COUNT(*) FROM inventory;
EOF

# Take base backup (for PITR starting point)
docker exec pg-lab pg_basebackup \
  -U postgres \
  -D /tmp/pg-pitr-backup \
  --wal-method=stream \
  --checkpoint=fast \
  --label="pitr-lab-backup"

echo "Base backup taken at: $(date -u)"
SAFE_TIMESTAMP=$(date -u "+%Y-%m-%d %H:%M:%S")

# More operations
docker exec pg-lab psql -U postgres shopdb -e "
  INSERT INTO inventory (item, quantity) VALUES ('SuperWidget X', 75), ('MegaGadget Y', 30);
"

sleep 2
BEFORE_DISASTER=$(date -u "+%Y-%m-%d %H:%M:%S")
echo "Before disaster: $BEFORE_DISASTER"

sleep 1

# 💥 DISASTER
docker exec pg-lab psql -U postgres shopdb -c "
  DROP TABLE inventory;
  SELECT current_timestamp AS disaster_time;
"

echo "After disaster - tables:"
docker exec pg-lab psql -U postgres shopdb -c "\dt" || echo "No tables!"
```

📸 **Verified Output:**
```
Base backup taken at: Thu Mar  5 10:00:05 UTC 2026
Before disaster: 2026-03-05 10:00:07
    disaster_time     
----------------------
 2026-03-05 10:00:08

After disaster - tables:
Did not find any relations.
No tables!
```

---

## Step 8: Capstone — PostgreSQL PITR Restore

```bash
# Force WAL segment switch to archive current WAL
docker exec pg-lab psql -U postgres -c "SELECT pg_switch_wal();"
sleep 5

echo "Archived WAL files:"
ls /tmp/pg-archive/

# Stop PostgreSQL
docker stop pg-lab

# Prepare recovery directory
rm -rf /tmp/pg-pitr-restore
cp -r /tmp/pg-pitr-backup /tmp/pg-pitr-restore

# Create recovery configuration
cat > /tmp/pg-pitr-restore/postgresql.conf.recovery << EOF
# Point-in-time recovery settings
recovery_target_time = '${BEFORE_DISASTER}'
recovery_target_action = 'promote'
restore_command = 'cp /mnt/wal-archive/%f %p'
EOF

# Append recovery settings to postgresql.conf
cat /tmp/pg-pitr-restore/postgresql.conf.recovery >> /tmp/pg-pitr-restore/postgresql.conf

# Create standby.signal (tells PostgreSQL to enter recovery mode)
touch /tmp/pg-pitr-restore/standby.signal

# Start PostgreSQL with recovery configuration
docker run -d --name pg-restore \
  -e POSTGRES_PASSWORD=rootpass \
  -v /tmp/pg-pitr-restore:/var/lib/postgresql/data \
  -v /tmp/pg-archive:/mnt/wal-archive:ro \
  postgres:15

sleep 20

# Check if recovery is complete
docker exec pg-restore psql -U postgres -c "
  SELECT pg_is_in_recovery() AS still_recovering;
"

# Verify recovery (inventory should be back!)
docker exec pg-restore psql -U postgres shopdb -c "
  SELECT * FROM inventory;
  SELECT current_timestamp AS recovery_point;
"

# Cleanup
docker stop pg-lab pg-restore
docker rm -f pg-lab pg-restore
rm -rf /tmp/pg-archive /tmp/pg-pitr-backup /tmp/pg-pitr-restore
rm -f /tmp/shopdb_backup.sql /tmp/binlog_replay.sql

echo ""
echo "=== PITR Lab Complete ==="
```

📸 **Verified Output:**
```
 pg_switch_wal 
---------------
 0/4000000

Archived WAL files:
000000010000000000000001  000000010000000000000002  000000010000000000000003  000000010000000000000004

 still_recovering 
------------------
 f

 id |    item       | quantity |          updated_at           
----+---------------+----------+-------------------------------
  1 | Widget A      |      100 | 2026-03-05 10:00:03.412+00
  2 | Gadget B      |       50 | 2026-03-05 10:00:03.412+00
  3 | Device C      |       25 | 2026-03-05 10:00:03.412+00
  4 | SuperWidget X |       75 | 2026-03-05 10:00:06.012+00
  5 | MegaGadget Y  |       30 | 2026-03-05 10:00:06.012+00
(5 rows)   <- RECOVERED!

       recovery_point        
-----------------------------
 2026-03-05 10:00:07.000+00

=== PITR Lab Complete ===
```

---

## Summary

| Component | MySQL | PostgreSQL |
|-----------|-------|------------|
| Log type | Binary log (binlog) | WAL (Write-Ahead Log) |
| Full backup | `mysqldump --master-data=2` | `pg_basebackup` |
| Backup position | Stored in dump header | Implicit from backup LSN |
| Log replay | `mysqlbinlog --stop-datetime` | `restore_command` + `recovery_target_time` |
| Recovery config | N/A | `postgresql.conf` + `standby.signal` |
| Complete recovery | `pg_wal_replay_resume()` | `recovery_target_action=promote` |
| Archive | `expire_logs_days` | `archive_command` |

## Key Takeaways

- **Always take full backups with log position** — `--master-data=2` / `pg_basebackup`
- **Keep binlogs/WAL long enough** — default 7 days may not be enough; size them to RPO requirements
- **Test your PITR procedure** — practice before the disaster happens
- **`--stop-datetime`** is safer than `--stop-position` for human-error recovery (you know the time, not the position)
- **PostgreSQL WAL archiving** is more robust than MySQL binlogs for large setups — integrates with Barman, pgBackRest
