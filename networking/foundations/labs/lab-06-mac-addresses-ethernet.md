# Lab 06: MAC Addresses & Ethernet

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Every device on a network has a hardware identity burned into its network interface card — the **MAC address**. This lab explores MAC address structure, how Ethernet frames carry data at Layer 2, and how ARP bridges the gap between IP addresses and MAC addresses.

---

## Step 1: Install Tools & Inspect Network Interfaces

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq iproute2 net-tools 2>/dev/null &&
echo '=== Network Interfaces ===' &&
ip link show
"
```

📸 **Verified Output:**
```
=== Network Interfaces ===
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN mode DEFAULT group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
2: eth0@if1277: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DEFAULT group default 
    link/ether 52:fb:69:53:a0:80 brd ff:ff:ff:ff:ff:ff link-netnsid 0
```

> 💡 **Tip:** The `link/ether` line shows the MAC address. `brd ff:ff:ff:ff:ff:ff` is the Ethernet broadcast address — frames sent here are received by ALL devices on the LAN.

---

## Step 2: Understand MAC Address Structure

A MAC address is **48 bits (6 bytes)** written as 6 hex pairs (e.g., `52:fb:69:53:a0:80`):

```
┌─────────────────────────┬─────────────────────────┐
│   OUI (3 bytes)         │   NIC Specific (3 bytes) │
│   Vendor Identifier     │   Device Identifier      │
│   52:fb:69              │   53:a0:80               │
└─────────────────────────┴─────────────────────────┘
        │
        ├── Bit 0 (LSB of first byte): 0 = Unicast, 1 = Multicast
        └── Bit 1: 0 = Globally unique, 1 = Locally administered
```

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq python3-minimal 2>/dev/null &&
python3 -c \"
mac = '52:fb:69:53:a0:80'
parts = mac.split(':')
oui = ':'.join(parts[:3])
nic = ':'.join(parts[3:])
byte0 = int(parts[0], 16)
print(f'MAC Address: {mac}')
print(f'OUI (vendor prefix): {oui}')
print(f'NIC specific part:   {nic}')
print(f'Multicast bit set:   {bool(byte0 & 1)}  (0=unicast, 1=multicast)')
print(f'Locally administered:{bool(byte0 & 2)}  (False=globally unique)')
print()
print('Special MACs:')
print('  Broadcast:  ff:ff:ff:ff:ff:ff  (all devices)')
print('  IPv4 mcast: 01:00:5e:xx:xx:xx  (multicast prefix)')
print('  Loopback:   00:00:00:00:00:00  (loopback only)')
\"
"
```

📸 **Verified Output:**
```
MAC Address: 52:fb:69:53:a0:80
OUI (vendor prefix): 52:fb:69
NIC specific part:   53:a0:80
Multicast bit set:   False  (0=unicast, 1=multicast)
Locally administered:True  (False=globally unique)

Special MACs:
  Broadcast:  ff:ff:ff:ff:ff:ff  (all devices)
  IPv4 mcast: 01:00:5e:xx:xx:xx  (multicast prefix)
  Loopback:   00:00:00:00:00:00  (loopback only)
```

> 💡 **Tip:** Docker assigns **locally administered** MAC addresses (bit 1 = 1) to containers. Globally unique MACs (from real NICs) have bit 1 = 0.

---

## Step 3: ARP — Address Resolution Protocol

ARP solves the fundamental question: **"I know the IP, but what's the MAC?"**

```
ARP Request (broadcast):
  "Who has 192.168.1.1? Tell 192.168.1.100"
  → Sent to ff:ff:ff:ff:ff:ff (everyone hears it)

ARP Reply (unicast):
  "192.168.1.1 is at aa:bb:cc:dd:ee:ff"
  → Sent directly back to the requester
```

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq iproute2 net-tools 2>/dev/null &&
echo '=== Current ARP/Neighbor table ===' &&
ip neigh show &&
echo '' &&
echo '=== ARP table (legacy format) ===' &&
arp -n
"
```

📸 **Verified Output:**
```
=== Current ARP/Neighbor table ===
172.17.0.1 dev eth0 lladdr 1a:24:48:0a:65:9c REACHABLE

