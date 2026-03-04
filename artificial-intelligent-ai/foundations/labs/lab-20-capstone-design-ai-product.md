# Lab 20: Capstone — Design Your Own AI Product

## Objective
Apply everything from the Foundations track to design a complete AI product: define the problem, choose the right AI approach, design the system architecture, plan for safety and ethics, estimate costs, and create a product roadmap. This is a thinking and design exercise — no coding required.

**Time:** 45 minutes | **Level:** Foundations | **No coding required**

---

## Background: From Consumer to Builder

You've spent 19 labs learning *how* AI works. Now it's time to think like a builder.

The most important skill in AI is not prompt engineering or even ML — it's **product thinking**:
- What problem is actually worth solving?
- Where does AI add value vs traditional software?
- What could go wrong, and how do you prevent it?

```
The Product Builder's Hierarchy of Needs:
  1. Problem-market fit  (does this pain point exist and matter?)
  2. AI-solution fit     (is AI the right tool, or would a simple rule work?)
  3. Data feasibility    (do you have / can you get training data?)
  4. Safety & ethics     (what are the failure modes and harms?)
  5. Business model      (who pays, how much, why won't they churn?)
```

---

## Step 1: The AI Product Ideation Framework

### When AI Adds Genuine Value

```
AI ADDS VALUE when:
  ✅ Problem requires pattern recognition at scale (millions of events)
  ✅ Human expertise is scarce or expensive (radiologists, security analysts)
  ✅ Personalization matters at scale (recommendations, adaptive learning)
  ✅ The task involves natural language, images, or audio
  ✅ Speed matters more than perfect accuracy
  ✅ Decisions benefit from probabilistic confidence scores

AI is WRONG TOOL when:
  ❌ A simple if-else rule covers 95% of cases
  ❌ You don't have (and can't get) training data
  ❌ Explainability is legally required and ML can't provide it
  ❌ The problem changes so fast that models become stale immediately
  ❌ Stakes are high, errors are catastrophic, and you can't validate
```

### Security Domain Opportunities

```
Tier 1 — High impact, AI clearly adds value:
  → Alert triage: rank 100k daily SIEM alerts → analyst sees only top 50
  → Phishing detection: beyond rules, adapts to new campaigns
  → Malware classification: static analysis + ML → faster than sandboxing
  → Threat actor attribution: graph ML on IOC relationships
  → Vulnerability prioritisation: CVSS + exploit probability + asset criticality

Tier 2 — Medium impact, depends on context:
  → Log anomaly detection: needs good baseline, many false positives
  → Insider threat detection: privacy concerns, high sensitivity
  → Penetration testing assistance: augments humans, doesn't replace
  → Security policy compliance checking: LLM reads config, flags gaps

Tier 3 — Proceed carefully:
  → Automated patch decisions: what if the AI is wrong?
  → Employee behaviour monitoring: legal and ethical minefield
  → Autonomous offensive tools: serious dual-use risk
```

---

## Step 2: Design Exercise — Choose Your Product

Pick ONE of these hypothetical scenarios (or define your own):

### Option A: AI-Powered SOC Analyst Assistant

**Problem**: Tier-1 SOC analysts spend 70% of their time on false positives. Alert fatigue causes real threats to be missed.

**Proposed solution**: An AI assistant that:
- Automatically triages incoming SIEM alerts (benign / suspicious / critical)
- Enriches alerts with threat intel context
- Drafts incident response notes
- Learns from analyst decisions over time

### Option B: Autonomous Phishing Campaign Detector

**Problem**: Phishing campaigns evolve faster than signature-based tools can keep up.

**Proposed solution**: A system that:
- Monitors submitted URLs and screenshots in real time
- Uses multi-modal AI (vision + text + URL features) to classify pages
- Detects brand impersonation automatically
- Blocks pages within 60 seconds of submission

### Option C: AI Penetration Test Reporter

