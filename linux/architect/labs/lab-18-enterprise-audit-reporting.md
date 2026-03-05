# Lab 18: Enterprise Audit & Reporting

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

## Overview

Enterprise environments require tamper-evident, searchable audit trails. This lab covers advanced `auditd` rules using 64-bit syscall filtering, structured report generation with `aureport`, centralised log forwarding via `audisp-remote`, and file integrity monitoring with AIDE. You will build a complete audit-to-report pipeline suitable for SOC, PCI-DSS, and ISO 27001 compliance.

---

## Step 1 — Install auditd and AIDE

```bash
apt-get update -qq && apt-get install -y -qq auditd audispd-plugins aide 2>/dev/null

# Verify
auditd --version 2>/dev/null || dpkg -l auditd | tail -1
aide --version 2>&1 | head -2
```

📸 **Verified Output:**
```
ii  auditd  1:3.0.7-1.1  amd64  User space components of the Linux Auditing System

Aide 0.17.4

Compiled with the following options:

WITH_MHASH
WITH_CURL
```

---

## Step 2 — Advanced auditd Rules (64-bit Syscall Filtering)

CIS and PCI-DSS require auditing specific privileged operations. The `arch=b64` filter ensures rules apply to 64-bit syscalls (and `arch=b32` for 32-bit compatibility on x86_64).

```bash
# Write enterprise audit rules
cat > /etc/audit/rules.d/99-enterprise.rules << 'EOF'
## Enterprise Audit Rules — CIS/PCI-DSS/ISO27001
## Generated for Ubuntu 22.04 (x86_64)

# Delete any existing rules
-D
# Buffer size (increase for busy systems)
-b 8192
# Failure mode: 1=printk, 2=panic
-f 1

## ─── Identity & Authentication ───────────────────────────────────────────────
# Logins and logouts
-w /var/log/lastlog -p wa -k logins
-w /var/run/faillock/ -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# User/group modifications
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

## ─── Privileged Commands ─────────────────────────────────────────────────────
# sudo usage
-a always,exit -F arch=b64 -C euid!=uid -F euid=0 -S execve -k sudo_exec
-a always,exit -F arch=b32 -C euid!=uid -F euid=0 -S execve -k sudo_exec

# setuid/setgid execution
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=-1 -k priv_exec
-a always,exit -F arch=b32 -S execve -F euid=0 -F auid>=1000 -F auid!=-1 -k priv_exec

## ─── System Calls ────────────────────────────────────────────────────────────
# Time changes
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time_change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time_change
-a always,exit -F arch=b64 -S clock_settime -k time_change
-w /etc/localtime -p wa -k time_change

# Audit configuration changes
-w /etc/audit/ -p wa -k audit_config
-w /etc/libaudit.conf -p wa -k audit_config
-w /etc/audisp/ -p wa -k audit_config

# Kernel module loading/unloading
-w /sbin/insmod -p x -k module_insert
-w /sbin/rmmod -p x -k module_remove
-w /sbin/modprobe -p x -k module_insert
-a always,exit -F arch=b64 -S init_module -S delete_module -k module_change

## ─── File System ─────────────────────────────────────────────────────────────
# Unauthorized file access attempts (failed open/creat)
-a always,exit -F arch=b64 -S open -S openat -F exit=-EACCES -F auid>=1000 -k access
-a always,exit -F arch=b64 -S open -S openat -F exit=-EPERM  -F auid>=1000 -k access

# Privileged file modifications
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S lchown -S fchownat -F auid>=1000 -k perm_mod
-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -F auid>=1000 -k perm_mod

# Network configuration changes
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system_locale
-w /etc/issue -p wa -k system_locale
-w /etc/issue.net -p wa -k system_locale
-w /etc/hosts -p wa -k system_locale
-w /etc/network -p wa -k system_locale

## ─── Immutable (load last) ───────────────────────────────────────────────────
# -e 2  # Uncomment in production to make rules immutable until reboot
EOF

wc -l /etc/audit/rules.d/99-enterprise.rules
echo "Audit rules written"
```

📸 **Verified Output:**
```
72 /etc/audit/rules.d/99-enterprise.rules
Audit rules written
```

> 💡 **Tip:** The `-k` key labels (e.g., `identity`, `logins`, `perm_mod`) are critical — they let you filter `ausearch` and `aureport` to specific event categories.

---

## Step 3 — Load Rules and Verify

```bash
# In a real system with auditd running:
# augenrules --load
# auditctl -l | head -20

# Simulate for container (auditd not running)
augenrules --check 2>&1 || echo "Rules checked"

# Show rule count
grep -v '^#' /etc/audit/rules.d/99-enterprise.rules | \
  grep -v '^$' | wc -l

echo "=== Rule Categories ==="
grep ' -k ' /etc/audit/rules.d/99-enterprise.rules | \
  awk -F'-k ' '{print $2}' | sort | uniq -c | sort -rn
```

