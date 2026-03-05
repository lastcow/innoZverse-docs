# Lab 13: WAN Optimization

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

WAN links are expensive and high-latency. WAN optimization maximizes the effective throughput of these links through compression, deduplication, protocol acceleration, and QoS. Linux's `tc` (traffic control) subsystem provides powerful, production-grade QoS capabilities.

---

## Objectives
- Understand WAN optimization techniques
- Configure Linux tc qdisc for traffic shaping
- Implement DSCP-based QoS with HTB
- Test bandwidth with iperf3
- Design enterprise QoS architecture

---

## Step 1: WAN Optimization Techniques

**The WAN problem:**
- Links are expensive: MPLS 100Mbps often costs $5,000-$20,000/month
- Latency is fixed: physics limits speed of light (NYC→London = ~70ms RTT)
- Applications designed for LAN behavior break over WAN

**Optimization techniques:**

**1. Compression:**
```
LZ4: Ultra-fast, 1-3× compression. Good for large data volumes
Zstd: Balanced speed/ratio, 2-5× compression. Modern standard
gzip: Slow but widely supported (HTTP Content-Encoding)
Typical benefit: 30-70% bandwidth reduction for text/HTML/XML
Not effective on: already-compressed data (video, ZIP, TLS)
```

**2. Deduplication (WAN dedup):**
```
Identify repeated data patterns across flows
Replace repeated patterns with short references
Effective for: file transfers, email attachments, DB backups
Hardware: Riverbed SteelHead, Silver Peak, Cisco WAAS
Typical benefit: 5-20× effective bandwidth improvement
```

**3. Protocol Optimization:**
```
TCP Acceleration:
  - CUBIC/BBR congestion control for high-latency paths
  - TCP window scaling (receive window up to 1GB)
  - Spoofing local TCP ACKs to improve throughput
  
Effective window size = RTT × bandwidth
At 70ms RTT + 100Mbps: window = 70ms × 100Mbps = 875KB minimum

CIFS/SMB Optimization:
  - SMB2/SMB3 protocol (not CIFS) — fewer round trips
  - SMB signing disable (where security allows)
  - Pre-fetch and cache frequently accessed files locally
```

> 💡 **TCP throughput formula:** Max throughput = Window Size / RTT. Over a 100ms WAN with default 64KB window: 64KB / 0.1s = 640 Kbps — far below the physical link capacity! TCP window scaling is mandatory for WAN performance.

---

## Step 2: Linux tc (Traffic Control) Architecture

`tc` is the Linux kernel's traffic control subsystem — capable of enterprise-grade QoS.

**tc hierarchy:**
```
Network Interface (eth0)
    └── qdisc (queuing discipline) — root
         ├── class 1:1 (root class)
         │    ├── class 1:10 (VoIP — high priority)
         │    ├── class 1:20 (Video — guaranteed bandwidth)
         │    ├── class 1:30 (Default — fair share)
         │    └── class 1:40 (Bulk — low priority)
         └── filter (match packets to classes)
```

**Key qdiscs:**
| qdisc | Use Case | Features |
|-------|---------|---------|
| htb | Hierarchical Token Bucket — class-based bandwidth | Guaranteed + burst rates |
| tbf | Token Bucket Filter — simple rate limiting | Fixed rate + burst |
| fq_codel | Fair Queuing + CoDel — smart buffer management | Low latency, no manual config |
| sfq | Stochastic Fairness Queuing — per-flow fairness | Simple, no classes needed |
| pfifo_fast | Default Linux qdisc | 3 priority bands |

---

## Step 3: Simple Rate Limiting with TBF

**TBF (Token Bucket Filter):** Rate limits a single interface to specified throughput.

```bash
# Rate limit eth0 to 10 Mbps with burst of 32k
tc qdisc add dev eth0 root tbf rate 10mbit burst 32kbit latency 400ms

# View the qdisc
tc qdisc show dev eth0

# Remove
tc qdisc del dev eth0 root

# Simulate 100ms WAN delay + 1% packet loss (lab testing)
tc qdisc add dev eth0 root netem delay 100ms loss 1%

# Combined: delay + bandwidth limit
tc qdisc add dev eth0 root handle 1:0 netem delay 100ms
tc qdisc add dev eth0 parent 1:1 handle 10: tbf rate 10mbit burst 32kbit latency 400ms
```

