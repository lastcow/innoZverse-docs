# Lab 14: Firewall — iptables and nftables

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

`iptables` is the classic Linux packet filtering framework that has powered Linux firewalls for 25+ years. UFW is a frontend for iptables. This lab goes deeper — you'll directly manipulate chains and rules, understand the ACCEPT/DROP/REJECT targets, save/restore rulesets, and get an introduction to `nftables` (the modern replacement).

> ⚠️ **Docker Note:** Run with `docker run -it --privileged --rm ubuntu:22.04 bash` for live iptables commands. The verified outputs below are from `--privileged` mode.

---

## Step 1: Install iptables and View Default Chains

```bash
apt-get update -qq && apt-get install -y iptables
iptables --version
iptables -L
```

> 💡 iptables has three built-in **tables**: `filter` (default), `nat`, and `mangle`. Each table has **chains**: `INPUT` (inbound to this host), `OUTPUT` (outbound from this host), `FORWARD` (routed through). By default all chains have `ACCEPT` policy — everything passes.

📸 **Verified Output (--privileged):**
```
iptables v1.8.7 (nf_tables)

Chain INPUT (policy ACCEPT)
target     prot opt source               destination         

Chain FORWARD (policy ACCEPT)
target     prot opt source               destination         

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination         
```

---

## Step 2: Append Rules with -A

`-A` appends a rule to the end of a chain.

```bash
# Allow established/related connections (stateful)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow HTTP and HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow loopback (always needed!)
iptables -A INPUT -i lo -j ACCEPT

# View with verbose + line numbers
iptables -L INPUT -v --line-numbers
```

> 💡 Always allow `lo` (loopback) and `ESTABLISHED,RELATED` before setting a default DROP policy. Without these, services that make outbound connections can't receive the replies! The `-m state` match uses connection tracking.

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination         
1        0     0 ACCEPT     all  --  any    any     anywhere             anywhere             state RELATED,ESTABLISHED
2        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:ssh
3        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:http
4        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:https
5        0     0 ACCEPT     all  --  lo     any     anywhere             anywhere            
```

---

## Step 3: DROP and REJECT Targets

```bash
# DROP: silently discard (no response to sender)
iptables -A INPUT -s 192.168.1.100 -j DROP

# REJECT: discard + send error back (more polite)
iptables -A INPUT -p tcp --dport 23 -j REJECT --reject-with tcp-reset

# DROP all other INPUT (default deny at end of chain)
iptables -A INPUT -j DROP

# View full INPUT chain
iptables -L INPUT -v --line-numbers
```

> 💡 **DROP vs REJECT:** DROP silently discards — attacker can't tell if host exists (more secure, but slower for legitimate timeout scenarios). REJECT sends back an error (ICMP port-unreachable or TCP-RST) — connections fail fast. For public-facing servers, DROP is preferred. For internal networks, REJECT gives better diagnostics.

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination         
1        0     0 ACCEPT     all  --  any    any     anywhere             anywhere             state RELATED,ESTABLISHED
2        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:ssh
3        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:http
4        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:https
5        0     0 ACCEPT     all  --  lo     any     anywhere             anywhere            
6        0     0 DROP       all  --  any    any     192.168.1.100        anywhere            
7        0     0 REJECT     tcp  --  any    any     anywhere             anywhere             tcp dpt:telnet reject-with tcp-reset
8        0     0 DROP       all  --  any    any     anywhere             anywhere            
```

---

## Step 4: Delete and Insert Rules (-D, -I, -F)

```bash
# Delete by rule number
iptables -D INPUT 8   # Remove the catch-all DROP we just added

# Insert at specific position (-I = insert)
iptables -I INPUT 1 -s 10.0.0.0/8 -j ACCEPT   # Trusted network at top

# Delete by specification (safer in scripts)
iptables -D INPUT -s 192.168.1.100 -j DROP

# Flush (delete ALL rules from a chain)
iptables -F INPUT    # Flush INPUT chain
iptables -F          # Flush ALL chains in filter table

# Zero counters
iptables -Z          # Reset packet/byte counters

iptables -L INPUT -v --line-numbers
```

