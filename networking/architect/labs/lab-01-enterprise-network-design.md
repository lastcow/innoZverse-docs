# Lab 01: Enterprise Network Design

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

Enterprise networks must balance scalability, redundancy, performance, and cost. This lab covers the three major design models used in production networks today, and teaches you how to calculate capacity, plan redundancy, and document your architecture.

---

## Objectives
- Compare three-tier, two-tier (collapsed core), and spine-leaf topologies
- Apply capacity planning and bandwidth calculation methodologies
- Design ECMP redundancy paths
- Define QoS policy tiers
- Generate topology documentation programmatically

---

## Step 1: Three-Tier vs Two-Tier vs Spine-Leaf

The fundamental choice in network design:

**Three-Tier (Traditional Enterprise)**
```
         [Core Layer]          <- 100G, routing, inter-distribution
              ↕ ↕
     [Distribution Layer]      <- 40G, policy, aggregation, L3 boundary
              ↕ ↕
       [Access Layer]          <- 1G/10G, end devices, VLANs
```

**Two-Tier / Collapsed Core**
```
    [Core+Distribution]        <- 40G, collapsed into one tier
           ↕ ↕
      [Access Layer]           <- 1G/10G, end devices
```
Best for: campuses < 2,000 users; reduces latency and cost.

**Spine-Leaf (Data Center)**
```
  [Spine-1][Spine-2][Spine-3][Spine-4]   <- 100G/400G
     ||||     ||||     ||||     ||||
  [Leaf-1] [Leaf-2] [Leaf-3] [Leaf-4]   <- 10G/25G to servers
```
Every leaf connects to every spine → any two servers are always 2 hops apart.

> 💡 **Rule of thumb:** Use spine-leaf for data centers with significant east-west traffic (containerized apps, microservices). Use three-tier for traditional campus environments with mostly north-south traffic.

---

## Step 2: Capacity Planning

Bandwidth planning prevents congestion-related performance problems.

**Variables:**
- Users per access switch: 48
- Average bandwidth per user: 10 Mbps (office), 50 Mbps (engineering), 100 Mbps (media)
- Oversubscription ratio (access→distribution): 20:1 typical, 4:1 for storage
- Oversubscription ratio (distribution→core): 4:1

**Formula:**
```
Required uplink = (users × avg_bps) / oversubscription_ratio
```

**Traffic growth:** Plan for 30-40% annual growth; size for 3-year lifecycle.

**Switch capacity checklist:**
- Line-rate forwarding (no oversubscription at backplane)
- MAC table size ≥ 16K entries
- ARP table size ≥ 8K entries
- Routing table (for L3 switches): ≥ 32K routes

---

## Step 3: ECMP Redundancy Design

Equal-Cost Multi-Path (ECMP) enables load balancing across multiple paths without Spanning Tree Protocol (STP) convergence issues.

```
Core-SW1 ──────── Core-SW2
   │   ╲         ╱   │
   │    ╲       ╱    │
 Dist-1   ╲   ╱   Dist-2
   │        ╳        │
   │      ╱   ╲      │
 Acc-1  ╱       ╲  Acc-2
```

**ECMP with OSPF:**
```
router ospf 1
 maximum-paths 4           ! Enable 4 ECMP paths
 ecmp-based-load-balance   ! Hash-based distribution
```

**ECMP hashing algorithms:**
| Algorithm | Use Case |
|-----------|----------|
| src-dst-IP | Maximizes flow diversity |
| src-dst-port | Better for elephant flows |
| resilient hashing | Minimizes flow disruption on topology change |

> 💡 **Common mistake:** STP with ECMP is redundant. Use RSTP or eliminate STP entirely with L3 down to the access layer (L3 access design).

---

## Step 4: QoS Design Framework

QoS ensures critical traffic (voice, video) gets priority during congestion.

**DSCP Marking Policy:**
| Class | DSCP | Traffic Type | Bandwidth |
|-------|------|-------------|-----------|
| EF | 46 | VoIP RTP | 10% |
| AF41 | 34 | Video conferencing | 15% |
| AF31 | 26 | Call signaling | 5% |
| AF21 | 18 | Transactional (ERP/DB) | 20% |
| AF11 | 10 | Bulk transfers | 15% |
| BE | 0 | Default / internet | 35% |

**Queuing Architecture (per interface):**
```
Strict Priority Queue (PQ)  -> EF (VoIP)
    Weighted Fair Queue 1   -> AF41 (Video)
    Weighted Fair Queue 2   -> AF21 (Transactional)
    Weighted Fair Queue 3   -> AF11 (Bulk)
    Best-Effort Queue       -> BE (Default)
```

**DSCP marking at ingress (Cisco-style):**
```
class-map match-any VOICE-RTP
 match protocol rtp
policy-map WAN-QOS
 class VOICE-RTP
  set dscp ef
  bandwidth percent 10
  police rate 2 mbps
```

---

## Step 5: Network Documentation Standards

Good documentation is mandatory for enterprise networks.

**Required artifacts:**
1. **Physical topology** — rack layouts, cable runs, patch panel maps
2. **Logical topology** — IP addressing, VLANs, routing domains
3. **Layer 2 map** — STP root, VLANs per switch
4. **Layer 3 map** — routing protocol areas, redistribution points
5. **Change log** — every config change with ticket reference