---

## Step 4: HTB — Hierarchical QoS

HTB (Hierarchical Token Bucket) is the professional choice for multi-class QoS.

**Complete QoS configuration:**
```bash
# Step 1: Set root qdisc
tc qdisc add dev eth0 root handle 1: htb default 30

# Step 2: Root class (total bandwidth = 100mbit WAN link)
tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit

# Step 3: Child classes with guaranteed rates
# VoIP: 10Mbps guaranteed, 20Mbps burst
tc class add dev eth0 parent 1:1 classid 1:10 htb rate 10mbit ceil 20mbit prio 1

# Video: 30Mbps guaranteed, 50Mbps burst  
tc class add dev eth0 parent 1:1 classid 1:20 htb rate 30mbit ceil 50mbit prio 2

# Default/interactive: fair share, up to 80Mbps
tc class add dev eth0 parent 1:1 classid 1:30 htb rate 50mbit ceil 80mbit prio 3

# Bulk: 10Mbps, can burst but lowest priority
tc class add dev eth0 parent 1:1 classid 1:40 htb rate 10mbit ceil 100mbit prio 4

# Step 4: Add leaf qdiscs (fq_codel for fairness within each class)
tc qdisc add dev eth0 parent 1:10 handle 10: fq_codel
tc qdisc add dev eth0 parent 1:20 handle 20: fq_codel
tc qdisc add dev eth0 parent 1:30 handle 30: fq_codel
tc qdisc add dev eth0 parent 1:40 handle 40: fq_codel

# Step 5: Filters — match DSCP to class
# EF (VoIP) → class 1:10
tc filter add dev eth0 parent 1: protocol ip u32 \
    match ip tos 0xb8 0xfc \
    flowid 1:10

# AF41 (Video) → class 1:20
tc filter add dev eth0 parent 1: protocol ip u32 \
    match ip tos 0x88 0xfc \
    flowid 1:20

# CS3 (Signaling) → class 1:30  
tc filter add dev eth0 parent 1: protocol ip u32 \
    match ip tos 0x60 0xfc \
    flowid 1:30
```

---

## Step 5: DSCP Marking

DSCP (Differentiated Services Code Point) is the 6-bit field in the IP ToS byte used for QoS classification.

**DSCP values (most important):**
| Name | Value | Decimal | Hex | Use |
|------|-------|---------|-----|-----|
| EF | 46 | 184 | 0xB8 | VoIP (expedited forwarding) |
| AF41 | 34 | 136 | 0x88 | Video |
| AF31 | 26 | 104 | 0x68 | Call signaling |
| AF21 | 18 | 72 | 0x48 | Transactional |
| AF11 | 10 | 40 | 0x28 | Bulk |
| CS0/BE | 0 | 0 | 0x00 | Default |

**Mark DSCP with iptables:**
```bash
# Mark VoIP RTP traffic (UDP 10000-20000)
iptables -t mangle -A POSTROUTING -p udp --dport 10000:20000 -j DSCP --set-dscp 46

# Mark HTTP traffic
iptables -t mangle -A POSTROUTING -p tcp --dport 80 -j DSCP --set-dscp 0

# Mark SMB/file transfers
iptables -t mangle -A POSTROUTING -p tcp --dport 445 -j DSCP --set-dscp 10
```

---

## Step 6: iperf3 Bandwidth Testing

iperf3 is the standard tool for network throughput testing.

