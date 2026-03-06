# Lab 10: Module Federation — ESM Internals, vm.Module & CJS↔ESM Interop

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm node:20-alpine sh`

Understanding how Node.js resolves and caches modules is essential for building modular systems, dynamic plugins, and micro-frontend architectures. This lab covers ESM internals, `vm.Module`, and the painful world of CJS↔ESM interop.

---

## Step 1: ESM Module System Internals

ESM uses a three-phase lifecycle:
1. **Parse** — find all static imports, build module graph
2. **Link** — resolve specifiers, create bindings
3. **Evaluate** — execute module bodies in dependency order

```
app.mjs
  └── import './lib.mjs'          ← resolved at parse time (static)
        └── import './utils.mjs'  ← recursive
  └── const mod = await import(x) ← dynamic import: resolved at runtime
```

Key differences from CommonJS:
- ESM is **live bindings** (not copies) — exported values update in place
- ESM is **asynchronous** — top-level `await` is supported
- ESM has **`import.meta`** (URL, resolve, dirname equivalent)

---

## Step 2: `import.meta` — The ESM Context Object

```javascript
// file: meta-demo.mjs
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// Equivalent of __filename and __dirname in CJS
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

console.log('import.meta.url:', import.meta.url);
console.log('__filename:', __filename);
console.log('__dirname:', __dirname);

// import.meta.resolve (Node 20.6+)
// Resolves a specifier relative to this module
// const resolved = import.meta.resolve('./utils.mjs');
// console.log('resolved:', resolved);

// Dynamic join (CJS equivalent of path.join(__dirname, 'data'))
const dataPath = join(__dirname, 'data', 'config.json');
console.log('dataPath:', dataPath);
```

> 💡 Always use `fileURLToPath(import.meta.url)` for `__filename`/`__dirname` equivalents in ESM. Never hardcode paths.

---

## Step 3: Dynamic Import with Assertions

```javascript
// file: dynamic-import.mjs
import { createRequire } from 'module';

// Dynamic import: load on demand (lazy loading)
async function loadPlugin(name) {
  try {
    const mod = await import(`./plugins/${name}.mjs`);
    return mod.default;
  } catch (e) {
    console.error(`Plugin ${name} not found:`, e.message);
    return null;
  }
}

// Module graph caching: same specifier returns same module instance
const mod1 = await import('./some-module.mjs').catch(() => null);
const mod2 = await import('./some-module.mjs').catch(() => null);
console.log('Same module instance:', mod1 === mod2); // true (cached)

// JSON import (Node 18+ with assertion)
// const config = await import('./config.json', { assert: { type: 'json' } });

// createRequire: use CJS require() inside ESM
const require = createRequire(import.meta.url);
const path = require('path');
console.log('CJS require in ESM:', path.join('a', 'b'));
```

---

## Step 4: Module Graph Caching

```javascript
// file: module-cache.mjs
// ESM caches modules by their resolved URL

// To bust the cache (force reload) — NOT supported natively in ESM!
// Workaround: append a cache-busting query string
async function reloadModule(specifier) {
  const url = new URL(specifier, import.meta.url);
  url.searchParams.set('t', Date.now());  // unique query = new module instance
  return import(url.href);
}

// CJS module cache (accessible in hybrid apps)
import { createRequire } from 'module';
const require = createRequire(import.meta.url);

// View CJS cache
console.log('CJS cached modules count:', Object.keys(require.cache).length);

// Delete from CJS cache to force reload
// delete require.cache[require.resolve('./my-module')];

console.log('ESM modules are NOT in require.cache');
console.log('ESM cache is internal — use query strings to bust');
```

> 💡 Unlike CJS, ESM module cache cannot be easily cleared. This is intentional for better tree-shaking and analyzer support.

---

## Step 5: `vm.Module` — SyntheticModule & SourceTextModule

```javascript
// file: vm-modules.mjs
// MUST run with: node --experimental-vm-modules vm-modules.mjs
import vm from 'vm';
const { SourceTextModule, SyntheticModule } = vm;

// Create a SyntheticModule (exposes JS values as ESM exports)
const ctx = vm.createContext({ console });

const mathMod = new SyntheticModule(
  ['add', 'multiply', 'PI'],
  function() {
    this.setExport('add', (a, b) => a + b);
    this.setExport('multiply', (a, b) => a * b);
    this.setExport('PI', Math.PI);
  },
  { context: ctx }
);

// Create a SourceTextModule that imports from SyntheticModule
const src = new SourceTextModule(
  `import { add, multiply, PI } from 'math';
   export const result = add(3, 4) + multiply(2, 5);
   export const circle = PI * 5 * 5;`,
  { context: ctx }
);

// Link: resolve import specifiers
await src.link(async (specifier) => {
  if (specifier === 'math') return mathMod;
  throw new Error(`Cannot resolve: ${specifier}`);
});

// Evaluate both modules
await mathMod.evaluate();
await src.evaluate();

