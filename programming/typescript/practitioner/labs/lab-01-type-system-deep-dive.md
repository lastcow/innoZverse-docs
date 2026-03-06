# Lab 01: Type System Deep Dive

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Master TypeScript's type system: union/intersection types, type narrowing, literal types, template literal types, and const assertions.

---

## Step 1: Setup Environment

```bash
docker run -it --rm node:20-alpine sh
apk add --no-cache git
npm install -g typescript ts-node
mkdir /lab01 && cd /lab01
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

> 💡 We use `module: "commonjs"` so ts-node works without ESM configuration.

---

## Step 2: Union and Intersection Types

```typescript
// types.ts
type StringOrNumber = string | number;

type Named = { name: string };
type Aged  = { age: number };
type Person = Named & Aged;   // intersection: must have BOTH

function format(val: StringOrNumber): string {
  if (typeof val === 'string') return val.toUpperCase();
  return val.toFixed(2);
}

const p: Person = { name: 'Alice', age: 30 };
console.log(format('hello')); // HELLO
console.log(format(42));      // 42.00
console.log(p.name, p.age);
```

> 💡 `A | B` = either A or B. `A & B` = both A and B combined.

---

## Step 3: Type Narrowing — typeof / instanceof / in

```typescript
class ApiError extends Error {
  constructor(public statusCode: number, message: string) {
    super(message);
  }
}

function handle(err: Error | ApiError | string): string {
  if (typeof err === 'string') return `String error: ${err}`;
  if (err instanceof ApiError) return `API ${err.statusCode}: ${err.message}`;
  return `Error: ${err.message}`;
}

interface Cat { meow(): void }
interface Dog { bark(): void }
function speak(animal: Cat | Dog): void {
  if ('meow' in animal) animal.meow();
  else animal.bark();
}
```

> 💡 TypeScript narrows the type inside each `if` block based on the guard used.

---

## Step 4: Discriminated Union Pattern

```typescript
type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rect';   w: number; h: number }
  | { kind: 'triangle'; base: number; height: number };

function area(s: Shape): number {
  switch (s.kind) {
    case 'circle':   return Math.PI * s.radius ** 2;
    case 'rect':     return s.w * s.h;
    case 'triangle': return 0.5 * s.base * s.height;
    default:
      const _exhaustive: never = s;
      throw new Error(`Unknown shape: ${_exhaustive}`);
  }
}

console.log(area({ kind: 'circle', radius: 5 }).toFixed(4));  // 78.5398
console.log(area({ kind: 'rect', w: 4, h: 6 }));              // 24
```

> 💡 The `never` default branch catches missing cases at **compile time** — add a new shape and TypeScript errors if you forget to handle it.

---

## Step 5: Literal Types

```typescript
type Direction = 'north' | 'south' | 'east' | 'west';
type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
type Port = 80 | 443 | 3000 | 8080;

function fetch(url: string, method: HttpMethod): void {
  console.log(`${method} ${url}`);
}

fetch('https://api.example.com/users', 'GET');
// fetch('https://api.example.com', 'INVALID'); // TS error!
```

---

## Step 6: Template Literal Types

```typescript
type EventName = 'click' | 'focus' | 'blur';
type Handler = `on${Capitalize<EventName>}`;  // 'onClick' | 'onFocus' | 'onBlur'

type Getter<T extends string> = `get${Capitalize<T>}`;
type Setter<T extends string> = `set${Capitalize<T>}`;
type Accessor<T extends string> = Getter<T> | Setter<T>;

type NameAccessors = Accessor<'name'>;  // 'getName' | 'setName'

const h: Handler = 'onClick';
const a: NameAccessors = 'getName';
console.log(h, a);  // onClick getName

// CSS property safety
type CSSUnit = 'px' | 'em' | 'rem' | '%';
type CSSValue = `${number}${CSSUnit}`;
const spacing: CSSValue = '16px';
```

---

## Step 7: Const Assertions

```typescript
// Without as const — TypeScript widens types
const config1 = { host: 'localhost', port: 3000 };
// config1.port is number (mutable)

// With as const — types are narrowed to literals
const config2 = { host: 'localhost', port: 3000 } as const;
// config2.port is 3000 (readonly, literal)

const colors = ['red', 'green', 'blue'] as const;
// colors is readonly ['red', 'green', 'blue']
type Color = typeof colors[number];  // 'red' | 'green' | 'blue'

const routes = {
  home: '/',
  users: '/users',
  profile: '/profile',
} as const;
type Route = typeof routes[keyof typeof routes];  // '/' | '/users' | '/profile'

console.log(config2.port);          // 3000
console.log(colors[1]);             // green
console.log(Object.values(routes)); // ['/', '/users', '/profile']
```

> 💡 `as const` is invaluable for configuration objects, route maps, and anywhere you need TypeScript to infer the narrowest possible types.

---

## Step 8: Capstone — Full Type Safety Demo

```typescript
// Save as lab01-capstone.ts
type StringOrNumber = string | number;
type Named = { name: string };
type Aged  = { age: number };
type Person = Named & Aged;

type Shape =
  | { kind: 'circle'; radius: number }
  | { kind: 'rect';   w: number; h: number };

type EventName = 'click' | 'focus' | 'blur';
type Handler = `on${Capitalize<EventName>}`;

const config = { host: 'localhost', port: 3000, env: 'production' } as const;
type Env = typeof config['env'];  // 'production'

function format(val: StringOrNumber): string {
  return typeof val === 'string' ? val.toUpperCase() : val.toFixed(2);
}

function area(s: Shape): number {
  switch (s.kind) {
    case 'circle': return Math.PI * s.radius ** 2;
    case 'rect':   return s.w * s.h;
  }
}

const p: Person = { name: 'Alice', age: 30 };
const h: Handler = 'onClick';

console.log('--- Capstone Lab 01 ---');
console.log(format('hello'));
console.log(format(42));
console.log(area({ kind: 'circle', radius: 5 }).toFixed(4));
console.log(area({ kind: 'rect', w: 4, h: 6 }));
console.log(`${p.name}, age ${p.age}`);
console.log(h, config.port);
```

Run it:
```bash
ts-node -P tsconfig.json lab01-capstone.ts
```

📸 **Verified Output:**
```
--- Capstone Lab 01 ---
HELLO
42.00
78.5398
24
Alice, age 30
onClick 3000
```

---

## Summary

| Concept | Syntax | Use Case |
|---------|--------|----------|
| Union type | `A \| B` | Value can be one of several types |
| Intersection type | `A & B` | Value must satisfy all types |
| typeof narrowing | `typeof x === 'string'` | Primitives |
| instanceof narrowing | `x instanceof Cls` | Classes |
| in narrowing | `'prop' in x` | Object shapes |
| Discriminated union | `switch(x.kind)` | Tagged union pattern |
| Template literal type | `` `on${Capitalize<T>}` `` | String construction types |
| Const assertion | `x as const` | Narrow to literal types |
