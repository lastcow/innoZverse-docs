# Lab 2: Filesystem Hierarchy

## 🎯 Objective
Explore the Linux Filesystem Hierarchy Standard (FHS): /etc, /var, /home, /usr, /tmp, and /proc without needing root privileges.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 1: Terminal Basics

## 🔬 Lab Instructions

### Step 1: Overview of Root Directory

```bash
ls /
```

**Expected output:**
```
bin  boot  dev  etc  home  lib  lib64  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var
```

### Step 2: Explore /etc — System Configuration

```bash
ls /etc | head -20
```

```bash
cat /etc/hostname
```

```bash
cat /etc/os-release
```

**Expected output:**
```
PRETTY_NAME="Ubuntu 22.04.x LTS"
NAME="Ubuntu"
...
```

### Step 3: Explore /var — Variable Data

```bash
ls /var
```

```bash
ls /var/log | head -15
```

### Step 4: Explore /home — User Home Directories

```bash
ls /home
```

```bash
ls -la ~
```

```bash
echo "My home is: $HOME"
```

### Step 5: Explore /usr — User Programs

```bash
ls /usr
```

```bash
ls /usr/bin | head -20
```

```bash
ls /usr/bin | wc -l
```

### Step 6: Explore /tmp — Temporary Files

```bash
ls -la /tmp | head -10
```

```bash
echo "test data" > /tmp/mytest.txt
cat /tmp/mytest.txt
```

### Step 7: Explore /proc — Process and Kernel Info

```bash
ls /proc | head -20
```

```bash
cat /proc/version
```

```bash
cat /proc/cpuinfo | grep "model name" | head -2
```

```bash
cat /proc/meminfo | head -10
```

### Step 8: Use stat and file to Inspect Files

```bash
stat /etc/passwd
```

**Expected output (includes):**
```
Access: (0644/-rw-r--r--)  Uid: (    0/    root)
```

```bash
file /etc/passwd
file /etc/hostname
file /bin/ls
```

**Expected output:**
```
/etc/passwd:   ASCII text
/etc/hostname: ASCII text
/bin/ls:       ELF 64-bit LSB pie executable, x86-64, ...
```

## ✅ Verification

```bash
echo "=== OS Release ===" && cat /etc/os-release | grep PRETTY_NAME
echo "=== CPU Model ===" && cat /proc/cpuinfo | grep "model name" | head -1
echo "=== Hostname ===" && cat /etc/hostname
echo "=== Temp file ===" && echo "ok" > /tmp/mytest.txt && cat /tmp/mytest.txt && rm /tmp/mytest.txt
```

## 📝 Summary
- `/etc` contains system configuration files
- `/var` stores variable data like logs and caches
- `/home` holds user personal directories; `~` is a shortcut to yours
- `/usr` contains installed programs and libraries
- `/tmp` is a world-writable scratch space, cleared on reboot
- `/proc` is a virtual filesystem exposing kernel and process information
- `file` identifies file types; `stat` shows detailed metadata
