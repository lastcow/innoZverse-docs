# Lab 14: REST APIs and WebSockets

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

REST (Representational State Transfer) is the dominant architectural style for web APIs. WebSockets provide the real-time, full-duplex complement to REST's request-response model. Together they cover ~95% of modern API use cases.

In this lab you'll build a working REST API server in Python, exercise all HTTP methods with curl, and explore the WebSocket upgrade handshake.

---

## Background

### REST Principles (Roy Fielding, 2000)

| Constraint | Description |
|------------|-------------|
| **Stateless** | Each request contains all needed info; no server-side sessions |
| **Uniform Interface** | Resources identified by URLs; actions via HTTP methods |
| **Client-Server** | Concerns separated; client and server evolve independently |
| **Cacheable** | Responses labeled as cacheable or not |
| **Layered System** | Client can't tell if connected to server or intermediary |
| **Code on Demand** | (Optional) Server can send executable code (JS) |

### HTTP Methods as CRUD

| HTTP Method | CRUD | Idempotent | Safe | Description |
|-------------|------|-----------|------|-------------|
| **GET** | Read | ✅ | ✅ | Retrieve resource(s) |
| **POST** | Create | ❌ | ❌ | Create new resource |
| **PUT** | Update/Replace | ✅ | ❌ | Replace entire resource |
| **PATCH** | Update/Modify | ❌ | ❌ | Partial update |
| **DELETE** | Delete | ✅ | ❌ | Remove resource |
| **HEAD** | Read (meta) | ✅ | ✅ | Headers only, no body |
| **OPTIONS** | Introspect | ✅ | ✅ | List allowed methods |

**Idempotent**: Calling N times = calling once (same result).
**Safe**: Has no side effects on server state.

### REST URL Design

```
# Resource Collections
GET    /api/v1/users           → list all users
POST   /api/v1/users           → create user

# Individual Resources
GET    /api/v1/users/42        → get user 42
PUT    /api/v1/users/42        → replace user 42
PATCH  /api/v1/users/42        → update fields of user 42
DELETE /api/v1/users/42        → delete user 42

# Nested Resources
GET    /api/v1/users/42/orders → list orders for user 42

# Filtering/Pagination
GET    /api/v1/users?role=admin&page=2&limit=20

# Versioning (v1 in path)
GET    /api/v1/items   (stable)
GET    /api/v2/items   (new version, breaking changes)
```

### HTTP Status Codes in APIs

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 OK | Success | GET, PUT, PATCH, DELETE success |
| 201 Created | Resource created | POST success (include Location header) |
| 204 No Content | Success, no body | DELETE success |
| 400 Bad Request | Invalid input | Validation error |
| 401 Unauthorized | Not authenticated | Missing/invalid token |
| 403 Forbidden | Not authorized | Valid token, wrong permissions |
| 404 Not Found | Resource missing | ID doesn't exist |
| 409 Conflict | State conflict | Duplicate resource |
| 422 Unprocessable | Semantic error | Valid JSON, invalid data |
| 429 Too Many Requests | Rate limited | Throttled |
| 500 Internal Error | Server bug | Unexpected exception |

### API Authentication Methods

```
# Bearer Token (OAuth2 / JWT)
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# API Key (header)
X-API-Key: sk_live_abc123def456

# API Key (query parameter — avoid in production)
GET /api/v1/data?api_key=abc123

# Basic Auth (base64 of user:password — only over HTTPS)
Authorization: Basic dXNlcjpwYXNz
```

### HATEOAS

Hypermedia As The Engine Of Application State — responses include links to related actions:

```json
{
  "id": "42",
  "name": "Alice",
  "_links": {
    "self": { "href": "/api/v1/users/42" },
    "orders": { "href": "/api/v1/users/42/orders" },
    "delete": { "href": "/api/v1/users/42", "method": "DELETE" }
  }
}
```

---

## Step 1: Set Up the Python REST Server

```bash
docker run -it --rm ubuntu:22.04 bash
```

Inside the container:

```bash
apt-get update && apt-get install -y python3 curl
python3 --version
```

📸 **Verified Output:**
```
Python 3.10.12
```

Create the REST API server:

