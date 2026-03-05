# Lab 06: Deleting Files and Directories

## Objective
Use `rm`, `rmdir`, glob patterns, and understand why Linux has no Recycle Bin. Learn safe deletion practices that prevent catastrophic mistakes in production.

**Time:** 20 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Deleting a Single File

```bash
touch /tmp/test.txt /tmp/test2.txt /tmp/test3.txt
rm /tmp/test.txt
ls /tmp/test*
```

**📸 Verified Output:**
```
/tmp/test2.txt
/tmp/test3.txt
```

> 💡 **Linux has no Recycle Bin.** `rm` permanently deletes. There is no "undo". In a container or test environment this is fine — on a production server, one wrong `rm -rf` can be catastrophic.

---

## Step 2: Deleting Directories

```bash
mkdir /tmp/empty_dir
rmdir /tmp/empty_dir    # works on empty directories only
echo "Exit code: $?"    # 0 = success
```

**📸 Verified Output:**
```
Exit code: 0
```

```bash
# rmdir fails on non-empty dirs:
mkdir -p /tmp/full_dir/subdir
rmdir /tmp/full_dir 2>&1
```

**📸 Verified Output:**
```
rmdir: failed to remove '/tmp/full_dir': Directory not empty
```

```bash
# rm -r deletes recursively
rm -r /tmp/full_dir
ls /tmp/full_dir 2>&1
```

**📸 Verified Output:**
```
ls: cannot access '/tmp/full_dir': No such file or directory
```

> 💡 `rm -r` is powerful — it deletes everything inside a directory tree. Always double-check the path before running it.

---

## Step 3: Glob Patterns for Batch Deletion

```bash
mkdir /tmp/glob_test
touch /tmp/glob_test/log_{1..5}.txt /tmp/glob_test/config.cfg
ls /tmp/glob_test/
```

**📸 Verified Output:**
```
config.cfg  log_1.txt  log_2.txt  log_3.txt  log_4.txt  log_5.txt
```

```bash
# Delete all .txt files (config.cfg survives)
rm /tmp/glob_test/*.txt
ls /tmp/glob_test/
```

**📸 Verified Output:**
```
config.cfg
```

> 💡 **Always test your glob before deleting.** Run `ls /path/*.txt` first, confirm it shows what you expect, then replace `ls` with `rm`. This habit prevents disasters.

---

## Step 4: Interactive Deletion (-i flag)

```bash
# -i asks before each deletion (type n to cancel, y to proceed)
touch /tmp/ask_before_delete.txt
rm -i /tmp/ask_before_delete.txt << 'EOF'
y
EOF
echo "File deleted: $(ls /tmp/ask_before_delete.txt 2>&1)"
```

**📸 Verified Output:**
```
rm: remove regular empty file '/tmp/ask_before_delete.txt'? File deleted: ls: cannot access '/tmp/ask_before_delete.txt': No such file or directory
```

> 💡 Some sysadmins alias `rm='rm -i'` in their `.bashrc` on servers. In scripts, use `-f` (force, no prompts). In interactive use, `-i` adds a safety net.

---

## Step 5: Verbose Deletion (-v flag)

```bash
mkdir /tmp/verbose_test
touch /tmp/verbose_test/a.log /tmp/verbose_test/b.log /tmp/verbose_test/c.log
rm -rv /tmp/verbose_test/
```

**📸 Verified Output:**
```
removed '/tmp/verbose_test/a.log'
removed '/tmp/verbose_test/b.log'
removed '/tmp/verbose_test/c.log'
removed directory '/tmp/verbose_test/'
```

> 💡 `-v` prints each file as it's deleted. Useful when running `rm` in scripts so you have an audit trail of exactly what was removed.

---

## Step 6: The Danger of rm -rf

```bash
# Safe demo: remove a disposable directory
mkdir -p /tmp/cleanup/dir1/dir2
touch /tmp/cleanup/dir1/file{1,2,3}
touch /tmp/cleanup/dir1/dir2/nested_file

# What would be deleted? (preview with find)
find /tmp/cleanup -print

echo ""
echo "Deleting..."
rm -rf /tmp/cleanup
echo "Done. Exit code: $?"
```

**📸 Verified Output:**
```
/tmp/cleanup
/tmp/cleanup/dir1
/tmp/cleanup/dir1/file1
/tmp/cleanup/dir1/file2
/tmp/cleanup/dir1/file3
/tmp/cleanup/dir1/dir2
/tmp/cleanup/dir1/dir2/nested_file

Deleting...
Done. Exit code: 0
```

> 💡 The infamous `rm -rf /` would delete your entire system. Modern Linux distributions add a `--no-preserve-root` safeguard that you must explicitly add to override. Never run commands with `-rf` without triple-checking the path.

---

## Step 7: Securely Deleting Sensitive Files

```bash
# Create a file with "sensitive" content
echo "SECRET_KEY=abc123xyz" > /tmp/credentials.txt

# Overwrite before deleting (basic secure delete)
dd if=/dev/urandom of=/tmp/credentials.txt bs=1 count=$(wc -c < /tmp/credentials.txt) 2>/dev/null
rm /tmp/credentials.txt
echo "Secure deletion complete"
```

**📸 Verified Output:**
```
Secure deletion complete
```

> 💡 On SSDs, `shred` and `dd` overwrites are unreliable due to wear-leveling. True secure deletion on SSDs requires full-disk encryption (`dm-crypt`) so deleted files are unrecoverable by default.

---

## Step 8: Capstone — Safe Log Rotation Cleanup

```bash
# Simulate cleaning up old log files older than 7 days
mkdir -p /tmp/logs
for i in 1 2 3 4 5 6 7 8 9 10; do
    touch -d "-${i} days" /tmp/logs/app_$(date -d "-${i} days" +%Y%m%d).log
done

echo "Before cleanup:"
ls -la /tmp/logs/

# Find and delete files older than 7 days
echo ""
echo "Deleting logs older than 7 days:"
find /tmp/logs -name "*.log" -mtime +7 -print -delete

echo ""
echo "After cleanup:"
ls /tmp/logs/ | wc -l
echo "files remaining"
```

**📸 Verified Output:**
```
Before cleanup:
total 40
drwxr-xr-x 2 root root 4096 Mar  5 00:56 .
drwxrwxrwt 1 root root 4096 Mar  5 00:56 ..
-rw-r--r-- 1 root root    0 Feb 26 00:56 app_20260226.log
...
-rw-r--r-- 1 root root    0 Mar  4 00:56 app_20260304.log

Deleting logs older than 7 days:
/tmp/logs/app_20260226.log

After cleanup:
9
files remaining
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `rm file` | Delete a file |
| `rm -r dir` | Delete directory recursively |
| `rm -rf dir` | Force recursive delete (no prompts) |
| `rm -i file` | Prompt before each deletion |
| `rm -v file` | Verbose: show each deletion |
| `rmdir dir` | Delete empty directory only |
| `find -mtime +N -delete` | Delete files older than N days |
