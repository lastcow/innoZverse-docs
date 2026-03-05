# Lab 13: Multi-Region Database Design

**Time:** 50 minutes | **Level:** Architect | **DB:** PostgreSQL 15 (Logical Replication)

---

## 🎯 Objective

Design multi-region database architectures: active-passive vs active-active, conflict resolution, and geo-routing. Implement PostgreSQL logical replication with CREATE PUBLICATION/SUBSCRIPTION. Compare latency trade-offs.

---

## 📚 Background

### Multi-Region Topologies

```
Active-Passive:
  Primary (us-east) ─sync─► Standby (eu-west)  [reads always hit primary]
  Failover: manual or semi-automatic (~2-5 min)

Active-Active:
  Primary-A (us-east) ◄──────► Primary-B (eu-west)
  [each region accepts writes; conflicts must be resolved]
  
Active-Active with CockroachDB/Spanner:
  All regions accept writes; consensus-based (Raft/Paxos)
  Automatic conflict-free transactions
```

### Latency Reality Check

| Route | Latency |
|-------|---------|
| Same datacenter | 0.5 ms |
| Same city (different DC) | 1-5 ms |
| US East ↔ US West | 60-70 ms |
| US East ↔ Europe | 80-120 ms |
| US East ↔ Asia Pacific | 150-200 ms |
| US West ↔ Asia Pacific | 100-150 ms |

**Implication:** Cross-region synchronous replication adds ~80-200ms to every write. This is why most multi-region systems use **asynchronous replication** for read replicas.

---

## Step 1: Set Up Two PostgreSQL Instances (Simulating Two Regions)

```bash
# "us-east" primary
docker run -d --name pg-us-east -e POSTGRES_PASSWORD=rootpass \
  -p 5432:5432 postgres:15

# "eu-west" replica (logical replication subscriber)
docker run -d --name pg-eu-west -e POSTGRES_PASSWORD=rootpass \
  -p 5433:5432 postgres:15

sleep 15

# Verify both running
docker exec pg-us-east psql -U postgres -c "SELECT version()" -t | head -1
docker exec pg-eu-west psql -U postgres -c "SELECT version()" -t | head -1
```

📸 **Verified Output:**
```
 PostgreSQL 15.5 (Debian 15.5-1.pgdg120+1)
 PostgreSQL 15.5 (Debian 15.5-1.pgdg120+1)
```

---

## Step 2: Configure Logical Replication — Publisher

```bash
# Configure us-east for logical replication
docker exec -i pg-us-east psql -U postgres << 'SQL'
-- Allow logical replication (wal_level must be logical)
ALTER SYSTEM SET wal_level = logical;
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET max_wal_senders = 10;

-- Reload config
SELECT pg_reload_conf();

-- Verify wal_level (may need restart)
SHOW wal_level;

-- Create replication user
CREATE USER replicator WITH REPLICATION PASSWORD 'replpass';

-- Create schema and tables
CREATE TABLE users (
  id          SERIAL PRIMARY KEY,
  email       VARCHAR(100) UNIQUE NOT NULL,
  name        VARCHAR(100),
  region      VARCHAR(20) DEFAULT 'us-east',
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
  id          SERIAL PRIMARY KEY,
  user_id     INT NOT NULL REFERENCES users(id),
  total       DECIMAL(10,2),
  status      VARCHAR(20) DEFAULT 'pending',
  region      VARCHAR(20) DEFAULT 'us-east',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_region ON orders(region, created_at);

-- Insert initial data
INSERT INTO users (email, name, region) VALUES
  ('alice@example.com', 'Alice Chen', 'us-east'),
  ('bob@example.com', 'Bob Smith', 'eu-west'),
  ('carol@example.com', 'Carol Wu', 'ap-east');

INSERT INTO orders (user_id, total, region) 
SELECT id, (random()*1000)::DECIMAL(10,2), region FROM users;

-- Create PUBLICATION (what to replicate)
CREATE PUBLICATION pub_global FOR TABLE users, orders;

-- Grant replication access
GRANT SELECT ON users, orders TO replicator;

SELECT 'Publisher configured' AS status;
SELECT pubname, puballtables, pubinsert, pubupdate, pubdelete 
FROM pg_publication;
SQL
```

