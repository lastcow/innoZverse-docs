# Lab 06: CSS Animations

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master CSS animations from `@keyframes` to advanced techniques: the 8-property animation shorthand, transitions vs animations, `will-change`, motion path with `offset-path`, timing functions, and accessibility considerations.

---

## Step 1: @keyframes

```css
/* Basic keyframe definition */
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* With percentage steps */
@keyframes slideAndFade {
  0%   { opacity: 0; transform: translateY(-20px); }
  60%  { opacity: 1; transform: translateY(4px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* Pulse animation */
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.05); }
}

/* Shimmer loading effect */
@keyframes shimmer {
  0%   { background-position: -1000px 0; }
  100% { background-position: 1000px 0; }
}

/* Typing cursor */
@keyframes blink {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0; }
}

/* Rotation */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Bounce */
@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40%           { transform: translateY(-24px); }
  60%           { transform: translateY(-12px); }
}
```

---

## Step 2: Animation Shorthand — 8 Sub-Properties

```css
/* Full shorthand: name | duration | easing | delay | iterations | direction | fill-mode | play-state */
.element {
  animation: fadeIn 0.3s ease-out 0s 1 normal forwards running;
}

/* Each sub-property */
.card {
  animation-name:            slideAndFade;  /* @keyframes name */
  animation-duration:        0.5s;          /* how long */
  animation-timing-function: ease-out;      /* easing curve */
  animation-delay:           0.1s;          /* wait before start */
  animation-iteration-count: 1;             /* 1, 2, infinite */
  animation-direction:       normal;        /* normal, reverse, alternate, alternate-reverse */
  animation-fill-mode:       forwards;      /* none, forwards, backwards, both */
  animation-play-state:      running;       /* running, paused */
}

/* Multiple animations */
.loader {
  animation:
    spin   1s linear infinite,
    pulse  2s ease-in-out infinite;
}

/* fill-mode values */
/* none:      element returns to pre-animation state after ending */
/* forwards:  element stays at final keyframe after ending ✓ most used */
/* backwards: element starts at first keyframe during delay period */
/* both:      combines backwards + forwards */
```

> 💡 `animation-fill-mode: forwards` is almost always what you want — it keeps the element at its final state after the animation ends.

---

## Step 3: Transitions vs Animations

```css
/* TRANSITIONS: for state changes (hover, focus, active) */
.button {
  background: blue;
  transform: translateY(0);
  transition:
    background 0.2s ease,
    transform  0.15s ease-out;
}

.button:hover {
  background: darkblue;
  transform: translateY(-2px);
}

/* Full transition shorthand */
.link {
  /* property | duration | easing | delay */
  transition: color 0.2s ease 0s, opacity 0.3s ease-in 0.1s;
}

/* transition: all (convenient but avoid in production - triggers on everything) */
.bad  { transition: all 0.3s ease; }
.good { transition: transform 0.3s ease, opacity 0.3s ease; }

/* ANIMATIONS: for autonomous, looping, or complex sequences */
.spinner {
  animation: spin 1s linear infinite; /* doesn't need a trigger */
}

.notification-badge {
  animation: pulse 2s ease-in-out infinite; /* always running */
}
```

**When to use which:**
| Scenario | Use |
|----------|-----|
| Hover/focus state change | Transition |
| Looping animation | Animation |
| Multi-step sequence | Animation |
| Playing on page load | Animation |
| Triggered by JS | Animation (toggle class) |

---

## Step 4: will-change

```css
/* Hint browser to create compositor layer BEFORE animation starts */
/* Improves performance for complex animations */

/* ✓ Good: use will-change before animation is needed */
.card {
  will-change: transform; /* prepare for upcoming animation */
}

.card:hover {
  transform: translateY(-4px);
  transition: transform 0.2s ease;
}

/* Remove will-change after animation completes (via JS) */
element.addEventListener('animationend', () => {
  element.style.willChange = 'auto';
});

/* ❌ Don't will-change everything — creates memory overhead */
/* ❌ Don't will-change: all */

/* Compositable properties (GPU accelerated): */
/* - transform: translate(), scale(), rotate() */
/* - opacity */
/* - filter */
/* - will-change itself */
```

---

## Step 5: CSS Motion Path (`offset-path`)

```css
/* Move an element along a path */
@keyframes move-along-path {
  from { offset-distance: 0%; }
  to   { offset-distance: 100%; }
}

.follower {
  offset-path: path('M 10,80 Q 100,10 190,80 T 370,80'); /* SVG path */
  offset-rotate: auto; /* rotate to follow path direction */
  animation: move-along-path 3s ease-in-out infinite alternate;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: red;
}

/* Path types */
.element {
  /* SVG path string */
  offset-path: path('M0,0 C100,0 200,100 300,100');
  
  /* Geometric shapes */
  offset-path: circle(50% at 50% 50%);
  offset-path: ellipse(200px 100px at 50% 50%);
  
  /* URL to SVG path element */
  offset-path: url('#my-svg-path');
}
```

