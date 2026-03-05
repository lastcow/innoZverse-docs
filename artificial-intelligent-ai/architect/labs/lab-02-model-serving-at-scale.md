# Lab 02: Model Serving at Scale

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Model serving is the bridge between trained models and business value. This lab covers serving patterns, model server architectures, latency-throughput trade-offs, deployment strategies, and SLO design for ML systems.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Model Serving Architecture                   │
├──────────────┬──────────────────┬───────────────────────────┤
│ Online Serving│  Batch Serving  │   Streaming Serving       │
│ (< 100ms)    │  (hours/minutes)│   (< 1 second)            │
│ REST/gRPC    │  Spark/Ray      │   Kafka + Flink            │
├──────────────┴──────────────────┴───────────────────────────┤
│         Load Balancer / API Gateway / Service Mesh          │
├─────────────────────────────────────────────────────────────┤
│  Model Server Pool (auto-scaled, K8s, GPU-enabled)          │
│  [Model v1.0 - 95%] [Model v1.1 - 5% canary]              │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Serving Patterns

Choose the right serving pattern based on latency requirements and data volume.

| Pattern | Latency | Throughput | Use Case | Complexity |
|---------|---------|-----------|---------|-----------|
| **Online** | < 100ms | Low-medium | Fraud detection, recommendations | Medium |
| **Batch** | Hours-days | Very high | Overnight scoring, ETL enrichment | Low |
| **Streaming** | < 1 second | Medium-high | Real-time alerts, live scoring | High |
| **Near-real-time** | 1-30 seconds | Medium | Personalization, content filtering | Medium |

**Decision Framework:**
```
Is real-time response required?
  YES → Is latency < 200ms needed?
    YES → Online serving (REST/gRPC)
    NO  → Streaming (Kafka + ML)
  NO  → How large is the dataset?
    < 1M rows/day → Batch (Spark)
    > 1M rows/day → Batch (Spark distributed)
```

> 💡 Most teams over-engineer for online serving when batch is sufficient. Ask: "Does the user need the prediction in < 1 second?"

---

## Step 2: REST vs gRPC Serving

| Dimension | REST | gRPC |
|-----------|------|------|
| Protocol | HTTP/1.1 | HTTP/2 |
| Payload | JSON (verbose) | Protobuf (compact) |
| Latency | Higher (JSON serialization) | 5-10x lower |
| Streaming | Limited | Native bi-directional |
| Client support | Universal | Requires gRPC client |
| Debugging | Easy (curl/browser) | Harder (need grpcurl) |
| Use case | External APIs, microservices | High-throughput internal services |

**When to choose gRPC:**
- High-throughput inference (> 10k RPS)
- Low-latency requirements (< 10ms)
- Embedding services (large vectors)
- Service-to-service communication

**REST API Design for ML:**
```
POST /v1/predict
{
  "model_version": "1.2.0",
  "instances": [{"feature_1": 0.5, "feature_2": 1.2}],
  "parameters": {"threshold": 0.8}
}

Response:
{
  "predictions": [{"score": 0.91, "label": "fraud"}],
  "model_version": "1.2.0",
  "latency_ms": 12
}
```

---

## Step 3: Model Server Architectures

**Comparison of Production Model Servers:**

| Server | Framework | GPU Support | Batching | Multi-model | Best For |
|--------|-----------|------------|---------|------------|---------|
| **TorchServe** | PyTorch | ✅ | ✅ | ✅ | PyTorch models |
| **TF Serving** | TensorFlow | ✅ | ✅ | ✅ | TensorFlow models |
| **Triton** | NVIDIA | ✅ (CUDA) | ✅ (dynamic) | ✅ | Multi-framework, GPU |
| **BentoML** | Any | ✅ | ✅ | ✅ | Python-first, fast dev |
| **KServe** | Any | ✅ | ✅ | ✅ | Kubernetes-native |
| **vLLM** | LLMs | ✅ | ✅ (continuous) | ✅ | LLM inference |

**Triton Architecture (NVIDIA):**
```
Client → HTTP/gRPC → Triton Inference Server
                          ↓
                    Model Repository
                    ├── model_a/ (TensorRT)
                    ├── model_b/ (ONNX)
                    └── ensemble_pipeline/
                          ↓
                    Dynamic Batching
                    GPU Instance Groups
```