**Problem**: Writing pentest reports takes 40% of a pentest engagement.

**Proposed solution**: An LLM-powered tool that:
- Ingests tool output (nmap, Burp Suite, Metasploit logs)
- Generates structured findings in CVSS format
- Drafts executive summary and technical detail sections
- References relevant CVEs and remediation guides

---

## Step 3: Architecture Design Template

For **your chosen product**, fill in this framework:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI PRODUCT DESIGN CANVAS                     │
├─────────────────┬───────────────────────────────────────────────┤
│ Problem         │ [Who has what pain, how often, how severe?]  │
│ Users           │ [Persona: role, technical level, urgency]    │
│ Success metric  │ [What does good look like? How measured?]    │
├─────────────────┼───────────────────────────────────────────────┤
│ AI approach     │ [Classification / generation / retrieval?]   │
│ Data source     │ [Where does training data come from?]        │
│ Model choice    │ [Off-shelf API / fine-tuned / custom?]       │
│ Evaluation      │ [AUC? F1? Human eval? A/B test?]            │
├─────────────────┼───────────────────────────────────────────────┤
│ System diagram  │                                               │
│                 │  Input → Preprocessing → AI Model → Output   │
│                 │            ↑                  ↓              │
│                 │         Feature eng.       Postprocess        │
│                 │            ↑                  ↓              │
│                 │       Data pipeline      Human review         │
├─────────────────┼───────────────────────────────────────────────┤
│ Failure modes   │ [What if model is wrong? Who gets hurt?]     │
│ Bias risks      │ [Does training data represent all users?]    │
│ Safety measures │ [Human in loop? Confidence thresholds?]      │
├─────────────────┼───────────────────────────────────────────────┤
│ Cost estimate   │ [Compute, API, engineering, data labelling]  │
│ Business model  │ [SaaS? Per-alert? License? Internal tool?]   │
└─────────────────┴───────────────────────────────────────────────┘
```

---

## Step 4: Worked Example — SOC Alert Triage (Option A)

### Problem Definition

```
Users:     Tier-1 SOC analysts at mid-sized enterprises (500-5000 employees)
Pain:      300-500 SIEM alerts/day, 85% false positive rate
           Analyst manually investigates each → 2-4 min per alert = 10-20 hours
Severity:  Critical — real threats buried in noise → MTTD (mean time to detect) averages 21 days
Goal:      Reduce analyst time on FPs by 60%, reduce MTTD to <4 hours
```

### AI Approach

```
Model: Gradient Boosted Trees + LLM enrichment
Input features:
  - Alert type, severity, source IP, destination
  - Historical alert patterns for same source
  - Time of day, user context
  - Threat intel enrichment (VirusTotal, AbuseIPDB scores)

Output:
  - Risk score (0-1)
  - Triage decision (auto-close / escalate / investigate)
  - Explanation (why this decision)
  - Suggested SOAR playbook

Training data:
  - 6 months of analyst-resolved alerts (true positives + false positives)
  - Min 50k samples needed for reliable classification
  - Active learning: analysts' decisions feed back as labels
```

### System Architecture

```
SIEM
 │
 ▼
[Kafka Stream] → [Feature Extractor] → [ML Triage Model] → Risk Score
                        │                       │
                  [Threat Intel API]    [LLM Explanation]
                  (enrichment)          (GPT-4o / Claude)
                        │                       │
                        └─────────┬─────────────┘
                                  ▼
                         [Alert Dashboard]
                          ├── Auto-closed (score < 0.1) → Queue for daily review
                          ├── Auto-escalated (score > 0.85) → Page on-call
                          └── Investigate (0.1-0.85) → Analyst queue
