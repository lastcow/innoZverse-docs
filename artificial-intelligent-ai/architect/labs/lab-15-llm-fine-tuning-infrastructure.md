# Lab 15: LLM Fine-Tuning Infrastructure

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Fine-tuning LLMs for enterprise use cases requires careful infrastructure decisions. This lab covers fine-tuning approaches (full, LoRA, QLoRA), data preparation, GPU memory planning, alignment techniques (DPO vs RLHF), and evaluation metrics.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              LLM Fine-Tuning Infrastructure                  │
├──────────────────────────────────────────────────────────────┤
│  DATA PIPELINE          │  TRAINING INFRASTRUCTURE           │
│  Raw data → JSONL       │  Base Model (HuggingFace)         │
│  Instruction format     │  PEFT/LoRA adapter init           │
│  Train/val split        │  Mixed precision (BF16)           │
│  Quality filtering      │  Gradient checkpointing           │
│                         │  DeepSpeed ZeRO / FSDP            │
├──────────────────────────┴──────────────────────────────────┤
│  EVALUATION             │  DEPLOYMENT                        │
│  BLEU, ROUGE, BERTScore │  Merge LoRA → Base model          │
│  Human evaluation       │  Quantize to INT4/INT8            │
│  Benchmark suites       │  Serve with vLLM                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Fine-Tuning Approaches

**When to Fine-Tune vs Prompt Engineering:**
```
Prompt engineering (try first):
  - No GPU required
  - Fast iteration
  - Works for well-scoped tasks
  - Base model has sufficient capability

Fine-tuning needed when:
  - Specific domain vocabulary/format required
  - Consistent style/persona
  - Lower latency (fewer prompt tokens)
  - Higher accuracy on narrow task
  - Cannot share sensitive examples in prompts
```

**Fine-Tuning Methods Comparison:**

| Method | Trainable Params | GPU Memory (7B) | Quality | Use Case |
|--------|----------------|----------------|---------|---------|
| **Full fine-tuning** | 100% | ~112 GB | Best | Max quality, ample GPU |
| **LoRA** | 0.1-1% | ~18 GB | Excellent | Most enterprise use cases |
| **QLoRA** | 0.1-1% | ~8 GB | Very good | Single consumer GPU |
| **Prefix tuning** | <0.1% | ~14 GB | Good | Task-specific, less storage |
| **Prompt tuning** | <0.01% | ~14 GB | Moderate | Many tasks, limited storage |

---

## Step 2: LoRA Architecture

**LoRA (Low-Rank Adaptation):**
```
Original: W ∈ R^(d×d) (frozen)
LoRA adapter: W' = W + BA
  where B ∈ R^(d×r), A ∈ R^(r×d), r << d

Initialization: B = 0, A ~ Normal(0,σ²)
Forward: h = Wx + BAx × (α/r)  (α is scaling factor)

Parameters: d×r + r×d = 2×d×r (much less than d²)
```

**Why LoRA Works:**
```
Pre-trained models have low intrinsic rank for adaptation
"Intrinsic rank" = most of the weight changes live in a low-dim subspace
rank=8 captures 90%+ of fine-tuning benefit vs full fine-tuning
```

**LoRA Target Modules:**
```
LLaMA: q_proj, v_proj (minimum), or all: q_proj, k_proj, v_proj, o_proj
       + gate_proj, down_proj, up_proj (for better performance)

Trade-off: more modules → more trainable params → better quality, more memory
```

---

## Step 3: QLoRA

QLoRA = Quantized LoRA. Fine-tune on 4-bit quantized base model.

**QLoRA Innovations:**
1. **4-bit NormalFloat (NF4)**: Optimal quantization for normally-distributed weights
2. **Double quantization**: Quantize the quantization constants (saves ~0.37 GB for 65B)
3. **Paged optimizers**: NVIDIA unified memory for gradient optimizer states

**QLoRA Memory Breakdown (LLaMA-7B):**
```
Base model (4-bit NF4):  ~3.5 GB
LoRA adapters (fp16):    ~0.5 GB
Activations:             ~2.0 GB
Optimizer states:        ~2.0 GB
Total:                   ~8 GB → fits on RTX 3090/4090!
```

**QLoRA vs LoRA:**
```
LoRA:  base model in FP16 (14GB) + adapters → 18GB GPU needed
QLoRA: base model in INT4 (~3.5GB) + adapters → 8GB GPU needed
Quality: QLoRA slightly worse than LoRA (< 1% on most benchmarks)
```

---

## Step 4: Data Preparation

**Instruction Following Format (Alpaca/ChatML):**

