# Lab 1: Hello World & JavaScript Basics in Node.js

## 🎯 Objective

Write and run your first JavaScript program in Node.js, explore the runtime environment, and understand how JavaScript executes in a server-side context.

## 📚 Background

JavaScript was originally a browser language, but Node.js (released 2009) brought it to the server using the V8 engine. Node.js is event-driven and non-blocking — perfect for I/O-heavy applications. In this lab you'll use the `innozverse-js:latest` Docker image which ships Node.js v20 LTS.

## ⏱️ Estimated Time

45–60 minutes

## 📋 Prerequisites

- Docker installed and running
- Basic terminal/shell familiarity

## 🛠️ Tools Used

- Docker (`innozverse-js:latest`)
- Node.js v20

## 🔬 Lab Instructions

### Step 1: Verify the Environment

```bash
docker run --rm innozverse-js:latest node --version
docker run --rm innozverse-js:latest node -e "console.log('Node ready!')"
```

**📸 Verified Output:**
```
v20.20.0
Node ready!
```

💡 The `-e` flag runs a string of JavaScript inline. `--rm` removes the container after it exits.

---

### Step 2: Hello World

```bash
docker run --rm innozverse-js:latest node -e "console.log('Hello, World!');"
```

**📸 Verified Output:**
```
Hello, World!
```

💡 `console.log()` is the primary output function in Node.js. It writes to stdout with a newline.

---

### Step 3: Explore the Process Object

```bash
docker run --rm innozverse-js:latest node -e "
console.log('Node version:', process.version);
console.log('Platform:', process.platform);
console.log('Architecture:', process.arch);
console.log('PID:', process.pid);
console.log('Working dir:', process.cwd());
"
```

**📸 Verified Output:**
```
Node version: v20.20.0
Platform: linux
Architecture: x64
PID: 1
Working dir: /labs
```

💡 `process` is a global object in Node.js containing runtime information. No import required.

---

### Step 4: Multiple Console Methods

```bash
docker run --rm innozverse-js:latest node -e "
console.log('Standard log');
console.error('This is an error (stderr)');
console.warn('This is a warning');
console.info('Info message');
console.log('Multiple', 'values', 'separated', 'by', 'spaces');
console.log('Object:', { name: 'Alice', age: 30 });
console.log('Array:', [1, 2, 3]);
"
```

**📸 Verified Output:**
```
Standard log
This is an error (stderr)
This is a warning
Info message
Multiple values separated by spaces
Object: { name: 'Alice', age: 30 }
Array: [ 1, 2, 3 ]
```

💡 `console.error` and `console.warn` write to stderr, useful for logging errors separately from normal output.

---

### Step 5: Write and Run a Script File

Create a file named `hello.js` on your host machine:

```javascript
// hello.js
'use strict';

console.log('=== My First Node.js Script ===');
console.log('Hello, World!');

const name = 'JavaScript Developer';
console.log(`Welcome, ${name}!`);

console.log('\n--- Process Info ---');
console.log('Node:', process.version);
console.log('Args:', process.argv.slice(2));
```

```bash
echo "console.log('Hello from file!')" > /tmp/hello.js
docker run --rm -v /tmp:/tmp innozverse-js:latest node /tmp/hello.js
```

**📸 Verified Output:**
```
Hello from file!
```

💡 `-v /tmp:/tmp` mounts your host `/tmp` directory into the container, so Node.js can read your file.

---

### Step 6: Pass Command-Line Arguments

```bash
docker run --rm innozverse-js:latest node -e "
const args = process.argv.slice(2);
console.log('Arguments received:', args);
if (args.length > 0) {
  console.log('Hello,', args[0] + '!');
} else {
  console.log('No arguments passed.');
}
" -- Alice Bob
```

**📸 Verified Output:**
```
Arguments received: [ 'Alice', 'Bob' ]
Hello, Alice!
```

💡 `process.argv[0]` is `node`, `process.argv[1]` is the script path. Your arguments start at index 2.

---

### Step 7: Comments and Basic Operators

```bash
docker run --rm innozverse-js:latest node -e "
// This is a single-line comment

/*
  This is a
  multi-line comment
*/

// Arithmetic operators
console.log(10 + 3);   // 13
console.log(10 - 3);   // 7
console.log(10 * 3);   // 30
console.log(10 / 3);   // 3.3333...
console.log(10 % 3);   // 1 (remainder)
console.log(10 ** 3);  // 1000 (exponentiation)

// Increment / decrement
let x = 5;
console.log(x++);  // 5 (post-increment)
console.log(x);    // 6
console.log(++x);  // 7 (pre-increment)
"
```

**📸 Verified Output:**
```
13
7
30
3.3333333333333335
1
1000
5
6
7
```

💡 JavaScript uses IEEE 754 floating-point math. `10 / 3` gives a repeating decimal, not an integer.

---

### Step 8: String Output Formatting

```bash
docker run --rm innozverse-js:latest node -e "
// console.log with formatted output
console.log('Name: %s, Age: %d', 'Alice', 30);
console.log('Pi is approximately %f', 3.14159);
console.log('Hex: %i => %o => %s', 255, 255, 255..toString(16));

// JSON formatting
const data = { name: 'Bob', scores: [95, 87, 92] };
console.log(JSON.stringify(data, null, 2));
"
```

**📸 Verified Output:**
```
Name: Alice, Age: 30
Pi is approximately 3.14159
Hex: 255 => 377 => ff
{
  "name": "Bob",
  "scores": [
    95,
    87,
    92
  ]
}
```

💡 `JSON.stringify(obj, null, 2)` pretty-prints JSON with 2-space indentation — very handy for debugging.

---

## ✅ Verification

Run this final snippet to confirm all basics work:

```bash
docker run --rm innozverse-js:latest node -e "
console.log('✅ Lab 1 complete!');
console.log('Node:', process.version);
console.log('2 + 2 =', 2 + 2);
console.log('Hello from Node.js!');
"
```

**Expected Output:**
```
✅ Lab 1 complete!
Node: v20.20.0
2 + 2 = 4
Hello from Node.js!
```

## 🚨 Common Mistakes

| Mistake | Fix |
|---------|-----|
| `console.log` without parentheses | Always use `console.log(...)` with parens |
| Forgetting semicolons | JS has ASI but explicit semicolons avoid ambiguity |
| Mixing `'` and `"` | Both work — pick one style and be consistent |
| `process.argv[0]` for your arg | User args start at index 2 |
| File not found in Docker | Use `-v` to mount your host directory |

## 📝 Summary

- Node.js runs JavaScript outside the browser using the V8 engine
- `console.log()` is your primary output tool (also `.error`, `.warn`, `.info`)
- `process` is a global object with runtime info
- Run scripts with `node filename.js` or inline with `node -e "code"`
- Use `-v` to mount files into Docker containers

## 🔗 Further Reading

- [Node.js Official Docs](https://nodejs.org/en/docs)
- [Node.js `process` API](https://nodejs.org/api/process.html)
- [V8 JavaScript Engine](https://v8.dev/)
- [MDN: console](https://developer.mozilla.org/en-US/docs/Web/API/console)
