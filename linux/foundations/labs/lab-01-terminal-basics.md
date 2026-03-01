# Lab 1: Terminal Basics

## 🎯 Objective
Learn the essential commands every Linux user needs from their very first terminal session: navigating identity, system info, and orientation commands.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Access to a Linux terminal (Ubuntu 22.04)
- No prior Linux knowledge required

## 🔬 Lab Instructions

### Step 1: Find Out Who You Are

```bash
# Display your current username
whoami
```

**Expected output:**
```
zchen
```

```bash
# Display detailed user and group information
id
```

**Expected output:**
```
uid=1000(zchen) gid=1000(zchen) groups=1000(zchen),4(adm),27(sudo),...
```

### Step 2: Find Out Where You Are

```bash
# Print working directory (your current location)
pwd
```

**Expected output:**
```
/home/zchen
```

### Step 3: Get System Information

```bash
# Show kernel and system architecture
uname -a
```

**Expected output:**
```
Linux hostname 6.14.0-37-generic #37-Ubuntu SMP ... x86_64 GNU/Linux
```

```bash
# Show just the OS type
uname -s
```

**Expected output:**
```
Linux
```

```bash
# Show machine hostname
hostname
```

**Expected output:**
```
openclaw
```

### Step 4: Check the Date and System Uptime

```bash
# Show current date and time
date
```

**Expected output:**
```
Sun Mar  1 17:00:00 UTC 2026
```

```bash
# Show how long the system has been running
uptime
```

**Expected output:**
```
 17:00:00 up 2 days,  5:00,  2 users,  load average: 0.10, 0.20, 0.15
```

### Step 5: List Files and Directories

```bash
# List files in current directory
ls
```

```bash
# List files with details (long format)
ls -l ~
```

**Expected output:**
```
total 0
drwxr-xr-x 2 zchen zchen 4096 Mar  1 12:00 Documents
```

```bash
# List all files including hidden ones
ls -la ~
```

```bash
# List with human-readable sizes
ls -lh /tmp
```

### Step 6: Print Messages to the Screen

```bash
# Print a simple message
echo "Hello, Linux!"
```

**Expected output:**
```
Hello, Linux!
```

```bash
# Print the value of a variable
echo "You are logged in as: $(whoami) on $(hostname)"
```

**Expected output:**
```
You are logged in as: zchen on openclaw
```

## ✅ Verification

```bash
echo "User: $(whoami)"
echo "Host: $(hostname)"
echo "Dir:  $(pwd)"
echo "Date: $(date +%Y-%m-%d)"
uname -r
uptime -p
```

## 📝 Summary
- `whoami` and `id` reveal your identity and group memberships
- `pwd` shows your current location in the filesystem
- `hostname` and `uname -a` describe the system you're on
- `date` and `uptime` show time and system availability
- `ls`, `ls -l`, and `ls -la` list files with increasing detail
- `echo` prints text and variable values to the screen
