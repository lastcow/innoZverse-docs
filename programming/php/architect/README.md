# PHP Architect Track

**Level:** Architect | **Docker:** `php:8.3-cli` | **All labs Docker-verified**

This track covers advanced PHP internals, concurrency, security, distributed systems patterns, and production platform engineering. Every lab includes Docker-verified code examples with real output.

---

## Prerequisites

- PHP 8.1+ concepts (match, enums, fibers, attributes)
- Familiarity with design patterns (DDD, SOLID)
- Basic SQL and SQLite knowledge
- Docker installed locally

## Quick Start

```bash
# Start Docker environment
docker run -it --rm php:8.3-cli bash

# Verify environment
php -v
php -m | grep -E 'OPcache|sodium|PDO'
```

---

## Lab Index

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 01 | [PHP Internals & Zend Engine](labs/lab-01-php-internals.md) | OPcache, zval, CoW, tokenizer | 60 min |
| 02 | [JIT Compiler](labs/lab-02-jit-compiler.md) | PHP 8 JIT modes, benchmarks, opcache.jit=1255 | 60 min |
| 03 | [Fiber Internals](labs/lab-03-fiber-internals.md) | Fibers, cooperative scheduler, async simulation | 60 min |
| 04 | [FFI C Bindings](labs/lab-04-ffi-c-bindings.md) | FFI::cdef(), libc, structs, pointers, callbacks | 60 min |
| 05 | [Custom Stream Wrappers](labs/lab-05-custom-stream-wrappers.md) | stream_wrapper_register, SQLite-backed db:// | 60 min |
| 06 | [SPL Advanced](labs/lab-06-spl-advanced.md) | SplFixedArray, heaps, priority queues, iterators | 60 min |
| 07 | [Reflection & Code Generation](labs/lab-07-reflection-codegen.md) | ReflectionClass, Attributes, DI container, proxies | 60 min |
| 08 | [Advanced Security](labs/lab-08-security-advanced.md) | libsodium: XSalsa20, Ed25519, Argon2id, BLAKE2b | 60 min |
| 09 | [Async with Amp v3](labs/lab-09-async-amphp.md) | Future, async(), delay(), cancellation | 60 min |
| 10 | [Event Sourcing](labs/lab-10-event-sourcing.md) | EventStore, aggregates, projections, snapshots | 60 min |
| 11 | [Distributed Patterns](labs/lab-11-distributed-patterns.md) | Circuit breaker, retry, rate limiter, bulkhead | 60 min |
| 12 | [gRPC PHP](labs/lab-12-grpc-php.md) | Proto3 messages, client stub, metadata, interceptors | 60 min |
| 13 | [Observability](labs/lab-13-observability.md) | OpenTelemetry, spans, metrics, Monolog JSON | 60 min |
| 14 | [Performance Profiling](labs/lab-14-performance-profiling.md) | OPcache tuning, benchmarks, memory profiling | 60 min |
| 15 | [Capstone Platform](labs/lab-15-capstone-platform.md) | Full integration + PHPUnit 10 (7 tests) | 90 min |

**Total: ~870 minutes (~14.5 hours)**

---

## Learning Path

```
Week 1: Internals & Runtime
  Lab 01 → PHP Internals (zval, CoW, tokenizer)
  Lab 02 → JIT Compiler (benchmarks, modes)
  Lab 14 → Performance Profiling (OPcache, memory)

Week 2: Concurrency & Systems Programming
  Lab 03 → Fibers (cooperative scheduling)
  Lab 04 → FFI (C bindings, libc)
  Lab 05 → Stream Wrappers (custom protocols)
  Lab 09 → Async with Amp v3

Week 3: Data Structures & Metaprogramming
  Lab 06 → SPL (heaps, iterators, memory-efficient structs)
  Lab 07 → Reflection (DI container, code generation)

Week 4: Security & Distributed Systems
  Lab 08 → libsodium (Ed25519, Argon2id, XSalsa20)
  Lab 10 → Event Sourcing (CQRS, EventStore, projections)
  Lab 11 → Distributed Patterns (circuit breaker, rate limiter)

Week 5: Platform Engineering
  Lab 12 → gRPC (proto3, interceptors, metadata)
  Lab 13 → Observability (OpenTelemetry, Prometheus, Monolog)
  Lab 15 → Capstone (production platform, PHPUnit 10)
```

