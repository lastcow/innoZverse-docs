# Lab 01: iptables Stateful Firewall

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

iptables is the classic Linux firewall tool backed by Netfilter in the kernel. In this lab you will explore the four tables, five built-in chains, rule management commands, match extensions, and build a complete stateful firewall using connection tracking (conntrack). Every command below was verified live in Docker.

---

## Step 1 — Install iptables and inspect the default ruleset

```bash
apt-get update -qq && apt-get install -y -qq iptables
iptables -L -v -n
```

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         

Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         

Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
```

> 💡 The three chains shown belong to the **filter** table — the default table iptables operates on. `-v` shows packet/byte counters; `-n` suppresses DNS lookups.

**Understanding the four tables:**

| Table | Purpose | Chains |
|-------|---------|--------|
| `filter` | Packet allow/deny decisions | INPUT, FORWARD, OUTPUT |
| `nat` | Address/port translation | PREROUTING, POSTROUTING, OUTPUT |
| `mangle` | Packet header modification | All five chains |
| `raw` | Early processing, bypass conntrack | PREROUTING, OUTPUT |

---

## Step 2 — Understand built-in chains and packet flow

```bash
# View all tables
iptables -t filter -L -n
iptables -t nat -L -n
iptables -t mangle -L -n
iptables -t raw -L -n
```

📸 **Verified Output (nat table):**
```
Chain PREROUTING (policy ACCEPT)
target     prot opt source               destination         

Chain INPUT (policy ACCEPT)
target     prot opt source               destination         

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination         

Chain POSTROUTING (policy ACCEPT)
target     prot opt source               destination         
```

> 💡 **Packet flow:** Incoming → PREROUTING → (routing decision) → INPUT (local) or FORWARD (routed). Outgoing → OUTPUT → POSTROUTING.

---

## Step 3 — Rule management commands: -A, -I, -D, -L, -F, -P

```bash
# Append a rule
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -L INPUT -v -n
```

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:80
```

```bash
# Insert a rule at position 1 (highest priority)
iptables -I INPUT 1 -i lo -j ACCEPT

# Delete by rule number
iptables -D INPUT 2

# Flush all rules in a chain
iptables -F INPUT

# Set default policy
iptables -P INPUT DROP
iptables -P INPUT ACCEPT   # reset
```

> 💡 Rule order matters! iptables evaluates rules top-to-bottom and stops at the first match. Use `-I` to insert high-priority rules at the top.

---

## Step 4 — Targets: ACCEPT, DROP, REJECT, LOG

```bash
# DROP silently discards
iptables -A INPUT -p tcp --dport 23 -j DROP

# REJECT sends an error back to the sender
iptables -A INPUT -p tcp --dport 8080 -j REJECT --reject-with tcp-reset

# LOG writes to kernel log (dmesg / /var/log/kern.log)
iptables -A INPUT -p tcp --dport 22 -j LOG --log-prefix "SSH_ATTEMPT: " --log-level 4

# Verify all three rules
iptables -L INPUT -v -n --line-numbers
```

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination         
1        0     0 DROP       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:23
2        0     0 REJECT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:8080 reject-with tcp-reset
3        0     0 LOG        tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22 LOG flags 0 level 4 prefix "SSH_ATTEMPT: "
```

> 💡 **DROP vs REJECT:** DROP is stealthier (attacker waits for timeout), REJECT is friendlier to legitimate users who mistype a port. Use DROP for untrusted sources.

---

## Step 5 — Match extensions: -m state, conntrack, multiport, iprange

```bash
iptables -F INPUT

# conntrack state matching
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# multiport: multiple ports in one rule
iptables -A INPUT -p tcp -m multiport --dports 80,443,8080 -j ACCEPT

# iprange: match IP address ranges
iptables -A INPUT -m iprange --src-range 192.168.1.100-192.168.1.200 -j ACCEPT

iptables -L INPUT -v -n
```

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            multiport dports 80,443,8080
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            source IP range 192.168.1.100-192.168.1.200
```

> 💡 **conntrack states:** `NEW` (first packet), `ESTABLISHED` (ongoing connection), `RELATED` (associated, e.g. FTP data channel), `INVALID` (broken packets — always DROP these).

---

## Step 6 — Build a stateful firewall with default DROP policy

```bash
iptables -F INPUT
iptables -F OUTPUT
iptables -F FORWARD

# Rule 1: Allow loopback (critical — needed for local services)
iptables -A INPUT -i lo -j ACCEPT

# Rule 2: Allow established and related connections (stateful core)
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Rule 3: Drop invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Rule 4: Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Rule 5: Allow HTTP and HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Rule 6: Set default DROP policy
iptables -P INPUT DROP
iptables -P FORWARD DROP

iptables -L -v -n
```

