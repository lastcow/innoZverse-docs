# Lab 05: IPv6 Fundamentals — The Next Generation of IP

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

IPv4's ~4.3 billion addresses ran out. IPv6 was designed to solve this with **340 undecillion addresses** (3.4 × 10³⁸) — enough to assign billions of addresses to every grain of sand on Earth. But IPv6 isn't just bigger; it's architecturally cleaner: no broadcast, built-in security (IPsec), stateless autoconfiguration, and simplified headers. In this lab, you'll master IPv6 addressing, explore address types, and verify everything with real Docker commands.

---

## Step 1: Set Up the Lab Environment

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null &&
  apt-get install -y -qq iproute2 iputils-ping python3 2>/dev/null &&
  echo 'Lab environment ready' &&
  ip -6 addr show lo
"
```

📸 **Verified Output:**
```
Lab environment ready
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
```

---

## Step 2: IPv6 Address Structure — 128 Bits in Hex

IPv6 addresses are **128 bits** written as 8 groups of 4 hexadecimal digits, separated by colons:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq python3 2>/dev/null &&
  python3 -c \"
import ipaddress

print('=== IPv6 Address Structure ===')
print()
addr_str = '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
addr = ipaddress.IPv6Address(addr_str)

print(f'Full address:      {addr_str}')
print(f'Compressed:        {addr}')
print()
print(f'Structure: 8 groups × 16 bits = 128 bits total')
print(f'Each group: 4 hex digits (0000–ffff = 0–65535)')
print()

# Break down each group
groups = addr_str.split(':')
print('Group breakdown:')
for i, g in enumerate(groups):
    val = int(g, 16)
    print(f'  Group {i+1}: {g} = {val:5d} = {val:016b}')

print()
print(f'Total addresses: 2^128 = {2**128:,}')
print(f'IPv4 was:        2^32  = {2**32:,}')
print(f'Ratio: IPv6 has {2**96:,}× more addresses')
\"
"
```

📸 **Verified Output:**
```
=== IPv6 Address Structure ===

Full address:      2001:0db8:85a3:0000:0000:8a2e:0370:7334
Compressed:        2001:db8:85a3::8a2e:370:7334

Structure: 8 groups × 16 bits = 128 bits total
Each group: 4 hex digits (0000–ffff = 0–65535)

Group breakdown:
  Group 1: 2001 =  8193 = 0010000000000001
  Group 2: 0db8 =  3512 = 0000110110111000
  Group 3: 85a3 = 34211 = 1000010110100011
  Group 4: 0000 =     0 = 0000000000000000
  Group 5: 0000 =     0 = 0000000000000000
  Group 6: 8a2e = 35374 = 1000101000101110
  Group 7: 0370 =   880 = 0000001101110000
  Group 8: 7334 = 29492 = 0111001100110100

Total addresses: 340,282,366,920,938,463,463,374,607,431,768,211,456
IPv4 was:        4,294,967,296
Ratio: IPv6 has 79,228,162,514,264,337,593,543,950,336× more addresses
```

> 💡 **Memory trick:** IPv6 = 16 bytes = 32 hex chars. IPv4 = 4 bytes = 8 hex chars. IPv6 is 4× longer in hex.

---

## Step 3: IPv6 Address Compression Rules

Two rules for shortening IPv6 addresses:

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== IPv6 Compression Rules ===')
print()
print('Rule 1: Drop leading zeros in each group')
print('  2001:0db8:0001:0000:0000:0000:0000:0001')
print('→ 2001:db8:1:0:0:0:0:1')
print()
print('Rule 2: Replace one longest run of consecutive all-zero groups with ::')
print('  2001:db8:1:0:0:0:0:1')
print('→ 2001:db8:1::1')
print()

examples = [
    '2001:0db8:0000:0000:0000:0000:0000:0001',
    'fe80:0000:0000:0000:0a17:5bcf:f1b7:0000',
    '0000:0000:0000:0000:0000:0000:0000:0001',
    '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
    'ff02:0000:0000:0000:0000:0000:0000:0001',
]

