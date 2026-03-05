# Lab 19: Shell Scripting Basics

## Objective
Write real shell scripts: shebang line, variables, if/else, for/while loops, functions, exit codes, and arguments. Scripts automate repetitive tasks — from backups to deployment pipelines.

**Time:** 35 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Your First Script

```bash
cat > /tmp/hello.sh << 'EOF'
#!/bin/bash
NAME=${1:-World}
echo "Hello, $NAME!"
echo "Today is: $(date +%A)"
echo "You are running bash $BASH_VERSION"
EOF

chmod +x /tmp/hello.sh
/tmp/hello.sh
```

**📸 Verified Output:**
```
Hello, World!
Today is: Thursday
You are running bash 5.1.16(1)-release
```

```bash
/tmp/hello.sh Linux
```

**📸 Verified Output:**
```
Hello, Linux!
Today is: Thursday
You are running bash 5.1.16(1)-release
```

> 💡 `#!/bin/bash` is the **shebang** — it tells the kernel which interpreter to use. Without it, the script might run with `sh` (less featured). Always include it as line 1.

---

## Step 2: Variables and Arguments

```bash
cat > /tmp/vars.sh << 'EOF'
#!/bin/bash
# Positional arguments
echo "Script name: $0"
echo "First arg:   $1"
echo "Second arg:  $2"
echo "All args:    $@"
echo "Arg count:   $#"

# Assign to named variables
FILE=$1
DIR=${2:-/tmp}   # default to /tmp if not given

echo ""
echo "File: $FILE"
echo "Dir:  $DIR"
EOF

chmod +x /tmp/vars.sh
/tmp/vars.sh report.txt /var/log
```

**📸 Verified Output:**
```
Script name: /tmp/vars.sh
First arg:   report.txt
Second arg:  /var/log
All args:    report.txt /var/log
Arg count:   2

File: report.txt
Dir:  /var/log
```

---

## Step 3: if / elif / else

```bash
cat > /tmp/check.sh << 'EOF'
#!/bin/bash
FILE=$1
if [ -f "$FILE" ]; then
    echo "File exists: $FILE"
    echo "Size: $(wc -c < "$FILE") bytes"
elif [ -d "$FILE" ]; then
    echo "Directory: $FILE"
    echo "Contents: $(ls "$FILE" | wc -l) items"
else
    echo "Not found: $FILE"
    exit 1
fi
EOF

chmod +x /tmp/check.sh
/tmp/check.sh /etc/passwd
```

**📸 Verified Output:**
```
File exists: /etc/passwd
Size: 922 bytes
```

```bash
/tmp/check.sh /etc
```

**📸 Verified Output:**
```
Directory: /etc
Contents: 36 items
```

```bash
/tmp/check.sh /nonexistent
```

**📸 Verified Output:**
```
Not found: /nonexistent
```

> 💡 Common test conditions: `-f` file exists, `-d` directory exists, `-z` string is empty, `-n` string is non-empty, `-eq` numbers equal, `-lt` less than, `-gt` greater than.

---

## Step 4: for Loop

```bash
cat > /tmp/forloop.sh << 'EOF'
#!/bin/bash
# Loop over a list
echo "=== Days of week ==="
for day in Mon Tue Wed Thu Fri Sat Sun; do
    echo "  $day"
done

# Loop over files
echo ""
echo "=== Config files in /etc ==="
for file in /etc/*.conf; do
    echo "  $(basename $file): $(wc -l < $file) lines"
done | head -5

# Loop with seq
echo ""
echo "=== Countdown ==="
for i in $(seq 5 -1 1); do
    echo -n "$i... "
done
echo "Go!"
EOF

chmod +x /tmp/forloop.sh
/tmp/forloop.sh
```

**📸 Verified Output:**
```
=== Days of week ===
  Mon
  Tue
  Wed
  Thu
  Fri
  Sat
  Sun

=== Config files in /etc ===
  adduser.conf: 76 lines
  debconf.conf: 83 lines
  deluser.conf: 34 lines
  e2scrub.conf: 16 lines
  gai.conf: 56 lines

=== Countdown ===
5... 4... 3... 2... 1... Go!
```

---

## Step 5: while Loop

```bash
cat > /tmp/whileloop.sh << 'EOF'
#!/bin/bash
# Count up while condition is true
count=0
while [ $count -lt 5 ]; do
    echo "  count: $count"
    count=$((count + 1))
done

# Read file line by line
echo ""
echo "=== Reading /etc/shells ==="
while IFS= read -r line; do
    # Skip comments and empty lines
    [[ "$line" =~ ^# ]] && continue
    [[ -z "$line" ]] && continue
    echo "  Shell: $line"
done < /etc/shells
EOF

chmod +x /tmp/whileloop.sh
/tmp/whileloop.sh
```

**📸 Verified Output:**
```
  count: 0
  count: 1
  count: 2
  count: 3
  count: 4

=== Reading /etc/shells ==="
  Shell: /bin/sh
  Shell: /bin/bash
  Shell: /usr/bin/bash
  Shell: /bin/rbash
  Shell: /usr/bin/rbash
  Shell: /usr/bin/sh
  Shell: /bin/dash
  Shell: /usr/bin/dash
```

