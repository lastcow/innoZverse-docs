# Lab 01: Shell Scripting — Variables & Conditionals

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

In this lab you'll build a solid foundation in Bash scripting: declaring variables, understanding quoting rules, performing arithmetic, and controlling flow with `if/elif/else` and `case` statements. Every example is Docker-verified so you see exactly what to expect.

---

## Step 1: Declaring and Using Variables

Variables in Bash are untyped and assigned without spaces around `=`.

```bash
name="Alice"
greeting="Hello, $name!"
echo "$greeting"
echo "Single: $name"
echo 'No expand: $name'
```

📸 **Verified Output:**
```
Hello, Alice!
Single: Alice
No expand: $name
```

> 💡 **Tip:** Always double-quote variable expansions (`"$var"`) to prevent word-splitting on values that contain spaces. Single quotes treat everything literally — no variable expansion occurs inside `'...'`.

---

## Step 2: Variable Quoting Deep Dive

Quoting is one of the most common sources of bugs. Practice the three quoting styles:

```bash
file="my report.txt"
echo $file          # RISKY: splits on space
echo "$file"        # SAFE: treats as one argument
echo '$file'        # LITERAL: prints $file
echo "Path: ${file}"  # braces delimit the variable name
```

📸 **Verified Output:**
```
my report.txt
my report.txt
$file
Path: my report.txt
```

> 💡 **Tip:** Use `${var}` (braces) when the variable name is immediately followed by alphanumeric characters, e.g., `${prefix}file` instead of `$prefixfile`.

---

## Step 3: Arithmetic Operations

Bash supports integer arithmetic via `$(( ))`.

```bash
x=10; y=3
echo "Add: $((x + y))"
echo "Sub: $((x - y))"
echo "Mul: $((x * y))"
echo "Div: $((x / y))"
echo "Mod: $((x % y))"
```

📸 **Verified Output:**
```
Add: 13
Sub: 7
Mul: 30
Div: 3
Mod: 1
```

> 💡 **Tip:** `$(( ))` does integer arithmetic only. For floating-point math use `bc` or `awk`: `echo "scale=2; 10/3" | bc` → `3.33`.

---

## Step 4: Test Operators — Files and Strings

The `[ ]` command (aka `test`) evaluates conditions. File and string tests:

```bash
touch /tmp/testfile
mkdir -p /tmp/testdir
var=""
nonempty="hello"

[ -f /tmp/testfile ] && echo "-f: file exists"
[ -d /tmp/testdir ] && echo "-d: dir exists"
[ -z "$var" ] && echo "-z: var is empty"
[ -n "$nonempty" ] && echo "-n: nonempty has content"
```

📸 **Verified Output:**
```
-f: file exists
-d: dir exists
-z: var is empty
-n: nonempty has content
```

> 💡 **Tip:** Use `[[ ]]` (double brackets) in Bash scripts for safer string tests — it handles empty variables and glob patterns without quoting surprises.

---

## Step 5: Test Operators — Numeric Comparisons

Numeric comparisons use letter-based operators inside `[ ]`:

```bash
[ 5 -eq 5 ] && echo "-eq: 5 equals 5"
[ 3 -lt 5 ] && echo "-lt: 3 less than 5"
[ 7 -gt 5 ] && echo "-gt: 7 greater than 5"
[ 4 -le 4 ] && echo "-le: 4 less or equal 4"
[ 6 -ge 5 ] && echo "-ge: 6 greater or equal 5"
[ 3 -ne 5 ] && echo "-ne: 3 not equal 5"
```

📸 **Verified Output:**
```
-eq: 5 equals 5
-lt: 3 less than 5
-gt: 7 greater than 5
-le: 4 less or equal 4
-ge: 6 greater or equal 5
-ne: 3 not equal 5
```

> 💡 **Tip:** Don't use `<` or `>` for numeric comparison inside `[ ]` — those redirect files! Use `-lt`, `-gt`, etc., or use `(( x > y ))` with double parentheses for arithmetic truth tests.