**Tools:**
- **draw.io** (free, web-based, Git-exportable)
- **NetBox** (IPAM + DCIM + documentation)
- **Visio** (enterprise standard, expensive)
- **Diagrams.net** (open-source draw.io)

**IP Documentation standard (YAML):**
```yaml
network: campus-hq
vlans:
  - id: 10
    name: management
    subnet: 10.0.10.0/24
    gateway: 10.0.10.1
  - id: 20
    name: users
    subnet: 10.0.20.0/22
    gateway: 10.0.20.1
```

---

## Step 6: Spine-Leaf Deep Dive

Spine-leaf is the dominant data center fabric design.

**Design rules:**
1. Every leaf connects to every spine (full mesh between tiers)
2. Leaves never connect to each other (no leaf-to-leaf links)
3. Spines never connect to each other (except in super-spine scenarios)
4. Consistent latency: always 2 hops between any two servers

**Scaling:**
| Fabric Size | Spines | Leaves | Max Servers |
|-------------|--------|--------|-------------|
| Small | 2 | 20 | 1,280 |
| Medium | 4 | 40 | 5,120 |
| Large | 8 | 64 | 16,384 |

**ECMP math:**
- 2 spines → 2 paths per leaf pair
- 4 spines → 4 paths (doubles bandwidth)
- 8 spines → 8 paths (optimal for large scale)

> 💡 **Bandwidth calculation:** If each leaf has 4 × 100G uplinks to 4 spines, and 48 × 25G server ports, the oversubscription ratio is (48 × 25G) / (4 × 100G) = 1200G / 400G = 3:1. Enterprise standard is ≤ 3:1.

---

## Step 7: Verification — Bandwidth Calculator + Topology Generator

```bash
docker run --rm ubuntu:22.04 bash -c "apt-get update -qq && apt-get install -y -qq python3 && python3 -c \"
tiers = [('Core', 2, '100G'), ('Distribution', 4, '40G'), ('Access', 48, '1G')]
for tier, count, speed in tiers:
    print(f'  {tier}: {count} devices @ {speed}')
total_bw = 500 * 10
uplink = total_bw / 20
print(f'Bandwidth: 500 users x 10 Mbps = {total_bw} Mbps total')
print(f'Uplink (20:1 oversub): {uplink} Mbps committed')
print('ECMP paths: 4 equal-cost paths between core switches')
\""
```

📸 **Verified Output:**
```
  Core: 2 devices @ 100G
  Distribution: 4 devices @ 40G
  Access: 48 devices @ 1G
Bandwidth: 500 users x 10 Mbps = 5000 Mbps total
Uplink (20:1 oversub): 250.0 Mbps committed
ECMP paths: 4 equal-cost paths between core switches
```

**Topology ASCII Generator:**
```
Topology (Three-Tier):
       [Core-SW1]═══[Core-SW2]
           ║    ╲ ╱    ║
       [Dist-1]   [Dist-2]
       /    \       /    \
  [Acc-1][Acc-2][Acc-3][Acc-4]
  
Spine-Leaf (DC):
  [Spine-1]─[Spine-2]─[Spine-3]─[Spine-4]
      │×4      │×4       │×4       │×4
  [Leaf-1] [Leaf-2] [Leaf-3] [Leaf-4]
```

---

## Step 8: Capstone — Design a 2,000-User Enterprise Network

**Scenario:** Design a network for a 2,000-user company with:
- 4 floors, 500 users per floor
- Data center with 200 servers
- 2 × 10G internet connections
- Voice/video requirements
- 99.99% uptime requirement

**Your design must include:**

1. **Topology choice** and justification
2. **VLAN plan** (minimum 6 VLANs)
3. **IP addressing scheme** (summarizable, room for growth)
4. **Redundancy** (no single point of failure)
5. **QoS policy** (4 traffic classes minimum)
6. **Bandwidth calculation** for each tier
7. **Documentation plan** (tools, cadence, ownership)

**Reference solution:**
```
Campus: Two-tier (collapsed core) — 2,000 users doesn't justify three-tier
DC: Spine-leaf with 2 spines + 8 leaves
WAN: eBGP multi-homing to 2 ISPs

VLAN plan:
  10   Management      10.0.10.0/24
  20   Users-Floor1    10.0.20.0/23
  30   Users-Floor2    10.0.22.0/23
  40   Users-Floor3    10.0.24.0/23
  50   Users-Floor4    10.0.26.0/23
  100  Voice           10.0.100.0/23
  200  Servers         10.0.200.0/22
  900  DMZ             10.0.9.0/28

Uplink calculation:
  Per floor: 500 × 10 Mbps / 20:1 = 250 Mbps → 2 × 10G (redundant)
  Core uplink: 4 floors × 250 Mbps × 2 = 2 Gbps → 4 × 10G (ECMP)
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| Three-tier | Best for large campuses >5,000 users |
| Collapsed core | Cost-effective for medium campuses |
| Spine-leaf | Mandatory for modern data centers |
| ECMP | Eliminates STP, doubles/quadruples bandwidth |
| Oversubscription | 20:1 access, 4:1 distribution, 1:1 storage |
| QoS | DSCP marking at ingress, queuing at WAN egress |
| Documentation | NetBox + draw.io + YAML as code |

**Next:** [Lab 02: SD-WAN Architecture →](lab-02-sdwan-architecture.md)
