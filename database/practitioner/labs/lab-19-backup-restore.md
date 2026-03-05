# Lab 19: Backup and Restore

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MySQL 8.0 + PostgreSQL 15 + MongoDB 7

Backups are insurance. This lab covers the tools every practitioner must know: logical dumps, binary logs (PITR), and document store backups. Tested and verified with Docker.

---

## Step 1 — MySQL: mysqldump Basics

```bash
# Full database dump (single database)
docker exec mysql-lab8 mysqldump \
  -uroot -prootpass \
  --single-transaction \
  --routines \
  --triggers \
  labdb > /tmp/labdb_backup.sql

# Verify backup
wc -l /tmp/labdb_backup.sql
head -30 /tmp/labdb_backup.sql
```

📸 **Verified Output:**
```
168 /tmp/labdb_backup.sql

-- MySQL dump 10.13  Distrib 8.0.45, for Linux (x86_64)
-- Host: localhost    Database: labdb
-- Server version 8.0.45
...
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `customer` varchar(100) DEFAULT NULL,
...
```

> 💡 `--single-transaction` uses a repeatable-read snapshot for InnoDB tables — no table locks during backup. Critical for production backups without downtime.

---

## Step 2 — MySQL: Backup Options

```bash
# All databases
mysqldump -uroot -prootpass \
  --all-databases \
  --single-transaction \
  --routines \
  --events \
  > /tmp/all_databases.sql

# Specific tables
mysqldump -uroot -prootpass labdb orders articles \
  > /tmp/specific_tables.sql

# Structure only (no data)
mysqldump -uroot -prootpass --no-data labdb \
  > /tmp/schema_only.sql

# Data only (no CREATE statements)
mysqldump -uroot -prootpass --no-create-info labdb \
  > /tmp/data_only.sql

# Compressed backup
mysqldump -uroot -prootpass --single-transaction labdb \
  | gzip > /tmp/labdb_backup_$(date +%Y%m%d).sql.gz

# Show backup size
ls -lh /tmp/labdb_backup.sql
```

---

## Step 3 — MySQL: Restore from Dump

```bash
# Create a new database to restore into
docker exec mysql-lab8 mysql -uroot -prootpass -e \
  "CREATE DATABASE IF NOT EXISTS labdb_restored;"

# Restore
docker exec -i mysql-lab8 mysql -uroot -prootpass labdb_restored \
  < /tmp/labdb_backup.sql

# Verify restore
docker exec mysql-lab8 mysql -uroot -prootpass labdb_restored -e \
  "SHOW TABLES; SELECT COUNT(*) AS orders_count FROM orders;" 2>/dev/null
```

📸 **Verified Output:**
```
Tables_in_labdb_restored
audit_log
orders
orders_deleted

orders_count
6
```

```bash
# Restore from gzip
gunzip -c /tmp/labdb_backup_$(date +%Y%m%d).sql.gz \
  | docker exec -i mysql-lab8 mysql -uroot -prootpass labdb_restored2
```

---

## Step 4 — MySQL: Binary Log and Point-in-Time Recovery

```bash
# Check binary log status
docker exec mysql-lab8 mysql -uroot -prootpass -e "SHOW VARIABLES LIKE 'log_bin%';" 2>/dev/null
docker exec mysql-lab8 mysql -uroot -prootpass -e "SHOW BINARY LOGS;" 2>/dev/null

# Enable binary logging (in my.cnf / my.ini):
# [mysqld]
# log-bin = mysql-bin
# binlog_format = ROW
# expire_logs_days = 7

# List binary log events
# mysqlbinlog /var/lib/mysql/mysql-bin.000001

# Point-in-Time Recovery workflow:
# 1. Restore from last full backup
mysql -uroot -prootpass labdb_restored < /tmp/labdb_backup.sql

# 2. Replay binary logs from backup timestamp to target time
# mysqlbinlog --start-datetime="2024-01-15 10:00:00" \
#             --stop-datetime="2024-01-15 10:30:00" \
#             /var/lib/mysql/mysql-bin.000001 \
#             | mysql -uroot -prootpass labdb_restored

# 3. Verify data at the target point in time
```

> 💡 Binary log PITR requires: (1) full backup as baseline, (2) binary logs enabled and retained from that point, (3) ability to replay logs up to any point in time.

---

## Step 5 — PostgreSQL: pg_dump

```bash
# pg_dump: logical backup of a single database

# Custom format (compressed, supports selective restore)
docker exec pg-lab15 pg_dump \
  -U postgres \
  -Fc \
  -f /tmp/postgres_backup.dump \
  postgres

# Check backup size
docker exec pg-lab15 ls -lh /tmp/postgres_backup.dump
```

📸 **Verified Output:**
```
-rw-r--r-- 1 root root 173K Mar  5 15:57 /tmp/postgres_backup.dump
```

```bash
# Plain SQL format
docker exec pg-lab15 pg_dump -U postgres -Fp postgres > /tmp/postgres.sql

# Directory format (parallel dump, each table a file)
docker exec pg-lab15 pg_dump -U postgres -Fd -j 4 \
  -f /tmp/postgres_dir postgres

# Schema only
docker exec pg-lab15 pg_dump -U postgres --schema-only postgres \
  > /tmp/schema.sql

# Table list from dump (custom format)
docker exec pg-lab15 pg_restore --list /tmp/postgres_backup.dump | head -20
```

