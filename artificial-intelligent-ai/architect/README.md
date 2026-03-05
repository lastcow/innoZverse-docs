# 🏛️ AI Architect Track

**Level:** Architect | **Labs:** 20 | **Total Time:** ~17 hours | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

The AI Architect track covers enterprise-grade AI platform design, MLOps at scale, LLM infrastructure, AI safety, and governance frameworks. Every lab includes verified Docker output and production-ready architecture patterns.

**Prerequisites:** Foundations + Practitioner tracks (or equivalent experience)

**You will learn to:**
- Design enterprise MLOps platforms (L0 → L1 → L2 maturity)
- Build LLM infrastructure with proper quantization and serving
- Architect RAG systems at scale with hybrid search
- Implement AI governance, fairness audits, and EU AI Act compliance
- Design federated learning and multi-agent systems
- Secure AI systems against adversarial attacks
- Optimize AI costs and ROI

---

## Lab Index

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 01 | [MLOps Platform Architecture](labs/lab-01-mlops-platform-architecture.md) | Maturity model L0/L1/L2, ML pipeline, MLflow, model registry, CI/CD for ML | 50 min |
| 02 | [Model Serving at Scale](labs/lab-02-model-serving-at-scale.md) | Online/batch/streaming, REST vs gRPC, Triton/BentoML, SLO, canary/shadow/A-B | 50 min |
| 03 | [Vector Database Architecture](labs/lab-03-vector-database-architecture.md) | Similarity metrics, IVF/HNSW indexes, pgvector/Pinecone/Weaviate/Chroma, PCA | 50 min |
| 04 | [LLM Infrastructure Design](labs/lab-04-llm-infrastructure-design.md) | A100/H100, quantization INT8/INT4, vLLM, KV cache, tensor/pipeline parallelism | 50 min |
| 05 | [RAG at Scale](labs/lab-05-rag-at-scale.md) | Ingestion pipeline, chunking, hybrid search BM25+vector, re-ranking, RAGAS eval | 50 min |
| 06 | [AI Observability & Monitoring](labs/lab-06-ai-observability-monitoring.md) | KS test, PSI, concept drift, feature importance drift, Evidently/Grafana | 50 min |
| 07 | [Federated Learning at Scale](labs/lab-07-federated-learning-at-scale.md) | FedAvg, differential privacy (ε-δ), secure aggregation, Byzantine tolerance | 50 min |
| 08 | [Multi-Agent System Design](labs/lab-08-multiagent-system-design.md) | ReAct pattern, orchestration topologies, memory types, guardrails, sandboxing | 50 min |
| 09 | [AI Security Red Team](labs/lab-09-ai-security-red-team.md) | Prompt injection, jailbreaking, model extraction, membership inference, MITRE ATLAS | 50 min |
| 10 | [EU AI Act Compliance](labs/lab-10-eu-ai-act-compliance.md) | Risk tiers, high-risk requirements, GPAI, CE marking, NIST AI RMF comparison | 50 min |
| 11 | [AI Cost Optimization](labs/lab-11-ai-cost-optimization.md) | GPU utilization, spot instances, distillation, caching, FinOps, ROI calculator | 50 min |
| 12 | [Enterprise AI Platform](labs/lab-12-enterprise-ai-platform.md) | Self-service ML, data layer, governance, build vs buy (SageMaker/Vertex/Azure/Databricks) | 50 min |
| 13 | [AI Data Pipeline Architecture](labs/lab-13-ai-data-pipeline-architecture.md) | Lambda/Kappa, feature engineering, DVC, Great Expectations, lineage, Feast | 50 min |
| 14 | [Responsible AI Audit](labs/lab-14-responsible-ai-audit.md) | Fairness metrics, disparate impact, SHAP/LIME, model cards, audit trail | 50 min |
| 15 | [LLM Fine-Tuning Infrastructure](labs/lab-15-llm-fine-tuning-infrastructure.md) | Full/LoRA/QLoRA, data prep JSONL, GPU memory calculator, DPO vs RLHF, BLEU/ROUGE | 50 min |
| 16 | [Knowledge Graph + LLM](labs/lab-16-knowledge-graph-llm.md) | Entity/relation extraction, Neo4j Cypher, GraphRAG, SPARQL, KG-augmented generation | 50 min |
| 17 | [Real-Time AI Inference](labs/lab-17-real-time-ai-inference.md) | Kafka→FeatureStore→Model→Action, latency budget P50/P95/P99, circuit breaker | 50 min |
| 18 | [AI SOC Automation](labs/lab-18-ai-soc-automation.md) | Alert triage, SIEM enrichment, UEBA, FP reduction, playbook automation, ATT&CK | 50 min |
| 19 | [Distributed Training Architecture](labs/lab-19-distributed-training-architecture.md) | DDP, tensor/pipeline parallel, ZeRO stages, gradient compression, mixed precision | 50 min |
| 20 | [Capstone: Enterprise AI Security Platform](labs/lab-20-capstone-enterprise-ai-security-platform.md) | Full platform: threat detection + RAG + agent + fairness + compliance + cost model | 50 min |

---

## Quick Reference: Architecture Patterns

| Pattern | Use When | Labs |
|---------|---------|------|
| MLOps Pipeline | Deploying ML to production | 01, 13 |
| LLM Serving | High-throughput LLM inference | 02, 04 |
| RAG System | Grounding LLM on enterprise data | 03, 05, 16 |
| Federated Learning | Cross-org training without data sharing | 07 |
| Multi-Agent | Complex multi-step automation | 08 |
| Real-Time ML | Sub-100ms prediction pipelines | 17 |
| Enterprise Platform | Self-service ML for teams | 12 |
| AI Security | Protecting LLM and ML systems | 09, 18 |
| Compliance | EU AI Act, fairness, audits | 10, 14 |

---

## Docker Quick Start

All labs use the same Docker image:

```bash
# Interactive shell
docker run -it --rm zchencow/innozverse-ai:latest bash

# Run a specific lab's code directly
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
from sklearn.linear_model import LogisticRegression
print('Environment ready!')
"
```

**Available packages:** numpy, sklearn, pandas, scipy, matplotlib, fastapi, pydantic, requests

---

## Learning Path

```
Foundations Track
    ↓
Practitioner Track
    ↓
Architect Track (this track)
    ↓
Labs 01-05: Core Platform (MLOps, Serving, Vector, LLM, RAG)
    ↓
Labs 06-10: Advanced AI (Monitoring, FL, Agents, Security, Compliance)
    ↓
Labs 11-15: Optimization & Governance (Cost, Platform, Data, Fairness, Fine-tuning)
    ↓
Labs 16-19: Specialized Topics (KG, Real-time, SOC, Distributed Training)
    ↓
Lab 20: Capstone — Enterprise AI Security Platform
```

---

*All labs include verified Docker output. Architecture diagrams represent production patterns from enterprise deployments.*
