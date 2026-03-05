# Lab 13: AI Data Pipeline Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

ML data pipelines are the foundation of every AI system. This lab covers batch vs streaming architectures (Lambda/Kappa), feature engineering at scale, data versioning with DVC, validation with Great Expectations, lineage tracking, and feature store design patterns.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               ML Data Pipeline Architecture                  │
├────────────────────────┬─────────────────────────────────────┤
│    LAMBDA ARCHITECTURE │    KAPPA ARCHITECTURE               │
│  ─────────────────     │  ──────────────────────             │
│  Batch Layer (Spark)   │  Streaming Layer only               │
│  Speed Layer (Flink)   │  (Kafka + Flink)                    │
│  Serving Layer         │  Re-processing = replay topic       │
│  Merge at query time   │  Simpler, but streaming-first       │
├────────────────────────┴─────────────────────────────────────┤
│  Feature Engineering → Data Versioning → Validation          │
│        ↓                    (DVC)           (GE)             │
│  Feature Store (Feast) → Training Data → Model               │
└──────────────────────────────────────────────────────────────┘
```

---

## Step 1: Batch ETL vs Streaming Architectures

**Batch ETL (Traditional):**
```
Source systems → nightly extract → transform → load to data warehouse
Latency: hours to days
Best for: reports, training data, non-time-critical features
Technology: Apache Spark, dbt, Airflow
```

**Streaming (Real-time):**
```
Source → Kafka → Flink/Spark Streaming → feature store
Latency: milliseconds to seconds
Best for: fraud detection, real-time personalization
Technology: Kafka, Apache Flink, Kafka Streams
```

**Lambda Architecture:**
```
Data Source
    ↓
├── Batch Layer (HDFS/S3): complete historical data, Spark jobs run daily
│       ↓ batch views
├── Speed Layer (Kafka+Flink): recent data, streaming microlatency
│       ↓ real-time views
└── Serving Layer: merges batch + speed views for queries

Pro: complete historical accuracy + real-time freshness
Con: two code paths = double maintenance, operational complexity
```

**Kappa Architecture:**
```
All data → Kafka (indefinite retention)
                ↓
        Flink streaming job (always running)
                ↓
        Feature Store / Serving Layer

Pro: single code path, simpler
Con: streaming is harder to develop, reprocessing = replay Kafka topic
Use when: team is streaming-native, latency < minutes required
```

> 💡 Most enterprises start with Lambda (batch + streaming) and migrate to Kappa as streaming maturity grows. Don't over-engineer — pure batch solves 80% of problems.

---

## Step 2: Feature Engineering at Scale

**Scale Challenges:**
```
100M users × 500 features × daily refresh = 50 billion feature values
Need: Distributed computation, efficient storage, fast serving
```

**Feature Engineering Tools:**

| Tool | Type | Scale | Best For |
|------|------|-------|---------|
| Pandas | Single-node | < 1M rows | Prototyping, exploration |
| Spark (PySpark) | Distributed | Billions of rows | Production batch features |
| Dask | Distributed Python | Medium | Python-native, parallel |
| Flink | Streaming | Real-time | Event-time streaming features |
| DBT | SQL transform | Millions-billions | SQL-native teams |

**Feature Types:**
```
Static features:  Customer demographics (rarely change)
Time-series:      Transaction count in last 7/30/90 days
Event-based:      Last login timestamp, days_since_purchase
Behavioral:       Click-through rate, session duration
Interaction:      User × Item features for recommendation
Cross features:   feature_A × feature_B combinations
```

**Window Aggregations (Most Common ML Features):**
```python
# Feast feature definition
Feature('txn_count_7d', ValueType.INT64, 
        source=Feature('transactions', aggregation=FeatureView.COUNT,
                        window=timedelta(days=7)))

Feature('avg_amount_30d', ValueType.FLOAT,
        source=Feature('transactions', aggregation=FeatureView.MEAN,
                        window=timedelta(days=30)))
```

---

## Step 3: Data Versioning with DVC

DVC (Data Version Control) treats data like code — version, share, and reproduce.

**DVC Workflow:**
```
git init
dvc init
dvc add data/training_set.parquet    # track large files in DVC, not git
git add data/training_set.parquet.dvc
git commit -m "training data v2.1"

# Share with team
dvc push                              # push data to S3/GCS
git push                              # push .dvc pointers to git

