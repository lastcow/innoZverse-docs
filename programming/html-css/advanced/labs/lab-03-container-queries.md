# Lab 03: Container Queries

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master CSS Container Queries: `@container` inline-size queries, `container-type`, named containers, style container queries, nested containers, and real-world card components that reflow at container breakpoints.

---

## Step 1: Container Setup

```css
/* Mark an element as a container */

/* container-type: inline-size */
/* — enables @container queries on inline (width) axis */
/* — does NOT enable height queries */
.card-wrapper {
  container-type: inline-size;
}

/* container-type: size */
/* — enables both width AND height queries */
/* — rare: sizing must not depend on children */
.fixed-panel {
  container-type: size;
  width: 400px;
  height: 300px;
}

/* container-type: normal */
/* — enables style container queries only */
/* — default for all elements */
.style-container {
  container-type: normal;
}

/* Named containers (for targeting specific ancestors) */
.page-layout {
  container-type: inline-size;
  container-name: page;
}

/* Shorthand: container: name / type */
.sidebar {
  container: sidebar / inline-size;
}

.card-grid {
  container: card-grid / inline-size;
}
```

> 💡 `container-type: inline-size` makes the element a containment context. It also applies `contain: inline-size layout style` automatically.

---

## Step 2: Writing @container Queries

```css
/* Target the nearest container */
@container (min-width: 400px) {
  .card {
    flex-direction: row;
  }
}

/* Named container queries */
@container sidebar (max-width: 200px) {
  .nav-label {
    display: none;
  }
}

@container page (min-width: 1024px) {
  .article-grid {
    grid-template-columns: 1fr 1fr;
  }
}

/* Logical conditions */
@container (min-width: 400px) and (max-width: 800px) {
  .card { /* medium container */ }
}

@container (width >= 400px) {  /* modern range syntax */
  .card { /* cleaner range notation */ }
}

/* Container units: cqw, cqh, cqi, cqb, cqmin, cqmax */
.card__title {
  font-size: clamp(1rem, 4cqi, 1.5rem);
  /* cqi = 1% of container inline size */
}
```

---

## Step 3: Real-World Card Component

```html
<div class="card-container">
  <article class="card">
    <div class="card__media">
      <img class="card__image" src="article-thumb.jpg" alt="">
    </div>
    <div class="card__content">
      <div class="card__meta">
        <span class="card__category">Technology</span>
        <time class="card__date" datetime="2024-03-15">Mar 15, 2024</time>
      </div>
      <h2 class="card__title">Building Responsive Components</h2>
      <p class="card__excerpt">Container queries allow components to reflow based on their container size...</p>
      <div class="card__footer">
        <div class="card__author">
          <img class="card__avatar" src="author.jpg" alt="Jane Doe" width="32" height="32">
          <span>Jane Doe</span>
        </div>
        <a class="card__cta" href="#">Read More</a>
      </div>
    </div>
  </article>
</div>
```

```css
/* Container setup on the wrapper */
.card-container {
  container-type: inline-size;
  container-name: card;
}

/* Base styles: narrow/mobile card */
.card {
  display: flex;
  flex-direction: column;
  background: var(--color-surface, white);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--color-border, #e5e7eb);
}

.card__image {
  width: 100%;
  aspect-ratio: 16/9;
  object-fit: cover;
}

.card__content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.card__meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.card__title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  line-height: 1.3;
}

.card__excerpt { display: none; }

.card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
}

.card__avatar { border-radius: 50%; }
.card__author { display: flex; align-items: center; gap: 0.5rem; font-size: 0.875rem; }

/* Medium container: side-by-side layout */
@container card (min-width: 400px) {
  .card {
    flex-direction: row;
    align-items: stretch;
  }

  .card__image {
    width: 40%;
    aspect-ratio: auto;
    flex-shrink: 0;
  }

  .card__title { font-size: 1.125rem; }
  .card__excerpt { display: block; font-size: 0.875rem; color: #6b7280; }
}

/* Large container: magazine layout */
@container card (min-width: 600px) {
  .card__image {
    width: 45%;
  }

  .card__content { padding: 1.5rem; }
  .card__title { font-size: 1.375rem; }
  .card__excerpt { -webkit-line-clamp: 3; }

  .card__cta {
    background: var(--color-primary, #3b82f6);
    color: white;
    padding: 0.4em 1em;
    border-radius: 4px;
    text-decoration: none;
    font-size: 0.875rem;
    font-weight: 600;
  }
}
```

---

## Step 4: Nested Containers

```css
/* Parent container */
.page-layout {
  container: layout / inline-size;
}

/* Child is also a container */
.sidebar {
  container: sidebar / inline-size;
}

.main {
  container: main-content / inline-size;
}

/* Each @container queries its nearest named or unnamed ancestor */

/* Queries the sidebar container */
@container sidebar (max-width: 150px) {
  .nav-item span { display: none; }  /* icon-only nav */
}

/* Queries the page layout container */
@container layout (max-width: 768px) {
  .page {
    flex-direction: column;
  }
}

/* Queries the main-content container */
@container main-content (min-width: 800px) {
  .post-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```

