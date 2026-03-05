# Lab 11: Advanced TypeScript

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master advanced TypeScript: conditional types, mapped types, template literal types, the `infer` keyword, utility types, declaration merging, and module augmentation.

---

## Step 1: Setup

```bash
cd /tmp && npm init -y --quiet
npm install typescript --save-dev
npx tsc --version
```

---

## Step 2: Conditional Types

```typescript
// Conditional types: T extends U ? X : Y
type IsArray<T> = T extends any[] ? true : false;
type IsString<T> = T extends string ? true : false;
type IsFunction<T> = T extends (...args: any[]) => any ? true : false;

type TestArray = IsArray<number[]>;    // true
type TestString = IsArray<string>;     // false
type TestFn = IsFunction<() => void>;  // true

// Distributive conditional types
type NonNullable<T> = T extends null | undefined ? never : T;
type Flatten<T> = T extends (infer U)[] ? U : T;
type UnwrapPromise<T> = T extends Promise<infer U> ? U : T;

type FlatNumber = Flatten<number[]>;      // number
type FlatString = Flatten<string>;        // string (not array)
type Unwrapped = UnwrapPromise<Promise<string>>; // string

// Deep flattening
type DeepFlatten<T> = T extends (infer U)[]
  ? DeepFlatten<U>
  : T;

type Nested = DeepFlatten<number[][][]>; // number

// Extract and Exclude
type Strings = Extract<string | number | boolean, string>; // string
type NoStrings = Exclude<string | number | boolean, string>; // number | boolean
```

---

## Step 3: Mapped Types

```typescript
// Mapped types transform all properties
type Readonly<T> = { readonly [K in keyof T]: T[K] };
type Partial<T> = { [K in keyof T]?: T[K] };
type Required<T> = { [K in keyof T]-?: T[K] };
type Nullable<T> = { [K in keyof T]: T[K] | null };

// With modifiers
type Mutable<T> = { -readonly [K in keyof T]: T[K] };
type NonOptional<T> = { [K in keyof T]-?: T[K] };

// Value transformation
type Stringify<T> = { [K in keyof T]: string };
type Optional<T> = { [K in keyof T]?: T[K] | undefined };

// Filtering properties
type PickByValue<T, V> = {
  [K in keyof T as T[K] extends V ? K : never]: T[K]
};

interface User {
  id: number;
  name: string;
  email: string;
  active: boolean;
  createdAt: Date;
}

type StringFields = PickByValue<User, string>;
// { name: string; email: string }

type NumberFields = PickByValue<User, number>;
// { id: number }

// Rename keys
type WithPrefix<T, P extends string> = {
  [K in keyof T as `${P}${Capitalize<string & K>}`]: T[K]
};

type PrefixedUser = WithPrefix<{ name: string; age: number }, 'get'>;
// { getName: string; getAge: number }
```

---

## Step 4: Template Literal Types

```typescript
// Template literal types: powerful string manipulation
type EventName = 'click' | 'focus' | 'blur';
type HandlerName = `on${Capitalize<EventName>}`;
// 'onClick' | 'onFocus' | 'onBlur'

// CSS property types
type Side = 'top' | 'right' | 'bottom' | 'left';
type Box = 'margin' | 'padding';
type BoxProperty = `${Box}-${Side}`;
// 'margin-top' | 'margin-right' | ... | 'padding-left'

// CRUD API types
type Entity = 'user' | 'post' | 'comment';
type Operation = 'create' | 'read' | 'update' | 'delete';
type Permission = `${Operation}:${Entity}`;
// 'create:user' | 'read:user' | ... | 'delete:comment'

// Event emitter with type-safe events
type EventPayloads = {
  'user:created': { id: number; name: string };
  'user:deleted': { id: number };
  'post:published': { id: number; title: string };
};

type EventEmitter<Events> = {
  on<K extends keyof Events>(event: K, handler: (data: Events[K]) => void): void;
  emit<K extends keyof Events>(event: K, data: Events[K]): void;
};

declare const typedEmitter: EventEmitter<EventPayloads>;
typedEmitter.on('user:created', (data) => {
  console.log(data.name); // Typed!
  // data.foo; // TypeScript Error
});
```

---

## Step 5: The `infer` Keyword

```typescript
// infer extracts types from conditional types
type ReturnType<T> = T extends (...args: any[]) => infer R ? R : never;
type Parameters<T> = T extends (...args: infer P) => any ? P : never;
type InstanceType<T> = T extends new (...args: any[]) => infer I ? I : never;
type FirstArgument<T> = T extends (first: infer F, ...rest: any[]) => any ? F : never;

function greet(name: string, age: number): string { return `Hello ${name}`; }
type GreetReturn = ReturnType<typeof greet>;     // string
type GreetParams = Parameters<typeof greet>;     // [string, number]
type FirstParam = FirstArgument<typeof greet>;   // string

// Unwrap nested types
type Awaited<T> = T extends Promise<infer U>
  ? U extends Promise<any>
    ? Awaited<U>   // Recursively unwrap
    : U
  : T;

type Result1 = Awaited<Promise<string>>;                  // string
type Result2 = Awaited<Promise<Promise<number>>>;         // number
type Result3 = Awaited<string>;                           // string (no-op)

// Extract function argument names (TS 4.1+)
type FuncArgs<T extends string> =
  T extends `(${infer Params})` ? Params : never;

// Recursive type parsing
type Last<T extends any[]> = T extends [...any[], infer L] ? L : never;
type First<T extends any[]> = T extends [infer F, ...any[]] ? F : never;

type LastItem = Last<[1, 2, 3, 4]>; // 4
type FirstItem = First<[string, number, boolean]>; // string
```

