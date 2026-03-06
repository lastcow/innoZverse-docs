# Lab 13: Internationalization (i18n)

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build globally-ready HTML/CSS: `dir` attribute for RTL/LTR, vertical writing modes, CSS logical properties, `:lang()` pseudo-class, international font stacks, `Intl.DateTimeFormat`, and `unicode-bidi`.

---

## Step 1: Direction — dir Attribute

```html
<!-- HTML-level direction -->
<html lang="en" dir="ltr">  <!-- Latin languages: left to right -->
<html lang="ar" dir="rtl">  <!-- Arabic: right to left -->
<html lang="he" dir="rtl">  <!-- Hebrew: right to left -->

<!-- Per-element direction -->
<p dir="auto">
  <!-- auto: browser detects based on first strong directional character -->
  This could be any language
</p>

<!-- Bidirectional content: RTL within LTR page -->
<p>
  User wrote:
  <bdi>مرحبا بالعالم</bdi>  <!-- isolated bidirectional content -->
</p>

<!-- Override direction -->
<span dir="ltr">user@email.com</span>  <!-- keep email LTR in RTL context -->
<span dir="rtl">⬅ Back</span>

<!-- Form inputs in RTL document -->
<input type="text" dir="auto" lang="ar">
<input type="email" dir="ltr">  <!-- emails always LTR -->
```

---

## Step 2: CSS Logical Properties — Full Reference

```css
/* The key principle: use logical properties instead of physical */
/* Logical adapts to writing mode + text direction automatically */

/* ====== SPACING ====== */
/* Physical → Logical */
.element {
  /* Margins */
  margin-top:    → margin-block-start: 1rem;
  margin-bottom: → margin-block-end:   1rem;
  margin-left:   → margin-inline-start: 1rem;
  margin-right:  → margin-inline-end:   1rem;
  
  /* Shorthand */
  margin-block:  1rem;      /* block-start + block-end */
  margin-inline: 2rem;      /* inline-start + inline-end */
  margin-inline: 1rem 2rem; /* start end */
  
  /* Padding (same pattern) */
  padding-block:  1rem;
  padding-inline: 1.5rem;
}

/* ====== SIZING ====== */
.element {
  inline-size: 300px;      /* width in LTR/RTL, height in vertical */
  block-size: auto;        /* height in LTR/RTL, width in vertical */
  min-inline-size: 200px;
  max-inline-size: 100%;
  min-block-size: 100px;
}

/* ====== POSITIONING ====== */
.element {
  position: absolute;
  inset-inline-start: 0;  /* left in LTR, right in RTL */
  inset-inline-end: auto;
  inset-block-start: 0;   /* top */
  inset-block-end: auto;  /* bottom */
  inset: 0;               /* all four sides */
  inset: 10px 20px;       /* block inline */
}

/* ====== BORDERS ====== */
.element {
  border-inline-start: 4px solid blue;
  border-block-end: 1px solid #e5e7eb;
  border-inline: 1px solid; /* both inline borders */
  border-block:  1px solid; /* both block borders */
}

/* ====== BORDER RADIUS ====== */
.element {
  border-start-start-radius: 8px;  /* top-left in LTR */
  border-start-end-radius:   8px;  /* top-right in LTR */
  border-end-start-radius:   0;    /* bottom-left in LTR */
  border-end-end-radius:     0;    /* bottom-right in LTR */
}

/* ====== TEXT ====== */
.element {
  text-align: start;  /* left in LTR, right in RTL */
  text-align: end;    /* right in LTR, left in RTL */
}

/* ====== FLOAT ====== */
.element {
  float: inline-start;  /* left in LTR, right in RTL */
  float: inline-end;
}
```

---

## Step 3: RTL Layout Example

```css
/* Before: physical properties (needs [dir=rtl] overrides) */
.nav {
  padding-left: 1rem;
  border-right: 4px solid blue;
  text-align: left;
  float: left;
}

[dir="rtl"] .nav {
  padding-left: 0;
  padding-right: 1rem;  /* duplicate everything */
  border-right: none;
  border-left: 4px solid blue;
  text-align: right;
  float: right;
}

/* After: logical properties (RTL works automatically!) */
.nav {
  padding-inline-start: 1rem;
  border-inline-end: 4px solid blue;
  text-align: start;
  float: inline-start;
}
/* NO [dir=rtl] overrides needed! */
```

---

