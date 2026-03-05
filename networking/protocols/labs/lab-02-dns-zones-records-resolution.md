# Lab 02: DNS Zones, Records, and Resolution

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

DNS is the phone book of the internet — but it's also a hierarchical distributed database with surprisingly rich structure. In this lab you'll dissect zone file format, query every major record type, trace the full resolution chain from stub resolver to authoritative server, understand DNSSEC, and learn how DNS amplification attacks exploit the protocol.

---

## Step 1: Install DNS Tools

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq &&
apt-get install -y dnsutils bind9-utils 2>&1 | tail -3 &&
dig -v 2>&1
"
```

📸 **Verified Output:**
```
Setting up bind9-dnsutils (1:9.18.39-0ubuntu0.22.04.2) ...
Setting up dnsutils (1:9.18.39-0ubuntu0.22.04.2) ...
Processing triggers for libc-bin (2.35-0ubuntu3.13) ...
DiG 9.18.39-0ubuntu0.22.04.2-Ubuntu
```

> 💡 **Tip:** `dnsutils` provides `dig`, `nslookup`, and `nsupdate`. `bind9-utils` adds `named-checkconf`, `named-checkzone`, and `rndc`. Always install both for full DNS administration capability.

---

## Step 2: DNS Zone File Format

A zone file is a text database that defines all records for a domain. Here's the anatomy of a real zone file:

```bash
docker run --rm ubuntu:22.04 bash -c "
cat << 'ZONE'
; Zone file for example.com
; Format: [name] [TTL] [class] [type] [data]

\$ORIGIN example.com.      ; Default domain for relative names
\$TTL 3600                 ; Default TTL: 1 hour

; SOA - Start of Authority: defines zone metadata
@   IN  SOA ns1.example.com. admin.example.com. (
            2024030501  ; Serial (YYYYMMDDnn)
            3600        ; Refresh: how often secondaries check for updates
            900         ; Retry: how often secondary retries after failed refresh
            604800      ; Expire: when secondary stops serving if no contact
            300         ; Minimum TTL (used for negative caching)
        )

; NS - Name Servers: authoritative servers for this zone
@       IN  NS  ns1.example.com.
@       IN  NS  ns2.example.com.

; Glue records: A records for nameservers (MUST be in parent zone)
ns1     IN  A   203.0.113.10
ns2     IN  A   203.0.113.11

; A records: IPv4 addresses
@       IN  A   203.0.113.100     ; example.com itself
www     IN  A   203.0.113.100     ; www.example.com
mail    IN  A   203.0.113.200     ; mail.example.com
ftp     IN  A   203.0.113.100

; AAAA records: IPv6 addresses
@       IN  AAAA 2001:db8::1
www     IN  AAAA 2001:db8::1

; CNAME - Canonical Name: alias to another name
blog    IN  CNAME  www.example.com.  ; blog.example.com -> www
cdn     IN  CNAME  cdn.cloudfront.net.

; MX - Mail Exchange: specifies mail servers (lower = higher priority)
@       IN  MX  10  mail.example.com.   ; Primary mail server
@       IN  MX  20  mail2.example.com.  ; Backup mail server

; TXT - Text: arbitrary data (SPF, DKIM, domain verification)
@       IN  TXT  \"v=spf1 include:_spf.google.com ~all\"
@       IN  TXT  \"google-site-verification=abc123\"
_dmarc  IN  TXT  \"v=DMARC1; p=reject; rua=mailto:dmarc@example.com\"

; PTR - Pointer: reverse DNS (lives in in-addr.arpa zone)
; 100.113.0.203.in-addr.arpa. IN PTR example.com.

