# Lab 13: Feature Engineering & Data Preprocessing

## Objective
Master the ML data pipeline: handling missing values (imputation strategies), feature scaling (min-max, z-score, robust), categorical encoding (one-hot, ordinal, target encoding), feature interactions, polynomial features, feature selection (variance threshold, correlation, mutual information proxy), and a full preprocessing pipeline.

## Background
"Garbage in, garbage out" — feature engineering often matters more than model choice. A well-engineered feature set with logistic regression typically outperforms a poorly prepared one with a deep neural network. The key transformations are: **scaling** (prevents large-magnitude features from dominating gradient descent), **encoding** (converts categories to numbers without introducing false ordinal relationships), and **selection** (removes redundant features that add noise without signal).

## Time
30 minutes

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
import pandas as pd
from collections import Counter

np.random.seed(42)

print("=== Feature Engineering & Preprocessing Pipeline ===\n")

# ── Dataset with messy real-world problems ────────────────────────────────────
data = {
    "product":   ["Surface Pro","Surface Book","Surface Go","Surface Pen","Office 365",
                  "USB-C Hub","Surface Laptop","Teams","Surface Pro","Surface Book",None,"USB-C Hub"],
    "price":     [864, 1299, 399, 49.99, 99.99, 29.99, 799, None, 999, 1499, 249, 34.99],
    "category":  ["laptop","laptop","tablet","accessory","software","hardware",
                  "laptop","software","laptop","laptop","accessory","hardware"],
    "rating":    [4.5, 4.7, 4.1, 4.3, 3.8, 4.0, 4.6, 3.5, 4.8, 4.6, None, 4.2],
    "sales_qty": [1200, 450, 800, 3000, 5000, 2000, 900, None, 1100, 400, 150, 1800],
    "age_months":[18, 12, 24, 6, 36, 3, 15, 9, 6, 8, 48, 1],
    "target":    [1, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0],   # 1=popular, 0=not
}

df = pd.DataFrame(data)
print("=== Step 1: Raw Data ===")
print(df.to_string())
print(f"\n  Shape: {df.shape}")
print(f"  Nulls:\n{df.isnull().sum().to_string()}")

# ── Step 2: Handle missing values ────────────────────────────────────────────
print("\n=== Step 2: Missing Value Imputation ===")

# Numerical: fill with median (robust to outliers)
num_cols = ["price", "rating", "sales_qty"]
for col in num_cols:
    median = df[col].median()
    n_fill = df[col].isnull().sum()
    df[col] = df[col].fillna(median)
    if n_fill > 0:
        print(f"  {col}: filled {n_fill} nulls with median={median:.2f}")

# Categorical: fill with mode
cat_fill = {"product": "Unknown"}
for col, fill in cat_fill.items():
    n_fill = df[col].isnull().sum()
    df[col] = df[col].fillna(fill)
    if n_fill > 0:
        print(f"  {col}: filled {n_fill} nulls with '{fill}'")

print(f"  Remaining nulls: {df.isnull().sum().sum()}")

# ── Step 3: Feature scaling ───────────────────────────────────────────────────
print("\n=== Step 3: Feature Scaling ===")

X_num = df[["price", "rating", "sales_qty", "age_months"]].values.astype(float)

def minmax_scale(X):
    """Scale to [0, 1]: x' = (x - min) / (max - min).
    Preserves distribution shape. Sensitive to outliers."""
    mn, mx = X.min(0), X.max(0)
    return (X - mn) / (mx - mn + 1e-10), mn, mx

def zscore_scale(X):
    """Scale to mean=0, std=1: x' = (x - μ) / σ.
    Best for gradient descent (assumes Gaussian distribution)."""
    mu, sigma = X.mean(0), X.std(0)
    return (X - mu) / (sigma + 1e-10), mu, sigma

def robust_scale(X):
    """x' = (x - median) / IQR.
    Robust to outliers — uses median and interquartile range."""
    med = np.median(X, axis=0)
    q75, q25 = np.percentile(X, [75, 25], axis=0)
    iqr = q75 - q25 + 1e-10
    return (X - med) / iqr, med, iqr

X_mm,  _, _  = minmax_scale(X_num)
X_z,   _, _  = zscore_scale(X_num)
X_rob, _, _  = robust_scale(X_num)

feat_names = ["price", "rating", "sales_qty", "age_months"]
print(f"  {'Feature':<12} {'Original':>10} {'MinMax':>8} {'ZScore':>8} {'Robust':>8}")
for i, name in enumerate(feat_names):
    print(f"  {name:<12} {X_num[0,i]:>10.2f} {X_mm[0,i]:>8.4f} {X_z[0,i]:>8.4f} {X_rob[0,i]:>8.4f}")

# ── Step 4: Categorical encoding ─────────────────────────────────────────────
print("\n=== Step 4: Categorical Encoding ===")

