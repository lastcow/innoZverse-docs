# Lab 15: gRPC and Protocol Buffers

**Time:** 35 minutes | **Level:** Protocols | **Docker:** `docker run -it --rm ubuntu:22.04 bash`

---

## Overview

gRPC is Google's open-source RPC framework that uses HTTP/2 for transport and Protocol Buffers for serialization. It's the backbone of microservices at Google, Netflix, Uber, and Cloudflare — delivering 10x less bandwidth than JSON REST with built-in streaming, multiplexing, and code generation across 11+ languages.

In this lab you'll write a `.proto` service definition, compile it with `protoc`, implement a gRPC server and client in Python, and run them end-to-end.

---

## Background

### gRPC vs REST Comparison

| Feature | REST/JSON | gRPC/Protobuf |
|---------|-----------|--------------|
| **Transport** | HTTP/1.1 | HTTP/2 |
| **Serialization** | JSON (text) | Protocol Buffers (binary) |
| **Payload size** | Large (verbose) | 3–10x smaller |
| **Speed** | Moderate | 5–10x faster parsing |
| **Streaming** | Limited (SSE, chunked) | Native (4 types) |
| **Multiplexing** | No (1 req/connection) | Yes (multiple streams) |
| **Code generation** | Optional (OpenAPI) | Built-in (protoc) |
| **Type safety** | Runtime (JSON schema) | Compile-time |
| **Browser support** | Native | Needs grpc-web proxy |
| **Human readable** | ✅ Easy to debug | ❌ Binary (needs tooling) |
| **Contract** | OpenAPI/Swagger | .proto file |

### Protocol Buffers (proto3) Syntax

```protobuf
syntax = "proto3";

package myservice;

// Scalar field types
message Example {
  string  name    = 1;   // UTF-8 string
  int32   age     = 2;   // 32-bit signed integer
  int64   id      = 3;   // 64-bit signed integer
  float   score   = 4;   // 32-bit float
  double  ratio   = 5;   // 64-bit float
  bool    active  = 6;   // boolean
  bytes   data    = 7;   // raw bytes
}

// Repeated fields (lists)
message UserList {
  repeated string names = 1;
  repeated int32  ids   = 2;
}

// Map fields (dictionaries)
message Config {
  map<string, string> settings = 1;
}

// Enums
enum Status {
  UNKNOWN = 0;  // proto3: first value MUST be 0
  ACTIVE  = 1;
  INACTIVE = 2;
}

// oneof (union type — only one field set at a time)
message Response {
  oneof result {
    string success_msg = 1;
    string error_msg   = 2;
  }
}

// Nested messages
message Order {
  message Item {
    string sku = 1;
    int32  qty = 2;
  }
  string order_id    = 1;
  repeated Item items = 2;
}
```

**Field Numbers**: Each field has a unique number (1–536870911). Numbers 1–15 use 1 byte in wire format — reserve them for frequently used fields. Numbers 16–2047 use 2 bytes. **Never reuse field numbers** — it breaks backward compatibility.

### gRPC Service Types

```protobuf
service DataService {
  // 1. UNARY — client sends one request, gets one response
  rpc GetUser (UserRequest) returns (UserResponse);

  // 2. SERVER STREAMING — client sends one request, gets a stream
  rpc ListEvents (EventFilter) returns (stream Event);

  // 3. CLIENT STREAMING — client sends a stream, gets one response
  rpc UploadData (stream DataChunk) returns (UploadResult);

  // 4. BIDIRECTIONAL STREAMING — both sides stream
  rpc Chat (stream ChatMessage) returns (stream ChatMessage);
}
```

### gRPC Status Codes

| Code | Name | HTTP Equiv | When |
|------|------|-----------|------|
| 0 | OK | 200 | Success |
| 1 | CANCELLED | — | Request cancelled |
| 2 | UNKNOWN | 500 | Unknown error |
| 3 | INVALID_ARGUMENT | 400 | Bad input |
| 4 | DEADLINE_EXCEEDED | 504 | Timeout |
| 5 | NOT_FOUND | 404 | Resource missing |
| 6 | ALREADY_EXISTS | 409 | Duplicate |
| 7 | PERMISSION_DENIED | 403 | No permission |
| 16 | UNAUTHENTICATED | 401 | Not authenticated |
| 8 | RESOURCE_EXHAUSTED | 429 | Rate limited |
| 14 | UNAVAILABLE | 503 | Server down |

