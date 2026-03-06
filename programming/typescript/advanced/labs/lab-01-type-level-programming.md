# Lab 01: Type-Level Programming

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Recursive types, variadic tuple types, type-safe curry, HList, `Awaited<T>` pattern, TypeScript 4.7+/5.x inference improvements.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab-adv01 && cd /lab-adv01
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

## Step 2: Recursive Types

```typescript
// Recursive JSON type
type JSONValue =
  | string
  | number
  | boolean
  | null
  | JSONValue[]
  | { [key: string]: JSONValue };

// Deep nested type
type DeepPartial<T> = T extends object
  ? { [P in keyof T]?: DeepPartial<T[P]> }
  : T;

type DeepReadonly<T> = T extends object
  ? { readonly [P in keyof T]: DeepReadonly<T[P]> }
  : T;

// Recursive path extraction
type Paths<T, Prefix extends string = ''> = T extends object
  ? {
      [K in keyof T & string]:
        | `${Prefix}${K}`
        | Paths<T[K], `${Prefix}${K}.`>
    }[keyof T & string]
  : never;

interface Config {
  db: { host: string; port: number; name: string };
  app: { host: string; port: number; debug: boolean };
}

type ConfigPaths = Paths<Config>;
// 'db' | 'db.host' | 'db.port' | 'db.name' | 'app' | ...

const path: ConfigPaths = 'db.host';
console.log(path);

const json: JSONValue = { a: [1, 'two', { b: true }], c: null };
console.log(JSON.stringify(json));
```

---

## Step 3: Variadic Tuple Types

```typescript
// TypeScript 4.0+: variadic tuples
type Concat<T extends unknown[], U extends unknown[]> = [...T, ...U];
type Prepend<T, Arr extends unknown[]> = [T, ...Arr];
type Tail<T extends unknown[]> = T extends [any, ...infer Rest] ? Rest : never;
type Head<T extends unknown[]> = T extends [infer H, ...any[]] ? H : never;

type A = Concat<[1, 2], [3, 4]>;        // [1, 2, 3, 4]
type B = Prepend<0, [1, 2, 3]>;         // [0, 1, 2, 3]
type C = Tail<[string, number, boolean]>; // [number, boolean]
type H = Head<[string, number, boolean]>; // string

// Typed function composition using tuples
function concat<T extends unknown[], U extends unknown[]>(
  a: [...T],
  b: [...U]
): [...T, ...U] {
  return [...a, ...b];
}

const result = concat([1, 'two'] as const, [true, 3] as const);
console.log(result); // [1, 'two', true, 3]

// Typed zip
type Zip<T extends unknown[], U extends unknown[]> =
  T extends [infer TH, ...infer TT]
    ? U extends [infer UH, ...infer UT]
      ? [[TH, UH], ...Zip<TT, UT>]
      : []
    : [];

type Zipped = Zip<[1, 2, 3], ['a', 'b', 'c']>;
// [[1, 'a'], [2, 'b'], [3, 'c']]
```

---

## Step 4: Type-Safe Curry

```typescript
// Recursive curry type
type Curry<Args extends unknown[], Return> =
  Args extends [infer First, ...infer Rest]
    ? (arg: First) => Curry<Rest, Return>
    : Return;

function curry<Args extends unknown[], R>(
  fn: (...args: Args) => R
): Curry<Args, R> {
  const arity = fn.length;
  function curried(...args: unknown[]): unknown {
    if (args.length >= arity) return fn(...(args as Args));
    return (...moreArgs: unknown[]) => curried(...args, ...moreArgs);
  }
  return curried as Curry<Args, R>;
}

const add = (a: number, b: number): number => a + b;
const curriedAdd = curry(add);
const add5 = curriedAdd(5);   // (b: number) => number
const result2 = add5(3);       // 8

console.log(curriedAdd(3)(4)); // 7
console.log(add5(10));         // 15

const multiply3 = curry((a: number, b: number, c: number) => a * b * c);
console.log(multiply3(2)(3)(4)); // 24
```

---

## Step 5: HList (Heterogeneous List)

```typescript
// HList: typed list with different element types
type HList = unknown[];

type HNil = [];
type HCons<H, T extends HList> = [H, ...T];

// Type-safe head/tail
type HHead<L extends HList> = L extends [infer H, ...any[]] ? H : never;
type HTail<L extends HList> = L extends [any, ...infer T] ? T : never;
type HLength<L extends HList> = L['length'];

// Reverse an HList
type HReverse<L extends HList, Acc extends HList = []> =
  L extends [infer H, ...infer T]
    ? HReverse<T, [H, ...Acc]>
    : Acc;

type List = [string, number, boolean, Date];
type FirstEl = HHead<List>;    // string
type RestEls = HTail<List>;    // [number, boolean, Date]
type Len = HLength<List>;      // 4
type Rev = HReverse<List>;     // [Date, boolean, number, string]

const list: List = ['hello', 42, true, new Date()];
const [first, ...rest] = list;
console.log(first, typeof first);      // hello string
console.log(rest[0], typeof rest[0]);  // 42 number
```

