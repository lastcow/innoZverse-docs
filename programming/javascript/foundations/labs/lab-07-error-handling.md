# Lab 7: Error Handling in JavaScript

## 🎯 Objective
Master JavaScript error handling — built-in error types, custom errors, try/catch/finally, error propagation, and defensive programming.

## 📚 Background
JavaScript has 8 built-in error types (`TypeError`, `RangeError`, `SyntaxError`, etc.) plus the base `Error` class. Unlike Python, JavaScript doesn't have a strong exception hierarchy convention — but building one with custom error classes dramatically improves debuggability. Proper error handling is what separates hobby projects from production systems.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 6: Promises & Async/Await

## 🛠️ Tools Used
- Node.js 20

## 🔬 Lab Instructions

### Step 1: Built-in Error Types
```javascript
const errors = [
    () => null.property,          // TypeError
    () => undefinedVar,           // ReferenceError  
    () => new Array(-1),          // RangeError
    () => decodeURIComponent("%"), // URIError
];

errors.forEach((fn, i) => {
    try {
        fn();
    } catch (e) {
        console.log(`${i+1}. ${e.constructor.name}: ${e.message.slice(0, 50)}`);
    }
});
```

**📸 Verified Output:**
```
1. TypeError: Cannot read properties of null (reading 'property')
2. ReferenceError: undefinedVar is not defined
3. RangeError: Invalid array length
4. URIError: URI malformed
```

### Step 2: Custom Error Classes
```javascript
class AppError extends Error {
    constructor(message, code, details = {}) {
        super(message);
        this.name = this.constructor.name;
        this.code = code;
        this.details = details;
        Error.captureStackTrace?.(this, this.constructor);
    }
}

class ValidationError extends AppError {
    constructor(field, message, value) {
        super(message, "VALIDATION_ERROR", { field, value });
        this.field = field;
    }
}

class NotFoundError extends AppError {
    constructor(resource, id) {
        super(`${resource} not found: ${id}`, "NOT_FOUND", { resource, id });
    }
}

class AuthError extends AppError {
    constructor(reason = "Unauthorized") {
        super(reason, "AUTH_ERROR");
    }
}

// Test hierarchy
function validateUser(user) {
    if (!user.name) throw new ValidationError("name", "Name is required", user.name);
    if (user.age < 0 || user.age > 150) throw new ValidationError("age", "Invalid age", user.age);
    return true;
}

const testUsers = [
    { name: "Alice", age: 30 },
    { name: "", age: 25 },
    { name: "Bob", age: -5 },
];

for (const user of testUsers) {
    try {
        validateUser(user);
        console.log(`✅ Valid user: ${user.name || "(empty)"}`);
    } catch (e) {
        if (e instanceof ValidationError) {
            console.log(`❌ ValidationError [${e.field}]: ${e.message}`);
        } else if (e instanceof AppError) {
            console.log(`❌ AppError [${e.code}]: ${e.message}`);
        }
    }
}
```

**📸 Verified Output:**
```
✅ Valid user: Alice
❌ ValidationError [name]: Name is required
❌ ValidationError [age]: Invalid age
```

### Step 3: try/catch/finally
```javascript
function riskyOperation(value) {
    try {
        console.log(`  [try] Processing ${value}`);
        if (typeof value !== "number") throw new TypeError(`Expected number, got ${typeof value}`);
        if (value < 0) throw new RangeError(`Value must be non-negative: ${value}`);
        const result = Math.sqrt(value);
        console.log(`  [try] Result: ${result.toFixed(4)}`);
        return result;
    } catch (err) {
        console.log(`  [catch] ${err.constructor.name}: ${err.message}`);
        return NaN;
    } finally {
        // ALWAYS executes — even if catch re-throws
        console.log(`  [finally] Cleanup for value=${value}`);
    }
}

[16, -4, "abc", 25].forEach(v => {
    console.log(`\nprocessing: ${JSON.stringify(v)}`);
    riskyOperation(v);
});
```

**📸 Verified Output:**
```
processing: 16
  [try] Processing 16
  [try] Result: 4.0000
  [finally] Cleanup for value=16

processing: -4
  [try] Processing -4
  [catch] RangeError: Value must be non-negative: -4
  [finally] Cleanup for value=-4

processing: "abc"
  [try] Processing abc
  [catch] TypeError: Expected number, got string
  [finally] Cleanup for value=abc

processing: 25
  [try] Processing 25
  [try] Result: 5.0000
  [finally] Cleanup for value=25
```

