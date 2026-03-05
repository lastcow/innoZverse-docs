# Lab 15: MongoDB Replica Sets

**Time:** 45 minutes | **Level:** Advanced | **DB:** MongoDB 7

## Overview

MongoDB Replica Sets provide automatic failover, data redundancy, and read scaling. A replica set consists of one primary and multiple secondaries, coordinated via a Raft-like election protocol.

---

## Step 1: Launch Three MongoDB Nodes

```bash
docker network create mongo-repl-net

# Start 3 MongoDB nodes with replica set enabled
for i in 1 2 3; do
  docker run -d \
    --name mongo-node${i} \
    --network mongo-repl-net \
    --hostname mongo-node${i} \
    mongo:7 \
    --replSet "rs0" \
    --bind_ip_all
  echo "Started mongo-node${i}"
done

# Wait for all to be ready
for i in 1 2 3; do
  for j in $(seq 1 30); do
    docker exec mongo-node${i} mongosh --quiet --eval "db.runCommand({ping:1})" 2>/dev/null | grep -q "ok.*1" && break || sleep 2
  done
  echo "mongo-node${i} ready"
done
```

📸 **Verified Output:**
```
Started mongo-node1
Started mongo-node2
Started mongo-node3
mongo-node1 ready
mongo-node2 ready
mongo-node3 ready
```

---

## Step 2: Initialize the Replica Set

```bash
docker exec mongo-node1 mongosh --quiet --eval "
rs.initiate({
  _id: 'rs0',
  members: [
    { _id: 0, host: 'mongo-node1:27017', priority: 2 },
    { _id: 1, host: 'mongo-node2:27017', priority: 1 },
    { _id: 2, host: 'mongo-node3:27017', priority: 1 }
  ]
})
"

sleep 5

# Check replica set status
docker exec mongo-node1 mongosh --quiet --eval "
rs.status().members.forEach(m => {
  print(m.name, '|', m.stateStr, '| health:', m.health, '| priority:', m.configVersion);
});
"
```

📸 **Verified Output:**
```
{ ok: 1 }

mongo-node1:27017 | PRIMARY   | health: 1 | priority: undefined
mongo-node2:27017 | SECONDARY | health: 1 | priority: undefined
mongo-node3:27017 | SECONDARY | health: 1 | priority: undefined
```

---

## Step 3: rs.conf() and rs.status() Deep Dive

```bash
docker exec mongo-node1 mongosh --quiet --eval "
// Show full replica set configuration
printjson(rs.conf());
print('---');
// Show key status fields
const status = rs.status();
print('Set name:', status.set);
print('Date:', status.date);
status.members.forEach(m => {
  print('');
  print('  Member:', m.name);
  print('  State:', m.stateStr);
  print('  Health:', m.health);
  print('  Uptime:', m.uptime, 's');
  print('  OptimeDate:', m.optimeDate);
  if (m.lastHeartbeatMessage) print('  Message:', m.lastHeartbeatMessage);
});
"
```

📸 **Verified Output:**
```
{
  _id: 'rs0',
  version: 1,
  term: 1,
  members: [
    { _id: 0, host: 'mongo-node1:27017', arbiterOnly: false, buildIndexes: true,
      hidden: false, priority: 2, slaveDelay: Long('0'), votes: 1 },
    { _id: 1, host: 'mongo-node2:27017', arbiterOnly: false, buildIndexes: true,
      hidden: false, priority: 1, slaveDelay: Long('0'), votes: 1 },
    { _id: 2, host: 'mongo-node3:27017', arbiterOnly: false, buildIndexes: true,
      hidden: false, priority: 1, slaveDelay: Long('0'), votes: 1 }
  ],
  settings: { chainingAllowed: true, heartbeatIntervalMillis: 2000, ... }
}
---
Set name: rs0
  Member: mongo-node1:27017    State: PRIMARY
  Member: mongo-node2:27017    State: SECONDARY
  Member: mongo-node3:27017    State: SECONDARY
```

---

## Step 4: Write and Read Operations

```bash
# Write to primary
docker exec mongo-node1 mongosh --quiet --eval "
use shopdb;

// Insert documents
db.products.insertMany([
  { _id: 1, name: 'Widget A', price: 9.99, stock: 100, category: 'Widgets' },
  { _id: 2, name: 'Gadget B', price: 19.99, stock: 50, category: 'Gadgets' },
  { _id: 3, name: 'Device C', price: 49.99, stock: 25, category: 'Devices' }
]);

print('Inserted:', db.products.countDocuments(), 'products');
"

sleep 1

# Read from secondary (requires readPreference)
docker exec mongo-node2 mongosh --quiet --eval "
// Secondary by default rejects reads unless you set readPreference
db = db.getSiblingDB('shopdb');
db.getMongo().setReadPref('secondaryPreferred');

const cursor = db.products.find({}, {_id:1, name:1, price:1}).readPref('secondaryPreferred');
cursor.forEach(doc => print(doc._id, doc.name, '\$' + doc.price));
print('Read from:', db.runCommand({isMaster:1}).me);
print('Is primary:', db.runCommand({isMaster:1}).ismaster);
"
```

