# Lab 07: Responsive Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Fluid design system engineering: `clamp()`-based type and spacing scales (minor/major third ratios), container queries for component-level responsiveness, intrinsic layout with auto-fill/auto-fit, and responsive image art direction.

---

## Step 1: Fluid Type Scale — Math

```
Musical scale ratios for typography:
  Minor Third:  1.200 (comfortable, compact)
  Major Third:  1.250 (clear hierarchy)
  Perfect Fourth: 1.333 (dramatic, common)
  Golden Ratio: 1.618 (bold hierarchy)

clamp(min, preferred, max)
  min = minimum at small viewport (320px)
  max = maximum at large viewport (1280px)
  preferred = slope * 100vw + intercept

Slope = (maxPx - minPx) / (maxVw - minVw)
Intercept = minPx - slope * minVw
```

---

## Step 2: Fluid Type Scale Generator

```javascript
// Node.js type scale generator
const minVw = 320, maxVw = 1280;

function fluidClamp(minPx, maxPx) {
  const minRem = (minPx / 16).toFixed(4);
  const maxRem = (maxPx / 16).toFixed(4);
  const slope = (maxPx - minPx) / (maxVw - minVw);
  const intercept = minPx - slope * minVw;
  const vw = (slope * 100).toFixed(4);
  const rem = (intercept / 16).toFixed(4);
  return `clamp(${minRem}rem, ${vw}vw + ${rem}rem, ${maxRem}rem)`;
}

// Minor third scale (1.2 ratio)
const minorThirdScale = [
  { name: 'xs',   min: 12, max: 14 },
  { name: 'sm',   min: 14, max: 16 },
  { name: 'base', min: 16, max: 18 },
  { name: 'lg',   min: 18, max: 22 },
  { name: 'xl',   min: 20, max: 28 },
  { name: '2xl',  min: 24, max: 36 },
  { name: '3xl',  min: 30, max: 48 },
  { name: '4xl',  min: 36, max: 64 },
];

minorThirdScale.forEach(({ name, min, max }) => {
  console.log(`--fs-${name}: ${fluidClamp(min, max)};`);
});
```

---

## Step 3: Fluid Spacing Scale

```css
/* Fluid spacing using clamp */
:root {
  --space-1:  clamp(0.25rem, 0.5vw, 0.5rem);
  --space-2:  clamp(0.5rem,  1vw,   1rem);
  --space-3:  clamp(0.75rem, 1.5vw, 1.5rem);
  --space-4:  clamp(1rem,    2vw,   2rem);
  --space-6:  clamp(1.5rem,  3vw,   3rem);
  --space-8:  clamp(2rem,    4vw,   4rem);
  --space-12: clamp(3rem,    6vw,   6rem);
  --space-16: clamp(4rem,    8vw,   8rem);
}

/* One-up / one-down pairs (Utopia method) */
.flow > * + * {
  margin-block-start: var(--flow-space, var(--space-4));
}
```

---

## Step 4: Container Queries Architecture

```css
/* Define containment contexts */
.page-layout { container-type: inline-size; container-name: layout; }
.card-wrapper { container-type: inline-size; container-name: card; }
.sidebar { container-type: inline-size; container-name: sidebar; }

/* Layout responds to its container, not viewport */
@container layout (width >= 768px) {
  .content-area {
    display: grid;
    grid-template-columns: 1fr 300px;
    gap: var(--space-6);
  }
}

/* Card responds to its own container */
@container card (width >= 400px) {
  .card {
    display: flex;
    flex-direction: row;
  }
  .card-image {
    width: 40%;
    flex-shrink: 0;
  }
}

@container card (width < 400px) {
  .card {
    flex-direction: column;
  }
  .card-image {
    width: 100%;
    aspect-ratio: 16 / 9;
  }
}

/* Sidebar pattern */
@container sidebar (width >= 240px) {
  .sidebar-nav .nav-label { display: block; }
}
@container sidebar (width < 240px) {
  .sidebar-nav .nav-label { display: none; }
  .sidebar-nav .nav-icon { margin: 0 auto; }
}
```

> 💡 Container queries solve the "component in unknown context" problem. A card component can adapt to being in a sidebar, modal, or full-width layout without media query hacks.

---

## Step 5: Intrinsic Layout — auto-fill vs auto-fit

```css
/* auto-fill: creates as many tracks as fit (empty columns remain) */
.grid-fill {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

/* auto-fit: collapses empty tracks (items stretch to fill) */
.grid-fit {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-4);
}

/* RAM technique: Repeat, Auto, Minmax */
.ram {
  --min: 280px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(var(--min), 100%), 1fr));
}

/* Sidebar + main intrinsic layout (Holy Grail) */
.holy-grail {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
}

.holy-grail > .sidebar {
  flex: 1 1 280px;  /* grow, shrink, basis */
  min-width: 0;
}

.holy-grail > .main {
  flex: 3 1 0;      /* 3x growth ratio vs sidebar */
  min-width: 0;
}
```

