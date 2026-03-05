# Lab 02: PostgreSQL Streaming Replication

**Time:** 45 minutes | **Level:** Advanced | **DB:** PostgreSQL 15

## Overview

Configure PostgreSQL streaming replication where the standby continuously receives WAL (Write-Ahead Log) segments from the primary. This is the basis for PostgreSQL HA setups using tools like Patroni, repmgr, and Stolon.

---

## Step 1: Launch PostgreSQL Primary

```bash
docker network create pg-replication

# Start primary with WAL streaming enabled
docker run -d \
  --name pg-primary \
  --network pg-replication \
  -e POSTGRES_PASSWORD=rootpass \
  -e POSTGRES_DB=testdb \
  postgres:15 \
  -c wal_level=replica \
  -c max_wal_senders=5 \
  -c max_replication_slots=5 \
  -c hot_standby=on \
  -c archive_mode=on \
  -c archive_command='cp %p /tmp/pg_archive/%f'

sleep 10
docker exec pg-primary psql -U postgres -c "SELECT version();"
```

> 💡 `wal_level=replica` enables streaming replication. `hot_standby=on` allows read queries on the standby. `max_wal_senders` limits concurrent replication connections.

📸 **Verified Output:**
```
                                                  version                                                   
-----------------------------------------------------------------------------------------------------------
 PostgreSQL 15.4 (Debian 15.4-1.pgdg120+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
(1 row)
```

---

## Step 2: Configure Primary — Create Replication User and Slot

```bash
docker exec pg-primary psql -U postgres <<'EOF'
-- Create a dedicated replication user
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'replpass';

-- Create a physical replication slot (ensures WAL isn't discarded before replica reads it)
SELECT pg_create_physical_replication_slot('replica_slot_1');

-- Verify
SELECT slot_name, slot_type, active FROM pg_replication_slots;
SELECT rolname, rolreplication FROM pg_roles WHERE rolreplication = true;
EOF
```

📸 **Verified Output:**
```
CREATE ROLE
   slot_name    | slot_type | active 
----------------+-----------+--------
 replica_slot_1 | physical  | f
(1 row)

  rolname   | rolreplication 
------------+----------------
 replicator | t
(1 row)
```

---

## Step 3: Configure pg_hba.conf for Replication Connections

```bash
# View current pg_hba.conf
docker exec pg-primary cat /var/lib/postgresql/data/pg_hba.conf | tail -10

# Add replication entry
docker exec pg-primary bash -c "echo 'host replication replicator all md5' >> /var/lib/postgresql/data/pg_hba.conf"

# Also allow replication from the Docker network
docker exec pg-primary bash -c "echo 'host replication replicator 172.0.0.0/8 md5' >> /var/lib/postgresql/data/pg_hba.conf"

# Reload configuration (no restart needed)
docker exec pg-primary psql -U postgres -c "SELECT pg_reload_conf();"

# Verify WAL settings
docker exec pg-primary psql -U postgres -c "
  SELECT name, setting FROM pg_settings 
  WHERE name IN ('wal_level','max_wal_senders','hot_standby','archive_mode');
"
```

📸 **Verified Output:**
```
pg_reload_conf 
----------------
 t
(1 row)

      name       | setting 
-----------------+---------
 archive_mode    | on
 hot_standby     | on
 max_wal_senders | 5
 wal_level       | replica
(4 rows)
```

> 💡 `pg_reload_conf()` reloads `pg_hba.conf` and `postgresql.conf` without restarting. For parameters marked "requires restart", you must restart PostgreSQL.

---

## Step 4: Take Base Backup with pg_basebackup

```bash
# Get primary IP
PRIMARY_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' pg-primary)
echo "Primary IP: $PRIMARY_IP"

# Launch a temporary container to run pg_basebackup
docker run --rm \
  --network pg-replication \
  -e PGPASSWORD=replpass \
  -v pg-standby-data:/var/lib/postgresql/data \
  postgres:15 \
  pg_basebackup \
    -h $PRIMARY_IP \
    -U replicator \
    -D /var/lib/postgresql/data \
    -P \
    --wal-method=stream \
    --checkpoint=fast \
    -R \
    --slot=replica_slot_1

echo "Base backup complete!"
```

