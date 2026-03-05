# Lab 04: Shell Scripting — Error Handling

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Robust scripts don't just work when everything is fine — they fail *gracefully* and *loudly* when something goes wrong. In this lab you'll use `set -e`, `set -u`, `set -o pipefail` to make scripts fail fast, `trap` to run cleanup on exit or error, build custom error functions, understand exit codes, and chain commands with `&&` and `||`.

---

## Step 1: set -e — Exit on Error

By default, Bash continues executing even after a command fails. `set -e` changes that:

```bash
set -e
echo "Before error"
false          # returns exit code 1
echo "This should not print"
```

📸 **Verified Output:**
```
Before error
```
*(Script exits immediately after `false`; the last line never runs.)*

> 💡 **Tip:** `set -e` can be counterintuitive — it also triggers on `[ false ]` and other exit-1 commands in conditions. Use `command || true` to explicitly allow a command to fail without killing the script.

---

## Step 2: set -u — Treat Unset Variables as Errors

Accessing an unset variable silently returns empty string by default — a common source of bugs:

```bash
set -u
echo "Defined: hello"
echo "Undefined: $undefined_var"
```

📸 **Verified Output:**
```
Defined: hello
bash: line 4: undefined_var: unbound variable
```
*(Script exits on the unset variable access.)*

> 💡 **Tip:** Use `${var:-default}` to provide a fallback when a variable might be unset without triggering `set -u`. Example: `${CONFIG_FILE:-/etc/default.conf}`.

---

## Step 3: set -o pipefail — Catch Pipeline Failures

Without `pipefail`, a pipeline's exit status is only the last command's status — earlier failures are silently swallowed:

```bash
set -o pipefail
false | echo "pipe continues..."
echo "exit: $?"
```

📸 **Verified Output:**
```
pipe continues...
exit: 1
```

> 💡 **Tip:** The golden combination for reliable scripts is to put `set -euo pipefail` at the very top of every script. These three options together catch the most common silent failures.

---

## Step 4: trap — Cleanup on EXIT

`trap` registers a handler that runs automatically when the script exits, regardless of whether it exited cleanly or due to an error:

```bash
cleanup() {
  echo "Cleanup running on exit"
}
trap cleanup EXIT
echo "Doing work..."
echo "Done."
```

📸 **Verified Output:**
```
Doing work...
Done.
Cleanup running on exit
```

> 💡 **Tip:** Use `trap` to remove temporary files, release locks, or kill background processes. The EXIT trap fires on both successful exit and error — which is exactly what you want for cleanup.

---

## Step 5: trap ERR — Catch Errors with Line Numbers

The ERR trap fires whenever a command returns a non-zero exit code:

```bash
on_error() {
  echo "ERROR at line $1"
}
trap 'on_error $LINENO' ERR
echo "Step 1"
false
echo "Step 2"
```

📸 **Verified Output:**
```
Step 1
ERROR at line 7
Step 2
```

> 💡 **Tip:** With `set -e` enabled, the ERR trap fires and then the script exits. Without `set -e`, execution continues after the ERR trap. Combine both for maximum reliability: the trap logs context, then `set -e` stops execution.

---

## Step 6: Custom Error Functions and Exit Codes

A `die()` function gives you a consistent, readable way to fail with a message and specific exit code:

```bash
die() {
  echo "FATAL: $1" >&2
  exit "${2:-1}"
}
check_file() {
  [ -f "$1" ] || die "File not found: $1" 2
}
check_file /nonexistent
```

📸 **Verified Output:**
```
FATAL: File not found: /nonexistent
```
*(Script exits with code 2.)*

> 💡 **Tip:** Always write error messages to stderr (`>&2`), not stdout. This lets callers capture only the useful output with `result=$(script.sh)` while error messages still appear on the terminal.

---

## Step 7: && and || Chains

`&&` runs the next command only on success; `||` runs it only on failure — a compact alternative to `if/else` for simple cases:

```bash
mkdir -p /tmp/mydir && echo "mkdir succeeded"
cat /nonexistent 2>/dev/null || echo "cat failed, fallback used"
```

📸 **Verified Output:**
```
mkdir succeeded
cat failed, fallback used
```

> 💡 **Tip:** Chain multiple operations: `cmd1 && cmd2 && cmd3 || handle_failure`. The entire chain short-circuits on first failure and runs `handle_failure`. For complex logic, prefer `if` blocks — chains become unreadable beyond 2–3 commands.

---

## Step 8: Capstone — Production-Grade Script Header

Combine all error handling techniques into a template used by real production scripts:

```bash
#!/usr/bin/env bash
set -euo pipefail

# ── Constants ──────────────────────────────────────────────
SCRIPT_NAME="$(basename "$0")"
TMPDIR_WORK="$(mktemp -d)"
LOG_FILE="/tmp/${SCRIPT_NAME}.log"

# ── Logging ────────────────────────────────────────────────
log()  { echo "[INFO]  $*" | tee -a "$LOG_FILE"; }
warn() { echo "[WARN]  $*" | tee -a "$LOG_FILE" >&2; }
die()  { echo "[FATAL] $*" | tee -a "$LOG_FILE" >&2; exit 1; }

# ── Cleanup ────────────────────────────────────────────────
cleanup() {
  local exit_code=$?
  log "Cleanup: removing temp dir $TMPDIR_WORK"
  rm -rf "$TMPDIR_WORK"
  [ $exit_code -eq 0 ] && log "Script completed successfully" \
                        || warn "Script exited with code $exit_code"
}
trap cleanup EXIT
trap 'die "Unexpected error on line $LINENO"' ERR
trap 'warn "Interrupted by user"; exit 130' INT

# ── Main ───────────────────────────────────────────────────
log "Starting $SCRIPT_NAME"
log "Working directory: $TMPDIR_WORK"

# Simulate work with a potential failure
echo "data" > "$TMPDIR_WORK/output.txt"
[ -f "$TMPDIR_WORK/output.txt" ] && log "Output file created" || die "Output missing"

log "All steps completed"
```

📸 **Verified Output:**
```
[INFO]  Starting bash
[INFO]  Working directory: /tmp/tmp.XXXXXX
[INFO]  Output file created
[INFO]  All steps completed
[INFO]  Cleanup: removing temp dir /tmp/tmp.XXXXXX
[INFO]  Script completed successfully
```

> 💡 **Tip:** This header is a template — save it as `script_template.sh` and copy it as the foundation of every new script. The combination of `set -euo pipefail` + `trap cleanup EXIT` + `trap die ERR` catches virtually all common failure modes automatically.

---

## Summary

| Technique | What It Does | When to Use |
|---|---|---|
| `set -e` | Exit on any command failure | Almost always |
| `set -u` | Error on unset variables | Almost always |
| `set -o pipefail` | Pipe fails if any stage fails | Almost always |
| `trap ... EXIT` | Run cleanup on any exit | Resource cleanup (temp files, locks) |
| `trap ... ERR` | Run handler on any error | Logging error context |
| `trap ... INT` | Handle Ctrl-C | User-facing interactive scripts |
| `die()` function | Log to stderr + exit | Fatal errors with context |
| `echo >&2` | Write to stderr | Error/warning messages |
| `cmd && next` | Run next only on success | Sequential dependent steps |
| `cmd \|\| fallback` | Run fallback on failure | Default values, recovery |
| `exit N` | Exit with specific code | Signal specific failure types |
| `${var:-default}` | Unset variable fallback | Work with `set -u` |
