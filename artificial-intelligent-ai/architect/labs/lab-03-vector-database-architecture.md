# Lab 03: Vector Database Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Vector databases power semantic search, RAG systems, and recommendation engines by storing and querying high-dimensional embeddings. This lab covers similarity metrics, index architectures, major vector DB comparisons, and dimensionality reduction techniques.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│              Vector Database Architecture                 │
├──────────────────────────────────────────────────────────┤
│  Embedding Models (text/image/audio) → Dense Vectors     │
│  Dimension: 384 (MiniLM), 768 (BERT), 1536 (GPT-4)     │
├──────────────────────────────────────────────────────────┤
│  Index Layer:                                            │
│  ├── Flat Index (exact, small datasets <100K)            │
│  ├── IVF (inverted file, medium datasets)                │
│  └── HNSW (hierarchical, large datasets, best recall)    │
├──────────────────────────────────────────────────────────┤
│  Query: embedding → ANN search → Top-K results          │
└──────────────────────────────────────────────────────────┘
```

---

## Step 1: Why Vector Databases?

Traditional databases can't efficiently answer: "Find the 10 most semantically similar documents to this query."

**The RAG Architecture Need:**
```
User Query → Embedding Model → Query Vector
                                    ↓
Vector DB ← Top-K semantic search ←─┘
    ↓
Retrieved Chunks → LLM Context Window → Response
```

**Vector DB vs Traditional DB:**

| Dimension | Relational DB | Vector DB |
|-----------|--------------|-----------|
| Data type | Structured rows | High-dim embeddings |
| Query type | Exact match, range | Approximate nearest neighbor |
| Scale | Billions of rows | Millions-billions of vectors |
| Latency | ms (indexed) | ms (ANN indexed) |
| Use case | OLTP, reports | Semantic search, RAG, recommenders |

---

## Step 2: Similarity Metrics

Choose your distance/similarity metric based on how your embeddings are trained.

**Cosine Similarity** (most common for NLP):
```
cos(A, B) = (A · B) / (|A| × |B|)
Range: [-1, 1], higher = more similar
```

**Euclidean Distance** (L2 norm):
```
dist(A, B) = √(Σ(aᵢ - bᵢ)²)
Range: [0, ∞), lower = more similar
```

**Dot Product** (unnormalized cosine):
```
dot(A, B) = Σ(aᵢ × bᵢ)
Range: (-∞, ∞), used for learned embeddings
```

| Metric | Best For | Notes |
|--------|---------|-------|
| **Cosine** | Text, normalized embeddings | Unit sphere, magnitude-invariant |
| **Euclidean** | Image embeddings, coordinates | Sensitive to vector magnitude |
| **Dot Product** | Recommendation systems | Fast but requires normalized vectors |
| **Inner Product** | FAISS indexes, retrieval | Default for many embedding models |

> 💡 OpenAI text-embedding models are optimized for cosine similarity. Always normalize vectors before computing cosine — use dot product on normalized vectors (identical, but faster).

---

## Step 3: Index Types

The index determines how vectors are stored and searched.

**Flat Index (Brute Force):**
```
Query → Compare with EVERY vector → Return top-K
Recall: 100% | Build: O(1) | Query: O(n)
Best for: < 100K vectors, where recall = 100% required
```

**IVF (Inverted File Index):**
```
Build: K-means clusters (nlist centroids)
Query: Find nearest centroids → search vectors in those clusters
Recall: ~95% | Build: O(n) | Query: O(√n)
Parameters: nlist=1024, nprobe=64
```

**HNSW (Hierarchical Navigable Small World):**
```
Build: Multi-layer graph of vectors (greedy)
Query: Navigate graph layers from coarse to fine
Recall: ~98% | Build: O(n log n) | Query: O(log n)
Parameters: M=16 (connections), ef_construction=200
```

**Index Selection Guide:**

| Vectors | Requirement | Recommended Index |
|---------|------------|------------------|
| < 100K | Max recall | Flat |
| 100K - 10M | Balanced | IVF (nlist=1024) |
| > 1M | Speed priority | HNSW (M=16) |
| > 1B | Memory-constrained | IVF + PQ (product quantization) |

---

## Step 4: Vector Database Comparison

| Feature | pgvector | Pinecone | Weaviate | Chroma |
|---------|---------|---------|---------|--------|
| **Type** | PostgreSQL extension | Managed cloud | Open-source/cloud | Open-source |
| **Scale** | <10M vectors | Billions | Millions-billions | Millions |
| **Index types** | IVF, HNSW | Proprietary | HNSW | HNSW |
| **Hybrid search** | With FTS | ✅ | ✅ | Limited |
| **Metadata filtering** | SQL | ✅ | ✅ | ✅ |
| **Self-hosted** | ✅ | ❌ | ✅ | ✅ |
| **GDPR/compliance** | ✅ (your infra) | Enterprise tier | ✅ | ✅ |
| **Best for** | Existing Postgres users | Managed/no-ops | Production RAG | Dev/prototyping |

**Architecture Decision:**
```
< 1M vectors + existing Postgres → pgvector (simple, no new infra)
Production RAG, millions+ → Weaviate or Pinecone
Development/testing → Chroma (in-memory or local)
Compliance-critical → Weaviate self-hosted or pgvector
```

---

## Step 5: Dimensionality Reduction with PCA

High-dimensional embeddings are expensive. PCA reduces dimensions while preserving variance.

**When to Use Dimensionality Reduction:**
- Cost optimization (smaller storage, faster queries)
- Visualization (reduce to 2D/3D with t-SNE/UMAP)
- Speed optimization (lower dimensions = faster ANN)
- Memory constraints

**PCA Trade-offs:**
```
512-dim → 128-dim: 50% variance retained, 4x memory savings
512-dim → 256-dim: 75% variance retained, 2x memory savings
1536-dim → 256-dim: ~60% variance retained, 6x memory savings
```

> 💡 Matryoshka Representation Learning (MRL) is better than post-hoc PCA for LLM embeddings. Models like OpenAI text-embedding-3 support variable dimensions natively.

---

## Step 6: Approximate Nearest Neighbor Trade-offs

ANN algorithms trade recall for speed. Understand the parameters.

**HNSW Parameters:**
```
M = 16:          Number of connections per node (higher = better recall, more memory)
ef_construction = 200: Build-time accuracy (higher = slower build, better index)
ef = 64:         Query-time accuracy (higher = slower query, better recall)
```

**Recall vs Latency Curve:**
```
ef=10:  recall=0.85, latency=0.5ms
ef=50:  recall=0.95, latency=1.5ms
ef=200: recall=0.99, latency=5ms
ef=500: recall=0.999, latency=12ms
```

**IVF Parameters:**
```
nlist = 1024:    Number of clusters (√n rule of thumb)
nprobe = 64:     Clusters to search at query time (higher = better recall, slower)
```

---

## Step 7: Production Vector DB Design

**Sharding Strategy for Large Collections:**
```
Collection (1B vectors) → Shard by: time, category, customer_segment
Each shard: 100M vectors → fits in single HNSW index
Query routing: metadata filter → target shard(s) → merge results
```

**Replication for High Availability:**
```
Primary node: reads + writes
Replica nodes (2+): reads only
Consistency: eventual (writes replicate async)
Failover: automatic, < 30 seconds
```

**Vector DB in Multi-tenant Architecture:**
```
Tenant A namespace: 10M vectors (isolated)
Tenant B namespace: 50M vectors (isolated)
Shared infrastructure: index per namespace
Billing: by vector storage + query volume
```

---

## Step 8: Capstone — Build Vector Similarity Engine

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
from sklearn.decomposition import PCA

np.random.seed(42)
dim = 128

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

query = np.random.randn(dim)
docs = np.random.randn(10, dim)
query_norm = query / np.linalg.norm(query)
docs_norm = docs / np.linalg.norm(docs, axis=1, keepdims=True)

print('=== Vector Similarity Metrics (dim=128) ===')
print(f'Query vector norm: {np.linalg.norm(query_norm):.4f}')
scores = [(i, cosine_sim(query_norm, docs_norm[i])) for i in range(10)]
scores.sort(key=lambda x: -x[1])
print('Top-3 by cosine similarity:')
for rank, (idx, score) in enumerate(scores[:3]):
    print(f'  rank={rank+1} doc={idx} cosine_sim={score:.4f}')

high_dim = np.random.randn(1000, 512)
pca = PCA(n_components=128)
reduced = pca.fit_transform(high_dim)
variance_retained = sum(pca.explained_variance_ratio_) * 100
print(f'PCA: 512-dim -> 128-dim | variance_retained={variance_retained:.1f}%')

index_types = {
    'Flat (brute force)': {'recall': 1.0, 'build_time': 'O(1)', 'query_time': 'O(n)', 'memory': 'high'},
    'IVF (inverted file)': {'recall': 0.95, 'build_time': 'O(n)', 'query_time': 'O(sqrt(n))', 'memory': 'medium'},
    'HNSW (hierarchical)': {'recall': 0.98, 'build_time': 'O(n log n)', 'query_time': 'O(log n)', 'memory': 'high'},
}
print('=== Index Type Comparison ===')
for itype, info in index_types.items():
    print(f'  {itype:30s}: recall={info[\"recall\"]} query={info[\"query_time\"]:15s} mem={info[\"memory\"]}')
"
```

