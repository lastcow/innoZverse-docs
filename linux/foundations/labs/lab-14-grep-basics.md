# Lab 14: Searching with grep

## 🎯 Objective
Use grep to search for patterns in files using key options: -i, -n, -v, -l, -c.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 13: find Command

## 🔬 Lab Instructions

### Step 1: Create Test Files

```bash
mkdir -p /tmp/grep-lab

cat > /tmp/grep-lab/server.log << 'EOF'
2026-01-01 10:00:01 INFO  Server started on port 8080
2026-01-01 10:01:15 INFO  Connection from 192.168.1.10
2026-01-01 10:02:30 ERROR Failed to read config file
2026-01-01 10:03:44 WARN  Memory usage at 80%
2026-01-01 10:04:55 INFO  Request processed: GET /api/users
2026-01-01 10:05:10 ERROR Database connection timeout
2026-01-01 10:06:20 INFO  Connection from 192.168.1.20
2026-01-01 10:07:35 DEBUG Processing request ID 12345
EOF

cat > /tmp/grep-lab/config.txt << 'EOF'
# Server Configuration
host=localhost
port=8080
debug=false
log_level=INFO
database_host=db01.example.com
database_port=5432
max_connections=100
EOF
```

### Step 2: Basic grep Usage

```bash
grep "ERROR" /tmp/grep-lab/server.log
```

**Expected output:**
```
2026-01-01 10:02:30 ERROR Failed to read config file
2026-01-01 10:05:10 ERROR Database connection timeout
```

```bash
grep "bash" /etc/passwd
grep "Ubuntu" /proc/version
```

### Step 3: Case-Insensitive Search (-i)

```bash
grep "error" /tmp/grep-lab/server.log
grep -i "error" /tmp/grep-lab/server.log
grep -i "HOST" /tmp/grep-lab/config.txt
```

### Step 4: Show Line Numbers (-n)

```bash
grep -n "INFO" /tmp/grep-lab/server.log
```

**Expected output:**
```
1:2026-01-01 10:00:01 INFO  Server started on port 8080
2:2026-01-01 10:01:15 INFO  Connection from 192.168.1.10
5:2026-01-01 10:04:55 INFO  Request processed: GET /api/users
7:2026-01-01 10:06:20 INFO  Connection from 192.168.1.20
```

### Step 5: Invert Match (-v)

```bash
grep -v "INFO" /tmp/grep-lab/server.log
grep -v "^#" /tmp/grep-lab/config.txt
grep -v "^#" /tmp/grep-lab/config.txt | grep -v "^$"
```

**Expected output (no comments):**
```
host=localhost
port=8080
debug=false
...
```

### Step 6: Count Matches (-c)

```bash
grep -c "INFO" /tmp/grep-lab/server.log
grep -c "ERROR" /tmp/grep-lab/server.log
grep -c "/bin/bash" /etc/passwd
```

### Step 7: List Files with Matches (-l)

```bash
echo "apple banana cherry" > /tmp/grep-lab/fruits.txt
echo "cat dog elephant" > /tmp/grep-lab/animals.txt
echo "apple pie recipe" > /tmp/grep-lab/recipes.txt

grep -l "apple" /tmp/grep-lab/*.txt
```

**Expected output:**
```
/tmp/grep-lab/fruits.txt
/tmp/grep-lab/recipes.txt
```

```bash
grep -L "apple" /tmp/grep-lab/*.txt
```

### Step 8: Combine Options and Recursive Search

```bash
grep -in "error" /tmp/grep-lab/server.log
grep "$(whoami)" /etc/passwd
grep -r "ERROR" /tmp/grep-lab/
grep -rl "INFO" /tmp/grep-lab/
```

## ✅ Verification

```bash
echo "ERROR count: $(grep -c "ERROR" /tmp/grep-lab/server.log)"
echo "INFO lines: $(grep -n "INFO" /tmp/grep-lab/server.log | wc -l)"
echo "Non-comment config lines: $(grep -v "^#" /tmp/grep-lab/config.txt | grep -vc "^$")"
echo "Files with apple: $(grep -l "apple" /tmp/grep-lab/*.txt | wc -l)"
rm -r /tmp/grep-lab
echo "Lab 14 complete"
```

## 📝 Summary
- `grep "pattern" file` finds lines matching a pattern
- `-i` makes search case-insensitive
- `-n` shows line numbers before matches
- `-v` inverts match — shows lines that do NOT match
- `-c` counts the number of matching lines
- `-l` shows filenames with matches; `-L` shows files without matches
- `-r` searches recursively through directories
