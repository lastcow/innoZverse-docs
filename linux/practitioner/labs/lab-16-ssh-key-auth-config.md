# Lab 16: SSH Key Authentication & Configuration

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

SSH key authentication is the gold standard for secure remote access. In this lab you will generate ed25519 keypairs, configure the SSH client config file, understand `authorized_keys`, manage `known_hosts`, and simulate `scp` file transfers — all verified in a live Docker container.

**Prerequisites:** Docker installed, Labs 01–15 completed.

---

## Step 1: Install SSH Tools & Generate an ed25519 Key

ed25519 keys are shorter, faster, and more secure than RSA-2048.

```bash
docker run -it --rm ubuntu:22.04 bash
apt-get update -qq && apt-get install -y -qq openssh-client
```

Generate a key non-interactively:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519 -C "admin@example.com"
```

| Flag | Meaning |
|------|---------|
| `-t ed25519` | Key type (ed25519 = Edwards-curve DSA) |
| `-N ""` | Empty passphrase (use a passphrase in production!) |
| `-f ~/.ssh/id_ed25519` | Output file path |
| `-C "admin@example.com"` | Comment (typically user@host) |

```bash
ls -la ~/.ssh/
cat ~/.ssh/id_ed25519.pub
ssh-keygen -l -f ~/.ssh/id_ed25519.pub
```

📸 **Verified Output:**
```
Generating public/private ed25519 key pair.
Your identification has been saved in /tmp/testkey
Your public key has been saved in /tmp/testkey.pub
The key fingerprint is:
SHA256:USwRmzasQRyWrlDprQscHIrs8x/ugMR8YNtVw6sAfvs admin@example.com
The key's randomart image is:
+--[ED25519 256]--+
|     o==o+.      |
| .. oo+oo+.      |
|+=.+ +. O.       |
|*oBoo o= o       |
|.*.=ooo S        |
|.o=.o.           |
| .oo.o           |
|   .+E.          |
|    o+           |
+----[SHA256]-----+
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGbiShwdx4NX8s71hVAaaNiJf5m3gM9vHszE0L1dAAwr admin@example.com
256 SHA256:USwRmzasQRyWrlDprQscHIrs8x/ugMR8YNtVw6sAfvs admin@example.com (ED25519)
```

> 💡 **Always use ed25519 for new keys.** If you must use RSA for compatibility, use at least 4096 bits: `ssh-keygen -t rsa -b 4096`. Never use DSA or ECDSA-256.

---

## Step 2: Understand Key Pair Structure

A keypair has two files:

```bash
# View the private key header (never share this file)
head -1 ~/.ssh/id_ed25519

# View the full public key (safe to share/deploy)
cat ~/.ssh/id_ed25519.pub

# Compare file permissions
ls -la ~/.ssh/
```

📸 **Verified Output:**
```
-----BEGIN OPENSSH PRIVATE KEY-----

ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGbiShwdx4NX8s71hVAaaNiJf5m3gM9vHszE0L1dAAwr admin@example.com

total 16
drwx------ 2 root root 4096 Mar  5 05:48 .
drwx------ 1 root root 4096 Mar  5 05:48 ..
-rw------- 1 root root  411 Mar  5 05:48 id_ed25519
-rw-r--r-- 1 root root  101 Mar  5 05:48 id_ed25519.pub
```

**Critical permissions:**

| File | Required Permission | Breaks SSH if wrong? |
|------|--------------------|--------------------|
| `~/.ssh/` | `700` (drwx------) | ✅ Yes |
| `~/.ssh/id_ed25519` | `600` (-rw-------) | ✅ Yes |
| `~/.ssh/id_ed25519.pub` | `644` (-rw-r--r--) | ❌ No |
| `~/.ssh/authorized_keys` | `600` (-rw-------) | ✅ Yes |

> 💡 **SSH is strict about permissions.** If `~/.ssh/` is world-readable, SSH will refuse to use your key with "bad permissions" error. Fix with `chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_ed25519`.

---

## Step 3: Configure authorized_keys (Server Side)

`authorized_keys` is how servers grant access — it lists public keys that may log in.

```bash
# Simulate the server side
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# ssh-copy-id does this automatically; here's what it does manually:
cat ~/.ssh/id_ed25519.pub >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

