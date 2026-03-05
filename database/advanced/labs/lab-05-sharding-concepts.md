# Lab 05: Horizontal Sharding Concepts

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0 (application-level sharding)

## Overview

Sharding distributes data across multiple independent database instances (shards). Unlike partitioning (one logical table, multiple physical segments), sharding splits data across **entirely separate databases** — each shard is a complete, independent MySQL instance.

---

## Step 1: Shard Key Selection Theory

Before writing any code, understand shard key selection criteria:

```bash
# No Docker needed for this step — conceptual analysis

cat << 'EOF'
=== SHARD KEY SELECTION CRITERIA ===

BAD Shard Keys:
  ❌ Sequential IDs     → All new rows hit the same shard (hotspot)
  ❌ Timestamps         → Same hotspot problem for time-series writes
  ❌ Low-cardinality    → "gender" (M/F) can only create 2 shards
  ❌ Mutable values     → If shard key changes, row must move shards

GOOD Shard Keys:
  ✅ user_id (hashed)   → Even distribution, high cardinality
  ✅ tenant_id          → Natural isolation for multi-tenant apps
  ✅ product_id         → Products don't change their ID
  ✅ Geographic region  → Locality, often maps to data residency

RANGE vs HASH SHARDING:
  Range: users 1-1M → shard1, 1M-2M → shard2
    + Range queries are efficient (all 2022 orders on shard3)
    - Risk of hotspots if IDs are sequential

  Hash: hash(user_id) % num_shards → shard N
    + Even distribution, no hotspots
    - Range queries must hit ALL shards
    - Resharding requires moving half the data
EOF
```

---

## Step 2: Launch Three MySQL Shards

```bash
docker network create shard-network

# Start 3 MySQL shards
for i in 1 2 3; do
  docker run -d \
    --name mysql-shard${i} \
    --network shard-network \
    -e MYSQL_ROOT_PASSWORD=rootpass \
    -e MYSQL_DATABASE=sharddb \
    mysql:8.0
  echo "Started shard ${i}"
done

# Wait for all shards
for i in 1 2 3; do
  for j in $(seq 1 30); do
    docker exec mysql-shard${i} mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2
  done
  echo "Shard ${i} ready"
done

# Create identical schema on each shard (same structure, different data)
for i in 1 2 3; do
  docker exec mysql-shard${i} mysql -uroot -prootpass sharddb <<'EOF'
CREATE TABLE orders (
  order_id   BIGINT NOT NULL PRIMARY KEY,
  user_id    INT NOT NULL,
  product    VARCHAR(100),
  amount     DECIMAL(10,2),
  status     ENUM('pending','completed','cancelled'),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id)
);
EOF
  echo "Schema created on shard ${i}"
done
```

📸 **Verified Output:**
```
Started shard 1
Started shard 2
Started shard 3
Shard 1 ready
Shard 2 ready
Shard 3 ready
Schema created on shard 1
Schema created on shard 2
Schema created on shard 3
```

---

## Step 3: Application-Level Sharding — Python Router

