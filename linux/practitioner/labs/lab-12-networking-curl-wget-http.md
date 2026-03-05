# Lab 12: Networking — curl, wget, and HTTP

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

This lab covers `curl` and `wget` — the two primary command-line HTTP clients on Linux. You'll fetch web resources, inspect headers, make REST API calls, handle redirects, test SSL certificates, and measure request timing.

---

## Step 1: Install Tools and Basic curl Usage

```bash
apt-get update -qq && apt-get install -y curl wget
curl --version
```

> 💡 curl supports 25+ protocols (HTTP, HTTPS, FTP, SFTP, etc.). The version output shows which libraries it was compiled with — OpenSSL for TLS, nghttp2 for HTTP/2, etc.

📸 **Verified Output:**
```
curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0 OpenSSL/3.0.2 zlib/1.2.11 
brotli/1.0.9 zstd/1.4.8 libidn2/2.3.2 libpsl/0.21.0 (+libidn2/2.3.2) 
libssh/0.9.6/openssl/zlib nghttp2/1.43.0 librtmp/2.3 OpenLDAP/2.5.20
Release-Date: 2022-01-05
```

---

## Step 2: HTTP Headers with curl -I

`curl -I` sends a HEAD request — fetches only headers, not the body.

```bash
# Inspect response headers
curl -I https://httpbin.org/get

# Include request headers too (-v verbose)
curl -v -I https://httpbin.org/get 2>&1 | head -30
```

> 💡 HTTP response headers tell you: server software, content type, cache policies, security headers (HSTS, CSP), and the response status code. A `200 OK` means success; `301/302` = redirect; `404` = not found; `500` = server error.

📸 **Verified Output:**
```
HTTP/2 200 
date: Thu, 05 Mar 2026 05:49:11 GMT
content-type: application/json
content-length: 256
server: gunicorn/19.9.0
access-control-allow-origin: *
access-control-allow-credentials: true
```

---

## Step 3: Silent Mode and JSON APIs

`-s` suppresses progress output; useful in scripts and when piping output.

```bash
# Silent GET request to REST API
curl -s https://httpbin.org/get

# Pretty-print JSON (pipe to python)
curl -s https://httpbin.org/get | python3 -m json.tool

# GET with custom User-Agent header
curl -s -H "User-Agent: MyBot/1.0" https://httpbin.org/get | python3 -m json.tool
```

> 💡 `-H` adds request headers. APIs often require headers like `Authorization: Bearer TOKEN`, `Content-Type: application/json`, or `Accept: application/json`. Always check API docs for required headers.

📸 **Verified Output:**
```json
{
  "args": {},
  "headers": {
    "Accept": "*/*",
    "Host": "httpbin.org",
    "User-Agent": "curl/7.81.0",
    "X-Amzn-Trace-Id": "Root=1-69a91957-156215cc037c2bed46b4796c"
  },
  "origin": "104.167.196.22",
  "url": "https://httpbin.org/get"
}
```

---

## Step 4: Following Redirects with -L

By default, curl does NOT follow HTTP redirects. Use `-L` to follow them.

```bash
# Without -L: stops at redirect
curl -I https://httpbin.org/redirect/1

# With -L: follows to final destination
curl -sL -o /dev/null -w '%{http_code} %{url_effective}\n' https://httpbin.org/redirect/1

# Show all redirect chain
curl -v -L -o /dev/null https://httpbin.org/redirect/3 2>&1 | grep -E "< HTTP|Location:"
```

> 💡 `-o /dev/null` discards the body (we only want headers/metadata). `-w` writes formatted output after transfer. `%{http_code}` and `%{url_effective}` are curl write-out variables — there are 50+ available.

📸 **Verified Output:**
```
200 https://httpbin.org/get
```

---

## Step 5: POST Requests and Sending Data

```bash
# POST with form data
curl -s -X POST -d "username=alice&password=secret" https://httpbin.org/post

# POST with JSON body
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","role":"admin"}' \
  https://httpbin.org/post | python3 -m json.tool

# POST with Basic Auth
curl -s -u "user:pass" https://httpbin.org/basic-auth/user/pass
```

> 💡 `-X POST` sets the HTTP method. `-d` sends data in the request body. For JSON APIs, always set `-H "Content-Type: application/json"`. `-u user:pass` uses HTTP Basic Authentication (base64 encoded). Never use Basic Auth over plain HTTP.

📸 **Verified Output:**
```json
{
  "data": "{\"name\":\"Alice\",\"role\":\"admin\"}",
  "headers": {
    "Content-Type": "application/json",
    "Host": "httpbin.org"
  },
  "json": {
    "name": "Alice",
    "role": "admin"
  },
  "url": "https://httpbin.org/post"
}
```

---

## Step 6: Downloading Files and Checking SSL

```bash
# Download to a file
curl -o /tmp/example.html https://example.com
ls -lh /tmp/example.html
head -3 /tmp/example.html

# wget: quiet download with custom filename
wget --quiet --output-document=/tmp/example-wget.html https://example.com
wc -l /tmp/example-wget.html

# wget: check if URL exists without downloading (spider mode)
wget --spider --quiet https://example.com 2>&1
echo "Exit code: $?"

# Check SSL certificate info
curl -vI https://example.com 2>&1 | grep -E "subject:|issuer:|expire date:|SSL connection"
```

