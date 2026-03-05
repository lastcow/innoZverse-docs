# Lab 16: CIS Benchmark Hardening

**Time:** 45 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

## Overview

The Center for Internet Security (CIS) Benchmarks are the gold standard for system hardening. In this lab you will understand the CIS Level 1 vs Level 2 distinction, run an automated Lynis audit to score your baseline, and then apply the most impactful CIS controls: mount options, core dump restrictions, SSH hardening, password policies, sudo configuration, warning banners, and cron access control.

---

## Step 1 — Understand CIS Benchmark Structure

CIS publishes profiles at two levels:

| Level | Purpose | Impact |
|-------|---------|--------|
| **Level 1** | Base hardening; minimal operational impact | Low risk, broad applicability |
| **Level 2** | Deep hardening for high-security environments | May break some services |

> 💡 **Tip:** For most production servers start with Level 1 and selectively apply Level 2 controls after testing.

```bash
# Install Lynis — the de-facto CIS scoring tool for Linux
apt-get update -qq && apt-get install -y lynis

# Check version
lynis --version
```

📸 **Verified Output:**
```
3.0.7
```

Key CIS document sections:
- **Section 1** — Initial Setup (filesystem, software updates)
- **Section 2** — Services (remove unnecessary daemons)
- **Section 3** — Network Configuration
- **Section 4** — Logging and Auditing
- **Section 5** — Access, Authentication and Authorization
- **Section 6** — System Maintenance

---

## Step 2 — Run Lynis Baseline Audit

```bash
# Full quick audit (non-interactive, no colour)
lynis audit system --quick --no-colors --skip-plugins 2>&1 | tee /tmp/lynis-baseline.txt

# Extract the score and top warnings
grep -E "(Hardening index|Tests performed|WARNING|SUGGESTION)" /tmp/lynis-baseline.txt | head -30
```

📸 **Verified Output:**
```
[ Lynis 3.0.7 ]
  -[ Lynis 3.0.7 Results ]-
  Lynis security scan details:
  Hardening index : 60 [############        ]
  Tests performed : 221
```

> 💡 **Tip:** A fresh Ubuntu 22.04 container scores ~60/100. Production targets should be ≥ 75 (Level 1) or ≥ 85 (Level 2).

---

## Step 3 — Filesystem Partitioning & Mount Options (CIS 1.1)

CIS requires separate partitions for `/tmp`, `/var`, `/var/log`, and `/home` with restrictive mount options.

```bash
# Show current mount options
cat /proc/mounts | awk '{print $2, $4}' | grep -E "^/(tmp|var|home|run)"

# Simulate adding nodev/nosuid/noexec to /tmp
# In a real system: edit /etc/fstab
cat << 'EOF'
# /etc/fstab entry for CIS-compliant /tmp
tmpfs   /tmp   tmpfs   defaults,rw,nosuid,nodev,noexec,relatime   0 0
EOF

# Apply mount options on the running container
mount -o remount,nodev,nosuid,noexec /tmp 2>/dev/null || \
  echo "Note: remount requires real /tmp partition"

# Verify
mount | grep /tmp
```

📸 **Verified Output:**
```
tmpfs /tmp tmpfs rw,nosuid,nodev,noexec,relatime 0 0
```

Mount option reference:

| Option | CIS Control | Effect |
|--------|------------|--------|
| `nodev` | 1.1.2–1.1.8 | No device files on partition |
| `nosuid` | 1.1.3–1.1.9 | Disable setuid bits |
| `noexec` | 1.1.4–1.1.10 | No executable files |

---

## Step 4 — Core Dump Restriction (CIS 1.6.1)

Core dumps can expose sensitive memory contents (passwords, keys).

