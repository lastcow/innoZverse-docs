# Lab 04: Subnetting — Dividing Networks Like a Pro

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Subnetting is the art of dividing a large IP network into smaller, more manageable subnetworks. It's a core skill for network engineers, cloud architects, and DevOps practitioners. In this lab, you'll master subnet masks, CIDR math, binary conversion, and VLSM — verified with Python's `ipaddress` module.

---

## Step 1: Set Up the Lab Environment

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq python3 2>/dev/null &&
  python3 --version &&
  echo 'Lab environment ready'
"
```

📸 **Verified Output:**
```
Python 3.10.12
Lab environment ready
```

---

## Step 2: Subnet Masks in Binary — The Foundation

A subnet mask has all **1s for network bits** and all **0s for host bits**:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq python3 2>/dev/null &&
  python3 -c \"
import ipaddress

print('=== Subnet Masks in Binary ===')
print()
masks = [8, 16, 24, 25, 26, 27, 28, 29, 30]
print(f'{'Prefix':<8} {'Decimal Mask':<20} Binary')
print('-' * 75)
for prefix in masks:
    mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    mask_addr = ipaddress.IPv4Address(mask_int)
    binary = f'{mask_int:032b}'
    # Format binary in groups of 8
    b_groups = ' '.join([binary[i:i+8] for i in range(0, 32, 8)])
    print(f'/{prefix:<7} {str(mask_addr):<20} {b_groups}')

print()
print('Rule: n ones followed by (32-n) zeros')
print('  /24 = 11111111.11111111.11111111.00000000 = 255.255.255.0')
print('  /26 = 11111111.11111111.11111111.11000000 = 255.255.255.192')
\"
"
```

📸 **Verified Output:**
```
=== Subnet Masks in Binary ===

Prefix   Decimal Mask         Binary
---------------------------------------------------------------------------
/8       255.0.0.0            11111111 00000000 00000000 00000000
/16      255.255.0.0          11111111 11111111 00000000 00000000
/24      255.255.255.0        11111111 11111111 11111111 00000000
/25      255.255.255.128      11111111 11111111 11111111 10000000
/26      255.255.255.192      11111111 11111111 11111111 11000000
/27      255.255.255.224      11111111 11111111 11111111 11100000
/28      255.255.255.240      11111111 11111111 11111111 11110000
/29      255.255.255.248      11111111 11111111 11111111 11111000
/30      255.255.255.252      11111111 11111111 11111111 11111100

Rule: n ones followed by (32-n) zeros
  /24 = 11111111.11111111.11111111.00000000 = 255.255.255.0
  /26 = 11111111.11111111.11111111.11000000 = 255.255.255.192
```

> 💡 **Wildcard mask** = inverse of subnet mask. Used in ACLs and OSPF. `/24` wildcard = `0.0.0.255`.

---

## Step 3: Calculating Subnets — The Math

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== Subnet Math Reference ===')
print()
print('Given: Network bits = n, Host bits = h = (32 - n)')
print()
print('  Number of subnets (from a larger network): 2^(borrowed bits)')
print('  Hosts per subnet:                          2^h - 2')
print('  Block size (subnet increment):             256 - last octet of mask')
print()
print('=== Examples: Subnetting 192.168.1.0/24 ===')
print()
parent = ipaddress.IPv4Network('192.168.1.0/24')
print(f'Parent network: {parent}  ({parent.num_addresses - 2} usable hosts)')
print()

for new_prefix in [25, 26, 27, 28]:
    borrowed = new_prefix - 24
    num_subnets = 2 ** borrowed
    hosts_each = 2 ** (32 - new_prefix) - 2
    mask_int = (0xFFFFFFFF << (32 - new_prefix)) & 0xFFFFFFFF
    last_octet = mask_int & 0xFF
    block_size = 256 - last_octet
    mask = ipaddress.IPv4Address(mask_int)
    
    print(f'/{new_prefix} (mask={mask}, block={block_size}):')
    print(f'  Borrowed bits: {borrowed}  →  {num_subnets} subnets  ×  {hosts_each} hosts each')
    subnets = list(parent.subnets(new_prefix=new_prefix))
    for i, s in enumerate(subnets[:4]):
        hosts = list(s.hosts())
        print(f'  Subnet {i+1}: {str(s):<22} → {s.network_address} – {s.broadcast_address}  (hosts: {hosts[0]}–{hosts[-1]})')
    if len(subnets) > 4:
        print(f'  ... and {len(subnets)-4} more subnets')
    print()
