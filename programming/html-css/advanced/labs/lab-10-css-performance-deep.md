# Lab 10: CSS Performance Deep Dive

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master CSS performance engineering: `contain`, `content-visibility`, `@layer` for cascade management, selector performance, `will-change` budgeting, and CSS logical properties.

---

## Step 1: CSS Contain

`contain` isolates an element from the rest of the page, enabling browser optimizations:

```css
/* Individual contain values */
.widget {
  contain: layout;  /* layout changes don't affect outside */
  contain: paint;   /* painting is clipped to the element's bounds */
  contain: size;    /* element's size doesn't depend on its children */
  contain: style;   /* counters and quotes don't escape this element */
}

/* Shorthand values */
.card {
  contain: content; /* = layout + paint (most useful combo) */
}

.fixed-size-widget {
  contain: strict;  /* = layout + paint + size (most aggressive) */
  width: 300px;
  height: 200px; /* must set explicit size with 'strict' */
}

/* inline-size containment (for container queries) */
.container {
  container-type: inline-size; /* auto-applies contain: inline-size layout style */
}

/* When to use contain */
.sidebar-widget { contain: content; }
/* — Each widget's reflows won't ripple to the page */

.ad-unit { contain: strict; }
/* — Ads can't affect page layout */

.code-editor { contain: layout paint; }
/* — Complex inner renders won't cause page reflow */
```

> 💡 `contain: content` is the most practical value. It isolates layout and paint without requiring a fixed size.

---

## Step 2: content-visibility

```css
/* Skip rendering off-screen content entirely */
.article-section {
  content-visibility: auto;
  
  /* Estimate height to prevent scroll jump when rendering is skipped */
  contain-intrinsic-size: auto 500px;
  /* auto: browser learns actual height after first render */
  /* 500px: initial estimated height */
}

/* More specific intrinsic size */
.card {
  content-visibility: auto;
  contain-intrinsic-size: auto 200px; /* width: auto, height: 200px */
  /* Or: contain-intrinsic-size: 300px 200px; (width height) */
}

/* content-visibility: hidden — like display:none but preserves render state */
.offscreen-panel {
  content-visibility: hidden; /* not rendered, not accessible */
  /* Fast to show: just change to 'visible', state is preserved */
}

/* Transition content-visibility on/off */
.panel {
  content-visibility: hidden;
  transition: content-visibility 0.3s allow-discrete;
}
.panel.open {
  content-visibility: visible;
}

/* Impact: Google Chrome team reported 7x rendering speedup
   on a page with 1000s of off-screen articles */
```

---

## Step 3: @layer for Cascade Management

```css
/* Define layer order (earlier = lower priority) */
@layer reset, base, objects, components, utilities, overrides;

/* Unlayered styles ALWAYS win over layered styles */

@layer reset {
  *, *::before, *::after { box-sizing: border-box; }
  body { margin: 0; }
}

@layer base {
  /* Reasonable defaults — lower priority than components */
  a { color: blue; }
  h1 { font-size: 2rem; }
}

@layer components {
  /* UI components */
  .btn { padding: 0.5em 1em; }
  .card { border-radius: 8px; }
}

@layer utilities {
  /* Utility overrides */
  .mt-0 { margin-top: 0; }
  .sr-only { 
    position: absolute;
    width: 1px; height: 1px;
    overflow: hidden; clip: rect(0,0,0,0);
  }
}

/* Import library into specific layer (it can't escape!) */
@import url("bootstrap.css") layer(vendor.bootstrap);
@import url("normalize.css") layer(reset);

/* Layer grouping */
@layer vendor {
  @layer bootstrap { /* vendor.bootstrap */ }
  @layer animate   { /* vendor.animate  */ }
}

/* Override library without specificity fights */
@layer components {
  .btn { background: var(--color-primary); } /* beats any bootstrap style */
}
```

---

## Step 4: Selector Performance

```css
/* Selector evaluation: right to left (key selector matters most) */

/* ❌ Slow: universal selector on key */
div > * { color: red; }      /* engine checks every element */
* + * { margin-top: 1rem; }  /* VERY expensive */

/* ❌ Slow: deep descendant with universal */
#nav > ul > li > a { }
.sidebar * { }

/* ✓ Fast: class selector is key */
.nav__link { }       /* fast: one class lookup */
.nav .nav__link { }  /* ok: still .nav__link is key */

/* ❌ Avoid over-qualifying */
div.card { }     /* unnecessary element prefix */
ul.list { }

/* ✓ Use class, keep flat */
.card { }
.list { }

/* Expensive pseudo-selectors (use sparingly in hot paths) */
:has(img)        /* expensive: parent lookup */
:nth-child(...)  /* acceptable */
:not(...)        /* acceptable with class/type args */

/* ✓ Animation performance: stick to compositor props */
/* GPU composited: transform, opacity, filter, will-change */
/* Layout-triggering: width, height, top, left, margin, padding */

/* Measure: DevTools > Performance > Recalculate Style */
```

---

## Step 5: will-change Budget

```css
/* will-change: tells browser to prepare a layer in advance */

/* ✓ Good uses */
.card:hover { transform: translateY(-4px); }
.card { will-change: transform; } /* prepare layer before hover */

.modal { will-change: opacity, transform; }

/* ✓ Add/remove via JS for brief animations */
element.addEventListener('mouseenter', () => {
  element.style.willChange = 'transform';
});
element.addEventListener('animationend', () => {
  element.style.willChange = 'auto'; /* release the layer */
});

/* ❌ Don't overuse — each will-change costs memory */
/* ❌ Never: will-change: all */
/* ❌ Not on everything: body * { will-change: transform; } */

/* Memory cost estimation */
/* 1280×720 layer at 4 bytes/pixel = ~3.5MB per layer */
/* 10 will-change elements = potentially 35MB+ extra GPU memory */

/* ✓ Budget: max 5-10 will-change elements on screen */
```