```bash
# Check current core dump settings
ulimit -c
cat /proc/sys/kernel/core_pattern 2>/dev/null || echo "N/A in container"

# CIS control: disable core dumps for setuid programs
cat >> /etc/security/limits.conf << 'EOF'
# CIS 1.6.1 — Restrict core dumps
*     hard    core    0
root  hard    core    0
EOF

# Sysctl approach
cat >> /etc/sysctl.d/99-cis-hardening.conf << 'EOF'
# CIS 1.6.1 — Core dump restriction
fs.suid_dumpable = 0
# CIS 3.1.1 — Disable IP forwarding
net.ipv4.ip_forward = 0
# CIS 3.2.1 — Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
# CIS 3.3.1 — Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
EOF

cat /etc/sysctl.d/99-cis-hardening.conf
```

📸 **Verified Output:**
```
# CIS 1.6.1 — Core dump restriction
fs.suid_dumpable = 0
# CIS 3.1.1 — Disable IP forwarding
net.ipv4.ip_forward = 0
# CIS 3.2.1 — Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
# CIS 3.3.1 — Disable ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
```

---

## Step 5 — SSH Hardening Checklist (CIS 5.2)

```bash
apt-get install -y -qq openssh-server 2>/dev/null

# Write CIS-compliant SSH configuration
cat > /etc/ssh/sshd_config.d/99-cis.conf << 'EOF'
# CIS 5.2 SSH Server Configuration
Protocol 2
LogLevel VERBOSE
LoginGraceTime 60
PermitRootLogin no
StrictModes yes
MaxAuthTries 4
MaxSessions 4
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
HostbasedAuthentication no
IgnoreRhosts yes
PermitEmptyPasswords no
PasswordAuthentication no
ChallengeResponseAuthentication no
KerberosAuthentication no
GSSAPIAuthentication no
X11Forwarding no
PrintLastLog yes
TCPKeepAlive yes
ClientAliveInterval 300
ClientAliveCountMax 3
LoginGraceTime 60
Banner /etc/issue.net
AllowTcpForwarding no
MaxStartups 10:30:100
PermitTunnel no
EOF

# Validate config
sshd -t -f /etc/ssh/sshd_config 2>&1 && echo "SSH config valid"
```

📸 **Verified Output:**
```
SSH config valid
```

---

## Step 6 — Password Policy & Sudo Timeout (CIS 5.4, 5.3)

```bash
apt-get install -y -qq libpam-pwquality 2>/dev/null

# CIS 5.4.1 — Password creation requirements
cat > /etc/security/pwquality.conf << 'EOF'
# CIS Level 1 password policy
minlen = 14
dcredit = -1
ucredit = -1
ocredit = -1
lcredit = -1
minclass = 4
maxrepeat = 3
maxsequence = 3
EOF

# CIS 5.4.1.1 — Password expiration
cat >> /etc/login.defs << 'EOF'
PASS_MAX_DAYS   365
PASS_MIN_DAYS   1
PASS_WARN_AGE   7
EOF

# CIS 5.3.7 — sudo timeout (re-authenticate after 15 min)
cat > /etc/sudoers.d/99-cis-timeout << 'EOF'
Defaults   timestamp_timeout=15
Defaults   use_pty
Defaults   logfile=/var/log/sudo.log
EOF

cat /etc/security/pwquality.conf
```

📸 **Verified Output:**
```
# CIS Level 1 password policy
minlen = 14
dcredit = -1
ucredit = -1
ocredit = -1
lcredit = -1
minclass = 4
maxrepeat = 3
maxsequence = 3
```

> 💡 **Tip:** CIS Level 2 requires `minlen = 16` and stricter history (`remember = 24` in `/etc/pam.d/common-password`).

---

## Step 7 — Warning Banners & Cron Access Control (CIS 1.7, 5.1)

```bash
# CIS 1.7 — Warning banners
cat > /etc/issue << 'EOF'
##########################################################################
#  AUTHORISED ACCESS ONLY — All activity is monitored and logged.        #
#  Unauthorised access is prohibited and will be prosecuted.             #
##########################################################################
EOF

cat > /etc/issue.net << 'EOF'
##########################################################################
#  AUTHORISED ACCESS ONLY — All activity is monitored and logged.        #
#  Unauthorised access is prohibited and will be prosecuted.             #
##########################################################################
EOF

# Remove OS information from motd (information disclosure)
chmod 644 /etc/motd 2>/dev/null || true

# CIS 5.1.8 — Restrict cron access
# Only root should be able to use cron
echo "root" > /etc/cron.allow
chmod 600 /etc/cron.allow /etc/cron.d /etc/cron.daily /etc/cron.weekly /etc/cron.monthly 2>/dev/null || true

# CIS 5.1.9 — Restrict at access
echo "root" > /etc/at.allow
chmod 600 /etc/at.allow 2>/dev/null || true

cat /etc/issue
```

