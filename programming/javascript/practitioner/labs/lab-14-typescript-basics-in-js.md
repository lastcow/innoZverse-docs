# Lab 14: TypeScript Basics in JavaScript

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Use TypeScript features within JavaScript: JSDoc type annotations, `@ts-check`, optional chaining (`?.`), nullish coalescing (`??`), logical assignment operators (`&&=`/`||=`/`??=`), and the modern safety operators.

---

## Step 1: Optional Chaining (?.)

```javascript
// Without optional chaining — verbose null checks
function getCity_old(user) {
  return user && user.address && user.address.city;
}

// With optional chaining — clean and safe
function getCity(user) {
  return user?.address?.city;
}

const users = [
  { name: 'Alice', address: { city: 'New York', zip: '10001' } },
  { name: 'Bob', address: null },
  { name: 'Charlie' } // No address property
];

users.forEach(u => {
  console.log(u.name, '->', getCity(u) ?? '(no city)');
});
// Alice -> New York
// Bob -> (no city)
// Charlie -> (no city)

// Optional chaining with method calls
const config = {
  getTheme: () => 'dark',
  // getLocale is missing
};
console.log(config.getTheme?.());  // 'dark'
console.log(config.getLocale?.());  // undefined (no error!)

// Optional chaining with arrays
const data = { items: [1, 2, 3] };
const empty = {};
console.log(data.items?.[0]); // 1
console.log(empty.items?.[0]); // undefined (not a TypeError!)
```

> 💡 `?.` short-circuits: if the left side is `null` or `undefined`, the whole expression returns `undefined` without evaluating the rest.

---

## Step 2: Nullish Coalescing (??)

```javascript
// ?? returns right side only when left is null or undefined
// Unlike ||, it doesn't treat 0, '', or false as falsy!

const userSettings = {
  theme: '',       // Intentionally empty
  volume: 0,       // Intentionally zero
  notifications: false, // Intentionally false
  username: null   // Not set
};

// OLD way with || — WRONG for falsy values
const theme_bad = userSettings.theme || 'light'; // 'light' (wrong! overwrites '')
const volume_bad = userSettings.volume || 50;    // 50 (wrong! 0 is valid)

// CORRECT with ??
const theme = userSettings.theme ?? 'light';           // '' (empty string preserved)
const volume = userSettings.volume ?? 50;              // 0 (zero preserved)
const notifs = userSettings.notifications ?? true;     // false (false preserved)
const username = userSettings.username ?? 'Anonymous'; // 'Anonymous' (null replaced)

console.log({ theme, volume, notifs, username });
// { theme: '', volume: 0, notifs: false, username: 'Anonymous' }

// Chaining
const firstName = null;
const lastName = undefined;
const displayName = firstName ?? lastName ?? 'Guest';
console.log(displayName); // 'Guest'

// Combined with optional chaining
const appName = process.env.APP_NAME ?? config?.app?.name ?? 'MyApp';
```

---

## Step 3: Logical Assignment Operators

```javascript
// &&= — assign only if left is truthy
let user = { name: 'Alice', verified: true };
user.verified &&= 'email'; // user.verified is truthy, so assign
console.log(user.verified); // 'email'

let guest = { name: 'Guest', verified: false };
guest.verified &&= 'email'; // verified is falsy, no assignment
console.log(guest.verified); // false

// ||= — assign only if left is falsy
let settings = { theme: null, lang: 'en' };
settings.theme ||= 'dark';  // null is falsy, assign 'dark'
settings.lang ||= 'fr';     // 'en' is truthy, no assignment
console.log(settings); // { theme: 'dark', lang: 'en' }

// ??= — assign only if left is null or undefined
let config = { timeout: 0, name: null };
config.timeout ??= 5000; // 0 is not null/undefined, no assignment!
config.name ??= 'default';
config.host ??= 'localhost'; // undefined, assign

console.log(config); // { timeout: 0, name: 'default', host: 'localhost' }

// Real-world use case: default initialization
function initializeCache(options = {}) {
  options.maxSize ??= 1000;
  options.ttl ??= 3600;
  options.strategy ??= 'lru';
  options.debug ||= false;
  return options;
}

console.log(initializeCache({ maxSize: 500 }));
// { maxSize: 500, ttl: 3600, strategy: 'lru', debug: false }
```

