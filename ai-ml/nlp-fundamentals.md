# NLP Fundamentals

Natural Language Processing enables machines to understand human language.

## Text Preprocessing

```python
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

text = "Machine learning is transforming the world!"

# Tokenize
tokens = word_tokenize(text.lower())
# ['machine', 'learning', 'is', 'transforming', 'the', 'world', '!']

# Remove stopwords
stop_words = set(stopwords.words('english'))
filtered = [w for w in tokens if w not in stop_words]
# ['machine', 'learning', 'transforming', 'world', '!']
```

## Using Transformers (HuggingFace)

```python
from transformers import pipeline

# Sentiment analysis
classifier = pipeline("sentiment-analysis")
result = classifier("Innozverse is an amazing learning platform!")
# [{'label': 'POSITIVE', 'score': 0.9998}]

# Text generation
generator = pipeline("text-generation", model="gpt2")
output = generator("The future of AI is", max_length=50)

# Question answering
qa = pipeline("question-answering")
answer = qa(question="What is Innozverse?",
            context="Innozverse is a student tech store and learning platform.")
```

## Large Language Models (LLMs)

Modern NLP is dominated by LLMs like GPT, Claude, and Gemini. Key concepts:

- **Tokenization** — Text split into subword tokens
- **Attention** — Model focuses on relevant parts of input
- **Fine-tuning** — Adapting pre-trained models to specific tasks
- **RAG** — Retrieval Augmented Generation for factual accuracy
