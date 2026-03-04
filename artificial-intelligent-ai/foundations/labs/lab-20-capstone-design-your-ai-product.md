# Lab 20: Capstone — Design Your Own AI Product

## Objective

Apply everything from Labs 1–19 to design a complete AI product from idea to architecture. By the end you will have produced:

- A one-page product brief with a well-scoped AI use case
- A technical architecture diagram showing the full AI stack
- A data strategy (sourcing, quality, bias mitigation)
- A safety and ethics assessment
- A build vs. buy decision for each component

---

## The Product Design Framework

Designing AI products requires answering five questions in order:

```
1. PROBLEM    → What human problem does this solve?
2. DATA       → What data exists / can be collected?
3. APPROACH   → What AI technique fits best?
4. ARCHITECTURE → How do the components connect?
5. RISKS      → What could go wrong?
```

Skipping straight to "let's use GPT-4" is the most common AI product failure mode.

---

## Part 1: Product Brief Template

Use this template to define your AI product:

```markdown
# AI Product Brief: [Your Product Name]

## Problem Statement
**User:** [Who experiences this problem?]
**Pain:** [What is the specific, measurable pain?]
**Current solution:** [How do they solve it today? Why is that inadequate?]
**Impact:** [What is the cost/time/risk of the current approach?]

## Proposed Solution
[One paragraph describing the AI-powered solution]

## Success Metrics
- Primary: [The metric that shows the product works]
- Secondary: [Supporting metrics]
- Guard rails: [Metrics that must NOT get worse]

## Constraints
- Data availability: [What data exists?]
- Latency requirement: [How fast must the response be?]
- Budget: [Training and inference cost limits]
- Regulatory: [Any compliance requirements?]
```

### Example Brief: InnoZverse AI Tutor

```markdown
# AI Product Brief: InnoZverse Intelligent Tutor

## Problem Statement
User: Students studying for cybersecurity certifications (Security+, CEH)
Pain: 68% of students abandon self-paced courses due to lack of feedback
      when stuck (Coursera internal data). Getting unstuck requires
      posting on forums and waiting hours for responses.
Current solution: Forum posts, Google search, YouTube — slow and generic
Impact: 4-6 hours wasted per week per student; 40% course completion rate

## Proposed Solution
An AI tutor integrated into each lab that answers questions using only
the course materials (RAG), provides Socratic guidance rather than
direct answers, and escalates to human instructors when the AI
is uncertain or the student is repeatedly stuck.

## Success Metrics
- Primary: Course completion rate (target: 40% → 65%)
- Secondary: Time-to-unstuck (target: <2 minutes vs. current 4 hours)
- Guard rail: Student satisfaction score must not drop below 4.2/5
- Guard rail: Hallucination rate <0.5% (monitored via sampling)

## Constraints
- Data: 240 existing lab documents; student question logs available
- Latency: <3 seconds for first token
- Budget: <£0.02 per student query
- Regulatory: GDPR compliant; student data stays in EU
```

---

## Part 2: AI Technique Selection

Choose the right AI approach for your use case:

```python
# Decision framework
def select_ai_approach(requirements: dict) -> str:

    if requirements["needs_real_time_data"]:
        if requirements["needs_web_browsing"]:
            return "LLM + web search agent (RAG with live retrieval)"
        else:
            return "Fine-tuned LLM + streaming API"

    if requirements["has_labelled_data"] and requirements["data_volume"] > 10_000:
        if requirements["structured_tabular_data"]:
            return "Gradient Boosting (XGBoost) — fast, interpretable, no GPU"
        elif requirements["image_or_audio"]:
            return "CNN or Vision Transformer + transfer learning"
        else:
            return "Fine-tuned LLM or BERT-style model"

    if not requirements["has_labelled_data"]:
        if requirements["needs_generation"]:
            return "Foundation model API (OpenAI/Anthropic/Google)"
        else:
            return "Unsupervised clustering + LLM for interpretation"

    return "Few-shot prompting with frontier LLM (no training needed)"

# For InnoZverse Tutor:
requirements = {
    "needs_real_time_data": False,       # course content is fixed
    "has_labelled_data": False,          # no (question, answer) pairs yet
    "data_volume": 240,                  # 240 lab documents
    "needs_generation": True,            # yes — generate tutor responses
    "latency_ms": 3000,
    "budget_per_query_gbp": 0.02
}
# → "Few-shot prompting + RAG with frontier LLM"
```

### Technique Comparison

| Use Case | Recommended Approach | Why |
|----------|---------------------|-----|
| Q&A over documents | RAG + LLM | Prevents hallucination, stays current |
| Classify emails/tickets | Fine-tuned BERT or few-shot GPT | Fast, cheap, accurate |
| Generate images | Stable Diffusion / DALL-E | Open or API options |
| Detect anomalies | Isolation Forest or Autoencoder | No labels needed |
| Recommend content | Collaborative filtering + embeddings | Personalised at scale |
| Translate text | DeepL API or NLLB (open) | Purpose-built, better than GPT |
| Transcribe audio | Whisper (OpenAI, open) | State-of-the-art, local option |
| Predict churn | Gradient Boosting on tabular | Interpretable, fast |

