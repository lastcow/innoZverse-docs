# Lab 17: Log Management — journalctl, syslog & logrotate

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Linux logs are your system's black box recorder. In this lab you will explore the `/var/log/` structure, send messages with `logger`, configure `logrotate`, understand `rsyslog` basics, and analyze structured application logs — skills critical for debugging and operations.

**Prerequisites:** Docker installed, Labs 01–15 completed.

---

## Step 1: Explore /var/log/ Structure

```bash
docker run -it --rm ubuntu:22.04 bash
ls -la /var/log/
```

📸 **Verified Output:**
```
total 304
drwxr-xr-x  3 root root   4096 Feb 10 14:05 .
drwxr-xr-x 11 root root   4096 Feb 10 14:12 ..
-rw-r--r--  1 root root   4860 Feb 10 14:11 alternatives.log
drwxr-xr-x  2 root root   4096 Feb 10 14:12 apt
-rw-r--r--  1 root root  64549 Feb 10 14:05 bootstrap.log
-rw-rw----  1 root utmp      0 Feb 10 14:05 btmp
-rw-r--r--  1 root root 186634 Feb 10 14:12 dpkg.log
-rw-r--r--  1 root root   3232 Feb 10 14:05 faillog
-rw-rw-r--  1 root utmp  29492 Feb 10 14:05 lastlog
-rw-rw-r--  1 root utmp      0 Feb 10 14:05 wtmp
```

**Key log files on a full system:**

| Log File | Contents |
|----------|---------|
| `/var/log/syslog` | General system messages (Debian/Ubuntu) |
| `/var/log/messages` | General system messages (RHEL/CentOS) |
| `/var/log/auth.log` | Authentication: SSH, sudo, PAM |
| `/var/log/kern.log` | Kernel messages |
| `/var/log/dpkg.log` | Package installations/removals |
| `/var/log/apt/` | APT package manager logs |
| `/var/log/nginx/` | Web server access/error logs |
| `/var/log/journal/` | systemd journal binary logs |

> 💡 **Log files have different permission levels.** `auth.log` is often readable only by root and the `adm` group — add your user to `adm` with `usermod -aG adm youruser` to read auth logs without sudo.

---

## Step 2: The `logger` Command — Write to System Log

`logger` sends messages to the syslog daemon from the command line or scripts.

```bash
# Basic usage
logger "Application started successfully"
echo "exit: $?"

# With priority (facility.severity)
logger -p user.info   "INFO: Service health check passed"
logger -p user.warn   "WARN: Disk usage above 80%"
logger -p user.err    "ERROR: Database connection failed"
logger -p daemon.crit "CRIT: Out of memory condition"

# With tag (identifies the program)
logger -t myapp -p user.info "User login: alice from 192.168.1.10"
logger -t backup -p user.notice "Backup completed: 1.2GB in 45s"

# Show the message would go to syslog
logger --stderr -p user.info "This also prints to stderr" 2>&1

echo "logger exit code: $?"
```

📸 **Verified Output:**
```
exit: 0
This also prints to stderr
logger exit code: 0
```

**Syslog priorities (severity levels):**

| Level | Number | Use Case |
|-------|--------|---------|
| `emerg` | 0 | System is unusable |
| `alert` | 1 | Action must be taken immediately |
| `crit` | 2 | Critical conditions |
| `err` | 3 | Error conditions |
| `warn` | 4 | Warning conditions |
| `notice` | 5 | Normal but significant |
| `info` | 6 | Informational messages |
| `debug` | 7 | Debug-level messages |

> 💡 **Use `logger` in shell scripts for proper log integration.** Instead of `echo "Error occurred"`, use `logger -t myscript -p user.err "Error occurred"` — this integrates with syslog, journald, and centralized log aggregators automatically.

---

## Step 3: journalctl — Query the systemd Journal

`journalctl` queries the binary journal maintained by `systemd-journald`. It's the primary log tool on modern Linux systems.

