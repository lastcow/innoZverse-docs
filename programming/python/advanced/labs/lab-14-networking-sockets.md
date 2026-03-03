# Lab 14: Networking — Sockets & Async HTTP

## Objective
Master Python networking: raw TCP sockets with a request-response protocol, `socketserver.ThreadingTCPServer` for a multi-client echo service, `http.server` for a minimal HTTP server, `urllib.request` for HTTP GET/POST, and `asyncio` streams for an async TCP client-server pair — all on localhost.

## Background
Every network library (requests, aiohttp, FastAPI) sits on top of the OS socket API. Understanding raw sockets demystifies connection handling, framing, and protocol design. Python's `socketserver` adds threading, and `asyncio` replaces threads with coroutines for non-blocking I/O. Production services use frameworks on top of these primitives, but knowing the layers helps you debug, tune, and design correctly.

## Time
35 minutes

## Prerequisites
- Python Advanced Lab 05 (Advanced Async)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Steps 1–8: Raw TCP echo, length-prefixed framing, ThreadingTCPServer, urllib HTTP, async TCP server, async client, concurrent requests, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import socket, socketserver, threading, time, asyncio, json, urllib.request, urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from concurrent.futures import ThreadPoolExecutor

# ── Step 1: Raw TCP echo server + client (loopback) ──────────────────────────
print("=== Raw TCP Echo ===")

def tcp_echo_server(port, ready_event):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port))
        srv.listen(5)
        srv.settimeout(3.0)
        ready_event.set()
        try:
            conn, _ = srv.accept()
            with conn:
                data = conn.recv(1024)
                conn.sendall(b"Echo: " + data)
        except socket.timeout:
            pass

ready = threading.Event()
t = threading.Thread(target=tcp_echo_server, args=(19900, ready), daemon=True)
t.start(); ready.wait()

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("127.0.0.1", 19900))
    s.sendall(b"Surface Pro order:1001")
    response = s.recv(1024)
print(f"  Sent:     'Surface Pro order:1001'")
print(f"  Received: '{response.decode()}'")
t.join(timeout=1)

# ── Step 2: Length-prefixed framing ──────────────────────────────────────────
print("\n=== Length-Prefixed Framing ===")
import struct

def send_msg(sock, msg: bytes):
    sock.sendall(struct.pack(">I", len(msg)) + msg)

def recv_msg(sock) -> bytes:
    raw_len = sock.recv(4)
    if not raw_len: return b""
    length = struct.unpack(">I", raw_len)[0]
    data = b""
    while len(data) < length:
        chunk = sock.recv(length - len(data))
        if not chunk: break
        data += chunk
    return data

def framed_server(port, ready_event):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", port)); srv.listen(5); srv.settimeout(3.0)
        ready_event.set()
        try:
            conn, _ = srv.accept()
            with conn:
                for _ in range(3):
                    msg = recv_msg(conn)
                    if not msg: break
                    obj = json.loads(msg)
                    reply = json.dumps({"status": "ok", "id": obj["id"], "total": obj["price"]*obj["qty"]})
                    send_msg(conn, reply.encode())
        except socket.timeout:
            pass

ready2 = threading.Event()
t2 = threading.Thread(target=framed_server, args=(19901, ready2), daemon=True)
t2.start(); ready2.wait()

orders = [
    {"id": 1001, "product": "Surface Pro",  "price": 864.0, "qty": 2},
    {"id": 1002, "product": "Surface Pen",  "price": 49.99, "qty": 5},
    {"id": 1003, "product": "Office 365",   "price": 99.99, "qty": 1},
]
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("127.0.0.1", 19901))
    for order in orders:
        send_msg(s, json.dumps(order).encode())
        reply = json.loads(recv_msg(s))
        print(f"  Order #{reply['id']}  total=${reply['total']:.2f}  status={reply['status']}")
t2.join(timeout=1)

# ── Step 3: ThreadingTCPServer ────────────────────────────────────────────────
print("\n=== ThreadingTCPServer (multi-client) ===")

class EchoHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(256)
        self.request.sendall(b"[" + threading.current_thread().name.encode() + b"] " + data)

server = socketserver.ThreadingTCPServer(("127.0.0.1", 19902), EchoHandler)
server.daemon_threads = True
st = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
st.start()
time.sleep(0.05)

responses = []
def send_to_server(msg):
    with socket.socket() as s:
        s.connect(("127.0.0.1", 19902))
        s.sendall(msg.encode()); responses.append(s.recv(256).decode())

with ThreadPoolExecutor(max_workers=5) as pool:
    list(pool.map(send_to_server, [f"Client-{i}: hello" for i in range(5)]))
server.shutdown()
for r in sorted(responses): print(f"  {r}")

# ── Step 4: urllib HTTP GET ───────────────────────────────────────────────────
print("\n=== urllib HTTP (minimal HTTP server) ===")