---

## Key Skills Developed

### PHP Runtime Mastery
- Zend Engine internals: zval types, copy-on-write memory model
- OPcache configuration for production (validate_timestamps, preloading)
- JIT compiler modes (function JIT 1255, tracing JIT 1205) and when to use each
- Performance profiling with `hrtime()`, memory_get_usage(), custom benchmarking

### Systems Programming
- PHP FFI: calling C libraries (libc), struct manipulation, memory management
- Custom stream wrappers: transparent protocol implementation
- Fiber-based cooperative multitasking without external frameworks

### Concurrency & Async
- PHP 8.1 Fibers: lifecycle, scheduling, error propagation
- Amp v3: `Future`, `async()`, `delay()`, cancellation tokens
- Cooperative scheduler implementation from scratch

### Security Engineering
- libsodium: authenticated encryption (XSalsa20-Poly1305), digital signatures (Ed25519)
- Key derivation: Argon2id with INTERACTIVE/SENSITIVE parameters
- Secure token systems: Ed25519-signed, encrypted JWT-style tokens
- Constant-time comparison, memory zeroing with sodium_memzero

### Distributed Systems
- Event Sourcing: append-only event store, aggregate reconstitution, projections, snapshots
- Circuit breaker: Closed/Open/HalfOpen state machine with configurable thresholds
- Retry with exponential backoff and full jitter
- Token bucket rate limiter, bulkhead pattern, distributed locking

### Platform Engineering
- OpenTelemetry: TracerProvider, span hierarchies, W3C context propagation
- gRPC: proto3 message design, client stubs, interceptor chains, status codes
- Reflection-based DI container with constructor autowiring
- PHPUnit 10 testing: unit tests for all platform components

---

## Docker Reference

```bash
# Basic PHP execution
docker run --rm php:8.3-cli php -r "echo PHP_VERSION;"

# Multi-line script
docker run --rm php:8.3-cli bash -c "cat > /tmp/script.php << 'EOF'
<?php echo 'Hello';
EOF
php /tmp/script.php"

# With Composer packages
docker run --rm php:8.3-cli bash -c "
  apt-get update -qq && apt-get install -y -q curl unzip
  curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
  mkdir /app && cd /app
  composer require amphp/amp:^3.0 --no-interaction -q
  php script.php
"

# With OPcache enabled (CLI)
docker run --rm php:8.3-cli php \
  -d opcache.enable_cli=1 \
  -d opcache.jit_buffer_size=128M \
  -d opcache.jit=1255 \
  script.php

# Run PHPUnit tests
docker run --rm php:8.3-cli bash -c "
  cd /app && ./vendor/bin/phpunit tests/ --no-configuration
"
```

---

## Extension Availability in `php:8.3-cli`

| Extension | Available | Notes |
|-----------|-----------|-------|
| OPcache | ✓ | `php -d opcache.enable_cli=1` |
| sodium | ✓ | Built-in since PHP 7.2 |
| PDO + pdo_sqlite | ✓ | SQLite available |
| Fibers | ✓ | PHP 8.1+ core |
| FFI | ✗ | Needs `--with-ffi` compile flag; use `php:8.3-fpm` |
| grpc | ✗ | Install via pecl |
| xhprof | ✗ | Install via pecl |

---

## References

- [PHP Internals Book](https://www.phpinternalsbook.com/)
- [OpenTelemetry PHP](https://opentelemetry.io/docs/languages/php/)
- [Amp v3 Documentation](https://amphp.org/)
- [libsodium PHP Manual](https://www.php.net/manual/en/book.sodium.php)
- [PHP FFI Manual](https://www.php.net/manual/en/book.ffi.php)
- [PHPUnit 10 Docs](https://docs.phpunit.de/en/10.0/)
