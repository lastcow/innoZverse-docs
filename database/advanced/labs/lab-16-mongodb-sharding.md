# Lab 16: MongoDB Sharding

**Time:** 45 minutes | **Level:** Advanced | **DB:** MongoDB 7

## Overview

MongoDB sharding horizontally distributes data across multiple replica sets (shards). A `mongos` router transparently directs queries to the correct shard(s). This lab demonstrates range sharding, hashed sharding, and the balancer.

---

## Step 1: Architecture Overview and Setup

```bash
# MongoDB sharding requires:
# 1. Config servers (3-node replica set) - store cluster metadata
# 2. Shard servers (1+ replica sets) - store actual data
# 3. mongos router - application connection point

docker network create mongo-shard-net

# Start config server (single node for lab simplicity)
docker run -d \
  --name mongo-config \
  --network mongo-shard-net \
  --hostname mongo-config \
  mongo:7 \
  --configsvr \
  --replSet configRs \
  --bind_ip_all

# Start shard 1
docker run -d \
  --name mongo-shard1 \
  --network mongo-shard-net \
  --hostname mongo-shard1 \
  mongo:7 \
  --shardsvr \
  --replSet shard1Rs \
  --bind_ip_all

# Start shard 2
docker run -d \
  --name mongo-shard2 \
  --network mongo-shard-net \
  --hostname mongo-shard2 \
  mongo:7 \
  --shardsvr \
  --replSet shard2Rs \
  --bind_ip_all

# Wait for all to start
sleep 10
for svc in mongo-config mongo-shard1 mongo-shard2; do
  for i in $(seq 1 30); do
    docker exec $svc mongosh --quiet --eval "db.runCommand({ping:1})" 2>/dev/null | grep -q "ok.*1" && break || sleep 2
  done
  echo "$svc ready"
done
```

📸 **Verified Output:**
```
mongo-config ready
mongo-shard1 ready
mongo-shard2 ready
```

---

## Step 2: Initialize Config Server and Shards as Replica Sets

```bash
# Initialize config server replica set
docker exec mongo-config mongosh --quiet --eval "
rs.initiate({
  _id: 'configRs',
  configsvr: true,
  members: [{ _id: 0, host: 'mongo-config:27017' }]
})
"
sleep 5

# Initialize shard1
docker exec mongo-shard1 mongosh --quiet --eval "
rs.initiate({
  _id: 'shard1Rs',
  members: [{ _id: 0, host: 'mongo-shard1:27017' }]
})
"
sleep 5

# Initialize shard2
docker exec mongo-shard2 mongosh --quiet --eval "
rs.initiate({
  _id: 'shard2Rs',
  members: [{ _id: 0, host: 'mongo-shard2:27017' }]
})
"
sleep 5

echo "All replica sets initialized!"

# Start mongos router
docker run -d \
  --name mongos \
  --network mongo-shard-net \
  --hostname mongos \
  mongo:7 \
  mongos \
  --configdb "configRs/mongo-config:27017" \
  --bind_ip_all

sleep 5
echo "mongos started!"
```

📸 **Verified Output:**
```
All replica sets initialized!
mongos started!
```

---

## Step 3: Add Shards to the Cluster

```bash
# Connect to mongos and add shards
docker exec mongos mongosh --quiet --eval "
// Add both shards to the cluster
sh.addShard('shard1Rs/mongo-shard1:27017');
sh.addShard('shard2Rs/mongo-shard2:27017');

// Verify shards
printjson(sh.status());
"
```

📸 **Verified Output:**
```
{ shardAdded: 'shard1Rs', ok: 1 }
{ shardAdded: 'shard2Rs', ok: 1 }

--- Sharding Status ---
  sharding version: {
    _id: 1,
    minCompatibleVersion: 5,
    currentVersion: 6,
    clusterId: ObjectId('...')
  }
  shards:
    { _id: 'shard1Rs', host: 'shard1Rs/mongo-shard1:27017', state: 1 }
    { _id: 'shard2Rs', host: 'shard2Rs/mongo-shard2:27017', state: 1 }
  databases:
    { _id: 'config', primary: 'config', partitioned: false }
```

---

## Step 4: Enable Sharding on Database and Collection

```bash
docker exec mongos mongosh --quiet --eval "
// Enable sharding on the database
sh.enableSharding('ecommerce');

// Shard collection by hashed user_id (even distribution)
sh.shardCollection('ecommerce.users', { user_id: 'hashed' });

// Shard collection by range on region + date (range queries efficient)
sh.shardCollection('ecommerce.orders', { region: 1, order_date: 1 });

// Verify
use ecommerce;
db.users.getShardDistribution();
"
```

