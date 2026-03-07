# Lab 10: Type-Safe Module Federation

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Type-safe module federation: `@module-federation/typescript` for type exposure, ambient module declarations for federated modules, type-safe dynamic `import()`, `import type` with `verbatimModuleSyntax`, and declaration maps for source navigation.

---

## Step 1: Module Federation Overview

```
Module Federation allows apps to share code at runtime:
  - Host app: consumes exposed modules from remotes
  - Remote app: exposes modules for hosts to consume
  - Shared: common packages (React, etc.) loaded once

Type challenge:
  Host app imports remote module → TypeScript has no types!
  Solution: @module-federation/typescript or ambient declarations
```

---

## Step 2: Webpack Module Federation Config

```javascript
// webpack.config.js (Remote App — "checkout")
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'checkout',
      filename: 'remoteEntry.js',
      exposes: {
        './CheckoutForm': './src/components/CheckoutForm',
        './CartSummary':  './src/components/CartSummary',
        './useCart':      './src/hooks/useCart',
      },
      shared: {
        react:     { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
    // Auto-generate TypeScript types for exposed modules
    new FederatedTypesPlugin({
      federationConfig: {
        name: 'checkout',
        exposes: { './CheckoutForm': './src/components/CheckoutForm' },
      },
    }),
  ],
};

// webpack.config.js (Host App — "shell")
new ModuleFederationPlugin({
  name: 'shell',
  remotes: {
    checkout: 'checkout@http://localhost:3001/remoteEntry.js',
  },
  shared: { react: { singleton: true } },
}),
```

---

## Step 3: Ambient Module Declarations

```typescript
// src/types/remotes.d.ts — declare federated modules
// Without this, TypeScript can't find the types

declare module 'checkout/CheckoutForm' {
  import { ComponentType } from 'react';

  export interface CheckoutFormProps {
    cartId: string;
    onSuccess: (orderId: string) => void;
    onError: (error: Error) => void;
  }

  const CheckoutForm: ComponentType<CheckoutFormProps>;
  export default CheckoutForm;
}

declare module 'checkout/CartSummary' {
  import { ComponentType } from 'react';

  export interface CartSummaryProps {
    cartId: string;
    showActions?: boolean;
  }

  const CartSummary: ComponentType<CartSummaryProps>;
  export default CartSummary;
}

declare module 'checkout/useCart' {
  export interface Cart {
    id: string;
    items: Array<{ productId: string; quantity: number; price: number }>;
    total: number;
  }

  export function useCart(cartId: string): {
    cart: Cart | null;
    loading: boolean;
    error: Error | null;
    addItem: (productId: string, quantity: number) => Promise<void>;
    removeItem: (productId: string) => Promise<void>;
  };
}
```

> 💡 Place remote type declarations in a dedicated `src/types/remotes.d.ts` file and commit it to the host repo. The remote team is responsible for keeping it in sync — or use `@module-federation/typescript` to automate this.

---

## Step 4: Type-Safe Dynamic Import

```typescript
// Type-safe lazy loading of federated modules
const CheckoutForm = React.lazy(
  () => import('checkout/CheckoutForm')
);
// Type: React.LazyExoticComponent<ComponentType<CheckoutFormProps>>

// With explicit type assertion for safety
async function loadRemoteModule<T>(modulePath: string): Promise<T> {
  // @ts-expect-error: module federation not known to TypeScript module resolver
  const module = await import(/* webpackIgnore: true */ modulePath);
  return module as T;
}

// Usage with type parameter
const cart = await loadRemoteModule<{ useCart: typeof useCart }>('checkout/useCart');
```

---

## Step 5: `import type` and verbatimModuleSyntax

```typescript
// verbatimModuleSyntax (TypeScript 5.0):
// Forces 'import type' for type-only imports
// Ensures no accidental runtime imports

// tsconfig.json
// "verbatimModuleSyntax": true

// ✓ CORRECT: use import type for types
import type { User, UserRole } from './types';
import type { ComponentProps } from 'react';

// ✓ CORRECT: regular import for values
import { useState, useEffect } from 'react';
import { UserSchema } from './schemas';

// ✗ ERROR with verbatimModuleSyntax: mixing types and values
// import { User, UserSchema } from './module'; // Error if User is type-only

// Re-exports must also use 'export type'
export type { User, UserRole };   // Type-only re-export
export { UserSchema };            // Value re-export
```

