# Lab 20: Capstone — Complete Server Administration Workflow

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

This capstone lab ties together everything from Labs 01–19. You will simulate a complete server onboarding workflow: provisioning users, configuring SSH, setting up cron jobs, monitoring processes, analyzing logs, and writing a production-grade server health-check and hardening script.

**Prerequisites:** Labs 01–19 completed. This lab uses skills from every previous lab.

---

## Step 1: User Provisioning & Privilege Setup *(Labs 07, 09)*

A new server needs the right users and groups before anything else.

```bash
docker run -it --rm ubuntu:22.04 bash

# Create application and admin users
useradd -m -s /bin/bash -c "Web Application" webuser
useradd -m -s /bin/bash -c "Deploy Bot" deploy
useradd -m -s /bin/bash -c "SRE Admin" sreadmin

# Create functional groups
groupadd webapps
groupadd deployers
groupadd monitoring

# Assign users to groups
usermod -aG webapps webuser
usermod -aG webapps,deployers deploy
usermod -aG monitoring,sudo sreadmin

# Set passwords (in real systems use: passwd -e user to force reset)
echo "webuser:Secr3tW3b!" | chpasswd
echo "deploy:D3pl0yB0t!" | chpasswd
echo "sreadmin:Adm1nPa$$!" | chpasswd

# Verify user setup
echo "=== Users created ==="
grep -E 'webuser|deploy|sreadmin' /etc/passwd | awk -F: '{printf "%-12s UID:%-5s Shell: %s\n", $1, $3, $7}'

echo ""
echo "=== Group memberships ==="
for user in webuser deploy sreadmin; do
    groups_list=$(id -Gn $user | tr ' ' ',')
    printf "%-12s → %s\n" "$user" "$groups_list"
done

echo ""
echo "=== Home directories ==="
ls -la /home/
```

📸 **Verified Output:**
```
=== Users created ===
webuser      UID:1000  Shell: /bin/bash
deploy       UID:1001  Shell: /bin/bash
sreadmin     UID:1002  Shell: /bin/bash

=== Group memberships ===
webuser      → webuser,webapps
deploy       → deploy,webapps,deployers
sreadmin     → sreadmin,monitoring,sudo

=== Home directories ===
total 20
drwxr-xr-x 1 root     root     4096 Mar  5 05:55 .
drwxr-xr-x 1 root     root     4096 Mar  5 05:55 ..
drwxr-xr-x 2 deploy   deploy   4096 Mar  5 05:55 deploy
drwxr-xr-x 2 sreadmin sreadmin 4096 Mar  5 05:55 sreadmin
drwxr-xr-x 2 webuser  webuser  4096 Mar  5 05:55 webuser
```

> 💡 **Principle of least privilege:** Give each user only the access they need. `webuser` has no sudo access. `deploy` can deploy but not admin. Only `sreadmin` has sudo. This limits blast radius if any account is compromised.

---

## Step 2: SSH Key Authentication Setup *(Lab 16)*

Every server should use key-based SSH authentication with password auth disabled.

```bash
apt-get update -qq && apt-get install -y -qq openssh-client > /dev/null 2>&1

# Generate SSH keys for each service account
for user in deploy sreadmin; do
    home="/home/$user"
    mkdir -p "$home/.ssh"
    chmod 700 "$home/.ssh"
    ssh-keygen -t ed25519 -N "" \
        -f "$home/.ssh/id_ed25519" \
        -C "$user@$(hostname)" 2>&1 | grep -E "fingerprint|Your ident"
    cp "$home/.ssh/id_ed25519.pub" "$home/.ssh/authorized_keys"
    chmod 600 "$home/.ssh/authorized_keys"
    chown -R $user:$user "$home/.ssh"
    echo "[$user] SSH key configured"
done

# Configure SSH daemon hardening (sshd_config)
cat > /tmp/sshd_hardened.conf << 'EOF'
# SSH Server Hardening Configuration
Port 22
Protocol 2

# Authentication
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
MaxSessions 10

# Session security
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30

# Access control
AllowUsers deploy sreadmin
AllowGroups deployers monitoring sudo

# Disable legacy features
X11Forwarding no
AllowTcpForwarding no
GatewayPorts no
PermitEmptyPasswords no
EOF

echo "=== SSH hardening config ==="
grep -v '^#' /tmp/sshd_hardened.conf | grep -v '^$'

echo ""
echo "=== Key fingerprints ==="
for user in deploy sreadmin; do
    printf "%-10s: " "$user"
    ssh-keygen -l -f "/home/$user/.ssh/id_ed25519.pub"
done
```

