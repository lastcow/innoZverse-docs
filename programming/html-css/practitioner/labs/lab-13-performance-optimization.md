# Lab 13: Performance Optimization

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Optimize HTML/CSS performance: extract critical CSS, use resource hints, understand Core Web Vitals (LCP/CLS/INP), leverage `content-visibility`, and implement lazy loading.

---

## Step 1: Critical CSS (Above-the-Fold Inline)

Critical CSS = the minimum styles needed to render above-the-fold content:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>My Page</title>

  <!-- 1. Inline critical CSS (no network request) -->
  <style>
    /* Only what's needed for above-the-fold content */
    *, *::before, *::after { box-sizing: border-box; }
    body { margin: 0; font-family: system-ui, sans-serif; }
    .hero { min-height: 100svh; display: flex; align-items: center; justify-content: center; }
    .nav { position: sticky; top: 0; z-index: 100; background: white; }
    h1 { font-size: clamp(2rem, 5vw, 4rem); }
  </style>

  <!-- 2. Non-critical CSS: async load -->
  <link rel="preload" href="/css/main.css" as="style" onload="this.onload=null;this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="/css/main.css"></noscript>

  <!-- 3. Resource hints (see Step 2) -->
</head>
```

---

## Step 2: Resource Hints

```html
<!-- preconnect: establish connection early (DNS + TCP + TLS) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- dns-prefetch: cheaper than preconnect (DNS only) -->
<link rel="dns-prefetch" href="//cdn.example.com">
<link rel="dns-prefetch" href="//analytics.example.com">

<!-- preload: critical resources needed for current page -->
<link rel="preload" href="/fonts/inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/css/critical.css" as="style">
<link rel="preload" href="/images/hero.webp" as="image">
<link rel="preload" href="/js/main.js" as="script">

<!-- prefetch: resources for likely next navigation -->
<link rel="prefetch" href="/about.html">
<link rel="prefetch" href="/images/gallery-1.webp" as="image">

<!-- modulepreload: ES modules specifically -->
<link rel="modulepreload" href="/js/app.mjs">
```

**Priority:**
- `preconnect` → `preload` → page load → `prefetch` → idle

---

## Step 3: async vs defer Scripts

```html
<!-- Normal: blocks HTML parsing -->
<script src="app.js"></script>

<!-- async: parallel download, executes immediately when ready -->
<!-- Order NOT guaranteed, runs before DOMContentLoaded if ready -->
<script async src="analytics.js"></script>   <!-- perfect for analytics -->
<script async src="ads.js"></script>          <!-- independent scripts -->

<!-- defer: parallel download, executes AFTER HTML parsed -->
<!-- Order IS guaranteed, runs before DOMContentLoaded -->
<script defer src="app.js"></script>          <!-- perfect for most scripts -->
<script defer src="components.js"></script>   <!-- runs in order with app.js -->

<!-- type="module": automatic defer behavior -->
<script type="module" src="app.mjs"></script>

<!-- Inline scripts: use defer pattern -->
<script>
  // This runs synchronously — move it or use DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => {
    initApp();
  });
</script>
```

---

## Step 4: Core Web Vitals

**LCP — Largest Contentful Paint** (target: ≤2.5s)
```html
<!-- Mark hero image for priority loading -->
<img
  src="/hero.webp"
  alt="..."
  fetchpriority="high"    <!-- LCP optimization -->
  loading="eager"         <!-- don't lazy-load LCP image -->
  decoding="async"
>

<!-- Preload LCP image -->
<link rel="preload" href="/hero.webp" as="image" fetchpriority="high">
```

**CLS — Cumulative Layout Shift** (target: ≤0.1)
```html
<!-- Always set width/height to prevent CLS -->
<img src="photo.jpg" alt="..." width="800" height="600">

<!-- Reserve space for async content -->
<div style="min-height: 200px;"><!-- ads load here --></div>

<!-- Avoid inserting content above existing content -->
```

```css
/* Prevent CLS from fonts */
@font-face {
  font-family: 'MyFont';
  font-display: optional; /* or: swap + size-adjust */
}

/* Size-adjust: match fallback font to web font */
@font-face {
  font-family: 'MyFont-fallback';
  src: local('Arial');
  ascent-override: 92.7%;
  descent-override: 24.1%;
  line-gap-override: 0%;
  size-adjust: 107.4%;
}
```

**INP — Interaction to Next Paint** (target: ≤200ms)
```javascript
// Break up long tasks
// ❌ Blocks main thread
function heavyWork() {
  for (let i = 0; i < 100000; i++) { /* sync work */ }
}

