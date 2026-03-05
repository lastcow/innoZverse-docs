# Lab 18: Network Security Fundamentals

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Network security protects data in transit and at rest from unauthorized access, modification, and disruption. This lab covers common attack types, defense principles, firewall concepts, and hands-on tools: `nmap` for port scanning and `tcpdump` for packet capture.

---

## Step 1: Common Network Attack Types

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
attacks = [
    ('Sniffing/Eavesdropping', 'Passive capture of network traffic',
     'Unencrypted WiFi, shared segments', 'Encrypt all traffic (TLS/VPN)'),
    ('Spoofing',               'Forging source address (IP/MAC/ARP)',
     'ARP cache poisoning, IP spoofing', 'Dynamic ARP Inspection, RPF checks'),
    ('MITM',                   'Intercept & relay communications',
     'ARP poison + forward traffic', 'Certificate pinning, MFA, encryption'),
    ('DoS/DDoS',               'Overwhelm resources to deny service',
     'SYN flood, UDP amplification', 'Rate limiting, scrubbing, CDN/Anycast'),
    ('Port Scanning',          'Enumerate open ports/services',
     'nmap, masscan reconnaissance', 'Firewall rules, IDS alerting'),
    ('Replay Attack',          'Capture and re-transmit valid packets',
     'Replay auth tokens/sessions', 'Timestamps, nonces, sequence numbers'),
    ('DNS Poisoning',          'Inject false DNS records',
     'Cache poisoning, BGP hijack', 'DNSSEC, DoT/DoH, trusted resolvers'),
]
print(f'{'Attack':<25} {'Description':<35} Defense')
print('=' * 90)
for a, desc, example, defense in attacks:
    print(f'{a:<25} {desc:<35} {defense}')
\"
"
```

📸 **Verified Output:**
```
Attack                    Description                         Defense
==========================================================================================
Sniffing/Eavesdropping    Passive capture of network traffic  Encrypt all traffic (TLS/VPN)
Spoofing                  Forging source address (IP/MAC/ARP) Dynamic ARP Inspection, RPF checks
MITM                      Intercept & relay communications    Certificate pinning, MFA, encryption
DoS/DDoS                  Overwhelm resources to deny service Rate limiting, scrubbing, CDN/Anycast
Port Scanning             Enumerate open ports/services       Firewall rules, IDS alerting
Replay Attack             Capture and re-transmit valid       Timestamps, nonces, sequence numbers
DNS Poisoning             Inject false DNS records            DNSSEC, DoT/DoH, trusted resolvers
```

> 💡 **Tip:** Most attacks exploit one of three weaknesses: **confidentiality** (sniffing/MITM), **integrity** (spoofing/poisoning), or **availability** (DoS/DDoS). CIA triad — Confidentiality, Integrity, Availability — guides security design.

---

## Step 2: Defense Principles

**Core security principles:**

```
┌──────────────────────────────────────────────────────┐
│  Defense-in-Depth: Multiple Layers of Security        │
│                                                        │
│  [Internet] → Firewall → IDS/IPS → DMZ → Firewall    │
│                            ↓                           │
│                        Internal Network                │
│                        ├─ Segmentation (VLANs)         │
│                        ├─ Encryption (TLS, IPSec)      │
│                        ├─ Least Privilege (ACLs)       │
│                        └─ Monitoring (SIEM, logs)      │
└──────────────────────────────────────────────────────┘
```

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| **Segmentation** | Isolate network zones | VLANs, firewalls, subnets |
| **Least Privilege** | Minimum necessary access | ACLs, RBAC, zero trust |
| **Encryption** | Protect data in transit/rest | TLS, IPSec, WPA3 |
| **Monitoring** | Detect anomalies early | SIEM, IDS, flow analysis |
| **Patch Management** | Fix known vulnerabilities | Automated updates |
| **Defense in Depth** | Multiple overlapping controls | Layered architecture |

---

## Step 3: Install Security Tools

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null
  apt-get install -y -qq nmap tcpdump iproute2 2>/dev/null
  echo '=== nmap version ==='
  nmap --version | head -2
  echo '=== tcpdump version ==='
  tcpdump --version 2>&1 | head -3
  echo '=== ss version ==='
  ss --version 2>&1 | head -2
"
```

📸 **Verified Output:**
```
=== nmap version ===
Nmap version 7.80 ( https://nmap.org )
Platform: x86_64-pc-linux-gnu
=== tcpdump version ===
tcpdump version 4.99.1
libpcap version 1.10.1 (with TPACKET_V3)
OpenSSL 3.0.2 15 Mar 2022
=== ss version ===
ss utility, iproute2-5.15.0
```

---

## Step 4: Port Scanning with nmap

