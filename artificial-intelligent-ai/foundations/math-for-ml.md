# Mathematics for Machine Learning

## Linear Algebra

**Vectors** — 1D arrays of numbers
```python
import numpy as np
v = np.array([3, 4])
print(np.linalg.norm(v))    # Magnitude: 5.0
print(v / np.linalg.norm(v)) # Unit vector
```

**Dot Product** — Similarity measure
```python
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
print(np.dot(a, b))  # 32 = 1*4 + 2*5 + 3*6
```

**Matrix Multiplication** — Core of neural networks
```python
A = np.random.randn(3, 4)  # 3x4 matrix
B = np.random.randn(4, 2)  # 4x2 matrix
C = A @ B                   # 3x2 result
```

## Calculus — Gradients & Backprop

**Gradient** — Direction of steepest ascent
```python
# Numerical gradient approximation
def gradient(f, x, h=1e-5):
    return (f(x + h) - f(x - h)) / (2 * h)

f = lambda x: x**2
print(gradient(f, 3))  # ≈ 6.0 (derivative of x² is 2x)
```

**Chain rule** is the foundation of backpropagation in neural networks.

## Probability & Statistics

```python
import numpy as np
from scipy import stats

data = np.array([2, 4, 4, 4, 5, 5, 7, 9])

print(f"Mean: {data.mean()}")           # 5.0
print(f"Variance: {data.var()}")        # 4.0
print(f"Std Dev: {data.std()}")         # 2.0
print(f"Median: {np.median(data)}")     # 4.5

# Normal distribution
x = np.linspace(-4, 4, 100)
pdf = stats.norm.pdf(x, loc=0, scale=1)

# Softmax (used in classification)
def softmax(x):
    e_x = np.exp(x - x.max())  # Numerical stability
    return e_x / e_x.sum()

logits = np.array([2.0, 1.0, 0.1])
print(softmax(logits))  # [0.659, 0.242, 0.099]
```
