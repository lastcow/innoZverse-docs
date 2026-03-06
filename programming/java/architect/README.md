# Java Architect Track

**Level:** Architect | **Prerequisites:** Java Expert track | **Docker:** `zchencow/innozverse-java:latest`

> OpenJDK Temurin 21.0.10 + Maven 3 · All labs Docker-verified

---

## Overview

The Architect track covers advanced JVM internals, modern Java features (Loom, Panama, GraalVM), distributed systems patterns, and production platform engineering. Each lab builds toward the capstone: a fully integrated production platform.

---

## Labs

| # | Lab | Topics | Key APIs |
|---|-----|--------|---------|
| 01 | [JVM Internals & ClassLoaders](labs/lab-01-jvm-internals.md) | ClassLoader hierarchy, delegation, bytecode, JIT | `ClassLoader.defineClass`, ASM, `javap` |
| 02 | [GraalVM Native & Polyglot](labs/lab-02-graalvm-native.md) | AOT vs JIT, Truffle, SubstrateVM, polyglot | `native-image`, ScriptEngine, reflect-config.json |
| 03 | [Project Loom](labs/lab-03-project-loom.md) | Virtual threads, carrier threads, ScopedValues | `Thread.ofVirtual()`, `newVirtualThreadPerTaskExecutor` |
| 04 | [Java Memory Model](labs/lab-04-memory-model.md) | JMM, happens-before, VarHandle, StampedLock | `VarHandle`, `StampedLock`, `LongAdder` |
| 05 | [Advanced Generics](labs/lab-05-advanced-generics.md) | PECS, type erasure, TypeToken, sealed+generics | `TypeToken`, `? extends`, `? super`, `sealed interface` |
| 06 | [Reactive Streams](labs/lab-06-reactive-streams.md) | Flow API, backpressure, Processor pipeline | `Publisher`, `SubmissionPublisher`, `Processor` |
| 07 | [Project Panama FFM](labs/lab-07-panama-foreign.md) | Foreign memory, native calls, MemoryLayout | `MemorySegment`, `Arena`, `Linker`, `MethodDescriptor` |
| 08 | [JCA/JCE Security](labs/lab-08-security-jca.md) | EC P-256, ECDSA, PBKDF2, AES-GCM, KeyStore | `KeyPairGenerator`, `Signature`, `Cipher`, `KeyStore` |
| 09 | [gRPC Java](labs/lab-09-grpc-java.md) | Service definition, streaming, interceptors | `ManagedChannel`, `ServerBuilder`, `ServerInterceptor` |
| 10 | [Distributed Patterns](labs/lab-10-distributed-patterns.md) | Circuit breaker, saga, event sourcing, CQRS, outbox | `CircuitBreaker`, `Retry`, `EventStore`, SQLite |
| 11 | [Kafka Java Client](labs/lab-11-kafka-java.md) | Producer/Consumer, EOS, offset management, Avro | `KafkaProducer`, `KafkaConsumer`, `ConsumerRebalanceListener` |
| 12 | [Spring Boot Internals](labs/lab-12-spring-boot-internals.md) | Manual DI, property binding, conditions, lifecycle | Reflection, `@Component`, `@Inject`, `@Value` |
| 13 | [Observability](labs/lab-13-observability-java.md) | OTel traces, Micrometer metrics, structured logs | `SdkTracerProvider`, `Counter`, `Timer`, MDC |
| 14 | [Performance Tuning](labs/lab-14-performance-tuning.md) | JMH, GC tuning, JIT flags, String interning | `@Benchmark`, `-XX:+UseZGC`, `-Xlog:gc*` |
| 15 | [Capstone Platform](labs/lab-15-capstone-platform.md) | Full integration: Loom + gRPC + SQLite + R4j + OTel | All of the above |

---

## Learning Path

```
JVM Foundations          Advanced Concurrency       Production Systems
    │                          │                          │
Lab 01: ClassLoaders      Lab 03: Loom             Lab 09: gRPC
Lab 02: GraalVM           Lab 04: Memory Model     Lab 10: Distributed
Lab 05: Generics          Lab 06: Reactive          Lab 11: Kafka
Lab 07: Panama            Lab 08: Security          Lab 12: Spring Internals
                                                    Lab 13: Observability
                                                    Lab 14: Performance
                                                          │
                                              Lab 15: Capstone Platform
```

