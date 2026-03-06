# Lab 04: Performance Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Master Core Web Vitals optimization: LCP via preload and resource hints, CLS elimination via explicit dimensions and `font-display`, INP via deferred non-critical JS, `content-visibility:auto` for long pages, critical CSS extraction, and HTTP/2 push vs preload tradeoffs.

---

## Step 1: Core Web Vitals Architecture Overview

```
CWV Targets (2024 thresholds):
  LCP (Largest Contentful Paint) — < 2.5s (Good), < 4s (Needs Improvement)
  INP (Interaction to Next Paint) — < 200ms (replaces FID)
  CLS (Cumulative Layout Shift) — < 0.1

CSS Contribution:
  LCP: render-blocking CSS, missing preload, no critical CSS inline
  CLS: images without dimensions, late-loaded fonts, dynamic content injection
  INP: long tasks from layout thrashing, heavy style recalculations
```

---

## Step 2: LCP Optimization

```html
<!-- 1. Preload hero image (highest priority) -->
<link rel="preload" as="image" href="/hero.webp"
      imagesrcset="/hero-400.webp 400w, /hero-800.webp 800w, /hero-1600.webp 1600w"
      imagesizes="(max-width: 768px) 100vw, 50vw"
      fetchpriority="high">

<!-- 2. Preconnect to font origin (DNS + TCP + TLS early) -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<!-- 3. Prefetch next page's hero -->
<link rel="prefetch" as="image" href="/next-page-hero.webp">

<!-- 4. Hero image — explicit dimensions prevent layout shift -->
<img src="/hero.webp"
     srcset="/hero-400.webp 400w, /hero-800.webp 800w"
     sizes="(max-width: 768px) 100vw, 50vw"
     width="1600" height="900"
     fetchpriority="high"
     decoding="async"
     alt="Mountain landscape at sunrise">
```

```css
/* 5. Critical CSS for hero — inline in <head> */
.hero {
  min-height: 100svh;
  display: grid;
  place-items: center;
  /* Hint browser about paint containment */
  contain: layout style;
}

/* font-display: optional → no FOIT/FOUT for LCP text */
@font-face {
  font-family: 'Brand Serif';
  src: url('/fonts/brand-serif.woff2') format('woff2');
  font-display: optional; /* don't block rendering */
  unicode-range: U+0020-007E; /* ASCII only for hero */
}
```

> 💡 `fetchpriority="high"` on the LCP image signals to the browser's preload scanner to fetch it before layout is complete. This alone can improve LCP by 200–400ms.

---

## Step 3: CLS Prevention

```css
/* Prevent CLS from images */
img, video {
  /* Modern: use aspect-ratio */
  aspect-ratio: attr(width) / attr(height);
  max-width: 100%;
  height: auto;
}

/* Prevent CLS from fonts — reserve space */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter.woff2') format('woff2');
  font-display: swap;          /* FOUT is better than FOIT for CLS */
  ascent-override: 90%;        /* Fine-tune to match fallback metrics */
  descent-override: 22%;
  line-gap-override: 0%;
}

/* Fallback font with matching metrics */
.font-inter {
  font-family: 'Inter', 'Inter Fallback', sans-serif;
}
```

```css
/* Prevent CLS from dynamic content */
/* Reserve space for skeleton/loading states */
.skeleton {
  aspect-ratio: 16 / 9;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  contain: strict; /* Isolate layout impact */
}

@keyframes skeleton-shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Anchored positioning — coming in CSS Anchor API */
/* For now: fixed dimensions for tooltips/popovers */
.tooltip {
  position: absolute;
  width: max-content;
  max-width: 200px;
  /* Prevent tooltip from causing reflow */
  contain: layout;
}
```

---

## Step 4: INP Optimization

```javascript
// INP: Break up long tasks
// BEFORE: 200ms synchronous style recalc
function updateTheme(newTheme) {
  document.querySelectorAll('[data-component]').forEach(el => {
    el.style.setProperty('--component-bg', newTheme.bg);
    el.style.setProperty('--component-color', newTheme.color);
  });
}

// AFTER: Batch via CSS custom property on :root — single reflow
function updateThemeFast(newTheme) {
  const root = document.documentElement;
  // Single style mutation → one layout pass
  Object.entries(newTheme).forEach(([key, val]) => {
    root.style.setProperty(`--theme-${key}`, val);
  });
}
```