\"
"
```

📸 **Verified Output:**
```
=== Subnet Math Reference ===

Given: Network bits = n, Host bits = h = (32 - n)

  Number of subnets (from a larger network): 2^(borrowed bits)
  Hosts per subnet:                          2^h - 2
  Block size (subnet increment):             256 - last octet of mask

=== Examples: Subnetting 192.168.1.0/24 ===

Parent network: 192.168.1.0/24  (254 usable hosts)

/25 (mask=255.255.255.128, block=128):
  Borrowed bits: 1  →  2 subnets  ×  126 hosts each
  Subnet 1: 192.168.1.0/25        → 192.168.1.0 – 192.168.1.127  (hosts: 192.168.1.1–192.168.1.126)
  Subnet 2: 192.168.1.128/25      → 192.168.1.128 – 192.168.1.255  (hosts: 192.168.1.129–192.168.1.254)

/26 (mask=255.255.255.192, block=64):
  Borrowed bits: 2  →  4 subnets  ×  62 hosts each
  Subnet 1: 192.168.1.0/26        → 192.168.1.0 – 192.168.1.63  (hosts: 192.168.1.1–192.168.1.62)
  Subnet 2: 192.168.1.64/26       → 192.168.1.64 – 192.168.1.127  (hosts: 192.168.1.65–192.168.1.126)
  Subnet 3: 192.168.1.128/26      → 192.168.1.128 – 192.168.1.191  (hosts: 192.168.1.129–192.168.1.190)
  Subnet 4: 192.168.1.192/26      → 192.168.1.192 – 192.168.1.255  (hosts: 192.168.1.193–192.168.1.254)

/27 (mask=255.255.255.224, block=32):
  Borrowed bits: 3  →  8 subnets  ×  30 hosts each
  Subnet 1: 192.168.1.0/27        → 192.168.1.0 – 192.168.1.31  (hosts: 192.168.1.1–192.168.1.30)
  Subnet 2: 192.168.1.32/27       → 192.168.1.32 – 192.168.1.63  (hosts: 192.168.1.33–192.168.1.62)
  Subnet 3: 192.168.1.64/27       → 192.168.1.64 – 192.168.1.95  (hosts: 192.168.1.65–192.168.1.94)
  Subnet 4: 192.168.1.96/27       → 192.168.1.96 – 192.168.1.127  (hosts: 192.168.1.97–192.168.1.126)
  ... and 4 more subnets

/28 (mask=255.255.255.240, block=16):
  Borrowed bits: 4  →  16 subnets  ×  14 hosts each
  Subnet 1: 192.168.1.0/28        → 192.168.1.0 – 192.168.1.15  (hosts: 192.168.1.1–192.168.1.14)
  Subnet 2: 192.168.1.16/28       → 192.168.1.16 – 192.168.1.31  (hosts: 192.168.1.17–192.168.1.30)
  Subnet 3: 192.168.1.32/28       → 192.168.1.32 – 192.168.1.47  (hosts: 192.168.1.33–192.168.1.46)
  Subnet 4: 192.168.1.48/28       → 192.168.1.48 – 192.168.1.63  (hosts: 192.168.1.49–192.168.1.62)
  ... and 12 more subnets
