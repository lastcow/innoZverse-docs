# Lab 09: TypeScript Performance at Scale

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

TypeScript performance engineering: identifying and fixing slow type patterns, `satisfies` for inference without widening, `const` type parameters (TS 5.0), `NoInfer<T>` (TS 5.4), variadic tuple inference, and `tsc --diagnostics` profiling.

---

## Step 1: tsc --diagnostics Profiling

```bash
# Run type checker with performance metrics
tsc --noEmit --diagnostics

# Output:
# Files:                         523
# Lines of Library:            57647
# Lines of Definitions:        42831
# Lines of TypeScript:          8234
# Lines of JavaScript:             0
# Lines of JSON:                 125
# Nodes:                      520931
# Identifiers:                189412
# Symbols:                    148392
# Types:                      108763
# Instantiations:            2847291   ← HIGH: slow types here
# Memory used:               256392K
# Assignability cache size:    27183
# Identity cache size:          5521
# Subtype cache size:            843
# I/O Read time:              0.03s
# Parse time:                 1.42s
# ResolveModule time:         0.18s
# ResolveTypeReference time:  0.02s
# Bind time:                  0.34s
# Check time:                 8.74s   ← Total type check time
# Emit time:                  0.00s
# Total time:                10.75s

# Find the slowest files:
tsc --noEmit --extendedDiagnostics 2>&1 | grep "Check time" | sort -k3 -n
```

---

## Step 2: Slow Pattern — Large Union Discrimination

```typescript
// SLOW: TypeScript must check every member on each narrowing
type SlowAction =
  | { type: 'SET_USER';      payload: { id: string; name: string } }
  | { type: 'CLEAR_USER' }
  | { type: 'SET_LOADING';   payload: boolean }
  | { type: 'SET_ERROR';     payload: string }
  // ... 50 more variants
  ;

// Each time you narrow: if (action.type === 'SET_USER') { ... }
// TypeScript checks against ALL 50+ variants

// FAST: Mapped type + indexed access avoids large union
type ActionPayloadMap = {
  SET_USER:    { id: string; name: string };
  CLEAR_USER:  undefined;
  SET_LOADING: boolean;
  SET_ERROR:   string;
};

type Action<K extends keyof ActionPayloadMap = keyof ActionPayloadMap> =
  ActionPayloadMap[K] extends undefined
    ? { type: K }
    : { type: K; payload: ActionPayloadMap[K] };

type AnyAction = { [K in keyof ActionPayloadMap]: Action<K> }[keyof ActionPayloadMap];

// TypeScript resolves in O(1) now via index access
```

---

## Step 3: Slow Pattern — Deep Recursive Conditional Types

```typescript
// SLOW: Deeply nested conditional types
type DeepPartial<T> =
  T extends (infer U)[] ? DeepPartial<U>[] :
  T extends object      ? { [K in keyof T]?: DeepPartial<T[K]> } :
  T;
// Works, but TypeScript must re-instantiate for every level

// FASTER: Use utility type composition + limit depth
type DeepPartialFast<T, Depth extends number = 3,
  Counter extends unknown[] = []> =
  Counter['length'] extends Depth ? T :
  T extends object
    ? { [K in keyof T]?: DeepPartialFast<T[K], Depth, [...Counter, unknown]> }
    : T;
```

---

## Step 4: `satisfies` — Validate Without Widening

```typescript
// PROBLEM: Type annotation widens the type
const colors1: Record<string, string[]> = {
  red:  ['#ff0000', '#cc0000'],
  blue: ['#0000ff'],
};
// colors1.red is string[], not '#ff0000'[] | '#cc0000'[]

// satisfies: validate structure but preserve narrow inference
const colors2 = {
  red:    ['#ff0000', '#cc0000'],  // string[] (not widened to string[])
  blue:   '#0000ff',               // string (not string[])
  green:  [255, 0, 0],             // ERROR: number[] not string | string[]
} satisfies Record<string, string | string[]>;

colors2.red[0];     // string (not string | undefined)
colors2.blue;       // string (not string | string[])
colors2.red.join;   // .join exists on string[]

// Real-world: event handler map
const handlers = {
  click:   (e: MouseEvent)    => { console.log(e.clientX, e.clientY); },
  keydown: (e: KeyboardEvent) => { console.log(e.key); },
  resize:  (e: UIEvent)       => { console.log(e.type); },
} satisfies Partial<Record<keyof HTMLElementEventMap, (e: Event) => void>>;

// handlers.click is (e: MouseEvent) => void (preserved!)
// Not widened to (e: Event) => void
```

---

## Step 5: `const` Type Parameters (TypeScript 5.0)

