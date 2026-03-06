# Lab 09: CSS Typography

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master modern web typography: variable fonts with `font-variation-settings`, `font-display` strategies, system font stacks, fluid type scales, `text-wrap: balance`, optical sizing, and multi-line truncation.

---

## Step 1: Variable Fonts

Variable fonts encode multiple type styles in a single file, controlled via CSS axes.

```css
/* @font-face for variable font */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/Inter.var.woff2') format('woff2 supports variations'),
       url('/fonts/Inter.var.woff2') format('woff2'); /* fallback */
  font-weight: 100 900;    /* range for variable font */
  font-style: normal;
  font-display: swap;
}

/* Standard axes (registered): */
/* wght — weight: 100 to 900 */
/* wdth — width: condensed to expanded */
/* ital — italic: 0 or 1 */
/* slnt — slant: -90 to 90 degrees */
/* opsz — optical size */

/* font-variation-settings: 'axis' value */
.heading {
  font-family: 'Inter', sans-serif;
  font-variation-settings:
    'wght' 800,    /* bold */
    'opsz' 32;     /* optical size for display text */
}

.body-text {
  font-variation-settings:
    'wght' 400,
    'opsz' 14;
}

/* Prefer font-weight for standard axes (it maps to wght) */
h1 { font-weight: 800; }  /* browser maps to wght 800 */
p  { font-weight: 400; }

/* Custom axes (use 4-char uppercase tags) */
.display {
  font-variation-settings: 'GRAD' 150, 'SOFT' 0;
}

/* Animate variable font */
@keyframes font-pulse {
  0%, 100% { font-variation-settings: 'wght' 400; }
  50%       { font-variation-settings: 'wght' 800; }
}

.animated-text {
  animation: font-pulse 2s ease-in-out infinite;
}
```

> 💡 Variable fonts can reduce HTTP requests (one file instead of 4-8 font weights) and save bandwidth. Check support at `variablefonts.io`.

---

## Step 2: font-display

Controls how fonts behave while loading:

```css
@font-face {
  font-family: 'MyFont';
  src: url('/fonts/myfont.woff2') format('woff2');
  
  /* font-display values: */
  /* auto      — browser decides (usually block) */
  /* block     — invisible text until font loads (FOIT) */
  /* swap      — use fallback, swap when ready (FOUT) — best for readability */
  /* fallback  — 100ms block, 3s swap window, then keep fallback */
  /* optional  — 100ms block, no swap (best for performance) */
  
  font-display: swap;
}
```

**Recommendations:**
- `swap` — Body text: readability over flash
- `optional` — Non-critical display fonts
- `fallback` — Balance between appearance and performance

---

## Step 3: System Font Stacks

Use system fonts for zero-latency text rendering:

```css
/* Modern system UI stack */
body {
  font-family:
    system-ui,          /* generic system font keyword */
    -apple-system,      /* macOS/iOS */
    BlinkMacSystemFont, /* Chrome on macOS */
    'Segoe UI',         /* Windows */
    Roboto,             /* Android/Chrome OS */
    Oxygen,             /* KDE Linux */
    Ubuntu,             /* Ubuntu Linux */
    Cantarell,          /* GNOME Linux */
    'Helvetica Neue',   /* older macOS */
    Arial,              /* wide fallback */
    sans-serif;
}

/* Monospace */
code, pre, kbd {
  font-family:
    ui-monospace,       /* system monospace */
    'Cascadia Code',    /* Windows 11 */
    'Fira Code',        /* popular for coding */
    'Source Code Pro',
    Menlo,              /* macOS */
    Monaco,             /* macOS legacy */
    Consolas,           /* Windows */
    'Courier New',
    monospace;
}

/* Serif */
.prose {
  font-family:
    'Georgia',
    'Times New Roman',
    Times,
    serif;
}
```

---

## Step 4: Fluid Type Scale with clamp()

