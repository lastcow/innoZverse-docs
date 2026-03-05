# Lab 08: Multi-Agent System Design

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Multi-agent AI systems enable complex task automation by coordinating specialized AI agents. This lab covers ReAct patterns, agent orchestration topologies, memory architectures, inter-agent communication, evaluation frameworks, and production guardrails.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Multi-Agent Orchestration System                │
├─────────────────────────────────────────────────────────────┤
│  User Request → Orchestrator Agent                          │
│                      ↓                                      │
│         ┌────────────┴────────────┐                        │
│     Planner Agent          Tool Router                      │
│         ↓                       ↓                          │
│  Task Decomposition    ┌─────────┴─────────┐               │
│         ↓              │                   │               │
│  [Researcher] [Analyst] [Code Agent] [API Agent]           │
│         ↓         ↓         ↓           ↓                  │
│     Memory Layer (Working/Episodic/Semantic)                │
│         ↓                                                   │
│  Synthesizer Agent → Final Response                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: ReAct Pattern (Reason + Act)

ReAct is the fundamental pattern for tool-using agents.

**ReAct Loop:**
```
Observation: [user query or previous action result]
    ↓
Thought: "I need to search for X to answer this"
    ↓
Action: search(query="X")
    ↓
Observation: [search results]
    ↓
Thought: "I found X. Now I need to calculate Y"
    ↓
Action: calculator(expression="Y")
    ↓
Observation: [calculation result]
    ↓
Thought: "I have all the information to answer"
    ↓
Final Answer: [complete response]
```

**ReAct Prompt Structure:**
```
System: You are an AI assistant. Use tools when needed.
Available tools: search, calculator, code_executor, database_query

You must respond with:
Thought: [reasoning]
Action: tool_name(params)
OR
Final Answer: [answer]
```

> 💡 The key innovation of ReAct is interleaving reasoning and acting. This allows the agent to adapt its plan based on tool results, unlike CoT (chain-of-thought) which reasons without acting.

---

## Step 2: Agent Orchestration Topologies

**Sequential (Pipeline):**
```
Agent A → Agent B → Agent C → Result
Each agent's output becomes next agent's input
Best for: step-by-step workflows, document processing pipelines
```

**Parallel:**
```
                ┌→ Agent A ─┐
Orchestrator ──→├→ Agent B ─┼→ Aggregator → Result
                └→ Agent C ─┘
All agents run simultaneously
Best for: independent subtasks, research that can be parallelized
```

**Hierarchical:**
```
Manager Agent
├── SubManager A
│   ├── Worker Agent 1
│   └── Worker Agent 2
└── SubManager B
    ├── Worker Agent 3
    └── Worker Agent 4
Best for: complex tasks requiring coordination across domains
```

**Comparison:**

| Topology | Latency | Scalability | Complexity | Use Case |
|----------|---------|------------|-----------|---------|
| Sequential | High | Low | Low | Step-by-step workflows |
| Parallel | Low | High | Medium | Independent research tasks |
| Hierarchical | Medium | High | High | Complex enterprise workflows |

---

## Step 3: Memory Types

Agents need different types of memory for different purposes.

| Memory Type | Storage | Persistence | Capacity | Use Case |
|-------------|---------|------------|---------|---------|
| **Working** | LLM context window | Session only | 4K-128K tokens | Current task context |
| **Episodic** | Vector database | Persistent | Unlimited | Past interactions, conversation history |
| **Semantic** | Knowledge base/KG | Persistent | Unlimited | Domain knowledge, facts |
| **Procedural** | Fine-tuned model | In weights | Fixed | Skills, how-to knowledge |

**Memory Architecture for Production Agent:**
```
Query → Check semantic memory (cached facts)
     → Check episodic memory (past interactions)
     → Load working memory (current context)
     
After response:
     → Summarize → store in episodic memory (vector DB)
     → Extract facts → update semantic memory (KG)
     → Update working memory (next turn)
```

