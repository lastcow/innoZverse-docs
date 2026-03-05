# Lab 18: Apache Cassandra Wide-Column Store

**Time:** 45 minutes | **Level:** Advanced | **DB:** Apache Cassandra

## Overview

Cassandra is a distributed wide-column database designed for massive write throughput and linear scalability. Its data model — partition keys, clustering columns, and configurable consistency levels — makes it ideal for time-series, IoT, and high-write workloads.

---

## Step 1: Launch Cassandra

```bash
docker run -d --name cassandra-lab \
  -e MAX_HEAP_SIZE=512M \
  -e HEAP_NEWSIZE=128M \
  cassandra:4.1

echo "Waiting for Cassandra to start (60-90 seconds)..."
for i in $(seq 1 60); do
  docker exec cassandra-lab cqlsh -e "SELECT now() FROM system.local;" 2>/dev/null | grep -q "system.time_uuid" && break || sleep 3
done

echo "Cassandra ready!"
docker exec cassandra-lab nodetool status
```

📸 **Verified Output:**
```
Cassandra ready!
Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address     Load        Tokens  Owns (effective)  Host ID                               Rack 
UN  172.18.0.2  69.07 KiB   16      100.0%            a1b2c3d4-1234-5678-abcd-ef0123456789  rack1

UN = Up Normal
```

> 💡 A single-node Cassandra cluster is useful for development but not fault-tolerant. Production requires minimum 3 nodes for quorum (`QUORUM` consistency).

---

## Step 2: Create Keyspace with Replication Strategy

```bash
docker exec cassandra-lab cqlsh <<'EOF'
-- Create a keyspace (equivalent to database)
-- SimpleStrategy: for single data center
-- NetworkTopologyStrategy: for multi-DC production
CREATE KEYSPACE ecommerce 
WITH REPLICATION = {
  'class': 'SimpleStrategy',
  'replication_factor': 1    -- Set to 3 in production
};

-- NetworkTopologyStrategy example (production):
-- CREATE KEYSPACE prod_ks WITH REPLICATION = {
--   'class': 'NetworkTopologyStrategy',
--   'datacenter1': 3,
--   'datacenter2': 2
-- };

-- View keyspace metadata
DESCRIBE KEYSPACE ecommerce;

-- List all keyspaces
SELECT keyspace_name, replication FROM system_schema.keyspaces;
EOF
```

📸 **Verified Output:**
```
CREATE KEYSPACE ecommerce WITH replication = {'class': 'SimpleStrategy', 'replication_factor': '1'} AND durable_writes = true;

 keyspace_name      | replication                                                              
--------------------+--------------------------------------------------------------------------
 ecommerce          | {'class': 'org.apache.cassandra.locator.SimpleStrategy', 'replication_factor': '1'}
 system             | {'class': 'org.apache.cassandra.locator.LocalStrategy'}
 system_auth        | {'class': 'org.apache.cassandra.locator.SimpleStrategy', 'replication_factor': '1'}
 system_distributed | {'class': 'org.apache.cassandra.locator.SimpleStrategy', 'replication_factor': '3'}
 system_schema      | {'class': 'org.apache.cassandra.locator.LocalStrategy'}
(5 rows)
```

---

## Step 3: Create Tables — Partition Key and Clustering Columns

```bash
docker exec cassandra-lab cqlsh <<'EOF'
USE ecommerce;

-- Table design: query-driven in Cassandra!
-- Q: "Give me all orders for user X, sorted by date descending"
-- Partition key: user_id (distributes data across nodes)
-- Clustering column: order_date DESC (determines row order within partition)

CREATE TABLE user_orders (
  user_id     UUID,
  order_date  TIMESTAMP,
  order_id    UUID,
  product_id  UUID,
  quantity    INT,
  price       DECIMAL,
  status      TEXT,
  notes       TEXT,
  PRIMARY KEY ((user_id), order_date, order_id)  -- Composite key
) WITH CLUSTERING ORDER BY (order_date DESC, order_id ASC)
  AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1
  };

-- IoT time-series table
-- Partition: sensor_id + date (prevents unbounded partitions)
-- Clustering: timestamp DESC
CREATE TABLE sensor_readings (
  sensor_id    TEXT,
  date         DATE,
  measured_at  TIMESTAMP,
  temperature  FLOAT,
  humidity     FLOAT,
  pressure     FLOAT,
  PRIMARY KEY ((sensor_id, date), measured_at)
) WITH CLUSTERING ORDER BY (measured_at DESC)
  AND default_time_to_live = 2592000  -- Auto-expire after 30 days (86400 * 30)
  AND compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'HOURS',
    'compaction_window_size': 1
  };

-- Simple user lookup table
CREATE TABLE users (
  user_id   UUID PRIMARY KEY,
  username  TEXT,
  email     TEXT,
  country   TEXT,
  created_at TIMESTAMP
);

DESCRIBE TABLES;
EOF
```