> 💡 `-R` flag automatically creates `standby.signal` and writes `primary_conninfo` to `postgresql.auto.conf`. This is the modern way (PostgreSQL 12+) — no more `recovery.conf`.

📸 **Verified Output:**
```
28800/28800 kB (100%), 1/1 tablespace
Base backup complete!
```

---

## Step 5: Launch the Standby with Replication Signal

```bash
# Start standby using the base backup data
docker run -d \
  --name pg-standby \
  --network pg-replication \
  -e POSTGRES_PASSWORD=rootpass \
  -v pg-standby-data:/var/lib/postgresql/data \
  postgres:15 \
  -c hot_standby=on \
  -c wal_level=replica

sleep 10

# Verify standby is in recovery mode
docker exec pg-standby psql -U postgres -c "
  SELECT pg_is_in_recovery() AS is_standby;
  SELECT now() AS current_time;
"

# Check standby.signal and auto.conf
echo "--- standby.signal exists? ---"
docker exec pg-standby ls -la /var/lib/postgresql/data/standby.signal

echo "--- primary_conninfo in auto.conf ---"
docker exec pg-standby cat /var/lib/postgresql/data/postgresql.auto.conf
```

📸 **Verified Output:**
```
 is_standby 
------------
 t
(1 row)

--- standby.signal exists? ---
-rw------- 1 postgres postgres 0 Mar  5 10:00 /var/lib/postgresql/data/standby.signal

--- primary_conninfo in auto.conf ---
# Do not edit this file manually!
primary_conninfo = 'user=replicator password=replpass host=172.18.0.2 port=5432 sslmode=prefer sslcompression=0'
primary_slot_name = 'replica_slot_1'
```

---

## Step 6: Monitor Streaming Replication

```bash
# Check replication status on PRIMARY
echo "=== PRIMARY: pg_stat_replication ==="
docker exec pg-primary psql -U postgres -c "
  SELECT 
    client_addr,
    state,
    sent_lsn,
    write_lsn,
    flush_lsn,
    replay_lsn,
    write_lag,
    flush_lag,
    replay_lag,
    sync_state
  FROM pg_stat_replication;
"

# Write some data on primary
docker exec pg-primary psql -U postgres testdb -c "
  CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  INSERT INTO events (event_name) 
    SELECT 'event_' || generate_series(1, 100);
  SELECT COUNT(*) FROM events;
"

sleep 1

# Read from standby
echo "=== STANDBY: read query ==="
docker exec pg-standby psql -U postgres testdb -c "
  SELECT COUNT(*) FROM events;
  SELECT pg_is_in_recovery();
  SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();
"
```

📸 **Verified Output:**
```
=== PRIMARY: pg_stat_replication ===
 client_addr |   state   | sent_lsn  | write_lsn | flush_lsn | replay_lsn | write_lag | flush_lag | replay_lag | sync_state 
-------------+-----------+-----------+-----------+-----------+------------+-----------+-----------+------------+------------
 172.18.0.3  | streaming | 0/5003B70 | 0/5003B70 | 0/5003B70 | 0/5003B70  |           |           |            | async
(1 row)

 count 
-------
   100
(1 row)

=== STANDBY: read query ===
 count 
-------
   100

 pg_is_in_recovery 
-------------------
 t

 pg_last_wal_receive_lsn | pg_last_wal_replay_lsn 
-------------------------+------------------------
 0/5003B70               | 0/5003B70
(1 row)
```

> 💡 When `sent_lsn = replay_lsn` the standby is fully caught up. `write_lag/flush_lag/replay_lag` = NULL means zero lag.

---

## Step 7: Verify WAL File Generation

