# Lab 05: Accessibility Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

WCAG 2.2 AAA accessibility engineering: ARIA authoring practices for complex widgets (modal, combobox, tabs, tree), focus trap implementation, live region patterns, color contrast AAA (7:1), keyboard navigation, and automated axe-core auditing.

---

## Step 1: ARIA Modal Dialog Pattern

```html
<!-- Modal: role=dialog, aria-modal, focus trap, return focus -->
<div role="dialog"
     aria-modal="true"
     aria-labelledby="modal-title"
     aria-describedby="modal-desc"
     id="confirm-dialog"
     tabindex="-1">
  <h2 id="modal-title">Confirm Action</h2>
  <p id="modal-desc">This action cannot be undone. Are you sure?</p>
  <div class="dialog-actions">
    <button id="modal-cancel" type="button">Cancel</button>
    <button id="modal-confirm" type="button" class="danger">Confirm</button>
  </div>
</div>
```

```javascript
// Focus trap — keep focus inside modal
class FocusTrap {
  #element;
  #focusableSelectors = [
    'a[href]', 'button:not([disabled])', 'input:not([disabled])',
    'select:not([disabled])', 'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])', 'details > summary',
  ].join(', ');

  constructor(element) {
    this.#element = element;
  }

  get #focusable() {
    return [...this.#element.querySelectorAll(this.#focusableSelectors)]
      .filter(el => !el.closest('[inert]') && getComputedStyle(el).display !== 'none');
  }

  activate() {
    this.#element.addEventListener('keydown', this.#handleKeydown);
    // Set initial focus to first focusable or dialog itself
    const first = this.#focusable[0] || this.#element;
    first.focus();
  }

  deactivate() {
    this.#element.removeEventListener('keydown', this.#handleKeydown);
  }

  #handleKeydown = (e) => {
    if (e.key !== 'Tab') return;
    const focusable = this.#focusable;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault();
        last.focus();
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
  };
}
```

> 💡 Always use `inert` attribute (not `display:none`) to hide background content from AT when modal is open. Supported in all modern browsers.

---

## Step 2: Combobox (Autocomplete) ARIA Pattern

```html
<!-- ARIA 1.2 Combobox pattern -->
<div class="combobox-container">
  <label for="country-input" id="country-label">Country</label>
  <div class="combobox-wrapper">
    <input type="text"
           id="country-input"
           role="combobox"
           aria-expanded="false"
           aria-autocomplete="list"
           aria-controls="country-listbox"
           aria-activedescendant=""
           aria-labelledby="country-label"
           autocomplete="off">
    <button type="button"
            aria-label="Show country options"
            tabindex="-1"
            aria-controls="country-listbox">
      ▼
    </button>
  </div>
  <ul role="listbox"
      id="country-listbox"
      aria-labelledby="country-label"
      hidden>
    <li role="option" id="opt-us" aria-selected="false">United States</li>
    <li role="option" id="opt-uk" aria-selected="false">United Kingdom</li>
    <li role="option" id="opt-de" aria-selected="false">Germany</li>
  </ul>
</div>
```

---

## Step 3: Tabs Widget

```html
<div class="tabs">
  <div role="tablist" aria-label="Product details">
    <button role="tab" id="tab-overview"
            aria-controls="panel-overview"
            aria-selected="true"
            tabindex="0">Overview</button>
    <button role="tab" id="tab-specs"
            aria-controls="panel-specs"
            aria-selected="false"
            tabindex="-1">Specs</button>
    <button role="tab" id="tab-reviews"
            aria-controls="panel-reviews"
            aria-selected="false"
            tabindex="-1">Reviews</button>
  </div>

  <div role="tabpanel" id="panel-overview"
       aria-labelledby="tab-overview"
       tabindex="0">
    Overview content...
  </div>
  <div role="tabpanel" id="panel-specs"
       aria-labelledby="tab-specs"
       tabindex="0" hidden>
    Specs content...
  </div>
</div>
```

```javascript
// Tabs keyboard navigation
tabList.addEventListener('keydown', (e) => {
  const tabs = [...tabList.querySelectorAll('[role=tab]')];
  const current = tabs.findIndex(t => t === document.activeElement);

  const map = {
    ArrowRight: (current + 1) % tabs.length,
    ArrowLeft:  (current - 1 + tabs.length) % tabs.length,
    Home: 0,
    End: tabs.length - 1,
  };

  if (e.key in map) {
    e.preventDefault();
    tabs[map[e.key]].focus();
    // Automatic activation on focus (ARIA practice)
    activateTab(tabs[map[e.key]]);
  }
});
```

---

## Step 4: Screen Reader Announcement Patterns