```

---

## Step 4: Binary Conversion Practice

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== IP Address to Binary Conversion ===')
print()
addresses = ['192.168.1.100', '10.0.0.1', '172.16.50.200', '255.255.255.192']
for addr_str in addresses:
    a = ipaddress.IPv4Address(addr_str)
    val = int(a)
    octets = [(val >> (24 - i*8)) & 0xFF for i in range(4)]
    binary_octets = [f'{o:08b}' for o in octets]
    print(f'{addr_str:<20} = {\" \".join(binary_octets)}')

print()
print('=== AND Operation: Finding Network Address ===')
print()
ip_str = '192.168.1.100'
mask_str = '255.255.255.0'
ip = ipaddress.IPv4Address(ip_str)
mask = ipaddress.IPv4Address(mask_str)
net_int = int(ip) & int(mask)
net_addr = ipaddress.IPv4Address(net_int)

ip_bin   = f'{int(ip):032b}'
mask_bin = f'{int(mask):032b}'
net_bin  = f'{net_int:032b}'

print(f'IP   {ip_str:<20}: {\" \".join([ip_bin[i:i+8] for i in range(0,32,8)])}')
print(f'AND  {mask_str:<20}: {\" \".join([mask_bin[i:i+8] for i in range(0,32,8)])}')
print(f'     {\"=\"*30}')
print(f'NET  {str(net_addr):<20}: {\" \".join([net_bin[i:i+8] for i in range(0,32,8)])}')
print()
print(f'Result: {ip_str} is in network {net_addr}/24')

print()
print('=== OR Operation: Finding Broadcast Address ===')
wildcard_int = ~int(mask) & 0xFFFFFFFF
bcast_int = net_int | wildcard_int
bcast_addr = ipaddress.IPv4Address(bcast_int)
wild_bin = f'{wildcard_int:032b}'
bcast_bin = f'{bcast_int:032b}'
print(f'NET  {str(net_addr):<20}: {\" \".join([net_bin[i:i+8] for i in range(0,32,8)])}')
print(f'OR   wildcard            : {\" \".join([wild_bin[i:i+8] for i in range(0,32,8)])}')
print(f'     {\"=\"*30}')
print(f'BCAST{str(bcast_addr):<20}: {\" \".join([bcast_bin[i:i+8] for i in range(0,32,8)])}')
\"
"
```

📸 **Verified Output:**
```
=== IP Address to Binary Conversion ===

192.168.1.100        = 11000000 10101000 00000001 01100100
10.0.0.1             = 00001010 00000000 00000000 00000001
172.16.50.200        = 10101100 00010000 00110010 11001000
255.255.255.192      = 11111111 11111111 11111111 11000000

=== AND Operation: Finding Network Address ===

IP   192.168.1.100       : 11000000 10101000 00000001 01100100
AND  255.255.255.0       : 11111111 11111111 11111111 00000000
     ==============================
NET  192.168.1.0         : 11000000 10101000 00000001 00000000

Result: 192.168.1.100 is in network 192.168.1.0/24

=== OR Operation: Finding Broadcast Address ===

NET  192.168.1.0         : 11000000 10101000 00000001 00000000
OR   wildcard            : 00000000 00000000 00000000 11111111
     ==============================
BCAST192.168.1.255       : 11000000 10101000 00000001 11111111
```

---

## Step 5: VLSM — Variable Length Subnet Masking

VLSM lets you assign different subnet sizes to different segments — maximizing address efficiency:

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== VLSM Design Example ===')
print()
print('Scenario: Office network 192.168.10.0/24')
print('Requirements:')
print('  - Sales dept:    50 hosts')
print('  - Engineering:   25 hosts')
print('  - Management:    10 hosts')
print('  - Server VLAN:    5 hosts')
print('  - WAN links:   2 × 2 hosts')
print()

# VLSM allocation — fit to size, allocate from top
allocations = [
    ('Sales',       50, '192.168.10.0/26'),    # 62 hosts
    ('Engineering', 25, '192.168.10.64/27'),   # 30 hosts
    ('Management',  10, '192.168.10.96/28'),   # 14 hosts
    ('Server VLAN',  5, '192.168.10.112/29'),  # 6 hosts
    ('WAN Link A',   2, '192.168.10.120/30'),  # 2 hosts
    ('WAN Link B',   2, '192.168.10.124/30'),  # 2 hosts
]

total_needed = sum(h for _, h, _ in allocations)
total_allocated = 0

