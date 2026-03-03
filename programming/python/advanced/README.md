# Python — Advanced Level

> 15 labs covering Python's deepest internals: metaprogramming, AST/bytecode, memory management, profiling, cryptography, advanced async, binary protocols, and building production-grade platforms.

## Labs

| # | Lab | Key Skill |
|---|-----|-----------|
| 01 | [Metaprogramming](labs/lab-01-metaprogramming.md) | `__init_subclass__`, metaclasses, descriptors, `type()` factory |
| 02 | [AST & Bytecode](labs/lab-02-ast-bytecode.md) | `ast.parse`, `NodeTransformer`, `dis`, code generation |
| 03 | [Memory Management](labs/lab-03-memory-management.md) | `tracemalloc`, `__slots__`, weak refs, `memoryview`, GC |
| 04 | [Profiling & Performance](labs/lab-04-profiling-performance.md) | `timeit`, `cProfile`, memoization, numpy vs pure Python |
| 05 | [Advanced Async](labs/lab-05-advanced-async.md) | Semaphore, TaskGroup, retry/backoff, `asyncio.timeout` |
| 06 | [ctypes & Binary](labs/lab-06-ctypes-binary.md) | `struct`, `ctypes.Structure`, `array`, binary file format |
| 07 | [Cryptography & Security](labs/lab-07-cryptography-security.md) | PBKDF2, HMAC, `secrets`, JWT-style tokens, audit log |
| 08 | [Advanced SQLite](labs/lab-08-advanced-sqlite.md) | Window functions, FTS5, recursive CTEs, WAL, partial indexes |
| 09 | [numpy Advanced](labs/lab-09-numpy-advanced.md) | Broadcasting, einsum, fancy indexing, structured arrays |
| 10 | [pandas Advanced](labs/lab-10-pandas-advanced.md) | MultiIndex, time series, `pipe()`, `pd.eval`, memory optimisation |
| 11 | [Advanced Concurrency](labs/lab-11-concurrency-advanced.md) | ProcessPool, Actor pattern, condition variables, hybrid pipelines |
| 12 | [Plugin Architecture](labs/lab-12-plugin-architecture.md) | importlib discovery, hook systems, DI container, versioned plugins |
| 13 | [Serialization & Protocols](labs/lab-13-serialization-protocols.md) | pickle, JSON encoders, versioned formats, `deepcopy`, shelve |
| 14 | [Advanced FastAPI](labs/lab-14-fastapi-advanced.md) | Lifespan, middleware chains, dependency injection, SSE streaming |
| 15 | [Capstone — Production Platform](labs/lab-15-capstone.md) | Metaclass models + SQLite + async + numpy + FastAPI + pytest |

## Prerequisites

- Python Practitioner Labs 01–15 (all)
- Comfort with: async/await, OOP, SQLite, numpy/pandas basics, FastAPI basics

## Run Any Lab

```bash
docker pull zchencow/innozverse-python:latest

# Run any lab's code block:
docker run --rm zchencow/innozverse-python:latest python3 -c "<paste code here>"
```
