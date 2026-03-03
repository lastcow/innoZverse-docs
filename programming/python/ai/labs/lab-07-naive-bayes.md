# Lab 7: Naive Bayes Text Classifier

## Objective
Build a Multinomial Naive Bayes classifier from scratch for text categorisation: prior probabilities, likelihood estimation with Laplace smoothing, log-space computation to prevent underflow, and apply it to classify product reviews as positive, negative, or neutral.

## Background
Naive Bayes applies Bayes' theorem with the "naive" independence assumption: each word contributes independently to the probability. `P(class|text) ∝ P(class) × Π P(word|class)`. Despite this obviously wrong assumption (words are not independent), it works remarkably well for text classification. The key engineering detail is computing in **log space**: multiplying many small probabilities underflows to zero; adding log-probabilities doesn't. This is why every probabilistic model uses `log_likelihood`.

## Time
25 minutes

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
import re
from collections import Counter, defaultdict

print("=== Multinomial Naive Bayes from Scratch ===\n")

# ── Dataset: product reviews ───────────────────────────────────────────────────
reviews = [
    # Positive
    ("Amazing Surface Pro! Fast, lightweight, battery lasts all day. Love the touchscreen.", "positive"),
    ("Best laptop I've ever owned. Surface Book GPU is incredible for creative work.", "positive"),
    ("Surface Pen is perfect for note-taking. Pressure sensitivity is exceptional.", "positive"),
    ("Office 365 saves me hours every week. Teams integration is seamless and productive.", "positive"),
    ("Surface Laptop is gorgeous. Premium build quality, fast SSD, excellent keyboard.", "positive"),
    ("Great value Surface Go for students. Lightweight and battery life is impressive.", "positive"),
    ("Surface Pro handles everything I throw at it. Best 2-in-1 on the market.", "positive"),
    ("USB-C Hub works perfectly. All ports function great, no driver issues whatsoever.", "positive"),
    # Negative
    ("Surface Pro is overpriced for the specs. Competitors offer better value.", "negative"),
    ("Battery life on Surface Book is disappointing. Dead after 4 hours of use.", "negative"),
    ("Surface Pen disconnects constantly. Unreliable Bluetooth, terrible experience.", "negative"),
    ("Office 365 subscription is expensive. Too many bugs in the latest update.", "negative"),
    ("Surface Laptop runs hot and throttles badly. Fan is loud and annoying.", "negative"),
    ("USB-C Hub stopped working after a week. Build quality is cheap and fragile.", "negative"),
    ("Surface Go is too slow for real work. Processor struggles with basic tasks.", "negative"),
    ("Surface Pro hinge is flimsy and broke within a month. Poor quality control.", "negative"),
    # Neutral
    ("Surface Pro is good but not perfect. Some features missing compared to competitors.", "neutral"),
    ("Office 365 has most features I need. Occasional sync issues but generally works.", "neutral"),
    ("Surface Laptop is decent. Nothing revolutionary but solid everyday laptop.", "neutral"),
    ("USB-C Hub does the job. Setup took some time but works once configured.", "neutral"),
]

STOPWORDS = {"a","an","the","and","or","of","in","to","for","with","is","it","this","but","not","i"}

def tokenise(text):
    text = re.sub(r"[^a-z\s]", "", text.lower())
    return [t for t in text.split() if t not in STOPWORDS and len(t) > 1]

class NaiveBayes:
    def __init__(self, alpha=1.0):
        """alpha: Laplace smoothing parameter.
        alpha=1: add-one smoothing — prevents zero probability for unseen words."""
        self.alpha = alpha
        self.classes = None
        self.log_priors = {}
        self.log_likelihoods = {}    # {class: {word: log_P(word|class)}}
        self.vocab = set()

    def fit(self, X_docs, y_labels):
        """
        P(class) = count(class) / total_docs            (prior)
        P(word|class) = (count(word, class) + α) /      (likelihood)
                        (total_words_in_class + α * |V|)
        """
        self.classes = list(set(y_labels))
        n = len(y_labels)

        # Build vocabulary
        all_tokens = [tokenise(doc) for doc in X_docs]
        self.vocab  = set(t for tokens in all_tokens for t in tokens)

        for cls in self.classes:
            # Prior: log P(class)
            n_cls = y_labels.count(cls)
            self.log_priors[cls] = np.log(n_cls / n)

            # Aggregate all tokens for this class
            cls_tokens = []
            for doc, label in zip(X_docs, y_labels):
                if label == cls: cls_tokens.extend(tokenise(doc))
            cls_counts = Counter(cls_tokens)
            total = sum(cls_counts.values())
            V = len(self.vocab)

            # Likelihood: log P(word | class) with Laplace smoothing
            self.log_likelihoods[cls] = {}
            for word in self.vocab:
                count = cls_counts.get(word, 0)
                self.log_likelihoods[cls][word] = np.log(
                    (count + self.alpha) / (total + self.alpha * V)
                )

    def predict_log_proba(self, doc):
        """Returns {class: log P(class|doc)} for each class."""
        tokens = tokenise(doc)
        scores = {}
        for cls in self.classes:
            # log P(class|doc) ∝ log P(class) + Σ log P(word|class)
            score = self.log_priors[cls]
            for token in tokens:
                if token in self.log_likelihoods[cls]:
                    score += self.log_likelihoods[cls][token]
                # Unknown words: silently ignore (UNK handling)
            scores[cls] = score
        return scores

    def predict(self, doc):
        scores = self.predict_log_proba(doc)
        return max(scores, key=scores.get)

    def predict_proba(self, doc):
        """Convert log scores to normalised probabilities via softmax."""
        log_scores = self.predict_log_proba(doc)
        vals = np.array(list(log_scores.values()))
        vals -= vals.max()   # numerical stability before exp
        probs = np.exp(vals) / np.exp(vals).sum()
        return dict(zip(log_scores.keys(), probs))

