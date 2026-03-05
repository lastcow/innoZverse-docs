# Lab 11: AI Cost Optimization

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

AI infrastructure costs can spiral out of control without intentional FinOps practices. This lab covers the full cost landscape, GPU utilization optimization, spot instances, model distillation, query caching, and building a comprehensive ROI model.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    AI Cost Landscape                         │
├───────────────┬──────────────────┬───────────────────────────┤
│  COMPUTE      │    DATA          │    PEOPLE                 │
│  ───────────  │  ─────────────── │  ─────────────────        │
│  GPU training │  Storage (hot)   │  ML engineers             │
│  GPU inference│  Storage (cold)  │  Data engineers           │
│  CPU serving  │  Data transfer   │  MLOps engineers          │
│  Spot savings │  Feature store   │  AI product managers      │
├───────────────┴──────────────────┴───────────────────────────┤
│  OPTIMIZATION LEVERS                                         │
│  Spot (70% off) | Distillation (60% off) | Cache (30% off)  │
│  Quantization (50% off) | Batching | Right-sizing            │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: AI Cost Components

**Complete Cost Breakdown:**

| Category | Component | Typical % of Total | Optimization Potential |
|----------|-----------|-------------------|----------------------|
| **Compute** | GPU training | 15-30% | Spot instances (70% savings) |
| **Compute** | GPU inference | 10-20% | Quantization, distillation |
| **Data** | Storage (model/data) | 3-8% | Tiered storage, compression |
| **Data** | Transfer costs | 1-3% | CDN, regional serving |
| **API** | External LLM APIs | 5-15% | Caching, model cascade |
| **People** | ML/Data engineers | 30-50% | Platform automation |
| **Tooling** | MLOps tools/licenses | 2-5% | Open-source alternatives |
| **Cloud** | Networking, K8s | 5-10% | Reserved instances |

**People Costs Are Often Underestimated:**
```
Junior ML Engineer: $150K/year (US)
Senior ML Engineer: $250K/year
Staff/Principal: $400K+/year

Team of 4 ML engineers = $800K-$1.6M/year
This often exceeds ALL infrastructure costs combined
→ Automation and platform investment pays for itself quickly
```

---

## Step 2: GPU Utilization Optimization

GPU idling is money on fire. Target > 80% GPU utilization.

**Why GPUs Are Underutilized:**
```
1. Model too small for GPU memory → GPU memory-bound but compute-idle
2. Small batch sizes → GPU waiting for data
3. Data preprocessing bottleneck → GPU starved
4. Training pauses (evaluation, checkpointing)
5. Model parallelism pipeline bubbles
```

**Optimization Techniques:**

| Technique | GPU Utilization Impact | Complexity |
|-----------|----------------------|-----------|
| **Mixed precision (FP16/BF16)** | +20-30% | Low (1 line of code) |
| **Larger batch sizes** | +15-25% | Low |
| **DataLoader prefetching** | +10-20% | Low |
| **Gradient accumulation** | Enables larger effective batch | Low |
| **Flash Attention** | +30-50% (memory + speed) | Medium |
| **Continuous batching** | +40-60% (inference) | Medium (use vLLM) |
| **Multi-GPU tensor parallel** | Near-linear scaling | High |

**Right-sizing GPUs:**
```
For inference:
  Model < 10GB → A10G 24GB (cheapest per token)
  Model 10-40GB → A100 40GB or L40S
  Model 40-80GB → A100 80GB
  Model > 80GB → Multi-GPU (A100/H100)
  
Don't pay for H100 if A10G meets your SLO!
H100 = 5x cost, 3x faster → worse price/performance for most workloads
```

---

## Step 3: Spot and Preemptible Instances

Training workloads are ideal for spot instances — they can checkpoint and resume.

**Spot Instance Economics:**

| Cloud | On-demand (A100 80G) | Spot (A100 80G) | Savings |
|-------|---------------------|----------------|---------|
| AWS p4d | $3.20/hr | $0.96/hr | 70% |
| GCP A100 | $3.47/hr | $1.04/hr | 70% |
| Azure NC A100 | $3.40/hr | $0.85/hr | 75% |

**Spot Instance Best Practices:**
```
1. Checkpoint frequently (every 30 minutes minimum)
2. Use checkpoint resume logic in training code
3. Implement spot interruption handler (2-minute warning)
4. Multi-zone spot pools: if us-east-1 is preempted, try us-west-2
5. Spot for training, on-demand for inference SLO
```