**Memory Compression:**
```
Working memory fills up → Summarize oldest context → Store in episodic
Episodic memory grows large → Cluster + summarize → Create semantic memories
```

---

## Step 4: Tool Use and Function Calling

**Tool Design Principles:**
```
1. Atomic tools: one function per tool (search, calculate, query, write)
2. Clear interfaces: precise parameter types and descriptions
3. Error handling: tools return structured errors, not exceptions
4. Idempotency: safe to call multiple times
5. Timeout limits: prevent hanging agents
```

**Tool Taxonomy:**

| Category | Examples | Risk Level |
|----------|---------|-----------|
| Read-only | search, database_read, file_read | Low |
| Write | file_write, database_write, email_send | High |
| Execute | code_run, shell_command, API_call | Critical |
| External | web_browse, API_call | Medium |

**Human-in-the-loop for High-Risk Tools:**
```
Agent wants to: send_email(to="all_customers@company.com", ...)
                    ↓
Human approval required → notify human
                    ↓
Human approves → action executes
Human rejects → agent tries alternative
```

---

## Step 5: Inter-Agent Communication

**Message Bus Pattern:**
```
Agent A → publish(topic="analysis_complete", data=results)
Agent B → subscribe(topic="analysis_complete") → receive results → continue
```

**Direct Communication:**
```
Orchestrator.delegate(task="research", to=researcher_agent)
researcher_agent.report(result=findings, to=orchestrator)
```

**Blackboard Pattern:**
```
Shared workspace (database/memory) that all agents read/write
Agent A writes: {"entity_extraction": ["Person: John", "Org: Acme"]}
Agent B reads: entity_extraction results → builds relationship graph
Agent C reads: relationship graph → generates report
```

**Agent Communication Protocols:**
- **LangChain**: Python-native, broad tool ecosystem
- **AutoGen (Microsoft)**: Multi-agent conversation framework
- **CrewAI**: Role-based agents with task management
- **OpenAI Assistants API**: Managed threads and tool calls

---

## Step 6: Agent Evaluation Framework

**Evaluation Dimensions:**

| Dimension | Metric | Tool |
|-----------|--------|------|
| Task completion | % tasks completed correctly | Custom benchmark |
| Tool accuracy | Correct tool selection rate | Logging |
| Reasoning quality | Step-by-step correctness | LLM judge |
| Efficiency | Avg steps to completion | Tracing |
| Safety | Harmful action rate | Red-team testing |
| Latency | P95 time to complete task | APM |

**Agent Trajectory Evaluation:**
```
Trace: [thought, action, observation, thought, action, ...]
         ↓
LLM judge evaluates:
  - Was reasoning correct at each step?
  - Were appropriate tools chosen?
  - Was the final answer grounded in evidence?
  - Were any unnecessary steps taken?
```

**Benchmark Datasets:**
- HotpotQA: multi-hop reasoning
- WebArena: web navigation tasks
- MINT: multi-turn tool use
- SWE-Bench: software engineering tasks

---

## Step 7: Guardrails and Sandboxing

**Input Guardrails:**
```
User input → Content filter (harmful content check)
          → Injection detector (prompt injection)
          → Scope validator (is this in-domain?)
          → Rate limiter (per user/org)
```

**Output Guardrails:**
```
Agent output → PII detector (redact personal data)
            → Hallucination checker (citation required)
            → Policy compliance (legal review topics)
            → Format validator (structured output)
```

**Code Execution Sandboxing:**
```
Agent writes code → 
  Sandbox: Docker container (no network, limited CPU/RAM)
  Resource limits: 10s timeout, 256MB RAM, no disk write
  Security scan: detect malicious patterns before execution
  Output capture: stdout/stderr only, no side effects
```

**Agent Guardrail Architecture (Nemo Guardrails / Llama Guard):**
```
User → Input rails → LLM → Output rails → Response
         ↓                       ↓
    Block harmful          Verify grounded
    input topics           in provided context
```

---

## Step 8: Capstone — Multi-Agent Simulation

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
import time

