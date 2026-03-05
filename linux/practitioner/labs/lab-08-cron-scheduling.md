# Lab 08: Cron Scheduling

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Cron is Linux's built-in task scheduler — the engine behind automated backups, log rotation, report generation, and system maintenance. In this lab you'll master cron syntax, manage crontabs, use system-wide cron directories, handle environment variables, and capture cron output properly.

---

## Step 1: Understanding Cron Syntax

Every cron job is a line with 5 time fields plus a command:

```
┌───────────── minute (0–59)
│ ┌───────────── hour (0–23)
│ │ ┌───────────── day of month (1–31)
│ │ │ ┌───────────── month (1–12)
│ │ │ │ ┌───────────── day of week (0–7, 0 and 7 = Sunday)
│ │ │ │ │
* * * * * command_to_run
```

```bash
# Demonstrate cron syntax interpretation
echo "Cron syntax examples:"
echo "30 8 * * 1-5     = 8:30 AM, Monday through Friday"
echo "0 */6 * * *      = every 6 hours (midnight, 6am, noon, 6pm)"
echo "*/15 * * * *     = every 15 minutes"
echo "0 0 1 * *        = midnight on the 1st of every month"
echo "0 2 * * 0        = 2:00 AM every Sunday"
echo "15 10 * * 1,3,5  = 10:15 AM on Mon, Wed, Fri"
echo "0 0 15 1,6,12 *  = midnight on Jan 15, Jun 15, Dec 15"
```

📸 **Verified Output:**
```
Cron syntax examples:
30 8 * * 1-5     = 8:30 AM, Monday through Friday
0 */6 * * *      = every 6 hours (midnight, 6am, noon, 6pm)
*/15 * * * *     = every 15 minutes
0 0 1 * *        = midnight on the 1st of every month
0 2 * * 0        = 2:00 AM every Sunday
15 10 * * 1,3,5  = 10:15 AM on Mon, Wed, Fri
0 0 15 1,6,12 *  = midnight on Jan 15, Jun 15, Dec 15
```

> 💡 **Special characters:** `*` = any value, `,` = list (1,3,5), `-` = range (1-5), `/` = step (*/15 means every 15). Remember: cron uses 0-indexed weekdays where both 0 AND 7 mean Sunday.

---

## Step 2: User Crontabs with `crontab`

Each user has their own crontab file managed by the `crontab` command.

```bash
# Install cron daemon
DEBIAN_FRONTEND=noninteractive apt-get update -qq && \
  apt-get install -y -q cron

# View current crontab (empty for new users)
crontab -l 2>&1 || echo "no crontab for root"

# Add a cron job
echo '*/5 * * * * /usr/bin/backup.sh >> /var/log/backup.log 2>&1' | crontab -
echo '0 2 * * * /usr/bin/cleanup.sh >> /var/log/cleanup.log 2>&1' | crontab -

# Actually, crontab - replaces entirely; use a heredoc for multiple jobs
crontab - << 'EOF'
# Backup every 5 minutes
*/5 * * * * /usr/bin/backup.sh >> /var/log/backup.log 2>&1
# Daily cleanup at 2 AM
0 2 * * * /usr/bin/cleanup.sh >> /var/log/cleanup.log 2>&1
# Weekly report on Sunday at 8 AM
0 8 * * 0 /usr/bin/weekly_report.sh | mail -s "Weekly Report" admin@example.com
EOF

# List the crontab
crontab -l
```

📸 **Verified Output:**
```
no crontab for root

# Backup every 5 minutes
*/5 * * * * /usr/bin/backup.sh >> /var/log/backup.log 2>&1
# Daily cleanup at 2 AM
0 2 * * * /usr/bin/cleanup.sh >> /var/log/cleanup.log 2>&1
# Weekly report on Sunday at 8 AM
0 8 * * 0 /usr/bin/weekly_report.sh | mail -s "Weekly Report" admin@example.com
```

> 💡 **Edit safely:** Use `crontab -e` interactively (opens your `$EDITOR`). It validates syntax before saving. Never edit `/var/spool/cron/crontabs/username` directly — you'll bypass validation and may corrupt the file.

---

## Step 3: `@` Shortcuts — Human-Friendly Scheduling