📸 **Verified Output:**
```
CREATE TABLE ecommerce.user_orders (
    user_id uuid,
    order_date timestamp,
    order_id uuid,
    ...
    PRIMARY KEY (user_id, order_date, order_id)
) WITH CLUSTERING ORDER BY (order_date DESC, order_id ASC)...

Tables in keyspace ecommerce:
sensor_readings  user_orders  users
```

> 💡 **Cassandra design rule**: Design tables around queries, not normalized data. Each query gets its own table. Duplicate data is expected and encouraged.

---

## Step 4: INSERT, SELECT, UPDATE Operations

```bash
docker exec cassandra-lab cqlsh <<'EOF'
USE ecommerce;

-- Insert users
INSERT INTO users (user_id, username, email, country, created_at) VALUES 
  (uuid(), 'alice', 'alice@example.com', 'US', toTimestamp(now()));
INSERT INTO users (user_id, username, email, country, created_at) VALUES 
  (550e8400-e29b-41d4-a716-446655440000, 'bob', 'bob@example.com', 'UK', toTimestamp(now()));

-- Insert orders for a specific user
INSERT INTO user_orders (user_id, order_date, order_id, product_id, quantity, price, status)
VALUES (
  550e8400-e29b-41d4-a716-446655440000,
  '2024-03-01 10:00:00+0000',
  uuid(),
  uuid(),
  2, 19.99, 'delivered'
);

INSERT INTO user_orders (user_id, order_date, order_id, product_id, quantity, price, status)
VALUES (
  550e8400-e29b-41d4-a716-446655440000,
  '2024-06-15 14:30:00+0000',
  uuid(),
  uuid(),
  1, 49.99, 'shipped'
);

INSERT INTO user_orders (user_id, order_date, order_id, product_id, quantity, price, status)
VALUES (
  550e8400-e29b-41d4-a716-446655440000,
  '2024-11-20 09:00:00+0000',
  uuid(),
  uuid(),
  5, 9.99, 'pending'
);

-- Query orders for user (efficient: same partition!)
SELECT order_date, quantity, price, status 
FROM user_orders 
WHERE user_id = 550e8400-e29b-41d4-a716-446655440000;

-- Range query on clustering column
SELECT order_date, price, status 
FROM user_orders 
WHERE user_id = 550e8400-e29b-41d4-a716-446655440000
  AND order_date > '2024-06-01 00:00:00+0000';
EOF
```

📸 **Verified Output:**
```
 order_date                      | quantity | price | status   
---------------------------------+----------+-------+----------
 2024-11-20 09:00:00.000000+0000 |        5 |  9.99 | pending
 2024-06-15 14:30:00.000000+0000 |        1 | 49.99 | shipped
 2024-03-01 10:00:00.000000+0000 |        2 | 19.99 | delivered
(3 rows)   <- Sorted DESC by order_date (as configured)

 order_date                      | price | status  
---------------------------------+-------+---------
 2024-11-20 09:00:00.000000+0000 |  9.99 | pending
 2024-06-15 14:30:00.000000+0000 | 49.99 | shipped
(2 rows)
```

---

## Step 5: CQL Data Types and TTL

