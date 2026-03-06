# Lab 08: HTML5 APIs

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Explore the browser Observer APIs (Intersection, Resize, Mutation), Web Storage (localStorage/sessionStorage), and Custom Elements. These APIs enable performant, declarative web applications without polling.

---

## Step 1: Intersection Observer

Detect when elements enter/exit the viewport without scroll event listeners:

```javascript
// Basic usage
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target); // stop watching once visible
    }
  });
});

document.querySelectorAll('.animate-on-scroll').forEach(el => {
  observer.observe(el);
});

// With options
const lazyObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;  // load image
      img.removeAttribute('data-src');
      lazyObserver.unobserve(img);
    }
  });
}, {
  root: null,          // null = viewport
  rootMargin: '0px 0px -100px 0px',  // trigger 100px before bottom edge
  threshold: 0.1       // 10% visible triggers callback
});

// Multiple thresholds
const progressObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    // entry.intersectionRatio: 0.0 to 1.0
    entry.target.style.opacity = entry.intersectionRatio;
  });
}, {
  threshold: [0, 0.1, 0.25, 0.5, 0.75, 1.0]
});
```

> 💡 The `rootMargin` uses CSS shorthand (top right bottom left). Negative values shrink the intersection area, positive values expand it.

---

## Step 2: Resize Observer

React to element size changes:

```javascript
const resizeObserver = new ResizeObserver((entries) => {
  entries.forEach(entry => {
    const { width, height } = entry.contentRect;
    
    // Component-level responsive behavior
    if (width < 400) {
      entry.target.classList.add('compact');
      entry.target.classList.remove('expanded');
    } else {
      entry.target.classList.add('expanded');
      entry.target.classList.remove('compact');
    }
    
    // Access the border box
    const [boxSize] = entry.borderBoxSize;
    console.log('Border box width:', boxSize.inlineSize);
    console.log('Border box height:', boxSize.blockSize);
  });
});

resizeObserver.observe(document.querySelector('.responsive-component'));

// Observe multiple elements
document.querySelectorAll('.chart-container').forEach(el => {
  resizeObserver.observe(el);
});

// Stop observing
resizeObserver.unobserve(element);
resizeObserver.disconnect(); // stop all observations
```

---

## Step 3: Mutation Observer

Watch for DOM changes:

```javascript
const mutationObserver = new MutationObserver((mutations) => {
  mutations.forEach(mutation => {
    if (mutation.type === 'childList') {
      // nodes added/removed
      mutation.addedNodes.forEach(node => {
        console.log('Added:', node);
      });
      mutation.removedNodes.forEach(node => {
        console.log('Removed:', node);
      });
    }
    
    if (mutation.type === 'attributes') {
      console.log(`Attribute ${mutation.attributeName} changed`);
      console.log('Old value:', mutation.oldValue);
      console.log('New value:', mutation.target.getAttribute(mutation.attributeName));
    }
    
    if (mutation.type === 'characterData') {
      console.log('Text changed:', mutation.target.textContent);
    }
  });
});

// Observe configuration
mutationObserver.observe(document.body, {
  childList: true,        // direct children added/removed
  subtree: true,          // all descendants
  attributes: true,       // attribute changes
  attributeOldValue: true, // capture old attribute value
  characterData: true,    // text content changes
  characterDataOldValue: true,
  attributeFilter: ['class', 'data-state'], // only watch specific attributes
});

mutationObserver.disconnect();
```

---

## Step 4: Web Storage

```javascript
// localStorage: persists across browser sessions
localStorage.setItem('theme', 'dark');
localStorage.setItem('user', JSON.stringify({ name: 'Alice', age: 30 }));

const theme = localStorage.getItem('theme');          // 'dark'
const user  = JSON.parse(localStorage.getItem('user')); // { name: 'Alice' }
const missing = localStorage.getItem('nonexistent'); // null

localStorage.removeItem('theme');
localStorage.clear(); // remove ALL items for this origin

// Check storage
console.log('Items stored:', localStorage.length);
for (let i = 0; i < localStorage.length; i++) {
  const key = localStorage.key(i);
  console.log(key, ':', localStorage.getItem(key));
}

// sessionStorage: cleared when tab/window closes
sessionStorage.setItem('draft', JSON.stringify(formData));
const draft = JSON.parse(sessionStorage.getItem('draft'));

// Storage event: fires in OTHER tabs/windows when storage changes
window.addEventListener('storage', (event) => {
  if (event.key === 'theme') {
    applyTheme(event.newValue);
  }
});

// Safe storage helper
const storage = {
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch { return defaultValue; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); }
    catch (e) { console.warn('Storage full:', e); }
  },
  remove(key) { localStorage.removeItem(key); }
};
```

---

## Step 5: Custom Elements

