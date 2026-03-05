# Lab 14: Network Forensics and PCAP Investigation

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Network forensics is the systematic collection, preservation, and analysis of network traffic to reconstruct events, identify attackers, and extract Indicators of Compromise (IOCs). In this lab, you will capture traffic with `tcpdump`, analyse PCAPs with `tshark` (CLI Wireshark), extract IOCs with Python/Scapy, and apply forensic methodology — all verified in Docker.

---

## Step 1 — Install Tools and Verify

```bash
apt-get update -qq && apt-get install -y tcpdump tshark wireshark-common python3 curl
tshark --version 2>&1 | head -2
```

📸 **Verified Output:**
```
Setting up tcpdump (4.99.1-3ubuntu0.2) ...
Setting up wireshark-common (3.6.2-2) ...
Setting up tshark (3.6.2-2) ...
Running as user "root" and group "root". This could be dangerous.
TShark (Wireshark) 3.6.2 (Git v3.6.2 packaged as 3.6.2-2)
```

> 💡 **Tip:** In production, never run tshark as root on live systems — use a dedicated capture user with `setcap cap_net_raw,cap_net_admin=eip /usr/bin/dumpcap`. The Docker lab runs as root for simplicity.

---

## Step 2 — Network Forensics Methodology

Before touching any evidence, follow the digital forensics process:

```
1. COLLECTION    → Capture traffic without alteration
2. PRESERVATION  → Store PCAPs with hash verification (sha256sum)
3. ANALYSIS      → Examine with read-only tools (-r flag, never modify)
4. REPORTING     → Timeline, IOCs, chain of custody documentation
```

### Chain of Custody for PCAPs

```bash
# 1. Capture traffic
tcpdump -i lo -nn -w /tmp/evidence.pcap -c 1000

# 2. Immediately hash the file (preservation)
sha256sum /tmp/evidence.pcap > /tmp/evidence.pcap.sha256
cat /tmp/evidence.pcap.sha256

# 3. Verify integrity before every analysis session
sha256sum -c /tmp/evidence.pcap.sha256
```

> 💡 **Tip:** **Never** analyse the original PCAP directly. Work on a copy: `cp /tmp/evidence.pcap /tmp/working_copy.pcap`. Courts require provable chain of custody with hash verification.

---

## Step 3 — Generate a PCAP for Analysis

```bash
# Start HTTP server
python3 -m http.server 8080 &
sleep 1

# Capture traffic to PCAP
tcpdump -i lo -nn -c 10 -w /tmp/net.pcap port 8080 &
sleep 0.5

# Generate HTTP traffic
curl -s http://127.0.0.1:8080/ -o /dev/null
sleep 2

# Verify capture
sha256sum /tmp/net.pcap
ls -lh /tmp/net.pcap
```

📸 **Verified Output:**
```
tcpdump: listening on lo, link-type EN10MB (Ethernet), snapshot length 262144 bytes
127.0.0.1 - - [05/Mar/2026 14:01:35] "GET / HTTP/1.1" 200 -
10 packets captured
26 packets received by filter
0 packets dropped by kernel
```

---

## Step 4 — tshark Analysis: Reading and Filtering PCAPs

### Basic PCAP read

```bash
tshark -r /tmp/net.pcap
```

📸 **Verified Output:**
```
Running as user "root" and group "root". This could be dangerous.
    1   0.000000    127.0.0.1 → 127.0.0.1    TCP 74 34682 → 8080 [SYN] Seq=0 Win=65495 Len=0 MSS=65495 SACK_PERM=1 TSval=2902989834 TSecr=0 WS=128
    2   0.000033    127.0.0.1 → 127.0.0.1    TCP 74 8080 → 34682 [SYN, ACK] Seq=0 Ack=1 Win=65483 Len=0 MSS=65495 SACK_PERM=1 TSval=2902989834 TSecr=2902989834 WS=128
    3   0.000064    127.0.0.1 → 127.0.0.1    TCP 66 34682 → 8080 [ACK] Seq=1 Ack=1 Win=65536 Len=0 TSval=2902989834 TSecr=2902989834
    4   0.000228    127.0.0.1 → 127.0.0.1    HTTP 144 GET / HTTP/1.1 
    5   0.000248    127.0.0.1 → 127.0.0.1    TCP 66 8080 → 34682 [ACK] Seq=1 Ack=79 Win=65408 Len=0 TSval=2902989834 TSecr=2902989834
    6   0.005002    127.0.0.1 → 127.0.0.1    TCP 223 HTTP/1.0 200 OK  [TCP segment of a reassembled PDU]
    7   0.005047    127.0.0.1 → 127.0.0.1    TCP 66 34682 → 8080 [ACK] Seq=79 Ack=158 Win=65408 Len=0 TSval=2902989839 TSecr=2902989839
    8   0.005128    127.0.0.1 → 127.0.0.1    HTTP 1129 HTTP/1.0 200 OK  (text/html)
    9   0.005147    127.0.0.1 → 127.0.0.1    TCP 66 34682 → 8080 [ACK] Seq=79 Ack=1221 Win=67584 Len=0 TSval=2902989839 TSecr=2902989839
```

