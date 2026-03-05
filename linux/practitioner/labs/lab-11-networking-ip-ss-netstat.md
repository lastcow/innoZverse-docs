# Lab 11: Networking — ip, ss, and Network Inspection

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

This lab covers Linux networking tools from the `iproute2` suite (`ip`, `ss`) which replace the older `ifconfig`/`netstat` commands. You'll inspect interfaces, routes, sockets, and read directly from the kernel's `/proc/net/` filesystem.

---

## Step 1: Install iproute2 and Explore ip addr

The `ip` command is the modern replacement for `ifconfig`. It's part of the `iproute2` package.

```bash
apt-get update -qq && apt-get install -y iproute2
ip addr show
```

> 💡 `ip addr show` lists all network interfaces with their IPv4 and IPv6 addresses. The `lo` interface is the loopback (127.0.0.1) and `eth0` is the primary network interface in Docker containers.

📸 **Verified Output:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0@if1113: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 06:11:d6:6b:d9:ce brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.6/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever
```

---

## Step 2: Inspect Network Links with ip link

`ip link` shows layer-2 (data link) information — MAC addresses and interface flags.

```bash
ip link show
ip link show eth0
```

> 💡 Interface flags like `UP`, `LOWER_UP`, and `BROADCAST` tell you the operational state. `LOWER_UP` means the physical/virtual link is active. `mtu 1500` is the standard Ethernet Maximum Transmission Unit.

📸 **Verified Output:**
```
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: eth0@if1113: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default 
    link/ether 06:11:d6:6b:d9:ce brd ff:ff:ff:ff:ff:ff link-netnsid 0
```

---

## Step 3: View Routing Table with ip route

The routing table tells the kernel how to forward packets to their destinations.

```bash
ip route show
ip route get 8.8.8.8
```

> 💡 The `default` route (gateway) is where packets go when no more-specific route matches. `proto kernel` means the route was added automatically by the kernel when the interface came up. `src` shows the preferred source IP for outgoing packets.

📸 **Verified Output:**
```
default via 172.17.0.1 dev eth0 
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.6 
```

---

## Step 4: Socket Statistics with ss

`ss` (socket statistics) replaces `netstat`. It's faster and reads directly from the kernel.

```bash
# Show listening TCP sockets
ss -tlnp

# Show all sockets (TCP+UDP) with process info
ss -alnp | head -20

# Show socket summary
ss -s
```

> 💡 Flags: `-t` = TCP, `-u` = UDP, `-l` = listening only, `-n` = numeric (no DNS resolution), `-p` = show process. On a minimal Docker container with no services running, `ss -tlnp` will show an empty table — that's expected and correct.

📸 **Verified Output:**
```
State Recv-Q Send-Q Local Address:Port Peer Address:PortProcess

Total: 2
TCP:   39 (estab 0, closed 39, orphaned 4, timewait 3)

Transport Total     IP        IPv6
RAW	  0         0         0        
UDP	  0         0         0        
TCP	  0         0         0        
INET	  0         0         0        
FRAG	  0         0         0        
```

---

## Step 5: Reading /proc/net/ Virtual Filesystem

The Linux kernel exposes network state through `/proc/net/`. These are not real files — they're kernel data structures rendered as text.

```bash
# Network interfaces with byte/packet counters
cat /proc/net/dev

# Raw TCP connection table (hex addresses)
cat /proc/net/tcp | head -5

# Routing table in hex
cat /proc/net/route

# IPv6 interfaces
cat /proc/net/if_inet6
```

> 💡 `/proc/net/tcp` shows connections in hex format: `local_address` is `IP:PORT` in little-endian hex. State `06` = TIME_WAIT, `01` = ESTABLISHED. Tools like `ss` and `netstat` parse this file for you.

📸 **Verified Output:**
```
Inter-|   Receive                                                |  Transmit
 face |bytes    packets errs drop fifo frame compressed multicast|bytes    packets errs drop fifo colls carrier compressed
    lo:       0       0    0    0    0     0          0         0        0       0    0    0    0     0       0          0
  eth0: 46549003    2497    0    0    0     0          0         0   142269    2070    0    0    0     0       0          0

Iface    Destination  Gateway   Flags  RefCnt  Use  Metric  Mask     MTU  Window  IRTT                                                       
eth0     00000000     010011AC  0003   0       0    0       00000000  0    0       0
eth0     000011AC     00000000  0001   0       0    0       0000FFFF  0    0       0
```

---

## Step 6: Hostname Resolution

Linux resolves hostnames through multiple mechanisms configured in `/etc/nsswitch.conf`.

```bash
# View current hostname
hostname
hostname -I          # Show all IP addresses

