# Lab 08: Animation Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Enterprise animation system: CSS custom property animation tokens, scroll-driven animations with `animation-timeline`, View Transitions API, `prefers-reduced-motion` patterns, and the FLIP (First, Last, Invert, Play) animation technique.

---

## Step 1: Animation Token System

```css
/* tokens/animation.css */
:root {
  /* Duration tokens */
  --duration-instant:  0ms;
  --duration-fast:     100ms;
  --duration-normal:   200ms;
  --duration-slow:     400ms;
  --duration-slower:   700ms;
  --duration-slowest:  1000ms;

  /* Easing tokens (Material Design 3) */
  --easing-standard:    cubic-bezier(0.2, 0, 0, 1);
  --easing-decelerate:  cubic-bezier(0, 0, 0.2, 1);    /* Enter */
  --easing-accelerate:  cubic-bezier(0.4, 0, 1, 1);    /* Exit */
  --easing-sharp:       cubic-bezier(0.4, 0, 0.6, 1);  /* Attention */
  --easing-spring:      cubic-bezier(0.175, 0.885, 0.32, 1.275);

  /* Composite tokens */
  --transition-fade:    opacity var(--duration-normal) var(--easing-standard);
  --transition-slide:   transform var(--duration-normal) var(--easing-decelerate);
  --transition-scale:   transform var(--duration-fast) var(--easing-spring);
  --transition-color:   color var(--duration-fast) var(--easing-standard),
                        background-color var(--duration-fast) var(--easing-standard);
}

/* Respect user preferences */
@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-fast:    0ms;
    --duration-normal:  0ms;
    --duration-slow:    0ms;
    --duration-slower:  0ms;
    --duration-slowest: 0ms;
    /* Easing irrelevant when duration is 0 */
  }
}
```

> 💡 Setting duration tokens to `0ms` under `prefers-reduced-motion` means every component using tokens automatically respects the preference — no individual component changes needed.

---

## Step 2: Scroll-Driven Animations

```css
/* animation-timeline: scroll() — tied to scroll position */
@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(2rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.reveal-on-scroll {
  animation: fade-in-up linear both;
  animation-timeline: view();
  /* animation-range: 0% cover 25% */
  animation-range: entry 0% entry 50%;
}

/* Sticky header progress bar — tied to document scroll */
.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: var(--color-primary);
  transform-origin: left;
  animation: grow-width linear;
  animation-timeline: scroll(root block);
}

@keyframes grow-width {
  from { transform: scaleX(0); }
  to   { transform: scaleX(1); }
}

/* Parallax using scroll() */
.hero-image {
  animation: parallax linear both;
  animation-timeline: scroll(root);
}
@keyframes parallax {
  from { transform: translateY(-20%); }
  to   { transform: translateY(20%); }
}
```

---

## Step 3: View Transitions API

```css
/* View Transitions — smooth page-to-page transitions */
/* Step 1: Default cross-fade (free) */
/* Just calling document.startViewTransition() gets this */

/* Step 2: Named elements — persistent across transition */
.product-card {
  view-transition-name: var(--card-id); /* Must be unique per page */
}

/* Step 3: Custom animations for old/new states */
::view-transition-old(product-card) {
  animation: slide-out-left var(--duration-normal) var(--easing-accelerate) both;
}

::view-transition-new(product-card) {
  animation: slide-in-right var(--duration-normal) var(--easing-decelerate) both;
}

/* Global page transition */
::view-transition-old(root) {
  animation: fade-out var(--duration-fast) var(--easing-standard) both;
}

::view-transition-new(root) {
  animation: fade-in var(--duration-normal) var(--easing-decelerate) both;
}

@keyframes fade-out  { to { opacity: 0; } }
@keyframes fade-in   { from { opacity: 0; } }
@keyframes slide-out-left  { to { transform: translateX(-20px); opacity: 0; } }
@keyframes slide-in-right  { from { transform: translateX(20px); opacity: 0; } }
```

```javascript
// Trigger view transition
async function navigateTo(url) {
  if (!document.startViewTransition) {
    location.href = url;
    return;
  }

  const transition = document.startViewTransition(async () => {
    const html = await fetch(url).then(r => r.text());
    document.documentElement.innerHTML = parseHTML(html);
  });

  await transition.finished;
}
```

---

## Step 4: FLIP Animation Technique

