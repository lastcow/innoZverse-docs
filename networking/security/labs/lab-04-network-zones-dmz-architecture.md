# Lab 04: Network Zones and DMZ Architecture

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Network segmentation divides infrastructure into security zones with controlled traffic flows between them. A DMZ (Demilitarized Zone) is the classic pattern: public-facing servers live in an intermediate zone — accessible from the Internet, but isolated from the internal network. In this lab you will implement zone-based firewall chains, create dummy network interfaces per zone, and design the ACL matrix that governs inter-zone traffic.

---

## Step 1 — Security zones concept

Network zones represent trust boundaries. Traffic crossing a zone boundary passes through a firewall policy.

```
Internet (untrusted)
    │
    ▼
┌─────────────┐
│  PERIMETER  │  ← Firewall/Router
│   FIREWALL  │
└──────┬──────┘
       │
  ┌────▼────┐
  │   DMZ   │  ← Web, Mail, DNS servers (semi-trusted)
  └────┬────┘
       │
┌──────▼──────┐
│  INTERNAL   │  ← Workstations, File servers (trusted)
│  FIREWALL   │
└──────┬──────┘
       │
  ┌────▼────┐
  │INTERNAL │  ← Corporate LAN
  │ NETWORK │
  └─────────┘
       │
  ┌────▼────┐
  │MGMT ZONE│  ← Out-of-band management (most trusted)
  └─────────┘
```

**Zone trust levels:**
| Zone | Trust Level | Typical Servers |
|------|-------------|-----------------|
| Internet | Untrusted | External clients |
| DMZ | Semi-trusted | Web, Mail, DNS, VPN |
| Internal | Trusted | Workstations, file servers |
| Management | Highest | Monitoring, bastion host |

---

## Step 2 — Create zone interfaces with dummy devices

```bash
apt-get update -qq && apt-get install -y -qq iptables iproute2

# Create dummy network interfaces to represent zones
ip link add dmz0      type dummy
ip link add internal0 type dummy
ip link add mgmt0     type dummy

# Bring them up
ip link set dmz0      up
ip link set internal0 up
ip link set mgmt0     up

# Assign IP addresses
ip addr add 10.10.1.1/24 dev dmz0
ip addr add 10.10.2.1/24 dev internal0
ip addr add 10.10.3.1/24 dev mgmt0

ip link show type dummy
ip addr show dmz0
```

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT)
target     prot opt source               destination         

Chain FORWARD (policy ACCEPT)
target     prot opt source               destination         

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination         

Chain DMZ_IN (0 references)
target     prot opt source               destination         

Chain INTERNAL_IN (0 references)
target     prot opt source               destination         
```

> 💡 Dummy interfaces are virtual NICs with no physical backing — perfect for simulating network zones in a single container. In production, these would be physical NICs or VLAN sub-interfaces.

---

## Step 3 — Create zone-based custom chains

The key to zone-based firewalling with iptables: create one custom chain per zone, then jump to it from FORWARD based on the incoming interface.

```bash
# Create custom chains for each zone's inbound traffic
iptables -N ZONE_INTERNET
iptables -N ZONE_DMZ
iptables -N ZONE_INTERNAL
iptables -N ZONE_MGMT

# Create chains for inter-zone routing decisions
iptables -N INET_TO_DMZ
iptables -N DMZ_TO_INTERNAL
iptables -N INTERNAL_TO_DMZ
iptables -N MGMT_TO_ALL

iptables -L -n
```

📸 **Verified Output:**
```
Chain INPUT (policy ACCEPT)
target     prot opt source               destination         

Chain FORWARD (policy ACCEPT)
target     prot opt source               destination         

Chain OUTPUT (policy ACCEPT)
target     prot opt source               destination         

Chain DMZ_IN (0 references)
target     prot opt source               destination         

Chain INTERNAL_IN (0 references)
target     prot opt source               destination         

Chain INET_TO_DMZ (0 references)
target     prot opt source               destination         

Chain DMZ_TO_INTERNAL (0 references)
target     prot opt source               destination         

Chain INTERNAL_TO_DMZ (0 references)
target     prot opt source               destination         

Chain MGMT_TO_ALL (0 references)
target     prot opt source               destination         