class Agent:
    def __init__(self, name, role, tools):
        self.name = name
        self.role = role
        self.tools = tools
        self.memory = []
        self.messages_sent = 0
    
    def think(self, observation):
        thought = f'Thought: I need to {self.role} for: {observation[:30]}'
        action = self.tools[0] if self.tools else 'respond'
        return thought, action
    
    def act(self, action, context):
        result = f'[{self.name}] executed {action} on context'
        self.memory.append({'action': action, 'result': result})
        self.messages_sent += 1
        return result

class Orchestrator:
    def __init__(self, agents):
        self.agents = agents
        self.task_queue = []
    
    def sequential_run(self, task):
        print(f'Orchestrator: Sequential execution for task: \"{task}\"')
        context = task
        for agent in self.agents:
            thought, action = agent.think(context)
            result = agent.act(action, context)
            context = result
            print(f'  {agent.name} ({agent.role}): {action} -> done')
        return context
    
    def parallel_run(self, subtasks):
        print(f'Orchestrator: Parallel execution for {len(subtasks)} subtasks')
        results = []
        for agent, task in zip(self.agents, subtasks):
            thought, action = agent.think(task)
            result = agent.act(action, task)
            results.append(result)
            print(f'  {agent.name}: processed in parallel')
        return results

agents = [
    Agent('Planner', 'decompose tasks into subtasks', ['decompose', 'plan']),
    Agent('Researcher', 'search and retrieve information', ['search', 'retrieve']),
    Agent('Analyst', 'analyze and synthesize information', ['analyze', 'summarize']),
    Agent('Writer', 'generate final response', ['generate', 'format']),
]
orchestrator = Orchestrator(agents)

print('=== Multi-Agent System Simulation ===')
print()
result = orchestrator.sequential_run('Analyze enterprise AI security threats')
print()
subtasks = ['research CVEs', 'analyze logs', 'check compliance', 'generate report']
results = orchestrator.parallel_run(subtasks)
print()
print('=== Agent Memory Types ===')
memory_types = {
    'working': 'Current task context (in-context window)',
    'episodic': 'Past interaction history (vector DB)',
    'semantic': 'Domain knowledge base (knowledge graph)',
    'procedural': 'Tool usage patterns (fine-tuned skills)',
}
for mtype, desc in memory_types.items():
    print(f'  {mtype:12s}: {desc}')
print()
print(f'Total agent messages: {sum(a.messages_sent for a in agents)}')
"
```

📸 **Verified Output:**
```
=== Multi-Agent System Simulation ===

Orchestrator: Sequential execution for task: "Analyze enterprise AI security threats"
  Planner (decompose tasks into subtasks): decompose -> done
  Researcher (search and retrieve information): search -> done
  Analyst (analyze and synthesize information): analyze -> done
  Writer (generate final response): generate -> done

Orchestrator: Parallel execution for 4 subtasks
  Planner: processed in parallel
  Researcher: processed in parallel
  Analyst: processed in parallel
  Writer: processed in parallel

=== Agent Memory Types ===
  working     : Current task context (in-context window)
  episodic    : Past interaction history (vector DB)
  semantic    : Domain knowledge base (knowledge graph)
  procedural  : Tool usage patterns (fine-tuned skills)

Total agent messages: 8
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| ReAct Pattern | Interleave reasoning + tool actions; adapt plan to results |
| Orchestration | Sequential (pipeline), Parallel (speed), Hierarchical (complex) |
| Memory Types | Working (context), Episodic (history), Semantic (knowledge), Procedural (skills) |
| Tool Design | Atomic, clear interface, error handling, human approval for high-risk |
| Inter-Agent Comms | Message bus, direct delegation, blackboard pattern |
| Evaluation | Task completion rate + reasoning quality + safety + efficiency |
| Guardrails | Input validation + output filtering + code sandboxing |

**Next Lab:** [Lab 09: AI Security Red Team →](lab-09-ai-security-red-team.md)
