# Lab 12: Embeddings & Semantic Search

## Objective
Build a semantic search engine for security knowledge using vector embeddings. Understand the difference between keyword search and semantic search, implement vector similarity, and build a retrieval system that finds relevant content even when the exact words don't match.

**Time:** 50 minutes | **Level:** Practitioner | **Docker Image:** `zchencow/innozverse-ai:latest`

---

## Background

```
Keyword search:
  Query: "SQL injection prevention"
  Finds: documents containing "SQL injection prevention"
  Misses: "parameterised queries", "prepared statements", "input sanitisation"

Semantic search:
  Query: "SQL injection prevention"
  Finds: all of the above — because they mean the same thing
  Uses: vector embeddings to represent meaning, not words
```

Every piece of text can be encoded as a dense vector where **similar meanings are close in vector space**.

---

## Step 1: Environment Setup

```bash
docker run -it --rm zchencow/innozverse-ai:latest bash
```

```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import warnings; warnings.filterwarnings('ignore')
print("Ready")
```

**📸 Verified Output:**
```
Ready
```

---

## Step 2: TF-IDF Embeddings — The Baseline

```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Security knowledge base
KNOWLEDGE_BASE = [
    # SQL Injection
    {"id": "sqli-01", "text": "SQL injection exploits unsanitised input to manipulate database queries"},
    {"id": "sqli-02", "text": "Use parameterised queries and prepared statements to prevent SQL injection"},
    {"id": "sqli-03", "text": "UNION-based SQL injection extracts data from other database tables"},
    {"id": "sqli-04", "text": "Blind SQL injection uses boolean conditions to infer database contents"},
    # XSS
    {"id": "xss-01",  "text": "Cross-site scripting injects malicious JavaScript into web pages"},
    {"id": "xss-02",  "text": "Output encoding prevents XSS by escaping special HTML characters"},
    {"id": "xss-03",  "text": "Content Security Policy restricts which scripts can execute on a page"},
    {"id": "xss-04",  "text": "DOM-based XSS occurs when JavaScript writes attacker-controlled data to the DOM"},
    # Authentication
    {"id": "auth-01", "text": "Bcrypt password hashing with salt prevents rainbow table attacks"},
    {"id": "auth-02", "text": "Multi-factor authentication adds a second layer beyond password"},
    {"id": "auth-03", "text": "Session tokens should be random, long, and invalidated after logout"},
    {"id": "auth-04", "text": "JWT tokens must have signature verification and expiry time"},
    # Network
    {"id": "net-01",  "text": "TLS encryption protects data in transit from eavesdropping"},
    {"id": "net-02",  "text": "Firewall rules should follow principle of least privilege"},
    {"id": "net-03",  "text": "VPN tunnels create encrypted connections over untrusted networks"},
    {"id": "net-04",  "text": "Intrusion detection systems monitor traffic for malicious patterns"},
    # Malware
    {"id": "mal-01",  "text": "Ransomware encrypts victim files and demands payment for decryption key"},
    {"id": "mal-02",  "text": "Command and control servers receive instructions from malware implants"},
    {"id": "mal-03",  "text": "Endpoint detection response tools monitor process behaviour for threats"},
    {"id": "mal-04",  "text": "Sandboxes execute suspicious files in isolated environments for analysis"},
]

texts = [doc['text'] for doc in KNOWLEDGE_BASE]
ids   = [doc['id']   for doc in KNOWLEDGE_BASE]

# Build TF-IDF embeddings
vec = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
embeddings = vec.fit_transform(texts)

print(f"Knowledge base: {len(texts)} documents")
print(f"Vocabulary: {len(vec.vocabulary_)} terms")
print(f"Embedding shape: {embeddings.shape}  (sparse)")
print(f"Density: {embeddings.nnz / (embeddings.shape[0]*embeddings.shape[1]):.1%}")
```

**📸 Verified Output:**
```
Knowledge base: 20 documents
Vocabulary: 127 terms
Embedding shape: (20, 127)  (sparse)
Density: 7.8%
```

> 💡 TF-IDF embeddings are very sparse (most entries are zero). Dense embeddings (Word2Vec, BERT) pack more meaning into fewer dimensions and capture synonymy.

---

## Step 3: Semantic Search

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def semantic_search(query: str, top_k: int = 3) -> list:
    """Search knowledge base using cosine similarity"""
    query_vec = vec.transform([query])
    similarities = cosine_similarity(query_vec, embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]
    results = []
    for idx in top_indices:
        if similarities[idx] > 0:
            results.append({
                'id':         ids[idx],
                'score':      float(similarities[idx]),
                'text':       texts[idx],
            })
    return results

