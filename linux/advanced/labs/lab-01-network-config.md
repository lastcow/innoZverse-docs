# Lab 1: Network Configuration with ip and nmcli

## 🎯 Objective
Configure and inspect network interfaces using `ip addr`, `ip route`, `ip link`, and `nmcli` on Ubuntu 22.04.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Ubuntu 22.04 system access
- Basic Linux command line familiarity

## 🔬 Lab Instructions

### Step 1: View Network Interfaces
```bash
ip addr show
# 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN
#     link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
#     inet 127.0.0.1/8 scope host lo
# 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP
#     link/ether 02:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff
#     inet 10.0.0.5/24 brd 10.0.0.255 scope global dynamic eth0

# Brief format
ip -brief addr show
# lo               UNKNOWN        127.0.0.1/8
# eth0             UP             10.0.0.5/24
```

### Step 2: Inspect a Specific Interface
```bash
IFACE=$(ip -brief link show | grep -v lo | awk 'NR==1{print $1}')
echo "Primary interface: $IFACE"

ip addr show dev "$IFACE"
# Shows full details: MAC, IP, broadcast, scope
```

### Step 3: View the Routing Table
```bash
ip route show
# default via 10.0.0.1 dev eth0 proto dhcp src 10.0.0.5 metric 100
# 10.0.0.0/24 dev eth0 proto kernel scope link src 10.0.0.5

# Show default gateway only
ip route show default
# default via 10.0.0.1 dev eth0
```

### Step 4: View Link Layer Details
```bash
ip link show
# 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
#     link/ether 02:11:22:33:44:55 brd ff:ff:ff:ff:ff:ff

# Check interface statistics
ip -s link show eth0
# RX: bytes  packets  errors  dropped  missed  mcast
#     ...
```

### Step 5: Add a Temporary IP Address
```bash
# Add a secondary IP (temporary, lost on reboot)
sudo ip addr add 192.168.99.1/24 dev lo
ip addr show lo
# inet 127.0.0.1/8 scope host lo
# inet 192.168.99.1/24 scope global lo

# Test connectivity
ping -c 2 192.168.99.1
# PING 192.168.99.1: 64 bytes from 192.168.99.1: icmp_seq=0 ttl=64 time=0.05 ms
```

### Step 6: Remove the Temporary IP Address
```bash
sudo ip addr del 192.168.99.1/24 dev lo
ip addr show lo
# inet 127.0.0.1/8 scope host lo  (back to original)
```

### Step 7: Bring an Interface Down and Up
```bash
# View current state
ip link show lo | grep state
# lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 ... state UNKNOWN

# Bring loopback down
sudo ip link set lo down
ip link show lo | grep state
# state DOWN

# Bring it back up
sudo ip link set lo up
ip link show lo | grep state
# state UNKNOWN
```

### Step 8: nmcli Basics — View Connections
```bash
nmcli connection show
# NAME    UUID                                  TYPE      DEVICE
# eth0    xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  ethernet  eth0

nmcli device status
# DEVICE  TYPE      STATE      CONNECTION
# eth0    ethernet  connected  eth0
# lo      loopback  unmanaged  --
```

### Step 9: nmcli — View Connection Details
```bash
nmcli connection show eth0
# connection.id:                eth0
# connection.type:              802-3-ethernet
# IP4.ADDRESS[1]:               10.0.0.5/24
# IP4.GATEWAY:                  10.0.0.1
# IP4.DNS[1]:                   8.8.8.8

# Show only IP info
nmcli -f IP4 connection show eth0
```

### Step 10: Check DNS Configuration
```bash
# View current DNS settings
resolvectl status
# Global
#   DNS Servers: 8.8.8.8 1.1.1.1
# Link 2 (eth0)
#   DNS Servers: 10.0.0.1

# Or check resolv.conf
cat /etc/resolv.conf
# nameserver 127.0.0.53
# options edns0 trust-ad
```

## ✅ Verification
```bash
ip addr show | grep 'inet ' | awk '{print $2}'
# 127.0.0.1/8
# 10.0.0.5/24

ip route show default | awk '{print "Gateway:", $3}'
# Gateway: 10.0.0.1
```

## 📝 Summary
- `ip addr show` displays interfaces and IP addresses
- `ip route show` shows the routing table; `ip route show default` for gateway
- `ip link show` and `ip -s link show` display link layer and statistics
- `ip addr add/del` manages temporary IP addresses
- `nmcli connection show` and `nmcli device status` manage NetworkManager connections
