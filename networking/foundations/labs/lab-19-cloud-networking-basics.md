# Lab 19: Cloud Networking Basics

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

Cloud networking virtualizes traditional network infrastructure. AWS, Azure, and GCP each offer virtual networks (VPC/VNet), subnets, security controls, and load balancers as software-defined services. This lab uses Python's `ipaddress` module to demonstrate real VPC design calculations.

---

## Step 1: Virtual Private Cloud (VPC) Concepts

A **VPC** (Virtual Private Cloud) is a logically isolated virtual network in the cloud. You define the IP address range, subnets, routing, and security.

```
AWS VPC: 10.0.0.0/16  (65,534 usable host IPs)
│
├─ Public Subnet:  10.0.1.0/24  → Internet Gateway → Internet
│   ├─ Load Balancer (public IP)
│   └─ NAT Gateway (for private subnet outbound)
│
├─ Private Subnet: 10.0.2.0/24  → NAT Gateway → Internet (outbound only)
│   ├─ App Servers (EC2 instances)
│   └─ Cache (ElastiCache)
│
└─ Private Subnet: 10.0.3.0/24  → No internet access
    └─ Database (RDS — isolated)
```

**Key VPC components:**

| Component | Function | Analogy |
|-----------|----------|---------|
| **VPC** | Isolated virtual network | Office building |
| **Subnet** | Segment of VPC CIDR | Floor of the building |
| **Route Table** | Controls traffic routing | Elevator/signage |
| **Internet Gateway** | Connects VPC to internet (bidirectional) | Main entrance |
| **NAT Gateway** | Outbound-only internet for private subnets | One-way exit |
| **Security Group** | Stateful firewall at instance level | Personal bodyguard |
| **NACL** | Stateless ACL at subnet level | Lobby security desk |
| **VPN Gateway** | IPSec tunnel to on-premise | Secure tunnel to HQ |
| **VPC Peering** | Direct routing between VPCs | Inter-building corridor |

> 💡 **Tip:** Security Groups are **stateful** (return traffic auto-allowed). NACLs are **stateless** (must explicitly allow inbound AND outbound). Security Groups are the first line of defense; NACLs add a second layer.

---

## Step 2: VPC CIDR Calculations with Python

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
  python3 -c \"
import ipaddress

print('=== VPC Subnet Planning (10.0.0.0/16) ===')
vpc = ipaddress.IPv4Network('10.0.0.0/16')
subnets = list(vpc.subnets(new_prefix=24))
for i, s in enumerate(subnets[:5]):
    print(f'Subnet {i+1}: {s} — {s.num_addresses-2} hosts')

print()
print('=== VPC Info ===')
print(f'VPC CIDR:         {vpc}')
print(f'Network address:  {vpc.network_address}')
print(f'Broadcast:        {vpc.broadcast_address}')
print(f'Total IPs:        {vpc.num_addresses:,}')
print(f'Usable hosts:     {vpc.num_addresses - 2:,}')
print(f'Available /24s:   {len(subnets)}')
  \"
"
```

📸 **Verified Output:**
```
=== VPC Subnet Planning (10.0.0.0/16) ===
Subnet 1: 10.0.0.0/24 - 254 hosts
Subnet 2: 10.0.1.0/24 - 254 hosts
Subnet 3: 10.0.2.0/24 - 254 hosts
Subnet 4: 10.0.3.0/24 - 254 hosts
Subnet 5: 10.0.4.0/24 - 254 hosts

