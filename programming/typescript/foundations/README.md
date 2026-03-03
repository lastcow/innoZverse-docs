# TypeScript Foundations

> Master TypeScript from first principles — types, generics, async, decorators, and a complete CLI capstone.

{% hint style="info" %}
**Prerequisites:** Basic JavaScript (variables, functions, arrays, objects). No TypeScript experience required.
{% endhint %}

---

## Lab Overview

| # | Lab | Key Concepts | Time |
|---|-----|-------------|------|
| 01 | [Hello World & Basics](labs/lab-01-hello-world.md) | Primitive types, inference, tuples, interfaces, `strict` mode | 20 min |
| 02 | [Functions & Type Signatures](labs/lab-02-functions.md) | Typed params, generics, overloads, closures, Result type | 25 min |
| 03 | [Interfaces & Utility Types](labs/lab-03-interfaces-types.md) | `Partial`, `Pick`, `Omit`, `Record`, mapped types, discriminated unions | 30 min |
| 04 | [Classes & OOP](labs/lab-04-classes.md) | Access modifiers, abstract, mixins, generic classes, decorators | 35 min |
| 05 | [Enums & Literal Types](labs/lab-05-enums.md) | String/numeric/const enums, literal unions, state machines | 25 min |
| 06 | [Generics Deep Dive](labs/lab-06-generics.md) | Constraints, `infer`, `Optional<T>`, `Result<T,E>`, TTL cache | 35 min |
| 07 | [Modules & Declarations](labs/lab-07-modules.md) | ES modules, `.d.ts`, module augmentation, barrel files | 25 min |
| 08 | [Error Handling](labs/lab-08-error-handling.md) | Typed errors, Result pattern, `never`, retry, validation | 30 min |
| 09 | [Async TypeScript](labs/lab-09-async.md) | `Promise<T>`, `Awaited<T>`, async generators, timeout/retry | 35 min |
| 10 | [Type Manipulation](labs/lab-10-type-manipulation.md) | `keyof`, `typeof`, indexed access, template literals, `as const` | 30 min |
| 11 | [Decorators & Metadata](labs/lab-11-decorators.md) | Class/method/property decorators, DI container, validation | 35 min |
| 12 | [TypeScript + Node.js](labs/lab-12-nodejs.md) | File I/O, HTTP server, streams, env vars, process types | 35 min |
| 13 | [Testing](labs/lab-13-testing.md) | Node test runner, typed mocks, spies, builders, property tests | 30 min |
| 14 | [Advanced Patterns](labs/lab-14-patterns.md) | Builder, Observer, Command, Strategy, Proxy, state machine | 35 min |
| 15 | [Capstone: CLI Tool](labs/lab-15-capstone.md) | Full `prodctl` CLI: types, store, parser, formatter, tests | 60 min |

**Total estimated time:** ~8 hours

---

{% hint style="success" %}
**Start here:** [Lab 01 — Hello World & TypeScript Basics](labs/lab-01-hello-world.md)
{% endhint %}

---

## Learning Path

**Labs 01–04** lay the foundation: types, functions, interfaces, and classes. These cover ~80% of day-to-day TypeScript.

**Labs 05–08** expand your toolkit: enums, generics, modules, and error handling. You'll write code that rivals production TypeScript.

**Labs 09–12** go deep: async patterns, type manipulation, decorators, and Node.js integration. These power real-world backends.

**Labs 13–15** are about quality: testing, patterns, and the capstone CLI that ties everything together.

---

## Docker Quick Start

```bash
docker pull zchencow/innozverse-ts:latest
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const greet = (name: string): string => \`Hello, \${name}!\`;
console.log(greet('TypeScript'));
"
```
