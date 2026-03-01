# Distributed Databases & Scaling

## Scaling Strategies

### Vertical Scaling (Scale Up)
Add more CPU/RAM/disk to existing server. Simple but limited.

### Horizontal Scaling (Scale Out)

**Read Replicas**
```
[Primary] ──→ [Replica 1]  ← Read traffic
          └─→ [Replica 2]  ← Read traffic
          └─→ [Replica 3]  ← Read traffic
Writes go to Primary only
```

**Sharding (Partitioning)**
```python
# Hash-based sharding
def get_shard(user_id, num_shards=4):
    return user_id % num_shards

# user_id 1001 → shard 1 (DB server 2)
# user_id 1002 → shard 2 (DB server 3)
# user_id 1003 → shard 3 (DB server 4)
# user_id 1004 → shard 0 (DB server 1)
```

## PostgreSQL High Availability (Patroni)

```yaml
# patroni.yml
scope: my-postgres-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008

etcd3:
  hosts: etcd1:2379,etcd2:2379,etcd3:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
  postgresql:
    use_pg_rewind: true

postgresql:
  listen: 0.0.0.0:5432
  connect_address: node1:5432
  data_dir: /var/lib/postgresql/data
  parameters:
    max_connections: 500
    shared_buffers: 4GB
    effective_cache_size: 12GB
    work_mem: 64MB
```

## CAP Theorem

Distributed systems can only guarantee 2 of 3:

| System | Consistency | Availability | Partition Tolerance |
|--------|------------|-------------|-------------------|
| PostgreSQL (single) | ✅ | ✅ | ❌ |
| Cassandra | ❌ | ✅ | ✅ |
| HBase | ✅ | ❌ | ✅ |
| DynamoDB | Configurable | ✅ | ✅ |
| MongoDB | Configurable | ✅ | ✅ |

## Database Architecture Patterns

### CQRS (Command Query Responsibility Segregation)
```
Write Operations → [Command DB] (PostgreSQL - normalized)
                          ↓ events
Read Operations ← [Query DB]  (Elasticsearch/Redis - denormalized)
```

### Event Sourcing
```python
# Store events, not current state
events = [
    {"type": "OrderPlaced", "order_id": 1, "amount": 999.99},
    {"type": "PaymentReceived", "order_id": 1},
    {"type": "OrderShipped", "order_id": 1, "tracking": "1ZY549..."},
]
# Current state = replay all events
```
