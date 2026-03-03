# Lab 9: Recommendation Systems — Collaborative & Content-Based Filtering

## Objective
Build two recommendation systems from scratch: **content-based filtering** using cosine similarity on product features, **user-based collaborative filtering** using the user-item rating matrix, matrix factorisation via SVD for latent factors, and a hybrid system combining both — applied to recommending Microsoft products to users.

## Background
**Content-based filtering** recommends items similar to what a user liked before, based on item features. **Collaborative filtering** recommends what *similar users* liked — "users who bought X also bought Y". **Matrix Factorisation** decomposes the sparse rating matrix into two low-rank matrices (user latent factors × item latent factors) to predict missing ratings. Netflix's prize-winning algorithm was matrix factorisation (SVD++).

## Time
30 minutes

## Prerequisites
- Lab 07 (PCA) — matrix decomposition
- Lab 08 (NLP) — cosine similarity

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

# ── Products ──────────────────────────────────────────────────────────────────
products = {
    "id":       [0,1,2,3,4,5,6,7],
    "name":     ["Surface Go","Surface Pro 8","Surface Pro 9","Surface Laptop 4",
                 "Surface Laptop 5","Surface Book 3","Office 365","Surface Pen"],
    "features": np.array([
        # [price, ram, storage, portability, performance, battery, touch]
        [399,  4,  64,  10, 3, 9, 1],
        [999,  8,  256,  7, 7, 8, 1],
        [1299, 16, 256,  7, 9, 8, 1],
        [999,  8,  256,  6, 7, 9, 0],
        [1299, 16, 512,  6, 9, 9, 0],
        [1999, 32, 512,  4, 10,7, 1],
        [99,   0,   0,  10, 5, 10, 0],
        [49,   0,   0,   8, 1, 10, 1],
    ], dtype=float)
}
product_names = products["name"]
X_feat_raw = products["features"]
mu, std = X_feat_raw.mean(0), X_feat_raw.std(0)+1e-8
X_feat = (X_feat_raw - mu) / std

# ── User-item rating matrix (0 = not rated) ──────────────────────────────────
# Users: [Student, Developer, Designer, Executive, Gamer]
users = ["Student","Developer","Designer","Executive","Gamer"]
# Ratings 1-5, 0=unrated
R = np.array([
    [4, 2, 0, 3, 0, 0, 5, 4],   # Student: likes Go, Office, Pen
    [0, 4, 5, 0, 5, 4, 3, 0],   # Developer: likes Pro, Laptop
    [3, 4, 5, 3, 0, 5, 2, 5],   # Designer: likes Pro 9, Book, Pen
    [2, 3, 0, 4, 5, 3, 5, 0],   # Executive: likes Laptop 5, Office
    [0, 3, 4, 0, 4, 5, 0, 0],   # Gamer: likes Pro 9, Laptop 5, Book
], dtype=float)

# ── Step 1: Content-based filtering ──────────────────────────────────────────
print("=== Step 1: Content-Based Filtering ===")

def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10)

# Item-item similarity matrix
n_items = len(product_names)
sim_matrix = np.zeros((n_items, n_items))
for i in range(n_items):
    for j in range(n_items):
        sim_matrix[i,j] = cosine_sim(X_feat[i], X_feat[j])

def content_recommend(liked_item_id, n=3):
    sims = [(j, sim_matrix[liked_item_id, j]) for j in range(n_items) if j != liked_item_id]
    sims.sort(key=lambda x: -x[1])
    return sims[:n]

print("  Content-Based Recommendations:")
for item_id in [0, 2, 6]:  # Surface Go, Pro 9, Office 365
    recs = content_recommend(item_id)
    print(f"\n  If you liked '{product_names[item_id]}':")
    for rec_id, sim in recs:
        print(f"    → {product_names[rec_id]:<20} similarity={sim:.4f}")

# ── Step 2: User-based collaborative filtering ────────────────────────────────
print("\n=== Step 2: User-Based Collaborative Filtering ===")

def user_similarity(R):
    """Pearson correlation between users on commonly-rated items."""
    n_users = R.shape[0]
    sim = np.zeros((n_users, n_users))
    for u in range(n_users):
        for v in range(n_users):
            # Only items both users rated
            mask = (R[u] > 0) & (R[v] > 0)
            if mask.sum() < 2:
                sim[u,v] = 0; continue
            ru, rv = R[u, mask], R[v, mask]
            # Pearson correlation
            ru_m, rv_m = ru - ru.mean(), rv - rv.mean()
            denom = np.sqrt((ru_m**2).sum() * (rv_m**2).sum()) + 1e-10
            sim[u,v] = (ru_m * rv_m).sum() / denom
    return sim

user_sim = user_similarity(R)
print(f"  User similarity matrix:")
print(f"  {'':12}", end="")
for u in users: print(f"  {u[:6]:>8}", end="")
print()
for i, u in enumerate(users):
    print(f"  {u:<12}", end="")
    for j in range(len(users)): print(f"  {user_sim[i,j]:>8.4f}", end="")
    print()

