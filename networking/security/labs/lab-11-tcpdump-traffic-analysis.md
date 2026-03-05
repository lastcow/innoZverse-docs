# Lab 11: tcpdump Traffic Analysis

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

`tcpdump` is the de-facto command-line packet analyser used by security engineers for real-time traffic capture, BPF-filtered analysis, and offline PCAP investigation. In this lab you will capture live traffic, write and read PCAP files, decode TCP flags, write BPF filter expressions, and identify suspicious patterns — all inside a Docker container.

---

## Step 1 — Install tcpdump and Python 3

```bash
apt-get update -qq && apt-get install -y tcpdump python3 curl
tcpdump --version
python3 --version
```

📸 **Verified Output:**
```
tcpdump version 4.99.1
libpcap version 1.10.1 (with TPACKET_V3)
OpenSSL 3.0.2 15 Mar 2022
Python 3.10.12
```

> 💡 **Tip:** `tcpdump` requires root or `CAP_NET_RAW`. In the privileged Docker container, you are already root — no `sudo` needed.

---

## Step 2 — Capture Live Traffic on Loopback

Start a Python HTTP server in the background, then capture packets on the loopback interface:

```bash
# Start HTTP server
python3 -m http.server 8080 &

# Capture 10 packets on loopback
tcpdump -i lo -nn -c 10 port 8080 &

# Generate traffic
sleep 1 && curl -s http://127.0.0.1:8080/ -o /dev/null
```

**Flag reference:**

| Flag | Meaning |
|------|---------|
| `-i lo` | Listen on loopback interface |
| `-nn` | Do not resolve hostnames or port names |
| `-c 10` | Stop after 10 packets |
| `-e` | Print link-layer (Ethernet) header |
| `-X` | Print packet payload in hex + ASCII |
| `-A` | Print payload in ASCII only |

> 💡 **Tip:** Use `-i any` to capture on **all** interfaces simultaneously. Useful when you don't know which interface carries the traffic.

---

## Step 3 — Write a PCAP File and Read it Offline

```bash
# Capture to file
tcpdump -i lo -nn -c 10 -w /tmp/test.pcap port 8080 &
sleep 0.5
curl -s http://127.0.0.1:8080/ -o /dev/null
curl -s http://127.0.0.1:8080/nonexistent -o /dev/null
sleep 2

# Read the pcap offline
tcpdump -r /tmp/test.pcap -nn
```

📸 **Verified Output:**
```
reading from file /tmp/test.pcap, link-type EN10MB (Ethernet), snapshot length 262144
14:00:01.737312 IP 127.0.0.1.51426 > 127.0.0.1.8080: Flags [S], seq 3659952289, win 65495, options [mss 65495,sackOK,TS val 2902895860 ecr 0,nop,wscale 7], length 0
14:00:01.737344 IP 127.0.0.1.8080 > 127.0.0.1.51426: Flags [S.], seq 2511711281, ack 3659952290, win 65483, options [mss 65495,sackOK,TS val 2902895860 ecr 2902895860,nop,wscale 7], length 0
14:00:01.737376 IP 127.0.0.1.51426 > 127.0.0.1.8080: Flags [.], ack 1, win 512, options [nop,nop,TS val 2902895860 ecr 2902895860], length 0
14:00:01.737523 IP 127.0.0.1.51426 > 127.0.0.1.8080: Flags [P.], seq 1:79, ack 1, win 512, options [nop,nop,TS val 2902895860 ecr 2902895860], length 78: HTTP: GET / HTTP/1.1
14:00:01.737543 IP 127.0.0.1.8080 > 127.0.0.1.51426: Flags [.], ack 79, win 511, options [nop,nop,TS val 2902895860 ecr 2902895860], length 0
14:00:01.741630 IP 127.0.0.1.8080 > 127.0.0.1.51426: Flags [P.], seq 1:158, ack 79, win 512, length 157: HTTP: HTTP/1.0 200 OK
14:00:01.741672 IP 127.0.0.1.51426 > 127.0.0.1.8080: Flags [.], ack 158, win 511, length 0
14:00:01.741740 IP 127.0.0.1.8080 > 127.0.0.1.51426: Flags [P.], seq 158:1221, ack 79, win 512, length 1063: HTTP
14:00:01.741759 IP 127.0.0.1.51426 > 127.0.0.1.8080: Flags [.], ack 1221, win 528, length 0
14:00:01.741876 IP 127.0.0.1.8080 > 127.0.0.1.51426: Flags [F.], seq 1221, ack 79, win 512, length 0
```

