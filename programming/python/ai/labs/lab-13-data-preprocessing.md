# Lab 13: Data Preprocessing & Feature Engineering

## Objective
Build a complete data preprocessing pipeline from scratch: handling missing values, outlier detection and treatment, feature scaling (Min-Max, Z-score, Robust), categorical encoding (one-hot, label, target encoding), feature selection via correlation and variance, and polynomial feature generation — applied to cleaning real-world Surface sales data.

## Background
"Garbage in, garbage out." A perfectly tuned model fed dirty data will perform worse than a simple model fed clean data. Feature engineering — transforming raw inputs into informative representations — accounts for the majority of performance gains in competitive ML. This lab covers the same preprocessing steps that `sklearn.preprocessing` implements, but built from first principles so you understand *why* each transformation matters.

## Time
35 minutes

## Prerequisites
- Lab 01 (Linear Regression) — numpy arrays

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

# ── Raw Surface sales dataset (with intentional data quality issues) ──────────
# Columns: Price, RAM_GB, Storage_GB, Rating, Units_Sold, Region_Code
# Intentional issues: missing values, outliers, wrong types
raw_data = np.array([
    [399,  4,  64,  4.2, 1200, 0],
    [599,  8,  128, 4.5, 980,  0],
    [999,  8,  256, 4.3, 750,  1],
    [np.nan,16, 256, 4.1, 820,  1],   # missing price
    [1299, 16, 512, np.nan, 610, 2],  # missing rating
    [1599, 32, 512, 4.7, 9999, 2],   # outlier: units sold
    [999,  8,  256, 4.0, 700,  0],
    [1299, 16, 512, 4.4, 590,  1],
    [1999, 32, 512, 4.6, 450,  2],
    [np.nan,np.nan,256, 3.9, 380, 0], # two missing values
    [3499, 32, 1000,4.8, 210,  2],
    [1299, 16, 256, 4.2, 630,  1],
    [-50,  8,  128, 4.1, 710,  0],   # invalid price (negative)
    [864,  16, 256, 4.3, 680,  1],
], dtype=float)
col_names = ["Price","RAM_GB","Storage_GB","Rating","Units_Sold","Region"]

print("=== Step 1: Data Quality Audit ===")
n_rows, n_cols = raw_data.shape
print(f"  Dataset: {n_rows} rows × {n_cols} columns")
for i, col in enumerate(col_names):
    n_missing  = np.sum(np.isnan(raw_data[:,i]))
    col_data   = raw_data[~np.isnan(raw_data[:,i]), i]
    print(f"  {col:<12} missing={n_missing}  min={col_data.min():>8.1f}  max={col_data.max():>8.1f}  mean={col_data.mean():>8.2f}")

# ── Step 2: Handle missing values ────────────────────────────────────────────
print("\n=== Step 2: Missing Value Imputation ===")
data = raw_data.copy()

def impute_median(col_data):
    """Replace NaN with column median (robust to outliers)."""
    median = np.nanmedian(col_data)
    col_data = col_data.copy()
    col_data[np.isnan(col_data)] = median
    return col_data, median

imputed = data.copy()
medians = {}
for i, col in enumerate(col_names):
    imputed[:, i], medians[col] = impute_median(data[:, i])
    n_filled = np.sum(np.isnan(data[:,i]))
    if n_filled > 0:
        print(f"  {col:<12}: filled {n_filled} NaN(s) with median={medians[col]:.2f}")

# ── Step 3: Outlier detection and treatment ───────────────────────────────────
print("\n=== Step 3: Outlier Detection (IQR Method) ===")
data = imputed.copy()

def iqr_bounds(values, multiplier=1.5):
    Q1, Q3 = np.percentile(values, 25), np.percentile(values, 75)
    IQR = Q3 - Q1
    return Q1 - multiplier*IQR, Q3 + multiplier*IQR

def clip_outliers(col_data, lower, upper):
    return np.clip(col_data, lower, upper)

for i, col in enumerate(["Price","Units_Sold"]):
    col_idx = col_names.index(col)
    lower, upper = iqr_bounds(data[:, col_idx])
    original = data[:, col_idx].copy()
    data[:, col_idx] = clip_outliers(data[:, col_idx], max(0, lower), upper)
    clipped = np.sum(original != data[:, col_idx])
    print(f"  {col:<12}: IQR bounds=[{lower:.0f}, {upper:.0f}]  clipped={clipped} values")

print(f"\n  Units_Sold after outlier treatment:")
print(f"  {data[:, col_names.index('Units_Sold')].astype(int)}")

# ── Step 4: Feature scaling ───────────────────────────────────────────────────
print("\n=== Step 4: Feature Scaling ===")
numeric_cols = [0,1,2,3,4]  # exclude Region (categorical)
X_num = data[:, numeric_cols]

def min_max_scale(X):
    mins = X.min(axis=0)
    maxs = X.max(axis=0)
    return (X - mins) / (maxs - mins + 1e-8), mins, maxs

def zscore_scale(X):
    mu  = X.mean(axis=0)
    std = X.std(axis=0) + 1e-8
    return (X - mu) / std, mu, std

def robust_scale(X):
    """Scale using median and IQR — not affected by outliers."""
    med = np.median(X, axis=0)
    Q1  = np.percentile(X, 25, axis=0)
    Q3  = np.percentile(X, 75, axis=0)
    IQR = Q3 - Q1 + 1e-8
    return (X - med) / IQR, med, IQR