```css
:root {
  /* Fluid typography scale — scales from 320px to 1440px viewport */
  --text-xs:   clamp(0.69rem, 0.66rem + 0.14vw, 0.75rem);
  --text-sm:   clamp(0.83rem, 0.80rem + 0.14vw, 0.875rem);
  --text-base: clamp(0.875rem, 0.85rem + 0.14vw, 1rem);
  --text-lg:   clamp(1.05rem,  1.01rem + 0.20vw, 1.125rem);
  --text-xl:   clamp(1.26rem,  1.20rem + 0.30vw, 1.25rem);
  --text-2xl:  clamp(1.51rem,  1.41rem + 0.50vw, 1.5rem);
  --text-3xl:  clamp(1.81rem,  1.63rem + 0.93vw, 1.875rem);
  --text-4xl:  clamp(2.17rem,  1.87rem + 1.52vw, 2.25rem);
  --text-5xl:  clamp(2.49rem,  2.11rem + 1.90vw, 3rem);
  --text-6xl:  clamp(2.99rem,  2.40rem + 2.96vw, 3.75rem);
}

/* Apply scale */
body   { font-size: var(--text-base); }
p      { font-size: var(--text-base); line-height: 1.6; }
small  { font-size: var(--text-sm); }
h6     { font-size: var(--text-lg); }
h5     { font-size: var(--text-xl); }
h4     { font-size: var(--text-2xl); }
h3     { font-size: var(--text-3xl); }
h2     { font-size: var(--text-4xl); }
h1     { font-size: var(--text-5xl); }
.hero  { font-size: var(--text-6xl); }
```

---

## Step 5: text-wrap and Line Control

```css
/* text-wrap: balance — distribute text evenly across lines */
h1, h2, h3, blockquote {
  text-wrap: balance;
  /* Prevents awkward single-word last lines in headings */
  /* Only works for up to ~10 lines (performance limit) */
}

/* text-wrap: pretty — better last-line orphan prevention */
p {
  text-wrap: pretty; /* similar to balance but for long paragraphs */
}

/* Multi-line truncation with -webkit-line-clamp */
.card__description {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;  /* show max 3 lines */
  overflow: hidden;
}

/* Single-line truncation */
.card__title {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* Hyphenation for justified text */
.article-body {
  hyphens: auto;
  text-align: justify;
  -webkit-hyphens: auto;
  hyphenate-limit-chars: 6 3 3; /* min-chars before after limit */
}

/* Prevent hyphenation for some words */
.no-hyphen { hyphens: none; }

/* line-height: use unitless values */
body      { line-height: 1.6; }   /* body text */
headings  { line-height: 1.2; }   /* tight for large text */
.compact  { line-height: 1.0; }   /* very tight */
```

---

## Step 6: font-optical-sizing

```css
/* Optical sizing: adjust letterforms for display vs text sizes */
/* Most variable fonts support this via 'opsz' axis */

h1 {
  font-size: 3rem;
  font-optical-sizing: auto; /* default — browser adjusts for size */
}

.small-caption {
  font-size: 0.75rem;
  font-optical-sizing: auto; /* uses tighter, more legible forms */
}

/* Manual override (rare) */
.override {
  font-optical-sizing: none;
  font-variation-settings: 'opsz' 14; /* explicit */
}
```

---

## Step 7: Letter Spacing & Advanced Features

```css
/* letter-spacing: use em for relative scaling */
.heading {
  letter-spacing: -0.02em; /* tight for large headings */
}
.uppercase-label {
  text-transform: uppercase;
  letter-spacing: 0.1em;   /* wider for all-caps */
  font-size: 0.75rem;
}

/* OpenType features via font-feature-settings */
.prose {
  font-feature-settings:
    "liga" 1,   /* ligatures */
    "kern" 1,   /* kerning */
    "onum" 1;   /* oldstyle numerals */
}

/* Prefer font-variant shorthand */
.prose {
  font-variant-ligatures: common-ligatures;
  font-variant-numeric: oldstyle-nums;
  font-variant-caps: small-caps;
}

/* Kerning */
body { font-kerning: auto; }
```

---

## Step 8: Capstone — Type Scale Generator

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

| Property | Values | Purpose |
|----------|--------|---------|
| `font-variation-settings` | `'wght' 800` | Variable font axes |
| `font-display` | `swap`, `optional` | Loading behavior |
| `system-ui` | Font keyword | Native system font |
| `clamp()` | `min, preferred, max` | Fluid sizing |
| `text-wrap: balance` | — | Even line distribution |
| `-webkit-line-clamp` | integer | Multi-line truncation |
| `font-optical-sizing` | `auto`, `none` | Size-appropriate letterforms |
| `hyphens: auto` | — | Automatic hyphenation |
| `font-kerning` | `auto`, `normal` | Letter pair spacing |
| `font-variant-numeric` | `oldstyle-nums` | OpenType numerals |