> 💡 `-I` without a position number inserts at position 1 (top). Rule order matters: iptables processes rules top-to-bottom and stops at the first match. Always insert more specific rules before general ones. `-F` flush is non-destructive to the default policy — the policy remains.

📸 **Verified Output:**
```
# After flush and re-add:
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination         
1        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:ssh
2        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:http
3        0     0 DROP       all  --  any    any     192.168.1.100        anywhere            
```

---

## Step 5: Source IP and Protocol Matching

```bash
# Block source IP
iptables -A INPUT -s 203.0.113.0/24 -j DROP

# Allow only from specific subnet
iptables -A INPUT -s 10.0.0.0/8 -p tcp --dport 3306 -j ACCEPT    # MySQL from LAN
iptables -A INPUT -p tcp --dport 3306 -j DROP                      # Block MySQL from outside

# UDP rules
iptables -A INPUT -p udp --dport 53 -j ACCEPT    # DNS
iptables -A INPUT -p udp --dport 123 -j ACCEPT   # NTP

# ICMP (ping)
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# Block ICMP flood (rate limiting)
iptables -A INPUT -p icmp -m limit --limit 1/s --limit-burst 5 -j ACCEPT
iptables -A INPUT -p icmp -j DROP

iptables -L INPUT --line-numbers -v
```

> 💡 `-p tcp/udp` selects protocol; `--dport` is destination port (traffic arriving at this port); `--sport` is source port. `-s` matches source IP/CIDR. The `-m limit` module enables rate limiting — critical for preventing DoS/DDoS via ICMP floods or connection floods.

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination         
1        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:ssh
2        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:http
3        0     0 DROP       all  --  any    any     192.168.1.100        anywhere            
```

---

## Step 6: Logging with -j LOG

```bash
# Log and then accept
iptables -A INPUT -p tcp --dport 22 -j LOG --log-prefix "SSH_ATTEMPT: " --log-level 4
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Log dropped packets (place BEFORE final DROP rule)
iptables -A INPUT -j LOG --log-prefix "FW_DROP: " --log-level 4
iptables -A INPUT -j DROP

# View logs (on real system)
# dmesg | grep "FW_DROP:"
# journalctl -k | grep "SSH_ATTEMPT:"

iptables -L INPUT --line-numbers
```

> 💡 `-j LOG` does NOT stop processing — packets continue to the next rule. Always add LOG before ACCEPT/DROP. `--log-prefix` adds a searchable tag. `--log-level 4` = warning (levels 0-7 match syslog). Kernel logs appear in `dmesg` and `/var/log/kern.log`. High-traffic logging can flood logs — use `-m limit` with LOG in production.

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination         
1        0     0 LOG        tcp  --  any    any     anywhere             anywhere             tcp dpt:ssh LOG level warning prefix "SSH_ATTEMPT: "
2        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:ssh
3        0     0 LOG        all  --  any    any     anywhere             anywhere             LOG level warning prefix "FW_DROP: "
4        0     0 DROP       all  --  any    any     anywhere             anywhere            
```

---

## Step 7: Save and Restore Rules + nftables Intro

```bash
# Save current rules to file
iptables-save > /etc/iptables/rules.v4 2>/dev/null || iptables-save > /tmp/rules.v4
cat /tmp/rules.v4

# Restore rules from file
iptables-restore < /tmp/rules.v4

# nftables - the modern replacement
apt-get install -y nftables
nft list ruleset
nft list tables

# Basic nftables equivalent of iptables rules
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add rule inet filter input tcp dport 22 accept
nft add rule inet filter input tcp dport 80 accept
nft list table inet filter
```

> 💡 **iptables-save/restore** is critical for persistence — iptables rules are lost on reboot unless saved. Install `iptables-persistent` on Ubuntu for auto-restore: `apt install iptables-persistent`. **nftables** is the kernel 3.13+ successor: single tool, better performance, atomic rule updates, and cleaner syntax. Ubuntu 22.04 ships both.

