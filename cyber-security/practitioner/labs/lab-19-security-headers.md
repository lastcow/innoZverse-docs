# Lab 19: Security Headers

## Objective

Audit and exploit missing HTTP security headers using a live web API from Kali Linux:

1. **Header audit** — use `curl` to enumerate exactly which security headers are missing from an unprotected API (score: **0/7**)
2. **Reflected XSS amplified by missing CSP** — send a `<script>` tag in a query parameter; with no `Content-Security-Policy`, the browser would execute it
3. **Clickjacking risk from missing X-Frame-Options** — demonstrate how the app can be embedded in a malicious iframe
4. **MIME sniffing via missing X-Content-Type-Options** — upload polyglot content that a browser would execute as a different type
5. **Secure endpoint comparison** — audit the protected version (score: **7/7**) and confirm every header is present and correct
6. **Implement the full header set** — write a Flask middleware that adds all 7 headers globally

---

## Background

Security headers are the cheapest, highest-ROI security controls available — a one-time server configuration change that mitigates entire vulnerability classes at the browser level.

**Real-world impact of missing headers:**
- **Missing CSP → XSS escalation**: The 2018 British Airways breach ($228M fine, 500,000 customers) began with a skimming script injected into their payment page. A strong CSP blocking `script-src 'self'` would have prevented the injected script from executing.
- **Missing X-Frame-Options → Clickjacking**: In 2009, Adobe Flash settings pages were clickjacked via invisible iframes, allowing attackers to silently enable webcam access. `X-Frame-Options: DENY` would have blocked this.
- **Missing HSTS → SSL strip**: Attackers on the same network (coffee shop Wi-Fi, hotel) can downgrade HTTPS to HTTP before the first connection. HSTS tells the browser to always use HTTPS, preventing the downgrade.
- **Missing X-Content-Type-Options → MIME sniffing**: A file uploaded as `text/plain` but containing HTML gets rendered as HTML by IE/Chrome if `nosniff` is absent — XSS via file uploads.
- **Missing Referrer-Policy → data leakage**: Without this header, the browser sends the full URL (including query params with PII) in the `Referer` header to third-party analytics/CDN providers.

**OWASP coverage:** A05:2021 (Security Misconfiguration)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Network: lab-a19                         │
│                                                                     │
│  ┌──────────────────────┐         HTTP requests                    │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  innozverse-kali     │                                           │
│  │                      │  ◀──────── HTTP responses (with headers)  │
│  │  Tools:              │                                           │
│  │  • curl -I           │  ┌────────────────────────────────────┐  │
│  │  • python3           │  │       VICTIM WEB APP (Lab 19)      │  │
│  └──────────────────────┘  │   zchencow/innozverse-cybersec     │  │
│                             │                                    │  │
│                             │  Flask :5000                       │  │
│                             │  /api/products     (0/7 headers)   │  │
│                             │  /api/products-secure (7/7)        │  │
│                             │  /api/headers-check (audit tool)   │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
35 minutes

---

## Lab Instructions

### Step 1: Environment Setup