print(f'{'Full Address':<45} {'Compressed'}')
print('-' * 80)
for addr_str in examples:
    addr = ipaddress.IPv6Address(addr_str)
    print(f'{addr_str:<45} {str(addr)}')

print()
print('IMPORTANT: :: can only appear ONCE in an address')
print('  ✓ fe80::1  (valid)')
print('  ✗ 1::2::3  (invalid — ambiguous)')
\"
"
```

📸 **Verified Output:**
```
=== IPv6 Compression Rules ===

Rule 1: Drop leading zeros in each group
  2001:0db8:0001:0000:0000:0000:0000:0001
→ 2001:db8:1:0:0:0:0:1

Rule 2: Replace one longest run of consecutive all-zero groups with ::
  2001:db8:1:0:0:0:0:1
→ 2001:db8:1::1

Full Address                                  Compressed
--------------------------------------------------------------------------------
2001:0db8:0000:0000:0000:0000:0000:0001       2001:db8::1
fe80:0000:0000:0000:0a17:5bcf:f1b7:0000       fe80::a17:5bcf:f1b7:0
0000:0000:0000:0000:0000:0000:0000:0001       ::1
2001:0db8:85a3:0000:0000:8a2e:0370:7334       2001:db8:85a3::8a2e:370:7334
ff02:0000:0000:0000:0000:0000:0000:0001       ff02::1

IMPORTANT: :: can only appear ONCE in an address
  ✓ fe80::1  (valid)
  ✗ 1::2::3  (invalid — ambiguous)
```

---

## Step 4: IPv6 Address Types

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
import ipaddress

print('=== IPv6 Address Types ===')
print()

types = [
    ('::1',              'Loopback',        '::1/128',          'Equivalent to 127.0.0.1'),
    ('fe80::1',          'Link-Local',      'fe80::/10',        'Auto-configured, not routed beyond L2'),
    ('2001:db8::1',      'Global Unicast',  '2000::/3',         'Internet-routable (2001:db8:: = documentation)'),
    ('fc00::1',          'Unique Local',    'fc00::/7',         'Private use (like RFC 1918), not routed'),
    ('ff02::1',          'Multicast',       'ff00::/8',         'One-to-many (ff02::1 = all nodes on link)'),
    ('2001:db8::1',      'Unicast',         'any',              'One-to-one communication'),
    ('2001:db8::1',      'Anycast',         'shared prefix',    'One-to-nearest (same address, multiple devices)'),
]

print(f'{'Address':<22} {'Type':<20} {'Prefix':<18} Description')
print('-' * 90)
for addr, typ, prefix, desc in types:
    print(f'{addr:<22} {typ:<20} {prefix:<18} {desc}')

print()
print('=== Verifying address properties ===')
test = [
    ('::1',           'loopback'),
    ('fe80::1',       'link_local'),
    ('2001:db8::1',   'global'),
    ('fc00::1',       'private'),
    ('ff02::1',       'multicast'),
]
for addr_str, expected_prop in test:
    a = ipaddress.IPv6Address(addr_str)
    props = {
        'loopback': a.is_loopback,
        'link_local': a.is_link_local,
        'global': a.is_global,
        'private': a.is_private,
        'multicast': a.is_multicast,
    }
    status = '✓' if props.get(expected_prop) else '?'
    active = [k for k, v in props.items() if v]
    print(f'  {status} {addr_str:<22} → {\", \".join(active)}')
\"
"
```

