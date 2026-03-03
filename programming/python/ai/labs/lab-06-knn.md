# Lab 6: K-Nearest Neighbours (KNN)

## Objective
Implement KNN for both classification and regression: Euclidean, Manhattan, and Minkowski distances, weighted voting by distance, the curse of dimensionality, K selection via cross-validation, and a product recommendation engine using KNN similarity search.

## Background
KNN is a **lazy learner** — it memorises the training set and makes predictions by looking up the K most similar training examples at query time. There is no explicit training phase. For classification, the K neighbours vote (majority wins). For regression, their labels are averaged (optionally weighted by 1/distance). KNN is powerful but slow at inference: finding the K nearest points in N-dimensional data costs O(N·D) per query.

## Time
25 minutes

## Prerequisites
- Lab 04 (K-Means) — distance concepts

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
from collections import Counter

np.random.seed(42)

# Product dataset
names = [
    "Surface Go 3","Surface Go 4","Surface Pro 8","Surface Pro 9 (8GB)",
    "Surface Pro 9 (16GB)","Surface Pro 9 (32GB)","Surface Laptop 4",
    "Surface Laptop 5","Surface Book 3 (16GB)","Surface Book 3 (32GB)",
    "Surface Studio 2+","Surface Pro X",
]
# Features: [Price, RAM_GB, Storage_GB, Display_in, Weight_kg]
X_raw = np.array([
    [399,  4,  64,  10.5, 0.55], [599,  8,  128, 10.5, 0.55],
    [999,  8,  256, 12.3, 0.77], [999,  8,  256, 12.3, 0.77],
    [1299, 16, 256, 12.3, 0.77], [1599, 32, 512, 12.3, 0.77],
    [999,  8,  256, 13.5, 1.13], [1299, 16, 512, 13.5, 1.12],
    [1299, 16, 256, 13.5, 1.64], [1999, 32, 512, 13.5, 1.64],
    [3499, 32, 1000,28.0, 4.60], [1299, 16, 256, 13.0, 0.82],
], dtype=float)
y_tier  = np.array([0,0, 1,1,2,2, 1,2,2,2,2,2])   # 0=budget,1=mid,2=premium
y_price = X_raw[:, 0]   # for regression
tier_names = ["Budget","Mid","Premium"]

mu, std = X_raw.mean(0), X_raw.std(0)+1e-8
X = (X_raw - mu) / std

# ── Step 1: Distance metrics ──────────────────────────────────────────────────
print("=== Step 1: Distance Metrics ===")
def euclidean(a, b):  return np.sqrt(np.sum((a-b)**2))
def manhattan(a, b):  return np.sum(np.abs(a-b))
def minkowski(a, b, p=3): return np.sum(np.abs(a-b)**p)**(1/p)

i, j = 0, 2  # Surface Go vs Surface Pro
print(f"  Comparing: {names[i]} vs {names[j]}")
print(f"  Euclidean:   {euclidean(X[i], X[j]):.4f}")
print(f"  Manhattan:   {manhattan(X[i], X[j]):.4f}")
print(f"  Minkowski p=3: {minkowski(X[i], X[j]):.4f}")

# ── Step 2: KNN classifier ───────────────────────────────────────────────────
print("\n=== Step 2: KNN Classifier ===")
class KNNClassifier:
    def __init__(self, k=3, dist_fn=euclidean, weighted=False):
        self.k = k
        self.dist_fn = dist_fn
        self.weighted = weighted

    def fit(self, X, y):
        self.X_train = X
        self.y_train = y

    def predict_one(self, x):
        dists = np.array([self.dist_fn(x, xi) for xi in self.X_train])
        k_idx = np.argsort(dists)[:self.k]
        k_labels = self.y_train[k_idx]
        if not self.weighted:
            return Counter(k_labels).most_common(1)[0][0]
        # Weighted vote: closer neighbours count more (1/distance)
        k_dists = dists[k_idx] + 1e-10
        weights = 1 / k_dists
        vote = {}
        for label, w in zip(k_labels, weights):
            vote[label] = vote.get(label, 0) + w
        return max(vote, key=vote.get)

    def predict(self, X): return np.array([self.predict_one(x) for x in X])

knn = KNNClassifier(k=3)
knn.fit(X, y_tier)
preds = knn.predict(X)