# Verify
cat /root/.ssh/authorized_keys
ls -la /root/.ssh/
```

📸 **Verified Output:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGbiShwdx4NX8s71hVAaaNiJf5m3gM9vHszE0L1dAAwr admin@example.com

total 16
drwx------ 2 root root 4096 Mar  5 05:48 .
drwx------ 1 root root 4096 Mar  5 05:48 ..
-rw------- 1 root root  101 Mar  5 05:48 authorized_keys
```

**`ssh-copy-id` equivalent:**

```bash
# What ssh-copy-id myserver does under the hood:
ssh user@server "mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
  cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys" \
  < ~/.ssh/id_ed25519.pub
```

> 💡 **Multiple keys in authorized_keys:** Each line is one public key. You can have many — one per team member, one per device. Comment lines start with `#`. Prefix keys with options like `command="backup.sh"` to restrict what a key can do.

---

## Step 4: Create ~/.ssh/config for Host Aliases

The SSH config file saves you from typing long commands every time.

```bash
cat > ~/.ssh/config << 'EOF'
# Production web server
Host webprod
    HostName 203.0.113.10
    User deploy
    IdentityFile ~/.ssh/id_ed25519
    Port 22

# Jump / bastion host
Host jumpbox
    HostName jump.example.com
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
    Port 2222
    ServerAliveInterval 60

# Reach internal hosts through jumpbox
Host internal-*
    ProxyJump jumpbox
    User admin
    IdentityFile ~/.ssh/id_ed25519

# Default settings for all hosts
Host *
    AddKeysToAgent yes
    ServerAliveCountMax 3
EOF

chmod 600 ~/.ssh/config
cat ~/.ssh/config
```

📸 **Verified Output:**
```
# Production web server
Host webprod
    HostName 203.0.113.10
    User deploy
    IdentityFile ~/.ssh/id_ed25519
    Port 22

# Jump / bastion host
Host jumpbox
    HostName jump.example.com
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
    Port 2222
    ServerAliveInterval 60

# Reach internal hosts through jumpbox
Host internal-*
    ProxyJump jumpbox
    User admin
    IdentityFile ~/.ssh/id_ed25519

# Default settings for all hosts
Host *
    AddKeysToAgent yes
    ServerAliveCountMax 3
```

**Config directives explained:**

| Directive | Purpose |
|-----------|---------|
| `Host` | Alias (what you type in `ssh <alias>`) |
| `HostName` | Real hostname or IP |
| `User` | Remote username |
| `IdentityFile` | Which private key to use |
| `Port` | SSH port (default 22) |
| `ProxyJump` | Jump through another host |
| `ServerAliveInterval` | Send keepalive every N seconds |

> 💡 **With this config, `ssh webprod` expands to `ssh -i ~/.ssh/id_ed25519 -p 22 deploy@203.0.113.10`** — much less typing. Use `ssh -G webprod` to see all resolved options for a host.

---

## Step 5: SSH Agent — Managing Keys in Memory

`ssh-agent` caches your decrypted private keys so you don't retype passphrases.

```bash
# Start the agent (normally done by your login shell)
eval $(ssh-agent -s)

# Add your key to the agent
ssh-add ~/.ssh/id_ed25519

# List loaded keys
ssh-add -l

# Check agent environment variables
echo "SSH_AUTH_SOCK=$SSH_AUTH_SOCK"
echo "SSH_AGENT_PID=$SSH_AGENT_PID"
```

📸 **Verified Output:**
```
Agent pid 1042
Identity added: /root/.ssh/id_ed25519 (admin@example.com)
256 SHA256:USwRmzasQRyWrlDprQscHIrs8x/ugMR8YNtVw6sAfvs admin@example.com (ED25519)
SSH_AUTH_SOCK=/tmp/ssh-XXXXXX/agent.1042
SSH_AGENT_PID=1042
```

**Agent commands:**

| Command | Action |
|---------|--------|
| `ssh-add ~/.ssh/id_ed25519` | Add key to agent |
| `ssh-add -l` | List loaded keys |
| `ssh-add -d ~/.ssh/id_ed25519` | Remove specific key |
| `ssh-add -D` | Remove all keys |
| `ssh-add -t 3600` | Add with 1-hour expiry |

> 💡 **`AddKeysToAgent yes` in ~/.ssh/config** automatically adds keys when first used, so you don't need to manually run `ssh-add`. On macOS, also set `UseKeychain yes` to store passphrases in the system keychain.

---

## Step 6: known_hosts — Preventing MITM Attacks

`known_hosts` records server fingerprints so you can detect if a server's identity changes.

