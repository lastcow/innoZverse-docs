# Lab 13: The Ethics of AI — Bias, Hallucinations, Deepfakes, and Accountability

## Objective

Understand the ethical challenges that come with deploying AI in the real world. By the end you will be able to:

- Identify and categorise AI harms across multiple dimensions
- Explain why AI hallucinations occur and how to mitigate them
- Describe the deepfake threat landscape
- Apply an ethical framework when building or deploying AI systems

---

## Why Ethics in AI Matters

AI systems are not neutral tools. They amplify human decisions — and human biases — at machine scale. A biased human makes biased decisions for the people they interact with. A biased AI system makes biased decisions for millions of people simultaneously, often invisibly, often automatically.

> *"The discourse on AI ethics has moved from 'should we worry?' to 'what do we do about the harms that are already happening?'"* — Kate Crawford, *Atlas of AI* (2021)

---

## The Harm Taxonomy

AI harms fall into several categories:

```
AI HARMS
│
├── Allocative harms
│   └── AI denies resources/opportunities: loans, jobs, bail, healthcare
│
├── Representational harms  
│   └── AI reinforces stereotypes: image search "CEO" returns mostly men
│
├── Quality-of-service disparities
│   └── AI works worse for some groups: voice recognition fails on accents
│
├── Informational harms
│   └── AI generates false information: hallucinations, misinformation
│
├── Privacy harms
│   └── AI infers sensitive information: sexual orientation from photos
│
└── Autonomy harms
    └── AI manipulates or surveils: Cambridge Analytica, social scoring
```

---

## Algorithmic Bias: Case Studies

### Case 1: COMPAS Recidivism Scoring (USA)

COMPAS was used by US courts to predict whether defendants would reoffend, informing bail and sentencing decisions.

ProPublica's 2016 analysis found:
- Black defendants: **44.9%** incorrectly flagged as high risk (false positive rate)
- White defendants: **23.5%** incorrectly flagged as high risk (false positive rate)
- Nearly **2×** disparity in false positive rates

The algorithm never saw race — but neighbourhood, employment history, and social connections are correlated with race due to systemic inequality. Historical injustice was encoded as "risk factors."

### Case 2: Facial Recognition in Law Enforcement

MIT Media Lab study (2018, Joy Buolamwini):
- Light-skinned men: 0.8% error rate
- Dark-skinned women: 34.7% error rate

Real-world consequence: Robert Williams (2020) — first documented case of wrongful arrest due to facial recognition. Detroit police arrested him based on a false match despite him having an alibi for the entire period.

### Case 3: Amazon Hiring Algorithm (2018)

Amazon trained a CV screening model on 10 years of hiring decisions (predominantly male in tech roles). The model learned to penalise:
- CVs with the word "women's" (women's chess club, women's cricket)
- Graduates of all-women's colleges

Amazon scrapped the system when the bias was discovered. It was never used in production.

---

## Hallucinations: When AI Confidently Lies

An **AI hallucination** is when an LLM generates plausible-sounding but factually incorrect information, stated with complete confidence.

```
User: "Who is the CEO of InnoZverse?"
LLM:  "The CEO of InnoZverse is Dr. James Harrison, who founded the company 
       in 2019 after leaving Google DeepMind..."
      [HALLUCINATION — Dr. James Harrison does not exist; 
       InnoZverse's actual leadership is entirely fabricated here]
```

**Why hallucinations happen:**

1. **Training objective mismatch** — the model is trained to produce fluent, coherent text, not to produce accurate text. Fluency and accuracy are not the same thing.

2. **No factual grounding** — LLMs don't retrieve facts from a database; they generate text that matches statistical patterns from training data.

3. **Knowledge cutoff** — events after the training cutoff are unknown to the model, but it may still generate plausible-sounding responses.

4. **Long-tail knowledge** — rare facts appear rarely in training data; the model has weak signal and is more likely to confabulate.

```python
# Detecting potential hallucinations: confidence calibration
# Well-calibrated models: when they say 90% confident → actually correct 90% of time

# Mitigation 1: RAG (Retrieval-Augmented Generation)
def grounded_answer(question: str, knowledge_base) -> str:
    # Step 1: retrieve relevant facts
    relevant_docs = knowledge_base.search(question, top_k=5)
    
    # Step 2: answer ONLY from retrieved context
    prompt = f"""
    Answer the question using ONLY the information below.
    If the answer is not in the context, say "I don't know."
    
    Context:
    {relevant_docs}
    
    Question: {question}
    """
    return llm(prompt)

# Mitigation 2: Source citation requirement
prompt = """
Answer the question and cite your source for each claim.
If you are uncertain about a fact, say "I believe..." or "I'm not certain but...".
Never state uncertain information as fact.

Question: {question}
"""
```

**Hallucination rates (2024 benchmark — TruthfulQA):**
- GPT-4: ~59% truthful
- Claude 3: ~64% truthful
- GPT-3.5: ~47% truthful
- Best open-source models: ~55% truthful

These numbers are improving rapidly — but no model is hallucination-free.

---

## Deepfakes: The Synthetic Media Crisis

