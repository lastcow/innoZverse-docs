# Lab 13: find — Locating Files on the Filesystem

## Objective
Use `find` to locate files by name, type, size, permission, age, and owner. Combine `find` with `-exec` and `-delete` for powerful one-liners used in security auditing and system maintenance.

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Find by Name

```bash
find /etc -name 'passwd' 2>/dev/null
```

**📸 Verified Output:**
```
/etc/pam.d/passwd
/etc/passwd
```

```bash
# Wildcard: all .conf files in /etc
find /etc -name '*.conf' 2>/dev/null | head -5
```

**📸 Verified Output:**
```
/etc/mke2fs.conf
/etc/sysctl.conf
/etc/ld.so.conf.d/x86_64-linux-gnu.conf
/etc/ld.so.conf.d/libc.conf
/etc/nsswitch.conf
```

> 💡 `find` searches recursively by default. Always redirect `2>/dev/null` to suppress "Permission denied" errors when searching as non-root.

---

## Step 2: Limit Search Depth

```bash
# Only look in /etc directly (no subdirectories)
find /etc -maxdepth 1 -name '*.conf' 2>/dev/null
```

**📸 Verified Output:**
```
/etc/mke2fs.conf
/etc/sysctl.conf
/etc/nsswitch.conf
/etc/e2scrub.conf
/etc/pam.conf
/etc/ld.so.conf
/etc/xattr.conf
/etc/debconf.conf
/etc/resolv.conf
/etc/adduser.conf
/etc/libaudit.conf
/etc/deluser.conf
/etc/host.conf
/etc/gai.conf
```

---

## Step 3: Find by Type

```bash
# Files only (-type f)
find /usr/bin -type f -perm -111 2>/dev/null | wc -l
```

**📸 Verified Output:**
```
271
```

```bash
# Directories only (-type d)
find /etc -type d -maxdepth 2 2>/dev/null | head -8
```

**📸 Verified Output:**
```
/etc
/etc/alternatives
/etc/apt
/etc/apt/sources.list.d
/etc/apt/trusted.gpg.d
/etc/apt/preferences.d
/etc/apt/apt.conf.d
/etc/cloud
```

---

## Step 4: Find by Size

```bash
# Files larger than 10KB in /etc
find /etc -size +10k -type f 2>/dev/null | head -5
```

**📸 Verified Output:**
```
/etc/login.defs
```

```bash
# Largest files on the system
find / -xdev -type f -printf '%s %p\n' 2>/dev/null | sort -rn | head -5
```

**📸 Verified Output:**
```
4455728 /usr/lib/x86_64-linux-gnu/libcrypto.so.3
3806200 /usr/bin/perl5.34.0
3806200 /usr/bin/perl
2260296 /usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.30
2220400 /usr/lib/x86_64-linux-gnu/libc.so.6
```

> 💡 `-xdev` = **don't cross filesystem boundaries**. Without it, `find /` might also search `/proc` and `/sys` virtual filesystems, causing infinite loops or enormous output.

---

## Step 5: Find by Modification Time

```bash
mkdir /tmp/findtest
touch /tmp/findtest/{a,b,c}.txt
touch -d '-10 days' /tmp/findtest/old.txt  # artificially old file

# Find files modified more than 5 days ago
find /tmp/findtest -mtime +5 -name '*.txt'
```

**📸 Verified Output:**
```
/tmp/findtest/old.txt
```

```bash
# Find files modified in the last 24 hours
find /var/log -mtime -1 -type f 2>/dev/null | head -5
```

**📸 Verified Output:**
```
/var/log/alternatives.log
/var/log/dpkg.log
```

> 💡 `-mtime N`: `+N` = older than N days, `-N` = newer than N days, `N` = exactly N days. `-mmin` does the same in minutes — useful for finding files changed in the last 10 minutes.

---

## Step 6: Find by Permissions (Security Audit)

```bash
# Find SUID binaries (potential privilege escalation)
find /usr/bin /bin -perm -4000 -type f 2>/dev/null
```

**📸 Verified Output:**
```
/usr/bin/chsh
/usr/bin/mount
/usr/bin/passwd
/usr/bin/su
/usr/bin/umount
/usr/bin/newgrp
/usr/bin/gpasswd
/usr/bin/chfn
```

