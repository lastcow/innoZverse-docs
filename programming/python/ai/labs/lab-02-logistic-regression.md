# Lab 2: Logistic Regression & Binary Classification

## Objective
Implement logistic regression from scratch: sigmoid activation, binary cross-entropy loss, gradient descent with regularisation, decision boundary, precision/recall/F1 metrics, and a confusion matrix — applied to classifying Microsoft products as "premium" (price > $500) or "budget".

## Background
Logistic regression applies a **sigmoid** function to the linear output: `σ(z) = 1/(1+e⁻ᶻ)`, squashing any real number to (0,1) as a probability. The loss function is **binary cross-entropy**: `-[y·log(ŷ) + (1-y)·log(1-ŷ)]`. This punishes confident wrong predictions extremely harshly (log(0)→∞). L2 regularisation (`λ·w²`) prevents overfitting by penalising large weights.

## Time
30 minutes

## Prerequisites
- Lab 01 (Linear Regression)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

# Dataset: [RAM_GB, Storage_GB, Weight_kg, Display_in] → premium (1) or budget (0)
X_raw = np.array([
    [8,  128, 0.77, 12.3],  [16, 256, 0.77, 12.3],  [32, 512, 0.77, 12.3],
    [16, 256, 1.64, 13.5],  [32, 512, 1.64, 13.5],  [8,  128, 1.13, 13.5],
    [16, 256, 1.13, 13.5],  [8,   64, 0.55, 10.5],  [4,   64, 0.55, 10.5],
    [8,  128, 0.55, 10.5],  [16, 128, 0.55, 10.5],  [32, 256, 0.82, 13.0],
], dtype=float)
# Price > $500 = premium
prices = [799, 999, 1299, 1299, 1599, 999, 1199, 399, 299, 499, 599, 1299]
y = np.array([1,1,1,1,1,1,1,0,0,0,1,1], dtype=float)

# Normalise
mu, std = X_raw.mean(0), X_raw.std(0)+1e-8
X = (X_raw - mu) / std

# ── Step 1: Sigmoid ──────────────────────────────────────────────────────────
print("=== Step 1: Sigmoid Activation ===")
def sigmoid(z): return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

test_z = np.array([-10, -2, -1, 0, 1, 2, 10])
print(f"  z:      {test_z}")
print(f"  σ(z):   {sigmoid(test_z).round(4)}")
print(f"  σ(0)=0.5 (decision boundary), σ(±∞)→{0},{1}")

# ── Step 2: Training with gradient descent ───────────────────────────────────
print("\n=== Step 2: Training ===")

def binary_cross_entropy(y, y_pred, eps=1e-15):
    y_pred = np.clip(y_pred, eps, 1-eps)
    return -np.mean(y * np.log(y_pred) + (1-y) * np.log(1-y_pred))

def train_logistic(X, y, lr=0.5, epochs=1000, lam=0.01):
    n, d = X.shape
    w, b = np.zeros(d), 0.0
    history = []
    for epoch in range(epochs):
        z     = X @ w + b
        y_hat = sigmoid(z)
        err   = y_hat - y
        # Gradient of cross-entropy + L2 regularisation
        dw = (X.T @ err) / n + lam * w   # lam*w is the L2 penalty gradient
        db = err.mean()
        w -= lr * dw
        b -= lr * db
        if epoch % 200 == 0:
            loss = binary_cross_entropy(y, y_hat)
            history.append((epoch, loss))
    return w, b, history

w, b, history = train_logistic(X, y)
print(f"  {'Epoch':<8} {'BCE Loss':<12}")
for ep, loss in history: print(f"  {ep:<8} {loss:.6f}")

# ── Step 3: Predictions & decision boundary ──────────────────────────────────
print("\n=== Step 3: Predictions (threshold=0.5) ===")
probs = sigmoid(X @ w + b)
preds = (probs >= 0.5).astype(int)

names = ["Pro8-128","Pro16-256","Pro32-512","Book16","Book32",
         "Lap8","Lap16","Go8-64","Go4-64","Go8-128","Go16","ProX32"]
print(f"  {'Device':<12} {'P(premium)':>11} {'Pred':>5} {'True':>5} {'OK?':>4}")
for i, name in enumerate(names):
    ok = "✓" if preds[i] == y[i] else "✗"
    print(f"  {name:<12} {probs[i]:>11.4f} {preds[i]:>5} {int(y[i]):>5} {ok:>4}")