# Reproduce exact dataset
git checkout v1.0
dvc pull                              # download data from that commit
```

**DVC Pipelines:**
```yaml
# dvc.yaml
stages:
  preprocess:
    cmd: python preprocess.py
    deps:
      - data/raw/customers.csv
      - preprocess.py
    outs:
      - data/processed/features.parquet
  
  train:
    cmd: python train.py
    deps:
      - data/processed/features.parquet
      - train.py
    outs:
      - models/model.pkl
    metrics:
      - metrics/accuracy.json
```

**Benefits:**
```
Reproducibility: exact data + code → exact model
Collaboration: share large datasets without git bloat
Experimentation: switch between data versions easily
Audit trail: know which data produced which model
```

---

## Step 4: Data Validation with Great Expectations

Data quality is the #1 silent killer of ML model performance.

**Great Expectations (GE) Concepts:**

| Concept | Definition |
|---------|-----------|
| Expectation Suite | Collection of data quality rules |
| Expectation | Individual rule: "column_A must not be null" |
| Data Docs | Auto-generated data quality reports |
| Checkpoint | Run expectations against new data |
| Validation Result | Pass/fail result with statistics |

**Common Expectations:**
```python
# Schema expectations
expect_column_to_exist("customer_id")
expect_column_values_to_be_of_type("age", "int64")

# Statistical expectations
expect_column_values_to_be_between("age", min_value=18, max_value=120)
expect_column_values_to_not_be_null("customer_id", mostly=0.99)
expect_column_mean_to_be_between("income", min_value=20000, max_value=200000)

# Distribution expectations
expect_column_proportion_of_unique_values_to_be_between("customer_id", 0.99, 1.0)
expect_column_values_to_be_in_set("status", ["active", "inactive", "churned"])
```

**GE in ML Pipeline:**
```
New data arrives → run Checkpoint → all expectations pass?
                                        ↓ YES: proceed to training
                                        ↓ NO: quarantine data, alert, investigate
```

---

## Step 5: Data Lineage Tracking

**Lineage Graph Example:**
```
raw_transactions.parquet
      ↓ (spark transformation)
customer_features_v1.parquet
      ↓ (feature engineering)
training_dataset_2024_Q1.parquet
      ↓ (model training: run_42)
fraud_model_v2.3.pkl
      ↓ (deployment)
fraud_detection_service (production)
```

**What Lineage Enables:**
```
Impact analysis: "If we change feature_X, which models are affected?"
Audit: "Which data was used to train the model that made this decision?"
Root cause: "Why did model performance drop? → trace back to data change"
Compliance: "Prove this model was trained on approved, unbiased data"
```

**Lineage Tools:**
- **Apache Atlas**: Enterprise, integrates with Hadoop/Spark
- **OpenLineage**: Open standard, vendor-neutral
- **Marquez**: OpenLineage reference implementation
- **DataHub (LinkedIn)**: Comprehensive data catalog + lineage
- **MLflow**: ML-specific lineage (model → data → code)

---

## Step 6: Feature Store Design (Feast)

**Feast Architecture:**
```
Feature Definition (Python/YAML)
         ↓
Offline Store (S3 + Parquet/Delta)
         ↓
Online Store Materialization (batch or streaming)
         ↓
Online Store (Redis) → Serving (< 1ms lookup)
```

**Feast Feature View:**
```python
from feast import FeatureStore, Entity, FeatureView, Field
from feast.types import Int64, Float32

customer = Entity(name="customer_id", value_type=ValueType.INT64)

customer_stats_fv = FeatureView(
    name="customer_stats",
    entities=["customer_id"],
    ttl=timedelta(days=30),
    schema=[
        Field(name="transaction_count_7d", dtype=Int64),
        Field(name="avg_amount_30d", dtype=Float32),
        Field(name="days_since_last_login", dtype=Int64),
    ],
    online=True,
    source=bigquery_source,
)

# Training: point-in-time correct join
training_df = store.get_historical_features(
    entity_df=entity_df,  # customer_id + event_timestamp
    features=["customer_stats:transaction_count_7d"]
).to_df()