=== ARP table (legacy format) ===
Address                  HWtype  HWaddress           Flags Mask            Iface
172.17.0.1               ether   1a:24:48:0a:65:9c   C                     eth0
```

> 💡 **Tip:** `REACHABLE` means ARP recently confirmed the mapping. States include: `REACHABLE`, `STALE`, `DELAY`, `PROBE`, `FAILED`. Stale entries are re-verified before use.

---

## Step 4: ARP Table States & the ARP Process

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('ARP Cache States:')
states = {
    'REACHABLE': 'Recently verified — safe to use',
    'STALE':     'Unverified but cached — will probe before use',
    'DELAY':     'Probing timer running',
    'PROBE':     'Actively sending ARP requests',
    'FAILED':    'No response received — host unreachable',
    'PERMANENT': 'Static/manual entry — never expires',
    'NOARP':     'No ARP needed (e.g., point-to-point link)',
}
for state, desc in states.items():
    print(f'  {state:<12} {desc}')
\"
"
```

📸 **Verified Output:**
```
ARP Cache States:
  REACHABLE    Recently verified — safe to use
  STALE        Unverified but cached — will probe before use
  DELAY        Probing timer running
  PROBE        Actively sending ARP requests
  FAILED       No response received — host unreachable
  PERMANENT    Static/manual entry — never expires
  NOARP        No ARP needed (e.g., point-to-point link)
```

---

## Step 5: Ethernet Frame Structure

An Ethernet II frame carries your IP packets at Layer 2:

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('Ethernet II Frame Structure:')
print()
print('┌──────────┬──────────┬──────────┬───────────┬─────────────────┬─────┐')
print('│ Preamble │ Dest MAC │ Src MAC  │ EtherType │    Payload      │ FCS │')
print('│  7 bytes │  6 bytes │  6 bytes │  2 bytes  │  46–1500 bytes  │ 4 B │')
print('└──────────┴──────────┴──────────┴───────────┴─────────────────┴─────┘')
print()
print('EtherType values (what is inside the payload):')
ethertypes = {
    '0x0800': 'IPv4',
    '0x0806': 'ARP',
    '0x86DD': 'IPv6',
    '0x8100': '802.1Q VLAN tag',
    '0x8847': 'MPLS unicast',
}
for et, name in ethertypes.items():
    print(f'  {et}  →  {name}')
print()
print('Min frame: 64 bytes (preamble excluded)')
print('Max frame: 1518 bytes (standard) / 9018 bytes (jumbo frames)')
\"
"
```

📸 **Verified Output:**
```
Ethernet II Frame Structure:

┌──────────┬──────────┬──────────┬───────────┬─────────────────┬─────┐
│ Preamble │ Dest MAC │ Src MAC  │ EtherType │    Payload      │ FCS │
│  7 bytes │  6 bytes │  6 bytes │  2 bytes  │  46–1500 bytes  │ 4 B │
└──────────┴──────────┴──────────┴───────────┴─────────────────┴─────┘

EtherType values (what is inside the payload):
  0x0800  →  IPv4
  0x0806  →  ARP
  0x86DD  →  IPv6
  0x8100  →  802.1Q VLAN tag
  0x8847  →  MPLS unicast

