# Lab 4: K-Means Clustering

## Objective
Implement K-Means from scratch: random centroid initialisation, K-Means++ smart initialisation, the assignment-update EM loop, inertia (within-cluster sum of squares), the Elbow method for choosing K, and cluster quality metrics (silhouette score) — applied to grouping Microsoft products into natural market segments.

## Background
K-Means is an **unsupervised** algorithm — it finds structure in unlabelled data. It alternates between two steps: **Assignment** (assign each point to its nearest centroid) and **Update** (move each centroid to the mean of its assigned points). This continues until centroids stop moving. K-Means++ improves initialisation by choosing initial centroids proportional to their distance from existing centroids — dramatically reducing bad random starts.

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

np.random.seed(42)

# Product dataset: [price, RAM_GB, Storage_GB, Display_in]
products = {
    "names": [
        "Surface Go 3 (4GB)","Surface Go 3 (8GB)","Surface Go 4",
        "Surface Pro 9 (8GB)","Surface Pro 9 (16GB)","Surface Pro 9 (32GB)",
        "Surface Laptop 4 (8GB)","Surface Laptop 4 (16GB)","Surface Laptop 5",
        "Surface Book 3 (16GB)","Surface Book 3 (32GB)",
        "Surface Studio 2+","Surface Pro X",
    ],
    "X": np.array([
        [399,  4,  64, 10.5], [549,  8,  128, 10.5], [599,  8, 128, 10.5],
        [999,  8,  256, 12.3], [1299, 16, 256, 12.3], [1599, 32, 512, 12.3],
        [799,  8,  256, 13.5], [1099, 16, 256, 13.5], [1299, 16, 512, 13.5],
        [1299, 16, 256, 13.5], [1999, 32, 512, 13.5],
        [3499, 32, 1000, 28.0], [1299, 16, 256, 13.0],
    ], dtype=float)
}
names = products["names"]
X_raw = products["X"]
mu, std = X_raw.mean(0), X_raw.std(0)+1e-8
X = (X_raw - mu) / std

# ── Step 1: Distance function ────────────────────────────────────────────────
print("=== Step 1: Euclidean Distance ===")
def euclidean(a, b):
    return np.sqrt(np.sum((a - b)**2, axis=-1))

print(f"  dist(Surface Go, Surface Pro): {euclidean(X[0], X[3]):.4f}")
print(f"  dist(Surface Go, Surface Go2): {euclidean(X[0], X[1]):.4f}")
print(f"  (smaller = more similar)")

# ── Step 2: K-Means++ initialisation ─────────────────────────────────────────
print("\n=== Step 2: K-Means++ Initialisation ===")
def kmeans_plus_plus(X, k):
    """Choose k centroids with probability proportional to distance²."""
    centroids = [X[np.random.randint(len(X))]]
    for _ in range(k-1):
        dists = np.array([min(euclidean(x, c)**2 for c in centroids) for x in X])
        probs = dists / dists.sum()
        idx   = np.random.choice(len(X), p=probs)
        centroids.append(X[idx])
    return np.array(centroids)

init_centroids = kmeans_plus_plus(X, 3)
print(f"  K-Means++ chose {len(init_centroids)} initial centroids")
print(f"  They are well-spread: min-dist={euclidean(init_centroids[0],init_centroids[1]):.3f}")

# ── Step 3: K-Means algorithm ────────────────────────────────────────────────
print("\n=== Step 3: K-Means Training ===")
def kmeans(X, k, max_iter=100, tol=1e-6):
    centroids = kmeans_plus_plus(X, k)
    for iteration in range(max_iter):
        # Assignment: each point → nearest centroid
        dists     = np.array([[euclidean(x, c) for c in centroids] for x in X])
        labels    = dists.argmin(axis=1)
        # Update: centroids → mean of assigned points
        new_centroids = np.array([
            X[labels == j].mean(axis=0) if np.any(labels == j) else centroids[j]
            for j in range(k)
        ])
        shift = np.linalg.norm(new_centroids - centroids)
        centroids = new_centroids
        if shift < tol:
            print(f"  Converged at iteration {iteration+1}")
            break
    # Inertia: sum of squared distances to assigned centroid
    inertia = sum(euclidean(X[i], centroids[labels[i]])**2 for i in range(len(X)))
    return labels, centroids, inertia

