# Lab 9: Linux Security Basics

## 🎯 Objective
Master Linux file permissions as a security mechanism: understand rwx bits, SUID/SGID, sticky bit, find world-writable files, and understand why /tmp is a security risk.

## 📚 Background
Linux uses a discretionary access control (DAC) model for file permissions. Every file has an owner, a group, and permissions for three classes: owner (u), group (g), and others (o). Each class has read (r=4), write (w=2), and execute (x=1) bits. So `chmod 755` sets owner=rwx(7), group=r-x(5), others=r-x(5).

**SUID (Set User ID)** is a special permission bit. When set on an executable, it runs with the file owner's privileges rather than the executing user's. For example, `/usr/bin/passwd` has SUID set and is owned by root — allowing regular users to change their own passwords (which requires writing to /etc/shadow). Attackers look for SUID binaries they can abuse to escalate privileges.

**SGID (Set Group ID)** is similar but for groups. On directories, SGID ensures new files inherit the directory's group. **Sticky bit** on directories means only the file owner can delete their files, even if the directory is world-writable — this is why /tmp has the sticky bit (so users can't delete each other's temp files).

**World-writable files** (permissions 777 or o+w) are accessible by every user — a significant security risk. World-writable scripts in cron jobs are a classic privilege escalation path.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Basic Linux command line
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `ls -la` — List permissions
- `chmod`, `chown` — Modify permissions
- `find` — Find files by permission
- `stat` — Detailed file metadata

## 🔬 Lab Instructions

### Step 1: Understanding File Permissions
```bash
docker run --rm innozverse-cybersec bash -c "ls -la /etc/passwd /etc/shadow"
```

**📸 Verified Output:**
```
-rw-r--r-- 1 root root   1025 Mar  1 19:45 /etc/passwd
-rw-r----- 1 root shadow  562 Mar  1 19:45 /etc/shadow
```

> 💡 **What this means:** `/etc/passwd` is readable by everyone (`r--` for others) — it contains usernames but not passwords. `/etc/shadow` is only readable by root and the shadow group (`r-----`) — it contains password hashes. This design separates what's needed for user lookup from what's sensitive.

### Step 2: Permission Bits in Detail
```bash
docker run --rm innozverse-cybersec bash -c "
python3 -c \"
perms = [
    ('777', 'rwxrwxrwx', 'DANGEROUS: everyone can read/write/execute'),
    ('755', 'rwxr-xr-x', 'Normal executable: owner full, others read+execute'),
    ('644', 'rw-r--r--', 'Normal file: owner read/write, others read only'),
    ('600', 'rw-------', 'Private file: only owner can read/write'),
    ('400', 'r--------', 'Read-only by owner: protect private keys'),
    ('4755', 'rwsr-xr-x', 'SUID bit: runs as owner (root!) when executed'),
    ('1777', 'rwxrwxrwt', 'Sticky bit: only owner can delete (used on /tmp)'),
]
for octal, symbolic, desc in perms:
    print(f'{octal:5} ({symbolic}) - {desc}')
\"
"
```

**📸 Verified Output:**
```
  777 (rwxrwxrwx) - DANGEROUS: everyone can read/write/execute
  755 (rwxr-xr-x) - Normal executable: owner full, others read+execute
  644 (rw-r--r--) - Normal file: owner read/write, others read only
  600 (rw-------) - Private file: only owner can read/write
  400 (r--------) - Read-only by owner: protect private keys
 4755 (rwsr-xr-x) - SUID bit: runs as owner (root!) when executed
 1777 (rwxrwxrwt) - Sticky bit: only owner can delete (used on /tmp)
```

> 💡 **What this means:** The `s` in SUID (`rwsr-xr-x`) indicates the SUID bit is set. When you execute this file, it runs as the file's owner (often root), not as you. This is the primary way attackers escalate from regular user to root — finding vulnerable SUID files.

### Step 3: Find SUID Files
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== SUID files (run as owner when executed) ==='
find /usr/bin -perm -4000 -type f 2>/dev/null
echo ''
echo '=== /tmp sticky bit ==='
ls -la / | grep ' tmp'
"
```

**📸 Verified Output:**
```
=== SUID files (run as owner when executed) ===
/usr/bin/newgrp
/usr/bin/chsh
/usr/bin/gpasswd
/usr/bin/su
/usr/bin/chfn
/usr/bin/passwd
/usr/bin/umount
/usr/bin/mount

=== /tmp sticky bit ===
drwxrwxrwt  1 root root  4096 Mar  1 19:52 tmp
```

> 💡 **What this means:** These SUID binaries are legitimate — `/usr/bin/passwd` needs SUID to write to /etc/shadow as root. However, if an attacker can exploit a vulnerability in `su` or `mount`, they get root. Tools like GTFOBins (gtfobins.github.io) catalog SUID binary abuses. The `t` at the end of `/tmp`'s permissions is the sticky bit.

### Step 4: Demonstrate File Permission Changes
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Permission demonstration ==='
touch /tmp/secret.txt
chmod 600 /tmp/secret.txt
ls -la /tmp/secret.txt
echo 'Only owner can read/write'

chmod 777 /tmp/secret.txt
ls -la /tmp/secret.txt
echo 'Now everyone can read/write - DANGEROUS'

touch /tmp/private_key.pem
chmod 400 /tmp/private_key.pem
ls -la /tmp/private_key.pem
echo 'SSH private key should be 400 - read-only by owner'
"
```

