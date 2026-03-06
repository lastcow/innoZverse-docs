# Lab 13: Testing with Vitest

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Vitest with TypeScript: describe/it/expect, typed mocks (`vi.fn`), spies, async tests, beforeEach/afterEach, coverage.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab13 && cd /lab13
npm init -y
npm install --save-dev vitest @vitest/coverage-v8
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true
  }
}
EOF
cat > vitest.config.ts << 'EOF'
import { defineConfig } from 'vitest/config';
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: { provider: 'v8' },
  },
});
EOF
```

---

## Step 2: Source Files Under Test

```typescript
// src/math.ts
export function add(a: number, b: number): number { return a + b; }
export function multiply(a: number, b: number): number { return a * b; }
export function divide(a: number, b: number): number {
  if (b === 0) throw new Error('Division by zero');
  return a / b;
}
export function factorial(n: number): number {
  if (n < 0) throw new RangeError('Negative input');
  return n <= 1 ? 1 : n * factorial(n - 1);
}

// src/user-service.ts
export interface User { id: number; name: string; email: string }
export interface UserRepository {
  findById(id: number): Promise<User | null>;
  save(user: Omit<User, 'id'>): Promise<User>;
  delete(id: number): Promise<boolean>;
}

export class UserService {
  constructor(private repo: UserRepository) {}

  async getUser(id: number): Promise<User> {
    const user = await this.repo.findById(id);
    if (!user) throw new Error(`User ${id} not found`);
    return user;
  }

  async createUser(data: Omit<User, 'id'>): Promise<User> {
    if (!data.email.includes('@')) throw new Error('Invalid email');
    return this.repo.save(data);
  }
}
```

---

## Step 3: Basic Tests

```typescript
// src/math.test.ts
import { describe, it, expect } from 'vitest';
import { add, multiply, divide, factorial } from './math';

describe('Math utilities', () => {
  describe('add', () => {
    it('adds two positive numbers', () => {
      expect(add(1, 2)).toBe(3);
    });

    it('adds negative numbers', () => {
      expect(add(-1, -2)).toBe(-3);
    });

    it('handles zero', () => {
      expect(add(5, 0)).toBe(5);
      expect(add(0, 0)).toBe(0);
    });
  });

  describe('divide', () => {
    it('divides correctly', () => {
      expect(divide(10, 2)).toBe(5);
      expect(divide(7, 2)).toBeCloseTo(3.5);
    });

    it('throws on division by zero', () => {
      expect(() => divide(1, 0)).toThrow('Division by zero');
      expect(() => divide(1, 0)).toThrow(Error);
    });
  });

  describe('factorial', () => {
    it.each([
      [0, 1],
      [1, 1],
      [5, 120],
      [10, 3628800],
    ])('factorial(%i) = %i', (n, expected) => {
      expect(factorial(n)).toBe(expected);
    });

    it('throws for negative numbers', () => {
      expect(() => factorial(-1)).toThrow(RangeError);
    });
  });
});
```

---

## Step 4: Typed Mocks (vi.fn)

```typescript
// src/user-service.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UserService, UserRepository, User } from './user-service';

describe('UserService', () => {
  let mockRepo: UserRepository;
  let service: UserService;

  beforeEach(() => {
    // Typed mock — vi.fn<Args, Return>
    mockRepo = {
      findById: vi.fn<[number], Promise<User | null>>(),
      save: vi.fn<[Omit<User, 'id'>], Promise<User>>(),
      delete: vi.fn<[number], Promise<boolean>>(),
    };
    service = new UserService(mockRepo);
    vi.clearAllMocks();
  });

  describe('getUser', () => {
    it('returns user when found', async () => {
      const mockUser: User = { id: 1, name: 'Alice', email: 'alice@example.com' };
      vi.mocked(mockRepo.findById).mockResolvedValue(mockUser);

      const result = await service.getUser(1);

      expect(result).toEqual(mockUser);
      expect(mockRepo.findById).toHaveBeenCalledOnce();
      expect(mockRepo.findById).toHaveBeenCalledWith(1);
    });

    it('throws when user not found', async () => {
      vi.mocked(mockRepo.findById).mockResolvedValue(null);

      await expect(service.getUser(999)).rejects.toThrow('User 999 not found');
    });
  });

  describe('createUser', () => {
    it('creates user with valid data', async () => {
      const dto = { name: 'Bob', email: 'bob@example.com' };
      const created: User = { id: 2, ...dto };
      vi.mocked(mockRepo.save).mockResolvedValue(created);

      const result = await service.createUser(dto);

      expect(result).toEqual(created);
      expect(mockRepo.save).toHaveBeenCalledWith(dto);
    });

    it('throws for invalid email', async () => {
      await expect(service.createUser({ name: 'Bob', email: 'invalid' }))
        .rejects.toThrow('Invalid email');
      expect(mockRepo.save).not.toHaveBeenCalled();
    });
  });
});
```

---

## Step 5: vi.spyOn and Implementation

```typescript
import { describe, it, expect, vi, afterEach } from 'vitest';

