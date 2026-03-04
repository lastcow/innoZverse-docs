# Lab 05: Neural Networks Demystified — Perceptrons to Deep Learning

## Objective

Build intuition for how neural networks actually work — from a single neuron to GPT-scale models. By the end you will understand:

- What a neuron computes mathematically
- How layers build increasingly abstract representations
- What activation functions, loss functions, and optimisers do
- The key architectural families: CNNs, RNNs, Transformers

---

## The Neuron: One Unit of Computation

A biological neuron receives signals from other neurons, sums them, and fires if the sum exceeds a threshold. The artificial neuron does the same — but with mathematics:

```
                    w₁
x₁ ───────────────▶ ×  ⎤
                    w₂  ⎥
x₂ ───────────────▶ ×  ⎥──▶ Σ ──▶ f(Σ) ──▶ output
                    w₃  ⎥
x₃ ───────────────▶ ×  ⎦  + bias (b)
```

**Mathematically:**
```
output = f(w₁x₁ + w₂x₂ + w₃x₃ + b)
```

Where:
- **xᵢ** = inputs (features)
- **wᵢ** = weights (learned parameters)
- **b** = bias (learned offset)
- **f** = activation function (introduces non-linearity)

```python
import numpy as np

def neuron(x, w, b, activation='relu'):
    """Single artificial neuron"""
    z = np.dot(w, x) + b          # weighted sum
    if activation == 'relu':
        return max(0, z)           # ReLU: max(0, z)
    elif activation == 'sigmoid':
        return 1 / (1 + np.exp(-z))  # sigmoid: squash to (0,1)

# Example: 3 inputs
x = np.array([0.5, -0.3, 0.8])
w = np.array([0.4,  0.7, -0.2])
b = 0.1

output = neuron(x, w, b, activation='relu')
print(f"Neuron output: {output:.4f}")
```

---

## Activation Functions: The Non-Linearity Source

Without activation functions, stacking layers is useless — multiple linear transformations compose into one linear transformation.

| Function | Formula | Shape | Used In |
|----------|---------|-------|---------|
| **Sigmoid** | 1/(1+e⁻ˣ) | S-curve, (0,1) | Binary output |
| **Tanh** | (eˣ-e⁻ˣ)/(eˣ+e⁻ˣ) | S-curve, (-1,1) | RNNs |
| **ReLU** | max(0, x) | Flat then linear | Hidden layers (default) |
| **GELU** | x·Φ(x) | Smooth ReLU | Transformers, BERT, GPT |
| **Softmax** | eˣⁱ/Σeˣ | Probability distribution | Multiclass output |

```python
import numpy as np

def relu(x):    return np.maximum(0, x)
def sigmoid(x): return 1 / (1 + np.exp(-x))
def softmax(x): e = np.exp(x - x.max()); return e / e.sum()

# Softmax: convert raw scores to probabilities
logits = np.array([2.0, 1.0, 0.1])         # raw outputs
probs  = softmax(logits)
print(probs)  # → [0.659, 0.242, 0.099]  (sum = 1.0)
# Model is 65.9% confident in class 0
```

---

## Layers: Building Abstraction

Each layer transforms the representation from the previous layer into something more useful:

```
Input (raw pixels 28×28=784)
    ↓ Layer 1: Linear(784→256) + ReLU
    → Detects edges, corners, gradients
    ↓ Layer 2: Linear(256→128) + ReLU
    → Detects curves, shapes, stroke patterns
    ↓ Layer 3: Linear(128→10)  + Softmax
    → "This is the digit 7"
```

```python
import torch
import torch.nn as nn

class MNISTClassifier(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Dropout(0.2),      # randomly zero 20% of neurons → prevents overfitting
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 10),
            # No activation here — CrossEntropyLoss applies softmax internally
        )

    def forward(self, x):
        return self.net(x.view(-1, 784))  # flatten 28×28 to 784
```

---

## The Loss Function: Measuring Wrongness

The **loss** quantifies how far the model's predictions are from the truth. Training minimises this.

```python
# Binary Cross-Entropy (for binary classification)
def binary_cross_entropy(y_pred, y_true):
    # Penalises being confidently wrong more than being uncertain
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))

# Example:
y_true = 1          # correct answer: spam
y_pred_good = 0.95  # confident and correct
y_pred_bad  = 0.05  # confident and WRONG

loss_good = binary_cross_entropy(y_pred_good, y_true)  # → 0.051  (small penalty)
loss_bad  = binary_cross_entropy(y_pred_bad,  y_true)  # → 2.996  (large penalty)
```

| Loss Function | Use Case |
|--------------|----------|
| Binary Cross-Entropy | Binary classification (spam/not) |
| Categorical Cross-Entropy | Multiclass (digit 0–9) |
| Mean Squared Error | Regression (house prices) |
| Huber Loss | Regression, outlier-robust |