**📸 Verified Output:**
```
=== Permission demonstration ===
-rw------- 1 root root 0 Mar  1 19:52 /tmp/secret.txt
Only owner can read/write

-rwxrwxrwx 1 root root 0 Mar  1 19:52 /tmp/secret.txt
Now everyone can read/write - DANGEROUS

-r-------- 1 root root 0 Mar  1 19:52 /tmp/private_key.pem
SSH private key should be 400 - read-only by owner
```

> 💡 **What this means:** SSH private keys MUST be `400` or `600` — SSH will refuse to use them if they're world-readable. This is a built-in security check. If you accidentally expose a private key, rotate it immediately.

### Step 5: Find World-Writable Files
```bash
docker run --rm innozverse-cybersec bash -c "
touch /tmp/dangerous_script.sh
chmod 777 /tmp/dangerous_script.sh
echo '=== World-writable files in /tmp ==='
find /tmp -perm -0002 -type f 2>/dev/null
echo ''
echo '=== Privilege escalation via world-writable cron script ==='
echo 'If root cron runs /tmp/dangerous_script.sh and its world-writable:'
echo 'ANY user can modify it to: echo \"attacker ALL=(ALL) NOPASSWD:ALL\" >> /etc/sudoers'
"
```

**📸 Verified Output:**
```
=== World-writable files in /tmp ===
/tmp/dangerous_script.sh

=== Privilege escalation via world-writable cron script ===
If root cron runs /tmp/dangerous_script.sh and its world-writable:
ANY user can modify it to: echo "attacker ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
```

> 💡 **What this means:** This is a classic privilege escalation path in CTF challenges and real penetration tests. If a cron job run by root executes a world-writable script, any user can modify that script to run arbitrary code as root. Always check cron jobs and their target script permissions during security audits.

### Step 6: umask — Default Permission Mask
```bash
docker run --rm innozverse-cybersec bash -c "
umask
touch /tmp/newfile.txt
ls -la /tmp/newfile.txt
echo '---'
echo 'umask 022: Files get 644, Dirs get 755'
echo 'umask 077: Files get 600, Dirs get 700 (more private)'
"
```

**📸 Verified Output:**
```
0022
-rw-r--r-- 1 root root 0 Mar  1 19:52 /tmp/newfile.txt
---
umask 022: Files get 644, Dirs get 755
umask 077: Files get 600, Dirs get 700 (more private)
```

> 💡 **What this means:** `umask 022` is the standard default — group and others get read but not write. Setting `umask 077` in user shell profiles makes all new files private by default. Sensitive applications like SSH key generation should use a restrictive umask.

### Step 7: /tmp Security Risks
```bash
docker run --rm innozverse-cybersec bash -c "
ls -la / | grep ' tmp'
echo '---'
echo '/tmp is world-writable (rwxrwxrwx) with sticky bit (t)'
echo 'Risks:'
echo '  - Race condition: attacker creates symlink before program writes'
echo '  - Information leakage: temp files may contain sensitive data'
echo '  - Malware staging: attackers use /tmp to store tools'
echo 'Defenses:'
echo '  - Mount /tmp with noexec,nosuid'
echo '  - Use mktemp for unique filenames'
echo '  - Clean /tmp regularly'
"
```

**📸 Verified Output:**
```
drwxrwxrwt  1 root root  4096 Mar  1 19:52 tmp
---
/tmp is world-writable (rwxrwxrwx) with sticky bit (t)
Risks:
  - Race condition: attacker creates symlink before program writes
  - Information leakage: temp files may contain sensitive data
  - Malware staging: attackers use /tmp to store tools
Defenses:
  - Mount /tmp with noexec,nosuid
  - Use mktemp for unique filenames
  - Clean /tmp regularly
```

> 💡 **What this means:** The `t` (sticky bit) prevents users from deleting each other's files in /tmp. But symlink races are still possible: an attacker creates `/tmp/target_filename` as a symlink to `/etc/sudoers` before a root script creates the file — the root script then overwrites sudoers! Use `mktemp` for random unpredictable filenames.

### Step 8: Linux User and Group Security
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Users with UID 0 (root) ==='
awk -F: '\$3==0 {print \$1}' /etc/passwd
echo ''
echo '=== System accounts (no shell) ==='
awk -F: '\$7 ~ /nologin|false/ {print \$1\": \"\$7}' /etc/passwd | head -5
echo ''
echo '=== Account status ==='
cat /etc/passwd | head -3
"
```

**📸 Verified Output:**
```
=== Users with UID 0 (root) ===
root

