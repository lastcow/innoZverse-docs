# Lab 9: fail2ban Intrusion Prevention

## 🎯 Objective
Understand fail2ban configuration by inspecting its status, jail configuration, and log patterns for protecting against brute-force attacks.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Advanced Lab 8: UFW Firewall

## 🔬 Lab Instructions

### Step 1: Check fail2ban Status

```bash
which fail2ban-client 2>/dev/null && echo "fail2ban installed" || echo "fail2ban not installed"
```

```bash
systemctl status fail2ban 2>/dev/null | head -15 || echo "fail2ban service not found"
```

```bash
# Client status (requires fail2ban to be running)
fail2ban-client status 2>/dev/null | head -10 || echo "Cannot get fail2ban status"
```

### Step 2: Understand fail2ban Architecture

```bash
cat > /tmp/fail2ban-concepts.txt << 'EOF'
FAIL2BAN ARCHITECTURE:

COMPONENTS:
  fail2ban-server  Daemon that monitors logs and bans IPs
  fail2ban-client  CLI interface to control the server
  jails            Rules that define what to monitor
  filters          Regex patterns to detect attacks
  actions          What to do when a filter matches

HOW IT WORKS:
  1. Monitor log files (auth.log, nginx/access.log, etc.)
  2. Count failed attempts from each IP
  3. When threshold exceeded → ban the IP
  4. After bantime expires → unban automatically

CONFIGURATION FILES:
  /etc/fail2ban/fail2ban.conf      Main config (don't edit)
  /etc/fail2ban/jail.conf          Default jails (don't edit)
  /etc/fail2ban/jail.local         Your customizations (create this)
  /etc/fail2ban/filter.d/          Regex filter files
  /etc/fail2ban/action.d/          Ban action scripts
EOF

cat /tmp/fail2ban-concepts.txt
```

### Step 3: View Configuration Files

```bash
# Check if fail2ban is installed
ls /etc/fail2ban/ 2>/dev/null | head -15 || echo "fail2ban config not found"
```

```bash
# View the default jail.conf (if installed)
head -50 /etc/fail2ban/jail.conf 2>/dev/null | head -40 || echo "jail.conf not found"
```

```bash
# View filter examples
ls /etc/fail2ban/filter.d/ 2>/dev/null | head -20 || echo "filter.d not found"
```

### Step 4: jail.local Configuration

```bash
cat > /tmp/jail-local-example.txt << 'EOF'
# /etc/fail2ban/jail.local
# This file OVERRIDES settings in jail.conf
# Create this file, never modify jail.conf

[DEFAULT]
# Ban hosts for 1 hour after 5 failures within 10 minutes
bantime  = 3600
findtime = 600
maxretry = 5

# Email notification (optional)
# destemail = admin@example.com
# sendername = Fail2Ban
# mta = sendmail
# action = %(action_mwl)s

# Default ban action: UFW
banaction = ufw

[sshd]
enabled  = true
port     = ssh
logpath  = %(sshd_log)s
maxretry = 3
bantime  = 86400   # 24 hours for SSH

[nginx-http-auth]
enabled  = true
port     = http,https
logpath  = /var/log/nginx/error.log
maxretry = 5

[nginx-limit-req]
enabled  = true
port     = http,https
logpath  = /var/log/nginx/error.log
maxretry = 10

[postfix]
enabled = false
port    = smtp,465,submission
logpath = /var/log/mail.log
EOF

cat /tmp/jail-local-example.txt
```

### Step 5: SSH fail2ban Filter

```bash
# View the SSH filter (if fail2ban is installed)
cat /etc/fail2ban/filter.d/sshd.conf 2>/dev/null | head -40 || cat > /tmp/sshd-filter-example.txt << 'EOF'
# Example: /etc/fail2ban/filter.d/sshd.conf
# Detects failed SSH login attempts

[INCLUDES]
before = common.conf

[Definition]
_daemon = sshd

failregex = ^%(__prefix_line)s(?:error: PAM: )?[aA]uthentication (?:failure|error|failed) for .* from <HOST>( via \S+)?\s*$
            ^%(__prefix_line)s(?:error: PAM: )?User not known to the underlying authentication module for .* from <HOST>\s*$
            ^%(__prefix_line)sInvalid user .+ from <HOST>\s*$

ignoreregex =

[Init]
# The number of 'Failed' login attempts, then also ban.
maxlines = 1
EOF
cat /tmp/sshd-filter-example.txt
```

### Step 6: fail2ban Management Commands

```bash
cat > /tmp/fail2ban-commands.txt << 'EOF'
FAIL2BAN MANAGEMENT (requires root):

Status:
  fail2ban-client status              List all jails
  fail2ban-client status sshd         Status of specific jail
  fail2ban-client get sshd bantime    Get setting value

Manual Ban/Unban:
  fail2ban-client set sshd banip 1.2.3.4      Ban an IP
  fail2ban-client set sshd unbanip 1.2.3.4    Unban an IP

Testing Filters:
  fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf

Reload Configuration:
  fail2ban-client reload
  fail2ban-client reload sshd

View Banned IPs:
  fail2ban-client status sshd | grep "Banned IP"
  iptables -n -L f2b-sshd 2>/dev/null

Log Analysis:
  grep "Ban\|Unban\|Found" /var/log/fail2ban.log | tail -20
EOF

cat /tmp/fail2ban-commands.txt
```

### Step 7: Monitor Current Brute Force Attempts

```bash
# See recent SSH failures from system logs
journalctl --no-pager -n 50 2>/dev/null | grep -E "Failed password|Invalid user|authentication failure" | head -10
```

```bash
# Count failures by IP (from journal)
journalctl --no-pager --since "1 hour ago" 2>/dev/null | \
    grep -E "Failed password|Invalid user" | \
    grep -Eo "from [0-9.]+" | sort | uniq -c | sort -rn | head -10
```

## ✅ Verification

```bash
echo "=== fail2ban installed ==="
which fail2ban-client 2>/dev/null && echo "YES" || echo "NO"

echo "=== fail2ban config ==="
ls /etc/fail2ban/ 2>/dev/null | wc -l

echo "=== Recent SSH failures ==="
journalctl --no-pager --since "1 hour ago" 2>/dev/null | grep -c "Failed password" || echo "0"

rm /tmp/fail2ban-concepts.txt /tmp/jail-local-example.txt /tmp/fail2ban-commands.txt /tmp/sshd-filter-example.txt 2>/dev/null
echo "Advanced Lab 9 complete"
```

## 📝 Summary
- fail2ban monitors log files and bans IPs that exceed failed attempt thresholds
- `jail.local` overrides `jail.conf` — always edit `jail.local`, never `jail.conf`
- Key settings: `bantime` (ban duration), `findtime` (window), `maxretry` (threshold)
- `fail2ban-client status sshd` shows banned IPs and statistics
- Filters in `/etc/fail2ban/filter.d/` are regex patterns matching attack signatures
- `fail2ban-regex logfile filter` tests whether a filter matches log entries
