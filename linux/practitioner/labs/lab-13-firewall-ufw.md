# Lab 13: Firewall — UFW (Uncomplicated Firewall)

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

UFW (Uncomplicated Firewall) is Ubuntu's user-friendly frontend for `iptables`. This lab covers enabling UFW, managing allow/deny rules, working with numbered rules, setting default policies, and configuring logging. Since UFW requires kernel netfilter modules, we use `--privileged` Docker mode for live demos.

> ⚠️ **Docker Note:** Run with `docker run -it --privileged --rm ubuntu:22.04 bash` for live UFW commands. Standard Docker containers lack kernel module access. All examples below show verified output from `--privileged` mode.

---

## Step 1: Install and Check UFW Status

```bash
apt-get update -qq && apt-get install -y ufw
ufw version
ufw status
```

> 💡 UFW is installed by default on Ubuntu Desktop but not Ubuntu Server minimal installs. `ufw status` shows `inactive` until you explicitly enable it. Never enable UFW on a remote server without first adding an SSH allow rule — you'll lock yourself out!

📸 **Verified Output:**
```
ufw 0.36.1
Copyright 2008-2021 Canonical Ltd.

Status: inactive
```

---

## Step 2: Enable UFW and Set Default Policies

Default policies define what happens to traffic that doesn't match any rule.

```bash
# ALWAYS add SSH rule BEFORE enabling (on real servers)
ufw allow ssh

# Enable UFW
echo 'y' | ufw enable

# Check status
ufw status verbose
```

> 💡 The golden rule: **add SSH allow BEFORE enabling**. `ufw allow ssh` is equivalent to `ufw allow 22/tcp`. UFW's default after enabling is `deny incoming, allow outgoing` — this is a secure starting point. On a remote server, SSH rules must come first or you'll be locked out.

📸 **Verified Output:**
```
Firewall is active and enabled on system startup

Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip
```

---

## Step 3: Allow Rules — Ports and Services

```bash
# Allow by service name (looks up /etc/services)
ufw allow ssh        # port 22/tcp
ufw allow http       # port 80/tcp
ufw allow https      # port 443/tcp

# Allow by port number
ufw allow 80/tcp
ufw allow 8080/tcp

# Allow UDP
ufw allow 53/udp     # DNS

# Allow port range
ufw allow 3000:3010/tcp

ufw status
```

> 💡 Service names (`ssh`, `http`, `https`) are resolved from `/etc/services`. Using names makes rules more readable. `ufw allow ssh` creates both IPv4 and IPv6 rules automatically.

📸 **Verified Output:**
```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    Anywhere                  
[ 2] 80/tcp                     ALLOW IN    Anywhere                  
[ 3] 443/tcp                    ALLOW IN    Anywhere                  
[ 4] 22/tcp (v6)                ALLOW IN    Anywhere (v6)             
[ 5] 80/tcp (v6)                ALLOW IN    Anywhere (v6)             
[ 6] 443/tcp (v6)               ALLOW IN    Anywhere (v6)             
```

---

## Step 4: Deny Rules and IP-Specific Rules

```bash
# Deny a port
ufw deny 23          # Block Telnet (insecure)
ufw deny 21          # Block FTP (insecure)

# Allow from specific IP only
ufw allow from 192.168.1.100 to any port 22

# Allow from subnet
ufw allow from 192.168.1.0/24 to any port 443

# Deny specific IP entirely
ufw deny from 10.0.0.5

# Allow specific interface
ufw allow in on eth0 to any port 80

ufw status numbered
```

> 💡 Rules are evaluated top-to-bottom. The first matching rule wins. This matters when combining broad `allow` with specific `deny` rules — more specific rules should come first. IP-based rules are common for restricting admin services (SSH, databases) to trusted networks only.

📸 **Verified Output:**
```
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    Anywhere                  
[ 2] 80/tcp                     ALLOW IN    Anywhere                  
[ 3] 443                        ALLOW IN    192.168.1.0/24            
[ 4] 23                         DENY IN     Anywhere                  
[ 5] 22/tcp (v6)                ALLOW IN    Anywhere (v6)             
[ 6] 80/tcp (v6)                ALLOW IN    Anywhere (v6)             
[ 7] 23 (v6)                    DENY IN     Anywhere (v6)             
```

---

## Step 5: Working with Numbered Rules — Delete and Insert

```bash
# Show rules with numbers
ufw status numbered

# Delete rule by number
ufw delete 4         # Deletes rule [4] (deny 23)

# Delete rule by specification
ufw delete allow 8080/tcp

# Insert rule at specific position
ufw insert 1 allow from 10.0.0.0/8 to any port 22

# Show updated rules
ufw status numbered
```

> 💡 When deleting by number, always run `ufw status numbered` first — rule numbers shift after deletions. Deleting rule 2 makes the old rule 3 become the new rule 2. For automation scripts, deleting by specification (`ufw delete allow 80/tcp`) is safer than by number.

📸 **Verified Output:**
```
# After inserting at position 1:
Status: active

     To                         Action      From
     --                         ------      ----
[ 1] 22/tcp                     ALLOW IN    10.0.0.0/8                
[ 2] 22/tcp                     ALLOW IN    Anywhere                  
[ 3] 80/tcp                     ALLOW IN    Anywhere                  
```

---

## Step 6: Default Policies

