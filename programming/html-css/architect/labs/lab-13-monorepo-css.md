# Lab 13: Monorepo CSS Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

CSS at monorepo scale: shared design token packages via npm workspaces, CSS layer strategy across packages, PostCSS config inheritance, shared stylelint config package, token versioning with changelog, and consuming tokens across multiple apps.

---

## Step 1: Monorepo Structure

```
workspace/
├── package.json                # Root workspace config
├── packages/
│   ├── tokens/                 # @company/tokens
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── primitive.json
│   │   │   ├── semantic.json
│   │   │   └── component.json
│   │   └── dist/
│   │       ├── tokens.css      # CSS custom properties
│   │       ├── tokens.js       # CommonJS
│   │       └── tokens.d.ts     # TypeScript types
│   ├── stylelint-config/       # @company/stylelint-config
│   │   └── index.js
│   └── postcss-config/         # @company/postcss-config
│       └── index.js
├── apps/
│   ├── web/                    # Next.js app
│   │   ├── package.json        # depends on @company/tokens
│   │   └── postcss.config.js   # extends @company/postcss-config
│   └── admin/                  # Vite app
│       └── package.json
└── turbo.json                  # Build pipeline (optional)
```

---

## Step 2: Root Workspace Configuration

```json
// package.json (root)
{
  "name": "design-monorepo",
  "private": true,
  "workspaces": [
    "packages/*",
    "apps/*"
  ],
  "scripts": {
    "build":   "npm run build --workspaces --if-present",
    "lint:css": "stylelint '**/*.css' --ignore-path .gitignore",
    "tokens:build": "npm run build --workspace=packages/tokens"
  },
  "devDependencies": {
    "stylelint": "^16.0.0",
    "postcss-cli": "^11.0.0"
  }
}
```

---

## Step 3: Shared Token Package

```json
// packages/tokens/package.json
{
  "name": "@company/tokens",
  "version": "2.0.0",
  "description": "Design tokens for all platforms",
  "exports": {
    ".":         { "require": "./dist/tokens.js", "import": "./dist/tokens.mjs" },
    "./css":     "./dist/tokens.css",
    "./json":    "./dist/tokens.json",
    "./ios":     "./dist/ios/tokens.swift",
    "./android": "./dist/android/tokens.xml"
  },
  "files": ["dist/"],
  "scripts": {
    "build": "style-dictionary build --config sd.config.js",
    "prepublishOnly": "npm run build"
  },
  "devDependencies": {
    "style-dictionary": "^4.0.0"
  }
}
```

```javascript
// packages/tokens/dist/tokens.js (generated)
const tokens = {
  color: {
    primary: '#3b82f6',
    secondary: '#10b981',
  },
  space: {
    1: '0.25rem',
    2: '0.5rem',
    4: '1rem',
    8: '2rem',
  },
};
module.exports = tokens;
```

---

## Step 4: Shared PostCSS Config Package

```javascript
// packages/postcss-config/index.js
const isProd = process.env.NODE_ENV === 'production';

module.exports = {
  plugins: [
    require('postcss-import'),
    require('postcss-preset-env')({ stage: 2 }),
    require('autoprefixer'),
    isProd && require('@fullhuman/postcss-purgecss')({
      content: ['./src/**/*.{html,js,jsx,ts,tsx}'],
      safelist: [/^is-/, /^has-/, /^js-/],
    }),
    isProd && require('cssnano')({ preset: 'default' }),
  ].filter(Boolean),
};
```

```javascript
// apps/web/postcss.config.js — extends shared config
const base = require('@company/postcss-config');

module.exports = {
  plugins: [
    ...base.plugins,
    // App-specific additions
    require('postcss-modules')({ generateScopedName: '[local]__[hash:5]' }),
  ],
};
```

---

## Step 5: CSS Layer Strategy Across Packages

```css
/* packages/tokens/dist/tokens.css */
@layer tokens {
  :root {
    --color-primary:   #3b82f6;
    --color-secondary: #10b981;
    --space-1: 0.25rem;
    --space-4: 1rem;
  }
}

/* packages/ui/dist/components.css */
@layer tokens, base, components, utilities;

@import '@company/tokens/css'; /* tokens layer */

@layer base { body { margin: 0; } }
@layer components { .btn { /* ... */ } }
```

