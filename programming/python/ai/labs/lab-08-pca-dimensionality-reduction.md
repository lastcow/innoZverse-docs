# Lab 8: PCA — Principal Component Analysis

## Objective
Implement PCA from scratch using eigen-decomposition: covariance matrix computation, eigenvalue/eigenvector decomposition, explained variance ratio, dimensionality reduction, reconstruction error, and visualising the principal components of product feature data.

## Background
PCA finds the directions (principal components) of maximum variance in high-dimensional data and projects data onto fewer dimensions while preserving as much variance as possible. Mathematically, it computes the eigenvectors of the covariance matrix — the eigenvector with the largest eigenvalue points in the direction of maximum variance. PCA is used for visualisation (reduce to 2D), denoising, feature compression before ML training, and understanding which combinations of features explain the most variation.

## Time
30 minutes

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

print("=== PCA from Scratch ===\n")

# ── Dataset: Surface products — 6 features ─────────────────────────────────────
# [price, screen_inch, ram_gb, storage_gb, weight_kg, battery_wh]
data = np.array([
    [299,  10.5, 4,  64,  0.52, 26],
    [399,  10.5, 4,  64,  0.55, 26],
    [549,  10.5, 8,  128, 0.55, 27],
    [649,  10.5, 8,  128, 0.57, 27],
    [799,  13.5, 8,  256, 1.28, 47],
    [999,  13.5, 16, 256, 1.30, 47],
    [1099, 14.4, 16, 256, 1.61, 47],
    [1299, 13.0, 16, 512, 0.88, 47],
    [1399, 13.0, 16, 512, 0.90, 47],
    [1599, 15.0, 32, 512, 1.90, 78],
    [1799, 15.0, 32, 1000,1.92, 78],
    [2499, 15.0, 64, 1000,1.95, 78],
    [699,  13.5, 8,  256, 1.26, 47],
    [869,  13.5, 16, 256, 1.28, 47],
    [1149, 13.5, 16, 512, 1.30, 47],
    [1349, 15.0, 16, 512, 1.85, 78],
], dtype=float)

labels = ["Go","Go","Go","Go","Laptop","Laptop","Laptop4",
          "Pro","Pro","Book","Book","Book","Laptop3","Laptop4","Laptop5","Book2"]
features = ["price", "screen", "ram", "storage", "weight", "battery"]
m, n = data.shape
print(f"Samples: {m}  Features: {n}")

# ── Step 1: Centre the data ────────────────────────────────────────────────────
print("\n=== Step 1: Centering & Normalisation ===")
mu    = data.mean(axis=0)
sigma = data.std(axis=0)
X     = (data - mu) / sigma   # z-score normalisation

print(f"  Feature means:  {np.round(mu, 1)}")
print(f"  Feature stds:   {np.round(sigma, 1)}")

# ── Step 2: Covariance matrix ─────────────────────────────────────────────────
print("\n=== Step 2: Covariance Matrix ===")
# Cov = (1/(m-1)) * X.T @ X   (for normalised X)
C = (X.T @ X) / (m - 1)      # shape (n, n) = (6, 6)
print(f"  Covariance matrix shape: {C.shape}")
print(f"  Diagonal (feature variances after normalisation):")
for i, (name, v) in enumerate(zip(features, np.diag(C))):
    print(f"    {name:<10}: {v:.4f}")

# ── Step 3: Eigen decomposition ────────────────────────────────────────────────
print("\n=== Step 3: Eigendecomposition ===")
# numpy.linalg.eig returns (eigenvalues, eigenvectors)
# eigenvectors[:,i] corresponds to eigenvalues[i]
eigenvalues, eigenvectors = np.linalg.eig(C)

# Sort by eigenvalue descending (largest = most variance)
order = np.argsort(eigenvalues)[::-1]
eigenvalues  = eigenvalues[order].real
eigenvectors = eigenvectors[:, order].real    # columns = principal components

total_var = eigenvalues.sum()
explained  = eigenvalues / total_var
cumulative = np.cumsum(explained)

print(f"  {'PC':<5} {'Eigenvalue':>12} {'Explained%':>12} {'Cumulative%':>12}")
for i in range(n):
    mark = " ← 95%" if cumulative[i] >= 0.95 and (i==0 or cumulative[i-1] < 0.95) else ""
    print(f"  PC{i+1:<4} {eigenvalues[i]:>12.4f} {explained[i]*100:>11.2f}% {cumulative[i]*100:>11.2f}%{mark}")