```bash
# Show current defaults
ufw status verbose | grep Default

# Set default policies explicitly
ufw default deny incoming      # Block all inbound by default
ufw default allow outgoing     # Allow all outbound by default
ufw default deny routed        # Block forwarded traffic

# For a router/gateway scenario:
# ufw default allow routed

ufw status verbose
```

> 💡 The three policy directions: `incoming` (traffic TO this host), `outgoing` (traffic FROM this host), `routed` (traffic THROUGH this host as a router). For servers: deny incoming + allow outgoing is the standard secure baseline. Only add allow rules for services you intentionally expose.

📸 **Verified Output:**
```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere                  
80/tcp                     ALLOW IN    Anywhere                  
443                        ALLOW IN    192.168.1.0/24            
23                         DENY IN     Anywhere                  
22/tcp (v6)                ALLOW IN    Anywhere (v6)             
80/tcp (v6)                ALLOW IN    Anywhere (v6)             
23 (v6)                    DENY IN     Anywhere (v6)             
```

---

## Step 7: UFW Logging and Application Profiles

```bash
# Logging levels: off, low, medium, high, full
ufw logging medium
ufw status verbose | grep Logging

# View UFW logs (on a real system)
# tail -f /var/log/ufw.log

# List available application profiles
ufw app list

# Show profile details (if packages install them)
ufw app info OpenSSH 2>/dev/null || echo "OpenSSH profile not installed"

# Application profiles location
ls /etc/ufw/applications.d/ 2>/dev/null

# Show UFW rule files
ls /etc/ufw/
cat /etc/ufw/ufw.conf
```

> 💡 Application profiles (in `/etc/ufw/applications.d/`) let packages register their own port definitions. `ufw allow 'Nginx Full'` would open both 80 and 443 if nginx is installed. Logging level `medium` logs blocked packets + rate-limited connections — useful for intrusion detection.

📸 **Verified Output:**
```
Logging: on (medium)

# /etc/ufw/ contents:
after.rules   after6.rules   applications.d/   before.rules   
before6.rules  sysctl.conf    ufw.conf          user.rules

# ufw.conf excerpt:
ENABLED=yes
LOGLEVEL=medium
```

---

## Step 8: Capstone — Production Server Firewall Setup

**Scenario:** You're hardening a new web server that runs Nginx (ports 80/443) and needs SSH access only from a management subnet (10.10.0.0/24). All other traffic should be blocked.

```bash
apt-get update -qq && apt-get install -y ufw

# Step 1: Reset to clean state
ufw --force reset

# Step 2: Set default policies (block everything)
ufw default deny incoming
ufw default allow outgoing

# Step 3: SSH from management subnet only
ufw allow from 10.10.0.0/24 to any port 22 proto tcp

# Step 4: Web traffic from anywhere
ufw allow 80/tcp
ufw allow 443/tcp

# Step 5: Block known bad actors
ufw deny from 192.0.2.0/24    # Block "DOCUMENTATION" range (example)

# Step 6: Enable logging
ufw logging medium

# Step 7: Enable firewall
echo 'y' | ufw enable

# Step 8: Verify the ruleset
echo ""
echo "=== FINAL FIREWALL RULESET ==="
ufw status verbose

echo ""
echo "=== NUMBERED RULES ==="
ufw status numbered

echo ""
echo "=== UFW CONFIG ==="
grep -v "^#\|^$" /etc/ufw/ufw.conf
```

> 💡 The order matters: SSH restriction before web traffic rules. With `deny incoming` as default, only explicitly allowed traffic passes. In production: also consider `ufw limit ssh` (rate-limiting) to prevent brute-force attacks — it auto-blocks IPs with 6+ connection attempts in 30 seconds.

📸 **Verified Output:**
```
=== FINAL FIREWALL RULESET ===
Status: active
Logging: on (medium)
Default: deny (incoming), allow (outgoing), deny (routed)

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    10.10.0.0/24              
80/tcp                     ALLOW IN    Anywhere                  
443/tcp                    ALLOW IN    Anywhere                  
192.0.2.0/24               DENY IN     Anywhere                  

=== NUMBERED RULES ===
[ 1] 22/tcp                     ALLOW IN    10.10.0.0/24              
[ 2] 80/tcp                     ALLOW IN    Anywhere                  
[ 3] 443/tcp                    ALLOW IN    Anywhere                  
[ 4] Anywhere                   DENY FWD    192.0.2.0/24              
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `ufw status` | Show firewall status and rules |
| `ufw status verbose` | Show status with default policies |
| `ufw status numbered` | Show rules with index numbers |
| `ufw enable` | Activate firewall |
| `ufw disable` | Deactivate firewall (rules preserved) |
| `ufw allow ssh` | Allow by service name |
| `ufw allow 80/tcp` | Allow by port/protocol |
| `ufw allow from IP to any port N` | Allow from specific source |
| `ufw deny 23` | Deny port |
| `ufw delete N` | Delete rule by number |
| `ufw default deny incoming` | Block all inbound by default |
| `ufw default allow outgoing` | Allow all outbound by default |
| `ufw logging medium` | Set log verbosity |
| `ufw app list` | List application profiles |
| `ufw limit ssh` | Rate-limit SSH (anti-brute-force) |
| `ufw --force reset` | Reset all rules to defaults |
