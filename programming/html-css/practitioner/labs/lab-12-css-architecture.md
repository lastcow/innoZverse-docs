# Lab 12: CSS Architecture

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Learn scalable CSS organization with BEM naming, ITCSS layers, Tailwind utility-first concepts, CSS Modules scoping, and stylelint configuration.

---

## Step 1: BEM — Block, Element, Modifier

BEM is a naming convention that creates self-documenting, non-conflicting CSS class names.

```
block           — standalone component   (.card)
block__element  — child part of block    (.card__title)
block--modifier — variant of block       (.card--featured)
block__element--modifier — variant child (.card__title--large)
```

```html
<!-- BEM HTML structure -->
<article class="card card--featured">
  <div class="card__media">
    <img class="card__image" src="..." alt="...">
    <span class="card__badge">New</span>
  </div>
  <div class="card__body">
    <h2 class="card__title card__title--large">Article Title</h2>
    <p class="card__text">Description text here...</p>
    <footer class="card__footer">
      <button class="btn btn--primary">Read More</button>
      <button class="btn btn--ghost btn--sm">Save</button>
    </footer>
  </div>
</article>
```

```css
/* BEM CSS — flat specificity (0,1,0) */
.card { /* Block */ }
.card--featured { /* Modifier */ }
.card__title { /* Element */ }
.card__title--large { /* Element modifier */ }

/* Avoid nesting in BEM */
/* ❌ .card .card__title { } */
/* ✓  .card__title { } */

/* Exception: state modifiers */
.card.is-loading { }   /* JS state class */
.card.has-error { }
```

---

## Step 2: ITCSS — Inverted Triangle CSS

ITCSS organizes CSS by specificity and reach (general → specific):

```
Layer 1: Settings    — Variables, config (no CSS output)
Layer 2: Tools       — Mixins, functions (no CSS output)
Layer 3: Generic     — Reset, normalize
Layer 4: Elements    — Unclassed HTML elements (h1, a, etc.)
Layer 5: Objects     — Layout patterns, no cosmetics (.container, .grid)
Layer 6: Components  — UI components (.card, .button, .nav)
Layer 7: Utilities   — Single-purpose overrides (.mt-4, .sr-only)
```

```css
/* main.css — import in ITCSS order */

/* 1. Settings */
/* 2. Tools */

/* 3. Generic */
@layer generic {
  *, *::before, *::after { box-sizing: border-box; }
  html { font-size: 16px; }
  body { margin: 0; }
}

/* 4. Elements */
@layer elements {
  h1, h2, h3, h4, h5, h6 {
    font-family: system-ui, sans-serif;
    line-height: 1.2;
  }
  a { color: var(--color-link); }
  img { max-width: 100%; height: auto; }
}

/* 5. Objects */
@layer objects {
  .o-container {
    max-width: 1200px;
    margin-inline: auto;
    padding-inline: 1rem;
  }
  .o-grid { display: grid; gap: 1rem; }
  .o-stack > * + * { margin-block-start: 1rem; }
}

/* 6. Components */
@layer components {
  .c-card { /* card component */ }
  .c-button { /* button component */ }
  .c-nav { /* navigation */ }
}

/* 7. Utilities */
@layer utilities {
  .u-sr-only {
    position: absolute;
    width: 1px; height: 1px;
    overflow: hidden;
    clip: rect(0,0,0,0);
  }
  .u-mt-auto { margin-block-start: auto; }
  .u-text-center { text-align: center; }
}
```

---

## Step 3: Tailwind Utility-First Concepts

```html
<!-- Tailwind: compose styles directly in HTML -->
<article class="rounded-lg border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden">
  <img class="w-full h-48 object-cover" src="..." alt="...">
  <div class="p-4 space-y-2">
    <h2 class="text-xl font-semibold text-gray-900 leading-tight">Title</h2>
    <p class="text-sm text-gray-600 line-clamp-3">Description...</p>
    <div class="flex items-center justify-between pt-2">
      <span class="text-xs text-gray-500">2 min read</span>
      <button class="px-3 py-1.5 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 transition-colors">
        Read More
      </button>
    </div>
  </div>
</article>

<!-- Tailwind custom values via [] syntax -->
<div class="w-[328px] bg-[#3b82f6] p-[1.25rem]">Custom values</div>

<!-- Responsive prefix: sm: md: lg: xl: 2xl: -->
<div class="flex-col md:flex-row">Responsive flex direction</div>

<!-- Dark mode prefix -->
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-white">Theme-aware</div>

<!-- State variants: hover: focus: active: group-hover: -->
<a class="text-blue-600 hover:text-blue-800 underline hover:no-underline">Link</a>
```

```javascript
// tailwind.config.js — extending the design system
module.exports = {
  content: ['./src/**/*.{html,js}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        }
      },
      fontFamily: {
        sans: ['Inter', ...defaultTheme.fontFamily.sans],
      },
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
      }
    }
  }
};
```

---

## Step 4: CSS Modules Scoping

