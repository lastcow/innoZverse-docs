# Enterprise Network Design

## 3-Tier Architecture

```
                    [Internet]
                        │
                 [Edge Router / ISP]
                        │
              [Core Layer] ← High-speed switching backbone
             /     │      \
    [Distribution] [Distribution] [Distribution]
        │               │               │
   [Access]         [Access]        [Access]
   [Switches]       [Switches]      [Switches]
       │                │               │
   [End Devices]    [Servers]      [Wireless APs]
```

## Leaf-Spine Data Center Fabric

```
[Spine 1]──────────────────────[Spine 2]
   │  │  │                    │  │  │
   │  │  └──────────┐         │  │  │
[L1][L2][L3]    [L4][L5][L6][L7][L8][L9]
 │   │   │        Every leaf connects to every spine
[Servers]          Equal-cost multipath (ECMP)
```

## BGP Design

```bash
# eBGP between ISPs
router bgp 65001
  bgp router-id 1.1.1.1
  neighbor 203.0.113.1 remote-as 65002    # ISP 1
  neighbor 198.51.100.1 remote-as 65003   # ISP 2
  
  # Inbound: prefer ISP 1
  neighbor 203.0.113.1 route-map PREFER-ISP1 in
  
  # Outbound: advertise your prefix
  network 192.0.2.0 mask 255.255.255.0

# Route map
route-map PREFER-ISP1 permit 10
  set local-preference 200

route-map PREFER-ISP2 permit 10
  set local-preference 100
```

## SD-WAN Architecture

```
Branch Office ──→ SD-WAN Edge ──→ [Transport: MPLS/Internet/LTE]
                      ↓
                [SD-WAN Orchestrator] (Viptela/Meraki/Versa)
                      ↓
                [Data Center / Cloud]

Benefits:
✅ Application-aware routing
✅ Zero-touch provisioning
✅ Centralized policy management
✅ WAN optimization
✅ Reduced MPLS costs
```

## Network Capacity Planning

```python
# Bandwidth utilization calculation
def bandwidth_util(current_mbps, capacity_mbps, growth_rate=0.2):
    """Calculate years until bandwidth saturation"""
    years = 0
    while current_mbps < capacity_mbps * 0.8:  # 80% threshold
        current_mbps *= (1 + growth_rate)
        years += 1
    return years

print(bandwidth_util(500, 1000))  # Years until 80% at 20% annual growth
```
