# Lab 02: SD-WAN Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

SD-WAN revolutionized enterprise WAN by decoupling network intelligence from hardware, enabling application-aware routing, centralized management, and cost reduction through hybrid underlay support.

---

## Objectives
- Contrast traditional WAN vs SD-WAN architecture
- Understand underlay vs overlay design
- Simulate application-aware path selection
- Compare MPLS, internet, and LTE underlay options
- Evaluate major SD-WAN vendors

---

## Step 1: Traditional WAN vs SD-WAN

**Traditional WAN (Hub-and-Spoke MPLS):**
```
Branch-1 ──┐
Branch-2 ──┤── [MPLS Cloud] ── HQ
Branch-3 ──┘
```
Problems:
- All traffic must traverse HQ (hairpinning)
- MPLS circuits are expensive (3-10× internet cost)
- Provisioning takes weeks
- No application visibility

**SD-WAN Architecture:**
```
              [SD-WAN Controller]
                    │ (management plane)
    ┌───────────────┼───────────────┐
Branch-1        Branch-2        Branch-3
(MPLS+LTE)      (Internet)      (MPLS+Internet)
    └───────────── Overlay ─────────┘
```
Benefits:
- Application-aware traffic steering
- Hybrid underlay (MPLS + internet + LTE)
- Zero-touch provisioning (ZTP)
- 50-70% WAN cost reduction typical

---

## Step 2: Underlay vs Overlay

**Underlay:** Physical transport networks (MPLS, internet broadband, LTE/5G)
**Overlay:** Virtual tunnels (IPSec/GRE) built on top of underlay

```
Application Layer     HTTP/S, VoIP, SAP, Office365
      ↑
SD-WAN Overlay        IPSec tunnels, policy enforcement
      ↑
Underlay Transport    MPLS (low latency) / Internet (high bandwidth) / LTE (backup)
```

**Underlay comparison:**
| Property | MPLS | Internet | LTE/5G |
|----------|------|----------|--------|
| Latency | 5-20ms | 20-80ms | 30-100ms |
| Jitter | <2ms | 5-20ms | 10-50ms |
| Packet loss | <0.01% | 0.1-1% | 0.5-2% |
| Cost | $$$ | $ | $$ |
| SLA | Yes | No | Limited |
| Bandwidth | 10-1000M | 10-10000M | 5-1000M |

> 💡 **Best practice:** Deploy minimum 2 underlays per branch. Primary: MPLS or fiber internet. Secondary: LTE/5G for resilience. The cost savings from eliminating pure MPLS typically fund the LTE backup.

---

## Step 3: Zero-Touch Provisioning (ZTP)

ZTP eliminates manual on-site configuration of branch routers.

**ZTP flow:**
```
1. Device boots → contacts cloud bootstrap server via DHCP option 43
2. Bootstrap server → authenticates device serial number
3. Downloads: OS image, config template, certificates
4. Device registers with SD-WAN controller
5. Controller pushes site-specific configuration
6. Branch goes live: < 30 minutes vs 2-4 weeks manual
```

**Key components:**
- **SD-WAN Controller** (vManage / Orchestrator): centralized policy and monitoring
- **SD-WAN Gateway/Hub** (vSmart / Hub): route distribution, policy enforcement
- **SD-WAN Edge** (vEdge / CPE): branch appliance with SD-WAN software

---

## Step 4: Application-Aware Routing

Traffic steering based on real-time link quality per application:

**Policy model:**
```
IF application = VoIP
  AND path MPLS meets: latency < 30ms, jitter < 5ms, loss < 0.1%
  THEN use MPLS
  ELSE IF path Internet meets: latency < 60ms, jitter < 10ms, loss < 0.5%
       THEN use Internet
       ELSE use LTE (last resort)

IF application = Office365
  AND has direct internet path
  THEN use Internet (direct cloud breakout, bypass HQ)
```

**BFD (Bidirectional Forwarding Detection):** SD-WAN uses BFD to continuously measure path quality (latency, jitter, loss) at 100ms intervals. When a path degrades, traffic migrates to alternative paths in < 1 second.

**Application identification:**
- DPI (Deep Packet Inspection) — Layer 7 signatures
- NBAR (Cisco) / AppID (Palo Alto) — named application detection
- First-packet classification — classify without full flow inspection

---

## Step 5: WAN Optimization Techniques

SD-WAN includes optimization features to maximize link efficiency:

**Compression:** LZ4/Zstd compress repetitive data patterns
- Typical compression ratio: 3:1 for text/HTML, 1.5:1 for mixed, 1:1 for encrypted/video

**Forward Error Correction (FEC):** Add redundant packets to recover from loss
- 10% overhead can recover from up to 5% packet loss
- Useful for LTE paths with variable quality

**Packet Duplication:** Send same packet on 2 paths simultaneously
- Receiver uses whichever arrives first
- Used for real-time apps (VoIP) on unreliable paths

**TCP Optimization:**
- TCP window scaling without WAN RTT impact
- Spoofing TCP ACKs locally to improve throughput
- SMB acceleration for file share performance

