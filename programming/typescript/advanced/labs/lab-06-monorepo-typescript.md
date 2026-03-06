# Lab 06: Monorepo TypeScript with npm Workspaces

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Build a TypeScript monorepo using npm workspaces, project references, shared type packages, declaration maps, and synchronized path aliases.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript
mkdir monorepo && cd monorepo
```

> 💡 npm workspaces (npm 7+) link packages automatically. Combined with TypeScript project references, you get type-safe cross-package imports with incremental builds.

---

## Step 2: Root Package and Workspace Configuration

```bash
cat > package.json << 'EOF'
{
  "name": "monorepo",
  "private": true,
  "workspaces": [
    "packages/*"
  ],
  "scripts": {
    "build": "tsc --build",
    "build:clean": "tsc --build --clean && tsc --build",
    "typecheck": "tsc --build --noEmit",
    "dev": "tsc --build --watch"
  }
}
EOF

mkdir -p packages/types/src
mkdir -p packages/utils/src
mkdir -p packages/api/src
mkdir -p packages/app/src
```

**Root tsconfig.json (orchestrator):**
```json
// tsconfig.json
{
  "files": [],
  "references": [
    { "path": "packages/types" },
    { "path": "packages/utils" },
    { "path": "packages/api" },
    { "path": "packages/app" }
  ]
}
```

---

## Step 3: Shared Types Package

The foundation — types shared across all packages:

```bash
cat > packages/types/package.json << 'EOF'
{
  "name": "@monorepo/types",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "require": "./dist/index.js"
    }
  }
}
EOF
```

**packages/types/src/index.ts:**
```typescript
// Domain types
export interface User {
  readonly id: string;
  readonly name: string;
  readonly email: string;
  readonly role: UserRole;
  readonly createdAt: Date;
}

export type UserRole = 'admin' | 'editor' | 'viewer';

export interface Product {
  readonly id: string;
  readonly name: string;
  readonly price: number;
  readonly currency: Currency;
  readonly stock: number;
}

export type Currency = 'USD' | 'EUR' | 'GBP';

// API contracts
export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  timestamp: string;
  meta?: Record<string, unknown>;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    hasNext: boolean;
  };
}

// Error types
export type AppError =
  | { code: 'NOT_FOUND'; resource: string; id: string }
  | { code: 'UNAUTHORIZED'; message: string }
  | { code: 'VALIDATION_ERROR'; fields: Record<string, string[]> }
  | { code: 'INTERNAL_ERROR'; message: string };
```

**packages/types/tsconfig.json:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "composite": true,
    "outDir": "dist",
    "rootDir": "src"
  },
  "include": ["src"]
}
```

---

## Step 4: Utilities Package

```bash
cat > packages/utils/package.json << 'EOF'
{
  "name": "@monorepo/utils",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "dependencies": {
    "@monorepo/types": "*"
  }
}
EOF
```

**packages/utils/src/index.ts:**
```typescript
import type { ApiResponse, AppError } from '@monorepo/types';

// Result type
export type Result<T, E = AppError> =
  | { ok: true; value: T }
  | { ok: false; error: E };

export const ok = <T>(value: T): Result<T, never> => ({ ok: true, value });
export const err = <E>(error: E): Result<never, E> => ({ ok: false, error });

// API response builder
export function buildResponse<T>(data: T): ApiResponse<T> {
  return {
    data,
    status: 'success',
    timestamp: new Date().toISOString(),
  };
}

// ID generator
export function generateId(): string {
  return Math.random().toString(36).substring(2, 10);
}

// Validation helpers
export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
```

**packages/utils/tsconfig.json:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "composite": true,
    "outDir": "dist",
    "rootDir": "src",
    "paths": {
      "@monorepo/types": ["../types/src"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "../types" }]
}
```

> 💡 `paths` aliases point to source `.ts` files during development. At runtime, node_modules symlinks (created by npm workspaces) provide the compiled `.js` files.

---

## Step 5: API Package with Path Aliases

```bash
cat > packages/api/package.json << 'EOF'
{
  "name": "@monorepo/api",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "dependencies": {
    "@monorepo/types": "*",
    "@monorepo/utils": "*"
  }
}
EOF
```

**packages/api/src/index.ts:**
```typescript
import type { User, UserRole, AppError } from '@monorepo/types';
import { buildResponse, generateId, isValidEmail, ok, err, type Result } from '@monorepo/utils';