```javascript
// Define a custom element
class UserCard extends HTMLElement {
  // Which attributes to watch
  static get observedAttributes() {
    return ['name', 'avatar', 'role'];
  }
  
  constructor() {
    super();
    // Don't touch DOM here — not connected yet
  }
  
  // Element added to DOM
  connectedCallback() {
    this.render();
  }
  
  // Element removed from DOM
  disconnectedCallback() {
    // cleanup: remove event listeners, cancel timers
  }
  
  // Attribute changed
  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      this.render(); // re-render when attribute changes
    }
  }
  
  // Element moved to new document
  adoptedCallback() {
    // rarely needed
  }
  
  render() {
    const name = this.getAttribute('name') || 'Unknown';
    const avatar = this.getAttribute('avatar') || '';
    const role = this.getAttribute('role') || 'Member';
    
    this.innerHTML = `
      <div class="user-card">
        <img src="${avatar}" alt="${name}" width="48" height="48">
        <div class="user-card__info">
          <strong>${name}</strong>
          <span>${role}</span>
        </div>
      </div>
    `;
  }
}

// Register: name must contain a hyphen
customElements.define('user-card', UserCard);

// Usage in HTML:
// <user-card name="Alice" avatar="/alice.jpg" role="Admin"></user-card>

// Wait for definition
customElements.whenDefined('user-card').then(() => {
  console.log('user-card is defined');
});

// Upgrade existing elements
customElements.upgrade(document.querySelector('user-card'));
```

---

## Step 6: Template & Slot (for Custom Elements)

```html
<template id="card-template">
  <style>
    .card { border: 1px solid #ddd; border-radius: 8px; padding: 1rem; }
    .card__title { font-size: 1.25rem; margin: 0; }
  </style>
  <div class="card">
    <h2 class="card__title">
      <slot name="title">Default Title</slot>
    </h2>
    <div class="card__body">
      <slot>Default content</slot>
    </div>
  </div>
</template>
```

```javascript
class MyCard extends HTMLElement {
  constructor() {
    super();
    const shadow = this.attachShadow({ mode: 'open' });
    const template = document.getElementById('card-template');
    shadow.appendChild(template.content.cloneNode(true));
  }
}
customElements.define('my-card', MyCard);
```

```html
<my-card>
  <span slot="title">Custom Title</span>
  <p>This is the card body content</p>
</my-card>
```

---

## Step 7: Practical Patterns

```javascript
// Lazy loading with IntersectionObserver
document.querySelectorAll('img[data-src]').forEach(img => {
  const io = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) {
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      io.disconnect();
    }
  }, { rootMargin: '200px' });
  io.observe(img);
});

// Infinite scroll
const sentinel = document.querySelector('#load-more-sentinel');
new IntersectionObserver(([entry]) => {
  if (entry.isIntersecting) loadMoreItems();
}).observe(sentinel);

// Animate counters when visible
document.querySelectorAll('[data-counter]').forEach(el => {
  new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) {
      animateCounter(el, 0, parseInt(el.dataset.counter), 2000);
    }
  }, { threshold: 0.5 }).observe(el);
});
```

---

## Step 8: Capstone — jsdom API Simulation

```bash
cd /tmp && npm init -y 2>/dev/null | grep name
npm install jsdom 2>/dev/null | tail -1
node -e "
const { JSDOM } = require('/tmp/node_modules/jsdom');
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {url:'http://localhost'});
const {window} = dom;
const {document} = window;

window.localStorage.setItem('theme', 'dark');
window.localStorage.setItem('lang', 'en');
console.log('localStorage theme:', window.localStorage.getItem('theme'));
console.log('localStorage length:', window.localStorage.length);
window.localStorage.removeItem('lang');
console.log('After removeItem length:', window.localStorage.length);
document.body.innerHTML = '<p id=test>Hello World</p>';
console.log('querySelector #test:', document.querySelector('#test').textContent);
class MockIO { constructor(cb){this.cb=cb;} observe(el){console.log('Observing:', el.tagName);} disconnect(){} }
window.IntersectionObserver = MockIO;
var io = new window.IntersectionObserver(function(entries){});
io.observe(document.body);
console.log('jsdom HTML5 API simulation: PASS');
"
```

📸 **Verified Output:**
```
"name": "tmp"
found 0 vulnerabilities
localStorage theme: dark
localStorage length: 2
After removeItem length: 1
querySelector #test: Hello World
Observing: BODY
jsdom HTML5 API simulation: PASS
```

---

## Summary

| API | Constructor | Key Methods |
|-----|-------------|-------------|
| IntersectionObserver | `new IntersectionObserver(cb, opts)` | `observe()`, `unobserve()`, `disconnect()` |
| ResizeObserver | `new ResizeObserver(cb)` | `observe()`, `unobserve()`, `disconnect()` |
| MutationObserver | `new MutationObserver(cb)` | `observe(el, config)`, `disconnect()` |
| localStorage | Built-in | `setItem()`, `getItem()`, `removeItem()`, `clear()` |
| sessionStorage | Built-in | Same as localStorage |
| Custom Elements | `customElements.define()` | `connectedCallback`, `disconnectedCallback`, `attributeChangedCallback` |