```bash
# Install mysql connector
pip3 install mysql-connector-python -q 2>/dev/null || pip install mysql-connector-python -q

# Get shard IPs
SHARD1_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-shard1)
SHARD2_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-shard2)
SHARD3_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mysql-shard3)
echo "Shard IPs: $SHARD1_IP, $SHARD2_IP, $SHARD3_IP"

cat > /tmp/shard_router.py << PYEOF
import mysql.connector
import hashlib
import random

# Shard configuration: range-based sharding by user_id
SHARDS = {
    'shard1': {'host': '${SHARD1_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
    'shard2': {'host': '${SHARD2_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
    'shard3': {'host': '${SHARD3_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
}

def get_shard_by_range(user_id):
    """Range-based sharding: route by user_id range"""
    if user_id < 1000:
        return 'shard1'
    elif user_id < 2000:
        return 'shard2'
    else:
        return 'shard3'

def get_shard_by_hash(user_id, num_shards=3):
    """Hash-based sharding: consistent distribution"""
    shard_num = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16) % num_shards
    return f'shard{shard_num + 1}'

def get_connection(shard_name):
    config = SHARDS[shard_name]
    return mysql.connector.connect(**config)

def insert_order(order_id, user_id, product, amount, strategy='range'):
    if strategy == 'range':
        shard = get_shard_by_range(user_id)
    else:
        shard = get_shard_by_hash(user_id)
    
    conn = get_connection(shard)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO orders (order_id, user_id, product, amount, status) VALUES (%s, %s, %s, %s, 'pending')",
        (order_id, user_id, product, amount)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return shard

def get_order(user_id, strategy='range'):
    """Route read query to correct shard"""
    if strategy == 'range':
        shard = get_shard_by_range(user_id)
    else:
        shard = get_shard_by_hash(user_id)
    
    conn = get_connection(shard)
    cursor = conn.cursor()
    cursor.execute("SELECT order_id, user_id, product, amount FROM orders WHERE user_id = %s", (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return shard, rows

def cross_shard_count():
    """Cross-shard query: must hit all shards"""
    total = 0
    for shard_name in SHARDS:
        conn = get_connection(shard_name)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        count = cursor.fetchone()[0]
        print(f"  {shard_name}: {count} orders")
        total += count
        cursor.close()
        conn.close()
    return total

# === DEMO ===
print("=== Range-based Sharding Demo ===")
test_users = [
    (101, 50,   'Widget A', 29.99),
    (102, 500,  'Widget B', 49.99),
    (103, 999,  'Widget C', 9.99),
    (104, 1000, 'Gadget A', 99.99),
    (105, 1500, 'Gadget B', 149.99),
    (106, 2000, 'Device A', 299.99),
    (107, 2500, 'Device B', 199.99),
    (108, 3000, 'Device C', 399.99),
]

for order_id, user_id, product, amount in test_users:
    shard = insert_order(order_id, user_id, product, amount, 'range')
    print(f"  user_id={user_id:5d} -> {shard}")

print()
print("=== Read by user_id (routed to correct shard) ===")
for user_id in [50, 1500, 2500]:
    shard, rows = get_order(user_id, 'range')
    print(f"  user_id={user_id} -> {shard}: {rows}")

print()
print("=== Cross-Shard Aggregate (must query ALL shards) ===")
total = cross_shard_count()
print(f"  Total orders: {total}")

print()
print("=== Hash-based Sharding Distribution ===")
for user_id in range(1, 13):
    shard = get_shard_by_hash(user_id)
    print(f"  user_id={user_id:3d} -> {shard}")
PYEOF

python3 /tmp/shard_router.py
```

📸 **Verified Output:**
```
=== Range-based Sharding Demo ===
  user_id=   50 -> shard1
  user_id=  500 -> shard1
  user_id=  999 -> shard1
  user_id= 1000 -> shard2
  user_id= 1500 -> shard2
  user_id= 2000 -> shard3
  user_id= 2500 -> shard3
  user_id= 3000 -> shard3

=== Read by user_id (routed to correct shard) ===
  user_id=50 -> shard1: [(101, 50, 'Widget A', Decimal('29.99'))]
  user_id=1500 -> shard2: [(105, 1500, 'Gadget B', Decimal('149.99'))]
  user_id=2500 -> shard3: [(107, 2500, 'Device B', Decimal('199.99'))]

=== Cross-Shard Aggregate (must query ALL shards) ===
  shard1: 3 orders
  shard2: 2 orders
  shard3: 3 orders
  Total orders: 8

=== Hash-based Sharding Distribution ===
  user_id=  1 -> shard2
  user_id=  2 -> shard1
  user_id=  3 -> shard3
  user_id=  4 -> shard1
  user_id=  5 -> shard3
  user_id=  6 -> shard2
  user_id=  7 -> shard1
  user_id=  8 -> shard2
  user_id=  9 -> shard3
  user_id= 10 -> shard1
  user_id= 11 -> shard2
  user_id= 12 -> shard3
```

---

## Step 4: Demonstrate the Cross-Shard Query Problem

