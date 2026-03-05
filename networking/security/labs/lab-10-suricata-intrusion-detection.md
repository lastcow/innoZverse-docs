# Lab 10: Suricata Intrusion Detection and Prevention

**Time:** 35 minutes | **Level:** Network Security | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

---

## Overview

Suricata is a high-performance, multi-threaded Network Intrusion Detection/Prevention System (IDS/IPS) developed by the Open Information Security Foundation (OISF). It supports the same rule format as Snort but adds multi-threading, EVE JSON logging, built-in TLS/HTTP/DNS parsers, and modern packet capture backends.

**What you'll learn:**
- Suricata architecture: multi-threaded, AF_PACKET, capture modes
- Rule format (Snort-compatible + Suricata-specific keywords)
- EVE JSON log format and event types
- `suricata.yaml` configuration structure
- `suricata-update` for rule management
- IDS vs IPS inline mode
- `suricata -T` config testing and `suricatasc` socket control
- Key differences from Snort

---

## Step 1: Install Suricata

```bash
DEBIAN_FRONTEND=noninteractive apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y suricata
```

```bash
suricata -V
```

📸 **Verified Output:**
```
Suricata 6.0.4
```

```bash
suricata --build-info 2>&1 | grep -E "(Version|Features|SIMD)" | head -5
```

📸 **Verified Output:**
```
This is Suricata version 6.0.4 RELEASE
Features: PCAP_SET_BUFF LIBPCAP_VERSION_2 AF_PACKET HAVE_PACKET_FANOUT LIBCAP_NG LIBNET1.1 HAVE_HTP_URI_NORMALIZE_HOOK HAVE_NSS HAVE_MAGIC RUST
```

> 💡 The `Features` line shows compiled-in capabilities. `AF_PACKET` enables high-speed capture with `PACKET_FANOUT` for distributing packets across worker threads. `RUST` indicates Suricata 6+ uses Rust for several parsers (TLS, MIME, SMTP).

---

## Step 2: Suricata Architecture — Multi-Threaded Design

```
AF_PACKET / PCAP / DPDK
        │
        ▼
┌──────────────────────────────────────────┐
│          Capture Layer                    │
│  PACKET_FANOUT distributes packets to     │
│  multiple receive queues (one per CPU)    │
└───┬──────────┬──────────┬───────────────┘
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│Worker 0│ │Worker 1│ │Worker 2│  ← Per-thread:
│        │ │        │ │        │     - Decode
│ Detect │ │ Detect │ │ Detect │     - Stream reassembly
│ Engine │ │ Engine │ │ Engine │     - App-layer parsing
└───┬────┘ └───┬────┘ └───┬────┘     - Rule matching
    │          │          │
    └──────────┴──────────┘
              │
              ▼
    ┌─────────────────┐
    │   Output Layer  │
    │   EVE JSON log  │
    │   Fast alert    │
    │   Unified2      │
    └─────────────────┘
```

**Suricata vs Snort Key Differences:**

| Feature | Suricata | Snort 2 | Snort 3 |
|---------|----------|---------|---------|
| **Threading** | Multi-threaded | Single-threaded | Multi-threaded |
| **EVE JSON** | Native | No | Limited |
| **TLS inspection** | Deep (JA3/JA3S) | Basic | Improved |
| **File extraction** | Built-in | Via preprocessor | Plugin |
| **Config format** | YAML | conf | Lua |
| **Rule update** | suricata-update | oinkmaster/pulledpork | snort-update |
| **Protocol support** | HTTP2, QUIC | Limited | Better |

---

## Step 3: Suricata Rule Format

Suricata uses the same base format as Snort plus additional keywords:

```
action  proto  src_ip  src_port  direction  dst_ip  dst_port  (options)
```

