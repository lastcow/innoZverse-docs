# Lab 05: Responsive Design

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build truly responsive layouts with mobile-first methodology, fluid typography via `clamp()`, container queries, modern viewport units, intrinsic sizing, and responsive images.

---

## Step 1: Mobile-First Methodology

Mobile-first means: write styles for small screens first, then use `min-width` queries to enhance for larger screens.

```css
/* ❌ Desktop-first: start big, scale down */
.nav { display: flex; gap: 2rem; }
@media (max-width: 768px) { .nav { flex-direction: column; } }

/* ✓ Mobile-first: start small, scale up */
.nav {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

@media (min-width: 640px) {  /* sm */
  .nav { flex-direction: row; gap: 1rem; }
}

@media (min-width: 1024px) { /* lg */
  .nav { gap: 2rem; }
}
```

**Breakpoint system:**
```css
/* Tailwind-inspired breakpoints */
/* sm:  640px  — landscape phones */
/* md:  768px  — tablets */
/* lg:  1024px — laptops */
/* xl:  1280px — desktops */
/* 2xl: 1536px — large screens */
```

> 💡 Mobile-first is better for performance: mobile devices download the minimal CSS first, then progressive enhancements load with media queries.

---

## Step 2: Fluid Typography with clamp()

`clamp(min, preferred, max)` — value is clamped between min and max, tracking preferred in between.

```css
/* Formula: clamp(min-size, min-size + (max-size - min-size) * vw-factor, max-size) */

:root {
  /* Fluid type scale */
  --text-h1: clamp(28px, 21.65px + 1.98vw, 56px);
  --text-h2: clamp(22px, 17.49px + 1.41vw, 42px);
  --text-h3: clamp(18px, 14.85px + 0.98vw, 32px);
  --text-h4: clamp(16px, 14.20px + 0.56vw, 24px);
  --text-h5: clamp(14px, 12.65px + 0.42vw, 20px);
  --text-h6: clamp(13px, 11.88px + 0.35vw, 18px);
  --text-body: clamp(14px, 13.55px + 0.14vw, 16px);
}

h1 { font-size: var(--text-h1); }
h2 { font-size: var(--text-h2); }
body { font-size: var(--text-body); }

/* Fluid spacing */
.section {
  padding-block: clamp(2rem, 5vw, 6rem);
}

/* Fluid gap */
.grid {
  gap: clamp(1rem, 2.5vw, 2rem);
}
```

---

## Step 3: Container Queries

Container queries respond to the **container's** size, not the viewport.

```css
/* 1. Mark parent as a container */
.card-container {
  container-type: inline-size; /* respond to width */
  container-name: card;        /* optional name */
}

/* Shorthand */
.sidebar {
  container: sidebar / inline-size;
}

/* 2. Write queries relative to the container */
@container (min-width: 400px) {
  .card {
    display: flex;
    flex-direction: row;
    gap: 1rem;
  }
}

@container (min-width: 600px) {
  .card {
    grid-template-columns: 200px 1fr;
  }
}

/* Named container query */
@container card (min-width: 500px) {
  .card__title { font-size: 1.5rem; }
}

/* Container units: cqw, cqh, cqi (inline), cqb (block) */
.card__title {
  font-size: clamp(1rem, 3cqi, 2rem); /* 3% of container inline-size */
}
```

---

## Step 4: Modern Viewport Units

```css
/* Problem with 100vh: mobile browser chrome causes overflow */

/* Solution: new viewport units */
.hero {
  height: 100svh; /* small viewport: excludes browser UI */
}

.sticky-footer {
  min-height: 100dvh; /* dynamic: adjusts as browser UI shows/hides */
}

.fixed-panel {
  height: 100lvh; /* large viewport: includes browser UI (same as old 100vh) */
}

/* Inline/block viewport units */
.full-width  { width: 100vi; }  /* 100% of viewport inline axis */
.full-height { height: 100vb; } /* 100% of viewport block axis */

/* Practical pattern */
.app-layout {
  min-height: 100dvh;     /* dynamic, handles mobile chrome */
  min-height: 100svh;     /* fallback for older support */
}
```

---

## Step 5: Intrinsic Sizing

```css
/* min-content: smallest possible width */
.tag {
  width: min-content; /* wraps text at word boundaries */
}

/* max-content: content's natural maximum width (no wrapping) */
.tooltip {
  width: max-content;
  max-width: 300px; /* but cap it */
}

/* fit-content: like max-content but respects the available space */
.caption {
  width: fit-content;
  margin-inline: auto; /* center it */
}

/* Intrinsic sizing in grid */
.grid {
  grid-template-columns:
    min-content      /* fits longest word */
    max-content      /* never wraps */
    fit-content(300px) /* max-content, capped at 300px */
    1fr;             /* remaining space */
}
```