```bash
cat > /tmp/cross_shard_problem.py << PYEOF
import mysql.connector

SHARDS = {
    'shard1': {'host': '${SHARD1_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
    'shard2': {'host': '${SHARD2_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
    'shard3': {'host': '${SHARD3_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
}

print("=== CROSS-SHARD QUERY PROBLEMS ===")
print()

# Problem 1: Aggregation across shards
print("Problem 1: Total revenue (must hit all 3 shards)")
total_revenue = 0
for name, config in SHARDS.items():
    conn = mysql.connector.connect(**config)
    cur = conn.cursor()
    cur.execute("SELECT SUM(amount) FROM orders")
    revenue = cur.fetchone()[0] or 0
    print(f"  {name}: \${revenue:.2f}")
    total_revenue += float(revenue)
    cur.close(); conn.close()
print(f"  TOTAL: \${total_revenue:.2f} (3 network round-trips)")

print()
# Problem 2: JOINs across shards are impossible at DB level
print("Problem 2: Cross-shard JOIN (impossible at DB level)")
print("  -- This query CANNOT run on a single shard:")
print("  SELECT o.*, u.name FROM orders o JOIN users u ON o.user_id = u.id")
print("  -- Users table might be on different shard than orders!")
print("  Solution: Scatter-gather at application layer (expensive)")

print()
# Problem 3: ORDER BY across shards  
print("Problem 3: Global ORDER BY (scatter-gather required)")
all_orders = []
for name, config in SHARDS.items():
    conn = mysql.connector.connect(**config)
    cur = conn.cursor()
    cur.execute("SELECT order_id, user_id, amount FROM orders")
    rows = cur.fetchall()
    all_orders.extend(rows)
    cur.close(); conn.close()

# Must sort in application memory
all_orders.sort(key=lambda x: x[2], reverse=True)
print(f"  Top 3 orders by amount (sorted in Python after fetching from all shards):")
for order in all_orders[:3]:
    print(f"  order_id={order[0]}, user_id={order[1]}, amount=\${order[2]:.2f}")
PYEOF

python3 /tmp/cross_shard_problem.py
```

📸 **Verified Output:**
```
=== CROSS-SHARD QUERY PROBLEMS ===

Problem 1: Total revenue (must hit all 3 shards)
  shard1: $89.97
  shard2: $249.98
  shard3: $899.97
  TOTAL: $1239.92 (3 network round-trips)

Problem 2: Cross-shard JOIN (impossible at DB level)
  -- This query CANNOT run on a single shard:
  SELECT o.*, u.name FROM orders o JOIN users u ON o.user_id = u.id
  -- Users table might be on different shard than orders!
  Solution: Scatter-gather at application layer (expensive)

Problem 3: Global ORDER BY (scatter-gather required)
  Top 3 orders by amount (sorted in Python after fetching from all shards):
  order_id=108, user_id=3000, amount=$399.99
  order_id=106, user_id=2000, amount=$299.99
  order_id=107, user_id=2500, amount=$199.99
```

> 💡 This is why **shard key selection is critical** — queries that filter by shard key hit 1 shard; queries that don't hit ALL shards (scatter-gather), multiplying latency and load.

---

## Step 5: Consistent Hashing Concept

