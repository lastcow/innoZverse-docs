# Python Architect Track

**Level:** Architect | **15 Labs** | **Docker:** `python:3.11-slim`

Deep-dive into CPython internals, advanced concurrency, security hardening, and production platform engineering. Each lab is independently runnable via Docker.

## Quick Start

```bash
docker run -it --rm python:3.11-slim bash
pip install fastapi uvicorn pydantic pluggy cryptography prometheus-client opentelemetry-sdk
```

## Lab Index

| # | Lab | Topics | Key Verification |
|---|-----|--------|-----------------|
| 01 | [CPython Internals](labs/lab-01-cpython-internals.md) | PyObject, dis module, bytecode, frame objects, code objects, peephole optimizer | `dis.dis()` output on real function |
| 02 | [Custom Import System](labs/lab-02-custom-import-system.md) | MetaPathFinder, PathEntryFinder, custom Loader, sys.meta_path, import hooks, pkgutil | Custom importer loading synthetic module |
| 03 | [Descriptor Protocol](labs/lab-03-descriptor-protocol.md) | `__get__/__set__/__delete__`, data vs non-data, property internals, `__set_name__`, slots, validation | Typed descriptor with validation |
| 04 | [Memory Allocator & GC](labs/lab-04-memory-allocator.md) | pymalloc arenas/pools/blocks, getsizeof, tracemalloc, gc module, weakref caches | tracemalloc top-5 allocators snapshot |
| 05 | [C Extensions (ctypes)](labs/lab-05-c-extension-ctypes.md) | CDLL, POINTER, Structure, Union, cast, libc qsort/malloc/free, CFUNCTYPE | ctypes calling libc qsort |
| 06 | [Async Internals](labs/lab-06-async-internals.md) | Event loop, selectors, Future.__await__, Task scheduling, call_soon, async generators, contextvars | ContextVar request-scoped state demo |
| 07 | [Advanced Metaclasses](labs/lab-07-metaclass-advanced.md) | `__prepare__`, metaclass __new__/__init__/__call__, conflict resolution, __init_subclass__, singleton, ORM registry | ORM-like metaclass field tracking |
| 08 | [GIL-Free Concurrency](labs/lab-08-gil-free-concurrency.md) | GIL impact, multiprocessing.Pool, ProcessPoolExecutor, shared memory, mmap IPC, as_completed | GIL vs multiprocessing speedup benchmark |
| 09 | [JIT & Caching Patterns](labs/lab-09-jit-caching-patterns.md) | lru_cache internals, cache_info/clear, __wrapped__, TTL decorator, disk cache, numpy caching | lru_cache hits/misses + TTL expiry |
| 10 | [Protocol & Typing](labs/lab-10-protocol-typing.md) | typing.Protocol, runtime_checkable, Protocol.__call__, ParamSpec, TypeVarTuple, Concatenate, overload | mypy-compatible Protocol + isinstance |
| 11 | [Distributed Task Queue](labs/lab-11-distributed-task-queue.md) | Redis-backed queue, task serialization, worker pool, exponential backoff, dead letter queue, result TTL | In-memory queue demo + Redis pattern |
| 12 | [Observability Platform](labs/lab-12-observability-platform.md) | OpenTelemetry TracerProvider, SpanKind, attributes, baggage; Prometheus Counter/Histogram/Gauge; structlog | Real span capture + Prometheus metrics |
| 13 | [Plugin Framework](labs/lab-13-plugin-framework.md) | pluggy hookspec/hookimpl, entry points, __init_subclass__ registry, versioning, DI, sandboxing | pluggy hook call chain |
| 14 | [Security Hardening](labs/lab-14-security-hardening.md) | secrets module, hmac.compare_digest, sha3_256/blake2b, cryptography Fernet + RSA + X25519, safe unpickling | Fernet encrypt/decrypt + RSA sign/verify |
| 15 | [Capstone Platform](labs/lab-15-capstone-platform.md) | FastAPI + Pydantic v2 + import hook + descriptors + asyncio + tracemalloc + pluggy + Prometheus + Fernet + pytest | Full platform integration, 8+ tests |

## Available Packages (python:3.11-slim)

| Package | Version |
|---------|---------|
| fastapi | 0.135.1 |
| numpy | 2.4.2 |
| pandas | 3.0.1 |
| pydantic | 2.12.5 |
| pytest | 9.0.2 |
| requests | 2.32.5 |
| uvicorn | 0.41.0 |
| rich | latest |
| anyio | latest |
| click | latest |

Additional via `pip install`:
- `pluggy` — Plugin framework
- `cryptography` — Fernet, RSA, ECDH
- `opentelemetry-sdk` — Distributed tracing
- `prometheus-client` — Metrics
- `structlog` — Structured logging
- `redis` — Redis client (Lab 11)

## Learning Path

```
Labs 01-05: CPython Deep Dive
  ├── 01: How Python runs your code
  ├── 02: Python's import machinery
  ├── 03: Attribute access protocol
  ├── 04: Memory management
  └── 05: C interop via ctypes

Labs 06-10: Advanced Python Patterns
  ├── 06: Async/await internals
  ├── 07: Metaclass engineering
  ├── 08: True parallelism
  ├── 09: Caching & memoization
  └── 10: Type system advanced

Labs 11-14: Production Infrastructure
  ├── 11: Distributed task queues
  ├── 12: Observability (traces/metrics/logs)
  ├── 13: Plugin architectures
  └── 14: Security hardening

Lab 15: Capstone
  └── Full production platform
```

## Prerequisites

- Python Intermediate or Advanced track completed
- Familiarity with: classes, decorators, async/await, type hints
- Docker installed for isolation

## Running Any Lab

```bash
# Interactive Docker session
docker run -it --rm python:3.11-slim bash

# Or run a specific snippet
docker run --rm python:3.11-slim bash -c "
  pip install PACKAGES -q 2>/dev/null
  python3 -c 'YOUR_CODE_HERE'
"
```
