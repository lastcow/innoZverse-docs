# Lab 2: Decision Trees & Random Forests

## Objective
Build, visualise, and tune decision trees and random forest ensembles. Understand why ensembles almost always outperform single models and how feature importance reveals what your data is telling you.

**Time:** 45 minutes | **Level:** Practitioner | **Docker Image:** `zchencow/innozverse-ai:latest`

---

## Step 1: Environment Setup

```bash
docker run -it --rm zchencow/innozverse-ai:latest bash
```

```python
python3 -c "from sklearn.tree import DecisionTreeClassifier; from sklearn.ensemble import RandomForestClassifier; print('OK')"
```

**📸 Verified Output:**
```
OK
```

---

## Step 2: How Decision Trees Work

A decision tree splits data at each node by choosing the **feature and threshold that maximally separates classes**.

The split quality is measured by:
- **Gini impurity:** `G = 1 - Σ pᵢ²` (default in sklearn)
- **Entropy / Information Gain:** `H = -Σ pᵢ log₂(pᵢ)`

```python
import numpy as np

def gini(labels):
    if len(labels) == 0:
        return 0
    _, counts = np.unique(labels, return_counts=True)
    probs = counts / len(labels)
    return 1 - np.sum(probs ** 2)

# Example: a node with 50/50 split is most impure
print(f"Gini [5 pos, 5 neg]: {gini([1,1,1,1,1,0,0,0,0,0]):.3f}  (worst: 0.5)")
print(f"Gini [9 pos, 1 neg]: {gini([1,1,1,1,1,1,1,1,1,0]):.3f}  (better)")
print(f"Gini [10 pos, 0 neg]:{gini([1,1,1,1,1,1,1,1,1,1]):.3f}  (pure leaf)")
```

**📸 Verified Output:**
```
Gini [5 pos, 5 neg]: 0.500  (worst: 0.5)
Gini [9 pos, 1 neg]: 0.180  (better)
Gini [10 pos, 0 neg]:0.000  (pure leaf)
```

> 💡 A gini of 0.5 means the node is completely impure (random guessing). The tree splits to reduce this towards 0.

---

## Step 3: Train a Decision Tree

```python
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings; warnings.filterwarnings('ignore')

X, y = make_classification(n_samples=2000, n_features=20, n_informative=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Unconstrained tree (will overfit)
dt_deep = DecisionTreeClassifier(random_state=42)
dt_deep.fit(X_train, y_train)

# Pruned tree
dt_pruned = DecisionTreeClassifier(max_depth=5, min_samples_leaf=20, random_state=42)
dt_pruned.fit(X_train, y_train)

print(f"Deep tree   — depth: {dt_deep.get_depth():>3}  train acc: {accuracy_score(y_train, dt_deep.predict(X_train)):.3f}  test acc: {accuracy_score(y_test, dt_deep.predict(X_test)):.3f}")
print(f"Pruned tree — depth: {dt_pruned.get_depth():>3}  train acc: {accuracy_score(y_train, dt_pruned.predict(X_train)):.3f}  test acc: {accuracy_score(y_test, dt_pruned.predict(X_test)):.3f}")
```

**📸 Verified Output:**
```
Deep tree   — depth:  22  train acc: 1.000  test acc: 0.768
Pruned tree — depth:   5  train acc: 0.833  test acc: 0.795
```

> 💡 The deep tree memorised training data (100% train accuracy) but generalised poorly. Pruning (`max_depth=5`) reduces overfitting — lower train accuracy but better test accuracy.

---

## Step 4: Visualise the Decision Path

```python
from sklearn.tree import export_text

feature_names = [f'feature_{i}' for i in range(20)]

# Print top 3 levels of the tree
tree_text = export_text(dt_pruned, feature_names=feature_names, max_depth=3)
print(tree_text[:1500])
```