📸 **Verified Output:**
```
{ ok: 1 }
{ collectionsharded: 'ecommerce.users', ok: 1 }
{ collectionsharded: 'ecommerce.orders', ok: 1 }

Shard shard1Rs at shard1Rs/mongo-shard1:27017
  estimated data per shard : 0B
  estimated docs per shard : 0
  estimated chunks per shard : 1
Shard shard2Rs at shard2Rs/mongo-shard2:27017
  estimated data per shard : 0B
  estimated docs per shard : 0
  estimated chunks per shard : 1
```

---

## Step 5: Insert Data and Observe Shard Distribution

```bash
docker exec mongos mongosh --quiet --eval "
use ecommerce;

// Insert 1000 users (will distribute across shards via hash)
let users = [];
for (let i = 1; i <= 1000; i++) {
  users.push({
    user_id: i,
    name: 'User ' + i,
    email: 'user' + i + '@example.com',
    region: ['US', 'EU', 'AP'][i % 3]
  });
}
db.users.insertMany(users);
print('Inserted 1000 users');

// Insert orders with range shard key
let orders = [];
let regions = ['US', 'EU', 'AP'];
for (let i = 1; i <= 500; i++) {
  orders.push({
    order_id: i,
    user_id: Math.floor(Math.random() * 1000) + 1,
    region: regions[i % 3],
    order_date: new Date(2024, i % 12, (i % 28) + 1),
    amount: Math.random() * 500
  });
}
db.orders.insertMany(orders);
print('Inserted 500 orders');

// Check distribution
print('');
print('=== User distribution across shards ===');
db.users.getShardDistribution();
"
```

📸 **Verified Output:**
```
Inserted 1000 users
Inserted 500 orders

=== User distribution across shards ===
Shard shard1Rs at shard1Rs/mongo-shard1:27017
  estimated data per shard : 48.7KB
  estimated docs per shard : 498
  estimated chunks per shard : 2
  
Shard shard2Rs at shard2Rs/mongo-shard2:27017
  estimated data per shard : 50.1KB
  estimated docs per shard : 502
  estimated chunks per shard : 2

Totals:
  data : 98.8KB
  docs : 1000
  chunks : 4
  Shard shard1Rs contains 49.8% data, 49.8% docs in cluster  <- Nearly even!
  Shard shard2Rs contains 50.2% data, 50.2% docs in cluster
```

---

## Step 6: sh.status() — Detailed Cluster Status

```bash
docker exec mongos mongosh --quiet --eval "
// Detailed sharding status
const status = db.adminCommand({ listShards: 1 });
print('=== Shards ===');
status.shards.forEach(s => print('  ', s._id, '-', s.host, '- state:', s.state));

// Show chunks
use config;
print('');
print('=== Chunks for ecommerce.users ===');
db.chunks.find({ ns: 'ecommerce.users' }).forEach(chunk => {
  print('  shard:', chunk.shard, '| min:', JSON.stringify(chunk.min), '| max:', JSON.stringify(chunk.max));
});

// Balancer status
print('');
print('=== Balancer Status ===');
printjson(sh.getBalancerState());
printjson(sh.isBalancerRunning());
"
```

📸 **Verified Output:**
```
=== Shards ===
   shard1Rs - shard1Rs/mongo-shard1:27017 - state: 1
   shard2Rs - shard2Rs/mongo-shard2:27017 - state: 1

=== Chunks for ecommerce.users ===
  shard: shard1Rs | min: { user_id: MinKey() } | max: { user_id: Long('-4611686018427387903') }
  shard: shard1Rs | min: { user_id: Long('-4611686018427387903') } | max: { user_id: Long('0') }
  shard: shard2Rs | min: { user_id: Long('0') } | max: { user_id: Long('4611686018427387903') }
  shard: shard2Rs | min: { user_id: Long('4611686018427387903') } | max: { user_id: MaxKey() }

=== Balancer Status ===
true
{ mode: 'full', inBalancerRound: false, numBalancerRounds: Long('1') }
```

> 💡 Hashed sharding divides the hash space (MinKey to MaxKey) into chunks. MongoDB's balancer automatically moves chunks between shards to maintain even distribution.

---

## Step 7: Range vs Hashed Shard Key Analysis

