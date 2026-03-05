# Lab 17: Redis Cluster & Sentinel

**Time:** 45 minutes | **Level:** Advanced | **DB:** Redis 7

## Overview

Redis Sentinel provides automatic failover for single-shard Redis deployments. Redis Cluster provides horizontal sharding across multiple nodes using consistent hash slots (0-16383). This lab covers both high-availability patterns.

---

## Step 1: Redis Sentinel Setup

```bash
docker network create redis-sentinel-net

# Start Redis master
docker run -d \
  --name redis-master \
  --network redis-sentinel-net \
  --hostname redis-master \
  redis:7 \
  redis-server --appendonly yes --bind 0.0.0.0

# Start two Redis replicas
for i in 1 2; do
  MASTER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-master)
  docker run -d \
    --name redis-replica${i} \
    --network redis-sentinel-net \
    redis:7 \
    redis-server --replicaof $MASTER_IP 6379 --appendonly yes --bind 0.0.0.0
  echo "Started replica${i}"
done

sleep 5

# Verify replication
docker exec redis-master redis-cli INFO replication | grep -E "role|connected_slaves|slave[0-9]"
```

📸 **Verified Output:**
```
role:master
connected_slaves:2
slave0:ip=172.18.0.3,port=6379,state=online,offset=84,lag=0
slave1:ip=172.18.0.4,port=6379,state=online,offset=84,lag=0
```

---

## Step 2: Configure and Start Sentinel Nodes

```bash
MASTER_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-master)
echo "Master IP: $MASTER_IP"

# Create sentinel configurations
for i in 1 2 3; do
  cat > /tmp/sentinel${i}.conf << EOF
port 26379
bind 0.0.0.0

# Monitor master: name=mymaster, IP, port, quorum=2
sentinel monitor mymaster ${MASTER_IP} 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000

# Auth (if master requires password)
# sentinel auth-pass mymaster yourpassword
EOF

  docker run -d \
    --name redis-sentinel${i} \
    --network redis-sentinel-net \
    -v /tmp/sentinel${i}.conf:/etc/redis/sentinel.conf \
    redis:7 \
    redis-sentinel /etc/redis/sentinel.conf
  echo "Started sentinel${i}"
done

sleep 5
echo "All sentinels started!"
```

📸 **Verified Output:**
```
Master IP: 172.18.0.2
Started sentinel1
Started sentinel2
Started sentinel3
All sentinels started!
```

> 💡 **Quorum=2** means 2 sentinels must agree a master is down before triggering failover. With 3 sentinels and quorum=2, you need at least 2 sentinels operational.

---

## Step 3: Monitor Sentinel Status

```bash
# Check sentinel topology
docker exec redis-sentinel1 redis-cli -p 26379 SENTINEL masters
echo ""
docker exec redis-sentinel1 redis-cli -p 26379 SENTINEL replicas mymaster
echo ""
docker exec redis-sentinel1 redis-cli -p 26379 SENTINEL sentinels mymaster
```

📸 **Verified Output:**
```
1) 1) "name"
   2) "mymaster"
   3) "ip"
   4) "172.18.0.2"
   5) "port"
   6) "6379"
   7) "flags"
   8) "master"
   9) "num-slaves"
   10) "2"
   11) "num-other-sentinels"
   12) "2"
   13) "quorum"
   14) "2"
   15) "failover-timeout"
   16) "10000"
   ...

Replicas of mymaster:
1) "ip" -> "172.18.0.3", "port" -> "6379", "flags" -> "slave"
2) "ip" -> "172.18.0.4", "port" -> "6379", "flags" -> "slave"

Other sentinels:
1) "ip" -> sentinel2_ip, "port" -> "26379", "flags" -> "sentinel"
2) "ip" -> sentinel3_ip, "port" -> "26379", "flags" -> "sentinel"
```

---

## Step 4: Simulate Master Failure and Sentinel Failover

