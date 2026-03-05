# Lab 03: ES Modules (ESM)

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Understand ES module system: named/default exports, imports, dynamic import(), namespace imports, re-exporting, and differences between ESM and CommonJS.

---

## Step 1: Named Exports & Imports

```javascript
// math.mjs — named exports
export const PI = 3.14159265358979;
export function add(a, b) { return a + b; }
export function multiply(a, b) { return a * b; }
export class Vector {
  constructor(x, y) { this.x = x; this.y = y; }
  magnitude() { return Math.sqrt(this.x ** 2 + this.y ** 2); }
  add(other) { return new Vector(this.x + other.x, this.y + other.y); }
}

// main.mjs — named imports
import { PI, add, multiply, Vector } from './math.mjs';
console.log(PI);                          // 3.14159...
console.log(add(2, 3));                   // 5
const v = new Vector(3, 4);
console.log(v.magnitude());               // 5
```

> 💡 Named exports are bound to the module's live bindings — if the value changes in the exporting module, importers see the change.

---

## Step 2: Default Exports

```javascript
// logger.mjs — default export
export default class Logger {
  constructor(prefix = '') { this.prefix = prefix; }
  log(msg) { console.log(`[${this.prefix}] ${msg}`); }
  warn(msg) { console.warn(`[${this.prefix}] WARN: ${msg}`); }
  error(msg) { console.error(`[${this.prefix}] ERROR: ${msg}`); }
}

// main.mjs — default import (any name works)
import Logger from './logger.mjs';
import MyLogger from './logger.mjs'; // Same thing, different alias

const log = new Logger('APP');
log.log('Server started');
```

> 💡 A module can have only ONE default export but unlimited named exports.

---

## Step 3: Namespace Imports & Re-exports

```javascript
// utils/string.mjs
export const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);
export const truncate = (s, n) => s.length > n ? s.slice(0, n) + '...' : s;

// utils/array.mjs
export const unique = arr => [...new Set(arr)];
export const chunk = (arr, size) => {
  const chunks = [];
  for (let i = 0; i < arr.length; i += size) chunks.push(arr.slice(i, i + size));
  return chunks;
};

// utils/index.mjs — re-export everything
export * from './string.mjs';
export * from './array.mjs';
export * as StringUtils from './string.mjs'; // Namespace re-export

// main.mjs
import * as Utils from './utils/index.mjs'; // Namespace import
import { capitalize, unique } from './utils/index.mjs';

console.log(Utils.chunk([1, 2, 3, 4, 5], 2)); // [[1,2],[3,4],[5]]
console.log(capitalize('hello'));               // Hello
console.log(unique([1, 2, 2, 3, 3]));           // [1, 2, 3]
```

---

## Step 4: Dynamic import()

```javascript
// Lazy loading — only load when needed
async function loadModule(type) {
  switch (type) {
    case 'chart':
      const { default: ChartLib } = await import('./chart.mjs');
      return new ChartLib();
    case 'pdf':
      const { PDFGenerator } = await import('./pdf.mjs');
      return new PDFGenerator();
    default:
      throw new Error(`Unknown module type: ${type}`);
  }
}

// Conditional loading
async function loadPolyfill() {
  if (!globalThis.fetch) {
    await import('node-fetch'); // Only load if needed
  }
}

// Dynamic import returns a Module object
const moduleSpecifier = './math.mjs';
const mathModule = await import(moduleSpecifier);
console.log(mathModule.add(1, 2)); // 3
console.log(Object.keys(mathModule)); // ['PI', 'add', 'multiply', 'Vector', 'default']
```

> 💡 Dynamic `import()` is perfect for code splitting and lazy loading in browsers.

---

## Step 5: Module Resolution

```javascript
// Relative imports (explicit extension required in ESM)
import { foo } from './foo.mjs';       // ✓ explicit .mjs
import { bar } from '../utils/bar.js'; // ✓ works with .js too
// import { baz } from './baz';        // ✗ Error in ESM (works in CJS)

// Node.js built-in modules
import { readFile } from 'node:fs/promises'; // Preferred: node: prefix
import path from 'node:path';
import { createHash } from 'node:crypto';

// Package imports (from node_modules)
import express from 'express';
import { z } from 'zod';

// Package.json exports field (modern packages)
// "exports": {
//   ".": "./dist/index.js",
//   "./utils": "./dist/utils.js"
// }
import { helper } from 'my-package/utils';
```

