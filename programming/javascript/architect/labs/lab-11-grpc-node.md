# Lab 11: gRPC in Node.js — Proto Loading, Streaming & Interceptors

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

gRPC is the backbone of microservice communication. This lab covers loading `.proto` files at runtime, all four RPC patterns (unary, server-streaming, client-streaming, bidirectional), interceptors, and deadlines.

---

## Step 1: gRPC Architecture

```
Client                          Server
  │                               │
  ├──── Unary RPC ───────────────→│  req/res (like HTTP)
  │                               │
  ├──── Server Streaming ────────→│  one req, stream of responses
  │←──────────────────────────────│
  │                               │
  ├──── Client Streaming ────────→│  stream of requests, one response
  │←──────────────────────────────│
  │                               │
  ├──── Bidirectional ───────────→│  full-duplex streaming
  │←──────────────────────────────│
```

Transport: HTTP/2 (multiplexed, binary framing, header compression)
Serialization: Protocol Buffers (3-10x smaller than JSON)

---

## Step 2: Install Dependencies

```bash
npm install @grpc/grpc-js @grpc/proto-loader
```

---

## Step 3: Define the Proto File

```protobuf
// file: service.proto
syntax = "proto3";
package architect;

// Unary + Streaming service
service DataService {
  // Unary: single request, single response
  rpc GetUser (GetUserRequest) returns (User);

  // Server streaming: one request, stream of responses
  rpc ListUsers (ListUsersRequest) returns (stream User);

  // Client streaming: stream of requests, one response
  rpc BulkCreate (stream CreateUserRequest) returns (BulkCreateResponse);

  // Bidirectional: stream both ways
  rpc Chat (stream ChatMessage) returns (stream ChatMessage);
}

message GetUserRequest { int32 id = 1; }
message ListUsersRequest { int32 limit = 1; }
message CreateUserRequest { string name = 1; string email = 2; }
message BulkCreateResponse { int32 created = 1; repeated string errors = 2; }
message ChatMessage { string user = 1; string text = 2; int64 timestamp = 3; }
message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
  string role = 4;
}
```

---

## Step 4: gRPC Server Implementation

```javascript
// file: server.js
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

// Load proto at runtime (no code generation needed)
const packageDef = protoLoader.loadSync(
  path.join(__dirname, 'service.proto'),
  {
    keepCase: true,
    longs: String,
    enums: String,
    defaults: true,
    oneofs: true,
  }
);

const proto = grpc.loadPackageDefinition(packageDef).architect;

// Sample data
const users = [
  { id: 1, name: 'Alice', email: 'alice@example.com', role: 'admin' },
  { id: 2, name: 'Bob', email: 'bob@example.com', role: 'user' },
  { id: 3, name: 'Carol', email: 'carol@example.com', role: 'user' },
];

const serviceImpl = {
  // Unary RPC
  getUser(call, callback) {
    const user = users.find(u => u.id === call.request.id);
    if (!user) {
      return callback({ code: grpc.status.NOT_FOUND, message: `User ${call.request.id} not found` });
    }
    callback(null, user);
  },

  // Server streaming
  listUsers(call) {
    const limit = call.request.limit || users.length;
    for (const user of users.slice(0, limit)) {
      call.write(user);
    }
    call.end();
  },

  // Client streaming
  bulkCreate(call, callback) {
    const created = [];
    const errors = [];
    call.on('data', (req) => {
      if (!req.name || !req.email) {
        errors.push(`Invalid: ${JSON.stringify(req)}`);
      } else {
        const id = users.length + created.length + 1;
        created.push({ id, ...req, role: 'user' });
      }
    });
    call.on('end', () => {
      users.push(...created);
      callback(null, { created: created.length, errors });
    });
  },

  // Bidirectional streaming
  chat(call) {
    call.on('data', (msg) => {
      // Echo with server prefix
      call.write({
        user: 'server',
        text: `Echo: ${msg.text}`,
        timestamp: Date.now(),
      });
    });
    call.on('end', () => call.end());
    call.on('error', console.error);
  },
};

const server = new grpc.Server();
server.addService(proto.DataService.service, serviceImpl);

module.exports = { server, proto };
```

