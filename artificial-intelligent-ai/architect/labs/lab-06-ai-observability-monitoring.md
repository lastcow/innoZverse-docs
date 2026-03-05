# Lab 06: AI Observability & Monitoring

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

ML models silently degrade in production. This lab covers the complete ML observability stack: data drift detection (KS test, PSI), concept drift, model performance monitoring, feature importance tracking, outlier detection, and production monitoring architectures.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                 ML Observability Stack                        │
├──────────────────────────────────────────────────────────────┤
│  Production Traffic → Feature Logging → Drift Pipeline       │
│       ↓                                      ↓               │
│  Prediction Store                      KS Test / PSI         │
│  Ground Truth (delayed)                Feature Drift Detect  │
│       ↓                                      ↓               │
│  Performance Metrics                   ALERT System          │
│  (Accuracy, F1, AUC)                  (PagerDuty / Slack)   │
├──────────────────────────────────────────────────────────────┤
│  Dashboards: Grafana + Evidently AI + Prometheus             │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Types of ML Model Degradation

**Silent Degradation is the Enemy:**
- Model accuracy drops but no error logs appear
- Business metrics worsen weeks later
- Root cause: data or concept drift

**Four Types of Drift:**

| Type | Definition | Detection Method | Frequency |
|------|-----------|-----------------|-----------|
| **Data drift** | Input distribution changed | KS test, PSI, JS divergence | Daily |
| **Concept drift** | P(Y\|X) relationship changed | Performance metrics monitoring | Weekly |
| **Label drift** | Output distribution changed | Output distribution monitoring | Daily |
| **Feature drift** | Individual feature statistics changed | Per-feature statistics | Daily |

**Examples:**
```
Data drift:    Customer ages used to be 25-45, now 18-65 (population shift)
Concept drift: Economic recession changes what "creditworthy" means
Label drift:   Fraud rate dropped from 2% to 0.5% (good or model failure?)
Feature drift: API change returns null for previously populated field
```

---

## Step 2: KS Test for Feature Drift

The Kolmogorov-Smirnov test compares two distributions without assuming normality.

**KS Test:**
```
H₀: reference and production distributions are the same
H₁: distributions differ significantly

Statistic: D = max|F_ref(x) - F_prod(x)|  (max CDF difference)
p-value < 0.05 → reject H₀ → DRIFT DETECTED
```

**Interpretation:**
```
p-value > 0.05:  No drift (distributions similar)
p-value < 0.05:  Drift detected (investigate)
p-value < 0.001: Severe drift (urgent action)
```

> 💡 KS test is powerful but sensitive to sample size. With N=100,000 samples, even tiny insignificant differences will have p < 0.05. Always combine p-value with KS statistic magnitude.

---

## Step 3: PSI (Population Stability Index)

PSI is the industry standard for monitoring data drift in credit scoring and finance.

**PSI Formula:**
```
PSI = Σ (actual% - expected%) × ln(actual% / expected%)

Thresholds:
  PSI < 0.1:   Stable (no action needed)
  0.1 ≤ PSI < 0.2: Monitor (investigate cause)
  PSI ≥ 0.2:   Retrain required (significant shift)
```

**PSI vs KS Test:**

| Metric | Sensitivity | Directionality | Industry Use |
|--------|------------|---------------|-------------|
| KS Test | High | Yes (which direction?) | General ML |
| PSI | Medium | No (magnitude only) | Finance/credit |
| JS Divergence | Medium | Symmetric | General ML |
| Wasserstein | High | Yes | Research |

---

## Step 4: Concept Drift Detection

Concept drift means the relationship between features and labels has changed.

**Detection Approaches:**

**1. Performance-based monitoring (most practical):**
```
Track rolling accuracy/F1/AUC over 7/14/30 day windows
Alert when: current_7day_accuracy < baseline * 0.95
```

**2. Statistical tests on predictions:**
```
Compare predicted score distribution: reference vs production
If PSI(predicted_scores) > 0.2 → possible concept drift
```

**3. Challenger model comparison:**
```
Periodically retrain on fresh data → compare vs champion
If challenger >> champion → concept drift has occurred
```

**ADWIN (Adaptive Windowing):**
```
Maintains adaptive window of recent samples
Detects change in mean → shrinks window after change point
Used in: streaming ML, online learning
```

---

## Step 5: Feature Importance Drift

Even without overall performance drop, individual feature importances can shift.

**Monitoring Feature Importances Over Time:**
```
Baseline:  feature_1=0.35, feature_2=0.28, feature_3=0.22...
Week 4:    feature_1=0.12, feature_2=0.45, feature_3=0.25...

feature_1 dropped from 35% → 12% importance → INVESTIGATE
Could mean: feature_1 data quality issue, API change, business change
```

**SHAP-based Drift:**
```
Store SHAP values for sample of production predictions
Track: mean |SHAP value| per feature over time
Alert: if any feature's mean |SHAP| changes > 30% vs baseline
```

---

## Step 6: Outlier Detection for ML Monitoring

Detect input samples that are far outside the training distribution.

**Methods:**