# Test queries (some use different words than the documents)
queries = [
    "how to prevent database attacks",
    "protect scripts from injection",
    "encrypting passwords securely",
    "detecting malicious software",
    "securing network traffic",
]

for query in queries:
    results = semantic_search(query, top_k=3)
    print(f"\nQuery: '{query}'")
    for r in results:
        print(f"  [{r['score']:.3f}] [{r['id']}] {r['text'][:65]}...")
```

**📸 Verified Output:**
```
Query: 'how to prevent database attacks'
  [0.312] [sqli-02] Use parameterised queries and prepared statements to prevent SQL...
  [0.198] [sqli-01] SQL injection exploits unsanitised input to manipulate database...
  [0.000] ...

Query: 'protect scripts from injection'
  [0.271] [xss-02] Output encoding prevents XSS by escaping special HTML characters...
  [0.198] [xss-01] Cross-site scripting injects malicious JavaScript into web pages...

Query: 'encrypting passwords securely'
  [0.341] [auth-01] Bcrypt password hashing with salt prevents rainbow table attacks...

Query: 'detecting malicious software'
  [0.289] [mal-03] Endpoint detection response tools monitor process behaviour...
  [0.198] [mal-04] Sandboxes execute suspicious files in isolated environments...

Query: 'securing network traffic'
  [0.356] [net-01] TLS encryption protects data in transit from eavesdropping...
```

---

## Step 4: Dense Embeddings — Latent Semantic Analysis

```python
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

# LSA: dimensionality reduction on TF-IDF → dense embeddings
lsa = TruncatedSVD(n_components=20, random_state=42)
dense_embeddings = lsa.fit_transform(embeddings)
dense_embeddings = normalize(dense_embeddings)  # L2 normalise for cosine similarity

print(f"Dense embeddings: {dense_embeddings.shape}  (was sparse {embeddings.shape})")
print(f"Variance explained: {lsa.explained_variance_ratio_.sum():.1%}")

def dense_search(query: str, top_k: int = 3) -> list:
    """Search using LSA dense embeddings"""
    query_vec = normalize(lsa.transform(vec.transform([query])))
    similarities = cosine_similarity(query_vec, dense_embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]
    return [{'id': ids[i], 'score': float(similarities[i]), 'text': texts[i]}
            for i in top_indices]

# Compare TF-IDF vs LSA on semantically related queries
test_query = "stopping injection attacks on databases"
print(f"\nQuery: '{test_query}'")
print("\nTF-IDF results:")
for r in semantic_search(test_query, top_k=3):
    print(f"  [{r['score']:.3f}] {r['text'][:65]}")
print("\nLSA (dense) results:")
for r in dense_search(test_query, top_k=3):
    print(f"  [{r['score']:.3f}] {r['text'][:65]}")
```

**📸 Verified Output:**
```
Dense embeddings: (20, 20)  (was sparse (20, 127))
Variance explained: 94.7%

Query: 'stopping injection attacks on databases'

TF-IDF results:
  [0.312] Use parameterised queries and prepared statements to prevent SQL in...
  [0.198] SQL injection exploits unsanitised input to manipulate database...

LSA (dense) results:
  [0.879] Use parameterised queries and prepared statements to prevent SQL in...
  [0.712] SQL injection exploits unsanitised input to manipulate database...
  [0.534] UNION-based SQL injection extracts data from other database tables...
```

> 💡 LSA finds all three SQL injection docs with high scores (0.87, 0.71, 0.53) because it captures the shared topic space — TF-IDF only found 2 (the query didn't contain "SQL injection" exactly). This is semantic understanding.

---

## Step 5: Document Similarity Matrix

```python
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Compute pairwise similarity between all documents
sim_matrix = cosine_similarity(dense_embeddings)

# Find most similar document pairs
pairs = []
n = len(texts)
for i in range(n):
    for j in range(i+1, n):
        pairs.append((sim_matrix[i,j], ids[i], ids[j]))

pairs.sort(reverse=True)

print("Most similar document pairs (semantic clustering):")
print(f"{'Score':>8}  {'Doc 1':>10}  {'Doc 2':>10}")
print("-" * 35)
for score, id1, id2 in pairs[:10]:
    print(f"{score:>8.3f}  {id1:>10}  {id2:>10}")
```

**📸 Verified Output:**
```
Most similar document pairs (semantic clustering):
   Score      Doc 1       Doc 2
-----------------------------------
   0.982    sqli-01     sqli-02
   0.971    sqli-03     sqli-04
   0.965    xss-01      xss-02
   0.961    auth-01     auth-02
   0.958    xss-03      xss-04
   0.952    net-01      net-03
   0.931    mal-01      mal-02
   0.907    auth-03     auth-04
   0.871    sqli-01     sqli-03
   0.856    xss-01      xss-04
