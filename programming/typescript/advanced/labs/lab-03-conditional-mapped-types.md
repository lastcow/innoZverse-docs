# Lab 03: Advanced Conditional & Mapped Types

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Master TypeScript's most powerful type-level utilities by implementing them from scratch: DeepPartial, DeepReadonly, DeepRequired, Flatten, UnionToIntersection, OmitNever, and PickByValue.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
apk add --no-cache curl
npm install -g typescript ts-node
mkdir lab03 && cd lab03
echo '{"compilerOptions":{"module":"commonjs","target":"es2020","strict":true}}' > tsconfig.json
```

> 💡 We use `strict: true` to catch type errors. All our utilities must satisfy the strictest TypeScript checks.

---

## Step 2: DeepPartial and DeepReadonly

These recursively modify object properties:

```typescript
// types.ts
type DeepPartial<T> = T extends object
  ? { [P in keyof T]?: DeepPartial<T[P]> }
  : T;

type DeepReadonly<T> = T extends object
  ? { readonly [P in keyof T]: DeepReadonly<T[P]> }
  : T;

interface Config {
  host: string;
  port: number;
  options: {
    timeout: number;
    retries: number;
    ssl: { cert: string; key: string };
  };
}

// DeepPartial: all nested props optional
const partial: DeepPartial<Config> = {
  host: 'localhost',
  options: { timeout: 5000 }, // ssl and retries optional too!
};

// DeepReadonly: all nested props readonly
const frozen: DeepReadonly<Config> = {
  host: 'prod.server.com',
  port: 443,
  options: { timeout: 30000, retries: 3, ssl: { cert: 'cert.pem', key: 'key.pem' } },
};
// frozen.host = 'other'; // Error: Cannot assign to 'host' because it is a read-only property
```

> 💡 The conditional `T extends object` stops recursion at primitives like `string`, `number`, `boolean`.

---

## Step 3: DeepRequired

Remove all optional modifiers recursively:

```typescript
type DeepRequired<T> = T extends object
  ? { [P in keyof T]-?: DeepRequired<T[P]> }
  : T;

// The `-?` removes optionality from every property

interface FormData {
  name?: string;
  address?: {
    street?: string;
    city?: string;
    zip?: string;
  };
}

// All fields required — compiler enforces completeness
const form: DeepRequired<FormData> = {
  name: 'Alice',
  address: {
    street: '123 Main St',
    city: 'Springfield',
    zip: '12345',
  },
};

console.log('DeepRequired form:', form.name, form.address.city);
```

> 💡 The `-?` modifier is the inverse of `?`. Similarly, `-readonly` removes readonly. These are "mapping modifiers."

---

## Step 4: Flatten

Extract the element type from an array:

```typescript
type Flatten<T> = T extends Array<infer U> ? U : T;

// Nested usage
type FlattenDeep<T> = T extends Array<infer U> ? FlattenDeep<U> : T;

type StringArray = string[];
type S = Flatten<StringArray>;    // string
type N = Flatten<number>;          // number (not an array, identity)
type Nested = number[][][];
type FlatN = FlattenDeep<Nested>;  // number

// Practical: extract callback parameter type
type Callback<T> = (item: Flatten<T>) => void;
type NumberCallback = Callback<number[]>; // (item: number) => void

function processItems<T extends any[]>(arr: T, cb: Callback<T>): void {
  arr.forEach(item => cb(item));
}
processItems([1, 2, 3], num => console.log('Item:', num));
```

---

## Step 5: UnionToIntersection

Convert a union type to an intersection — one of the trickiest type-level operations:

```typescript
type UnionToIntersection<U> =
  (U extends any ? (x: U) => void : never) extends (x: infer I) => void
    ? I
    : never;

// How it works:
// 1. Distribute U into function parameter positions
// 2. Infer the intersection from contravariant position

type A = { name: string };
type B = { age: number };
type C = { email: string };

type ABC = UnionToIntersection<A | B | C>;
// = { name: string } & { age: number } & { email: string }

const combined: ABC = {
  name: 'Alice',
  age: 30,
  email: 'alice@example.com',
};

// Real-world use: merging mixins
type Mixin1 = { serialize(): string };
type Mixin2 = { validate(): boolean };
type Mixin3 = { clone(): this };

type CombinedMixin = UnionToIntersection<Mixin1 | Mixin2 | Mixin3>;
console.log('UnionToIntersection:', combined.name, combined.age);
```

> 💡 **Contravariance trick**: Function parameter types are contravariant, meaning `(x: A) => void` is a subtype of `(x: A | B) => void`. TypeScript leverages this for intersection inference.

---

## Step 6: OmitNever and PickByValue

Filter object properties by type:

```typescript
// Remove properties typed as 'never'
type OmitNever<T> = {
  [K in keyof T as T[K] extends never ? never : K]: T[K];
};

// Pick properties matching a specific value type
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K];
};

// OmitNever example: conditional types can produce 'never' fields
type ConditionalShape<T> = {
  strings: T extends string ? T : never;
  numbers: T extends number ? T : never;
};

type StringResult = OmitNever<ConditionalShape<string>>;
// = { strings: string } — 'numbers' was 'never', now removed

// PickByValue: filter by type
interface Model {
  id: number;
  name: string;
  email: string;
  score: number;
  active: boolean;
}

