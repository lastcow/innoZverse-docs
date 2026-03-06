# Lab 12: Component API Design

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Component API design principles: CSS custom property API surface with `@property`, variant systems using `data-variant` + `:is()`, compound component patterns, CSS-only state machines via `:has()`, and slot-based composition strategies.

---

## Step 1: CSS Custom Property API — @property

```css
/* Document the component's CSS API surface via @property */
/* This makes the API explicit, type-checked, and animatable */

@property --ds-btn-bg {
  syntax: '<color>';
  initial-value: #3b82f6;
  inherits: false;  /* Component-scoped, not inherited */
}

@property --ds-btn-color {
  syntax: '<color>';
  initial-value: #ffffff;
  inherits: false;
}

@property --ds-btn-radius {
  syntax: '<length>';
  initial-value: 0.375rem;
  inherits: false;
}

@property --ds-btn-padding {
  syntax: '<length>{1,4}';
  initial-value: 0.5rem 1rem;
  inherits: false;
}

@property --ds-btn-font-size {
  syntax: '<length>';
  initial-value: 1rem;
  inherits: false;
}

@property --ds-btn-border {
  syntax: '<length> || <line-style> || <color>';
  initial-value: none;
  inherits: false;
}

/* Component uses its own API */
.btn {
  background: var(--ds-btn-bg);
  color: var(--ds-btn-color);
  border-radius: var(--ds-btn-radius);
  padding: var(--ds-btn-padding);
  font-size: var(--ds-btn-font-size);
  border: var(--ds-btn-border);

  /* Internal use only (--_*) — NOT in public API */
  --_focus-ring: var(--ds-btn-bg);
}

/* Consumers set the API */
.hero .btn {
  --ds-btn-radius: 9999px;    /* Pill button in hero */
  --ds-btn-bg: white;
  --ds-btn-color: #1e293b;
}
```

> 💡 Prefix public API vars with `--ds-component-` and internal-only vars with `--_`. The leading underscore signals "don't override this externally."

---

## Step 2: Variant System — data-variant + :is()

```css
/* Attribute-based variant system */
.btn { /* base styles */ }

/* Single selector matches any variant */
.btn:is([data-variant="primary"]),
.btn:not([data-variant]) {
  --ds-btn-bg: var(--color-primary);
  --ds-btn-color: white;
}

.btn[data-variant="secondary"] {
  --ds-btn-bg: var(--color-surface);
  --ds-btn-color: var(--color-text-primary);
  --ds-btn-border: 1px solid var(--color-border);
}

.btn[data-variant="danger"] {
  --ds-btn-bg: var(--color-danger);
  --ds-btn-color: white;
}

.btn[data-variant="ghost"] {
  --ds-btn-bg: transparent;
  --ds-btn-color: var(--color-primary);
  --ds-btn-border: 1px solid currentColor;
}

/* Size variants */
.btn[data-size="sm"] {
  --ds-btn-padding: 0.25rem 0.5rem;
  --ds-btn-font-size: 0.875rem;
}

.btn[data-size="lg"] {
  --ds-btn-padding: 0.75rem 1.5rem;
  --ds-btn-font-size: 1.125rem;
}

/* Compound variants: danger + lg */
.btn[data-variant="danger"][data-size="lg"] {
  letter-spacing: 0.025em;
  font-weight: 700;
}
```

```html
<!-- Clean HTML API -->
<button class="btn" data-variant="primary" data-size="md">Save</button>
<button class="btn" data-variant="secondary" data-size="sm">Cancel</button>
<button class="btn" data-variant="danger" data-size="lg">Delete Account</button>
```

---

## Step 3: Compound Components

```html
<!-- Card compound component — composed of named parts -->
<article class="card">
  <!-- card-header: flex row with space-between -->
  <header class="card__header">
    <h3 class="card__title">Product Name</h3>
    <span class="card__badge" data-variant="new">New</span>
  </header>

  <!-- card-media: full-width image with aspect ratio -->
  <figure class="card__media">
    <img src="product.jpg" alt="Product image" loading="lazy">
  </figure>

  <!-- card-body: content area -->
  <div class="card__body">
    <p class="card__description">Description text</p>
  </div>

  <!-- card-footer: action area -->
  <footer class="card__footer">
    <button class="btn" data-variant="primary">Add to Cart</button>
  </footer>
</article>
```

```css
/* BEM + data attributes hybrid */
.card {
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  border-radius: var(--ds-card-radius, 0.5rem);
  overflow: hidden;
  background: var(--ds-card-bg, white);
}

.card__media {
  aspect-ratio: 16 / 9;
  overflow: hidden;
}

.card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--duration-normal) var(--easing-standard);
}

.card:hover .card__media img {
  transform: scale(1.05);
}

/* Horizontal layout variant */
.card[data-layout="horizontal"] {
  grid-template-rows: none;
  grid-template-columns: 40% 1fr;
}

.card[data-layout="horizontal"] .card__media {
  grid-row: 1 / -1;
  aspect-ratio: auto;
}
```

---

## Step 4: CSS-Only State Machines with :has()