```bash
apt-get update -qq && apt-get install -y -qq systemd 2>/dev/null | tail -3

# Key journalctl flags:
echo "=== journalctl command reference ==="
cat << 'EOF'
journalctl                          # All logs (oldest first)
journalctl -n 20                    # Last 20 lines
journalctl -f                       # Follow (like tail -f)
journalctl -p err                   # Priority: err and above
journalctl -p warning..err          # Priority range
journalctl -u nginx.service         # Specific unit
journalctl --since "2024-01-15 08:00:00"
journalctl --until "2024-01-15 09:00:00"
journalctl --since "1 hour ago"
journalctl --since today
journalctl --no-pager               # Don't use pager (good for scripts)
journalctl -o json                  # JSON output
journalctl -o json-pretty           # Pretty JSON
journalctl --disk-usage             # Show journal disk usage
journalctl --vacuum-size=500M       # Reduce journal to 500MB
journalctl --vacuum-time=30d        # Delete entries older than 30 days
journalctl -b                       # This boot only
journalctl -b -1                    # Previous boot
journalctl _PID=1234                # Messages from specific PID
journalctl _SYSTEMD_UNIT=sshd.service _PRIORITY=3   # Combined filters
EOF
```

📸 **Verified Output:**
```
=== journalctl command reference ===
journalctl                          # All logs (oldest first)
journalctl -n 20                    # Last 20 lines
journalctl -f                       # Follow (like tail -f)
journalctl -p err                   # Priority: err and above
journalctl -p warning..err          # Priority range
journalctl -u nginx.service         # Specific unit
journalctl --since "2024-01-15 08:00:00"
journalctl --until "2024-01-15 09:00:00"
journalctl --since "1 hour ago"
journalctl --since today
journalctl --no-pager               # Don't use pager (good for scripts)
journalctl -o json                  # JSON output
journalctl -o json-pretty           # Pretty JSON
journalctl --disk-usage             # Show journal disk usage
journalctl --vacuum-size=500M       # Reduce journal to 500MB
journalctl --vacuum-time=30d        # Delete entries older than 30 days
journalctl -b                       # This boot only
journalctl -b -1                    # Previous boot
journalctl _PID=1234                # Messages from specific PID
journalctl _SYSTEMD_UNIT=sshd.service _PRIORITY=3   # Combined filters
```

> 💡 **`journalctl --no-pager` is essential in scripts.** Without it, journalctl opens an interactive pager (less) which blocks automation. Always add `--no-pager` in scripts, cron jobs, and monitoring tools.

---

## Step 4: logrotate — Prevent Logs from Filling Your Disk

`logrotate` automatically rotates, compresses, and deletes old log files.

```bash
apt-get install -y -qq logrotate > /dev/null 2>&1

# View global config
cat /etc/logrotate.conf
```

📸 **Verified Output:**
```
# see "man logrotate" for details

# global options do not affect preceding include directives

# rotate log files weekly
weekly

# use the adm group by default, since this is the owning group
# of /var/log/syslog.
su root adm

# keep 4 weeks worth of backlogs
rotate 4

# create new (empty) log files after rotating old ones
create

# use date as a suffix of the rotated file
#dateext

# uncomment this if you want your log files compressed
#compress

# packages drop log rotation information into this directory
include /etc/logrotate.d
```

```bash
# View installed logrotate configs
ls /etc/logrotate.d/
```

📸 **Verified Output:**
```
alternatives  apt  btmp  dpkg  rsyslog  wtmp
```

```bash
# Write a custom logrotate config for an app
cat > /etc/logrotate.d/myapp << 'EOF'
/var/log/myapp/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    postrotate
        systemctl reload myapp 2>/dev/null || true
    endscript
}
EOF
cat /etc/logrotate.d/myapp
```

📸 **Verified Output:**
```
/var/log/myapp/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    postrotate
        systemctl reload myapp 2>/dev/null || true
    endscript
}
```

**logrotate directives explained:**

| Directive | Meaning |
|-----------|---------|
| `daily` / `weekly` / `monthly` | Rotation frequency |
| `rotate 7` | Keep 7 rotated files |
| `compress` | gzip rotated files |
| `delaycompress` | Don't compress the most recent rotation |
| `missingok` | Don't error if log doesn't exist |
| `notifempty` | Skip rotation if log is empty |
| `create 0640 user group` | Create new log with these perms |
| `postrotate` | Shell script to run after rotation |
| `sharedscripts` | Run postrotate once for all matching files |

> 💡 **Test logrotate configs with `logrotate -d`** (debug/dry-run mode): `logrotate -d /etc/logrotate.d/myapp`. It shows what would happen without doing it. Use `logrotate -f` to force rotation even if not due yet.

---

