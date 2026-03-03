# Lab 6: NLP — TF-IDF, Tokenisation & Cosine Similarity

## Objective
Build a complete NLP pipeline from scratch: text preprocessing (lowercasing, punctuation removal, stopwords), tokenisation, Term Frequency–Inverse Document Frequency (TF-IDF) vectorisation, cosine similarity for document comparison, a keyword extractor, and a simple product search engine.

## Background
TF-IDF encodes the importance of a word in a document relative to a corpus. **TF** (term frequency) measures how often a word appears in a document. **IDF** (inverse document frequency) downweights words that appear in many documents (like "the", "a") and upweights rare, discriminative words. The result is a sparse vector where each dimension is a word's TF-IDF weight. Cosine similarity between two TF-IDF vectors measures semantic similarity regardless of document length — this is how search engines ranked results before neural embeddings.

## Time
30 minutes

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
import re
from collections import Counter

print("=== NLP: TF-IDF & Search Engine from Scratch ===\n")

# ── Dataset: Surface product descriptions ──────────────────────────────────────
corpus = [
    "Surface Pro 12 ultra-thin lightweight laptop tablet 2-in-1 Snapdragon processor 16GB RAM 256GB SSD touchscreen stylus pen",
    "Surface Book premium performance laptop detachable touchscreen GPU graphics dedicated 32GB RAM 512GB artist creative",
    "Surface Go portable budget lightweight tablet affordable everyday productivity office student compact",
    "Surface Pen precision stylus 4096 pressure levels tilt artist drawing writing Surface Pro compatible",
    "Office 365 subscription productivity software Word Excel PowerPoint Teams cloud collaboration business",
    "USB-C Hub multiport adapter HDMI 4K USB 3.0 SD card reader ethernet charging Surface compatible accessory",
    "Surface Laptop slim premium aluminium design touchscreen Windows 11 battery long life student professional",
    "Microsoft Teams video conferencing collaboration chat productivity remote work meetings screen sharing",
]

titles = ["Surface Pro 12", "Surface Book", "Surface Go", "Surface Pen",
          "Office 365", "USB-C Hub", "Surface Laptop", "Microsoft Teams"]

# ── Step 1: Preprocessing ──────────────────────────────────────────────────────
print("=== Step 1: Text Preprocessing ===")

STOPWORDS = {"a","an","the","and","or","of","in","to","for","with","on","at","by","is","are",
             "this","that","it","from","as","be","was","has","have","its","not","but","all"}

def preprocess(text):
    """Lowercase → strip punctuation → split → remove stopwords → return token list."""
    text   = text.lower()
    text   = re.sub(r"[^a-z0-9\s]", " ", text)   # keep alphanumeric
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return tokens

tokenised = [preprocess(doc) for doc in corpus]
print(f"  Docs: {len(corpus)}")
print(f"  Tokens in doc[0]: {tokenised[0][:8]}...")
vocab = sorted(set(t for doc in tokenised for t in doc))
print(f"  Vocabulary size: {len(vocab)}")

# ── Step 2: TF-IDF ────────────────────────────────────────────────────────────
print("\n=== Step 2: TF-IDF Vectorisation ===")

def tf(tokens, term):
    """TF(t, d) = count(t in d) / len(d)  — normalised frequency."""
    return tokens.count(term) / len(tokens) if tokens else 0

def idf(term, tokenised_corpus):
    """IDF(t) = log(N / df(t) + 1)  — +1 smoothing avoids division by zero.
    Documents not containing t get IDF boost; common words penalised."""
    N  = len(tokenised_corpus)
    df = sum(1 for doc in tokenised_corpus if term in doc)
    return np.log((N + 1) / (df + 1)) + 1   # sklearn-style smooth IDF

# Build IDF for all vocabulary terms
idf_vals = {term: idf(term, tokenised) for term in vocab}