📸 **Verified Output:**
```
=== Vector Similarity Metrics (dim=128) ===
Query vector norm: 1.0000
Top-3 by cosine similarity:
  rank=1 doc=3 cosine_sim=0.1921
  rank=2 doc=0 cosine_sim=0.0296
  rank=3 doc=1 cosine_sim=0.0289
PCA: 512-dim -> 128-dim | variance_retained=50.0%
=== Index Type Comparison ===
  Flat (brute force)            : recall=1.0 query=O(n)            mem=high
  IVF (inverted file)           : recall=0.95 query=O(sqrt(n))      mem=medium
  HNSW (hierarchical)           : recall=0.98 query=O(log n)        mem=high
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Vector DB Role | Store embeddings, enable semantic search and RAG |
| Similarity Metrics | Cosine (NLP), Euclidean (images), Dot product (recommenders) |
| Index Types | Flat (exact), IVF (medium scale), HNSW (large scale, best recall) |
| DB Comparison | pgvector (Postgres), Pinecone (managed), Weaviate (open-source prod), Chroma (dev) |
| PCA | Reduce dims, trade variance for speed/storage |
| ANN Trade-offs | Higher ef/nprobe = better recall, slower queries |

**Next Lab:** [Lab 04: LLM Infrastructure Design →](lab-04-llm-infrastructure-design.md)