## Step 4: Vertical Writing Modes

```css
/* writing-mode: controls text flow direction */
.english     { writing-mode: horizontal-tb; } /* default: L→R, T→B */
.japanese    { writing-mode: vertical-rl; }    /* T→B, R→L (columns) */
.mongolian   { writing-mode: vertical-lr; }    /* T→B, L→R */

/* Practical: vertical sidebar labels */
.tab-label {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg); /* flip for upward reading */
}

/* Decorative headings */
.page-section::before {
  content: "SECTION";
  writing-mode: vertical-lr;
  font-size: 0.75rem;
  letter-spacing: 0.2em;
  color: #999;
}

/* text-orientation: with vertical writing */
.vertical-cjk {
  writing-mode: vertical-rl;
  text-orientation: mixed;      /* default: rotate Latin, upright CJK */
}
.vertical-upright {
  writing-mode: vertical-rl;
  text-orientation: upright;    /* all characters upright */
}
.vertical-sideways {
  writing-mode: vertical-rl;
  text-orientation: sideways;   /* all characters rotated 90deg */
}

/* In vertical writing mode: inline/block swap! */
/* width becomes the block axis (like height normally is) */
/* height becomes the inline axis (like width normally is) */
.vertical-card {
  writing-mode: vertical-rl;
  inline-size: 200px;  /* controls the height (block) in vertical mode */
  block-size: 100px;   /* controls the width (inline) in vertical mode */
}
```

---

## Step 5: :lang() Pseudo-Class

```css
/* Style based on language */
:lang(ar), :lang(he), :lang(fa) {
  /* RTL languages */
  font-family: 'Noto Sans Arabic', 'Segoe UI', sans-serif;
  font-size: 1.1em;    /* Arabic text often needs slightly larger size */
  line-height: 1.8;    /* Arabic script needs more line height */
}

:lang(zh), :lang(ja), :lang(ko) {
  /* CJK (Chinese, Japanese, Korean) */
  font-family: 'Noto Sans CJK', 'PingFang SC', 'Hiragino Sans', sans-serif;
  word-break: break-all; /* CJK characters can break anywhere */
  overflow-wrap: break-word;
}

:lang(hi), :lang(bn), :lang(pa) {
  /* Devanagari script */
  font-family: 'Noto Sans Devanagari', 'Mangal', sans-serif;
  line-height: 2;  /* Devanagari needs extra line height for matras */
}

/* Quotes per language */
:lang(en) q { quotes: '"' '"' "'" "'"; }
:lang(fr) q { quotes: '«' '»' '‹' '›'; }
:lang(de) q { quotes: '„' '"' '‚' '''; }
:lang(ja) q { quotes: '「' '」' '『' '』'; }
:lang(zh) q { quotes: '「' '」' '『' '』'; }
```

---

## Step 6: International Font Stacks

```css
/* Universal system font stack (all scripts) */
body {
  font-family:
    /* Latin extended */
    'Inter', 'Segoe UI', system-ui,
    /* Arabic */
    'Noto Sans Arabic', 'Arabic UI Text',
    /* Hebrew */
    'Noto Sans Hebrew', 'Arial Hebrew',
    /* CJK Simplified */
    'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei',
    /* CJK Traditional */
    'Noto Sans TC', 'Apple LiGothic',
    /* Japanese */
    'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Yu Gothic',
    /* Korean */
    'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic',
    /* Devanagari */
    'Noto Sans Devanagari',
    /* Fallback */
    sans-serif;
}

/* Per-language font targeting */
[lang="ar"] body { font-family: 'Noto Naskh Arabic', 'Arabic Typesetting', serif; }
[lang="zh-CN"] body { font-family: 'Noto Sans SC', 'PingFang SC', sans-serif; }
[lang="ja"] body { font-family: 'Noto Sans JP', 'Hiragino Sans', sans-serif; }
```

---

## Step 7: Intl.DateTimeFormat & unicode-bidi