**Deepfakes** are AI-generated media — video, audio, images — that depict real people doing or saying things they never did.

**The technology progression:**

| Year | Capability |
|------|-----------|
| 2017 | Face-swap videos (poor quality, obvious artefacts) |
| 2019 | Real-time face-swap; voice cloning from 5 minutes of audio |
| 2021 | Full-body pose transfer; any face on any body |
| 2023 | Video generation from text (not yet mainstream) |
| 2024 | Photorealistic video + voice in seconds; Sora-level quality |

**Documented harms:**

1. **Non-consensual intimate imagery (NCII):** 96% of deepfake videos online are NCII targeting women. Victims lose employment, relationships, mental health.

2. **Political disinformation:** Deepfake of Ukrainian President Zelenskyy "surrendering" distributed on social media (2022). Quickly debunked but viewed millions of times.

3. **Financial fraud:** CEO voice clone used to authorise £200,000 wire transfer (UK, 2019). Estimated $25M lost to deepfake fraud in 2023.

4. **Eroding reality:** "Liar's dividend" — knowing deepfakes exist allows bad actors to deny authentic footage. Real evidence becomes deniable.

**Detection approaches:**

```python
# Deepfake detection signals (conceptual)
detection_features = {
    "facial_inconsistencies": [
        "eye blinking rate (deepfakes often blink unnaturally)",
        "facial boundary artefacts at hair/skin edges",
        "skin texture inconsistency across frames",
        "gaze direction not tracking correctly"
    ],
    "audio_visual_sync": [
        "lip movement doesn't match audio phonemes",
        "audio background noise inconsistent with video setting"
    ],
    "metadata": [
        "compression artefacts inconsistent with claimed source",
        "GAN fingerprints (spectral analysis of pixel statistics)"
    ]
}

# Current detection models: ~80-90% accuracy on lab datasets
# ~50-60% accuracy on in-the-wild deepfakes
# Arms race: detectors improve → generators improve to evade detection
```

**Defensive measures:**
- C2PA (Coalition for Content Provenance and Authenticity) — digital watermarking standard
- Content credentials embedded at capture time by cameras and devices
- Adobe, Microsoft, Google, Sony all implementing C2PA

---

## Accountability: Who Is Responsible?

When an AI system causes harm, who is liable?

```
Patient harmed by AI diagnosis
         │
    Who's responsible?
         │
    ┌────┴───────────────────────────┐
    │                                │
Hospital (deployed it)   AI Company (built it)
         │                          │
    Did they validate       Was the training data
    it for this use case?   representative?
    Did they get consent?   Did they document limits?
         │                          │
    Doctor (used it)         Data labellers
                             (who labelled training data?)
```

**The EU AI Act (2024)** — the world's first comprehensive AI law:

| Risk Level | Examples | Requirements |
|-----------|---------|-------------|
| **Unacceptable** | Social scoring, real-time biometric surveillance | **Banned** |
| **High** | Medical AI, credit scoring, recruitment AI, CCTV | Conformity assessment, human oversight, transparency |
| **Limited** | Chatbots | Must disclose AI nature |
| **Minimal** | Spam filters, AI video games | No requirements |

---

## Building Ethically: A Framework

```python
# Ethical AI checklist (before deployment)

ETHICAL_CHECKLIST = {
    "fairness": [
        "Audit model performance across demographic groups",
        "Document any disparate impact",
        "Consider whether the use case is appropriate at all",
    ],
    "transparency": [
        "Document training data sources and known biases",
        "Provide explanations for consequential decisions",
        "Disclose when users are interacting with AI",
    ],
    "privacy": [
        "Collect minimum necessary data",
        "Obtain informed consent for AI use",
        "Enable data deletion (right to erasure)",
    ],
    "accountability": [
        "Designate responsible AI owner",
        "Establish incident response process",
        "Create feedback channel for affected individuals",
    ],
    "robustness": [
        "Test on distribution shifts (out-of-domain inputs)",
        "Monitor for performance degradation in production",
        "Define human override mechanism",
    ]
}

for category, checks in ETHICAL_CHECKLIST.items():
    print(f"\n[{category.upper()}]")
    for check in checks:
        print(f"  ☐ {check}")
```

---

## Summary

| Issue | Root Cause | Mitigation |
|-------|-----------|-----------|
| Algorithmic bias | Biased training data; proxy variables | Diverse data; fairness auditing; human review |
| Hallucinations | Training objective ≠ accuracy | RAG; source citation; uncertainty quantification |
| Deepfakes | Generative model capability | C2PA watermarking; media literacy; detection tools |
| Lack of accountability | No clear legal framework | EU AI Act; internal governance; impact assessments |

---

## Further Reading

- [Atlas of AI — Kate Crawford](https://katecrawford.net/)
- [Algorithmic Justice League](https://www.ajl.org/)
- [EU AI Act Full Text](https://artificialintelligenceact.eu/)
- [Partnership on AI — Responsible AI Practices](https://partnershiponai.org/)
- [Deepfake Detection Challenge](https://ai.facebook.com/datasets/dfdc/)
