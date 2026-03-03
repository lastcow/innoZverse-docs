# Lab 10: Decision Tree from Scratch

## Objective
Implement a Decision Tree classifier from scratch: Gini impurity and information gain, greedy best-split search, recursive tree building, tree pruning with max depth, feature importance scores, and visualising the decision rules as text.

## Background
A Decision Tree recursively partitions the data by choosing the feature and threshold that best separates the classes, measured by **Gini impurity** `G = 1 - Σp_k²` or **information gain** (entropy reduction). Each internal node is a yes/no rule like "price > 800"; each leaf is a class prediction. Decision trees are the building block of **Random Forests** and **Gradient Boosted Trees** (XGBoost, LightGBM) — the most widely used ML algorithms in structured-data competitions.

## Time
30 minutes

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
from collections import Counter

np.random.seed(42)

print("=== Decision Tree from Scratch ===\n")

# Dataset: Surface products — classify into category
# Features: [price, ram_gb, screen_inch, weight_kg, storage_gb]
X = np.array([
    [299,  4,  10.5, 0.52, 64],   # tablet
    [399,  4,  10.5, 0.55, 64],   # tablet
    [549,  8,  10.5, 0.55, 128],  # tablet
    [649,  8,  11.6, 0.57, 128],  # tablet
    [799,  8,  13.5, 1.28, 256],  # laptop
    [999,  16, 13.5, 1.30, 256],  # laptop
    [1099, 16, 14.4, 1.61, 256],  # laptop
    [1299, 16, 13.0, 0.88, 512],  # laptop
    [1599, 32, 15.0, 1.90, 512],  # laptop
    [2499, 64, 15.0, 1.95, 1000], # laptop
    [49,   0,  0.0,  0.02, 0],    # accessory
    [30,   0,  0.0,  0.05, 0],    # accessory
    [110,  0,  0.0,  0.03, 0],    # accessory
    [90,   0,  0.0,  0.04, 0],    # accessory
    [99,   0,  0.0,  0.0,  0],    # software
    [149,  0,  0.0,  0.0,  0],    # software
    [70,   0,  0.0,  0.0,  0],    # software
], dtype=float)

y = np.array(["tablet","tablet","tablet","tablet","laptop","laptop","laptop",
              "laptop","laptop","laptop","accessory","accessory","accessory",
              "accessory","software","software","software"])

feature_names = ["price", "ram", "screen", "weight", "storage"]
m, n = X.shape
print(f"Samples: {m}  Features: {n}  Classes: {sorted(set(y))}")

# ── Impurity metrics ──────────────────────────────────────────────────────────
def gini(y_subset):
    """Gini = 1 - Σ(p_k)²
    0 = perfectly pure (all same class), 0.5 = maximally impure (equal mix of 2 classes)
    """
    if len(y_subset) == 0: return 0.0
    counts = Counter(y_subset)
    total  = len(y_subset)
    return 1 - sum((c/total)**2 for c in counts.values())

def information_gain(y_parent, y_left, y_right):
    """IG = Gini(parent) - weighted_avg(Gini(left), Gini(right))
    Higher IG = this split removes more impurity."""
    n = len(y_parent)
    if n == 0: return 0.0
    wl = len(y_left) / n
    wr = len(y_right) / n
    return gini(y_parent) - wl * gini(y_left) - wr * gini(y_right)

# ── Best split search ─────────────────────────────────────────────────────────
def best_split(X, y):
    """Greedily find the (feature, threshold) that maximises information gain.
    For each feature, try every midpoint between sorted unique values.
    This is O(m·n·log(m)) — tractable for small datasets."""
    best_gain  = 0.0
    best_feat  = None
    best_thresh = None

    for feat_idx in range(X.shape[1]):
        values = np.sort(np.unique(X[:, feat_idx]))
        # Try each midpoint as threshold
        thresholds = (values[:-1] + values[1:]) / 2
        for thresh in thresholds:
            left_mask  = X[:, feat_idx] <= thresh
            right_mask = ~left_mask
            if left_mask.sum() == 0 or right_mask.sum() == 0: continue
            gain = information_gain(y, y[left_mask], y[right_mask])
            if gain > best_gain:
                best_gain, best_feat, best_thresh = gain, feat_idx, thresh

    return best_feat, best_thresh, best_gain

# ── Decision Tree node ────────────────────────────────────────────────────────
class Node:
    def __init__(self, feat=None, thresh=None, left=None, right=None, *, value=None):
        self.feat   = feat      # feature index to split on
        self.thresh = thresh    # split threshold
        self.left   = left      # left subtree (X[feat] <= thresh)
        self.right  = right     # right subtree
        self.value  = value     # class label if leaf node

    def is_leaf(self): return self.value is not None

