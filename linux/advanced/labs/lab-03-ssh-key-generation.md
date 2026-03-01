# Lab 3: SSH Key Generation

## 🎯 Objective
Generate SSH key pairs, examine public keys, manage the known_hosts file, and understand key fingerprints.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Advanced Lab 1: Network Configuration

## 🔬 Lab Instructions

### Step 1: Generate an ed25519 Key Pair

```bash
# -t ed25519: modern, secure algorithm
# -N "": no passphrase (for automation)
# -f: specify output file
ssh-keygen -t ed25519 -N "" -f /tmp/testkey -q
ls -la /tmp/testkey*
```

**Expected output:**
```
-rw------- 1 zchen zchen 411 Mar  1 17:00 /tmp/testkey
-rw-r--r-- 1 zchen zchen  96 Mar  1 17:00 /tmp/testkey.pub
```

```bash
# Note the permissions:
# Private key: 600 (owner read/write only — CRITICAL!)
# Public key:  644 (readable by all)
stat /tmp/testkey | grep Access:
```

### Step 2: Examine the Keys

```bash
# View the public key
cat /tmp/testkey.pub
```

**Expected output:**
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA... zchen@hostname
```

```bash
# Public key parts:
# 1. Algorithm: ssh-ed25519
# 2. Base64-encoded key data: AAAAC3NzaC1...
# 3. Comment: user@host

# View private key format (not the actual key - just first line)
head -1 /tmp/testkey
```

**Expected output:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
```

### Step 3: Generate RSA Key (for compatibility)

```bash
ssh-keygen -t rsa -b 4096 -N "" -f /tmp/testkey-rsa -q
ls -la /tmp/testkey-rsa*
cat /tmp/testkey-rsa.pub | cut -c1-40
```

### Step 4: Check Key Fingerprint

```bash
# Fingerprint helps verify key identity
ssh-keygen -l -f /tmp/testkey
```

**Expected output:**
```
256 SHA256:abc123... zchen@hostname (ED25519)
```

```bash
# Fingerprint of RSA key
ssh-keygen -l -f /tmp/testkey-rsa
```

```bash
# Show fingerprint in different formats
ssh-keygen -l -E md5 -f /tmp/testkey
ssh-keygen -l -E sha256 -f /tmp/testkey
```

### Step 5: View Your Existing SSH Keys

```bash
# List any existing keys in ~/.ssh/
ls -la ~/.ssh/ 2>/dev/null || echo "~/.ssh/ does not exist yet"
```

```bash
# Check for common key files
for keytype in id_ed25519 id_rsa id_ecdsa; do
    [[ -f "$HOME/.ssh/$keytype" ]] && echo "Found: $HOME/.ssh/$keytype" || echo "Not found: $HOME/.ssh/$keytype"
done
```

### Step 6: Understanding ~/.ssh/authorized_keys

```bash
# authorized_keys format: each line is one public key
# Syntax: options algorithm key-data comment

cat > /tmp/authorized_keys_example.txt << 'EOF'
# Simple entry (most common)
ssh-ed25519 AAAAC3Nza... user@workstation

# With options (restrict to specific command)
command="/usr/bin/backup.sh",no-pty,no-port-forwarding ssh-ed25519 AAAA... backup@server

# With IP restriction
from="192.168.1.0/24" ssh-ed25519 AAAA... alice@internal
EOF

cat /tmp/authorized_keys_example.txt
```

### Step 7: SSH Key Best Practices

```bash
cat > /tmp/ssh-best-practices.txt << 'EOF'
SSH KEY SECURITY BEST PRACTICES:

1. Use ed25519 (modern) or RSA-4096 (legacy compatibility)
   ssh-keygen -t ed25519 -C "your_email@example.com"

2. Always use a strong passphrase for keys in ~/.ssh/
   (Only skip passphrase for automation/service accounts)

3. Private key permissions MUST be 600
   chmod 600 ~/.ssh/id_ed25519

4. ~/.ssh directory permissions MUST be 700
   chmod 700 ~/.ssh

5. Never share or copy your private key
   Only distribute the .pub file

6. Rotate keys periodically (annually minimum)

7. Use separate keys for different services/environments
EOF

cat /tmp/ssh-best-practices.txt
```

### Step 8: known_hosts File

```bash
# known_hosts stores fingerprints of servers you've connected to
cat ~/.ssh/known_hosts 2>/dev/null | head -5 || echo "No known_hosts file yet"
```

```bash
# View structure explanation
cat > /tmp/known_hosts_example.txt << 'EOF'
# known_hosts format:
# hostname algorithm public-key
# [hostname]:port algorithm public-key  (non-standard ports)

# Example entries:
github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GkZl
[myserver.com]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAA...

# Hashed entries (more secure):
|1|abc123=|xyz789= ssh-ed25519 AAAAC3Nza...
EOF

cat /tmp/known_hosts_example.txt
```

## ✅ Verification

```bash
echo "=== Key files ===" && ls -la /tmp/testkey*
echo "=== ed25519 fingerprint ===" && ssh-keygen -l -f /tmp/testkey
echo "=== RSA fingerprint ===" && ssh-keygen -l -f /tmp/testkey-rsa
echo "=== Public key format ===" && cat /tmp/testkey.pub

rm /tmp/testkey /tmp/testkey.pub /tmp/testkey-rsa /tmp/testkey-rsa.pub 2>/dev/null
rm /tmp/authorized_keys_example.txt /tmp/ssh-best-practices.txt /tmp/known_hosts_example.txt 2>/dev/null
echo "Advanced Lab 3 complete"
```

## 📝 Summary
- `ssh-keygen -t ed25519 -N "" -f keyfile` generates a key pair non-interactively
- Private key (no extension) must be chmod 600; public key (.pub) is shareable
- `ssh-keygen -l -f keyfile` shows the fingerprint for verification
- ed25519 is preferred for new keys; RSA-4096 for compatibility with older systems
- Never share private keys; only distribute `.pub` files
- `~/.ssh/authorized_keys` stores public keys of users allowed to log in