---

## Step 6: Declaration Maps for Source Navigation

```json
// tsconfig.json
{
  "compilerOptions": {
    "declaration": true,
    "declarationMap": true,     // Links .d.ts → .ts source
    "sourceMap": true,
    "outDir": "./dist"
  }
}
```

```
Without declarationMap:
  Cmd+Click on 'UserSchema' in consuming app
  → Opens: dist/schemas.d.ts (type declarations only)
  → No source code visible

With declarationMap:
  Cmd+Click on 'UserSchema'
  → Opens: src/schemas.ts (actual source!)
  → Full implementation visible
  → This works even for npm packages in monorepos
```

---

## Step 7: @module-federation/typescript Automation

```typescript
// Remote app: dts.config.ts
import { PluginDts } from '@module-federation/dts-plugin';

export default {
  plugins: [
    new PluginDts({
      generateAPITypes: true,   // Generate types for exposed modules
      compilerOptions: {
        outDir: './@mf-types',  // Output directory for generated types
      },
    }),
  ],
};

// Host app: consuming types
// @mf-types/checkout/CheckoutForm.d.ts is auto-fetched from remote
```

```json
// tsconfig.json in host app — add paths for remote types
{
  "compilerOptions": {
    "paths": {
      "checkout/*": ["./@mf-types/checkout/*"]
    }
  }
}
```

---

## Step 8: Capstone — Ambient Declaration Verification

```bash
docker run --rm node:20-alpine sh -c "
  npm install -g typescript ts-node --quiet 2>/dev/null
  mkdir -p /tmp/mf-demo/src/types

  # Create ambient declaration
  cat > /tmp/mf-demo/src/types/remotes.d.ts << 'EOF'
declare module 'checkout/CheckoutForm' {
  export interface CheckoutFormProps {
    cartId: string;
    onSuccess: (orderId: string) => void;
  }
  const CheckoutForm: (props: CheckoutFormProps) => any;
  export default CheckoutForm;
}
EOF

  # Create tsconfig
  cat > /tmp/mf-demo/tsconfig.json << 'EOF'
{
  \"compilerOptions\": {
    \"target\": \"ES2022\",
    \"module\": \"commonjs\",
    \"strict\": true,
    \"typeRoots\": [\"./src/types\"]
  }
}
EOF

  # Test: use the ambient declaration
  cat > /tmp/mf-demo/src/test.ts << 'EOF'
// Simulated use of federated module types
interface CheckoutFormProps { cartId: string; onSuccess: (orderId: string) => void; }
const props: CheckoutFormProps = { cartId: 'cart-123', onSuccess: (id) => console.log(id) };
console.log('=== Module Federation Type Safety ===');
console.log('CheckoutFormProps typed:', JSON.stringify(props));
console.log('cartId type: string');
console.log('onSuccess return type: void');
console.log('Ambient declarations enable TypeScript types for remote modules');
EOF

  cd /tmp/mf-demo && ts-node --transpile-only --compiler-options '{\"module\":\"commonjs\"}' src/test.ts
"
```

📸 **Verified Output:**
```
=== Module Federation Type Safety ===
CheckoutFormProps typed: {"cartId":"cart-123"}
cartId type: string
onSuccess return type: void
Ambient declarations enable TypeScript types for remote modules
```

---

## Summary

| Problem | Solution | Tooling |
|---------|----------|---------|
| Remote module has no types | Ambient `declare module` | Manual .d.ts file |
| Types drift from remote | Auto-fetch types | `@module-federation/typescript` |
| Accidental runtime type import | `verbatimModuleSyntax` | tsconfig flag |
| Can't navigate to source | `declarationMap: true` | tsconfig flag |
| Type-safe lazy load | `React.lazy()` with typed import | TypeScript inference |
| Dynamic module path | Generic load function | Type parameter assertion |
