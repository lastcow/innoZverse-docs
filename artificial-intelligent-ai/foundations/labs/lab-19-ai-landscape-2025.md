# Lab 19: The AI Landscape in 2025–2026 — GPT-4o, Claude 4, Gemini 2, Grok, and Beyond

## Objective

Get a current map of the AI industry. By the end you will understand:

- The state of frontier models and how they compare
- Key trends shaping AI development in 2025–2026
- Which companies are leading in which areas
- Where the industry is likely to go next

---

## The Current Frontier (Early 2026)

The AI landscape has never moved faster. Models that were state-of-the-art six months ago are now mid-tier. Here is the lay of the land:

### Language Models

| Model | Organisation | Context | Key Strength |
|-------|-------------|---------|-------------|
| **o3 / o3-pro** | OpenAI | 128K | Extended reasoning (chain of thought); highest benchmark scores |
| **GPT-4o** | OpenAI | 128K | Fast, multimodal (text/image/audio/video), API dominance |
| **Claude 4 Sonnet** | Anthropic | 1M+ | Long context, coding, nuanced writing, agentic tasks |
| **Claude 4 Opus** | Anthropic | 1M+ | Highest quality; research and complex analysis |
| **Gemini 2.0 Ultra** | Google DeepMind | 2M | Natively multimodal; deep Google integration |
| **Gemini 2.0 Flash** | Google DeepMind | 1M | Speed + cost; production scale |
| **Grok 3** | xAI | 128K | Real-time X/Twitter data; less restricted |
| **Llama 3.3 (70B)** | Meta | 128K | Best open-weight; competitive with GPT-3.5 |
| **DeepSeek V3** | DeepSeek | 128K | Near-frontier quality; open weights; trained cheaply |
| **Mistral Large 2** | Mistral AI | 128K | European; strong multilingual; open weights option |

### The Reasoning Revolution: OpenAI o-series

The most significant development of 2024–2025: models that **think before answering**.

```
Standard LLM:
  Question → [single forward pass] → Answer

o1 / o3:
  Question → [internal chain of thought, hundreds of steps] → Answer
  The model "thinks" for 5–60 seconds before responding

Result: dramatically better performance on:
- Mathematical reasoning (competition-level)
- Scientific problem solving
- Multi-step logic
- Code generation for complex algorithms
```

**Benchmark example:**
- GPT-4o on AIME 2024 math competition: **13%**
- o1 on same benchmark: **83%**
- o3 on same benchmark: **96.7%** (near perfect)

The tradeoff: thinking takes time and tokens. o3 can cost 30–100× more than GPT-4o for the same question.

---

## Multimodal: One Model for Everything

The "any-to-any" model is the dominant architecture of 2025:

```
INPUT MODALITIES:           OUTPUT MODALITIES:
  Text        ─────┐        ┌──── Text
  Images      ─────┤        ├──── Images (generation)
  Audio       ─────┤ MODEL  ├──── Audio (speech, music)
  Video       ─────┤        ├──── Video (short clips)
  Documents   ─────┤        ├──── Code
  Code        ─────┘        └──── Structured data
```

**GPT-4o:** The "o" stands for "omni" — processes and generates text, image, and audio in a single model (no separate modules). Result: real-time voice conversation with emotional tone, laughter, and interruption handling.

**Gemini 2.0:** Designed as native multimodal from the ground up (not text-model with vision bolted on). Processes 2M token context — can ingest an entire film + script + book as context.

---

## The Context Window Arms Race

```
2020: GPT-3       →    4,096 tokens  (about 3,000 words)
2023: GPT-4       →  128,000 tokens  (a novel)
2023: Claude 2    →  100,000 tokens
2024: Claude 3    →  200,000 tokens  (a long dissertation)
2024: Gemini 1.5  →1,000,000 tokens  (the entire Harry Potter series)
2025: Claude 4    →1,000,000+ tokens
2025: Gemini 2    →2,000,000 tokens  (multiple novels + their film adaptations)
```

**What this enables:**
- Entire codebase in one context window (vs. retrieval-based approaches)
- Full legal contract analysis (thousands of pages)
- Long-document translation without chunking artefacts
- Meeting transcripts + all related emails + Slack history as context

---

## The Open Source Surge

2024–2025 saw open-weight models close the gap dramatically:

| Model | Year | Notable |
|-------|------|---------|
| **Llama 3.1 405B** | 2024 | First open model competitive with GPT-4 on some benchmarks |
| **DeepSeek V3** | 2024 | Trained for ~$6M vs. estimated $100M+ for GPT-4; near-identical performance |
| **Mistral Large 2** | 2024 | European open model; Apache 2.0 licence |
| **Qwen 2.5 Max** | 2025 | Alibaba; strong multilingual; open weights |
| **Falcon 3** | 2025 | UAE Technology Innovation Institute |

**The DeepSeek moment (January 2025):**

DeepSeek released R1, a reasoning model competitive with o1 — trained at a fraction of the cost using efficient training techniques (MoE architecture, mixture of experts). US AI stocks dropped 15–20% in a single day. The implication: frontier AI capability is not as compute-exclusive as assumed.

