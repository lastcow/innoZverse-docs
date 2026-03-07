# TypeScript Architect Track

**15 Labs | 60 min each | Docker-verified**

Master enterprise TypeScript engineering: type system limits, compiler APIs, monorepo architecture, runtime safety, functional programming, Effect-TS, type-safe databases, GraphQL, testing, observability, and AI integration.

---

## Labs

| # | Lab | Key Skills |
|---|-----|-----------|
| 01 | [Type System Limits](labs/lab-01-type-system-limits.md) | Recursive types, `satisfies`, `const T`, `NoInfer` |
| 02 | [Compiler Plugin](labs/lab-02-compiler-plugin.md) | ts.TransformerFactory, ts-morph, ts-patch |
| 03 | [Monorepo Architecture](labs/lab-03-monorepo-architecture.md) | Project references, composite, Turborepo |
| 04 | [Runtime Safety](labs/lab-04-runtime-safety.md) | Zod, OpenAPI generation, t3-env |
| 05 | [FP Architecture](labs/lab-05-fp-architecture.md) | fp-ts, TaskEither, Reader monad, pipe |
| 06 | [Effect System](labs/lab-06-effect-system.md) | Effect-TS, Layer, Scope, typed errors |
| 07 | [Type-Safe ORM](labs/lab-07-type-safe-orm.md) | Drizzle ORM, Kysely, branded SQL types |
| 08 | [GraphQL Architecture](labs/lab-08-graphql-architecture.md) | Pothos, DataLoader, GraphQL Yoga |
| 09 | [Performance Types](labs/lab-09-performance-types.md) | tsc diagnostics, slow patterns, satisfies |
| 10 | [Module Federation](labs/lab-10-module-federation-ts.md) | Ambient declarations, verbatimModuleSyntax |
| 11 | [Testing Architecture](labs/lab-11-testing-architecture.md) | Vitest, expectTypeOf, MSW, fast-check |
| 12 | [Security Types](labs/lab-12-security-types.md) | Branded types, Opaque, Secret<T>, permissions |
| 13 | [Observability](labs/lab-13-observability-ts.md) | OpenTelemetry, pino, AsyncLocalStorage |
| 14 | [AI Integration](labs/lab-14-ai-integration-ts.md) | Vercel AI SDK, generateObject, tool types |
| 15 | [Capstone: Platform](labs/lab-15-capstone-platform.md) | Full integration, all techniques |

---

## Prerequisites

- TypeScript Intermediate + Advanced tracks complete
- Node.js 20+ and Docker installed
- Comfort with generics and conditional types

## Docker Images Used

- `node:20-alpine` — all labs

## Key Outcomes

After completing this track you can:
- Architect type-safe monorepos with project references and Turborepo
- Build TypeScript compiler transforms with ts-morph
- Design runtime-safe systems with Zod as single source of truth
- Apply functional programming patterns with fp-ts and Effect-TS
- Build type-safe GraphQL APIs with Pothos and DataLoader
- Prevent security bugs using branded types and opaque types
- Instrument applications with typed OpenTelemetry spans
- Integrate AI models with fully typed structured outputs
- Write property-based tests and type-level tests with Vitest
