# Lab 07: Large Language Models Explained — GPT, Claude, Gemini, Llama

## Objective

Understand how modern LLMs are built, trained, and differentiated. By the end you will be able to:

- Explain the three stages of LLM training (pre-training, SFT, RLHF)
- Compare the major LLM families and their key design choices
- Describe what makes each model distinctive
- Understand context windows, tokenisation, and inference

---

## What is a Large Language Model?

A **Large Language Model** is a Transformer-based neural network trained to predict the next token in a sequence, at massive scale.

```
Input:  "The capital of France is"
LLM:    [token probabilities for every word in vocabulary]
         Paris: 0.94
         Lyon:  0.02
         Rome:  0.01
         ...
Output: "Paris"
```

That's it. Next-token prediction, trained on trillions of tokens of text. The emergent result: a system that can write code, reason about logic, translate languages, summarise documents, and pass professional exams.

---

## Stage 1: Pre-Training

**What happens:** The model trains on a massive dataset of internet text, books, code, and scientific papers — learning to predict the next token.

**Scale:**
- GPT-3: 175B parameters, ~300B tokens
- Llama 3 (70B): ~15 trillion tokens
- GPT-4: estimated ~1 trillion tokens, ~1.8 trillion parameters (MoE)

**Cost:** Estimated $4M–$100M per major model in compute alone.

**Result:** A **base model** that can complete any text — but is not yet useful as an assistant. It might complete "How do I make a bomb?" with "Here are the steps..." because the training data contains such text.

```python
# Conceptual pre-training loop
for batch in internet_text_corpus:  # 15 trillion tokens
    tokens = tokenise(batch)        # split text into integer IDs

    # Input: all tokens except last. Target: all tokens except first (shifted by 1)
    input_ids  = tokens[:-1]
    target_ids = tokens[1:]

    logits = model(input_ids)                         # forward pass
    loss   = cross_entropy(logits, target_ids)        # how wrong?
    loss.backward()                                   # compute gradients
    optimiser.step()                                  # update 70B parameters
    # Repeat ~10M times
```

---

## Stage 2: Supervised Fine-Tuning (SFT)

Take the pre-trained base model and fine-tune on **high-quality (prompt, response) pairs** written by humans:

```
Prompt:   "Explain quantum entanglement to a 10-year-old"
Response: "Imagine you and your friend each have a magic coin..."

Prompt:   "Write a Python function to sort a list"
Response: "def sort_list(lst):\n    return sorted(lst)\n..."
```

This teaches the model to follow instructions and respond helpfully. But it doesn't teach it to be safe or aligned — that requires stage 3.

---

## Stage 3: RLHF — Reinforcement Learning from Human Feedback

**The alignment stage.** Humans rate model outputs; those ratings train a **reward model**; the LLM is then optimised to maximise that reward using PPO (Proximal Policy Optimisation).

```
Step 1: Sample many responses to the same prompt
        "Tell me about sharks"
        Response A: "Sharks are fascinating marine predators..."
        Response B: "Sharks will kill you. They're terrifying."

Step 2: Human raters rank A > B
        (more helpful, more accurate, less alarmist)

Step 3: Train a reward model R(prompt, response) → score

Step 4: Fine-tune LLM with RL to maximise R(prompt, response)
        while staying close to the SFT model (KL divergence penalty)
```

RLHF is why ChatGPT felt so different from GPT-3 — same underlying capability, vastly more aligned behaviour.

**Modern variants:**
- **DPO** (Direct Preference Optimisation) — simpler than RLHF; skips the reward model
- **Constitutional AI** (Anthropic) — uses a set of principles; the model critiques its own outputs

---

## Tokenisation

Text is converted to integers before entering the model:

```python
from tiktoken import get_encoding  # OpenAI's tokeniser

enc = get_encoding("cl100k_base")  # GPT-4's tokeniser

text = "Hello, world! 🌍"
tokens = enc.encode(text)
print(tokens)           # [9906, 11, 1917, 0, 9468, 234, 222]
print(len(tokens))      # 7 tokens (not 7 characters)

# Roundtrip
decoded = enc.decode(tokens)
print(decoded)          # "Hello, world! 🌍"
```

**Why it matters:**
- LLMs think in tokens, not characters or words
- Token count ≠ word count (~0.75 words per token for English)
- Non-English languages are often less efficient (more tokens per word)
- Context window limits are measured in **tokens**, not words

---

## Major LLM Families

### GPT Family (OpenAI)

| Model | Parameters | Context | Key Feature |
|-------|-----------|---------|-------------|
| GPT-3 (2020) | 175B | 4K | First truly capable LLM |
| GPT-3.5 (2022) | ~175B | 16K | ChatGPT; RLHF aligned |
| GPT-4 (2023) | ~1.8T (MoE est.) | 128K | Multimodal; passes bar exam |
| GPT-4o (2024) | Unknown | 128K | Omni: text+image+audio in one model |
| o1 / o3 (2024–25) | Unknown | 128K | Extended "chain of thought" reasoning |

