# Lab 06: The Transformer Revolution — Attention is All You Need

## Objective

Understand the architecture that powers every major AI system today. By the end you will be able to explain:

- Why RNNs failed at long-range dependencies
- What self-attention computes and why it's powerful
- The full Transformer encoder/decoder architecture
- How scaling Transformers produced the LLM revolution

---

## The Problem with RNNs

Before Transformers, sequences (text, audio, time series) were processed with **Recurrent Neural Networks** — reading one token at a time, updating a hidden state:

```
"The cat sat on the mat"
   ↓    ↓    ↓   ↓   ↓    ↓
  h₁ → h₂ → h₃→ h₄→ h₅ → h₆ → output
```

**Three fatal problems:**

1. **Sequential** — you can't process token 5 until you've processed tokens 1–4. No parallelism → slow training.

2. **Vanishing gradients** — in long sequences, the gradient signal fades as it propagates backwards through hundreds of time steps. The model forgets early tokens.

3. **Fixed-size bottleneck** — in encoder-decoder RNNs (for translation), the entire source sentence must be compressed into one fixed-size vector. Information loss is inevitable.

---

## The Attention Mechanism (2014)

Bahdanau et al. (2014) added **attention** to RNNs: instead of compressing everything into one vector, let the decoder look back at ALL encoder hidden states — weighted by relevance.

```
Translating: "Je voudrais un café"

When generating "coffee":
  attention to "café"        → 0.91  (very relevant)
  attention to "voudrais"    → 0.06
  attention to "Je"          → 0.02
  attention to "un"          → 0.01
```

This was the idea that unlocked everything. The 2017 paper took it further: **what if attention is the only mechanism you need?**

---

## Attention is All You Need (2017)

Google Brain researchers Vaswani, Shazeer, Parmar et al. proposed the **Transformer**: discard the RNN entirely. Use only attention. Process all tokens simultaneously.

The paper's title was deliberately provocative. It was correct.

### The Query-Key-Value Framework

Self-attention is computed via three learned matrices: **Q** (queries), **K** (keys), **V** (values). Think of it as a soft database lookup:

```
For each token:
  Query = "what information do I need?"
  Keys  = "what information does each token offer?"
  Values = "what information does each token contain?"

Attention score = softmax(Q · Kᵀ / √d_k)
Output = attention_score × V
```

```python
import torch
import torch.nn.functional as F
import math

def self_attention(Q, K, V):
    """
    Q, K, V: (batch_size, seq_len, d_k)
    Returns: attended values (batch_size, seq_len, d_v)
    """
    d_k = Q.size(-1)

    # Dot product attention scores
    scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)
    # scores shape: (batch, seq_len, seq_len)
    # scores[i][j] = how much token i attends to token j

    # Convert to probabilities
    attention_weights = F.softmax(scores, dim=-1)

    # Weighted sum of values
    output = torch.matmul(attention_weights, V)

    return output, attention_weights
```

**Concrete example with 4 tokens:**

```
Sentence: "it was the animal that was tired"
                                       ↑ what does "it" refer to?

Self-attention lets "it" look at all other tokens simultaneously:
  it → animal: 0.78  ← highest attention (resolves coreference!)
  it → tired:  0.12
  it → was:    0.06
  it → the:    0.04
```

This is why Transformers handle long-range dependencies so well — every token can attend to every other token in a single operation.

---

## Multi-Head Attention

Rather than one attention computation, run **h parallel attention heads**, each learning to attend to different aspects:

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model=512, num_heads=8):
        super().__init__()
        self.d_k = d_model // num_heads
        self.heads = num_heads

        # Each head has its own Q, K, V projections
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, x):
        B, T, C = x.shape

        Q = self.W_q(x).view(B, T, self.heads, self.d_k).transpose(1,2)
        K = self.W_k(x).view(B, T, self.heads, self.d_k).transpose(1,2)
        V = self.W_v(x).view(B, T, self.heads, self.d_k).transpose(1,2)

        # Attention in parallel for all heads
        scores = (Q @ K.transpose(-2,-1)) / math.sqrt(self.d_k)
        weights = F.softmax(scores, dim=-1)
        attended = weights @ V

        # Concatenate all heads and project
        out = attended.transpose(1,2).contiguous().view(B, T, C)
        return self.W_o(out)
