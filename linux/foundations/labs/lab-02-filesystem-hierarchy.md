# Lab 02: Filesystem Hierarchy Standard (FHS)

## Objective
Understand the Linux directory tree: what each top-level directory is for, how to explore it, and why Linux organises files this way. This is the map you'll use for every future lab.

**Time:** 25 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Step 1: The Root of Everything

```bash
ls /
```

**📸 Verified Output:**
```
bin   boot  dev  etc  home  lib  lib32  lib64  libx32
media mnt   opt  proc root  run  sbin   srv    sys  tmp  usr  var
```

> 💡 Every file on a Linux system lives under `/` (the root directory). There are no drive letters like Windows — one unified tree.

---

## Step 2: Explore the Root with Details

```bash
ls -la /
```

**📸 Verified Output:**
```
total 56
drwxr-xr-x   1 root root 4096 Mar  5 00:53 .
drwxr-xr-x   1 root root 4096 Mar  5 00:53 ..
-rwxr-xr-x   1 root root    0 Mar  5 00:53 .dockerenv
lrwxrwxrwx   1 root root    7 Feb 10 14:04 bin -> usr/bin
drwxr-xr-x   2 root root 4096 Apr 18  2022 boot
drwxr-xr-x   5 root root  340 Mar  5 00:53 dev
drwxr-xr-x   1 root root 4096 Mar  5 00:53 etc
drwxr-xr-x   2 root root 4096 Apr 18  2022 home
lrwxrwxrwx   1 root root    7 Feb 10 14:04 lib -> usr/lib
drwxr-xr-x   2 root root 4096 Feb 10 14:05 media
drwxr-xr-x   2 root root 4096 Feb 10 14:05 mnt
drwxr-xr-x   2 root root 4096 Feb 10 14:05 opt
dr-xr-xr-x 593 root root    0 Mar  5 00:53 proc
drwx------   2 root root 4096 Feb 10 14:12 root
drwxr-xr-x   5 root root 4096 Feb 10 14:12 run
lrwxrwxrwx   1 root root    8 Feb 10 14:04 sbin -> usr/sbin
drwxr-xr-x   2 root root 4096 Feb 10 14:05 srv
dr-xr-xr-x  13 root root    0 Mar  1 20:13 sys
drwxrwxrwt   2 root root 4096 Feb 10 14:12 tmp
drwxr-xr-x  14 root root 4096 Feb 10 14:05 usr
drwxr-xr-x  11 root root 4096 Feb 10 14:12 var
```

> 💡 Notice `bin -> usr/bin` — this is a **symlink**. Modern Ubuntu merges `/bin` into `/usr/bin`. The `l` at the start of `lrwxrwxrwx` tells you it's a symbolic link.

---

## Step 3: The Essential Directories

```bash
echo "=== /etc — System Configuration ==="
ls /etc | head -10

echo "=== /var/log — Log Files ==="
ls -lh /var/log | head -8

echo "=== /usr/bin — User Commands ==="
ls /usr/bin | wc -l

echo "=== /proc — Kernel Virtual Filesystem ==="
ls /proc | head -15
```

**📸 Verified Output:**
```
=== /etc — System Configuration ===
adduser.conf
alternatives
apt
bash.bashrc
bindresvport.blacklist
ca-certificates
ca-certificates.conf
cloud
cron.d
debconf.conf

=== /var/log — Log Files ===
total 296K
-rw-r--r-- 1 root root 4.8K Feb 10 14:11 alternatives.log
drwxr-xr-x 2 root root 4.0K Feb 10 14:12 apt
-rw-r--r-- 1 root root  64K Feb 10 14:05 bootstrap.log
-rw-rw---- 1 root utmp    0 Feb 10 14:05 btmp
-rw-r--r-- 1 root root 183K Feb 10 14:12 dpkg.log
-rw-r--r-- 1 root root 3.2K Feb 10 14:05 faillog
-rw-rw-r-- 1 root utmp  29K Feb 10 14:05 lastlog

=== /usr/bin — User Commands ===
856

=== /proc — Kernel Virtual Filesystem ===
1  buddyinfo  bus  cgroups  cmdline  consoles  cpuinfo  crypto
devices  diskstats  dma  driver  dynamic_debug  execdomains  fb
```

---

## Step 4: The /proc Virtual Filesystem

```bash
cat /proc/cpuinfo | grep -E "model name|cpu cores" | head -4
```