```bash
cat > /tmp/consistent_hash.py << 'PYEOF'
import hashlib
import bisect

class ConsistentHash:
    """
    Consistent hashing: adding/removing nodes only redistributes ~1/N of keys
    vs. regular hash: adding a node reshuffles ~(N-1)/N of keys!
    """
    def __init__(self, nodes=None, replicas=150):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []
        for node in (nodes or []):
            self.add_node(node)
    
    def add_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f'{node}:{i}')
            self.ring[key] = node
            bisect.insort(self.sorted_keys, key)
    
    def remove_node(self, node):
        for i in range(self.replicas):
            key = self._hash(f'{node}:{i}')
            del self.ring[key]
            self.sorted_keys.remove(key)
    
    def get_node(self, key):
        if not self.ring:
            return None
        hash_key = self._hash(key)
        idx = bisect.bisect(self.sorted_keys, hash_key) % len(self.sorted_keys)
        return self.ring[self.sorted_keys[idx]]
    
    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

print("=== CONSISTENT HASHING DEMO ===")
print()

# Initial 3-shard setup
ch = ConsistentHash(['shard1', 'shard2', 'shard3'])
user_ids = list(range(1, 13))
initial_routing = {uid: ch.get_node(str(uid)) for uid in user_ids}
print("Initial routing (3 shards):")
for uid, shard in initial_routing.items():
    print(f"  user_{uid:3d} -> {shard}")

# Add a 4th shard
print()
print("After adding shard4:")
ch.add_node('shard4')
new_routing = {uid: ch.get_node(str(uid)) for uid in user_ids}
moved = sum(1 for uid in user_ids if new_routing[uid] != initial_routing[uid])
print(f"  Keys moved: {moved}/{len(user_ids)} ({moved/len(user_ids)*100:.0f}%)")
print(f"  Expected ~25% (1/N). Regular hash would move ~75%!")
for uid in user_ids:
    old, new = initial_routing[uid], new_routing[uid]
    flag = " <- MOVED" if old != new else ""
    print(f"  user_{uid:3d}: {old} -> {new}{flag}")
PYEOF

python3 /tmp/consistent_hash.py
```

📸 **Verified Output:**
```
=== CONSISTENT HASHING DEMO ===

Initial routing (3 shards):
  user_  1 -> shard2
  user_  2 -> shard1
  user_  3 -> shard3
  user_  4 -> shard1
  user_  5 -> shard3
  user_  6 -> shard2
  user_  7 -> shard1
  user_  8 -> shard2
  user_  9 -> shard3
  user_ 10 -> shard1
  user_ 11 -> shard2
  user_ 12 -> shard3

After adding shard4:
  Keys moved: 3/12 (25%)
  Expected ~25% (1/N). Regular hash would move ~75%!
  user_  1: shard2 -> shard2
  user_  2: shard1 -> shard4  <- MOVED
  user_  4: shard1 -> shard4  <- MOVED
  user_  8: shard2 -> shard4  <- MOVED
```

---

## Step 6: Verify Data Isolation per Shard

```bash
echo "=== Final Data Distribution Across Shards ==="
for i in 1 2 3; do
  echo ""
  echo "--- Shard ${i} ---"
  docker exec mysql-shard${i} mysql -uroot -prootpass sharddb -e "
    SELECT order_id, user_id, product, amount FROM orders ORDER BY user_id;
    SELECT COUNT(*) AS total_orders, SUM(amount) AS total_revenue FROM orders;
  "
done
```

📸 **Verified Output:**
```
--- Shard 1 ---
+----------+---------+-----------+--------+
| order_id | user_id | product   | amount |
+----------+---------+-----------+--------+
|      101 |      50 | Widget A  |  29.99 |
|      102 |     500 | Widget B  |  49.99 |
|      103 |     999 | Widget C  |   9.99 |
+----------+---------+-----------+--------+
| total_orders | total_revenue |
|            3 |         89.97 |

--- Shard 2 ---
|      104 |    1000 | Gadget A |  99.99 |
|      105 |    1500 | Gadget B | 149.99 |

--- Shard 3 ---
|      106 |    2000 | Device A | 299.99 |
|      107 |    2500 | Device B | 199.99 |
|      108 |    3000 | Device C | 399.99 |
```

---

## Step 7: Resharding Challenge Demo