---

## Step 6: Major SD-WAN Vendors

| Vendor | Platform | Strength |
|--------|----------|----------|
| Cisco | Catalyst SD-WAN (Viptela) | Enterprise scale, IOS integration |
| VMware | VeloCloud | Cloud-native, NSX integration |
| Fortinet | Secure SD-WAN | Built-in NGFW, no separate security stack |
| Palo Alto | Prisma SD-WAN | Best-in-class SASE integration |
| Versa | Versa Networks | OpenSource-friendly, flexible licensing |
| Aruba | EdgeConnect (Silver Peak) | WAN optimization heritage |

**SASE (Secure Access Service Edge):** Convergence of SD-WAN with cloud-delivered security (SWG, CASB, ZTNA, FWaaS). Gartner's recommended architecture for 2025+.

> 💡 **Architecture trend:** Purpose-built SD-WAN is giving way to SASE. When evaluating SD-WAN vendors, assess their SASE roadmap and cloud PoP coverage (Zscaler, Netskope, Cloudflare One integration).

---

## Step 7: Verification — Path Selection Simulator

```bash
docker run --rm ubuntu:22.04 bash -c "apt-get update -qq && apt-get install -y -qq python3 && python3 - << 'EOF'
paths = [
    {'name': 'MPLS',     'latency': 15, 'jitter': 2,  'loss': 0.01},
    {'name': 'Internet', 'latency': 45, 'jitter': 12, 'loss': 0.5},
    {'name': 'LTE',      'latency': 60, 'jitter': 20, 'loss': 1.2},
]
def score(p):
    return p['latency']*0.5 + p['jitter']*0.3 + p['loss']*100*0.2
best = min(paths, key=score)
print('SD-WAN Path Selection Simulator')
print('-'*50)
print(f'{\"Path\":<12} {\"Latency(ms)\":>11} {\"Jitter(ms)\":>10} {\"Loss%\":>6} {\"Score\":>7}')
print('-'*50)
for p in paths:
    s = score(p)
    m = ' <- SELECTED' if p == best else ''
    print(f\"{p['name']:<12} {p['latency']:>11} {p['jitter']:>10} {p['loss']:>6} {s:>7.2f}{m}\")
print(f'\\nSelected: {best[\"name\"]} | Policy: VoIP->MPLS, Bulk->Internet')
EOF"
```

📸 **Verified Output:**
```
SD-WAN Path Selection Simulator
--------------------------------------------------
Path         Latency(ms) Jitter(ms)  Loss%   Score
--------------------------------------------------
MPLS                  15          2   0.01    8.30 <- SELECTED
Internet              45         12    0.5   36.10
LTE                   60         20    1.2   60.00

Selected: MPLS | Policy: VoIP->MPLS, Bulk->Internet
```

---

## Step 8: Capstone — Design an SD-WAN for 50 Branches

**Scenario:** Global retail chain, 50 branch offices (40 small, 10 large), 2 data centers, heavy cloud usage (Office 365, Salesforce, SAP on Azure).

**Design deliverables:**

1. **Underlay selection** per branch type:
   - Small branch (< 20 users): _______________
   - Large branch (> 100 users): _______________

2. **Traffic steering policies** (define 5 application classes)

3. **Security architecture** — where does inspection happen?
   - Internet-bound traffic: breakout locally or backhaul to DC?
   - SaaS: how to optimize?

4. **Failure scenarios:**
   - MPLS circuit fails → ?
   - Both links fail → ?
   - Controller unreachable → ?

**Reference answers:**
```
Small branch: Dual internet (fiber + LTE backup)
Large branch: MPLS (10-50M) + internet (100M) + LTE (backup)

Traffic classes:
  1. Real-time (VoIP/Video): MPLS preferred, SLA strict
  2. Interactive (ERP/CRM): MPLS primary, Internet fallback
  3. Cloud (O365/Salesforce): Direct internet breakout (CASB inspection)
  4. Bulk (backups): Internet, background priority
  5. Guest/IOT: Internet only, isolated VLAN

Security: SASE cloud (Zscaler or Cloudflare One)
  - All internet traffic → SASE PoP for inspection
  - SaaS: optimized via SD-WAN + SASE
  - DC: hairpin through DC firewall for on-prem apps

Failure:
  - MPLS fails: auto-steer to Internet (< 500ms via BFD)
  - Both links fail: LTE 4G emergency backup activates
  - Controller unreachable: last good policy continues operating (local forwarding)
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| SD-WAN vs WAN | SD-WAN adds application awareness, reduces cost |
| Underlay | MPLS (quality) + Internet (cost) + LTE (resilience) |
| ZTP | Branch up in <30 min, no on-site tech needed |
| App-aware routing | BFD measures path quality; policy drives steering |
| FEC/dedup | Improve effective quality on lossy paths |
| SASE | Next evolution: SD-WAN + cloud security converged |

**Next:** [Lab 03: Network Automation with Ansible →](lab-03-network-automation-ansible.md)
