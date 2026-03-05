# Lab 13: Testing with Jest

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master testing in JavaScript using Jest: `describe`/`it`/`expect`, matchers, mocks (`jest.fn`/`jest.spyOn`/`jest.mock`), async testing, and code coverage.

---

## Step 1: Setup

```bash
cd /app && npm init -y
npm install --save-dev jest

# package.json
# "scripts": { "test": "jest", "test:coverage": "jest --coverage" }
```

---

## Step 2: Basic Tests

```javascript
// math.js
function add(a, b) { return a + b; }
function multiply(a, b) { return a * b; }
function divide(a, b) {
  if (b === 0) throw new RangeError('Division by zero');
  return a / b;
}
function factorial(n) {
  if (n < 0) throw new RangeError('n must be non-negative');
  if (n === 0 || n === 1) return 1;
  return n * factorial(n - 1);
}
module.exports = { add, multiply, divide, factorial };

// math.test.js
const { add, multiply, divide, factorial } = require('./math');

describe('add()', () => {
  it('adds two positive numbers', () => {
    expect(add(2, 3)).toBe(5);
  });
  it('handles negative numbers', () => {
    expect(add(-1, 1)).toBe(0);
  });
  it('handles floats', () => {
    expect(add(0.1, 0.2)).toBeCloseTo(0.3);
  });
});

describe('divide()', () => {
  it('divides correctly', () => {
    expect(divide(10, 2)).toBe(5);
  });
  it('throws on division by zero', () => {
    expect(() => divide(10, 0)).toThrow(RangeError);
    expect(() => divide(10, 0)).toThrow('Division by zero');
  });
});

describe('factorial()', () => {
  it.each([
    [0, 1], [1, 1], [5, 120], [10, 3628800]
  ])('factorial(%i) = %i', (n, expected) => {
    expect(factorial(n)).toBe(expected);
  });
});
```

---

## Step 3: Matchers

```javascript
// matchers.test.js
describe('Jest Matchers', () => {
  // Equality
  test('toBe — strict equality (===)', () => {
    expect(1 + 1).toBe(2);
    expect('hello').toBe('hello');
  });

  test('toEqual — deep equality', () => {
    expect({ a: 1, b: { c: 2 } }).toEqual({ a: 1, b: { c: 2 } });
    expect([1, [2, 3]]).toEqual([1, [2, 3]]);
  });

  // Truthiness
  test('truthy/falsy matchers', () => {
    expect(1).toBeTruthy();
    expect('').toBeFalsy();
    expect(null).toBeNull();
    expect(undefined).toBeUndefined();
    expect(0).toBeDefined(); // 0 is defined (not undefined)
  });

  // Numbers
  test('number matchers', () => {
    expect(3.14).toBeGreaterThan(3);
    expect(3.14).toBeLessThanOrEqual(3.14);
    expect(0.1 + 0.2).toBeCloseTo(0.3, 5);
  });

  // Strings
  test('string matchers', () => {
    expect('Hello, World').toContain('World');
    expect('hello@example.com').toMatch(/\w+@\w+\.\w+/);
  });

  // Arrays
  test('array matchers', () => {
    expect([1, 2, 3]).toContain(2);
    expect([1, 2, 3]).toHaveLength(3);
    expect(['apple', 'banana']).toEqual(expect.arrayContaining(['apple']));
  });

  // Objects
  test('object matchers', () => {
    const user = { id: 1, name: 'Alice', email: 'alice@ex.com' };
    expect(user).toHaveProperty('name');
    expect(user).toHaveProperty('name', 'Alice');
    expect(user).toMatchObject({ id: 1, name: 'Alice' });
  });
});
```

---

## Step 4: Mocking Functions

```javascript
// service.js
const axios = require('axios');

async function getUser(id) {
  const response = await axios.get(`https://api.example.com/users/${id}`);
  return response.data;
}

async function processUsers(userIds) {
  const users = await Promise.all(userIds.map(id => getUser(id)));
  return users.map(u => ({ ...u, processed: true }));
}

module.exports = { getUser, processUsers };

// service.test.js
const axios = require('axios');
jest.mock('axios'); // Auto-mock the module

describe('getUser()', () => {
  beforeEach(() => jest.clearAllMocks());

  it('fetches user successfully', async () => {
    const mockUser = { id: 1, name: 'Alice' };
    axios.get.mockResolvedValue({ data: mockUser });

    const user = await getUser(1);
    expect(user).toEqual(mockUser);
    expect(axios.get).toHaveBeenCalledWith('https://api.example.com/users/1');
    expect(axios.get).toHaveBeenCalledTimes(1);
  });

  it('handles API errors', async () => {
    axios.get.mockRejectedValue(new Error('Network error'));
    await expect(getUser(1)).rejects.toThrow('Network error');
  });
});
```

---

## Step 5: jest.fn and jest.spyOn

```javascript
// jest.fn — create mock functions
describe('jest.fn()', () => {
  it('tracks calls', () => {
    const mockFn = jest.fn((x) => x * 2);

    const results = [1, 2, 3].map(mockFn);

    expect(mockFn).toHaveBeenCalledTimes(3);
    expect(mockFn).toHaveBeenCalledWith(1, 0, [1, 2, 3]);
    expect(mockFn).toHaveBeenLastCalledWith(3, 2, [1, 2, 3]);
    expect(results).toEqual([2, 4, 6]);
  });

  it('can return specific values', () => {
    const mockFn = jest.fn()
      .mockReturnValueOnce('first')
      .mockReturnValueOnce('second')
      .mockReturnValue('default');

    expect(mockFn()).toBe('first');
    expect(mockFn()).toBe('second');
    expect(mockFn()).toBe('default');
    expect(mockFn()).toBe('default');
  });
});