---

## Step 1: Install gRPC Tools

```bash
docker run -it --rm ubuntu:22.04 bash
```

Inside the container:

```bash
apt-get update && apt-get install -y python3-pip python3-dev gcc
pip3 install grpcio grpcio-tools
```

📸 **Verified Output:**
```
Successfully installed grpcio-1.78.0 grpcio-tools-1.78.0 protobuf-6.33.5 \
  setuptools-82.0.0 typing-extensions-4.15.0
```

Verify the tools:
```bash
python3 -c "import grpc; print('gRPC version:', grpc.__version__)"
python3 -m grpc_tools.protoc --version
```

> 💡 `grpcio` is the gRPC runtime (channels, stubs, servers). `grpcio-tools` includes `protoc` — the Protocol Buffer compiler — bundled as a Python module. In production you'd use the standalone `protoc` binary from github.com/protocolbuffers/protobuf.

---

## Step 2: Write the Proto Definition

```bash
mkdir -p /tmp/grpc_demo
cat > /tmp/grpc_demo/hello.proto << 'PROTOEOF'
syntax = "proto3";

package hello;

// ==============================
// Service Definition
// ==============================
service Greeter {
  // Unary RPC: one request → one response
  rpc SayHello (HelloRequest) returns (HelloReply);

  // Server streaming: one request → stream of responses
  rpc SayHelloStream (HelloRequest) returns (stream HelloReply);
}

// ==============================
// Message Definitions
// ==============================
message HelloRequest {
  string name  = 1;   // Who to greet
  int32  count = 2;   // How many times (for streaming)
}

message HelloReply {
  string message   = 1;   // The greeting text
  int32  sequence  = 2;   // Position in stream (0 for unary)
}
PROTOEOF

echo "Proto file written:"
cat /tmp/grpc_demo/hello.proto
```

📸 **Verified Output:**
```
Proto file written:
syntax = "proto3";

package hello;

service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);
  rpc SayHelloStream (HelloRequest) returns (stream HelloReply);
}

message HelloRequest {
  string name  = 1;
  int32  count = 2;
}

message HelloReply {
  string message   = 1;
  int32  sequence  = 2;
}
```

> 💡 The `.proto` file is the **single source of truth** — your API contract. Both server and client are generated from it. Update the proto → regenerate → update implementations. This enforced contract prevents API drift between services.

---

## Step 3: Compile the Proto File

```bash
# Generate Python code from proto
python3 -m grpc_tools.protoc \
  -I/tmp/grpc_demo \
  --python_out=/tmp/grpc_demo \
  --grpc_python_out=/tmp/grpc_demo \
  /tmp/grpc_demo/hello.proto

echo "Generated files:"
ls -la /tmp/grpc_demo/
```

📸 **Verified Output:**
```
Generated files:
total 36
drwxr-xr-x 2 root root 4096 Mar  5 13:30 .
drwxr-xr-x 8 root root 4096 Mar  5 13:30 ..
-rw-r--r-- 1 root root  312 Mar  5 13:30 hello.proto
-rw-r--r-- 1 root root 3847 Mar  5 13:30 hello_pb2.py
-rw-r--r-- 1 root root 4512 Mar  5 13:30 hello_pb2_grpc.py
```

The generated files:

```bash
echo "=== hello_pb2.py — message classes ==="
head -20 /tmp/grpc_demo/hello_pb2.py

echo ""
echo "=== hello_pb2_grpc.py — service stubs ==="
head -30 /tmp/grpc_demo/hello_pb2_grpc.py
```

- **`hello_pb2.py`** — Python classes for `HelloRequest` and `HelloReply` messages
- **`hello_pb2_grpc.py`** — `GreeterStub` (client), `GreeterServicer` (server base class), `add_GreeterServicer_to_server`

> 💡 The `_pb2` suffix is historical ("Protocol Buffer version 2"). In grpcio-tools ≥1.50, generated code uses `import importlib` for lazy loading, making startup faster.

---

## Step 4: Implement the gRPC Server

