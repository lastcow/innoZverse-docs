# Lab 2: awk Basics

## 🎯 Objective
Use awk to process structured text: print specific fields, use NR/NF, filter with patterns, and use BEGIN/END blocks with custom field separators.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Foundations Labs 14 (grep) and 19 (I/O Redirection)

## 🔬 Lab Instructions

### Step 1: awk Fundamentals

```bash
echo "hello world foo bar" | awk '{ print $1 }'
```

**Expected output:**
```
hello
```

```bash
echo "hello world foo bar" | awk '{ print $3 }'
```

**Expected output:**
```
foo
```

```bash
echo "hello world foo bar" | awk '{ print $1, $3 }'
```

**Expected output:**
```
hello foo
```

### Step 2: Process /etc/passwd with Custom Field Separator

```bash
# /etc/passwd: username:password:UID:GID:GECOS:home:shell
awk -F: '{ print $1 }' /etc/passwd | head -10
```

```bash
awk -F: '{ print $1, $7 }' /etc/passwd | head -10
```

```bash
awk -F: '{ printf "%-20s %s\n", $1, $7 }' /etc/passwd | head -10
```

### Step 3: Use NR and NF

```bash
# NR = current line number
awk '{ print NR, $0 }' /etc/passwd | head -5
```

```bash
# NF = number of fields in current line
echo "one two three" | awk '{ print NF }'
```

**Expected output:**
```
3
```

```bash
# Print last field using $NF
awk -F: '{ print $NF }' /etc/passwd | head -10
```

```bash
# Print total line count at end
awk 'END { print "Total lines:", NR }' /etc/passwd
```

### Step 4: Pattern Matching

```bash
# Only print lines where UID >= 1000
awk -F: '$3 >= 1000 { print $1, $3 }' /etc/passwd
```

```bash
# Print lines containing "bash"
awk '/bash/' /etc/passwd
```

```bash
# Print lines NOT containing "nologin"
awk '!/nologin/' /etc/passwd | head -5
```

### Step 5: BEGIN and END Blocks

```bash
awk -F: 'BEGIN { print "=== User List ===" } { print $1 } END { print "=== Total:", NR, "===" }' /etc/passwd
```

### Step 6: Arithmetic and Variables

```bash
# Sum UIDs
awk -F: '{ sum += $3 } END { print "Sum of UIDs:", sum }' /etc/passwd
```

```bash
# Count users with bash shell
awk -F: '$7 ~ /bash/ { count++ } END { print "bash users:", count }' /etc/passwd
```

```bash
# Show users with UID between 100 and 999
awk -F: '$3 >= 100 && $3 < 1000 { print $1, $3 }' /etc/passwd | head -10
```

### Step 7: Custom Output with awk

```bash
# Create a report
cat > /tmp/awk-data.txt << 'EOF'
Alice 85 92 78
Bob 91 88 95
Carol 72 68 80
Dave 95 97 99
EOF

awk '{ avg = ($2+$3+$4)/3; printf "%-10s avg: %.1f\n", $1, avg }' /tmp/awk-data.txt
```

**Expected output:**
```
Alice      avg: 85.0
Bob        avg: 91.3
Carol      avg: 73.3
Dave       avg: 97.0
```

### Step 8: Process Multiple Files

```bash
awk -F: 'FNR==1 { print "=== File:", FILENAME }' /etc/passwd /etc/group
```

## ✅ Verification

```bash
echo "=== Users with bash ===" && awk -F: '$7 ~ /bash/ { print $1 }' /etc/passwd
echo "=== User count ===" && awk 'END { print NR }' /etc/passwd
echo "=== UID range ===" && awk -F: '$3 >= 1000 { print $1, $3 }' /etc/passwd | head -5
rm /tmp/awk-data.txt 2>/dev/null
echo "Practitioner Lab 2 complete"
```

## 📝 Summary
- `awk '{ print $1 }'` prints the first whitespace-separated field
- `-F:` sets field separator to colon (for /etc/passwd)
- `NR` is the current line number; `NF` is the number of fields
- `$NF` refers to the last field dynamically
- `BEGIN {}` runs before processing; `END {}` runs after all lines
- Pattern matching: `awk '/pattern/ { action }'` or `awk '$3 >= 1000 { action }'`
