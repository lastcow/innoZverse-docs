# Lab 7: Bash Conditionals

## 🎯 Objective
Write bash conditionals using `if/elif/else`, the `test` command, `[[]]` extended tests, and comparison operators for strings, numbers, and files.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Practitioner Lab 6 (shell variables)
- Basic bash scripting knowledge

## 🔬 Lab Instructions

### Step 1: Basic if Statement
```bash
# if condition; then ... fi
if true; then
  echo "Condition is true"
fi

# Always check exit code: 0 = true, non-zero = false
if ls /etc > /dev/null 2>&1; then
  echo "/etc exists"
fi
```

### Step 2: if/else Structure
```bash
age=25

if [ $age -ge 18 ]; then
  echo "Adult"
else
  echo "Minor"
fi
```

### Step 3: if/elif/else Chain
```bash
score=75

if [ $score -ge 90 ]; then
  echo "Grade: A"
elif [ $score -ge 80 ]; then
  echo "Grade: B"
elif [ $score -ge 70 ]; then
  echo "Grade: C"
elif [ $score -ge 60 ]; then
  echo "Grade: D"
else
  echo "Grade: F"
fi
```

### Step 4: test Command and [ ] Syntax
```bash
# [ ] is an alias for the test command
# Numeric comparisons: -eq -ne -lt -le -gt -ge
x=10
[ $x -eq 10 ] && echo "equal"
[ $x -ne 5 ]  && echo "not equal to 5"
[ $x -gt 5 ]  && echo "greater than 5"
[ $x -lt 20 ] && echo "less than 20"
[ $x -ge 10 ] && echo "greater or equal to 10"
[ $x -le 10 ] && echo "less or equal to 10"
```

### Step 5: String Comparisons
```bash
name="Alice"

# String equality
if [ "$name" = "Alice" ]; then
  echo "Hello, Alice!"
fi

# Not equal
if [ "$name" != "Bob" ]; then
  echo "You are not Bob"
fi

# Empty string check
if [ -z "$name" ]; then
  echo "name is empty"
else
  echo "name is set: $name"
fi

# Non-empty string check
if [ -n "$name" ]; then
  echo "name is not empty"
fi
```

### Step 6: [[ ]] Extended Test — Preferred in bash
```bash
# [[ ]] is bash-specific, more powerful than [ ]
# No word splitting, so no need to always quote

name="Alice Smith"

# Pattern matching with ==
if [[ "$name" == Alice* ]]; then
  echo "Name starts with Alice"
fi

# Regex matching with =~
if [[ "$name" =~ ^[A-Z][a-z]+ ]]; then
  echo "Name starts with a capital letter"
fi

# Logical operators: && and ||
age=25
if [[ $age -ge 18 && $age -lt 65 ]]; then
  echo "Working age adult"
fi
```

### Step 7: File Test Operators
```bash
# -f: is a regular file
# -d: is a directory
# -e: exists (file or dir)
# -r: is readable
# -w: is writable
# -x: is executable
# -s: exists and is not empty
# -L: is a symbolic link

file="/etc/passwd"
if [ -f "$file" ]; then
  echo "$file is a regular file"
fi

if [ -r "$file" ]; then
  echo "$file is readable"
fi

dir="/tmp"
if [ -d "$dir" ]; then
  echo "$dir is a directory"
fi

# Check if file is non-empty
if [ -s "$file" ]; then
  echo "$file is not empty"
fi
```

### Step 8: Logical Operators in Conditions
```bash
# AND: -a in [ ], && in [[ ]]
x=15
if [ $x -gt 10 ] && [ $x -lt 20 ]; then
  echo "x is between 10 and 20"
fi

# OR: -o in [ ], || in [[ ]]
color="red"
if [[ "$color" == "red" || "$color" == "blue" ]]; then
  echo "Color is red or blue"
fi

# NOT: !
if ! [ -f /tmp/nonexistent ]; then
  echo "/tmp/nonexistent does not exist"
fi
```

### Step 9: Case Statement
```bash
day="Monday"

case $day in
  Monday|Tuesday|Wednesday|Thursday|Friday)
    echo "Weekday"
    ;;
  Saturday|Sunday)
    echo "Weekend"
    ;;
  *)
    echo "Unknown day"
    ;;
esac
```

### Step 10: Ternary-Style with && and ||
```bash
# If condition, then do A; else do B
[ -f /etc/passwd ] && echo "file exists" || echo "file missing"

# Assign based on condition
status=$([ -f /etc/passwd ] && echo "present" || echo "missing")
echo "Status: $status"
```

### Step 11: Checking Command Success
```bash
# Check if a command succeeds
if ping -c 1 -W 1 8.8.8.8 &>/dev/null; then
  echo "Network is up"
else
  echo "Network is unreachable"
fi

# Check if a package is installed
if dpkg -l curl 2>/dev/null | grep -q "^ii"; then
  echo "curl is installed"
else
  echo "curl is not installed"
fi
```

### Step 12: Practical Script — System Check
```bash
cat > /tmp/syscheck.sh << 'EOF'
#!/bin/bash
echo "=== System Check ==="

# Check disk space
usage=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$usage" -gt 90 ]; then
  echo "WARNING: Disk usage is ${usage}%"
elif [ "$usage" -gt 75 ]; then
  echo "NOTICE: Disk usage is ${usage}%"
else
  echo "OK: Disk usage is ${usage}%"
fi

# Check if SSH is running
if systemctl is-active --quiet ssh 2>/dev/null; then
  echo "OK: SSH is running"
else
  echo "WARNING: SSH is not running"
fi
EOF
chmod +x /tmp/syscheck.sh
bash /tmp/syscheck.sh
rm /tmp/syscheck.sh
```

## ✅ Verification
```bash
# Test file operators
[ -f /etc/passwd ] && echo "PASS: file exists" || echo "FAIL"
[ -d /tmp ] && echo "PASS: dir exists" || echo "FAIL"
[ ! -f /tmp/nonexistent ] && echo "PASS: file missing confirmed" || echo "FAIL"

# Test string comparison
name="test"
[[ "$name" == t* ]] && echo "PASS: pattern match" || echo "FAIL"
```

## 📝 Summary
- `if condition; then ... elif ...; else ...; fi` is the full conditional structure
- `[ ]` (test) works in all POSIX shells; `[[ ]]` is bash-specific and more powerful
- Numeric operators: `-eq -ne -lt -le -gt -ge`; string: `= != -z -n`
- File tests: `-f` (file), `-d` (dir), `-e` (exists), `-r/-w/-x` (permissions), `-s` (non-empty)
- `[[ ]]` supports glob patterns (`==`) and regex (`=~`) — prefer it in bash scripts
- `case` is cleaner than long `if/elif` chains for matching a variable against multiple values

