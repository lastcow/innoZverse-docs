# Lab 17: Network Micro-Segmentation — Namespaces, Policy-as-Code & Service Mesh

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm --privileged ubuntu:22.04 bash`

## Overview

Implement network micro-segmentation using Linux network namespaces, veth pairs, and iptables — then extend the concept to Kubernetes Network Policies and service mesh mTLS. Micro-segmentation provides east-west security controls that traditional perimeter firewalls cannot enforce.

## Architecture: Micro-Segmentation Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Micro-Segmentation Architecture                     │
│                                                                      │
│  ┌──────────┐  ✗  ┌──────────┐  ✓  ┌──────────┐  ✗  ┌──────────┐ │
│  │  Web     │────►│  App     │────►│  DB      │────►│ Payment  │ │
│  │  Tier    │     │  Tier    │     │  Tier    │     │  Tier    │ │
│  │  seg-web │     │  seg-app │     │  seg-db  │     │  seg-pay │ │
│  └──────────┘     └──────────┘     └──────────┘     └──────────┘ │
│                                                                      │
│  Policy Engine (JSON rules → iptables/NetworkPolicy)               │
│  East-West Control: ALLOW only explicit flows, DENY all else       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: The East-West Security Problem

Traditional security assumes a hard perimeter (North-South):
```
Internet → Firewall → Internal Network (trusted)
                              ↓
              No controls on internal lateral movement!
```

**Why micro-segmentation:**
- Attackers who breach perimeter move freely laterally
- 70% of breaches involve lateral movement (IBM X-Force)
- PCI DSS requires segmentation of Cardholder Data Environment (CDE)
- Zero Trust: "never trust, always verify" — even internal traffic

**Micro-segmentation zones:**
```
Traditional: 1 flat network → 1 breach = full access
Micro:       N segments    → 1 breach = 1 segment only

  Blast radius reduction: 100% → 1/N per segment
```

---

## Step 2: Linux Network Namespaces as Micro-Segments

Network namespaces provide complete network isolation at the kernel level:

```bash
# Create isolated network segments (micro-segments)
ip netns add seg-web
ip netns add seg-app
ip netns add seg-db

# Each namespace has its own:
# - Network interfaces
# - Routing table
# - iptables rules
# - ARP table
# - Socket space

# Verify isolation
ip netns exec seg-web ip link  # Only lo, no other interfaces
```

### Namespace = Container Network Model
This is exactly how **Docker** and **Kubernetes** implement network isolation:
```
Docker container → Linux network namespace + veth pair
Kubernetes Pod   → Linux network namespace + veth pair (managed by CNI)
```

---

## Step 3: veth Pairs — Virtual Network Cables

Connect namespaces with virtual ethernet (veth) pairs:

```bash
# Create veth pair: veth-web ↔ veth-app (virtual cable)
ip link add veth-web type veth peer name veth-app

# Assign each end to its namespace
ip link set veth-web netns seg-web
ip link set veth-app netns seg-app

# Configure addresses
ip netns exec seg-web ip addr add 10.10.1.1/24 dev veth-web
ip netns exec seg-app ip addr add 10.10.1.2/24 dev veth-app

# Bring up interfaces
ip netns exec seg-web ip link set veth-web up
ip netns exec seg-app ip link set veth-app up
ip netns exec seg-web ip link set lo up
ip netns exec seg-app ip link set lo up
```

### Multi-Segment Topology (via bridge)
```bash
# Create a bridge as the "network fabric"
ip link add br-fabric type bridge
ip link set br-fabric up

# Connect all segments to the bridge
for seg in web app db pay; do
    ip link add veth-${seg}-a type veth peer name veth-${seg}-b
    ip link set veth-${seg}-b master br-fabric
    ip link set veth-${seg}-b up
    ip netns add seg-${seg}
    ip link set veth-${seg}-a netns seg-${seg}
done
```

---

## Step 4: Per-Namespace iptables Policies

Each network namespace has independent iptables rule sets:

```bash
# Default deny policy for all namespaces
for ns in seg-web seg-app seg-db; do
    ip netns exec ${ns} iptables -P INPUT DROP
    ip netns exec ${ns} iptables -P FORWARD DROP
    ip netns exec ${ns} iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    ip netns exec ${ns} iptables -A INPUT -i lo -j ACCEPT
done