**Spot-Safe Training Architecture:**
```python
# PyTorch Lightning spot-safe training
trainer = Trainer(
    enable_checkpointing=True,
    callbacks=[ModelCheckpoint(every_n_train_steps=100)],
    # Detect spot interruption
    plugins=[SpotInterruptionPlugin()],
)
```

> 💡 For LLM fine-tuning (hours to days), spot instances can save $50K+ per training run. The engineering investment in checkpoint/resume pays back in the first training job.

---

## Step 4: Model Distillation

Train a small "student" model to mimic a large "teacher" model. Often 3-10x smaller with <10% quality loss.

**Distillation Process:**
```
Teacher model (GPT-4, 175B params) → generates soft labels on dataset
Student model (7B params) → trained on: (hard labels + soft labels × temperature)

Loss = α × Cross_entropy(hard_labels, student) 
     + (1-α) × KL_divergence(teacher_logits, student_logits)
```

**Distillation Variants:**

| Variant | Method | Best For |
|---------|--------|---------|
| **Response distillation** | Student mimics teacher outputs | Classification, extraction |
| **Feature distillation** | Student mimics intermediate activations | Complex reasoning |
| **Attention distillation** | Student mimics attention patterns | Sequence tasks |
| **Data augmentation** | Teacher generates training data | Low-data domains |

**Cost Savings Example:**
```
GPT-4 API for 10M queries/month: $30,000/month
Fine-tuned distilled 7B model:
  Training: $2,000 one-time
  Serving: $3,000/month (GPU)
  Total: $3,000/month after payback
  
Savings: $27,000/month, payback: < 1 week
```

---

## Step 5: Query Caching

Cache identical or semantically similar queries. LLM calls are expensive; caching is free.

**Caching Layers:**

| Layer | Type | Hit Rate | Implementation |
|-------|------|---------|---------------|
| Exact match | Redis | 5-15% | Hash query → cache result |
| Semantic match | Vector similarity | 20-40% | Embed query → find similar cached |
| KV cache (LLM) | Prefix reuse | 60-80% | Cache system prompt KV |
| CDN/Edge | HTTP | 10-30% | Cache API responses at edge |

**Semantic Cache Architecture:**
```
Query arrives → embed query
              → search cache (cosine sim > 0.95)
              → Cache HIT: return cached response (< 1ms)
              → Cache MISS: call LLM → store result + embedding
              → Return response
```

**KV Cache Prefix Sharing:**
```
System prompt = 2000 tokens (same for every user)
Without prefix caching: pay for 2000 tokens per request
With prefix caching: pay for 2000 tokens ONCE per hour (cached)
Savings: 80% of input token cost for high-volume same-prompt workloads
```

---

## Step 6: Batching for Cost Optimization

Batching amortizes fixed costs across many requests.

**Batch Processing Economics:**
```
Online serving: 1 request at a time, GPU at 30% utilization
Batch serving: 1000 requests batched, GPU at 90% utilization

Throughput improvement: 3-5x
Cost per prediction: 3-5x lower
Latency: increases (wait for batch to fill or timeout)
```

**Asynchronous Batch Pattern:**
```
User submits prediction request → Job queue
                                      ↓
                               Batch processor
                               (accumulate for 100ms)
                                      ↓
                               Process batch of 32-128
                                      ↓
                               Return results async
                                      ↓
                               User polls or webhook
```

**When to Use Batch vs Online:**
```
Real-time fraud detection → Online (latency critical)
Overnight customer scoring → Batch (cost critical)
Email personalization → Batch (millions of users)
Search ranking → Online (user waits for results)
```

---

## Step 7: FinOps Practices for AI

**FinOps = Cloud Financial Operations applied to AI**

**Show-back / Charge-back Model:**
```
Track GPU hours per team, project, model version
Team A used: 500 GPU-hours on experiment X = $1,500
Report monthly: "Your AI experiments cost $15K this month"
Accountability → teams optimize their own spend
```

**Cost Anomaly Detection:**
```
Baseline: $50K/month
Alert threshold: > $65K or > $45K
Trigger investigation: runaway training job, accidental deployment
Automated kill: training jobs > $10K budget without approval
```

**Reserved Instance Planning:**
```
Committed use (1 year): 30-40% discount vs on-demand
Analyze: GPU baseline (always running) → reserve
         GPU peaks (training bursts) → spot
         Mix: 60% reserved + 40% spot + 10% on-demand
```

---

