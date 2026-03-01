# Lab 3: Directory Navigation

## 🎯 Objective
Master creating, navigating, and removing directory structures using mkdir, rmdir, cd, pwd, and find as a tree replacement.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 2: Filesystem Hierarchy

## 🔬 Lab Instructions

### Step 1: Create a Directory Structure

```bash
mkdir /tmp/myproject
mkdir -p /tmp/myproject/src/utils
mkdir -p /tmp/myproject/docs
mkdir -p /tmp/myproject/tests
ls /tmp/myproject
```

**Expected output:**
```
docs  src  tests
```

### Step 2: Navigate with cd and pwd

```bash
cd /tmp/myproject
pwd
```

**Expected output:**
```
/tmp/myproject
```

```bash
cd ..
pwd
```

**Expected output:**
```
/tmp
```

```bash
cd ~
pwd
```

```bash
cd /tmp/myproject/src
cd -
pwd
```

### Step 3: Absolute vs Relative Paths

```bash
cd /tmp/myproject/docs
cd ../src
pwd
```

**Expected output:**
```
/tmp/myproject/src
```

```bash
ls .
ls ..
```

### Step 4: Simulate tree with find

```bash
find /tmp/myproject -type d
```

**Expected output:**
```
/tmp/myproject
/tmp/myproject/docs
/tmp/myproject/src
/tmp/myproject/src/utils
/tmp/myproject/tests
```

```bash
find /tmp/myproject -maxdepth 2
```

```bash
find /tmp/myproject | sort | awk -F/ '{ indent=""; for(i=5;i<NF;i++) indent=indent"  "; print indent $NF }'
```

### Step 5: Create Files in the Structure

```bash
touch /tmp/myproject/docs/README.md
touch /tmp/myproject/src/main.py
touch /tmp/myproject/src/utils/helpers.py
touch /tmp/myproject/tests/test_main.py
find /tmp/myproject
```

### Step 6: Remove Directories

```bash
mkdir /tmp/emptydir
rmdir /tmp/emptydir
echo "rmdir exit code: $?"
```

**Expected output:**
```
rmdir exit code: 0
```

```bash
rm -r /tmp/myproject
ls /tmp/myproject 2>/dev/null || echo "Directory successfully removed"
```

## ✅ Verification

```bash
mkdir -p /tmp/verify-lab/{alpha,beta,gamma/subdir}
find /tmp/verify-lab -type d | sort
echo "Directory count: $(find /tmp/verify-lab -type d | wc -l)"
rm -r /tmp/verify-lab
echo "Cleanup done"
```

## 📝 Summary
- `mkdir -p` creates nested directories in one command
- `cd`, `cd ..`, `cd ~`, and `cd -` navigate the filesystem
- `pwd` always shows your current absolute location
- `find -type d` replaces `tree` when tree is not installed
- `rmdir` removes empty directories; `rm -r` removes trees (use carefully)
- `.` means current directory; `..` means parent directory