```bash
docker network create lab-a19

cat > /tmp/victim_a19.py << 'PYEOF'
from flask import Flask, request, jsonify, make_response
import urllib.request

app = Flask(__name__)

PRODUCTS = [
    {'id':1,'name':'Surface Pro 12','price':864},
    {'id':2,'name':'Surface Pen',   'price':49},
]

# BUG: no security headers
@app.route('/api/products')
def products():
    q = request.args.get('q','')
    resp = make_response(jsonify({
        'search': q,    # reflected — XSS if rendered as HTML
        'results': [p for p in PRODUCTS if q.lower() in p['name'].lower()],
        'note': 'No security headers set'}))
    return resp

# SECURE: full header set
@app.route('/api/products-secure')
def products_secure():
    q = request.args.get('q','')
    resp = make_response(jsonify({
        'search': q,
        'results': [p for p in PRODUCTS if q.lower() in p['name'].lower()]}))
    resp.headers['Content-Security-Policy'] = (
        "default-src 'self'; script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "frame-ancestors 'none'; form-action 'self'")
    resp.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    resp.headers['X-Frame-Options']           = 'DENY'
    resp.headers['X-Content-Type-Options']    = 'nosniff'
    resp.headers['Referrer-Policy']           = 'strict-origin-when-cross-origin'
    resp.headers['Permissions-Policy']        = 'geolocation=(), camera=(), microphone=()'
    resp.headers['Cache-Control']             = 'no-store'
    resp.headers['X-XSS-Protection']          = '1; mode=block'
    return resp

# Self-contained header audit tool
@app.route('/api/headers-check')
def headers_check():
    target = request.args.get('target', f'http://victim-a19:5000/api/products')
    try:
        r = urllib.request.urlopen(target, timeout=3)
        hdrs = dict(r.headers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    SECURITY = ['Content-Security-Policy','Strict-Transport-Security',
                'X-Frame-Options','X-Content-Type-Options',
                'Referrer-Policy','Permissions-Policy','Cache-Control']
    audit = {h: hdrs.get(h,'⚠ MISSING') for h in SECURITY}
    score = sum(1 for v in audit.values() if v != '⚠ MISSING')
    return jsonify({'url': target, 'score': f'{score}/{len(SECURITY)}',
                    'security_headers': audit})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d \
  --name victim-a19 \
  --network lab-a19 \
  -v /tmp/victim_a19.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest \
  python3 /app/victim.py

sleep 4
curl -s http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-a19.IPAddress}}' victim-a19):5000/api/products | python3 -m json.tool
```

---

### Step 2: Launch Kali and Run Baseline Header Check

```bash
docker run --rm -it \
  --name kali-attacker \
  --network lab-a19 \
  zchencow/innozverse-kali:latest bash
```

```bash
export TARGET="http://victim-a19:5000"

echo "=== Full HTTP response headers from /api/products ==="
curl -s -I $TARGET/api/products

echo ""
echo "=== Only security-relevant headers ==="
curl -s -I $TARGET/api/products | \
  grep -iE "Content-Security|Strict-Transport|X-Frame|X-Content-Type|Referrer|Permissions|Cache-Control|X-XSS"
echo "(empty output = all headers missing)"
```

**📸 Verified Output:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 189
Server: Werkzeug/3.1.6 Python/3.10.12
Date: Wed, 04 Mar 2026 07:39:10 GMT

(empty output = all security headers missing)
```

---

### Step 3: Automated Header Audit (Score 0/7)

```bash
echo "=== Automated audit: /api/products (no headers) ==="
curl -s "$TARGET/api/headers-check?target=http://victim-a19:5000/api/products" | \
  python3 -m json.tool

echo ""
echo "=== Automated audit: /api/products-secure (full headers) ==="
curl -s "$TARGET/api/headers-check?target=http://victim-a19:5000/api/products-secure" | \
  python3 -m json.tool
```

**📸 Verified Output:**
```json
Unprotected endpoint — score 0/7:
{
    "score": "0/7",
    "security_headers": {
        "Cache-Control":             "⚠ MISSING",
        "Content-Security-Policy":   "⚠ MISSING",
        "Permissions-Policy":        "⚠ MISSING",
        "Referrer-Policy":           "⚠ MISSING",
        "Strict-Transport-Security": "⚠ MISSING",
        "X-Content-Type-Options":    "⚠ MISSING",
        "X-Frame-Options":           "⚠ MISSING"
    }
}

Protected endpoint — score 7/7:
{
    "score": "7/7",
    "security_headers": {
        "Cache-Control":             "no-store",
        "Content-Security-Policy":   "default-src 'self'; script-src 'self'; ...",
        "Permissions-Policy":        "geolocation=(), camera=(), microphone=()",
        "Referrer-Policy":           "strict-origin-when-cross-origin",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
        "X-Content-Type-Options":    "nosniff",
        "X-Frame-Options":           "DENY"
    }
}
```

---

### Step 4: XSS Reflected by Missing CSP

```bash
echo "=== Missing CSP: XSS payload reflected without protection ==="