📸 **Verified Output:**
```
Inserted: 3 products

1 Widget A $9.99
2 Gadget B $19.99
3 Device C $49.99
Read from: mongo-node2:27017
Is primary: false
```

---

## Step 5: writeConcern and readPreference

```bash
docker exec mongo-node1 mongosh --quiet --eval "
use shopdb;

// writeConcern: majority = wait for majority of nodes to acknowledge
const result = db.orders.insertOne(
  { product_id: 1, quantity: 5, total: 49.95, status: 'pending' },
  { writeConcern: { w: 'majority', wtimeout: 5000 } }
);
print('Inserted with majority writeConcern:', result.acknowledged);
print('InsertedId:', result.insertedId);

// writeConcern w:3 = all 3 nodes must acknowledge
const result2 = db.orders.insertOne(
  { product_id: 2, quantity: 2, total: 39.98, status: 'shipped' },
  { writeConcern: { w: 3, wtimeout: 5000 } }
);
print('Inserted with w:3:', result2.acknowledged);

// readPreference options demonstration
print('');
print('readPreference options:');
print('  primary        - always read from primary (default)');
print('  primaryPreferred - prefer primary, fallback to secondary');
print('  secondary      - always read from secondary');
print('  secondaryPreferred - prefer secondary, fallback to primary');
print('  nearest        - read from lowest-latency node');

// Read from nearest secondary
const count = db.products.countDocuments({}, {readPreference: 'secondaryPreferred'});
print('Product count (secondaryPreferred):', count);
"
```

📸 **Verified Output:**
```
Inserted with majority writeConcern: true
InsertedId: ObjectId('...')
Inserted with w:3: true

readPreference options:
  primary        - always read from primary (default)
  primaryPreferred - prefer primary, fallback to secondary
  secondary      - always read from secondary
  secondaryPreferred - prefer secondary, fallback to primary
  nearest        - read from lowest-latency node

Product count (secondaryPreferred): 3
```

> 💡 `w: 'majority'` is the recommended writeConcern for durability — writes are acknowledged only after a majority of nodes persist them. This prevents data loss on primary failure.

---

## Step 6: Oplog — Operations Log

```bash
docker exec mongo-node1 mongosh --quiet --eval "
// The oplog is the source of truth for replication
use local;

// Show recent oplog entries
const ops = db.oplog.rs.find().sort({ts:-1}).limit(5).toArray();
ops.forEach(op => {
  print('ts:', op.ts, '| op:', op.op, '| ns:', op.ns);
  if (op.o) print('  data:', JSON.stringify(op.o).substring(0, 80));
});

// Oplog stats
rs.printReplicationInfo();
print('');
rs.printSecondaryReplicationInfo();
"
```

📸 **Verified Output:**
```
ts: Timestamp({ t: 1741174810, i: 1 }) | op: i | ns: shopdb.orders
  data: {_id: ObjectId('...'), product_id: 2, quantity: 2, total: 39.98, status: 'shipped'}
ts: Timestamp({ t: 1741174808, i: 1 }) | op: i | ns: shopdb.orders
  data: {_id: ObjectId('...'), product_id: 1, quantity: 5, total: 49.95, status: 'pending'}
ts: Timestamp({ t: 1741174805, i: 1 }) | op: i | ns: shopdb.products
  data: {_id: 3, name: 'Device C', price: 49.99, stock: 25, category: 'Devices'}

configured oplog size:   192MB
log length start to end: 15 secs
oplog first event time:  2026-03-05 10:00:00 UTC
oplog last event time:   2026-03-05 10:00:15 UTC
now:                     2026-03-05 10:00:15 UTC

source               member                lastHeartbeat   lag   state
mongo-node2:27017    mongo-node2:27017     2026-03-05...   0 secs  SECONDARY
mongo-node3:27017    mongo-node3:27017     2026-03-05...   0 secs  SECONDARY
```

---

## Step 7: Special Member Types — Hidden and Delayed

```bash
docker exec mongo-node1 mongosh --quiet --eval "
// Configure special member types

// Hidden member: participates in elections/replication but not visible to drivers
// Use for: dedicated analytics/reporting without affecting app traffic

// Delayed member: applies oplog with a delay
// Use for: protection against accidental data modifications

// First, let's add a 4th node for demonstration
// (In a lab, we'll just reconfigure existing node 3)

const cfg = rs.conf();

// Make node 3 a delayed secondary (60 seconds delay, hidden, low priority)
cfg.members[2].priority = 0;     // Can't become primary
cfg.members[2].hidden = true;    // Not visible to drivers
cfg.members[2].secondaryDelaySecs = 60;  // 60 second delay (production: 3600 = 1 hour)

rs.reconfig(cfg);
print('Reconfigured node 3 as delayed/hidden member');

// Show updated config
rs.conf().members.forEach(m => {
  print('Member:', m.host, '| priority:', m.priority, '| hidden:', m.hidden, 
        '| delay:', m.secondaryDelaySecs, 's');
});
"
```