---

## Step 5: gRPC Client — Unary Call

```javascript
// file: client-unary.js
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const path = require('path');

const packageDef = protoLoader.loadSync(path.join(__dirname, 'service.proto'), {
  keepCase: true, longs: String, enums: String, defaults: true, oneofs: true,
});
const proto = grpc.loadPackageDefinition(packageDef).architect;

const client = new proto.DataService(
  'localhost:50051',
  grpc.credentials.createInsecure()
);

// Unary call
client.getUser({ id: 1 }, (err, user) => {
  if (err) { console.error('Error:', err.message); return; }
  console.log('Got user:', user);
});

// With deadline
const deadline = new Date();
deadline.setSeconds(deadline.getSeconds() + 5); // 5 second timeout

client.getUser({ id: 999 }, { deadline }, (err, user) => {
  if (err) console.log('Expected error:', err.details);
});
```

---

## Step 6: Complete Server + Client Test

```javascript
// file: grpc-complete.js
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const fs = require('fs');
const path = require('path');

// Write proto inline
const PROTO_CONTENT = `
syntax = "proto3";
package hello;
service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);
  rpc SayManyHellos (HelloRequest) returns (stream HelloReply);
}
message HelloRequest { string name = 1; }
message HelloReply { string message = 1; int32 index = 2; }
`;

const protoPath = '/tmp/hello.proto';
fs.writeFileSync(protoPath, PROTO_CONTENT);

const def = protoLoader.loadSync(protoPath, {
  keepCase: true, longs: String, enums: String, defaults: true, oneofs: true
});
const pkg = grpc.loadPackageDefinition(def).hello;

// Server
const server = new grpc.Server();
server.addService(pkg.Greeter.service, {
  sayHello: (call, cb) => {
    cb(null, { message: `Hello, ${call.request.name}!`, index: 0 });
  },
  sayManyHellos: (call) => {
    for (let i = 1; i <= 3; i++) {
      call.write({ message: `Hello #${i}, ${call.request.name}!`, index: i });
    }
    call.end();
  },
});

server.bindAsync('127.0.0.1:50051', grpc.ServerCredentials.createInsecure(), (err, port) => {
  if (err) { console.error(err); process.exit(1); }
  console.log('gRPC server on port', port);

  const client = new pkg.Greeter('127.0.0.1:50051', grpc.credentials.createInsecure());

  // Unary call
  client.sayHello({ name: 'Architect' }, (err, res) => {
    if (err) { console.error(err); process.exit(1); }
    console.log('Unary response:', res.message);

    // Server streaming
    const stream = client.sayManyHellos({ name: 'Architect' });
    const messages = [];
    stream.on('data', (msg) => messages.push(msg.message));
    stream.on('end', () => {
      console.log('Server streaming:', messages);
      server.forceShutdown();
      process.exit(0);
    });
  });
});
```

📸 **Verified Output:**
```
gRPC server on port 50051
Unary response: Hello, Architect!
Server streaming: [ 'Hello #1, Architect!', 'Hello #2, Architect!', 'Hello #3, Architect!' ]
```

---

## Step 7: Interceptors

```javascript
// file: interceptors.js
const grpc = require('@grpc/grpc-js');

// Client interceptor: add auth token to every call
function authInterceptor(options, nextCall) {
  return new grpc.InterceptingCall(nextCall(options), {
    start(metadata, listener, next) {
      // Add auth header
      metadata.add('authorization', 'Bearer my-jwt-token');
      metadata.add('x-request-id', Math.random().toString(36).slice(2));
      next(metadata, {
        onReceiveMessage(message, next) {
          console.log('[Interceptor] Received message:', message ? 'yes' : 'empty');
          next(message);
        },
        onReceiveStatus(status, next) {
          console.log('[Interceptor] Call status:', status.code, grpc.status[status.code]);
          next(status);
        },
      });
    },
  });
}

// Server interceptor: logging
function loggingInterceptor(methodDefinition, handler) {
  return {
    ...handler,
    func(call, callback) {
      const start = Date.now();
      const originalCb = callback;
      const wrappedCb = (err, response) => {
        console.log(`[Server] ${methodDefinition.path} took ${Date.now() - start}ms, err=${err?.code ?? 'none'}`);
        originalCb(err, response);
      };
      handler.func(call, wrappedCb);
    }
  };
}