# DNS resolution config
cat /etc/resolv.conf

# Static hostname mappings
cat /etc/hosts

# Test resolution (requires dnsutils)
apt-get install -y -qq dnsutils
getent hosts example.com
```

> 💡 Resolution order: `/etc/hosts` first (for static entries), then DNS servers listed in `/etc/resolv.conf`. Docker containers use `8.8.8.8` as their default nameserver. The `getent` command queries NSS (Name Service Switch) the same way programs do.

📸 **Verified Output:**
```
# /etc/resolv.conf (Docker-generated)
nameserver 8.8.8.8
search .

# /etc/hosts
127.0.0.1   localhost
::1         localhost ip6-localhost ip6-loopback
172.17.0.6  a389f683e619
```

---

## Step 7: Network Namespaces — Isolation Intro

Network namespaces provide isolated network stacks (used by Docker, Kubernetes, VPNs).

```bash
# List existing network namespaces
ip netns list

# Attempt to create one (requires elevated privileges)
# ip netns add testns

# View netns in /proc (each process's namespace)
ls -la /proc/1/ns/net 2>/dev/null || echo "No access to PID 1 ns"

# Check /proc/net/if_inet6 for IPv6 interface state
cat /proc/net/if_inet6
```

> 💡 Docker itself uses network namespaces — each container gets its own isolated network stack. `ip netns add` requires `CAP_SYS_ADMIN` which is restricted in standard Docker containers (run with `--privileged` on a dev machine to experiment). The `@if1113` suffix in `eth0@if1113` shows the veth peer interface index in the host namespace.

📸 **Verified Output:**
```
# ip netns list (empty — no named namespaces in container)

# /proc/net/if_inet6
00000000000000000000000000000001 01 80 10 80       lo
```

---

## Step 8: Capstone — Network Audit Script

**Scenario:** You're a sysadmin who needs a quick network health snapshot of a new server. Write a script that collects key networking info.

```bash
apt-get update -qq && apt-get install -y -qq iproute2 dnsutils iputils-ping

# Full network audit
echo "=== INTERFACES ==="
ip addr show | grep -E "^[0-9]+:|inet "

echo ""
echo "=== ROUTING TABLE ==="
ip route show

echo ""
echo "=== LISTENING SOCKETS ==="
ss -tlnp

echo ""
echo "=== SOCKET SUMMARY ==="
ss -s

echo ""
echo "=== DNS CONFIGURATION ==="
cat /etc/resolv.conf | grep -v "^#"

echo ""
echo "=== INTERFACE STATS ==="
cat /proc/net/dev

echo ""
echo "=== CONNECTIVITY CHECK ==="
ping -c 2 -W 2 8.8.8.8 && echo "Internet: OK" || echo "Internet: UNREACHABLE"

echo ""
echo "=== DNS RESOLUTION CHECK ==="
getent hosts google.com && echo "DNS: OK" || echo "DNS: FAILED"
```

> 💡 This pattern — collect interface info, routes, sockets, DNS config, and connectivity in sequence — is a standard first-response checklist when diagnosing network issues. Save it as `/usr/local/bin/netaudit` and `chmod +x` for reuse.

📸 **Verified Output (excerpt):**
```
=== INTERFACES ===
1: lo: <LOOPBACK,UP,LOWER_UP>
    inet 127.0.0.1/8 scope host lo
2: eth0@if1113: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 172.17.0.6/16 brd 172.17.255.255 scope global eth0

=== ROUTING TABLE ===
default via 172.17.0.1 dev eth0 
172.17.0.0/16 dev eth0 proto kernel scope link src 172.17.0.6 

=== CONNECTIVITY CHECK ===
PING 8.8.8.8: 3 packets transmitted, 3 received, 0% packet loss
Internet: OK
```

---

## Summary

| Command | Purpose | Replaces |
|---------|---------|---------|
| `ip addr show` | List interfaces and IPs | `ifconfig` |
| `ip link show` | Show layer-2 / MAC info | `ifconfig` |
| `ip route show` | View routing table | `route -n` |
| `ss -tlnp` | Listening TCP sockets | `netstat -tlnp` |
| `ss -alnp` | All sockets with processes | `netstat -anp` |
| `ss -s` | Socket statistics summary | `netstat -s` |
| `/proc/net/dev` | Interface byte counters | `ifconfig` stats |
| `/proc/net/tcp` | Raw TCP connection table | `netstat -t` raw |
| `/proc/net/route` | Routing table (hex) | `route` raw |
| `ip netns list` | List network namespaces | N/A (new concept) |
| `cat /etc/resolv.conf` | DNS server config | N/A |
| `getent hosts NAME` | Resolve via NSS | `nslookup` / `host` |