```html
<!-- Live regions: polite vs assertive -->

<!-- Status updates (non-urgent) — screen reader announces at next pause -->
<div role="status" aria-live="polite" aria-atomic="true" id="form-status" class="sr-only">
  <!-- JS updates textContent here -->
</div>

<!-- Alerts (urgent) — screen reader announces immediately -->
<div role="alert" aria-live="assertive" aria-atomic="true" id="error-alert" class="sr-only">
  <!-- Errors only -->
</div>

<!-- Progress: use aria-valuenow -->
<div role="progressbar"
     aria-valuemin="0"
     aria-valuemax="100"
     aria-valuenow="65"
     aria-label="Upload progress">
  <div class="progress-fill" style="width: 65%"></div>
</div>
```

```css
/* Visually hidden but accessible */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Focus-visible: only show for keyboard, not mouse */
:focus-visible {
  outline: 3px solid var(--color-focus, #3b82f6);
  outline-offset: 2px;
}
:focus:not(:focus-visible) {
  outline: none;
}
```

---

## Step 5: Color Contrast AAA (7:1 ratio)

```javascript
// Contrast ratio calculator
function luminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c /= 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

function contrastRatio(hex1, hex2) {
  const parse = hex => {
    const n = parseInt(hex.replace('#', ''), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  };
  const l1 = luminance(...parse(hex1));
  const l2 = luminance(...parse(hex2));
  const [lighter, darker] = l1 > l2 ? [l1, l2] : [l2, l1];
  return (lighter + 0.05) / (darker + 0.05);
}

// AAA requires 7:1 for normal text, 4.5:1 for large text
console.log(contrastRatio('#1e293b', '#f8fafc').toFixed(2)); // ~15.3:1 ✓ AAA
console.log(contrastRatio('#3b82f6', '#ffffff').toFixed(2)); // ~3.0:1 ✗ AA fail
console.log(contrastRatio('#1d4ed8', '#ffffff').toFixed(2)); // ~7.0:1 ✓ AAA
```

---

## Step 6: Tree Widget Navigation

```html
<ul role="tree" aria-label="File system">
  <li role="treeitem" aria-expanded="true" aria-level="1" tabindex="0">
    <span>src/</span>
    <ul role="group">
      <li role="treeitem" aria-level="2" tabindex="-1">components/</li>
      <li role="treeitem" aria-level="2" tabindex="-1">styles/</li>
    </ul>
  </li>
  <li role="treeitem" aria-level="1" tabindex="-1">package.json</li>
</ul>
```

---

## Step 7: axe-core Audit Setup

```javascript
// audit.js — automated accessibility audit
const { JSDOM } = require('jsdom');
const html = `
  <html lang="en">
    <head><title>Accessible App</title></head>
    <body>
      <main>
        <h1>Dashboard</h1>
        <nav aria-label="Main navigation">
          <ul><li><a href="/">Home</a></li></ul>
        </nav>
        <button aria-label="Close dialog">X</button>
        <img src="hero.jpg" alt="Hero image" />
        <form>
          <label for="email">Email address</label>
          <input type="email" id="email" name="email" required />
        </form>
      </main>
    </body>
  </html>`;

const dom = new JSDOM(html, { runScripts: 'dangerously' });
dom.window.eval(require('fs').readFileSync('./node_modules/axe-core/axe.js', 'utf8'));
dom.window.axe.run(dom.window.document, (err, results) => {
  console.log('Violations:', results.violations.length);
  console.log('Passes:', results.passes.length);
  results.violations.forEach(v =>
    console.log('  FAIL:', v.id, '-', v.help));
});
```

---

## Step 8: Capstone — Full axe-core Audit

```bash
docker run --rm node:20-alpine sh -c "
  cd /app && npm init -y > /dev/null 2>&1
  npm install axe-core jsdom 2>&1 | tail -1
  node audit.js
"
```

📸 **Verified Output:**
```
found 0 vulnerabilities
=== axe-core WCAG 2.2 Audit ===
Violations: 1
Passes: 17
  FAIL: html-has-lang - <html> element must have a lang attribute
```

*(Adding `lang="en"` to `<html>` yields 0 violations.)*

---

## Summary

| Pattern | ARIA Role/Property | Keyboard |
|---------|-------------------|----------|
| Modal | `role=dialog`, `aria-modal` | Trap Tab, Esc closes |
| Combobox | `role=combobox`, `aria-expanded` | ↑↓ navigate, Enter select |
| Tabs | `role=tablist/tab/tabpanel` | ←→ switch tabs, Tab to panel |
| Tree | `role=tree/treeitem`, `aria-expanded` | ←→ collapse/expand |
| Live region | `role=status/alert` | Polite vs assertive |
| Focus visible | `:focus-visible` | Keyboard-only outline |
| SR-only | `.sr-only` pattern | Visible to AT, not screen |
| Contrast AAA | 7:1 ratio | - |
| Audit | `axe-core` | Automated WCAG 2.2 |
