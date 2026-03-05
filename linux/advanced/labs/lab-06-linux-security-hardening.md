# Lab 06: Linux Security Hardening

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

Security hardening reduces your attack surface by eliminating unnecessary services, enforcing strict authentication policies, and configuring the kernel to resist exploitation. This lab follows CIS Benchmark principles and covers SSH hardening, password policy, kernel parameters, file attribute locking, and TCP wrappers.

---

## Step 1: Audit the Current System State

Before hardening, understand what you're working with.

```bash
# Check running services (in a real system)
systemctl list-units --type=service --state=running 2>/dev/null || echo "systemd not active in container"

# Check open ports
ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null

# Check current kernel parameters
sysctl kernel.randomize_va_space
sysctl net.ipv4.ip_forward
sysctl net.ipv4.conf.all.accept_redirects
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "sysctl kernel.randomize_va_space net.ipv4.ip_forward 2>/dev/null"
kernel.randomize_va_space = 2
net.ipv4.ip_forward = 1
```

> 💡 `kernel.randomize_va_space = 2` means full ASLR is enabled — memory addresses are randomized, making buffer overflow exploits much harder to execute reliably.

---

## Step 2: SSH Hardening — sshd_config

SSH is the primary remote access vector. Lock it down.

```bash
# Install openssh-server to inspect the config
apt-get update -qq && apt-get install -y -qq openssh-server

# View the default sshd_config
grep -E '#?PermitRootLogin|#?PasswordAuthentication|#?MaxAuthTries|#?AllowUsers' /etc/ssh/sshd_config
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "apt-get update -qq 2>/dev/null && apt-get install -y -qq openssh-server 2>/dev/null && grep -E '#?PermitRootLogin|#?PasswordAuthentication|#?MaxAuthTries' /etc/ssh/sshd_config"
#PermitRootLogin prohibit-password
#MaxAuthTries 6
#PasswordAuthentication yes
# PasswordAuthentication.  Depending on your PAM configuration,
# the setting of "PermitRootLogin without-password".
# PAM authentication, then enable this but set PasswordAuthentication
```

Apply hardened settings:

```bash
# Harden sshd_config
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config

# Add AllowUsers (replace with your actual username)
echo "AllowUsers secadmin" >> /etc/ssh/sshd_config

# Verify changes
grep -E 'PermitRootLogin|PasswordAuthentication|MaxAuthTries|AllowUsers' /etc/ssh/sshd_config | grep -v '^#'
```

📸 **Verified Output (after edits):**
```
PermitRootLogin no
PasswordAuthentication no
MaxAuthTries 3
AllowUsers secadmin
```

> 💡 `AllowUsers` creates an explicit allowlist. Any account not listed is denied SSH access even with valid credentials — this is a critical defense-in-depth layer.

---

## Step 3: Password Policy — /etc/login.defs

Configure system-wide password aging and length defaults.

```bash
# View current password defaults
grep -E '^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_MIN_LEN|^PASS_WARN_AGE' /etc/login.defs
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "grep -E '^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_MIN_LEN|^PASS_WARN_AGE' /etc/login.defs"
PASS_MAX_DAYS   99999
PASS_MIN_DAYS   0
PASS_MIN_LEN    8
PASS_WARN_AGE   7
```

Apply CIS-compliant password aging:

```bash
# CIS Benchmark: max 90 days, min 7 days, warn 14 days
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/' /etc/login.defs
sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   7/' /etc/login.defs
sed -i 's/^PASS_WARN_AGE.*/PASS_WARN_AGE   14/' /etc/login.defs

# Verify
grep -E '^PASS_MAX_DAYS|^PASS_MIN_DAYS|^PASS_WARN_AGE' /etc/login.defs
```

> 💡 `login.defs` changes only affect **new** accounts. Apply `chage` to existing users: `chage --maxdays 90 --mindays 7 --warndays 14 username`

---

## Step 4: PAM Password Quality — libpam-pwquality

Enforce password complexity via PAM.

