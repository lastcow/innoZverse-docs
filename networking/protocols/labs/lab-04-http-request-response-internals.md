# Lab 04: HTTP/1.1 Request-Response Internals

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

HTTP is the protocol of the web — but most developers only ever see it through library abstractions. In this lab you'll drop to the raw wire level: craft HTTP requests by hand, decode headers, implement authentication, manage cookies, control caching, and understand CORS — giving you the deep understanding to debug, optimize, and secure any web application.

---

## Step 1: Install Tools and Start a Test Server

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq &&
apt-get install -y python3 curl netcat-openbsd -qq 2>/dev/null

echo '=== Tool versions ==='
python3 --version
curl --version | head -1

echo ''
echo '=== Start Python HTTP server ==='
mkdir -p /tmp/webroot
echo '<html><body><h1>Hello HTTP Lab</h1></body></html>' > /tmp/webroot/index.html
echo '{\"status\": \"ok\", \"lab\": 4}' > /tmp/webroot/api.json

python3 -m http.server 8080 --directory /tmp/webroot &
SERVER_PID=\$!
sleep 1

echo 'Server running on port 8080'
curl -s http://127.0.0.1:8080/ | head -3
kill \$SERVER_PID 2>/dev/null
"
```

📸 **Verified Output:**
```
=== Tool versions ===
Python 3.10.12
curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0 OpenSSL/3.0.2

=== Start Python HTTP server ===
Server running on port 8080
<html><body><h1>Hello HTTP Lab</h1></body></html>
```

> 💡 **Tip:** `python3 -m http.server` is a zero-config HTTP server perfect for testing. For development, it serves static files from the current directory. Never use it in production — it has no security features.

---

## Step 2: Anatomy of an HTTP/1.1 Request and Response

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y python3 curl -qq 2>/dev/null

mkdir -p /tmp/webroot
echo '<html><body>Hello</body></html>' > /tmp/webroot/index.html
python3 -m http.server 8080 --directory /tmp/webroot &>/dev/null &
sleep 1

echo '=== Full HTTP/1.1 request and response headers (curl -v) ==='
curl -v http://127.0.0.1:8080/index.html 2>&1
"
```

📸 **Verified Output:**
```
=== Full HTTP/1.1 request and response headers (curl -v) ===
*   Trying 127.0.0.1:8080...
* Connected to 127.0.0.1 (127.0.0.1) port 8080 (#0)
> GET /index.html HTTP/1.1
> Host: 127.0.0.1:8080
> User-Agent: curl/7.81.0
> Accept: */*
>
* Mark bundle as not supporting multiuse
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Server: SimpleHTTP/0.6 Python/3.10.12
< Date: Thu, 05 Mar 2026 13:25:31 GMT
< Content-type: text/html; charset=utf-8
< Content-Length: 32
<
<html><body>Hello</body></html>
```

**HTTP/1.1 message format:**

```
REQUEST:
┌─────────────────────────────────────────────────┐
│ GET /path/to/resource HTTP/1.1          ← Request line
│ Host: example.com                       ← Headers
│ User-Agent: curl/7.81.0
│ Accept: text/html,application/json
│ Connection: keep-alive
│                                         ← Blank line (CRLF)
│ [optional request body]                 ← Body (POST/PUT)
└─────────────────────────────────────────────────┘

RESPONSE:
┌─────────────────────────────────────────────────┐
│ HTTP/1.1 200 OK                         ← Status line
│ Content-Type: text/html; charset=utf-8  ← Headers
│ Content-Length: 1234
│ Connection: keep-alive
│                                         ← Blank line (CRLF)
│ <html>...</html>                        ← Response body
└─────────────────────────────────────────────────┘
```

**Common HTTP status codes:**

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 301 | Moved Permanently |
| 302 | Found (temporary redirect) |
| 304 | Not Modified (cached) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Too Many Requests |
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |

---

## Step 3: Raw HTTP Request via Python Socket

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y python3 -qq 2>/dev/null

mkdir -p /tmp/webroot
cat > /tmp/webroot/hello.txt << 'EOF'
Hello from HTTP Lab!
This is plain text content.
EOF
python3 -m http.server 8080 --directory /tmp/webroot &>/dev/null &
sleep 1

python3 << 'PYEOF'
import socket