---

## Step 6: Responsive Images

```html
<!-- srcset: provide multiple resolutions -->
<img
  src="photo-800.jpg"
  srcset="photo-400.jpg 400w,
          photo-800.jpg 800w,
          photo-1600.jpg 1600w"
  sizes="(max-width: 640px) 100vw,
         (max-width: 1024px) 50vw,
         800px"
  alt="Descriptive text"
  loading="lazy"
  decoding="async"
>

<!-- picture: art direction (different crops) -->
<picture>
  <source
    media="(max-width: 640px)"
    srcset="photo-square-400.jpg 1x, photo-square-800.jpg 2x"
  >
  <source
    media="(min-width: 641px)"
    srcset="photo-wide-800.jpg 1x, photo-wide-1600.jpg 2x"
  >
  <img src="photo-wide-800.jpg" alt="Descriptive text">
</picture>

<!-- picture: modern formats with fallback -->
<picture>
  <source type="image/avif" srcset="photo.avif">
  <source type="image/webp" srcset="photo.webp">
  <img src="photo.jpg" alt="Descriptive text">
</picture>
```

```css
/* CSS for responsive images */
img {
  max-width: 100%;
  height: auto;
  display: block;
}

/* Aspect ratio container */
.image-container {
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.image-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;    /* cover, contain, fill, none, scale-down */
  object-position: center top;
}
```

---

## Step 7: Complete Responsive Layout

```css
/* Mobile-first responsive page layout */
:root {
  --max-width: 1200px;
  --sidebar-width: 260px;
}

.page {
  display: grid;
  grid-template-areas:
    "header"
    "main"
    "sidebar"
    "footer";
  gap: 1rem;
  padding: 1rem;
  max-width: var(--max-width);
  margin-inline: auto;
}

@media (min-width: 768px) {
  .page {
    grid-template-areas:
      "header  header"
      "main    sidebar"
      "footer  footer";
    grid-template-columns: 1fr var(--sidebar-width);
  }
}

@media (min-width: 1024px) {
  .page { padding: 2rem; gap: 2rem; }
}

.page__header  { grid-area: header; }
.page__main    { grid-area: main; }
.page__sidebar { grid-area: sidebar; }
.page__footer  { grid-area: footer; }
```

---

## Step 8: Capstone — clamp() Type Scale Calculator

```bash
docker run --rm node:20-alpine node -e "
function fluidClamp(minPx, maxPx, minVw, maxVw) {
  var slope = (maxPx - minPx) / (maxVw - minPx);
  var intercept = minPx - slope * minVw;
  return 'clamp(' + minPx + 'px, ' + intercept.toFixed(2) + 'px + ' + (slope*100).toFixed(2) + 'vw, ' + maxPx + 'px)';
}
var scale = [
  {tag:'h1',min:28,max:56},{tag:'h2',min:22,max:42},{tag:'h3',min:18,max:32},
  {tag:'h4',min:16,max:24},{tag:'h5',min:14,max:20},{tag:'h6',min:13,max:18},
  {tag:'p',min:14,max:16},{tag:'small',min:11,max:13}
];
scale.forEach(function(s){
  console.log(s.tag + ': ' + fluidClamp(s.min,s.max,320,1440));
});
"
```

📸 **Verified Output:**
```
h1: clamp(28px, 21.65px + 1.98vw, 56px)
h2: clamp(22px, 17.49px + 1.41vw, 42px)
h3: clamp(18px, 14.85px + 0.98vw, 32px)
h4: clamp(16px, 14.20px + 0.56vw, 24px)
h5: clamp(14px, 12.65px + 0.42vw, 20px)
h6: clamp(13px, 11.88px + 0.35vw, 18px)
p: clamp(14px, 13.55px + 0.14vw, 16px)
small: clamp(11px, 10.55px + 0.14vw, 13px)
```

---

## Summary

| Feature | Syntax | Purpose |
|---------|--------|---------|
| Mobile-first | `@media (min-width: ...)` | Start small, enhance up |
| Fluid type | `clamp(min, vw-calc, max)` | Smooth font scaling |
| Container query | `@container (min-width: ...)` | Component-level responsiveness |
| svh | `100svh` | Safe height (mobile browser) |
| dvh | `100dvh` | Dynamic height |
| min-content | `width: min-content` | Shrink to content |
| fit-content | `width: fit-content` | Content width, space-aware |
| srcset | `srcset="img-400.jpg 400w"` | Resolution switching |
| picture | `<picture><source><img>` | Art direction |
| object-fit | `cover`, `contain` | Image sizing in box |