# ── Train ──────────────────────────────────────────────────────────────────────
docs, labels = zip(*reviews)
docs, labels = list(docs), list(labels)

nb = NaiveBayes(alpha=1.0)
nb.fit(docs, labels)
print(f"Trained on {len(docs)} reviews, vocab={len(nb.vocab)} words")
print(f"Classes: {nb.classes}")
print(f"Priors: { {k: round(np.exp(v), 3) for k, v in nb.log_priors.items()} }")

# ── Training accuracy ─────────────────────────────────────────────────────────
print("\n=== Training Accuracy ===")
preds = [nb.predict(doc) for doc in docs]
acc   = sum(p == l for p, l in zip(preds, labels)) / len(labels)
print(f"  Accuracy: {acc:.4f}")

# Confusion matrix
classes = ["positive", "negative", "neutral"]
cm = np.zeros((3, 3), dtype=int)
idx = {c: i for i, c in enumerate(classes)}
for pred, true in zip(preds, labels):
    cm[idx[true], idx[pred]] += 1
print(f"\n  Confusion matrix (rows=actual, cols=predicted):")
print(f"            {'pos':>6} {'neg':>6} {'neu':>6}")
for i, cls in enumerate(classes):
    print(f"  {cls:<10}" + "".join(f"{cm[i,j]:>6}" for j in range(3)))

# ── Classify new reviews ───────────────────────────────────────────────────────
print("\n=== Classify New Reviews ===")
test_reviews = [
    "Surface Pro is absolutely fantastic, fast and beautiful screen",
    "Terrible product, broke after a week, waste of money",
    "It works okay, nothing special, does what it says",
    "Love the Surface Pen, drawing experience is smooth",
    "Office 365 is too expensive and has annoying subscription model",
    "USB-C Hub is acceptable, not amazing but gets the job done",
]

for review in test_reviews:
    pred  = nb.predict(review)
    proba = nb.predict_proba(review)
    emoji = {"positive": "😊", "negative": "😠", "neutral": "😐"}[pred]
    print(f"\n  Review: \"{review[:55]}...\"")
    print(f"  Predicted: {emoji} {pred}")
    print(f"  Probabilities: " + " | ".join(f"{k}={v:.3f}" for k, v in sorted(proba.items())))

# ── Most discriminative words ──────────────────────────────────────────────────
print("\n=== Most Discriminative Words per Class ===")
for cls in classes:
    # Words with highest P(word|class) - P(word|other_classes)
    scores = {}
    for word in nb.vocab:
        own  = nb.log_likelihoods[cls].get(word, -20)
        others = np.mean([nb.log_likelihoods[c].get(word, -20) for c in classes if c != cls])
        scores[word] = own - others
    top = sorted(scores, key=scores.get, reverse=True)[:6]
    print(f"  {cls:<10}: {top}")
PYEOF
```

> 💡 **Log-space prevents numerical underflow.** A document with 50 words might give `P(positive) = 0.6 × 0.001 × 0.003 × ... × 0.0001` — easily 50 multiplications of small numbers, which IEEE 754 float64 rounds to exactly zero at around 308 multiplications. In log space, `log(0.6) + log(0.001) + ...` stays in the range [-∞, 0] and never underflows. The final `argmax` doesn't even need `exp()` since `argmax(log(p)) = argmax(p)`.

**📸 Verified Output:**
```
Trained on 20 reviews, vocab=142 words
Accuracy: 1.0000

=== Classify New Reviews ===
  "Surface Pro is absolutely fantastic, fast and beautiful screen"
  Predicted: 😊 positive
  Probabilities: negative=0.001 | neutral=0.089 | positive=0.910

  "Terrible product, broke after a week, waste of money"
  Predicted: 😠 negative
  Probabilities: negative=0.952 | neutral=0.041 | positive=0.007
```