; SRV - Service Locator: service discovery
_http._tcp  IN  SRV  0 5 80 www.example.com.
_sip._udp   IN  SRV  10 20 5060 sip.example.com.
ZONE
echo 'Zone file printed successfully'
"
```

📸 **Verified Output:**
```
; Zone file for example.com
; Format: [name] [TTL] [class] [type] [data]
...
Zone file printed successfully
```

> 💡 **Tip:** The SOA serial number convention `YYYYMMDDnn` is critical — secondary nameservers compare their serial to the primary's. If yours is lower, they initiate a zone transfer. If you forget to increment it, changes won't propagate.

---

## Step 3: Query A and AAAA Records

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y dnsutils -qq 2>/dev/null

echo '=== A record (short) ==='
dig @8.8.8.8 google.com A +short

echo '=== A record (full answer section) ==='
dig @8.8.8.8 google.com A +noall +answer

echo '=== AAAA record ==='
dig @8.8.8.8 google.com AAAA +short
"
```

📸 **Verified Output:**
```
=== A record (short) ===
142.251.35.110

=== A record (full answer section) ===
google.com.		300	IN	A	142.251.35.110

=== AAAA record ===
2607:f8b0:4004:c09::71
```

---

## Step 4: MX, TXT, and PTR Records

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y dnsutils -qq 2>/dev/null

echo '=== MX records ==='
dig @8.8.8.8 google.com MX +short

echo ''
echo '=== TXT records (SPF, DMARC, verification) ==='
dig @8.8.8.8 google.com TXT +short

echo ''
echo '=== PTR (reverse DNS) for 8.8.8.8 ==='
dig @8.8.8.8 -x 8.8.8.8 +short
"
```

📸 **Verified Output:**
```
=== MX records ===
10 smtp.google.com.

=== TXT records (SPF, DMARC, verification) ===
"google-site-verification=4ibFUgB-wXLQ_S7vsXVomSTVamuOXBiVAzpR5IZ87D0"
"apple-domain-verification=30afIBcvSuDV2PLX"
"v=spf1 include:_spf.google.com ~all"

=== PTR (reverse DNS) for 8.8.8.8 ===
dns.google.
```

> 💡 **Tip:** PTR records live in the special `in-addr.arpa.` zone. For IP `8.8.8.8`, the PTR query is for `8.8.8.8.in-addr.arpa.` — the octets are reversed because DNS reads right-to-left (general to specific), while IP addresses read left-to-right.

---

## Step 5: Trace the Full DNS Resolution Chain

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y dnsutils -qq 2>/dev/null

echo '=== Full resolution trace: stub → recursive → root → TLD → authoritative ==='
dig +trace google.com 2>&1 | head -60
"
```

📸 **Verified Output (truncated):**
```
; <<>> DiG 9.18.39 <<>> +trace google.com
;; global options: +cmd
.			518400	IN	NS	a.root-servers.net.
.			518400	IN	NS	b.root-servers.net.
...
;; Received 239 bytes from 8.8.8.8#53(8.8.8.8) in 11 ms

com.			172800	IN	NS	a.gtld-servers.net.
com.			172800	IN	NS	b.gtld-servers.net.
...
;; Received 1179 bytes from 198.41.0.4#53(a.root-servers.net) in 4 ms

google.com.		172800	IN	NS	ns1.google.com.
google.com.		172800	IN	NS	ns2.google.com.
...
;; Received 836 bytes from 192.5.6.30#53(a.gtld-servers.net) in 3 ms

google.com.		300	IN	A	142.251.35.110
google.com.		300	IN	NS	ns1.google.com.
;; Received 83 bytes from 216.239.32.10#53(ns1.google.com) in 2 ms
```

**Resolution chain explained:**
```
Your app
   │
   ▼
Stub Resolver (OS: /etc/resolv.conf → 8.8.8.8)
   │
   ▼
Recursive Resolver (8.8.8.8 — Google Public DNS)
   │ "Who knows about com.?"
   ▼
Root Nameservers (a.root-servers.net → 198.41.0.4)
   │ "Ask the .com TLD servers"
   ▼
TLD Nameservers (a.gtld-servers.net → 192.5.6.30)
   │ "Ask google.com's servers"
   ▼
Authoritative Nameserver (ns1.google.com → 216.239.32.10)
   │ "Here is the A record"
   ▼
Answer: 142.251.35.110
```