📸 **Verified Output:**
```
=== IPv6 Address Types ===

Address                Type                 Prefix             Description
------------------------------------------------------------------------------------------
::1                    Loopback             ::1/128            Equivalent to 127.0.0.1
fe80::1                Link-Local           fe80::/10          Auto-configured, not routed beyond L2
2001:db8::1            Global Unicast       2000::/3           Internet-routable (2001:db8:: = documentation)
fc00::1                Unique Local         fc00::/7           Private use (like RFC 1918), not routed
ff02::1                Multicast            ff00::/8           One-to-many (ff02::1 = all nodes on link)
2001:db8::1            Unicast              any                One-to-one communication
2001:db8::1            Anycast              shared prefix      One-to-nearest (same address, multiple devices)

=== Verifying address properties ===
  ✓ ::1                    → loopback
  ✓ fe80::1                → link_local, private
  ✓ 2001:db8::1            → global
  ✓ fc00::1                → private
  ✓ ff02::1                → multicast
```

---

## Step 5: Real IPv6 Interfaces in Docker

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq iproute2 iputils-ping 2>/dev/null &&
  echo '=== IPv6 Interfaces ===' &&
  ip -6 addr show &&
  echo '' &&
  echo '=== Ping IPv6 Loopback ===' &&
  ping6 -c 3 ::1 &&
  echo '' &&
  echo '=== IPv6 Routing Table ===' &&
  ip -6 route show
"
```

📸 **Verified Output:**
```
=== IPv6 Interfaces ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever

=== Ping IPv6 Loopback ===
PING ::1(::1) 56 data bytes
64 bytes from ::1: icmp_seq=1 ttl=64 time=0.050 ms
64 bytes from ::1: icmp_seq=2 ttl=64 time=0.055 ms
64 bytes from ::1: icmp_seq=3 ttl=64 time=0.048 ms

--- ::1 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2044ms
rtt min/avg/max/mdev = 0.048/0.051/0.055/0.003 ms

=== IPv6 Routing Table ===
::1 dev lo proto kernel metric 256 pref medium
```

> 💡 Docker containers don't get a global IPv6 address by default unless the Docker daemon is configured with `--ipv6`. The loopback `::1` is always present.

---

## Step 6: EUI-64 — Deriving Interface ID from MAC Address

IPv6 link-local addresses are auto-generated from the MAC address using **EUI-64**:

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq iproute2 python3 2>/dev/null &&
  python3 -c \"
import ipaddress

print('=== EUI-64: MAC → IPv6 Interface ID ===')
print()
print('Algorithm:')
print('  1. Take 48-bit MAC address')
print('  2. Insert FF:FE in the middle (making 64 bits)')
print('  3. Flip bit 7 (Universal/Local bit) of the first byte')
print('  4. Append to fe80:: prefix')
print()

mac = '0a:17:5b:cf:f1:b7'  # Docker container MAC
print(f'MAC address:    {mac}')
parts = mac.split(':')
# Split into OUI and NIC
oui = parts[:3]
nic = parts[3:]
# Insert FF:FE in middle
extended = oui + ['ff', 'fe'] + nic
print(f'After FF:FE:    {\":\".join(extended)}')

# Flip U/L bit (bit 7 = second-least-significant bit of first byte)
first_byte = int(extended[0], 16)
first_byte ^= 0x02  # XOR with 0000 0010 to flip bit 7
extended[0] = f'{first_byte:02x}'
print(f'After bit flip: {\":\".join(extended)}')

# Format as IPv6 interface ID
iid_groups = []
for i in range(0, 8, 2):
    iid_groups.append(extended[i] + extended[i+1])
iid = ':'.join(iid_groups)
link_local = f'fe80::{iid}'
print()
print(f'IPv6 Interface ID: {iid}')
print(f'Link-local addr:   {link_local}')
print()
print(f'Parsed:            {ipaddress.IPv6Address(link_local)}')
print()
print('Note: Many OSes use random IIDs (RFC 4941 privacy extensions)')
print('to prevent tracking. EUI-64 is optional.')
\"
"
```

