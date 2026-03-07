# Lab 15: Capstone — Enterprise TypeScript Platform

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Build a complete enterprise TypeScript platform integrating all concepts from Labs 01–14: Effect-TS typed effects + DI, Drizzle ORM, Pothos GraphQL, fp-ts pipelines, Zod→OpenAPI, Vitest type tests, branded security types, and OpenTelemetry spans.

---

## Step 1: Platform Architecture

```
platform/
├── src/
│   ├── telemetry/
│   │   └── sdk.ts              # OTel setup
│   ├── db/
│   │   ├── schema.ts           # Drizzle schema + type exports
│   │   └── index.ts            # Database connection
│   ├── domain/
│   │   ├── types.ts            # Domain types + branded types
│   │   ├── schemas.ts          # Zod schemas → OpenAPI
│   │   └── errors.ts           # Tagged error types
│   ├── services/
│   │   ├── UserService.ts      # Effect-TS service with DI
│   │   └── OrderService.ts     # fp-ts ReaderTaskEither
│   ├── graphql/
│   │   ├── builder.ts          # Pothos builder
│   │   └── schema.ts           # Schema definition
│   └── server.ts               # GraphQL Yoga server
└── tests/
    ├── types.test-d.ts         # Type-level tests
    └── services.test.ts        # Vitest + fast-check
```

---

## Step 2: Domain Types + Branded Types

```typescript
// src/domain/types.ts
declare const UserIdBrand:  unique symbol;
declare const OrderIdBrand: unique symbol;

export type UserId  = string & { readonly [UserIdBrand]: typeof UserIdBrand };
export type OrderId = string & { readonly [OrderIdBrand]: typeof OrderIdBrand };

export const UserId  = (id: string): UserId  => id as UserId;
export const OrderId = (id: string): OrderId => id as OrderId;

export class Secret<T> {
  readonly #value: T;
  constructor(value: T) { this.#value = value; }
  expose(): T { return this.#value; }
  toJSON(): string { return '[REDACTED]'; }
  toString(): string { return '[REDACTED]'; }
}
```

---

## Step 3: Zod Schemas → OpenAPI

```typescript
// src/domain/schemas.ts
import { z } from 'zod';

export const CreateUserSchema = z.object({
  name:  z.string().min(1).max(100),
  email: z.string().email(),
  role:  z.enum(['admin', 'user', 'guest']).default('user'),
});

export const UserSchema = CreateUserSchema.extend({
  id:        z.string().uuid(),
  createdAt: z.date(),
});

export type CreateUser = z.infer<typeof CreateUserSchema>;
export type User       = z.infer<typeof UserSchema>;

// Build OpenAPI spec
export function buildOpenApiSpec() {
  return {
    openapi: '3.0.0',
    info: { title: 'Enterprise API', version: '1.0.0' },
    components: {
      schemas: {
        CreateUser: {
          type: 'object',
          properties: {
            name:  { type: 'string', minLength: 1, maxLength: 100 },
            email: { type: 'string', format: 'email' },
            role:  { type: 'string', enum: ['admin', 'user', 'guest'], default: 'user' },
          },
          required: ['name', 'email'],
        },
      },
    },
  };
}
```

---

## Step 4: Effect-TS Service with DI

```typescript
// src/services/UserService.ts
import { Effect, Context, Layer, pipe } from 'effect';
import type { User, CreateUser, UserId } from '../domain/types';

// Service interfaces
interface UserRepository {
  readonly findById: (id: UserId) => Effect.Effect<User, DatabaseError>;
  readonly create:   (data: CreateUser) => Effect.Effect<User, DatabaseError>;
}
const UserRepository = Context.GenericTag<UserRepository>('UserRepository');

// Service implementation
const UserRepositoryLive = Layer.succeed(UserRepository, {
  findById: (id) => Effect.tryPromise({
    try: () => db.select().from(users).where(eq(users.id, id)).then(r => r[0]),
    catch: (e) => new DatabaseError({ message: String(e), query: 'SELECT' }),
  }),
  create: (data) => Effect.tryPromise({
    try: () => db.insert(users).values(data).returning().then(r => r[0]),
    catch: (e) => new DatabaseError({ message: String(e), query: 'INSERT' }),
  }),
});

// Business logic using the service
const createUserProgram = (data: CreateUser) =>
  Effect.gen(function* () {
    const repo = yield* UserRepository;
    const user = yield* repo.create(data);
    yield* Effect.log(`Created user: ${user.id}`);
    return user;
  });

// Run with real dependencies
Effect.runPromise(
  createUserProgram({ name: 'Alice', email: 'alice@example.com', role: 'user' })
    .pipe(Effect.provide(UserRepositoryLive))
);
```

---

## Step 5: fp-ts ReaderTaskEither Pipeline

```typescript
// src/services/OrderService.ts
import * as RTE from 'fp-ts/ReaderTaskEither';
import * as TE from 'fp-ts/TaskEither';
import { pipe } from 'fp-ts/function';

interface OrderDeps {
  db:     Database;
  mailer: Mailer;
  logger: Logger;
}

const createOrder = (data: CreateOrderInput) =>
  pipe(
    RTE.ask<OrderDeps>(),
    RTE.flatMap(deps =>
      RTE.tryCatch(
        () => deps.db.orders.create(data),
        (e) => new DatabaseError({ message: String(e), query: 'INSERT' })
      )
    ),
    RTE.tap(order =>
      RTE.fromTaskEither(
        TE.tryCatch(
          () => deps.mailer.sendOrderConfirmation(order),
          (e) => new EmailError({ message: String(e) })
        )
      )
    )
  );
```