// ✓ Yield to browser between chunks
async function heavyWorkChunked(items) {
  for (let i = 0; i < items.length; i++) {
    process(items[i]);
    if (i % 100 === 0) await new Promise(r => setTimeout(r, 0));
  }
}
```

---

## Step 5: content-visibility

```css
/* Skip rendering off-screen content */
.long-article section {
  content-visibility: auto;
  contain-intrinsic-size: 0 500px; /* estimated height (prevents scroll jump) */
}

/* Skip all rendering */
.offscreen {
  content-visibility: hidden; /* persists rendering state — fast show/hide */
}

/* Visible (default) */
.always-render {
  content-visibility: visible;
}

/* Combined with CSS contain */
.card-list-item {
  content-visibility: auto;
  contain-intrinsic-size: auto 200px; /* auto: learns actual size */
  contain: layout paint style;        /* additional containment */
}
```

> 💡 Google reported up to 7× rendering speedup using `content-visibility: auto` on a news page with thousands of off-screen articles.

---

## Step 6: loading=lazy and Image Optimization

```html
<!-- Lazy load all images except above-the-fold -->
<img src="photo.jpg" alt="..." loading="lazy" decoding="async">

<!-- Hero image: DON'T lazy load -->
<img src="hero.jpg" alt="..." loading="eager" fetchpriority="high">

<!-- Responsive images with lazy loading -->
<img
  src="photo-800.jpg"
  srcset="photo-400.jpg 400w, photo-800.jpg 800w, photo-1600.jpg 1600w"
  sizes="(max-width: 640px) 100vw, 50vw"
  alt="..."
  loading="lazy"
  decoding="async"
  width="800"
  height="600"
>

<!-- Lazy iframe (e.g., embedded videos) -->
<iframe
  src="https://www.youtube.com/embed/abc"
  loading="lazy"
  title="Video title"
  width="560"
  height="315"
></iframe>
```

---

## Step 7: CSS Performance Patterns

```css
/* ✓ Composite-only animations (GPU) */
.animate {
  transform: translateX(100px);  /* GPU layer */
  opacity: 0.8;                  /* GPU layer */
  filter: blur(4px);             /* GPU layer */
}

/* ❌ Avoid triggering layout/paint in animations */
/* Animating these causes layout reflow: */
/* width, height, top, left, margin, padding, border */

/* ✓ Use transform instead of top/left */
.bad  { position: absolute; left: 100px; } /* triggers layout */
.good { transform: translateX(100px); }    /* GPU only */

/* ✓ CSS containment */
.widget {
  contain: layout paint; /* isolates layout/paint */
}

/* ❌ Avoid expensive selectors */
* { } /* matches everything */
div > * > span { } /* deep descendant */

/* ✓ Efficient selectors */
.specific-class { }
[data-type] { }
```

---

## Step 8: Capstone — CSS Minifier

```bash
docker run --rm node:20-alpine node -e "
function minify(css) {
  return css
    .replace(/\/\*[\s\S]*?\*\//g, '')
    .replace(/\s+/g, ' ')
    .replace(/\s*([{};:,>~+])\s*/g, '\$1')
    .replace(/;\}/g, '}')
    .trim();
}
var css = '/* Critical CSS */ .hero { display: flex; flex-direction: column; align-items: center; padding: 2rem; } .nav { position: sticky; top: 0; z-index: 100; background: white; }';
var minified = minify(css);
console.log('Original length:', css.length);
console.log('Minified length:', minified.length);
console.log('Savings:', ((1 - minified.length/css.length)*100).toFixed(1) + '%');
console.log('');
console.log('Minified:', minified);
"
```

📸 **Verified Output:**
```
Original length: 171
Minified length: 129
Savings: 24.6%

Minified: .hero{display:flex;flex-direction:column;align-items:center;padding:2rem}.nav{position:sticky;top:0;z-index:100;background:white}
```

---

## Summary

| Technique | Implementation | Metric Impact |
|-----------|---------------|---------------|
| Critical CSS inline | `<style>` in `<head>` | FCP, LCP |
| preload | `<link rel="preload">` | LCP |
| preconnect | `<link rel="preconnect">` | TTFB |
| defer | `<script defer>` | TTI |
| content-visibility | `content-visibility: auto` | INP, rendering |
| contain-intrinsic-size | `auto 500px` | CLS |
| fetchpriority="high" | On LCP image | LCP |
| loading="lazy" | On below-fold images | LCP, bandwidth |
| width/height on images | `<img width="800">` | CLS |
| Transform animations | `transform` not `top/left` | INP, FPS |
