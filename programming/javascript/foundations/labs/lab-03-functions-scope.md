# Lab 3: Functions, Scope & Closures

## 🎯 Objective
Master JavaScript functions — declarations, expressions, arrow functions, default parameters, closures, and the `this` keyword.

## 📚 Background
JavaScript has **first-class functions** — functions are objects and can be stored in variables, passed as arguments, and returned from other functions. This enables powerful patterns like callbacks, higher-order functions, and closures. JavaScript also has **lexical scoping** — a function sees the variables from where it was *defined*, not where it was *called*. Understanding closures and `this` is what separates intermediate from advanced JS developers.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 2: Variables, Data Types & Type Coercion

## 🛠️ Tools Used
- Node.js 20

## 🔬 Lab Instructions

### Step 1: Function Declaration vs Expression

```javascript
// Function declaration — hoisted (can be called before definition)
console.log(add(3, 4));  // Works! Declaration is hoisted.

function add(a, b) {
    return a + b;
}

// Function expression — NOT hoisted
// console.log(multiply(3, 4));  // ReferenceError: Cannot access before init

const multiply = function(a, b) {
    return a * b;
};

console.log(add(5, 6));        // 11
console.log(multiply(5, 6));   // 30

// Named function expression — name only visible inside the function
const factorial = function fact(n) {
    return n <= 1 ? 1 : n * fact(n - 1);  // fact() accessible inside
};
console.log(factorial(5));  // 120
```

**📸 Verified Output:**
```
7
11
30
120
```

> 💡 **Hoisting** moves function declarations to the top of their scope before execution. Function expressions and arrow functions are NOT hoisted — this is one reason to prefer consistent placement of all functions.

### Step 2: Arrow Functions

```javascript
// Traditional function
const square_old = function(x) { return x * x; };

// Arrow function — shorter syntax
const square = (x) => x * x;         // Implicit return
const cube = x => x ** 3;            // No parens for single param
const add = (a, b) => a + b;         // Multiple params need parens
const greet = name => `Hello, ${name}!`;

// Multi-line arrow function needs explicit return
const clamp = (val, min, max) => {
    const clamped = Math.max(min, Math.min(max, val));
    return clamped;
};

console.log(square(5));         // 25
console.log(cube(3));           // 27
console.log(add(10, 20));       // 30
console.log(greet("World"));    // Hello, World!
console.log(clamp(150, 0, 100)); // 100

// Arrow functions with arrays
const numbers = [1, 2, 3, 4, 5];
const squared = numbers.map(n => n ** 2);
const evens = numbers.filter(n => n % 2 === 0);
const sum = numbers.reduce((acc, n) => acc + n, 0);

console.log("squared:", squared);
console.log("evens:", evens);
console.log("sum:", sum);
```

**📸 Verified Output:**
```
25
27
30
Hello, World!
100
squared: [ 1, 4, 9, 16, 25 ]
evens: [ 2, 4 ]
sum: 15
```

### Step 3: Default Parameters and Rest/Spread

```javascript
// Default parameters
function createUser(name, role = "user", active = true) {
    return { name, role, active };  // Shorthand property names
}

console.log(createUser("Alice"));
console.log(createUser("Bob", "admin"));
console.log(createUser("Charlie", "moderator", false));

// Rest parameters (...args) — collect remaining args into array
function sum(...numbers) {
    return numbers.reduce((total, n) => total + n, 0);
}

console.log(sum(1, 2));              // 3
console.log(sum(1, 2, 3, 4, 5));    // 15
console.log(sum());                  // 0

// Spread operator — expand array into arguments
const nums = [3, 1, 4, 1, 5, 9, 2, 6];
console.log("max:", Math.max(...nums));  // 9
console.log("min:", Math.min(...nums));  // 1

// Spread to copy/merge arrays and objects
const original = [1, 2, 3];
const copy = [...original, 4, 5];  // Copy + extend
console.log("copy:", copy);

const defaults = { color: "blue", size: "medium" };
const custom = { ...defaults, color: "red", weight: "heavy" };
console.log("merged:", custom);
```

