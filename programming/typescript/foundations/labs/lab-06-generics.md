# Lab 6: Generics Deep Dive

## Objective
Master advanced generic patterns: constrained generics, conditional types, `infer`, variance, generic utility types, and building reusable generic data structures.

## Time
35 minutes

## Prerequisites
- Lab 02 (Functions), Lab 03 (Interfaces)

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Generic Constraints

```typescript
// keyof constraint
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}

// Multiple constraints
function merge<T extends object, U extends object>(a: T, b: U): T & U {
    return { ...a, ...b };
}

// Constraint with interface
interface HasId { id: number; }
interface HasName { name: string; }

function findById<T extends HasId>(items: T[], id: number): T | undefined {
    return items.find(item => item.id === id);
}

function sortByName<T extends HasName>(items: T[]): T[] {
    return [...items].sort((a, b) => a.name.localeCompare(b.name));
}

const products = [
    { id: 1, name: "Surface Pro", price: 864 },
    { id: 2, name: "Surface Pen", price: 49 },
    { id: 3, name: "Office 365", price: 99 },
];

console.log(findById(products, 2));
sortByName(products).forEach(p => console.log(` ${p.name}`));

const merged = merge({ a: 1, b: 2 }, { c: 3, d: "four" });
console.log(merged); // { a: 1, b: 2, c: 3, d: 'four' }
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
function pick<T, K extends keyof T>(obj: T, keys: K[]): Pick<T, K> {
    return Object.fromEntries(keys.map(k => [k, obj[k]])) as Pick<T, K>;
}
const product = { id: 1, name: 'Surface Pro', price: 864, stock: 15 };
console.log(JSON.stringify(pick(product, ['name', 'price'])));
"
```

> 💡 **`K extends keyof T`** constrains `K` to be one of the actual keys of `T`. This makes `getProperty(user, "name")` safe — TypeScript knows the return type is `string`, not `unknown`. Without this constraint, you'd need to use `as unknown` casts everywhere.

**📸 Verified Output:**
```
{"name":"Surface Pro","price":864}
```

---

### Step 2: Conditional Types & infer

```typescript
// Extract array element type
type ElementOf<T> = T extends (infer E)[] ? E : never;
type PromiseValue<T> = T extends Promise<infer V> ? V : T;
type FunctionReturn<T> = T extends (...args: unknown[]) => infer R ? R : never;
type FunctionParams<T> = T extends (...args: infer P) => unknown ? P : never;

// Deeply unwrap arrays
type DeepFlatten<T> = T extends (infer E)[] ? DeepFlatten<E> : T;

type E1 = ElementOf<string[]>;        // string
type E2 = ElementOf<number[][]>;      // number[] (one level)
type E3 = DeepFlatten<number[][][]>;  // number

type P1 = PromiseValue<Promise<string>>;   // string
type P2 = PromiseValue<number>;            // number (not a promise)

// Awaited<T> — recursively unwrap promises
type MyAwaited<T> = T extends Promise<infer V> ? MyAwaited<V> : T;
type A1 = MyAwaited<Promise<Promise<string>>>;  // string

// Practical: get the type a function returns
async function fetchUser() { return { id: 1, name: "Dr. Chen" }; }
type User = Awaited<ReturnType<typeof fetchUser>>; // { id: number; name: string }

// Distributive conditional types
type StringOrNumber<T> = T extends string ? "it's a string" : "it's not a string";
type R1 = StringOrNumber<string | number>; // "it's a string" | "it's not a string"

console.log("Conditional types checked at compile time");
console.log("infer keyword extracts type from within another type");

// Runtime usage
function isArray<T>(val: T | T[]): val is T[] {
    return Array.isArray(val);
}

const maybeArr: string | string[] = ["a", "b", "c"];
if (isArray(maybeArr)) {
    console.log("Is array:", maybeArr.length);
}
```

> 💡 **`infer` names a type variable within a conditional type.** `T extends Promise<infer V>` says "if T is a Promise of something, name that something V and use it." This is the only way to extract type components from generic types. `ReturnType`, `Parameters`, `InstanceType` all use `infer`.

**📸 Verified Output:**
```
Conditional types checked at compile time
infer keyword extracts type from within another type
Is array: 3
```

---

### Step 3: Generic Data Structures

