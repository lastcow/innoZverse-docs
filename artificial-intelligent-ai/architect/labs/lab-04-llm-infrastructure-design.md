# Lab 04: LLM Infrastructure Design

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Deploying Large Language Models at scale requires specialized infrastructure decisions. This lab covers inference hardware selection, quantization strategies, serving frameworks, KV cache architecture, model parallelism, and cost optimization.

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                   LLM Serving Infrastructure                   │
├────────────────────────────────────────────────────────────────┤
│  Client → API Gateway → Load Balancer                         │
│                              ↓                                 │
│  vLLM / TGI / llama.cpp serving engine                        │
│  ├── Continuous Batching (PagedAttention)                      │
│  ├── KV Cache (GPU HBM → CPU → Disk tiering)                  │
│  └── Multi-GPU: Tensor Parallel / Pipeline Parallel           │
├────────────────────────────────────────────────────────────────┤
│  Hardware: H100 80GB / A100 80GB / A10G 24GB                  │
│  Quantization: FP32 → FP16 → INT8 → INT4                     │
└────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Inference Hardware Selection

**GPU Comparison for LLM Inference:**

| GPU | Memory | Bandwidth | FP16 TFLOPS | Price/hr (cloud) | Best For |
|-----|--------|----------|------------|-----------------|---------|
| **H100 SXM5** | 80GB HBM3 | 3.35 TB/s | 989 TFLOPS | $5-8 | Largest models, max throughput |
| **A100 SXM4** | 80GB HBM2e | 2.0 TB/s | 312 TFLOPS | $3-4 | Standard production LLMs |
| **A10G** | 24GB GDDR6 | 600 GB/s | 125 TFLOPS | $1.0-1.5 | 7B-13B models, cost-optimized |
| **L40S** | 48GB GDDR6 | 864 GB/s | 362 TFLOPS | $2-3 | Mid-size models, inference |
| **CPU (96-core)** | 768GB RAM | 300 GB/s | N/A | $3-5 | Low-QPS, latency-tolerant |

**Hardware Selection Decision Tree:**
```
Model size?
├── 7B-13B  → A10G 24GB (INT8) or A100 40GB (FP16)
├── 30-70B  → A100 80GB (INT4/INT8) or 2x A10G tensor parallel
├── 70-180B → 4x A100 80GB tensor parallel
└── 405B+   → 8x H100 (tensor + pipeline parallel)
```

> 💡 Memory bandwidth is more important than TFLOPS for LLM inference. LLMs are memory-bandwidth-bound, not compute-bound at small batch sizes.

---

## Step 2: Quantization Strategies

Quantization reduces model precision to lower memory and increase speed.

**Precision Levels:**

| Precision | Bits | LLaMA-70B Size | Speed Gain | Quality Loss |
|-----------|------|---------------|-----------|-------------|
| **FP32** | 32 | 280 GB | 1x (baseline) | None |
| **FP16/BF16** | 16 | 140 GB | 2x | Negligible |
| **INT8** | 8 | 70 GB | 3-4x | ~1% accuracy |
| **INT4** | 4 | 35 GB | 5-8x | 1-3% accuracy |
| **GPTQ** | 4 | 35 GB | 5-8x | Best INT4 quality |
| **AWQ** | 4 | 35 GB | 6-10x | Slightly better than GPTQ |

**Quantization Impact:**
```
LLaMA-70B FP32: 280 GB (need 4x A100 80GB)
LLaMA-70B FP16: 140 GB (need 2x A100 80GB)
LLaMA-70B INT8: 70 GB  (fits on 1x A100 80GB)
LLaMA-70B INT4: 35 GB  (fits on 1x A100 40GB or 2x A10G)
```

**Quantization Tooling:**
- **bitsandbytes**: Easy INT8/INT4, Hugging Face integration
- **GPTQ**: Post-training quantization, high quality
- **AWQ**: Activation-aware, best quality/speed
- **llama.cpp**: CPU quantization (Q4_K_M, Q5_K_M, Q8_0)

---

## Step 3: Serving Frameworks (vLLM, llama.cpp)

**vLLM (Production LLM Serving):**

Key Innovation: **PagedAttention** — manages KV cache like OS virtual memory
```
Traditional:   Reserve max_seq_len memory upfront (wastes 60-80%)
PagedAttention: Allocate KV cache in pages, reclaim on sequence end
                → 3-10x higher throughput, supports larger batches
```

**vLLM Architecture:**
```
Incoming requests → Scheduler → PagedAttention KV Manager
                                     ↓
                               Continuous batching
                               (add new requests mid-batch)
                                     ↓
                               GPU inference → Token streaming
```

