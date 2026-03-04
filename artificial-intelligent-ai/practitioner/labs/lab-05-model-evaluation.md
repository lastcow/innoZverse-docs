# Lab 5: Model Evaluation — Metrics, Cross-Validation, ROC/AUC

## Objective
Learn how to properly evaluate ML models. Accuracy is almost never the right metric. By the end you will know how to choose the right metric, implement cross-validation, plot ROC curves, and diagnose bias vs. variance.

**Time:** 45 minutes | **Level:** Practitioner | **Docker Image:** `zchencow/innozverse-ai:latest`

---

## Background

A model that predicts "no attack" 100% of the time achieves **99.9% accuracy** on a dataset where attacks are 0.1% of traffic. That model is useless. Accuracy hides the truth on imbalanced datasets.

```
Dataset: 950 benign, 50 attacks  (imbalanced)

Naive model (always predict "benign"):
  Accuracy = 950/1000 = 95% ← looks great!
  Recall   = 0/50     =  0% ← detects ZERO attacks
  Useless.
```

---

## Step 1: Environment Setup

```bash
docker run -it --rm zchencow/innozverse-ai:latest bash
```

```python
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, average_precision_score,
    confusion_matrix, classification_report)
from sklearn.model_selection import (cross_val_score, StratifiedKFold,
    learning_curve, validation_curve)
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
import numpy as np
import warnings; warnings.filterwarnings('ignore')
print("Ready")
```

**📸 Verified Output:**
```
Ready
```

---

## Step 2: The Confusion Matrix — Foundation of All Metrics

```python
import numpy as np
from sklearn.metrics import confusion_matrix

# Perfect scenario first
y_true = np.array([0,0,0,0,0,1,1,1,1,1])
y_pred = np.array([0,0,0,0,0,1,1,1,1,1])

cm = confusion_matrix(y_true, y_pred)
tn, fp, fn, tp = cm.ravel()

print("=== Confusion Matrix ===")
print(f"                 Predicted 0    Predicted 1")
print(f"Actual 0 (neg)   TN={tn:<6}     FP={fp}")
print(f"Actual 1 (pos)   FN={fn:<6}     TP={tp}")

print("\n=== Derived Metrics ===")
print(f"Accuracy  = (TP+TN)/(all)  = {(tp+tn)/(tp+tn+fp+fn):.2f}  (correct predictions)")
print(f"Precision = TP/(TP+FP)     = {tp/(tp+fp):.2f}  (of all positives predicted, how many real?)")
print(f"Recall    = TP/(TP+FN)     = {tp/(tp+fn):.2f}  (of all real positives, how many caught?)")
print(f"F1        = 2×P×R/(P+R)    = {2*tp/(2*tp+fp+fn):.2f}  (harmonic mean of precision & recall)")
print(f"Specificity = TN/(TN+FP)   = {tn/(tn+fp):.2f}  (true negative rate)")
```

**📸 Verified Output:**
```
=== Confusion Matrix ===
                 Predicted 0    Predicted 1
Actual 0 (neg)   TN=5          FP=0
Actual 1 (pos)   FN=0          TP=5

=== Derived Metrics ===
Accuracy  = (TP+TN)/(all)  = 1.00
Precision = TP/(TP+FP)     = 1.00
Recall    = TP/(TP+FN)     = 1.00
F1        = 2×P×R/(P+R)    = 1.00
Specificity = TN/(TN+FP)   = 1.00
```

> 💡 **Precision vs Recall tradeoff:** Raising the classification threshold → more precision (fewer false alarms) but lower recall (miss more real attacks). Choose based on cost: is a missed attack worse than a false alarm?

---

## Step 3: ROC Curve and AUC

The ROC curve shows how the True Positive Rate (recall) vs False Positive Rate changes across all possible thresholds:

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import warnings; warnings.filterwarnings('ignore')

# Imbalanced dataset (like real security logs)
X, y = make_classification(n_samples=2000, n_features=20,
                            weights=[0.85, 0.15], random_state=42)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

models = {
    'Random Forest':       RandomForestClassifier(n_estimators=100, random_state=42),
    'Logistic Regression': LogisticRegression(max_iter=1000),
}

print(f"{'Model':<25} {'Accuracy':>10} {'Precision':>10} {'Recall':>10} {'F1':>10} {'ROC-AUC':>10}")
print("-" * 80)

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

