# Lab 9: Responsive Design & Media Queries

## Objective
Build websites that look great on every screen — from smartphones to 4K monitors — using mobile-first design, media queries, fluid typography, and responsive images.

## Background
Over 60% of web traffic comes from mobile devices. Responsive design isn't optional — it's the baseline. CSS provides powerful tools: viewport meta tag, `@media` queries, `clamp()`, `srcset`, and CSS custom properties. This lab covers all of them.

## Time
35 minutes

## Prerequisites
- Lab 07: CSS Flexbox
- Lab 08: CSS Grid

## Tools
```bash
docker run --rm -it -v /tmp:/workspace zchencow/innozverse-htmlcss:latest bash
```

---

## Lab Instructions

### Step 1: Viewport Meta Tag & Mobile-First

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mobile First</title>
  <style>
    /* MOBILE FIRST: styles here apply to ALL screen sizes */
    body {
      font-family: sans-serif;
      padding: 16px;
      font-size: 16px;
      background: #f8f9fa;
    }
    .card {
      background: white;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 16px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* TABLET: add styles for 600px and above */
    @media (min-width: 600px) {
      body { padding: 24px; }
      .card { padding: 28px; }
    }
    /* DESKTOP: add styles for 1024px and above */
    @media (min-width: 1024px) {
      body { max-width: 1200px; margin: 0 auto; padding: 40px; }
    }
  </style>
</head>
<body>
  <h1>Mobile-First Design</h1>
  <div class="card">
    <h2>What is Mobile-First?</h2>
    <p>Start with mobile CSS as the base. Use min-width media queries to progressively enhance for larger screens. This approach is better than max-width (desktop-first) because it forces you to prioritize content over decoration.</p>
  </div>
  <div class="card">
    <h2>The Viewport Meta Tag</h2>
    <p>Without <code>&lt;meta name="viewport"&gt;</code>, mobile browsers render the page at 980px and scale it down, making text tiny. This tag tells the browser to use the device's actual width.</p>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/responsive-step1.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mobile First</title>
  <style>
    body { font-family: sans-serif; padding: 16px; background: #f8f9fa; }
    .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    @media (min-width: 600px) { body { padding: 24px; } }
    @media (min-width: 1024px) { body { max-width: 1200px; margin: 0 auto; padding: 40px; } }
  </style>
</head>
<body>
  <h1>Mobile-First Design</h1>
  <div class="card"><h2>Mobile First</h2><p>Start small, enhance for larger screens.</p></div>
  <div class="card"><h2>Viewport Meta Tag</h2><p>Tells browser to use actual device width.</p></div>
</body>
</html>
EOF
```

> 💡 **Mobile-first means writing `min-width` media queries, not `max-width`.** Start with the simplest layout (mobile) and progressively add complexity for larger screens. This results in leaner CSS and forces content prioritization.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/responsive-step1.html', 'utf8');
console.log(html.includes('viewport') ? '✓ Viewport meta found' : '✗ Missing viewport');
console.log(html.includes('min-width') ? '✓ Mobile-first media query found' : '✗ Missing min-width');
"
✓ Viewport meta found
✓ Mobile-first media query found
```

---

### Step 2: Media Queries & Breakpoints

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Media Queries</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; margin: 0; padding: 20px; }
    .layout {
      display: grid;
      gap: 16px;
      /* Mobile: single column */
      grid-template-columns: 1fr;
    }
    /* Tablet: 2 columns */
    @media (min-width: 640px) {
      .layout { grid-template-columns: repeat(2, 1fr); }
    }
    /* Desktop: 3 columns */
    @media (min-width: 1024px) {
      .layout { grid-template-columns: repeat(3, 1fr); }
    }
    /* Large: 4 columns */
    @media (min-width: 1280px) {
      .layout { grid-template-columns: repeat(4, 1fr); }
    }
    .card {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
      padding: 24px;
      border-radius: 12px;
      text-align: center;
    }
    /* Screen orientation media query */
    @media (orientation: landscape) and (max-width: 768px) {
      body { padding: 10px; }
    }
    /* Print media query */
    @media print {
      body { background: white; }
      .card { break-inside: avoid; }
    }
  </style>
</head>
<body>
  <h2>Responsive Grid with Breakpoints</h2>
  <p>Resize the browser to see columns change: 1 → 2 → 3 → 4</p>
  <div class="layout">
    <div class="card"><h3>Card 1</h3><p>Mobile: 1 col</p></div>
    <div class="card"><h3>Card 2</h3><p>640px+: 2 cols</p></div>
    <div class="card"><h3>Card 3</h3><p>1024px+: 3 cols</p></div>
    <div class="card"><h3>Card 4</h3><p>1280px+: 4 cols</p></div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/responsive-step2.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Media Queries</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; margin: 0; padding: 20px; }
    .layout { display: grid; gap: 16px; grid-template-columns: 1fr; }
    @media (min-width: 640px) { .layout { grid-template-columns: repeat(2, 1fr); } }
    @media (min-width: 1024px) { .layout { grid-template-columns: repeat(3, 1fr); } }
    @media (min-width: 1280px) { .layout { grid-template-columns: repeat(4, 1fr); } }
    .card { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 24px; border-radius: 12px; text-align: center; }
  </style>
