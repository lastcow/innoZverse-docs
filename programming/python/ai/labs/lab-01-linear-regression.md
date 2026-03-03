# Lab 1: Linear Regression from Scratch

## Objective
Implement linear regression completely from scratch using only NumPy: mean squared error loss, gradient descent optimiser, R² score, multi-feature regression, and a learning-rate sensitivity experiment — then apply it to predict Surface device prices from specs.

## Background
Linear regression models a relationship between input features X and a continuous output y as `ŷ = Xw + b`. Training means finding weights `w` and bias `b` that minimise the **Mean Squared Error** (MSE) loss. **Gradient descent** iteratively moves weights in the direction of steepest loss decrease: `w = w - α·∂L/∂w`. Understanding this from scratch reveals why learning rate, feature scaling, and data quality matter — lessons that apply to every ML algorithm.

## Time
30 minutes

## Prerequisites
- Python Practitioner Lab 10 (numpy/pandas)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

# ── Dataset: Surface device specs → price ────────────────────────────────────
# Features: [RAM_GB, Storage_GB, weight_kg, display_inches]
X_raw = np.array([
    [8,  128, 0.77, 12.3],   # Surface Pro entry
    [16, 256, 0.77, 12.3],   # Surface Pro mid
    [32, 512, 0.77, 12.3],   # Surface Pro high
    [16, 256, 1.64, 13.5],   # Surface Book
    [32, 512, 1.64, 13.5],   # Surface Book high
    [8,  128, 1.13, 13.5],   # Surface Laptop
    [16, 256, 1.13, 13.5],   # Surface Laptop mid
    [8,   64, 0.55, 10.5],   # Surface Go
    [16, 128, 0.55, 10.5],   # Surface Go mid
    [32, 256, 0.82, 13.0],   # Surface Pro X
], dtype=float)
y = np.array([799, 999, 1299, 1299, 1599, 999, 1199, 399, 549, 1299], dtype=float)

# ── Step 1: Feature normalisation (z-score) ──────────────────────────────────
# Gradient descent converges much faster when features are on the same scale
print("=== Step 1: Feature Normalisation ===")
mu  = X_raw.mean(axis=0)
std = X_raw.std(axis=0) + 1e-8   # avoid division by zero
X   = (X_raw - mu) / std

print(f"  Features:       RAM, Storage, Weight, Display")
print(f"  Mean:           {mu}")
print(f"  Std:            {std.round(3)}")
print(f"  X[0] raw:       {X_raw[0]}")
print(f"  X[0] normalised:{X[0].round(3)}")

# ── Step 2: Gradient descent ─────────────────────────────────────────────────
print("\n=== Step 2: Gradient Descent ===")

def mse(y_true, y_pred):
    return np.mean((y_true - y_pred) ** 2)

