# Lab 17: Real-Time AI Inference

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Real-time AI inference requires sub-100ms end-to-end pipelines from data ingestion to model decision. This lab covers streaming inference architecture, latency budgeting, feature freshness, model warm-up, blue-green model deployment, and circuit breaker patterns.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Real-Time AI Inference Pipeline                 │
├──────────────────────────────────────────────────────────────┤
│  Event Source                                                │
│  (Kafka Topic) → Feature Computation → Online Feature Store │
│       ↓              (Flink, < 5ms)        (Redis, < 1ms)   │
│  Feature Assembly                                            │
│  (join event + stored features, < 2ms)                      │
│       ↓                                                      │
│  Model Inference (ML server, < 20ms)                        │
│       ↓                                                      │
│  Post-processing → Action/Response (< 5ms)                  │
│  Total budget: < 50ms                                        │
├──────────────────────────────────────────────────────────────┤
│  CIRCUIT BREAKER: fallback to rule-based if model fails     │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Streaming Inference Architecture

**Event-Driven ML Pipeline:**
```
User Action → Kafka Producer → Kafka Topic
                                    ↓
                         Flink Streaming Job:
                           1. Parse event
                           2. Compute real-time features
                           3. Enrich with stored features (Redis lookup)
                           4. Assemble feature vector
                           5. Call Model API
                           6. Process prediction
                           7. Emit action to output topic
                                    ↓
                         Action Consumer:
                           - Block transaction (fraud)
                           - Show personalized content
                           - Trigger alert
```

**Kafka Integration with ML:**
```
Topic: payment_events → Flink job → model API → Topic: fraud_decisions
Topic: clickstream → Flink job → model API → Topic: recommendations
Topic: login_events → Flink job → model API → Topic: risk_scores
```

**Flink vs Spark Streaming for ML:**

| Dimension | Apache Flink | Spark Streaming |
|-----------|-------------|----------------|
| Latency | ~10-50ms (true streaming) | ~100ms-1s (micro-batch) |
| State | Native stateful (feature computation) | Limited |
| Exactly-once | ✅ | ✅ (with Kafka) |
| Python support | PyFlink | PySpark |
| Ecosystem | Kafka-native | Spark ecosystem |

> 💡 For sub-100ms latency requirements, Flink is the clear choice. Spark Streaming's micro-batch architecture adds latency.

---

## Step 2: Latency Budget Design

**P50/P95/P99 Latency Percentiles:**
```
P50: Median (typical user experience)
P95: 95th percentile (experience for majority of users)
P99: 99th percentile (tail latency, worst common experience)

Why P99 matters: In 1000 requests/second, 10 requests hit P99 every second
                  Users who hit P99 repeatedly churn
```

**Latency Budget Decomposition:**
```
Total SLO: P99 < 50ms
   ├── Network (client to server): 5ms
   ├── Feature extraction (event): 2ms
   ├── Feature store lookup (Redis): 1ms
   ├── Feature assembly: 1ms
   ├── Model inference: 20ms
   ├── Post-processing: 2ms
   └── Network (response): 5ms
   Buffer: 14ms
   Total: 50ms
```

**Latency Optimization Techniques:**

| Technique | Latency Reduction | Implementation |
|-----------|------------------|---------------|
| Co-location | 5-10ms | Deploy model server in same AZ as feature store |
| Feature pre-computation | 2-5ms | Compute features async, store in Redis |
| Model quantization | 30-50% | INT8 or INT4 quantization |
| ONNX export | 20-40% | Export to ONNX, use ORT inference |
| Batching (if async ok) | 3-5x throughput | Dynamic batching |
| gRPC vs REST | 5x | Switch to gRPC for model calls |

---

## Step 3: Feature Freshness Requirements

Different features have different freshness requirements.

**Feature Freshness Matrix:**

| Feature Type | Example | Max Staleness | Update Mechanism |
|-------------|---------|--------------|-----------------|
| Real-time event | current transaction amount | 0ms (event itself) | Kafka event |
| Near-real-time | transactions in last 5 min | < 30 seconds | Flink → Redis |
| Session | user session features | < 5 minutes | Session service |
| Daily | avg spend last 30 days | < 24 hours | Daily Spark job |
| Static | account age, demographics | < 7 days | Weekly refresh |

**Feature Staleness Detection:**
```
Feature value in Redis includes: value + computed_at_timestamp

At serving time:
  feature_age = now() - computed_at_timestamp
  if feature_age > max_staleness[feature_name]:
    log warning: stale feature
    option 1: use stale value (with staleness flag)
    option 2: recompute synchronously (adds latency)
    option 3: use fallback value
```

---

## Step 4: Model Warm-Up