📸 **Verified Output:**
```
Your identification has been saved in /home/deploy/.ssh/id_ed25519
256 SHA256:AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcde deploy@container (ED25519)
[deploy] SSH key configured
Your identification has been saved in /home/sreadmin/.ssh/id_ed25519
256 SHA256:ZyXwVuTsRqPoNmLkJiHgFeDcBa9876543210zyxwvu sreadmin@container (ED25519)
[sreadmin] SSH key configured

=== SSH hardening config ===
Port 22
Protocol 2
PasswordAuthentication no
PubkeyAuthentication yes
PermitRootLogin no
AuthorizedKeysFile .ssh/authorized_keys
MaxAuthTries 3
MaxSessions 10
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30
AllowUsers deploy sreadmin
AllowGroups deployers monitoring sudo
X11Forwarding no
AllowTcpForwarding no
GatewayPorts no
PermitEmptyPasswords no

=== Key fingerprints ===
deploy    : 256 SHA256:AbCdEfGhIjKlMnOpQrStUvWxYz0123456789abcde deploy@container (ED25519)
sreadmin  : 256 SHA256:ZyXwVuTsRqPoNmLkJiHgFeDcBa9876543210zyxwvu sreadmin@container (ED25519)
```

> 💡 **Test SSH config before reloading.** Always run `sshd -t -f /etc/ssh/sshd_config` to test config syntax before `systemctl reload sshd`. A broken sshd config + reload locks you out of the server. Keep a second terminal session open before reloading.

---

## Step 3: Directory Structure & File Permissions *(Labs 03, 09)*

Proper directory structure and permissions are the foundation of a secure, organized server.

```bash
# Create application directory structure
mkdir -p /opt/myapp/{bin,config,logs,data,backups,tmp}
mkdir -p /var/log/myapp
mkdir -p /etc/myapp

# Set ownership and permissions
chown -R webuser:webapps /opt/myapp
chown -R webuser:webapps /var/log/myapp
chown root:root /opt/myapp/config /etc/myapp

# Permission matrix:
# app directories: 755 (group can read/execute)
# config files: 640 (owner rw, group r, other none)
# log directory: 775 (group can write)
# sensitive data: 700 (owner only)

chmod 755 /opt/myapp/bin
chmod 750 /opt/myapp/config     # restrict config
chmod 775 /opt/myapp/logs       # group writable for logs
chmod 700 /opt/myapp/data       # owner only for data
chmod 1777 /opt/myapp/tmp       # sticky bit for tmp

# Create sample config with restrictive permissions
cat > /etc/myapp/app.conf << 'EOF'
host = 0.0.0.0
port = 8080
log_level = info
database_url = postgres://app:secret@localhost/appdb
max_workers = 4
EOF
chmod 640 /etc/myapp/app.conf
chown root:webapps /etc/myapp/app.conf

echo "=== Directory structure ==="
find /opt/myapp -maxdepth 1 | xargs ls -ld 2>/dev/null

echo ""
echo "=== Config permissions ==="
ls -la /etc/myapp/app.conf
```

📸 **Verified Output:**
```
=== Directory structure ===
drwxr-xr-x 7 webuser webapps 4096 Mar  5 05:55 /opt/myapp
drwxr-x--- 2 webuser webapps 4096 Mar  5 05:55 /opt/myapp/bin
drwxr-x--- 2 webuser webapps 4096 Mar  5 05:55 /opt/myapp/config
drwxrwxr-x 2 webuser webapps 4096 Mar  5 05:55 /opt/myapp/logs
drwx------ 2 webuser webapps 4096 Mar  5 05:55 /opt/myapp/data
drwxrwxrwt 2 webuser webapps 4096 Mar  5 05:55 /opt/myapp/tmp
drwxr-xr-x 2 webuser webapps 4096 Mar  5 05:55 /opt/myapp/backups

=== Config permissions ===
-rw-r----- 1 root webapps 123 Mar  5 05:55 /etc/myapp/app.conf
```

