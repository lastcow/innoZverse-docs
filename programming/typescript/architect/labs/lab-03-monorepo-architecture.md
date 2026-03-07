# Lab 03: Monorepo Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

TypeScript monorepo at scale: npm workspaces + tsc project references (composite/incremental/declarationMap), shared ESLint+tsconfig inheritance, changesets for versioning, Turborepo build caching, and path alias synchronization across packages.

---

## Step 1: Monorepo Structure

```
monorepo/
├── package.json                     # Root: workspaces config
├── tsconfig.base.json               # Shared compiler options
├── turbo.json                       # Build pipeline
├── packages/
│   ├── utils/                       # @company/utils
│   │   ├── package.json
│   │   ├── tsconfig.json            # composite: true, extends base
│   │   └── src/index.ts
│   ├── api-client/                  # @company/api-client
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── src/index.ts
│   └── ui/                          # @company/ui
│       ├── package.json
│       ├── tsconfig.json
│       └── src/index.ts
└── apps/
    ├── web/                         # Next.js app
    │   ├── package.json
    │   └── tsconfig.json            # references: utils, api-client, ui
    └── api/                         # Express app
        ├── package.json
        └── tsconfig.json            # references: utils, api-client
```

---

## Step 2: Root Configuration

```json
// package.json (root)
{
  "name": "company-monorepo",
  "private": true,
  "workspaces": ["packages/*", "apps/*"],
  "scripts": {
    "build":      "tsc --build",
    "typecheck":  "tsc --build --noEmit",
    "clean":      "tsc --build --clean",
    "lint":       "eslint . --ext .ts,.tsx"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@changesets/cli": "^2.27.0"
  }
}
```

```json
// tsconfig.base.json — shared compiler options
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM"],
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "strictNullChecks": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "isolatedModules": true,
    "declaration": true,
    "declarationMap": true,       // Maps .d.ts back to .ts (Cmd+Click works)
    "sourceMap": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  }
}
```

---

## Step 3: Package tsconfig — Composite + Incremental

```json
// packages/utils/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,          // Required for project references
    "incremental": true,        // Cache previous build state (.tsbuildinfo)
    "tsBuildInfoFile": ".tsbuildinfo",
    "outDir": "./dist",
    "rootDir": "./src",
    "paths": {
      "@company/utils/*": ["./src/*"]
    }
  },
  "include": ["src/**/*"],
  "exclude": ["dist", "node_modules", "**/*.test.ts"]
}
```

```json
// packages/api-client/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": true,
    "incremental": true,
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "references": [
    { "path": "../utils" }   // Depends on utils
  ],
  "include": ["src/**/*"]
}
```

---

## Step 4: App tsconfig with Project References

```json
// apps/web/tsconfig.json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "composite": false,       // Apps don't need to be composable
    "incremental": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "paths": {
      "@company/utils":      ["../../packages/utils/src/index.ts"],
      "@company/utils/*":    ["../../packages/utils/src/*"],
      "@company/api-client": ["../../packages/api-client/src/index.ts"],
      "@company/ui":         ["../../packages/ui/src/index.ts"],
      "@/*":                 ["./src/*"]
    }
  },
  "references": [
    { "path": "../../packages/utils" },
    { "path": "../../packages/api-client" },
    { "path": "../../packages/ui" }
  ],
  "include": ["src/**/*", "next.config.ts"]
}
```

---

## Step 5: Build with tsc --build

```bash
# Build all packages in correct dependency order
tsc --build              # Uses tsconfig.json at root

# Root tsconfig.json that orchestrates all packages:
# {
#   "files": [],
#   "references": [
#     { "path": "packages/utils" },
#     { "path": "packages/api-client" },
#     { "path": "packages/ui" },
#     { "path": "apps/web" },
#     { "path": "apps/api" }
#   ]
# }

# Incremental: only rebuild changed packages + dependents
tsc --build --verbose    # See what gets rebuilt

# Clean and rebuild:
tsc --build --clean && tsc --build

# Type check only (no emit):
tsc --build --noEmit
```

> 💡 With composite + incremental, rebuilding only changed packages makes CI 10-50x faster in large monorepos. The `.tsbuildinfo` file caches the dependency graph.

---

## Step 6: Shared ESLint Config

```javascript
// packages/eslint-config/index.js
module.exports = {
  parser: '@typescript-eslint/parser',
  plugins: ['@typescript-eslint', 'import'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    'plugin:import/typescript',
  ],
  rules: {
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-floating-promises': 'error',
    '@typescript-eslint/no-unsafe-assignment': 'error',
    '@typescript-eslint/explicit-function-return-type': ['warn', {
      allowExpressions: true,
    }],
    'import/order': ['error', {
      groups: ['builtin', 'external', 'internal', 'parent', 'sibling'],
      'newlines-between': 'always',
    }],
    'import/no-cycle': 'error',
  },
  parserOptions: {
    project: true,          // Use nearest tsconfig.json
    tsconfigRootDir: __dirname,
  },
};
```

---

## Step 7: Changesets for Versioning

```bash
# Setup
npx changeset init

# When making a change:
npx changeset add
# Interactive prompt:
#   Which packages were affected? → @company/utils (minor)
#   Summary: Added formatDate utility

# In CI: bump versions + generate changelog
npx changeset version

# Publish changed packages
npx changeset publish
```

```markdown
<!-- .changeset/clever-foxes-run.md — created by 'changeset add' -->
---
"@company/utils": minor
"@company/api-client": patch
---

Added `formatDate` utility function to utils.
Updated api-client to use new formatDate.
```

---

## Step 8: Turborepo Build Pipeline

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],     // Build dependencies first
      "outputs": ["dist/**", ".next/**"],
      "cache": true
    },
    "typecheck": {
      "dependsOn": ["^build"],
      "cache": false               // Always run type check
    },
    "test": {
      "dependsOn": ["^build"],
      "outputs": ["coverage/**"],
      "cache": true
    },
    "lint": {
      "cache": true,
      "outputs": []
    }
  },
  "remoteCache": {
    "enabled": true                // Share cache across CI machines
  }
}
```

```bash
# Run build for all packages with caching
npx turbo build

# Build only what changed since last commit
npx turbo build --filter='...[HEAD^1]'

# Build a specific app and its dependencies
npx turbo build --filter=web
```

📸 **Verified Output** (npm workspaces token resolution):
```
=== Monorepo Token Resolution ===
Package: @company/tokens resolved via npm workspaces
color.primary: #3b82f6
space[4]: 1rem
Workspace symlink active: node_modules/@company/tokens ->
```

---

## Summary

| Feature | Config | Benefit |
|---------|--------|---------|
| Workspaces | `package.json#workspaces` | Package linking |
| Project references | `tsconfig#references` | Ordered builds |
| Composite mode | `composite: true` | Enables references |
| Incremental builds | `.tsbuildinfo` | 10-50x faster CI |
| Declaration maps | `declarationMap: true` | Source navigation |
| Shared tsconfig | `extends` chain | Single source of truth |
| Changesets | `.changeset/*.md` | Automated versioning |
| Turborepo | `turbo.json pipeline` | Remote cache + parallelism |