---

## Step 5: Style Container Queries

Query CSS custom property values:

```css
/* Set up style container */
.card-wrapper {
  container-type: normal; /* or inline-size */
  --variant: default;     /* custom property as state */
}

.card-wrapper.featured {
  --variant: featured;
}

/* Query the style */
@container style(--variant: featured) {
  .card {
    border-color: gold;
    background: linear-gradient(135deg, #fffbeb, #fef3c7);
  }
  .card__title { color: #92400e; }
}

@container style(--variant: compact) {
  .card { padding: 0.5rem; }
  .card__excerpt { display: none; }
  .card__meta { display: none; }
}
```

---

## Step 6: Container Queries vs Media Queries

```
Feature         | Media Query      | Container Query
────────────────────────────────────────────────────────
Responds to     | Viewport size    | Container size
Use case        | Page-level layout| Component-level
Reusability     | Context-specific | Context-agnostic
Sidebar widget  | Can't adapt      | Adapts correctly
Grid columns    | Viewport-based   | Container-based
Font size       | vw units         | cqi/cqw units
Support         | Universal        | 90%+ (2024)
```

```css
/* Media queries: global page breakpoints */
@media (min-width: 1024px) {
  .page-layout {
    grid-template-columns: 280px 1fr;
  }
}

/* Container queries: component-level adaptation */
@container (min-width: 300px) {
  .widget {
    flex-direction: row;
  }
}
/* Works whether widget is in sidebar OR main content */
```

---

## Step 7: Practical Pattern — Dashboard Widgets

```html
<div class="widget-grid">
  <div class="widget-container wide">
    <div class="widget">...</div>
  </div>
  <div class="widget-container narrow">
    <div class="widget">...</div>
  </div>
</div>
```

```css
.widget-container {
  container: widget / inline-size;
}

.widget-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1rem;
}

/* Widget adapts to its container, not the viewport */
.widget { display: flex; flex-direction: column; }

@container widget (min-width: 400px) {
  .widget {
    flex-direction: row;
    align-items: center;
  }
  .widget__chart { flex: 1; }
  .widget__stats { width: 200px; }
}

@container widget (min-width: 600px) {
  .widget__stats { display: grid; grid-template-columns: repeat(2, 1fr); }
}
```

---

## Step 8: Capstone — Container Query Parser + Breakpoint Calculator

```bash
docker run --rm -v /tmp/container_query.js:/test.js node:20-alpine node /test.js
```

*(Create the test file:)*
```bash
cat > /tmp/container_query.js << 'EOF'
var containerQueries = [
  {name:"card",condition:"inline-size > 400px",changes:"flex-direction: row"},
  {name:"card",condition:"inline-size > 600px",changes:"display: grid; grid-template-columns: 1fr 2fr"},
  {name:"sidebar",condition:"inline-size < 200px",changes:"display: none"},
  {name:"nav",condition:"inline-size >= 768px",changes:"flex-direction: row; gap: 2rem"},
];
console.log("Container Query Analysis:");
console.log("=".repeat(50));
containerQueries.forEach(function(q,i){
  console.log("\n[" + (i+1) + "] Container: " + q.name);
  console.log("    Condition: @container (" + q.condition + ")");
  console.log("    Effect: " + q.changes);
});
console.log("\n\nExtracted Breakpoints:");
console.log("-".repeat(30));
containerQueries.forEach(function(q){
  var match = q.condition.match(/(\d+)px/);
  if(match){
    var px = parseInt(match[1]);
    var rem = (px/16).toFixed(2);
    console.log(q.name + " @ " + px + "px (" + rem + "rem)");
  }
});
EOF
docker run --rm -v /tmp/container_query.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
Container Query Analysis:
==================================================

[1] Container: card
    Condition: @container (inline-size > 400px)
    Effect: flex-direction: row

[2] Container: card
    Condition: @container (inline-size > 600px)
    Effect: display: grid; grid-template-columns: 1fr 2fr

[3] Container: sidebar
    Condition: @container (inline-size < 200px)
    Effect: display: none

[4] Container: nav
    Condition: @container (inline-size >= 768px)
    Effect: flex-direction: row; gap: 2rem


Extracted Breakpoints:
------------------------------
card @ 400px (25.00rem)
card @ 600px (37.50rem)
sidebar @ 200px (12.50rem)
nav @ 768px (48.00rem)
```

---

## Summary

| Feature | Syntax | Purpose |
|---------|--------|---------|
| Inline container | `container-type: inline-size` | Width-based queries |
| Size container | `container-type: size` | Width + height queries |
| Named container | `container: name / type` | Target specific ancestor |
| Width query | `@container (min-width: 400px)` | Breakpoint |
| Range syntax | `@container (width >= 400px)` | Modern syntax |
| Container unit | `font-size: 4cqi` | % of container inline |
| Style query | `@container style(--variant: x)` | Value-based theming |
| Nested | Container inside container | Component isolation |