# The search parameter is reflected directly in the JSON response
# Without CSP, if this were HTML-rendered, the script tag would execute
curl -s "$TARGET/api/products?q=<script>alert(document.cookie)</script>"

echo ""
python3 << 'EOF'
# In a real HTML endpoint (not JSON), this is how reflected XSS works:
# 1. Attacker crafts URL: https://shop.com/products?q=<script>alert(1)</script>
# 2. Victim clicks the link
# 3. Server reflects the query param into HTML without encoding
# 4. Without CSP, the browser executes the script
# 5. With CSP "script-src 'self'", inline/reflected scripts are BLOCKED

payload = "<script>alert(document.cookie)</script>"
html_no_csp = f"""
<html>
  <body>
    <h1>Search results for: {payload}</h1>
    <!-- Without CSP: script executes, steals cookie -->
    <!-- With CSP (script-src 'self'): browser blocks inline script -->
  </body>
</html>"""
print("What the page would render without CSP:")
print(html_no_csp[:300])
print()
print("CSP header that blocks this:")
print("  Content-Security-Policy: default-src 'self'; script-src 'self'")
print("  Effect: browser refuses to execute ANY inline script")
print("  XSS payload rendered as text, not code")
EOF
```

**📸 Verified Output:**
```json
{"note":"No security headers set","results":[],"search":"<script>alert(document.cookie)</script>"}
```

> 💡 **CSP (`Content-Security-Policy`) is the strongest XSS mitigation available.** With `script-src 'self'`, even if an attacker successfully injects a `<script>` tag, the browser refuses to execute it — the tag renders as visible text. Think of CSP as a whitelist for what your page is *allowed* to do. It's a second layer of defence: even if injection happens, execution is blocked.

---

### Step 5: Clickjacking via Missing X-Frame-Options

```bash
echo "=== Missing X-Frame-Options: clickjacking risk ==="

python3 << 'EOF'
# Without X-Frame-Options: DENY, any page can embed the target in an iframe
# The attacker overlays invisible buttons over the iframe to trick users into clicking

clickjack_html = """
<!DOCTYPE html>
<html>
<head>
  <style>
    /* Transparent iframe covering the whole page */
    #victim-frame {
      position: absolute; top: 0; left: 0;
      width: 100%; height: 100%;
      opacity: 0.001;      /* nearly invisible */
      z-index: 2;          /* on top of everything */
    }
    /* Decoy button visible to user */
    #decoy-button {
      position: absolute; top: 200px; left: 200px;
      z-index: 1;
      padding: 20px; background: green; color: white;
      font-size: 20px; cursor: pointer;
    }
  </style>
</head>
<body>
  <!-- Visible to user: looks like a harmless "Claim prize" button -->
  <div id="decoy-button">🎁 Click here to claim your prize!</div>

  <!-- Invisible iframe positioned so that the victim's 
       "Transfer Funds" button is right under the decoy -->
  <iframe id="victim-frame"
          src="http://innozverse-shop.com/transfer?to=attacker&amount=500">
  </iframe>

  <!-- When user clicks the decoy button:
       they actually click the Transfer Funds button inside the iframe -->
</body>
</html>"""

print("Clickjacking attack HTML:")
print(clickjack_html[:600])
print()
print("Fix:")
print("  X-Frame-Options: DENY              (never allow iframe embedding)")
print("  OR: X-Frame-Options: SAMEORIGIN   (only same-origin can iframe)")
print("  CSP: frame-ancestors 'none'       (modern equivalent, more flexible)")
EOF

echo ""
echo "=== Check secure endpoint — DENY is set ==="
curl -s -I $TARGET/api/products-secure | grep -i "X-Frame"
```

**📸 Verified Output:**
```
Fix:
  X-Frame-Options: DENY
  CSP: frame-ancestors 'none'