```bash
apt-get install -y -qq libpam-pwquality

# Configure pwquality
cat >> /etc/security/pwquality.conf << 'EOF'
minlen = 14
minclass = 4
maxrepeat = 3
gecoscheck = 1
EOF

# Verify
grep -v '^#' /etc/security/pwquality.conf | grep -v '^$'
```

📸 **Verified Output:**
```
minlen = 14
minclass = 4
maxrepeat = 3
gecoscheck = 1
```

> 💡 `minclass = 4` requires all four character classes: uppercase, lowercase, digits, and symbols. This makes passwords far more resistant to dictionary attacks.

---

## Step 5: Kernel Hardening via sysctl

Harden the kernel against network attacks and memory exploits.

```bash
# View current ASLR level
sysctl kernel.randomize_va_space
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "sysctl kernel.randomize_va_space"
kernel.randomize_va_space = 2
```

Create a persistent hardening configuration:

```bash
cat > /etc/sysctl.d/99-hardening.conf << 'EOF'
# ASLR - Full randomization
kernel.randomize_va_space = 2

# Disable IP forwarding (unless this is a router)
net.ipv4.ip_forward = 0

# Disable ICMP redirect acceptance
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Enable SYN flood protection
net.ipv4.tcp_syncookies = 1

# Ignore ICMP broadcasts
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0

# Log martian packets
net.ipv4.conf.all.log_martians = 1

# Restrict dmesg access
kernel.dmesg_restrict = 1

# Restrict ptrace
kernel.yama.ptrace_scope = 1
EOF

# Apply settings
sysctl -p /etc/sysctl.d/99-hardening.conf 2>/dev/null || echo "sysctl apply (some restricted in container)"

cat /etc/sysctl.d/99-hardening.conf
```

---

## Step 6: File Attribute Locking with chattr

Prevent modification of critical config files — even by root.

```bash
# Install e2fsprogs if not present (provides chattr)
apt-get install -y -qq e2fsprogs 2>/dev/null || true

# Lock a sensitive file with immutable attribute
touch /etc/secure-banner.txt
echo "Authorized use only" > /etc/secure-banner.txt
chattr +i /etc/secure-banner.txt

# Verify the immutable flag
lsattr /etc/secure-banner.txt

# Try to modify (will fail)
echo "modification attempt" >> /etc/secure-banner.txt 2>&1 || echo "Write blocked — chattr +i working!"

# Remove the lock when needed
chattr -i /etc/secure-banner.txt
echo "Lock removed" && lsattr /etc/secure-banner.txt
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "touch /tmp/t && chattr +i /tmp/t && lsattr /tmp/t && echo test >> /tmp/t 2>&1 || echo 'Blocked!'"
----i---------e------- /tmp/t
Blocked!
```

> 💡 `chattr +i` sets the immutable bit at the filesystem level. Even `rm -f` fails. Use it to protect `/etc/passwd`, `/etc/shadow`, `/etc/sudoers` after hardening.

---

## Step 7: umask Hardening and /etc/hosts.deny

Tighten default file permissions and configure TCP wrappers.

```bash
# View current umask
umask
```

📸 **Verified Output:**
```
$ docker run --rm ubuntu:22.04 bash -c "umask"
0022
```

```bash
# Harden umask to 027 (no world permissions)
# Add to /etc/profile and /etc/bash.bashrc for all users
echo "umask 027" >> /etc/profile
echo "umask 027" >> /etc/bash.bashrc

# Configure TCP wrappers - deny all by default
cat > /etc/hosts.deny << 'EOF'
# /etc/hosts.deny - CIS Benchmark: deny all by default
ALL: ALL
EOF

# Allow specific services/hosts in /etc/hosts.allow
cat > /etc/hosts.allow << 'EOF'
# /etc/hosts.allow - Explicitly allowed connections
sshd: 192.168.1.0/24
sshd: 10.0.0.0/8
EOF

echo "=== hosts.deny ===" && cat /etc/hosts.deny
echo "=== hosts.allow ===" && cat /etc/hosts.allow
```

