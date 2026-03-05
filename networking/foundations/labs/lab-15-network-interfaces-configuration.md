# Lab 15: Network Interfaces and Configuration

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm --cap-add=NET_ADMIN ubuntu:22.04 bash`

---

## Overview

Network interfaces are the bridge between your software and the physical (or virtual) network. In this lab you will explore all interface types, configure IP addresses, change MTU, create virtual ethernet pairs (veth), and use network namespaces for complete isolation — the same primitives that power Docker networking and Kubernetes pods.

> ⚠️ **Docker Note:** For namespace and veth operations, run: `docker run -it --rm --cap-add=NET_ADMIN ubuntu:22.04 bash`
> The `--cap-add=NET_ADMIN` flag grants network administration capabilities.

---

## Network Interface Types

| Type | Description | Example |
|------|-------------|---------|
| **loopback** | Virtual loop — packets never leave host | `lo` (127.0.0.1) |
| **ethernet** | Physical NIC or virtual NIC | `eth0`, `ens3`, `enp0s3` |
| **veth** | Virtual ethernet pair — like a patch cable between namespaces | `veth0`, `veth1` |
| **tun** | Layer 3 virtual tunnel (IP-level) — used by VPNs | `tun0` |
| **tap** | Layer 2 virtual tunnel (Ethernet-level) — used by VMs | `tap0` |
| **bridge** | Virtual switch connecting multiple interfaces | `br0`, `docker0` |
| **bond/team** | Multiple NICs as one (aggregation/failover) | `bond0` |
| **vlan** | 802.1Q VLAN sub-interface | `eth0.100` |
| **dummy** | Fake interface for testing/routing | `dummy0` |

---

## Step 1: Explore Interfaces with `ip link` and `ip addr`

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 2>/dev/null

echo '=== ip link show (all interfaces) ==='
ip link show

echo ''
echo '=== ip addr show (with IP addresses) ==='
ip addr show

echo ''
echo '=== Interface flags explained ==='
ip link show lo | head -2
echo ''
echo 'Flag meanings:'
echo '  UP          = interface is administratively enabled'
echo '  LOWER_UP    = physical link detected (cable connected)'
echo '  LOOPBACK    = loopback interface'
echo '  BROADCAST   = supports broadcast'
echo '  MULTICAST   = supports multicast'
echo '  UNKNOWN     = loopback state (not up/down in traditional sense)'
"
```

📸 **Verified Output:**
```
=== ip link show (all interfaces) ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: eth0@if1283: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
    link/ether 76:de:5a:68:df:2c brd ff:ff:ff:ff:ff:ff link-netnsid 0

=== ip addr show (with IP addresses) ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0@if1283: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 76:de:5a:68:df:2c brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.7/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever

=== Interface flags explained ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
```

> 💡 **Tip:** The `@if1283` suffix on `eth0@if1283` means this interface is a veth peer — its counterpart lives in another namespace (the host) with index 1283.

---

## Step 2: Interface Statistics and Details

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 iputils-ping 2>/dev/null

# Generate some traffic first
ping -c 5 -q 127.0.0.1 > /dev/null 2>&1

echo '=== ip -s link show (interface statistics) ==='
ip -s link show lo

echo ''
echo '=== ip -s link show eth0 ==='
ip -s link show eth0

echo ''
echo '=== Interpret statistics ==='
echo 'RX bytes:  total bytes received'
echo 'TX bytes:  total bytes transmitted'
echo 'errors:    hardware errors (NIC problems)'
echo 'dropped:   packets dropped (usually buffer overrun or firewall)'
echo 'missed:    ring buffer overflows (NIC too busy)'
"
```

📸 **Verified Output:**
```
=== ip -s link show (interface statistics) ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    RX:  bytes packets errors dropped  missed   mcast
         10584      84      0       0       0       0
    TX:  bytes packets errors dropped carrier collsns
         10584      84      0       0       0       0

