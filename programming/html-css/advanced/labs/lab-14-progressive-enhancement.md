# Lab 14: Progressive Enhancement

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master progressive enhancement and graceful degradation: `@supports` feature detection, CSS fallback stacks, Baseline 2024 features, polyfill strategies with `type=module/nomodule`, and the PE vs graceful degradation philosophy.

---

## Step 1: Progressive Enhancement vs Graceful Degradation

```
Progressive Enhancement (PE):
─────────────────────────────────────
Start: Basic functionality works everywhere
Then: Enhance for capable browsers
Philosophy: "Works for all, better for modern"

Graceful Degradation (GD):
─────────────────────────────────────
Start: Build for modern browsers
Then: Add fallbacks for older browsers
Philosophy: "Best for modern, acceptable for old"

The difference in practice:
  PE: Start with <form>, enhance with JS validation
  GD: Build JS validation, fall back to server-side

Modern recommendation: Progressive Enhancement
  — Users on slow connections get core functionality
  — Screen reader users get accessible baseline
  — Future browsers don't break unexpectedly
```

---

## Step 2: @supports Feature Detection

```css
/* Basic @supports — test property: value pairs */
@supports (display: grid) {
  .layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}

@supports not (display: grid) {
  .layout {
    display: flex;
    flex-wrap: wrap;
  }
}

/* Combine conditions */
@supports (display: grid) and (gap: 1rem) {
  .grid { display: grid; gap: 1rem; }
}

@supports (display: flex) or (display: grid) {
  .modern { /* either flex or grid supported */ }
}

/* Nested @supports */
@supports (container-type: inline-size) {
  .wrapper {
    container-type: inline-size;
  }
  
  @container (min-width: 400px) {
    .card { flex-direction: row; }
  }
}

/* Test custom properties */
@supports (--custom: value) {
  :root { --color-primary: #3b82f6; }
}

/* Test modern color functions */
@supports (color: oklch(57% 0.2 250)) {
  :root { --color-primary: oklch(57% 0.2 250); }
}
@supports not (color: oklch(57% 0.2 250)) {
  :root { --color-primary: #3b82f6; }  /* hex fallback */
}
```

---

## Step 3: @supports selector()

```css
/* Test if a selector is supported */
@supports selector(:has(a)) {
  /* :has() is supported */
  .card:has(img) { padding-top: 0; }
}

@supports not selector(:has(a)) {
  /* Fallback: use JS to add a class */
  .card.has-image { padding-top: 0; }
}

/* Test :is() */
@supports selector(:is(h1, h2)) {
  :is(h1, h2, h3) { line-height: 1.2; }
}

/* Test :focus-visible */
@supports selector(:focus-visible) {
  /* Native support */
  :focus:not(:focus-visible) { outline: none; }
  :focus-visible { outline: 3px solid blue; }
}

@supports not selector(:focus-visible) {
  /* Polyfill needed */
  :focus { outline: 3px solid blue; }
}
```

---

## Step 4: CSS Fallback Value Stacks

```css
/* Property-level fallbacks (browser ignores unknown values) */
.element {
  /* Color fallbacks */
  color: #3b82f6;            /* legacy: hex always works */
  color: rgb(59, 130, 246);  /* rgb: works everywhere */
  color: hsl(217, 91%, 60%); /* hsl: IE9+ */
  color: oklch(57% 0.20 250);/* last wins if supported */
  
  /* Background fallbacks */
  background: #f9fafb;
  background: color-mix(in oklch, white 95%, var(--color-primary));
  
  /* Size fallbacks */
  height: 100vh;
  height: 100svh; /* small viewport: newer browsers */
  height: 100dvh; /* dynamic viewport: latest browsers */
}

/* Layout fallbacks */
.container {
  /* Old: float layout */
  float: left;
  width: 66.666%;
}

@supports (display: flex) {
  .container {
    float: none; /* reset float */
    width: auto;
    display: flex;
  }
}

@supports (display: grid) {
  .container {
    display: grid;
    grid-template-columns: 2fr 1fr;
  }
}

/* Custom property fallback */
.component {
  /* If --brand-color not defined, use fallback */
  color: var(--brand-color, #3b82f6);
  
  /* Chained fallbacks */
  color: var(--brand-color, var(--color-primary, #3b82f6));
}
```

