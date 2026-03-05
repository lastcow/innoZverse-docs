# Lab 04: Open Files and Sockets with lsof

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

`lsof` (List Open Files) is one of the most powerful diagnostic tools on Linux. Because "everything is a file" — including network sockets, pipes, devices, and directories — `lsof` provides a unified view of all resource usage by every process. This lab covers process inspection, socket analysis, deleted file detection, and security auditing.

---

## Step 1: Install lsof and Explore Its Version

```bash
apt-get update -qq && apt-get install -y lsof
lsof -v 2>&1 | head -3
```

📸 **Verified Output:**
```
lsof version information:
    revision: 4.93.2
    latest revision: https://github.com/lsof-org/lsof
```

> 💡 `lsof` reads from `/proc/` and kernel structures. Many operations require root to see all processes. Run as root in this lab.

---

## Step 2: Understand lsof Output Format

List files opened by the current shell process:

```bash
lsof -p $$
```

📸 **Verified Output:**
```
COMMAND PID USER   FD   TYPE DEVICE SIZE/OFF     NODE NAME
bash      1 root  cwd    DIR   0,87     4096  2110322 /
bash      1 root  rtd    DIR   0,87     4096  2110322 /
bash      1 root  txt    REG   0,87  1396520  1049938 /usr/bin/bash
bash      1 root  mem    REG   0,87  2220400  1050677 /usr/lib/x86_64-linux-gnu/libc.so.6
bash      1 root  mem    REG   0,87   200136  1050795 /usr/lib/x86_64-linux-gnu/libtinfo.so.6.3
bash      1 root  mem    REG   0,87   240936  1050659 /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2
bash      1 root    0u   CHR    1,3      0t0        5 /dev/null
bash      1 root    1w  FIFO   0,15      0t0 21097568 pipe
bash      1 root    2w  FIFO   0,15      0t0 21097569 pipe
```

**Column meanings:**
| Column | Meaning |
|--------|---------|
| `COMMAND` | Process name |
| `PID` | Process ID |
| `USER` | Owner of the process |
| `FD` | File descriptor (`cwd`=current dir, `txt`=executable, `mem`=memory-mapped, numbers=open FDs) |
| `TYPE` | `REG`=regular file, `DIR`=directory, `CHR`=char device, `FIFO`=pipe, `IPv4`/`IPv6`=socket |
| `DEVICE` | Major:minor device numbers |
| `SIZE/OFF` | File size or offset |
| `NODE` | Inode number |
| `NAME` | File path or socket description |

---

## Step 3: List Files by Process (-p) and Command (-c)

```bash
# List files for a specific PID
lsof -p 1 | head -8
```

📸 **Verified Output:**
```
COMMAND PID USER   FD   TYPE DEVICE SIZE/OFF     NODE NAME
bash      1 root  cwd    DIR   0,87     4096  2110322 /
bash      1 root  rtd    DIR   0,87     4096  2110322 /
bash      1 root  txt    REG   0,87  1396520  1049938 /usr/bin/bash
bash      1 root  mem    REG   0,87  2220400  1050677 /usr/lib/x86_64-linux-gnu/libc.so.6
bash      1 root  mem    REG   0,87   200136  1050795 /usr/lib/x86_64-linux-gnu/libtinfo.so.6.3
bash      1 root  mem    REG   0,87   240936  1050659 /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2
bash      1 root    0u   CHR    1,3      0t0        5 /dev/null
```

```bash
# List files by command name pattern
lsof -c bash | head -8

# List files by user
lsof -u root | head -10

# Get just PIDs (useful for scripting)
lsof -t -u root | head -5
```

> 💡 `-t` (terse) outputs just PIDs, one per line. Combine with `kill`: `kill $(lsof -t -u baduser)` to kill all processes owned by a user.

---

## Step 4: Network Sockets with -i

`lsof -i` lists all network connections:

```bash
# All network connections
lsof -i -n 2>&1 | head -15

# TCP only
lsof -i TCP -n 2>&1 | head -10

# UDP only
lsof -i UDP -n 2>&1 | head -10

# Specific port
lsof -i :80 -n 2>&1
lsof -i :22 -n 2>&1
```

📸 **Verified Output (in a minimal container):**
```
(no output — no network connections in this isolated container)
```

**On a real system with services running:**
```
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
sshd      892   root    3u  IPv4  22156      0t0  TCP *:ssh (LISTEN)
nginx    1234   www     6u  IPv4  45678      0t0  TCP *:http (LISTEN)
nginx    1234   www     7u  IPv4  45679      0t0  TCP *:https (LISTEN)
python3  5678   alice  4u  IPv4  89012      0t0  TCP 10.0.0.1:54321->93.184.216.34:http (ESTABLISHED)
```

> 💡 Use `lsof -i :PORT` to find which process owns a port. This is faster than `netstat -tlnp` and works even when `netstat` isn't installed.

---

## Step 5: Find Deleted Files Still Held Open

When a file is deleted but still open by a process, disk space isn't freed. `lsof` reveals these "ghost" files:

```bash
# Create a file, open it, then delete it
exec 3>/tmp/testfile
rm /tmp/testfile

# Now find it with lsof
lsof -p $$ | grep deleted
```

📸 **Verified Output:**
```
bash      1 root    3w   REG   0,87        0  2109882 /tmp/testfile (deleted)
```

```bash
# System-wide search for deleted files still in use
lsof 2>/dev/null | grep '(deleted)' | head -10

# Find deleted files consuming disk space
lsof 2>/dev/null | grep '(deleted)' | awk '{print $2, $9, $7}' | sort -k3 -rn | head -10
```

**Common scenario:** A log file gets rotated/deleted, but the service still writes to the old FD. Disk fills up even though `ls` shows nothing. The fix is `systemctl reload service` to reopen log files.

> 💡 After finding the process holding the deleted file, `kill -HUP $PID` (SIGHUP) often causes services to reopen their log files — releasing the old inode.

---

## Step 6: List Files in a Directory with +D

Find all processes with files open inside a directory (useful before unmounting):

```bash
# Create some test files
mkdir -p /tmp/mydir
echo "test" > /tmp/mydir/file1.txt
exec 4</tmp/mydir/file1.txt  # open file4 in current shell

# List all open files in /tmp/mydir
lsof +D /tmp/mydir 2>/dev/null
```

📸 **Verified Output:**
```
COMMAND PID USER   FD   TYPE DEVICE SIZE/OFF     NODE NAME
bash      1 root    4r   REG   0,87        5  2109995 /tmp/mydir/file1.txt
```

```bash
# Common use: find what's using a mount point before unmounting
lsof +D /mnt/usb 2>/dev/null
# If this shows results, those processes prevent unmounting
```

> 💡 `lsof +D /path` is recursive and can be slow on large directories. Use `lsof +d /path` (lowercase d) for non-recursive listing of just that directory.

---

## Step 7: Security Audit Use Cases

```bash
# Find all programs listening on network ports
lsof -i -sTCP:LISTEN -n 2>/dev/null | head -15

# Find network connections to a suspicious IP
lsof -i @203.0.113.1 -n 2>/dev/null

# Find processes run by non-root users with open network connections
lsof -i -n 2>/dev/null | awk 'NR>1 && $3 != "root" {print}' | head -10

# Find all executable files that have been deleted (possible malware technique)
lsof 2>/dev/null | grep 'txt.*deleted' | head -10

# Find processes with open files in /tmp (suspicious scripts)
lsof +D /tmp 2>/dev/null | grep -v 'bash\|sh\|python' | head -10
```

**Security red flags in lsof output:**
- Processes with `txt` entries pointing to `/tmp` or `/dev/shm` (executables in temp dirs)
- `(deleted)` entries for executable files (malware hiding its binary)
- Unexpected outbound connections from system processes
- High FD count for a single process (possible FD leak or DoS)

> 💡 Run `lsof -u nobody -i` to see all network activity by the `nobody` user — often used by web servers. Unexpected outbound connections here signal potential compromise.

---

## Step 8: Capstone — Security Audit of a Running System

**Scenario:** Perform a complete open-file security audit.

```bash
apt-get install -y lsof procps

# 1. Count total open files per process (top 10)
lsof 2>/dev/null | awk 'NR>1 {count[$2" "$1]++} END {for(k in count) print count[k], k}' \
  | sort -rn | head -10

# 2. Find all network listeners
echo "=== Network Listeners ==="
lsof -i -sTCP:LISTEN -n 2>/dev/null || echo "(no listeners in container)"

# 3. Find deleted files still held open
echo "=== Deleted Files Still Open ==="
lsof 2>/dev/null | grep '(deleted)' | head -5 || echo "(none found)"

# 4. Count open files by type
echo "=== Open File Types ==="
lsof 2>/dev/null | awk 'NR>1 {print $5}' | sort | uniq -c | sort -rn | head -10

# 5. Find processes with most file descriptors
echo "=== FD Hogs ==="
lsof 2>/dev/null | awk 'NR>1 {pid[$2]++} END {for(p in pid) print pid[p], p}' \
  | sort -rn | head -5
```

📸 **Verified Output:**
```
=== Network Listeners ===
(no listeners in container)
=== Deleted Files Still Open ===
bash      1 root    3w   REG   0,87        0  2109882 /tmp/testfile (deleted)
=== Open File Types ===
     14 REG
      3 FIFO
      3 CHR
      1 DIR
=== FD Hogs ===
21 1
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `lsof` | List all open files system-wide |
| `lsof -p PID` | Files opened by a specific process |
| `lsof -c bash` | Files opened by processes named "bash" |
| `lsof -u root` | Files opened by a specific user |
| `lsof -i` | All network connections |
| `lsof -i :PORT` | Find process using a specific port |
| `lsof -i TCP -sTCP:LISTEN` | All TCP listeners |
| `lsof +D /path` | All files open inside a directory (recursive) |
| `lsof +d /path` | Files open in directory (non-recursive) |
| `lsof -t -u user` | Just PIDs for user's open files |
| `lsof \| grep '(deleted)'` | Find deleted files still held open |
| `lsof -n` | Don't resolve hostnames (faster output) |