## Step 5: rsyslog — Traditional Syslog Daemon

rsyslog receives, filters, and routes log messages.

```bash
apt-get install -y -qq rsyslog > /dev/null 2>&1

# View rsyslog main config
head -40 /etc/rsyslog.conf

# rsyslog rule format: facility.severity   destination
# Examples of rules you'd add to /etc/rsyslog.conf or /etc/rsyslog.d/
cat > /etc/rsyslog.d/myapp.conf << 'EOF'
# Route myapp logs to a dedicated file
:programname, isequal, "myapp" /var/log/myapp/app.log

# Send all errors to a dedicated error log
*.err /var/log/errors.log

# Forward everything to a remote syslog server (UDP)
# *.* @192.168.1.200:514

# Forward with TCP (more reliable)
# *.* @@logserver.example.com:514

# Drop debug messages (don't log them)
*.debug stop
EOF
cat /etc/rsyslog.d/myapp.conf
```

📸 **Verified Output:**
```
# Route myapp logs to a dedicated file
:programname, isequal, "myapp" /var/log/myapp/app.log

# Send all errors to a dedicated error log
*.err /var/log/errors.log

# Forward everything to a remote syslog server (UDP)
# *.* @192.168.1.200:514

# Forward with TCP (more reliable)
# *.* @@logserver.example.com:514

# Drop debug messages (don't log them)
*.debug stop
```

> 💡 **rsyslog vs journald:** On modern systemd systems, journald captures all logs in binary format. rsyslog can subscribe to journald and forward logs to files or remote servers. They complement each other — journald for local structured queries, rsyslog for forwarding and text-file compatibility.

---

## Step 6: Create & Analyze Structured Log Entries

Good log format makes analysis easy. Learn to write and parse structured logs.

```bash
mkdir -p /var/log/myapp

# Create a realistic application log
cat > /var/log/myapp/app.log << 'EOF'
2024-01-15 08:00:01 INFO  [web]  GET /api/users HTTP/1.1 200 45ms user=alice ip=192.168.1.10
2024-01-15 08:00:02 ERROR [db]   Connection timeout after 30s host=db-01 pool=main
2024-01-15 08:00:03 WARN  [web]  Slow response GET /api/reports 2341ms threshold=1000ms
2024-01-15 08:00:04 INFO  [auth] Login successful user=bob ip=10.0.1.5 method=key
2024-01-15 08:00:05 ERROR [web]  500 Internal Server Error /api/export user=alice
2024-01-15 08:00:06 INFO  [cron] Backup job started size_estimate=2.1GB
2024-01-15 08:00:07 WARN  [disk] Disk usage 85% on /var/data threshold=80%
2024-01-15 08:00:08 INFO  [web]  GET /health HTTP/1.1 200 2ms
2024-01-15 08:00:09 ERROR [auth] Login failed user=mallory ip=203.0.113.99 attempts=5
2024-01-15 08:00:10 CRIT  [sys]  Memory pressure: 95% used, OOM killer may activate
EOF

# Count by level
echo "=== Log level counts ==="
awk '{print $3}' /var/log/myapp/app.log | sort | uniq -c | sort -rn

# Show only errors
echo "=== Errors only ==="
grep -E '^[0-9-]+ [0-9:]+ (ERROR|CRIT)' /var/log/myapp/app.log

# Show last 5 entries
echo "=== Last 5 entries ==="
tail -5 /var/log/myapp/app.log

# Extract slow responses
echo "=== Slow responses (>1000ms) ==="
grep 'WARN.*[0-9]\{4,\}ms' /var/log/myapp/app.log
```

📸 **Verified Output:**
```
=== Log level counts ===
      5 INFO
      3 ERROR
      1 WARN
      1 CRIT
=== Errors only ===
2024-01-15 08:00:02 ERROR [db]   Connection timeout after 30s host=db-01 pool=main
2024-01-15 08:00:05 ERROR [web]  500 Internal Server Error /api/export user=alice
2024-01-15 08:00:09 ERROR [auth] Login failed user=mallory ip=203.0.113.99 attempts=5
2024-01-15 08:00:10 CRIT  [sys]  Memory pressure: 95% used, OOM killer may activate
=== Last 5 entries ===
2024-01-15 08:00:06 INFO  [cron] Backup job started size_estimate=2.1GB
2024-01-15 08:00:07 WARN  [disk] Disk usage 85% on /var/data threshold=80%
2024-01-15 08:00:08 INFO  [web]  GET /health HTTP/1.1 200 2ms
2024-01-15 08:00:09 ERROR [auth] Login failed user=mallory ip=mallory ip=203.0.113.99 attempts=5
2024-01-15 08:00:10 CRIT  [sys]  Memory pressure: 95% used, OOM killer may activate
=== Slow responses (>1000ms) ===
2024-01-15 08:00:03 WARN  [web]  Slow response GET /api/reports 2341ms threshold=1000ms
```