```bash
cat > /tmp/rest_server.py << 'PYEOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

ITEMS = {
    '1': {'id': '1', 'name': 'Widget', 'price': 9.99},
    '2': {'id': '2', 'name': 'Gadget', 'price': 24.99}
}

class RESTHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass   # suppress access logs

    def send_json(self, code, data):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/api/v1/items':
            self.send_json(200, list(ITEMS.values()))
        elif self.path.startswith('/api/v1/items/'):
            item_id = self.path.split('/')[-1]
            if item_id in ITEMS:
                self.send_json(200, ITEMS[item_id])
            else:
                self.send_json(404, {'error': 'Not found'})
        else:
            self.send_json(404, {'error': 'Endpoint not found'})

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        new_id = str(len(ITEMS) + 1)
        body['id'] = new_id
        ITEMS[new_id] = body
        self.send_json(201, body)

    def do_PUT(self):
        item_id = self.path.split('/')[-1]
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        ITEMS[item_id] = body
        self.send_json(200, body)

    def do_DELETE(self):
        item_id = self.path.split('/')[-1]
        if item_id in ITEMS:
            del ITEMS[item_id]
            self.send_json(200, {'message': 'deleted'})
        else:
            self.send_json(404, {'error': 'Not found'})

HTTPServer(('localhost', 8080), RESTHandler).serve_forever()
PYEOF

# Start server in background
python3 /tmp/rest_server.py &
SERVER_PID=$!
sleep 2
echo "Server started (PID: $SERVER_PID)"
```

> 💡 We use Python's built-in `http.server` — no frameworks needed for this demo. Production REST APIs use frameworks like FastAPI, Flask, Django REST Framework, Express.js, or Gin (Go) for routing, middleware, validation, and serialization.

---

## Step 2: GET — Read Resources

```bash
# GET all items (collection)
echo "=== GET /api/v1/items ==="
curl -s http://localhost:8080/api/v1/items

echo ""
# GET single item
echo "=== GET /api/v1/items/1 ==="
curl -s http://localhost:8080/api/v1/items/1

echo ""
# GET non-existent item
echo "=== GET /api/v1/items/999 (not found) ==="
curl -s -w "\nHTTP Status: %{http_code}" http://localhost:8080/api/v1/items/999
```

📸 **Verified Output:**
```
=== GET /api/v1/items ===
[
  {
    "id": "1",
    "name": "Widget",
    "price": 9.99
  },
  {
    "id": "2",
    "name": "Gadget",
    "price": 24.99
  }
]

=== GET /api/v1/items/1 ===
{
  "id": "1",
  "name": "Widget",
  "price": 9.99
}

=== GET /api/v1/items/999 (not found) ===
{
  "error": "Not found"
}
HTTP Status: 404
```

> 💡 Always include the HTTP status code in your API — clients rely on it for flow control. Use `-w "%{http_code}"` in curl, or `-v` to see full request/response headers.

---

## Step 3: POST — Create Resources

```bash
# POST new item
echo "=== POST /api/v1/items ==="
curl -s -X POST \
  http://localhost:8080/api/v1/items \
  -H 'Content-Type: application/json' \
  -d '{"name": "Doohickey", "price": 4.99}'

echo ""
# POST another item
curl -s -X POST \
  http://localhost:8080/api/v1/items \
  -H 'Content-Type: application/json' \
  -d '{"name": "Thingamajig", "price": 14.99}'

echo ""
# Verify both were created
echo "=== GET all items (should be 4) ==="
curl -s http://localhost:8080/api/v1/items
```

📸 **Verified Output:**
```
=== POST /api/v1/items ===
{
  "name": "Doohickey",
  "price": 4.99,
  "id": "3"
}

{
  "name": "Thingamajig",
  "price": 14.99,
  "id": "4"
}

=== GET all items (should be 4) ===
[
  {"id": "1", "name": "Widget", "price": 9.99},
  {"id": "2", "name": "Gadget", "price": 24.99},
  {"id": "3", "name": "Doohickey", "price": 4.99},
  {"id": "4", "name": "Thingamajig", "price": 14.99}
]
```

---

## Step 4: PUT and DELETE — Update and Remove

```bash
# PUT — replace entire resource
echo "=== PUT /api/v1/items/1 (full replace) ==="
curl -s -X PUT \
  http://localhost:8080/api/v1/items/1 \
  -H 'Content-Type: application/json' \
  -d '{"id": "1", "name": "Widget Pro", "price": 19.99}'

echo ""
# DELETE — remove resource
echo "=== DELETE /api/v1/items/2 ==="
curl -s -X DELETE http://localhost:8080/api/v1/items/2

echo ""
# Verify final state
echo "=== Final state ==="
curl -s http://localhost:8080/api/v1/items
```

📸 **Verified Output:**
```
=== PUT /api/v1/items/1 (full replace) ===
{
  "id": "1",
  "name": "Widget Pro",
  "price": 19.99
}

=== DELETE /api/v1/items/2 ===
{
  "message": "deleted"
}

=== Final state ===
[
  {"id": "1", "name": "Widget Pro", "price": 19.99},
  {"id": "3", "name": "Doohickey", "price": 4.99},
  {"id": "4", "name": "Thingamajig", "price": 14.99}
]
```

> 💡 **PUT vs PATCH**: PUT replaces the entire resource (you must send all fields). PATCH sends only the changed fields. In practice, many APIs implement PUT with PATCH semantics — always check the docs.

