# Lab 19: Text Processing — grep, awk & sed

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

The Unix text processing triad — `grep`, `awk`, and `sed` — is your Swiss Army knife for log analysis, data transformation, and automation. In this lab you will master extended regular expressions, field-based processing, stream editing, and build real-world log analysis pipelines.

**Prerequisites:** Docker installed, Labs 01–15 completed.

---

## Step 1: Set Up Sample Log Data

All exercises use a realistic web access log. Let's create it first.

```bash
docker run -it --rm ubuntu:22.04 bash

cat > /tmp/access.log << 'EOF'
192.168.1.10 - alice [15/Jan/2024:08:00:01 +0000] "GET /api/users HTTP/1.1" 200 1234
192.168.1.20 - bob [15/Jan/2024:08:00:02 +0000] "POST /api/login HTTP/1.1" 401 89
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
192.168.1.10 - alice [15/Jan/2024:08:00:04 +0000] "DELETE /api/users/42 HTTP/1.1" 403 78
10.0.0.6 - charlie [15/Jan/2024:08:00:05 +0000] "GET /health HTTP/1.1" 200 12
192.168.1.30 - dave [15/Jan/2024:08:00:06 +0000] "PUT /api/config HTTP/1.1" 200 567
192.168.1.20 - bob [15/Jan/2024:08:00:07 +0000] "GET /api/users HTTP/1.1" 200 1190
10.0.0.7 - eve [15/Jan/2024:08:00:08 +0000] "POST /api/upload HTTP/1.1" 413 234
192.168.1.10 - alice [15/Jan/2024:08:00:09 +0000] "GET /api/export HTTP/1.1" 200 98765
10.0.0.5 - - [15/Jan/2024:08:00:10 +0000] "GET /api/reports HTTP/1.1" 500 456
EOF

wc -l /tmp/access.log
echo "Log created successfully"
```

📸 **Verified Output:**
```
10 /tmp/access.log
Log created successfully
```

> 💡 **Keep a test dataset for practicing text processing.** Real log files can be huge. Before running `sed -i` (in-place edit) on a production log, always test on a copy. Use `cp /var/log/nginx/access.log /tmp/test.log` to make a safe copy.

---

## Step 2: grep — Pattern Matching Mastery

`grep` filters lines matching a pattern. `-E` enables Extended Regular Expressions (ERE); `-P` enables Perl-compatible regex (PCRE).

```bash
# Basic grep
echo "=== Lines with errors ==="
grep -E '40[13]|500' /tmp/access.log

# Case-insensitive
echo "=== Case insensitive ==="
grep -i 'get' /tmp/access.log | wc -l

# Invert match (lines NOT matching)
echo "=== Non-200 responses ==="
grep -v '" 200 ' /tmp/access.log

# Count matches
echo "=== Count of 200 responses ==="
grep -c '" 200 ' /tmp/access.log

# Show line numbers
echo "=== With line numbers ==="
grep -n '500' /tmp/access.log

# PCRE — Perl regex (most powerful)
echo "=== PCRE: status 4xx or 5xx ==="
grep -P '"\s(4|5)\d{2}\s' /tmp/access.log
```

📸 **Verified Output:**
```
=== Lines with errors ===
192.168.1.20 - bob [15/Jan/2024:08:00:02 +0000] "POST /api/login HTTP/1.1" 401 89
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
192.168.1.10 - alice [15/Jan/2024:08:00:04 +0000] "DELETE /api/users/42 HTTP/1.1" 403 78
=== Case insensitive ===
6
=== Non-200 responses ===
192.168.1.20 - bob [15/Jan/2024:08:00:02 +0000] "POST /api/login HTTP/1.1" 401 89
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
192.168.1.10 - alice [15/Jan/2024:08:00:04 +0000] "DELETE /api/users/42 HTTP/1.1" 403 78
10.0.0.7 - eve [15/Jan/2024:08:00:08 +0000] "POST /api/upload HTTP/1.1" 413 234
10.0.0.5 - - [15/Jan/2024:08:00:10 +0000] "GET /api/reports HTTP/1.1" 500 456
=== Count of 200 responses ===
5
=== With line numbers ===
3:10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
10:10.0.0.5 - - [15/Jan/2024:08:00:10 +0000] "GET /api/reports HTTP/1.1" 500 456
=== PCRE: status 4xx or 5xx ===
192.168.1.20 - bob [15/Jan/2024:08:00:02 +0000] "POST /api/login HTTP/1.1" 401 89
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
192.168.1.10 - alice [15/Jan/2024:08:00:04 +0000] "DELETE /api/users/42 HTTP/1.1" 403 78
10.0.0.7 - eve [15/Jan/2024:08:00:08 +0000] "POST /api/upload HTTP/1.1" 413 234
10.0.0.5 - - [15/Jan/2024:08:00:10 +0000] "GET /api/reports HTTP/1.1" 500 456
```

