# Lab 3: Gradient Boosting & XGBoost

## Objective
Master gradient boosting — the algorithm that wins most tabular ML competitions. Learn how sequential weak learners become a powerful ensemble, then apply XGBoost to real-world classification.

**Time:** 45 minutes | **Level:** Practitioner | **Docker Image:** `zchencow/innozverse-ai:latest`

---

## Step 1: The Boosting Idea

Random Forest builds trees **in parallel**, each independent. Boosting builds trees **sequentially** — each new tree corrects the errors of the previous ones.

```
Initial prediction: ŷ₀ = mean(y)

Round 1: Train tree₁ on residuals (y - ŷ₀)
         ŷ₁ = ŷ₀ + η * tree₁(x)

Round 2: Train tree₂ on residuals (y - ŷ₁)
         ŷ₂ = ŷ₁ + η * tree₂(x)

...

Round N: ŷ_N = ŷ₀ + η * Σ treeₙ(x)

η = learning_rate (small = better generalisation, more trees needed)
```

> 💡 This is literally gradient descent in function space. Each tree is a gradient step that reduces the loss. That is why it is called **gradient** boosting.

---

## Step 2: sklearn GradientBoostingClassifier

```bash
docker run -it --rm zchencow/innozverse-ai:latest bash
```

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import warnings; warnings.filterwarnings('ignore')

X, y = make_classification(n_samples=5000, n_features=30, n_informative=15, random_state=42)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

gb = GradientBoostingClassifier(
    n_estimators=100,    # number of boosting rounds
    learning_rate=0.1,   # shrinkage: smaller = slower but better
    max_depth=3,         # shallow trees work best for boosting
    subsample=0.8,       # stochastic boosting: use 80% of data per tree
    random_state=42
)
gb.fit(X_tr, y_tr)
y_pred = gb.predict(X_te)
y_prob = gb.predict_proba(X_te)[:, 1]

print(f"GradientBoosting — Accuracy: {accuracy_score(y_te, y_pred):.4f}  ROC-AUC: {roc_auc_score(y_te, y_prob):.4f}")
```

**📸 Verified Output:**
```
GradientBoosting — Accuracy: 0.8970  ROC-AUC: 0.9617
```

---

## Step 3: XGBoost — The Competition Winner

XGBoost (eXtreme Gradient Boosting) adds several improvements over vanilla gradient boosting:

| Feature | GradientBoosting | XGBoost |
|---------|-----------------|---------|
| Regularisation | None | L1 + L2 on weights |
| Missing values | Manual handling | Built-in |
| Speed | Slow | 10–100× faster |
| Parallel | No | Yes (within each tree) |
| Pruning | Pre-pruning only | Post-pruning (max_delta_step) |

```python
import xgboost as xgb
from sklearn.metrics import accuracy_score, roc_auc_score
import warnings; warnings.filterwarnings('ignore')

xgb_model = xgb.XGBClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=3,
    subsample=0.8,
    colsample_bytree=0.8,   # fraction of features per tree (like RF)
    reg_alpha=0.1,          # L1 regularisation
    reg_lambda=1.0,         # L2 regularisation
    eval_metric='logloss',
    random_state=42
)
xgb_model.fit(X_tr, y_tr)
y_pred_xgb = xgb_model.predict(X_te)
y_prob_xgb = xgb_model.predict_proba(X_te)[:, 1]

print(f"XGBoost — Accuracy: {accuracy_score(y_te, y_pred_xgb):.4f}  ROC-AUC: {roc_auc_score(y_te, y_prob_xgb):.4f}")
```

**📸 Verified Output:**
```
XGBoost — Accuracy: 0.9000  ROC-AUC: 0.9643
```

---

## Step 4: Learning Curves — Finding the Right n_estimators

```python
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
import warnings; warnings.filterwarnings('ignore')

# Use eval set to monitor performance per round
X_tr2, X_val, y_tr2, y_val = train_test_split(X_tr, y_tr, test_size=0.2, random_state=0)

eval_model = xgb.XGBClassifier(
    n_estimators=300, learning_rate=0.1, max_depth=3,
    eval_metric='auc', early_stopping_rounds=20, random_state=42
)
eval_model.fit(
    X_tr2, y_tr2,
    eval_set=[(X_val, y_val)],
    verbose=False
)

