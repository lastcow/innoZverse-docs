# Lab 7: Modules, Namespaces & Declaration Files

## Objective
Use ES modules with TypeScript, write and consume `.d.ts` declaration files, augment existing modules, and organize code with barrels and namespaces.

## Time
25 minutes

## Prerequisites
- Lab 04 (Classes)

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: ES Module Imports & Exports

```typescript
// Named exports
export function add(a: number, b: number): number { return a + b; }
export const PI = 3.14159;
export type Point = { x: number; y: number };
export interface Shape { area(): number; }

// Default export
export default class Calculator {
    constructor(private value: number = 0) {}
    add(n: number): this { this.value += n; return this; }
    result(): number { return this.value; }
}

// Re-export
export { readFileSync as readFile } from "fs";
export * from "./utils";       // re-export all named exports
export * as utils from "./utils"; // namespace re-export
```

```typescript
// Consuming modules
import Calculator, { add, PI, type Point } from "./math";
import type { Shape } from "./math"; // type-only import (erased at runtime)

const calc = new Calculator(10).add(5).add(3);
console.log(calc.result()); // 18
console.log(add(2, 3));     // 5
console.log(PI);             // 3.14159
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
// Simulate module pattern inline
const mathModule = (() => {
    const PI = Math.PI;
    function circleArea(r: number): number { return PI * r ** 2; }
    function squareArea(s: number): number { return s ** 2; }
    return { PI, circleArea, squareArea };
})();

console.log('PI:', mathModule.PI.toFixed(5));
console.log('Circle r=5:', mathModule.circleArea(5).toFixed(2));
console.log('Square s=4:', mathModule.squareArea(4));
"
```

> 💡 **`import type`** (TypeScript 3.8+) is a type-only import that is completely erased at runtime — no `require()` or `import()` is emitted. Use it for interfaces, type aliases, and enums that are only needed for type checking. This speeds up compilation and prevents circular dependency issues.

**📸 Verified Output:**
```
PI: 3.14159
Circle r=5: 78.54
Square s=4: 16
```

---

### Step 2: Declaration Files (.d.ts)

```typescript
// What a .d.ts file looks like for a JavaScript library
// mylib.d.ts — tells TypeScript the types of a JS module

declare module "mylib" {
    export function greet(name: string): string;
    export function version(): string;
    export const MAX_RETRIES: number;

    export interface Config {
        timeout?: number;
        retries?: number;
    }

    export class Client {
        constructor(config?: Config);
        request(url: string): Promise<string>;
        close(): void;
    }

    export default Client;
}

// Global augmentation — add to global scope
declare global {
    interface Window {
        appVersion: string;
        analytics: { track(event: string): void };
    }
}

// Module augmentation — extend existing module
declare module "express" {
    interface Request {
        user?: { id: number; name: string };
        requestId: string;
    }
}
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
// Simulate declaring ambient types
declare function formatCurrency(amount: number, currency?: string): string;
// In real .d.ts this would describe a JS library
// For now, implement it:
const formatCurrency = (amount: number, currency = 'USD'): string =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amount);

console.log(formatCurrency(864));
console.log(formatCurrency(49.99, 'EUR'));
"
```

> 💡 **`.d.ts` files are the glue between JavaScript and TypeScript.** When you install `@types/lodash`, you get a `.d.ts` file describing lodash's types without changing lodash's source. The DefinitelyTyped project maintains 8,000+ such files. For your own JS, `tsc --declaration` generates `.d.ts` automatically.

**📸 Verified Output:**
```
$864.00
€49.99
```

---

### Steps 3–8: Barrel Files, Namespaces, Path Aliases, Circular Deps, Tree Shaking, Capstone

```typescript
// Step 3: Barrel files — index.ts re-exports
// src/models/index.ts
// export { User } from "./user";
// export { Product } from "./product";
// export type { UserRole } from "./user";
// Consumers: import { User, Product } from "./models" — clean!

// Step 4: Namespace (for SDK/library internal organization)
namespace Validators {
    export function isEmail(s: string): boolean {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
    }
    export function isUrl(s: string): boolean {
        try { new URL(s); return true; } catch { return false; }
    }
    export namespace String {
        export function isSlug(s: string): boolean { return /^[a-z0-9-]+$/.test(s); }
        export function isAlpha(s: string): boolean { return /^[a-zA-Z]+$/.test(s); }
    }
}

console.log(Validators.isEmail("chen@example.com"));   // true
console.log(Validators.isEmail("bad-email"));          // false
console.log(Validators.isUrl("https://docs.innozverse.com")); // true
console.log(Validators.String.isSlug("hello-world")); // true

// Step 5: Dynamic imports
async function loadModule(name: string): Promise<{ default: unknown }> {
    // Simulated dynamic import
    return Promise.resolve({ default: `Module ${name} loaded` });
}

// Step 6: Path aliases (tsconfig.json)
// {
//   "compilerOptions": {
//     "paths": {
//       "@models/*": ["src/models/*"],
//       "@utils/*": ["src/utils/*"],
//       "@/*": ["src/*"]
//     }
//   }
// }
// Usage: import { User } from "@models/user"

// Step 7: Tree shaking — named exports enable better bundling
export const util1 = () => "util1";
export const util2 = () => "util2";
// import { util1 } from "./utils" — bundler only includes util1

// Step 8: Capstone — module system
const modules = new Map<string, unknown>();

function registerModule(name: string, factory: () => unknown): void {
    modules.set(name, factory());
}

function getModule<T>(name: string): T {
    const mod = modules.get(name);
    if (!mod) throw new Error(`Module '${name}' not registered`);
    return mod as T;
}

// Register modules
registerModule("config", () => ({ host: "localhost", port: 3000, debug: true }));
registerModule("logger", () => ({
    info: (msg: string) => console.log(`[INFO] ${msg}`),
    error: (msg: string) => console.error(`[ERROR] ${msg}`),
}));

interface Logger { info(msg: string): void; error(msg: string): void; }
interface Config { host: string; port: number; debug: boolean; }

const config = getModule<Config>("config");
const logger = getModule<Logger>("logger");

logger.info(`Starting on ${config.host}:${config.port}`);
logger.info(`Debug mode: ${config.debug}`);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
namespace Fmt {
    export const currency = (n: number) => '\$' + n.toFixed(2);
    export const percent  = (n: number) => (n * 100).toFixed(1) + '%';
    export const pad      = (s: string, w: number) => s.padStart(w);
}
console.log(Fmt.currency(864));
console.log(Fmt.percent(0.075));
console.log(Fmt.pad('42', 8));
"
```

> 💡 **Namespaces are rarely needed in modern TypeScript** — ES modules replaced their use case. The exception is declaration files (`.d.ts`) for global APIs like DOM and ambient declarations for window/global. In application code, use modules. In library type declarations, namespaces still make sense.

**📸 Verified Output:**
```
$864.00
7.5%
      42
```

---

## Summary

TypeScript modules are the backbone of large-scale applications. You've covered named/default exports, `import type`, declaration files, module augmentation, barrel files, namespaces, dynamic imports, path aliases, and a simple module registry system.

## Further Reading
- [TypeScript Modules](https://www.typescriptlang.org/docs/handbook/2/modules.html)
- [Declaration Files](https://www.typescriptlang.org/docs/handbook/declaration-files/introduction.html)
