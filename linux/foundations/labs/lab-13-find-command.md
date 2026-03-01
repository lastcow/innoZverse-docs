# Lab 13: The find Command

## 🎯 Objective
Master the find command to search for files by name, type, size, and modification time, and execute actions on results.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 12: vim Basics

## 🔬 Lab Instructions

### Step 1: Set Up Test Files

```bash
mkdir -p /tmp/find-lab/docs /tmp/find-lab/scripts /tmp/find-lab/logs

echo "document 1" > /tmp/find-lab/docs/report.txt
echo "document 2" > /tmp/find-lab/docs/notes.txt
echo "document 3" > /tmp/find-lab/docs/readme.md
echo "#!/bin/bash" > /tmp/find-lab/scripts/deploy.sh
echo "#!/bin/bash" > /tmp/find-lab/scripts/backup.sh
echo "2026-01-01 INFO started" > /tmp/find-lab/logs/app.log
echo "2026-01-02 ERROR failed" > /tmp/find-lab/logs/error.log

find /tmp/find-lab
```

### Step 2: Find by Name

```bash
find /tmp/find-lab -name "report.txt"
```

**Expected output:**
```
/tmp/find-lab/docs/report.txt
```

```bash
find /tmp/find-lab -name "*.txt"
find /tmp/find-lab -iname "*.LOG"
find /tmp/find-lab -name "*.sh"
```

### Step 3: Find by Type

```bash
find /tmp/find-lab -type f
find /tmp/find-lab -type d
```

### Step 4: Limit Search Depth

```bash
find /tmp/find-lab -maxdepth 1
find /tmp/find-lab -mindepth 2 -maxdepth 2 -type f
```

### Step 5: Find by Size

```bash
python3 -c "print('x' * 1000)" > /tmp/find-lab/small.txt
python3 -c "print('x' * 100000)" > /tmp/find-lab/medium.txt

find /tmp/find-lab -size +1k -type f
```

**Expected output:**
```
/tmp/find-lab/medium.txt
```

```bash
find /tmp/find-lab -size -10k -type f | head -10
find /tmp/find-lab -size 0 -type f
```

### Step 6: Find by Modification Time

```bash
find /tmp/find-lab -mtime -1 -type f
find /tmp/find-lab -mmin -60 -type f
```

### Step 7: Find in Home Directory

```bash
find ~ -maxdepth 1 -name ".*" -type f | head -10
find ~ -maxdepth 2 -mtime -7 -type f 2>/dev/null | head -10
```

### Step 8: Execute Actions with -exec

```bash
find /tmp/find-lab -name "*.txt" -exec echo "Found: {}" \;
```

**Expected output:**
```
Found: /tmp/find-lab/docs/report.txt
Found: /tmp/find-lab/docs/notes.txt
...
```

```bash
find /tmp/find-lab -name "*.sh" -exec ls -l {} \;
find /tmp/find-lab -name "*.txt" -exec wc -l {} +
```

### Step 9: Combine Conditions

```bash
find /tmp/find-lab -name "*.log" -type f
find /tmp/find-lab \( -name "*.txt" -o -name "*.md" \) -type f
find /tmp/find-lab -type f ! -name "*.log"
```

## ✅ Verification

```bash
echo "All files in find-lab:"
find /tmp/find-lab -type f | wc -l

echo "Shell scripts:"
find /tmp/find-lab -name "*.sh" | sort

echo "Files modified today:"
find /tmp/find-lab -mtime -1 -type f | wc -l

rm -r /tmp/find-lab
echo "Lab 13 complete"
```

## 📝 Summary
- `find /path -name "pattern"` searches by filename; use `*` wildcards
- `-type f` for files, `-type d` for directories
- `-size +1k` finds files larger than 1KB
- `-mtime -1` finds files modified in the last 24 hours
- `-exec command {} \;` runs a command on each result
- `-maxdepth N` limits search depth; use `-o` for OR conditions
