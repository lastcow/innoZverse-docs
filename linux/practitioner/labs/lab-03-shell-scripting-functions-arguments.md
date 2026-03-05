# Lab 03: Shell Scripting — Functions & Arguments

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Functions transform scripts from linear sequences into reusable, testable components. In this lab you'll define functions, scope variables with `local`, capture return values, work with special argument variables (`$0`, `$1`, `$@`, `$#`, `$?`), parse command-line options with `getopts`, and use `shift` to consume arguments.

---

## Step 1: Defining and Calling Functions

Two equivalent syntaxes exist. The `function` keyword is optional:

```bash
greet() {
  echo "Hello, $1!"
}
greet "World"
greet "Alice"
```

📸 **Verified Output:**
```
Hello, World!
Hello, Alice!
```

> 💡 **Tip:** Functions must be defined before they're called (Bash reads top-to-bottom). A common pattern is to define all functions at the top, then have a `main()` function at the bottom that runs last.

---

## Step 2: Local Variables — Scope Isolation

Without `local`, all variables in a function are global and can corrupt outer state:

```bash
x="global"
demo() {
  local x="local"
  echo "Inside: $x"
}
demo
echo "Outside: $x"
```

📸 **Verified Output:**
```
Inside: local
Outside: global
```

> 💡 **Tip:** Always use `local` for variables inside functions. This is especially critical when function names shadow global variables. A bug where an inner function modifies an outer variable is extremely hard to track down.

---

## Step 3: Return Values — Numeric Exit Codes

Bash `return` only returns integers 0–255 (the function's exit status). To return string/complex data, use `echo` and command substitution:

```bash
add() {
  echo $(( $1 + $2 ))
}
result=$(add 7 3)
echo "7 + 3 = $result"
```

📸 **Verified Output:**
```
7 + 3 = 10
```

> 💡 **Tip:** The pattern `result=$(func args)` captures everything the function prints to stdout. This makes functions composable — the output of one function can become the input of another.

---

## Step 4: Special Variables — $0, $1, $@, $#

These automatic variables let functions and scripts know about their invocation context:

```bash
show_args() {
  echo "Script name: $0"
  echo "Arg count: $#"
  echo "All args: $@"
  echo "First: $1"
  echo "Second: $2"
}
show_args alpha beta gamma
```

📸 **Verified Output:**
```
Script name: bash
Arg count: 3
All args: alpha beta gamma
First: alpha
Second: beta
```

> 💡 **Tip:** Inside a function, `$0` still refers to the script name (not the function name). To get the function's name, use `${FUNCNAME[0]}`. The `$@` variable is the gold standard for passing all arguments to another command — it preserves quoting correctly.

---

## Step 5: Exit Status — $?

`$?` holds the exit code of the last command. `0` means success; non-zero means failure:

```bash
is_even() {
  [ $(( $1 % 2 )) -eq 0 ] && return 0 || return 1
}
is_even 4 && echo "4 is even" || echo "4 is odd"
is_even 7 && echo "7 is even" || echo "7 is odd"
```

📸 **Verified Output:**
```
4 is even
7 is odd
```

> 💡 **Tip:** Check `$?` immediately after a command — the next command will overwrite it. For clarity, assign it: `status=$?; if [ $status -ne 0 ]; then ...`. Or use `if command; then` directly.

---

## Step 6: shift — Consuming Arguments

`shift` removes `$1` and shifts all other positional parameters down:

```bash
show() {
  while [ $# -gt 0 ]; do
    echo "Arg: $1"
    shift
  done
}
show one two three
```

📸 **Verified Output:**
```
Arg: one
Arg: two
Arg: three
```

> 💡 **Tip:** `shift N` shifts N positions at once. This is useful for skipping past an option and its value together: after parsing `-o value`, call `shift 2` to consume both. Without `shift`, the loop would never terminate.

---

## Step 7: getopts — Proper Option Parsing

`getopts` is the POSIX-standard way to parse `-f`, `-v`, `-n value` style options:

```bash
parse() {
  local name="" verbose=false
  while getopts "n:v" opt; do
    case $opt in
      n) name="$OPTARG" ;;
      v) verbose=true ;;
    esac
  done
  echo "Name: $name"
  echo "Verbose: $verbose"
}
parse -n Bob -v
```

📸 **Verified Output:**
```
Name: Bob
Verbose: true
```

> 💡 **Tip:** A colon after a letter in the `getopts` string (like `n:`) means that option requires an argument, available via `$OPTARG`. After `getopts` finishes, `shift $((OPTIND - 1))` removes all parsed options, leaving only positional arguments in `$@`.

---

## Step 8: Capstone — Reusable Script Library

Build a small library of utility functions with proper argument handling, exit codes, and option parsing — the kind you'd `source` into real scripts:

```bash
#!/usr/bin/env bash
# utils.sh — reusable function library

log() {
  local level="$1"; shift
  echo "[$(date '+%H:%M:%S')] [$level] $*"
}

require_args() {
  local func="$1" needed="$2" got="$3"
  if [ "$got" -lt "$needed" ]; then
    log ERROR "${func}: requires $needed args, got $got"
    return 1
  fi
}

create_dir() {
  require_args "create_dir" 1 $# || return 1
  local dir="$1"
  if [ -d "$dir" ]; then
    log INFO "Directory already exists: $dir"
  else
    mkdir -p "$dir" && log INFO "Created: $dir" || {
      log ERROR "Failed to create: $dir"
      return 1
    }
  fi
}

summarize() {
  local verbose=false label="Summary"
  while getopts "vl:" opt; do
    case $opt in
      v) verbose=true ;;
      l) label="$OPTARG" ;;
    esac
  done
  shift $((OPTIND - 1))
  echo "=== $label ==="
  for item in "$@"; do
    echo "  • $item"
    $verbose && echo "    (verbose detail for: $item)"
  done
}

# --- Main ---
create_dir /tmp/myapp/data
create_dir /tmp/myapp/data   # second call shows idempotent behavior
summarize -l "Directories" -v /tmp/myapp/data /tmp/myapp/logs
```

📸 **Verified Output:**
```
[05:49:07] [INFO] Created: /tmp/myapp/data
[05:49:07] [INFO] Directory already exists: /tmp/myapp/data
=== Directories ===
  • /tmp/myapp/data
    (verbose detail for: /tmp/myapp/data)
  • /tmp/myapp/logs
    (verbose detail for: /tmp/myapp/logs)
```

> 💡 **Tip:** Source a shared library into your scripts with `. /path/to/utils.sh` (or `source /path/to/utils.sh`). This lets multiple scripts share the same `log()`, `die()`, and validation functions — keeping your codebase DRY.

---

## Summary

| Concept | Syntax | Notes |
|---|---|---|
| Define function | `name() { ... }` | Define before calling |
| Local variable | `local var="value"` | Prevents global pollution |
| Function output | `result=$(func args)` | Capture via command substitution |
| Argument 1, 2… | `$1`, `$2`, `$N` | Positional parameters |
| All arguments | `"$@"` | Preserves quoting |
| Argument count | `$#` | Number of positional params |
| Script name | `$0` | Name of the script file |
| Last exit status | `$?` | 0=success, non-zero=failure |
| Return exit code | `return N` | 0–255 only |
| Shift args | `shift` / `shift N` | Consume positional params |
| Parse options | `getopts "ab:c" opt` | `:` means arg required |
| Option argument | `$OPTARG` | Value for options with `:` |
| Function name | `${FUNCNAME[0]}` | Current function's name |
