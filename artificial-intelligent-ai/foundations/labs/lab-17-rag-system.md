# Lab 17: Building a RAG System — Retrieval-Augmented Generation in Practice

## Objective

Build a complete RAG (Retrieval-Augmented Generation) pipeline. By the end you will be able to:

- Explain why RAG solves hallucination and knowledge cutoff problems
- Implement the full RAG pipeline: ingest → embed → retrieve → generate
- Apply chunking strategies for different document types
- Evaluate RAG system quality

---

## What is RAG and Why Does It Exist?

LLMs have two fundamental limitations:

1. **Knowledge cutoff** — they only know what was in their training data (e.g., before April 2024)
2. **Hallucination** — they generate plausible-sounding but potentially false information when uncertain

RAG solves both by **retrieving relevant documents at query time** and providing them as context:

```
WITHOUT RAG:
  User: "What were InnoZverse's Q3 2025 results?"
  LLM:  "InnoZverse's Q3 2025 results showed..."  [HALLUCINATION]

WITH RAG:
  User: "What were InnoZverse's Q3 2025 results?"
  Step 1: Search knowledge base for "InnoZverse Q3 2025"
  Step 2: Retrieve: actual_q3_report.pdf, pages 3-7
  Step 3: "Based on the Q3 2025 report: revenue was £4.2M..."  [GROUNDED]
```

---

## The RAG Architecture

```
INDEXING PIPELINE (offline):
  Documents → Chunking → Embedding → Vector Store

RETRIEVAL PIPELINE (online, at query time):
  Query → Embed query → Similarity search → Top-K chunks → LLM → Answer
```

---

## Step 1: Document Ingestion and Chunking

Raw documents must be split into chunks before embedding — you can't embed a 500-page PDF as one vector.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    WebBaseLoader,
    DirectoryLoader,
    TextLoader
)

# Load documents from various sources
loaders = {
    "pdf":  PyPDFLoader("security_policy.pdf"),
    "web":  WebBaseLoader("https://owasp.org/www-project-top-ten/"),
    "dir":  DirectoryLoader("./labs/", glob="**/*.md", loader_cls=TextLoader),
}

all_docs = []
for source, loader in loaders.items():
    docs = loader.load()
    for doc in docs:
        doc.metadata["source"] = source
    all_docs.extend(docs)

# Chunking strategy: recursive character splitting
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,         # characters per chunk
    chunk_overlap=50,       # overlap between chunks (maintain context)
    separators=["\n\n", "\n", ".", " ", ""],  # split preference order
)

chunks = splitter.split_documents(all_docs)
print(f"Ingested {len(all_docs)} documents → {len(chunks)} chunks")
```

### Chunking Strategies by Document Type

```python
# Strategy 1: Fixed-size (simple, works for prose)
chunk_size = 500  # characters
overlap = 50

# Strategy 2: Semantic chunking (split on meaning, not size)
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

splitter = SemanticChunker(
    embeddings=OpenAIEmbeddings(),
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=95
)
# Splits where semantic similarity drops — keeps related content together

# Strategy 3: By document structure (for code)
from langchain.text_splitter import Language

python_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.PYTHON,
    chunk_size=300,
    chunk_overlap=30
)
# Splits on function/class boundaries — keeps functions intact

# Strategy 4: Parent-child chunking
# Store large "parent" chunks for context, small "child" chunks for retrieval
# Return parent chunk to LLM when child chunk is matched
```

---

## Step 2: Embedding

Convert each chunk into a vector representation:

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings

# OpenAI embeddings (API call, costs money, very good quality)
openai_embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # 1536 dimensions, cheapest
    # model="text-embedding-3-large" # 3072 dimensions, better quality
)

# Hugging Face embeddings (free, local, good quality)
hf_embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5",  # best open embedding model
    encode_kwargs={"normalize_embeddings": True}  # normalise for cosine similarity
)

# Test embedding
embedding_vector = hf_embeddings.embed_query("What is SQL injection?")
print(f"Embedding dimensions: {len(embedding_vector)}")  # 1024 for bge-large
print(f"First 5 values: {embedding_vector[:5]}")
# [-0.023, 0.048, -0.011, 0.032, -0.089]
```

---

## Step 3: Vector Store

Store chunks and their embeddings:

```python
from langchain_community.vectorstores import Chroma

# Create vector store and ingest chunks
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=hf_embeddings,
    persist_directory="./chroma_db",    # persist to disk
    collection_name="innozverse_knowledge"
)

# Later: load existing vector store
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=hf_embeddings,
    collection_name="innozverse_knowledge"
)

# Similarity search
retriever = vectorstore.as_retriever(
    search_type="mmr",           # Maximum Marginal Relevance — diverse results
    search_kwargs={
        "k": 5,                  # top 5 chunks
        "fetch_k": 20,           # candidates before MMR filtering
        "lambda_mult": 0.7       # diversity vs relevance balance (0=max diversity)
    }
)

# Test retrieval
docs = retriever.invoke("How does CSRF work?")
for i, doc in enumerate(docs):
    print(f"\n--- Chunk {i+1} ({doc.metadata.get('source','?')}) ---")
    print(doc.page_content[:200])
```