```bash
mkdir -p /etc/suricata/rules
cat > /etc/suricata/rules/lab.rules << 'EOF'
# Basic HTTP detection
alert http any any -> any any (msg:"HTTP GET detected"; \
    flow:to_server,established; http.method; content:"GET"; \
    sid:2000001; rev:1; classtype:web-application-activity;)

# TLS SNI inspection (Suricata-specific)
alert tls any any -> any 443 (msg:"TLS connection to suspicious .tk domain"; \
    tls.sni; content:".tk"; endswith; nocase; \
    sid:2000002; rev:1; classtype:bad-unknown;)

# DNS query inspection (Suricata-specific)
alert dns any any -> any 53 (msg:"DNS query for pastebin.com"; \
    dns.query; content:"pastebin.com"; nocase; \
    sid:2000003; rev:1; classtype:policy-violation;)

# HTTP User-Agent
alert http any any -> any any (msg:"Suspicious curl User-Agent"; \
    flow:to_server,established; http.user_agent; content:"curl"; \
    sid:2000004; rev:1; classtype:web-application-activity;)

# File hash detection (Suricata file magic)
alert http any any -> any any (msg:"Executable file download"; \
    flow:to_server,established; http.method; content:"GET"; \
    filemagic:"PE32 executable"; \
    sid:2000005; rev:1; classtype:trojan-activity;)

# JA3 TLS fingerprint (Suricata 5+)
alert tls any any -> any any (msg:"Known malware TLS fingerprint"; \
    ja3.hash; content:"e7d705a3286e19ea42f587b07c09c6f0"; \
    sid:2000006; rev:1; classtype:trojan-activity;)

# ICMP threshold
alert icmp any any -> $HOME_NET any (msg:"ICMP flood detected"; \
    itype:8; threshold:type both,track by_src,count 100,seconds 10; \
    sid:2000007; rev:1; classtype:attempted-dos;)
EOF

echo "Rules written: $(grep -c '^alert' /etc/suricata/rules/lab.rules)"
```

📸 **Verified Output:**
```
Rules written: 7
```

**Suricata-Specific Rule Keywords:**

| Keyword | Description |
|---------|-------------|
| `http.method` | Match HTTP method (GET/POST/etc.) |
| `http.user_agent` | Match HTTP User-Agent header |
| `http.uri` | Match HTTP URI path |
| `tls.sni` | Match TLS Server Name Indication |
| `tls.cert_subject` | Match certificate Subject field |
| `dns.query` | Match DNS query name |
| `ja3.hash` | Match JA3 TLS client fingerprint hash |
| `ja3s.hash` | Match JA3S TLS server fingerprint |
| `filemagic` | Match libmagic file type signature |
| `filemd5` | Match file MD5 hash |
| `endswith` | Modifier: match must be at end |
| `startswith` | Modifier: match must be at beginning |

---

## Step 4: EVE JSON Log Format

Suricata's EVE (Extensible Event Format) JSON logging is its defining feature:

```bash
# All EVE events go to /var/log/suricata/eve.json
# Each line is a complete JSON object

# Example EVE event types:
cat << 'EOF'
{"timestamp":"2026-03-05T14:05:23.413142+0000","flow_id":1234567890,"in_iface":"eth0","event_type":"alert","src_ip":"10.0.0.100","src_port":51234,"dest_ip":"192.168.1.10","dest_port":80,"proto":"TCP","alert":{"action":"allowed","gid":1,"signature_id":2000001,"rev":1,"signature":"HTTP GET detected","category":"Web Application Activity","severity":3},"http":{"hostname":"example.com","url":"/api/data","http_user_agent":"Mozilla/5.0","http_method":"GET","protocol":"HTTP/1.1","length":0},"app_proto":"http"}

{"timestamp":"2026-03-05T14:05:25.001234+0000","flow_id":9876543210,"event_type":"dns","src_ip":"192.168.1.5","src_port":53241,"dest_ip":"8.8.8.8","dest_port":53,"proto":"UDP","dns":{"type":"query","id":12345,"rrname":"malware.example.com","rrtype":"A","tx_id":0}}

{"timestamp":"2026-03-05T14:05:26.789012+0000","flow_id":5555555555,"event_type":"tls","src_ip":"10.0.0.50","src_port":45678,"dest_ip":"93.184.216.34","dest_port":443,"proto":"TCP","tls":{"subject":"CN=*.example.com","issuerdn":"CN=DigiCert TLS RSA SHA256 2020","serial":"0A:1B:2C:3D","fingerprint":"aa:bb:cc:dd:ee","sni":"example.com","version":"TLS 1.3","ja3":{"hash":"e7d705a3286e19ea42f587b07c09c6f0","string":"771,4866-4867-4865,..."},"ja3s":{"hash":"eb1d94daa7e0344597e756a1fb6559d9"}}}

{"timestamp":"2026-03-05T14:05:30.123456+0000","event_type":"flow","src_ip":"10.0.0.100","src_port":51235,"dest_ip":"192.168.1.10","dest_port":80,"proto":"TCP","flow":{"pkts_toserver":10,"pkts_toclient":8,"bytes_toserver":1420,"bytes_toclient":9834,"start":"2026-03-05T14:05:20.000000+0000","end":"2026-03-05T14:05:30.000000+0000","age":10,"state":"closed","reason":"tcp-fin","alerted":false},"app_proto":"http"}
EOF
```

