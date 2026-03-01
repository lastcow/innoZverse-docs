# Lab 18: Log Parsing

## 🎯 Objective
Create sample log files and build pipelines to extract patterns, count occurrences, and generate a top IPs report.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Practitioner Labs 1 (grep advanced), 2 (awk), 4 (cut/sort/uniq)

## 🔬 Lab Instructions

### Step 1: Create a Sample Log File

```bash
cat > /tmp/access.log << 'EOF'
192.168.1.10 - alice [01/Mar/2026:10:00:01 +0000] "GET /index.html HTTP/1.1" 200 1024
192.168.1.20 - bob [01/Mar/2026:10:00:15 +0000] "GET /api/users HTTP/1.1" 200 2048
192.168.1.10 - alice [01/Mar/2026:10:01:00 +0000] "POST /api/login HTTP/1.1" 200 512
10.0.0.5 - - [01/Mar/2026:10:01:30 +0000] "GET /admin HTTP/1.1" 403 256
192.168.1.30 - carol [01/Mar/2026:10:02:00 +0000] "GET /api/products HTTP/1.1" 200 4096
192.168.1.10 - alice [01/Mar/2026:10:02:30 +0000] "GET /api/orders HTTP/1.1" 200 8192
10.0.0.5 - - [01/Mar/2026:10:03:00 +0000] "POST /admin/users HTTP/1.1" 403 256
192.168.1.20 - bob [01/Mar/2026:10:03:30 +0000] "DELETE /api/users/5 HTTP/1.1" 204 0
192.168.1.40 - dave [01/Mar/2026:10:04:00 +0000] "GET /api/products HTTP/1.1" 200 4096
192.168.1.10 - alice [01/Mar/2026:10:04:30 +0000] "GET /api/stats HTTP/1.1" 200 1536
10.0.0.5 - - [01/Mar/2026:10:05:00 +0000] "GET /etc/passwd HTTP/1.1" 404 128
192.168.1.30 - carol [01/Mar/2026:10:05:30 +0000] "PUT /api/products/1 HTTP/1.1" 200 1024
192.168.1.20 - bob [01/Mar/2026:10:06:00 +0000] "GET /api/orders HTTP/1.1" 404 256
192.168.1.50 - - [01/Mar/2026:10:06:30 +0000] "GET /index.html HTTP/1.1" 200 1024
192.168.1.10 - alice [01/Mar/2026:10:07:00 +0000] "POST /api/orders HTTP/1.1" 201 512
EOF

wc -l /tmp/access.log
```

### Step 2: Extract Basic Patterns

```bash
# Count requests by status code
echo "=== Status Code Distribution ==="
awk '{ print $9 }' /tmp/access.log | sort | uniq -c | sort -rn
```

**Expected output:**
```
     10 200
      2 403
      1 201
      1 204
      1 404
```

```bash
# Find all 4xx and 5xx errors
echo "=== Error Requests ==="
awk '$9 >= 400 { print $0 }' /tmp/access.log
```

### Step 3: Top IP Addresses Report

```bash
echo "=== Top IP Addresses ==="
awk '{ print $1 }' /tmp/access.log | sort | uniq -c | sort -rn
```

**Expected output:**
```
      5 192.168.1.10
      3 10.0.0.5
      3 192.168.1.20
      2 192.168.1.30
      1 192.168.1.40
      1 192.168.1.50
```

```bash
# Flag suspicious IPs (403 errors)
echo "=== IPs with 403 Errors ==="
awk '$9 == 403 { print $1 }' /tmp/access.log | sort | uniq -c | sort -rn
```

### Step 4: Time-Based Analysis

```bash
# Count requests per minute
echo "=== Requests per Minute ==="
awk '{ match($4, /[0-9]{2}:[0-9]{2}:[0-9]{2}/); print substr($4, RSTART, 5) }' /tmp/access.log | sort | uniq -c
```