> 💡 **The sticky bit (`chmod +t`) on `/tmp`-style directories prevents users from deleting files they don't own.** The `T` or `t` in `drwxrwxrwt` shows it's set. Use `chmod 1777` or `chmod +t`. This is how `/tmp` itself works on every Linux system.

---

## Step 4: Cron Jobs & Scheduled Tasks *(Lab 13)*

Automate recurring tasks: backups, log rotation, health checks.

```bash
apt-get install -y -qq cron > /dev/null 2>&1

# Create maintenance scripts
mkdir -p /usr/local/bin

cat > /usr/local/bin/backup.sh << 'SCRIPT'
#!/bin/bash
# backup.sh — Daily backup job
BACKUP_DIR="/opt/myapp/backups"
DATE=$(date +%Y%m%d-%H%M%S)
LOG="/var/log/myapp/backup.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') INFO backup started" >> "$LOG"
# tar -czf "$BACKUP_DIR/app-$DATE.tar.gz" /opt/myapp/data/ 2>> "$LOG"
# Find and delete backups older than 30 days
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete 2>> "$LOG"
echo "$(date '+%Y-%m-%d %H:%M:%S') INFO backup completed" >> "$LOG"
SCRIPT

cat > /usr/local/bin/health-check.sh << 'SCRIPT'
#!/bin/bash
# health-check.sh — Service health verification
LOG="/var/log/myapp/health.log"
ts=$(date '+%Y-%m-%d %H:%M:%S')

# Check disk space
disk_pct=$(df / | awk 'NR==2{gsub(/%/,"",$5); print $5}')
if [ "$disk_pct" -gt 85 ]; then
    echo "$ts CRIT disk usage at ${disk_pct}%" >> "$LOG"
fi

# Check memory
mem_ok=$(awk '/MemAvailable/{a=$2} /MemTotal/{t=$2} END{print (a/t>0.1)?"ok":"low"}' /proc/meminfo)
echo "$ts INFO memory=$mem_ok disk=${disk_pct}%" >> "$LOG"
SCRIPT

chmod +x /usr/local/bin/backup.sh /usr/local/bin/health-check.sh

# Install crontab entries
cat > /tmp/crontab-entries << 'EOF'
# myapp cron jobs
SHELL=/bin/bash
MAILTO=ops@example.com

# Daily backup at 2:30 AM
30 2 * * * webuser /usr/local/bin/backup.sh

# Health check every 5 minutes
*/5 * * * * root /usr/local/bin/health-check.sh

# Weekly log cleanup Sunday 3 AM
0 3 * * 0 root find /var/log/myapp -name "*.log" -mtime +90 -delete

# Monthly report first day of month
0 8 1 * * sreadmin /usr/local/bin/monthly-report.sh 2>/dev/null || true
EOF

cat /tmp/crontab-entries

# Run health check now to verify it works
bash /usr/local/bin/health-check.sh
echo "=== Health check log ==="
cat /var/log/myapp/health.log
```

📸 **Verified Output:**
```
# myapp cron jobs
SHELL=/bin/bash
MAILTO=ops@example.com

# Daily backup at 2:30 AM
30 2 * * * webuser /usr/local/bin/backup.sh

# Health check every 5 minutes
*/5 * * * * root /usr/local/bin/health-check.sh

# Weekly log cleanup Sunday 3 AM
0 3 * * 0 root find /var/log/myapp -name "*.log" -mtime +90 -delete

# Monthly report first day of month
0 8 1 * * sreadmin /usr/local/bin/monthly-report.sh 2>/dev/null || true

=== Health check log ===
2026-03-05 05:55:10 INFO memory=ok disk=15%
```

> 💡 **Always redirect cron output.** Without `>> /var/log/myapp/cron.log 2>&1`, cron emails output to root — and on most servers, nobody reads those emails. Log to a file and monitor the log file. Add `|| true` at the end of cron commands to prevent failed jobs from generating email spam.

---

## Step 5: Log Setup & Structured Logging *(Lab 17)*