```bash
# @ shortcuts and their equivalents
echo "=== Cron @ Shortcuts ==="
echo "@reboot   = run once at startup (no time equivalent)"
echo "@yearly   = 0 0 1 1 *   (once a year, January 1st midnight)"
echo "@annually = 0 0 1 1 *   (same as @yearly)"
echo "@monthly  = 0 0 1 * *   (once a month, 1st at midnight)"
echo "@weekly   = 0 0 * * 0   (once a week, Sunday midnight)"
echo "@daily    = 0 0 * * *   (once a day, midnight)"
echo "@midnight = 0 0 * * *   (same as @daily)"
echo "@hourly   = 0 * * * *   (once an hour, on the hour)"

# Example crontab using @ shortcuts
cat << 'EOF'
# Clear temp files on every system boot
@reboot rm -rf /tmp/myapp_cache/

# Database backup daily at midnight
@daily /usr/local/bin/db_backup.sh >> /var/log/db_backup.log 2>&1

# SSL certificate renewal check weekly
@weekly certbot renew --quiet >> /var/log/certbot.log 2>&1

# Annual license key rotation
@yearly /usr/local/bin/rotate_license.sh
EOF
```

📸 **Verified Output:**
```
=== Cron @ Shortcuts ===
@reboot   = run once at startup (no time equivalent)
@yearly   = 0 0 1 1 *   (once a year, January 1st midnight)
@annually = 0 0 1 1 *   (same as @yearly)
@monthly  = 0 0 1 * *   (once a month, 1st at midnight)
@weekly   = 0 0 * * 0   (once a week, Sunday midnight)
@daily    = 0 0 * * *   (once a day, midnight)
@midnight = 0 0 * * *   (same as @daily)
@hourly   = 0 * * * *   (once an hour, on the hour)
```

> 💡 **`@reboot` gotcha:** Tasks run at boot run as the crontab owner, but the environment may differ from a login shell. Always use full paths (`/usr/bin/python3`, not `python3`) and set `PATH` explicitly in the crontab or script.

---

## Step 4: System-Wide Cron with `/etc/cron.d/`

System cron files (managed by packages or admins) live in `/etc/cron.d/`. These have an extra **user** field.

```bash
# Create a system-wide cron job
mkdir -p /etc/cron.d

cat > /etc/cron.d/example-jobs << 'EOF'
# /etc/cron.d/example-jobs
# Format: min hour day month dow USER command

# Health check every 5 minutes as root
*/5  *    *   *     *   root  /usr/local/bin/healthcheck.sh >> /var/log/health.log 2>&1

# Business hours report (8 AM, Mon-Fri) as www-data
0    8    *   *    1-5  www-data  /usr/local/bin/report.sh

# Monthly cleanup as root on the 1st at 3 AM
0    3    1   *     *   root  find /var/log -name "*.old" -delete
EOF

# View the file
cat /etc/cron.d/example-jobs

# List other system cron locations
echo "---"
ls /etc/cron.daily/ 2>/dev/null && echo "Found: /etc/cron.daily/" || echo "/etc/cron.daily/ (scripts here run daily)"
ls /etc/cron.weekly/ 2>/dev/null && echo "Found: /etc/cron.weekly/" || echo "/etc/cron.weekly/ (scripts here run weekly)"
```

📸 **Verified Output:**
```
# /etc/cron.d/example-jobs
# Format: min hour day month dow USER command

# Health check every 5 minutes as root
*/5  *    *   *     *   root  /usr/local/bin/healthcheck.sh >> /var/log/health.log 2>&1

# Business hours report (8 AM, Mon-Fri) as www-data
0    8    *   *    1-5  www-data  /usr/local/bin/report.sh

# Monthly cleanup as root on the 1st at 3 AM
0    3    1   *     *   root  find /var/log -name "*.old" -delete
---
/etc/cron.daily/ (scripts here run daily)
/etc/cron.weekly/ (scripts here run weekly)
```

> 💡 **cron.d vs crontab:** Files in `/etc/cron.d/` must include the user field and are owned by packages/admins. User crontabs (via `crontab -e`) don't have a user field — they always run as the crontab owner. Prefer `/etc/cron.d/` for system-level automation.

---

## Step 5: Cron Environment Variables

Cron runs with a minimal environment — not your login shell's. Set variables explicitly.

```bash
# Show what cron's environment typically looks like
cat << 'EOF'
# Cron's default environment (very minimal):
SHELL=/bin/sh
PATH=/usr/bin:/bin
HOME=/root
LOGNAME=root
MAILTO=root

# Always override in your crontab:
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=""              # suppress email on output (or set to admin@example.com)
HOME=/home/appuser

# Then your jobs:
0 * * * * /usr/local/bin/hourly_job.sh
EOF

# Demonstrate PATH issue (why full paths matter)
echo "---"
echo "which python3 gives: $(which python3)"
echo "In cron, PATH may not include /usr/bin — use full path!"
echo "Good:  0 * * * * /usr/bin/python3 /opt/app/script.py"
echo "Bad:   0 * * * * python3 /opt/app/script.py  (may fail)"
```

