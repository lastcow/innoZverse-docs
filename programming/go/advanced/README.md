# Go Advanced Track

**15 hands-on labs** covering production Go engineering: memory internals, profiling, gRPC, distributed systems, generics, WebAssembly, cryptography, and performance tuning — all Docker-verified.

**Prerequisites:** Go fundamentals (goroutines, channels, interfaces), familiarity with `go test` and modules.

**Environment:** Every lab runs in `docker run -it --rm golang:1.22-alpine sh` — no local setup required.

---

## Lab Index

| # | Lab | Key Concepts | Time |
|---|---|---|---|
| 01 | [Memory Model & Escape Analysis](labs/lab-01-memory-model-escape-analysis.md) | stack vs heap, `//go:noinline`, `-gcflags="-m"` | 30 min |
| 02 | [Profiling with pprof](labs/lab-02-profiling-pprof.md) | CPU/memory profiling, flame graphs, `go tool pprof` | 35 min |
| 03 | [unsafe & reflect](labs/lab-03-unsafe-reflect.md) | `unsafe.Pointer`, `reflect.Value`, struct field access | 35 min |
| 04 | [sync.Pool & Custom Allocator](labs/lab-04-sync-pool-allocator.md) | `sync.Pool`, buffer reuse, GC pressure reduction | 30 min |
| 05 | [gRPC Service](labs/lab-05-grpc-service.md) | protobuf, `google.golang.org/grpc`, interceptors | 40 min |
| 06 | [Distributed Patterns](labs/lab-06-distributed-patterns.md) | circuit breaker, retry, graceful shutdown, `os/signal` | 40 min |
| 07 | [Kafka + Go](labs/lab-07-kafka-go.md) | `kafka-go`, producers, consumers, offset management | 40 min |
| 08 | [Redis + Go](labs/lab-08-redis-go.md) | `go-redis/v9`, pipelines, pub/sub, TTL caching | 35 min |
| 09 | [Microservice — Hexagonal Architecture](labs/lab-09-microservice-hexagonal.md) | ports & adapters, dependency inversion, interface mocks | 45 min |
| 10 | [Advanced Generics](labs/lab-10-generics-advanced.md) | type constraints, generic data structures, type inference | 35 min |
| 11 | [WebAssembly with Go](labs/lab-11-wasm-go.md) | `GOOS=js GOARCH=wasm`, `syscall/js`, browser interop | 35 min |
| 12 | [Plugin System](labs/lab-12-plugin-system.md) | `plugin` package, `modernc.org/sqlite` (pure Go), dynamic loading | 40 min |
| 13 | [TLS & Cryptography](labs/lab-13-tls-crypto.md) | `crypto/tls`, mutual TLS, AES-GCM, HMAC, cert generation | 40 min |
| 14 | [Performance Tuning](labs/lab-14-performance-tuning.md) | GOGC, GOMEMLIMIT, GOMAXPROCS, `net.Buffers`, zero-copy I/O | 45 min |
| 15 | [**Capstone — Production Distributed Service**](labs/lab-15-capstone-distributed-service.md) | gRPC + Redis + SQLite + slog + circuit breaker + graceful shutdown + tests | 60 min |

---

## Learning Path

```
Labs 01–04  ──▶  Memory & Runtime internals
Labs 05–08  ──▶  Network services (gRPC, Kafka, Redis)
Labs 09–12  ──▶  Architecture & extensibility
Labs 13–14  ──▶  Security & performance
Lab  15     ──▶  Capstone: production distributed microservice
```

## Quick Start

```bash
# Run any lab in Docker — no local Go install needed
docker run -it --rm golang:1.22-alpine sh

# Inside the container:
mkdir mylab && cd mylab
go mod init mylab
# Follow the lab steps...
```

## Tips

- **Run labs in order** — each builds on previous concepts.
- **Don't skip the verified output** — run it yourself and compare.
- **Experiment** — break things, change values, observe behaviour.
- **Lab 15** is the best capstone project for your portfolio.