> 💡 For LLM serving (Llama, Mistral), use vLLM with PagedAttention — it achieves 10-24x higher throughput vs naive serving through KV cache management.

---

## Step 4: Latency vs Throughput Trade-offs

These two metrics are fundamentally in tension. Understand the trade-off curve.

**Batching Effect:**
```
batch_size=1:   latency=5ms,   throughput=200 RPS  (low latency)
batch_size=8:   latency=9ms,   throughput=889 RPS  (balanced)
batch_size=32:  latency=21ms,  throughput=1524 RPS (high throughput)
batch_size=128: latency=69ms,  throughput=1856 RPS (max throughput)
```

**Key Insight:** GPU utilization improves with batch size, but P99 latency increases.

**SLO-Aware Batching Strategy:**
```
If P99_SLO = 50ms:
  - Find max batch_size where p99 < 50ms
  - Tune batching window (max_wait_time)
  - Use adaptive batching: increase batch during high load
```

**Batching Strategies:**

| Strategy | Description | Best For |
|----------|-------------|---------|
| **Static batching** | Fixed batch size, synchronous | Offline/batch serving |
| **Dynamic batching** | Waits max_wait_ms, fills batch | Mixed online serving |
| **Continuous batching** | Per-token for LLMs (vLLM) | LLM inference |
| **Micro-batching** | Very small batches, low latency | Streaming ML |

---

## Step 5: Canary, Shadow, and A/B Deployments

**Deployment Strategies Comparison:**

| Strategy | Traffic Split | Risk | Rollback | Use Case |
|----------|--------------|------|---------|---------|
| **Canary** | 95%/5% → gradual | Low | < 1 min | General production rollouts |
| **Blue-Green** | 0%/100% switch | Medium | < 30 sec | Zero-downtime deploys |
| **Shadow** | 100% mirror | None | N/A | Safe new model testing |
| **A/B Test** | 50%/50% (statistical) | Medium | < 1 min | Business metric experiments |

**Canary Deployment Process:**
```
Deploy v2 alongside v1
  ↓
Route 5% traffic → v2
  ↓
Monitor: error rate, latency, model metrics
  ↓
All healthy? → increase to 25% → 50% → 100%
  ↓
Detect problem? → route 100% back to v1 (instant rollback)
```

**Shadow Mode (Safest for ML):**
```
Production traffic → v1 (serves real responses)
                  ↘ v2 (shadow, no user impact)
                        ↓
                  Compare: latency, predictions, errors
                        ↓
                  No user sees v2 output
```

> 💡 Always run shadow mode for at least 48 hours before promoting an LLM or complex model to production. Collect real production distribution data.

---

## Step 6: SLO Design for ML Systems

Service Level Objectives for ML have two dimensions: latency AND model quality.

**Latency SLOs:**
```
Tier 1 (payment fraud):    P50 < 20ms,  P95 < 50ms,  P99 < 100ms
Tier 2 (recommendations):  P50 < 100ms, P95 < 300ms, P99 < 500ms
Tier 3 (batch scoring):    P50 < 5min,  P95 < 15min, P99 < 30min
```

**Model Quality SLOs:**
```
Precision >= 0.90 (measured over rolling 24h window)
Recall >= 0.85
PSI < 0.2 (feature drift)
Data freshness < 1 hour
```

**Error Budget Concept:**
```
SLO: 99.9% requests < 100ms
Error budget: 0.1% = 43.8 minutes/month
If error budget consumed > 50%: halt deploys, focus on reliability
If error budget < 10% consumed: accelerate feature delivery
```

---

## Step 7: Auto-scaling for Model Serving

**Kubernetes HPA for ML:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef:
    name: model-server
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: inference_requests_per_second
      target:
        averageValue: 100