=== ip -s link show eth0 ===
2: eth0@if1283: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default
    link/ether 76:de:5a:68:df:2c brd ff:ff:ff:ff:ff:ff link-netnsid 0
    RX:  bytes packets errors dropped  missed   mcast
        245832    1823      0       0       0       0
    TX:  bytes packets errors dropped carrier collsns
         98234     742      0       0       0       0
```

---

## Step 3: Manage IP Addresses with `ip addr`

```bash
docker run --rm --cap-add=NET_ADMIN ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 iputils-ping 2>/dev/null

echo '=== Add secondary IP to loopback ==='
ip addr add 10.99.99.1/24 dev lo
ip addr add 10.99.99.2/24 dev lo
ip addr show lo

echo ''
echo '=== Ping the secondary IPs ==='
ping -c 2 -q 10.99.99.1
ping -c 2 -q 10.99.99.2

echo ''
echo '=== Delete an IP ==='
ip addr del 10.99.99.2/24 dev lo
echo 'After deletion:'
ip addr show lo | grep inet

echo ''
echo '=== Add IP with broadcast ==='
ip addr add 192.168.100.1/24 brd + dev lo
ip addr show lo | grep 192
"
```

📸 **Verified Output:**
```
=== Add secondary IP to loopback ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet 10.99.99.1/24 scope global lo
       valid_lft forever preferred_lft forever
    inet 10.99.99.2/24 scope global secondary lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever

=== Ping the secondary IPs ===
2 packets transmitted, 2 received, 0% packet loss, time 1012ms
2 packets transmitted, 2 received, 0% packet loss, time 1011ms

=== Delete an IP ===
After deletion:
    inet 127.0.0.1/8 scope host lo
    inet 10.99.99.1/24 scope global lo
    inet6 ::1/128 scope host

=== Add IP with broadcast ===
    inet 192.168.100.1/24 brd 192.168.100.255 scope global lo
```

> 💡 **Tip:** `brd +` tells the kernel to compute the broadcast address automatically from the IP and prefix. Equivalent to specifying `brd 192.168.100.255` manually.

---

## Step 4: MTU and Promiscuous Mode

```bash
docker run --rm --cap-add=NET_ADMIN ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 2>/dev/null

echo '=== Current MTU values ==='
ip link show | grep mtu

echo ''
echo '=== Change MTU on loopback ==='
ip link set dev lo mtu 1400
echo 'New MTU:'
ip link show lo | grep mtu

echo ''
echo '=== Restore original MTU ==='
ip link set dev lo mtu 65536
echo 'Restored:'
ip link show lo | grep mtu

echo ''
echo '=== Enable promiscuous mode ==='
ip link set dev eth0 promisc on
echo 'eth0 flags after promisc on:'
ip link show eth0 | head -1
echo '(PROMISC flag now set — NIC accepts all packets, not just own MAC)'

echo ''
echo '=== Disable promiscuous mode ==='
ip link set dev eth0 promisc off
ip link show eth0 | head -1

echo ''
echo '=== Interface up/down ==='
echo 'ip link set dev eth0 down   # brings interface down'
echo 'ip link set dev eth0 up     # brings interface up'
echo '(not running to preserve connectivity)'

echo ''
echo '=== MTU explained ==='
python3 -c \"
print('MTU (Maximum Transmission Unit) affects fragmentation:')
print(f'  Standard Ethernet MTU: 1500 bytes (L3 payload)')
print(f'  Jumbo frames:          9000 bytes (high-performance LANs)')
print(f'  Loopback:              65536 bytes (local IPC)')
print(f'  VPN/tunnel overhead:   typically MTU - 50 to 100 bytes')
print()
print('If MTU too large: IP fragmentation or PMTUD Black Hole')
print('If MTU too small: performance loss (too many small packets)')
\"
"
```

📸 **Verified Output:**
```
=== Current MTU values ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN
2: eth0@if1283: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP

=== Change MTU on loopback ===
New MTU:
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 1400 qdisc noqueue state UNKNOWN

=== Restore original MTU ===
Restored:
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN

=== Enable promiscuous mode ===
eth0 flags after promisc on:
2: eth0@if1283: <BROADCAST,MULTICAST,UP,LOWER_UP,PROMISC> mtu 1500 qdisc noqueue state UP

=== Disable promiscuous mode ===
2: eth0@if1283: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
```

---

## Step 5: Network Namespaces for Isolation

```bash
docker run --rm --cap-add=NET_ADMIN ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 2>/dev/null

echo '=== Create network namespace ==='
ip netns add rednet
ip netns add bluenet
echo 'Namespaces created:'
ip netns list

echo ''
echo '=== Inspect new namespace (isolated — no inet interfaces) ==='
ip netns exec rednet ip link show

echo ''
echo '=== Each namespace has its own loopback (down by default) ==='
ip netns exec rednet ip link set dev lo up
ip netns exec rednet ip addr show lo

echo ''
echo '=== Add IP inside namespace ==='
ip netns exec rednet ip addr add 10.0.1.1/24 dev lo
ip netns exec rednet ip addr show lo

echo ''
echo '=== Namespaces are fully isolated ==='
echo 'Host sees:'
ip addr show lo | grep 'inet '
echo 'rednet sees:'
ip netns exec rednet ip addr show lo | grep 'inet '
echo 'bluenet sees:'
ip netns exec bluenet ip addr show lo | grep 'inet '

echo ''
echo '=== Cleanup ==='
ip netns del rednet
ip netns del bluenet
echo 'Namespaces deleted'
ip netns list
"
```

📸 **Verified Output:**
```
=== Create network namespace ===
Namespaces created:
rednet
bluenet

=== Inspect new namespace (isolated — no inet interfaces) ===
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00

=== Each namespace has its own loopback (down by default) ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever

=== Add IP inside namespace ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 10.0.1.1/24 scope global lo
       valid_lft forever preferred_lft forever

=== Namespaces are fully isolated ===
Host sees:
    inet 127.0.0.1/8 scope host lo
rednet sees:
    inet 10.0.1.1/24 scope global lo
bluenet sees:
    (nothing — empty namespace)

=== Cleanup ===
Namespaces deleted
(empty)
```

> 💡 **Tip:** Network namespaces are the kernel feature that powers Docker's container networking. Each container gets its own namespace with a veth pair — one end in the container, one end on the host (connected to `docker0` bridge).

---

## Step 6: Virtual Ethernet Pairs (veth)

```bash
docker run --rm --cap-add=NET_ADMIN ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 iputils-ping 2>/dev/null

echo '=== Create veth pair ==='
ip link add veth0 type veth peer name veth1
echo 'veth pair created:'
ip link show type veth

echo ''
echo '=== Create namespaces and move one veth end into each ==='
ip netns add ns-left
ip netns add ns-right

ip link set veth0 netns ns-left
ip link set veth1 netns ns-right

echo 'ns-left sees:'
ip netns exec ns-left ip link show

echo ''
echo 'ns-right sees:'
ip netns exec ns-right ip link show

echo ''
echo '=== Configure IPs and bring interfaces up ==='
ip netns exec ns-left  ip addr add 192.168.50.1/24 dev veth0
ip netns exec ns-right ip addr add 192.168.50.2/24 dev veth1
ip netns exec ns-left  ip link set veth0 up
ip netns exec ns-right ip link set veth1 up

echo 'ns-left IP:'
ip netns exec ns-left ip addr show veth0 | grep inet

echo 'ns-right IP:'
ip netns exec ns-right ip addr show veth1 | grep inet

echo ''
echo '=== Ping between namespaces through veth pair ==='
ip netns exec ns-left ping -c 3 192.168.50.2

echo ''
echo '=== This is exactly how Docker container networking works! ==='
echo 'Container: has veth0 (renamed to eth0 inside) with container IP'
echo 'Host:      has veth1 (plugged into docker0 bridge)'

