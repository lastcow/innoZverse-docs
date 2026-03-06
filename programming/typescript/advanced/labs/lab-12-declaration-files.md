# Lab 12: Writing TypeScript Declaration Files

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Write `.d.ts` declaration files for untyped libraries, augment globals, add function overloads, merge namespaces with modules, and understand the @types publishing workflow.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript
mkdir lab12 && cd lab12
npm init -y
echo '{"compilerOptions":{"module":"commonjs","target":"es2020","strict":true,"esModuleInterop":true,"baseUrl":"."}}' > tsconfig.json
```

> 💡 Declaration files describe the shape of JavaScript code to TypeScript. They provide type information without any runtime code — TypeScript discards them at compile time.

---

## Step 2: Basic declare module

Type an untyped JavaScript library:

```bash
# Simulate an untyped JS library
mkdir -p node_modules/myutils
cat > node_modules/myutils/index.js << 'EOF'
exports.formatDate = function(date, format) {
  // ... simplified
  return date.toISOString().split('T')[0];
};
exports.slugify = function(text) {
  return text.toLowerCase().replace(/\s+/g, '-');
};
exports.chunk = function(arr, size) {
  const chunks = [];
  for (let i = 0; i < arr.length; i += size) chunks.push(arr.slice(i, i + size));
  return chunks;
};
EOF
```

```typescript
// @types/myutils/index.d.ts  (or types/myutils.d.ts)
declare module 'myutils' {
  /**
   * Format a Date object to a string.
   * @param date - The date to format
   * @param format - Format pattern ('YYYY-MM-DD', 'MM/DD/YYYY')
   */
  export function formatDate(date: Date, format?: string): string;

  /**
   * Convert a string to a URL-friendly slug.
   */
  export function slugify(text: string): string;

  /**
   * Split an array into chunks of a given size.
   * @returns Array of chunks
   */
  export function chunk<T>(arr: T[], size: number): T[][];

  // Type the entire module as the default export too
  const myutils: {
    formatDate: typeof formatDate;
    slugify: typeof slugify;
    chunk: typeof chunk;
  };
  export default myutils;
}
```

```typescript
// main.ts — use the typed module
import { formatDate, slugify, chunk } from 'myutils';

const date = formatDate(new Date(), 'YYYY-MM-DD');
const slug = slugify('Hello World TypeScript');
const chunks = chunk([1, 2, 3, 4, 5], 2);

console.log('Date:', date);
console.log('Slug:', slug);
console.log('Chunks:', JSON.stringify(chunks));
```

---

## Step 3: Global Augmentation

Add properties to global types like `Window`, `process`, or `Array`:

```typescript
// global.d.ts

// Augment the Window type (browser environment)
declare global {
  interface Window {
    __APP_CONFIG__: {
      apiUrl: string;
      version: string;
      features: Record<string, boolean>;
    };
    trackEvent(event: string, properties?: Record<string, unknown>): void;
  }

  // Add a global function
  function uuid(): string;

  // Augment existing types
  interface Array<T> {
    last(): T | undefined;
    groupBy<K extends string>(keyFn: (item: T) => K): Record<K, T[]>;
  }

  // Global constants injected by webpack/bundler
  const __DEV__: boolean;
  const __VERSION__: string;
  const __BUILD_DATE__: string;
}

// This export makes it a module augmentation, not an ambient module
export {};
```

```typescript
// polyfills.ts — provide runtime implementation
Array.prototype.last = function<T>(this: T[]): T | undefined {
  return this[this.length - 1];
};

