# Python AI & Machine Learning

<table data-view="cards">
  <thead><tr><th></th><th></th></tr></thead>
  <tbody>
    <tr><td><strong>🧮 From Scratch</strong></td><td>Every algorithm implemented in pure NumPy — no scikit-learn, no PyTorch. Understand the math before the framework.</td></tr>
    <tr><td><strong>🛍️ Real Data</strong></td><td>Microsoft Surface product data as the consistent applied context across all 15 labs.</td></tr>
    <tr><td><strong>✅ Verified</strong></td><td>Every code block runs in Docker. Every output block shows real verified results.</td></tr>
  </tbody>
</table>

{% hint style="info" %}
**Prerequisites:** Python Foundations + Practitioner. All labs use only `numpy 2.4.2` and `pandas 3.0.1` — no scikit-learn or PyTorch required.
{% endhint %}

## Quick Start

{% tabs %}
{% tab title="🐳 Docker (Recommended)" %}
```bash
docker pull zchencow/innozverse-python:latest
docker run --rm zchencow/innozverse-python:latest python3 -c "import numpy; print(numpy.__version__)"
```
{% endtab %}
{% tab title="Local" %}
```bash
pip install numpy pandas
python3 -c "import numpy; print(numpy.__version__)"
```
{% endtab %}
{% endtabs %}

---

## Lab Curriculum

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 01 | [Linear Regression](labs/lab-01-linear-regression.md) | MSE, gradient descent, R², normalisation | 35 min |
| 02 | [Logistic Regression](labs/lab-02-logistic-regression.md) | Sigmoid, binary cross-entropy, L2, confusion matrix | 30 min |
| 03 | [Neural Network from Scratch](labs/lab-03-neural-network.md) | Backprop, ReLU, softmax, He init | 40 min |
| 04 | [K-Means Clustering](labs/lab-04-kmeans-clustering.md) | K-Means++, elbow, silhouette, market segmentation | 30 min |
| 05 | [Decision Trees](labs/lab-05-decision-trees.md) | Gini impurity, information gain, pruning, feature importance | 35 min |
| 06 | [K-Nearest Neighbours](labs/lab-06-knn.md) | Distance metrics, weighted voting, ANN context | 25 min |
| 07 | [PCA](labs/lab-07-pca.md) | Covariance, eigenvectors, explained variance, reconstruction | 30 min |
| 08 | [NLP & TF-IDF](labs/lab-08-nlp-tfidf.md) | Tokenisation, TF-IDF, cosine similarity, Naive Bayes | 30 min |
| 09 | [Recommendation Systems](labs/lab-09-recommendation-system.md) | Content-based, collaborative filtering, SVD, hybrid | 30 min |
| 10 | [Time Series](labs/lab-10-time-series.md) | SMA/EMA, decomposition, ACF, AR(p) forecast | 30 min |
| 11 | [Gradient Descent Optimisers](labs/lab-11-gradient-descent-optimisers.md) | SGD, Momentum, RMSProp, Adam, bias correction | 30 min |
| 12 | [Convolutional Operations](labs/lab-12-convolutional-operations.md) | Conv2D, Sobel, Gaussian, pooling, stride/padding | 35 min |
| 13 | [Data Preprocessing](labs/lab-13-data-preprocessing.md) | Imputation, IQR, scaling, encoding, feature selection | 35 min |
| 14 | [Model Evaluation](labs/lab-14-model-evaluation.md) | K-fold CV, stratified CV, metrics, bias-variance | 35 min |
| 15 | [Capstone: Full ML Pipeline](labs/lab-15-capstone.md) | End-to-end: ingest → preprocess → train → ensemble → serialise | 45 min |

**Total: ~500 minutes of hands-on AI/ML from scratch**