```javascript
/**
 * FLIP: First, Last, Invert, Play
 * Animate elements smoothly even when layout changes
 */
class FlipAnimation {
  static animate(element, callback, options = {}) {
    const { duration = 300, easing = 'cubic-bezier(0.2, 0, 0, 1)' } = options;

    // FIRST: Record initial position
    const first = element.getBoundingClientRect();

    // Perform DOM change synchronously
    callback();

    // LAST: Record final position
    const last = element.getBoundingClientRect();

    // INVERT: Calculate delta
    const deltaX = first.left - last.left;
    const deltaY = first.top  - last.top;
    const deltaW = first.width / last.width;
    const deltaH = first.height / last.height;

    // Skip if no movement
    if (deltaX === 0 && deltaY === 0 && deltaW === 1 && deltaH === 1) return;

    // PLAY: Animate from inverted position to natural position
    element.animate([
      {
        transformOrigin: 'top left',
        transform: `translate(${deltaX}px, ${deltaY}px) scale(${deltaW}, ${deltaH})`,
      },
      {
        transformOrigin: 'top left',
        transform: 'none',
      },
    ], { duration, easing, fill: 'both' });
  }
}

// Usage: animate card from list position to grid position
FlipAnimation.animate(card, () => {
  container.classList.toggle('grid-view');
});
```

---

## Step 5: Reduced Motion Safe Patterns

```css
/* Pattern 1: Use @media query directly */
.animated-element {
  animation: slide-up 300ms ease-out;
}

@media (prefers-reduced-motion: reduce) {
  .animated-element {
    animation: fade-in 150ms ease-out; /* Replace movement with fade */
  }
}

/* Pattern 2: Token-based (preferred — covered in Step 1) */
.animated-element {
  transition: var(--transition-slide);
}

/* Pattern 3: JavaScript feature detection */
/* const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches; */
```

```javascript
// WAAPI: Respect reduced motion
function animateElement(el, keyframes, options) {
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (prefersReduced) {
    // Jump to final state immediately
    el.animate(keyframes, { duration: 0, fill: 'forwards' });
    return;
  }

  return el.animate(keyframes, options);
}
```

---

## Step 6: Stagger and Orchestration

```css
/* CSS stagger using --i custom property */
.list-item {
  animation: fade-in-up var(--duration-normal) var(--easing-decelerate) both;
  animation-delay: calc(var(--i, 0) * 50ms);
}

/* Set via HTML attribute or JS */
/* <li style="--i: 0">, <li style="--i: 1">, ... */
```

```javascript
// JS orchestration
const items = document.querySelectorAll('.list-item');
items.forEach((item, i) => {
  item.style.setProperty('--i', i);
});

// Parallel + sequential with Web Animations API
const timeline = document.timeline;
async function runSequence(elements) {
  for (const el of elements) {
    const anim = el.animate(
      [{ opacity: 0, transform: 'translateY(8px)' }, { opacity: 1, transform: 'none' }],
      { duration: 200, easing: 'ease-out', fill: 'both' }
    );
    await anim.finished;
  }
}
```

---

## Step 7: CSS Registered Custom Properties for Animation

```css
/* Register for interpolation (enables CSS transitions on custom properties) */
/* In JS: CSS.registerProperty({ name, syntax, inherits, initialValue }) */

/* Or via @property */
@property --progress {
  syntax: '<number>';
  initial-value: 0;
  inherits: false;
}

.progress-ring {
  /* --progress can now be transitioned! */
  transition: --progress 500ms ease;
}
```

---

## Step 8: Capstone — Animation Token Generator

```bash
docker run --rm node:20-alpine node -e "
const tokens = {
  duration: { fast: '100ms', normal: '200ms', slow: '400ms', slower: '700ms' },
  easing: {
    standard: 'cubic-bezier(0.2, 0, 0, 1)',
    decelerate: 'cubic-bezier(0, 0, 0.2, 1)',
    accelerate: 'cubic-bezier(0.4, 0, 1, 1)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
    spring: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
  }
};
console.log('=== Animation Token CSS Custom Properties ===');
console.log(':root {');
Object.entries(tokens.duration).forEach(([k,v]) => console.log('  --duration-'+k+': '+v+';'));
Object.entries(tokens.easing).forEach(([k,v]) => console.log('  --easing-'+k+': '+v+';'));
console.log('}');
"
```

📸 **Verified Output:**
```
=== Animation Token CSS Custom Properties ===
:root {
  --duration-fast: 100ms;
  --duration-normal: 200ms;
  --duration-slow: 400ms;
  --duration-slower: 700ms;
  --easing-standard: cubic-bezier(0.2, 0, 0, 1);
  --easing-decelerate: cubic-bezier(0, 0, 0.2, 1);
  --easing-accelerate: cubic-bezier(0.4, 0, 1, 1);
  --easing-sharp: cubic-bezier(0.4, 0, 0.6, 1);
  --easing-spring: cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
```

---

## Summary

| Technique | API | Use Case |
|-----------|-----|----------|
| Token system | CSS custom properties | Consistent timing |
| Reduced motion | Duration = 0ms | Accessibility compliance |
| Scroll-driven | `animation-timeline: scroll()` | No JS scroll listeners |
| View transitions | `startViewTransition()` | Page-level animations |
| Named transitions | `view-transition-name` | Shared element animation |
| FLIP | getBoundingClientRect delta | Layout-change animations |
| Stagger | `--i * 50ms` delay | List entrance effects |
| Registered props | `@property` | Transition custom values |
