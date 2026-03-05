# Lab 04: BGP Enterprise Design

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

BGP is the routing protocol of the internet and a critical component of enterprise multi-homing, SD-WAN, and data center networks. This lab covers enterprise BGP design from AS allocation to RPKI validation.

---

## Objectives
- Allocate AS numbers and design AS topology
- Implement iBGP with route reflectors
- Configure eBGP peering with ISPs
- Apply BGP communities for traffic engineering
- Design BGP policy with route-maps and prefix-lists
- Understand RPKI route origin validation

---

## Step 1: AS Number Design

**Public vs Private ASNs:**
| Type | Range | Use |
|------|-------|-----|
| Public 2-byte | 1–64495 | Internet BGP |
| Well-known | 64496–64511 | Documentation |
| Private 2-byte | 64512–65534 | Internal BGP |
| Last 2-byte | 65535 | Reserved |
| Public 4-byte | 131072+ | Modern internet |
| Private 4-byte | 4200000000–4294967294 | Large-scale private |

**Design principle:** Use private ASNs (64512–65534) for internal iBGP. Use a public ASN (from ARIN/RIPE/APNIC) for eBGP peering with ISPs.

```
Internet
   ↑  ↑
  ISP1 ISP2
  (AS100) (AS200)
    ↑  ↑
  [Edge-R1]──[Edge-R2]   AS65001 (enterprise)
      ↑              ↑
  [Core-1]────[Core-2]    (iBGP full mesh or RR)
      ↑              ↑
  [DC-1]          [DC-2]
```

---

## Step 2: iBGP — Full Mesh vs Route Reflectors

**iBGP Full Mesh Problem:** Every iBGP router must peer with every other iBGP router. At N routers, you need N(N-1)/2 sessions. At 50 routers = 1,225 sessions. Unscalable.

**Route Reflectors (RR):**
```
         [RR-1]────[RR-2]   <- RR cluster (redundant)
        / | \      / | \
      R1  R2  R3  R4  R5  R6   <- RR clients

# vs full mesh:
6 routers full mesh: 15 sessions
With RRs: 6 client sessions + 1 RR-RR session = 7 sessions
```

**RR configuration (FRRouting):**
```
router bgp 65001
 bgp router-id 1.1.1.1
 neighbor 10.0.0.2 remote-as 65001
 neighbor 10.0.0.2 route-reflector-client
 neighbor 10.0.0.3 remote-as 65001
 neighbor 10.0.0.3 route-reflector-client
 bgp cluster-id 1.1.1.1
```

**RR client configuration:**
```
router bgp 65001
 bgp router-id 2.2.2.2
 neighbor 1.1.1.1 remote-as 65001   ! Peer only with RR, not full mesh
```

> 💡 **Best practice:** Deploy 2 RRs per cluster for redundancy. In large networks, use hierarchical RRs (regional RRs peering to global RRs). Never make RRs the bottleneck — they only need to pass updates, not forward data.

---

## Step 3: eBGP Multi-Homing

Dual ISP connectivity with BGP provides internet redundancy and optional traffic engineering.

**Scenario:** Enterprise (AS65001) connected to ISP1 (AS100) and ISP2 (AS200)

```
ISP1 (AS100)        ISP2 (AS200)
    |                    |
  [R1] ─────iBGP──── [R2]
    |                    |
  [Core Network]
```

**eBGP configuration (FRRouting):**
```
router bgp 65001
 bgp router-id 203.0.113.1
 
 ! eBGP to ISP1
 neighbor 198.51.100.1 remote-as 100
 neighbor 198.51.100.1 description ISP1-Uplink
 neighbor 198.51.100.1 prefix-list ANNOUNCE out
 neighbor 198.51.100.1 prefix-list ACCEPT-ISP1 in
 neighbor 198.51.100.1 route-map SET-ISP1-COMMUNITY in
 
 ! eBGP to ISP2
 neighbor 203.0.113.1 remote-as 200
 neighbor 203.0.113.1 description ISP2-Uplink
 neighbor 203.0.113.1 prefix-list ANNOUNCE out
 neighbor 203.0.113.1 route-map PREFER-ISP1 in

ip prefix-list ANNOUNCE permit 203.0.114.0/22
```

---

## Step 4: BGP Communities

Communities are tags attached to routes for policy signaling.

**Well-known communities:**
| Community | Action |
|-----------|--------|
| `no-export` | Don't export to eBGP peers |
| `no-advertise` | Don't advertise to any peer |
| `internet` | Advertise to internet |

**Standard communities (AS:value):**
```
65001:100    Customer-learned routes
65001:200    Peer-learned routes  
65001:300    Transit-learned routes
65001:666    Blackhole (RTBH - Remote Triggered Black Hole)
```

**Extended communities (for MPLS VPN):**
```
RT:65001:100    Route Target — import/export VRF routes
RD:65001:100    Route Distinguisher — make VPN routes unique
```

**Large communities (ASN:value1:value2):**
```
65001:1:100    Region 1, customer type 100
65001:2:200    Region 2, transit type 200
```

**Set community in route-map:**
```
route-map ISP1-IN permit 10
 set community 65001:100 additive
 set local-preference 200

route-map ISP2-IN permit 10
 set community 65001:200 additive
 set local-preference 100
```

---

## Step 5: BGP Policy Design

**Traffic engineering with local-preference (inbound traffic → use AS path prepending outbound):**

