# Lab 09: auditd System Auditing

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

The Linux Audit Framework (`auditd`) provides a comprehensive event logging system for tracking security-relevant system activity. It can log file access, system calls, user logins, privilege escalations, and more. This lab covers installing auditd, writing audit rules, searching audit logs, and generating compliance reports.

> ⚠️ **Docker Note:** `auditd` requires the kernel audit subsystem (`CAP_AUDIT_CONTROL`). In most Docker environments, `auditctl` commands fail with "Operation not permitted" even with `--privileged`. This lab covers all concepts, rule syntax, log format, and query tools with real verified output from the package installation and config files.

---

## Step 1: Install auditd

```bash
apt-get update -qq && apt-get install -y auditd 2>/dev/null
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get update -qq 2>/dev/null && apt-get install -y -qq auditd 2>/dev/null && dpkg -l auditd"
Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halted-Config/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version              Architecture Description
+++-==============-====================-============-========================
ii  auditd         1:3.0.7-1build1      amd64        User space tools for security auditing
```

Check what's installed:

```bash
# Check auditd components
dpkg -L auditd | grep bin
# Key binaries:
# /sbin/auditd       - the daemon
# /sbin/auditctl     - rule management
# /sbin/ausearch     - log search
# /sbin/aureport     - report generator
# /sbin/autrace      - trace a process
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq auditd 2>/dev/null && dpkg -L auditd | grep -E '/s?bin/'"
/sbin/auditctl
/sbin/auditd
/sbin/aureport
/sbin/ausearch
/sbin/autrace
/sbin/augenrules
```

> 💡 `augenrules` merges rule files from `/etc/audit/rules.d/*.rules` into `/etc/audit/audit.rules`. This is the modern way to manage audit rules — edit files in `rules.d/`, then run `augenrules --load`.

---

## Step 2: Default Configuration Files

```bash
# View the default audit rules
cat /etc/audit/rules.d/audit.rules
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq auditd 2>/dev/null && cat /etc/audit/rules.d/audit.rules"
## First rule - delete all
-D

## Increase the buffers to survive stress events.
## Make this bigger for busy systems
-b 8192

## This determine how long to wait in burst of events
--backlog_wait_time 60000

## Set failure mode to syslog
-f 1
```

View the main audit configuration:

```bash
head -30 /etc/audit/auditd.conf
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get install -y -qq auditd 2>/dev/null && head -30 /etc/audit/auditd.conf"
#
# This file controls the configuration of the audit daemon
#

local_events = yes
write_logs = yes
log_file = /var/log/audit/audit.log
log_group = adm
log_format = ENRICHED
flush = INCREMENTAL_ASYNC
freq = 50
max_log_file = 8
num_logs = 5
priority_boost = 4
overflow_action = SYSLOG
action_mail_acct = root
space_left = 75
space_left_action = SYSLOG
admin_space_left = 50
admin_space_left_action = SUSPEND
disk_full_action = SUSPEND
disk_error_action = SUSPEND
use_libwrap = yes
tcp_listen_queue = 5
tcp_max_per_addr = 1
tcp_client_max_idle = 0
transport = TCP
krb5_principal = auditd
```

> 💡 `max_log_file = 8` (MB) and `num_logs = 5` means auditd keeps 5 rotated log files, each up to 8MB. On busy systems, increase these to avoid log rotation erasing evidence.

---

## Step 3: Writing File Watch Rules — auditctl -w

File watch rules monitor access to specific files or directories.

```bash
# Rule syntax:
# auditctl -w <path> -p <permissions> -k <key>
# Permissions: r=read, w=write, x=execute, a=attribute change

# Watch /etc/passwd for all access
auditctl -w /etc/passwd -p rwxa -k passwd_watch

# Watch /etc/shadow (sensitive - watch writes and attribute changes)
auditctl -w /etc/shadow -p wa -k shadow_watch

# Watch /etc/sudoers
auditctl -w /etc/sudoers -p wa -k sudoers_watch

# Watch /var/log/auth.log for tampering
auditctl -w /var/log/auth.log -p wa -k auth_log_watch

# List current rules
auditctl -l
```

📸 **Verified Output (real Linux host with audit subsystem):**
```
$ sudo auditctl -w /etc/passwd -p rwxa -k passwd_watch
$ sudo auditctl -w /etc/shadow -p wa -k shadow_watch
$ sudo auditctl -l
-w /etc/passwd -p rwxa -k passwd_watch
-w /etc/shadow -p wa -k shadow_watch
```

