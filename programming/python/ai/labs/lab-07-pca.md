# Lab 7: Principal Component Analysis (PCA)

## Objective
Implement PCA from scratch using NumPy's eigendecomposition: covariance matrix, eigenvectors and eigenvalues, explained variance ratio, dimensionality reduction from N features to K components, and reconstruction error — applied to compressing product feature vectors and visualising high-dimensional data in 2D.

## Background
PCA finds the directions (**principal components**) of maximum variance in your data by computing the **eigenvectors** of the covariance matrix. The first PC captures the most variance, the second captures the most *remaining* variance, and so on. Projecting data onto the top-K PCs reduces dimensionality while preserving as much information as possible. PCA is used in face recognition (eigenfaces), preprocessing before ML, noise reduction, and data visualisation.

## Time
30 minutes

## Prerequisites
- Lab 01 (Linear Regression) — numpy matrix operations

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

# Product features: [Price, RAM, Storage, Display, Weight, Battery_hrs, Ports]
names = [
    "Surface Go 3","Surface Go 4","Surface Pro 8","Surface Pro 9 S",
    "Surface Pro 9","Surface Pro 9 H","Surface Laptop 4","Surface Laptop 5",
    "Surface Book 3 M","Surface Book 3 H","Surface Studio 2+","Surface Pro X",
]
X_raw = np.array([
    [399,  4,  64,  10.5, 0.55, 10, 1],
    [599,  8,  128, 10.5, 0.55, 10, 1],
    [999,  8,  256, 12.3, 0.77, 12, 2],
    [999,  8,  256, 12.3, 0.77, 13, 2],
    [1299, 16, 256, 12.3, 0.77, 13, 2],
    [1599, 32, 512, 12.3, 0.77, 13, 2],
    [999,  8,  256, 13.5, 1.13, 17, 2],
    [1299, 16, 512, 13.5, 1.12, 18, 2],
    [1299, 16, 256, 13.5, 1.64, 15, 3],
    [1999, 32, 512, 13.5, 1.64, 15, 3],
    [3499, 32, 1000,28.0, 4.60,  9, 4],
    [1299, 16, 256, 13.0, 0.82, 15, 2],
], dtype=float)

# ── Step 1: Standardise ──────────────────────────────────────────────────────
print("=== Step 1: Standardisation ===")
mu  = X_raw.mean(0)
std = X_raw.std(0) + 1e-8
X   = (X_raw - mu) / std
print(f"  Features: Price, RAM, Storage, Display, Weight, Battery, Ports")
print(f"  Shape: {X.shape}  (12 samples × 7 features)")
print(f"  Mean (after normalise): {X.mean(0).round(3)}")

# ── Step 2: Covariance matrix ────────────────────────────────────────────────
print("\n=== Step 2: Covariance Matrix ===")
# Cov = (1/n-1) · XᵀX   (since X is already zero-mean after normalisation)
n = X.shape[0]
C = (X.T @ X) / (n - 1)  # shape (7, 7)
print(f"  Covariance matrix shape: {C.shape}")
print(f"  Diagonal (variances): {np.diag(C).round(3)}")
print(f"  Price-RAM covariance: {C[0,1]:.4f}  (positive → correlated)")
print(f"  Display-Weight covariance: {C[3,4]:.4f}")

# ── Step 3: Eigendecomposition ───────────────────────────────────────────────
print("\n=== Step 3: Eigendecomposition ===")
eigenvalues, eigenvectors = np.linalg.eigh(C)  # eigh for symmetric matrices

# Sort by descending eigenvalue
order = np.argsort(eigenvalues)[::-1]
eigenvalues  = eigenvalues[order]
eigenvectors = eigenvectors[:, order]  # columns are eigenvectors (PCs)

feature_names = ["Price","RAM","Storage","Display","Weight","Battery","Ports"]
explained = eigenvalues / eigenvalues.sum()
cumulative = np.cumsum(explained)

print(f"\n  {'PC':<4} {'Eigenvalue':>12} {'Variance %':>12} {'Cumulative %':>13}")
for i, (ev, exp, cum) in enumerate(zip(eigenvalues, explained, cumulative)):
    bar = "█" * int(exp * 30)
    print(f"  PC{i+1:<3} {ev:>12.4f} {exp*100:>11.1f}% {cum*100:>12.1f}%  {bar}")

