# Lab 15: File Operations in Scripts

## 🎯 Objective
Use file test operators, read file contents in scripts, and use process substitution for advanced file processing.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Practitioner Labs 7 (Conditionals) and 8 (Loops)

## 🔬 Lab Instructions

### Step 1: File Test Operators

```bash
# Set up test environment
mkdir -p /tmp/fileops-lab
echo "content" > /tmp/fileops-lab/readable.txt
chmod 400 /tmp/fileops-lab/readable.txt   # read-only
touch /tmp/fileops-lab/empty.txt
echo "executable" > /tmp/fileops-lab/script.sh
chmod 755 /tmp/fileops-lab/script.sh

# Test each operator
[[ -e "/tmp/fileops-lab/readable.txt" ]] && echo "-e: file exists"
[[ -f "/tmp/fileops-lab/readable.txt" ]] && echo "-f: is regular file"
[[ -d "/tmp/fileops-lab" ]] && echo "-d: is directory"
[[ -r "/tmp/fileops-lab/readable.txt" ]] && echo "-r: is readable"
[[ -w "/tmp/fileops-lab/readable.txt" ]] && echo "-w: is writable" || echo "-w: NOT writable (expected)"
[[ -x "/tmp/fileops-lab/script.sh" ]] && echo "-x: is executable"
[[ -s "/tmp/fileops-lab/readable.txt" ]] && echo "-s: non-empty file"
[[ ! -s "/tmp/fileops-lab/empty.txt" ]] && echo "!-s: empty file"
```

**Expected output:**
```
-e: file exists
-f: is regular file
-d: is directory
-r: is readable
-w: NOT writable (expected)
-x: is executable
-s: non-empty file
!-s: empty file
```

### Step 2: Compare Files

```bash
cp /tmp/fileops-lab/readable.txt /tmp/fileops-lab/copy.txt
chmod 644 /tmp/fileops-lab/readable.txt

# -nt: newer than; -ot: older than; -ef: same file (hard link)
[[ "/tmp/fileops-lab/copy.txt" -nt "/tmp/fileops-lab/readable.txt" ]] && echo "copy is newer" || echo "copy is older or same"
[[ "/tmp/fileops-lab/readable.txt" -ot "/tmp/fileops-lab/copy.txt" ]] && echo "readable is older"
```

### Step 3: Read File Line by Line

```bash
cat > /tmp/fileops-lab/hosts.txt << 'EOF'
192.168.1.10 web01.local
192.168.1.11 web02.local
192.168.1.20 db01.local
192.168.1.30 cache01.local
EOF

# Read line by line preserving whitespace
while IFS= read -r line; do
    echo "Line: $line"
done < /tmp/fileops-lab/hosts.txt
```

```bash
# Parse specific fields while reading
while IFS=" " read -r ip hostname; do
    echo "IP: $ip -> Host: $hostname"
done < /tmp/fileops-lab/hosts.txt
```

**Expected output:**
```
IP: 192.168.1.10 -> Host: web01.local
IP: 192.168.1.11 -> Host: web02.local
...
```

### Step 4: Skip Comments and Blank Lines

```bash
cat > /tmp/fileops-lab/config.conf << 'EOF'
# Server configuration
host = web01

# Database settings
db_host = db01
db_port = 5432

# Cache
cache_host = cache01
EOF

while IFS= read -r line; do
    # Skip comments and blank lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${line// }" ]] && continue
    echo "Config: $line"
done < /tmp/fileops-lab/config.conf
```

**Expected output:**
```
Config: host = web01
Config: db_host = db01
Config: db_port = 5432
Config: cache_host = cache01
```

### Step 5: Process Substitution

```bash
# <() creates a virtual file from command output
while IFS= read -r user; do
    echo "System user: $user"
done < <(cut -d: -f1 /etc/passwd | head -5)
```

```bash
# Compare two command outputs
diff <(cut -d: -f1 /etc/passwd | sort) <(cut -d: -f1 /etc/group | sort) | head -15
```

```bash
# Feed sorted output to while
while IFS=: read -r name _ uid _; do
    echo "UID $uid: $name"
done < <(sort -t: -k3 -n /etc/passwd | head -5)
```

### Step 6: Write to Files Safely

```bash
# Atomic write: write to temp then move
cat > /tmp/fileops-lab/write-safe.sh << 'EOF'
#!/bin/bash
OUTPUT_FILE="/tmp/fileops-lab/config-final.txt"
TEMP_FILE=$(mktemp /tmp/fileops-lab/config.XXXXXX)

# Write to temp file
cat > "$TEMP_FILE" << 'CONFEOF'
host = production
port = 443
debug = false
CONFEOF

# Atomically replace (move is atomic on same filesystem)
mv "$TEMP_FILE" "$OUTPUT_FILE"
echo "Written: $OUTPUT_FILE"
cat "$OUTPUT_FILE"
EOF

bash /tmp/fileops-lab/write-safe.sh
```

### Step 7: Find and Process Files

```bash
# Process all .txt files
find /tmp/fileops-lab -name "*.txt" -type f | while IFS= read -r f; do
    lines=$(wc -l < "$f")
    echo "$f: $lines lines"
done
```

```bash
# Check if any files need attention
find /tmp/fileops-lab -type f -newer /tmp/fileops-lab/empty.txt 2>/dev/null | while IFS= read -r f; do
    echo "Recently modified: $f"
done
```

## ✅ Verification

```bash
[[ -f "/tmp/fileops-lab/readable.txt" ]] && echo "PASS: -f test"
[[ -d "/tmp/fileops-lab" ]] && echo "PASS: -d test"
[[ -x "/tmp/fileops-lab/script.sh" ]] && echo "PASS: -x test"

echo "PASS: while read test:"
echo -e "line1\nline2\nline3" | while IFS= read -r line; do echo "  $line"; done

rm -r /tmp/fileops-lab
echo "Practitioner Lab 15 complete"
```

## 📝 Summary
- File tests: `-f` (regular file), `-d` (directory), `-e` (exists), `-r/-w/-x` (permissions)
- `-s` tests non-empty file; `-nt` newer than; `-ot` older than
- `while IFS= read -r line; do ... done < file` reads file line by line
- `IFS=" " read -r field1 field2` splits each line into variables
- Skip lines with `[[ "$line" =~ ^# ]] && continue`
- Process substitution `< <(command)` feeds command output like a file
- Use `mktemp` + `mv` for atomic file writes
