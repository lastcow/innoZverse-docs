# Lab 08: WebSockets & Real-Time

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build real-time applications with the `ws` module: broadcasting, rooms/namespaces, heartbeat/ping-pong, reconnection logic, and message queuing for disconnected clients.

---

## Step 1: Setup

```bash
cd /tmp && npm init -y --quiet
npm install ws
```

---

## Step 2: Basic WebSocket Server & Client

```javascript
const WebSocket = require('ws');

// Server
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws, req) => {
  const clientId = Math.random().toString(36).slice(2, 9);
  ws.clientId = clientId;
  console.log(`Client connected: ${clientId}`);

  // Send welcome message
  ws.send(JSON.stringify({ type: 'WELCOME', clientId }));

  ws.on('message', (data, isBinary) => {
    try {
      const message = JSON.parse(data.toString());
      console.log(`Message from ${clientId}:`, message);

      // Echo back
      ws.send(JSON.stringify({ type: 'ECHO', original: message, clientId }));
    } catch {
      ws.send(JSON.stringify({ type: 'ERROR', message: 'Invalid JSON' }));
    }
  });

  ws.on('close', (code, reason) => {
    console.log(`Client disconnected: ${clientId} (${code})`);
  });

  ws.on('error', (err) => {
    console.error(`Error from ${clientId}:`, err.message);
  });
});

// Client
const ws = new WebSocket('ws://localhost:8080');

ws.on('open', () => {
  console.log('Connected to server');
  ws.send(JSON.stringify({ type: 'HELLO', message: 'Hi from client!' }));
});

ws.on('message', (data) => {
  const msg = JSON.parse(data.toString());
  console.log('Received:', msg);
  if (msg.type === 'ECHO') ws.close();
});
```

---

## Step 3: Broadcasting

```javascript
const WebSocket = require('ws');

class ChatServer {
  #wss;
  #clients = new Set();

  constructor(port) {
    this.#wss = new WebSocket.Server({ port });
    this.#wss.on('connection', this.#handleConnection.bind(this));
    console.log(`Chat server listening on ws://localhost:${port}`);
  }

  #handleConnection(ws, req) {
    ws.id = Math.random().toString(36).slice(2, 9);
    ws.username = `User-${ws.id.slice(0, 4)}`;
    this.#clients.add(ws);

    this.broadcast({ type: 'JOIN', username: ws.username, count: this.#clients.size }, ws);
    ws.send(JSON.stringify({ type: 'WELCOME', username: ws.username }));

    ws.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        this.#handleMessage(ws, msg);
      } catch {}
    });

    ws.on('close', () => {
      this.#clients.delete(ws);
      this.broadcast({ type: 'LEAVE', username: ws.username, count: this.#clients.size });
    });
  }

  #handleMessage(ws, msg) {
    switch (msg.type) {
      case 'MESSAGE':
        this.broadcast({
          type: 'MESSAGE',
          username: ws.username,
          content: msg.content,
          timestamp: Date.now()
        });
        break;
      case 'SET_NAME':
        ws.username = msg.name;
        ws.send(JSON.stringify({ type: 'NAME_SET', username: ws.username }));
        break;
    }
  }

  // Broadcast to all (or all except sender)
  broadcast(data, exclude = null) {
    const json = JSON.stringify(data);
    for (const client of this.#clients) {
      if (client !== exclude && client.readyState === WebSocket.OPEN) {
        client.send(json);
      }
    }
  }

  // Send to specific client
  sendTo(clientId, data) {
    for (const client of this.#clients) {
      if (client.id === clientId && client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(data));
        return true;
      }
    }
    return false;
  }
}
```

---

## Step 4: Rooms (Namespaces)

```javascript
class RoomManager {
  #rooms = new Map(); // roomId -> Set<ws>