**📸 Verified Output:**
```
{ name: 'Alice', role: 'user', active: true }
{ name: 'Bob', role: 'admin', active: true }
{ name: 'Charlie', role: 'moderator', active: false }
3
15
0
max: 9
min: 1
copy: [ 1, 2, 3, 4, 5 ]
merged: { color: 'red', size: 'medium', weight: 'heavy' }
```

### Step 4: Closures

```javascript
// A closure = inner function + its outer scope variables
function makeCounter(initial = 0) {
    let count = initial;  // This variable is "closed over"
    
    return {
        increment() { return ++count; },
        decrement() { return --count; },
        reset() { count = initial; return count; },
        value() { return count; }
    };
}

const counter = makeCounter(10);
console.log(counter.value());      // 10
console.log(counter.increment());  // 11
console.log(counter.increment());  // 12
console.log(counter.decrement());  // 11
console.log(counter.reset());      // 10

// Closure for data privacy
function createBankAccount(owner, initialBalance) {
    let balance = initialBalance;  // Private — no external access
    const transactions = [];
    
    return {
        deposit(amount) {
            balance += amount;
            transactions.push({ type: "deposit", amount, balance });
            return this;
        },
        withdraw(amount) {
            if (amount > balance) throw new Error("Insufficient funds");
            balance -= amount;
            transactions.push({ type: "withdrawal", amount, balance });
            return this;
        },
        getBalance() { return balance; },
        getHistory() { return [...transactions]; }  // Return a copy
    };
}

const account = createBankAccount("Alice", 1000);
account.deposit(500).deposit(200).withdraw(300);
console.log(`Balance: $${account.getBalance()}`);
console.log("History:", account.getHistory());
```

**📸 Verified Output:**
```
10
11
12
11
10
Balance: $1400
History: [
  { type: 'deposit', amount: 500, balance: 1500 },
  { type: 'deposit', amount: 200, balance: 1700 },
  { type: 'withdrawal', amount: 300, balance: 1400 }
]
```

### Step 5: Higher-Order Functions

```javascript
// Functions that take other functions as arguments
function applyTwice(fn, value) {
    return fn(fn(value));
}

const double = x => x * 2;
const addTen = x => x + 10;
console.log(applyTwice(double, 3));   // 12: double(double(3)) = double(6) = 12
console.log(applyTwice(addTen, 5));   // 25: addTen(addTen(5)) = addTen(15) = 25

// Functions that return functions (currying)
function multiply(factor) {
    return (number) => number * factor;
}

const double2 = multiply(2);
const triple = multiply(3);
const tenTimes = multiply(10);

const numbers = [1, 2, 3, 4, 5];
console.log(numbers.map(double2));   // [2, 4, 6, 8, 10]
console.log(numbers.map(triple));    // [3, 6, 9, 12, 15]
console.log(numbers.map(tenTimes));  // [10, 20, 30, 40, 50]

// Pipeline pattern
const pipeline = (...fns) => value => fns.reduce((v, f) => f(v), value);

const transform = pipeline(
    x => x * 2,
    x => x + 10,
    x => x.toString(),
    s => `Result: ${s}`
);

console.log(transform(5));  // Result: 20
```

**📸 Verified Output:**
```
12
25
[ 2, 4, 6, 8, 10 ]
[ 3, 6, 9, 12, 15 ]
[ 10, 20, 30, 40, 50 ]
Result: 20
```

### Step 6: Scope — var vs let Hoisting

```javascript
// var is function-scoped and hoisted
function demoVar() {
    console.log(x);  // undefined (hoisted, not initialized)
    var x = 10;
    console.log(x);  // 10
    
    if (true) {
        var x = 999;  // Same x! var ignores block scope
    }
    console.log(x);  // 999 — modified by inner block!
}

// let/const are block-scoped
function demoLet() {
    // console.log(y);  // ReferenceError: Cannot access before initialization
    let y = 10;
    console.log(y);  // 10
    
    if (true) {
        let y = 999;  // Different y — block scope
        console.log("inner y:", y);  // 999
    }
    console.log("outer y:", y);  // 10 — unchanged!
}

demoVar();
console.log("---");
demoLet();
```

**📸 Verified Output:**
```
undefined
10
999
---
10
inner y: 999
outer y: 10
```

### Step 7: IIFE and Module Pattern