// Spy on existing methods without replacing them
class Calculator {
  add(a: number, b: number): number { return a + b; }
  log(result: number): void { console.log(`Result: ${result}`); }
}

describe('Calculator with spies', () => {
  const calc = new Calculator();

  afterEach(() => vi.restoreAllMocks());

  it('spies on add without changing behavior', () => {
    const spy = vi.spyOn(calc, 'add');
    const result = calc.add(2, 3);
    expect(result).toBe(5);
    expect(spy).toHaveBeenCalledWith(2, 3);
  });

  it('replaces implementation temporarily', () => {
    vi.spyOn(calc, 'add').mockReturnValue(42);
    expect(calc.add(1, 1)).toBe(42);
  });

  it('suppresses console.log', () => {
    const spy = vi.spyOn(console, 'log').mockImplementation(() => {});
    calc.log(100);
    expect(spy).toHaveBeenCalledWith('Result: 100');
  });
});
```

---

## Step 6: Async Tests and Timers

```typescript
import { describe, it, expect, vi, beforeAll } from 'vitest';

// Async test patterns
describe('Async tests', () => {
  it('resolves promise', async () => {
    const fetchData = (): Promise<string> =>
      new Promise(r => setTimeout(() => r('data'), 100));

    await expect(fetchData()).resolves.toBe('data');
  });

  it('rejects promise', async () => {
    const fail = (): Promise<never> =>
      Promise.reject(new Error('Network error'));

    await expect(fail()).rejects.toThrow('Network error');
  });

  it('uses fake timers', () => {
    vi.useFakeTimers();
    let called = false;
    setTimeout(() => { called = true; }, 1000);
    expect(called).toBe(false);
    vi.advanceTimersByTime(1000);
    expect(called).toBe(true);
    vi.useRealTimers();
  });
});
```

---

## Step 7: Package.json & Running Tests

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

```bash
# Run tests
npx vitest run

# Watch mode
npx vitest

# Coverage
npx vitest run --coverage
```

---

## Step 8: Capstone — Full Test Suite

```bash
# lab13-capstone — quick runnable test
mkdir -p /lab13cap/src && cd /lab13cap
npm init -y
npm install --save-dev vitest
cat > vitest.config.js << 'EOF'
export default { test: { globals: true } };
EOF
cat > src/math.js << 'EOF'
export function add(a, b) { return a + b; }
export function divide(a, b) {
  if (b === 0) throw new Error('Division by zero');
  return a / b;
}
EOF
cat > src/math.test.js << 'EOF'
import { describe, it, expect } from 'vitest';
import { add, divide } from './math.js';
describe('Math', () => {
  it('adds', () => expect(add(1, 2)).toBe(3));
  it('divides', () => expect(divide(10, 2)).toBe(5));
  it('throws on zero', () => expect(() => divide(1, 0)).toThrow('Division by zero'));
});
EOF
npx vitest run --reporter=verbose
```

📸 **Verified Output:**
```
✓ src/math.test.js (3)
  ✓ Math (3)
    ✓ adds
    ✓ divides
    ✓ throws on zero

 Test Files  1 passed (1)
      Tests  3 passed (3)
```

---

## Summary

| API | Purpose |
|-----|---------|
| `describe(name, fn)` | Group related tests |
| `it(name, fn)` / `test()` | Individual test case |
| `expect(val).toBe(x)` | Strict equality |
| `expect(val).toEqual(x)` | Deep equality |
| `expect(fn).toThrow(msg)` | Thrown error |
| `expect(p).resolves.toBe(x)` | Promise resolves |
| `expect(p).rejects.toThrow(x)` | Promise rejects |
| `vi.fn<Args, Return>()` | Typed mock function |
| `vi.mocked(fn).mockResolvedValue(x)` | Mock async return |
| `vi.spyOn(obj, 'method')` | Spy on real method |
| `it.each([...])` | Parameterized tests |
| `beforeEach` / `afterEach` | Setup / teardown |