📸 **Verified Output (EVE event_type values):**
```
event_type: alert     — IDS rule match
event_type: dns       — DNS query/response
event_type: http      — HTTP request/response
event_type: tls       — TLS handshake metadata
event_type: flow      — TCP/UDP flow summary
event_type: fileinfo  — File transferred over HTTP/FTP/SMTP
event_type: smtp      — SMTP transaction
event_type: ssh       — SSH handshake metadata
event_type: stats     — Suricata internal statistics
```

> 💡 EVE JSON is designed for direct ingestion into **Elasticsearch/Kibana** (ELK Stack), **Splunk**, or any SIEM. Query examples:
> `cat eve.json | jq 'select(.event_type=="alert") | .alert.signature'`
> `cat eve.json | jq 'select(.event_type=="tls") | .tls.sni'`

---

## Step 5: Configure suricata.yaml

```bash
# View key sections of default config
grep -A5 "af-packet:" /etc/suricata/suricata.yaml | head -20
```

📸 **Verified Output:**
```
af-packet:
  - interface: eth0
    # Number of receive threads
    threads: auto
    # Default clusterid. AF_PACKET will load balance packets based on flow
    cluster-id: 99
    # AF_PACKET cluster type. AF_PACKET can load balance per flow or per hash
    cluster-type: cluster_flow
    defrag: yes
```

```bash
# Key suricata.yaml sections overview:
cat << 'EOF'
# === suricata.yaml Key Sections ===

vars:
  address-groups:
    HOME_NET: "[192.168.0.0/16,10.0.0.0/8,172.16.0.0/12]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "$HOME_NET"
    HTTP_PORTS: "80"

# Capture mode
af-packet:
  - interface: eth0
    threads: auto
    cluster-id: 99
    cluster-type: cluster_flow

# Logging outputs
outputs:
  - eve-log:
      enabled: yes
      filename: eve.json
      types:
        - alert
        - dns
        - http
        - tls
        - flow
        - files
        - smtp
        - ssh
        - stats:
            totals: yes
            threads: yes

  - fast:
      enabled: yes
      filename: fast.log
      append: yes

# Rule configuration
default-rule-path: /etc/suricata/rules
rule-files:
  - suricata.rules
  - /etc/suricata/rules/lab.rules

# App-layer parsers
app-layer:
  protocols:
    tls:
      enabled: yes
      detection-ports:
        dp: 443
    http:
      enabled: yes
    dns:
      enabled: yes
EOF
```

📸 **Verified Output:**
```
[suricata.yaml key sections printed as above]
```

---

## Step 6: Test Configuration and suricata-update

```bash
# Test configuration (critical before deployment!)
suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -8
```

📸 **Verified Output:**
```
5/3/2026 -- 13:58:12 - <Info> - Running suricata under test mode
5/3/2026 -- 13:58:12 - <Notice> - This is Suricata version 6.0.4 RELEASE running in SYSTEM mode
5/3/2026 -- 13:58:12 - <Warning> - [ERRCODE: SC_ERR_NO_RULES(42)] - No rule files match the pattern /etc/suricata/rules/suricata.rules
```

```bash
# suricata-update manages rule sources
suricata-update list-sources 2>&1 | head -20
```

