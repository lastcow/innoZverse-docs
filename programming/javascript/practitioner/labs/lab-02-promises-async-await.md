# Lab 02: Promises & Async/Await

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master asynchronous JavaScript: Promise creation, chaining, combinators (all/race/allSettled/any), and the cleaner async/await syntax with proper error handling.

---

## Step 1: Creating Promises

```javascript
// Basic Promise
const success = new Promise((resolve, reject) => {
  setTimeout(() => resolve('Data fetched!'), 100);
});

const failure = new Promise((resolve, reject) => {
  setTimeout(() => reject(new Error('Network error')), 100);
});

// Promise.resolve / Promise.reject shortcuts
const immediate = Promise.resolve(42);
const failed = Promise.reject(new Error('Instant failure'));

immediate.then(v => console.log('Value:', v)); // Value: 42
failed.catch(e => console.log('Error:', e.message)); // Error: Instant failure
```

> 💡 A Promise represents a value that may be available now, in the future, or never.

---

## Step 2: Promise Chaining

```javascript
function fetchUser(id) {
  return new Promise(resolve => {
    setTimeout(() => resolve({ id, name: `User ${id}`, roleId: 'admin' }), 50);
  });
}

function fetchPermissions(roleId) {
  return new Promise(resolve => {
    setTimeout(() => resolve(['read', 'write', 'delete']), 50);
  });
}

fetchUser(1)
  .then(user => {
    console.log('Got user:', user.name);
    return fetchPermissions(user.roleId); // Return new promise
  })
  .then(permissions => {
    console.log('Permissions:', permissions);
    return permissions.length;
  })
  .then(count => console.log('Total permissions:', count))
  .catch(err => console.error('Error:', err.message))
  .finally(() => console.log('Request complete'));
```

> 💡 `.finally()` runs regardless of success or failure — perfect for cleanup.

---

## Step 3: Promise.all — Parallel Execution

```javascript
function delay(ms, value) {
  return new Promise(resolve => setTimeout(() => resolve(value), ms));
}

// All resolve — runs in parallel
async function demo() {
  console.time('parallel');
  const [a, b, c] = await Promise.all([
    delay(100, 'first'),
    delay(150, 'second'),
    delay(80, 'third')
  ]);
  console.timeEnd('parallel'); // ~150ms, not 330ms
  console.log(a, b, c);

  // If any rejects, Promise.all rejects
  try {
    await Promise.all([
      Promise.resolve('ok'),
      Promise.reject(new Error('one failed')),
      Promise.resolve('also ok')
    ]);
  } catch (e) {
    console.log('Promise.all failed:', e.message);
  }
}
demo();
```

---

## Step 4: Promise.allSettled, race, any

```javascript
const promises = [
  Promise.resolve('success 1'),
  Promise.reject(new Error('failure')),
  Promise.resolve('success 2')
];

// allSettled — waits for all, never rejects
Promise.allSettled(promises).then(results => {
  results.forEach(r => {
    if (r.status === 'fulfilled') console.log('✓', r.value);
    else console.log('✗', r.reason.message);
  });
});

// race — first to settle wins
const fast = delay => new Promise(res => setTimeout(() => res(`done in ${delay}ms`), delay));
Promise.race([fast(200), fast(50), fast(100)])
  .then(winner => console.log('Winner:', winner));

// any — first to RESOLVE wins (ignores rejections)
Promise.any([
  Promise.reject(new Error('fail 1')),
  Promise.resolve('first success'),
  Promise.resolve('second success')
]).then(v => console.log('First success:', v));
```

---

## Step 5: Async/Await Syntax

```javascript
// async function always returns a Promise
async function greet(name) {
  return `Hello, ${name}!`; // Equivalent to Promise.resolve(...)
}

greet('World').then(console.log); // Hello, World!

// await pauses execution inside async function
async function getUserData(userId) {
  const user = await fetchUser(userId);
  const permissions = await fetchPermissions(user.roleId);
  return { ...user, permissions };
}

// Async IIFE pattern
(async () => {
  const data = await getUserData(1);
  console.log(data);
})();

// Top-level await (in ES modules)
// const data = await getUserData(1); // Valid in .mjs files
```

> 💡 `async/await` is syntactic sugar over Promises. Under the hood it's still Promises.

---

## Step 6: Error Handling with Async/Await

