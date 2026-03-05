# Lab 05: Security in Node.js

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

OWASP Top 10 in Node.js context: prototype pollution, ReDoS, path traversal, deserialization attacks, CSP headers, rate limiting, and input validation patterns.

---

## Step 1: Prototype Pollution

```javascript
// VULNERABLE: Recursive merge without sanitization
function deepMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === 'object') {
      target[key] = target[key] ?? {};
      deepMerge(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

// Attack: pollute Object.prototype
const attack = JSON.parse('{"__proto__": {"isAdmin": true}}');
deepMerge({}, attack);
console.log({}.isAdmin); // true! — All objects now have isAdmin

// SECURE: Check for dangerous keys
function safeMerge(target, source, depth = 0) {
  if (depth > 10) throw new Error('Max depth exceeded'); // Prevent deep recursion
  for (const key of Object.keys(source)) {
    if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
      continue; // Skip dangerous keys
    }
    if (source[key] && typeof source[key] === 'object') {
      target[key] = target[key] ?? Object.create(null);
      safeMerge(target[key], source[key], depth + 1);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

// Use Object.create(null) for safe lookup tables
const safe = Object.create(null);
safe['__proto__'] = 'not a prototype!';
console.log(safe['__proto__']); // 'not a prototype!' (just a key)

// Reset pollution from demo (don't do this in production!)
delete Object.prototype.isAdmin;
```

---

## Step 2: ReDoS (Regular Expression Denial of Service)

```javascript
// VULNERABLE: Catastrophic backtracking
const vulnerable = /^(a+)+$/;
// This takes exponential time for non-matching input!
// vulnerable.test('a'.repeat(30) + '!'); // HANGS!

// SAFE: Rewrite without nested quantifiers
const safePattern = /^a+$/;

// Common vulnerable patterns:
// (a+)+   -> catastrophic
// (a|aa)+ -> catastrophic  
// (a*)*   -> catastrophic

// Safe alternatives:
const safeEmail = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
const safeUrl = /^https?:\/\/[^\s<>"]+$/;

// Timeout protection
function safeRegexTest(pattern, input, timeoutMs = 100) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error('RegEx timeout — possible ReDoS'));
    }, timeoutMs);

    // Run in a non-blocking way
    setImmediate(() => {
      try {
        const result = pattern.test(input);
        clearTimeout(timer);
        resolve(result);
      } catch (e) {
        clearTimeout(timer);
        reject(e);
      }
    });
  });
}

console.log('Email valid:', safeEmail.test('user@example.com'));
console.log('Email invalid:', safeEmail.test('not-an-email'));
```

---

## Step 3: Path Traversal

```javascript
const path = require('node:path');
const fs = require('node:fs/promises');

// VULNERABLE: Direct user input in file path
async function readFileUnsafe(userInput) {
  const filePath = '/app/uploads/' + userInput;
  // userInput = '../../etc/passwd' -> reads /etc/passwd!
  return fs.readFile(filePath, 'utf8');
}

// SECURE: Validate path stays within base directory
async function readFileSafe(baseDir, userInput) {
  // Resolve to absolute path (handles ../ etc)
  const resolved = path.resolve(baseDir, userInput);

  // Ensure resolved path starts with base directory
  const normalized = path.normalize(baseDir);
  if (!resolved.startsWith(normalized + path.sep) && resolved !== normalized) {
    throw new Error(`Path traversal detected: ${userInput}`);
  }

  // Also check for null bytes (common attack)
  if (userInput.includes('\0')) {
    throw new Error('Null byte in path');
  }

  return fs.readFile(resolved, 'utf8');
}

// Test
const base = '/app/uploads';
try { readFileSafe(base, '../../etc/passwd'); }
catch (e) { console.log('Blocked:', e.message); }

// Safe path is allowed
const safePath = path.resolve(base, 'image.png');
console.log('Safe path:', safePath);
console.log('Within base:', safePath.startsWith(base));
```

---

## Step 4: Deserialization & Injection