---

## Step 5 — Field Extraction for IOC Analysis

### Extract specific fields (IP src, dst, port)

```bash
tshark -r /tmp/net.pcap -Y "tcp" -T fields \
  -e ip.src -e ip.dst -e tcp.dstport
```

📸 **Verified Output:**
```
Running as user "root" and group "root". This could be dangerous.
127.0.0.1	127.0.0.1	8080
127.0.0.1	127.0.0.1	34682
127.0.0.1	127.0.0.1	8080
127.0.0.1	127.0.0.1	8080
127.0.0.1	127.0.0.1	34682
127.0.0.1	127.0.0.1	34682
127.0.0.1	127.0.0.1	8080
127.0.0.1	127.0.0.1	34682
127.0.0.1	127.0.0.1	8080
```

### Filter HTTP traffic

```bash
tshark -r /tmp/net.pcap -Y "http"
```

📸 **Verified Output:**
```
Running as user "root" and group "root". This could be dangerous.
    4   0.000228    127.0.0.1 → 127.0.0.1    HTTP 144 GET / HTTP/1.1 
    8   0.005128    127.0.0.1 → 127.0.0.1    HTTP 1129 HTTP/1.0 200 OK  (text/html)
```

### Common tshark Display Filters

```bash
# SYN packets only (detect scanners)
tshark -r /tmp/net.pcap -Y "tcp.flags.syn==1 && tcp.flags.ack==0"

# DNS queries
tshark -r /tmp/net.pcap -Y "dns.flags.response==0" \
  -T fields -e frame.time -e ip.src -e dns.qry.name

# Large DNS responses (tunnelling detection > 200 bytes)
tshark -r /tmp/net.pcap -Y "dns && udp.length > 200"

# HTTP Basic Auth (credential exposure)
tshark -r /tmp/net.pcap -Y "http.authorization"

# IP conversation statistics
tshark -r /tmp/net.pcap -q -z conv,ip

# Protocol hierarchy
tshark -r /tmp/net.pcap -q -z io,phs
```

> 💡 **Tip:** `tshark -z` statistics options are powerful for rapid triage. Use `-z conv,tcp` to see all TCP conversations sorted by bytes — a large outbound transfer to an unknown IP is a red flag.

---

## Step 6 — IOC Extraction

### Extract all unique IPs

```bash
tshark -r /tmp/net.pcap -T fields -e ip.src -e ip.dst 2>/dev/null \
  | tr '\t' '\n' | sort -u | grep -v '^$'
```

### Extract all DNS domains queried

```bash
tshark -r /tmp/net.pcap -Y "dns" -T fields -e dns.qry.name 2>/dev/null \
  | sort -u | grep -v '^$'
```

### Extract file hashes from transferred files

```bash
# Extract HTTP objects (files transferred via HTTP)
tshark -r /tmp/net.pcap --export-objects http,/tmp/http_objects 2>/dev/null
ls /tmp/http_objects/ 2>/dev/null && \
  find /tmp/http_objects -type f -exec sha256sum {} \;
```

### Detect Base64-encoded data in HTTP (exfiltration indicator)

```bash
tshark -r /tmp/net.pcap -Y "http" -T fields -e http.request.uri \
  -e http.file_data 2>/dev/null | \
  grep -E '[A-Za-z0-9+/]{50,}={0,2}$'
```

---

## Step 7 — Timeline Reconstruction

```bash
# Build chronological event timeline
tshark -r /tmp/net.pcap -T fields \
  -e frame.time_epoch \
  -e ip.src \
  -e ip.dst \
  -e _ws.col.Protocol \
  -e _ws.col.Info \
  2>/dev/null | \
  awk '{printf "%.6f %s -> %s [%s] %s\n", $1, $2, $3, $4, $5}' | \
  sort -n | head -20

# TCP stream reassembly (follow conversation)
tshark -r /tmp/net.pcap -q -z follow,tcp,ascii,0 2>/dev/null | head -40
```

