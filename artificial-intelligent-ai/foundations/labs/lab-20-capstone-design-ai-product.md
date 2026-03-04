# Lab 20: Capstone — Design Your Own AI Product

## Objective
Apply everything from Labs 01–19 to design a complete AI product: from problem definition through architecture, model selection, data strategy, safety considerations, deployment plan, and business model. You leave with a professional product spec.

**Time:** 60 minutes | **Level:** Foundations | **Type:** Design Workshop

---

## Background

Building an AI product is 20% choosing the model and 80% everything else:

```
20%: Which model?
80%: What problem? Who for? What data? How to evaluate?
     How to handle failures? What are the risks? How to monetise?
     How to maintain it? What if it's wrong?
```

This capstone walks you through the entire product design process using a structured framework. You'll design a real AI product from scratch.

---

## The AI Product Design Framework

```
┌─────────────────────────────────────────────────────────┐
│  1. PROBLEM DEFINITION                                  │
│     What specific pain are you solving? For whom?       │
├─────────────────────────────────────────────────────────┤
│  2. DATA STRATEGY                                       │
│     What data do you have? What do you need? Privacy?   │
├─────────────────────────────────────────────────────────┤
│  3. AI ARCHITECTURE                                     │
│     Which model? RAG? Agents? Fine-tune or prompt?      │
├─────────────────────────────────────────────────────────┤
│  4. EVALUATION PLAN                                     │
│     How do you know it's working? Metrics? Benchmarks?  │
├─────────────────────────────────────────────────────────┤
│  5. SAFETY & ALIGNMENT                                  │
│     What can go wrong? Bias? Misuse? Failure modes?     │
├─────────────────────────────────────────────────────────┤
│  6. DEPLOYMENT & MONITORING                             │
│     How do users access it? How do you detect drift?    │
├─────────────────────────────────────────────────────────┤
│  7. BUSINESS MODEL                                      │
│     How does it create value? How do you capture it?    │
└─────────────────────────────────────────────────────────┘
```

---

## Worked Example: SecureAdvisor — AI Cybersecurity Assistant

Let's design a complete product together as a worked example.

---

### Step 1: Problem Definition

**Problem statement:**
> Security analysts at mid-sized companies (50–500 employees) spend 3–4 hours per day triaging alerts, searching knowledge bases, and writing incident reports — time that should go to actual investigation.

**Target user:** Tier-1 and Tier-2 SOC analysts

**Job to be done (JTBD):**
- "When I get a security alert, I need to quickly understand if it's a real threat and what to do"
- "When writing an incident report, I need help structuring findings professionally"
- "When a new CVE drops, I need to know if our environment is affected"

**Success metric (user):**
- Alert triage time reduced by ≥50%
- Analyst satisfaction score ≥ 4/5
- False negative rate (missed real threats) < 0.1%

**What this is NOT:**
- Not a replacement for analysts (augmentation, not automation)
- Not a compliance tool
- Not a threat intelligence platform

> 💡 Narrow problem definitions win. "AI for cybersecurity" is not a product. "Reduce Tier-1 SOC triage time by 50% at mid-market companies" is a product.

---

### Step 2: Data Strategy

**Data inventory:**

| Data Source | Volume | Quality | Privacy Risk |
|-------------|--------|---------|-------------|
| NVD CVE database | 250K CVEs | High | None |
| MITRE ATT&CK | 800+ techniques | High | None |
| Customer SIEM logs | Varies | Medium | HIGH — PII |
| Incident reports | 10–100/company | High | Medium |
| Threat intel feeds | Real-time | Medium | Low |
| Vendor advisories | Thousands/year | High | None |

**Data pipeline:**

```python
# Pseudocode: SecureAdvisor data pipeline
class DataPipeline:
    def ingest_public(self):
        """Public knowledge: CVE, MITRE, advisories → RAG knowledge base"""
        sources = [NVD(), MITREAttack(), VendorAdvisories(), SecurityBlogs()]
        for source in sources:
            docs = source.fetch_latest()
            embeddings = embed(docs)
            vector_db.upsert(embeddings)

    def ingest_customer(self, tenant_id: str):
        """Customer-specific: SIEM logs, past incidents → per-tenant context"""
        # CRITICAL: never mix tenant data
        with TenantIsolation(tenant_id):
            logs = siem.fetch_recent(days=90)
            clean_logs = pii_remover.process(logs)  # strip IPs, usernames
            tenant_vector_db[tenant_id].upsert(embed(clean_logs))
```