```javascript
// NEVER deserialize untrusted data with eval or Function()

// VULNERABLE: eval-based deserialization
function deserializeUnsafe(data) {
  return eval(`(${data})`); // Code injection!
  // attack: '(process.env)' or 'require("child_process").execSync("rm -rf /")'
}

// SECURE: Use JSON.parse with validation
function deserializeSafe(data) {
  if (typeof data !== 'string') throw new TypeError('Expected string');
  if (data.length > 10000) throw new RangeError('Data too large');

  const parsed = JSON.parse(data); // Throws on invalid JSON

  // Validate structure with schema
  if (!isValidShape(parsed)) throw new Error('Invalid data shape');

  return parsed;
}

function isValidShape(obj) {
  if (typeof obj !== 'object' || obj === null) return false;
  const allowedFields = ['id', 'name', 'email', 'age'];
  const keys = Object.keys(obj);
  return keys.every(k => allowedFields.includes(k));
}

// SQL Injection prevention (parameterized queries)
// WRONG: string concatenation
// const query = `SELECT * FROM users WHERE id = ${userId}`;

// CORRECT: parameterized
// const query = 'SELECT * FROM users WHERE id = ?';
// db.query(query, [userId]);

// XSS prevention
function escapeHtml(str) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return str.replace(/[&<>"']/g, m => map[m]);
}

console.log(escapeHtml('<script>alert("XSS")</script>'));
```

---

## Step 5: Security Headers

```javascript
// Security headers (without helmet, manually for understanding)
function securityMiddleware(req, res, next) {
  // Content Security Policy
  res.setHeader('Content-Security-Policy',
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"
  );

  // Prevent MIME type sniffing
  res.setHeader('X-Content-Type-Options', 'nosniff');

  // Prevent clickjacking
  res.setHeader('X-Frame-Options', 'DENY');

  // XSS Protection (legacy browsers)
  res.setHeader('X-XSS-Protection', '1; mode=block');

  // HSTS (HTTPS only)
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');

  // Referrer policy
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');

  // Permissions policy
  res.setHeader('Permissions-Policy', 'geolocation=(), microphone=(), camera=()');

  // Remove fingerprinting header
  res.removeHeader('X-Powered-By');

  next();
}

// Rate limiting (token bucket algorithm)
class RateLimiter {
  #buckets = new Map();
  #maxTokens;
  #refillRate;
  #refillInterval;

  constructor({ maxRequests = 100, windowMs = 60000 } = {}) {
    this.#maxTokens = maxRequests;
    this.#refillRate = maxRequests;
    this.#refillInterval = windowMs;

    // Clean up old entries periodically
    setInterval(() => {
      const now = Date.now();
      for (const [key, bucket] of this.#buckets) {
        if (now - bucket.lastRefill > this.#refillInterval * 2) {
          this.#buckets.delete(key);
        }
      }
    }, this.#refillInterval).unref();
  }

  check(key) {
    const now = Date.now();
    let bucket = this.#buckets.get(key);

    if (!bucket) {
      bucket = { tokens: this.#maxTokens, lastRefill: now };
      this.#buckets.set(key, bucket);
    }

    // Refill tokens
    const elapsed = now - bucket.lastRefill;
    const tokensToAdd = (elapsed / this.#refillInterval) * this.#refillRate;
    bucket.tokens = Math.min(this.#maxTokens, bucket.tokens + tokensToAdd);
    bucket.lastRefill = now;

    if (bucket.tokens >= 1) {
      bucket.tokens -= 1;
      return { allowed: true, remaining: Math.floor(bucket.tokens) };
    }

    return { allowed: false, remaining: 0, retryAfter: Math.ceil(
      (1 - bucket.tokens) / (this.#refillRate / this.#refillInterval)
    )};
  }
}
```

---

## Step 6: Input Validation