---

## Part 3: Architecture Design

### Full Stack Diagram Template

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE                           │
│         [React / Next.js / Mobile App / Discord Bot]        │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTPS
┌────────────────────────────▼────────────────────────────────┐
│                       API GATEWAY                           │
│      [FastAPI / Express / Kong]  Auth + Rate Limiting        │
└──────────────┬─────────────────────────────┬───────────────┘
               │                             │
┌──────────────▼─────────┐   ┌───────────────▼──────────────┐
│   AI ORCHESTRATION      │   │    TRADITIONAL BACKEND       │
│   [LangChain/LangGraph] │   │    [PostgreSQL, Redis,       │
│   • RAG pipeline        │   │     User accounts,           │
│   • Agent loop          │   │     Course progress]         │
│   • Memory management   │   │                              │
└──────┬─────────┬────────┘   └──────────────────────────────┘
       │         │
┌──────▼──┐  ┌──▼────────────┐
│  LLM    │  │ VECTOR DB     │
│  API    │  │ [Chroma /     │
│ Claude  │  │  Pinecone]    │
│ GPT-4o  │  │ Lab content   │
└─────────┘  └───────────────┘
```

### InnoZverse Tutor Architecture (Detailed)

```python
# Component breakdown with build vs. buy decisions

architecture = {
    "frontend": {
        "component": "Chat widget embedded in GitBook",
        "decision": "Build",
        "tech": "React + WebSocket for streaming",
        "rationale": "Custom integration with lab content"
    },
    "api_gateway": {
        "component": "Request routing, auth, rate limiting",
        "decision": "Buy",
        "tech": "AWS API Gateway",
        "rationale": "Not our core competency; cheap and reliable"
    },
    "orchestration": {
        "component": "RAG pipeline + conversation management",
        "decision": "Build with LangChain",
        "tech": "Python + LangChain + LangGraph",
        "rationale": "Custom logic; LangChain handles plumbing"
    },
    "llm": {
        "component": "Response generation",
        "decision": "Buy",
        "tech": "Claude Sonnet via Anthropic API",
        "rationale": "Best reasoning quality; £0.003/1K tokens at scale"
    },
    "vector_db": {
        "component": "Lab content retrieval",
        "decision": "Buy (managed)",
        "tech": "Pinecone Serverless",
        "rationale": "240 docs → small; serverless = no ops overhead"
    },
    "embeddings": {
        "component": "Document and query embeddings",
        "decision": "Buy",
        "tech": "text-embedding-3-small (OpenAI)",
        "rationale": "One-time cost; better than open alternatives at this scale"
    },
    "monitoring": {
        "component": "Hallucination detection, quality tracking",
        "decision": "Build",
        "tech": "Custom sampling + Claude as judge",
        "rationale": "Domain-specific quality criteria"
    }
}
```

---

## Part 4: Data Strategy

```python
data_strategy = {
    "sources": {
        "existing": [
            "240 lab markdown files (primary knowledge base)",
            "OWASP Top 10 documentation",
            "CVE database (for security questions)",
        ],
        "to_collect": [
            "Student question logs (anonymised) — start from day 1",
            "Student satisfaction ratings per response",
            "Instructor corrections (gold standard for fine-tuning)",
        ],
        "synthetic": [
            "Generate FAQ pairs using Claude on each lab",
            "Create common misconception Q&A pairs",
        ]
    },
    "quality_controls": {
        "before_indexing": [
            "Deduplication — remove near-duplicate content",
            "Freshness check — labs updated within 6 months",
            "Format validation — all required sections present",
        ],
        "ongoing": [
            "Random sample 50 responses/week for human review",
            "Track: hallucination rate, citation accuracy, student satisfaction",
            "Quarterly re-embedding as labs are updated",
        ]
    },
    "privacy": {
        "student_queries": "Hash user IDs; strip PII before logging",
        "retention": "90 days for individual queries; aggregate forever",
        "gdpr": "Right to deletion; data stays in EU-West-2 (AWS)"
    }
}
```

---

## Part 5: Safety and Ethics Assessment

```python
# Mandatory for any AI product — complete before launch