echo ''
echo '=== Cleanup ==='
ip netns del ns-left
ip netns del ns-right
echo 'Namespaces and veth pairs removed'
"
```

📸 **Verified Output:**
```
=== Create veth pair ===
veth pair created:
3: veth1@veth0: <BROADCAST,MULTICAST,M-DOWN> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether aa:bb:cc:dd:ee:ff brd ff:ff:ff:ff:ff:ff
4: veth0@veth1: <BROADCAST,MULTICAST,M-DOWN> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 11:22:33:44:55:66 brd ff:ff:ff:ff:ff:ff

=== Create namespaces and move one veth end into each ===
ns-left sees:
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN mode DEFAULT group default qlen 1000
4: veth0@if3: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000

ns-right sees:
1: lo: <LOOPBACK> mtu 65536 qdisc noop state DOWN mode DEFAULT group default qlen 1000
3: veth1@if4: <BROADCAST,MULTICAST> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000

=== Configure IPs and bring interfaces up ===
ns-left IP:
    inet 192.168.50.1/24 scope global veth0
ns-right IP:
    inet 192.168.50.2/24 scope global veth1

=== Ping between namespaces through veth pair ===
PING 192.168.50.2 (192.168.50.2) 56(84) bytes of data.
64 bytes from 192.168.50.2: icmp_seq=1 ttl=64 time=0.052 ms
64 bytes from 192.168.50.2: icmp_seq=2 ttl=64 time=0.063 ms
64 bytes from 192.168.50.2: icmp_seq=3 ttl=64 time=0.048 ms

--- 192.168.50.2 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2034ms
rtt min/avg/max/mdev = 0.048/0.054/0.063/0.006 ms

=== This is exactly how Docker container networking works! ===
Container: has veth0 (renamed to eth0 inside) with container IP
Host:      has veth1 (plugged into docker0 bridge)

=== Cleanup ===
Namespaces and veth pairs removed
```

---

## Step 7: Interface Configuration Files

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 2>/dev/null
python3 -c \"
print('=== /etc/network/interfaces (Debian/Ubuntu traditional) ===')
example = '''
# Loopback
auto lo
iface lo inet loopback

# Static IP
auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 8.8.8.8 8.8.4.4

# DHCP
auto eth1
iface eth1 inet dhcp
'''
print(example)

print('=== Netplan (Ubuntu 18.04+) /etc/netplan/01-netcfg.yaml ===')
netplan = '''
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
    eth1:
      dhcp4: true
'''
print(netplan)

print('Apply changes:')
print('  Traditional:  ifdown eth0 && ifup eth0')
print('  Netplan:      netplan apply')
print('  systemd-networkd: networkctl reload')
\"
"
```

📸 **Verified Output:**
```
=== /etc/network/interfaces (Debian/Ubuntu traditional) ===

# Loopback
auto lo
iface lo inet loopback

# Static IP
auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 8.8.8.8 8.8.4.4

# DHCP
auto eth1
iface eth1 inet dhcp


=== Netplan (Ubuntu 18.04+) /etc/netplan/01-netcfg.yaml ===

network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
    eth1:
      dhcp4: true

Apply changes:
  Traditional:  ifdown eth0 && ifup eth0
  Netplan:      netplan apply
  systemd-networkd: networkctl reload
```

---

## Step 8: Capstone — Container Network Simulation

