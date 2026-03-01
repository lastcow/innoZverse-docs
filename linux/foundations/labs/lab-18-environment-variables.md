# Lab 18: Environment Variables

## 🎯 Objective
Understand shell environment variables, inspect them with printenv and env, set custom variables with export, and learn about .bashrc.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 17: Getting Help

## 🔬 Lab Instructions

### Step 1: View Environment Variables

```bash
printenv | head -20
env | head -20
printenv | wc -l
```

### Step 2: Read Important Built-in Variables

```bash
echo "USER: $USER"
echo "HOME: $HOME"
echo "SHELL: $SHELL"
echo "PATH: $PATH"
echo "HOSTNAME: $HOSTNAME"
echo "PWD: $PWD"
echo "TERM: $TERM"
echo "LANG: $LANG"
echo "EDITOR: ${EDITOR:-not set}"
```

### Step 3: View a Specific Variable

```bash
printenv HOME
printenv PATH
printenv USER

# Show PATH in readable form (split on :)
echo $PATH | tr ':' '\n'
```

### Step 4: Set and Export Variables

```bash
MY_VAR="hello from shell"
echo $MY_VAR
```

```bash
export MY_APP="myapp-v1.0"
export MY_PORT=9090
echo "App: $MY_APP"
echo "Port: $MY_PORT"

printenv MY_APP
printenv MY_PORT
```

```bash
export GREETING="Hello Linux"
bash -c 'echo "In subshell: $GREETING"'
```

### Step 5: Variable Manipulation

```bash
echo ${UNDEFINED_VAR:-"default value"}
echo ${MY_APP:-"fallback"}
```

```bash
FILE="report-2026-03.txt"
echo "Full: $FILE"
echo "Without extension: ${FILE%.txt}"
echo "Without prefix: ${FILE#report-}"
echo "Upper case: ${FILE^^}"
echo "Length: ${#FILE}"
```

### Step 6: Unset Variables

```bash
export TEMP_VAR="temporary"
echo "Before unset: $TEMP_VAR"
unset TEMP_VAR
echo "After unset: ${TEMP_VAR:-not set}"
```

### Step 7: Understand .bashrc

```bash
head -30 ~/.bashrc 2>/dev/null || echo "~/.bashrc not found"
head -20 ~/.profile 2>/dev/null || echo "~/.profile not found"
```

```bash
cat > /tmp/env-example.sh << 'EOF'
# Example: Add these to ~/.bashrc for persistence
export MY_PROJECT_DIR="/home/zchen/projects"
export EDITOR="vim"
export HISTSIZE=10000
export PATH="$HOME/.local/bin:$PATH"
EOF

echo "Example .bashrc additions:"
cat /tmp/env-example.sh
```

### Step 8: Single-Command Variable

```bash
MY_VAR=test bash -c 'echo $MY_VAR'
echo "After: ${MY_VAR:-not set in parent}"
```

## ✅ Verification

```bash
export LAB18_TEST="verification"
echo "Exported: $(printenv LAB18_TEST)"
echo "User home: $HOME"
echo "PATH has $(echo $PATH | tr ':' '\n' | wc -l) directories"
echo "Shell is: $SHELL"
unset LAB18_TEST
echo "After unset: ${LAB18_TEST:-not set}"
rm /tmp/env-example.sh 2>/dev/null
echo "Lab 18 complete"
```

## 📝 Summary
- `printenv` and `env` show all current environment variables
- Key built-in variables: `$USER`, `$HOME`, `$PATH`, `$SHELL`, `$PWD`
- `export MYVAR="value"` makes a variable available to child processes
- Without `export`, a variable only exists in the current shell
- `${VAR:-default}` uses a default value if the variable is unset
- `~/.bashrc` is loaded for interactive shells — add exports here for persistence
- `unset MYVAR` removes a variable from the environment