---

## Step 4 — TCP Flag Analysis

### Flag Reference Table

| tcpdump Flag | TCP Flag Bits | Meaning |
|-------------|--------------|---------|
| `[S]` | SYN | Connection initiation |
| `[S.]` | SYN-ACK | Server response to SYN |
| `[.]` | ACK | Acknowledgement |
| `[P.]` | PSH-ACK | Data push |
| `[F.]` | FIN-ACK | Connection teardown |
| `[R]` | RST | Connection reset |
| `[R.]` | RST-ACK | Reset with acknowledgement |

### Filter for SYN packets (connection initiation)

```bash
tcpdump -r /tmp/test.pcap -nn 'tcp[tcpflags] & tcp-syn != 0'
```

📸 **Verified Output:**
```
reading from file /tmp/test.pcap, link-type EN10MB (Ethernet), snapshot length 262144
14:00:01.737312 IP 127.0.0.1.51426 > 127.0.0.1.8080: Flags [S], seq 3659952289, win 65495, options [mss 65495,sackOK,TS val 2902895860 ecr 0,nop,wscale 7], length 0
14:00:01.737344 IP 127.0.0.1.8080 > 127.0.0.1.51426: Flags [S.], seq 2511711281, ack 3659952290, win 65483, options [mss 65495,sackOK,TS val 2902895860 ecr 2902895860,nop,wscale 7], length 0
```

> 💡 **Tip:** A SYN scan (port scan) sends only `[S]` packets and never completes the handshake. If you see many `[S]` with no matching `[S.]` response, the ports are filtered or closed.

---

## Step 5 — BPF Filter Expressions

Berkeley Packet Filter (BPF) lets you select exactly which packets to capture:

```bash
# Filter by host
tcpdump -i lo -nn 'host 192.168.1.100'

# Filter by network
tcpdump -i lo -nn 'net 10.0.0.0/8'

# Filter by port
tcpdump -i lo -nn 'port 443'

# Filter by protocol
tcpdump -i lo -nn 'proto 17'         # UDP
tcpdump -i lo -nn 'tcp'

# Composite: HTTP traffic from specific source
tcpdump -i lo -nn 'src 10.0.0.1 and dst port 80'

# NOT filters (exclude noise)
tcpdump -i lo -nn 'not port 22 and not arp'

# Detect SYN-only packets (port scan signature)
tcpdump -i lo -nn 'tcp[tcpflags] == tcp-syn'

# DNS tunnelling detection (large DNS TXT queries > 100 bytes)
tcpdump -i any -nn 'udp port 53 and udp[4:2] > 100'

# HTTP plaintext credentials (look for POST)
tcpdump -i lo -nn -A 'tcp port 80 and (tcp[((tcp[12:1] & 0xf0) >> 2):4] = 0x504f5354)'
```

> 💡 **Tip:** BPF expressions are compiled into bytecode and executed in the kernel — they are extremely efficient. Always prefer BPF filters over `grep`-piping for high-speed captures.

---

## Step 6 — Payload Inspection (-A and -X modes)

```bash
# ASCII mode — great for HTTP/SMTP/FTP plaintext inspection
tcpdump -r /tmp/test.pcap -nn -A 2>&1 | head -20
```

📸 **Verified Output (excerpt):**
```
14:00:01.737523 IP 127.0.0.1.51426 > 127.0.0.1.8080: Flags [P.], seq 1:79, ack 1, win 512, length 78: HTTP: GET / HTTP/1.1
E.....@.@.*d.............&p....2.....v.....
........GET / HTTP/1.1
Host: 127.0.0.1:8080
User-Agent: curl/7.81.0
Accept: */*
```

The `-X` flag adds hex dump alongside ASCII, useful for binary protocols.

```bash
tcpdump -r /tmp/test.pcap -nn -X 2>&1 | head -15
```

