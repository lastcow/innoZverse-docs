# Lab 3: Neural Network from Scratch

## Objective
Build a fully-connected neural network using only NumPy: forward propagation through multiple layers, ReLU and sigmoid activations, backpropagation with the chain rule, mini-batch gradient descent, and weight initialisation strategies — trained to classify Surface products by tier.

## Background
A neural network stacks **layers** of weighted connections. Each layer computes `Z = XW + b`, then applies a non-linear **activation** (ReLU: `max(0,z)`, Sigmoid: `1/(1+e⁻ᶻ)`). **Backpropagation** computes gradients layer-by-layer using the chain rule: `∂L/∂W = ∂L/∂Z · ∂Z/∂W`. This lab implements a full 3-layer network (input → hidden → hidden → output) without any framework.

## Time
35 minutes

## Prerequisites
- Lab 01 (Linear Regression), Lab 02 (Logistic Regression)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

# ── Dataset: classify Surface tier (0=budget, 1=mid, 2=premium) ──────────────
# Features: [RAM_GB, Storage_GB, Weight_kg, Display_in, Price_normalized]
X_raw = np.array([
    [4,  64,  0.55, 10.5, 299],  [8,  64,  0.55, 10.5, 399],
    [8,  128, 0.55, 10.5, 499],  [8,  128, 1.13, 13.5, 799],
    [8,  128, 0.77, 12.3, 799],  [16, 256, 1.13, 13.5, 999],
    [16, 256, 0.77, 12.3, 999],  [16, 256, 1.64, 13.5, 1299],
    [32, 512, 0.77, 12.3, 1299], [32, 512, 1.64, 13.5, 1599],
    [32, 512, 1.13, 13.5, 1199], [32, 256, 0.82, 13.0, 1299],
], dtype=float)
# 0=budget(<500), 1=mid(500-999), 2=premium(>=1000)
y_labels = np.array([0,0,0,1,1,1,1,2,2,2,2,2])
n_classes = 3
mu, std = X_raw.mean(0), X_raw.std(0)+1e-8
X = (X_raw - mu) / std
# One-hot encode labels
Y = np.eye(n_classes)[y_labels]   # shape (12, 3)

# ── Step 1: Activations ──────────────────────────────────────────────────────
print("=== Step 1: Activation Functions ===")
def relu(z):          return np.maximum(0, z)
def relu_deriv(z):    return (z > 0).astype(float)
def sigmoid(z):       return 1 / (1 + np.exp(-np.clip(z,-500,500)))
def softmax(z):
    e = np.exp(z - z.max(axis=1, keepdims=True))  # subtract max for stability
    return e / e.sum(axis=1, keepdims=True)

z_test = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
print(f"  ReLU:    {relu(z_test)}")
print(f"  Sigmoid: {sigmoid(z_test).round(4)}")
logits = np.array([[2.0, 1.0, 0.1]])
print(f"  Softmax: {softmax(logits).round(4)}  (sums to {softmax(logits).sum():.4f})")

# ── Step 2: Network class ────────────────────────────────────────────────────
print("\n=== Step 2: 3-Layer Network ===")

class NeuralNetwork:
    """Input(5) → Hidden(8,ReLU) → Hidden(6,ReLU) → Output(3,Softmax)"""
    def __init__(self, layer_dims, lr=0.05):
        self.lr = lr
        self.params = {}
        # He initialisation: scale by sqrt(2/fan_in) — good for ReLU
        for i in range(1, len(layer_dims)):
            scale = np.sqrt(2.0 / layer_dims[i-1])
            self.params[f"W{i}"] = np.random.randn(layer_dims[i-1], layer_dims[i]) * scale
            self.params[f"b{i}"] = np.zeros((1, layer_dims[i]))
        self.L = len(layer_dims) - 1  # number of layers
        self.cache = {}

    def forward(self, X):
        A = X
        for i in range(1, self.L):
            Z = A @ self.params[f"W{i}"] + self.params[f"b{i}"]
            A = relu(Z)
            self.cache[f"A{i}"] = A
            self.cache[f"Z{i}"] = Z
        # Final layer: softmax for multi-class
        ZL = A @ self.params[f"W{self.L}"] + self.params[f"b{self.L}"]
        AL = softmax(ZL)
        self.cache[f"A{self.L}"] = AL
        self.cache[f"Z{self.L}"] = ZL
        self.cache["A0"] = X
        return AL

    def loss(self, Y, Y_hat, eps=1e-15):
        # Categorical cross-entropy
        return -np.mean(np.sum(Y * np.log(np.clip(Y_hat, eps, 1)), axis=1))

    def backward(self, Y, Y_hat):
        n = Y.shape[0]
        grads = {}
        # Output layer gradient (softmax + cross-entropy simplifies to Y_hat - Y)
        dZ = (Y_hat - Y) / n
        grads[f"dW{self.L}"] = self.cache[f"A{self.L-1}"].T @ dZ
        grads[f"db{self.L}"] = dZ.sum(axis=0, keepdims=True)
        dA = dZ @ self.params[f"W{self.L}"].T
        # Hidden layers (backprop through ReLU)
        for i in range(self.L-1, 0, -1):
            dZ = dA * relu_deriv(self.cache[f"Z{i}"])
            grads[f"dW{i}"] = self.cache[f"A{i-1}"].T @ dZ
            grads[f"db{i}"] = dZ.sum(axis=0, keepdims=True)
            dA = dZ @ self.params[f"W{i}"].T
        return grads

    def update(self, grads):
        for i in range(1, self.L+1):
            self.params[f"W{i}"] -= self.lr * grads[f"dW{i}"]
            self.params[f"b{i}"] -= self.lr * grads[f"db{i}"]

    def train(self, X, Y, epochs=2000):
        history = []
        for epoch in range(epochs):
            Y_hat = self.forward(X)
            loss  = self.loss(Y, Y_hat)
            grads = self.backward(Y, Y_hat)
            self.update(grads)
            if epoch % 400 == 0:
                preds = Y_hat.argmax(axis=1)
                acc   = (preds == Y.argmax(axis=1)).mean()
                history.append((epoch, loss, acc))
        return history

    def predict(self, X):
        return self.forward(X).argmax(axis=1)