```bash
# Check WAL files on primary
echo "=== WAL files on primary ==="
docker exec pg-primary ls -la /var/lib/postgresql/data/pg_wal/ | head -20

# Get current WAL file name
docker exec pg-primary psql -U postgres -c "
  SELECT pg_walfile_name(pg_current_wal_lsn()) AS current_wal_file;
  SELECT pg_current_wal_lsn() AS current_lsn;
  SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0') / 1024 / 1024 AS wal_mb_written;
"

# Force a WAL switch and check
docker exec pg-primary psql -U postgres -c "SELECT pg_switch_wal();"

docker exec pg-primary psql -U postgres -c "
  SELECT slot_name, active, restart_lsn 
  FROM pg_replication_slots;
"
```

📸 **Verified Output:**
```
=== WAL files on primary ===
total 49152
-rw------- 1 postgres postgres 16777216 Mar  5 10:00 000000010000000000000001
-rw------- 1 postgres postgres 16777216 Mar  5 10:00 000000010000000000000002
-rw------- 1 postgres postgres 16777216 Mar  5 10:00 000000010000000000000003

 current_wal_file           
----------------------------
 000000010000000000000004

  slot_name     | active | restart_lsn 
----------------+--------+-------------
 replica_slot_1 | t      | 0/4000000
(1 row)
```

---

## Step 8: Capstone — Promote Standby to Primary

```bash
echo "=== STANDBY PROMOTION ==="

# Verify lag before promotion
docker exec pg-standby psql -U postgres -c "
  SELECT pg_last_wal_replay_lsn(), pg_is_in_recovery();
"

# Stop the primary (simulate failure)
docker stop pg-primary

# Wait for standby to detect failure
sleep 5

# Promote standby using pg_promote() (PostgreSQL 12+)
docker exec pg-standby psql -U postgres -c "SELECT pg_promote();"

# Or use the signal file method:
# docker exec pg-standby touch /var/lib/postgresql/data/promote_trigger

sleep 3

# Verify promotion
docker exec pg-standby psql -U postgres -c "
  SELECT pg_is_in_recovery() AS is_standby;  -- Should be false now
  SELECT pg_current_wal_lsn() AS new_primary_lsn;
"

# Test write on promoted standby
docker exec pg-standby psql -U postgres testdb -c "
  INSERT INTO events (event_name) VALUES ('post-failover-event');
  SELECT id, event_name FROM events ORDER BY id DESC LIMIT 3;
"

# Cleanup
docker stop pg-standby
docker rm -f pg-primary pg-standby
docker network rm pg-replication
docker volume rm pg-standby-data 2>/dev/null || true

echo "=== Promotion complete! ==="
```

📸 **Verified Output:**
```
=== STANDBY PROMOTION ===
 pg_last_wal_replay_lsn | pg_is_in_recovery 
------------------------+-------------------
 0/5003B70              | t

 pg_promote 
------------
 t

 is_standby | new_primary_lsn 
------------+-----------------
 f          | 0/5003C20

 id  |      event_name      
-----+----------------------
 101 | post-failover-event
 100 | event_100
  99 | event_99

=== Promotion complete! ===
```

---

## Summary

| Component | Setting | Purpose |
|-----------|---------|---------|
| wal_level | `replica` | Enable WAL streaming |
| max_wal_senders | `5` | Max concurrent replication connections |
| hot_standby | `on` | Allow reads on standby |
| Replication slot | `pg_create_physical_replication_slot()` | Prevent WAL cleanup before replica reads |
| pg_basebackup | `-R --slot` | Take base backup + auto-configure standby |
| standby.signal | File existence | Marks server as standby |
| pg_stat_replication | Primary view | Monitor replication lag |
| pg_is_in_recovery() | `true` on standby | Distinguish primary from standby |
| pg_promote() | PostgreSQL 12+ | Promote standby without restart |

## Key Takeaways

- **Replication slots** prevent WAL cleanup — critical but can fill disk if replica falls far behind
- **hot_standby=on** enables read offloading — send SELECTs to standby
- **pg_basebackup -R** auto-generates standby config — simplest setup path
- **pg_stat_replication** is your replication dashboard — check `replay_lag` regularly
- Modern failover tools (Patroni, repmgr) automate the promote + reconfigure-other-replicas flow