console.log('SyntheticModule exports: add, multiply, PI');
console.log('SourceTextModule result:', src.namespace.result, '(expected: 17)');
console.log('Circle area:', src.namespace.circle.toFixed(4));
```

Run: `node --experimental-vm-modules vm-modules.mjs`

📸 **Verified Output:**
```
SyntheticModule exports: add, multiply, PI
SourceTextModule result: 17 (expected: 17)
Circle area: 78.5398
```

---

## Step 6: CJS ↔ ESM Interop — The Gotchas

```javascript
// file: interop-notes.mjs
// Key CJS ↔ ESM interop rules:

// ✅ ESM CAN import CJS:
// import cjsMod from './legacy.cjs';  // gets module.exports as default
// import { specific } = from './legacy.cjs';  // ❌ named imports from CJS may NOT work

// ✅ CJS CANNOT require() ESM synchronously:
// const esm = require('./modern.mjs');  // ❌ Error: require() is not supported

// ✅ CJS CAN use dynamic import() to load ESM:
// const { default: fn } = await import('./modern.mjs');

// Package.json "exports" field controls what's accessible:
const exportsExample = {
  "exports": {
    ".": {
      "import": "./dist/index.mjs",  // for ESM consumers
      "require": "./dist/index.cjs", // for CJS consumers
      "types": "./dist/index.d.ts"   // for TypeScript
    }
  }
};

console.log('CJS ↔ ESM interop rules:');
console.log('  1. ESM can import CJS (default export only reliably)');
console.log('  2. CJS cannot require() ESM directly');
console.log('  3. CJS can use dynamic import() for ESM');
console.log('  4. Use "exports" in package.json for dual-mode packages');
console.log('  5. Set "type": "module" in package.json for .js → ESM');
```

---

## Step 7: Dual-Mode Package (CJS + ESM)

```
my-package/
├── package.json
├── src/
│   └── index.js
├── dist/
│   ├── index.cjs    ← CommonJS build
│   └── index.mjs    ← ESM build
```

```json
// package.json
{
  "name": "my-package",
  "version": "1.0.0",
  "main": "./dist/index.cjs",
  "module": "./dist/index.mjs",
  "exports": {
    ".": {
      "import": {
        "types": "./dist/index.d.mts",
        "default": "./dist/index.mjs"
      },
      "require": {
        "types": "./dist/index.d.ts",
        "default": "./dist/index.cjs"
      }
    }
  },
  "files": ["dist"],
  "sideEffects": false
}
```

> 💡 Always provide both `"import"` and `"require"` in `"exports"`. This is the standard for dual-mode packages (tsup, esbuild, rollup can build both automatically).

---

## Step 8: Capstone — Plugin System with vm.Module

Build a dynamic plugin loader using `vm.Module`:

```javascript
// file: plugin-system.mjs
import vm from 'vm';
const { SourceTextModule, SyntheticModule } = vm;

class PluginSystem {
  constructor() {
    this.plugins = new Map();
    this.hostContext = vm.createContext({
      console,
      Date,
      Math,
      JSON,
      setTimeout,
      clearTimeout,
    });
  }

  // Create host API as SyntheticModule
  createHostAPI() {
    return new SyntheticModule(
      ['log', 'register', 'getConfig'],
      function() {
        this.setExport('log', (msg) => console.log('[Plugin]', msg));
        this.setExport('register', (name, fn) => console.log(`Registered: ${name}`));
        this.setExport('getConfig', () => ({ version: '1.0', env: 'sandbox' }));
      },
      { context: this.hostContext }
    );
  }

  async loadPlugin(name, code) {
    const hostAPI = this.createHostAPI();
    const pluginModule = new SourceTextModule(code, {
      context: this.hostContext,
      identifier: `plugin:${name}`,
    });

    await pluginModule.link(async (spec) => {
      if (spec === '@host') return hostAPI;
      throw new Error(`Plugin ${name}: cannot import '${spec}'`);
    });

    await hostAPI.evaluate();
    await pluginModule.evaluate();

    this.plugins.set(name, pluginModule.namespace);
    return pluginModule.namespace;
  }
}

// Demo: load a plugin
const sys = new PluginSystem();

const pluginCode = `
import { log, register, getConfig } from '@host';

const config = getConfig();
log('Plugin loaded! Config version: ' + config.version);
register('greet', (name) => 'Hello, ' + name);

export const version = '2.0';
export const greet = (name) => 'Hi, ' + name + '!';
`;

const plugin = await sys.loadPlugin('greeter', pluginCode);
console.log('Plugin version:', plugin.version);
console.log('Plugin greet:', plugin.greet('Architect'));
console.log('Total plugins:', sys.plugins.size);
```

Run: `node --experimental-vm-modules plugin-system.mjs`

---

## Summary

| Concept | API | Key Point |
|---|---|---|
| ESM live bindings | `export let x` | Updates propagate to importers |
| Module context | `import.meta.url` | Self-referential module URL |
| CJS in ESM | `createRequire(import.meta.url)` | Access CJS require() from ESM |
| ESM in CJS | `await import(spec)` | Dynamic import (async only) |
| SyntheticModule | `new SyntheticModule(exports, fn)` | Expose JS as ESM |
| SourceTextModule | `new SourceTextModule(code)` | Evaluate JS string as ESM |
| Dual-mode package | `"exports"` in package.json | Serve CJS + ESM from one package |
| Cache busting | Query string on URL | Force reload dynamic ESM |