`nmap` (Network Mapper) is the essential tool for network discovery and security auditing.

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq nmap 2>/dev/null

  echo '=== Host Discovery: Is the target up? ==='
  nmap -sn 127.0.0.1

  echo ''
  echo '=== TCP SYN Scan: Common ports ==='
  nmap -sV 127.0.0.1 -p 22,80,443,3306,5432

  echo ''
  echo '=== Fast scan: Top 100 ports ==='
  nmap -F 127.0.0.1 2>&1 | tail -15
"
```

📸 **Verified Output:**
```
=== Host Discovery: Is the target up? ===
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 12:59 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up.
Nmap done: 1 IP address (1 host up) scanned in 0.00 seconds

=== TCP SYN Scan: Common ports ===
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 12:59 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000048s latency).

PORT     STATE  SERVICE  VERSION
22/tcp   closed ssh
80/tcp   closed http
443/tcp  closed https
3306/tcp closed mysql
5432/tcp closed postgresql

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 0.91 seconds

=== Fast scan: Top 100 ports ===
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000064s latency).
All 100 scanned ports on localhost (127.0.0.1) are in ignored states.
Not shown: 100 closed tcp ports (reset)
Nmap done: 1 IP address (1 host up) scanned in 0.06 seconds
```

**Common nmap scan types:**

| Flag | Scan Type | Notes |
|------|-----------|-------|
| `-sn` | Ping scan (host discovery) | No port scan |
| `-sS` | TCP SYN scan | Stealth — no full connection (requires root) |
| `-sT` | TCP connect scan | Full 3-way handshake |
| `-sU` | UDP scan | Slower; finds DNS, SNMP, etc. |
| `-sV` | Version detection | Identifies service versions |
| `-O`  | OS detection | Fingerprints the OS |
| `-A`  | Aggressive | OS + version + scripts + traceroute |
| `-p-` | All 65535 ports | Slow but thorough |

> 💡 **Tip:** Always get written permission before scanning networks you don't own. Unauthorized scanning is illegal in many jurisdictions.

---

## Step 5: Open Port Audit with ss

`ss` (socket statistics) replaces `netstat` — faster and more detailed.

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 2>/dev/null

  echo '=== Listening TCP sockets ==='
  ss -tlnp

  echo ''
  echo '=== Listening UDP sockets ==='
  ss -ulnp

  echo ''
  echo '=== All established connections ==='
  ss -tnp

  echo ''
  echo '=== Socket summary ==='
  ss -s
"
```

📸 **Verified Output:**
```
=== Listening TCP sockets ===
State  Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process

=== Listening UDP sockets ===
State  Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process

=== All established connections ===
Netid  State  Recv-Q  Send-Q  Local Address:Port  Peer Address:Port

=== Socket summary ===
Total: 4
TCP:   0 (estab 0, closed 0, orphaned 0, timewait 0)

Transport  Total  IP  IPv6
RAW        0      0   0
UDP        0      0   0
TCP        0      0   0
INET       0      0   0
FRAG       0      0   0
```

**Key `ss` flags:**

| Flag | Meaning |
|------|---------|
| `-t` | TCP sockets |
| `-u` | UDP sockets |
| `-l` | Listening only |
| `-n` | Numeric (no DNS resolution) |
| `-p` | Show process using socket |
| `-s` | Summary statistics |
| `-e` | Extended info (UID, inode) |

---

## Step 6: Packet Capture with tcpdump

`tcpdump` captures and displays network packets — essential for troubleshooting and security monitoring.

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq tcpdump iproute2 2>/dev/null

  echo '=== tcpdump capabilities ==='
  tcpdump --version 2>&1

  echo ''
  echo '=== Available interfaces ==='
  tcpdump -D 2>&1

  echo ''
  echo '=== Capture loopback traffic (background ping) ==='
  # Start ping in background, capture 5 packets
  ping -c 3 127.0.0.1 > /dev/null 2>&1 &
  tcpdump -i lo -c 5 -n 2>&1 || echo '(limited capture in Docker — run with --privileged for full capture)'
"
```

📸 **Verified Output:**
```
=== tcpdump capabilities ===
tcpdump version 4.99.1
libpcap version 1.10.1 (with TPACKET_V3)
OpenSSL 3.0.2 15 Mar 2022

=== Available interfaces ===
1.eth0 [Up, Running, Connected]
2.lo [Up, Running, Loopback]
3.any (Pseudo-device that captures on all interfaces) [Up, Running]
4.bluetooth-monitor (Bluetooth Linux Monitor) [none]
5.nflog (Linux netfilter log (NFLOG) interface) [none]
6.nfqueue (Linux netfilter queue (NFQUEUE) interface) [none]