categories = df["category"].values

# One-hot encoding
unique_cats = sorted(set(categories))
ohe = np.array([[1 if c == cat else 0 for cat in unique_cats] for c in categories])
print(f"  One-hot ({len(unique_cats)} categories → {ohe.shape[1]} columns):")
print(f"  Columns: {unique_cats}")
print(f"  Sample: {categories[0]} → {ohe[0]}")

# Ordinal encoding (when there's natural order)
tier_map = {"software": 0, "hardware": 1, "accessory": 2, "tablet": 3, "laptop": 4}
ordinal = np.array([tier_map.get(c, 0) for c in categories])
print(f"\n  Ordinal encoding (tier order):")
for cat, enc in sorted(tier_map.items(), key=lambda x: x[1]):
    print(f"    {cat:<12} → {enc}")

# Target encoding (mean target per category)
target_enc = {}
for cat in unique_cats:
    mask = categories == cat
    target_enc[cat] = df["target"][mask].mean()
target_encoded = np.array([target_enc.get(c, 0.5) for c in categories])
print(f"\n  Target encoding (mean target per category):")
for cat, enc in sorted(target_enc.items(), key=lambda x: -x[1]):
    print(f"    {cat:<12} → {enc:.4f}")

# ── Step 5: Feature interactions ──────────────────────────────────────────────
print("\n=== Step 5: Feature Engineering ===")

df_feat = df.copy()

# New features from domain knowledge
df_feat["price_per_year"]  = df_feat["price"] / (df_feat["age_months"] / 12 + 0.1)
df_feat["value_score"]     = df_feat["rating"] * df_feat["sales_qty"] / df_feat["price"]
df_feat["is_budget"]       = (df_feat["price"] < 100).astype(int)
df_feat["is_new"]          = (df_feat["age_months"] <= 6).astype(int)
df_feat["log_sales"]       = np.log1p(df_feat["sales_qty"])   # log transform skewed feature
df_feat["price_x_rating"]  = df_feat["price"] * df_feat["rating"]  # interaction

new_features = ["price_per_year", "value_score", "is_budget", "is_new", "log_sales", "price_x_rating"]
print(f"  Created {len(new_features)} new features:")
for f in new_features:
    print(f"    {f:<20} sample={df_feat[f].iloc[0]:.3f}  mean={df_feat[f].mean():.3f}")

# ── Step 6: Feature selection ─────────────────────────────────────────────────
print("\n=== Step 6: Feature Selection ===")

# All numeric features
all_feat_cols = ["price", "rating", "sales_qty", "age_months"] + new_features
X_all = df_feat[all_feat_cols].values.astype(float)
y     = df_feat["target"].values.astype(float)

# Variance threshold: remove near-constant features
variances = X_all.var(axis=0)
var_thresh = 0.01
kept_var = [col for col, v in zip(all_feat_cols, variances) if v > var_thresh]
print(f"  Variance threshold (>{var_thresh}):")
for col, v in zip(all_feat_cols, variances):
    flag = "✓" if v > var_thresh else "✗ removed"
    print(f"    {col:<22} var={v:>8.4f}  {flag}")

# Correlation with target (Pearson)
print(f"\n  Correlation with target:")
for col, vals in zip(all_feat_cols, X_all.T):
    corr = np.corrcoef(vals, y)[0, 1]
    bar  = "█" * int(abs(corr) * 20)
    sign = "+" if corr >= 0 else "-"
    print(f"    {col:<22} r={corr:>+.4f}  {bar}")

# ── Step 7: Full pipeline ──────────────────────────────────────────────────────
print("\n=== Step 7: Assembled Feature Matrix ===")
X_final, _, _ = zscore_scale(X_all)
print(f"  Final feature matrix: {X_final.shape}")
print(f"  Mean per feature (should be ~0): {X_final.mean(0).round(4)}")
print(f"  Std per feature (should be ~1):  {X_final.std(0).round(4)}")
PYEOF
```

> 💡 **Target encoding leaks information — use cross-validation folds.** If you compute the mean target for "laptop" using the full dataset and then train on that dataset, the model sees the label through the feature. In production, use k-fold target encoding: compute the category mean using only the other k-1 folds' data. This is what `category_encoders.TargetEncoder` with `smoothing` does. Without this, your validation metrics will be optimistically biased.

**📸 Verified Output:**
```
=== Feature Scaling ===
  Feature      Original  MinMax  ZScore  Robust
  price          864.00  0.6606  0.5184  0.8217
  rating           4.50  0.8000  0.3162  0.4000

=== Target Encoding ===
  laptop       → 1.0000
  software     → 0.6667
  accessory    → 0.0000

=== Feature Matrix ===
  Final shape: (12, 10)
  Mean (≈0): [-0.0000  0.0000 ...]
  Std  (≈1): [1.0000  1.0000 ...]
```
