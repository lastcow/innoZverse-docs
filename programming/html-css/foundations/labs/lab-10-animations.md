# Lab 10: CSS Animations & Transitions

## Objective
Create smooth, performant animations and transitions using CSS — from simple hover effects to complex multi-step keyframe animations and 3D transforms.

## Background
CSS animations make interfaces feel alive and responsive. Done well, they guide user attention, provide feedback, and delight users. Done poorly, they cause motion sickness and slow pages. This lab teaches both the technique and the taste.

## Time
30 minutes

## Prerequisites
- Lab 07: CSS Flexbox
- Lab 08: CSS Grid

## Tools
```bash
docker run --rm -it -v /tmp:/workspace zchencow/innozverse-htmlcss:latest bash
```

---

## Lab Instructions

### Step 1: CSS Transitions

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CSS Transitions</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #f0f2f5; }
    .btn {
      background: #667eea;
      color: white;
      border: none;
      padding: 14px 32px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 1rem;
      font-weight: 600;
      margin: 10px;
      /* transition: property duration timing-function delay */
      transition: background 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease;
    }
    .btn:hover {
      background: #764ba2;
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    .btn:active { transform: translateY(0); }
    .box {
      width: 100px;
      height: 100px;
      background: #e74c3c;
      border-radius: 8px;
      margin: 20px;
      transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .box:hover {
      width: 200px;
      background: #3498db;
      border-radius: 50px;
    }
    /* Easing examples */
    .ease-demo { display: flex; gap: 10px; margin-top: 20px; align-items: flex-end; }
    .bar { width: 30px; background: #9b59b6; border-radius: 4px 4px 0 0; }
  </style>
</head>
<body>
  <h2>CSS Transitions</h2>
  <button class="btn">Hover Me!</button>
  <button class="btn" style="background:#e74c3c;transition:background 0.3s ease">Danger</button>
  <button class="btn" style="background:#27ae60;transition:background 0.3s ease">Success</button>
  <div class="box"></div>
  <p>The transition shorthand: <code>transition: property duration timing delay</code></p>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/anim-step1.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CSS Transitions</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #f0f2f5; }
    .btn { background: #667eea; color: white; border: none; padding: 14px 32px; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; transition: background 0.3s ease, transform 0.2s ease, box-shadow 0.3s ease; }
    .btn:hover { background: #764ba2; transform: translateY(-2px); box-shadow: 0 8px 25px rgba(102,126,234,0.4); }
    .btn:active { transform: translateY(0); }
    .box { width: 100px; height: 100px; background: #e74c3c; border-radius: 8px; margin: 20px; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
    .box:hover { width: 200px; background: #3498db; border-radius: 50px; }
  </style>
</head>
<body>
  <button class="btn">Hover Me!</button>
  <div class="box"></div>
</body>
</html>
EOF
```

> 💡 **`transition`** animates CSS property changes. `transition: all 0.3s ease` catches everything but is inefficient — name specific properties. Only `transform` and `opacity` are GPU-accelerated and won't cause layout reflow. Prefer those for performance.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/anim-step1.html', 'utf8');
console.log(html.includes('transition') ? '✓ transition found' : '✗ Missing transition');
console.log(html.includes('cubic-bezier') ? '✓ custom easing found' : '✗ Missing easing');
"
✓ transition found
✓ custom easing found
```

---

### Step 2: CSS Transforms

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CSS Transforms</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #f8f9fa; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; }
    .box {
      height: 100px;
      background: #667eea;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      font-size: 0.85rem;
      font-weight: bold;
      transition: transform 0.3s ease;
    }
    .translate:hover { transform: translate(10px, -10px); }
    .rotate:hover { transform: rotate(45deg); }
    .scale:hover { transform: scale(1.2); }
    .skew:hover { transform: skew(15deg, 5deg); }
    .multi:hover { transform: translateY(-5px) rotate(5deg) scale(1.1); }
    .origin:hover { transform: rotate(45deg); transform-origin: bottom left; }
  </style>
</head>
<body>
  <h2>CSS Transforms</h2>
  <div class="grid">
    <div class="box translate">translate(10px, -10px)</div>
    <div class="box rotate">rotate(45deg)</div>
    <div class="box scale">scale(1.2)</div>
    <div class="box skew">skew(15deg)</div>
    <div class="box multi">Combined</div>
    <div class="box origin" style="background:#e74c3c">transform-origin</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/anim-step2.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>CSS Transforms</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #f8f9fa; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; }
    .box { height: 100px; background: #667eea; color: white; display: flex; align-items: center; justify-content: center; border-radius: 8px; font-size: 0.85rem; font-weight: bold; transition: transform 0.3s ease; }
    .translate:hover { transform: translate(10px, -10px); }
    .rotate:hover { transform: rotate(45deg); }
    .scale:hover { transform: scale(1.2); }
    .multi:hover { transform: translateY(-5px) rotate(5deg) scale(1.1); }
  </style>
</head>
<body>
  <div class="grid">
    <div class="box translate">translate</div>
    <div class="box rotate">rotate</div>
    <div class="box scale">scale</div>
    <div class="box multi">combined</div>
  </div>
</body>
</html>
EOF
```

> 💡 **Transforms don't affect layout** — they move/scale the painted element without pushing other elements around. This makes them perfect for animations. Multiple transforms combine left-to-right: `transform: translateY(-5px) scale(1.1)` translates first, then scales.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/anim-step2.html', 'utf8');
console.log(html.includes('transform:') || html.includes('transform: ') ? '✓ transform found' : '✗ Missing');
console.log(html.includes('rotate') ? '✓ rotate transform' : '✗ Missing rotate');
"
✓ transform found
✓ rotate transform
```

---

### Step 3: @keyframes Animations

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Keyframe Animations</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #1a1a2e; color: white; display: flex; gap: 40px; flex-wrap: wrap; align-items: center; }
    /* Bounce animation */
    @keyframes bounce {
      0%, 100% { transform: translateY(0); animation-timing-function: ease-out; }
      50%       { transform: translateY(-40px); animation-timing-function: ease-in; }
    }
    .ball {
      width: 60px; height: 60px;
      background: #e74c3c;
      border-radius: 50%;
      animation: bounce 1s infinite;
    }
    /* Pulse animation */
    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50%       { transform: scale(1.1); opacity: 0.8; }
    }
    .heart {
      font-size: 3rem;
      animation: pulse 1s ease-in-out infinite;
    }
    /* Gradient shift */
    @keyframes gradient {
      0%   { background-position: 0% 50%; }
      50%  { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    .gradient-box {
      width: 200px; height: 80px;
      background: linear-gradient(270deg, #667eea, #f5576c, #43e97b, #667eea);
      background-size: 400% 400%;
      animation: gradient 3s ease infinite;
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-weight: bold;
    }
    /* Text appear */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fade-in { animation: fadeIn 0.6s ease forwards; opacity: 0; }
    .delay-1 { animation-delay: 0.2s; }
    .delay-2 { animation-delay: 0.4s; }
    .delay-3 { animation-delay: 0.6s; }
  </style>
</head>
<body>
  <div class="ball"></div>
  <div class="heart">❤️</div>
  <div class="gradient-box">Animated Gradient</div>
  <div>
    <p class="fade-in">First line</p>
    <p class="fade-in delay-1">Second line</p>
    <p class="fade-in delay-2">Third line</p>
    <p class="fade-in delay-3">Fourth line</p>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/anim-step3.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Keyframe Animations</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #1a1a2e; color: white; display: flex; gap: 40px; flex-wrap: wrap; align-items: center; }
    @keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-40px); } }
    @keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.15); } }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    .ball { width: 60px; height: 60px; background: #e74c3c; border-radius: 50%; animation: bounce 1s infinite; }
    .heart { font-size: 3rem; animation: pulse 1s ease-in-out infinite; }
    .fade-in { animation: fadeIn 0.6s ease forwards; opacity: 0; }
    .delay-1 { animation-delay: 0.2s; }
  </style>
</head>
<body>
  <div class="ball"></div>
  <div class="heart">❤️</div>
  <div><p class="fade-in">Line 1</p><p class="fade-in delay-1">Line 2</p></div>
</body>
</html>
EOF
```

> 💡 **`@keyframes`** defines the animation sequence. Use `from/to` for simple start-end or `0%, 50%, 100%` for multi-step. Staggered `animation-delay` creates a cascade effect. `animation-fill-mode: forwards` keeps the final state after the animation ends.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/anim-step3.html', 'utf8');
console.log(html.includes('@keyframes') ? '✓ @keyframes found' : '✗ Missing @keyframes');
console.log(html.includes('animation:') || html.includes('animation: ') ? '✓ animation property found' : '✗ Missing');
"
✓ @keyframes found
✓ animation property found
```

---

### Step 4: Animation Properties

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Animation Properties</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #f8f9fa; }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to   { transform: rotate(360deg); }
    }
    @keyframes colorCycle {
      0%   { background: #e74c3c; }
      25%  { background: #3498db; }
      50%  { background: #2ecc71; }
      75%  { background: #f39c12; }
      100% { background: #e74c3c; }
    }
    .demo { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 20px; }
    .box {
      width: 80px; height: 80px;
      border-radius: 8px;
      background: #667eea;
      display: flex; align-items: center; justify-content: center;
      color: white; font-size: 0.7rem; text-align: center;
    }
    /* iteration-count */
    .once     { animation: spin 1s ease 1; }          /* play once */
    .thrice   { animation: spin 1s ease 3; }          /* play 3x */
    .infinite { animation: spin 2s linear infinite; } /* forever */
    /* direction */
    .reverse  { animation: spin 1.5s linear infinite reverse; }
    .alternate{ animation: spin 1.5s ease-in-out infinite alternate; }
    /* fill-mode */
    .forwards { animation: colorCycle 2s ease 1 forwards; }   /* stays at end */
    .backwards{ animation: colorCycle 2s ease 1 backwards; }  /* jumps to start before playing */
    /* play-state */
    .paused   { animation: spin 2s linear infinite; animation-play-state: paused; }
    .paused:hover { animation-play-state: running; }
  </style>
</head>
<body>
  <h2>Animation Properties Deep Dive</h2>
  <div class="demo">
    <div class="box once">once</div>
    <div class="box infinite">∞</div>
    <div class="box reverse">↺ reverse</div>
    <div class="box alternate">⇄ alternate</div>
    <div class="box forwards">forwards</div>
    <div class="box paused">hover to play</div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/anim-step4.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Animation Properties</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #f8f9fa; }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes colorCycle { 0% { background: #e74c3c; } 50% { background: #3498db; } 100% { background: #2ecc71; } }
    .demo { display: flex; gap: 20px; flex-wrap: wrap; margin-top: 20px; }
    .box { width: 80px; height: 80px; border-radius: 8px; background: #667eea; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.75rem; text-align: center; }
    .infinite { animation: spin 2s linear infinite; }
    .reverse { animation: spin 1.5s linear infinite reverse; }
    .alternate { animation: spin 1.5s ease-in-out infinite alternate; }
    .forwards { animation: colorCycle 3s ease 1 forwards; }
    .paused { animation: spin 2s linear infinite paused; }
    .paused:hover { animation-play-state: running; }
  </style>
</head>
<body>
  <div class="demo">
    <div class="box infinite">∞</div>
    <div class="box reverse">↺</div>
    <div class="box alternate">⇄</div>
    <div class="box forwards">color</div>
    <div class="box paused">hover</div>
  </div>
</body>
</html>
EOF
```

> 💡 **Key animation properties:** `animation-iteration-count` (infinite or number), `animation-direction` (normal/reverse/alternate), `animation-fill-mode` (forwards = stay at end), `animation-play-state` (running/paused — controllable with JavaScript).

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/anim-step4.html', 'utf8');
console.log(html.includes('infinite') ? '✓ infinite animation' : '✗ Missing infinite');
console.log(html.includes('forwards') ? '✓ fill-mode forwards' : '✗ Missing forwards');
"
✓ infinite animation
✓ fill-mode forwards
```

---

### Step 5: Hover Effects & Interactive Animations

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Hover Effects</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #1a1a2e; display: flex; gap: 20px; flex-wrap: wrap; }
    /* Magnetic button */
    .btn-magnetic {
      background: #667eea;
      color: white;
      border: none;
      padding: 16px 32px;
      border-radius: 50px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    .btn-magnetic::before {
      content: '';
      position: absolute;
      top: 50%; left: 50%;
      width: 0; height: 0;
      background: rgba(255,255,255,0.3);
      border-radius: 50%;
      transform: translate(-50%, -50%);
      transition: width 0.6s ease, height 0.6s ease;
    }
    .btn-magnetic:hover::before { width: 300px; height: 300px; }
    .btn-magnetic:hover { box-shadow: 0 12px 30px rgba(102,126,234,0.5); transform: translateY(-3px); }
    /* Underline link effect */
    .link-effect {
      color: white;
      text-decoration: none;
      font-size: 1.2rem;
      position: relative;
      padding-bottom: 4px;
    }
    .link-effect::after {
      content: '';
      position: absolute;
      bottom: 0; left: 0;
      width: 0; height: 2px;
      background: #667eea;
      transition: width 0.3s ease;
    }
    .link-effect:hover::after { width: 100%; }
    /* Image zoom card */
    .img-card {
      width: 200px;
      border-radius: 12px;
      overflow: hidden;
      background: #16213e;
    }
    .img-thumb {
      height: 140px;
      background: linear-gradient(135deg, #667eea, #764ba2);
      display: flex; align-items: center; justify-content: center;
      font-size: 3rem;
      overflow: hidden;
      transition: transform 0.4s ease;
    }
    .img-card:hover .img-thumb { transform: scale(1.1); }
    .img-card p { color: white; padding: 12px; font-size: 0.9rem; }
  </style>
</head>
<body>
  <button class="btn-magnetic">Ripple Hover</button>
  <a href="#" class="link-effect">Underline Reveal</a>
  <div class="img-card">
    <div class="img-thumb">🖼️</div>
    <p>Image Zoom on Hover</p>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/anim-step5.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Hover Effects</title>
  <style>
    body { font-family: sans-serif; padding: 40px; background: #1a1a2e; display: flex; gap: 20px; flex-wrap: wrap; align-items: center; }
    .btn { background: #667eea; color: white; border: none; padding: 16px 32px; border-radius: 50px; font-size: 1rem; cursor: pointer; position: relative; overflow: hidden; transition: transform 0.2s ease, box-shadow 0.3s ease; }
    .btn::before { content: ''; position: absolute; top: 50%; left: 50%; width: 0; height: 0; background: rgba(255,255,255,0.3); border-radius: 50%; transform: translate(-50%,-50%); transition: width 0.6s ease, height 0.6s ease; }
    .btn:hover::before { width: 300px; height: 300px; }
    .btn:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(102,126,234,0.5); }
    .link-effect { color: white; text-decoration: none; font-size: 1.2rem; position: relative; padding-bottom: 4px; }
    .link-effect::after { content: ''; position: absolute; bottom: 0; left: 0; width: 0; height: 2px; background: #667eea; transition: width 0.3s ease; }
    .link-effect:hover::after { width: 100%; }
    .img-card { width: 200px; border-radius: 12px; overflow: hidden; background: #16213e; }
    .img-thumb { height: 140px; background: linear-gradient(135deg,#667eea,#764ba2); display: flex; align-items: center; justify-content: center; font-size: 3rem; transition: transform 0.4s ease; }
    .img-card:hover .img-thumb { transform: scale(1.1); }
  </style>
</head>
<body>
  <button class="btn">Ripple Effect</button>
  <a href="#" class="link-effect">Underline Reveal</a>
  <div class="img-card"><div class="img-thumb">🖼️</div><p style="color:white;padding:12px">Image Zoom</p></div>
</body>
</html>
EOF
```

> 💡 **CSS pseudo-elements (`::before`, `::after`)** add decorative content without extra HTML. The ripple effect uses a pseudo-element that starts at 0 size and grows to cover the button on hover. `overflow: hidden` clips it to the button shape.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/anim-step5.html', 'utf8');
console.log(html.includes('::before') || html.includes(':before') ? '✓ Pseudo-element found' : '✗ Missing ::before');
console.log(html.includes('overflow: hidden') || html.includes('overflow:hidden') ? '✓ overflow hidden found' : '✗ Missing overflow');
"
✓ Pseudo-element found
✓ overflow hidden found
```

---

### Step 6: Loading Spinner Animation

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Loading Spinners</title>
  <style>
    body { font-family: sans-serif; background: #1a1a2e; display: flex; gap: 40px; flex-wrap: wrap; justify-content: center; align-items: center; min-height: 100vh; }
    /* Classic spinner */
    @keyframes spin { to { transform: rotate(360deg); } }
    .spinner {
      width: 48px; height: 48px;
      border: 5px solid rgba(255,255,255,0.1);
      border-top-color: #667eea;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    /* Dots */
    @keyframes dotBounce {
      0%, 80%, 100% { transform: scale(0); opacity: 0; }
      40% { transform: scale(1); opacity: 1; }
    }
    .dots { display: flex; gap: 8px; }
    .dot {
      width: 12px; height: 12px;
      background: #667eea;
      border-radius: 50%;
      animation: dotBounce 1.4s ease-in-out infinite;
    }
    .dot:nth-child(2) { animation-delay: 0.16s; }
    .dot:nth-child(3) { animation-delay: 0.32s; }
    /* Skeleton loader */
    @keyframes shimmer {
      from { background-position: -468px 0; }
      to   { background-position: 468px 0; }
    }
    .skeleton {
      width: 200px;
      background: linear-gradient(90deg, #16213e 8%, #0f3460 18%, #16213e 33%);
      background-size: 800px 104px;
      animation: shimmer 1.5s ease-in-out infinite;
      border-radius: 4px;
    }
    .skeleton-text { height: 12px; margin: 8px 0; border-radius: 4px; }
    .skeleton-img { height: 120px; border-radius: 8px; margin-bottom: 12px; }
    /* Progress bar */
    @keyframes progress { from { width: 0%; } to { width: 85%; } }
    .progress-bar {
      width: 200px; height: 6px;
      background: rgba(255,255,255,0.1);
      border-radius: 3px;
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #667eea, #f5576c);
      animation: progress 2s ease-out forwards;
    }
  </style>
</head>
<body>
  <div class="spinner"></div>
  <div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
  <div class="skeleton">
    <div class="skeleton skeleton-img"></div>
    <div class="skeleton skeleton-text"></div>
    <div class="skeleton skeleton-text" style="width:80%"></div>
    <div class="skeleton skeleton-text" style="width:60%"></div>
  </div>
  <div>
    <p style="color:white;margin-bottom:8px">Loading: 85%</p>
    <div class="progress-bar"><div class="progress-fill"></div></div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/anim-step6.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Loading Animations</title>
  <style>
    body { font-family: sans-serif; background: #1a1a2e; display: flex; gap: 40px; justify-content: center; align-items: center; min-height: 100vh; flex-wrap: wrap; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .spinner { width: 48px; height: 48px; border: 5px solid rgba(255,255,255,0.1); border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes dotBounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
    .dots { display: flex; gap: 8px; }
    .dot { width: 12px; height: 12px; background: #667eea; border-radius: 50%; animation: dotBounce 1.4s ease-in-out infinite; }
    .dot:nth-child(2) { animation-delay: 0.16s; }
    .dot:nth-child(3) { animation-delay: 0.32s; }
    @keyframes shimmer { from { background-position: -468px 0; } to { background-position: 468px 0; } }
    .skeleton { width: 200px; }
    .skeleton-block { background: linear-gradient(90deg, #16213e 8%, #0f3460 18%, #16213e 33%); background-size: 800px; animation: shimmer 1.5s infinite; border-radius: 4px; margin: 8px 0; }
  </style>
</head>
<body>
  <div class="spinner"></div>
  <div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
  <div class="skeleton">
    <div class="skeleton-block" style="height:120px;border-radius:8px"></div>
    <div class="skeleton-block" style="height:12px"></div>
    <div class="skeleton-block" style="height:12px;width:80%"></div>
  </div>
</body>
</html>
EOF
```

> 💡 **Loading indicators** reduce perceived wait time and prevent users from thinking something broke. The shimmer/skeleton loader is especially effective — it shows content shape before data loads, reducing layout shift when content appears (better CLS score).

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/anim-step6.html', 'utf8');
console.log(html.includes('spinner') ? '✓ Spinner found' : '✗ Missing');
console.log(html.includes('shimmer') ? '✓ Shimmer/skeleton found' : '✗ Missing shimmer');
"
✓ Spinner found
✓ Shimmer/skeleton found
```

---

### Step 7: Card Flip Animation (3D Transforms)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>3D Card Flip</title>
  <style>
    body { font-family: sans-serif; background: #1a1a2e; display: flex; gap: 30px; justify-content: center; align-items: center; min-height: 100vh; flex-wrap: wrap; }
    .card-3d {
      width: 200px;
      height: 280px;
      perspective: 1000px;
      cursor: pointer;
    }
    .card-inner {
      width: 100%;
      height: 100%;
      position: relative;
      transform-style: preserve-3d;
      transition: transform 0.7s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .card-3d:hover .card-inner { transform: rotateY(180deg); }
    .card-front,
    .card-back {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 16px;
      backface-visibility: hidden;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .card-front {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
    }
    .card-back {
      background: linear-gradient(135deg, #f5576c, #f093fb);
      color: white;
      transform: rotateY(180deg);
    }
    .card-icon { font-size: 4rem; margin-bottom: 16px; }
    .card-title { font-size: 1.1rem; font-weight: bold; text-align: center; }
    .card-desc { font-size: 0.85rem; margin-top: 10px; text-align: center; opacity: 0.9; line-height: 1.4; }
  </style>
</head>
<body>
  <div class="card-3d">
    <div class="card-inner">
      <div class="card-front">
        <div class="card-icon">🎴</div>
        <div class="card-title">Hover to Flip</div>
        <div class="card-desc">CSS 3D transform magic</div>
      </div>
      <div class="card-back">
        <div class="card-icon">✨</div>
        <div class="card-title">Back Side!</div>
        <div class="card-desc">backface-visibility: hidden hides each side when rotated</div>
      </div>
    </div>
  </div>
  <div class="card-3d">
    <div class="card-inner">
      <div class="card-front" style="background:linear-gradient(135deg,#43e97b,#38f9d7)">
        <div class="card-icon">🌿</div>
        <div class="card-title">Profile Card</div>
        <div class="card-desc">Hover for contact info</div>
      </div>
      <div class="card-back" style="background:linear-gradient(135deg,#4facfe,#00f2fe)">
        <div class="card-icon">📧</div>
        <div class="card-title">Contact</div>
        <div class="card-desc">hello@example.com<br>+1 234 567 890</div>
      </div>
    </div>
  </div>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/anim-step7.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>3D Card Flip</title>
  <style>
    body { font-family: sans-serif; background: #1a1a2e; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
    .card-3d { width: 200px; height: 280px; perspective: 1000px; cursor: pointer; }
    .card-inner { width: 100%; height: 100%; position: relative; transform-style: preserve-3d; transition: transform 0.7s ease; }
    .card-3d:hover .card-inner { transform: rotateY(180deg); }
    .card-front, .card-back { position: absolute; width: 100%; height: 100%; border-radius: 16px; backface-visibility: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; color: white; }
    .card-front { background: linear-gradient(135deg, #667eea, #764ba2); }
    .card-back { background: linear-gradient(135deg, #f5576c, #f093fb); transform: rotateY(180deg); }
  </style>
</head>
<body>
  <div class="card-3d">
    <div class="card-inner">
      <div class="card-front"><div style="font-size:4rem">🎴</div><h3>Hover to Flip</h3></div>
      <div class="card-back"><div style="font-size:4rem">✨</div><h3>Back Side!</h3></div>
    </div>
  </div>
</body>
</html>
EOF
```

> 💡 **3D transforms require three things:** `perspective` on the parent (creates depth), `transform-style: preserve-3d` on the flip container, and `backface-visibility: hidden` on each face. `perspective: 1000px` means the vanishing point is 1000px away — smaller = more dramatic 3D effect.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/anim-step7.html', 'utf8');
console.log(html.includes('perspective') ? '✓ 3D perspective found' : '✗ Missing perspective');
console.log(html.includes('backface-visibility') ? '✓ backface-visibility found' : '✗ Missing backface-visibility');
console.log(html.includes('preserve-3d') ? '✓ transform-style preserve-3d' : '✗ Missing preserve-3d');
"
✓ 3D perspective found
✓ backface-visibility found
✓ transform-style preserve-3d
```

---

### Step 8: Capstone — Animated Hero Section

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Animated Hero</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: 'Segoe UI', sans-serif; overflow-x: hidden; }
    /* Animated gradient background */
    @keyframes gradientShift {
      0%   { background-position: 0% 50%; }
      50%  { background-position: 100% 50%; }
      100% { background-position: 0% 50%; }
    }
    .hero {
      background: linear-gradient(270deg, #667eea, #764ba2, #f5576c, #43e97b, #667eea);
      background-size: 400% 400%;
      animation: gradientShift 8s ease infinite;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      color: white;
      padding: 20px;
      position: relative;
      overflow: hidden;
    }
    /* Floating shapes */
    @keyframes float {
      0%, 100% { transform: translateY(0) rotate(0deg); }
      50% { transform: translateY(-30px) rotate(180deg); }
    }
    .shape {
      position: absolute;
      border-radius: 50%;
      opacity: 0.1;
      animation: float linear infinite;
    }
    /* Text reveal */
    @keyframes slideUp {
      from { opacity: 0; transform: translateY(40px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .hero-tag {
      background: rgba(255,255,255,0.2);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 50px;
      padding: 8px 20px;
      font-size: 0.85rem;
      margin-bottom: 24px;
      animation: slideUp 0.6s ease both;
    }
    .hero h1 {
      font-size: clamp(2.5rem, 8vw, 5rem);
      font-weight: 900;
      line-height: 1.05;
      margin-bottom: 24px;
      animation: slideUp 0.6s ease 0.2s both;
    }
    .hero p {
      font-size: clamp(1rem, 2.5vw, 1.3rem);
      opacity: 0.9;
      max-width: 600px;
      line-height: 1.6;
      margin-bottom: 40px;
      animation: slideUp 0.6s ease 0.4s both;
    }
    .hero-btns {
      display: flex;
      gap: 16px;
      flex-wrap: wrap;
      justify-content: center;
      animation: slideUp 0.6s ease 0.6s both;
    }
    .btn-primary {
      background: white;
      color: #667eea;
      border: none;
      padding: 16px 36px;
      border-radius: 50px;
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.2s ease, box-shadow 0.3s ease;
    }
    .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,0.2); }
    .btn-secondary {
      background: transparent;
      color: white;
      border: 2px solid rgba(255,255,255,0.6);
      padding: 16px 36px;
      border-radius: 50px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.3s ease, transform 0.2s ease;
    }
    .btn-secondary:hover { background: rgba(255,255,255,0.15); transform: translateY(-3px); }
    /* Stats bar */
    .stats {
      display: flex;
      gap: 40px;
      margin-top: 60px;
      animation: slideUp 0.6s ease 0.8s both;
      flex-wrap: wrap;
      justify-content: center;
    }
    .stat { text-align: center; }
    .stat-n { font-size: 2rem; font-weight: 900; }
    .stat-l { font-size: 0.8rem; opacity: 0.7; margin-top: 4px; }
  </style>
</head>
<body>
  <section class="hero">
    <!-- Floating shapes -->
    <div class="shape" style="width:300px;height:300px;background:white;top:-100px;left:-100px;animation-duration:15s"></div>
    <div class="shape" style="width:200px;height:200px;background:white;bottom:-50px;right:-50px;animation-duration:12s;animation-delay:-5s"></div>
    <div class="shape" style="width:100px;height:100px;background:white;top:30%;right:10%;animation-duration:8s;animation-delay:-3s"></div>
    <div class="hero-tag">🚀 Now with 10x Performance</div>
    <h1>Build the Future<br>of the Web</h1>
    <p>A complete platform for modern web development. Ship faster, scale easier, delight users.</p>
    <div class="hero-btns">
      <button class="btn-primary">Start Building Free</button>
      <button class="btn-secondary">▶ Watch Demo</button>
    </div>
    <div class="stats">
      <div class="stat"><div class="stat-n">50K+</div><div class="stat-l">DEVELOPERS</div></div>
      <div class="stat"><div class="stat-n">99.9%</div><div class="stat-l">UPTIME</div></div>
      <div class="stat"><div class="stat-n">&lt;1ms</div><div class="stat-l">RESPONSE TIME</div></div>
      <div class="stat"><div class="stat-n">4.9★</div><div class="stat-l">USER RATING</div></div>
    </div>
  </section>
</body>
</html>
```

Write this file:
```bash
cat > /tmp/animations.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Animated Hero</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: sans-serif; }
    @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    @keyframes slideUp { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-30px); } }
    .hero { background: linear-gradient(270deg, #667eea, #764ba2, #f5576c, #43e97b, #667eea); background-size: 400% 400%; animation: gradientShift 8s ease infinite; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; color: white; padding: 20px; position: relative; overflow: hidden; }
    .hero h1 { font-size: clamp(2.5rem, 8vw, 5rem); font-weight: 900; margin-bottom: 24px; animation: slideUp 0.6s ease 0.2s both; }
    .hero p { font-size: clamp(1rem, 2.5vw, 1.3rem); max-width: 600px; margin-bottom: 40px; animation: slideUp 0.6s ease 0.4s both; }
    .hero-btns { display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; animation: slideUp 0.6s ease 0.6s both; }
    .btn-primary { background: white; color: #667eea; border: none; padding: 16px 36px; border-radius: 50px; font-size: 1rem; font-weight: 700; cursor: pointer; transition: transform 0.2s ease; }
    .btn-primary:hover { transform: translateY(-3px); }
    .shape { position: absolute; border-radius: 50%; opacity: 0.1; animation: float linear infinite; }
  </style>
</head>
<body>
  <section class="hero">
    <div class="shape" style="width:300px;height:300px;background:white;top:-100px;left:-100px;animation-duration:15s"></div>
    <h1>Build the Future</h1>
    <p>Animated hero section with CSS keyframes, gradient animation, and staggered entrance effects.</p>
    <div class="hero-btns">
      <button class="btn-primary">Get Started Free</button>
    </div>
  </section>
</body>
</html>
EOF
```

> 💡 **Animation checklist:** Use `animation-fill-mode: both` to apply the start state immediately. Stagger delays with multiples of 0.2s for elegant cascades. Always check `prefers-reduced-motion` in production for accessibility. Gradient animations use `background-size: 400%` to give the position something to move through.

**📸 Verified Output:**
```
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const html = fs.readFileSync('/workspace/animations.html', 'utf8');
console.log(html.includes('@keyframes') ? '✓ Keyframe animations' : '✗ Missing @keyframes');
console.log(html.includes('gradientShift') || html.includes('gradient') ? '✓ Gradient animation' : '✗ Missing');
console.log(html.includes('slideUp') ? '✓ Entrance animation' : '✗ Missing entrance');
"
✓ Keyframe animations
✓ Gradient animation
✓ Entrance animation
```

---

## Verification

```bash
docker run --rm -v /tmp:/workspace zchencow/innozverse-htmlcss:latest node -e "
const fs = require('fs');
const checks = [
  ['anim-step1.html', 'transition'],
  ['anim-step2.html', 'transform'],
  ['anim-step3.html', '@keyframes'],
  ['anim-step4.html', 'infinite'],
  ['anim-step5.html', '::before'],
  ['anim-step6.html', 'spinner'],
  ['anim-step7.html', 'perspective'],
  ['animations.html', '@keyframes'],
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

| Concept | CSS | Best For |
|---------|-----|----------|
| Transitions | `transition: prop dur ease` | Hover/focus state changes |
| Transforms | `transform: translate/rotate/scale` | Movement without layout reflow |
| Keyframes | `@keyframes name { ... }` | Complex multi-step animations |
| 3D | `perspective`, `preserve-3d` | Flip cards, depth effects |
| Performance | `transform` + `opacity` only | GPU-accelerated, no reflow |

## Further Reading
- [MDN CSS Animations](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_animations)
- [cubic-bezier.com](https://cubic-bezier.com/) — visual easing editor
- [Animate.css](https://animate.style/) — ready-made animation library
