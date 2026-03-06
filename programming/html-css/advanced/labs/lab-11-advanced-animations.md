# Lab 11: Advanced Animations

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master advanced animation techniques: scroll-driven animations with `animation-timeline`, View Transitions API, CSS motion path, staggered animations, and `prefers-reduced-motion` safe patterns.

---

## Step 1: Scroll-Driven Animations — scroll()

```css
/* Scroll progress indicator */
@keyframes progress-bar {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}

.scroll-progress {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 4px;
  background: var(--color-primary);
  transform-origin: left center;
  
  /* Link animation to page scroll */
  animation: progress-bar linear both;
  animation-timeline: scroll(root block);
  /* scroll(scroller axis) */
  /* scroller: root | self | nearest | <element> */
  /* axis: block | inline | x | y */
}

/* Sticky header opacity change on scroll */
@keyframes header-fade {
  0%   { background: transparent; backdrop-filter: none; }
  100% { background: rgba(255,255,255,0.9); backdrop-filter: blur(10px); }
}

.header {
  animation: header-fade linear both;
  animation-timeline: scroll(root);
  animation-range: 0px 100px; /* start-offset end-offset */
}

/* Parallax effect */
@keyframes parallax-slow {
  from { transform: translateY(0); }
  to   { transform: translateY(-30%); }
}

.hero-background {
  animation: parallax-slow linear both;
  animation-timeline: scroll(root);
  animation-range: 0% 50vh; /* only during first 50vh of scroll */
}
```

---

## Step 2: Scroll-Driven Animations — view()

```css
/* animation-timeline: view() — element entering viewport */

@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.reveal-on-scroll {
  animation: fade-up ease-out both;
  animation-timeline: view();
  
  /* When to play: entry 0% (start entering) to entry 100% (fully entered) */
  animation-range: entry 0% entry 100%;
}

/* Fade out as element leaves viewport */
.fade-out-on-leave {
  animation: fade-up ease-in both reverse; /* reverse plays backwards */
  animation-timeline: view();
  animation-range: exit 0% exit 100%;
}

/* Combined: fade in AND fade out */
.card {
  animation: fade-up linear both;
  animation-timeline: view();
  animation-range: entry 20% cover 50%; /* delay start, end at center */
}

/* view() options */
.element {
  animation-timeline: view(block);      /* default: block axis */
  animation-timeline: view(inline);     /* inline axis */
  animation-timeline: view(block 20px 20px); /* inset margins */
}
```

---

## Step 3: View Transitions API

```javascript
// Page transitions without full reload
async function navigateTo(url) {
  if (!document.startViewTransition) {
    window.location.href = url;
    return;
  }

  const transition = document.startViewTransition(async () => {
    // Fetch new page content
    const response = await fetch(url);
    const html = await response.text();
    const doc = new DOMParser().parseFromString(html, 'text/html');
    
    // Replace content (must happen inside this callback)
    document.title = doc.title;
    document.querySelector('main').replaceWith(
      doc.querySelector('main')
    );
  });

  // You can do things with the transition object
  await transition.ready;    // CSS animation is about to begin
  await transition.finished; // CSS animation is complete
}

// SPA navigation
document.addEventListener('click', (e) => {
  const link = e.target.closest('a[href]');
  if (!link) return;
  const url = link.href;
  if (!url.startsWith(location.origin)) return;
  
  e.preventDefault();
  navigateTo(url);
});
```

```css
/* View transition animations */

/* Default cross-fade — customize the timing */
::view-transition-old(root) {
  animation: 300ms ease-out both fade-out;
}
::view-transition-new(root) {
  animation: 300ms ease-in both fade-in;
}

/* Named element transition (morphing) */
.hero-title {
  view-transition-name: hero-title;
}

/* Slide transition */
@keyframes slide-in-from-right {
  from { transform: translateX(100vw); }
}
@keyframes slide-out-to-left {
  to   { transform: translateX(-100vw); }
}

::view-transition-new(root)  { animation: 400ms ease slide-in-from-right; }
::view-transition-old(root)  { animation: 400ms ease slide-out-to-left; }

/* Individual element morph */
::view-transition-group(hero-title) {
  animation-duration: 500ms;
  animation-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1); /* spring */
}
```

