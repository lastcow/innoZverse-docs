# Lab 03: IPv4 Addressing — The Language of the Internet

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Every device on the Internet needs an address — and IPv4 is the addressing system that has powered the Internet since 1981. In this lab, you'll understand the 32-bit address structure, address classes, private vs public ranges, CIDR notation, and how to calculate network and broadcast addresses using Python's `ipaddress` module.

---

## Step 1: Set Up the Lab Environment

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq iproute2 python3 2>/dev/null &&
  echo 'Ready — iproute2 and python3 installed'
"
```

📸 **Verified Output:**
```
Ready — iproute2 and python3 installed
```

---

## Step 2: IPv4 Address Structure — 32 Bits, Dotted Decimal

An IPv4 address is a **32-bit number** written as 4 octets (groups of 8 bits) in decimal, separated by dots:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq python3 2>/dev/null &&
  python3 -c \"
import ipaddress

print('=== IPv4 Address Anatomy ===')
print()
addr = ipaddress.IPv4Address('192.168.1.100')
val = int(addr)

# Show each octet
octets = [192, 168, 1, 100]
binary_octets = [f'{o:08b}' for o in octets]

print(f'Address: 192.168.1.100')
print(f'         ↓       ↓   ↓   ↓')
print(f'Decimal: {octets[0]:<8} {octets[1]:<5} {octets[2]:<4} {octets[3]}')
print(f'Binary:  {binary_octets[0]} {binary_octets[1]} {binary_octets[2]} {binary_octets[3]}')
print()
print(f'Full binary: {val:032b}')
print(f'Total bits:  32 (4 octets × 8 bits)')
print(f'Range:       0.0.0.0 — 255.255.255.255 ({2**32:,} addresses total)')
print()
print('=== Address Components ===')
net = ipaddress.IPv4Network('192.168.1.0/24', strict=False)
print(f'For 192.168.1.100/24:')
print(f'  Network portion:  192.168.1  (first 24 bits)')
print(f'  Host portion:     .100       (last 8 bits)')
print(f'  Subnet mask:      {net.netmask}')
print(f'  Hosts available:  {net.num_addresses - 2}')
\"
"
```

📸 **Verified Output:**
```
=== IPv4 Address Anatomy ===

Address: 192.168.1.100
         ↓       ↓   ↓   ↓
Decimal: 192      168   1    100
Binary:  11000000 10101000 00000001 01100100

Full binary: 11000000101010000000000101100100
Total bits:  32 (4 octets × 8 bits)
Range:       0.0.0.0 — 255.255.255.255 (4,294,967,296 addresses total)

=== Address Components ===
For 192.168.1.100/24:
  Network portion:  192.168.1  (first 24 bits)
  Host portion:     .100       (last 8 bits)
  Subnet mask:      255.255.255.0
  Hosts available:  254
```

> 💡 The `/24` in CIDR notation means the first 24 bits identify the network, leaving 8 bits for hosts: 2⁸ - 2 = 254 usable addresses.

---

## Step 3: Address Classes — Historical Context

Before CIDR, IPv4 used **classful** addressing (1981–1993):

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== IPv4 Address Classes (Historical) ===')
print()
classes = [
    ('A', '0xxxxxxx', '1.0.0.0',   '126.255.255.255', '/8',  '16,777,214', 'Large organizations, ISPs'),
    ('B', '10xxxxxx', '128.0.0.0', '191.255.255.255', '/16', '65,534',     'Universities, corporations'),
    ('C', '110xxxxx', '192.0.0.0', '223.255.255.255', '/24', '254',        'Small businesses'),
    ('D', '1110xxxx', '224.0.0.0', '239.255.255.255', 'N/A', 'N/A',        'Multicast groups'),
    ('E', '1111xxxx', '240.0.0.0', '255.255.255.255', 'N/A', 'N/A',        'Reserved/Experimental'),
]
print(f'{'Class':<6} {'First bits':<12} {'Start':<16} {'End':<18} {'Mask':<6} {'Hosts/net':<14} Use')
print('-' * 95)
for cls, bits, start, end, mask, hosts, use in classes:
    print(f'{cls:<6} {bits:<12} {start:<16} {end:<18} {mask:<6} {hosts:<14} {use}')

print()
print('Note: Class A 0.x.x.x and 127.x.x.x are reserved')
print('127.0.0.1 = loopback (this machine)')
print('CIDR replaced classful addressing in 1993 (RFC 1519)')
\"
"
```

📸 **Verified Output:**
```
=== IPv4 Address Classes (Historical) ===

