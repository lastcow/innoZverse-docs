# Supervised Learning

## Algorithms Overview

| Algorithm | Type | Use Case | Pros |
|-----------|------|----------|------|
| Linear Regression | Regression | Price prediction | Fast, interpretable |
| Logistic Regression | Classification | Binary classification | Probabilistic output |
| Decision Tree | Both | Tabular data | Interpretable |
| Random Forest | Both | General purpose | Robust, accurate |
| Gradient Boosting | Both | Kaggle competitions | Often best accuracy |
| SVM | Both | High-dimensional | Effective with small data |
| KNN | Both | Simple baseline | No training required |

## Scikit-learn Examples

```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix

# Random Forest
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Feature importance
importances = pd.Series(rf.feature_importances_, index=X_train.columns)
print(importances.sort_values(ascending=False).head(10))

# Cross-validation
scores = cross_val_score(rf, X, y, cv=5, scoring='accuracy')
print(f"CV Accuracy: {scores.mean():.3f} ± {scores.std():.3f}")

# Hyperparameter tuning
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20],
    'min_samples_split': [2, 5, 10]
}
grid_search = GridSearchCV(rf, param_grid, cv=5, n_jobs=-1)
grid_search.fit(X_train, y_train)
print(f"Best params: {grid_search.best_params_}")

# Evaluation
y_pred = rf.predict(X_test)
print(classification_report(y_test, y_pred))
```