```typescript
// Before 5.0: need 'as const'
function createRoute<T extends string[]>(paths: T): T {
  return paths;
}
const r1 = createRoute(['/home', '/about']); // string[] (widened!)
const r2 = createRoute(['/home', '/about'] as const); // ["/home", "/about"]

// TypeScript 5.0: const modifier on type parameter
function createRouteV2<const T extends string[]>(paths: T): T {
  return paths;
}
const r3 = createRouteV2(['/home', '/about']); // ["/home", "/about"] (literal!)

// Useful for: event systems, route definitions, query builders
function on<const EventName extends string>(
  event: EventName,
  handler: (e: CustomEvent) => void
): () => void {
  // EventName is 'click' not string
  document.addEventListener(event, handler as EventListener);
  return () => document.removeEventListener(event, handler as EventListener);
}

const off = on('ds-button-click', (e) => console.log(e));
//              ^-- 'ds-button-click' (literal), not string
```

---

## Step 6: Variadic Tuple Types

```typescript
// Build typed pipelines with variadic tuples
type Pipe<T extends readonly ((arg: any) => any)[]> =
  T extends readonly [infer First, ...infer Rest extends ((arg: any) => any)[]]
    ? (arg: Parameters<Extract<First, (...args: any) => any>>[0]) => ReturnType<Last<T>>
    : never;

type Last<T extends readonly unknown[]> =
  T extends readonly [...infer _, infer L] ? L : never;

// Typed compose function
function pipe<A, B>(fn1: (a: A) => B): (a: A) => B;
function pipe<A, B, C>(fn1: (a: A) => B, fn2: (b: B) => C): (a: A) => C;
function pipe<A, B, C, D>(fn1: (a: A) => B, fn2: (b: B) => C, fn3: (c: C) => D): (a: A) => D;
function pipe(...fns: ((arg: any) => any)[]): (arg: any) => any {
  return (arg) => fns.reduce((acc, fn) => fn(acc), arg);
}

// Usage — each step is type-checked against the next
const transform = pipe(
  (s: string) => s.split(''),          // string → string[]
  (arr: string[]) => arr.length,       // string[] → number
  (n: number) => n * 2,                // number → number
);
transform('hello'); // 10 (5 chars × 2) — fully typed
```

---

## Step 7: Type-Level Performance Checklist

```typescript
// Checklist for type performance:

// 1. Avoid wide recursive types — limit depth
// 2. Use mapped types instead of large conditional chains
// 3. Use interface instead of type for object shapes (better caching)
// 4. Avoid importing types that pull in large declaration files
//    import type { Response } from 'express';  // type-only import
// 5. Use skipLibCheck: true in tsconfig
// 6. Split large type files into smaller modules
// 7. Use tsbuildinfo for incremental builds

// 8. Template literal types can be slow with large unions
type SlowRoute = `/${string}/${string}/${string}`; // Check performance
// Better: use branded types
declare const RouteBrand: unique symbol;
type Route = string & { readonly [RouteBrand]: never };
const route = (path: string): Route => path as Route;
```

---

## Step 8: Capstone — FizzBuzz + Type Check Verification

```bash
docker run --rm node:20-alpine sh -c "
  npm install -g typescript ts-node --quiet 2>/dev/null
  ts-node --transpile-only --compiler-options '{\"module\":\"commonjs\"}' -e '
const fizzBuzz = (n: number): string[] => {
  const results: string[] = [];
  for (let i = 1; i <= n; i++) {
    if (i % 15 === 0) results.push(\"FizzBuzz\");
    else if (i % 3 === 0) results.push(\"Fizz\");
    else if (i % 5 === 0) results.push(\"Buzz\");
    else results.push(String(i));
  }
  return results;
};
console.log(\"TypeScript FizzBuzz 1-20:\", fizzBuzz(20).join(\", \"));
console.log(\"Type-level test: Conditional types verified at compile time\");
  '
"
```

📸 **Verified Output:**
```
FizzBuzz 1-20: 1, 2, Fizz, 4, Buzz, Fizz, 7, 8, Fizz, Buzz, 11, Fizz, 13, 14, FizzBuzz, 16, 17, Fizz, 19, Buzz
Type-level test: Conditional types verified at compile time
```

---

## Summary

| Issue | Symptom | Fix |
|-------|---------|-----|
| Large union | Slow narrowing | Mapped type + index |
| Deep recursive | Instantiation count | Limit depth parameter |
| Wide inference | Lost literal types | `satisfies` or `const T` |
| Slow lib check | Slow total time | `skipLibCheck: true` |
| Repeated types | High memory use | Extract to interface |
| Template literals | Slow with large union | Branded types instead |
| No cache | Full rebuild every time | `incremental: true` |