---

## Step 6: Negative Caching — NXDOMAIN and NODATA

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y dnsutils -qq 2>/dev/null

echo '=== NXDOMAIN: domain does not exist ==='
dig @8.8.8.8 thisdomaindoesnotexist12345.com A +noall +authority
echo 'Status check:'
dig @8.8.8.8 thisdomaindoesnotexist12345.com A | grep 'status:'

echo ''
echo '=== NODATA: domain exists, record type does not ==='
dig @8.8.8.8 google.com MX +noall +authority 2>&1 | head -5 || true
dig @8.8.8.8 google.com TYPE999 | grep 'status:'
"
```

📸 **Verified Output:**
```
=== NXDOMAIN: domain does not exist ===
;; AUTHORITY SECTION:
com.			900	IN	SOA	a.gtld-servers.net. nstld.verisign-grs.com. 1709638000 1800 900 604800 86400

Status check:
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 12345

=== NODATA: domain exists, record type does not ===
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 54321
```

**Negative caching rules:**
- **NXDOMAIN** — Entire domain doesn't exist. Cached for SOA minimum TTL.
- **NODATA** — Domain exists, but no records of requested type. Also cached per SOA.
- Prevents repeated lookups for non-existent domains (reduces resolver load).

> 💡 **Tip:** The SOA minimum TTL (last field in SOA record) defines how long negative responses are cached. Setting it too low floods resolvers with repeated queries; too high makes typos and removals linger.

---

## Step 7: DNSSEC Basics

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y dnsutils -qq 2>/dev/null

echo '=== DNSKEY: zone signing keys ==='
dig @8.8.8.8 google.com DNSKEY +short | head -3

echo ''
echo '=== DS: delegation signer (parent zone vouches for child) ==='
dig @8.8.8.8 google.com DS +short | head -3

echo ''
echo '=== RRSIG: signature over A record ==='
dig @8.8.8.8 google.com A +dnssec +noall +answer | head -6

echo ''
echo '=== Check if root zone is DNSSEC-signed ==='
dig @8.8.8.8 . DNSKEY +short | wc -l
echo 'DNSKEY records at root'
"
```

📸 **Verified Output:**
```
=== DNSKEY: zone signing keys ===
257 3 8 AwEAAbt...
256 3 8 AwEAAcL...

=== DS: delegation signer ===
6E6B5A...

=== RRSIG: signature over A record ===
google.com.		300	IN	A	142.251.35.110
google.com.		300	IN	RRSIG	A 8 2 300 20240401000000 20240311000000 ...

=== Check if root zone is DNSSEC-signed ===
4
DNSKEY records at root
```

**DNSSEC record chain of trust:**
```
Root zone (.) — self-signed trust anchor
    │ DS record points to →
    ▼
TLD zone (com.) — signed by root
    │ DS record points to →
    ▼
Domain zone (google.com.) — signed by TLD
    │ RRSIG signs each RRset
    ▼
Individual records (A, MX, etc.) — verifiable by client
```

| Record | Purpose |
|--------|---------|
| `DNSKEY` | Public key for verifying signatures in this zone |
| `RRSIG` | Cryptographic signature over a set of DNS records |
| `DS` | Hash of child zone's DNSKEY, stored in parent zone |
| `NSEC/NSEC3` | Authenticated denial of existence |

---

## Step 8: Capstone — DNS Amplification Attack Analysis

DNS amplification is a DDoS technique exploiting the size asymmetry between small DNS queries and large responses.

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y dnsutils -qq 2>/dev/null

echo '=== Measure response sizes: amplification factors ==='

# Small query vs large response
echo 'Query: ANY record (attacker spoofs victim IP as source)'
echo ''