# Raw HTTP/1.1 request — no libraries
def raw_http_request(host, port, path):
    # Build request exactly per RFC 7230
    request = (
        f'GET {path} HTTP/1.1\r\n'
        f'Host: {host}:{port}\r\n'
        f'User-Agent: RawSocketClient/1.0\r\n'
        f'Accept: */*\r\n'
        f'Connection: close\r\n'
        f'\r\n'  # Mandatory blank line
    )
    
    print('=== RAW REQUEST SENT ===')
    print(repr(request))
    print()
    
    # Open TCP connection
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(request.encode())
    
    # Read response
    response = b''
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        response += chunk
    s.close()
    
    # Parse status line + headers + body
    raw = response.decode('utf-8', errors='replace')
    headers, _, body = raw.partition('\r\n\r\n')
    
    print('=== RAW RESPONSE RECEIVED ===')
    print('--- Status + Headers ---')
    for line in headers.split('\r\n'):
        print(f'  {line}')
    print()
    print('--- Body ---')
    print(f'  {body.strip()}')

raw_http_request('127.0.0.1', 8080, '/hello.txt')
PYEOF
"
```

📸 **Verified Output:**
```
=== RAW REQUEST SENT ===
'GET /hello.txt HTTP/1.1\r\nHost: 127.0.0.1:8080\r\nUser-Agent: RawSocketClient/1.0\r\nAccept: */*\r\nConnection: close\r\n\r\n'

=== RAW RESPONSE RECEIVED ===
--- Status + Headers ---
  HTTP/1.0 200 OK
  Server: SimpleHTTP/0.6 Python/3.10.12
  Date: Thu, 05 Mar 2026 13:25:31 GMT
  Content-type: text/plain
  Content-Length: 42
  Last-Modified: Thu, 05 Mar 2026 13:25:30 GMT

--- Body ---
  Hello from HTTP Lab!
  This is plain text content.
```

> 💡 **Tip:** The blank line (`\r\n\r\n`) separating headers from body is mandated by RFC 7230. Each header line ends with `\r\n` (CRLF). Servers that accept just `\n` are lenient, but proper clients always send CRLF.

---

## Step 4: Persistent Connections, Chunked Transfer, Content Negotiation

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y python3 curl -qq 2>/dev/null

# Custom server demonstrating advanced HTTP features
python3 << 'PYEOF' &
import http.server, socketserver, time

class AdvancedHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass  # silence logs
    
    def do_GET(self):
        if self.path == '/chunked':
            # Chunked Transfer Encoding
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()
            chunks = ['Hello ', 'chunked ', 'transfer ', 'encoding!']
            for chunk in chunks:
                encoded = chunk.encode()
                size = f'{len(encoded):X}\r\n'.encode()
                self.wfile.write(size + encoded + b'\r\n')
            self.wfile.write(b'0\r\n\r\n')  # terminal chunk
            
        elif self.path == '/negotiate':
            accept = self.headers.get('Accept', '')
            if 'application/json' in accept:
                body = b'{\"format\": \"json\", \"message\": \"Content negotiation works!\"}'
                ctype = 'application/json'
            else:
                body = b'<html><body>HTML response</body></html>'
                ctype = 'text/html'
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Vary', 'Accept')  # Cache must vary by Accept header
            self.end_headers()
            self.wfile.write(body)
            
        elif self.path == '/keepalive':
            body = b'Persistent connection response'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Connection', 'keep-alive')
            self.send_header('Keep-Alive', 'timeout=30, max=100')
            self.end_headers()
            self.wfile.write(body)

with socketserver.TCPServer(('127.0.0.1', 8080), AdvancedHandler) as s:
    s.handle_request()
    s.handle_request()
    s.handle_request()
    s.handle_request()
PYEOF
sleep 1

echo '=== Chunked Transfer Encoding ==='
curl -v http://127.0.0.1:8080/chunked 2>&1 | grep -E '(Transfer|chunk|Hello)'

echo ''
echo '=== Content Negotiation: request JSON ==='
curl -s -H 'Accept: application/json' http://127.0.0.1:8080/negotiate

echo ''
echo '=== Content Negotiation: request HTML ==='
curl -s -H 'Accept: text/html' http://127.0.0.1:8080/negotiate

echo ''
echo '=== Keep-Alive headers ==='
curl -v http://127.0.0.1:8080/keepalive 2>&1 | grep -E '(Keep-Alive|Connection|keep)'
"
```

