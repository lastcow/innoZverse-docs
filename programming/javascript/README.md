# JavaScript Learning Path

Welcome to the innoZverse JavaScript curriculum — a complete, hands-on journey from absolute basics to production-grade Node.js engineering. Every code example is **Docker-verified** using the `innozverse-js:latest` image (Node.js v20 LTS).

## 🗺️ Learning Tracks

| Track | Labs | Topics |
|-------|------|--------|
| [Foundations](./foundations/README.md) | 15 | Core JS syntax, data structures, functions, OOP basics |
| [Practitioner](./practitioner/README.md) | 15 | Async patterns, Node.js APIs, Express, testing, debugging |
| [Advanced](./advanced/README.md) | 15 | TypeScript, design patterns, performance, security, production ops |

## 🐳 Setup

All labs use Docker for a consistent environment:

```bash
# Pull the image
docker pull innozverse-js:latest

# Verify
docker run --rm innozverse-js:latest node --version
```

## 📋 Prerequisites

- Docker installed and running
- A text editor (VS Code recommended)
- Basic command-line familiarity

## 🚀 Quick Start

```bash
# Run any Node.js snippet
docker run --rm innozverse-js:latest node -e "console.log('Hello, World!')"

# Run a script file
docker run --rm -v $(pwd):/workspace innozverse-js:latest node /workspace/app.js
```

## 📚 Track Descriptions

### Foundations (Labs 1–15)
Master the JavaScript language itself — syntax, types, control flow, functions, closures, classes, and asynchronous basics. No prior JS experience required.

### Practitioner (Labs 1–15)
Apply JavaScript in real Node.js contexts — Promises, async/await, file I/O, HTTP servers, REST APIs, testing, streams, and debugging. Requires Foundations.

### Advanced (Labs 1–15)
Production-grade engineering — TypeScript, design patterns, performance optimization, security hardening, WebSockets, microservices, Docker, CI/CD, and Node.js production best practices. Requires Practitioner.

---

*All code verified with Node.js v20 on `innozverse-js:latest`*