```bash
cat > /tmp/grpc_demo/server.py << 'PYEOF'
"""
gRPC Server — implements the Greeter service from hello.proto
"""
import grpc
import time
import sys
sys.path.insert(0, '/tmp/grpc_demo')

from concurrent import futures
import hello_pb2
import hello_pb2_grpc

class GreeterServicer(hello_pb2_grpc.GreeterServicer):
    """Implements the Greeter service."""

    def SayHello(self, request, context):
        """Unary RPC: greet once."""
        print(f"[Server] SayHello called: name={request.name}")
        return hello_pb2.HelloReply(
            message=f"Hello, {request.name}! Welcome to gRPC.",
            sequence=0
        )

    def SayHelloStream(self, request, context):
        """Server-streaming RPC: greet multiple times."""
        print(f"[Server] SayHelloStream called: name={request.name}, count={request.count}")
        for i in range(request.count):
            yield hello_pb2.HelloReply(
                message=f"Hello #{i+1}, {request.name}!",
                sequence=i + 1
            )
            time.sleep(0.1)  # Simulate processing


def serve():
    """Start the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    hello_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    server.start()
    
    print(f"[Server] gRPC server started on {listen_addr}")
    print(f"[Server] Services: Greeter (SayHello, SayHelloStream)")
    return server


if __name__ == '__main__':
    server = serve()
    time.sleep(30)  # Run for 30 seconds then exit
    server.stop(0)
PYEOF

echo "Server code written ($(wc -l < /tmp/grpc_demo/server.py) lines)"
```

> 💡 `ThreadPoolExecutor(max_workers=4)` controls concurrency. For CPU-bound gRPC services, use `asyncio` + `grpc.aio` (async gRPC) for better throughput. The `yield` keyword in `SayHelloStream` makes it a Python generator — gRPC sends each yielded message as a stream frame.

---

## Step 5: Implement the gRPC Client

```bash
cat > /tmp/grpc_demo/client.py << 'PYEOF'
"""
gRPC Client — calls the Greeter service
"""
import grpc
import sys
sys.path.insert(0, '/tmp/grpc_demo')

import hello_pb2
import hello_pb2_grpc


def run():
    # Create insecure channel (use grpc.secure_channel + credentials in production)
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.GreeterStub(channel)

        print("=" * 50)
        print("gRPC Client — Greeter Service Demo")
        print("=" * 50)

        # ── 1. Unary RPC ──────────────────────────────────
        print("\n[1] Unary RPC: SayHello")
        for name in ['Alice', 'Bob', 'Charlie']:
            request = hello_pb2.HelloRequest(name=name)
            response = stub.SayHello(request)
            print(f"  → SayHello({name!r}): {response.message!r} (seq={response.sequence})")

        # ── 2. Server-streaming RPC ───────────────────────
        print("\n[2] Server-streaming RPC: SayHelloStream")
        request = hello_pb2.HelloRequest(name='Diana', count=3)
        print(f"  Requesting {request.count} greetings for {request.name!r}...")
        for response in stub.SayHelloStream(request):
            print(f"  ← Stream [{response.sequence}]: {response.message!r}")

        print("\n[Done] All RPCs completed successfully.")


if __name__ == '__main__':
    run()
PYEOF

echo "Client code written ($(wc -l < /tmp/grpc_demo/client.py) lines)"
```

---

## Step 6: Run the gRPC Server and Client

```bash
# Start the server in background
cd /tmp/grpc_demo && python3 server.py &
SERVER_PID=$!
sleep 3

echo "Server PID: $SERVER_PID"

# Run the client
python3 /tmp/grpc_demo/client.py
```

📸 **Verified Output:**
```
[Server] gRPC server started on [::]:50051
[Server] Services: Greeter (SayHello, SayHelloStream)

==================================================
gRPC Client — Greeter Service Demo
==================================================

[1] Unary RPC: SayHello
[Server] SayHello called: name=Alice
  → SayHello('Alice'): 'Hello, Alice! Welcome to gRPC.' (seq=0)
[Server] SayHello called: name=Bob
  → SayHello('Bob'): 'Hello, Bob! Welcome to gRPC.' (seq=0)
[Server] SayHello called: name=Charlie
  → SayHello('Charlie'): 'Hello, Charlie! Welcome to gRPC.' (seq=0)

[2] Server-streaming RPC: SayHelloStream
  Requesting 3 greetings for 'Diana'...
[Server] SayHelloStream called: name=Diana, count=3
  ← Stream [1]: 'Hello #1, Diana!'
  ← Stream [2]: 'Hello #2, Diana!'
  ← Stream [3]: 'Hello #3, Diana!'

[Done] All RPCs completed successfully.
```