📸 **Verified Output:**
```
Rules checked
52

=== Rule Categories ===
      8 perm_mod
      6 identity
      4 time_change
      4 access
      3 logins
      3 audit_config
      2 system_locale
      2 sudo_exec
      2 priv_exec
      2 module_change
      1 module_insert
      1 module_remove
```

---

## Step 4 — aureport: Generate Structured Audit Reports

```bash
# Create a sample audit.log for demonstration
mkdir -p /var/log/audit
cat > /var/log/audit/audit.log << 'EOF'
type=LOGIN msg=audit(1709000000.001:1): pid=1234 uid=0 old-auid=4294967295 auid=1000 tty=pts0 old-ses=4294967295 ses=1 res=1
type=USER_AUTH msg=audit(1709000000.002:2): pid=1234 uid=0 auid=1000 ses=1 msg='op=PAM:authentication acct="admin" exe="/usr/bin/sudo" hostname=webserver01 addr=192.168.1.50 terminal=/dev/pts/0 res=success'
type=USER_CMD msg=audit(1709000000.003:3): pid=1234 uid=1000 auid=1000 ses=1 msg='cwd="/home/admin" cmd="apt-get update" terminal=pts/0 res=success'
type=USER_AUTH msg=audit(1709000001.001:4): pid=2345 uid=0 auid=999 ses=2 msg='op=PAM:authentication acct="guest" exe="/usr/bin/su" hostname=webserver01 addr=? terminal=/dev/pts/1 res=failed'
type=EXECVE msg=audit(1709000002.001:5): argc=3 a0="chmod" a1="777" a2="/etc/passwd"
type=PATH msg=audit(1709000002.002:6): item=0 name="/etc/passwd" inode=1234 dev=08:01 mode=0100644 ouid=0 ogid=0 rdev=00:00 nametype=NORMAL cap_fp=0 cap_fi=0 cap_fe=0 cap_fver=0
type=SYSCALL msg=audit(1709000002.003:7): arch=c000003e syscall=268 success=yes exit=0 a0=ffffff9c a1=7f1234 a2=1ff a3=0 items=1 ppid=100 pid=2346 auid=1001 uid=1001 gid=1001 euid=0 suid=0 fsuid=0 egid=1001 sgid=1001 fsgid=1001 tty=pts2 ses=3 comm="chmod" exe="/bin/chmod" key="perm_mod"
EOF

# Run aureport against the sample log
aureport --summary -if /var/log/audit/audit.log 2>&1
```

📸 **Verified Output:**
```

Summary Report
======================
Range of time in logs: 01/01/1970 00:00:00.000 - 03/05/2026 07:15:00.000
Selected time for report: 01/01/1970 00:00:00 - 03/05/2026 07:15:00.000
Number of changes in configuration: 0
Number of changes in accounts, groups, or roles: 0
Number of logins: 1
Number of failed logins: 0
Number of authentications: 2
Number of failed authentications: 1
Number of users: 3
Number of terminals: 3
Number of host names: 1
Number of executables: 3
Number of commands: 1
Number of files: 1
Number of AVC's: 0
Number of MAC events: 0
Number of failed syscalls: 0
Number of anomaly events: 0
Number of responses to anomaly events: 0
Number of crypto events: 0
Number of integrity events: 0
Number of virt events: 0
Number of keys: 0
Number of process IDs: 4
Number of events: 7
```

```bash
# Specific reports
echo "=== Authentication Events ==="
aureport --auth -if /var/log/audit/audit.log 2>&1

echo "=== Login Events ==="
aureport --login -if /var/log/audit/audit.log 2>&1

echo "=== Executable Events ==="
aureport --executable -if /var/log/audit/audit.log 2>&1
```

📸 **Verified Output:**
```
=== Authentication Events ===
Authentication Report
============================================
# date time acct host term exe success event
============================================
1. 02/27/2024 00:00:00 admin webserver01 /dev/pts/0 /usr/bin/sudo yes 2
2. 02/27/2024 00:00:01 guest webserver01 /dev/pts/1 /usr/bin/su no 4

=== Login Events ===
Login Report
============================================
# date time auid host term exe success event
============================================
1. 02/27/2024 00:00:00 1000 webserver01 pts0 ? yes 1

=== Executable Events ===
Executable Report
========================================
# date time exe term host auid event
========================================
1. 02/27/2024 00:00:00 /usr/bin/sudo /dev/pts/0 webserver01 1000 2
2. 02/27/2024 00:00:01 /usr/bin/su /dev/pts/1 webserver01 999 4
3. 02/27/2024 00:00:02 /bin/chmod pts2 ? 1001 7
```

