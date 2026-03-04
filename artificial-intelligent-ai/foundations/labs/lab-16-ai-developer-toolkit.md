# Lab 16: AI Developer Toolkit — APIs, SDKs, LangChain, and Vector Databases

## Objective

Get hands-on with the tools professional AI developers use. By the end you will be able to:

- Call LLM APIs directly using SDKs
- Use LangChain to build chains and agents
- Understand vector databases and why they're essential for AI apps
- Architect a complete AI application stack

---

## The Modern AI Application Stack

```
┌─────────────────────────────────────────────────────┐
│                  USER INTERFACE                     │
│          (web app, mobile app, chatbot)             │
├─────────────────────────────────────────────────────┤
│               APPLICATION LAYER                     │
│      (orchestration: LangChain / LangGraph)         │
├──────────────┬──────────────────┬───────────────────┤
│   LLM APIs   │  Vector Database │   Traditional DB  │
│  (OpenAI /   │  (Pinecone /     │  (PostgreSQL /    │
│  Anthropic / │   Chroma /       │   MongoDB /       │
│  Google)     │   Weaviate)      │   Redis)          │
├──────────────┴──────────────────┴───────────────────┤
│                INFRASTRUCTURE                       │
│       (Docker / Kubernetes / Cloud)                 │
└─────────────────────────────────────────────────────┘
```

---

## LLM APIs: The Foundation

### OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")  # or set OPENAI_API_KEY env var

# Basic completion
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a cybersecurity expert."},
        {"role": "user",   "content": "Explain XSS in one paragraph."}
    ],
    temperature=0.7,
    max_tokens=500
)
print(response.choices[0].message.content)

# Structured output (guaranteed JSON)
from pydantic import BaseModel

class VulnerabilityReport(BaseModel):
    name: str
    severity: str   # critical/high/medium/low
    cvss_score: float
    affected_versions: list[str]
    remediation: str

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Describe CVE-2021-44228 (Log4Shell)"}],
    response_format=VulnerabilityReport,
)
report: VulnerabilityReport = response.choices[0].message.parsed
print(f"Severity: {report.severity}, CVSS: {report.cvss_score}")
```

### Anthropic (Claude) SDK

```python
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")

# Basic message
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a helpful assistant for InnoZverse students.",
    messages=[
        {"role": "user", "content": "What's the difference between authentication and authorisation?"}
    ]
)
print(message.content[0].text)

# Streaming
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=500,
    messages=[{"role": "user", "content": "Explain TCP handshake step by step"}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# Vision: analyse an image
import base64
with open("network_diagram.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=500,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
            {"type": "text", "text": "Identify any security vulnerabilities in this network diagram."}
        ]
    }]
)
```

### Google Gemini SDK

```python
import google.generativeai as genai

genai.configure(api_key="AI...")

model = genai.GenerativeModel("gemini-1.5-pro")

# Chat session with history
chat = model.start_chat(history=[])

response = chat.send_message("What is a buffer overflow?")
print(response.text)

response2 = chat.send_message("Give me a Python example that demonstrates it")
print(response2.text)

# The chat object maintains conversation history automatically
print(f"Messages in history: {len(chat.history)}")
```

---

## LangChain: Orchestration Framework

LangChain provides building blocks for composing LLM applications:

### Chains

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser

# LCEL (LangChain Expression Language): compose with | pipe operator
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Chain 1: generate a quiz question
question_chain = (
    ChatPromptTemplate.from_template(
        "Generate a multiple choice question about {topic} for a student "
        "studying for CompTIA Security+. Include 4 options (A-D) and mark the correct answer."
    )
    | llm
    | StrOutputParser()
)

# Chain 2: evaluate student answer
evaluation_chain = (
    ChatPromptTemplate.from_template(
        "Question: {question}\nStudent answered: {student_answer}\n"
        "Is the student correct? Explain in one sentence."
    )
    | llm
    | StrOutputParser()
)

# Use chains
question = question_chain.invoke({"topic": "SQL injection"})
print(question)

feedback = evaluation_chain.invoke({
    "question": question,
    "student_answer": "B - Input validation"
})
print(feedback)
```

### Agents with Tools

```python
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain import hub

@tool
def search_cve_database(cve_id: str) -> str:
    """Search the CVE database for vulnerability details. Input: CVE ID like CVE-2021-44228"""
    import requests
    url = f"https://cve.circl.lu/api/cve/{cve_id}"
    response = requests.get(url, timeout=5)
    if response.ok:
        data = response.json()
        return f"CVE: {cve_id}\nDescription: {data.get('summary', 'Not found')}\nCVSS: {data.get('cvss', 'N/A')}"
    return f"CVE {cve_id} not found"

@tool
def calculate_risk_score(severity: str, exploitability: str, asset_value: str) -> str:
    """Calculate a risk score. Inputs: severity (low/medium/high/critical), exploitability (low/medium/high), asset_value (low/medium/high/critical)"""
    scores = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    total = scores[severity] * scores[exploitability] * scores[asset_value]
    rating = "Critical" if total >= 36 else "High" if total >= 12 else "Medium" if total >= 4 else "Low"
    return f"Risk score: {total}/64 — {rating} Risk"

llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [search_cve_database, calculate_risk_score]
prompt = hub.pull("hwchase17/openai-tools-agent")

agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({
    "input": "Look up CVE-2021-44228 and calculate its risk for a high-value database server"
})
```

