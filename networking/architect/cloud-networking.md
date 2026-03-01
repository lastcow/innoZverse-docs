# Cloud Networking Architecture

## AWS VPC Design

```
VPC: 10.0.0.0/16
├── Public Subnets (Multi-AZ)
│   ├── us-east-1a: 10.0.1.0/24  [NAT GW, Load Balancer]
│   └── us-east-1b: 10.0.2.0/24
├── Private App Subnets
│   ├── us-east-1a: 10.0.10.0/24 [App servers]
│   └── us-east-1b: 10.0.11.0/24
└── Private Data Subnets
    ├── us-east-1a: 10.0.20.0/24 [Databases]
    └── us-east-1b: 10.0.21.0/24
```

## Multi-Region Active-Active

```
Region 1 (us-east-1)          Region 2 (eu-west-1)
    VPC ←─── VPC Peering ───→     VPC
     │        /Transit GW/          │
   [App]    ←── Route 53 ──→     [App]
     │       (Latency-based)        │
   [RDS] ←── Cross-Region ──→   [RDS]
           Replication
```

## Terraform VPC Module

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "production"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false  # One per AZ for HA
  enable_vpn_gateway     = true
  enable_dns_hostnames   = true
  enable_flow_log        = true

  tags = { Environment = "production" }
}
```
