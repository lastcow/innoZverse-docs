# Lab 08: Advanced Accessibility

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master advanced accessibility: WCAG 2.2 AAA criteria, ARIA live regions, advanced focus management (`inert`, `:focus-visible`), skip navigation, and automated axe-core testing.

---

## Step 1: WCAG 2.2 Overview

```
WCAG 2.2 Conformance Levels:
  A   — Minimum accessibility (24 criteria)
  AA  — Standard/recommended (38 criteria total)
  AAA — Highest level (62 criteria total)

New in WCAG 2.2 (over 2.1):
  2.4.11 Focus Not Obscured (AA)
  2.4.12 Focus Not Obscured (AAA, enhanced)
  2.4.13 Focus Appearance (AAA)
  2.5.7  Dragging Movements (AA)      — alternatives to drag
  2.5.8  Target Size (AA)             — 24×24px minimum
  3.2.6  Consistent Help (A)          — help in same location
  3.3.7  Redundant Entry (A)          — don't re-ask info
  3.3.8  Accessible Authentication (AA) — no cognitive tests
  3.3.9  Accessible Authentication (AAA, no exceptions)
```

---

## Step 2: ARIA Live Regions

```html
<!-- aria-live: announce dynamic content changes -->

<!-- polite: wait for user to be idle -->
<div
  id="status-message"
  role="status"
  aria-live="polite"
  aria-atomic="true"
>
  <!-- Content injected here is announced when user is idle -->
</div>

<!-- assertive: interrupt immediately (urgent messages) -->
<div
  id="error-banner"
  role="alert"
  aria-live="assertive"
  aria-atomic="true"
>
  <!-- Error messages; interrupts current reading -->
</div>

<!-- aria-relevant: what changes to announce -->
<div aria-live="polite"
     aria-relevant="additions text"  <!-- additions | removals | text | all -->
     aria-atomic="false">            <!-- false: announce only changed node -->
</div>

<!-- off: suppress announcements temporarily -->
<div aria-live="off">
  <!-- Changes here are silent until set to polite/assertive -->
</div>
```

```javascript
// Live region utilities
function announceStatus(message, urgency = 'polite') {
  const region = document.getElementById(
    urgency === 'assertive' ? 'error-banner' : 'status-message'
  );
  
  // Clear and reset to ensure announcement fires
  region.textContent = '';
  
  // Small delay ensures screen readers re-read
  requestAnimationFrame(() => {
    region.textContent = message;
  });
}

// Usage
announceStatus('Form saved successfully.');
announceStatus('Error: Email address is invalid.', 'assertive');
announceStatus('3 results found for "CSS Grid".');
announceStatus('Loading...'); // then clear when done
```

---

## Step 3: Advanced Focus Management

```css
/* :focus-visible — keyboard focus only */
:focus-visible {
  outline: 3px solid var(--color-primary, #3b82f6);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Don't suppress focus-visible */
:focus:not(:focus-visible) {
  outline: none; /* safe: only removes mouse focus ring */
}

/* WCAG 2.2: Focus Appearance (AAA)
   — 2px+ perimeter
   — 3:1 contrast against adjacent colors */
.custom-focus:focus-visible {
  outline: 3px solid #005fcc;
  outline-offset: 3px;
  /* Or: box-shadow as alternative */
}

/* Focus within composite widget */
.listbox:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.2);
}

/* WCAG 2.2: Focus Not Obscured
   — Focused element must not be fully hidden by sticky headers */
html {
  scroll-padding-top: calc(var(--header-height, 0px) + 16px);
}
```

---

## Step 4: The `inert` Attribute

```html
<!-- inert: make element and all descendants non-interactive -->
<!-- Used for: backgrounds behind modals, inactive panels, loading states -->

<div id="main-content" inert aria-hidden="true">
  <!-- This content is completely inaccessible when inert -->
  <!-- No focus, no clicks, not in tab order, invisible to screen readers -->
</div>

<dialog id="modal">
  <!-- Content here is active when modal is open -->
</dialog>
```

