# Lab 05: Cloud Security Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-cybersec:latest bash`

## Objectives
- Understand CSPM, CWPP, and CASB in cloud security
- Apply the shared responsibility model
- Analyse IAM policies for least-privilege compliance
- Evaluate CIS Benchmarks for cloud

---

## Step 1: Shared Responsibility Model

| Layer | AWS/Azure/GCP | Customer |
|-------|-------------|----------|
| Physical infrastructure | ✅ Provider | |
| Virtualisation/Hypervisor | ✅ Provider | |
| OS (managed services) | ✅ Provider (e.g., RDS) | |
| OS (IaaS VMs) | | ✅ Customer |
| Middleware/Runtime | | ✅ Customer |
| Application code | | ✅ Customer |
| Data | | ✅ Customer |
| IAM / Access Control | | ✅ Customer |
| Network configuration | Shared | Shared |
| Encryption in transit/rest | Shared | Shared |

> 💡 **The most common cloud breaches** involve customer-managed layers: misconfigured S3 buckets, overly permissive IAM roles, and exposed management ports. The provider's infrastructure is rarely compromised.

---

## Step 2: CSPM / CWPP / CASB

**Cloud Security Posture Management (CSPM):**
- Continuously scans cloud resources for misconfigurations
- Checks against CIS Benchmarks, NIST, PCI DSS
- Examples: Prisma Cloud, AWS Security Hub, Wiz

**Cloud Workload Protection Platform (CWPP):**
- Protects cloud workloads at runtime
- Vulnerability scanning, EDR for cloud instances, container security
- Examples: CrowdStrike Falcon Cloud, Lacework, Aqua Security

**Cloud Access Security Broker (CASB):**
- Visibility and control over SaaS applications
- Shadow IT discovery, DLP for cloud, UEBA
- Examples: Microsoft Defender for Cloud Apps, Netskope, McAfee MVISION

```
┌──────────────────────────────────────────────────┐
│              Cloud Security Architecture          │
│  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  CSPM    │  │  CWPP    │  │     CASB      │  │
│  │Posture & │  │Workload  │  │ SaaS/Shadow IT│  │
│  │Compliance│  │Protection│  │ DLP/UEBA      │  │
│  └────┬─────┘  └────┬─────┘  └──────┬────────┘  │
│       └─────────────┼────────────────┘           │
│                     ▼                            │
│              Cloud SIEM / CNAPP                  │
└──────────────────────────────────────────────────┘
```

---

## Step 3: CIS Benchmarks for Cloud

**CIS AWS Foundations Benchmark (Level 1 critical controls):**

| Control | Description | Check |
|---------|-----------|-------|
| 1.1 | Avoid use of root account | CloudTrail + CloudWatch alarm |
| 1.4 | MFA on root account | IAM credential report |
| 1.14 | Hardware MFA for root | IAM MFA device |
| 2.1.2 | S3 buckets not publicly accessible | S3 Block Public Access |
| 2.2.1 | EBS volumes encrypted | EC2 API check |
| 3.1 | CloudTrail enabled in all regions | CloudTrail config |
| 3.4 | CloudTrail log file validation | CloudTrail setting |
| 4.1 | No unrestricted SSH (0.0.0.0/0:22) | Security Group rules |
| 4.2 | No unrestricted RDP (0.0.0.0/0:3389) | Security Group rules |

---

## Step 4: IAM Least-Privilege Analyser

```python
policies = [
    {
        'name': 'AdminPolicy',
        'statements': [{'Effect': 'Allow', 'Action': '*', 'Resource': '*'}]
    },
    {
        'name': 'S3ReadOnly',
        'statements': [{'Effect': 'Allow', 'Action': ['s3:GetObject', 's3:ListBucket'], 'Resource': 'arn:aws:s3:::my-bucket/*'}]
    },
    {
        'name': 'EC2PowerUser',
        'statements': [
            {'Effect': 'Allow', 'Action': 'ec2:*', 'Resource': '*'},
            {'Effect': 'Allow', 'Action': 'iam:PassRole', 'Resource': '*'}
        ]
    }
]

HIGH_RISK = ['*', 'iam:*', 'sts:AssumeRole', 'iam:PassRole', 's3:*', 'ec2:*']

def analyse_policy(p):
    findings = []
    for stmt in p['statements']:
        if stmt['Effect'] != 'Allow':
            continue
        actions = stmt['Action'] if isinstance(stmt['Action'], list) else [stmt['Action']]
        resource = stmt['Resource']
        for action in actions:
            if action == '*' or action in HIGH_RISK:
                risk = 'CRITICAL' if action == '*' else 'HIGH'
                findings.append(f'{risk}: action={action}, resource={resource}')
    return findings

print('=== IAM Least-Privilege Analyser ===')
for p in policies:
    findings = analyse_policy(p)
    status = 'FAIL' if findings else 'PASS'
    print(f'  [{status}] {p["name"]}')
    for f in findings:
        print(f'         {f}')

print()
print('=== Cloud Security Model Summary ===')
models = [('CSPM', 'Cloud Security Posture Mgmt', 'Misconfigurations, compliance'),
          ('CWPP', 'Cloud Workload Protection',    'Runtime, vuln scanning'),
          ('CASB', 'Cloud Access Security Broker', 'Shadow IT, DLP, UEBA')]
for abbr, name, scope in models:
    print(f'  {abbr:<6} {name:<32} {scope}')
```