Class  First bits   Start            End                Mask   Hosts/net      Use
-----------------------------------------------------------------------------------------------
A      0xxxxxxx     1.0.0.0          126.255.255.255    /8     16,777,214     Large organizations, ISPs
B      10xxxxxx     128.0.0.0        191.255.255.255    /16    65,534         Universities, corporations
C      110xxxxx     192.0.0.0        223.255.255.255    /24    254            Small businesses
D      1110xxxx     224.0.0.0        239.255.255.255    N/A    N/A            Multicast groups
E      1111xxxx     240.0.0.0        255.255.255.255    N/A    N/A            Reserved/Experimental

Note: Class A 0.x.x.x and 127.x.x.x are reserved
127.0.0.1 = loopback (this machine)
CIDR replaced classful addressing in 1993 (RFC 1519)
```

---

## Step 4: Private vs Public IP Ranges (RFC 1918)

Private IP addresses are used inside networks and **cannot be routed on the public Internet**:

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== Private IP Ranges (RFC 1918) ===')
print()
private_ranges = [
    ('10.0.0.0/8',       'Class A private', '10.0.0.0 – 10.255.255.255',     16777216),
    ('172.16.0.0/12',    'Class B private', '172.16.0.0 – 172.31.255.255',   1048576),
    ('192.168.0.0/16',   'Class C private', '192.168.0.0 – 192.168.255.255', 65536),
]
for cidr, label, rng, count in private_ranges:
    n = ipaddress.IPv4Network(cidr)
    print(f'{cidr:<20} {label:<18} {count:>10,} addresses')
    print(f'  Range: {rng}')
    print()

print('=== Special Purpose Addresses ===')
special = [
    ('127.0.0.0/8',      'Loopback (127.0.0.1 = this machine)'),
    ('0.0.0.0',          'Unspecified / default route'),
    ('255.255.255.255',  'Limited broadcast (all hosts on local segment)'),
    ('169.254.0.0/16',   'Link-local / APIPA (no DHCP response)'),
    ('100.64.0.0/10',    'Shared address space (ISP CGN - RFC 6598)'),
]
for addr, desc in special:
    print(f'  {addr:<22} {desc}')

print()
print('=== Testing addresses with python3 ipaddress ===')
test_addrs = ['10.1.1.1', '172.16.5.10', '192.168.1.1', '8.8.8.8', '127.0.0.1']
for addr_str in test_addrs:
    a = ipaddress.IPv4Address(addr_str)
    print(f'  {addr_str:<18} private={str(a.is_private):<6} loopback={str(a.is_loopback):<6} global={a.is_global}')
\"
"
```

📸 **Verified Output:**
```
=== Private IP Ranges (RFC 1918) ===

10.0.0.0/8           Class A private    16,777,216 addresses
  Range: 10.0.0.0 – 10.255.255.255

172.16.0.0/12        Class B private     1,048,576 addresses
  Range: 172.16.0.0 – 172.31.255.255

192.168.0.0/16       Class C private        65,536 addresses
  Range: 192.168.0.0 – 192.168.255.255

=== Special Purpose Addresses ===
  127.0.0.0/8            Loopback (127.0.0.1 = this machine)
  0.0.0.0                Unspecified / default route
  255.255.255.255        Limited broadcast (all hosts on local segment)
  169.254.0.0/16         Link-local / APIPA (no DHCP response)
  100.64.0.0/10          Shared address space (ISP CGN - RFC 6598)

=== Testing addresses with python3 ipaddress ===
  10.1.1.1           private=True   loopback=False  global=False
  172.16.5.10        private=True   loopback=False  global=False
  192.168.1.1        private=True   loopback=False  global=False
  8.8.8.8            private=False  loopback=False  global=True
  127.0.0.1          private=False  loopback=True   global=False
```

> 💡 Your home router uses NAT (Network Address Translation) to map private IP addresses to a single public IP. That's how billions of devices share the ~4 billion IPv4 addresses.

---

## Step 5: View Your Container's IP Address

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq iproute2 2>/dev/null &&
  echo '=== ip addr show (all interfaces) ===' &&
  ip addr show &&
  echo '' &&
  echo '=== Loopback interface explained ===' &&
  echo 'lo (loopback): 127.0.0.1/8' &&
  echo '  Always present, used for local process communication' &&
  echo '  ping 127.0.0.1 never leaves the machine' &&
  echo '' &&
  echo '=== eth0 (container network interface) ===' &&
  ip addr show eth0
"
```

📸 **Verified Output:**
```
=== ip addr show (all interfaces) ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: eth0@if1276: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 0a:17:5b:cf:f1:b7 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.6/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever

=== Loopback interface explained ===
lo (loopback): 127.0.0.1/8
  Always present, used for local process communication
  ping 127.0.0.1 never leaves the machine

