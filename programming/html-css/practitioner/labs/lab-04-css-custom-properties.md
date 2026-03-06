# Lab 04: CSS Custom Properties

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

CSS Custom Properties (variables) enable dynamic theming, design tokens, and component-level customization. Learn `var()` with fallbacks, scoping, JS manipulation, `@property` registration, and token patterns.

---

## Step 1: Basic var() and Fallbacks

```css
/* Declaration: always starts with -- */
:root {
  --color-primary: #3b82f6;
  --spacing-base: 16px;
  --border-radius: 8px;
  --font-size-base: 1rem;
}

/* Usage: var(--name, fallback) */
.button {
  background: var(--color-primary);
  padding: var(--spacing-base, 1rem);   /* fallback if undefined */
  border-radius: var(--border-radius);
  
  /* Chained fallbacks */
  color: var(--button-color, var(--color-text, #111));
  
  /* Fallback can be any valid value */
  font-size: var(--button-font-size, 1rem);
}

/* Using in calc() */
.grid {
  gap: calc(var(--spacing-base) * 1.5);
  padding: calc(var(--spacing-base) * 2);
}
```

> 💡 If `--my-var` is not defined, `var(--my-var, fallback)` uses the fallback. If it IS defined but invalid for the property, the browser uses `initial` or `inherit` — **not** the fallback.

---

## Step 2: Scoping — Root vs Component

```css
/* Global tokens on :root */
:root {
  --color-primary: #3b82f6;
  --color-danger:  #ef4444;
  --color-success: #22c55e;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 2rem;
}

/* Component scope: override just for this component */
.card {
  --card-bg: white;
  --card-padding: var(--spacing-md);
  --card-radius: 8px;
  
  background: var(--card-bg);
  padding: var(--card-padding);
  border-radius: var(--card-radius);
}

/* Variant: override the component variable */
.card--dark {
  --card-bg: #1a1a2e;
  --card-color: white;
}

.card--compact {
  --card-padding: var(--spacing-sm);
}

/* Nested: inner elements inherit parent scope */
.theme-holiday {
  --color-primary: #dc2626;  /* red for holiday */
  --color-accent: #16a34a;   /* green */
}

/* All children of .theme-holiday see the overridden values */
.theme-holiday .button {
  background: var(--color-primary); /* #dc2626 */
}
```

---

## Step 3: Dynamic Theming via JavaScript

```html
<button id="theme-toggle">Toggle Dark Mode</button>
```

```javascript
// Read CSS variable value
const root = document.documentElement;
const primaryColor = getComputedStyle(root)
  .getPropertyValue('--color-primary')
  .trim(); // "#3b82f6"

// Set CSS variable
root.style.setProperty('--color-primary', '#8b5cf6');

// Theme switcher with localStorage
const themes = {
  light: {
    '--color-bg': '#ffffff',
    '--color-text': '#111111',
    '--color-primary': '#3b82f6',
    '--color-surface': '#f5f5f5',
  },
  dark: {
    '--color-bg': '#0d0d0d',
    '--color-text': '#f0f0f0',
    '--color-primary': '#60a5fa',
    '--color-surface': '#1a1a1a',
  }
};

function applyTheme(themeName) {
  const theme = themes[themeName];
  Object.entries(theme).forEach(([prop, value]) => {
    root.style.setProperty(prop, value);
  });
  localStorage.setItem('theme', themeName);
  root.setAttribute('data-theme', themeName);
}

// Initialize from saved preference
const savedTheme = localStorage.getItem('theme') || 
  (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
applyTheme(savedTheme);

document.getElementById('theme-toggle').addEventListener('click', () => {
  const current = localStorage.getItem('theme') || 'light';
  applyTheme(current === 'light' ? 'dark' : 'light');
});
```

---

## Step 4: `@property` — Registered Custom Properties

`@property` enables type-safe custom properties that can be animated:

```css
/* Without @property: can't animate --color or --number */
/* With @property: browser knows the type! */

@property --brand-color {
  syntax: '<color>';        /* type: color */
  inherits: true;           /* does it inherit through DOM? */
  initial-value: #3b82f6;   /* default value */
}

@property --progress {
  syntax: '<number>';
  inherits: false;
  initial-value: 0;
}

@property --angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

/* Now you can animate these! */
.brand-button {
  background: var(--brand-color);
  transition: --brand-color 0.3s ease;
}

.brand-button:hover {
  --brand-color: #1d4ed8; /* animates smoothly! */
}

/* Animated gradient via @property */
@property --gradient-angle {
  syntax: '<angle>';
  inherits: false;
  initial-value: 0deg;
}

@keyframes rotate-gradient {
  to { --gradient-angle: 360deg; }
}

.animated-card {
  background: conic-gradient(from var(--gradient-angle), #3b82f6, #8b5cf6, #3b82f6);
  animation: rotate-gradient 4s linear infinite;
}
```