---

## Step 4: CSS Motion Path

```css
/* Move element along an SVG path */
@keyframes move-along-path {
  0%   { offset-distance: 0%; }
  100% { offset-distance: 100%; }
}

.car {
  offset-path: path('M 0,100 C 50,0 150,0 200,100 S 350,200 400,100');
  offset-rotate: auto;         /* face direction of travel */
  offset-anchor: 50% 50%;     /* pivot point */
  
  animation: move-along-path 3s ease-in-out infinite;
  position: absolute;
  width: 40px; height: 20px;
}

/* Different path types */
.element {
  /* SVG path string */
  offset-path: path('M0 100 C30 0 170 0 200 100');
  
  /* Geometric shapes */
  offset-path: circle(100px at 200px 200px);
  offset-path: ellipse(150px 80px at 50% 50%);
  offset-path: inset(10px round 10px);
  offset-path: polygon(0 0, 100% 0, 100% 100%);
  
  /* Reference to SVG element */
  offset-path: url('#svg-track');
  
  /* ray() — straight line at an angle */
  offset-path: ray(45deg closest-side);
}

/* Combined with transforms */
.particle {
  offset-path: circle(120px at center);
  animation: orbit 3s linear infinite;
}

@keyframes orbit {
  to { offset-distance: 100%; }
}
```

---

## Step 5: Staggered Animations

```css
/* Stagger with nth-child delay */
.item-list .item {
  opacity: 0;
  transform: translateY(20px);
  animation: fade-in-up 0.5s ease forwards;
}

.item-list .item:nth-child(1) { animation-delay: 0.0s; }
.item-list .item:nth-child(2) { animation-delay: 0.1s; }
.item-list .item:nth-child(3) { animation-delay: 0.2s; }
.item-list .item:nth-child(4) { animation-delay: 0.3s; }
.item-list .item:nth-child(5) { animation-delay: 0.4s; }

/* CSS custom property stagger (cleaner) */
.item-list .item {
  animation: fade-in-up 0.5s ease forwards;
  animation-delay: calc(var(--i, 0) * 100ms);
}

/* Set --i via inline style or JS */
/* <li style="--i: 0">...</li> */
/* <li style="--i: 1">...</li> */

/* JavaScript stagger */
document.querySelectorAll('.item').forEach((el, i) => {
  el.style.setProperty('--i', i);
});

/* Grid stagger */
.grid .cell {
  animation: pop-in 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
  animation-delay: calc((var(--row, 0) * 4 + var(--col, 0)) * 50ms);
}

@keyframes pop-in {
  from { opacity: 0; transform: scale(0.5); }
  to   { opacity: 1; transform: scale(1); }
}
```

---

## Step 6: prefers-reduced-motion — Safe Patterns

```css
/* ✓ Pattern 1: Opt-in (safest) */
/* Define NO animations by default */
/* Only add animations when motion is OK */

@media (prefers-reduced-motion: no-preference) {
  .card {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }
  .card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  }
}

/* ✓ Pattern 2: Reduce (still useful feedback) */
/* Keep animations but make them instant or simpler */

.button {
  transition: background 0.3s ease, transform 0.2s ease;
}

@media (prefers-reduced-motion: reduce) {
  .button {
    transition: background 0.1s ease; /* instant, but still shows state change */
  }
  
  /* Remove transforms that suggest motion */
  .animated-element {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}

/* ✓ Pattern 3: Alternative animation */
/* Different animation that's still meaningful */

@media (prefers-reduced-motion: no-preference) {
  .page-enter { animation: slide-in-from-right 0.4s ease; }
}

@media (prefers-reduced-motion: reduce) {
  .page-enter { animation: fade-in 0.2s ease; } /* fade instead of slide */
}

/* ✓ Check in JavaScript */
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (!prefersReduced) {
  element.animate([...], { duration: 500 });
} else {
  element.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 10 });
}
```

---

## Step 7: WAAPI (Web Animations API)