📸 **Verified Output:**
```
=== hosts.deny ===
# /etc/hosts.deny - CIS Benchmark: deny all by default
ALL: ALL
=== hosts.allow ===
# /etc/hosts.allow - Explicitly allowed connections
sshd: 192.168.1.0/24
sshd: 10.0.0.0/8
```

> 💡 TCP wrappers (`/etc/hosts.allow` and `/etc/hosts.deny`) provide network-level access control before a service even accepts a connection. Use `hosts.deny: ALL: ALL` as a baseline deny-all policy.

---

## Step 8: Capstone — Harden a Fresh Ubuntu Server

**Scenario:** Your team just provisioned a new Ubuntu 22.04 server exposed to the internet. You need to apply full CIS-level hardening before it goes into production.

```bash
# Full hardening script — simulate a production deployment
apt-get update -qq && apt-get install -y -qq openssh-server libpam-pwquality e2fsprogs 2>/dev/null

# 1. SSH Hardening
sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#MaxAuthTries.*/MaxAuthTries 3/' /etc/ssh/sshd_config
echo "ClientAliveInterval 300" >> /etc/ssh/sshd_config
echo "ClientAliveCountMax 2" >> /etc/ssh/sshd_config
echo "LoginGraceTime 60" >> /etc/ssh/sshd_config
echo "AllowUsers deploy" >> /etc/ssh/sshd_config

# 2. Password policy
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   90/' /etc/login.defs
sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   7/' /etc/login.defs

# 3. Kernel hardening
cat > /etc/sysctl.d/99-hardening.conf << 'EOF'
kernel.randomize_va_space = 2
net.ipv4.ip_forward = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
kernel.dmesg_restrict = 1
EOF

# 4. umask hardening
echo "umask 027" >> /etc/profile

# 5. TCP wrappers
echo "ALL: ALL" > /etc/hosts.deny
echo "sshd: 10.0.0.0/8" > /etc/hosts.allow

# 6. Lock critical files
chattr +i /etc/hosts.deny /etc/hosts.allow

# 7. Verify all changes
echo "=== SSH hardening ===" && grep -E '^PermitRootLogin|^PasswordAuthentication|^MaxAuthTries|^AllowUsers' /etc/ssh/sshd_config
echo "=== Password policy ===" && grep -E '^PASS_MAX_DAYS|^PASS_MIN_DAYS' /etc/login.defs
echo "=== ASLR ===" && cat /proc/sys/kernel/randomize_va_space
echo "=== hosts.deny ===" && cat /etc/hosts.deny
echo "=== Immutable files ===" && lsattr /etc/hosts.deny /etc/hosts.allow
```

📸 **Verified Output:**
```
=== SSH hardening ===
PermitRootLogin no
PasswordAuthentication no
MaxAuthTries 3
AllowUsers deploy
=== Password policy ===
PASS_MAX_DAYS   90
PASS_MIN_DAYS   7
=== ASLR ===
2
=== hosts.deny ===
ALL: ALL
=== Immutable files ===
----i---------e------- /etc/hosts.deny
----i---------e------- /etc/hosts.allow
```

---

## Summary

| Topic | Tool / File | Key Setting |
|-------|-------------|-------------|
| SSH hardening | `/etc/ssh/sshd_config` | `PermitRootLogin no`, `MaxAuthTries 3`, `AllowUsers` |
| Password aging | `/etc/login.defs` | `PASS_MAX_DAYS 90`, `PASS_MIN_DAYS 7` |
| Password complexity | `/etc/security/pwquality.conf` | `minlen=14`, `minclass=4` |
| ASLR | `sysctl kernel.randomize_va_space` | `= 2` (full randomization) |
| Network hardening | `/etc/sysctl.d/99-hardening.conf` | Disable redirects, enable SYN cookies |
| File locking | `chattr +i <file>` | Immutable bit blocks all writes |
| Default deny | `/etc/hosts.deny` | `ALL: ALL` |
| umask hardening | `/etc/profile` | `umask 027` |
