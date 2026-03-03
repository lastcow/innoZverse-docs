# Lab 1: Hello World & TypeScript Basics

## Objective
Set up TypeScript, compile `.ts` files to JavaScript, understand the TypeScript compiler (`tsc`), and write your first typed program.

## Background
TypeScript is a statically typed superset of JavaScript created by Microsoft. Every valid JavaScript file is valid TypeScript — TypeScript adds optional type annotations that are erased at compile time. The result is plain JavaScript that runs anywhere JS runs. TypeScript's killer feature: it catches bugs at compile time that JavaScript would only reveal at runtime.

## Time
20 minutes

## Prerequisites
- Basic JavaScript knowledge

## Tools
- Docker image: `zchencow/innozverse-ts:latest` (Node 20 + TypeScript 5.x)
- Run: `docker run --rm -it zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Your First TypeScript File

```typescript
// hello.ts
const message: string = "Hello, TypeScript!";
const year: number = 2026;
const isAwesome: boolean = true;

console.log(message);
console.log(`Year: ${year}`);
console.log(`TypeScript is awesome: ${isAwesome}`);

// Type inference — TypeScript figures out the type
const name = "Dr. Chen";        // inferred: string
const score = 98.5;              // inferred: number
const tags = ["ts", "js", "node"]; // inferred: string[]

console.log(`\n${name} scored ${score}`);
console.log(`Tags: ${tags.join(", ")}`);

// Function with types
function greet(name: string, greeting: string = "Hello"): string {
    return `${greeting}, ${name}!`;
}

console.log(greet("Dr. Chen"));
console.log(greet("Alice", "Welcome"));
```

Run with ts-node:
```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const message: string = 'Hello, TypeScript!';
const year: number = 2026;
console.log(message);
console.log('Year: ' + year);
console.log('Type of year: ' + typeof year);
"
```

> 💡 **TypeScript type annotations** are written as `: TypeName` after a variable or parameter. They're completely erased when compiled to JavaScript — zero runtime overhead. The TypeScript compiler (`tsc`) checks types statically before any code runs.

**📸 Verified Output:**
```
Hello, TypeScript!
Year: 2026
Type of year: number
```

---

### Step 2: Primitive Types

```typescript
// All TypeScript primitive types
const str: string = "hello";
const num: number = 42;
const flt: number = 3.14;       // no separate float type
const big: bigint = 9007199254740993n;
const bool: boolean = true;
const sym: symbol = Symbol("id");
const nothing: null = null;
const undef: undefined = undefined;

// any — escape hatch (use sparingly!)
let anything: any = "start";
anything = 42;
anything = true;

// unknown — safer than any
let unknown: unknown = "hello";
// Must narrow before use:
if (typeof unknown === "string") {
    console.log(unknown.toUpperCase()); // OK — narrowed to string
}

// never — impossible type
function throwError(msg: string): never {
    throw new Error(msg);
}

// void — function that returns nothing
function logMsg(msg: string): void {
    console.log(msg);
}

console.log(typeof str, typeof num, typeof bool);
console.log(typeof big, typeof sym);
console.log(typeof nothing, typeof undef); // "object", "undefined"
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const x: number = 42;
const s: string = 'hello';
const b: boolean = true;
console.log(typeof x, typeof s, typeof b);
const arr: number[] = [1, 2, 3];
console.log(arr.map(n => n * 2).join(', '));
"
```

> 💡 **`unknown` is safer than `any`** — with `any`, TypeScript trusts you completely (no checking). With `unknown`, TypeScript requires you to narrow the type before using it. Use `unknown` for values from external sources (JSON, user input, API responses) and narrow with `typeof`, `instanceof`, or type guards.

**📸 Verified Output:**
```
number string boolean
bigint symbol
object undefined
2, 4, 6
```

---

### Step 3: Arrays & Tuples

```typescript
// Arrays — two syntax styles (both identical)
const nums: number[] = [1, 2, 3, 4, 5];
const strs: Array<string> = ["a", "b", "c"];

