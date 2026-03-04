# Lab 12: AI in the Real World — Healthcare, Finance, Security Use Cases

## Objective

See how AI is deployed across industries today. By the end you will understand:

- Concrete AI applications in healthcare, finance, and cybersecurity
- The gap between research benchmarks and production realities
- Key failure modes and why responsible deployment matters
- Career paths and opportunity areas in applied AI

---

## Healthcare: AI as a Diagnostic Tool

### Medical Imaging

AI has reached or exceeded radiologist-level accuracy on several imaging tasks:

| Task | Model | Performance | vs. Human |
|------|-------|-------------|-----------|
| Diabetic retinopathy screening | Google DeepMind | 94.5% AUC | Comparable |
| Lung cancer detection (CT) | Google Healthcare AI | Surpasses 6/6 radiologists | Better |
| Breast cancer screening (mammography) | DeepMind | 11.5% fewer false positives | Better |
| Skin cancer classification | Stanford CNN | Dermatologist-level on 21 conditions | Comparable |

```python
# Conceptual: medical image classifier using transfer learning
import torchvision.models as models
import torch.nn as nn

class ChestXRayClassifier(nn.Module):
    """Classify chest X-rays into 14 pathologies (CheXNet architecture)"""

    def __init__(self, num_classes=14):
        super().__init__()
        # DenseNet-121 pre-trained on ImageNet
        self.densenet = models.densenet121(pretrained=True)

        # Replace final layer for multi-label classification
        num_features = self.densenet.classifier.in_features
        self.densenet.classifier = nn.Sequential(
            nn.Linear(num_features, num_classes),
            nn.Sigmoid()    # multi-label: each class independent 0-1 probability
        )

    def forward(self, x):
        return self.densenet(x)

# Output: [0.92, 0.03, 0.87, ...]
# Labels: [Atelectasis, Cardiomegaly, Effusion, ...]
# Radiologist reviews AI flags — AI is the triage, human is the decision
```

### Drug Discovery

DeepMind's **AlphaFold 2** (2020) solved the 50-year protein folding problem — predicting a protein's 3D structure from its amino acid sequence. This matters because protein structure determines function and therefore drug targets.

- 200 million protein structures predicted (vs. ~150,000 known experimentally)
- Used in research against malaria, Parkinson's, antibiotic resistance
- Nobel Prize in Chemistry awarded to Demis Hassabis (2024)

### Clinical Language Understanding

```python
# Clinical NLP: extract structured data from clinical notes
prompt = """
Extract the following from this clinical note and return JSON:
- diagnoses (list)
- medications (list with dosage)
- lab values (dict)
- follow_up_required (boolean)

Note: Patient presents with T2DM poorly controlled (HbA1c 9.2%). 
Current medications: Metformin 1000mg BD, Empagliflozin 10mg OD. 
Starting Ozempic 0.25mg weekly. Follow up in 3 months for repeat HbA1c.
"""
# AI extracts structured data from unstructured clinical text
# Feeds into EHR systems, billing, population health dashboards
```

---

## Finance: AI in Markets, Risk, and Fraud

### Algorithmic Trading

Hedge funds like Renaissance Technologies, Two Sigma, and D.E. Shaw have used ML for decades. Modern approaches:

```python
import numpy as np

# Feature engineering for stock price prediction
def build_features(price_history: np.ndarray, volume: np.ndarray) -> np.ndarray:
    """Technical indicators as ML features"""
    features = {}

    # Moving averages
    features['sma_5']  = np.convolve(price_history, np.ones(5)/5,  mode='valid')[-1]
    features['sma_20'] = np.convolve(price_history, np.ones(20)/20, mode='valid')[-1]

    # Momentum
    features['roc_5']  = (price_history[-1] - price_history[-6])  / price_history[-6]
    features['roc_20'] = (price_history[-1] - price_history[-21]) / price_history[-21]

    # Volatility
    returns = np.diff(np.log(price_history[-21:]))
    features['volatility_20'] = returns.std() * np.sqrt(252)

    # Volume ratio
    features['volume_ratio'] = volume[-1] / volume[-20:].mean()

    return np.array(list(features.values()))

# These features feed into gradient boosting, LSTM, or Transformer models
# Predicting: direction (up/down), magnitude, or optimal position size
```

### Credit Scoring

Traditional credit scoring (FICO) uses 5 variables. ML uses thousands:

- **Traditional features:** payment history, credit utilisation, length of history
- **Alternative features:** bank transaction patterns, employment history, education, social connections

**Regulatory concern:** Alternative features can be proxies for protected characteristics (race, gender). Regulators in UK (FCA), EU (ECB), and US (CFPB) require explainability for credit decisions.

```python
# SHAP: explain why a credit application was declined
import shap

explainer = shap.TreeExplainer(credit_model)
shap_values = explainer.shap_values(applicant_features)

# Output: which features pushed the score up or down
# "Your application was declined because:
#  - Short credit history: -45 points
#  - High credit utilisation (82%): -38 points
#  - Recent missed payment: -52 points"
```

### Fraud Detection

Payment fraud detection must operate at millisecond speed with ~0.1% false positive rate (or customers complain):