```javascript
// try/catch with async/await
async function safeFetch(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Fetch failed:', error.message);
    return null;
  }
}

// Utility: wrap async to return [error, result]
async function to(promise) {
  try {
    const result = await promise;
    return [null, result];
  } catch (error) {
    return [error, null];
  }
}

async function main() {
  const [err, user] = await to(fetchUser(1));
  if (err) {
    console.error('Failed:', err.message);
    return;
  }
  console.log('User:', user.name);
}
main();
```

---

## Step 7: Sequential vs Parallel Async

```javascript
function fetchItem(id) {
  return new Promise(resolve =>
    setTimeout(() => resolve({ id, data: `item-${id}` }), 100)
  );
}

// WRONG: Sequential (slow) — 500ms total
async function sequentialFetch(ids) {
  const results = [];
  for (const id of ids) {
    const item = await fetchItem(id); // Waits for each one
    results.push(item);
  }
  return results;
}

// CORRECT: Parallel (fast) — ~100ms total
async function parallelFetch(ids) {
  return Promise.all(ids.map(id => fetchItem(id)));
}

// Controlled concurrency
async function batchFetch(ids, batchSize = 2) {
  const results = [];
  for (let i = 0; i < ids.length; i += batchSize) {
    const batch = ids.slice(i, i + batchSize);
    const batchResults = await Promise.all(batch.map(fetchItem));
    results.push(...batchResults);
  }
  return results;
}

(async () => {
  const ids = [1, 2, 3, 4, 5];
  
  console.time('sequential');
  await sequentialFetch(ids);
  console.timeEnd('sequential'); // ~500ms

  console.time('parallel');
  await parallelFetch(ids);
  console.timeEnd('parallel'); // ~100ms

  console.time('batched');
  const items = await batchFetch(ids, 2);
  console.timeEnd('batched'); // ~300ms
  console.log('Items:', items.map(i => i.id));
})();
```

---

## Step 8: Capstone — Async Data Pipeline

```javascript
// Simulated async data pipeline
const delay = (ms) => new Promise(r => setTimeout(r, ms));

async function fetchUsers() {
  await delay(50);
  return [
    { id: 1, name: 'Alice', active: true },
    { id: 2, name: 'Bob', active: false },
    { id: 3, name: 'Charlie', active: true }
  ];
}

async function fetchUserScore(userId) {
  await delay(30);
  const scores = { 1: 95, 2: 72, 3: 88 };
  if (!scores[userId]) throw new Error(`No score for user ${userId}`);
  return scores[userId];
}

async function processUsers() {
  const users = await fetchUsers();
  const activeUsers = users.filter(u => u.active);

  const usersWithScores = await Promise.allSettled(
    activeUsers.map(async user => {
      const score = await fetchUserScore(user.id);
      return { ...user, score };
    })
  );

  return usersWithScores
    .filter(r => r.status === 'fulfilled')
    .map(r => r.value)
    .sort((a, b) => b.score - a.score);
}

processUsers().then(results => {
  console.log('Top performers:');
  results.forEach(u => console.log(`  ${u.name}: ${u.score}`));
});
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
const p1 = Promise.resolve(1);
const p2 = new Promise((res) => setTimeout(() => res(2), 10));
const p3 = Promise.reject(new Error(\"fail\"));
Promise.allSettled([p1, p2, p3]).then(results => {
  results.forEach(r => console.log(r.status, r.value ?? r.reason?.message));
});
async function fetchData() {
  const results = await Promise.all([Promise.resolve(\"data1\"), Promise.resolve(\"data2\")]);
  return results;
}
fetchData().then(d => console.log(d));
'"
```

📸 **Verified Output:**
```
[ 'data1', 'data2' ]
fulfilled 1
fulfilled 2
rejected fail
```

---

## Summary

| API | Behavior | Use When |
|-----|----------|----------|
| `Promise.resolve(v)` | Wraps value in resolved promise | Creating instant promises |
| `Promise.all(arr)` | Resolves when ALL resolve; rejects on first failure | All-or-nothing parallel tasks |
| `Promise.allSettled(arr)` | Waits for all, reports each result | Need all results regardless |
| `Promise.race(arr)` | First to settle (resolve or reject) wins | Timeouts, fastest service |
| `Promise.any(arr)` | First to RESOLVE wins; rejects if all fail | Fallback sources |
| `async/await` | Sync-looking async code | Readability, sequential deps |
| `try/catch` with await | Catch async errors | Error handling in async code |
