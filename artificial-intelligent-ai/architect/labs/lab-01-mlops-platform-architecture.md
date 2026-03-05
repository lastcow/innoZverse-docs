# Lab 01: MLOps Platform Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

MLOps (Machine Learning Operations) bridges the gap between model development and production systems. This lab covers the MLOps maturity model, end-to-end ML pipeline architecture, experiment tracking, model registry patterns, and CI/CD for ML systems.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MLOps Platform                           │
├─────────────────────────────────────────────────────────────┤
│  Data Layer        │  Training Layer  │  Serving Layer      │
│  ─────────────     │  ──────────────  │  ─────────────      │
│  Feature Store     │  Experiment Track│  Model Server        │
│  Data Catalog      │  Distributed Train│  A/B Testing        │
│  Data Validation   │  HPO             │  Canary Deploy       │
├─────────────────────────────────────────────────────────────┤
│  Model Registry → Staging → Production → Archived          │
├─────────────────────────────────────────────────────────────┤
│  CI/CD Pipeline → Build → Test → Deploy → Monitor          │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: MLOps Maturity Model

Understand the three maturity levels before designing any ML platform.

| Level | Name | Characteristics | Deployment Frequency |
|-------|------|-----------------|---------------------|
| **L0** | Manual | Jupyter notebooks, manual steps, no CI/CD | Monthly/quarterly |
| **L1** | ML Pipeline Automation | Automated retraining, model monitoring, pipeline orchestration | Weekly |
| **L2** | CI/CD Automation | Automated pipeline deployment, feature store, A/B testing | On-demand (hours) |

> 💡 Most enterprises start at L0-L1. The jump to L2 requires significant platform investment but delivers 10x faster iteration.

**L0 Pain Points:**
- Models live in notebooks, not production
- Reproducibility is near-impossible
- Manual retraining triggered by gut feeling
- No performance monitoring

**L2 Benefits:**
- New models deploy in hours, not weeks
- Automated drift detection triggers retraining
- Full audit trail for compliance
- Experiments reproducible across teams

---

## Step 2: ML Pipeline Stages

A production ML pipeline has six core stages:

```
Data Ingestion → Feature Engineering → Model Training
     ↓                                      ↓
Data Validation                    Model Evaluation
     ↓                                      ↓
Feature Store  ←─────────────── Model Registry
                                       ↓
                              Deployment + Monitoring
```

**Stage Details:**

| Stage | Purpose | Key Tools | Failure Mode |
|-------|---------|-----------|-------------|
| Data Ingestion | Collect raw data | Kafka, Airflow, Spark | Schema drift, data gaps |
| Data Validation | Check data quality | Great Expectations, Deequ | Silent corruption |
| Feature Engineering | Transform features | Feast, Tecton | Training-serving skew |
| Model Training | Fit model | sklearn, PyTorch, TF | Underfitting/overfitting |
| Model Evaluation | Measure performance | MLflow, custom metrics | Wrong evaluation split |
| Deployment | Serve predictions | FastAPI, BentoML, KServe | Latency regression |
| Monitoring | Detect drift | Evidently, Prometheus | Silent degradation |

> 💡 Training-serving skew is the #1 production ML bug. Your feature store must serve identical features at training and inference time.

---

## Step 3: Experiment Tracking with MLflow

MLflow provides four components: Tracking, Projects, Models, and Registry.

**Tracking Server Architecture:**
```
ML Engineer → MLflow Client → Tracking Server → Artifact Store (S3/GCS)
                                    ↓
                              Metadata DB (PostgreSQL)
                                    ↓
                              MLflow UI (port 5000)
```

**Experiment Hierarchy:**
```
Experiment: "credit_scoring_v2"
├── Run: run_001 (C=0.1, accuracy=0.865, status=FINISHED)
├── Run: run_002 (C=1.0, accuracy=0.855, status=FINISHED)
└── Run: run_003 (C=10.0, accuracy=0.855, status=FINISHED)
```

**Key MLflow Concepts:**

