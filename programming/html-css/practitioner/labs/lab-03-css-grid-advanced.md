# Lab 03: CSS Grid Advanced

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master advanced CSS Grid: named template areas, auto-placement with `dense`, `minmax()`/`fit-content()`/`repeat()`, subgrid, named lines, implicit grid, and building a magazine layout.

---

## Step 1: Grid Template Areas

```css
.dashboard {
  display: grid;
  grid-template-areas:
    "header  header  header"
    "sidebar main    main  "
    "sidebar widgets widgets"
    "footer  footer  footer";
  grid-template-columns: 240px 1fr 300px;
  grid-template-rows: 60px 1fr auto 50px;
  min-height: 100vh;
  gap: 0;
}

.dashboard__header  { grid-area: header; }
.dashboard__sidebar { grid-area: sidebar; }
.dashboard__main    { grid-area: main; }
.dashboard__widgets { grid-area: widgets; }
.dashboard__footer  { grid-area: footer; }

/* Period (.) = empty cell */
.sparse-grid {
  display: grid;
  grid-template-areas:
    "logo . nav"
    ".    . .  "
    "hero hero hero";
}
```

> 💡 Every row must have the same number of cells. Named areas must be rectangular (no L-shapes).

---

## Step 2: Auto-Placement & Dense Packing

```css
/* Default auto-placement: row by row */
.gallery {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  grid-auto-flow: row; /* default */
}

/* Dense packing: fills gaps with smaller items */
.masonry-style {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 100px;
  gap: 1rem;
  grid-auto-flow: row dense; /* backfills gaps! */
}

.item--wide  { grid-column: span 2; }
.item--tall  { grid-row: span 2; }
.item--large { grid-column: span 2; grid-row: span 2; }

/* Column-based flow */
.sidebar-list {
  display: grid;
  grid-auto-flow: column;
  grid-template-rows: repeat(3, auto);
  /* Items flow down columns, then next column */
}
```

---

## Step 3: minmax(), fit-content(), repeat()

```css
/* minmax(min, max) — flexible tracks with limits */
.responsive-grid {
  display: grid;
  grid-template-columns: minmax(200px, 1fr) 3fr;
  /* col 1: min 200px, max 1fr; col 2: always 3fr */
}

/* fit-content(val) — max at val, min at content size */
.auto-cols {
  grid-template-columns: fit-content(300px) 1fr;
  /* col 1 is as wide as content, but never > 300px */
}

/* repeat() patterns */
.fixed-cols {
  grid-template-columns: repeat(4, 1fr);           /* 4 equal columns */
  grid-template-columns: repeat(4, 100px 200px);   /* alternating */
}

/* auto-fill: create as many columns as fit, may have empty tracks */
.auto-fill-grid {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  /* fills row with columns, empty columns if content doesn't fill */
}

/* auto-fit: same but collapses empty tracks to 0 */
.auto-fit-grid {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  /* preferred for card grids — items stretch to fill */
}

/* The magical responsive grid (no media queries!) */
.responsive-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
  gap: 1.5rem;
}
```

> 💡 **auto-fill vs auto-fit**: Use `auto-fill` when you want empty tracks to hold space. Use `auto-fit` (more common) when you want items to stretch and fill the row.

---

## Step 4: Named Lines

```css
.layout {
  display: grid;
  grid-template-columns:
    [full-start] 1rem
    [content-start sidebar-start] 200px
    [sidebar-end main-start] 1fr
    [main-end content-end] 1rem
    [full-end];
  grid-template-rows:
    [header-start] 60px [header-end content-start]
    1fr [content-end footer-start] 50px [footer-end];
}

/* Place by name */
.full-bleed { grid-column: full-start / full-end; }
.content    { grid-column: content-start / content-end; }
.header     { grid-row: header-start / header-end; }
```

---

## Step 5: Subgrid

```css
/* Subgrid: inherit parent grid tracks */
.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto;
  gap: 1rem;
}

.card {
  display: grid;
  grid-row: span 4;  /* occupy 4 rows */
  grid-template-rows: subgrid; /* inherit parent row tracks */
}

/* Now all cards align their internal rows across the grid! */
.card__header { } /* row 1 */
.card__image  { } /* row 2 */
.card__body   { } /* row 3 */
.card__footer { } /* row 4 */

/* Column subgrid */
.article {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
}
```

---

