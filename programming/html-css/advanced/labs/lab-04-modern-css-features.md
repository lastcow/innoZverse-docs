# Lab 04: Modern CSS Features

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Explore cutting-edge CSS: native nesting with `&`, `@scope`, advanced `:has()` patterns, CSS anchor positioning, View Transitions API, and scroll-driven animations.

---

## Step 1: Native CSS Nesting

```css
/* CSS nesting (baseline 2023) — no preprocessor needed */

.card {
  background: white;
  border-radius: 8px;
  padding: 1rem;

  /* Nested: & refers to .card */
  & .card__title {
    font-size: 1.25rem;
    color: #111;
  }

  /* Pseudo-class on the parent */
  &:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    transform: translateY(-2px);
  }

  /* Pseudo-element */
  &::before {
    content: '';
    display: block;
    height: 4px;
    background: var(--color-primary);
    border-radius: 8px 8px 0 0;
  }

  /* Modifier (BEM-like) */
  &.card--featured {
    border-color: gold;
  }

  /* Descendant (without &) — shorthand */
  .card__body {
    color: #666;
    line-height: 1.6;
  }

  /* Media query inside rule */
  @media (min-width: 768px) {
    & {
      padding: 1.5rem;
    }
  }

  /* Container query inside rule */
  @container (min-width: 400px) {
    & {
      display: flex;
      gap: 1rem;
    }
  }
}
```

> 💡 Starting a nested rule with `&` is safe in all contexts. Without `&`, the nested selector is treated as a descendant — but `&` is clearer and required when nesting pseudo-elements.

---

## Step 2: @scope

```css
/* @scope: style within a boundary without high specificity */

@scope (.card) {
  /* Only applies inside .card — no :where() specificity penalty */
  .title { font-size: 1.25rem; }
  .body  { color: #666; }
  img    { border-radius: 4px; }
}

/* @scope with lower boundary: style between two selectors */
@scope (.article) to (.comments) {
  /* Applies inside .article but NOT inside .comments */
  p { line-height: 1.7; }
  a { color: var(--color-primary); }
}

/* Practical: override styles in specific zones */
@scope (.hero) {
  h1 { color: white; font-size: 4rem; }
  p  { color: rgba(255,255,255,0.8); }
}

@scope (.sidebar) {
  h1 { color: inherit; font-size: 1.125rem; }
}
```

---

## Step 3: Advanced :has() Patterns

```css
/* :has() = parent selector + relational selector */

/* Style parent based on child state */
.form:has(input:invalid) {
  border-left: 3px solid red;
}

/* Card with image vs without */
.card:has(.card__image) .card__body {
  padding-top: 0;
}
.card:not(:has(.card__image)) {
  background: var(--color-surface-2);
}

/* Count-based layouts via :has() */
.gallery:has(:nth-child(4)) {
  grid-template-columns: repeat(2, 1fr);
}
.gallery:has(:nth-child(7)) {
  grid-template-columns: repeat(3, 1fr);
}

/* Navigation: active link in group */
nav:has(a[aria-current="page"]) {
  border-bottom: 2px solid currentColor;
}

/* Sibling targeting */
h2:has(+ p) {
  margin-bottom: 0.25rem; /* less space when followed by paragraph */
}

/* Form: required fields indicator */
form:has(input[required]) label {
  /* Add required indicator to all labels in forms that have required fields */
}
.field:has(input:required) .field__label::after {
  content: " *";
  color: red;
}

/* Table: style rows where checkbox is checked */
tr:has(input[type="checkbox"]:checked) {
  background: #eff6ff;
}
```

---

## Step 4: CSS Anchor Positioning

```css
/* Define an anchor */
.trigger-button {
  anchor-name: --tooltip-anchor;
}

/* Position relative to anchor */
.tooltip {
  position-anchor: --tooltip-anchor;
  position: absolute;
  
  /* anchor() function: reference anchor edges */
  top:  anchor(bottom);      /* top of tooltip = bottom of anchor */
  left: anchor(center);      /* left of tooltip = center of anchor */
  
  /* Or use inset shorthand */
  inset-area: block-end center; /* above/below, aligned center */
  
  /* Flip if overflows viewport */
  position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;
  
  /* Center tooltip relative to anchor */
  translate: -50% 0.5rem;
}

/* Tooltip with margin from anchor */
.tooltip {
  anchor-name: inherit;
  position: absolute;
  position-anchor: --tooltip-anchor;
  bottom: calc(anchor(top) + 8px);
  left: anchor(center);
  transform: translateX(-50%);
}
```