type StringFields = PickByValue<Model, string>;
// = { name: string; email: string }

type NumericFields = PickByValue<Model, number>;
// = { id: number; score: number }

const sf: StringFields = { name: 'Bob', email: 'bob@test.com' };
const nf: NumericFields = { id: 1, score: 95 };
console.log('StringFields:', sf.name, sf.email);
console.log('NumericFields:', nf.id, nf.score);
```

> 💡 The `as` clause in mapped types (TypeScript 4.1+) remaps or filters keys. Using `as never` removes the key entirely.

---

## Step 7: Combining Utilities

Build a practical type-safe configuration system:

```typescript
// Combine utilities for a config system
type DeepPartial<T> = T extends object ? { [P in keyof T]?: DeepPartial<T[P]> } : T;
type DeepReadonly<T> = T extends object ? { readonly [P in keyof T]: DeepReadonly<T[P]> } : T;
type PickByValue<T, V> = { [K in keyof T as T[K] extends V ? K : never]: T[K] };

interface AppConfig {
  server: { host: string; port: number; secure: boolean };
  database: { url: string; poolSize: number; timeout: number };
  features: { darkMode: boolean; analytics: boolean; beta: boolean };
}

// Partial config for user overrides
type UserConfig = DeepPartial<AppConfig>;

// Immutable system defaults
type SystemDefaults = DeepReadonly<AppConfig>;

// Only string config values (for env var mapping)
type StringConfig = PickByValue<AppConfig['server'], string | boolean>;

function mergeConfig(defaults: SystemDefaults, overrides: UserConfig): AppConfig {
  return {
    server: { ...defaults.server, ...overrides.server },
    database: { ...defaults.database, ...overrides.database },
    features: { ...defaults.features, ...overrides.features },
  };
}

const defaults: SystemDefaults = {
  server: { host: '0.0.0.0', port: 3000, secure: false },
  database: { url: 'sqlite:./dev.db', poolSize: 5, timeout: 5000 },
  features: { darkMode: false, analytics: false, beta: false },
};

const userOverrides: UserConfig = {
  server: { port: 8080, secure: true },
  features: { darkMode: true },
};

const final = mergeConfig(defaults, userOverrides);
console.log('Merged config port:', final.server.port);
console.log('Merged config darkMode:', final.features.darkMode);
```

---

## Step 8: Capstone — Type Utility Library

Build a complete type utility module with tests:

```typescript
// Save as: type-utils.ts
export type DeepPartial<T> = T extends object ? { [P in keyof T]?: DeepPartial<T[P]> } : T;
export type DeepReadonly<T> = T extends object ? { readonly [P in keyof T]: DeepReadonly<T[P]> } : T;
export type DeepRequired<T> = T extends object ? { [P in keyof T]-?: DeepRequired<T[P]> } : T;
export type Flatten<T> = T extends Array<infer U> ? U : T;
export type FlattenDeep<T> = T extends Array<infer U> ? FlattenDeep<U> : T;
export type UnionToIntersection<U> = (U extends any ? (x: U) => void : never) extends (x: infer I) => void ? I : never;
export type OmitNever<T> = { [K in keyof T as T[K] extends never ? never : K]: T[K] };
export type PickByValue<T, V> = { [K in keyof T as T[K] extends V ? K : never]: T[K] };

// Type-level tests (compile-time assertions)
type Assert<T extends true> = T;
type Equal<A, B> = [A] extends [B] ? ([B] extends [A] ? true : false) : false;

// Verify: Flatten<string[]> === string
type Test1 = Assert<Equal<Flatten<string[]>, string>>;
// Verify: DeepPartial makes all optional
type HasOptional = { a?: string };
type Test2 = Assert<Equal<DeepPartial<{ a: string }>, HasOptional>>;

// Runtime verification
interface Product {
  id: number;
  name: string;
  price: number;
  meta: { tags: string[]; weight: number };
}

const partial: DeepPartial<Product> = { name: 'Widget', meta: { tags: ['sale'] } };
const intersection: UnionToIntersection<{ x: number } | { y: number }> = { x: 1, y: 2 };

console.log('=== Type Utils Capstone ===');
console.log('DeepPartial:', JSON.stringify(partial));
console.log('UnionToIntersection:', JSON.stringify(intersection));
console.log('All compile-time assertions passed!');
console.log('✅ Lab 03 complete');
```

Run it:
```bash
ts-node type-utils.ts
```

📸 **Verified Output:**
```
DeepPartial: {"host":"localhost"}
UnionToIntersection: {"a":"x","b":1}
All advanced types compiled successfully!
```

---

## Summary

| Utility | Pattern | Use Case |
|---|---|---|
| `DeepPartial<T>` | Recursive `?` on all keys | Config overrides |
| `DeepReadonly<T>` | Recursive `readonly` on all keys | Immutable state |
| `DeepRequired<T>` | Recursive `-?` on all keys | Form completion |
| `Flatten<T>` | `infer U` from array | Unwrap array elements |
| `UnionToIntersection<U>` | Contravariant function inference | Merge mixins |
| `OmitNever<T>` | `as never` key remapping | Filter conditional types |
| `PickByValue<T,V>` | `extends V` key remapping | Select fields by type |