---

## Step 6: Pothos GraphQL Schema

```typescript
// src/graphql/schema.ts
import SchemaBuilder from '@pothos/core';
import { createYoga } from 'graphql-yoga';

const builder = new SchemaBuilder<{
  Objects: { User: User };
  Context: { db: Database };
}>();

builder.objectType('User', {
  fields: (t) => ({
    id:    t.exposeString('id'),
    name:  t.exposeString('name'),
    email: t.exposeString('email'),
    role:  t.exposeString('role'),
  }),
});

builder.queryType({
  fields: (t) => ({
    user: t.field({
      type: 'User', nullable: true,
      args: { id: t.arg.string({ required: true }) },
      resolve: (_, { id }, ctx) => ctx.db.users.findById(id),
    }),
  }),
});
```

---

## Step 7: Vitest Type Tests + Property-Based

```typescript
// tests/types.test-d.ts
import { expectTypeOf } from 'vitest';
import type { UserId, OrderId } from '../src/domain/types';

test('UserId is not assignable to OrderId', () => {
  expectTypeOf<UserId>().not.toMatchTypeOf<OrderId>();
  expectTypeOf<OrderId>().not.toMatchTypeOf<UserId>();
});

// tests/services.test.ts
import fc from 'fast-check';

test('Zod schema validates all valid users', () => {
  fc.assert(fc.property(
    fc.record({
      name:  fc.string({ minLength: 1, maxLength: 100 }),
      email: fc.emailAddress(),
      role:  fc.constantFrom('admin' as const, 'user' as const, 'guest' as const),
    }),
    (data) => CreateUserSchema.safeParse(data).success
  ));
});
```

---

## Step 8: Capstone — Full Integration Verification

```bash
docker run --rm node:20-alpine sh -c "
  mkdir -p /work && cd /work && npm init -y > /dev/null 2>&1
  npm install zod fp-ts effect fast-check @opentelemetry/sdk-trace-base @opentelemetry/api 2>&1 | tail -2

  node -e \"
// 1. Zod schema validation
const {z} = require('zod');
const UserSchema = z.object({ id: z.string().uuid(), name: z.string().min(1), role: z.enum(['admin','user']) });
const u = UserSchema.safeParse({ id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', name: 'Alice', role: 'admin' });
console.log('[1] Zod schema valid:', u.success);

// 2. fp-ts pipeline
const { pipe } = require('fp-ts/function');
const E = require('fp-ts/Either');
const TE = require('fp-ts/TaskEither');
const pipeline = (id) => pipe(
  id > 0 ? E.right(id) : E.left(new Error('Invalid')),
  TE.fromEither,
  TE.flatMap(id => TE.right({ userId: id, name: 'Alice' }))
);
pipeline(42)().then(r => console.log('[2] fp-ts pipeline:', E.isRight(r) ? 'right('+JSON.stringify(r.right)+')' : 'left'));

// 3. Effect-TS
const { Effect } = require('effect');
Effect.runPromise(Effect.gen(function* () {
  const x = yield* Effect.succeed(42);
  const y = yield* Effect.sync(() => x * 2);
  console.log('[3] Effect pipeline:', y);
}));

// 4. OpenTelemetry span
const { BasicTracerProvider, SimpleSpanProcessor, InMemorySpanExporter } = require('@opentelemetry/sdk-trace-base');
const api = require('@opentelemetry/api');
const exp = new InMemorySpanExporter();
const prov = new BasicTracerProvider({ spanProcessors: [new SimpleSpanProcessor(exp)] });
api.trace.setGlobalTracerProvider(prov);
const span = prov.getTracer('platform').startSpan('capstone');
span.setAttribute('test', true);
span.end();
const spans = exp.getFinishedSpans();
console.log('[4] OTel span:', spans[0].name, 'traceId:', spans[0].spanContext().traceId.substring(0,8) + '...');

// 5. Property-based test
const fc = require('fast-check');
fc.assert(fc.property(fc.string(), s => s.split('').reverse().join('').split('').reverse().join('') === s));
console.log('[5] Property test: reverse involution PASS');

console.log('=== Enterprise TypeScript Platform: ALL CHECKS PASSED ===');
  \"
"
```

📸 **Verified Output:**
```
[1] Zod schema valid: true
[2] fp-ts pipeline: right({"userId":42,"name":"Alice"})
[3] Effect pipeline: 84
[4] OTel span: capstone traceId: 3089959a...
[5] Property test: reverse involution PASS
=== Enterprise TypeScript Platform: ALL CHECKS PASSED ===
```

---

## Summary

| Component | Technology | Status |
|-----------|-----------|--------|
| Type system | Branded types + satisfies | ✅ Compile-time safety |
| Compiler | ts-morph AST transforms | ✅ Auto-inject logging |
| Monorepo | npm workspaces + tsc refs | ✅ Incremental builds |
| Runtime safety | Zod → OpenAPI | ✅ Schema-first |
| FP patterns | fp-ts ReaderTaskEither | ✅ Typed DI + errors |
| Effect system | Effect-TS gen + Layer | ✅ Structured effects |
| Database | Drizzle ORM + Kysely | ✅ Type-inferred SQL |
| GraphQL | Pothos + Yoga | ✅ Code-first typed |
| Testing | Vitest + fast-check | ✅ Type + property tests |
| Observability | OpenTelemetry spans | ✅ Typed attributes |
| AI Integration | Vercel AI SDK + Zod | ✅ Structured output |