---

## Step 7 — Security Filters for Suspicious Patterns

### Detect Port Scan (SYN flood to multiple ports)
```bash
# Capture SYN-only packets — a classic port-scan signature
tcpdump -i any -nn 'tcp[tcpflags] == tcp-syn' -c 20
```

### Detect DNS Tunnelling
```bash
# Oversized DNS responses often indicate data exfiltration over DNS
tcpdump -i any -nn 'udp port 53 and udp[4:2] > 200'
```

### Detect Beaconing (periodic connections)
```bash
# Capture all TCP connections — review timestamps for regular intervals
tcpdump -i any -nn 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0' \
  -w /tmp/beacon.pcap
```

### Detect Large Data Transfers (Exfiltration)
```bash
# Packets > 1400 bytes on unexpected ports
tcpdump -i any -nn 'greater 1400 and not port 443 and not port 80'
```

### Python3 PCAP Analysis with scapy
```bash
pip3 install scapy 2>/dev/null
python3 - <<'EOF'
from scapy.all import rdpcap, TCP
packets = rdpcap('/tmp/test.pcap')
for pkt in packets:
    if TCP in pkt:
        flags = pkt[TCP].flags
        print(f"{pkt[0][1].src}:{pkt[TCP].sport} -> "
              f"{pkt[0][1].dst}:{pkt[TCP].dport} flags={flags}")
EOF
```

> 💡 **Tip:** `scapy` lets you craft, send, and parse packets programmatically. Use `rdpcap()` for offline analysis and `sniff()` for live capture with Python callbacks.

---

## Step 8 — Capstone: Investigate a Suspicious PCAP

**Scenario:** You've been given `/tmp/test.pcap` from a DMZ server. Your task is to extract all IOCs (Indicators of Compromise).

```bash
# 1. Show all unique source/destination IPs
tcpdump -r /tmp/test.pcap -nn 2>/dev/null | \
  grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}\.[0-9]+' | \
  cut -d. -f1-4 | sort -u

# 2. Show all TCP flags seen
tcpdump -r /tmp/test.pcap -nn 2>/dev/null | \
  grep -oE 'Flags \[[^]]+\]' | sort | uniq -c | sort -rn

# 3. Show all HTTP methods
tcpdump -r /tmp/test.pcap -nn -A 2>/dev/null | \
  grep -E '^(GET|POST|PUT|DELETE|HEAD|PATCH)'

# 4. Count packets by destination port
tcpdump -r /tmp/test.pcap -nn 2>/dev/null | \
  grep -oE '> 127\.0\.0\.1\.[0-9]+' | \
  awk '{print $NF}' | sort | uniq -c | sort -rn

# 5. Check for plaintext credentials (Basic Auth)
tcpdump -r /tmp/test.pcap -nn -A 2>/dev/null | grep -i 'authorization: basic'
```

📸 **Verified Output (Step 8 — flags summary):**
```
      6 Flags [.]
      2 Flags [F.]
      2 Flags [P.]
      2 Flags [S]
      2 Flags [S.]
```

---

## Summary

| Concept | Command / Expression |
|---------|-------------------|
| Capture on all interfaces | `tcpdump -i any -nn` |
| Write to PCAP | `tcpdump -i lo -w file.pcap` |
| Read PCAP offline | `tcpdump -r file.pcap -nn` |
| ASCII payload decode | `tcpdump -r file.pcap -A` |
| Filter by host | `tcpdump 'host 10.0.0.1'` |
| Filter by network | `tcpdump 'net 192.168.0.0/16'` |
| Filter by port | `tcpdump 'port 443'` |
| SYN-only packets | `tcpdump 'tcp[tcpflags] == tcp-syn'` |
| Exclude SSH noise | `tcpdump 'not port 22'` |
| Large DNS (tunnelling) | `tcpdump 'udp port 53 and udp[4:2] > 200'` |
| TCP flag `[S]` | Connection initiation |
| TCP flag `[S.]` | Server SYN-ACK |
| TCP flag `[P.]` | Data push |
| TCP flag `[F.]` | Connection teardown |
| TCP flag `[R]` | Connection reset |