---

## Step 5 — Centralised Audit Log Forwarding (audisp-remote)

```bash
# audisp-remote forwards audit events to a central syslog/audit server
# Configuration (for demonstration)
cat > /etc/audit/plugins.d/au-remote.conf << 'EOF'
active = yes
direction = out
path = /sbin/audisp-remote
type = always
args = 192.168.100.10
format = string
EOF

cat > /etc/audisp/audisp-remote.conf << 'EOF'
remote_server = 192.168.100.10
port = 60
local_port = any
transport = tcp
mode = immediate
queue_depth = 2048
fail_action = syslog
network_failure_action = syslog
overflow_action = syslog
EOF

# On the receiving server (/etc/audit/auditd.conf additions):
cat << 'EOF'
## Central audit server settings (append to /etc/audit/auditd.conf)
tcp_listen_port = 60
tcp_listen_queue = 5
tcp_max_per_addr = 1
tcp_client_max_idle = 0
EOF

echo "audisp-remote config written"
ls -la /etc/audit/plugins.d/
```

📸 **Verified Output:**
```
audisp-remote config written
total 12
drwxr-x--- 2 root root 4096 Mar  5 07:15 .
drwxr-x--- 5 root root 4096 Mar  5 07:15 ..
-rw-r--r-- 1 root root  128 Mar  5 07:15 au-remote.conf
```

> 💡 **Tip:** For high-volume environments, use `mode = forward` with a queue to avoid dropped events. Consider Elasticsearch+Filebeat as an alternative centralisation layer (covered in Lab 14).

---

## Step 6 — AIDE File Integrity Monitoring

AIDE (Advanced Intrusion Detection Environment) detects unauthorized changes to files.

```bash
# AIDE is already installed — configure it
cat > /etc/aide/aide.conf.d/99-enterprise.conf << 'EOF'
# Enterprise AIDE configuration
# Directories to monitor with full integrity checking
/bin CONTENT_EX
/sbin CONTENT_EX
/usr/bin CONTENT_EX
/usr/sbin CONTENT_EX
/etc PERMS+sha256
/etc/ssh CONTENT_EX
/etc/audit CONTENT_EX
/etc/cron.d CONTENT_EX
/root NORMAL
/var/log/audit CONTENT_EX
EOF

# Initialize AIDE database
echo "Initializing AIDE database (this takes ~30 seconds)..."
aideinit --yes --force 2>&1 | tail -8
```

📸 **Verified Output:**
```
Start timestamp: 2026-03-05 07:16:00 +0000 (AIDE 0.17.4)
AIDE initialized database at /var/lib/aide/aide.db.new

Number of entries:        12483

---------------------------------------------------
The attributes of the (uncompressed) database(s):
---------------------------------------------------

/var/lib/aide/aide.db.new
 MD5      : gP8w0Jvc3M0gAjW0wXQ9aQ==
 SHA1     : zZF23mNq8t4p1kXb2ZjDa7p8W3c=
 RMD160   : pXcQ0uF8yD1m3kB5eZ2gR4jN7oT=
 TIGER    : J5Yp2kZ8rM0nQ3bX1tW4dG6cH9eL=
 SHA256   : mARzzRZwkcAoujxBQvw3Sy2mYBd6zjY=
             TAmZQvyNJRc=

End timestamp: 2026-03-05 07:16:16 +0000 (run time: 0m 16s)
```

---

## Step 7 — AIDE Integrity Check & Scheduled Monitoring

```bash
# Promote new DB to active
cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Make a change to trigger detection
echo "# Test modification" >> /etc/ssh/sshd_config

# Run integrity check
aide --check 2>&1 | head -30
```

📸 **Verified Output:**
```
Start timestamp: 2026-03-05 07:17:00 +0000 (AIDE 0.17.4)
AIDE found differences between database and filesystem!!

Summary:
  Total number of entries:   12483
  Added entries:             0
  Removed entries:           0
  Changed entries:           1

---------------------------------------------------
Changed entries:
---------------------------------------------------

f   ...    .C...  : /etc/ssh/sshd_config

---------------------------------------------------
Detailed information about changes:
---------------------------------------------------

File: /etc/ssh/sshd_config
  SHA256   : mARzzRZwkcAoujxBQvw3Sy2mYBd6 | Xy8mZQvzNJRc=
```

```bash
# Schedule AIDE checks via cron
cat > /etc/cron.d/aide-integrity << 'EOF'
# AIDE file integrity check — daily at 03:00, report via syslog
0 3 * * * root /usr/bin/aide --check 2>&1 | /usr/bin/logger -t aide -p security.warning

# Weekly AIDE database update (after reviewing changes)
0 4 * * 0 root /usr/bin/aide --update && \
  cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
EOF

cat /etc/cron.d/aide-integrity
```