# Serving: real-time lookup
online_features = store.get_online_features(
    features=["customer_stats:transaction_count_7d"],
    entity_rows=[{"customer_id": 12345}]
)
```

---

## Step 7: Training-Serving Skew Prevention

**The #1 ML Production Bug:**
```
Training: preprocess with pandas → scaled_age = (age - 35) / 10
Serving: preprocess with different code → scaled_age = age / 100

Result: model sees different features at serving time → silent failure
```

**Prevention Strategies:**
```
1. Feature Store: single source of truth for features
   - Same feature computation used at training and serving time
   - Point-in-time joins prevent future data leakage

2. Shared preprocessing library:
   - training.py and serving.py import same preprocess.py
   - Version the preprocessing code

3. Skew detection in monitoring:
   - Compare training distribution vs serving distribution
   - Alert if significant difference detected
```

---

## Step 8: Capstone — ML Data Pipeline with Feature Versioning

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
from sklearn.model_selection import cross_val_score

np.random.seed(42)
X, y = make_classification(n_samples=500, n_features=10, random_state=42)
df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])
df['target'] = y
df.loc[np.random.choice(df.index, 50), 'feature_0'] = np.nan
df.loc[np.random.choice(df.index, 30), 'feature_1'] = np.nan

print('=== ML Data Pipeline with Feature Versioning ===')
print()
print(f'Raw data shape: {df.shape}')
print(f'Missing values: feature_0={df[\"feature_0\"].isna().sum()}, feature_1={df[\"feature_1\"].isna().sum()}')

print()
print('Data Validation Results:')
validations = {
    'row_count >= 100': len(df) >= 100,
    'no_duplicate_rows': df.duplicated().sum() == 0,
    'target_binary': set(df['target'].unique()) == {0, 1},
    'missing_pct < 20%': df.isna().mean().max() < 0.20,
    'feature_range_valid': (df.drop('target', axis=1).abs() < 10).all().all(),
}
for check, result in validations.items():
    icon = 'PASS' if result else 'FAIL'
    print(f'  [{icon}] {check}')

feature_versions = {
    'v1': {'features': ['feature_0','feature_1','feature_2'], 'created': '2024-01-01', 'accuracy': 0.78},
    'v2': {'features': ['feature_0','feature_1','feature_2','feature_3','feature_4'], 'created': '2024-02-01', 'accuracy': 0.83},
    'v3': {'features': [f'feature_{i}' for i in range(10)], 'created': '2024-03-01', 'accuracy': None},
}

pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler()),
    ('model', LogisticRegression(random_state=42)),
])
scores = cross_val_score(pipeline, df.drop('target', axis=1), df['target'], cv=5)
feature_versions['v3']['accuracy'] = round(scores.mean(), 4)

print()
print('Feature Store Version History:')
for ver, info in feature_versions.items():
    n_feat = len(info['features'])
    acc = info['accuracy'] if info['accuracy'] else 'TBD'
    print(f'  {ver}: {n_feat} features | accuracy={acc} | created={info[\"created\"]}')
print(f'Pipeline CV Score (v3): {scores.mean():.4f} ± {scores.std():.4f}')
"
```

📸 **Verified Output:**
```
=== ML Data Pipeline with Feature Versioning ===

Raw data shape: (500, 11)
Missing values: feature_0=47, feature_1=30

Data Validation Results:
  [PASS] row_count >= 100
  [PASS] no_duplicate_rows
  [PASS] target_binary
  [PASS] missing_pct < 20%
  [FAIL] feature_range_valid

Feature Store Version History:
  v1: 3 features | accuracy=0.78 | created=2024-01-01
  v2: 5 features | accuracy=0.83 | created=2024-02-01
  v3: 10 features | accuracy=0.89 | created=2024-03-01
Pipeline CV Score (v3): 0.8900 ± 0.0089
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Lambda Architecture | Batch + Speed layers merged at query time; complete but complex |
| Kappa Architecture | Streaming only; simpler but streaming-first teams only |
| Feature Engineering at Scale | Spark (batch), Flink (streaming), Feast (feature store) |
| DVC | Version data like code: git-trackable pointers to large files |
| Great Expectations | Automated data validation; block bad data from reaching training |
| Lineage Tracking | Know which data → which model → which decision; audit + debugging |
| Training-Serving Skew | Single feature store = same features at training and serving time |

**Next Lab:** [Lab 14: Responsible AI Audit →](lab-14-responsible-ai-audit.md)
