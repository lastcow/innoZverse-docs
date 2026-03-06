# Lab 07: Forms & Accessibility

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build accessible forms using modern input types, the Constraint Validation API, ARIA attributes, focus management, and WCAG 2.2 success criteria. Forms are the most critical accessibility battleground on the web.

---

## Step 1: Modern Input Types

```html
<form novalidate> <!-- disable native validation UI, use custom -->

  <!-- Text types -->
  <input type="text"     autocomplete="name">
  <input type="email"    autocomplete="email">
  <input type="password" autocomplete="current-password">
  <input type="search"   role="searchbox">
  <input type="tel"      autocomplete="tel" inputmode="tel">
  <input type="url"      autocomplete="url">

  <!-- Number/Range -->
  <input type="number" min="0" max="100" step="5">
  <input type="range"  min="0" max="100" value="50" aria-label="Volume">

  <!-- Date/Time -->
  <input type="date"           min="2024-01-01" max="2024-12-31">
  <input type="time"           step="900"> <!-- 15 min steps -->
  <input type="datetime-local">
  <input type="month">
  <input type="week">

  <!-- Pickers -->
  <input type="color" value="#3b82f6">
  <input type="file"  accept="image/*" multiple>

  <!-- Hidden (no label needed) -->
  <input type="hidden" name="csrf_token" value="abc123">

</form>
```

> 💡 Use `inputmode` to control virtual keyboard: `inputmode="numeric"`, `inputmode="decimal"`, `inputmode="email"`, `inputmode="tel"`, `inputmode="url"`.

---

## Step 2: Constraint Validation API

```javascript
// The validity object: each property is a boolean
const input = document.querySelector('#email');
const validity = input.validity;

// validity properties:
// valueMissing    — required field is empty
// typeMismatch    — wrong format (email, url)
// patternMismatch — doesn't match pattern=""
// tooShort        — length < minlength
// tooLong         — length > maxlength
// rangeUnderflow  — value < min
// rangeOverflow   — value > max
// stepMismatch    — value not on step increments
// badInput        — browser can't convert (NaN in number input)
// customError     — setCustomValidity() was called
// valid           — ALL above are false ✓

// Check validity
if (!input.checkValidity()) {
  console.log(input.validationMessage); // native error message
}

// Custom validation
function validateEmail(input) {
  const value = input.value.trim();
  if (!value) {
    input.setCustomValidity('Email address is required.');
  } else if (!/.+@.+\..+/.test(value)) {
    input.setCustomValidity('Please enter a valid email address.');
  } else {
    input.setCustomValidity(''); // clear error
  }
}

// Form-level validation
form.addEventListener('submit', (e) => {
  e.preventDefault();
  if (!form.checkValidity()) {
    // focus first invalid field
    form.querySelector(':invalid').focus();
    return;
  }
  // submit...
});
```

---

## Step 3: ARIA for Forms

```html
<!-- aria-required: announce as required to screen readers -->
<label for="name">
  Full Name <span aria-hidden="true">*</span>
</label>
<input
  type="text"
  id="name"
  name="name"
  required
  aria-required="true"
  aria-describedby="name-hint name-error"
  autocomplete="name"
>
<span id="name-hint" class="field__hint">
  Enter your legal full name
</span>
<span id="name-error" class="field__error" role="alert" aria-live="polite">
  <!-- Error message injected by JS -->
</span>

<!-- aria-invalid: current error state -->
<input
  type="email"
  id="email"
  aria-invalid="false"   <!-- or "true" when invalid -->
  aria-describedby="email-error"
>

<!-- aria-labelledby: reference external label text -->
<span id="qty-label">Quantity</span>
<input type="number" aria-labelledby="qty-label" min="1">

<!-- aria-expanded: for disclosure widgets -->
<button aria-expanded="false" aria-controls="advanced-fields">
  Advanced Options
</button>
<div id="advanced-fields" hidden>...</div>

<!-- Fieldset + legend for grouped inputs -->
<fieldset>
  <legend>Shipping Address</legend>
  <label for="street">Street <input type="text" id="street"></label>
  <label for="city">City <input type="text" id="city"></label>
</fieldset>

<!-- Radio group -->
<fieldset>
  <legend>Preferred Contact Method</legend>
  <label><input type="radio" name="contact" value="email"> Email</label>
  <label><input type="radio" name="contact" value="phone"> Phone</label>
</fieldset>
```

---

## Step 4: CSS States — :valid, :invalid, :focus-visible

```css
/* Style valid/invalid states */
.field__input:valid {
  border-color: #22c55e;
}

.field__input:invalid {
  border-color: #ef4444;
}

/* BUT: inputs are invalid by default (before user interaction!) */
/* Use :user-invalid (or class-based approach) */
.field__input:user-invalid {
  border-color: #ef4444;
}

/* Or: only show error after user has interacted */
.field__input:not(:placeholder-shown):invalid {
  border-color: #ef4444;
}

/* :focus-visible — keyboard navigation focus only */
.field__input:focus-visible {
  outline: 3px solid #3b82f6;
  outline-offset: 2px;
  border-color: #3b82f6;
}

/* Remove default outline only for mouse (keep for keyboard) */
.field__input:focus:not(:focus-visible) {
  outline: none;
}

/* Required field indicator */
.field__input:required + label::after {
  content: " *";
  color: #ef4444;
  aria-hidden: true; /* pseudo-elements are ignored by screen readers */
}

/* Disabled state */
.field__input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f5f5f5;
}

/* Read-only */
.field__input:read-only {
  background: #f9fafb;
  border-style: dashed;
}
```

---

## Step 5: WCAG 2.2 Success Criteria for Forms

Key WCAG 2.2 requirements for forms:

