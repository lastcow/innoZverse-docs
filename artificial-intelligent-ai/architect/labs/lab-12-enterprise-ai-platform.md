# Lab 12: Enterprise AI Platform Design

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Designing an enterprise AI platform requires balancing self-service capabilities, governance, and infrastructure complexity. This lab covers complete platform architecture: data access, training, model registry, feature store, serving, and governance — with a build vs buy analysis.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Enterprise AI Platform                        │
├──────────────────────────────────────────────────────────────────┤
│  USER PERSONAS                                                   │
│  Data Scientist → Self-Service ML │ ML Engineer → Platform APIs │
│  Analyst → No-code tools          │ IT/Ops → Infrastructure     │
├──────────────────────────────────────────────────────────────────┤
│  DATA LAYER          │  TRAINING LAYER   │  GOVERNANCE LAYER    │
│  Feature Store       │  Compute Cluster  │  RBAC/IAM            │
│  Data Catalog        │  Experiment Track │  Audit Logging       │
│  Data Versioning     │  AutoML           │  Policy Engine       │
│  Lineage Tracking    │  HPO              │  Compliance Reports  │
├──────────────────────────────────────────────────────────────────┤
│  MODEL REGISTRY  ←→  SERVING LAYER  ←→  MONITORING LAYER       │
│  Versioning          Load Balancer       Drift Detection         │
│  Lifecycle Mgmt      A/B Testing         Performance Metrics     │
│  Approval Flows      Auto-scaling        Alerting                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Self-Service ML Platform Design

A self-service ML platform democratizes ML without requiring infrastructure expertise.

**User Experience Goals:**
```
Data Scientist can:
  - Start an experiment with 2 clicks
  - Access any approved dataset from catalog
  - Train on GPU without knowing Kubernetes
  - Deploy to staging with 1 command
  - Monitor model health on a dashboard

ML Engineer can:
  - Add new data sources through self-service
  - Configure autoscaling policies
  - Define governance guardrails
  - Manage platform resources
```

**Self-Service Layers:**

| Layer | Abstraction | Technology |
|-------|------------|-----------|
| Compute | Kubernetes abstraction | Kubeflow, SageMaker Studio |
| Storage | Managed feature store | Feast, Tecton |
| Experiments | Notebook → MLflow auto-track | JupyterHub + MLflow |
| Deployment | Model card + 1 button deploy | ArgoCD + KServe |
| Monitoring | Auto-generated dashboards | Grafana + Evidently |

---

## Step 2: Data Access Layer

**Data Catalog:**
```
Purpose: Data discovery, governance, lineage
Components:
  - Metadata catalog (what data exists, schema, owners)
  - Data lineage (how data was created, transformations)
  - Data quality metrics (freshness, completeness, accuracy)
  - Access control (who can access what)

Technology: Apache Atlas, DataHub, Collibra, Alation
```

**Data Access Tiers:**

| Tier | Data Type | Access Method | Latency | Cost |
|------|-----------|--------------|---------|------|
| Hot | Feature store, recent data | Redis, DynamoDB | < 1ms | High |
| Warm | Training data, last 90 days | S3 + DuckDB | < 1s | Medium |
| Cold | Historical data, archives | S3 Glacier | Minutes | Low |

**Training Data Governance:**
```
Data access request → Data steward approval
                        ↓
                    Data lineage recorded
                        ↓
                    Sensitive fields: PII masking
                        ↓
                    RBAC: ML team can read, not delete
                        ↓
                    Audit log: who accessed what, when
```

---

## Step 3: Training Infrastructure

**Compute Tiers:**

| Tier | Hardware | Use Case | Autoscale |
|------|---------|---------|----------|
| Interactive | CPU + small GPU | Notebooks, exploration | No (reserved) |
| Training | A100/H100 clusters | Model training | Yes (queue) |
| Hyperparameter tuning | A100 multi-GPU | HPO sweeps | Yes |
| Fine-tuning | A100 80GB | LLM fine-tuning | Limited |

**Job Scheduling:**
```
Training jobs → Queue (Volcano/Kueue on K8s)
             → Resource quotas (team gets N GPUs/month)
             → Priority scheduling (production > experiment)
             → Fair share among teams
             → Preemption for high-priority jobs
```

**Distributed Training Support:**
```
Single GPU:    PyTorch standard
Multi-GPU:     PyTorch DDP (data parallel)
Multi-Node:    PyTorch + NCCL + K8s training operator
Large models:  DeepSpeed ZeRO or Megatron-LM
```