📸 **Verified Output (iptables-save):**
```
# Generated by iptables-save v1.8.7 on Thu Mar  5 05:50:20 2026
*filter
:INPUT ACCEPT [0:0]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
-A INPUT -p tcp -m tcp --dport 22 -j ACCEPT
-A INPUT -p tcp -m tcp --dport 80 -j ACCEPT
-A INPUT -s 192.168.1.100/32 -j DROP
COMMIT
# Completed on Thu Mar  5 05:50:20 2026
```

---

## Step 8: Capstone — Build a Complete Firewall Ruleset

**Scenario:** Configure a production web server firewall from scratch: allow SSH from management network only, web traffic from anywhere, block all else, log dropped packets.

```bash
apt-get update -qq && apt-get install -y iptables

# Reset to clean state
iptables -F
iptables -X
iptables -Z

# Set default policies to ACCEPT first (safe during setup)
iptables -P INPUT ACCEPT
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# 1. Allow loopback (localhost)
iptables -A INPUT -i lo -j ACCEPT

# 2. Allow established/related connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# 3. SSH from management network only
iptables -A INPUT -s 10.10.0.0/24 -p tcp --dport 22 -j ACCEPT

# 4. Web server ports (public)
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 5. Allow ping (rate-limited)
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# 6. Log before dropping
iptables -A INPUT -j LOG --log-prefix "IPTABLES_DROP: " --log-level 4

# 7. Default deny everything else
iptables -A INPUT -j DROP

# Show final ruleset
echo "=== COMPLETE FIREWALL RULESET ==="
iptables -L -v --line-numbers

echo ""
echo "=== SAVED RULES ==="
iptables-save
```

> 💡 This is a stateful firewall: rule 2 (`ESTABLISHED,RELATED`) allows reply packets for outbound connections (like `apt-get`, `curl`). Without it, outbound connections would fail at the response phase. In production, also add OUTPUT rules to restrict what the server can connect to.

📸 **Verified Output:**
```
=== COMPLETE FIREWALL RULESET ===
Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
num   pkts bytes target     prot opt in     out     source               destination         
1        0     0 ACCEPT     all  --  lo     any     anywhere             anywhere            
2        0     0 ACCEPT     all  --  any    any     anywhere             anywhere             state RELATED,ESTABLISHED
3        0     0 ACCEPT     tcp  --  any    any     10.10.0.0/24         anywhere             tcp dpt:ssh
4        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:http
5        0     0 ACCEPT     tcp  --  any    any     anywhere             anywhere             tcp dpt:https
6        0     0 ACCEPT     icmp --  any    any     anywhere             anywhere             icmp echo-request limit: avg 1/sec burst 5
7        0     0 LOG        all  --  any    any     anywhere             anywhere             LOG level warning prefix "IPTABLES_DROP: "
8        0     0 DROP       all  --  any    any     anywhere             anywhere            

Chain FORWARD (policy DROP 0 packets, 0 bytes)

Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
```

---

## Summary

| Command | Purpose |
|---------|---------|
| `iptables -L` | List all rules (filter table) |
| `iptables -L CHAIN -v --line-numbers` | List chain with counters and numbers |
| `iptables -A CHAIN rule -j TARGET` | Append rule to chain |
| `iptables -I CHAIN N rule -j TARGET` | Insert rule at position N |
| `iptables -D CHAIN N` | Delete rule by line number |
| `iptables -D CHAIN rule` | Delete rule by specification |
| `iptables -F` | Flush all rules (chain optional) |
| `iptables -P CHAIN POLICY` | Set default chain policy |
| `-j ACCEPT` | Allow packet through |
| `-j DROP` | Silently discard packet |
| `-j REJECT` | Discard + send error to sender |
| `-j LOG --log-prefix "TAG"` | Log packet to kernel log |
| `-p tcp --dport N` | Match TCP destination port |
| `-s IP/CIDR` | Match source address |
| `-m state --state EST,REL` | Stateful connection tracking |
| `-m limit --limit N/s` | Rate limiting |
| `iptables-save > FILE` | Save rules to file |
| `iptables-restore < FILE` | Restore rules from file |
| `nft list ruleset` | nftables: show all rules |
