# Lab 13: HTML Accessibility & ARIA

## Objective
Build inclusive web experiences that work for everyone — including users of screen readers, keyboard navigation, and assistive technologies — using semantic HTML, ARIA attributes, and WCAG best practices.

## Background
Over 1 billion people worldwide have some form of disability. Accessibility (a11y) ensures your website works for screen reader users, keyboard-only users, people with motor impairments, and those with low vision. Beyond ethics, accessibility is often legally required (ADA, WCAG 2.1 AA).

## Time
35 minutes

## Prerequisites
- Lab 07: CSS Flexbox
- Lab 09: Responsive Design
- Lab 11: Forms

## Tools
```bash
docker run --rm -it -v /tmp:/workspace zchencow/innozverse-htmlcss:latest bash
```

---

## Lab Instructions

### Step 1: Semantic HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Semantic HTML</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: sans-serif; }
    header { background: #2c3e50; color: white; padding: 16px 24px; }
    nav { background: #34495e; padding: 8px 24px; }
    nav ul { list-style: none; display: flex; gap: 20px; }
    nav a { color: #ecf0f1; text-decoration: none; }
    main { padding: 24px; max-width: 900px; margin: 0 auto; }
    article { margin-bottom: 32px; border-bottom: 1px solid #eee; padding-bottom: 24px; }
    aside { background: #f8f9fa; padding: 16px; border-radius: 8px; margin-top: 24px; }
    footer { background: #2c3e50; color: white; padding: 16px 24px; text-align: center; }
  </style>
</head>
<body>
  <!-- SEMANTIC: each element conveys meaning, not just appearance -->
  <header>
    <h1>My Blog</h1>
    <p>Thoughts on web development</p>
  </header>
  <nav aria-label="Main navigation">
    <ul>
      <li><a href="#">Home</a></li>
      <li><a href="#" aria-current="page">Articles</a></li>
      <li><a href="#">About</a></li>
      <li><a href="#">Contact</a></li>
    </ul>
  </nav>
  <main>
    <section aria-labelledby="featured-heading">
      <h2 id="featured-heading">Featured Articles</h2>
      <article>
        <header>
          <h3>Understanding CSS Grid</h3>
          <time datetime="2024-01-15">January 15, 2024</time>
          by <address rel="author">Jane Smith</address>
        </header>
        <p>CSS Grid is a powerful two-dimensional layout system...</p>
        <footer>
          <a href="#" aria-label="Read more about Understanding CSS Grid">Read more →</a>
        </footer>
      </article>
      <article>
        <header>
          <h3>Accessibility First Development</h3>
          <time datetime="2024-01-20">January 20, 2024</time>
        </header>
        <p>Building accessible websites benefits everyone...</p>
      </article>
    </section>
    <aside aria-label="Newsletter signup">
      <h3>Subscribe to Newsletter</h3>
      <p>Get weekly tips on web development</p>
    </aside>
  </main>
  <footer>
    <p>© 2024 My Blog. Built with semantic HTML.</p>
  </footer>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/a11y-step1.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Semantic HTML</title>
  <style>
    body { font-family: sans-serif; }
    header, footer { background: #2c3e50; color: white; padding: 16px 24px; }
    nav { background: #34495e; padding: 8px 24px; }
    nav ul { list-style: none; display: flex; gap: 20px; }
    nav a { color: #ecf0f1; text-decoration: none; }
    main { padding: 24px; max-width: 900px; margin: 0 auto; }
    article { margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #eee; }
    aside { background: #f8f9fa; padding: 16px; border-radius: 8px; margin-top: 24px; }
    footer { text-align: center; margin-top: 0; }
  </style>
</head>
<body>
  <header><h1>My Blog</h1></header>
  <nav aria-label="Main navigation">
    <ul>
      <li><a href="#">Home</a></li>
      <li><a href="#" aria-current="page">Articles</a></li>
      <li><a href="#">About</a></li>
    </ul>
  </nav>
  <main>
    <section aria-labelledby="featured-heading">
      <h2 id="featured-heading">Featured Articles</h2>
      <article>
        <h3>Understanding CSS Grid</h3>
        <time datetime="2024-01-15">January 15, 2024</time>
        <p>CSS Grid is a powerful two-dimensional layout system.</p>
        <a href="#" aria-label="Read more about Understanding CSS Grid">Read more →</a>
      </article>
      <article>
        <h3>Accessibility First</h3>
        <p>Building accessible websites benefits everyone.</p>
      </article>
    </section>
    <aside aria-label="Newsletter signup"><h3>Subscribe</h3><p>Weekly web dev tips.</p></aside>
  </main>
  <footer><p>© 2024 My Blog</p></footer>
</body>
</html>
EOF
```

> 💡 **Semantic elements** communicate meaning to screen readers and search engines. `<article>` is self-contained content. `<section>` groups related content with a heading. `<aside>` is tangentially related. `<nav>` marks navigation. `lang="en"` on `<html>` lets screen readers use the right pronunciation.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/a11y-step1.html', 'utf8');
console.log(html.includes('<main>') ? '✓ main landmark found' : '✗ Missing main');
console.log(html.includes('<nav') ? '✓ nav element found' : '✗ Missing nav');
console.log(html.includes('<article>') ? '✓ article elements found' : '✗ Missing article');
console.log(html.includes('<aside') ? '✓ aside element found' : '✗ Missing aside');
"
✓ main landmark found
✓ nav element found
✓ article elements found
✓ aside element found
```

---

### Step 2: ARIA Roles and Labels

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ARIA Roles & Labels</title>
  <style>
    body { font-family: sans-serif; padding: 24px; max-width: 700px; }
    .alert { background: #fff3cd; border: 1px solid #f39c12; border-radius: 8px; padding: 16px; margin-bottom: 16px; display: flex; gap: 12px; align-items: flex-start; }
    .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; margin: 4px; }
    .btn-primary { background: #667eea; color: white; }
    .btn-icon { background: #667eea; color: white; width: 40px; height: 40px; border-radius: 50%; border: none; cursor: pointer; font-size: 1.2rem; }
    .progress { height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; margin: 16px 0; }
    .progress-fill { height: 100%; background: #667eea; width: 65%; border-radius: 4px; }
    .tab-list { display: flex; gap: 4px; border-bottom: 2px solid #e9ecef; margin-bottom: 16px; }
    .tab { padding: 10px 20px; border: none; background: none; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -2px; }
    .tab[aria-selected="true"] { border-bottom-color: #667eea; color: #667eea; font-weight: 600; }
    .tab-panel { padding: 16px; }
  </style>
</head>
<body>
  <h2>ARIA Attributes in Practice</h2>

  <!-- Alert with role -->
  <div role="alert" aria-live="polite" class="alert">
    <span aria-hidden="true">⚠️</span>
    <div>
      <strong>Warning:</strong> Your session expires in 5 minutes.
      <a href="#" aria-label="Extend session by 30 minutes">Extend session</a>
    </div>
  </div>

  <!-- Button with descriptive label -->
  <button class="btn-icon" aria-label="Add to favorites">★</button>
  <button class="btn-icon" aria-label="Share this article">⤴</button>
  <button class="btn-icon" aria-label="Download PDF" aria-describedby="download-hint">⬇</button>
  <div id="download-hint" style="color:#636e72;font-size:0.8rem;margin:8px 0">Downloads the article as a PDF file</div>

  <!-- Progress bar -->
  <div role="progressbar" aria-valuenow="65" aria-valuemin="0" aria-valuemax="100" aria-label="Upload progress: 65%">
    <div class="progress"><div class="progress-fill"></div></div>
    <p style="font-size:0.85rem;color:#636e72">65% uploaded</p>
  </div>

  <!-- Expandable section -->
  <button class="btn btn-primary" aria-expanded="false" aria-controls="panel1" id="btn1"
    onclick="const p=document.getElementById('panel1');const e=this.getAttribute('aria-expanded')==='true';this.setAttribute('aria-expanded',!e);p.hidden=e">
    Toggle Details
  </button>
  <div id="panel1" hidden aria-labelledby="btn1" style="background:#f8f9fa;padding:16px;border-radius:8px;margin-top:8px">
    <p>This panel is hidden by default. When expanded, screen readers announce its content automatically.</p>
  </div>

  <!-- Tabs -->
  <div style="margin-top:24px">
    <div role="tablist" aria-label="Content sections" class="tab-list">
      <button role="tab" aria-selected="true" aria-controls="tab-html" id="tab-btn-html" class="tab">HTML</button>
      <button role="tab" aria-selected="false" aria-controls="tab-css" id="tab-btn-css" class="tab">CSS</button>
      <button role="tab" aria-selected="false" aria-controls="tab-js" id="tab-btn-js" class="tab">JavaScript</button>
    </div>
    <div role="tabpanel" id="tab-html" aria-labelledby="tab-btn-html" class="tab-panel">
      <p>HTML provides the structure and semantic meaning of web content.</p>
    </div>
    <div role="tabpanel" id="tab-css" aria-labelledby="tab-btn-css" class="tab-panel" hidden>
      <p>CSS controls presentation, layout, and visual design.</p>
    </div>
    <div role="tabpanel" id="tab-js" aria-labelledby="tab-btn-js" class="tab-panel" hidden>
      <p>JavaScript adds interactivity and dynamic behavior.</p>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/a11y-step2.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ARIA Roles & Labels</title>
  <style>
    body { font-family: sans-serif; padding: 24px; max-width: 700px; }
    .alert { background: #fff3cd; border: 1px solid #f39c12; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    .btn-icon { background: #667eea; color: white; width: 40px; height: 40px; border-radius: 50%; border: none; cursor: pointer; font-size: 1.2rem; margin: 4px; }
    .progress { height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; margin: 16px 0; }
    .progress-fill { height: 100%; background: #667eea; width: 65%; }
  </style>
</head>
<body>
  <div role="alert" aria-live="polite" class="alert">
    <span aria-hidden="true">⚠️</span>
    <strong>Warning:</strong> Session expires in 5 minutes.
    <a href="#" aria-label="Extend session by 30 minutes">Extend session</a>
  </div>
  <button class="btn-icon" aria-label="Add to favorites">★</button>
  <button class="btn-icon" aria-label="Share article">⤴</button>
  <button class="btn-icon" aria-label="Download PDF" aria-describedby="dl-hint">⬇</button>
  <div id="dl-hint" style="color:#636e72;font-size:0.8rem;margin:8px 0">Downloads as PDF</div>
  <div role="progressbar" aria-valuenow="65" aria-valuemin="0" aria-valuemax="100" aria-label="Upload: 65%">
    <div class="progress"><div class="progress-fill"></div></div>
    <p style="font-size:0.85rem;color:#636e72">65% uploaded</p>
  </div>
</body>
</html>
EOF
```

> 💡 **ARIA rules of thumb:** 1) Use semantic HTML first — `<button>` not `<div role="button">`. 2) `aria-label` overrides visible text for screen readers. 3) `aria-describedby` adds supplementary description. 4) `aria-live="polite"` announces dynamic updates without interrupting. 5) `aria-hidden="true"` hides decorative elements.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/a11y-step2.html', 'utf8');
console.log(html.includes('role=\"alert\"') ? '✓ alert role found' : '✗ Missing role=alert');
console.log(html.includes('aria-label') ? '✓ aria-label found' : '✗ Missing aria-label');
console.log(html.includes('aria-live') ? '✓ aria-live found' : '✗ Missing aria-live');
console.log(html.includes('aria-hidden') ? '✓ aria-hidden found' : '✗ Missing aria-hidden');
"
✓ alert role found
✓ aria-label found
✓ aria-live found
✓ aria-hidden found
```

---

### Step 3: Keyboard Navigation & tabindex

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Keyboard Navigation</title>
  <style>
    body { font-family: sans-serif; padding: 24px; }
    /* Visible focus styles — never remove outline without replacement! */
    :focus-visible {
      outline: 3px solid #667eea;
      outline-offset: 2px;
      border-radius: 4px;
    }
    .btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; }
    .card { border: 2px solid #e9ecef; border-radius: 8px; padding: 16px; margin: 8px; cursor: pointer; transition: border-color 0.2s; }
    .card:focus { border-color: #667eea; }
    .card:hover, .card:focus { border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.15); }
    /* Interactive div needs tabindex="0" to be keyboard focusable */
    .custom-control {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      background: #f8f9fa;
      border: 2px solid #e9ecef;
      border-radius: 6px;
      cursor: pointer;
      margin: 4px;
    }
    .custom-control:focus { border-color: #667eea; outline: none; }
    /* Roving tabindex pattern for arrow-key navigation */
    [role="radiogroup"] { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
    [role="radio"] { padding: 10px 20px; border: 2px solid #ddd; border-radius: 6px; cursor: pointer; }
    [role="radio"][aria-checked="true"] { border-color: #667eea; background: #eef; }
    [role="radio"]:focus { outline: 3px solid #667eea; }
    .focus-trap-demo { border: 2px dashed #ddd; border-radius: 8px; padding: 20px; margin-top: 20px; }
  </style>
</head>
<body>
  <h2>Keyboard Navigation</h2>
  <p>Tab through all elements below. Each should be visibly focused.</p>

  <!-- Native interactive elements: naturally keyboard-focusable -->
  <button class="btn">Button (naturally focusable)</button>
  <a href="#" style="margin:8px;display:inline-block">Link (naturally focusable)</a>

  <!-- tabindex="0": adds element to tab order -->
  <div class="card" tabindex="0" role="article" aria-label="Clickable card — press Enter to open">
    <h3>Focusable Card</h3>
    <p>tabindex="0" makes this div keyboard focusable. Screen readers will announce it as it's focused.</p>
  </div>

  <!-- tabindex="-1": focusable programmatically, not in tab order -->
  <div id="error-msg" tabindex="-1" style="background:#f8d7da;padding:12px;border-radius:6px;margin:12px 0" aria-live="polite">
    Error message (focusable via JS, not in tab order)
  </div>
  <button class="btn" onclick="document.getElementById('error-msg').focus()">Focus Error Message</button>

  <!-- Custom control with keyboard interaction -->
  <h3 style="margin-top:20px">Custom Controls</h3>
  <div class="custom-control" tabindex="0" role="checkbox" aria-checked="false"
    onclick="this.setAttribute('aria-checked', this.getAttribute('aria-checked')!=='true')"
    onkeydown="if(event.key===' '||event.key==='Enter'){event.preventDefault();this.click()}">
    <span aria-hidden="true">☐</span> Custom Checkbox (Space/Enter to toggle)
  </div>

  <!-- Arrow key navigation with roving tabindex -->
  <h3 style="margin-top:20px">Roving tabindex Radio Group</h3>
  <div role="radiogroup" aria-label="Notification frequency" id="radio-group">
    <div role="radio" aria-checked="true"  tabindex="0"  class="">Immediately</div>
    <div role="radio" aria-checked="false" tabindex="-1">Daily</div>
    <div role="radio" aria-checked="false" tabindex="-1">Weekly</div>
    <div role="radio" aria-checked="false" tabindex="-1">Never</div>
  </div>

  <script>
    // Arrow key navigation for radio group
    const radios = document.querySelectorAll('[role=radio]');
    radios.forEach((radio, i) => {
      radio.addEventListener('keydown', e => {
        let next = i;
        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = (i + 1) % radios.length;
        if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = (i - 1 + radios.length) % radios.length;
        if (next !== i) {
          radios[i].setAttribute('tabindex', '-1');
          radios[i].setAttribute('aria-checked', 'false');
          radios[next].setAttribute('tabindex', '0');
          radios[next].setAttribute('aria-checked', 'true');
          radios[next].focus();
          e.preventDefault();
        }
      });
    });
  </script>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/a11y-step3.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Keyboard Navigation</title>
  <style>
    body { font-family: sans-serif; padding: 24px; }
    :focus-visible { outline: 3px solid #667eea; outline-offset: 2px; border-radius: 4px; }
    .btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; }
    .card { border: 2px solid #e9ecef; border-radius: 8px; padding: 16px; margin: 8px 0; cursor: pointer; }
    .card:focus { border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.15); }
    [role="radio"] { padding: 10px 20px; border: 2px solid #ddd; border-radius: 6px; cursor: pointer; display: inline-block; margin: 4px; }
    [role="radio"][aria-checked="true"] { border-color: #667eea; background: rgba(102,126,234,0.1); }
  </style>
</head>
<body>
  <h2>Keyboard Navigation</h2>
  <button class="btn">Native Button (Tab-focusable)</button>
  <a href="#" style="display:inline-block;margin:8px">Native Link</a>
  <div class="card" tabindex="0" role="article" aria-label="Focusable card">
    <h3>tabindex="0"</h3>
    <p>Makes non-interactive elements keyboard-focusable.</p>
  </div>
  <div id="err" tabindex="-1" style="background:#f8d7da;padding:12px;border-radius:6px;margin:12px 0">
    tabindex="-1": focusable via JS only, not in tab order
  </div>
  <button class="btn" onclick="document.getElementById('err').focus()">Focus Error Via JS</button>
  <h3 style="margin-top:20px">Radio Group</h3>
  <div role="radiogroup" aria-label="Frequency" id="rg">
    <div role="radio" aria-checked="true"  tabindex="0">Daily</div>
    <div role="radio" aria-checked="false" tabindex="-1">Weekly</div>
    <div role="radio" aria-checked="false" tabindex="-1">Monthly</div>
  </div>
  <script>
    const radios = document.querySelectorAll('#rg [role=radio]');
    radios.forEach((r, i) => r.addEventListener('keydown', e => {
      let n = i;
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') n = (i+1) % radios.length;
      if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   n = (i-1+radios.length) % radios.length;
      if (n !== i) { radios[i].setAttribute('tabindex','-1'); radios[i].setAttribute('aria-checked','false'); radios[n].setAttribute('tabindex','0'); radios[n].setAttribute('aria-checked','true'); radios[n].focus(); e.preventDefault(); }
    }));
  </script>
</body>
</html>
EOF
```

> 💡 **tabindex rules:** `tabindex="0"` adds to natural tab order. `tabindex="-1"` allows programmatic focus (`.focus()`) without being in the tab order — perfect for error messages and modals. `tabindex="1"` and above disrupts natural tab order — avoid it. Use **roving tabindex** for widget navigation (arrow keys inside, Tab out).

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/a11y-step3.html', 'utf8');
console.log(html.includes('tabindex=\"0\"') ? '✓ tabindex=0 found' : '✗ Missing tabindex');
console.log(html.includes('tabindex=\"-1\"') ? '✓ tabindex=-1 found' : '✗ Missing tabindex=-1');
console.log(html.includes(':focus-visible') ? '✓ focus-visible styles' : '✗ Missing focus styles');
"
✓ tabindex=0 found
✓ tabindex=-1 found
✓ focus-visible styles
```

---

### Step 4: Skip Links & Focus Indicators

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Skip Links & Focus</title>
  <style>
    * { box-sizing: border-box; }
    /* Skip link — visually hidden until focused */
    .skip-link {
      position: absolute;
      top: -100%;
      left: 8px;
      background: #667eea;
      color: white;
      padding: 10px 20px;
      border-radius: 0 0 8px 8px;
      font-weight: 600;
      text-decoration: none;
      z-index: 9999;
      transition: top 0.2s ease;
    }
    .skip-link:focus { top: 0; }
    /* Custom focus indicators — replace removed outline */
    :focus { outline: none; }
    :focus-visible {
      outline: 3px solid #667eea;
      outline-offset: 3px;
      border-radius: 4px;
    }
    /* High-contrast focus for dark backgrounds */
    .dark-bg:focus-visible { outline-color: #ffd700; }
    /* Focus ring style options */
    .focus-ring-1:focus-visible { box-shadow: 0 0 0 3px white, 0 0 0 5px #667eea; outline: none; }
    .focus-ring-2:focus-visible { box-shadow: inset 0 0 0 2px #667eea; outline: none; }
    body { font-family: sans-serif; }
    header { background: #2c3e50; color: white; padding: 16px 24px; }
    nav { padding: 8px 24px; background: #34495e; }
    nav a { color: white; text-decoration: none; margin-right: 16px; }
    main { padding: 24px; max-width: 800px; margin: 0 auto; }
    .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.95rem; margin: 4px; }
    .btn-1 { background: #667eea; color: white; }
    .btn-2 { background: #2c3e50; color: white; }
  </style>
</head>
<body>
  <!-- Skip link: first in DOM so keyboard users can skip nav -->
  <a href="#main-content" class="skip-link">Skip to main content</a>

  <header>
    <h1>Website with Skip Link</h1>
  </header>
  <nav>
    <a href="#">Home</a>
    <a href="#">Products</a>
    <a href="#">Services</a>
    <a href="#">About</a>
    <a href="#">Contact</a>
  </nav>
  <main id="main-content" tabindex="-1">
    <h2>Main Content Area</h2>
    <p>Press Tab from the page start to see the skip link appear. Without it, keyboard users must Tab through every nav link to reach the content.</p>

    <h3 style="margin-top:20px">Focus Indicator Styles</h3>
    <button class="btn btn-1 focus-ring-1">Double ring focus</button>
    <button class="btn btn-2 dark-bg focus-ring-2">Inset ring focus</button>
    <p style="margin-top:12px;font-size:0.85rem;color:#636e72">Tab to the buttons to see different focus indicator styles. Never use <code>outline: none</code> without a replacement!</p>
  </main>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/a11y-step4.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Skip Links & Focus</title>
  <style>
    * { box-sizing: border-box; }
    .skip-link { position: absolute; top: -100%; left: 8px; background: #667eea; color: white; padding: 10px 20px; border-radius: 0 0 8px 8px; font-weight: 600; text-decoration: none; z-index: 9999; }
    .skip-link:focus { top: 0; }
    :focus-visible { outline: 3px solid #667eea; outline-offset: 3px; border-radius: 4px; }
    body { font-family: sans-serif; }
    header { background: #2c3e50; color: white; padding: 16px 24px; }
    nav { padding: 8px 24px; background: #34495e; }
    nav a { color: white; text-decoration: none; margin-right: 16px; }
    main { padding: 24px; }
    .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.95rem; margin: 4px; }
  </style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <header><h1>Website</h1></header>
  <nav><a href="#">Home</a><a href="#">Products</a><a href="#">About</a><a href="#">Contact</a></nav>
  <main id="main-content" tabindex="-1">
    <h2>Main Content</h2>
    <p>Tab from the page start to reveal the skip link. It lets keyboard users bypass repeated navigation.</p>
    <button class="btn" style="background:#667eea;color:white">Tab to me</button>
    <button class="btn" style="background:#2c3e50;color:white">And me too</button>
  </main>
</body>
</html>
EOF
```

> 💡 **Skip links** are the #1 keyboard accessibility feature. Place them as the first element in `<body>`. They should be visually hidden until focused (using a negative `top` value, not `display:none` — `display:none` removes from tab order). The target (`#main-content`) should have `tabindex="-1"` so browsers send focus there.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/a11y-step4.html', 'utf8');
console.log(html.includes('skip-link') ? '✓ Skip link found' : '✗ Missing skip link');
console.log(html.includes(':focus-visible') ? '✓ focus-visible styles' : '✗ Missing');
console.log(html.includes('Skip to main') ? '✓ Skip link text found' : '✗ Missing skip text');
"
✓ Skip link found
✓ focus-visible styles
✓ Skip link text found
```

---

### Step 5: Color Contrast (WCAG AA)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Color Contrast</title>
  <style>
    body { font-family: sans-serif; padding: 24px; max-width: 700px; }
    .swatch { padding: 20px; border-radius: 8px; margin-bottom: 16px; }
    .ratio { font-size: 0.75rem; font-weight: bold; margin-bottom: 4px; display: inline-block; }
    .pass { color: #155724; background: #d4edda; padding: 2px 8px; border-radius: 4px; }
    .fail { color: #721c24; background: #f8d7da; padding: 2px 8px; border-radius: 4px; }
    .aa { color: #0c5460; background: #d1ecf1; padding: 2px 8px; border-radius: 4px; }
    h3 { margin-bottom: 4px; }
  </style>
</head>
<body>
  <h2>WCAG Color Contrast Requirements</h2>
  <p style="margin-bottom:20px">WCAG AA requires 4.5:1 for normal text, 3:1 for large text (18px+ or 14px bold). WCAG AAA requires 7:1.</p>

  <!-- FAIL examples -->
  <h3>❌ Failing Combinations</h3>
  <div class="swatch" style="background:#ffffff;color:#aaaaaa">
    <span class="ratio fail">FAIL 2.3:1</span>
    <h3>Light gray on white</h3>
    <p>This gray text (#aaa) on white has only 2.3:1 contrast — far below the 4.5:1 minimum. Many users with low vision cannot read this.</p>
  </div>
  <div class="swatch" style="background:#ff9900;color:#ffffff">
    <span class="ratio fail">FAIL 2.9:1</span>
    <h3>White on orange</h3>
    <p>White text on orange brand colors often fails — check before shipping!</p>
  </div>

  <!-- PASS AA examples -->
  <h3>✅ Passing AA (4.5:1+)</h3>
  <div class="swatch" style="background:#ffffff;color:#595959">
    <span class="ratio aa">AA 7:1</span>
    <h3>Dark gray on white</h3>
    <p>Use #595959 or darker for body text. This has 7:1 contrast — exceeds both AA and AAA for normal text.</p>
  </div>
  <div class="swatch" style="background:#667eea;color:#ffffff">
    <span class="ratio pass">PASS 4.54:1</span>
    <h3>White on brand blue</h3>
    <p>Our primary color #667eea just barely passes AA for normal text. Test your brand colors!</p>
  </div>
  <div class="swatch" style="background:#1a1a2e;color:#e0e0e0">
    <span class="ratio aa">AA 10.5:1</span>
    <h3>Light gray on dark background</h3>
    <p>Dark mode done right — high contrast, easy to read.</p>
  </div>

  <!-- Color not as only indicator -->
  <h3 style="margin-top:20px">❌ Never Use Color Alone</h3>
  <div style="padding:16px;background:#f8f9fa;border-radius:8px">
    <p><span style="color:red">Error</span> (bad — only color distinguishes this)</p>
    <p><span style="color:red">❌ Error:</span> Invalid email address (good — icon + text + color)</p>
    <p><span style="color:green">✅ Success:</span> Form submitted (good — icon + color + text)</p>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/a11y-step5.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Color Contrast</title>
  <style>
    body { font-family: sans-serif; padding: 24px; max-width: 700px; }
    .swatch { padding: 20px; border-radius: 8px; margin-bottom: 16px; }
    .badge { font-size: 0.75rem; font-weight: bold; padding: 2px 8px; border-radius: 4px; display: inline-block; margin-bottom: 8px; }
    .fail { color: #721c24; background: #f8d7da; }
    .pass { color: #155724; background: #d4edda; }
  </style>
</head>
<body>
  <h2>WCAG Color Contrast</h2>
  <p style="margin-bottom:20px">AA requires 4.5:1 for normal text, 3:1 for large text.</p>
  <div class="swatch" style="background:#fff;color:#aaa">
    <span class="badge fail">FAIL 2.3:1</span>
    <p>Light gray on white — unreadable for low vision users.</p>
  </div>
  <div class="swatch" style="background:#fff;color:#595959">
    <span class="badge pass">PASS 7:1</span>
    <p>Dark gray on white — #595959 or darker for body text.</p>
  </div>
  <div class="swatch" style="background:#667eea;color:#fff">
    <span class="badge pass">PASS 4.54:1</span>
    <p>White on our brand blue — just passes AA.</p>
  </div>
  <h3 style="margin-top:20px">Never color alone:</h3>
  <p><span style="color:red">❌ Error:</span> Invalid email (icon + color + text — accessible)</p>
  <p><span style="color:green">✅ Success:</span> Form saved (icon + color + text — accessible)</p>
</body>
</html>
EOF
```

> 💡 **WCAG AA contrast ratios:** 4.5:1 for normal text (under 18px), 3:1 for large text (18px+ or 14px bold), 3:1 for UI components (buttons, icons). Use tools like WebAIM Contrast Checker or browser DevTools. Never use color as the only visual differentiator — add icons, patterns, or text.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/a11y-step5.html', 'utf8');
console.log(html.includes('FAIL') ? '✓ Contrast fail examples' : '✗ Missing examples');
console.log(html.includes('PASS') ? '✓ Contrast pass examples' : '✗ Missing examples');
"
✓ Contrast fail examples
✓ Contrast pass examples
```

---

### Step 6: Screen Reader Friendly Forms

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Accessible Forms</title>
  <style>
    body { font-family: sans-serif; padding: 24px; max-width: 550px; }
    .field { margin-bottom: 24px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; }
    .required::after { content: ' *'; color: #e74c3c; }
    input, select, textarea { width: 100%; padding: 10px 14px; border: 2px solid #dfe6e9; border-radius: 6px; font-size: 1rem; box-sizing: border-box; }
    input:focus, select:focus, textarea:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.15); }
    input[aria-invalid="true"] { border-color: #e74c3c; }
    .hint { font-size: 0.8rem; color: #636e72; margin-top: 4px; }
    .error-msg { font-size: 0.8rem; color: #e74c3c; margin-top: 4px; display: flex; gap: 4px; align-items: center; }
    .error-msg::before { content: '⚠'; }
    fieldset { border: 2px solid #dfe6e9; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
    legend { font-weight: 700; padding: 0 8px; }
    .radio-label { display: flex; align-items: center; gap: 8px; margin: 8px 0; cursor: pointer; }
    .btn { background: #667eea; color: white; border: none; padding: 12px 28px; border-radius: 6px; font-size: 1rem; cursor: pointer; }
    .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
  </style>
</head>
<body>
  <h1>Account Registration</h1>
  <!-- Required fields note: announced to screen readers -->
  <p id="required-note"><span aria-hidden="true">*</span> Required fields</p>
  <form aria-describedby="required-note" novalidate>
    <!-- Properly labeled input -->
    <div class="field">
      <label for="fullname" class="required">Full Name</label>
      <input type="text" id="fullname" name="fullname" required
             autocomplete="name"
             aria-required="true"
             aria-describedby="name-hint">
      <div id="name-hint" class="hint">Enter your legal first and last name</div>
    </div>

    <!-- Input with error state -->
    <div class="field">
      <label for="email-bad" class="required">Email Address</label>
      <input type="email" id="email-bad" name="email" required
             value="invalid-email"
             aria-required="true"
             aria-invalid="true"
             aria-describedby="email-error">
      <div id="email-error" class="error-msg" role="alert">Please enter a valid email address</div>
    </div>

    <!-- Fieldset for grouped controls -->
    <fieldset>
      <legend>Preferred Contact Method</legend>
      <label class="radio-label">
        <input type="radio" name="contact" value="email" checked aria-describedby="email-desc">
        Email
        <span id="email-desc" class="sr-only">(fastest response)</span>
      </label>
      <label class="radio-label">
        <input type="radio" name="contact" value="phone"> Phone
      </label>
      <label class="radio-label">
        <input type="radio" name="contact" value="sms"> SMS
      </label>
    </fieldset>

    <!-- Select with clear label -->
    <div class="field">
      <label for="timezone">Time Zone</label>
      <select id="timezone" name="timezone" autocomplete="timezone">
        <option value="">Select your time zone</option>
        <optgroup label="Americas">
          <option value="est">Eastern Time (ET)</option>
          <option value="cst">Central Time (CT)</option>
          <option value="pst">Pacific Time (PT)</option>
        </optgroup>
        <optgroup label="Europe">
          <option value="gmt">Greenwich Mean Time (GMT)</option>
          <option value="cet">Central European Time (CET)</option>
        </optgroup>
      </select>
    </div>

    <button type="submit" class="btn">Create Account</button>
  </form>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/a11y-step6.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Accessible Forms</title>
  <style>
    body { font-family: sans-serif; padding: 24px; max-width: 550px; }
    .field { margin-bottom: 24px; }
    label { display: block; margin-bottom: 6px; font-weight: 600; }
    .required::after { content: ' *'; color: #e74c3c; }
    input, select, textarea { width: 100%; padding: 10px 14px; border: 2px solid #dfe6e9; border-radius: 6px; font-size: 1rem; box-sizing: border-box; }
    input:focus, select:focus { outline: none; border-color: #667eea; box-shadow: 0 0 0 3px rgba(102,126,234,0.15); }
    input[aria-invalid="true"] { border-color: #e74c3c; }
    .hint { font-size: 0.8rem; color: #636e72; margin-top: 4px; }
    .error-msg { font-size: 0.8rem; color: #e74c3c; margin-top: 4px; }
    fieldset { border: 2px solid #dfe6e9; border-radius: 8px; padding: 16px; margin-bottom: 20px; }
    legend { font-weight: 700; padding: 0 8px; }
    .btn { background: #667eea; color: white; border: none; padding: 12px 28px; border-radius: 6px; cursor: pointer; }
    .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0,0,0,0); }
  </style>
</head>
<body>
  <h1>Account Registration</h1>
  <p id="req-note">* Required fields</p>
  <form aria-describedby="req-note">
    <div class="field">
      <label for="name" class="required">Full Name</label>
      <input type="text" id="name" required aria-required="true" aria-describedby="name-hint" autocomplete="name">
      <div id="name-hint" class="hint">Enter your legal first and last name</div>
    </div>
    <div class="field">
      <label for="email" class="required">Email Address</label>
      <input type="email" id="email" required aria-required="true" aria-invalid="true" aria-describedby="email-err" value="bad-email">
      <div id="email-err" class="error-msg" role="alert">⚠ Please enter a valid email</div>
    </div>
    <fieldset>
      <legend>Contact Preference</legend>
      <label><input type="radio" name="contact" value="email" checked> Email</label><br>
      <label><input type="radio" name="contact" value="phone"> Phone</label>
    </fieldset>
    <button type="submit" class="btn">Create Account</button>
  </form>
</body>
</html>
EOF
```

> 💡 **Accessible form checklist:** Every input needs a visible `<label>` connected via `for`/`id`. Error messages use `role="alert"` (announces immediately) or `aria-live="polite"`. `aria-invalid="true"` signals invalid state to screen readers. `aria-describedby` links hints and errors to inputs. `fieldset`+`legend` groups related controls. `autocomplete` enables autofill.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/a11y-step6.html', 'utf8');
console.log(html.includes('aria-required') ? '✓ aria-required found' : '✗ Missing aria-required');
console.log(html.includes('aria-invalid') ? '✓ aria-invalid found' : '✗ Missing aria-invalid');
console.log(html.includes('aria-describedby') ? '✓ aria-describedby found' : '✗ Missing');
console.log(html.includes('<fieldset>') ? '✓ fieldset found' : '✗ Missing fieldset');
"
✓ aria-required found
✓ aria-invalid found
✓ aria-describedby found
✓ fieldset found
```

---

### Step 7: Accessible Modal Dialog

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Accessible Modal</title>
  <style>
    body { font-family: sans-serif; padding: 24px; }
    .btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; }
    /* Modal overlay */
    .modal-overlay {
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.6);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s;
    }
    .modal-overlay[aria-hidden="false"] { opacity: 1; pointer-events: all; }
    .modal {
      background: white;
      border-radius: 12px;
      padding: 24px;
      max-width: 480px;
      width: 90%;
      position: relative;
      transform: translateY(20px);
      transition: transform 0.2s;
    }
    .modal-overlay[aria-hidden="false"] .modal { transform: translateY(0); }
    .modal-close { position: absolute; top: 12px; right: 12px; background: none; border: none; font-size: 1.5rem; cursor: pointer; padding: 4px 8px; border-radius: 4px; }
    .modal-close:focus-visible { outline: 3px solid #667eea; }
    .modal h2 { margin-bottom: 16px; }
    .modal p { color: #636e72; margin-bottom: 20px; }
    .modal-actions { display: flex; gap: 12px; justify-content: flex-end; }
    .btn-cancel { background: transparent; border: 2px solid #dfe6e9; color: #636e72; padding: 10px 20px; border-radius: 6px; cursor: pointer; }
    :focus-visible { outline: 3px solid #667eea; outline-offset: 2px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Accessible Modal Dialog</h1>
  <p>Click the button to open a WCAG-compliant modal with focus trapping and proper ARIA.</p>
  <button class="btn" id="open-modal" onclick="openModal()">Open Dialog</button>

  <!-- Modal: role="dialog", aria-modal="true", aria-labelledby -->
  <div class="modal-overlay" id="modal-overlay" aria-hidden="true" aria-modal="true"
       role="dialog" aria-labelledby="modal-title" aria-describedby="modal-desc">
    <div class="modal">
      <button class="modal-close" aria-label="Close dialog" onclick="closeModal()">✕</button>
      <h2 id="modal-title">Delete Account</h2>
      <p id="modal-desc">Are you sure you want to delete your account? This action cannot be undone and all your data will be permanently removed.</p>
      <div class="modal-actions">
        <button class="btn-cancel" onclick="closeModal()">Cancel</button>
        <button class="btn" style="background:#e74c3c" onclick="closeModal()">Delete Account</button>
      </div>
    </div>
  </div>

  <script>
    const overlay = document.getElementById('modal-overlay');
    const opener = document.getElementById('open-modal');

    // All focusable elements inside the modal
    const getFocusable = () => Array.from(overlay.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ));

    function openModal() {
      overlay.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden'; // prevent scroll
      // Move focus to first element in modal
      setTimeout(() => getFocusable()[0]?.focus(), 50);
      // Trap focus inside modal
      overlay.addEventListener('keydown', trapFocus);
      document.addEventListener('keydown', handleEsc);
    }

    function closeModal() {
      overlay.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
      overlay.removeEventListener('keydown', trapFocus);
      document.removeEventListener('keydown', handleEsc);
      // Return focus to the element that opened the modal
      opener.focus();
    }

    function trapFocus(e) {
      const focusable = getFocusable();
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === first) {
          last.focus(); e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus(); e.preventDefault();
        }
      }
    }

    function handleEsc(e) {
      if (e.key === 'Escape') closeModal();
    }

    // Close on overlay click
    overlay.addEventListener('click', e => { if (e.target === overlay) closeModal(); });
  </script>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/a11y-step7.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Accessible Modal</title>
  <style>
    body { font-family: sans-serif; padding: 24px; }
    .btn { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 6px; cursor: pointer; }
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; opacity: 0; pointer-events: none; transition: opacity 0.2s; }
    .modal-overlay[aria-hidden="false"] { opacity: 1; pointer-events: all; }
    .modal { background: white; border-radius: 12px; padding: 24px; max-width: 480px; width: 90%; position: relative; }
    .modal-close { position: absolute; top: 12px; right: 12px; background: none; border: none; font-size: 1.5rem; cursor: pointer; padding: 4px 8px; }
    :focus-visible { outline: 3px solid #667eea; outline-offset: 2px; border-radius: 4px; }
  </style>
</head>
<body>
  <h1>Accessible Modal</h1>
  <button class="btn" id="open-btn" onclick="openModal()">Open Dialog</button>
  <div class="modal-overlay" id="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby="modal-desc" aria-hidden="true">
    <div class="modal">
      <button class="modal-close" aria-label="Close dialog" onclick="closeModal()">✕</button>
      <h2 id="modal-title">Delete Account?</h2>
      <p id="modal-desc" style="color:#636e72;margin:12px 0">This action cannot be undone.</p>
      <div style="display:flex;gap:12px;justify-content:flex-end">
        <button onclick="closeModal()" style="background:transparent;border:2px solid #ddd;padding:10px 20px;border-radius:6px;cursor:pointer">Cancel</button>
        <button class="btn" style="background:#e74c3c" onclick="closeModal()">Delete</button>
      </div>
    </div>
  </div>
  <script>
    const modal = document.getElementById('modal');
    const opener = document.getElementById('open-btn');
    const getFocusable = () => Array.from(modal.querySelectorAll('button, [href], input, [tabindex]:not([tabindex="-1"])'));
    function openModal() {
      modal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      setTimeout(() => getFocusable()[0]?.focus(), 50);
      modal.addEventListener('keydown', trapFocus);
      document.addEventListener('keydown', handleEsc);
    }
    function closeModal() {
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
      modal.removeEventListener('keydown', trapFocus);
      document.removeEventListener('keydown', handleEsc);
      opener.focus();
    }
    function trapFocus(e) {
      const f = getFocusable(); const first = f[0]; const last = f[f.length-1];
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === first) { last.focus(); e.preventDefault(); }
        else if (!e.shiftKey && document.activeElement === last) { first.focus(); e.preventDefault(); }
      }
    }
    function handleEsc(e) { if (e.key === 'Escape') closeModal(); }
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });
  </script>
</body>
</html>
EOF
```

> 💡 **Accessible modal checklist:** `role="dialog"` + `aria-modal="true"` + `aria-labelledby` pointing to the title. When opened: move focus inside, trap Tab/Shift+Tab, close on Escape. When closed: return focus to the element that opened it. This pattern prevents screen reader users from interacting with content behind the modal.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/a11y-step7.html', 'utf8');
console.log(html.includes('role=\"dialog\"') ? '✓ dialog role found' : '✗ Missing dialog role');
console.log(html.includes('aria-modal') ? '✓ aria-modal found' : '✗ Missing aria-modal');
console.log(html.includes('trapFocus') ? '✓ Focus trap found' : '✗ Missing focus trap');
console.log(html.includes('Escape') ? '✓ Escape key handling' : '✗ Missing Escape');
"
✓ dialog role found
✓ aria-modal found
✓ Focus trap found
✓ Escape key handling
```

---

### Step 8: Capstone — Accessible Product Card with ARIA

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Accessible Product Card</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; padding: 24px; }
    :focus-visible { outline: 3px solid #667eea; outline-offset: 3px; border-radius: 4px; }
    .products { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; max-width: 900px; margin: 0 auto; }
    /* Product card as an article landmark */
    .product-card {
      background: white;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    .product-img { height: 200px; display: flex; align-items: center; justify-content: center; font-size: 5rem; }
    .product-body { padding: 20px; }
    .product-category { font-size: 0.75rem; color: #667eea; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
    .product-name { font-size: 1.15rem; font-weight: 700; color: #2d3436; margin-bottom: 8px; }
    .product-desc { font-size: 0.9rem; color: #636e72; line-height: 1.5; margin-bottom: 16px; }
    /* Star rating: accessible pattern */
    .rating { display: flex; gap: 4px; align-items: center; margin-bottom: 16px; }
    .stars { color: #fdcb6e; }
    .rating-text { font-size: 0.85rem; color: #636e72; margin-left: 4px; }
    /* Price section */
    .price-row { display: flex; justify-content: space-between; align-items: center; }
    .price-group { display: flex; flex-direction: column; }
    .price-original { font-size: 0.85rem; color: #b2bec3; text-decoration: line-through; }
    .price-sale { font-size: 1.4rem; font-weight: 700; color: #e17055; }
    /* Buttons with meaningful labels */
    .btn-cart { background: #667eea; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-size: 0.9rem; font-weight: 600; }
    .btn-cart:hover { background: #5a6fd6; }
    .btn-wishlist { background: white; color: #636e72; border: 2px solid #e9ecef; width: 44px; height: 44px; border-radius: 8px; cursor: pointer; font-size: 1.2rem; display: flex; align-items: center; justify-content: center; }
    .btn-wishlist[aria-pressed="true"] { color: #e74c3c; border-color: #e74c3c; }
    /* Badge for sale/new */
    .badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }
    .badge-sale { background: #ffe0d6; color: #e17055; }
  </style>
</head>
<body>
  <h1 style="text-align:center;margin-bottom:24px">Accessible Product Catalog</h1>
  <div class="products">
    <!-- Each card is an <article> with proper headings and ARIA -->
    <article class="product-card" aria-label="Pro Wireless Headphones, $139.99, 30% off">
      <div class="product-img" style="background:linear-gradient(135deg,#f093fb,#f5576c)" role="img" aria-label="Pro Wireless Headphones product image">🎧</div>
      <div class="product-body">
        <div class="product-category" aria-label="Category: Electronics">Electronics</div>
        <h2 class="product-name">Pro Wireless Headphones</h2>
        <!-- Rating: text-based so screen readers can read it -->
        <div class="rating">
          <span class="stars" aria-hidden="true">★★★★★</span>
          <span class="sr-only" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)">Rated 5 out of 5 stars</span>
          <span class="rating-text">(2,847 reviews)</span>
        </div>
        <p class="product-desc">Premium noise-canceling headphones with 40-hour battery, Hi-Fi audio, and ultra-comfortable design.</p>
        <div class="price-row">
          <div class="price-group">
            <span class="price-original" aria-label="Original price: $199.99">$199.99</span>
            <span class="price-sale" aria-label="Sale price: $139.99">$139.99</span>
          </div>
          <div style="display:flex;gap:8px">
            <button class="btn-wishlist" aria-label="Add Pro Wireless Headphones to wishlist" aria-pressed="false"
              onclick="this.setAttribute('aria-pressed', this.getAttribute('aria-pressed')!=='true'); this.setAttribute('aria-label', this.getAttribute('aria-pressed')==='true' ? 'Remove Pro Wireless Headphones from wishlist' : 'Add Pro Wireless Headphones to wishlist')">♡</button>
            <button class="btn-cart" aria-label="Add Pro Wireless Headphones to cart for $139.99">🛒 Add to Cart</button>
          </div>
        </div>
      </div>
    </article>

    <article class="product-card" aria-label="Mechanical Keyboard, $89.99">
      <div class="product-img" style="background:linear-gradient(135deg,#4facfe,#00f2fe)" role="img" aria-label="Mechanical Keyboard product image">⌨️</div>
      <div class="product-body">
        <div class="product-category">Peripherals</div>
        <h2 class="product-name">Mechanical Keyboard</h2>
        <div class="rating">
          <span class="stars" aria-hidden="true">★★★★☆</span>
          <span class="rating-text">(1,204 reviews)</span>
        </div>
        <p class="product-desc">Tactile mechanical switches, RGB backlight, TKL layout for more desk space.</p>
        <div class="price-row">
          <div class="price-group">
            <span class="price-sale" aria-label="Price: $89.99">$89.99</span>
          </div>
          <div style="display:flex;gap:8px">
            <button class="btn-wishlist" aria-label="Add Mechanical Keyboard to wishlist" aria-pressed="false">♡</button>
            <button class="btn-cart" aria-label="Add Mechanical Keyboard to cart for $89.99">🛒 Add to Cart</button>
          </div>
        </div>
      </div>
    </article>
  </div>

  <script>
    // Make wishlist buttons toggle properly
    document.querySelectorAll('.btn-wishlist').forEach(btn => {
      btn.addEventListener('click', () => {
        const pressed = btn.getAttribute('aria-pressed') === 'true';
        btn.setAttribute('aria-pressed', !pressed);
        btn.textContent = pressed ? '♡' : '♥';
      });
    });
  </script>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/accessibility.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Accessible Product Card</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; background: #f0f2f5; padding: 24px; }
    :focus-visible { outline: 3px solid #667eea; outline-offset: 3px; border-radius: 4px; }
    .products { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; max-width: 900px; margin: 0 auto; }
    .product-card { background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
    .product-img { height: 180px; display: flex; align-items: center; justify-content: center; font-size: 5rem; }
    .product-body { padding: 20px; }
    .product-name { font-size: 1.1rem; font-weight: 700; color: #2d3436; margin-bottom: 8px; }
    .product-desc { font-size: 0.9rem; color: #636e72; margin-bottom: 16px; line-height: 1.5; }
    .price-row { display: flex; justify-content: space-between; align-items: center; }
    .price-sale { font-size: 1.3rem; font-weight: 700; color: #e17055; }
    .btn-cart { background: #667eea; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; }
    .btn-wishlist { background: white; border: 2px solid #e9ecef; width: 44px; height: 44px; border-radius: 8px; cursor: pointer; font-size: 1.2rem; }
    .btn-wishlist[aria-pressed="true"] { color: #e74c3c; border-color: #e74c3c; }
  </style>
</head>
<body>
  <h1 style="text-align:center;margin-bottom:24px">Accessible Product Catalog</h1>
  <div class="products">
    <article class="product-card" aria-label="Pro Wireless Headphones, $139.99">
      <div class="product-img" style="background:linear-gradient(135deg,#f093fb,#f5576c)" role="img" aria-label="Headphones image">🎧</div>
      <div class="product-body">
        <h2 class="product-name">Pro Wireless Headphones</h2>
        <p class="product-desc">Noise-canceling, 40-hour battery, Hi-Fi audio.</p>
        <div class="price-row">
          <span class="price-sale" aria-label="Sale price: $139.99">$139.99</span>
          <div style="display:flex;gap:8px">
            <button class="btn-wishlist" aria-label="Add to wishlist" aria-pressed="false">♡</button>
            <button class="btn-cart" aria-label="Add Pro Headphones to cart">🛒 Add</button>
          </div>
        </div>
      </div>
    </article>
    <article class="product-card" aria-label="Mechanical Keyboard, $89.99">
      <div class="product-img" style="background:linear-gradient(135deg,#4facfe,#00f2fe)" role="img" aria-label="Keyboard image">⌨️</div>
      <div class="product-body">
        <h2 class="product-name">Mechanical Keyboard</h2>
        <p class="product-desc">Tactile switches, RGB backlight, TKL layout.</p>
        <div class="price-row">
          <span class="price-sale" aria-label="Price: $89.99">$89.99</span>
          <div style="display:flex;gap:8px">
            <button class="btn-wishlist" aria-label="Add to wishlist" aria-pressed="false">♡</button>
            <button class="btn-cart" aria-label="Add Keyboard to cart">🛒 Add</button>
          </div>
        </div>
      </div>
    </article>
  </div>
  <script>
    document.querySelectorAll('.btn-wishlist').forEach(btn => {
      btn.addEventListener('click', () => {
        const p = btn.getAttribute('aria-pressed') === 'true';
        btn.setAttribute('aria-pressed', !p);
        btn.textContent = p ? '♡' : '♥';
      });
    });
  </script>
</body>
</html>
EOF
```

> 💡 **Accessible card checklist:** Use `<article>` for self-contained cards. Give each card a descriptive `aria-label` (not just "Card"). Use `role="img"` with `aria-label` on emoji/icon image areas. Star ratings: hide stars from screen readers (`aria-hidden="true"`) and add text equivalent. Toggle buttons use `aria-pressed`. Prices need meaningful `aria-label` (not just "$139").

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/accessibility.html', 'utf8');
console.log(html.includes('<article') ? '✓ article elements found' : '✗ Missing article');
console.log(html.includes('aria-label') ? '✓ aria-label found' : '✗ Missing aria-label');
console.log(html.includes('aria-pressed') ? '✓ aria-pressed toggle' : '✗ Missing aria-pressed');
console.log(html.includes(':focus-visible') ? '✓ Focus styles' : '✗ Missing focus styles');
"
✓ article elements found
✓ aria-label found
✓ aria-pressed toggle
✓ Focus styles
```

---

## Verification

```bash
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const checks = [
  ['a11y-step1.html', '<main>'],
  ['a11y-step2.html', 'aria-label'],
  ['a11y-step3.html', 'tabindex'],
  ['a11y-step4.html', 'skip-link'],
  ['a11y-step5.html', 'PASS'],
  ['a11y-step6.html', 'aria-required'],
  ['a11y-step7.html', 'role=\"dialog\"'],
  ['accessibility.html', '<article'],
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

| Technique | Implementation | Benefit |
|-----------|---------------|---------|
| Semantic HTML | `<main>`, `<nav>`, `<article>` | Screen reader landmarks |
| ARIA labels | `aria-label`, `aria-labelledby` | Descriptive names for UI |
| Keyboard nav | `tabindex`, `:focus-visible` | Full keyboard access |
| Skip links | First link in `<body>` | Bypass repeated navigation |
| Color contrast | 4.5:1 minimum ratio | Low vision accessibility |
| Accessible forms | `label`, `aria-invalid`, `fieldset` | Screen reader form support |
| Modal dialogs | Focus trap + Escape key | ARIA dialog pattern |

## Further Reading
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [MDN ARIA](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA)
- [axe DevTools](https://www.deque.com/axe/) — accessibility testing