**llama.cpp (CPU/Edge):**
- Pure C++, runs on CPU (Apple Silicon, x86)
- Quantized models (GGUF format: Q4_K_M ≈ 4GB for 7B)
- 10-30 tokens/sec on modern CPU (vs 100+ on GPU)
- Use for: local dev, edge deployment, cost-sensitive low-QPS

**Framework Comparison:**

| Framework | Hardware | Throughput | Latency | Use Case |
|-----------|----------|-----------|---------|---------|
| vLLM | GPU | Highest | Low | Production, high QPS |
| TGI (HuggingFace) | GPU | High | Low | Production, HF ecosystem |
| llama.cpp | CPU/GPU | Low | Medium | Local, edge, dev |
| Ollama | CPU/GPU | Low | Medium | Developer experience |

---

## Step 4: Batching (Dynamic and Continuous)

**Static vs Dynamic vs Continuous Batching:**

```
Static: Wait for full batch_size=32 → process together → respond all
  Latency: ~32 requests × wait_time = high latency for first requests
  
Dynamic: Wait max_wait_ms=20 → process whatever arrived → respond
  Better latency, variable throughput

Continuous (vLLM): Iteration-level scheduling
  New request can join IN-PROGRESS batch at any token step
  → Maximum GPU utilization, best throughput, fair queuing
```

**Why Continuous Batching is Critical for LLMs:**
```
Without: GPU waits for slowest sequence to finish before starting new request
With:    Finished sequences immediately replaced by new requests
         GPU utilization: 40% → 90%+
```

---

## Step 5: KV Cache Architecture

The KV (Key-Value) cache is the most critical memory component in LLM inference.

**What is KV Cache?**
```
For each token: Transformer computes Q, K, V matrices
                K and V from previous tokens can be CACHED
                (no need to recompute for autoregressive generation)

KV Cache size = 2 × n_layers × n_heads × head_dim × seq_len × batch_size × 2 bytes (fp16)
```

**KV Cache for LLaMA-7B:**
```
= 2 × 32 layers × 32 heads × 128 dim × 4096 seq × 32 batch × 2 bytes
= ~2.1 GB per batch of 32 at 4096 context
```

**KV Cache Tiering:**
```
Hot  (< 1s old):  GPU HBM (fastest)
Warm (< 1min):    CPU RAM (swap out when GPU full)
Cold (> 1min):    NVMe SSD (rare access)
```

**Context Length Cost:**
- Context 2K → 4K: 4x KV cache memory
- Context 4K → 128K: 32x KV cache memory
- Long context models (Claude, Gemini) require careful KV memory management

---

## Step 6: Model Sharding (Tensor and Pipeline Parallelism)

When a model doesn't fit on one GPU, you must split it.

**Tensor Parallelism (within a layer):**
```
GPU 0: handles attention_heads [0-15]
GPU 1: handles attention_heads [16-31]
Communication: AllReduce after each layer
Latency overhead: low (NVLink: 600 GB/s)
```

**Pipeline Parallelism (across layers):**
```
GPU 0: layers 1-8   (receives input, sends activations)
GPU 1: layers 9-16  (receives activations, sends to next)
GPU 2: layers 17-24
GPU 3: layers 25-32 (final output)
Challenge: "pipeline bubble" — GPUs idle during warm-up
Solution: micro-batching to fill the pipeline
```

**ZeRO (Zero Redundancy Optimizer) for Training:**
```
Stage 1: Shard optimizer states across GPUs (4x memory savings)
Stage 2: + shard gradients (8x savings)
Stage 3: + shard parameters (64x savings) — enables trillion-param models
```

---

## Step 7: Cost Per Token Optimization

**Cost Calculator Framework:**

| Model | Precision | GPU | GPUs | $/hr | Tokens/sec | $/1M tokens |
|-------|----------|-----|------|------|-----------|------------|
| LLaMA-7B | INT8 | A10G | 1 | $1.20 | ~1000 | $0.33 |
| LLaMA-13B | FP16 | A100 | 1 | $3.00 | ~600 | $0.83 |
| LLaMA-70B | INT4 | A100 | 1 | $3.00 | ~600 | $0.83 |
| GPT-175B | INT8 | H100 | 3 | $15.00 | ~400 | $12.50 |

**Cost Optimization Strategies:**
1. **Quantize**: INT4 vs FP16 = 4x cost reduction, minimal quality loss
2. **Cascade models**: Use 7B for simple queries, 70B only for complex
3. **Prompt caching**: Cache KV for repeated system prompts (80% cost savings on prefix)
4. **Speculative decoding**: Draft small model + verify with large = 2-3x faster
5. **Batch offline workloads**: Spot/preemptible instances = 70% cost reduction

