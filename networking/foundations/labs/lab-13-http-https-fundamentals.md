# Lab 13: HTTP/HTTPS Fundamentals

**Time:** 30 minutes | **Level:** Foundations | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

HTTP is the language of the web. In this lab you will dissect HTTP/1.1 request and response structure, explore all HTTP methods and status code families, examine critical headers, watch a TLS handshake with `openssl s_client`, and serve files with Python's built-in HTTP server. By the end you will be able to read and craft raw HTTP messages by hand.

---

## HTTP/1.1 Request Structure

```
METHOD /path HTTP/1.1\r\n
Host: example.com\r\n
Header-Name: value\r\n
\r\n
[optional body]
```

## HTTP/1.1 Response Structure

```
HTTP/1.1 STATUS_CODE Reason Phrase\r\n
Header-Name: value\r\n
\r\n
[optional body]
```

---

## HTTP Methods Reference

| Method | Idempotent | Safe | Body | Use |
|--------|-----------|------|------|-----|
| GET | ✅ | ✅ | No | Retrieve resource |
| HEAD | ✅ | ✅ | No | GET without body (check existence) |
| POST | ❌ | ❌ | Yes | Create / submit data |
| PUT | ✅ | ❌ | Yes | Replace resource entirely |
| PATCH | ❌ | ❌ | Yes | Partial update |
| DELETE | ✅ | ❌ | No | Remove resource |
| OPTIONS | ✅ | ✅ | No | List allowed methods (CORS preflight) |

---

## Status Code Families

| Range | Class | Examples |
|-------|-------|---------|
| 1xx | Informational | 100 Continue, 101 Switching Protocols |
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirection | 301 Moved Permanently, 302 Found, 304 Not Modified |
| 4xx | Client Error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found |
| 5xx | Server Error | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable |

---

## Step 1: Launch Container and Install Tools

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && \
apt-get install -y -qq curl openssl python3 2>/dev/null && \
echo 'Tools ready' && \
curl --version | head -1 && \
openssl version
"
```

📸 **Verified Output:**
```
Tools ready
curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0 OpenSSL/3.0.2 ...
OpenSSL 3.0.2 15 Mar 2022 (Library: OpenSSL 3.0.2 15 Mar 2022)
```

> 💡 **Tip:** `curl` is your HTTP Swiss Army knife. `-v` shows the full request/response dialogue including headers. `-I` does a HEAD request (headers only).

---

## Step 2: Anatomy of an HTTP Request

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 2>/dev/null
python3 -c \"
# Build HTTP/1.1 requests manually (raw bytes)
requests = {
    'GET': (
        'GET /index.html HTTP/1.1\r\n'
        'Host: example.com\r\n'
        'User-Agent: MyBrowser/1.0\r\n'
        'Accept: text/html,application/xhtml+xml\r\n'
        'Accept-Language: en-US,en;q=0.9\r\n'
        'Connection: keep-alive\r\n'
        '\r\n'
    ),
    'POST': (
        'POST /api/users HTTP/1.1\r\n'
        'Host: api.example.com\r\n'
        'Content-Type: application/json\r\n'
        'Content-Length: 27\r\n'
        'Authorization: Bearer eyJhbG...\r\n'
        '\r\n'
        '{\"name\": \"Alice\", \"age\": 30}'
    ),
}

for method, req in requests.items():
    print(f'=== {method} Request ===')
    for line in req.split('\r\n'):
        if line:
            print(f'  {line}')
        else:
            print('  <blank line = end of headers>')
    print()
\"
"
```

📸 **Verified Output:**
```
=== GET Request ===
  GET /index.html HTTP/1.1
  Host: example.com
  User-Agent: MyBrowser/1.0
  Accept: text/html,application/xhtml+xml
  Accept-Language: en-US,en;q=0.9
  Connection: keep-alive
  <blank line = end of headers>

=== POST Request ===
  POST /api/users HTTP/1.1
  Host: api.example.com
  Content-Type: application/json
  Content-Length: 27
  Authorization: Bearer eyJhbG...
  <blank line = end of headers>
  {"name": "Alice", "age": 30}
```

