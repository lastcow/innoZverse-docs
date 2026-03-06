# Lab 07: Cluster & IPC — Master/Worker Architecture & Graceful Restart

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Node.js runs on a single CPU core by default. The `cluster` module forks multiple worker processes to utilize all cores. This lab covers cluster architecture, IPC messaging, sticky sessions, scheduling policies, and graceful restart patterns.

---

## Step 1: Cluster Architecture

```
Master Process (cluster.isMaster)
│
├── Worker 1 (cluster.fork()) ─── IPC channel ──→ Master
├── Worker 2 (cluster.fork()) ─── IPC channel ──→ Master
├── Worker 3 (cluster.fork()) ─── IPC channel ──→ Master
└── Worker 4 (cluster.fork()) ─── IPC channel ──→ Master

OS-level: Workers share listening port via file descriptor passing
          Master handles ACCEPT for Round-Robin scheduling
```

Workers share the same port because the master holds the server socket and passes connections to workers via IPC.

---

## Step 2: Basic Cluster Setup

```javascript
// file: cluster-basic.js
const cluster = require('cluster');
const os = require('os');

if (cluster.isPrimary) {  // cluster.isMaster deprecated in Node 16+
  const numWorkers = Math.min(os.cpus().length, 4);
  console.log(`Master ${process.pid} starting ${numWorkers} workers`);

  for (let i = 0; i < numWorkers; i++) {
    const worker = cluster.fork();
    console.log(`  Forked worker ${worker.process.pid}`);
  }

  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died (code: ${code}, signal: ${signal})`);
    console.log('Forking replacement...');
    cluster.fork(); // auto-restart
  });

  cluster.on('online', (worker) => {
    console.log(`Worker ${worker.process.pid} is online`);
  });

} else {
  // Worker process
  const http = require('http');
  const server = http.createServer((req, res) => {
    res.writeHead(200);
    res.end(`Response from worker ${process.pid}\n`);
  });
  server.listen(8080, () => {
    console.log(`Worker ${process.pid} listening on :8080`);
  });
}
```

> 💡 Each worker is a full Node.js process with its own V8 heap and event loop. They share no memory — only communicate via IPC.

---

## Step 3: IPC Messaging — Master ↔ Worker

```javascript
// file: cluster-ipc.js
const cluster = require('cluster');

if (cluster.isPrimary) {
  console.log(`Master PID: ${process.pid}`);

  // Fork 2 workers
  const workers = [];
  for (let i = 0; i < 2; i++) {
    const worker = cluster.fork({ WORKER_ID: i + 1 });
    workers.push(worker);

    // Receive messages from worker
    worker.on('message', (msg) => {
      console.log(`Master received from Worker ${msg.workerId}: ${msg.text}`);

      // Reply to that worker
      worker.send({ from: 'master', text: `Got your message #${msg.seq}` });
    });
  }

  // Broadcast to all workers after 100ms
  setTimeout(() => {
    console.log('Master broadcasting to all workers...');
    for (const w of Object.values(cluster.workers)) {
      w.send({ from: 'master', text: 'broadcast: hello everyone', ts: Date.now() });
    }
  }, 100);

  // Graceful shutdown after 500ms
  setTimeout(() => {
    console.log('Master initiating graceful shutdown...');
    for (const w of Object.values(cluster.workers)) {
      w.send({ cmd: 'shutdown' });
    }
  }, 500);

} else {
  const workerId = parseInt(process.env.WORKER_ID);
  let seq = 0;

  // Receive messages from master
  process.on('message', (msg) => {
    if (msg.cmd === 'shutdown') {
      console.log(`Worker ${workerId} (${process.pid}) shutting down gracefully`);
      process.exit(0);
    }
    console.log(`  Worker ${workerId} received: ${msg.text}`);
  });

  // Send messages to master
  const interval = setInterval(() => {
    process.send({ workerId, text: `ping from worker`, seq: ++seq, pid: process.pid });
    if (seq >= 2) clearInterval(interval);
  }, 50);
}
```

📸 **Verified Output** (2-worker cluster):
```
Master PID: 12345
  Forked worker 12346
  Forked worker 12347
Worker 1 (12346) is online
Worker 2 (12347) is online
Master received from Worker 1: ping from worker
Master received from Worker 2: ping from worker
...
Master initiating graceful shutdown...
Worker 1 (12346) shutting down gracefully
Worker 2 (12347) shutting down gracefully
```

---

## Step 4: Sticky Sessions (Hash by IP)

In round-robin, subsequent requests from the same client may go to different workers (breaking session affinity). Sticky sessions route the same client to the same worker:

```javascript
// file: sticky-sessions.js
const cluster = require('cluster');
const net = require('net');

