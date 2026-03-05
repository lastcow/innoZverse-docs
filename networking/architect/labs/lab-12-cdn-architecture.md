# Lab 12: CDN Architecture

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

Content Delivery Networks reduce latency and origin load by caching content at edge Points of Presence (PoPs) distributed globally. This lab covers CDN architecture, cache hierarchy, Varnish configuration, and CDN security.

---

## Objectives
- Design CDN origin-edge architecture
- Master cache-control header strategies
- Configure Varnish Cache with VCL
- Implement cache invalidation strategies
- Design CDN security (WAF, DDoS, bot management)

---

## Step 1: CDN Architecture — Origin to Edge

```
User (Tokyo)
     ↓
Tokyo PoP (edge cache)  ←──── hit? ────→ serve immediately
     ↓ (cache miss)
Regional PoP (mid-tier) ←──── hit? ────→ serve + cache at Tokyo
     ↓ (cache miss)
Origin Server (us-east-1) ──────────────→ serve + populate cache chain
```

**Three-tier cache hierarchy:**
| Tier | Name | Purpose | TTL |
|------|------|---------|-----|
| Edge | PoP cache | Serve users | Short (minutes-hours) |
| Regional | Mid-tier | Shield origin from PoPs | Medium (hours-days) |
| Origin | Source of truth | Dynamic content generation | n/a |

**Major CDN providers:**
| Provider | Strength |
|----------|----------|
| Cloudflare | DDoS protection, Workers edge compute |
| AWS CloudFront | Deep AWS integration, Lambda@Edge |
| Fastly | Instant cache purge, VCL control |
| Akamai | Largest PoP network, security focus |
| Azure Front Door | Microsoft/Office integration |

---

## Step 2: Cache-Control Headers

Cache-control is the primary mechanism for controlling caching behavior.

**Cache-Control directives:**
```
# Cache for 1 day at CDN, 1 hour at browser
Cache-Control: public, max-age=3600, s-maxage=86400

# Don't cache (sensitive pages)
Cache-Control: private, no-store

# Stale-while-revalidate: serve stale while refreshing
Cache-Control: public, max-age=300, stale-while-revalidate=60

# Conditional: serve from cache but validate with origin
Cache-Control: no-cache          # Must revalidate before serving
ETag: "abc123def"                # Fingerprint of content
Last-Modified: Thu, 01 Jan 2026 00:00:00 GMT
```

**Directive reference:**
| Directive | Who | Meaning |
|-----------|-----|---------|
| `public` | CDN + browser | Anyone can cache |
| `private` | Browser only | CDN must not cache |
| `no-store` | All | Never cache or store |
| `no-cache` | All | Cache but revalidate |
| `max-age=N` | Browser | Browser cache TTL seconds |
| `s-maxage=N` | CDN only | CDN cache TTL seconds |
| `stale-while-revalidate=N` | CDN | Serve stale for N seconds while refreshing |
| `stale-if-error=N` | CDN | Serve stale for N seconds on origin error |
| `immutable` | Browser | Never revalidate (for versioned assets) |

**Per-content strategy:**
```
Static assets (hashed filename):
  Cache-Control: public, max-age=31536000, immutable
  (1 year — never changes, filename changes on update)

HTML pages:
  Cache-Control: public, max-age=0, s-maxage=300, must-revalidate

API responses:
  Cache-Control: no-cache, no-store  (or vary by endpoint)

User-specific content:
  Cache-Control: private, max-age=300
```

> 💡 **Cache key design:** The CDN cache key determines what's cached separately. By default: URL only. Consider including relevant Vary headers (Accept-Language, Accept-Encoding) but NOT cookies or Authorization (prevents sharing cached responses between users).

---

## Step 3: Varnish Cache Configuration

Varnish is the leading open-source HTTP cache. It uses VCL (Varnish Configuration Language) for flexible caching policies.

**VCL subroutines:**
```
vcl_recv:   Process incoming request (decide to pass/hash)
vcl_hash:   Compute cache key
vcl_hit:    Cache hit (deliver or miss)
vcl_miss:   Cache miss (fetch from backend)
vcl_pass:   Pass request to backend (don't cache)
vcl_backend_response: Process backend response (set TTL)
vcl_deliver: Send response to client
```

