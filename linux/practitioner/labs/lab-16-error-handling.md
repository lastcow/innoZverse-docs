# Lab 16: Error Handling in bash

## 🎯 Objective
Implement robust error handling using set -euo pipefail, trap for cleanup, exit codes, and conditional operators.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Practitioner Labs 7 (Conditionals) and 9 (Functions)

## 🔬 Lab Instructions

### Step 1: Exit Codes

```bash
# Every command returns an exit code: 0=success, non-zero=failure
ls /etc/passwd
echo "Exit code: $?"   # 0 = success

ls /nonexistent 2>/dev/null
echo "Exit code: $?"   # 2 = failure

true
echo "true exit code: $?"   # Always 0

false
echo "false exit code: $?"  # Always 1
```

### Step 2: && and || Operators

```bash
# && runs right side only if left side succeeded
ls /etc/passwd > /dev/null && echo "File exists"
ls /nonexistent > /dev/null 2>&1 && echo "This won't print"

# || runs right side only if left side failed
ls /nonexistent > /dev/null 2>&1 || echo "File not found (expected)"

# Chain them for simple if/else
ls /etc/passwd > /dev/null 2>&1 && echo "Found" || echo "Not found"
```

### Step 3: set -e — Exit on Error

```bash
cat > /tmp/set-e-demo.sh << 'EOF'
#!/bin/bash
set -e   # Exit immediately on error

echo "Step 1: OK"
echo "Step 2: OK"
ls /nonexistent    # This will fail and exit
echo "Step 3: This will NOT run"
EOF

bash /tmp/set-e-demo.sh || true 2>/dev/null
echo "Script exited with code: $?"
```

**Expected output:**
```
Step 1: OK
Step 2: OK
Script exited with code: 2
```

### Step 4: set -u — Error on Undefined Variables

```bash
cat > /tmp/set-u-demo.sh << 'EOF'
#!/bin/bash
set -u   # Error on undefined variables

DEFINED_VAR="hello"
echo "Defined: $DEFINED_VAR"
echo "Undefined: $UNDEFINED_VAR"   # This will cause an error
EOF

bash /tmp/set-u-demo.sh || true 2>/dev/null
echo "Script exit code: $?"
```

### Step 5: set -o pipefail — Catch Pipeline Failures

```bash
# Without pipefail: pipeline exit code = last command's code
ls /nonexistent 2>/dev/null | echo "Piped"
echo "Without pipefail: $?"   # 0 because echo succeeded

# With pipefail: pipeline fails if ANY command fails
cat > /tmp/pipefail-demo.sh << 'EOF'
#!/bin/bash
set -o pipefail
ls /nonexistent 2>/dev/null | echo "Piped"
echo "Exit: $?"
EOF

bash /tmp/pipefail-demo.sh || true
```

### Step 6: set -euo pipefail Together

```bash
cat > /tmp/robust-script.sh << 'EOF'
#!/bin/bash
set -euo pipefail

WORK_DIR="/tmp/robust-test"
mkdir -p "$WORK_DIR"

echo "Working in: $WORK_DIR"

# All operations must succeed
echo "data" > "$WORK_DIR/data.txt"
cp "$WORK_DIR/data.txt" "$WORK_DIR/backup.txt"
echo "Files created: $(ls $WORK_DIR | wc -l)"

echo "Script completed successfully"
EOF

bash /tmp/robust-script.sh
echo "Exit code: $?"
```

### Step 7: trap for Cleanup

```bash
cat > /tmp/trap-demo.sh << 'EOF'
#!/bin/bash
set -euo pipefail

TEMP_DIR=$(mktemp -d /tmp/trap-test.XXXXXX)
echo "Created temp dir: $TEMP_DIR"

# Cleanup function
cleanup() {
    echo "Running cleanup..."
    rm -rf "$TEMP_DIR"
    echo "Temp dir removed"
}

# Register trap: run cleanup on EXIT (normal or error)
trap cleanup EXIT

# Also trap specific signals
trap 'echo "Interrupted!"; exit 130' INT TERM

# Do some work
echo "Working..." > "$TEMP_DIR/work.txt"
echo "Data processed"

# Cleanup runs automatically when script exits
EOF

bash /tmp/trap-demo.sh
ls /tmp/trap-test.* 2>/dev/null || echo "Temp dir was cleaned up"
```

### Step 8: Custom Error Messages

```bash
cat > /tmp/error-handling.sh << 'EOF'
#!/bin/bash
set -euo pipefail

# Error handler function
die() {
    local msg="$1"
    local code="${2:-1}"
    echo "ERROR: $msg" >&2
    exit "$code"
}

# Validate input
validate_dir() {
    local dir="$1"
    [[ -d "$dir" ]] || die "Directory not found: $dir" 2
    [[ -r "$dir" ]] || die "Directory not readable: $dir" 3
    echo "Directory OK: $dir" || true
}

validate_dir "/etc"
validate_dir "/tmp"
validate_dir "/nonexistent" 2>/dev/null || echo "Caught error from validate_dir"
echo "Done"
EOF

bash /tmp/error-handling.sh || true
```

## ✅ Verification

```bash
# Test exit codes
true; echo "true: $?"
false; echo "false: $?"

# Test && and ||
true && echo "PASS: && works"
false || echo "PASS: || works"

# Test trap
cat > /tmp/trap-verify.sh << 'EOF'
#!/bin/bash
trap 'echo "Trap fired"' EXIT
echo "Inside script"
EOF
bash /tmp/trap-verify.sh

rm /tmp/set-e-demo.sh /tmp/set-u-demo.sh /tmp/pipefail-demo.sh /tmp/robust-script.sh /tmp/trap-demo.sh /tmp/error-handling.sh /tmp/trap-verify.sh /tmp/robust-test 2>/dev/null
rm -rf /tmp/robust-test 2>/dev/null
echo "Practitioner Lab 16 complete"
```

## 📝 Summary
- `$?` holds the exit code of the last command: 0=success, non-zero=failure
- `&&` runs next command only on success; `||` only on failure
- `set -e` exits the script immediately when any command fails
- `set -u` treats undefined variables as errors
- `set -o pipefail` makes pipelines fail if any component fails
- `trap cleanup EXIT` ensures cleanup code runs even on errors
- Always write a `die()` function for consistent error messages