---

## Key Trends Shaping AI (2025–2026)

### 1. AI Agents Go Mainstream

Moving from demos to production:
- **OpenAI Operator** — agent that controls a web browser to complete tasks
- **Anthropic Computer Use** — Claude controls a real computer
- **Google Project Mariner** — browser agent integrated into Chrome
- **Apple Intelligence** — on-device agent with deep app integration

```python
# What agentic AI looks like in production (2025)
result = agent.run("""
    1. Check my calendar for next week's meetings
    2. For any meeting without a prepared agenda, draft one based on previous meeting notes
    3. Send the draft agendas to attendees via email for review
    4. Book a 15-minute buffer before each meeting
""")
# → Agent executes all 4 steps autonomously over several minutes
```

### 2. On-Device AI

Models running on phones and laptops, not cloud servers:
- **Apple A18 Pro** (iPhone 16 Pro) — dedicated Neural Engine for on-device LLMs
- **Qualcomm Snapdragon X** — PC chip with 45 TOPS NPU for Windows AI
- **Microsoft Copilot+ PCs** — certified AI PC category
- **Phi-3.5 (3.8B)** — Microsoft's model specifically designed for phone deployment

Benefits: privacy, latency, works offline. Limitation: quality gap vs. frontier models.

### 3. AI Coding: The Productivity Revolution

```
GitHub Copilot statistics (2024):
  - 1.3 million paying users
  - 55% of code in some repositories is AI-generated
  - 55% faster task completion for developers

New agentic coding tools (2025):
  - Cursor: AI-first IDE (4 million users)
  - Devin: first autonomous software engineer (handles full engineering tasks)
  - Claude Code: AI coding agent in terminal
  - GitHub Copilot Workspace: multi-agent PR creation
```

### 4. AI Search: The End of the 10 Blue Links?

- **Perplexity AI** — AI-native search with citations; 100M+ monthly searches
- **Google AI Overviews** — AI-generated summaries at top of search results
- **Bing Copilot** — GPT-4 integrated into search
- **ChatGPT Search** — real-time web search in ChatGPT

### 5. Synthetic Data and Model Self-Improvement

The frontier models are increasingly trained on data generated by other frontier models:
- Meta uses LLM-generated data to train Llama
- OpenAI's GPT-4 used to generate training data for smaller models
- "Constitutional AI" uses Claude to critique Claude

The concern: **model collapse** — if models train on their own outputs recursively, quality degrades. Current research shows this requires careful management.

---

## The Compute Race

```
AI compute (FLOPs) used in training:

GPT-2 (2019):     3 × 10²¹ FLOP
GPT-3 (2020):     3 × 10²³ FLOP
GPT-4 (2023):     ~2 × 10²⁵ FLOP  (estimated)
Projected 2026:   10²⁷ FLOP

Each step: ~100× increase in compute
Every 2-3 years since 2012 (faster than Moore's Law)
```

**The energy question:** Training and running LLMs consumes significant energy. GPT-4 inference is estimated to use ~10× the energy of a Google search. AI data centres are a growing share of global electricity consumption. This is an active area of research and policy debate.

---

## What's Coming: 2026 and Beyond

**Near-certain (12–18 months):**
- Reasoning models (o-series style) become standard across all providers
- 10M+ token context windows in production
- AI agents handling multi-day autonomous tasks
- Physical AI: robotics (Figure, Tesla Optimus) using LLM-based reasoning

**Likely (2–3 years):**
- AI scientist — autonomous hypothesis generation and experimental design
- "AGI" claims from at least one major lab (definition contested)
- AI writing most of its own training data
- Personalised on-device models fine-tuned to individual users

**Contested/uncertain:**
- AGI (generally capable AI) — timelines range from "already achieved" to "decades away"
- AI replacing most knowledge workers — vs. augmenting them
- Regulatory fragmentation — EU AI Act vs. US executive orders vs. Chinese regulations
- Open vs. closed — will the open ecosystem sustain the frontier gap closure?

---

## Staying Current

The AI landscape moves faster than any textbook can track. Resources to stay informed:

| Resource | Frequency | Focus |
|----------|-----------|-------|
| **The Batch (DeepLearning.AI)** | Weekly | Applied ML news, curated by Andrew Ng |
| **Import AI (Jack Clark)** | Weekly | Research papers and safety |
| **The State of AI Report** | Annual | Comprehensive industry review |
| **Hugging Face Papers** | Daily | Latest research, with code |
| **Andrej Karpathy (YouTube/X)** | Irregular | Deep technical explanations |
| **Simon Willison's Weblog** | Near-daily | LLM applications and tools |
| **LMSYS Chatbot Arena** | Continuous | Live model benchmarking |

---

## Further Reading

- [State of AI Report 2025](https://www.stateof.ai/)
- [Epoch AI — AI Compute Trends](https://epochai.org/)
- [LMSYS Chatbot Arena Leaderboard](https://chat.lmsys.org/)
- [DeepSeek R1 Technical Report](https://arxiv.org/abs/2501.12948)
- [Anthropic's Model Card for Claude](https://www.anthropic.com/claude)