---

## Vector Databases: AI's Long-Term Memory

Traditional databases store structured data and search by exact match. **Vector databases** store embeddings (high-dimensional vectors) and search by **semantic similarity**.

### Why Vector Databases?

```python
# Traditional DB: exact match
SELECT * FROM documents WHERE content LIKE '%SQL injection%'
# Finds: "SQL injection explained"
# Misses: "how to prevent database attacks via input manipulation"
#         (same concept, different words)

# Vector DB: semantic search
results = vector_db.search("database attack via input manipulation", top_k=5)
# Finds ALL documents about SQL injection regardless of exact wording
# Because their embeddings are mathematically close
```

### Chroma (Local, Python)

```python
import chromadb
from chromadb.utils import embedding_functions

# Initialise local vector database
client = chromadb.PersistentClient(path="./my_vectordb")

# Use Sentence Transformers for embeddings (free, local)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# Create a collection (like a table)
collection = client.create_collection(
    name="cybersecurity_labs",
    embedding_function=emb_fn
)

# Add documents — embeddings computed automatically
collection.add(
    documents=[
        "SQL injection occurs when user input is concatenated directly into SQL queries",
        "XSS allows attackers to inject malicious scripts into web pages",
        "CSRF tricks authenticated users into making unintended requests",
        "Buffer overflow writes beyond allocated memory, overwriting the call stack",
    ],
    ids=["doc1", "doc2", "doc3", "doc4"],
    metadatas=[
        {"lab": "practitioner-03", "severity": "critical"},
        {"lab": "advanced-08",     "severity": "high"},
        {"lab": "practitioner-18", "severity": "medium"},
        {"lab": "advanced-16",     "severity": "high"},
    ]
)

# Semantic search
results = collection.query(
    query_texts=["how do attackers exploit input fields?"],
    n_results=2
)
print(results["documents"])
# → ["SQL injection occurs...", "XSS allows attackers..."]
# Both are relevant! Even though the query doesn't match either exactly
```

### Pinecone (Cloud, Production-Scale)

```python
from pinecone import Pinecone

pc = Pinecone(api_key="your-pinecone-key")

# Create index (dimension must match your embedding model)
index = pc.Index("innozverse-knowledge-base")  # 1536 dimensions for text-embedding-3-small

# Upsert vectors
vectors = [
    ("lab-01", embed("History of AI content..."), {"category": "foundations", "lab": 1}),
    ("lab-02", embed("How AI works content..."), {"category": "foundations", "lab": 2}),
]
index.upsert(vectors=vectors, namespace="ai-foundations")

# Query by semantic similarity
results = index.query(
    vector=embed("What is the difference between ML and deep learning?"),
    top_k=3,
    namespace="ai-foundations",
    filter={"category": "foundations"},  # metadata filtering
    include_metadata=True
)
for match in results["matches"]:
    print(f"Score: {match['score']:.3f}  Lab: {match['metadata']['lab']}")
```

---

## Building a Complete AI App: Tech Stack Example

```python
# InnoZverse AI Tutor — complete stack example

# 1. FastAPI backend
from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
import anthropic

app = FastAPI()
vector_db = chromadb.PersistentClient(path="./knowledge_base")
collection = vector_db.get_collection("labs")
claude = anthropic.Anthropic()

class Question(BaseModel):
    question: str
    student_level: str = "foundations"

@app.post("/ask")
async def answer_question(q: Question):
    # Step 1: retrieve relevant lab content
    results = collection.query(
        query_texts=[q.question],
        n_results=3,
        where={"level": q.student_level}
    )
    context = "\n\n".join(results["documents"][0])

    # Step 2: generate grounded answer
    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=f"""You are an InnoZverse tutor for {q.student_level} students.
Answer questions using the provided course content.
Reference specific labs when relevant.
If the answer isn't in the context, say so honestly.""",
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {q.question}"
        }]
    )
    return {
        "answer": response.content[0].text,
        "sources": results["metadatas"][0]
    }
```

---

## Tools at a Glance

| Tool | Category | Use When |
|------|---------|---------|
| OpenAI Python SDK | LLM API | Building on GPT models |
| Anthropic SDK | LLM API | Building on Claude models |
| Google Generative AI | LLM API | Building on Gemini |
| LangChain | Orchestration | Complex chains, agents, RAG |
| LangGraph | Orchestration | Multi-step stateful workflows |
| Chroma | Vector DB | Local development, small scale |
| Pinecone | Vector DB | Production, millions of vectors |
| Weaviate | Vector DB | Self-hosted production |
| Qdrant | Vector DB | High performance, open source |
| FastAPI | Backend | Building AI-powered APIs |
| Streamlit | Frontend | Quick AI demos and tools |
| Gradio | Frontend | ML model interfaces |

---

## Further Reading

- [OpenAI Cookbook](https://cookbook.openai.com/)
- [Anthropic Developer Documentation](https://docs.anthropic.com/)
- [LangChain Documentation](https://python.langchain.com/docs/)
- [Chroma Documentation](https://docs.trychroma.com/)
- [Vector Database Comparison](https://ann-benchmarks.com/)