**Critical data decisions:**
- **Multi-tenancy isolation**: Every customer's data stays strictly separate
- **PII scrubbing**: SIEM logs → strip IP addresses, usernames before LLM sees them
- **Retention policy**: Logs kept 90 days; anonymised summaries kept 2 years
- **Consent model**: Customers explicitly opt-in to using their data for improvements

---

### Step 3: AI Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     SecureAdvisor Architecture               │
│                                                              │
│  User Query                                                  │
│      │                                                       │
│      ▼                                                       │
│  Intent Router ─────────────────────────────────────────    │
│      │              │                    │                   │
│      ▼              ▼                    ▼                   │
│  CVE Lookup    Alert Triage        Report Writer             │
│      │              │                    │                   │
│      ▼              ▼                    ▼                   │
│  Public RAG    Hybrid RAG           Structured LLM           │
│  (NVD, MITRE)  (Public + Tenant)    (template + fill)        │
│      │              │                    │                   │
│      └──────────────┴────────────────────┘                   │
│                      │                                       │
│                      ▼                                       │
│               Claude Sonnet (LLM)                            │
│                      │                                       │
│                      ▼                                       │
│              Response + Citations                            │
└──────────────────────────────────────────────────────────────┘
```

**Model selection decision:**

| Option | Why Consider | Why Reject |
|--------|-------------|------------|
| GPT-4o | Great capabilities | Data leaves infrastructure |
| Claude Sonnet | 200K context, strong reasoning | API dependency |
| Llama 3.1 70B (self-hosted) | Privacy, no API cost | Infrastructure burden |
| **Decision: Claude Sonnet + private deployment** | Balance of capability + control | — |

**Why RAG instead of fine-tuning:**

```python
# Fine-tuning: bake knowledge into weights
# Problem: CVE database updates daily — can't retrain daily
# 
# RAG: retrieve relevant knowledge at query time
# Benefit: add new CVEs without retraining, cite sources
# 
# Fine-tuning IS appropriate for: style/format consistency,
# domain-specific reasoning patterns, inference efficiency

# Architecture: RAG for knowledge, fine-tune for format
pipeline = """
1. Retrieve: Top-5 relevant CVEs/techniques from vector DB
2. Augment: Inject into prompt with structured context
3. Generate: Claude produces grounded response
4. Cite: Response includes source links (CVE IDs, ATT&CK IDs)
"""
```

**Agent vs non-agent:**

```python
# For SecureAdvisor: Agent with tools
agent_tools = [
    search_nvd_database,      # lookup CVE details
    query_mitre_attack,       # find related techniques
    check_customer_history,   # similar past incidents
    generate_yara_rule,       # create detection signatures
    create_jira_ticket,       # action: create incident ticket
]

# Agentic loop: query → tool calls → synthesise → respond
```

---

### Step 4: Evaluation Plan

**Automated evaluation:**

```python
eval_suite = {
    "CVE accuracy": {
        "metric": "exact_match + fuzzy_match on CVE IDs",
        "dataset": "100 CVE questions with verified answers",
        "target": ">= 95% accuracy"
    },
    "Hallucination rate": {
        "metric": "% responses citing non-existent CVEs",
        "dataset": "200 queries, verified by security expert",
        "target": "< 0.5% hallucination"
    },
    "Triage accuracy": {
        "metric": "False negative rate on alert classification",
        "dataset": "500 labelled alerts (200 real threats)",
        "target": "FN rate < 0.1%"
    },
    "Response latency": {
        "metric": "P95 response time",
        "target": "< 3 seconds"
    },
    "Retrieval precision": {
        "metric": "NDCG@5 on retrieved documents",
        "target": "> 0.85"
    }
}
```

**Human evaluation:**

```python
human_eval = {
    "Analyst satisfaction": "Weekly survey, 1–5 scale, target 4.2+",
    "Helpfulness":          "Was this response useful? Yes/No, target 80%+",
    "Trust calibration":    "Did the model admit uncertainty when appropriate?",
    "Escalation accuracy":  "Did it correctly identify when human review needed?",
}
```

**A/B testing plan:**

```python
"""
Week 1–2: 20% analysts get AI assistant (silent mode, suggestions not shown)
Week 3–4: 20% see suggestions, compare triage time
Week 5+:  Gradual rollout, monitoring false negative rate closely
Never:    Full auto-action without human approval
"""
```

---

### Step 5: Safety and Alignment

**Threat model for AI product:**

```python
threats = {
    "Prompt injection": {
        "scenario": "Attacker embeds instruction in log file: 'Ignore all previous instructions...'",
        "mitigation": "Input sanitisation, separate system/user message boundaries, canary tokens",
    },
    "Data exfiltration": {
        "scenario": "Model asked to 'summarise all customer records'",
        "mitigation": "Strict tenant isolation, data access controls, output filtering",
    },
    "Hallucination of CVEs": {
        "scenario": "Model invents non-existent vulnerabilities, analyst wastes time",
        "mitigation": "All CVE citations verified against live NVD; model says 'I don't know' if uncertain",
    },
    "Adversarial inputs": {
        "scenario": "Attacker crafts SIEM log to manipulate AI classification",
        "mitigation": "Model confidence scores, human review for edge cases, anomaly detection on model outputs",
    },
    "Bias in threat prioritisation": {
        "scenario": "Model deprioritises threats associated with specific countries/vendors",
        "mitigation": "Regular bias audits, diverse evaluation dataset, human override always available",
    },
    "Over-reliance": {
        "scenario": "Analysts trust AI completely, stop thinking critically",
        "mitigation": "Show confidence scores, explain reasoning, require human sign-off on critical actions",
    },
}