**Alpaca format:**
```json
{
  "instruction": "Classify this email as spam or legitimate",
  "input": "Dear customer, you have won $1,000,000...",
  "output": "spam"
}
```

**ChatML format (Llama-3, Mistral):**
```
<|system|>
You are a helpful financial analyst assistant.
</s>
<|user|>
What is the P/E ratio of Apple?
</s>
<|assistant|>
As of Q4 2024, Apple's P/E ratio is approximately 29.5...
</s>
```

**Data Quality for Fine-Tuning:**
```
Quantity: 1,000-10,000 high-quality examples > 100,000 mediocre examples
Format: Consistent instruction format throughout dataset
Length: Cover variety of lengths (short and long responses)
Diversity: Avoid repetitive examples (dilutes gradient signal)
Quality filter: Remove examples with: hallucinations, toxic content, wrong format
Deduplication: Near-duplicate removal (SimHash or embedding similarity)
```

---

## Step 5: Alignment Techniques (RLHF vs DPO)

**RLHF (Reinforcement Learning from Human Feedback):**
```
Stage 1: Supervised fine-tuning (SFT)
          Base model → fine-tune on curated demonstrations

Stage 2: Reward model training
          Human annotators: prefer response A or B?
          Train reward model to predict human preferences

Stage 3: RL optimization (PPO)
          Policy (LLM) → generates response
          Reward model → scores response
          PPO → update LLM to maximize reward
          KL penalty → prevent model from diverging too far from SFT

Complexity: Need reward model + PPO training infrastructure
```

**DPO (Direct Preference Optimization):**
```
Simpler alternative: directly optimize on preference pairs (no reward model needed)

Dataset: (prompt, chosen_response, rejected_response)
Loss: maximize log σ(β × (log_ratio(chosen) - log_ratio(rejected)))

Advantages:
  - No separate reward model needed
  - Simpler to implement and train
  - Similar or better results than RLHF in many benchmarks

Libraries: trl (HuggingFace), Axolotl
```

**DPO Data Format:**
```json
{
  "prompt": "Explain gradient descent",
  "chosen": "Gradient descent is an optimization algorithm that...",
  "rejected": "It's like going downhill. You just follow the slope!"
}
```

---

## Step 6: Compute Requirements

**GPU Memory Calculator:**

```
Model memory (FP16): params_B × 2 bytes
LoRA params (FP16):  lora_params × 2 bytes  
Gradients:          = model_memory (for LoRA adapters only)
Optimizer states:   = gradients × 2 (Adam: m + v)
Activations:        batch_size × seq_len × hidden × layers × 2 bytes

For QLoRA (4-bit base + FP16 LoRA):
  7B QLoRA:  3.5 + 0.3 + 0.6 + 1.2 + 2 = ~8GB
  13B QLoRA: 7 + 0.5 + 1 + 2 + 3 = ~14GB
  70B QLoRA: 35 + 2 + 4 + 8 + 8 = ~57GB (need 4x A100 or 2x H100)
```

**Compute Budget Estimation:**
```
Fine-tuning speed (A100 80GB, FP16):
  7B model: ~2,000 tokens/sec
  13B model: ~1,200 tokens/sec
  70B model: ~300 tokens/sec

For 1M token dataset (100K examples × 10 tokens average):
  7B: 500 seconds ≈ 8 minutes per epoch
  13B: 833 seconds ≈ 14 minutes per epoch
  70B: 3,333 seconds ≈ 55 minutes per epoch

Budget 3-5 epochs for most fine-tuning tasks
```

---

## Step 7: Evaluation (BLEU, ROUGE, BERTScore)

**Automated Metrics:**

| Metric | Measures | Range | Use Case |
|--------|---------|-------|---------|
| **BLEU** | N-gram precision vs reference | 0-100 | Translation, generation |
| **ROUGE-L** | Longest common subsequence | 0-1 | Summarization |
| **BERTScore** | Semantic similarity (BERT embeddings) | 0-1 | Open-ended generation |
| **Perplexity** | Model confidence on holdout set | Lower=better | Language modeling quality |

**Human Evaluation (Gold Standard):**
```
Dimensions (Likert 1-5):
  Helpfulness: Does response answer the question?
  Accuracy: Is information correct?
  Harmlessness: No harmful content?
  Coherence: Is response well-structured?
  Conciseness: Appropriately brief?

Scale: 100-500 human annotations minimum for significance
```