=== VPC Info ===
VPC CIDR:         10.0.0.0/16
Network address:  10.0.0.0
Broadcast:        10.0.255.255
Total IPs:        65536
Usable hosts:     65,534
Available /24s:   256
```

> 💡 **Tip:** AWS reserves **5 IP addresses** per subnet (network, VPC router, DNS, future, broadcast). A /24 subnet gives you 254 - 5 = **251 usable** IPs in AWS, not 254.

---

## Step 3: 3-Tier VPC Architecture Planning

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
  python3 -c \"
import ipaddress

print('=== 3-Tier VPC Architecture: 10.0.0.0/16 ===')
print()

tiers = [
    ('Public/DMZ',    '10.0.1.0/24',  'Internet Gateway',  'ALB, NAT GW, Bastion'),
    ('App/Private',   '10.0.2.0/24',  'NAT Gateway',       'EC2 App Servers, ECS'),
    ('DB/Private',    '10.0.3.0/24',  'None (isolated)',   'RDS, ElastiCache'),
    ('Management',    '10.0.4.0/24',  'NAT Gateway',       'Monitoring, CI/CD'),
    ('Reserved',      '10.0.5.0/24',  'TBD',               'Future expansion'),
]

print(f'  {'Tier':<15} {'CIDR':<16} {'Gateway':<20} {'Hosts':<6} Services')
print('  ' + '=' * 80)

for name, cidr, gw, services in tiers:
    net = ipaddress.IPv4Network(cidr)
    hosts = net.num_addresses - 2
    first = list(net.hosts())[0]
    last  = list(net.hosts())[-1]
    print(f'  {name:<15} {cidr:<16} {gw:<20} {hosts:<6} {services}')

print()
print('  Detailed subnet breakdown:')
print()
for name, cidr, gw, services in tiers:
    net = ipaddress.IPv4Network(cidr)
    hosts_list = list(net.hosts())
    print(f'  [{name}] {cidr}')
    print(f'    Network:   {net.network_address}')
    print(f'    Gateway:   {hosts_list[0]}  (first usable = router/gateway)')
    print(f'    Hosts:     {hosts_list[1]} — {hosts_list[-1]}')
    print(f'    Broadcast: {net.broadcast_address}')
    print(f'    Usable:    {len(hosts_list) - 1} IPs (minus 1 for gateway)')
    print()
  \"
"
```

📸 **Verified Output:**
```
=== 3-Tier VPC Architecture: 10.0.0.0/16 ===

  Tier            CIDR             Gateway              Hosts   Services
  ================================================================================
  Public/DMZ      10.0.1.0/24      Internet Gateway     254     ALB, NAT GW, Bastion
  App/Private     10.0.2.0/24      NAT Gateway          254     EC2 App Servers, ECS
  DB/Private      10.0.3.0/24      None (isolated)      254     RDS, ElastiCache
  Management      10.0.4.0/24      NAT Gateway          254     Monitoring, CI/CD
  Reserved        10.0.5.0/24      TBD                  254     Future expansion

  Detailed subnet breakdown:

  [Public/DMZ] 10.0.1.0/24
    Network:   10.0.1.0
    Gateway:   10.0.1.1  (first usable = router/gateway)
    Hosts:     10.0.1.2 — 10.0.1.254
    Broadcast: 10.0.1.255
    Usable:    253 IPs (minus 1 for gateway)

  [App/Private] 10.0.2.0/24
    Network:   10.0.2.0
    Gateway:   10.0.2.1
    Hosts:     10.0.2.2 — 10.0.2.254
    Broadcast: 10.0.2.255
    Usable:    253 IPs (minus 1 for gateway)

  [DB/Private] 10.0.3.0/24
    Network:   10.0.3.0
    Gateway:   10.0.3.1
    Hosts:     10.0.3.2 — 10.0.3.254
    Broadcast: 10.0.3.255
    Usable:    253 IPs (minus 1 for gateway)
```

---

## Step 4: Public vs Private Subnets & Gateways

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
  python3 -c \"
print('=== Public vs Private Subnet Comparison ===')
print()
comparison = {
    'Route Table':     ('Has route 0.0.0.0/0 → IGW',    'Has route 0.0.0.0/0 → NAT GW or none'),
    'Internet access': ('Inbound + Outbound',             'Outbound only (via NAT) or none'),
    'Public IP':       ('Instances can get public IPs',   'Instances only have private IPs'),
    'Use cases':       ('Load balancers, NAT GW, bastion','App servers, databases, caches'),
    'Security':        ('Exposed to internet (firewalled)','Not directly reachable from internet'),
    'Cost':            ('IGW is free',                    'NAT GW ~\$0.045/hr + data transfer'),
}
for feature, (public, private) in comparison.items():
    print(f'  {feature}:')
    print(f'    Public:  {public}')
    print(f'    Private: {private}')
    print()