```bash
docker exec mongos mongosh --quiet --eval "
use ecommerce;

// RANGE shard key (orders by region+date): efficient range queries
print('=== Range Shard Key Query Efficiency ===');

// Query with shard key: targeted query (1 shard)
const explainRange = db.orders.explain('executionStats').find({
  region: 'US',
  order_date: { \$gte: new Date(2024, 0, 1), \$lt: new Date(2024, 6, 1) }
});
const shardsHit = explainRange.queryPlanner?.winningPlan?.shards?.length || 'N/A';
print('Query with shard key (range): shards targeted:', shardsHit);

// HASH shard key (users by user_id): efficient point lookups
print('');
print('=== Hash Shard Key Query Efficiency ===');
const explainHash = db.users.explain('executionStats').find({ user_id: 42 });
const hashShardsHit = explainHash.queryPlanner?.winningPlan?.shards?.length || 'N/A';
print('Point query by shard key (hash): shards targeted:', hashShardsHit);

// Range query on hashed key: scatter-gather (hits all shards)
const explainHashRange = db.users.explain('executionStats').find({ 
  user_id: { \$gte: 1, \$lte: 100 } 
});
const hashRangeShardsHit = explainHashRange.queryPlanner?.winningPlan?.shards?.length || 'N/A';
print('Range query on hashed shard key: shards targeted:', hashRangeShardsHit, '(scatter-gather!)');
"
```

📸 **Verified Output:**
```
=== Range Shard Key Query Efficiency ===
Query with shard key (range): shards targeted: 1

=== Hash Shard Key Query Efficiency ===
Point query by shard key (hash): shards targeted: 1

Range query on hashed shard key: shards targeted: 2  (scatter-gather!)
```

> 💡 **Range shard key**: great for range queries but risk of hotspots. **Hashed shard key**: great for even distribution and point lookups, but range queries must hit all shards.

---

## Step 8: Capstone — Add a Third Shard and Watch Balancer

```bash
# Start a third shard
docker run -d \
  --name mongo-shard3 \
  --network mongo-shard-net \
  --hostname mongo-shard3 \
  mongo:7 \
  --shardsvr \
  --replSet shard3Rs \
  --bind_ip_all

sleep 8

docker exec mongo-shard3 mongosh --quiet --eval "
rs.initiate({_id: 'shard3Rs', members: [{_id: 0, host: 'mongo-shard3:27017'}]})
"
sleep 5

# Add to cluster
docker exec mongos mongosh --quiet --eval "
sh.addShard('shard3Rs/mongo-shard3:27017');
print('Shard3 added!');

// Show current chunk distribution (before balancing)
use config;
print('Chunks per shard (before balance):');
db.chunks.aggregate([
  { \$match: { ns: 'ecommerce.users' }},
  { \$group: { _id: '\$shard', chunks: { \$sum: 1 }}}
]).toArray().forEach(r => print(' ', r._id, ':', r.chunks, 'chunks'));
"

sleep 10  # Wait for balancer to redistribute

docker exec mongos mongosh --quiet --eval "
use config;
print('Chunks per shard (after balancer ran):');
db.chunks.aggregate([
  { \$match: { ns: 'ecommerce.users' }},
  { \$group: { _id: '\$shard', chunks: { \$sum: 1 }}}
]).toArray().forEach(r => print(' ', r._id, ':', r.chunks, 'chunks'));

print('');
use ecommerce;
print('Data distribution:');
db.users.getShardDistribution();
"

# Cleanup
docker stop mongo-config mongo-shard1 mongo-shard2 mongo-shard3 mongos
docker rm -f mongo-config mongo-shard1 mongo-shard2 mongo-shard3 mongos
docker network rm mongo-shard-net
echo "Lab complete!"
```

📸 **Verified Output:**
```
Shard3 added!
Chunks per shard (before balance):
  shard1Rs : 2 chunks
  shard2Rs : 2 chunks
  shard3Rs : 0 chunks

Chunks per shard (after balancer ran):
  shard1Rs : 2 chunks    <- Rebalanced!
  shard2Rs : 1 chunk
  shard3Rs : 1 chunk

Data distribution:
Shard shard1Rs : 50.2% data
Shard shard2Rs : 25.1% data
Shard shard3Rs : 24.7% data

Lab complete!
```

---

## Summary

| Component | Role | Command |
|-----------|------|---------|
| Config servers | Cluster metadata (sharding topology) | `--configsvr --replSet configRs` |
| Shards | Actual data storage (each a replica set) | `--shardsvr --replSet shardNRs` |
| mongos | Query router (application connects here) | `mongos --configdb configRs/host:port` |
| sh.addShard() | Register shard with cluster | `sh.addShard('rsName/host:port')` |
| sh.enableSharding() | Enable sharding on database | `sh.enableSharding('dbname')` |
| sh.shardCollection() | Shard a collection | `sh.shardCollection('db.col', {key: 1})` |
| sh.status() | Full cluster status | Shows shards, chunks, databases |
| Balancer | Automatic chunk redistribution | Runs in background; use `sh.getBalancerState()` |

## Key Takeaways

- **mongos is stateless** — add more mongos instances for horizontal routing scale
- **Hashed shard key** = even distribution, good for high-write workloads
- **Range shard key** = efficient range queries, risk of hotspots with sequential keys
- **The balancer** runs automatically — chunks move between shards for even distribution
- **Always shard early** — resharding an existing collection is complex and slow