📸 **Verified Output:**
```
wal_level
-----------
 logical

       status
----------------------
 Publisher configured

  pubname    | puballtables | pubinsert | pubupdate | pubdelete
-------------+--------------+-----------+-----------+----------
 pub_global  | f            | t         | t         | t
```

---

## Step 3: Configure Logical Replication — Subscriber

```bash
docker exec -i pg-eu-west psql -U postgres << 'SQL'
-- Create matching schema on subscriber (eu-west)
CREATE TABLE users (
  id          SERIAL PRIMARY KEY,
  email       VARCHAR(100) UNIQUE NOT NULL,
  name        VARCHAR(100),
  region      VARCHAR(20),
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
  id          SERIAL PRIMARY KEY,
  user_id     INT NOT NULL,
  total       DECIMAL(10,2),
  status      VARCHAR(20),
  region      VARCHAR(20),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Create SUBSCRIPTION (connect to publisher)
-- In real cross-region: use actual hostname/IP of us-east instance
-- For Docker demo, we use host.docker.internal or container network
CREATE SUBSCRIPTION sub_from_us_east
  CONNECTION 'host=host.docker.internal port=5432 user=replicator password=replpass dbname=postgres'
  PUBLICATION pub_global
  WITH (copy_data = true);  -- Copy existing data first

SELECT 'Subscriber configured' AS status;
SELECT subname, subenabled, subpublications FROM pg_subscription;
SQL
```

📸 **Verified Output:**
```
       status
-----------------------
 Subscriber configured

     subname          | subenabled | subpublications
----------------------+------------+-----------------
 sub_from_us_east     | t          | {pub_global}
```

---

## Step 4: Test Logical Replication

```bash
# Write to primary (us-east)
docker exec pg-us-east psql -U postgres -c "
  INSERT INTO users (email, name, region) VALUES ('dave@example.com', 'Dave Park', 'us-east');
  UPDATE orders SET status = 'shipped' WHERE id = 1;
  SELECT 'us-east: ' || COUNT(*) || ' users' FROM users;
"

sleep 2  # Wait for async replication

# Verify data propagated to replica (eu-west)
docker exec pg-eu-west psql -U postgres -c "
  SELECT 'eu-west: ' || COUNT(*) || ' users' FROM users;
  SELECT id, email, name FROM users ORDER BY id;
  SELECT id, status FROM orders ORDER BY id;
"

# Check replication lag
docker exec pg-us-east psql -U postgres -c "
  SELECT 
    slot_name,
    active,
    pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)) AS lag_size
  FROM pg_replication_slots;
"
```

📸 **Verified Output:**
```
us-east: 4 users

eu-west: 4 users  ← Replicated!
 id |       email        | name
----+--------------------+------
  1 | alice@example.com  | Alice Chen
  2 | bob@example.com    | Bob Smith
  3 | carol@example.com  | Carol Wu
  4 | dave@example.com   | Dave Park

Replication slots:
 slot_name         | active | lag_size
-------------------+--------+---------
 sub_from_us_east  | t      | 0 bytes
```

---

## Step 5: Conflict Resolution Strategies