---

## Step 4: Model Registry and Feature Store

**Model Registry Requirements:**
```
Core features:
  ✅ Model versioning (semantic versioning: 1.2.0)
  ✅ Metadata storage (metrics, parameters, lineage)
  ✅ Stage management (staging/production/archived)
  ✅ Approval workflows (manager sign-off for production)
  ✅ Artifact storage (weights, config, preprocessing)
  ✅ Deployment integration (push to serving layer)
  ✅ Lineage tracking (data version + code version → model version)
```

**Feature Store Architecture:**
```
                    ┌─────────────────────────────────┐
                    │         Feature Store            │
                    ├─────────────────┬───────────────┤
Batch Pipeline →    │  Offline Store  │  Online Store │ ← Real-time
(Spark/Airflow)     │  (S3/BigQuery)  │  (Redis)      │   Pipeline
                    │  Training data  │  Serving data │
                    └─────────────────┴───────────────┘
                              ↑ Point-in-time joins
                              ↑ Feature versioning
                              ↑ Lineage tracking
```

---

## Step 5: Serving Layer Architecture

**Multi-model Serving:**
```
Model Gateway (KServe / Seldon)
├── /v1/models/fraud_detection → FraudModel v2.1 (canary: v2.2 5%)
├── /v1/models/churn_predictor → ChurnModel v1.8 (production)
├── /v1/models/llm_assistant → Mistral-7B-Instruct v0.2 (shadow: Llama-3)
└── /v1/models/embeddings → BGE-M3 v1.5 (stable)
```

**Traffic Management:**
```
100% production → Model A v1.0
     ↓ (canary)
5% → Model A v2.0   [monitor error rate, latency, model quality]
     ↓ (success)
25% → Model A v2.0  [watch for 24h]
     ↓ (success)
100% → Model A v2.0 [complete rollout]
```

---

## Step 6: Governance Layer

**RBAC (Role-Based Access Control):**

| Role | Permissions |
|------|-----------|
| Data Scientist | Train experiments, view own models, read datasets |
| ML Engineer | Deploy to staging, manage model registry |
| ML Lead | Approve production deployments, manage team resources |
| Data Steward | Approve data access requests, manage catalog |
| Platform Admin | Full access, infrastructure management |

**Audit Trail Requirements:**
```
What to log:
  - Every training run (who, what data, what result)
  - Every model deployment (who, what model, when, to where)
  - Every prediction (for high-risk models)
  - Data access events
  - Model registry changes

Retention: 3-7 years (regulatory requirement)
Format: Immutable, tamper-evident (append-only logs)
```

**Model Governance Workflow:**
```
ML Scientist trains model → submit for review
                                ↓
                        Automated checks:
                          - Fairness metrics pass?
                          - Performance threshold met?
                          - Security scan clean?
                                ↓
                        Human review (ML Lead):
                          - Model card complete?
                          - Risk assessment done?
                                ↓
                        Approved → deploy to staging → production
```

---

## Step 7: Build vs Buy Analysis

**Platform Options Comparison:**

| Dimension | Build (Custom) | AWS SageMaker | GCP Vertex AI | Azure ML | Databricks |
|-----------|---------------|--------------|--------------|---------|-----------|
| **Cost/year** | $2M+ | $500K | $450K | $480K | $600K |
| **Time to value** | 18+ months | 2-3 months | 2-3 months | 2-3 months | 1-2 months |
| **Flexibility** | Maximum | Medium | Medium | Medium | High |
| **Vendor lock-in** | None | High | High | High | Medium |
| **Open source** | Full | Partial | Partial | Partial | Partial |
| **Multi-cloud** | ✅ | AWS only | GCP only | Azure only | ✅ |
| **LLM support** | DIY | JumpStart | Model Garden | Azure OpenAI | ✅ |
| **On-prem** | ✅ | Limited | Limited | Limited | ✅ |

**Decision Framework:**
```
Choose BUILD when:
  - Strong regulatory/compliance requirements (banking, healthcare)
  - Must run on-premises
  - Existing large infrastructure team
  - Custom requirements that vendors don't support

Choose AWS/GCP/Azure when:
  - Speed to value > cost optimization
  - Already in that cloud ecosystem
  - Limited MLOps team (1-3 people)
  - Standard ML use cases

Choose Databricks when:
  - Already using Databricks for data engineering
  - Need multi-cloud flexibility
  - Strong Spark/Delta Lake investment
```

---

## Step 8: Capstone — Platform Architecture Validator

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
print('=== Enterprise AI Platform Architecture Validator ===')
print()