# Allow: seg-web → seg-app (TCP 8080 only)
ip netns exec seg-app iptables -A INPUT -s 10.10.1.1 -p tcp --dport 8080 -j ACCEPT

# Allow: seg-app → seg-db (TCP 5432 only)
ip netns exec seg-db iptables -A INPUT -s 10.10.1.2 -p tcp --dport 5432 -j ACCEPT

# Deny: seg-web → seg-db (direct DB access blocked)
ip netns exec seg-db iptables -A INPUT -s 10.10.1.1 -j DROP
```

---

## Step 5: Micro-Segmentation Demo with Connectivity Matrix

```bash
# Full demo script (run in privileged Docker container)
docker run --rm --privileged ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq iproute2 iptables iputils-ping 2>/dev/null

# Create segments
ip netns add seg-a
ip netns add seg-b

# Wire them together
ip link add veth-a type veth peer name veth-b
ip link set veth-a netns seg-a
ip link set veth-b netns seg-b

# Configure addresses
ip netns exec seg-a ip addr add 10.10.1.1/24 dev veth-a
ip netns exec seg-b ip addr add 10.10.1.2/24 dev veth-b
ip netns exec seg-a ip link set veth-a up && ip netns exec seg-a ip link set lo up
ip netns exec seg-b ip link set veth-b up && ip netns exec seg-b ip link set lo up

echo '--- Segment A interface ---'
ip netns exec seg-a ip addr show veth-a

echo '--- Before policy (ping should work) ---'
ip netns exec seg-a ping -c2 10.10.1.2

echo '--- Apply DROP rule in seg-b ---'
ip netns exec seg-b iptables -A INPUT -s 10.10.1.1 -j DROP

echo '--- After policy (should be BLOCKED) ---'
ip netns exec seg-a ping -c2 -W1 10.10.1.2 && echo REACHABLE || echo BLOCKED
"
```

📸 **Verified Output:**
```
--- Segment A interface ---
4: veth-a@if3: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
    link/ether aa:90:c2:b5:58:43 brd ff:ff:ff:ff:ff:ff link-netns seg-b
    inet 10.10.1.1/24 scope global veth-a
       valid_lft forever preferred_lft forever
    inet6 fe80::a890:c2ff:feb5:5843/64 scope link tentative 
       valid_lft forever preferred_lft forever
--- Before policy (ping should work) ---
PING 10.10.1.2 (10.10.1.2) 56(84) bytes of data.
64 bytes from 10.10.1.2: icmp_seq=1 ttl=64 time=0.130 ms
64 bytes from 10.10.1.2: icmp_seq=2 ttl=64 time=0.042 ms

--- 10.10.1.2 ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1027ms
--- Apply DROP rule in seg-b ---
--- After policy (should be BLOCKED) ---
PING 10.10.1.2 (10.10.1.2) 56(84) bytes of data.

--- 10.10.1.2 ping statistics ---
2 packets transmitted, 0 received, 100% packet loss, time 1061ms

BLOCKED
```

### Connectivity Matrix
```
         → seg-web  → seg-app  → seg-db  → seg-pay
seg-web  │    -    │  TCP 443  │   ✗     │   ✗    │
seg-app  │   ✗     │    -      │ TCP 5432│   ✗    │
seg-db   │   ✗     │   ✗       │   -     │   ✗    │
seg-pay  │   ✗     │  TCP 9090 │ TCP 5432│   -    │

Legend: ✗=DENY, TCP N=ALLOW specific port only
```

---

## Step 6: Policy-as-Code (JSON Rules → iptables)

```python
import json, subprocess

policy = {
    "version": "1.0",
    "segments": {
        "seg-web": {"cidr": "10.10.1.0/28"},
        "seg-app": {"cidr": "10.10.1.16/28"},
        "seg-db":  {"cidr": "10.10.1.32/28"},
    },
    "rules": [
        {"from": "seg-web", "to": "seg-app", "proto": "tcp", "port": 443,  "action": "ACCEPT"},
        {"from": "seg-app", "to": "seg-db",  "proto": "tcp", "port": 5432, "action": "ACCEPT"},
        {"from": "*",       "to": "*",       "proto": "all", "port": None,  "action": "DROP"},
    ]
}