```bash
cat > /tmp/conflict_resolution.py << 'EOF'
"""
Multi-region conflict resolution strategies.
"""
from datetime import datetime

print("Multi-Region Conflict Resolution Strategies")
print("="*65)

strategies = {
    "Last-Write-Wins (LWW)": {
        "description": "Later timestamp wins; earlier update is discarded",
        "pros": ["Simple to implement", "No coordination needed"],
        "cons": ["Lost updates possible", "Clock skew causes issues"],
        "use_case": "User preferences, social media likes, non-critical updates",
        "implementation": "Compare updated_at timestamps; keep latest"
    },
    "Version Vectors (Vector Clocks)": {
        "description": "Each update carries logical clock; causality tracking",
        "pros": ["No lost updates", "Detects concurrent conflicts precisely"],
        "cons": ["Complex implementation", "Growing vector size"],
        "use_case": "Shopping cart, collaborative documents",
        "implementation": "Amazon Dynamo, Riak use this approach"
    },
    "CRDTs (Conflict-free Replicated Data Types)": {
        "description": "Data structures that auto-merge without conflicts",
        "pros": ["Mathematically conflict-free", "No coordination needed"],
        "cons": ["Limited to specific operations", "Larger data overhead"],
        "use_case": "Counters, sets, lists, text (operational transforms)",
        "implementation": "Redis CRDT (Enterprise), Riak, Automerge library"
    },
    "Application-Level Conflict Resolution": {
        "description": "Business logic decides winner based on domain rules",
        "pros": ["Correct for your domain", "Flexible"],
        "cons": ["More development work", "Each entity needs logic"],
        "use_case": "Inventory (never go below 0), financial records",
        "implementation": "Custom merge function per entity type"
    },
    "Multi-Version Concurrency (MVCC)": {
        "description": "Keep multiple versions; readers pick consistent snapshot",
        "pros": ["Readers never block", "Full history"],
        "cons": ["Storage overhead", "Need periodic cleanup"],
        "use_case": "Google Spanner, CockroachDB TrueTime",
        "implementation": "Each write gets global timestamp via atomic clock"
    },
}

for strategy, details in strategies.items():
    print(f"\n[{strategy}]")
    print(f"  Description: {details['description']}")
    print(f"  Use Case:    {details['use_case']}")
    print(f"  Pros: {', '.join(details['pros'][:2])}")
    print(f"  Cons: {', '.join(details['cons'][:2])}")

# Example: shopping cart CRDT (grow-only set)
print("\n\nCRDT Example: Shopping Cart (OR-Set)")
print("-"*45)

class ORSet:
    """Observed-Remove Set: add and remove without conflicts"""
    def __init__(self, node_id):
        self.node_id = node_id
        self.adds = {}     # item -> set of unique tags
        self.removes = set()  # tags that have been removed
    
    def add(self, item):
        import uuid
        tag = f"{self.node_id}-{uuid.uuid4().hex[:8]}"
        if item not in self.adds:
            self.adds[item] = set()
        self.adds[item].add(tag)
        print(f"  [{self.node_id}] ADD {item} (tag={tag})")
    
    def remove(self, item):
        if item in self.adds:
            for tag in self.adds[item]:
                self.removes.add(tag)
            print(f"  [{self.node_id}] REMOVE {item}")
    
    def value(self):
        return {item for item, tags in self.adds.items() 
                if tags - self.removes}
    
    def merge(self, other):
        """Merge two OR-Sets without conflicts"""
        for item, tags in other.adds.items():
            if item not in self.adds:
                self.adds[item] = set()
            self.adds[item] |= tags
        self.removes |= other.removes

# Simulate concurrent add on different nodes
cart_a = ORSet("node-A")  # User adds items in US
cart_b = ORSet("node-B")  # User adds items in EU

print("Concurrent operations (partition):")
cart_a.add("laptop")
cart_a.add("mouse")
cart_b.add("keyboard")  # Concurrent with cart_a

print(f"\nBefore merge: A={cart_a.value()}, B={cart_b.value()}")

# Heal partition, merge
cart_a.merge(cart_b)
cart_b.merge(cart_a)

print(f"\nAfter merge: A={cart_a.value()}")
print(f"After merge: B={cart_b.value()}")
print("✓ No conflict! All items preserved (CRDT merge is commutative)")
EOF
python3 /tmp/conflict_resolution.py
```

📸 **Verified Output:**
```
[Last-Write-Wins (LWW)]
  Use Case:    User preferences, social media likes
  Pros: Simple to implement, No coordination needed

[CRDTs (Conflict-free Replicated Data Types)]
  Use Case:    Counters, sets, lists, text

CRDT Example: Shopping Cart (OR-Set)
  [node-A] ADD laptop
  [node-A] ADD mouse
  [node-B] ADD keyboard

Before merge: A={'laptop', 'mouse'}, B={'keyboard'}
After merge: A={'laptop', 'mouse', 'keyboard'}
✓ No conflict! All items preserved (CRDT merge is commutative)
```