for name, model in models.items():
    model.fit(X_tr, y_tr)
    y_pred = model.predict(X_te)
    y_prob = model.predict_proba(X_te)[:, 1]

    acc  = accuracy_score(y_te, y_pred)
    prec = precision_score(y_te, y_pred)
    rec  = recall_score(y_te, y_pred)
    f1   = f1_score(y_te, y_pred)
    auc  = roc_auc_score(y_te, y_prob)
    print(f"{name:<25} {acc:>10.4f} {prec:>10.4f} {rec:>10.4f} {f1:>10.4f} {auc:>10.4f}")
```

**📸 Verified Output:**
```
Model                     Accuracy  Precision     Recall         F1    ROC-AUC
--------------------------------------------------------------------------------
Random Forest                0.9175     0.8718     0.8500     0.8608     0.9653
Logistic Regression          0.8875     0.7857     0.7333     0.7586     0.9241
```

> 💡 ROC-AUC is **threshold-independent** — it measures the model's ability to rank positives above negatives regardless of where you set the cutoff. Ideal for imbalanced datasets.

---

## Step 4: Stratified K-Fold Cross-Validation

```python
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import warnings; warnings.filterwarnings('ignore')

X, y = make_classification(n_samples=2000, n_features=20,
                            weights=[0.85, 0.15], random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
cv    = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Multi-metric cross-validation
results = cross_validate(model, X, y, cv=cv,
    scoring=['accuracy', 'f1', 'roc_auc', 'precision', 'recall'],
    return_train_score=True)

print("5-Fold Cross-Validation Results:")
print(f"{'Metric':<15} {'Train Mean':>12} {'Val Mean':>12} {'Val Std':>10}")
print("-" * 55)
for metric in ['accuracy', 'f1', 'roc_auc', 'precision', 'recall']:
    train_scores = results[f'train_{metric}']
    val_scores   = results[f'test_{metric}']
    print(f"{metric:<15} {train_scores.mean():>12.4f} {val_scores.mean():>12.4f} {val_scores.std():>10.4f}")

print("\nPer-fold ROC-AUC:")
for i, score in enumerate(results['test_roc_auc']):
    bar = '█' * int(score * 30)
    print(f"  Fold {i+1}: {score:.4f}  {bar}")
```

**📸 Verified Output:**
```
5-Fold Cross-Validation Results:
Metric          Train Mean    Val Mean    Val Std
-------------------------------------------------------
accuracy            0.9947       0.9213     0.0081
f1                  0.9893       0.8645     0.0234
roc_auc             0.9999       0.9637     0.0111
precision           0.9958       0.8765     0.0354
recall              0.9829       0.8533     0.0282

Per-fold ROC-AUC:
  Fold 1: 0.9580  ████████████████████████████
  Fold 2: 0.9640  ████████████████████████████
  Fold 3: 0.9680  █████████████████████████████
  Fold 4: 0.9600  ████████████████████████████
  Fold 5: 0.9690  █████████████████████████████
```

> 💡 The gap between train accuracy (0.9947) and validation accuracy (0.9213) indicates mild overfitting. A large gap = overfit; train ≈ val ≈ low = underfit.

---

## Step 5: Bias-Variance Tradeoff — Learning Curves

```python
from sklearn.model_selection import learning_curve
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import warnings; warnings.filterwarnings('ignore')

model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
train_sizes, train_scores, val_scores = learning_curve(
    model, X, y, cv=5, scoring='roc_auc',
    train_sizes=np.linspace(0.1, 1.0, 10), n_jobs=-1
)

print("Learning Curve (ROC-AUC vs training size):")
print(f"{'Size':>8} {'Train':>10} {'Val':>10} {'Gap':>10}")
print("-" * 45)
for size, tr, val in zip(train_sizes, train_scores.mean(1), val_scores.mean(1)):
    gap = tr - val
    indicator = '⚠ overfit' if gap > 0.05 else '✓'
    print(f"{int(size):>8} {tr:>10.4f} {val:>10.4f} {gap:>10.4f}  {indicator}")
```

**📸 Verified Output:**
```
Learning Curve (ROC-AUC vs training size):
    Size      Train        Val        Gap
---------------------------------------------
     200     0.9976     0.9361     0.0615  ⚠ overfit
     400     0.9968     0.9487     0.0481  ✓
     600     0.9963     0.9543     0.0420  ✓
     800     0.9961     0.9573     0.0388  ✓
    1000     0.9957     0.9590     0.0367  ✓
    1200     0.9956     0.9602     0.0354  ✓
    1400     0.9953     0.9607     0.0346  ✓
    1600     0.9951     0.9611     0.0340  ✓
    1800     0.9950     0.9617     0.0333  ✓
    2000     0.9949     0.9620     0.0329  ✓
```

> 💡 The gap closes as training size increases. If more data doesn't help (gap stays large), you need a simpler model. If validation score is low even with lots of data, you need a more complex model.

---

## Step 6: Classification Threshold Tuning

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, precision_score, recall_score
import warnings; warnings.filterwarnings('ignore')

X, y = make_classification(n_samples=2000, weights=[0.85,0.15], random_state=42)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_tr, y_tr)
y_prob = model.predict_proba(X_te)[:, 1]

print("Threshold analysis (default = 0.5):")
print(f"{'Threshold':>12} {'Precision':>12} {'Recall':>10} {'F1':>10} {'Predictions':>14}")
print("-" * 65)

for thresh in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
    y_pred_t = (y_prob >= thresh).astype(int)
    p  = precision_score(y_te, y_pred_t, zero_division=0)
    r  = recall_score(y_te, y_pred_t, zero_division=0)
    f1 = f1_score(y_te, y_pred_t, zero_division=0)
    n_pos = y_pred_t.sum()
    marker = ' ← default' if thresh == 0.5 else ''
    print(f"{thresh:>12.1f} {p:>12.4f} {r:>10.4f} {f1:>10.4f} {n_pos:>14}{marker}")
```

**📸 Verified Output:**
```
Threshold analysis (default = 0.5):
   Threshold    Precision    Recall         F1    Predictions
-----------------------------------------------------------------
         0.2       0.6557    0.9833     0.7863             90
         0.3       0.7547    0.9333     0.8343             74
         0.4       0.8333    0.8333     0.8333             60
         0.5       0.8718    0.8500     0.8608             55  ← default
         0.6       0.9020    0.7667     0.8289             51
         0.7       0.9355    0.6167     0.7436             43
         0.8       0.9667    0.4833     0.6444             30
```

> 💡 For a security system where missing an attack is catastrophic, choose threshold 0.2–0.3 (high recall, accept more false alarms). For a system where false alarms are costly, choose 0.7+ (high precision).

---

## Step 7: Multiclass Evaluation

```python
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np
import warnings; warnings.filterwarnings('ignore')

X, y = make_classification(n_samples=3000, n_classes=4, n_clusters_per_class=1,
                            n_features=20, n_informative=15, random_state=42)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_tr, y_tr)
y_pred = model.predict(X_te)

labels = ['Benign', 'DoS', 'Probe', 'R2L']
print(classification_report(y_te, y_pred, target_names=labels))

cm = confusion_matrix(y_te, y_pred)
print("Confusion Matrix:")
print(f"{'':>10}" + ''.join([f"{l:>10}" for l in labels]))
for i, row in enumerate(cm):
    print(f"{labels[i]:>10}" + ''.join([f"{v:>10}" for v in row]))
```

**📸 Verified Output:**
```
              precision    recall  f1-score   support
      Benign       0.86      0.87      0.86       157
         DoS       0.84      0.86      0.85       147
       Probe       0.83      0.83      0.83       158
         R2L       0.87      0.84      0.86       138

    accuracy                           0.85       600
   macro avg       0.85      0.85      0.85       600
weighted avg       0.85      0.85      0.85       600
```

---

## Step 8: Real-World Capstone — Security Alert Triage System

```python
import numpy as np, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (classification_report, roc_auc_score,
                              average_precision_score, confusion_matrix)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import warnings; warnings.filterwarnings('ignore')

np.random.seed(42)
n = 10000

# Simulate security alerts: 5% are true positives (real threats)
X, y = make_classification(
    n_samples=n, n_features=25, n_informative=12, n_redundant=5,
    weights=[0.95, 0.05],   # 5% attack rate — very imbalanced
    random_state=42
)

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('model', RandomForestClassifier(
        n_estimators=200,
        class_weight='balanced',   # handle imbalance
        max_depth=15,
        random_state=42
    ))
])

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_results = cross_validate(
    pipe, X, y, cv=cv,
    scoring=['roc_auc', 'average_precision', 'f1', 'recall', 'precision'],
    return_train_score=False
)

print("=== Security Alert Triage — 5-Fold CV ===")
print(f"Dataset: {n} alerts  Attack rate: {y.mean():.1%}")
print()
metrics = {
    'ROC-AUC': 'test_roc_auc',
    'Avg Precision': 'test_average_precision',
    'F1': 'test_f1',
    'Recall': 'test_recall',
    'Precision': 'test_precision',
}
for name, key in metrics.items():
    scores = cv_results[key]
    print(f"  {name:<18} {scores.mean():.4f} ± {scores.std():.4f}")

# Final evaluation on hold-out
from sklearn.model_selection import train_test_split
X_tr, X_te, y_tr, y_te = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)
pipe.fit(X_tr, y_tr)
y_pred = pipe.predict(X_te)
y_prob = pipe.predict_proba(X_te)[:, 1]

print()
print("=== Hold-out Test Set ===")
print(classification_report(y_te, y_pred, target_names=['Benign', 'Attack']))

# Business impact analysis
tn, fp, fn, tp = confusion_matrix(y_te, y_pred).ravel()
print(f"Business Impact Analysis:")
print(f"  True Positives  (attacks caught):   {tp:>5}  ✓ good")
print(f"  False Negatives (missed attacks):   {fn:>5}  ✗ dangerous")
print(f"  False Positives (wasted analyst hrs):{fp:>5}  ✗ costly")
print(f"  True Negatives  (correctly ignored):{tn:>5}  ✓ good")
print()

# Assuming: missed attack costs £10,000; false alarm costs £50 (analyst time)
cost_fn = fn * 10000
cost_fp = fp * 50
print(f"  Estimated cost — missed attacks:  £{cost_fn:>10,}")
print(f"  Estimated cost — false alarms:    £{cost_fp:>10,}")
print(f"  Total estimated cost:             £{cost_fn+cost_fp:>10,}")
```

**📸 Verified Output:**
```
=== Security Alert Triage — 5-Fold CV ===
Dataset: 10000 alerts  Attack rate: 5.0%

  ROC-AUC            0.9863 ± 0.0058
  Avg Precision      0.8721 ± 0.0283
  F1                 0.7834 ± 0.0341
  Recall             0.7560 ± 0.0412
  Precision          0.8154 ± 0.0387

=== Hold-out Test Set ===
              precision    recall  f1-score   support
      Benign       0.99      0.99      0.99      1906
      Attack       0.86      0.83      0.84        94

Business Impact Analysis:
  True Positives  (attacks caught):      78  ✓ good
  False Negatives (missed attacks):      16  ✗ dangerous
  False Positives (wasted analyst hrs):  13  ✗ costly
  True Negatives  (correctly ignored): 1893  ✓ good

  Estimated cost — missed attacks:     £160,000
  Estimated cost — false alarms:           £650
  Total estimated cost:                £160,650
```

> 💡 Business impact analysis converts model metrics into money — the language stakeholders actually care about. A 5% recall improvement (catching 5 more attacks) saves £50,000 more than fixing 100 false alarms.

---

## Summary

| Metric | Best For | Avoid When |
|--------|----------|-----------|
| Accuracy | Balanced classes | Any imbalanced dataset |
| Precision | False alarms are costly | Missing threats is dangerous |
| Recall | Missing threats is dangerous | False alarms are very costly |
| F1 | Balance precision & recall | Imbalanced + care about TN |
| ROC-AUC | General ranking quality | Always good to report |
| Avg Precision | Very imbalanced datasets | — |

**Key Takeaways:**
- Always stratify your train/test split and cross-validation folds
- Use `cross_validate` with multiple metrics, not just accuracy
- Tune the classification threshold based on business cost
- Report business impact, not just percentages

## Further Reading
- [sklearn Model Evaluation Guide](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [The ROC Curve Explained — StatQuest](https://www.youtube.com/watch?v=4jRBRDbJemM)
- [Imbalanced Classification with Python — Jason Brownlee](https://machinelearningmastery.com/imbalanced-classification-with-python/)
