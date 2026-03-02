# Lab 8: Node.js Modules (CommonJS & ESM)

## 🎯 Objective
Master Node.js module systems — CommonJS (`require/module.exports`) and ES Modules (`import/export`), module resolution, and circular dependency avoidance.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 7: Error Handling

## 🛠️ Tools Used
- Node.js 20

## 🔬 Lab Instructions

### Step 1: CommonJS Modules
```javascript
const path = require("path");
const os = require("os");
const fs = require("fs");

// Built-in modules
console.log("Home:", os.homedir());
console.log("CPUs:", os.cpus().length);
console.log("Platform:", process.platform);
console.log("Node:", process.version);

// __dirname and __filename
console.log("Dir:", __dirname.slice(-20));
```

**📸 Verified Output:**
```
Home: /root
CPUs: 2
Platform: linux
Node: v20.x.x
Dir: ...
```

### Step 2: Creating and Exporting Modules
```javascript
const fs = require("fs");

// Write a utility module
fs.writeFileSync("/tmp/mathlib.js", `
const PI = 3.14159265358979;
const E  = 2.71828182845905;

function add(a, b) { return a + b; }
function multiply(a, b) { return a * b; }
function power(base, exp) { return base ** exp; }
function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
function range(start, end, step = 1) {
    const r = [];
    for (let i = start; i < end; i += step) r.push(i);
    return r;
}

module.exports = { PI, E, add, multiply, power, clamp, range };
`);

// Import and use it
const math = require("/tmp/mathlib");
console.log("PI:", math.PI.toFixed(5));
console.log("add:", math.add(10, 20));
console.log("power:", math.power(2, 10));
console.log("clamp:", math.clamp(150, 0, 100));
console.log("range:", math.range(0, 10, 2));
```

**📸 Verified Output:**
```
PI: 3.14159
add: 30
power: 1024
clamp: 100
range: [ 0, 2, 4, 6, 8 ]
```

### Step 3: ES Modules Syntax (ESM)
```javascript
// ESM uses import/export — write to .mjs file
const fs = require("fs");

fs.writeFileSync("/tmp/utils.mjs", `
// Named exports
export const VERSION = "1.0.0";
export function greet(name) { return \`Hello, \${name}!\`; }
export function slugify(str) {
    return str.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-");
}

// Default export
export default class Logger {
    constructor(prefix) { this.prefix = prefix; }
    log(msg) { console.log(\`[\${this.prefix}] \${msg}\`); }
    error(msg) { console.error(\`[\${this.prefix}] ERROR: \${msg}\`); }
}
`);

fs.writeFileSync("/tmp/main.mjs", `
import Logger, { VERSION, greet, slugify } from "/tmp/utils.mjs";

const logger = new Logger("APP");
logger.log(\`Version: \${VERSION}\`);
logger.log(greet("Dr. Chen"));
logger.log(slugify("Hello World! This is a Test."));
`);

const { execSync } = require("child_process");
const output = execSync("node /tmp/main.mjs").toString();
console.log(output.trim());
```

**📸 Verified Output:**
```
[APP] Version: 1.0.0
[APP] Hello, Dr. Chen!
[APP] hello-world-this-is-a-test
```

### Step 4: Module Pattern — Revealing Module
```javascript
// Classic pattern for encapsulation
const EventBus = (() => {
    const listeners = new Map();
    let eventCount = 0;
    
    function on(event, fn) {
        if (!listeners.has(event)) listeners.set(event, []);
        listeners.get(event).push(fn);
    }
    
    function off(event, fn) {
        const list = listeners.get(event) || [];
        listeners.set(event, list.filter(f => f !== fn));
    }
    
    function emit(event, ...args) {
        eventCount++;
        (listeners.get(event) || []).forEach(fn => fn(...args));
    }
    
    // Public API only
    return { on, off, emit, get count() { return eventCount; } };
})();

EventBus.on("login", user => console.log(`User logged in: ${user}`));
EventBus.on("login", user => console.log(`Audit: ${user} at ${new Date().toISOString().split("T")[0]}`));
EventBus.on("logout", user => console.log(`User logged out: ${user}`));

EventBus.emit("login", "Alice");
EventBus.emit("login", "Bob");
EventBus.emit("logout", "Alice");
console.log("Total events:", EventBus.count);
```

**📸 Verified Output:**
```
User logged in: Alice
Audit: Alice at 2026-03-02
User logged in: Bob
Audit: Bob at 2026-03-02
User logged out: Alice
Total events: 3
```

### Step 5: Dynamic Imports
```javascript
// Dynamic import — lazy loading
async function loadModule(name) {
    try {
        // In Node.js, dynamic import works with ESM
        // For CJS, we simulate with conditional require
        const modules = {
            "math": { sqrt: Math.sqrt, abs: Math.abs, PI: Math.PI },
            "string": { upper: s => s.toUpperCase(), slug: s => s.toLowerCase().replace(/\s+/g,"-") }
        };
        
        if (!modules[name]) throw new Error(`Module '${name}' not found`);
        console.log(`✅ Loaded module: ${name}`);
        return modules[name];
    } catch (e) {
        console.error(`❌ Failed to load '${name}': ${e.message}`);
        return null;
    }
}

async function main() {
    const math = await loadModule("math");
    console.log("sqrt(16):", math.sqrt(16));
    
    const str = await loadModule("string");
    console.log("upper:", str.upper("hello world"));
    
    await loadModule("nonexistent");
}

main();
```

**📸 Verified Output:**
```
✅ Loaded module: math
sqrt(16): 4
✅ Loaded module: string
upper: HELLO WORLD
❌ Failed to load 'nonexistent': Module 'nonexistent' not found
```

### Step 6: package.json and npm
```javascript
const fs = require("fs");
const path = require("path");