```python
# Log parameters, metrics, and artifacts
mlflow.log_param("learning_rate", 0.01)
mlflow.log_metric("accuracy", 0.865)
mlflow.log_artifact("confusion_matrix.png")
mlflow.sklearn.log_model(model, "model")
```

> 💡 Always log: (1) git commit hash, (2) data version, (3) all hyperparameters. This is the minimum for reproducibility.

---

## Step 4: Model Registry Workflow

The model registry tracks model lifecycle from development to retirement.

```
Development → Staging → Production → Archived
     ↑                      ↓
  New model         Champion/Challenger
  registered        A/B testing
```

**Registry States:**

| State | Description | Gate Criteria |
|-------|-------------|---------------|
| **Registered** | Model exists in registry | Successfully logged in MLflow |
| **Staging** | Undergoing validation | Passes unit tests, performance threshold |
| **Production** | Serving live traffic | Canary test passed, stakeholder approval |
| **Archived** | Retired/superseded | Replaced by better model |

**Promotion Checklist:**
- [ ] Performance ≥ baseline on holdout set
- [ ] Fairness metrics within acceptable range
- [ ] Latency P99 < SLO threshold
- [ ] Security scan passed
- [ ] Explainability documentation complete

---

## Step 5: CI/CD for ML Pipelines

ML CI/CD differs from software CI/CD — you're testing data and models, not just code.

```
Code Push → GitHub/GitLab
     ↓
CI Pipeline:
  ├── Unit tests (data schema, feature logic)
  ├── Integration tests (pipeline end-to-end)
  ├── Model training (on subset)
  ├── Model evaluation (vs baseline)
  └── Model validation (performance gates)
     ↓
CD Pipeline:
  ├── Build model serving container
  ├── Deploy to staging environment
  ├── Run smoke tests
  ├── Canary deployment (5% traffic)
  └── Full production rollout
```

**What to Test in ML CI:**

| Test Type | What to Check | Example |
|-----------|---------------|---------|
| Data tests | Schema, distributions, nulls | `assert df['age'].between(0,120).all()` |
| Feature tests | Value ranges, cardinality | Feature store output validation |
| Model tests | Performance > threshold | `assert accuracy > 0.80` |
| Integration tests | Pipeline end-to-end | Run full pipeline on 1% sample |

> 💡 Use `pytest` + `great_expectations` for data tests. A broken data pipeline will silently degrade your model.

---

## Step 6: Feature Store Architecture

Feature stores solve training-serving skew by centralizing feature computation.

```
Offline Store (batch features):          Online Store (real-time features):
  Raw Data → Feature Pipeline            Feature Pipeline → Redis/DynamoDB
       ↓                                       ↓
  Parquet/Delta Lake                    Sub-millisecond lookup
       ↓                                       ↓
  Training features                     Serving features
       └──────────────────┬─────────────────┘
                     Feature Registry
                   (metadata, lineage)
```

**Feature Store Components:**

| Component | Technology Options | Purpose |
|-----------|-------------------|---------|
| Feature pipeline | Spark, Flink, dbt | Compute features at scale |
| Offline store | S3 + Parquet, BigQuery | Historical features for training |
| Online store | Redis, DynamoDB, Bigtable | Low-latency feature serving |
| Registry | Feast, Tecton, Hopsworks | Feature discovery and versioning |

---

## Step 7: MLOps Platform Design Patterns

**Pattern 1: Scheduled Retraining**
```
Cron (weekly) → Data pipeline → Training → Evaluation
                                               ↓
                                        Pass gates? → Deploy
                                               ↓
                                          Fail → Alert + human review
```

**Pattern 2: Triggered Retraining (Reactive)**
```
Monitor drift → Threshold exceeded → Alert
                                        ↓
                                  Auto-trigger retrain OR
                                  Human approval required
```

**Pattern 3: Continuous Training (Advanced)**
```
Streaming data → Online learning OR frequent batch retraining
                            ↓
                     Shadow deployment → Compare vs live model
                            ↓
                     Auto-promote if better
```

