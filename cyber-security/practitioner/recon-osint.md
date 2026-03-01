# Reconnaissance & OSINT

OSINT (Open Source Intelligence) uses publicly available information to gather intel about a target — without touching their systems.

## Passive Reconnaissance Tools

```bash
# DNS enumeration
whois target.com
dig target.com ANY
dig target.com MX
dnsrecon -d target.com

# Certificate transparency
curl "https://crt.sh/?q=%.target.com&output=json" | jq '.[].name_value'

# Email harvesting
theHarvester -d target.com -b google,bing,linkedin

# Shodan (requires account)
shodan search "hostname:target.com"
```

## Google Dorks

```
site:target.com filetype:pdf
site:target.com inurl:admin
site:target.com "password" filetype:txt
intitle:"index of" site:target.com
```

## Social Media & People Search

- **LinkedIn** — Employees, org structure, tech stack
- **GitHub** — Source code, credentials in commits
- **Pastebin** — Leaked data
- **Wayback Machine** — Old versions of sites

```bash
# Search GitHub for exposed secrets
# https://github.com/search?q=target.com+password

# Check for leaked credentials
# https://haveibeenpwned.com
```

## Subdomain Enumeration

```bash
subfinder -d target.com             # Fast passive enumeration
amass enum -d target.com            # Comprehensive enumeration
ffuf -w subdomains.txt -u http://FUZZ.target.com -H "Host: FUZZ.target.com"
```
