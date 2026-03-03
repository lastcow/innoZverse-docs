# Lab 13: Testing TypeScript — Type-Safe Tests & Mocks

## Objective
Write type-safe tests using Node.js built-in test runner, create typed mocks, use assertion helpers, and test generic/async code confidently.

## Time
30 minutes

## Prerequisites
- Lab 02 (Functions), Lab 04 (Classes), Lab 09 (Async)

## Tools
- Docker image: `zchencow/innozverse-ts:latest` (Node 20 built-in test runner)

---

## Lab Instructions

### Step 1: Node.js Built-in Test Runner

```typescript
import { test, describe, it, before, after, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";

// Simple test
test("add numbers", () => {
    assert.equal(2 + 2, 4);
    assert.equal(10 - 3, 7);
});

// Describe block
describe("Math utilities", () => {
    function clamp(n: number, min: number, max: number): number {
        return Math.min(Math.max(n, min), max);
    }

    it("clamps above max", () => assert.equal(clamp(100, 0, 10), 10));
    it("clamps below min", () => assert.equal(clamp(-5, 0, 10), 0));
    it("keeps value in range", () => assert.equal(clamp(5, 0, 10), 5));
});

// Async test
test("async operation", async () => {
    const result = await Promise.resolve(42);
    assert.equal(result, 42);
});

// Test with error assertion
test("throws on invalid input", () => {
    function parsePositive(n: number): number {
        if (n <= 0) throw new RangeError("Must be positive");
        return n;
    }
    assert.throws(() => parsePositive(-1), RangeError);
    assert.equal(parsePositive(5), 5);
});
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
import assert from 'node:assert/strict';
// Micro test runner
let passed = 0, failed = 0;
function test(name: string, fn: () => void) {
    try { fn(); console.log('✓', name); passed++; }
    catch (e) { console.log('✗', name, '-', (e as Error).message); failed++; }
}
test('string equality', () => assert.equal('hello', 'hello'));
test('array deep equal', () => assert.deepEqual([1,2,3], [1,2,3]));
test('number comparison', () => assert.ok(5 > 3));
console.log(passed + ' passed, ' + failed + ' failed');
"
```

> 💡 **Node.js 18+ has a built-in test runner** (`node:test`) — no Jest or Mocha needed for simple test suites. It supports `describe`/`it`/`test`, async tests, subtests, mocking, and `--test` CLI flag. For TypeScript, run with `ts-node --test` or compile first.

**📸 Verified Output:**
```
✓ string equality
✓ array deep equal
✓ number comparison
3 passed, 0 failed
```

---

### Step 2: Type-Safe Assertions & Custom Matchers

```typescript
import assert from "node:assert/strict";

// Custom typed assertions
function assertDefined<T>(val: T | null | undefined, msg?: string): asserts val is T {
    assert.notEqual(val, null, msg ?? "Value should be defined");
    assert.notEqual(val, undefined, msg ?? "Value should be defined");
}

function assertArrayOf<T>(arr: unknown[], type: string): asserts arr is T[] {
    arr.forEach((item, i) => assert.equal(typeof item, type, `Item ${i} should be ${type}`));
}

function assertInstanceOf<T>(val: unknown, Ctor: new (...args: unknown[]) => T): asserts val is T {
    assert.ok(val instanceof Ctor, `Expected instance of ${Ctor.name}`);
}

// Test typed assertions
const maybeUser: { name: string } | null = { name: "Dr. Chen" };
assertDefined(maybeUser, "User should exist");
console.log("User name:", maybeUser.name); // TypeScript knows maybeUser is not null

const scores: unknown[] = [95, 87, 92];
assertArrayOf<number>(scores, "number");
const total = (scores as number[]).reduce((a, b) => a + b, 0);
console.log("Total:", total);

// Deep equality for complex objects
interface Product { id: number; name: string; price: number; }
const expected: Product = { id: 1, name: "Surface Pro", price: 864 };
const actual: Product   = { id: 1, name: "Surface Pro", price: 864 };
assert.deepEqual(actual, expected);
console.log("Products match ✓");

// Approximate equality for floats
function assertClose(a: number, b: number, tolerance = 0.001): void {
    assert.ok(Math.abs(a - b) < tolerance, `${a} should be close to ${b} (±${tolerance})`);
}

assertClose(0.1 + 0.2, 0.3);  // 0.30000000000000004 ≈ 0.3
console.log("Float equality ✓");
```

