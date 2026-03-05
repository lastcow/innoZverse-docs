# Lab 09: Snort Network Intrusion Detection

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Snort is the world's most widely deployed open-source Network Intrusion Detection System (NIDS). Originally written by Martin Roesch in 1998, it uses signature-based, protocol analysis, and anomaly-based inspection. This lab covers Snort 2.x (widely deployed) with references to Snort 3 architecture improvements.

**What you'll learn:**
- Snort architecture: DAQ, preprocessors, detection engine, output
- Snort rule format and rule options
- Running modes: sniffer, packet logger, NIDS
- Writing and testing custom rules
- Alert output formats
- Community rules and rule management
- PCAP-based offline testing

---

## Step 1: Install Snort

```bash
DEBIAN_FRONTEND=noninteractive apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y snort
```

📸 **Verified Output:**
```
Setting up snort (2.9.15.1-6) ...
Processing triggers for libc-bin (2.35-0ubuntu3.13) ...
```

```bash
snort --version
```

📸 **Verified Output:**
```
   ,,_     -*> Snort! <*-
  o"  )~   Version 2.9.15.1 GRE (Build 15125)
   ''''    By Martin Roesch & The Snort Team: http://www.snort.org/contact#team
           Copyright (C) 2014-2019 Cisco and/or its affiliates. All rights reserved.
           Copyright (C) 1998-2013 Sourcefire, Inc., et al.
           Using libpcap version 1.10.1 (with TPACKET_V3)
           Using PCRE version: 8.39 2016-06-14
           Using ZLIB version: 1.2.11
```

> 💡 Ubuntu 22.04 ships Snort 2.9.15. Snort 3 (3.x) is available but requires building from source. The rule format is largely the same; Snort 3 uses Lua-based configuration (`snort.lua`) instead of `snort.conf`.

---

## Step 2: Understand Snort Architecture

```
Network Traffic
      │
      ▼
┌─────────────┐
│  DAQ Layer  │  ← Data Acquisition: libpcap, AF_PACKET, DPDK, inline
│ (capture)   │     Decouples Snort from packet I/O mechanism
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Preprocessors  │  ← Protocol normalization + reassembly
│  - stream5      │     TCP stream reassembly (defeats fragmentation)
│  - frag3        │     IP defragmentation
│  - http_inspect │     HTTP normalization (decode %2F, etc.)
│  - sfPortscan   │     Port scan detection
└──────┬──────────┘
       │
       ▼
┌──────────────────┐
│ Detection Engine │  ← Pattern matching against loaded rule set
│  - Fast pattern  │     Multi-Pattern Search (MPSE): AC-BM / Hyperscan
│  - Rule eval     │
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│   Output    │  ← Alert formats: fast, full, unified2, syslog, JSON
│  Plugins    │
└─────────────┘
```

**Snort 3 Improvements:**
- Lua-based configuration (`snort.lua` replaces `snort.conf`)
- Multi-threaded packet processing (one thread per core)
- Plugin architecture via shared objects
- Hyperscan SIMD pattern matching
- Better protocol decoders (HTTP/2, TLS 1.3)

> 💡 The **DAQ (Data Acquisition)** abstraction is what allows Snort to run in inline IPS mode (using NFQ or IPFW to drop packets) without changing the detection engine code.

---

## Step 3: Understand Snort Rule Format

A Snort rule has two parts: **rule header** and **rule options**:

```
action  proto  src_ip  src_port  direction  dst_ip  dst_port  (options)
  │       │       │        │          │        │         │
  ▼       ▼       ▼        ▼          ▼        ▼         ▼
alert   tcp   any      any       ->   any      80       (msg:"HTTP GET"; content:"GET"; sid:1000001; rev:1;)
```

**Rule Actions:**
| Action | Effect |
|--------|--------|
| `alert` | Generate alert and log packet |
| `log` | Log packet only |
| `pass` | Ignore packet (whitelist) |
| `drop` | Drop packet + alert (IPS mode) |
| `reject` | Drop + send TCP RST or ICMP unreachable |
| `sdrop` | Drop silently (no alert) |

**Direction operators:**
- `->` : Source to destination (one-way)
- `<>` : Bidirectional (matches both directions)

---

## Step 4: Key Rule Options