```python
# Real-time fraud scoring (conceptual)
def score_transaction(transaction: dict) -> float:
    """Return fraud probability 0-1"""
    features = extract_features(transaction)
    # Features include:
    # - Transaction amount vs. historical average
    # - Geographic distance from last transaction
    # - Time since last transaction  
    # - Merchant category risk score
    # - Device fingerprint match
    # - Velocity: transactions in last hour/day
    
    score = fraud_model.predict_proba([features])[0][1]
    
    if score > 0.95:   block_transaction()
    elif score > 0.7:  request_authentication()
    else:              approve_transaction()
    
    return score
```

Visa processes 65,000+ transactions per second — each scored by ML in <100ms.

---

## Cybersecurity: AI Attacks and Defences

### Threat Detection

```python
# Network anomaly detection using Isolation Forest
from sklearn.ensemble import IsolationForest
import pandas as pd

# Features: network packet statistics
features = pd.DataFrame({
    'bytes_sent':    [1200, 1100, 5_000_000, 1300],  # 3rd = suspicious
    'packet_count':  [12,   11,   45000,    13],
    'unique_dests':  [3,    2,    847,      4],
    'duration_sec':  [2.1,  1.8,  300.0,   2.3],
})

# Isolation Forest: anomalies are easier to isolate (shorter path in tree)
model = IsolationForest(contamination=0.01, random_state=42)
model.fit(features)
predictions = model.predict(features)
# -1 = anomaly, 1 = normal
# Row 3 (index 2): flagged as anomaly — potential data exfiltration
```

### AI-Generated Malware (The Threat)

LLMs have lowered the barrier to creating sophisticated malware:

- **2023:** Researchers demonstrated GPT-4 writing functional phishing emails, polymorphic code, and social engineering scripts
- **WormGPT/FraudGPT:** Uncensored LLMs sold on darknet forums specifically for cybercrime
- **AI-generated spear phishing:** Personalised to target's LinkedIn, reducing detection by humans

### Deepfakes and Social Engineering

**Deepfake audio attack (2019, UK):** Criminals used AI voice cloning to impersonate a German executive's voice on a phone call, directing a UK employee to transfer €220,000. The voice was indistinguishable.

**Scale of the problem (2024):**
- 25 million deepfake video/audio pieces circulating online
- 3,000% increase in deepfake fraud attempts (2023→2024)
- AI-generated fake IDs passing document verification systems

### AI for Defence

```python
# LLM-assisted code security review
code_review_prompt = """
Review this code for security vulnerabilities. 
For each vulnerability:
1. Name the vulnerability type (e.g., SQL injection, XSS)
2. Identify the specific line(s)
3. Explain the attack vector
4. Provide the remediated code

Code to review:
{code}
"""

# Deployed by:
# - GitHub Advanced Security (CodeQL + LLM explanations)
# - Snyk Code (AI-powered SAST)
# - Amazon CodeGuru (automated code review)
```

---

## Legal, Education, and Creative Industries

### Legal

- **Contract review:** Kira Systems, Harvey AI — review 1,000-page contracts in minutes
- **Legal research:** Lexis+ AI, Westlaw AI — cite cases, find precedents
- **E-discovery:** AI reviews millions of documents for relevant evidence

### Education

- **Khan Academy Khanmigo** — personalised Socratic tutor (never just gives answers)
- **Duolingo Max** — AI conversation partner for language learning
- **GitHub Copilot** — used by 1.3M developers; 55% of code in some repos is AI-generated

### Creative Industries

| Tool | Use Case | Controversy |
|------|----------|-------------|
| GitHub Copilot | Code generation | Trained on GPL code without licence compliance |
| Midjourney | Image generation | Artists sue over training data |
| Suno/Udio | Music generation | Record labels sue for copyright |
| ElevenLabs | Voice cloning | Voice actors sue; used for fraud |

---

## The Production Reality Gap

Research benchmarks vs. production systems:

| Research | Production Reality |
|----------|-------------------|
| 95% accuracy | 95% accuracy on test set, 73% on real users (distribution shift) |
| English only | Degrades significantly for non-English speakers |
| Clean images | Struggles with phone photos: blur, glare, unusual angles |
| Single task | Users ask off-topic questions constantly |
| Offline batch | Must respond in <500ms at 10,000 requests/second |

The last mile from "works in research" to "works reliably in production" is where most AI projects fail.

---

## Career Paths in Applied AI

| Role | Skills | Typical Entry |
|------|--------|--------------|
| ML Engineer | Python, PyTorch/TensorFlow, MLOps, cloud | CS degree or bootcamp + portfolio |
| Data Scientist | Python, statistics, SQL, business insight | Stats/CS degree |
| AI Product Manager | Domain expertise + AI literacy | PM experience + AI upskilling |
| AI Safety Researcher | Deep learning theory, philosophy, formal methods | PhD level |
| Prompt Engineer | LLM expertise, domain knowledge | Emerging role; no formal path |
| MLOps Engineer | Docker, Kubernetes, monitoring, CI/CD | DevOps → ML |

---

## Further Reading

- [AlphaFold and the Protein Folding Revolution](https://www.nature.com/articles/s41586-021-03819-2)
- [AI in Finance — BIS Working Papers](https://www.bis.org/publ/work1014.htm)
- [AI and Cybersecurity — ENISA Report](https://www.enisa.europa.eu/publications/artificial-intelligence-cybersecurity-challenges)
- [The State of AI Report 2024](https://www.stateof.ai/)
