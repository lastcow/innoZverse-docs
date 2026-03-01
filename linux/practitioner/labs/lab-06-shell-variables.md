# Lab 6: Shell Variables and Quoting

## 🎯 Objective
Master shell variable types, understand quoting rules, and perform string operations in bash — foundations for writing robust scripts.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Foundations Lab 18 (environment variables)
- Basic bash shell usage

## 🔬 Lab Instructions

### Step 1: Variable Assignment and Access
```bash
# No spaces around = sign!
name="Alice"
age=30
pi=3.14

echo $name
# Output: Alice

echo "Name: $name, Age: $age"
# Output: Name: Alice, Age: 30

# Curly brace syntax for clarity
echo "Hello, ${name}!"
echo "${name}s department"  # Would fail without braces: $names = empty
```

### Step 2: Single vs Double Quotes
```bash
name="World"

# Double quotes: variables are expanded
echo "Hello $name"
# Output: Hello World

# Single quotes: everything is literal
echo 'Hello $name'
# Output: Hello $name

# Escape a special character
echo "Price: \$5.00"
# Output: Price: $5.00
```

### Step 3: Command Substitution
```bash
# $(command) or `command` captures command output
today=$(date +%Y-%m-%d)
echo "Today is: $today"

hostname=$(hostname)
echo "Running on: $hostname"

# Nested command substitution
echo "Home: $(dirname $(echo $HOME))"
```

### Step 4: Arithmetic Expansion
```bash
# $(( )) for integer arithmetic
x=10
y=3
echo $((x + y))   # 13
echo $((x * y))   # 30
echo $((x / y))   # 3 (integer division)
echo $((x % y))   # 1 (remainder)
echo $((x ** 2))  # 100

# Increment
count=0
count=$((count + 1))
echo $count  # 1

((count++))
echo $count  # 2
```

### Step 5: Variable Types and declare
```bash
# Integer variable
declare -i num=42
echo $num

# Read-only variable
declare -r CONST="unchangeable"
echo $CONST
# CONST="new"  # Would error

# Uppercase transformation
declare -u upper_var
upper_var="hello"
echo $upper_var
# Output: HELLO

# Lowercase transformation
declare -l lower_var
lower_var="HELLO"
echo $lower_var
# Output: hello
```

### Step 6: Default Values and Substitution
```bash
# ${var:-default}: use default if var is unset or empty
unset myvar
echo ${myvar:-"default value"}
# Output: default value
echo $myvar  # Still unset

# ${var:=default}: assign default if unset
echo ${myvar:="assigned default"}
echo $myvar  # Now set to "assigned default"

# ${var:+value}: use value if var IS set
name="Alice"
echo ${name:+"Name is set: $name"}
# Output: Name is set: Alice

# ${var:?error}: print error and exit if unset
echo ${required_var:?"required_var is not set"}
# Script exits with error if required_var is unset
```

### Step 7: String Length
```bash
str="Hello, World!"
echo ${#str}
# Output: 13

# Length of array
arr=(a b c d e)
echo ${#arr[@]}
# Output: 5
```

### Step 8: Substring Extraction
```bash
str="Hello, World!"

# ${var:offset:length}
echo ${str:0:5}    # Hello
echo ${str:7:5}    # World
echo ${str:7}      # World! (from position 7 to end)
echo ${str: -6}    # World! (last 6 chars)
```

### Step 9: Pattern Matching and Removal
```bash
filename="report_2026-03-01.tar.gz"

# Remove shortest match from START
echo ${filename#*_}
# Output: 2026-03-01.tar.gz

# Remove longest match from START
echo ${filename##*-}
# Output: 01.tar.gz

# Remove shortest match from END
echo ${filename%.*}
# Output: report_2026-03-01.tar

# Remove longest match from END
echo ${filename%%.*}
# Output: report_2026-03-01
```

### Step 10: Pattern Substitution
```bash
str="The cat sat on the mat"

# Replace first occurrence
echo ${str/cat/dog}
# Output: The dog sat on the mat

# Replace all occurrences
echo ${str//at/ot}
# Output: The cot sot on the mot

# Replace at beginning
path="/home/student/docs"
echo ${path/#\/home/$HOME}
```

### Step 11: Case Conversion (bash 4+)
```bash
str="Hello World"

# Uppercase
echo ${str^^}
# Output: HELLO WORLD

# Lowercase
echo ${str,,}
# Output: hello world

# Capitalize first character
echo ${str^}
# Output: Hello World (already capital)

str2="hello world"
echo ${str2^}
# Output: Hello world
```

### Step 12: Practical Variable Usage in Scripts
```bash
#!/bin/bash
# Demonstrate variable best practices

# Always quote variables in comparisons
name="John Doe"
if [ "$name" = "John Doe" ]; then
  echo "Welcome, $name!"
fi

# Use ${} for safety in string concatenation
prefix="backup"
echo "${prefix}_$(date +%Y%m%d).tar.gz"
# Output: backup_20260301.tar.gz

# Check if variable is set and non-empty
check_var() {
  local var_name="$1"
  local var_value="${!var_name}"
  if [[ -n "$var_value" ]]; then
    echo "$var_name is set to: $var_value"
  else
    echo "$var_name is empty or unset"
  fi
}
check_var HOME
check_var NONEXISTENT
```

## ✅ Verification
```bash
# Test variable operations
str="linux_admin_2026"
echo "Length: ${#str}"         # 16
echo "Upper: ${str^^}"          # LINUX_ADMIN_2026
echo "Substr: ${str:6:5}"       # admin
echo "Trim ext: ${str%_*}"      # linux_admin  (removes last _xxx)
echo "Default: ${unset_var:-fallback}"  # fallback
```

## 📝 Summary
- Variables use `name=value` (no spaces); access with `$name` or `${name}`
- Double quotes expand variables; single quotes treat everything literally
- `$(command)` captures command output; `$((expr))` does integer arithmetic
- `${var:-default}` provides defaults; `${#var}` gives length
- `${str:offset:length}` extracts substrings; `${str/old/new}` substitutes patterns
- `${str^^}` uppercases; `${str,,}` lowercases — available in bash 4+

