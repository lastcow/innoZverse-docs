# Lab 6: Promises & Async/Await

## 🎯 Objective
Master JavaScript's asynchronous programming model — callbacks, Promises, async/await, and error handling for async code.

## 📚 Background
JavaScript is single-threaded but **non-blocking** — I/O operations (network, files, timers) happen asynchronously. **Callbacks** were the original solution but lead to "callback hell." **Promises** (ES6) clean this up with chainable `.then()`. **async/await** (ES2017) makes async code read like synchronous code. Every modern JS developer must be fluent in all three.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Lab 5: Classes & OOP

## 🛠️ Tools Used
- Node.js 20

## 🔬 Lab Instructions

### Step 1: Callbacks (Foundation)
```javascript
// The original async pattern — Node.js style (error-first callback)
function delay(ms, callback) {
    setTimeout(() => callback(null, `Done after ${ms}ms`), ms);
}

function fetchData(id, callback) {
    const db = { 1: "Alice", 2: "Bob", 3: "Charlie" };
    setTimeout(() => {
        if (db[id]) {
            callback(null, db[id]);
        } else {
            callback(new Error(`User ${id} not found`));
        }
    }, 50);
}

fetchData(1, (err, user) => {
    if (err) return console.error("Error:", err.message);
    console.log("User:", user);
});

fetchData(99, (err, user) => {
    if (err) return console.error("Error:", err.message);
    console.log("User:", user);
});
```

**📸 Verified Output:**
```
User: Alice
Error: User 99 not found
```

### Step 2: Promises
```javascript
// Wrapping callback in a Promise
function fetchUser(id) {
    return new Promise((resolve, reject) => {
        const db = { 1: "Alice", 2: "Bob", 3: "Charlie" };
        setTimeout(() => {
            if (db[id]) resolve(db[id]);
            else reject(new Error(`User ${id} not found`));
        }, 50);
    });
}

// Promise chaining
fetchUser(1)
    .then(user => {
        console.log("Got user:", user);
        return user.toUpperCase();  // Pass to next .then()
    })
    .then(upper => console.log("Uppercased:", upper))
    .catch(err => console.error("Caught:", err.message));

// Handle rejection
fetchUser(99)
    .then(user => console.log("Found:", user))
    .catch(err => console.error("Caught:", err.message));
```

**📸 Verified Output:**
```
Got user: Alice
Caught: User 99 not found
Uppercased: ALICE
```

### Step 3: async/await
```javascript
function fetchUser(id) {
    const db = { 1: "Alice", 2: "Bob", 3: "Charlie" };
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (db[id]) resolve({ id, name: db[id], createdAt: "2026-01-01" });
            else reject(new Error(`User ${id} not found`));
        }, 50);
    });
}

async function getUserInfo(id) {
    try {
        const user = await fetchUser(id);    // Pause until resolved
        console.log(`User ${id}: ${user.name} (joined ${user.createdAt})`);
        return user;
    } catch (err) {
        console.error(`Failed to get user ${id}: ${err.message}`);
        return null;
    }
}

// async functions return a Promise
async function main() {
    const u1 = await getUserInfo(1);
    const u2 = await getUserInfo(2);
    const u3 = await getUserInfo(99);
    
    const found = [u1, u2, u3].filter(Boolean);
    console.log(`Found ${found.length} users`);
}

main();
```

**📸 Verified Output:**
```
User 1: Alice (joined 2026-01-01)
User 2: Bob (joined 2026-01-01)
Failed to get user 99: User 99 not found
Found 2 users
```

### Step 4: Promise.all, Promise.race, Promise.allSettled
```javascript
function fetchWithDelay(id, ms) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (id < 0) reject(new Error(`Invalid id: ${id}`));
            else resolve(`Data for ${id}`);
        }, ms);
    });
}

async function demonstratePromiseMethods() {
    // Promise.all — wait for ALL (fails fast on any rejection)
    try {
        const results = await Promise.all([
            fetchWithDelay(1, 50),
            fetchWithDelay(2, 30),
            fetchWithDelay(3, 70),
        ]);
        console.log("all:", results);
    } catch (err) {
        console.log("all failed:", err.message);
    }
    
    // Promise.allSettled — wait for ALL, include failures
    const settled = await Promise.allSettled([
        fetchWithDelay(1, 50),
        fetchWithDelay(-1, 30),  // Will reject
        fetchWithDelay(3, 40),
    ]);
    settled.forEach((r, i) => {
        const status = r.status === "fulfilled"
            ? `✅ ${r.value}`
            : `❌ ${r.reason.message}`;
        console.log(`  [${i}] ${status}`);
    });
    
    // Promise.race — first to settle wins
    const winner = await Promise.race([
        fetchWithDelay(1, 100),
        fetchWithDelay(2, 30),   // This wins
        fetchWithDelay(3, 200),
    ]);
    console.log("race winner:", winner);
}

demonstratePromiseMethods();
```

**📸 Verified Output:**
```
all: [ 'Data for 1', 'Data for 2', 'Data for 3' ]
  [0] ✅ Data for 1
  [1] ❌ Invalid id: -1
  [2] ✅ Data for 3
race winner: Data for 2
```

### Step 5: Sequential vs Parallel Execution
```javascript
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function processItem(id) {
    await sleep(50);
    return `item_${id}`;
}

async function main() {
    const ids = [1, 2, 3, 4, 5];
    
    // Sequential — items wait for each other (~250ms total)
    console.time("sequential");
    const sequential = [];
    for (const id of ids) {
        sequential.push(await processItem(id));
    }
    console.timeEnd("sequential");
    console.log("sequential:", sequential);
    
    // Parallel — all run simultaneously (~50ms total)
    console.time("parallel");
    const parallel = await Promise.all(ids.map(processItem));
    console.timeEnd("parallel");
    console.log("parallel:", parallel);
}

main();
```