def policy_to_iptables(policy):
    cmds = []
    segs = policy["segments"]
    for rule in policy["rules"]:
        src = segs.get(rule["from"], {}).get("cidr", "0.0.0.0/0") if rule["from"] != "*" else "0.0.0.0/0"
        if rule["port"]:
            cmd = f"iptables -A FORWARD -s {src} -p {rule['proto']} --dport {rule['port']} -j {rule['action']}"
        else:
            cmd = f"iptables -A FORWARD -s {src} -j {rule['action']}"
        cmds.append(cmd)
        print(f"  {cmd}")
    return cmds

print("=== Generated iptables rules from policy JSON ===")
policy_to_iptables(policy)
```

> 💡 This is the foundation of **Kubernetes Network Policy** — declarative JSON/YAML policies compiled to iptables/eBPF rules by CNI plugins.

---

## Step 7: Kubernetes Network Policy — Calico vs Cilium

### Kubernetes Network Policy Structure
```yaml
# Allow only seg-app to reach seg-db on port 5432
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: db-ingress-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      tier: database              # Apply to DB pods
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: app               # Only from app pods
    ports:
    - protocol: TCP
      port: 5432
```

### Calico vs Cilium Comparison

| Feature | Calico | Cilium |
|---------|--------|--------|
| Data plane | iptables / eBPF | eBPF (native) |
| Policy model | NetworkPolicy + GlobalNetworkPolicy | NetworkPolicy + CiliumNetworkPolicy |
| L7 filtering | Limited | Yes (HTTP, gRPC, Kafka) |
| Performance | Good (iptables) / Excellent (eBPF) | Excellent |
| Observability | Flow logs | Hubble (full L3-L7) |
| WireGuard encryption | Yes | Yes |
| BGP integration | Yes (calico-bgp) | No |
| Complexity | Medium | Medium-High |

```
Calico eBPF data path:
  Pod A → eBPF hook → policy check → Pod B
  (bypasses iptables entirely, ~30% latency reduction)

Cilium identity model:
  Not IP-based but identity-based (label hash → uint32 security ID)
  Policy: "allow identity=app to talk to identity=db on TCP 5432"
  Survives pod restarts without policy update
```

---

## Step 8: Capstone — Service Mesh mTLS & Zero Trust East-West

### Istio Sidecar Pattern
```
Without service mesh:
  Service A ──plain text──► Service B

With Istio mTLS:
  Service A → [Envoy sidecar] ──TLS 1.3──► [Envoy sidecar] → Service B
                ↕ Policy                          ↕ Policy
              Istiod (control plane)

mTLS benefits:
  - Mutual authentication (both sides present certs)
  - Workload identity via SPIFFE/SPIRE (X.509 SVIDs)
  - Automatic cert rotation (no manual PKI management)
  - L7 policy enforcement (HTTP headers, gRPC methods)
```

### mTLS Policy Example (Istio)
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT          # All traffic must use mTLS

---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: db-policy
spec:
  selector:
    matchLabels:
      app: postgres
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/app-service"]
    to:
    - operation:
        ports: ["5432"]
```

### Complete East-West Security Architecture

```
Zero Trust East-West Controls (layered):

Layer 1 — Network: Micro-segmentation (VLAN/namespace isolation)
Layer 2 — Firewall: iptables/eBPF policy (L3/L4 filtering)
Layer 3 — Service Mesh: mTLS (L7 identity + encryption)
Layer 4 — App: JWT/OAuth token validation

Security posture:
  Before segmentation: 1 breach = all services compromised
  After all 4 layers:  1 breach = 1 micro-segment + identity-gated
```

---

## Summary

| Concept | Implementation | Use Case |
|---------|---------------|---------|
| Network namespace | `ip netns add` | Container/VM isolation |
| veth pair | `ip link add type veth` | Connect segments |
| Per-namespace firewall | `ip netns exec iptables` | Micro-segment policy |
| Policy-as-code | JSON → iptables | Declarative security |
| Kubernetes NetworkPolicy | CNI plugin enforcement | Pod-level segmentation |
| Calico | iptables/eBPF + BGP | Enterprise K8s |
| Cilium | eBPF native + L7 | High-performance K8s |
| Istio mTLS | Envoy sidecar + SPIFFE | Service-to-service auth |
| Zero Trust | Never trust, always verify | Full east-west control |
| Blast radius | 1/N segments on breach | Risk reduction metric |