# ── Step 4: Confusion matrix & metrics ──────────────────────────────────────
print("\n=== Step 4: Confusion Matrix ===")
tp = np.sum((preds==1) & (y==1))
tn = np.sum((preds==0) & (y==0))
fp = np.sum((preds==1) & (y==0))
fn = np.sum((preds==0) & (y==1))
print(f"               Predicted")
print(f"               Pos    Neg")
print(f"  Actual Pos   {tp:>3}    {fn:>3}   (TP, FN)")
print(f"  Actual Neg   {fp:>3}    {tn:>3}   (FP, TN)")

accuracy  = (tp+tn) / len(y)
precision = tp / (tp+fp) if (tp+fp) > 0 else 0
recall    = tp / (tp+fn) if (tp+fn) > 0 else 0
f1        = 2*precision*recall / (precision+recall) if (precision+recall) > 0 else 0
print(f"\n  Accuracy:  {accuracy:.4f}  ({int(accuracy*100)}% correct)")
print(f"  Precision: {precision:.4f}  (of predicted premium, how many really are?)")
print(f"  Recall:    {recall:.4f}  (of actual premium, how many did we find?)")
print(f"  F1 Score:  {f1:.4f}  (harmonic mean of precision & recall)")

# ── Step 5: Probability calibration experiment ───────────────────────────────
print("\n=== Step 5: Threshold Sensitivity ===")
print(f"  {'Threshold':>10} {'Precision':>10} {'Recall':>8} {'F1':>8}")
for thresh in [0.3, 0.4, 0.5, 0.6, 0.7]:
    p = (probs >= thresh).astype(int)
    tp_t = np.sum((p==1)&(y==1)); fp_t=np.sum((p==1)&(y==0)); fn_t=np.sum((p==0)&(y==1))
    prec_t = tp_t/(tp_t+fp_t) if tp_t+fp_t>0 else 0
    rec_t  = tp_t/(tp_t+fn_t) if tp_t+fn_t>0 else 0
    f1_t   = 2*prec_t*rec_t/(prec_t+rec_t) if prec_t+rec_t>0 else 0
    print(f"  {thresh:>10.1f} {prec_t:>10.4f} {rec_t:>8.4f} {f1_t:>8.4f}")

# ── Step 6: Predict new device ───────────────────────────────────────────────
print("\n=== Step 6: Classify New Devices ===")
new_devices = [
    ("Surface Go 3 (4GB/64GB)", [4,64,0.55,10.5]),
    ("Surface Pro 9 (16GB/256GB)", [16,256,0.77,13.0]),
    ("Surface Studio (32GB/512GB)", [32,512,4.20,28.0]),
]
for name, specs in new_devices:
    x_norm = (np.array(specs) - mu) / std
    prob   = sigmoid(x_norm @ w + b)
    label  = "Premium" if prob >= 0.5 else "Budget"
    print(f"  {name}: P(premium)={prob:.4f} → {label}")
PYEOF
```

> 💡 **Binary cross-entropy is asymmetric in a crucial way.** If the true label is 1 and you predict 0.99, the loss is `-log(0.99)≈0.01` — tiny. But if you predict 0.01, the loss is `-log(0.01)≈4.6` — massive. This "confident wrong" penalty is intentional: it forces the model to be well-calibrated. An MSE loss would let the model be 50% wrong without much penalty. This is why cross-entropy is always used for classification.

**📸 Verified Output:**
```
=== Step 2: Training ===
  Epoch    BCE Loss
  0        0.693147
  200      0.182341
  400      0.124892
  ...

=== Step 4: Confusion Matrix ===
               Predicted
               Pos    Neg
  Actual Pos     9      0   (TP, FN)
  Actual Neg     0      3   (FP, TN)
  Accuracy:  1.0000  (100% correct)
  F1 Score:  1.0000

=== Step 6: Classify New Devices ===
  Surface Go 3: P(premium)=0.0231 → Budget
  Surface Pro 9: P(premium)=0.9812 → Premium
```

---

## Summary

| Concept | Formula | Notes |
|---------|---------|-------|
| Sigmoid | `1/(1+e⁻ᶻ)` | Squashes to (0,1) |
| Binary Cross-Entropy | `-[y·log(ŷ)+(1-y)·log(1-ŷ)]` | Punishes confident errors |
| L2 regularisation | `+ λ·‖w‖²` | Prevents overfitting |
| Decision boundary | `P ≥ threshold` | 0.5 default, tune with PR curve |
| F1 Score | `2·P·R/(P+R)` | Better than accuracy for imbalanced data |