---

## Step 6: Responsive Images

```html
<!-- Art direction: different images at breakpoints -->
<picture>
  <source media="(width >= 1200px)"
          srcset="/img/hero-wide.webp 1200w, /img/hero-wide-2x.webp 2400w"
          sizes="100vw">
  <source media="(width >= 768px)"
          srcset="/img/hero-tablet.webp 800w, /img/hero-tablet-2x.webp 1600w"
          sizes="100vw">
  <!-- Fallback: mobile -->
  <img src="/img/hero-mobile.webp"
       srcset="/img/hero-mobile.webp 400w, /img/hero-mobile-2x.webp 800w"
       sizes="100vw"
       width="400" height="600"
       alt="Product showcase"
       loading="lazy"
       decoding="async">
</picture>

<!-- Fluid image in grid context -->
<img srcset="product-320.webp 320w,
             product-640.webp 640w,
             product-960.webp 960w"
     sizes="(max-width: 480px) 100vw,
            (max-width: 1024px) 50vw,
            33vw"
     src="product-640.webp"
     alt="Product image"
     width="960" height="720">
```

---

## Step 7: Viewport Units — svh/dvh/lvh

```css
/* Legacy vh had issues with mobile browser chrome */
.hero-old { min-height: 100vh; } /* jumps on mobile */

/* Modern units */
.hero {
  /* svh: Small Viewport Height (browser chrome visible) */
  min-height: 100svh;
}

.modal-overlay {
  /* dvh: Dynamic Viewport Height (changes as chrome hides/shows) */
  height: 100dvh;
}

.background-fill {
  /* lvh: Large Viewport Height (browser chrome hidden) */
  min-height: 100lvh;
}

/* Safe area insets for notched devices */
.bottom-nav {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}
```

---

## Step 8: Capstone — Fluid Type Scale

```bash
docker run --rm node:20-alpine node -e "
const minVw=320, maxVw=1280;
const sizes = [
  {name:'xs', minPx:12, maxPx:14},{name:'sm', minPx:14, maxPx:16},
  {name:'base',minPx:16, maxPx:18},{name:'lg', minPx:18, maxPx:22},
  {name:'xl', minPx:20, maxPx:28},{name:'2xl',minPx:24, maxPx:36},
  {name:'3xl',minPx:30, maxPx:48},{name:'4xl',minPx:36, maxPx:64},
];
console.log('=== Fluid Type Scale (clamp) ===');
sizes.forEach(({name,minPx,maxPx})=>{
  const minRem=(minPx/16).toFixed(4), maxRem=(maxPx/16).toFixed(4);
  const slope=(maxPx-minPx)/(maxVw-minVw);
  const intercept=minPx-slope*minVw;
  const vw=(slope*100).toFixed(4), rem=(intercept/16).toFixed(4);
  console.log('--fs-'+name+': clamp('+minRem+'rem, '+vw+'vw + '+rem+'rem, '+maxRem+'rem)');
});
"
```

📸 **Verified Output:**
```
=== Fluid Type Scale (clamp) ===
--fs-xs: clamp(0.7500rem, 0.2083vw + 0.7083rem, 0.8750rem)
--fs-sm: clamp(0.8750rem, 0.2083vw + 0.8333rem, 1.0000rem)
--fs-base: clamp(1.0000rem, 0.2083vw + 0.9583rem, 1.1250rem)
--fs-lg: clamp(1.1250rem, 0.4167vw + 1.0417rem, 1.3750rem)
--fs-xl: clamp(1.2500rem, 0.8333vw + 1.0833rem, 1.7500rem)
--fs-2xl: clamp(1.5000rem, 1.2500vw + 1.2500rem, 2.2500rem)
--fs-3xl: clamp(1.8750rem, 1.8750vw + 1.5000rem, 3.0000rem)
--fs-4xl: clamp(2.2500rem, 2.9167vw + 1.6667rem, 4.0000rem)
```

---

## Summary

| Technique | CSS Feature | Use Case |
|-----------|------------|----------|
| Fluid type | `clamp(min, vw + rem, max)` | Scale-aware typography |
| Fluid spacing | `clamp()` spacing tokens | Proportional whitespace |
| Component layout | Container queries | Self-adapting components |
| Intrinsic grid | `auto-fill/auto-fit` | No breakpoints needed |
| Sidebar | `flex: 1 1 280px` | Wraps naturally |
| Art direction | `<picture>` + `<source media>` | Different crops |
| Viewport | `svh/dvh/lvh` | Mobile-correct sizing |