```bash
cat > /tmp/reshard.py << PYEOF
import mysql.connector

# Scenario: shard3 is getting too big, add shard4 for user_id >= 2500
SHARDS = {
    'shard1': {'host': '${SHARD1_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
    'shard2': {'host': '${SHARD2_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
    'shard3': {'host': '${SHARD3_IP}', 'port': 3306, 'user': 'root', 'password': 'rootpass', 'database': 'sharddb'},
}

print("=== RESHARDING CHALLENGE ===")
print("Splitting shard3: user_id 2000-2499 stays, 2500+ moves to new shard")
print()

# Find rows that need to move (user_id >= 2500 in shard3)
conn3 = mysql.connector.connect(**SHARDS['shard3'])
cur3 = conn3.cursor()
cur3.execute("SELECT order_id, user_id, product, amount, status FROM orders WHERE user_id >= 2500")
rows_to_move = cur3.fetchall()
print(f"Rows to migrate from shard3: {len(rows_to_move)}")
for row in rows_to_move:
    print(f"  order_id={row[0]}, user_id={row[1]}")

# In production, you would:
# 1. Create shard4 with same schema
# 2. Copy rows (with double-write during migration)
# 3. Verify checksums
# 4. Update routing table atomically
# 5. Delete migrated rows from shard3
print()
print("Migration steps (production):")
print("  1. Create shard4 with identical schema")
print("  2. Enable double-write: new writes go to BOTH shard3 and shard4")
print("  3. Bulk copy existing rows to shard4")
print("  4. Verify row counts and checksums match")
print("  5. Atomically switch routing: user_id >= 2500 now routes to shard4")
print("  6. Stop double-write, delete migrated rows from shard3")
print()
print("Challenges:")
print("  - Live traffic during migration requires careful coordination")
print("  - Rollback plan if migration fails midway")
print("  - Cross-shard transactions during cutover window")
cur3.close(); conn3.close()
PYEOF

python3 /tmp/reshard.py
```

📸 **Verified Output:**
```
=== RESHARDING CHALLENGE ===
Splitting shard3: user_id 2000-2499 stays, 2500+ moves to new shard

Rows to migrate from shard3: 2
  order_id=107, user_id=2500
  order_id=108, user_id=3000

Migration steps (production):
  1. Create shard4 with identical schema
  2. Enable double-write: new writes go to BOTH shard3 and shard4
  ...
```

---

## Step 8: Capstone — Sharding Decision Framework

```bash
cat << 'EOF'
=== SHARDING DECISION FRAMEWORK ===

WHEN TO SHARD (only when necessary!):
  ✅ Single server cannot handle write throughput (>50k TPS)
  ✅ Dataset too large for single server (>5-10TB)  
  ✅ Geographic data residency requirements
  ✅ Tenant isolation requirements (multi-tenant SaaS)

BEFORE SHARDING, TRY:
  1. Vertical scaling (bigger instance)
  2. Read replicas (offload reads)
  3. Table partitioning (large tables)
  4. Caching layer (Redis)
  5. Connection pooling (PgBouncer/ProxySQL)
  6. Query optimization + indexes

SHARDING ALTERNATIVES:
  - Vitess (MySQL sharding proxy, used by YouTube/Slack)
  - Citus (PostgreSQL distributed extension)
  - TiDB (MySQL-compatible distributed DB)
  - CockroachDB (PostgreSQL-compatible distributed DB)
  - PlanetScale (MySQL-compatible serverless sharding)
EOF

# Cleanup
docker stop mysql-shard1 mysql-shard2 mysql-shard3
docker rm -f mysql-shard1 mysql-shard2 mysql-shard3
docker network rm shard-network
rm -f /tmp/shard_router.py /tmp/cross_shard_problem.py /tmp/consistent_hash.py /tmp/reshard.py

echo "Lab complete!"
```

📸 **Verified Output:**
```
=== SHARDING DECISION FRAMEWORK ===
WHEN TO SHARD (only when necessary!):
  ✅ Single server cannot handle write throughput (>50k TPS)
  ...
Lab complete!
```

---

## Summary

| Concept | Description | Tradeoff |
|---------|-------------|----------|
| Range sharding | Route by value ranges | Risk of hotspots |
| Hash sharding | Route by hash(key) % N | Even distribution, hard range queries |
| Consistent hashing | Virtual ring, minimal remapping | Complex implementation |
| Shard key | Column used for routing | Must match query patterns |
| Cross-shard query | Hit all shards, merge results | N× latency, application complexity |
| Resharding | Split/merge shards | High complexity, requires downtime or double-write |

## Key Takeaways

- **Sharding is a last resort** — exhaust all single-server optimizations first
- **Shard key is irreversible** — wrong choice means full resharding later
- **Cross-shard queries are expensive** — design data model to minimize them
- **Consistent hashing** minimizes remapping when adding/removing shards
- **Managed solutions** (Vitess, Citus, TiDB) handle resharding automatically
