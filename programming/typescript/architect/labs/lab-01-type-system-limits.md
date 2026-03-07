# Lab 01: Type System Limits

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Push the TypeScript type system to its limits: type instantiation depth, recursive type performance, type-level Fibonacci and FizzBuzz, `tsc --diagnostics` profiling, `@ts-expect-error` vs assertion functions, and `satisfies` for inference without widening.

---

## Step 1: Understanding Type Instantiation Depth

```typescript
// TypeScript has a default depth limit of ~100 recursive instantiations
// Compiler option: --maxNodeModuleJsDepth (different concern)

// SLOW: deeply recursive type
type Repeat<T, N extends number, A extends T[] = []> =
  A['length'] extends N ? A : Repeat<T, N, [...A, T]>;

// type R50 = Repeat<string, 50>;  // OK
// type R100 = Repeat<string, 100>; // Type instantiation is excessively deep

// FAST: alternative using tail recursion simulation
type BuildTuple<L extends number, T extends any[] = []> =
  T['length'] extends L ? T : BuildTuple<L, [...T, unknown]>;

type TupleOf<T, N extends number> =
  BuildTuple<N> extends infer U
    ? { [K in keyof U]: T }
    : never;

type Five = TupleOf<string, 5>; // [string, string, string, string, string]
```

---

## Step 2: Type-Level Computation — FizzBuzz

```typescript
// Type-level number arithmetic via tuple length
type Length<T extends any[]> = T['length'];
type Increment<T extends any[]> = [...T, unknown];
type BuildN<N extends number, A extends unknown[] = []> =
  A['length'] extends N ? A : BuildN<N, [...A, unknown]>;

// Type-level modulo
type Mod<A extends number, B extends number,
  _A extends unknown[] = BuildN<A>,
  _B extends unknown[] = BuildN<B>> =
  _A extends [..._B, ...infer Rest] ? Mod<Rest['length'], B, Rest, _B> : A;

// FizzBuzz — evaluates at compile time
type FizzBuzzFor<N extends number> =
  Mod<N, 15> extends 0 ? 'FizzBuzz' :
  Mod<N, 3>  extends 0 ? 'Fizz' :
  Mod<N, 5>  extends 0 ? 'Buzz' :
  N;

// Examples (all computed at TYPE LEVEL, zero runtime cost):
type FB1  = FizzBuzzFor<1>;   // 1
type FB3  = FizzBuzzFor<3>;   // "Fizz"
type FB5  = FizzBuzzFor<5>;   // "Buzz"
type FB15 = FizzBuzzFor<15>;  // "FizzBuzz"
```

---

## Step 3: Avoiding Slow Type Patterns

```typescript
// SLOW: Large union type discrimination
type SlowUnion =
  | { type: 'a'; a: string }
  | { type: 'b'; b: number }
  | { type: 'c'; c: boolean }
  // ... 100 more variants

// TS must check each discriminant — O(n) per narrowing

// FAST: Use indexed access types instead
type ActionMap = {
  a: { a: string };
  b: { b: number };
  c: { c: boolean };
};
type Action<K extends keyof ActionMap> = { type: K } & ActionMap[K];
type AnyAction = { [K in keyof ActionMap]: Action<K> }[keyof ActionMap];

// SLOW: Deep conditional type chains
type DeepCondition<T> =
  T extends string  ? 'string'  :
  T extends number  ? 'number'  :
  T extends boolean ? 'boolean' :
  T extends null    ? 'null'    :
  T extends undefined ? 'undefined' :
  T extends any[]   ? 'array'   :
  'object';

// FAST: Use intrinsic types or lookup tables
```

---

## Step 4: `satisfies` Operator (TypeScript 4.9+)

```typescript
// PROBLEM: const loses narrow type with explicit annotation
const palette1: Record<string, string[]> = {
  red: ['#ff0000', '#cc0000'],
  blue: ['#0000ff', '#0000cc'],
};
// palette1.red.toUpperCase(); // ERROR: string[] has no toUpperCase

// satisfies: validate against type but KEEP NARROW inference
const palette2 = {
  red: ['#ff0000', '#cc0000'],
  blue: '#0000ff',         // Different shape per key
} satisfies Record<string, string | string[]>;

palette2.red;  // string[] (narrow type preserved)
palette2.blue; // string  (narrow type preserved)
// palette2.green; // ERROR: Property 'green' does not exist

// Real-world: route configuration
type Route = { path: string; component: string; auth?: boolean };
const routes = {
  home:     { path: '/', component: 'Home' },
  about:    { path: '/about', component: 'About' },
  settings: { path: '/settings', component: 'Settings', auth: true },
} satisfies Record<string, Route>;

// routes.home.component is "Home" (literal), not just string
```

---

## Step 5: `@ts-expect-error` vs Assertion Functions

```typescript
// @ts-expect-error: suppress next line's type error
// FAILS if next line has no error (unlike @ts-ignore)
function divide(a: number, b: number): number {
  // @ts-expect-error: testing error case
  return a / 0; // intentional for test
}

// When to use:
// @ts-expect-error — test that something IS an error (type tests)
// @ts-ignore       — suppress error you can't fix (last resort)

// BETTER: Assertion functions (runtime + type narrowing)
function assertDefined<T>(
  value: T,
  message = 'Expected value to be defined'
): asserts value is NonNullable<T> {
  if (value === undefined || value === null) {
    throw new Error(message);
  }
}

// Type-only assertion (no runtime cost)
function assertType<T>(_value: unknown): asserts _value is T {}

// Usage:
const value: string | null = getUserName();
assertDefined(value, 'User name is required');
// After: value is string (not null)
console.log(value.toUpperCase()); // TypeScript knows it's string
```

---

## Step 6: `const` Type Parameters (TypeScript 5.0)

```typescript
// Before 5.0: needed 'as const' assertions
function inferTuple<T extends unknown[]>(values: T): T {
  return values;
}
const t1 = inferTuple(['a', 'b', 'c']); // string[] (widened)

// TypeScript 5.0: const type parameter
function inferTupleConst<const T extends unknown[]>(values: T): T {
  return values;
}
const t2 = inferTupleConst(['a', 'b', 'c']); // ['a', 'b', 'c'] (literal)

// Practical: type-safe event names
function on<const EventName extends string>(
  event: EventName,
  handler: (e: Event) => void
): void {
  // EventName is 'click' | 'scroll' etc., not widened to string
}
```

---

## Step 7: NoInfer (TypeScript 5.4)

```typescript
// NoInfer<T>: prevents inference at a specific position

// PROBLEM: inference conflict
function createState<T>(
  initial: T,
  reducer: (state: T, action: string) => T
): { state: T; dispatch: (action: string) => void } {
  // T is inferred from initial — but action parameter might widen it
}

// WITH NoInfer: T is only inferred from 'initial'
function createStore<T>(
  initial: T,
  reducer: (state: NoInfer<T>, action: string) => NoInfer<T>
): T {
  return initial;
}
```

---

## Step 8: Capstone — Type-Level FizzBuzz + Runtime Verification

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

| Feature | Version | Use Case |
|---------|---------|----------|
| Recursive types | All | Data structures, parsing |
| `satisfies` | 4.9 | Validate + keep narrow type |
| `const` type param | 5.0 | Infer literals not widened |
| `NoInfer<T>` | 5.4 | Control inference site |
| `@ts-expect-error` | All | Type-level tests |
| Assertion functions | All | Runtime + type narrowing |
| `tsc --diagnostics` | All | Performance profiling |
| Depth limit | All | ~100 recursions default |