---

## Step 5: Baseline 2024 Features

```
Baseline indicates broad cross-browser support.

Baseline 2024 (Widely Available — all major browsers, 2+ years):
  ✓ CSS Grid (2017)
  ✓ CSS Custom Properties (2016)
  ✓ Flexbox (2012)
  ✓ CSS Transitions (2013)
  ✓ :is(), :where() (2021)
  ✓ aspect-ratio (2021)
  ✓ gap (for flex/grid) (2020)
  ✓ CSS Scroll Snap (2021)
  ✓ clamp() (2020)
  ✓ color-scheme (2021)

Baseline 2024 (Newly Available — all major browsers, just arrived):
  ~ :has() (2023) — 89% support
  ~ container queries (2023) — 90% support
  ~ @layer (2022) — 88% support
  ~ text-wrap: balance (2023) — 85% support
  ~ CSS nesting (2023) — 88% support
  ~ oklch() colors (2023) — 87% support

Not Yet Baseline (Limited support):
  ⚠ scroll-driven animations (2023) — 72%
  ⚠ view transitions (2023) — 75%
  ⚠ anchor positioning (2024) — 30%
  ⚠ CSS @scope (2024) — 85%
  ⚠ CSS animation-timeline (2023) — 72%
```

---

## Step 6: JavaScript Module/NoModule Pattern

```html
<!-- ES Modules: modern browsers (2017+) -->
<!-- nomodule: old browsers that don't support modules -->

<!-- Modern browsers execute this, old ones skip it -->
<script type="module" src="/js/app.mjs"></script>

<!-- Old browsers execute this, modern ones skip it -->
<script nomodule src="/js/app.legacy.js"></script>

<!-- Complete differential serving setup -->
<head>
  <!-- Modern CSS: only sent if @supports works -->
  <!-- Old CSS: always sent as link -->
  <link rel="stylesheet" href="/css/base.css">
  
  <!-- Modern features via ES module check -->
  <script>
    // Feature detection for critical path
    const hasModules = 'noModule' in HTMLScriptElement.prototype;
    const hasIntersectionObserver = 'IntersectionObserver' in window;
    
    if (!hasIntersectionObserver) {
      // Load polyfill synchronously
      document.write('<script src="/polyfills/intersection-observer.js"><\/script>');
    }
  </script>
</head>

<body>
  <!-- App code: module (modern) or legacy bundle (old) -->
  <script type="module">
    // Modern: dynamic import, optional chaining, etc.
    const { initApp } = await import('./app-modern.mjs');
    initApp();
  </script>
  <script nomodule src="/js/app-legacy.js"></script>
</body>
```

---

## Step 7: Polyfill Strategies

```javascript
// Feature-detect and polyfill only what's missing

// CSS Custom Properties polyfill (IE11)
if (!CSS.supports('color', 'var(--test)')) {
  import('css-vars-ponyfill').then(({ default: cssVars }) => {
    cssVars({ watch: true, silent: true });
  });
}

// IntersectionObserver polyfill
if (!('IntersectionObserver' in window)) {
  import('intersection-observer').then(() => {
    initLazyLoading();
  });
} else {
  initLazyLoading();
}

// Dialog polyfill
if (!window.HTMLDialogElement) {
  import('dialog-polyfill').then(({ default: dialogPolyfill }) => {
    document.querySelectorAll('dialog').forEach(dialog => {
      dialogPolyfill.registerDialog(dialog);
    });
  });
}

// Progressive enhancement for View Transitions
function navigateWithTransition(url) {
  if (document.startViewTransition) {
    // Modern: animated transition
    return document.startViewTransition(() => navigate(url));
  }
  // Fallback: instant navigation
  return navigate(url);
}

// Scroll-driven animations fallback
if (!CSS.supports('animation-timeline', 'scroll()')) {
  // Polyfill with IntersectionObserver
  document.querySelectorAll('.reveal-on-scroll').forEach(el => {
    const io = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        el.classList.add('visible');
        io.disconnect();
      }
    }, { threshold: 0.1 });
    io.observe(el);
  });
}
```