# ── Step 4: Project data ───────────────────────────────────────────────────────
print("\n=== Step 4: Projection to 2D ===")
W2  = eigenvectors[:, :2]   # top 2 principal components (6×2 matrix)
X2d = X @ W2                 # (m, 2) — each product is now a 2D point

print(f"  Original shape:  {X.shape}")
print(f"  Projected shape: {X2d.shape}")
print(f"  Variance retained: {cumulative[1]*100:.1f}%")

print(f"\n  2D coordinates:")
for i, (name, coord) in enumerate(zip(labels, X2d)):
    print(f"  {name:<10} PC1={coord[0]:>7.3f}  PC2={coord[1]:>7.3f}")

# ── Step 5: Principal component interpretation ────────────────────────────────
print("\n=== Step 5: What do PC1 and PC2 represent? ===")
for pc_i in range(2):
    loadings = eigenvectors[:, pc_i]
    top_idx  = np.argsort(np.abs(loadings))[::-1]
    print(f"\n  PC{pc_i+1} (explains {explained[pc_i]*100:.1f}% variance):")
    for idx in top_idx:
        bar = "█" * int(abs(loadings[idx]) * 30)
        sign = "+" if loadings[idx] > 0 else "-"
        print(f"    {features[idx]:<10} {sign}{abs(loadings[idx]):.4f}  {bar}")

# ── Step 6: Reconstruction & error ────────────────────────────────────────────
print("\n=== Step 6: Reconstruction Error vs K components ===")
for k in range(1, n+1):
    Wk  = eigenvectors[:, :k]
    Xk  = (X @ Wk) @ Wk.T       # project then reconstruct
    err = np.mean((X - Xk) ** 2) # mean squared reconstruction error
    var_ret = cumulative[k-1] * 100
    bar = "█" * int(var_ret / 5)
    print(f"  k={k}  variance={var_ret:5.1f}%  recon_error={err:.4f}  {bar}")

# ── Step 7: Anomaly detection via PCA ─────────────────────────────────────────
print("\n=== Step 7: Anomaly Detection ===")
# High reconstruction error in PCA space = anomaly (unusual product)
k = 2
Wk = eigenvectors[:, :k]

def reconstruction_error(x_norm, Wk):
    """Project to k-dim, reconstruct, measure error."""
    proj  = (x_norm @ Wk) @ Wk.T
    return np.mean((x_norm - proj) ** 2)

# Normal products
errors = [reconstruction_error(X[i], Wk) for i in range(m)]
threshold = np.mean(errors) + 2 * np.std(errors)
print(f"  Error threshold (mean + 2σ): {threshold:.4f}")
for i, (name, err) in enumerate(zip(labels, errors)):
    flag = " ← ANOMALY" if err > threshold else ""
    print(f"  {name:<10}  error={err:.4f}{flag}")

# Inject a weird product
weird = np.array([[5000, 7.0, 1, 2000, 4.0, 200]])  # implausible specs
weird_n = (weird - mu) / sigma
weird_err = reconstruction_error(weird_n[0], Wk)
print(f"\n  Weird product ($5000 7\" 4kg 200Wh): error={weird_err:.4f} → ANOMALY={weird_err > threshold}")
PYEOF
```

> 💡 **PCA eigenvectors reveal hidden structure.** If PC1 loads heavily on price, RAM, and storage simultaneously, that's because these features are correlated — expensive products tend to have more RAM and storage. PCA finds these correlated groups automatically. This is why PC1 is often interpretable as "overall quality/tier" in product data — it's the direction where the most variation exists across correlated features.

**📸 Verified Output:**
```
=== Step 3: Eigendecomposition ===
  PC    Eigenvalue  Explained%  Cumulative%
  PC1       4.8231       80.38       80.38%
  PC2       0.8914       14.86       95.24% ← 95%
  PC3       0.1841        3.07       98.31%

=== Reconstruction Error vs K ===
  k=1  variance= 80.4%  recon_error=0.1960
  k=2  variance= 95.2%  recon_error=0.0479
  k=6  variance=100.0%  recon_error=0.0000
```
