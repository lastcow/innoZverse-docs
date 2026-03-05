# Lab 12: Monorepo Tooling

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Manage monorepos with npm/yarn/pnpm workspaces, Turborepo concepts, shared packages, dependency hoisting, `publishConfig`, and changesets for versioning.

---

## Step 1: npm Workspaces Setup

```bash
# Create monorepo structure
mkdir /app/monorepo && cd /app/monorepo

# Root package.json with workspaces
cat > package.json << 'EOF'
{
  "name": "my-monorepo",
  "version": "1.0.0",
  "private": true,
  "workspaces": [
    "packages/*",
    "apps/*"
  ],
  "scripts": {
    "build": "npm run build --workspaces",
    "test": "npm run test --workspaces --if-present",
    "lint": "npm run lint --workspaces --if-present"
  }
}
EOF

# Create workspace directories
mkdir -p packages/utils packages/ui apps/web apps/api
```

---

## Step 2: Shared Package Structure

```javascript
// packages/utils/package.json
{
  "name": "@my-mono/utils",
  "version": "1.0.0",
  "main": "./dist/index.js",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./string": {
      "import": "./dist/string.mjs",
      "require": "./dist/string.js"
    }
  },
  "files": ["dist"],
  "scripts": {
    "build": "tsc && node scripts/build-esm.js",
    "test": "jest"
  },
  "publishConfig": {
    "access": "public",
    "registry": "https://registry.npmjs.org"
  }
}

// packages/utils/src/index.js
export * from './string.js';
export * from './array.js';
export * from './object.js';
export * from './async.js';

// packages/utils/src/string.js
export const capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);
export const camelToKebab = s => s.replace(/[A-Z]/g, l => `-${l.toLowerCase()}`);
export const truncate = (s, n, suffix = '...') =>
  s.length > n ? s.slice(0, n - suffix.length) + suffix : s;

// packages/utils/src/array.js
export const unique = arr => [...new Set(arr)];
export const chunk = (arr, size) =>
  Array.from({ length: Math.ceil(arr.length / size) }, (_, i) =>
    arr.slice(i * size, (i + 1) * size)
  );
export const groupBy = (arr, keyFn) =>
  arr.reduce((groups, item) => {
    const key = typeof keyFn === 'function' ? keyFn(item) : item[keyFn];
    (groups[key] = groups[key] || []).push(item);
    return groups;
  }, {});
```

---

## Step 3: Consuming Shared Packages

```javascript
// apps/api/package.json
{
  "name": "@my-mono/api",
  "version": "1.0.0",
  "dependencies": {
    "@my-mono/utils": "workspace:*",  // pnpm syntax
    // OR
    "@my-mono/utils": "*"             // npm/yarn workspaces
  }
}

// apps/api/src/server.js
const { capitalize, chunk, groupBy } = require('@my-mono/utils');

// Works because npm workspaces creates symlinks in node_modules
console.log(capitalize('hello')); // Hello
console.log(chunk([1,2,3,4,5], 2)); // [[1,2],[3,4],[5]]
```

---

## Step 4: Dependency Hoisting

```
# Hoisted structure (default behavior)
monorepo/
  node_modules/
    express/           # Shared by all packages
    lodash/            # Hoisted to root
    @my-mono/utils/    # Symlink to packages/utils
  packages/
    utils/
      node_modules/
        # Only package-specific deps that conflict go here
  apps/
    api/
      node_modules/
        # Only if version conflict with root
```

```javascript
// .npmrc — control hoisting
// hoist=true (default)
// hoist-pattern[]=*  # What to hoist
// public-hoist-pattern[]=*eslint*  # pnpm: hoist eslint to root

// package.json — nohoist (yarn workspaces)
{
  "workspaces": {
    "packages": ["packages/*", "apps/*"],
    "nohoist": ["**/webpack", "**/webpack/**"]
  }
}
```

---

## Step 5: Turborepo Concepts

```javascript
// turbo.json — Turborepo pipeline configuration
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],  // Build deps first (^=upstream)
      "outputs": ["dist/**", ".next/**"],
      "cache": true
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"],
      "cache": true
    },
    "lint": {
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}

// Commands
// turbo build          -- build all packages in dependency order
// turbo build --filter=@my-mono/api  -- build only api (+ deps)
// turbo build --filter=...@my-mono/utils  -- build all dependents of utils
// turbo build --dry-run  -- show what would run
// turbo build --force    -- ignore cache

// Benefits:
// 1. Incremental builds — only rebuild changed packages
// 2. Remote caching — share build cache across CI machines
// 3. Parallel execution — run independent tasks simultaneously
// 4. Smart task ordering — respect inter-package dependencies
```

---

## Step 6: Changesets for Versioning