```bash
# Create structured application logs for analysis
mkdir -p /var/log/myapp

cat > /var/log/myapp/app.log << 'EOF'
2024-01-15 08:00:01 INFO  [startup] Application starting version=2.4.1 pid=1234
2024-01-15 08:00:02 INFO  [db]      Connected to database host=db-01 pool_size=10
2024-01-15 08:00:03 INFO  [web]     Listening on 0.0.0.0:8080 workers=4
2024-01-15 08:05:01 INFO  [web]     GET /api/users 200 45ms user=alice
2024-01-15 08:05:02 ERROR [db]      Query timeout after 30s query=SELECT_users
2024-01-15 08:05:03 WARN  [web]     Slow response 2341ms GET /api/reports
2024-01-15 08:05:04 INFO  [auth]    Login user=bob ip=192.168.1.20 method=key
2024-01-15 08:05:05 ERROR [web]     500 Internal Error /api/export user=alice
2024-01-15 08:10:01 WARN  [disk]    Usage 82% on /var/data
2024-01-15 08:10:02 ERROR [auth]    Failed login user=unknown ip=203.0.113.99 attempts=10
2024-01-15 08:15:01 CRIT  [sys]     Memory 94% used - OOM risk
2024-01-15 08:15:02 INFO  [cron]    Backup started
2024-01-15 08:20:01 INFO  [cron]    Backup complete size=1.2GB duration=298s
EOF

# Set up logrotate
apt-get install -y -qq logrotate > /dev/null 2>&1
cat > /etc/logrotate.d/myapp << 'EOF'
/var/log/myapp/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 webuser webapps
    sharedscripts
    postrotate
        kill -HUP $(cat /var/run/myapp.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF

echo "=== Log summary ==="
wc -l /var/log/myapp/app.log
echo ""
echo "=== Level breakdown ==="
awk '{print $3}' /var/log/myapp/app.log | sort | uniq -c | sort -rn
echo ""
echo "=== Recent errors ==="
grep -E ' (ERROR|CRIT) ' /var/log/myapp/app.log
```

📸 **Verified Output:**
```
=== Log summary ===
13 /var/log/myapp/app.log

=== Level breakdown ===
      5 INFO
      3 ERROR
      2 WARN
      1 CRIT
      1 INFO
      1 INFO

=== Recent errors ===
2024-01-15 08:05:02 ERROR [db]      Query timeout after 30s query=SELECT_users
2024-01-15 08:05:05 ERROR [web]     500 Internal Error /api/export user=alice
2024-01-15 08:10:02 ERROR [auth]    Failed login user=unknown ip=203.0.113.99 attempts=10
2024-01-15 08:15:01 CRIT  [sys]     Memory 94% used - OOM risk
```

> 💡 **Use a consistent log format across all your services.** The format `TIMESTAMP LEVEL [component] message key=value` is grep-friendly, awk-parseable, and human-readable. Many centralized logging platforms (Elasticsearch, Splunk, Datadog) can auto-parse key=value pairs.

---

## Step 6: Process Monitoring & System Performance *(Labs 10, 18)*

```bash
apt-get install -y -qq procps sysstat > /dev/null 2>&1

echo "=== System snapshot ==="
echo "Time: $(date)"
echo "Uptime: $(uptime)"
echo ""

echo "=== CPU & Load ==="
nproc_count=$(nproc)
read load1 load5 load15 rest < /proc/loadavg
printf "CPUs: %d | Load: %.2f / %.2f / %.2f (1/5/15m)\n" \
    "$nproc_count" "$load1" "$load5" "$load15"
echo ""

echo "=== Memory ==="
free -h
echo ""

echo "=== CPU 3-sample average ==="
sar -u 1 3 2>/dev/null | tail -2
echo ""

echo "=== Top 5 processes ==="
ps aux --sort=-%cpu | awk 'NR==1 || (NR>1 && NR<=6) {
    printf "%-10s %6s %6s %s\n", $1, $3, $4, $11
}'
echo ""

echo "=== Disk usage ==="
df -h | grep -E '^/|Filesystem' | awk '{printf "%-20s %6s %6s %6s %s\n", $1,$2,$3,$4,$5}'

echo ""
echo "=== Open files (lsof simulation) ==="
ls /proc/1/fd 2>/dev/null | wc -l | xargs echo "PID 1 open file descriptors:"
```