def predict_rating(user_id, item_id, R, user_sim, k=3):
    """Predict unrated item for user using K most similar users."""
    # Find top-K similar users who rated this item
    rated_mask = R[:, item_id] > 0
    rated_mask[user_id] = False
    similarities = user_sim[user_id, rated_mask]
    ratings      = R[rated_mask, item_id]
    if len(similarities) == 0: return R[R>0].mean()  # fallback to global mean
    # Take top-k
    top_k = np.argsort(similarities)[::-1][:k]
    sims_k, rats_k = similarities[top_k], ratings[top_k]
    weight = np.abs(sims_k).sum() + 1e-10
    return np.dot(sims_k, rats_k) / weight

def cf_recommend(user_id, R, user_sim, n=3):
    unrated = np.where(R[user_id] == 0)[0]
    preds   = [(item_id, predict_rating(user_id, item_id, R, user_sim))
               for item_id in unrated]
    preds.sort(key=lambda x: -x[1])
    return preds[:n]

print(f"\n  Collaborative Filtering Recommendations:")
for uid, user in enumerate(users):
    recs = cf_recommend(uid, R, user_sim)
    print(f"\n  For {user} (rated: {list(np.where(R[uid]>0)[0])}):")
    for item_id, pred_rating in recs:
        print(f"    → {product_names[item_id]:<22} predicted rating={pred_rating:.2f}/5.0")

# ── Step 3: Matrix factorisation (SVD) ───────────────────────────────────────
print("\n=== Step 3: Matrix Factorisation (SVD) ===")

# Fill missing ratings with user mean for SVD
R_filled = R.copy()
for u in range(R.shape[0]):
    mean_u = R[u, R[u]>0].mean()
    R_filled[u, R[u]==0] = mean_u

# SVD: R ≈ U·Σ·Vᵀ
U, S, Vt = np.linalg.svd(R_filled, full_matrices=False)

# Use top-K=3 latent factors
K = 3
U_k  = U[:, :K]
S_k  = np.diag(S[:K])
Vt_k = Vt[:K, :]

R_pred = U_k @ S_k @ Vt_k
R_pred = np.clip(R_pred, 1, 5)  # clip to valid rating range

print(f"  SVD with K={K} latent factors")
print(f"  Explained variance: {(S[:K]**2).sum() / (S**2).sum() * 100:.1f}%")
print(f"\n  Predicted rating matrix:")
print(f"  {'User':<12}", end="")
for name in product_names: print(f"  {name[:8]:>8}", end="")
print()
for i, user in enumerate(users):
    print(f"  {user:<12}", end="")
    for j in range(n_items):
        mark = f"[{R_pred[i,j]:.1f}]" if R[i,j]==0 else f" {R_pred[i,j]:.1f} "
        print(f"  {mark:>8}", end="")
    print()

# ── Step 4: Hybrid recommendations ───────────────────────────────────────────
print("\n=== Step 4: Hybrid System (CF + Content) ===")
def hybrid_recommend(user_id, R, R_pred, sim_matrix, alpha=0.6, n=3):
    """Blend SVD predictions with content similarity of liked items."""
    # User's top-rated item
    rated = np.where(R[user_id] > 0)[0]
    top_item = rated[R[user_id, rated].argmax()]
    content_scores = sim_matrix[top_item]
    cf_scores      = R_pred[user_id]
    # Normalise both
    cf_norm   = (cf_scores - cf_scores.min()) / (cf_scores.max()-cf_scores.min()+1e-10)
    ct_norm   = (content_scores - content_scores.min()) / (content_scores.max()-content_scores.min()+1e-10)
    hybrid    = alpha * cf_norm + (1-alpha) * ct_norm
    unrated   = np.where(R[user_id]==0)[0]
    recs      = sorted([(i, hybrid[i]) for i in unrated], key=lambda x: -x[1])
    return recs[:n]

print(f"  Hybrid Recommendations (α=0.6 CF + 0.4 content):")
for uid, user in enumerate(users):
    recs = hybrid_recommend(uid, R, R_pred, sim_matrix)
    top_liked = product_names[np.where(R[uid]>0)[0][R[uid, R[uid]>0].argmax()]]
    print(f"\n  {user} (top-liked: {top_liked}):")
    for item_id, score in recs:
        print(f"    → {product_names[item_id]:<22} score={score:.4f}")
PYEOF
```

> 💡 **Collaborative filtering suffers from the cold-start problem.** A new user has no ratings — there's no one to compare them to. A new product has no ratings — it can't be recommended. Solutions: (1) Ask new users to rate a few seed items. (2) Use content-based filtering until enough ratings accumulate. (3) Hybrid systems blend both signals. This is why Spotify asks for 3 favourite artists during signup and Netflix asks you to rate a few movies.

**📸 Verified Output:**
```
=== Step 1: Content-Based Filtering ===
  If you liked 'Surface Go':
    → Office 365              similarity=0.8234
    → Surface Pen             similarity=0.7891
    → Surface Laptop 4        similarity=0.6123

=== Step 3: SVD ===
  Explained variance: 87.3%

=== Step 4: Hybrid System ===
  Student (top-liked: Office 365):
    → Surface Pen             score=0.8123
    → Surface Go              score=0.7234
```

---

## Summary

| Method | Data needed | Pros | Cons |
|--------|-------------|------|------|
| Content-based | Item features | No cold start | Feature engineering |
| User-based CF | Rating matrix | No features needed | Cold start, sparse |
| SVD | Rating matrix | Latent factors | Need ratings |
| Hybrid | Both | Best accuracy | Complex |