for threat, details in threats.items():
    print(f"Threat: {threat}")
    print(f"  Scenario:   {details['scenario'][:70]}...")
    print(f"  Mitigation: {details['mitigation'][:70]}...")
    print()
```

**Alignment principles for SecureAdvisor:**

```python
alignment_principles = [
    "NEVER take destructive action (block IP, delete files) without explicit human approval",
    "ALWAYS cite sources — no claims without evidence",
    "ALWAYS express uncertainty — 'I'm not sure' is correct and expected",
    "NEVER access data outside the current tenant context",
    "ALWAYS escalate to human when confidence < 80% on critical decisions",
    "NEVER expose one customer's data to another customer",
    "ALWAYS provide a 'why' explanation, not just a verdict",
]
```

---

### Step 6: Deployment and Monitoring

**Deployment architecture:**

```yaml
# Infrastructure decision: private cloud deployment
deployment:
  strategy: kubernetes_on_aws
  regions: [us-east-1, eu-west-1]  # data residency compliance

  services:
    api_gateway:      rate_limiting + auth
    inference:        2x claude_sonnet_api (primary + fallback)
    vector_db:        weaviate (tenant-isolated collections)
    embedding_service: text-embedding-3-small (openai)

  scaling:
    min_replicas: 2
    max_replicas: 20
    target_latency_p95: 3000ms
```

**Monitoring plan:**

```python
monitoring_metrics = {
    "Model metrics": [
        "hallucination_rate",           # checked by verifier service
        "citation_accuracy",            # CVE IDs validated vs NVD
        "false_negative_rate",          # weekly human audit sample
        "response_confidence_dist",     # track confidence score drift
    ],
    "System metrics": [
        "latency_p50_p95_p99",
        "error_rate",
        "vector_db_recall@5",
    ],
    "Business metrics": [
        "analyst_triage_time",          # integration with ticketing
        "model_suggestions_accepted",   # acceptance rate
        "escalation_rate",              # how often model deferred to human
    ],
    "Safety metrics": [
        "prompt_injection_attempts",    # logged, alerted at threshold
        "cross_tenant_access_attempts", # zero tolerance, immediate alert
        "output_filter_triggers",       # content policy triggers
    ],
}
```

---

### Step 7: Business Model

```python
business_model = {
    "Target segment": "Mid-market companies (50–500 employees), 1–10 SOC analysts",
    "Pricing": {
        "Starter":    "$499/month — 1 analyst seat, public knowledge only",
        "Team":       "$1,499/month — 5 seats, customer log integration",
        "Enterprise": "Custom — unlimited seats, on-premise option, SLA",
    },
    "Value proposition": {
        "Analyst":   "Save 2+ hours/day on triage and documentation",
        "CISO":      "Faster MTTR, better coverage with same headcount",
        "CFO":       "$500/month vs $80K/year analyst — ROI in first week",
    },
    "Moat": "Network effects: more customer data → better triage models → more customers",
    "Risk": "OpenAI / Microsoft could build this into Copilot for Security",
    "Differentiation": "Vertical depth (security-specific), privacy-first, explainability",
}
```

---

## Your Turn: Design Worksheet

Use this template to design your own AI product:

```markdown
## AI Product Design Worksheet