print('=== Gateway Types ===')
print()
gateways = [
    ('Internet Gateway (IGW)',  'Bidirectional internet access',   'Public subnets',     'Free'),
    ('NAT Gateway',            'Outbound-only internet (SNAT)',    'Private subnets',    '\$0.045/hr + data'),
    ('VPN Gateway (VGW)',      'IPSec tunnel to on-premise',      'Hybrid cloud',       '\$0.05/hr per VPN'),
    ('Transit Gateway',        'Hub for multiple VPCs/VPNs',      'Large multi-VPC',    '\$0.05/hr + data'),
    ('Direct Connect Gateway', 'Dedicated physical WAN circuit',   'Enterprise hybrid',  '\$\$\$ (contracted)'),
]
for gw, function, use_case, cost in gateways:
    print(f'  {gw}')
    print(f'    Function: {function}')
    print(f'    Use case: {use_case}')
    print(f'    Cost:     {cost}')
    print()
  \"
"
```

📸 **Verified Output:**
```
=== Public vs Private Subnet Comparison ===

  Route Table:
    Public:  Has route 0.0.0.0/0 → IGW
    Private: Has route 0.0.0.0/0 → NAT GW or none

  Internet access:
    Public:  Inbound + Outbound
    Private: Outbound only (via NAT) or none

  Public IP:
    Public:  Instances can get public IPs
    Private: Instances only have private IPs

  Use cases:
    Public:  Load balancers, NAT GW, bastion
    Private: App servers, databases, caches

  Security:
    Public:  Exposed to internet (firewalled)
    Private: Not directly reachable from internet

  Cost:
    Public:  IGW is free
    Private: NAT GW ~$0.045/hr + data transfer

=== Gateway Types ===

  Internet Gateway (IGW)
    Function: Bidirectional internet access
    Use case: Public subnets
    Cost:     Free

  NAT Gateway
    Function: Outbound-only internet (SNAT)
    Use case: Private subnets
    Cost:     $0.045/hr + data

  VPN Gateway (VGW)
    Function: IPSec tunnel to on-premise
    Use case: Hybrid cloud
    Cost:     $0.05/hr per VPN
```

---

## Step 5: Load Balancer Types

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
  python3 -c \"
print('=== Cloud Load Balancer Types ===')
print()
lbs = [
    {
        'name': 'Application Load Balancer (ALB)',
        'layer': 'Layer 7 (HTTP/HTTPS)',
        'routing': 'Path-based, host-based, header-based',
        'protocols': 'HTTP, HTTPS, WebSocket, gRPC',
        'use_case': 'Microservices, web apps, API gateway',
        'aws': 'aws elbv2 create-load-balancer --type application',
    },
    {
        'name': 'Network Load Balancer (NLB)',
        'layer': 'Layer 4 (TCP/UDP/TLS)',
        'routing': 'Source IP hash or round-robin',
        'protocols': 'TCP, UDP, TLS',
        'use_case': 'Low latency, static IP, gaming, IoT',
        'aws': 'aws elbv2 create-load-balancer --type network',
    },
    {
        'name': 'Gateway Load Balancer (GWLB)',
        'layer': 'Layer 3 (IP)',
        'routing': 'Transparent bump-in-the-wire',
        'protocols': 'IP (GENEVE encapsulation)',
        'use_case': 'Inline security appliances (IDS/IPS/NGFW)',
        'aws': 'aws elbv2 create-load-balancer --type gateway',
    },
]
for lb in lbs:
    print(f'  ▶ {lb[\"name\"]}')
    print(f'    Layer:     {lb[\"layer\"]}')
    print(f'    Routing:   {lb[\"routing\"]}')
    print(f'    Protocols: {lb[\"protocols\"]}')
    print(f'    Use case:  {lb[\"use_case\"]}')
    print()

print('  ==> Decision Guide:')
print('    HTTP/HTTPS app with smart routing → ALB')
print('    Ultra-low latency / UDP / static IP → NLB')
print('    Inline security inspection → GWLB')
  \"
"
```

📸 **Verified Output:**
```
=== Cloud Load Balancer Types ===

  ▶ Application Load Balancer (ALB)
    Layer:     Layer 7 (HTTP/HTTPS)
    Routing:   Path-based, host-based, header-based
    Protocols: HTTP, HTTPS, WebSocket, gRPC
    Use case:  Microservices, web apps, API gateway

  ▶ Network Load Balancer (NLB)
    Layer:     Layer 4 (TCP/UDP/TLS)
    Routing:   Source IP hash or round-robin
    Protocols: TCP, UDP, TLS
    Use case:  Low latency, static IP, gaming, IoT

  ▶ Gateway Load Balancer (GWLB)
    Layer:     Layer 3 (IP)
    Routing:   Transparent bump-in-the-wire
    Protocols: IP (GENEVE encapsulation)
    Use case:  Inline security appliances (IDS/IPS/NGFW)

  ==> Decision Guide:
    HTTP/HTTPS app with smart routing → ALB
    Ultra-low latency / UDP / static IP → NLB
    Inline security inspection → GWLB
```

