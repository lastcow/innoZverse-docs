# Lab 15: Open Source vs Closed AI — Hugging Face, Ollama, and Local LLMs

## Objective

Navigate the open vs. closed AI ecosystem. By the end you will be able to:

- Explain the spectrum from fully open to fully proprietary AI
- Set up and run local LLMs with Ollama
- Use Hugging Face to find, download, and deploy open models
- Make informed decisions about when to use open vs. closed models

---

## The Spectrum of Openness

"Open source AI" is not binary — it's a spectrum:

```
MOST OPEN                                           MOST CLOSED
    │                                                    │
    ▼                                                    ▼
Open         Open         Open          Open         Proprietary
weights    weights +    weights +      API +         API only
+ code +   training     code only    no weights
training   data                                      
data
    │           │             │            │              │
TinyLlama   Llama 3 *    Mistral *     Gemini       GPT-4 / Claude
                                       Flash         / Gemini Ultra
```

*Llama and Mistral use "open weights" licences — you can download and modify the weights, but with restrictions (no commercial use above certain scale, no redistribution).

True open source (OSI definition) requires open training data too. Almost no major LLM qualifies because training data includes copyrighted content.

---

## The Case for Closed AI

**Why pay for GPT-4 or Claude when open models are free?**

| Advantage | Detail |
|-----------|--------|
| **Quality** | GPT-4o and Claude 3.5 Sonnet still outperform all open models on hard reasoning tasks (2025) |
| **No infrastructure** | No GPU, no serving cost, no maintenance |
| **Multimodal** | Vision + audio capabilities require frontier models |
| **Safety** | Commercially deployed models have more safety testing |
| **Legal clarity** | Using the API is lower risk than using training data of unclear provenance |
| **Reliability** | 99.9% SLA; managed scaling |

---

## The Case for Open Models

| Advantage | Detail |
|-----------|--------|
| **Privacy** | Data never leaves your infrastructure |
| **Cost at scale** | $0 per token once hardware is acquired |
| **No rate limits** | Run as many requests as your hardware supports |
| **Customisation** | Fine-tune on your proprietary data |
| **Offline** | Works without internet access |
| **No vendor lock-in** | Not dependent on one company's pricing/policy |
| **Transparency** | Some open models release training details |

---

## Running Local LLMs with Ollama

**Ollama** is the simplest way to run LLMs locally. It handles model downloads, serving, and a simple API.

### Installation and Quick Start

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull and run Llama 3.1 (8B parameters, ~5GB)
ollama pull llama3.1
ollama run llama3.1
# → interactive chat in terminal

# Pull a coding-focused model
ollama pull codellama:13b

# Pull a smaller model for resource-limited machines
ollama pull phi3.5        # Microsoft Phi-3.5, 3.8B, excellent quality/size ratio

# List available models
ollama list
```

### Hardware Requirements

| Model Size | RAM Required | GPU (recommended) | Quality |
|-----------|-------------|-------------------|---------|
| 3B–7B | 8GB RAM | 4GB VRAM | Good for simple tasks |
| 13B | 16GB RAM | 8GB VRAM | Good for most tasks |
| 30B–34B | 32GB RAM | 24GB VRAM | Near GPT-3.5 quality |
| 70B | 64GB RAM | 48GB VRAM (2×24GB) | Near GPT-4 quality |

### Ollama REST API

```python
import requests
import json

def ollama_chat(prompt: str, model: str = "llama3.1") -> str:
    """Chat with a local Ollama model"""
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
    )
    return response.json()["message"]["content"]

# Use it like any API
answer = ollama_chat("Explain SQL injection in 3 sentences")
print(answer)

# Streaming response
def ollama_stream(prompt: str, model: str = "llama3.1"):
    """Stream tokens as they're generated"""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": True},
        stream=True
    )
    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            if not data.get("done"):
                print(data["response"], end="", flush=True)
```

---

## Hugging Face: The GitHub of AI

**Hugging Face** hosts 400,000+ models, 100,000+ datasets, and provides the most widely used ML library (`transformers`). It is the central hub of the open AI ecosystem.

```
huggingface.co
│
├── Models    → search, download, use any of 400K+ models
├── Datasets  → download training/benchmark datasets
├── Spaces    → hosted demos (free GPU for demo apps)
├── Hub       → store your own models/datasets
└── Inference API → run models via API without local hardware
```

### Using the Transformers Library

```python
from transformers import pipeline

# Sentiment analysis — downloads model automatically
classifier = pipeline("sentiment-analysis")
result = classifier("The InnoZverse course is incredibly well structured!")
print(result)
# [{'label': 'POSITIVE', 'score': 0.9998}]