### Python3 + Scapy for PCAP Parsing

```bash
pip3 install scapy 2>/dev/null | tail -1

python3 - <<'EOF'
from scapy.all import rdpcap, IP, TCP, UDP, DNS, DNSQR
import base64

packets = rdpcap('/tmp/net.pcap')
print(f"Total packets: {len(packets)}")
print("\n=== TCP Connections ===")
connections = set()
for pkt in packets:
    if IP in pkt and TCP in pkt:
        src = f"{pkt[IP].src}:{pkt[TCP].sport}"
        dst = f"{pkt[IP].dst}:{pkt[TCP].dport}"
        flags = pkt[TCP].flags
        if 'S' in str(flags) and 'A' not in str(flags):
            connections.add((pkt[IP].src, pkt[IP].dst, pkt[TCP].dport))
for conn in connections:
    print(f"  SYN: {conn[0]} -> {conn[1]}:{conn[2]}")

print("\n=== DNS Queries ===")
for pkt in packets:
    if DNS in pkt and DNSQR in pkt:
        print(f"  Query: {pkt[DNSQR].qname.decode()}")
EOF
```

> 💡 **Tip:** Scapy's `sniff(prn=callback, store=False)` is memory-efficient for live analysis of high-volume streams. Use `store=False` to avoid buffering all packets in RAM.

---

## Step 8 — Capstone: Detect Data Exfiltration

**Scenario:** Analyse a PCAP for signs of data exfiltration over HTTP.

```bash
# Simulate exfiltration: base64-encode sensitive data in URL
python3 -m http.server 8090 &>/dev/null &
sleep 1
tcpdump -i lo -nn -c 20 -w /tmp/exfil.pcap port 8090 &
sleep 0.5

# Simulate attacker sending data via GET parameters (base64 encoded)
SENSITIVE=$(echo "credit_card=4111111111111111&ssn=123-45-6789" | base64)
curl -s "http://127.0.0.1:8090/?data=${SENSITIVE}" -o /dev/null
curl -s "http://127.0.0.1:8090/?data=$(echo 'passwd:root:x:0:0:root:/root:/bin/bash' | base64)" -o /dev/null
sleep 2

# Analyse for exfiltration patterns
echo "=== HTTP URIs with base64-like data ==="
tshark -r /tmp/exfil.pcap -Y "http.request" \
  -T fields -e http.request.uri 2>/dev/null

echo "=== Large outbound transfers ==="
tshark -r /tmp/exfil.pcap -q -z conv,tcp 2>/dev/null

echo "=== Full TCP stream reconstruction ==="
tshark -r /tmp/exfil.pcap -q -z follow,tcp,ascii,0 2>/dev/null | \
  grep -A2 'GET /'
```

**IOC Summary Report Template:**

```markdown
## Incident IOC Report
Date: $(date -u)
Analyst: [Name]
PCAP SHA256: [hash]

### Indicators of Compromise
| Type | Value | First Seen | Last Seen | Confidence |
|------|-------|-----------|-----------|-----------|
| IP | 192.168.1.100 | 14:00:01 | 14:05:32 | High |
| Domain | evil.example.com | 14:01:15 | 14:01:15 | High |
| URL Pattern | /data?d=<base64> | 14:02:01 | 14:03:44 | Medium |
| User-Agent | curl/7.81.0 (automated) | 14:00:01 | - | Low |

### Timeline
[Reconstructed event sequence]

### Recommendations
[Containment/remediation steps]
```

---

## Summary

| Task | Command |
|------|---------|
| Install tshark | `apt-get install tshark wireshark-common` |
| Read PCAP | `tshark -r file.pcap` |
| Filter traffic | `tshark -r file.pcap -Y "http"` |
| Extract fields | `tshark -r file.pcap -T fields -e ip.src -e ip.dst` |
| SYN scan detection | `tshark -Y "tcp.flags.syn==1 && tcp.flags.ack==0"` |
| HTTP objects | `tshark --export-objects http,/tmp/dir` |
| Follow TCP stream | `tshark -z follow,tcp,ascii,0` |
| IP conversations | `tshark -z conv,ip` |
| Protocol hierarchy | `tshark -z io,phs` |
| Hash PCAP (CoC) | `sha256sum evidence.pcap > evidence.pcap.sha256` |
| Python PCAP parse | `from scapy.all import rdpcap; pkts = rdpcap('file.pcap')` |
| DNS tunnelling | `tshark -Y "dns && udp.length > 200"` |
| HTTP auth exposure | `tshark -Y "http.authorization"` |
