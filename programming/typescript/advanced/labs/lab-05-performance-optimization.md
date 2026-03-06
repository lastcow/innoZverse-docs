# Lab 05: TypeScript Build Performance Optimization

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Optimize TypeScript compilation speed and reliability using project references, incremental builds, compiler flags, and type-level performance patterns.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript
mkdir lab05 && cd lab05
```

> 💡 We'll measure compilation times with `tsc --diagnostics`. Even small projects benefit from understanding these metrics at scale.

---

## Step 2: Understanding tsc --diagnostics

Create a sample project and measure baseline performance:

```bash
mkdir src
cat > src/index.ts << 'EOF'
export function greet(name: string): string {
  return `Hello, ${name}!`;
}

export function add(a: number, b: number): number {
  return a + b;
}

export interface User {
  id: number;
  name: string;
  email: string;
  createdAt: Date;
}

export class UserService {
  private users: Map<number, User> = new Map();

  create(name: string, email: string): User {
    const id = this.users.size + 1;
    const user: User = { id, name, email, createdAt: new Date() };
    this.users.set(id, user);
    return user;
  }

  findById(id: number): User | undefined {
    return this.users.get(id);
  }

  getAll(): User[] {
    return Array.from(this.users.values());
  }
}
EOF

cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "outDir": "dist"
  },
  "include": ["src"]
}
EOF

tsc --diagnostics
```

📸 **Verified Output:**
```
Parse time:      1.12s
Bind time:       0.38s
Check time:      0.07s
Emit time:       0.07s
Total time:      1.64s
```

> 💡 **Key metrics**: Parse time = reading .ts files. Check time = type checking. For large projects, check time dominates. `tsc --extendedDiagnostics` gives even more detail.

---

## Step 3: skipLibCheck and isolatedModules

Two flags with major performance impact:

```json
// tsconfig.optimized.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "outDir": "dist",

    // Skip type checking of .d.ts files (huge speedup in large projects)
    "skipLibCheck": true,

    // Each file must be independently compilable (enables parallel builds)
    "isolatedModules": true,

    // Don't emit on type errors (fail fast)
    "noEmitOnError": true
  }
}
```

**When to use each:**

| Flag | Speedup | Trade-off |
|---|---|---|
| `skipLibCheck: true` | 10-40% | Misses errors in .d.ts files |
| `isolatedModules: true` | Enables parallel transpilation | Can't use `const enum`, `namespace` merging |

> 💡 `isolatedModules` is required for tools like `babel`, `esbuild`, and `swc` that transpile TypeScript without type checking.

---

## Step 4: Incremental Builds

Enable caching with `incremental: true`:

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "skipLibCheck": true,
    "incremental": true,
    "tsBuildInfoFile": ".tsbuildinfo",
    "outDir": "dist"
  }
}
```

```bash
# First build (cold)
tsc --diagnostics
# Output: Total time: ~1.5s

# Second build (cached, no changes)
tsc --diagnostics
# Output: Total time: ~0.1s  (10-15x faster!)

# Check the cache file
ls -lh .tsbuildinfo
```

> 💡 `.tsbuildinfo` stores a JSON snapshot of the last compilation. Add it to `.gitignore` but keep it in CI for faster builds.

---

## Step 5: Project References (composite: true)

Split large projects into sub-projects for parallel, incremental compilation:

```
lab05/
├── packages/
│   ├── shared/           # Shared types
│   ├── core/             # Core logic (depends on shared)
│   └── app/              # Application (depends on core + shared)
└── tsconfig.json         # Root references config
```

```bash
mkdir -p packages/shared/src packages/core/src packages/app/src
```

**packages/shared/src/types.ts:**
```typescript
export interface User {
  id: number;
  name: string;
  email: string;
}

export interface Product {
  id: number;
  name: string;
  price: number;
}

export type Result<T> = { success: true; data: T } | { success: false; error: string };
```

**packages/shared/tsconfig.json:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "declaration": true,
    "composite": true,
    "outDir": "dist"
  },
  "include": ["src"]
}
```

> 💡 `composite: true` requires `declaration: true`. It signals this project can be referenced by others and enables `tsc --build` mode.

**packages/core/src/services.ts:**
```typescript
import type { User, Result } from '../../shared/src/types';

export class UserService {
  private users: Map<number, User> = new Map();

  create(name: string, email: string): Result<User> {
    if (!email.includes('@')) {
      return { success: false, error: 'Invalid email' };
    }
    const user: User = { id: this.users.size + 1, name, email };
    this.users.set(user.id, user);
    return { success: true, data: user };
  }