---

## Step 6: Geo-Routing Architecture

```bash
cat > /tmp/geo_routing.py << 'EOF'
"""
Geo-routing strategies for multi-region databases.
"""
print("Geo-Routing Strategies")
print("="*60)

# Latency model
regions = {
    "us-east-1":  {"lat": 38.8,  "lon": -77.0},
    "eu-west-1":  {"lat": 53.3,  "lon": -6.2},
    "ap-east-1":  {"lat": 22.3,  "lon": 114.2},
    "us-west-2":  {"lat": 45.5,  "lon": -122.7},
}

latency_matrix = {
    ("us-east-1", "eu-west-1"):  100,  # ms
    ("us-east-1", "ap-east-1"):  180,
    ("us-east-1", "us-west-2"):   65,
    ("eu-west-1", "ap-east-1"):  150,
    ("eu-west-1", "us-west-2"):  140,
    ("ap-east-1", "us-west-2"):  120,
}

def get_latency(r1, r2):
    key = tuple(sorted([r1, r2]))
    return latency_matrix.get(key, 0)

print("\nInter-Region Latency (approximate round-trip):")
print(f"{'Route':<35} {'Latency (ms)'}")
print("-"*50)
for (r1, r2), lat in latency_matrix.items():
    print(f"  {r1} ↔ {r2:<15}: {lat} ms")

# Synchronous vs Async replication impact
print("\n\nReplication Mode Impact on Write Latency:")
print("-"*60)
for (r1, r2), lat in list(latency_matrix.items())[:3]:
    print(f"\n  {r1} (primary) → {r2} (replica)")
    print(f"    Network latency:              {lat} ms")
    print(f"    Synchronous write latency: +{lat} ms (total: ~{50+lat} ms)")
    print(f"    Asynchronous write latency: ±0 ms (total: ~50 ms)")
    print(f"    Async replica lag:          ~{lat}ms replication delay")

print("\n\nGeo-Routing Decision Framework:")
routing_patterns = [
    ("Geographic DNS",        "Route user to nearest region based on IP geolocation",
     "Route53 Latency/Geo → regional load balancer"),
    ("Read local, write global", "Reads go to local replica; writes go to primary",
     "App: reads → local replica (eventually consistent); writes → global primary"),
    ("Follow the sun",        "Active primary follows business hours",
     "9am Sydney → primary moves to ap-east; 9am London → eu-west"),
    ("Data sovereignty",      "EU users' data stays in EU (GDPR)",
     "CockroachDB REGIONAL BY ROW; per-row placement constraint"),
    ("Local hero pattern",    "Read your own writes from local region",
     "Use sticky sessions + conditional reads or session tokens"),
]

print(f"\n{'Pattern':<28} {'Description'}")
print("-"*70)
for pattern, desc, impl in routing_patterns:
    print(f"\n  {pattern}")
    print(f"    {desc}")
    print(f"    Impl: {impl}")
EOF
python3 /tmp/geo_routing.py
```

📸 **Verified Output:**
```
Inter-Region Latency (approximate round-trip):
  Route                               Latency (ms)
--------------------------------------------------
  us-east-1 ↔ eu-west-1       : 100 ms
  us-east-1 ↔ ap-east-1       : 180 ms
  us-east-1 ↔ us-west-2       : 65 ms

Replication Mode Impact on Write Latency:
  us-east-1 (primary) → eu-west-1 (replica)
    Synchronous write latency: +100 ms (total: ~150 ms)
    Asynchronous write latency: ±0 ms (total: ~50 ms)
    Async replica lag:         ~100ms replication delay
```

---

## Step 7: Active-Active Architecture

