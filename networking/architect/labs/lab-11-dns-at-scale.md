# Lab 11: DNS at Scale

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

DNS is the phone book of the internet — and like all critical infrastructure, it needs to scale, be resilient, and be secured. This lab covers anycast DNS deployment, GeoDNS, BIND9 views, rate limiting, and DNSSEC.

---

## Objectives
- Design anycast DNS architecture
- Configure BIND9 views (internal/external split-horizon)
- Implement DNS Response Rate Limiting (RRL)
- Configure DNS firewall with RPZ (Response Policy Zones)
- Understand DNSSEC key management at scale
- Build a DNS load simulator

---

## Step 1: Anycast DNS Architecture

**Anycast DNS:** Same IP announced via BGP from multiple locations. Clients reach the nearest PoP.

```
                    BGP AS65001
                   /    |    \
              PoP-NYC  PoP-LON  PoP-TYO
              (1.1.1.1) (1.1.1.1) (1.1.1.1)
                   ↑         ↑         ↑
              NYC users   EU users  APAC users
              (same IP, different locations!)
```

**Requirements:**
1. Own public IP block (/24 minimum for BGP)
2. BGP router at each PoP announcing the /24
3. DNS server(s) at each PoP handling the anycast IP
4. Health check: withdraw BGP if DNS is unhealthy

**Anycast vs unicast DNS:**
| | Unicast | Anycast |
|-|---------|---------|
| Latency | High for distant users | Low (nearest PoP) |
| Failover | Manual/DNS TTL | Automatic (BGP reconverges) |
| DDoS resilience | Single target | Attack distributed across all PoPs |
| Complexity | Simple | Requires BGP + multi-PoP |

---

## Step 2: GeoDNS

GeoDNS returns different answers based on where the client is querying from.

**Use cases:**
- Route US users to us-east-1, EU users to eu-west-1
- Serve localized content (language, regulations)
- Implement PCI compliance (EU data in EU)

**BIND9 GeoDNS with GeoIP:**
```
# Install bind9 + geoip
apt-get install bind9 bind9-plugin-http

# named.conf.options
options {
    geoip-directory "/usr/share/GeoIP";
};

# ACL by country
acl eu_clients {
    geoip country EU;
};
acl us_clients {
    geoip country US;
};

# Zone with views
view "eu-view" {
    match-clients { eu_clients; };
    zone "app.example.com" {
        type master;
        file "/etc/bind/zones/app.example.com.eu";
    };
};
```

**Commercial GeoDNS alternatives:**
- Route 53 (AWS) — latency-based or geolocation routing
- Cloudflare Load Balancing — latency, geographic steering
- NS1 — programmatic DNS with advanced filters
- PowerDNS with GeoIP backend

---

## Step 3: BIND9 Split-Horizon Views

Split-horizon DNS returns different answers for internal vs external queries — typically private IPs internally, public IPs externally.

```
External query: www.company.com → 203.0.113.10 (public IP)
Internal query: www.company.com → 10.0.1.50 (private IP, direct)
```

**BIND9 views configuration:**
```
# /etc/bind/named.conf
acl internal_nets {
    10.0.0.0/8;
    172.16.0.0/12;
    192.168.0.0/16;
    localhost;
    localnets;
};

view "internal" {
    match-clients { internal_nets; };
    recursion yes;
    
    zone "company.com" {
        type master;
        file "/etc/bind/zones/company.com.internal";
    };
    
    # Include all public zones too
    include "/etc/bind/named.conf.default-zones";
};

view "external" {
    match-clients { any; };
    recursion no;   # No recursion for external — prevents abuse!
    
    zone "company.com" {
        type master;
        file "/etc/bind/zones/company.com.external";
    };
};
```

**Internal zone (`company.com.internal`):**
```
$TTL 300
@   IN SOA ns1.company.com. admin.company.com. (
            2026030501 ; serial
            3600       ; refresh
            900        ; retry
            604800     ; expire
            300 )      ; minimum TTL

@   IN NS  ns1.company.com.
www IN A   10.0.1.50        ; internal IP
app IN A   10.0.2.100       ; internal app server
db  IN A   10.0.3.200       ; internal DB (never external!)
```

