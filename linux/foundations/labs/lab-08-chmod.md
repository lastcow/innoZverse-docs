# Lab 8: Changing Permissions with chmod

## 🎯 Objective
Use chmod to change file permissions using both symbolic notation (u+x, g-w, o=r) and octal notation (755, 644).

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 7: Understanding File Permissions

## 🔬 Lab Instructions

### Step 1: Set Up Test Files

```bash
mkdir -p /tmp/chmod-lab
touch /tmp/chmod-lab/script.sh
touch /tmp/chmod-lab/config.txt
touch /tmp/chmod-lab/data.bin
ls -l /tmp/chmod-lab
```

### Step 2: Symbolic Mode — Add Permissions

```bash
# chmod [who][operator][permission] file
# who: u=user, g=group, o=others, a=all
# operator: +=add, -=remove, ==set exactly

chmod u+x /tmp/chmod-lab/script.sh
ls -l /tmp/chmod-lab/script.sh
```

**Expected output:**
```
-rwxrw-r-- 1 zchen zchen 0 ... script.sh
```

```bash
chmod g+rw /tmp/chmod-lab/config.txt
ls -l /tmp/chmod-lab/config.txt
chmod o-w /tmp/chmod-lab/data.bin
ls -l /tmp/chmod-lab/data.bin
```

### Step 3: Symbolic Mode — Set Exact Permissions

```bash
chmod u=rwx,g=rx,o=r /tmp/chmod-lab/script.sh
ls -l /tmp/chmod-lab/script.sh
```

**Expected output:**
```
-rwxr-xr-- 1 zchen zchen 0 ... script.sh
```

```bash
chmod a=r /tmp/chmod-lab/config.txt
ls -l /tmp/chmod-lab/config.txt
chmod u+w /tmp/chmod-lab/config.txt
ls -l /tmp/chmod-lab/config.txt
```

### Step 4: Octal Mode — Common Settings

```bash
# 755: owner=rwx, group=r-x, others=r-x (standard for executables)
chmod 755 /tmp/chmod-lab/script.sh
ls -l /tmp/chmod-lab/script.sh
```

**Expected output:**
```
-rwxr-xr-x 1 zchen zchen 0 ... script.sh
```

```bash
# 644: owner=rw-, group=r--, others=r-- (standard for files)
chmod 644 /tmp/chmod-lab/config.txt
ls -l /tmp/chmod-lab/config.txt
```

**Expected output:**
```
-rw-r--r-- 1 zchen zchen 0 ... config.txt
```

```bash
# 600: owner=rw-, group=none, others=none (private files)
chmod 600 /tmp/chmod-lab/data.bin
ls -l /tmp/chmod-lab/data.bin
```

**Expected output:**
```
-rw------- 1 zchen zchen 0 ... data.bin
```

```bash
# 700: owner=rwx, group=none, others=none (private directories)
mkdir /tmp/chmod-lab/private
chmod 700 /tmp/chmod-lab/private
ls -ld /tmp/chmod-lab/private
```

### Step 5: chmod on Directories and Recursive

```bash
mkdir /tmp/chmod-lab/shared
chmod 755 /tmp/chmod-lab/shared
ls -ld /tmp/chmod-lab/shared
```

```bash
mkdir -p /tmp/chmod-lab/project/src
touch /tmp/chmod-lab/project/src/main.sh
chmod -R 755 /tmp/chmod-lab/project
find /tmp/chmod-lab/project -exec ls -ld {} \;
```

### Step 6: Verify with stat

```bash
chmod 644 /tmp/chmod-lab/config.txt
stat /tmp/chmod-lab/config.txt | grep "Access:"
```

**Expected output:**
```
Access: (0644/-rw-r--r--)  Uid: (...)
```

```bash
stat -c "%a %n" /tmp/chmod-lab/script.sh
stat -c "%a %n" /tmp/chmod-lab/config.txt
stat -c "%a %n" /tmp/chmod-lab/data.bin
```

## ✅ Verification

```bash
cd /tmp/chmod-lab

chmod 755 script.sh
chmod 644 config.txt
chmod 600 data.bin

echo "script.sh: $(stat -c '%a' script.sh) (expect 755)"
echo "config.txt: $(stat -c '%a' config.txt) (expect 644)"
echo "data.bin: $(stat -c '%a' data.bin) (expect 600)"

cd /tmp && rm -r /tmp/chmod-lab
echo "chmod lab complete"
```

## 📝 Summary
- Symbolic: `chmod u+x file`, `chmod g-w file`, `chmod o=r file`
- `u`=user/owner, `g`=group, `o`=others, `a`=all three
- `+`=add, `-`=remove, `=`=set exactly
- Octal: `chmod 755 file` — three digits for user, group, others
- Common: 755 (executable), 644 (file), 600 (private), 700 (private dir)
- `chmod -R` applies permissions recursively
- `stat -c "%a %n"` shows the octal value