| Method | Type | Complexity | Best For |
|--------|------|-----------|---------|
| Z-score | Statistical | Low | Univariate, normal dist |
| Isolation Forest | ML | Medium | Multivariate, any dist |
| Autoencoder | Deep learning | High | High-dim, complex patterns |
| LOF | Distance-based | Medium | Local anomalies |
| OCSVM | SVM-based | Medium | Small datasets |

**Production Outlier Monitoring:**
```
Training data → fit Isolation Forest (contamination=0.01)
Production samples → score with trained model
If outlier_score < threshold → flag as OOD (out-of-distribution)
Don't serve predictions for OOD inputs OR serve with low confidence flag
```

---

## Step 7: Monitoring Architecture (Evidently + Grafana)

**Evidently AI Reports:**
```python
# Generate drift report
report = Report(metrics=[
    DataDriftPreset(),
    DataQualityPreset(),
    RegressionPreset(),  # or ClassificationPreset()
])
report.run(reference_data=ref_df, current_data=prod_df)
report.save_html("drift_report.html")
```

**Metrics Stack:**
```
ML Predictions → Kafka → Prediction Logger → PostgreSQL/ClickHouse
                                                    ↓
                              Evidently (batch reports, weekly)
                              Prometheus (real-time metrics)
                                    ↓
                              Grafana Dashboards
                              PagerDuty Alerts
```

**Shadow Mode for Safe Monitoring:**
```
Traffic → Production Model v1.0 (serves responses)
       ↘ Shadow Model v2.0 (logs predictions, NOT served)

Compare: v2.0 predictions vs v1.0 predictions on same inputs
If v2.0 better → safe to promote (no user impact during evaluation)
```

> 💡 Run every new model in shadow mode for at least 48 hours (covering weekday + weekend patterns) before canary promotion.

---

## Step 8: Capstone — Build Drift Detection System

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
from scipy import stats

np.random.seed(42)
n = 1000

ref_age = np.random.normal(35, 10, n)
ref_income = np.random.lognormal(10, 0.5, n)
ref_score = np.random.beta(2, 5, n)

prod_age = np.random.normal(38, 12, n)
prod_income = np.random.lognormal(10.3, 0.6, n)
prod_score = np.random.beta(2, 5, n)

print('=== Data Drift Detection (KS Test) ===')
features = [
    ('age', ref_age, prod_age),
    ('income', ref_income, prod_income),
    ('score', ref_score, prod_score),
]
for fname, ref, prod in features:
    ks_stat, p_value = stats.ks_2samp(ref, prod)
    drift = 'DRIFT DETECTED' if p_value < 0.05 else 'No drift'
    print(f'  {fname:8s}: KS_stat={ks_stat:.4f} p_value={p_value:.4f} -> {drift}')

def calc_psi(expected, actual, buckets=10):
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets+1))
    expected_pct = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    actual_pct = np.histogram(actual, bins=breakpoints)[0] / len(actual)
    eps = 1e-10
    psi = np.sum((actual_pct + eps - expected_pct - eps) * np.log((actual_pct + eps) / (expected_pct + eps)))
    return abs(psi)

print()
print('=== PSI (Population Stability Index) ===')
print('Threshold: PSI < 0.1 = stable | 0.1-0.2 = monitor | > 0.2 = retrain')
for fname, ref, prod in features:
    psi = calc_psi(ref, prod)
    level = 'STABLE' if psi < 0.1 else ('MONITOR' if psi < 0.2 else 'RETRAIN')
    print(f'  {fname:8s}: PSI={psi:.4f} -> {level}')
"
```

📸 **Verified Output:**
```
=== Data Drift Detection (KS Test) ===
  age     : KS_stat=0.1440 p_value=0.0000 -> DRIFT DETECTED
  income  : KS_stat=0.2000 p_value=0.0000 -> DRIFT DETECTED
  score   : KS_stat=0.0350 p_value=0.5729 -> No drift

=== PSI (Population Stability Index) ===
Threshold: PSI < 0.1 = stable | 0.1-0.2 = monitor | > 0.2 = retrain
  age     : PSI=0.1310 -> MONITOR
  income  : PSI=0.2438 -> RETRAIN
  score   : PSI=0.0152 -> STABLE
```

**Monitoring Action Matrix:**

| KS p-value | PSI | Action |
|-----------|-----|--------|
| > 0.05 | < 0.1 | ✅ No action |
| < 0.05 | 0.1-0.2 | ⚠️ Investigate root cause |
| < 0.01 | > 0.2 | 🚨 Trigger retraining pipeline |
| < 0.001 | > 0.25 | 🚨 Disable model, manual review |

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Data Drift | Input distribution changed; detect with KS test or PSI |
| Concept Drift | Y\|X relationship changed; detect with performance monitoring |
| KS Test | Non-parametric, p < 0.05 = drift; sensitive to sample size |
| PSI | Finance standard: <0.1=stable, 0.1-0.2=monitor, >0.2=retrain |
| Feature Importance Drift | Track SHAP values over time; sudden changes = investigate |
| Shadow Mode | New model runs on live traffic, no user impact, safest test |
| Monitoring Stack | Evidently (reports) + Prometheus (metrics) + Grafana (dashboards) |

**Next Lab:** [Lab 07: Federated Learning at Scale →](lab-07-federated-learning-at-scale.md)
