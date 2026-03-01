# Lab 2: Network Troubleshooting

## 🎯 Objective
Diagnose network connectivity issues using ping, tracepath, ss, and curl to test reachability and diagnose problems.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Advanced Lab 1: Network Configuration

## 🔬 Lab Instructions

### Step 1: Test Basic Connectivity with ping

```bash
# Ping with count limit (non-interactive)
ping -c2 -W1 127.0.0.1
```

**Expected output:**
```
PING 8.8.8.8 (8.8.8.8) 56(84) bytes of data.
64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=5.23 ms
...
--- 8.8.8.8 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
```

```bash
# Ping with deadline (timeout after 5 seconds)
ping -c2 -W1 127.0.0.1
```

```bash
# Quick reachability check
ping -c1 -W1 127.0.0.1 > /dev/null 2>&1 && echo "Loopback reachable" || echo "Network error"
```

### Step 2: Trace Network Path with tracepath

```bash
# tracepath doesn't require root (unlike traceroute)
tracepath -m3 127.0.0.1 2>/dev/null | head -5 || echo "tracepath to localhost"
```

```bash
# Check if tracepath is available
which tracepath && echo "tracepath available" || echo "tracepath not found"
which traceroute && echo "traceroute available" || echo "traceroute not found"
```

### Step 3: HTTP Testing with curl

```bash
# Get HTTP headers only (-I flag)
ss -tuln | head -10
```

**Expected output:**
```
HTTP/2 200
content-type: text/html; charset=UTF-8
...
```

```bash
# Time the connection
# curl timing demo (requires internet): \
     -o /dev/null -s https://example.com
```

```bash
# Follow redirects and show final URL
ss -s
```

```bash
# Download a small file (test download speed)
# curl speed test (requires internet)
```

### Step 4: Check Socket Statistics

```bash
# Summary of all connections
ss -s
```

```bash
# Show all TCP connections
ss -tn | head -15
```

```bash
# Find what's listening on a specific port
ss -tlnp | grep ":22"
ss -tlnp | grep ":80" || echo "Port 80 not listening"
```

```bash
# Show connections to a specific remote host
ss -tn dst 8.8.8.8 2>/dev/null | head -5 || echo "No connections to 8.8.8.8"
```

### Step 5: DNS Troubleshooting

```bash
# Check DNS resolver configuration
cat /etc/resolv.conf
```

```bash
# Test DNS resolution
getent hosts google.com 2>/dev/null | head -3 || echo "getent not working"
```

```bash
# Check /etc/hosts
cat /etc/hosts
```

```bash
# Check DNS lookup order
grep "^hosts:" /etc/nsswitch.conf
```

### Step 6: Network Interface Diagnosis

```bash
# Check interface errors
ip -s link | grep -A 3 "LOWER_UP" | head -20
```

```bash
# Check for packet loss in /proc
cat /proc/net/dev | grep -v "^Inter\|^ face"
```

```bash
# ARP cache (local network neighbors)
ip neigh show 2>/dev/null | head -10 || echo "No ARP entries"
```

### Step 7: Port Connectivity Testing

```bash
# Test if a port is open using bash TCP device
timeout 3 bash -c "echo > /dev/tcp/8.8.8.8/53" 2>/dev/null && echo "Port 53 on 8.8.8.8 is open" || echo "Port 53 unreachable or timeout"
```

```bash
# Test HTTPS port
timeout 3 bash -c "echo > /dev/tcp/example.com/443" 2>/dev/null && echo "Port 443 open" || echo "Port 443 closed"
```

### Step 8: Systematic Troubleshooting

```bash
cat > /tmp/net-diag.sh << 'EOF'
#!/bin/bash
echo "=== Network Diagnostics ==="

echo ""
echo "1. Interface Status:"
ip link show | grep -E "^[0-9]+:" | awk '{print "  " $2, $3}'

echo ""
echo "2. IP Addresses:"
ip addr | grep "inet " | awk '{print "  " $2, $NF}'

echo ""
echo "3. Default Gateway:"
ip route | grep default | awk '{print "  " $3}'

echo ""
echo "4. DNS Resolvers:"
grep nameserver /etc/resolv.conf | awk '{print "  " $2}'

echo ""
echo "5. Internet Reachability:"
ping -c1 -W1 127.0.0.1 > /dev/null 2>&1 && echo "  Loopback: OK" || echo "  Network: error"

echo ""
echo "6. Listening Services:"
ss -tlnp | grep LISTEN | awk '{print "  Port", $4}' | head -10
EOF

bash /tmp/net-diag.sh
```

## ✅ Verification

```bash
echo "=== Connectivity test ===" && ping -c2 -W1 127.0.0.1 | tail -3
echo "=== Socket stats ===" && ss -s | head -5
echo "=== Socket summary ===" && ss -s | head -5
rm /tmp/net-diag.sh 2>/dev/null
echo "Advanced Lab 2 complete"
```

## 📝 Summary
- `ping -c N host` tests ICMP connectivity; `-W` sets timeout in seconds
- `tracepath` traces the network path without root (unlike `traceroute`)
- `curl -I url` fetches only HTTP headers; `-w` formats timing info
- `ss -s` shows socket summary; `-tlnp` shows listening TCP ports
- `ss -tn dst IP` shows connections to a specific destination
- `timeout N bash -c "echo > /dev/tcp/host/port"` tests TCP port connectivity
