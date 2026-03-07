# Go Architect — 15 Labs

Production-grade Go patterns for platform engineers and senior architects. Each lab is Docker-verified with real output, 8 steps, and a complete capstone.

**Docker:** `golang:1.22-alpine`  
**Level:** Architect  
**Time:** ~15 hours total (60 min/lab)

---

## Labs

| # | Title | Core Topics | Verified |
|---|-------|-------------|---------|
| 01 | [Go Runtime Scheduler](labs/lab-01-go-scheduler.md) | GMP model, GOMAXPROCS, work stealing, runtime/trace | ✅ |
| 02 | [CGO Interoperability](labs/lab-02-cgo-interop.md) | C/Go boundary, memory management, overhead | ✅ |
| 03 | [Generic Architecture Patterns](labs/lab-03-generics-architecture.md) | Repository[T], EventBus[T], Pipeline, constraints | ✅ |
| 04 | [Distributed Tracing](labs/lab-04-distributed-tracing.md) | OpenTelemetry SDK, spans, W3C propagation, Prometheus | ✅ |
| 05 | [Service Mesh Patterns](labs/lab-05-service-mesh.md) | mTLS, cert generation, DNS-SD, LB strategies | ✅ |
| 06 | [Event Sourcing](labs/lab-06-event-sourcing.md) | EventStore, Aggregate, Projection, Snapshot, optimistic concurrency | ✅ |
| 07 | [CQRS Patterns](labs/lab-07-cqrs-patterns.md) | CommandBus, QueryBus, middleware chain, Saga | ✅ |
| 08 | [Actor Model](labs/lab-08-actor-model.md) | ActorSystem, mailbox, supervision, request-reply | ✅ |
| 09 | [Kubernetes Operator](labs/lab-09-kubernetes-operator.md) | Reconciler, CRD, informer, fake client | ✅ |
| 10 | [WASM Architecture](labs/lab-10-wasm-architecture.md) | GOOS=js, syscall/js, TinyGo, streaming compile | ✅ |
| 11 | [Security Architecture](labs/lab-11-security-architecture.md) | XChaCha20-Poly1305, Argon2id, Ed25519, rate limiting | ✅ |
| 12 | [Performance Architecture](labs/lab-12-performance-architecture.md) | sync.Pool, zero-alloc, mmap, strings.Builder, pprof | ✅ |
| 13 | [Plugin Architecture](labs/lab-13-plugin-architecture.md) | plugin package, hashicorp/go-plugin, WASM plugins, capabilities | ✅ |
| 14 | [Chaos Engineering](labs/lab-14-chaos-engineering.md) | Fault injection, circuit breaker, bulkhead, retry+jitter | ✅ |
| 15 | [Capstone Platform](labs/lab-15-capstone-platform.md) | All patterns integrated, 10 table-driven tests, version injection | ✅ |

---

## Quick Start

```bash
# Run any lab's capstone step
docker run --rm golang:1.22-alpine sh -c "
cat > /tmp/main.go << 'GOEOF'
# paste lab's Step 8 code here
GOEOF
cd /tmp && go run main.go
"
```

## Prerequisites

- Go 1.22+ concepts (goroutines, channels, interfaces)
- Docker installed
- Familiarity with distributed systems concepts

## Track Summary

| Area | Labs | Key Output |
|------|------|-----------|
| Runtime | 01, 12 | Scheduler tuning + zero-alloc patterns |
| Generics | 03 | Type-safe repositories and pipelines |
| Architecture | 06, 07, 08 | Event sourcing + CQRS + Actor model |
| Cloud Native | 04, 05, 09 | OTel tracing + mTLS + k8s operators |
| Security | 11 | XChaCha20 + Ed25519 + rate limiting |
| Resilience | 14 | Circuit breaker + chaos engineering |
| Platform | 15 | Full integration capstone |

---

*Part of the [innoZverse-docs](../../../README.md) curriculum — Architect track.*