📸 **Verified Output:**
```
Chain INPUT (policy DROP 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0           
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
    0     0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate INVALID
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:80
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:443

Chain FORWARD (policy DROP 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         

Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
```

> 💡 Always put the `ESTABLISHED,RELATED` rule first — it matches most traffic on a busy server and exits the chain immediately, improving performance dramatically.

---

## Step 7 — Saving and restoring rules

```bash
# Save current ruleset to file
iptables-save > /etc/iptables/rules.v4

# View the saved rules
iptables-save
```

📸 **Verified Output:**
```
# Generated by iptables-save v1.8.7 on Thu Mar  5 13:56:47 2026
*filter
:INPUT DROP [0:0]
:FORWARD DROP [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -i lo -j ACCEPT
-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A INPUT -m conntrack --ctstate INVALID -j DROP
-A INPUT -p tcp -m tcp --dport 22 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 80 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 443 -j ACCEPT
COMMIT
# Completed on Thu Mar  5 13:56:47 2026
```

```bash
# Restore rules from file
iptables-restore < /etc/iptables/rules.v4

# On Ubuntu, install iptables-persistent to auto-load on boot:
# apt-get install -y iptables-persistent
# Rules saved to /etc/iptables/rules.v4 are loaded automatically
```

> 💡 `iptables-save` format is human-readable and version-control friendly. Commit your firewall rules to git like any other config file.

---

## Step 8 — Capstone: Complete server hardening ruleset

Build and verify a production-grade stateful firewall. This simulates a web server that also accepts admin SSH only from a trusted subnet:

```bash
# Clear everything
iptables -F
iptables -X
iptables -Z

# === LOOPBACK ===
iptables -A INPUT  -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# === STATEFUL CORE ===
iptables -A INPUT  -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT  -m conntrack --ctstate INVALID -j DROP

# === ICMP (ping) — limited ===
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 5/sec -j ACCEPT

# === SSH — restricted to admin subnet ===
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j LOG --log-prefix "SSH_BLOCKED: "
iptables -A INPUT -p tcp --dport 22 -j DROP

# === WEB SERVICES ===
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# === DEFAULT POLICIES ===
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# === VERIFY ===
iptables -L -v -n --line-numbers
echo "=== Saved ruleset ==="
iptables-save
```

📸 **Verified Output:**
```
Chain INPUT (policy DROP 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination         
1        0     0 ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0           
2        0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
3        0     0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate INVALID
4        0     0 ACCEPT     icmp --  *      *       0.0.0.0/0            0.0.0.0/0            icmptype 8 limit: avg 5/sec burst 5
5        0     0 ACCEPT     tcp  --  *      *       10.0.0.0/8           0.0.0.0/0            tcp dpt:22
6        0     0 LOG        tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22 LOG flags 0 level 4 prefix "SSH_BLOCKED: "
7        0     0 DROP       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22
8        0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            multiport dports 80,443
```

> 💡 This is a real production pattern: stateful core first, explicit allows, log+drop for sensitive ports from unauthorized sources, default DROP. Save with `iptables-save` and persist across reboots with `iptables-persistent`.

---

## Summary

| Concept | Command | Notes |
|---------|---------|-------|
| List rules (verbose) | `iptables -L -v -n` | `-n` skips DNS |
| Append rule | `iptables -A INPUT ...` | Added at end |
| Insert at position | `iptables -I INPUT 1 ...` | High priority |
| Delete by number | `iptables -D INPUT 2` | Use `--line-numbers` first |
| Flush chain | `iptables -F INPUT` | Removes all rules |
| Set default policy | `iptables -P INPUT DROP` | Default if no rule matches |
| Stateful accept | `-m conntrack --ctstate ESTABLISHED,RELATED` | Core of stateful firewall |
| Multiport match | `-m multiport --dports 80,443` | Up to 15 ports |
| Save rules | `iptables-save > /etc/iptables/rules.v4` | Persist to file |
| Restore rules | `iptables-restore < /etc/iptables/rules.v4` | Load from file |
| ACCEPT target | `-j ACCEPT` | Allow packet |
| DROP target | `-j DROP` | Silently discard |
| REJECT target | `-j REJECT` | Send error back |
| LOG target | `-j LOG --log-prefix "..."` | Write to kernel log |