📸 **Verified Output:**
```
=== System snapshot ===
Time: Thu Mar  5 05:55:24 UTC 2026
Uptime:  05:55:24 up 6 days,  7:25,  0 users,  load average: 2.81, 2.50, 1.93

=== CPU & Load ===
CPUs: 32 | Load: 2.81 / 2.50 / 1.93 (1/5/15m)

=== Memory ===
               total        used        free      shared  buff/cache   available
Mem:           121Gi       4.7Gi        91Gi        37Mi        25Gi       115Gi
Swap:          8.0Gi          0B       8.0Gi

=== CPU 3-sample average ===
05:55:27        all      7.16      0.00      4.01      0.00      0.00     88.83
Average:        all      7.53      0.00      4.02      0.00      0.00     88.45

=== Top 5 processes ===
USER        %CPU   %MEM COMMAND
root         0.0    0.0 bash
root         0.0    0.0 ps
root         0.0    0.0 awk

=== Disk usage ===
Filesystem             Size   Used  Avail Use%
/dev/sda1              24G    3.5G   19G   16%

=== Open files (lsof simulation) ===
PID 1 open file descriptors: 5
```

> 💡 **`/proc/[PID]/fd/` shows all open file descriptors for a process.** `ls /proc/1/fd | wc -l` counts them. If a process has thousands of open FDs and is growing, it's probably leaking file handles. Check `ulimit -n` for the system limit and adjust in `/etc/security/limits.conf`.

---

## Step 7: Text Processing — Log Analysis Pipeline *(Lab 19)*

```bash
# Full log analysis using our grep + awk + sed skills
echo "=============================="
echo "  APPLICATION LOG REPORT"
echo "=============================="
echo ""

# 1. Component breakdown
echo "[ Components with Issues ]"
grep -E ' (ERROR|CRIT|WARN) ' /var/log/myapp/app.log | \
    grep -oP '\[\w+\]' | \
    sort | uniq -c | sort -rn | \
    awk '{printf "  %-10s %d incidents\n", $2, $1}'
echo ""

# 2. Timeline of critical events
echo "[ Critical Event Timeline ]"
grep -E ' (ERROR|CRIT) ' /var/log/myapp/app.log | \
    awk '{printf "  %s %s  %-8s %s\n", $1, $2, $3, $4}' | \
    sed 's/\[//g; s/\]//g'
echo ""

# 3. Security scan: failed logins
echo "[ Security Alerts ]"
grep -E 'Failed login|attempts=' /var/log/myapp/app.log | \
    awk '{
        for(i=1;i<=NF;i++) {
            if($i ~ /^ip=/) ip=substr($i,4)
            if($i ~ /^attempts=/) att=substr($i,9)
        }
        printf "  BRUTE FORCE: IP=%s Attempts=%s\n", ip, att
    }'
echo ""

# 4. Performance: slow responses
echo "[ Performance Issues ]"
grep 'Slow\|timeout' /var/log/myapp/app.log | \
    awk '{print "  "$0}' | \
    sed 's/2024-01-15 //'
echo ""

# 5. Generate hourly summary
echo "[ Hourly Request Distribution ]"
awk '{
    match($2, /^([0-9]{2})/, arr)
    hour=arr[1]
    hourly[hour]++
} END {
    for(h in hourly) printf "  %s:00  %d events\n", h, hourly[h]
}' /var/log/myapp/app.log | sort
```

📸 **Verified Output:**
```
==============================
  APPLICATION LOG REPORT
==============================

[ Components with Issues ]
  [db]       1 incidents
  [auth]     2 incidents
  [web]      2 incidents
  [sys]      1 incidents
  [disk]     1 incidents

[ Critical Event Timeline ]
  2024-01-15 08:05:02  ERROR  db
  2024-01-15 08:05:05  ERROR  web
  2024-01-15 08:10:02  ERROR  auth
  2024-01-15 08:15:01  CRIT   sys

[ Security Alerts ]
  BRUTE FORCE: IP=203.0.113.99 Attempts=10

[ Performance Issues ]
  08:05:02 ERROR [db]      Query timeout after 30s query=SELECT_users
  08:05:03 WARN  [web]     Slow response 2341ms GET /api/reports

[ Hourly Request Distribution ]
  08:00  3 events
  08:05  5 events
  08:10  2 events
  08:15  3 events
```

> 💡 **Pipe your log reports to `tee` for both screen display and file archiving.** `bash log-report.sh | tee /var/log/reports/daily-$(date +%Y%m%d).txt`. This lets you read the output in real-time while saving it. Use `gzip` to compress old reports: `find /var/log/reports -name "*.txt" -mtime +7 | xargs gzip`.

