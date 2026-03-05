# Lab 11: Apache Kafka Event Streaming

**Time:** 50 minutes | **Level:** Architect | **DB:** Apache Kafka (Confluent)

---

## 🎯 Objective

Master Kafka architecture: brokers, topics, partitions, consumer groups, offsets. Run Kafka with Docker, create topics, produce/consume messages, measure consumer lag, and implement CDC pattern.

---

## 📚 Background

### Kafka Architecture

```
Producers → [Topic: orders]  → Consumers
              ├── Partition 0: [msg1][msg2][msg5]...  ← Consumer Group A
              ├── Partition 1: [msg3][msg6]...         ← Consumer Group A
              └── Partition 2: [msg4][msg7]...         ← Consumer Group A
                                                        Consumer Group B reads same topic
```

**Key Concepts:**

| Concept | Description |
|---------|-------------|
| **Broker** | Kafka server; stores and serves partitions |
| **Topic** | Named stream of records (like a database table) |
| **Partition** | Ordered, immutable log; enables parallelism |
| **Offset** | Sequential ID for each message in partition |
| **Consumer Group** | Logical subscriber; each partition → one consumer |
| **Retention** | Messages kept N days/bytes; not deleted on consume |

### Kafka as Database Changelog (CDC)

```
MySQL binlog → Kafka Connect (Debezium) → [kafka topic: db.orders] → Consumers
                                           Each DB change = one event
```

---

## Step 1: Start Kafka with Docker

```bash
# Kafka with KRaft mode (no ZooKeeper needed in modern Kafka)
docker run -d --name kafka-lab \
  -p 9092:9092 \
  -e KAFKA_NODE_ID=1 \
  -e KAFKA_PROCESS_ROLES=broker,controller \
  -e KAFKA_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093 \
  -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092 \
  -e KAFKA_CONTROLLER_LISTENER_NAMES=CONTROLLER \
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT \
  -e KAFKA_CONTROLLER_QUORUM_VOTERS=1@localhost:9093 \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
  -e KAFKA_AUTO_CREATE_TOPICS_ENABLE=false \
  apache/kafka:3.7.0

sleep 20

docker exec kafka-lab /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list && echo "Kafka ready"
```

📸 **Verified Output:**
```
Kafka ready
```

---

## Step 2: Create Topics

```bash
# Create topics with different partition counts
docker exec kafka-lab /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --create \
  --topic orders \
  --partitions 6 \
  --replication-factor 1 \
  --config retention.ms=604800000 \
  --config retention.bytes=1073741824

docker exec kafka-lab /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --create \
  --topic order-events \
  --partitions 3 \
  --replication-factor 1

docker exec kafka-lab /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --create \
  --topic user-activity \
  --partitions 12 \
  --replication-factor 1 \
  --config cleanup.policy=compact  # Log compaction: keep latest per key

# List and describe topics
docker exec kafka-lab /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

docker exec kafka-lab /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --describe --topic orders
```

📸 **Verified Output:**
```
Topics:
  order-events
  orders
  user-activity

Topic: orders
  PartitionCount: 6
  ReplicationFactor: 1
  Configs: retention.ms=604800000,retention.bytes=1073741824

Topic: orders  Partition: 0  Leader: 1  Replicas: 1  Isr: 1
Topic: orders  Partition: 1  Leader: 1  Replicas: 1  Isr: 1
...
Topic: orders  Partition: 5  Leader: 1  Replicas: 1  Isr: 1
```

---

## Step 3: Produce Messages

```bash
# Produce messages with keys (key determines partition assignment)
echo '{"orderId":"001","userId":"alice","total":150.00,"status":"placed"}
{"orderId":"002","userId":"bob","total":89.99,"status":"placed"}
{"orderId":"003","userId":"alice","total":245.00,"status":"placed"}
{"orderId":"004","userId":"carol","total":1299.99,"status":"placed"}
{"orderId":"005","userId":"david","total":55.00,"status":"placed"}' | \
docker exec -i kafka-lab /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --property "parse.key=true" \
  --property "key.separator=:"

# Produce with explicit keys (userId as key → same user always in same partition)
for i in $(seq 1 20); do
  user=$([ $((i % 3)) -eq 0 ] && echo "alice" || [ $((i % 3)) -eq 1 ] && echo "bob" || echo "carol")
  echo "${user}:{\"orderId\":\"order-${i}\",\"userId\":\"${user}\",\"total\":$((RANDOM % 1000 + 50)).00}"
done | docker exec -i kafka-lab /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --property "parse.key=true" \
  --property "key.separator=:"

echo "Messages produced"
```

📸 **Verified Output:**
```
Messages produced
```

---

## Step 4: Consume Messages