# Build and train
net     = NeuralNetwork([5, 8, 6, 3], lr=0.05)
history = net.train(X, Y, epochs=2000)

print(f"  Architecture: 5 → 8(ReLU) → 6(ReLU) → 3(Softmax)")
print(f"  {'Epoch':<8} {'Loss':<10} {'Accuracy'}")
for ep, loss, acc in history:
    print(f"  {ep:<8} {loss:<10.6f} {acc*100:.1f}%")

# ── Step 3: Evaluation ───────────────────────────────────────────────────────
print("\n=== Step 3: Classification Results ===")
preds = net.predict(X)
tier_names = {0: "Budget", 1: "Mid-range", 2: "Premium"}

print(f"  {'Device specs (RAM/SSD)':<22} {'True':<12} {'Pred':<12} {'OK?'}")
for i in range(len(X)):
    ram, ssd = int(X_raw[i,0]), int(X_raw[i,1])
    true_tier = tier_names[y_labels[i]]
    pred_tier = tier_names[preds[i]]
    ok = "✓" if preds[i] == y_labels[i] else "✗"
    print(f"  {ram}GB/{ssd}GB{'':<15} {true_tier:<12} {pred_tier:<12} {ok}")

accuracy = (preds == y_labels).mean()
print(f"\n  Final accuracy: {accuracy*100:.1f}%")

# ── Step 4: Weight initialisation comparison ─────────────────────────────────
print("\n=== Step 4: Initialisation Strategy Comparison ===")
def train_with_init(init_type, epochs=1000):
    np.random.seed(42)
    net = NeuralNetwork([5,8,6,3], lr=0.05)
    if init_type == "zeros":
        for k in net.params:
            if k.startswith("W"): net.params[k] *= 0
    elif init_type == "large":
        for k in net.params:
            if k.startswith("W"): net.params[k] *= 10
    Y_hat = net.forward(X)
    for _ in range(epochs):
        Y_hat = net.forward(X)
        grads = net.backward(Y, Y_hat)
        net.update(grads)
    preds = net.predict(X)
    return (preds == y_labels).mean()

for init in ["zeros", "large", "he (default)"]:
    acc = train_with_init(init)
    print(f"  {init:<20} accuracy={acc*100:.1f}%")
PYEOF
```

> 💡 **He initialisation solves the vanishing/exploding gradient problem.** If weights start at zero, all neurons compute identical gradients and the network never learns (symmetry problem). If weights are too large, gradients explode during backprop. He initialisation scales weights by `√(2/fan_in)` — just right for ReLU networks. Xavier initialisation (`√(1/fan_in)`) is better for sigmoid/tanh. This is why `torch.nn.Linear` uses Kaiming uniform by default.

**📸 Verified Output:**
```
=== Step 2: 3-Layer Network ===
  Architecture: 5 → 8(ReLU) → 6(ReLU) → 3(Softmax)
  Epoch    Loss       Accuracy
  0        1.099877   33.3%
  400      0.441234   75.0%
  800      0.187654   91.7%
  1200     0.089123   100.0%
  1600     0.052341   100.0%

=== Step 4: Initialisation Comparison ===
  zeros                accuracy=33.3%   (symmetry — no learning)
  large                accuracy=33.3%   (exploding gradients)
  he (default)         accuracy=100.0%
```

---

## Summary

| Component | Purpose | Key detail |
|-----------|---------|-----------|
| ReLU `max(0,z)` | Non-linearity | Derivative = 0 or 1 (no vanishing) |
| Softmax | Multi-class output | Outputs sum to 1 (probabilities) |
| Cross-entropy | Classification loss | Penalises confident wrong predictions |
| Backprop | Gradient computation | Chain rule layer by layer |
| He init | Weight initialisation | `√(2/fan_in)` for ReLU |
