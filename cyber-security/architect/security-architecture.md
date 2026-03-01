# Security Architecture

## Zero Trust Architecture

"Never trust, always verify" — assume breach, verify explicitly, use least privilege.

```
Traditional:    [Trusted Inside] ←firewall→ [Untrusted Outside]
Zero Trust:     Every request verified regardless of origin

Pillars:
1. Identity verification (MFA, IAM)
2. Device health validation
3. Network micro-segmentation
4. Application-level access control
5. Data classification & protection
6. Continuous monitoring & analytics
```

## Security Architecture Patterns

### Defense in Depth
```
Layer 1: Perimeter (WAF, DDoS protection)
Layer 2: Network (Firewalls, IDS/IPS)
Layer 3: Application (Auth, input validation)
Layer 4: Data (Encryption at rest & in transit)
Layer 5: Identity (MFA, PAM, least privilege)
Layer 6: Endpoint (EDR, patch management)
Layer 7: Physical (Data center access control)
```

### SIEM Architecture (Splunk/ELK)

```
[Data Sources]          [Collection]      [Processing]      [Analysis]
Web logs ─────────────→                                   
Auth logs ────────────→  Logstash/      → Elasticsearch → Kibana/Splunk
Network logs ─────────→  Fluent Bit     
Endpoint logs ────────→                 → Alerts → SOC Team
Cloud audit logs ─────→
```

## Threat Modeling (STRIDE)

| Threat | Description | Mitigation |
|--------|-------------|-----------|
| **S**poofing | Impersonating another user/system | Strong authentication, MFA |
| **T**ampering | Modifying data in transit/rest | Integrity checks, signing |
| **R**epudiation | Denying actions taken | Audit logging, non-repudiation |
| **I**nformation Disclosure | Unauthorized data access | Encryption, access control |
| **D**enial of Service | Disrupting availability | Rate limiting, redundancy |
| **E**levation of Privilege | Gaining higher permissions | Least privilege, RBAC |

## Compliance Frameworks

```
SOC 2 Type II    → Service organizations (SaaS)
ISO 27001        → Information security management
PCI DSS          → Payment card data
HIPAA            → Healthcare data (US)
GDPR             → EU personal data
NIST CSF         → Cybersecurity framework
```