---

## Step 6: Functions

```bash
cat > /tmp/functions.sh << 'EOF'
#!/bin/bash

# Define a function
log() {
    local LEVEL=$1
    local MSG=$2
    echo "[$(date +%H:%M:%S)] [$LEVEL] $MSG"
}

check_file() {
    local file=$1
    if [ -f "$file" ]; then
        log "INFO" "Found: $file ($(wc -l < "$file") lines)"
        return 0
    else
        log "ERROR" "Missing: $file"
        return 1
    fi
}

# Call functions
log "INFO" "Script started"
check_file /etc/passwd
check_file /etc/hosts
check_file /nonexistent
log "INFO" "Script finished"
EOF

chmod +x /tmp/functions.sh
/tmp/functions.sh
```

**📸 Verified Output:**
```
[01:09:00] [INFO] Script started
[01:09:00] [INFO] Found: /etc/passwd (19 lines)
[01:09:00] [INFO] Found: /etc/hosts (8 lines)
[01:09:00] [ERROR] Missing: /nonexistent
[01:09:00] [INFO] Script finished
```

---

## Step 7: Exit Codes

```bash
cat > /tmp/exit_codes.sh << 'EOF'
#!/bin/bash
# Every command returns an exit code
# 0 = success, non-zero = failure

ls /etc/passwd > /dev/null
echo "ls /etc/passwd exit code: $?"

ls /nonexistent > /dev/null 2>&1
echo "ls /nonexistent exit code: $?"

# Use exit codes for flow control
if grep -q 'root' /etc/passwd; then
    echo "root found in passwd (exit 0 = true)"
fi

# Return custom exit codes from functions
validate() {
    [ -f "$1" ] || { echo "ERROR: $1 not found"; return 1; }
    echo "OK: $1"
    return 0
}

validate /etc/hosts && echo "Validation passed"
validate /nonexistent || echo "Validation failed"
EOF

chmod +x /tmp/exit_codes.sh
/tmp/exit_codes.sh
```

**📸 Verified Output:**
```
ls /etc/passwd exit code: 0
ls /nonexistent exit code: 2
root found in passwd (exit 0 = true)
OK: /etc/hosts
Validation passed
ERROR: /nonexistent not found
Validation failed
```

---

## Step 8: Capstone — System Health Check Script

```bash
cat > /tmp/healthcheck.sh << 'SCRIPT'
#!/bin/bash
PASS=0
WARN=0
FAIL=0

check() {
    local NAME=$1
    local STATUS=$2
    local MSG=$3
    case $STATUS in
        pass) echo "  ✅ $NAME: $MSG"; PASS=$((PASS+1)) ;;
        warn) echo "  ⚠️  $NAME: $MSG"; WARN=$((WARN+1)) ;;
        fail) echo "  ❌ $NAME: $MSG"; FAIL=$((FAIL+1)) ;;
    esac
}

echo "=== System Health Check: $(date) ==="
echo ""

# Check disk space
DISK_USE=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_USE" -lt 70 ]; then
    check "Disk" "pass" "/ at ${DISK_USE}% used"
elif [ "$DISK_USE" -lt 90 ]; then
    check "Disk" "warn" "/ at ${DISK_USE}% used — getting full"
else
    check "Disk" "fail" "/ at ${DISK_USE}% — CRITICAL"
fi

# Check /etc/passwd exists
[ -f /etc/passwd ] && check "passwd" "pass" "exists" || check "passwd" "fail" "missing!"

# Check /etc/shadow permissions
SHADOW_PERM=$(stat -c '%a' /etc/shadow 2>/dev/null)
if [ "$SHADOW_PERM" = "640" ] || [ "$SHADOW_PERM" = "000" ]; then
    check "shadow" "pass" "permissions OK ($SHADOW_PERM)"
else
    check "shadow" "warn" "unusual permissions: $SHADOW_PERM"
fi

# Check Python available
python3 --version &>/dev/null && check "Python3" "pass" "$(python3 --version)" \
    || check "Python3" "warn" "not installed"

echo ""
echo "Results: ✅ $PASS passed  ⚠️  $WARN warnings  ❌ $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
SCRIPT

chmod +x /tmp/healthcheck.sh
/tmp/healthcheck.sh
echo "Exit code: $?"
```

**📸 Verified Output:**
```
=== System Health Check: Thu Mar  5 01:09:00 UTC 2026 ===

  ✅ Disk: / at 36% used
  ✅ passwd: exists
  ✅ shadow: permissions OK (640)
  ✅ Python3: Python 3.10.12

Results: ✅ 4 passed  ⚠️  0 warnings  ❌ 0 failed
Exit code: 0
```

---

## Summary

| Concept | Syntax |
|---------|--------|
| Shebang | `#!/bin/bash` |
| Variable | `NAME=value` |
| Argument 1 | `$1` |
| All arguments | `$@` |
| Last exit code | `$?` |
| if statement | `if [ condition ]; then ... fi` |
| for loop | `for x in list; do ... done` |
| while loop | `while [ cond ]; do ... done` |
| Function | `myfunc() { ...; }` |
| Local variable | `local VAR=value` |
| Default value | `${VAR:-default}` |