> 💡 Start with scheduled retraining (simplest). Move to triggered when you have drift monitoring. Only implement continuous training if your data truly changes that fast.

---

## Step 8: Capstone — Design MLOps Platform for Financial Services

**Scenario:** You're the AI Architect at a bank deploying a credit scoring model used for 50,000 loan decisions per day. Design the MLOps platform.

**Requirements:**
- Regulatory compliance (Basel III, GDPR, ECOA)
- Model explainability for every decision
- Bias monitoring across protected groups
- Full audit trail for 7 years
- Retraining SLA: < 24 hours when drift detected

**Architecture Exercise:**

```python
# Run this to simulate the experiment tracking component
```

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split

X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

experiments = {}
for C in [0.1, 1.0, 10.0]:
    model = LogisticRegression(C=C, random_state=42)
    model.fit(X_train, y_train)
    acc = model.score(X_test, y_test)
    experiments[f'run_C{C}'] = {'C': C, 'accuracy': round(acc, 4), 'n_features': 20, 'status': 'FINISHED'}

print('=== MLOps Experiment Tracking (MLflow-style) ===')
print(f'Experiment: classification_v1')
for run, metrics in experiments.items():
    print(f'  Run: {run} | accuracy={metrics[\"accuracy\"]} | C={metrics[\"C\"]} | status={metrics[\"status\"]}')

best = max(experiments.items(), key=lambda x: x[1]['accuracy'])
print(f'Best run: {best[0]} | accuracy={best[1][\"accuracy\"]}')

stages = {'staging': best[0], 'production': None, 'archived': []}
print(f'Model Registry: staging={stages[\"staging\"]} -> promote to production')
stages['production'] = stages['staging']
print(f'Model Registry: production={stages[\"production\"]} (deployed)')

pipeline = ['data_validation', 'feature_engineering', 'model_training', 'model_evaluation', 'model_registry', 'deployment', 'monitoring']
print('ML Pipeline stages:', ' -> '.join(pipeline))
"
```

📸 **Verified Output:**
```
=== MLOps Experiment Tracking (MLflow-style) ===
Experiment: classification_v1
  Run: run_C0.1 | accuracy=0.865 | C=0.1 | status=FINISHED
  Run: run_C1.0 | accuracy=0.855 | C=1.0 | status=FINISHED
  Run: run_C10.0 | accuracy=0.855 | C=10.0 | status=FINISHED
Best run: run_C0.1 | accuracy=0.865
Model Registry: staging=run_C0.1 -> promote to production
Model Registry: production=run_C0.1 (deployed)
ML Pipeline stages: data_validation -> feature_engineering -> model_training -> model_evaluation -> model_registry -> deployment -> monitoring
```

**Platform Design Decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration | Airflow/Kubeflow Pipelines | Enterprise support, audit trail |
| Experiment tracking | MLflow on-prem | Data sovereignty requirements |
| Feature store | Feast + Redis | Open source, GDPR compliant |
| Model serving | KServe on K8s | Scalable, explainability hooks |
| Monitoring | Evidently + Prometheus | Drift detection + alerting |
| Audit storage | S3 + Glacier | 7-year retention, cost-optimized |

---

## Summary

| Concept | Key Points |
|---------|-----------|
| MLOps Maturity | L0 (manual) → L1 (automated pipeline) → L2 (CI/CD automation) |
| Pipeline Stages | Data → Feature → Train → Evaluate → Registry → Deploy → Monitor |
| Experiment Tracking | Log params + metrics + artifacts; enable reproducibility |
| Model Registry | Staging → Production → Archived lifecycle with gates |
| CI/CD for ML | Test data + models + code; canary deployments |
| Feature Store | Offline (training) + Online (serving) = eliminate training-serving skew |
| Retraining Triggers | Schedule (simple) → Drift-triggered (reactive) → Continuous (advanced) |

**Next Lab:** [Lab 02: Model Serving at Scale →](lab-02-model-serving-at-scale.md)
