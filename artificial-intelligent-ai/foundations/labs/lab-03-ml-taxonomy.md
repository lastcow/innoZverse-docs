# Lab 03: The Machine Learning Taxonomy — Supervised, Unsupervised, Reinforcement

## Objective

Map the landscape of machine learning approaches. By the end you will understand:

- The three main ML paradigms and when to use each
- Key algorithms in each category
- Real-world applications of each approach
- How self-supervised learning powers modern LLMs

---

## The Three Main Paradigms

```
                        MACHINE LEARNING
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
    Supervised          Unsupervised         Reinforcement
    Learning              Learning             Learning
    (labelled data)    (no labels needed)  (learn from rewards)
          │                   │                   │
    ┌─────┴─────┐       ┌─────┴─────┐       ┌─────┴─────┐
Classification Regression Clustering Generative  Policy
  (cat/dog)  (house price) (segments) (GANs, VAE) (games, robots)
```

---

## 1. Supervised Learning

The most common paradigm. Every training example has an **input** and a **known correct output** (label). The model learns the mapping.

**Two subtypes:**

### Classification — "Which category?"

Output is a discrete class label.

```python
# Binary classification: email spam detection
from sklearn.linear_model import LogisticRegression

# X: feature vectors (word counts, etc.)
# y: 0=not spam, 1=spam
model = LogisticRegression()
model.fit(X_train, y_train)

probability = model.predict_proba(["Buy now!!"])[0][1]
# → 0.94  (94% probability of spam)
```

**Examples:**
- Email spam / not spam
- Medical image: tumour / benign
- Credit application: approve / deny
- Sentiment: positive / neutral / negative

### Regression — "How much?"

Output is a continuous number.

```python
# House price prediction
from sklearn.ensemble import GradientBoostingRegressor

# Features: bedrooms, location, size, age
model = GradientBoostingRegressor(n_estimators=200)
model.fit(X_train, y_prices)

predicted_price = model.predict([[4, 'London', 120, 5]])
# → [£485,000]
```

**Examples:**
- House price prediction
- Stock price forecasting
- Demand forecasting
- Temperature prediction

### Common Supervised Algorithms

| Algorithm | Best For | Interpretable? |
|-----------|----------|---------------|
| Linear/Logistic Regression | Baseline, simple relationships | ✅ Yes |
| Decision Trees | Categorical features, non-linear | ✅ Yes |
| Random Forest | Tabular data, robust | Partially |
| Gradient Boosting (XGBoost) | Competitions, tabular data | Partially |
| Support Vector Machine | High-dimensional, small data | Partially |
| Neural Networks | Images, text, complex patterns | ❌ No |

---

## 2. Unsupervised Learning

No labels. The model must find **structure in the data** on its own.

### Clustering — "Which group?"

Find natural groupings in data.

```python
from sklearn.cluster import KMeans

# Customer segmentation: no labels, just features
kmeans = KMeans(n_clusters=4, random_state=42)
kmeans.fit(customer_features)  # purchase history, demographics

segments = kmeans.labels_
# → [0, 2, 1, 3, 0, 2, ...]
# Segment 0: high-value frequent buyers
# Segment 1: price-sensitive occasional buyers
# ...
```

