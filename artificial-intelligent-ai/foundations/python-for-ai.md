# Python for AI

Python is the language of AI and data science. These libraries are essential.

## NumPy — Numerical Computing

```python
import numpy as np

# Create arrays
a = np.array([1, 2, 3, 4, 5])
matrix = np.zeros((3, 3))
identity = np.eye(3)
random = np.random.randn(100)

# Array operations (vectorized — fast!)
print(a * 2)            # [2, 4, 6, 8, 10]
print(a.mean())         # 3.0
print(a.std())          # 1.414...
print(a.reshape(1, 5))  # [[1, 2, 3, 4, 5]]

# Matrix operations
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])
print(A @ B)            # Matrix multiplication
print(np.linalg.inv(A)) # Inverse
```

## Pandas — Data Manipulation

```python
import pandas as pd

# Load data
df = pd.read_csv('data.csv')
df = pd.read_json('data.json')

# Explore
print(df.shape)          # (rows, columns)
print(df.head(10))       # First 10 rows
print(df.describe())     # Statistics
print(df.info())         # Data types, nulls
print(df.isnull().sum()) # Missing values per column

# Filter & select
high_price = df[df['price'] > 1000]
surface_only = df[df['product'].str.contains('Surface')]
cols = df[['name', 'price', 'category']]

# Group & aggregate
summary = df.groupby('category').agg({
    'price': ['mean', 'min', 'max', 'count'],
    'quantity': 'sum'
})

# Handle missing data
df.dropna()                         # Drop rows with NaN
df.fillna(0)                        # Fill NaN with 0
df['price'].fillna(df['price'].mean())  # Fill with mean
```

## Matplotlib — Visualization

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Line plot
plt.figure(figsize=(10, 6))
plt.plot(df['date'], df['sales'], label='Sales', color='blue')
plt.title('Monthly Sales')
plt.xlabel('Date')
plt.ylabel('Revenue ($)')
plt.legend()
plt.tight_layout()
plt.savefig('sales.png', dpi=300)
plt.show()

# Distribution plot
sns.histplot(df['price'], bins=50, kde=True)

# Correlation heatmap
sns.heatmap(df.corr(), annot=True, cmap='coolwarm')
```

## Scikit-learn — Machine Learning

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report

# Prepare data
X = df.drop('target', axis=1)
y = df['target']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = LogisticRegression(max_iter=1000)
model.fit(X_train_scaled, y_train)

# Evaluate
predictions = model.predict(X_test_scaled)
print(classification_report(y_test, predictions))
```
