# Lab 01: ES6 Destructuring & Spread

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master modern JavaScript syntax: destructuring assignments, rest/spread operators, computed property names, and shorthand methods. These features make code cleaner and more expressive.

---

## Step 1: Array Destructuring

```javascript
// Basic array destructuring
const [first, second, third] = [10, 20, 30];
console.log(first, second, third); // 10 20 30

// Skipping elements
const [, , last] = [1, 2, 3];
console.log(last); // 3

// Default values
const [a = 0, b = 0, c = 0] = [1, 2];
console.log(a, b, c); // 1 2 0

// Swapping variables
let x = 1, y = 2;
[x, y] = [y, x];
console.log(x, y); // 2 1
```

> 💡 Destructuring doesn't mutate the original array. It creates new bindings.

---

## Step 2: Object Destructuring

```javascript
const user = { name: 'Alice', age: 30, role: 'admin' };

// Basic object destructuring
const { name, age } = user;
console.log(name, age); // Alice 30

// Renaming
const { name: userName, role: userRole } = user;
console.log(userName, userRole); // Alice admin

// Default values
const { name: n, country = 'US' } = user;
console.log(n, country); // Alice US
```

> 💡 Object destructuring uses property names as keys; order doesn't matter unlike arrays.

---

## Step 3: Nested Destructuring

```javascript
const config = {
  server: {
    host: 'localhost',
    port: 3000,
    tls: { cert: '/etc/ssl/cert.pem', key: '/etc/ssl/key.pem' }
  },
  database: { url: 'postgres://localhost/mydb' }
};

const {
  server: { host, port, tls: { cert } },
  database: { url: dbUrl }
} = config;

console.log(host, port);  // localhost 3000
console.log(cert);        // /etc/ssl/cert.pem
console.log(dbUrl);       // postgres://localhost/mydb

// In function parameters
function connect({ host = 'localhost', port = 3000, tls = false } = {}) {
  return `${tls ? 'https' : 'http'}://${host}:${port}`;
}
console.log(connect({ host: 'example.com', tls: true })); // https://example.com:3000
```

---

## Step 4: Rest Parameters

```javascript
// Rest in array destructuring
const [head, ...tail] = [1, 2, 3, 4, 5];
console.log(head); // 1
console.log(tail); // [2, 3, 4, 5]

// Rest in object destructuring
const { name: personName, ...rest } = { name: 'Bob', age: 25, city: 'NY' };
console.log(personName); // Bob
console.log(rest);       // { age: 25, city: 'NY' }

// Rest in function parameters
function sum(first, ...numbers) {
  return first + numbers.reduce((acc, n) => acc + n, 0);
}
console.log(sum(1, 2, 3, 4, 5)); // 15
```

> 💡 Rest must always be the **last** element. `const [...rest, last]` is a syntax error.

---

## Step 5: Spread Operator

```javascript
// Spread in arrays
const arr1 = [1, 2, 3];
const arr2 = [4, 5, 6];
const combined = [...arr1, ...arr2];
console.log(combined); // [1, 2, 3, 4, 5, 6]

// Copy array (shallow)
const original = [1, 2, { nested: true }];
const copy = [...original];
copy.push(4);
console.log(original.length, copy.length); // 3 4

// Spread in objects (ES2018)
const defaults = { theme: 'dark', lang: 'en', fontSize: 14 };
const userPrefs = { theme: 'light', fontSize: 16 };
const merged = { ...defaults, ...userPrefs };
console.log(merged); // { theme: 'light', lang: 'en', fontSize: 16 }

// Spread with function calls
const numbers = [3, 1, 4, 1, 5, 9];
console.log(Math.max(...numbers)); // 9
```

---

## Step 6: Computed Property Names

```javascript
const prefix = 'get';
const entity = 'User';

const api = {
  [`${prefix}${entity}`]: () => ({ id: 1, name: 'Alice' }),
  [`${prefix}All${entity}s`]: () => [{ id: 1 }, { id: 2 }],
};

console.log(api.getUser());     // { id: 1, name: 'Alice' }
console.log(api.getAllUsers()); // [{ id: 1 }, { id: 2 }]

// Dynamic key from variable
function createLookup(items, keyField) {
  return items.reduce((acc, item) => ({
    ...acc,
    [item[keyField]]: item
  }), {});
}

