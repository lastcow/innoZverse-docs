# Lab 7: Understanding File Permissions

## 🎯 Objective
Understand Linux file permission output from ls -l, read octal notation, and use stat to inspect permissions in detail.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 6: Deleting Files Safely

## 🔬 Lab Instructions

### Step 1: Read ls -l Permission Output

```bash
mkdir -p /tmp/perm-lab
touch /tmp/perm-lab/script.sh /tmp/perm-lab/config.txt /tmp/perm-lab/data.csv
ls -l /tmp/perm-lab
```

**Expected output:**
```
-rw-rw-r-- 1 zchen zchen 0 Mar  1 17:00 config.txt
-rw-rw-r-- 1 zchen zchen 0 Mar  1 17:00 data.csv
-rw-rw-r-- 1 zchen zchen 0 Mar  1 17:00 script.sh
```

```bash
# The permission string breakdown:
# -rw-r--r--
# ^ file type: - (file), d (dir), l (link)
#  ^^^ user/owner permissions: rw-
#     ^^^ group permissions: r--
#        ^^^ others permissions: r--
ls -l /etc/passwd /bin/ls
ls -ld /tmp
```

### Step 2: Understand Permission Bits

```bash
# r = read  (4)
# w = write (2)
# x = execute (1)
# - = no permission (0)
ls -l /bin/bash
ls -l /etc/passwd
ls -ld /tmp
```

**Expected output (excerpt):**
```
-rwxr-xr-x ... /bin/bash    <- executable by all
-rw-r--r-- ... /etc/passwd  <- readable by all, writable by root
drwxrwxrwt ... /tmp         <- sticky bit (t)
```

### Step 3: Read Octal Notation

```bash
# Octal: each group sums to a single digit
# r=4, w=2, x=1
# rw-  = 4+2+0 = 6
# r-x  = 4+0+1 = 5
# r--  = 4+0+0 = 4
# rwx  = 4+2+1 = 7

stat /etc/passwd
```

**Expected output includes:**
```
Access: (0644/-rw-r--r--)  Uid: (    0/    root)
```

```bash
echo "755 = rwxr-xr-x  (executables)"
echo "644 = rw-r--r--  (regular files)"
echo "600 = rw-------  (private files)"
echo "700 = rwx------  (private directories)"
```

### Step 4: Use stat to Check Permissions

```bash
stat /tmp/perm-lab/config.txt
stat ~
stat -c "%a %n" /etc/passwd /bin/ls /tmp
```

**Expected output:**
```
644 /etc/passwd
755 /bin/ls
1777 /tmp
```

### Step 5: Directory Permissions

```bash
# For directories:
# r = can list files (ls works)
# w = can create/delete files inside
# x = can enter the directory (cd works)
mkdir -p /tmp/perm-lab/shared-dir
ls -ld /tmp/perm-lab/shared-dir
ls -ld /tmp
```

**Expected output (for /tmp):**
```
drwxrwxrwt ... /tmp
              ^--- t = sticky bit (only owner can delete their files)
```

### Step 6: Find Files by Permission

```bash
find ~ -maxdepth 2 -perm 600 2>/dev/null | head -5
find /usr/bin -maxdepth 1 -perm /u+x -type f | head -10
```

## ✅ Verification

```bash
echo "=== /etc/passwd ===" && stat /etc/passwd | grep Access:
echo "=== /bin/ls ===" && stat /bin/ls | grep Access:
echo "=== /tmp ===" && stat /tmp | grep Access:
echo "=== perm-lab file ===" && stat -c "%a" /tmp/perm-lab/config.txt
rm -r /tmp/perm-lab
echo "Lab 7 complete"
```

## 📝 Summary
- `ls -l` shows permissions as: type + user(3) + group(3) + others(3)
- Permissions: `r`=read(4), `w`=write(2), `x`=execute(1), `-`=none(0)
- Octal notation: 755=rwxr-xr-x, 644=rw-r--r--, 600=rw-------
- `stat` shows the octal value directly under `Access:`
- Directory `x` bit means you can `cd` into it; `w` means you can create files
- The sticky bit `t` on /tmp prevents users from deleting each other's files