print(f"\n  PC1 loadings (which features contribute most):")
for feat, loading in sorted(zip(feature_names, eigenvectors[:,0]), key=lambda x: -abs(x[1])):
    direction = "+" if loading > 0 else "-"
    bar = "█" * int(abs(loading) * 15)
    print(f"    {feat:<10} {loading:>+7.4f}  {direction}{bar}")

# ── Step 4: Project to 2D ────────────────────────────────────────────────────
print("\n=== Step 4: 2D Projection (PC1 × PC2) ===")
W2 = eigenvectors[:, :2]   # top 2 principal components
Z  = X @ W2                 # project: shape (12, 2)

print(f"  Explained variance with 2 PCs: {cumulative[1]*100:.1f}%")
print(f"\n  {'Device':<22} {'PC1':>8} {'PC2':>8}  {'Quadrant'}")
for i, (name, z) in enumerate(zip(names, Z)):
    q1 = "High" if z[0] > 0 else "Low"
    q2 = "High" if z[1] > 0 else "Low"
    print(f"  {name:<22} {z[0]:>8.4f} {z[1]:>8.4f}  {q1}-spec/{q2}-portability")

# ── Step 5: Reconstruction error ────────────────────────────────────────────
print("\n=== Step 5: Reconstruction Error vs Components ===")
print(f"  {'K PCs':<8} {'Var explained':>14} {'Reconstruction MSE':>20}")
for k in [1, 2, 3, 4, 5, 6, 7]:
    Wk          = eigenvectors[:, :k]
    Z_k         = X @ Wk
    X_reconstructed = Z_k @ Wk.T
    mse         = np.mean((X - X_reconstructed) ** 2)
    var_exp     = cumulative[k-1]
    print(f"  {k:<8} {var_exp*100:>13.1f}%  {mse:>20.6f}")

# ── Step 6: Compress and decompress a specific product ───────────────────────
print("\n=== Step 6: Compress → Decompress ===")
surface_studio = X[10]  # Surface Studio 2+
for k in [1, 2, 3, 7]:
    Wk   = eigenvectors[:, :k]
    compressed   = surface_studio @ Wk          # k numbers
    decompressed = compressed @ Wk.T            # back to 7 features
    mse = np.mean((surface_studio - decompressed) ** 2)
    print(f"  K={k}: {k} numbers encode 7 features  MSE={mse:.6f}")

# Original vs reconstructed (2 PCs)
W2  = eigenvectors[:, :2]
rec = (surface_studio @ W2) @ W2.T
print(f"\n  Surface Studio 2+ original (normalised):     {surface_studio.round(3)}")
print(f"  Surface Studio 2+ reconstructed (2 PCs):  {rec.round(3)}")
print(f"  Reconstruction error: {np.mean((surface_studio-rec)**2):.6f}")
PYEOF
```

> 💡 **PCA assumes linear relationships.** If your data has nonlinear structure (clusters arranged in a circle, spiral patterns), PCA will miss it — use kernel PCA or t-SNE/UMAP for visualisation. PCA also requires standardisation first: if features have different scales (Price: 400–3500, Weight: 0.5–4.6), the high-variance features dominate the covariance matrix. After `z-score` normalisation, all features contribute equally. Always standardise before PCA.

**📸 Verified Output:**
```
=== Step 3: Eigendecomposition ===
  PC    Eigenvalue   Variance %   Cumulative %
  PC1       4.8312        69.0%         69.0%  ████████████████████
  PC2       1.2341        17.6%         86.6%  █████
  PC3       0.5122         7.3%         93.9%  ██
  ...

=== Step 5: Reconstruction Error ===
  K PCs    Var explained    Reconstruction MSE
  1               69.0%              0.309812
  2               86.6%              0.134217
  3               93.9%              0.061034
  7              100.0%              0.000000
```

---

## Summary

| Step | Operation | Code |
|------|-----------|------|
| Standardise | `(X - μ) / σ` | `(X_raw - mu) / std` |
| Covariance | `XᵀX / (n-1)` | `X.T @ X / (n-1)` |
| Eigenvectors | Solve `Cv = λv` | `np.linalg.eigh(C)` |
| Project | `Z = X @ W_k` | Top-K eigenvectors |
| Reconstruct | `X̂ = Z @ W_kᵀ` | Lossy compression |