```typescript
class Optional<T> {
    private constructor(private readonly _value: T | null) {}

    static of<T>(value: T): Optional<T>     { return new Optional(value); }
    static empty<T>(): Optional<T>           { return new Optional<T>(null); }
    static from<T>(val: T | null | undefined): Optional<T> {
        return val == null ? Optional.empty() : Optional.of(val);
    }

    isPresent(): boolean { return this._value !== null; }
    get(): T {
        if (!this.isPresent()) throw new Error("Optional is empty");
        return this._value as T;
    }
    getOrElse(defaultVal: T): T { return this.isPresent() ? (this._value as T) : defaultVal; }
    map<U>(fn: (val: T) => U): Optional<U> { return this.isPresent() ? Optional.of(fn(this._value as T)) : Optional.empty(); }
    filter(pred: (val: T) => boolean): Optional<T> { return this.isPresent() && pred(this._value as T) ? this : Optional.empty(); }
    flatMap<U>(fn: (val: T) => Optional<U>): Optional<U> { return this.isPresent() ? fn(this._value as T) : Optional.empty(); }
}

const users = [
    { id: 1, name: "Dr. Chen", email: "chen@example.com" },
    { id: 2, name: "Alice", email: null },
];

users.forEach(u => {
    const email = Optional.from(u.email)
        .map(e => e.toLowerCase())
        .filter(e => e.includes("@"))
        .getOrElse("no-email@example.com");
    console.log(`${u.name}: ${email}`);
});

// Generic Result type
type Result<T, E = Error> =
    | { ok: true; value: T }
    | { ok: false; error: E };

function ok<T>(value: T): Result<T, never> { return { ok: true, value }; }
function err<E extends Error>(error: E): Result<never, E> { return { ok: false, error }; }

function divideResult(a: number, b: number): Result<number> {
    return b === 0 ? err(new Error("Division by zero")) : ok(a / b);
}

[divideResult(10, 2), divideResult(10, 0)].forEach(r => {
    console.log(r.ok ? `Result: ${r.value}` : `Error: ${r.error.message}`);
});
```

> 💡 **`Optional<T>`** (Java-style Maybe monad) avoids null pointer errors — instead of returning `null`, return `Optional.empty()`. Callers use `map`, `filter`, and `getOrElse` to chain operations safely. If the optional is empty, operations are skipped automatically.

**📸 Verified Output:**
```
Dr. Chen: chen@example.com
Alice: no-email@example.com
Result: 5
Error: Division by zero
```

---

### Steps 4–8: Generic Builder, Repository, Middleware, Pipeline, Capstone

```typescript
// Step 4: Generic Builder Pattern
class Builder<T extends Record<string, unknown>> {
    private data: Partial<T> = {};

    set<K extends keyof T>(key: K, value: T[K]): this {
        this.data[key] = value;
        return this;
    }

    build(defaults: T): T {
        return { ...defaults, ...this.data } as T;
    }
}

interface Config {
    host: string; port: number; ssl: boolean; timeout: number; maxRetries: number;
}

const config = new Builder<Config>()
    .set("host", "localhost")
    .set("port", 3000)
    .set("ssl", false)
    .build({ host: "0.0.0.0", port: 80, ssl: true, timeout: 30, maxRetries: 3 });

console.log("Config:", JSON.stringify(config));

// Step 5: Generic Repository
class InMemoryRepository<T extends { id: number }> {
    protected store = new Map<number, T>();
    private nextId = 1;

    create(data: Omit<T, "id">): T {
        const item = { ...data, id: this.nextId++ } as T;
        this.store.set(item.id, item);
        return item;
    }

    findById(id: number): T | undefined { return this.store.get(id); }
    findAll(): T[] { return [...this.store.values()]; }
    delete(id: number): boolean { return this.store.delete(id); }
    count(): number { return this.store.size; }
}

interface Product { id: number; name: string; price: number; }
const repo = new InMemoryRepository<Product>();
repo.create({ name: "Surface Pro", price: 864 });
repo.create({ name: "Surface Pen", price: 49.99 });
console.log("Products:", repo.findAll().map(p => p.name).join(", "));
console.log("Count:", repo.count());

// Step 6: Generic Middleware
type Handler<C> = (ctx: C, next: () => Promise<void>) => Promise<void>;

class Pipeline<C> {
    private middlewares: Handler<C>[] = [];

    use(fn: Handler<C>): this { this.middlewares.push(fn); return this; }

    async run(ctx: C): Promise<void> {
        let index = 0;
        const next = async (): Promise<void> => {
            if (index < this.middlewares.length) await this.middlewares[index++](ctx, next);
        };
        await next();
    }
}

interface RequestContext { path: string; user?: string; log: string[] }

const app = new Pipeline<RequestContext>()
    .use(async (ctx, next) => { ctx.log.push("auth"); await next(); })
    .use(async (ctx, next) => { ctx.log.push("rate-limit"); await next(); })
    .use(async (ctx, next) => { ctx.log.push(`handle: ${ctx.path}`); await next(); });

(async () => {
    const ctx: RequestContext = { path: "/products", log: [] };
    await app.run(ctx);
    console.log("Middleware chain:", ctx.log.join(" → "));
})();

// Step 7: Generic EventEmitter
class TypedEmitter<Events extends Record<string, unknown[]>> {
    private listeners = new Map<keyof Events, ((...args: unknown[]) => void)[]>();

    on<E extends keyof Events>(event: E, listener: (...args: Events[E]) => void): void {
        if (!this.listeners.has(event)) this.listeners.set(event, []);
        this.listeners.get(event)!.push(listener as (...args: unknown[]) => void);
    }

    emit<E extends keyof Events>(event: E, ...args: Events[E]): void {
        this.listeners.get(event)?.forEach(fn => fn(...args));
    }
}

type ShopEvents = {
    "product:created": [product: Product];
    "order:placed": [orderId: number, total: number];
    "stock:low": [productId: number, stock: number];
};

const emitter = new TypedEmitter<ShopEvents>();
emitter.on("product:created", p => console.log("New product:", p.name));
emitter.on("order:placed", (id, total) => console.log(`Order #${id}: $${total}`));
emitter.emit("product:created", { id: 1, name: "Surface Pro", price: 864 });
emitter.emit("order:placed", 1001, 933.12);