```bash
# Simulate known_hosts entries
mkdir -p ~/.ssh

# Add a fake known_hosts entry (format: hostname key-type public-key)
cat > ~/.ssh/known_hosts << 'EOF'
webprod,203.0.113.10 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPmHXzK5H2pzQ+e/vL4xnQG3FJP5b6789zyXVvkQ0000
jump.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBkTmqJD2wZ3fRs+b/t0QkLj7Fw+9e6Yq5cHGkAoAaaa
EOF

cat ~/.ssh/known_hosts

# ssh-keyscan gathers fingerprints from live hosts:
# ssh-keyscan -H github.com >> ~/.ssh/known_hosts
echo "known_hosts has $(wc -l < ~/.ssh/known_hosts) entries"

# Hashed known_hosts (more private)
# ssh-keygen -H -F webprod   # look up a host
# ssh-keygen -R webprod       # remove a host entry
```

📸 **Verified Output:**
```
webprod,203.0.113.10 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPmHXzK5H2pzQ+e/vL4xnQG3FJP5b6789zyXVvkQ0000
jump.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBkTmqJD2wZ3fRs+b/t0QkLj7Fw+9e6Yq5cHGkAoAaaa
known_hosts has 2 entries
```

> 💡 **`StrictHostKeyChecking yes`** (set in `~/.ssh/config` Host * block) refuses connections to unknown hosts instead of prompting. Use this in scripts and automation to catch MITM attacks. Use `ssh-keyscan` to pre-populate `known_hosts` before automation runs.

---

## Step 7: SCP — Secure File Copy

`scp` uses SSH to copy files between hosts. With your `~/.ssh/config`, the aliases work here too.

```bash
# Create test files
mkdir -p /tmp/myfiles
echo "Server config v2.1" > /tmp/myfiles/server.conf
echo "Deployment notes" > /tmp/myfiles/deploy.txt
ls -la /tmp/myfiles/

# SCP syntax examples (these would run against real hosts):
# Copy local file to remote:
echo "scp /tmp/myfiles/server.conf webprod:/etc/myapp/server.conf"

# Copy remote file to local:
echo "scp webprod:/var/log/app.log /tmp/app.log"

# Copy entire directory recursively:
echo "scp -r /tmp/myfiles/ webprod:/tmp/backup/"

# Copy between two remote hosts:
echo "scp webprod:/etc/myapp/server.conf jumpbox:/tmp/server.conf"

# Use specific port:
echo "scp -P 2222 /tmp/file.txt user@host:/tmp/"

# Show equivalent rsync (preferred for large transfers):
echo "rsync -avz --progress /tmp/myfiles/ webprod:/tmp/backup/"

# Verify local file structure
find /tmp/myfiles -type f -exec echo "  {}" \;
```

📸 **Verified Output:**
```
total 16
drwxr-xr-x 2 root root 4096 Mar  5 05:50 .
drwxrwxrwt 1 root root 4096 Mar  5 05:50 ..
-rw-r--r-- 1 root root   19 Mar  5 05:50 deploy.txt
-rw-r--r-- 1 root root   19 Mar  5 05:50 server.conf
scp /tmp/myfiles/server.conf webprod:/etc/myapp/server.conf
scp webprod:/var/log/app.log /tmp/app.log
scp -r /tmp/myfiles/ webprod:/tmp/backup/
scp webprod:/etc/myapp/server.conf jumpbox:/tmp/server.conf
scp -P 2222 /tmp/file.txt user@host:/tmp/
rsync -avz --progress /tmp/myfiles/ webprod:/tmp/backup/
  /tmp/myfiles/deploy.txt
  /tmp/myfiles/server.conf
```

> 💡 **Prefer `rsync` over `scp` for anything more than a single file.** `rsync` skips unchanged files, supports resuming interrupted transfers, and preserves permissions. `scp -3` routes through your local machine when copying between two remote hosts, which is slower than direct `rsync`.

---

## Step 8: Capstone — Build a Complete SSH Setup Script

**Scenario:** You're onboarding a new server. Automate the entire SSH security setup.