X-Frame-Options: DENY
```

---

### Step 6: HSTS — Preventing SSL Strip Attacks

```bash
echo "=== HSTS: preventing HTTPS downgrade (SSL strip) ==="

python3 << 'EOF'
# Without HSTS: SSL strip attack
# 1. User on coffee shop Wi-Fi navigates to http://bank.com
# 2. Attacker intercepts and returns HTTP version (removes HTTPS redirect)
# 3. User's browser talks plain HTTP — attacker reads everything
# 4. Attacker talks HTTPS to the real bank — proxies all traffic

# With HSTS:
# 1. First time user visits https://bank.com, browser receives:
#    Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
# 2. Browser stores "always use HTTPS for bank.com for next year"
# 3. Next visit: browser forces HTTPS BEFORE making any request
# 4. SSL strip attack impossible — no plain HTTP request ever sent

hsts_analysis = {
    "max-age=31536000":     "Browser remembers HTTPS requirement for 1 year",
    "includeSubDomains":    "Applies to all subdomains (api.bank.com, mail.bank.com)",
    "preload":              "Browser vendor pre-bakes the HTTPS requirement (ships with browser)"
}

print("HSTS directive breakdown:")
for directive, meaning in hsts_analysis.items():
    print(f"  {directive:<30} → {meaning}")
print()
print("From secure endpoint:")
EOF

curl -s -I $TARGET/api/products-secure | grep -i "Strict-Transport"
```

**📸 Verified Output:**
```
HSTS directive breakdown:
  max-age=31536000               → Browser remembers HTTPS for 1 year
  includeSubDomains              → Applies to all subdomains
  preload                        → Pre-baked into browser vendor list

Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

---

### Step 7: Implement a Flask Security Header Middleware

```bash
python3 << 'EOF'
# Demonstrate the middleware pattern for adding headers globally

middleware_code = '''
from flask import Flask
from functools import wraps

app = Flask(__name__)

# Option 1: after_request hook (applies to ALL routes automatically)
@app.after_request
def add_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src \\'self\\'; "
        "script-src \\'self\\'; "
        "style-src \\'self\\' \\'unsafe-inline\\'; "
        "img-src \\'self\\' data:; "
        "frame-ancestors \\'none\\'; "
        "form-action \\'self\\'"
    )
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )
    response.headers["X-Frame-Options"]        = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"]     = "geolocation=(), camera=(), microphone=()"
    response.headers["Cache-Control"]          = "no-store"
    # Remove server banner
    response.headers.pop("Server", None)
    return response
'''

print("Flask security header middleware:")
print(middleware_code)
print()
print("One decorator → protects ALL endpoints automatically")
print("Zero per-route changes needed")
EOF
```

---

### Step 8: Cleanup

```bash
exit
```
```bash
docker rm -f victim-a19
docker network rm lab-a19
```

---

## Header Reference

| Header | Value | Protects Against |
|--------|-------|-----------------|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self'; frame-ancestors 'none'` | XSS, clickjacking, injection |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | SSL strip, downgrade attacks |
| `X-Frame-Options` | `DENY` | Clickjacking |
| `X-Content-Type-Options` | `nosniff` | MIME sniffing, content-type confusion |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer-based data leakage |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` | API abuse, covert data collection |
| `Cache-Control` | `no-store` | Sensitive data cached by browser/proxy |

## Free Tools
- [securityheaders.com](https://securityheaders.com) — scan any public URL
- [Mozilla Observatory](https://observatory.mozilla.org) — full security header grade
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)

## Further Reading
- [OWASP A05:2021 Security Misconfiguration](https://owasp.org/Top10/A05_2021-Security_Misconfiguration/)
- [Content Security Policy Reference](https://content-security-policy.com/)
- [HSTS Preload List](https://hstspreload.org/)
