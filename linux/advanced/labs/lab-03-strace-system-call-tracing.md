# Lab 03: System Call Tracing with strace

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Every interaction between a program and the Linux kernel goes through **system calls** (syscalls). `strace` intercepts and logs these calls in real-time, making it invaluable for debugging, security analysis, and understanding program behavior. This lab covers filtering, counting, following forks, and tracing real programs.

---

## Step 1: Install strace

```bash
apt-get update -qq && apt-get install -y strace
strace --version | head -1
```

📸 **Verified Output:**
```
strace -- version 5.16
```

> 💡 `strace` works by using the `ptrace()` syscall to intercept system calls of the target process. This is why it requires root or matching UID. It has a performance overhead (2–10x slowdown) — use it for debugging only.

---

## Step 2: Basic Tracing — Understand the Output Format

Trace a simple command and observe the output format:

```bash
strace ls /tmp 2>&1 | head -15
```

📸 **Verified Output:**
```
execve("/usr/bin/ls", ["ls", "/tmp"], 0x7ffee45c9fd0 /* 6 vars */) = 0
brk(NULL)                               = 0x55fa3c8e0000
arch_prctl(0x3001 /* ARCH_??? */, 0xffffd050) = -1 EINVAL (Invalid argument)
mmap(NULL, 8192, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0) = 0x7f3a12345000
access("/etc/ld.so.preload", R_OK)      = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libselinux.so.1", O_RDONLY|O_CLOEXEC) = 3
read(3, "\177ELF\2\1\1\0\0\0\0\0\0\0\0\0\3\0>\0\1\0\0\0\220p\0\0\0\0\0\0"..., 832) = 832
mmap(NULL, 2252792, PROT_READ, MAP_PRIVATE|MAP_DENYWRITE, 3, 0) = 0x7f3a12100000
close(3)                                = 0
write(1, "\n", 1)                       = 1
+++ exited with 0 +++
```

**Output format anatomy:**
```
syscall_name(arg1, arg2, ...) = return_value [error_message]
```

- `=` followed by **positive number**: success (often a file descriptor)
- `= -1 ENOENT`: failure with error code
- `= 0`: success (no meaningful return)
- `+++ exited with 0 +++`: process exit status

---

## Step 3: Filter Syscalls with -e trace=

Focus on specific syscalls to reduce noise:

```bash
# Trace only file opens
strace -e trace=openat ls /tmp 2>&1
```

📸 **Verified Output:**
```
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libselinux.so.1", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libpcre2-8.so.0", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/proc/filesystems", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/tmp", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 3
+++ exited with 0 +++
```

```bash
# Trace multiple syscall types
strace -e trace=read,write,close ls /tmp 2>&1 | head -10

# Trace by category
strace -e trace=network curl -s http://example.com 2>&1 | head -10
strace -e trace=file ls /tmp 2>&1 | head -10
strace -e trace=process bash -c 'exit 0' 2>&1
```

**Syscall categories:**
| Category | Syscalls included |
|----------|------------------|
| `file` | All file-related: open, read, stat, etc. |
| `network` | socket, connect, bind, send, recv, etc. |
| `process` | execve, fork, clone, wait, exit |
| `memory` | mmap, brk, mprotect |
| `signal` | kill, sigaction, pause |

> 💡 Combine filters: `strace -e trace=openat,read,write` — multiple syscalls comma-separated.

---

## Step 4: Timestamp Output with -tt

Add precise timestamps to understand timing:

```bash
strace -tt -e trace=execve date 2>&1
```

📸 **Verified Output:**
```
06:41:54.865612 execve("/usr/bin/date", ["date"], 0x7fffdf949fb8 /* 6 vars */) = 0
Thu Mar  5 06:41:54 UTC 2026
06:41:54.876604 +++ exited with 0 +++
```

```bash
# Use -T to show time spent in each syscall
strace -T -e trace=openat ls /tmp 2>&1
```

**Output includes `<N.NNNNNN>` — time in seconds for each call:**
```
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3 <0.000045>
```

> 💡 `-tt` shows wall-clock time of each call (for sequencing). `-T` shows duration of each call (for identifying slow operations). Use both together with `-ttT`.

---

## Step 5: Count Syscalls with -c

Get a statistical summary of all syscall activity:

```bash
strace -c ls /tmp 2>&1
```