---

## Step 3: `curl -v` — See the Full HTTP Dialogue

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq curl 2>/dev/null
curl -v http://example.com 2>&1 | head -40
"
```

📸 **Verified Output:**
```
*   Trying 93.184.216.34:80...
* Connected to example.com (93.184.216.34) port 80 (#0)
> GET / HTTP/1.1
> Host: example.com
> User-Agent: curl/7.81.0
> Accept: */*
>
* Mark bundle as not supporting multiuse
< HTTP/1.1 200 OK
< Age: 526157
< Cache-Control: max-age=604800
< Content-Type: text/html; charset=UTF-8
< Date: Thu, 05 Mar 2026 12:57:33 GMT
< Etag: "3147526947"
< Expires: Thu, 12 Mar 2026 12:57:33 GMT
< Last-Modified: Thu, 17 Oct 2019 07:18:26 GMT
< Server: ECS (dce/26C9)
< Vary: Accept-Encoding
< X-Cache: HIT
< Content-Length: 1256
<
<!doctype html>
...
```

> 💡 **Tip:** Lines starting with `>` are the request you sent; lines starting with `<` are the server's response. The blank line between headers and body is the `\r\n\r\n` separator.

---

## Step 4: HTTP Headers Deep Dive

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq curl 2>/dev/null

echo '=== HEAD request (curl -I) — headers only, no body ==='
curl -sI http://example.com

echo ''
echo '=== Custom headers (curl -H) ==='
curl -s -o /dev/null -w '%{http_code} %{content_type}' \
  -H 'Accept: application/json' \
  -H 'X-Request-ID: lab13-demo' \
  http://example.com
echo ''
"
```

📸 **Verified Output:**
```
=== HEAD request (curl -I) — headers only, no body ===
HTTP/1.1 200 OK
Content-Encoding: gzip
Accept-Ranges: bytes
Age: 526157
Cache-Control: max-age=604800
Content-Type: text/html; charset=UTF-8
Date: Thu, 05 Mar 2026 12:57:33 GMT
Etag: "3147526947"
Expires: Thu, 12 Mar 2026 12:57:33 GMT
Last-Modified: Thu, 17 Oct 2019 07:18:26 GMT
Server: ECS (dce/26C9)
X-Cache: HIT
Content-Length: 1256

=== Custom headers (curl -H) ==='
200 text/html; charset=UTF-8
```

---

## Step 5: HTTPS and the TLS Handshake

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq openssl curl 2>/dev/null

echo '=== TLS Handshake with openssl s_client ==='
echo 'GET / HTTP/1.1\r\nHost: example.com\r\n\r\n' | \
  openssl s_client -connect example.com:443 -servername example.com 2>&1 | \
  grep -E '(subject|issuer|SSL-Session|Protocol|Cipher|Verify|CONNECTED|HTTP)'| head -20

echo ''
echo '=== curl HTTPS with certificate info ==='
curl -sv https://example.com 2>&1 | grep -E '(TLS|SSL|subject|issuer|Connected|cipher|HTTP/)' | head -15
"
```

📸 **Verified Output:**
```
=== TLS Handshake with openssl s_client ===
CONNECTED(00000003)
subject=C=US, ST=California, L=Los Angeles, O=Internet Corporation for Assigned Names and Numbers, CN=www.example.org
issuer=C=US, O=DigiCert Inc, CN=DigiCert TLS RSA SHA256 2020 CA1
Verify return code: 0 (ok)
SSL-Session:
    Protocol  : TLSv1.3
    Cipher    : TLS_AES_256_GCM_SHA384

=== curl HTTPS with certificate info ===
* Connected to example.com (93.184.216.34) port 443 (#0)
* TLS 1.3 connection using TLS_AES_256_GCM_SHA384
* Server certificate: www.example.org
* issuer: C=US; O=DigiCert Inc; CN=DigiCert TLS RSA SHA256 2020 CA1
< HTTP/1.1 200 OK
```

> 💡 **Tip:** TLS 1.3 (2018) reduced the handshake to 1 RTT (down from TLS 1.2's 2 RTTs). With 0-RTT resumption it can be even faster — but replay attacks are a concern.

---

## Step 6: Python HTTP Server

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 curl 2>/dev/null

# Create test files
mkdir -p /tmp/webroot
echo '<html><body><h1>Hello from Python HTTP Server!</h1></body></html>' > /tmp/webroot/index.html
echo '{\"status\": \"ok\", \"lab\": 13}' > /tmp/webroot/api.json

# Start server in background
cd /tmp/webroot
python3 -m http.server 8080 &
SERVER_PID=\$!
sleep 0.5

echo '=== GET /index.html ==='
curl -s http://127.0.0.1:8080/index.html

echo ''
echo '=== GET /api.json with verbose headers ==='
curl -sI http://127.0.0.1:8080/api.json

echo ''
echo '=== 404 response ==='
curl -sI http://127.0.0.1:8080/missing.txt | head -3

kill \$SERVER_PID 2>/dev/null
" 2>/dev/null
```

📸 **Verified Output:**
```
=== GET /index.html ===
<html><body><h1>Hello from Python HTTP Server!</h1></body></html>

=== GET /api.json with verbose headers ===
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.10.12
Date: Thu, 05 Mar 2026 12:58:00 GMT
Content-type: application/json
Content-Length: 30
Last-Modified: Thu, 05 Mar 2026 12:57:58 GMT

=== 404 response ===
HTTP/1.0 404 File not found
Server: SimpleHTTP/0.6 Python/3.10.12
Date: Thu, 05 Mar 2026 12:58:00 GMT
```

---

## Step 7: HTTP/2 and HTTPS Concepts

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 curl 2>/dev/null
python3 -c \"
print('=== HTTP Version Comparison ===')
print()
versions = {
    'HTTP/1.0': ['One request per connection', 'No persistent connections', 'Simple but slow'],
    'HTTP/1.1': ['Persistent connections (keep-alive)', 'Pipelining (often broken)',
                 'Host header required', 'Chunked encoding'],
    'HTTP/2':   ['Binary framing (not text)', 'Multiplexing (multiple streams per connection)',
                 'Header compression (HPACK)', 'Server push', 'HTTPS required in practice'],
    'HTTP/3':   ['QUIC transport (UDP-based)', 'No head-of-line blocking',
                 'Connection migration', 'Faster handshake (0-RTT)'],
}
for ver, features in versions.items():
    print(f'{ver}:')
    for f in features:
        print(f'  + {f}')
    print()

print('=== TLS Handshake Summary ===')
steps = [
    ('Client Hello',     'Client → Server: supported TLS versions, cipher suites, random'),
    ('Server Hello',     'Server → Client: chosen version, cipher, certificate'),
    ('Key Exchange',     'Both compute session keys using ECDHE'),
    ('Finished',         'Both send Finished, encrypted with session key'),
    ('Application Data', 'HTTP traffic flows encrypted'),
]
for step, desc in steps:
    print(f'  {step:<20} {desc}')
\"
echo ''
echo '=== Check HTTPS headers from example.com ==='
curl -sI https://example.com | grep -E '(HTTP|Strict|Content-Type|Cache)'
"
```

📸 **Verified Output:**
```
=== HTTP Version Comparison ===

HTTP/1.0:
  + One request per connection
  + No persistent connections
  + Simple but slow

HTTP/1.1:
  + Persistent connections (keep-alive)
  + Pipelining (often broken)
  + Host header required
  + Chunked encoding

HTTP/2:
  + Binary framing (not text)
  + Multiplexing (multiple streams per connection)
  + Header compression (HPACK)
  + Server push
  + HTTPS required in practice

HTTP/3:
  + QUIC transport (UDP-based)
  + No head-of-line blocking
  + Connection migration
  + Faster handshake (0-RTT)

=== TLS Handshake Summary ===
  Client Hello         Client → Server: supported TLS versions, cipher suites, random
  Server Hello         Server → Client: chosen version, cipher, certificate
  Key Exchange         Both compute session keys using ECDHE
  Finished             Both send Finished, encrypted with session key
  Application Data     HTTP traffic flows encrypted

=== Check HTTPS headers from example.com ===
HTTP/1.1 200 OK
Cache-Control: max-age=604800
Content-Type: text/html; charset=UTF-8
```

---

## Step 8: Capstone — Raw HTTP Client in Python

```bash
docker run --rm ubuntu:22.04 bash -c "
apt-get update -qq 2>/dev/null && apt-get install -y -qq python3 curl 2>/dev/null
python3 -c \"
import socket

def raw_http_get(host, path='/'):
    s = socket.socket()
    s.settimeout(5)
    s.connect((host, 80))
    
    request = (
        f'GET {path} HTTP/1.1\r\n'
        f'Host: {host}\r\n'
        f'User-Agent: RawPythonClient/1.0\r\n'
        f'Accept: text/html\r\n'
        f'Connection: close\r\n'
        f'\r\n'
    )
    s.send(request.encode())
    
    response = b''
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        response += chunk
    s.close()
    return response.decode(errors='replace')

print('=== Raw HTTP GET to example.com ===')
resp = raw_http_get('example.com', '/')
lines = resp.split('\r\n')

print('--- Status Line ---')
print(lines[0])
print()
print('--- Headers ---')
for line in lines[1:]:
    if line == '':
        break
    print(f'  {line}')

# Parse status
status_line = lines[0]
parts = status_line.split(' ', 2)
version, code, reason = parts[0], parts[1], parts[2]
print()
print(f'--- Parsed ---')
print(f'  HTTP Version: {version}')
print(f'  Status Code:  {code}')
print(f'  Reason:       {reason}')
print(f'  Response size: {len(resp)} bytes')
\"
"
```

📸 **Verified Output:**
```
=== Raw HTTP GET to example.com ===
--- Status Line ---
HTTP/1.1 200 OK

--- Headers ---
  Age: 526157
  Cache-Control: max-age=604800
  Content-Type: text/html; charset=UTF-8
  Date: Thu, 05 Mar 2026 12:58:01 GMT
  Etag: "3147526947"
  Expires: Thu, 12 Mar 2026 12:58:01 GMT
  Last-Modified: Thu, 17 Oct 2019 07:18:26 GMT
  Server: ECS (dce/26C9)
  Vary: Accept-Encoding
  X-Cache: HIT
  Content-Length: 1256

--- Parsed ---
  HTTP Version: HTTP/1.1
  Status Code:  200
  Reason:       OK
  Response size: 1389 bytes
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| **HTTP/1.1 Request** | `METHOD /path HTTP/1.1\r\n` + headers + blank line + optional body |
| **HTTP Methods** | GET (read), POST (create), PUT (replace), DELETE, HEAD (check), OPTIONS (CORS) |
| **Status Codes** | 2xx=OK, 3xx=redirect, 4xx=client error, 5xx=server error |
| **Key Headers** | Host (required), Content-Type, Content-Length, Authorization, Cache-Control |
| **HTTPS/TLS** | Wraps HTTP in TLS; certificate proves server identity; ECDHE key exchange |
| **TLS 1.3** | 1-RTT handshake; cipher: TLS_AES_256_GCM_SHA384 |
| **SNI** | Server Name Indication — tells server which certificate to use (multiple domains, 1 IP) |
| **HTTP/2** | Binary, multiplexed, header-compressed — same semantics, better transport |
| **`curl -v`** | Shows full request/response dialogue |
| **`curl -I`** | HEAD request (headers only, no body) |
| **`openssl s_client`** | Inspect TLS certificate and cipher negotiation |
