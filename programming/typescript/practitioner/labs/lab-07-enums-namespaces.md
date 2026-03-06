# Lab 07: Enums & Namespaces

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Numeric/string/const enums, reverse mapping, enum pitfalls, union type alternatives, namespaces vs modules, ambient declarations.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab07 && cd /lab07
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

## Step 2: Numeric Enums

```typescript
enum Direction {
  Up,     // 0
  Down,   // 1
  Left,   // 2
  Right,  // 3
}

enum Status {
  Active = 1,
  Inactive,  // 2
  Pending,   // 3
  Banned = 10,
  Suspended, // 11
}

// Reverse mapping (numeric enums only)
console.log(Direction.Up);        // 0
console.log(Direction[0]);        // 'Up'  — reverse mapping!
console.log(Status.Active);       // 1
console.log(Status[2]);           // 'Inactive'

// Enums as types
function move(direction: Direction): void {
  switch (direction) {
    case Direction.Up:    console.log('Moving up'); break;
    case Direction.Down:  console.log('Moving down'); break;
    case Direction.Left:  console.log('Moving left'); break;
    case Direction.Right: console.log('Moving right'); break;
  }
}
move(Direction.Up);
```

---

## Step 3: String Enums

```typescript
enum Color {
  Red   = 'RED',
  Green = 'GREEN',
  Blue  = 'BLUE',
}

enum HttpMethod {
  Get    = 'GET',
  Post   = 'POST',
  Put    = 'PUT',
  Delete = 'DELETE',
  Patch  = 'PATCH',
}

// String enums have NO reverse mapping
console.log(Color.Red);        // RED
console.log(HttpMethod.Post);  // POST

function request(url: string, method: HttpMethod): void {
  console.log(`${method} ${url}`);
}
request('/api/users', HttpMethod.Get);

// Check if value is valid enum
function isHttpMethod(val: string): val is HttpMethod {
  return Object.values(HttpMethod).includes(val as HttpMethod);
}
console.log(isHttpMethod('GET'));    // true
console.log(isHttpMethod('INVALID')); // false
```

---

## Step 4: Const Enums

```typescript
// const enum — inlined at compile time, no JS object generated
const enum Size {
  Small  = 1,
  Medium = 2,
  Large  = 3,
}

const enum LogLevel {
  Debug = 'DEBUG',
  Info  = 'INFO',
  Warn  = 'WARN',
  Error = 'ERROR',
}

const size: Size = Size.Medium;
console.log(size);  // 2

// At compile time, Size.Medium is replaced with 2 directly
// Generated JS: const size = 2; (no enum object!)

// Limitation: const enums can't be used at runtime
// (no Size[2] reverse lookup, no Object.values(Size))
```

> 💡 `const enum` produces smaller/faster output but can't be used with `isolatedModules`.

---

## Step 5: Enum Pitfalls & Union Type Alternatives

```typescript
// PITFALL 1: Numeric enums accept any number
enum Permission { Read = 1, Write = 2, Admin = 4 }
const p: Permission = 999;  // No TS error! (bad)

// PITFALL 2: Enums are JS objects (bundle size)
// PITFALL 3: String comparison doesn't work
// Direction.Up === 'Up' is false (it's 0)

// BETTER: Union literal types
type DirectionType = 'up' | 'down' | 'left' | 'right';
type HttpMethodType = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
type LogLevelType = 'debug' | 'info' | 'warn' | 'error';

function moveAlt(dir: DirectionType): void {
  console.log(`Moving ${dir}`);
}
moveAlt('up');  // autocomplete works, no enum import needed

// BETTER: const object (best of both worlds)
const HTTP_METHODS = {
  Get:    'GET',
  Post:   'POST',
  Put:    'PUT',
  Delete: 'DELETE',
} as const;
type HttpMethodConst = typeof HTTP_METHODS[keyof typeof HTTP_METHODS];
// 'GET' | 'POST' | 'PUT' | 'DELETE'

console.log(HTTP_METHODS.Get);         // 'GET'
const method: HttpMethodConst = 'GET'; // type-safe
console.log(method);
```

---

## Step 6: Namespaces

```typescript
// Namespaces group related code (like modules without files)
namespace Validation {
  export interface StringValidator {
    isValid(s: string): boolean;
  }

  export class EmailValidator implements StringValidator {
    isValid(s: string): boolean {
      return /^[^@]+@[^@]+\.[^@]+$/.test(s);
    }
  }

  export class PhoneValidator implements StringValidator {
    isValid(s: string): boolean {
      return /^\+?[\d\s-]{7,15}$/.test(s);
    }
  }

  export function validate(s: string, validator: StringValidator): boolean {
    return validator.isValid(s);
  }
}

// Nested namespaces
namespace App {
  export namespace Utils {
    export function log(msg: string): void { console.log(`[App] ${msg}`); }
  }
  export namespace Config {
    export const version = '1.0.0';
  }
}

const emailV = new Validation.EmailValidator();
console.log(emailV.isValid('alice@example.com'));  // true
console.log(emailV.isValid('not-an-email'));       // false
App.Utils.log('Starting...');
console.log(App.Config.version);
```

---

## Step 7: Ambient Declarations

```typescript
// Ambient declarations describe types for external code
// Usually in .d.ts files, but can be inline with declare

declare namespace jQuery {
  function ajax(url: string): void;
  interface AjaxOptions {
    url: string;
    method?: string;
  }
}

declare const __VERSION__: string;
declare function require(module: string): any;

// Ambient module for custom file types
declare module '*.svg' {
  const content: string;
  export default content;
}

declare module '*.json' {
  const value: any;
  export default value;
}

// Global augmentation
declare global {
  interface String {
    toTitleCase(): string;
  }
}

String.prototype.toTitleCase = function () {
  return this.replace(/\b\w/g, c => c.toUpperCase());
};

console.log('hello world'.toTitleCase());  // Hello World
```

---

## Step 8: Capstone — Enums vs Union Types

```typescript
// Save as lab07-capstone.ts
enum Direction { Up = 'UP', Down = 'DOWN', Left = 'LEFT', Right = 'RIGHT' }
enum Status { Active = 1, Inactive, Pending }

const d: Direction = Direction.Up;
console.log(d);                     // UP
console.log(Status.Active, Status[2]); // 1 Inactive

type Color = 'red' | 'green' | 'blue';
const c: Color = 'red';
console.log(c);

const enum Size { Small = 1, Medium = 2, Large = 3 }
const s: Size = Size.Medium;
console.log(s);

const HTTP = { Get: 'GET', Post: 'POST' } as const;
type Method = typeof HTTP[keyof typeof HTTP];
const m: Method = 'GET';
console.log(m);
console.log('Enums OK');
```

Run:
```bash
ts-node -P tsconfig.json lab07-capstone.ts
```

📸 **Verified Output:**
```
UP
1 Inactive
red
2
GET
Enums OK
```

---

## Summary

| Type | Syntax | Reverse Map | Tree-Shakeable | Recommendation |
|------|--------|-------------|----------------|----------------|
| Numeric enum | `enum E { A = 1 }` | ✅ | ❌ | Avoid (unsafe) |
| String enum | `enum E { A = 'A' }` | ❌ | ❌ | OK for debugging |
| Const enum | `const enum E { A = 1 }` | ❌ | ✅ | Fast, limited use |
| Union type | `'a' \| 'b' \| 'c'` | N/A | ✅ | **Preferred** |
| Const object | `{ A: 'A' } as const` | N/A | ✅ | **Best of both** |