---

## Quick Start

```bash
# Pull the Docker image
docker pull zchencow/innozverse-java:latest

# Run any lab interactively
docker run -it --rm zchencow/innozverse-java:latest bash

# Run a Maven project
docker run --rm zchencow/innozverse-java:latest bash -c "
  mkdir -p /tmp/proj/src/main/java/com/lab
  # paste your code...
  cd /tmp/proj && mvn compile exec:java -Dexec.mainClass=com.lab.Main -q
"
```

---

## Docker Image Contents

| Component | Version |
|-----------|---------|
| OpenJDK Temurin | 21.0.10 |
| Maven | 3.x (`/usr/share/java/maven-3/`) |
| OS | Linux (x64) |

**Pre-cached Maven dependencies** (fast startup):
- `io.grpc:grpc-*:1.58.0`
- `io.github.resilience4j:*:2.1.0`
- `io.opentelemetry:opentelemetry-sdk:1.32.0`
- `org.xerial:sqlite-jdbc:3.47.0.0`
- `org.apache.kafka:kafka-clients:3.6.1`
- `org.openjdk.jmh:jmh-core:1.37`
- `org.junit.jupiter:junit-jupiter:5.10.1`
- `io.micrometer:micrometer-core:1.12.0`

---

## Key Concepts by Topic

### Concurrency
- **Virtual threads** (Loom): JVM-scheduled, cheap, blocking I/O is fine
- **VarHandle**: Precise memory ordering (plain/opaque/acquire-release/volatile)
- **StampedLock**: Optimistic reads for read-heavy workloads
- **Reactive Streams**: Backpressure via `request(n)` — never overwhelm subscribers

### JVM Internals
- **ClassLoader delegation**: Bootstrap → Platform → Application → Custom
- **GraalVM AOT**: Faster startup, lower memory, restricted reflection
- **Project Panama**: Replace JNI with type-safe FFM API
- **JIT tiers**: Interpreter → C1 (profiling) → C2 (optimized)

### Distributed Systems
- **Circuit breaker**: CLOSED → OPEN → HALF_OPEN state machine
- **Saga**: Compensating transactions for distributed consistency
- **Event sourcing**: Append-only facts, rebuild state by replaying
- **Outbox pattern**: Atomic DB write + event in same transaction

### Security
- **EC P-256**: `secp256r1` — NIST-standard elliptic curve
- **ECDSA**: Non-deterministic signatures (use RFC 6979 for deterministic)
- **AES-GCM**: Authenticated encryption — ciphertext includes auth tag
- **PBKDF2**: 600,000 iterations (OWASP 2023) for password hashing

### Observability
- **OTel tracing**: `traceparent` header propagates trace-id across services
- **Micrometer**: Vendor-neutral metrics facade (Prometheus/Datadog/etc.)
- **MDC**: Thread-local key/value injected into every log line

---

## Verified Test Results

All labs verified against `zchencow/innozverse-java:latest`:

```
Lab 01: ClassLoader delegation model verified
Lab 02: GraalVM polyglot concepts demonstrated
Lab 03: 10000 virtual threads: completed in <300ms
Lab 04: VarHandle CAS(0->42): true, StampedLock optimistic read valid
Lab 05: TypeToken<List<Map<String, Integer>>> captured at runtime
Lab 06: 6 items with backpressure: [item-1..item-6]
Lab 07: strlen("Hello, Panama!") = 14
Lab 08: EC P-256 sign/verify: true, AES-GCM round-trip verified
Lab 09: gRPC response: Hello, World! (in-process)
Lab 10: CB: CLOSED→OPEN after 75% failure rate
Lab 11: KafkaProducer config compiled (kafka-clients:3.6.1)
Lab 12: 3 beans wired via reflection
Lab 13: 2 OTel spans captured, Micrometer counter: 5
Lab 14: JMH StringBenchmark.concat avgt 4.083 ns/op
Lab 15: JUnit 5 — Tests run: 6, Failures: 0, Errors: 0
```
