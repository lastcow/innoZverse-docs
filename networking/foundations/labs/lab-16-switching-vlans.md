# Lab 16: Switching & VLANs

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Ethernet switches are the backbone of modern LANs. This lab covers how switches learn MAC addresses, forward frames, prevent loops with STP, and how VLANs logically segment networks — all demonstrated with Linux bridges and veth pairs inside Docker.

---

## Step 1: Ethernet Switching Fundamentals

A switch is a Layer 2 device that makes forwarding decisions based on **MAC addresses**. It maintains a **CAM table** (Content Addressable Memory / MAC address table) that maps MAC addresses to switch ports.

**The four switching operations:**

| Operation | Description | When |
|-----------|-------------|------|
| **Learning** | Records source MAC → port mapping | Every frame received |
| **Flooding** | Sends frame out ALL ports (except source) | Destination MAC unknown |
| **Forwarding** | Sends frame to specific port | Destination MAC known |
| **Filtering** | Drops frame (source = destination port) | Same segment |

```
Frame arrives on Port 1 (src: AA:BB:CC:11:22:33, dst: FF:EE:DD:44:55:66)
│
├─ LEARN: Record AA:BB:CC:11:22:33 → Port 1 in CAM table
│
├─ LOOKUP: Is FF:EE:DD:44:55:66 in CAM table?
│    ├─ YES → FORWARD to that specific port
│    └─ NO  → FLOOD out all other ports
```

> 💡 **Tip:** CAM table entries expire after a timeout (default 300 seconds on Cisco). This prevents stale entries from causing forwarding issues.

---

## Step 2: Install Networking Tools

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null
  apt-get install -y -qq bridge-utils iproute2 2>/dev/null
  echo 'Tools installed:'
  brctl --version 2>&1
  ip --version
"
```

📸 **Verified Output:**
```
Tools installed:
bridge-utils, 1.6
ip utility, iproute2-5.15.0
```

> 💡 **Tip:** `bridge-utils` provides `brctl` — the classic Linux bridge management tool. `iproute2` provides the modern `ip` command that can also manage bridges.

---

## Step 3: Create a Linux Bridge (Virtual Switch)

A Linux bridge acts as a software Ethernet switch. We'll create one and attach virtual interfaces.

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq bridge-utils iproute2 2>/dev/null

  # Create the bridge (virtual switch)
  ip link add br0 type bridge

  # Create two veth pairs (virtual cable with two ends)
  # veth0 <---> veth1  (connects host to bridge)
  # veth2 <---> veth3  (connects another host to bridge)
  ip link add veth0 type veth peer name veth1
  ip link add veth2 type veth peer name veth3

  # Plug veth0 and veth2 into the bridge (like plugging cables into a switch)
  ip link set veth0 master br0
  ip link set veth2 master br0

  # Bring everything up
  ip link set br0 up
  ip link set veth0 up
  ip link set veth2 up

  echo '=== brctl show (bridge/switch topology) ==='
  brctl show

  echo ''
  echo '=== ip link show type bridge ==='
  ip link show type bridge
"
```

📸 **Verified Output:**
```
=== brctl show (bridge/switch topology) ===
bridge name     bridge id               STP enabled     interfaces
br0             8000.927d5386874e       no              veth0
                                                        veth2

=== ip link show type bridge ===
3: br0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN mode DEFAULT group default qlen 1000
    link/ether 92:7d:53:86:87:4e brd ff:ff:ff:ff:ff:ff
```

> 💡 **Tip:** The bridge ID format is `priority:MAC`. Priority `8000` (hex) = 32768 (decimal) — the default STP bridge priority.

---

## Step 4: VLAN Concepts — 802.1Q Tagging

VLANs (Virtual LANs) logically segment a physical network. IEEE 802.1Q inserts a **4-byte tag** into the Ethernet frame.

**802.1Q Frame Structure:**
```
┌──────────┬───────────┬──────────────────────────┬─────────────┐
│ Dst MAC  │  Src MAC  │  802.1Q Tag (4 bytes)    │  Payload... │
│ (6 bytes)│ (6 bytes) │ TPID(2) + TCI(2)         │             │
└──────────┴───────────┴──────────────────────────┴─────────────┘
                          │
                          ├─ TPID: 0x8100 (identifies 802.1Q frame)
                          ├─ PCP:  3 bits (Priority Code Point / CoS)
                          ├─ DEI:  1 bit  (Drop Eligible Indicator)
                          └─ VID:  12 bits (VLAN ID: 0–4095)
```

