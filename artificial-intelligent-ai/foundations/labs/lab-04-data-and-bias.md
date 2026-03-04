# Lab 04: Data is Everything — Datasets, Bias, and the Garbage-In Problem

## Objective

Understand why data quality determines AI quality. By the end you will be able to:

- Explain why "more data" is not always better
- Identify the main types of dataset bias and their real-world consequences
- Describe how major training datasets are built
- Apply basic data quality checks before training any model

---

## The Fundamental Truth

> *"Garbage in, garbage out."* — IBM, 1957

Every ML model is a compressed reflection of its training data. It cannot know things that weren't in the data. It will repeat every bias, error, and gap in the data — often amplified.

A 99% accurate model trained on biased data is a precise, reliable bias-generator.

---

## What Makes a Good Dataset?

**Five dimensions of data quality:**

| Dimension | Question | Bad Example |
|-----------|----------|-------------|
| **Volume** | Enough examples? | 50 images to train a face detector |
| **Variety** | Covers all real-world cases? | Only light-skinned faces in training set |
| **Accuracy** | Labels are correct? | Mislabelled medical scans |
| **Recency** | Reflects current reality? | 2010 data for 2024 fraud detection |
| **Representativeness** | Matches deployment distribution? | English-only training for global product |

---

## Famous Training Datasets

| Dataset | Size | Domain | Used For |
|---------|------|--------|----------|
| **ImageNet** | 14M images, 1,000 classes | Vision | AlexNet, ResNet, all vision benchmarks |
| **Common Crawl** | ~250B web pages | Text | GPT-3, LLaMA, most LLMs |
| **Wikipedia** | ~6.7M articles (English) | Text | BERT pre-training |
| **LAION-5B** | 5.85B image-text pairs | Vision-language | DALL-E, Stable Diffusion |
| **The Pile** | 825GB curated text | Text | EleutherAI open models |
| **MS COCO** | 330K images + captions | Vision | Object detection, captioning |

> 💡 **Scale insight:** GPT-4 was estimated to train on ~13 trillion tokens — roughly 10,000× all the books ever published in English.

---

## Types of Dataset Bias

### 1. Historical Bias

The data reflects historical inequalities, which the model then perpetuates.

**Example:** Amazon's AI recruiting tool (2018) trained on 10 years of résumés — which came mostly from men because the tech industry is male-dominated. The model learned to penalise résumés that contained the word "women's" (as in "women's chess club"). Amazon scrapped it.

```python
# Detecting historical bias: check label distribution by group
import pandas as pd

df = pd.read_csv("loan_applications.csv")
approval_by_race = df.groupby("race")["approved"].mean()

print(approval_by_race)
# White:    0.73
# Black:    0.45
# Hispanic: 0.49
# Asian:    0.68
# ← Is this disparity from actual creditworthiness or historical discrimination?
```

### 2. Representation Bias

Some groups are underrepresented in the training data.

**Example:** Facial recognition systems (2018 MIT study by Joy Buolamwini):
- Error rate for light-skinned men: **0.8%**
- Error rate for dark-skinned women: **34.7%**

The training datasets (Adience, IJB-A) were overwhelmingly light-skinned. The models were accurate — on the data they were trained on.

### 3. Measurement Bias

The way data is collected or labelled introduces systematic errors.

**Example:** Predicting hospital readmission. "Healthcare cost" is used as a proxy for "health needs." But Black patients, on average, have lower healthcare costs because they receive less healthcare — not because they're healthier. The model learned to predict cost, not need, and systematically underestimated the health needs of Black patients. (Obermeyer et al., *Science*, 2019)

### 4. Aggregation Bias

Using one model for multiple subgroups when different subgroups have different underlying patterns.

**Example:** Blood glucose prediction models trained on a mixed population may perform well on average but poorly for diabetic patients with atypical presentations.

### 5. Deployment Bias

The model is used in a context different from where it was trained.

**Example:** A depression screening model trained on Twitter data from the USA deployed in the UK — cultural expressions of distress differ. Performance degrades. Errors aren't caught because the deployers don't have ground truth.

---

## The Data Pipeline

```
Raw Sources → Collection → Cleaning → Labelling → Splitting → Training
                 │              │           │
             web scraping    dedup      crowdwork
             surveys         filter     expert annotation
             sensors         format     RLHF (for LLMs)
```

### Data Splits: The Cardinal Rule

```python
# Always split BEFORE any preprocessing
from sklearn.model_selection import train_test_split

# 70% train, 15% validation, 15% test
X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176)

# NEVER touch test set until final evaluation
# Peeking at test data → inflated performance → real-world failure
```

**Data leakage** is the #1 source of misleadingly good model performance:
- Train/test split after normalisation (test statistics leak into training)
- Future information in features (tomorrow's stock price to predict today's)
- Duplicate records spanning train and test sets

---

## Data Preprocessing Basics

```python
import pandas as pd
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("dataset.csv")

# 1. Check for missing values
print(df.isnull().sum())
# Fill or drop: df.fillna(df.mean()) or df.dropna()

# 2. Check class balance
print(df["label"].value_counts(normalize=True))
# Output: class 0: 95%, class 1: 5%  ← imbalanced!
# Fix: oversample minority (SMOTE) or undersample majority

# 3. Check for outliers
print(df.describe())  # max values way beyond 75th percentile?

# 4. Normalise numerical features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[["age", "income", "credit_score"]])
# Now all features have mean=0, std=1
# Models converge faster; no feature dominates due to scale
```

---

## Synthetic Data — The New Frontier

When real data is scarce, biased, or private, **synthetic data** can help:

- **GANs** generate realistic medical images where patient data is restricted
- **Simulation** (games, physics engines) generates infinite labelled data for robotics
- **LLMs** generate synthetic training data for other LLMs (a controversial practice called "model collapse" when done naively)

> 💡 **2024 trend:** Meta's Llama 3 used synthetically generated instruction data. OpenAI's GPT-4 was reportedly used to generate training data for smaller models. The line between "real" and "synthetic" training data is blurring rapidly.

---

## Practical Data Quality Checklist

Before training any model:

- [ ] Are all classes represented proportionally to their real-world frequency?
- [ ] Is the test set truly held out (no leakage)?
- [ ] Are labels consistent (inter-annotator agreement > 80%)?
- [ ] Is the data recent enough for the deployment context?
- [ ] Have you audited performance across demographic subgroups?
- [ ] Is there a data card documenting collection methodology?
- [ ] Do you have consent/rights to use this data?

---

## Summary

The model is only as good as the data. No algorithm, however sophisticated, can overcome:
- Missing subgroups in training data
- Mislabelled examples
- Historical bias baked into labels
- Data leakage between splits

The best AI practitioners spend **80% of their time on data** and 20% on modelling.

---

## Further Reading

- [Datasheets for Datasets (Gebru et al., 2021)](https://arxiv.org/abs/1803.09010)
- [Gender Shades — Joy Buolamwini](http://gendershades.org/)
- [Failing Loudly: An Empirical Study of Methods for Detecting Dataset Shift](https://arxiv.org/abs/1810.11953)
- [Kaggle Data Cleaning Course](https://www.kaggle.com/learn/data-cleaning)