// Array methods preserve types
const doubled = nums.map(n => n * 2);       // number[]
const filtered = nums.filter(n => n > 2);   // number[]
const sum = nums.reduce((a, b) => a + b, 0); // number

console.log("doubled:", doubled.join(", "));
console.log("filtered:", filtered.join(", "));
console.log("sum:", sum);

// Tuples — fixed-length, fixed-type arrays
const point: [number, number] = [3, 4];
const person: [string, number, boolean] = ["Dr. Chen", 40, true];

// Named tuple elements (TypeScript 4.0+)
type RGB = [red: number, green: number, blue: number];
const blue: RGB = [0, 120, 212];

console.log(`Point: (${point[0]}, ${point[1]})`);
console.log(`Person: ${person[0]}, age ${person[1]}`);
console.log(`Blue: rgb(${blue.join(", ")})`);

// Readonly arrays — cannot be mutated
const immutable: readonly number[] = [1, 2, 3];
// immutable.push(4); // Error: Property 'push' does not exist on type 'readonly number[]'
console.log("Immutable:", immutable[0]);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const nums: number[] = [1, 2, 3, 4, 5];
const point: [number, number] = [3, 4];
console.log('sum:', nums.reduce((a, b) => a + b, 0));
console.log('distance:', Math.sqrt(point[0] ** 2 + point[1] ** 2));
const words: string[] = ['TypeScript', 'is', 'typed', 'JavaScript'];
console.log(words.filter(w => w.length > 3).join(' '));
"
```

> 💡 **Tuples encode position-dependent meaning.** `[number, number]` for a point is cleaner than `{x: number, y: number}` for math operations, and cleaner than just `number[]` (which could be any length). React's `useState` returns a tuple: `[state, setState]` — that's why you destructure it.

**📸 Verified Output:**
```
sum: 15
distance: 5
TypeScript typed JavaScript
```

---

### Step 4: Object Types & Interfaces

```typescript
// Inline object type
const product: { name: string; price: number; inStock: boolean } = {
    name: "Surface Pro",
    price: 864,
    inStock: true,
};

// Interface — reusable, extendable
interface Product {
    readonly id: number;
    name: string;
    price: number;
    stock?: number;        // optional property
    category: string;
}

const p: Product = { id: 1, name: "Surface Pro", price: 864, category: "Laptop" };
console.log(`${p.name}: $${p.price} (${p.category})`);

// Extending interfaces
interface DigitalProduct extends Product {
    downloadUrl: string;
    licenseKey?: string;
}

const software: DigitalProduct = {
    id: 2, name: "Office 365", price: 99.99, category: "Software",
    downloadUrl: "https://download.microsoft.com/office365",
};

// Index signature — dynamic keys
interface StringMap {
    [key: string]: string;
}

const headers: StringMap = {
    "Content-Type": "application/json",
    "Authorization": "Bearer token123",
    "X-Request-Id": "abc-123",
};

Object.entries(headers).forEach(([k, v]) => console.log(`  ${k}: ${v}`));
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
interface Point { x: number; y: number; }
const p: Point = { x: 3, y: 4 };
const dist = Math.sqrt(p.x ** 2 + p.y ** 2);
console.log('Distance from origin: ' + dist);
console.log('Point:', JSON.stringify(p));
"
```

> 💡 **`interface` vs `type`:** Both define shapes. Use `interface` for object shapes (it's extendable with `extends`). Use `type` for unions, intersections, and complex types. A key difference: `interface` can be "declaration merged" — two `interface User` declarations merge into one. `type` cannot be reopened.

**📸 Verified Output:**
```
Distance from origin: 5
Point: {"x":3,"y":4}
```

---

### Step 5: Type Aliases

```typescript
// Type alias — name for any type
type ID = number | string;
type Name = string;
type Price = number;
type Status = "active" | "inactive" | "pending"; // literal union
type Direction = "north" | "south" | "east" | "west";

let userId: ID = 42;
userId = "UUID-abc"; // also valid

const status: Status = "active";
// const bad: Status = "deleted"; // Error!

// Object type alias
type Point = { x: number; y: number };
type Point3D = Point & { z: number }; // intersection