</head>
<body>
  <div class="layout">
    <div class="card"><h3>Card 1</h3><p>Mobile: 1 col</p></div>
    <div class="card"><h3>Card 2</h3><p>640px+: 2 cols</p></div>
    <div class="card"><h3>Card 3</h3><p>1024px+: 3 cols</p></div>
    <div class="card"><h3>Card 4</h3><p>1280px+: 4 cols</p></div>
  </div>
</body>
</html>
EOF
```

> 💡 **Common breakpoints:** 640px (small tablet), 768px (tablet), 1024px (laptop), 1280px (desktop), 1536px (large). You don't need to use all of them — use breakpoints where your content naturally breaks, not based on device sizes.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/responsive-step2.html', 'utf8');
const matches = (html.match(/@media/g) || []).length;
console.log(matches >= 3 ? '✓ Multiple media queries: ' + matches : '✗ Need more breakpoints');
"
✓ Multiple media queries: 3
```

---

### Step 3: Fluid Typography with clamp()

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fluid Typography</title>
  <style>
    body { font-family: sans-serif; padding: 20px; max-width: 900px; margin: 0 auto; }
    /* clamp(min, preferred, max) */
    h1 {
      font-size: clamp(1.5rem, 5vw, 3rem);
      /* min: 1.5rem (24px), scales with viewport, max: 3rem (48px) */
    }
    h2 {
      font-size: clamp(1.2rem, 3vw, 2rem);
    }
    p {
      font-size: clamp(0.9rem, 2vw, 1.1rem);
      line-height: 1.6;
    }
    .big-text {
      font-size: clamp(2rem, 8vw, 5rem);
      font-weight: 900;
      background: linear-gradient(135deg, #667eea, #f5576c);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    /* Container-relative: rem vs em */
    .em-example {
      font-size: 1.2rem; /* relative to root */
      padding: 1em; /* relative to this element's font-size */
      background: #f0f0f0;
      margin: 20px 0;
      border-radius: 8px;
    }
    .em-example p {
      font-size: 0.875em; /* 87.5% of parent's font-size */
    }
  </style>
</head>
<body>
  <div class="big-text">FLUID</div>
  <h1>Heading scales with viewport width</h1>
  <h2>Subheading also fluid</h2>
  <p>Body text uses clamp() — it's never too small to read on mobile, never too large on desktop. Resize the browser to see smooth scaling without media query jumps.</p>
  <div class="em-example">
    <h3>rem vs em</h3>
    <p>rem = relative to root (html) font-size. em = relative to parent. Use rem for font sizes, em for padding/margin.</p>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/responsive-step3.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Fluid Typography</title>
  <style>
    body { font-family: sans-serif; padding: 20px; max-width: 900px; margin: 0 auto; }
    h1 { font-size: clamp(1.5rem, 5vw, 3rem); }
    h2 { font-size: clamp(1.2rem, 3vw, 2rem); }
    p  { font-size: clamp(0.9rem, 2vw, 1.1rem); line-height: 1.6; }
    .big-text { font-size: clamp(2rem, 8vw, 5rem); font-weight: 900; color: #667eea; }
  </style>
</head>
<body>
  <div class="big-text">FLUID</div>
  <h1>Heading scales with viewport</h1>
  <p>clamp(min, preferred, max) gives smooth fluid scaling without jumps.</p>
</body>
</html>
EOF
```

> 💡 **`clamp(min, preferred, max)`** eliminates most font-size media queries. `clamp(1rem, 2.5vw, 1.5rem)` means: never smaller than 1rem, scale with viewport width, never larger than 1.5rem. `vw` = 1% of viewport width — great for fluid scaling.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/responsive-step3.html', 'utf8');
console.log(html.includes('clamp(') ? '✓ clamp() found' : '✗ Missing clamp');
console.log(html.includes('vw') ? '✓ vw units found' : '✗ Missing vw');
"
✓ clamp() found
✓ vw units found
```

---

### Step 4: Responsive Images

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Images</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    img { max-width: 100%; height: auto; display: block; }
    .image-container { max-width: 800px; margin: 0 auto; }
    figure { margin: 20px 0; background: #f8f9fa; border-radius: 8px; overflow: hidden; }
    figcaption { padding: 12px 16px; font-size: 0.9rem; color: #666; }
    /* CSS for object-fit */
    .cover-image {
      width: 100%;
      height: 300px;
      object-fit: cover;
      object-position: center top;
    }
  </style>
</head>
<body>
  <div class="image-container">
    <h2>Responsive Image Techniques</h2>

    <!-- 1. Basic: max-width: 100% -->
    <h3>1. max-width: 100% (simplest)</h3>
    <figure>
      <img src="https://picsum.photos/800/400" alt="Landscape photo" style="max-width:100%;height:auto">
      <figcaption>Image scales with container, never overflows</figcaption>
    </figure>

    <!-- 2. srcset for different resolutions -->
    <h3>2. srcset — serve different sizes</h3>
    <figure>
      <img
        src="https://picsum.photos/400/200"
        srcset="
          https://picsum.photos/400/200 400w,
          https://picsum.photos/800/400 800w,
          https://picsum.photos/1200/600 1200w
        "
        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 800px"
        alt="Responsive srcset example"
        style="max-width:100%;height:auto"
      >
      <figcaption>Browser picks the best size based on screen + pixel density</figcaption>
    </figure>

    <!-- 3. picture element for art direction -->
    <h3>3. picture element — different crops</h3>
    <figure>
      <picture>
        <source media="(min-width: 800px)" srcset="https://picsum.photos/800/300">
        <source media="(min-width: 400px)" srcset="https://picsum.photos/400/300">
        <img src="https://picsum.photos/300/300" alt="Art directed image" style="max-width:100%;height:auto">
      </picture>
      <figcaption>Different image crops for different screens</figcaption>
    </figure>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/responsive-step4.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Images</title>
  <style>
    body { font-family: sans-serif; padding: 20px; }
    img { max-width: 100%; height: auto; }
    figure { margin: 20px 0; background: #f8f9fa; border-radius: 8px; overflow: hidden; }
    figcaption { padding: 12px; font-size: 0.85rem; color: #666; }
  </style>
</head>
<body>
  <h2>Responsive Images</h2>
  <figure>
    <img src="https://picsum.photos/800/400" srcset="https://picsum.photos/400/200 400w, https://picsum.photos/800/400 800w" sizes="(max-width: 640px) 100vw, 800px" alt="Responsive image">
    <figcaption>srcset serves the right size for each screen</figcaption>
  </figure>
  <figure>
    <picture>
      <source media="(min-width: 800px)" srcset="https://picsum.photos/800/300">
      <img src="https://picsum.photos/300/300" alt="Art directed">
    </picture>
    <figcaption>picture element for art direction</figcaption>
  </figure>
</body>
</html>
EOF
```

> 💡 **`srcset` + `sizes`** tells the browser about multiple image versions and hints about display size. The browser then picks the optimal one based on screen size AND pixel density. `picture` element lets you serve completely different image crops for different screens — "art direction."

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/responsive-step4.html', 'utf8');
console.log(html.includes('srcset') ? '✓ srcset found' : '✗ Missing srcset');
console.log(html.includes('<picture>') ? '✓ picture element found' : '✗ Missing picture');
"
✓ srcset found
✓ picture element found
```

---

### Step 5: Breakpoint System

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Breakpoint System</title>
  <style>
    :root {
      --bp-sm: 640px;
      --bp-md: 768px;
      --bp-lg: 1024px;
      --bp-xl: 1280px;
    }
    * { box-sizing: border-box; }
    body { font-family: sans-serif; margin: 0; }
    /* Screen size indicator */
    .breakpoint-indicator {
      position: fixed;
      bottom: 10px;
      right: 10px;
      background: #2d3436;
      color: white;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 0.8rem;
      font-weight: bold;
    }
    .bp-label { display: none; }
    .bp-mobile .bp-label  { display: inline; }
    @media (min-width: 640px)  { .bp-sm .bp-label  { display: inline; } .bp-mobile .bp-label { display: none; } }
    @media (min-width: 768px)  { .bp-md .bp-label  { display: inline; } .bp-sm .bp-label { display: none; } }
    @media (min-width: 1024px) { .bp-lg .bp-label  { display: inline; } .bp-md .bp-label { display: none; } }
    @media (min-width: 1280px) { .bp-xl .bp-label  { display: inline; } .bp-lg .bp-label { display: none; } }
    /* Responsive layout demo */
    .page { padding: 20px; }
    .hero { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 40px 20px; text-align: center; }
    .hero h1 { font-size: clamp(1.5rem, 5vw, 3rem); margin-bottom: 16px; }
    .feature-grid { display: grid; grid-template-columns: 1fr; gap: 16px; margin-top: 30px; }
    @media (min-width: 640px)  { .feature-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (min-width: 1024px) { .feature-grid { grid-template-columns: repeat(3, 1fr); } }
    .feature { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  </style>
</head>
<body>
  <div class="breakpoint-indicator">
    <span class="bp-mobile bp-label">📱 Mobile (&lt;640px)</span>
    <span class="bp-sm bp-label">📱 SM (640px+)</span>
    <span class="bp-md bp-label">💻 MD (768px+)</span>
    <span class="bp-lg bp-label">🖥️ LG (1024px+)</span>
    <span class="bp-xl bp-label">🖥️ XL (1280px+)</span>
  </div>
  <div class="hero">
    <h1>Responsive Breakpoint System</h1>
    <p>Watch the indicator in the corner change as you resize</p>
  </div>
  <div class="page">
    <div class="feature-grid">
      <div class="feature"><h3>📱 Mobile</h3><p>Single column, touch-friendly</p></div>
      <div class="feature"><h3>💻 Tablet</h3><p>Two columns, hybrid interaction</p></div>
      <div class="feature"><h3>🖥️ Desktop</h3><p>Three columns, hover states</p></div>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/responsive-step5.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Breakpoint System</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; margin: 0; padding: 20px; }
    .feature-grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
    @media (min-width: 640px) { .feature-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (min-width: 1024px) { .feature-grid { grid-template-columns: repeat(3, 1fr); } }
    .feature { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
  </style>
</head>
<body>
  <div class="feature-grid">
    <div class="feature"><h3>📱 Mobile</h3><p>Single column layout</p></div>
    <div class="feature"><h3>💻 Tablet</h3><p>Two column layout at 640px+</p></div>
    <div class="feature"><h3>🖥️ Desktop</h3><p>Three column layout at 1024px+</p></div>
  </div>
</body>
</html>
EOF
```

> 💡 **Breakpoints are about content, not devices.** Don't say "this is the iPhone breakpoint" — say "at this width, my content starts to break." Add a breakpoint when the layout looks wrong, not based on device specs. Fewer breakpoints = simpler CSS.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/responsive-step5.html', 'utf8');
const bps = (html.match(/min-width/g) || []).length;
console.log(bps >= 2 ? '✓ Multiple breakpoints: ' + bps : '✗ Need more breakpoints');
"
✓ Multiple breakpoints: 2
```

---

### Step 6: Responsive Navigation

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Nav</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; }
    nav {
      background: #2c3e50;
      padding: 0 20px;
    }
    .nav-container {
      display: flex;
      justify-content: space-between;
      align-items: center;
      height: 60px;
    }
    .logo { color: white; font-size: 1.3rem; font-weight: bold; }
    .nav-toggle {
      display: flex;
      flex-direction: column;
      gap: 5px;
      cursor: pointer;
      padding: 5px;
    }
    .nav-toggle span {
      display: block;
      width: 24px;
      height: 2px;
      background: white;
      border-radius: 2px;
    }
    .nav-links {
      display: none; /* hidden on mobile */
      flex-direction: column;
      list-style: none;
      padding: 10px 0 20px;
    }
    .nav-links.open { display: flex; }
    .nav-links a {
      color: #bdc3c7;
      text-decoration: none;
      padding: 12px 0;
      display: block;
      border-top: 1px solid #34495e;
    }
    /* Desktop: show links inline, hide toggle */
    @media (min-width: 768px) {
      .nav-toggle { display: none; }
      .nav-links {
        display: flex !important;
        flex-direction: row;
        gap: 30px;
        padding: 0;
        align-items: center;
      }
      .nav-links a { border: none; padding: 0; }
      .nav-links a:hover { color: white; }
    }
  </style>
</head>
<body>
  <nav>
    <div class="nav-container">
      <div class="logo">🌐 Brand</div>
      <div class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')">
        <span></span><span></span><span></span>
      </div>
      <ul class="nav-links">
        <li><a href="#">Home</a></li>
        <li><a href="#">About</a></li>
        <li><a href="#">Services</a></li>
        <li><a href="#">Blog</a></li>
        <li><a href="#">Contact</a></li>
      </ul>
    </div>
  </nav>
  <main style="padding:30px">
    <h1>Responsive Navigation</h1>
    <p>On mobile: click the ☰ hamburger icon. On desktop (768px+): links show inline.</p>
  </main>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/responsive-step6.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Nav</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; }
    nav { background: #2c3e50; padding: 0 20px; }
    .nav-container { display: flex; justify-content: space-between; align-items: center; height: 60px; }
    .logo { color: white; font-size: 1.3rem; font-weight: bold; }
    .nav-toggle { display: flex; flex-direction: column; gap: 5px; cursor: pointer; }
    .nav-toggle span { display: block; width: 24px; height: 2px; background: white; }
    .nav-links { display: none; flex-direction: column; list-style: none; padding: 10px 0; }
    .nav-links.open { display: flex; }
    .nav-links a { color: #bdc3c7; text-decoration: none; padding: 10px 0; display: block; }
    @media (min-width: 768px) {
      .nav-toggle { display: none; }
      .nav-links { display: flex !important; flex-direction: row; gap: 30px; padding: 0; align-items: center; }
    }
  </style>
</head>
<body>
  <nav>
    <div class="nav-container">
      <div class="logo">🌐 Brand</div>
      <div class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')">
        <span></span><span></span><span></span>
      </div>
      <ul class="nav-links">
        <li><a href="#">Home</a></li>
        <li><a href="#">About</a></li>
        <li><a href="#">Services</a></li>
        <li><a href="#">Contact</a></li>
      </ul>
    </div>
  </nav>
  <main style="padding:30px"><h1>Responsive Navigation</h1></main>
</body>
</html>
EOF
```

> 💡 **The hamburger pattern:** Mobile shows a toggle button; desktop shows links inline. `display: none` hides links on mobile, `display: flex` shows them on desktop. One JavaScript toggle class handles the mobile open/close state.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/responsive-step6.html', 'utf8');
console.log(html.includes('nav-toggle') ? '✓ Hamburger toggle found' : '✗ Missing');
console.log(html.includes('min-width: 768px') || html.includes('min-width:768px') ? '✓ Desktop breakpoint found' : '✗ Missing');
"
✓ Hamburger toggle found
✓ Desktop breakpoint found
```

---

### Step 7: CSS Custom Properties for Responsive Theming

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive CSS Variables</title>
  <style>
    :root {
      /* Mobile values */
      --spacing-sm: 8px;
      --spacing-md: 16px;
      --spacing-lg: 24px;
      --font-size-base: 1rem;
      --font-size-h1: clamp(1.5rem, 5vw, 2.5rem);
      --container-padding: 16px;
      --columns: 1;
    }
    @media (min-width: 768px) {
      :root {
        --spacing-sm: 12px;
        --spacing-md: 24px;
        --spacing-lg: 40px;
        --container-padding: 40px;
        --columns: 2;
      }
    }
    @media (min-width: 1024px) {
      :root {
        --spacing-lg: 60px;
        --container-padding: 80px;
        --columns: 3;
      }
    }
    * { box-sizing: border-box; }
    body { font-family: sans-serif; margin: 0; padding: var(--container-padding); }
    h1 { font-size: var(--font-size-h1); margin-bottom: var(--spacing-md); }
    .grid { display: grid; grid-template-columns: repeat(var(--columns), 1fr); gap: var(--spacing-md); }
    .card { background: #f8f9fa; border-radius: 8px; padding: var(--spacing-md); }
  </style>
</head>
<body>
  <h1>CSS Variables + Media Queries</h1>
  <p style="margin-bottom: var(--spacing-lg)">CSS custom properties update in media queries — all components using those variables update automatically.</p>
  <div class="grid">
    <div class="card"><h3>Card 1</h3><p>Spacing adapts via --spacing-md variable.</p></div>
    <div class="card"><h3>Card 2</h3><p>Columns controlled by --columns variable.</p></div>
    <div class="card"><h3>Card 3</h3><p>One source of truth for responsive design.</p></div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/responsive-step7.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive CSS Variables</title>
  <style>
    :root { --spacing-md: 16px; --container-padding: 16px; --font-h1: clamp(1.5rem, 5vw, 2.5rem); }
    @media (min-width: 768px) { :root { --spacing-md: 24px; --container-padding: 40px; } }
    @media (min-width: 1024px) { :root { --container-padding: 80px; } }
    * { box-sizing: border-box; }
    body { font-family: sans-serif; margin: 0; padding: var(--container-padding); }
    h1 { font-size: var(--font-h1); margin-bottom: var(--spacing-md); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: var(--spacing-md); }
    .card { background: #f8f9fa; border-radius: 8px; padding: var(--spacing-md); }
  </style>
</head>
<body>
  <h1>CSS Variables for Responsive Design</h1>
  <div class="grid">
    <div class="card"><h3>Card 1</h3><p>Spacing adapts automatically.</p></div>
    <div class="card"><h3>Card 2</h3><p>One variable change, all components update.</p></div>
    <div class="card"><h3>Card 3</h3><p>DRY responsive design.</p></div>
  </div>
</body>
</html>
EOF
```

> 💡 **CSS variables in media queries** — update the variable, everything using it updates automatically. This is the DRY (Don't Repeat Yourself) principle applied to responsive design. Define spacing/typography scales as variables, adjust them at breakpoints.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/responsive-step7.html', 'utf8');
console.log(html.includes('--') && html.includes('var(') ? '✓ CSS variables found' : '✗ Missing');
console.log(html.includes('@media') ? '✓ Media queries with variables' : '✗ Missing media queries');
"
✓ CSS variables found
✓ Media queries with variables
```

---

### Step 8: Capstone — Fully Responsive Landing Page

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Landing Page</title>
  <style>
    :root {
      --primary: #667eea;
      --secondary: #764ba2;
      --text: #2d3436;
      --light: #f8f9fa;
      --pad: clamp(16px, 4vw, 60px);
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; color: var(--text); }
    /* NAV */
    nav { position: sticky; top: 0; background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); z-index: 100; }
    .nav-inner { max-width: 1200px; margin: 0 auto; padding: 0 var(--pad); display: flex; justify-content: space-between; align-items: center; height: 64px; }
    .logo { font-weight: 800; font-size: 1.3rem; background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .nav-links { display: none; list-style: none; gap: 28px; }
    @media (min-width: 768px) { .nav-links { display: flex; } }
    .nav-links a { text-decoration: none; color: #636e72; font-size: 0.95rem; }
    .nav-links a:hover { color: var(--primary); }
    .btn { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border: none; padding: 10px 24px; border-radius: 24px; cursor: pointer; font-size: 0.95rem; font-weight: 600; }
    /* HERO */
    .hero { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 80px var(--pad); text-align: center; }
    .hero h1 { font-size: clamp(2rem, 6vw, 4rem); font-weight: 900; margin-bottom: 20px; line-height: 1.1; }
    .hero p { font-size: clamp(1rem, 2vw, 1.25rem); opacity: 0.9; max-width: 600px; margin: 0 auto 32px; }
    .hero-btns { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
    .btn-outline { background: transparent; border: 2px solid white; color: white; padding: 10px 24px; border-radius: 24px; cursor: pointer; font-size: 0.95rem; font-weight: 600; }
    /* FEATURES */
    section { padding: 80px var(--pad); }
    .section-inner { max-width: 1200px; margin: 0 auto; }
    .section-title { text-align: center; font-size: clamp(1.5rem, 4vw, 2.5rem); margin-bottom: 48px; }
    .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; }
    .feature-card { background: white; border-radius: 16px; padding: 32px 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; }
    .feature-icon { font-size: 3rem; margin-bottom: 16px; }
    .feature-card h3 { margin-bottom: 12px; font-size: 1.1rem; }
    .feature-card p { color: #636e72; font-size: 0.9rem; line-height: 1.6; }
    /* STATS */
    .stats-section { background: var(--light); }
    .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 24px; text-align: center; }
    .stat-value { font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 900; background: linear-gradient(135deg, var(--primary), var(--secondary)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .stat-label { color: #636e72; margin-top: 8px; }
    /* FOOTER */
    footer { background: #2d3436; color: #b2bec3; padding: 40px var(--pad); text-align: center; }
  </style>
</head>
<body>
  <nav>
    <div class="nav-inner">
      <div class="logo">✨ StartupName</div>
      <ul class="nav-links">
        <li><a href="#">Features</a></li>
        <li><a href="#">Pricing</a></li>
        <li><a href="#">About</a></li>
      </ul>
      <button class="btn">Get Started</button>
    </div>
  </nav>
  <section class="hero">
    <h1>Build Something<br>Amazing Today</h1>
    <p>The complete platform for modern web development. Responsive by default, fast by design.</p>
    <div class="hero-btns">
      <button class="btn" style="background:white;color:var(--primary)">Start Free Trial</button>
      <button class="btn-outline">Watch Demo</button>
    </div>
  </section>
  <section>
    <div class="section-inner">
      <h2 class="section-title">Everything You Need</h2>
      <div class="features">
        <div class="feature-card"><div class="feature-icon">⚡</div><h3>Lightning Fast</h3><p>Optimized for performance with lazy loading and code splitting.</p></div>
        <div class="feature-card"><div class="feature-icon">📱</div><h3>Mobile First</h3><p>Responsive design that works beautifully on every device.</p></div>
        <div class="feature-card"><div class="feature-icon">🔐</div><h3>Secure by Default</h3><p>Enterprise-grade security with automatic SSL and DDoS protection.</p></div>
        <div class="feature-card"><div class="feature-icon">🎨</div><h3>Beautiful UI</h3><p>Stunning components that delight users and build trust.</p></div>
      </div>
    </div>
  </section>
  <section class="stats-section">
    <div class="section-inner">
      <div class="stats">
        <div><div class="stat-value">50K+</div><div class="stat-label">Active Users</div></div>
        <div><div class="stat-value">99.9%</div><div class="stat-label">Uptime SLA</div></div>
        <div><div class="stat-value">180+</div><div class="stat-label">Countries</div></div>
        <div><div class="stat-value">4.9★</div><div class="stat-label">User Rating</div></div>
      </div>
    </div>
  </section>
  <footer>© 2024 StartupName. Built with CSS Grid, Flexbox &amp; ❤️</footer>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/responsive.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Responsive Landing Page</title>
  <style>
    :root { --primary: #667eea; --secondary: #764ba2; --pad: clamp(16px, 4vw, 60px); }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; }
    nav { background: white; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .nav-inner { max-width: 1200px; margin: 0 auto; padding: 0 var(--pad); display: flex; justify-content: space-between; align-items: center; height: 64px; }
    .logo { font-weight: 800; font-size: 1.3rem; color: var(--primary); }
    .nav-links { display: none; list-style: none; gap: 28px; }
    @media (min-width: 768px) { .nav-links { display: flex; } }
    .nav-links a { text-decoration: none; color: #636e72; }
    .btn { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; border: none; padding: 10px 24px; border-radius: 24px; cursor: pointer; font-weight: 600; }
    .hero { background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 80px var(--pad); text-align: center; }
    .hero h1 { font-size: clamp(2rem, 6vw, 4rem); margin-bottom: 20px; }
    .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 24px; padding: 60px var(--pad); max-width: 1200px; margin: 0 auto; }
    .feature-card { background: white; border-radius: 16px; padding: 32px 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; }
    footer { background: #2d3436; color: #b2bec3; padding: 40px var(--pad); text-align: center; }
  </style>
</head>
<body>
  <nav><div class="nav-inner"><div class="logo">✨ StartupName</div><ul class="nav-links"><li><a href="#">Features</a></li><li><a href="#">Pricing</a></li></ul><button class="btn">Get Started</button></div></nav>
  <section class="hero"><h1>Build Something Amazing</h1><p>Responsive by default, fast by design.</p></section>
  <div class="features">
    <div class="feature-card"><div style="font-size:3rem">⚡</div><h3>Fast</h3></div>
    <div class="feature-card"><div style="font-size:3rem">📱</div><h3>Mobile</h3></div>
    <div class="feature-card"><div style="font-size:3rem">🔐</div><h3>Secure</h3></div>
    <div class="feature-card"><div style="font-size:3rem">🎨</div><h3>Beautiful</h3></div>
  </div>
  <footer>© 2024 StartupName</footer>
</body>
</html>
EOF
```

> 💡 **Capstone recap:** This landing page applies every technique from this lab: viewport meta, mobile-first CSS, clamp() typography, CSS variables, responsive grid (auto-fit), and a responsive navigation. The `--pad` variable alone eliminates 6+ repeated media query blocks.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/responsive.html', 'utf8');
console.log(html.includes('viewport') ? '✓ Viewport meta' : '✗ Missing viewport');
console.log(html.includes('clamp(') ? '✓ clamp() typography' : '✗ Missing clamp');
console.log(html.includes('auto-fit') ? '✓ Responsive grid' : '✗ Missing auto-fit');
console.log(html.includes('@media') ? '✓ Media queries' : '✗ Missing media queries');
"
✓ Viewport meta
✓ clamp() typography
✓ Responsive grid
✓ Media queries
```

---

## Verification

```bash
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const files = ['responsive-step1.html','responsive-step2.html','responsive-step3.html','responsive-step4.html','responsive-step5.html','responsive-step6.html','responsive-step7.html','responsive.html'];
files.forEach(f => {
  try { fs.accessSync('/workspace/' + f); console.log('✓ ' + f); }
  catch(e) { console.log('✗ ' + f + ' missing'); }
});
"
```

## Summary

| Technique | CSS | Purpose |
|-----------|-----|---------|
| Viewport meta | `<meta name="viewport">` | Enable proper mobile scaling |
| Mobile-first | `@media (min-width: ...)` | Progressive enhancement |
| Fluid type | `clamp(min, vw, max)` | Smooth scaling without jumps |
| Responsive images | `srcset`, `sizes`, `picture` | Right image for right screen |
| Responsive grid | `repeat(auto-fit, minmax())` | No media queries needed |
| CSS variables | `--var` in `@media` | Centralized responsive values |

## Further Reading
- [MDN Responsive Design Guide](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [web.dev Responsive Design](https://web.dev/learn/design/)
- [The Sizes Attribute](https://ericportis.com/posts/2014/srcset-sizes/)