---

## Step 6: Utility Types Deep Dive

```typescript
interface ComplexUser {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user';
  profile?: {
    bio: string;
    avatar: string;
  };
  readonly createdAt: Date;
  metadata: Record<string, unknown>;
}

// Standard utility types
type PartialUser = Partial<ComplexUser>;        // All optional
type RequiredUser = Required<ComplexUser>;      // All required
type ReadonlyUser = Readonly<ComplexUser>;      // All readonly

// Pick and Omit
type PublicUser = Pick<ComplexUser, 'id' | 'name' | 'email'>;
type UserWithoutMeta = Omit<ComplexUser, 'metadata' | 'createdAt'>;

// Record
type UserMap = Record<string, ComplexUser>;
type RolePermissions = Record<ComplexUser['role'], string[]>;

// Function types
async function fetchUser(id: number): Promise<ComplexUser> { /* ... */ }
type FetchReturn = Awaited<ReturnType<typeof fetchUser>>; // ComplexUser
type FetchParams = Parameters<typeof fetchUser>;          // [number]

// NonNullable
type MaybeUser = ComplexUser | null | undefined;
type DefiniteUser = NonNullable<MaybeUser>; // ComplexUser

// Conditional utility
type CreateInput<T> = Omit<T, 'id' | 'createdAt'> & { id?: never };
type UserCreateInput = CreateInput<ComplexUser>;
```

---

## Step 7: Declaration Merging & Module Augmentation

```typescript
// Interface merging — add properties to existing interface
interface Window {
  myCustomLib: {
    version: string;
    initialize(): void;
  };
}

// Extend express Request type
declare namespace Express {
  interface Request {
    user?: { id: number; role: string };
    requestId: string;
  }
}

// Module augmentation — add methods to external library
declare module 'express' {
  interface Request {
    db: import('knex').Knex;
    logger: import('pino').Logger;
  }
}

// Extend built-in types
interface Array<T> {
  chunk(size: number): T[][];
  unique(): T[];
}

Array.prototype.chunk = function<T>(size: number): T[][] {
  const chunks: T[][] = [];
  for (let i = 0; i < this.length; i += size) {
    chunks.push(this.slice(i, i + size));
  }
  return chunks;
};

// Global type augmentation
declare global {
  interface String {
    toSlug(): string;
  }
}
```

---

## Step 8: Capstone — TypeScript Compile Demo

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && npm init -y --quiet > /dev/null && npm install typescript --save-dev --quiet > /dev/null 2>&1

cat > /tmp/demo.ts << 'TSEOF'
// TypeScript advanced types demo
type IsArray<T> = T extends any[] ? true : false;
type ElementType<T> = T extends (infer U)[] ? U : never;
type DeepPartial<T> = { [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K] };
type CSSProperty = 'margin' | 'padding';
type CSSDirection = 'top' | 'bottom' | 'left' | 'right';
type CSSProp = \`\${CSSProperty}-\${CSSDirection}\`;

console.log('TypeScript types demo');
const test: CSSProp = 'margin-top';
console.log(test);
const arr: IsArray<number[]> = true;
console.log(arr);
type Nums = ElementType<number[]>;
const n: Nums = 42;
console.log(n);
TSEOF

/tmp/node_modules/.bin/tsc /tmp/demo.ts --outDir /tmp/out --target ES2020 --strict 2>&1 | head -5 || true
node /tmp/out/demo.js 2>/dev/null
" 2>/dev/null
```

📸 **Verified Output:**
```
TypeScript types demo
margin-top
true
42
```

---

## Summary

| Feature | Syntax | Use Case |
|---------|--------|----------|
| Conditional type | `T extends U ? X : Y` | Type branching |
| Mapped type | `{ [K in keyof T]: ... }` | Transform all properties |
| Template literal | `` `${A}-${B}` `` | String type combinations |
| `infer` | `T extends (infer U)[]` | Extract inner types |
| `Partial<T>` | Built-in | Make all fields optional |
| `Required<T>` | Built-in | Make all fields required |
| `Pick<T, K>` | Built-in | Select subset of fields |
| `Omit<T, K>` | Built-in | Remove subset of fields |
| `ReturnType<T>` | Built-in | Extract function return type |
| Declaration merging | Repeat `interface` | Extend existing types |
| Module augmentation | `declare module '...'` | Add to third-party types |
