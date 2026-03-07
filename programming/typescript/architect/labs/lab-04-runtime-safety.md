# Lab 04: Runtime Type Safety

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Runtime type safety architecture: Zod as single source of truth (infer TypeScript types + runtime validators), comparison with ArkType/io-ts, generating OpenAPI schemas from Zod, and type-safe environment variables with t3-env.

---

## Step 1: The Problem with TypeScript Types Alone

```typescript
// TypeScript types are ERASED at runtime
// This is perfectly valid TypeScript but unsafe at runtime:

interface User {
  id: string;
  email: string;
  role: 'admin' | 'user';
}

async function getUser(id: string): Promise<User> {
  const response = await fetch(`/api/users/${id}`);
  const data = await response.json();
  return data as User;  // DANGEROUS: no runtime validation
  // If API returns { id: 1, emal: "typo" }, TypeScript is blind to this
}
```

---

## Step 2: Zod — Single Source of Truth

```typescript
import { z } from 'zod';

// Define schema ONCE → TypeScript type + runtime validator
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  age: z.number().int().min(0).max(150).optional(),
  role: z.enum(['admin', 'user', 'guest']),
  createdAt: z.date(),
  preferences: z.object({
    theme: z.enum(['light', 'dark']).default('light'),
    notifications: z.boolean().default(true),
  }).optional(),
});

// Infer TypeScript type — stays in sync with schema automatically
type User = z.infer<typeof UserSchema>;
// Equivalent to:
// type User = {
//   id: string;
//   name: string;
//   email: string;
//   age?: number;
//   role: 'admin' | 'user' | 'guest';
//   createdAt: Date;
//   preferences?: { theme: 'light' | 'dark'; notifications: boolean };
// }

// Runtime validation
const result = UserSchema.safeParse(untrustedData);
if (!result.success) {
  // result.error.issues has typed error details
  console.error('Validation failed:', result.error.issues);
  return null;
}
// result.data is typed as User
console.log(result.data.email.toLowerCase());
```

---

## Step 3: Advanced Zod Patterns

```typescript
// Transform: parse and shape simultaneously
const ApiUserSchema = z.object({
  user_id: z.string(),
  user_name: z.string(),
  user_email: z.string().email(),
}).transform(data => ({
  id: data.user_id,          // Rename snake_case → camelCase
  name: data.user_name,
  email: data.user_email,
}));

// Superrefine: complex cross-field validation
const PasswordSchema = z.object({
  password: z.string().min(8),
  confirm: z.string(),
}).superRefine(({ password, confirm }, ctx) => {
  if (password !== confirm) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Passwords do not match',
      path: ['confirm'],
    });
  }
});

// Discriminated unions
const EventSchema = z.discriminatedUnion('type', [
  z.object({ type: z.literal('click'),  x: z.number(), y: z.number() }),
  z.object({ type: z.literal('key'),    key: z.string() }),
  z.object({ type: z.literal('resize'), width: z.number(), height: z.number() }),
]);
type Event = z.infer<typeof EventSchema>;
```

---

## Step 4: Zod → OpenAPI Schema Generation

```typescript
import { z } from 'zod';
import { zodToJsonSchema } from 'zod-to-json-schema';

const CreateUserSchema = z.object({
  name:  z.string().min(1).max(100).describe('Full name'),
  email: z.string().email().describe('Email address'),
  role:  z.enum(['admin', 'user']).default('user'),
});

// Generate JSON Schema (OpenAPI compatible)
const jsonSchema = zodToJsonSchema(CreateUserSchema, {
  name: 'CreateUser',
  target: 'openApi3',
});

// Integrate into OpenAPI spec
const openApiSpec = {
  openapi: '3.0.0',
  info: { title: 'User API', version: '1.0.0' },
  components: {
    schemas: {
      CreateUser: jsonSchema,
    },
  },
  paths: {
    '/users': {
      post: {
        requestBody: {
          content: {
            'application/json': {
              schema: { $ref: '#/components/schemas/CreateUser' },
            },
          },
        },
      },
    },
  },
};
```

---

## Step 5: Library Comparison

