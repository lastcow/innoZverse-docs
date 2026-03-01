# Lab 14: Arrays in Bash

## 🎯 Objective
Learn to declare, populate, iterate, and manipulate indexed and associative arrays in Bash.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Labs 7–8 (Conditionals and Loops)

## 🔬 Lab Instructions

### Step 1: Declare an Indexed Array
```bash
# Method 1: declare
declare -a fruits=("apple" "banana" "cherry")

# Method 2: direct assignment
colors=("red" "green" "blue")

# Method 3: element by element
servers[0]="web01"
servers[1]="web02"
servers[2]="db01"

echo ${fruits[0]}    # apple
echo ${colors[2]}    # blue
echo ${servers[1]}   # web02
```

### Step 2: Array Length and All Elements
```bash
fruits=("apple" "banana" "cherry" "date" "elderberry")

echo "Length: ${#fruits[@]}"      # Length: 5
echo "All: ${fruits[@]}"          # All: apple banana cherry date elderberry
echo "Indices: ${!fruits[@]}"     # Indices: 0 1 2 3 4
```

### Step 3: Modify and Append Elements
```bash
fruits=("apple" "banana" "cherry")
fruits[1]="blueberry"            # modify index 1
fruits+=("dragonfruit")          # append one
fruits+=("elderberry" "fig")     # append multiple

echo ${fruits[@]}
# apple blueberry cherry dragonfruit elderberry fig
echo "Length: ${#fruits[@]}"
# Length: 6
```

### Step 4: Array Slicing
```bash
arr=("a" "b" "c" "d" "e" "f")
echo ${arr[@]:1:3}    # b c d  (from index 1, take 3 elements)
echo ${arr[@]:3}      # d e f  (from index 3 to end)
echo ${arr[@]: -2}    # e f    (last 2 elements)
```

### Step 5: Iterate Over an Array
```bash
servers=("web01" "web02" "db01" "cache01")

# Method 1: for-in
for server in "${servers[@]}"; do
    echo "Checking: $server"
done
# Checking: web01
# Checking: web02
# Checking: db01
# Checking: cache01

# Method 2: with index
for i in "${!servers[@]}"; do
    echo "[$i] ${servers[$i]}"
done
# [0] web01
# [1] web02
```

### Step 6: Remove Elements
```bash
arr=("one" "two" "three" "four" "five")
unset arr[2]            # remove index 2 (three)
echo ${arr[@]}          # one two four five
echo ${!arr[@]}         # 0 1 3 4  (note gap at index 2)

# Re-index after removal
arr=("${arr[@]}")
echo ${!arr[@]}         # 0 1 2 3
```

### Step 7: Associative Arrays (Dictionaries)
```bash
declare -A config
config["host"]="localhost"
config["port"]="5432"
config["dbname"]="myapp"
config["user"]="dbadmin"

echo "Host: ${config[host]}"    # Host: localhost
echo "Port: ${config[port]}"    # Port: 5432
echo "Keys: ${!config[@]}"      # Keys: host port dbname user
echo "Vals: ${config[@]}"       # Values: localhost 5432 myapp dbadmin
```

### Step 8: Iterate Associative Array
```bash
declare -A env_vars
env_vars["APP_ENV"]="production"
env_vars["LOG_LEVEL"]="warn"
env_vars["MAX_CONN"]="100"

for key in "${!env_vars[@]}"; do
    echo "export $key=${env_vars[$key]}"
done
# export APP_ENV=production
# export LOG_LEVEL=warn
# export MAX_CONN=100
```

### Step 9: Array from Command Output
```bash
# Capture command output into array
mapfile -t conf_files < <(ls /etc/*.conf 2>/dev/null)
echo "Found ${#conf_files[@]} .conf files"
echo "First: ${conf_files[0]}"

# Read file lines into array
mapfile -t lines < /etc/hostname
echo "Hostname: ${lines[0]}"
# Hostname: myserver
```

### Step 10: Practical Script — Server Ping Check
```bash
cat > ~/ping_check.sh << 'EOF'
#!/bin/bash
declare -a servers=("8.8.8.8" "1.1.1.1" "9.9.9.9")
declare -A results

for host in "${servers[@]}"; do
    if ping -c 1 -W 2 "$host" &>/dev/null; then
        results[$host]="UP"
    else
        results[$host]="DOWN"
    fi
done

echo "=== Ping Results ==="
for host in "${!results[@]}"; do
    printf "%-15s %s\n" "$host" "${results[$host]}"
done
EOF
chmod +x ~/ping_check.sh
~/ping_check.sh
# === Ping Results ===
# 8.8.8.8         UP
# 1.1.1.1         UP
# 9.9.9.9         UP
```

## ✅ Verification
```bash
arr=("x" "y" "z")
echo ${#arr[@]}      # 3
echo ${arr[@]}       # x y z
echo ${arr[1]}       # y
arr+=("w")
echo ${arr[-1]}      # w
```

## 📝 Summary
- `arr=(a b c)` declares indexed array; `declare -A` for associative
- `${arr[@]}` all elements; `${#arr[@]}` length; `${!arr[@]}` indices/keys
- `${arr[@]:n:len}` slices; `arr+=("x")` appends
- `unset arr[i]` removes element (leaves gap); re-assign to re-index
- `mapfile -t arr < file` reads file lines into array safely
