# Lab 8: UFW Firewall

## 🎯 Objective
Understand UFW (Uncomplicated Firewall) configuration by inspecting status, application profiles, and understanding rule management.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Advanced Lab 7: iptables Basics

## 🔬 Lab Instructions

### Step 1: Check UFW Status

```bash
# UFW status (read-only, no sudo needed for status)
ufw status 2>/dev/null || echo "UFW not available or requires root"
```

```bash
which ufw && echo "UFW is installed" || echo "UFW not installed"
```

```bash
# Check if UFW is active via systemd
systemctl is-active ufw 2>/dev/null || echo "Cannot check UFW status via systemd"
```

### Step 2: UFW Application Profiles

```bash
# List available application profiles
ufw app list 2>/dev/null | head -20 || echo "Cannot list app profiles (may need privileges)"
```

```bash
# View profile locations
ls /etc/ufw/applications.d/ 2>/dev/null | head -10
cat /etc/ufw/applications.d/openssh-server 2>/dev/null || echo "No openssh profile found"
```

### Step 3: UFW Rule Syntax Reference

```bash
cat > /tmp/ufw-syntax.txt << 'EOF'
UFW COMMAND REFERENCE:

Status and Info:
  ufw status                  Show enabled/disabled + rules
  ufw status verbose          Show with interface and policy info
  ufw status numbered         Show rules with numbers
  ufw app list                Show available application profiles
  ufw show raw                Show underlying iptables rules

Enable/Disable (requires root):
  ufw enable                  Enable firewall
  ufw disable                 Disable firewall
  ufw reset                   Reset to defaults (deletes all rules)

Allow Rules (requires root):
  ufw allow ssh               Allow SSH (uses app profile)
  ufw allow 22/tcp            Allow port 22 TCP
  ufw allow 80                Allow port 80 (all protocols)
  ufw allow from 192.168.1.0/24  Allow from subnet
  ufw allow from 10.0.0.5 to any port 5432  Specific IP to port
  ufw allow 8080:8090/tcp     Allow port range

Deny Rules (requires root):
  ufw deny 23                 Block telnet
  ufw deny from 1.2.3.4      Block a specific IP

Delete Rules (requires root):
  ufw delete allow 80         Delete by rule
  ufw delete 5                Delete by number (from ufw status numbered)

Logging (requires root):
  ufw logging on              Enable logging
  ufw logging off             Disable logging
  ufw logging medium          Log level: low|medium|high|full
EOF

cat /tmp/ufw-syntax.txt
```

### Step 4: UFW Default Policies

```bash
cat > /tmp/ufw-policies.txt << 'EOF'
UFW DEFAULT POLICIES:

Ubuntu's default UFW configuration:
  Incoming: DENY (block all inbound traffic unless allowed)
  Outgoing: ALLOW (permit all outbound traffic)
  Forward:  DISABLED

This means:
  - Services only become accessible after you explicitly allow them
  - The system can still initiate outbound connections
  - Routing/forwarding is disabled

Best practices:
  1. Enable UFW immediately after SSH access is confirmed
  2. Always allow SSH BEFORE enabling UFW:
     ufw allow ssh && ufw enable
  3. Enable logging for security monitoring:
     ufw logging on
  4. Use app profiles when available (maintained automatically)

Config files:
  /etc/default/ufw          Main configuration
  /etc/ufw/before.rules     Rules applied before UFW rules
  /etc/ufw/after.rules      Rules applied after UFW rules
  /etc/ufw/user.rules       User-defined rules (managed by ufw)
EOF

cat /tmp/ufw-policies.txt
```

### Step 5: Example Web Server Firewall Config

```bash
cat > /tmp/ufw-webserver-example.txt << 'EOF'
# Example: Web server firewall setup
# Commands shown for reference (require root to execute)

# Reset and start fresh
# ufw reset

# Set default policies
# ufw default deny incoming
# ufw default allow outgoing

# Allow SSH (ALWAYS do this first!)
# ufw allow ssh

# Allow web traffic
# ufw allow 'Nginx Full'    # or 'Apache Full'
# ufw allow 80/tcp
# ufw allow 443/tcp

# Allow specific admin IP for management ports
# ufw allow from 192.168.1.100 to any port 3306  # MySQL from admin only
# ufw allow from 192.168.1.100 to any port 6379  # Redis from admin only

# Enable the firewall
# ufw --force enable

# Verify
# ufw status verbose
EOF

cat /tmp/ufw-webserver-example.txt
```

### Step 6: UFW Logs

```bash
# UFW log location
ls /var/log/ufw.log 2>/dev/null && head -10 /var/log/ufw.log || echo "UFW log not found"
```

```bash
# Or via journalctl
journalctl -k --no-pager 2>/dev/null | grep -i "ufw\|BLOCK\|ALLOW" | head -10 || echo "No UFW journal entries"
```

### Step 7: UFW Application Profile Format

```bash
cat > /tmp/custom-ufw-profile.txt << 'EOF'
# Example custom UFW application profile
# Save to: /etc/ufw/applications.d/myapp

[MyApp]
title=My Application
description=Custom application server
ports=8080,8443/tcp

# After creating, run: ufw app update MyApp
# Then: ufw allow MyApp
EOF

cat /tmp/custom-ufw-profile.txt
```

## ✅ Verification

```bash
echo "=== UFW availability ==="
which ufw 2>/dev/null && echo "UFW installed" || echo "UFW not found"

echo "=== UFW config files ==="
ls /etc/ufw/ 2>/dev/null | head -10

echo "=== UFW app profiles ==="
ls /etc/ufw/applications.d/ 2>/dev/null | head -10

echo "=== UFW log ==="
ls -la /var/log/ufw.log 2>/dev/null || echo "No UFW log file"

rm /tmp/ufw-syntax.txt /tmp/ufw-policies.txt /tmp/ufw-webserver-example.txt /tmp/custom-ufw-profile.txt 2>/dev/null
echo "Advanced Lab 8 complete"
```

## 📝 Summary
- UFW is Ubuntu's simplified firewall frontend that manages iptables rules
- `ufw status` shows current state; `ufw app list` shows available profiles
- Default policy: deny incoming, allow outgoing
- Always allow SSH before enabling UFW to avoid locking yourself out
- `ufw allow ssh` uses the application profile; `ufw allow 22/tcp` is explicit
- Application profiles in `/etc/ufw/applications.d/` define common services
- Enable logging with `ufw logging on` for security monitoring
