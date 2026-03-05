# 🏛️ Networking Architect — Lab Index

**Level:** Architect | **Labs:** 20 | **Time:** ~17 hours total

Advanced networking labs for senior engineers and architects. Covers enterprise design patterns, data center fabrics, cloud-scale networking, security architecture, and compliance auditing.

**Prerequisites:** Networking Fundamentals + Protocols + Network Security tracks recommended.

---

## Lab Index

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 01 | [Enterprise Network Design](labs/lab-01-enterprise-network-design.md) | Campus hierarchy, redundancy, QoS, OSPF/BGP | 50 min |
| 02 | [SD-WAN Architecture](labs/lab-02-sdwan-architecture.md) | Overlay/underlay, vEdge, policies, ZTP | 50 min |
| 03 | [Network Automation (Ansible)](labs/lab-03-network-automation-ansible.md) | Playbooks, NAPALM, Netconf, IaC | 50 min |
| 04 | [BGP Enterprise Design](labs/lab-04-bgp-enterprise-design.md) | eBGP/iBGP, route reflectors, communities | 50 min |
| 05 | [MPLS VPN Architecture](labs/lab-05-mpls-vpn-architecture.md) | L3VPN, VRF, PE/CE, route targets | 50 min |
| 06 | [Cloud Networking (Advanced)](labs/lab-06-cloud-networking-advanced.md) | VPC peering, Transit GW, private link | 50 min |
| 07 | [NFV & SDN Architecture](labs/lab-07-nfv-sdn-architecture.md) | OpenFlow, ONOS, VNF, service chaining | 50 min |
| 08 | [Load Balancing at Scale](labs/lab-08-load-balancing-scale.md) | L4/L7 LB, DSR, ECMP, anycast | 50 min |
| 09 | [Network Observability](labs/lab-09-network-observability.md) | NetFlow, IPFIX, telemetry, dashboards | 50 min |
| 10 | [IPv6 Migration Planning](labs/lab-10-ipv6-migration-planning.md) | Dual-stack, 6to4, NAT64, transition | 50 min |
| 11 | [DNS at Scale](labs/lab-11-dns-at-scale.md) | Anycast DNS, DNSSEC, split-horizon, DoH | 50 min |
| 12 | [CDN Architecture](labs/lab-12-cdn-architecture.md) | PoP design, cache hierarchy, Anycast | 50 min |
| 13 | [WAN Optimisation](labs/lab-13-wan-optimization.md) | WAAS, TCP optimisation, QoS, dedup | 50 min |
| 14 | [Network Disaster Recovery](labs/lab-14-network-disaster-recovery.md) | BCP, RTO/RPO, failover, geo-redundancy | 50 min |
| 15 | [Campus Network Design](labs/lab-15-campus-network-design.md) | Wi-Fi 6, 802.1X, NAC, PoE++, WPA3-Ent | 50 min |
| 16 | [Data Center Network](labs/lab-16-data-center-network.md) | CLOS fabric, EVPN-VXLAN, BGP underlay | 50 min |
| 17 | [Micro-Segmentation](labs/lab-17-micro-segmentation.md) | Namespaces, NetworkPolicy, Cilium, mTLS | 50 min |
| 18 | [Network Compliance Auditing](labs/lab-18-network-compliance-auditing.md) | CIS Benchmarks, PCI DSS, automated audit | 50 min |
| 19 | [Multi-Cloud Networking](labs/lab-19-multicloud-networking.md) | TGW, vWAN, NCC, SD-WAN, latency opt. | 50 min |
| 20 | [Capstone: Architecture Audit](labs/lab-20-capstone-network-architecture-audit.md) | Full audit, redesign, migration, compliance | 50 min |

---

## Learning Path

```
Labs 01–05: Enterprise Routing & WAN
    ↓
Labs 06–09: Cloud, SDN & Observability
    ↓
Labs 10–14: Scale, Resilience & Specialised Protocols
    ↓
Labs 15–17: Modern DC & Campus Architecture (NEW)
    ↓
Labs 18–19: Security Compliance & Multi-Cloud (NEW)
    ↓
Lab 20: Capstone — Full Architecture Audit (NEW)
```

## Key Technologies Covered

| Domain | Technologies |
|--------|-------------|
| Wireless | 802.11ax (Wi-Fi 6/6E), WPA3-Enterprise, 802.1X EAP-TLS |
| DC Fabric | CLOS topology, EVPN-VXLAN, BGP EVPN (RFC 7432), ECMP |
| Segmentation | Linux namespaces, Calico, Cilium, Istio mTLS, SPIFFE |
| Compliance | CIS Benchmarks L1/L2, PCI DSS v4.0, NIST SP 800-41 |
| Multi-Cloud | AWS TGW, Azure vWAN, GCP NCC, Direct Connect, ExpressRoute |
| Automation | Ansible, Python3 (ipaddress, json, socket) |

## Docker Quick Reference

All labs verified in Docker:
```bash
# Standard labs (network concepts)
docker run -it --rm ubuntu:22.04 bash

# Labs requiring kernel network features (16, 17)
docker run -it --rm --privileged ubuntu:22.04 bash

# Install common tools inside container
apt-get update -qq && apt-get install -y -qq iproute2 iptables iputils-ping python3
```