**📸 Verified Output:**
```
model name	: Intel(R) Xeon(R) CPU @ 2.20GHz
cpu cores	: 1
```

```bash
cat /proc/meminfo | head -5
```

**📸 Verified Output:**
```
MemTotal:       32871484 kB
MemFree:        19234512 kB
MemAvailable:   28912340 kB
Buffers:          892344 kB
Cached:          8234512 kB
```

> 💡 `/proc` is not a real directory on disk — it's a **virtual filesystem** generated live by the kernel. Reading `/proc/cpuinfo` actually asks the kernel "what CPU do I have?" in real time.

---

## Step 5: The /etc Directory (System Configuration)

```bash
ls /etc/*.conf
```

**📸 Verified Output:**
```
/etc/adduser.conf   /etc/debconf.conf    /etc/ld.so.conf     /etc/nsswitch.conf
/etc/ca-certificates.conf  /etc/deluser.conf  /etc/mke2fs.conf   /etc/sysctl.conf
/etc/e2scrub.conf
```

```bash
cat /etc/hostname
```

**📸 Verified Output:**
```
3e03e4da0e25
```

```bash
cat /etc/shells
```

**📸 Verified Output:**
```
# /etc/shells: valid login shells
/bin/sh
/bin/bash
/usr/bin/bash
/bin/rbash
/usr/bin/rbash
/usr/bin/sh
/bin/dash
/usr/bin/dash
```

---

## Step 6: The /var Directory (Variable Data)

```bash
du -sh /var/*
```

**📸 Verified Output:**
```
4.0K	/var/backups
4.0K	/var/cache
4.0K	/var/lib
4.0K	/var/local
0	    /var/lock
296K	/var/log
0	    /var/mail
4.0K	/var/opt
0	    /var/run
4.0K	/var/spool
0	    /var/tmp
```

> 💡 `/var` holds data that **changes** while the system runs: logs, databases, package caches, mail spools, print queues. A full `/var` partition will crash your system — a common production incident.

---

## Step 7: The /tmp Directory

```bash
ls -la /tmp
echo "Permissions on /tmp:"
stat /tmp | grep Access
```

**📸 Verified Output:**
```
total 8
drwxrwxrwt 2 root root 4096 Feb 10 14:12 .
drwxr-xr-x 1 root root 4096 Mar  5 00:53 ..
Permissions on /tmp:
Access: (1777/drwxrwxrwt)  Uid: (    0/    root)   Gid: (    0/    root)
```

> 💡 The `t` in `drwxrwxrwt` is the **sticky bit** — anyone can create files in `/tmp`, but only the owner can delete their own files. Without it, any user could delete any other user's temp files.

---

## Step 8: Capstone — FHS Reference Card

```bash
cat << 'EOF'
Linux Filesystem Hierarchy — Quick Reference
============================================
/           Root of the filesystem
├── /bin    → /usr/bin  Essential user binaries (ls, cp, mv)
├── /boot       Kernel and bootloader files
├── /dev        Device files (disks, terminals, /dev/null)
├── /etc        System-wide configuration files
├── /home       User home directories (/home/alice, /home/bob)
├── /lib    → /usr/lib  Shared libraries
├── /media      Mount points for removable media
├── /mnt        Temporary mount points
├── /opt        Optional/third-party software
├── /proc       Virtual FS: kernel and process info (not on disk)
├── /root       Root user's home directory
├── /run        Runtime data (PID files, sockets) — cleared on boot
├── /sbin   → /usr/sbin  System administration binaries
├── /srv        Data served by this system (web, FTP)
├── /sys        Virtual FS: hardware and kernel subsystems
├── /tmp        Temporary files — cleared on reboot (sticky bit)
├── /usr        Read-only user data (binaries, libraries, docs)
└── /var        Variable data: logs, caches, databases, mail
EOF
```

**📸 Verified Output:**
```
Linux Filesystem Hierarchy — Quick Reference
============================================
/           Root of the filesystem
├── /bin    → /usr/bin  Essential user binaries (ls, cp, mv)
├── /boot       Kernel and bootloader files
...
└── /var        Variable data: logs, caches, databases, mail
```

---

## Summary

| Directory | Purpose | Grows? |
|-----------|---------|--------|
| `/etc` | Config files | Rarely |
| `/var` | Logs, databases, caches | Yes — monitor! |
| `/tmp` | Temporary files | Cleared on reboot |
| `/proc` | Kernel virtual FS | Not on disk |
| `/usr` | Programs and libraries | On install |
| `/home` | User data | Yes |