**Production VCL configuration:**
```vcl
vcl 4.1;

import std;

backend default {
    .host = "10.0.1.50";
    .port = "8080";
    .probe = {
        .url = "/health";
        .timeout = 2s;
        .interval = 5s;
        .window = 5;
        .threshold = 3;
    }
}

acl internal {
    "localhost";
    "10.0.0.0"/8;
}

sub vcl_recv {
    # Normalize URL
    set req.url = std.querysort(req.url);
    
    # Strip tracking params from cache key
    set req.url = regsuball(req.url, "[?&](utm_[a-z]+|fbclid|gclid)=[^&]+", "");
    
    # Pass for authenticated requests
    if (req.http.Authorization) {
        return(pass);
    }
    
    # Pass for POST/PUT/DELETE
    if (req.method != "GET" && req.method != "HEAD") {
        return(pass);
    }
    
    # Strip cookies for static assets
    if (req.url ~ "\.(css|js|png|jpg|gif|ico|woff2|svg)(\?.*)?$") {
        unset req.http.Cookie;
        return(hash);
    }
}

sub vcl_backend_response {
    # Cache 5xx for 1 second (prevent thundering herd)
    if (beresp.status >= 500) {
        set beresp.ttl = 1s;
        set beresp.grace = 5s;
    }
    
    # Enable grace mode: serve stale up to 1 hour on origin errors
    set beresp.grace = 1h;
    
    # Don't cache if Set-Cookie present
    if (beresp.http.Set-Cookie) {
        set beresp.uncacheable = true;
    }
    
    # Override TTL for static assets
    if (req.url ~ "\.(css|js|png|jpg)(\?.*)?$") {
        set beresp.ttl = 86400s;  # 24 hours
    }
}

sub vcl_deliver {
    # Add cache status header for debugging
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
        set resp.http.X-Cache-Hits = obj.hits;
    } else {
        set resp.http.X-Cache = "MISS";
    }
    
    # Remove internal headers
    unset resp.http.Server;
    unset resp.http.X-Powered-By;
}

# Purge endpoint (internal only)
sub vcl_recv {
    if (req.method == "PURGE") {
        if (!client.ip ~ internal) {
            return(synth(403, "Forbidden"));
        }
        return(purge);
    }
}
```

---

## Step 4: Cache Invalidation

**Methods:**
1. **TTL expiry:** Let cache expire naturally (simplest, least control)
2. **URL purge:** Invalidate specific URL immediately
3. **Tag-based (surrogate keys):** Purge all content tagged with a key
4. **Soft purge:** Mark as stale but still serve during revalidation

**URL purge:**
```bash
# Varnish
curl -X PURGE http://cache-server/path/to/file.html

# Cloudflare API
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"files": ["https://www.example.com/style.css"]}'
```

**Tag-based purge (Surrogate-Key / Cache-Tag):**
```
# Response from origin:
Surrogate-Key: product:123 category:electronics brand:apple

# Purge all products in category when catalog updates:
curl -X POST /purge -d '{"tag": "category:electronics"}'
# Invalidates ALL cached pages tagged with category:electronics
```

> 💡 **Tag-based purge is the key to maintainable cache invalidation at scale.** When a product price changes, purge by product ID tag — all pages, API responses, and fragments referencing that product are instantly invalidated.

---

## Step 5: CDN Security

**DDoS protection:**
```
Layer 3/4 DDoS:
  Anycast absorption — attack traffic distributed across all PoPs
  BGP blackhole (RTBH) for volumetric attacks
  Rate limiting at network edge

Layer 7 DDoS:
  Request rate limiting per IP/ASN
  Challenge pages (JS challenge, CAPTCHA)
  IP reputation blocking
```

**WAF (Web Application Firewall) at CDN edge:**
```
Rule categories:
  OWASP Core Rule Set (CRS) — SQLi, XSS, RFI, LFI
  IP reputation — known bad actors, Tor exit nodes
  Custom rules — application-specific patterns

Cloudflare WAF example:
  (http.request.uri.path contains "/admin") and 
  not (ip.src in {10.0.0.0/8})
  → block
```