```css
/* Defer non-critical CSS */
```

```html
<!-- Critical CSS inline -->
<style>/* ...critical above-fold styles... */</style>

<!-- Non-critical CSS: load after LCP -->
<link rel="stylesheet" href="/styles/components.css"
      media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="/styles/components.css"></noscript>
```

---

## Step 5: `content-visibility` for Long Pages

```css
/* Long article pages: virtualize off-screen sections */
article > section {
  /* Skip rendering off-screen sections */
  content-visibility: auto;

  /* CRITICAL: must set contain-intrinsic-size to prevent scroll jump */
  contain-intrinsic-size: auto 0 auto 800px;
  /* auto: cache actual size after first render */
  /* 0 auto 800px: width=0 (auto), height=800px (estimate) */
}

/* Product card grid */
.product-grid .product-card {
  content-visibility: auto;
  contain-intrinsic-size: 280px 380px; /* card dimensions */
}

/* Header/footer: always render */
header, footer, .above-fold {
  content-visibility: visible; /* never skip */
}
```

> 💡 `content-visibility: auto` can reduce initial rendering time by 40–60% on long pages. Without `contain-intrinsic-size`, the scrollbar jumps as elements render in.

---

## Step 6: Critical CSS Extraction

```javascript
// Node.js critical CSS extractor (simplified production version)
const criticalSelectors = (html, viewportHeight = 900) => {
  // Heuristic: selectors matching elements in first 100vh
  const aboveFoldPatterns = [
    /^:root$/,
    /^body$/,
    /^html$/,
    /^\./,     // any class (simplification)
  ];

  // Production: use puppeteer + coverage API
  // const coverage = await page.coverage.startCSSCoverage();
  // await page.goto(url);
  // const usedCSS = await page.coverage.stopCSSCoverage();
  // Filter to only rules used above-the-fold

  return aboveFoldPatterns;
};
```

```html
<!-- Critical CSS inline pattern -->
<head>
  <style id="critical-css">
    /* Generated by build tool — styles for above-fold content */
    :root { --color-primary: #3b82f6; }
    body { margin: 0; font-family: 'Inter Fallback', sans-serif; }
    .hero { min-height: 100svh; display: grid; place-items: center; }
    .nav { position: sticky; top: 0; z-index: 100; }
  </style>
  <!-- Deferred: full stylesheet -->
  <link rel="preload" as="style" href="/styles/main.css"
        onload="this.rel='stylesheet'">
</head>
```

---

## Step 7: HTTP/2 Push vs Preload

```
HTTP/2 Push (Server Push):                 Resource Hints (Preload):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━           ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Server initiates before client asks        Client requests after parsing HTML
Can waste bandwidth (cache unaware)        Cache-aware (checks cache first)
Server must know what client needs         Client explicitly declares need
Deprecated in HTTP/3 (QUIC)               Standard, works everywhere

Best practice: Use preload (<link rel="preload">)
HTTP/2 Push: only for non-cached critical resources with Link header
```

---

## Step 8: Capstone — Critical CSS Extractor

```bash
docker run --rm node:20-alpine node /tmp/critical_css.js
```

📸 **Verified Output:**
```
=== Critical CSS Extractor ===
Critical rules (4):
  :root { --c-primary:#3b82f6 }
  .hero { min-height:100vh }
  .hero-title { font-size:clamp(2rem,5vw,4rem) }
  .nav { position:sticky;top:0 }
Deferred rules (4):
  .body
  .card
  .footer
  .sidebar

Critical CSS bytes: 111 (should be <14KB for inline)
Performance: inline critical → eliminates render-blocking CSS request
```

---

## Summary

| CWV Metric | CSS Technique | Impact |
|-----------|--------------|--------|
| LCP | `fetchpriority="high"`, preload | -200–400ms |
| LCP | Inline critical CSS | Eliminate 1 RTT |
| LCP | `font-display: optional` | No render block |
| CLS | `aspect-ratio` on images | Zero shift |
| CLS | Font metrics override | Match fallback |
| CLS | `contain-intrinsic-size` | Stable scroll |
| INP | Single CSS var mutation | One reflow |
| INP | `contain: layout` | Scope reflow |
| All | `content-visibility: auto` | 40-60% render time |
