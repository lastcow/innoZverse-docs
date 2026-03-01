# Lab 20: Automation Project — System Health Report

## 🎯 Objective
Build a complete, production-quality system health report script that checks CPU, memory, disk, top processes, services, and network, outputting a timestamped formatted report.

## ⏱️ Estimated Time
50 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Labs 11–19

## 🔬 Lab Instructions

### Step 1: Plan the Health Report
```bash
# Our script will collect:
# 1. System uptime and load averages
# 2. CPU usage and top processes
# 3. Memory usage summary
# 4. Disk usage with alerts
# 5. Network interface status
# 6. Failed systemd services
# 7. Recent auth failures

mkdir -p ~/health_report/reports
echo "Project directory ready"
```

### Step 2: Uptime and Load Average
```bash
uptime
#  06:01:23 up 2 days, 14:22,  1 user,  load average: 0.08, 0.05, 0.01

# Structured extraction
uptime | awk '{
    for(i=1;i<=NF;i++) {
        if($i=="average:") {
            print "Load 1m:", $(i+1), "5m:", $(i+2), "15m:", $(i+3)
        }
    }
}'
# Load 1m: 0.08, 5m: 0.05, 15m: 0.01
```

### Step 3: CPU Usage
```bash
# CPU summary from top
top -bn1 | grep '%Cpu'
# %Cpu(s):  3.0 us,  1.0 sy,  0.0 ni, 95.0 id,  1.0 wa,  0.0 hi,  0.0 si,  0.0 st

# Top 5 CPU processes
ps aux --sort=-%cpu | awk 'NR>1 && NR<=6 {printf "  %-20s CPU: %s%%\n", $11, $3}'
#   /usr/bin/python3     CPU: 2.1%
#   /usr/sbin/sshd      CPU: 0.1%
```

### Step 4: Memory Usage
```bash
free -h
#               total        used        free      shared  buff/cache   available
# Mem:          1.9Gi       456Mi       823Mi       1.0Mi       706Mi       1.4Gi

free -m | awk '/^Mem:/{
    pct = int($3/$2*100)
    printf "Memory: %dMB total, %dMB used (%d%%), %dMB available\n",
    $2, $3, pct, $7
}'
# Memory: 1987MB total, 456MB used (22%), 1434MB available
```

### Step 5: Disk Usage with Alerts
```bash
df -h --output=source,size,used,avail,pcent,target | grep -v tmpfs | grep -v udev
# Filesystem      Size  Used Avail Use% Mounted on
# /dev/sda1        20G  4.2G   15G  23% /

# Alert check
THRESHOLD=80
df --output=pcent,target | grep -v Use | while read pct mount; do
    num=${pct%%%}
    if [[ "$num" -gt "$THRESHOLD" ]]; then
        echo "DISK ALERT: $mount is ${pct} full!"
    fi
done
```

### Step 6: Network Status
```bash
ip -brief addr show
# lo               UNKNOWN        127.0.0.1/8
# eth0             UP             10.0.0.5/24

ip route show default
# default via 10.0.0.1 dev eth0 proto dhcp src 10.0.0.5 metric 100
```

### Step 7: Failed Services Check
```bash
systemctl --failed --no-legend 2>/dev/null | head -5
# (empty if all OK)

failed_count=$(systemctl --failed --no-legend 2>/dev/null | wc -l)
echo "Failed services: $failed_count"
# Failed services: 0
```

### Step 8: Auth Failures Check
```bash
if [[ -r /var/log/auth.log ]]; then
    fails=$(grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0)
elif command -v journalctl &>/dev/null; then
    fails=$(journalctl -u ssh --since "24 hours ago" --no-pager 2>/dev/null \
            | grep -c 'Failed' 2>/dev/null || echo 0)
else
    fails="N/A"
fi
echo "Auth failures (24h): $fails"
```