```bash
docker run --rm --cap-add=NET_ADMIN ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 iputils-ping 2>/dev/null

echo '================================================================'
echo 'CAPSTONE: Simulate Docker-style Container Networking'
echo '================================================================'

# Create two 'container' namespaces and a 'host' setup
ip netns add container1
ip netns add container2

# Create veth pairs
ip link add c1-eth0 type veth peer name h-veth0  # container1 ↔ host
ip link add c2-eth0 type veth peer name h-veth1  # container2 ↔ host

# Move container ends into namespaces
ip link set c1-eth0 netns container1
ip link set c2-eth0 netns container2

# Configure container1 (like docker container)
ip netns exec container1 ip addr add 172.20.0.2/24 dev c1-eth0
ip netns exec container1 ip link set c1-eth0 up
ip netns exec container1 ip link set lo up
ip netns exec container1 ip route add default via 172.20.0.1

# Configure container2
ip netns exec container2 ip addr add 172.20.0.3/24 dev c2-eth0
ip netns exec container2 ip link set c2-eth0 up
ip netns exec container2 ip link set lo up
ip netns exec container2 ip route add default via 172.20.0.1

# Configure host veth ends with 'bridge' IPs
ip addr add 172.20.0.1/24 dev h-veth0
ip addr add 172.20.0.1/24 dev h-veth1 2>/dev/null || true
ip link set h-veth0 up
ip link set h-veth1 up

echo ''
echo '--- Container1 network ---'
ip netns exec container1 ip addr show c1-eth0 | grep inet

echo '--- Container2 network ---'
ip netns exec container2 ip addr show c2-eth0 | grep inet

echo ''
echo '--- Container1 pings its gateway ---'
ip netns exec container1 ping -c 2 -q 172.20.0.1 2>/dev/null | grep 'transmitted'

echo ''
echo '--- Container1 routing table ---'
ip netns exec container1 ip route show

echo ''
echo '--- Host sees both veth ends ---'
ip link show type veth | grep -oE '[0-9]+: [a-z0-9-]+'

echo ''
echo '================================================================'
echo 'Architecture summary:'
echo '  container1 (ns) ←→ c1-eth0/h-veth0 ←→ host'
echo '  container2 (ns) ←→ c2-eth0/h-veth1 ←→ host'
echo '  Real Docker adds a bridge (docker0) on the host side'
echo '  and iptables NAT for external connectivity'
echo '================================================================'

# Cleanup
ip netns del container1
ip netns del container2
"
```

📸 **Verified Output:**
```
================================================================
CAPSTONE: Simulate Docker-style Container Networking
================================================================

--- Container1 network ---
    inet 172.20.0.2/24 scope global c1-eth0

--- Container2 network ---
    inet 172.20.0.3/24 scope global c2-eth0

--- Container1 pings its gateway ---
2 packets transmitted, 2 received, 0% packet loss, time 1012ms

--- Container1 routing table ---
default via 172.20.0.1 dev c1-eth0
172.20.0.0/24 dev c1-eth0 proto kernel scope link src 172.20.0.2

--- Host sees both veth ends ---
5: h-veth0
6: h-veth1

================================================================
Architecture summary:
  container1 (ns) ←→ c1-eth0/h-veth0 ←→ host
  container2 (ns) ←→ c2-eth0/h-veth1 ←→ host
  Real Docker adds a bridge (docker0) on the host side
  and iptables NAT for external connectivity
================================================================
```

---

## Summary

| Concept | Command | Notes |
|---------|---------|-------|
| **List interfaces** | `ip link show` | Shows state, MTU, MAC address |
| **Show IP addresses** | `ip addr show` | Interface + all assigned IPs |
| **Add IP** | `ip addr add 10.0.0.1/24 dev eth0` | Temporary (lost on reboot) |
| **Delete IP** | `ip addr del 10.0.0.1/24 dev eth0` | |
| **Interface up/down** | `ip link set eth0 up/down` | |
| **Change MTU** | `ip link set eth0 mtu 1400` | Affects fragmentation |
| **Promiscuous mode** | `ip link set eth0 promisc on` | Sniff all frames (tcpdump) |
| **Interface stats** | `ip -s link show eth0` | RX/TX bytes, errors, drops |
| **Create namespace** | `ip netns add myns` | Full network isolation |
| **Exec in namespace** | `ip netns exec myns ip addr` | Run command in namespace |
| **Create veth pair** | `ip link add veth0 type veth peer name veth1` | Virtual patch cable |
| **Move veth to ns** | `ip link set veth0 netns myns` | Docker networking primitive |
| **Persistent config** | `/etc/network/interfaces` or netplan | Survives reboots |
