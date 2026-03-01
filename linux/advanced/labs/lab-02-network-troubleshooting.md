# Lab 2: Network Troubleshooting

## 🎯 Objective
Use `ping`, `traceroute`, `mtr`, `ss`, and `tcpdump` to diagnose network connectivity issues and inspect traffic.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Completion of Lab 1 (Network Configuration)

## 🔬 Lab Instructions

### Step 1: ping — Basic Connectivity Test
```bash
ping -c 4 8.8.8.8
# PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
# 64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=12.3 ms
# ...
# 4 packets transmitted, 4 received, 0% packet loss, time 3005ms
# rtt min/avg/max/mdev = 11.9/12.3/12.8/0.3 ms

# Ping with interval and deadline
ping -c 3 -i 0.5 -W 2 google.com
```

### Step 2: ping — Diagnose Local vs Remote Failures
```bash
# Test local network stack
ping -c 2 127.0.0.1
# (should always succeed)

# Test gateway
GW=$(ip route show default | awk '{print $3}')
echo "Gateway: $GW"
ping -c 2 "$GW"

# Test external DNS
ping -c 2 8.8.8.8

# Test DNS resolution
ping -c 2 google.com
```

### Step 3: traceroute — Path Analysis
```bash
sudo apt install -y traceroute 2>/dev/null || true
traceroute 8.8.8.8
# traceroute to 8.8.8.8 (8.8.8.8), 30 hops max
#  1  10.0.0.1 (10.0.0.1)  1.234 ms  0.987 ms  0.876 ms
#  2  203.0.113.1 (203.0.113.1)  5.432 ms  5.123 ms  5.234 ms
#  3  ...
#  8  8.8.8.8 (8.8.8.8)  12.345 ms  12.234 ms  12.456 ms

# UDP traceroute (default) vs ICMP
sudo traceroute -I 8.8.8.8
```

### Step 4: mtr — Combined ping + traceroute
```bash
sudo apt install -y mtr-tiny 2>/dev/null || true

# Run 10 cycles then report
mtr --report --report-cycles 10 8.8.8.8
# HOST: myserver            Loss%   Snt   Last   Avg  Best  Wrst StDev
#   1. 10.0.0.1              0.0%    10    0.8   0.9   0.7   1.1   0.1
#   2. 203.0.113.1           0.0%    10    4.9   5.1   4.8   5.5   0.2
#   ...
#   8. 8.8.8.8               0.0%    10   12.3  12.4  12.1  12.8   0.2
```

### Step 5: ss — Socket Statistics (replacement for netstat)
```bash
# Show all listening ports
ss -tlnp
# State    Recv-Q  Send-Q  Local Address:Port   Peer Address:Port   Process
# LISTEN   0       128     0.0.0.0:22           0.0.0.0:*           users:(("sshd",pid=...))

# Show established TCP connections
ss -tnp state established
# Netid  State   Recv-Q  Send-Q  Local Address:Port   Peer Address:Port

# Show UDP
ss -ulnp
```

### Step 6: ss — Filter by Port or State
```bash
# Connections on port 22
ss -tnp 'sport = :22 or dport = :22'

# Count established connections per remote IP
ss -tn state established | awk 'NR>1 {print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn
```

### Step 7: Install and Use tcpdump
```bash
sudo apt install -y tcpdump

# Capture on eth0, 10 packets
IFACE=$(ip -brief link | grep -v lo | awk 'NR==1{print $1}')
sudo tcpdump -i "$IFACE" -c 10
# 06:01:23.123456 IP 10.0.0.5.52100 > 8.8.8.8.53: UDP, length 30
# ...
```

### Step 8: tcpdump Filtering
```bash
IFACE=$(ip -brief link | grep -v lo | awk 'NR==1{print $1}')

# Capture only ICMP (ping) traffic
sudo tcpdump -i "$IFACE" -c 5 icmp &
TCPDUMP_PID=$!
ping -c 3 8.8.8.8 > /dev/null
wait $TCPDUMP_PID 2>/dev/null || true
# 06:01:23 IP myserver > 8.8.8.8: ICMP echo request
# 06:01:23 IP 8.8.8.8 > myserver: ICMP echo reply

# Capture DNS queries
sudo tcpdump -i "$IFACE" -c 5 port 53 &
TCPDUMP_PID=$!
nslookup google.com > /dev/null 2>&1 || dig google.com > /dev/null 2>&1
wait $TCPDUMP_PID 2>/dev/null || true
```

### Step 9: DNS Resolution Testing
```bash
# Test DNS lookup
nslookup google.com
# Server:  127.0.0.53
# Address: 127.0.0.53#53
# Non-authoritative answer:
# Name:   google.com
# Address: 142.250.x.x

# Alternatively
host google.com
# google.com has address 142.250.x.x

# Using dig for more detail
dig google.com +short
# 142.250.x.x
```

### Step 10: Systematic Troubleshooting Checklist Script
```bash
cat > ~/net_troubleshoot.sh << 'EOF'
#!/bin/bash
set -euo pipefail
echo "=== Network Troubleshooting Report ==="
echo "Date: $(date)"
echo ""

check() { local label="$1"; shift; printf "%-30s " "$label:"; "$@" &>/dev/null && echo "OK" || echo "FAIL"; }

check "Loopback ping"          ping -c 1 -W 2 127.0.0.1
GW=$(ip route show default | awk '{print $3}' | head -1)
check "Gateway ping ($GW)"     ping -c 1 -W 2 "$GW"
check "External IP (8.8.8.8)" ping -c 1 -W 3 8.8.8.8
check "DNS resolution"         getent hosts google.com

echo ""
echo "Listening services:"
ss -tlnp | grep LISTEN | awk '{print "  " $4, $6}'
EOF
chmod +x ~/net_troubleshoot.sh
~/net_troubleshoot.sh
# === Network Troubleshooting Report ===
# Loopback ping               OK
# Gateway ping (10.0.0.1)     OK
# External IP (8.8.8.8)       OK
# DNS resolution              OK
```

## ✅ Verification
```bash
ping -c 1 -W 2 8.8.8.8 && echo "Internet: OK"
ss -tlnp | grep -q ':22' && echo "SSH port: listening"
```

## 📝 Summary
- `ping` tests reachability; test loopback → gateway → external in sequence
- `traceroute` shows the hop-by-hop path; `mtr` combines traceroute with statistics
- `ss -tlnp` replaces `netstat`; shows listening ports and owning processes
- `tcpdump` captures live traffic; filter by host, port, or protocol
- Systematic troubleshooting: loopback → gateway → internet → DNS