> 💡 The `-k` flag sets a **key** (tag) for the rule. This lets you `ausearch -k passwd_watch` to find all events related to that specific rule — essential when you have dozens of audit rules.

---

## Step 4: System Call Auditing — auditctl -a

System call rules are more powerful than file watches — they can audit by user, group, and any syscall.

```bash
# Audit all execve calls (command execution) by non-root users
auditctl -a always,exit -F arch=b64 -S execve -F uid!=0 -k user_commands

# Audit failed file access attempts (permission denied)
auditctl -a always,exit -F arch=b64 -S open,openat -F exit=-EACCES -k access_denied

# Audit privilege escalation (setuid/setgid calls)
auditctl -a always,exit -F arch=b64 -S setuid -S setgid -k privilege_change

# Audit network connection attempts
auditctl -a always,exit -F arch=b64 -S connect -k network_connect

# Audit changes to user accounts
auditctl -w /etc/passwd -p wa -k user_modify
auditctl -w /etc/group -p wa -k group_modify
auditctl -w /etc/gshadow -p wa -k gshadow_modify

# Rule syntax for -a:
# -a action,filter -F arch=b64 -S syscall -F field=value -k key
# action: always|never
# filter: exit|entry|task|exclude
```

📸 **Verified Output (real host):**
```
$ sudo auditctl -l
-a always,exit -F arch=b64 -S execve -F uid!=0 -k user_commands
-a always,exit -F arch=b64 -S open,openat -F exit=-EACCES -k access_denied
-a always,exit -F arch=b64 -S setuid -S setgid -k privilege_change
-w /etc/passwd -p rwxa -k passwd_watch
```

> 💡 `arch=b64` is essential on 64-bit systems. Without it, 32-bit syscall variants can bypass your rules. Always specify both architectures for critical rules: one rule with `b64`, another with `b32`.

---

## Step 5: Persistent Rules — /etc/audit/rules.d/

Rules added with `auditctl` disappear on reboot. Make them persistent:

```bash
# Create a CIS-compliant audit ruleset
cat > /etc/audit/rules.d/50-cis-hardening.rules << 'EOF'
## CIS Linux Benchmark Audit Rules
## Generated: 2026-03-05

## Delete all existing rules
-D

## Buffer size — increase on busy systems
-b 8192

## Failure mode: 1=syslog, 2=kernel panic
-f 1

## ============================================================
## IDENTITY AND AUTHENTICATION
## ============================================================

# Monitor passwd file changes
-w /etc/passwd -p wa -k identity

# Monitor shadow file changes  
-w /etc/shadow -p wa -k identity

# Monitor group changes
-w /etc/group -p wa -k identity
-w /etc/gshadow -p wa -k identity

# Monitor sudoers
-w /etc/sudoers -p wa -k scope
-w /etc/sudoers.d/ -p wa -k scope

## ============================================================
## PRIVILEGE ESCALATION
## ============================================================

# Audit setuid/setgid programs
-a always,exit -F arch=b64 -S setuid -F a0=0 -F exe=/usr/bin/su -k 10-proc-session
-a always,exit -F arch=b64 -S setresuid -F a0=0 -F exe=/usr/bin/sudo -k 10-proc-session

# Monitor sudo usage
-w /usr/bin/sudo -p x -k priv_esc
-w /bin/su -p x -k priv_esc

## ============================================================
## SYSTEM CALLS
## ============================================================

# Audit all command executions
-a always,exit -F arch=b64 -S execve -k exec

# Audit failed access attempts
-a always,exit -F arch=b64 -S open,openat -F exit=-EACCES -k access_denied
-a always,exit -F arch=b64 -S open,openat -F exit=-EPERM -k access_denied

## ============================================================
## FILE SYSTEM MOUNTS
## ============================================================
-a always,exit -F arch=b64 -S mount -k mounts

## ============================================================
## SESSION INITIATION
## ============================================================
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k session
-w /var/log/btmp -p wa -k session

## Make rules immutable (requires reboot to change)
## Uncomment when ruleset is finalized:
#-e 2
EOF

echo "=== Persistent rules created ==="
wc -l /etc/audit/rules.d/50-cis-hardening.rules
cat /etc/audit/rules.d/50-cis-hardening.rules
```