// Usage: client with interceptors
// const client = new proto.Service(addr, creds, {
//   interceptors: [authInterceptor],
// });

console.log('Interceptor patterns defined');
console.log('Use { interceptors: [fn] } in channel options');
```

---

## Step 8: Capstone — Resilient gRPC Client

```javascript
// file: resilient-client.js
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const fs = require('fs');

const PROTO = `
syntax = "proto3";
package resilient;
service TaskService {
  rpc Process (TaskRequest) returns (TaskResponse);
}
message TaskRequest { string id = 1; string payload = 2; }
message TaskResponse { string result = 1; int32 durationMs = 2; }
`;
fs.writeFileSync('/tmp/task.proto', PROTO);

const def = protoLoader.loadSync('/tmp/task.proto', {
  keepCase: true, longs: String, enums: String, defaults: true, oneofs: true
});
const pkg = grpc.loadPackageDefinition(def).resilient;

// Resilient client with retry and timeout
class ResilientGRPCClient {
  constructor(address, maxRetries = 3, timeoutMs = 5000) {
    this.client = new pkg.TaskService(address, grpc.credentials.createInsecure(), {
      'grpc.keepalive_time_ms': 10000,
      'grpc.keepalive_timeout_ms': 5000,
      'grpc.keepalive_permit_without_calls': 1,
    });
    this.maxRetries = maxRetries;
    this.timeoutMs = timeoutMs;
  }

  async process(request, retries = 0) {
    const deadline = new Date(Date.now() + this.timeoutMs);
    return new Promise((resolve, reject) => {
      this.client.process(request, { deadline }, (err, response) => {
        if (!err) return resolve(response);

        // Retry on transient errors
        const retryable = [grpc.status.UNAVAILABLE, grpc.status.RESOURCE_EXHAUSTED];
        if (retryable.includes(err.code) && retries < this.maxRetries) {
          const delay = Math.pow(2, retries) * 100; // exponential backoff
          console.log(`  Retry ${retries + 1}/${this.maxRetries} after ${delay}ms`);
          setTimeout(() => this.process(request, retries + 1).then(resolve, reject), delay);
        } else {
          reject(err);
        }
      });
    });
  }

  close() { grpc.closeClient(this.client); }
}

// Server
const server = new grpc.Server();
let callCount = 0;
server.addService(pkg.TaskService.service, {
  process(call, cb) {
    callCount++;
    const start = Date.now();
    // Simulate occasional failures
    if (callCount % 3 === 0) {
      return cb({ code: grpc.status.UNAVAILABLE, message: 'Server temporarily unavailable' });
    }
    setTimeout(() => {
      cb(null, {
        result: `Processed: ${call.request.payload}`,
        durationMs: Date.now() - start,
      });
    }, 10);
  }
});

server.bindAsync('127.0.0.1:50052', grpc.ServerCredentials.createInsecure(), async (err, port) => {
  if (err) { console.error(err); process.exit(1); }
  console.log('Resilient gRPC server on port', port);

  const client = new ResilientGRPCClient('127.0.0.1:50052');

  for (let i = 1; i <= 5; i++) {
    try {
      const res = await client.process({ id: `task-${i}`, payload: `data-${i}` });
      console.log(`Task ${i}: ${res.result} (${res.durationMs}ms)`);
    } catch (e) {
      console.log(`Task ${i} failed permanently: ${e.message}`);
    }
  }

  client.close();
  server.forceShutdown();
  process.exit(0);
});
```

---

## Summary

| Pattern | Direction | Use Case |
|---|---|---|
| Unary RPC | req → res | Standard API call |
| Server streaming | req → stream | Real-time feeds, logs |
| Client streaming | stream → res | File upload, batch ingest |
| Bidirectional | stream ↔ stream | Chat, real-time sync |
| Interceptors | Both | Auth, logging, metrics |
| Deadlines | Client | Prevent hanging calls |
| Status codes | Both | Error classification |
| Retry + backoff | Client | Transient failure recovery |