```javascript
// Modal focus management with inert
class Modal {
  constructor(modal, trigger) {
    this.modal = modal;
    this.trigger = trigger;
    this.mainContent = document.querySelector('#main-content');
  }
  
  open() {
    this.modal.removeAttribute('hidden');
    this.modal.removeAttribute('inert');
    
    // Trap focus in modal, hide rest
    this.mainContent.setAttribute('inert', '');
    this.mainContent.setAttribute('aria-hidden', 'true');
    
    // Focus first focusable element
    const firstFocusable = this.modal.querySelector(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    firstFocusable?.focus();
  }
  
  close() {
    this.modal.setAttribute('hidden', '');
    this.modal.setAttribute('inert', '');
    
    // Restore main content
    this.mainContent.removeAttribute('inert');
    this.mainContent.removeAttribute('aria-hidden');
    
    // Return focus to trigger
    this.trigger.focus();
  }
}
```

---

## Step 5: Skip Navigation

```html
<!-- First focusable element on the page -->
<a href="#main-content" class="skip-link">
  Skip to main content
</a>

<!-- Multiple skip links -->
<nav class="skip-links" aria-label="Skip navigation">
  <a href="#main-content">Skip to main content</a>
  <a href="#navigation">Skip to navigation</a>
  <a href="#search">Skip to search</a>
</nav>
```

```css
.skip-link {
  /* Hidden until focused */
  position: absolute;
  top: -100%;
  left: 0;
  z-index: 1000;
  
  /* Visible when focused */
  background: var(--color-primary, #3b82f6);
  color: white;
  padding: 0.75rem 1.5rem;
  font-weight: 600;
  font-size: 1rem;
  text-decoration: none;
  border-radius: 0 0 8px 0;
  
  transition: top 0.2s ease;
}

.skip-link:focus {
  top: 0;
}

/* Ensure target has visual indicator */
#main-content:target,
#main-content:focus {
  outline: none; /* handled by skip link UX */
}
```

---

## Step 6: ARIA Patterns for Complex Widgets

```html
<!-- Accessible tabs -->
<div class="tabs">
  <div role="tablist" aria-label="Settings sections">
    <button
      role="tab"
      id="tab-general"
      aria-controls="panel-general"
      aria-selected="true"
      tabindex="0"
    >General</button>
    <button
      role="tab"
      id="tab-security"
      aria-controls="panel-security"
      aria-selected="false"
      tabindex="-1"
    >Security</button>
  </div>
  
  <div
    role="tabpanel"
    id="panel-general"
    aria-labelledby="tab-general"
    tabindex="0"
  >
    <!-- General settings -->
  </div>
  
  <div
    role="tabpanel"
    id="panel-security"
    aria-labelledby="tab-security"
    tabindex="0"
    hidden
  >
    <!-- Security settings -->
  </div>
</div>

<!-- Accessible combobox -->
<div role="combobox"
     aria-expanded="false"
     aria-haspopup="listbox"
     aria-owns="search-results">
  <input type="text"
         aria-autocomplete="list"
         aria-controls="search-results"
         aria-activedescendant="">
</div>

<ul id="search-results"
    role="listbox"
    aria-label="Search suggestions">
  <li role="option" id="option-1" aria-selected="false">Option 1</li>
  <li role="option" id="option-2" aria-selected="false">Option 2</li>
</ul>
```

---

## Step 7: Color Contrast Requirements

```css
/* WCAG 2.1/2.2 Contrast Ratios:
   AA Normal text:  4.5:1
   AA Large text:   3:1   (18pt regular or 14pt bold)
   AA UI components: 3:1  (icons, borders, inputs)
   AAA Normal text: 7:1
   AAA Large text:  4.5:1
*/

/* Tools to check: */
/* - WebAIM Contrast Checker */
/* - Chrome DevTools (hover over color) */
/* - axe DevTools browser extension */

/* oklch makes it easy to maintain contrast */
:root {
  /* Light theme: dark text on light background */
  --color-text:   oklch(10% 0 0);    /* ~#111 — very high contrast */
  --color-bg:     oklch(98% 0 0);    /* ~#fafafa */
  
  /* Ratio: approximately 18:1 ✓ */
}

[data-theme="dark"] {
  --color-text: oklch(95% 0 0);   /* light text */
  --color-bg:   oklch(12% 0 0);   /* dark background */
  /* Ratio: approximately 16:1 ✓ */
}

/* Interactive elements: minimum 3:1 against background */
.button-outline {
  border: 2px solid oklch(57% 0.20 250); /* primary blue */
  /* Must be 3:1 against both the button background AND the page background */
}
```