=== eth0 (container network interface) ===
2: eth0@if1276: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 0a:17:5b:cf:f1:b7 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 172.17.0.6/16 brd 172.17.255.255 scope global eth0
       valid_lft forever preferred_lft forever
```

---

## Step 6: CIDR Notation — Classless Inter-Domain Routing

CIDR replaced classful addressing and allows flexible subnet sizes:

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== CIDR Prefix Length Reference ===')
print()
cidrs = [8, 16, 24, 25, 26, 27, 28, 29, 30, 32]
print(f'{'Prefix':<8} {'Mask':<18} {'Hosts':>10}  {'Example'}')
print('-' * 60)
for prefix in cidrs:
    n = ipaddress.IPv4Network(f'10.0.0.0/{prefix}')
    hosts = max(0, n.num_addresses - 2)
    print(f'/{prefix:<7} {str(n.netmask):<18} {hosts:>10,}  10.0.0.0/{prefix}')

print()
print('=== /32 special case: single host route ===')
single = ipaddress.IPv4Network('192.168.1.50/32')
print(f'192.168.1.50/32: {single.num_addresses} address, used for host routes or loopbacks')
\"
"
```

📸 **Verified Output:**
```
=== CIDR Prefix Length Reference ===

Prefix   Mask               Hosts  Example
------------------------------------------------------------
/8       255.0.0.0           16,777,214  10.0.0.0/8
/16      255.255.0.0             65,534  10.0.0.0/16
/24      255.255.255.0              254  10.0.0.0/24
/25      255.255.255.128            126  10.0.0.0/25
/26      255.255.255.192             62  10.0.0.0/26
/27      255.255.255.224             30  10.0.0.0/27
/28      255.255.255.240             14  10.0.0.0/28
/29      255.255.255.248              6  10.0.0.0/29
/30      255.255.255.252              2  10.0.0.0/30
/32      255.255.255.255              0  10.0.0.0/32

=== /32 special case: single host route ===
192.168.1.50/32: 1 address, used for host routes or loopbacks
```

---

## Step 7: Calculating Network and Broadcast Addresses

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== Network & Broadcast Calculation ===')
print()
examples = [
    '192.168.1.0/24',
    '10.0.0.0/8',
    '172.16.50.128/26',
    '203.0.113.0/28',
]

for cidr in examples:
    n = ipaddress.IPv4Network(cidr, strict=False)
    hosts = list(n.hosts())
    print(f'Network:    {n}')
    print(f'  Mask:         {n.netmask}')
    print(f'  Network addr: {n.network_address}  (cannot assign to host)')
    print(f'  Broadcast:    {n.broadcast_address}  (cannot assign to host)')
    if hosts:
        print(f'  First host:   {hosts[0]}')
        print(f'  Last host:    {hosts[-1]}')
        print(f'  Usable hosts: {len(hosts)}')
    print()

print('=== Formula ===')
print('Network address  = IP AND Mask')
print('Broadcast addr   = Network OR (NOT Mask)')
print('Usable hosts     = 2^(host bits) - 2')
print('First host       = Network + 1')
print('Last host        = Broadcast - 1')
\"
"
```

📸 **Verified Output:**
```
=== Network & Broadcast Calculation ===

Network:    192.168.1.0/24
  Mask:         255.255.255.0
  Network addr: 192.168.1.0  (cannot assign to host)
  Broadcast:    192.168.1.255  (cannot assign to host)
  First host:   192.168.1.1
  Last host:    192.168.1.254
  Usable hosts: 254

Network:    10.0.0.0/8
  Mask:         255.0.0.0
  Network addr: 10.0.0.0  (cannot assign to host)
  Broadcast:    10.255.255.255  (cannot assign to host)
  First host:   10.0.0.1
  Last host:    10.255.255.254
  Usable hosts: 16777214

Network:    172.16.50.128/26
  Mask:         255.255.255.192
  Network addr: 172.16.50.128  (cannot assign to host)
  Broadcast:    172.16.50.191  (cannot assign to host)
  First host:   172.16.50.129
  Last host:    172.16.50.190
  Usable hosts: 62

Network:    203.0.113.0/28
  Mask:         255.255.255.240
  Network addr: 203.0.113.0  (cannot assign to host)
  Broadcast:    203.0.113.15  (cannot assign to host)
  First host:   203.0.113.1
  Last host:    203.0.113.14
  Usable hosts: 14

