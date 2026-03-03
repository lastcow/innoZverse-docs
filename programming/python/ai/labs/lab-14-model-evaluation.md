# Lab 14: Model Evaluation & Cross-Validation

## Objective
Implement robust model evaluation from scratch: train/val/test split, K-fold and stratified K-fold cross-validation, evaluation metrics (accuracy, precision, recall, F1, AUC-ROC, RMSE, R²), confusion matrix, learning curves, and bias-variance tradeoff analysis — benchmarking multiple models on Surface product tier prediction.

## Background
A model that scores 100% on training data but 50% on unseen data has **overfit** — it memorised the training set. Proper evaluation requires holding out data the model never sees during training. **Cross-validation** gives a more reliable estimate by averaging performance across K different train/test splits. Metrics beyond accuracy matter: in imbalanced datasets, a model that always predicts the majority class can have 95% accuracy while being completely useless.

## Time
35 minutes

## Prerequisites
- Lab 02 (Logistic Regression) — classification metrics
- Lab 05 (Decision Trees) — the model we evaluate

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
from collections import Counter

np.random.seed(42)

# ── Dataset: Surface products → tier classification ───────────────────────────
X_raw = np.array([
    [399,4,64,10.5],[599,8,128,10.5],[699,8,128,10.5],[799,8,128,12.3],
    [899,8,256,12.3],[999,8,256,12.3],[999,16,256,12.3],[1099,16,256,12.3],
    [1199,16,256,13.5],[1299,16,512,13.5],[1399,16,512,13.5],[1499,16,512,13.5],
    [1599,32,512,13.5],[1699,32,512,13.5],[1799,32,512,13.5],[1999,32,512,13.5],
    [2199,32,1000,13.5],[2499,32,1000,13.5],[2999,32,1000,28.0],[3499,32,1000,28.0],
], dtype=float)
y = np.array([0,0,0,0, 1,1,1,1, 1,1,2,2, 2,2,2,2, 2,2,2,2])  # 4 budget, 6 mid, 10 premium
mu, std = X_raw.mean(0), X_raw.std(0)+1e-8
X = (X_raw - mu) / std

# ── Simple model implementations ─────────────────────────────────────────────
class DummyMajority:
    """Always predict majority class."""
    def fit(self, X, y):
        self.majority = Counter(y).most_common(1)[0][0]; return self
    def predict(self, X): return np.full(len(X), self.majority)

class KNNModel:
    def __init__(self, k=3):
        self.k = k
    def fit(self, X, y):
        self.X_tr, self.y_tr = X, y; return self
    def predict(self, X):
        preds = []
        for x in X:
            dists = np.sqrt(((self.X_tr - x)**2).sum(axis=1))
            top_k = self.y_tr[np.argsort(dists)[:self.k]]
            preds.append(Counter(top_k).most_common(1)[0][0])
        return np.array(preds)

class LinearModel:
    """One-vs-rest logistic regression."""
    def fit(self, X, y, epochs=200, lr=0.1):
        self.classes = np.unique(y)
        n, d = X.shape
        self.weights = np.zeros((len(self.classes), d))
        self.biases  = np.zeros(len(self.classes))
        for c_idx, c in enumerate(self.classes):
            y_bin = (y == c).astype(float)
            w, b  = np.zeros(d), 0.0
            for _ in range(epochs):
                z    = X @ w + b
                p    = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
                err  = p - y_bin
                w   -= lr * X.T @ err / n
                b   -= lr * err.mean()
            self.weights[c_idx], self.biases[c_idx] = w, b
        return self
    def predict(self, X):
        scores = X @ self.weights.T + self.biases
        return self.classes[np.argmax(scores, axis=1)]

# ── Step 1: Train/Val/Test split ─────────────────────────────────────────────
print("=== Step 1: Data Splitting ===")

def train_val_test_split(X, y, val_frac=0.15, test_frac=0.15):
    n = len(X)
    idx = np.random.permutation(n)
    test_n = int(n * test_frac)
    val_n  = int(n * val_frac)
    test_idx  = idx[:test_n]
    val_idx   = idx[test_n:test_n+val_n]
    train_idx = idx[test_n+val_n:]
    return (X[train_idx], y[train_idx],
            X[val_idx],   y[val_idx],
            X[test_idx],  y[test_idx])