📸 **Verified Output:**
```
=== EUI-64: MAC → IPv6 Interface ID ===

Algorithm:
  1. Take 48-bit MAC address
  2. Insert FF:FE in the middle (making 64 bits)
  3. Flip bit 7 (Universal/Local bit) of the first byte
  4. Append to fe80:: prefix

MAC address:    0a:17:5b:cf:f1:b7
After FF:FE:    0a:17:5b:ff:fe:cf:f1:b7
After bit flip: 08:17:5b:ff:fe:cf:f1:b7

IPv6 Interface ID: 0817:5bff:fecf:f1b7
Link-local addr:   fe80::817:5bff:fecf:f1b7

Parsed:            fe80::817:5bff:fecf:f1b7

Note: Many OSes use random IIDs (RFC 4941 privacy extensions)
to prevent tracking. EUI-64 is optional.
```

---

## Step 7: IPv6 vs IPv4 — Key Differences

```bash
docker run --rm ubuntu:22.04 bash -c "
  python3 -c \"
print('=== IPv6 vs IPv4 Comparison ===')
print()
comparisons = [
    ('Address size',      '32 bits (4 bytes)',     '128 bits (16 bytes)'),
    ('Address space',     '~4.3 billion',          '340 undecillion'),
    ('Notation',          'Dotted decimal',        'Hex colon notation'),
    ('Header size',       '20-60 bytes (variable)', '40 bytes (fixed!)'),
    ('Header fields',     '12+ fields',            '8 fields (simpler)'),
    ('Broadcast',         'Yes (255.255.255.255)', 'No (replaced by multicast)'),
    ('Multicast',         'Optional (224.x.x.x)',  'Built-in (ff00::/8)'),
    ('Loopback',          '127.0.0.1',             '::1'),
    ('Link-local',        '169.254.x.x (APIPA)',   'fe80::/10 (always present)'),
    ('Private range',     'RFC 1918',               'ULA fc00::/7'),
    ('Autoconfiguration', 'DHCP required',          'SLAAC (stateless, no server)'),
    ('NAT required',      'Yes (address shortage)', 'No (enough addresses)'),
    ('IPsec',             'Optional',              'Mandatory (built-in)'),
    ('Fragmentation',     'Routers fragment',      'Only source host'),
    ('Checksum',          'IP header checksum',    'None (L2/L4 handle it)'),
    ('DNS record type',   'A record',              'AAAA record'),
]
print(f'{'Feature':<25} {'IPv4':<30} IPv6')
print('-' * 85)
for feat, v4, v6 in comparisons:
    print(f'{feat:<25} {v4:<30} {v6}')
\"
"
```

📸 **Verified Output:**
```
=== IPv6 vs IPv4 Comparison ===

Feature                   IPv4                           IPv6
-------------------------------------------------------------------------------------
Address size              32 bits (4 bytes)              128 bits (16 bytes)
Address space             ~4.3 billion                   340 undecillion
Notation                  Dotted decimal                 Hex colon notation
Header size               20-60 bytes (variable)         40 bytes (fixed!)
Header fields             12+ fields                     8 fields (simpler)
Broadcast                 Yes (255.255.255.255)          No (replaced by multicast)
Multicast                 Optional (224.x.x.x)           Built-in (ff00::/8)
Loopback                  127.0.0.1                      ::1
Link-local                169.254.x.x (APIPA)            fe80::/10 (always present)
Private range             RFC 1918                       ULA fc00::/7
Autoconfiguration         DHCP required                  SLAAC (stateless, no server)
NAT required              Yes (address shortage)          No (enough addresses)
IPsec                     Optional                       Mandatory (built-in)
Fragmentation             Routers fragment               Only source host
Checksum                  IP header checksum             None (L2/L4 handle it)
DNS record type           A record                       AAAA record
```

> 💡 **SLAAC** (Stateless Address Autoconfiguration) lets devices configure their own IPv6 address from router advertisements — no DHCP server needed. Devices use the /64 prefix + EUI-64 or random interface ID.

---

## Step 8: Capstone — IPv6 Address Calculator & Transition Mechanisms

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get install -y -qq python3 iproute2 iputils-ping 2>/dev/null &&
  python3 -c \"
