# Working with LLMs

## OpenAI API

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

# Chat completion
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Explain Docker in simple terms."}
    ],
    temperature=0.7,
    max_tokens=500
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Write a haiku about Linux"}],
    stream=True
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)
```

## HuggingFace Transformers

```python
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

# Zero-shot classification
classifier = pipeline("zero-shot-classification")
result = classifier(
    "This product exceeded my expectations!",
    candidate_labels=["positive review", "negative review", "neutral review"]
)

# Text generation with local model
tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")

inputs = tokenizer("Explain machine learning:", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## Prompt Engineering

```python
# Zero-shot
prompt = "Classify this review as positive or negative: 'Great product!'"

# Few-shot
prompt = """
Classify reviews as positive or negative:

Review: "Amazing quality!" → Positive
Review: "Broke after 2 days" → Negative
Review: "Fast shipping, great price" → Positive
Review: "Terrible customer service" → ?
"""

# Chain of thought
prompt = """
Problem: If I buy 3 Surface Pros at $999 each and get a 10% student discount, 
what's the total?

Let's think step by step:
"""
```
