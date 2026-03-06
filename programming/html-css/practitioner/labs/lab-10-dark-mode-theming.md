# Lab 10: Dark Mode & Theming

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build a complete dark/light theming system using `prefers-color-scheme`, CSS custom properties as design tokens, the `color-scheme` property, `forced-colors` support, modern `oklch()` color space, and a persistent JS theme switcher.

---

## Step 1: prefers-color-scheme Media Query

```css
/* Base (light) styles */
:root {
  --color-bg:          #ffffff;
  --color-surface:     #f5f5f5;
  --color-text:        #111111;
  --color-text-muted:  #666666;
  --color-primary:     #3b82f6;
  --color-border:      #e0e0e0;
}

/* Dark mode: override tokens */
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg:          #0d0d0d;
    --color-surface:     #1a1a1a;
    --color-text:        #f0f0f0;
    --color-text-muted:  #aaaaaa;
    --color-primary:     #60a5fa;
    --color-border:      #333333;
  }
}

/* Use tokens throughout */
body {
  background: var(--color-bg);
  color: var(--color-text);
}

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
}
```

---

## Step 2: color-scheme Property

```css
/* Tell the browser which mode you support */
/* This affects: scrollbars, form controls, system UI */
:root {
  color-scheme: light dark; /* support both */
}

/* Force a specific scheme for an element */
.code-block {
  color-scheme: dark; /* always dark syntax highlighting */
  background: #1a1a2e;
  color: #e2e8f0;
}

/* In HTML: */
/* <meta name="color-scheme" content="light dark"> */
```

---

## Step 3: Manual Theme Toggle with Data Attribute

```css
/* Attribute-based theming (supports user toggle) */
:root,
[data-theme="light"] {
  --color-bg:         #ffffff;
  --color-surface:    #f5f5f5;
  --color-text:       #111111;
  --color-primary:    #3b82f6;
  --color-border:     #e0e0e0;
  color-scheme: light;
}

[data-theme="dark"] {
  --color-bg:         #0d0d0d;
  --color-surface:    #1a1a1a;
  --color-text:       #f0f0f0;
  --color-primary:    #60a5fa;
  --color-border:     #333333;
  color-scheme: dark;
}

/* Also support auto (follow OS) */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    /* only applies when no explicit theme set */
    --color-bg: #0d0d0d;
    /* ... */
  }
}
```

---

## Step 4: oklch() Color Space

`oklch(lightness% chroma hue)` — perceptually uniform color space:

```css
/* oklch advantages:
   - Perceptually uniform: equal numeric distance = equal visual difference
   - Easy to create color scales by changing just lightness
   - Wider gamut (P3 display support)
   - No hue shifting when adjusting brightness (unlike HSL)
*/

:root {
  /* Primary color in oklch */
  --color-primary-50:  oklch(96% 0.03 250);
  --color-primary-100: oklch(92% 0.06 250);
  --color-primary-200: oklch(84% 0.10 250);
  --color-primary-300: oklch(74% 0.15 250);
  --color-primary-400: oklch(65% 0.18 250);
  --color-primary-500: oklch(57% 0.20 250);  /* base */
  --color-primary-600: oklch(49% 0.20 250);
  --color-primary-700: oklch(41% 0.18 250);
  --color-primary-800: oklch(33% 0.14 250);
  --color-primary-900: oklch(25% 0.09 250);
}

/* Dark mode: just change lightness */
[data-theme="dark"] {
  --color-primary: oklch(70% 0.20 250); /* lighter for dark bg */
}

/* Generate accessible color pairs */
.badge {
  background: oklch(65% 0.18 250);   /* medium blue */
  color: oklch(98% 0.01 250);        /* near-white */
}
```

---

## Step 5: forced-colors (High Contrast Mode)

```css
/* Windows High Contrast / forced colors mode */
@media (forced-colors: active) {
  /* System color keywords work here */
  .button {
    background: ButtonFace;
    color: ButtonText;
    border: 1px solid ButtonBorder;
  }
  
  /* Restore hidden elements that may be invisible */
  .icon { forced-color-adjust: auto; }
  
  /* Preserve custom styling (use sparingly) */
  .chart {
    forced-color-adjust: none;
  }
}

/* System color keywords for forced-colors: */
/* Canvas, CanvasText, LinkText, VisitedText, ActiveText */
/* ButtonFace, ButtonText, ButtonBorder */
/* Field, FieldText */
/* Highlight, HighlightText */
/* Mark, MarkText */
/* GrayText */
```

