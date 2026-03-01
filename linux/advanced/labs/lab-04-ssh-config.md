# Lab 4: SSH Client Configuration

## 🎯 Objective
Configure `~/.ssh/config` to create connection aliases, set per-host options, use ProxyJump for bastion hosts, and simplify complex SSH workflows.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Lab 3 (SSH Key Generation)

## 🔬 Lab Instructions

### Step 1: Understand the SSH Config File
```bash
# ~/.ssh/config is read by the ssh client before connecting
# Format: Host alias -> options
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ls -la ~/.ssh/config 2>/dev/null || echo "Config file doesn't exist yet"
```

### Step 2: Create a Basic SSH Config Entry
```bash
cat > ~/.ssh/config << 'EOF'
# Basic host alias
Host webserver
    HostName 192.168.1.100
    User ubuntu
    Port 22
    IdentityFile ~/.ssh/id_ed25519
EOF
chmod 600 ~/.ssh/config

# Now connect with alias instead of full command:
# ssh webserver
# (equivalent to: ssh -i ~/.ssh/id_ed25519 -p 22 ubuntu@192.168.1.100)
echo "Config created"
```

### Step 3: Add Multiple Hosts
```bash
cat >> ~/.ssh/config << 'EOF'

Host db-primary
    HostName 192.168.1.200
    User dbadmin
    Port 2222
    IdentityFile ~/.ssh/id_ed25519
    ConnectTimeout 10

Host staging
    HostName staging.example.com
    User deploy
    IdentityFile ~/.ssh/id_rsa_backup
    ForwardAgent yes
EOF

cat ~/.ssh/config
```

### Step 4: Global Default Settings
```bash
cat >> ~/.ssh/config << 'EOF'

# Apply to all hosts (must come last or use Host *)
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    ConnectTimeout 10
    AddKeysToAgent yes
    IdentityFile ~/.ssh/id_ed25519
EOF

# ServerAliveInterval: send keepalive every 60 seconds
# ServerAliveCountMax: drop after 3 missed keepalives
# AddKeysToAgent: auto-add to ssh-agent on use
```

### Step 5: SSH Config Option Reference
```bash
# Common SSH config options:
cat << 'EOF'
Host           - alias for the connection
HostName       - actual hostname or IP
User           - username to connect as
Port           - SSH port (default 22)
IdentityFile   - path to private key
ForwardAgent   - forward your ssh-agent (for chained connections)
StrictHostKeyChecking - yes/no/ask for host key verification
ConnectTimeout - seconds before timeout
ServerAliveInterval - keepalive interval in seconds
Compression    - yes to compress connection
EOF
```

### Step 6: ProxyJump — Jump Through a Bastion Host
```bash
# Scenario: access internal server through a bastion/jump host
# bastion.example.com -> internal-server (192.168.10.50)

cat >> ~/.ssh/config << 'EOF'

Host bastion
    HostName bastion.example.com
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519

Host internal-server
    HostName 192.168.10.50
    User ubuntu
    ProxyJump bastion
    IdentityFile ~/.ssh/id_ed25519
EOF

# Connect to internal-server through bastion with one command:
# ssh internal-server
# (OpenSSH will automatically connect through bastion first)
echo "ProxyJump config added"
```

### Step 7: Disable Host Key Checking for Lab/Test Hosts
```bash
cat >> ~/.ssh/config << 'EOF'

# For disposable test/lab hosts only — never in production!
Host 192.168.99.*
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    LogLevel QUIET
EOF

# WARNING: Disabling StrictHostKeyChecking removes MITM protection
# Only use for known test environments
```

### Step 8: SSH Config for Multiplexing (Faster Connections)
```bash
cat >> ~/.ssh/config << 'EOF'

Host fasthost
    HostName 192.168.1.100
    User ubuntu
    ControlMaster auto
    ControlPath ~/.ssh/control/%r@%h:%p
    ControlPersist 10m
EOF

mkdir -p ~/.ssh/control
chmod 700 ~/.ssh/control

# First connection establishes the master socket
# Subsequent connections reuse it — much faster!
# ssh fasthost ls    # instant reconnect within 10 minutes
```

### Step 9: Verify Config Syntax
```bash
# Test config without connecting
ssh -G webserver 2>/dev/null | grep -E '^(hostname|user|port|identityfile)'
# hostname 192.168.1.100
# user ubuntu
# port 22
# identityfile /home/ubuntu/.ssh/id_ed25519

# Count configured hosts
grep '^Host ' ~/.ssh/config | grep -v '\*'
# Host webserver
# Host db-primary
# Host staging
# Host bastion
# Host internal-server
```

### Step 10: Backup and Secure the Config
```bash
# Always secure config file
chmod 600 ~/.ssh/config

# Backup
cp ~/.ssh/config ~/.ssh/config.bak
echo "Config backed up to ~/.ssh/config.bak"

# View final config
echo "=== Final SSH Config ==="
cat ~/.ssh/config
echo ""
echo "Hosts defined:"
grep '^Host ' ~/.ssh/config
```

## ✅ Verification
```bash
chmod 600 ~/.ssh/config
ssh -G webserver | grep hostname
# hostname 192.168.1.100

ls -la ~/.ssh/config
# -rw------- ... /home/ubuntu/.ssh/config
```

## 📝 Summary
- `~/.ssh/config` stores per-host SSH settings with `Host alias` blocks
- Options: `HostName`, `User`, `Port`, `IdentityFile`, `ProxyJump`, `ForwardAgent`
- `Host *` at the end applies defaults to all connections
- `ProxyJump bastion` enables transparent access through jump hosts
- `ControlMaster`/`ControlPath` multiplexing speeds up repeated connections
- Config file must be mode `600` or SSH will refuse to use it