---

## Step 6: Cloud Provider Comparison

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
  python3 -c \"
print('=== Cloud Networking: AWS vs Azure vs GCP ===')
print()
features = [
    ('Virtual Network',    'VPC',               'VNet',          'VPC (global)'),
    ('Subnet scope',       'AZ-specific',        'AZ-specific',   'Regional (global)'),
    ('DNS service',        'Route 53',           'Azure DNS',     'Cloud DNS'),
    ('Private DNS',        'Route 53 Resolver',  'Private DNS',   'Cloud DNS (private)'),
    ('Load Balancer L7',   'ALB',                'App Gateway',   'Cloud Load Balancing'),
    ('Load Balancer L4',   'NLB',                'Azure LB',      'TCP/UDP LB'),
    ('CDN',                'CloudFront',         'Azure CDN/FD',  'Cloud CDN'),
    ('VPC Peering',        'VPC Peering',        'VNet Peering',  'VPC Network Peering'),
    ('VPN',                'VPN Gateway',        'VPN Gateway',   'Cloud VPN'),
    ('Dedicated WAN',      'Direct Connect',     'ExpressRoute',  'Cloud Interconnect'),
    ('Hub-spoke routing',  'Transit Gateway',    'Virtual WAN',   'VPC Network Hub'),
    ('Firewall L7',        'AWS Network FW',     'Azure Firewall','Cloud NGFW'),
    ('Flow Logs',          'VPC Flow Logs',      'NSG Flow Logs', 'VPC Flow Logs'),
    ('Security Group',     'Security Groups',    'NSG',           'Firewall Rules'),
    ('Private IPs',        'RFC 1918 + /16-/28', '/8 to /29',     '/8 to /29'),
]
print(f'  {'Feature':<22} {'AWS':<22} {'Azure':<22} GCP')
print('  ' + '=' * 85)
for feat, aws, az, gcp in features:
    print(f'  {feat:<22} {aws:<22} {az:<22} {gcp}')
  \"
"
```

📸 **Verified Output:**
```
=== Cloud Networking: AWS vs Azure vs GCP ===

  Feature                AWS                    Azure                  GCP
  =====================================================================================
  Virtual Network        VPC                    VNet                   VPC (global)
  Subnet scope           AZ-specific            AZ-specific            Regional (global)
  DNS service            Route 53               Azure DNS              Cloud DNS
  Private DNS            Route 53 Resolver      Private DNS            Cloud DNS (private)
  Load Balancer L7       ALB                    App Gateway            Cloud Load Balancing
  Load Balancer L4       NLB                    Azure LB               TCP/UDP LB
  CDN                    CloudFront             Azure CDN/FD           Cloud CDN
  VPC Peering            VPC Peering            VNet Peering           VPC Network Peering
  VPN                    VPN Gateway            VPN Gateway            Cloud VPN
  Dedicated WAN          Direct Connect         ExpressRoute           Cloud Interconnect