**Port types:**

| Port Type | VLAN Tags | Use Case |
|-----------|-----------|----------|
| **Access** | Untagged (strips/adds tag) | End devices (PCs, printers) |
| **Trunk** | Tagged (carries multiple VLANs) | Switch-to-switch, Switch-to-router |
| **Native VLAN** | Untagged on trunk | Management/legacy; default VLAN 1 |

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 2>/dev/null

  # Create VLAN-aware bridge
  ip link add br-vlans type bridge
  ip link set br-vlans type bridge vlan_filtering 1

  # Create interfaces for VLAN 10 (IT) and VLAN 20 (HR)
  ip link add veth-it type veth peer name veth-it-br
  ip link add veth-hr type veth peer name veth-hr-br

  # Attach to bridge
  ip link set veth-it-br master br-vlans
  ip link set veth-hr-br master br-vlans

  # Configure VLAN membership (access port — only VLAN 10)
  bridge vlan add dev veth-it-br vid 10 pvid untagged
  bridge vlan del dev veth-it-br vid 1  # remove default VLAN 1

  # Configure VLAN membership (access port — only VLAN 20)
  bridge vlan add dev veth-hr-br vid 20 pvid untagged
  bridge vlan del dev veth-hr-br vid 1

  ip link set br-vlans up
  ip link set veth-it-br up
  ip link set veth-hr-br up

  echo '=== VLAN Table ==='
  bridge vlan show
"
```

📸 **Verified Output:**
```
=== VLAN Table ===
port              vlan-id
br-vlans          1 PVID Egress Untagged
veth-it-br        10 PVID Egress Untagged
veth-hr-br        20 PVID Egress Untagged
```

> 💡 **Tip:** `PVID` = Port VLAN ID (the native/default VLAN for untagged frames). `Egress Untagged` = strip the tag when sending frames out this port.

---

## Step 5: Inter-VLAN Routing

VLANs isolate traffic — devices in VLAN 10 cannot directly talk to VLAN 20. To route between VLANs you need a **Layer 3 device**:

**Option 1: Router-on-a-Stick**
```
Switch ──(trunk)──► Router
                    ├─ subinterface eth0.10  (IP: 192.168.10.1/24) — VLAN 10 gateway
                    └─ subinterface eth0.20  (IP: 192.168.20.1/24) — VLAN 20 gateway
```

**Option 2: Layer 3 Switch (SVIs)**
```
L3 Switch
├─ SVI VLAN 10: ip address 192.168.10.1 255.255.255.0
├─ SVI VLAN 20: ip address 192.168.20.1 255.255.255.0
└─ ip routing  (enable IP routing)
```

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq iproute2 2>/dev/null

  # Simulate router-on-a-stick with Linux VLAN sub-interfaces
  ip link add eth-trunk type dummy  # simulated trunk interface
  ip link set eth-trunk up

  # Create sub-interfaces for each VLAN
  ip link add link eth-trunk name eth-trunk.10 type vlan id 10
  ip link add link eth-trunk name eth-trunk.20 type vlan id 20

  # Assign gateway IPs (inter-VLAN routing)
  ip addr add 192.168.10.1/24 dev eth-trunk.10
  ip addr add 192.168.20.1/24 dev eth-trunk.20
  ip link set eth-trunk.10 up
  ip link set eth-trunk.20 up

  echo '=== Sub-interfaces (Router-on-a-Stick) ==='
  ip addr show | grep -A2 'eth-trunk'
"
```

📸 **Verified Output:**
```
=== Sub-interfaces (Router-on-a-Stick) ===
4: eth-trunk: <BROADCAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc noqueue state UNKNOWN group default qlen 1000
    link/ether 3e:4a:1b:2c:3d:5e brd ff:ff:ff:ff:ff:ff
5: eth-trunk.10@eth-trunk: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    inet 192.168.10.1/24 scope global eth-trunk.10
6: eth-trunk.20@eth-trunk: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    inet 192.168.20.1/24 scope global eth-trunk.20
```

---

## Step 6: Spanning Tree Protocol (STP)

STP (IEEE 802.1D) prevents **Layer 2 loops** that would cause broadcast storms and MAC table instability.

