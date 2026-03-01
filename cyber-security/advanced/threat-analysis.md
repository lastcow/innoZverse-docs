# Threat Analysis Framework

## The Cyber Kill Chain

| Phase | Attacker Action | Defender Response |
|-------|----------------|-------------------|
| 1. Reconnaissance | Research target | Monitor public exposure |
| 2. Weaponization | Create exploit | Patch vulnerabilities |
| 3. Delivery | Send phishing email | Email filtering, training |
| 4. Exploitation | Execute payload | EDR, patching |
| 5. Installation | Install malware | AV, application control |
| 6. C2 | Establish backdoor | Network monitoring, firewall |
| 7. Actions | Exfiltrate data | DLP, anomaly detection |

## MITRE ATT&CK Framework

MITRE ATT&CK is a knowledge base of adversary tactics and techniques.

- **Tactics** — The *why* (what the attacker wants to achieve)
- **Techniques** — The *how* (specific methods used)
- **Procedures** — Real-world implementations

```bash
# Example: T1059.001 - Command and Scripting: PowerShell
# Detection: Monitor for powershell.exe with suspicious arguments
```

## Threat Intelligence Feeds

- **VirusTotal** — File and URL analysis
- **AbuseIPDB** — Malicious IP database
- **AlienVault OTX** — Open threat exchange
- **CISA Advisories** — US government alerts

```bash
# Check if an IP is malicious
curl "https://api.abuseipdb.com/api/v2/check?ipAddress=1.2.3.4" \
  -H "Key: YOUR_API_KEY"
```