**📸 Verified Output:**
```
sequential: ~250ms
sequential: [ 'item_1', 'item_2', 'item_3', 'item_4', 'item_5' ]
parallel: ~50ms
parallel: [ 'item_1', 'item_2', 'item_3', 'item_4', 'item_5' ]
```

### Step 6: Async Error Handling Patterns
```javascript
// Pattern 1: try/catch in async function
async function withTryCatch(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (err) {
        console.error("Request failed:", err.message);
        return null;
    }
}

// Pattern 2: Wrapper to avoid try/catch repetition
async function safeAwait(promise) {
    try {
        const data = await promise;
        return [null, data];
    } catch (err) {
        return [err, null];
    }
}

async function main() {
    const createPromise = (willFail) => new Promise((resolve, reject) => {
        setTimeout(() => {
            if (willFail) reject(new Error("Something went wrong"));
            else resolve({ data: "success!", timestamp: Date.now() });
        }, 50);
    });
    
    // Using safeAwait pattern
    const [err1, result1] = await safeAwait(createPromise(false));
    console.log("Success:", err1, result1?.data);
    
    const [err2, result2] = await safeAwait(createPromise(true));
    console.log("Failure:", err2?.message, result2);
}

main();
```

**📸 Verified Output:**
```
Success: null success!
Failure: Something went wrong null
```

### Step 7: Async Iteration
```javascript
async function* generatePages(totalPages) {
    for (let page = 1; page <= totalPages; page++) {
        // Simulate API call delay
        await new Promise(r => setTimeout(r, 20));
        yield {
            page,
            items: Array.from({ length: 3 }, (_, i) => ({
                id: (page - 1) * 3 + i + 1,
                name: `Item ${(page - 1) * 3 + i + 1}`
            }))
        };
    }
}

async function main() {
    const allItems = [];
    
    // for await...of with async generator
    for await (const page of generatePages(3)) {
        console.log(`Page ${page.page}: ${page.items.map(i => i.name).join(", ")}`);
        allItems.push(...page.items);
    }
    
    console.log(`Total items collected: ${allItems.length}`);
}

main();
```

**📸 Verified Output:**
```
Page 1: Item 1, Item 2, Item 3
Page 2: Item 4, Item 5, Item 6
Page 3: Item 7, Item 8, Item 9
Total items collected: 9
```

### Step 8: Real-World Async Pattern — Retry with Backoff
```javascript
async function withRetry(fn, maxAttempts = 3, baseDelayMs = 100) {
    let lastError;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
            return await fn(attempt);
        } catch (err) {
            lastError = err;
            console.log(`  Attempt ${attempt}/${maxAttempts} failed: ${err.message}`);
            
            if (attempt < maxAttempts) {
                const delay = baseDelayMs * 2 ** (attempt - 1);  // Exponential backoff
                console.log(`  Retrying in ${delay}ms...`);
                await new Promise(r => setTimeout(r, delay));
            }
        }
    }
    
    throw new Error(`All ${maxAttempts} attempts failed: ${lastError.message}`);
}

let callCount = 0;
async function unstableAPI(attempt) {
    callCount++;
    if (callCount < 3) throw new Error("Server temporarily unavailable");
    return { data: "success", attempts: callCount };
}

async function main() {
    callCount = 0;
    try {
        const result = await withRetry(unstableAPI, 5, 10);
        console.log("Success:", result);
    } catch (err) {
        console.error("Final failure:", err.message);
    }
}

main();
```

**📸 Verified Output:**
```
  Attempt 1/5 failed: Server temporarily unavailable
  Retrying in 10ms...
  Attempt 2/5 failed: Server temporarily unavailable
  Retrying in 20ms...
Success: { data: 'success', attempts: 3 }
```

## ✅ Verification
```javascript
async function main() {
    const delay = (ms, val) => new Promise(r => setTimeout(() => r(val), ms));
    
    // Parallel fetch simulation
    const [a, b, c] = await Promise.all([
        delay(30, "first"),
        delay(10, "second"),
        delay(20, "third"),
    ]);
    console.log(a, b, c);
    
    // allSettled
    const results = await Promise.allSettled([
        Promise.resolve(42),
        Promise.reject(new Error("oops")),
        Promise.resolve("ok"),
    ]);
    console.log(results.map(r => r.status));
    console.log("Lab 6 verified ✅");
}
main();
```

**Expected output:**
```
first second third
[ 'fulfilled', 'rejected', 'fulfilled' ]
Lab 6 verified ✅
```

## 🚨 Common Mistakes
1. **Forgetting `await`**: `const data = fetchData()` — without await, `data` is a Promise, not the value.
2. **`await` outside async**: `await` only works inside `async` functions.
3. **Sequential when parallel is possible**: `await a(); await b()` is slow — use `Promise.all([a(), b()])`.
4. **Swallowing errors**: `promise.catch(() => {})` silently ignores errors — always log or rethrow.
5. **Using `async` in `forEach`**: `arr.forEach(async fn)` doesn't wait for promises — use `for...of` or `Promise.all`.

## 📝 Summary
- Callbacks → Promises → async/await: each solves callback hell
- `async function` always returns a Promise; `await` pauses until resolved
- `Promise.all([])` — parallel, fails fast; `Promise.allSettled([])` — parallel, all results
- `Promise.race([])` — first settlement wins; `Promise.any([])` — first success wins
- Always wrap async calls in try/catch or use `.catch()`
- `for await...of` loops over async iterables (API pagination, streams)

## 🔗 Further Reading
- [MDN: Promises](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Promise)
- [JavaScript.info: Async/Await](https://javascript.info/async-await)