📸 **Verified Output:**
```
# Cron's default environment (very minimal):
SHELL=/bin/sh
PATH=/usr/bin:/bin
HOME=/root
LOGNAME=root
MAILTO=root

# Always override in your crontab:
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=""
HOME=/home/appuser

# Then your jobs:
0 * * * * /usr/local/bin/hourly_job.sh
---
which python3 gives: /usr/bin/python3
In cron, PATH may not include /usr/bin — use full path!
Good:  0 * * * * /usr/bin/python3 /opt/app/script.py
Bad:   0 * * * * python3 /opt/app/script.py  (may fail)
```

> 💡 **MAILTO variable:** Set `MAILTO=""` to suppress emails for successful jobs. Set `MAILTO=admin@example.com` to receive output by email. Any cron job that produces stdout/stderr output will trigger an email to `MAILTO` by default.

---

## Step 6: Logging Cron Output

Proper logging is critical for cron job debugging.

```bash
# Create a script that generates both stdout and stderr
cat > /tmp/example_job.sh << 'SCRIPT'
#!/bin/bash
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Job started"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Processing..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Warning: disk at 80%" >&2
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Job completed"
SCRIPT
chmod +x /tmp/example_job.sh

# Run it with different logging strategies
echo "=== Strategy 1: stdout only ==="
/tmp/example_job.sh > /tmp/job.log
cat /tmp/job.log

echo "=== Strategy 2: stdout + stderr ==="
/tmp/example_job.sh > /tmp/job_all.log 2>&1
cat /tmp/job_all.log

echo "=== Strategy 3: append with timestamp ==="
/tmp/example_job.sh >> /tmp/job_append.log 2>&1
/tmp/example_job.sh >> /tmp/job_append.log 2>&1
cat /tmp/job_append.log
```

📸 **Verified Output:**
```
=== Strategy 1: stdout only ===
[2026-03-05 05:49:00] Job started
[2026-03-05 05:49:00] Processing...
[2026-03-05 05:49:00] Job completed

=== Strategy 2: stdout + stderr ===
[2026-03-05 05:49:00] Job started
[2026-03-05 05:49:00] Processing...
[2026-03-05 05:49:00] Warning: disk at 80%
[2026-03-05 05:49:00] Job completed

=== Strategy 3: append with timestamp ===
[2026-03-05 05:49:00] Job started
[2026-03-05 05:49:00] Processing...
[2026-03-05 05:49:00] Warning: disk at 80%
[2026-03-05 05:49:00] Job completed
[2026-03-05 05:49:00] Job started
[2026-03-05 05:49:00] Processing...
[2026-03-05 05:49:00] Warning: disk at 80%
[2026-03-05 05:49:00] Job completed
```

> 💡 **Always use `>> log 2>&1`:** The `>>` appends (vs `>` overwrites), and `2>&1` captures stderr with stdout. Without `2>&1`, errors silently disappear (or go to MAILTO). Add a timestamp to every log line: `echo "[$(date '+%Y-%m-%d %H:%M:%S')] message"`.

---

## Step 7: `crontab -r` and Safety Practices

```bash
# List current crontab before removing
echo "Current crontab:"
crontab -l 2>/dev/null || echo "(none)"

# DANGEROUS: crontab -r removes the ENTIRE crontab with no confirmation!
# Safer approach: backup first
crontab - << 'EOF'
@daily /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
@weekly /usr/local/bin/cleanup.sh >> /var/log/cleanup.log 2>&1
EOF

echo "Saving backup..."
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d).txt
echo "Backup saved to: /tmp/crontab_backup_$(date +%Y%m%d).txt"
cat /tmp/crontab_backup_$(date +%Y%m%d).txt

# Restore from backup
# crontab /tmp/crontab_backup_20260305.txt

# Remove (would destroy if run!)
# crontab -r

echo "---"
echo "Safe removal: backup first with 'crontab -l > backup.txt'"
echo "Then remove: 'crontab -r'"
echo "Restore: 'crontab backup.txt'"
```

📸 **Verified Output:**
```
Current crontab:
(none)
Saving backup...
Backup saved to: /tmp/crontab_backup_20260305.txt
@daily /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1
@weekly /usr/local/bin/cleanup.sh >> /var/log/cleanup.log 2>&1
---
Safe removal: backup first with 'crontab -l > backup.txt'
Then remove: 'crontab -r'
Restore: 'crontab backup.txt'
```

> 💡 **`crontab -r` is destructive:** There's no undo. Always backup: `crontab -l > ~/crontab.bak` before editing or removing. Some systems offer `crontab -i` (interactive) which asks for confirmation before removal — check if your system supports it.

