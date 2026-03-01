# NLP Fundamentals

## Text Preprocessing Pipeline

```python
import re
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer

nltk.download(['punkt', 'stopwords', 'wordnet'])

text = "Machine learning is transforming the world! Let's learn it."

# 1. Lowercase
text = text.lower()

# 2. Remove special characters
text = re.sub(r'[^a-zA-Z\s]', '', text)

# 3. Tokenize
tokens = word_tokenize(text)

# 4. Remove stopwords
stop_words = set(stopwords.words('english'))
tokens = [t for t in tokens if t not in stop_words]

# 5. Lemmatize (better than stemming)
lemmatizer = WordNetLemmatizer()
tokens = [lemmatizer.lemmatize(t) for t in tokens]

print(tokens)
# ['machine', 'learning', 'transforming', 'world', 'let', 'learn']
```

## Text Vectorization

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim.models import Word2Vec

# TF-IDF
tfidf = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
X = tfidf.fit_transform(documents)

# Word2Vec embeddings
model = Word2Vec(sentences, vector_size=100, window=5, min_count=1)
vector = model.wv['machine']    # 100-dim vector
similar = model.wv.most_similar('python', topn=5)
```

## Sentiment Analysis

```python
from transformers import pipeline

# Pre-trained sentiment model
sentiment = pipeline("sentiment-analysis")
results = sentiment([
    "Innozverse is an amazing platform!",
    "The delivery was delayed and I'm unhappy."
])
# [{'label': 'POSITIVE', 'score': 0.9998}, {'label': 'NEGATIVE', 'score': 0.9987}]
```
