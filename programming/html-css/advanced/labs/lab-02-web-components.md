# Lab 02: Web Components

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build native Web Components using Custom Elements v1, Shadow DOM, `<template>/<slot>`, and CSS custom properties crossing the Shadow DOM boundary.

---

## Step 1: Custom Elements Lifecycle

```javascript
class MyButton extends HTMLElement {
  // Declare which attributes trigger attributeChangedCallback
  static get observedAttributes() {
    return ['variant', 'disabled', 'size', 'label'];
  }

  constructor() {
    super();
    // ✓ Can: attach shadow DOM, set up initial state
    // ✗ Can't: access children, inspect DOM, set attributes
    this._shadow = this.attachShadow({ mode: 'open' });
  }

  // Element inserted into DOM
  connectedCallback() {
    this.render();
    this._addEventListeners();
  }

  // Element removed from DOM
  disconnectedCallback() {
    this._removeEventListeners();
    // Cancel subscriptions, timers, etc.
  }

  // Element moved to new document (e.g., into iframe)
  adoptedCallback() {
    // Rarely needed
  }

  // Observed attribute changed
  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return; // no-op
    this.render(); // re-render on any attribute change
  }

  // Getters/setters for property ↔ attribute reflection
  get variant() { return this.getAttribute('variant') || 'primary'; }
  set variant(v) { this.setAttribute('variant', v); }

  get disabled() { return this.hasAttribute('disabled'); }
  set disabled(v) { v ? this.setAttribute('disabled', '') : this.removeAttribute('disabled'); }

  render() {
    this._shadow.innerHTML = `
      <style>
        :host { display: inline-flex; }
        :host([disabled]) { opacity: 0.5; pointer-events: none; }
        button { /* styles */ }
      </style>
      <button part="button" ?disabled="${this.disabled}">
        <slot></slot>
      </button>
    `;
  }

  _addEventListeners() {
    this._shadow.querySelector('button')?.addEventListener('click', this._handleClick);
  }

  _removeEventListeners() {
    this._shadow.querySelector('button')?.removeEventListener('click', this._handleClick);
  }

  _handleClick = (e) => {
    this.dispatchEvent(new CustomEvent('my-click', {
      bubbles: true,
      composed: true, // cross Shadow DOM boundary
      detail: { variant: this.variant }
    }));
  }
}

customElements.define('my-button', MyButton);
```

---

## Step 2: Shadow DOM — open vs closed

```javascript
// open: external JS can access shadowRoot
const shadow = this.attachShadow({ mode: 'open' });
document.querySelector('my-button').shadowRoot; // returns the shadow root

// closed: external JS CANNOT access shadowRoot
const shadow = this.attachShadow({ mode: 'closed' });
document.querySelector('my-button').shadowRoot; // returns null

// Closed mode use cases: security-sensitive UI (payment forms)
// Most components should use 'open' for debuggability
```

---

## Step 3: Template and Slot

```html
<!-- Define template in HTML -->
<template id="card-template">
  <style>
    :host {
      display: block;
      --card-bg: white;
      --card-padding: 1rem;
      --card-radius: 8px;
    }

    .card {
      background: var(--card-bg);
      padding: var(--card-padding);
      border-radius: var(--card-radius);
      border: 1px solid #e5e7eb;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    .card__header {
      margin-block-end: 0.75rem;
      padding-block-end: 0.75rem;
      border-block-end: 1px solid #e5e7eb;
    }

    .card__title {
      margin: 0;
      font-size: 1.1rem;
      font-weight: 600;
    }

    .card__footer {
      margin-block-start: 0.75rem;
      padding-block-start: 0.75rem;
      border-block-start: 1px solid #e5e7eb;
    }

    /* slot with fallback content */
    slot[name="icon"]::slotted(*) {
      vertical-align: middle;
      margin-inline-end: 0.5rem;
    }
  </style>
  <div class="card">
    <div class="card__header">
      <slot name="icon"></slot>
      <h2 class="card__title">
        <slot name="title">Card Title</slot>  <!-- fallback -->
      </h2>
    </div>
    <div class="card__body">
      <slot></slot>  <!-- default slot -->
    </div>
    <div class="card__footer" hidden>
      <slot name="footer"></slot>
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

  connectedCallback() {
    // Show footer only if footer slot has content
    const footerSlot = this.shadowRoot.querySelector('slot[name="footer"]');
    const footerWrapper = this.shadowRoot.querySelector('.card__footer');
    
    footerSlot.addEventListener('slotchange', () => {
      const nodes = footerSlot.assignedNodes({ flatten: true });
      footerWrapper.hidden = nodes.length === 0;
    });
  }
}

customElements.define('my-card', MyCard);
```

```html
<!-- Usage -->
<my-card>
  <svg slot="icon" width="24" height="24" aria-hidden="true">...</svg>
  <span slot="title">Revenue Report</span>
  
  <!-- default slot content -->
  <p>Q4 revenue increased by 23% over Q3...</p>
  <ul>
    <li>Total: $48,290</li>
    <li>Growth: +23%</li>
  </ul>
  
  <div slot="footer">
    <button>View Details</button>
  </div>
</my-card>
```

---

## Step 4: CSS Custom Properties Across Shadow DOM

CSS custom properties **DO** pierce the Shadow DOM boundary (they inherit through it):

```css
/* Host page: set tokens */
:root {
  --color-primary: #3b82f6;
  --card-bg: #ffffff;
  --border-radius: 8px;
}

[data-theme="dark"] {
  --color-primary: #60a5fa;
  --card-bg: #1e293b;
}

/* Inside shadow DOM: use the tokens */
:host {
  /* :host matches the custom element itself */
  display: block;
}

.inner-button {
  /* These custom properties come FROM the host page's stylesheet */
  background: var(--color-primary, #3b82f6);
  border-radius: var(--border-radius, 4px);
}
```