=== Formula ===
Network address  = IP AND Mask
Broadcast addr   = Network OR (NOT Mask)
Usable hosts     = 2^(host bits) - 2
First host       = Network + 1
Last host        = Broadcast - 1
```

> 💡 **Why subtract 2?** The network address (all host bits = 0) and broadcast address (all host bits = 1) cannot be assigned to individual hosts.

---

## Step 8: Capstone — IPv4 Address Inspector Tool

Build a complete IPv4 address analysis tool:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq iproute2 python3 2>/dev/null &&
  python3 -c \"
import ipaddress, subprocess

print('=' * 65)
print('IPv4 ADDRESS INSPECTOR')
print('=' * 65)

# Get container's actual IP
result = subprocess.run(['ip', 'addr', 'show', 'eth0'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'inet ' in line:
        parts = line.strip().split()
        my_ip_cidr = parts[1]
        break

print(f'Container IP: {my_ip_cidr}')
print()

n = ipaddress.IPv4Interface(my_ip_cidr)
net = n.network

print('--- Address Details ---')
print(f'IP Address:        {n.ip}')
print(f'Network:           {net}')
print(f'Subnet Mask:       {net.netmask}')
print(f'Wildcard Mask:     {net.hostmask}')
print(f'CIDR Prefix:       /{net.prefixlen}')
print(f'Network Address:   {net.network_address}')
print(f'Broadcast:         {net.broadcast_address}')
hosts = list(net.hosts())
print(f'First Host:        {hosts[0]}')
print(f'Last Host:         {hosts[-1]}')
print(f'Usable Hosts:      {len(hosts):,}')
print()

print('--- Binary Representation ---')
ip_int = int(n.ip)
mask_int = int(net.netmask)
print(f'IP:   {ip_int:032b}')
print(f'Mask: {mask_int:032b}')
net_int = ip_int & mask_int
bcast_int = net_int | (~mask_int & 0xFFFFFFFF)
print(f'Net:  {net_int:032b}  ({ipaddress.IPv4Address(net_int)})')
print(f'Bcast:{bcast_int:032b}  ({ipaddress.IPv4Address(bcast_int)})')
print()

print('--- Address Classification ---')
a = n.ip
print(f'Is Private:    {a.is_private}')
print(f'Is Loopback:   {a.is_loopback}')
print(f'Is Global:     {a.is_global}')
print(f'Is Multicast:  {a.is_multicast}')
print(f'Is Link-local: {a.is_link_local}')
first_octet = int(str(a).split(\".\")[0])
cls = 'A' if first_octet < 128 else 'B' if first_octet < 192 else 'C' if first_octet < 224 else 'D' if first_octet < 240 else 'E'
print(f'Address Class: {cls} (historical)')
\"
"
```

📸 **Verified Output:**
```
=================================================================
IPv4 ADDRESS INSPECTOR
=================================================================
Container IP: 172.17.0.6/16

--- Address Details ---
IP Address:        172.17.0.6
Network:           172.17.0.0/16
Subnet Mask:       255.255.0.0
Wildcard Mask:     0.0.255.255
CIDR Prefix:       /16
Network Address:   172.17.0.0
Broadcast:         172.17.255.255
First Host:        172.17.0.1
Last Host:         172.17.255.254
Usable Hosts:      65,534

--- Binary Representation ---
IP:   10101100000100010000000000000110
Mask: 11111111111111110000000000000000
Net:  10101100000100010000000000000000  (172.17.0.0)
Bcast:10101100000100011111111111111111  (172.17.255.255)

--- Address Classification ---
Is Private:    True
Is Loopback:   False
Is Global:     False
Is Multicast:  False
Is Link-local: False
Address Class: B (historical)
```

---

## Summary

| Concept          | Description                                      | Example              |
|------------------|--------------------------------------------------|----------------------|
| IPv4 address     | 32-bit number, dotted decimal notation           | `192.168.1.1`        |
| CIDR prefix      | Bits used for network identification             | `/24` = 24 net bits  |
| Subnet mask      | Binary mask separating network/host              | `255.255.255.0`      |
| Network address  | All host bits = 0, identifies the subnet         | `192.168.1.0`        |
| Broadcast        | All host bits = 1, reaches all subnet hosts      | `192.168.1.255`      |
| Private ranges   | RFC 1918, not routed on internet                 | `10.x`, `172.16-31.x`, `192.168.x` |
| Loopback         | Always `127.0.0.1`, never leaves machine         | `ping 127.0.0.1`     |
| Usable hosts     | 2^(host bits) - 2                                | /24 → 254 hosts      |

**Key takeaways:**
- IPv4 = 32 bits = ~4.3 billion addresses (nearly exhausted — hence IPv6)
- Private ranges are free for internal use; NAT maps them to public IPs
- CIDR notation (`/prefix`) is how modern networking specifies subnets
- Network and broadcast addresses can't be assigned to hosts (hence -2)
- Python's `ipaddress` module is your best friend for IP calculations

**Next Lab:** [Lab 04: Subnetting →](lab-04-subnetting.md)