---

## Step 6 — PostgreSQL: pg_restore and pg_dumpall

```bash
# Create restore target
docker exec pg-lab15 psql -U postgres -c "CREATE DATABASE postgres_restored;"

# pg_restore from custom format
docker exec pg-lab15 pg_restore \
  -U postgres \
  -d postgres_restored \
  /tmp/postgres_backup.dump

# Restore only specific tables
docker exec pg-lab15 pg_restore \
  -U postgres \
  -d postgres_restored \
  -t products \
  -t sales \
  /tmp/postgres_backup.dump

# Restore in parallel (faster for large DBs)
docker exec pg-lab15 pg_restore \
  -U postgres \
  -d postgres_restored \
  -j 4 \
  /tmp/postgres_backup.dump

# Verify restore
docker exec pg-lab15 psql -U postgres -d postgres_restored -c "
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;"
```

```bash
# pg_dumpall: backup ALL databases + global objects (roles, tablespaces)
docker exec pg-lab15 pg_dumpall -U postgres > /tmp/all_postgres.sql

# Restore with pg_dumpall output
# psql -U postgres < /tmp/all_postgres.sql
```

---

## Step 7 — PostgreSQL: Point-in-Time Recovery Concept

PostgreSQL PITR uses WAL (Write-Ahead Log) — every change is logged before being applied.

**Setup continuous archiving (postgresql.conf):**
```
wal_level = replica
archive_mode = on
archive_command = 'cp %p /wal_archive/%f'
```

**PITR Recovery workflow:**
```bash
# 1. Take base backup
pg_basebackup -h localhost -U replicator -D /backup/base \
  --wal-method=stream --checkpoint=fast

# 2. Later, restore to specific time
# Edit recovery.conf (PG <12) or postgresql.conf (PG 12+):
# restore_command = 'cp /wal_archive/%f %p'
# recovery_target_time = '2024-01-15 14:30:00'

# 3. Start PostgreSQL — it replays WAL up to the target time
```

> 💡 PITR is PostgreSQL's equivalent to MySQL binary log recovery. It can restore to any second in time as long as WAL files are retained from the base backup.

---

## Step 8 — MongoDB: mongodump and mongorestore

```bash
# mongodump: backup a database
docker exec mongo-lab7 mongodump \
  --db shopdb \
  --out /tmp/mongodump \
  --quiet

# View backup files
docker exec mongo-lab7 ls -la /tmp/mongodump/shopdb/
```

📸 **Verified Output:**
```
total 36
drwxr-xr-x 2 root root 4096 Mar  5 15:57 .
drwxr-xr-x 3 root root 4096 Mar  5 15:57 ..
-rw-r--r-- 1 root root  254 Mar  5 15:57 customers.bson
-rw-r--r-- 1 root root  176 Mar  5 15:57 customers.metadata.json
-rw-r--r-- 1 root root  893 Mar  5 15:57 orders.bson
-rw-r--r-- 1 root root  173 Mar  5 15:57 orders.metadata.json
-rw-r--r-- 1 root root  691 Mar  5 15:57 products.bson
-rw-r--r-- 1 root root  846 Mar  5 15:57 products.metadata.json
```

```bash
# Restore with mongorestore
docker exec mongo-lab7 mongorestore \
  --drop \
  --db shopdb_restored \
  /tmp/mongodump/shopdb/ \
  --quiet

# Verify restore
docker exec mongo-lab7 mongosh shopdb_restored --quiet --eval \
  'print("Orders restored:", db.orders.countDocuments())'
```

📸 **Verified Output:**
```
Orders restored: 7
```

```bash
# Backup all databases
docker exec mongo-lab7 mongodump --out /tmp/mongodump_all --quiet

# Backup with compression
docker exec mongo-lab7 mongodump \
  --db shopdb \
  --archive=/tmp/shopdb.archive \
  --gzip

# Restore from archive
docker exec mongo-lab7 mongorestore \
  --db shopdb_restored2 \
  --archive=/tmp/shopdb.archive \
  --gzip

# Export single collection as JSON (human-readable)
docker exec mongo-lab7 mongoexport \
  --db shopdb \
  --collection orders \
  --out /tmp/orders.json \
  --jsonArray --pretty

# Import from JSON
docker exec mongo-lab7 mongoimport \
  --db shopdb_imported \
  --collection orders \
  --file /tmp/orders.json \
  --jsonArray
```

---

## Summary

| Tool | Database | Format | Use Case |
|------|---------|--------|----------|
| `mysqldump` | MySQL | SQL text | Logical backup, migration |
| `mysqlbinlog` | MySQL | Binary log | PITR, audit |
| `mysqlpump` | MySQL | SQL parallel | Faster logical backup |
| `pg_dump` | PostgreSQL | SQL / custom / dir | Single database |
| `pg_dumpall` | PostgreSQL | SQL text | All databases + globals |
| `pg_restore` | PostgreSQL | — | Restore custom/dir format |
| `pg_basebackup` | PostgreSQL | Binary | Physical backup for PITR |
| `mongodump` | MongoDB | BSON | Logical collection backup |
| `mongorestore` | MongoDB | BSON | Restore collections |
| `mongoexport` | MongoDB | JSON/CSV | Export for migration |
| `mongoimport` | MongoDB | JSON/CSV | Import from files |
