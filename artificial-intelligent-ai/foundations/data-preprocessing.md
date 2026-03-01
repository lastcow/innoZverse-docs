# Data Preprocessing

80% of ML work is data preparation. Good data = good models.

## Common Preprocessing Steps

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder

df = pd.read_csv('dataset.csv')

# 1. Handle missing values
df['age'].fillna(df['age'].median(), inplace=True)
df['category'].fillna('Unknown', inplace=True)
df.dropna(subset=['target'], inplace=True)  # Must have target

# 2. Remove duplicates
df.drop_duplicates(inplace=True)

# 3. Feature encoding
# Label encoding (for ordinal: Low/Medium/High)
le = LabelEncoder()
df['size_encoded'] = le.fit_transform(df['size'])

# One-hot encoding (for nominal categories)
df = pd.get_dummies(df, columns=['color', 'brand'])

# 4. Feature scaling
scaler = StandardScaler()
df[['price', 'age']] = scaler.fit_transform(df[['price', 'age']])

# 5. Outlier detection
Q1 = df['price'].quantile(0.25)
Q3 = df['price'].quantile(0.75)
IQR = Q3 - Q1
df = df[(df['price'] >= Q1 - 1.5*IQR) & (df['price'] <= Q3 + 1.5*IQR)]

# 6. Train/validation/test split
from sklearn.model_selection import train_test_split
X = df.drop('target', axis=1)
y = df['target']
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5)
# Result: 70% train, 15% val, 15% test
```