```javascript
// Intl.DateTimeFormat — locale-aware date formatting
const dates = {
  en: new Intl.DateTimeFormat('en-US', {
    year: 'numeric', month: 'long', day: 'numeric'
  }).format(new Date('2024-03-15')),
  // "March 15, 2024"

  ar: new Intl.DateTimeFormat('ar-SA', {
    year: 'numeric', month: 'long', day: 'numeric',
    calendar: 'islamic'
  }).format(new Date('2024-03-15')),
  // "٤ رمضان ١٤٤٥ هـ"

  ja: new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric', month: 'long', day: 'numeric'
  }).format(new Date('2024-03-15')),
  // "2024年3月15日"

  zh: new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: 'short', day: 'numeric'
  }).format(new Date('2024-03-15')),
  // "2024年3月15日"
};

// Intl.NumberFormat
const currency = new Intl.NumberFormat('ar-SA', {
  style: 'currency', currency: 'SAR'
}).format(1234.56);
// "١٬٢٣٤٫٥٦ ر.س."

// Intl.RelativeTimeFormat
const rtf = new Intl.RelativeTimeFormat('fr', { style: 'long' });
rtf.format(-3, 'day');  // "il y a 3 jours"
```

```css
/* unicode-bidi: controls bidirectional algorithm */
.embed {
  unicode-bidi: embed;      /* creates embedded bidi context */
}
.override-rtl {
  unicode-bidi: bidi-override;  /* force override of direction */
  direction: rtl;
}
.isolated {
  unicode-bidi: isolate;    /* same as <bdi> — preferred */
}
.isolate-override {
  unicode-bidi: isolate-override;
}
.plaintext {
  unicode-bidi: plaintext;  /* use first-strong heuristics */
}
```

---

## Step 8: Capstone — RTL/LTR Logical Property Converter

```bash
docker run --rm -v /tmp/rtl_converter.js:/test.js node:20-alpine node /test.js
```

*(Create the file:)*
```bash
cat > /tmp/rtl_converter.js << 'EOF'
var physicalToLogical = {
  "margin-left":   "margin-inline-start",
  "margin-right":  "margin-inline-end",
  "margin-top":    "margin-block-start",
  "margin-bottom": "margin-block-end",
  "padding-left":  "padding-inline-start",
  "padding-right": "padding-inline-end",
  "padding-top":   "padding-block-start",
  "padding-bottom":"padding-block-end",
  "border-left":   "border-inline-start",
  "border-right":  "border-inline-end",
  "left":          "inset-inline-start",
  "right":         "inset-inline-end",
  "width":         "inline-size",
  "height":        "block-size",
  "text-align: left":  "text-align: start",
  "text-align: right": "text-align: end",
};
console.log("Physical Property → Logical Property (CSS Internationalization)");
console.log("=".repeat(60));
Object.entries(physicalToLogical).forEach(function(e){
  console.log(e[0].padEnd(20) + " → " + e[1]);
});
console.log("\nFor RTL layouts (dir=\"rtl\" or dir=\"auto\"):");
console.log("margin-inline-start auto-flips to right margin");
console.log("padding-inline-end  auto-flips to left padding");
console.log("No need for separate [dir=rtl] overrides!");
EOF
docker run --rm -v /tmp/rtl_converter.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
Physical Property → Logical Property (CSS Internationalization)
============================================================
margin-left          → margin-inline-start
margin-right         → margin-inline-end
margin-top           → margin-block-start
margin-bottom        → margin-block-end
padding-left         → padding-inline-start
padding-right        → padding-inline-end
padding-top          → padding-block-start
padding-bottom       → padding-block-end
border-left          → border-inline-start
border-right         → border-inline-end
left                 → inset-inline-start
right                → inset-inline-end
width                → inline-size
height               → block-size
text-align: left     → text-align: start
text-align: right    → text-align: end

For RTL layouts (dir="rtl" or dir="auto"):
margin-inline-start auto-flips to right margin
padding-inline-end  auto-flips to left padding
No need for separate [dir=rtl] overrides!
```

---

## Summary

| Feature | Implementation | Languages |
|---------|---------------|-----------|
| `dir="rtl"` | HTML attribute | Arabic, Hebrew, Farsi |
| `dir="auto"` | Auto-detect | Mixed content |
| `margin-inline-start` | Logical property | All |
| `padding-block` | Block-axis padding | All |
| `writing-mode: vertical-rl` | Vertical text | CJK |
| `text-orientation: upright` | Character orientation | CJK |
| `:lang(ar)` | Language-specific CSS | Any |
| `Intl.DateTimeFormat` | Locale-aware dates | All |
| `unicode-bidi: isolate` | Bidi isolation (`<bdi>`) | Mixed RTL/LTR |
| `quotes` property | Language-appropriate | FR, DE, JA... |
