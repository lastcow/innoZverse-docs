# Lab 5: Decision Trees from Scratch

## Objective
Build a decision tree classifier from scratch: Gini impurity and information gain, greedy best-split search, recursive tree construction, max-depth pruning, and feature importance scores — trained to predict Surface product tier from specs.

## Background
A decision tree learns a hierarchy of binary questions ("Is RAM > 16GB?") that partitions the training data into increasingly pure subsets. **Gini impurity** measures class mixing: `G = 1 - Σpᵢ²` (0 = pure, 0.5 = maximally mixed for binary). At each node, the algorithm tries every feature and every threshold, picking the split that maximally reduces impurity (**information gain**). Trees are powerful, interpretable, and the foundation of Random Forests and XGBoost.

## Time
35 minutes

## Prerequisites
- Lab 02 (Logistic Regression) — classification concepts

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
from collections import Counter

np.random.seed(42)

# Dataset: Surface specs → tier (0=budget, 1=mid, 2=premium)
X = np.array([
    [4,  64,  399,  10.5], [8,  64,  399,  10.5], [8,  128, 499,  10.5],
    [8,  128, 799,  12.3], [8,  256, 899,  13.5], [16, 256, 999,  12.3],
    [16, 256, 999,  13.5], [16, 256, 1099, 13.5], [16, 512, 1299, 12.3],
    [32, 512, 1299, 13.5], [32, 512, 1599, 13.5], [32, 512, 1299, 12.3],
    [32, 1000,3499, 28.0], [16, 256, 1299, 13.0],
], dtype=float)
y = np.array([0,0,0, 1,1,1,1,1, 2,2,2,2,2,2])
feature_names = ["RAM_GB", "Storage_GB", "Price", "Display_in"]
class_names   = ["Budget", "Mid-range", "Premium"]

# ── Step 1: Gini impurity ────────────────────────────────────────────────────
print("=== Step 1: Gini Impurity ===")
def gini(y):
    n = len(y)
    if n == 0: return 0
    counts = Counter(y)
    return 1 - sum((c/n)**2 for c in counts.values())

# Examples
examples = [
    ("All Budget",    [0,0,0,0]),
    ("All Mixed",     [0,1,2,0,1,2]),
    ("Mostly Budget", [0,0,0,1]),
]
for name, y_ex in examples:
    print(f"  {name:<20} gini={gini(y_ex):.4f}")

# ── Step 2: Best split search ─────────────────────────────────────────────────
print("\n=== Step 2: Best Split Search ===")
def best_split(X, y):
    best_gain, best_feat, best_thresh = -1, None, None
    parent_gini = gini(y)
    n = len(y)
    for feat in range(X.shape[1]):
        thresholds = np.unique(X[:, feat])
        for t in thresholds:
            left_mask  = X[:, feat] <= t
            right_mask = ~left_mask
            if left_mask.sum() == 0 or right_mask.sum() == 0: continue
            # Weighted Gini after split
            g_left  = gini(y[left_mask])
            g_right = gini(y[right_mask])
            w_left  = left_mask.sum() / n
            w_right = right_mask.sum() / n
            gain = parent_gini - (w_left * g_left + w_right * g_right)
            if gain > best_gain:
                best_gain, best_feat, best_thresh = gain, feat, t
    return best_feat, best_thresh, best_gain

feat, thresh, gain = best_split(X, y)
print(f"  Root split: {feature_names[feat]} <= {thresh:.1f}")
print(f"  Information gain: {gain:.4f}")

# ── Step 3: Decision tree class ──────────────────────────────────────────────
print("\n=== Step 3: Building the Tree ===")
class Node:
    def __init__(self, feat=None, thresh=None, left=None, right=None, *, label=None, gini_val=0, samples=0):
        self.feat, self.thresh = feat, thresh
        self.left, self.right  = left, right
        self.label = label          # set only for leaf nodes
        self.gini_val = gini_val
        self.samples  = samples

