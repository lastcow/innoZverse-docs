# Lab 02: Flexbox Deep Dive

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master the full Flexbox model: flex shorthand, alignment axes, ordering, wrapping, and real-world layout patterns including Holy Grail, sticky footer, and card grids.

---

## Step 1: The Flex Shorthand

`flex: <grow> <shrink> <basis>` — the three properties that control how flex items size themselves.

```css
/* Common patterns */
flex: 1;         /* flex: 1 1 0%    — grow, shrink, start from 0 */
flex: auto;      /* flex: 1 1 auto  — grow, shrink, use content size */
flex: none;      /* flex: 0 0 auto  — fixed, no grow/shrink */
flex: 0;         /* flex: 0 1 0%    — don't grow, can shrink */

/* Full explicit form */
.item {
  flex-grow:   1;     /* proportion of available space to take */
  flex-shrink: 0;     /* don't shrink below flex-basis */
  flex-basis:  200px; /* ideal size before flex adjustment */
}

/* Common layouts */
.sidebar { flex: 0 0 280px; }  /* fixed width sidebar */
.main    { flex: 1; }          /* main takes remaining space */
.icon    { flex: 0 0 1.5rem; } /* icon won't flex */
```

> 💡 `flex: 1` vs `flex: auto`: `flex: 1` starts distributing from 0 (ignores content size), `flex: auto` starts from content size. Use `flex: 1` for equal columns.

---

## Step 2: Alignment — Two Axes

```css
.container {
  display: flex;
  flex-direction: row; /* or column, row-reverse, column-reverse */
  
  /* Main axis (direction of flex-direction) */
  justify-content: flex-start | flex-end | center | space-between | space-around | space-evenly;
  
  /* Cross axis (perpendicular to flex-direction) */
  align-items: flex-start | flex-end | center | stretch | baseline;
  
  /* Cross axis — MULTI-LINE only (when flex-wrap is used) */
  align-content: flex-start | flex-end | center | space-between | stretch;
  
  flex-wrap: wrap; /* needed for align-content to have effect */
}

/* Per-item cross-axis override */
.item-special {
  align-self: flex-end; /* overrides align-items for this item */
}
```

**`align-items` vs `align-content`:**
- `align-items` — aligns items within their **current row/line**
- `align-content` — aligns the **lines themselves** within the container (only when `flex-wrap: wrap`)

---

## Step 3: Order & Flex-Wrap

```css
/* Order: default is 0, lower numbers come first */
.sidebar { order: -1; } /* move sidebar before main in DOM */
.footer  { order: 99; } /* always last */

/* flex-wrap patterns */
.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.card-grid .card {
  flex: 1 1 280px; /* grow/shrink, ideal width 280px */
  /* Creates responsive grid: wraps when cards can't fit */
}

/* wrap-reverse: fills from bottom */
.timeline {
  display: flex;
  flex-wrap: wrap-reverse;
}
```

---

## Step 4: Auto Margin Tricks

Auto margins in flex consume all available space on one side:

```css
/* Push last item to far end */
.nav {
  display: flex;
  align-items: center;
}
.nav .logo       { /* takes natural space */ }
.nav .nav-links  { margin-inline-start: auto; } /* pushes to right */

/* Center one item, push it away from siblings */
.toolbar {
  display: flex;
}
.toolbar .spacer { margin: auto; } /* equal margins on all sides */

/* Push footer to bottom */
.card {
  display: flex;
  flex-direction: column;
}
.card .card__body  { flex: 1; } /* grows to fill */
.card .card__footer { margin-block-start: auto; } /* or flex:1 on body */
```

---

## Step 5: Holy Grail Layout

Classic three-column layout with header and footer:

```html
<body class="holy-grail">
  <header class="holy-grail__header">Header</header>
  <div class="holy-grail__body">
    <nav class="holy-grail__nav">Nav</nav>
    <main class="holy-grail__main">Main Content</main>
    <aside class="holy-grail__aside">Sidebar</aside>
  </div>
  <footer class="holy-grail__footer">Footer</footer>
</body>
```

