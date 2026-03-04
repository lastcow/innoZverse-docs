# Lab 09: AI Agents — From Chatbots to Autonomous Systems

## Objective

Understand how AI agents work and how they differ from simple chatbots. By the end you will be able to:

- Define what makes a system an "agent" vs a chatbot
- Explain the ReAct (Reason + Act) loop
- Describe the major agent frameworks and architectures
- Understand multi-agent systems and their real-world applications

---

## Chatbot vs Agent: The Key Difference

A **chatbot** responds to one message at a time. An **agent** pursues a goal over multiple steps, using tools, making decisions, and adapting to results.

```
CHATBOT:
  User: "What's the weather in London?"
  Bot:  "I don't have real-time data."  ← end of interaction

AGENT:
  User: "What's the weather in London?"
  Agent thinks: "I need real-time weather data"
  Agent acts:   [calls weather API]
  Agent sees:   {"temp": 12°C, "condition": "rainy"}
  Agent replies: "It's 12°C and raining in London. You may want an umbrella."
  ← goal achieved through tool use
```

---

## The Agent Loop: Observe → Think → Act → Observe

```
                    ┌─────────────┐
                    │    GOAL     │
                    └──────┬──────┘
                           │
              ┌────────────▼────────────────┐
              │         OBSERVE             │
              │  (environment, tool results, │
              │   memory, user message)     │
              └────────────┬────────────────┘
                           │
              ┌────────────▼────────────────┐
              │          THINK              │
              │  (LLM: plan next action,    │
              │   select tool, reason)      │
              └────────────┬────────────────┘
                           │
              ┌────────────▼────────────────┐
              │           ACT               │
              │  (call tool, write file,    │
              │   send message, search web) │
              └────────────┬────────────────┘
                           │
              ┌────────────▼────────────────┐
              │     Check: goal achieved?   │
              │  NO → loop back to OBSERVE  │
              │  YES → return result        │
              └─────────────────────────────┘
```

---

## ReAct: Reason + Act

The foundational agent pattern (Yao et al., 2022). The LLM interleaves **Thought**, **Action**, and **Observation** steps:

```
User: "Find the population of the 3 largest cities in Japan and calculate their total."

Thought: I need to find Japan's 3 largest cities.
Action: search("largest cities in Japan by population")
Observation: Tokyo (13.96M), Yokohama (3.77M), Osaka (2.75M)

Thought: Now I have the three cities and their populations.
Action: calculator("13960000 + 3770000 + 2750000")
Observation: 20480000

Thought: I have all the information needed to answer.
Final Answer: The 3 largest cities in Japan are Tokyo (13.96M), 
              Yokohama (3.77M), and Osaka (2.75M). 
              Their total population is 20,480,000.
```

```python
# Simplified ReAct implementation
def react_agent(goal: str, tools: dict, max_steps: int = 10) -> str:
    history = [{"role": "system", "content": REACT_SYSTEM_PROMPT}]
    history.append({"role": "user", "content": goal})

    for step in range(max_steps):
        # LLM thinks and decides what to do
        response = llm(history)
        history.append({"role": "assistant", "content": response})

        # Parse the action
        if "Final Answer:" in response:
            return response.split("Final Answer:")[-1].strip()

        if "Action:" in response:
            action_line = [l for l in response.split('\n') if 'Action:' in l][0]
            tool_name, tool_input = parse_action(action_line)

            # Execute the tool
            if tool_name in tools:
                observation = tools[tool_name](tool_input)
                history.append({"role": "user", "content": f"Observation: {observation}"})

    return "Max steps reached without conclusion"
```

---

## Tools: What Agents Can Do

Tools extend the LLM beyond text — into the real world:

```python
# Example tool definitions (OpenAI function calling format)
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for current information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute Python code and return output",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"}
                },
                "required": ["code"]
            }
        }
    }
]
```

**Common agent tools:**

| Category | Tools |
|----------|-------|
| Information | Web search, Wikipedia, calculator, calendar |
| Code | Python REPL, bash shell, SQL executor |
| Files | Read/write files, create documents, parse PDFs |
| APIs | Weather, maps, email, calendar, Slack, GitHub |
| Browsers | Selenium/Playwright for web automation |
| Databases | Query and update databases |
| Communication | Send email, SMS, Discord messages |

---

## Memory Systems

Agents need memory to maintain context across sessions:

```
┌─────────────────────────────────────────────────────┐
│                  AGENT MEMORY                       │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │
│  │  In-Context  │  │  External    │  │ Semantic │  │
│  │  (working    │  │  (files,     │  │ (vector  │  │
│  │   memory)    │  │   database)  │  │  store)  │  │
│  │              │  │              │  │          │  │
│  │ Last 10 msgs │  │ All history  │  │ Fuzzy    │  │
│  │ Current task │  │ User prefs   │  │ recall   │  │
│  │ Tool results │  │ Learned facts│  │ by topic │  │
│  └──────────────┘  └──────────────┘  └──────────┘  │
└─────────────────────────────────────────────────────┘
```