---

## Backpropagation: Learning by Attribution

The chain rule from calculus tells us: how much did each weight contribute to the total loss?

```
Forward pass:
x → w₁ → h₁ → w₂ → h₂ → w₃ → ŷ → Loss

Backward pass (backprop):
∂L/∂w₃ = ∂L/∂ŷ · ∂ŷ/∂w₃
∂L/∂w₂ = ∂L/∂ŷ · ∂ŷ/∂h₂ · ∂h₂/∂w₂
∂L/∂w₁ = ∂L/∂ŷ · ∂ŷ/∂h₂ · ∂h₂/∂h₁ · ∂h₁/∂w₁
```

PyTorch handles this automatically with autograd — every operation records itself and the chain rule is applied backwards automatically.

```python
x = torch.tensor([1.0, 2.0], requires_grad=False)
w = torch.tensor([0.5, -0.3], requires_grad=True)  # we want gradient of w

y = (w * x).sum()  # forward computation
y.backward()       # backprop: compute ∂y/∂w

print(w.grad)      # → tensor([1., 2.])  ← gradient tells us how to update w
```

---

## Optimisers: How Weights Update

**Gradient descent:** nudge every weight in the direction that reduces loss.

```python
# Stochastic Gradient Descent (SGD)
# w_new = w_old - learning_rate × gradient
for param in model.parameters():
    param.data -= learning_rate * param.grad

# Adam (Adaptive Moment Estimation) — the modern default
# Adapts learning rate per-parameter; tracks momentum
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
optimizer.step()  # applies update
optimizer.zero_grad()  # clear gradients for next batch
```

**Learning rate:** the most important hyperparameter.
- Too high → overshoots minimum, loss oscillates or diverges
- Too low → training is extremely slow
- **Learning rate scheduling** reduces LR over time

---

## Architectural Families

### Convolutional Neural Networks (CNNs) — for Images

Instead of connecting every neuron to every other (expensive), CNNs use **filters** that slide across the image — detecting the same feature anywhere in the image (translation invariance).

```python
# 2D convolution: detect horizontal edges
conv = nn.Conv2d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
pool = nn.MaxPool2d(kernel_size=2)  # halves spatial dimensions

# Feature map: 28×28 → 32 filters of 14×14
```

### Recurrent Neural Networks (RNNs/LSTMs) — for Sequences

Process sequences step-by-step, maintaining a **hidden state** (memory).

```python
lstm = nn.LSTM(input_size=100, hidden_size=256, num_layers=2, batch_first=True)
# Problem: vanishing gradients over long sequences
# Solution: attention mechanisms → Transformers
```

### Transformers — for Everything

Process the entire sequence at once using **self-attention**: each position attends to all other positions simultaneously.

```python
# Multi-head self-attention (conceptual)
attention_output = softmax(Q @ K.T / sqrt(d_k)) @ V
# Q = queries, K = keys, V = values
# Each token computes how much to "attend" to every other token
```

The Transformer replaced RNNs as the dominant architecture for NLP (2017) and is now being applied to images (ViT), audio, and multimodal data.

---

## Overfitting vs Underfitting

```
         Loss
          │
          │  Training loss
   high   │ ─────────────────────────────────
          │                                 Overfitting region
          │  Validation loss                (memorising training data)
          │ ──────────────────────┐
          │                       └─────────
   low    │
          └──────────────────────────────────▶ Training steps
                              ↑
                         Ideal stopping point (early stopping)
```

**Regularisation techniques to combat overfitting:**

| Technique | How It Works |
|-----------|-------------|
| Dropout | Randomly disable neurons during training |
| Weight Decay (L2) | Penalise large weights |
| Data Augmentation | Artificially expand training set |
| Early Stopping | Stop when validation loss stops improving |
| Batch Normalisation | Normalise layer outputs → smoother training |

---

## Summary

| Concept | One-line Description |
|---------|---------------------|
| Neuron | Weighted sum + activation function |
| Layer | Group of neurons transforming one representation to another |
| Activation | Non-linearity that lets deep networks learn complex patterns |
| Loss | Numerical measure of how wrong the model is |
| Backprop | Chain rule applied backwards to compute gradients |
| Optimiser | Algorithm that uses gradients to update weights |
| CNN | Spatial feature detection via sliding filters |
| Transformer | Parallel sequence processing via self-attention |

---

## Further Reading

- [Neural Networks — 3Blue1Brown (YouTube)](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi)
- [CS231n — Convolutional Neural Networks (Stanford)](https://cs231n.github.io/)
- [The Illustrated Transformer — Jay Alammar](https://jalammar.github.io/illustrated-transformer/)
- [fast.ai Practical Deep Learning](https://course.fast.ai/)