```bash
# Setup changesets
npm install -D @changesets/cli
npx changeset init

# .changeset/config.json (generated)
{
  "$schema": "https://unpkg.com/@changesets/config@2.3.0/schema.json",
  "changelog": "@changesets/cli/changelog",
  "commit": false,
  "fixed": [],
  "linked": [],
  "access": "restricted",  // or "public"
  "baseBranch": "main",
  "updateInternalDependencies": "patch",
  "ignore": []
}

# Workflow:
# 1. Make changes to packages
# 2. npx changeset      -- interactive: select packages + bump type
# 3. npx changeset version -- bump versions, update CHANGELOG.md
# 4. git add && git commit -m "Version packages"
# 5. npx changeset publish -- publish to npm

# .changeset/my-change.md (generated by `npx changeset`)
---
"@my-mono/utils": minor
"@my-mono/api": patch
---

Add groupBy to utils, fix route handler
```

---

## Step 7: npm Workspaces Demo

```bash
# Demonstrate workspaces in Docker
docker run --rm node:20-alpine sh -c "
cd /tmp
mkdir -p monorepo/packages/utils monorepo/packages/math monorepo/apps/cli

# Root package.json
cat > monorepo/package.json << 'EOF'
{\"name\":\"mono\",\"private\":true,\"workspaces\":[\"packages/*\",\"apps/*\"]}
EOF

# Utils package
cat > monorepo/packages/utils/package.json << 'EOF'
{\"name\":\"@mono/utils\",\"version\":\"1.0.0\",\"main\":\"index.js\"}
EOF
cat > monorepo/packages/utils/index.js << 'EOF'
exports.capitalize = s => s.charAt(0).toUpperCase() + s.slice(1);
exports.chunk = (arr, n) => Array.from({length: Math.ceil(arr.length/n)}, (_,i) => arr.slice(i*n, (i+1)*n));
EOF

# Math package
cat > monorepo/packages/math/package.json << 'EOF'
{\"name\":\"@mono/math\",\"version\":\"1.0.0\",\"main\":\"index.js\"}
EOF
cat > monorepo/packages/math/index.js << 'EOF'
exports.sum = arr => arr.reduce((a,b)=>a+b, 0);
exports.avg = arr => exports.sum(arr) / arr.length;
EOF

# CLI app
cat > monorepo/apps/cli/package.json << 'EOF'
{\"name\":\"@mono/cli\",\"version\":\"1.0.0\",\"dependencies\":{\"@mono/utils\":\"*\",\"@mono/math\":\"*\"}}
EOF
cat > monorepo/apps/cli/index.js << 'EOF'
const { capitalize, chunk } = require('@mono/utils');
const { sum, avg } = require('@mono/math');
console.log(capitalize('hello monorepo'));
console.log(chunk([1,2,3,4,5], 2));
const nums = [10, 20, 30, 40, 50];
console.log('Sum:', sum(nums), 'Avg:', avg(nums));
EOF

cd monorepo && npm install --workspaces --silent 2>/dev/null
node apps/cli/index.js
"
```

---

## Step 8: Capstone — Workspace Demo

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && mkdir -p monorepo/packages/utils monorepo/apps/cli

cat > /tmp/monorepo/package.json << 'EOF'
{\"name\":\"mono\",\"private\":true,\"workspaces\":[\"packages/*\",\"apps/*\"]}
EOF
echo '{\"name\":\"@mono/utils\",\"version\":\"1.0.0\",\"main\":\"index.js\"}' > /tmp/monorepo/packages/utils/package.json
echo 'exports.capitalize = s => s[0].toUpperCase() + s.slice(1); exports.unique = arr => [...new Set(arr)];' > /tmp/monorepo/packages/utils/index.js
echo '{\"name\":\"@mono/cli\",\"version\":\"1.0.0\",\"dependencies\":{\"@mono/utils\":\"*\"}}' > /tmp/monorepo/apps/cli/package.json
echo 'const {capitalize, unique} = require(\"@mono/utils\"); console.log(capitalize(\"hello\")); console.log(unique([1,2,2,3,3,4]));' > /tmp/monorepo/apps/cli/index.js

cd /tmp/monorepo && npm install --workspaces --silent 2>/dev/null
node apps/cli/index.js
"
```

📸 **Verified Output:**
```
Hello
[ 1, 2, 3, 4 ]
```

---

## Summary

| Tool | Config File | Key Feature |
|------|-------------|-------------|
| npm workspaces | `"workspaces"` in package.json | Built-in, symlinks |
| yarn workspaces | Same + `.yarnrc.yml` | Faster installs |
| pnpm workspaces | `pnpm-workspace.yaml` | Strict linking, disk efficient |
| Turborepo | `turbo.json` | Incremental builds, remote cache |
| Changesets | `.changeset/config.json` | Versioning + CHANGELOG |
| `publishConfig` | In package.json | Override publish settings |
| `workspace:*` | Dependency version | pnpm workspace reference |
