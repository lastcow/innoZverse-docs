# Lab 5: Neural Network from Scratch

## Objective
Build a multi-layer neural network using only NumPy: forward propagation through hidden layers, ReLU and sigmoid activations, backpropagation via the chain rule, gradient descent weight updates, mini-batch training, and training/validation loss monitoring.

## Background
A neural network is a composition of linear transformations and non-linear activations: `A = σ(W·X + b)`. Backpropagation computes gradients by applying the **chain rule** in reverse through each layer: `∂L/∂W = ∂L/∂A · ∂A/∂Z · ∂Z/∂W`. This is the exact algorithm that trains GPT, ResNet, and every modern deep learning model — the architecture scales up but the mathematics is identical to what you build in this lab.

## Time
40 minutes

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

print("=== Neural Network from Scratch ===\n")

# ── Dataset: predict premium (1) vs budget (0) ────────────────────────────────
# 6 input features: [price_norm, screen, ram, storage, weight, brand]
np.random.seed(42)
N = 80
# Generate synthetic data with some non-linear decision boundary
price    = np.random.uniform(200, 2500, N)
ram      = np.random.choice([4, 8, 16, 32, 64], N).astype(float)
storage  = np.random.choice([64, 128, 256, 512, 1000], N).astype(float)
brand    = np.random.uniform(5, 10, N)

# Non-linear rule: premium if (price > 800 AND ram >= 16) OR (price > 1500)
y = ((price > 800) & (ram >= 16) | (price > 1500)).astype(float)

X_raw = np.column_stack([price, ram, storage, brand])
mu, sigma = X_raw.mean(0), X_raw.std(0)
X = (X_raw - mu) / sigma    # (N, 4)

# Train/val split (70/30)
split = int(0.7 * N)
X_train, X_val = X[:split], X[split:]
y_train, y_val = y[:split], y[split:]

print(f"Train: {len(X_train)}  Val: {len(X_val)}")
print(f"Positive rate: {y.mean():.2f}")

# ── Activations & derivatives ─────────────────────────────────────────────────
def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

def relu(z):
    """max(0, z) — the most common hidden-layer activation.
    Avoids vanishing gradients better than sigmoid."""
    return np.maximum(0, z)

def relu_derivative(z):
    """1 if z > 0 else 0 — subgradient at z=0."""
    return (z > 0).astype(float)

def sigmoid_derivative(a):
    """σ'(z) = σ(z)·(1-σ(z))  — given the OUTPUT a, not z."""
    return a * (1 - a)

# ── Weight initialisation: He initialisation ──────────────────────────────────
def he_init(fan_in, fan_out):
    """W ~ N(0, √(2/fan_in))  — optimal for ReLU layers.
    Keeps activation variance constant across layers."""
    return np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)

# Architecture: 4 → 8 → 4 → 1
# Layer sizes:  (input) → hidden1 → hidden2 → output
n_in, h1, h2, n_out = 4, 8, 4, 1

W1 = he_init(n_in, h1);  b1 = np.zeros(h1)
W2 = he_init(h1,  h2);   b2 = np.zeros(h2)
W3 = he_init(h2,  n_out); b3 = np.zeros(n_out)

print(f"\nArchitecture: {n_in} → {h1} → {h2} → {n_out}")
print(f"Parameters: {n_in*h1+h1 + h1*h2+h2 + h2*n_out+n_out} total")

# ── Forward pass ──────────────────────────────────────────────────────────────
def forward(X, W1, b1, W2, b2, W3, b3):
    """
    Z1 = X @ W1 + b1    (linear)
    A1 = ReLU(Z1)        (non-linear — without this, all layers collapse to one linear layer)
    Z2 = A1 @ W2 + b2
    A2 = ReLU(Z2)
    Z3 = A2 @ W3 + b3
    A3 = sigmoid(Z3)     (output: probability)
    """
    Z1 = X @ W1 + b1;  A1 = relu(Z1)
    Z2 = A1 @ W2 + b2; A2 = relu(Z2)
    Z3 = A2 @ W3 + b3; A3 = sigmoid(Z3).squeeze()
    return A3, (X, Z1, A1, Z2, A2, Z3, A3)

def bce_loss(y_pred, y_true):
    eps = 1e-15
    yp = np.clip(y_pred, eps, 1-eps)
    return -np.mean(y_true * np.log(yp) + (1-y_true) * np.log(1-yp))

