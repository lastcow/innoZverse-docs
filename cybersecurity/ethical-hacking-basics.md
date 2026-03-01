# Ethical Hacking Basics

Ethical hacking (penetration testing) involves legally testing systems for vulnerabilities before malicious actors do.

## The Penetration Testing Process

1. **Reconnaissance** — Gather information about the target
2. **Scanning** — Identify open ports and services
3. **Exploitation** — Attempt to exploit vulnerabilities
4. **Post-Exploitation** — Assess impact, maintain access
5. **Reporting** — Document findings and remediation steps

## Reconnaissance

```bash
# Passive recon (no direct contact)
whois target.com
dig target.com
theHarvester -d target.com -b google

# Active recon
nmap -sn 192.168.1.0/24      # Ping sweep
nmap -sV -O 192.168.1.100    # OS + version detection
```

## Common Vulnerabilities (OWASP Top 10)

1. **Broken Access Control**
2. **Cryptographic Failures**
3. **Injection** (SQL, Command, XSS)
4. **Insecure Design**
5. **Security Misconfiguration**
6. **Vulnerable Components**
7. **Auth Failures**
8. **Data Integrity Failures**
9. **Logging Failures**
10. **SSRF**

## SQL Injection Example

```sql
-- Normal query
SELECT * FROM users WHERE username = 'alice';

-- Injected
SELECT * FROM users WHERE username = '' OR '1'='1';
-- Returns all users!
```

> ⚠️ **Legal Notice:** Only test systems you own or have explicit written permission to test.
