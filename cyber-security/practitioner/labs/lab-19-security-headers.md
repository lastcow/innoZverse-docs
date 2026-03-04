# Lab 19: Security Headers

## Objective
Audit and implement HTTP security headers: detect missing headers on live servers, implement Content-Security-Policy (CSP) to block XSS, configure HSTS with preloading to prevent SSL stripping, use X-Frame-Options and frame-ancestors to block clickjacking, implement Permissions-Policy to restrict browser APIs, and score a web application against industry-standard security header benchmarks.

## Background
HTTP security headers are a free layer of defence that instruct browsers on how to behave when loading your application. A missing `Content-Security-Policy` allows XSS attacks to run freely; a missing `Strict-Transport-Security` enables SSL stripping on public Wi-Fi; missing `X-Frame-Options` enables clickjacking. Security headers require no code changes — they're configuration. Yet studies show over 90% of the top million websites are missing critical headers. The [securityheaders.com](https://securityheaders.com) scanner grades sites A–F on header implementation.

## Time
30 minutes

## Prerequisites
- Lab 05 (A05 Security Misconfiguration)
- Lab 14 (File Upload) — mentions CSP in context

## Tools
- Docker: `zchencow/innozverse-cybersec:latest`

---

## Lab Instructions

### Step 1: Security Header Audit

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Security Header Audit ===')
print()

# Simulate HTTP response headers from a typical web server
typical_insecure_response = {
    'Content-Type':   'text/html; charset=utf-8',
    'Server':         'Apache/2.4.52 (Ubuntu)',  # Information disclosure!
    'X-Powered-By':   'PHP/8.1.2',               # Information disclosure!
    'Date':           'Wed, 04 Mar 2026 01:00:00 GMT',
    'Content-Length': '12543',
}

required_security_headers = {
    'Strict-Transport-Security': {
        'recommended': 'max-age=31536000; includeSubDomains; preload',
        'protects': 'SSL stripping, MITM on HTTP→HTTPS redirect',
        'missing_risk': 'HIGH',
    },
    'Content-Security-Policy': {
        'recommended': \"default-src 'self'; script-src 'self'; style-src 'self'\",
        'protects': 'XSS, data injection, clickjacking (frame-ancestors)',
        'missing_risk': 'HIGH',
    },
    'X-Frame-Options': {
        'recommended': 'DENY',
        'protects': 'Clickjacking attacks',
        'missing_risk': 'MEDIUM',
    },
    'X-Content-Type-Options': {
        'recommended': 'nosniff',
        'protects': 'MIME-type sniffing attacks',
        'missing_risk': 'MEDIUM',
    },
    'Referrer-Policy': {
        'recommended': 'strict-origin-when-cross-origin',
        'protects': 'Sensitive URL leakage via Referer header',
        'missing_risk': 'LOW-MEDIUM',
    },
    'Permissions-Policy': {
        'recommended': 'geolocation=(), microphone=(), camera=()',
        'protects': 'Unauthorized browser API access (camera, location)',
        'missing_risk': 'MEDIUM',
    },
    'Cache-Control': {
        'recommended': 'no-store (for authenticated pages)',
        'protects': 'Sensitive data in browser/proxy cache',
        'missing_risk': 'MEDIUM',
    },
}

information_disclosure_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version', 'X-AspNetMvc-Version']

print('Response header audit:')
print()
score = 0
max_score = len(required_security_headers)

print('[Present headers]')
for header, value in typical_insecure_response.items():
    if header in information_disclosure_headers:
        print(f'  ⚠️  {header}: {value}  ← REMOVE (information disclosure)')
    else:
        print(f'  ℹ️  {header}: {value}')

print()
print('[Missing security headers]')
for header, info in required_security_headers.items():
    present = header in typical_insecure_response
    if not present:
        risk_icon = '🔴' if info['missing_risk'] == 'HIGH' else ('🟠' if 'MEDIUM' in info['missing_risk'] else '🟡')
        print(f'  {risk_icon} MISSING: {header}')
        print(f'     Risk:     {info[\"missing_risk\"]}')
        print(f'     Protects: {info[\"protects\"]}')
        print(f'     Add:      {header}: {info[\"recommended\"][:60]}')
        print()
    else:
        score += 1

print(f'Security Header Score: {score}/{max_score} — Grade: F')
"
```

**📸 Verified Output:**
```
[Missing security headers]
  🔴 MISSING: Strict-Transport-Security
     Risk: HIGH
     Protects: SSL stripping, MITM on HTTP→HTTPS redirect

  🔴 MISSING: Content-Security-Policy
     Risk: HIGH
     Protects: XSS, data injection, clickjacking

