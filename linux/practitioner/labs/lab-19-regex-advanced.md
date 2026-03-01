# Lab 19: Advanced Regular Expressions

## 🎯 Objective
Master extended regular expressions (ERE) in grep -E, use POSIX character classes, groups, alternation, and anchors.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Practitioner Lab 1: Advanced grep

## 🔬 Lab Instructions

### Step 1: Set Up Test Data

```bash
cat > /tmp/regex-test.txt << 'EOF'
alice@example.com
bob.smith@company.org
invalid-email
192.168.1.100
10.0.0.1
999.999.999.999
2026-03-01
2026-13-45
phone: +1-555-0100
phone: 555.0101
phone: (555) 0102
Price: $29.99
Price: $1,299.00
ERROR: file not found
WARNING: low memory
INFO: server started
line with   multiple   spaces
UPPERCASE ONLY LINE
lowercase only line
MiXeD CaSe LiNe
EOF
```

### Step 2: POSIX Character Classes

```bash
# [[:alpha:]] = any letter (a-z, A-Z)
grep -E "^[[:alpha:]]+$" /tmp/regex-test.txt
```

**Expected output:**
```
(none - all lines have non-alpha chars)
```

```bash
# [[:lower:]] = lowercase letters
grep -E "^[[:lower:] ]+$" /tmp/regex-test.txt
```

**Expected output:**
```
lowercase only line
```

```bash
# [[:upper:]] = uppercase letters
grep -E "^[[:upper:] ]+$" /tmp/regex-test.txt
```

**Expected output:**
```
UPPERCASE ONLY LINE
```

```bash
# [[:digit:]] = digits 0-9
grep -E "[[:digit:]]" /tmp/regex-test.txt | head -10
```

```bash
# [[:alnum:]] = letters and digits
grep -E "^[[:alnum:]]+$" /tmp/regex-test.txt
```

```bash
# [[:space:]] = whitespace
grep -E "[[:space:]]{2,}" /tmp/regex-test.txt
```

### Step 3: Quantifiers

```bash
# + = one or more
grep -E "[0-9]+" /tmp/regex-test.txt | head -5

# * = zero or more
grep -E "^[[:alpha:]]*$" /tmp/regex-test.txt | head -3

# ? = zero or one (optional)
grep -E "colou?r" <<< "color and colour are the same"

# {n} = exactly n
grep -E "[0-9]{3}" /tmp/regex-test.txt | head -5

# {n,m} = between n and m
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" /tmp/regex-test.txt
```

**Expected output (IPs):**
```
192.168.1.100
10.0.0.1
999.999.999.999
```

### Step 4: Anchors

```bash
# ^ = start of line
grep -E "^[[:upper:]]" /tmp/regex-test.txt

# $ = end of line
grep -E "com$" /tmp/regex-test.txt

# \b = word boundary (in ERE)
echo "cat catalog category" | grep -Eo "\bcat\b"
```

**Expected output:**
```
cat
```

```bash
# Match complete lines
grep -E "^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$" /tmp/regex-test.txt
```

**Expected output:**
```
192.168.1.100
10.0.0.1
999.999.999.999
```

### Step 5: Groups and Alternation

```bash
# | = alternation (OR)
grep -E "ERROR|WARNING" /tmp/regex-test.txt
```

**Expected output:**
```
ERROR: file not found
WARNING: low memory
```

```bash
# () = grouping
grep -E "(ERROR|WARNING|INFO):" /tmp/regex-test.txt
```

```bash
# Groups with quantifiers
echo "abcabcabc" | grep -E "(abc){3}"
echo "abcabc" | grep -E "(abc){3}" || echo "no match for (abc){3}"
```

```bash
# Alternation for log levels
journalctl -n 20 --no-pager 2>/dev/null | grep -E "(error|warn|fail)" -i | head -5 || echo "no matching journal entries"
```

### Step 6: Email Pattern

```bash
# Basic email regex
grep -E "^[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}$" /tmp/regex-test.txt
```

**Expected output:**
```
alice@example.com
bob.smith@company.org
```

### Step 7: IP Address Pattern

```bash
# Simplified IP address pattern (1-3 digits in each octet)
grep -E "^([0-9]{1,3}\.){3}[0-9]{1,3}$" /tmp/regex-test.txt
```

```bash
# Stricter: only valid octet ranges (0-255)
grep -E "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$" /tmp/regex-test.txt
```

**Expected output:**
```
192.168.1.100
10.0.0.1
```

Note: 999.999.999.999 is excluded as invalid.

### Step 8: Extract with -o

```bash
# Extract email addresses
grep -Eo "[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}" /tmp/regex-test.txt
```

```bash
# Extract IP addresses
grep -Eo "([0-9]{1,3}\.){3}[0-9]{1,3}" /tmp/regex-test.txt
```

```bash
# Extract dates (YYYY-MM-DD format)
grep -Eo "[0-9]{4}-[0-9]{2}-[0-9]{2}" /tmp/regex-test.txt
```

**Expected output:**
```
2026-03-01
2026-13-45
```

```bash
# Extract prices
grep -Eo "\$[0-9,]+\.[0-9]{2}" /tmp/regex-test.txt
```

## ✅ Verification

```bash
echo "=== Email extraction ===" && grep -Eo "[[:alnum:]._%+-]+@[[:alnum:].-]+\.[[:alpha:]]{2,}" /tmp/regex-test.txt
echo "=== IP extraction ===" && grep -Eo "([0-9]{1,3}\.){3}[0-9]{1,3}" /tmp/regex-test.txt | head -5
echo "=== LOG levels ===" && grep -E "^(ERROR|WARNING|INFO):" /tmp/regex-test.txt
echo "=== POSIX lower ===" && grep -E "^[[:lower:] ]+$" /tmp/regex-test.txt
rm /tmp/regex-test.txt
echo "Practitioner Lab 19 complete"
```

## 📝 Summary
- POSIX classes: `[[:alpha:]]`, `[[:digit:]]`, `[[:alnum:]]`, `[[:space:]]`, `[[:upper:]]`, `[[:lower:]]`
- Quantifiers: `+` (1+), `*` (0+), `?` (0 or 1), `{n,m}` (range)
- Anchors: `^` start of line, `$` end of line, `\b` word boundary
- Alternation: `(ERROR|WARN|INFO)` matches any of the options
- Groups `()` allow applying quantifiers: `([0-9]{1,3}\.){3}`
- `grep -Eo` extracts only the matched portion — great for data extraction