**LLM-as-Judge (Scalable Human-Quality Eval):**
```
Use GPT-4 or Claude to evaluate fine-tuned model outputs
Prompt: "Rate this response 1-10 for helpfulness, accuracy, safety"
Correlation with human judges: ~0.85 (reasonably reliable)
Cost: ~100x cheaper than human evaluation
```

---

## Step 8: Capstone — LoRA Parameter Calculator

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
def lora_params(model_params_M, rank=8, target_modules=None):
    if target_modules is None:
        target_modules = {'q_proj': (4096, 4096), 'v_proj': (4096, 4096), 'k_proj': (4096, 4096), 'o_proj': (4096, 4096)}
    
    lora_params = 0
    for name, (in_dim, out_dim) in target_modules.items():
        lora_params += in_dim * rank + rank * out_dim
    
    n_layers = {'7B': 32, '13B': 40, '70B': 80}
    model_size = f'{round(model_params_M/1000)}B'
    layers = n_layers.get(model_size, 32)
    total_lora = lora_params * layers
    
    return {
        'base_params': model_params_M * 1e6,
        'lora_params': total_lora,
        'trainable_pct': total_lora / (model_params_M * 1e6) * 100,
        'lora_size_MB': total_lora * 2 / 1e6,
    }

print('=== LoRA Parameter Efficiency Calculator ===')
print()
models = [
    ('LLaMA-7B', 7000, 8),
    ('LLaMA-13B', 13000, 8),
    ('LLaMA-70B', 70000, 16),
]
for name, params_M, rank in models:
    r = lora_params(params_M, rank=rank)
    print(f'{name} (rank={rank}):')
    print(f'  Base params:     {r[\"base_params\"]/1e9:.1f}B')
    print(f'  LoRA params:     {r[\"lora_params\"]/1e6:.2f}M')
    print(f'  Trainable:       {r[\"trainable_pct\"]:.2f}%')
    print(f'  LoRA adapter:    {r[\"lora_size_MB\"]:.1f} MB')
    print()

print('GPU Memory Requirements for Fine-tuning:')
methods = {
    'Full fine-tune (FP16)': {'LLaMA-7B': 112, 'LLaMA-13B': 210, 'LLaMA-70B': 1120},
    'LoRA (rank=8)':         {'LLaMA-7B': 18,  'LLaMA-13B': 30,  'LLaMA-70B': 80},
    'QLoRA (4-bit)':         {'LLaMA-7B': 8,   'LLaMA-13B': 12,  'LLaMA-70B': 40},
}
print(f'  {\"Method\":35s} | LLaMA-7B | LLaMA-13B | LLaMA-70B')
print(f'  {\"-\"*70}')
for method, sizes in methods.items():
    print(f'  {method:35s} | {sizes[\"LLaMA-7B\"]:6}GB | {sizes[\"LLaMA-13B\"]:7}GB | {sizes[\"LLaMA-70B\"]:7}GB')
"
```

📸 **Verified Output:**
```
=== LoRA Parameter Efficiency Calculator ===

LLaMA-7B (rank=8):
  Base params:     7.0B
  LoRA params:     8.39M
  Trainable:       0.12%
  LoRA adapter:    16.8 MB

LLaMA-13B (rank=8):
  Base params:     13.0B
  LoRA params:     10.49M
  Trainable:       0.08%
  LoRA adapter:    21.0 MB

LLaMA-70B (rank=16):
  Base params:     70.0B
  LoRA params:     41.94M
  Trainable:       0.06%
  LoRA adapter:    83.9 MB

GPU Memory Requirements for Fine-tuning:
  Method                              | LLaMA-7B | LLaMA-13B | LLaMA-70B
  ----------------------------------------------------------------------
  Full fine-tune (FP16)               |    112GB |     210GB |    1120GB
  LoRA (rank=8)                       |     18GB |      30GB |      80GB
  QLoRA (4-bit)                       |      8GB |      12GB |      40GB
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Full Fine-tuning | Best quality; needs 112GB+ for 7B; use for mission-critical |
| LoRA | Train 0.1% params; W' = W + BA; 18GB for 7B; standard approach |
| QLoRA | 4-bit base + FP16 LoRA adapters; 8GB for 7B; single consumer GPU |
| Data Format | Instruction format (Alpaca/ChatML); 1K-10K quality > 100K quantity |
| RLHF | SFT → Reward Model → PPO; complex but powerful |
| DPO | Preference pairs only; no reward model; simpler, comparable quality |
| Evaluation | BLEU/ROUGE (automated) + BERTScore (semantic) + LLM-judge (scalable) |

**Next Lab:** [Lab 16: Knowledge Graph + LLM →](lab-16-knowledge-graph-llm.md)
