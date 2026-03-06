# TypeScript Advanced Labs

**Level:** Advanced | **Labs:** 15 | **Prerequisites:** [TypeScript Practitioner](../practitioner/README.md)

Master TypeScript at the expert level — type-level metaprogramming, compiler internals, functional programming, dependency injection, security patterns, and enterprise architecture.

---

## Lab Index

| # | Lab | Topic | Key Skills |
|---|-----|-------|------------|
| 01 | [Type-Level Programming](labs/lab-01-type-level-programming.md) | Type metaprogramming | Conditional types, `infer`, template literal types, recursive types |
| 02 | [Template Literal Types](labs/lab-02-template-literal-types.md) | String type manipulation | Template literal types, `Capitalize`, `Uppercase`, string unions |
| 03 | [Conditional & Mapped Types](labs/lab-03-conditional-mapped-types.md) | Advanced type utilities | `DeepPartial`, `DeepReadonly`, `Flatten`, `UnionToIntersection`, `OmitNever` |
| 04 | [TypeScript Compiler API](labs/lab-04-typescript-compiler-api.md) | AST & compiler access | `ts.createProgram`, `SyntaxKind`, `forEachChild`, ts-morph |
| 05 | [Build Performance](labs/lab-05-performance-optimization.md) | Compilation speed | Project references, `composite`, `incremental`, `skipLibCheck`, diagnostics |
| 06 | [Monorepo TypeScript](labs/lab-06-monorepo-typescript.md) | Monorepo setup | npm workspaces, `tsc --build`, declaration maps, path aliases |
| 07 | [Advanced Zod Validation](labs/lab-07-runtime-validation-advanced.md) | Runtime types | `discriminatedUnion`, `z.lazy`, `z.brand`, `transform`, error flattening |
| 08 | [Dependency Injection](labs/lab-08-dependency-injection.md) | DI with tsyringe | `@injectable`, `@inject`, `@singleton`, interface tokens, mock containers |
| 09 | [Functional Programming](labs/lab-09-fp-typescript.md) | FP with fp-ts | `Option`, `Either`, `pipe`, `flow`, `TaskEither` for async |
| 10 | [GraphQL + TypeScript](labs/lab-10-graphql-typescript.md) | Type-safe GraphQL | type-graphql decorators, `@ObjectType`, `@Resolver`, custom scalars |
| 11 | [Advanced Error Handling](labs/lab-11-advanced-error-handling.md) | Typed errors | `assertNever`, Result monad, error unions, neverthrow library |
| 12 | [Declaration Files](labs/lab-12-declaration-files.md) | .d.ts authoring | `declare module`, global augmentation, overloads, namespace merging |
| 13 | [Branded Types & Security](labs/lab-13-branded-types-security.md) | Nominal typing | SQL injection prevention, `Secret<T>`, URL branding, validated types |
| 14 | [Drizzle ORM](labs/lab-14-drizzle-orm-typesafe.md) | Type-safe SQL | SQLite schema, `$inferSelect`, CRUD, relations, drizzle-kit |
| 15 | [Capstone: Enterprise Platform](labs/lab-15-capstone-enterprise-ts.md) | Full integration | Drizzle + Zod + fp-ts + tsyringe + Vitest, strict types end-to-end |

---

## Learning Path

```
Lab 01-03: Type system mastery
    ↓
Lab 04-06: Tooling & monorepos
    ↓
Lab 07-09: Validation, DI & FP
    ↓
Lab 10-12: Framework integration
    ↓
Lab 13-14: Security & database
    ↓
Lab 15: Enterprise capstone
```

## Prerequisites

Before starting this track:
- Complete [TypeScript Practitioner](../practitioner/README.md) (labs 01-15)
- Comfortable with generics, decorators, async/await
- Understanding of npm packages and module systems

## Docker Verification

All labs include Docker-verified code examples:
```bash
docker run -it --rm node:20-alpine sh
```

Each lab's code is tested and confirmed working in a clean Docker environment.
