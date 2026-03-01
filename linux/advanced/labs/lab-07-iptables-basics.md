# Lab 7: iptables Basics

## 🎯 Objective
List, inspect, and understand iptables rules; work with INPUT, OUTPUT, and FORWARD chains; and save/restore rule sets.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access with sudo privileges
- Basic understanding of TCP/IP ports

## 🔬 Lab Instructions

### Step 1: View Current iptables Rules
```bash
sudo iptables -L
# Chain INPUT (policy ACCEPT)
# target     prot opt source               destination
#
# Chain FORWARD (policy ACCEPT)
# target     prot opt source               destination
#
# Chain OUTPUT (policy ACCEPT)
# target     prot opt source               destination

# Verbose output with packet counts
sudo iptables -L -v
# Chain INPUT (policy ACCEPT 12345 packets, 987K bytes)
#  pkts bytes target prot opt in out source destination
```

### Step 2: View Rules with Line Numbers and No DNS Lookup
```bash
# -n: no DNS lookup (faster)
# --line-numbers: show rule numbers for easy deletion
sudo iptables -L -n --line-numbers
# Chain INPUT (policy ACCEPT)
# num  target     prot opt source               destination
# 1    ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0   ctstate RELATED,ESTABLISHED
```

### Step 3: Understand Chains and Targets
```bash
# Chains:
# INPUT   - packets destined for this host
# OUTPUT  - packets originating from this host
# FORWARD - packets routing through this host

# Targets:
# ACCEPT  - allow the packet
# DROP    - silently discard (no response to sender)
# REJECT  - discard with ICMP error (sender gets notification)
# LOG     - log to kernel log (dmesg/syslog)

# View all tables (-t specifies table: filter, nat, mangle)
sudo iptables -t filter -L -n
sudo iptables -t nat -L -n
```

### Step 4: Allow an Incoming Port
```bash
# Allow incoming SSH (already likely allowed, but explicit)
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
# -A INPUT: append rule to INPUT chain
# -p tcp: protocol
# --dport 22: destination port
# -j ACCEPT: jump to ACCEPT target

# Allow HTTP and HTTPS
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

sudo iptables -L INPUT -n --line-numbers
```

### Step 5: Allow Established Connections and Loopback
```bash
# Allow loopback interface (critical for local services)
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established/related connections (stateful)
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

sudo iptables -L INPUT -n
# ACCEPT  all -- 0.0.0.0/0  0.0.0.0/0  (lo)
# ACCEPT  all -- 0.0.0.0/0  0.0.0.0/0  ctstate RELATED,ESTABLISHED
```

### Step 6: Block an IP Address
```bash
# Block all traffic from a specific IP
sudo iptables -A INPUT -s 192.0.2.100 -j DROP
# -s: source IP

# Block a range (CIDR)
sudo iptables -A INPUT -s 192.0.2.0/24 -j DROP

# Verify
sudo iptables -L INPUT -n | grep 192.0.2
# DROP  all  --  192.0.2.100  0.0.0.0/0
```

### Step 7: Insert and Delete Rules
```bash
# Insert at specific position (not append)
sudo iptables -I INPUT 1 -s 10.0.0.50 -j ACCEPT
# -I INPUT 1: insert as rule #1

# View with line numbers
sudo iptables -L INPUT -n --line-numbers

# Delete rule by number
sudo iptables -D INPUT 1

# Delete by rule specification
sudo iptables -D INPUT -s 192.0.2.100 -j DROP
sudo iptables -D INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -D INPUT -p tcp --dport 443 -j ACCEPT
```

### Step 8: Flush Rules (Clear All)
```bash
# Flush specific chain
sudo iptables -F INPUT

# Flush all chains
sudo iptables -F

# Flush and reset policies to ACCEPT
sudo iptables -F
sudo iptables -X    # delete user-defined chains
sudo iptables -Z    # zero packet counters

echo "All rules flushed — back to default ACCEPT"
```

### Step 9: Save and Restore Rules
```bash
sudo apt install -y iptables-persistent 2>/dev/null || true

# Save current rules
sudo iptables-save | sudo tee /etc/iptables/rules.v4
# *filter
# :INPUT ACCEPT [0:0]
# :FORWARD ACCEPT [0:0]
# :OUTPUT ACCEPT [0:0]
# COMMIT

# Restore rules
sudo iptables-restore < /etc/iptables/rules.v4

# Alternative without iptables-persistent:
sudo iptables-save > /tmp/ipt_backup.rules
sudo iptables-restore < /tmp/ipt_backup.rules
```

### Step 10: Basic Firewall Policy Script
```bash
cat > ~/basic_firewall.sh << 'EOF'
#!/bin/bash
# Basic iptables firewall — default deny, allow SSH + established

# Flush existing rules
iptables -F
iptables -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow ICMP ping
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

echo "Firewall rules applied"
iptables -L -n
EOF
echo "Script created at ~/basic_firewall.sh"
# IMPORTANT: Test thoroughly before applying policy DROP on a remote server
```

## ✅ Verification
```bash
sudo iptables -L -n --line-numbers
# Verify expected rules are present

# Check SSH is still allowed
sudo iptables -L INPUT -n | grep ':22'
```

## 📝 Summary
- `iptables -L -n --line-numbers` lists all rules without DNS lookups
- `-A` appends; `-I n` inserts at position; `-D` deletes a rule
- Chains: INPUT (inbound), OUTPUT (outbound), FORWARD (routed packets)
- Targets: ACCEPT, DROP (silent), REJECT (with error), LOG
- Always allow loopback and ESTABLISHED connections before setting DROP policy
- `iptables-save` and `iptables-restore` persist rules across sessions