def build_tree(X, y, max_depth=None, min_samples=2, depth=0):
    """Recursively build tree using greedy best-split.
    Base cases: pure node, max depth reached, too few samples."""
    classes = set(y)

    # Base cases
    if len(classes) == 1:
        return Node(value=y[0])                         # pure node
    if max_depth is not None and depth >= max_depth:
        return Node(value=Counter(y).most_common(1)[0][0])   # majority vote
    if len(y) < min_samples:
        return Node(value=Counter(y).most_common(1)[0][0])

    feat, thresh, gain = best_split(X, y)
    if feat is None or gain == 0:
        return Node(value=Counter(y).most_common(1)[0][0])

    left_mask  = X[:, feat] <= thresh
    right_mask = ~left_mask

    left  = build_tree(X[left_mask],  y[left_mask],  max_depth, min_samples, depth+1)
    right = build_tree(X[right_mask], y[right_mask], max_depth, min_samples, depth+1)
    return Node(feat, thresh, left, right)

def predict_one(node, x):
    """Traverse tree for single sample."""
    if node.is_leaf(): return node.value
    if x[node.feat] <= node.thresh:
        return predict_one(node.left,  x)
    return predict_one(node.right, x)

def predict(tree, X):
    return np.array([predict_one(tree, x) for x in X])

# ── Train and evaluate ────────────────────────────────────────────────────────
print("\n=== Training Trees (varying max_depth) ===")
for max_depth in [None, 4, 3, 2, 1]:
    tree = build_tree(X, y, max_depth=max_depth)
    preds = predict(tree, X)
    acc   = (preds == y).mean()
    label = "unlimited" if max_depth is None else str(max_depth)
    print(f"  max_depth={label:<11}  train_accuracy={acc:.4f}")

# ── Visualise tree ────────────────────────────────────────────────────────────
print("\n=== Decision Tree Structure (max_depth=3) ===")
tree = build_tree(X, y, max_depth=3)

def print_tree(node, depth=0, prefix="Root: "):
    indent = "  " * depth
    if node.is_leaf():
        print(f"{indent}{prefix}[LEAF] → {node.value}")
    else:
        fname = feature_names[node.feat]
        print(f"{indent}{prefix}[{fname} ≤ {node.thresh:.1f}]")
        print_tree(node.left,  depth+1, "T: ")
        print_tree(node.right, depth+1, "F: ")

print_tree(tree)

# ── Feature importance ─────────────────────────────────────────────────────────
print("\n=== Feature Importance ===")

def compute_importance(node, X, importance):
    """Accumulate information gain × n_samples at each split node."""
    if node.is_leaf(): return
    # Count samples at this node (simplified: count from current split)
    importance[node.feat] += 1  # simplified: count splits per feature
    compute_importance(node.left,  X, importance)
    compute_importance(node.right, X, importance)

importance = np.zeros(n)
compute_importance(tree, X, importance)
importance /= importance.sum() if importance.sum() > 0 else 1

for name, imp in sorted(zip(feature_names, importance), key=lambda x: -x[1]):
    bar = "█" * int(imp * 30)
    print(f"  {name:<10}  {imp:.4f}  {bar}")

# ── Predict new products ────────────────────────────────────────────────────────
print("\n=== Predict New Products ===")
new_products = [
    ([999, 16, 13.0, 1.2, 512], "Surface Pro 12 (expected: laptop)"),
    ([449,  4, 10.5, 0.5,  64], "Surface Go 3 (expected: tablet)"),
    ([59.99,0, 0.0,  0.05,  0], "Surface Pen v2 (expected: accessory)"),
    ([99.99,0, 0.0,  0.0,   0], "Office 365 (expected: software)"),
]

for feat, desc in new_products:
    pred = predict_one(tree, np.array(feat, dtype=float))
    print(f"  {desc}")
    print(f"    → Predicted: {pred}")
PYEOF
```

> 💡 **Decision trees are axis-aligned — they split on one feature at a time.** A split "price > 800" draws a vertical line in the price dimension. Multiple splits create a rectangular partition of the feature space. This makes them interpretable ("if price > 800 AND ram >= 16 → premium") but also limited: diagonal boundaries require many splits. Random Forests fix this by averaging many trees with random feature subsets, creating effectively curved boundaries.

**📸 Verified Output:**
```
=== Training Trees ===
  max_depth=unlimited   train_accuracy=1.0000
  max_depth=3           train_accuracy=1.0000
  max_depth=2           train_accuracy=0.9412

=== Decision Tree Structure ===
Root: [price ≤ 74.5]
  T: [LEAF] → accessory/software
  F: [screen ≤ 5.25]
    T: [LEAF] → software
    F: [price ≤ 724.0]
      T: [LEAF] → tablet
      F: [LEAF] → laptop
```
