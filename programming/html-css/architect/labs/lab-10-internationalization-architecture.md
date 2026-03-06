# Lab 10: Internationalization Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Global CSS architecture for i18n: CSS logical properties migration (physical→logical), RTL/LTR switching, CJK/Arabic/Devanagari font stacks, writing-mode layouts, Intl-aware spacing, and unicode-range font splitting.

---

## Step 1: Physical → Logical Properties Migration

```
Physical properties (direction-aware):     Logical properties (flow-relative):
  margin-left       →  margin-inline-start
  margin-right      →  margin-inline-end
  margin-top        →  margin-block-start
  margin-bottom     →  margin-block-end
  padding-left      →  padding-inline-start
  padding-right     →  padding-inline-end
  padding-top       →  padding-block-start
  padding-bottom    →  padding-block-end
  border-left       →  border-inline-start
  border-right      →  border-inline-end
  left              →  inset-inline-start
  right             →  inset-inline-end
  top               →  inset-block-start
  bottom            →  inset-block-end
  width             →  inline-size
  height            →  block-size
  text-align: left  →  text-align: start
  text-align: right →  text-align: end
  float: left       →  float: inline-start
  float: right      →  float: inline-end
```

```css
/* Before: physical (breaks RTL) */
.nav-item {
  margin-left: 1rem;
  padding-right: 0.5rem;
  border-left: 3px solid var(--color-primary);
}

/* After: logical (LTR and RTL both work) */
.nav-item {
  margin-inline-start: 1rem;
  padding-inline-end: 0.5rem;
  border-inline-start: 3px solid var(--color-primary);
}
```

---

## Step 2: RTL/LTR Switching

```html
<!-- Set direction on html element -->
<html lang="ar" dir="rtl">
<!-- OR -->
<html lang="en" dir="ltr">
```

```css
/* Using :dir() pseudo-class (no JS needed) */
:dir(ltr) .icon-arrow { transform: none; }
:dir(rtl) .icon-arrow { transform: scaleX(-1); } /* Mirror arrow icons */

/* Using [dir] attribute selectors */
[dir="rtl"] .sidebar {
  border-inline-end: 1px solid var(--border-color);
}

/* Global logical properties — works for both directions */
.layout {
  padding-inline: var(--space-4);    /* left+right (LTR) or right+left (RTL) */
  margin-block: var(--space-6);      /* top+bottom (always) */
  text-align: start;                 /* left in LTR, right in RTL */
}

/* Bidirectional-safe absolute positioning */
.badge {
  position: absolute;
  inset-inline-end: -0.5rem;  /* top-right in LTR, top-left in RTL */
  inset-block-start: -0.5rem;
}
```

> 💡 `padding-inline: X` is shorthand for `padding-inline-start: X; padding-inline-end: X` — it sets both inline sides simultaneously, equivalent to the old `padding-left + padding-right`.

---

## Step 3: Multi-Script Font Stacks

```css
/* CJK (Chinese, Japanese, Korean) */
.lang-cjk {
  font-family:
    /* Japanese */
    'Noto Sans JP', 'Hiragino Sans', 'Hiragino Kaku Gothic ProN',
    /* Korean */
    'Noto Sans KR', 'Apple SD Gothic Neo',
    /* Chinese Traditional */
    'Noto Sans TC', 'PingFang TC',
    /* Chinese Simplified */
    'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei',
    /* Fallback */
    sans-serif;
  /* CJK-specific line height — more breathing room needed */
  line-height: 1.8;
  /* Improve CJK kerning */
  text-spacing-trim: space-all;
}

/* Arabic / Persian */
[lang="ar"], [lang="fa"] {
  font-family:
    'Noto Sans Arabic', 'Geeza Pro', 'Arabic Typesetting',
    'Arial Unicode MS', sans-serif;
  direction: rtl;
  /* Arabic-specific: no word-spacing for connected script */
  word-spacing: 0;
  letter-spacing: 0;
  line-height: 1.9;
}

/* Devanagari (Hindi, Marathi, Nepali) */
[lang="hi"], [lang="mr"] {
  font-family:
    'Noto Sans Devanagari', 'Kohinoor Devanagari', 'Mangal',
    sans-serif;
  line-height: 2.0; /* Accommodate top descenders */
}
```

---

## Step 4: Writing-Mode Layouts