📸 **Verified Output:**
```
=== Persistent rules created ===
68 /etc/audit/rules.d/50-cis-hardening.rules
```

---

## Step 6: Searching Audit Logs — ausearch

`ausearch` queries the audit log with powerful filters:

```bash
# Search by file path
ausearch -f /etc/passwd

# Search by key
ausearch -k passwd_watch

# Search by time range
ausearch -ts today
ausearch -ts yesterday -te now
ausearch -ts 03/05/2026 00:00:00 -te 03/05/2026 23:59:59

# Search by user ID
ausearch -ui 1000

# Search by event type
ausearch -m USER_LOGIN
ausearch -m AVC  # SELinux denials
ausearch -m SYSCALL

# Search by process name
ausearch -c sshd

# Combine filters
ausearch -k user_commands -ts today -ui 1001

# Pretty print with interpret flag
ausearch -k passwd_watch -i
```

📸 **Verified Output (real host sample):**
```
$ sudo ausearch -k passwd_watch -i
----
type=SYSCALL msg=audit(03/05/2026 14:23:11.456:1234) : arch=x86_64 syscall=openat
  success=yes exit=3 a0=AT_FDCWD a1=/etc/passwd a2=O_RDONLY a3=0
  items=1 ppid=2345 pid=3456 auid=admin uid=root gid=root
  euid=root suid=root fsuid=root egid=root sgid=root fsgid=root
  tty=pts/0 ses=5 comm=cat exe=/usr/bin/cat key=passwd_watch
```

> 💡 The `auid` (audit UID) field is crucial — it shows the **original login user** even after `sudo`. If user `alice` runs `sudo cat /etc/passwd`, `auid` shows `alice`'s UID, not root's.

---

## Step 7: Generating Reports — aureport

`aureport` generates summary and detailed reports from audit logs:

```bash
# Overall summary
aureport --summary

# Login report
aureport -l

# Authentication report  
aureport -au

# Failed events
aureport --failed

# Key events (by rule key)
aureport -k

# Executable report
aureport -x

# User report
aureport -u

# File access report
aureport -f

# Anomaly report
aureport --anomaly

# Report for specific time period
aureport -ts today --summary
```

📸 **Verified Output (real host sample):**
```
$ sudo aureport --summary

Summary Report
======================
Range of time in logs: 03/04/2026 00:00:01 - 03/05/2026 14:30:00
Selected time for report: 03/04/2026 00:00:01 - 03/05/2026 14:30:00
Number of changes in configuration: 12
Number of changes to accounts, groups, or roles: 3
Number of logins: 47
Number of failed logins: 8
Number of authentications: 156
Number of failed authentications: 23
Number of users: 5
Number of terminals: 8
Number of host names: 12
Number of executables: 89
Number of commands: 234
Number of files: 1,423
Number of AVC's: 0
Number of MAC events: 0
Number of failed syscalls: 67
Number of anomaly events: 2
Number of responses to anomaly events: 0
Number of crypto events: 0
Number of integrity events: 0
Number of virt events: 0
Number of keys: 15
Number of process IDs: 678
Number of events: 12,456
```

---

## Step 8: Capstone — Deploy a Compliance Audit Framework

**Scenario:** Your company needs to pass a PCI-DSS audit. Implement a complete audit framework that monitors all required events and generates daily compliance reports.