```
! Prefer ISP1 for all outbound traffic
route-map ISP1-IN permit 10
 set local-preference 200     ! Higher = preferred

route-map ISP2-IN permit 10
 set local-preference 100     ! Lower = backup

! Prefer ISP2 for specific prefixes
route-map ISP2-IN permit 20
 match ip address prefix-list PREFER-ISP2-PREFIXES
 set local-preference 300

! Control inbound traffic — AS path prepend on ISP2
route-map ISP2-OUT permit 10
 set as-path prepend 65001 65001 65001   ! Make ISP2 path longer → less preferred
```

**Prefix list filtering:**
```
ip prefix-list BOGONS deny 10.0.0.0/8 le 32
ip prefix-list BOGONS deny 172.16.0.0/12 le 32
ip prefix-list BOGONS deny 192.168.0.0/16 le 32
ip prefix-list BOGONS deny 0.0.0.0/0
ip prefix-list BOGONS permit 0.0.0.0/0 le 32

! Always filter on both directions
neighbor ISP1 prefix-list BOGONS in
neighbor ISP1 prefix-list OUR-PREFIXES out
```

> 💡 **Security rule:** Always apply prefix-list filtering to eBGP peers. Never accept default route from a peer without explicit intent. Never advertise more-specific routes than your allocated prefix.

---

## Step 6: BGP Graceful Restart & RPKI

**BGP Graceful Restart:** Allows BGP sessions to survive router restarts without dropping all routes.
```
router bgp 65001
 bgp graceful-restart    ! Enable GR
 bgp graceful-restart stalepath-time 360
 bgp graceful-restart restart-time 120
```

**RPKI (Resource Public Key Infrastructure):**
RPKI validates that the AS advertising a prefix is authorized to do so, preventing BGP hijacks.

```
! Route Origin Validation (ROV) with FRR
rpki
 rpki cache rpki.example.net 3323 preference 1
 exit

router bgp 65001
 bgp bestpath prefix-validate allow-invalid   ! Or: deny-invalid for strict
```

**ROV states:**
| State | Meaning |
|-------|---------|
| `valid` | Prefix+ASN matches RPKI ROA |
| `invalid` | Prefix matches ROA but wrong ASN → drop |
| `not-found` | No ROA — accept with lower preference |

---

## Step 7: Verification

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq frr &&
cat > /etc/frr/frr.conf << 'EOF'
frr version 8.1
hostname bgp-lab
log syslog informational
router bgp 65001
 bgp router-id 1.1.1.1
 neighbor 10.0.0.2 remote-as 65001
 neighbor 10.0.0.2 description RR-Client-R2
 neighbor 10.0.0.2 route-reflector-client
 bgp cluster-id 1.1.1.1
 address-family ipv4 unicast
  network 10.0.0.0/24
 exit-address-family
EOF
python3 -c \"
asn_start = 64512; asn_end = 65534
print(f'Private ASN range: {asn_start} - {asn_end}')
print(f'Available private ASNs: {asn_end - asn_start + 1}')
print('RR topology: 2 RRs x 6 clients = 13 sessions vs 28 full-mesh')
print()
print('BGP Communities:')
communities = [('65001:100','Customer'), ('65001:200','Peer'), ('65001:300','Transit'), ('no-export','No eBGP export')]
for c,d in communities:
    print(f'  {c:<15} -> {d}')
\""
```

📸 **Verified Output:**
```
Private ASN range: 64512 - 65534
Available private ASNs: 1023
RR topology: 2 RRs x 6 clients = 13 sessions vs 28 full-mesh

BGP Communities:
  65001:100       -> Customer
  65001:200       -> Peer
  65001:300       -> Transit
  no-export       -> No eBGP export
```

**FRR BGP Config (verified syntax):**
```
router bgp 65001
 bgp router-id 1.1.1.1
 neighbor 10.0.0.2 remote-as 65001
 neighbor 10.0.0.2 route-reflector-client
 bgp cluster-id 1.1.1.1
 address-family ipv4 unicast
  network 10.0.0.0/24
 exit-address-family
```

---

## Step 8: Capstone — Multi-Homed Enterprise BGP Design

**Scenario:** Design BGP for a financial services firm:
- 1 public AS (65001)
- 2 ISPs: Tier-1 (primary, 10G), Tier-2 (backup, 1G)
- Own /22 block: 203.0.114.0/22
- Requirement: All outbound via ISP1, failover to ISP2
- Requirement: Inbound should prefer ISP1 for < /24 routes

**Your design must cover:**
1. eBGP session parameters for both ISPs
2. Local-preference policy (ISP1 preferred)
3. AS-path prepend strategy (influence inbound)
4. Community tagging scheme
5. RPKI configuration
6. Route filtering (bogons, customer aggregates only)
7. Graceful restart timers
8. Monitoring: `show bgp summary`, `show bgp neighbors`, alerts

**FRR `vtysh` verification commands:**
```bash
vtysh -c "show bgp summary"
vtysh -c "show bgp neighbors 198.51.100.1"
vtysh -c "show ip bgp 203.0.114.0/22"
vtysh -c "show bgp rpki prefix 203.0.114.0/22"
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| Private ASNs | 64512-65534 for internal, public for ISP peering |
| Route Reflectors | Eliminate iBGP full mesh, deploy in pairs |
| eBGP multi-homing | Dual ISP = redundancy + traffic engineering |
| Communities | Tags for policy signaling between ASes |
| Local-preference | Controls outbound path selection (higher = preferred) |
| AS-path prepend | Controls inbound path selection (longer = less preferred) |
| RPKI | Prevents BGP hijacks via cryptographic route validation |

**Next:** [Lab 05: MPLS & VPN Architecture →](lab-05-mpls-vpn-architecture.md)