# Text generation with a specific model
generator = pipeline(
    "text-generation",
    model="microsoft/phi-2",    # 2.7B parameter model
    device=0                     # use GPU if available
)
output = generator(
    "def fibonacci(n):",
    max_new_tokens=100,
    temperature=0.1
)
print(output[0]["generated_text"])
```

### Searching for the Right Model

```python
from huggingface_hub import HfApi

api = HfApi()

# Find top models for a specific task
models = api.list_models(
    task="text-generation",
    sort="downloads",
    direction=-1,     # descending
    limit=10
)

for m in models:
    print(f"{m.modelId:<40} Downloads: {m.downloads:>10,}")

# Output:
# meta-llama/Llama-3.1-8B-Instruct          Downloads:  2,847,291
# mistralai/Mistral-7B-Instruct-v0.2        Downloads:  1,943,102
# microsoft/phi-3.5-mini-instruct           Downloads:  1,204,847
# ...
```

---

## Top Open Models (2025)

### Text Generation

| Model | Params | Licence | Strengths |
|-------|--------|---------|-----------|
| **Llama 3.1** (Meta) | 8B–405B | Llama Community | Best overall open model |
| **Mistral 7B / Mixtral 8×7B** | 7B / 47B | Apache 2.0 | Fast, efficient, truly open |
| **Phi-3.5-mini** (Microsoft) | 3.8B | MIT | Tiny but surprisingly capable |
| **Gemma 2** (Google) | 2B–27B | Gemma | Strong coding, safe |
| **DeepSeek-V3** | 685B (MoE) | MIT | Frontier quality, open weights |
| **Qwen 2.5** (Alibaba) | 7B–72B | Apache 2.0 | Excellent multilingual |

### Coding

| Model | Notes |
|-------|-------|
| **CodeLlama** | Meta; optimised for code generation |
| **DeepSeek-Coder-V2** | State-of-the-art open coding model |
| **Starcoder 2** | BigCode; trained on 600+ programming languages |

### Embeddings (for RAG, search, similarity)

```python
from sentence_transformers import SentenceTransformer

# Best open embedding model (2024)
model = SentenceTransformer("BAAI/bge-large-en-v1.5")

sentences = [
    "How does SQL injection work?",
    "SQL injection is a code injection technique",
    "My cat loves tuna fish"
]
embeddings = model.encode(sentences)
# Compute similarity
from sklearn.metrics.pairwise import cosine_similarity
sim = cosine_similarity(embeddings)
print(sim[0][1])  # 0.87 — high similarity (same topic)
print(sim[0][2])  # 0.12 — low similarity (unrelated)
```

---

## Fine-Tuning Open Models

Open weights = you can train further on your own data:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# Load base model
model_name = "meta-llama/Llama-3.1-8B-Instruct"
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

# LoRA: efficient fine-tuning — train only 1% of parameters
# (reduces memory from 80GB to ~12GB for 8B model)
lora_config = LoraConfig(
    r=16,                    # rank of adaptation matrices
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],  # which layers to adapt
    lora_dropout=0.1,
    bias="none",
    task_type="CAUSAL_LM"
)
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# trainable params: 3,407,872 || all params: 8,033,669,120
# → only 0.04% of parameters are trained!

# Fine-tune on your dataset
trainer = SFTTrainer(
    model=model,
    train_dataset=your_dataset,     # (instruction, response) pairs
    max_seq_length=2048,
    num_train_epochs=3,
)
trainer.train()
trainer.save_model("my-finetuned-llama")
```

---

## When to Use Which

```python
decision = {
    "sensitive_data": {
        "recommendation": "Local/open model",
        "reason": "Data never leaves your infrastructure"
    },
    "maximum_quality_needed": {
        "recommendation": "GPT-4o or Claude Sonnet",
        "reason": "Frontier closed models still lead on hard tasks"
    },
    "high_volume_cost_sensitive": {
        "recommendation": "Fine-tuned open model",
        "reason": "$0 per token at scale; custom domain knowledge"
    },
    "quick_prototype": {
        "recommendation": "Any API (OpenAI/Anthropic/Google)",
        "reason": "No infrastructure setup; iterate fast"
    },
    "regulated_industry": {
        "recommendation": "Open model, self-hosted",
        "reason": "Data residency requirements; auditability"
    },
    "offline_or_edge": {
        "recommendation": "Phi-3.5-mini via Ollama",
        "reason": "Runs on laptop/phone; no internet required"
    }
}
```

---

## Further Reading

- [Hugging Face Hub](https://huggingface.co/models)
- [Ollama Model Library](https://ollama.ai/library)
- [Open LLM Leaderboard](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard)
- [LLM.int8() — Efficient quantisation (Dettmers et al.)](https://arxiv.org/abs/2208.07339)
- [QLoRA: Efficient Finetuning](https://arxiv.org/abs/2305.14314)
