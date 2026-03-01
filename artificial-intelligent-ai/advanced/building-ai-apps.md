# Building AI Applications

## RAG — Retrieval Augmented Generation

RAG combines document retrieval with LLM generation for accurate, up-to-date answers.

```python
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# 1. Load documents
loader = DirectoryLoader('./docs/', glob="**/*.md")
documents = loader.load()

# 2. Split into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

# 3. Create vector store
embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")

# 4. Create QA chain
llm = ChatOpenAI(model="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5})
)

# 5. Query
answer = qa_chain.run("How do I configure SSH key authentication?")
print(answer)
```

## Building a Simple AI API (FastAPI)

```python
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI()
client = OpenAI()

class QuestionRequest(BaseModel):
    question: str
    context: str = ""

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    messages = [
        {"role": "system", "content": "You are an expert tech educator."},
    ]
    if request.context:
        messages.append({"role": "user", "content": f"Context: {request.context}"})
    messages.append({"role": "user", "content": request.question})

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    return {"answer": response.choices[0].message.content}

# Run: uvicorn main:app --reload
```
