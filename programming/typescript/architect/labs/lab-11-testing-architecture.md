# Lab 11: Testing Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

TypeScript testing architecture: Vitest with full type inference, type-level testing with `expectTypeOf`, MSW typed request handlers, typed test fixtures with factory pattern, and property-based testing with fast-check.

---

## Step 1: Vitest Setup

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,              // No import needed for describe/test/expect
    environment: 'node',        // or 'jsdom' for browser-like
    typecheck: {
      enabled: true,            // Run type tests with tsc
      tsconfig: './tsconfig.test.json',
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      thresholds: { lines: 80, functions: 80, branches: 70 },
    },
    setupFiles: ['./src/test/setup.ts'],
  },
});
```

---

## Step 2: Type-Level Tests with expectTypeOf

```typescript
// src/__tests__/types.test-d.ts (.test-d.ts = type-only test file)
import { expectTypeOf, assertType } from 'vitest';
import type { User, UserRole } from '../types';
import { createUser, updateUser } from '../services/users';

describe('User type shapes', () => {
  test('UserRole is a string union', () => {
    expectTypeOf<UserRole>().toEqualTypeOf<'admin' | 'user' | 'guest'>();
    // compile error if type changes
  });

  test('createUser returns User', () => {
    expectTypeOf(createUser).returns.toMatchTypeOf<Promise<User>>();
  });

  test('updateUser accepts partial fields', () => {
    expectTypeOf(updateUser).parameter(1).toMatchTypeOf<Partial<User>>();
  });

  test('User id is string not number', () => {
    expectTypeOf<User['id']>().toBeString();
    expectTypeOf<User['id']>().not.toBeNumber();
  });

  // assertType: fails if type doesn't match
  const role: UserRole = 'admin';
  assertType<'admin' | 'user' | 'guest'>(role);
});
```

---

## Step 3: MSW — Typed Request Handlers

```typescript
// src/test/handlers.ts
import { http, HttpResponse } from 'msw';
import type { User, CreateUserInput } from '../types';

export const handlers = [
  // GET /api/users/:id
  http.get<{ id: string }, never, User>('/api/users/:id', ({ params }) => {
    const { id } = params;  // { id: string } — typed from path params
    const user: User = {
      id,
      name: 'Test User',
      email: 'test@example.com',
      role: 'user',
      createdAt: new Date(),
    };
    return HttpResponse.json(user);
  }),

  // POST /api/users
  http.post<never, CreateUserInput, User>('/api/users', async ({ request }) => {
    const body = await request.json() as CreateUserInput;
    const newUser: User = { id: 'new-id', ...body, createdAt: new Date() };
    return HttpResponse.json(newUser, { status: 201 });
  }),

  // Error case
  http.get('/api/users/not-found', () =>
    HttpResponse.json({ error: 'User not found' }, { status: 404 })
  ),
];

// setupTests.ts
import { server } from './server';
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

---

## Step 4: Typed Test Fixtures — Factory Pattern

```typescript
// src/test/factories.ts
import { faker } from '@faker-js/faker';
import type { User, Post, Order } from '../types';

// Type-safe factory with overrides
function createUser(overrides: Partial<User> = {}): User {
  return {
    id:        faker.string.uuid(),
    name:      faker.person.fullName(),
    email:     faker.internet.email(),
    role:      'user',
    createdAt: faker.date.past(),
    ...overrides,
  };
}

function createPost(overrides: Partial<Post> = {}): Post {
  return {
    id:        faker.string.uuid(),
    title:     faker.lorem.sentence(),
    body:      faker.lorem.paragraphs(3),
    authorId:  faker.string.uuid(),
    published: false,
    createdAt: faker.date.past(),
    ...overrides,
  };
}

// Builder pattern for complex objects
class OrderBuilder {
  private data: Order;

  constructor() {
    this.data = {
      id:       faker.string.uuid(),
      userId:   faker.string.uuid(),
      items:    [],
      status:   'pending',
      total:    0,
      createdAt: new Date(),
    };
  }

  withUser(userId: string): this {
    this.data.userId = userId;
    return this;
  }

  withItem(productId: string, price: number, qty = 1): this {
    this.data.items.push({ productId, price, quantity: qty });
    this.data.total += price * qty;
    return this;
  }

  withStatus(status: Order['status']): this {
    this.data.status = status;
    return this;
  }

  build(): Order { return { ...this.data }; }
}

export { createUser, createPost, OrderBuilder };
```

---

## Step 5: Property-Based Testing with fast-check