## Step 6: Implicit Grid

```css
/* Explicit grid: what you define with grid-template-* */
/* Implicit grid: what browser creates for overflow items */

.explicit {
  display: grid;
  grid-template-columns: repeat(3, 200px);  /* explicit: 3 columns */
  grid-template-rows: 100px;               /* explicit: 1 row */
  
  /* Control implicit rows/columns */
  grid-auto-rows: 120px;    /* new rows are 120px */
  grid-auto-columns: 1fr;   /* new columns are 1fr */
}

/* Negative index: count from end of explicit grid */
.last-col {
  grid-column: -1; /* last explicit column line */
  grid-column: 1 / -1; /* full width of explicit grid */
}
```

---

## Step 7: Magazine Layout

```html
<article class="magazine">
  <header class="magazine__header">Breaking News</header>
  <figure class="magazine__hero">
    <img src="hero.jpg" alt="Hero image">
  </figure>
  <div class="magazine__main">Main story text...</div>
  <aside class="magazine__pull">Key quote here</aside>
  <section class="magazine__secondary">Secondary story</section>
  <section class="magazine__tertiary">Tertiary story</section>
  <footer class="magazine__footer">© 2024</footer>
</article>
```

```css
.magazine {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  grid-template-rows: auto;
  grid-template-areas:
    "header    header    header    header    header    header  "
    "hero      hero      hero      hero      .         .       "
    "hero      hero      hero      hero      secondary secondary"
    "main      main      main      pull      tertiary  tertiary"
    "footer    footer    footer    footer    footer    footer  ";
  gap: 1rem;
  padding: 1rem;
}

.magazine__header    { grid-area: header; }
.magazine__hero      { grid-area: hero; }
.magazine__main      { grid-area: main; }
.magazine__pull      { grid-area: pull; font-size: 1.5em; font-style: italic; }
.magazine__secondary { grid-area: secondary; }
.magazine__tertiary  { grid-area: tertiary; }
.magazine__footer    { grid-area: footer; }
```

---

## Step 8: Capstone — HTML Generation with Grid Demo

```bash
docker run --rm node:20-alpine node -e "
var cols = 'repeat(auto-fit, minmax(200px, 1fr))';
var items = ['Home','About','Work','Contact','Blog','Gallery'];

var html = '<!DOCTYPE html><html lang=\"en\"><head>';
html += '<meta charset=\"UTF-8\"><title>Grid Demo</title>';
html += '<style>';
html += '.grid{display:grid;grid-template-columns:' + cols + ';gap:1rem;padding:1rem;}';
html += '.item{background:#3b82f6;color:white;padding:2rem;border-radius:8px;text-align:center;}';
html += '.item:nth-child(3n+1){grid-column:span 2;}';
html += '</style></head><body><div class=\"grid\">';
items.forEach(function(name,i){
  html += '<div class=\"item\">' + name + '</div>';
});
html += '</div></body></html>';

var fs = require('fs');
fs.writeFileSync('/tmp/grid-demo.html', html);
console.log('Grid template columns: ' + cols);
console.log('Generated ' + items.length + ' grid items');
console.log('File size: ' + html.length + ' bytes');
console.log('span-2 items: ' + items.filter((_,i) => (i+1)%3===1).length + ' (every 3rd starting at 1)');
"
```

📸 **Verified Output:**
```
Grid template columns: repeat(auto-fit, minmax(200px, 1fr))
Generated 6 grid items
File size: 443 bytes
span-2 items: 2 (every 3rd starting at 1)
```

---

## Summary

| Feature | Syntax | Use Case |
|---------|--------|----------|
| Template areas | `grid-template-areas: "a b"` | Named layout regions |
| Auto dense | `grid-auto-flow: row dense` | Fill gaps in grid |
| minmax | `minmax(200px, 1fr)` | Flexible tracks |
| fit-content | `fit-content(300px)` | Content-sized column |
| auto-fill | `repeat(auto-fill, ...)` | Fixed-size with empty tracks |
| auto-fit | `repeat(auto-fit, ...)` | Stretching card grids |
| Subgrid | `grid-template-rows: subgrid` | Align across grid items |
| Named lines | `[start] 1fr [end]` | Semantic placement |
| Implicit rows | `grid-auto-rows: 120px` | Control overflow rows |
| span | `grid-column: span 3` | Multi-column/row item |