---

## Step 6: CSS Logical Properties

```css
/* Physical → Logical mapping */
/* Automatically adapts to: LTR/RTL text, vertical writing modes */

/* Margins */
margin-top:    → margin-block-start
margin-bottom: → margin-block-end
margin-left:   → margin-inline-start
margin-right:  → margin-inline-end

/* Shorthand logical margins */
.element {
  margin-block:  1rem;       /* top + bottom */
  margin-inline: auto;       /* left + right */
  padding-block: 0.5rem 1rem; /* top bottom */
  padding-inline: 1rem;
}

/* Sizing */
width:     → inline-size
height:    → block-size
min-width: → min-inline-size
max-width: → max-inline-size

/* Positioning */
left:  → inset-inline-start
right: → inset-inline-end
top:   → inset-block-start
bottom:→ inset-block-end
inset: 0;  /* shorthand: all four sides */

/* Borders */
border-left:  → border-inline-start
border-right: → border-inline-end
border-top:   → border-block-start
border-bottom:→ border-block-end
border-inline: 1px solid; /* both inline sides */
border-block:  1px solid; /* both block sides */

/* Border radius */
border-top-left-radius:     → border-start-start-radius
border-top-right-radius:    → border-start-end-radius
border-bottom-left-radius:  → border-end-start-radius
border-bottom-right-radius: → border-end-end-radius

/* Text */
text-align: left  → text-align: start
text-align: right → text-align: end

/* Full example: before/after */
/* Before (physical): */
.sidebar {
  width: 280px;
  margin-left: 0;
  padding-left: 1rem;
  border-right: 1px solid #e5e7eb;
  text-align: left;
}

/* After (logical): */
.sidebar {
  inline-size: 280px;
  margin-inline-start: 0;
  padding-inline-start: 1rem;
  border-inline-end: 1px solid #e5e7eb;
  text-align: start;
}
/* Now works perfectly in both LTR and RTL! */
```

---

## Step 7: CSS Layer Import Strategy

```css
/* Recommended @layer ordering for real projects */
@layer
  /* External */
  vendor.normalize,      /* CSS reset */
  vendor.animations,     /* animation library */
  
  /* Internal */
  settings,     /* CSS variables/tokens */
  generic,      /* low-level element styles */
  objects,      /* layout patterns */
  components,   /* UI components */
  utilities,    /* single-purpose overrides */
  
  /* Emergency escape */
  overrides;    /* for legitimate exceptions */

/* Import vendors into layers */
@import "normalize.css"    layer(vendor.normalize);
@import "animate.min.css"  layer(vendor.animations);

/* Your own CSS in specific layers */
@layer settings {
  :root { --color-primary: #3b82f6; }
}

@layer components {
  .btn { /* never fights with vendor styles */ }
}
```

---

## Step 8: Capstone — Contain Property Analyzer

```bash
docker run --rm -v /tmp/css_contain.js:/test.js node:20-alpine node /test.js
```

*(Create the file:)*
```bash
cat > /tmp/css_contain.js << 'EOF'
var containValues = [
  {value:"none",desc:"No containment",score:0},
  {value:"layout",desc:"Layout is isolated from rest of page",score:30},
  {value:"paint",desc:"Paint is clipped, no overflow",score:35},
  {value:"size",desc:"Size does not depend on children",score:20},
  {value:"style",desc:"Counter/quote scope limited",score:10},
  {value:"content",desc:"layout + paint (most common)",score:65},
  {value:"strict",desc:"layout + paint + size (maximum)",score:85},
  {value:"inline-size",desc:"Inline size does not depend on children",score:15},
];
console.log("CSS contain Performance Analysis");
console.log("=".repeat(55));
containValues.forEach(function(c){
  var bar = "#".repeat(Math.floor(c.score/5));
  console.log("contain: " + c.value.padEnd(15) + " [" + bar.padEnd(17) + "] " + c.score + "%");
  console.log("  " + c.desc);
});
console.log("\ncontent-visibility: auto;");
console.log("  + contain-intrinsic-size: 0 500px;");
console.log("  => Skip rendering off-screen elements");
console.log("  => Up to 7x rendering performance boost (Google Chrome data)");
EOF
docker run --rm -v /tmp/css_contain.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
CSS contain Performance Analysis
=======================================================
contain: none            [                 ] 0%
  No containment
contain: layout          [######           ] 30%
  Layout is isolated from rest of page
contain: paint           [#######          ] 35%
  Paint is clipped, no overflow
...
contain: content         [#############    ] 65%
  layout + paint (most common)
contain: strict          [#################] 85%
  layout + paint + size (maximum)

content-visibility: auto;
  + contain-intrinsic-size: 0 500px;
  => Skip rendering off-screen elements
  => Up to 7x rendering performance boost (Google Chrome data)
```

---

## Summary

| Feature | Value | Performance Impact |
|---------|-------|-------------------|
| `contain: content` | layout + paint | Isolate component reflows |
| `contain: strict` | layout+paint+size | Maximum isolation |
| `content-visibility: auto` | — | Skip off-screen rendering |
| `contain-intrinsic-size` | `auto 500px` | Prevent scroll jump |
| `@layer` | Layer order | Zero-specificity cascade control |
| Avoid `*` selector | — | Reduce selector matching |
| `will-change: transform` | — | GPU layer promotion |
| Logical properties | `margin-inline` | i18n + performance |
| Class selectors | `.class {}` | Fastest selector type |
| Avoid `!important` | — | Use `@layer` instead |
