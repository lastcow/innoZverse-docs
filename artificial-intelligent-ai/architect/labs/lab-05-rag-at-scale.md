# Lab 05: RAG at Scale

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Retrieval-Augmented Generation (RAG) extends LLMs with enterprise knowledge bases. This lab covers the complete RAG architecture for production scale: document ingestion, chunking strategies, hybrid search, re-ranking, and evaluation frameworks.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG at Scale Architecture                   │
├──────────────────────────────┬──────────────────────────────────┤
│     INGESTION PIPELINE       │         QUERY PIPELINE           │
│  Documents → Parse           │  Query → Embedding               │
│  → Chunk (strategy)          │  → BM25 sparse search            │
│  → Embed (model)             │  → Vector dense search           │
│  → Index (vector DB)         │  → RRF fusion                    │
│  → BM25 index                │  → Re-ranker (cross-encoder)     │
│                              │  → Context compression           │
│                              │  → LLM → Answer                  │
└──────────────────────────────┴──────────────────────────────────┘
```

---

## Step 1: Document Ingestion Pipeline

**Processing Flow:**
```
Raw Sources → Document Parser → Text Extractor → Chunker
PDF, DOCX, HTML, APIs
     ↓
Text + Metadata (source, date, author, section)
     ↓
Chunks → Embedding Model → Vector + BM25 Index
```

**Document Parsing Challenges:**
- PDF: tables, columns, headers — use PyMuPDF or Unstructured.io
- HTML: navigation/boilerplate noise — use trafilatura
- DOCX: style-based structure — python-docx
- Code: language-aware splitting — tree-sitter

**Metadata Strategy (Critical for Production):**
```json
{
  "chunk_id": "doc_123_chunk_5",
  "source": "policy_2024_q1.pdf",
  "source_type": "policy_document",
  "date": "2024-01-15",
  "section": "Section 3.2: Data Governance",
  "page_number": 12,
  "document_version": "v2.1"
}
```

> 💡 Metadata is your query-time filter. Without source/date metadata, you can't answer: "What does our Q1 2024 policy say about X?" — you'll get mixed results from all dates.

---

## Step 2: Chunking Strategies

Chunking is the most impactful RAG parameter. Bad chunking = bad retrieval.

**Fixed-Size Chunking:**
```
Chunk: 512 tokens, Overlap: 50 tokens
Pro: Simple, predictable, consistent
Con: Cuts mid-sentence, breaks semantic units
Best for: Homogeneous documents, quick prototyping
```

**Recursive Character Chunking (LangChain default):**
```
Split hierarchy: \n\n → \n → ". " → " " → character
Try larger splits first, fall back to smaller
Pro: Preserves paragraph/sentence boundaries
Con: Variable chunk sizes, harder to predict latency
```

**Semantic Chunking:**
```
Use embedding similarity between adjacent sentences
High similarity → same chunk
Low similarity → chunk boundary
Pro: Semantically coherent chunks
Con: Expensive (embed every sentence), slow ingestion
```

**Hierarchical Chunking (Best for Complex Docs):**
```
Document → Summary (for coarse retrieval)
         → Sections → Paragraphs → Sentences
Query: retrieve at appropriate granularity
```

| Strategy | Chunk Size | Overlap | Best For |
|----------|-----------|---------|---------|
| Fixed | 512 tokens | 50 | Quick start, homogeneous content |
| Recursive | 256-1024 | 20 | General documents |
| Semantic | Variable | 0 | High-quality retrieval |
| Hierarchical | Multi-level | 0 | Long documents, complex queries |

---

## Step 3: Embedding Models

**Embedding Model Comparison:**

| Model | Dimension | Context | MTEB Score | Cost | Best For |
|-------|----------|---------|-----------|------|---------|
| text-embedding-3-small | 1536 | 8191 | 62.3 | $0.02/1M | Cost-efficient |
| text-embedding-3-large | 3072 | 8191 | 64.6 | $0.13/1M | Highest quality |
| all-MiniLM-L6-v2 | 384 | 256 | 56.3 | Free (local) | Speed-optimized |
| BGE-M3 | 1024 | 8192 | 65.0 | Free (local) | Best open-source |
| E5-large | 1024 | 512 | 63.2 | Free (local) | Multilingual |
| Cohere embed-v3 | 1024 | 512 | 64.5 | $0.10/1M | Production open-source alt |

> 💡 BGE-M3 is the best free embedding model as of 2024. It supports sparse+dense (hybrid) from a single model. For production self-hosting, BGE-M3 is the top choice.

---

## Step 4: Hybrid Search (BM25 + Vector)

Pure vector search misses exact keyword matches. Pure BM25 misses semantic meaning. Hybrid search combines both.

**BM25 (Sparse Retrieval):**
```
Good at: exact keyword matches, entity names, IDs
Bad at: synonyms, paraphrases, semantic similarity
```

**Dense Vector Search:**
```
Good at: semantic similarity, paraphrases, concepts
Bad at: rare keywords, precise entity names
```

**Reciprocal Rank Fusion (RRF):**
```
score(doc) = Σ 1/(k + rank_in_list_i)
k = 60 (smoothing constant)