```python
# Semantic memory with vector store
from sentence_transformers import SentenceTransformer
import numpy as np

class AgentMemory:
    def __init__(self):
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.memories = []
        self.embeddings = []

    def store(self, memory: str):
        """Store a memory with its embedding"""
        embedding = self.encoder.encode(memory)
        self.memories.append(memory)
        self.embeddings.append(embedding)

    def recall(self, query: str, top_k: int = 3) -> list[str]:
        """Recall most relevant memories for a query"""
        query_embedding = self.encoder.encode(query)
        similarities = [
            np.dot(query_embedding, emb) / 
            (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            for emb in self.embeddings
        ]
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self.memories[i] for i in top_indices]
```

---

## Major Agent Frameworks

### LangChain

The most widely used framework. Provides chains, agents, tools, memory, and RAG out of the box.

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o", temperature=0)
tools = [DuckDuckGoSearchRun()]
agent = create_react_agent(llm, tools, prompt=REACT_PROMPT)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "What happened in AI news this week?"})
```

### LangGraph

Graph-based agent orchestration — define agents as nodes, transitions as edges. Better for complex multi-step workflows.

```python
from langgraph.graph import StateGraph, END

def should_continue(state):
    return "continue" if not state["done"] else END

graph = StateGraph(AgentState)
graph.add_node("research", research_node)
graph.add_node("write",    write_node)
graph.add_node("review",   review_node)
graph.add_conditional_edges("review", should_continue)
graph.set_entry_point("research")
```

### AutoGen (Microsoft)

Multi-agent conversations — multiple specialised agents collaborate:

```python
# AutoGen: code review with specialised agents
from autogen import AssistantAgent, UserProxyAgent

coder  = AssistantAgent("coder",  llm_config=llm_config)
tester = AssistantAgent("tester", llm_config=llm_config,
    system_message="You write comprehensive test cases for code you receive.")
reviewer = AssistantAgent("reviewer", llm_config=llm_config,
    system_message="You review code for security vulnerabilities.")

# Agents collaborate: coder writes → tester writes tests → reviewer checks security
```

---

## Multi-Agent Systems

Complex tasks benefit from **specialisation**:

```
User Goal: "Write and publish a blog post about quantum computing"
           │
           ▼
    ┌─────────────┐
    │  ORCHESTRATOR│  ← breaks task into subtasks, assigns agents
    └──────┬──────┘
           │
    ┌──────┴──────────────────────────────┐
    │              │              │        │
    ▼              ▼              ▼        ▼
┌────────┐   ┌─────────┐   ┌─────────┐  ┌──────┐
│Research│   │ Writer  │   │ Editor  │  │Publish│
│Agent   │   │ Agent   │   │ Agent   │  │Agent │
│        │   │         │   │         │  │      │
│web     │   │drafts   │   │reviews  │  │posts │
│search  │   │content  │   │grammar  │  │CMS   │
└────────┘   └─────────┘   └─────────┘  └──────┘
```

**Real-world multi-agent deployments:**
- **Devin (Cognition AI)** — autonomous software engineer; writes, tests, debugs, deploys code
- **OpenAI Operator** — controls a web browser to complete real-world tasks
- **GitHub Copilot Workspace** — multi-agent code review and refactoring
- **OpenClaw** — personal AI assistant with memory, scheduling, messaging, browsing tools

---

## Agent Safety Considerations

Autonomous agents introduce new risks:

| Risk | Example | Mitigation |
|------|---------|-----------|
| Prompt injection | Malicious webpage tricks agent to exfiltrate data | Separate privileged context from web content |
| Irreversible actions | Agent deletes files, sends emails, charges cards | Human-in-the-loop for destructive actions |
| Scope creep | Agent installs software "to be more helpful" | Explicit capability allowlisting |
| Infinite loops | Agent keeps retrying failed actions | Max step limits, circuit breakers |
| Hallucinated tool calls | Agent calls a tool with fabricated parameters | Input validation before tool execution |

---

## The Future: Agentic AI

The shift from **chatbots** to **agents** is the major transition happening in AI right now (2024–2026):

- **Claude 3.5 Sonnet computer use** — controls a real computer via screenshots
- **OpenAI Operator** — books restaurants, fills forms, manages subscriptions
- **Google Project Mariner** — browser agent integrated into Chrome
- **Apple Intelligence** — on-device agent with app integration

The endgame: AI systems that can take on tasks measured in hours and days, not seconds — with minimal human supervision.

---

## Further Reading

- [ReAct: Synergizing Reasoning and Acting (Yao et al., 2022)](https://arxiv.org/abs/2210.03629)
- [LangChain Documentation](https://python.langchain.com/docs/)
- [AutoGen Framework (Microsoft)](https://microsoft.github.io/autogen/)
- [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