### 1. Problem
- Who has this problem? (Be specific — "security analysts at 50–500 person companies")
- What do they do today instead? (Manual, slow, expensive, error-prone)
- What's the cost of the problem? (Time, money, risk)

### 2. Data
- What data do I have access to?
- What data do I need to acquire?
- What are the privacy/legal constraints?

### 3. AI Architecture
- Foundation model: (GPT-4o / Claude / Gemini / Llama / other)
- Approach: (Prompt engineering / RAG / Fine-tuning / Agents)
- Why this approach vs alternatives?

### 4. Evaluation
- What does "good" look like? (Metrics with numbers)
- How will I test before launching?
- How will I monitor in production?

### 5. Safety
- What are the 3 worst failure modes?
- How will I prevent/detect/recover from each?

### 6. Deployment
- Who accesses it and how? (API / web app / IDE plugin)
- What's my rollout plan? (Pilot → gradual → full)

### 7. Business
- How does this create value?
- How do I capture part of that value?
- What's my unfair advantage?
```

---

## Product Ideas to Inspire You

| Domain | Problem | AI Approach |
|--------|---------|-------------|
| Healthcare | Doctors spend 2h/day on documentation | LLM + voice → auto SOAP notes |
| Legal | Lawyers charge $400/h for contract review | RAG + LLM → clause extraction |
| Education | Students don't know what to study next | Adaptive learning + LLM tutor |
| Finance | Analysts read 50 reports/day | Summarisation + sentiment + alerts |
| HR | Hiring managers screen 200 CVs/role | Embedding similarity + LLM scoring |
| Security | SOC analysts spend 3h/day on triage | SecureAdvisor (our example above) |
| DevOps | Engineers debug for hours | Log analysis + RAG + LLM root cause |
| Supply Chain | Procurement reads 1000s of supplier docs | Document parsing + risk scoring |

---

## What Makes an AI Product Succeed

Based on real product launches:

```python
success_factors = {
    "Narrow focus wins":   "Solve ONE problem brilliantly vs many problems poorly",
    "Data moat matters":   "Proprietary data = defensible advantage; prompts are not a moat",
    "Trust is earned":     "Explainability + confidence scores + 'I don't know' build trust",
    "Latency kills UX":    "If >3 seconds, users abandon; if >10 seconds, they never come back",
    "Humans in the loop":  "For high-stakes decisions, always keep human override; reduces liability",
    "Eval before launch":  "No eval = flying blind; launch with eval suite in place",
    "Monitor everything":  "Model drift is silent; production monitoring is not optional",
}

failure_modes = {
    "Demo-to-prod gap":    "Product demos on hand-picked examples but fails on real data",
    "Hallucination trust": "Users trust model without verification → bad decisions",
    "Privacy breach":      "Customer data leaks → career-ending incident",
    "Prompt injection":    "Attacker hijacks product via crafted inputs",
    "No eval baseline":    "Can't detect degradation without baseline metrics",
    "Over-engineering":    "RAG + agents + fine-tuning when prompt engineering works",
}
```

---

## Capstone Checklist

Before you call your AI product "designed," verify:

- [ ] Problem is specific (named target user, measurable pain)
- [ ] Data sources identified (with privacy analysis)
- [ ] Architecture decision justified (not just "GPT-4")
- [ ] Evaluation suite defined (automated + human)
- [ ] Top 3 failure modes documented with mitigations
- [ ] Monitoring plan includes safety metrics
- [ ] Business model answers: who pays, how much, why now

---

## Congratulations — You've Completed AI Foundations 🎉

Over 20 labs, you've covered:

| Labs | Topics |
|------|--------|
| 01–03 | AI history, how LLMs work, transformers |
| 04–07 | Prompt engineering, RAG, agents, fine-tuning |
| 08–10 | AI coding tools, OpenClaw platform, multi-agent |
| 11–14 | Vision AI, real-world AI, ethics, safety |
| 15–18 | Open source vs closed, AI developer toolkit, RAG systems, AI in cybersecurity |
| 19–20 | 2025 AI landscape, product design capstone |

**What's next:** AI/ML Practitioner — 20 hands-on labs where you implement these concepts in Python with real verified code.

## Further Reading
- [Chip Huyen — Designing Machine Learning Systems](https://www.oreilly.com/library/view/designing-machine-learning/9781098107956/)
- [LangChain Product Patterns](https://blog.langchain.dev/)
- [A16z: The New Language Model Stack](https://a16z.com/emerging-architectures-for-llm-applications/)
- [AI Snake Oil by Arvind Narayanan](https://www.aisnakeoil.com/)