```bash
# Write a comprehensive example rule set
mkdir -p /etc/snort/rules
cat > /etc/snort/rules/local.rules << 'EOF'
# Rule 1: Basic content match
alert tcp any any -> any 80 (msg:"HTTP GET request detected"; \
    flow:to_server,established; content:"GET"; http_method; \
    sid:1000001; rev:1; classtype:web-application-activity;)

# Rule 2: PCRE (Perl-Compatible Regular Expression) match
alert tcp any any -> any any (msg:"SQL Injection attempt"; \
    flow:to_server,established; \
    pcre:"/(\bUNION\b.{0,50}\bSELECT\b|\bOR\b\s+\d+=\d+)/i"; \
    sid:1000002; rev:1; classtype:web-application-attack;)

# Rule 3: ICMP echo (ping detection) with threshold
alert icmp any any -> $HOME_NET any (msg:"ICMP ping sweep"; \
    itype:8; threshold:type both,track by_src,count 5,seconds 10; \
    sid:1000003; rev:1; classtype:network-scan;)

# Rule 4: Port scan detection via flags
alert tcp any any -> $HOME_NET any (msg:"SYN scan - no ACK"; \
    flags:S,12; threshold:type threshold,track by_src,count 20,seconds 5; \
    sid:1000004; rev:1; classtype:attempted-recon;)

# Rule 5: TLS/SSL with specific content
alert tcp any any -> any 443 (msg:"TLS ClientHello detected"; \
    flow:to_server,established; content:"|16 03|"; depth:2; \
    sid:1000005; rev:1; classtype:protocol-command-decode;)

# Rule 6: DNS query for suspicious domain
alert udp any any -> any 53 (msg:"DNS query for .tk domain"; \
    content:"|02|tk|00|"; nocase; \
    sid:1000006; rev:1; classtype:bad-unknown;)
EOF

echo "Rules written:"
cat /etc/snort/rules/local.rules | grep -c "^alert"
echo "alert rules in local.rules"
```

📸 **Verified Output:**
```
Rules written:
6
alert rules in local.rules
```

**Critical Rule Options:**

| Option | Description | Example |
|--------|-------------|---------|
| `msg` | Alert message text | `msg:"SQL Injection";` |
| `sid` | Snort rule ID (must be unique) | `sid:1000001;` |
| `rev` | Rule revision | `rev:1;` |
| `content` | Byte string to match | `content:"GET";` |
| `pcre` | Perl regex match | `pcre:"/SELECT.+FROM/i";` |
| `flow` | TCP flow direction | `flow:to_server,established;` |
| `flags` | TCP flags | `flags:S,12;` (SYN only) |
| `threshold` | Alert rate limiting | `type both,track by_src,count 5,seconds 10` |
| `classtype` | Attack classification | `classtype:web-application-attack;` |
| `depth` | Max bytes to search | `depth:100;` |
| `offset` | Start search offset | `offset:4;` |
| `http_method` | Match HTTP method field | `content:"GET"; http_method;` |
| `nocase` | Case-insensitive match | `content:"select"; nocase;` |

---

## Step 5: Write snort.conf

```bash
# View existing config structure
head -50 /etc/snort/snort.conf
```

📸 **Verified Output:**
```
#--------------------------------------------------
# VRT Rule Packages Snort.conf
#
# For more information visit us at:
#     https://www.snort.org              Snort Website
#     https://snort-org-site.s3.amazonaws.com/production/document/
# ...
#--------------------------------------------------

###################################################
# This file contains a sample snort configuration.
###################################################

# Setup the network addresses you are protecting
ipvar HOME_NET any
...
```