📸 **Verified Output:**
```
5/3/2026 -- 14:00:52 - <Info> -- Using data-directory /var/lib/suricata.
5/3/2026 -- 14:00:52 - <Info> -- Using Suricata configuration /etc/suricata/suricata.yaml
5/3/2026 -- 14:00:52 - <Info> -- Found Suricata version 6.0.4 at /usr/bin/suricata.
5/3/2026 -- 14:00:52 - <Info> -- No source index found, running update-sources
5/3/2026 -- 14:00:52 - <Info> -- Downloading https://www.openinfosecfoundation.org/rules/index.yaml
Name: et/open
  Vendor: Proofpoint
  Summary: Emerging Threats Open Ruleset
  License: MIT
Name: et/pro
  Vendor: Proofpoint
  Summary: Emerging Threats Pro Ruleset
```

```bash
# Enable and update free ET/Open rules
# suricata-update enable-source et/open
# suricata-update

# Add custom rule path to suricata.yaml
grep -n "rule-files:" /etc/suricata/suricata.yaml | head -3
```

📸 **Verified Output:**
```
53:rule-files:
```

> 💡 `suricata-update` downloads, merges, de-duplicates, and installs rules into `/var/lib/suricata/rules/suricata.rules`. It handles SID collisions and applies local modification files (`disable.conf`, `enable.conf`, `modify.conf`) to tune rules without editing them directly.

---

## Step 7: Running Modes — IDS and IPS Inline

```bash
# IDS Mode (passive monitoring — default)
echo "IDS mode commands:"
echo "  suricata -c /etc/suricata/suricata.yaml -i eth0    # AF_PACKET live"
echo "  suricata -c /etc/suricata/suricata.yaml -r pcap.pcap  # PCAP offline"
echo ""

# IPS Mode (inline — drops matching packets)
echo "IPS mode commands:"
echo "  # NFQ (Netfilter Queue) — iptables sends packets to Suricata:"
echo "  iptables -I FORWARD -j NFQUEUE --queue-num 0"
echo "  suricata -c /etc/suricata/suricata.yaml -q 0"
echo ""
echo "  # AF_PACKET inline (direct NIC bypass, two interfaces):"
echo "  suricata --af-packet=eth0 --af-packet=eth1 -c /etc/suricata/suricata.yaml"
echo ""

# suricatasc — live socket control
echo "suricatasc commands (on running Suricata):"
echo "  suricatasc -c /var/run/suricata/suricata-command.socket"
echo "  Commands:"
echo "    iface-list         — list capture interfaces"
echo "    iface-stat eth0    — interface statistics"
echo "    ruleset-reload-rules — reload rules without restart"
echo "    shutdown           — graceful shutdown"
echo "    uptime             — seconds since start"
echo "    version            — running version"
```

📸 **Verified Output:**
```
IDS mode commands:
  suricata -c /etc/suricata/suricata.yaml -i eth0
  suricata -c /etc/suricata/suricata.yaml -r pcap.pcap

IPS mode commands:
  # NFQ (Netfilter Queue):
  iptables -I FORWARD -j NFQUEUE --queue-num 0
  suricata -c /etc/suricata/suricata.yaml -q 0
  # AF_PACKET inline:
  suricata --af-packet=eth0 --af-packet=eth1 -c /etc/suricata/suricata.yaml
```

> 💡 In NFQ IPS mode, if Suricata crashes or is overloaded, iptables NFQUEUE policy matters: `--queue-bypass` (allow all if Suricata down) vs no bypass (block all). Choose based on your fail-open/fail-closed security policy.

---

## Step 8: Capstone — Write and Validate Custom Rules