**Examples:**
- Customer segmentation
- Document clustering (group similar articles)
- Anomaly detection (the point that doesn't fit any cluster)
- Gene expression analysis

### Dimensionality Reduction — "What's essential?"

Compress high-dimensional data while preserving structure.

```python
from sklearn.decomposition import PCA

# 500-dimensional word embeddings → 2D for visualisation
pca = PCA(n_components=2)
embeddings_2d = pca.fit_transform(word_embeddings_500d)

# Now plot — similar words appear near each other
# "king" near "queen", "London" near "Paris"
```

**Examples:**
- Visualising high-dimensional data (t-SNE, UMAP)
- Feature compression before training
- Noise removal from signals
- Recommendation: compress user preferences to latent factors

### Generative Models — "Create new data"

Learn the underlying distribution of the training data to generate new samples.

**GANs (Generative Adversarial Networks):**
```
Generator          Discriminator
(creates fake) → (real or fake?) → feedback → Generator improves
      ↑                                              │
      └──────────────── adversarial game ────────────┘
```

**VAEs (Variational Autoencoders):**
```
Input → Encoder → Latent space (z) → Decoder → Reconstructed input
                     │
                  sample z → generate new variation
```

---

## 3. Reinforcement Learning

The model (agent) learns by taking **actions** in an **environment** and receiving **rewards** or **penalties**. No labelled data — just trial and error.

```
┌──────────┐  action  ┌─────────────┐
│  AGENT   │ ───────▶ │ ENVIRONMENT │
│          │ ◀─────── │             │
└──────────┘  reward  └─────────────┘
             + state
```

```python
# Q-learning: conceptual (cartpole balancing)
import gymnasium as gym

env = gym.make("CartPole-v1")
state, _ = env.reset()

# Agent chooses action based on Q-values (learned value of each action)
action = agent.select_action(state)   # 0=left, 1=right
next_state, reward, done, _, _ = env.step(action)

# Update Q-values based on reward received
agent.update(state, action, reward, next_state)
```

**Famous RL successes:**
- AlphaGo / AlphaZero — board games
- OpenAI Five — Dota 2 at world championship level
- AlphaStar — StarCraft II
- ChatGPT — RLHF (humans rate responses; model learns to maximise ratings)
- Robotics — Boston Dynamics locomotion
- Data centre cooling — DeepMind reduced Google's cooling costs 40%

**RL is hard because:**
- Sparse rewards — agent may do 10,000 actions before getting any feedback
- Reward hacking — agent finds unintended ways to maximise reward
- Sample inefficiency — requires millions of episodes to learn

---

## 4. Self-Supervised Learning — The Modern Paradigm

The paradigm that powers LLMs. **Labels come from the data itself** — no human annotation needed.

**Masked Language Modelling (BERT):**
```
Input:  "The [MASK] sat on the mat"
Target: predict [MASK] = "cat"
```

**Next Token Prediction (GPT):**
```
Input:  "The cat sat on the"
Target: predict next token = "mat"
```

By training on trillions of tokens from the internet using these self-supervised tasks, the model is forced to develop deep understanding of language, facts, reasoning patterns, and world knowledge — without a single human-labelled example.

This is the key insight behind modern LLMs: **language modelling at scale = general intelligence**.

---

## Choosing the Right Approach

```
Do you have labelled data?
├── YES → Supervised Learning
│         ├── Output is a category? → Classification
│         └── Output is a number?   → Regression
└── NO  → Do you know the reward signal?
          ├── YES → Reinforcement Learning (games, robotics, RLHF)
          └── NO  → Unsupervised Learning
                    ├── Find groups?     → Clustering
                    ├── Compress data?  → Dimensionality Reduction
                    └── Generate data?  → GANs, VAEs, Diffusion
```

---

## Summary

| Paradigm | Signal | Typical Use | Example Models |
|----------|--------|-------------|----------------|
| Supervised | Labelled data | Classification, regression | XGBoost, ResNet, BERT |
| Unsupervised | None | Clustering, generation | K-Means, GAN, VAE |
| Reinforcement | Reward signal | Games, robotics, alignment | PPO, AlphaZero |
| Self-supervised | Labels from data | LLMs, vision-language | GPT, CLIP, DALL-E |

---

## Further Reading

- [ML Cheatsheet — Supervised vs Unsupervised](https://ml-cheatsheet.readthedocs.io)
- [Spinning Up in Deep RL — OpenAI](https://spinningup.openai.com/)
- [The Illustrated BERT — Jay Alammar](https://jalammar.github.io/illustrated-bert/)
- [Kaggle Learn — Machine Learning](https://www.kaggle.com/learn/machine-learning)
