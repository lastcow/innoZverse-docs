# MLOps — Production ML Systems

MLOps applies DevOps principles to machine learning — enabling reliable, scalable, and reproducible ML in production.

## MLOps Maturity Levels

```
Level 0: Manual process
  → Train locally, deploy manually, no monitoring

Level 1: ML pipeline automation
  → Automated training pipelines, feature store, model registry

Level 2: CI/CD for ML
  → Automated testing, continuous training, A/B deployment
```

## ML Pipeline Architecture

```
[Data Sources] → [Feature Store] → [Training Pipeline]
                                          ↓
[Model Registry] ← [Experiment Tracking (MLflow)]
        ↓
[Model Serving] → [A/B Testing] → [Monitoring]
        ↓
[Drift Detection] → [Retrain Trigger] → back to Training Pipeline
```

## MLflow — Experiment Tracking

```python
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier

mlflow.set_tracking_uri("http://mlflow-server:5000")
mlflow.set_experiment("surface-demand-prediction")

with mlflow.start_run():
    # Log parameters
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    mlflow.log_param("features", X_train.columns.tolist())

    # Train
    model = RandomForestClassifier(n_estimators=100, max_depth=10)
    model.fit(X_train, y_train)

    # Log metrics
    mlflow.log_metric("accuracy", model.score(X_test, y_test))
    mlflow.log_metric("f1_score", f1_score(y_test, model.predict(X_test)))

    # Log model
    mlflow.sklearn.log_model(model, "model", registered_model_name="demand-predictor")
```

## Model Serving (FastAPI + Docker)

```python
# serve.py
import mlflow
from fastapi import FastAPI
import pandas as pd

app = FastAPI()
model = mlflow.sklearn.load_model("models:/demand-predictor/Production")

@app.post("/predict")
async def predict(data: dict):
    df = pd.DataFrame([data])
    prediction = model.predict(df)[0]
    probability = model.predict_proba(df)[0].max()
    return {"prediction": int(prediction), "confidence": float(probability)}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY serve.py .
CMD ["uvicorn", "serve:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Model Monitoring & Drift Detection

```python
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, ClassificationPreset

# Compare training data vs production data
report = Report(metrics=[DataDriftPreset(), ClassificationPreset()])
report.run(reference_data=training_df, current_data=production_df)
report.save_html("drift_report.html")

# Alert if drift detected
drift_summary = report.as_dict()
if drift_summary['metrics'][0]['result']['dataset_drift']:
    trigger_retraining_pipeline()
```
