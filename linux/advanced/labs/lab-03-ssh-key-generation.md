# Lab 3: SSH Key Generation and Setup

## 🎯 Objective
Generate SSH key pairs, copy public keys to remote servers, and understand the `authorized_keys` mechanism for passwordless authentication.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- SSH installed (`openssh-client`, `openssh-server`)

## 🔬 Lab Instructions

### Step 1: Check SSH Installation
```bash
ssh -V
# OpenSSH_8.9p1 Ubuntu-3ubuntu0.6, OpenSSL 3.0.2

which ssh-keygen
# /usr/bin/ssh-keygen

ls ~/.ssh/ 2>/dev/null || echo "~/.ssh does not exist yet"
```

### Step 2: Generate an Ed25519 Key Pair (Recommended)
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# Generating public/private ed25519 key pair.
# Enter file in which to save the key (/home/ubuntu/.ssh/id_ed25519):  [press Enter]
# Enter passphrase (empty for no passphrase): [enter passphrase or leave empty]
# Enter same passphrase again:
# Your identification has been saved in /home/ubuntu/.ssh/id_ed25519
# Your public key has been saved in /home/ubuntu/.ssh/id_ed25519.pub
# The key fingerprint is: SHA256:xxxxx your_email@example.com
# The key's randomart image is: ...
```

### Step 3: Generate an RSA 4096-bit Key (Alternative)
```bash
ssh-keygen -t rsa -b 4096 -C "backup_key" -f ~/.ssh/id_rsa_backup
# Creates ~/.ssh/id_rsa_backup and ~/.ssh/id_rsa_backup.pub
```

### Step 4: Inspect the Generated Keys
```bash
ls -la ~/.ssh/
# drwx------ 2 ubuntu ubuntu 4096 Mar  1 06:01 .
# -rw------- 1 ubuntu ubuntu  419 Mar  1 06:01 id_ed25519      (private)
# -rw-r--r-- 1 ubuntu ubuntu  104 Mar  1 06:01 id_ed25519.pub  (public)

# View the public key
cat ~/.ssh/id_ed25519.pub
# ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... your_email@example.com

# View key fingerprint
ssh-keygen -lf ~/.ssh/id_ed25519.pub
# 256 SHA256:xxxxxxxxxxxxx your_email@example.com (ED25519)
```

### Step 5: Understand Key Permissions
```bash
# Correct permissions are critical
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

ls -la ~/.ssh/
# drwx------  (700 - directory: owner rwx only)
# -rw-------  (600 - private key: owner read/write only)
# -rw-r--r--  (644 - public key: world readable)
```

### Step 6: Set Up authorized_keys (Local Simulation)
```bash
# authorized_keys stores public keys of trusted clients
mkdir -p ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Add your own public key (for local testing)
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/authorized_keys
# ssh-ed25519 AAAAC3NzaC1... your_email@example.com
```

### Step 7: ssh-copy-id — Copy Key to Remote Server
```bash
# Syntax: ssh-copy-id -i ~/.ssh/id_ed25519.pub user@remote_host
# This copies your public key to remote's ~/.ssh/authorized_keys

# Example (replace with your actual remote host):
# ssh-copy-id -i ~/.ssh/id_ed25519.pub ubuntu@192.168.1.100

# Manual equivalent:
cat ~/.ssh/id_ed25519.pub | ssh user@host "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
echo "Public key copy method demonstrated"
```

### Step 8: Test Key-Based Authentication
```bash
# After copying key to remote, connect without password:
# ssh ubuntu@192.168.1.100
# (should connect without prompting for password)

# Test local SSH with key (if SSH server is running locally)
if systemctl is-active --quiet ssh 2>/dev/null || systemctl is-active --quiet sshd 2>/dev/null; then
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_ed25519 localhost "echo 'Key auth works: $(hostname)'"
else
    echo "SSH server not running locally — test against a remote host"
fi
```

### Step 9: Use ssh-agent to Cache Passphrase
```bash
# Start the agent
eval $(ssh-agent -s)
# Agent pid 12345

# Add key to agent (prompts for passphrase once)
ssh-add ~/.ssh/id_ed25519
# Identity added: /home/ubuntu/.ssh/id_ed25519

# List loaded keys
ssh-add -l
# 256 SHA256:xxxxx your_email@example.com (ED25519)

# Stop the agent when done
ssh-agent -k
# Agent pid 12345 killed
```

### Step 10: Revoke Access by Removing a Key
```bash
# To revoke access from a remote server:
# 1. SSH into the remote server
# 2. Edit ~/.ssh/authorized_keys
# 3. Remove the line containing that public key

# View authorized_keys
cat ~/.ssh/authorized_keys

# Count authorized keys
wc -l ~/.ssh/authorized_keys
# 1 /home/ubuntu/.ssh/authorized_keys

# Good security practice: audit authorized_keys regularly
echo "Audit: $(wc -l < ~/.ssh/authorized_keys) key(s) authorized"
```

## ✅ Verification
```bash
ls -la ~/.ssh/id_ed25519* 2>/dev/null
# -rw------- ... id_ed25519
# -rw-r--r-- ... id_ed25519.pub

ssh-keygen -lf ~/.ssh/id_ed25519.pub
# 256 SHA256:... (ED25519)
```

## 📝 Summary
- `ssh-keygen -t ed25519` generates a modern, secure key pair
- Private key (`id_ed25519`) must be `600`; public key (`id_ed25519.pub`) can be `644`
- `ssh-copy-id` copies your public key to a remote server's `authorized_keys`
- `authorized_keys` (mode `600`) lists trusted public keys for passwordless login
- `ssh-agent` caches your passphrase so you don't re-enter it every connection
