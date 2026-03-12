# Troubleshooting Guide

## OpenClaw Issues

### "openclaw command not found"

**Solutions:**

1. Check Node.js version:
   ```bash
   node --version
   ```
   Must be 22 or higher. If not, upgrade Node.js.

2. Reinstall OpenClaw:
   ```bash
   curl -fsSL https://openclaw.ai/install.sh | bash
   ```

3. Verify PATH includes openclaw:
   ```bash
   echo $PATH | grep openclaw
   ```

4. Restart your shell:
   ```bash
   source ~/.bashrc   # Linux/macOS
   source ~/.zshrc    # macOS (if using Zsh)
   ```

### "Control UI won't open"

**Solutions:**

1. Check if gateway is running:
   ```bash
   openclaw gateway status
   ```

2. Start it manually:
   ```bash
   openclaw gateway --port 18789
   ```

3. Open http://127.0.0.1:18789/ in your browser

4. If port 18789 is in use:
   ```bash
   openclaw gateway --port 18790
   ```

### "Permission denied" errors

**Solutions:**

1. Grant permissions:
   ```bash
   chmod +x ~/.local/bin/openclaw
   ```

2. Run with sudo (not recommended):
   ```bash
   sudo openclaw gateway --port 18789
   ```

3. Check home directory permissions:
   ```bash
   ls -la ~/.openclaw
   ```

---

## Docker Issues

### "Docker image not found"

**Solutions:**

1. Verify Docker is running:
   ```bash
   docker ps
   ```

2. Check image name (case-sensitive):
   ```bash
   docker pull zchencow/innozverse-linux:latest
   ```

3. List available images:
   ```bash
   docker images | grep innozverse
   ```

4. Pull the image:
   ```bash
   docker pull zchencow/innozverse-linux:latest
   ```

### "Cannot connect to Docker daemon"

**Solutions:**

1. Start Docker:
   - **macOS:** Open Docker Desktop
   - **Linux:** `sudo systemctl start docker`
   - **Windows:** Launch Docker Desktop

2. Check Docker status:
   ```bash
   docker info
   ```

3. Add user to docker group (Linux):
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### "Disk space error"

**Solutions:**

1. Clean up unused images:
   ```bash
   docker system prune -a
   ```

2. Check available space:
   ```bash
   df -h
   ```

3. Free up disk space and retry

---

## Lab Issues

### "Lab output doesn't match the guide"

This is **normal**! Environments vary by OS, Docker version, library versions, etc.

**What to do:**

1. Compare the **structure** of your output (same files, similar sizes)
2. Check for **error messages** (those matter)
3. Re-run the command if it failed
4. Read the lab **README.md** for environment notes
5. Check the lab GitHub issues for known issues

### "Command not found inside lab"

**Solutions:**

1. Verify you're inside the container:
   ```bash
   whoami  # Should show lab user, not your OS user
   ```

2. Update package manager:
   ```bash
   apt-get update && apt-get install -y PACKAGE_NAME  # Linux
   brew install PACKAGE_NAME                           # macOS
   ```

3. Install missing dependencies per lab instructions

### "Files disappear after exiting container"

**Solution:** Use volume mount to persist files:

```bash
docker run -it --rm -v $(pwd):/work zchencow/innozverse-{DOMAIN}:latest bash
```

---

## Network Issues

### "Cannot reach OpenClaw gateway"

**Solutions:**

1. Verify gateway is running and listening:
   ```bash
   openclaw gateway status
   curl http://127.0.0.1:18789/health
   ```

2. Check firewall allows port 18789:
   ```bash
   sudo lsof -i :18789  # macOS/Linux
   netstat -ano | findstr :18789  # Windows
   ```

3. Try a different port:
   ```bash
   openclaw gateway --port 18790
   ```

---

## Frequently Asked Issues

**Q: My lab runs but produces different output**\
A: This is expected. Compare structure, check for errors, and verify prerequisites.

**Q: Files are lost when I exit Docker**\
A: You didn't use `-v` flag. Use: `docker run -it --rm -v $(pwd):/work ...`

**Q: OpenClaw wizard keeps crashing**\
A: Check `~/.openclaw/logs/` for error details. Try reinstalling.

**Q: Discord integration not working**\
A: Ensure OAuth token is valid. Re-authorize in Control UI.

---

## Getting Help

If these solutions don't work:

1. Check lab GitHub issues: https://github.com/lastcow/innoZverse-docs/issues
2. Read the official [OpenClaw Docs](https://docs.openclaw.ai/)
3. Join the community: https://discord.com/invite/clawd
4. Report a bug with details (OS, versions, error messages)

---

**See Also:**
- [Installation Guide](installation.md)
- [OpenClaw Setup](openclaw-setup.md)
- [Docker Quick Start](docker-quickstart.md)
- [Getting Started](README.md)