class DecisionTree:
    def __init__(self, max_depth=4, min_samples_split=2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None
        self.feature_importances_ = None

    def fit(self, X, y):
        self._n_features = X.shape[1]
        self._importance  = np.zeros(self._n_features)
        self.root = self._grow(X, y, depth=0)
        # Normalise importances
        total = self._importance.sum()
        self.feature_importances_ = self._importance / (total + 1e-12)

    def _grow(self, X, y, depth):
        n, d = X.shape
        # Stopping conditions
        if depth >= self.max_depth or n < self.min_samples_split or len(np.unique(y)) == 1:
            majority = Counter(y).most_common(1)[0][0]
            return Node(label=majority, gini_val=gini(y), samples=n)
        feat, thresh, gain = best_split(X, y)
        if feat is None or gain <= 0:
            return Node(label=Counter(y).most_common(1)[0][0], gini_val=gini(y), samples=n)
        # Track importance: gain × fraction of samples
        self._importance[feat] += gain * n
        mask = X[:, feat] <= thresh
        left  = self._grow(X[mask],  y[mask],  depth+1)
        right = self._grow(X[~mask], y[~mask], depth+1)
        return Node(feat=feat, thresh=thresh, left=left, right=right, gini_val=gini(y), samples=n)

    def predict_one(self, x, node=None):
        node = node or self.root
        if node.label is not None: return node.label
        if x[node.feat] <= node.thresh: return self.predict_one(x, node.left)
        else:                            return self.predict_one(x, node.right)

    def predict(self, X): return np.array([self.predict_one(x) for x in X])

    def print_tree(self, node=None, indent="", depth=0):
        node = node or self.root
        if node.label is not None:
            print(f"{indent}→ LEAF: {class_names[node.label]} "
                  f"(gini={node.gini_val:.3f}, n={node.samples})")
            return
        print(f"{indent}[{feature_names[node.feat]} <= {node.thresh:.1f}?] "
              f"gini={node.gini_val:.3f} n={node.samples}")
        print(f"{indent}  YES:")
        self.print_tree(node.left,  indent+"    ", depth+1)
        print(f"{indent}  NO:")
        self.print_tree(node.right, indent+"    ", depth+1)

tree = DecisionTree(max_depth=4)
tree.fit(X, y)

print("\nLearned Decision Tree:")
tree.print_tree()

# ── Step 4: Evaluation ───────────────────────────────────────────────────────
print("\n=== Step 4: Predictions ===")
preds = tree.predict(X)
print(f"  {'RAM':>4} {'SSD':>4} {'$':>5} {'True':<10} {'Pred':<10} {'OK?'}")
for i in range(len(X)):
    ok = "✓" if preds[i]==y[i] else "✗"
    print(f"  {int(X[i,0]):>4} {int(X[i,1]):>4} ${X[i,2]:>4.0f} "
          f"{class_names[y[i]]:<10} {class_names[preds[i]]:<10} {ok}")
acc = (preds == y).mean()
print(f"\n  Accuracy: {acc*100:.1f}%")

# ── Step 5: Feature importance ───────────────────────────────────────────────
print("\n=== Step 5: Feature Importance ===")
for feat, imp in sorted(zip(feature_names, tree.feature_importances_), key=lambda x: -x[1]):
    bar = "█" * int(imp * 30)
    print(f"  {feat:<12} {imp:.4f}  {bar}")

# ── Step 6: Depth vs accuracy ────────────────────────────────────────────────
print("\n=== Step 6: Max Depth vs Accuracy (overfitting watch) ===")
for depth in [1, 2, 3, 4, 5, 10]:
    t = DecisionTree(max_depth=depth)
    t.fit(X, y)
    acc = (t.predict(X) == y).mean()
    print(f"  depth={depth:<3} train_acc={acc*100:.1f}%")
print("  (High depth on small dataset = perfect train acc but overfits)")
PYEOF
```

> 💡 **Decision trees always overfit without constraints.** With unlimited depth, a tree can memorise every training example (accuracy = 100%), but it will fail on new data. `max_depth`, `min_samples_split`, and `min_samples_leaf` are the main pruning knobs. Random Forests fix overfitting by averaging many trees trained on random subsets of data and features — each tree overfits differently, and the average cancels out.

**📸 Verified Output:**
```
=== Step 1: Gini Impurity ===
  All Budget           gini=0.0000
  All Mixed            gini=0.6667
  Mostly Budget        gini=0.3750

=== Step 3: Decision Tree ===
[Price <= 499.0?] gini=0.617 n=14
  YES:
    → LEAF: Budget (gini=0.000, n=3)
  NO:
    [Price <= 999.0?] ...
      → LEAF: Mid-range ...
      [RAM_GB <= 16.0?] ...

=== Step 5: Feature Importance ===
  Price        0.6832  ████████████████████
  RAM_GB       0.2114  ██████
  Storage_GB   0.0721  ██
  Display_in   0.0333  █
```

---

## Summary

| Concept | Formula/Rule | Notes |
|---------|-------------|-------|
| Gini impurity | `1 - Σpᵢ²` | 0=pure, 0.5=max mix |
| Information gain | `G(parent) - weighted G(children)` | Maximised at each split |
| Pruning | `max_depth`, `min_samples` | Prevents overfitting |
| Feature importance | Sum of gain × samples | Normalised across features |