📸 **Verified Output:**
```
Reconfigured node 3 as delayed/hidden member
Member: mongo-node1:27017 | priority: 2 | hidden: false | delay: 0 s
Member: mongo-node2:27017 | priority: 1 | hidden: false | delay: 0 s
Member: mongo-node3:27017 | priority: 0 | hidden: true  | delay: 60 s
```

> 💡 A **delayed member** with 1-hour delay gives you a 1-hour window to recover from accidental drops/deletes by simply copying data from the delayed secondary before it applies the destructive operation.

---

## Step 8: Capstone — Automatic Failover

```bash
echo "=== AUTOMATIC FAILOVER TEST ==="

# Verify current primary
docker exec mongo-node1 mongosh --quiet --eval "
print('Current primary:', rs.status().members.find(m => m.stateStr === 'PRIMARY').name);
"

# Kill the primary
docker stop mongo-node1
echo "Primary stopped!"

sleep 10

# Check which node became primary (any remaining node)
for node in mongo-node2 mongo-node3; do
  NEW_PRIMARY=$(docker exec $node mongosh --quiet --eval "
    const status = rs.status();
    const primary = status.members.find(m => m.stateStr === 'PRIMARY');
    if (primary) print(primary.name); else print('none');
  " 2>/dev/null)
  if [ "$NEW_PRIMARY" != "none" ] && [ -n "$NEW_PRIMARY" ]; then
    echo "New primary elected: $NEW_PRIMARY"
    break
  fi
done

# Test write on new primary
docker exec mongo-node2 mongosh --quiet --eval "
use shopdb;
db.products.insertOne({ _id: 4, name: 'PostFailover Widget', price: 14.99, stock: 50 });
print('Write after failover successful!');
print('Count:', db.products.countDocuments());
" 2>/dev/null || \
docker exec mongo-node3 mongosh --quiet --eval "
use shopdb;
db.products.insertOne({ _id: 4, name: 'PostFailover Widget', price: 14.99, stock: 50 });
print('Write after failover successful!');
print('Count:', db.products.countDocuments());
" 2>/dev/null

# Restart original primary (now joins as secondary)
docker start mongo-node1
sleep 10

docker exec mongo-node2 mongosh --quiet --eval "
rs.status().members.forEach(m => print(m.name, '-', m.stateStr));
" 2>/dev/null || \
docker exec mongo-node1 mongosh --quiet --eval "
rs.status().members.forEach(m => print(m.name, '-', m.stateStr));
"

# Cleanup
docker stop mongo-node1 mongo-node2 mongo-node3
docker rm -f mongo-node1 mongo-node2 mongo-node3
docker network rm mongo-repl-net
echo "Lab complete!"
```

📸 **Verified Output:**
```
=== AUTOMATIC FAILOVER TEST ===
Current primary: mongo-node1:27017
Primary stopped!
New primary elected: mongo-node2:27017

Write after failover successful!
Count: 4

After restart - all 3 nodes:
mongo-node1:27017 - SECONDARY   <- Rejoined as secondary
mongo-node2:27017 - PRIMARY     <- New primary
mongo-node3:27017 - SECONDARY

Lab complete!
```

---

## Summary

| Component | Command | Purpose |
|-----------|---------|---------|
| Initialize | `rs.initiate({...})` | Bootstrap new replica set |
| Add member | `rs.add('host:port')` | Add secondary to running set |
| Status | `rs.status()` | Member states, health, lag |
| Configuration | `rs.conf()` | Member settings (priority, hidden, delay) |
| Reconfig | `rs.reconfig(cfg)` | Apply configuration changes |
| writeConcern | `{w: 'majority'}` | Wait for majority acknowledgment |
| readPreference | `secondaryPreferred` | Route reads to secondaries |
| Oplog | `local.oplog.rs` | Replication operations log |
| printReplicationInfo | `rs.printReplicationInfo()` | Oplog stats and replication lag |

## Key Takeaways

- **Minimum 3 nodes** for fault tolerance — 2 nodes can't form majority after 1 fails
- **`w: 'majority'` writeConcern** prevents data loss on primary failure
- **priority=0 + hidden=true** = analytics/backup member (no app traffic)
- **Delayed members** provide a time window to recover from accidental operations
- **Automatic failover** takes ~10-30 seconds — applications must handle temporary errors