  join(ws, roomId) {
    if (!this.#rooms.has(roomId)) this.#rooms.set(roomId, new Set());
    this.#rooms.get(roomId).add(ws);
    ws.rooms = ws.rooms ?? new Set();
    ws.rooms.add(roomId);
    console.log(`${ws.id} joined room ${roomId}`);
  }

  leave(ws, roomId) {
    this.#rooms.get(roomId)?.delete(ws);
    ws.rooms?.delete(roomId);
    if (this.#rooms.get(roomId)?.size === 0) this.#rooms.delete(roomId);
  }

  leaveAll(ws) {
    for (const roomId of ws.rooms ?? []) this.leave(ws, roomId);
  }

  broadcast(roomId, data, exclude = null) {
    const room = this.#rooms.get(roomId);
    if (!room) return 0;
    const json = JSON.stringify(data);
    let count = 0;
    for (const client of room) {
      if (client !== exclude && client.readyState === WebSocket.OPEN) {
        client.send(json);
        count++;
      }
    }
    return count;
  }

  getRoomSize(roomId) { return this.#rooms.get(roomId)?.size ?? 0; }
  getRooms() { return [...this.#rooms.keys()]; }
}
```

---

## Step 5: Heartbeat / Ping-Pong

```javascript
const WebSocket = require('ws');

const PING_INTERVAL = 30000; // 30 seconds

function setupHeartbeat(wss) {
  function heartbeat() {
    this.isAlive = true; // 'this' is the ws client
  }

  wss.on('connection', (ws) => {
    ws.isAlive = true;
    ws.on('pong', heartbeat); // Built-in WebSocket pong
  });

  const interval = setInterval(() => {
    wss.clients.forEach((ws) => {
      if (!ws.isAlive) {
        console.log('Client timed out, terminating');
        return ws.terminate(); // Force close
      }
      ws.isAlive = false;
      ws.ping(); // Send ping, expect pong
    });
  }, PING_INTERVAL);

  wss.on('close', () => clearInterval(interval));
  return interval;
}

// Custom application-level heartbeat (for environments that strip pings)
function setupAppHeartbeat(wss, intervalMs = 30000) {
  const interval = setInterval(() => {
    const now = Date.now();
    wss.clients.forEach((ws) => {
      if (now - (ws.lastActivity ?? 0) > intervalMs * 2) {
        console.log('Stale connection, closing');
        ws.close(1000, 'Heartbeat timeout');
        return;
      }
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'PING', serverTime: now }));
      }
    });
  }, intervalMs);

  return interval;
}
```

---

## Step 6: Reconnection Logic (Client Side)

```javascript
// Resilient WebSocket client with auto-reconnect
class ReconnectingWebSocket {
  #url; #options; #ws = null;
  #reconnectDelay; #maxDelay; #reconnectAttempts = 0;
  #messageQueue = [];
  #listeners = {};

  constructor(url, options = {}) {
    this.#url = url;
    this.#options = options;
    this.#reconnectDelay = options.initialDelay ?? 1000;
    this.#maxDelay = options.maxDelay ?? 30000;
    this.#connect();
  }

  #connect() {
    try {
      this.#ws = new WebSocket(this.#url, this.#options.protocols);

      this.#ws.on('open', () => {
        console.log('Connected!');
        this.#reconnectAttempts = 0;
        this.#reconnectDelay = this.#options.initialDelay ?? 1000;
        this.#flushQueue();
        this.#emit('open');
      });

      this.#ws.on('message', (data) => {
        this.#emit('message', data);
      });

      this.#ws.on('close', (code) => {
        console.log(`Disconnected (${code}). Reconnecting...`);
        this.#emit('close', code);
        this.#scheduleReconnect();
      });

      this.#ws.on('error', (err) => {
        this.#emit('error', err);
      });
    } catch (err) {
      this.#scheduleReconnect();
    }
  }

  #scheduleReconnect() {
    if (this.#options.maxAttempts && this.#reconnectAttempts >= this.#options.maxAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }
    const delay = Math.min(this.#reconnectDelay * 2 ** this.#reconnectAttempts, this.#maxDelay);
    const jitter = delay * 0.2 * Math.random();
    this.#reconnectAttempts++;
    console.log(`Reconnecting in ${Math.round(delay + jitter)}ms (attempt ${this.#reconnectAttempts})`);
    setTimeout(() => this.#connect(), delay + jitter);
  }

  #flushQueue() {
    while (this.#messageQueue.length > 0) {
      this.#ws.send(this.#messageQueue.shift());
    }
  }

  send(data) {
    const json = typeof data === 'string' ? data : JSON.stringify(data);
    if (this.#ws?.readyState === WebSocket.OPEN) {
      this.#ws.send(json);
    } else {
      this.#messageQueue.push(json); // Queue for when reconnected
    }
  }

  on(event, handler) {
    this.#listeners[event] = this.#listeners[event] ?? [];
    this.#listeners[event].push(handler);
    return this;
  }

  #emit(event, ...args) {
    this.#listeners[event]?.forEach(h => h(...args));
  }

  close() { this.#ws?.close(); }
}
```

---

## Step 7: Message Queue for Offline Clients

```javascript
class OfflineMessageQueue {
  #queues = new Map(); // userId -> messages[]
  #maxMessages;
  #ttl;