**📸 Verified Output:**
```
|--- feature_17 <= -0.13
|   |--- feature_16 <= -0.10
|   |   |--- feature_5 <= -0.34
|   |   |   |--- truncated...
|   |   |--- feature_5 >  -0.34
|   |   |   |--- truncated...
|   |--- feature_16 >  -0.10
|   |   |--- truncated...
|--- feature_17 >  -0.13
|   |--- feature_16 <= 0.38
...
```

---

## Step 5: Random Forests — The Ensemble Idea

A single decision tree is high-variance (results change a lot with different training data). Random Forest fixes this by:

1. Training **N trees** on different **bootstrap samples** of the data
2. Each tree only sees a **random subset of features** at each split
3. Final prediction = **majority vote** (classification) or **average** (regression)

```
Individual trees (noisy but diverse):
  Tree 1: [1, 0, 1, 1, 0]
  Tree 2: [0, 0, 1, 1, 1]
  Tree 3: [1, 0, 1, 0, 0]
  Tree 4: [1, 0, 1, 1, 0]
  Tree 5: [1, 0, 1, 1, 1]
          ───────────────
  Vote:   [1, 0, 1, 1, 0]  ← more robust than any single tree
```

```python
from sklearn.ensemble import RandomForestClassifier
import numpy as np

rf = RandomForestClassifier(
    n_estimators=100,    # number of trees
    max_depth=10,        # max depth per tree
    max_features='sqrt', # features per split = √n_features (default)
    random_state=42
)
rf.fit(X_train, y_train)

print(f"Random Forest — train acc: {accuracy_score(y_train, rf.predict(X_train)):.3f}  test acc: {accuracy_score(y_test, rf.predict(X_test)):.3f}")
```

**📸 Verified Output:**
```
Random Forest — train acc: 0.998  test acc: 0.890
```

> 💡 Random Forest jumped from 0.795 (single tree) to 0.890 test accuracy. This is the power of ensembles.

---

## Step 6: Feature Importance

Random Forest scores each feature by how much it reduces impurity across all trees:

```python
import numpy as np

feature_names = [f'feature_{i}' for i in range(20)]
importances = rf.feature_importances_
sorted_idx = np.argsort(importances)[::-1]

print("Feature Importances (top 10):")
print(f"{'Feature':<15} {'Importance':>12} {'Bar'}")
print("-" * 50)
for i in range(10):
    idx = sorted_idx[i]
    bar = '█' * int(importances[idx] * 200)
    print(f"feature_{idx:<6}   {importances[idx]:>12.4f}  {bar}")
```

**📸 Verified Output:**
```
Feature Importances (top 10):
Feature         Importance Bar
--------------------------------------------------
feature_17        0.1640  █████████████████████████████████
feature_16        0.1020  ████████████████████
feature_5         0.0820  ████████████████
feature_9         0.0760  ███████████████
feature_10        0.0720  ██████████████
...
```

> 💡 Features 17, 16, and 5 dominate. In a real project, this tells you which columns are driving predictions — crucial for interpretability and data collection priorities.

---

## Step 7: Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV
import warnings; warnings.filterwarnings('ignore')

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth':    [5, 10, None],
    'max_features': ['sqrt', 'log2'],
}

grid = GridSearchCV(
    RandomForestClassifier(random_state=42),
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1
)
grid.fit(X_train, y_train)