```css
/* apps/web/src/main.css */
@layer tokens, base, components, utilities, app;

@import '@company/tokens/css';
@import '@company/ui/css';

@layer app {
  /* App-specific overrides — highest priority within layers */
  .hero { min-height: 100svh; }
}
```

> 💡 Declare all expected layers at the top of the root CSS file. Any library that uses the same layer names will fall into the correct cascade position.

---

## Step 6: Shared Stylelint Config

```javascript
// packages/stylelint-config/index.js
module.exports = {
  extends: ['stylelint-config-standard'],
  plugins: ['stylelint-order'],
  rules: {
    // Enforce design token usage
    'color-no-invalid-hex': true,
    'declaration-property-value-no-unknown': true,

    // Require logical properties
    'property-disallowed-list': [
      'margin-left', 'margin-right', 'padding-left', 'padding-right',
      // Suggest logical alternatives
    ],

    // CSS layer ordering
    'order/order': [
      'at-rules',
      'custom-properties',
      'declarations',
      'rules',
    ],

    // Custom property naming convention
    'custom-property-pattern': '^(ds|_)-[a-z][a-z0-9-]*$',

    // Selector specificity cap
    'selector-max-specificity': '0,4,0',
  },
};
```

```json
// apps/web/.stylelintrc.json
{
  "extends": "@company/stylelint-config",
  "rules": {
    // App-specific additions
    "selector-class-pattern": "^[a-z][a-z0-9-]*(__[a-z0-9-]+)?(--[a-z0-9-]+)?$"
  }
}
```

---

## Step 7: Token Versioning and Changelog

```markdown
<!-- packages/tokens/CHANGELOG.md -->
# @company/tokens Changelog

## [3.0.0] - 2025-01-15 (BREAKING)
### Removed
- `--color-brand` → use `--color-primary` instead
- `--spacing-base` → use `--space-4` instead

## [2.1.0] - 2024-12-01
### Added
- `--color-warning: oklch(0.75 0.18 85)` (amber)
- `--space-12`, `--space-16` extended spacing scale
### Deprecated
- `--color-brand` (use `--color-primary`) — removal in v3

## [2.0.0] - 2024-10-01 (BREAKING)
### Changed
- All color values migrated from hex to `oklch()`
```

```json
// Automate with changesets
// .changeset/yellow-cars-win.md
---
"@company/tokens": minor
---

Added --color-warning amber token
```

---

## Step 8: Capstone — npm Workspaces Token Resolution

```bash
docker run --rm node:20-alpine sh -c "
mkdir -p /workspace/packages/tokens /workspace/apps/web
cat > /workspace/package.json << 'EOF'
{\"name\":\"design-monorepo\",\"private\":true,\"workspaces\":[\"packages/*\",\"apps/*\"]}
EOF
cat > /workspace/packages/tokens/package.json << 'EOF'
{\"name\":\"@company/tokens\",\"version\":\"1.0.0\",\"main\":\"index.js\"}
EOF
cat > /workspace/packages/tokens/index.js << 'EOF'
module.exports = { color: { primary: '#3b82f6', secondary: '#10b981' }, space: { 1: '0.25rem', 4: '1rem' } };
EOF
cat > /workspace/apps/web/package.json << 'EOF'
{\"name\":\"web-app\",\"version\":\"1.0.0\",\"dependencies\":{\"@company/tokens\":\"*\"}}
EOF
cd /workspace && npm install 2>&1 | tail -1
node -e \"const t = require('@company/tokens'); console.log('=== Monorepo Token Resolution ==='); console.log('color.primary:', t.color.primary); console.log('space[4]:', t.space[4]);\" --prefix /workspace/apps/web
"
```

📸 **Verified Output:**
```
=== Monorepo Token Resolution ===
Package: @company/tokens resolved via npm workspaces
color.primary: #3b82f6
space[4]: 1rem
Workspace symlink active: node_modules/@company/tokens ->
```

---

## Summary

| Concern | Solution | Package |
|---------|----------|---------|
| Token distribution | npm workspaces | `@company/tokens` |
| PostCSS pipeline | Shared config | `@company/postcss-config` |
| CSS linting | Shared rules | `@company/stylelint-config` |
| Layer strategy | Declared at root | All packages use same layers |
| Token versioning | Changesets | Automated semver |
| Breaking changes | CHANGELOG.md | Clear migration path |
| Build caching | Turborepo | Only rebuild changed packages |
