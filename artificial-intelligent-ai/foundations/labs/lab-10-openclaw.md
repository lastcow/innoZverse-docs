# Lab 10: OpenClaw — Building Your Own AI Personal Assistant

## Objective

Understand what OpenClaw is, how it works, and how to extend it. By the end you will be able to:

- Explain OpenClaw's architecture and how it differs from simple chatbots
- Understand how skills, memory, and tool integrations are structured
- Set up and configure your own OpenClaw instance
- Create a basic custom skill

---

## What is OpenClaw?

**OpenClaw** is an open-source AI personal assistant platform that turns a powerful LLM (Claude) into a persistent, multi-channel, tool-using personal agent. It runs on your own hardware or server, connects to your messaging apps, and maintains memory across sessions.

The key differences from using ChatGPT directly:

| Feature | ChatGPT | OpenClaw |
|---------|---------|----------|
| Memory | Session only | Persistent across sessions |
| Channels | Web only | Discord, WhatsApp, Telegram, Signal, iMessage |
| Tools | Limited | Extensible via Skills |
| Your data | OpenAI's servers | Your server |
| Personality | Generic | Configurable (SOUL.md) |
| Integrations | Via plugins | Via Skills (local scripts) |
| Multi-agent | No | Yes (subagents, ACP) |

---

## OpenClaw Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         OPENCLAW                                │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  Channels    │  │   Gateway    │  │   Claude API         │ │
│  │              │  │   Daemon     │  │   (Anthropic)        │ │
│  │  Discord     │──│              │──│                      │ │
│  │  Telegram    │  │  • Routing   │  │  Tool calls ←────────│ │
│  │  WhatsApp    │  │  • Sessions  │  │  ↓                   │ │
│  │  Signal      │  │  • Cron      │  │  Tool execution      │ │
│  └──────────────┘  └──────┬───────┘  └──────────────────────┘ │
│                           │                                     │
│  ┌──────────────┐  ┌──────▼───────┐  ┌──────────────────────┐ │
│  │   Memory     │  │   Skills     │  │   Nodes (devices)    │ │
│  │              │  │              │  │                      │ │
│  │  MEMORY.md   │  │  discord/    │  │  Paired phones       │ │
│  │  daily logs  │  │  weather/    │  │  Cameras             │ │
│  │  SOUL.md     │  │  apify/      │  │  Screen recording    │ │
│  │  USER.md     │  │  tmux/       │  │  Location            │ │
│  └──────────────┘  └──────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
# Install OpenClaw via npm
npm install -g openclaw

# Initialise a new workspace
openclaw init

# Configure your API keys
openclaw config set anthropic.apiKey "sk-ant-..."
openclaw config set discord.token "your-discord-bot-token"

# Start the gateway daemon
openclaw gateway start

# Check status
openclaw status
```

---

## The Workspace: Your Agent's Home

OpenClaw uses a file-based workspace. The key files:

```bash
~/.openclaw/workspace/
├── SOUL.md        ← AI personality and behaviour
├── USER.md        ← Who you are (name, preferences, context)
├── AGENTS.md      ← How the agent should behave each session
├── MEMORY.md      ← Long-term curated memory
├── TOOLS.md       ← Device/environment notes
├── HEARTBEAT.md   ← Periodic background tasks
├── memory/
│   ├── 2026-03-04.md    ← Daily session notes
│   └── heartbeat-state.json
└── skills/
    ├── weather/
    ├── discord/
    └── your-custom-skill/
```

### SOUL.md — The Personality File

```markdown
# SOUL.md - Who You Are

You are InnoZverse Assistant — the educational AI for InnoZverse Labs.

## Core Traits
- Expert in cybersecurity, programming, Linux, AI, networking
- Teaching style: Socratic — guide students to answers, don't just give them
- Tone: Professional but warm. Encouraging, not condescending
- When unsure: say so clearly, then provide your best understanding

## Behaviour
- Always include practical examples with theory
- Use real-world case studies when explaining security concepts
- Format code with proper syntax highlighting
- Reference specific labs in this course when relevant

## Boundaries
- This is an educational platform — never assist with actual attacks
- Keep personal user data strictly private
```

### MEMORY.md — Long-Term Memory

```markdown
# Long-Term Memory

## User Preferences
- Prefers examples in Python (primary) or Go (secondary)
- Uses Docker for all development work
- Working on InnoZverse documentation platform

## Project Context
- Building GitBook-based documentation at lastcow/innoZverse-docs
- GitHub token stored securely
- Docker images published to zchencow/ namespace

## Key Decisions
- Labs verified in Docker before documenting
- Two-container architecture for cybersecurity labs
- All commands must run on Ubuntu 22.04 non-interactively
```

---

## Skills: Extending OpenClaw

A **skill** is a directory containing a `SKILL.md` file that gives the agent specialised instructions and tools for a specific task.

### Skill Structure

```
skills/my-skill/
├── SKILL.md          ← instructions for the agent
├── scripts/
│   └── fetch_data.py
└── assets/
    └── template.md