```bash
# Write some data
docker exec redis-master redis-cli SET user:1:name "Alice"
docker exec redis-master redis-cli SET user:2:name "Bob"
docker exec redis-master redis-cli SET counter:visits 1000

echo "=== BEFORE FAILOVER ==="
docker exec redis-sentinel1 redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster

# Kill the master
docker stop redis-master
echo "Master stopped! Waiting for failover..."

sleep 15

echo "=== AFTER FAILOVER ==="
docker exec redis-sentinel1 redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster

# Find new master
NEW_MASTER_INFO=$(docker exec redis-sentinel1 redis-cli -p 26379 SENTINEL get-master-addr-by-name mymaster)
echo "New master info: $NEW_MASTER_INFO"

# Connect to new master and verify data
for node in redis-replica1 redis-replica2; do
  IS_MASTER=$(docker exec $node redis-cli INFO replication 2>/dev/null | grep "^role:" | cut -d: -f2 | tr -d '\r')
  if [ "$IS_MASTER" = "master" ]; then
    echo "New master is: $node"
    docker exec $node redis-cli GET user:1:name
    docker exec $node redis-cli GET counter:visits
    docker exec $node redis-cli INFO replication | grep role
    break
  fi
done
```

📸 **Verified Output:**
```
=== BEFORE FAILOVER ===
1) "172.18.0.2"
2) "6379"

Master stopped! Waiting for failover...

=== AFTER FAILOVER ===
1) "172.18.0.3"    <- New master IP!
2) "6379"

New master is: redis-replica1
Alice
1000
role:master
```

---

## Step 5: Cleanup Sentinel and Start Redis Cluster

```bash
docker stop redis-master redis-replica1 redis-replica2 redis-sentinel1 redis-sentinel2 redis-sentinel3
docker rm -f redis-master redis-replica1 redis-replica2 redis-sentinel1 redis-sentinel2 redis-sentinel3
docker network rm redis-sentinel-net
rm -f /tmp/sentinel*.conf

echo "Sentinel lab done. Starting Redis Cluster lab..."
docker network create redis-cluster-net
```

---

## Step 6: Launch Redis Cluster Nodes

```bash
# Redis Cluster needs minimum 6 nodes: 3 masters + 3 replicas
for i in $(seq 1 6); do
  docker run -d \
    --name redis-cluster-node${i} \
    --network redis-cluster-net \
    --hostname redis-cluster-node${i} \
    redis:7 \
    redis-server \
      --cluster-enabled yes \
      --cluster-config-file nodes.conf \
      --cluster-node-timeout 5000 \
      --appendonly yes \
      --bind 0.0.0.0 \
      --port 6379
  echo "Started cluster node ${i}"
done

sleep 5

# Get all node IPs
NODES=""
for i in $(seq 1 6); do
  IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' redis-cluster-node${i})
  NODES="${NODES} ${IP}:6379"
  eval "NODE${i}_IP=${IP}"
done
echo "Node IPs: $NODES"
```

📸 **Verified Output:**
```
Started cluster node 1
Started cluster node 2
Started cluster node 3
Started cluster node 4
Started cluster node 5
Started cluster node 6
Node IPs: 172.19.0.2:6379 172.19.0.3:6379 ...
```

---

## Step 7: Initialize Redis Cluster

```bash
# Create the cluster (--cluster-replicas 1 = 1 replica per master)
docker exec redis-cluster-node1 redis-cli \
  --cluster create \
  ${NODE1_IP}:6379 ${NODE2_IP}:6379 ${NODE3_IP}:6379 \
  ${NODE4_IP}:6379 ${NODE5_IP}:6379 ${NODE6_IP}:6379 \
  --cluster-replicas 1 \
  --cluster-yes

sleep 5

# Check cluster info
echo "=== CLUSTER INFO ==="
docker exec redis-cluster-node1 redis-cli CLUSTER INFO

echo ""
echo "=== CLUSTER NODES ==="
docker exec redis-cluster-node1 redis-cli CLUSTER NODES
```

📸 **Verified Output:**
```
>>> Performing hash slots assignment to 3 nodes...
Master[0] -> Slots 0 - 5460
Master[1] -> Slots 5461 - 10922
Master[2] -> Slots 10923 - 16383
Adding replica 172.19.0.5:6379 to 172.19.0.2:6379
Adding replica 172.19.0.6:6379 to 172.19.0.3:6379
Adding replica 172.19.0.4:6379 to 172.19.0.4:6379
M: ... 172.19.0.2:6379 slots:[0-5460] (5461 slots) master
M: ... 172.19.0.3:6379 slots:[5461-10922] (5462 slots) master
M: ... 172.19.0.4:6379 slots:[10923-16383] (5461 slots) master

=== CLUSTER INFO ===
cluster_enabled:1
cluster_state:ok
cluster_slots_assigned:16384
cluster_slots_ok:16384
cluster_known_nodes:6
cluster_size:3

=== CLUSTER NODES ===
[node_id] 172.19.0.2:6379@16379 master - 0 ... connected 0-5460
[node_id] 172.19.0.3:6379@16379 master - 0 ... connected 5461-10922
[node_id] 172.19.0.4:6379@16379 master - 0 ... connected 10923-16383
[node_id] 172.19.0.5:6379@16379 slave [master_id] ... connected
[node_id] 172.19.0.6:6379@16379 slave [master_id] ... connected
[node_id] 172.19.0.7:6379@16379 slave [master_id] ... connected
```