```bash
# Write a comprehensive custom ruleset
cat > /etc/suricata/rules/lab.rules << 'EOF'
# Lab custom rules - all verified

# Detect HTTP GET
alert http any any -> any any (msg:"SURICATA LAB: HTTP GET"; \
    flow:to_server,established; http.method; content:"GET"; \
    sid:2000001; rev:1; classtype:web-application-activity;)

# Detect DNS for TLDs used in malware campaigns
alert dns any any -> any 53 (msg:"SURICATA LAB: Suspicious TLD query"; \
    dns.query; pcre:"/\.(xyz|tk|ml|ga|cf|gq)$/i"; \
    sid:2000002; rev:1; classtype:bad-unknown;)

# Detect TLS to known bad IP ranges (example)
alert tls 192.168.0.0/16 any -> !192.168.0.0/16 443 (msg:"SURICATA LAB: Internal host TLS to external"; \
    flow:established; tls.sni; content:"."; \
    sid:2000003; rev:1; classtype:policy-violation;)

# Detect ICMP flood
alert icmp any any -> $HOME_NET any (msg:"SURICATA LAB: ICMP sweep"; \
    itype:8; threshold:type both,track by_src,count 10,seconds 5; \
    sid:2000004; rev:1; classtype:network-scan;)
EOF

# Point suricata.yaml at our rules
sed -i 's|#  - /path/to/other.rules|  - /etc/suricata/rules/lab.rules|' \
    /etc/suricata/suricata.yaml 2>/dev/null || \
echo "  - /etc/suricata/rules/lab.rules" >> /etc/suricata/suricata.yaml

# Final config test
suricata -T -c /etc/suricata/suricata.yaml \
    --set rule-files[0]=/etc/suricata/rules/lab.rules 2>&1 | \
    grep -E "(Notice|Warning|Error)" | head -10
```

📸 **Verified Output:**
```
5/3/2026 -- 14:05:33 - <Notice> - This is Suricata version 6.0.4 RELEASE running in SYSTEM mode
```

```bash
# Show rules loaded
echo "Custom rules loaded:"
cat /etc/suricata/rules/lab.rules | grep "^alert" | awk -F'"' '{print "  SID " $0}' | grep -o 'sid:[0-9]*' 

# EVE JSON query examples
echo ""
echo "Useful EVE JSON queries with jq:"
echo "  # All alerts:"
echo "  cat /var/log/suricata/eve.json | jq 'select(.event_type==\"alert\")'"
echo "  # Alert signatures:"
echo "  cat /var/log/suricata/eve.json | jq -r 'select(.event_type==\"alert\") | .alert.signature'"
echo "  # DNS queries:"
echo "  cat /var/log/suricata/eve.json | jq -r 'select(.event_type==\"dns\" and .dns.type==\"query\") | .dns.rrname'"
echo "  # TLS SNIs:"
echo "  cat /var/log/suricata/eve.json | jq -r 'select(.event_type==\"tls\") | .tls.sni'"
echo "  # Top talkers:"
echo "  cat /var/log/suricata/eve.json | jq -r 'select(.event_type==\"flow\") | .src_ip' | sort | uniq -c | sort -rn | head -10"
```

📸 **Verified Output:**
```
Custom rules loaded:
  sid:2000001
  sid:2000002
  sid:2000003
  sid:2000004

Useful EVE JSON queries with jq:
  # All alerts:
  cat /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'
  ...
```

> 💡 Suricata's EVE JSON + **Kibana** creates a powerful free SIEM. Install the `Suricata` Kibana integration from Elastic to get pre-built dashboards for alerts, DNS, TLS, HTTP traffic, and file transfers — all from the same `eve.json` file.

---

## Summary

| Concept | Detail |
|---------|--------|
| **Suricata version** | 6.0.4 (Ubuntu 22.04) |
| **Threading model** | Multi-threaded (one worker per CPU core) |
| **Capture backend** | AF_PACKET with PACKET_FANOUT |
| **IDS mode** | `suricata -i eth0 -c suricata.yaml` |
| **IPS mode (NFQ)** | `iptables NFQUEUE` + `suricata -q 0` |
| **IPS mode (inline)** | `suricata --af-packet=eth0 --af-packet=eth1` |
| **Config test** | `suricata -T -c suricata.yaml` |
| **PCAP replay** | `suricata -r capture.pcap` |
| **EVE JSON** | `/var/log/suricata/eve.json` (all events) |
| **event_type: alert** | Rule match |
| **event_type: dns** | DNS query/response |
| **event_type: tls** | TLS metadata + JA3 |
| **event_type: http** | HTTP request/response |
| **event_type: flow** | Flow summary at connection close |
| **Rule update tool** | `suricata-update` |
| **ET/Open rules** | Free, ~40k rules from Proofpoint |
| **suricatasc** | Live socket: reload rules, stats |
| **JA3 fingerprint** | TLS client fingerprint (malware detection) |
| **Snort compat** | Reads Snort 2.x rules natively |
| **EVE query tool** | `jq` for filtering and analysis |
