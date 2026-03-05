# Lab 09: Design Patterns

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Implement classic design patterns in modern JavaScript: Observer/EventEmitter, Factory, Singleton, Strategy, Decorator, and Command patterns using Node.js built-ins.

---

## Step 1: Observer / EventEmitter

```javascript
const { EventEmitter } = require('events');

// Basic EventEmitter usage
class DataStore extends EventEmitter {
  #data = new Map();

  set(key, value) {
    const old = this.#data.get(key);
    this.#data.set(key, value);
    this.emit('change', { key, value, old });
    if (old === undefined) this.emit('add', { key, value });
    return this;
  }

  get(key) { return this.#data.get(key); }

  delete(key) {
    const value = this.#data.get(key);
    if (this.#data.delete(key)) this.emit('delete', { key, value });
    return this;
  }

  get size() { return this.#data.size; }
}

const store = new DataStore();
store.on('change', ({ key, value }) => console.log(`Changed: ${key} = ${value}`));
store.on('add', ({ key }) => console.log(`New key added: ${key}`));
store.on('delete', ({ key }) => console.log(`Deleted: ${key}`));

store.set('name', 'Alice'); // New key added: name / Changed: name = Alice
store.set('name', 'Bob');   // Changed: name = Bob
store.delete('name');        // Deleted: name

// Once listener
store.once('add', ({ key }) => console.log(`First add: ${key}`));
store.set('x', 1); // First add: x
store.set('y', 2); // (once listener already fired)
```

---

## Step 2: Factory Pattern

```javascript
// Factory function — create objects without `new`
function createButton(options = {}) {
  const {
    label = 'Click me',
    type = 'primary',
    disabled = false,
    onClick = () => {}
  } = options;

  return {
    label,
    type,
    disabled,
    click() {
      if (disabled) { console.log(`Button "${label}" is disabled`); return; }
      console.log(`Button "${label}" clicked`);
      onClick();
    },
    render() { return `<button type="${type}" ${disabled ? 'disabled' : ''}>${label}</button>`; }
  };
}

// Factory Class — use `new` with configuration
class ShapeFactory {
  static #creators = {};

  static register(type, creator) {
    ShapeFactory.#creators[type] = creator;
  }

  static create(type, ...args) {
    const creator = ShapeFactory.#creators[type];
    if (!creator) throw new Error(`Unknown shape type: ${type}`);
    return creator(...args);
  }
}

ShapeFactory.register('circle', (r) => ({
  type: 'circle', radius: r,
  area: () => Math.PI * r * r,
  toString: () => `Circle(r=${r})`
}));

ShapeFactory.register('rect', (w, h) => ({
  type: 'rectangle', width: w, height: h,
  area: () => w * h,
  toString: () => `Rect(${w}x${h})`
}));

const c = ShapeFactory.create('circle', 5);
const r = ShapeFactory.create('rect', 4, 6);
console.log(c.toString(), c.area().toFixed(2)); // Circle(r=5) 78.54
console.log(r.toString(), r.area());            // Rect(4x6) 24
```

---

## Step 3: Singleton Pattern

```javascript
// Singleton — one instance per application
class Config {
  static #instance = null;
  #data;

  constructor(defaults = {}) {
    if (Config.#instance) return Config.#instance;
    this.#data = new Map(Object.entries(defaults));
    Config.#instance = this;
  }

  get(key, defaultValue) {
    return this.#data.has(key) ? this.#data.get(key) : defaultValue;
  }

  set(key, value) {
    this.#data.set(key, value);
    return this;
  }

  static getInstance(defaults) {
    if (!Config.#instance) new Config(defaults);
    return Config.#instance;
  }

  static reset() { Config.#instance = null; } // For testing
}

// Module-level singleton (simpler in ES modules)
const appConfig = Config.getInstance({
  env: 'production',
  debug: false,
  maxRetries: 3
});

const sameConfig = Config.getInstance();
console.log(appConfig === sameConfig); // true

appConfig.set('timeout', 5000);
console.log(sameConfig.get('timeout')); // 5000 (same instance)
console.log(appConfig.get('env'));      // production
```