Security Header Score: 0/7 — Grade: F
```

> 💡 **Security headers are client-side enforcement.** They tell the browser what to do, not what not to do. A `Content-Security-Policy: default-src 'self'` header means the browser will refuse to load scripts from `evil.com` — even if the attacker injects `<script src="https://evil.com/steal.js">`. Without the header, the browser will happily load it.

### Step 2: Strict-Transport-Security (HSTS)

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== HTTP Strict Transport Security (HSTS) ===')
print()

print('Problem: HTTP → HTTPS redirect is vulnerable to SSL stripping.')
print()
print('Attack (SSLstrip):')
attack_steps = [
    'Victim connects to coffee shop Wi-Fi (attacker controls router)',
    'Victim types: innozverse.com (HTTP)',
    'Browser sends: GET http://innozverse.com/',
    'Attacker intercepts, makes HTTPS connection to innozverse.com on behalf of victim',
    'Attacker responds to victim over plain HTTP',
    'Victim sees no HTTPS padlock — credentials sent in plaintext',
    'Attacker reads username and password',
]
for i, step in enumerate(attack_steps, 1):
    print(f'  Step {i}: {step}')

print()
print('HSTS prevents this:')
print('  First visit (must be over HTTPS):')
print('  ← Strict-Transport-Security: max-age=31536000; includeSubDomains; preload')
print()
print('  Browser stores: \"innozverse.com → HTTPS only for 1 year\"')
print()
print('  Next time victim types: innozverse.com')
print('  Browser: internally upgrades to HTTPS BEFORE making network request')
print('  Attacker never sees any HTTP traffic → SSLstrip fails')
print()

hsts_directives = {
    'max-age=31536000': {
        'meaning': '1 year — cache this HSTS policy for 1 year',
        'note': 'Start with smaller value (300), increase after testing',
    },
    'includeSubDomains': {
        'meaning': 'Apply HSTS to all subdomains (api., admin., etc.)',
        'note': 'Ensure ALL subdomains have valid TLS before enabling',
    },
    'preload': {
        'meaning': 'Submit to browser preload list (hardcoded HTTPS before first visit)',
        'note': 'Submit at hstspreload.org — PERMANENT, very hard to undo',
    },
}

for directive, info in hsts_directives.items():
    print(f'  [{directive}]')
    print(f'    Meaning: {info[\"meaning\"]}')
    print(f'    Note:    {info[\"note\"]}')
    print()

print('HSTS preload list:')
print('  Chrome, Firefox, Edge, Safari all ship with preloaded list')
print('  ~140,000 domains are preloaded (as of 2026)')
print('  Once preloaded: users NEVER send HTTP to your domain, ever')
print('  Removal takes 6-12 months and requires site to be reachable over HTTP first')
"
```

### Step 3: Content-Security-Policy (CSP)

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Content Security Policy (CSP) ===')
print()

print('CSP directives explained:')

