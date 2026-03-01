# Lab 1: Advanced grep — Regex and Context

## 🎯 Objective
Use grep with extended regular expressions (`-E`), Perl-compatible regex (`-P`), and context flags (`-A`, `-B`, `-C`) for powerful log and text searching.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Completed Foundations Lab 14 (grep basics)
- Basic understanding of regular expressions

## 🔬 Lab Instructions

### Step 1: Create a Test Dataset
```bash
cat > /tmp/sample.log << 'EOF'
2026-03-01 08:00:01 INFO  User admin logged in from 192.168.1.10
2026-03-01 08:00:15 ERROR Failed login attempt for user bob from 10.0.0.5
2026-03-01 08:01:03 INFO  File /etc/passwd accessed by admin
2026-03-01 08:01:45 WARN  Disk usage at 85% on /dev/sda1
2026-03-01 08:02:10 ERROR Connection refused: port 8080
2026-03-01 08:02:30 INFO  User alice logged in from 192.168.1.20
2026-03-01 08:03:00 ERROR Failed login attempt for user root from 203.0.113.5
2026-03-01 08:03:30 CRITICAL Service nginx is down
2026-03-01 08:04:00 INFO  Backup completed successfully
2026-03-01 08:04:45 ERROR Database connection timeout after 30 seconds
EOF
```

### Step 2: Extended Regular Expressions with `-E`
```bash
# -E enables extended regex (no need to escape + ? | {})
# Match lines with ERROR or WARN or CRITICAL
grep -E "ERROR|WARN|CRITICAL" /tmp/sample.log

# Match lines starting with a date (2026)
grep -E "^2026" /tmp/sample.log

# Match log levels exactly (whole word)
grep -E "\b(INFO|WARN|ERROR)\b" /tmp/sample.log
```

### Step 3: Quantifiers in Extended Regex
```bash
# + means one or more
grep -E "login+" /tmp/sample.log  # 'loginn', 'loginnn', etc.

# ? means zero or one
grep -E "Failed?" /tmp/sample.log  # 'Faile' or 'Failed'

# {n,m} means between n and m repetitions
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" /tmp/sample.log
# Matches IP addresses
```

### Step 4: Character Classes
```bash
# [abc] matches any one of a, b, c
grep -E "us[ei]r" /tmp/sample.log  # matches 'user' or 'usir'

# [^abc] matches anything NOT a, b, or c
# [a-z] matches any lowercase letter
# [A-Z] matches any uppercase letter
# [0-9] matches any digit

# POSIX classes
grep -E "[[:upper:]]{3,}" /tmp/sample.log  # 3+ uppercase letters together
grep -E "[[:digit:]]{2}:[[:digit:]]{2}" /tmp/sample.log  # time pattern HH:MM
```

### Step 5: Anchors and Boundaries
```bash
# ^ anchors to start of line
grep -E "^2026-03-01 08:0[34]" /tmp/sample.log  # Lines from 08:03 or 08:04

# $ anchors to end of line
grep -E "successfully$" /tmp/sample.log

# \b word boundary
grep -E "\broot\b" /tmp/sample.log  # matches 'root' but not 'rooting'
```

### Step 6: Perl-Compatible Regex with `-P`
```bash
# -P enables Perl regex — most powerful option
# Lookahead: (?=...)
grep -P "(?=.*ERROR)(?=.*login)" /tmp/sample.log
# Lines containing both ERROR and login

# Lookahead for IP extraction
grep -oP "\b\d{1,3}(\.\d{1,3}){3}\b" /tmp/sample.log
# -o prints only the matching part (not whole line)
# Output: list of IP addresses

# Named groups
grep -oP "(?<=from )\d+\.\d+\.\d+\.\d+" /tmp/sample.log
# Extracts IP addresses that come after "from "
```

### Step 7: Context Lines with `-A`, `-B`, `-C`
```bash
# -A N: show N lines After the match
grep -A 2 "CRITICAL" /tmp/sample.log
# Shows the CRITICAL line plus 2 lines after it

# -B N: show N lines Before the match
grep -B 2 "CRITICAL" /tmp/sample.log
# Shows 2 lines before the CRITICAL line

# -C N: show N lines around (Before and After)
grep -C 1 "CRITICAL" /tmp/sample.log
# Shows 1 line before and 1 line after
```

### Step 8: Extract Only Matching Text with `-o`
```bash
# Print only the matched text, not the whole line
grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" /tmp/sample.log
# Output: just the IP addresses, one per line

# Extract timestamps
grep -oE "[0-9]{2}:[0-9]{2}:[0-9]{2}" /tmp/sample.log

# Extract log levels
grep -oE "\b(INFO|WARN|ERROR|CRITICAL)\b" /tmp/sample.log
```

### Step 9: Count and Aggregate
```bash
# Count occurrences of each log level
echo "Log Level Counts:"
for level in INFO WARN ERROR CRITICAL; do
  count=$(grep -c "\b$level\b" /tmp/sample.log)
  echo "  $level: $count"
done
```

### Step 10: Recursive Regex Search
```bash
# Search all log files in /var/log for failed logins
grep -rE "Failed|FAILED" /var/log/auth.log 2>/dev/null | head -10

# Search for IPs attempting login
grep -oP "(?<=from )\d+\.\d+\.\d+\.\d+" /var/log/auth.log 2>/dev/null | \
  sort | uniq -c | sort -rn | head -10
```

### Step 11: Multiline Matching Strategy
```bash
# grep is line-oriented — use pcregrep for multiline
sudo apt install pcregrep -y

# Match pattern spanning lines
pcregrep -M "ERROR.*\n.*timeout" /tmp/sample.log
```

### Step 12: Practical Log Filtering Pipeline
```bash
# Extract all ERROR lines with timestamps and IPs
grep -E "ERROR" /tmp/sample.log | \
  grep -oP "^\S+ \S+ .* from \K\d+\.\d+\.\d+\.\d+" 2>/dev/null || \
  grep "ERROR" /tmp/sample.log

# Clean up
rm /tmp/sample.log
```

## ✅ Verification
```bash
# Create test data and verify grep -E works
echo -e "cat\ndog\ncod\nbat" > /tmp/gtest.txt
grep -E "c(at|od)" /tmp/gtest.txt
# Output: cat, cod

grep -oE "[a-z]{3}" /tmp/gtest.txt
# Output: cat, dog, cod, bat

grep -c "." /tmp/gtest.txt
# Output: 4

rm /tmp/gtest.txt
```

## 📝 Summary
- `-E` enables extended regex with `+`, `?`, `|`, `{n,m}` without escaping
- `-P` enables Perl-compatible regex for lookaheads, lookbehinds, named groups
- `-o` prints only the matched text — powerful for extraction
- `-A/-B/-C` show context around matches — essential for log analysis
- Combine with pipes (`sort`, `uniq -c`, `head`) for log aggregation
- `\b` word boundaries prevent partial word matches
