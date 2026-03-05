# Lab 05: MPLS & VPN Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

MPLS (Multi-Protocol Label Switching) is the backbone of service provider networks and enterprise WAN. This lab covers label forwarding mechanics, L3VPN architecture, traffic engineering, and the evolution to Segment Routing.

---

## Objectives
- Understand MPLS label forwarding (push/swap/pop)
- Compare LDP vs RSVP-TE label distribution
- Design MPLS L3VPN with VRF/RD/RT
- Understand P/PE/CE router roles
- Configure MPLS Traffic Engineering (TE)
- Evaluate Segment Routing (SR-MPLS vs SRv6)

---

## Step 1: MPLS Label Forwarding

MPLS adds a 32-bit label between Layer 2 and Layer 3 headers, enabling fast forwarding without IP lookup.

**Label structure (32 bits):**
```
┌─────────────────────┬─────┬───┬─────────┐
│     Label (20 bits) │ EXP │ S │  TTL    │
│                     │ 3b  │1b │  8 bits │
└─────────────────────┴─────┴───┴─────────┘
EXP: Traffic class (QoS)
S:   Bottom of Stack flag (1 = last label)
TTL: Time to Live
```

**Label operations:**
| Operation | Where | Action |
|-----------|-------|--------|
| PUSH | Ingress PE | Add label to packet |
| SWAP | P (core) routers | Replace label |
| POP | Egress PE | Remove label |
| PHP | Penultimate-hop | Pop before final PE |

**Forwarding example:**
```
CE1 → [IP packet] → PE1 → [label 5678 | label 1234 | IP] → P1 → P2 → PE2 → CE2
                          ↑                                ↑
                    PUSH (ingress)                  PHP (pop transport)
                    outer=transport label          inner=VPN label remains
                    inner=VPN label
```

---

## Step 2: Label Distribution — LDP vs RSVP-TE

**LDP (Label Distribution Protocol):**
- Automatic label distribution along IGP best paths
- No traffic engineering capability
- Simple to configure
- Follows OSPF/ISIS shortest path only

```
! LDP configuration (Cisco)
mpls ldp autoconfig
interface GigabitEthernet0/0
 mpls ip
```

**RSVP-TE (Resource Reservation Protocol — Traffic Engineering):**
- Explicit path setup (can route around congestion)
- Bandwidth reservation per LSP (Label Switched Path)
- Required for MPLS Traffic Engineering
- More complex, requires CSPF (Constrained Shortest Path First)

```
! RSVP-TE tunnel (Cisco)
interface Tunnel0
 tunnel mode mpls traffic-eng
 tunnel mpls traffic-eng bandwidth 100000   ! 100 Mbps
 tunnel mpls traffic-eng path-option 1 explicit name PATH1
 tunnel mpls traffic-eng fast-reroute
```

> 💡 **When to use which:** LDP for simple L3VPN service delivery. RSVP-TE when you need explicit path control, bandwidth guarantees, or Fast Reroute (sub-50ms failover). Segment Routing is gradually replacing both.

---

## Step 3: MPLS L3VPN Architecture

L3VPN is the most common MPLS service: enterprise sites connected via shared MPLS backbone while maintaining full routing isolation.

**Router roles:**
```
CE (Customer Edge)  → Customer's router, speaks only IP
PE (Provider Edge)  → Connects CE to MPLS core, has VRF
P  (Provider core)  → Core MPLS router, no VRF needed

CE1 ──── PE1 ═════════════════ PE2 ──── CE2
  (IP)     (VRF/MPLS)   (MPLS)   (VRF/MPLS)   (IP)
```

**VRF (Virtual Routing and Forwarding):**
```
! PE1 configuration
ip vrf CUSTOMER-A
 rd 65001:100              ! Route Distinguisher - makes VPN routes unique
 route-target export 65001:100   ! RT exported to other PEs
 route-target import 65001:100   ! RT imported from other PEs

interface GigabitEthernet0/0    ! CE-facing interface
 ip vrf forwarding CUSTOMER-A
 ip address 10.0.0.2 255.255.255.252

! CE-PE BGP peering (per-VRF)
router bgp 65001
 address-family ipv4 vrf CUSTOMER-A
  neighbor 10.0.0.1 remote-as 64512   ! CE's AS
  neighbor 10.0.0.1 activate
```

**MP-BGP for VPN route distribution between PEs:**
```
router bgp 65001
 neighbor 2.2.2.2 remote-as 65001   ! iBGP to PE2
 neighbor 2.2.2.2 update-source Loopback0
 
 address-family vpnv4
  neighbor 2.2.2.2 activate
  neighbor 2.2.2.2 send-community extended
```

---

## Step 4: Route Distinguisher vs Route Target

**Route Distinguisher (RD):** Makes VPN route unique in the global BGP table
- Format: `ASN:number` or `IP:number`
- 65001:100 means: PE65001, VPN 100
- Different PEs with same customer use different RDs

**Route Target (RT):** Controls import/export of VPN routes
- Export RT: Tag routes leaving a VRF
- Import RT: Accept routes with matching RT into VRF

**Hub-and-spoke VPN:**
```
Spoke VRF (branch):
  export RT: 65001:200
  import RT: 65001:100    ! Only receive hub routes

Hub VRF (datacenter):
  export RT: 65001:100
  import RT: 65001:200    ! Receive all spoke routes
```

**Full-mesh VPN:**
```
All sites:
  export RT: 65001:1
  import RT: 65001:1      ! Everyone imports everyone
```

---

## Step 5: MPLS Traffic Engineering & Fast Reroute

**MPLS-TE objectives:**
- Route traffic along non-shortest paths to avoid congestion
- Reserve bandwidth along LSPs
- Preempt lower-priority LSPs when needed