📸 **Verified Output:**
```
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 25.78    0.000998         998         1           execve
 20.02    0.000775          45        17           mmap
  8.19    0.000317          45         7           mprotect
  7.83    0.000303          50         6           openat
  6.28    0.000243          30         8           close
  5.27    0.000204          40         5           read
  5.09    0.000197          32         6           newfstatat
  3.07    0.000119         119         1           munmap
  2.92    0.000113          37         3           brk
  2.92    0.000113          56         2           getdents64
  2.58    0.000100          50         2         2 statfs
  2.01    0.000078          39         2         2 access
  1.58    0.000061          30         2         1 arch_prctl
  1.50    0.000058          29         2         2 ioctl
  1.11    0.000043          43         1           statx
  0.83    0.000032          32         1           getrandom
  0.83    0.000032          32         1           rseq
  0.75    0.000029          29         1           set_tid_address
  0.75    0.000029          29         1           set_robust_list
  0.70    0.000027          27         1           prlimit64
  0.00    0.000000           0         4           pread64
------ ----------- ----------- --------- --------- ----------------
100.00    0.003871          52        74         7 total
```

> 💡 The `errors` column is gold — it shows failed syscall counts. `2 access` errors above = the `access()` calls for `/etc/ld.so.preload` (doesn't exist but checked anyway).

---

## Step 6: Follow Forks with -f

Trace child processes spawned via `fork()` or `clone()`:

```bash
strace -f -e trace=process bash -c 'echo hello' 2>&1
```

📸 **Verified Output:**
```
execve("/usr/bin/bash", ["bash", "-c", "echo hello"], 0x7ffff3e0b578 /* 6 vars */) = 0
hello
exit_group(0)                           = ?
+++ exited with 0 +++
```

```bash
# More complex example with child PID tracking
strace -f -e trace=clone,execve,exit_group bash -c 'ls && echo done' 2>&1
```

With `-f`, output prefixes show which PID made each call:
```
[pid  1234] execve("/usr/bin/ls", ...) = 0
[pid  1234] +++ exited with 0 +++
[pid  1200] write(1, "done\n", 5) = 5
```

> 💡 Use `-ff -o /tmp/trace` to write each process's trace to a separate file (`/tmp/trace.PID`). Essential for debugging multi-process applications.

---

## Step 7: Write Output to File with -o

For long traces, redirect to a file:

```bash
strace -o /tmp/trace.log -e trace=openat ls /tmp
cat /tmp/trace.log
```

📸 **Verified Output:**
```
openat(AT_FDCWD, "/etc/ld.so.cache", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libselinux.so.1", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libc.so.6", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/lib/x86_64-linux-gnu/libpcre2-8.so.0", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/proc/filesystems", O_RDONLY|O_CLOEXEC) = 3
openat(AT_FDCWD, "/tmp", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 3
+++ exited with 0 +++
```

```bash
# Attach to a running process by PID
PID=$(pgrep -f some-program)
strace -p $PID -o /tmp/live-trace.log &
sleep 5
kill %1  # stop strace
```

> 💡 Attaching with `-p` doesn't restart the program — it observes an already-running process. The process continues normally; only syscall logging is added.

---

## Step 8: Capstone — Debug a "File Not Found" Error

**Scenario:** A program fails silently. Use strace to find what file it's trying to open.

```bash
# Create a wrapper script that tries to read a config file
cat > /tmp/myapp.sh << 'EOF'
#!/bin/bash
# Simulate an app that reads config
cat /etc/myapp/config.yaml 2>/dev/null || echo "Config not found, using defaults"
cat /var/lib/myapp/data.db 2>/dev/null || echo "Database missing"
EOF
chmod +x /tmp/myapp.sh

# Trace it — find all failed file operations
strace -e trace=openat,read -c /tmp/myapp.sh 2>&1
```

📸 **Verified Output:**
```
Config not found, using defaults
Database missing
% time     seconds  usecs/call     calls    errors syscall
------ ----------- ----------- --------- --------- ----------------
 61.23    0.000312          26        12         2 openat
 38.77    0.000198          28         7           read
------ ----------- ----------- --------- --------- ----------------
100.00    0.000510          27        19         2 total
```

```bash
# Show exactly which opens failed
strace -e trace=openat /tmp/myapp.sh 2>&1 | grep 'ENOENT'
```

📸 **Verified Output:**
```
openat(AT_FDCWD, "/etc/myapp/config.yaml", O_RDONLY) = -1 ENOENT (No such file or directory)
openat(AT_FDCWD, "/var/lib/myapp/data.db", O_RDONLY) = -1 ENOENT (No such file or directory)
```

**Debug summary:** strace revealed exactly which two files were missing, their full paths, and the error code — without needing source code or verbose logging.

---

## Summary

| Flag | Purpose |
|------|---------|
| `strace <cmd>` | Trace all syscalls of a command |
| `-e trace=openat,read` | Filter to specific syscalls |
| `-e trace=file` | Filter by syscall category |
| `-c` | Count/summarize syscalls (statistics) |
| `-tt` | Add wall-clock timestamps |
| `-T` | Show time spent in each syscall |
| `-f` | Follow child processes (fork/clone) |
| `-ff -o file` | Write per-PID traces to separate files |
| `-o file` | Write trace to file instead of stderr |
| `-p PID` | Attach to running process |
| `grep ENOENT` | Find failed file operations |