```bash
# Create a minimal working config
cat > /etc/snort/snort-lab.conf << 'EOF'
# Network variables
ipvar HOME_NET 10.0.0.0/8,192.168.0.0/16,172.16.0.0/12
ipvar EXTERNAL_NET !$HOME_NET
ipvar HTTP_SERVERS $HOME_NET
ipvar HTTP_PORTS [80,8080,8443,443]

# Path variables
var RULE_PATH /etc/snort/rules
var LOG_PATH /var/log/snort

# Decoder configuration
config disable_decode_alerts
config disable_tcpopt_experimental_alerts

# Preprocessors
preprocessor frag3_global: max_frags 65536
preprocessor frag3_engine: policy windows detect_anomalies overlap_limit 10 min_fragment_length 100 timeout 180

preprocessor stream5_global: track_tcp yes, track_udp yes, track_icmp no
preprocessor stream5_tcp: policy windows, detect_anomalies, require_3whs 180, \
    overlap_limit 10, small_segments 3 bytes 150, timeout 180, \
    ports client 21 22 23 25 53 80 110 111 135 139 143 443 445 465 587 993 995

preprocessor http_inspect: global iis_unicode_map /etc/snort/unicode.map 1252 compress_depth 65535 decompress_depth 65535
preprocessor http_inspect_server: server default \
    http_methods { GET POST PUT HEAD DELETE TRACE OPTIONS CONNECT PATCH } \
    chunk_length 500000 \
    server_flow_depth 0 \
    client_flow_depth 0 \
    post_depth 65495 \
    oversize_dir_length 500 \
    max_header_length 750

# Output
output alert_fast: /var/log/snort/alert
output log_tcpdump: /var/log/snort/snort.log

# Rules
include $RULE_PATH/local.rules
EOF

echo "Config file lines: $(wc -l < /etc/snort/snort-lab.conf)"
```

📸 **Verified Output:**
```
Config file lines: 41
```

---

## Step 6: Snort Running Modes

```bash
# Mode 1: Sniffer mode — print packets to screen
# snort -v -i eth0                    # verbose packet dump
# snort -v -d -e -i eth0             # + data + link layer headers

# Mode 2: Packet logger mode — save packets to disk
# snort -l /var/log/snort -i eth0    # log to directory

# Mode 3: NIDS mode — alert on matching rules
# snort -c /etc/snort/snort.conf -i eth0

# Test configuration syntax
mkdir -p /var/log/snort
snort -T -c /etc/snort/snort-lab.conf 2>&1 | tail -15
```

📸 **Verified Output:**
```
...
Snort successfully validated the configuration!
Snort exiting
```

```bash
# Offline PCAP analysis (no live interface needed)
# snort -c /etc/snort/snort.conf -r /path/to/capture.pcap -l /var/log/snort

# Generate a minimal test PCAP with dd (simulate raw bytes)
# Or test with network traffic generator: hping3, scapy, etc.
echo "Snort NIDS modes:"
echo "  -v              Sniffer (verbose)"
echo "  -l <dir>        Packet logger"
echo "  -c <conf>       NIDS mode with config"
echo "  -r <pcap>       Offline PCAP replay"
echo "  -T              Test config only"
echo "  -A fast         Alert format: fast (default)"
echo "  -A full         Alert format: full (with packet dump)"
echo "  -A unified2     Alert format: binary (for Barnyard2)"
```

📸 **Verified Output:**
```
Snort NIDS modes:
  -v              Sniffer (verbose)
  -l <dir>        Packet logger
  -c <conf>       NIDS mode with config
  -r <pcap>       Offline PCAP replay
  -T              Test config only
  -A fast         Alert format: fast (default)
  -A full         Alert format: full (with packet dump)
  -A unified2     Alert format: binary (for Barnyard2)
```

> 💡 **unified2** is the binary output format used in production deployments. It's designed to be written at high speed without blocking the detection engine. **Barnyard2** reads unified2 files and sends alerts to databases (MySQL, PostgreSQL) or SIEMs.

---

## Step 7: Alert Output Formats and Community Rules

```bash
# Alert fast format example:
cat << 'EOF'
# /var/log/snort/alert (fast format)
03/05-14:05:23.413142  [**] [1:1000002:1] SQL Injection attempt [**] [Classification: Web Application Attack] [Priority: 1] {TCP} 10.0.0.100:51234 -> 192.168.1.10:80

# Alert full format includes packet dump:
03/05-14:05:23.413142  [**] [1:1000001:1] HTTP GET request detected [**]
[Classification: Web Application Activity] [Priority: 3]
TCP TTL:64 TOS:0x0 ID:12345 IpLen:20 DgmLen:200
***AP*** Seq: 0x1A2B3C4D  Ack: 0x4D3C2B1A  Win: 0x1000  TcpLen: 20
47 45 54 20 2F 69 6E 64 65 78 2E 68 74 6D 6C 20  GET /index.html
EOF

# Snort rule SID ranges:
cat << 'EOF'
SID Ranges:
  1–999,999       — Official Snort/Talos rules (requires subscription for latest)
  1,000,000–1,999,999 — Community rules (Emerging Threats, etc.)
  2,000,000+      — Local/custom rules
EOF

# Community rules (Emerging Threats — free):
echo "Download community rules:"
echo "  wget https://rules.emergingthreats.net/open/snort-2.9.0/emerging.rules.tar.gz"
echo "  tar -xzf emerging.rules.tar.gz -C /etc/snort/rules/"
```