```css
/* Accordion — pure CSS, no JS */
.accordion-item {
  border: 1px solid var(--color-border);
  border-radius: 0.375rem;
  overflow: hidden;
}

/* Detect if checkbox is checked */
.accordion-item:has(input[type="checkbox"]:checked) .accordion-content {
  display: block;
}

.accordion-item:not(:has(input[type="checkbox"]:checked)) .accordion-content {
  display: none;
}

/* Chevron rotation state */
.accordion-item:has(input[type="checkbox"]:checked) .chevron {
  transform: rotate(180deg);
}

/* Form validation state machine */
.form-field:has(input:valid) .field-hint   { color: var(--color-success); }
.form-field:has(input:invalid:not(:focus)) .field-hint { color: var(--color-danger); }
.form-field:has(input:focus) .field-hint   { color: var(--color-primary); }

/* Navigation state: detect active descendant */
.nav-group:has(.nav-link[aria-current="page"]) > .nav-group-label {
  color: var(--color-primary);
  font-weight: 600;
}

/* Complex state: form with any invalid field */
.form:has(input:invalid:not(:placeholder-shown)) .submit-btn {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
```

> 💡 `:has()` is a parent selector in disguise — it reads child state and applies styles to any ancestor. CSS state machines without JavaScript are now production-ready.

---

## Step 5: Slot-Based Composition Strategies

```html
<!-- Slot API documentation -->
<!--
  ds-dialog slots:
    [default]     → Dialog body content
    header        → Custom header (replaces default title)
    footer        → Action buttons area
    close-button  → Custom close trigger

  ds-dialog CSS API:
    --ds-dialog-width: max(min(90vw, 600px), 300px)
    --ds-dialog-padding: 1.5rem
    --ds-dialog-bg: white
    --ds-dialog-radius: 0.5rem
-->

<ds-dialog aria-labelledby="dialog-title">
  <!-- header slot override -->
  <h2 slot="header" id="dialog-title">Custom Header</h2>

  <!-- default slot: body -->
  <p>Dialog content with full control over markup.</p>
  <ds-input label="Name" name="name"></ds-input>

  <!-- footer slot: actions -->
  <div slot="footer" style="display: flex; gap: 0.5rem; justify-content: end">
    <button class="btn" data-variant="secondary">Cancel</button>
    <button class="btn" data-variant="primary" type="submit">Save</button>
  </div>
</ds-dialog>
```

---

## Step 6: Component Contract Documentation

```typescript
// TypeScript component contract (used with Web Components or React)
interface ButtonProps {
  // Variant enum — maps to data-variant attribute
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  // Size enum — maps to data-size attribute
  size?: 'sm' | 'md' | 'lg';
  // Disabled state
  disabled?: boolean;
  // Loading state (shows spinner)
  loading?: boolean;
  // Full width
  fullWidth?: boolean;
  // Click handler
  onClick?: (event: MouseEvent) => void;
}

// CSS API contract — documented via @property
// --ds-btn-bg: <color> = var(--color-primary)
// --ds-btn-color: <color> = white
// --ds-btn-radius: <length> = 0.375rem
// --ds-btn-padding: <length>{1,4} = 0.5rem 1rem
```

---

## Step 7: Variant Resolution Algorithm

```javascript
// Resolve CSS class/attribute based on variant props
function resolveVariants(element, variants) {
  // Clear all current variants
  Object.keys(variants).forEach(key => {
    element.removeAttribute(`data-${key}`);
  });

  // Apply new variants
  Object.entries(variants).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== false) {
      element.setAttribute(`data-${key}`, value === true ? '' : value);
    }
  });
}

// Usage
resolveVariants(button, {
  variant: 'primary',
  size: 'lg',
  loading: true,
  disabled: false,  // Not applied (false)
});
// Result: <button data-variant="primary" data-size="lg" data-loading="">
```

---

## Step 8: Capstone — API Documentation Generator

```bash
docker run --rm node:20-alpine node -e "
const componentAPI = {
  name: 'ds-button',
  properties: [
    { name: '--ds-btn-bg', type: '<color>', default: '#3b82f6', desc: 'Background color' },
    { name: '--ds-btn-color', type: '<color>', default: 'white', desc: 'Text color' },
    { name: '--ds-btn-radius', type: '<length>', default: '0.375rem', desc: 'Border radius' },
  ],
  variants: ['primary','secondary','danger','ghost'],
};
console.log('=== Component API: ' + componentAPI.name + ' ===');
console.log('');
console.log('CSS Custom Property API:');
componentAPI.properties.forEach(p => {
  console.log('  ' + p.name);
  console.log('    Type:    ' + p.type);
  console.log('    Default: ' + p.default);
  console.log('    Desc:    ' + p.desc);
});
console.log('');
console.log('Variants:', componentAPI.variants.join(' | '));
"
```

📸 **Verified Output:**
```
=== Component API: ds-button ===

CSS Custom Property API:
  --ds-btn-bg
    Type:    <color>
    Default: #3b82f6
    Desc:    Background color
  --ds-btn-color
    Type:    <color>
    Default: white
    Desc:    Text color
  --ds-btn-radius
    Type:    <length>
    Default: 0.375rem
    Desc:    Border radius

Variants: primary | secondary | danger | ghost
```

---

## Summary

| Pattern | Implementation | Benefit |
|---------|---------------|---------|
| API surface | `@property` declarations | Type-safe, animatable |
| Variant system | `data-variant` + `:is()` | Clean HTML API |
| Compound components | BEM + slot names | Composable structure |
| CSS state machines | `:has()` selectors | Zero JS needed |
| Slot composition | Web Component slots | Flexible content |
| Private vars | `--_` prefix convention | Clear API boundary |
| Contract docs | TypeScript interface | Self-documenting |