// Step 8: Capstone — Generic Cache with TTL
class TTLCache<K, V> {
    private cache = new Map<K, { value: V; expires: number }>();

    constructor(private defaultTTL: number = 60_000) {}

    set(key: K, value: V, ttl: number = this.defaultTTL): void {
        this.cache.set(key, { value, expires: Date.now() + ttl });
    }

    get(key: K): V | undefined {
        const entry = this.cache.get(key);
        if (!entry) return undefined;
        if (Date.now() > entry.expires) { this.cache.delete(key); return undefined; }
        return entry.value;
    }

    has(key: K): boolean { return this.get(key) !== undefined; }
    delete(key: K): void { this.cache.delete(key); }
    get size(): number {
        this.evict();
        return this.cache.size;
    }

    private evict(): void {
        const now = Date.now();
        for (const [k, v] of this.cache) if (now > v.expires) this.cache.delete(k);
    }
}

const productCache = new TTLCache<number, Product>(5000);
productCache.set(1, { id: 1, name: "Surface Pro", price: 864 });
productCache.set(2, { id: 2, name: "Surface Pen", price: 49 }, 1); // 1ms TTL

console.log("Cache hit:", productCache.get(1)?.name);
await new Promise(r => setTimeout(r, 10));
console.log("Expired:", productCache.get(2));
console.log("Cache size:", productCache.size);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
class Stack<T> {
    private items: T[] = [];
    push = (...items: T[]) => { this.items.push(...items); return this; };
    pop = (): T | undefined => this.items.pop();
    get top() { return this.items[this.items.length - 1]; }
    get size() { return this.items.length; }
}
const s = new Stack<number>();
s.push(1, 2, 3);
console.log('top:', s.top, 'size:', s.size);
console.log('pop:', s.pop(), s.pop());
"
```

> 💡 **Generic caches** (`TTLCache<K, V>`) are reusable for any key/value types — `TTLCache<string, User>` or `TTLCache<number, Product>`. The type parameters propagate through all methods, so `get()` returns `V | undefined` and TypeScript knows the exact type at each call site.

**📸 Verified Output:**
```
top: 3 size: 3
pop: 3 2
```

---

## Summary

Generics are TypeScript's superpower. You've covered constrained generics, `infer` for type extraction, `Optional<T>`, `Result<T,E>`, generic builders, repositories, middleware pipelines, typed event emitters, and a TTL cache. These patterns appear in every production TypeScript codebase.

## Further Reading
- [TypeScript Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)
- [Conditional Types](https://www.typescriptlang.org/docs/handbook/2/conditional-types.html)