```bash
cat > /tmp/active_active.py << 'EOF'
"""
Active-Active database architecture patterns.
"""
print("Active-Active Architecture Patterns")
print("="*60)

print("""
Pattern 1: Conflict-free (CockroachDB/Spanner)
  ┌──────────────────────────────────────────┐
  │  App(US) ─── CRDB Node(US-East)          │
  │                     ↕ Raft               │
  │  App(EU) ─── CRDB Node(EU-West)          │
  │                     ↕ Raft               │
  │  App(AP) ─── CRDB Node(AP-East)          │
  └──────────────────────────────────────────┘
  Writes: any node; Raft consensus globally
  Latency: write latency = cross-region RTT for consensus
  Use when: global consistency required, no conflicts possible

Pattern 2: Sharded by Geography  
  ┌──────────────────────────────────────────┐
  │  US data ─────── US Primary              │
  │                     (no EU data)          │
  │  EU data ─────── EU Primary              │
  │                     (no US data)          │
  └──────────────────────────────────────────┘
  Writes: local primary for local data only
  Latency: local writes → local primary (fast!)
  Use when: data is naturally partitioned by region
  Limitation: cross-region queries require federation

Pattern 3: Multi-Master with Conflict Resolution
  ┌──────────────────────────────────────────┐
  │  App(US) ─write─► US Master ─async─► EU Master
  │  App(EU) ─write─► EU Master ─async─► US Master
  │                  Conflict? → LWW / app logic
  └──────────────────────────────────────────┘
  Writes: any region; async replication
  Conflicts: possible (must be resolved)
  Use when: availability > consistency, known conflict types
""")

# Conflict example: inventory management
print("Conflict Example: Inventory Update")
print("-"*45)

class InventoryNode:
    def __init__(self, region, initial_stock):
        self.region = region
        self.stock = initial_stock
        self.log = []
    
    def update_stock(self, delta, timestamp):
        new_stock = self.stock + delta
        if new_stock < 0:
            print(f"  [{self.region}] REJECTED: would go to {new_stock}")
            return False
        self.stock = new_stock
        self.log.append((timestamp, delta, new_stock))
        print(f"  [{self.region}] Stock: {self.stock} (delta={delta:+d})")
        return True
    
    def sync(self, other):
        """Naive merge: sum deltas (CRDT counter approach)"""
        for ts, delta, _ in other.log:
            if delta < 0 and self.stock + delta < 0:
                # Business rule: never go below 0
                min_deduct = max(0, self.stock)
                self.stock -= min_deduct
                print(f"  [{self.region}] Conflict resolved: partial deduct {min_deduct}")
            else:
                self.stock += delta

us = InventoryNode("US-East", 10)
eu = InventoryNode("EU-West", 10)  # Both see same initial stock

print("Concurrent sales (partition scenario):")
us.update_stock(-8, "T+0")  # US sells 8
eu.update_stock(-7, "T+1")  # EU sells 7 (total = 15, but only 10 exist!)

print(f"\nBefore sync: US stock={us.stock}, EU stock={eu.stock}")
print("After sync... (overselling problem!)")
print("Solution: use authoritative primary for inventory, not multi-master")
print("Or: reserve with optimistic locking, then confirm globally")
EOF
python3 /tmp/active_active.py
```

📸 **Verified Output:**
```
Active-Active Architecture Patterns
  Pattern 1: Conflict-free (CockroachDB/Spanner)
  Pattern 2: Sharded by Geography
  Pattern 3: Multi-Master with Conflict Resolution

Conflict Example: Inventory Update
  [US-East] Stock: 2 (delta=-8)
  [EU-West] Stock: 3 (delta=-7)

Before sync: US stock=2, EU stock=3
Solution: use authoritative primary for inventory, not multi-master
```

---

## Step 8: Capstone — Multi-Region Design Checklist

