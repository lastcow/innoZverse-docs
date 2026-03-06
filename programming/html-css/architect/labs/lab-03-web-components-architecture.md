# Lab 03: Web Components Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Build production-grade Web Components using vanilla Custom Elements v1 API: Shadow DOM, slots, `::part()`, CSS custom properties crossing the shadow boundary, element registry collision detection, and component composition patterns — no framework dependencies.

---

## Step 1: Custom Element Lifecycle

```javascript
class DsButton extends HTMLElement {
  // Observed attributes trigger attributeChangedCallback
  static get observedAttributes() {
    return ['variant', 'size', 'disabled', 'loading'];
  }

  constructor() {
    super();
    // Always call super() first
    this._shadow = this.attachShadow({ mode: 'open' });
    this._state = { loading: false };
  }

  // Lifecycle: element added to DOM
  connectedCallback() {
    this._render();
    this._setupEventListeners();
  }

  // Lifecycle: element removed from DOM
  disconnectedCallback() {
    this._cleanup();
  }

  // Lifecycle: element moved to new document
  adoptedCallback() {
    console.log('Element adopted into new document');
  }

  // Lifecycle: observed attribute changed
  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue === newValue) return;
    if (name === 'loading') this._state.loading = newValue !== null;
    this._render();
  }
}
```

---

## Step 2: Shadow DOM — Slots and Parts