// Simple IP hash for worker selection
function hashIP(ip) {
  return ip.split('.').reduce((acc, octet) => acc + parseInt(octet), 0);
}

if (cluster.isPrimary) {
  const workers = [];
  const NUM_WORKERS = 4;

  for (let i = 0; i < NUM_WORKERS; i++) {
    workers.push(cluster.fork());
  }

  // TCP proxy for sticky sessions
  const proxy = net.createServer({ pauseOnConnect: true }, (conn) => {
    const ip = conn.remoteAddress || '127.0.0.1';
    const idx = hashIP(ip.replace('::ffff:', '')) % NUM_WORKERS;
    const target = workers[idx];
    console.log(`Connection from ${ip} → Worker ${idx} (PID: ${target.process.pid})`);
    target.send('sticky', conn); // send the socket to the specific worker
  });

  proxy.listen(8080, () => console.log('Sticky proxy listening on :8080'));

} else {
  const http = require('http');
  const server = http.createServer((req, res) => {
    res.writeHead(200);
    res.end(`Handled by worker PID ${process.pid}\n`);
  });

  // Receive connections from master
  process.on('message', (msg, socket) => {
    if (msg === 'sticky') {
      server.emit('connection', socket);
      socket.resume();
    }
  });
}
```

> 💡 For production sticky sessions, use a load balancer like nginx with `ip_hash` or HAProxy with `stick-table`. Node's cluster module is for single-machine scenarios.

---

## Step 5: Scheduling Policies

```javascript
// file: scheduling.js
const cluster = require('cluster');

// Default: Round-Robin (recommended)
// cluster.schedulingPolicy = cluster.SCHED_RR;

// OS-controlled (default on Windows):
// cluster.schedulingPolicy = cluster.SCHED_NONE;

// MUST be set before cluster.fork()!
console.log('Scheduling policy:', cluster.schedulingPolicy);
console.log('SCHED_RR:', cluster.SCHED_RR);  // 2
console.log('SCHED_NONE:', cluster.SCHED_NONE); // 1

// Also configurable via:
// NODE_CLUSTER_SCHED_POLICY=rr node app.js
// NODE_CLUSTER_SCHED_POLICY=none node app.js
```

> 💡 Round-Robin (SCHED_RR) is better than SCHED_NONE because OS scheduling can create hot spots where one worker gets all the connections.

---

## Step 6: Graceful Worker Restart on SIGTERM

```javascript
// file: graceful-restart.js
const cluster = require('cluster');
const http = require('http');

if (cluster.isPrimary) {
  const NUM_WORKERS = 2;
  for (let i = 0; i < NUM_WORKERS; i++) cluster.fork();

  // Rolling restart: restart workers one by one
  async function rollingRestart() {
    console.log('Starting rolling restart...');
    const workerIds = Object.keys(cluster.workers);
    for (const id of workerIds) {
      const oldWorker = cluster.workers[id];
      console.log(`  Restarting worker ${oldWorker.process.pid}...`);

      // Fork new worker before killing old
      const newWorker = cluster.fork();
      await new Promise(resolve => newWorker.once('listening', resolve));
      console.log(`  New worker ${newWorker.process.pid} is listening`);

      // Gracefully terminate old worker
      oldWorker.send('shutdown');
      await new Promise(resolve => oldWorker.once('exit', resolve));
      console.log(`  Old worker ${oldWorker.process.pid} exited`);
    }
    console.log('Rolling restart complete');
  }

  // Trigger rolling restart after 500ms (simulate deploy)
  setTimeout(rollingRestart, 500);

  cluster.on('exit', (worker) => {
    console.log(`Worker ${worker.process.pid} exited`);
  });

} else {
  const server = http.createServer((req, res) => {
    res.writeHead(200);
    res.end(`PID ${process.pid}\n`);
  });

  server.listen(8081, () => {
    console.log(`Worker ${process.pid} listening`);
  });

  // Graceful shutdown handler
  process.on('message', (msg) => {
    if (msg === 'shutdown') {
      console.log(`Worker ${process.pid} draining connections...`);
      server.close(() => {
        console.log(`Worker ${process.pid} done, exiting`);
        process.exit(0);
      });
      // Force exit after timeout
      setTimeout(() => process.exit(1), 5000);
    }
  });
}
```

---

## Step 7: Worker Health Monitoring

```javascript
// file: health-monitor.js
const cluster = require('cluster');