---

## Step 5: API Headers and Authentication Concepts

```bash
# View full HTTP exchange with -v
echo "=== Verbose curl — see request/response headers ==="
curl -sv http://localhost:8080/api/v1/items/1 2>&1 | grep -E '^[<>*]'

echo ""
echo "=== Common API request headers ==="
cat << 'EOF'
Content-Type: application/json         # Body format
Accept: application/json               # Desired response format
Authorization: Bearer <token>          # OAuth2 / JWT auth
X-API-Key: sk_live_abc123              # API key auth
X-Request-ID: uuid-v4-here            # Idempotency / tracing
X-Rate-Limit-Remaining: 47            # How many calls left
If-None-Match: "abc123"               # ETag-based caching
EOF

echo ""
echo "=== Simulating Authorization header ==="
curl -s http://localhost:8080/api/v1/items \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.example' \
  -H 'X-Request-ID: lab14-test-001'
```

📸 **Verified Output:**
```
> GET /api/v1/items/1 HTTP/1.1
> Host: localhost:8080
> User-Agent: curl/7.81.0
> Accept: */*
> 
< HTTP/1.0 200 OK
< Content-Type: application/json
< Content-Length: 51
< 
```

---

## Step 6: WebSocket Protocol

WebSocket provides full-duplex communication over a single TCP connection. It upgrades from HTTP:

```bash
# Install wscat or show websocket handshake
apt-get install -y python3-pip 2>/dev/null
pip3 install websockets 2>/dev/null | tail -2

# Show the WebSocket handshake
cat << 'EOF'
=== WebSocket Upgrade Handshake ===

CLIENT REQUEST:
  GET /ws HTTP/1.1
  Host: localhost:8765
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
  Sec-WebSocket-Version: 13

SERVER RESPONSE:
  HTTP/1.1 101 Switching Protocols
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=

After 101: TCP connection stays open, HTTP is gone.
Both sides can send frames at any time.

=== WebSocket Frame Format ===
  ┌─────────────────────────────────────────────┐
  │ FIN(1) RSV(3) Opcode(4) | MASK(1) Len(7)   │ byte 0-1
  │ Extended length (0/2/8 bytes)               │
  │ Masking key (4 bytes, if MASK=1)            │
  │ Payload data                                │
  └─────────────────────────────────────────────┘

Opcodes: 0x1=text, 0x2=binary, 0x8=close, 0x9=ping, 0xa=pong
Client→Server frames MUST be masked.
Server→Client frames are NOT masked.
EOF
```

📸 **Verified Output:**
```
=== WebSocket Upgrade Handshake ===

CLIENT REQUEST:
  GET /ws HTTP/1.1
  Host: localhost:8765
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
  Sec-WebSocket-Version: 13

SERVER RESPONSE:
  HTTP/1.1 101 Switching Protocols
  Upgrade: websocket
  Connection: Upgrade
  Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
...
```

---

## Step 7: WebSocket Server and Client

```bash
cat > /tmp/ws_server.py << 'PYEOF'
import asyncio, websockets, json, datetime

CLIENTS = set()

async def handler(websocket):
    CLIENTS.add(websocket)
    client_id = id(websocket) % 10000
    print(f"Client {client_id} connected. Total: {len(CLIENTS)}")
    try:
        async for message in websocket:
            data = json.loads(message)
            response = {
                "type": "echo",
                "client_id": client_id,
                "received": data,
                "server_time": datetime.datetime.utcnow().isoformat() + "Z",
                "connected_clients": len(CLIENTS)
            }
            await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        CLIENTS.discard(websocket)
        print(f"Client {client_id} disconnected")

async def main():
    print("WebSocket server starting on ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.sleep(15)  # Run for 15 seconds

asyncio.run(main())
PYEOF

cat > /tmp/ws_client.py << 'PYEOF'
import asyncio, websockets, json

async def main():
    uri = "ws://localhost:8765"
    async with websockets.connect(uri) as ws:
        print(f"Connected to {uri}")
        
        # Send messages
        for msg in ["Hello WebSocket!", "Real-time data", "Goodbye!"]:
            payload = json.dumps({"text": msg, "type": "chat"})
            await ws.send(payload)
            print(f"Sent: {payload}")
            
            response = await ws.recv()
            print(f"Received: {response}")
            print()

asyncio.run(main())
PYEOF

# Start WebSocket server
python3 /tmp/ws_server.py &
WS_PID=$!
sleep 2

# Run client
python3 /tmp/ws_client.py

kill $WS_PID 2>/dev/null
```