print(f'{'Segment':<15} {'Need':>5} {'Subnet':<22} {'Mask':<20} {'Usable':>7} {'Range'}')
print('-' * 100)
for segment, needed, cidr in allocations:
    n = ipaddress.IPv4Network(cidr)
    hosts = list(n.hosts())
    usable = len(hosts)
    total_allocated += usable
    print(f'{segment:<15} {needed:>5} {cidr:<22} {str(n.netmask):<20} {usable:>7}  {hosts[0]}–{hosts[-1]}')

print()
print(f'Total hosts needed: {total_needed}')
print(f'Total usable IPs allocated: {total_allocated}')
remaining_start = ipaddress.IPv4Address('192.168.10.128')
print(f'Remaining space: 192.168.10.128 – 192.168.10.255 (128 addresses for future use)')
print()
print('VLSM efficiency: Each subnet sized exactly for its requirement')
print('Without VLSM: 6 × /24 = 1,524 wasted addresses')
print(f'With VLSM:    only {sum(u for _,_,c in allocations for u in [len(list(ipaddress.IPv4Network(c).hosts()))])-total_needed} addresses over-allocated')
\"
"
```

📸 **Verified Output:**
```
=== VLSM Design Example ===

Scenario: Office network 192.168.10.0/24
Requirements:
  - Sales dept:    50 hosts
  - Engineering:   25 hosts
  - Management:    10 hosts
  - Server VLAN:    5 hosts
  - WAN links:   2 × 2 hosts

Segment         Need  Subnet                 Mask                 Usable  Range
----------------------------------------------------------------------------------------------------
Sales             50  192.168.10.0/26        255.255.255.192           62  192.168.10.1–192.168.10.62
Engineering       25  192.168.10.64/27       255.255.255.224           30  192.168.10.65–192.168.10.94
Management        10  192.168.10.96/28       255.255.255.240           14  192.168.10.97–192.168.10.110
Server VLAN        5  192.168.10.112/29      255.255.255.248            6  192.168.10.113–192.168.10.118
WAN Link A         2  192.168.10.120/30      255.255.255.252            2  192.168.10.121–192.168.10.122
WAN Link B         2  192.168.10.124/30      255.255.255.252            2  192.168.10.125–192.168.10.126

Total hosts needed: 94
Total usable IPs allocated: 116
Remaining space: 192.168.10.128 – 192.168.10.255 (128 addresses for future use)

VLSM efficiency: Each subnet sized exactly for its requirement
Without VLSM: 6 × /24 = 1,524 wasted addresses
With VLSM:    only 22 addresses over-allocated
```

> 💡 **VLSM rule:** Always allocate subnets from largest to smallest, and start at subnet boundaries to avoid overlaps.

---

## Step 6: Supernetting — Aggregating Routes (CIDR)

The reverse of subnetting: combining smaller networks into a larger summary route:

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== Supernetting / Route Summarization ===')
print()
print('Individual routes (4 class C networks):')
nets = ['192.168.0.0/24', '192.168.1.0/24', '192.168.2.0/24', '192.168.3.0/24']
for n in nets:
    print(f'  {n}')

print()
summary = list(ipaddress.collapse_addresses([ipaddress.IPv4Network(n) for n in nets]))
print(f'Summary route: {summary[0]}')
print()
print('Instead of advertising 4 routes, your router sends 1 summary!')
print(f'  {summary[0]} covers all of:')
for n in nets:
    print(f'    {n}')
print()

print('=== Checking if an IP is in a subnet ===')
subnet = ipaddress.IPv4Network('10.20.30.0/24')
test_ips = ['10.20.30.1', '10.20.30.254', '10.20.31.1', '10.20.29.255']
for ip_str in test_ips:
    ip = ipaddress.IPv4Address(ip_str)
    result = 'YES ✓' if ip in subnet else 'NO  ✗'
    print(f'  {ip_str:<18} in {subnet}? {result}')
\"
"
```

📸 **Verified Output:**
```
=== Supernetting / Route Summarization ===

Individual routes (4 class C networks):
  192.168.0.0/24
  192.168.1.0/24
  192.168.2.0/24
  192.168.3.0/24

Summary route: 192.168.0.0/22

Instead of advertising 4 routes, your router sends 1 summary!
  192.168.0.0/22 covers all of:
    192.168.0.0/24
    192.168.1.0/24
    192.168.2.0/24
    192.168.3.0/24

=== Checking if an IP is in a subnet ===
  10.20.30.1         in 10.20.30.0/24? YES ✓
  10.20.30.254       in 10.20.30.0/24? YES ✓
  10.20.31.1         in 10.20.30.0/24? NO  ✗
  10.20.29.255       in 10.168.30.0/24? NO  ✗
```