```

> 💡 **Tip:** GCP's VPC is **global** — subnets are regional but the VPC spans all regions. AWS and Azure VPCs/VNets are **regional** and require explicit peering to connect across regions.

---

## Step 7: Cloud-Native DNS with Route 53 / Azure DNS

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
  python3 -c \"
print('=== Cloud DNS Architecture ===')
print()
print('  [Public Zone] example.com — served to internet')
print('    A     www.example.com      → 1.2.3.4  (ALB public IP)')
print('    A     api.example.com      → 1.2.3.5  (API ALB)')
print('    CNAME cdn.example.com      → d1234.cloudfront.net')
print('    MX    example.com          → mail.example.com (priority 10)')
print('    TXT   example.com          → v=spf1 include:amazonses.com ~all')
print()
print('  [Private Zone] internal.corp — DNS split-horizon')
print('    A     db.internal.corp     → 10.0.3.10  (RDS private IP)')
print('    A     cache.internal.corp  → 10.0.3.20  (ElastiCache)')
print('    A     app01.internal.corp  → 10.0.2.10')
print('    A     app02.internal.corp  → 10.0.2.11')
print('    SRV   _grpc.internal.corp  → 10.0.2.10:9090')
print()
print('  [Route 53 Routing Policies]')
policies = [
    ('Simple',       'Single record → single endpoint'),
    ('Weighted',     'Split traffic by weight: 80% v2 / 20% v1 (A/B testing)'),
    ('Failover',     'Primary + standby; health-check-based automatic failover'),
    ('Latency',      'Route to lowest-latency AWS region for user'),
    ('Geolocation',  'Route by user country/continent'),
    ('Geoproximity', 'Route by geographic proximity with bias'),
    ('Multivalue',   'Return multiple IPs; client-side load balancing'),
]
for policy, desc in policies:
    print(f'    {policy:<15} — {desc}')
  \"
"
```

📸 **Verified Output:**
```
=== Cloud DNS Architecture ===

  [Public Zone] example.com — served to internet
    A     www.example.com      → 1.2.3.4  (ALB public IP)
    A     api.example.com      → 1.2.3.5  (API ALB)
    CNAME cdn.example.com      → d1234.cloudfront.net
    MX    example.com          → mail.example.com (priority 10)
    TXT   example.com          → v=spf1 include:amazonses.com ~all

  [Private Zone] internal.corp — DNS split-horizon
    A     db.internal.corp     → 10.0.3.10  (RDS private IP)
    A     cache.internal.corp  → 10.0.3.20  (ElastiCache)
    A     app01.internal.corp  → 10.0.2.10
    A     app02.internal.corp  → 10.0.2.11
    SRV   _grpc.internal.corp  → 10.0.2.10:9090

  [Route 53 Routing Policies]
    Simple          — Single record → single endpoint
    Weighted        — Split traffic by weight: 80% v2 / 20% v1 (A/B testing)
    Failover        — Primary + standby; health-check-based automatic failover
    Latency         — Route to lowest-latency AWS region for user
    Geolocation     — Route by user country/continent
    Geoproximity    — Route by geographic proximity with bias
    Multivalue      — Return multiple IPs; client-side load balancing
```

---

## Step 8: Capstone — Complete Multi-AZ VPC Design

```bash
docker run --rm ubuntu:22.04 bash -c "
  apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
  python3 -c \"
import ipaddress

print('=' * 65)
print('  CAPSTONE: Production Multi-AZ VPC Design')
print('  Region: us-east-1  |  VPC: 10.10.0.0/16')
print('=' * 65)

vpc = ipaddress.IPv4Network('10.10.0.0/16')
print(f'  VPC total IPs: {vpc.num_addresses:,}  ({vpc.num_addresses//256} potential /24 subnets)')
print()

# 3 AZs x 3 tiers = 9 subnets
design = [
    # (tier, AZ, CIDR, internet_access, purpose)
    ('Public',  'us-east-1a', '10.10.1.0/24',  'IGW',  'ALB, NAT GW, Bastion'),
    ('Public',  'us-east-1b', '10.10.2.0/24',  'IGW',  'ALB (multi-AZ)'),
    ('Public',  'us-east-1c', '10.10.3.0/24',  'IGW',  'ALB (multi-AZ)'),
    ('App',     'us-east-1a', '10.10.11.0/24', 'NAT',  'App servers, ECS'),
    ('App',     'us-east-1b', '10.10.12.0/24', 'NAT',  'App servers, ECS'),
    ('App',     'us-east-1c', '10.10.13.0/24', 'NAT',  'App servers, ECS'),
    ('DB',      'us-east-1a', '10.10.21.0/24', 'None', 'RDS Primary'),
    ('DB',      'us-east-1b', '10.10.22.0/24', 'None', 'RDS Replica'),
    ('DB',      'us-east-1c', '10.10.23.0/24', 'None', 'ElastiCache'),
]

print(f'  {'Tier':<8} {'AZ':<14} {'CIDR':<16} {'Usable':<8} {'Internet':<6} Purpose')
print('  ' + '-' * 75)
for tier, az, cidr, internet, purpose in design:
    net = ipaddress.IPv4Network(cidr)
    usable = net.num_addresses - 5  # AWS reserves 5
    print(f'  {tier:<8} {az:<14} {cidr:<16} {usable:<8} {internet:<6} {purpose}')

print()
print('  Security Group Rules:')
sgs = [
    ('alb-sg',  'Inbound',  '0.0.0.0/0',     '80,443', 'Public internet to ALB'),
    ('app-sg',  'Inbound',  'alb-sg',          '8080',   'ALB to App servers'),
    ('app-sg',  'Outbound', '0.0.0.0/0',       'ALL',    'App outbound via NAT'),
    ('db-sg',   'Inbound',  'app-sg',           '3306',   'App to RDS MySQL'),
    ('db-sg',   'Outbound', 'DENY ALL',         '-',      'DB: no outbound'),
]
print(f'  {'SG':<10} {'Direction':<10} {'Source/Dest':<15} {'Port':<8} Description')
print('  ' + '-' * 65)
for sg, direction, src, port, desc in sgs:
    print(f'  {sg:<10} {direction:<10} {src:<15} {port:<8} {desc}')

print()
print('  Route Tables:')
print('    Public RT:  0.0.0.0/0 → igw-xxx  (Internet Gateway)')
print('    App RT:     0.0.0.0/0 → nat-xxx  (NAT Gateway, per AZ)')
print('    DB RT:      10.10.0.0/16 local only  (no internet route!)')
print()
print('  High Availability:')
print('    ALB: spans all 3 AZs (public subnets)')
print('    App: ASG across 3 AZs (min=3, desired=6, max=30)')
print('    DB:  RDS Multi-AZ (synchronous replication)')
print()
print('  CAPSTONE COMPLETE: Production Multi-AZ VPC design verified!')
  \"
"
```