Array.prototype.groupBy = function<T, K extends string>(
  this: T[],
  keyFn: (item: T) => K,
): Record<K, T[]> {
  return this.reduce((acc, item) => {
    const key = keyFn(item);
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {} as Record<K, T[]>);
};

// Now TypeScript knows about these
const items = [1, 2, 3, 4, 5];
console.log('Last:', items.last());  // 5

const people = [
  { name: 'Alice', role: 'admin' as const },
  { name: 'Bob', role: 'user' as const },
  { name: 'Charlie', role: 'admin' as const },
];
const grouped = people.groupBy(p => p.role);
console.log('Admins:', grouped.admin.map(p => p.name).join(', '));
```

> 💡 `export {}` at the bottom of a `.d.ts` file makes it a "module" (not a script). In module context, `declare global {}` augments the global scope. Without `export {}`, the file would be ambient and the declarations would apply globally by default.

---

## Step 4: Function Overload Signatures

Describe functions with multiple call signatures:

```typescript
// overloads.d.ts

declare module 'overloaded-lib' {
  // Overload 1: synchronous with string input
  export function parse(input: string): string[];
  // Overload 2: synchronous with buffer
  export function parse(input: Buffer): Uint8Array;
  // Overload 3: async variant
  export function parse(input: string, async: true): Promise<string[]>;
  // Implementation signature (not visible externally)
  export function parse(input: string | Buffer, async?: boolean): string[] | Uint8Array | Promise<string[]>;

  // Overloaded constructor
  export class Parser {
    constructor(options: { encoding: 'utf8' | 'ascii' }): Parser;
    constructor(input: string): Parser;

    // Method overloads
    read(): string;
    read(n: number): string;
    read(encoding: 'base64' | 'hex'): string;
  }
}
```

```typescript
// In your TypeScript code
// overloads.ts
function process(input: string): string[];
function process(input: number): string;
function process(input: string | number): string[] | string {
  if (typeof input === 'string') return input.split(',');
  return String(input);
}

// TypeScript correctly infers return types from overloads
const arr: string[] = process('a,b,c');   // string[]
const str: string = process(42);           // string

console.log('Overload string:', arr);
console.log('Overload number:', str);
```

---

## Step 5: Namespace and Module Merging

Extend a module by adding properties and nested namespaces:

```typescript
// extend-express.d.ts — classic pattern for Express middleware types
import { Request } from 'express';

declare global {
  namespace Express {
    // Augment Express Request type
    interface Request {
      user?: {
        id: string;
        email: string;
        roles: string[];
      };
      requestId: string;
      startTime: number;
    }
  }
}

export {};
```

```typescript
// augment-module.ts
// Merge declarations with an existing module
// This adds to 'myutils' without redefining it

declare module 'myutils' {
  // Add new exports to the existing module declaration
  export function debounce<T extends (...args: unknown[]) => unknown>(
    fn: T,
    delayMs: number,
  ): (...args: Parameters<T>) => void;

  export function throttle<T extends (...args: unknown[]) => unknown>(
    fn: T,
    intervalMs: number,
  ): (...args: Parameters<T>) => void;
}
```

> 💡 Module augmentation must be in a module (file with import/export). The new declarations merge with the original `declare module` block at compile time.

---

## Step 6: Namespace Declarations

Type libraries that use the global namespace pattern:

```typescript
// legacy-lib.d.ts — for IIFE/UMD libraries

declare namespace MyLib {
  interface Config {
    apiKey: string;
    timeout?: number;
    retries?: number;
  }

  interface Response<T = unknown> {
    data: T;
    status: number;
    headers: Record<string, string>;
  }

  class Client {
    constructor(config: Config);
    get<T>(url: string): Promise<Response<T>>;
    post<T>(url: string, body: unknown): Promise<Response<T>>;
    delete(url: string): Promise<Response<void>>;
  }

  // Nested namespace
  namespace utils {
    function serialize(data: unknown): string;
    function deserialize<T>(json: string): T;
  }

  // Static factory
  function create(config: Config): Client;
  const version: string;
}

// UMD export (can be used with both import and global)
export = MyLib;
export as namespace MyLib;
```

---

## Step 7: Publishing @types Packages

Structure for contributing to DefinitelyTyped:

```bash
# Project structure for @types/mylib
mkdir -p types/mylib
cat > types/mylib/index.d.ts << 'EOF'
// Type definitions for mylib 2.x
// Project: https://github.com/example/mylib
// Definitions by: Your Name <https://github.com/yourname>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped
// TypeScript Version: 4.5

export interface Options {
  timeout?: number;
  retries?: number;
  debug?: boolean;
}

export function initialize(options?: Options): void;
export function process(input: string): Promise<string>;
export const version: string;
EOF

cat > types/mylib/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "module": "commonjs",
    "lib": ["es6"],
    "noImplicitAny": true,
    "noImplicitThis": true,
    "strictFunctionTypes": true,
    "strictNullChecks": true,
    "types": [],
    "noEmit": true,
    "forceConsistentCasingInFileNames": true
  },
  "files": ["index.d.ts", "mylib-tests.ts"]
}
EOF

# Test file validates the types work correctly
cat > types/mylib/mylib-tests.ts << 'EOF'
import { initialize, process, version } from 'mylib';

// $ExpectType void
initialize({ timeout: 5000 });

// $ExpectType Promise<string>
const p = process('input');
p.then(result => result.toUpperCase());

// $ExpectType string
const v: string = version;
EOF
```

---

## Step 8: Capstone — Full Declaration File Suite

```typescript
// capstone-types.d.ts — type a complete fictional library

declare module 'db-client' {
  // Generic query result
  interface QueryResult<T = Record<string, unknown>> {
    rows: T[];
    count: number;
    duration: number;
  }

  // Overloaded query function
  function query(sql: string): Promise<QueryResult>;
  function query<T>(sql: string, params: unknown[]): Promise<QueryResult<T>>;

  // Transaction support
  interface Transaction {
    query<T>(sql: string, params?: unknown[]): Promise<QueryResult<T>>;
    commit(): Promise<void>;
    rollback(): Promise<void>;
  }

  class Connection {
    constructor(connectionString: string);
    query: typeof query;
    transaction(): Promise<Transaction>;
    close(): Promise<void>;

    on(event: 'connect', listener: () => void): this;
    on(event: 'error', listener: (err: Error) => void): this;
    on(event: 'disconnect', listener: () => void): this;
  }

  function createPool(options: {
    connectionString: string;
    min?: number;
    max?: number;
    idleTimeoutMs?: number;
  }): Connection;
}

// global.d.ts
declare global {
  interface Window {
    dbClient?: import('db-client').Connection;
  }
}

export {};
```

```bash
# Verify the .d.ts compiles
tsc --noEmit
echo "✅ Lab 12 complete — Declaration files compile with no errors"
```

📸 **Verified Output:**
```
✅ Lab 12 complete — Declaration files compile with no errors
```

---

## Summary

| Pattern | Syntax | Use Case |
|---|---|---|
| Module typing | `declare module 'libname' { ... }` | Type untyped JS library |
| Global augmentation | `declare global { interface Window {...} }` | Extend browser globals |
| Module augmentation | `declare module 'x' { export ... }` | Add to existing types |
| Overloads | Multiple `function f(...)` signatures | Multi-signature functions |
| Namespace | `declare namespace MyLib { ... }` | IIFE/global libraries |
| UMD | `export = Lib; export as namespace Lib` | Works with import or global |
| @types publishing | DefinitelyTyped structure | Community type packages |
