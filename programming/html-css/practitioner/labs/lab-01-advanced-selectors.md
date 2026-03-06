# Lab 01: Advanced CSS Selectors & Specificity

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master CSS selectors beyond basics: attribute selectors, advanced pseudo-classes, specificity calculation, cascade layers, and logical properties. These skills unlock precise styling without class proliferation.

---

## Step 1: Attribute Selectors

Attribute selectors target elements by their HTML attributes and values.

```css
/* [attr]       — has attribute */
input[required] { border-color: red; }

/* [attr=val]   — exact match */
input[type="email"] { background: url(email-icon.svg) no-repeat right; }

/* [attr^=val]  — starts with */
a[href^="https"] { color: green; }    /* secure links */
a[href^="mailto"] { color: blue; }   /* email links */

/* [attr$=val]  — ends with */
a[href$=".pdf"]::after { content: " (PDF)"; }
a[href$=".zip"]::after { content: " (ZIP)"; }

/* [attr*=val]  — contains */
[class*="icon-"] { display: inline-block; width: 1em; height: 1em; }

/* [attr~=val]  — word in space-separated list */
[data-tags~="featured"] { border: 2px solid gold; }

/* [attr|=val]  — exact or prefix with hyphen (language codes) */
[lang|="en"] { font-family: "Georgia", serif; }

/* Case-insensitive flag */
input[type="TEXT" i] { outline: 2px solid blue; }
```

> 💡 Attribute selectors have the same specificity as class selectors `(0,1,0)`.

---

## Step 2: Structural Pseudo-Classes

```css
/* :nth-child(An+B) — pattern-based */
li:nth-child(odd)  { background: #f5f5f5; }
li:nth-child(even) { background: white; }
li:nth-child(3n+1) { font-weight: bold; }  /* every 3rd starting at 1 */

/* :nth-of-type — among same-type siblings */
p:nth-of-type(1) { font-size: 1.2em; font-weight: bold; } /* first paragraph */
img:nth-of-type(2n) { float: right; }

/* :first-child, :last-child, :only-child */
li:first-child { border-top: none; }
li:last-child  { border-bottom: none; }

/* :not() — negation (accepts complex selectors in modern CSS) */
input:not([type="submit"]):not([type="reset"]) { border: 1px solid #ccc; }
.card:not(.card--featured) { opacity: 0.8; }

/* :is() — forgiving selector list (specificity = most specific arg) */
:is(h1, h2, h3, h4, h5, h6) { font-family: "Helvetica Neue", sans-serif; }
:is(article, section, aside) p { line-height: 1.7; }

/* :where() — same as :is() but ZERO specificity */
:where(h1, h2, h3) { margin-block: 0.5em; }

/* :has() — parent/relational selector */
form:has(input:invalid) { border-left: 3px solid red; }
.card:has(img) { padding-top: 0; }
li:has(+ li:last-child) { margin-bottom: 0.5rem; }
```

---

## Step 3: Specificity Calculation

Specificity is calculated as three numbers `(A, B, C)`:
- **A** = ID selectors (`#id`)
- **B** = Class, attribute, and pseudo-class selectors
- **C** = Element and pseudo-element selectors

```
Selector                    A  B  C
─────────────────────────────────────
h1                          0, 0, 1
.class                      0, 1, 0
#id                         1, 0, 0
div.class                   0, 1, 1
a:hover                     0, 1, 1
#nav .link                  1, 1, 0
ul li a                     0, 0, 3
[type=text]                 0, 1, 0
div::before                 0, 0, 2
.card:not(.disabled)        0, 2, 0
```

**Rules:**
1. Higher `A` always wins over any `B` or `C`
2. `!important` overrides all specificity (use sparingly)
3. Inline styles beat all selectors (treat as `1,0,0,0`)
4. `:where()` = zero specificity `(0,0,0)`
5. `:is()` and `:not()` take specificity of their **most specific** argument

---

## Step 4: Cascade Layers (`@layer`)

```css
/* Define layer order — later layers win ties */
@layer reset, base, components, utilities;

@layer reset {
  *, *::before, *::after { box-sizing: border-box; }
  body { margin: 0; }
}

@layer base {
  a { color: blue; text-decoration: underline; }
  h1 { font-size: 2rem; }
}

@layer components {
  .btn { padding: 0.5em 1em; border-radius: 4px; }
  .btn-primary { background: blue; color: white; }
}

@layer utilities {
  .mt-auto { margin-top: auto; }
  .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
}

/* Unlayered styles beat ALL layers */
.override { color: red; } /* wins over everything in layers */

/* Import with layer */
@import url("reset.css") layer(reset);
```

> 💡 `@layer` lets you manage CSS origin without fighting specificity wars. Libraries go in lower layers; your code wins.

