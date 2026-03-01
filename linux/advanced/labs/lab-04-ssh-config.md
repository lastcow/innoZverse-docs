# Lab 4: SSH Configuration

## 🎯 Objective
Create and manage SSH client configuration using ~/.ssh/config to simplify connections, define aliases, and configure security options.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Advanced Lab 3: SSH Key Generation

## 🔬 Lab Instructions

### Step 1: Create ~/.ssh Directory and Config

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ls -la ~/.ssh
```

```bash
# Check for existing config
cat ~/.ssh/config 2>/dev/null || echo "No config file yet"
```

### Step 2: Basic SSH Config Structure

```bash
# Backup existing config if it exists
cp ~/.ssh/config ~/.ssh/config.bak 2>/dev/null || true

# Create a basic config
cat > /tmp/ssh-config-demo.txt << 'EOF'
# SSH Client Configuration (~/.ssh/config)
# Format: Host alias followed by settings

# Default settings for all hosts
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
    AddKeysToAgent yes
    IdentityFile ~/.ssh/id_ed25519

# Production web server
Host webprod
    HostName 192.168.1.100
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519-prod

# Development server
Host dev
    HostName dev.example.com
    User zchen
    Port 2222
    ForwardAgent yes

# Jump through bastion host
Host internal-db
    HostName 10.0.1.50
    User dbadmin
    ProxyJump bastion

# Bastion/jump host
Host bastion
    HostName bastion.example.com
    User zchen
    IdentityFile ~/.ssh/id_ed25519

# GitHub (common configuration)
Host github.com
    User git
    IdentityFile ~/.ssh/id_ed25519-github
    AddKeysToAgent yes
EOF

cat /tmp/ssh-config-demo.txt
```

### Step 3: Write a Working Config File

```bash
# Write a safe demo config (using localhost)
cat > /tmp/demo-ssh-config << 'EOF'
# Demo SSH Config

Host localhost-test
    HostName 127.0.0.1
    User zchen
    Port 22
    StrictHostKeyChecking no
    ConnectTimeout 5

Host * 
    ServerAliveInterval 60
    ConnectTimeout 10
EOF

# Validate syntax
ssh -F /tmp/demo-ssh-config -G localhost-test 2>/dev/null | grep -E "^(hostname|user|port|connecttimeout)" | head -10
```

**Expected output:**
```
hostname 127.0.0.1
user zchen
port 22
connecttimeout 5
```

### Step 4: Understand Key Configuration Options

```bash
cat > /tmp/ssh-options-reference.txt << 'EOF'
COMMON SSH CONFIG OPTIONS:

Connection:
  HostName          Actual hostname or IP to connect to
  Port              SSH port (default: 22)
  User              Username to connect as
  ConnectTimeout    Seconds before connection times out

Security:
  IdentityFile      Path to private key file
  StrictHostKeyChecking  yes|no|accept-new
    yes: Fail if host key not in known_hosts
    no:  Accept any host key (INSECURE - use for testing only)
    accept-new: Accept new keys, reject changed keys

ProxyJump / Bastion:
  ProxyJump         Jump through another SSH host
  ProxyCommand      Custom command to establish connection

Agent Forwarding:
  ForwardAgent      yes|no - Forward SSH agent (use carefully)
  AddKeysToAgent    yes|no - Add private key to agent

Keepalive:
  ServerAliveInterval  Send keepalive every N seconds
  ServerAliveCountMax  Max keepalives before disconnect

Multiplexing (faster reconnects):
  ControlMaster     auto
  ControlPath       ~/.ssh/controlmasters/%r@%h:%p
  ControlPersist    10m
EOF

cat /tmp/ssh-options-reference.txt
```

### Step 5: ProxyJump Explained

```bash
cat > /tmp/proxyjump-example.txt << 'EOF'
PROXYJUMP (Bastion/Jump Host):

Scenario: You need to reach internal-server (10.0.1.50)
but can only access it through bastion.example.com

Without config (verbose):
  ssh -J user@bastion.example.com user@10.0.1.50

With ~/.ssh/config:
  Host bastion
      HostName bastion.example.com
      User zchen

  Host internal-server
      HostName 10.0.1.50
      User appuser
      ProxyJump bastion

Usage:
  ssh internal-server  (auto-jumps through bastion)

Multi-hop:
  ProxyJump bastion1,bastion2  (chain multiple jumps)
EOF

cat /tmp/proxyjump-example.txt
```

### Step 6: SSH Connection Multiplexing

```bash
cat > /tmp/ssh-mux-config.txt << 'EOF'
# SSH Multiplexing: reuse existing connections
# Add to ~/.ssh/config for faster reconnects

Host *
    ControlMaster auto
    ControlPath ~/.ssh/controlmasters/%r@%h:%p
    ControlPersist 10m

# How it works:
# First connection creates a master socket
# Subsequent connections reuse it (instant connect)

# Setup:
# mkdir -p ~/.ssh/controlmasters
# chmod 700 ~/.ssh/controlmasters
EOF

cat /tmp/ssh-mux-config.txt
mkdir -p ~/.ssh/controlmasters
chmod 700 ~/.ssh/controlmasters
echo "Multiplexing directory created"
```

### Step 7: Test Config Validation

```bash
# ssh -G shows the effective configuration for a host
ssh -F /tmp/demo-ssh-config -G localhost-test 2>/dev/null | head -20
```

```bash
# Check what the default config would use
ssh -G github.com 2>/dev/null | grep -E "^(hostname|user|port|identityfile)" | head -10
```

## ✅ Verification

```bash
# Validate the demo config
echo "=== Config validation ==="
ssh -F /tmp/demo-ssh-config -G localhost-test 2>/dev/null | grep -E "^(hostname|user|port)" | head -5

echo "=== ~/.ssh permissions ==="
ls -ld ~/.ssh
ls -la ~/.ssh/ | head -10

rm /tmp/ssh-config-demo.txt /tmp/demo-ssh-config /tmp/ssh-options-reference.txt /tmp/proxyjump-example.txt /tmp/ssh-mux-config.txt 2>/dev/null
echo "Advanced Lab 4 complete"
```

## 📝 Summary
- `~/.ssh/config` defines host aliases, simplifying `ssh hostname` connections
- `Host *` applies settings to all connections (useful for defaults)
- `HostName` is the actual IP/DNS; `Host` is just your alias
- `ProxyJump bastion` routes connection through a jump host automatically
- `StrictHostKeyChecking accept-new` accepts new keys but rejects changed ones
- `ControlMaster auto` enables connection multiplexing for faster reconnects
- Always `chmod 700 ~/.ssh` and `chmod 600 ~/.ssh/config`