Example: doc3 ranks #1 in BM25, #3 in vector → high RRF score
```

**Hybrid Search Architecture:**
```
Query → [BM25 index → top-K sparse results]
     ↓  [Vector index → top-K dense results]
        → RRF or linear combination → merged top-K
```

---

## Step 5: Re-ranking

Retrieve many, re-rank to top-few. Re-rankers are cross-encoders that consider query+document jointly.

**Bi-encoder vs Cross-encoder:**
```
Bi-encoder (retrieval): Embed query and docs independently → dot product
  Fast (pre-compute doc embeddings), less accurate

Cross-encoder (re-ranking): Feed query + doc together → relevance score
  Slow (no pre-computation), much more accurate
```

**Re-ranking Pipeline:**
```
Query → Retrieval: top-100 (fast, approximate)
         ↓
      Re-ranker: score all 100 query+doc pairs
         ↓
      Top-5 → LLM context window
```

**Re-ranking Models:**
- `cross-encoder/ms-marco-MiniLM-L-6-v2` (fast, free)
- `Cohere Rerank` (API, excellent quality)
- `BGE-reranker-large` (open-source, competitive quality)

> 💡 Re-ranking alone can improve RAG answer quality by 20-30% without changing the LLM or embeddings.

---

## Step 6: Context Compression

LLM context windows are expensive. Compress retrieved context before sending to LLM.

**Compression Techniques:**

| Technique | Method | Compression Ratio | Quality Impact |
|-----------|--------|------------------|----------------|
| LLM extraction | Ask LLM to extract relevant sentences | 3-5x | Low |
| Embeddings filter | Remove low-similarity sentences | 2-3x | Low |
| Summarization | Summarize each chunk | 3-8x | Medium |
| Query-focused | Keep only query-relevant parts | 2-4x | Low |

**Contextual Compression Pipeline:**
```
Retrieved chunks (3000 tokens total)
    ↓
Filter: remove sentences with cosine_sim < 0.3 to query
    ↓
Compressed context (800 tokens)
    ↓
LLM: answer with citations
```

---

## Step 7: RAG Evaluation Metrics

**RAGAS Framework (Key Metrics):**

| Metric | Measures | Formula |
|--------|---------|---------|
| **Faithfulness** | Is answer grounded in context? | statements in context / total statements |
| **Answer Relevancy** | Does answer address the question? | semantic sim(question, answer) |
| **Context Precision** | Are retrieved chunks relevant? | relevant chunks / total retrieved |
| **Context Recall** | Were all relevant chunks retrieved? | retrieved relevant / all relevant |

**Automated Evaluation Loop:**
```
Golden Dataset (Q&A pairs) → Run RAG pipeline → LLM judge
    ↓
faithfulness_score, relevancy_score, context_score
    ↓
Aggregate → RAGAS score (0-1)
    ↓
