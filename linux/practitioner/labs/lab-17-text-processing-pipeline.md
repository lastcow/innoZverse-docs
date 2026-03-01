# Lab 17: Text Processing Pipelines

## 🎯 Objective
Combine `grep`, `sed`, and `awk` into powerful pipelines for real-world log parsing and data transformation.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Labs 1–3 (grep, awk, sed basics)

## 🔬 Lab Instructions

### Step 1: Generate Sample Log Data
```bash
cat > /tmp/app.log << 'EOF'
2026-03-01 06:00:01 INFO  [web] GET /index.html 200 0.023s
2026-03-01 06:00:02 ERROR [db]  Connection timeout after 30s
2026-03-01 06:00:03 INFO  [web] GET /api/users 200 0.145s
2026-03-01 06:00:04 WARN  [web] Rate limit exceeded for 10.0.0.5
2026-03-01 06:00:05 ERROR [api] Null pointer exception in UserService
2026-03-01 06:00:06 INFO  [web] POST /api/login 401 0.012s
2026-03-01 06:00:07 INFO  [web] GET /api/data 200 1.234s
2026-03-01 06:00:08 ERROR [db]  Query timeout: SELECT * FROM orders
2026-03-01 06:00:09 INFO  [web] GET /health 200 0.001s
2026-03-01 06:00:10 WARN  [auth] Failed login attempt from 10.0.0.99
EOF
echo "Log created with $(wc -l < /tmp/app.log) lines"
# Log created with 10 lines
```

### Step 2: Filter and Count by Log Level
```bash
grep -oE '(INFO|WARN|ERROR)' /tmp/app.log | sort | uniq -c | sort -rn
#       5 INFO
#       3 ERROR
#       2 WARN
```

### Step 3: Extract Only Error Lines
```bash
grep 'ERROR' /tmp/app.log
# 2026-03-01 06:00:02 ERROR [db]  Connection timeout after 30s
# 2026-03-01 06:00:05 ERROR [api] Null pointer exception in UserService
# 2026-03-01 06:00:08 ERROR [db]  Query timeout: SELECT * FROM orders
```

### Step 4: grep | awk — Extract Fields from Matches
```bash
# Extract timestamp and component from ERROR lines
grep 'ERROR' /tmp/app.log | awk '{print $1, $2, $4, substr($0, index($0,$5))}'
# 2026-03-01 06:00:02 [db]  Connection timeout after 30s
# 2026-03-01 06:00:05 [api] Null pointer exception in UserService
# 2026-03-01 06:00:08 [db]  Query timeout: SELECT * FROM orders
```

### Step 5: sed — Clean and Transform Output
```bash
# Remove brackets from component names
grep 'ERROR' /tmp/app.log | sed 's/\[//g; s/\]//g'
# 2026-03-01 06:00:02 ERROR db   Connection timeout after 30s

# Replace ERROR with CRITICAL in output stream
grep 'ERROR' /tmp/app.log | sed 's/ERROR/CRITICAL/g'
# 2026-03-01 06:00:02 CRITICAL [db]  Connection timeout after 30s
```

### Step 6: Full Pipeline — HTTP Status Summary
```bash
# Extract HTTP status codes from web logs and count
grep '\[web\]' /tmp/app.log \
  | grep -oE '[1-5][0-9]{2} [0-9]+\.[0-9]+s' \
  | awk '{count[$1]++} END {for (s in count) print s, count[s]}' \
  | sort
# 200 4
# 401 1
```

### Step 7: awk — Response Time Statistics
```bash
# Average response time for INFO requests
grep 'INFO' /tmp/app.log | awk '
{
    if (match($0, /([0-9]+\.[0-9]+)s$/, arr)) {
        sum += arr[1]
        count++
    }
}
END {
    if (count > 0) printf "Requests: %d  Avg time: %.3fs\n", count, sum/count
}'
# Requests: 5  Avg time: 0.281s
```

### Step 8: Multi-Stage Pipeline — Error Component Report
```bash
echo "=== Error Report ==="
grep 'ERROR' /tmp/app.log \
  | sed 's/\[//g; s/\]//g' \
  | awk '{print $4}' \
  | sort | uniq -c | sort -rn \
  | awk '{printf "  Count: %-3s  Component: %s\n", $1, $2}'
# === Error Report ===
#   Count: 2    Component: db
#   Count: 1    Component: api
```

### Step 9: Extract and Deduplicate IPs
```bash
grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' /tmp/app.log \
  | sort -u
# 10.0.0.5
# 10.0.0.99
```

### Step 10: Build a Log Summary Script
```bash
cat > ~/log_summary.sh << 'EOF'
#!/bin/bash
set -euo pipefail
LOG="${1:-/tmp/app.log}"
[[ -f "$LOG" ]] || { echo "Log not found: $LOG" >&2; exit 1; }

echo "=== Log Summary: $LOG ==="
echo "Total lines : $(wc -l < "$LOG")"
echo ""
echo "By Level:"
grep -oE '(INFO|WARN|ERROR)' "$LOG" \
  | sort | uniq -c | sort -rn \
  | awk '{printf "  %-6s %s\n", $2, $1}'
echo ""
echo "Errors:"
grep 'ERROR' "$LOG" \
  | sed 's/\[//g; s/\]//g' \
  | awk '{print "  " $1, $2, $4, substr($0, index($0,$5))}'
echo ""
echo "Unique IPs:"
grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' "$LOG" \
  | sort -u \
  | awk '{print "  " $0}'
EOF
chmod +x ~/log_summary.sh
~/log_summary.sh /tmp/app.log
# === Log Summary: /tmp/app.log ===
# Total lines : 10
# ...
```

## ✅ Verification
```bash
grep 'WARN' /tmp/app.log | awk '{print NR, $3, $4}' | sed 's/\[//g; s/\]//g'
# 1 WARN web
# 2 WARN auth
```

## 📝 Summary
- Chain `grep | awk | sed | sort | uniq` for powerful log analysis
- `grep -oE 'pattern'` extracts only the matching text
- `awk` can accumulate statistics across lines with associative arrays
- `sed` is best for line-by-line text substitution and cleanup
- Build reusable pipeline scripts that accept filenames as arguments
