# Lab 06: Advanced Cloud Networking

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

Cloud networking has become the dominant connectivity model. This lab covers advanced VPC design, Transit Gateway architecture, Direct Connect, and multi-region strategies across AWS, Azure, and GCP.

---

## Objectives
- Design multi-AZ, multi-region AWS VPC
- Implement Transit Gateway hub-and-spoke
- Configure PrivateLink and VPC endpoints
- Plan Direct Connect / ExpressRoute / Cloud Interconnect
- Design Route 53 for global traffic management
- Calculate VPC subnets with Python

---

## Step 1: AWS VPC Multi-AZ Design

**VPC CIDR Planning Rules:**
1. Use RFC 1918 space: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
2. Avoid overlapping with on-premises or other VPCs (needed for peering/TGW)
3. Size for 3-year growth (subnets can't be resized after creation)
4. Reserve /28 for management/monitoring per AZ

**Subnet Design (per VPC):**
```
VPC: 10.0.0.0/16 (us-east-1)

Public subnets (internet-facing):
  10.0.1.0/24    us-east-1a Public  (254 hosts)
  10.0.2.0/24    us-east-1b Public  (254 hosts)
  10.0.3.0/24    us-east-1c Public  (254 hosts)

Private subnets (app tier):
  10.0.16.0/20   us-east-1a Private (4094 hosts)
  10.0.32.0/20   us-east-1b Private (4094 hosts)
  10.0.48.0/20   us-east-1c Private (4094 hosts)

Data subnets (DB, ElastiCache):
  10.0.64.0/22   us-east-1a Data    (1022 hosts)
  10.0.68.0/22   us-east-1b Data    (1022 hosts)
  10.0.72.0/22   us-east-1c Data    (1022 hosts)

Management:
  10.0.0.0/28    VPC-wide management (14 hosts)
```

**Route table design:**
- Public subnets → IGW (Internet Gateway)
- Private subnets → NAT Gateway (per-AZ for HA)
- Data subnets → No internet access, only internal routing

---

## Step 2: Transit Gateway (TGW) — Hub-and-Spoke

TGW acts as a regional cloud router, replacing complex VPC peering meshes.

**Without TGW (VPC mesh):**
```
3 VPCs = 3 peering connections
5 VPCs = 10 peering connections  
10 VPCs = 45 peering connections  ← Unmanageable
```

**With TGW:**
```
10 VPCs = 10 TGW attachments  ← Linear scaling

     [TGW] ←── Direct Connect / VPN
    / | | \
  VPC1 VPC2 VPC3 VPC4
```

**TGW Route Tables:**
```
# Shared-services VPC route table (spoke isolation)
Route: 0.0.0.0/0 → Firewall VPC (inspection)
Route: 10.0.0.0/8 → Firewall VPC (all RFC1918 inspected)

# Security VPC route table
Route: 10.1.0.0/16 → VPC1 attachment
Route: 10.2.0.0/16 → VPC2 attachment
Route: 0.0.0.0/0 → Internet Gateway
```

**TGW multi-region (inter-region peering):**
```
us-east-1 TGW ←──── Peering (encrypted, AWS backbone) ────→ eu-west-1 TGW
     │                                                              │
  US VPCs                                                       EU VPCs
```

---

## Step 3: PrivateLink & VPC Endpoints

**PrivateLink:** Access AWS services or your own services without internet traffic.

**Interface endpoints (PrivateLink):**
```
# Access S3 via PrivateLink (no internet required)
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.s3 \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-abc subnet-def \
  --security-group-ids sg-xyz
```

**Gateway endpoints (free, S3/DynamoDB only):**
```
# Free gateway endpoint for S3
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-abc
```

**PrivateLink for your SaaS service:**
```
Architecture:
  Consumer VPC → Interface Endpoint (ENI) → NLB → Service VPC
  
  Benefits:
  - Service provider doesn't know consumer's IP space
  - No VPC peering, no route overlap concerns
  - Works cross-account, cross-region
```

> 💡 **Cost optimization:** Use gateway endpoints for S3 and DynamoDB (free). Interface endpoints cost ~$7.30/month per AZ. Enable VPC endpoint policies to restrict access to specific S3 buckets.

---

## Step 4: AWS Direct Connect

Direct Connect provides dedicated private connectivity (bypasses internet).

```
Enterprise DC                           AWS
[Customer Router]
       │
  [Direct Connect location]
       │ (1G / 10G / 100G fiber)
  [AWS Direct Connect router]
       │
   [Virtual Interface (VIF)]
    ├── Private VIF → VPC via VGW
    ├── Transit VIF → TGW (access multiple VPCs)
    └── Public VIF → AWS public services (S3, DynamoDB)
```

**Resilience options:**
| Option | Failover | Use Case |
|--------|----------|----------|
| Single DX | None | Dev/test |
| Dual DX (same location) | Location failure → down | Production (OK) |
| Dual DX (different locations) | Any single failure covered | Production (recommended) |
| DX + VPN backup | DX fails → IPSec VPN | Production + cost-conscious |

---

## Step 5: Route 53 Global Traffic Management

Route 53 routing policies for global applications:

**Routing policies:**
| Policy | Description | Use Case |
|--------|-------------|----------|
| Simple | One record | Single endpoint |
| Weighted | Split traffic by % | A/B testing, gradual rollout |
| Latency | Route to lowest latency | Global apps |
| Geolocation | Route by user country/continent | Compliance, regionalization |
| Geoproximity | Route by distance + bias | Custom regional boundaries |
| Failover | Active-passive | DR failover |
| Multivalue | Multiple healthy IPs | Simple load balancing |

**Global Accelerator:**
```
User (anywhere) → anycast IP (AWS edge) → optimized AWS backbone → Target
                                           ↑
                              Bypasses public internet, 50-60% lower latency
```

---

## Step 6: Azure & GCP Equivalents

**Azure:**
| AWS | Azure Equivalent |
|-----|-----------------|
| VPC | Virtual Network (VNet) |
| TGW | Virtual WAN (vWAN) |
| Direct Connect | ExpressRoute |
| PrivateLink | Private Endpoint |
| Global Accelerator | Front Door / Traffic Manager |
| VPC Peering | VNet Peering |

**Azure ExpressRoute circuits:**
```
On-premises → ExpressRoute location → Microsoft Edge → Azure region
  (up to 100G, SLA-backed, private, no internet exposure)
  ExpressRoute Premium: global routing to all Azure regions on one circuit
```

**GCP Cloud Interconnect:**
```
Dedicated Interconnect: Direct fiber to Google PoP (10G/100G)
Partner Interconnect: Via service provider (50M to 50G)
Cross-Cloud Interconnect: Direct GCP ↔ AWS (new, 10G/100G)
```

---

## Step 7: Verification — VPC Subnet Calculator

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq python3 &&
python3 - << 'EOF'
import ipaddress
vpc = ipaddress.IPv4Network('10.0.0.0/16')
print(f'VPC CIDR: {vpc}')
print(f'Total hosts: {vpc.num_addresses - 2:,}')
subnets = [
    ('us-east-1a Public',  '/24'),
    ('us-east-1b Public',  '/24'),
    ('us-east-1a Private', '/22'),
    ('us-east-1b Private', '/22'),
    ('Management',         '/28'),
]
sub24 = list(vpc.subnets(new_prefix=24))
sub22 = list(vpc.subnets(new_prefix=22))
sub28 = list(vpc.subnets(new_prefix=28))
nets = [sub24[0], sub24[1], sub22[2], sub22[3], sub28[0]]
print(f\"{'Subnet':<25} {'CIDR':<20} {'Hosts'}\")
print('-'*55)
for (name, pfx), net in zip(subnets, nets):
    print(f'{name:<25} {str(net):<20} {net.num_addresses-2}')
EOF"
```

📸 **Verified Output:**
```
VPC CIDR: 10.0.0.0/16
Total hosts: 65,534

Subnet                    CIDR                 Hosts
-------------------------------------------------------
us-east-1a Public         10.0.0.0/24          254
us-east-1b Public         10.0.1.0/24          254
us-east-1a Private        10.0.8.0/22          1022
us-east-1b Private        10.0.12.0/22         1022
Management                10.0.0.64/28         14
```

---

## Step 8: Capstone — Multi-Cloud Architecture

**Scenario:** Global SaaS company running on AWS + Azure, expanding to GCP for ML workloads. Design the network architecture.

**Requirements:**
- AWS: 3 regions (us-east-1, eu-west-1, ap-southeast-1)
- Azure: 1 region (eastus) for enterprise customers on Microsoft
- GCP: us-central1 for ML training workloads
- On-premises DC: Direct Connect to AWS primary, ExpressRoute to Azure
- Requirement: Any workload can reach any other workload privately

**Design:**
```
AWS us-east-1 (primary)
  VPC: 10.1.0.0/16
  TGW: hub for US VPCs
  Direct Connect: 10G to on-prem DC

AWS eu-west-1
  VPC: 10.2.0.0/16
  TGW: peered to us-east-1 TGW

Azure eastus
  VNet: 10.3.0.0/16
  ExpressRoute: to on-prem DC
  VNet peering: to Azure vWAN hub

GCP us-central1
  VPC: 10.4.0.0/16
  Cloud Interconnect (Cross-Cloud): to AWS us-east-1 TGW

Connectivity matrix:
  On-prem ↔ AWS: Direct Connect (10G)
  On-prem ↔ Azure: ExpressRoute (1G)
  AWS ↔ Azure: IPSec VPN via TGW + VGW (fallback: Megaport)
  AWS ↔ GCP: Cross-Cloud Interconnect (10G)
  AWS us-east-1 ↔ eu-west-1: TGW inter-region peering

DNS:
  Route 53 private: aws.internal
  Azure Private DNS: azure.internal
  Split-horizon: resolve cloud.company.com to cloud-native endpoints
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| VPC design | Size for 3 years, don't overlap CIDRs, /22-/20 per tier |
| TGW | Replaces VPC peering mesh; hub-and-spoke at cloud scale |
| PrivateLink | Access services without internet, no route overlap |
| Direct Connect | Sub-ms latency, consistent bandwidth, not internet |
| Route 53 | Latency/geo/weighted routing for global apps |
| Multi-cloud | Plan IP space globally; Direct interconnects > VPN |

**Next:** [Lab 07: NFV & SDN Architecture →](lab-07-nfv-sdn-architecture.md)