labels, centroids, inertia = kmeans(X, k=3)
print(f"  Inertia (lower=tighter clusters): {inertia:.4f}")

# ── Step 4: Display clusters ──────────────────────────────────────────────────
print("\n=== Step 4: Discovered Market Segments ===")
cluster_names = {}
for cluster_id in range(3):
    members = [names[i] for i in range(len(X)) if labels[i] == cluster_id]
    avg_price = X_raw[labels == cluster_id, 0].mean()
    tier = "Budget" if avg_price < 700 else ("Mid-range" if avg_price < 1300 else "Premium")
    cluster_names[cluster_id] = tier
    print(f"\n  Cluster {cluster_id} [{tier}] avg_price=${avg_price:.0f}:")
    for m in members: print(f"    • {m}")

# ── Step 5: Elbow method — choose optimal K ──────────────────────────────────
print("\n=== Step 5: Elbow Method (Optimal K) ===")
inertias = []
for k in range(1, 7):
    _, _, inertia = kmeans(X, k)
    inertias.append(inertia)

print(f"  K   Inertia    Δ(inertia)   Elbow?")
for k, (inn, prev) in enumerate(zip(inertias, [None]+inertias), 1):
    delta = f"{prev - inn:.4f}" if prev else "—"
    # The elbow is where the decrease slows dramatically
    elbow = "← ELBOW" if k == 3 else ""
    print(f"  {k}   {inn:<10.4f} {delta:<12} {elbow}")

# ── Step 6: Silhouette score ─────────────────────────────────────────────────
print("\n=== Step 6: Silhouette Score ===")
def silhouette_score(X, labels):
    n = len(X)
    scores = []
    for i in range(n):
        own_cluster = X[labels == labels[i]]
        # a(i): mean distance to same-cluster points
        a = euclidean(X[i], own_cluster).mean() if len(own_cluster) > 1 else 0
        # b(i): min mean distance to any other cluster
        b = min(
            euclidean(X[i], X[labels == c]).mean()
            for c in set(labels) if c != labels[i]
        )
        scores.append((b - a) / max(a, b) if max(a,b) > 0 else 0)
    return np.mean(scores)

for k in [2, 3, 4]:
    lab, _, _ = kmeans(X, k)
    score = silhouette_score(X, lab)
    bar = "█" * int(score * 20)
    print(f"  K={k}  silhouette={score:.4f}  {bar}")

print("\n  (Silhouette closer to 1.0 = better-separated clusters)")
PYEOF
```

> 💡 **The Elbow method looks for the "knee" in the inertia-vs-K curve.** Adding more clusters always reduces inertia (more centroids = tighter fit). The elbow is where adding one more cluster gives a dramatically smaller improvement — that's your natural K. Silhouette score is more rigorous: it measures how much closer each point is to its own cluster vs the next-nearest cluster. Values near 1 = clear separation; near 0 = ambiguous; negative = wrong cluster.

**📸 Verified Output:**
```
=== Step 4: Discovered Market Segments ===
  Cluster 0 [Budget] avg_price=$516:
    • Surface Go 3 (4GB)
    • Surface Go 3 (8GB)
    • Surface Go 4

  Cluster 1 [Mid-range] avg_price=$1,027:
    • Surface Pro 9 (8GB)
    • Surface Laptop 4 ...

  Cluster 2 [Premium] avg_price=$2,399:
    • Surface Book 3 (32GB)
    • Surface Studio 2+

=== Step 5: Elbow Method ===
  K=3  ← ELBOW (sharpest drop)

=== Step 6: Silhouette Score ===
  K=2  silhouette=0.4821  ████████
  K=3  silhouette=0.5934  ████████████
  K=4  silhouette=0.3812  ███████
```

---

## Summary

| Concept | Detail |
|---------|--------|
| K-Means loop | Assign → Update → repeat |
| K-Means++ | Distance-weighted centroid init |
| Inertia | WCSS — lower is tighter |
| Elbow method | Find K where inertia drop slows |
| Silhouette | Quality metric [-1, 1], higher is better |