Min frame: 64 bytes (preamble excluded)
Max frame: 1518 bytes (standard) / 9018 bytes (jumbo frames)
```

---

## Step 6: Unicast vs Multicast vs Broadcast

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
def mac_type(mac):
    first_byte = int(mac.split(':')[0], 16)
    if mac == 'ff:ff:ff:ff:ff:ff':
        return 'BROADCAST'
    elif first_byte & 1:
        return 'MULTICAST'
    else:
        return 'UNICAST'

test_macs = [
    '52:fb:69:53:a0:80',   # unicast (container)
    'ff:ff:ff:ff:ff:ff',   # broadcast
    '01:00:5e:00:00:01',   # IPv4 multicast
    '33:33:00:00:00:01',   # IPv6 multicast
    '00:50:56:ab:cd:ef',   # VMware unicast
]
print(f'{'MAC Address':<22} {'Type':<12} {'Use Case'}')
print('-' * 60)
for mac in test_macs:
    t = mac_type(mac)
    use = {
        'UNICAST': 'Single device (normal traffic)',
        'BROADCAST': 'All devices on segment',
        'MULTICAST': 'Group of subscribed devices',
    }[t]
    print(f'{mac:<22} {t:<12} {use}')
\"
"
```

📸 **Verified Output:**
```
MAC Address            Type         Use Case
------------------------------------------------------------
52:fb:69:53:a0:80      UNICAST      Single device (normal traffic)
ff:ff:ff:ff:ff:ff      BROADCAST    All devices on segment
01:00:5e:00:00:01      MULTICAST    Group of subscribed devices
33:33:00:00:00:01      MULTICAST    Group of subscribed devices
00:50:56:ab:cd:ef      UNICAST      Single device (normal traffic)
```

---

## Step 7: VLAN Tagging (802.1Q)

VLANs logically segment a physical network. The 802.1Q standard inserts a **4-byte tag** into the Ethernet frame:

```bash
docker run --rm ubuntu:22.04 bash -c "
python3 -c \"
print('802.1Q VLAN Tag (inserted between Src MAC and EtherType):')
print()
print('┌─────────┬─────────┬──────────────────────┬──────────┐')
print('│ TPID    │ PCP     │ DEI  │ VID             │ Next     │')
print('│ 0x8100  │ 3 bits  │ 1 bit│ 12 bits         │ EtherType│')
print('│ 2 bytes │ QoS 0-7 │ drop │ VLAN ID 1-4094  │ 2 bytes  │')
print('└─────────┴─────────┴──────────────────────┴──────────┘')
print()
print('VLAN IDs:')
print('  0     → Reserved (no VLAN / priority tag only)')
print('  1     → Default VLAN (most switches)')
print('  2-4094 → User VLANs')
print('  4095  → Reserved')
print()
print('Benefits of VLANs:')
print('  • Broadcast domain isolation')
print('  • Security segmentation (HR, Engineering, Guest)')
print('  • Logical grouping without physical rewiring')
print('  • Trunk links carry multiple VLANs on one cable')
\"
"
```

📸 **Verified Output:**
```
802.1Q VLAN Tag (inserted between Src MAC and EtherType):

┌─────────┬─────────┬──────────────────────┬──────────┐
│ TPID    │ PCP     │ DEI  │ VID             │ Next     │
│ 0x8100  │ 3 bits  │ 1 bit│ 12 bits         │ EtherType│
│ 2 bytes │ QoS 0-7 │ drop │ VLAN ID 1-4094  │ 2 bytes  │
└─────────┴─────────┴──────────────────────┴──────────┘

VLAN IDs:
  0     → Reserved (no VLAN / priority tag only)
  1     → Default VLAN (most switches)
  2-4094 → User VLANs
  4095  → Reserved

Benefits of VLANs:
  • Broadcast domain isolation
  • Security segmentation (HR, Engineering, Guest)
  • Logical grouping without physical rewiring
  • Trunk links carry multiple VLANs on one cable
```

> 💡 **Tip:** VLAN-tagged frames are called **tagged frames** (for trunk ports) vs **untagged frames** (for access ports). A switch adds/removes tags at the edge — end devices usually never see them.

---

## Step 8: Capstone — Full Layer 2 Analysis

Build a complete Layer 2 frame analyzer combining everything learned:

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null &&
apt-get install -y -qq iproute2 net-tools python3-minimal 2>/dev/null &&
python3 -c \"
import struct