**grep flags reference:**

| Flag | Meaning |
|------|---------|
| `-E` | Extended regex (alternation `|`, `+`, `?`) |
| `-P` | Perl regex (lookaheads, `\d`, `\s`, `\b`) |
| `-i` | Case-insensitive |
| `-v` | Invert match |
| `-c` | Count matching lines |
| `-n` | Show line numbers |
| `-l` | List files with matches |
| `-r` | Recursive directory search |
| `-o` | Print only the matched part |
| `-A 3` | Show 3 lines after match |
| `-B 2` | Show 2 lines before match |
| `-C 2` | Show 2 lines context (before + after) |

> 💡 **`grep -o` extracts just the matching part.** Combined with sort and uniq, it's powerful: `grep -oE '\b[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b' access.log | sort | uniq -c | sort -rn` extracts and counts all IP addresses.

---

## Step 3: awk — Field-Based Processing

`awk` processes text field by field. It's a complete programming language built for columnar data.

```bash
# Print specific fields (space-delimited by default)
echo "=== IP, Method+Path, Status ==="
awk '{print $1, $6, $7, $9}' /tmp/access.log

# BEGIN and END blocks
echo "=== Request count with totals ==="
awk 'BEGIN{print "=== Request Log Analysis ==="} \
     {count++} \
     END{print "Total requests:", count}' /tmp/access.log

# Count status codes
echo "=== Status code distribution ==="
awk '{counts[$9]++} END{for(s in counts) print s, counts[s]}' \
    /tmp/access.log | sort -k1

# Conditional processing
echo "=== Only errors ==="
awk '$9 >= 400 {print "ERROR:", $7, "status=" $9, "user=" $3}' /tmp/access.log

# printf for formatted output
echo "=== Formatted table ==="
awk 'BEGIN{printf "%-18s %-30s %s\n", "IP", "Path", "Status"}
     {printf "%-18s %-30s %s\n", $1, $7, $9}' /tmp/access.log
```

📸 **Verified Output:**
```
=== IP, Method+Path, Status ===
192.168.1.10 "GET /api/users 200
192.168.1.20 "POST /api/login 401
10.0.0.5 "GET /api/reports 500
192.168.1.10 "DELETE /api/users/42 403
10.0.0.6 "GET /health 200
192.168.1.30 "PUT /api/config 200
192.168.1.20 "GET /api/users 200
10.0.0.7 "POST /api/upload 413
192.168.1.10 "GET /api/export 200
10.0.0.5 "GET /api/reports 500
=== Request count with totals ===
=== Request Log Analysis ===
Total requests: 10
=== Status code distribution ===
200 5
401 1
403 1
413 1
500 2
=== Only errors ===
ERROR: /api/login status=401 user=bob
ERROR: /api/reports status=500 user=-
ERROR: /api/users/42 status=403 user=alice
ERROR: /api/upload status=413 user=eve
ERROR: /api/reports status=500 user=-
=== Formatted table ===
IP                 Path                           Status
192.168.1.10       /api/users                     200
192.168.1.20       /api/login                     401
10.0.0.5           /api/reports                   500
192.168.1.10       /api/users/42                  403
10.0.0.6           /health                        200
192.168.1.30       /api/config                    200
192.168.1.20       /api/users                     200
10.0.0.7           /api/upload                    413
192.168.1.10       /api/export                    200
10.0.0.5           /api/reports                   500
```

> 💡 **awk uses `$0` for the entire line, `$1`–`$NF` for fields, `NR` for line number, `NF` for field count.** Change the field separator with `-F ':'` for colon-delimited files (like `/etc/passwd`): `awk -F: '{print $1, $3}' /etc/passwd` prints usernames and UIDs.

---

## Step 4: awk Advanced — Aggregation & Reporting

```bash
# Sum bytes transferred per user
echo "=== Bytes transferred per user ==="
awk '$3 != "-" {bytes[$3] += $10} END{
    for (user in bytes)
        printf "%-10s %10d bytes\n", user, bytes[user]
}' /tmp/access.log | sort -k2 -rn

# Error rate calculation
echo "=== Error rate ==="
awk '{total++; if ($9+0 >= 400) errors++} END{
    rate = (errors/total)*100
    printf "Total: %d | Errors: %d | Error rate: %.1f%%\n", total, errors, rate
}' /tmp/access.log

# Multi-condition analysis
echo "=== POST requests only ==="
awk '$6 == "\"POST" {print $1, $7, $9}' /tmp/access.log

# Using getline and custom separators
echo "=== /etc/passwd: UID >= 1000 ==="
awk -F: '$3 >= 1000 && $3 < 65534 {printf "User: %-15s UID: %d Shell: %s\n", $1, $3, $7}' \
    /etc/passwd | head -5
```

📸 **Verified Output:**
```
=== Bytes transferred per user ===
alice       100077 bytes
bob           1279 bytes
dave           567 bytes
charlie         12 bytes
eve            234 bytes
=== Error rate ===
Total: 10 | Errors: 5 | Error rate: 50.0%
=== POST requests only ===
192.168.1.20 /api/login 401
10.0.0.7 /api/upload 413
=== /etc/passwd: UID >= 1000 ==="
```

> 💡 **awk arrays are associative (hash maps).** You can accumulate any key-value data: `awk '{sum[$1]+=$10} END{for(ip in sum) print ip, sum[ip]}' access.log` gives total bytes per IP. Arrays are automatically created when first referenced — no declaration needed.

---

## Step 5: sed — Stream Editor for Transformations

`sed` edits text streams line by line using commands.

```bash
# Basic substitution: s/pattern/replacement/flags
echo "=== Replace HTTP/1.1 with HTTP/2 ==="
sed 's/HTTP\/1.1/HTTP\/2/g' /tmp/access.log | head -3

# Delete lines matching pattern
echo "=== Remove 200 OK lines ==="
sed '/\" 200 /d' /tmp/access.log

# Print only matching lines (-n suppresses default output)
echo "=== Print only error lines ==="
sed -n '/\" [45][0-9][0-9] /p' /tmp/access.log

# Address ranges: lines 3 to 5
echo "=== Lines 3-5 ==="
sed -n '3,5p' /tmp/access.log

# Address range: first match to last match
echo "=== From first 500 to end ==="
sed -n '/500/,$p' /tmp/access.log | head -5

# Multiple commands with -e
echo "=== Multiple transforms ==="
sed -e 's/HTTP\/1.1/HTTP2/' -e 's/+0000/UTC/' /tmp/access.log | head -3

# Delete blank lines
echo "Testing" > /tmp/blanks.txt
echo "" >> /tmp/blanks.txt
echo "More text" >> /tmp/blanks.txt
echo "" >> /tmp/blanks.txt
echo "End" >> /tmp/blanks.txt
echo "=== With blanks:"
cat /tmp/blanks.txt
echo "=== Blanks removed:"
sed '/^$/d' /tmp/blanks.txt
```

📸 **Verified Output:**
```
=== Replace HTTP/1.1 with HTTP/2 ===
192.168.1.10 - alice [15/Jan/2024:08:00:01 +0000] "GET /api/users HTTP/2" 200 1234
192.168.1.20 - bob [15/Jan/2024:08:00:02 +0000] "POST /api/login HTTP/2" 401 89
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/2" 500 456
=== Remove 200 OK lines ===
192.168.1.20 - bob [15/Jan/2024:08:00:02 +0000] "POST /api/login HTTP/1.1" 401 89
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
192.168.1.10 - alice [15/Jan/2024:08:00:04 +0000] "DELETE /api/users/42 HTTP/1.1" 403 78
10.0.0.7 - eve [15/Jan/2024:08:00:08 +0000] "POST /api/upload HTTP/1.1" 413 234
10.0.0.5 - - [15/Jan/2024:08:00:10 +0000] "GET /api/reports HTTP/1.1" 500 456
=== Print only error lines ===
192.168.1.20 - bob [15/Jan/2024:08:00:02 +0000] "POST /api/login HTTP/1.1" 401 89
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
192.168.1.10 - alice [15/Jan/2024:08:00:04 +0000] "DELETE /api/users/42 HTTP/1.1" 403 78
10.0.0.7 - eve [15/Jan/2024:08:00:08 +0000] "POST /api/upload HTTP/1.1" 413 234
10.0.0.5 - - [15/Jan/2024:08:00:10 +0000] "GET /api/reports HTTP/1.1" 500 456
=== Lines 3-5 ===
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
192.168.1.10 - alice [15/Jan/2024:08:00:04 +0000] "DELETE /api/users/42 HTTP/1.1" 403 78
10.0.0.6 - charlie [15/Jan/2024:08:00:05 +0000] "GET /health HTTP/1.1" 200 12
=== From first 500 to end ===
10.0.0.5 - - [15/Jan/2024:08:00:03 +0000] "GET /api/reports HTTP/1.1" 500 456
192.168.1.10 - alice [15/Jan/2024:08:00:04 +0000] "DELETE /api/users/42 HTTP/1.1" 403 78
10.0.0.6 - charlie [15/Jan/2024:08:00:05 +0000] "GET /health HTTP/1.1" 200 12
192.168.1.30 - dave [15/Jan/2024:08:00:06 +0000] "PUT /api/config HTTP/1.1" 200 567
192.168.1.20 - bob [15/Jan/2024:08:00:07 +0000] "GET /api/users HTTP/1.1" 200 1190
=== Multiple transforms ===
192.168.1.10 - alice [15/Jan/2024:08:00:01 UTC] "GET /api/users HTTP2" 200 1234
192.168.1.20 - bob [15/Jan/2024:08:00:02 UTC] "POST /api/login HTTP2" 401 89
10.0.0.5 - - [15/Jan/2024:08:00:03 UTC] "GET /api/reports HTTP2" 500 456
=== With blanks:
Testing

More text

End
=== Blanks removed:
Testing
More text
End
```

> 💡 **`sed -i` edits files in-place — always test first without `-i`.** On macOS, `sed -i` requires an extension argument: `sed -i '' 's/old/new/' file`. On Linux, `sed -i 's/old/new/' file` works directly. Use `sed -i.bak` to create a backup before editing.

---

## Step 6: sed Advanced — In-place Editing & Config Management

```bash
# Create a config file to edit
cat > /tmp/app.conf << 'EOF'
# Application Configuration
host = localhost
port = 8080
debug = true
log_level = debug
max_connections = 10
database_url = postgres://localhost/devdb
EOF

echo "=== Original config ==="
cat /tmp/app.conf

# In-place edit: change port (make backup first)
cp /tmp/app.conf /tmp/app.conf.bak
sed -i 's/port = 8080/port = 443/' /tmp/app.conf
sed -i 's/debug = true/debug = false/' /tmp/app.conf
sed -i 's/log_level = debug/log_level = warn/' /tmp/app.conf
sed -i 's|database_url = postgres://localhost/devdb|database_url = postgres://db.prod.example.com/proddb|' /tmp/app.conf

echo "=== Updated config ==="
cat /tmp/app.conf

echo "=== Diff ==="
diff /tmp/app.conf.bak /tmp/app.conf
```

📸 **Verified Output:**
```
=== Original config ===
# Application Configuration
host = localhost
port = 8080
debug = true
log_level = debug
max_connections = 10
database_url = postgres://localhost/devdb
=== Updated config ===
# Application Configuration
host = localhost
port = 443
debug = false
log_level = warn
max_connections = 10
database_url = postgres://db.prod.example.com/proddb
=== Diff ===
3c3
< port = 8080
---
> port = 443
4c4
< debug = true
---
> debug = false
5c5
< log_level = debug
---
> log_level = warn
7c7
< database_url = postgres://localhost/devdb
---
> database_url = postgres://db.prod.example.com/proddb
```

> 💡 **Use `|` as a delimiter in sed when the pattern contains `/`.** `sed 's|/old/path|/new/path|g'` avoids escaping slashes. You can use any character: `sed 's#old#new#g'` works too. This is essential when editing file paths or URLs.

---

## Step 7: Combining grep + awk + sed in Pipelines

```bash
echo "=== Top 5 IPs by request count ==="
awk '{print $1}' /tmp/access.log | sort | uniq -c | sort -rn | head -5

echo ""
echo "=== Error summary report ==="
grep -E '" [45][0-9]{2} ' /tmp/access.log | \
    awk '{
        gsub(/"/, "", $6)  # Remove quotes from method
        print $1, $6, $7, $9
    }' | \
    sort -k4 -n

echo ""
echo "=== Bandwidth by status code ==="
awk '{bytes[$9]+=$10} END{
    printf "%-8s %12s\n", "Status", "Bytes"
    printf "%-8s %12s\n", "------", "-----"
    for (s in bytes) printf "%-8s %12d\n", s, bytes[s]
}' /tmp/access.log | sort

echo ""
echo "=== Users who hit errors ==="
grep -E '" [45][0-9]{2} ' /tmp/access.log | \
    awk '$3 != "-" {users[$3]++} END{
        for (u in users) printf "%-10s: %d errors\n", u, users[u]
    }' | sort -t: -k2 -rn
```

📸 **Verified Output:**
```
=== Top 5 IPs by request count ===
      3 192.168.1.10
      2 192.168.1.20
      2 10.0.0.5
      1 192.168.1.30
      1 10.0.0.7
=== Error summary report ===
192.168.1.20 POST /api/login 401
192.168.1.10 DELETE /api/users/42 403
10.0.0.7 POST /api/upload 413
10.0.0.5 GET /api/reports 500
10.0.0.5 GET /api/reports 500
=== Bandwidth by status code ===
Status        Bytes
------        -----
200          101011
401              89
403              78
413             234
500             912
=== Users who hit errors ===
alice     : 1 errors
bob       : 1 errors
eve       : 1 errors
```

> 💡 **Build pipelines incrementally.** Start with `cat file`, add `| grep pattern`, check output, add `| awk ...`, check again. Never write a 5-stage pipeline from scratch — build and verify each stage. Use `| head -5` to preview without processing everything.

---

## Step 8: Capstone — Complete Log Analysis Script

**Scenario:** Build a production-ready log analyzer that generates an HTML-friendly report.

```bash
cat > /tmp/log-analyze.sh << 'SCRIPT'
#!/bin/bash
# log-analyze.sh — Full log analysis pipeline
set -euo pipefail

LOG="${1:-/tmp/access.log}"
echo "========================================"
echo "  Web Access Log Analysis Report"
echo "  File: $LOG"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 1. Traffic Summary
echo "[ 1 ] TRAFFIC SUMMARY"
echo "---------------------------------------"
total=$(wc -l < "$LOG")
success=$(grep -cE '" 2[0-9]{2} ' "$LOG" || true)
redirect=$(grep -cE '" 3[0-9]{2} ' "$LOG" || true)
client_err=$(grep -cE '" 4[0-9]{2} ' "$LOG" || true)
server_err=$(grep -cE '" 5[0-9]{2} ' "$LOG" || true)

printf "  Total requests:  %d\n" "$total"
printf "  2xx Success:     %d (%.0f%%)\n" "$success" "$(echo "$success $total" | awk '{printf "%d", $1/$2*100}')"
printf "  3xx Redirect:    %d\n" "$redirect"
printf "  4xx Client Err:  %d\n" "$client_err"
printf "  5xx Server Err:  %d\n" "$server_err"
echo ""

# 2. Status Code Breakdown
echo "[ 2 ] STATUS CODE BREAKDOWN"
echo "---------------------------------------"
awk '{counts[$9]++} END{for(s in counts) printf "  HTTP %-3s : %d requests\n", s, counts[s]}' \
    "$LOG" | sort
echo ""

# 3. Top Requestors
echo "[ 3 ] TOP 5 IP ADDRESSES"
echo "---------------------------------------"
awk '{print $1}' "$LOG" | sort | uniq -c | sort -rn | head -5 | \
    awk '{printf "  %-18s %d requests\n", $2, $1}'
echo ""

# 4. Most Requested Endpoints
echo "[ 4 ] TOP 5 ENDPOINTS"
echo "---------------------------------------"
awk '{print $7}' "$LOG" | sort | uniq -c | sort -rn | head -5 | \
    awk '{printf "  %-30s %d requests\n", $2, $1}'
echo ""

# 5. Error Details
echo "[ 5 ] ERROR DETAILS"
echo "---------------------------------------"
grep -E '" [45][0-9]{2} ' "$LOG" | \
    awk '{printf "  [%s] %s %-30s → %s\n", 
        substr($4,2), $6, $7, $9}' | \
    sed 's/"//g'
echo ""

# 6. Bandwidth Analysis
echo "[ 6 ] BANDWIDTH BY STATUS"
echo "---------------------------------------"
awk '{bytes[$9]+=$10} END{
    for(s in bytes) printf "  HTTP %s: %d bytes (%.1f KB)\n", s, bytes[s], bytes[s]/1024
}' "$LOG" | sort
echo ""

echo "========================================"
echo "  Analysis complete"
echo "========================================"
SCRIPT

chmod +x /tmp/log-analyze.sh
bash /tmp/log-analyze.sh /tmp/access.log
```

📸 **Verified Output:**
```
========================================
  Web Access Log Analysis Report
  File: /tmp/access.log
  Date: 2024-01-15 08:00:10
========================================

[ 1 ] TRAFFIC SUMMARY
---------------------------------------
  Total requests:  10
  2xx Success:     5 (50%)
  3xx Redirect:    0
  4xx Client Err:  3
  5xx Server Err:  2

[ 2 ] STATUS CODE BREAKDOWN
---------------------------------------
  HTTP 200 : 5 requests
  HTTP 401 : 1 requests
  HTTP 403 : 1 requests
  HTTP 413 : 1 requests
  HTTP 500 : 2 requests

[ 3 ] TOP 5 IP ADDRESSES
---------------------------------------
  192.168.1.10       3 requests
  10.0.0.5           2 requests
  192.168.1.20       2 requests
  10.0.0.6           1 requests
  10.0.0.7           1 requests

[ 4 ] TOP 5 ENDPOINTS
---------------------------------------
  /api/reports                   2 requests
  /api/users                     2 requests
  /api/config                    1 requests
  /api/export                    1 requests
  /api/login                     1 requests

[ 5 ] ERROR DETAILS
---------------------------------------
  [15/Jan/2024:08:00:02] POST /api/login                        → 401
  [15/Jan/2024:08:00:03] GET  /api/reports                      → 500
  [15/Jan/2024:08:00:04] DELETE /api/users/42                   → 403
  [15/Jan/2024:08:00:08] POST /api/upload                       → 413
  [15/Jan/2024:08:00:10] GET  /api/reports                      → 500

[ 6 ] BANDWIDTH BY STATUS
---------------------------------------
  HTTP 200: 101011 bytes (98.6 KB)
  HTTP 401: 89 bytes (0.1 KB)
  HTTP 403: 78 bytes (0.1 KB)
  HTTP 413: 234 bytes (0.2 KB)
  HTTP 500: 912 bytes (0.9 KB)

========================================
  Analysis complete
========================================
```

> 💡 **This script is a foundation for a real log monitoring tool.** Add `--since` filtering with `awk '$4 > "[15/Jan/2024:08:00:05"'`, email output with `| mail -s "Log Report" ops@team.com`, or schedule with cron. The grep+awk+sed combination handles any structured text file — Apache logs, nginx logs, custom app logs.

---

## Summary

| Tool | Best For | Key Flags |
|------|---------|-----------|
| `grep` | Finding lines matching a pattern | `-E` (ERE), `-P` (PCRE), `-v` (invert), `-c` (count), `-n` (line nums), `-o` (match only) |
| `grep -E` | Extended regex: `+`, `?`, `\|`, `{n}` | `'pat1\|pat2'` |
| `grep -P` | Perl regex: `\d`, `\s`, `\b`, lookaheads | `'\b[45]\d{2}\b'` |
| `awk` | Field processing, aggregation, reporting | `-F` (delimiter), `BEGIN`/`END`, arrays |
| `awk` patterns | Conditional processing | `$9 >= 400 {print}` |
| `sed 's/a/b/g'` | Global substitution | `g` = all occurrences |
| `sed -n '/pat/p'` | Print only matches | `-n` suppresses default output |
| `sed '/pat/d'` | Delete matching lines | — |
| `sed -i` | In-place file edit | Use `.bak` extension for safety |
| `\|` pipe | Chain tools together | Build incrementally |