📸 **Verified Output:**
```
=== IAM Least-Privilege Analyser ===
  [FAIL] AdminPolicy
         CRITICAL: action=*, resource=*
  [PASS] S3ReadOnly
  [FAIL] EC2PowerUser
         HIGH: action=ec2:*, resource=*
         HIGH: action=iam:PassRole, resource=*

=== Cloud Security Model Summary ===
  CSPM   Cloud Security Posture Mgmt      Misconfigurations, compliance
  CWPP   Cloud Workload Protection        Runtime, vuln scanning
  CASB   Cloud Access Security Broker     Shadow IT, DLP, UEBA
```

---

## Step 5: IAM Design Principles

**Principle of Least Privilege (PoLP):**
```
Bad:  {"Effect": "Allow", "Action": "*", "Resource": "*"}
Good: {"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::bucket/*"}
```

**IAM at scale — service accounts:**
- Use IAM roles (not access keys) for EC2/Lambda/ECS workloads
- Rotate access keys every 90 days
- Use AWS Organizations SCPs to enforce guardrails across all accounts
- Enable AWS IAM Access Analyzer to detect external access

**Permission boundary pattern:**
```json
{
  "Effect": "Allow",
  "Action": ["s3:*", "ec2:Describe*"],
  "Resource": "*",
  "Condition": {
    "StringEquals": {"aws:RequestedRegion": ["us-east-1", "eu-west-1"]},
    "Bool": {"aws:MultiFactorAuthPresent": "true"}
  }
}
```

---

## Step 6: Cloud Network Security Architecture

**Multi-account architecture (AWS Landing Zone):**
```
AWS Organizations
├── Management Account (billing + SCPs)
├── Security Account (security tooling, GuardDuty aggregation)
├── Log Archive Account (centralised CloudTrail/VPC flow logs)
├── Production OU
│   ├── Production Account A (workload)
│   └── Production Account B (workload)
├── Development OU
│   └── Dev Account
└── Shared Services (DNS, Active Directory, Transit Gateway)
```

**VPC security layers:**
```
Internet → WAF/Shield → ALB → [Public subnet: NAT, Bastion]
                            → [Private subnet: EC2/ECS workloads]
                            → [Isolated subnet: RDS, ElastiCache]
```

> 💡 **Security groups are stateful; NACLs are stateless.** Use security groups for application-level rules; use NACLs as an additional layer for subnet-level blocking (e.g., block known-malicious CIDRs).

---

## Step 7: Cloud Security Monitoring

**Key log sources for cloud SIEM:**
| Service | Log Source | Key Events |
|---------|-----------|-----------|
| AWS | CloudTrail | API calls, IAM changes, console logins |
| AWS | VPC Flow Logs | Network traffic accept/reject |
| AWS | GuardDuty | Threat detection (crypto mining, C2, anomalies) |
| AWS | Config | Configuration changes, compliance drift |
| Azure | Azure AD Audit | Login events, role changes |
| GCP | Cloud Audit Logs | Admin activity, data access |

**Critical CloudTrail alerts:**
- Root account login
- MFA disabled
- IAM policy change
- S3 bucket ACL change to public
- CloudTrail stopped/deleted
- Console login from new country

---

## Step 8: Capstone — Multi-Cloud Security Architecture

**Scenario:** Financial services firm running AWS (primary) + Azure (M365/Entra ID)

```
Cloud Security Architecture:

Identity Federation:
  - Azure AD as primary IdP
  - AWS SSO federated with Azure AD via SAML
  - All AWS accounts: MFA required, no IAM users (roles only)

CSPM:
  - Prisma Cloud (multi-cloud: AWS + Azure)
  - CIS Benchmark Level 1 compliance target
  - Automated remediation for S3/storage public access

Workload Protection:
  - CrowdStrike Falcon for EC2 instances
  - AWS Inspector for vulnerability scanning
  - ECR image scanning for containers

Data Security:
  - S3 encryption: SSE-KMS, bucket policies deny HTTP
  - KMS key rotation: annual
  - Macie for PII/PAN detection in S3

Monitoring:
  - CloudTrail → Security Account S3 → Splunk
  - GuardDuty enabled all regions
  - Security Hub aggregating findings
  - MTTR target for critical findings: 4 hours

Network:
  - Transit Gateway hub-and-spoke
  - Egress inspection via Gateway Load Balancer + Palo Alto
  - VPC Flow Logs → centralized S3 → Splunk
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| Shared Responsibility | Cloud secures infrastructure; customer secures data/IAM/config |
| CSPM | Continuous posture scanning against CIS/NIST benchmarks |
| CWPP | Runtime protection for cloud workloads |
| CASB | SaaS visibility, shadow IT, DLP |
| IAM PoLP | No wildcards; use conditions; roles not keys |
| Multi-account | Separate accounts per environment/function |
| Monitoring | CloudTrail + GuardDuty + Config = cloud security telemetry |
