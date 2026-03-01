# Lab 8: Bash Loops

## 🎯 Objective
Use `for`, `while`, and `until` loops in bash, control flow with `break` and `continue`, and apply loops in practical scripting scenarios.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Practitioner Lab 7 (conditionals)
- Basic bash scripting knowledge

## 🔬 Lab Instructions

### Step 1: Basic for Loop
```bash
# for item in list; do ... done
for fruit in apple banana cherry; do
  echo "Fruit: $fruit"
done
# Output: Fruit: apple, Fruit: banana, Fruit: cherry
```

### Step 2: for Loop with Ranges
```bash
# Brace expansion: {start..end}
for i in {1..5}; do
  echo "Number: $i"
done

# With step: {start..end..step}
for i in {0..10..2}; do
  echo "$i"
done
# Output: 0 2 4 6 8 10

# C-style for loop
for ((i=1; i<=5; i++)); do
  echo "Count: $i"
done
```

### Step 3: for Loop Over Files
```bash
mkdir -p /tmp/looptest
touch /tmp/looptest/file{1..5}.txt

# Loop over files matching a glob
for file in /tmp/looptest/*.txt; do
  echo "Processing: $file"
  wc -l "$file"
done
```

### Step 4: for Loop Over Command Output
```bash
# Iterate over lines from a command
for user in $(cut -d: -f1 /etc/passwd | head -5); do
  echo "User: $user"
done

# Better approach for filenames with spaces:
while IFS= read -r user; do
  echo "User: $user"
done < <(cut -d: -f1 /etc/passwd | head -5)
```

### Step 5: while Loop
```bash
# while condition; do ... done
count=1
while [ $count -le 5 ]; do
  echo "Count: $count"
  ((count++))
done
```

### Step 6: while Loop Reading a File
```bash
cat > /tmp/names.txt << 'EOF'
Alice
Bob
Carol
Dave
EOF

while IFS= read -r line; do
  echo "Hello, $line!"
done < /tmp/names.txt
# IFS= preserves leading whitespace
# -r prevents backslash interpretation
```

### Step 7: until Loop
```bash
# until runs WHILE condition is FALSE (opposite of while)
count=1
until [ $count -gt 5 ]; do
  echo "Count: $count"
  ((count++))
done
# Same result as while, opposite logic
```

### Step 8: Infinite Loop with break
```bash
# Infinite loop with break condition
counter=0
while true; do
  ((counter++))
  if [ $counter -ge 5 ]; then
    echo "Reached $counter, breaking"
    break
  fi
  echo "Counter: $counter"
done
```

### Step 9: continue — Skip an Iteration
```bash
# Skip even numbers
for i in {1..10}; do
  if (( i % 2 == 0 )); then
    continue  # Skip to next iteration
  fi
  echo "$i"
done
# Output: 1 3 5 7 9
```

### Step 10: Nested Loops
```bash
# Multiplication table
for i in {1..3}; do
  for j in {1..3}; do
    printf "%4d" $((i * j))
  done
  echo ""
done
# Output:
#    1   2   3
#    2   4   6
#    3   6   9
```

### Step 11: Loop with Array
```bash
servers=("web01" "web02" "db01" "cache01")

for server in "${servers[@]}"; do
  echo "Checking $server..."
  # Simulate a check
  ping -c 1 -W 1 localhost > /dev/null 2>&1 && \
    echo "  $server: OK" || \
    echo "  $server: UNREACHABLE"
done
```

### Step 12: Practical Loop — Batch File Processing
```bash
# Create test files with different content
mkdir -p /tmp/batch
for i in {1..5}; do
  echo "File $i content - $(date)" > "/tmp/batch/report_$i.txt"
done

# Process each file
for file in /tmp/batch/report_*.txt; do
  basename="${file##*/}"
  lines=$(wc -l < "$file")
  size=$(stat -c %s "$file")
  echo "${basename}: ${lines} lines, ${size} bytes"
done

# Clean up
rm -rf /tmp/looptest /tmp/batch /tmp/names.txt
```

## ✅ Verification
```bash
# Sum 1 to 10
total=0
for i in {1..10}; do
  ((total += i))
done
echo "Sum 1-10: $total"
# Output: Sum 1-10: 55

# Count lines in /etc/passwd using while
count=0
while IFS= read -r line; do
  ((count++))
done < /etc/passwd
echo "Lines in /etc/passwd: $count"
wc -l < /etc/passwd  # Verify match
```

## 📝 Summary
- `for item in list` iterates over a list; `{1..10}` generates a sequence
- C-style `for ((i=0; i<10; i++))` is useful for numeric iteration with complex logic
- `while condition` loops while true; `until condition` loops while false
- `break` exits the loop immediately; `continue` skips to the next iteration
- Always quote `"$file"` when looping over filenames to handle spaces
- `while IFS= read -r line; do ... done < file` is the safest way to process files line by line

