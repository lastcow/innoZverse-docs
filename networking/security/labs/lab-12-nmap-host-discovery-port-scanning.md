# Lab 12: Nmap Host Discovery and Port Scanning

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Nmap (Network Mapper) is the industry-standard open-source tool for network discovery and security auditing. This lab covers all major scan types, host discovery techniques, NSE scripts, output formats, timing templates, and firewall evasion — with real verified output from Docker.

---

## Step 1 — Install Nmap and Verify Version

```bash
apt-get update -qq && apt-get install -y nmap
nmap --version
```

📸 **Verified Output:**
```
Nmap version 7.80 ( https://nmap.org )
Platform: x86_64-pc-linux-gnu
Compiled with: liblua-5.3.6 openssl-3.0.2 nmap-libssh2-1.8.2 libz-1.2.11 libpcre-8.39 libpcap-1.10.1 nmap-libdnet-1.12 ipv6
Compiled without:
Available nsock engines: epoll poll select
```

> 💡 **Tip:** Always note the Nmap version before an engagement — NSE scripts and detection capabilities vary significantly between versions. Nmap 7.80+ includes >600 NSE scripts.

---

## Step 2 — Host Discovery

Before port scanning, confirm which hosts are alive:

```bash
# Ping sweep — no port scan
nmap -sn 127.0.0.1
```

📸 **Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 14:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up.
Nmap done: 1 IP address (1 host up) scanned in 0.00 seconds
```

### Host Discovery Techniques

| Option | Method | Use Case |
|--------|--------|----------|
| `-sn` | Ping sweep (no ports) | Quick host enumeration |
| `-Pn` | Skip ping, assume host up | Hosts behind ICMP-blocking firewalls |
| `-PS<ports>` | TCP SYN ping | Ping via SYN to specified ports |
| `-PA<ports>` | TCP ACK ping | Bypass stateful firewalls |
| `-PU<ports>` | UDP ping | Discover hosts responding to UDP |
| `-PE` | ICMP echo request | Traditional ping |
| `-PP` | ICMP timestamp | Alternative ICMP probe |

```bash
# Skip ping, force scan (for ICMP-blocked hosts)
nmap -Pn -p 80,443 127.0.0.1

# TCP SYN ping on port 80
nmap -PS80 -sn 127.0.0.1
```

---

## Step 3 — Scan Types

### SYN Scan (Stealth) — Default for root
```bash
nmap -sS 127.0.0.1 -p 80,443,8080
```

### TCP Connect Scan — Full 3-way handshake
```bash
nmap -sT -p 1-1024 127.0.0.1
```

📸 **Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 14:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.00058s latency).
All 1024 scanned ports on localhost (127.0.0.1) are closed

Nmap done: 1 IP address (1 host up) scanned in 0.21 seconds
```

### Scan Type Comparison

| Flag | Type | TCP Handshake | Logged? | Requires Root? |
|------|------|--------------|---------|----------------|
| `-sS` | SYN (Stealth) | Half-open | Sometimes | Yes |
| `-sT` | Connect | Full | Yes | No |
| `-sU` | UDP | N/A | Rarely | Yes |
| `-sN` | Null | No flags | Rarely | Yes |
| `-sF` | FIN | FIN only | Rarely | Yes |
| `-sX` | Xmas | FIN+PSH+URG | Rarely | Yes |
| `-sA` | ACK | ACK only | N/A | Yes |

> 💡 **Tip:** **Null, FIN, and Xmas** scans exploit RFC 793 — closed ports respond with RST, open ports ignore the packet. They bypass some older firewalls but **don't work on Windows** (Windows always sends RST).

---

## Step 4 — Service Version Detection and OS Fingerprinting

```bash
# Version detection
nmap -sV -p 22,80,443 127.0.0.1
```

📸 **Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 14:00 UTC
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 0.85 seconds
```

```bash
# OS detection (requires open + closed port)
nmap -O 127.0.0.1
```

📸 **Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 14:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000037s latency).
All 1000 scanned ports on localhost (127.0.0.1) are closed
Too many fingerprints match this host to give specific OS details
Network Distance: 0 hops

OS detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 2.07 seconds
```

> 💡 **Tip:** `-A` is the aggressive meta-flag combining `-sV -O -sC --traceroute`. Use it for comprehensive single-host enumeration: `nmap -A <target>`.

---

## Step 5 — Port States

Nmap reports six possible port states:

| State | Meaning |
|-------|---------|
| `open` | Application accepting connections |
| `closed` | Port reachable but no listener |
| `filtered` | Firewall blocking probe packets |
| `unfiltered` | Reachable, can't determine open/closed (ACK scan) |
| `open\|filtered` | Can't distinguish (UDP/Null/FIN/Xmas) |
| `closed\|filtered` | Can't distinguish (IP ID idle scan) |

```bash
# Show only open ports
nmap --open -p 1-65535 127.0.0.1

# Show reason for each port state
nmap --reason -p 22,80,443 127.0.0.1
```

---

## Step 6 — NSE Scripts and Output Formats

### NSE Script Categories

