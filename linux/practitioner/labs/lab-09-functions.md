# Lab 9: Functions in bash

## 🎯 Objective
Define and use bash functions with parameters, local variables, return values, and exported functions.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Practitioner Labs 7 (Conditionals) and 8 (Loops)

## 🔬 Lab Instructions

### Step 1: Define and Call a Function

```bash
# Two equivalent syntaxes
greet() {
    echo "Hello, World!"
}

function say_hi {
    echo "Hi there!"
}

greet
say_hi
```

**Expected output:**
```
Hello, World!
Hi there!
```

### Step 2: Function Parameters

```bash
# $1, $2, ... are positional parameters
greet_user() {
    echo "Hello, $1!"
    echo "You are $2 years old."
}

greet_user "Alice" 30
greet_user "Bob" 25
```

**Expected output:**
```
Hello, Alice!
You are 30 years old.
Hello, Bob!
You are 25 years old.
```

```bash
# $@ = all arguments, $# = argument count
show_args() {
    echo "Count: $#"
    echo "All: $@"
    for arg in "$@"; do
        echo "  Arg: $arg"
    done
}

show_args "apple" "banana" "cherry"
```

### Step 3: Local Variables

```bash
# Variables without 'local' are global!
GLOBAL_VAR="global"

test_scope() {
    local LOCAL_VAR="local"
    GLOBAL_VAR="modified"
    echo "Inside: LOCAL=$LOCAL_VAR, GLOBAL=$GLOBAL_VAR"
}

test_scope
echo "Outside: GLOBAL=$GLOBAL_VAR"
echo "Outside: LOCAL=${LOCAL_VAR:-not accessible}"
```

**Expected output:**
```
Inside: LOCAL=local, GLOBAL=modified
Outside: GLOBAL=modified
Outside: LOCAL=not accessible
```

### Step 4: Return Values

```bash
# return sets exit code (0=success, 1-255=error)
is_even() {
    local num=$1
    if (( num % 2 == 0 )); then
        return 0  # success = even
    else
        return 1  # failure = odd
    fi
}

is_even 4 && echo "4 is even" || echo "4 is odd"
is_even 7 && echo "7 is even" || echo "7 is odd"
```

**Expected output:**
```
4 is even
7 is odd
```

```bash
# To return a string, use echo and command substitution
get_greeting() {
    local name=$1
    echo "Hello, ${name}!"
}

MSG=$(get_greeting "Linux")
echo "Got: $MSG"
```

### Step 5: Functions with Default Values

```bash
connect() {
    local host="${1:-localhost}"
    local port="${2:-8080}"
    echo "Connecting to $host:$port"
}

connect                    # uses defaults
connect "db.server.com"    # custom host, default port
connect "api.server.com" 443  # both custom
```

**Expected output:**
```
Connecting to localhost:8080
Connecting to db.server.com:8080
Connecting to api.server.com:443
```

### Step 6: Recursive Functions

```bash
factorial() {
    local n=$1
    if [[ $n -le 1 ]]; then
        echo 1
    else
        local prev=$(factorial $((n-1)))
        echo $((n * prev))
    fi
}

echo "5! = $(factorial 5)"
echo "6! = $(factorial 6)"
```

**Expected output:**
```
5! = 120
6! = 720
```

### Step 7: Export Functions to Subshells

```bash
my_function() {
    echo "I'm an exported function!"
}

export -f my_function
bash -c 'my_function'
```

**Expected output:**
```
I'm an exported function!
```

### Step 8: Practical Function Library Script

```bash
cat > /tmp/lib-functions.sh << 'EOF'
#!/bin/bash

# Log with timestamp
log() {
    local level="${1:-INFO}"
    local msg="$2"
    echo "[$(date +%H:%M:%S)] [$level] $msg"
}

# Check if a command exists
has_command() {
    command -v "$1" > /dev/null 2>&1
}

# Get file size in bytes
file_size() {
    stat -c %s "$1" 2>/dev/null || echo 0
}

log "INFO" "Script started"
log "WARN" "This is a warning"

has_command bash && log "INFO" "bash found at $(which bash)"
has_command nonexistent || log "WARN" "nonexistent command not found"

log "INFO" "Size of /etc/passwd: $(file_size /etc/passwd) bytes"
EOF

bash /tmp/lib-functions.sh
```

## ✅ Verification

```bash
double() { echo $(( $1 * 2 )); }
is_positive() { [[ $1 -gt 0 ]] && return 0 || return 1; }

echo "double 7 = $(double 7)"
is_positive 5 && echo "5 is positive"
is_positive -3 || echo "-3 is not positive"

rm /tmp/lib-functions.sh 2>/dev/null
echo "Practitioner Lab 9 complete"
```

## 📝 Summary
- Functions are defined with `funcname() { }` or `function funcname { }`
- Parameters: `$1`, `$2`, ...; `$@` = all; `$#` = count
- `local` restricts variable scope to the function; always use it
- `return N` sets the exit code; `echo` + command substitution returns strings
- `${1:-default}` provides default values for parameters
- `export -f funcname` makes a function available to subshells
