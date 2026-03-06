# Lab 14: tsconfig.json Deep Dive

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

`target/lib/module/moduleResolution`, strict flags, project references, composite builds, incremental, paths/baseUrl, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab14 && cd /lab14
```

---

## Step 2: target, lib, module

```json
{
  "compilerOptions": {
    // target: which JS version to emit
    // ES5 = IE11 compat, ES2020 = modern Node/browser
    "target": "ES2020",

    // lib: which built-in APIs TypeScript knows about
    // Defaults to match target, but you can override
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    // For Node.js only (no DOM):
    // "lib": ["ES2020"],

    // module: module format for output
    // "commonjs"   = require/module.exports (Node.js, ts-node)
    // "ESNext"     = import/export (bundlers, browser)
    // "NodeNext"   = Node.js ESM with .js extensions
    "module": "commonjs",

    // moduleResolution: how to resolve imports
    // "node"    = classic Node.js algorithm (recommended for ts-node)
    // "bundler" = bundler-friendly (TS 5.0+)
    // "NodeNext"= matches Node.js ESM
    "moduleResolution": "node"
  }
}
```

---

## Step 3: Strict Flags Explained

```json
{
  "compilerOptions": {
    // "strict": true is shorthand for ALL of these:
    "strictNullChecks": true,       // null/undefined must be handled
    "strictFunctionTypes": true,    // safer function parameter variance
    "strictBindCallApply": true,    // typed .bind/.call/.apply
    "strictPropertyInitialization": true, // class fields must be initialized
    "noImplicitAny": true,          // no implicit 'any'
    "noImplicitThis": true,         // 'this' must be typed
    "alwaysStrict": true,           // emit 'use strict'
    "useUnknownInCatchVariables": true, // catch(e: unknown) instead of any

    // Additional safety flags (not in "strict"):
    "noUncheckedIndexedAccess": true,   // arr[0] is T | undefined
    "exactOptionalPropertyTypes": true, // optional ≠ undefined
    "noImplicitReturns": true,          // all code paths must return
    "noFallthroughCasesInSwitch": true, // no fallthrough in switch
    "noUnusedLocals": true,             // error on unused variables
    "noUnusedParameters": true,         // error on unused parameters
    "noPropertyAccessFromIndexSignature": true
  }
}
```

---

## Step 4: noUncheckedIndexedAccess

```typescript
// With "noUncheckedIndexedAccess": true
const arr = [1, 2, 3];
const first = arr[0];  // number | undefined (not just number!)

if (first !== undefined) {
  console.log(first * 2);  // safe
}

// Non-null assertion when you know it's there
const second = arr[1]!;  // number (trust me)

// Works with Record too
const map: Record<string, number> = { a: 1 };
const val = map['a'];  // number | undefined
const definiteVal = map['a']!;

// Useful pattern: use ?? for defaults
const safe = arr[0] ?? 0;
console.log(safe);
```

---

## Step 5: exactOptionalPropertyTypes

```typescript
// With "exactOptionalPropertyTypes": true
// optional means "maybe absent" — NOT "may be undefined"

interface User {
  name: string;
  nickname?: string;  // may be absent from object
}

// Without exactOptionalPropertyTypes:
const u1: User = { name: 'Alice', nickname: undefined }; // allowed

// With exactOptionalPropertyTypes:
// const u2: User = { name: 'Alice', nickname: undefined }; // ERROR!
// nickname must either be absent or a string — not undefined!

const u3: User = { name: 'Alice' };               // OK — absent
const u4: User = { name: 'Alice', nickname: 'Al' }; // OK — string
```

---

## Step 6: Project References

```bash
# Multi-package setup with project references
mkdir -p /lab14/{shared,app} && cd /lab14

cat > shared/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "declaration": true,
    "composite": true,
    "outDir": "dist"
  },
  "include": ["src"]
}
EOF

cat > app/tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "outDir": "dist"
  },
  "references": [{ "path": "../shared" }]
}
EOF

cat > tsconfig.json << 'EOF'
{
  "files": [],
  "references": [
    { "path": "shared" },
    { "path": "app" }
  ]
}
EOF
```

> 💡 `composite: true` enables project references. TypeScript builds only what changed. Use `tsc --build` (or `tsc -b`) to build the whole project graph.

---

## Step 7: Incremental Builds

```json
{
  "compilerOptions": {
    // Incremental — saves build info for faster rebuilds
    "incremental": true,
    "tsBuildInfoFile": ".tsbuildinfo",

    // For libs: emit declarations
    "declaration": true,
    "declarationMap": true,  // source maps for declarations
    "sourceMap": true,

    // Skip type checking node_modules (faster)
    "skipLibCheck": true,

    // For bundlers: don't emit
    "noEmit": true,
    "isolatedModules": true  // each file must be a module
  }
}
```

---

## Step 8: Capstone — Show Config

```bash
mkdir -p /lab14final && cd /lab14final
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020"],
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "skipLibCheck": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
EOF

tsc --showConfig --project tsconfig.json
```

📸 **Verified Output:**
```json
{
    "compilerOptions": {
        "target": "es2020",
        "lib": [
            "es2020"
        ],
        "module": "commonjs",
        "moduleResolution": "node",
        "strict": true,
        "esModuleInterop": true,
        "noImplicitReturns": true,
        "noFallthroughCasesInSwitch": true,
        "noUnusedLocals": true,
        "skipLibCheck": true,
        "outDir": "./dist",
        "rootDir": "./src"
    },
    "files": [],
    "include": [
        "src"
    ],
    "exclude": [
        "node_modules",
        "dist"
    ]
}
```

---

## Summary

| Option | Description | Recommended |
|--------|-------------|-------------|
| `target` | JS version to emit | `ES2020` for Node 14+ |
| `module` | Module format | `commonjs` (ts-node), `ESNext` (bundlers) |
| `moduleResolution` | Import resolution | `node` (ts-node), `bundler` (Vite) |
| `strict` | Enable all strict flags | ✅ Always |
| `noUncheckedIndexedAccess` | `arr[0]` = `T \| undefined` | ✅ Recommended |
| `exactOptionalPropertyTypes` | `?:` ≠ `undefined` | Consider |
| `composite` | Enable project references | For monorepos |
| `incremental` | Cache build state | For large projects |
| `skipLibCheck` | Skip node_modules type check | ✅ Usually |
| `isolatedModules` | Each file is a module | For esbuild/swc |