```

**GPU-aware Scaling Considerations:**
- GPU pods take 30-60 seconds to start (model loading)
- Pre-warm minimum replicas to avoid cold starts
- Use GPU fractional allocation for small models (MIG on A100)
- Consider GPU sharing for low-QPS models

---

## Step 8: Capstone — Design High-Availability Model Serving

**Scenario:** Your fraud detection model must serve 10,000 RPS with P99 < 50ms, 99.99% availability.

**Verification — Run FastAPI + SLO Simulation:**

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
import random

def simulate_serving(batch_size, n_requests=100):
    latencies = []
    for _ in range(n_requests):
        base = 5 + batch_size * 0.5
        noise = random.gauss(0, 1)
        latencies.append(max(1, base + noise))
    latencies.sort()
    return {
        'p50': round(np.percentile(latencies, 50), 2),
        'p95': round(np.percentile(latencies, 95), 2),
        'p99': round(np.percentile(latencies, 99), 2),
        'throughput_rps': round(1000 / np.mean(latencies), 1)
    }

print('=== Model Serving SLO Analysis ===')
for bs in [1, 8, 32, 128]:
    stats = simulate_serving(bs)
    slo_ok = 'PASS' if stats['p99'] < 100 else 'FAIL'
    print(f'batch={bs:3d} | p50={stats[\"p50\"]:5.1f}ms | p95={stats[\"p95\"]:5.1f}ms | p99={stats[\"p99\"]:5.1f}ms | throughput={stats[\"throughput_rps\"]:5.1f} rps | SLO(p99<100ms): {slo_ok}')

print()
print('=== Deployment Strategies ===')
strategies = {
    'canary': {'traffic_split': '95/5', 'risk': 'low', 'rollback_time': '< 1min'},
    'blue_green': {'traffic_split': '0/100', 'risk': 'medium', 'rollback_time': '< 30sec'},
    'shadow': {'traffic_split': '100/0 (mirror)', 'risk': 'none', 'rollback_time': 'N/A'},
    'a_b_test': {'traffic_split': '50/50', 'risk': 'medium', 'rollback_time': '< 1min'},
}
for s, info in strategies.items():
    print(f'  {s:12s}: traffic={info[\"traffic_split\"]:20s} risk={info[\"risk\"]:8s} rollback={info[\"rollback_time\"]}')
"
```

📸 **Verified Output:**
```
=== Model Serving SLO Analysis ===
batch=  1 | p50=  5.5ms | p95=  7.1ms | p99=  7.6ms | throughput=180.6 rps | SLO(p99<100ms): PASS
batch=  8 | p50=  8.9ms | p95= 10.7ms | p99= 11.0ms | throughput=112.6 rps | SLO(p99<100ms): PASS
batch= 32 | p50= 20.9ms | p95= 22.6ms | p99= 22.8ms | throughput= 47.9 rps | SLO(p99<100ms): PASS
batch=128 | p50= 69.0ms | p95= 70.5ms | p99= 71.2ms | throughput= 14.5 rps | SLO(p99<100ms): PASS

=== Deployment Strategies ===
  canary      : traffic=95/5                 risk=low      rollback=< 1min
  blue_green  : traffic=0/100                risk=medium   rollback=< 30sec
  shadow      : traffic=100/0 (mirror)       risk=none     rollback=N/A
  a_b_test    : traffic=50/50                risk=medium   rollback=< 1min
```

**Architecture for 10k RPS Fraud Detection:**

| Component | Design Decision |
|-----------|----------------|
| Load balancer | AWS ALB / GCP HTTPS LB |
| Model server | Triton on GPU nodes (A10G) |
| Batch size | 8 (balanced latency/throughput) |
| Replicas | 10 minimum, autoscale to 50 |
| Deployment | Canary, 5% → 25% → 100% |
| Monitoring | P99 latency alert at 80ms |
| Rollback | Automated if error_rate > 0.1% |

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Serving Patterns | Online (<100ms), Batch (hours), Streaming (<1s) |
| REST vs gRPC | REST for external; gRPC for 5-10x lower latency internal |
| Model Servers | Triton (GPU/multi-framework), vLLM (LLMs), BentoML (Python-first) |
| Batching | Larger batches = higher GPU utilization but higher P99 latency |
| Deployment Strategies | Shadow (safest) → Canary (standard) → Blue-Green (instant) |
| SLO Design | Latency SLO + Model Quality SLO + Error Budget |
| Auto-scaling | GPU pods need 30-60s warm-up; pre-warm minimum replicas |

**Next Lab:** [Lab 03: Vector Database Architecture →](lab-03-vector-database-architecture.md)