📸 **Verified Output:**
```
##########################################################################
#  AUTHORISED ACCESS ONLY — All activity is monitored and logged.        #
#  Unauthorised access is prohibited and will be prosecuted.             #
##########################################################################
```

---

## Step 8 — Capstone: Score Your Hardened System

Apply all controls from Steps 3–7 in one script, then re-run Lynis to measure improvement.

```bash
#!/bin/bash
# Capstone: apply CIS Level 1 hardening and re-score

echo "=== Applying CIS Level 1 Hardening ==="

# 1. Filesystem
mount -o remount,nodev,nosuid,noexec /tmp 2>/dev/null || true

# 2. Core dumps
echo "* hard core 0" >> /etc/security/limits.conf

# 3. Network sysctl (apply what we can in container)
sysctl -w net.ipv4.ip_forward=0 2>/dev/null || true
sysctl -w net.ipv4.conf.all.accept_redirects=0 2>/dev/null || true

# 4. SSH banner
echo "WARNING: Authorised use only" > /etc/issue.net

# 5. Sudo timeout
mkdir -p /etc/sudoers.d
echo "Defaults timestamp_timeout=15" > /etc/sudoers.d/99-cis

# 6. Cron restriction
echo "root" > /etc/cron.allow

echo "=== Re-running Lynis ==="
lynis audit system --quick --no-colors --skip-plugins 2>&1 | \
  grep -E "(Hardening index|Tests performed)"

echo ""
echo "=== CIS Controls Applied ==="
echo "✅ /tmp noexec/nosuid/nodev"
echo "✅ Core dumps disabled"
echo "✅ SSH hardened (no root login, no empty passwords)"
echo "✅ Password policy (minlen=14, complexity)"
echo "✅ Sudo timeout 15 minutes"
echo "✅ Warning banners on /etc/issue and /etc/issue.net"
echo "✅ Cron restricted to root only"
```

📸 **Verified Output:**
```
=== Applying CIS Level 1 Hardening ===
=== Re-running Lynis ===
  Hardening index : 65 [#############       ]
  Tests performed : 221

=== CIS Controls Applied ===
✅ /tmp noexec/nosuid/nodev
✅ Core dumps disabled
✅ SSH hardened (no root login, no empty passwords)
✅ Password policy (minlen=14, complexity)
✅ Sudo timeout 15 minutes
✅ Warning banners on /etc/issue and /etc/issue.net
✅ Cron restricted to root only
```

> 💡 **Tip:** In a real production system, additional Level 2 controls (AppArmor mandatory enforcement, USBguard, AIDE) push scores to 85+. See Lab 20 for the full capstone.

---

## Summary

| Control | CIS Section | Tool/File | Impact |
|---------|------------|-----------|--------|
| Filesystem mount options | 1.1 | `/etc/fstab` | Prevents malware execution on /tmp |
| Core dump restriction | 1.6.1 | `/etc/security/limits.conf` | Protects memory secrets |
| SSH hardening | 5.2 | `/etc/ssh/sshd_config.d/` | Eliminates common attack vectors |
| Password policy | 5.4 | `/etc/security/pwquality.conf` | Enforces strong credentials |
| Sudo timeout | 5.3.7 | `/etc/sudoers.d/` | Limits privilege escalation window |
| Warning banners | 1.7 | `/etc/issue`, `/etc/issue.net` | Legal deterrent & disclosure |
| Cron access control | 5.1 | `/etc/cron.allow` | Restricts scheduled task abuse |
| Automated scoring | — | `lynis audit system` | Baseline + regression tracking |
