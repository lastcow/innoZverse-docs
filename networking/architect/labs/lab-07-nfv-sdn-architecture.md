# Lab 07: NFV & SDN Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

NFV and SDN decouple network functions from hardware, enabling software-defined infrastructure. This lab covers the ETSI NFV framework, Open vSwitch operations, SDN controllers, and the P4 language concept.

---

## Objectives
- Understand ETSI NFV framework (NFVI/VNF/MANO)
- Design VNF service chaining
- Configure Open vSwitch (OVS) with flow tables
- Compare SDN controllers (OpenDaylight/ONOS/Faucet)
- Understand OpenFlow protocol mechanics
- Explore P4 language for programmable data planes

---

## Step 1: ETSI NFV Framework

NFV replaces purpose-built hardware appliances with software running on commodity servers.

**Three layers:**
```
┌─────────────────────────────────────────┐
│              MANO                        │
│  NFV Orchestrator │ VNF Manager │ VIM   │
├─────────────────────────────────────────┤
│              VNF Layer                  │
│  [vFirewall] [vRouter] [vLB] [vIDS]    │
├─────────────────────────────────────────┤
│              NFVI                       │
│  Compute │ Storage │ Network (OVS)      │
│  (x86 servers, COTS hardware)          │
└─────────────────────────────────────────┘
```

**NFVI (Infrastructure):**
- Commodity x86 servers (Intel/AMD)
- COTS (Commercial Off-The-Shelf) networking
- KVM/QEMU hypervisor or containers

**VNF (Virtual Network Function):**
- vFirewall (Palo Alto VM-Series, Fortinet FortiGate-VM)
- vRouter (Cisco CSR 1000V, Juniper vMX)
- vLoadBalancer (F5 BIG-IP VE)
- vIDS/IPS (Snort, Suricata as VNF)

**MANO (Management & Orchestration):**
- **NFV Orchestrator:** lifecycle management of network services
- **VNF Manager:** VNF instantiation, scaling, termination
- **VIM (Virtualized Infrastructure Manager):** OpenStack or VMware managing NFVI

---

## Step 2: VNF Lifecycle & Service Chaining

**VNF Lifecycle:**
```
Onboard → Instantiate → Configure → Scale Out/In → Heal → Terminate
```

**Service Function Chaining (SFC):**
Route traffic through ordered sequence of VNFs:
```
Client → vFirewall → vIDS → vLoadBalancer → Backend Servers
         (VNF 1)    (VNF 2)    (VNF 3)
```

**NSH (Network Service Header):**
SFC uses NSH to encode service path and index:
```
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Ver|O|U|    TTL    |   Length  |U|U|U|U|MD Type|  Next Proto   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Service Path Identifier (SPI)        | Service Index |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

---

## Step 3: SDN — Control/Data Plane Separation

Traditional networking: control plane and data plane are tightly coupled in each device.

**SDN architecture:**
```
┌─────────────────────────────────────────┐
│          SDN Applications               │
│  (Traffic Engineering, Load Balancing)  │
├─────────────────────────────────────────┤
│          SDN Controller                 │  ← Control Plane (centralized)
│  (OpenDaylight / ONOS / Faucet)        │
├─────────────────────────────────────────┤
│     OpenFlow / Southbound API           │  ← Protocol
├─────────────────────────────────────────┤
│       Network Devices (OVS, HW)         │  ← Data Plane (distributed)
└─────────────────────────────────────────┘
```

**OpenFlow:** Protocol between controller and data plane
- Controller installs flow rules in switch flow tables
- Switch matches packets against flow tables, applies actions
- Actions: forward, drop, modify, send to controller

**OpenFlow pipeline:**
```
Packet IN → Table 0 → Table 1 → Table N → Action Set → Output
                         ↓
                    No match → Table-miss (send to controller or drop)
```

> 💡 **When SDN makes sense:** Large-scale data centers (Google Jupiter, Facebook Fabric), carrier networks (AT&T SDN transformation), academic research networks. SDN overhead can hurt performance in small deployments.

---

## Step 4: Open vSwitch (OVS)

OVS is the de facto software switch for virtual environments (KVM, OpenStack, Kubernetes).

**OVS architecture:**
```
OVS Architecture:
  ovs-vsctl   → Management (add bridges, ports)
  ovs-ofctl   → OpenFlow flow management
  ovsdb-server → Configuration database
  ovs-vswitchd → Fast-path packet forwarding
```

**Basic OVS configuration:**
```bash
# Start OVS
service openvswitch-switch start

# Create bridge
ovs-vsctl add-br br0

# Add physical and virtual ports
ovs-vsctl add-port br0 eth1              # Physical uplink
ovs-vsctl add-port br0 veth0            # VM veth pair

# Show configuration
ovs-vsctl show

# Add VLAN tagging
ovs-vsctl add-port br0 eth1 tag=10      # Access port VLAN 10
ovs-vsctl add-port br0 eth2 trunks=10,20,30  # Trunk port

# Set OpenFlow controller
ovs-vsctl set-controller br0 tcp:192.168.1.100:6633
```

**Flow table manipulation:**
```bash
# Add flow: forward TCP port 80 to specific port
ovs-ofctl add-flow br0 "priority=100,tcp,tp_dst=80,actions=output:2"

# Add flow: send ICMP to controller
ovs-ofctl add-flow br0 "priority=50,icmp,actions=controller"

# Drop unknown traffic
ovs-ofctl add-flow br0 "priority=0,actions=drop"