```typescript
import fc from 'fast-check';
import { describe, test, expect } from 'vitest';
import { sortUsers, calculateDiscount } from '../utils';

describe('Property-based tests', () => {
  // Property 1: sort is stable and idempotent
  test('sortUsers is idempotent', () => {
    fc.assert(fc.property(
      fc.array(fc.record({
        id:   fc.string(),
        name: fc.string(),
        age:  fc.integer({ min: 0, max: 120 }),
      })),
      (users) => {
        const once  = sortUsers(users, 'name');
        const twice = sortUsers(once,  'name');
        return twice.every((u, i) => u.id === once[i].id);
      }
    ), { numRuns: 200 });
  });

  // Property 2: discount calculation is bounded
  test('discount is always between 0% and 50%', () => {
    fc.assert(fc.property(
      fc.float({ min: 0, max: 10000 }),
      fc.integer({ min: 0, max: 100 }),
      (price, loyaltyPoints) => {
        const discounted = calculateDiscount(price, loyaltyPoints);
        return discounted >= price * 0.5 && discounted <= price;
      }
    ));
  });

  // Property 3: serialization round-trip
  test('JSON.stringify/parse is identity for valid data', () => {
    fc.assert(fc.property(
      fc.record({
        id:   fc.uuidV(4),
        name: fc.string({ minLength: 1 }),
        role: fc.constantFrom('admin' as const, 'user' as const),
      }),
      (obj) => {
        const roundTripped = JSON.parse(JSON.stringify(obj));
        return roundTripped.id === obj.id && roundTripped.role === obj.role;
      }
    ));
  });
});
```

---

## Step 6: Integration Test with Dependency Injection

```typescript
// src/__tests__/user-service.test.ts
import { describe, test, expect, vi } from 'vitest';
import { UserService } from '../services/UserService';
import { createUser } from '../test/factories';
import type { UserRepository } from '../repositories/UserRepository';

describe('UserService', () => {
  // Mock the repository
  const mockRepo: UserRepository = {
    findById: vi.fn(),
    create:   vi.fn(),
    update:   vi.fn(),
    delete:   vi.fn(),
  };

  const service = new UserService(mockRepo);

  test('getUser returns user when found', async () => {
    const user = createUser({ role: 'admin' });
    vi.mocked(mockRepo.findById).mockResolvedValue(user);

    const result = await service.getUser(user.id);

    expect(result).toEqual(user);
    expect(mockRepo.findById).toHaveBeenCalledWith(user.id);
  });

  test('createUser validates email', async () => {
    await expect(
      service.createUser({ name: 'Alice', email: 'not-an-email', role: 'user' })
    ).rejects.toThrow('Invalid email');
  });
});
```

---

## Step 7: Snapshot Testing with Type Checks

```typescript
test('user profile snapshot', () => {
  const user = createUser({
    id: 'test-id-123',
    name: 'Alice Smith',
    email: 'alice@test.com',
  });
  // Vitest will create/compare snapshot
  expect(user).toMatchInlineSnapshot(`
    {
      "createdAt": Any<Date>,
      "email": "alice@test.com",
      "id": "test-id-123",
      "name": "Alice Smith",
      "role": "user",
    }
  `);
});
```

---

## Step 8: Capstone — Property-Based Tests

```bash
docker run --rm node:20-alpine sh -c "
  mkdir -p /work && cd /work && npm init -y > /dev/null 2>&1
  npm install fast-check 2>&1 | tail -1
  node -e \"
const fc = require('fast-check');
console.log('=== Property-Based Tests with fast-check ===');
fc.assert(fc.property(fc.string(), (s) => {
  return s.split('').reverse().join('').split('').reverse().join('') === s;
}));
console.log('PASS: reverse(reverse(s)) === s for all strings');
const sort = (arr) => [...arr].sort((a,b)=>a-b);
fc.assert(fc.property(fc.array(fc.integer({min:-100,max:100})), (arr) => {
  const once = sort(arr); const twice = sort(once);
  return once.every((v,i) => v === twice[i]);
}));
console.log('PASS: sort(sort(arr)) === sort(arr)');
function createBranded(value, brand) { return Object.freeze({ __brand: brand, value }); }
const isSqlQuery = (x) => x && x.__brand === 'SqlQuery';
const query = createBranded('SELECT 1', 'SqlQuery');
console.log('PASS: SqlQuery branded type:', isSqlQuery(query), '| raw string:', isSqlQuery('SELECT 1'));
console.log('All property tests passed!');
  \"
"
```

📸 **Verified Output:**
```
=== Property-Based Tests with fast-check ===
PASS: reverse(reverse(s)) === s for all strings
PASS: sort(sort(arr)) === sort(arr)
PASS: SqlQuery branded type: true | raw string: false
All property tests passed!
```

---

## Summary

| Tool | Purpose | TypeScript Benefit |
|------|---------|-------------------|
| Vitest | Unit/integration tests | Full TS inference |
| `expectTypeOf` | Type-level tests | Catch type regressions |
| MSW | API mocking | Typed request/response |
| Factory pattern | Test data | Type-safe overrides |
| fast-check | Property-based | Generate edge cases |
| `vi.fn()` | Mocking | Type-preserving mocks |
| `toMatchInlineSnapshot` | Regression | Visual type output |