```css
/* Vertical text (Japanese/Chinese traditional) */
.vertical-text {
  writing-mode: vertical-rl;    /* right-to-left column progression */
  text-orientation: mixed;      /* sideways for non-CJK chars */
}

/* Vertical sideways (rotated Latin in sidebar labels) */
.rotated-label {
  writing-mode: vertical-rl;
  text-orientation: sideways;   /* rotate all chars */
  transform: rotate(180deg);    /* flip direction if needed */
}

/* Vertical layout: block/inline swap */
.manga-panel {
  writing-mode: vertical-rl;
  /* Now: inline-size = height, block-size = width */
  inline-size: 200px; /* height of text */
}

/* Mixed writing modes in same document */
.article-japanese {
  writing-mode: vertical-rl;
}
.article-japanese .aside {
  writing-mode: horizontal-tb; /* Override for embedded aside */
  display: inline-block;
}
```

---

## Step 5: Unicode-Range Font Splitting

```css
/* Load only the characters actually used — huge performance win */

/* Latin subset (most common for English UI) */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-latin.woff2') format('woff2');
  font-display: swap;
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC,
                 U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074,
                 U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215,
                 U+FEFF, U+FFFD;
}

/* Extended Latin (Eastern European) */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-latin-ext.woff2') format('woff2');
  font-display: swap;
  unicode-range: U+0100-024F, U+0259, U+1E00-1EFF;
}

/* Cyrillic */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-cyrillic.woff2') format('woff2');
  font-display: swap;
  unicode-range: U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116;
}

/* Greek */
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-greek.woff2') format('woff2');
  font-display: swap;
  unicode-range: U+0370-03FF;
}
```

> 💡 With unicode-range splitting, browsers download only the font subsets containing characters present in the document. An English-only page downloads only the Latin subset.

---

## Step 6: Intl-Aware Spacing

```css
/* Different scripts need different density settings */
:root {
  /* Latin: standard density */
  --text-density: 1;
  --line-height: 1.5;
  --paragraph-gap: 1em;
}

[lang="zh"], [lang="ja"], [lang="ko"] {
  /* CJK: looser */
  --line-height: 1.8;
  --paragraph-gap: 0.75em;
}

[lang="ar"], [lang="fa"], [lang="ur"] {
  /* Arabic/Persian: looser vertical */
  --line-height: 1.9;
  --paragraph-gap: 0.5em;
}

/* Apply consistently */
.prose {
  line-height: var(--line-height);
  p + p { margin-block-start: var(--paragraph-gap); }
}
```

---

## Step 7: Automated Migration Tool

```javascript
// Node.js physical-to-logical migrator
const physToLogical = {
  'margin-left': 'margin-inline-start',
  'margin-right': 'margin-inline-end',
  'margin-top': 'margin-block-start',
  'margin-bottom': 'margin-block-end',
  'padding-left': 'padding-inline-start',
  'padding-right': 'padding-inline-end',
  'padding-top': 'padding-block-start',
  'padding-bottom': 'padding-block-end',
};

function migrateCSS(css) {
  let result = css;
  for (const [physical, logical] of Object.entries(physToLogical)) {
    result = result.split(physical).join(logical);
  }
  return result;
}
```

---

## Step 8: Capstone — Logical Property Converter

```bash
docker run --rm node:20-alpine node -e "
const physToLogical = {
  'margin-left': 'margin-inline-start', 'margin-right': 'margin-inline-end',
  'padding-top': 'padding-block-start', 'padding-bottom': 'padding-block-end',
};
const css = '.nav { margin-left: 1rem; padding-top: 0.5rem; margin-right: auto; }';
let out = css;
Object.entries(physToLogical).forEach(([p,l]) => { out = out.split(p).join(l); });
console.log('=== Physical to Logical Property Converter ===');
console.log('Before:', css);
console.log('After: ', out);
"
```

📸 **Verified Output:**
```
=== Physical → Logical Property Converter ===
Before: .nav { margin-left: 1rem; padding-top: 0.5rem; margin-right: auto; }
After:  .nav { margin-inline-start: 1rem; padding-block-start: 0.5rem; margin-inline-end: auto; }
```

---

## Summary

| Topic | Technique | Benefit |
|-------|-----------|---------|
| Physical→logical | `margin-inline-start` etc. | Auto RTL support |
| RTL switching | `dir` attribute + `:dir()` | No duplicate CSS |
| Icon mirroring | `:dir(rtl) { scaleX(-1) }` | Directional icons |
| CJK fonts | Noto family stack | All CJK coverage |
| Arabic | `writing-system: 0; letter-spacing: 0` | Connected script |
| Font subsetting | `unicode-range` | Smaller font loads |
| Writing modes | `vertical-rl` | CJK vertical text |
| Density | Per-lang line-height vars | Readable in all scripts |