---

## Step 8: Capstone — LLM Infrastructure Cost Calculator

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
def calculate_llm_cost(model_params_B, hardware, precision, batch_size, seq_len):
    bytes_per_param = {'fp32': 4, 'fp16': 2, 'int8': 1, 'int4': 0.5}
    bpp = bytes_per_param[precision]
    model_memory_GB = model_params_B * 1e9 * bpp / 1e9
    kv_cache_GB = 2 * batch_size * seq_len * 128 * 32 * bpp / 1e9
    total_memory_GB = model_memory_GB + kv_cache_GB
    
    gpu_memory = {'A100_80G': 80, 'H100_80G': 80, 'A10G_24G': 24}
    gpus_needed = max(1, int(total_memory_GB / gpu_memory.get(hardware, 80)) + 1)
    
    gpu_cost_hr = {'A100_80G': 3.0, 'H100_80G': 5.0, 'A10G_24G': 1.2}
    tokens_per_sec = 1000 / gpus_needed
    cost_per_1M_tokens = (gpu_cost_hr.get(hardware, 3.0) * gpus_needed / 3600) / tokens_per_sec * 1e6
    
    return {
        'model_memory_GB': round(model_memory_GB, 1),
        'kv_cache_GB': round(kv_cache_GB, 2),
        'total_memory_GB': round(total_memory_GB, 1),
        'gpus_needed': gpus_needed,
        'cost_per_1M_tokens': round(cost_per_1M_tokens, 4)
    }

print('=== LLM Infrastructure Cost Calculator ===')
configs = [
    ('LLaMA-7B', 7, 'A10G_24G', 'int8', 32, 2048),
    ('LLaMA-13B', 13, 'A100_80G', 'fp16', 32, 4096),
    ('LLaMA-70B', 70, 'A100_80G', 'int4', 16, 4096),
    ('GPT-175B', 175, 'H100_80G', 'int8', 8, 8192),
]
for name, params, hw, prec, bs, seq in configs:
    r = calculate_llm_cost(params, hw, prec, bs, seq)
    print(f'{name:12s} | {prec:4s} | {hw:10s} | model={r[\"model_memory_GB\"]:6.1f}GB | KV={r[\"kv_cache_GB\"]:5.2f}GB | GPUs={r[\"gpus_needed\"]} | cost=\${r[\"cost_per_1M_tokens\"]:.4f}/1M tokens')

print()
print('Quantization impact on model size:')
for prec, bpp in [('FP32', 4), ('FP16', 2), ('INT8', 1), ('INT4', 0.5)]:
    size = 70 * bpp
    print(f'  LLaMA-70B {prec}: {size:.0f} GB')
"
```

📸 **Verified Output:**
```
=== LLM Infrastructure Cost Calculator ===
LLaMA-7B     | int8 | A10G_24G   | model=   7.0GB | KV= 0.54GB | GPUs=1 | cost=$0.3333/1M tokens
LLaMA-13B    | fp16 | A100_80G   | model=  26.0GB | KV= 2.15GB | GPUs=1 | cost=$0.8333/1M tokens
LLaMA-70B    | int4 | A100_80G   | model=  35.0GB | KV= 0.27GB | GPUs=1 | cost=$0.8333/1M tokens
GPT-175B     | int8 | H100_80G   | model= 175.0GB | KV= 0.54GB | GPUs=3 | cost=$12.5000/1M tokens

Quantization impact on model size:
  LLaMA-70B FP32: 280 GB
  LLaMA-70B FP16: 140 GB
  LLaMA-70B INT8: 70 GB
  LLaMA-70B INT4: 35 GB
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Hardware | H100 > A100 > A10G; bandwidth > TFLOPS for inference |
| Quantization | FP16 (standard), INT8 (~1% loss), INT4 (~3% loss, 4x savings) |
| vLLM | PagedAttention = virtual memory for KV cache, 3-10x throughput |
| Continuous Batching | New requests join mid-batch, maximizes GPU utilization |
| KV Cache | 2 × layers × heads × dim × seq × batch × 2 bytes |
| Tensor Parallelism | Split heads across GPUs (within layer, NVLink required) |
| Pipeline Parallelism | Split layers across GPUs (micro-batch to fill pipeline) |
| Cost Optimization | Quantize → cascade → cache prompts → speculative decoding |

**Next Lab:** [Lab 05: RAG at Scale →](lab-05-rag-at-scale.md)