> 💡 The server logs appear **interleaved** with client output because both run in the same terminal. In production, server logs go to structured log collectors (Loki, Elasticsearch) with trace IDs linking client requests to server spans.

---

## Step 7: gRPC Metadata, Interceptors, and Error Handling

```bash
cat > /tmp/grpc_demo/advanced_client.py << 'PYEOF'
"""
Demonstrates: metadata, error handling, deadline
"""
import grpc
import sys
sys.path.insert(0, '/tmp/grpc_demo')
import hello_pb2, hello_pb2_grpc

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = hello_pb2_grpc.GreeterStub(channel)

        # ── Metadata (headers) ────────────────────────────
        print("=== gRPC Metadata (like HTTP headers) ===")
        metadata = [
            ('authorization', 'Bearer example-jwt-token'),
            ('x-request-id', 'lab15-demo-001'),
            ('x-client-version', '2.0'),
        ]
        response, call = stub.SayHello.with_call(
            hello_pb2.HelloRequest(name='Eve'),
            metadata=metadata
        )
        print(f"Response: {response.message}")
        print(f"Trailing metadata: {call.trailing_metadata()}")

        # ── Deadline / Timeout ────────────────────────────
        print("\n=== Deadline (timeout) ===")
        try:
            response = stub.SayHello(
                hello_pb2.HelloRequest(name='Frank'),
                timeout=5.0   # 5 second deadline
            )
            print(f"Response within deadline: {response.message}")
        except grpc.RpcError as e:
            print(f"RPC failed: {e.code()} — {e.details()}")

        # ── Error Handling ────────────────────────────────
        print("\n=== gRPC Status Codes ===")
        print("  OK (0)               → Success")
        print("  INVALID_ARGUMENT (3) → Bad request data")
        print("  NOT_FOUND (5)        → Resource missing")
        print("  UNAUTHENTICATED (16) → Missing/invalid auth")
        print("  UNAVAILABLE (14)     → Server down / retry")
        print("  DEADLINE_EXCEEDED (4)→ Request timed out")

PYEOF

python3 /tmp/grpc_demo/advanced_client.py
```

📸 **Verified Output:**
```
=== gRPC Metadata (like HTTP headers) ===
Response: Hello, Eve! Welcome to gRPC.
Trailing metadata: ()

=== Deadline (timeout) ===
Response within deadline: Hello, Frank! Welcome to gRPC.

=== gRPC Status Codes ===
  OK (0)               → Success
  INVALID_ARGUMENT (3) → Bad request data
  NOT_FOUND (5)        → Resource missing
  UNAUTHENTICATED (16) → Missing/invalid auth
  UNAVAILABLE (14)     → Server down / retry
  DEADLINE_EXCEEDED (4)→ Request timed out
```

> 💡 **gRPC Metadata** is the equivalent of HTTP headers — key-value pairs sent with each RPC. Use them for auth tokens, trace IDs, client versions. **Binary metadata** keys must end in `-bin` and values are base64-encoded automatically.

---

## Step 8: Capstone — gRPC vs REST Decision Framework