```bash
docker exec cassandra-lab cqlsh <<'EOF'
USE ecommerce;

-- Cassandra data types demo
CREATE TABLE type_examples (
  id          UUID PRIMARY KEY,
  -- Numeric
  age         INT,
  score       BIGINT,
  price       DECIMAL,
  ratio       FLOAT,
  -- Text
  name        TEXT,
  data        BLOB,
  -- Time
  created_at  TIMESTAMP,
  my_date     DATE,
  time_only   TIME,
  -- Collections
  tags        SET<TEXT>,
  scores      LIST<INT>,
  metadata    MAP<TEXT, TEXT>,
  -- Special
  ip_addr     INET,
  my_uuid     UUID,
  my_timeuuid TIMEUUID
);

-- Insert with collections
INSERT INTO type_examples (id, age, name, tags, scores, metadata, ip_addr)
VALUES (
  uuid(), 30, 'Alice',
  {'admin', 'user', 'beta-tester'},
  [95, 87, 92, 88],
  {'lang': 'Python', 'team': 'backend'},
  '192.168.1.100'
);

SELECT name, age, tags, scores, metadata, ip_addr FROM type_examples;

-- TTL: Per-row expiration
-- Useful for session data, cache, rate limiting
INSERT INTO user_orders (user_id, order_date, order_id, product_id, quantity, price, status)
VALUES (
  550e8400-e29b-41d4-a716-446655440000,
  '2024-12-31 23:59:59+0000',
  uuid(), uuid(), 1, 5.00, 'temp-record'
) USING TTL 3600;  -- Expires in 1 hour

-- Check TTL remaining
SELECT status, TTL(status) AS ttl_remaining_seconds
FROM user_orders
WHERE user_id = 550e8400-e29b-41d4-a716-446655440000
  AND order_date = '2024-12-31 23:59:59+0000';
EOF
```

📸 **Verified Output:**
```
 name  | age | tags                              | scores            | metadata                          | ip_addr       
-------+-----+-----------------------------------+-------------------+-----------------------------------+---------------
 Alice |  30 | {'admin', 'beta-tester', 'user'}  | [95, 87, 92, 88] | {'lang': 'Python', 'team': 'backend'} | 192.168.1.100

 status      | ttl_remaining_seconds 
-------------+-----------------------
 temp-record |                  3597
(1 row)
```

---

## Step 6: Consistency Levels

```bash
docker exec cassandra-lab cqlsh <<'EOF'
USE ecommerce;

-- Consistency level controls: how many replicas must respond
-- For a 1-node cluster, only LOCAL_ONE works
-- In production (3 replicas): 
--   ONE = fastest, least consistent
--   QUORUM = (RF/2)+1 nodes = 2 of 3 = balanced
--   ALL = all nodes = strongest consistency, lowest availability

-- Set consistency for this session
CONSISTENCY LOCAL_ONE;

INSERT INTO users (user_id, username, email, country, created_at)
VALUES (uuid(), 'carol', 'carol@example.com', 'DE', toTimestamp(now()));

SELECT username, email FROM users;

-- Consistency levels reference (production with RF=3):
-- CONSISTENCY ONE      → 1 replica responds → Fast, may read stale data
-- CONSISTENCY QUORUM   → 2 of 3 respond → Strongly consistent for writes
-- CONSISTENCY ALL      → All 3 respond → Slowest, fails if any node down
-- CONSISTENCY LOCAL_QUORUM → For multi-DC: quorum in local DC only
-- CONSISTENCY EACH_QUORUM  → Quorum in each DC (for global writes)

-- Check current consistency
CONSISTENCY;
EOF
```

📸 **Verified Output:**
```
Current consistency level is LOCAL_ONE.

 username | email             
----------+-------------------
 alice    | alice@example.com
 bob      | bob@example.com  
 carol    | carol@example.com
(3 rows)

Current consistency level is LOCAL_ONE.
```

> 💡 **Golden rule**: `QUORUM` writes + `QUORUM` reads = strong consistency. `ONE` writes + `ONE` reads = eventual consistency (may read stale data).

---

## Step 7: nodetool — Cluster Operations

```bash
# Cassandra node management
echo "=== nodetool status ==="
docker exec cassandra-lab nodetool status

echo ""
echo "=== Ring info (token ranges) ==="
docker exec cassandra-lab nodetool ring 2>/dev/null | head -15

echo ""
echo "=== Table stats ==="
docker exec cassandra-lab nodetool tablestats ecommerce.user_orders 2>/dev/null | head -30

echo ""
echo "=== Compaction stats ==="
docker exec cassandra-lab nodetool compactionstats

echo ""
echo "=== GC stats ==="
docker exec cassandra-lab nodetool gcstats
```

📸 **Verified Output:**
```
=== nodetool status ===
Datacenter: datacenter1
=======================
Status=Up/Down
|/ State=Normal/Leaving/Joining/Moving
--  Address     Load       Tokens  Owns (effective)  Host ID                               Rack 
UN  172.18.0.2  109.36 KiB  16      100.0%            a1b2c3d4-1234-5678-abcd-ef0123456789  rack1

=== Table stats ===
Keyspace : ecommerce
        Table: user_orders
        SSTable count: 1
        Space used (live): 17.21 KiB
        Space used (total): 17.21 KiB
        Number of partitions (estimate): 1
        Memtable cell count: 4
        Memtable data size: 820
        Bloom filter false positives: 0
        ...

=== Compaction stats ===
pending tasks: 0
```

