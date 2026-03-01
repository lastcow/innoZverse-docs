# Lab 11: Cron Jobs

## 🎯 Objective
Understand cron syntax, view existing crontabs, write cron entries to a file, and explore the cron.d directory structure.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Practitioner Lab 10: Script Arguments

## 🔬 Lab Instructions

### Step 1: View Existing Crontab

```bash
# List current user's crontab (may be empty)
crontab -l 2>/dev/null || echo "No crontab for $(whoami)"
```

### Step 2: Understand Cron Syntax

```bash
# Cron field format:
# MIN HOUR DAY_OF_MONTH MONTH DAY_OF_WEEK COMMAND
# *   *    *            *     *
# |   |    |            |     |
# |   |    |            |     +-- Day of week (0-7, 0 and 7 = Sunday)
# |   |    |            +-------- Month (1-12)
# |   |    +---------------------- Day of month (1-31)
# |   +--------------------------- Hour (0-23)
# +------------------------------- Minute (0-59)

cat > /tmp/cron-examples.txt << 'EOF'
# Run every minute
* * * * * /path/to/script.sh

# Run every hour at minute 0
0 * * * * /path/to/script.sh

# Run daily at 2:30 AM
30 2 * * * /path/to/script.sh

# Run every Monday at 8:00 AM
0 8 * * 1 /path/to/script.sh

# Run on 1st of every month at midnight
0 0 1 * * /path/to/script.sh

# Run every 5 minutes
*/5 * * * * /path/to/script.sh

# Run at 9am on weekdays (Mon-Fri)
0 9 * * 1-5 /path/to/script.sh

# Run at 8am, 12pm, and 6pm
0 8,12,18 * * * /path/to/script.sh
EOF

cat /tmp/cron-examples.txt
```

### Step 3: Write a Crontab Entry to /tmp

```bash
# Generate a valid crontab file (written to /tmp, not installed)
cat > /tmp/my-crontab.txt << 'EOF'
# Custom crontab for zchen
# Backup home directory daily at 1:00 AM
0 1 * * * tar -czf /tmp/home-backup-$(date +\%Y\%m\%d).tar.gz $HOME --exclude=$HOME/.cache 2>/dev/null

# Clean /tmp files older than 7 days, every Sunday at midnight
0 0 * * 0 find /tmp -maxdepth 1 -mtime +7 -delete 2>/dev/null

# Log disk usage every hour
0 * * * * df -h / >> /tmp/disk-usage.log 2>/dev/null

# Run health check every 5 minutes
*/5 * * * * /home/zchen/scripts/health-check.sh >> /tmp/health.log 2>&1
EOF

cat /tmp/my-crontab.txt
echo ""
echo "Number of cron entries: $(grep -v '^#' /tmp/my-crontab.txt | grep -v '^$' | wc -l)"
```

### Step 4: Explore /etc/cron.d Structure

```bash
ls /etc/cron.d/ 2>/dev/null | head -10
```

```bash
# View an existing cron.d file (if any)
ls /etc/cron.d/ 2>/dev/null && head -20 /etc/cron.d/$(ls /etc/cron.d/ | head -1) 2>/dev/null || echo "No cron.d files"
```

```bash
# Cron directories for specific frequencies
ls /etc/cron.hourly/ 2>/dev/null | head -5
ls /etc/cron.daily/ 2>/dev/null | head -5
ls /etc/cron.weekly/ 2>/dev/null | head -5
ls /etc/cron.monthly/ 2>/dev/null | head -5
```

### Step 5: Cron Job Best Practices

```bash
cat > /tmp/cron-best-practices.txt << 'EOF'
CRON BEST PRACTICES:

1. ALWAYS redirect output:
   */5 * * * * /script.sh >> /var/log/script.log 2>&1

2. Use FULL PATHS for commands:
   0 * * * * /usr/bin/find /tmp -mtime +1 -delete

3. Set PATH explicitly in crontab:
   PATH=/usr/local/bin:/usr/bin:/bin

4. Use MAILTO to disable email:
   MAILTO=""

5. Test the script manually first:
   bash -x /path/to/script.sh

6. Validate cron syntax before installing:
   Use: https://crontab.guru

7. Use flock to prevent overlapping runs:
   */5 * * * * /usr/bin/flock -n /tmp/script.lock /path/to/script.sh
EOF

cat /tmp/cron-best-practices.txt
```

### Step 6: Special Cron Strings

```bash
cat > /tmp/cron-special.txt << 'EOF'
# Special strings (not all cron implementations support these):
@reboot     Run once at startup
@hourly     Same as: 0 * * * *
@daily      Same as: 0 0 * * *
@weekly     Same as: 0 0 * * 0
@monthly    Same as: 0 0 1 * *
@yearly     Same as: 0 0 1 1 *

# Examples:
@reboot     /path/to/startup-script.sh
@daily      /path/to/daily-backup.sh
EOF

cat /tmp/cron-special.txt
```

### Step 7: systemd Timer Alternative

```bash
# Modern alternative to cron: systemd timers
systemctl list-timers --no-pager 2>/dev/null | head -15
```

## ✅ Verification

```bash
echo "=== crontab check ===" && crontab -l 2>/dev/null || echo "No crontab"
echo "=== cron entries in /tmp ===" && grep -v "^#" /tmp/my-crontab.txt | grep -v "^$" | wc -l
echo "=== cron directories ===" && ls /etc/cron.d/ 2>/dev/null | wc -l
rm /tmp/my-crontab.txt /tmp/cron-examples.txt /tmp/cron-best-practices.txt /tmp/cron-special.txt 2>/dev/null
echo "Practitioner Lab 11 complete"
```

## 📝 Summary
- Cron format: `MIN HOUR DOM MONTH DOW COMMAND` (5 time fields + command)
- `*` means "every"; `*/5` means "every 5"; `1-5` means range; `1,3,5` means list
- `crontab -l` lists current crontab; `crontab -e` edits it interactively
- Always use full paths in cron commands; always redirect output
- `/etc/cron.d/` contains system cron jobs; `/etc/cron.daily/` has daily scripts
- `@daily`, `@weekly`, `@reboot` are convenient shorthand strings
