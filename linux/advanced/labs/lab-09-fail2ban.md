# Lab 9: fail2ban — Brute Force Protection

## 🎯 Objective
Install and configure fail2ban to protect SSH from brute force attacks using custom jail settings, monitor ban status, and understand the jail.local configuration.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access with sudo privileges
- SSH service running
- UFW or iptables active (Lab 7 or 8)

## 🔬 Lab Instructions

### Step 1: Install fail2ban
```bash
sudo apt update && sudo apt install -y fail2ban
systemctl status fail2ban
# ● fail2ban.service - Fail2Ban Service
#    Active: active (running)
```

### Step 2: Understand Configuration Files
```bash
ls /etc/fail2ban/
# action.d/  fail2ban.conf  filter.d/  jail.conf  jail.d/  paths-common.conf

# jail.conf = default config (do NOT edit — overwritten on upgrade)
# jail.local = your customizations (create this file)
# jail.d/*.conf = per-jail overrides

head -60 /etc/fail2ban/jail.conf
# [DEFAULT]
# bantime  = 10m
# findtime = 10m
# maxretry = 5
```

### Step 3: Create jail.local
```bash
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo chmod 640 /etc/fail2ban/jail.local

# Or create a minimal override file:
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# Ban duration
bantime  = 1h
# Time window to count failures
findtime = 10m
# Max failures before ban
maxretry = 5
# Whitelist (never ban these IPs)
ignoreip = 127.0.0.1/8 ::1

# Email notifications (optional)
# destemail = admin@example.com
# sender = fail2ban@example.com

[sshd]
enabled  = true
port     = ssh
logpath  = %(sshd_log)s
backend  = %(sshd_backend)s
maxretry = 3
bantime  = 2h
EOF
```

### Step 4: Restart fail2ban and Verify
```bash
sudo systemctl restart fail2ban
sudo systemctl status fail2ban
# ● fail2ban.service - Fail2Ban Service
#    Active: active (running)

# Check fail2ban log
sudo tail -20 /var/log/fail2ban.log
# 2026-03-01 06:01:00,123 fail2ban.jail [INFO] Creating new jail 'sshd'
# 2026-03-01 06:01:00,456 fail2ban.jail [INFO] Jail 'sshd' started
```

### Step 5: Check fail2ban Status
```bash
# List all jails
sudo fail2ban-client status
# Status
# |- Number of jail:      1
# `- Jail list:   sshd

# Detailed jail status
sudo fail2ban-client status sshd
# Status for the jail: sshd
# |- Filter
# |  |- Currently failed: 0
# |  |- Total failed:     0
# |  `- File list:        /var/log/auth.log
# `- Actions
#    |- Currently banned: 0
#    |- Total banned:     0
#    `- Banned IP list:
```

### Step 6: View fail2ban Filter for SSH
```bash
cat /etc/fail2ban/filter.d/sshd.conf | head -30
# [INCLUDES]
# before = common.conf
#
# [Definition]
# failregex = ^%(__prefix_line)s(?:error: PAM: )?[aA]uthentication (?:failure|error|failed)...
#
# The filter defines what log pattern constitutes a "failed attempt"

# Test a filter against a log file
sudo fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf 2>/dev/null | tail -10
# Results:
# Lines:   120 lines, 0 ignored, 8 matched, 112 missed
```

### Step 7: Manually Ban and Unban an IP
```bash
# Manually ban an IP
sudo fail2ban-client set sshd banip 192.0.2.200
# 1

# Verify ban
sudo fail2ban-client status sshd | grep "Banned IP"
# `- Banned IP list:   192.0.2.200

# Check iptables rule created by fail2ban
sudo iptables -L f2b-sshd -n 2>/dev/null || sudo iptables -L INPUT -n | grep 192.0.2.200

# Manually unban
sudo fail2ban-client set sshd unbanip 192.0.2.200
# 1

sudo fail2ban-client status sshd | grep "Banned IP"
# `- Banned IP list:   (empty)
```

### Step 8: Configure Jail for Other Services
```bash
sudo tee -a /etc/fail2ban/jail.local << 'EOF'

[nginx-http-auth]
enabled  = true
port     = http,https
logpath  = /var/log/nginx/error.log
maxretry = 6

[postfix]
enabled  = false
port     = smtp,465,submission
logpath  = /var/log/mail.log
maxretry = 3
EOF

sudo systemctl reload fail2ban
sudo fail2ban-client status
# Status
# |- Number of jail: 2
# `- Jail list: nginx-http-auth, sshd
```

### Step 9: Monitor Bans in Real Time
```bash
# Follow fail2ban log
sudo tail -f /var/log/fail2ban.log &
TAIL_PID=$!
sleep 2
kill $TAIL_PID 2>/dev/null

# Show recently banned IPs with timestamps
sudo grep "Ban" /var/log/fail2ban.log | tail -20
# 2026-03-01 06:05:12,345 fail2ban.actions [NOTICE] [sshd] Ban 198.51.100.42

# Count total bans today
sudo grep -c "Ban " /var/log/fail2ban.log 2>/dev/null || echo "0"
```

### Step 10: Create a Ban Status Report Script
```bash
cat > ~/fail2ban_report.sh << 'EOF'
#!/bin/bash
echo "=== fail2ban Status Report: $(date) ==="
echo ""

if ! systemctl is-active --quiet fail2ban; then
    echo "ALERT: fail2ban is NOT running!"
    exit 1
fi

echo "Service: $(systemctl is-active fail2ban)"
echo ""

# List all jails and their status
for jail in $(sudo fail2ban-client status | grep 'Jail list' | sed 's/.*://;s/,//g'); do
    echo "--- Jail: $jail ---"
    sudo fail2ban-client status "$jail" | grep -E '(Currently|Total|Banned IP)'
    echo ""
done

echo "Recent bans (last 10):"
sudo grep "Ban " /var/log/fail2ban.log | tail -10 | awk '{print "  " $1, $2, $NF}'
EOF
chmod +x ~/fail2ban_report.sh
sudo ~/fail2ban_report.sh
```

## ✅ Verification
```bash
sudo fail2ban-client status sshd
# Status for the jail: sshd
# |- Filter ... Currently failed: 0
# `- Actions ... Currently banned: 0

sudo systemctl is-active fail2ban
# active
```

## 📝 Summary
- `jail.local` overrides `jail.conf` — always customize in `jail.local`
- Key settings: `bantime`, `findtime`, `maxretry`, `ignoreip`
- `fail2ban-client status JAIL` shows current ban counts and IP list
- `fail2ban-client set JAIL banip/unbanip IP` manages bans manually
- fail2ban works by adding iptables rules when thresholds are exceeded
- Filter files in `/etc/fail2ban/filter.d/` define log patterns to match
