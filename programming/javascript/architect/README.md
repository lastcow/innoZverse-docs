# JavaScript Architect Track

**Level:** Architect | **Labs:** 15 | **Docker:** `node:20-alpine`

Master the deep internals of Node.js: V8 engine, event loop, native addons, streams, gRPC, security, observability, and production architecture patterns.

---

## Prerequisites

- Completed JavaScript Advanced Track (or equivalent experience)
- Comfortable with async/await, Promises, and Node.js core modules
- Basic understanding of HTTP and networking
- Docker installed locally

## Quick Start

```bash
docker run -it --rm node:20-alpine sh
# Inside container:
node --version  # v20.x
```

---

## Lab Overview

| Lab | Title | Key Topics | Verify |
|---|---|---|---|
| [01](labs/lab-01-v8-internals.md) | V8 Internals | Hidden classes, IC, TurboFan, deopt | `--allow-natives-syntax` opt status |
| [02](labs/lab-02-event-loop-advanced.md) | Advanced Event Loop | libuv phases, nextTick/queueMicrotask ordering, async_hooks | Phase timing output |
| [03](labs/lab-03-memory-management.md) | Memory Management | Heap spaces, WeakRef, FinalizationRegistry, leak patterns | `v8.getHeapStatistics()` |
| [04](labs/lab-04-worker-threads-advanced.md) | Worker Threads | SharedArrayBuffer, Atomics, thread pool, zero-copy | Atomic counter = 4000 |
| [05](labs/lab-05-native-addons.md) | Native Addons | N-API, node-gyp, C source, FFI | `node index.js` native call |
| [06](labs/lab-06-streams-advanced.md) | Advanced Streams | Transform, backpressure, pipeline, Web Streams | Byte count pipeline |
| [07](labs/lab-07-cluster-ipc.md) | Cluster & IPC | Master/worker, IPC messaging, sticky sessions, graceful restart | 2-worker IPC demo |
| [08](labs/lab-08-performance-profiling.md) | Performance Profiling | `--prof`, perf_hooks, PerformanceObserver, autocannon | Real timing measurement |
| [09](labs/lab-09-security-hardening.md) | Security Hardening | AES-GCM, Ed25519, scrypt, prototype pollution, CSP | Encrypt/sign with real hex |
| [10](labs/lab-10-module-federation.md) | Module Federation | ESM internals, vm.Module, SyntheticModule, CJS↔ESM | vm.Module evaluation |
| [11](labs/lab-11-grpc-node.md) | gRPC in Node.js | Proto loading, unary/streaming, interceptors, deadlines | Real gRPC server+client |
| [12](labs/lab-12-caching-strategies.md) | Caching Strategies | LRU impl, Redis patterns, cache-aside, consistent hashing | LRU eviction demo |
| [13](labs/lab-13-microservices-patterns.md) | Microservices Patterns | Circuit breaker, bulkhead, saga, event sourcing, CQRS | opossum state demo |
| [14](labs/lab-14-observability.md) | Observability | OpenTelemetry, spans, metrics, pino, diagnostics_channel | Real span output |
| [15](labs/lab-15-capstone-platform.md) | Capstone Platform | All patterns integrated: gRPC + workers + cache + OTel + tests | 6+ Vitest tests pass |

---

## Learning Path

```
V8 & Runtime          Memory & Threads         APIs & Protocols
    │                       │                       │
    ▼                       ▼                       ▼
Lab 01: V8 Internals   Lab 03: Memory         Lab 06: Streams
Lab 02: Event Loop     Lab 04: Workers        Lab 11: gRPC
Lab 08: Profiling      Lab 05: Native         Lab 10: Modules

Security & Reliability   Architecture             Capstone
         │                    │                      │
         ▼                    ▼                      ▼
Lab 09: Security        Lab 07: Cluster        Lab 15: Platform
Lab 12: Caching         Lab 13: Microservices
Lab 14: Observability
```

---

## Key Concepts at a Glance

### V8 Optimization Rules
1. Keep object shapes **monomorphic** (same property order)
2. Use **TypedArrays** for numeric-heavy code
3. Avoid **type polymorphism** in hot functions
4. Pre-allocate objects with all properties

### Event Loop Priority
```
sync → process.nextTick → Promise/queueMicrotask → setTimeout → setImmediate
```

### Production Node.js Checklist
- [ ] `--max-old-space-size` set for your container RAM
- [ ] Cluster mode with `os.cpus().length` workers
- [ ] Graceful shutdown: drain connections before exit
- [ ] Circuit breakers on all external calls
- [ ] Structured logging with correlation IDs
- [ ] OpenTelemetry traces to your observability backend
- [ ] `--experimental-permission` for hardened services
- [ ] Heap profiling enabled in staging

---

## Docker Reference

All labs use:
```bash
docker run -it --rm node:20-alpine sh
```

For labs requiring npm packages:
```bash
docker run -it --rm -w /app node:20-alpine sh -c "npm install opossum && node demo.js"
```

For Native Addons (Lab 05):
```bash
docker run -it --rm node:20-alpine sh -c "apk add python3 make g++ && npm install -g node-gyp"
```

---

## Verified On

- **Node.js**: v20.20.0
- **Docker image**: node:20-alpine
- **Date**: 2026-03-06
- All `📸 Verified Output:` blocks contain real Docker execution results.