```javascript
_render() {
  this._shadow.innerHTML = `
    <style>
      :host {
        display: inline-flex;
        /* CSS custom props cross shadow boundary */
        --_bg: var(--ds-btn-bg, #3b82f6);
        --_color: var(--ds-btn-color, white);
        --_radius: var(--ds-btn-radius, 0.375rem);
      }
      :host([variant="secondary"]) {
        --_bg: var(--ds-btn-secondary-bg, #f1f5f9);
        --_color: var(--ds-btn-secondary-color, #1e293b);
      }
      :host([disabled]) {
        opacity: 0.5;
        pointer-events: none;
        cursor: not-allowed;
      }

      /* ::part() — expose styled elements to outside */
      button {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: var(--_bg);
        color: var(--_color);
        border: none;
        border-radius: var(--_radius);
        padding: var(--ds-btn-padding, 0.5rem 1rem);
        font-size: var(--ds-btn-font-size, 1rem);
        cursor: pointer;
        transition: opacity 150ms ease;
      }

      /* Slots */
      ::slotted([slot="icon-start"]) {
        width: 1.25em;
        height: 1.25em;
      }
    </style>

    <button part="base" role="button" aria-busy="${this._state.loading}">
      <slot name="icon-start"></slot>
      <slot></slot>
      <slot name="icon-end"></slot>
    </button>
  `;
}
```

```css
/* Outside component: styling via ::part() */
ds-button::part(base) {
  font-weight: 600;
  letter-spacing: 0.025em;
}

/* Override via CSS custom properties */
.danger-zone ds-button {
  --ds-btn-bg: #ef4444;
  --ds-btn-color: white;
}
```

> 💡 CSS custom properties **do** cross the shadow boundary (they inherit). `::part()` provides a controlled styling API. Never pierce the shadow DOM with `/deep/` or `>>>` — they're deprecated.

---

## Step 3: Element Registry with Collision Detection

```javascript
// registry.js — safe registration
class ComponentRegistry {
  static #registered = new Map();

  static define(name, constructor, options = {}) {
    // Check for collision
    if (customElements.get(name)) {
      const existing = this.#registered.get(name);
      if (existing === constructor) {
        console.warn(`[Registry] ${name} already registered with same constructor`);
        return;
      }
      throw new Error(
        `[Registry] Collision: "${name}" already registered by ${existing?.name}. ` +
        `Use a unique prefix (e.g., "v2-${name}").`
      );
    }

    customElements.define(name, constructor, options);
    this.#registered.set(name, constructor);
    console.log(`[Registry] Registered: ${name}`);
  }

  static getAll() {
    return [...this.#registered.entries()];
  }

  static async whenAllDefined() {
    const names = [...this.#registered.keys()];
    await Promise.all(names.map(n => customElements.whenDefined(n)));
  }
}

// Usage
ComponentRegistry.define('ds-button', DsButton);
ComponentRegistry.define('ds-card', DsCard);
ComponentRegistry.define('ds-modal', DsModal);
ComponentRegistry.define('ds-input', DsInput);
ComponentRegistry.define('ds-badge', DsBadge);
```

---

## Step 4: Component Composition Patterns

```javascript
// Compound components: ds-card contains ds-badge
class DsCard extends HTMLElement {
  connectedCallback() {
    this.attachShadow({ mode: 'open' }).innerHTML = `
      <style>
        :host { display: block; }
        .card { background: var(--ds-card-bg, white); border-radius: var(--ds-card-radius, 0.5rem); }
        .card-header { display: flex; justify-content: space-between; align-items: center; }
      </style>
      <div class="card" part="base">
        <div class="card-header" part="header">
          <slot name="header"></slot>
          <slot name="badge"></slot>
        </div>
        <slot></slot>
        <slot name="footer"></slot>
      </div>
    `;
  }
}

// Usage — composition via slots
/*
<ds-card>
  <span slot="header">Card Title</span>
  <ds-badge slot="badge" variant="new">New</ds-badge>
  <p>Card content goes here</p>
  <ds-button slot="footer">Learn More</ds-button>
</ds-card>
*/
```

---

## Step 5: CSS Custom Properties API Surface

```javascript
// Define the public API via @property (registered properties)
const registerProperties = () => {
  const props = [
    { name: '--ds-btn-bg',         syntax: '<color>',  initial: '#3b82f6' },
    { name: '--ds-btn-color',      syntax: '<color>',  initial: '#ffffff' },
    { name: '--ds-btn-radius',     syntax: '<length>', initial: '0.375rem' },
    { name: '--ds-card-bg',        syntax: '<color>',  initial: '#ffffff' },
    { name: '--ds-card-radius',    syntax: '<length>', initial: '0.5rem' },
  ];

  props.forEach(({ name, syntax, initial }) => {
    try {
      CSS.registerProperty({
        name, syntax,
        inherits: false,
        initialValue: initial,
      });
    } catch (e) {
      // Already registered — safe to ignore
    }
  });
};
```

> 💡 Registered properties (via `CSS.registerProperty`) enable CSS transitions on custom properties — critical for animation systems.

---

## Step 6: Reactive State Pattern

```javascript
class ReactiveElement extends HTMLElement {
  #state = {};
  #updateScheduled = false;

  setState(partial) {
    this.#state = { ...this.#state, ...partial };
    this.#scheduleUpdate();
  }

  get state() { return this.#state; }

  #scheduleUpdate() {
    if (this.#updateScheduled) return;
    this.#updateScheduled = true;
    // Batch updates via microtask
    queueMicrotask(() => {
      this.#updateScheduled = false;
      this.render();
    });
  }

  render() {
    // Override in subclass
    throw new Error('render() must be implemented');
  }
}
```

---

## Step 7: Event Communication Pattern

```javascript
// Type-safe custom events
class DsButton extends ReactiveElement {
  _handleClick(e) {
    // Dispatch typed event with composed:true to cross shadow boundary
    this.dispatchEvent(new CustomEvent('ds-click', {
      bubbles: true,
      composed: true,   // Cross shadow boundary
      detail: {
        variant: this.getAttribute('variant'),
        value: this.getAttribute('value'),
        originalEvent: e,
      },
    }));
  }
}

// Event delegation pattern
document.addEventListener('ds-click', (e) => {
  console.log('Button clicked:', e.detail.variant, e.detail.value);
  console.log('Composed path:', e.composedPath().map(n => n.tagName).filter(Boolean));
});
```

---

## Step 8: Capstone — Lifecycle Verification

```bash
docker run --rm node:20-alpine sh -c "
  cd /app && npm init -y > /dev/null && npm install jsdom 2>&1 | tail -1 && node test.js
"
```

*Verified by running the lifecycle script (see test.js mounted via volume):*

📸 **Verified Output:**
```
[ds-button] attr: variant -> primary
[ds-button] connected, variant=primary
[test] tagName: DS-BUTTON
[test] shadowRoot mode: open
[ds-button] attr: variant -> secondary
[ds-button] disconnected
```

---

## Summary

| Concept | API | Notes |
|---------|-----|-------|
| Element definition | `customElements.define()` | Hyphenated name required |
| Lifecycle hooks | `connected/disconnected/adoptedCallback` | Always call `super()` |
| Shadow DOM | `attachShadow({ mode: 'open' })` | Use `open` for tooling |
| Named slots | `<slot name="header">` | Content projection API |
| Part exposure | `part="base"`, `::part(base)` | Controlled style API |
| CSS inheritance | `--custom-props` | Cross shadow boundary |
| Registered properties | `CSS.registerProperty()` | Enable transitions |
| Collision detection | Custom registry map | Multi-version safety |
| Custom events | `composed: true` | Bubble through shadow DOM |