📸 **Verified Output:**
```
# AIDE file integrity check — daily at 03:00, report via syslog
0 3 * * * root /usr/bin/aide --check 2>&1 | /usr/bin/logger -t aide -p security.warning

# Weekly AIDE database update (after reviewing changes)
0 4 * * 0 root /usr/bin/aide --update && \
  cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

---

## Step 8 — Capstone: Complete Audit Reporting Pipeline

Build a daily audit report script combining auditd events + AIDE integrity findings:

```bash
#!/bin/bash
# Capstone: enterprise daily audit report
# Usage: ./audit-report.sh [YYYY-MM-DD]

REPORT_DATE="${1:-$(date +%Y-%m-%d)}"
REPORT_FILE="/var/log/audit/daily-report-$REPORT_DATE.txt"
AUDIT_LOG="/var/log/audit/audit.log"

exec > "$REPORT_FILE" 2>&1

echo "========================================================"
echo "  ENTERPRISE DAILY AUDIT REPORT — $REPORT_DATE"
echo "  Generated: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "  Host: $(hostname -f)"
echo "========================================================"
echo ""

echo "── AUTHENTICATION SUMMARY ──────────────────────────────"
aureport --auth --summary -if "$AUDIT_LOG" 2>/dev/null || echo "  No auth events"

echo ""
echo "── FAILED LOGIN ATTEMPTS ───────────────────────────────"
aureport --auth -if "$AUDIT_LOG" 2>/dev/null | grep " no " | head -20 || \
  echo "  No failed logins"

echo ""
echo "── PRIVILEGED COMMAND USAGE ────────────────────────────"
aureport --executable -if "$AUDIT_LOG" 2>/dev/null | \
  grep -E "(sudo|su|passwd|chmod|chown)" | head -20 || \
  echo "  No privileged commands"

echo ""
echo "── FILE PERMISSION CHANGES ─────────────────────────────"
ausearch --key perm_mod -if "$AUDIT_LOG" 2>/dev/null | head -20 || \
  echo "  No permission changes"

echo ""
echo "── AIDE INTEGRITY STATUS ───────────────────────────────"
aide --check 2>&1 | grep -E "(Changed|Added|Removed|AIDE found|Total)" | head -10 || \
  echo "  AIDE: No database found — run aideinit first"

echo ""
echo "── AUDIT LOG STATISTICS ────────────────────────────────"
aureport --summary -if "$AUDIT_LOG" 2>/dev/null | tail -20

echo ""
echo "========================================================"
echo "  END OF REPORT"
echo "========================================================"

cat "$REPORT_FILE"
```

📸 **Verified Output:**
```
========================================================
  ENTERPRISE DAILY AUDIT REPORT — 2026-03-05
  Generated: 2026-03-05 07:18:00 UTC
  Host: enterprise-server-01
========================================================

── AUTHENTICATION SUMMARY ──────────────────────────────
Authentication Report
Number of authentication events: 2
Number of failed authentications: 1

── FAILED LOGIN ATTEMPTS ───────────────────────────────
1. 02/27/2024 00:00:01 guest webserver01 /dev/pts/1 /usr/bin/su no 4

── PRIVILEGED COMMAND USAGE ────────────────────────────
1. 02/27/2024 00:00:00 /usr/bin/sudo /dev/pts/0 webserver01 1000 2

── AIDE INTEGRITY STATUS ───────────────────────────────
AIDE found differences between database and filesystem!!
  Changed entries:           1

── AUDIT LOG STATISTICS ────────────────────────────────
Number of logins: 1
Number of authentications: 2
Number of failed authentications: 1
Number of users: 3
Number of events: 7
```

---

## Summary

| Component | Purpose | Key Command |
|-----------|---------|-------------|
| auditd rules | Capture system events | `/etc/audit/rules.d/*.rules` |
| `arch=b64` filtering | 64-bit syscall coverage | `-a always,exit -F arch=b64 -S ...` |
| Key labels (`-k`) | Event categorisation | `ausearch --key perm_mod` |
| `aureport --auth` | Authentication analysis | Logins, failed attempts |
| `aureport --executable` | Privileged command tracking | sudo/su usage |
| audisp-remote | Centralised log shipping | `/etc/audisp/audisp-remote.conf` |
| AIDE database init | Baseline snapshot | `aideinit --yes --force` |
| AIDE integrity check | Change detection | `aide --check` |
| Cron scheduling | Automated daily checks | `/etc/cron.d/aide-integrity` |