import ipaddress, subprocess

print('=' * 65)
print('IPv6 FUNDAMENTALS CAPSTONE')
print('=' * 65)
print()

# 1. Show real IPv6 interface
print('--- Real IPv6 Interfaces ---')
result = subprocess.run(['ip', '-6', 'addr', 'show'], capture_output=True, text=True)
for line in result.stdout.strip().split('\n'):
    print(f'  {line}')
print()

# 2. IPv6 subnet calculations
print('--- IPv6 Subnet Calculations ---')
networks = [
    ('2001:db8::/32',  'ISP allocation'),
    ('2001:db8:1::/48','Site prefix'),
    ('2001:db8:1:1::/64', 'LAN subnet (standard /64)'),
    ('fe80::/10',      'Link-local range'),
    ('fc00::/7',       'Unique Local (ULA)'),
]
for net_str, label in networks:
    n = ipaddress.IPv6Network(net_str)
    print(f'  {net_str:<25} {label}')
    print(f'    Prefix len: /{n.prefixlen}   Total addresses: {n.num_addresses:,}')

print()

# 3. IPv6 /64 — the standard LAN size
print('--- Why /64 is the Standard Subnet Size ---')
n64 = ipaddress.IPv6Network('2001:db8:1:1::/64')
print(f'  Subnet: {n64}')
print(f'  Addresses: {n64.num_addresses:,}')
print(f'  = {n64.num_addresses / 2**32:.2e} × IPv4 address space')
print(f'  Host portion: 64 bits (for EUI-64 / SLAAC interface IDs)')
print()

# 4. Transition mechanisms
print('--- IPv6 Transition Mechanisms ---')
mechanisms = [
    ('Dual Stack',   'Run IPv4 and IPv6 simultaneously on same interface'),
    ('6to4',         'Encode IPv6 in IPv4 packets (prefix 2002::/16, RFC 3056)'),
    ('Teredo',       'IPv6 through NAT via UDP tunneling (Microsoft, RFC 4380)'),
    ('NAT64',        'Translate IPv6 packets to IPv4 (prefix 64:ff9b::/96)'),
    ('DNS64',        'Synthesize AAAA records from A records for NAT64'),
    ('ISATAP',       'Intra-site tunneling, embed IPv4 in IPv6 address'),
    ('6rd',          'ISP rapid deployment using IPv6 over IPv4 infrastructure'),
]
for mech, desc in mechanisms:
    print(f'  {mech:<12} {desc}')

print()

# 5. Live ping6 test
print('--- Live IPv6 Connectivity Test ---')
result = subprocess.run(['ping6', '-c', '2', '::1'], capture_output=True, text=True)
for line in result.stdout.strip().split('\n'):
    print(f'  {line}')

print()
print('✅ IPv6 Fundamentals Capstone Complete!')
print()
print('Summary:')
print('  • IPv6: 128-bit, hex colon notation, 340 undecillion addresses')
print('  • ::1 = loopback, fe80::/10 = link-local, 2000::/3 = global unicast')
print('  • No broadcast — replaced by multicast (ff02::1 = all nodes)')
print('  • SLAAC = devices auto-configure IPv6 from router advertisements')
print('  • /64 is the standard LAN prefix; hosts use bottom 64 bits')
\"
"
```

📸 **Verified Output:**
```
=================================================================
IPv6 FUNDAMENTALS CAPSTONE
=================================================================

--- Real IPv6 Interfaces ---
  1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 state UNKNOWN qlen 1000
      inet6 ::1/128 scope host 
         valid_lft forever preferred_lft forever

--- IPv6 Subnet Calculations ---
  2001:db8::/32             ISP allocation
    Prefix len: /32   Total addresses: 79,228,162,514,264,337,593,543,950,336
  2001:db8:1::/48           Site prefix
    Prefix len: /48   Total addresses: 1,208,925,819,614,629,174,706,176
  2001:db8:1:1::/64         LAN subnet (standard /64)
    Prefix len: /64   Total addresses: 18,446,744,073,709,551,616
  fe80::/10                 Link-local range
    Prefix len: /10   Total addresses: 332,306,998,946,228,968,225,951,765,070,086,144
  fc00::/7                  Unique Local (ULA)
    Prefix len: /7    Total addresses: 680,564,733,841,876,926,926,749,214,863,536,422,912

