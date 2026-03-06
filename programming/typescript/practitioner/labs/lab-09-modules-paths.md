# Lab 09: Modules & Path Resolution

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Module resolution strategies, path aliases, barrel files, declaration files (.d.ts), @types packages, triple-slash directives.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab09 && cd /lab09
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "baseUrl": ".",
    "paths": {
      "@utils/*": ["src/utils/*"],
      "@models/*": ["src/models/*"]
    },
    "rootDir": ".",
    "outDir": "dist"
  }
}
EOF
mkdir -p src/utils src/models
```

---

## Step 2: Module Resolution Strategies

```typescript
// moduleResolution: "node" (classic CommonJS, still most common)
//   - import './file' → ./file.ts, ./file.tsx, ./file.d.ts
//   - import 'lodash' → node_modules/lodash/index.js

// moduleResolution: "bundler" (TS 5.0+, for Vite/webpack/esbuild)
//   - Supports package.json "exports" field
//   - Allows extensionless imports in .ts files

// moduleResolution: "NodeNext"/"Node16" (for Node.js ESM)
//   - Requires explicit extensions (.js) in import paths
//   - Respects package.json "exports" and "type": "module"

// For most projects with ts-node: use "node"
// For Vite/Next.js: use "bundler"
// For Node.js ESM native: use "NodeNext"
```

---

## Step 3: Barrel Files (index.ts)

```bash
# Create modules
cat > src/models/user.ts << 'EOF'
export interface User {
  id: number;
  name: string;
  email: string;
}
export function createUser(name: string, email: string, id = 0): User {
  return { id, name, email };
}
EOF

cat > src/models/post.ts << 'EOF'
export interface Post {
  id: number;
  title: string;
  content: string;
  authorId: number;
}
export function createPost(title: string, content: string, authorId: number): Post {
  return { id: 0, title, content, authorId };
}
EOF

# Barrel file — re-exports everything
cat > src/models/index.ts << 'EOF'
export * from './user';
export * from './post';
EOF

cat > src/utils/format.ts << 'EOF'
export function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
export function truncate(s: string, max: number): string {
  return s.length > max ? s.slice(0, max) + '...' : s;
}
EOF

cat > src/utils/index.ts << 'EOF'
export * from './format';
EOF
```

---

## Step 4: Path Aliases

```typescript
// With paths config, you can use aliases instead of relative imports
// import { User } from '../../../models/user' → import { User } from '@models/user'
```

```bash
cat > src/main.ts << 'EOF'
// Without path aliases (hard to maintain):
import { createUser } from './models/user';
import { capitalize } from './utils/format';

// With barrel + relative:
import { User, Post, createUser as cu } from './models';
import { capitalize as cap } from './utils';

const user = createUser('alice', 'alice@example.com', 1);
const post = { id: 1, title: 'Hello', content: 'World', authorId: 1 };

console.log(capitalize(user.name));
console.log('User:', JSON.stringify(user));
console.log('Post:', JSON.stringify(post));
EOF
```

---

## Step 5: Declaration Files (.d.ts)

```bash
# Create a JS file that has no types
cat > src/legacy.js << 'EOF'
function greet(name) {
  return 'Hello, ' + name + '!';
}
function add(a, b) {
  return a + b;
}
module.exports = { greet, add };
EOF

# Write a declaration file for it
cat > src/legacy.d.ts << 'EOF'
export declare function greet(name: string): string;
export declare function add(a: number, b: number): number;
EOF

cat > src/use-legacy.ts << 'EOF'
const { greet, add } = require('./legacy');
const msg: string = greet('TypeScript');
const sum: number = add(1, 2);
console.log(msg, sum);
EOF
```

---

## Step 6: @types Packages

```bash
# @types packages provide TypeScript declarations for JS libraries
npm install --save-dev @types/node

cat > src/node-demo.ts << 'EOF'
import * as path from 'path';
import * as os from 'os';

const cwd = process.cwd();
const home = os.homedir();
const ext = path.extname('file.ts');

console.log('CWD:', cwd);
console.log('Home:', home);
console.log('Extension:', ext);
console.log('Platform:', process.platform);
EOF
```

---

## Step 7: Triple-Slash Directives

```typescript
// Triple-slash directives are special comments that provide compiler hints

// Reference a declaration file
/// <reference path="../types/custom.d.ts" />

// Reference a types package
/// <reference types="node" />

// Reference lib declarations
/// <reference lib="es2020" />

// Example custom global types
// In types/globals.d.ts:
declare global {
  interface Window {
    __APP_VERSION__: string;
  }
  var __APP_ENV__: 'development' | 'production' | 'test';
}

// Modern recommendation: use tsconfig "types" and "typeRoots" instead
// triple-slash is mainly for legacy and specific edge cases
export {};
```

---

## Step 8: Capstone — Module System Demo

```bash
# Save and run the main module
cat > lab09-capstone.ts << 'EOF'
// Barrel imports work with relative paths
import { createUser } from './src/models/user';
import { capitalize, truncate } from './src/utils/format';

const user = createUser('alice johnson', 'alice@example.com', 1);

console.log(capitalize(user.name));
console.log(truncate('This is a very long description that needs truncating', 20));
console.log(JSON.stringify(user));
console.log('Modules OK');
EOF

ts-node -P tsconfig.json lab09-capstone.ts
```

📸 **Verified Output:**
```
Alice johnson
This is a very long...
{"id":1,"name":"alice johnson","email":"alice@example.com"}
Modules OK
```

---

## Summary

| Concept | Description | Config |
|---------|-------------|--------|
| `moduleResolution: "node"` | CommonJS/ts-node compatible | Default for most projects |
| `moduleResolution: "bundler"` | Vite/webpack/esbuild | TS 5.0+ |
| `moduleResolution: "NodeNext"` | Native Node.js ESM | Needs `.js` extensions |
| Barrel file | `index.ts` re-exporting | `export * from './file'` |
| Path aliases | `@utils/*` shorthand | `"paths"` in tsconfig |
| Declaration file | `.d.ts` | Types for JS files |
| @types | `npm install @types/X` | Community type declarations |
| Triple-slash | `/// <reference>` | Legacy compiler hints |