```javascript
// Programmatic animations using the Web Animations API

// element.animate() — creates and plays an animation
const animation = element.animate(
  // Keyframes array
  [
    { opacity: 0, transform: 'translateY(-20px)' },  // from
    { opacity: 1, transform: 'translateY(0)' }        // to
  ],
  // Options
  {
    duration: 400,
    easing: 'ease-out',
    fill: 'forwards',
    delay: 200,
    iterations: 1,
    direction: 'normal',
    id: 'fade-in'
  }
);

// Control playback
animation.pause();
animation.play();
animation.reverse();
animation.cancel();
animation.finish();

// Callbacks
animation.addEventListener('finish', () => {
  console.log('Animation complete!');
});

animation.ready.then(() => {
  console.log('Animation is playing');
});

// Access all animations
const animations = document.getAnimations();
animations.forEach(a => a.pause()); // pause all page animations

// Stagger with WAAPI
document.querySelectorAll('.item').forEach((el, i) => {
  el.animate(
    [{ opacity: 0, transform: 'translateY(20px)' },
     { opacity: 1, transform: 'translateY(0)' }],
    { duration: 400, delay: i * 100, fill: 'forwards', easing: 'ease-out' }
  );
});
```

---

## Step 8: Capstone — Animation Timeline Calculator

```bash
docker run --rm -v /tmp/animation_timeline.js:/test.js node:20-alpine node /test.js
```

*(Create the file:)*
```bash
cat > /tmp/animation_timeline.js << 'EOF'
function easeInOut(t) { return t < 0.5 ? 2*t*t : -1+(4-2*t)*t; }
function easeIn(t) { return t*t; }
function easeOut(t) { return t*(2-t); }
function linear(t) { return t; }
var funcs = {linear:linear, easeIn:easeIn, easeOut:easeOut, easeInOut:easeInOut};
var steps = [0, 0.25, 0.5, 0.75, 1.0];
console.log("Animation Easing Values at keyframe points");
console.log("=".repeat(55));
console.log("t".padEnd(6) + Object.keys(funcs).map(function(n){ return n.padEnd(14); }).join(""));
console.log("-".repeat(55));
steps.forEach(function(t){
  var row = String(t).padEnd(6);
  Object.values(funcs).forEach(function(fn){ row += fn(t).toFixed(4).padEnd(14); });
  console.log(row);
});
console.log("\nScroll-driven animation breakdown:");
console.log("animation-timeline: scroll(root block)");
console.log("  => tracks document scroll position (0% to 100%)");
console.log("animation-timeline: view()");
console.log("  => tracks element entering/leaving viewport");
console.log("animation-range: entry 0% entry 100%");
console.log("  => play animation as element enters view");
EOF
docker run --rm -v /tmp/animation_timeline.js:/test.js node:20-alpine node /test.js
```

📸 **Verified Output:**
```
Animation Easing Values at keyframe points
=======================================================
t     linear        easeIn        easeOut       easeInOut     
-------------------------------------------------------
0     0.0000        0.0000        0.0000        0.0000        
0.25  0.2500        0.0625        0.4375        0.1250        
0.5   0.5000        0.2500        0.7500        0.5000        
0.75  0.7500        0.5625        0.9375        0.8750        
1     1.0000        1.0000        1.0000        1.0000        

Scroll-driven animation breakdown:
animation-timeline: scroll(root block)
  => tracks document scroll position (0% to 100%)
animation-timeline: view()
  => tracks element entering/leaving viewport
animation-range: entry 0% entry 100%
  => play animation as element enters view
```

---

## Summary

| Feature | Syntax | Browser Support |
|---------|--------|----------------|
| Scroll timeline | `animation-timeline: scroll()` | Chrome 115+, ~72% |
| View timeline | `animation-timeline: view()` | Chrome 115+, ~72% |
| animation-range | `entry 0% entry 100%` | Chrome 115+ |
| View Transitions | `document.startViewTransition()` | Chrome 111+, ~75% |
| `view-transition-name` | Named element morph | Chrome 111+ |
| Motion path | `offset-path: path(...)` | 88%+ |
| `offset-distance` | `0% to 100%` | 88%+ |
| Stagger | `animation-delay: calc(var(--i) * 100ms)` | Universal |
| WAAPI | `element.animate([...], opts)` | Universal |
| `prefers-reduced-motion` | `@media (prefers-reduced-motion: reduce)` | 95%+ |