**CSPF constraints:**
```
! Avoid specific link/node
tunnel mpls traffic-eng path-option 1 explicit name AVOID-R3
ip explicit-path name AVOID-R3
 next-address 10.0.1.2    ! Hop 1
 next-address 10.0.2.2    ! Hop 2 (bypass R3)
 next-address 10.0.3.1    ! Destination PE
```

**Fast Reroute (FRR) — sub-50ms failover:**
```
! Primary LSP
interface Tunnel0
 tunnel mpls traffic-eng fast-reroute
 tunnel mpls traffic-eng priority 5 5

! Backup LSP (automatically computed)
mpls traffic-eng fast-reroute
mpls traffic-eng frr facility-backup   ! Facility backup = single bypass LSP protects multiple primaries
```

---

## Step 6: Segment Routing — SR-MPLS & SRv6

Segment Routing replaces LDP/RSVP-TE with source-routing: the ingress node encodes the entire path in the packet header.

**SR-MPLS:** Uses MPLS label stack (backward-compatible)
```
! FRR SR configuration
segment-routing
 global-block 16000 23999   ! SRGB (Segment Routing Global Block)

router ospf 1
 segment-routing on
 segment-routing global-block 16000 23999

interface Loopback0
 ip ospf segment-routing sid prefix-sid absolute 16001   ! Node SID
```

**SRv6:** Uses IPv6 extension header (Segment Routing Header)
- 128-bit SID = IPv6 address → natively routable
- Enables network slicing, service function chaining
- Simplifies MPLS stack to pure IPv6

**SR vs traditional MPLS:**
| Feature | LDP | RSVP-TE | SR-MPLS |
|---------|-----|---------|---------|
| Traffic Engineering | No | Yes | Yes |
| FRR | No | Yes | Yes (TI-LFA) |
| Complexity | Low | High | Low |
| Scalability | Medium | Low | High |
| Signaling | LDP | RSVP | None (controller) |

> 💡 **Industry direction:** Segment Routing with SPRING (Source Packet Routing in Networking) is the future. Hyperscalers (Google, Facebook) have deployed SRv6 at massive scale. New deployments should prefer SR over RSVP-TE.

---

## Step 7: Verification — Label Stack Simulator

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 iproute2 &&
python3 - << 'EOF'
class Label:
    def __init__(self, val, bos=0, ttl=64):
        self.val, self.bos, self.ttl = val, bos, ttl
    def __repr__(self):
        return f'[{self.val}|bos={self.bos}|ttl={self.ttl}]'

stack = []
payload = '10.1.1.1 -> 192.168.100.1'
print(f'Payload: {payload}')

stack.append(Label(1234, bos=1, ttl=64))
print(f'  PUSH VPN label 1234:  {stack}')
stack.append(Label(5678, bos=0, ttl=64))
print(f'  PUSH transport 5678:  {stack}')
stack[-1] = Label(9012, bos=0, ttl=63)
print(f'  SWAP 5678->9012 (P):  {stack}')
stack.pop()
print(f'  PHP pop transport:    {stack}')
print(f'  Egress PE: forward via VRF, deliver to CE')
EOF
ip -M route 2>/dev/null || echo 'ip -M route: MPLS kernel module not loaded (expected in container)'"
```

📸 **Verified Output:**
```
Payload: 10.1.1.1 -> 192.168.100.1
  PUSH VPN label 1234:  [[1234|bos=1|ttl=64]]
  PUSH transport 5678:  [[1234|bos=1|ttl=64], [5678|bos=0|ttl=64]]
  SWAP 5678->9012 (P):  [[1234|bos=1|ttl=64], [9012|bos=0|ttl=63]]
  PHP pop transport:    [[1234|bos=1|ttl=64]]
  Egress PE: forward via VRF, deliver to CE
ip -M route: MPLS kernel module not loaded (expected in container)
```

---

## Step 8: Capstone — Service Provider VPN Design

**Scenario:** Design MPLS L3VPN for 3 enterprise customers:

**Customer A (Full mesh):** 5 sites, needs any-to-any connectivity
**Customer B (Hub-spoke):** 20 branches, all traffic through HQ data center
**Customer C (Extranet):** Needs to share routes with Customer A's site 3

**Design answers:**

```
Customer A:
  RD: 65001:1xx (per-PE, e.g., 65001:101 on PE1)
  RT export: 65001:10
  RT import: 65001:10     ! Full mesh

Customer B:
  Hub VRF:
    RT export: 65001:21 (hub exports)
    RT import: 65001:20 (imports spoke routes)
  Spoke VRF:
    RT export: 65001:20 (spoke exports)
    RT import: 65001:21 (imports hub routes only)

Customer C / Extranet:
  Customer C site:
    RT import: 65001:10  ! Import Customer A routes
  Customer A site 3:
    RT export: 65001:10, 65001:30  ! Export to both A and C

Segment Routing migration plan:
  Phase 1: Enable SR-MPLS alongside LDP (dual-stack)
  Phase 2: Migrate PE-PE tunnels to SR
  Phase 3: Retire LDP, deploy SR-TE policies
  Phase 4: Evaluate SRv6 for next-gen fabric
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| MPLS forwarding | Label push/swap/pop replaces IP lookup in core |
| LDP | Automatic label distribution, no TE capability |
| RSVP-TE | Explicit paths, bandwidth reservation, FRR |
| L3VPN | VRF isolation + MP-BGP route distribution between PEs |
| RD | Makes VPN routes globally unique in BGP |
| RT | Controls which VRFs import/export routes |
| Segment Routing | Replaces LDP+RSVP-TE, source-routing via SID stack |

**Next:** [Lab 06: Advanced Cloud Networking →](lab-06-cloud-networking-advanced.md)