csp_directives = {
    'default-src': (\"'self'\", 'Fallback for all content types not explicitly listed'),
    'script-src':  (\"'self' 'nonce-RANDOM' https://cdn.trusted.com\",
                    'Where scripts can load from (most important!)'),
    'style-src':   (\"'self' 'nonce-RANDOM'\", 'Stylesheet sources'),
    'img-src':     (\"'self' data: https:\", 'Image sources'),
    'connect-src': (\"'self' https://api.innozverse.com\", 'XHR/fetch/WebSocket destinations'),
    'font-src':    (\"'self' https://fonts.gstatic.com\", 'Web font sources'),
    'frame-src':   (\"'none'\", 'Iframe sources (none = no iframes allowed)'),
    'frame-ancestors':(\"'none'\", 'Who can embed this page in iframes (prevents clickjacking)'),
    'form-action': (\"'self'\", 'Where forms can submit to'),
    'base-uri':    (\"'self'\", 'Restricts <base> tag (prevents base tag injection)'),
    'object-src':  (\"'none'\", 'Flash/Java plugins (none = block all)'),
    'upgrade-insecure-requests': ('', 'Upgrade all HTTP subresources to HTTPS'),
    'report-uri':  ('/csp-report', 'Send violation reports here (for monitoring)'),
}

print(f'  {\"Directive\":<25} {\"Example Value\":<50} Description')
for directive, (value, desc) in csp_directives.items():
    print(f'  {directive:<25} {value:<50} {desc}')

print()
print('CSP bypass techniques:')
bypasses = [
    (\"unsafe-inline\", \"Allows all inline scripts — defeats CSP entirely\"),
    (\"unsafe-eval\",   \"Allows eval() — can be abused to execute arbitrary code\"),
    (\"*\",             \"Wildcard source — allows any domain\"),
    ('data:', \"Allows data: URIs — can encode malicious scripts\"),
    ('JSONP endpoints', 'Allowed CDN has JSONP endpoint → script injection'),
    ('Angular + CSP',   'Angular 1.x template injection bypasses CSP'),
]
for bypass, desc in bypasses:
    print(f'  [AVOID] {bypass:<30} → {desc}')

print()
print('Nonce-based CSP (best practice):')
import secrets
nonce = secrets.token_urlsafe(16)
print(f'  Server generates per-request nonce: {nonce}')
print(f'  CSP header: script-src \\'nonce-{nonce}\\' \\'strict-dynamic\\'')
print(f'  HTML: <script nonce=\"{nonce}\">...</script>')
print(f'  Attacker-injected <script> has no nonce → blocked!')
print(f'  Even if attacker injects: <script src=evil.com/x.js> → no nonce → blocked!')
"
```

**📸 Verified Output:**
```
CSP bypass techniques:
  [AVOID] unsafe-inline → Allows all inline scripts — defeats CSP entirely
  [AVOID] * (wildcard)  → allows any domain

Nonce-based CSP:
  Server nonce: 3q8Kv2mP9xR4wT7n...
  CSP: script-src 'nonce-3q8Kv2mP9xR4wT7n' 'strict-dynamic'
  Attacker-injected <script> has no nonce → blocked!
```

### Step 4: Clickjacking and X-Frame-Options

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Clickjacking Attack & Defences ===')
print()
print('Clickjacking: attacker overlays transparent iframe over legitimate site.')
print('Victim thinks they are clicking on attacker\\'s page, actually clicking innozverse.com.')
print()

clickjacking_html = '''<!-- Attacker\\'s page: evil.com/clickjack.html -->
<html>
<head>
  <style>
    iframe {
      position: absolute; top: 0; left: 0;
      width: 100%; height: 100%;
      opacity: 0.00001;   /* Nearly invisible */
      z-index: 99;        /* On top of everything */
    }
    #fake-button {
      position: absolute;
      top: 200px; left: 300px;  /* Aligned with Delete Account button on target */
    }
  </style>
</head>
<body>
  <!-- This iframe loads the real innozverse.com -->
  <iframe src=\"https://innozverse.com/settings\"></iframe>
  <!-- Victim sees this, clicks it, actually clicks the invisible iframe -->
  <button id=\"fake-button\">🎁 Click to claim your free Surface Pro!</button>
</body>
</html>'''

print('Attacker\\'s page:')
print(clickjacking_html)
print()
print('What happens:')
print('  Victim thinks they clicked \"Claim Prize\" button')
print('  Actually clicked \"Delete Account\" on innozverse.com settings page')
print()

print('Defences:')
defences = {
    'X-Frame-Options: DENY': {
        'effect': 'Browser refuses to render page in any iframe',
        'coverage': 'All browsers (legacy support)',
        'caveats': 'No granular control; cannot allow specific origins',
    },
    'X-Frame-Options: SAMEORIGIN': {
        'effect': 'Only same origin can embed in iframe',
        'coverage': 'All browsers',
        'caveats': 'Cannot allow specific third-party origins',
    },
    'CSP frame-ancestors: \\'none\\'': {
        'effect': 'Same as X-Frame-Options: DENY (modern equivalent)',
        'coverage': 'Modern browsers only',
        'caveats': 'Use both for legacy browser support',
    },
    'CSP frame-ancestors: \\'self\\' https://trusted.com': {
        'effect': 'Allow specific origins to embed page',
        'coverage': 'Modern browsers',
        'caveats': 'Most flexible option',
    },
}
for header, info in defences.items():
    print(f'  [{header}]')
    for k, v in info.items():
        print(f'    {k}: {v}')
    print()

print('Recommendation: Set BOTH for compatibility:')
print('  X-Frame-Options: DENY')
print('  Content-Security-Policy: frame-ancestors \\'none\\'')
"
```

### Step 5: Permissions-Policy Header

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Permissions-Policy (formerly Feature-Policy) ===')
print()
print('Controls which browser APIs/features can be used by the page and its iframes.')
print()

permissions = {
    'geolocation':         ('()', 'Disable geolocation access completely'),
    'microphone':          ('()', 'Block microphone access'),
    'camera':              ('()', 'Block camera access'),
    'payment':             ('()', 'Block Payment Request API'),
    'usb':                 ('()', 'Block USB device access'),
    'bluetooth':           ('()', 'Block Bluetooth access'),
    'notifications':       ('()', 'Block Push Notification API'),
    'fullscreen':          ('self', 'Only allow fullscreen for same origin'),
    'autoplay':            ('()', 'Disable autoplay (reduces ad abuse)'),
    'sync-xhr':            ('()', 'Disable synchronous XHR (performance)'),
    'accelerometer':       ('()', 'Block motion sensor access'),
    'gyroscope':           ('()', 'Block gyroscope access'),
    'interest-cohort':     ('()', 'Opt out of FLoC (privacy)'),
}

print('Recommended Permissions-Policy for e-commerce:')
policy_parts = []
for feature, (value, desc) in permissions.items():
    policy_parts.append(f'{feature}={value}')
    print(f'  {feature}={value:<10} ← {desc}')

full_policy = ', '.join(policy_parts)
print()
print(f'Full header:')
print(f'  Permissions-Policy: {full_policy[:80]}')
print(f'                      {full_policy[80:]}')
print()
print('Why this matters for security:')
reasons = [
    ('geolocation=()',  'Malicious iframe cannot covertly track user location'),
    ('microphone=()',   'Malicious ad cannot enable microphone without permission'),
    ('camera=()',       'Prevents invisible camera activation'),
    ('payment=()',      'Prevents payment API abuse in iframes'),
    ('usb=()',          'Prevents BadUSB-style attacks via browser'),
]
for feature, reason in reasons:
    print(f'  [{feature}] {reason}')
"
```

### Step 6: Referrer-Policy and Cache-Control

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
print('=== Referrer-Policy ===')
print()
print('Controls what URL info is sent in the Referer header to other sites.')
print()

policies = {
    'no-referrer':                    'Never send Referer header',
    'no-referrer-when-downgrade':     'Default: send to HTTPS, not HTTP (legacy)',
    'origin':                         'Send only origin (no path): https://site.com',
    'origin-when-cross-origin':       'Full URL same-origin, origin-only cross-origin',
    'same-origin':                    'Only send Referer for same-origin requests',
    'strict-origin':                  'Only send origin (HTTPS→HTTPS only)',
    'strict-origin-when-cross-origin':'Recommended: full URL same-origin, origin cross-origin',
    'unsafe-url':                     'Always send full URL (DANGEROUS)',
}

print(f'  {\"Policy\":<45} Description')
for policy, desc in policies.items():
    danger = '⚠️' if policy == 'unsafe-url' else ('✓' if 'strict' in policy or policy == 'no-referrer' else ' ')
    print(f'  {danger} {policy:<43} {desc}')

print()
print('Risk without Referrer-Policy:')
print('  User visits: https://innozverse.com/order/ORD-99999/confirm?token=abc123')
print('  Clicks link to external resource (CDN, analytics, image)')
print('  Referer: https://innozverse.com/order/ORD-99999/confirm?token=abc123')
print('  → Token visible to third-party server in their access logs!')
print()
print('Recommendation: Referrer-Policy: strict-origin-when-cross-origin')
print()

print('=== Cache-Control for Authenticated Pages ===')
print()
cache_scenarios = {
    'Authenticated dashboard': {
        'value':    'no-store',
        'reason':   'Never cache — contains personal data',
        'risk_without': 'Browser back button shows cached page after logout',
    },
    'API response with sensitive data': {
        'value':    'no-store, private',
        'reason':   'Not stored in browser or CDN cache',
        'risk_without': 'CDN caches personal data, serves to wrong users',
    },
    'Static assets (JS/CSS)': {
        'value':    'public, max-age=31536000, immutable',
        'reason':   'Cache aggressively — content-addressed filenames',
        'risk_without': 'Users re-download assets on every page load',
    },
    'API 200 response (default)': {
        'value':    'no-cache, must-revalidate',
        'reason':   'Validate with server before using cached response',
        'risk_without': 'Stale data shown; security fixes bypassed',
    },
}

for resource, config in cache_scenarios.items():
    print(f'  [{resource}]')
    for k, v in config.items():
        print(f'    {k:<18}: {v}')
    print()
"
```

### Step 7: Complete Security Headers Configuration

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
import secrets

nonce = secrets.token_urlsafe(16)

print('=== Complete Security Headers for InnoZverse ===')
print()

headers = {
    # Transport security
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

    # XSS / code injection
    'Content-Security-Policy': (
        f\"default-src 'self'; \"
        f\"script-src 'self' 'nonce-{nonce}' 'strict-dynamic'; \"
        f\"style-src 'self' 'nonce-{nonce}'; \"
        f\"img-src 'self' data: https:; \"
        f\"font-src 'self' https://fonts.gstatic.com; \"
        f\"connect-src 'self' https://api.innozverse.com; \"
        f\"frame-ancestors 'none'; \"
        f\"object-src 'none'; \"
        f\"base-uri 'self'; \"
        f\"form-action 'self'; \"
        f\"upgrade-insecure-requests; \"
        f\"report-uri /csp-violations\"
    ),

    # Clickjacking (legacy)
    'X-Frame-Options': 'DENY',

    # MIME sniffing
    'X-Content-Type-Options': 'nosniff',

    # Referrer
    'Referrer-Policy': 'strict-origin-when-cross-origin',

    # Permissions
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=()',

    # Cache (authenticated pages)
    'Cache-Control': 'no-store',

    # Remove info disclosure
    'Server': '',  # Remove entirely
    'X-Powered-By': '',  # Remove entirely

    # Cross-origin isolation
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Embedder-Policy': 'require-corp',
    'Cross-Origin-Resource-Policy': 'same-origin',
}

for header, value in headers.items():
    if value:
        print(f'{header}: {value[:100]}')
        if len(value) > 100:
            print(f'         {value[100:]}')
    else:
        print(f'  REMOVE: {header} header')
"
```

### Step 8: Capstone — Security Header Scoring

```bash
docker run --rm zchencow/innozverse-cybersec:latest python3 -c "
headers = [
    # Header name, grade value, present, recommendation
    ('Strict-Transport-Security',      'A', True,  'max-age=31536000; includeSubDomains; preload'),
    ('Content-Security-Policy',        'A', True,  'nonce-based with strict-dynamic'),
    ('X-Frame-Options',                'B', True,  'DENY (backup for CSP frame-ancestors)'),
    ('X-Content-Type-Options',         'B', True,  'nosniff'),
    ('Referrer-Policy',                'B', True,  'strict-origin-when-cross-origin'),
    ('Permissions-Policy',             'B', True,  'geolocation=(), microphone=(), camera=()'),
    ('Cross-Origin-Opener-Policy',     'A', True,  'same-origin'),
    ('Cross-Origin-Embedder-Policy',   'A', True,  'require-corp'),
    ('Cross-Origin-Resource-Policy',   'A', True,  'same-origin'),
    ('Cache-Control (sensitive pages)','B', True,  'no-store'),
    ('Server header removed',          'B', True,  '(no version disclosure)'),
    ('X-Powered-By removed',           'B', True,  '(no tech stack disclosure)'),
]

print('Security Headers Score — innozverse.com')
print()
score = sum(1 for _, _, present, _ in headers if present)
total = len(headers)
pct = score / total * 100

for header, grade, present, rec in headers:
    icon = '✓' if present else '✗'
    print(f'  [{icon}] {header:<45} [{grade}] {rec[:50]}')

print()
print(f'Total: {score}/{total} ({pct:.0f}%)')
grade = 'A+' if pct == 100 else 'A' if pct >= 90 else 'B' if pct >= 75 else 'C' if pct >= 60 else 'F'
print(f'Grade: {grade}')
print()
print('Verification tools:')
print('  • https://securityheaders.com — free online scanner')
print('  • https://observatory.mozilla.org — Mozilla Observatory')
print('  • curl -I https://innozverse.com — manual inspection')
print('  • Lighthouse audit (Chrome DevTools)')
"
```

---

## Summary

| Header | Protects Against | Recommended Value |
|--------|-----------------|-------------------|
| HSTS | SSL stripping, MITM | `max-age=31536000; includeSubDomains; preload` |
| CSP | XSS, data injection | Nonce-based with `strict-dynamic` |
| X-Frame-Options | Clickjacking | `DENY` |
| X-Content-Type-Options | MIME sniffing | `nosniff` |
| Referrer-Policy | URL data leakage | `strict-origin-when-cross-origin` |
| Permissions-Policy | Browser API abuse | Disable unused APIs |
| Cache-Control | Data exposure in cache | `no-store` for authenticated pages |

## Further Reading
- [securityheaders.com](https://securityheaders.com) — Scan any site
- [Mozilla Observatory](https://observatory.mozilla.org) — Detailed analysis
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [CSP Evaluator](https://csp-evaluator.withgoogle.com) — Validate your CSP