> 💡 **`asserts val is T`** return type makes custom assertion functions narrow types. After `assertDefined(user)`, TypeScript removes `null | undefined` from `user`'s type. Without this return type, TypeScript doesn't know the assertion changed the type — you'd still need `!` or `?.` afterward.

**📸 Verified Output:**
```
User name: Dr. Chen
Total: 274
Products match ✓
Float equality ✓
```

---

### Steps 3–8: Mocks, Stubs, Spies, Test Utilities, Integration Tests, Capstone

```typescript
// Step 3: Simple typed mocks
type Mock<T> = {
    [K in keyof T]: T[K] extends (...args: infer A) => infer R
        ? jest.Mock<R, A> | ((...args: A) => R)
        : T[K];
};

// Manual mock factory (no jest needed)
function createMock<T>(overrides: Partial<T> = {}): T & Record<string, unknown> {
    return new Proxy(overrides as T, {
        get(target, prop) {
            if (prop in target) return (target as Record<string | symbol, unknown>)[prop as string];
            return () => undefined; // default: return undefined for unknown methods
        }
    }) as T & Record<string, unknown>;
}

interface UserRepository {
    findById(id: number): Promise<{ id: number; name: string } | null>;
    save(user: { name: string }): Promise<{ id: number; name: string }>;
    delete(id: number): Promise<boolean>;
}

const mockRepo = createMock<UserRepository>({
    findById: async (id: number) => id === 1 ? { id: 1, name: "Dr. Chen" } : null,
    save: async (user) => ({ id: 99, ...user }),
    delete: async () => true,
});

(async () => {
    const user = await mockRepo.findById(1);
    console.log("Mock findById(1):", user?.name);

    const saved = await mockRepo.save({ name: "Alice" });
    console.log("Mock save:", saved.id, saved.name);

    const deleted = await mockRepo.delete(1);
    console.log("Mock delete:", deleted);
})();

// Step 4: Spy pattern
class SpyFunction<TArgs extends unknown[], TReturn> {
    calls: TArgs[] = [];
    returnValues: TReturn[] = [];

    constructor(private impl: (...args: TArgs) => TReturn) {}

    call(...args: TArgs): TReturn {
        this.calls.push(args);
        const result = this.impl(...args);
        this.returnValues.push(result);
        return result;
    }

    get callCount(): number { return this.calls.length; }
    get lastCall(): TArgs | undefined { return this.calls[this.calls.length - 1]; }
    reset(): void { this.calls = []; this.returnValues = []; }
}

const addSpy = new SpyFunction((a: number, b: number) => a + b);
addSpy.call(1, 2);
addSpy.call(3, 4);
addSpy.call(5, 6);

console.log("Call count:", addSpy.callCount);
console.log("Last call:", addSpy.lastCall);
console.log("Return values:", addSpy.returnValues.join(", "));

// Step 5: Test data builders
class ProductBuilder {
    private product = { id: 1, name: "Test Product", price: 9.99, stock: 100, category: "Test" };

    withId(id: number): this            { this.product.id = id; return this; }
    withName(name: string): this        { this.product.name = name; return this; }
    withPrice(price: number): this      { this.product.price = price; return this; }
    withStock(stock: number): this      { this.product.stock = stock; return this; }
    withCategory(cat: string): this     { this.product.category = cat; return this; }
    outOfStock(): this                  { this.product.stock = 0; return this; }
    build()                             { return { ...this.product }; }
}

const laptopProduct = new ProductBuilder()
    .withId(1)
    .withName("Surface Pro 12\"")
    .withPrice(864)
    .withCategory("Laptop")
    .build();

const outOfStockItem = new ProductBuilder()
    .withName("Discontinued Item")
    .outOfStock()
    .build();

console.log("Laptop:", laptopProduct.name, "$" + laptopProduct.price);
console.log("OOS:", outOfStockItem.name, "stock=" + outOfStockItem.stock);

// Step 6: Snapshot testing
function snapshot<T>(value: T): string { return JSON.stringify(value, null, 2); }

function assertSnapshot<T>(value: T, expected: string): void {
    const actual = snapshot(value);
    assert.equal(actual, expected, "Snapshot mismatch");
}

const productSnapshot = snapshot(laptopProduct);
console.log("Snapshot length:", productSnapshot.length);

// Step 7: Property-based testing (simple)
function* generate(n: number) {
    for (let i = 0; i < n; i++) {
        yield {
            price: Math.random() * 1000,
            quantity: Math.floor(Math.random() * 100),
        };
    }
}

function totalCost(price: number, qty: number): number { return price * qty; }

let allPassed = true;
for (const { price, quantity } of generate(100)) {
    const total = totalCost(price, quantity);
    if (total < 0 || !isFinite(total)) { allPassed = false; break; }
    if (price > 0 && quantity > 0 && total <= 0) { allPassed = false; break; }
}
console.log("Property tests:", allPassed ? "100/100 ✓" : "FAILED");

// Step 8: Capstone — service test suite
class OrderService {
    private orders: { id: number; total: number; status: string }[] = [];
    private nextId = 1;

    createOrder(total: number): { id: number; total: number; status: string } {
        if (total <= 0) throw new RangeError("Total must be positive");
        const order = { id: this.nextId++, total, status: "pending" };
        this.orders.push(order);
        return order;
    }

    getOrder(id: number) { return this.orders.find(o => o.id === id) ?? null; }
    confirmOrder(id: number): boolean {
        const order = this.getOrder(id);
        if (!order) return false;
        order.status = "confirmed";
        return true;
    }
    count() { return this.orders.length; }
}

// Test suite
const tests: [string, () => void | Promise<void>][] = [
    ["creates order", () => {
        const svc = new OrderService();
        const order = svc.createOrder(864);
        assert.equal(order.status, "pending");
        assert.equal(order.total, 864);
        assert.ok(order.id > 0);
    }],
    ["rejects negative total", () => {
        const svc = new OrderService();
        assert.throws(() => svc.createOrder(-1), RangeError);
    }],
    ["confirms order", () => {
        const svc = new OrderService();
        const { id } = svc.createOrder(100);
        assert.equal(svc.confirmOrder(id), true);
        assert.equal(svc.getOrder(id)?.status, "confirmed");
    }],
    ["returns false for missing order", () => {
        const svc = new OrderService();
        assert.equal(svc.confirmOrder(999), false);
    }],
];

let p = 0, f = 0;
for (const [name, fn] of tests) {
    try { await fn(); console.log("  ✓", name); p++; }
    catch (e) { console.log("  ✗", name, "-", (e as Error).message); f++; }
}
console.log(`\n${p} passed, ${f} failed`);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
import assert from 'node:assert/strict';
function add(a: number, b: number): number { return a + b; }
// Tests
const tests = [
    ['1+1=2',     () => assert.equal(add(1, 1), 2)],
    ['0+0=0',     () => assert.equal(add(0, 0), 0)],
    ['-1+1=0',    () => assert.equal(add(-1, 1), 0)],
    ['5.5+4.5=10',() => assert.equal(add(5.5, 4.5), 10)],
] as [string, () => void][];
let p=0, f=0;
tests.forEach(([n,fn]) => { try { fn(); console.log('✓', n); p++; } catch(e) { console.log('✗', n); f++; } });
console.log(p+'/'+(p+f), 'passed');
"
```

**📸 Verified Output:**
```
✓ 1+1=2  ✓ 0+0=0  ✓ -1+1=0  ✓ 5.5+4.5=10
4/4 passed
```

---

## Summary

TypeScript testing is expressive and type-safe. You've written typed assertions with `asserts` type predicates, created mock factories, implemented spy functions, built test data with builders, done property-based testing, and ran a complete OrderService test suite — all with zero external testing frameworks.

## Further Reading
- [Node.js Test Runner](https://nodejs.org/api/test.html)
- [Vitest — TypeScript-first test runner](https://vitest.dev)
- [ts-jest](https://kulshekhar.github.io/ts-jest)