**OpenAI's approach:** proprietary, safety-focused, API-first commercialisation.

### Claude Family (Anthropic)

| Model | Series | Context | Key Feature |
|-------|--------|---------|-------------|
| Claude 2 | 2023 | 100K | Longest context at launch |
| Claude 3 Haiku/Sonnet/Opus | 2024 | 200K | Three-tier speed/quality tradeoff |
| Claude 3.5 Sonnet | 2024 | 200K | Best coding; computer use |
| Claude 4 | 2025 | 1M+ | Agentic; extended context |

**Anthropic's approach:** Constitutional AI, safety-first research, strong reasoning focus.

> 💡 **Claude powers OpenClaw** — the AI personal assistant platform used in this course.

### Gemini Family (Google DeepMind)

| Model | Size | Context | Key Feature |
|-------|------|---------|-------------|
| Gemini Ultra | Large | 1M | Outperforms GPT-4 on MMLU |
| Gemini Pro | Medium | 1M | Production API |
| Gemini Flash | Small | 1M | Fast, cheap, efficient |
| Gemini 2.0 (2025) | — | 2M | Native multimodal from day one |

**Google's approach:** natively multimodal, integrated with Google Search and Workspace.

### Llama Family (Meta)

| Model | Parameters | Notes |
|-------|-----------|-------|
| Llama 2 | 7B–70B | First mainstream open-weight model |
| Llama 3 | 8B–70B | Competitive with GPT-3.5; 15T tokens |
| Llama 3.1 | Up to 405B | Competes with GPT-4 |
| Llama 3.3 (2025) | 70B | Efficient; runs on consumer hardware |

**Meta's approach:** open weights (not open source — the licence has restrictions). Can run locally.

### Other Notable Models

| Model | Organisation | Notes |
|-------|-------------|-------|
| Mistral / Mixtral | Mistral AI (France) | Efficient; MoE architecture; open weights |
| Grok | xAI (Elon Musk) | Real-time web access; integrated with X |
| Qwen | Alibaba | Strong multilingual; Chinese-English |
| DeepSeek | DeepSeek (China) | Extremely efficient training; open weights |
| Phi-3 / Phi-4 | Microsoft | Small but capable (3.8B); runs on phone |

---

## Context Windows

The **context window** is how much text the model can consider at once (input + output combined).

```
GPT-3:      4,096 tokens  ≈  3,000 words
GPT-4:    128,000 tokens  ≈ 96,000 words (a full novel)
Claude 3: 200,000 tokens  ≈ 150,000 words
Gemini:  1,000,000 tokens  ≈ 750,000 words (the entire Harry Potter series)
```

**Practical implication:** A 1M-token context window means you can feed an entire codebase into a single conversation and ask questions about it.

---

## Inference: How LLMs Generate Text

Generation is **autoregressive** — one token at a time, each token fed back in as input:

```
Prompt: "The"
Step 1: model → "cat"         → "The cat"
Step 2: model → "sat"         → "The cat sat"
Step 3: model → "on"          → "The cat sat on"
Step 4: model → "the"         → "The cat sat on the"
Step 5: model → "mat"         → "The cat sat on the mat"
Step 6: model → "<|endoftext|>" → stop
```

**Temperature** controls randomness:
```python
# High temperature → more creative, more random
# Low temperature  → more deterministic, more precise

logits = model(input_ids)
probs  = softmax(logits / temperature)  # temperature=0.0 → argmax (greedy)
next_token = sample(probs)              # temperature=1.0 → sample distribution
```

---

## Summary Comparison

| Property | GPT-4o | Claude 4 | Gemini Ultra | Llama 3.1 |
|----------|--------|---------|--------------|-----------|
| Open weights | ❌ | ❌ | ❌ | ✅ |
| Context | 128K | 1M+ | 2M | 128K |
| Multimodal | ✅ | ✅ | ✅ | Limited |
| Local deployment | ❌ | ❌ | ❌ | ✅ |
| Best for | General; coding | Reasoning; long doc | Multimodal | Privacy; cost |

---

## Further Reading

- [GPT-4 Technical Report (OpenAI)](https://openai.com/research/gpt-4)
- [Claude's Character (Anthropic)](https://www.anthropic.com/research)
- [Gemini Technical Report (Google)](https://arxiv.org/abs/2312.11805)
- [Llama 3 Model Card (Meta)](https://ai.meta.com/llama/)
- [LMSYS Chatbot Arena — Live LLM Leaderboard](https://chat.lmsys.org/)
