# Lab 2: Functions & Type Signatures

## Objective
Write typed functions with parameters, return types, overloads, generics, and higher-order functions. Understand arrow functions, optional/rest parameters, and function type signatures.

## Background
TypeScript's function types are its most powerful feature for eliminating bugs. Typed parameters catch wrong argument orders, optional parameters document intent, and generic functions work across types without sacrificing safety. TypeScript also supports function overloads — multiple signatures for one implementation.

## Time
25 minutes

## Prerequisites
- Lab 01 (Hello World)

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Function Types & Signatures

```typescript
// Named function
function add(a: number, b: number): number {
    return a + b;
}

// Arrow function
const multiply = (a: number, b: number): number => a * b;

// Function type — store in variable
type MathFn = (a: number, b: number) => number;
const subtract: MathFn = (a, b) => a - b;  // types inferred from MathFn

// Pass functions as arguments
function applyOp(a: number, b: number, op: MathFn): number {
    return op(a, b);
}

console.log(applyOp(10, 3, add));       // 13
console.log(applyOp(10, 3, multiply));  // 30
console.log(applyOp(10, 3, subtract));  // 7
console.log(applyOp(10, 3, (a, b) => a % b)); // 1

// Return function
function makeMultiplier(factor: number): (n: number) => number {
    return n => n * factor;
}

const triple = makeMultiplier(3);
const tenX   = makeMultiplier(10);
console.log(triple(7));   // 21
console.log(tenX(5));     // 50
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type MathFn = (a: number, b: number) => number;
const ops: Record<string, MathFn> = {
    add: (a, b) => a + b,
    mul: (a, b) => a * b,
    pow: (a, b) => a ** b,
};
Object.entries(ops).forEach(([name, fn]) => console.log(name + '(3,4) =', fn(3, 4)));
"
```

> 💡 **Function types** are just type annotations for functions: `(a: number, b: number) => number` describes any function that takes two numbers and returns a number. TypeScript uses structural typing — any function with this shape is assignable, regardless of what it's called.

**📸 Verified Output:**
```
add(3,4) = 7
mul(3,4) = 12
pow(3,4) = 81
```

---

### Step 2: Optional, Default & Rest Parameters

```typescript
// Optional parameter (?): may be undefined
function createTag(tag: string, content: string, className?: string): string {
    const cls = className ? ` class="${className}"` : "";
    return `<${tag}${cls}>${content}</${tag}>`;
}

console.log(createTag("p", "Hello"));
console.log(createTag("div", "World", "container"));

// Default parameter
function padLeft(s: string, width: number = 10, char: string = " "): string {
    return s.padStart(width, char);
}

console.log("|" + padLeft("hi") + "|");
console.log("|" + padLeft("hi", 8, "0") + "|");

// Rest parameters — variable argument count
function sum(...nums: number[]): number {
    return nums.reduce((a, b) => a + b, 0);
}

function joinWith(separator: string, ...parts: string[]): string {
    return parts.join(separator);
}

console.log(sum(1, 2, 3, 4, 5));            // 15
console.log(joinWith(" | ", "a", "b", "c")); // a | b | c

// Spread into function
const numbers = [10, 20, 30];
console.log(sum(...numbers));  // 60

// Destructured parameters
function formatPoint({ x, y }: { x: number; y: number }): string {
    return `(${x}, ${y})`;
}

console.log(formatPoint({ x: 3, y: 4 }));
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
function stats(...nums: number[]): { min: number; max: number; avg: number } {
    return {
        min: Math.min(...nums),
        max: Math.max(...nums),
        avg: nums.reduce((a, b) => a + b, 0) / nums.length,
    };
}
const r = stats(3, 1, 4, 1, 5, 9, 2, 6);
console.log('min:', r.min, 'max:', r.max, 'avg:', r.avg.toFixed(2));
"
```

> 💡 **Optional vs default:** `param?: string` means the caller may omit it (receives `undefined`). `param: string = "default"` means the caller may omit it (receives `"default"`). Prefer defaults over optional when a sensible default exists — it makes the function easier to call and the code cleaner.

**📸 Verified Output:**
```
min: 1 max: 9 avg: 3.88
```

---

### Step 3: Generics

