# Lab 19: The AI Landscape in 2025–2026

## Objective
Survey the rapidly evolving AI landscape: frontier models (GPT-4o, Claude 4, Gemini 2, Llama 3, Grok), benchmark comparisons, the open vs closed model ecosystem, emerging capabilities (long context, vision, agents, reasoning), and what the next 12 months will bring.

**Time:** 35 minutes | **Level:** Foundations | **No coding required**

---

## Background: Why the Landscape Changes So Fast

AI capabilities are advancing faster than any technology in history. What was state-of-the-art 18 months ago is now surpassed by open-source models running on a laptop.

```
2020: GPT-3 (175B params) — text only, API only, expensive
2022: ChatGPT launches → mainstream AI awareness
2023: GPT-4 (multimodal), Llama 1/2 (open-source), Claude 2
2024: GPT-4o, Claude 3 (Haiku/Sonnet/Opus), Gemini 1.5 Pro (1M context)
      Llama 3 (open, competitive with closed models)
2025: Claude 4, Gemini 2, GPT-4.5/o3, Grok 3, Llama 4
      Reasoning models (o1, o3, R1), long context (10M+ tokens)
2026: Multi-agent, real-time voice, autonomous coding agents emerging
```

---

## Step 1: Frontier Model Comparison

### Closed Models (API-only)

| Model | Provider | Context | Strengths | Pricing (approx) |
|-------|----------|---------|-----------|-----------------|
| Claude Sonnet 4.6 | Anthropic | 200K | Coding, safety, instruction following | $3/MTok in |
| Claude Opus 4 | Anthropic | 200K | Most capable, complex reasoning | $15/MTok in |
| GPT-4o | OpenAI | 128K | Multimodal, fast, ecosystem | $5/MTok in |
| GPT-o3 | OpenAI | 200K | Chain-of-thought reasoning | $10/MTok in |
| Gemini 2.0 Pro | Google | 2M | Huge context, multimodal, Search grounding | $3.5/MTok in |
| Grok 3 | xAI | 128K | Real-time web, Twitter data | Available via API |

> 💡 **The context window arms race**: Gemini 2.0 supports 2 million tokens — enough to fit the entire Linux kernel source code in a single prompt. Claude and GPT are not far behind.

### Open-Source Models (run locally)

| Model | Params | Context | Quantised Size | Who Uses It |
|-------|--------|---------|---------------|-------------|
| Llama 3.3 70B | 70B | 128K | ~40GB (FP16), 20GB (INT8) | Enterprises, researchers |
| Mistral 7B | 7B | 32K | ~4GB (INT4) | Edge, privacy-first |
| Qwen 2.5 72B | 72B | 128K | ~40GB | Coding tasks |
| DeepSeek R1 | 671B | 128K | Too large for most | Research |
| Phi-3 Mini | 3.8B | 128K | ~2GB | Mobile, IoT |

```
To run Llama 3.3 70B locally (Ollama):
  ollama pull llama3.3:70b-instruct-q4_K_M
  ollama run llama3.3:70b-instruct-q4_K_M

Minimum hardware: 24GB VRAM GPU (RTX 3090 / 4090)
Consumer option:  32GB MacBook M3 Pro runs 70B INT4 at ~15 tokens/s
```

---

## Step 2: Benchmark Comparison

### Standard Benchmarks (as of early 2026)

```
MMLU (Multi-task Language Understanding — knowledge breadth):
  GPT-4o:          0.887
  Claude Sonnet 4: 0.892
  Gemini 2 Pro:    0.901
  Llama 3.3 70B:   0.862

HumanEval (Python code generation):
  Claude Sonnet 4: 0.912
  GPT-4o:          0.895
  Gemini 2 Pro:    0.883
  Llama 3.3 70B:   0.814

MATH (competition mathematics):
  GPT-o3:          0.963  ← reasoning model
  Claude Opus 4:   0.897
  GPT-4o:          0.762
  Llama 3.3 70B:   0.701
```

> 💡 **Benchmark saturation**: Models are approaching 90%+ on many benchmarks designed for humans. The field is moving to harder benchmarks: SWE-bench (real GitHub issues), ARC-AGI (novel reasoning), Humanity's Last Exam.

### Real-World Performance Matters More

Benchmark scores don't tell the whole story:
- **Instruction following**: Claude is generally considered best
- **Code quality**: Claude Sonnet and GPT-4o are neck-and-neck
- **Safety**: Claude (RLHF + Constitutional AI) leads
- **Speed**: Gemini Flash, Claude Haiku are fastest at low cost
- **Long context accuracy**: Gemini 2.0 handles 1M+ tokens best

---

## Step 3: Emerging Capabilities in 2025–2026

### 1. Reasoning Models (o1, o3, R1, QwQ)

