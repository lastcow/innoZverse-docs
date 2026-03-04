# Lab 02: How AI Actually Works — Symbols, Statistics, and Neural Nets

## Objective

Strip away the magic and understand the three fundamental approaches to building intelligent systems. By the end you will be able to explain:

- Why symbolic AI works in closed worlds but fails in open ones
- How statistical machine learning learns patterns from data
- What a neural network actually computes
- Why scale changed everything

---

## The Three Paradigms

There is no single "AI." There are three fundamentally different philosophies about what intelligence is and how to build it:

| Paradigm | Core Idea | Example |
|----------|-----------|---------|
| Symbolic AI | Intelligence = manipulating symbols by rules | Chess engines, Prolog, expert systems |
| Statistical ML | Intelligence = patterns extracted from data | Spam filters, recommendation engines |
| Neural Networks | Intelligence = learned representations in layers | GPT-4, image classifiers, AlphaGo |

---

## Paradigm 1: Symbolic AI (The Logic Approach)

Symbolic AI — also called **GOFAI** (Good Old-Fashioned AI) — treats intelligence as rule-following. Knowledge is encoded explicitly:

```prolog
% Prolog: symbolic AI example
parent(tom, bob).
parent(bob, ann).
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).

% Query: grandparent(tom, ann) → true
```

**Strengths:**
- Transparent and explainable — you can inspect every rule
- Guaranteed correct within its domain
- Requires no training data

**Weaknesses:**
- Rules must be written by hand — doesn't scale
- Brittle: any situation not covered by a rule causes failure
- The "frame problem" — maintaining a consistent world-model as things change is computationally intractable

> 💡 **Real example:** Early GPS navigation used symbolic rules: "turn left at junction X." When a road was closed, the system had no idea what to do — it had no ability to reason about novel situations.

---

## Paradigm 2: Statistical Machine Learning

Instead of writing rules, **machine learning** finds patterns in data automatically.

**The key insight:** given enough examples of inputs and correct outputs, an algorithm can learn the mapping between them — without being told the rules.

```python
# Conceptual example: spam classifier
from sklearn.naive_bayes import MultinomialNB

# Training data: emails labelled spam/not-spam
X_train = vectorize(emails)    # convert text to numbers
y_train = labels               # 1 = spam, 0 = not spam

# Learn the pattern from data
model = MultinomialNB()
model.fit(X_train, y_train)

# Predict new emails
prediction = model.predict(["Buy cheap medication now!!!"])
# → [1]  (spam)
```

**Types of ML:**
- **Supervised** — labelled data (spam/not-spam, cat/dog)
- **Unsupervised** — find structure in unlabelled data (clustering customers)
- **Reinforcement** — learn from rewards (game playing, robotics)

**Weaknesses:**
- Requires huge amounts of labelled data
- Black box — hard to explain *why* a prediction was made
- Learns correlations, not causation ("ice cream sales predict drownings")

---

## Paradigm 3: Neural Networks (Deep Learning)

Neural networks were inspired by the brain but are better understood as **function approximators**. A neural network takes numbers in, applies layers of mathematical transformations, and produces numbers out.

### The Perceptron (1957)

The simplest unit — one neuron:

```
inputs → weighted sum → activation function → output

x₁ × w₁ ⎤
x₂ × w₂ ⎥ → Σ → σ(Σ) → y
x₃ × w₃ ⎦
```

The **weights** (w₁, w₂, w₃) are learned from data. The activation function (σ) introduces non-linearity — without it, stacking layers would be pointless (linear × linear = linear).

### Deep Neural Networks

Stack many layers of neurons, and each layer learns increasingly abstract features:

```
Input        Hidden 1       Hidden 2        Output
(pixels) → (edges) →   (shapes) →    (cat/dog)
           low-level    mid-level      high-level
           features     features       concepts
```

```python
# PyTorch: a simple 3-layer neural network
import torch
import torch.nn as nn

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(784, 256),   # 784 inputs (28×28 image)
            nn.ReLU(),             # activation: max(0, x)
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10),   # 10 outputs (digits 0-9)
        )

    def forward(self, x):
        return self.layers(x)

model = SimpleNet()
# Forward pass: input → prediction
output = model(torch.randn(1, 784))
```

### How Training Works

1. **Forward pass** — input flows through the network; prediction is made
2. **Loss calculation** — how wrong was the prediction? (e.g., cross-entropy loss)
3. **Backpropagation** — calculate the gradient of the loss with respect to every weight
4. **Update** — nudge each weight slightly in the direction that reduces loss (gradient descent)
5. Repeat millions of times

```python
# Training loop (conceptual)
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = nn.CrossEntropyLoss()

for batch in dataloader:
    x, y = batch
    prediction = model(x)             # forward pass
    loss = loss_fn(prediction, y)     # how wrong?
    loss.backward()                   # backprop: compute gradients
    optimizer.step()                  # update weights
    optimizer.zero_grad()             # reset gradients
```

---

## Why Scale Changed Everything

For decades, neural networks underperformed simpler methods. Three things changed:

**1. Data** — the internet produced billions of labelled examples (text, images, clicks) that didn't exist before.

**2. Compute** — GPUs, originally designed for video games, turned out to be perfect for the matrix multiplications that neural networks require. Training time dropped from years to days.

**3. Architecture** — the Transformer (2017) enabled efficient parallel training on sequences of any length.

The "bitter lesson" (Rich Sutton, 2019): every time researchers added domain knowledge to AI systems, general-purpose learning methods trained on more data eventually surpassed them. **Scale beats cleverness.**

---

## What Neural Networks Are Really Doing

A neural network is a **compressed statistical summary of its training data**, encoded as billions of floating-point numbers (weights).

When GPT-4 "knows" that Paris is the capital of France, it's not because there's a database lookup. It's because the relationship between tokens "Paris", "capital", and "France" appeared together in patterns across millions of documents, and the weights learned to encode that relationship.

This is why LLMs:
- **Hallucinate** — they generate statistically plausible text, not verified facts
- **Work across domains** — the same weights encode everything they saw during training
- **Improve with scale** — more parameters = more capacity to encode patterns

---

## Summary Comparison

| Property | Symbolic AI | Statistical ML | Deep Learning |
|----------|------------|----------------|---------------|
| Data needed | None (rules written) | Moderate | Massive |
| Explainability | High (inspect rules) | Medium | Low (black box) |
| Generalisation | Poor (brittle) | Good | Excellent |
| Development cost | High (manual rules) | Medium | High (compute) |
| Performance ceiling | Low | Medium | Very high |
| Best for | Closed-world logic | Structured tabular data | Unstructured: text, images, audio |

---

## Further Reading

- [Neural Networks — 3Blue1Brown (visual)](https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi)
- [The Bitter Lesson — Rich Sutton](http://www.incompleteideas.net/IncIdeas/BitterLesson.html)
- [A Visual Introduction to Machine Learning](http://www.r2d3.us/visual-intro-to-machine-learning-part-1/)
- Goodfellow, I. et al. (2016). *Deep Learning*. MIT Press. (free online)