Compare: baseline vs new chunking strategy vs new embedding model
```

---

## Step 8: Capstone — Hybrid RAG Search System

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

docs = [
    'Machine learning models require large amounts of training data',
    'Deep learning neural networks can process images and text',
    'Natural language processing enables computers to understand human language',
    'Vector databases store embeddings for semantic similarity search',
    'Retrieval augmented generation combines search with language models',
    'Enterprise AI platforms require robust MLOps infrastructure',
    'Model serving at scale requires load balancing and auto-scaling',
    'Data pipelines must handle real-time streaming and batch processing',
]

query = 'how do vector databases work with language models'

tfidf = TfidfVectorizer()
tfidf_matrix = tfidf.fit_transform(docs)
query_vec = tfidf.transform([query])
from sklearn.metrics.pairwise import cosine_similarity
tfidf_scores = cosine_similarity(query_vec, tfidf_matrix)[0]

np.random.seed(42)
doc_embeddings = np.random.randn(len(docs), 384)
doc_embeddings = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
query_embedding = np.random.randn(384)
query_embedding = query_embedding / np.linalg.norm(query_embedding)
for i in [3, 4]:
    doc_embeddings[i] = 0.7 * query_embedding + 0.3 * doc_embeddings[i]
    doc_embeddings[i] /= np.linalg.norm(doc_embeddings[i])
vector_scores = doc_embeddings @ query_embedding

def rrf(ranks1, ranks2, k=60):
    scores = {}
    for i, r in enumerate(ranks1):
        scores[r] = scores.get(r, 0) + 1/(k + i + 1)
    for i, r in enumerate(ranks2):
        scores[r] = scores.get(r, 0) + 1/(k + i + 1)
    return sorted(scores.keys(), key=lambda x: -scores[x])

tfidf_ranks = np.argsort(-tfidf_scores)
vector_ranks = np.argsort(-vector_scores)
hybrid_ranks = rrf(tfidf_ranks, vector_ranks)

print('=== RAG Hybrid Search (TF-IDF + Vector + RRF) ===')
print(f'Query: \"{query}\"')
print()
print('Top-3 Results:')
for rank, idx in enumerate(hybrid_ranks[:3]):
    print(f'  rank={rank+1} | tfidf={tfidf_scores[idx]:.3f} | vector={vector_scores[idx]:.3f} | doc: \"{docs[idx][:60]}...\"')

print()
print('=== Chunking Strategy Comparison ===')
strategies = {
    'fixed_size': {'chunk_size': 512, 'overlap': 50, 'pros': 'simple, predictable', 'cons': 'cuts sentences'},
    'semantic': {'chunk_size': 'variable', 'overlap': 0, 'pros': 'coherent units', 'cons': 'complex'},
    'recursive': {'chunk_size': '256-1024', 'overlap': 20, 'pros': 'balanced', 'cons': 'slower'},
}
for s, info in strategies.items():
    print(f'  {s:12s}: chunk={str(info[\"chunk_size\"]):10s} | pros={info[\"pros\"]}')
"
```

📸 **Verified Output:**
```
=== RAG Hybrid Search (TF-IDF + Vector + RRF) ===
Query: "how do vector databases work with language models"

Top-3 Results:
  rank=1 | tfidf=0.430 | vector=0.919 | doc: "Retrieval augmented generation combines search with language..."
  rank=2 | tfidf=0.343 | vector=0.915 | doc: "Vector databases store embeddings for semantic similarity se..."
  rank=3 | tfidf=0.217 | vector=0.053 | doc: "Natural language processing enables computers to understand ..."

=== Chunking Strategy Comparison ===
  fixed_size  : chunk=512        | pros=simple, predictable
  semantic    : chunk=variable   | pros=coherent units
  recursive   : chunk=256-1024   | pros=balanced
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Ingestion Pipeline | Parse → chunk → embed → index (vector + BM25) |
| Chunking | Fixed (simple) → Recursive (balanced) → Semantic (quality) |
| Embeddings | BGE-M3 (best open-source), text-embedding-3 (OpenAI) |
| Hybrid Search | BM25 (keywords) + Vector (semantic) + RRF (fusion) |
| Re-ranking | Cross-encoder: retrieve 100, re-rank to top-5 = +20-30% quality |
| Context Compression | Filter/compress before LLM = lower cost, better focus |
| Evaluation | RAGAS: faithfulness + answer relevancy + context precision/recall |

**Next Lab:** [Lab 06: AI Observability & Monitoring →](lab-06-ai-observability-monitoring.md)