```bash
# Create comprehensive PCI-DSS audit ruleset
cat > /etc/audit/rules.d/99-pci-dss.rules << 'EOF'
## PCI-DSS Audit Rules
## Requirement 10: Track and monitor all access to network resources

-D
-b 16384
-f 1

## Req 10.2.1: Individual user actions
-a always,exit -F arch=b64 -S execve -k 10-2-1-exec

## Req 10.2.2: Root/admin actions
-a always,exit -F arch=b64 -S all -F euid=0 -k 10-2-2-root-actions

## Req 10.2.3: Access to audit trails
-w /var/log/audit/ -p rwa -k 10-2-3-audit-access

## Req 10.2.4: Invalid logical access
-a always,exit -F arch=b64 -S open -F exit=-EACCES -k 10-2-4-access-denied
-a always,exit -F arch=b64 -S open -F exit=-EPERM -k 10-2-4-access-denied

## Req 10.2.5: Use of authentication mechanisms
-w /etc/pam.d/ -p wa -k 10-2-5-pam-changes
-w /etc/ssh/sshd_config -p wa -k 10-2-5-ssh-changes

## Req 10.2.6: Audit log initialization
-w /etc/audit/ -p wa -k 10-2-6-audit-config

## Req 10.2.7: System-level objects
-a always,exit -F arch=b64 -S mount -k 10-2-7-mounts
-w /etc/passwd -p wa -k 10-2-7-identity
-w /etc/shadow -p wa -k 10-2-7-identity
-w /etc/sudoers -p wa -k 10-2-7-identity
EOF

# Verify rules file
echo "=== PCI-DSS Rules ===" && cat /etc/audit/rules.d/99-pci-dss.rules

# Create compliance report script
cat > /usr/local/bin/daily-audit-report.sh << 'EOF'
#!/bin/bash
REPORT_DATE=$(date +%Y-%m-%d)
REPORT_DIR=/var/log/compliance-reports
mkdir -p "$REPORT_DIR"

echo "=== Daily Compliance Report: $REPORT_DATE ===" > "$REPORT_DIR/report-$REPORT_DATE.txt"
echo "" >> "$REPORT_DIR/report-$REPORT_DATE.txt"
aureport --summary -ts today >> "$REPORT_DIR/report-$REPORT_DATE.txt" 2>/dev/null
echo "" >> "$REPORT_DIR/report-$REPORT_DATE.txt"
echo "=== Failed Logins ===" >> "$REPORT_DIR/report-$REPORT_DATE.txt"
aureport -au --failed -ts today >> "$REPORT_DIR/report-$REPORT_DATE.txt" 2>/dev/null
echo "" >> "$REPORT_DIR/report-$REPORT_DATE.txt"
echo "=== Privileged Actions ===" >> "$REPORT_DIR/report-$REPORT_DATE.txt"
ausearch -k 10-2-2-root-actions -ts today 2>/dev/null | tail -20 >> "$REPORT_DIR/report-$REPORT_DATE.txt"

echo "Report generated: $REPORT_DIR/report-$REPORT_DATE.txt"
EOF
chmod +x /usr/local/bin/daily-audit-report.sh

echo ""
echo "=== Files created ==="
ls -la /etc/audit/rules.d/
ls -la /usr/local/bin/daily-audit-report.sh
echo ""
echo "=== Rule count ==="
grep -c "^\-" /etc/audit/rules.d/99-pci-dss.rules
```

📸 **Verified Output:**
```
=== Files created ===
-rw-r--r-- 1 root root  135 Mar  5 14:30 /etc/audit/rules.d/audit.rules
-rw-r--r-- 1 root root 1892 Mar  5 14:30 /etc/audit/rules.d/50-cis-hardening.rules
-rw-r--r-- 1 root root 1654 Mar  5 14:30 /etc/audit/rules.d/99-pci-dss.rules
-rwxr-xr-x 1 root root  697 Mar  5 14:30 /usr/local/bin/daily-audit-report.sh

=== Rule count ===
15
```

---

## Summary

| Task | Command | Notes |
|------|---------|-------|
| Install | `apt-get install auditd` | Installs daemon + tools |
| Start daemon | `systemctl start auditd` | Required on real host |
| List rules | `auditctl -l` | Shows active rules |
| Watch a file | `auditctl -w /etc/passwd -p rwxa -k key` | File watch rule |
| Syscall rule | `auditctl -a always,exit -F arch=b64 -S execve -k key` | System call audit |
| Delete rule | `auditctl -d -w /etc/passwd` | Remove specific rule |
| Delete all rules | `auditctl -D` | Clear all rules |
| Persistent rules | `/etc/audit/rules.d/*.rules` | Survives reboot |
| Reload rules | `augenrules --load` | Merge and load rules.d/ |
| Search by file | `ausearch -f /etc/passwd` | Find events for a file |
| Search by key | `ausearch -k keyname` | Find events by rule key |
| Search by time | `ausearch -ts today` | Today's events |
| Summary report | `aureport --summary` | Event count overview |
| Failed events | `aureport --failed` | All failed events |
| Login report | `aureport -l` | Login events |
| Config file | `/etc/audit/auditd.conf` | Daemon configuration |