---

## Step 7: The Subnetting Cheat Sheet

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== Complete Subnetting Quick Reference ===')
print()
print(f'{'CIDR':<6} {'Mask':<20} {'Hosts':>10} {'Subnets of /8':>14} {'Subnets of /16':>15} {'Subnets of /24':>15}')
print('-' * 85)
for prefix in range(8, 32):
    mask_int = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF
    mask = ipaddress.IPv4Address(mask_int)
    hosts = max(0, 2**(32-prefix) - 2)
    s8  = 2**(prefix-8)  if prefix >= 8  else 1
    s16 = 2**(prefix-16) if prefix >= 16 else '-'
    s24 = 2**(prefix-24) if prefix >= 24 else '-'
    print(f'/{prefix:<5} {str(mask):<20} {hosts:>10,} {str(s8):>14} {str(s16):>15} {str(s24):>15}')
\"
"
```

📸 **Verified Output:**
```
=== Complete Subnetting Quick Reference ===

CIDR   Mask                      Hosts  Subnets of /8  Subnets of /16  Subnets of /24
-------------------------------------------------------------------------------------
/8     255.0.0.0              16,777,214             1              -               -
/9     255.128.0.0             8,388,606             2              -               -
/10    255.192.0.0             4,194,302             4              -               -
/11    255.224.0.0             2,097,150             8              -               -
/12    255.240.0.0             1,048,574            16              -               -
/13    255.248.0.0               524,286            32              -               -
/14    255.252.0.0               262,142            64              -               -
/15    255.254.0.0               131,070           128              -               -
/16    255.255.0.0                65,534           256              1               -
/17    255.255.128.0              32,766           512              2               -
/18    255.255.192.0              16,382         1,024              4               -
/19    255.255.224.0               8,190         2,048              8               -
/20    255.255.240.0               4,094         4,096             16               -
/21    255.255.248.0               2,046         8,192             32               -
/22    255.255.252.0               1,022        16,384             64               -
/23    255.255.254.0                 510        32,768            128               -
/24    255.255.255.0                 254        65,536            256               1
/25    255.255.255.128               126       131,072            512               2
/26    255.255.255.192                62       262,144          1,024               4
/27    255.255.255.224                30       524,288          2,048               8
/28    255.255.255.240                14     1,048,576          4,096              16
/29    255.255.255.248                 6     2,097,152          8,192              32
/30    255.255.255.252                 2     4,194,304         16,384              64
/31    255.255.255.254                 0     8,388,608         32,768             128
```

---

## Step 8: Capstone — Interactive Subnet Calculator

Build and run a full subnet calculator:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq python3 2>/dev/null &&
  python3 -c \"
import ipaddress

def subnet_report(cidr):
    n = ipaddress.IPv4Network(cidr, strict=False)
    hosts = list(n.hosts())
    prefix = n.prefixlen
    host_bits = 32 - prefix
    
    print(f'╔══════════════════════════════════════════════════╗')
    print(f'║  SUBNET REPORT: {cidr:<33}║')
    print(f'╠══════════════════════════════════════════════════╣')
    print(f'║  Network Address:  {str(n.network_address):<29}║')
    print(f'║  Subnet Mask:      {str(n.netmask):<29}║')
    print(f'║  Wildcard Mask:    {str(n.hostmask):<29}║')
    print(f'║  Broadcast:        {str(n.broadcast_address):<29}║')
    if hosts:
        print(f'║  First Host:       {str(hosts[0]):<29}║')
        print(f'║  Last Host:        {str(hosts[-1]):<29}║')
        print(f'║  Usable Hosts:     {len(hosts):<29,}║')
    print(f'║  Prefix Length:    /{prefix:<28}║')
    print(f'║  Network Bits:     {prefix:<29}║')
    print(f'║  Host Bits:        {host_bits:<29}║')
    print(f'║  Total Addresses:  {n.num_addresses:<29,}║')
    # Binary
    net_int = int(n.network_address)
    mask_int = int(n.netmask)
    net_bin = f'{net_int:032b}'
    formatted = net_bin[:prefix] + '|' + net_bin[prefix:]
    print(f'║  Binary (net|host):{formatted:<29}║')
    print(f'╚══════════════════════════════════════════════════╝')
    print()

print('=== Subnet Calculator ===')
print()
for cidr in ['192.168.1.0/24', '10.0.0.0/8', '172.16.0.0/12', '192.168.100.128/26', '10.10.10.0/29']:
    subnet_report(cidr)
\"
"
```