```

### Safety & Ethics

```
Risks:
  1. False negatives: real attack auto-closed → missed breach
     Mitigation: conservative threshold (0.1), periodic review of closed alerts

  2. Model drift: attacker learns to evade the triage model
     Mitigation: drift monitoring, monthly retraining, A/B test new models

  3. Bias: model trained on one environment, deployed in another
     Mitigation: 30-day parallel run, measure performance vs manual baseline

  4. Over-reliance: analysts stop reviewing, lose skills
     Mitigation: random sampling of auto-closed alerts for analyst review

Human-in-the-loop: ALL escalations are reviewed by human. No automated blocks.
```

### Cost Estimate

```
Engineering (1 ML eng, 1 backend, 3 months): £150k
Data labelling (analyst time, 2 weeks):      £8k
Infrastructure (GPU inference, 1 year):      £24k
LLM API (Claude/GPT, 500 alerts/day):        £3k/year

Total first year:  ~£185k
ROI:               If saves 3 analyst hours/day at £50/hr → £55k/yr
                   + Faster MTTD reduces breach cost by £200k+ avg
Payback period:    ~2 years (conservative)
```

---

## Step 5: Roadmap Planning

```
Phase 1 — Proof of Concept (weeks 1-8):
  ☐ Collect 6 months of historical alert data
  ☐ Label sample with analyst decisions
  ☐ Train baseline XGBoost classifier
  ☐ Internal evaluation: does it beat random?
  ☐ Demo to SOC manager

Phase 2 — Pilot (weeks 9-20):
  ☐ Deploy in shadow mode (predictions logged, not acted on)
  ☐ Compare model vs analyst decisions on same alerts
  ☐ Tune threshold to hit <1% false negative rate
  ☐ Integrate LLM explanation generation
  ☐ Build simple UI for analysts to see predictions

Phase 3 — Production (weeks 21-32):
  ☐ Enable auto-close for score < 0.05 (very high confidence benign)
  ☐ Implement drift monitoring
  ☐ Active learning pipeline: analyst decisions → retraining queue
  ☐ SOAR integration for auto-escalated alerts
  ☐ Monthly model review cadence

Phase 4 — Scale (months 9-12):
  ☐ Multi-tenant (serve multiple customer environments)
  ☐ Model specialisation per industry vertical
  ☐ Federated learning (share signals without sharing data)
  ☐ Marketplace listing / partnership with SIEM vendors
```

---

## Key Takeaways from the Foundations Track

Congratulations — you've completed the **AI Foundations track**. Here's what you should now understand:

1. **AI history**: From Turing to Transformers in 70 years — we're in the most rapid phase
2. **How ML works**: Data → features → model → predictions (not magic)
3. **LLMs**: Transformers + RLHF → instruction-following at scale
4. **Prompt engineering**: Clear, specific, contextual prompts get better results
5. **AI agents**: LLMs + tools + memory → autonomous task completion
6. **Vision AI**: CNNs and ViTs process images; CLIP connects vision and language
7. **AI ethics**: Bias, hallucination, privacy, accountability — all must be designed for
8. **AI safety**: Alignment is hard; RLHF helps but isn't solved
9. **Open vs closed**: Trade-offs in capability, privacy, cost, and control
10. **Building AI products**: Problem-first, data-second, model-third

### Your Next Step

Choose your path:
- **Practitioner track** → Get hands-on with scikit-learn, PyTorch, and production ML
- **Security + AI** → Apply ML to threat detection, SIEM triage, malware analysis
- **AI Engineering** → LangChain, RAG, fine-tuning, agent frameworks
- **Build something** → Take your design from Step 2 and start with a 1-week spike

The best way to learn AI is to build something with it. Start small. Iterate fast. Measure everything.

---

## Further Reading
- [AI Product Playbook — Sequoia Capital](https://www.sequoiacap.com/article/ai-playbook/)
- [Designing AI Products — Google PAIR](https://pair.withgoogle.com/)
- [The Pragmatic Engineer — AI Special](https://newsletter.pragmaticengineer.com/)
- [Anthropic's approach to AI safety](https://www.anthropic.com/research)