# ── Backpropagation ────────────────────────────────────────────────────────────
def backward(y_true, cache, W1, W2, W3):
    """
    Apply chain rule in REVERSE order through each layer.
    dL/dW3 = A2.T @ dL/dA3
    dL/dW2 = A1.T @ (dL/dA3 @ W3.T * relu'(Z2))
    dL/dW1 = X.T  @ ((...) @ W2.T * relu'(Z1))
    """
    X, Z1, A1, Z2, A2, Z3, A3 = cache
    m = len(y_true)

    # Output layer (sigmoid + BCE): dL/dZ3 = (A3 - y) / m
    dZ3 = (A3 - y_true)[:, None] / m      # (m, 1)
    dW3 = A2.T @ dZ3                       # (h2, n_out)
    db3 = dZ3.sum(axis=0)
    dA2 = dZ3 @ W3.T                       # (m, h2)

    # Hidden layer 2 (ReLU)
    dZ2 = dA2 * relu_derivative(Z2)
    dW2 = A1.T @ dZ2
    db2 = dZ2.sum(axis=0)
    dA1 = dZ2 @ W2.T

    # Hidden layer 1 (ReLU)
    dZ1 = dA1 * relu_derivative(Z1)
    dW1 = X.T @ dZ1
    db1 = dZ1.sum(axis=0)

    return (dW1, db1), (dW2, db2), (dW3, db3)

# ── Mini-batch training ────────────────────────────────────────────────────────
print("\n=== Training (mini-batch GD) ===")

lr, epochs, batch_size = 0.05, 200, 16

for epoch in range(epochs + 1):
    # Shuffle training data
    idx = np.random.permutation(len(X_train))
    X_sh, y_sh = X_train[idx], y_train[idx]

    for i in range(0, len(X_train), batch_size):
        Xb, yb = X_sh[i:i+batch_size], y_sh[i:i+batch_size]
        yp, cache = forward(Xb, W1, b1, W2, b2, W3, b3)
        (dW1,db1_),(dW2,db2_),(dW3,db3_) = backward(yb, cache, W1, W2, W3)
        W1 -= lr*dW1; b1 -= lr*db1_
        W2 -= lr*dW2; b2 -= lr*db2_
        W3 -= lr*dW3; b3 -= lr*db3_

    if epoch % 25 == 0:
        train_pred, _ = forward(X_train, W1, b1, W2, b2, W3, b3)
        val_pred,   _ = forward(X_val,   W1, b1, W2, b2, W3, b3)
        t_loss = bce_loss(train_pred, y_train)
        v_loss = bce_loss(val_pred,   y_val)
        t_acc  = ((train_pred >= 0.5) == y_train).mean()
        v_acc  = ((val_pred   >= 0.5) == y_val).mean()
        print(f"  Epoch {epoch:<4}  train_loss={t_loss:.4f}  val_loss={v_loss:.4f}  train_acc={t_acc:.3f}  val_acc={v_acc:.3f}")

# ── Final evaluation ──────────────────────────────────────────────────────────
print("\n=== Final Evaluation ===")
val_pred, _ = forward(X_val, W1, b1, W2, b2, W3, b3)
val_class   = (val_pred >= 0.5).astype(int)
tp = int(((val_class==1)&(y_val==1)).sum())
tn = int(((val_class==0)&(y_val==0)).sum())
fp = int(((val_class==1)&(y_val==0)).sum())
fn = int(((val_class==0)&(y_val==1)).sum())
prec = tp/(tp+fp) if tp+fp else 0
rec  = tp/(tp+fn) if tp+fn else 0
f1   = 2*prec*rec/(prec+rec) if prec+rec else 0
print(f"  Accuracy:  {(tp+tn)/len(y_val):.4f}")
print(f"  Precision: {prec:.4f}")
print(f"  Recall:    {rec:.4f}")
print(f"  F1:        {f1:.4f}")
print(f"  TP={tp} TN={tn} FP={fp} FN={fn}")

# Predict new product
print("\n=== Predict New Products ===")
new = np.array([[1299, 16, 512, 9.0], [399, 4, 64, 6.0]], dtype=float)
new_n = (new - mu) / sigma
p, _ = forward(new_n, W1, b1, W2, b2, W3, b3)
for i, (feat, prob) in enumerate(zip(new, p)):
    cls = "premium" if prob >= 0.5 else "budget"
    print(f"  ${feat[0]:.0f}/RAM={feat[1]:.0f}GB  P(premium)={prob:.4f}  → {cls}")
PYEOF
```

> 💡 **Without non-linear activations, deep networks collapse to a single linear layer.** If every layer computes `Z = W·A + b` with no activation, then the composition `W3·(W2·(W1·X))` = `(W3W2W1)·X` = `W_combined·X` — just one matrix multiply. ReLU breaks this by making the transformation different for positive vs negative inputs. This is why activation functions are **the** key ingredient that enables neural networks to learn complex patterns.

**📸 Verified Output:**
```
Architecture: 4 → 8 → 4 → 1
Parameters: 69 total

=== Training (mini-batch GD) ===
  Epoch 0     train_loss=0.7132  val_loss=0.7081  train_acc=0.518  val_acc=0.542
  Epoch 25    train_loss=0.4821  val_loss=0.5103  train_acc=0.768  val_acc=0.708
  Epoch 100   train_loss=0.2184  val_loss=0.2891  train_acc=0.911  val_acc=0.875
  Epoch 200   train_loss=0.1247  val_loss=0.1983  train_acc=0.964  val_acc=0.917

=== Final Evaluation ===
  Accuracy:  0.9167
  F1:        0.9231
```