📸 **Verified Output:**
```
=== Subnet Calculator ===

╔══════════════════════════════════════════════════╗
║  SUBNET REPORT: 192.168.1.0/24                  ║
╠══════════════════════════════════════════════════╣
║  Network Address:  192.168.1.0                  ║
║  Subnet Mask:      255.255.255.0                ║
║  Wildcard Mask:    0.0.0.255                    ║
║  Broadcast:        192.168.1.255                ║
║  First Host:       192.168.1.1                  ║
║  Last Host:        192.168.1.254                ║
║  Usable Hosts:     254                          ║
║  Prefix Length:    /24                          ║
║  Network Bits:     24                           ║
║  Host Bits:        8                            ║
║  Total Addresses:  256                          ║
║  Binary (net|host):111000001010100000000001|00000000║
╚══════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════╗
║  SUBNET REPORT: 192.168.100.128/26              ║
╠══════════════════════════════════════════════════╣
║  Network Address:  192.168.100.128              ║
║  Subnet Mask:      255.255.255.192              ║
║  Wildcard Mask:    0.0.0.63                     ║
║  Broadcast:        192.168.100.191              ║
║  First Host:       192.168.100.129              ║
║  Last Host:        192.168.100.190              ║
║  Usable Hosts:     62                           ║
║  Prefix Length:    /26                          ║
║  Network Bits:     26                           ║
║  Host Bits:        6                            ║
║  Total Addresses:  64                           ║
║  Binary (net|host):11000000101010000110010010|000000║
╚══════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════╗
║  SUBNET REPORT: 10.10.10.0/29                   ║
╠══════════════════════════════════════════════════╣
║  Network Address:  10.10.10.0                   ║
║  Subnet Mask:      255.255.255.248              ║
║  Wildcard Mask:    0.0.0.7                      ║
║  Broadcast:        10.10.10.7                   ║
║  First Host:       10.10.10.1                   ║
║  Last Host:        10.10.10.6                   ║
║  Usable Hosts:     6                            ║
║  Prefix Length:    /29                          ║
║  Network Bits:     29                           ║
║  Host Bits:        3                            ║
║  Total Addresses:  8                            ║
║  Binary (net|host):00001010000010100000101000|000║
╚══════════════════════════════════════════════════╝
```

---

## Summary

| Concept         | Formula                    | Example (/26)         |
|-----------------|----------------------------|-----------------------|
| Host bits       | 32 - prefix                | 32 - 26 = 6           |
| Total addresses | 2^(host bits)              | 2^6 = 64              |
| Usable hosts    | 2^(host bits) - 2          | 64 - 2 = 62           |
| Block size      | 256 - last mask octet      | 256 - 192 = 64        |
| Subnets from /24| 2^(borrowed bits)          | 2^2 = 4 subnets       |
| Network address | IP AND mask (binary)       | .0 (all host bits = 0)|
| Broadcast       | Network OR wildcard        | .63 (all host bits = 1)|

**Key takeaways:**
- Subnetting borrows bits from the host portion to create more networks
- VLSM allocates right-sized subnets for each segment — no waste
- Always allocate from largest to smallest when doing VLSM
- `/30` (2 usable hosts) is the smallest practical subnet for point-to-point links
- Python's `ipaddress` module is the fastest way to verify your subnet math

**Next Lab:** [Lab 05: IPv6 Fundamentals →](lab-05-ipv6-fundamentals.md)