```typescript
// Generic function — works for any type T
function identity<T>(value: T): T {
    return value;
}

console.log(identity(42));           // number
console.log(identity("hello"));      // string
console.log(identity([1, 2, 3]));   // number[]

// Generic with constraint
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
    return obj[key];
}

const user = { name: "Dr. Chen", age: 40, active: true };
console.log(getProperty(user, "name"));   // string
console.log(getProperty(user, "age"));    // number
// getProperty(user, "missing"); // Error: not a valid key

// Generic array utilities
function first<T>(arr: T[]): T | undefined {
    return arr[0];
}

function last<T>(arr: T[]): T | undefined {
    return arr[arr.length - 1];
}

function chunk<T>(arr: T[], size: number): T[][] {
    const result: T[][] = [];
    for (let i = 0; i < arr.length; i += size) {
        result.push(arr.slice(i, i + size));
    }
    return result;
}

console.log(first([10, 20, 30]));     // 10
console.log(last(["a", "b", "c"]));   // c
console.log(JSON.stringify(chunk([1,2,3,4,5,6,7], 3))); // [[1,2,3],[4,5,6],[7]]

// Generic interface
interface Box<T> {
    value: T;
    map<U>(fn: (val: T) => U): Box<U>;
}

function box<T>(value: T): Box<T> {
    return { value, map: fn => box(fn(value)) };
}

const result = box(5)
    .map(n => n * 2)     // Box<number>
    .map(n => `val=${n}`) // Box<string>
    .value;

console.log(result);  // val=10
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
function zip<A, B>(as: A[], bs: B[]): [A, B][] {
    return as.map((a, i) => [a, bs[i]] as [A, B]);
}
const names = ['Alice', 'Bob', 'Carol'];
const scores = [95, 87, 92];
zip(names, scores).forEach(([name, score]) => console.log(name + ': ' + score));
"
```

> 💡 **Generics let you write once, use for any type.** Without generics, you'd need `numberFirst`, `stringFirst`, `userFirst`, etc. With `first<T>`, one function works for all types while preserving type information. The type parameter `T` is inferred from the argument — you rarely need to write `first<number>(arr)` explicitly.

**📸 Verified Output:**
```
Alice: 95
Bob: 87
Carol: 92
```

---

### Step 4: Function Overloads

```typescript
// Overloads — multiple signatures, one implementation
function format(value: number): string;
function format(value: number, decimals: number): string;
function format(value: string): string;
function format(value: number | string, decimals?: number): string {
    if (typeof value === "string") return value.trim().toUpperCase();
    return value.toFixed(decimals ?? 0);
}

console.log(format(3.14159));      // "3"
console.log(format(3.14159, 2));   // "3.14"
console.log(format("  hello  ")); // "HELLO"

// Overloads for DOM-like query
function query(selector: string): Element | null;
function query(selector: string, all: true): Element[];
function query(selector: string, all?: true): Element | Element[] | null {
    // Simulated implementation
    if (all) return [];
    return null;
}

// Overloads with conditional return type
function parseValue(s: string): string;
function parseValue(n: number): number;
function parseValue(b: boolean): boolean;
function parseValue(input: string | number | boolean): string | number | boolean {
    if (typeof input === "string") return input.trim();
    if (typeof input === "number") return Math.round(input);
    return !input; // flip boolean
}

console.log(parseValue("  hello  ")); // "hello"
console.log(parseValue(3.7));         // 4
console.log(parseValue(true));        // false
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
function repeat(str: string, times: number): string;
function repeat(str: string): string;
function repeat(str: string, times: number = 2): string {
    return str.repeat(times);
}
console.log(repeat('ha'));
console.log(repeat('ho', 4));
"
```

> 💡 **The implementation signature is not visible to callers** — only the overload signatures are. The implementation signature must be compatible with all overloads (usually using union types). Keep overloads minimal — if the function has wildly different behavior per type, consider separate functions.

**📸 Verified Output:**
```
haha
hohohoho
```

---

### Step 5: Higher-Order Functions