---

## Step 4: Strategy Pattern

```javascript
// Strategy — interchangeable algorithms
class Sorter {
  #strategy;

  constructor(strategy) { this.#strategy = strategy; }

  setStrategy(strategy) { this.#strategy = strategy; return this; }

  sort(data) { return this.#strategy.sort([...data]); }
}

// Concrete strategies
const bubbleSort = {
  name: 'bubble',
  sort(arr) {
    const a = [...arr];
    for (let i = 0; i < a.length; i++)
      for (let j = 0; j < a.length - i - 1; j++)
        if (a[j] > a[j+1]) [a[j], a[j+1]] = [a[j+1], a[j]];
    return a;
  }
};

const quickSort = {
  name: 'quick',
  sort(arr) {
    if (arr.length <= 1) return arr;
    const pivot = arr[Math.floor(arr.length / 2)];
    const left = arr.filter(x => x < pivot);
    const mid = arr.filter(x => x === pivot);
    const right = arr.filter(x => x > pivot);
    return [...quickSort.sort(left), ...mid, ...quickSort.sort(right)];
  }
};

const data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3];
const sorter = new Sorter(bubbleSort);
console.log(sorter.sort(data));
sorter.setStrategy(quickSort);
console.log(sorter.sort(data));

// Payment strategy example
const paymentStrategies = {
  creditCard: { process: (amount) => `Charged $${amount} to credit card` },
  paypal: { process: (amount) => `Sent $${amount} via PayPal` },
  crypto: { process: (amount) => `Transferred ${(amount / 50000).toFixed(6)} BTC` }
};

function checkout(amount, method) {
  const strategy = paymentStrategies[method];
  if (!strategy) throw new Error(`Unsupported: ${method}`);
  return strategy.process(amount);
}
console.log(checkout(99.99, 'paypal'));
```

---

## Step 5: Decorator Pattern

```javascript
// Functional decorator
function readonly(fn) {
  return function(...args) {
    const result = fn.apply(this, args);
    return typeof result === 'object' ? Object.freeze(result) : result;
  };
}

function memoize(fn) {
  const cache = new Map();
  return function(...args) {
    const key = JSON.stringify(args);
    if (!cache.has(key)) cache.set(key, fn.apply(this, args));
    return cache.get(key);
  };
}

function timed(fn, label = fn.name) {
  return function(...args) {
    console.time(label);
    const result = fn.apply(this, args);
    console.timeEnd(label);
    return result;
  };
}

// Class decorator (manual implementation)
function logged(Class) {
  return class extends Class {
    constructor(...args) {
      super(...args);
      console.log(`${Class.name} instance created`);
    }
  };
}

function withTimestamp(Class) {
  return class extends Class {
    constructor(...args) {
      super(...args);
      this.createdAt = new Date().toISOString();
    }
  };
}

class User { constructor(name) { this.name = name; } }
const TimestampedUser = withTimestamp(logged(User));
const u = new TimestampedUser('Alice'); // logs: "User instance created"
console.log(u.createdAt ? 'Has timestamp' : 'No timestamp');
```

---

## Step 6: Command Pattern

```javascript
// Command pattern — encapsulate operations as objects
class TextEditor {
  #content = '';
  #history = [];
  #redoStack = [];

  execute(command) {
    command.execute(this);
    this.#history.push(command);
    this.#redoStack = [];
  }

  undo() {
    const command = this.#history.pop();
    if (command) {
      command.undo(this);
      this.#redoStack.push(command);
    }
  }

  redo() {
    const command = this.#redoStack.pop();
    if (command) {
      command.execute(this);
      this.#history.push(command);
    }
  }

  get content() { return this.#content; }
  set content(v) { this.#content = v; }
}

// Commands
const insertCommand = (text, position) => ({
  execute(editor) {
    const c = editor.content;
    editor.content = c.slice(0, position) + text + c.slice(position);
  },
  undo(editor) {
    const c = editor.content;
    editor.content = c.slice(0, position) + c.slice(position + text.length);
  }
});

const editor = new TextEditor();
editor.execute(insertCommand('Hello', 0));
editor.execute(insertCommand(' World', 5));
console.log(editor.content); // Hello World
editor.undo();
console.log(editor.content); // Hello
editor.redo();
console.log(editor.content); // Hello World
```