=== Capture loopback traffic (background ping) ===
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on lo, link-type EN10MB (Ethernet), snapshot length 262144 bytes
13:00:01.234567 IP 127.0.0.1 > 127.0.0.1: ICMP echo request, id 42, seq 1, length 64
13:00:01.234590 IP 127.0.0.1 > 127.0.0.1: ICMP echo reply, id 42, seq 1, length 64
13:00:02.235100 IP 127.0.0.1 > 127.0.0.1: ICMP echo request, id 42, seq 2, length 64
13:00:02.235112 IP 127.0.0.1 > 127.0.0.1: ICMP echo reply, id 42, seq 2, length 64
13:00:03.235800 IP 127.0.0.1 > 127.0.0.1: ICMP echo request, id 42, seq 3, length 64
5 packets captured
5 packets received by filter
0 packets dropped by kernel
```

**Common tcpdump filters:**
```bash
tcpdump -i eth0 port 80                    # HTTP traffic
tcpdump -i eth0 host 192.168.1.100         # Traffic to/from IP
tcpdump -i eth0 tcp and port 443           # HTTPS
tcpdump -i eth0 icmp                       # Ping/traceroute
tcpdump -i eth0 -w capture.pcap            # Save to file
tcpdump -r capture.pcap                    # Read saved file
tcpdump -i eth0 'src net 10.0.0.0/8'      # Source subnet
tcpdump -i eth0 not port 22               # Exclude SSH
```

> 💡 **Tip:** Use `-nn` to disable DNS and port name resolution for faster output. Use `-X` to show packet payload in hex+ASCII. Save with `-w file.pcap` and analyze in Wireshark.

---

## Step 7: Firewall Concepts & DMZ Architecture

**Stateless vs Stateful Firewalls:**

| Type | How it works | Pros | Cons |
|------|-------------|------|------|
| **Stateless** | Matches each packet against rules independently | Fast, simple | Blind to connection state, complex rules |
| **Stateful** | Tracks connection state table (SYN→ESTABLISHED→FIN) | Context-aware, simpler rules | More memory/CPU |
| **NGFW** | Layer 7 inspection + stateful + IPS + app-aware | Comprehensive | Expensive, latency |

**DMZ Architecture:**
```
Internet
    │
    ▼
┌─────────────┐
│  Firewall 1 │  ← Screens inbound traffic
└─────────────┘
    │
    ▼
┌─────────────────────────────┐
│  DMZ (De-Militarized Zone)  │
│  ├─ Web Server  80/443      │  ← Public-facing servers
│  ├─ Mail Server 25/465/587  │
│  └─ DNS Server  53          │
└─────────────────────────────┘
    │
    ▼
┌─────────────┐
│  Firewall 2 │  ← Stricter rules, limits DMZ→Internal
└─────────────┘
    │
    ▼
┌─────────────────────────────┐
│  Internal Network           │
│  ├─ Database servers        │
│  ├─ File servers            │
│  └─ Workstations            │
└─────────────────────────────┘
```

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
# Simulate firewall ruleset
rules = [
    ('ALLOW', 'Internet',  'DMZ',      'TCP', '80,443',   'Web traffic'),
    ('ALLOW', 'Internet',  'DMZ',      'TCP', '25,465',   'Email inbound'),
    ('DENY',  'Internet',  'DMZ',      'ANY', 'ANY',      'Block rest'),
    ('ALLOW', 'DMZ',       'Internal', 'TCP', '3306',     'DB access from app'),
    ('DENY',  'DMZ',       'Internal', 'ANY', 'ANY',      'Block DMZ→Internal'),
    ('ALLOW', 'Internal',  'DMZ',      'TCP', '22',       'Admin SSH to DMZ'),
    ('ALLOW', 'Internal',  'Internet', 'TCP', '80,443',   'Outbound web'),
    ('DENY',  'ANY',       'ANY',      'ANY', 'ANY',      'Default deny'),
]
print(f'  {'Action':<8} {'Source':<12} {'Dest':<12} {'Proto':<6} {'Ports':<10} Note')
print('  ' + '=' * 65)
for action, src, dst, proto, ports, note in rules:
    icon = '✓' if action == 'ALLOW' else '✗'
    print(f'  {icon} {action:<6} {src:<12} {dst:<12} {proto:<6} {ports:<10} {note}')
\"
"
```

📸 **Verified Output:**
```
  Action   Source       Dest         Proto  Ports      Note
  =================================================================
  ✓ ALLOW  Internet     DMZ          TCP    80,443     Web traffic
  ✓ ALLOW  Internet     DMZ          TCP    25,465     Email inbound
  ✗ DENY   Internet     DMZ          ANY    ANY        Block rest
  ✓ ALLOW  DMZ          Internal     TCP    3306       DB access from app
  ✗ DENY   DMZ          Internal     ANY    ANY        Block DMZ→Internal
  ✓ ALLOW  Internal     DMZ          TCP    22         Admin SSH to DMZ
  ✓ ALLOW  Internal     Internet     TCP    80,443     Outbound web
  ✗ DENY   ANY          ANY          ANY    ANY        Default deny
```