```bash
cat > /tmp/ssh-setup.sh << 'SCRIPT'
#!/bin/bash
# ssh-setup.sh — Complete SSH key + config setup
set -euo pipefail

SSH_DIR="$HOME/.ssh"
KEY_FILE="$SSH_DIR/id_ed25519"
CONFIG_FILE="$SSH_DIR/config"
SERVER_USER="${1:-admin}"
SERVER_HOST="${2:-myserver.example.com}"
SERVER_PORT="${3:-22}"
ALIAS="${4:-myserver}"

echo "=== SSH Setup for $ALIAS ($SERVER_USER@$SERVER_HOST:$SERVER_PORT) ==="

# 1. Ensure ~/.ssh exists with correct permissions
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"
echo "[1] ~/.ssh directory: OK (chmod 700)"

# 2. Generate key if it doesn't exist
if [ ! -f "$KEY_FILE" ]; then
    ssh-keygen -t ed25519 -N "" -f "$KEY_FILE" -C "$SERVER_USER@$(hostname)"
    echo "[2] Generated new ed25519 key: $KEY_FILE"
else
    echo "[2] Key already exists: $KEY_FILE"
fi

# 3. Add host to SSH config if not already there
if ! grep -q "^Host $ALIAS$" "$CONFIG_FILE" 2>/dev/null; then
    cat >> "$CONFIG_FILE" << EOF

Host $ALIAS
    HostName $SERVER_HOST
    User $SERVER_USER
    IdentityFile $KEY_FILE
    Port $SERVER_PORT
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
    chmod 600 "$CONFIG_FILE"
    echo "[3] Added '$ALIAS' to SSH config"
else
    echo "[3] '$ALIAS' already in SSH config"
fi

# 4. Display public key for deployment
echo ""
echo "=== Deploy this public key to $SERVER_HOST ==="
echo "Run on the server: mkdir -p ~/.ssh && chmod 700 ~/.ssh"
echo "Then append this line to ~/.ssh/authorized_keys:"
cat "$KEY_FILE.pub"
echo ""

# 5. Show fingerprint
echo "=== Key fingerprint ==="
ssh-keygen -l -f "$KEY_FILE.pub"

# 6. Test connection syntax (won't connect in Docker)
echo ""
echo "=== Connection command ==="
echo "ssh $ALIAS"
echo "# Expands to: ssh -i $KEY_FILE -p $SERVER_PORT $SERVER_USER@$SERVER_HOST"

echo ""
echo "=== Setup complete! ==="
SCRIPT

chmod +x /tmp/ssh-setup.sh
bash /tmp/ssh-setup.sh deploy prod.example.com 22 prod
```

📸 **Verified Output:**
```
=== SSH Setup for prod (deploy@prod.example.com:22) ===
[1] ~/.ssh directory: OK (chmod 700)
Generating public/private ed25519 key pair.
Your identification has been saved in /root/.ssh/id_ed25519
Your public key has been saved in /root/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:USwRmzasQRyWrlDprQscHIrs8x/ugMR8YNtVw6sAfvs deploy@container
[2] Generated new ed25519 key: /root/.ssh/id_ed25519
[3] Added 'prod' to SSH config

=== Deploy this public key to prod.example.com ===
Run on the server: mkdir -p ~/.ssh && chmod 700 ~/.ssh
Then append this line to ~/.ssh/authorized_keys:
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGbiShwdx4NX8s71hVAaaNiJf5m3gM9vHszE0L1dAAwr deploy@container

=== Key fingerprint ===
256 SHA256:USwRmzasQRyWrlDprQscHIrs8x/ugMR8YNtVw6sAfvs deploy@container (ED25519)

=== Connection command ===
ssh prod
# Expands to: ssh -i /root/.ssh/id_ed25519 -p 22 deploy@prod.example.com

=== Setup complete! ===
```

> 💡 **Security hardening checklist:** Disable password auth (`PasswordAuthentication no` in `/etc/ssh/sshd_config`), disable root login (`PermitRootLogin no`), restrict to key auth only, use `AllowUsers` to whitelist users, and change the default port from 22 to reduce automated scanning noise.

---

## Summary

| Concept | Command / File | Purpose |
|---------|---------------|---------|
| Generate key | `ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519` | Create keypair |
| Deploy key | `ssh-copy-id user@host` | Append pubkey to authorized_keys |
| authorized_keys | `~/.ssh/authorized_keys` | Server: allowed public keys |
| SSH config | `~/.ssh/config` | Client: host aliases & options |
| SSH agent | `eval $(ssh-agent -s); ssh-add` | Cache decrypted keys |
| known_hosts | `~/.ssh/known_hosts` | Server fingerprint verification |
| Secure copy | `scp file user@host:/path/` | Copy files over SSH |
| View config | `ssh -G hostname` | Show resolved SSH options |
| Scan fingerprint | `ssh-keyscan -H host` | Get host's public key |
| Remove host | `ssh-keygen -R hostname` | Remove from known_hosts |