Cold model inference (first request) is 10-100x slower than warm inference.

**Cold Start Sources:**
```
1. Model loading: reading weights from disk/S3 → GPU memory
   Mitigation: pre-load models at startup

2. JIT compilation: TorchScript, TensorRT optimization
   Mitigation: run warmup requests at startup

3. CUDA initialization: first GPU kernel invocation
   Mitigation: run dummy inference at startup

4. Feature store connections: Redis connection pool setup
   Mitigation: pre-warm connection pools
```

**Warm-Up Strategy:**
```python
# At service startup:
def warmup(model, feature_store):
    print("Warming up model...")
    # 1. Pre-load model to GPU
    model.to('cuda')
    
    # 2. Run dummy inference (triggers JIT compilation)
    dummy_input = torch.zeros(1, 100).cuda()
    for _ in range(10):
        _ = model(dummy_input)
    
    # 3. Warm up feature store connections
    feature_store.get_online_features(entity_rows=[{"customer_id": -1}])
    
    print("Warm-up complete. Ready for traffic.")
```

**Minimum Replicas for Zero Cold Starts:**
```
Set min_replicas = 2 (never scale to zero)
Use liveness/readiness probes to delay traffic until warm-up complete
Pre-scale before predicted traffic spikes (time-of-day scheduling)
```

---

## Step 5: Blue-Green Model Deployment

Zero-downtime model updates using blue-green deployment.

**Blue-Green for ML:**
```
BLUE (current production):  Model v1.0, serving 100% traffic
GREEN (new version):        Model v1.1, deployed but receiving 0% traffic

Validation phase:
  - Run smoke tests on GREEN
  - Compare GREEN vs BLUE on validation set
  - Shadow traffic: route 10% to GREEN, compare predictions
  
Switch:
  - Route 100% to GREEN (single DNS/load balancer change)
  - BLUE remains running for rollback (15-30 min)
  
Rollback (< 30 seconds):
  - Route 100% back to BLUE
  - Investigate GREEN issues
```

**Why Blue-Green for ML > Code:**
```
Code: rollback if error rate increases
ML: rollback if:
  - Error rate increases (hard failure)
  - Prediction distribution shifts (soft failure)
  - Model quality metric drops (quality failure)
  - Latency SLO breached (performance failure)
  - Fairness metrics violated (governance failure)
```

---

## Step 6: Circuit Breaker Pattern

Prevent cascading failures when the ML model is slow or unavailable.

**Circuit Breaker States:**
```
CLOSED (normal): requests pass through to model
    ↓ (failure rate > threshold)
OPEN (tripped): requests bypass model → fallback immediately
    ↓ (after timeout_seconds)
HALF-OPEN (testing): let one request through
    ↓ (success) → CLOSED
    ↓ (failure) → OPEN
```

**ML-Specific Circuit Breaker Configuration:**
```
failure_threshold: 5 failures in 10 seconds
timeout_seconds: 30 (how long to stay OPEN)
success_threshold: 3 successes to close

What counts as "failure":
  - Model response time > 200ms
  - HTTP 500 from model server
  - Model returns confidence < 0.1 (degenerate output)
  
Fallback strategy:
  - Return most recent cached prediction
  - Use simpler rule-based logic
  - Return safe default (approve/reject based on risk appetite)
```

---

## Step 7: Online Feature Computation

Real-time features computed from the event stream before model inference.

**Real-Time Feature Patterns:**

| Pattern | Example | Implementation |
|---------|---------|---------------|
| Count aggregation | Transactions in last 5 min | Redis INCR + TTL |
| Sum aggregation | Total amount today | Redis INCRBY + TTL |
| Distinct count | Unique merchants today | HyperLogLog (Redis) |
| Last-N events | Last 10 transaction amounts | Redis LPUSH + LTRIM |
| Sliding window | Velocity: N txns in 60 seconds | Redis Sorted Set + ZRANGEBYSCORE |

**Redis Feature Patterns:**
```python
# Transaction count (last 5 minutes)
redis.execute_command("INCR", f"txn_count:{customer_id}:5min")
redis.execute_command("EXPIRE", f"txn_count:{customer_id}:5min", 300)

# Running sum with time-based key rotation
hour_key = f"amount_sum:{customer_id}:{datetime.hour}"
redis.incrbyfloat(hour_key, transaction_amount)
redis.expire(hour_key, 3600)

# Velocity check: timestamps of recent events
redis.zadd(f"txn_times:{customer_id}", {transaction_id: timestamp})
redis.zremrangebyscore(f"txn_times:{customer_id}", 0, timestamp - 60)
velocity_count = redis.zcard(f"txn_times:{customer_id}")
```

---

## Step 8: Capstone — Inference Pipeline Simulator

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
import random