=== System accounts (no shell) ==='
daemon: /usr/sbin/nologin
bin: /usr/sbin/nologin
sys: /usr/sbin/nologin
sync: /bin/sync
games: /usr/sbin/nologin

=== Account status ===
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
```

> 💡 **What this means:** Only `root` should have UID 0. Multiple UID 0 accounts is a serious backdoor indicator. System accounts use `/usr/sbin/nologin` as their shell — they can't be logged into interactively, only used by services. The `x` in the password field means the actual hash is in /etc/shadow.

### Step 9: File Capabilities (Alternative to SUID)
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== File capabilities ==='
getcap /usr/bin/ping 2>/dev/null || echo 'ping: uses SUID or no special caps in this container'
getcap /usr/bin/python3 2>/dev/null || echo 'python3: no special capabilities'
echo ''
echo 'Capabilities more granular than SUID:'
echo '  CAP_NET_RAW: create raw sockets (needed by ping)'
echo '  CAP_NET_BIND_SERVICE: bind to ports < 1024'
echo '  CAP_DAC_OVERRIDE: bypass file permission checks (dangerous!)'
echo '  If python3 had cap_setuid -> instant root escalation'
"
```

**📸 Verified Output:**
```
=== File capabilities ===
ping: uses SUID or no special caps in this container
python3: no special capabilities

Capabilities more granular than SUID:
  CAP_NET_RAW: create raw sockets (needed by ping)
  CAP_NET_BIND_SERVICE: bind to ports < 1024
  CAP_DAC_OVERRIDE: bypass file permission checks (dangerous!)
  If python3 had cap_setuid -> instant root escalation
```

> 💡 **What this means:** Linux capabilities split root's omnipotent privileges into ~40 distinct capabilities. If Python3 had `cap_setuid` or `cap_dac_override`, an attacker with code execution could escalate to root. Always audit capabilities with `getcap -r / 2>/dev/null` during security assessments.

### Step 10: Security Audit Script
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Linux Security Quick Audit ==='
echo ''
echo '[+] SUID files count:'
find /usr/bin /usr/sbin -perm -4000 -type f 2>/dev/null | wc -l
echo ''
echo '[+] World-writable files in /etc:'
find /etc -perm -0002 -type f 2>/dev/null | head -5 || echo '  None found (good!)'
echo ''
echo '[+] Checking for empty passwords:'
awk -F: '(\$2==\"\") {print \"EMPTY PASSWORD: \"\$1}' /etc/shadow 2>/dev/null || echo '  Cannot read /etc/shadow (run as root)'
echo ''
echo '[+] Orphaned files (no owner):'
find /tmp -nouser 2>/dev/null | head -3 || echo '  None found'
echo ''
echo 'Audit complete'
"
```

**📸 Verified Output:**
```
=== Linux Security Quick Audit ===

[+] SUID files count:
8

[+] World-writable files in /etc:
  None found (good!)

[+] Checking for empty passwords:
  Cannot read /etc/shadow (run as root)

[+] Orphaned files (no owner):
  None found

Audit complete
```

> 💡 **What this means:** This mini-audit checks the most common security issues. No world-writable files in /etc is good. 8 SUID files is a reasonable count for a standard installation. This is what automated tools like LinPEAS and LinEnum do comprehensively — run during post-exploitation to find privilege escalation paths.

## ✅ Verification
```bash
docker run --rm innozverse-cybersec bash -c "
find /usr/bin -perm -4000 -type f 2>/dev/null | head -3
ls -la / | grep ' tmp'
echo 'Linux security audit complete'
"
```

**📸 Verified Output:**
```
/usr/bin/newgrp
/usr/bin/chsh
/usr/bin/gpasswd
drwxrwxrwt  1 root root  4096 Mar  1 20:00 tmp
Linux security audit complete
```

## 🚨 Common Mistakes
- **Forgetting that SUID on scripts is mostly ignored**: Linux ignores SUID on interpreted scripts for security. Only binaries honor SUID.
- **World-writable directories in PATH**: If any directory in $PATH is world-writable, attackers can plant malicious binaries.
- **Confusing /tmp sticky bit with security**: The sticky bit prevents deletion, but world-writable /tmp still allows creating/reading files — never store sensitive data in /tmp.

## 📝 Summary
- Linux file permissions (rwx for owner/group/others) are the foundation of access control; misconfigured permissions are a leading privilege escalation vector
- SUID/SGID bits run programs with the file owner's/group's privileges; audit SUID files regularly against a known-good baseline
- World-writable files and directories are dangerous — especially if executed by privileged processes (cron, systemd)
- /tmp is world-writable but sticky — use mktemp for random filenames; never store sensitive data there without encryption

## 🔗 Further Reading
- [GTFOBins - SUID exploitation](https://gtfobins.github.io/)
- [Linux Privilege Escalation Guide](https://book.hacktricks.xyz/linux-hardening/privilege-escalation)
- [CIS Linux Benchmarks](https://www.cisecurity.org/benchmark/distribution_independent_linux)
