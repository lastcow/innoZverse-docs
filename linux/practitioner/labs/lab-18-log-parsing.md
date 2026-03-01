# Lab 18: Log Parsing — SSH Auth Log Analysis

## 🎯 Objective
Parse `/var/log/auth.log` (or a simulated version) to extract failed login IPs, count occurrences, identify brute force patterns, and generate a security report.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Labs 1–3 and Lab 17

## 🔬 Lab Instructions

### Step 1: Examine Auth Log Structure
```bash
sudo tail -10 /var/log/auth.log 2>/dev/null || echo "Using simulation"

# Create a realistic simulation
cat > /tmp/auth.log.sim << 'EOF'
Mar  1 05:58:01 server sshd[1234]: Failed password for root from 203.0.113.10 port 45231 ssh2
Mar  1 05:58:03 server sshd[1234]: Failed password for admin from 203.0.113.10 port 45232 ssh2
Mar  1 05:58:22 server sshd[1235]: Accepted publickey for ubuntu from 10.0.0.5 port 52100 ssh2
Mar  1 05:59:01 server sshd[1236]: Failed password for root from 198.51.100.42 port 33891 ssh2
Mar  1 05:59:11 server sshd[1236]: Failed password for root from 198.51.100.42 port 33892 ssh2
Mar  1 05:59:21 server sshd[1236]: Failed password for root from 198.51.100.42 port 33893 ssh2
Mar  1 06:00:01 server sshd[1237]: Failed password for ubuntu from 203.0.113.10 port 45250 ssh2
Mar  1 06:00:15 server sshd[1238]: Accepted password for deploy from 10.0.0.10 port 41000 ssh2
Mar  1 06:01:00 server sshd[1239]: Failed password for pi from 192.0.2.77 port 12345 ssh2
Mar  1 06:01:10 server sshd[1239]: Failed password for pi from 192.0.2.77 port 12346 ssh2
Mar  1 06:01:20 server sshd[1240]: Invalid user admin from 203.0.113.10 port 45260
Mar  1 06:02:00 server sshd[1241]: Accepted publickey for alice from 10.0.0.20 port 55001 ssh2
EOF
echo "Simulation log: $(wc -l < /tmp/auth.log.sim) lines"
```

### Step 2: Count Failed Logins
```bash
LOG=/tmp/auth.log.sim
grep -c 'Failed password' "$LOG"
# 8
```

### Step 3: Extract Source IPs from Failed Logins
```bash
grep 'Failed password' "$LOG" \
  | grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' \
  | awk '{print $2}'
# 203.0.113.10
# 203.0.113.10
# 198.51.100.42
# 198.51.100.42
# 198.51.100.42
# 203.0.113.10
# 192.0.2.77
# 192.0.2.77
```

### Step 4: Count Failures per IP
```bash
grep 'Failed password' "$LOG" \
  | grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' \
  | awk '{print $2}' \
  | sort | uniq -c | sort -rn
#       3 198.51.100.42
#       3 203.0.113.10
#       2 192.0.2.77
```

### Step 5: Extract Targeted Usernames
```bash
grep 'Failed password' "$LOG" \
  | awk '{print $9}' \
  | sort | uniq -c | sort -rn
#       5 root
#       2 pi
#       1 ubuntu
#       1 admin
```

### Step 6: Find Successful Logins
```bash
grep 'Accepted' "$LOG" | awk '{print $9, "from", $11, "method:", $8}' | sort -u
# alice from 10.0.0.20 method: publickey
# deploy from 10.0.0.10 method: password
# ubuntu from 10.0.0.5 method: publickey
```

### Step 7: Identify Invalid User Attempts
```bash
grep 'Invalid user' "$LOG" \
  | awk '{print "User:", $10, "from IP:", $12}' \
  | sort | uniq -c | sort -rn
#       1 User: admin from IP: 203.0.113.10
```

### Step 8: Find Brute Force Candidates (more than 2 failures)
```bash
THRESHOLD=2
grep 'Failed password' "$LOG" \
  | grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' \
  | awk '{print $2}' \
  | sort | uniq -c | sort -rn \
  | awk -v t="$THRESHOLD" '$1 > t {print "BRUTE FORCE:", $2, "(" $1 " attempts)"}'
# BRUTE FORCE: 198.51.100.42 (3 attempts)
# BRUTE FORCE: 203.0.113.10 (3 attempts)
```

### Step 9: Timeline for a Specific IP
```bash
TARGET="198.51.100.42"
echo "=== Timeline for $TARGET ==="
grep "$TARGET" "$LOG" | awk '{print $1, $2, $3, $6, $7, $8, $9}'
# Mar 1 05:59:01 Failed password for root
# Mar 1 05:59:11 Failed password for root
# Mar 1 05:59:21 Failed password for root
```

### Step 10: Full Security Report Script
```bash
cat > ~/auth_report.sh << 'EOF'
#!/bin/bash
set -euo pipefail
LOG="${1:-/var/log/auth.log}"
[[ -f "$LOG" ]] || { echo "Log not found: $LOG" >&2; exit 1; }
THRESHOLD=3

echo "======================================="
echo " SSH Auth Security Report"
echo " Log  : $LOG"
echo " Date : $(date)"
echo "======================================="

echo ""
echo "--- Failed Login Summary ---"
total=$(grep -c 'Failed password' "$LOG" || echo 0)
echo "Total failed attempts: $total"

echo ""
echo "--- Top Attacking IPs ---"
grep 'Failed password' "$LOG" \
  | grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' \
  | awk '{print $2}' \
  | sort | uniq -c | sort -rn | head -10 \
  | awk '{printf "  %-18s %s attempts\n", $2, $1}'

echo ""
echo "--- Brute Force Candidates (>$THRESHOLD attempts) ---"
grep 'Failed password' "$LOG" \
  | grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' \
  | awk '{print $2}' \
  | sort | uniq -c | sort -rn \
  | awk -v t="$THRESHOLD" '$1 > t {print "  ALERT:", $2, "(" $1 " attempts)"}'

echo ""
echo "--- Targeted Usernames ---"
grep 'Failed password' "$LOG" | awk '{print $9}' \
  | sort | uniq -c | sort -rn | head -5 \
  | awk '{printf "  %-15s %s times\n", $2, $1}'

echo ""
echo "--- Successful Logins ---"
grep 'Accepted' "$LOG" \
  | awk '{print "  " $9, "from", $11, "at", $1, $2, $3}' | sort -u
EOF
chmod +x ~/auth_report.sh
~/auth_report.sh /tmp/auth.log.sim
```

## ✅ Verification
```bash
grep -c 'Failed password' /tmp/auth.log.sim   # 8
grep -c 'Accepted' /tmp/auth.log.sim           # 3
~/auth_report.sh /tmp/auth.log.sim | grep "Total failed"
# Total failed attempts: 8
```

## 📝 Summary
- `grep 'Failed password'` filters SSH brute force attempts from auth.log
- `grep -oE 'from IP_REGEX'` extracts just the attacker IP addresses
- `sort | uniq -c | sort -rn` counts and ranks occurrences
- Combine `grep + awk + sort + uniq` into complete security report pipelines
- In production, use `sudo cat /var/log/auth.log` or `sudo journalctl -u ssh`
