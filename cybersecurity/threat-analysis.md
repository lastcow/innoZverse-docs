# Threat Analysis

Understanding how to identify, analyze, and respond to security threats.

## The Cyber Kill Chain

1. **Reconnaissance** — Target research
2. **Weaponization** — Create exploit + payload
3. **Delivery** — Phishing, drive-by download
4. **Exploitation** — Trigger vulnerability
5. **Installation** — Malware installed
6. **C2** — Command & control established
7. **Actions** — Data exfiltration, ransomware

## Common Threat Types

| Threat | Description |
|--------|-------------|
| Phishing | Fraudulent emails/sites to steal credentials |
| Ransomware | Encrypts data, demands payment |
| DDoS | Overwhelms servers with traffic |
| Man-in-the-Middle | Intercepts communications |
| Zero-Day | Exploits unknown vulnerabilities |

## Log Analysis

```bash
# Check auth logs for failed logins
grep "Failed password" /var/log/auth.log | tail -20

# Find suspicious IPs
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn

# Monitor in real-time
tail -f /var/log/auth.log
```

## Incident Response Checklist

- [ ] Identify and isolate affected systems
- [ ] Preserve evidence (logs, memory dumps)
- [ ] Determine attack vector
- [ ] Eradicate the threat
- [ ] Recover systems
- [ ] Post-incident review