---

## Step 4: JSDoc Type Annotations

```javascript
// @ts-check enables TypeScript checking in JS files!
// Add to top of file: // @ts-check

/**
 * Represents a product in the catalog
 * @typedef {Object} Product
 * @property {string} id - Unique identifier
 * @property {string} name - Product name
 * @property {number} price - Price in USD
 * @property {string[]} [tags] - Optional tags
 * @property {'in_stock' | 'out_of_stock' | 'discontinued'} status
 */

/**
 * Calculate the discounted price of a product
 * @param {Product} product - The product
 * @param {number} discountPercent - Discount percentage (0-100)
 * @returns {number} Discounted price
 */
function getDiscountedPrice(product, discountPercent) {
  if (discountPercent < 0 || discountPercent > 100) {
    throw new RangeError('Discount must be 0-100');
  }
  return product.price * (1 - discountPercent / 100);
}

/**
 * @template T
 * @param {T[]} items - Array of items
 * @param {(item: T) => string} keyFn - Key extractor function
 * @returns {Map<string, T>} Map of items by key
 */
function groupBy(items, keyFn) {
  return items.reduce((map, item) => {
    const key = keyFn(item);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(item);
    return map;
  }, new Map());
}

// Usage
const products = [
  { id: 'p1', name: 'Widget', price: 9.99, status: 'in_stock' },
  { id: 'p2', name: 'Gadget', price: 24.99, status: 'out_of_stock' }
];

console.log(getDiscountedPrice(products[0], 20)); // 7.992
```

---

## Step 5: Modern JavaScript Type Safety

```javascript
// TypeScript-like validation patterns in JavaScript

// Type checking utilities
const is = {
  string: (v) => typeof v === 'string',
  number: (v) => typeof v === 'number' && !isNaN(v),
  array: (v) => Array.isArray(v),
  object: (v) => v !== null && typeof v === 'object' && !Array.isArray(v),
  defined: (v) => v !== null && v !== undefined,
};

// Runtime type assertion
function assertString(value, name = 'value') {
  if (!is.string(value)) throw new TypeError(`${name} must be a string, got ${typeof value}`);
  return value;
}

function assertPositiveNumber(value, name = 'value') {
  if (!is.number(value) || value <= 0) {
    throw new RangeError(`${name} must be a positive number, got ${value}`);
  }
  return value;
}

// Structured clone (safe deep copy)
const original = { a: 1, b: { c: [1, 2, 3] }, d: new Date() };
const clone = structuredClone(original);
clone.b.c.push(4);
console.log(original.b.c.length); // 3 (unchanged)
console.log(clone.b.c.length);    // 4

// Object.hasOwn (safe alternative to hasOwnProperty)
const obj = { name: 'Alice' };
console.log(Object.hasOwn(obj, 'name'));        // true
console.log(Object.hasOwn(obj, 'constructor')); // false (prototype)
```

---

## Step 6: Practical Modern Patterns

```javascript
// at() — negative indexing
const fruits = ['apple', 'banana', 'cherry', 'date'];
console.log(fruits.at(-1));  // 'date' (last element)
console.log(fruits.at(-2));  // 'cherry'
console.log(fruits.at(0));   // 'apple'

// Array grouping (Object.groupBy)
const items = [
  { name: 'Widget', category: 'hardware' },
  { name: 'Gadget', category: 'electronics' },
  { name: 'Doohickey', category: 'hardware' }
];

// Polyfill if Object.groupBy not available
const groupByCategory = Object.groupBy
  ? Object.groupBy(items, item => item.category)
  : items.reduce((acc, item) => {
      (acc[item.category] ??= []).push(item);
      return acc;
    }, {});

console.log(Object.keys(groupByCategory)); // ['hardware', 'electronics']

// Promise.withResolvers (Node.js 22+, or polyfill)
function withResolvers() {
  let resolve, reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

const { promise, resolve } = withResolvers();
setTimeout(() => resolve('done!'), 10);
promise.then(v => console.log('Resolved:', v));
```