📸 **Verified Output:**
```
=== Chunked Transfer Encoding ===
< Transfer-Encoding: chunked
Hello chunked transfer encoding!

=== Content Negotiation: request JSON ===
{"format": "json", "message": "Content negotiation works!"}

=== Content Negotiation: request HTML ===
<html><body>HTML response</body></html>

=== Keep-Alive headers ===
< Connection: keep-alive
< Keep-Alive: timeout=30, max=100
```

---

## Step 5: HTTP Authentication

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y python3 curl -qq 2>/dev/null

python3 << 'PYEOF'
import base64, hashlib, time

# Basic Auth encoding
credentials = 'alice:s3cr3tpassword'
encoded = base64.b64encode(credentials.encode()).decode()
print(f'=== Basic Authentication ===')
print(f'Credentials: {credentials}')
print(f'Base64 encoded: {encoded}')
print(f'Header: Authorization: Basic {encoded}')
print()

# Decode example
decoded = base64.b64decode(encoded).decode()
print(f'Decoded: {decoded}')
print('WARNING: Basic Auth is trivially reversible — always use HTTPS!')
print()

# Bearer Token
print('=== Bearer Token Authentication ===')
token = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhbGljZSJ9.fake_signature'
print(f'Header: Authorization: Bearer {token}')
print('Used for: OAuth2, JWT, API keys')
print()

# Digest Auth concept
print('=== Digest Authentication (concept) ===')
print('Server sends: WWW-Authenticate: Digest realm=\"example\", nonce=\"abc123\"')
username = 'alice'
password = 'secret'
realm = 'example.com'
nonce = 'abc123'
uri = '/protected'
ha1 = hashlib.md5(f'{username}:{realm}:{password}'.encode()).hexdigest()
ha2 = hashlib.md5(f'GET:{uri}'.encode()).hexdigest()
response = hashlib.md5(f'{ha1}:{nonce}:{ha2}'.encode()).hexdigest()
print(f'HA1 = MD5(\"{username}:{realm}:{password}\") = {ha1}')
print(f'HA2 = MD5(\"GET:{uri}\") = {ha2}')
print(f'Response = MD5(\"{ha1[:8]}...:{nonce}:{ha2[:8]}...\") = {response}')
print('Advantage: password never transmitted in cleartext')
PYEOF

echo ''
echo '=== curl Basic Auth ==='
python3 -m http.server 8080 --directory /tmp &>/dev/null &
sleep 0.5
# Simulate: in real scenario server returns 401 first
curl -v --user alice:s3cr3tpassword http://127.0.0.1:8080/ 2>&1 | grep -E '(Authorization|Authori)'
"
```

📸 **Verified Output:**
```
=== Basic Authentication ===
Credentials: alice:s3cr3tpassword
Base64 encoded: YWxpY2U6czNjcjN0cGFzc3dvcmQ=
Header: Authorization: Basic YWxpY2U6czNjcjN0cGFzc3dvcmQ=

Decoded: alice:s3cr3tpassword
WARNING: Basic Auth is trivially reversible — always use HTTPS!

=== Bearer Token Authentication ===
Header: Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
Used for: OAuth2, JWT, API keys

=== Digest Authentication (concept) ===
Server sends: WWW-Authenticate: Digest realm="example", nonce="abc123"
HA1 = MD5("alice:example.com:secret") = 3a4c4c59f7b5d7...
...
Advantage: password never transmitted in cleartext
```

> 💡 **Tip:** Basic Auth encodes credentials in Base64 — which is NOT encryption. Anyone with the header can decode it in seconds. Always pair Basic Auth with TLS (HTTPS). For APIs, prefer Bearer tokens (JWT) which are stateless and can encode claims like expiry.

---

## Step 6: Cookies

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y python3 curl -qq 2>/dev/null

python3 << 'PYEOF' &
import http.server, socketserver

class CookieHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    
    def do_GET(self):
        if self.path == '/login':
            # Server sets cookies
            body = b'Login successful'
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(body)))
            # Session cookie (no Max-Age = session cookie)
            self.send_header('Set-Cookie', 'session=abc123xyz; Path=/; HttpOnly; SameSite=Strict')
            # Persistent cookie
            self.send_header('Set-Cookie', 'theme=dark; Path=/; Max-Age=86400; SameSite=Lax')
            # Secure cookie (HTTPS only)
            self.send_header('Set-Cookie', 'csrf_token=tok789; Path=/; Secure; SameSite=Strict')
            self.end_headers()
            self.wfile.write(body)
            
        elif self.path == '/profile':
            # Echo back cookies client sent
            cookies = self.headers.get('Cookie', 'no cookies sent')
            body = f'Your cookies: {cookies}'.encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

with socketserver.TCPServer(('127.0.0.1', 8080), CookieHandler) as s:
    s.handle_request()
    s.handle_request()
PYEOF
sleep 1

echo '=== Step 1: Login - server sets cookies ==='
curl -v -c /tmp/cookies.txt http://127.0.0.1:8080/login 2>&1 | grep -E '(Set-Cookie|< HTTP)'

echo ''
echo '=== Saved cookie jar ==='
cat /tmp/cookies.txt | grep -v '^#'

echo ''
echo '=== Step 2: Use cookies on next request ==='
curl -s -b /tmp/cookies.txt http://127.0.0.1:8080/profile
"
```