---

## Step 6: if / elif / else

Grade a score using chained conditionals:

```bash
score=75
if [ $score -ge 90 ]; then
  echo "Grade: A"
elif [ $score -ge 80 ]; then
  echo "Grade: B"
elif [ $score -ge 70 ]; then
  echo "Grade: C"
else
  echo "Grade: F"
fi
```

📸 **Verified Output:**
```
Grade: C
```

> 💡 **Tip:** Conditions are evaluated top-to-bottom; the first match wins. Structure your `elif` branches from most restrictive to least restrictive for predictable logic.

---

## Step 7: case Statement

`case` is cleaner than chains of `if` when matching one variable against multiple patterns:

```bash
day="Monday"
case "$day" in
  Monday|Tuesday|Wednesday|Thursday|Friday)
    echo "$day is a weekday"
    ;;
  Saturday|Sunday)
    echo "$day is a weekend"
    ;;
  *)
    echo "Unknown day"
    ;;
esac
```

📸 **Verified Output:**
```
Monday is a weekday
```

> 💡 **Tip:** The `*` catch-all pattern at the end of a `case` acts like the `else` clause — always include it to handle unexpected input gracefully.

---

## Step 8: Capstone — User Input Validator Script

Combine everything into a practical validator script. This simulates what you'd write to validate configuration values before a deployment:

```bash
validate_config() {
  local env="$1"
  local port="$2"
  local config_file="$3"

  echo "=== Config Validator ==="

  # Check environment
  case "$env" in
    prod|staging|dev)
      echo "[OK] Environment: $env"
      ;;
    *)
      echo "[ERROR] Unknown environment: $env"
      return 1
      ;;
  esac

  # Check port is numeric and in valid range
  if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -ge 1024 ] && [ "$port" -le 65535 ]; then
    echo "[OK] Port: $port"
  else
    echo "[ERROR] Invalid port: $port (must be 1024-65535)"
    return 1
  fi

  # Check config file
  if [ -z "$config_file" ]; then
    echo "[WARN] No config file specified, using defaults"
  elif [ -f "$config_file" ]; then
    echo "[OK] Config file: $config_file"
  else
    echo "[ERROR] Config file not found: $config_file"
    return 1
  fi

  echo "=== Validation PASSED ==="
  return 0
}

# Test with valid input
validate_config "staging" "8080" ""

echo ""

# Test with invalid input
validate_config "unknown" "99" "/nonexistent.conf"
```

📸 **Verified Output:**
```
=== Config Validator ===
[OK] Environment: staging
[OK] Port: 8080
[WARN] No config file specified, using defaults
=== Validation PASSED ===

=== Config Validator ===
[ERROR] Unknown environment: unknown
```

> 💡 **Tip:** The capstone pattern — validate inputs, report clearly, return meaningful exit codes — is the backbone of reliable automation scripts. Build this habit early.

---

## Summary

| Concept | Syntax | Example |
|---|---|---|
| Variable assignment | `name="value"` | `user="alice"` |
| Double-quote expand | `"$var"` | `echo "$name"` |
| No expansion | `'$var'` | `echo '$name'` |
| Arithmetic | `$(( expr ))` | `$((x + y))` |
| File exists | `[ -f path ]` | `[ -f /etc/hosts ]` |
| Dir exists | `[ -d path ]` | `[ -d /tmp ]` |
| String empty | `[ -z "$s" ]` | test for blank |
| String non-empty | `[ -n "$s" ]` | test for content |
| Numeric equal | `[ x -eq y ]` | `[ $a -eq 0 ]` |
| Numeric less | `[ x -lt y ]` | `[ $count -lt 10 ]` |
| Numeric greater | `[ x -gt y ]` | `[ $size -gt 100 ]` |
| If/elif/else | `if [...]; then ... fi` | grade classifier |
| Case statement | `case "$v" in pat) ;; esac` | environment selector |