---

## Step 6: Circular Dependencies

```javascript
// a.mjs
import { b } from './b.mjs';
export const a = 'A';
console.log('a.mjs loaded, b =', b); // b may be undefined on first load!

// b.mjs
import { a } from './a.mjs';
export const b = 'B';
console.log('b.mjs loaded, a =', a);

// The key: ESM handles circulars differently than CJS
// ESM: live bindings, evaluated in declaration order
// CJS: gets whatever was exported at the time of require()

// Solution: Use functions to defer evaluation
// a.mjs (safe version)
import { getB } from './b.mjs';
export const a = 'A';
export function getA() { return a; } // Lazy — called after modules loaded

// b.mjs (safe version)
import { getA } from './a.mjs';
export const b = 'B';
export function getB() { return b; }
// Both getA() and getB() work correctly when called after initialization
```

---

## Step 7: CommonJS vs ESM Differences

```javascript
// CommonJS (require/module.exports)
// Works in .js files (default in Node.js without "type": "module")
const fs = require('fs');
const { join } = require('path');
module.exports = { myFunction };
module.exports.default = MyClass;

// ESM (import/export)
// Works in .mjs files or .js with "type": "module" in package.json
import fs from 'node:fs';
import { join } from 'node:path';
export { myFunction };
export default MyClass;

// Key differences:
// 1. CJS: synchronous require(); ESM: asynchronous import
// 2. CJS: __dirname, __filename available; ESM: use import.meta.url
// 3. CJS: dynamic require(variable); ESM: use dynamic import()
// 4. CJS: exports are copies; ESM: exports are live bindings

// ESM equivalent of __dirname
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Importing CJS from ESM (default import only)
import cjsModule from './legacy-cjs.js';
const { namedExport } = cjsModule; // Destructure from default

// import.meta object
console.log(import.meta.url);  // file:///path/to/current/module.mjs
```

> 💡 Use `"type": "module"` in `package.json` to make all `.js` files use ESM.

---

## Step 8: Capstone — Module-Based Utility Library

```javascript
// Run this as ESM: echo '...' | node --input-type=module

// Inline module simulation
const createMathUtils = () => {
  const PI = Math.PI;
  const add = (a, b) => a + b;
  const multiply = (a, b) => a * b;
  const factorial = n => n <= 1 ? 1 : n * factorial(n - 1);
  return { PI, add, multiply, factorial };
};

const createStringUtils = () => {
  const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);
  const camelToSnake = s => s.replace(/[A-Z]/g, l => `_${l.toLowerCase()}`);
  const template = (str, vars) => str.replace(/\${(\w+)}/g, (_, k) => vars[k] ?? '');
  return { capitalize, camelToSnake, template };
};

// Namespace pattern (simulates namespace import)
const Math2 = createMathUtils();
const String2 = createStringUtils();

console.log(Math2.factorial(6));                        // 720
console.log(String2.capitalize('hello world'));          // Hello world
console.log(String2.camelToSnake('camelCaseString'));    // camel_case_string
console.log(String2.template('Hello ${name}!', { name: 'Alice' })); // Hello Alice!
```

**Run with ESM:**
```bash
docker run --rm node:20-alpine sh -c "echo '
import { createRequire } from \"node:module\";
import { fileURLToPath } from \"node:url\";
const __filename = fileURLToPath(import.meta.url);
console.log(\"ESM file:\", __filename);
const add = (a, b) => a + b;
export default add;
const result = add(3, 4);
console.log(\"3 + 4 =\", result);
const items = [1, 2, 3];
const doubled = items.map(x => x * 2);
console.log(\"Doubled:\", doubled);
' | node --input-type=module"
```

📸 **Verified Output:**
```
ESM file: /dev/stdin
3 + 4 = 7
Doubled: [ 2, 4, 6 ]
```

---

## Summary

| Feature | ESM | CommonJS |
|---------|-----|----------|
| Syntax | `import`/`export` | `require()`/`module.exports` |
| Loading | Async, static analysis | Sync, dynamic |
| File extension | `.mjs` or `.js` with `"type":"module"` | `.cjs` or `.js` (default) |
| `__dirname` | `dirname(fileURLToPath(import.meta.url))` | Built-in |
| Dynamic | `await import(specifier)` | `require(variable)` |
| Tree shaking | ✓ Yes (bundlers can optimize) | ✗ No |
| Circular deps | Live bindings | Snapshot at require time |
