# Lab 19: Advanced Regular Expressions

## 🎯 Objective
Master POSIX character classes, grouping, alternation, quantifiers, and backreferences in `grep`, `sed`, and `awk`.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Labs 1–3 (grep, awk, sed basics)

## 🔬 Lab Instructions

### Step 1: POSIX Character Classes
```bash
echo "abc 123 ABC !@#" | grep -oE '[[:alpha:]]+'
# abc
# ABC

echo "abc 123 ABC !@#" | grep -oE '[[:digit:]]+'
# 123

echo "abc 123 ABC !@#" | grep -oE '[[:alnum:]]+'
# abc
# 123
# ABC

# Available POSIX classes:
# [:alpha:]   letters (a-z, A-Z)
# [:digit:]   digits 0-9
# [:alnum:]   letters and digits
# [:space:]   whitespace (space, tab, newline)
# [:upper:]   uppercase letters
# [:lower:]   lowercase letters
# [:punct:]   punctuation characters
```

### Step 2: Anchors and Word Boundaries
```bash
printf "cat\ncats\nconcat\nthe cat sat\n" | grep '\bcat\b'
# cat
# the cat sat

printf "start\nrestart\nstarting\n" | grep '^start'
# start
# starting

printf "log\nblog\ncatalog\n" | grep 'log$'
# log
# blog
# catalog
```

### Step 3: Grouping and Alternation
```bash
printf "color\ncolour\ncolr\n" | grep -E 'colou?r'
# color
# colour

printf "cat\ndog\nbird\nfish\n" | grep -E '^(cat|dog)$'
# cat
# dog

# Alternation in sed
echo "Hello World" | sed -E 's/(Hello|Hi)/Greetings/'
# Greetings World
```

### Step 4: Quantifiers
```bash
# ? = 0 or 1    + = 1 or more    * = 0 or more    {n,m} = range
printf "color\ncolour\ncolouur\n" | grep -E '^colou{0,2}r$'
# color
# colour
# colouur

echo "192.168.1.100" | grep -E '^([0-9]{1,3}\.){3}[0-9]{1,3}$'
# 192.168.1.100

echo "aababab" | grep -oE 'a{1,2}b'
# ab
# ab
# ab
```

### Step 5: Capturing Groups in sed
```bash
# Rearrange date format YYYY-MM-DD to DD/MM/YYYY
echo "2026-03-01" | sed -E 's/([0-9]{4})-([0-9]{2})-([0-9]{2})/\3\/\2\/\1/'
# 01/03/2026

# Wrap words in double quotes
echo "apple banana cherry" | sed -E 's/([a-z]+)/"\1"/g'
# "apple" "banana" "cherry"

# Extract domain from email
echo "user@example.com" | sed -E 's/.*@([a-zA-Z0-9.]+)/\1/'
# example.com
```

### Step 6: Groups in awk with match()
```bash
echo "Error: connection refused at line 42" | awk '{
    if (match($0, /line ([0-9]+)/, arr)) {
        print "Line number:", arr[1]
    }
}'
# Line number: 42

echo "2026-03-01 ERROR server crashed" | awk '{
    if (match($0, /([0-9]{4})-([0-9]{2})-([0-9]{2})/, d)) {
        print "Year:", d[1], "Month:", d[2], "Day:", d[3]
    }
}'
# Year: 2026 Month: 03 Day: 01
```

### Step 7: Lookahead and Lookbehind (grep -P)
```bash
# grep -P enables Perl-compatible regex

# Positive lookahead: match "foo" followed by "bar"
printf "foobar\nfooBAZ\nfoo\n" | grep -P 'foo(?=bar)'
# foobar

# Negative lookahead: "foo" NOT followed by "bar"
printf "foobar\nfooBAZ\nfoo\n" | grep -P 'foo(?!bar)'
# fooBAZ
# foo

# Lookbehind: IP preceded by "from "
echo "Connection from 192.168.1.1 refused" | grep -oP '(?<=from )[0-9.]+'
# 192.168.1.1
```

### Step 8: Validate Common Patterns
```bash
# Validate email (simplified)
for e in "user@example.com" "invalid@.com" "@bad.com" "good+tag@domain.org"; do
    if echo "$e" | grep -qE '^[a-zA-Z0-9._%++-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'; then
        echo "VALID  : $e"
    else
        echo "INVALID: $e"
    fi
done
# VALID  : user@example.com
# INVALID: invalid@.com
# INVALID: @bad.com
# VALID  : good+tag@domain.org

# Validate IPv4
for ip in "192.168.1.1" "256.0.0.1" "10.0.0" "172.16.254.254"; do
    if echo "$ip" | grep -qE '^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'; then
        echo "VALID IP  : $ip"
    else
        echo "INVALID IP: $ip"
    fi
done
```

### Step 9: Non-Greedy Matching (grep -P)
```bash
echo '<a>link1</a> <a>link2</a>' | grep -oP '<a>.*?</a>'
# <a>link1</a>
# <a>link2</a>

# Without ? (greedy), would match from first <a> to last </a>
echo '<a>link1</a> <a>link2</a>' | grep -oP '<a>.*</a>'
# <a>link1</a> <a>link2</a>
```

### Step 10: Practical Script — Log Analyzer with Regex
```bash
cat > ~/regex_log_check.sh << 'EOF'
#!/bin/bash
set -euo pipefail
LOG="${1:-/tmp/app.log}"
[[ -f "$LOG" ]] || { echo "File not found: $LOG" >&2; exit 1; }

echo "=== Regex Log Analyzer: $LOG ==="

echo ""
echo "Timestamps found:"
grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}' "$LOG" \
  | sort -u | awk '{print "  " $0}'

echo ""
echo "IPs found:"
grep -oE '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' "$LOG" \
  | sort -u | awk '{print "  " $0}'

echo ""
echo "HTTP status codes:"
grep -oE '\b[1-5][0-9]{2}\b' "$LOG" \
  | sort | uniq -c | sort -rn \
  | awk '{printf "  %s: %s occurrences\n", $2, $1}'
EOF
chmod +x ~/regex_log_check.sh
~/regex_log_check.sh /tmp/app.log
```

## ✅ Verification
```bash
echo "Phone: 555-123-4567" | grep -oP '\d{3}-\d{3}-\d{4}'
# 555-123-4567

echo "2026-03-01" | sed -E 's/([0-9]{4})-([0-9]{2})-([0-9]{2})/\3-\2-\1/'
# 01-03-2026
```

## 📝 Summary
- POSIX classes `[:alpha:]`, `[:digit:]`, `[:alnum:]` work in grep, sed, and awk
- `grep -E` enables extended regex; `grep -P` enables Perl regex (lookahead, etc.)
- Grouping `()` in `sed -E` allows backreferences `\1`, `\2` for reordering
- `awk match($0, /re/, arr)` captures groups into array for extraction
- Non-greedy matching `.*?` requires `grep -P` or Perl-compatible tools