# Dump flows
ovs-ofctl dump-flows br0

# Show port stats
ovs-ofctl dump-ports br0
```

---

## Step 5: SDN Controllers

**OpenDaylight (ODL):**
- Most feature-rich, enterprise-grade
- Java-based, runs on standard server
- Plugins: OpenFlow, BGP, NETCONF, YANG
- Used by AT&T, Ericsson, Huawei

**ONOS (Open Network Operating System):**
- High-performance, carrier-grade
- Distributed architecture (cluster of 3+ nodes)
- Intent-based networking API
- Used by China Mobile, Comcast, SK Telecom

**Faucet:**
- Simple, production-tested OpenFlow controller
- Python-based, easy to deploy
- Excellent for enterprise campus SDN
- Supports VLAN, STP, ACLs via YAML config

**Faucet configuration example:**
```yaml
# faucet.yaml
vlans:
  office:
    vid: 100
    description: "Office VLAN"
  iot:
    vid: 200
    description: "IoT devices"

dps:
  sw1:
    dp_id: 0x1
    interfaces:
      1:
        native_vlan: office
      2:
        native_vlan: iot
      24:
        tagged_vlans: [office, iot]  # Uplink trunk
```

---

## Step 6: P4 — Programmable Data Planes

P4 (Programming Protocol-independent Packet Processors) allows programming the forwarding behavior of network devices.

**P4 abstracts:**
- Parser: how to parse incoming packets
- Match-Action tables: how to process headers
- Deparser: how to reconstruct packets

**Simple P4 example (IPv4 forwarding):**
```p4
// Define packet headers
header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}
header ipv4_t {
    bit<4>  version;
    bit<8>  diffserv;
    bit<32> srcAddr;
    bit<32> dstAddr;
    bit<8>  protocol;
}

// Match-action table
table ipv4_lpm {
    key = { hdr.ipv4.dstAddr: lpm; }
    actions = { ipv4_forward; drop; }
    size = 1024;
}

// Action: forward packet
action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
    standard_metadata.egress_spec = port;
    hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
    hdr.ethernet.dstAddr = dstAddr;
    hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
}
```

**P4 use cases:** INT (In-band Network Telemetry), custom load balancing, new protocol support without hardware changes.

---

## Step 7: Verification — OVS Real Commands

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq openvswitch-switch &&
service openvswitch-switch start 2>/dev/null || true
ovs-vsctl --no-wait init
ovs-vsctl --no-wait add-br br-lab
ovs-vsctl --no-wait show
echo 'OVS version:'
ovs-vsctl --version | head -1"
```

📸 **Verified Output:**
```
390c0de5-30af-4140-9b07-541db75c0ded
    Bridge br-lab
        Port br-lab
            Interface br-lab
                type: internal
    ovs_version: "2.17.9"
OVS version:
ovs-vsctl (Open vSwitch) 2.17.9
```

**Add flow rules:**
```bash
# After bridge created:
ovs-ofctl add-flow br-lab "priority=100,ip,nw_dst=10.0.0.0/8,actions=output:1"
ovs-ofctl add-flow br-lab "priority=0,actions=drop"
ovs-ofctl dump-flows br-lab
```
```
NXST_FLOW reply:
 cookie=0x0, priority=100,ip,nw_dst=10.0.0.0/8 actions=output:1
 cookie=0x0, priority=0 actions=drop
```

---

## Step 8: Capstone — NFV Service Chain Design

**Scenario:** Telco wants to replace hardware firewalls, IDS, and load balancers with NFV service chain.

**Current state:** 3 hardware appliances per PoP × 50 PoPs = 150 devices

**Target state with NFV:**
```
Traffic Flow:
  Internet → [vFW] → [vIDS] → [vLB] → Application Servers

VNF stack per PoP (on 2 × COTS servers):
  vFirewall:   2 instances (active-standby), 4 vCPU, 8GB RAM
  vIDS:        1 instance, 4 vCPU, 16GB RAM (memory for signatures)
  vLB:         2 instances (active-active), 2 vCPU, 4GB RAM

MANO platform: OpenStack + Tacker (OpenStack NFV orchestrator)
Controller: ONOS (for service chaining via NSH)
Underlay: OVS with DPDK (Data Plane Development Kit) for line-rate performance

Cost analysis:
  Hardware per PoP: $50K → $8K (COTS server)
  Provisioning time: 2 weeks → 2 hours (automated)
  Scale: vertical hardware → horizontal software scaling
```

**Service chain definition (Tacker):**
```yaml
tosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0
topology_template:
  node_templates:
    VNF1:
      type: tosca.nodes.nfv.VNF
      properties:
        descriptor_id: vfirewall-1.0
        flavour_id: simple
    VNF2:
      type: tosca.nodes.nfv.VNF
      properties:
        descriptor_id: vids-1.0
    VNF3:
      type: tosca.nodes.nfv.VNF
      properties:
        descriptor_id: vlb-1.0
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| NFVI | Commodity hardware running VNFs |
| VNF | Software-based network functions (vFW, vLB, vRouter) |
| MANO | Orchestrates VNF lifecycle |
| Service chaining | Ordered sequence of VNFs per traffic class |
| SDN/OpenFlow | Controller programs flow tables in switches |
| OVS | Software switch for KVM/OpenStack/containers |
| P4 | Programs forwarding behavior at data plane level |

**Next:** [Lab 08: Load Balancing at Scale →](lab-08-load-balancing-scale.md)
