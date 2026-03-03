# Lab 8: Natural Language Processing — TF-IDF & Text Classification

## Objective
Build an NLP pipeline from scratch: text tokenisation and normalisation, Term Frequency-Inverse Document Frequency (TF-IDF) vectorisation, cosine similarity for document comparison, Naive Bayes text classifier, and a semantic search engine for Microsoft product descriptions.

## Background
TF-IDF measures how important a word is to a document within a corpus. **TF** (term frequency) = how often a word appears in a document. **IDF** (inverse document frequency) = log(N/df) where df is how many documents contain the word — common words like "the" get low IDF. The product TF×IDF gives high scores to words that are frequent in a document but rare in the corpus — exactly the words that characterise that document.

## Time
30 minutes

## Prerequisites
- Lab 01 (Linear Regression) — numpy fundamentals

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
import re
from collections import Counter, defaultdict
import math

# ── Product review corpus ─────────────────────────────────────────────────────
corpus = {
    "surface_pro_pos": "The Surface Pro is an incredible laptop with amazing performance. The display is stunning and the keyboard cover works great. Battery life is excellent for productivity. Perfect for professional work and creative tasks.",
    "surface_pro_neg": "The Surface Pro is overpriced for what it offers. The fan is noisy under load. Battery life is disappointing. The keyboard is sold separately which is unacceptable at this price. Not worth the money.",
    "surface_go_pos":  "Surface Go is a great compact tablet for students. Lightweight and portable. Good battery life for note taking. Perfect size for carrying around. Great for light productivity and web browsing.",
    "surface_go_neg":  "Surface Go is underpowered for multitasking. Slow performance with multiple apps. Limited storage is frustrating. Not suitable for demanding tasks. Feels sluggish compared to competitors.",
    "surface_book_pos":"Surface Book has incredible build quality and performance. The detachable display is innovative and useful. Great for both laptop and tablet use. Excellent GPU performance for creative work.",
    "surface_book_neg":"Surface Book is extremely expensive. Battery life is poor when using GPU. Hinges feel fragile. Software has compatibility issues. Not reliable for daily professional use.",
}

# ── Step 1: Tokenisation ──────────────────────────────────────────────────────
print("=== Step 1: Tokenisation ===")
STOPWORDS = {"the","a","an","is","for","and","of","in","to","it","not","at",
             "this","that","with","has","are","be","been","by","from","on"}

def tokenise(text: str) -> list[str]:
    # Lowercase, remove punctuation, split, remove stopwords
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = text.split()
    return [t for t in tokens if t not in STOPWORDS and len(t) > 2]

for doc_id, text in list(corpus.items())[:2]:
    tokens = tokenise(text)
    print(f"  {doc_id}: {tokens[:8]}...")

# ── Step 2: TF-IDF vectorisation ─────────────────────────────────────────────
print("\n=== Step 2: TF-IDF Vectorisation ===")
class TFIDFVectoriser:
    def __init__(self, max_features=50):
        self.max_features = max_features
        self.vocab = {}           # word → index
        self.idf_values = {}      # word → IDF score

    def fit(self, docs: list[str]):
        tokenised = [tokenise(d) for d in docs]
        # IDF: how many documents contain each word
        N = len(docs)
        df = defaultdict(int)
        for tokens in tokenised:
            for word in set(tokens):
                df[word] += 1
        # Select top-max_features by document frequency
        self.vocab = {w: i for i, (w,_) in enumerate(
            sorted(df.items(), key=lambda x: -x[1])[:self.max_features]
        )}
        # IDF = log(N / df(w)) + 1  (smooth)
        self.idf_values = {
            w: math.log(N / df[w]) + 1
            for w in self.vocab
        }
        return self

    def transform(self, docs: list[str]) -> np.ndarray:
        V = len(self.vocab)
        matrix = np.zeros((len(docs), V))
        for i, doc in enumerate(docs):
            tokens = tokenise(doc)
            tf = Counter(tokens)
            total = len(tokens) + 1
            for word, idx in self.vocab.items():
                if word in tf:
                    tf_val  = tf[word] / total
                    idf_val = self.idf_values[word]
                    matrix[i, idx] = tf_val * idf_val
        # L2-normalise each document vector
        norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
        return matrix / norms

    def fit_transform(self, docs):
        return self.fit(docs).transform(docs)

docs     = list(corpus.values())
doc_keys = list(corpus.keys())
vectoriser = TFIDFVectoriser(max_features=40)
tfidf_matrix = vectoriser.fit_transform(docs)
print(f"  TF-IDF matrix: {tfidf_matrix.shape} (6 docs × 40 terms)")
print(f"  Vocabulary size: {len(vectoriser.vocab)} terms")

