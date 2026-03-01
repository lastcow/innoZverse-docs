# Lab 1: Network Configuration

## 🎯 Objective
Inspect network interface configuration using ip commands, hostname, and ss to understand how your system is connected.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Foundations Lab 1: Terminal Basics
- Basic understanding of TCP/IP

## 🔬 Lab Instructions

### Step 1: View Network Interfaces

```bash
ip addr show
```

**Expected output:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 ...
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
2: ens34: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    link/ether 00:0c:29:50:6c:2e brd ff:ff:ff:ff:ff:ff
    inet 192.168.x.x/24 scope global ens34
```

```bash
# Short form
ip a
```

```bash
# Show a specific interface
ip addr show lo
ip addr show $(ip -o link show | grep -v "lo" | head -1 | cut -d: -f2 | xargs)
```

### Step 2: View Routing Table

```bash
ip route show
```

**Expected output:**
```
default via 192.168.1.1 dev ens34 proto dhcp
192.168.1.0/24 dev ens34 proto kernel scope link
```

```bash
ip route
ip route show table main
```

```bash
# Find default gateway
ip route | grep default
```

### Step 3: View Link Layer Info

```bash
ip link show
```

**Expected output:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 ...
2: ens34: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    link/ether 00:0c:29:50:6c:2e brd ff:ff:ff:ff:ff:ff
```

```bash
# Link state (UP/DOWN)
ip link show | grep -E "^[0-9]+:"
```

### Step 4: hostname Commands

```bash
# Short hostname
hostname
```

```bash
# All IP addresses
hostname -I
```

**Expected output:**
```
192.168.1.100 
```

```bash
# FQDN (may just return hostname if DNS not configured)
hostname -f 2>/dev/null || hostname
```

### Step 5: Socket Statistics with ss

```bash
# Show all sockets with numeric addresses
ss -tuln
```

**Expected output:**
```
Netid State  Recv-Q Send-Q  Local Address:Port   Peer Address:Port
udp   UNCONN 0      0       127.0.0.53:53        0.0.0.0:*
tcp   LISTEN 0      128     0.0.0.0:22           0.0.0.0:*
```

```bash
# TCP listening ports
ss -tlnp
```

```bash
# All established TCP connections
ss -tn state established | head -10
```

```bash
# Summary statistics
ss -s
```

**Expected output:**
```
Total: 150
TCP:   12 (estab 4, closed 3, orphaned 0, timewait 3)
```

### Step 6: Network Interface Statistics

```bash
# Interface statistics
ip -s link show | head -30
```

```bash
# Read from /proc/net
cat /proc/net/dev | head -10
```

```bash
# Receive and transmit statistics
cat /proc/net/dev | awk 'NR>2 { printf "%-10s RX=%s TX=%s\n", $1, $2, $10 }' | head -5
```

### Step 7: DNS Configuration

```bash
cat /etc/resolv.conf
```

```bash
cat /etc/hosts | head -10
```

```bash
# Test DNS lookup
cat /etc/nsswitch.conf | grep hosts
```

## ✅ Verification

```bash
echo "=== Interface summary ==="
ip addr show | grep "inet " | awk '{print $2, $NF}'

echo "=== Default gateway ==="
ip route | grep default | head -2

echo "=== Listening ports ==="
ss -tlnp | head -10

echo "=== Hostname ==="
hostname && hostname -I
echo "Advanced Lab 1 complete"
```

## 📝 Summary
- `ip addr show` (or `ip a`) shows all network interfaces and IP addresses
- `ip route show` displays the routing table including the default gateway
- `ip link show` shows the link layer state and MAC addresses
- `hostname -I` shows all IP addresses assigned to the host
- `ss -tuln` shows listening TCP/UDP ports with numeric addresses
- `ss -s` provides a summary of all socket states