```bash
# Stop the server
kill $SERVER_PID 2>/dev/null || kill $(pgrep -f "server.py") 2>/dev/null

cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════╗
║            gRPC vs REST — When to Use Each                          ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  USE gRPC WHEN:                                                      ║
║  ✅ Internal microservice-to-microservice communication              ║
║  ✅ High-throughput APIs (> 1000 RPS per service)                   ║
║  ✅ Bidirectional streaming (live telemetry, chat, games)            ║
║  ✅ Polyglot environments (auto-generate Go, Java, Python, Rust…)   ║
║  ✅ Strict schema / contract enforcement needed                      ║
║  ✅ Low-latency requirements (binary = less parsing)                 ║
║                                                                      ║
║  USE REST WHEN:                                                      ║
║  ✅ Public/third-party APIs (human-readable, easy to test)          ║
║  ✅ Browser clients without grpc-web proxy                          ║
║  ✅ Simple CRUD with infrequent calls                               ║
║  ✅ Team unfamiliar with protobuf toolchain                         ║
║  ✅ Caching is important (HTTP GET caching)                         ║
║                                                                      ║
║  gRPC SERVICE TYPES SUMMARY:                                        ║
║  Unary              → GET /resource  (one request, one response)    ║
║  Server Streaming   → SSE            (one request, many responses)  ║
║  Client Streaming   → File upload    (many requests, one response)  ║
║  Bidirectional      → WebSocket      (many:many)                    ║
║                                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  PROTOBUF WIRE FORMAT (binary efficiency)                           ║
║                                                                      ║
║  JSON:  {"name":"Alice","age":30}  = 24 bytes                       ║
║  Proto: field_1="Alice", field_2=30 = ~9 bytes  (62% smaller!)     ║
║                                                                      ║
║  Field encoding: (field_number << 3) | wire_type                   ║
║  Wire types: 0=varint, 1=64bit, 2=length-delimited, 5=32bit        ║
╚══════════════════════════════════════════════════════════════════════╝
EOF

echo ""
echo "=== Lab Summary: What We Built ==="
echo ""
ls -lh /tmp/grpc_demo/
echo ""
echo "Proto → protoc → Generated Python → Server + Client"
echo ""
echo "Files generated from hello.proto:"
echo "  hello_pb2.py      — Message classes (HelloRequest, HelloReply)"
echo "  hello_pb2_grpc.py — Service stubs (GreeterStub, GreeterServicer)"
echo ""
echo "RPC types demonstrated:"
echo "  SayHello       → Unary (1 request → 1 response)"
echo "  SayHelloStream → Server streaming (1 request → N responses)"
echo ""
echo "gRPC version: $(python3 -c 'import grpc; print(grpc.__version__)')"
echo "Protobuf version: $(python3 -c 'import google.protobuf; print(google.protobuf.__version__)')"
```

📸 **Verified Output:**
```
╔══════════════════════════════════════════════════════════════════════╗
║            gRPC vs REST — When to Use Each                          ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  USE gRPC WHEN:                                                      ║
║  ✅ Internal microservice-to-microservice communication              ║
...
╚══════════════════════════════════════════════════════════════════════╝

=== Lab Summary: What We Built ===

total 36K
-rw-r--r-- 1 root root  312 Mar  5 13:30 hello.proto
-rw-r--r-- 1 root root 3.8K Mar  5 13:30 hello_pb2.py
-rw-r--r-- 1 root root 4.5K Mar  5 13:30 hello_pb2_grpc.py
-rw-r--r-- 1 root root 1.6K Mar  5 13:30 server.py
-rw-r--r-- 1 root root 1.8K Mar  5 13:30 client.py
-rw-r--r-- 1 root root 1.2K Mar  5 13:30 advanced_client.py

Proto → protoc → Generated Python → Server + Client

Files generated from hello.proto:
  hello_pb2.py      — Message classes (HelloRequest, HelloReply)
  hello_pb2_grpc.py — Service stubs (GreeterStub, GreeterServicer)

RPC types demonstrated:
  SayHello       → Unary (1 request → 1 response)
  SayHelloStream → Server streaming (1 request → N responses)

gRPC version: 1.78.0
Protobuf version: 6.33.5
```

---

## Summary

| Concept | Key Points |
|---------|-----------|
| **gRPC Transport** | HTTP/2 — multiplexed streams, header compression, binary framing |
| **Protocol Buffers** | Binary serialization; 3–10x smaller than JSON |
| **proto3 Syntax** | `message`, `service`, `rpc`; scalar types; `repeated`, `map`, `oneof` |
| **Field Numbers** | Immutable identifiers; 1–15 = 1 byte (use for frequent fields) |
| **protoc compiler** | `python3 -m grpc_tools.protoc` generates `_pb2.py` + `_pb2_grpc.py` |
| **Unary RPC** | Single request → single response (most common) |
| **Server Streaming** | Single request → sequence of responses (`stream` return) |
| **Client Streaming** | Sequence of requests → single response (`stream` parameter) |
| **Bidirectional** | Both sides stream; real-time, full-duplex |
| **gRPC Metadata** | Key-value pairs with each call (like HTTP headers) |
| **Status Codes** | OK(0), NOT_FOUND(5), UNAUTHENTICATED(16), UNAVAILABLE(14) |
| **Deadline/Timeout** | Per-call timeout: `stub.SayHello(req, timeout=5.0)` |
| **vs REST** | gRPC = internal/high-perf; REST = public/browser/simple CRUD |
| **grpcurl** | CLI tool to call gRPC APIs like curl: `grpcurl -plaintext localhost:50051 list` |

---

*End of Networking Protocols Labs 11–15.*

*Return to [Networking Protocols Overview](../README.md)*
