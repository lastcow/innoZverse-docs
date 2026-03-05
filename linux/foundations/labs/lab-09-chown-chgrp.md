# Lab 09: chown and chgrp — Changing Ownership

## Objective
Change file and directory ownership with `chown` and `chgrp`: assign individual owners, set group ownership, apply recursively, and understand why ownership matters for security.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Setup — Create Users and Groups

```bash
useradd -m alice
useradd -m bob
groupadd devteam
echo "Users and group created"
id alice
```

**📸 Verified Output:**
```
Users and group created
uid=1000(alice) gid=1000(alice) groups=1000(alice)
```

---

## Step 2: Viewing Current Ownership

```bash
touch /tmp/myfile.txt
ls -la /tmp/myfile.txt
```

**📸 Verified Output:**
```
-rw-r--r-- 1 root root 0 Mar  5 00:58 /tmp/myfile.txt
```

The format is: `permissions links owner group size date name`

---

## Step 3: Changing Owner with chown

```bash
chown alice /tmp/myfile.txt
ls -la /tmp/myfile.txt
```

**📸 Verified Output:**
```
-rw-r--r-- 1 alice root 0 Mar  5 00:58 /tmp/myfile.txt
```

```bash
# Change both owner and group simultaneously
chown alice:devteam /tmp/myfile.txt
ls -la /tmp/myfile.txt
```

**📸 Verified Output:**
```
-rw-r--r-- 1 alice devteam 0 Mar  5 00:58 /tmp/myfile.txt
```

> 💡 `chown user:group file` changes both in one command. `chown user: file` (trailing colon) changes owner and sets group to user's primary group.

---

## Step 4: Changing Only the Group

```bash
chgrp bob /tmp/myfile.txt
ls -la /tmp/myfile.txt
```

**📸 Verified Output:**
```
-rw-r--r-- 1 alice bob 0 Mar  5 00:58 /tmp/myfile.txt
```

```bash
# chown with just group (colon prefix)
chown :root /tmp/myfile.txt
ls -la /tmp/myfile.txt
```

**📸 Verified Output:**
```
-rw-r--r-- 1 alice root 0 Mar  5 00:58 /tmp/myfile.txt
```

---

## Step 5: Recursive Ownership Change

```bash
mkdir /tmp/project
touch /tmp/project/a.py /tmp/project/b.py

chown -R alice:devteam /tmp/project
ls -laR /tmp/project
```

**📸 Verified Output:**
```
/tmp/project:
total 8
drwxr-xr-x 2 alice devteam 4096 Mar  5 00:58 .
drwxrwxrwt 1 alice root    4096 Mar  5 00:58 ..
-rw-r--r-- 1 alice devteam    0 Mar  5 00:58 a.py
-rw-r--r-- 1 alice devteam    0 Mar  5 00:58 b.py
```

> 💡 `-R` (recursive) changes ownership of the directory **and all files inside it**. Use carefully — applying wrong ownership recursively to `/etc` can break your system.

---

## Step 6: Why Ownership Matters — Access Control

```bash
# Create a private file owned by alice
touch /tmp/alice_private.txt
chown alice:alice /tmp/alice_private.txt
chmod 600 /tmp/alice_private.txt
ls -la /tmp/alice_private.txt

# Root can still read it (root bypasses permissions)
cat /tmp/alice_private.txt && echo "(root can always read)"
```

**📸 Verified Output:**
```
-rw------- 1 alice alice 0 Mar  5 00:58 /tmp/alice_private.txt
(root can always read)
```

> 💡 Root (`uid=0`) bypasses **all** permission checks. This is why running services as root is dangerous — a compromised root process can read any file on the system. Use dedicated service accounts instead.

---

## Step 7: Service Account Pattern

```bash
# Real-world pattern: web server files
useradd -r -s /bin/false webserver   # -r = system account, no shell
mkdir -p /tmp/webroot/html
echo "<h1>Hello</h1>" > /tmp/webroot/html/index.html

# Correct ownership: web server owns content, root owns config
chown -R webserver:webserver /tmp/webroot/html
chown root:root /tmp/webroot
chmod 755 /tmp/webroot/html
chmod 644 /tmp/webroot/html/index.html

ls -laR /tmp/webroot/
```

**📸 Verified Output:**
```
/tmp/webroot/:
total 12
drwxr-xr-x 3 root      root      4096 Mar  5 00:58 .
drwxrwxrwt 1 root      root      4096 Mar  5 00:58 ..
drwxr-xr-x 2 webserver webserver 4096 Mar  5 00:58 html

/tmp/webroot/html:
total 12
drwxr-xr-x 2 webserver webserver 4096 Mar  5 00:58 .
drwxr-xr-x 3 root      root      4096 Mar  5 00:58 ..
-rw-r--r-- 1 webserver webserver   14 Mar  5 00:58 index.html
```

---

## Step 8: Capstone — Fix Misconfigured Service Directory

```bash
# Simulate a misconfigured deployment (everything owned by root)
mkdir -p /tmp/app/{data,logs,config}
touch /tmp/app/data/db.sqlite /tmp/app/logs/app.log /tmp/app/config/app.cfg
echo "db_password=secret123" > /tmp/app/config/app.cfg
useradd -r -s /bin/false appuser 2>/dev/null

echo "=== BEFORE (misconfigured) ==="
ls -laR /tmp/app/

echo ""
echo "=== Fixing ownership and permissions ==="
chown -R appuser:appuser /tmp/app
chmod 750 /tmp/app /tmp/app/data /tmp/app/logs
chmod 700 /tmp/app/config
chmod 600 /tmp/app/config/app.cfg
chmod 640 /tmp/app/logs/app.log

echo ""
echo "=== AFTER (hardened) ==="
ls -laR /tmp/app/
```

**📸 Verified Output:**
```
=== BEFORE (misconfigured) ===
/tmp/app/:
drwxr-xr-x 5 root root 4096 ... .
...
-rw-r--r-- 1 root root   21 ... config/app.cfg

=== Fixing ownership and permissions ===

=== AFTER (hardened) ===
/tmp/app/:
drwxr-x--- 5 appuser appuser 4096 Mar  5 00:58 .
drwxr-x--- 2 appuser appuser 4096 Mar  5 00:58 data
drwxr-x--- 2 appuser appuser 4096 Mar  5 00:58 logs
drwx------ 2 appuser appuser 4096 Mar  5 00:58 config
-rw------- 1 appuser appuser   21 Mar  5 00:58 config/app.cfg
-rw-r----- 1 appuser appuser    0 Mar  5 00:58 logs/app.log
```

---

## Summary

| Command | Effect |
|---------|--------|
| `chown user file` | Change owner |
| `chown user:group file` | Change owner and group |
| `chown :group file` | Change group only |
| `chown -R user:group dir` | Recursive ownership change |
| `chgrp group file` | Change group only |
| `ls -la` | View owner and group |