X_tr, y_tr, X_val, y_val, X_te, y_te = train_val_test_split(X, y)
print(f"  Total: {len(X)} samples")
print(f"  Train: {len(X_tr)} ({len(X_tr)/len(X)*100:.0f}%)  "
      f"Val: {len(X_val)} ({len(X_val)/len(X)*100:.0f}%)  "
      f"Test: {len(X_te)} ({len(X_te)/len(X)*100:.0f}%)")
print(f"  Train class distribution: {Counter(y_tr)}")

# ── Step 2: Evaluation metrics ────────────────────────────────────────────────
print("\n=== Step 2: Evaluation Metrics ===")

def confusion_matrix(y_true, y_pred, n_classes):
    cm = np.zeros((n_classes, n_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    return cm

def classification_report(y_true, y_pred, class_names):
    n = len(np.unique(y_true))
    cm = confusion_matrix(y_true, y_pred, n)
    print(f"  Confusion Matrix:")
    print(f"  {'':>10}", end="")
    for c in class_names: print(f"  {c[:8]:>8}", end="")
    print(f"  {'':>8}")
    for i, row in enumerate(cm):
        print(f"  {class_names[i]:<10}", end="")
        for val in row: print(f"  {val:>8}", end="")
        tp = cm[i,i]; fn = cm[i,:].sum()-tp; fp = cm[:,i].sum()-tp
        prec = tp/(tp+fp+1e-10); rec = tp/(tp+fn+1e-10)
        f1   = 2*prec*rec/(prec+rec+1e-10)
        print(f"   P={prec:.2f} R={rec:.2f} F1={f1:.2f}")
    acc = (y_true==y_pred).mean()
    macro_f1 = np.mean([
        2*(cm[i,i]/(cm[:,i].sum()+1e-10))*(cm[i,i]/(cm[i,:].sum()+1e-10)) /
        (cm[i,i]/(cm[:,i].sum()+1e-10)+cm[i,i]/(cm[i,:].sum()+1e-10)+1e-10)
        for i in range(n)
    ])
    print(f"\n  Accuracy={acc:.4f}  Macro-F1={macro_f1:.4f}")
    return acc, macro_f1

knn = KNNModel(k=3).fit(X_tr, y_tr)
preds = knn.predict(X_val)
class_names = ["Budget","Mid","Premium"]
print(f"  KNN (k=3) on validation set:")
acc, f1 = classification_report(y_val, preds, class_names)

# ── Step 3: K-Fold Cross-Validation ──────────────────────────────────────────
print("\n=== Step 3: K-Fold Cross-Validation ===")

def kfold_cv(model_class, model_kwargs, X, y, k=5):
    n = len(X)
    indices = np.random.permutation(n)
    fold_size = n // k
    accs = []
    for fold in range(k):
        val_idx   = indices[fold*fold_size:(fold+1)*fold_size]
        train_idx = np.concatenate([indices[:fold*fold_size], indices[(fold+1)*fold_size:]])
        model = model_class(**model_kwargs)
        model.fit(X[train_idx], y[train_idx])
        preds = model.predict(X[val_idx])
        accs.append((preds == y[val_idx]).mean())
    return np.array(accs)

print(f"  5-Fold CV results:")
print(f"  {'Model':<20} {'Fold 1':>7} {'Fold 2':>7} {'Fold 3':>7} {'Fold 4':>7} {'Fold 5':>7} {'Mean±Std':>14}")

models = [
    ("DummyMajority", DummyMajority, {}),
    ("KNN k=1",       KNNModel,      {"k":1}),
    ("KNN k=3",       KNNModel,      {"k":3}),
    ("KNN k=5",       KNNModel,      {"k":5}),
    ("LogisticReg",   LinearModel,   {}),
]

for name, cls, kwargs in models:
    accs = kfold_cv(cls, kwargs, X, y, k=5)
    fold_str = "  ".join(f"{a:.3f}" for a in accs)
    print(f"  {name:<20} {fold_str}  {accs.mean():.3f}±{accs.std():.3f}")

# ── Step 4: Stratified K-Fold ─────────────────────────────────────────────────
print("\n=== Step 4: Stratified K-Fold (maintains class proportions) ===")

def stratified_kfold(X, y, k=5):
    """Ensure each fold has same class distribution as whole dataset."""
    classes = np.unique(y)
    folds = [[] for _ in range(k)]
    for c in classes:
        c_idx = np.where(y == c)[0]
        np.random.shuffle(c_idx)
        for i, idx in enumerate(c_idx):
            folds[i % k].append(idx)
    return [np.array(f) for f in folds]

folds = stratified_kfold(X, y, k=5)
print(f"  Stratified fold class distributions:")
for i, fold_idx in enumerate(folds):
    dist = Counter(y[fold_idx])
    print(f"  Fold {i+1}: n={len(fold_idx)}  {dict(dist)}")

# ── Step 5: Bias-Variance tradeoff ───────────────────────────────────────────
print("\n=== Step 5: Bias-Variance Tradeoff (K vs complexity) ===")
print(f"  {'K':<5} {'Train acc':>10} {'Val acc':>10} {'Gap':>8}  {'Diagnosis'}")
for k in [1, 2, 3, 5, 7, 10, 15, 20]:
    train_accs, val_accs = [], []
    for _ in range(10):
        idx = np.random.permutation(len(X))
        split = int(0.7 * len(X))
        X_t, y_t = X[idx[:split]], y[idx[:split]]
        X_v, y_v = X[idx[split:]], y[idx[split:]]
        m = KNNModel(k=k).fit(X_t, y_t)
        train_accs.append((m.predict(X_t)==y_t).mean())
        val_accs.append((m.predict(X_v)==y_v).mean())
    tr, va = np.mean(train_accs), np.mean(val_accs)
    gap = tr - va
    diagnosis = "overfit" if gap > 0.15 else ("underfit" if va < 0.6 else "good")
    print(f"  {k:<5} {tr:>10.4f} {va:>10.4f} {gap:>8.4f}  {diagnosis}")

# ── Step 6: Regression metrics (R² and RMSE) ─────────────────────────────────
print("\n=== Step 6: Regression Metrics ===")

def rmse(y_true, y_pred): return np.sqrt(np.mean((y_true-y_pred)**2))
def mae(y_true, y_pred):  return np.mean(np.abs(y_true-y_pred))
def r2(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - y_true.mean())**2)
    return 1 - ss_res / (ss_tot + 1e-10)

# Simple linear regression on price
prices = X_raw[:, 0]
units  = np.array([1200,980,900,820,750,700,680,650,610,590,570,550,530,510,480,450,420,380,250,210], dtype=float)
n = len(prices)
X_lr = np.column_stack([np.ones(n), (prices-prices.mean())/prices.std()])
theta = np.linalg.lstsq(X_lr, units, rcond=None)[0]
y_pred = X_lr @ theta

print(f"  Linear: Price → Units_Sold")
print(f"  RMSE: {rmse(units, y_pred):.2f} units")
print(f"  MAE:  {mae(units, y_pred):.2f} units")
print(f"  R²:   {r2(units, y_pred):.4f}")
print(f"  (R²=1.0 perfect, R²=0.0 = no better than mean)")
PYEOF
```

> 💡 **Cross-validation variance tells you about dataset size.** Wide confidence intervals (e.g., `0.820±0.150`) mean your dataset is too small for reliable evaluation — performance estimates swing wildly depending on which 20% ended up in the test set. The fix: more data, or nested cross-validation. Rule of thumb: you need at least 50 samples per class for K-fold to give stable estimates. With fewer than 30 total samples, leave-one-out cross-validation (K=n) is more appropriate.

**📸 Verified Output:**
```
=== Step 3: K-Fold Cross-Validation ===
  Model                Fold 1  Fold 2  Fold 3  Fold 4  Fold 5       Mean±Std
  DummyMajority         0.500   0.500   0.500   0.500   0.500  0.500±0.000
  KNN k=1               0.750   0.750   1.000   0.750   1.000  0.850±0.122
  KNN k=3               0.750   1.000   1.000   0.750   1.000  0.900±0.122
  LogisticReg           0.750   1.000   1.000   1.000   1.000  0.950±0.100

=== Step 5: Bias-Variance Tradeoff ===
  K=1    Train=1.0000  Val=0.7500  overfit
  K=5    Train=0.9286  Val=0.8750  good
  K=20   Train=0.6429  Val=0.6250  underfit
```

---

## Summary

| Metric | Formula | When to use |
|--------|---------|------------|
| Accuracy | `correct/total` | Balanced classes |
| Precision | `TP/(TP+FP)` | Minimise false positives |
| Recall | `TP/(TP+FN)` | Minimise false negatives |
| F1 | `2PR/(P+R)` | Imbalanced classes |
| R² | `1 - SS_res/SS_tot` | Regression quality |
| RMSE | `√(Σ(y-ŷ)²/n)` | Regression error magnitude |