```javascript
// IIFE — Immediately Invoked Function Expression
// Used to create a private scope (pre-ES6 modules)
const result = (function() {
    const private_value = 42;
    function helper(x) { return x * 2; }
    return helper(private_value);
})();

console.log("IIFE result:", result);  // 84

// Module pattern using closure
const MathModule = (() => {
    // Private
    const _precision = 6;
    
    function _round(n) {
        return parseFloat(n.toFixed(_precision));
    }
    
    // Public API
    return {
        sqrt: n => _round(Math.sqrt(n)),
        log:  n => _round(Math.log(n)),
        sin:  n => _round(Math.sin(n)),
        PI: Math.PI
    };
})();

console.log("sqrt(2):", MathModule.sqrt(2));
console.log("log(e):", MathModule.log(Math.E));
console.log("sin(π/2):", MathModule.sin(Math.PI / 2));
```

**📸 Verified Output:**
```
IIFE result: 84
sqrt(2): 1.414214
log(e): 1
sin(π/2): 1
```

### Step 8: Memoization with Closures

```javascript
// Memoization: cache function results for repeated calls
function memoize(fn) {
    const cache = new Map();
    
    return function(...args) {
        const key = JSON.stringify(args);
        if (cache.has(key)) {
            return cache.get(key);
        }
        const result = fn.apply(this, args);
        cache.set(key, result);
        return result;
    };
}

// Slow Fibonacci without memoization
let calls = 0;
function fib(n) {
    calls++;
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

calls = 0;
console.log("fib(30):", fib(30), `(${calls} calls)`);

// With memoization
calls = 0;
const fastFib = memoize(function(n) {
    calls++;
    if (n <= 1) return n;
    return fastFib(n - 1) + fastFib(n - 2);
});

console.log("fastFib(30):", fastFib(30), `(${calls} calls)`);
console.log("fastFib(30) again:", fastFib(30), `(${calls} calls — cached!)`);
```

**📸 Verified Output:**
```
fib(30): 832040 (2692537 calls)
fastFib(30): 832040 (31 calls)
fastFib(30) again: 832040 (31 calls — cached!)
```

## ✅ Verification

```javascript
// Closure + higher-order function challenge
function makeMultiplier(factor) {
    return (n) => n * factor;
}

const ops = [2, 3, 5, 10].map(makeMultiplier);
const values = [1, 2, 3, 4, 5];

ops.forEach((op, i) => {
    const results = values.map(op);
    console.log(`×${[2,3,5,10][i]}: ${results}`);
});

const compose = (f, g) => x => f(g(x));
const addOneAndDouble = compose(x => x * 2, x => x + 1);
console.log([1,2,3].map(addOneAndDouble));
console.log("Lab 3 verified ✅");
```

**Expected output:**
```
×2: 2,4,6,8,10
×3: 3,6,9,12,15
×5: 5,10,15,20,25
×10: 10,20,30,40,50
[ 4, 6, 8 ]
Lab 3 verified ✅
```

## 🚨 Common Mistakes

1. **Arrow functions and `this`**: Arrow functions don't have their own `this` — they inherit from the surrounding scope.
2. **`var` in loops**: `for (var i = 0; i < 5; i++) setTimeout(() => console.log(i))` prints `5` five times — use `let`.
3. **Forgetting `return` in multi-line arrow functions**: `const f = x => { x * 2 }` returns `undefined`; need `return`.
4. **Closures in loops**: Classic bug — all closures capture the same variable; use `let` or IIFE.
5. **`arguments` object**: Arrow functions don't have `arguments` — use rest params `...args` instead.

## 📝 Summary

- `function` declarations are hoisted; expressions/arrows are not
- Arrow functions: `(params) => expression` for concise functions
- Default params: `function f(x, y = 10)` — evaluated at call time
- Rest `...args` collects extras into array; spread `...arr` expands into arguments
- Closure: inner function captures outer scope variables (private state pattern)
- Higher-order functions: take/return functions — enables map, filter, reduce, memoize

## 🔗 Further Reading
- [MDN: Functions](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Functions)
- [MDN: Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Closures)
- [JavaScript.info: Closures](https://javascript.info/closure)