| Category | Description |
|----------|-------------|
| `auth` | Authentication bypass tests |
| `brute` | Credential brute-force |
| `default` | Safe, informative scripts (`-sC`) |
| `discovery` | Network/service enumeration |
| `exploit` | Active exploitation (use with caution) |
| `safe` | Non-disruptive scripts |
| `vuln` | Vulnerability checks |

```bash
# Run default scripts
nmap -sC -p 80,443 127.0.0.1

# Run banner grabbing script
nmap --script=banner -p 80 127.0.0.1
```

📸 **Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 14:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000090s latency).

PORT   STATE  SERVICE
80/tcp closed http

Nmap done: 1 IP address (1 host up) scanned in 0.60 seconds
```

### Output Formats

```bash
# Normal text output
nmap -oN scan_results.txt 192.168.1.0/24

# XML output (for tools like Metasploit/Faraday)
nmap -oX scan_results.xml 192.168.1.0/24

# Grepable output
nmap -oG scan_results.gnmap 192.168.1.0/24

# All formats simultaneously
nmap -oA scan_results 192.168.1.0/24
```

> 💡 **Tip:** Use `-oX` for integration with vulnerability management platforms. Tools like `ndiff` can compare two XML scan outputs to detect network changes over time.

---

## Step 7 — Timing Templates and Firewall Evasion

### Timing Templates

| Template | Name | Speed | Use Case |
|----------|------|-------|----------|
| `-T0` | Paranoid | Extremely slow (5min/probe) | IDS evasion |
| `-T1` | Sneaky | Very slow | Avoid detection |
| `-T2` | Polite | Slow | Reduce bandwidth impact |
| `-T3` | Normal | Default | Balanced |
| `-T4` | Aggressive | Fast | Reliable networks |
| `-T5` | Insane | Maximum | Fast LANs only |

```bash
# Aggressive timing (fast networks)
nmap -T4 -sn 127.0.0.1
```

📸 **Verified Output:**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 14:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up.
Nmap done: 1 IP address (1 host up) scanned in 0.00 seconds
```

### Firewall Evasion Techniques

```bash
# Fragment packets (8-byte fragments)
nmap -f 192.168.1.1

# Use decoy addresses to confuse IDS
nmap -D RND:10 192.168.1.1

# Spoof source port (bypass stateless ACL)
nmap --source-port 53 192.168.1.1

# Idle/zombie scan (completely stealthy)
nmap -sI <zombie_host> <target>

# Randomise target scan order
nmap --randomize-hosts 192.168.1.0/24

# Set maximum retries
nmap --max-retries 1 192.168.1.0/24
```

> 💡 **Tip:** Decoy scans (`-D`) make it appear that multiple hosts are scanning simultaneously. The real attacker IP is hidden among decoys. However, this only works if the decoy IPs are reachable — otherwise the forged packets won't be routed.

---

## Step 8 — Capstone: Comprehensive Network Audit

**Scenario:** Perform a full audit of a target subnet, identifying open services, OS versions, and potential vulnerabilities.

```bash
# Phase 1: Host discovery
nmap -sn 10.0.0.0/24 -oG /tmp/hosts.gnmap
grep "Up" /tmp/hosts.gnmap | awk '{print $2}' > /tmp/alive_hosts.txt
cat /tmp/alive_hosts.txt

# Phase 2: Full port scan on alive hosts
nmap -iL /tmp/alive_hosts.txt -sS -p- -T4 --open -oN /tmp/ports.txt

# Phase 3: Service/version detection on open ports
nmap -iL /tmp/alive_hosts.txt -sV -sC --open -oA /tmp/services

# Phase 4: Vulnerability check
nmap -iL /tmp/alive_hosts.txt --script=vuln --open -oN /tmp/vulns.txt

# Simulate on localhost (all phases at once)
nmap -sT -sV -p 1-1024 --open --reason -T4 127.0.0.1

# Parse XML output for open ports
nmap -oX /tmp/scan.xml -p 1-65535 127.0.0.1
grep 'state="open"' /tmp/scan.xml
```

📸 **Verified Output (Phase 1 on 127.0.0.1):**
```
Starting Nmap 7.80 ( https://nmap.org ) at 2026-03-05 14:00 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up.
Nmap done: 1 IP address (1 host up) scanned in 0.00 seconds
```

---

## Summary

| Task | Command |
|------|---------|
| Ping sweep | `nmap -sn <range>` |
| Skip ping | `nmap -Pn <target>` |
| SYN scan (stealth) | `nmap -sS <target>` |
| TCP connect scan | `nmap -sT <target>` |
| UDP scan | `nmap -sU <target>` |
| Version detection | `nmap -sV <target>` |
| OS detection | `nmap -O <target>` |
| Aggressive scan | `nmap -A <target>` |
| Default scripts | `nmap -sC <target>` |
| All output formats | `nmap -oA <basename> <target>` |
| Fast timing | `nmap -T4 <target>` |
| Stealth timing | `nmap -T1 <target>` |
| Only open ports | `nmap --open <target>` |
| Vuln scripts | `nmap --script=vuln <target>` |
| Fragment packets | `nmap -f <target>` |
| Decoy scan | `nmap -D RND:5 <target>` |