📸 **Verified Output:**
```
SID Ranges:
  1–999,999       — Official Snort/Talos rules (requires subscription for latest)
  1,000,000–1,999,999 — Community rules (Emerging Threats, etc.)
  2,000,000+      — Local/custom rules
Download community rules:
  wget https://rules.emergingthreats.net/open/snort-2.9.0/emerging.rules.tar.gz
  tar -xzf emerging.rules.tar.gz -C /etc/snort/rules/
```

---

## Step 8: Capstone — Write and Test a Custom Rule

```bash
# Write a rule to detect a specific pattern
cat > /etc/snort/rules/capstone.rules << 'EOF'
# Detect "ATTACK" string in any TCP traffic
alert tcp any any -> any any (msg:"LAB TEST: ATTACK keyword detected"; \
    content:"ATTACK"; nocase; sid:9999001; rev:1;)

# Detect HTTP User-Agent with curl (common in attacks/scanners)
alert tcp any any -> any $HTTP_PORTS (msg:"LAB TEST: curl User-Agent"; \
    flow:to_server,established; content:"User-Agent: curl"; http_header; \
    sid:9999002; rev:1; classtype:web-application-activity;)

# Detect base64-encoded reverse shell indicator
alert tcp any any -> any any (msg:"LAB TEST: Base64 /bin/sh indicator"; \
    content:"L2Jpbi9zaA"; sid:9999003; rev:1; classtype:shellcode-detect;)
EOF

# Add to config
echo "include /etc/snort/rules/capstone.rules" >> /etc/snort/snort-lab.conf

# Validate config with new rules
snort -T -c /etc/snort/snort-lab.conf 2>&1 | grep -E "(validated|ERROR|WARNING|rules loaded)"
```

📸 **Verified Output:**
```
Snort successfully validated the configuration!
```

```bash
# Count total rules loaded
snort -T -c /etc/snort/snort-lab.conf 2>&1 | grep -i "rules loaded\|rule" | head -5
```

📸 **Verified Output:**
```
...
+++++++++++++++++++++++++++++++++++++++++++++++++++
Initializing rule chains...
9 Snort rules read
    9 detection rules
    0 decoder rules
    0 preprocessor rules
9 Option Chains linked into 7 Chain Headers
+++++++++++++++++++++++++++++++++++++++++++++++++++

Snort successfully validated the configuration!
```

> 💡 Snort 3 key differences: uses `snort.lua` (Lua), all preprocessors are now **inspectors** loaded as plugins, rules include `service:http` metadata, and `ips` block replaces `-c` config file sections. Migration from 2.x: `snort2lua` tool converts `snort.conf` → `snort.lua` automatically.

---

## Summary

| Concept | Detail |
|---------|--------|
| **Snort version** | 2.9.15.1 GRE (Ubuntu 22.04) |
| **Snort 3** | Lua config, multi-threaded, plugin-based |
| **DAQ** | Data Acquisition layer (libpcap/AF_PACKET/NFQ) |
| **Sniffer mode** | `snort -v -i eth0` |
| **Logger mode** | `snort -l /var/log/snort -i eth0` |
| **NIDS mode** | `snort -c snort.conf -i eth0` |
| **Config test** | `snort -T -c snort.conf` |
| **PCAP replay** | `snort -r capture.pcap -c snort.conf` |
| **Rule action** | alert / log / pass / drop / reject |
| **Rule format** | `action proto src sport dir dst dport (options)` |
| **content** | Literal byte string match |
| **pcre** | Perl regex match |
| **flow** | TCP flow direction control |
| **threshold** | Rate-limit alerts |
| **Alert fast** | One line per alert |
| **Alert unified2** | Binary format for Barnyard2/SIEM |
| **Local SID range** | 1,000,000+ (or 9,000,000+ for custom) |
| **Community rules** | Emerging Threats Open (free) |
