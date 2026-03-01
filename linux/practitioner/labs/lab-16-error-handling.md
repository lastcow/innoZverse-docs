# Lab 16: Error Handling in Bash Scripts

## 🎯 Objective
Write robust scripts using `set -e`, `set -u`, `set -o pipefail`, `trap` for cleanup, and meaningful exit codes.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Labs 7–9 (Conditionals, Loops, Functions)

## 🔬 Lab Instructions

### Step 1: Understand Exit Codes
```bash
ls /etc/hosts
echo "Exit code: $?"    # 0 = success

ls /nonexistent 2>/dev/null
echo "Exit code: $?"    # 2 = error

true;  echo $?    # 0
false; echo $?    # 1
```

### Step 2: The Problem Without Error Handling
```bash
cat > /tmp/bad_script.sh << 'EOF'
#!/bin/bash
cd /nonexistent_dir
echo "This should NOT print if cd failed"
touch important_file.txt
EOF
bash /tmp/bad_script.sh
# bash: line 2: cd: /nonexistent_dir: No such file or directory
# This should NOT print if cd failed   <-- problem!
```

### Step 3: set -e — Exit on Error
```bash
cat > /tmp/set_e.sh << 'EOF'
#!/bin/bash
set -e
echo "Step 1: start"
cd /nonexistent_dir    # will fail and exit here
echo "Step 2: this never runs"
EOF
bash /tmp/set_e.sh
# Step 1: start
# bash: line 4: cd: /nonexistent_dir: No such file or directory
# (script exits immediately)
```

### Step 4: set -u — Error on Undefined Variables
```bash
cat > /tmp/set_u.sh << 'EOF'
#!/bin/bash
set -u
name="Alice"
echo "Hello, $name"
echo "Age: $age"    # $age is undefined
EOF
bash /tmp/set_u.sh
# Hello, Alice
# bash: age: unbound variable
```

### Step 5: set -o pipefail — Catch Pipeline Failures
```bash
# Without pipefail, only last command exit code matters
cat /nonexistent_file 2>/dev/null | grep "foo"
echo "Exit code: $?"    # 0 (grep succeeded on empty input)

cat > /tmp/pipefail.sh << 'EOF'
#!/bin/bash
set -o pipefail
cat /nonexistent_file | grep "foo"
echo "This won't print"
EOF
bash /tmp/pipefail.sh 2>/dev/null
echo "Exit code: $?"    # non-zero (pipeline failed)
```

### Step 6: Combine All Three (Best Practice Header)
```bash
cat > ~/robust_header.sh << 'EOF'
#!/bin/bash
set -euo pipefail
IFS=$'\n\t'   # safer word splitting

echo "Script started safely"
echo "User: $USER"
echo "Host: $(hostname)"
EOF
chmod +x ~/robust_header.sh
~/robust_header.sh
# Script started safely
# User: ubuntu
# Host: myserver
```

### Step 7: trap for Cleanup on Exit
```bash
cat > ~/trap_demo.sh << 'EOF'
#!/bin/bash
set -euo pipefail

TMPFILE=$(mktemp)
echo "Created temp file: $TMPFILE"

cleanup() {
    echo "Cleaning up: removing $TMPFILE"
    rm -f "$TMPFILE"
}
trap cleanup EXIT

echo "Working with $TMPFILE..."
echo "some data" > "$TMPFILE"
cat "$TMPFILE"
echo "Script complete"
# cleanup runs automatically on exit
EOF
chmod +x ~/trap_demo.sh
~/trap_demo.sh
# Created temp file: /tmp/tmp.XXXXXXXX
# Working with /tmp/tmp.XXXXXXXX...
# some data
# Script complete
# Cleaning up: removing /tmp/tmp.XXXXXXXX
```

### Step 8: trap on Specific Signals
```bash
cat > ~/signal_trap.sh << 'EOF'
#!/bin/bash
handle_int() {
    echo ""
    echo "Caught SIGINT (Ctrl+C). Exiting cleanly."
    exit 130
}
trap handle_int INT

echo "Running... press Ctrl+C to test"
for i in $(seq 1 30); do
    echo "Tick $i"
    sleep 1
done
EOF
chmod +x ~/signal_trap.sh
# Run ~/signal_trap.sh and press Ctrl+C:
# Tick 1
# Tick 2
# ^C
# Caught SIGINT (Ctrl+C). Exiting cleanly.
```

### Step 9: Return Custom Exit Codes
```bash
cat > ~/check_service.sh << 'EOF'
#!/bin/bash
set -euo pipefail
SERVICE="${1:-ssh}"

if systemctl is-active --quiet "$SERVICE"; then
    echo "$SERVICE is running"
    exit 0
else
    echo "$SERVICE is NOT running" >&2
    exit 1
fi
EOF
chmod +x ~/check_service.sh

~/check_service.sh ssh
echo "Exit: $?"    # Exit: 0

~/check_service.sh fakesvc 2>/dev/null || echo "Service check failed (exit $?)"
# Service check failed (exit 1)
```

### Step 10: Error Function Pattern
```bash
cat > ~/error_pattern.sh << 'EOF'
#!/bin/bash
set -euo pipefail

log()   { echo "[$(date +%T)] INFO : $*"; }
error() { echo "[$(date +%T)] ERROR: $*" >&2; exit 1; }

DATADIR="${1:-/tmp/mydata}"
mkdir -p "$DATADIR" || error "Cannot create directory: $DATADIR"
log "Data directory ready: $DATADIR"

CONFIGFILE="$DATADIR/config.txt"
[[ -f "$CONFIGFILE" ]] || error "Config not found: $CONFIGFILE"
log "Config loaded"
EOF
chmod +x ~/error_pattern.sh
~/error_pattern.sh /tmp/testdata
# [06:01:23] INFO : Data directory ready: /tmp/testdata
# [06:01:23] ERROR: Config not found: /tmp/testdata/config.txt
```

## ✅ Verification
```bash
cat > /tmp/verify.sh << 'EOF'
#!/bin/bash
set -euo pipefail
trap 'echo "Exited at line $LINENO"' EXIT
echo "All error guards active"
EOF
bash /tmp/verify.sh
# All error guards active
# Exited at line 4
```

## 📝 Summary
- `set -e` exits script on any non-zero command
- `set -u` errors on undefined variables
- `set -o pipefail` makes pipeline failures propagate
- `trap cleanup EXIT` ensures cleanup runs even on error or signal
- Custom exit codes (0=ok, 1=error) make scripts composable
- Always write error messages to stderr: `echo "error" >&2`