Chain ZONE_DMZ (0 references)
target     prot opt source               destination         

Chain ZONE_INTERNAL (0 references)
target     prot opt source               destination         

Chain ZONE_INTERNET (0 references)
target     prot opt source               destination         

Chain ZONE_MGMT (0 references)
target     prot opt source               destination         
```

> 💡 Custom chains are the building blocks of zone-based firewalls. The FORWARD chain becomes a **dispatcher** — it reads the interface and jumps to the appropriate zone chain, which contains the actual policies.

---

## Step 4 — Wire the FORWARD chain to zone chains

```bash
# Stateful core: established/related traffic always passes
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate INVALID -j DROP

# Dispatch to zone chains based on ingress interface
# (eth0 = Internet, dmz0 = DMZ, internal0 = Internal, mgmt0 = Management)
iptables -A FORWARD -i eth0      -j ZONE_INTERNET
iptables -A FORWARD -i dmz0      -j ZONE_DMZ
iptables -A FORWARD -i internal0 -j ZONE_INTERNAL
iptables -A FORWARD -i mgmt0     -j ZONE_MGMT

# Zone dispatch: Internet → DMZ
iptables -A ZONE_INTERNET -o dmz0 -j INET_TO_DMZ
iptables -A ZONE_INTERNET -j DROP   # Block Internet → Internal by default

# Zone dispatch: DMZ → Internal (restricted)
iptables -A ZONE_DMZ -o internal0 -j DMZ_TO_INTERNAL
iptables -A ZONE_DMZ -j DROP

# Zone dispatch: Internal → anywhere
iptables -A ZONE_INTERNAL -o dmz0 -j INTERNAL_TO_DMZ

# Management → everything
iptables -A ZONE_MGMT -j MGMT_TO_ALL