```bash
# Server side
iperf3 -s

# Client: TCP test (10 seconds)
iperf3 -c 192.168.1.1 -t 10

# Client: UDP test with target bandwidth
iperf3 -c 192.168.1.1 -u -b 100M -t 10

# Bidirectional test
iperf3 -c 192.168.1.1 --bidir -t 10

# Multiple streams (simulate real traffic)
iperf3 -c 192.168.1.1 -P 8 -t 30

# JSON output for automation
iperf3 -c 192.168.1.1 -J | python3 -c "
import json, sys
data = json.load(sys.stdin)
bps = data['end']['sum_received']['bits_per_second']
print(f'Throughput: {bps/1e6:.1f} Mbps')
"
```

---

## Step 7: Verification — tc + iperf3

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq iproute2 iperf3 &&
tc -V &&
iperf3 --version | head -1 &&

echo 'Setting up TBF rate limiter on loopback:' &&
tc qdisc add dev lo root tbf rate 10mbit burst 32kbit latency 400ms 2>&1 &&
tc qdisc show dev lo &&

echo 'Removing rate limiter:' &&
tc qdisc del dev lo root 2>&1 &&
echo 'Default qdisc restored:' &&
tc qdisc show dev lo &&

echo 'WAN simulation: 100ms delay, 1% loss:' &&
tc qdisc add dev lo root netem delay 100ms loss 1% 2>&1 &&
tc qdisc show dev lo &&
tc qdisc del dev lo root 2>&1"
```

📸 **Verified Output:**
```
tc utility, iproute2-5.15.0, libbpf 0.5.0
iperf 3.9 (cJSON 1.7.13)
Setting up TBF rate limiter on loopback:
qdisc tbf 8001: root refcnt 2 rate 10Mbit burst 4Kb lat 400ms
Removing rate limiter:
Default qdisc restored:
qdisc noqueue 0: dev lo root refcnt 2
WAN simulation: 100ms delay, 1% loss:
qdisc netem 8001: root refcnt 2 limit 1000 delay 100ms loss 1%
```

---

## Step 8: Capstone — Enterprise WAN QoS Design

**Scenario:** 1,000-user company, 100Mbps MPLS WAN to 3 branch offices. Implement QoS for mixed traffic.

**Traffic profile:**
- VoIP (Cisco UCM): 10% of users active at peak, 90kbps per call
- Video conferencing (Zoom/Teams): 15% utilization, 3Mbps per session
- ERP (SAP): transactional, latency-sensitive
- File transfers (backup, updates): 40% bandwidth
- General internet: 35% bandwidth

**QoS design:**
```bash
# Total WAN bandwidth: 100Mbps (leave 5% overhead = 95Mbps)
tc qdisc add dev eth0 root handle 1: htb default 40
tc class add dev eth0 parent 1: classid 1:1 htb rate 95mbit

# 1:10 VoIP (EF DSCP 46): 10Mbps guaranteed, 15Mbps ceil, priority 1
# 1:20 Video (AF41 DSCP 34): 25Mbps guaranteed, 40Mbps ceil, priority 2  
# 1:30 ERP (AF21 DSCP 18): 15Mbps guaranteed, 40Mbps ceil, priority 3
# 1:40 Default: fair share, 45Mbps guaranteed, 80Mbps ceil
# 1:50 Bulk (AF11 DSCP 10): 5Mbps guaranteed, 30Mbps ceil, priority 5

# VoIP calculations:
# 100 users × 10% active = 10 concurrent calls
# 10 calls × 90kbps = 900kbps + overhead = ~1.5Mbps minimum
# Reserve 10Mbps to support video calls and softphones

# Monitoring:
tc -s qdisc show dev eth0    # Stats: bytes, packets, dropped
tc -s class show dev eth0    # Per-class statistics
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| TBF | Simple rate limiting; single token bucket |
| HTB | Class-based QoS with guaranteed + burst rates |
| fq_codel | Leaf qdisc for per-flow fairness and low latency |
| DSCP | Marks packet priority; preserved across MPLS/SD-WAN |
| netem | Simulate WAN conditions (delay, loss, jitter) |
| iperf3 | Measure actual throughput and validate QoS |
| WAN opt | Compression + dedup + TCP accel = effective 3-5× bandwidth |

**Next:** [Lab 14: Network Disaster Recovery →](lab-14-network-disaster-recovery.md)
