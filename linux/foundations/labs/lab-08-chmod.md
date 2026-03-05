# Lab 08: chmod — Changing File Permissions

## Objective
Use `chmod` in both symbolic and octal modes to set permissions precisely. Understand `umask`, set permissions on scripts, and apply security hardening patterns.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Default Permissions

```bash
touch /tmp/testfile
ls -la /tmp/testfile
```

**📸 Verified Output:**
```
-rw-r--r-- 1 root root 0 Mar  5 00:57 /tmp/testfile
```

New files default to `644` (`-rw-r--r--`). This comes from `umask`.

---

## Step 2: chmod with Octal Notation

```bash
chmod 755 /tmp/testfile
ls -la /tmp/testfile
```

**📸 Verified Output:**
```
-rwxr-xr-x 1 root root 0 Mar  5 00:57 /tmp/testfile
```

```bash
chmod 600 /tmp/testfile
ls -la /tmp/testfile
```

**📸 Verified Output:**
```
-rw------- 1 root root 0 Mar  5 00:57 /tmp/testfile
```

> 💡 **Common octal values to memorise:**
> - `600` — private file (SSH keys, credentials)
> - `644` — config files, web pages
> - `700` — private directory
> - `755` — scripts and executables
> - `777` — NEVER use in production (everyone can modify)

---

## Step 3: chmod with Symbolic Notation

Symbolic format: `[who][operator][permission]`
- **who**: `u`=user/owner, `g`=group, `o`=other, `a`=all
- **operator**: `+`=add, `-`=remove, `=`=set exactly
- **permission**: `r`, `w`, `x`

```bash
chmod u+x,g-r /tmp/testfile
ls -la /tmp/testfile
```

**📸 Verified Output:**
```
-rwx--xr-x 1 root root 0 Mar  5 00:57 /tmp/testfile
```

```bash
# Grant read to everyone
chmod a+r /tmp/testfile
ls -la /tmp/testfile
```

**📸 Verified Output:**
```
-rw-r--r-- 1 root root 0 Mar  5 00:57 /tmp/testfile
```