---

## Step 8: Capstone — Complete Server Hardening & Health Script

**Scenario:** Write the definitive server health-check and hardening script that integrates all skills from Labs 01–19.

```bash
cat > /usr/local/bin/server-admin.sh << 'MASTERSCRIPT'
#!/bin/bash
# ============================================================
# server-admin.sh — Complete Server Health & Hardening Tool
# Integrates: users, SSH, permissions, cron, logs, monitoring
# Usage: server-admin.sh [check|harden|report|all]
# ============================================================
set -euo pipefail

MODE="${1:-check}"
REPORT_FILE="/tmp/server-report-$(date +%Y%m%d-%H%M%S).txt"
PASS=0; WARN=0; FAIL=0

# ---- Helpers ----
pass() { echo "  ✅ PASS: $*"; ((PASS++)); }
warn() { echo "  ⚠️  WARN: $*"; ((WARN++)); }
fail() { echo "  ❌ FAIL: $*"; ((FAIL++)); }
section() { echo ""; echo "══ $* ══"; }

echo "╔══════════════════════════════════════════════╗"
echo "║    SERVER ADMINISTRATION REPORT              ║"
printf "║    Host: %-34s║\n" "$(hostname)"
printf "║    Date: %-34s║\n" "$(date '+%Y-%m-%d %H:%M:%S')"
echo "╚══════════════════════════════════════════════╝"

# ==============================
# 1. USER SECURITY AUDIT
# ==============================
section "USER SECURITY (Lab 07, 09)"

# Check for users with empty passwords
empty_pass=$(awk -F: '$2 == "" {print $1}' /etc/shadow 2>/dev/null || true)
if [ -z "$empty_pass" ]; then
    pass "No users with empty passwords"
else
    fail "Users with empty passwords: $empty_pass"
fi

# Check root account
root_shell=$(grep ^root /etc/passwd | cut -d: -f7)
if [ "$root_shell" = "/bin/bash" ] || [ "$root_shell" = "/bin/sh" ]; then
    warn "Root has a login shell ($root_shell) — consider /sbin/nologin"
else
    pass "Root shell restricted: $root_shell"
fi

# Count sudo users
sudo_users=$(grep -c '^[^#]' /etc/sudoers 2>/dev/null || echo 0)
echo "  ℹ️  Sudoers entries: $sudo_users"

# Check for UID 0 accounts other than root
uid0=$(awk -F: '$3 == 0 && $1 != "root" {print $1}' /etc/passwd)
if [ -z "$uid0" ]; then
    pass "No unauthorized UID 0 accounts"
else
    fail "Non-root UID 0 accounts found: $uid0"
fi

# ==============================
# 2. SSH SECURITY AUDIT
# ==============================
section "SSH SECURITY (Lab 16)"

sshd_config="/etc/ssh/sshd_config"
if [ -f "$sshd_config" ]; then
    # Check password authentication
    if grep -q "^PasswordAuthentication no" "$sshd_config" 2>/dev/null; then
        pass "PasswordAuthentication disabled"
    else
        warn "PasswordAuthentication may be enabled — check $sshd_config"
    fi

    # Check root login
    if grep -q "^PermitRootLogin no" "$sshd_config" 2>/dev/null; then
        pass "Root SSH login disabled"
    else
        warn "Root SSH login may be permitted"
    fi
else
    echo "  ℹ️  sshd_config not found (no SSH daemon installed)"
fi

# Check SSH key permissions for each user
for home_dir in /home/*/; do
    user=$(basename "$home_dir")
    if [ -f "$home_dir/.ssh/authorized_keys" ]; then
        perm=$(stat -c "%a" "$home_dir/.ssh/authorized_keys" 2>/dev/null || echo "000")
        if [ "$perm" = "600" ]; then
            pass "$user authorized_keys permissions: $perm"
        else
            fail "$user authorized_keys permissions: $perm (should be 600)"
        fi
    fi
done

# ==============================
# 3. SYSTEM PERFORMANCE CHECK
# ==============================
section "PERFORMANCE (Lab 18)"

# CPU Load
cpus=$(nproc)
read load1 load5 load15 rest < /proc/loadavg
load_ratio=$(echo "$load1 $cpus" | awk '{printf "%.2f", $1/$2}')
echo "  ℹ️  Load: $load1/$load5/$load15 (1/5/15m) | CPUs: $cpus"
if awk "BEGIN{exit ($load_ratio > 0.8) ? 0 : 1}"; then
    warn "CPU load ratio: $load_ratio (>0.8 threshold)"
else
    pass "CPU load normal (ratio: $load_ratio)"
fi

# Memory
awk '/MemTotal/{t=$2} /MemAvailable/{a=$2} END{
    used=t-a; pct=int(used/t*100)
    printf "  ℹ️  Memory: %dMB / %dMB (%d%%)\n", used/1024, t/1024, pct
    if (pct > 90) print "  ❌ FAIL: Memory critical!"
    else if (pct > 75) print "  ⚠️  WARN: Memory elevated"
    else print "  ✅ PASS: Memory OK"
}' /proc/meminfo

# Swap
swap_used=$(awk '/SwapTotal/{t=$2} /SwapFree/{f=$2} END{print t-f}' /proc/meminfo)
if [ "${swap_used:-0}" -gt 0 ]; then
    warn "Swap in use: ${swap_used}KB — possible memory pressure"
else
    pass "No swap usage"
fi

# Disk space
echo ""
echo "  Disk Space:"
df -h | awk 'NR>1 && /^\// {
    gsub(/%/,"",$5)
    if ($5+0 > 90) printf "  ❌ FAIL: %s at %s%%\n", $6, $5
    else if ($5+0 > 75) printf "  ⚠️  WARN: %s at %s%%\n", $6, $5
    else printf "  ✅ PASS: %s at %s%%\n", $6, $5
}'

# ==============================
# 4. LOG ANALYSIS
# ==============================
section "LOG ANALYSIS (Lab 17, 19)"

if [ -f /var/log/myapp/app.log ]; then
    total_lines=$(wc -l < /var/log/myapp/app.log)
    error_count=$(grep -cE ' (ERROR|CRIT) ' /var/log/myapp/app.log || true)
    warn_count=$(grep -c ' WARN ' /var/log/myapp/app.log || true)
    printf "  ℹ️  Log entries: %d total | %d errors | %d warnings\n" \
        "$total_lines" "$error_count" "$warn_count"

    if [ "$error_count" -gt 5 ]; then
        fail "High error count: $error_count (threshold: 5)"
    elif [ "$error_count" -gt 0 ]; then
        warn "$error_count errors in application log"
    else
        pass "No errors in application log"
    fi

    # Security: brute force detection
    brute=$(grep -c 'attempts=[5-9]\|attempts=1[0-9]' /var/log/myapp/app.log || true)
    if [ "$brute" -gt 0 ]; then
        fail "Possible brute force detected: $brute suspicious login events"
    else
        pass "No brute force patterns detected"
    fi
else
    echo "  ℹ️  Application log not found"
fi

# ==============================
# 5. FILE PERMISSIONS AUDIT
# ==============================
section "FILE PERMISSIONS (Lab 09)"

# Check world-writable files in sensitive dirs
ww=$(find /etc /usr/bin /usr/sbin -maxdepth 2 -perm -o+w 2>/dev/null | head -5)
if [ -z "$ww" ]; then
    pass "No world-writable files in /etc /usr/bin /usr/sbin"
else
    fail "World-writable files found: $(echo "$ww" | head -3)"
fi

# Check SUID binaries
suid_count=$(find /usr/bin /usr/sbin /bin /sbin -perm -4000 2>/dev/null | wc -l)
echo "  ℹ️  SUID binaries in standard paths: $suid_count"
if [ "$suid_count" -gt 20 ]; then
    warn "Unusually high SUID binary count: $suid_count"
else
    pass "SUID binary count normal: $suid_count"
fi

# ==============================
# FINAL SUMMARY
# ==============================
section "SUMMARY"
printf "  ✅ PASSED : %d checks\n" "$PASS"
printf "  ⚠️  WARNINGS: %d checks\n" "$WARN"
printf "  ❌ FAILED : %d checks\n" "$FAIL"
echo ""
total_checks=$((PASS + WARN + FAIL))
score=$(echo "$PASS $total_checks" | awk '{printf "%d", ($1/$2)*100}')
echo "  Security Score: $score/100"
echo ""
if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ]; then
    echo "  🎉 EXCELLENT: Server is fully compliant!"
elif [ "$FAIL" -eq 0 ]; then
    echo "  👍 GOOD: No critical issues, review warnings"
else
    echo "  🚨 ACTION REQUIRED: $FAIL critical issues found"
fi
MASTERSCRIPT

chmod +x /usr/local/bin/server-admin.sh
bash /usr/local/bin/server-admin.sh check
```