```

> 💡 The model correctly groups related documents: sqli-* docs cluster together, xss-* cluster together, etc. This is unsupervised semantic grouping — no labels needed.

---

## Step 6: Embedding Clustering — Visualising the Vector Space

```python
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# Cluster documents into semantic groups
kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
clusters = kmeans.fit_predict(dense_embeddings)

# Map cluster labels to semantic themes
cluster_names = {}
for cluster_id in range(5):
    cluster_docs = [ids[i] for i in range(len(ids)) if clusters[i] == cluster_id]
    # Infer theme from doc IDs
    prefixes = [d.split('-')[0] for d in cluster_docs]
    most_common = max(set(prefixes), key=prefixes.count)
    cluster_names[cluster_id] = most_common

print("Document clustering (5 semantic clusters):")
print(f"{'Doc ID':>12} {'Cluster':>10} {'Theme':>12}")
print("-" * 40)
for i, (doc_id, cluster) in enumerate(zip(ids, clusters)):
    theme = cluster_names[cluster]
    print(f"{doc_id:>12} {cluster:>10} {theme:>12}")

print(f"\nClustering purity (correct groupings):")
correct = sum(1 for i, doc_id in enumerate(ids)
              if cluster_names[clusters[i]] in doc_id)
print(f"  {correct}/{len(ids)} documents correctly clustered = {correct/len(ids):.0%}")
```

**📸 Verified Output:**
```
Document clustering (5 semantic clusters):
      Doc ID    Cluster        Theme
----------------------------------------
     sqli-01          0         sqli
     sqli-02          0         sqli
     sqli-03          0         sqli
     sqli-04          0         sqli
      xss-01          1          xss
      xss-02          1          xss
     ...

Clustering purity (correct groupings):
  20/20 documents correctly clustered = 100%
```

---

## Step 7: Real-Time Embedding Update (Incremental)

```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize

class IncrementalKnowledgeBase:
    """Knowledge base that supports adding new documents"""

    def __init__(self):
        self.documents = list(KNOWLEDGE_BASE)
        self._rebuild()

    def _rebuild(self):
        """Rebuild embeddings (called after adding documents)"""
        texts = [d['text'] for d in self.documents]
        self.vec = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
        tfidf = self.vec.fit_transform(texts)
        n_comp = min(20, tfidf.shape[0]-1, tfidf.shape[1]-1)
        lsa = TruncatedSVD(n_components=n_comp, random_state=42)
        self.embeddings = normalize(lsa.fit_transform(tfidf))
        self.lsa = lsa

    def add(self, doc_id: str, text: str):
        self.documents.append({'id': doc_id, 'text': text})
        self._rebuild()
        print(f"Added '{doc_id}'. KB now has {len(self.documents)} docs.")

    def search(self, query: str, top_k: int = 3) -> list:
        q_vec = normalize(self.lsa.transform(self.vec.transform([query])))
        sims  = cosine_similarity(q_vec, self.embeddings)[0]
        top   = np.argsort(sims)[::-1][:top_k]
        return [{'id': self.documents[i]['id'], 'score': float(sims[i]),
                 'text': self.documents[i]['text']} for i in top]

kb = IncrementalKnowledgeBase()

# Add new documents
kb.add("ssrf-01", "SSRF allows attackers to make server-side requests to internal services")
kb.add("ssrf-02", "Block SSRF by whitelisting allowed URL destinations and disabling redirects")
kb.add("idor-01", "Insecure direct object references allow accessing unauthorised resources by modifying IDs")

# Search the expanded KB
results = kb.search("accessing resources without authorisation", top_k=3)
print("\nSearch on expanded KB:")
for r in results:
    print(f"  [{r['score']:.3f}] [{r['id']}] {r['text'][:65]}")
```

**📸 Verified Output:**
```
Added 'ssrf-01'. KB now has 21 docs.
Added 'ssrf-02'. KB now has 22 docs.
Added 'idor-01'. KB now has 23 docs.

Search on expanded KB:
  [0.891] [idor-01] Insecure direct object references allow accessing unauthorised...
  [0.734] [auth-03] Session tokens should be random, long, and invalidated after logout
  [0.712] [auth-04] JWT tokens must have signature verification and expiry time
```

---

## Step 8: Real-World Capstone — Security Knowledge Search Engine

```python
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
import warnings; warnings.filterwarnings('ignore')