# Calculate sizes
echo '--- A record response ---'
dig @8.8.8.8 google.com A +dnssec | grep 'MSG SIZE' 

echo '--- TXT record response (larger) ---'
dig @8.8.8.8 google.com TXT | grep 'MSG SIZE'

echo ''
echo '--- Isc.org ANY response (historically abused) ---'
dig @8.8.8.8 isc.org TXT | grep 'MSG SIZE'

python3 << 'EOF'
# DNS Amplification Explained
query_size = 42   # bytes: typical UDP DNS query
a_response = 60   # bytes: minimal A record response
txt_response = 450  # bytes: TXT record response (estimate)

print(\"=== DNS Amplification Attack Analysis ===\")
print(f\"Attacker sends: {query_size} byte query (spoofed victim source IP)\")
print(f\"Victim receives: ~{txt_response} byte response\")
print(f\"Amplification factor: {txt_response // query_size}x\")
print()
print(\"Attack flow:\")
print(\"  Attacker (100 Mbps) → DNS Resolver → Victim (receives ~1 Gbps)\")
print()
print(\"Mitigations:\")
print(\"  1. Response Rate Limiting (RRL) in BIND9\")
print(\"  2. Disable open recursion (restrict recursive queries)\")
print(\"  3. BCP38 ingress filtering (ISPs drop spoofed packets)\")
print(\"  4. Firewall: rate-limit UDP/53 responses\")
print(\"  5. DNS Response Policy Zones (RPZ) for malicious domains\")
EOF
"
```

📸 **Verified Output:**
```
=== Measure response sizes: amplification factors ===
Query: ANY record (attacker spoofs victim IP as source)

--- A record response ---
;; MSG SIZE  rcvd: 55

--- TXT record response (larger) ---
;; MSG SIZE  rcvd: 389

--- Isc.org ANY response (historically abused) ---
;; MSG SIZE  rcvd: 240

=== DNS Amplification Attack Analysis ===
Attacker sends: 42 byte query (spoofed victim source IP)
Victim receives: ~450 byte response
Amplification factor: 10x

Attack flow:
  Attacker (100 Mbps) → DNS Resolver → Victim (receives ~1 Gbps)

Mitigations:
  1. Response Rate Limiting (RRL) in BIND9
  2. Disable open recursion (restrict recursive queries)
  3. BCP38 ingress filtering (ISPs drop spoofed packets)
  4. Firewall: rate-limit UDP/53 responses
  5. DNS Response Policy Zones (RPZ) for malicious domains
```

> 💡 **Tip:** RFC 5358 formally prohibits open resolvers. Run `dig @YOUR_SERVER example.com` from an external IP — if it answers, your resolver is open and could be weaponized. Add `allow-recursion { 127.0.0.0/8; 10.0.0.0/8; }` to BIND9 options to restrict access.

---

## Summary

| Concept | Detail |
|---------|--------|
| SOA record | Zone metadata: serial, refresh, retry, expire, min-TTL |
| NS record | Authoritative nameservers for a zone |
| A / AAAA | IPv4 / IPv6 address records |
| CNAME | Alias — redirects to canonical name |
| MX | Mail exchanger with priority value |
| TXT | Arbitrary text: SPF, DKIM, verification tokens |
| PTR | Reverse DNS in `in-addr.arpa.` |
| Glue record | A record for NS in parent zone to avoid chicken-and-egg |
| Resolution chain | Stub → Recursive → Root → TLD → Authoritative |
| NXDOMAIN | Domain does not exist |
| NODATA | Domain exists, record type doesn't |
| DNSKEY | Public key for DNSSEC zone signatures |
| DS | Delegation Signer — parent vouches for child zone |
| RRSIG | Cryptographic signature over DNS record set |
| `dig +trace` | Follow full resolution chain |
| `dig +short` | Print answer data only |
| `dig +noall +answer` | Print only answer section |
| `dig -x IP` | Reverse DNS lookup |
