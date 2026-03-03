# TypeScript

> **JavaScript with superpowers.** TypeScript adds static typing, interfaces, generics, and advanced type inference to JavaScript — catching bugs at compile time, not runtime.

---

<table data-view="cards">
<thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead>
<tbody>
<tr>
<td><strong>🟩 Foundations</strong></td>
<td>Types, functions, classes, generics, async, Node.js</td>
<td><a href="foundations/README.md">foundations/README.md</a></td>
</tr>
<tr>
<td><strong>🟦 Practitioner</strong></td>
<td>Advanced types, React, NestJS, testing at scale</td>
<td><a href="practitioner/README.md">practitioner/README.md</a></td>
</tr>
<tr>
<td><strong>🟧 Advanced</strong></td>
<td>Compiler API, custom transformers, monorepos</td>
<td><a href="advanced/README.md">advanced/README.md</a></td>
</tr>
<tr>
<td><strong>🟥 Expert</strong></td>
<td>Type-level programming, DSLs, performance</td>
<td><a href="expert/README.md">expert/README.md</a></td>
</tr>
</tbody>
</table>

---

## Why TypeScript?

TypeScript is the most popular typed language in web development — used by Angular, Next.js, NestJS, Prisma, Deno, and millions of projects. It compiles to plain JavaScript and adds zero runtime overhead.

| Feature | Benefit |
|---------|---------|
| **Static Types** | Catch bugs before running code |
| **Interfaces & Type Aliases** | Document and enforce data shapes |
| **Generics** | Write reusable, type-safe utilities |
| **Union & Intersection Types** | Precise modeling of real-world data |
| **Literal Types** | Type-safe constants and enums |
| **Template Literal Types** | Generate types from string patterns |
| **Mapped Types** | Transform types programmatically |
| **Conditional Types** | Type-level if/else logic |
| **Decorators** | Metadata-driven frameworks (Angular, NestJS) |
| **`strict` mode** | Eliminate entire classes of runtime errors |

---

## Quick Start

{% tabs %}
{% tab title="Ubuntu/Debian" %}
```bash
# Install Node.js + TypeScript
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
npm install -g typescript ts-node

# Or use Docker (recommended for labs)
docker pull zchencow/innozverse-ts:latest
docker run --rm -it zchencow/innozverse-ts:latest
```
{% endtab %}
{% tab title="macOS" %}
```bash
brew install node
npm install -g typescript ts-node

# Or Docker
docker pull zchencow/innozverse-ts:latest
docker run --rm -it zchencow/innozverse-ts:latest
```
{% endtab %}
{% tab title="Windows" %}
```powershell
# Install Node.js from nodejs.org, then:
npm install -g typescript ts-node

# Or Docker Desktop
docker pull zchencow/innozverse-ts:latest
docker run --rm -it zchencow/innozverse-ts:latest
```
{% endtab %}
{% tab title="Alpine/Docker" %}
```bash
docker pull zchencow/innozverse-ts:latest
docker run --rm -it zchencow/innozverse-ts:latest ts-node --version
# TypeScript 5.x, Node 20, ts-node included
```
{% endtab %}
{% endtabs %}

---

## What You'll Learn

### 🟩 Foundations (Labs 01–15)
Core TypeScript: primitive types, functions, interfaces, type aliases, classes, enums, generics, modules, error handling, async/await, type manipulation, decorators, Node.js integration, testing, and a complete CLI capstone.

### 🟦 Practitioner (Labs 01–15)
Real-world TypeScript: React with full type safety, NestJS REST APIs, TypeORM, GraphQL, authentication, middleware, interceptors, and integration testing.

### 🟧 Advanced (Labs 01–15)
Deep TypeScript: compiler API, custom ESLint rules, Babel plugins, monorepo setup with Nx/Turborepo, performance profiling, and custom type transformers.

### 🟥 Expert (Labs 01–15)
Type-level programming: HKTs, type-safe DSLs, phantom types, branded types, nominal typing, and building TypeScript libraries.

---

{% hint style="info" %}
**Start here:** The [Foundations](foundations/README.md) track assumes basic JavaScript knowledge. Each lab builds on the previous — follow them in order for the best experience.
{% endhint %}

{% hint style="success" %}
**Pro tip:** Use the [TypeScript Playground](https://www.typescriptlang.org/play) to experiment with types interactively while working through labs.
{% endhint %}
