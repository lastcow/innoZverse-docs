# Lab 8: Loops in bash

## 🎯 Objective
Master for, while, and until loops with break/continue, and iterate over lists, ranges, and file lines.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Practitioner Lab 7: Conditionals

## 🔬 Lab Instructions

### Step 1: for Loop — Iterate Over a List

```bash
for color in red green blue yellow; do
    echo "Color: $color"
done
```

**Expected output:**
```
Color: red
Color: green
Color: blue
Color: yellow
```

```bash
# Loop over files
for file in /etc/hostname /etc/os-release /etc/passwd; do
    echo "Lines in $file: $(wc -l < $file)"
done
```

### Step 2: for Loop — C-style with Numeric Range

```bash
for ((i=0; i<5; i++)); do
    echo "i = $i"
done
```

**Expected output:**
```
i = 0
i = 1
i = 2
i = 3
i = 4
```

```bash
# Count down
for ((i=10; i>=1; i--)); do
    echo -n "$i "
done
echo ""
```

```bash
# Using brace expansion
for i in {1..5}; do
    echo "Item $i"
done
```

```bash
# Step brace expansion
for i in {0..10..2}; do
    echo -n "$i "
done
echo ""
```

**Expected output:**
```
0 2 4 6 8 10
```

### Step 3: for Loop — Iterate Over Command Output

```bash
for user in $(cut -d: -f1 /etc/passwd | head -5); do
    echo "User: $user"
done
```

```bash
# Loop over find results
for file in $(find /tmp -name "*.txt" -maxdepth 1 2>/dev/null | head -5); do
    echo "Found: $file"
done
```

### Step 4: while Loop

```bash
# Countdown with while
COUNT=5
while [[ $COUNT -gt 0 ]]; do
    echo "Countdown: $COUNT"
    ((COUNT--))
done
echo "Done!"
```

**Expected output:**
```
Countdown: 5
Countdown: 4
Countdown: 3
Countdown: 2
Countdown: 1
Done!
```

```bash
# Read file line by line with while
cat > /tmp/names.txt << 'EOF'
Alice
Bob
Carol
Dave
EOF

while IFS= read -r line; do
    echo "Name: $line"
done < /tmp/names.txt
```

**Expected output:**
```
Name: Alice
Name: Bob
Name: Carol
Name: Dave
```

### Step 5: until Loop

```bash
# until runs until condition becomes TRUE
COUNTER=0
until [[ $COUNTER -ge 3 ]]; do
    echo "Counter: $COUNTER"
    ((COUNTER++))
done
```

**Expected output:**
```
Counter: 0
Counter: 1
Counter: 2
```

### Step 6: break and continue

```bash
# break exits the loop immediately
for i in {1..10}; do
    if [[ $i -eq 5 ]]; then
        echo "Breaking at $i"
        break
    fi
    echo "Processing: $i"
done
```

**Expected output:**
```
Processing: 1
Processing: 2
Processing: 3
Processing: 4
Breaking at 5
```

```bash
# continue skips the rest of the current iteration
for i in {1..8}; do
    if (( i % 2 == 0 )); then
        continue
    fi
    echo "Odd: $i"
done
```

**Expected output:**
```
Odd: 1
Odd: 3
Odd: 5
Odd: 7
```

### Step 7: Nested Loops

```bash
for i in 1 2 3; do
    for j in a b c; do
        echo -n "$i$j "
    done
done
echo ""
```

**Expected output:**
```
1a 1b 1c 2a 2b 2c 3a 3b 3c
```

### Step 8: Practical Loop Script

```bash
cat > /tmp/loop-report.sh << 'EOF'
#!/bin/bash
echo "=== File Type Report ==="
for dir in /etc /tmp /usr/bin; do
    file_count=$(find "$dir" -maxdepth 1 -type f 2>/dev/null | wc -l)
    dir_count=$(find "$dir" -maxdepth 1 -type d 2>/dev/null | wc -l)
    echo "$dir: $file_count files, $dir_count subdirs"
done
EOF

bash /tmp/loop-report.sh
```

## ✅ Verification

```bash
# Test each loop type
echo "=== for list ===" && for x in a b c; do echo -n "$x "; done && echo ""
echo "=== for range ===" && for ((i=0;i<3;i++)); do echo -n "$i "; done && echo ""
echo "=== while ===" && n=3; while [[ $n -gt 0 ]]; do echo -n "$n "; ((n--)); done && echo ""
echo "=== break ===" && for i in 1 2 3 4 5; do [[ $i -eq 3 ]] && break; echo -n "$i "; done && echo ""
echo "=== while read ===" && echo -e "x\ny\nz" | while IFS= read -r line; do echo -n "$line "; done && echo ""

rm /tmp/names.txt /tmp/loop-report.sh 2>/dev/null
echo "Practitioner Lab 8 complete"
```

## 📝 Summary
- `for item in list; do ... done` iterates over a space-separated list
- `for ((i=0; i<N; i++)); do` is a C-style numeric loop
- `for i in {1..10}; do` uses brace expansion for ranges
- `while [[ condition ]]; do` runs while condition is true
- `while IFS= read -r line; do ... done < file` reads file line by line
- `until [[ condition ]]; do` runs until condition becomes true
- `break` exits a loop; `continue` skips to the next iteration
