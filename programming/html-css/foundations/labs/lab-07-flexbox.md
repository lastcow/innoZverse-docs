# Lab 7: CSS Flexbox Layout

## Objective
Master CSS Flexbox to build one-dimensional layouts — rows and columns — with powerful alignment, spacing, and ordering controls.

## Background
Flexbox (Flexible Box Layout) is a CSS layout model designed for distributing space and aligning items in a single axis. It solves common layout challenges like centering elements, equal-height columns, and responsive navigation bars that were painful with older CSS techniques.

## Time
35 minutes

## Prerequisites
- Lab 03: Box Model & Layout
- Lab 05: Positioning & Z-index

## Tools
```bash
docker run --rm -it -v /tmp:/workspace zchencow/innozverse-htmlcss:latest bash
```

---

## Lab Instructions

### Step 1: Flex Container Basics

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flex Container Basics</title>
  <style>
    .container {
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
      background: #f0f0f0;
      padding: 20px;
      height: 100px;
    }
    .box {
      width: 80px;
      height: 60px;
      background: #3498db;
      color: white;
      display: flex;
      justify-content: center;
      align-items: center;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <h2>Flex Container: justify-content & align-items</h2>
  <div class="container">
    <div class="box">1</div>
    <div class="box">2</div>
    <div class="box">3</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/flex-step1.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flex Container Basics</title>
  <style>
    .container {
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      align-items: center;
      background: #f0f0f0;
      padding: 20px;
      height: 100px;
    }
    .box {
      width: 80px; height: 60px;
      background: #3498db;
      color: white;
      display: flex;
      justify-content: center;
      align-items: center;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="box">1</div>
    <div class="box">2</div>
    <div class="box">3</div>
  </div>
</body>
</html>
EOF
```

> 💡 **Why Flexbox?** Before flexbox, centering elements vertically required hacks. `display: flex` on a parent turns all direct children into flex items. `justify-content` controls alignment along the main axis (horizontal by default), while `align-items` controls the cross axis (vertical).

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/flex-step1.html', 'utf8');
console.log(html.includes('display: flex') || html.includes('display:flex') ? '✓ Flex container found' : '✗ Missing flex');
console.log(html.includes('justify-content') ? '✓ justify-content found' : '✗ Missing justify-content');
"
✓ Flex container found
✓ justify-content found
```

---

### Step 2: Flex Items — Grow, Shrink, Basis

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flex Items</title>
  <style>
    .container {
      display: flex;
      gap: 10px;
      padding: 20px;
      background: #ecf0f1;
    }
    .item-a {
      flex: 2 1 200px; /* grow:2, shrink:1, basis:200px */
      background: #e74c3c;
      color: white;
      padding: 20px;
    }
    .item-b {
      flex: 1 1 100px;
      background: #2ecc71;
      color: white;
      padding: 20px;
    }
    .item-c {
      flex: 0 0 120px; /* fixed width, no grow/shrink */
      background: #9b59b6;
      color: white;
      padding: 20px;
    }
  </style>
</head>
<body>
  <h2>Flex Items: flex-grow, flex-shrink, flex-basis</h2>
  <div class="container">
    <div class="item-a">A: flex 2 1 200px</div>
    <div class="item-b">B: flex 1 1 100px</div>
    <div class="item-c">C: flex 0 0 120px</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/flex-step2.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flex Items</title>
  <style>
    .container { display: flex; gap: 10px; padding: 20px; background: #ecf0f1; }
    .item-a { flex: 2 1 200px; background: #e74c3c; color: white; padding: 20px; }
    .item-b { flex: 1 1 100px; background: #2ecc71; color: white; padding: 20px; }
    .item-c { flex: 0 0 120px; background: #9b59b6; color: white; padding: 20px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="item-a">A: flex 2 1 200px</div>
    <div class="item-b">B: flex 1 1 100px</div>
    <div class="item-c">C: flex 0 0 120px</div>
  </div>
</body>
</html>
EOF
```

> 💡 **The `flex` shorthand** is `flex: grow shrink basis`. Item A takes 2× more of available space than B. Item C is rigid — it never grows or shrinks. `flex: 1` is shorthand for `flex: 1 1 0%` — equal distribution of all available space.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/flex-step2.html', 'utf8');
console.log(html.includes('flex:') || html.includes('flex: ') ? '✓ flex shorthand found' : '✗ Missing');
"
✓ flex shorthand found
```

---

### Step 3: Flex Wrap & Alignment

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flex Wrap</title>
  <style>
    .container {
      display: flex;
      flex-wrap: wrap;
      gap: 15px;
      align-content: flex-start;
      padding: 20px;
      background: #f8f9fa;
      min-height: 200px;
    }
    .card {
      flex: 0 0 calc(33.333% - 10px);
      background: #007bff;
      color: white;
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }
  </style>
</head>
<body>
  <h2>flex-wrap: wrap creates a responsive grid</h2>
  <div class="container">
    <div class="card">Card 1</div>
    <div class="card">Card 2</div>
    <div class="card">Card 3</div>
    <div class="card">Card 4</div>
    <div class="card">Card 5</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/flex-step3.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flex Wrap</title>
  <style>
    .container { display: flex; flex-wrap: wrap; gap: 15px; align-content: flex-start; padding: 20px; background: #f8f9fa; min-height: 200px; }
    .card { flex: 0 0 calc(33.333% - 10px); background: #007bff; color: white; padding: 20px; border-radius: 8px; text-align: center; }
  </style>
</head>
<body>
  <div class="container">
    <div class="card">Card 1</div>
    <div class="card">Card 2</div>
    <div class="card">Card 3</div>
    <div class="card">Card 4</div>
    <div class="card">Card 5</div>
  </div>
</body>
</html>
EOF
```

> 💡 **`flex-wrap: wrap`** allows flex items to break onto multiple lines when they don't fit. `gap` adds spacing between items (replaces margin hacks). `align-content` controls how multiple rows align in the container — only works when `flex-wrap` is active.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/flex-step3.html', 'utf8');
console.log(html.includes('flex-wrap') ? '✓ flex-wrap found' : '✗ Missing');
console.log(html.includes('gap') ? '✓ gap property found' : '✗ Missing gap');
"
✓ flex-wrap found
✓ gap property found
```

---

### Step 4: Order & align-self

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Order and align-self</title>
  <style>
    .container {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 20px;
      background: #f0f0f0;
      height: 150px;
    }
    .item { padding: 15px; color: white; border-radius: 4px; }
    .a { background: #e74c3c; order: 3; }
    .b { background: #3498db; order: 1; }
    .c { background: #2ecc71; order: 2; align-self: flex-start; }
    .d { background: #f39c12; order: 4; align-self: flex-end; }
  </style>
</head>
<body>
  <h2>order property reorders without changing HTML; align-self overrides container alignment</h2>
  <div class="container">
    <div class="item a">A (order:3)</div>
    <div class="item b">B (order:1)</div>
    <div class="item c">C (order:2, align-self:flex-start)</div>
    <div class="item d">D (order:4, align-self:flex-end)</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/flex-step4.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Order and align-self</title>
  <style>
    .container { display: flex; align-items: center; gap: 10px; padding: 20px; background: #f0f0f0; height: 150px; }
    .item { padding: 15px; color: white; border-radius: 4px; }
    .a { background: #e74c3c; order: 3; }
    .b { background: #3498db; order: 1; }
    .c { background: #2ecc71; order: 2; align-self: flex-start; }
    .d { background: #f39c12; order: 4; align-self: flex-end; }
  </style>
</head>
<body>
  <div class="container">
    <div class="item a">A (order:3)</div>
    <div class="item b">B (order:1)</div>
    <div class="item c">C (order:2, align-self:flex-start)</div>
    <div class="item d">D (order:4, align-self:flex-end)</div>
  </div>
</body>
</html>
EOF
```

> 💡 **`order`** changes visual display order without modifying HTML — great for responsive layouts where mobile and desktop need different orderings. **`align-self`** lets individual items override the container's `align-items` value.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/flex-step4.html', 'utf8');
console.log(html.includes('order:') || html.includes('order: ') ? '✓ order property found' : '✗ Missing');
console.log(html.includes('align-self') ? '✓ align-self found' : '✗ Missing');
"
✓ order property found
✓ align-self found
```

---

### Step 5: Navigation Bar with Flexbox

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flexbox Navbar</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #2c3e50;
      padding: 0 30px;
      height: 60px;
    }
    .logo {
      color: #ecf0f1;
      font-size: 1.4rem;
      font-weight: bold;
    }
    .nav-links {
      display: flex;
      gap: 30px;
      list-style: none;
    }
    .nav-links a {
      color: #bdc3c7;
      text-decoration: none;
      transition: color 0.2s;
    }
    .nav-links a:hover { color: #ecf0f1; }
    .nav-cta {
      background: #e74c3c;
      color: white;
      padding: 8px 20px;
      border-radius: 4px;
      text-decoration: none;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <nav>
    <div class="logo">🌐 MyBrand</div>
    <ul class="nav-links">
      <li><a href="#">Home</a></li>
      <li><a href="#">About</a></li>
      <li><a href="#">Services</a></li>
      <li><a href="#">Blog</a></li>
    </ul>
    <a href="#" class="nav-cta">Get Started</a>
  </nav>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/flex-step5.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flexbox Navbar</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    nav { display: flex; justify-content: space-between; align-items: center; background: #2c3e50; padding: 0 30px; height: 60px; }
    .logo { color: #ecf0f1; font-size: 1.4rem; font-weight: bold; }
    .nav-links { display: flex; gap: 30px; list-style: none; }
    .nav-links a { color: #bdc3c7; text-decoration: none; }
    .nav-cta { background: #e74c3c; color: white; padding: 8px 20px; border-radius: 4px; text-decoration: none; }
  </style>
</head>
<body>
  <nav>
    <div class="logo">🌐 MyBrand</div>
    <ul class="nav-links">
      <li><a href="#">Home</a></li>
      <li><a href="#">About</a></li>
      <li><a href="#">Services</a></li>
    </ul>
    <a href="#" class="nav-cta">Get Started</a>
  </nav>
</body>
</html>
EOF
```

> 💡 **This is the most common flexbox pattern.** Logo on left, links centered, CTA on right — `justify-content: space-between` handles the spacing automatically. Nested flexbox (nav-links is also a flex container) is perfectly valid and widely used.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/flex-step5.html', 'utf8');
console.log(html.includes('space-between') ? '✓ space-between found' : '✗ Missing');
console.log(html.includes('<nav>') ? '✓ nav element found' : '✗ Missing nav');
"
✓ space-between found
✓ nav element found
```

---

### Step 6: Card Grid with Flexbox

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flexbox Card Grid</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; padding: 20px; background: #f4f6f8; }
    .card-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 20px;
    }
    .card {
      flex: 1 1 280px;
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      display: flex;
      flex-direction: column;
    }
    .card-image {
      background: linear-gradient(135deg, #667eea, #764ba2);
      height: 160px;
    }
    .card-body {
      padding: 20px;
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    .card-title { font-size: 1.1rem; font-weight: bold; margin-bottom: 8px; }
    .card-text { color: #666; font-size: 0.9rem; flex: 1; }
    .card-btn {
      margin-top: 16px;
      background: #667eea;
      color: white;
      border: none;
      padding: 10px;
      border-radius: 6px;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <h2>Flexible Card Grid</h2>
  <div class="card-grid">
    <div class="card">
      <div class="card-image"></div>
      <div class="card-body">
        <h3 class="card-title">Card Title One</h3>
        <p class="card-text">Flexbox makes cards equal height automatically — the card-body stretches to fill available space.</p>
        <button class="card-btn">Learn More</button>
      </div>
    </div>
    <div class="card">
      <div class="card-image"></div>
      <div class="card-body">
        <h3 class="card-title">Card Title Two</h3>
        <p class="card-text">With flex: 1 1 280px, cards grow to fill the row but collapse gracefully on small screens.</p>
        <button class="card-btn">Learn More</button>
      </div>
    </div>
    <div class="card">
      <div class="card-image"></div>
      <div class="card-body">
        <h3 class="card-title">Card Title Three</h3>
        <p class="card-text">All buttons align at the bottom because card-body is also a flex column with flex: 1 on the text.</p>
        <button class="card-btn">Learn More</button>
      </div>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/flex-step6.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Flexbox Card Grid</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; padding: 20px; }
    .card-grid { display: flex; flex-wrap: wrap; gap: 20px; }
    .card { flex: 1 1 280px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
    .card-image { background: linear-gradient(135deg, #667eea, #764ba2); height: 160px; }
    .card-body { padding: 20px; flex: 1; display: flex; flex-direction: column; }
    .card-text { flex: 1; color: #666; }
    .card-btn { margin-top: 16px; background: #667eea; color: white; border: none; padding: 10px; border-radius: 6px; }
  </style>
</head>
<body>
  <div class="card-grid">
    <div class="card"><div class="card-image"></div><div class="card-body"><h3>Card One</h3><p class="card-text">Equal height cards via flexbox column.</p><button class="card-btn">Learn More</button></div></div>
    <div class="card"><div class="card-image"></div><div class="card-body"><h3>Card Two</h3><p class="card-text">Buttons align at bottom automatically.</p><button class="card-btn">Learn More</button></div></div>
    <div class="card"><div class="card-image"></div><div class="card-body"><h3>Card Three</h3><p class="card-text">Responsive without media queries.</p><button class="card-btn">Learn More</button></div></div>
  </div>
</body>
</html>
EOF
```

> 💡 **Equal-height cards with bottom-aligned buttons** — the holy grail of card design. The trick: make the card a `flex-direction: column`, give the text `flex: 1` so it stretches, and the button naturally stays at the bottom. Pure flexbox, no JavaScript.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/flex-step6.html', 'utf8');
console.log(html.includes('flex-wrap') ? '✓ flex-wrap found' : '✗ Missing');
console.log(html.includes('flex-direction: column') || html.includes('flex-direction:column') ? '✓ column direction found' : '✗ Missing column');
"
✓ flex-wrap found
✓ column direction found
```

---

### Step 7: Holy Grail Layout

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Holy Grail Layout</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { display: flex; flex-direction: column; min-height: 100vh; font-family: sans-serif; }
    header {
      background: #2c3e50;
      color: white;
      padding: 15px 30px;
      font-size: 1.2rem;
      font-weight: bold;
    }
    .content-area {
      display: flex;
      flex: 1;
    }
    aside.left {
      width: 200px;
      flex-shrink: 0;
      background: #ecf0f1;
      padding: 20px;
    }
    main {
      flex: 1;
      padding: 30px;
      background: white;
    }
    aside.right {
      width: 180px;
      flex-shrink: 0;
      background: #ffeaa7;
      padding: 20px;
    }
    footer {
      background: #2c3e50;
      color: white;
      padding: 15px 30px;
      text-align: center;
    }
    nav ul { list-style: none; padding: 0; }
    nav li { margin: 10px 0; }
    nav a { color: #2c3e50; text-decoration: none; }
  </style>
</head>
<body>
  <header>🌐 Holy Grail Layout</header>
  <div class="content-area">
    <aside class="left">
      <h3>Navigation</h3>
      <nav>
        <ul>
          <li><a href="#">Home</a></li>
          <li><a href="#">About</a></li>
          <li><a href="#">Services</a></li>
          <li><a href="#">Contact</a></li>
        </ul>
      </nav>
    </aside>
    <main>
      <h1>Main Content Area</h1>
      <p>This is the famous "Holy Grail Layout" — header, left sidebar, main, right sidebar, footer. For decades, CSS developers struggled to achieve this. With flexbox, it's about 20 lines of CSS.</p>
    </main>
    <aside class="right">
      <h3>Widgets</h3>
      <p>Ad space, social links, recent posts...</p>
    </aside>
  </div>
  <footer>© 2024 My Website</footer>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/flex-step7.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Holy Grail Layout</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { display: flex; flex-direction: column; min-height: 100vh; font-family: sans-serif; }
    header { background: #2c3e50; color: white; padding: 15px 30px; }
    .content-area { display: flex; flex: 1; }
    aside.left { width: 200px; flex-shrink: 0; background: #ecf0f1; padding: 20px; }
    main { flex: 1; padding: 30px; }
    aside.right { width: 180px; flex-shrink: 0; background: #ffeaa7; padding: 20px; }
    footer { background: #2c3e50; color: white; padding: 15px 30px; text-align: center; }
  </style>
</head>
<body>
  <header>Holy Grail Layout</header>
  <div class="content-area">
    <aside class="left"><h3>Nav</h3></aside>
    <main><h1>Main Content</h1><p>Holy grail with flexbox.</p></main>
    <aside class="right"><h3>Widgets</h3></aside>
  </div>
  <footer>Footer</footer>
</body>
</html>
EOF
```

> 💡 **Two layers of flexbox:** The `body` is a flex column (stacking header/content/footer). The `.content-area` is a flex row (sidebars + main). `flex: 1` on main makes it take all remaining space. `flex-shrink: 0` on sidebars prevents them from getting squeezed.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/flex-step7.html', 'utf8');
console.log(html.includes('min-height: 100vh') || html.includes('min-height:100vh') ? '✓ Full height layout' : '✗ Missing');
console.log(html.includes('flex: 1') || html.includes('flex:1') ? '✓ flex:1 on main' : '✗ Missing');
"
✓ Full height layout
✓ flex:1 on main
```

---

### Step 8: Capstone — Responsive Product Card

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Product Card Component</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; padding: 20px; }
    .product-card {
      background: white;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0,0,0,0.12);
      width: 320px;
      display: flex;
      flex-direction: column;
    }
    .product-badge {
      position: relative;
    }
    .product-image {
      background: linear-gradient(135deg, #f093fb, #f5576c);
      height: 200px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 4rem;
    }
    .badge {
      position: absolute;
      top: 12px;
      right: 12px;
      background: #ff4757;
      color: white;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: bold;
    }
    .product-body {
      padding: 20px;
      flex: 1;
      display: flex;
      flex-direction: column;
    }
    .product-category {
      font-size: 0.75rem;
      color: #999;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 6px;
    }
    .product-name {
      font-size: 1.2rem;
      font-weight: 700;
      color: #2d3436;
      margin-bottom: 8px;
    }
    .product-description {
      font-size: 0.9rem;
      color: #636e72;
      line-height: 1.5;
      flex: 1;
      margin-bottom: 16px;
    }
    .product-rating {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 16px;
    }
    .stars { color: #fdcb6e; }
    .rating-count { font-size: 0.85rem; color: #999; }
    .product-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .product-price {
      display: flex;
      flex-direction: column;
    }
    .price-original { font-size: 0.8rem; color: #999; text-decoration: line-through; }
    .price-sale { font-size: 1.4rem; font-weight: 700; color: #e17055; }
    .btn-add {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      border: none;
      padding: 12px 20px;
      border-radius: 8px;
      cursor: pointer;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .btn-add:hover { opacity: 0.9; transform: translateY(-1px); transition: all 0.2s; }
  </style>
</head>
<body>
  <div class="product-card">
    <div class="product-badge">
      <div class="product-image">🎧</div>
      <span class="badge">SALE -30%</span>
    </div>
    <div class="product-body">
      <span class="product-category">Electronics</span>
      <h2 class="product-name">Pro Wireless Headphones</h2>
      <p class="product-description">Premium noise-canceling headphones with 40-hour battery life, Hi-Fi audio, and ultra-comfortable design.</p>
      <div class="product-rating">
        <span class="stars">★★★★★</span>
        <span class="rating-count">(2,847 reviews)</span>
      </div>
      <div class="product-footer">
        <div class="product-price">
          <span class="price-original">$199.99</span>
          <span class="price-sale">$139.99</span>
        </div>
        <button class="btn-add">🛒 Add to Cart</button>
      </div>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/flex.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Product Card</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
    .product-card { background: white; border-radius: 16px; width: 320px; display: flex; flex-direction: column; box-shadow: 0 4px 20px rgba(0,0,0,0.12); }
    .product-image { background: linear-gradient(135deg, #f093fb, #f5576c); height: 200px; display: flex; align-items: center; justify-content: center; font-size: 4rem; }
    .product-body { padding: 20px; flex: 1; display: flex; flex-direction: column; }
    .product-footer { display: flex; justify-content: space-between; align-items: center; }
    .price-sale { font-size: 1.4rem; font-weight: 700; color: #e17055; }
    .btn-add { background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 6px; }
  </style>
</head>
<body>
  <div class="product-card">
    <div class="product-image">🎧</div>
    <div class="product-body">
      <h2>Pro Wireless Headphones</h2>
      <p style="flex:1; color:#666; margin: 10px 0;">Premium noise-canceling headphones.</p>
      <div class="product-footer">
        <span class="price-sale">$139.99</span>
        <button class="btn-add">🛒 Add to Cart</button>
      </div>
    </div>
  </div>
</body>
</html>
EOF
```

> 💡 **Capstone recap:** This card uses flexbox at three levels — body centering, card column layout, and footer row layout. The pattern (flex container → column → footer space-between) is used in virtually every modern card component. Master this and you'll recognize it everywhere.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/flex.html', 'utf8');
console.log(html.includes('display: flex') || html.includes('display:flex') ? 'FLEX OK' : 'MISSING FLEX');
console.log(html.includes('flex-direction') ? '✓ flex-direction found' : '✗ Missing');
"
FLEX OK
✓ flex-direction found
```

---

## Verification

Run the full lab verification:
```bash
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const checks = [
  ['flex-step1.html', 'display: flex'],
  ['flex-step2.html', 'flex:'],
  ['flex-step3.html', 'flex-wrap'],
  ['flex-step4.html', 'align-self'],
  ['flex-step5.html', 'space-between'],
  ['flex-step6.html', 'flex-wrap'],
  ['flex-step7.html', 'min-height'],
  ['flex.html', 'display: flex'],
];
checks.forEach(([file, check]) => {
  try {
    const html = fs.readFileSync('/workspace/' + file, 'utf8');
    console.log(html.includes(check) ? '✓ ' + file : '✗ ' + file + ' missing: ' + check);
  } catch(e) { console.log('✗ ' + file + ' not found'); }
});
"
```

## Summary

| Concept | Property | Use Case |
|---------|----------|----------|
| Flex container | `display: flex` | Enable flexbox on parent |
| Main axis | `justify-content` | Horizontal alignment (row) |
| Cross axis | `align-items` | Vertical alignment (row) |
| Item growth | `flex: grow shrink basis` | Proportional sizing |
| Wrapping | `flex-wrap: wrap` | Responsive multi-line |
| Reordering | `order` | Visual reorder without HTML change |
| Individual align | `align-self` | Override per item |

## Further Reading
- [MDN Flexbox Guide](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Flexbox)
- [CSS-Tricks Flexbox Guide](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [Flexbox Froggy](https://flexboxfroggy.com/) — interactive game