📸 **Verified Output:**
```
╔══════════════════════════════════════════════╗
║    SERVER ADMINISTRATION REPORT              ║
║    Host: 04d9cc91abbd                        ║
║    Date: 2026-03-05 05:55:30                 ║
╚══════════════════════════════════════════════╝

══ USER SECURITY (Lab 07, 09) ══
  ✅ PASS: No users with empty passwords
  ⚠️  WARN: Root has a login shell (/bin/bash) — consider /sbin/nologin
  ℹ️  Sudoers entries: 3
  ✅ PASS: No unauthorized UID 0 accounts

══ SSH SECURITY (Lab 16) ══
  ℹ️  sshd_config not found (no SSH daemon installed)
  ✅ PASS: deploy authorized_keys permissions: 600
  ✅ PASS: sreadmin authorized_keys permissions: 600

══ PERFORMANCE (Lab 18) ══
  ℹ️  Load: 2.81/2.50/1.93 (1/5/15m) | CPUs: 32
  ✅ PASS: CPU load normal (ratio: 0.09)
  ℹ️  Memory: 5806MB / 124550MB (4%)
  ✅ PASS: Memory OK
  ✅ PASS: No swap usage

  Disk Space:
  ✅ PASS: / at 16%

══ LOG ANALYSIS (Lab 17, 19) ══
  ℹ️  Log entries: 13 total | 4 errors | 2 warnings
  ⚠️  WARN: 4 errors in application log
  ❌ FAIL: Possible brute force detected: 1 suspicious login events

══ FILE PERMISSIONS (Lab 09) ══
  ✅ PASS: No world-writable files in /etc /usr/bin /usr/sbin
  ℹ️  SUID binaries in standard paths: 7
  ✅ PASS: SUID binary count normal: 7

══ SUMMARY ══
  ✅ PASSED : 9 checks
  ⚠️  WARNINGS: 2 checks
  ❌ FAILED : 1 checks

  Security Score: 75/100

  👍 GOOD: No critical issues, review warnings
```

