# Lab 11: Cron Jobs and Scheduled Tasks

## 🎯 Objective
Learn to schedule recurring tasks with cron, understand cron syntax, use system cron directories, and capture cron output to logs.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Basic shell scripting knowledge
- Completion of Labs 1–10

## 🔬 Lab Instructions

### Step 1: Verify cron is Running
```bash
systemctl status cron
# ● cron.service - Regular background program processing daemon
#    Loaded: loaded (/lib/systemd/system/cron.service; enabled; ...)
#    Active: active (running) since ...
```

### Step 2: Understand Cron Syntax
Cron entries follow the format: `minute hour day-of-month month day-of-week command`
```bash
# Field ranges:
# Minute    0-59
# Hour      0-23
# Day       1-31
# Month     1-12
# Weekday   0-7  (0 and 7 = Sunday)
# Special: * (any), */n (every n), 1,5 (list), 1-5 (range)
echo "Cron syntax: MIN HOUR DOM MON DOW CMD"
```

### Step 3: Create a Test Script
```bash
cat > ~/cron_test.sh << 'EOF'
#!/bin/bash
echo "Cron ran at: $(date)" >> /tmp/cron_output.log
echo "Hostname: $(hostname)" >> /tmp/cron_output.log
EOF
chmod +x ~/cron_test.sh
```

### Step 4: Edit Your Crontab
```bash
crontab -e
# Add the following line (runs every minute):
# * * * * * /home/$USER/cron_test.sh
# Save and exit (CTRL+X if nano)
```

### Step 5: List Your Crontab
```bash
crontab -l
# * * * * * /home/ubuntu/cron_test.sh
```

### Step 6: Wait and Verify Output
```bash
sleep 65
cat /tmp/cron_output.log
# Cron ran at: Sun Mar  1 06:01:01 UTC 2026
# Hostname: myserver
```

### Step 7: Schedule Realistic Times
```bash
# Examples (view only, add to crontab -e to activate):
# 0 2 * * *   /usr/local/bin/backup.sh        # daily at 2am
# */15 * * * * /usr/local/bin/healthcheck.sh  # every 15 min
# 0 9 * * 1   /usr/local/bin/weekly_report.sh # Mon 9am
echo "Review cron examples above"
```

### Step 8: Use System Cron Directories
```bash
ls /etc/cron.d/
# e2scrub_all  popularity-contest  sysstat

ls /etc/cron.daily/
# apt-compat  dpkg  logrotate  man-db

# Place scripts in these directories for system-wide scheduling
sudo cp ~/cron_test.sh /etc/cron.daily/mytest
sudo chmod 755 /etc/cron.daily/mytest
```

### Step 9: Log Cron Output with Redirection
```bash
crontab -e
# Update the entry to capture both stdout and stderr:
# * * * * * /home/$USER/cron_test.sh >> /tmp/cron_output.log 2>&1
```

### Step 10: Remove the Test Cron Job
```bash
crontab -e
# Delete the test line, save and exit

crontab -l
# (empty or remaining entries)

sudo rm -f /etc/cron.daily/mytest
```

## ✅ Verification
```bash
crontab -l
cat /tmp/cron_output.log
# Confirm at least one successful execution was logged
```

## 📝 Summary
- Cron syntax: minute hour day month weekday command
- `crontab -e` edits your personal crontab; `crontab -l` lists it
- `/etc/cron.daily/`, `/etc/cron.weekly/` run scripts on schedule
- Redirect cron output with `>> logfile 2>&1` to capture errors
- Special strings like `@daily`, `@reboot` are valid shortcuts