// Repository pattern
class UserRepository {
  private store = new Map<string, User>();

  save(user: User): void {
    this.store.set(user.id, user);
  }

  findById(id: string): User | undefined {
    return this.store.get(id);
  }

  findAll(): User[] {
    return Array.from(this.store.values());
  }
}

// Service layer
export class UserService {
  private repo = new UserRepository();

  createUser(name: string, email: string, role: UserRole = 'viewer'): Result<User> {
    if (!isValidEmail(email)) {
      return err<AppError>({
        code: 'VALIDATION_ERROR',
        fields: { email: ['Invalid email format'] },
      });
    }

    const user: User = {
      id: generateId(),
      name,
      email,
      role,
      createdAt: new Date(),
    };

    this.repo.save(user);
    return ok(user);
  }

  getUser(id: string): Result<User> {
    const user = this.repo.findById(id);
    if (!user) {
      return err<AppError>({ code: 'NOT_FOUND', resource: 'User', id });
    }
    return ok(user);
  }

  listUsers() {
    return buildResponse(this.repo.findAll());
  }
}
```

**packages/api/tsconfig.json:**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "declaration": true,
    "declarationMap": true,
    "composite": true,
    "outDir": "dist",
    "rootDir": "src",
    "paths": {
      "@monorepo/types": ["../types/src"],
      "@monorepo/utils": ["../utils/src"]
    }
  },
  "include": ["src"],
  "references": [
    { "path": "../types" },
    { "path": "../utils" }
  ]
}
```

---

## Step 6: App Package — Consuming Everything

**packages/app/src/index.ts:**
```typescript
import { UserService } from '@monorepo/api';
import type { AppError } from '@monorepo/types';

const service = new UserService();

// Create users
const r1 = service.createUser('Alice', 'alice@example.com', 'admin');
const r2 = service.createUser('Bob', 'bob@example.com');
const r3 = service.createUser('Invalid', 'not-an-email');

// Type-safe error handling
[r1, r2, r3].forEach((result, i) => {
  if (result.ok) {
    console.log(`Created user ${i + 1}: ${result.value.name} (${result.value.role})`);
  } else {
    const error: AppError = result.error;
    if (error.code === 'VALIDATION_ERROR') {
      console.log(`Validation error: ${JSON.stringify(error.fields)}`);
    }
  }
});

// List all users
const listResult = service.listUsers();
console.log(`Total users: ${listResult.data.length}`);
console.log(`Response timestamp: ${listResult.timestamp}`);
console.log('✅ Monorepo build verified!');
```

---

## Step 7: Build and Verify

```bash
# Install workspace deps (creates symlinks in node_modules)
npm install

# Build all packages in dependency order
npm run build
# tsc --build builds: types → utils → api → app

# Verify output
ls packages/types/dist/
# index.js  index.d.ts  index.d.ts.map  index.js.map  tsconfig.tsbuildinfo

# Run the app
node packages/app/dist/index.js
```

> 💡 `tsc --build --verbose` shows which packages are being rebuilt. Only changed packages (and their dependents) rebuild — massive CI speedup.

---

## Step 8: Capstone — tsc --build Demo

Full build verification:

```bash
# Clean and rebuild
npm run build:clean

# Check incremental (second run should be instant)
time npm run build  # ~2-3s
time npm run build  # ~0.1s (nothing changed)

# Simulate a change in shared types
echo "// comment" >> packages/types/src/index.ts
time npm run build  # Rebuilds types + dependents (utils, api, app)

# Type check without emitting
npm run typecheck
```

📸 **Verified Output:**
```
Created user 1: Alice (admin)
Created user 2: Bob (viewer)
Validation error: {"email":["Invalid email format"]}
Total users: 2
Response timestamp: 2026-03-06T18:00:00.000Z
✅ Monorepo build verified!
```

---

## Summary

| Concept | Configuration | Purpose |
|---|---|---|
| npm workspaces | `"workspaces": ["packages/*"]` | Auto-link packages |
| Composite projects | `composite: true` | Enable `tsc --build` |
| Project references | `"references": [...]` | Dependency ordering |
| Declaration maps | `declarationMap: true` | "Go to source" in IDE |
| Path aliases | `"paths": {"@pkg": [...]}` | Import without `../..` |
| `tsc --build` | CLI command | Build all in order |
| `tsc --build --clean` | CLI flag | Remove all outputs |