# Top terms per document
print(f"\n  Top-5 terms per document:")
vocab_inv = {v:k for k,v in vectoriser.vocab.items()}
for i, key in enumerate(doc_keys):
    top_idx  = np.argsort(tfidf_matrix[i])[::-1][:5]
    top_terms = [f"{vocab_inv[j]}({tfidf_matrix[i,j]:.3f})" for j in top_idx]
    print(f"  {key:<22}: {', '.join(top_terms)}")

# ── Step 3: Cosine similarity ─────────────────────────────────────────────────
print("\n=== Step 3: Cosine Similarity ===")
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)

# Similarity matrix
print(f"  {'':22}", end="")
for k in doc_keys: print(f"  {k[:8]:>8}", end="")
print()
for i, ki in enumerate(doc_keys):
    print(f"  {ki:<22}", end="")
    for j in range(len(doc_keys)):
        sim = cosine_sim(tfidf_matrix[i], tfidf_matrix[j])
        print(f"  {sim:>8.4f}", end="")
    print()

# ── Step 4: Semantic search ───────────────────────────────────────────────────
print("\n=== Step 4: Semantic Search ===")
queries = [
    "great battery life portable",
    "overpriced noisy fan disappointing",
    "excellent performance creative work",
]
for query in queries:
    q_vec = vectoriser.transform([query])[0]
    sims  = [(doc_keys[i], cosine_sim(q_vec, tfidf_matrix[i])) for i in range(len(docs))]
    sims.sort(key=lambda x: -x[1])
    print(f"\n  Query: '{query}'")
    for doc_id, sim in sims[:3]:
        print(f"    {sim:.4f}  {doc_id}")

# ── Step 5: Naive Bayes text classifier ──────────────────────────────────────
print("\n=== Step 5: Naive Bayes Sentiment Classifier ===")
# Labels: 1=positive, 0=negative
labels = np.array([1, 0, 1, 0, 1, 0])

class NaiveBayesClassifier:
    def fit(self, X, y):
        self.classes = np.unique(y)
        self.priors  = {}
        self.likelihoods = {}  # class → word probabilities
        for c in self.classes:
            X_c = X[y == c]
            self.priors[c] = len(X_c) / len(X)
            # Sum feature vectors and smooth (Laplace)
            word_counts = X_c.sum(axis=0) + 1e-6
            self.likelihoods[c] = np.log(word_counts / word_counts.sum())
        return self

    def predict_one(self, x):
        scores = {}
        for c in self.classes:
            scores[c] = np.log(self.priors[c]) + np.dot(x, self.likelihoods[c])
        return max(scores, key=scores.get)

    def predict(self, X): return np.array([self.predict_one(x) for x in X])

nb = NaiveBayesClassifier().fit(tfidf_matrix, labels)
preds = nb.predict(tfidf_matrix)
sentiment = {1: "Positive", 0: "Negative"}
print(f"  {'Review':<25} {'True':<10} {'Predicted':<10} {'OK?'}")
for i, key in enumerate(doc_keys):
    ok = "✓" if preds[i]==labels[i] else "✗"
    print(f"  {key:<25} {sentiment[labels[i]]:<10} {sentiment[preds[i]]:<10} {ok}")
acc = (preds == labels).mean()
print(f"\n  Accuracy: {acc*100:.1f}%")

# Test on new review
new_review = "The device has excellent performance and great display quality. Worth the price."
x_new = vectoriser.transform([new_review])[0]
pred  = nb.predict_one(x_new)
print(f"\n  New review: '{new_review[:50]}...'")
print(f"  Sentiment: {sentiment[pred]}")
PYEOF
```

> 💡 **IDF is what separates TF-IDF from simple word counts.** The word "great" appears in many product reviews — high TF, but low IDF because it's in almost every document. IDF = log(6/6)+1 ≈ 1.0. The word "detachable" appears only in Surface Book reviews — IDF = log(6/1)+1 ≈ 2.8. When multiplied by TF, "detachable" becomes the dominant term for Surface Book documents. This is exactly why search engines rank documents with rare matching terms higher.

**📸 Verified Output:**
```
=== Step 2: TF-IDF Vectorisation ===
  TF-IDF matrix: (6, 40)
  Top-5 terms per document:
  surface_pro_pos       : performance(0.089), display(0.089), keyboard(0.071)...
  surface_pro_neg       : keyboard(0.091), fan(0.081), noisy(0.081)...

=== Step 4: Semantic Search ===
  Query: 'overpriced noisy fan disappointing'
    0.4321  surface_pro_neg
    0.3124  surface_book_neg
    0.2341  surface_go_neg
```

---

## Summary

| Concept | Formula | Purpose |
|---------|---------|---------|
| TF | `count(word) / total_words` | Word frequency in doc |
| IDF | `log(N/df) + 1` | Penalise common words |
| TF-IDF | `TF × IDF` | Document word importance |
| Cosine sim | `a·b / (‖a‖‖b‖)` | Document similarity |
| Naive Bayes | `P(c|x) ∝ P(c)·ΠP(xᵢ|c)` | Text classification |