```javascript
// Schema-based validation (without Zod/Joi, educational implementation)
class Validator {
  static string({ minLength = 0, maxLength = Infinity, pattern, required = false } = {}) {
    return (value, field) => {
      if (value === undefined || value === null) {
        if (required) return `${field} is required`;
        return null;
      }
      if (typeof value !== 'string') return `${field} must be a string`;
      if (value.length < minLength) return `${field} must be at least ${minLength} chars`;
      if (value.length > maxLength) return `${field} must be at most ${maxLength} chars`;
      if (pattern && !pattern.test(value)) return `${field} has invalid format`;
      return null;
    };
  }

  static number({ min = -Infinity, max = Infinity, integer = false } = {}) {
    return (value, field) => {
      if (typeof value !== 'number' || isNaN(value)) return `${field} must be a number`;
      if (value < min) return `${field} must be >= ${min}`;
      if (value > max) return `${field} must be <= ${max}`;
      if (integer && !Number.isInteger(value)) return `${field} must be an integer`;
      return null;
    };
  }

  static schema(rules) {
    return (data) => {
      const errors = {};
      for (const [field, validator] of Object.entries(rules)) {
        const error = validator(data?.[field], field);
        if (error) errors[field] = error;
      }
      return { valid: Object.keys(errors).length === 0, errors };
    };
  }
}

const validateUser = Validator.schema({
  name: Validator.string({ required: true, minLength: 2, maxLength: 50 }),
  email: Validator.string({ required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ }),
  age: Validator.number({ min: 0, max: 150, integer: true })
});

console.log(validateUser({ name: 'Alice', email: 'alice@example.com', age: 30 }));
// { valid: true, errors: {} }
console.log(validateUser({ name: 'A', email: 'not-email', age: -1 }));
// { valid: false, errors: { name: '...', email: '...', age: '...' } }
```

---

## Step 7: Secure Coding Demo

```javascript
// Demonstrate prototype pollution blocked
const safe = (obj, key, value) => {
  if (key.includes('__proto__') || key.includes('constructor') || key.includes('prototype')) {
    throw new Error('Prototype pollution attempt blocked');
  }
  const keys = key.split('.');
  let curr = obj;
  for (let i = 0; i < keys.length - 1; i++) curr = curr[keys[i]] ??= {};
  curr[keys[keys.length - 1]] = value;
};

// Path traversal blocked
const path = require('node:path');
function safeReadPath(base, userInput) {
  const resolved = path.resolve(base, userInput);
  if (!resolved.startsWith(base)) throw new Error('Path traversal detected');
  return resolved;
}

// Email validation
const safeEmail = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const safe = (obj, key, value) => {
  if (key.includes(\"__proto__\") || key.includes(\"constructor\") || key.includes(\"prototype\")) {
    throw new Error(\"Prototype pollution attempt blocked\");
  }
  const keys = key.split(\".\");
  let curr = obj;
  for (let i = 0; i < keys.length - 1; i++) curr = curr[keys[i]] ??= {};
  curr[keys[keys.length - 1]] = value;
};
try { safe({}, \"__proto__.admin\", true); }
catch(e) { console.log(\"Blocked:\", e.message); }
const safeEmail = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
console.log(\"Email valid:\", safeEmail.test(\"user@example.com\"));
console.log(\"Email invalid:\", safeEmail.test(\"not-an-email\"));
const path = require(\"path\");
function safeReadPath(base, userInput) {
  const resolved = path.resolve(base, userInput);
  if (!resolved.startsWith(base)) throw new Error(\"Path traversal detected\");
  return resolved;
}
try { safeReadPath(\"/app/uploads\", \"../../etc/passwd\"); }
catch(e) { console.log(\"Blocked:\", e.message); }
console.log(\"Safe path:\", safeReadPath(\"/app/uploads\", \"image.png\"));
'"
```

📸 **Verified Output:**
```
Blocked: Prototype pollution attempt blocked
Email valid: true
Email invalid: false
Blocked: Path traversal detected
Safe path: /app/uploads/image.png
```

---

## Summary

| Vulnerability | Attack | Defense |
|---------------|--------|---------|
| Prototype pollution | `{"__proto__": {...}}` | Check keys, use `Object.create(null)` |
| ReDoS | Complex regex + long input | Timeout, rewrite patterns |
| Path traversal | `../../etc/passwd` | `path.resolve` + starts-with check |
| SQL injection | `'; DROP TABLE` | Parameterized queries |
| XSS | `<script>` in input | Escape HTML, CSP headers |
| CSRF | Forged requests | CSRF tokens, SameSite cookies |
| Deserialize | `eval(untrustedData)` | JSON.parse + validation only |
| DoS | Unbounded resources | Rate limiting, input size limits |