```typescript
// Function composition
const pipe = <T>(...fns: ((x: T) => T)[]) => (x: T): T =>
    fns.reduce((v, f) => f(v), x);

const compose = <T>(...fns: ((x: T) => T)[]) => (x: T): T =>
    fns.reduceRight((v, f) => f(v), x);

const trim     = (s: string) => s.trim();
const lower    = (s: string) => s.toLowerCase();
const slug     = (s: string) => s.replace(/\s+/g, "-");
const noSpec   = (s: string) => s.replace(/[^a-z0-9-]/g, "");

const toSlug = pipe(trim, lower, slug, noSpec);

console.log(toSlug("  Hello, World! PHP & TypeScript  "));
console.log(toSlug("  Dr. Chen's TypeScript Lab #2  "));

// Currying
function curry<A, B, C>(fn: (a: A, b: B) => C): (a: A) => (b: B) => C {
    return a => b => fn(a, b);
}

const add = (a: number, b: number) => a + b;
const add5  = curry(add)(5);
const add10 = curry(add)(10);

console.log(add5(3));   // 8
console.log(add10(3));  // 13

// Memoize with generics
function memoize<T extends unknown[], R>(fn: (...args: T) => R): (...args: T) => R {
    const cache = new Map<string, R>();
    return (...args: T): R => {
        const key = JSON.stringify(args);
        if (!cache.has(key)) cache.set(key, fn(...args));
        return cache.get(key)!;
    };
}

const expensiveSquare = memoize((n: number) => {
    console.log(`  computing ${n}²`);
    return n * n;
});

console.log(expensiveSquare(7));  // computes
console.log(expensiveSquare(7));  // from cache
console.log(expensiveSquare(8));  // computes
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const pipe = (...fns: ((x: number) => number)[]) => (x: number) =>
    fns.reduce((v, f) => f(v), x);
const process = pipe(
    x => x * 2,
    x => x + 10,
    x => x ** 2,
);
console.log(process(5));  // (5*2+10)^2 = 400
"
```

> 💡 **TypeScript's generic `pipe`** preserves types through transformations. If the functions have different input/output types, you need a more complex variadic generic type (like fp-ts's `pipe`). For same-type pipelines (string → string), this pattern is clean and fully typed.

**📸 Verified Output:**
```
400
```

---

### Step 6: Async Functions

```typescript
// async/await with types
async function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchData(id: number): Promise<{ id: number; title: string }> {
    await delay(10); // simulate network
    return { id, title: `Item #${id}` };
}

async function fetchAll(ids: number[]): Promise<{ id: number; title: string }[]> {
    return Promise.all(ids.map(id => fetchData(id)));
}

// Type-safe error handling in async
async function safeFetch(id: number): Promise<{ data: { id: number; title: string } | null; error: string | null }> {
    try {
        const data = await fetchData(id);
        return { data, error: null };
    } catch (err) {
        return { data: null, error: err instanceof Error ? err.message : "Unknown error" };
    }
}

// Run async code
(async () => {
    const item = await fetchData(42);
    console.log("Single:", item.title);

    const items = await fetchAll([1, 2, 3]);
    console.log("All:", items.map(i => i.title).join(", "));

    const { data, error } = await safeFetch(99);
    console.log("Safe fetch:", data?.title ?? error);
})();
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
async function* range(start: number, end: number): AsyncGenerator<number> {
    for (let i = start; i <= end; i++) {
        await new Promise(r => setTimeout(r, 1));
        yield i;
    }
}
(async () => {
    const results: number[] = [];
    for await (const n of range(1, 5)) results.push(n);
    console.log(results.join(', '));
})();
"
```

> 💡 **`async` functions always return `Promise<T>`** — even if you write `return 42`, TypeScript infers `Promise<number>`. The `await` keyword unwraps the promise to get `T`. TypeScript tracks this automatically, so `const x = await fetchData(1)` has type `{ id: number; title: string }`, not `Promise<...>`.

**📸 Verified Output:**
```
1, 2, 3, 4, 5
```

---

### Step 7: Type Guards

```typescript
// Type guard — narrow types at runtime
function isString(value: unknown): value is string {
    return typeof value === "string";
}

function isNumber(value: unknown): value is number {
    return typeof value === "number";
}

// Custom type guard for objects
interface Cat { kind: "cat"; meow(): void; }
interface Dog { kind: "dog"; bark(): void; }
type Animal = Cat | Dog;

function isCat(animal: Animal): animal is Cat {
    return animal.kind === "cat";
}

const animals: Animal[] = [
    { kind: "cat", meow: () => console.log("Meow!") },
    { kind: "dog", bark: () => console.log("Woof!") },
    { kind: "cat", meow: () => console.log("Purr!") },
];

animals.forEach(a => {
    if (isCat(a)) a.meow();
    else          a.bark();
});