### Step 9: Assemble the Full Health Report Script
```bash
cat > ~/health_report/health_report.sh << 'SCRIPT'
#!/bin/bash
set -euo pipefail

REPORT_DIR="$HOME/health_report/reports"
mkdir -p "$REPORT_DIR"
REPORT="$REPORT_DIR/health_$(date +%Y%m%d_%H%M%S).txt"
DISK_THRESHOLD=80

divider() { printf '%0.s=' {1..55}; echo; }
section() { echo ""; divider; echo "  $1"; divider; }

{
echo "SYSTEM HEALTH REPORT"
echo "Generated : $(date)"
echo "Hostname  : $(hostname -f 2>/dev/null || hostname)"
echo "Kernel    : $(uname -r)"
echo "OS        : $(lsb_release -ds 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')"

section "UPTIME AND LOAD"
uptime

section "CPU"
top -bn1 | grep '%Cpu' || true
echo ""
echo "Top 5 CPU-consuming processes:"
ps aux --sort=-%cpu | awk 'NR>1 && NR<=6 {printf "  %-8s %5s%%  %s\n", $1, $3, $11}'

section "MEMORY"
free -h
echo ""
free -m | awk '/^Mem:/{
    pct = int($3/$2*100)
    printf "  Used %d%% of %dMB total (%dMB available)\n", pct, $2, $7
}'

section "DISK USAGE"
df -h --output=source,size,used,avail,pcent,target | grep -v tmpfs | grep -v udev

alerts=$(df --output=pcent,target | grep -v Use | while read pct mount; do
    num=${pct%%%}
    [[ "$num" -gt "$DISK_THRESHOLD" ]] && echo "  ALERT: $mount is $pct full"
done)
if [[ -n "$alerts" ]]; then
    echo ""
    echo "Disk Alerts:"
    echo "$alerts"
fi

section "NETWORK"
ip -brief addr show
echo ""
echo "Default route:"
ip route show default 2>/dev/null || echo "  (none)"

section "SYSTEMD SERVICES"
echo "Failed services:"
systemctl --failed --no-legend 2>/dev/null | head -10 || echo "  None"

section "AUTH FAILURES (24h)"
if [[ -r /var/log/auth.log ]]; then
    fails=$(grep -c 'Failed password' /var/log/auth.log 2>/dev/null || echo 0)
    echo "Failed SSH attempts: $fails"
    if [[ "$fails" -gt 0 ]]; then
        echo "Top attacking IPs:"
        grep 'Failed password' /var/log/auth.log \
          | grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' \
          | awk '{print $2}' \
          | sort | uniq -c | sort -rn | head -5 \
          | awk '{printf "  %-15s %s attempts\n", $2, $1}'
    fi
else
    echo "  (auth.log not readable — run as root for details)"
fi

section "REPORT SAVED"
echo "File: $REPORT"

} | tee "$REPORT"
SCRIPT
chmod +x ~/health_report/health_report.sh
echo "Script ready"
```

### Step 10: Run and Schedule
```bash
~/health_report/health_report.sh
ls ~/health_report/reports/
# health_20260301_060123.txt

# Schedule daily at 7am
(crontab -l 2>/dev/null; echo "0 7 * * * $HOME/health_report/health_report.sh >> $HOME/health_report/cron.log 2>&1") | crontab -
crontab -l | grep health_report
# 0 7 * * * /home/ubuntu/health_report/health_report.sh >> ...
```

## ✅ Verification
```bash
ls -la ~/health_report/reports/
grep "SYSTEM HEALTH REPORT" ~/health_report/reports/*.txt
# SYSTEM HEALTH REPORT
crontab -l | grep health_report
# 0 7 * * * ...
```

## 📝 Summary
- Combined `uptime`, `top`, `free`, `df`, `ip`, `systemctl` into a structured report
- Used `tee` to write to both terminal and timestamped report file simultaneously
- Applied string manipulation, conditionals, and functions from earlier labs
- Scheduled the report with cron for daily automated execution
- This script is a production-ready template for infrastructure monitoring