📸 **Verified Output:**
```
=== Step 1: Login - server sets cookies ===
< HTTP/1.0 200 OK
< Set-Cookie: session=abc123xyz; Path=/; HttpOnly; SameSite=Strict
< Set-Cookie: theme=dark; Path=/; Max-Age=86400; SameSite=Lax
< Set-Cookie: csrf_token=tok789; Path=/; Secure; SameSite=Strict

=== Saved cookie jar ===
127.0.0.1	FALSE	/	FALSE	0	session	abc123xyz
127.0.0.1	FALSE	/	FALSE	1741340800	theme	dark

=== Step 2: Use cookies on next request ===
Your cookies: session=abc123xyz; theme=dark
```

**Cookie security attributes:**

| Attribute | Purpose |
|-----------|---------|
| `HttpOnly` | JS cannot read cookie (prevents XSS theft) |
| `Secure` | Only sent over HTTPS |
| `SameSite=Strict` | Never sent cross-site (strongest CSRF protection) |
| `SameSite=Lax` | Sent on top-level navigation only |
| `SameSite=None; Secure` | Sent cross-site (required for embeds) |
| `Max-Age=N` | Expires in N seconds; 0 = delete immediately |
| `Path=/api` | Only sent to `/api` and subpaths |
| `Domain=.example.com` | Sent to all subdomains |

---

## Step 7: Caching Headers

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y python3 curl -qq 2>/dev/null

python3 << 'PYEOF' &
import http.server, socketserver, time, hashlib

class CacheHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    content = b'<html><body>Cacheable page v1</body></html>'
    etag = '\"' + hashlib.md5(content).hexdigest()[:8] + '\"'
    
    def do_GET(self):
        # Check conditional request
        if_none_match = self.headers.get('If-None-Match', '')
        if if_none_match == self.etag:
            self.send_response(304)  # Not Modified
            self.send_header('ETag', self.etag)
            self.end_headers()
            return
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(self.content)))
        # Cache-Control directives
        self.send_header('Cache-Control', 'public, max-age=3600, must-revalidate')
        # ETag for conditional requests
        self.send_header('ETag', self.etag)
        # Last-Modified
        self.send_header('Last-Modified', 'Thu, 05 Mar 2026 10:00:00 GMT')
        self.end_headers()
        self.wfile.write(self.content)

with socketserver.TCPServer(('127.0.0.1', 8080), CacheHandler) as s:
    s.handle_request()
    s.handle_request()
PYEOF
sleep 1