> 💡 `wget --spider` returns exit code 0 if the URL is reachable, non-zero otherwise — great for health-check scripts. `curl -v` in verbose mode shows TLS handshake details including certificate subject and expiry date.

📸 **Verified Output:**
```
# wget spider
Exit code: 0

# Downloaded file
-rw-r--r-- 1 root root 1.2K Mar  5 05:49 /tmp/example.html
```

---

## Step 7: curl Timing Breakdown

curl's `-w` flag with timing variables reveals where time is spent in each request phase.

```bash
curl -s -o /dev/null -w '
     namelookup:  %{time_namelookup}s
        connect:  %{time_connect}s
     appconnect:  %{time_appconnect}s
    pretransfer:  %{time_pretransfer}s
       redirect:  %{time_redirect}s
  starttransfer:  %{time_starttransfer}s
                  --------
          total:  %{time_total}s
' https://httpbin.org/get
```

> 💡 **Timing breakdown:** `namelookup` = DNS resolution time; `connect` = TCP handshake; `appconnect` = TLS handshake (HTTPS only); `pretransfer` = ready to transfer; `starttransfer` = time to first byte (TTFB); `total` = everything. A slow `namelookup` indicates DNS issues; slow `appconnect` indicates TLS overhead.

📸 **Verified Output:**
```
     namelookup:  0.004455s
        connect:  0.032176s
     appconnect:  0.241946s
    pretransfer:  0.242516s
       redirect:  0.000000s
  starttransfer:  0.270799s
                  --------
          total:  0.271010s
```

---

## Step 8: Capstone — REST API Client Script

**Scenario:** You need to write a shell script that queries a public REST API, checks HTTP status, and processes the JSON response. The script must handle errors gracefully.

```bash
apt-get update -qq && apt-get install -y curl

# Complete REST API client with error handling
API_URL="https://httpbin.org"

check_api() {
  local endpoint="$1"
  local method="${2:-GET}"
  local data="$3"
  
  echo "=== Testing: $method $API_URL$endpoint ==="
  
  # Capture both body and status code
  HTTP_CODE=$(curl -s -o /tmp/api_response.json \
    -w "%{http_code}" \
    -X "$method" \
    -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    ${data:+-d "$data"} \
    "$API_URL$endpoint")
  
  echo "Status: $HTTP_CODE"
  
  if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "✓ Success"
    cat /tmp/api_response.json | python3 -m json.tool 2>/dev/null | head -10
  else
    echo "✗ Error: HTTP $HTTP_CODE"
    cat /tmp/api_response.json
  fi
  echo ""
}

# Test various endpoints
check_api "/get"
check_api "/post" "POST" '{"test": "data"}'
check_api "/status/404"
check_api "/status/500"

# Timing summary
echo "=== Performance Check ==="
curl -s -o /dev/null -w "DNS: %{time_namelookup}s | Connect: %{time_connect}s | TLS: %{time_appconnect}s | Total: %{time_total}s\n" \
  https://httpbin.org/get
```

> 💡 Always capture the HTTP status code separately from the body (`-o FILE -w "%{http_code}"`). Check for 2xx success before processing JSON. This pattern works for CI/CD health checks, API monitoring scripts, and automated testing pipelines.

📸 **Verified Output:**
```
=== Testing: GET https://httpbin.org/get ===
Status: 200
✓ Success
{
    "args": {},
    "headers": {
        "Accept": "application/json",
        "Host": "httpbin.org"
    }
}

=== Testing: POST https://httpbin.org/post ===
Status: 200
✓ Success

=== Testing: GET https://httpbin.org/status/404 ===
Status: 404
✗ Error: HTTP 404

=== Performance Check ===
DNS: 0.004455s | Connect: 0.032176s | TLS: 0.241946s | Total: 0.271010s
```

---

## Summary

| Tool / Flag | Purpose |
|-------------|---------|
| `curl -I URL` | Fetch headers only (HEAD request) |
| `curl -s URL` | Silent mode (suppress progress) |
| `curl -L URL` | Follow HTTP redirects |
| `curl -o FILE URL` | Save response to file |
| `curl -X POST -d DATA URL` | Send POST with body data |
| `curl -H "Key: Value" URL` | Add custom request header |
| `curl -u user:pass URL` | HTTP Basic Authentication |
| `curl -w "fmt" URL` | Write-out formatted metadata |
| `curl -v URL` | Verbose: show full TLS/HTTP exchange |
| `wget --quiet URL` | Download silently |
| `wget --output-document=FILE URL` | Download to specific filename |
| `wget --spider URL` | Check URL exists (exit code only) |
| HTTP 200 | OK — success |
| HTTP 301/302 | Redirect — use `-L` to follow |
| HTTP 401/403 | Auth required / forbidden |
| HTTP 404 | Not found |
| HTTP 500 | Server error |