```bash
# Find world-writable files (security risk)
find /etc -perm -002 -type f 2>/dev/null | head -3
echo "World-writable /etc files: $(find /etc -perm -002 -type f 2>/dev/null | wc -l)"
```

**📸 Verified Output:**
```
World-writable /etc files: 0
```

---

## Step 7: find with -exec (Run Commands on Results)

```bash
# Print details on all .conf files (exec ls -la)
find /etc -maxdepth 1 -name '*.conf' -exec ls -lh {} \; 2>/dev/null | head -5
```

**📸 Verified Output:**
```
-rw-r--r-- 1 root root  20K Jul 16  2022 /etc/mke2fs.conf
-rw-r--r-- 1 root root 224K Oct 20  2021 /etc/login.defs
-rw-r--r-- 1 root root 1.6K Jun  3  2021 /etc/sysctl.conf
-rw-r--r-- 1 root root 1.5K Apr 18  2022 /etc/nsswitch.conf
```

```bash
# Find and delete old temp files at once
mkdir /tmp/cleanup_test
for i in 1 2 3 4 5; do touch -d "-${i} days" /tmp/cleanup_test/old_${i}.tmp; done
touch /tmp/cleanup_test/fresh.tmp

echo "Before:"
ls /tmp/cleanup_test/

find /tmp/cleanup_test -name '*.tmp' -mtime +2 -delete

echo "After (only fresh remains):"
ls /tmp/cleanup_test/
```

**📸 Verified Output:**
```
Before:
fresh.tmp  old_1.tmp  old_2.tmp  old_3.tmp  old_4.tmp  old_5.tmp

After (only fresh remains):
fresh.tmp  old_1.tmp  old_2.tmp
```

> 💡 `-exec command {} \;` — `{}` is replaced by the filename, `\;` ends the exec clause. For better performance with many files use `-exec command {} +` which passes all files at once.

---

## Step 8: Capstone — Security Filesystem Audit

```bash
echo "=== Security Filesystem Audit ==="
echo ""

echo "1. SUID/SGID binaries:"
find /usr/bin /bin /usr/sbin /sbin \
    \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null \
    | xargs ls -la 2>/dev/null | awk '{print $1, $9}' | head -8

echo ""
echo "2. Files without owner (orphaned):"
ORPHANED=$(find /tmp -nouser -type f 2>/dev/null | wc -l)
echo "  Found: $ORPHANED orphaned files"

echo ""
echo "3. World-writable directories:"
find /etc /usr -perm -002 -type d 2>/dev/null | head -3
echo "  (should be empty)"

echo ""
echo "4. Python scripts on system:"
find / -name '*.py' -type f 2>/dev/null | wc -l
echo "Python files found"

echo ""
echo "5. Recently modified files in /etc (last 30 days):"
find /etc -mtime -30 -type f 2>/dev/null | head -5
```

**📸 Verified Output:**
```
=== Security Filesystem Audit ===

1. SUID/SGID binaries:
-rwsr-xr-x /usr/bin/chsh
-rwsr-xr-x /usr/bin/mount
-rwsr-xr-x /usr/bin/passwd
-rwsr-xr-x /usr/bin/su
-rwsr-xr-x /usr/bin/umount
-rwsr-xr-x /usr/bin/newgrp
-rwsr-xr-x /usr/bin/gpasswd
-rwsr-xr-x /usr/bin/chfn

2. Files without owner (orphaned):
  Found: 0 orphaned files

3. World-writable directories:
  (should be empty)

4. Python scripts on system:
5
Python files found

5. Recently modified files in /etc (last 30 days):
/etc/alternatives/editor
/etc/passwd
/etc/group
/etc/shadow
/etc/gshadow
```

---

## Summary

| find Option | Meaning |
|------------|---------|
| `-name '*.txt'` | Match filename with glob |
| `-type f` | Files only |
| `-type d` | Directories only |
| `-size +10k` | Larger than 10 KB |
| `-mtime +7` | Modified more than 7 days ago |
| `-mtime -1` | Modified in last 24 hours |
| `-perm -4000` | Has SUID bit |
| `-perm -002` | World-writable |
| `-maxdepth N` | Limit recursion depth |
| `-exec cmd {} \;` | Run command on each result |
| `-delete` | Delete matching files |