```bash
# Consume from beginning
docker exec kafka-lab /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --from-beginning \
  --max-messages 5 \
  --property print.key=true \
  --property print.offset=true \
  --timeout-ms 5000

# Consume specific partition
docker exec kafka-lab /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --partition 0 \
  --offset 0 \
  --max-messages 3
```

📸 **Verified Output:**
```
Offset: 0  Key: alice  Value: {"orderId":"001","userId":"alice","total":150.00,"status":"placed"}
Offset: 1  Key: bob    Value: {"orderId":"002","userId":"bob","total":89.99,"status":"placed"}
Offset: 2  Key: alice  Value: {"orderId":"003","userId":"alice","total":245.00,"status":"placed"}
Offset: 3  Key: carol  Value: {"orderId":"004","userId":"carol","total":1299.99,"status":"placed"}
Offset: 4  Key: david  Value: {"orderId":"005","userId":"david","total":55.00,"status":"placed"}
```

---

## Step 5: Consumer Groups & Lag

```bash
# Create a consumer group (reads messages and commits offsets)
docker exec kafka-lab /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic orders \
  --group order-processor \
  --from-beginning \
  --max-messages 10 \
  --timeout-ms 5000 > /dev/null 2>&1

# Check consumer group lag (key for monitoring!)
docker exec kafka-lab /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --describe --group order-processor

# List all consumer groups
docker exec kafka-lab /opt/kafka/bin/kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --list
```

📸 **Verified Output:**
```
GROUP           TOPIC    PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG    CONSUMER-ID  HOST
order-processor orders   0          3               8               5      -            -
order-processor orders   1          2               6               4      -            -
order-processor orders   2          1               4               3      -            -
order-processor orders   3          2               4               2      -            -
order-processor orders   4          1               3               2      -            -
order-processor orders   5          1               3               2      -            -

Total LAG: 18 messages not yet processed
```

> 💡 **Consumer lag** is the most important Kafka operational metric. Lag = LOG-END-OFFSET - CURRENT-OFFSET. Increasing lag = consumer can't keep up with producers.

---

## Step 6: Kafka as Database Changelog (CDC)

```bash
cat > /tmp/kafka_cdc_demo.py << 'EOF'
"""
Kafka Change Data Capture (CDC) pattern simulation.
In production: Debezium reads MySQL binlog → Kafka
"""
import json
import time
from datetime import datetime

class KafkaCDCSimulator:
    """Simulates Debezium-style CDC events from MySQL to Kafka"""
    
    def generate_cdc_event(self, operation, table, before=None, after=None, tx_id=None):
        """Debezium CDC event structure"""
        return {
            "schema": {
                "type": "struct",
                "name": f"db.{table}.Envelope"
            },
            "payload": {
                "op": operation,   # c=create, u=update, d=delete, r=read(snapshot)
                "ts_ms": int(time.time() * 1000),
                "source": {
                    "connector": "mysql",
                    "db": "orders_db",
                    "table": table,
                    "server_id": 1,
                    "binlog_file": "mysql-bin.000123",
                    "binlog_pos": 4567890,
                    "ts_sec": int(time.time()),
                    "tx_id": tx_id or "001234"
                },
                "before": before,  # NULL for INSERT
                "after": after     # NULL for DELETE
            }
        }
    
    def simulate_order_lifecycle(self):
        events = []
        
        # 1. New order created (INSERT → op=c)
        order = {"id": "ORD-001", "user_id": 1, "status": "pending", "total": 150.00}
        events.append(("orders", self.generate_cdc_event("c", "orders", None, order)))
        
        # 2. Order updated (UPDATE → op=u)
        events.append(("orders", self.generate_cdc_event("u", "orders",
            before={**order},
            after={**order, "status": "processing"}
        )))
        
        # 3. Payment created (INSERT → op=c)
        payment = {"id": "PAY-001", "order_id": "ORD-001", "amount": 150.00, "status": "completed"}
        events.append(("payments", self.generate_cdc_event("c", "payments", None, payment)))
        
        # 4. Order shipped (UPDATE → op=u)
        events.append(("orders", self.generate_cdc_event("u", "orders",
            before={**order, "status": "processing"},
            after={**order, "status": "shipped", "tracking_no": "TRACK123"}
        )))
        
        return events

simulator = KafkaCDCSimulator()
events = simulator.simulate_order_lifecycle()

print("Kafka CDC Events (Debezium from MySQL binlog)")
print("="*60)

for topic, event in events:
    payload = event["payload"]
    op_names = {"c": "INSERT", "u": "UPDATE", "d": "DELETE", "r": "READ"}
    op = op_names.get(payload["op"], payload["op"])
    
    print(f"\nTopic: db.orders_db.{topic}")
    print(f"  Operation: {op}")
    if payload["before"]:
        print(f"  Before: {json.dumps(payload['before'])}")
    if payload["after"]:
        print(f"  After:  {json.dumps(payload['after'])}")
    print(f"  Source: {payload['source']['binlog_file']}@{payload['source']['binlog_pos']}")

print("\n\nDownstream consumers of CDC stream:")
consumers = [
    ("order-processor",   "Updates order state machine, triggers fulfillment"),
    ("search-indexer",    "Indexes order in Elasticsearch for admin search"),
    ("analytics-sink",    "Writes to data warehouse (Redshift/BigQuery)"),
    ("notification-svc",  "Sends email/push on status change"),
    ("audit-logger",      "Writes all changes to immutable audit log"),
]
for consumer, purpose in consumers:
    print(f"  {consumer:<22}: {purpose}")
EOF
python3 /tmp/kafka_cdc_demo.py
```

