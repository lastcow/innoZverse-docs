---
description: Setup guides and quick-start tutorials for InnoZverse platform and tools
cover: .gitbook/assets/help-hero.svg
coverY: 0
layout:
  cover:
    visible: true
    size: hero
  title:
    visible: false
  description:
    visible: false
  tableOfContents:
    visible: false
  outline:
    visible: false
  pagination:
    visible: false
---

# Help Center

<div align="center">

## Quick Start & Setup Guides

**Get up and running with InnoZverse and OpenClaw in minutes.**\
Step-by-step tutorials without the deep verification.\
For detailed info, refer to the official [OpenClaw Docs](https://docs.openclaw.ai/).

</div>

---

## Getting Started

### 1. Install OpenClaw (AI Agent Gateway)

OpenClaw is a self-hosted gateway that connects your chat apps (Discord, Telegram, WhatsApp, etc.) to AI agents. Perfect for running InnoZverse labs and automating workflows.

**System Requirements:**
- Node.js 22 or newer
- Any OS (macOS, Linux, Windows)
- ~500MB free disk space

#### Step 1: Install OpenClaw

{% tabs %}
{% tab title="macOS / Linux" %}

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

{% endtab %}

{% tab title="Windows (PowerShell)" %}

```powershell
iwr -useb https://openclaw.ai/install.ps1 | iex
```

{% endtab %}
{% endtabs %}

#### Step 2: Run the Setup Wizard

```bash
openclaw onboard --install-daemon
```

This wizard will:
- Configure authentication
- Set gateway port (default: 18789)
- Optionally link Discord/Telegram channels
- Enable auto-start on reboot

#### Step 3: Verify Installation

```bash
openclaw gateway status
```

You should see: `Gateway is running`

#### Step 4: Open the Control UI

```bash
openclaw dashboard
```

Your browser will open to `http://127.0.0.1:18789/`. If it loads, you're ready!

**Next:** Configure your first channel in the Control UI.

---

### 2. Connect Discord (Optional)

If you want to chat with AI agents via Discord:

1. Go to the **OpenClaw Control UI** (http://127.0.0.1:18789/)
2. Click **Channels** → **+ Add Channel**
3. Select **Discord** and follow the OAuth flow
4. Select your Discord server and authorize
5. OpenClaw will create a DM conversation with you

You can now message the AI directly on Discord!

**For details:** [OpenClaw Channels Docs](https://docs.openclaw.ai/channels)

---

### 3. Run Your First Lab with OpenClaw

#### Docker-Based Lab (Recommended)

```bash
# Pull and run a Python lab
docker pull zchencow/innozverse-ai:latest
docker run -it --rm zchencow/innozverse-ai:latest bash
```

You're now inside the lab environment. Run Python scripts, try ML experiments, whatever the lab requires.

#### Local Lab (No Docker)

1. Clone the InnoZverse docs:
   ```bash
   git clone https://github.com/lastcow/innoZverse-docs.git
   cd innoZverse-docs
   ```

2. Navigate to a lab folder:
   ```bash
   cd linux/foundations/labs/lab-01-intro-to-terminal
   ```

3. Follow the lab's **README.md** for environment setup and commands

---

## Platform Guides

### Using the InnoZverse Labs

All labs are organized by level:

- **Foundations** — Core concepts, no prior experience needed
- **Practitioner** — Real-world scenarios, 1–3 years experience
- **Advanced** — Deep internals and complex patterns
- **Architect** — System design at scale

**How to start:**
1. Pick a domain (Linux, Cybersecurity, Networking, etc.)
2. Choose a level based on your experience
3. Read the lab **README.md** for prerequisites
4. Follow the step-by-step commands
5. Every output shown has been verified — if yours differs, that's a learning opportunity

### Docker Quick Reference

```bash
# Pull an image
docker pull zchencow/innozverse-{DOMAIN}:latest
# Example: zchencow/innozverse-linux, zchencow/innozverse-cybersec

# Run interactively
docker run -it --rm zchencow/innozverse-{DOMAIN}:latest bash

# Run with volume mount (persist files)
docker run -it --rm -v $(pwd):/work zchencow/innozverse-{DOMAIN}:latest bash

# Run a specific lab
docker run -it --rm zchencow/innozverse-{DOMAIN}:latest \
  bash /labs/foundations/lab-01/setup.sh
```

---

## Troubleshooting

### "openclaw command not found"

1. Check if Node.js 22+ is installed: `node --version`
2. Reinstall OpenClaw: `curl -fsSL https://openclaw.ai/install.sh | bash`
3. Verify PATH: `echo $PATH` should include `~/.local/bin`
4. Restart your shell or run: `source ~/.bashrc`

### "Control UI won't open"

1. Check if gateway is running: `openclaw gateway status`
2. Start it manually: `openclaw gateway --port 18789`
3. Open http://127.0.0.1:18789/ in your browser
4. If port 18789 is in use, change it: `openclaw gateway --port 18790`

### "Docker image not found"

1. Make sure Docker is running: `docker ps`
2. Check the image name (case-sensitive): `docker pull zchencow/innozverse-linux:latest`
3. List available images: `docker images | grep innozverse`
4. If not found, pull it: `docker pull zchencow/innozverse-linux:latest`

### "Lab output doesn't match"

This is normal! Lab environments vary by OS, Docker version, library versions, etc.

- Compare the **structure** of your output (same files, similar sizes)
- Check for error messages (those matter)
- Re-run the command if it failed
- Read the lab **README.md** for environment notes

---

## Resources

### Official Documentation

- **OpenClaw Docs:** https://docs.openclaw.ai/
- **OpenClaw GitHub:** https://github.com/openclaw/openclaw
- **Discord Community:** https://discord.com/invite/clawd

### InnoZverse

- **Lab Repository:** https://github.com/lastcow/innoZverse-docs
- **Home:** [HOME.md](HOME.md)
- **All Domains:** [Linux](linux/README.md) | [Cybersecurity](cyber-security/README.md) | [Networking](networking/README.md) | [Database](database/README.md) | [Programming](programming/README.md) | [AI & ML](artificial-intelligent-ai/README.md)

### Tutorials by Topic

- **Linux Setup** → [Linux Foundations](linux/README.md#foundations)
- **Security Labs** → [Cybersecurity Practitioner](cyber-security/README.md#practitioner)
- **Python Development** → [Programming Python](programming/python/README.md)
- **Database Design** → [Database Practitioner](database/README.md#practitioner)
- **Machine Learning** → [AI Foundations](artificial-intelligent-ai/README.md#foundations)

---

## Frequently Asked Questions

**Q: Do I need to buy anything?**\
A: No. All labs, OpenClaw, and InnoZverse are free and open-source.

**Q: Can I run multiple OpenClaw instances?**\
A: Yes, just use different ports: `openclaw gateway --port 18790`

**Q: Do my lab files persist when I exit Docker?**\
A: Only if you mount a volume with `-v $(pwd):/work`. Without it, files are lost.

**Q: Can I use OpenClaw without Docker?**\
A: Yes, most labs work on Ubuntu 22.04+ or macOS with Python 3.10+ installed natively.

**Q: What if I find a broken lab?**\
A: Open an issue on [GitHub](https://github.com/lastcow/innoZverse-docs/issues). Verified fixes are merged within 48 hours.

---

<div align="center">

**Ready to learn?** Pick a domain above and start with Foundations.

*InnoZverse — Learn by doing. Verify everything.*

</div>