> 💡 **Critical:** Never expose `db.company.com` in the external view. Attackers actively harvest DNS to find database servers, CI/CD systems, and management interfaces.

---

## Step 4: DNS Response Rate Limiting (RRL)

DNS amplification attacks use open resolvers to reflect/amplify traffic toward victims.

**Attack pattern:**
```
Attacker → DNS query (ANY example.com, spoofed src = victim IP)
         → DNS resolver (response 3000 bytes vs 40 byte query = 75× amplification)
         → Victim flooded with DNS responses
```

**RRL configuration (BIND9):**
```
options {
    rate-limit {
        responses-per-second 10;      // Max 10 responses/sec per client IP
        referrals-per-second 5;       // Max 5 referrals/sec
        errors-per-second 5;          // Limit error responses
        nxdomains-per-second 5;       // Limit NXDOMAIN responses
        window 5;                     // 5-second sliding window
        slip 2;                       // Send 1 truncated every 2 dropped
        log-only no;                  // Actually rate limit (not just log)
        exempt-clients { internal_nets; };  // Don't limit internal clients
    };
};
```

---

## Step 5: DNS Firewall (RPZ — Response Policy Zone)

RPZ allows DNS-level blocking of malicious domains (malware C&C, phishing, ransomware).

```
Client → DNS query for malware-c2.evil.com
       → DNS resolver (with RPZ) checks policy
       → RPZ says: "malware-c2.evil.com → NXDOMAIN or walled garden IP"
       → Client receives NXDOMAIN (domain doesn't exist)
       → Malware connection blocked!
```

**RPZ zone configuration:**
```
# named.conf.local
zone "rpz.internal" {
    type master;
    file "/etc/bind/zones/rpz.internal";
};

options {
    response-policy {
        zone "rpz.internal" policy NXDOMAIN;
    };
};
```

**RPZ zone file:**
```
$TTL 60
@ IN SOA ns1.company.com. admin.company.com. (
    2026030501 3600 900 604800 60 )
  IN NS ns1.company.com.

; Block malicious domains
malware-c2.evil.com.rpz.internal.       IN CNAME .  ; NXDOMAIN
phishing.fake-bank.net.rpz.internal.    IN CNAME .
; Wildcard block (all subdomains)
*.ransomware-domain.ru.rpz.internal.    IN CNAME .

; Walled garden (redirect to warning page)
ads.badnet.com.rpz.internal.            IN A 10.0.0.99  ; Show "blocked" page
```

**Commercial RPZ feeds:**
- Infoblox Threat Intelligence
- Cisco Umbrella (formerly OpenDNS)
- Quad9 (free, privacy-focused)
- ISC DNSRPZ feeds

---

## Step 6: DNSSEC at Scale

**DNSSEC adds cryptographic signatures to DNS records**, preventing cache poisoning and MITM attacks.

**Key types:**
- **ZSK (Zone Signing Key):** Signs zone records, rotated frequently (monthly)
- **KSK (Key Signing Key):** Signs ZSK, rotated rarely (annually), requires registry update

**DNSSEC workflow:**
```
Zone Admin → Signs zone with ZSK → Signs ZSK with KSK
Resolver   → Validates signature chain:
             DNSKEY (ZSK) → signs RRSIGs on records
             DNSKEY (KSK) → signs RRSIGs on DNSKEY
             DS record   → in parent zone, signed by parent
             Root KSK    → trust anchor (hardcoded in resolvers)
```

**Automatic DNSSEC with BIND9:**
```
zone "company.com" {
    type master;
    file "/etc/bind/zones/company.com";
    key-directory "/etc/bind/keys";
    inline-signing yes;        // Automatic signing
    auto-dnssec maintain;      // Automatic key rollover
    dnssec-policy default;     // Use default DNSSEC policy
};
```