```
Standard model: input → immediate answer
Reasoning model: input → [internal thinking: chain of thoughts] → answer

Key difference: reasoning models spend compute at inference time (not just training).
o3-high: solves competition math, writes better code, but costs 10-50× more.

When to use:
  ✅ Complex multi-step problems
  ✅ Math, logic, proofs
  ✅ Strategic planning
  ❌ Simple Q&A (overkill, slow, expensive)
  ❌ Real-time latency-sensitive applications
```

### 2. Agent Frameworks Maturing

```
2023: LangChain (complex, brittle, lots of abstraction)
2024: CrewAI, AutoGen (multi-agent, easier)
2025: OpenAI Agents SDK, Anthropic Agent framework
2026: Coding agents (Claude Code, Devin, OpenHands) doing real work

Real capability demonstrated:
  - SWE-bench score: agents solve 50%+ of real GitHub issues
  - OpenClaw: personal AI agent managing calendar, email, devices
  - Codex/Cursor: AI writes 40%+ of code at some companies
```

### 3. Multimodal Expansion

```
2024: Image understanding (GPT-4V, Claude 3)
2025: Video understanding, real-time voice (GPT-4o Advanced Voice)
2026: Document → structured data extraction, screen control agents

Security applications:
  - Screenshot forensics (analyse malware UI without execution)
  - Network diagram parsing
  - Log file visual summarisation
  - Voice-based SOC alert response
```

### 4. Context Window Explosion

```
Token limits (input):
  2022: 4K (GPT-3.5)
  2023: 32K (GPT-4)
  2024: 200K (Claude 3), 1M (Gemini 1.5)
  2025: 2M (Gemini 2), 200K standard

What becomes possible at 2M tokens:
  - Entire codebase in context
  - All past year's logs in a single prompt
  - Full novel/legal document analysis
  - Meeting transcript history (months)
```

---

## Step 4: Open-Source vs Closed — 2026 State

### The Capability Gap is Closing

```
2023: GPT-4 was 2-3 years ahead of open-source
2024: Llama 2 70B ≈ GPT-3.5; open models catching up
2025: Llama 3 70B ≈ GPT-4 (early 2024 version)
2026: Open frontier models (Llama 4, DeepSeek V3) approach GPT-4o

Rate of improvement: open-source halves the gap every 6-9 months.
```

### Choosing Open vs Closed

| Factor | Closed (API) | Open-Source |
|--------|-------------|-------------|
| Capability ceiling | Highest (today) | Catching up fast |
| Data privacy | Data sent to provider | 100% local |
| Cost at scale | Per-token (can be high) | Hardware only |
| Customisation | Limited fine-tuning | Full control |
| Compliance (HIPAA/GDPR) | Requires BAA/DPA | Easier |
| Setup complexity | Minutes (API key) | Hours–days |
| Latency | Network round-trip | Local inference |

---

## Step 5: What to Expect in the Next 12 Months

```
Prediction (with moderate confidence):

  Models:
  → Claude 5 / GPT-5 announced (1-2× current capability jump)
  → Sub-7B models rivalling today's 70B
  → Specialised security/coding models fine-tuned for enterprise

  Agents:
  → Computer-use agents (control browsers, GUIs) go mainstream
  → Multi-agent pipelines automate 60%+ of software sprint tasks
  → Autonomous red-team agents first commercial products

  Infrastructure:
  → Sub-1ms inference via speculative decoding + caching
  → On-device models on smartphones (iPhone, Android built-in)
  → AI chips (Groq, Cerebras, custom ASICs) cut inference cost 10×

  Regulatory:
  → EU AI Act enforcement begins (high-risk AI must be audited)
  → US executive orders on frontier model safety evaluations
  → Mandatory disclosure of AI-generated content in regulated sectors
```

---

## Key Takeaways

1. **Models are commoditising** — the API layer matters less; the application layer is where value is created
2. **Open-source is viable** for most enterprise use cases (data privacy, cost, customisation)
3. **Reasoning models** are a new paradigm — not just bigger, but thinking differently
4. **Context windows** are now practically unlimited — retrieval is supplemented, not replaced
5. **Agents are real** — not sci-fi; companies are deploying them in production today
6. **Security implications are growing** — AI is both a defensive tool and an attack vector

---

## Further Reading
- [LMSYS Chatbot Arena](https://chat.lmsys.org/) — live human preference rankings
- [Artificial Analysis](https://artificialanalysis.ai/) — model benchmark comparisons
- [The Batch — DeepLearning.AI](https://www.deeplearning.ai/the-batch/) — weekly AI news
- [State of AI Report 2025](https://www.stateof.ai/)
- [HuggingFace Open LLM Leaderboard](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)
