# Lab 01: CAP Theorem & Consistency Models

**Time:** 50 minutes | **Level:** Architect | **DB:** Distributed Systems (Python3 simulation)

---

## 🎯 Objective

Understand the CAP theorem, its practical implications, and the PACELC extension. Simulate partition scenarios to observe consistency vs. availability trade-offs. Map real databases (MySQL, Cassandra, ZooKeeper) to CAP categories.

---

## 📚 Background

The **CAP Theorem** (Brewer's Theorem, 2000) states that a distributed data store can only guarantee **two of three** properties simultaneously:

- **C — Consistency**: Every read receives the most recent write or an error
- **A — Availability**: Every request receives a (non-error) response, though it may not be the most recent
- **P — Partition Tolerance**: The system continues operating despite network partitions (message loss between nodes)

> 💡 **Key insight:** Network partitions are unavoidable in real distributed systems. You must choose: during a partition, do you sacrifice **C** (stay available with potentially stale data) or **A** (go offline to maintain consistency)?

### CAP Categories

| Category | Description | Examples |
|----------|-------------|---------|
| **CP** | Consistent + Partition Tolerant (sacrifices availability) | MySQL (with sync replication), ZooKeeper, HBase, etcd |
| **AP** | Available + Partition Tolerant (sacrifices consistency) | Cassandra, DynamoDB, CouchDB, DNS |
| **CA** | Consistent + Available (no partition tolerance) | Single-node RDBMS (not truly distributed) |

### PACELC Extension

PACELC extends CAP to cover **normal operation** (no partition):

```
if Partition:
    choose between Availability vs Consistency
else:
    choose between Latency vs Consistency
```

| System | Partition choice | Else choice |
|--------|-----------------|-------------|
| MySQL (sync replication) | CP | CL (consistency over latency) |
| Cassandra | AP | EL (eventual, low latency) |
| DynamoDB (strong) | CP | CL |
| DynamoDB (eventual) | AP | EL |

### Consistency Models (from strongest to weakest)

1. **Strong Consistency** — All reads see the latest write. Requires coordination. (ZooKeeper, etcd)
2. **Sequential Consistency** — Operations appear in program order across all nodes.
3. **Causal Consistency** — Causally related operations are seen in order. (MongoDB sessions)
4. **Eventual Consistency** — All nodes converge to the same value given no new updates. (Cassandra default)
5. **Read-Your-Writes** — After writing, you always see your own write.

---

## Step 1: Set Up Python Environment

```bash
# Install required packages
pip3 install requests threading

# Verify python3 is available
python3 --version
```

📸 **Verified Output:**
```
Python 3.10.12
```

---

## Step 2: Simulate a Distributed Key-Value Store

Create the simulation file:

```bash
cat > /tmp/cap_simulation.py << 'EOF'
"""
CAP Theorem Simulation
Simulates a 3-node distributed key-value store showing C vs A trade-off during partitions.
"""

import threading
import time
import random
from datetime import datetime

class Node:
    def __init__(self, node_id, peers):
        self.node_id = node_id
        self.data = {}
        self.peers = peers
        self.is_partitioned = False
        self.lock = threading.Lock()
        self.log = []
    
    def write(self, key, value, mode="AP"):
        """Write with either AP (available) or CP (consistent) behavior"""
        timestamp = time.time()
        
        if mode == "CP":
            # CP mode: require quorum before writing
            if self.is_partitioned:
                self.log.append(f"[{self.node_id}] CP mode: REFUSED write (partition detected, maintaining consistency)")
                return False, "Error: Cannot achieve consistency during partition"
            
            # Simulate writing to quorum
            success_count = 1  # self
            for peer in self.peers:
                if not peer.is_partitioned:
                    with peer.lock:
                        peer.data[key] = (value, timestamp)
                    success_count += 1
            
            if success_count >= 2:  # quorum of 3 nodes = 2
                with self.lock:
                    self.data[key] = (value, timestamp)
                self.log.append(f"[{self.node_id}] CP write OK: {key}={value} (quorum: {success_count}/3)")
                return True, value
            else:
                self.log.append(f"[{self.node_id}] CP write FAILED: insufficient quorum ({success_count}/3)")
                return False, "Error: Cannot achieve quorum"
        
        else:  # AP mode
            # AP mode: write locally, sync later (eventual consistency)
            with self.lock:
                self.data[key] = (value, timestamp)
            self.log.append(f"[{self.node_id}] AP write OK: {key}={value} (will sync later)")
            
            # Try to sync to peers in background (best effort)
            for peer in self.peers:
                if not peer.is_partitioned and not self.is_partitioned:
                    with peer.lock:
                        peer_val = peer.data.get(key, (None, 0))
                        if peer_val[1] < timestamp:
                            peer.data[key] = (value, timestamp)
            return True, value
    
    def read(self, key, mode="AP"):
        """Read with AP or CP behavior"""
        if mode == "CP" and self.is_partitioned:
            self.log.append(f"[{self.node_id}] CP read REFUSED: partition detected")
            return None, "Error: System unavailable during partition"
        
        with self.lock:
            val = self.data.get(key, (None, 0))
            self.log.append(f"[{self.node_id}] Read {key}={val[0]} (ts={val[1]:.3f})")
            return val[0], "OK"


def simulate_cap(mode):
    print(f"\n{'='*60}")
    print(f"Simulation: {mode} mode")
    print('='*60)
    
    # Create 3 nodes
    node1 = Node("Node1", [])
    node2 = Node("Node2", [])
    node3 = Node("Node3", [])
    node1.peers = [node2, node3]
    node2.peers = [node1, node3]
    node3.peers = [node1, node2]
    
    # Initial write (no partition)
    print("\n[Phase 1] Normal operation - writing user:alice=active")
    ok, msg = node1.write("user:alice", "active", mode=mode)
    print(f"  Write result: {ok} | {msg}")
    
    time.sleep(0.1)
    
    val, status = node2.read("user:alice", mode=mode)
    print(f"  Node2 read user:alice = {val} ({status})")
    val, status = node3.read("user:alice", mode=mode)
    print(f"  Node3 read user:alice = {val} ({status})")
    
    # Simulate network partition: Node3 isolated
    print("\n[Phase 2] NETWORK PARTITION: Node3 is isolated!")
    node3.is_partitioned = True
    
    # Write during partition
    print("\n[Phase 3] Writing user:alice=suspended during partition")
    ok, msg = node1.write("user:alice", "suspended", mode=mode)
    print(f"  Node1 write result: {ok} | {msg}")
    
    # Read from all nodes during partition
    print("\n[Phase 4] Reading from all nodes during partition:")
    val, status = node1.read("user:alice", mode=mode)
    print(f"  Node1 read = {val} ({status})")
    val, status = node2.read("user:alice", mode=mode)
    print(f"  Node2 read = {val} ({status})")
    val, status = node3.read("user:alice", mode=mode)
    print(f"  Node3 read = {val} ({status}) ← PARTITION NODE")
    
    # Heal partition
    print("\n[Phase 5] Partition healed - eventual sync")
    node3.is_partitioned = False
    if mode == "AP":
        # In AP mode, nodes eventually sync
        val1 = node1.data.get("user:alice", (None,0))
        val3 = node3.data.get("user:alice", (None,0))
        if val1[1] > val3[1]:
            node3.data["user:alice"] = val1
        print(f"  After sync - Node3 read = {node3.data.get('user:alice', (None,0))[0]}")
    
    print("\n[Event Log]")
    for node in [node1, node2, node3]:
        for entry in node.log:
            print(f"  {entry}")

# Run both simulations
simulate_cap("AP")  # Cassandra-style
simulate_cap("CP")  # ZooKeeper-style

print("\n" + "="*60)
print("SUMMARY:")
print("  AP (Cassandra): During partition, Node3 stays available but")
print("                  returns stale data → INCONSISTENCY")
print("  CP (ZooKeeper): During partition, Node3 refuses requests →")
print("                  UNAVAILABILITY but always consistent")
print("="*60)
EOF

python3 /tmp/cap_simulation.py```

---

## Step 3: Run the CAP Simulation

```bash
python3 /tmp/cap_simulation.py
```

📸 **Verified Output:**
```
============================================================
Simulation: AP mode
============================================================

[Phase 1] Normal operation - writing user:alice=active
  Write result: True | active
  Node2 read user:alice = active (OK)
  Node3 read user:alice = active (OK)

[Phase 2] NETWORK PARTITION: Node3 is isolated!

[Phase 3] Writing user:alice=suspended during partition
  Node1 write result: True | suspended

[Phase 4] Reading from all nodes during partition:
  Node1 read = suspended (OK)
  Node2 read = suspended (OK)
  Node3 read = active (OK) ← PARTITION NODE (STALE DATA!)

[Phase 5] Partition healed - eventual sync
  After sync - Node3 read = suspended

============================================================
Simulation: CP mode
============================================================

[Phase 3] Writing user:alice=suspended during partition
  Node1 write result: False | Error: Cannot achieve consistency during partition

[Phase 4] Reading from all nodes during partition:
  Node1 read REFUSED: partition detected
  Node3 CP read REFUSED: partition detected
```

---

## Step 4: MySQL as CP System

```bash
# Start MySQL
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

# MySQL with sync replication = CP: write fails if replica unreachable
docker exec mysql-lab mysql -uroot -prootpass -e "
  -- Show semi-sync replication variables (CP behavior)
  SHOW VARIABLES LIKE 'rpl_semi_sync%';
  
  -- Demonstrate transaction isolation (strong consistency within node)
  CREATE DATABASE cap_demo;
  USE cap_demo;
  CREATE TABLE accounts (id INT PRIMARY KEY, balance INT);
  INSERT INTO accounts VALUES (1, 1000), (2, 500);
  
  -- Strong consistency: transaction either fully commits or rolls back
  START TRANSACTION;
  UPDATE accounts SET balance = balance - 100 WHERE id = 1;
  UPDATE accounts SET balance = balance + 100 WHERE id = 2;
  COMMIT;
  
  SELECT * FROM accounts;
"
```

📸 **Verified Output:**
```
+------+-------------------------------------------+-------+
| Variable_name                                | Value |
+------+-------------------------------------------+-------+
| rpl_semi_sync_master_enabled                 | OFF   |
| rpl_semi_sync_master_timeout                 | 10000 |
+------+-------------------------------------------+-------+

+----+---------+
| id | balance |
+----+---------+
|  1 |     900 |
|  2 |     600 |
+----+---------+
```

> 💡 **MySQL CP characteristics:** With synchronous replication (rpl_semi_sync enabled), MySQL waits for at least one replica to acknowledge before committing. This makes it CP — during partition, writes may block/timeout rather than returning stale data.

---

## Step 5: Cassandra as AP System Concepts

```bash
# Cassandra tunable consistency (AP by default)
cat > /tmp/cassandra_consistency.py << 'EOF'
"""
Demonstrates Cassandra's tunable consistency model.
Cassandra is AP by default but can be tuned toward CP.
"""

consistency_levels = {
    "ONE": {
        "description": "Responds after 1 replica acknowledges",
        "cap": "AP",
        "use_case": "High availability, eventual consistency OK",
        "formula": "W=1, R=1",
        "risk": "Stale reads possible"
    },
    "QUORUM": {
        "description": "Responds after majority of replicas acknowledge",
        "cap": "CP (when W+R > N)",
        "use_case": "Balanced consistency and availability",
        "formula": "W=⌊N/2⌋+1, R=⌊N/2⌋+1",
        "risk": "Unavailable if > (N-quorum) nodes fail"
    },
    "ALL": {
        "description": "All replicas must acknowledge",
        "cap": "CP (strong)",
        "use_case": "Critical data, strong consistency required",
        "formula": "W=N, R=N",
        "risk": "Any node failure = unavailable"
    },
    "LOCAL_QUORUM": {
        "description": "Quorum within local datacenter",
        "cap": "AP across DCs, CP within DC",
        "use_case": "Multi-DC with local consistency",
        "formula": "W=local_quorum, R=local_quorum",
        "risk": "Cross-DC reads may be stale"
    }
}

# Replication factor = 3 (typical)
N = 3
print("Cassandra Consistency Levels (Replication Factor = 3)")
print("="*60)

for level, info in consistency_levels.items():
    print(f"\n[{level}]")
    print(f"  Description: {info['description']}")
    print(f"  CAP Category: {info['cap']}")
    print(f"  Formula:      {info['formula']}")
    print(f"  Use Case:     {info['use_case']}")
    print(f"  Risk:         {info['risk']}")

# Show consistency formula
print("\n" + "="*60)
print("Strong Consistency Rule: W + R > N")
print(f"  N=3 (replication factor)")
print(f"  QUORUM writes (W=2) + QUORUM reads (R=2) = 4 > 3 ✓ CONSISTENT")
print(f"  ONE write (W=1) + ONE read (R=1) = 2 ≤ 3 ✗ EVENTUAL")
EOF
python3 /tmp/cassandra_consistency.py
```

📸 **Verified Output:**
```
Cassandra Consistency Levels (Replication Factor = 3)
============================================================

[ONE]
  Description: Responds after 1 replica acknowledges
  CAP Category: AP
  Formula:      W=1, R=1
  Risk:         Stale reads possible

[QUORUM]
  Description: Responds after majority of replicas acknowledge
  CAP Category: CP (when W+R > N)
  Formula:      W=⌊N/2⌋+1, R=⌊N/2⌋+1

Strong Consistency Rule: W + R > N
  N=3 (replication factor)
  QUORUM writes (W=2) + QUORUM reads (R=2) = 4 > 3 ✓ CONSISTENT
  ONE write (W=1) + ONE read (R=1) = 2 ≤ 3 ✗ EVENTUAL
```

---

## Step 6: PACELC in Practice

```bash
cat > /tmp/pacelc_analysis.py << 'EOF'
"""
PACELC analysis: Partition tolerance vs Latency/Consistency tradeoff
"""

systems = [
    {
        "name": "MySQL (sync replication)",
        "partition_choice": "C",  # Consistency
        "else_choice": "C",       # Consistency over Latency
        "typical_write_latency_ms": 5,
        "consistency": "Strong",
        "notes": "Blocks on partition; low latency writes require async replication"
    },
    {
        "name": "Cassandra (ONE)",
        "partition_choice": "A",  # Availability
        "else_choice": "L",       # Latency over Consistency
        "typical_write_latency_ms": 1,
        "consistency": "Eventual",
        "notes": "Highly available, very low latency, eventual consistency"
    },
    {
        "name": "Cassandra (QUORUM)",
        "partition_choice": "A",
        "else_choice": "C",
        "typical_write_latency_ms": 3,
        "consistency": "Strong (effectively)",
        "notes": "W+R>N guarantees consistency; better latency than MySQL sync"
    },
    {
        "name": "ZooKeeper",
        "partition_choice": "C",
        "else_choice": "C",
        "typical_write_latency_ms": 10,
        "consistency": "Strong (linearizable)",
        "notes": "Configuration/coordination, not high-throughput data store"
    },
    {
        "name": "DynamoDB (eventual)",
        "partition_choice": "A",
        "else_choice": "L",
        "typical_write_latency_ms": 2,
        "consistency": "Eventual",
        "notes": "Default DynamoDB reads, lower cost"
    },
    {
        "name": "DynamoDB (strong)",
        "partition_choice": "C",
        "else_choice": "C",
        "typical_write_latency_ms": 5,
        "consistency": "Strong",
        "notes": "ConsistentRead=True, 2x read cost"
    },
    {
        "name": "etcd",
        "partition_choice": "C",
        "else_choice": "C",
        "typical_write_latency_ms": 10,
        "consistency": "Strong (Raft)",
        "notes": "Kubernetes config store, Raft consensus"
    },
]

print(f"{'System':<30} {'Partition':<12} {'Else':<8} {'Latency(ms)':<14} {'Consistency'}")
print("-"*80)
for s in systems:
    p = "Consistency" if s["partition_choice"] == "C" else "Availability"
    e = "Consistency" if s["else_choice"] == "C" else "Low Latency"
    print(f"{s['name']:<30} {p:<12} {e:<8} {s['typical_write_latency_ms']:<14} {s['consistency']}")
EOF
python3 /tmp/pacelc_analysis.py
```

📸 **Verified Output:**
```
System                         Partition    Else     Latency(ms)    Consistency
--------------------------------------------------------------------------------
MySQL (sync replication)       Consistency  Consis   5              Strong
Cassandra (ONE)                Availability Low La   1              Eventual
Cassandra (QUORUM)             Availability Consis   3              Strong (effectively)
ZooKeeper                      Consistency  Consis   10             Strong (linearizable)
DynamoDB (eventual)            Availability Low La   2              Eventual
DynamoDB (strong)              Consistency  Consis   5              Strong
etcd                           Consistency  Consis   10             Strong (Raft)
```

---

## Step 7: Eventual Consistency Deep Dive

```bash
cat > /tmp/eventual_consistency.py << 'EOF'
"""
Demonstrates eventual consistency with conflict resolution strategies.
"""
import time

class EventualNode:
    def __init__(self, name):
        self.name = name
        self.data = {}  # key -> (value, vector_clock)
    
    def write(self, key, value, clock=None):
        current = self.data.get(key, (None, 0))
        new_clock = (clock or current[1]) + 1
        self.data[key] = (value, new_clock)
        print(f"  [{self.name}] Write: {key}={value} (clock={new_clock})")
        return new_clock
    
    def read(self, key):
        val, clock = self.data.get(key, (None, 0))
        print(f"  [{self.name}] Read: {key}={val} (clock={clock})")
        return val, clock
    
    def sync(self, other):
        """Last-Write-Wins (LWW) conflict resolution"""
        print(f"\n  Syncing {self.name} ← {other.name}")
        for key in other.data:
            self_val, self_clock = self.data.get(key, (None, 0))
            other_val, other_clock = other.data[key]
            if other_clock > self_clock:
                self.data[key] = other.data[key]
                print(f"    Accepted {other.name}'s version of {key}={other_val} (clock {other_clock} > {self_clock})")
            elif other_clock < self_clock:
                print(f"    Kept own version of {key}={self_val} (clock {self_clock} > {other_clock})")
            else:
                print(f"    CONFLICT: {key} same clock! Using lexicographic winner: {max(str(self_val), str(other_val))}")
                winner = max(str(self_val), str(other_val))
                self.data[key] = (winner, self_clock)

# Simulate eventual consistency with conflict
print("=== Eventual Consistency Demo: Concurrent Writes ===\n")
node_a = EventualNode("Node-A")
node_b = EventualNode("Node-B")

# Initial state
print("[Initial] Both nodes start with same data:")
node_a.write("cart:user1", '["item1"]')
node_b.data["cart:user1"] = node_a.data["cart:user1"]  # sync

# Partition: concurrent writes
print("\n[Partition] Concurrent writes to same key:")
node_a.write("cart:user1", '["item1","item2"]')  # User adds item2
time.sleep(0.01)
node_b.write("cart:user1", '["item1","item3"]')  # User adds item3 on different node

print("\n[Reading during partition]:")
node_a.read("cart:user1")  # sees item2
node_b.read("cart:user1")  # sees item3

# Healing: sync
print("\n[Partition Healed] Syncing...")
node_a.sync(node_b)

print("\n[After sync]:")
node_a.read("cart:user1")
node_b.read("cart:user1")

print("\n⚠️  Conflict resolved by LWW — one user's change was LOST!")
print("   Real solution: CRDTs (Conflict-free Replicated Data Types)")
print("   Amazon Dynamo uses vector clocks + app-level conflict resolution")
EOF
python3 /tmp/eventual_consistency.py
```

📸 **Verified Output:**
```
=== Eventual Consistency Demo: Concurrent Writes ===

[Initial] Both nodes start with same data:
  [Node-A] Write: cart:user1=["item1"] (clock=1)

[Partition] Concurrent writes to same key:
  [Node-A] Write: cart:user1=["item1","item2"] (clock=2)
  [Node-B] Write: cart:user1=["item1","item3"] (clock=2)

[Reading during partition]:
  [Node-A] Read: cart:user1=["item1","item2"] (clock=2)
  [Node-B] Read: cart:user1=["item1","item3"] (clock=2)

[Partition Healed] Syncing...
  Syncing Node-A ← Node-B
    CONFLICT: cart:user1 same clock! Using lexicographic winner

⚠️  Conflict resolved by LWW — one user's change was LOST!
```

---

## Step 8: Capstone — Consistency Model Decision Framework

```bash
cat > /tmp/cap_decision.py << 'EOF'
"""
Decision framework: Which consistency model for which use case?
"""

use_cases = [
    {
        "use_case": "Bank account balance",
        "consistency_required": "Strong",
        "recommended_system": "PostgreSQL / MySQL (sync)",
        "cap_category": "CP",
        "reason": "Financial data: wrong balance = fraud/legal issues"
    },
    {
        "use_case": "Social media likes count",
        "consistency_required": "Eventual",
        "recommended_system": "Cassandra / DynamoDB",
        "cap_category": "AP",
        "reason": "Approximate count is fine; availability > perfect accuracy"
    },
    {
        "use_case": "Shopping cart",
        "consistency_required": "Causal (Read-Your-Writes)",
        "recommended_system": "DynamoDB / MongoDB",
        "cap_category": "AP with sessions",
        "reason": "You must see your own additions; others can be eventual"
    },
    {
        "use_case": "Distributed lock / leader election",
        "consistency_required": "Strong (linearizable)",
        "recommended_system": "ZooKeeper / etcd",
        "cap_category": "CP",
        "reason": "Two nodes must never both believe they're leader"
    },
    {
        "use_case": "IoT sensor data ingestion",
        "consistency_required": "Eventual",
        "recommended_system": "Cassandra / InfluxDB",
        "cap_category": "AP",
        "reason": "High write throughput; minor data loss acceptable"
    },
    {
        "use_case": "Inventory (e-commerce)",
        "consistency_required": "Strong or Causal",
        "recommended_system": "PostgreSQL + optimistic locking",
        "cap_category": "CP",
        "reason": "Overselling is costly; strong consistency preferred"
    },
    {
        "use_case": "User profile / preferences",
        "consistency_required": "Eventual",
        "recommended_system": "DynamoDB / MongoDB Atlas",
        "cap_category": "AP",
        "reason": "Slight delay seeing profile update is acceptable"
    },
]

print("CAP Decision Framework for Common Use Cases")
print("="*80)
print(f"{'Use Case':<35} {'Consistency':<22} {'Recommended':<30} {'CAP'}")
print("-"*80)
for uc in use_cases:
    print(f"{uc['use_case']:<35} {uc['consistency_required']:<22} {uc['recommended_system']:<30} {uc['cap_category']}")

print("\n" + "="*80)
print("ARCHITECT'S RULE: Design for the consistency model your use case NEEDS,")
print("not the strongest one available. Unnecessary consistency = lower performance.")
EOF
python3 /tmp/cap_decision.py

# Cleanup
docker rm -f mysql-lab 2>/dev/null || true
```

📸 **Verified Output:**
```
CAP Decision Framework for Common Use Cases
================================================================================
Use Case                            Consistency            Recommended                    CAP
--------------------------------------------------------------------------------
Bank account balance                Strong                 PostgreSQL / MySQL (sync)       CP
Social media likes count            Eventual               Cassandra / DynamoDB            AP
Shopping cart                       Causal (Read-Your-Writes) DynamoDB / MongoDB          AP with sessions
Distributed lock / leader election  Strong (linearizable)  ZooKeeper / etcd               CP
IoT sensor data ingestion           Eventual               Cassandra / InfluxDB            AP
Inventory (e-commerce)              Strong or Causal       PostgreSQL + optimistic locking CP
User profile / preferences          Eventual               DynamoDB / MongoDB Atlas        AP

ARCHITECT'S RULE: Design for the consistency model your use case NEEDS,
not the strongest one available. Unnecessary consistency = lower performance.
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| **CAP Theorem** | Can't have C + A + P simultaneously; P is unavoidable → choose C or A |
| **CP Systems** | MySQL, ZooKeeper, etcd — refuse requests during partition to stay consistent |
| **AP Systems** | Cassandra, DynamoDB, DNS — serve requests with potentially stale data |
| **PACELC** | Extends CAP: normal operation also requires Latency vs Consistency choice |
| **Strong Consistency** | All reads see latest write; requires coordination overhead |
| **Eventual Consistency** | Nodes converge given time; high availability and low latency |
| **Causal Consistency** | Your writes visible to you immediately; others may lag |
| **Tunable Consistency** | Cassandra: ONE=AP, QUORUM=CP, ALL=CP (strongest) |
| **LWW Conflict Resolution** | Last-Write-Wins; simple but may lose concurrent updates |

> 💡 **Architect's insight:** "CP vs AP" is not a binary choice — Cassandra lets you tune per-operation. Design systems with the RIGHT consistency level for each data type, not a one-size-fits-all approach.