---

## Step 5: View Transitions API

```javascript
// Triggered view transition
document.getElementById('nav-link').addEventListener('click', async (e) => {
  e.preventDefault();
  const href = e.currentTarget.href;
  
  if (!document.startViewTransition) {
    // Fallback: no transition
    window.location.href = href;
    return;
  }
  
  const transition = document.startViewTransition(async () => {
    // DOM update happens here — browser captures before/after
    const response = await fetch(href);
    const html = await response.text();
    const doc = new DOMParser().parseFromString(html, 'text/html');
    document.body.innerHTML = doc.body.innerHTML;
  });
  
  await transition.finished;
});
```

```css
/* View transition animations */

/* Default: cross-fade */
::view-transition-old(root) {
  animation: fade-out 0.3s ease;
}
::view-transition-new(root) {
  animation: fade-in 0.3s ease;
}

/* Named transitions: element-specific */
.hero-image {
  view-transition-name: hero;  /* mark for morphing */
}

/* Hero morphs smoothly between pages */
::view-transition-old(hero) {
  animation: 0.5s ease-in-out both;
}
::view-transition-new(hero) {
  animation: 0.5s ease-in-out both;
}

/* Slide navigation transition */
@keyframes slide-from-right {
  from { transform: translateX(100%); }
}
@keyframes slide-to-left {
  to { transform: translateX(-100%); }
}

::view-transition-new(root) {
  animation: slide-from-right 0.4s ease;
}
::view-transition-old(root) {
  animation: slide-to-left 0.4s ease;
}

/* Respect reduced motion */
@media (prefers-reduced-motion) {
  ::view-transition-old(root),
  ::view-transition-new(root) {
    animation: none;
  }
}
```

---

## Step 6: Scroll-Driven Animations

```css
/* animation-timeline: scroll() — progress = scroll position */
.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 4px;
  background: var(--color-primary);
  transform-origin: left;
  animation: progress linear both;
  animation-timeline: scroll(root block); /* scroll root element, block axis */
}

@keyframes progress {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}

/* animation-timeline: view() — progress = element in viewport */
.section {
  animation: reveal linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 100%; /* play during entry into viewport */
}

@keyframes reveal {
  from { opacity: 0; transform: translateY(30px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Scroll-driven parallax */
.hero-bg {
  animation: parallax linear both;
  animation-timeline: scroll(root);
}

@keyframes parallax {
  to { transform: translateY(30%); }
}

/* Image reveal on scroll */
.gallery-item {
  clip-path: inset(0 100% 0 0);
  animation: clip-reveal linear both;
  animation-timeline: view();
  animation-range: entry 10% entry 60%;
}

@keyframes clip-reveal {
  to { clip-path: inset(0 0% 0 0); }
}
```

---

## Step 7: Scroll Snap

```css
/* Scroll snap container */
.carousel {
  display: flex;
  overflow-x: auto;
  scroll-snap-type: x mandatory; /* or: x proximity */
  scroll-behavior: smooth;
  gap: 1rem;
  padding: 1rem;
  
  /* Hide scrollbar visually */
  scrollbar-width: none; /* Firefox */
  &::-webkit-scrollbar { display: none; }
}

/* Snap items */
.carousel__item {
  flex: 0 0 80%;
  max-width: 400px;
  scroll-snap-align: start; /* start, center, end */
  scroll-snap-stop: always; /* prevent skipping */
}

/* Vertical scroll snap */
.full-page-scroll {
  height: 100svh;
  overflow-y: scroll;
  scroll-snap-type: y mandatory;
}

.full-page-scroll section {
  height: 100svh;
  scroll-snap-align: start;
}
```

---

## Step 8: Capstone — CSS Feature Compatibility Checker

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
```

---

## Summary

| Feature | Syntax | Support 2024 |
|---------|--------|-------------|
| CSS nesting | `& .child {}` | 88%+ |
| `@scope` | `@scope (.card) {}` | 85%+ |
| `:has()` advanced | `:has(input:invalid)` | 89%+ |
| Anchor positioning | `anchor-name: --x; top: anchor(bottom)` | 30% (limited) |
| View Transitions | `document.startViewTransition()` | Chrome/Edge |
| `::view-transition-*` | `::view-transition-new(hero)` | Chrome/Edge |
| Scroll timeline | `animation-timeline: scroll()` | 72% |
| View timeline | `animation-timeline: view()` | 72% |
| animation-range | `entry 0% entry 100%` | 72% |
| Scroll snap | `scroll-snap-type: x mandatory` | 97%+ |