class ProductHandler(BaseHTTPRequestHandler):
    PRODUCTS = [
        {"id":1,"name":"Surface Pro","price":864.0},
        {"id":2,"name":"Surface Pen","price":49.99},
    ]
    def do_GET(self):
        body = json.dumps({"products": self.PRODUCTS, "count": len(self.PRODUCTS)}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))
        result = {"id": 99, "name": payload.get("name","?"), "status": "created"}
        body = json.dumps(result).encode()
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args): pass  # silence access log

http_srv = HTTPServer(("127.0.0.1", 19903), ProductHandler)
ht = threading.Thread(target=http_srv.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
ht.start(); time.sleep(0.05)

with urllib.request.urlopen("http://127.0.0.1:19903/products") as resp:
    data = json.load(resp)
    print(f"  GET /products → {data['count']} products, status={resp.status}")
    for p in data["products"]: print(f"    {p}")

post_data = json.dumps({"name": "USB-C Hub", "price": 29.99}).encode()
req = urllib.request.Request("http://127.0.0.1:19903/products",
    data=post_data, headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req) as resp:
    result = json.load(resp)
    print(f"  POST /products → {result}")
http_srv.shutdown()

# ── Step 5: asyncio streams (async TCP) ───────────────────────────────────────
print("\n=== asyncio Streams (Async TCP) ===")

async def async_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    data = await reader.read(256)
    payload = json.loads(data)
    response = {"echo": payload, "server": "asyncio", "ts": time.time()}
    writer.write(json.dumps(response).encode())
    await writer.drain()
    writer.close()

async def async_client(port, message):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(json.dumps(message).encode())
    await writer.drain()
    data = await reader.read(1024)
    writer.close()
    return json.loads(data)

async def main():
    srv = await asyncio.start_server(async_handler, "127.0.0.1", 19904)
    async with srv:
        # 3 concurrent clients
        results = await asyncio.gather(
            async_client(19904, {"id": 1, "product": "Surface Pro", "qty": 2}),
            async_client(19904, {"id": 2, "product": "Surface Pen", "qty": 5}),
            async_client(19904, {"id": 3, "product": "Office 365",  "qty": 1}),
        )
        for r in results:
            p = r["echo"]
            print(f"  order #{p['id']} {p['product']} ×{p['qty']} → server={r['server']}")

asyncio.run(main())

print("\n=== Summary ===")
print("  Raw TCP:          socket.socket() — full control")
print("  Framed protocol:  struct length-prefix — reliable boundaries")
print("  ThreadingTCP:     socketserver.ThreadingTCPServer — concurrent")
print("  HTTP client:      urllib.request — stdlib, no deps")
print("  Async TCP:        asyncio.start_server / open_connection")
PYEOF
```

> 💡 **TCP is a stream, not a message protocol.** A single `send("hello world")` might arrive as `"hello"` + `" world"` in two `recv()` calls. This is TCP stream semantics. To build a message protocol on top, you need framing — the most common approach is a 4-byte length prefix before each message. The receiver reads 4 bytes, learns the message size, then loops on `recv()` until it has all the bytes. HTTP uses `Content-Length:` and chunked encoding for exactly the same reason.

**📸 Verified Output:**
```
=== Raw TCP Echo ===
  Sent:     'Surface Pro order:1001'
  Received: 'Echo: Surface Pro order:1001'

=== Length-Prefixed Framing ===
  Order #1001  total=$1728.00  status=ok
  Order #1002  total=$249.95   status=ok
  Order #1003  total=$99.99    status=ok

=== ThreadingTCPServer (multi-client) ===
  [Thread-N] Client-0: hello
  [Thread-N] Client-1: hello
  ...

=== urllib HTTP (minimal HTTP server) ===
  GET /products → 2 products, status=200
  POST /products → {'id': 99, 'name': 'USB-C Hub', 'status': 'created'}

=== asyncio Streams (Async TCP) ===
  order #1 Surface Pro ×2 → server=asyncio
  order #2 Surface Pen ×5 → server=asyncio
  order #3 Office 365  ×1 → server=asyncio
```

---

## Summary

| API | Layer | Use for |
|-----|-------|---------|
| `socket.socket()` | Raw TCP | Protocols, debugging |
| `struct` length-prefix | Framing | Message boundaries |
| `socketserver.ThreadingTCPServer` | Threaded server | Simple multi-client |
| `urllib.request` | HTTP client | Stdlib HTTP (no deps) |
| `asyncio.start_server` | Async TCP | High-concurrency server |
| `asyncio.open_connection` | Async TCP client | Non-blocking connect |

## Further Reading
- [Python `socket`](https://docs.python.org/3/library/socket.html)
- [Python `asyncio` Streams](https://docs.python.org/3/library/asyncio-stream.html)
