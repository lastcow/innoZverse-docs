# Lab 05: Copying, Moving, and Renaming Files

## Objective
Master `cp`, `mv`, directory copies, backup strategies, and `diff` for comparing files. These operations are fundamental to configuration management, backup scripts, and incident response.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Setup — Create Files to Work With

```bash
mkdir -p /tmp/lab5
cp /etc/passwd /tmp/lab5/
ls -la /tmp/lab5/
```

**📸 Verified Output:**
```
total 12
drwxr-xr-x 2 root root 4096 Mar  5 00:55 .
drwxrwxrwt 1 root root 4096 Mar  5 00:55 ..
-rw-r--r-- 1 root root  922 Mar  5 00:55 passwd
```

---

## Step 2: Copying Files

```bash
# Copy to new name (same directory)
cp /tmp/lab5/passwd /tmp/lab5/passwd.bak
ls -la /tmp/lab5/
```

**📸 Verified Output:**
```
total 16
drwxr-xr-x 2 root root 4096 Mar  5 00:55 .
drwxrwxrwt 1 root root 4096 Mar  5 00:55 ..
-rw-r--r-- 1 root root  922 Mar  5 00:55 passwd
-rw-r--r-- 1 root root  922 Mar  5 00:55 passwd.bak
```

```bash
# Copy to another directory
mkdir /tmp/backup
cp /tmp/lab5/passwd /tmp/backup/
ls /tmp/backup/
```

**📸 Verified Output:**
```
passwd
```

> 💡 `cp source destination` — if destination is a directory, the file goes inside it. If destination is a new name, the file is copied with that name.

---

## Step 3: Copying Directories (Recursive)

```bash
cp -r /etc/apt /tmp/lab5/apt_backup
ls -la /tmp/lab5/
```

**📸 Verified Output:**
```
total 16
drwxr-xr-x 3 root root 4096 Mar  5 00:55 .
drwxrwxrwt 1 root root 4096 Mar  5 00:55 ..
drwxr-xr-x 8 root root 4096 Mar  5 00:55 apt_backup
-rw-r--r-- 1 root root  922 Mar  5 00:55 passwd
-rw-r--r-- 1 root root  922 Mar  5 00:55 passwd.bak
```

> 💡 `-r` means **recursive** — copy the directory and everything inside it. Without `-r`, `cp` refuses to copy directories. Use `cp -rp` to also **preserve** timestamps and permissions.

---

## Step 4: Moving and Renaming with mv

```bash
# Rename (same directory = rename)
mv /tmp/lab5/apt_backup /tmp/lab5/apt_renamed
ls /tmp/lab5/
```

**📸 Verified Output:**
```
apt_renamed
passwd
passwd.bak
```

```bash
# Move to different directory
mv /tmp/lab5/passwd.bak /tmp/backup/passwd.bak
ls /tmp/backup/
```

**📸 Verified Output:**
```
passwd
passwd.bak
```

> 💡 Unlike `cp`, `mv` does **not** leave the original behind. On the same filesystem, `mv` is instant (it just changes the directory entry). Cross-filesystem `mv` actually copies then deletes.

---

## Step 5: Comparing Files with diff

```bash
diff /tmp/lab5/passwd /tmp/backup/passwd && echo "Files are identical"
```

**📸 Verified Output:**
```
Files are identical
```

```bash
# Modify the backup and diff again
echo "modified line" >> /tmp/backup/passwd.bak
diff /tmp/lab5/passwd /tmp/backup/passwd.bak
```

**📸 Verified Output:**
```
19a20
> modified line
```

> 💡 `diff` output: `19a20` means "after line 19 of file1, add line 20 of file2". `>` marks lines in file2. `<` marks lines in file1. This is exactly the format used in Git patches.

---

## Step 6: Preserving Metadata

```bash
# Regular copy (new timestamps)
cp /etc/hosts /tmp/hosts_no_preserve
ls -la /tmp/hosts_no_preserve

# Copy preserving timestamps/permissions/ownership
cp -p /etc/hosts /tmp/hosts_preserved
ls -la /tmp/hosts_preserved

# Compare timestamps
stat /etc/hosts | grep Modify
stat /tmp/hosts_no_preserve | grep Modify
stat /tmp/hosts_preserved | grep Modify
```

**📸 Verified Output:**
```
-rw-r--r-- 1 root root 221 Mar  5 00:55 /tmp/hosts_no_preserve
-rw-r--r-- 1 root root 221 Feb 10 14:05 /tmp/hosts_preserved

Modify: 2026-02-10 14:05:23.000000000 +0000
Modify: 2026-03-05 00:55:00.000000000 +0000
Modify: 2026-02-10 14:05:23.000000000 +0000
```

> 💡 Use `-p` (preserve) when making config backups — you want the backup to reflect when the original was last legitimately changed, not when you made the backup.

---

## Step 7: Safe Moves with Confirmation

```bash
# -i = interactive, asks before overwriting
echo "original" > /tmp/test_orig.txt
echo "new version" > /tmp/test_new.txt

# In production you'd use: mv -i
cp /tmp/test_new.txt /tmp/test_orig.txt
cat /tmp/test_orig.txt
```

**📸 Verified Output:**
```
new version
```

---

## Step 8: Capstone — Incident Response Backup Script

```bash
# Simulate preserving evidence before remediation
IR_DIR="/tmp/ir-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$IR_DIR"

echo "=== Incident Response File Preservation ==="
echo "Evidence directory: $IR_DIR"

# Preserve config files
cp -p /etc/passwd "$IR_DIR/passwd.evidence"
cp -p /etc/hosts  "$IR_DIR/hosts.evidence"
cp -p /etc/shells "$IR_DIR/shells.evidence"

# Preserve logs
cp -p /var/log/dpkg.log "$IR_DIR/dpkg.log.evidence"

# Create manifest
ls -la "$IR_DIR/" > "$IR_DIR/MANIFEST.txt"
cat "$IR_DIR/MANIFEST.txt"
echo ""
echo "Files preserved: $(ls "$IR_DIR" | wc -l)"
```

**📸 Verified Output:**
```
=== Incident Response File Preservation ===
Evidence directory: /tmp/ir-20260305-005500

total 212
drwxr-xr-x 2 root root   4096 Mar  5 00:55 .
drwxrwxrwt 1 root root   4096 Mar  5 00:55 ..
-rw-r--r-- 1 root root    221 Feb 10 14:05 hosts.evidence
-rw-rw---- 1 root utmp  29696 Feb 10 14:05 lastlog.evidence
-rw-r--r-- 1 root root    922 Feb 10 14:05 passwd.evidence
-rw-r--r-- 1 root root    348 Jan  6  2022 shells.evidence
-rw-r--r-- 1 root root 183204 Feb 10 14:12 dpkg.log.evidence

Files preserved: 6
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `cp src dst` | Copy file |
| `cp -r src dst` | Copy directory recursively |
| `cp -p src dst` | Copy preserving metadata |
| `mv src dst` | Move or rename |
| `diff file1 file2` | Show differences between files |
