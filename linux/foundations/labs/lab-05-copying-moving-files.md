# Lab 5: Copying and Moving Files

## 🎯 Objective
Learn to copy and move files and directories using cp and mv, including backup options and recursive operations.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Lab 4: File Creation and Viewing

## 🔬 Lab Instructions

### Step 1: Set Up a Working Environment

```bash
mkdir -p /tmp/cp-lab/source /tmp/cp-lab/dest
echo "Config version 1" > /tmp/cp-lab/source/config.txt
echo "Data file content" > /tmp/cp-lab/source/data.csv
echo "README content" > /tmp/cp-lab/source/README.md
ls /tmp/cp-lab/source
```

### Step 2: Copy Files with cp

```bash
cp /tmp/cp-lab/source/config.txt /tmp/cp-lab/dest/
ls /tmp/cp-lab/dest
```

**Expected output:**
```
config.txt
```

```bash
cp /tmp/cp-lab/source/README.md /tmp/cp-lab/dest/README-copy.md
cp /tmp/cp-lab/source/config.txt /tmp/cp-lab/source/data.csv /tmp/cp-lab/dest/
ls /tmp/cp-lab/dest
```

### Step 3: Copy Directories Recursively

```bash
mkdir -p /tmp/cp-lab/source/subdir
echo "nested file" > /tmp/cp-lab/source/subdir/nested.txt
cp -r /tmp/cp-lab/source/subdir /tmp/cp-lab/dest/
find /tmp/cp-lab/dest -type f
```

### Step 4: Copy with Backup Option

```bash
echo "Old content" > /tmp/cp-lab/dest/config.txt
cp --backup=simple /tmp/cp-lab/source/config.txt /tmp/cp-lab/dest/config.txt
ls /tmp/cp-lab/dest/
cat /tmp/cp-lab/dest/config.txt~
```

**Expected output:**
```
Old content
```

### Step 5: Copy Preserving Attributes

```bash
cp -p /tmp/cp-lab/source/data.csv /tmp/cp-lab/dest/data-preserved.csv
stat /tmp/cp-lab/source/data.csv | grep Modify
stat /tmp/cp-lab/dest/data-preserved.csv | grep Modify
```

### Step 6: Move Files with mv

```bash
mv /tmp/cp-lab/dest/README-copy.md /tmp/cp-lab/dest/README-final.md
ls /tmp/cp-lab/dest
```

```bash
mkdir -p /tmp/cp-lab/archive
mv /tmp/cp-lab/dest/data.csv /tmp/cp-lab/archive/
ls /tmp/cp-lab/dest
ls /tmp/cp-lab/archive
```

### Step 7: Rename with mv

```bash
echo "Original name" > /tmp/cp-lab/oldname.txt
mv /tmp/cp-lab/oldname.txt /tmp/cp-lab/newname.txt
ls /tmp/cp-lab/newname.txt
```

## ✅ Verification

```bash
mkdir -p /tmp/lab5-verify/{src,dst}
echo "test" > /tmp/lab5-verify/src/file.txt
cp /tmp/lab5-verify/src/file.txt /tmp/lab5-verify/dst/
mv /tmp/lab5-verify/dst/file.txt /tmp/lab5-verify/dst/moved.txt
ls /tmp/lab5-verify/dst/
echo "Content: $(cat /tmp/lab5-verify/dst/moved.txt)"
rm -r /tmp/lab5-verify /tmp/cp-lab
echo "Lab 5 complete"
```

## 📝 Summary
- `cp source dest` copies a file; `cp -r` copies directories recursively
- `cp --backup=simple` creates a `~` backup before overwriting
- `cp -p` preserves file timestamps, permissions, and ownership
- `mv source dest` moves or renames files and directories
- `mv` is the standard way to rename files in Linux
- Always use `-r` with `cp` when copying directories