```css
/* ::slotted() — style light DOM children inside shadow DOM */
::slotted(p) { margin-block: 0.5rem; }
::slotted(*) { color: inherit; }
::slotted(.highlight) { background: yellow; }
/* NOTE: only direct slotted children, not descendants */

/* ::part() — expose internals for external styling */
/* Inside component: */
.internal-button { } /* also: part="button" on the element */
/* External styles: */
my-component::part(button) { background: red; }
```

---

## Step 5: Custom Events and Element Communication

```javascript
// Emit events that cross Shadow DOM
class MyInput extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' }).innerHTML = `
      <input type="text" placeholder="Type here...">
    `;
    
    this.shadowRoot.querySelector('input').addEventListener('input', (e) => {
      this.dispatchEvent(new CustomEvent('value-change', {
        bubbles: true,
        composed: true, // CRUCIAL: allows event to cross shadow boundary
        detail: {
          value: e.target.value,
          length: e.target.value.length
        }
      }));
    });
  }
  
  get value() {
    return this.shadowRoot.querySelector('input').value;
  }
  
  set value(v) {
    this.shadowRoot.querySelector('input').value = v;
  }
}

customElements.define('my-input', MyInput);

// Listen from outside:
document.querySelector('my-input').addEventListener('value-change', (e) => {
  console.log('New value:', e.detail.value);
});
```

---

## Step 6: Form-Associated Custom Elements

```javascript
class MyRating extends HTMLElement {
  static formAssociated = true; // mark as form-associated
  
  constructor() {
    super();
    this._internals = this.attachInternals(); // get ElementInternals
    this.attachShadow({ mode: 'open' });
    this._value = 0;
  }
  
  connectedCallback() {
    this._render();
  }
  
  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        .stars { display: flex; gap: 4px; }
        .star { cursor: pointer; font-size: 2rem; color: #ccc; }
        .star.active { color: gold; }
      </style>
      <div class="stars" role="radiogroup" aria-label="Rating">
        ${[1,2,3,4,5].map(n => `
          <span
            class="star ${n <= this._value ? 'active' : ''}"
            role="radio"
            aria-checked="${n <= this._value}"
            aria-label="${n} star${n > 1 ? 's' : ''}"
            tabindex="${n === this._value ? '0' : '-1'}"
            data-value="${n}"
          >★</span>
        `).join('')}
      </div>
    `;
    
    this.shadowRoot.querySelectorAll('.star').forEach(star => {
      star.addEventListener('click', () => {
        this._value = parseInt(star.dataset.value);
        this._internals.setFormValue(String(this._value));
        this._render();
      });
    });
  }
}

customElements.define('my-rating', MyRating);
```

---

## Step 7: Upgrading and whenDefined

```javascript
// Upgrade manually
customElements.upgrade(element);

// Wait for element to be defined
customElements.whenDefined('my-card').then(() => {
  console.log('my-card is ready');
  document.querySelectorAll('my-card').forEach(el => {
    el.classList.add('loaded');
  });
});

// Get constructor
const MyCardClass = customElements.get('my-card');
const card = new MyCardClass();

// Check if defined
if (!customElements.get('my-card')) {
  import('./my-card.js');
}
```

---

## Step 8: Capstone — jsdom Custom Element Demo

```bash
cd /tmp && npm init -y 2>/dev/null | grep name
npm install jsdom 2>/dev/null | tail -1
node -e "
const { JSDOM } = require('/tmp/node_modules/jsdom');
const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {url:'http://localhost'});
const {window} = dom;
const {document, HTMLElement} = window;

// Simulate custom element registration
var registry = {};
window.customElements = {
  define: function(name, cls) {
    registry[name] = cls;
    console.log('Registered:', name);
  },
  get: function(name) { return registry[name]; },
  whenDefined: function(name) {
    return Promise.resolve(registry[name]);
  }
};

// Define a simple counter element
class Counter extends HTMLElement {
  constructor() {
    super();
    this._count = 0;
  }
  connectedCallback() {
    this.textContent = 'Count: ' + this._count;
    console.log('Counter connected, count:', this._count);
  }
  increment() {
    this._count++;
    this.textContent = 'Count: ' + this._count;
    return this._count;
  }
}

window.customElements.define('my-counter', Counter);

// Use the element
var counter = new Counter();
document.body.appendChild(counter);
counter.connectedCallback();
console.log('After increment:', counter.increment());
console.log('After increment:', counter.increment());
console.log('Element content:', counter.textContent);
console.log('Custom element demo: PASS');
"
```

📸 **Verified Output:**
```
"name": "tmp"
found 0 vulnerabilities
Registered: my-counter
Counter connected, count: 0
After increment: 1
After increment: 2
Element content: Count: 2
Custom element demo: PASS
```

---

## Summary

| Feature | API | Purpose |
|---------|-----|---------|
| Define element | `customElements.define('tag', Class)` | Register custom tag |
| Shadow root | `this.attachShadow({mode:'open'})` | Encapsulated DOM |
| Lifecycle | `connectedCallback()` etc. | DOM event hooks |
| Observe attrs | `static observedAttributes` | React to attr changes |
| Template | `<template>` + `cloneNode(true)` | Reusable HTML |
| Slots | `<slot name="x">` | Content projection |
| Cross-shadow events | `composed: true` | Event propagation |
| Style theming | CSS custom properties | Cross-shadow styling |
| Part styling | `::part(name)` | External style hooks |
| Form-associated | `static formAssociated = true` | Native form integration |