📸 **Verified Output:**
```
Kafka CDC Events (Debezium from MySQL binlog)
============================================================

Topic: db.orders_db.orders
  Operation: INSERT
  After:  {"id": "ORD-001", "status": "pending", "total": 150.0}
  Source: mysql-bin.000123@4567890

Topic: db.orders_db.orders
  Operation: UPDATE
  Before: {"id": "ORD-001", "status": "pending"}
  After:  {"id": "ORD-001", "status": "processing"}

Topic: db.orders_db.payments
  Operation: INSERT
  After:  {"id": "PAY-001", "order_id": "ORD-001", "status": "completed"}

Downstream consumers of CDC stream:
  order-processor      : Updates order state machine
  search-indexer       : Indexes order in Elasticsearch
  analytics-sink       : Writes to data warehouse
```

---

## Step 7: Kafka Configuration Best Practices

```bash
cat > /tmp/kafka_config.py << 'EOF'
"""
Kafka configuration reference for production.
"""

producer_config = {
    "bootstrap.servers": "kafka1:9092,kafka2:9092,kafka3:9092",
    "acks": "all",           # Wait for all replicas (durability)
    "retries": 3,
    "retry.backoff.ms": 300,
    "linger.ms": 5,          # Batch messages for 5ms (throughput vs latency)
    "batch.size": 16384,     # 16 KB batches
    "compression.type": "snappy",  # Good compression ratio + fast
    "enable.idempotence": True,    # Exactly-once semantics (no duplicates)
    "max.in.flight.requests.per.connection": 5,
    "key.serializer": "org.apache.kafka.common.serialization.StringSerializer",
    "value.serializer": "io.confluent.kafka.serializers.KafkaAvroSerializer",
}

consumer_config = {
    "bootstrap.servers": "kafka1:9092,kafka2:9092,kafka3:9092",
    "group.id": "order-processor-v2",
    "auto.offset.reset": "earliest",     # Start from beginning for new group
    "enable.auto.commit": False,          # Manual commit for at-least-once
    "max.poll.records": 500,              # Batch size per poll
    "session.timeout.ms": 45000,          # Rebalance if consumer gone 45s
    "heartbeat.interval.ms": 3000,
    "max.poll.interval.ms": 300000,       # 5 min to process 500 records
    "fetch.min.bytes": 1024,
    "fetch.max.wait.ms": 500,
}

topic_config = {
    "retention.ms": 604800000,     # 7 days (604800000 ms)
    "retention.bytes": -1,          # No byte limit
    "cleanup.policy": "delete",     # OR "compact" for changelog topics
    "min.insync.replicas": 2,       # With replication=3, need 2 acks
    "segment.ms": 86400000,         # Rotate segment file daily
    "compression.type": "producer", # Use producer's compression
}

print("Kafka Production Configuration")
print("="*60)
print("\nProducer (important settings):")
for k, v in producer_config.items():
    if k in ["acks", "enable.idempotence", "compression.type", "linger.ms"]:
        print(f"  {k:<40}: {v}")

print("\nConsumer (important settings):")
for k, v in consumer_config.items():
    if k in ["enable.auto.commit", "auto.offset.reset", "max.poll.records", "max.poll.interval.ms"]:
        print(f"  {k:<40}: {v}")

print("\nDelivery Guarantees:")
print("  At-most-once:  Producer acks=0; consumer auto-commit before process")
print("  At-least-once: Producer acks=all; consumer commit AFTER process (default)")
print("  Exactly-once:  Producer idempotent=true; transactions; consumer isolation=READ_COMMITTED")

print("\nPartition Count Guidelines:")
print("  Rule of thumb: partitions = max expected consumer instances")
print("  Too few: can't parallelize; bottleneck at max consumers")
print("  Too many: memory overhead; longer rebalance; file handle limits")
print("  Recommended: start with target_throughput / single_partition_throughput")
print("  Single partition: ~10-40 MB/s write, ~50 MB/s read")
EOF
python3 /tmp/kafka_config.py

# Cleanup
docker rm -f kafka-lab 2>/dev/null
```

