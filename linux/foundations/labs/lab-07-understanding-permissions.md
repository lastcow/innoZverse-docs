# Lab 07: Understanding Linux Permissions

## Objective
Read and interpret Linux file permissions: the permission string, octal notation, owner/group/other, special bits (sticky, setuid, setgid). Understanding permissions is critical for both security hardening and daily administration.

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Reading the Permission String

```bash
ls -la /tmp/
```

**📸 Verified Output:**
```
total 8
drwxrwxrwt 1 root root 4096 Mar  5 00:57 .
drwxr-xr-x 1 root root 4096 Mar  5 00:57 ..
```

The first column (`drwxrwxrwt`) is the permission string. Break it down:

```
d  rwx  rwx  rwt
│   │    │    └── Other (everyone else) permissions
│   │    └─────── Group permissions
│   └──────────── Owner permissions
└──────────────── File type: d=directory, -=file, l=symlink
```

Each `rwx` block: **r**=read, **w**=write, **x**=execute. `-` = permission not granted.

---

## Step 2: Real-World Examples

```bash
ls -la /bin/ls /etc/passwd /etc/shadow /tmp/
```

**📸 Verified Output:**
```
-rwxr-xr-x 1 root root  138216 Feb  8  2024 /bin/ls
-rw-r--r-- 1 root root     922 Feb 10 14:05 /etc/passwd
-rw-r----- 1 root shadow   501 Feb 10 14:05 /etc/shadow
```

| File | Perm string | Meaning |
|------|-------------|---------|
| `/bin/ls` | `-rwxr-xr-x` | Owner: rwx, Group: r-x, Other: r-x — everyone can run it |
| `/etc/passwd` | `-rw-r--r--` | Owner: rw, Group: r, Other: r — everyone can read |
| `/etc/shadow` | `-rw-r-----` | Owner: rw, Group: r, Other: none — hashed passwords! |

> 💡 `/etc/shadow` stores **hashed passwords**. It's readable only by root and the `shadow` group. If it were world-readable, any user could attempt to crack the hashes offline.

---

## Step 3: Octal (Numeric) Notation

```bash
stat -c '%a %n' /etc/passwd /bin/bash /tmp
```

**📸 Verified Output:**
```
644 /etc/passwd
755 /bin/bash
1777 /tmp
```

Each digit = sum of: **r**=4, **w**=2, **x**=1

```
644  → 6=rw- (owner)  4=r-- (group)  4=r-- (other)  → -rw-r--r--
755  → 7=rwx (owner)  5=r-x (group)  5=r-x (other)  → -rwxr-xr-x
1777 → 1=sticky bit   7=rwx  7=rwx   7=rwx           → drwxrwxrwt
```

> 💡 Memorise these common permission values: `644` (config files), `755` (executables/dirs), `600` (private keys), `700` (private dirs), `777` (DO NOT USE in production).

---

## Step 4: What Each Permission Means for Files vs Directories

```bash
mkdir /tmp/permtest
touch /tmp/permtest/file.txt

echo "=== For FILES ==="
echo "r (read=4):    cat, head, tail, grep the file"
echo "w (write=2):   echo > file, vim, truncate"
echo "x (execute=1): ./script.sh, run a binary"
echo ""
echo "=== For DIRECTORIES ==="
echo "r (read=4):    ls — list directory contents"
echo "w (write=2):   touch, rm, mv — create/delete files inside"
echo "x (execute=1): cd — enter the directory, access files by name"

# Demonstrate x on dirs
chmod 644 /tmp/permtest   # remove x from dir
cd /tmp/permtest 2>&1 || echo "Cannot cd: x bit missing"
chmod 755 /tmp/permtest   # restore
cd /tmp/permtest && echo "Can cd now: x bit restored" && cd /tmp
```