np.random.seed(42)
random.seed(42)

class InferencePipeline:
    def __init__(self, name, latency_ms_mean, latency_ms_std):
        self.name = name
        self.latency_mean = latency_ms_mean
        self.latency_std = latency_ms_std
        self.latencies = []
        self.circuit_open = False
        self.failure_count = 0
    
    def infer(self, warm=True):
        cold_penalty = 0 if warm else np.random.uniform(500, 2000)
        latency = max(1, np.random.normal(self.latency_mean, self.latency_std) + cold_penalty)
        
        if np.random.random() < 0.02:
            self.failure_count += 1
            if self.failure_count >= 3:
                self.circuit_open = True
            return None, latency
        
        self.failure_count = max(0, self.failure_count - 1)
        self.circuit_open = False
        self.latencies.append(latency)
        return 'prediction', latency
    
    def stats(self):
        if not self.latencies:
            return {}
        arr = np.array(self.latencies)
        return {
            'p50': round(np.percentile(arr, 50), 2),
            'p95': round(np.percentile(arr, 95), 2),
            'p99': round(np.percentile(arr, 99), 2),
            'mean': round(arr.mean(), 2),
            'count': len(arr),
        }

print('=== Real-Time AI Inference Simulator ===')
print()

stages = [
    InferencePipeline('Feature_Extraction', 2, 0.5),
    InferencePipeline('Model_Inference', 15, 3),
    InferencePipeline('Post_Processing', 1, 0.3),
]

n_requests = 1000
pipeline_latencies = []
for req in range(n_requests):
    total = 0
    failed = False
    for stage in stages:
        result, lat = stage.infer(warm=True)
        if result is None:
            failed = True
            break
        total += lat
    if not failed:
        pipeline_latencies.append(total)

pipeline_arr = np.array(pipeline_latencies)
print(f'Total requests: {n_requests}')
print(f'Successful: {len(pipeline_latencies)} ({len(pipeline_latencies)/n_requests*100:.1f}%)')
print()
print('Per-stage latency breakdown:')
for stage in stages:
    s = stage.stats()
    print(f'  {stage.name:25s}: p50={s[\"p50\"]:5.1f}ms p95={s[\"p95\"]:5.1f}ms p99={s[\"p99\"]:5.1f}ms')

print()
print('End-to-end pipeline:')
print(f'  p50={np.percentile(pipeline_arr, 50):.1f}ms')
print(f'  p95={np.percentile(pipeline_arr, 95):.1f}ms')
print(f'  p99={np.percentile(pipeline_arr, 99):.1f}ms')
slo = 50
print(f'  SLO ({slo}ms): {\"PASS\" if np.percentile(pipeline_arr, 99) < slo else \"FAIL\"}')

print()
print('Latency histogram:')
hist, edges = np.histogram(pipeline_arr, bins=8)
for count, left, right in zip(hist, edges[:-1], edges[1:]):
    bar = '#' * int(count / max(hist) * 30)
    print(f'  {left:5.0f}-{right:5.0f}ms | {bar} {count}')
"
```

📸 **Verified Output:**
```
=== Real-Time AI Inference Simulator ===

Total requests: 1000
Successful: 938 (93.8%)

Per-stage latency breakdown:
  Feature_Extraction       : p50=  2.0ms p95=  2.8ms p99=  3.1ms
  Model_Inference          : p50= 15.1ms p95= 20.1ms p99= 21.8ms
  Post_Processing          : p50=  1.0ms p95=  1.5ms p99=  1.7ms

End-to-end pipeline:
  p50=18.3ms
  p95=23.2ms
  p99=24.8ms
  SLO (50ms): PASS

Latency histogram:
      8-   11ms | # 14
     11-   14ms | ##### 60
     14-   17ms | ################## 194
     17-   19ms | ############################## 318
     19-   22ms | ####################### 254
     22-   25ms | ######## 87
     25-   27ms |  9
     27-   30ms |  2
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Streaming Pipeline | Kafka → Flink (features) → Redis (store) → Model → Action |
| Latency Budget | Decompose P99 SLO across each pipeline stage |
| Feature Freshness | Different features have different max staleness; monitor staleness in prod |
| Model Warm-Up | Pre-load model + run dummy inference at startup; min replicas = 2 |
| Blue-Green Deployment | Zero-downtime; instant rollback; validate on shadow traffic first |
| Circuit Breaker | 3 states: CLOSED → OPEN → HALF-OPEN; fallback to rules or cache |
| Online Features | Redis patterns: INCR+TTL (counts), Sorted Sets (velocity), HyperLogLog (distinct) |

**Next Lab:** [Lab 18: AI SOC Automation →](lab-18-ai-soc-automation.md)