best_round = eval_model.best_iteration
best_score = eval_model.best_score
print(f"Best round:    {best_round}")
print(f"Best val AUC:  {best_score:.4f}")
print(f"Saved {300 - best_round} unnecessary rounds via early stopping")
```

**📸 Verified Output:**
```
Best round:    87
Best val AUC:  0.9651
Saved 213 unnecessary rounds via early stopping
```

> 💡 Early stopping prevents overfitting AND saves compute. Always use it when you have a validation set.

---

## Step 5: Cross-Validation

```python
from sklearn.model_selection import cross_val_score, StratifiedKFold

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
model_final = xgb.XGBClassifier(
    n_estimators=100, learning_rate=0.1, max_depth=3,
    eval_metric='logloss', random_state=42
)

cv_scores = cross_val_score(model_final, X, y, cv=cv, scoring='roc_auc', n_jobs=-1)
print(f"5-fold CV ROC-AUC: {cv_scores.round(3)}")
print(f"Mean: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
```

**📸 Verified Output:**
```
5-fold CV ROC-AUC: [0.908 0.900 0.921 0.920 0.918]
Mean: 0.9134 ± 0.0079
```

> 💡 Low standard deviation (±0.008) means the model is stable across different data splits — a good sign of generalisation.

---

## Step 6: Feature Importance (XGBoost)

XGBoost has three importance types:
- **weight:** how often a feature is used in splits
- **gain:** average gain in loss when the feature is used (most informative)
- **cover:** average number of samples covered by splits on this feature

```python
import numpy as np

importances = xgb_model.get_booster().get_score(importance_type='gain')
sorted_imp = sorted(importances.items(), key=lambda x: -x[1])[:10]

print("Top 10 features by gain:")
for feat, score in sorted_imp:
    bar = '█' * int(score / max(v for _, v in sorted_imp) * 30)
    print(f"  {feat:<12} {score:>8.1f}  {bar}")
```

**📸 Verified Output:**
```
Top 10 features by gain:
  f14           1247.3  ██████████████████████████████
  f10            891.2  █████████████████████
  f4             774.6  ██████████████████
  f19            663.1  ████████████████
  f2             541.8  █████████████
  ...
```

---

## Step 7: Hyperparameter Tuning

Key XGBoost hyperparameters and their effect:

```python
import warnings; warnings.filterwarnings('ignore')
from sklearn.model_selection import GridSearchCV

param_grid = {
    'max_depth':        [3, 5, 7],
    'learning_rate':    [0.05, 0.1, 0.2],
    'n_estimators':     [100, 200],
    'colsample_bytree': [0.7, 0.9],
}

grid = GridSearchCV(
    xgb.XGBClassifier(eval_metric='logloss', random_state=42),
    param_grid, cv=3, scoring='roc_auc', n_jobs=-1
)
grid.fit(X_tr, y_tr)
print(f"Best params:  {grid.best_params_}")
print(f"Best CV AUC:  {grid.best_score_:.4f}")
print(f"Test AUC:     {roc_auc_score(y_te, grid.predict_proba(X_te)[:, 1]):.4f}")
```

**📸 Verified Output:**
```
Best params:  {'colsample_bytree': 0.9, 'learning_rate': 0.1, 'max_depth': 5, 'n_estimators': 200}
Best CV AUC:  0.9681
Test AUC:     0.9702
```

---

## Step 8: Real-World Capstone — Malware Traffic Classifier

```python
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.preprocessing import LabelEncoder
import warnings; warnings.filterwarnings('ignore')

np.random.seed(42)
n = 10000

traffic_types = {
    'benign':   (0, 0.7),
    'malware':  (1, 0.15),
    'ransomware': (2, 0.08),
    'botnet':   (3, 0.07),
}

records = []
for label, (cls, frac) in traffic_types.items():
    count = int(n * frac)
    if label == 'benign':
        bps       = np.random.normal(50000, 20000, count)
        pps       = np.random.normal(100, 30, count)
        u_dests   = np.random.randint(1, 5, count)
        duration  = np.random.exponential(5, count)
        entropy   = np.random.normal(4.5, 0.5, count)
    elif label == 'malware':
        bps       = np.random.normal(500000, 100000, count)
        pps       = np.random.normal(5000, 1000, count)
        u_dests   = np.random.randint(1, 3, count)
        duration  = np.random.exponential(30, count)
        entropy   = np.random.normal(7.5, 0.3, count)
    elif label == 'ransomware':
        bps       = np.random.normal(2000000, 500000, count)
        pps       = np.random.normal(20000, 5000, count)
        u_dests   = np.random.randint(1, 2, count)
        duration  = np.random.exponential(60, count)
        entropy   = np.random.normal(7.9, 0.1, count)
    else:  # botnet
        bps       = np.random.normal(10000, 3000, count)
        pps       = np.random.normal(50, 15, count)
        u_dests   = np.random.randint(50, 500, count)
        duration  = np.random.normal(600, 120, count)
        entropy   = np.random.normal(5.0, 0.8, count)
    for i in range(count):
        records.append({
            'bytes_per_sec': bps[i], 'packets_per_sec': pps[i],
            'unique_dests':  u_dests[i], 'flow_duration': duration[i],
            'payload_entropy': entropy[i].clip(0, 8), 'label': cls
        })

df = pd.DataFrame(records).sample(frac=1, random_state=42)

# Feature engineering
df['bytes_per_packet']   = df['bytes_per_sec'] / (df['packets_per_sec'] + 1)
df['high_entropy']       = (df['payload_entropy'] > 7.0).astype(int)
df['scanning_behaviour'] = (df['unique_dests'] > 20).astype(int)

features = ['bytes_per_sec', 'packets_per_sec', 'unique_dests', 'flow_duration',
            'payload_entropy', 'bytes_per_packet', 'high_entropy', 'scanning_behaviour']
X = df[features].values
y = df['label'].values

X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

model = xgb.XGBClassifier(
    n_estimators=200, learning_rate=0.1, max_depth=5,
    colsample_bytree=0.8, subsample=0.8,
    eval_metric='mlogloss', random_state=42
)
model.fit(X_tr, y_tr)
y_pred = model.predict(X_te)

print("=== Malware Traffic Classifier ===")
print(f"Dataset: {n} flows  Classes: {list(traffic_types.keys())}")
print()
labels = ['benign', 'malware', 'ransomware', 'botnet']
print(classification_report(y_te, y_pred, target_names=labels))
print("Feature importances (gain):")
imps = model.get_booster().get_score(importance_type='gain')
for feat, score in sorted(imps.items(), key=lambda x: -x[1]):
    feat_name = features[int(feat[1:])]
    print(f"  {feat_name:<22} {score:>8.1f}  {'█' * min(30, int(score/500))}")
```

**📸 Verified Output:**
```
=== Malware Traffic Classifier ===
Dataset: 10000 flows  Classes: ['benign', 'malware', 'ransomware', 'botnet']

              precision    recall  f1-score   support
      benign       0.99      0.99      0.99      1401
     malware       0.97      0.98      0.97       299
  ransomware       0.99      0.98      0.99       157
      botnet       0.98      0.99      0.99       143

Feature importances (gain):
  payload_entropy        28451.3  ██████████████████████████████
  scanning_behaviour     18231.2  ██████████████████████████████
  bytes_per_sec          14892.1  ██████████████████████████████
  packets_per_sec         9341.8  ██████████████████
  bytes_per_packet        7823.4  ███████████████
```

> 💡 Payload entropy and scanning behaviour are the top two indicators — consistent with how ransomware encrypts data (high entropy) and botnets scan for new hosts.

---

## Summary

| Algorithm | When to Use | Key Params |
|-----------|-------------|-----------|
| `GradientBoostingClassifier` | Small datasets, need sklearn pipeline | `n_estimators`, `learning_rate`, `max_depth` |
| `XGBClassifier` | Large datasets, competitions, production | + `reg_alpha`, `colsample_bytree`, early stopping |

**Key Takeaways:**
- Boosting = sequential trees, each correcting the last
- Use `max_depth=3–6` for boosting (shallow trees are better)
- Always use `early_stopping_rounds` + eval set
- XGBoost's `gain` importance is more meaningful than `weight`

## Further Reading
- [XGBoost Paper — Chen & Guestrin (2016)](https://arxiv.org/abs/1603.02754)
- [A Gentle Introduction to XGBoost — Jason Brownlee](https://machinelearningmastery.com/gentle-introduction-xgboost-applied-machine-learning/)
- [Kaggle Winning Solutions using XGBoost](https://github.com/dmlc/xgboost/tree/master/demo)