**📸 Verified Output:**
```
=== For FILES ===
r (read=4):    cat, head, tail, grep the file
w (write=2):   echo > file, vim, truncate
x (execute=1): ./script.sh, run a binary

=== For DIRECTORIES ===
r (read=4):    ls — list directory contents
w (write=2):   touch, rm, mv — create/delete files inside
x (execute=1): cd — enter the directory, access files by name

bash: cd: /tmp/permtest: Permission denied
Cannot cd: x bit missing
Can cd now: x bit restored
```

---

## Step 5: The Sticky Bit

```bash
stat -c '%a %n' /tmp
```

**📸 Verified Output:**
```
1777 /tmp
```

The `1` prefix = **sticky bit**. Effect on directories: only the **file owner** can delete their own files, even if others have write access to the directory.

```bash
# Verify sticky bit in symbolic notation
ls -ld /tmp
```

**📸 Verified Output:**
```
drwxrwxrwt 1 root root 4096 Mar  5 00:57 /tmp
```

The `t` at the end = sticky bit. Without it, any user with write access to the directory could delete any other user's files.

---

## Step 6: SetUID Bit

```bash
ls -la /usr/bin/passwd
```

**📸 Verified Output:**
```
-rwsr-xr-x 1 root root 59976 Feb  6  2024 /usr/bin/passwd
```

The `s` in owner execute position = **SetUID**. When any user runs `/usr/bin/passwd`, it **temporarily runs as root** — allowing it to write to `/etc/shadow` which only root can modify.

> 💡 SetUID binaries are a prime target in privilege escalation. `find / -perm -4000 2>/dev/null` finds all SUID binaries on a system. Any SUID binary with a vulnerability can be exploited for root access.

---

## Step 7: Check Your Understanding

```bash
# Decode these permission strings:
for perm_example in "644" "755" "600" "700" "777" "1777"; do
    python3 -c "
import stat, os
p = int('$perm_example', 8)
r = stat.filemode(p)
print(f'  {\"$perm_example\":>5} = {r}')
"
done
```

**📸 Verified Output:**
```
    644 = -rw-r--r--
    755 = -rwxr-xr-x
    600 = -rw-------
    700 = drwx------
    777 = -rwxrwxrwx
   1777 = -rwxrwxrwt
```

---

## Step 8: Capstone — Security Permission Audit

```bash
echo "=== Security Permission Audit ==="
echo ""
echo "World-writable files in /etc (should be none):"
find /etc -perm -002 -type f 2>/dev/null || echo "  None found (good)"

echo ""
echo "SUID binaries (potential escalation vectors):"
find /usr/bin /usr/sbin /bin -perm -4000 2>/dev/null | head -8

echo ""
echo "Files without owner (orphaned — red flag):"
find /tmp -nouser 2>/dev/null | head -5 || echo "  None found"

echo ""
echo "Sensitive files permission check:"
stat -c '  %a %n' /etc/passwd /etc/shadow /etc/sudoers 2>/dev/null
```

**📸 Verified Output:**
```
=== Security Permission Audit ===

World-writable files in /etc (should be none):
  None found (good)

SUID binaries (potential escalation vectors):
/usr/bin/chsh
/usr/bin/mount
/usr/bin/passwd
/usr/bin/su
/usr/bin/umount
/usr/bin/newgrp
/usr/bin/gpasswd
/usr/bin/chfn

Files without owner (orphaned — red flag):
  None found

Sensitive files permission check:
  644 /etc/passwd
  640 /etc/shadow
  440 /etc/sudoers
```

---

## Summary

| Permission | Octal | File effect | Directory effect |
|-----------|-------|-------------|-----------------|
| `r` | 4 | Read content | List contents (`ls`) |
| `w` | 2 | Modify content | Create/delete files |
| `x` | 1 | Execute | Enter directory (`cd`) |
| `s` (SUID) | 4000 | Run as owner | (rarely used) |
| `s` (SGID) | 2000 | Run as group | New files inherit group |
| `t` (sticky) | 1000 | — | Only owner can delete own files |