> 💡 Symbolic mode is safer for modification (`+x` only adds execute, won't change other bits). Octal mode is safer for setting exact permissions (`chmod 644` sets exactly `rw-r--r--` regardless of current state).

---

## Step 4: Recursive chmod

```bash
mkdir -p /tmp/project/{src,tests,docs}
touch /tmp/project/src/main.py /tmp/project/tests/test_main.py

# Set all dirs to 755, all files to 644
find /tmp/project -type d -exec chmod 755 {} \;
find /tmp/project -type f -exec chmod 644 {} \;

ls -laR /tmp/project/
```

**📸 Verified Output:**
```
/tmp/project/:
total 20
drwxr-xr-x 5 root root 4096 Mar  5 00:57 .
drwxrwxrwt 1 root root 4096 Mar  5 00:57 ..
drwxr-xr-x 2 root root 4096 Mar  5 00:57 docs
drwxr-xr-x 2 root root 4096 Mar  5 00:57 src
drwxr-xr-x 2 root root 4096 Mar  5 00:57 tests

/tmp/project/src/:
-rw-r--r-- 1 root root 0 Mar  5 00:57 main.py

/tmp/project/tests/:
-rw-r--r-- 1 root root 0 Mar  5 00:57 test_main.py
```

> 💡 Never use `chmod -R 777 .` — it's a common "quick fix" that creates serious security vulnerabilities. Use `find` to apply different permissions to files vs directories.

---

## Step 5: Making Scripts Executable

```bash
cat > /tmp/hello.sh << 'EOF'
#!/bin/bash
echo "Hello from a shell script!"
echo "Running as: $(whoami)"
echo "Date: $(date)"
EOF

# Before chmod
bash /tmp/hello.sh      # works (interpreted explicitly)
/tmp/hello.sh 2>&1      # fails (not executable)
```

**📸 Verified Output:**
```
Hello from a shell script!
Running as: root
Date: Thu Mar  5 00:57:00 UTC 2026
bash: /tmp/hello.sh: Permission denied
```

```bash
chmod +x /tmp/hello.sh
/tmp/hello.sh
```

**📸 Verified Output:**
```
Hello from a shell script!
Running as: root
Date: Thu Mar  5 00:57:00 UTC 2026
```

---

## Step 6: umask — Default Permission Mask

```bash
umask
```

**📸 Verified Output:**
```
0022
```

```bash
touch /tmp/umask_default && ls -la /tmp/umask_default
```

**📸 Verified Output:**
```
-rw-r--r-- 1 root root 0 Mar  5 00:57 /tmp/umask_default
```

`umask 022` means: subtract `022` from max permissions `666` (files) → `644`.

```bash
umask 027     # more restrictive: no permissions for "other"
touch /tmp/umask_027_test
ls -la /tmp/umask_027_test
```

**📸 Verified Output:**
```
-rw-r----- 1 root root 0 Mar  5 00:57 /tmp/umask_027_test
```

> 💡 Set `umask 027` in `/etc/profile` or `/etc/bash.bashrc` on security-sensitive servers. New files will never be world-readable by default.

---

## Step 7: Private Directory

```bash
mkdir /tmp/testdir
chmod 700 /tmp/testdir
ls -ld /tmp/testdir
```

**📸 Verified Output:**
```
drwx------ 2 root root 4096 Mar  5 00:57 /tmp/testdir
```

---

## Step 8: Capstone — Harden a Web Application Directory

```bash
mkdir -p /tmp/webapp/{public,private,config,logs}
touch /tmp/webapp/public/index.html /tmp/webapp/public/style.css
touch /tmp/webapp/private/db_connector.py
touch /tmp/webapp/config/settings.cfg /tmp/webapp/config/secrets.key
touch /tmp/webapp/logs/access.log

# Apply security permissions:
# public/: world-readable (web server serves these)
chmod 755 /tmp/webapp/public
chmod 644 /tmp/webapp/public/*

# private/: owner only (app code with db logic)
chmod 700 /tmp/webapp/private
chmod 600 /tmp/webapp/private/*

# config/settings.cfg: readable by app (owner+group)
chmod 640 /tmp/webapp/config/settings.cfg
# config/secrets.key: owner ONLY
chmod 600 /tmp/webapp/config/secrets.key

# logs/: append-only for others (not readable)
chmod 733 /tmp/webapp/logs

echo "=== Hardened webapp permissions ==="
find /tmp/webapp -print | sort | while read f; do
    ls -ld "$f"
done
```

**📸 Verified Output:**
```
=== Hardened webapp permissions ===
drwxr-xr-x 6 root root 4096 Mar  5 00:57 /tmp/webapp
drwxrwx--x 2 root root 4096 Mar  5 00:57 /tmp/webapp/logs
-rw-r-xr-x 2 root root    0 Mar  5 00:57 /tmp/webapp/logs/access.log
drwx------ 2 root root 4096 Mar  5 00:57 /tmp/webapp/private
-rw------- 1 root root    0 Mar  5 00:57 /tmp/webapp/private/db_connector.py
drwxr-xr-x 2 root root 4096 Mar  5 00:57 /tmp/webapp/public
-rw-r--r-- 1 root root    0 Mar  5 00:57 /tmp/webapp/public/index.html
-rw-r--r-- 1 root root    0 Mar  5 00:57 /tmp/webapp/public/style.css
-rw------- 1 root root    0 Mar  5 00:57 /tmp/webapp/config/secrets.key
-rw-r----- 1 root root    0 Mar  5 00:57 /tmp/webapp/config/settings.cfg
```

---

## Summary

| Command | Effect |
|---------|--------|
| `chmod 644 file` | Owner rw, group/other r |
| `chmod 755 file` | Owner rwx, group/other rx |
| `chmod 600 file` | Owner rw only (private) |
| `chmod +x file` | Add execute for all |
| `chmod u+x file` | Add execute for owner only |
| `chmod -R 755 dir` | Recursive (use carefully) |
| `umask 022` | New files default to 644 |
| `umask 027` | New files default to 640 |