const users = [{ id: 'a1', name: 'Alice' }, { id: 'b2', name: 'Bob' }];
const lookup = createLookup(users, 'id');
console.log(lookup['a1']); // { id: 'a1', name: 'Alice' }
```

---

## Step 7: Shorthand Methods & Property Shorthand

```javascript
const name = 'Alice';
const age = 30;

// Property shorthand (ES6)
const person = { name, age };
console.log(person); // { name: 'Alice', age: 30 }

// Method shorthand
const calculator = {
  value: 0,
  add(n) { this.value += n; return this; },
  subtract(n) { this.value -= n; return this; },
  multiply(n) { this.value *= n; return this; },
  result() { return this.value; }
};

const result = calculator.add(10).multiply(3).subtract(5).result();
console.log(result); // 25

// Getter/Setter shorthand
const circle = {
  _radius: 5,
  get radius() { return this._radius; },
  set radius(r) {
    if (r < 0) throw new RangeError('Radius must be non-negative');
    this._radius = r;
  },
  get area() { return Math.PI * this._radius ** 2; }
};

console.log(circle.radius);           // 5
console.log(circle.area.toFixed(2));  // 78.54
```

---

## Step 8: Capstone — Config Parser

Build a configuration parser that uses all concepts from this lab:

```javascript
// Complete config parser using all ES6 syntax features
const defaultConfig = {
  server: { host: 'localhost', port: 3000, ssl: false },
  database: { host: 'localhost', port: 5432, name: 'myapp' },
  cache: { ttl: 3600, maxSize: 1000 },
  features: ['auth', 'logging']
};

function parseConfig(userConfig = {}) {
  const {
    server: {
      host: serverHost = defaultConfig.server.host,
      port: serverPort = defaultConfig.server.port,
      ssl = defaultConfig.server.ssl,
      ...serverExtra
    } = {},
    database: dbConfig = {},
    cache: { ttl = 3600, maxSize = 1000 } = {},
    features: userFeatures = [],
    ...appConfig
  } = userConfig;

  const db = { ...defaultConfig.database, ...dbConfig };
  const features = [...defaultConfig.features, ...userFeatures];
  const serverUrl = `${ssl ? 'https' : 'http'}://${serverHost}:${serverPort}`;

  return {
    serverUrl,
    db,
    cache: { ttl, maxSize },
    features,
    ...appConfig
  };
}

const config = parseConfig({
  server: { host: 'api.example.com', port: 443, ssl: true },
  database: { name: 'production_db' },
  features: ['analytics'],
  appName: 'MyApp'
});

console.log('Server URL:', config.serverUrl);
console.log('DB name:', config.db.name);
console.log('Features:', config.features);
console.log('App name:', config.appName);
```

**Run it:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const [a, b, ...rest] = [1, 2, 3, 4, 5];
console.log(a, b, rest);
const {name, age = 25, address: {city} = {city: \"NYC\"}} = {name: \"Alice\", address: {city: \"SF\"}};
console.log(name, age, city);
const arr1 = [1, 2]; const arr2 = [3, 4];
console.log([...arr1, ...arr2]);
const key = \"dynamic\";
const obj = {[key]: 42, shorthand() { return \"method\"; }};
console.log(obj.dynamic, obj.shorthand());
'"
```

📸 **Verified Output:**
```
1 2 [ 3, 4, 5 ]
Alice 25 SF
[ 1, 2, 3, 4 ]
42 method
```

---

## Summary

| Feature | Syntax | Use Case |
|---------|--------|----------|
| Array destructuring | `const [a, b] = arr` | Unpack arrays, swap vars |
| Object destructuring | `const {x, y} = obj` | Unpack objects, function params |
| Nested destructuring | `const {a: {b}} = obj` | Deep data extraction |
| Rest (array) | `const [first, ...rest] = arr` | Collect remaining elements |
| Rest (object) | `const {a, ...rest} = obj` | Omit specific properties |
| Rest (params) | `function f(...args)` | Variadic functions |
| Spread (array) | `[...arr1, ...arr2]` | Merge/copy arrays |
| Spread (object) | `{...obj1, ...obj2}` | Merge/copy objects |
| Computed props | `{[expr]: value}` | Dynamic property names |
| Shorthand | `{name, method() {}}` | Concise object literals |