// Assertion functions
function assertIsString(val: unknown): asserts val is string {
    if (typeof val !== "string") throw new TypeError(`Expected string, got ${typeof val}`);
}

function processValue(val: unknown): string {
    assertIsString(val);
    return val.toUpperCase(); // TypeScript knows val is string here
}

console.log(processValue("hello"));
try { processValue(42); } catch (e) { console.log("Error:", (e as Error).message); }
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type Shape = { kind: 'circle'; r: number } | { kind: 'square'; s: number };
function area(shape: Shape): number {
    switch (shape.kind) {
        case 'circle': return Math.PI * shape.r ** 2;
        case 'square': return shape.s ** 2;
    }
}
const shapes: Shape[] = [{ kind: 'circle', r: 5 }, { kind: 'square', s: 4 }];
shapes.forEach(s => console.log(s.kind + ': ' + area(s).toFixed(2)));
"
```

> 💡 **`value is Type` return type** makes a function a type guard — after `if (isCat(animal))`, TypeScript narrows `animal`'s type to `Cat` in the if-branch and `Dog` in the else-branch. This is how TypeScript achieves safe type narrowing from union types without casting (`as`).

**📸 Verified Output:**
```
circle: 78.54
square: 16.00
```

---

### Step 8: Complete — Typed Pipeline

```typescript
type Result<T, E = Error> =
    | { ok: true; value: T }
    | { ok: false; error: E };

function ok<T>(value: T): Result<T> { return { ok: true, value }; }
function err<E extends Error>(error: E): Result<never, E> { return { ok: false, error }; }

function parseNumber(s: string): Result<number> {
    const n = parseFloat(s);
    return isNaN(n) ? err(new Error(`Not a number: '${s}'`)) : ok(n);
}

function divide(a: number, b: number): Result<number> {
    return b === 0 ? err(new Error("Division by zero")) : ok(a / b);
}

function sqrt(n: number): Result<number> {
    return n < 0 ? err(new Error(`Cannot sqrt negative: ${n}`)) : ok(Math.sqrt(n));
}

// Chain results (like Rust's ? operator)
function chain<T, U>(result: Result<T>, fn: (val: T) => Result<U>): Result<U> {
    return result.ok ? fn(result.value) : result;
}

function compute(aStr: string, bStr: string): Result<string> {
    const aResult = parseNumber(aStr);
    const bResult = parseNumber(bStr);
    if (!aResult.ok) return aResult;
    if (!bResult.ok) return bResult;

    return chain(
        chain(divide(aResult.value, bResult.value), sqrt),
        n => ok(n.toFixed(4))
    );
}

const testCases: [string, string][] = [
    ["16", "4"],    // √(16/4) = √4 = 2
    ["25", "0"],    // division by zero
    ["abc", "4"],   // parse error
    ["-16", "1"],   // negative sqrt... wait: -16/1 then sqrt
    ["100", "4"],   // √25 = 5
];

testCases.forEach(([a, b]) => {
    const result = compute(a, b);
    if (result.ok) console.log(`  √(${a}/${b}) = ${result.value}`);
    else           console.log(`  √(${a}/${b}) → Error: ${result.error.message}`);
});
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type Result<T> = { ok: true; value: T } | { ok: false; error: string };
const ok = <T>(v: T): Result<T> => ({ ok: true, value: v });
const err = (e: string): Result<never> => ({ ok: false, error: e });
const parse = (s: string): Result<number> => isNaN(+s) ? err('NaN: '+s) : ok(+s);
['3.14', 'abc', '42'].forEach(s => {
    const r = parse(s);
    console.log(s, '->', r.ok ? r.value : 'ERR: ' + r.error);
});
"
```

> 💡 **The Result type** makes errors explicit in the type system — callers must handle both `ok` and `error` cases. Compared to exceptions, Result types are visible in function signatures (`Result<number>` vs `number`) and force callers to handle errors at the call site. TypeScript's discriminated unions make this pattern ergonomic.

**📸 Verified Output:**
```
3.14 -> 3.14
abc -> ERR: NaN: abc
42 -> 42
```

---

## Summary

TypeScript's function system is expressive and type-safe. You've covered typed parameters, optional/default/rest args, generics, overloads, higher-order functions, async/await types, type guards, and the Result pattern. These skills make every function self-documenting and IDE-friendly.

## Further Reading
- [TypeScript Functions](https://www.typescriptlang.org/docs/handbook/2/functions.html)
- [Generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)
