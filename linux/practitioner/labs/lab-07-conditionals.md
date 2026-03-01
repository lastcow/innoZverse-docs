# Lab 7: Conditionals in bash

## 🎯 Objective
Use if/elif/else with [[ ]] for string and file tests, and numeric comparisons with -eq, -gt, -lt, -ne.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Foundations Lab 18: Environment Variables
- Practitioner Lab 6: Shell Variables

## 🔬 Lab Instructions

### Step 1: Basic if/elif/else Structure

```bash
AGE=25

if [[ $AGE -ge 18 ]]; then
    echo "Adult"
elif [[ $AGE -ge 13 ]]; then
    echo "Teenager"
else
    echo "Child"
fi
```

**Expected output:**
```
Adult
```

### Step 2: String Tests

```bash
NAME="Linux"

if [[ "$NAME" == "Linux" ]]; then
    echo "Exact match"
fi

if [[ "$NAME" != "Windows" ]]; then
    echo "Not Windows"
fi

# Pattern matching with ==
if [[ "$NAME" == L* ]]; then
    echo "Starts with L"
fi

# Test empty/non-empty
EMPTY=""
if [[ -z "$EMPTY" ]]; then
    echo "Variable is empty"
fi

if [[ -n "$NAME" ]]; then
    echo "Variable is not empty: $NAME"
fi
```

### Step 3: Numeric Comparisons

```bash
X=10
Y=20

if [[ $X -eq 10 ]]; then echo "X equals 10"; fi
if [[ $X -ne $Y ]]; then echo "X not equal to Y"; fi
if [[ $X -lt $Y ]]; then echo "X less than Y"; fi
if [[ $X -le 10 ]]; then echo "X less than or equal to 10"; fi
if [[ $Y -gt $X ]]; then echo "Y greater than X"; fi
if [[ $Y -ge 20 ]]; then echo "Y greater than or equal to 20"; fi
```

### Step 4: File Tests

```bash
# Create test files
touch /tmp/testfile.txt
mkdir -p /tmp/testdir

if [[ -f "/tmp/testfile.txt" ]]; then
    echo "Is a regular file"
fi

if [[ -d "/tmp/testdir" ]]; then
    echo "Is a directory"
fi

if [[ -e "/tmp/testfile.txt" ]]; then
    echo "File exists"
fi

if [[ -r "/tmp/testfile.txt" ]]; then
    echo "File is readable"
fi

if [[ -w "/tmp/testfile.txt" ]]; then
    echo "File is writable"
fi

chmod +x /tmp/testfile.txt
if [[ -x "/tmp/testfile.txt" ]]; then
    echo "File is executable"
fi

if [[ ! -f "/tmp/nonexistent.txt" ]]; then
    echo "File does not exist"
fi
```

### Step 5: Combining Conditions

```bash
AGE=25
SCORE=85

# AND with &&
if [[ $AGE -ge 18 && $SCORE -ge 80 ]]; then
    echo "Eligible: adult with good score"
fi

# OR with ||
ROLE="admin"
if [[ "$ROLE" == "admin" || "$ROLE" == "superuser" ]]; then
    echo "Has elevated permissions"
fi

# Negation with !
if [[ ! -d "/tmp/nonexistent_dir" ]]; then
    echo "Directory does not exist"
fi
```

### Step 6: test Command vs [[ ]]

```bash
# test and [ ] are equivalent but older
test -f /tmp/testfile.txt && echo "test: file exists"
[ -f /tmp/testfile.txt ] && echo "[ ]: file exists"
[[ -f /tmp/testfile.txt ]] && echo "[[ ]]: file exists"

# [[ ]] is preferred: handles spaces and special chars better
FILENAME="my file.txt"
touch "/tmp/$FILENAME"
if [[ -f "/tmp/$FILENAME" ]]; then
    echo "File with spaces found"
fi
```

### Step 7: Practical if/else Script

```bash
cat > /tmp/check-system.sh << 'EOF'
#!/bin/bash

# Check available disk space
USAGE=$(df / | awk 'NR==2 { gsub(/%/,""); print $5 }')

if [[ $USAGE -ge 90 ]]; then
    echo "CRITICAL: Disk usage at ${USAGE}%"
elif [[ $USAGE -ge 80 ]]; then
    echo "WARNING: Disk usage at ${USAGE}%"
elif [[ $USAGE -ge 70 ]]; then
    echo "NOTICE: Disk usage at ${USAGE}%"
else
    echo "OK: Disk usage at ${USAGE}%"
fi

# Check if important files exist
for f in /etc/passwd /etc/hostname /etc/os-release; do
    if [[ -f "$f" ]]; then
        echo "OK: $f exists"
    else
        echo "MISSING: $f"
    fi
done
EOF

bash /tmp/check-system.sh
```

## ✅ Verification

```bash
# Test all condition types
NUM=42
[[ $NUM -gt 40 ]] && echo "PASS: numeric comparison" || echo "FAIL"
[[ -f "/etc/passwd" ]] && echo "PASS: file test" || echo "FAIL"
[[ -z "" ]] && echo "PASS: empty string test" || echo "FAIL"
[[ -n "hello" ]] && echo "PASS: non-empty test" || echo "FAIL"
[[ "hello" == "hello" ]] && echo "PASS: string equality" || echo "FAIL"

rm /tmp/testfile.txt /tmp/testdir /tmp/check-system.sh "/tmp/my file.txt" 2>/dev/null
echo "Practitioner Lab 7 complete"
```

## 📝 Summary
- `if [[ condition ]]; then ... elif ...; else ...; fi` is the standard structure
- Numeric comparisons: `-eq`, `-ne`, `-lt`, `-le`, `-gt`, `-ge`
- String tests: `==`, `!=`, `-z` (empty), `-n` (non-empty)
- File tests: `-f` (file), `-d` (dir), `-e` (exists), `-r/-w/-x` (permissions)
- Combine: `&&` for AND, `||` for OR, `!` for NOT
- Use `[[ ]]` instead of `[ ]` — handles spaces and patterns better