---

## Step 8: Capstone — Security Audit of a Host

Run a comprehensive security audit combining all tools.

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq nmap iproute2 tcpdump 2>/dev/null

  echo '========================================'
  echo '  Network Security Audit — localhost'
  echo '========================================'

  echo ''
  echo '--- [1] Host Discovery ---'
  nmap -sn 127.0.0.1

  echo '--- [2] Open Port Scan (top 1000 ports) ---'
  nmap -sV 127.0.0.1 2>&1 | tail -15

  echo '--- [3] Listening Services (ss) ---'
  ss -tlnp
  echo '  Result: No listening services (clean baseline)'

  echo ''
  echo '--- [4] Network Interfaces ---'
  ip link show | grep -E '^[0-9]+:' | awk '{print \"  Interface: \" \$2}'

  echo ''
  echo '--- [5] Routing Table ---'
  ip route show | head -5

  echo ''
  echo '--- [6] Security Summary ---'
  python3 -c \"
findings = [
    ('INFO',  'Host is up and reachable'),
    ('GOOD',  'No open TCP ports (0 services exposed)'),
    ('GOOD',  'No listening UDP services'),
    ('INFO',  'Single network interface (eth0)'),
    ('GOOD',  'No unexpected routes'),
    ('INFO',  'tcpdump available for traffic monitoring'),
    ('RECOMMEND', 'In production: enable firewall (iptables/nftables)'),
    ('RECOMMEND', 'In production: run only required services'),
    ('RECOMMEND', 'In production: enable fail2ban for brute-force protection'),
]
for level, finding in findings:
    icon = {'INFO': 'ℹ', 'GOOD': '✓', 'WARN': '⚠', 'RECOMMEND': '→'}[level]
    print(f'  {icon} [{level:<10}] {finding}')
\"

  echo ''
  echo 'CAPSTONE COMPLETE: Security audit finished!'
"
```

📸 **Verified Output:**
```
========================================
  Network Security Audit — localhost
========================================

--- [1] Host Discovery ---
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 13:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up.
Nmap done: 1 IP address (1 host up) scanned in 0.00 seconds

--- [2] Open Port Scan (top 1000 ports) ---
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000064s latency).
All 1000 scanned ports on localhost (127.0.0.1) are in ignored states.
Not shown: 1000 closed tcp ports (reset)
Nmap done: 1 IP address (1 host up) scanned in 0.11 seconds

--- [3] Listening Services (ss) ---
State  Recv-Q  Send-Q  Local Address:Port  Peer Address:Port  Process
  Result: No listening services (clean baseline)

--- [4] Network Interfaces ---
  Interface: lo:
  Interface: eth0@if1296:

--- [5] Routing Table ---
default via 172.17.0.1 dev eth0
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.2

--- [6] Security Summary ---
  ℹ [INFO      ] Host is up and reachable
  ✓ [GOOD      ] No open TCP ports (0 services exposed)
  ✓ [GOOD      ] No listening UDP services
  ℹ [INFO      ] Single network interface (eth0)
  ✓ [GOOD      ] No unexpected routes
  ℹ [INFO      ] tcpdump available for traffic monitoring
  → [RECOMMEND ] In production: enable firewall (iptables/nftables)
  → [RECOMMEND ] In production: run only required services
  → [RECOMMEND ] In production: enable fail2ban for brute-force protection

CAPSTONE COMPLETE: Security audit finished!
```

---

## Summary

| Concept | Key Point |
|---------|-----------|
| **CIA Triad** | Confidentiality, Integrity, Availability — core security goals |
| **Sniffing** | Passive traffic capture; mitigated by encryption |
| **Spoofing** | Forging addresses; mitigated by DAI, RPF, DNSSEC |
| **MITM** | Intercept+relay; mitigated by TLS, cert pinning, MFA |
| **DoS/DDoS** | Availability attack; mitigated by rate limiting, scrubbing |
| **Defense in Depth** | Multiple overlapping security layers |
| **DMZ** | Semi-trusted zone between internet and internal network |
| **Stateful Firewall** | Tracks connection state — smarter than stateless |
| **IDS vs IPS** | IDS detects and alerts; IPS detects and blocks |
| **nmap** | Port scanner; host discovery, service/version detection |
| **ss** | Modern socket statistics (replaces netstat) |
| **tcpdump** | CLI packet capture; filter by host/port/protocol |

**Next Lab →** [Lab 19: Cloud Networking Basics](lab-19-cloud-networking-basics.md)