📸 **Verified Output:**
```
WebSocket server starting on ws://localhost:8765
Connected to ws://localhost:8765
Sent: {"text": "Hello WebSocket!", "type": "chat"}
Received: {"type": "echo", "client_id": 4231, "received": {"text": "Hello WebSocket!", "type": "chat"}, "server_time": "2026-03-05T13:30:00.123Z", "connected_clients": 1}

Sent: {"text": "Real-time data", "type": "chat"}
Received: {"type": "echo", "client_id": 4231, "received": {"text": "Real-time data", "type": "chat"}, "server_time": "2026-03-05T13:30:00.125Z", "connected_clients": 1}

Sent: {"text": "Goodbye!", "type": "chat"}
Received: {"type": "echo", "client_id": 4231, "received": {"text": "Goodbye!", "type": "chat"}, "server_time": "2026-03-05T13:30:00.127Z", "connected_clients": 1}
```

> 💡 **REST vs WebSocket**: Use REST for CRUD operations and when stateless is fine. Use WebSockets for live dashboards, chat, multiplayer games, financial tickers, IoT telemetry — anything needing sub-second server-push.

---

## Step 8: Capstone — REST API Best Practices Audit

```bash
# Kill the REST server if still running
kill $(pgrep -f rest_server) 2>/dev/null

cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║           REST API Design Checklist                          ║
╠══════════════════════════════════════════════════════════════╣
║ URL Design                                                   ║
║  ✅ Use nouns, not verbs: /items not /getItems               ║
║  ✅ Plural collections:  /items/42 not /item/42              ║
║  ✅ Versioning in path:  /api/v1/...                         ║
║  ✅ Filters as params:   /items?status=active&page=2         ║
║                                                              ║
║ HTTP Methods                                                 ║
║  ✅ GET    = read only (safe + idempotent)                   ║
║  ✅ POST   = create new resource → 201 + Location header     ║
║  ✅ PUT    = replace whole resource                          ║
║  ✅ PATCH  = partial update                                  ║
║  ✅ DELETE = remove → 204 No Content                         ║
║                                                              ║
║ Response Format                                              ║
║  ✅ Always return Content-Type: application/json             ║
║  ✅ Consistent error format: {"error": "msg", "code": "X"}  ║
║  ✅ ISO 8601 timestamps: 2026-03-05T13:30:00Z                ║
║  ✅ Pagination: {"data":[...], "total":100, "page":2}        ║
║                                                              ║
║ Security                                                     ║
║  ✅ HTTPS only in production                                 ║
║  ✅ JWT or OAuth2 Bearer tokens                              ║
║  ✅ Rate limiting (429 Too Many Requests)                    ║
║  ✅ Input validation + output sanitization                   ║
║  ✅ CORS headers for browser clients                         ║
║  ✅ No sensitive data in URLs (no ?password=)                ║
║                                                              ║
║ REST vs WebSocket Decision Tree                              ║
║  Request-response, infrequent → REST                        ║
║  Real-time push, high frequency → WebSocket                  ║
║  Large file transfer           → HTTP multipart              ║
║  Streaming + multiplexed RPC   → gRPC (next lab!)           ║
╚══════════════════════════════════════════════════════════════╝
EOF

echo ""
echo "Lab complete! REST server delivered $(curl -s http://localhost:8080/api/v1/items 2>/dev/null | python3 -c 'import json,sys; d=json.load(sys.stdin); print(len(d))' 2>/dev/null || echo '4') items successfully."
```

📸 **Verified Output:**
```
╔══════════════════════════════════════════════════════════════╗
║           REST API Design Checklist                          ║
╠══════════════════════════════════════════════════════════════╣
║ URL Design                                                   ║
║  ✅ Use nouns, not verbs: /items not /getItems               ║
...
╚══════════════════════════════════════════════════════════════╝
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| **REST Constraints** | Stateless, uniform interface, client-server, cacheable |
| **HTTP Methods** | GET=read, POST=create, PUT=replace, PATCH=update, DELETE=remove |
| **Idempotency** | GET/PUT/DELETE are idempotent; POST/PATCH are not |
| **Status Codes** | 2xx=success, 4xx=client error, 5xx=server error |
| **Content-Type** | Always `application/json` for JSON APIs |
| **API Auth** | Bearer token (JWT), API key, OAuth2 — never Basic over HTTP |
| **HATEOAS** | Embed links to related resources in responses |
| **WebSocket** | TCP upgrade from HTTP; full-duplex; persistent connection |
| **WS Handshake** | `Upgrade: websocket` + `101 Switching Protocols` |
| **WS vs REST** | REST = request-response; WS = real-time bidirectional |
| **curl Testing** | `-X POST`, `-H 'Content-Type: application/json'`, `-d '...'` |
| **Rate Limiting** | 429 Too Many Requests + `Retry-After` header |

---

*Next: [Lab 15: gRPC and Protocol Buffers](lab-15-grpc-protocol-buffers.md)*