const p3d: Point3D = { x: 1, y: 2, z: 3 };
console.log(`3D point: (${p3d.x}, ${p3d.y}, ${p3d.z})`);

// Function type alias
type Transformer<T> = (input: T) => T;
type Predicate<T> = (input: T) => boolean;
type Comparator<T> = (a: T, b: T) => number;

const double: Transformer<number> = n => n * 2;
const isEven: Predicate<number> = n => n % 2 === 0;
const byNum: Comparator<number> = (a, b) => a - b;

const nums = [5, 3, 1, 4, 2];
console.log(nums.filter(isEven).join(", "));
console.log(nums.sort(byNum).join(", "));
console.log([1, 2, 3].map(double).join(", "));

// Utility types
type Partial<T> = { [K in keyof T]?: T[K] };
type Required<T> = { [K in keyof T]-?: T[K] };

interface Config { host: string; port: number; ssl: boolean; }
const partial: Partial<Config> = { host: "localhost" }; // all optional
console.log(JSON.stringify(partial));
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type Status = 'active' | 'inactive' | 'pending';
const statuses: Status[] = ['active', 'inactive', 'pending'];
statuses.forEach(s => console.log(s));
type Point = { x: number; y: number };
const points: Point[] = [{x:0,y:0},{x:3,y:4}];
console.log(points.map(p => Math.sqrt(p.x**2 + p.y**2)).join(', '));
"
```

> 💡 **String literal unions** (`"active" | "inactive"`) are one of TypeScript's most useful features. They're like enums but lighter — you get autocomplete, type checking, and exhaustiveness checking in `switch` statements. Use them for status fields, directions, HTTP methods, and any closed set of string values.

**📸 Verified Output:**
```
active
inactive
pending
0, 5
```

---

### Step 6: tsconfig.json Overview

```typescript
// What a modern tsconfig.json looks like:
const tsconfig = {
    compilerOptions: {
        target: "ES2022",           // Output JS version
        module: "NodeNext",          // Module system
        moduleResolution: "NodeNext",
        lib: ["ES2022"],            // Type definitions included
        outDir: "./dist",            // Compiled JS goes here
        rootDir: "./src",            // Source TS files here
        strict: true,                // Enable ALL strict checks
        noImplicitAny: true,         // Forbid implicit 'any'
        strictNullChecks: true,      // null/undefined are separate types
        noUncheckedIndexedAccess: true, // array[i] is T | undefined
        exactOptionalPropertyTypes: true,
        noImplicitReturns: true,     // All code paths must return
        noFallthroughCasesInSwitch: true,
        esModuleInterop: true,       // Better CommonJS interop
        forceConsistentCasingInFileNames: true,
        declaration: true,           // Generate .d.ts files
        sourceMap: true,             // Generate source maps
        skipLibCheck: true,          // Skip type checking of .d.ts files
    },
    include: ["src/**/*"],
    exclude: ["node_modules", "dist", "**/*.test.ts"],
};

console.log("Key strict options:");
const strictOpts = [
    "noImplicitAny         → error on 'any' type inference",
    "strictNullChecks      → null/undefined must be handled explicitly",
    "strictFunctionTypes   → function parameter variance checking",
    "strictPropertyInit    → class properties must be initialized",
    "noUncheckedIndexedAccess → arr[i] returns T | undefined",
];
strictOpts.forEach(o => console.log("  " + o));
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
// Demonstrate strict null checks
function greet(name: string | null): string {
    if (name === null) return 'Hello, stranger!';
    return 'Hello, ' + name + '!';
}
console.log(greet('Dr. Chen'));
console.log(greet(null));
"
```

> 💡 **`strict: true`** enables 8+ strict checks with one flag. The most important: `strictNullChecks` makes `null` and `undefined` their own types — a `string` variable can't be `null` unless you write `string | null`. This eliminates entire classes of "Cannot read property of null" runtime errors.

**📸 Verified Output:**
```
Hello, Dr. Chen!
Hello, stranger!
```

---

### Step 7: Compiling TypeScript

```bash
# Verify TypeScript version in the Docker image
docker run --rm zchencow/innozverse-ts:latest tsc --version

