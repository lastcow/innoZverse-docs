# AI System Design

## Large-Scale AI Architecture

```
[Data Sources]                    [Training]              [Serving]
Raw data ─────→ [Data Lake] ─→ [Feature Store] ─→ [Model Training]
                     │                                    │
              [Data Pipeline]                    [Model Registry]
              (Spark/Airflow)                           │
                                              [Inference Service]
                                              /         │         \
                                        [Batch]    [Real-time]  [Stream]
                                           │            │           │
                                      [Reports]    [API]      [Kafka]
```

## Retrieval Augmented Generation (RAG) at Scale

```python
from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
import pinecone

# Initialize vector store
pinecone.init(api_key="...", environment="us-east-1-aws")
embeddings = OpenAIEmbeddings()
vectorstore = Pinecone.from_existing_index("innozverse-docs", embeddings)

# Build retrieval chain with memory
llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(
        search_type="mmr",          # Maximum Marginal Relevance
        search_kwargs={"k": 8, "fetch_k": 20}
    ),
    return_source_documents=True,
    verbose=False
)

# Usage
result = chain({"question": "How do I set up SSH keys?", "chat_history": []})
print(result['answer'])
```

## AI Evaluation Framework

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall

# Evaluate RAG pipeline quality
scores = evaluate(
    dataset=eval_dataset,
    metrics=[faithfulness, answer_relevancy, context_recall]
)

print(scores)
# faithfulness: 0.95    (Does answer match retrieved context?)
# answer_relevancy: 0.88 (Is answer relevant to question?)
# context_recall: 0.91  (Did we retrieve the right context?)
```

## LLM Fine-tuning Pipeline

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from peft import LoraConfig

# LoRA fine-tuning (efficient — only train 0.1% of params)
lora_config = LoraConfig(
    r=16,                   # Rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

training_args = TrainingArguments(
    output_dir="./fine-tuned-model",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch",
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    peft_config=lora_config,
    dataset_text_field="text",
    max_seq_length=2048,
)
trainer.train()
```