---

## Step 7: Combining Patterns

```javascript
const { EventEmitter } = require('events');

// Observer + Command + Singleton
class EventBus extends EventEmitter {
  static #instance = null;
  #commandHistory = [];

  static getInstance() {
    if (!EventBus.#instance) EventBus.#instance = new EventBus();
    return EventBus.#instance;
  }

  dispatch(event, data) {
    this.#commandHistory.push({ event, data, time: Date.now() });
    this.emit(event, data);
  }

  getHistory() { return [...this.#commandHistory]; }
}

const bus = EventBus.getInstance();
bus.on('user:login', ({ name }) => console.log(`${name} logged in`));
bus.on('user:logout', ({ name }) => console.log(`${name} logged out`));
bus.dispatch('user:login', { name: 'Alice', userId: 1 });
bus.dispatch('user:logout', { name: 'Alice', userId: 1 });
console.log('Events dispatched:', bus.getHistory().length);
```

---

## Step 8: Capstone — Observer + Singleton + Factory Demo

```javascript
const { EventEmitter } = require('events');
class Store extends EventEmitter {
  #state;
  constructor(initial) { super(); this.#state = initial; }
  setState(updater) {
    const prev = this.#state;
    this.#state = typeof updater === 'function' ? updater(prev) : updater;
    this.emit('change', this.#state, prev);
  }
  getState() { return this.#state; }
}
const store = new Store({ count: 0 });
store.on('change', (next, prev) => console.log('State:', prev.count, '->', next.count));
store.setState(s => ({ count: s.count + 1 }));
store.setState(s => ({ count: s.count + 5 }));
class Config {
  static #instance = null;
  constructor(data) { this.data = data; }
  static getInstance() {
    if (!Config.#instance) Config.#instance = new Config({env: 'prod'});
    return Config.#instance;
  }
}
const c1 = Config.getInstance();
const c2 = Config.getInstance();
console.log(c1 === c2, c1.data.env);
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const { EventEmitter } = require(\"events\");
class Store extends EventEmitter {
  #state;
  constructor(initial) { super(); this.#state = initial; }
  setState(updater) {
    const prev = this.#state;
    this.#state = typeof updater === \"function\" ? updater(prev) : updater;
    this.emit(\"change\", this.#state, prev);
  }
  getState() { return this.#state; }
}
const store = new Store({ count: 0 });
store.on(\"change\", (next, prev) => console.log(\"State:\", prev.count, \"->\", next.count));
store.setState(s => ({ count: s.count + 1 }));
store.setState(s => ({ count: s.count + 5 }));
class Config {
  static #instance = null;
  constructor(data) { this.data = data; }
  static getInstance() {
    if (!Config.#instance) Config.#instance = new Config({env: \"prod\"});
    return Config.#instance;
  }
}
const c1 = Config.getInstance(); const c2 = Config.getInstance();
console.log(c1 === c2, c1.data.env);
'"
```

📸 **Verified Output:**
```
State: 0 -> 1
State: 1 -> 6
true prod
```

---

## Summary

| Pattern | Intent | Node.js Use Case |
|---------|--------|-----------------|
| Observer | Notify many on state change | EventEmitter, pub/sub |
| Factory | Create without specifying exact class | Plugins, shapes, UI components |
| Singleton | Single global instance | Config, DB connection, EventBus |
| Strategy | Swap algorithms at runtime | Sorting, auth, payment |
| Decorator | Add behavior without changing class | Logging, caching, retry |
| Command | Encapsulate operations | Undo/redo, job queues, audit |