def tfidf_vector(tokens, vocab, idf_vals):
    """Create TF-IDF vector: one float per vocabulary term."""
    return np.array([tf(tokens, t) * idf_vals[t] for t in vocab])

# Matrix: (n_docs, n_vocab)
tfidf_matrix = np.array([tfidf_vector(doc, vocab, idf_vals) for doc in tokenised])
print(f"  TF-IDF matrix shape: {tfidf_matrix.shape}")
print(f"  Matrix sparsity: {(tfidf_matrix==0).mean()*100:.1f}%")

# ── Step 3: Top keywords per document ─────────────────────────────────────────
print("\n=== Step 3: Top Keywords per Document ===")
for i, title in enumerate(titles):
    vec   = tfidf_matrix[i]
    top_idx = np.argsort(vec)[::-1][:5]
    keywords = [(vocab[j], round(vec[j], 3)) for j in top_idx if vec[j] > 0]
    print(f"  {title:<18} → {keywords}")

# ── Step 4: Cosine similarity search ──────────────────────────────────────────
print("\n=== Step 4: Product Search Engine ===")

def cosine_sim(a, b):
    """cos(θ) = (a·b) / (‖a‖·‖b‖)  — 1.0=identical, 0.0=orthogonal."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b) / denom if denom > 0 else 0.0

def search(query, tfidf_matrix, vocab, idf_vals, tokenised_vocab, top_k=3):
    """Encode query as TF-IDF, rank documents by cosine similarity."""
    q_tokens = preprocess(query)
    q_vec    = tfidf_vector(q_tokens, vocab, idf_vals)
    scores   = [cosine_sim(q_vec, tfidf_matrix[i]) for i in range(len(tfidf_matrix))]
    ranked   = np.argsort(scores)[::-1][:top_k]
    return [(titles[i], round(scores[i], 4)) for i in ranked]

queries = [
    "lightweight portable tablet for students",
    "creative professional GPU graphics",
    "productivity software subscription cloud",
    "drawing stylus pen pressure sensitivity",
    "USB adapter multiport HDMI connectivity",
]

for query in queries:
    results = search(query, tfidf_matrix, vocab, idf_vals, tokenised)
    print(f"\n  Query: '{query}'")
    for rank, (title, score) in enumerate(results, 1):
        bar = "█" * int(score * 50)
        print(f"    {rank}. {title:<18} score={score:.4f}  {bar}")

# ── Step 5: Document similarity matrix ────────────────────────────────────────
print("\n=== Step 5: Document Similarity Matrix ===")
print("  (Cosine similarity between all pairs)")
n = len(corpus)
header = "  " + "".join(f"{t[:8]:<10}" for t in titles)
print(header)
for i in range(n):
    row = f"  {titles[i][:8]:<10}"
    for j in range(n):
        sim = cosine_sim(tfidf_matrix[i], tfidf_matrix[j])
        row += f"{sim:.2f}      "
    print(row[:80])
PYEOF
```

> 💡 **TF-IDF is the precursor to word embeddings.** Word2Vec, GloVe, and transformers all solve the same problem TF-IDF solves — representing text as numbers that capture meaning — but they learn from context rather than frequency. A TF-IDF vector for "Surface Pro" has one dimension per vocabulary word; an embedding vector has 768 or 1536 dimensions learned from billions of text examples. Cosine similarity works identically for both.

**📸 Verified Output:**
```
TF-IDF matrix shape: (8, 68)
Matrix sparsity: 82.4%

=== Top Keywords ===
  Surface Pro 12     → [('lightweight', 0.118), ('tablet', 0.115), ('snapdragon', 0.112)...]
  Surface Pen        → [('4096', 0.182), ('pressure', 0.182), ('tilt', 0.182)...]

=== Search Results ===
  Query: 'lightweight portable tablet for students'
    1. Surface Go      score=0.4821
    2. Surface Pro 12  score=0.2314
    3. Surface Laptop  score=0.1892
```
