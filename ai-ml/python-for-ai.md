# Python for AI

Python is the language of AI. These are the essential libraries you need.

## Core Libraries

```python
import numpy as np          # Numerical computing
import pandas as pd         # Data manipulation
import matplotlib.pyplot as plt  # Visualization
import sklearn              # Machine learning
import torch                # Deep learning (PyTorch)
import tensorflow as tf     # Deep learning (TensorFlow)
```

## NumPy Basics

```python
import numpy as np

# Create arrays
a = np.array([1, 2, 3, 4, 5])
matrix = np.zeros((3, 3))
random = np.random.rand(100)

# Operations
print(a.mean())     # 3.0
print(a.std())      # Standard deviation
print(a * 2)        # Element-wise: [2, 4, 6, 8, 10]
```

## Pandas Basics

```python
import pandas as pd

df = pd.read_csv('data.csv')
print(df.head())
print(df.describe())        # Statistics
print(df.isnull().sum())    # Missing values

# Filter
high_scores = df[df['score'] > 90]

# Group by
avg_by_category = df.groupby('category')['score'].mean()
```

## Scikit-learn Quick Start

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = LogisticRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, predictions):.2%}")
```