---

## Step 6: Cubic-Bezier Timing Functions

```css
/* Built-in easing keywords */
animation-timing-function: linear;      /* constant speed */
animation-timing-function: ease;        /* slow→fast→slow (default) */
animation-timing-function: ease-in;     /* slow start */
animation-timing-function: ease-out;    /* slow end ✓ for entrances */
animation-timing-function: ease-in-out; /* slow both ends */

/* Custom cubic-bezier(x1, y1, x2, y2) */
/* Use https://cubic-bezier.com to visualize */
animation-timing-function: cubic-bezier(0.25, 0.46, 0.45, 0.94); /* ease-out-quad */
animation-timing-function: cubic-bezier(0.34, 1.56, 0.64, 1);    /* spring/overshoot */
animation-timing-function: cubic-bezier(0.87, 0, 0.13, 1);       /* very sharp ease */

/* Stepped animations */
animation-timing-function: steps(4, end);   /* 4 discrete steps */
animation-timing-function: steps(1, start); /* flip immediately */
animation-timing-function: step-start;      /* = steps(1, start) */
animation-timing-function: step-end;        /* = steps(1, end) */

/* Per-keyframe timing */
@keyframes complex {
  0%   { transform: translateX(0); animation-timing-function: ease-in; }
  50%  { transform: translateX(100px); animation-timing-function: ease-out; }
  100% { transform: translateX(80px); }
}
```

---

## Step 7: prefers-reduced-motion

```css
/* Always provide reduced-motion alternatives */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.animated-element {
  animation: fadeIn 0.4s ease-out forwards;
}

/* Remove or simplify animations for users who request it */
@media (prefers-reduced-motion: reduce) {
  .animated-element {
    animation: fadeIn 0.01s; /* instant, but still fires 'animationend' */
  }
  
  /* Or disable completely */
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Better pattern: opt-in animations */
@media (prefers-reduced-motion: no-preference) {
  .animated-element {
    animation: fadeIn 0.4s ease-out forwards;
  }
}
```

---

## Step 8: Capstone — Timing Function Calculator

```bash
docker run --rm node:20-alpine node -e "
function cubicBezier(t, p1x, p1y, p2x, p2y) {
  var cx = 3*p1x, bx = 3*(p2x-p1x)-cx, ax = 1-cx-bx;
  var cy = 3*p1y, by = 3*(p2y-p1y)-cy, ay = 1-cy-by;
  function sampleY(t){ return ((ay*t+by)*t+cy)*t; }
  return sampleY(t).toFixed(4);
}
var eases = {'ease':'0.25,0.1,0.25,1','ease-in':'0.42,0,1,1','ease-out':'0,0,0.58,1','ease-in-out':'0.42,0,0.58,1'};
Object.keys(eases).forEach(function(name){
  var v = eases[name].split(',').map(Number);
  var mid = cubicBezier(0.5, v[0],v[1],v[2],v[3]);
  console.log(name + ': at t=0.5 => ' + mid + ' (cubic-bezier(' + eases[name] + '))');
});
"
```

📸 **Verified Output:**
```
ease: at t=0.5 => 0.5375 (cubic-bezier(0.25,0.1,0.25,1))
ease-in: at t=0.5 => 0.5000 (cubic-bezier(0.42,0,1,1))
ease-out: at t=0.5 => 0.5000 (cubic-bezier(0,0,0.58,1))
ease-in-out: at t=0.5 => 0.5000 (cubic-bezier(0.42,0,0.58,1))
```

---

## Summary

| Property | Key Values | Purpose |
|----------|-----------|---------|
| `animation-name` | `@keyframes` name | Which animation |
| `animation-duration` | `0.3s`, `500ms` | How long |
| `animation-timing-function` | `ease-out`, `cubic-bezier()` | Speed curve |
| `animation-delay` | `0.1s` | Wait before start |
| `animation-iteration-count` | `1`, `infinite` | How many times |
| `animation-direction` | `alternate`, `reverse` | Forward/backward |
| `animation-fill-mode` | `forwards`, `both` | State after end |
| `animation-play-state` | `paused`, `running` | Pause/resume |
| `will-change` | `transform`, `opacity` | GPU layer hint |
| `offset-path` | `path(...)` | Motion along path |
| `prefers-reduced-motion` | `reduce`, `no-preference` | Accessibility |