## Step 8: Capstone — AI Cost Model with ROI

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np

print('=== AI Cost Optimization Model ===')
print()

monthly_costs = {
    'GPU compute (training)': 15000,
    'GPU compute (inference)': 8000,
    'Storage (data + models)': 2000,
    'Data transfer': 500,
    'API costs (external LLMs)': 3000,
    'MLOps tooling': 1500,
    'Data engineering': 8000,
    'ML engineering': 12000,
}
total_monthly = sum(monthly_costs.values())
print('Monthly Cost Breakdown:')
for item, cost in monthly_costs.items():
    pct = cost/total_monthly*100
    print(f'  {item:35s}: \${cost:6,d} ({pct:4.1f}%)')
print(f'  {\"TOTAL\":35s}: \${total_monthly:6,d}')

print()
print('Cost Optimization Strategies:')
optimizations = {
    'Spot instances (training)': {'savings_pct': 0.70, 'applies_to': 'GPU compute (training)'},
    'Model distillation': {'savings_pct': 0.60, 'applies_to': 'GPU compute (inference)'},
    'Query caching (30% hit rate)': {'savings_pct': 0.30, 'applies_to': 'API costs (external LLMs)'},
    'Auto-scaling (off-hours)': {'savings_pct': 0.25, 'applies_to': 'GPU compute (inference)'},
}
total_savings = 0
for opt, info in optimizations.items():
    base = monthly_costs[info['applies_to']]
    savings = base * info['savings_pct']
    total_savings += savings
    print(f'  {opt:35s}: -\${savings:5,.0f}/mo ({info[\"savings_pct\"]*100:.0f}% of {info[\"applies_to\"]})')
print(f'  {\"Total monthly savings\":35s}: -\${total_savings:5,.0f}/mo')
print(f'  Optimized monthly cost: \${total_monthly - total_savings:,.0f}')

print()
business_value_monthly = 80000
print(f'Business Value (monthly): \${business_value_monthly:,}')
print(f'AI Cost (monthly): \${total_monthly - total_savings:,.0f}')
roi = (business_value_monthly - (total_monthly - total_savings)) / (total_monthly - total_savings) * 100
print(f'Monthly ROI: {roi:.1f}%')
print(f'Annual ROI: {roi*12:.0f}% (simplified)')
payback_months = total_monthly / (business_value_monthly - total_monthly + total_savings)
print(f'Payback period: {max(0,payback_months):.1f} months')
"
```

📸 **Verified Output:**
```
=== AI Cost Optimization Model ===

Monthly Cost Breakdown:
  GPU compute (training)             : $15,000 (30.0%)
  GPU compute (inference)            : $ 8,000 (16.0%)
  Storage (data + models)            : $ 2,000 ( 4.0%)
  Data transfer                      : $   500 ( 1.0%)
  API costs (external LLMs)          : $ 3,000 ( 6.0%)
  MLOps tooling                      : $ 1,500 ( 3.0%)
  Data engineering                   : $ 8,000 (16.0%)
  ML engineering                     : $12,000 (24.0%)
  TOTAL                              : $50,000

Cost Optimization Strategies:
  Spot instances (training)          : -$10,500/mo (70% of GPU compute (training))
  Model distillation                 : -$4,800/mo (60% of GPU compute (inference))
  Query caching (30% hit rate)       : -$  900/mo (30% of API costs (external LLMs))
  Auto-scaling (off-hours)           : -$2,000/mo (25% of GPU compute (inference))
  Total monthly savings              : -$18,200/mo
  Optimized monthly cost: $31,800

Business Value (monthly): $80,000
AI Cost (monthly): $31,800
Monthly ROI: 151.6%
Annual ROI: 1819% (simplified)
Payback period: 1.0 months
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Cost Components | Compute (45%), People (40%), Data (8%), Tools (7%) |
| GPU Utilization | Target > 80%; use mixed precision, larger batches, Flash Attention |
| Spot Instances | 70% savings on training; checkpoint every 30 min |
| Model Distillation | 3-10x smaller student model, <10% quality loss, 60% cost reduction |
| Query Caching | Exact (Redis) + Semantic (vector) + KV prefix = 30-80% cost reduction |
| Batching | Amortize GPU costs; 3-5x throughput improvement for async workloads |
| FinOps | Show-back/charge-back, cost anomaly alerts, reserved vs spot planning |

**Next Lab:** [Lab 12: Enterprise AI Platform →](lab-12-enterprise-ai-platform.md)