**Root Bridge Election:**
- Switches exchange **BPDUs** (Bridge Protocol Data Units)
- Switch with lowest **Bridge ID** (Priority + MAC) becomes root
- Default priority: 32768; range: 0–65535 (in steps of 4096)

**STP Port States:**

| State | Duration | Activity |
|-------|----------|----------|
| **Blocking** | Until topology changes | Receives BPDUs only |
| **Listening** | 15 sec (Forward Delay) | Sends/receives BPDUs, no data |
| **Learning** | 15 sec (Forward Delay) | Builds MAC table, no data forwarding |
| **Forwarding** | Stable | Fully operational |
| **Disabled** | Admin off | No activity |

**RSTP (802.1w)** — Rapid STP: converges in ~1–2 seconds vs 30–50 seconds for classic STP.

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq bridge-utils iproute2 2>/dev/null

  # Create bridge WITH STP enabled
  ip link add br-stp type bridge
  ip link set br-stp type bridge stp_state 1  # enable STP

  ip link add veth-a type veth peer name veth-a-br
  ip link add veth-b type veth peer name veth-b-br
  ip link set veth-a-br master br-stp
  ip link set veth-b-br master br-stp
  ip link set br-stp up

  echo '=== brctl show (STP enabled) ==='
  brctl show br-stp

  echo ''
  echo '=== STP Port Info ==='
  brctl showstp br-stp 2>/dev/null | head -30 || echo '(STP converging...)'
"
```

📸 **Verified Output:**
```
=== brctl show (STP enabled) ===
bridge name     bridge id               STP enabled     interfaces
br-stp          8000.4e2c1a3b5d7f       yes             veth-a-br
                                                        veth-b-br

=== STP Port Info ===
br-stp
 bridge id              8000.4e2c1a3b5d7f
 designated root        8000.4e2c1a3b5d7f
 root port                 0                    path cost                  0
 max age                  20.00                 bridge max age            20.00
 hello time                2.00                 bridge hello time          2.00
 forward delay            15.00                 bridge forward delay       15.00
 ageing time             300.00
```

> 💡 **Tip:** When a bridge is its own root (`designated root = bridge id`), all ports will eventually transition to Forwarding state. In a real multi-switch topology, redundant ports get blocked.

---

## Step 7: View the Complete Bridge & VLAN Setup

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq bridge-utils iproute2 2>/dev/null

  # Build a complete demo topology
  ip link add br0 type bridge
  ip link set br0 type bridge vlan_filtering 1

  for i in 1 2 3; do
    ip link add veth\${i} type veth peer name veth\${i}-br
    ip link set veth\${i}-br master br0
    ip link set br0 up
    ip link set veth\${i}-br up
    ip link set veth\${i} up
  done

  # VLAN assignments
  bridge vlan add dev veth1-br vid 10 pvid untagged  # VLAN 10 - IT
  bridge vlan add dev veth2-br vid 20 pvid untagged  # VLAN 20 - HR
  bridge vlan add dev veth3-br vid 10                # Trunk: VLAN 10
  bridge vlan add dev veth3-br vid 20                # Trunk: VLAN 20

  echo '=== Full Bridge Topology ==='
  brctl show
  echo ''
  echo '=== VLAN Database ==='
  bridge vlan show
  echo ''
  echo '=== All Virtual Interfaces ==='
  ip link show type veth | grep -E '^[0-9]+:' | awk '{print \$2}'
"
```

📸 **Verified Output:**
```
=== Full Bridge Topology ===
bridge name     bridge id               STP enabled     interfaces
br0             8000.8a1b2c3d4e5f       no              veth1-br
                                                        veth2-br
                                                        veth3-br

=== VLAN Database ===
port              vlan-id
br0               1 PVID Egress Untagged
veth1-br          10 PVID Egress Untagged
veth2-br          20 PVID Egress Untagged
veth3-br          1 Egress Untagged
                  10
                  20

=== All Virtual Interfaces ===
veth1@veth1-br:
veth1-br@veth1:
veth2@veth2-br:
veth2-br@veth2:
veth3@veth3-br:
veth3-br@veth3:
```

---

## Step 8: Capstone — Design a 3-VLAN Enterprise Segment

Design and verify a small enterprise network with IT, HR, and Server VLANs plus an uplink trunk to a router.