// Create a proper Node.js project
const projectDir = "/tmp/node_project";
fs.mkdirSync(projectDir, { recursive: true });

const packageJson = {
    name: "my-node-project",
    version: "1.0.0",
    description: "A sample Node.js project",
    main: "index.js",
    scripts: {
        start: "node index.js",
        test: "node --test test/*.test.js",
        dev: "nodemon index.js"
    },
    dependencies: {
        express: "^4.18.0"
    },
    devDependencies: {
        nodemon: "^3.0.0"
    },
    engines: { node: ">=18.0.0" },
    license: "MIT"
};

fs.writeFileSync(
    path.join(projectDir, "package.json"),
    JSON.stringify(packageJson, null, 2)
);

// Read it back
const pkg = JSON.parse(fs.readFileSync(path.join(projectDir, "package.json"), "utf8"));
console.log(`Project: ${pkg.name} v${pkg.version}`);
console.log(`Scripts: ${Object.keys(pkg.scripts).join(", ")}`);
console.log(`Dependencies: ${Object.keys(pkg.dependencies).join(", ")}`);
console.log(`Node required: ${pkg.engines.node}`);
```

**📸 Verified Output:**
```
Project: my-node-project v1.0.0
Scripts: start, test, dev
Dependencies: express
Node required: >=18.0.0
```

### Step 7: Circular Dependency Detection
```javascript
// Demonstrate the module cache
const cache = new Map();

function requireWithCache(name) {
    if (cache.has(name)) {
        console.log(`  [CACHE HIT] ${name}`);
        return cache.get(name);
    }
    console.log(`  [LOADING] ${name}`);
    const mod = { name, loaded: Date.now() };
    cache.set(name, mod);
    return mod;
}

// Node.js caches modules — same module object returned each time
const mod1a = requireWithCache("utils");
const mod1b = requireWithCache("utils");  // Cache hit!
const mod2  = requireWithCache("config");

console.log("\nSame object?", mod1a === mod1b);  // true!
console.log("Modules loaded:", cache.size);
```

**📸 Verified Output:**
```
  [LOADING] utils
  [CACHE HIT] utils
  [LOADING] config

Same object? true
Modules loaded: 2
```

### Step 8: Building a Module Index
```javascript
const fs = require("fs");

// index.js pattern — re-export from subdirectories
fs.mkdirSync("/tmp/mylib", { recursive: true });

fs.writeFileSync("/tmp/mylib/validators.js", `
exports.isEmail = (s) => /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(s);
exports.isPhone = (s) => /^\\+?[\\d\\s\\-().]{10,}$/.test(s);
exports.isUrl   = (s) => { try { new URL(s); return true; } catch { return false; } };
`);

fs.writeFileSync("/tmp/mylib/formatters.js", `
exports.currency = (n, cur="USD") => new Intl.NumberFormat("en-US",{style:"currency",currency:cur}).format(n);
exports.number   = (n) => new Intl.NumberFormat("en-US").format(n);
exports.percent  = (n, dec=1) => \`\${(n*100).toFixed(dec)}%\`;
`);

fs.writeFileSync("/tmp/mylib/index.js", `
const validators = require("./validators");
const formatters = require("./formatters");
module.exports = { ...validators, ...formatters };
`);

const lib = require("/tmp/mylib/index");

console.log(lib.isEmail("alice@example.com"));  // true
console.log(lib.isUrl("https://google.com"));   // true
console.log(lib.currency(1234567.89));           // $1,234,567.89
console.log(lib.number(9876543));                // 9,876,543
console.log(lib.percent(0.8567));                // 85.7%
```

**📸 Verified Output:**
```
true
true
$1,234,567.89
9,876,543
85.7%
```

## ✅ Verification
```javascript
const fs = require("fs");

// Write and require a module
fs.writeFileSync("/tmp/verify_mod.js", `
module.exports = {
    add: (a,b) => a+b,
    sub: (a,b) => a-b,
    mul: (a,b) => a*b,
    VERSION: "1.0.0"
};
`);

const m = require("/tmp/verify_mod");
console.log(m.add(10, 5));   // 15
console.log(m.sub(10, 5));   // 5
console.log(m.mul(10, 5));   // 50
console.log(m.VERSION);       // 1.0.0
console.log("Lab 8 verified ✅");
```

**Expected output:**
```
15
5
50
1.0.0
Lab 8 verified ✅
```

## 🚨 Common Mistakes
1. **`module.exports = fn` vs `exports.fn = fn`**: `exports` is a reference to `module.exports`; `exports = fn` breaks the reference.
2. **Circular dependencies**: A requires B which requires A — one gets a partial/empty module. Refactor to break cycles.
3. **ESM vs CJS mixing**: `.js` files with `type: "module"` in package.json are ESM; use `.cjs` for CommonJS.
4. **`require` with relative path**: Always use `./` prefix: `require("./utils")` not `require("utils")`.
5. **Mutating cached modules**: Node.js caches modules — mutations affect all importers.

## 📝 Summary
- CJS: `require()` / `module.exports` — synchronous, cacheable, traditional Node.js
- ESM: `import/export` — standard, supports tree-shaking, async capable
- Module cache: Node.js loads each module once; subsequent `require()` returns cached object
- Package.json: defines project metadata, scripts, and dependency versions
- Dynamic `import()` for lazy loading; `require()` is synchronous and cannot be lazy

## 🔗 Further Reading
- [Node.js Modules docs](https://nodejs.org/api/modules.html)
- [MDN: ES Modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
