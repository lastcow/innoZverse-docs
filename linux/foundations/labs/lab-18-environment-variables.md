# Lab 18: Environment Variables

## Objective
Understand, inspect, set, and use environment variables: `PATH`, `HOME`, `USER`, `export`, `.bashrc`, `.profile`, and how environment variables control program behaviour and pass configuration to applications.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Viewing Environment Variables

```bash
printenv | head -8
```

**📸 Verified Output:**
```
HOSTNAME=b77d3fb36284
PWD=/
HOME=/root
SHLVL=0
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
_=/usr/bin/printenv
```

```bash
echo "HOME:  $HOME"
echo "PATH:  $PATH"
```

**📸 Verified Output:**
```
HOME:  /root
PATH:  /usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

> 💡 Variables are accessed by prefixing with `$`. `$HOME` expands to `/root`. Curly braces `${HOME}` are equivalent and required when concatenating: `${HOME}_backup`.

---

## Step 2: The PATH Variable

`PATH` is a colon-separated list of directories searched when you type a command:

```bash
echo $PATH | tr ':' '\n'
```

**📸 Verified Output:**
```
/usr/local/sbin
/usr/local/bin
/usr/sbin
/usr/bin
/sbin
/bin
```

```bash
which bash
which ls
which python3
```

**📸 Verified Output:**
```
/usr/bin/bash
/usr/bin/ls
/usr/bin/python3
```

> 💡 The shell searches PATH **left-to-right**. Putting a directory first gives it priority. Security note: attackers who control a directory earlier in PATH can plant fake `ls`, `cat`, etc. — always verify PATH is trusted on compromised systems.

---

## Step 3: Setting and Exporting Variables

```bash
# Local variable — only this shell session
MY_VAR="hello"
echo $MY_VAR
```

**📸 Verified Output:**
```
hello
```

```bash
# Export — child processes inherit it
export APP_ENV="production"
export DB_HOST="localhost"
export DB_PORT="5432"

env | grep -E '^(APP_ENV|DB_HOST|DB_PORT)'
```

**📸 Verified Output:**
```
APP_ENV=production
DB_HOST=localhost
DB_PORT=5432
```

> 💡 Without `export`, child processes (scripts you call) **cannot** see the variable. With `export`, it's in the environment — all child processes inherit it automatically.

---

## Step 4: Variable Expansion and Defaults

```bash
# Default if unset
echo "${UNDEFINED:-fallback_value}"
```

**📸 Verified Output:**
```
fallback_value
```

```bash
# Command substitution
TODAY=$(date +%Y-%m-%d)
HOST=$(hostname)
echo "Date: $TODAY  Host: $HOST"
```

**📸 Verified Output:**
```
Date: 2026-03-05  Host: b77d3fb36284
```

```bash
# Arithmetic
X=10; Y=3
echo "Sum: $((X + Y))  Product: $((X * Y))  Modulo: $((X % Y))"
```

**📸 Verified Output:**
```
Sum: 13  Product: 30  Modulo: 1
```

---

## Step 5: Unsetting Variables

```bash
export TESTVAR=42
echo "Set:   $TESTVAR"

unset TESTVAR
echo "Unset: [${TESTVAR:-empty}]"
```

**📸 Verified Output:**
```
Set:   42
Unset: [empty]
```

---

## Step 6: Persistent Variables — .bashrc and .profile

```bash
# View current .bashrc (non-comment lines)
grep -v '^#' /root/.bashrc | grep -v '^$' | head -8
```

**📸 Verified Output:**
```
[ -z "$PS1" ] && return
HISTCONTROL=ignoredups:ignorespace
shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000
shopt -s checkwinsize
```

```bash
# Add a persistent export
echo 'export MY_APP_KEY="dev-key-12345"' >> /root/.bashrc
grep MY_APP_KEY /root/.bashrc
```

**📸 Verified Output:**
```
export MY_APP_KEY="dev-key-12345"
```

> 💡 `.bashrc` loads for every new interactive shell. `.profile` loads for login shells. Changes take effect in new sessions — or run `source ~/.bashrc` to apply immediately in the current shell.

---

## Step 7: Per-Command Environment

```bash
cat > /tmp/show_env.sh << 'EOF'
#!/bin/bash
echo "APP_ENV=${APP_ENV:-not set}"
echo "DB_HOST=${DB_HOST:-not set}"
echo "LOG_LEVEL=${LOG_LEVEL:-not set}"
EOF
chmod +x /tmp/show_env.sh

# Pass variables only to this one command
APP_ENV=staging DB_HOST=db.staging.example LOG_LEVEL=DEBUG /tmp/show_env.sh
echo ""
# They don't persist in the parent shell
echo "In parent: APP_ENV=${APP_ENV:-still not set}"
```

**📸 Verified Output:**
```
APP_ENV=staging
DB_HOST=db.staging.example
LOG_LEVEL=DEBUG

In parent: APP_ENV=still not set
```

---

## Step 8: Capstone — 12-Factor App Config Validator

```bash
cat > /tmp/config_check.sh << 'SCRIPT'
#!/bin/bash
# 12-Factor App: store ALL config in environment variables
echo "=== Configuration Validation ==="

REQUIRED_VARS="DATABASE_URL SECRET_KEY"
OPTIONAL_VARS="LOG_LEVEL PORT"
MISSING=0

for var in $REQUIRED_VARS; do
    if [ -z "${!var}" ]; then
        echo "  ❌ MISSING (required): $var"
        MISSING=$((MISSING + 1))
    else
        MASKED="${!var:0:4}****"
        echo "  ✅ $var = $MASKED"
    fi
done

for var in $OPTIONAL_VARS; do
    VAL="${!var:-<default>}"
    echo "  ℹ️  $var = $VAL"
done

echo ""
if [ $MISSING -gt 0 ]; then
    echo "  ❌ $MISSING required variable(s) missing. Cannot start."
    exit 1
else
    echo "  ✅ All required config present. Starting app..."
fi
SCRIPT
chmod +x /tmp/config_check.sh

echo "--- Without vars ---"
/tmp/config_check.sh; echo ""

echo "--- With vars set ---"
DATABASE_URL="postgres://user:pass@localhost/mydb" \
SECRET_KEY="s3cr3tk3y-abc123" \
PORT=8080 \
/tmp/config_check.sh
```

**📸 Verified Output:**
```
--- Without vars ---
=== Configuration Validation ===
  ❌ MISSING (required): DATABASE_URL
  ❌ MISSING (required): SECRET_KEY
  ℹ️  LOG_LEVEL = <default>
  ℹ️  PORT = <default>

  ❌ 2 required variable(s) missing. Cannot start.

--- With vars set ---
=== Configuration Validation ===
  ✅ DATABASE_URL = post****
  ✅ SECRET_KEY = s3cr****
  ℹ️  LOG_LEVEL = <default>
  ℹ️  PORT = 8080

  ✅ All required config present. Starting app...
```

---

## Summary

| Command / Syntax | Purpose |
|-----------------|---------|
| `echo $VAR` | Print variable |
| `export VAR=val` | Set + export to child processes |
| `unset VAR` | Delete variable |
| `printenv` | Print all environment |
| `env` | Same as printenv |
| `${VAR:-default}` | Use default if unset |
| `$(command)` | Command substitution |
| `VAR=x cmd` | Set variable for one command only |
| `source ~/.bashrc` | Reload config in current shell |
| `which cmd` | Find command location in PATH |