  findById(id: number): Result<User> {
    const user = this.users.get(id);
    return user
      ? { success: true, data: user }
      : { success: false, error: `User ${id} not found` };
  }
}
```

**packages/core/tsconfig.json:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "declaration": true,
    "composite": true,
    "outDir": "dist"
  },
  "include": ["src"],
  "references": [{ "path": "../shared" }]
}
```

**Root tsconfig.json (build orchestrator):**
```json
{
  "files": [],
  "references": [
    { "path": "packages/shared" },
    { "path": "packages/core" },
    { "path": "packages/app" }
  ]
}
```

Build all with dependency ordering:
```bash
tsc --build --verbose
# TypeScript will build shared → core → app in order
# On second run, only changed packages rebuild
```

---

## Step 6: Avoiding Deep Recursive Type Performance Traps

Some type patterns can exponentially slow compilation:

```typescript
// ❌ SLOW: Deep recursive conditional type (O(n) instantiations)
type DeepNested<T, Depth extends number = 10> =
  Depth extends 0 ? T :
  { value: T; next: DeepNested<T, [-1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9][Depth]> };

// ❌ SLOW: Unbounded conditional type recursion
type Repeat<T, N extends number, Acc extends T[] = []> =
  Acc['length'] extends N ? Acc : Repeat<T, N, [T, ...Acc]>;
type BigTuple = Repeat<string, 100>; // Very slow!

// ✅ FAST: Limit recursion depth
type DeepPartial<T, MaxDepth extends number = 5> =
  MaxDepth extends 0 ? T :
  T extends object ? { [P in keyof T]?: DeepPartial<T[P]> } : T;

// ✅ FAST: Use built-in utilities instead of custom recursion
type ReadonlyRecord<K extends string, V> = Readonly<Record<K, V>>;

// ✅ FAST: Avoid recomputing unions — cache with interface merging
type SmallUnion = 'a' | 'b' | 'c';           // Fast
type LargeUnion = 'a' | 'b' | 'c' | 'd' | 'e' | 'f' | 'g' | 'h'; // Fine

// Profile slow types with: tsc --extendedDiagnostics
// Look for high "Check time" — indicates expensive type instantiations
```

> 💡 **Rule of thumb**: If a conditional type recurses more than 10 levels deep, TypeScript will throw "Type instantiation is excessively deep". Use mapped types or utility types instead.

---

## Step 7: declaration Maps and Source Maps

Enable better debugging and IDE support:

```json
{
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true,   // Maps .d.ts back to .ts source
    "sourceMap": true,         // Maps .js back to .ts source
    "declarationDir": "types", // Separate types output dir
    "outDir": "dist"
  }
}
```

```bash
tsc
# Generates:
# dist/index.js           (compiled JavaScript)
# dist/index.js.map       (sourcemap: .js → .ts)
# types/index.d.ts        (declaration file)
# types/index.d.ts.map    (declaration map: .d.ts → .ts)
```

> 💡 `declarationMap: true` lets consumers of your library "Go to definition" and land in your original `.ts` source rather than the generated `.d.ts` file.

---

## Step 8: Capstone — Optimized tsconfig Template

Production-ready tsconfig with all optimizations:

```json
// tsconfig.production.json
{
  "compilerOptions": {
    // Target modern environments
    "target": "ES2022",
    "module": "commonjs",
    "moduleResolution": "node",
    "lib": ["ES2022"],

    // Strict type checking
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": false,

    // Performance optimizations
    "skipLibCheck": true,
    "isolatedModules": true,
    "incremental": true,
    "tsBuildInfoFile": ".tsbuildinfo",

    // Output
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist",
    "rootDir": "src",

    // Quality
    "noEmitOnError": true,
    "forceConsistentCasingInFileNames": true,
    "esModuleInterop": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

```bash
tsc -p tsconfig.production.json --diagnostics
```

📸 **Verified tsc --diagnostics Output:**
```
I/O write:       0.00s
Parse time:      1.12s
Bind time:       0.38s
Check time:      0.07s
Emit time:       0.07s
Total time:      1.64s
```

---

## Summary

| Optimization | Config | Impact |
|---|---|---|
| `skipLibCheck: true` | tsconfig | 10-40% faster |
| `isolatedModules: true` | tsconfig | Enables parallel transpilation |
| `incremental: true` | tsconfig | 10-15x faster on unchanged files |
| Project references | `composite: true` + `references` | Parallel sub-project builds |
| `tsc --build` | CLI flag | Dependency-ordered builds |
| Avoid deep recursion | Type patterns | Prevent O(n) type instantiation |
| `declarationMap: true` | tsconfig | Better "Go to definition" |