```css
.holy-grail {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.holy-grail__header,
.holy-grail__footer {
  flex: 0 0 auto; /* don't grow or shrink */
}

.holy-grail__body {
  display: flex;
  flex: 1; /* take remaining vertical space */
}

.holy-grail__nav,
.holy-grail__aside {
  flex: 0 0 200px; /* fixed-width sidebars */
}

.holy-grail__main {
  flex: 1; /* main takes remaining horizontal space */
  padding: 1rem;
}

/* Responsive: stack on mobile */
@media (max-width: 768px) {
  .holy-grail__body {
    flex-direction: column;
  }
  .holy-grail__nav,
  .holy-grail__aside {
    flex-basis: auto;
  }
}
```

---

## Step 6: Sticky Footer

```css
/* Method 1: Flexbox on body */
body {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin: 0;
}

main {
  flex: 1; /* pushes footer to bottom */
}

footer {
  /* naturally stays at bottom */
}
```

---

## Step 7: Responsive Card Grid

```html
<section class="card-grid">
  <article class="card">
    <img class="card__img" src="..." alt="...">
    <div class="card__body">
      <h2 class="card__title">Title</h2>
      <p class="card__text">Description...</p>
    </div>
    <footer class="card__footer">
      <button class="btn btn--primary">Read More</button>
    </footer>
  </article>
  <!-- more cards -->
</section>
```

```css
.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  padding: 1.5rem;
}

.card {
  display: flex;
  flex-direction: column;
  flex: 1 1 300px;       /* responsive minimum 300px */
  max-width: 400px;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.card__img {
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}

.card__body {
  flex: 1;              /* pushes footer to bottom */
  padding: 1rem;
}

.card__footer {
  padding: 1rem;
  border-top: 1px solid #eee;
  margin-block-start: auto;
}
```

---

## Step 8: Capstone — Validate with html-validate

```bash
docker run --rm node:20-alpine sh -c '
npm install -g html-validate 2>/dev/null | tail -1

cat > /tmp/flexbox-demo.html << "HTML"
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Flexbox Holy Grail</title>
  <style>
    body { display:flex; flex-direction:column; min-height:100vh; margin:0; }
    header, footer { flex:0 0 auto; padding:1rem; background:#333; color:white; }
    .body { display:flex; flex:1; }
    nav, aside { flex:0 0 200px; background:#f5f5f5; padding:1rem; }
    main { flex:1; padding:1rem; }
    .card-grid { display:flex; flex-wrap:wrap; gap:1rem; }
    .card { flex:1 1 250px; border:1px solid #ddd; border-radius:8px; padding:1rem; }
  </style>
</head>
<body>
  <header><h1>Holy Grail Layout</h1></header>
  <div class="body">
    <nav><p>Navigation</p></nav>
    <main>
      <section class="card-grid">
        <article class="card"><h2>Card 1</h2><p>Content</p></article>
        <article class="card"><h2>Card 2</h2><p>Content</p></article>
        <article class="card"><h2>Card 3</h2><p>Content</p></article>
      </section>
    </main>
    <aside><p>Sidebar</p></aside>
  </div>
  <footer><p>Footer</p></footer>
</body>
</html>
HTML

html-validate /tmp/flexbox-demo.html && echo "VALID HTML"
'
```

📸 **Verified Output:**
```
VALID HTML
```

---

## Summary

| Property | Values | Purpose |
|----------|--------|---------|
| `flex` | `<grow> <shrink> <basis>` | Shorthand for flex sizing |
| `flex: 1` | `1 1 0%` | Equal-width columns |
| `flex: none` | `0 0 auto` | Fixed size item |
| `justify-content` | `space-between` etc. | Main axis alignment |
| `align-items` | `center`, `stretch` | Cross axis (single line) |
| `align-content` | `space-between` etc. | Cross axis (multi-line) |
| `order` | integer | Reorder without changing DOM |
| `margin-inline-start: auto` | — | Push item to end |
| `flex-wrap: wrap` | — | Enable multi-line |
| `gap` | `<length>` | Space between items |
