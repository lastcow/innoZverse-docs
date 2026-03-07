# OpenClaw Server Setup — Project Log

**Server:** Ubuntu 25.04 @ `104.167.196.25`  
**User:** `zchen`  
**Completed:** 2026-03-07  
**Bot name:** `cow1` (Discord: `1479731383025930393`)

---

## Requirements

- OpenClaw latest version
- AI Model: ChatGPT (OpenAI Codex OAuth — no API key)
- Communication channel: Discord
- Skill: GitHub (`gh` CLI)
- Full server control (exec, file system, shell)
- Bot restricted to one Discord channel only

---

## Step-by-Step (Correct Process)

### 1. SSH Key Setup (Option B — key-based, not password)

Ubuntu 25 disables SSH password auth by default. Generate key locally, add pubkey to server.

```bash
# On local machine (OpenClaw sandbox):
ssh-keygen -t ed25519 -C "openclaw@lastcow" -f ~/.openclaw/workspace/professor/secrets/ssh/openclaw_server -N ""

# User runs on server console:
mkdir -p ~/.ssh && echo "<PUBLIC_KEY>" >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```

### 2. Install Node.js LTS

```bash
echo '<password>' | sudo -S bash -c "curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && apt-get install -y nodejs"
```

### 3. Install OpenClaw

```bash
echo '<password>' | sudo -S npm install -g openclaw --loglevel=error
openclaw --version  # verify: 2026.3.2
```

### 4. Install System Dependencies

```bash
echo '<password>' | sudo -S apt-get install -y curl git build-essential gh
```

### 5. Set Default Model

```bash
openclaw models set "openai/gpt-4o"  # placeholder; gets overwritten by OAuth wizard
```

### 6. Run Onboarding Wizard (via tmux — requires interactive TTY)

```bash
tmux new-session -d -s openclaw
tmux send-keys -t openclaw "openclaw onboard" Enter
```

Wizard flow:
1. Accept security notice → **Yes**
2. Onboarding mode → **QuickStart**
3. Config handling → **Use existing values**
4. Model/auth provider → **OpenAI (Codex OAuth + API key)**
5. OpenAI auth method → **OpenAI Codex (ChatGPT OAuth)**
6. A URL appears → open in **local browser**, sign in, copy the redirect URL (starts with `http://localhost:1455/auth/callback?code=...`), paste back
7. Default model → **Keep current** (`openai-codex/gpt-5.3-codex`)
8. Channel → **Discord (Bot API)** (press Down twice from Telegram)
9. Provide token → **Enter Discord bot token**
10. Configure channels access → **Yes** → **Open (allow all)** ← change to allowlist later
11. Skills → select **🐙 github** with Space → Enter
12. Homebrew prompt → **No** (install gh via apt instead)
13. Hooks → select **Skip for now** → Enter
14. Systemd lingering → auto-enabled

### 7. Fix Gateway Service (systemd issue)

The wizard fails to install the service cleanly. Create manually:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/openclaw-gateway.service << EOF
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
Environment=GH_TOKEN=<github_token>
ExecStart=/usr/bin/openclaw gateway run --bind lan
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF

export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user daemon-reload
systemctl --user enable openclaw-gateway
systemctl --user start openclaw-gateway
```

### 8. Fix Gateway ControlUI Error (non-loopback)

When using `--bind lan`, the gateway requires this config:

```bash
openclaw config set gateway.mode local
openclaw config set gateway.controlUi.dangerouslyAllowHostHeaderOriginFallback true
```

### 9. Authenticate GitHub CLI

The `gh auth login --with-token` requires interactive TTY. Use `GH_TOKEN` env var instead:

```bash
echo "export GH_TOKEN=<token>" >> ~/.bashrc
echo "export GH_TOKEN=<token>" >> ~/.profile
# Add to systemd service Environment= line too
```

Note: Token needs `repo`, `workflow` scopes minimum. `read:org` is optional but recommended.

### 10. Enable Full Server Control

Edit `~/.openclaw/openclaw.json`:

```json
"tools": {
    "profile": "full",
    "exec": {
        "ask": "off",
        "security": "full"
    }
}
```

Then restart: `systemctl --user restart openclaw-gateway`

### 11. Whitelist to One Discord Channel

Get server ID from channel ID via Discord API:
```bash
curl -s "https://discord.com/api/v10/channels/<CHANNEL_ID>" \
  -H "Authorization: Bot <BOT_TOKEN>" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('guild_id'))"