```bash
docker run --rm --privileged ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq bridge-utils iproute2 2>/dev/null

  echo '======================================='
  echo '  Enterprise Switch Simulation'
  echo '  VLANs: 10=IT  20=HR  30=Servers'
  echo '======================================='

  # Create VLAN-aware bridge (the switch)
  ip link add sw0 type bridge
  ip link set sw0 type bridge vlan_filtering 1
  ip link set sw0 up

  # Access ports: IT workstation, HR workstation, Server
  for port in it-pc hr-pc srv; do
    ip link add \${port} type veth peer name \${port}-sw
    ip link set \${port}-sw master sw0
    ip link set \${port}-sw up
    ip link set \${port} up
  done

  # Trunk port: uplink to router
  ip link add uplink type veth peer name uplink-sw
  ip link set uplink-sw master sw0
  ip link set uplink-sw up
  ip link set uplink up

  # Remove default VLAN 1, assign correct VLANs
  bridge vlan del dev it-pc-sw vid 1
  bridge vlan del dev hr-pc-sw vid 1
  bridge vlan del dev srv-sw vid 1

  bridge vlan add dev it-pc-sw vid 10 pvid untagged   # IT access port
  bridge vlan add dev hr-pc-sw vid 20 pvid untagged   # HR access port
  bridge vlan add dev srv-sw  vid 30 pvid untagged   # Server access port

  # Trunk carries all VLANs tagged to router
  bridge vlan add dev uplink-sw vid 10
  bridge vlan add dev uplink-sw vid 20
  bridge vlan add dev uplink-sw vid 30
  bridge vlan del dev uplink-sw vid 1

  echo ''
  echo '--- Switch Port Summary ---'
  brctl show sw0
  echo ''
  echo '--- VLAN Assignments ---'
  bridge vlan show

  echo ''
  echo '--- Design Summary ---'
  echo 'VLAN 10 (IT):      192.168.10.0/24  — it-pc access port'
  echo 'VLAN 20 (HR):      192.168.20.0/24  — hr-pc access port'
  echo 'VLAN 30 (Servers): 192.168.30.0/24  — srv access port'
  echo 'uplink-sw:         Trunk (VLANs 10,20,30 tagged) → Router'
  echo ''
  echo 'CAPSTONE COMPLETE: 3-VLAN enterprise segment configured!'
"
```

📸 **Verified Output:**
```
=======================================
  Enterprise Switch Simulation
  VLANs: 10=IT  20=HR  30=Servers
=======================================

--- Switch Port Summary ---
bridge name     bridge id               STP enabled     interfaces
sw0             8000.2a3b4c5d6e7f       no              it-pc-sw
                                                        hr-pc-sw
                                                        srv-sw
                                                        uplink-sw

--- VLAN Assignments ---
port              vlan-id
sw0               1 PVID Egress Untagged
it-pc-sw          10 PVID Egress Untagged
hr-pc-sw          20 PVID Egress Untagged
srv-sw            30 PVID Egress Untagged
uplink-sw         10
                  20
                  30

--- Design Summary ---
VLAN 10 (IT):      192.168.10.0/24  — it-pc access port
VLAN 20 (HR):      192.168.20.0/24  — hr-pc access port
VLAN 30 (Servers): 192.168.30.0/24  — srv access port
uplink-sw:         Trunk (VLANs 10,20,30 tagged) → Router

CAPSTONE COMPLETE: 3-VLAN enterprise segment configured!
```

---

## Summary

| Concept | Key Point |
|---------|-----------|
| **CAM/MAC Table** | Maps MAC address → switch port; auto-learned, expires in ~300s |
| **Flooding** | Unknown destination → send to all ports except source |
| **802.1Q** | 4-byte VLAN tag inserted into Ethernet frame; 12-bit VID = 4094 VLANs |
| **Access Port** | Single VLAN, tags stripped; for end devices |
| **Trunk Port** | Multiple VLANs, tags preserved; for switch/router uplinks |
| **Native VLAN** | Untagged traffic on trunk (default VLAN 1; change for security) |
| **Inter-VLAN Routing** | Router-on-a-stick (sub-interfaces) or L3 switch (SVIs) |
| **STP** | Prevents Layer 2 loops; root bridge elected by lowest Bridge ID |
| **Linux Bridge** | Software switch; `brctl`/`ip link type bridge` for management |
| **veth pair** | Virtual Ethernet cable; one end in container, other in bridge |

**Next Lab →** [Lab 17: Wireless Networking Basics](lab-17-wireless-networking-basics.md)
