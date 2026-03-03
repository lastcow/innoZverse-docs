# Lab 8: CSS Grid Layout

## Objective
Master CSS Grid to build two-dimensional layouts — controlling both rows and columns simultaneously for complex page structures.

## Background
CSS Grid is the most powerful layout system in CSS. Unlike Flexbox (one dimension), Grid works in two dimensions simultaneously. It excels at page-level layout, dashboards, image galleries, and magazine-style designs. Grid and Flexbox are complementary — use Grid for 2D layouts, Flexbox for 1D alignment.

## Time
35 minutes

## Prerequisites
- Lab 07: CSS Flexbox Layout

## Tools
```bash
docker run --rm -it -v /tmp:/workspace zchencow/innozverse-htmlcss:latest bash
```

---

## Lab Instructions

### Step 1: Grid Container Basics

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Grid Basics</title>
  <style>
    .grid {
      display: grid;
      grid-template-columns: 200px 1fr 2fr;
      grid-template-rows: 100px 150px;
      gap: 10px;
      padding: 20px;
      background: #f0f0f0;
    }
    .cell {
      background: #3498db;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      border-radius: 6px;
    }
  </style>
</head>
<body>
  <h2>CSS Grid: 3 columns (200px, 1fr, 2fr), 2 rows</h2>
  <div class="grid">
    <div class="cell">1</div>
    <div class="cell">2</div>
    <div class="cell">3</div>
    <div class="cell">4</div>
    <div class="cell">5</div>
    <div class="cell">6</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/grid-step1.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Grid Basics</title>
  <style>
    .grid { display: grid; grid-template-columns: 200px 1fr 2fr; grid-template-rows: 100px 150px; gap: 10px; padding: 20px; background: #f0f0f0; }
    .cell { background: #3498db; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; border-radius: 6px; }
  </style>
</head>
<body>
  <div class="grid">
    <div class="cell">1</div><div class="cell">2</div><div class="cell">3</div>
    <div class="cell">4</div><div class="cell">5</div><div class="cell">6</div>
  </div>
</body>
</html>
EOF
```

> 💡 **`fr` units** (fractional) are Grid's superpower. `1fr 2fr` means the second column is twice as wide as the first. `grid-template-columns: 200px 1fr 2fr` creates a fixed sidebar + flexible content area. The `fr` unit distributes remaining space after fixed sizes.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/grid-step1.html', 'utf8');
console.log(html.includes('display: grid') || html.includes('display:grid') ? '✓ Grid container found' : '✗ Missing');
console.log(html.includes('grid-template-columns') ? '✓ grid-template-columns found' : '✗ Missing');
"
✓ Grid container found
✓ grid-template-columns found
```

---

### Step 2: Grid Placement — Column & Row Spanning

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Grid Placement</title>
  <style>
    .grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      grid-template-rows: repeat(3, 100px);
      gap: 10px;
      padding: 20px;
    }
    .cell { background: #9b59b6; color: white; display: flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: bold; }
    .span-2-cols { grid-column: 1 / 3; background: #e74c3c; }
    .span-2-rows { grid-row: 2 / 4; grid-column: 4; background: #27ae60; }
    .big-cell { grid-column: 2 / 4; grid-row: 2 / 4; background: #2980b9; }
  </style>
</head>
<body>
  <h2>Grid Placement: grid-column & grid-row spanning</h2>
  <div class="grid">
    <div class="cell span-2-cols">Span 2 cols (1/3)</div>
    <div class="cell">C</div>
    <div class="cell">D</div>
    <div class="cell">E</div>
    <div class="cell big-cell">Big (cols 2-4, rows 2-4)</div>
    <div class="cell span-2-rows">Tall (col 4, rows 2-4)</div>
    <div class="cell">F</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/grid-step2.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Grid Placement</title>
  <style>
    .grid { display: grid; grid-template-columns: repeat(4, 1fr); grid-template-rows: repeat(3, 100px); gap: 10px; padding: 20px; }
    .cell { background: #9b59b6; color: white; display: flex; align-items: center; justify-content: center; border-radius: 6px; font-weight: bold; }
    .span-2-cols { grid-column: 1 / 3; background: #e74c3c; }
    .span-2-rows { grid-row: 2 / 4; grid-column: 4; background: #27ae60; }
    .big-cell { grid-column: 2 / 4; grid-row: 2 / 4; background: #2980b9; }
  </style>
</head>
<body>
  <div class="grid">
    <div class="cell span-2-cols">Span 2 cols</div>
    <div class="cell">C</div>
    <div class="cell">D</div>
    <div class="cell">E</div>
    <div class="cell big-cell">Big cell</div>
    <div class="cell span-2-rows">Tall</div>
    <div class="cell">F</div>
  </div>
</body>
</html>
EOF
```

> 💡 **Grid lines** are numbered from 1. `grid-column: 1 / 3` means "start at line 1, end at line 3" — spanning 2 columns. `grid-column: 1 / -1` spans the full width. You can also use `span`: `grid-column: span 2` means "take 2 columns from wherever I am."

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/grid-step2.html', 'utf8');
console.log(html.includes('grid-column') ? '✓ grid-column found' : '✗ Missing');
console.log(html.includes('grid-row') ? '✓ grid-row found' : '✗ Missing');
"
✓ grid-column found
✓ grid-row found
```

---

### Step 3: Named Template Areas

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Grid Template Areas</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      display: grid;
      grid-template-areas:
        "header header header"
        "sidebar main aside"
        "footer footer footer";
      grid-template-columns: 200px 1fr 160px;
      grid-template-rows: 60px 1fr 50px;
      min-height: 100vh;
      gap: 8px;
      font-family: sans-serif;
    }
    header  { grid-area: header;  background: #2c3e50; color: white; display: flex; align-items: center; padding: 0 20px; }
    .sidebar{ grid-area: sidebar; background: #ecf0f1; padding: 20px; }
    main    { grid-area: main;    background: white;   padding: 20px; }
    aside   { grid-area: aside;   background: #ffeaa7; padding: 20px; }
    footer  { grid-area: footer;  background: #2c3e50; color: white; display: flex; align-items: center; justify-content: center; }
  </style>
</head>
<body>
  <header><strong>Named Grid Areas</strong></header>
  <div class="sidebar"><h3>Sidebar</h3><p>Navigation here</p></div>
  <main><h1>Main Content</h1><p>This layout uses named template areas — the most readable CSS layout syntax ever invented.</p></main>
  <aside><h3>Aside</h3><p>Widgets</p></aside>
  <footer>Footer — grid-area makes layout self-documenting</footer>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/grid-step3.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Grid Template Areas</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { display: grid; grid-template-areas: "header header header" "sidebar main aside" "footer footer footer"; grid-template-columns: 200px 1fr 160px; grid-template-rows: 60px 1fr 50px; min-height: 100vh; gap: 8px; font-family: sans-serif; }
    header { grid-area: header; background: #2c3e50; color: white; display: flex; align-items: center; padding: 0 20px; }
    .sidebar { grid-area: sidebar; background: #ecf0f1; padding: 20px; }
    main { grid-area: main; background: white; padding: 20px; }
    aside { grid-area: aside; background: #ffeaa7; padding: 20px; }
    footer { grid-area: footer; background: #2c3e50; color: white; display: flex; align-items: center; justify-content: center; }
  </style>
</head>
<body>
  <header>Named Grid Areas</header>
  <div class="sidebar"><h3>Sidebar</h3></div>
  <main><h1>Main Content</h1><p>Named template areas make layout readable.</p></main>
  <aside><h3>Aside</h3></aside>
  <footer>Footer</footer>
</body>
</html>
EOF
```

> 💡 **`grid-template-areas`** is like a visual map of your layout in CSS. Each quoted string is a row, each word is a cell. A `.` creates an empty cell. This ASCII-art approach makes layouts self-documenting — you can literally see the page structure in the CSS.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/grid-step3.html', 'utf8');
console.log(html.includes('grid-template-areas') ? '✓ grid-template-areas found' : '✗ Missing');
console.log(html.includes('grid-area') ? '✓ grid-area found' : '✗ Missing');
"
✓ grid-template-areas found
✓ grid-area found
```

---

### Step 4: auto-fill, auto-fit & minmax()

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>auto-fill and minmax</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    h3 { margin: 20px 0 10px; }
    .auto-fill {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
      gap: 10px;
      margin-bottom: 30px;
    }
    .auto-fit {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 10px;
    }
    .cell {
      background: #6c5ce7;
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <h3>auto-fill: keeps empty columns</h3>
  <div class="auto-fill">
    <div class="cell">A</div>
    <div class="cell">B</div>
    <div class="cell">C</div>
  </div>
  <h3>auto-fit: stretches items to fill (more common)</h3>
  <div class="auto-fit">
    <div class="cell">A</div>
    <div class="cell">B</div>
    <div class="cell">C</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/grid-step4.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>auto-fill and minmax</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    .auto-fit { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
    .cell { background: #6c5ce7; color: white; padding: 20px; border-radius: 8px; text-align: center; font-weight: bold; }
  </style>
</head>
<body>
  <div class="auto-fit">
    <div class="cell">A</div>
    <div class="cell">B</div>
    <div class="cell">C</div>
  </div>
</body>
</html>
EOF
```

> 💡 **`repeat(auto-fit, minmax(150px, 1fr))`** is the most powerful one-liner in CSS. It creates as many columns as fit, each at least 150px wide, stretching to fill. This replaces complex media query breakpoints. `auto-fill` creates empty columns; `auto-fit` collapses them — prefer `auto-fit`.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/grid-step4.html', 'utf8');
console.log(html.includes('auto-fit') ? '✓ auto-fit found' : '✗ Missing');
console.log(html.includes('minmax') ? '✓ minmax found' : '✗ Missing');
"
✓ auto-fit found
✓ minmax found
```

---

### Step 5: Responsive Grid Without Media Queries

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Grid</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; padding: 20px; background: #f8f9fa; }
    .product-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 20px;
    }
    .product-card {
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .product-img {
      height: 180px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 3rem;
    }
    .product-info { padding: 16px; }
    .product-info h3 { margin-bottom: 8px; }
    .product-info p { color: #666; font-size: 0.9rem; margin-bottom: 12px; }
    .price { font-weight: bold; color: #e17055; font-size: 1.1rem; }
  </style>
</head>
<body>
  <h2>Responsive Product Grid — No Media Queries!</h2>
  <div class="product-grid">
    <div class="product-card">
      <div class="product-img" style="background:#ffeaa7">📱</div>
      <div class="product-info"><h3>Smartphone</h3><p>Latest model with 5G</p><div class="price">$799</div></div>
    </div>
    <div class="product-card">
      <div class="product-img" style="background:#dfe6e9">💻</div>
      <div class="product-info"><h3>Laptop</h3><p>Ultra-thin, 14-hour battery</p><div class="price">$1,299</div></div>
    </div>
    <div class="product-card">
      <div class="product-img" style="background:#fd79a8">🎧</div>
      <div class="product-info"><h3>Headphones</h3><p>Noise canceling, Hi-Fi</p><div class="price">$199</div></div>
    </div>
    <div class="product-card">
      <div class="product-img" style="background:#a29bfe">⌚</div>
      <div class="product-info"><h3>Smartwatch</h3><p>Health tracking, 7-day battery</p><div class="price">$299</div></div>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/grid-step5.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Grid</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; padding: 20px; }
    .product-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; }
    .product-card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
    .product-img { height: 180px; display: flex; align-items: center; justify-content: center; font-size: 3rem; }
    .product-info { padding: 16px; }
    .price { font-weight: bold; color: #e17055; }
  </style>
</head>
<body>
  <div class="product-grid">
    <div class="product-card"><div class="product-img" style="background:#ffeaa7">📱</div><div class="product-info"><h3>Smartphone</h3><div class="price">$799</div></div></div>
    <div class="product-card"><div class="product-img" style="background:#dfe6e9">💻</div><div class="product-info"><h3>Laptop</h3><div class="price">$1,299</div></div></div>
    <div class="product-card"><div class="product-img" style="background:#fd79a8">🎧</div><div class="product-info"><h3>Headphones</h3><div class="price">$199</div></div></div>
    <div class="product-card"><div class="product-img" style="background:#a29bfe">⌚</div><div class="product-info"><h3>Smartwatch</h3><div class="price">$299</div></div></div>
  </div>
</body>
</html>
EOF
```

> 💡 **Intrinsic responsiveness** — no media queries needed! The grid automatically creates columns as space allows. On mobile: 1 column. On tablet: 2-3 columns. On desktop: 4 columns. All from one line of CSS. This is modern CSS at its most powerful.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/grid-step5.html', 'utf8');
console.log(html.includes('auto-fit') && html.includes('minmax') ? '✓ Responsive grid pattern found' : '✗ Missing');
"
✓ Responsive grid pattern found
```

---

### Step 6: Magazine Layout with Grid

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Magazine Layout</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Georgia', serif; padding: 20px; background: #fff; }
    .magazine {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr;
      grid-template-rows: auto auto auto;
      gap: 20px;
      max-width: 900px;
      margin: 0 auto;
    }
    .article { background: #f8f9fa; border-radius: 8px; overflow: hidden; }
    .article-img { height: 200px; display: flex; align-items: center; justify-content: center; font-size: 3rem; }
    .article-body { padding: 16px; }
    .article-body h2 { font-size: 1.1rem; margin-bottom: 8px; }
    .article-body p { font-size: 0.85rem; color: #555; line-height: 1.5; }
    .featured {
      grid-column: 1 / 2;
      grid-row: 1 / 3;
    }
    .featured .article-img { height: 280px; font-size: 5rem; }
    .featured .article-body h2 { font-size: 1.4rem; }
    .wide { grid-column: 1 / -1; }
  </style>
</head>
<body>
  <h1 style="margin-bottom:20px">📰 Tech Weekly</h1>
  <div class="magazine">
    <div class="article featured">
      <div class="article-img" style="background:#74b9ff">🚀</div>
      <div class="article-body">
        <h2>Featured: The Future of Web Development</h2>
        <p>CSS Grid and modern layout techniques are transforming how we build websites. This featured article spans two rows while smaller stories sit beside it.</p>
      </div>
    </div>
    <div class="article">
      <div class="article-img" style="background:#a29bfe;height:120px">🤖</div>
      <div class="article-body"><h2>AI in Web Design</h2><p>How AI is changing the creative process.</p></div>
    </div>
    <div class="article">
      <div class="article-img" style="background:#55efc4;height:120px">🔐</div>
      <div class="article-body"><h2>Web Security 2024</h2><p>New threats and how to protect your apps.</p></div>
    </div>
    <div class="article">
      <div class="article-img" style="background:#fdcb6e;height:120px">📱</div>
      <div class="article-body"><h2>Mobile-First Design</h2><p>Why mobile-first is non-negotiable.</p></div>
    </div>
    <div class="article">
      <div class="article-img" style="background:#fd79a8;height:120px">🎨</div>
      <div class="article-body"><h2>Design Systems</h2><p>Building consistent UI at scale.</p></div>
    </div>
    <div class="article wide">
      <div class="article-body" style="padding:20px"><h2>Newsletter: Full Width Story Spanning All Columns</h2><p>Grid makes it trivial to break out of the column pattern for special content.</p></div>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/grid-step6.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Magazine Layout</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Georgia, serif; padding: 20px; }
    .magazine { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 20px; max-width: 900px; margin: 0 auto; }
    .article { background: #f8f9fa; border-radius: 8px; overflow: hidden; }
    .article-img { height: 150px; display: flex; align-items: center; justify-content: center; font-size: 3rem; }
    .article-body { padding: 16px; }
    .featured { grid-column: 1 / 2; grid-row: 1 / 3; }
    .wide { grid-column: 1 / -1; }
  </style>
</head>
<body>
  <div class="magazine">
    <div class="article featured"><div class="article-img" style="background:#74b9ff;height:250px">🚀</div><div class="article-body"><h2>Featured Story</h2><p>Spans 2 rows.</p></div></div>
    <div class="article"><div class="article-img" style="background:#a29bfe;height:100px">🤖</div><div class="article-body"><h2>AI</h2></div></div>
    <div class="article"><div class="article-img" style="background:#55efc4;height:100px">🔐</div><div class="article-body"><h2>Security</h2></div></div>
    <div class="article"><div class="article-img" style="background:#fdcb6e;height:100px">📱</div><div class="article-body"><h2>Mobile</h2></div></div>
    <div class="article"><div class="article-img" style="background:#fd79a8;height:100px">🎨</div><div class="article-body"><h2>Design</h2></div></div>
    <div class="article wide"><div class="article-body" style="padding:20px"><h2>Full Width Story</h2></div></div>
  </div>
</body>
</html>
EOF
```

> 💡 **Magazine-style layouts** used to require JavaScript masonry libraries. With Grid's explicit placement, you can span items across rows and columns directly in CSS. `grid-column: 1 / -1` is especially handy — `-1` always refers to the last line.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/grid-step6.html', 'utf8');
console.log(html.includes('grid-row') ? '✓ grid-row spanning found' : '✗ Missing');
console.log(html.includes('1 / -1') ? '✓ full-width span found' : '✗ Missing full span');
"
✓ grid-row spanning found
✓ full-width span found
```

---

### Step 7: Dashboard Grid Layout

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Dashboard Grid</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }
    .dashboard {
      display: grid;
      grid-template-areas:
        "sidebar header header"
        "sidebar stats stats"
        "sidebar chart activity";
      grid-template-columns: 220px 1fr 300px;
      grid-template-rows: 60px 120px 1fr;
      min-height: 100vh;
      gap: 12px;
      padding: 12px;
    }
    .sidebar { grid-area: sidebar; background: #16213e; border-radius: 12px; padding: 20px; }
    .header  { grid-area: header;  background: #16213e; border-radius: 12px; padding: 0 20px; display: flex; align-items: center; justify-content: space-between; }
    .stats   { grid-area: stats;   display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .stat    { background: #16213e; border-radius: 12px; padding: 20px; text-align: center; }
    .stat-value { font-size: 1.8rem; font-weight: bold; color: #e94560; }
    .chart   { grid-area: chart;    background: #16213e; border-radius: 12px; padding: 20px; }
    .activity{ grid-area: activity; background: #16213e; border-radius: 12px; padding: 20px; }
    .nav-item { padding: 10px; margin: 4px 0; border-radius: 6px; cursor: pointer; }
    .nav-item:hover { background: #0f3460; }
    .nav-item.active { background: #e94560; }
  </style>
</head>
<body>
  <div class="dashboard">
    <div class="sidebar">
      <h2 style="margin-bottom:20px;color:#e94560">📊 Dash</h2>
      <div class="nav-item active">🏠 Overview</div>
      <div class="nav-item">📈 Analytics</div>
      <div class="nav-item">👥 Users</div>
      <div class="nav-item">⚙️ Settings</div>
    </div>
    <div class="header">
      <h1 style="font-size:1.2rem">Dashboard Overview</h1>
      <span>Welcome back, Admin!</span>
    </div>
    <div class="stats">
      <div class="stat"><div class="stat-value">24.5K</div><div>Users</div></div>
      <div class="stat"><div class="stat-value">$128K</div><div>Revenue</div></div>
      <div class="stat"><div class="stat-value">8.3%</div><div>Growth</div></div>
      <div class="stat"><div class="stat-value">1,247</div><div>Orders</div></div>
    </div>
    <div class="chart"><h3>📈 Revenue Chart</h3><p style="margin-top:10px;color:#888">Chart placeholder — integrate Chart.js here</p></div>
    <div class="activity"><h3>🔔 Activity</h3><p style="margin-top:10px;color:#888">Recent events list</p></div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/grid-step7.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Dashboard Grid</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }
    .dashboard { display: grid; grid-template-areas: "sidebar header header" "sidebar stats stats" "sidebar chart activity"; grid-template-columns: 220px 1fr 300px; grid-template-rows: 60px 120px 1fr; min-height: 100vh; gap: 12px; padding: 12px; }
    .sidebar { grid-area: sidebar; background: #16213e; border-radius: 12px; padding: 20px; }
    .header { grid-area: header; background: #16213e; border-radius: 12px; padding: 0 20px; display: flex; align-items: center; }
    .stats { grid-area: stats; display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .stat { background: #16213e; border-radius: 12px; padding: 20px; text-align: center; }
    .stat-value { font-size: 1.8rem; font-weight: bold; color: #e94560; }
    .chart { grid-area: chart; background: #16213e; border-radius: 12px; padding: 20px; }
    .activity { grid-area: activity; background: #16213e; border-radius: 12px; padding: 20px; }
  </style>
</head>
<body>
  <div class="dashboard">
    <div class="sidebar"><h2 style="color:#e94560">📊 Dash</h2></div>
    <div class="header"><h1>Dashboard</h1></div>
    <div class="stats">
      <div class="stat"><div class="stat-value">24.5K</div><div>Users</div></div>
      <div class="stat"><div class="stat-value">$128K</div><div>Revenue</div></div>
      <div class="stat"><div class="stat-value">8.3%</div><div>Growth</div></div>
      <div class="stat"><div class="stat-value">1,247</div><div>Orders</div></div>
    </div>
    <div class="chart"><h3>Revenue Chart</h3></div>
    <div class="activity"><h3>Activity</h3></div>
  </div>
</body>
</html>
EOF
```

> 💡 **Grid within Grid (subgrid):** The stats section is itself a 4-column grid inside the dashboard grid. Grid layouts naturally nest. Named areas make the code read like a wireframe — you can see the exact layout from the CSS alone.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/grid-step7.html', 'utf8');
console.log(html.includes('sidebar') && html.includes('grid-area') ? '✓ Dashboard grid areas found' : '✗ Missing');
"
✓ Dashboard grid areas found
```

---

### Step 8: Capstone — Responsive Image Gallery

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Image Gallery</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; background: #111; color: white; }
    header {
      padding: 20px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #333;
    }
    .gallery {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 4px;
      padding: 4px;
    }
    .gallery-item {
      position: relative;
      overflow: hidden;
      aspect-ratio: 1;
      cursor: pointer;
    }
    .gallery-item.wide { grid-column: span 2; aspect-ratio: 2 / 1; }
    .gallery-item.tall { grid-row: span 2; aspect-ratio: 1 / 2; }
    .gallery-thumb {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 4rem;
      transition: transform 0.3s ease;
    }
    .gallery-item:hover .gallery-thumb { transform: scale(1.05); }
    .gallery-overlay {
      position: absolute;
      bottom: 0; left: 0; right: 0;
      background: linear-gradient(transparent, rgba(0,0,0,0.8));
      padding: 20px 16px 12px;
      transform: translateY(100%);
      transition: transform 0.3s ease;
    }
    .gallery-item:hover .gallery-overlay { transform: translateY(0); }
    .gallery-overlay h3 { font-size: 0.95rem; margin-bottom: 4px; }
    .gallery-overlay p  { font-size: 0.75rem; color: #ccc; }
  </style>
</head>
<body>
  <header>
    <h1>🖼️ Photo Gallery</h1>
    <nav style="display:flex;gap:20px"><a href="#" style="color:#aaa;text-decoration:none">All</a><a href="#" style="color:white;text-decoration:none">Nature</a><a href="#" style="color:#aaa;text-decoration:none">Urban</a></nav>
  </header>
  <div class="gallery">
    <div class="gallery-item wide">
      <div class="gallery-thumb" style="background:linear-gradient(135deg,#667eea,#764ba2)">🌌</div>
      <div class="gallery-overlay"><h3>Night Sky</h3><p>Milky Way, 2024</p></div>
    </div>
    <div class="gallery-item">
      <div class="gallery-thumb" style="background:linear-gradient(135deg,#f093fb,#f5576c)">🌸</div>
      <div class="gallery-overlay"><h3>Cherry Blossoms</h3><p>Spring Collection</p></div>
    </div>
    <div class="gallery-item tall">
      <div class="gallery-thumb" style="background:linear-gradient(135deg,#4facfe,#00f2fe)">🗼</div>
      <div class="gallery-overlay"><h3>City Tower</h3><p>Urban Architecture</p></div>
    </div>
    <div class="gallery-item">
      <div class="gallery-thumb" style="background:linear-gradient(135deg,#43e97b,#38f9d7)">🌲</div>
      <div class="gallery-overlay"><h3>Forest Path</h3><p>Nature Series</p></div>
    </div>
    <div class="gallery-item">
      <div class="gallery-thumb" style="background:linear-gradient(135deg,#fa709a,#fee140)">🌅</div>
      <div class="gallery-overlay"><h3>Sunrise</h3><p>Golden Hour</p></div>
    </div>
    <div class="gallery-item">
      <div class="gallery-thumb" style="background:linear-gradient(135deg,#a18cd1,#fbc2eb)">🏔️</div>
      <div class="gallery-overlay"><h3>Mountain Peak</h3><p>Adventure Series</p></div>
    </div>
    <div class="gallery-item wide">
      <div class="gallery-thumb" style="background:linear-gradient(135deg,#ffecd2,#fcb69f)">🏖️</div>
      <div class="gallery-overlay"><h3>Beach Panorama</h3><p>Summer 2024</p></div>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/grid.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Image Gallery</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; background: #111; color: white; }
    .gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 4px; padding: 4px; }
    .gallery-item { position: relative; overflow: hidden; aspect-ratio: 1; cursor: pointer; }
    .gallery-item.wide { grid-column: span 2; aspect-ratio: 2 / 1; }
    .gallery-item.tall { grid-row: span 2; aspect-ratio: 1 / 2; }
    .gallery-thumb { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; font-size: 4rem; transition: transform 0.3s ease; }
    .gallery-item:hover .gallery-thumb { transform: scale(1.05); }
    .gallery-overlay { position: absolute; bottom: 0; left: 0; right: 0; background: linear-gradient(transparent, rgba(0,0,0,0.8)); padding: 20px 16px 12px; transform: translateY(100%); transition: transform 0.3s ease; }
    .gallery-item:hover .gallery-overlay { transform: translateY(0); }
  </style>
</head>
<body>
  <div class="gallery">
    <div class="gallery-item wide"><div class="gallery-thumb" style="background:linear-gradient(135deg,#667eea,#764ba2)">🌌</div><div class="gallery-overlay"><h3>Night Sky</h3></div></div>
    <div class="gallery-item"><div class="gallery-thumb" style="background:linear-gradient(135deg,#f093fb,#f5576c)">🌸</div><div class="gallery-overlay"><h3>Blossoms</h3></div></div>
    <div class="gallery-item tall"><div class="gallery-thumb" style="background:linear-gradient(135deg,#4facfe,#00f2fe)">🗼</div><div class="gallery-overlay"><h3>Tower</h3></div></div>
    <div class="gallery-item"><div class="gallery-thumb" style="background:linear-gradient(135deg,#43e97b,#38f9d7)">🌲</div><div class="gallery-overlay"><h3>Forest</h3></div></div>
    <div class="gallery-item"><div class="gallery-thumb" style="background:linear-gradient(135deg,#fa709a,#fee140)">🌅</div><div class="gallery-overlay"><h3>Sunrise</h3></div></div>
  </div>
</body>
</html>
EOF
```

> 💡 **Grid masonry patterns** — `span 2` and `span 2` on items create the Pinterest-like layout. Combined with `auto-fit + minmax`, the gallery reflows perfectly on any screen size. The hover overlay uses CSS transitions (covered in Lab 10) — these techniques compound beautifully.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/grid.html', 'utf8');
console.log(html.includes('display: grid') || html.includes('display:grid') ? '✓ Grid gallery found' : '✗ Missing');
console.log(html.includes('span') ? '✓ Grid spanning found' : '✗ Missing span');
"
✓ Grid gallery found
✓ Grid spanning found
```

---

## Verification

```bash
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const checks = [
  ['grid-step1.html', 'grid-template-columns'],
  ['grid-step2.html', 'grid-column'],
  ['grid-step3.html', 'grid-template-areas'],
  ['grid-step4.html', 'minmax'],
  ['grid-step5.html', 'auto-fit'],
  ['grid-step6.html', 'grid-row'],
  ['grid-step7.html', 'grid-area'],
  ['grid.html', 'display: grid'],
];
checks.forEach(([file, check]) => {
  try {
    const html = fs.readFileSync('/workspace/' + file, 'utf8');
    console.log(html.includes(check) ? '✓ ' + file : '✗ ' + file);
  } catch(e) { console.log('✗ ' + file + ' not found'); }
});
"
```

## Summary

| Concept | Syntax | Use Case |
|---------|--------|----------|
| Basic grid | `display: grid` | Enable grid on container |
| Fixed columns | `grid-template-columns: 200px 1fr` | Sidebar + content |
| Responsive columns | `repeat(auto-fit, minmax(250px, 1fr))` | Card grids |
| Named areas | `grid-template-areas` | Page layout |
| Item placement | `grid-column: 1 / 3` | Spanning cells |
| Fractional units | `fr` | Proportional sizing |

## Further Reading
- [MDN CSS Grid Guide](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Grids)
- [CSS-Tricks Grid Guide](https://css-tricks.com/snippets/css/complete-guide-grid/)
- [Grid Garden](https://cssgridgarden.com/) — interactive game