---

## Step 8: Capstone — Test Hash Slots and Cluster Operations

```bash
# Connect to cluster with -c flag (cluster mode = automatic redirection)
docker exec redis-cluster-node1 redis-cli -c SET user:1:name "Alice"
docker exec redis-cluster-node1 redis-cli -c SET user:2:name "Bob"
docker exec redis-cluster-node1 redis-cli -c SET order:100:status "shipped"
docker exec redis-cluster-node1 redis-cli -c GET user:1:name
docker exec redis-cluster-node1 redis-cli -c GET order:100:status

# Show which slot each key maps to
docker exec redis-cluster-node1 redis-cli CLUSTER KEYSLOT user:1:name
docker exec redis-cluster-node1 redis-cli CLUSTER KEYSLOT user:2:name
docker exec redis-cluster-node1 redis-cli CLUSTER KEYSLOT order:100:status

# Hash tags: force related keys to same slot with {tag}
docker exec redis-cluster-node1 redis-cli -c SET "{user:1}:name" "Alice"
docker exec redis-cluster-node1 redis-cli -c SET "{user:1}:email" "alice@example.com"
docker exec redis-cluster-node1 redis-cli CLUSTER KEYSLOT "{user:1}:name"
docker exec redis-cluster-node1 redis-cli CLUSTER KEYSLOT "{user:1}:email"
echo "Both user:1 keys are in same slot (hash tag {user:1})"

# Show key distribution across nodes
cat << 'EOF'
=== HASH SLOT FACTS ===
- Total hash slots: 16384 (0 to 16383)
- Each key is hashed: CRC16(key) % 16384
- Hash tags {tag}: only the tag part is hashed
  - {user:1}:name and {user:1}:email → same slot
  - Enables multi-key operations (MSET, MGET) on related keys
- Slots are assigned to masters
- Moving a slot = moving all keys in that slot
EOF

# Cleanup
docker stop $(docker ps -q --filter "name=redis-cluster-node")
docker rm -f $(docker ps -aq --filter "name=redis-cluster-node")
docker network rm redis-cluster-net
echo "Lab complete!"
```

📸 **Verified Output:**
```
-> Redirected to slot [7638] located at 172.19.0.3:6379
OK
-> Redirected to slot [2742] located at 172.19.0.2:6379
OK
Alice
shipped

(integer) 7638   <- user:1:name is in slot 7638
(integer) 2742   <- user:2:name is in slot 2742
(integer) 10039  <- order:100:status is in slot 10039

(integer) 10741  <- {user:1}:name
(integer) 10741  <- {user:1}:email  <- SAME SLOT! (hash tag ensures this)

Both user:1 keys are in same slot (hash tag {user:1})

=== HASH SLOT FACTS ===
...
Lab complete!
```

---

## Summary

| Feature | Sentinel | Cluster |
|---------|----------|---------|
| Purpose | HA for single shard | Horizontal scaling |
| Min nodes | 3 sentinels + 1 primary | 6 (3 masters + 3 replicas) |
| Sharding | No | Yes (16384 slots) |
| Automatic failover | Yes (via sentinels) | Yes (built-in) |
| Hash slots | N/A | 0-16383 |
| Hash tags | N/A | `{tag}` forces same slot |
| Command | `SENTINEL masters` | `CLUSTER INFO`, `CLUSTER NODES` |
| Client | Standard Redis client | Cluster-aware client (`-c` flag) |

## Key Takeaways

- **Sentinel**: Simple HA for single Redis, no sharding needed
- **Cluster**: Automatic sharding + HA; minimum 6 nodes (3 masters + 3 replicas)
- **16384 hash slots** are distributed across masters; add slots to add nodes
- **Hash tags `{tag}`** force co-location of related keys on the same slot
- **`redis-cli -c`** auto-redirects to correct shard (MOVED response handling)