```typescript
// io-ts (functional, verbose)
import * as t from 'io-ts';
const UserCodec = t.type({ id: t.string, name: t.string });
type User = t.TypeOf<typeof UserCodec>;
const result = UserCodec.decode(data); // Either<Errors, User>

// ArkType (concise, no imports needed)
import { type } from 'arktype';
const User = type({ id: 'string', name: 'string' });
type User = typeof User.infer;
const out = User(data); // data | ArkErrors

// Valibot (smallest bundle: ~8KB)
import { object, string, parse } from 'valibot';
const UserSchema = object({ id: string(), name: string() });
const data = parse(UserSchema, untrustedData); // throws on failure

// Zod (most popular, best ecosystem)
const UserSchema = z.object({ id: z.string(), name: z.string() });
type User = z.infer<typeof UserSchema>;
```

---

## Step 6: Type-Safe Environment Variables

```typescript
// Using t3-env
import { createEnv } from '@t3-oss/env-core';
import { z } from 'zod';

export const env = createEnv({
  server: {
    DATABASE_URL:   z.string().url(),
    JWT_SECRET:     z.string().min(32),
    REDIS_URL:      z.string().url().optional(),
    NODE_ENV:       z.enum(['development', 'production', 'test']),
    PORT:           z.coerce.number().int().min(1).max(65535).default(3000),
  },
  client: {
    NEXT_PUBLIC_API_URL: z.string().url(),
    NEXT_PUBLIC_APP_ENV: z.enum(['dev', 'staging', 'prod']),
  },
  runtimeEnv: process.env,
});

// Usage — fully typed, throws at startup if invalid
console.log(env.DATABASE_URL);  // string (URL)
console.log(env.PORT);          // number (coerced from string)
```

---

## Step 7: Middleware Validation Pattern

```typescript
// Express middleware using Zod schemas
import { z, ZodSchema } from 'zod';
import { Request, Response, NextFunction } from 'express';

function validateBody<T>(schema: ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);
    if (!result.success) {
      return res.status(400).json({
        error: 'Validation failed',
        issues: result.error.issues.map(i => ({
          path: i.path.join('.'),
          message: i.message,
          code: i.code,
        })),
      });
    }
    req.body = result.data; // Typed and transformed
    next();
  };
}

// Route
app.post('/users',
  validateBody(CreateUserSchema),
  async (req: Request<{}, {}, z.infer<typeof CreateUserSchema>>, res) => {
    // req.body is fully typed as CreateUser
    const user = await createUser(req.body);
    res.json(user);
  }
);
```

---

## Step 8: Capstone — Zod Runtime Validation

```bash
docker run --rm node:20-alpine sh -c "
  cd /work && npm init -y > /dev/null 2>&1
  npm install zod 2>&1 | tail -1
  node -e \"
const {z} = require('zod');
const Schema = z.object({
  id: z.string().uuid(), name: z.string().min(1).max(100),
  email: z.string().email(), role: z.enum(['admin','user','guest']),
});
const bad = Schema.safeParse({ id: 'not-uuid', name: '', email: 'bad', role: 'admin' });
console.log('=== Zod Runtime Validation ===');
console.log('Valid:', bad.success);
if (!bad.success) bad.error.issues.forEach(i => console.log(' Error:', i.path.join('.'), '-', i.message));
const ok = Schema.safeParse({ id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', name: 'Alice', email: 'alice@example.com', role: 'admin' });
console.log('Valid object:', ok.success);
if (ok.success) console.log('Parsed:', JSON.stringify(ok.data));
  \"
"
```

📸 **Verified Output:**
```
=== Zod Runtime Validation ===
Valid: false
 Error: id - Invalid UUID
 Error: name - Too small: expected string to have >=1 characters
 Error: email - Invalid email address
Valid object: true
Parsed: {"id":"a1b2c3d4-e5f6-7890-abcd-ef1234567890","name":"Alice","email":"alice@example.com","role":"admin"}
```

---

## Summary

| Library | Bundle | DX | Ecosystem | Best For |
|---------|--------|----|-----------|---------| 
| Zod | ~14KB | Excellent | Huge | General purpose |
| ArkType | ~10KB | Concise | Growing | Performance |
| Valibot | ~8KB | Good | Good | Bundle-sensitive |
| io-ts | ~5KB | Verbose | Mature | fp-ts integration |
| t3-env | ~3KB | Excellent | Niche | Env variables |