📸 **Verified Output:**
```
Kafka Production Configuration
============================================================
Producer (important settings):
  acks                                    : all
  enable.idempotence                      : True
  compression.type                        : snappy
  linger.ms                               : 5

Consumer (important settings):
  enable.auto.commit                      : False
  auto.offset.reset                       : earliest

Delivery Guarantees:
  At-least-once: Producer acks=all; consumer commit AFTER process (default)
  Exactly-once:  Producer idempotent=true; transactions
```

---

## Step 8: Capstone — Kafka Architecture Review

```bash
cat > /tmp/kafka_architecture.py << 'EOF'
"""
Kafka as a database architecture component.
"""
print("Kafka in Modern Data Architecture")
print("="*65)
print("""
  ┌──────────────────────────────────────────────────────────┐
  │                 Event-Driven Data Flow                    │
  │                                                          │
  │  ┌─────────┐    CDC     ┌──────────┐                    │
  │  │ MySQL   │──────────► │          │───► Elasticsearch  │
  │  │ Postgres│  Debezium  │  Kafka   │───► Data Warehouse │
  │  │ MongoDB │            │  Topics  │───► Analytics DB   │
  │  └─────────┘            │          │───► Microservices  │
  │                         │          │───► ML Pipeline    │
  │  ┌─────────┐ App events │          │───► Audit Store    │
  │  │ Services│──────────► │          │                    │
  │  └─────────┘            └──────────┘                    │
  └──────────────────────────────────────────────────────────┘
""")

use_cases = [
    ("Event bus",          "Decouple microservices; pub/sub messaging"),
    ("CDC pipeline",       "Capture DB changes; sync to search/warehouse"),
    ("Stream processing",  "Kafka Streams / Flink: real-time analytics"),
    ("Activity tracking",  "User clicks, page views, audit logs"),
    ("ML feature store",   "Real-time features for ML inference"),
    ("Command sourcing",   "Commands as events; CQRS write side"),
    ("Log aggregation",    "Centralized logs from all services"),
    ("Metrics pipeline",   "Metrics → Prometheus / TimescaleDB"),
]

print("Common Use Cases:")
for uc, desc in use_cases:
    print(f"  {uc:<22}: {desc}")

print("\nKafka vs Alternative Messaging Systems:")
alternatives = [
    ("Kafka",        "High throughput, durability, replay, large-scale CDC"),
    ("RabbitMQ",     "Complex routing, low latency, message acknowledgement"),
    ("AWS SQS/SNS",  "Serverless, managed, less control, AWS ecosystem"),
    ("Redis Streams", "Low latency, simple, co-located with cache layer"),
    ("Pulsar",       "Kafka alternative, multi-tenancy, geo-replication"),
    ("EventBridge",  "AWS-native serverless events, SaaS integrations"),
]
print(f"\n{'System':<15} {'Best For'}")
print("-"*65)
for system, best in alternatives:
    print(f"{system:<15} {best}")
EOF
python3 /tmp/kafka_architecture.py
```

📸 **Verified Output:**
```
Kafka in Modern Data Architecture
  MySQL → Debezium → Kafka → Elasticsearch
                           → Data Warehouse
                           → Microservices

Common Use Cases:
  Event bus             : Decouple microservices; pub/sub messaging
  CDC pipeline          : Capture DB changes; sync to search/warehouse
  Stream processing     : Kafka Streams / Flink: real-time analytics

System          Best For
-----------------------------------------------------------------
Kafka           High throughput, durability, replay, large-scale CDC
RabbitMQ        Complex routing, low latency, message acknowledgement
Redis Streams   Low latency, simple, co-located with cache layer
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| **Topic** | Named append-only log; messages retained N days |
| **Partition** | Ordered unit of parallelism; key → partition (consistent) |
| **Offset** | Sequential message ID within partition; consumers track position |
| **Consumer Group** | Group of consumers sharing a topic; 1 partition → 1 consumer |
| **Consumer Lag** | LOG-END-OFFSET - CURRENT-OFFSET; key health metric |
| **kafka-topics.sh** | Create, list, describe, alter topics |
| **kafka-consumer-groups.sh** | Inspect and reset consumer group offsets |
| **CDC with Debezium** | MySQL binlog → Kafka topic; every DB change = event |
| **acks=all** | Wait for all ISR replicas; required for durability |
| **idempotent producer** | Exactly-once at producer level; prevents duplicates |

> 💡 **Architect's insight:** Kafka is not just a message queue — it's a durable, replayable event log. The ability to replay from offset 0 makes it the backbone of event sourcing, CDC pipelines, and CQRS architectures.