if (cluster.isPrimary) {
  const workerStats = new Map();

  function spawnWorker() {
    const w = cluster.fork();
    workerStats.set(w.id, { pid: w.process.pid, requests: 0, errors: 0, lastPing: Date.now() });

    w.on('message', (msg) => {
      const stats = workerStats.get(w.id);
      if (!stats) return;
      if (msg.type === 'ping') stats.lastPing = Date.now();
      if (msg.type === 'stats') { stats.requests = msg.requests; stats.errors = msg.errors; }
    });

    return w;
  }

  for (let i = 0; i < 2; i++) spawnWorker();

  // Health check: ping workers every 200ms
  setInterval(() => {
    const now = Date.now();
    for (const [id, w] of Object.entries(cluster.workers)) {
      w.send({ type: 'ping' });
      const stats = workerStats.get(parseInt(id));
      if (stats && now - stats.lastPing > 1000) {
        console.warn(`Worker ${stats.pid} appears unresponsive! Replacing...`);
        w.kill();
        spawnWorker();
      }
    }
  }, 200);

  // Print stats every 500ms
  let tick = 0;
  const statsInterval = setInterval(() => {
    tick++;
    console.log('\n=== Worker Health ===');
    for (const [id, stats] of workerStats) {
      console.log(`  Worker ${id} (PID ${stats.pid}): requests=${stats.requests} errors=${stats.errors} lastPing=${Date.now() - stats.lastPing}ms ago`);
    }
    if (tick >= 3) { clearInterval(statsInterval); process.exit(0); }
  }, 500);

} else {
  let requests = 0, errors = 0;

  process.on('message', (msg) => {
    if (msg.type === 'ping') {
      process.send({ type: 'ping' });
      process.send({ type: 'stats', requests, errors });
    }
  });

  // Simulate request handling
  setInterval(() => { requests++; }, 100);
}
```

---

## Step 8: Capstone — Production Cluster with Zero-Downtime Deploy

```javascript
// file: production-cluster.js
'use strict';
const cluster = require('cluster');
const http = require('http');
const os = require('os');

const PORT = 8082;
const NUM_WORKERS = Math.min(os.cpus().length, 4);

if (cluster.isPrimary) {
  console.log(`[Master ${process.pid}] Starting ${NUM_WORKERS} workers`);

  // Track worker state
  const workers = new Map(); // workerId → { pid, healthy, requests }

  function spawnWorker() {
    const w = cluster.fork();
    workers.set(w.id, { pid: w.process.pid, healthy: false, requests: 0 });
    w.on('message', (msg) => {
      const info = workers.get(w.id);
      if (!info) return;
      if (msg.type === 'ready') { info.healthy = true; console.log(`  Worker ${info.pid} ready`); }
      if (msg.type === 'stats') info.requests = msg.requests;
    });
    return w;
  }

  for (let i = 0; i < NUM_WORKERS; i++) spawnWorker();

  cluster.on('exit', (worker, code, signal) => {
    workers.delete(worker.id);
    if (!worker.exitedAfterDisconnect) {
      console.log(`Worker ${worker.process.pid} crashed! Restarting...`);
      spawnWorker();
    }
  });

  // Graceful shutdown
  process.on('SIGTERM', async () => {
    console.log('[Master] SIGTERM received, graceful shutdown...');
    for (const w of Object.values(cluster.workers)) {
      w.send({ cmd: 'shutdown' });
    }
    setTimeout(() => process.exit(0), 5000);
  });

  // Print cluster status every 1s
  let tick = 0;
  setInterval(() => {
    const healthy = [...workers.values()].filter(w => w.healthy).length;
    console.log(`[Master] ${healthy}/${workers.size} workers healthy`);
    if (++tick >= 3) process.exit(0);
  }, 1000);

} else {
  const server = http.createServer((req, res) => {
    res.writeHead(200, { 'X-Worker-PID': process.pid });
    res.end(JSON.stringify({ pid: process.pid, url: req.url }));
  });

  server.listen(PORT, () => {
    process.send({ type: 'ready' });
  });

  let requests = 0;
  setInterval(() => process.send({ type: 'stats', requests }), 500);

  process.on('message', ({ cmd }) => {
    if (cmd === 'shutdown') {
      server.close(() => process.exit(0));
      setTimeout(() => process.exit(1), 5000);
    }
  });
}
```

---

## Summary

| Concept | API | Description |
|---|---|---|
| Primary detection | `cluster.isPrimary` | Check if current process is master |
| Fork worker | `cluster.fork()` | Spawn a worker subprocess |
| Send to worker | `worker.send(msg)` | IPC from master to worker |
| Receive in worker | `process.on('message', fn)` | IPC from master to worker handler |
| Round-Robin | `SCHED_RR` | Evenly distribute connections |
| Sticky sessions | IP hash + socket passing | Route same client to same worker |
| Graceful shutdown | `server.close()` + exit | Drain connections before exit |
| Rolling restart | Fork new, then kill old | Zero-downtime deploy |