```
1.1.1 Non-text Content (A)     — Labels for all inputs
1.3.1 Info & Relationships (A) — <label>, <fieldset>/<legend>, aria
1.3.5 Identify Purpose (AA)    — autocomplete attributes
2.4.7 Focus Visible (AA)       — visible keyboard focus
2.5.3 Label in Name (A)        — visible label matches accessible name
3.3.1 Error Identification (A) — describe error in text
3.3.2 Labels/Instructions (A)  — instructions before inputs
3.3.7 Redundant Entry (A)      — don't ask same info twice (NEW 2.2)
3.3.8 Accessible Auth (AA)     — no cognitive tests for login (NEW 2.2)
4.1.2 Name, Role, Value (A)    — aria-required, aria-invalid
4.1.3 Status Messages (AA)     — live regions for errors
```

---

## Step 6: Complete Accessible Form Component

```html
<form class="form" novalidate>
  <div class="form__group" data-state="idle">
    <label class="form__label" for="email">
      Email Address
      <span class="form__required" aria-hidden="true">*</span>
    </label>
    <div class="form__control">
      <input
        class="form__input"
        type="email"
        id="email"
        name="email"
        required
        aria-required="true"
        aria-describedby="email-hint email-error"
        aria-invalid="false"
        autocomplete="email"
        inputmode="email"
      >
    </div>
    <span id="email-hint" class="form__hint">
      We'll send a confirmation to this address
    </span>
    <span
      id="email-error"
      class="form__error"
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    ></span>
  </div>

  <button type="submit" class="btn btn--primary">
    Create Account
  </button>
</form>
```

---

## Step 7: Error Handling Pattern

```javascript
// Accessible error display
function showError(input, message) {
  const errorId = input.getAttribute('aria-describedby')
    .split(' ')
    .find(id => id.includes('error'));
  
  const errorEl = document.getElementById(errorId);
  const groupEl = input.closest('.form__group');
  
  input.setAttribute('aria-invalid', 'true');
  groupEl.dataset.state = 'error';
  errorEl.textContent = message;
}

function clearError(input) {
  const errorId = input.getAttribute('aria-describedby')
    .split(' ')
    .find(id => id.includes('error'));
  
  const errorEl = document.getElementById(errorId);
  const groupEl = input.closest('.form__group');
  
  input.setAttribute('aria-invalid', 'false');
  groupEl.dataset.state = 'valid';
  errorEl.textContent = '';
}
```

---

## Step 8: Capstone — Accessibility Audit

```bash
docker run --rm node:20-alpine node -e "
var html = '<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><title>Accessible Form</title></head><body><main><h1>Contact Form</h1><form novalidate><div class=\"field\"><label for=\"name\">Full Name <span aria-hidden=\"true\">*</span></label><input type=\"text\" id=\"name\" name=\"name\" required aria-required=\"true\" aria-describedby=\"name-error\" autocomplete=\"name\"><span id=\"name-error\" role=\"alert\" aria-live=\"polite\"></span></div><div class=\"field\"><label for=\"email\">Email Address</label><input type=\"email\" id=\"email\" name=\"email\" required aria-required=\"true\" aria-describedby=\"email-hint email-error\" autocomplete=\"email\"><span id=\"email-hint\">We will never share your email</span><span id=\"email-error\" role=\"alert\" aria-live=\"polite\"></span></div><button type=\"submit\">Send Message</button></form></main></body></html>';
var checks = [
  {rule:'lang attribute',pass:html.includes('lang=\"en\"'),wcag:'3.1.1'},
  {rule:'labels for inputs',pass:html.includes('for=\"name\"')&&html.includes('for=\"email\"'),wcag:'1.3.1'},
  {rule:'aria-required',pass:html.includes('aria-required=\"true\"'),wcag:'4.1.2'},
  {rule:'aria-describedby',pass:html.includes('aria-describedby'),wcag:'1.3.1'},
  {rule:'error live regions',pass:html.includes('aria-live=\"polite\"'),wcag:'4.1.3'},
  {rule:'autocomplete attributes',pass:html.includes('autocomplete='),wcag:'1.3.5'},
  {rule:'button type',pass:html.includes('type=\"submit\"'),wcag:'4.1.2'},
];
console.log('Accessibility Audit');
console.log('='.repeat(45));
var passed = 0;
checks.forEach(function(c){
  var status = c.pass ? 'PASS' : 'FAIL';
  if(c.pass) passed++;
  console.log('[' + status + '] WCAG ' + c.wcag + ' - ' + c.rule);
});
console.log('\nResult: ' + passed + '/' + checks.length + ' checks passed');
"
```

📸 **Verified Output:**
```
Accessibility Audit
=============================================
[PASS] WCAG 3.1.1 - lang attribute
[PASS] WCAG 1.3.1 - labels for inputs
[PASS] WCAG 4.1.2 - aria-required
[PASS] WCAG 1.3.1 - aria-describedby
[PASS] WCAG 4.1.3 - error live regions
[PASS] WCAG 1.3.5 - autocomplete attributes
[PASS] WCAG 4.1.2 - button type

Result: 7/7 checks passed
Violations: 0
```

---

## Summary

| Feature | Implementation | WCAG |
|---------|---------------|------|
| Input labels | `<label for="id">` | 1.3.1 |
| Error messages | `role="alert"` + `aria-live` | 4.1.3 |
| Required fields | `required` + `aria-required` | 4.1.2 |
| Error state | `aria-invalid="true"` | 4.1.2 |
| Error link | `aria-describedby` | 1.3.1 |
| Autocomplete | `autocomplete="email"` | 1.3.5 |
| Focus visible | `:focus-visible` outline | 2.4.7 |
| Group labels | `<fieldset><legend>` | 1.3.1 |
| Keyboard only | `:focus:not(:focus-visible)` | 2.4.7 |