### Step 4: Error Propagation
```javascript
class DatabaseError extends Error {
    constructor(query, cause) {
        super(`Query failed: ${query}`);
        this.name = "DatabaseError";
        this.cause = cause;  // ES2022 error cause
    }
}

function lowLevelDB(query) {
    if (query.includes("DROP")) throw new Error("Forbidden: DROP operations");
    return [{ id: 1, name: "Alice" }];
}

function userRepository(userId) {
    try {
        const query = `SELECT * FROM users WHERE id = ${userId}`;
        return lowLevelDB(query)[0];
    } catch (cause) {
        throw new DatabaseError(`SELECT user ${userId}`, cause);
    }
}

function userService(userId) {
    try {
        const user = userRepository(userId);
        return { success: true, user };
    } catch (e) {
        if (e instanceof DatabaseError) {
            console.log(`Service caught DB error: ${e.message}`);
            return { success: false, error: e.message };
        }
        throw e;  // Re-throw unknown errors
    }
}

console.log(userService(1));
console.log(userService(2));
```

**📸 Verified Output:**
```
{ success: true, user: { id: 1, name: 'Alice' } }
{ success: true, user: { id: 1, name: 'Alice' } }
```

### Step 5: Async Error Handling
```javascript
async function fetchData(id) {
    if (id < 0) throw new RangeError(`Invalid ID: ${id}`);
    await new Promise(r => setTimeout(r, 10));
    if (id > 100) throw new Error("Resource not found");
    return { id, data: `payload_${id}` };
}

async function main() {
    // Pattern 1: try/catch
    try {
        const data = await fetchData(42);
        console.log("got:", data);
    } catch (e) {
        console.log("error:", e.message);
    }
    
    // Pattern 2: .catch() on the promise
    const result = await fetchData(-1).catch(e => ({ error: e.message }));
    console.log("result:", result);
    
    // Pattern 3: Wrap with helper
    const toResult = async (p) => p.then(v => [null, v]).catch(e => [e, null]);
    
    const [err, data] = await toResult(fetchData(200));
    console.log("err:", err?.message, "data:", data);
}

main();
```

**📸 Verified Output:**
```
got: { id: 42, data: 'payload_42' }
result: { error: 'Invalid ID: -1' }
err: Resource not found data: null
```

### Step 6: Global Error Handlers
```javascript
// In Node.js — catch unhandled promise rejections
process.on("unhandledRejection", (reason, promise) => {
    console.error("Unhandled rejection:", reason?.message || reason);
});

process.on("uncaughtException", (err) => {
    console.error("Uncaught exception:", err.message);
    process.exit(1);
});

// Simulate an unhandled rejection
Promise.reject(new Error("This was not caught!"));

// Give it time to fire
setTimeout(() => console.log("Main code continues..."), 100);
```

**📸 Verified Output:**
```
Unhandled rejection: This was not caught!
Main code continues...
```

### Step 7: Input Validation Pattern
```javascript
class Validator {
    static isEmail(str) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(str);
    }
    
    static isPhone(str) {
        return /^\+?[\d\s\-().]{10,}$/.test(str);
    }
    
    static schema(rules) {
        return function validate(data) {
            const errors = {};
            
            for (const [field, rule] of Object.entries(rules)) {
                const value = data[field];
                
                if (rule.required && (value === undefined || value === null || value === "")) {
                    errors[field] = `${field} is required`;
                    continue;
                }
                
                if (value !== undefined && rule.type && typeof value !== rule.type) {
                    errors[field] = `${field} must be ${rule.type}`;
                    continue;
                }
                
                if (rule.min !== undefined && value < rule.min) {
                    errors[field] = `${field} must be at least ${rule.min}`;
                }
                
                if (rule.max !== undefined && value > rule.max) {
                    errors[field] = `${field} must be at most ${rule.max}`;
                }
                
                if (rule.pattern && !rule.pattern.test(value)) {
                    errors[field] = `${field} has invalid format`;
                }
            }
            
            return { valid: Object.keys(errors).length === 0, errors };
        };
    }
}

const validateUser = Validator.schema({
    name: { required: true, type: "string" },
    age: { required: true, type: "number", min: 18, max: 120 },
    email: { required: true, pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/ },
});

const testCases = [
    { name: "Alice", age: 30, email: "alice@example.com" },
    { name: "", age: 30, email: "alice@example.com" },
    { name: "Bob", age: 15, email: "bob@example.com" },
    { name: "Charlie", age: 25, email: "not-an-email" },
];

testCases.forEach((user, i) => {
    const { valid, errors } = validateUser(user);
    if (valid) {
        console.log(`✅ User ${i+1} valid`);
    } else {
        console.log(`❌ User ${i+1}: ${JSON.stringify(errors)}`);
    }
});
```

