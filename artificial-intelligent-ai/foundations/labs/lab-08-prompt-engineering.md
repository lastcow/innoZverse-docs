# Lab 08: Prompt Engineering — Getting the Most Out of LLMs

## Objective

Master the art and science of writing prompts that reliably produce high-quality LLM outputs. By the end you will be able to:

- Apply the core principles of effective prompting
- Use zero-shot, few-shot, and chain-of-thought techniques
- Structure system prompts for consistent AI behaviour
- Avoid common prompting pitfalls

---

## Why Prompt Engineering Matters

LLMs are not search engines. The same question asked differently can produce dramatically different results:

```
❌ Bad:    "Write code"
✅ Good:   "Write a Python function that takes a list of integers and returns 
            the top 3 most frequent elements. Include type hints, a docstring, 
            and handle edge cases (empty list, ties). Use only standard library."
```

The model has the capability — your prompt determines whether it accesses the right capability.

---

## The Anatomy of a Good Prompt

```
┌─────────────────────────────────────────────────────┐
│  SYSTEM PROMPT (set the stage)                      │
│  Role + context + constraints + output format       │
├─────────────────────────────────────────────────────┤
│  USER MESSAGE (the actual task)                     │
│  Clear goal + input data + examples + constraints   │
└─────────────────────────────────────────────────────┘
```

---

## Core Techniques

### 1. Zero-Shot Prompting

No examples — just a clear instruction. Works well when the task is common in training data.

```python
# Zero-shot: sentiment analysis
prompt = """
Classify the sentiment of the following product review as 
Positive, Negative, or Neutral. Reply with only the classification.

Review: "Battery life is disappointing but the screen is gorgeous."
"""
# → "Negative"  (or "Mixed" if the model is more nuanced)
```

### 2. Few-Shot Prompting

Provide 2–5 examples to demonstrate the desired format and reasoning style. Dramatically improves consistency.

```python
prompt = """
Classify product reviews as Positive, Negative, or Neutral.

Review: "Absolutely love it, works perfectly!" → Positive
Review: "Stopped working after 2 days. Terrible." → Negative
Review: "It's okay. Nothing special." → Neutral
Review: "The colour is wrong but the quality is excellent." → ???
"""
# Model learns from the pattern → more consistent output
```

### 3. Chain-of-Thought (CoT) Prompting

For reasoning tasks, instruct the model to think step by step. Significantly improves accuracy on maths, logic, and multi-step problems.

```python
# Without CoT — unreliable on complex reasoning
prompt_bad = "If a bat and ball cost £1.10, and the bat costs £1 more than the ball, how much does the ball cost?"
# Common wrong answer: £0.10

# With CoT — explicit reasoning
prompt_good = """
If a bat and ball cost £1.10, and the bat costs £1 more than the ball, 
how much does the ball cost?

Think step by step:
"""
# Model output:
# Let the ball cost x.
# Bat costs x + 1.00
# x + (x + 1.00) = 1.10
# 2x = 0.10
# x = £0.05
# Answer: The ball costs 5p.
```

**Zero-shot CoT trick:** Simply add `"Let's think step by step"` to almost any reasoning question.

### 4. Role Prompting

Give the model a specific identity and expertise level.

```python
system_prompt = """
You are a senior Python developer with 15 years of experience. 
You write clean, Pythonic, well-documented code.
When reviewing code, you point out:
1. Correctness issues (bugs)
2. Performance improvements  
3. Pythonic style suggestions
4. Security concerns
Format feedback as a numbered list with code examples.
"""

user_message = """
Review this code:
def get_user(id):
    query = "SELECT * FROM users WHERE id = " + id
    return db.execute(query)
"""
# Model will correctly identify: SQL injection vulnerability,
# missing parameterised query, suggest f-string or ORM instead
```

### 5. Structured Output

Force JSON or specific formats for programmatic use.

```python
prompt = """
Extract the following information from this customer complaint and 
return as valid JSON only (no other text):

{
  "issue_type": "one of: billing, technical, shipping, other",
  "severity": "one of: low, medium, high, critical",
  "product": "product name or null",
  "requested_action": "what the customer wants"
}

Complaint: "I've been charged twice for my Surface Pro subscription 
this month! This is unacceptable. I want a full refund immediately."
"""

# Expected output:
# {
#   "issue_type": "billing",
#   "severity": "high",
#   "product": "Surface Pro",
#   "requested_action": "full refund"
# }
```