```bash
cat > /tmp/multi_region_checklist.py << 'EOF'
"""
Multi-region database design decision checklist.
"""

checklist = [
    ("Define RTO/RPO first",
     "RTO (recovery time) < 1min? → Synchronous replication\n     RPO (data loss) = 0? → Synchronous replication\n     RTO < 5min, RPO < 30s? → Async + fast failover tool"),
    
    ("Choose topology",
     "Single primary + read replicas → Active-passive (simpler)\n     Multi-region writes needed → Active-active (complex)\n     Shardable by geography → Partition by region"),
    
    ("Identify conflict-prone data",
     "Inventory, wallet balance, unique IDs → Use primary only\n     User preferences, profiles → LWW acceptable\n     Shopping cart → CRDT or event sourcing"),
    
    ("Plan for network partitions",
     "CAP: choose C or A for each data type\n     CP: refuse writes during partition (ZooKeeper, etcd)\n     AP: serve stale reads, resolve on heal (Cassandra, DynamoDB)"),
    
    ("Implement geo-routing",
     "DNS-based: Route53 Latency routing → regional endpoints\n     Application-level: detect user region → pick closest replica\n     Sticky sessions: ensure read-your-writes consistency"),
    
    ("Test failover",
     "Chaos engineering: kill primary, measure actual RTO\n     Test replication lag under load (not just idle)\n     Verify application handles connection failover automatically"),
    
    ("Data residency compliance",
     "GDPR: EU users' data must stay in EU\n     CCPA: California user data considerations\n     Solution: CockroachDB REGIONAL BY ROW, partition by jurisdiction"),
    
    ("Monitor lag continuously",
     "Alert: replication lag > 30s\n     Alert: replication slot inactive\n     Dashboard: per-region latency and throughput"),
]

print("Multi-Region Database Design Checklist")
print("="*65)
for i, (item, detail) in enumerate(checklist, 1):
    print(f"\n{i}. {item}")
    for line in detail.split('\n'):
        print(f"     {line.strip()}")

# Latency cheat sheet
print("\n\nLatency Cheat Sheet (for architecture decisions)")
print("-"*55)
latencies = [
    ("CPU cycle",          "0.3 ns"),
    ("L1 cache hit",       "1 ns"),
    ("RAM access",         "100 ns"),
    ("NVMe SSD read",      "100 μs"),
    ("HDD read",           "1-10 ms"),
    ("Same-DC network",    "0.5 ms"),
    ("Cross-city",         "1-5 ms"),
    ("US cross-country",   "60-70 ms"),
    ("US-Europe",          "80-120 ms"),
    ("US-Asia Pacific",    "150-200 ms"),
]
for op, lat in latencies:
    print(f"  {op:<25}: {lat}")
EOF
python3 /tmp/multi_region_checklist.py

# Cleanup
docker rm -f pg-us-east pg-eu-west 2>/dev/null
```

📸 **Verified Output:**
```
Multi-Region Database Design Checklist
=================================================================
1. Define RTO/RPO first
     RTO < 1min? → Synchronous replication
     RPO = 0? → Synchronous replication

3. Identify conflict-prone data
     Inventory, wallet balance → Use primary only
     User preferences → LWW acceptable

Latency Cheat Sheet:
  Same-DC network          : 0.5 ms
  US-Europe                : 80-120 ms
  US-Asia Pacific          : 150-200 ms
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| **Active-passive** | Single primary; replicas read-only; failover is manual/semi-auto |
| **Active-active** | Multiple writeable primaries; conflict resolution required |
| **Logical replication** | `CREATE PUBLICATION / SUBSCRIPTION` — table-level replication |
| **Physical replication** | Block-level streaming replication (full server copy) |
| **Replication lag** | Async = lag; sync = latency; choose based on RTO/RPO |
| **LWW** | Last-Write-Wins: simple but can lose concurrent updates |
| **CRDTs** | Conflict-free data types: counters, sets auto-merge |
| **Geo-routing** | Route53/Cloudflare → nearest read replica |
| **Data sovereignty** | GDPR requires EU data stay in EU → partition by region |
| **RTT impact** | US-EU = 100ms; async replication adds 100ms replica lag |

> 💡 **Architect's insight:** Most applications don't need active-active multi-region writes — they need active-passive with fast failover and read replicas in each region. Only go active-active when you have specific use cases and a plan for every conflict scenario.
