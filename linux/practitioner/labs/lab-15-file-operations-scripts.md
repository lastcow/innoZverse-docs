# Lab 15: File Operations in Scripts

## 🎯 Objective
Use file test operators (`-f`, `-d`, `-e`, `-s`), read files line by line, and safely handle file creation and deletion in Bash scripts.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Labs 7–8 (Conditionals and Loops)

## 🔬 Lab Instructions

### Step 1: File Test Operators
```bash
# Common test operators:
# -e  file exists (any type)
# -f  regular file
# -d  directory
# -L  symbolic link
# -r  readable
# -w  writable
# -x  executable
# -s  file exists and is non-empty

test -f /etc/passwd && echo "exists as file"
# exists as file
test -d /etc && echo "exists as directory"
# exists as directory
[[ -e /tmp ]] && echo "/tmp exists"
# /tmp exists
```

### Step 2: Check File Existence Before Acting
```bash
FILE="/etc/hosts"

if [[ -f "$FILE" ]]; then
    echo "File exists: $FILE"
    echo "Size: $(wc -c < "$FILE") bytes"
else
    echo "File not found: $FILE"
fi
# File exists: /etc/hosts
# Size: 221 bytes
```

### Step 3: Check Permissions
```bash
FILE="/etc/shadow"
if [[ -r "$FILE" ]]; then
    echo "Readable"
else
    echo "Not readable (need root)"
fi
# Not readable (need root)

SCRIPT=~/cron_test.sh
if [[ -x "$SCRIPT" ]]; then
    echo "Executable"
else
    echo "Not executable"
fi
```

### Step 4: Create Test Files and Directories
```bash
mkdir -p ~/lab15/{input,output,logs}
echo "line one"   > ~/lab15/input/file1.txt
echo "line two"  >> ~/lab15/input/file1.txt
echo "line three" >> ~/lab15/input/file1.txt
touch ~/lab15/input/empty.txt

[[ -s ~/lab15/input/file1.txt ]] && echo "file1.txt is non-empty"
# file1.txt is non-empty
[[ -s ~/lab15/input/empty.txt ]] || echo "empty.txt is empty or zero-size"
# empty.txt is empty or zero-size
```

### Step 5: Read a File Line by Line
```bash
while IFS= read -r line; do
    echo "LINE: $line"
done < ~/lab15/input/file1.txt
# LINE: line one
# LINE: line two
# LINE: line three
```

### Step 6: Process File Lines with Logic
```bash
cat > ~/lab15/input/servers.txt << 'EOF'
web01 192.168.1.10
web02 192.168.1.11
db01  192.168.1.20
cache01 192.168.1.30
EOF

while IFS=' ' read -r name ip; do
    echo "Server: $name  IP: $ip"
done < ~/lab15/input/servers.txt
# Server: web01  IP: 192.168.1.10
# Server: web02  IP: 192.168.1.11
# Server: db01   IP: 192.168.1.20
# Server: cache01 IP: 192.168.1.30
```

### Step 7: Find Files Matching Criteria
```bash
# Find all .txt files in lab15
find ~/lab15 -name "*.txt" -type f
# /home/ubuntu/lab15/input/file1.txt
# /home/ubuntu/lab15/input/servers.txt
# /home/ubuntu/lab15/input/empty.txt

# Find files modified in last 10 minutes
find ~/lab15 -mmin -10 -type f
```

### Step 8: Safe File Deletion
```bash
FILE=~/lab15/input/empty.txt
if [[ -f "$FILE" ]]; then
    rm "$FILE"
    echo "Deleted: $FILE"
else
    echo "File not found, skipping deletion"
fi
# Deleted: /home/ubuntu/lab15/input/empty.txt
```

### Step 9: Write Script Output to Log Files
```bash
LOGFILE=~/lab15/logs/run.log

{
    echo "=== Run started: $(date) ==="
    echo "User: $USER"
    echo "Hostname: $(hostname)"
    uptime
    echo "=== Run complete ==="
} >> "$LOGFILE"

cat "$LOGFILE"
# === Run started: Sun Mar  1 06:01:00 UTC 2026 ===
# User: ubuntu
# Hostname: myserver
```

### Step 10: Full Script — Batch File Processor
```bash
cat > ~/lab15/process_files.sh << 'EOF'
#!/bin/bash
INPUT_DIR="${1:-$HOME/lab15/input}"
OUTPUT_DIR="${2:-$HOME/lab15/output}"
LOG="$HOME/lab15/logs/process.log"

[[ -d "$INPUT_DIR" ]] || { echo "Input dir not found: $INPUT_DIR"; exit 1; }
mkdir -p "$OUTPUT_DIR"

echo "Processing files in $INPUT_DIR" | tee -a "$LOG"

for file in "$INPUT_DIR"/*.txt; do
    [[ -f "$file" ]] || continue
    [[ -s "$file" ]] || { echo "Skipping empty: $file" | tee -a "$LOG"; continue; }

    bname=$(basename "$file")
    out="$OUTPUT_DIR/${bname%.txt}_processed.txt"
    lines=$(wc -l < "$file")
    echo "Processing $bname ($lines lines)" | tee -a "$LOG"
    tr '[:lower:]' '[:upper:]' < "$file" > "$out"
    echo "  Written: $out" | tee -a "$LOG"
done

echo "Done. Check $OUTPUT_DIR" | tee -a "$LOG"
EOF
chmod +x ~/lab15/process_files.sh
~/lab15/process_files.sh
# Processing files in /home/ubuntu/lab15/input
# Processing file1.txt (3 lines)
#   Written: /home/ubuntu/lab15/output/file1_processed.txt
```

## ✅ Verification
```bash
[[ -f ~/lab15/output/file1_processed.txt ]] && cat ~/lab15/output/file1_processed.txt
# LINE ONE
# LINE TWO
# LINE THREE
cat ~/lab15/logs/process.log
```

## 📝 Summary
- `-f` tests regular file; `-d` directory; `-e` any type; `-s` non-empty
- `while IFS= read -r line; do ... done < file` reads files safely
- Always verify file existence before reading or deleting
- `find` with `-name`, `-type`, `-mmin` locates files matching criteria
- Use `tee -a logfile` to log output while still printing to screen
