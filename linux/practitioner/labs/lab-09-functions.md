# Lab 9: Bash Functions

## 🎯 Objective
Define and use functions in bash: pass arguments, use local variables, return values, and organize scripts with reusable function libraries.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Practitioner Labs 7 and 8 (conditionals, loops)
- Basic bash scripting

## 🔬 Lab Instructions

### Step 1: Define and Call a Function
```bash
# Function definition
greet() {
  echo "Hello from the function!"
}

# Call it
greet
# Output: Hello from the function!

# Alternative syntax
function farewell {
  echo "Goodbye!"
}
farewell
```

### Step 2: Functions with Arguments
```bash
# Arguments accessed as $1, $2, etc.
greet_user() {
  echo "Hello, $1!"
  echo "Your role is: $2"
}

greet_user "Alice" "admin"
# Output:
# Hello, Alice!
# Your role is: admin
```

### Step 3: Special Variables in Functions
```bash
show_args() {
  echo "Function name: ${FUNCNAME[0]}"
  echo "Number of args: $#"
  echo "All args: $@"
  echo "First: $1"
  echo "Second: $2"
}

show_args alpha beta gamma
```

### Step 4: Local Variables
```bash
# Without local: variable leaks to global scope
bad_function() {
  x=10  # Global!
}
bad_function
echo $x  # Output: 10  (leaked!)

# With local: contained to function scope
good_function() {
  local x=10
  echo "Inside: $x"
}
good_function
echo "Outside: $x"  # Output: 10 (from bad_function, not good_function)

# Best practice: always use local for function variables
calculate() {
  local num1=$1
  local num2=$2
  local result=$((num1 + num2))
  echo "Result: $result"
}
calculate 10 20
```

### Step 5: Return Values (Exit Codes)
```bash
# return sets the exit code (0-255)
is_even() {
  local num=$1
  if (( num % 2 == 0 )); then
    return 0  # true/success
  else
    return 1  # false/failure
  fi
}

is_even 4
echo "Exit code: $?"  # Output: 0

is_even 7
echo "Exit code: $?"  # Output: 1

# Use in conditionals
if is_even 8; then
  echo "8 is even"
fi
```

### Step 6: Returning Data (echo + Command Substitution)
```bash
# Functions can't return strings via return
# Instead, echo the result and capture with $()
get_greeting() {
  local name=$1
  echo "Hello, ${name}!"
}

message=$(get_greeting "World")
echo $message
# Output: Hello, World!

# More complex example
get_disk_usage() {
  local path=${1:-/}
  df -h "$path" | awk 'NR==2 {print $5}'
}
usage=$(get_disk_usage /)
echo "Root disk usage: $usage"
```

### Step 7: Default Parameter Values
```bash
create_backup() {
  local source=${1:-/etc}
  local dest=${2:-/tmp/backup}
  local timestamp=$(date +%Y%m%d_%H%M%S)

  mkdir -p "$dest"
  echo "Backing up $source to ${dest}/backup_${timestamp}.tar.gz"
  # tar -czf "${dest}/backup_${timestamp}.tar.gz" "$source"
}

create_backup              # Uses defaults
create_backup /home /tmp/myhome_backup
```

### Step 8: Validate Function Arguments
```bash
require_args() {
  local func_name=$1
  local required=$2
  local actual=$3
  if [ "$actual" -lt "$required" ]; then
    echo "ERROR: $func_name requires $required arguments, got $actual" >&2
    return 1
  fi
}

divide() {
  require_args "divide" 2 $# || return 1
  local a=$1
  local b=$2
  if [ "$b" -eq 0 ]; then
    echo "ERROR: Cannot divide by zero" >&2
    return 1
  fi
  echo $((a / b))
}

divide 10 2   # Output: 5
divide 10 0   # Output: ERROR
divide 5      # Output: ERROR (missing arg)
```

### Step 9: Recursive Functions
```bash
# Factorial using recursion
factorial() {
  local n=$1
  if [ $n -le 1 ]; then
    echo 1
  else
    local prev=$(factorial $((n - 1)))
    echo $((n * prev))
  fi
}

factorial 5
# Output: 120
```

### Step 10: Function Libraries
```bash
# Create a library file
cat > /tmp/lib_utils.sh << 'EOF'
#!/bin/bash
# Utility function library

log_info() { echo "[INFO]  $(date '+%H:%M:%S') $*"; }
log_warn() { echo "[WARN]  $(date '+%H:%M:%S') $*"; }
log_error() { echo "[ERROR] $(date '+%H:%M:%S') $*" >&2; }

is_root() { [ "$(id -u)" -eq 0 ]; }

file_exists() { [ -f "$1" ]; }
dir_exists() { [ -d "$1" ]; }
EOF

# Source the library in another script
source /tmp/lib_utils.sh

log_info "System check started"
log_warn "This is a warning"
is_root && echo "Running as root" || echo "Not root"
```

### Step 11: Functions with Arrays
```bash
# Pass array by reference (using nameref — bash 4.3+)
process_array() {
  local -n arr=$1  # nameref
  echo "Array size: ${#arr[@]}"
  for item in "${arr[@]}"; do
    echo "  - $item"
  done
}

fruits=("apple" "banana" "cherry")
process_array fruits
```

### Step 12: Cleanup Functions with trap
```bash
TMPDIR=$(mktemp -d)

cleanup() {
  echo "Cleaning up $TMPDIR"
  rm -rf "$TMPDIR"
}

# Register cleanup to run on exit
trap cleanup EXIT

echo "Working in $TMPDIR"
touch "$TMPDIR/workfile.txt"
echo "Work done"
# cleanup() runs automatically when script exits

rm -f /tmp/lib_utils.sh
```

## ✅ Verification
```bash
# Define and test a function
add() {
  local a=$1 b=$2
  echo $((a + b))
}

result=$(add 15 27)
echo "15 + 27 = $result"
# Output: 15 + 27 = 42

# Test local scope
test_scope() {
  local inner="local value"
  echo "Inside: $inner"
}
test_scope
echo "Outside: '${inner}'"  # Should be empty
```

## 📝 Summary
- Functions are defined with `name() { ... }` or `function name { ... }`
- Arguments are accessed as `$1`, `$2`, ... `$@` (all args), `$#` (count)
- Always use `local` for function variables to prevent scope leakage
- `return N` sets exit code; to return data, `echo` it and capture with `$()`
- Source function libraries with `. file` or `source file` to share functions across scripts
- `trap cleanup EXIT` ensures cleanup code runs even if the script exits unexpectedly