---

## Step 6: JavaScript Theme Switcher

```html
<button id="theme-toggle" aria-label="Toggle dark mode">
  <svg class="icon icon-sun">...</svg>
  <svg class="icon icon-moon">...</svg>
</button>
```

```javascript
class ThemeSwitcher {
  constructor() {
    this.root = document.documentElement;
    this.storageKey = 'theme-preference';
    this.themes = ['light', 'dark'];
    
    // Listen for OS preference changes
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    this.mediaQuery.addEventListener('change', () => {
      if (!this.hasStoredPreference()) {
        this.applyOsPreference();
      }
    });
  }
  
  getOsPreference() {
    return this.mediaQuery.matches ? 'dark' : 'light';
  }
  
  getStoredPreference() {
    return localStorage.getItem(this.storageKey);
  }
  
  hasStoredPreference() {
    return !!this.getStoredPreference();
  }
  
  getActiveTheme() {
    return this.getStoredPreference() || this.getOsPreference();
  }
  
  applyTheme(theme) {
    this.root.setAttribute('data-theme', theme);
    this.root.style.colorScheme = theme;
    // Update toggle button state
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
      toggle.setAttribute('aria-pressed', theme === 'dark');
      toggle.title = `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`;
    }
  }
  
  applyOsPreference() {
    this.applyTheme(this.getOsPreference());
  }
  
  init() {
    this.applyTheme(this.getActiveTheme());
    
    document.getElementById('theme-toggle')?.addEventListener('click', () => {
      const current = this.getActiveTheme();
      const next = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem(this.storageKey, next);
      this.applyTheme(next);
    });
  }
}

// Initialize as early as possible to prevent flash
const switcher = new ThemeSwitcher();
switcher.init();
```

---

## Step 7: Anti-Flash Script

```html
<!-- In <head>, before CSS: prevents flash of wrong theme -->
<script>
  (function() {
    const stored = localStorage.getItem('theme-preference');
    const theme = stored || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.style.colorScheme = theme;
  })();
</script>
```

---

## Step 8: Capstone — Theme Token Generator

```bash
docker run --rm node:20-alpine node -e "
var tokens = {
  light: {'--color-bg':'#ffffff','--color-surface':'#f5f5f5','--color-text':'#111111','--color-text-muted':'#666666','--color-primary':'oklch(60% 0.2 250)','--color-border':'#e0e0e0'},
  dark:  {'--color-bg':'#0d0d0d','--color-surface':'#1a1a1a','--color-text':'#f0f0f0','--color-text-muted':'#aaaaaa','--color-primary':'oklch(70% 0.2 250)','--color-border':'#333333'}
};
console.log(':root {');
Object.entries(tokens.light).forEach(function(e){ console.log('  ' + e[0] + ': ' + e[1] + ';'); });
console.log('}');
console.log('@media (prefers-color-scheme: dark) {');
console.log('  :root {');
Object.entries(tokens.dark).forEach(function(e){ console.log('    ' + e[0] + ': ' + e[1] + ';'); });
console.log('  }');
console.log('}');
"
```

📸 **Verified Output:**
```
:root {
  --color-bg: #ffffff;
  --color-surface: #f5f5f5;
  --color-text: #111111;
  --color-text-muted: #666666;
  --color-primary: oklch(60% 0.2 250);
  --color-border: #e0e0e0;
}
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #0d0d0d;
    --color-surface: #1a1a1a;
    --color-text: #f0f0f0;
    --color-text-muted: #aaaaaa;
    --color-primary: oklch(70% 0.2 250);
    --color-border: #333333;
  }
}
```

---

## Summary

| Feature | Syntax | Purpose |
|---------|--------|---------|
| OS preference | `@media (prefers-color-scheme: dark)` | Auto dark mode |
| Color scheme hint | `color-scheme: light dark` | Style system UI |
| Manual toggle | `[data-theme="dark"]` | User choice |
| oklch() | `oklch(57% 0.20 250)` | Perceptual color |
| Forced colors | `@media (forced-colors: active)` | High contrast support |
| JS set theme | `el.setAttribute('data-theme', ...)` | Dynamic switching |
| Persist preference | `localStorage.setItem(...)` | Remember choice |
| Anti-flash | Inline script in `<head>` | Prevent FOUC |