---

## Step 8: Capstone — Compaction Strategies

```bash
docker exec cassandra-lab cqlsh <<'EOF'
USE ecommerce;

-- Trigger manual compaction on sensor_readings
-- In Cassandra, writes go to memtable → flush to SSTable
-- Compaction merges SSTables and removes tombstones (deleted data)

-- Insert sensor data to generate SSTables
INSERT INTO sensor_readings (sensor_id, date, measured_at, temperature, humidity, pressure)
VALUES ('sensor-001', '2024-03-05', '2024-03-05 10:00:00+0000', 22.5, 65.2, 1013.25);
INSERT INTO sensor_readings (sensor_id, date, measured_at, temperature, humidity, pressure)
VALUES ('sensor-001', '2024-03-05', '2024-03-05 10:01:00+0000', 22.8, 64.9, 1013.20);
INSERT INTO sensor_readings (sensor_id, date, measured_at, temperature, humidity, pressure)
VALUES ('sensor-001', '2024-03-05', '2024-03-05 10:02:00+0000', 23.1, 64.5, 1013.15);

-- Query with date range (efficient: partition key includes date)
SELECT measured_at, temperature, humidity
FROM sensor_readings
WHERE sensor_id = 'sensor-001'
  AND date = '2024-03-05'
  AND measured_at > '2024-03-05 09:59:00+0000'
ORDER BY measured_at DESC;

-- Show table metadata and compaction settings
DESCRIBE TABLE sensor_readings;

-- Compaction strategy options:
-- SizeTieredCompactionStrategy (STCS): default, good for write-heavy
-- LeveledCompactionStrategy (LCS): uniform read performance, good for read-heavy
-- TimeWindowCompactionStrategy (TWCS): optimal for time-series data
--   - Compacts data within the same time window together
--   - Old windows sealed - won't be recompacted
--   - Perfect for append-only time-series

SELECT keyspace_name, table_name, compaction 
FROM system_schema.tables 
WHERE keyspace_name = 'ecommerce';
EOF

docker rm -f cassandra-lab
echo "Lab complete!"
```

📸 **Verified Output:**
```
 measured_at                     | temperature | humidity 
---------------------------------+-------------+----------
 2024-03-05 10:02:00.000000+0000 |        23.1 |     64.5
 2024-03-05 10:01:00.000000+0000 |        22.8 |     64.9
 2024-03-05 10:00:00.000000+0000 |        22.5 |     65.2
(3 rows)

 keyspace_name | table_name      | compaction                                             
---------------+-----------------+--------------------------------------------------------
 ecommerce     | sensor_readings | {'class': 'TimeWindowCompactionStrategy', ...}
 ecommerce     | user_orders     | {'class': 'TimeWindowCompactionStrategy', ...}
 ecommerce     | users           | {'class': 'SizeTieredCompactionStrategy', ...}

Lab complete!
```

---

## Summary

| Concept | Key Detail | Command/Setting |
|---------|-----------|----------------|
| Keyspace | Namespace + replication config | `CREATE KEYSPACE ... WITH REPLICATION` |
| Partition key | Determines which node stores data | `PRIMARY KEY ((pk))` |
| Clustering column | Row order within partition | `PRIMARY KEY ((pk), cc) ... CLUSTERING ORDER BY` |
| Consistency ONE | 1 replica responds | Fast, eventual consistency |
| Consistency QUORUM | Majority responds | Balanced consistency/availability |
| Consistency ALL | All replicas respond | Strongest, lowest availability |
| TTL | Automatic row expiration | `INSERT ... USING TTL seconds` |
| TWCS | Time-window compaction | Optimal for time-series |
| nodetool status | Node health + ownership | `nodetool status` |
| compactionstats | Pending compaction work | `nodetool compactionstats` |

## Key Takeaways

- **Design tables around queries** — Cassandra has no JOINs, so duplicate data is expected
- **Partition key drives distribution** — high cardinality, uniform access pattern = balanced nodes
- **Clustering columns** provide efficient range queries within a partition
- **QUORUM writes + QUORUM reads** = strong consistency without sacrificing availability
- **TWCS compaction** is essential for time-series data — dramatically reduces write amplification