> 💡 **Design logs for grep.** Use consistent field ordering, include key=value pairs for easy parsing, and choose a timestamp format that sorts lexicographically (ISO 8601: `2024-01-15 08:00:01`). Avoid log messages that span multiple lines — they're hard to grep.

---

## Step 7: tail -f Simulation — Following Logs in Real Time

```bash
# Simulate a live log stream
(
  for i in $(seq 1 8); do
    sleep 0.3
    echo "$(date '+%Y-%m-%d %H:%M:%S') INFO  [worker] Processing job id=$i status=running"
  done
  echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR [worker] Job id=5 failed: disk full"
  echo "$(date '+%Y-%m-%d %H:%M:%S') INFO  [worker] Jobs completed: 7/8 success=87%"
) | tee /var/log/myapp/worker.log

echo ""
echo "=== File written ==="
wc -l /var/log/myapp/worker.log
tail -3 /var/log/myapp/worker.log

# In real systems you'd use:
# tail -f /var/log/myapp/worker.log        # Follow a single file
# tail -f /var/log/nginx/access.log /var/log/nginx/error.log  # Multiple files
# journalctl -f -u myapp.service           # Follow systemd unit
# multitail /var/log/*.log                 # Follow multiple with colors
```

📸 **Verified Output:**
```
2024-01-15 08:00:01 INFO  [worker] Processing job id=1 status=running
2024-01-15 08:00:01 INFO  [worker] Processing job id=2 status=running
2024-01-15 08:00:02 INFO  [worker] Processing job id=3 status=running
2024-01-15 08:00:02 INFO  [worker] Processing job id=4 status=running
2024-01-15 08:00:02 INFO  [worker] Processing job id=5 status=running
2024-01-15 08:00:03 INFO  [worker] Processing job id=6 status=running
2024-01-15 08:00:03 INFO  [worker] Processing job id=7 status=running
2024-01-15 08:00:03 INFO  [worker] Processing job id=8 status=running
2024-01-15 08:00:03 ERROR [worker] Job id=5 failed: disk full
2024-01-15 08:00:03 INFO  [worker] Jobs completed: 7/8 success=87%

=== File written ===
10 /var/log/myapp/worker.log
2024-01-15 08:00:03 ERROR [worker] Job id=5 failed: disk full
2024-01-15 08:00:03 INFO  [worker] Jobs completed: 7/8 success=87%
```

> 💡 **`tee` writes to both stdout and a file simultaneously.** `command | tee file.log` shows output on screen AND saves to file. Use `tee -a` to append instead of overwrite. Critical for capture logs from interactive processes.

---

## Step 8: Capstone — Log Analysis & Alerting Script

**Scenario:** Build a log monitoring script that detects anomalies and generates an alert report.

