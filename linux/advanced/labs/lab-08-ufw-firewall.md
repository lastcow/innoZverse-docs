# Lab 8: UFW Firewall

## 🎯 Objective
Configure Ubuntu's Uncomplicated Firewall (UFW): enable/disable, allow/deny rules, check status, and use application profiles.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access with sudo privileges
- Basic understanding of ports and protocols

## 🔬 Lab Instructions

### Step 1: Check UFW Status
```bash
sudo ufw status
# Status: inactive
# or
# Status: active
# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW       Anywhere

sudo ufw status verbose
# Status: active
# Logging: on (low)
# Default: deny (incoming), allow (outgoing), deny (routed)
```

### Step 2: Enable UFW (Allow SSH First!)
```bash
# CRITICAL: Allow SSH before enabling to avoid lockout
sudo ufw allow ssh
# Rules updated
# Rules updated (v6)

# Enable UFW
sudo ufw enable
# Command may disrupt existing ssh connections. Proceed with operation (y|n)? y
# Firewall is active and enabled on system startup

sudo ufw status
# Status: active
```

### Step 3: Allow Ports by Number and Name
```bash
# Allow by port number
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8080/tcp

# Allow by service name (from /etc/services)
sudo ufw allow http    # port 80
sudo ufw allow https   # port 443

# Allow UDP
sudo ufw allow 53/udp

sudo ufw status
# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW       Anywhere
# 80/tcp                     ALLOW       Anywhere
# 443/tcp                    ALLOW       Anywhere
# 8080/tcp                   ALLOW       Anywhere
```

### Step 4: Allow Specific Source IPs
```bash
# Allow from a specific IP
sudo ufw allow from 10.0.0.10

# Allow from IP to specific port
sudo ufw allow from 10.0.0.0/24 to any port 5432
# (Allow PostgreSQL from internal network only)

# Allow from subnet to any port
sudo ufw allow from 192.168.1.0/24

sudo ufw status numbered
```

### Step 5: Deny and Reject Rules
```bash
# Deny (silently drop)
sudo ufw deny from 192.0.2.100

# Deny a port
sudo ufw deny 23/tcp    # block telnet

# Reject (send error back to sender)
sudo ufw reject 23/tcp

sudo ufw status numbered
# [ 1] 22/tcp                     ALLOW IN    Anywhere
# [ 2] 80/tcp                     ALLOW IN    Anywhere
# ...
```

### Step 6: Delete Rules
```bash
# View rules with numbers
sudo ufw status numbered
# [ 6] 23/tcp                     DENY IN     Anywhere

# Delete by number
sudo ufw delete 6

# Delete by rule specification
sudo ufw delete allow 8080/tcp
sudo ufw delete allow from 192.168.1.0/24

sudo ufw status
```

### Step 7: Application Profiles
```bash
# UFW includes application profiles from /etc/ufw/applications.d/
sudo ufw app list
# Available applications:
#   OpenSSH
#   Nginx Full
#   Nginx HTTP
#   Nginx HTTPS
#   Apache Full
#   Apache

# View profile details
sudo ufw app info OpenSSH
# Profile: OpenSSH
# Title: Secure Shell Server
# Description: OpenSSH is a free implementation of the Secure Shell protocol.
# Ports: 22/tcp

# Allow by application name
sudo ufw allow 'OpenSSH'
sudo ufw allow 'Nginx Full'
```

### Step 8: Logging
```bash
# Enable logging
sudo ufw logging on
# Logging enabled

# Set log level
sudo ufw logging medium    # options: off, low, medium, high, full

# View UFW logs
sudo tail -20 /var/log/ufw.log 2>/dev/null || sudo journalctl -k | grep UFW | tail -10
# Mar  1 06:01:23 server kernel: [UFW BLOCK] IN=eth0 OUT= MAC=... SRC=192.0.2.100 DST=10.0.0.5 ...
```

### Step 9: Default Policies
```bash
# View current defaults
sudo ufw status verbose | grep Default
# Default: deny (incoming), allow (outgoing), deny (routed)

# Change default policies
sudo ufw default deny incoming    # block all inbound by default
sudo ufw default allow outgoing   # allow all outbound by default
sudo ufw default deny forward     # block routing

# After changing defaults, re-check your allow rules are still in place
sudo ufw status
```

### Step 10: Disable and Reset UFW
```bash
# Disable UFW (rules stay but firewall is inactive)
sudo ufw disable
# Firewall stopped and disabled on system startup

# Reset UFW completely (removes all rules)
sudo ufw reset
# Resetting all rules to installed defaults. Proceed with operation (y|n)? y
# ...

# Re-enable with minimal ruleset
sudo ufw allow ssh
sudo ufw enable
sudo ufw status
# Status: active
# To   Action  From
# --   ------  ----
# 22   ALLOW   Anywhere
```

## ✅ Verification
```bash
sudo ufw status verbose
# Status: active
# Default: deny (incoming), allow (outgoing)

sudo ufw status numbered
# [1] 22/tcp ALLOW IN Anywhere

sudo ufw app list | grep OpenSSH
# OpenSSH
```

## 📝 Summary
- Always `ufw allow ssh` before `ufw enable` to prevent lockout
- `ufw allow PORT/proto` or `ufw allow from IP to any port PORT`
- Application profiles in `/etc/ufw/applications.d/` simplify common services
- `ufw status numbered` shows rules with numbers for easy deletion
- `ufw delete N` removes rule by number; `ufw delete allow PORT` by specification
- `ufw logging on` enables firewall log to `/var/log/ufw.log`