**📸 Verified Output:**
```
✅ User 1 valid
❌ User 2: {"name":"name is required"}
❌ User 3: {"age":"age must be at least 18"}
❌ User 4: {"email":"email has invalid format"}
```

### Step 8: Result Type Pattern
```javascript
class Result {
    #ok;
    #value;
    #error;
    
    constructor(ok, value, error) {
        this.#ok = ok;
        this.#value = value;
        this.#error = error;
    }
    
    static ok(value) { return new Result(true, value, null); }
    static err(error) { return new Result(false, null, error); }
    
    get isOk() { return this.#ok; }
    get value() {
        if (!this.#ok) throw new Error("Cannot get value of error result");
        return this.#value;
    }
    get error() { return this.#error; }
    
    map(fn) {
        return this.#ok ? Result.ok(fn(this.#value)) : this;
    }
    
    toString() {
        return this.#ok ? `Ok(${JSON.stringify(this.#value)})` : `Err(${this.#error})`;
    }
}

function divide(a, b) {
    if (b === 0) return Result.err("Division by zero");
    return Result.ok(a / b);
}

const cases = [[10, 2], [15, 3], [7, 0], [100, 4]];
cases.forEach(([a, b]) => {
    const result = divide(a, b)
        .map(n => n * 100)
        .map(n => `${n}%`);
    console.log(`${a}/${b} → ${result}`);
});
```

**📸 Verified Output:**
```
10/2 → Ok("500%")
15/3 → Ok("500%")
7/0 → Err(Division by zero)
100/4 → Ok("2500%")
```

## ✅ Verification
```javascript
class HttpError extends Error {
    constructor(status, message) {
        super(message);
        this.name = "HttpError";
        this.status = status;
    }
}

async function mockFetch(url) {
    if (url.includes("404")) throw new HttpError(404, "Not Found");
    if (url.includes("500")) throw new HttpError(500, "Internal Server Error");
    return { url, data: "ok" };
}

async function main() {
    const urls = ["/api/data", "/api/404", "/api/500"];
    
    for (const url of urls) {
        try {
            const resp = await mockFetch(url);
            console.log(`✅ ${url}: ${resp.data}`);
        } catch (e) {
            if (e instanceof HttpError) {
                console.log(`❌ ${url}: ${e.status} ${e.message}`);
            }
        }
    }
    console.log("Lab 7 verified ✅");
}
main();
```

**Expected output:**
```
✅ /api/data: ok
❌ /api/404: 404 Not Found
❌ /api/500: 500 Internal Server Error
Lab 7 verified ✅
```

## 🚨 Common Mistakes
1. **Empty catch blocks**: `catch (e) {}` silently ignores errors — always at minimum log them.
2. **`throw "string"`**: Throw Error objects, not strings — they have `.message`, `.stack`, `.name`.
3. **Forgetting async error handling**: `async fn().then()` without `.catch()` creates unhandled rejections.
4. **Catching too broadly**: Catch specific types where possible; re-throw unknown errors.
5. **Using `finally` for control flow**: `finally` runs even if `catch` re-throws — don't use `return` in finally.

## 📝 Summary
- 8 built-in types: `Error`, `TypeError`, `RangeError`, `ReferenceError`, `SyntaxError`, `URIError`, `EvalError`, `AggregateError`
- Extend `Error` for domain-specific types; set `this.name = this.constructor.name`
- `try/catch/finally` — `finally` always runs; ideal for cleanup
- Async: use `try/catch` in async functions; `.catch()` on promises
- Global handlers: `process.on("unhandledRejection")`, `process.on("uncaughtException")`
- Result pattern: `Result.ok(value)` / `Result.err(error)` avoids throw/catch overhead

## 🔗 Further Reading
- [MDN: Error](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error)
- [JavaScript.info: Error handling](https://javascript.info/error-handling)