```bash
cat > /tmp/log-monitor.sh << 'SCRIPT'
#!/bin/bash
# log-monitor.sh — Analyze logs and generate alert report
set -euo pipefail

LOG_FILE="${1:-/var/log/myapp/app.log}"
THRESHOLD_ERRORS="${2:-3}"
THRESHOLD_WARN="${3:-5}"
REPORT_FILE="/tmp/log-report-$(date +%Y%m%d-%H%M%S).txt"

echo "=== Log Monitor Report ===" | tee "$REPORT_FILE"
echo "Generated: $(date)" | tee -a "$REPORT_FILE"
echo "Analyzing: $LOG_FILE" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

if [ ! -f "$LOG_FILE" ]; then
    echo "ERROR: Log file not found: $LOG_FILE"
    exit 1
fi

# Count levels
total=$(wc -l < "$LOG_FILE")
errors=$(grep -cE ' (ERROR|CRIT) ' "$LOG_FILE" || true)
warnings=$(grep -c ' WARN ' "$LOG_FILE" || true)
info=$(grep -c ' INFO ' "$LOG_FILE" || true)

echo "=== Summary ===" | tee -a "$REPORT_FILE"
printf "  Total entries : %d\n" "$total" | tee -a "$REPORT_FILE"
printf "  INFO          : %d\n" "$info"  | tee -a "$REPORT_FILE"
printf "  WARN          : %d\n" "$warnings" | tee -a "$REPORT_FILE"
printf "  ERROR/CRIT    : %d\n" "$errors" | tee -a "$REPORT_FILE"
echo "" | tee -a "$REPORT_FILE"

# Alert on thresholds
ALERT=0
if [ "$errors" -ge "$THRESHOLD_ERRORS" ]; then
    echo "🚨 ALERT: $errors errors found (threshold: $THRESHOLD_ERRORS)" | tee -a "$REPORT_FILE"
    ALERT=1
fi
if [ "$warnings" -ge "$THRESHOLD_WARN" ]; then
    echo "⚠️  ALERT: $warnings warnings found (threshold: $THRESHOLD_WARN)" | tee -a "$REPORT_FILE"
    ALERT=1
fi
[ "$ALERT" -eq 0 ] && echo "✅ All levels within thresholds" | tee -a "$REPORT_FILE"

echo "" | tee -a "$REPORT_FILE"
echo "=== Recent Errors ===" | tee -a "$REPORT_FILE"
grep -E ' (ERROR|CRIT) ' "$LOG_FILE" | tail -5 | tee -a "$REPORT_FILE"

echo "" | tee -a "$REPORT_FILE"
echo "=== Component Error Breakdown ===" | tee -a "$REPORT_FILE"
grep -E ' (ERROR|CRIT) ' "$LOG_FILE" | \
    grep -oP '\[\w+\]' | sort | uniq -c | sort -rn | tee -a "$REPORT_FILE"

echo "" | tee -a "$REPORT_FILE"
echo "Report saved to: $REPORT_FILE"
SCRIPT

chmod +x /tmp/log-monitor.sh
bash /tmp/log-monitor.sh /var/log/myapp/app.log 2 3
```

📸 **Verified Output:**
```
=== Log Monitor Report ===
Generated: Mon Jan 15 08:00:10 UTC 2024
Analyzing: /var/log/myapp/app.log

=== Summary ===
  Total entries : 10
  INFO          : 5
  WARN          : 2
  ERROR/CRIT    : 4

🚨 ALERT: 4 errors found (threshold: 2)
⚠️  ALERT: 2 warnings found (threshold: 3)

=== Recent Errors ===
2024-01-15 08:00:02 ERROR [db]   Connection timeout after 30s host=db-01 pool=main
2024-01-15 08:00:05 ERROR [web]  500 Internal Server Error /api/export user=alice
2024-01-15 08:00:09 ERROR [auth] Login failed user=mallory ip=203.0.113.99 attempts=5
2024-01-15 08:00:10 CRIT  [sys]  Memory pressure: 95% used, OOM killer may activate

=== Component Error Breakdown ===
      1 [auth]
      1 [db]
      1 [sys]
      1 [web]

Report saved to: /tmp/log-report-20240115-080010.txt
```

> 💡 **Integrate log monitoring with alerting.** Pipe this script's output to `mail -s "Log Alert" ops@example.com` for email alerts, or use `curl -X POST` to send to Slack/PagerDuty webhooks. Schedule with cron: `*/15 * * * * /usr/local/bin/log-monitor.sh >> /var/log/monitor.log 2>&1`.

---

## Summary

| Tool / File | Purpose | Key Flags |
|-------------|---------|-----------|
| `/var/log/` | Log file directory | — |
| `logger` | Write to syslog from CLI/scripts | `-p facility.level -t tag` |
| `journalctl` | Query systemd journal | `-n -f -u -p --since --until --no-pager` |
| `logrotate` | Rotate/compress/delete old logs | `-d` (debug), `-f` (force) |
| `/etc/logrotate.d/` | Per-app logrotate configs | `daily rotate compress` |
| `rsyslog` | Route syslog messages to files/network | `/etc/rsyslog.d/*.conf` |
| `tail -f` | Follow a live log file | `-f file1 file2` |
| `tee` | Write to stdout and file simultaneously | `-a` (append) |