```bash
# Requests per hour
echo "=== Requests per Hour ==="
awk '{ match($4, /[0-9]{2}:[0-9]{2}/); print substr($4, RSTART, 5) }' /tmp/access.log | cut -c1-3 | sort | uniq -c
```

### Step 5: Traffic Volume Analysis

```bash
# Total bytes transferred
echo "=== Total Bytes Transferred ==="
awk '{ sum += $10 } END { printf "Total: %d bytes (%.2f KB)\n", sum, sum/1024 }' /tmp/access.log
```

```bash
# Bytes per IP
echo "=== Bytes per IP ==="
awk '{ bytes[$1] += $10 } END { for (ip in bytes) printf "%15s: %7d bytes\n", ip, bytes[ip] }' /tmp/access.log | sort -k2 -rn
```

### Step 6: HTTP Method Analysis

```bash
echo "=== HTTP Method Distribution ==="
awk '{ gsub(/"/, "", $6); print $6 }' /tmp/access.log | sort | uniq -c | sort -rn
```

**Expected output:**
```
      9 GET
      3 POST
      2 PUT
      1 DELETE
```

### Step 7: Full Log Analysis Script

```bash
cat > /tmp/log-analyzer.sh << 'EOF'
#!/bin/bash
LOG="${1:-/tmp/access.log}"

[[ -f "$LOG" ]] || { echo "Log file not found: $LOG"; exit 1; }

echo "================================================"
echo "  LOG ANALYSIS REPORT"
echo "  File: $LOG"
echo "  Lines: $(wc -l < "$LOG")"
echo "================================================"

echo ""
echo "--- Top 5 IP Addresses ---"
awk '{ print $1 }' "$LOG" | sort | uniq -c | sort -rn | head -5 | awk '{ printf "  %5d requests from %s\n", $1, $2 }'

echo ""
echo "--- Status Code Summary ---"
awk '{ print $9 }' "$LOG" | sort | uniq -c | sort -rn | awk '{ printf "  %5d  HTTP %s\n", $1, $2 }'

echo ""
echo "--- Total Bytes Served ---"
awk '{ sum += $10 } END { printf "  %d bytes (%.2f KB)\n", sum, sum/1024 }' "$LOG"

echo ""
echo "--- Error Requests (4xx) ---"
awk '$9 >= 400 && $9 < 500 { print "  " $1, $6, $7, "->", $9 }' "$LOG"
EOF

bash /tmp/log-analyzer.sh
```

### Step 8: Parse System Logs

```bash
# Parse journald for SSH events
journalctl -n 50 --no-pager 2>/dev/null | grep -i "ssh\|sshd" | head -10 || echo "No recent SSH events"
```

```bash
# Count events by hour from journald
journalctl --no-pager --since "1 hour ago" 2>/dev/null | awk '{ print $3 }' | cut -c1-2 | sort | uniq -c | head -5
```

## ✅ Verification

```bash
echo "=== Total log lines ===" && wc -l < /tmp/access.log
echo "=== Top IP ===" && awk '{ print $1 }' /tmp/access.log | sort | uniq -c | sort -rn | head -1
echo "=== Error count ===" && awk '$9 >= 400' /tmp/access.log | wc -l
echo "=== 200 count ===" && awk '$9 == 200' /tmp/access.log | wc -l
rm /tmp/access.log /tmp/log-analyzer.sh 2>/dev/null
echo "Practitioner Lab 18 complete"
```

## 📝 Summary
- `awk '{ print $1 }' log | sort | uniq -c | sort -rn` generates frequency reports
- `awk '$9 >= 400'` filters by numeric field value (status codes)
- `awk '{ sum += $10 } END { print sum }'` calculates running totals
- Build log parsers incrementally: extract, filter, count, format
- Associative arrays in awk (`bytes[$1] += $10`) aggregate data by key
- Use `journalctl --no-pager` to read system logs programmatically