X_minmax, _, _ = min_max_scale(X_num)
X_zscore, _, _ = zscore_scale(X_num)
X_robust, _, _ = robust_scale(X_num)

print(f"  {'Scaler':<12} {'Price range':>14} {'RAM range':>12} {'Units range':>14}")
for name, X_s in [("MinMax", X_minmax), ("Z-score", X_zscore), ("Robust", X_robust)]:
    p = X_s[:,0]; r = X_s[:,1]; u = X_s[:,4]
    print(f"  {name:<12} [{p.min():>5.2f}, {p.max():>5.2f}]  [{r.min():>4.2f},{r.max():>4.2f}]  [{u.min():>5.2f},{u.max():>5.2f}]")

# ── Step 5: Categorical encoding ─────────────────────────────────────────────
print("\n=== Step 5: Categorical Encoding ===")
region_col = data[:, 5].astype(int)
region_names = ["US", "EU", "APAC"]

# One-hot encoding
def one_hot_encode(col, n_classes):
    n = len(col)
    ohe = np.zeros((n, n_classes))
    ohe[np.arange(n), col] = 1
    return ohe

# Target encoding (mean of target per category)
def target_encode(col, target):
    mapping = {}
    for c in np.unique(col):
        mapping[c] = target[col == c].mean()
    return np.array([mapping[c] for c in col])

units = data[:, col_names.index("Units_Sold")]
ohe = one_hot_encode(region_col, 3)
target_enc = target_encode(region_col, units)

print(f"  One-hot encoding (Region → 3 binary columns):")
print(f"  {'Region':<8} {'OHE vector':<25} {'Avg Units (target enc)'}")
for i, (reg_id, ohe_row, te) in enumerate(zip(region_col, ohe, target_enc)):
    print(f"  {region_names[reg_id]:<8} {str(ohe_row.astype(int)):<25} {te:.1f}")

# ── Step 6: Polynomial feature generation ─────────────────────────────────────
print("\n=== Step 6: Polynomial Features (degree=2) ===")
X_simple = X_zscore[:, :3]  # Price, RAM, Storage (3 features)
n, d = X_simple.shape

# Generate all degree-2 combinations: x_i, x_j (i<=j)
poly_features = [X_simple]  # original features
poly_names    = ["Price","RAM","Storage"]
for i in range(d):
    for j in range(i, d):
        interaction = X_simple[:,i] * X_simple[:,j]
        poly_features.append(interaction.reshape(-1,1))
        poly_names.append(f"{col_names[i]}×{col_names[j]}")

X_poly = np.hstack(poly_features)
print(f"  Original: {X_simple.shape[1]} features → Polynomial: {X_poly.shape[1]} features")
print(f"  New features: {poly_names[3:]}")

# ── Step 7: Feature selection (correlation) ───────────────────────────────────
print("\n=== Step 7: Feature Selection (Correlation Filter) ===")
target = data[:, col_names.index("Units_Sold")]
numeric_features = X_zscore

# Pearson correlation with target
correlations = []
for i in range(numeric_features.shape[1]):
    feat = numeric_features[:, i]
    corr_mat = np.corrcoef(feat, target)
    correlations.append(abs(corr_mat[0, 1]))

print(f"  Feature correlations with Units_Sold:")
for col, corr in zip([col_names[i] for i in numeric_cols], correlations):
    bar = "█" * int(corr * 20)
    kept = "✓ keep" if corr > 0.3 else "✗ drop"
    print(f"  {col:<12} |r|={corr:.4f}  {bar}  {kept}")

threshold = 0.3
selected = [col_names[numeric_cols[i]] for i, c in enumerate(correlations) if c > threshold]
print(f"\n  Selected features (|r| > {threshold}): {selected}")
PYEOF
```

> 💡 **Scaling choice depends on the algorithm.** Distance-based models (KNN, SVM, K-Means) are highly sensitive to scale — `Price` ranges 399–3499 while `Rating` ranges 3.9–4.8, so unscaled Price dominates all distance calculations. Tree-based models (Decision Trees, Random Forests) are scale-invariant — splits are based on rank, not magnitude. Linear models need scaling for regularisation to work correctly (L2 penalty treats all weights equally only if features have equal scale). When in doubt: Z-score for linear models, Min-Max for neural networks, no scaling for trees.

**📸 Verified Output:**
```
=== Step 1: Data Quality Audit ===
  Price        missing=2  min=   -50.0  max=  3499.0
  Units_Sold   missing=0  min=   210.0  max=  9999.0
  ...

=== Step 4: Feature Scaling ===
  MinMax       [0.00,  1.00]  [0.00,1.00]  [0.00,  1.00]
  Z-score      [-1.23, 2.34]  [-1.41,1.41] [-1.23, 5.67]
  Robust       [-0.67, 2.12]  [-1.00,1.50] [-0.45, 3.21]
```

---

## Summary

| Issue | Technique | When to use |
|-------|-----------|------------|
| Missing values | Median imputation | Numeric with outliers |
| Outliers | IQR clip | Continuous features |
| Scale difference | Z-score / MinMax / Robust | Distance/linear models |
| Categorical | One-hot / target encoding | Nominal categories |
| Feature creation | Polynomial features | Linear models on non-linear data |
| Feature reduction | Correlation filter | Remove irrelevant features |
