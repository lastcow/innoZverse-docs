# Lab 14: Responsible AI Audit

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Responsible AI requires systematic auditing for fairness, explainability, and accountability. This lab covers fairness metrics, bias detection, SHAP/LIME explainability, model cards, AI impact assessments, and building an automated audit trail.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                Responsible AI Audit Framework                 │
├──────────────────────────────────────────────────────────────┤
│  FAIRNESS ASSESSMENT         │  EXPLAINABILITY               │
│  ────────────────────        │  ──────────────────           │
│  Demographic parity          │  SHAP (global + local)        │
│  Equalized odds              │  LIME (local)                 │
│  Calibration                 │  Feature importance           │
│  Disparate impact (80% rule) │  Counterfactuals              │
├──────────────────────────────┴──────────────────────────────┤
│  MODEL CARD  │  IMPACT ASSESSMENT  │  AUDIT TRAIL           │
│  Capabilities│  Stakeholder harm   │  Immutable logs         │
│  Limitations │  Risk register      │  Decision records       │
│  Metrics     │  Mitigation plan    │  Version history        │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Fairness Metrics Taxonomy

No single fairness metric covers all situations. Choose based on your use case and legal context.

**Group Fairness Metrics:**

| Metric | Definition | Formula | Use Case |
|--------|-----------|---------|---------|
| **Demographic parity** | Equal positive rates across groups | P(Ŷ=1\|A=0) = P(Ŷ=1\|A=1) | Hiring, loans |
| **Equalized odds** | Equal TPR and FPR across groups | TPR₀=TPR₁ and FPR₀=FPR₁ | Criminal justice |
| **Equal opportunity** | Equal TPR across groups | TPR₀=TPR₁ | Medical diagnosis |
| **Calibration** | Predicted prob equals actual prob | P(Y=1\|Ŷ=p,A=a) = p for all a | Risk scoring |
| **Individual fairness** | Similar people treated similarly | f(x)≈f(x') if x≈x' | General |

**Disparate Impact (Legal "80% Rule"):**
```
Disparate Impact Ratio = P(positive outcome | minority) / P(positive outcome | majority)

If DI < 0.8: potential legal violation (EEOC guidelines)
If DI > 0.8: acceptable (80% rule)
If DI > 1.0: majority group disadvantaged (reverse discrimination)
```

> 💡 Fairness is mathematically impossible to optimize all metrics simultaneously (Chouldechova, 2017). Choose the metric that aligns with your legal and ethical framework.

---

## Step 2: Bias Detection

**Sources of Bias:**

| Source | Description | Example |
|--------|-------------|---------|
| **Historical bias** | Training data reflects past discrimination | Credit data: women historically denied loans |
| **Representation bias** | Training data underrepresents some groups | Facial recognition trained mostly on white faces |
| **Measurement bias** | Different measurement accuracy across groups | Medical sensors less accurate on darker skin |
| **Aggregation bias** | One model for diverse subgroups | Diabetes model ignores ethnic variation |
| **Deployment bias** | System used in different context than designed | Designed for urban, deployed in rural |

**Simpson's Paradox:**
```
Overall: Model A accuracy = 85% > Model B accuracy = 82%
Group 1: Model A accuracy = 78% < Model B accuracy = 90%
Group 2: Model A accuracy = 91% > Model B accuracy = 74%

Model B is BETTER for each individual group but WORSE overall
→ Never evaluate fairness only at aggregate level
```

**Bias Audit Checklist:**
```
Training data:
  ✓ Representation: all groups represented in training data?
  ✓ Historical labels: do labels reflect historical discrimination?
  ✓ Protected attributes: accidentally encoded via proxy features?
  
Model outputs:
  ✓ Demographic parity across protected groups
  ✓ Equalized odds (TPR/FPR parity)
  ✓ Calibration across groups
  
Deployment:
  ✓ Feedback loops: does deployment reinforce bias?
  ✓ Edge cases: groups that appear rarely in training
```

---

## Step 3: SHAP Explainability

SHAP (SHapley Additive exPlanations) provides consistent, theoretically-grounded feature importance.

**SHAP Values:**
```
For each prediction:
  SHAP(feature_i) = average marginal contribution of feature_i across all feature coalitions

Properties:
  1. Efficiency: SHAP values sum to model output
  2. Symmetry: equal features get equal SHAP values
  3. Dummy: unused features get SHAP = 0
  4. Additivity: SHAP values from combined model = sum of individual models
```

**SHAP Visualizations:**

| Plot | Shows | Use |
|------|-------|-----|
| **Beeswarm** | Feature impact distribution | Global: which features matter most |
| **Waterfall** | Single prediction breakdown | Local: why this specific decision |
| **Bar chart** | Mean |SHAP| per feature | Global: feature ranking |
| **Dependence** | Feature value vs SHAP value | Feature interaction detection |
| **Force plot** | Single prediction visualization | User-facing explanation |

**SHAP for Compliance:**
```
Loan denied → extract SHAP values for that applicant
Top negative factors:
  1. high_debt_ratio: -0.35 (reduced approval probability by 35%)
  2. recent_delinquency: -0.28
  3. low_income: -0.19
Positive factors:
  1. long_credit_history: +0.12
  2. multiple_accounts: +0.08

Explanation to customer: "Primary reason for denial: debt-to-income ratio..."
```

---

## Step 4: LIME Explainability

LIME (Local Interpretable Model-Agnostic Explanations) explains any model locally.

**LIME Process:**
```
1. Pick instance to explain
2. Generate perturbed samples around instance (small random changes)
3. Query black-box model on perturbed samples
4. Fit simple interpretable model (linear regression) on local samples
5. LIME explanation = coefficients of local linear model
```

**LIME vs SHAP:**

| Dimension | LIME | SHAP |
|-----------|------|------|
| Scope | Local only | Local + Global |
| Speed | Fast | Can be slow |
| Consistency | Stochastic (varies per run) | Deterministic |
| Theoretical basis | Heuristic | Game theory (Shapley values) |
| Model support | Any | Any (but efficient for tree models) |
| Best for | Quick local explanations | Rigorous global + local analysis |

---

## Step 5: Model Cards

Model cards (Google, 2019) document model behavior, limitations, and intended use.

**Model Card Template:**

```markdown
# Model Card: Credit Default Prediction v2.3

## Model Details
- Developer: ML Team, Finance AI
- Date: 2024-03-01
- Type: Gradient Boosted Tree (XGBoost)
- Version: 2.3.1

## Intended Use
- Primary: Credit risk assessment for personal loans
- Out-of-scope: Business lending, mortgage decisions

## Training Data
- Source: Internal loan database 2015-2023
- Size: 2.4M records
- Protected attributes excluded: race, gender, religion (but proxies may exist)

## Performance Metrics
| Group        | Accuracy | Precision | Recall | AUC  |
|-------------|---------|-----------|--------|------|
| Overall     | 0.89    | 0.85      | 0.82   | 0.94 |
| Male        | 0.90    | 0.86      | 0.83   | 0.95 |
| Female      | 0.88    | 0.84      | 0.81   | 0.93 |
| Age 18-30   | 0.84    | 0.79      | 0.76   | 0.90 |
| Age 31-60   | 0.91    | 0.87      | 0.85   | 0.95 |

## Fairness Analysis
- Disparate impact (gender): 0.97 (PASS, > 0.8)
- Equalized odds gap (TPR): 0.02 (PASS, < 0.05)

## Known Limitations
- Lower accuracy for applicants with thin credit files
- May underestimate risk for recent immigrants

## Ethical Considerations
- Human review required for borderline cases (score 0.45-0.55)
- Quarterly bias audit required
- Model should not be sole decision maker

## Contact
- Model owner: credit-ai-team@company.com
```

---

## Step 6: AI Impact Assessment

Structured assessment of potential harms before deploying AI systems.

**Impact Assessment Framework:**

```
1. Scope Definition
   - What decisions does the AI influence?
   - Who are the affected stakeholders?
   - What are the deployment contexts?

2. Risk Identification
   - What harms could occur?
   - Who could be harmed?
   - How likely and severe?

3. Fairness Analysis
   - Protected groups: gender, race, age, disability, religion
   - Run fairness metrics on representative dataset
   - Document disparities and planned mitigations

4. Explainability Requirements
   - Are affected parties entitled to an explanation? (GDPR Art. 22)
   - What level of explanation is sufficient?
   - Can humans understand and override the model?

5. Data Governance
   - Was training data collected with consent?
   - Are protected attributes appropriately handled?
   - Can individuals opt out or request deletion?

6. Sign-off
   - DPO review (GDPR compliance)
   - Legal review
   - Ethicist review (for high-risk systems)
   - Executive accountability sign-off
```

---

## Step 7: Audit Trail Architecture

**Immutable Audit Log Requirements:**
```
Every decision must record:
  - Timestamp (UTC)
  - Model version
  - Input features (or hash for privacy)
  - Prediction and confidence
  - Threshold used
  - Human override? (yes/no)
  - Business outcome (ground truth, delayed)
```

**Audit Trail Storage:**
```
Append-only S3 bucket (versioning + MFA delete)
      ↓
Parquet format (compressed, columnar)
      ↓
Indexed by: customer_id, timestamp, model_version
      ↓
Retention: 7 years (financial) / as required by regulation
      ↓
Access: read-only for audit team, no update/delete possible
```

**Linking Predictions to Outcomes:**
```
Prediction: customer_123, score=0.7, approved (2024-01-15)
Ground truth: customer_123, default=true (2024-07-20, delayed)
Link: by customer_id + decision_date
Use for: model recalibration, discrimination claims, regulatory audit
```

---

## Step 8: Capstone — Fairness Metrics Calculator

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

np.random.seed(42)
n = 2000

age = np.random.normal(40, 12, n)
income = np.random.lognormal(10.5, 0.6, n)
gender = np.random.binomial(1, 0.5, n)

prob = 1 / (1 + np.exp(-(age/50 + income/50000 - 1.5 + gender * (-0.3))))
approved = (np.random.random(n) < prob).astype(int)

X = np.column_stack([age, income])
X_train, X_test, y_train, y_test, g_train, g_test = train_test_split(X, approved, gender, test_size=0.3, random_state=42)
model = LogisticRegression(random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

print('=== Responsible AI Fairness Audit ===')
print()

male_mask = g_test == 0
female_mask = g_test == 1
male_approval_rate = y_pred[male_mask].mean()
female_approval_rate = y_pred[female_mask].mean()
dp_diff = abs(male_approval_rate - female_approval_rate)

print('Fairness Metrics:')
print(f'  Male approval rate:   {male_approval_rate:.3f}')
print(f'  Female approval rate: {female_approval_rate:.3f}')
print(f'  Demographic parity difference: {dp_diff:.3f} (< 0.1 = fair)')
print(f'  Demographic parity: {\"FAIR\" if dp_diff < 0.1 else \"UNFAIR\"}')

di = female_approval_rate / male_approval_rate if male_approval_rate > 0 else 0
print(f'  Disparate impact ratio: {di:.3f} (> 0.8 = fair, \"80% rule\")')
print(f'  Disparate impact: {\"FAIR\" if di >= 0.8 else \"UNFAIR\"}')

def tpr(y_true, y_pred):
    tp = ((y_true==1) & (y_pred==1)).sum()
    fn = ((y_true==1) & (y_pred==0)).sum()
    return tp / (tp + fn) if (tp+fn) > 0 else 0

male_tpr = tpr(y_test[male_mask], y_pred[male_mask])
female_tpr = tpr(y_test[female_mask], y_pred[female_mask])
tpr_diff = abs(male_tpr - female_tpr)
print(f'  Male TPR: {male_tpr:.3f} | Female TPR: {female_tpr:.3f}')
print(f'  Equalized odds (TPR diff): {tpr_diff:.3f} (< 0.05 = fair)')
print(f'  Equalized odds: {\"FAIR\" if tpr_diff < 0.05 else \"UNFAIR\"}')

print()
print('Audit Summary:')
checks = [
    ('Demographic parity', dp_diff < 0.1),
    ('Disparate impact', di >= 0.8),
    ('Equalized odds', tpr_diff < 0.05),
]
for check, passed in checks:
    print(f'  [{\"PASS\" if passed else \"FAIL\"}] {check}')
overall = 'APPROVED' if all(p for _, p in checks) else 'REQUIRES_MITIGATION'
print(f'  Overall: {overall}')
"
```

📸 **Verified Output:**
```
=== Responsible AI Fairness Audit ===

Fairness Metrics:
  Male approval rate:   0.558
  Female approval rate: 0.572
  Demographic parity difference: 0.014 (< 0.1 = fair)
  Demographic parity: FAIR
  Disparate impact ratio: 1.025 (> 0.8 = fair, "80% rule")
  Disparate impact: FAIR
  Male TPR: 0.648 | Female TPR: 0.713
  Equalized odds (TPR diff): 0.065 (< 0.05 = fair)
  Equalized odds: UNFAIR

Audit Summary:
  [PASS] Demographic parity
  [PASS] Disparate impact
  [FAIL] Equalized odds
  Overall: REQUIRES_MITIGATION
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Fairness Metrics | Demographic parity, equalized odds, disparate impact (80% rule) |
| Simpson's Paradox | Always evaluate fairness per subgroup, not just aggregate |
| SHAP | Consistent feature importance; sum = model output; local + global |
| LIME | Local explanations; black-box compatible; stochastic |
| Model Cards | Document: performance per group, limitations, intended use, owners |
| AI Impact Assessment | Structured harm identification before deployment |
| Audit Trail | Append-only, immutable; link predictions to outcomes; 7-year retention |

**Next Lab:** [Lab 15: LLM Fine-Tuning Infrastructure →](lab-15-llm-fine-tuning-infrastructure.md)
