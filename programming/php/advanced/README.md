# PHP Advanced — 15 Labs

> **Level:** Advanced | **PHP:** 8.1–8.3 | **Docker-Verified**

This series covers PHP's most powerful modern features: Fibers, enums, generators, SPL data structures, the Reflection API, PHP Attributes, streams, OPcache/JIT, security hardening, Composer, testing, event-driven architecture, PSR-7/15 APIs, and a complete microservice capstone.

Each lab uses **Docker** (`php:8.3-cli`) for verification — no local PHP install required.

---

## Lab Index

| # | Lab | Topics | Time |
|---|-----|--------|------|
| 01 | [Fibers & Async](labs/lab-01-fibers-async.md) | `new Fiber()`, `start()`/`resume()`/`suspend()`, cooperative multitasking, coroutine scheduler | 40 min |
| 02 | [Readonly & Enums](labs/lab-02-readonly-enums.md) | `readonly` properties/classes, pure/backed enums, `from()`/`tryFrom()`, `cases()`, enum in `match` | 40 min |
| 03 | [Named Args & Types](labs/lab-03-named-args-intersection-types.md) | Named arguments, intersection types (`A&B`), DNF types, `never`, first-class callables, string-key spread | 40 min |
| 04 | [Advanced Generators](labs/lab-04-generators-advanced.md) | `yield from`, `send()`, `getReturn()`, bidirectional generators, lazy pipelines, memory benchmarks | 40 min |
| 05 | [SPL Data Structures](labs/lab-05-spl-data-structures.md) | `SplStack`/`SplQueue`/`SplPriorityQueue`/`SplFixedArray`/`SplMinHeap`/`SplObjectStorage`, benchmarks | 40 min |
| 06 | [Reflection API](labs/lab-06-reflection-api.md) | `ReflectionClass`/`ReflectionMethod`/`ReflectionProperty`, dynamic proxy, DI container | 40 min |
| 07 | [PHP Attributes](labs/lab-07-php-attributes.md) | `#[Attribute]` declaration, built-in attrs, custom Route/Validate attributes, attribute reading | 40 min |
| 08 | [Streams & Contexts](labs/lab-08-streams-context.md) | `stream_context_create`, fopen wrappers, stream filters, `zlib`, custom stream wrapper | 40 min |
| 09 | [OPcache & JIT](labs/lab-09-opcache-jit.md) | `opcache_get_status()`, JIT modes (1205/1255), preloading, benchmarks with/without JIT | 40 min |
| 10 | [Security Hardening](labs/lab-10-security-hardening.md) | Argon2id, CSRF tokens, `hash_hmac`/`hash_equals`, session hardening, CSP headers, PDO safety | 40 min |
| 11 | [Advanced Composer](labs/lab-11-composer-advanced.md) | Path repositories, custom scripts, classmap autoload, platform requirements, `composer audit` | 40 min |
| 12 | [PHPUnit 11 Testing](labs/lab-12-testing-phpunit.md) | `#[DataProvider]`, `createMock`/`createStub`, test doubles, SQLite integration tests | 40 min |
| 13 | [Event-Driven PHP](labs/lab-13-event-driven-php.md) | PSR-14 dispatcher, stoppable events, subscribers, async queue, Symfony Messenger concepts | 40 min |
| 14 | [API Design with PSR](labs/lab-14-api-design-psr.md) | PSR-7/15/17/18, middleware pipeline, API versioning, OpenAPI attributes, REST handler | 40 min |
| 15 | [Capstone Microservice](labs/lab-15-capstone-microservice.md) | Slim 4, JWT auth, SQLite PDO, PSR-14 events, PHPUnit, full Docker verification | 40 min |

**Total estimated time:** ~10 hours

---

## Quick Start

```bash
# Verify PHP 8.3 is available
docker run --rm php:8.3-cli php --version

# Run any lab example inline
docker run --rm php:8.3-cli php -r "
\$fiber = new Fiber(fn() => Fiber::suspend('hello'));
echo \$fiber->start(); // hello
"

# Interactive PHP 8.3 shell
docker run -it --rm php:8.3-cli bash
```

---

## Learning Path

```
Fibers (01) ──────────────────────────────► Async patterns
Readonly + Enums (02) ────────────────────► Immutable value objects
Named Args + Types (03) ──────────────────► Modern PHP syntax
Generators (04) ──────────────────────────► Memory-efficient data
SPL (05) ─────────────────────────────────► Right data structure
        │
        ▼
Reflection (06) + Attributes (07) ────────► Framework internals
Streams (08) ─────────────────────────────► I/O programming
OPcache/JIT (09) ─────────────────────────► Performance tuning
Security (10) ────────────────────────────► Production hardening
        │
        ▼
Composer (11) + Testing (12) ─────────────► Professional workflow
Events (13) + PSR APIs (14) ──────────────► Architecture patterns
        │
        ▼
Capstone Microservice (15) ───────────────► Everything together
```

---

## Prerequisites

- Completed PHP Intermediate series (or equivalent experience)
- Familiarity with OOP: classes, interfaces, traits, abstract classes
- Basic composer usage (`require`, `install`)
- Docker installed for lab verification

---

## Docker Commands Reference

```bash
# Run inline snippet
docker run --rm php:8.3-cli php -r "echo PHP_VERSION;"

# Run a file
docker run --rm -v $(pwd):/app php:8.3-cli php /app/script.php

# Interactive bash session
docker run -it --rm php:8.3-cli bash

# With Composer
docker run --rm -v $(pwd):/app composer:2 composer install

# Check extensions
docker run --rm php:8.3-cli php -m
```