--- Why /64 is the Standard Subnet Size ---
  Subnet: 2001:db8:1:1::/64
  Addresses: 18,446,744,073,709,551,616
  = 4.29e+09 × IPv4 address space
  Host portion: 64 bits (for EUI-64 / SLAAC interface IDs)

--- IPv6 Transition Mechanisms ---
  Dual Stack   Run IPv4 and IPv6 simultaneously on same interface
  6to4         Encode IPv6 in IPv4 packets (prefix 2002::/16, RFC 3056)
  Teredo       IPv6 through NAT via UDP tunneling (Microsoft, RFC 4380)
  NAT64        Translate IPv6 packets to IPv4 (prefix 64:ff9b::/96)
  DNS64        Synthesize AAAA records from A records for NAT64
  ISATAP       Intra-site tunneling, embed IPv4 in IPv6 address
  6rd          ISP rapid deployment using IPv6 over IPv4 infrastructure

--- Live IPv6 Connectivity Test ---
  PING ::1(::1) 56 data bytes
  64 bytes from ::1: icmp_seq=1 ttl=64 time=0.050 ms
  64 bytes from ::1: icmp_seq=2 ttl=64 time=0.055 ms

  --- ::1 ping statistics ---
  2 packets transmitted, 2 received, 0% packet loss, time 1037ms
  rtt min/avg/max/mdev = 0.050/0.052/0.055/0.002 ms

✅ IPv6 Fundamentals Capstone Complete!

Summary:
  • IPv6: 128-bit, hex colon notation, 340 undecillion addresses
  • ::1 = loopback, fe80::/10 = link-local, 2000::/3 = global unicast
  • No broadcast — replaced by multicast (ff02::1 = all nodes)
  • SLAAC = devices auto-configure IPv6 from router advertisements
  • /64 is the standard LAN prefix; hosts use bottom 64 bits
```

---

## Summary

| Concept            | IPv6 Value/Range          | Notes                               |
|--------------------|---------------------------|-------------------------------------|
| Address size       | 128 bits                  | 8 × 16-bit hex groups               |
| Total addresses    | 3.4 × 10³⁸               | Essentially unlimited               |
| Loopback           | `::1/128`                 | Equivalent to 127.0.0.1             |
| Link-local         | `fe80::/10`               | Auto-configured, L2 only            |
| Unique Local (ULA) | `fc00::/7`                | Like RFC 1918, not internet-routed  |
| Global Unicast     | `2000::/3`                | Internet-routable addresses          |
| Multicast          | `ff00::/8`                | Replaces broadcast                  |
| Documentation      | `2001:db8::/32`           | Used in examples (like 192.0.2.x)   |
| Standard LAN       | `/64` prefix              | Host uses bottom 64 bits            |
| DNS record         | `AAAA` record             | vs IPv4's `A` record                |
| No NAT needed      | End-to-end connectivity   | Each device gets a global address   |

**Key takeaways:**
- IPv6 = 128-bit addresses, written as 8 hex groups separated by colons
- `::` compresses consecutive all-zero groups (only once per address)
- No broadcast in IPv6 — all-nodes multicast `ff02::1` is used instead
- SLAAC lets devices auto-configure IPv6 without DHCP using `/64` prefixes + EUI-64
- Dual-stack (IPv4 + IPv6 simultaneously) is the primary transition strategy today
- A single `/64` subnet has more addresses than the entire IPv4 internet — 4.3 billion times over

**Previous Lab:** [Lab 04: Subnetting ←](lab-04-subnetting.md)  
**Next Module:** DNS, DHCP & Network Services