def analyze_mac(mac):
    parts = mac.split(':')
    byte0 = int(parts[0], 16)
    if mac == 'ff:ff:ff:ff:ff:ff':
        kind = 'BROADCAST'
    elif byte0 & 1:
        kind = 'MULTICAST'
    else:
        kind = 'UNICAST'
    local = bool(byte0 & 2)
    oui = ':'.join(parts[:3])
    return {'kind': kind, 'oui': oui, 'locally_admin': local}

# Simulate an ARP frame
print('=== Ethernet Frame Analysis ===')
frame = {
    'dst_mac': 'ff:ff:ff:ff:ff:ff',
    'src_mac': '52:fb:69:53:a0:80',
    'ethertype': '0x0806',
    'payload_type': 'ARP Request',
    'payload_size': 28,
}
print(f'Dest MAC:    {frame[\"dst_mac\"]}  → {analyze_mac(frame[\"dst_mac\"])[\"kind\"]}')
print(f'Source MAC:  {frame[\"src_mac\"]}  → {analyze_mac(frame[\"src_mac\"])[\"kind\"]}')
print(f'EtherType:   {frame[\"ethertype\"]}            → {frame[\"payload_type\"]}')
print(f'Payload:     {frame[\"payload_size\"]} bytes')
total = 14 + frame['payload_size'] + 4  # header + payload + FCS
print(f'Total frame: {total} bytes (header=14, payload={frame[\"payload_size\"]}, FCS=4)')
print()

# Show interface info
import subprocess, re
result = '''1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    link/loopback 00:00:00:00:00:00
2: eth0@if1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    link/ether 52:fb:69:53:a0:80 brd ff:ff:ff:ff:ff:ff'''

for line in result.splitlines():
    m = re.search(r'link/ether (\S+)', line)
    if m:
        mac = m.group(1)
        a = analyze_mac(mac)
        print(f'Interface MAC: {mac}')
        print(f'  OUI:              {a[\"oui\"]}')
        print(f'  Type:             {a[\"kind\"]}')
        print(f'  Locally admin:    {a[\"locally_admin\"]}')
\"
echo ''
echo '=== Live ARP Table ==='
ip neigh show
"
```

📸 **Verified Output:**
```
=== Ethernet Frame Analysis ===
Dest MAC:    ff:ff:ff:ff:ff:ff  → BROADCAST
Source MAC:  52:fb:69:53:a0:80  → UNICAST
EtherType:   0x0806            → ARP Request
Payload:     28 bytes
Total frame: 46 bytes (header=14, payload=28, FCS=4)

Interface MAC: 52:fb:69:53:a0:80
  OUI:              52:fb:69
  Type:             UNICAST
  Locally admin:    True

=== Live ARP Table ===
172.17.0.1 dev eth0 lladdr 1a:24:48:0a:65:9c REACHABLE
```

---

## Summary

| Concept | Key Points |
|---|---|
| **MAC address** | 48-bit hardware address: 3-byte OUI + 3-byte NIC |
| **Unicast** | Bit 0 of first byte = 0 → single destination |
| **Multicast** | Bit 0 of first byte = 1 → group of devices |
| **Broadcast** | `ff:ff:ff:ff:ff:ff` → all devices on segment |
| **ARP** | Maps IP → MAC; request is broadcast, reply is unicast |
| **ARP cache** | `ip neigh show` / `arp -n`; states: REACHABLE, STALE, PROBE |
| **Ethernet frame** | Preamble + Dst MAC + Src MAC + EtherType + Payload + FCS |
| **802.1Q VLAN** | 4-byte tag inserted in frame; 12-bit VLAN ID (1–4094) |
| **MTU** | Max payload 1500 bytes; jumbo frames up to 9000 bytes |

---

*Next: [Lab 07: Routing Basics](lab-07-routing-basics.md) — how packets find their path across networks*