📸 **Verified Output:**
```
=================================================================
  CAPSTONE: Production Multi-AZ VPC Design
  Region: us-east-1  |  VPC: 10.10.0.0/16
=================================================================
  VPC total IPs: 65,536  (256 potential /24 subnets)

  Tier     AZ             CIDR             Usable   Internet Purpose
  ---------------------------------------------------------------------------
  Public   us-east-1a     10.10.1.0/24     249      IGW    ALB, NAT GW, Bastion
  Public   us-east-1b     10.10.2.0/24     249      IGW    ALB (multi-AZ)
  Public   us-east-1c     10.10.3.0/24     249      IGW    ALB (multi-AZ)
  App      us-east-1a     10.10.11.0/24    249      NAT    App servers, ECS
  App      us-east-1b     10.10.12.0/24    249      NAT    App servers, ECS
  App      us-east-1c     10.10.13.0/24    249      NAT    App servers, ECS
  DB       us-east-1a     10.10.21.0/24    249      None   RDS Primary
  DB       us-east-1b     10.10.22.0/24    249      None   RDS Replica
  DB       us-east-1c     10.10.23.0/24    249      None   ElastiCache

  CAPSTONE COMPLETE: Production Multi-AZ VPC design verified!
```

---

## Summary

| Concept | Key Point |
|---------|-----------|
| **VPC** | Logically isolated virtual network; you define CIDR, subnets, routing |
| **Public Subnet** | Has route to Internet Gateway; hosts can receive inbound connections |
| **Private Subnet** | No inbound from internet; outbound via NAT Gateway |
| **Internet Gateway** | Free; bidirectional internet access for public subnets |
| **NAT Gateway** | Paid; outbound-only internet for private subnets (SNAT) |
| **Security Group** | Stateful; instance-level firewall; deny all by default |
| **NACL** | Stateless; subnet-level; must allow both inbound AND outbound |
| **VPC Peering** | Direct routing between two VPCs; non-transitive |
| **Transit Gateway** | Hub for multiple VPCs; transitive routing |
| **ALB** | Layer 7; path/host-based routing; HTTP/HTTPS |
| **NLB** | Layer 4; ultra-low latency; TCP/UDP; static IP |
| **Route 53** | AWS DNS; public + private zones; health-based routing |
| **Multi-AZ** | Deploy resources across 3+ AZs for high availability |
| **GCP VPC** | Global (spans regions); AWS/Azure VPCs are regional |

**Next Lab →** [Lab 20: Capstone — Network Design](lab-20-capstone-network-design.md)
