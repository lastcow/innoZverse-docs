# Lab 02: CSS Build Pipeline

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Engineer a production-grade PostCSS pipeline: postcss-preset-env (Stage 2), autoprefixer, cssnano, purgecss, postcss-import, and a custom plugin. Master the entire CSS compilation lifecycle from source to optimized output.

---

## Step 1: Pipeline Architecture

```
src/
├── tokens.css           # Design token definitions
├── base.css             # @import './tokens.css'; reset + base
├── components/
│   ├── button.css
│   └── card.css
└── utilities.css        # Utility classes

postcss build →

dist/
├── bundle.css           # Full build
└── bundle.min.css       # Minified + purged
```

The pipeline stages in order:
1. `postcss-import` — inline all `@import` statements
2. `postcss-preset-env` (Stage 2) — transpile modern CSS
3. `autoprefixer` — add vendor prefixes
4. `purgecss` — remove unused CSS rules
5. `cssnano` — minify + optimize

---

## Step 2: Install and Configure

```bash
npm install --save-dev \
  postcss postcss-cli \
  postcss-import \
  postcss-preset-env \
  autoprefixer \
  @fullhuman/postcss-purgecss \
  cssnano
```

```javascript
// postcss.config.js
const isProd = process.env.NODE_ENV === 'production';

module.exports = {
  plugins: [
    require('postcss-import'),
    require('postcss-preset-env')({
      stage: 2,
      features: {
        'nesting-rules': true,           // CSS Nesting
        'custom-media-queries': true,    // @custom-media
        'media-query-ranges': true,      // @media (width >= 768px)
        'cascade-layers': true,          // @layer
        'custom-properties': false,      // Keep CSS vars native
      },
    }),
    require('autoprefixer'),
    isProd && require('@fullhuman/postcss-purgecss')({
      content: ['./src/**/*.html', './src/**/*.js', './src/**/*.jsx'],
      defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || [],
      safelist: {
        standard: [/^is-/, /^has-/, /^js-/],
        greedy: [/data-state/],
      },
    }),
    isProd && require('cssnano')({
      preset: ['default', {
        discardComments: { removeAll: true },
        normalizeWhitespace: true,
        mergeLonghand: true,
        mergeRules: true,
      }],
    }),
  ].filter(Boolean),
};
```

> 💡 `filter(Boolean)` removes `false` entries from the plugins array — a clean pattern for conditional plugins.

---

## Step 3: Modern CSS Features (Stage 2)

```css
/* src/components/card.css */
@layer components {
  .card {
    /* CSS Nesting (Stage 2 → transpiled) */
    background: var(--color-surface);
    border-radius: clamp(0.25rem, 1vw, 0.5rem);
    padding: var(--spacing-4);
    user-select: none;

    /* Nesting syntax */
    & .card-title {
      font-size: var(--fs-lg);
      color: var(--color-text-primary);
    }

    &:hover {
      box-shadow: var(--shadow-md);
    }

    /* Color function (Stage 2) */
    &[data-variant="featured"] {
      background: color-mix(in oklch, var(--color-primary) 10%, transparent);
    }
  }
}

/* Custom media queries */
@custom-media --mobile (width < 768px);
@custom-media --tablet (768px <= width < 1024px);
@custom-media --desktop (width >= 1024px);

@media (--mobile) {
  .card { padding: var(--spacing-3); }
}
```

---

## Step 4: Custom PostCSS Plugin

```javascript
// plugins/postcss-design-tokens.js
/**
 * Custom PostCSS plugin: replaces design token references
 * Transforms: color(--brand-primary) → var(--ds-color-semantic-brand-primary)
 */
const plugin = (opts = {}) => {
  const prefix = opts.prefix || 'ds';
  const tokenRegex = /color\(--([^)]+)\)/g;

  return {
    postcssPlugin: 'postcss-design-tokens',

    // Walk every declaration
    Declaration(decl) {
      if (tokenRegex.test(decl.value)) {
        decl.value = decl.value.replace(tokenRegex, (match, tokenName) => {
          const cssVar = `--${prefix}-${tokenName.replace(/\./g, '-')}`;
          return `var(${cssVar})`;
        });
      }
    },

    // Walk every rule
    Rule(rule) {
      if (rule.selector.includes('[theme=')) {
        console.log(`  Found themed rule: ${rule.selector}`);
      }
    },

    // Walk every at-rule
    AtRule: {
      // Intercept @ds-include and expand to full token reference
      'ds-include': (atRule) => {
        const component = atRule.params;
        atRule.replaceWith(
          atRule.root().toResult().postcss.rule({
            selector: `.${component}`,
            nodes: [],
          })
        );
      },
    },
  };
};

plugin.postcss = true;
module.exports = plugin;
```