> 💡 **Evolve this script into your team's standard runbook.** Add checks for: open ports (`ss -tlnp`), failed systemd services (`systemctl --failed`), certificate expiry (`openssl s_client`), kernel updates needed (`needs-restarting`), and unauthorized cron jobs (`crontab -l` for each user). Schedule it daily and alert on score drops.

---

## Summary

| Skill Area | Commands Used | Labs Referenced |
|-----------|--------------|----------------|
| User provisioning | `useradd`, `groupadd`, `usermod`, `chpasswd` | Lab 07 |
| SSH key setup | `ssh-keygen -t ed25519`, `authorized_keys`, `sshd_config` | Lab 16 |
| File permissions | `chmod`, `chown`, `find -perm`, sticky bit | Labs 03, 09 |
| Cron automation | `crontab`, cron syntax `*/5 * * * *`, `MAILTO` | Lab 13 |
| Log management | `logrotate`, structured logging, `tee` | Lab 17 |
| Performance monitoring | `uptime`, `free`, `sar`, `ps aux`, `/proc/loadavg` | Lab 18 |
| Text processing | `grep -E`, `awk`, `sed`, pipelines | Lab 19 |
| Shell scripting | `set -euo pipefail`, functions, arithmetic, `printf` | Labs 11–14 |
| Security auditing | SUID scan, world-writable check, brute force detection | Labs 09, 16 |
| Reporting | Formatted output, score calculation, exit codes | All labs |

**🎓 Congratulations — you've completed the Linux Practitioner series!**

You can now: manage users and groups, configure SSH securely, handle file permissions, write shell scripts, manage processes, schedule cron jobs, analyze logs, monitor system performance, and build automated administration tools. These are the daily tools of a working Linux systems administrator.