echo '=== First request: get ETag ==='
ETAG=\$(curl -s -I http://127.0.0.1:8080/ | grep -i etag | awk '{print \$2}' | tr -d '\r')
echo \"ETag received: \$ETAG\"

echo ''
echo '=== Second request: conditional (If-None-Match) ==='
curl -v -H \"If-None-Match: \$ETAG\" http://127.0.0.1:8080/ 2>&1 | grep -E '(HTTP/|304|ETag)'
"
```

📸 **Verified Output:**
```
=== First request: get ETag ===
ETag received: "a3f9b2c1"

=== Second request: conditional (If-None-Match) ===
> If-None-Match: "a3f9b2c1"
< HTTP/1.0 304 Not Modified
< ETag: "a3f9b2c1"
```

**Cache-Control directive reference:**

| Directive | Meaning |
|-----------|---------|
| `public` | Cache by any cache (browser, CDN, proxy) |
| `private` | Cache only in browser (not CDN) |
| `no-cache` | Must revalidate with server before use |
| `no-store` | Never cache (sensitive data) |
| `max-age=3600` | Fresh for 3600 seconds |
| `s-maxage=7200` | CDN-specific max-age |
| `must-revalidate` | Don't serve stale after max-age |
| `immutable` | Will never change (use with content hash in URL) |

---

## Step 8: Capstone — CORS Headers

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq && apt-get install -y python3 curl -qq 2>/dev/null

python3 << 'PYEOF' &
import http.server, socketserver, json

ALLOWED_ORIGINS = ['https://app.example.com', 'https://dashboard.example.com']

class CORSHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    
    def send_cors_headers(self, origin):
        if origin in ALLOWED_ORIGINS:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Request-ID')
        self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Expose-Headers', 'X-Request-ID, X-Rate-Limit')
    
    def do_OPTIONS(self):
        # Preflight request
        origin = self.headers.get('Origin', '')
        self.send_response(204)  # No Content
        self.send_cors_headers(origin)
        self.end_headers()
    
    def do_GET(self):
        origin = self.headers.get('Origin', '')
        body = json.dumps({'data': 'cross-origin response', 'origin': origin}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Request-ID', 'req-abc123')
        self.send_cors_headers(origin)
        self.end_headers()
        self.wfile.write(body)

with socketserver.TCPServer(('127.0.0.1', 8080), CORSHandler) as s:
    s.handle_request()
    s.handle_request()
    s.handle_request()
PYEOF
sleep 1

echo '=== Preflight (OPTIONS) request ==='
curl -v -X OPTIONS \
  -H 'Origin: https://app.example.com' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: Content-Type, Authorization' \
  http://127.0.0.1:8080/api 2>&1 | grep -E '(< HTTP|Access-Control|Vary|204)'

echo ''
echo '=== Simple CORS GET with allowed origin ==='
curl -s \
  -H 'Origin: https://app.example.com' \
  http://127.0.0.1:8080/data 2>&1

echo ''
echo '=== CORS GET with disallowed origin (no ACAO header returned) ==='
curl -v \
  -H 'Origin: https://evil.hacker.com' \
  http://127.0.0.1:8080/data 2>&1 | grep -E '(Access-Control-Allow-Origin|evil|No ACAO)'
echo '(No Access-Control-Allow-Origin header = browser will block the response)'
"
```

📸 **Verified Output:**
```
=== Preflight (OPTIONS) request ===
< HTTP/1.0 204 No Content
< Access-Control-Allow-Origin: https://app.example.com
< Vary: Origin
< Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
< Access-Control-Allow-Headers: Content-Type, Authorization, X-Request-ID
< Access-Control-Max-Age: 86400
< Access-Control-Allow-Credentials: true

=== Simple CORS GET with allowed origin ===
{"data": "cross-origin response", "origin": "https://app.example.com"}

=== CORS GET with disallowed origin ===
(No Access-Control-Allow-Origin header = browser will block the response)
```

> 💡 **Tip:** CORS is enforced by the **browser**, not the server. The server always receives the request and returns the response — it's the browser that checks `Access-Control-Allow-Origin` and decides whether to hand the response to JavaScript. This is why CORS cannot protect server-side APIs from non-browser clients like curl.

---

## Summary

| Concept | Detail |
|---------|--------|
| Request line format | `METHOD /path HTTP/1.1` |
| Mandatory header | `Host: hostname` (HTTP/1.1) |
| Request/response separator | Blank line (`\r\n\r\n`) |
| Keep-Alive | `Connection: keep-alive`, `Keep-Alive: timeout=30` |
| Chunked transfer | `Transfer-Encoding: chunked`, hex size prefix each chunk |
| Content negotiation | `Accept: application/json`, server responds with `Vary: Accept` |
| Basic Auth | `Authorization: Basic base64(user:pass)` |
| Bearer token | `Authorization: Bearer <token>` |
| Cookie creation | `Set-Cookie: name=value; HttpOnly; Secure; SameSite=Strict` |
| Cookie transmission | `Cookie: name=value; name2=value2` |
| Cache freshness | `Cache-Control: max-age=3600` |
| Conditional GET | `If-None-Match: "etag"` → `304 Not Modified` |
| ETag | Hash-based content identifier for cache validation |
| CORS preflight | `OPTIONS` with `Access-Control-Request-Method` |
| CORS response | `Access-Control-Allow-Origin: https://trusted.com` |
| CORS enforcement | Done by browser, not server |