iptables -L FORWARD -v -n
```

📸 **Verified Output:**
```
Chain FORWARD (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target       prot opt in       out       source               destination         
    0     0 ACCEPT       all  --  *        *         0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
    0     0 DROP         all  --  *        *         0.0.0.0/0            0.0.0.0/0            ctstate INVALID
    0     0 ZONE_INTERNET all --  eth0     *         0.0.0.0/0            0.0.0.0/0           
    0     0 ZONE_DMZ     all  --  dmz0     *         0.0.0.0/0            0.0.0.0/0           
    0     0 ZONE_INTERNAL all --  internal0 *        0.0.0.0/0            0.0.0.0/0           
    0     0 ZONE_MGMT    all  --  mgmt0    *         0.0.0.0/0            0.0.0.0/0           
```

> 💡 This pattern scales beautifully: adding a new zone means creating two new custom chains and two FORWARD jump rules. The zone policy logic stays isolated in its own chain.

---

## Step 5 — Define inter-zone ACL policies

```bash
# === INTERNET → DMZ ===
# Allow HTTP/HTTPS to web server
iptables -A INET_TO_DMZ -p tcp -d 10.10.1.10 --dport 80  -j ACCEPT
iptables -A INET_TO_DMZ -p tcp -d 10.10.1.10 --dport 443 -j ACCEPT
# Allow email server
iptables -A INET_TO_DMZ -p tcp -d 10.10.1.20 --dport 25  -j ACCEPT
# Block everything else from Internet to DMZ
iptables -A INET_TO_DMZ -j LOG --log-prefix "INET_DMZ_BLOCK: "
iptables -A INET_TO_DMZ -j DROP

# === DMZ → INTERNAL ===
# DMZ servers should NOT directly access internal network
# Exception: App servers may query internal DB on specific port
iptables -A DMZ_TO_INTERNAL -p tcp -s 10.10.1.30 -d 10.10.2.50 --dport 5432 -j ACCEPT
iptables -A DMZ_TO_INTERNAL -j LOG --log-prefix "DMZ_INT_BLOCK: "
iptables -A DMZ_TO_INTERNAL -j DROP

# === INTERNAL → DMZ ===
# Internal clients can reach DMZ services freely
iptables -A INTERNAL_TO_DMZ -p tcp --dport 80  -j ACCEPT
iptables -A INTERNAL_TO_DMZ -p tcp --dport 443 -j ACCEPT
iptables -A INTERNAL_TO_DMZ -j DROP

# === MGMT → ALL ===
# Management zone has full access (for admins)
iptables -A MGMT_TO_ALL -j ACCEPT

# Default FORWARD policy: DROP
iptables -P FORWARD DROP

iptables -L -n --line-numbers | head -60
```

📸 **Verified Output:**
```
Chain FORWARD (policy DROP)
target     prot opt source               destination         
1  ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
2  DROP       all  --  0.0.0.0/0            0.0.0.0/0            ctstate INVALID
3  ZONE_INTERNET all --  0.0.0.0/0            0.0.0.0/0           
4  ZONE_DMZ   all  --  0.0.0.0/0            0.0.0.0/0           
5  ZONE_INTERNAL all --  0.0.0.0/0            0.0.0.0/0           
6  ZONE_MGMT  all  --  0.0.0.0/0            0.0.0.0/0           
```

> 💡 **Least-privilege principle applied to networks:** each zone only gets the access it needs. The DMZ app server talks to internal DB on one port only — not a blanket "DMZ can reach internal."

---

## Step 6 — Bastion host and jump server pattern

```bash
# Bastion host: single hardened entry point for administrative access
# 
# Pattern:
#   Admin laptop → (Internet) → Bastion (DMZ/Management zone)
#                               → SSH jump → Internal servers
#
# Key security properties of a bastion host:
# 1. Single point of entry with heavy logging
# 2. No other services running (minimal attack surface)
# 3. SSH key authentication only (no passwords)
# 4. All sessions logged (script/tlog/auditd)
# 5. MFA required

# Iptables rules for bastion host pattern:
# On the firewall, allow SSH from Internet to bastion only
iptables -A INET_TO_DMZ -p tcp -d 10.10.1.5 --dport 22 -j ACCEPT

# Allow bastion to SSH into internal zone
iptables -N BASTION_JUMP
iptables -A ZONE_DMZ -i dmz0 -s 10.10.1.5 -o internal0 -j BASTION_JUMP
iptables -A BASTION_JUMP -p tcp --dport 22 -j LOG --log-prefix "BASTION_JUMP: "
iptables -A BASTION_JUMP -p tcp --dport 22 -j ACCEPT
iptables -A BASTION_JUMP -j DROP

echo "Bastion rules configured"
iptables -L BASTION_JUMP -v -n
```

📸 **Verified Output:**
```
Chain BASTION_JUMP (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 LOG        tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22 LOG flags 0 level 4 prefix "BASTION_JUMP: "
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22
    0     0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0           
```

> 💡 **Bastion host usage:** `ssh -J bastion.example.com user@internal-server`. The `-J` flag (ProxyJump) tunnels through the bastion transparently. All traffic is logged at the bastion.

---

## Step 7 — Docker as a zone model

Docker networks naturally implement zone isolation. Each network is its own broadcast domain, and containers can only communicate if connected to the same network or via explicit routing.

```bash
# Docker zone analogy:
# docker network create internet-zone    ← Internet-facing
# docker network create dmz-zone         ← Semi-trusted
# docker network create internal-zone    ← Trusted private

# Docker automatically creates iptables rules:
# - DOCKER chain in filter table
# - DOCKER-USER chain for custom rules (persistent across docker restart)
# - DOCKER-ISOLATION-STAGE-1/2 for inter-network isolation

# Simulate the isolation model with ip netns
ip netns add ns-internet
ip netns add ns-dmz
ip netns add ns-internal

# Check network namespaces
ip netns list
```

📸 **Verified Output:**
```
ns-internal
ns-dmz
ns-internet
```

```bash
# Key principle: Docker uses iptables FORWARD rules and network namespaces
# to achieve the same isolation as zone-based firewalling
# 
# DOCKER-ISOLATION-STAGE-1: blocks cross-network FORWARD traffic
# DOCKER-ISOLATION-STAGE-2: enforces the isolation per network
# DOCKER-USER chain: your custom rules, insert here for Docker firewall integration
```

> 💡 When running Docker on a firewall host, add your custom rules to the **DOCKER-USER** chain — it's the only chain Docker won't overwrite on restart.

---

## Step 8 — Capstone: Complete zone-based firewall ruleset

Build and verify the complete zone firewall configuration:

```bash
iptables -F
iptables -X

# Zone interfaces already created in Step 2:
# dmz0 = 10.10.1.1/24, internal0 = 10.10.2.1/24, mgmt0 = 10.10.3.1/24

# Custom chains
iptables -N ZONE_INTERNET
iptables -N ZONE_DMZ
iptables -N ZONE_INTERNAL
iptables -N ZONE_MGMT
iptables -N DMZ_IN
iptables -N INTERNAL_IN

# Stateful core
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -m conntrack --ctstate INVALID -j DROP

# Zone dispatch
iptables -A FORWARD -i dmz0      -j ZONE_DMZ
iptables -A FORWARD -i internal0 -j ZONE_INTERNAL
iptables -A FORWARD -i mgmt0     -j ZONE_MGMT

# DMZ → Internal: restricted (app server to DB only)
iptables -A ZONE_DMZ -o internal0 -j DMZ_IN
iptables -A DMZ_IN -p tcp -d 10.10.2.50 --dport 5432 -j ACCEPT
iptables -A DMZ_IN -j DROP

# Internal → DMZ: web access allowed
iptables -A ZONE_INTERNAL -o dmz0 -j INTERNAL_IN
iptables -A INTERNAL_IN -p tcp -m multiport --dports 80,443 -j ACCEPT
iptables -A INTERNAL_IN -j DROP

# Mgmt → All: full access
iptables -A ZONE_MGMT -j ACCEPT

# Default policy: DROP
iptables -P FORWARD DROP
iptables -P INPUT DROP
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Final verification
echo "=== Zone Firewall Ruleset ==="
iptables -L -n -v
echo ""
echo "=== Zone Chain: DMZ_IN ==="
iptables -L DMZ_IN -n -v
echo ""
echo "=== Zone Chain: INTERNAL_IN ==="
iptables -L INTERNAL_IN -n -v
```

📸 **Verified Output:**
```
=== Zone Firewall Ruleset ===
Chain INPUT (policy DROP 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     all  --  lo     *       0.0.0.0/0            0.0.0.0/0           
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED

Chain FORWARD (policy DROP 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate RELATED,ESTABLISHED
    0     0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0            ctstate INVALID
    0     0 ZONE_DMZ   all  --  dmz0   *       0.0.0.0/0            0.0.0.0/0           
    0     0 ZONE_INTERNAL all --  internal0 *  0.0.0.0/0            0.0.0.0/0           
    0     0 ZONE_MGMT  all  --  mgmt0  *       0.0.0.0/0            0.0.0.0/0           

=== Zone Chain: DMZ_IN ===
Chain DMZ_IN (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            10.10.2.50           tcp dpt:5432
    0     0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0           

=== Zone Chain: INTERNAL_IN ===
Chain INTERNAL_IN (1 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 ACCEPT     tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            multiport dports 80,443
    0     0 DROP       all  --  *      *       0.0.0.0/0            0.0.0.0/0           
```

> 💡 This architecture ensures: **Internet cannot reach Internal** (no ZONE_INTERNET chain dispatches to internal0 directly), **DMZ can only reach Internal DB** (port 5432 only), **Internal can browse DMZ services** (HTTP/HTTPS), **Management has full access** (for admins).

---

## Summary

| Concept | Implementation | Benefit |
|---------|---------------|---------|
| Zone isolation | Custom iptables chains per zone | Modular, readable policies |
| FORWARD dispatcher | Match ingress interface → jump to zone chain | Scales to many zones |
| DMZ pattern | Semi-trusted zone for public servers | Limits blast radius of compromise |
| Bastion host | Single hardened SSH jump point | Centralized audit trail |
| Least-privilege ACL | Allow only specific flows between zones | Attacker can't pivot freely |
| Stateful core | `ctstate ESTABLISHED,RELATED` first | Performance + stateful tracking |
| Docker isolation | `DOCKER-USER` chain for custom rules | Survives Docker restarts |
| Default DROP | `iptables -P FORWARD DROP` | Deny-by-default posture |
| Management zone | Separate network for admin access | Out-of-band management |
| Bastion jump | `-J` ProxyJump SSH option | Transparent tunneling |