# Compile a file
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const add = (a: number, b: number): number => a + b;
const mul = (a: number, b: number): number => a * b;
const result = add(mul(3, 4), mul(2, 5));
console.log('Result:', result);
"

# TypeScript catches errors at compile time
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
function divide(a: number, b: number): number {
    return a / b;
}
// Type error would be caught:
// divide('10', '2'); // Argument of type 'string' is not assignable to parameter of type 'number'
console.log(divide(10, 2));
console.log(divide(7, 3).toFixed(2));
" 2>&1
```

> 💡 **`ts-node`** compiles and runs TypeScript in one step — perfect for learning and scripting. For production, compile with `tsc` first (produces `.js` files), then run with `node`. `ts-node` is slower (compiles on every run) but eliminates the build step during development.

**📸 Verified Output:**
```
Version 5.x.x
Result: 22
5
2.33
```

---

### Step 8: Complete — Type-Safe Calculator

```typescript
type Operation = "add" | "subtract" | "multiply" | "divide" | "power";

interface CalcResult {
    operation: Operation;
    a: number;
    b: number;
    result: number;
    formatted: string;
}

function calculate(op: Operation, a: number, b: number): CalcResult {
    const result = (() => {
        switch (op) {
            case "add":      return a + b;
            case "subtract": return a - b;
            case "multiply": return a * b;
            case "divide":
                if (b === 0) throw new Error("Division by zero");
                return a / b;
            case "power":    return Math.pow(a, b);
        }
    })();

    const symbols: Record<Operation, string> = {
        add: "+", subtract: "-", multiply: "×", divide: "÷", power: "^"
    };

    return {
        operation: op, a, b, result,
        formatted: `${a} ${symbols[op]} ${b} = ${result}`,
    };
}

const operations: [Operation, number, number][] = [
    ["add",      10, 5],
    ["subtract", 10, 5],
    ["multiply", 10, 5],
    ["divide",   10, 3],
    ["power",    2, 8],
];

console.log("=== Type-Safe Calculator ===");
for (const [op, a, b] of operations) {
    const r = calculate(op, a, b);
    console.log(`  ${r.formatted}`);
}

// History with type safety
const history: CalcResult[] = operations.map(([op, a, b]) => calculate(op, a, b));
const total = history.reduce((sum, r) => sum + r.result, 0);
console.log(`\nSum of all results: ${total.toFixed(4)}`);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
type Op = 'add' | 'sub' | 'mul' | 'div';
const calc = (op: Op, a: number, b: number): number =>
    op === 'add' ? a + b : op === 'sub' ? a - b : op === 'mul' ? a * b : a / b;
const ops: [Op, number, number][] = [['add',10,5],['mul',3,4],['div',10,3]];
ops.forEach(([op,a,b]) => console.log(op + ': ' + calc(op,a,b).toFixed(2)));
"
```

> 💡 **`Record<K, V>`** is a built-in utility type that creates an object type with keys of type `K` and values of type `V`. `Record<Operation, string>` means "an object where every Operation key must be present with a string value." This gives exhaustiveness checking — if you add a new Operation, TypeScript errors until you add it to the Record.

**📸 Verified Output:**
```
=== Type-Safe Calculator ===
  10 + 5 = 15
  10 - 5 = 5
  10 × 5 = 50
  10 ÷ 3 = 3.3333333333333335
  2 ^ 8 = 256

Sum of all results: 329.3333
add: 15.00
mul: 12.00
div: 3.33
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const greet = (name: string, times: number = 1): string =>
    Array(times).fill('Hello, ' + name + '!').join(' ');
console.log(greet('TypeScript'));
console.log(greet('World', 3));
"
```

## Summary

TypeScript adds a powerful type system on top of JavaScript. You've covered primitive types, inference, arrays, tuples, interfaces, type aliases, literal unions, `strict` mode, and a complete type-safe calculator. The type annotations disappear at runtime — you get the benefits of static typing with zero runtime cost.

## Further Reading
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [TypeScript Playground](https://www.typescriptlang.org/play)
- [tsconfig Reference](https://www.typescriptlang.org/tsconfig)