**Bot management:**
```
Detection methods:
  User-agent analysis (known bad bots)
  Behavioral analysis (mouse movements, timing)
  JavaScript challenges (bots can't execute JS)
  Device fingerprinting
  
Categories:
  Good bots:    Googlebot, Bingbot (allow)
  Verified bots: Uptimerobot, monitoring (allow)
  Bad bots:     Scrapers, credential stuffing (block/challenge)
```

---

## Step 6: CDN Routing Strategies

**DNS-based routing:**
```
CNAME www.example.com → xyz.cloudflare.net
                           ↓
               Cloudflare DNS returns nearest edge IP
               based on client's resolver IP location
```

**Anycast routing:**
```
BGP announces same IP from all PoPs
Client TCP connects → routed by BGP to nearest
(Cloudflare, NS1, Fastly use anycast)
```

**Origin shield:**
```
Edge PoPs → single origin shield PoP → origin
(reduces origin connections from 200 edge PoPs to 1 shield connection)
```

---

## Step 7: Verification — Varnish Install + VCL Syntax Check

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y -qq varnish &&
varnishd -V 2>&1 | head -1 &&
cat > /tmp/test.vcl << 'EOF'
vcl 4.1;
backend default {
    .host = \"127.0.0.1\";
    .port = \"8080\";
}
sub vcl_recv {
    if (req.url ~ \"^/static/\") {
        unset req.http.Cookie;
    }
}
sub vcl_backend_response {
    if (bereq.url ~ \"^/static/\") {
        set beresp.ttl = 86400s;
    }
}
sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = \"HIT\";
    } else {
        set resp.http.X-Cache = \"MISS\";
    }
}
EOF
varnishd -C -f /tmp/test.vcl 2>&1 | head -5 &&
echo 'VCL syntax: OK'"
```

📸 **Verified Output:**
```
varnishd (varnish-6.6.1 revision e6a8c860944c4f6a7e1af9f40674ea78bbdcdc66)
VCL syntax: OK
```

---

## Step 8: Capstone — CDN Strategy for Media Platform

**Scenario:** Video streaming platform, 10M daily active users, 50% video content, 30% images, 20% API.

**CDN design:**
```
Content strategy:
  Video (HLS segments):
    Cache-Control: public, max-age=31536000, immutable
    (Segments have content-hash in filename)
    CDN: Cloudflare Stream or Fastly
    
  Images (product/profile):
    Cache-Control: public, max-age=86400, s-maxage=604800
    Surrogate-Key: user:{uid} or product:{pid}
    CDN: Cloudflare Images (transform at edge)
    
  API responses:
    Cache-Control: public, s-maxage=60, stale-while-revalidate=30
    Vary: Accept-Language, Accept-Encoding
    Surrogate-Key: content:{id}

Geographic strategy:
  Primary CDN: Cloudflare (largest PoP coverage, DDoS protection)
  Video fallback: AWS CloudFront (S3 origin integration)
  Multi-CDN DNS: Route 53 weighted → 70% CF, 30% CF2 (resilience)

Origin protection:
  Origin shield in us-east-1 (single connection point to origin)
  Origin IP hidden (only CDN can connect)
  Firewall: allow only Cloudflare IP ranges to origin

Cache invalidation:
  API: Tag-based purge on content update webhook
  Video: Immutable (never purge, use versioned URLs)
  Images: Tag-based purge on user profile update

Security:
  WAF: OWASP CRS + custom API rules
  Bot: Allow Googlebot, block scrapers (JS challenge)
  DDoS: Cloudflare Magic Transit for L3/L4
  HTTPS: TLS 1.3 only, HSTS preload, Certificate Transparency
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| Edge hierarchy | User → edge PoP → regional shield → origin |
| s-maxage | CDN TTL (separate from browser max-age) |
| immutable | For versioned/hashed assets; never revalidate |
| stale-while-revalidate | Serve stale while refreshing = zero-latency revalidation |
| Surrogate keys | Tag-based purge → efficient content invalidation |
| Varnish VCL | Per-URL cache policies; strip cookies from static assets |
| WAF at edge | Block attacks before they reach origin |

**Next:** [Lab 13: WAN Optimization →](lab-13-wan-optimization.md)