With modern APIs, use **structured outputs** (JSON mode) to guarantee valid JSON:

```python
import openai

client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},  # guarantees valid JSON
)
import json
result = json.loads(response.choices[0].message.content)
```

### 6. Retrieval-Augmented Prompting

Ground the model in specific facts by including relevant documents in the prompt:

```python
retrieved_docs = search_knowledge_base(user_query)

prompt = f"""
Answer the user's question using ONLY the information in the context below.
If the answer is not in the context, say "I don't have that information."

CONTEXT:
{retrieved_docs}

QUESTION: {user_query}

ANSWER:
"""
# This prevents hallucination by constraining the model to provided facts
```

---

## System Prompt Design

The **system prompt** sets persistent behaviour for the entire conversation. Design it carefully:

```python
system_prompt = """
You are InnoZverse Assistant, a technical education AI for the InnoZverse 
learning platform.

## Role
Help students understand cybersecurity, programming, Linux, networking, 
databases, and AI concepts.

## Behaviour
- Explain concepts clearly with real-world analogies
- Include code examples when relevant
- Point to further reading (mention specific books/resources)
- If a question is outside your scope, redirect politely
- NEVER provide instructions for illegal activities

## Format
- Use markdown formatting
- Structure long answers with headers
- Code blocks for all code snippets
- Bullet points for lists of 3+ items

## Tone
Professional but approachable. Assume technical competence but 
explain clearly. Avoid jargon without explanation.
"""
```

---

## Prompt Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Vague instruction | "Make it better" | "Improve the clarity and reduce the word count by 30%" |
| No format specified | Random output structure | "Return as JSON / bullet list / numbered steps" |
| Negative-only constraints | "Don't use jargon" | Add positive: "Use plain English a 16-year-old could understand" |
| No context | "Fix this" | Paste the actual code/text with error messages |
| Overloaded prompts | 10 tasks in one message | Break into separate calls |
| Asking to lie | "Pretend you know X" | Provide X in the context instead |

---

## Advanced: Prompt Chaining

Break complex tasks into a pipeline of smaller prompts:

```python
def analyse_contract(contract_text: str) -> dict:
    """Multi-step contract analysis pipeline"""
    
    # Step 1: Extract key clauses
    clauses = llm(f"""
        Extract all key clauses from this contract as a JSON array.
        Include: clause_type, clause_text, page_reference
        CONTRACT: {contract_text}
    """)
    
    # Step 2: Identify risks in each clause
    risks = llm(f"""
        For each clause below, identify legal risks rated 1-5.
        Return as JSON with risk_level and explanation.
        CLAUSES: {clauses}
    """)
    
    # Step 3: Generate executive summary
    summary = llm(f"""
        Write a 200-word executive summary of this contract's risks.
        Focus on the top 3 issues. Audience: non-lawyer executives.
        RISK ANALYSIS: {risks}
    """)
    
    return {"clauses": clauses, "risks": risks, "summary": summary}
```

---

## Prompt Engineering for Code

```python
# Best practices for code generation prompts:

code_prompt = """
Write a Python function with these specifications:

PURPOSE: Parse CSV files with inconsistent date formats and normalise to ISO 8601

INPUT: 
  - file_path: str (path to CSV)
  - date_columns: list[str] (column names containing dates)

OUTPUT: pandas DataFrame with dates standardised to YYYY-MM-DD

REQUIREMENTS:
  - Handle formats: DD/MM/YYYY, MM-DD-YYYY, YYYY.MM.DD, "Jan 5 2024"
  - Invalid dates → NaT (not error)
  - Preserve all other columns unchanged
  - Include type hints
  - Include docstring with example

CONSTRAINTS:
  - Use only: pandas, dateutil
  - No external API calls
  - Handle files up to 1GB (chunk processing)
"""
```

---

## Summary

| Technique | When to Use | Impact |
|-----------|------------|--------|
| Zero-shot | Common, simple tasks | Baseline |
| Few-shot | Custom formats, edge cases | High |
| Chain-of-Thought | Maths, logic, multi-step | Very High |
| Role prompting | Specialised expertise | Medium–High |
| Structured output | Programmatic use | Critical |
| Retrieval-augmented | Factual accuracy | Very High |
| Prompt chaining | Complex multi-step tasks | Very High |

---

## Further Reading

- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Chain-of-Thought Prompting (Wei et al., 2022)](https://arxiv.org/abs/2201.11903)
- [Anthropic's Prompt Library](https://docs.anthropic.com/en/prompt-library/library)