  constructor({ maxMessages = 100, ttl = 24 * 60 * 60 * 1000 } = {}) {
    this.#maxMessages = maxMessages;
    this.#ttl = ttl;
  }

  enqueue(userId, message) {
    if (!this.#queues.has(userId)) this.#queues.set(userId, []);
    const queue = this.#queues.get(userId);

    // Remove expired messages
    const now = Date.now();
    while (queue.length > 0 && now - queue[0].enqueuedAt > this.#ttl) queue.shift();

    // Respect max size
    if (queue.length >= this.#maxMessages) queue.shift();

    queue.push({ ...message, enqueuedAt: now });
  }

  dequeue(userId) {
    const messages = this.#queues.get(userId) ?? [];
    this.#queues.delete(userId);
    return messages;
  }

  size(userId) { return this.#queues.get(userId)?.length ?? 0; }
}
```

---

## Step 8: Capstone — WebSocket Server + Client Demo

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && npm init -y --quiet > /dev/null && npm install ws --quiet > /dev/null 2>&1
node -e '
const WebSocket = require(\"/tmp/node_modules/ws\");

const wss = new WebSocket.Server({ port: 8765 });
const messages = [];

wss.on(\"connection\", (ws) => {
  ws.send(JSON.stringify({ type: \"WELCOME\" }));
  ws.on(\"message\", (data) => {
    const msg = JSON.parse(data.toString());
    messages.push(msg.content);
    // Broadcast to all clients
    wss.clients.forEach(client => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify({ type: \"MSG\", content: msg.content }));
      }
    });
  });
});

// Two clients
const client1 = new WebSocket(\"ws://localhost:8765\");
const client2 = new WebSocket(\"ws://localhost:8765\");

client1.on(\"open\", () => {
  setTimeout(() => client1.send(JSON.stringify({ content: \"Hello from client1!\" })), 50);
});

const received = [];
client2.on(\"message\", (data) => {
  const msg = JSON.parse(data.toString());
  if (msg.type === \"MSG\") {
    received.push(msg.content);
    console.log(\"Client2 received:\", msg.content);
    if (received.length >= 1) {
      wss.close();
      client1.close();
      client2.close();
      console.log(\"Server clients count was:\", messages.length > 0 ? \"working\" : \"none\");
    }
  }
});

setTimeout(() => { wss.close(); process.exit(0); }, 3000);
'" 2>/dev/null
```

📸 **Verified Output:**
```
Client2 received: Hello from client1!
Server clients count was: working
```

---

## Summary

| Feature | API | Notes |
|---------|-----|-------|
| Server | `new WebSocket.Server({ port })` | Listens for connections |
| Client | `new WebSocket(url)` | Connects to server |
| Send | `ws.send(string/Buffer)` | Send message |
| Broadcast | Loop `wss.clients` | No built-in broadcast |
| Rooms | Custom `Map<roomId, Set<ws>>` | Group clients |
| Heartbeat | `ws.ping()` + `ws.on('pong')` | Detect dead connections |
| Reconnect | Custom `ReconnectingWebSocket` | Exponential backoff |
| Message queue | Custom queue | Buffer offline messages |
| Close codes | `ws.close(code, reason)` | 1000=normal, 1001=going away |