```javascript
// Using the plugin
// postcss.config.js addition:
require('./plugins/postcss-design-tokens')({ prefix: 'ds' }),
```

---

## Step 5: NPM Scripts

```json
{
  "scripts": {
    "css:dev": "postcss src/main.css -o dist/bundle.css --watch",
    "css:build": "NODE_ENV=production postcss src/main.css -o dist/bundle.min.css",
    "css:analyze": "postcss src/main.css -o /dev/null --verbose"
  }
}
```

---

## Step 6: PurgeCSS Configuration

```javascript
// Advanced PurgeCSS for component libraries
require('@fullhuman/postcss-purgecss')({
  content: [
    './src/**/*.{html,js,jsx,ts,tsx,vue,svelte}',
    './node_modules/@company/design-system/dist/**/*.js',
  ],
  // Custom extractor for class-based frameworks
  extractors: [
    {
      extractor: content => {
        // Extract from JSX/TSX className props
        const classNames = content.match(/className=["'`][^"'`]+["'`]/g) || [];
        return classNames.flatMap(c => c.replace(/className=["'`]|["'`]/g, '').split(' '));
      },
      extensions: ['jsx', 'tsx'],
    },
  ],
  safelist: {
    standard: [/^is-/, /^has-/, /^state-/],
    deep: [/tooltip/, /dropdown/],
    greedy: [/\[data-/],
  },
})
```

> 💡 Always test PurgeCSS in staging first — aggressive purging can remove dynamically-added classes. Use `safelist.greedy` for attribute selectors.

---

## Step 7: Bundle Analysis

```javascript
// postcss-stats.js — custom plugin for CSS metrics
const plugin = () => {
  return {
    postcssPlugin: 'postcss-stats',
    OnceExit(root) {
      let rules = 0, decls = 0, selectors = 0;
      root.walkRules(rule => {
        rules++;
        selectors += rule.selectors.length;
      });
      root.walkDecls(decl => { decls++; });
      const bytes = root.toResult().css.length;
      console.log(`
  📊 CSS Bundle Statistics:
    Rules:      ${rules}
    Selectors:  ${selectors}
    Declarations: ${decls}
    Size:       ${(bytes / 1024).toFixed(2)} KB
      `);
    },
  };
};
plugin.postcss = true;
```

---

## Step 8: Capstone — Full Pipeline Verification

```bash
docker run --rm node:20-alpine sh -c "
  cd /app && npm init -y > /dev/null 2>&1
  npm install postcss postcss-preset-env autoprefixer cssnano 2>&1 | tail -1
  node -e \"
const postcss = require('postcss');
const presetEnv = require('postcss-preset-env');
const autoprefixer = require('autoprefixer');
const cssnano = require('cssnano');
const css = ':root{--c:oklch(0.6 0.2 250)}.card{border-radius:clamp(.25rem,1vw,.5rem);user-select:none}';
postcss([presetEnv({stage:2}),autoprefixer,cssnano({preset:'default'})])
  .process(css,{from:undefined})
  .then(r=>{ console.log('=== PostCSS Pipeline Output ==='); console.log(r.css); });
  \"
"
```

📸 **Verified Output:**
```
=== PostCSS Pipeline Output ===
:root{--c:#0083e0}@supports (color:color(display-p3 0 0 0%)){:root{--c:#0083e0}@media (color-gamut:p3){:root{--c:color(display-p3 0.12852 0.49701 0.91316)}}}.card{border-radius:max(.25rem,min(1vw,.5rem));-webkit-user-select:none;-moz-user-select:none;user-select:none}
```

---

## Summary

| Stage | Plugin | Purpose |
|-------|--------|---------|
| Import resolution | `postcss-import` | Inline all `@import` |
| Modern syntax | `postcss-preset-env Stage 2` | Transpile nesting/custom-media |
| Vendor prefixes | `autoprefixer` | `-webkit-`, `-moz-` etc. |
| Dead code removal | `purgecss` | Remove unused selectors |
| Minification | `cssnano` | Compress output |
| Custom transform | DIY plugin | Token replacement |
| Analysis | Custom plugin | Bundle statistics |
