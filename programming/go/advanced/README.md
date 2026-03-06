# Go Advanced Labs

**Level:** Advanced | **15 Labs** | **Docker:** `golang:1.22-alpine`

Master production-grade Go engineering: memory model, profiling, reflection, generics, distributed patterns, gRPC, Redis, TLS, WebAssembly, and a full capstone microservice.

---

## Lab Index

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 01 | [Memory Model & Escape Analysis](labs/lab-01-memory-model-escape-analysis.md) | happens-before, stack vs heap, `go build -gcflags="-m"`, sync/atomic, CAS, lock-free stack | 45 min |
| 02 | [Profiling with pprof](labs/lab-02-profiling-pprof.md) | CPU/heap/goroutine profiles, `net/http/pprof`, `go tool pprof`, benchmark + cpuprofile | 45 min |
| 03 | [unsafe & reflect](labs/lab-03-unsafe-reflect.md) | reflect.TypeOf/ValueOf, struct tags, MethodByName, MakeFunc, unsafe.Pointer, zero-copy []byte↔string | 45 min |
| 04 | [sync.Pool & Allocators](labs/lab-04-sync-pool-allocator.md) | sync.Pool, bytes.Buffer pooling, `-benchmem`, allocs/op, arena allocator concept | 45 min |
| 05 | [gRPC Service](labs/lab-05-grpc-service.md) | proto3, protoc-gen-go, unary + streaming RPC, interceptors, metadata, status codes | 45 min |
| 06 | [Distributed Patterns](labs/lab-06-distributed-patterns.md) | Circuit breaker (gobreaker), retry + jitter, token bucket (x/time/rate), bulkhead, health checks | 45 min |
| 07 | [Kafka with kafka-go](labs/lab-07-kafka-go.md) | Writer/Reader, consumer groups, key-based routing, at-least-once, EOS concept | 45 min |
| 08 | [Redis with go-redis/v9](labs/lab-08-redis-go.md) | String/Hash/ZSet/Pipeline/TxPipeline/Pub-Sub/Streams, live Redis verified | 45 min |
| 09 | [Hexagonal Microservice](labs/lab-09-microservice-hexagonal.md) | Ports & adapters, domain layer, slog, health/ready endpoints, graceful shutdown | 45 min |
| 10 | [Advanced Generics](labs/lab-10-generics-advanced.md) | Union constraints, `~T`, Stack/Queue/Set/OrderedMap, Map/Filter/Reduce/GroupBy, `cmp.Ordered` | 45 min |
| 11 | [Go to WebAssembly](labs/lab-11-wasm-go.md) | GOOS=js GOARCH=wasm, syscall/js DOM, JS↔Go calls, 2.1MB binary verified | 45 min |
| 12 | [Plugin System](labs/lab-12-plugin-system.md) | `-buildmode=plugin`, plugin.Open/Lookup, interface contracts, hashicorp/go-plugin RPC | 45 min |
| 13 | [TLS & Cryptography](labs/lab-13-tls-crypto.md) | ECDSA keygen, self-signed certs, mTLS, AES-256-GCM, HMAC-SHA256, bcrypt | 45 min |
| 14 | [Performance Tuning](labs/lab-14-performance-tuning.md) | GOGC, GOMEMLIMIT, GOMAXPROCS, goroutine stacks, net.Buffers, TCP_NODELAY, -benchmem | 45 min |
| 15 | [Capstone: Distributed Service](labs/lab-15-capstone-distributed-service.md) | SQLite (modernc), Redis cache, circuit breaker, slog, graceful shutdown, table tests | 45 min |

---

## Prerequisites

- Go 1.22+
- Docker (for isolated environments)
- Familiarity with Go goroutines, channels, and interfaces

## Quick Start

```bash
# Pull the Go 1.22 Alpine image
docker pull golang:1.22-alpine

# Start a lab container
docker run -it --rm golang:1.22-alpine sh

# For labs requiring Redis (Lab 08, Lab 15)
docker run -d --name redis-lab -p 6379:6379 redis:7-alpine

# For Lab 15 capstone (with Redis)
docker run -it --rm --network=host golang:1.22-alpine sh
```

## Learning Path

```
Labs 01-04  → Runtime internals (memory, profiling, reflection, pooling)
Labs 05-07  → Distributed infrastructure (gRPC, Kafka)
Labs 08-09  → Storage & architecture (Redis, hexagonal)
Lab  10     → Language features (generics)
Labs 11-12  → Platform targets (WASM, plugins)
Lab  13     → Security (TLS, crypto)
Lab  14     → Performance (tuning, benchmarking)
Lab  15     → Capstone (everything wired together)
```

## Key Libraries Used

| Library | Version | Purpose |
|---------|---------|---------|
| `github.com/sony/gobreaker` | v0.5.0 | Circuit breaker |
| `golang.org/x/time/rate` | v0.9.0 | Token bucket rate limiter |
| `github.com/redis/go-redis/v9` | v9.x | Redis client |
| `github.com/segmentio/kafka-go` | v0.4.47 | Kafka producer/consumer |
| `google.golang.org/grpc` | v1.62.0 | gRPC framework |
| `modernc.org/sqlite` | v1.33.1 | Pure Go SQLite (no CGO) |
| `log/slog` | stdlib Go 1.21 | Structured logging |

---

*Docker-verified with `golang:1.22-alpine`. All output captured from real runs.*