---

## Step 6: Awaited<T> and Promise Inference

```typescript
// Awaited<T> (built-in since TS 4.5) — recursively unwrap promises
type MyAwaited<T> =
  T extends null | undefined
    ? T
    : T extends object & { then(onfulfilled: infer F): any }
      ? F extends (value: infer V) => any
        ? MyAwaited<V>
        : never
      : T;

// Usage
type A2 = Awaited<Promise<string>>;                 // string
type B2 = Awaited<Promise<Promise<number>>>;         // number
type C2 = Awaited<Promise<string> | Promise<number>>; // string | number

async function fetchUser(): Promise<{ id: number; name: string }> {
  return { id: 1, name: 'Alice' };
}

type FetchUserReturn = Awaited<ReturnType<typeof fetchUser>>;
// { id: number; name: string }

// Infer types from async functions
type AsyncReturnType<T extends (...args: any[]) => Promise<any>> =
  T extends (...args: any[]) => Promise<infer R> ? R : never;

type UserData = AsyncReturnType<typeof fetchUser>;

const user: UserData = { id: 1, name: 'Alice' };
console.log(user.name);
console.log('Type-level programming OK');
```

---

## Step 7: TypeScript 5.x Features

```typescript
// const type parameters (TS 5.0)
function identity<const T>(x: T): T { return x; }
const arr = identity([1, 2, 3] as const);
// arr: readonly [1, 2, 3] — NOT number[]

// Variadic tuple labels (TS 4.0)
type Range<From extends string, To extends string> = [from: From, to: To];
type Bounds = Range<'start', 'end'>;

// Satisfies operator (TS 4.9) + type narrowing
type Palette = Record<string, [number, number, number] | string>;
const palette = {
  red: [255, 0, 0],
  green: '#00ff00',
} satisfies Palette;

// palette.red is [number, number, number], not the wider Color type
console.log(palette.red[0]);        // 255
console.log(palette.green.length);  // 7

// Using (TypeScript 5.2+) — explicit resource management
class Resource {
  [Symbol.dispose](): void { console.log('Resource disposed'); }
  read(): string { return 'data'; }
}

function withResource(): void {
  // using r = new Resource(); // TS 5.2+
  const r = new Resource();
  console.log(r.read());
  r[Symbol.dispose](); // manual for demo
}
withResource();
```

---

## Step 8: Capstone — Type-Level Utilities

```typescript
// Save as lab-adv01-capstone.ts
function identity<T>(x: T): T { return x; }
function first<T>(arr: T[]): T | undefined { return arr[0]; }

class Stack<T> {
  private items: T[] = [];
  push(item: T): void { this.items.push(item); }
  pop(): T | undefined { return this.items.pop(); }
  peek(): T | undefined { return this.items[this.items.length - 1]; }
  get size(): number { return this.items.length; }
}

const s = new Stack<number>();
s.push(1); s.push(2); s.push(3);
console.log('peek:', s.peek());
console.log('pop:', s.pop());
console.log('size:', s.size);
console.log(identity<string>('hello'));
console.log(first([10, 20, 30]));

type Partial2<T> = { [P in keyof T]?: T[P] };
type User = { id: number; name: string; email: string };
const partial: Partial2<User> = { name: 'Bob' };
console.log('partial user:', JSON.stringify(partial));
console.log('Generics OK');
```

Run:
```bash
ts-node -P tsconfig.json lab-adv01-capstone.ts
```

📸 **Verified Output:**
```
peek: 3
pop: 3
size: 2
hello
10
partial user: {"name":"Bob"}
Generics OK
```

---

## Summary

| Feature | Syntax | TS Version |
|---------|--------|------------|
| Recursive type | `type F<T> = T extends ... ? F<...> : ...` | 4.1+ |
| Variadic tuple | `[...T, ...U]` | 4.0+ |
| Tuple head/tail | `[infer H, ...infer T]` | 4.0+ |
| Type curry | `Curry<Args, Return>` recursive | 4.0+ |
| Awaited | `Awaited<Promise<T>>` | 4.5+ |
| const type param | `<const T>` | 5.0+ |
| satisfies | `value satisfies Type` | 4.9+ |
| using | `using x = new Resource()` | 5.2+ |