---

## Step 8: Capstone — @supports Compatibility Checker

```bash
docker run --rm -v /tmp/supports_checker.js:/test.js node:20-alpine node /test.js
```

*(Create the file:)*
```bash
cat > /tmp/supports_checker.js << 'EOF'
var features = [
  {property:"display",value:"grid",baseline:"2017",support:"97%"},
  {property:"display",value:"flex",baseline:"2012",support:"99%"},
  {property:"container-type",value:"inline-size",baseline:"2023",support:"90%"},
  {property:"color",value:"oklch(50% 0.2 250)",baseline:"2023",support:"87%"},
  {property:"animation-timeline",value:"scroll()",baseline:"2023 Limited",support:"72%"},
  {property:"offset-path",value:"path('M0,0 L100,100')",baseline:"2023",support:"88%"},
  {property:":has",value:"selector",baseline:"2023",support:"89%"},
  {property:"view-transition-name",value:"header",baseline:"2024 Limited",support:"75%"},
  {property:"text-wrap",value:"balance",baseline:"2023",support:"85%"},
  {property:"anchor-name",value:"--my-anchor",baseline:"2024 Limited",support:"30%"},
];
console.log("CSS Feature Compatibility Report");
console.log("=".repeat(55));
console.log("Feature".padEnd(30) + "Baseline".padEnd(15) + "Support");
console.log("-".repeat(55));
features.forEach(function(f){
  var status = parseInt(f.support) >= 90 ? "✓" : parseInt(f.support) >= 75 ? "~" : "⚠";
  console.log((f.property + ": " + f.value).substring(0,28).padEnd(30) + f.baseline.padEnd(15) + f.support + " " + status);
});
console.log("\n✓ = Widely supported (90%+)  ~ = Good (75-89%)  ⚠ = Limited (<75%)");
console.log("\n@supports fallback pattern:");
console.log("@supports (container-type: inline-size) {");
console.log("  /* modern container query styles */");
console.log("}");
EOF
docker run --rm -v /tmp/supports_checker.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
CSS Feature Compatibility Report
=======================================================
Feature                       Baseline       Support
-------------------------------------------------------
display: grid                 2017           97% ✓
display: flex                 2012           99% ✓
container-type: inline-size   2023           90% ✓
color: oklch(50% 0.2 250)     2023           87% ~
animation-timeline: scroll()  2023 Limited   72% ⚠
offset-path: path('M0,0 L100  2023           88% ~
:has: selector                2023           89% ~
view-transition-name: header  2024 Limited   75% ~
text-wrap: balance            2023           85% ~
anchor-name: --my-anchor      2024 Limited   30% ⚠

✓ = Widely supported (90%+)  ~ = Good (75-89%)  ⚠ = Limited (<75%)

@supports fallback pattern:
@supports (container-type: inline-size) {
  /* modern container query styles */
}
```

---

## Summary

| Technique | Syntax | Purpose |
|-----------|--------|---------|
| `@supports` | `@supports (display: grid) {}` | Feature detection |
| `@supports not` | `@supports not (display: grid)` | Absence detection |
| `@supports selector()` | `@supports selector(:has(a))` | Selector support |
| Value fallback | Multiple property values | Browser-specific |
| Module/nomodule | `type="module"` / `nomodule` | JS differential serving |
| Dynamic polyfill | `import('polyfill').then(...)` | Conditional loading |
| Baseline check | Baseline 2024 status | Ship decision |
| PE principle | Base → Enhanced | Future-proof |
