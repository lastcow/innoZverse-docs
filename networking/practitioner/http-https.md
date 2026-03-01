# HTTP & HTTPS

## HTTP Request/Response

```
GET /api/users HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGc...
Content-Type: application/json

↓

HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 248

{"users": [...]}
```

## HTTP Methods

| Method | Purpose | Idempotent | Body |
|--------|---------|-----------|------|
| GET | Retrieve data | Yes | No |
| POST | Create resource | No | Yes |
| PUT | Replace resource | Yes | Yes |
| PATCH | Partial update | No | Yes |
| DELETE | Remove resource | Yes | No |

## HTTP Status Codes

```
2xx Success
  200 OK
  201 Created
  204 No Content

3xx Redirection
  301 Moved Permanently
  302 Found (Temporary)
  304 Not Modified

4xx Client Errors
  400 Bad Request
  401 Unauthorized
  403 Forbidden
  404 Not Found
  429 Too Many Requests

5xx Server Errors
  500 Internal Server Error
  502 Bad Gateway
  503 Service Unavailable
  504 Gateway Timeout
```

## HTTPS & TLS

```bash
# Check SSL certificate
openssl s_client -connect example.com:443 </dev/null

# Certificate details
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -text -noout

# Test with curl
curl -v https://example.com    # Verbose, shows TLS handshake
curl -k https://example.com   # Ignore SSL errors (testing only)
```

## curl Cheatsheet

```bash
curl https://api.example.com/users                          # GET
curl -X POST -d '{"name":"Alice"}' -H "Content-Type: application/json" https://api.example.com/users
curl -u username:password https://api.example.com           # Basic auth
curl -H "Authorization: Bearer TOKEN" https://api.example.com
curl -o output.file https://example.com/file.zip            # Download
curl -I https://example.com                                  # Headers only
```