safety_assessment = {
    "potential_harms": [
        {
            "harm": "Hallucinated security advice leads student to believe vulnerability is patched when it isn't",
            "severity": "High",
            "likelihood": "Medium",
            "mitigation": "RAG grounds all responses; prompt requires source citation; human review queue for security-critical answers"
        },
        {
            "harm": "Student becomes dependent on AI tutor, doesn't develop problem-solving skills",
            "severity": "Medium",
            "likelihood": "Medium",
            "mitigation": "Socratic prompting: AI asks guiding questions, doesn't give direct answers; tracks 'hint usage' metric"
        },
        {
            "harm": "AI provides incorrect exam answers, student fails certification",
            "severity": "High",
            "likelihood": "Low",
            "mitigation": "Clear disclaimer: AI is for learning concepts, not exam prep; link to official study guides"
        },
        {
            "harm": "Jailbroken to provide actual attack instructions",
            "severity": "Critical",
            "likelihood": "Low",
            "mitigation": "Output classifier; system prompt constraints; rate limiting; abuse reporting"
        }
    ],
    "fairness_checks": [
        "Test response quality for non-native English speakers",
        "Ensure explanations don't assume Western educational background",
        "Review for gender/cultural bias in examples used"
    ],
    "human_oversight": {
        "escalation_triggers": [
            "Student marks response as wrong",
            "AI expresses uncertainty",
            "Same student stuck for >3 exchanges",
        ],
        "escalation_path": "Flag for instructor review within 24 hours",
        "kill_switch": "Feature flag to disable AI tutor instantly if major issue detected"
    }
}
```

---

## Part 6: Build Plan and Cost Model

```python
# Realistic cost model for InnoZverse Tutor at scale

COST_MODEL = {
    "per_query": {
        "llm_input_tokens":   240,    # avg system + context + question
        "llm_output_tokens":  180,    # avg response length
        "embedding_tokens":   50,     # query embedding
        "vector_db_query":    0.00001,  # Pinecone serverless per query
    },
    "cost_per_query_gbp": {
        "claude_sonnet": (240 + 180) / 1_000_000 * 3 * 0.78,  # ~£0.001
        "embeddings":    50 / 1_000_000 * 0.02 * 0.78,         # ~£0.000001
        "pinecone":      0.00001,                                # ~£0.00001
        "total":         "~£0.001 per query"
    },
    "monthly_at_scale": {
        "500_students": {
            "queries_per_student_per_day": 10,
            "total_queries": 150_000,
            "cost_gbp": 150   # £150/month
        },
        "5000_students": {
            "total_queries": 1_500_000,
            "cost_gbp": 1500  # £1,500/month
        }
    }
}

# Build timeline (2-person team)
TIMELINE = {
    "week_1": "Index all lab content; basic RAG pipeline working",
    "week_2": "Socratic prompting + conversation memory",
    "week_3": "Frontend widget + API integration",
    "week_4": "Safety testing, red-teaming, quality evaluation",
    "week_5": "Beta with 20 students; collect feedback",
    "week_6": "Iteration based on beta; monitoring setup",
    "week_7": "Production launch to all students",
}
```

---

## Your Capstone Assignment

Design an AI product using this framework. Choose one of these starting points or define your own:

**Option A: Security Training Simulator**
An AI red team opponent that simulates realistic attacker behaviour for students to practise incident response against.

**Option B: CVE Intelligence Briefing**
A daily AI-generated security briefing: pulls new CVEs, assesses impact for a given tech stack, drafts mitigation guidance.

**Option C: Code Security Review Bot**
A GitHub bot that reviews every PR for OWASP Top 10 vulnerabilities, explains issues with educational context, and suggests remediated code.

**Option D: Your own idea**
Use the framework to design any AI product you've been thinking about.

---

**Deliverables for each option:**
1. ✅ Product Brief (250 words)
2. ✅ Architecture diagram (sketch or ASCII)
3. ✅ Technique selection with justification
4. ✅ Data strategy (3 bullet points each for sources, quality, privacy)
5. ✅ Top 3 risks and mitigations
6. ✅ Cost estimate for 1,000 monthly users

---

## Congratulations

You have completed the **AI Foundations** track. You now understand:

- The history and trajectory of AI development
- How neural networks and Transformers work
- The full spectrum of ML approaches
- Why data quality determines model quality
- How modern LLMs are built and differentiated
- How to write effective prompts
- How AI agents use tools to act in the world
- OpenClaw and how to extend it with skills
- Vision AI, real-world applications, ethics, safety
- The current AI landscape and where it's heading
- How to design and evaluate an AI product end-to-end

**Next:** [AI Practitioner Track](../../practitioner/) — supervised learning, neural networks hands-on, NLP fundamentals.

---

## Further Reading

- [AI Product Management Specialisation (Coursera)](https://www.coursera.org/specializations/ai-product-management-duke)
- [Building AI Products — Chip Huyen](https://huyenchip.com/2023/06/07/generative-ai-strategy.html)
- [Pragmatic AI — Noah Gift](https://www.amazon.com/Pragmatic-AI-Introduction-Cloud-Based-Learning/dp/0134863863)
- [LLM Patterns — Eugene Yan](https://eugeneyan.com/writing/llm-patterns/)