```

Each head learns different relationships:
- Head 1: syntactic dependencies (subject-verb agreement)
- Head 2: coreference (pronouns to their referents)
- Head 3: positional proximity
- Head 4–8: semantic relationships, etc.

---

## Positional Encoding

Self-attention has no notion of order — "cat sat mat" and "mat sat cat" would produce the same attention scores. **Positional encoding** adds position information:

```python
import torch
import math

def positional_encoding(seq_len, d_model):
    """Sinusoidal positional encoding (original paper)"""
    PE = torch.zeros(seq_len, d_model)
    pos = torch.arange(0, seq_len).unsqueeze(1).float()
    div = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

    PE[:, 0::2] = torch.sin(pos * div)  # even dimensions
    PE[:, 1::2] = torch.cos(pos * div)  # odd dimensions
    return PE

# Modern LLMs use RoPE (Rotary Position Embedding) instead
# which allows better extrapolation to longer sequences
```

---

## The Full Transformer Architecture

```
                    ┌─────────────────────────┐
                    │      OUTPUT TOKENS       │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │  Linear + Softmax        │  ← vocabulary prediction
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐  ×N
                    │   Decoder Block          │
                    │  • Masked Self-Attention  │  ← can't see future tokens
                    │  • Cross-Attention        │  ← attend to encoder output
                    │  • Feed-Forward Network   │
                    │  • Layer Norm + Residual  │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐  ×N
                    │   Encoder Block          │
                    │  • Self-Attention         │
                    │  • Feed-Forward Network   │
                    │  • Layer Norm + Residual  │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │  Input Embeddings         │
                    │  + Positional Encoding    │
                    └─────────────────────────┘
```

**Two variants:**
- **Encoder-only** (BERT): good at understanding. Used for classification, NER, embeddings.
- **Decoder-only** (GPT, Llama, Claude): good at generation. Predicts the next token, autoregressively.
- **Encoder-Decoder** (T5, BART): translation, summarisation.

---

## Why Scaling Works: The Scaling Laws

Kaplan et al. (OpenAI, 2020) showed that Transformer performance follows **predictable power laws**:

```
Loss ∝ (1/N)^α    where N = number of parameters
Loss ∝ (1/D)^β    where D = dataset size
Loss ∝ (1/C)^γ    where C = compute budget
```

**The implication:** If you have 10× more compute, you can predict exactly how much better your model will be. And the relationship is smooth — no diminishing returns observed up to current scales.

Chinchilla (DeepMind, 2022) refined this: for a given compute budget, models had been overtrained on too few tokens. Optimal training: scale parameters and data **equally**.

---

## From Transformer to LLMs: The Key Innovations

| Innovation | What It Did |
|-----------|-------------|
| Transformer (2017) | Base architecture; replaced RNNs |
| GPT (2018) | Decoder-only; next-token prediction at scale |
| BERT (2018) | Encoder-only; masked language modelling |
| Scaling Laws (2020) | Showed predictable improvement with scale |
| RLHF (2022) | Aligned LLMs to human preferences via feedback |
| Flash Attention (2022) | 2–4× faster, 10× more memory-efficient attention |
| RoPE / ALiBi (2022) | Positional encoding that extrapolates to longer context |
| Mixture of Experts (2024) | Route tokens to specialised sub-networks → more efficient |

---

## Summary

The Transformer succeeded because:
1. **Parallel computation** — every token processed simultaneously (vs. RNN's sequential)
2. **Global context** — every token attends to every other token (no bottleneck)
3. **Scalability** — more parameters + more data = better, predictably
4. **Transfer learning** — pre-train once on internet text; fine-tune on any task

Everything after 2017 — BERT, GPT, Claude, Gemini, Llama, Stable Diffusion — is built on Transformers.

---

## Further Reading

- [Attention Is All You Need (original paper)](https://arxiv.org/abs/1706.03762)
- [The Illustrated Transformer — Jay Alammar](https://jalammar.github.io/illustrated-transformer/)
- [Andrej Karpathy: Let's build GPT from scratch (YouTube)](https://www.youtube.com/watch?v=kCc8FmEb1nY)
- [Chinchilla Scaling Laws (DeepMind)](https://arxiv.org/abs/2203.15556)