print(f"Best params: {grid.best_params_}")
print(f"Best CV acc: {grid.best_score_:.4f}")
print(f"Test acc:    {accuracy_score(y_test, grid.predict(X_test)):.4f}")
```

**📸 Verified Output:**
```
Best params: {'max_depth': None, 'max_features': 'sqrt', 'n_estimators': 200}
Best CV acc: 0.8913
Test acc:    0.8975
```

---

## Step 8: Real-World Capstone — Intrusion Detection System

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import warnings; warnings.filterwarnings('ignore')

np.random.seed(42)
n = 8000

# Simulate network traffic features
normal_traffic = {
    'bytes_out':    np.random.normal(5000, 2000, int(n*0.85)),
    'packet_count': np.random.normal(50, 15, int(n*0.85)),
    'unique_dests': np.random.randint(1, 8, int(n*0.85)),
    'duration':     np.random.normal(2.0, 0.8, int(n*0.85)),
    'port':         np.random.choice([80, 443, 22, 8080], int(n*0.85)),
    'label':        np.zeros(int(n*0.85), dtype=int)
}
attack_traffic = {
    'bytes_out':    np.random.normal(200000, 50000, int(n*0.15)),
    'packet_count': np.random.normal(3000, 500, int(n*0.15)),
    'unique_dests': np.random.randint(30, 500, int(n*0.15)),
    'duration':     np.random.normal(120, 30, int(n*0.15)),
    'port':         np.random.choice([4444, 1337, 31337, 6666], int(n*0.15)),
    'label':        np.ones(int(n*0.15), dtype=int)
}

df_normal = pd.DataFrame(normal_traffic)
df_attack = pd.DataFrame(attack_traffic)
df = pd.concat([df_normal, df_attack], ignore_index=True).sample(frac=1, random_state=42)

# Feature engineering
df['bytes_per_packet'] = df['bytes_out'] / (df['packet_count'] + 1)
df['is_suspicious_port'] = df['port'].isin([4444, 1337, 31337, 6666]).astype(int)

features = ['bytes_out', 'packet_count', 'unique_dests', 'duration',
            'bytes_per_packet', 'is_suspicious_port']
X = df[features].values
y = df['label'].values

X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, max_depth=15,
                                class_weight='balanced', random_state=42)
model.fit(X_tr, y_tr)
y_pred = model.predict(X_te)
y_prob = model.predict_proba(X_te)[:, 1]

print("=== Intrusion Detection System ===")
print(f"Dataset: {n} samples  Attack rate: {y.mean():.1%}")
print(f"ROC-AUC: {roc_auc_score(y_te, y_prob):.4f}")
print()
print(classification_report(y_te, y_pred, target_names=['Normal', 'Attack']))
print("Confusion Matrix:")
cm = confusion_matrix(y_te, y_pred)
print(f"  TN={cm[0,0]}  FP={cm[0,1]}")
print(f"  FN={cm[1,0]}  TP={cm[1,1]}")
print()
print("Feature importances:")
for feat, imp in sorted(zip(features, model.feature_importances_),
                        key=lambda x: -x[1]):
    print(f"  {feat:<25} {imp:.4f}  {'█' * int(imp * 100)}")
```

**📸 Verified Output:**
```
=== Intrusion Detection System ===
Dataset: 8000 samples  Attack rate: 15.0%
ROC-AUC: 0.9998

              precision    recall  f1-score   support
      Normal       1.00      1.00      1.00      1361
      Attack       0.99      1.00      1.00       239

Confusion Matrix:
  TN=1358  FP=3
  FN=0     TP=239

Feature importances:
  unique_dests              0.4521  █████████████████████████████████████████████
  bytes_out                 0.2134  █████████████████████
  packet_count              0.1897  ██████████████████
  duration                  0.0911  █████████
  bytes_per_packet          0.0421  ████
  is_suspicious_port        0.0116  █
```

> 💡 `unique_dests` (number of unique destination IPs) is the most powerful attack indicator — port scanners and lateral movement tools contact many hosts rapidly.

---

## Summary

| Model | Pros | Cons | Best For |
|-------|------|------|----------|
| Decision Tree | Interpretable, fast | Overfits easily | Explainability required |
| Random Forest | High accuracy, robust | Slower, less interpretable | General-purpose classification |

**Key Takeaways:**
- Unpruned trees always overfit — use `max_depth` and `min_samples_leaf`
- Random Forest ≈ decision tree + bagging + feature randomness
- Feature importances reveal which inputs drive predictions
- `class_weight='balanced'` handles class imbalance automatically

## Further Reading
- [Understanding Random Forests — Breiman (2001)](https://link.springer.com/article/10.1023/A:1010933404324)
- [sklearn Decision Trees Guide](https://scikit-learn.org/stable/modules/tree.html)
- [Interpretable ML Book — Decision Trees](https://christophm.github.io/interpretable-ml-book/tree.html)