---

## Step 4: Generation — The Full RAG Chain

```python
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

llm = ChatAnthropic(model="claude-sonnet-4-6", temperature=0.1)

RAG_PROMPT = ChatPromptTemplate.from_template("""
You are an expert tutor for the InnoZverse cybersecurity course.
Answer the student's question using ONLY the provided context.

Rules:
- If the answer is not in the context, say "This topic isn't covered in the materials I have access to."
- Cite which lab or document your answer comes from
- Be concise but complete
- Include code examples if they're in the context

Context:
{context}

Question: {question}

Answer:
""")

def format_docs(docs):
    return "\n\n---\n\n".join([
        f"Source: {d.metadata.get('source', 'unknown')}\n{d.page_content}"
        for d in docs
    ])

# Complete RAG chain using LCEL
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | RAG_PROMPT
    | llm
    | StrOutputParser()
)

# Query the RAG system
answer = rag_chain.invoke("How do I prevent SQL injection in Python?")
print(answer)
```

---

## Advanced RAG Patterns

### Hybrid Search: Keyword + Semantic

```python
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

# Dense retrieval: semantic similarity (vector search)
dense_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

# Sparse retrieval: keyword matching (BM25 — like a search engine)
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 5

# Ensemble: combine both — catches exact keyword matches + semantic matches
ensemble = EnsembleRetriever(
    retrievers=[bm25_retriever, dense_retriever],
    weights=[0.4, 0.6]   # 40% keyword, 60% semantic
)

# Hybrid search handles: "What is CVE-2021-44228?" (exact match) AND
# "How do attackers exploit log libraries?" (semantic)
```

### Self-Query: AI Generates the Filter

```python
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

metadata_fields = [
    AttributeInfo(name="level",    description="Difficulty: foundations/practitioner/advanced", type="string"),
    AttributeInfo(name="topic",    description="Topic: SQLi/XSS/privesc/networking/etc.", type="string"),
    AttributeInfo(name="lab",      description="Lab number (1-20)", type="integer"),
]

self_query_retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_contents="InnoZverse cybersecurity course labs",
    metadata_field_info=metadata_fields,
)

# LLM parses the question and generates a metadata filter automatically
docs = self_query_retriever.invoke("Show me advanced labs about SQL injection")
# Automatically generates: filter={"level": "advanced", "topic": "SQLi"}
```

---

## Evaluating RAG Quality

```python
# Key RAG metrics

def evaluate_rag(question, retrieved_docs, generated_answer, ground_truth):
    """Evaluate RAG pipeline quality"""

    # 1. Retrieval Recall: did we retrieve the relevant document?
    relevant_content_found = any(
        ground_truth_snippet in doc.page_content
        for doc in retrieved_docs
        for ground_truth_snippet in ground_truth["key_facts"]
    )

    # 2. Faithfulness: does the answer only use retrieved context?
    # (use LLM to check — "does this answer use only information from these docs?")
    faithfulness_prompt = f"""
    Context: {[d.page_content for d in retrieved_docs]}
    Answer: {generated_answer}
    
    Is every claim in the answer supported by the context? 
    Reply with only: YES or NO
    """
    faithful = llm.invoke(faithfulness_prompt).content.strip() == "YES"

    # 3. Answer Relevance: does the answer address the question?
    relevance_prompt = f"""
    Question: {question}
    Answer: {generated_answer}
    
    Does this answer address the question? Rate 1-5.
    """
    relevance = int(llm.invoke(relevance_prompt).content.strip())

    return {
        "retrieval_recall": relevant_content_found,
        "faithfulness": faithful,
        "answer_relevance": relevance / 5
    }

# RAGAS: automated RAG evaluation framework
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

results = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_recall]
)
print(results)
# {'faithfulness': 0.87, 'answer_relevancy': 0.91, 'context_recall': 0.79}
```

---

## Common RAG Failure Modes

| Problem | Symptom | Fix |
|---------|---------|-----|
| Chunks too large | Retrieved context irrelevant | Reduce chunk_size to 200-400 chars |
| Chunks too small | Missing context, incomplete answers | Increase chunk_size + overlap |
| Wrong top-k | Missing relevant docs | Increase k; use MMR for diversity |
| No overlap | Answers cut off at chunk boundaries | Increase chunk_overlap |
| Keyword mismatch | Can't find exact terms | Add BM25 hybrid retrieval |
| Model ignores context | Still hallucinating | Stronger prompt: "ONLY use context" |

---

## Further Reading

- [RAG Paper: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401)
- [LangChain RAG Tutorials](https://python.langchain.com/docs/tutorials/rag/)
- [RAGAS: RAG Evaluation Framework](https://docs.ragas.io/)
- [Advanced RAG Techniques (Pinecone)](https://www.pinecone.io/learn/advanced-rag/)
