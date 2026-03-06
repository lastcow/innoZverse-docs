# Lab 11: Theming System

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Enterprise theming architecture: CSS layer strategy, multi-brand theming with `data-theme`, media query stack (`prefers-color-scheme` + `forced-colors` + `prefers-contrast`), oklch() palette generation for P3 wide gamut, and CSS `@scope` for theme isolation.

---

## Step 1: CSS Layer Architecture

```css
/* Declare layers in correct cascade order */
@layer reset, base, tokens, components, utilities, overrides;

@layer reset {
  *, *::before, *::after { box-sizing: border-box; }
  body { margin: 0; }
  img  { max-width: 100%; display: block; }
}

@layer base {
  :root {
    font-family: var(--font-sans);
    line-height: var(--line-height-base);
    color: var(--color-text-primary);
    background: var(--color-bg-default);
  }
}

@layer tokens {
  :root {
    /* Light theme defaults */
    --color-primary: oklch(0.55 0.20 250);
    --color-bg-default: oklch(0.99 0 0);
    --color-text-primary: oklch(0.15 0 0);
  }
}

@layer components {
  .btn { /* ... */ }
  .card { /* ... */ }
}

@layer utilities {
  .sr-only { /* ... */ }
  .flex  { display: flex; }
}

@layer overrides {
  /* Third-party library overrides */
}
```

> 💡 Layer order matters: `utilities` overrides `components` regardless of specificity. This is the key insight — cascade layers trump specificity.

---

## Step 2: Multi-Brand Theming

```css
/* Base theme tokens */
@layer tokens {
  :root,
  [data-theme="brand-a"] {
    --color-primary:       oklch(0.55 0.20 250);  /* Blue */
    --color-secondary:     oklch(0.65 0.17 165);  /* Green */
    --color-accent:        oklch(0.70 0.22 330);  /* Purple */
    --color-bg-default:    oklch(0.99 0 0);
    --color-bg-subtle:     oklch(0.96 0 0);
    --color-text-primary:  oklch(0.15 0 0);
    --color-text-muted:    oklch(0.45 0 0);
    --border-radius-base:  0.375rem;
    --font-sans: 'Inter', sans-serif;
  }

  /* Brand B: different primary + slightly rounder */
  [data-theme="brand-b"] {
    --color-primary:       oklch(0.55 0.22 145);  /* Green brand */
    --color-secondary:     oklch(0.60 0.18 290);  /* Blue secondary */
    --color-accent:        oklch(0.70 0.20 40);   /* Orange */
    --border-radius-base:  0.5rem;
    --font-sans: 'Outfit', sans-serif;
  }

  /* Brand C: enterprise dark feel */
  [data-theme="brand-c"] {
    --color-primary:       oklch(0.65 0.15 250);  /* Muted blue */
    --color-secondary:     oklch(0.60 0.10 200);  /* Teal */
    --border-radius-base:  0.25rem;
    --font-sans: 'IBM Plex Sans', sans-serif;
  }
}
```

```javascript
// Theme switcher
function setTheme(brand) {
  document.documentElement.dataset.theme = brand;
  localStorage.setItem('theme', brand);
}

// Init from saved preference
const saved = localStorage.getItem('theme') || 'brand-a';
setTheme(saved);
```

---

## Step 3: Dark Mode + Forced Colors + High Contrast Stack

```css
/* Full media query stack */

/* Light (default) — already defined in :root */

/* Dark mode — system preference */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme-override]) {
    --color-bg-default:    oklch(0.12 0.01 255);
    --color-bg-subtle:     oklch(0.16 0.01 255);
    --color-text-primary:  oklch(0.95 0 0);
    --color-text-muted:    oklch(0.65 0 0);
    --color-primary:       oklch(0.70 0.18 250);  /* Lighter for dark bg */
  }
}

/* User-forced dark (data attribute overrides system) */
[data-color-scheme="dark"] {
  --color-bg-default:    oklch(0.12 0.01 255);
  --color-text-primary:  oklch(0.95 0 0);
}

[data-color-scheme="light"] {
  --color-bg-default:    oklch(0.99 0 0);
  --color-text-primary:  oklch(0.15 0 0);
}

/* High contrast mode — prefers-contrast: more */
@media (prefers-contrast: more) {
  :root {
    --color-primary:       oklch(0.35 0.22 250);  /* Darker for higher contrast */
    --color-text-primary:  oklch(0.05 0 0);       /* Near black */
    --color-bg-default:    oklch(1 0 0);           /* Pure white */
    --border-width:        2px;                    /* Thicker borders */
  }
}

/* Forced Colors (Windows High Contrast mode) */
@media (forced-colors: active) {
  :root {
    --color-primary:      ButtonText;
    --color-bg-default:   Canvas;
    --color-text-primary: CanvasText;
  }

  /* Preserve focus indicators in forced colors */
  :focus-visible {
    outline: 3px solid ButtonText;
    outline-offset: 2px;
  }

  /* SVG icons need forced color treatment */
  .icon {
    forced-color-adjust: auto;
  }
}
```

---

## Step 4: oklch() Color Palette Generation