```

Then set config:

```json
"channels": {
    "discord": {
        "groupPolicy": "allowlist",
        "guilds": {
            "<SERVER_ID>": {
                "requireMention": false,
                "channels": {
                    "<CHANNEL_ID>": {}
                }
            }
        }
    }
}
```

Validate: `openclaw config validate`  
Restart: `systemctl --user restart openclaw-gateway`

---

## Mistakes Made & Solutions

| # | Mistake | Solution |
|---|---------|----------|
| 1 | Tried `sshpass` — not installed in sandbox | Use SSH key pair (Option B) instead |
| 2 | `openclaw gateway status` hung (exit 255) | Gateway wasn't running yet; run `openclaw onboard` first |
| 3 | `openclaw models auth login --provider openai-codex` → "No provider plugins found" | Use `openclaw onboard` wizard instead — it wires OAuth correctly |
| 4 | GitHub skill install failed: "brew not installed" | Install `gh` via `sudo apt-get install -y gh` then set `GH_TOKEN` env var |
| 5 | `gh auth login --with-token` failed (needs interactive TTY) | Use `GH_TOKEN=<token>` env var; add to `~/.bashrc`, `~/.profile`, and systemd `Environment=` |
| 6 | Gateway failed with "non-loopback Control UI requires allowedOrigins" | Set `gateway.controlUi.dangerouslyAllowHostHeaderOriginFallback=true` |
| 7 | Systemd service install failed (`systemctl --user is-enabled` unavailable) | Create service file manually in `~/.config/systemd/user/` and enable manually |
| 8 | Config key `tools.exec.elevated` rejected by schema validator | Remove `elevated` — only valid keys are `ask` and `security` |
| 9 | Config key `agents.defaults.exec` rejected | `exec` lives under `tools`, not `agents.defaults` |
| 10 | Channel allowlist set as `"groups": ["<id>"]` (wrong key, array) | Correct key is `"guilds": { "<server_id>": { "channels": { "<channel_id>": {} } } }` |
| 11 | `"channels"` under guild set as array `["id"]` | Must be an object/record: `{ "<channel_id>": {} }` |
| 12 | Multi-line SSH commands with `#` comments failed | Comments inside multi-line SSH strings break bash; use separate commands or semicolons |

---

## Config Reference (Final State)

```json
{
    "tools": {
        "profile": "full",
        "exec": { "ask": "off", "security": "full" }
    },
    "agents": {
        "defaults": {
            "model": { "primary": "openai-codex/gpt-5.3-codex" },
            "workspace": "/home/zchen/.openclaw/workspace"
        }
    },
    "channels": {
        "discord": {
            "enabled": true,
            "token": "<BOT_TOKEN>",
            "groupPolicy": "allowlist",
            "streaming": "off",
            "guilds": {
                "<SERVER_ID>": {
                    "requireMention": false,
                    "channels": { "<CHANNEL_ID>": {} }
                }
            }
        }
    },
    "gateway": {
        "port": 18789,
        "mode": "local",
        "bind": "loopback",
        "controlUi": { "dangerouslyAllowHostHeaderOriginFallback": true }
    }
}
```

---

## Key Credentials (stored separately)

| Item | Location |
|------|----------|
| SSH private key | `~/.openclaw/workspace/professor/secrets/ssh/openclaw_server` |
| SSH public key | `~/.openclaw/workspace/professor/secrets/ssh/openclaw_server.pub` |
| Server password | `Paradise@0` |
| Discord bot token | In server `openclaw.json` |
| GitHub token | `GH_TOKEN` env var on server |