// jest.spyOn — spy on existing methods
describe('jest.spyOn()', () => {
  it('spies on object methods', () => {
    const console_log = jest.spyOn(console, 'log').mockImplementation(() => {});
    console.log('test message');
    expect(console_log).toHaveBeenCalledWith('test message');
    console_log.mockRestore(); // Restore original
  });

  it('spies on Date.now', () => {
    const now = Date.now;
    jest.spyOn(Date, 'now').mockReturnValue(1704067200000);
    expect(Date.now()).toBe(1704067200000);
    Date.now = now; // Restore
  });
});
```

---

## Step 6: Async Testing

```javascript
// async.test.js
function fetchData(shouldFail = false) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (shouldFail) reject(new Error('Fetch failed'));
      else resolve({ data: [1, 2, 3] });
    }, 10);
  });
}

describe('Async tests', () => {
  // Return the promise
  it('resolves with data (Promise)', () => {
    return fetchData().then(result => {
      expect(result.data).toEqual([1, 2, 3]);
    });
  });

  // async/await
  it('resolves with data (async/await)', async () => {
    const result = await fetchData();
    expect(result.data).toHaveLength(3);
  });

  // resolves/rejects matchers
  it('resolves correctly', () => {
    return expect(fetchData()).resolves.toMatchObject({ data: [1, 2, 3] });
  });

  it('rejects on failure', () => {
    return expect(fetchData(true)).rejects.toThrow('Fetch failed');
  });

  // Fake timers
  it('works with fake timers', () => {
    jest.useFakeTimers();
    const callback = jest.fn();
    setTimeout(callback, 1000);
    jest.advanceTimersByTime(1000);
    expect(callback).toHaveBeenCalled();
    jest.useRealTimers();
  });
});
```

---

## Step 7: Setup/Teardown and Coverage

```javascript
// lifecycle.test.js
let db;

beforeAll(async () => {
  // Run once before all tests in this file
  db = await createTestDatabase();
  console.log('Database initialized');
});

afterAll(async () => {
  await db.close();
});

beforeEach(async () => {
  // Run before each test
  await db.clear();
  await db.seed([{ id: 1, name: 'Alice' }]);
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('UserRepository', () => {
  it('finds user by id', async () => {
    const user = await db.findById(1);
    expect(user.name).toBe('Alice');
  });

  it('returns null for missing user', async () => {
    const user = await db.findById(999);
    expect(user).toBeNull();
  });
});

// jest.config.js — Coverage configuration
module.exports = {
  collectCoverage: true,
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  coverageDirectory: 'coverage',
  collectCoverageFrom: ['src/**/*.js', '!src/**/*.test.js']
};
```

---

## Step 8: Capstone — Inline Jest Test

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && npm init -y --quiet > /dev/null
npm install --save-dev jest --quiet > /dev/null 2>&1
cat > /tmp/math.js << 'EOF'
function add(a, b) { return a + b; }
function multiply(a, b) { return a * b; }
function divide(a, b) {
  if (b === 0) throw new RangeError('Division by zero');
  return a / b;
}
module.exports = { add, multiply, divide };
EOF

cat > /tmp/math.test.js << 'EOF'
const { add, multiply, divide } = require('./math');
describe('math', () => {
  test('add', () => { expect(add(2, 3)).toBe(5); });
  test('multiply', () => { expect(multiply(3, 4)).toBe(12); });
  test('divide', () => { expect(divide(10, 2)).toBe(5); });
  test('divide by zero throws', () => {
    expect(() => divide(10, 0)).toThrow(RangeError);
  });
  test('mock fn', () => {
    const fn = jest.fn().mockReturnValue(42);
    expect(fn()).toBe(42);
    expect(fn).toHaveBeenCalledTimes(1);
  });
});
EOF

cd /tmp && npx jest --no-coverage math.test.js 2>&1 | tail -12
"
```

📸 **Verified Output:**
```
 PASS  /tmp/math.test.js
  math
    ✓ add (Xms)
    ✓ multiply (Xms)
    ✓ divide (Xms)
    ✓ divide by zero throws (Xms)
    ✓ mock fn (Xms)

Test Suites: 1 passed, 1 total
Tests:       5 passed, 5 total
```

---

## Summary

| Jest API | Purpose |
|----------|---------|
| `describe(name, fn)` | Group related tests |
| `test`/`it(name, fn)` | Individual test case |
| `expect(val).toBe(v)` | Strict equality |
| `expect(val).toEqual(v)` | Deep equality |
| `expect(fn).toThrow()` | Expect thrown error |
| `jest.fn()` | Create mock function |
| `jest.spyOn(obj, 'method')` | Spy on existing method |
| `jest.mock('module')` | Auto-mock a module |
| `.resolves`/`.rejects` | Assert async promise |
| `beforeAll/afterAll` | Run once per suite |
| `beforeEach/afterEach` | Run around each test |
