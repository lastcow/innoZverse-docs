# Lab 6: Deleting Files Safely

## 🎯 Objective
Learn safe file deletion patterns using rm, understand the risks, and practice safe deletion habits using /tmp.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 5: Copying and Moving Files

## 🔬 Lab Instructions

### Step 1: Create Test Files for Deletion Practice

```bash
mkdir -p /tmp/del-lab
echo "file 1" > /tmp/del-lab/file1.txt
echo "file 2" > /tmp/del-lab/file2.txt
echo "file 3" > /tmp/del-lab/file3.txt
ls /tmp/del-lab
```

### Step 2: Delete a Single File

```bash
rm /tmp/del-lab/file1.txt
ls /tmp/del-lab
```

**Expected output:**
```
file2.txt  file3.txt
```

```bash
ls /tmp/del-lab/file1.txt 2>/dev/null || echo "File successfully deleted"
```

### Step 3: Delete Multiple Files

```bash
echo "a" > /tmp/del-lab/a.txt
echo "b" > /tmp/del-lab/b.txt
echo "c" > /tmp/del-lab/c.txt
rm /tmp/del-lab/a.txt /tmp/del-lab/b.txt /tmp/del-lab/c.txt
ls /tmp/del-lab
```

```bash
echo "log1" > /tmp/del-lab/app.log
echo "log2" > /tmp/del-lab/error.log
echo "keep" > /tmp/del-lab/important.conf
rm /tmp/del-lab/*.log
ls /tmp/del-lab
```

**Expected output:**
```
file2.txt  file3.txt  important.conf
```

### Step 4: Delete Directories

```bash
mkdir -p /tmp/del-lab/old-project/src
echo "code" > /tmp/del-lab/old-project/src/main.py
rm -r /tmp/del-lab/old-project
ls /tmp/del-lab
echo "Directory removed: $?"
```

### Step 5: Safe Deletion Patterns

```bash
# Pattern 1: List before deleting
echo "1" > /tmp/del-lab/test1.txt
echo "2" > /tmp/del-lab/test2.txt
ls /tmp/del-lab/test*.txt
rm /tmp/del-lab/test*.txt
```

```bash
# Pattern 2: Use a variable to avoid typos
TARGET_DIR="/tmp/del-lab/cleanup"
mkdir -p "$TARGET_DIR"
echo "data" > "$TARGET_DIR/data.txt"
rm -r "$TARGET_DIR"
echo "Cleaned up: $TARGET_DIR"
```

```bash
# Pattern 3: Count before deleting
mkdir -p /tmp/del-lab/project
echo "file" > /tmp/del-lab/project/file.txt
echo "Found $(find /tmp/del-lab 2>/dev/null/project -type f | wc -l) files to delete"
rm -r /tmp/del-lab/project
```

### Step 6: Suppress Errors and Verbose Mode

```bash
rm /tmp/nonexistent.txt 2>/dev/null
echo "Suppressed error exit code: $?"
rm -f /tmp/nonexistent.txt
echo "Exit code with -f: $?"
```

```bash
echo "a" > /tmp/del-lab/verbose1.txt
echo "b" > /tmp/del-lab/verbose2.txt
rm -v /tmp/del-lab/verbose1.txt /tmp/del-lab/verbose2.txt
```

**Expected output:**
```
removed '/tmp/del-lab/verbose1.txt'
removed '/tmp/del-lab/verbose2.txt'
```

## ✅ Verification

```bash
mkdir -p /tmp/lab6-verify
echo "test" > /tmp/lab6-verify/file.txt
rm /tmp/lab6-verify/file.txt
ls /tmp/lab6-verify/file.txt 2>/dev/null && echo "FAIL: file still exists" || echo "PASS: file deleted"
rmdir /tmp/lab6-verify
rm -r /tmp/del-lab 2>/dev/null
echo "Verification complete"
```

## 📝 Summary
- `rm` permanently deletes files — there is no recycle bin in Linux
- `rm -r` recursively deletes directories and their contents
- `rm -v` shows what is being deleted (verbose)
- `rm -f` suppresses errors for missing files
- Always practice in `/tmp` first; always quote variables in `rm` commands
- List what you're about to delete before running `rm -r`
