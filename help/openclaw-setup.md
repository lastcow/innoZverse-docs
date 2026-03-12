# OpenClaw Setup

## What is OpenClaw?

OpenClaw is a self-hosted gateway that connects your chat apps (Discord, Telegram, WhatsApp, etc.) to AI agents. Perfect for running InnoZverse labs and automating workflows.

## Setup Steps

### Step 1: Install OpenClaw

See [Installation Guide](installation.md)

### Step 2: Run the Setup Wizard

```bash
openclaw onboard --install-daemon
```

This wizard will:
- Configure authentication
- Set gateway port (default: 18789)
- Optionally link Discord/Telegram channels
- Enable auto-start on reboot

### Step 3: Verify the Gateway

```bash
openclaw gateway status
```

You should see: `Gateway is running`

### Step 4: Open the Control UI

```bash
openclaw dashboard
```

Your browser will open to `http://127.0.0.1:18789/`. If it loads, you're ready!

## Run Gateway in Foreground (Testing)

For quick tests or troubleshooting:

```bash
openclaw gateway --port 18789
```

## Environment Variables

```bash
# Custom home directory
export OPENCLAW_HOME=/path/to/home

# Custom state directory
export OPENCLAW_STATE_DIR=/path/to/state

# Custom config path
export OPENCLAW_CONFIG_PATH=/path/to/config.json
```

## Next Steps

- [Connect Discord Channel](../help/README.md#2-connect-discord-optional)
- [Run Your First Lab](docker-quickstart.md)
- [Troubleshooting](troubleshooting.md)

For full details: [OpenClaw Docs - Getting Started](https://docs.openclaw.ai/start/getting-started)