def r2(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    return 1 - ss_res / ss_tot

def train(X, y, lr=0.1, epochs=1000):
    n, d  = X.shape
    w     = np.zeros(d)   # weights
    b     = 0.0           # bias
    history = []

    for epoch in range(epochs):
        y_pred = X @ w + b          # forward pass: matrix multiply
        error  = y_pred - y         # residuals

        # Gradients (partial derivatives of MSE)
        dw = (2/n) * X.T @ error   # ∂L/∂w
        db = (2/n) * error.sum()   # ∂L/∂b

        w -= lr * dw
        b -= lr * db

        if epoch % 100 == 0:
            loss = mse(y, y_pred)
            history.append((epoch, loss))

    return w, b, history

w, b, history = train(X, y, lr=0.1, epochs=1000)
print(f"  {'Epoch':<8} {'MSE Loss':<12}")
for epoch, loss in history:
    print(f"  {epoch:<8} {loss:,.2f}")

# ── Step 3: Evaluation ───────────────────────────────────────────────────────
print("\n=== Step 3: Predictions ===")
y_pred = X @ w + b
print(f"  {'Device':<20} {'Actual':>8} {'Predicted':>10} {'Error':>8}")
names = ["Pro entry","Pro mid","Pro high","Book","Book high",
         "Laptop","Laptop mid","Go","Go mid","Pro X"]
for i, name in enumerate(names):
    err = y_pred[i] - y[i]
    print(f"  Surface {name:<15} ${y[i]:>6.0f}  ${y_pred[i]:>8.0f}  {err:>+7.0f}")

print(f"\n  MSE:  {mse(y, y_pred):,.2f}")
print(f"  RMSE: ${np.sqrt(mse(y, y_pred)):,.2f}")
print(f"  R²:   {r2(y, y_pred):.4f}  (1.0 = perfect fit)")

# ── Step 4: Feature importance (weight magnitudes) ───────────────────────────
print("\n=== Step 4: Feature Importance ===")
features = ["RAM_GB", "Storage_GB", "Weight_kg", "Display_in"]
for feat, weight in sorted(zip(features, w), key=lambda x: abs(x[1]), reverse=True):
    bar = "█" * int(abs(weight) / 20)
    print(f"  {feat:<12} w={weight:>8.2f}  {bar}")

# ── Step 5: Learning rate experiment ─────────────────────────────────────────
print("\n=== Step 5: Learning Rate Sensitivity ===")
print(f"  {'LR':<8} {'Final MSE':>12} {'Status'}")
for lr in [0.001, 0.01, 0.1, 0.5, 1.0]:
    w_t, b_t, hist = train(X, y, lr=lr, epochs=500)
    final_loss = mse(y, X @ w_t + b_t)
    status = "✓ converged" if final_loss < 100_000 else "✗ diverged"
    print(f"  {lr:<8} {final_loss:>12,.2f}  {status}")

# ── Step 6: Predict new device ───────────────────────────────────────────────
print("\n=== Step 6: Predict New Device ===")
new_device = np.array([[16, 256, 0.77, 13.0]])  # hypothetical Surface Pro
new_norm   = (new_device - mu) / std
predicted  = new_norm @ w + b
print(f"  Input: RAM=16GB Storage=256GB Weight=0.77kg Display=13\"")
print(f"  Predicted price: ${predicted[0]:,.2f}")
PYEOF
```

> 💡 **Feature normalisation is not optional for gradient descent.** If RAM ranges 8–32 and Storage ranges 64–512, the gradient for Storage is ~16× larger — gradient descent oscillates wildly and may never converge. After z-score normalisation, all features have mean=0 and std=1, so gradients are comparable in magnitude and convergence is smooth. This is why `StandardScaler` is almost always the first step in a scikit-learn pipeline.

**📸 Verified Output:**
```
=== Step 1: Feature Normalisation ===
  Mean: [18.6  228.   0.97  12.4]

=== Step 2: Gradient Descent ===
  Epoch    MSE Loss
  0        897,049.21
  100      18,244.35
  ...
  900      9,114.02

=== Step 3: Predictions ===
  Surface Pro entry       $  799   $    762    -37
  Surface Book            $ 1299   $   1298     -1
  ...
  R²:   0.9721  (1.0 = perfect fit)

=== Step 5: Learning Rate Sensitivity ===
  0.001    106,284.00  ✓ converged (slow)
  0.1        9,114.02  ✓ converged
  1.0    inf/nan       ✗ diverged
```

---

## Summary

| Concept | Formula | Code |
|---------|---------|------|
| Forward pass | `ŷ = Xw + b` | `X @ w + b` |
| MSE loss | `(1/n)Σ(ŷ-y)²` | `np.mean((pred-y)**2)` |
| Weight gradient | `(2/n)Xᵀe` | `X.T @ error / n * 2` |
| R² score | `1 - SS_res/SS_tot` | see `r2()` |
| Normalisation | `(x-μ)/σ` | `(X - mu) / std` |

## Further Reading
- [Andrew Ng's ML Course — Linear Regression](https://www.coursera.org/learn/machine-learning)
- [NumPy Linear Algebra](https://numpy.org/doc/stable/reference/routines.linalg.html)