> 💡 Without `@property`, CSS can't interpolate custom properties because it doesn't know their type. `@property` with `syntax: '<color>'` lets the browser do color interpolation between `red` and `blue`.

---

## Step 5: Design Token Patterns

```css
/* Tier 1: Primitive tokens (raw values) */
:root {
  /* Color palette */
  --blue-50:  #eff6ff;
  --blue-100: #dbeafe;
  --blue-500: #3b82f6;
  --blue-600: #2563eb;
  --blue-900: #1e3a8a;
  
  /* Spacing scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;
}

/* Tier 2: Semantic tokens (purpose-based) */
:root {
  --color-brand:    var(--blue-500);
  --color-brand-hover: var(--blue-600);
  --color-text:     #111827;
  --color-text-muted: #6b7280;
  --color-bg:       #ffffff;
  --color-surface:  #f9fafb;
  --color-border:   #e5e7eb;
  
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-pill: 9999px;
  
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
}

/* Tier 3: Component tokens */
.btn {
  --btn-bg:      var(--color-brand);
  --btn-color:   white;
  --btn-radius:  var(--radius-md);
  --btn-padding: var(--space-2) var(--space-4);
  
  background: var(--btn-bg);
  color: var(--btn-color);
  border-radius: var(--btn-radius);
  padding: var(--btn-padding);
}
```

---

## Step 6: CSS Variables in Media Queries & Containers

```css
/* Custom properties work with media queries */
:root {
  --container-max: 1200px;
  --grid-cols: 1;
}

@media (min-width: 640px) {
  :root { --grid-cols: 2; }
}

@media (min-width: 1024px) {
  :root { --grid-cols: 3; }
}

.grid {
  display: grid;
  grid-template-columns: repeat(var(--grid-cols), 1fr);
}
```

---

## Step 7: Invalid Values and the Initial/Inherit Trick

```css
/* Toggle a property with a single variable */
:root {
  --is-dark: ;  /* empty = "on" for space toggle trick */
}

.box {
  /* Light mode colors */
  --bg-l: white;
  --bg-d: #111;
  
  /* space toggle: if --is-dark is set, --bg-d wins */
  background: var(--is-dark, ) var(--bg-d)
              var(--is-dark) var(--bg-l);
}

/* Simpler: use data-theme attribute */
[data-theme="dark"] {
  --color-bg: #0d0d0d;
  --color-text: #f0f0f0;
}
```

---

## Step 8: Capstone — CSS Variable Extractor + @property Generator

```bash
docker run --rm node:20-alpine node -e "
// CSS var extraction + @property demo
var css = ':root { --color-primary: #3b82f6; --spacing-base: 16px; --border-radius: 8px; }';

// Extract variables
var varPattern = /--([\w-]+):\s*([^;]+)/g;
var match, vars = [];
while((match = varPattern.exec(css)) !== null) {
  vars.push({name: '--' + match[1], value: match[2].trim()});
}

console.log('Extracted CSS variables:');
vars.forEach(function(v){ console.log('  ' + v.name + ': ' + v.value); });

// Generate @property declarations
console.log('\n@property declarations:');
vars.forEach(function(v){
  var syntax = v.value.startsWith('#') || v.value.includes('rgb') ? '<color>' :
               v.value.endsWith('px') || v.value.endsWith('rem') ? '<length>' : '<*>';
  console.log('@property ' + v.name + ' {');
  console.log('  syntax: \"' + syntax + '\";');
  console.log('  inherits: true;');
  console.log('  initial-value: ' + v.value + ';');
  console.log('}');
});
"
```

📸 **Verified Output:**
```
Extracted CSS variables:
  --color-primary: #3b82f6
  --spacing-base: 16px
  --border-radius: 8px

@property declarations:
@property --color-primary {
  syntax: "<color>";
  inherits: true;
  initial-value: #3b82f6;
}
@property --spacing-base {
  syntax: "<length>";
  inherits: true;
  initial-value: 16px;
}
@property --border-radius {
  syntax: "<length>";
  inherits: true;
  initial-value: 8px;
}
```

---

## Summary

| Feature | Syntax | Use Case |
|---------|--------|----------|
| Declare variable | `--name: value` | Define token |
| Use variable | `var(--name)` | Apply token |
| With fallback | `var(--name, fallback)` | Safe usage |
| JS read | `getComputedStyle(el).getPropertyValue('--name')` | Read at runtime |
| JS write | `el.style.setProperty('--name', value)` | Dynamic theming |
| Register type | `@property --name { syntax: '<color>' }` | Animatable variables |
| Component scope | `selector { --name: value }` | Local override |
| Design tokens | Primitive → Semantic → Component | Token architecture |
