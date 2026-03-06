# Lab 03: Advanced Interfaces & Types

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Interface vs type alias, declaration merging, index signatures, mapped types, conditional types, and the `infer` keyword.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab03 && cd /lab03
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true
  }
}
EOF
```

---

## Step 2: Interface vs Type Alias

```typescript
// Both work for object shapes
interface UserInterface {
  id: number;
  name: string;
  greet(): string;
}

type UserType = {
  id: number;
  name: string;
  greet(): string;
};

// Key differences:
// 1. Interfaces can be extended (declaration merging)
// 2. Type aliases can use unions/intersections/mapped types
// 3. Interfaces are always named (better error messages for complex objects)

// Extend interface
interface AdminInterface extends UserInterface {
  role: 'admin';
  permissions: string[];
}

// Type alias intersection
type AdminType = UserType & { role: 'admin'; permissions: string[] };
```

---

## Step 3: Declaration Merging

```typescript
// Interfaces with the same name MERGE
interface Request {
  url: string;
  method: string;
}

interface Request {
  headers: Record<string, string>;
  body?: unknown;
}
// Now Request has url, method, headers, body

// Useful for module augmentation:
interface Window {
  myApp: { version: string };
}
// (In browser context, adds to the global Window type)

// Merging with function overloads
interface Formatter {
  (val: string): string;
  (val: number): string;
}
```

> 💡 Type aliases cannot merge — declaring `type X = ...` twice is an error. Interfaces can.

---

## Step 4: Index Signatures

```typescript
// Dynamic keys with known value types
interface StringMap {
  [key: string]: string;
}

interface NumberCache {
  [key: string]: number;
  count: number;  // known key — must match value type
}

// Mixed index + known properties
interface Config {
  host: string;
  port: number;
  [extra: string]: string | number;  // extras must match union
}

const m: StringMap = { a: 'hello', b: 'world' };
console.log(m['a']);  // hello

// Template literal index types (TS 4.4+)
interface EventRecord {
  [K: `on${string}`]: (event: Event) => void;
}
```

---

## Step 5: Mapped Types

```typescript
type User = { id: number; name: string; email: string };

// Basic mapped type
type Readonly2<T> = { readonly [K in keyof T]: T[K] };
type Optional<T>  = { [K in keyof T]?: T[K] };
type Nullable<T>  = { [K in keyof T]: T[K] | null };

// Key remapping with as
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};
type Setters<T> = {
  [K in keyof T as `set${Capitalize<string & K>}`]: (val: T[K]) => void;
};

type UserGetters = Getters<User>;
// { getId: () => number; getName: () => string; getEmail: () => string }

// Filter keys with conditional
type OnlyStrings<T> = {
  [K in keyof T as T[K] extends string ? K : never]: T[K];
};
type StringFields = OnlyStrings<User>;  // { name: string; email: string }

const u: Optional<User> = { name: 'Alice' };  // id and email optional
console.log(JSON.stringify(u));
```

---

## Step 6: Conditional Types

```typescript
// Basic conditional
type IsArray<T> = T extends any[] ? true : false;
type IsString<T> = T extends string ? true : false;

type A = IsArray<number[]>;  // true
type B = IsArray<string>;    // false

// Distributed conditional types
type ToArray<T> = T extends any ? T[] : never;
type Result = ToArray<string | number>;  // string[] | number[]

// Non-distributed version
type ToArrayND<T> = [T] extends [any] ? T[] : never;
type Result2 = ToArrayND<string | number>;  // (string | number)[]

// Conditional with extends
type UnwrapPromise<T> = T extends Promise<infer R> ? R : T;
type StringResult = UnwrapPromise<Promise<string>>;  // string
type Plain = UnwrapPromise<number>;                  // number

async function fetchString(): Promise<string> { return 'hello'; }
type FetchResult = UnwrapPromise<ReturnType<typeof fetchString>>;  // string
```

---

## Step 7: The `infer` Keyword

```typescript
// infer captures a type within extends
type ReturnType2<T> = T extends (...args: any[]) => infer R ? R : never;
type FirstArg<T> = T extends (first: infer F, ...rest: any[]) => any ? F : never;
type ArrayElement<T> = T extends Array<infer E> ? E : never;
type PromiseValue<T> = T extends Promise<infer V> ? V : T;

// Recursive infer — unwrap nested promises
type DeepAwaited<T> = T extends Promise<infer R> ? DeepAwaited<R> : T;

function add(a: number, b: number): string { return `${a + b}`; }

type AddReturn = ReturnType2<typeof add>;  // string
type AddFirst = FirstArg<typeof add>;     // number
type StrEl = ArrayElement<string[]>;      // string

// Infer from tuple
type Head<T extends any[]> = T extends [infer H, ...any[]] ? H : never;
type Tail<T extends any[]> = T extends [any, ...infer T] ? T : never;

type H = Head<[1, 2, 3]>;  // 1
type TT = Tail<[1, 2, 3]>; // [2, 3]

console.log('Inference OK');
```

---

## Step 8: Capstone — Type Utilities Library

```typescript
// Save as lab03-capstone.ts
// A collection of useful type utilities

// Conditional mapped type
type IsArray<T> = T extends any[] ? true : false;
type Flatten<T> = T extends Array<infer Item> ? Item : T;
type UnwrapPromise<T> = T extends Promise<infer R> ? R : T;

// Index signature
interface StringMap { [key: string]: string; }
const m: StringMap = { a: '1', b: '2' };

// Mapped types
type Nullable<T> = { [K in keyof T]: T[K] | null };
type Mutable<T>  = { -readonly [K in keyof T]: T[K] };

type User = { readonly id: number; name: string; email: string };
type MutableUser = Mutable<User>;  // id is now mutable

// Conditional type in practice
type NonFunctionKeys<T> = {
  [K in keyof T]: T[K] extends Function ? never : K;
}[keyof T];

type DataOnly<T> = Pick<T, NonFunctionKeys<T>>;

class Service {
  name = 'MyService';
  version = '1.0';
  start(): void {}
  stop(): void {}
}
type ServiceData = DataOnly<Service>;  // { name: string; version: string }

const r: IsArray<number[]> = true;
console.log(r);
console.log(m['a']);
const mu: MutableUser = { id: 1, name: 'Alice', email: 'alice@example.com' };
mu.id = 99;  // now allowed
console.log(mu.id);
console.log('Advanced interfaces OK');
```

Run:
```bash
ts-node -P tsconfig.json lab03-capstone.ts
```

📸 **Verified Output:**
```
true
1
99
Advanced interfaces OK
```

---

## Summary

| Concept | Syntax | Key Difference |
|---------|--------|----------------|
| Interface | `interface X {}` | Mergeable, extends |
| Type alias | `type X = {}` | Unions, intersections, aliases |
| Declaration merging | Two `interface X` | Interfaces only |
| Index signature | `[key: string]: T` | Dynamic properties |
| Mapped type | `[K in keyof T]: ...` | Transform every property |
| Conditional type | `T extends U ? X : Y` | Type-level if/else |
| infer | `T extends F<infer R>` | Capture inner type |