```

### Example: Weather Skill

```markdown
# SKILL.md — Weather

## When to Use This Skill
Use when the user asks about current weather, temperature, 
forecast, or whether to bring an umbrella.

## Instructions
1. Use the `web_fetch` tool to call:
   `https://wttr.in/{location}?format=j1`
   
2. Parse the JSON response for:
   - `current_condition[0].temp_C` — current temperature
   - `current_condition[0].weatherDesc[0].value` — description
   - `weather[0]` — today's forecast (max/min)

3. Present in a friendly, conversational format
   Include: temperature, conditions, feels-like, brief forecast

## Example Response Format
"It's 12°C and overcast in London right now, feeling like 9°C 
due to wind. Expect rain this afternoon, clearing by evening. 
Max 14°C today."
```

### Building a Custom Skill

```python
# skills/github-monitor/scripts/check_prs.py
import requests
import json
import sys

def get_open_prs(repo: str, token: str) -> list[dict]:
    """Fetch open pull requests for a GitHub repo"""
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    url = f"https://api.github.com/repos/{repo}/pulls?state=open"
    response = requests.get(url, headers=headers)
    prs = response.json()
    return [
        {
            "number": pr["number"],
            "title": pr["title"],
            "author": pr["user"]["login"],
            "created": pr["created_at"][:10],
            "url": pr["html_url"]
        }
        for pr in prs
    ]

if __name__ == "__main__":
    repo  = sys.argv[1]  # "lastcow/innoZverse-docs"
    token = sys.argv[2]
    prs = get_open_prs(repo, token)
    print(json.dumps(prs, indent=2))
```

```markdown
# SKILL.md — GitHub Monitor

## When to Use This Skill
Use when asked about pull requests, issues, or repo status 
for the innoZverse-docs repository.

## Instructions
1. Run: `python3 ~/openclaw/workspace/skills/github-monitor/scripts/check_prs.py lastcow/innoZverse-docs $GITHUB_TOKEN`
2. Parse the JSON output
3. Report: number of open PRs, their titles and authors
4. Flag any PRs open > 7 days as needing attention

## Environment Variables
- GITHUB_TOKEN: set in gateway config
```

---

## Heartbeat: Proactive Agent Behaviour

OpenClaw can run periodic background tasks via **heartbeats**:

```markdown
# HEARTBEAT.md

## Checks (run 2-4× per day)

### GitHub Repo
- Check lastcow/innoZverse-docs for any failed GitHub Actions
- Alert if workflow failures in last 24h

### Email
- Scan for emails with subject containing "InnoZverse" or "urgent"
- Summarise if any found

### Memory Maintenance
Every 3 days: review recent memory/*.md files and update MEMORY.md 
with key decisions and lessons learned
```

---

## Multi-Channel Deployment

OpenClaw can simultaneously respond on multiple platforms:

```yaml
# openclaw.config.yaml
channels:
  discord:
    token: "..."
    defaultChannel: "1476716608868061388"
    
  telegram:
    botToken: "..."
    
  whatsapp:
    accountId: "..."

agent:
  model: "claude-sonnet-4-6"
  workspace: "~/.openclaw/workspace"
  
cron:
  heartbeat: "*/30 * * * *"    # every 30 minutes
```

---

## ACP: Agent Communication Protocol

OpenClaw supports spawning sub-agents for parallel or specialised tasks:

```python
# In a session, spawn a coding subagent
sessions_spawn(
    task="Write and verify all 15 cybersecurity advanced labs",
    runtime="acp",
    agentId="claude-code",
    mode="session"
)
```

This is how the InnoZverse documentation itself was built — the main OpenClaw session orchestrated subagents to write, verify, and push hundreds of lab files in parallel.

---

## OpenClaw vs Other Platforms

| Platform | Self-hosted | Memory | Multi-channel | Skills | Open source |
|----------|------------|--------|--------------|--------|-------------|
| **OpenClaw** | ✅ | ✅ Persistent | ✅ | ✅ | ✅ |
| ChatGPT | ❌ | Limited | ❌ | Via plugins | ❌ |
| Claude.ai | ❌ | Projects only | ❌ | ❌ | ❌ |
| AutoGPT | ✅ | ✅ | ❌ | ✅ | ✅ |
| Open Interpreter | ✅ | ❌ | ❌ | Limited | ✅ |

---

## Further Reading

- [OpenClaw Documentation](https://docs.openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [ClawHub — Skill Marketplace](https://clawhub.com)
- [OpenClaw Discord Community](https://discord.com/invite/clawd)