platform_components = {
    'Data Layer': {
        'data_catalog': True, 'feature_store': True,
        'data_versioning': False, 'data_validation': True, 'lineage_tracking': False,
    },
    'Training Infrastructure': {
        'experiment_tracking': True, 'distributed_training': True,
        'hyperparameter_tuning': True, 'compute_autoscaling': False, 'gpu_scheduling': True,
    },
    'Model Management': {
        'model_registry': True, 'model_versioning': True, 'a_b_testing': True,
        'model_lineage': True, 'performance_tracking': True,
    },
    'Serving Layer': {
        'online_serving': True, 'batch_serving': True, 'auto_scaling': True,
        'load_balancing': True, 'canary_deployment': False,
    },
    'Governance Layer': {
        'rbac': True, 'audit_logging': True, 'bias_monitoring': False,
        'compliance_reporting': False, 'data_privacy': True,
    },
}

total_checks = 0
passed_checks = 0
for layer, checks in platform_components.items():
    layer_passed = sum(1 for v in checks.values() if v)
    layer_total = len(checks)
    total_checks += layer_total
    passed_checks += layer_passed
    status = 'COMPLETE' if layer_passed == layer_total else f'PARTIAL ({layer_passed}/{layer_total})'
    print(f'  {layer:30s}: {status}')
    for check, status in checks.items():
        icon = chr(10003) if status else chr(10007)
        print(f'    [{icon}] {check}')
    print()

score = passed_checks / total_checks * 100
maturity = 'ENTERPRISE-READY' if score >= 90 else ('PRODUCTION' if score >= 70 else 'DEVELOPING')
print(f'Platform Score: {passed_checks}/{total_checks} ({score:.1f}%) -> {maturity}')

print()
print('Build vs Buy Comparison:')
options = {
    'Build (custom)': {'cost_yr': 2_000_000, 'time_months': 18, 'flexibility': 'HIGH', 'risk': 'HIGH'},
    'AWS SageMaker': {'cost_yr': 500_000, 'time_months': 3, 'flexibility': 'MEDIUM', 'risk': 'LOW'},
    'GCP Vertex AI': {'cost_yr': 450_000, 'time_months': 3, 'flexibility': 'MEDIUM', 'risk': 'LOW'},
    'Azure ML': {'cost_yr': 480_000, 'time_months': 3, 'flexibility': 'MEDIUM', 'risk': 'LOW'},
    'Databricks': {'cost_yr': 600_000, 'time_months': 2, 'flexibility': 'HIGH', 'risk': 'LOW'},
}
for opt, info in options.items():
    print(f'  {opt:20s}: \${info[\"cost_yr\"]/1e6:.1f}M/yr | {info[\"time_months\"]}mo | flexibility={info[\"flexibility\"]} | risk={info[\"risk\"]}')
"
```

📸 **Verified Output:**
```
=== Enterprise AI Platform Architecture Validator ===

  Data Layer                    : PARTIAL (3/5)
    [✓] data_catalog
    [✓] feature_store
    [✗] data_versioning
    [✓] data_validation
    [✗] lineage_tracking
  ...
Platform Score: 19/25 (76.0%) -> PRODUCTION

Build vs Buy Comparison:
  Build (custom)      : $2.0M/yr | 18mo | flexibility=HIGH | risk=HIGH
  AWS SageMaker       : $0.5M/yr | 3mo | flexibility=MEDIUM | risk=LOW
  GCP Vertex AI       : $0.5M/yr | 3mo | flexibility=MEDIUM | risk=LOW
  Azure ML            : $0.5M/yr | 3mo | flexibility=MEDIUM | risk=LOW
  Databricks          : $0.6M/yr | 2mo | flexibility=HIGH | risk=LOW
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Self-Service Platform | Abstract infrastructure; data scientist trains without K8s knowledge |
| Data Layer | Catalog + Feature Store (offline+online) + Lineage tracking |
| Training Infra | Job queue, GPU scheduling, fair share, distributed training support |
| Model Registry | Versioning + approval workflows + deployment integration |
| Governance | RBAC + audit trail + model cards + bias monitoring |
| Build vs Buy | Custom (18mo, $2M+) vs Managed ($0.5M, 2-3mo); compliance drives build |
| Platform Maturity | Score against 25 checklist items; target ENTERPRISE-READY (>90%) |

**Next Lab:** [Lab 13: AI Data Pipeline Architecture →](lab-13-ai-data-pipeline-architecture.md)