> 💡 **DNSSEC failure mode:** If DNSSEC validation fails, the resolver returns SERVFAIL — the domain appears "down". Test thoroughly before enabling. Use `dig +dnssec` to verify signing and `delv` for full validation trace.

---

## Step 7: Verification — BIND9 Config + DNS Simulator

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq bind9 bind9utils python3 &&
named -v &&
named-checkconf /etc/bind/named.conf &&
echo 'named-checkconf: OK' &&
python3 - << 'EOF'
import random, time, statistics

print('DNS Load Simulator')
print('='*45)
queries = []
query_types = ['A', 'AAAA', 'MX', 'TXT', 'CNAME']
for i in range(1000):
    latency = random.gauss(2.5, 0.8)  # Mean 2.5ms, stddev 0.8ms
    latency = max(0.1, latency)
    queries.append({
        'type': random.choice(query_types),
        'latency_ms': round(latency, 2),
        'cache_hit': random.random() > 0.3  # 70% cache hit rate
    })

cache_hits = sum(1 for q in queries if q['cache_hit'])
latencies = [q['latency_ms'] for q in queries]
print(f'Total queries simulated: {len(queries)}')
print(f'Cache hit rate: {cache_hits/len(queries)*100:.1f}%')
print(f'Avg latency: {statistics.mean(latencies):.2f}ms')
print(f'P99 latency: {sorted(latencies)[990]:.2f}ms')
print(f'Max latency: {max(latencies):.2f}ms')
by_type = {}
for q in queries:
    by_type.setdefault(q['type'], []).append(q['latency_ms'])
print()
print('By query type:')
for qtype, lats in sorted(by_type.items()):
    print(f'  {qtype:<6} {len(lats):>4} queries  avg {statistics.mean(lats):.2f}ms')
EOF"
```

📸 **Verified Output:**
```
BIND 9.18.39-0ubuntu0.22.04.2-Ubuntu (Extended Support Version)
named-checkconf: OK
DNS Load Simulator
=============================================
Total queries simulated: 1000
Cache hit rate: 70.1%
Avg latency: 2.50ms
P99 latency: 4.37ms
Max latency: 5.42ms

By query type:
  A       209 queries  avg 2.52ms
  AAAA    198 queries  avg 2.48ms
  CNAME   196 queries  avg 2.51ms
  MX      204 queries  avg 2.49ms
  TXT     193 queries  avg 2.50ms
```

---

## Step 8: Capstone — Enterprise DNS Architecture

**Scenario:** Financial services firm, 10,000 users, strict compliance, SLA 99.999%.

**Architecture:**
```
External authoritative DNS:
  Anycast via BGP: 2 PoPs (US + EU)
  Provider: NS1 or Route 53 (SLA-backed)
  DNSSEC signed
  RPZ feeds: Infoblox + ISC

Internal recursive DNS:
  2 × BIND9 servers per datacenter (4 total)
  Views: internal (recursive) + DMZ (limited)
  RPZ: corporate security policy
  RRL: 20 resp/s per external IP
  Forwarders: 1.1.1.1, 8.8.8.8 as fallback

Split-horizon:
  internal.company.com → internal IPs
  company.com (public) → public IPs via NS1

Monitoring:
  dnsperf synthetic queries every 30s
  Alert on: latency > 50ms, SERVFAIL > 0.1%
  Grafana dashboard: query rate, cache hit, NXDOMAIN rate

DNSSEC:
  Algorithm: ECDSA P-256 (Algorithm 13) - modern, fast
  ZSK rotation: automated monthly (auto-dnssec maintain)
  KSK rotation: annual, coordinated with registrar DS update
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| Anycast DNS | Same IP, multiple PoPs — BGP routes to nearest |
| GeoDNS | Return different answers by client location |
| Split-horizon | Internal gets private IPs, external gets public IPs |
| RRL | Prevent DNS amplification attacks (10 resp/s limit) |
| RPZ | DNS-level malware/phishing blocking |
| DNSSEC | Cryptographic chain of trust, prevents cache poisoning |

**Next:** [Lab 12: CDN Architecture →](lab-12-cdn-architecture.md)