---

## Step 7: Error Handling with Modern Syntax

```javascript
// Using ?? and ?. for safer error handling
class ApiClient {
  #baseUrl;
  #defaultHeaders;

  constructor(options = {}) {
    this.#baseUrl = options.baseUrl ?? 'https://api.example.com';
    this.#defaultHeaders = {
      'Content-Type': 'application/json',
      ...(options.apiKey && { 'X-API-Key': options.apiKey }),
      ...options.headers
    };
  }

  async request(path, options = {}) {
    const url = new URL(path, this.#baseUrl);
    
    // Add query params safely
    for (const [key, value] of Object.entries(options.params ?? {})) {
      url.searchParams.set(key, value);
    }

    try {
      const response = await fetch(url, {
        method: options.method ?? 'GET',
        headers: { ...this.#defaultHeaders, ...options.headers },
        body: options.body ? JSON.stringify(options.body) : undefined
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(data?.message ?? `HTTP ${response.status}`);
      }

      return data;
    } catch (e) {
      throw new Error(`Request to ${path} failed: ${e.message}`, { cause: e });
    }
  }
}
```

---

## Step 8: Capstone — Type-Safe Utilities

```javascript
// All modern JS features together
const userSettings = { theme: '', volume: 0, notifications: false, username: null };

const theme = userSettings.theme ?? 'light';
const volume = userSettings.volume ?? 50;
const username = userSettings.username ?? 'Anonymous';
console.log({ theme, volume, username });

// Optional chaining
const users = [
  { name: 'Alice', address: { city: 'SF' } },
  { name: 'Bob' }
];
users.forEach(u => console.log(u.name, u?.address?.city ?? 'unknown'));

// Logical assignment
let opts = { maxSize: 0, name: null };
opts.maxSize ??= 1000; opts.name ??= 'default'; opts.debug ??= false;
console.log(opts);
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const userSettings = { theme: \"\", volume: 0, notifications: false, username: null };
const theme = userSettings.theme ?? \"light\";
const volume = userSettings.volume ?? 50;
const notifs = userSettings.notifications ?? true;
const username = userSettings.username ?? \"Anonymous\";
console.log({ theme, volume, notifs, username });

let config = { timeout: 0, name: null };
config.timeout ??= 5000;
config.name ??= \"default\";
config.host ??= \"localhost\";
console.log(config);

const fruits = [\"apple\", \"banana\", \"cherry\"];
console.log(fruits.at(-1));
'"
```

📸 **Verified Output:**
```
{ theme: '', volume: 0, notifs: false, username: 'Anonymous' }
{ timeout: 0, name: 'default', host: 'localhost' }
cherry
```

---

## Summary

| Feature | Syntax | Behavior |
|---------|--------|----------|
| Optional chaining | `obj?.prop` | Returns `undefined` if `obj` is null/undefined |
| Optional method call | `obj?.method()` | Calls only if method exists |
| Optional index | `arr?.[i]` | Indexes only if arr is defined |
| Nullish coalescing | `a ?? b` | Returns `b` only if `a` is null/undefined |
| Logical AND assign | `a &&= b` | Assigns `b` only if `a` is truthy |
| Logical OR assign | `a \|\|= b` | Assigns `b` only if `a` is falsy |
| Nullish assign | `a ??= b` | Assigns `b` only if `a` is null/undefined |
| JSDoc `@type` | `/** @type {string} */` | Editor/TypeScript hints |
| `@ts-check` | File comment | Enable TS checking in .js |
