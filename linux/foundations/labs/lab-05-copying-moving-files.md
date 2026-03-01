# Lab 5: Copying and Moving Files

## 🎯 Objective
Master copying files and directories with `cp` and moving/renaming them with `mv`, including key options and real-world usage patterns.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Completed Labs 1–4
- Ability to create files and navigate directories

## 🔬 Lab Instructions

### Step 1: Set Up a Working Environment
```bash
mkdir -p ~/lab05/source ~/lab05/backup ~/lab05/archive
cd ~/lab05
echo "Original content" > source/original.txt
echo "Config data" > source/app.conf
echo "Log entry 1" > source/app.log
ls source/
# Output: app.conf  app.log  original.txt
```

### Step 2: Copy a Single File with `cp`
```bash
cp source/original.txt backup/original.txt
ls backup/
# Output: original.txt

# Verify the copy has the same content
cat backup/original.txt
# Output: Original content
```

### Step 3: Copy to a Directory (Keeping Filename)
```bash
cp source/app.conf backup/
ls backup/
# Output: app.conf  original.txt
# cp automatically keeps the filename when destination is a directory
```

### Step 4: Copy with a New Name
```bash
cp source/app.log backup/app.log.bak
ls backup/
# Output: app.conf  app.log.bak  original.txt
```

### Step 5: Copy Multiple Files at Once
```bash
cp source/app.conf source/app.log archive/
ls archive/
# Output: app.conf  app.log
```

### Step 6: Copy a Directory Recursively with `-r`
```bash
cp -r source/ backup/source_copy
ls backup/
# Output: app.conf  app.log.bak  original.txt  source_copy

ls backup/source_copy/
# Output: app.conf  app.log  original.txt
```

### Step 7: Copy and Preserve Timestamps with `-p`
```bash
cp -p source/original.txt backup/original_preserved.txt
ls -la source/original.txt backup/original_preserved.txt
# Timestamps and permissions should match
```

### Step 8: Interactive Copy with `-i` (Prevent Overwrite)
```bash
cp -i source/original.txt backup/original.txt
# Output: cp: overwrite 'backup/original.txt'? 
# Type 'y' to overwrite, 'n' to skip
```

### Step 9: Move (Rename) a File with `mv`
```bash
# Rename a file
mv backup/app.log.bak backup/app.log.backup
ls backup/
# app.log.bak is gone, app.log.backup is present
```

### Step 10: Move a File to Another Directory
```bash
mv backup/app.log.backup archive/
ls backup/
# app.log.backup is gone from backup/

ls archive/
# app.log.backup is now in archive/
```

### Step 11: Move Multiple Files
```bash
touch source/data1.csv source/data2.csv source/data3.csv
mv source/data1.csv source/data2.csv source/data3.csv archive/
ls archive/
# Output: app.conf  app.log  app.log.backup  data1.csv  data2.csv  data3.csv
```

### Step 12: Move an Entire Directory
```bash
mv backup/source_copy archive/source_backup
ls backup/
# source_copy is gone

ls archive/
# source_backup is present

# Clean up
cd ~
rm -r ~/lab05
```

## ✅ Verification
```bash
# Quick copy/move test
mkdir -p /tmp/cptest/{src,dst}
echo "test" > /tmp/cptest/src/file.txt
cp /tmp/cptest/src/file.txt /tmp/cptest/dst/
mv /tmp/cptest/src/file.txt /tmp/cptest/src/file_moved.txt
ls /tmp/cptest/src/
# Output: file_moved.txt (file.txt is gone)
ls /tmp/cptest/dst/
# Output: file.txt

rm -r /tmp/cptest
```

## 📝 Summary
- `cp source dest` copies files; use `-r` for directories; `-p` preserves permissions and timestamps
- `mv source dest` moves or renames files and directories
- When the destination is a directory, the original filename is kept
- Use `-i` with `cp` or `mv` in production to avoid accidental overwrites
- `mv` is atomic on the same filesystem (instant rename); `cp` physically duplicates data