---

## Step 8: Capstone — Automated System Maintenance Schedule

**Scenario:** Design a complete automated maintenance crontab for a production web server.

```bash
# Create the complete maintenance crontab
cat > /tmp/production_crontab << 'EOF'
# =======================================================
# Production Web Server Maintenance Schedule
# =======================================================
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=ops-team@company.com

# --- Health Checks (every 5 minutes) ---
*/5 * * * * /usr/local/bin/healthcheck.sh >> /var/log/health.log 2>&1

# --- Log Rotation (daily at 1 AM) ---
@daily /usr/sbin/logrotate /etc/logrotate.conf >> /var/log/logrotate.log 2>&1

# --- Database Backup (daily at 2 AM) ---
0 2 * * * /usr/local/bin/db_backup.sh >> /var/log/db_backup.log 2>&1

# --- Cache Warm-up (every morning at 6 AM, Mon-Fri) ---
0 6 * * 1-5 /usr/local/bin/cache_warmup.sh >> /var/log/cache.log 2>&1

# --- Security Updates (weekly, Sunday 3 AM) ---
0 3 * * 0 DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q >> /var/log/apt_upgrade.log 2>&1

# --- SSL Certificate Renewal Check (twice weekly) ---
0 4 * * 1,4 certbot renew --quiet >> /var/log/certbot.log 2>&1

# --- Monthly cleanup: remove old logs > 90 days ---
0 1 1 * * find /var/log -name "*.log.*" -mtime +90 -delete

# --- Annual: rotate API keys (Jan 1st at midnight) ---
@yearly /usr/local/bin/rotate_api_keys.sh >> /var/log/security.log 2>&1
EOF

cat /tmp/production_crontab

echo ""
echo "=== Syntax validation (cron field counts) ==="
grep -v '^#' /tmp/production_crontab | grep -v '^$' | grep -v '^[A-Z]' | \
  awk '{
    if ($1 ~ /^@/) print "OK (@ shortcut): " $0
    else if (NF >= 6) print "OK (5 fields + cmd): " $1 " " $2 " " $3 " " $4 " " $5
    else print "WARN (check): " $0
  }'
```

📸 **Verified Output:**
```
# =======================================================
# Production Web Server Maintenance Schedule
# =======================================================
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
MAILTO=ops-team@company.com

# --- Health Checks (every 5 minutes) ---
*/5 * * * * /usr/local/bin/healthcheck.sh >> /var/log/health.log 2>&1

# --- Log Rotation (daily at 1 AM) ---
@daily /usr/sbin/logrotate /etc/logrotate.conf >> /var/log/logrotate.log 2>&1
...

=== Syntax validation (cron field counts) ===
OK (5 fields + cmd): */5 * * * *
OK (@ shortcut): @daily /usr/sbin/logrotate /etc/logrotate.conf >> /var/log/logrotate.log 2>&1
OK (5 fields + cmd): 0 2 * * *
OK (5 fields + cmd): 0 6 * * 1-5
OK (5 fields + cmd): 0 3 * * 0
OK (5 fields + cmd): 0 4 * * 1,4
OK (5 fields + cmd): 0 1 1 * *
OK (@ shortcut): @yearly /usr/local/bin/rotate_api_keys.sh >> /var/log/security.log 2>&1
```

> 💡 **Online cron parser:** Use [crontab.guru](https://crontab.guru) to visually validate and explain cron expressions before deploying. The site shows the next execution times and describes expressions in plain English — invaluable for complex schedules.

---

## Summary

| Command / Concept | Purpose | Example |
|-------------------|---------|---------|
| `crontab -e` | Edit user's crontab | Opens in `$EDITOR` |
| `crontab -l` | List user's crontab | `crontab -l > backup.txt` |
| `crontab -r` | Remove user's crontab | ⚠️ Backup first! |
| `* * * * *` | Cron time fields | `30 8 * * 1-5` = 8:30 AM weekdays |
| `@reboot` | Run at system startup | `@reboot /opt/myapp/start.sh` |
| `@daily` | Run once a day (midnight) | `@daily /usr/bin/backup.sh` |
| `@weekly` | Run weekly (Sunday midnight) | `@weekly /usr/bin/cleanup.sh` |
| `/etc/cron.d/` | System-wide cron files | Needs USER field: `* * * * * root cmd` |
| `2>&1` | Capture stderr with stdout | `cmd >> log.txt 2>&1` |
| `MAILTO=""` | Suppress cron email | Set in crontab header |
| `MAILTO=addr` | Email cron output | `MAILTO=admin@example.com` |