```javascript
// Generate a perceptually uniform 10-shade palette
function oklchShade(baseHue, baseChroma, step) {
  // step: 1 (lightest) to 10 (darkest)
  const lightness = 0.98 - (step - 1) * 0.088;
  // Reduce chroma at extremes for natural feel
  const chromaFactor = step === 1 || step === 10 ? 0.3 :
                       step < 4 ? 0.5 : 1.0;
  const chroma = baseChroma * chromaFactor;
  return `oklch(${(lightness * 100).toFixed(1)}% ${chroma.toFixed(3)} ${baseHue})`;
}

// Generate full palette
function generatePalette(name, hue, chroma = 0.18) {
  const palette = {};
  for (let i = 1; i <= 10; i++) {
    palette[`${name}-${i * 100}`] = oklchShade(hue, chroma, i);
  }
  return palette;
}
```

---

## Step 5: CSS `@scope` for Theme Isolation

```css
/* @scope limits where styles apply — prevents bleed */

/* Scope button styles only within .card */
@scope (.card) {
  .btn {
    /* This .btn rule ONLY applies inside .card */
    font-size: 0.875rem;
    padding: 0.375rem 0.75rem;
  }
}

/* Scope with exclusion (donut scope) */
@scope (.page) to (.widget) {
  /* Applies inside .page but NOT inside .widget within .page */
  .btn { background: var(--color-primary); }
}

/* Brand isolation */
@scope ([data-theme="brand-b"]) {
  .hero {
    background: linear-gradient(
      135deg,
      oklch(0.45 0.22 145) 0%,
      oklch(0.35 0.18 145) 100%
    );
  }
}
```

---

## Step 6: Theme Token Export

```javascript
// Generate CSS for all themes
function generateThemeCSS(themes) {
  return Object.entries(themes)
    .map(([name, tokens]) => {
      const selector = name === 'default' ? ':root' : `[data-theme="${name}"]`;
      const vars = Object.entries(tokens)
        .map(([k, v]) => `  --${k}: ${v};`)
        .join('\n');
      return `${selector} {\n${vars}\n}`;
    })
    .join('\n\n');
}
```

---

## Step 7: Smooth Theme Transition

```css
/* Transition color changes */
*, *::before, *::after {
  transition:
    background-color var(--duration-normal) var(--easing-standard),
    color var(--duration-fast) var(--easing-standard),
    border-color var(--duration-fast) var(--easing-standard);
}

/* But not on first load (no FOUC) */
.no-theme-transition * {
  transition: none !important;
}
```

```javascript
function toggleDarkMode() {
  // Temporarily disable transitions to prevent FOUC
  document.body.classList.add('no-theme-transition');
  document.documentElement.dataset.colorScheme =
    document.documentElement.dataset.colorScheme === 'dark' ? 'light' : 'dark';
  // Re-enable after browser paint
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      document.body.classList.remove('no-theme-transition');
    });
  });
}
```

---

## Step 8: Capstone — oklch Palette Generator

```bash
docker run --rm node:20-alpine node -e "
function oklchToCSS(l, c, h) {
  return 'oklch(' + (l*100).toFixed(1) + '% ' + c.toFixed(3) + ' ' + h.toFixed(1) + ')';
}
const hue = 250; const chroma = 0.18;
console.log('=== oklch() Blue Palette (10 shades) ===');
for(let i=1; i<=10; i++) {
  const l = 0.98 - (i-1)*0.088;
  const c = i===1||i===10 ? chroma*0.3 : i<5 ? chroma*0.5 : chroma;
  console.log('--color-blue-'+i*100+': '+oklchToCSS(l,c,hue)+';');
}
console.log('');
console.log('P3 gamut note: oklch values exceeding sRGB auto-mapped by browser');
"
```

📸 **Verified Output:**
```
=== oklch() Blue Palette (10 shades) ===
--color-blue-100: oklch(98.0% 0.054 250.0);
--color-blue-200: oklch(89.2% 0.090 250.0);
--color-blue-300: oklch(80.4% 0.090 250.0);
--color-blue-400: oklch(71.6% 0.090 250.0);
--color-blue-500: oklch(62.8% 0.180 250.0);
--color-blue-600: oklch(54.0% 0.180 250.0);
--color-blue-700: oklch(45.2% 0.180 250.0);
--color-blue-800: oklch(36.4% 0.180 250.0);
--color-blue-900: oklch(27.6% 0.180 250.0);
--color-blue-1000: oklch(18.8% 0.054 250.0);

P3 gamut note: oklch values exceeding sRGB auto-mapped by browser
```

---

## Summary

| Feature | CSS | Benefit |
|---------|-----|---------|
| Layer ordering | `@layer` | Predictable cascade |
| Multi-brand | `[data-theme]` attributes | Runtime switching |
| Dark mode | `prefers-color-scheme` | Auto OS-synced |
| Forced colors | `@media (forced-colors)` | Windows accessibility |
| High contrast | `prefers-contrast: more` | User preference |
| P3 colors | `oklch()` | Wider gamut palette |
| Scope isolation | `@scope (.parent)` | No style leakage |
| Smooth switch | Transition + no-FOUC | Polished UX |