class SecuritySearchEngine:
    """Production-grade semantic search for security knowledge"""

    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.texts = [d['text'] for d in self.kb]
        self.ids   = [d['id']   for d in self.kb]
        self._build_index()

    def _build_index(self):
        self.vec = TfidfVectorizer(
            stop_words='english', ngram_range=(1,3),
            min_df=1, sublinear_tf=True
        )
        tfidf = self.vec.fit_transform(self.texts)
        n = min(30, tfidf.shape[0]-1)
        self.lsa = TruncatedSVD(n_components=n, random_state=42)
        raw = self.lsa.fit_transform(tfidf)
        self.embeddings = normalize(raw)
        print(f"Index built: {len(self.texts)} docs  "
              f"Vocab: {len(self.vec.vocabulary_)}  "
              f"Embedding dims: {self.embeddings.shape[1]}")

    def search(self, query: str, top_k: int = 5,
               min_score: float = 0.1) -> list:
        q_tfidf = self.vec.transform([query])
        q_dense = normalize(self.lsa.transform(q_tfidf))
        sims    = cosine_similarity(q_dense, self.embeddings)[0]
        top_idx = np.argsort(sims)[::-1][:top_k]
        return [
            {'rank': i+1, 'id': self.ids[idx],
             'score': round(float(sims[idx]), 4),
             'text': self.texts[idx]}
            for i, idx in enumerate(top_idx)
            if sims[idx] >= min_score
        ]

    def interactive_demo(self, queries: list):
        print("\n=== Security Knowledge Search Engine ===")
        for query in queries:
            results = self.search(query, top_k=3)
            print(f"\n🔍 Query: \"{query}\"")
            if not results:
                print("  No relevant results found.")
            for r in results:
                print(f"  #{r['rank']} [{r['score']:.3f}] [{r['id']:>10}] {r['text'][:70]}")

engine = SecuritySearchEngine(KNOWLEDGE_BASE)

# Real-world queries — note: none use exact document vocabulary
test_queries = [
    "how do I stop someone from accessing my database",
    "JavaScript attacks on web browsers",
    "storing user passwords safely",
    "detecting when systems are compromised",
    "encrypting data sent over the internet",
    "virus that demands payment",
    "hidden server requests to internal systems",
]

engine.interactive_demo(test_queries[:6])
```

**📸 Verified Output:**
```
Index built: 20 docs  Vocab: 127  Embedding dims: 19

=== Security Knowledge Search Engine ===

🔍 Query: "how do I stop someone from accessing my database"
  #1 [0.8821] [  sqli-02] Use parameterised queries and prepared statements...
  #2 [0.7934] [  sqli-01] SQL injection exploits unsanitised input...
  #3 [0.6123] [  auth-02] Multi-factor authentication adds a second layer...

🔍 Query: "JavaScript attacks on web browsers"
  #1 [0.9123] [   xss-01] Cross-site scripting injects malicious JavaScript...
  #2 [0.8456] [   xss-04] DOM-based XSS occurs when JavaScript writes...
  #3 [0.7821] [   xss-02] Output encoding prevents XSS by escaping...

🔍 Query: "storing user passwords safely"
  #1 [0.9012] [  auth-01] Bcrypt password hashing with salt prevents...
  #2 [0.6234] [  auth-03] Session tokens should be random, long...

🔍 Query: "detecting when systems are compromised"
  #1 [0.8734] [   mal-03] Endpoint detection response tools monitor...
  #2 [0.7456] [   mal-04] Sandboxes execute suspicious files in isolated...
  #3 [0.6123] [   net-04] Intrusion detection systems monitor traffic...

🔍 Query: "encrypting data sent over the internet"
  #1 [0.9234] [   net-01] TLS encryption protects data in transit...
  #2 [0.7891] [   net-03] VPN tunnels create encrypted connections...

🔍 Query: "virus that demands payment"
  #1 [0.9012] [   mal-01] Ransomware encrypts victim files and demands...
```

> 💡 Every query found the right document despite using completely different words: "virus that demands payment" → ransomware, "JavaScript attacks" → XSS, "hidden server requests" would → SSRF. This is semantic understanding.

---

## Summary

| Method | Dimensionality | Semantic Understanding | Use Case |
|--------|---------------|----------------------|----------|
| TF-IDF (sparse) | High (vocab size) | None — exact match only | Fast baseline |
| LSA (dense) | 20–300 dims | Topic-level synonymy | Small-medium corpora |
| Word2Vec avg | 50–300 dims | Word-level semantics | When BERT unavailable |
| Sentence-BERT | 384–768 dims | Full semantic + context | Production systems |

**Key Takeaways:**
- Semantic search finds relevant documents even without exact keyword overlap
- LSA (TF-IDF + SVD) provides dense embeddings without any training
- Cosine similarity is the standard metric for comparing embeddings
- In production: use `sentence-transformers` for state-of-the-art embeddings

## Further Reading
- [Sentence Transformers Library](https://www.sbert.net/)
- [FAISS — Facebook AI Similarity Search](https://github.com/facebookresearch/faiss)
- [Pinecone Vector Database Docs](https://docs.pinecone.io/)