---

## Step 8: Capstone — Accessibility Audit

```bash
docker run --rm node:20-alpine node -e "
var html = '<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><title>Accessible Form</title></head><body><main><h1>Contact Form</h1><form novalidate><div class=\"field\"><label for=\"name\">Full Name <span aria-hidden=\"true\">*</span></label><input type=\"text\" id=\"name\" name=\"name\" required aria-required=\"true\" aria-describedby=\"name-error\" autocomplete=\"name\"><span id=\"name-error\" role=\"alert\" aria-live=\"polite\"></span></div><div class=\"field\"><label for=\"email\">Email Address</label><input type=\"email\" id=\"email\" name=\"email\" required aria-required=\"true\" aria-describedby=\"email-hint email-error\" autocomplete=\"email\"><span id=\"email-hint\">We will never share your email</span><span id=\"email-error\" role=\"alert\" aria-live=\"polite\"></span></div><button type=\"submit\">Send Message</button></form></main></body></html>';
var checks = [
  {rule:'lang attribute',pass:html.includes('lang=\"en\"'),wcag:'3.1.1 A'},
  {rule:'labels for inputs',pass:html.includes('for=\"name\"')&&html.includes('for=\"email\"'),wcag:'1.3.1 A'},
  {rule:'aria-required',pass:html.includes('aria-required=\"true\"'),wcag:'4.1.2 A'},
  {rule:'aria-describedby',pass:html.includes('aria-describedby'),wcag:'1.3.1 A'},
  {rule:'error live regions',pass:html.includes('aria-live=\"polite\"'),wcag:'4.1.3 AA'},
  {rule:'autocomplete attributes',pass:html.includes('autocomplete='),wcag:'1.3.5 AA'},
  {rule:'button type',pass:html.includes('type=\"submit\"'),wcag:'4.1.2 A'},
];
console.log('axe-core Accessibility Audit (simulated)');
console.log('='.repeat(45));
var passed = 0;
checks.forEach(function(c){
  var status = c.pass ? 'PASS' : 'FAIL';
  if(c.pass) passed++;
  console.log('[' + status + '] WCAG ' + c.wcag + ' - ' + c.rule);
});
console.log('\nResult: ' + passed + '/' + checks.length + ' checks passed');
console.log('Violations: ' + (checks.length - passed));
"
```

📸 **Verified Output:**
```
axe-core Accessibility Audit (simulated)
=============================================
[PASS] WCAG 3.1.1 A - lang attribute
[PASS] WCAG 1.3.1 A - labels for inputs
[PASS] WCAG 4.1.2 A - aria-required
[PASS] WCAG 1.3.1 A - aria-describedby
[PASS] WCAG 4.1.3 AA - error live regions
[PASS] WCAG 1.3.5 AA - autocomplete attributes
[PASS] WCAG 4.1.2 A - button type

Result: 7/7 checks passed
Violations: 0
```

---

## Summary

| Feature | Implementation | WCAG Level |
|---------|---------------|------------|
| Live region | `aria-live="polite"` | 4.1.3 AA |
| Assertive alert | `role="alert"` | 4.1.3 AA |
| Skip link | `.skip-link:focus { top: 0 }` | 2.4.1 A |
| Inert | `element.setAttribute('inert', '')` | — |
| Focus visible | `:focus-visible { outline }` | 2.4.7 AA |
| Focus not obscured | `scroll-padding-top` | 2.4.11 AA (2.2) |
| Target size | `min-width/height: 44px` | 2.5.5 AAA |
| Color contrast | 4.5:1 normal / 3:1 large | 1.4.3 AA |
| Tab widgets | `role="tab/tablist/tabpanel"` | 4.1.2 A |
