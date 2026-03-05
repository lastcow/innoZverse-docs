# Lab 01: Terminal Basics — Your First Commands

## Objective
Get comfortable with the Linux terminal: discover who you are, where you are, and what system you're on. These orientation commands are the foundation every Linux user starts with.

**Time:** 20 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: Launch Your Environment

```bash
docker run -it --rm ubuntu:22.04 bash
```

You are now inside an Ubuntu 22.04 container. The prompt `root@<id>:/#` means you are the root user at the filesystem root.

> 💡 The `--rm` flag deletes the container when you exit. Nothing you do here persists. Experiment freely.

---

## Step 2: Who Are You?

```bash
whoami
```

**📸 Verified Output:**
```
root
```

```bash
id
```

**📸 Verified Output:**
```
uid=0(root) gid=0(root) groups=0(root)
```

> 💡 `uid=0` means root — the superuser with no restrictions. In production systems, you never log in as root. Here it's safe for learning.

---

## Step 3: Where Are You?

```bash
pwd
```

**📸 Verified Output:**
```
/
```

```bash
echo $HOME
```

**📸 Verified Output:**
```
/root
```

> 💡 `pwd` = **P**rint **W**orking **D**irectory. You're currently at `/` — the filesystem root, the top of the entire Linux directory tree.

---

## Step 4: What System Are You On?

```bash
uname -a
```

**📸 Verified Output:**
```
Linux 3e03e4da0e25 6.14.0-37-generic #37-Ubuntu SMP PREEMPT_DYNAMIC Fri Nov 14 22:10:32 UTC 2025 x86_64 x86_64 x86_64 GNU/Linux
```

```bash
cat /etc/os-release | head -5
```

**📸 Verified Output:**
```
PRETTY_NAME="Ubuntu 22.04.5 LTS"
NAME="Ubuntu"
VERSION_ID="22.04"
VERSION="22.04.5 LTS (Jammy Jellyfish)"
VERSION_CODENAME=jammy
```

> 💡 `uname -a` gives: kernel name, hostname, kernel version, build date, architecture. The `x86_64` at the end means 64-bit Intel/AMD CPU.

---

## Step 5: System Status

```bash
uptime
```

**📸 Verified Output:**
```
 00:52:13 up 6 days,  2:22,  0 users,  load average: 1.38, 1.36, 1.37
```

```bash
date '+%Y-%m-%d %H:%M:%S %Z'
```

**📸 Verified Output:**
```
2026-03-05 00:52:13 UTC
```

> 💡 The **load average** (`1.38, 1.36, 1.37`) shows CPU demand over 1, 5, and 15 minutes. A value equal to your CPU count = 100% busy. Higher = overloaded.

---

## Step 6: What Shell Are You Using?

```bash
echo $SHELL
```

**📸 Verified Output:**
```
/bin/bash
```

```bash
bash --version | head -1
```

**📸 Verified Output:**
```
GNU bash, version 5.1.16(1)-release (x86_64-pc-linux-gnu)
```

> 💡 **bash** (Bourne Again SHell) is the most common Linux shell. Others include `zsh` (macOS default), `fish`, and `dash`. The shell interprets every command you type.

---

## Step 7: Hostname and Network Identity

```bash
hostname
```

**📸 Verified Output:**
```
3e03e4da0e25
```

```bash
hostname -i
```

**📸 Verified Output:**
```
172.17.0.2
```

---

## Step 8: Capstone — System Info Script

```bash
echo "=== System Identity Report ==="
echo "User:      $(whoami)"
echo "Host:      $(hostname)"
echo "OS:        $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"')"
echo "Kernel:    $(uname -r)"
echo "Arch:      $(uname -m)"
echo "IP:        $(hostname -i)"
echo "Shell:     $SHELL"
echo "Uptime:    $(uptime -p)"
echo "Time (UTC):$(date -u '+%Y-%m-%d %H:%M:%S')"
```

**📸 Verified Output:**
```
=== System Identity Report ===
User:      root
Host:      3e03e4da0e25
OS:        Ubuntu 22.04.5 LTS
Kernel:    6.14.0-37-generic
Arch:      x86_64
IP:        172.17.0.2
Shell:     /bin/bash
Uptime:    up 6 days, 2 hours, 22 minutes
Time (UTC):2026-03-05 00:52:13
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `whoami` | Current username |
| `id` | UID, GID, and group memberships |
| `pwd` | Current directory path |
| `uname -a` | Full kernel and architecture info |
| `hostname` | System hostname |
| `uptime` | System uptime and load |
| `date` | Current date/time |
| `echo $SHELL` | Active shell |