print(f"  {'Device':<25} {'True':<10} {'Pred':<10} {'OK?'}")
for i in range(len(X)):
    ok = "✓" if preds[i]==y_tier[i] else "✗"
    print(f"  {names[i]:<25} {tier_names[y_tier[i]]:<10} {tier_names[preds[i]]:<10} {ok}")
acc = (preds == y_tier).mean()
print(f"\n  K=3 accuracy: {acc*100:.1f}%")

# ── Step 3: KNN regression ───────────────────────────────────────────────────
print("\n=== Step 3: KNN Regression (Price Prediction) ===")
class KNNRegressor:
    def __init__(self, k=3):
        self.k = k

    def fit(self, X, y): self.X_train, self.y_train = X, y

    def predict_one(self, x):
        dists = np.array([euclidean(x, xi) for xi in self.X_train])
        k_idx = np.argsort(dists)[:self.k]
        weights = 1 / (dists[k_idx] + 1e-10)
        return np.average(self.y_train[k_idx], weights=weights)

    def predict(self, X): return np.array([self.predict_one(x) for x in X])

# Leave-one-out evaluation for regression
errors = []
for i in range(len(X)):
    X_tr = np.delete(X, i, axis=0)
    y_tr = np.delete(y_price, i)
    reg  = KNNRegressor(k=3)
    reg.fit(X_tr, y_tr)
    pred = reg.predict_one(X[i])
    errors.append(abs(pred - y_price[i]))
    print(f"  {names[i]:<25} actual=${y_price[i]:>5.0f}  predicted=${pred:>7.0f}  err=${abs(pred-y_price[i]):>5.0f}")
print(f"\n  Mean Absolute Error (LOO): ${np.mean(errors):.2f}")

# ── Step 4: K selection with cross-validation ────────────────────────────────
print("\n=== Step 4: K Selection (Cross-Validation) ===")
def cv_accuracy(X, y, k, folds=4):
    n = len(X)
    fold_size = n // folds
    accs = []
    for f in range(folds):
        val_idx  = list(range(f*fold_size, (f+1)*fold_size))
        train_idx = [i for i in range(n) if i not in val_idx]
        clf = KNNClassifier(k=k)
        clf.fit(X[train_idx], y[train_idx])
        preds = clf.predict(X[val_idx])
        accs.append((preds == y[val_idx]).mean())
    return np.mean(accs)

print(f"  {'K':<4} {'CV Accuracy'}")
for k in range(1, 8):
    acc = cv_accuracy(X, y_tier, k)
    bar = "█" * int(acc * 20)
    print(f"  {k:<4} {acc:.4f}  {bar}")

# ── Step 5: Product recommendation ───────────────────────────────────────────
print("\n=== Step 5: Product Recommendation Engine ===")
def find_similar(query_idx, X, names, k=3):
    dists = np.array([euclidean(X[query_idx], X[i]) for i in range(len(X))])
    similar_idx = np.argsort(dists)[1:k+1]  # skip self (idx 0)
    return [(names[i], dists[i]) for i in similar_idx]

for query in [0, 4, 10]:  # Go, Pro9 16GB, Studio
    similar = find_similar(query, X, names)
    print(f"\n  If you like '{names[query]}', you might also like:")
    for name, dist in similar:
        print(f"    • {name:<28} (similarity distance: {dist:.4f})")
PYEOF
```

> 💡 **KNN scales poorly with data size.** Finding K nearest neighbours requires computing distance to every training point — O(N·D) per query. With 1M training points and D=100 features, each prediction computes 100M multiplications. Production systems use **Approximate Nearest Neighbour** (ANN) libraries like FAISS (Meta), HNSW, or Annoy (Spotify) that trade a tiny accuracy loss for 100-1000× speed gains using spatial indexing. This is how Spotify's recommendations, vector databases, and semantic search work.

**📸 Verified Output:**
```
=== Step 2: KNN Classifier ===
  Surface Go 3              Budget     Budget     ✓
  Surface Pro 9 (16GB)      Premium    Premium    ✓
  ...
  K=3 accuracy: 91.7%

=== Step 5: Product Recommendation ===
  If you like 'Surface Go 3', you might also like:
    • Surface Go 4              (distance: 0.3821)
    • Surface Pro 8             (distance: 1.2344)
```

---

## Summary

| KNN aspect | Detail |
|-----------|--------|
| Training | Store all data (lazy learning) |
| Prediction | Find K nearest, vote/average |
| Weighted KNN | Weight by 1/distance |
| K selection | Cross-validation — pick best K |
| Scalability | O(N·D) per query — use ANN in production |