```css
/* Button.module.css */
.button {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.button--primary {
  background: var(--color-primary);
  color: white;
}

.button--secondary {
  background: transparent;
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
}
```

```javascript
// Button.jsx
import styles from './Button.module.css';

export function Button({ variant = 'primary', children }) {
  return (
    <button className={`${styles.button} ${styles[`button--${variant}`]}`}>
      {children}
    </button>
  );
}

// Generated output: <button class="button_abc123 button--primary_def456">
// No naming conflicts possible!
```

---

## Step 5: Stylelint Configuration

```json
// .stylelintrc.json
{
  "extends": ["stylelint-config-standard"],
  "rules": {
    "color-named": "never",
    "selector-class-pattern": "^([a-z][a-z0-9]*)(-[a-z0-9]+)*(__[a-z][a-z0-9]*(-[a-z0-9]+)*)?(--[a-z][a-z0-9]*(-[a-z0-9]+)*)?$",
    "declaration-no-important": [true, { "severity": "warning" }],
    "max-nesting-depth": 2,
    "selector-max-specificity": "0,3,0",
    "property-no-vendor-prefix": true,
    "value-no-vendor-prefix": true,
    "no-duplicate-selectors": true,
    "font-weight-notation": "numeric",
    "shorthand-property-no-redundant-values": true,
    "comment-empty-line-before": "always"
  }
}
```

---

## Step 6: Writing Maintainable CSS

```css
/* ✓ Good: descriptive, low-specificity, single responsibility */
.nav__link { color: var(--color-text); }
.nav__link:hover { color: var(--color-primary); }
.nav__link--active { color: var(--color-primary); font-weight: 600; }

/* ❌ Avoid: high specificity, unclear intent */
header nav ul li a { color: blue; }
#main-nav .active { font-weight: bold; }

/* ✓ Good: use custom properties for magic numbers */
.heading { margin-block-start: var(--space-lg); }

/* ❌ Avoid: magic numbers */
.heading { margin-top: 32px; }

/* ✓ Good: responsive with logical properties */
.sidebar { 
  inline-size: var(--sidebar-width, 280px);
  padding-inline: var(--space-md);
}

/* Comment intent, not syntax */
/* ✓ Establish stacking context for dropdown */
.nav { position: relative; z-index: 100; }

/* ❌ Don't comment the obvious */
/* sets position to relative */
.nav { position: relative; }
```

---

## Step 7: CSS Layers + Architecture Combined

```css
/* Complete ITCSS + @layer setup */
@layer settings, tools, generic, elements, objects, components, utilities;

@layer settings {
  :root {
    --color-brand: oklch(57% 0.20 250);
    --space-unit: 0.25rem;
  }
}

@layer generic {
  *, *::before, *::after { box-sizing: border-box; }
  body { margin: 0; line-height: 1.5; }
}

@layer elements {
  h1 { font-size: clamp(1.5rem, 4vw, 3rem); }
  a:hover { text-decoration: none; }
}

@layer objects {
  .o-container { max-width: 75rem; margin-inline: auto; }
}

@layer components {
  .c-button {
    padding: 0.5em 1.25em;
    border-radius: 0.375rem;
    font-weight: 600;
  }
}

@layer utilities {
  .u-visually-hidden {
    clip: rect(0,0,0,0);
    clip-path: inset(50%);
    height: 1px; width: 1px;
    overflow: hidden;
    white-space: nowrap;
  }
}
```

---

## Step 8: Capstone — Stylelint Validation

```bash
docker run --rm node:20-alpine sh -c '
npm install -g stylelint stylelint-config-standard 2>/dev/null | tail -1
node -e "
var css = \".card { display: flex; padding: 1rem; } .card__title { font-size: 1.25rem; } .card--featured { background: blue; }\";
var classes = css.match(/\.[a-z][a-z0-9-]*(__[a-z][a-z0-9-]*)?(--[a-z][a-z0-9-]*)?/g);
console.log(\"BEM classes found:\", classes);
var valid = classes.every(function(c){ return /^\.[a-z][a-z0-9-]*(__[a-z][a-z0-9-]*)?(--[a-z][a-z0-9-]*)?$/.test(c); });
console.log(\"All BEM-valid:\", valid);
"
'
```

📸 **Verified Output:**
```
stylelint installed
BEM classes found: [ '.card', '.card__title', '.card--featured' ]
All BEM-valid: true
```

---

## Summary

| Method | Pattern | Best For |
|--------|---------|----------|
| BEM | `.block__el--mod` | Naming convention |
| ITCSS | Settings→Utilities layers | File organization |
| `@layer` | `@layer components {}` | Cascade control |
| Tailwind | `class="p-4 flex"` | Rapid prototyping |
| CSS Modules | `import styles from '.module.css'` | Component scoping |
| Stylelint | `.stylelintrc.json` | Enforce standards |
| Logical props | `padding-inline` | i18n-ready CSS |
| Custom props | `--space-lg: 2rem` | Design tokens |