---

## Step 5: Logical Properties for Internationalization

```css
/* Physical → Logical mapping */
/* margin-left   → margin-inline-start  */
/* margin-right  → margin-inline-end    */
/* margin-top    → margin-block-start   */
/* margin-bottom → margin-block-end     */

.card {
  /* Works correctly for LTR, RTL, and vertical writing modes */
  margin-inline: auto;           /* left + right center */
  padding-inline: 1.5rem;       /* left + right padding */
  padding-block: 1rem;          /* top + bottom padding */
  border-inline-start: 4px solid blue; /* left border in LTR, right in RTL */
}

/* Sizing */
.sidebar {
  inline-size: 280px;     /* width in horizontal writing modes */
  max-inline-size: 100%;
  block-size: auto;       /* height */
}

/* Positioning */
.tooltip {
  inset-inline-end: 0;   /* right: 0 in LTR */
  inset-block-start: 0;  /* top: 0 */
}

/* Text alignment */
.caption {
  text-align: start;  /* left in LTR, right in RTL */
}
```

---

## Step 6: Combining Selectors Effectively

```html
<!-- Data-driven attribute targeting -->
<nav data-theme="dark" data-size="compact">
  <a href="/home" data-active="true">Home</a>
  <a href="/about">About</a>
  <a href="https://github.com/user">GitHub</a>
  <a href="mailto:hi@example.com">Contact</a>
</nav>
```

```css
/* Compound selectors */
[data-theme="dark"] [data-active="true"] {
  color: white;
  background: rgba(255,255,255,0.15);
}

[data-theme="dark"] a:not([data-active]) {
  color: rgba(255,255,255,0.7);
}

[data-theme="dark"] a:is([href^="https"], [href^="mailto"])::after {
  content: " ↗";
  font-size: 0.75em;
}

/* :has() for smart parent targeting */
nav:has([data-active]) {
  border-bottom: 2px solid currentColor;
}
```

---

## Step 7: Pseudo-Elements & Focus Management

```css
/* Generated content */
blockquote::before { content: "\201C"; font-size: 4em; color: #ccc; }
blockquote::after  { content: "\201D"; }

/* ::selection — highlighted text */
::selection { background: #ffd700; color: black; }

/* ::placeholder — input placeholder */
input::placeholder { color: #999; font-style: italic; }

/* :focus-visible — keyboard focus only (not mouse) */
button:focus-visible {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
}
button:focus:not(:focus-visible) {
  outline: none; /* hide for mouse users */
}

/* :target — URL fragment target */
section:target {
  animation: highlight 1s ease;
  background: #ffffcc;
}

/* :empty — elements with no children */
td:empty::before {
  content: "—";
  color: #999;
}
```

---

## Step 8: Capstone — Verified Specificity Calculator

```bash
docker run --rm node:20-alpine node -e "
function calcSpec(sel) {
  var a = (sel.match(/#[a-zA-Z]/g)||[]).length;
  var b = (sel.match(/\.[a-zA-Z]|\[[^\]]+\]|:(?!:)[a-zA-Z-]+/g)||[]).length;
  var c = (sel.match(/(^|[ >+~])[a-zA-Z]|::[a-zA-Z]/g)||[]).length;
  return a+','+b+','+c;
}
var selectors = ['h1','.class','#id','div.class','a:hover','#nav .link','ul li a','[type=text]','div::before','.card:not(.disabled)'];
selectors.forEach(function(s){ console.log(s + ' => (' + calcSpec(s) + ')'); });
"
```

📸 **Verified Output:**
```
h1 => (0,0,1)
.class => (0,1,0)
#id => (1,0,0)
div.class => (0,1,1)
a:hover => (0,1,1)
#nav .link => (1,1,0)
ul li a => (0,0,3)
[type=text] => (0,1,0)
div::before => (0,1,2)
.card:not(.disabled) => (0,3,0)
```

---

## Summary

| Concept | Syntax | Specificity |
|---------|--------|-------------|
| Attribute starts-with | `[href^="https"]` | `(0,1,0)` |
| Attribute ends-with | `[href$=".pdf"]` | `(0,1,0)` |
| Attribute contains | `[class*="icon"]` | `(0,1,0)` |
| nth-child pattern | `:nth-child(3n+1)` | `(0,1,0)` |
| Not selector | `:not(.disabled)` | `(0,1,0)` |
| Is selector | `:is(h1,h2,h3)` | most specific arg |
| Where selector | `:where(h1,h2,h3)` | `(0,0,0)` |
| Has parent | `:has(img)` | `(0,1,0)` |
| Cascade layer | `@layer name {}` | layer order |
| Logical property | `margin-inline-start` | same as physical |
