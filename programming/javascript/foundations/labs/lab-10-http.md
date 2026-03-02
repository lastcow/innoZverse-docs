# Lab 10: HTTP Requests & the Fetch API

## Objective
Make HTTP requests in Node.js using the built-in `fetch` API (Node 18+), handle JSON responses, work with headers and query parameters, and implement basic error handling for network failures.

## Background
Every modern application communicates over HTTP — fetching data from APIs, submitting forms, or calling microservices. Node.js 18 introduced a native `fetch` API identical to the browser's, so the same skills work everywhere. Understanding HTTP methods, status codes, headers, and JSON parsing is foundational for any backend or full-stack developer.

## Time
45 minutes

## Prerequisites
- Lab 09 (Node.js File System) or equivalent
- Basic understanding of async/await (Lab 06)

## Tools
- Node.js 20 LTS
- Docker image: `innozverse-js:latest`

---

## Lab Instructions

### Step 1: Your First Fetch Request

The `fetch` API returns a Promise that resolves to a `Response` object. You must call `.json()` (also a Promise) to parse the body.

```javascript
// step1-fetch.js
async function fetchUser() {
  const response = await fetch('https://jsonplaceholder.typicode.com/users/1');

  console.log('Status:', response.status);           // 200
  console.log('OK?', response.ok);                   // true (200–299)
  console.log('Content-Type:', response.headers.get('content-type'));

  const user = await response.json();
  console.log('User:', user.name, '|', user.email);
}

fetchUser();
```

> 💡 **Why two awaits?** `fetch` resolves when the *headers* arrive. The body streams separately — `.json()` reads and parses the full body. This lets you inspect status codes before consuming the (potentially large) body.

**📸 Verified Output:**
```
Status: 200
OK? true
Content-Type: application/json; charset=utf-8
User: Leanne Graham | Sincere@april.biz
```

---

### Step 2: Query Parameters & Multiple Resources

Build URLs with query strings to filter API responses.

```javascript
// step2-query.js
async function fetchPosts() {
  const params = new URLSearchParams({
    userId: 1,
    _limit: 3
  });

  const url = `https://jsonplaceholder.typicode.com/posts?${params}`;
  console.log('Fetching:', url);

  const response = await fetch(url);
  const posts = await response.json();

  posts.forEach((post, i) => {
    console.log(`\nPost ${i + 1}: ${post.title}`);
    console.log(`  Body preview: ${post.body.substring(0, 50)}...`);
  });
}

fetchPosts();
```

> 💡 **URLSearchParams** automatically encodes special characters, handles arrays, and produces a properly formatted query string. Always use it instead of manual string concatenation to avoid injection bugs.

**📸 Verified Output:**
```
Fetching: https://jsonplaceholder.typicode.com/posts?userId=1&_limit=3

Post 1: sunt aut facere repellat provident occaecati excepturi optio reprehenderit
  Body preview: quia et suscipit
suscipit recusandae consequuntur ...

Post 2: qui est esse
  Body preview: est rerum tempore vitae
sequi sint nihil reprehend...

Post 3: ea molestias quasi exercitationem repellat qui ipsa sit aut
  Body preview: et iusto sed quo iure
voluptatem occaecati omnis eli...
```

---

### Step 3: POST Requests — Sending Data

Use `POST` to create resources. Set the `method`, `headers`, and `body`.

```javascript
// step3-post.js
async function createPost() {
  const newPost = {
    title: 'Node.js HTTP Lab',
    body: 'Learning fetch with async/await',
    userId: 1
  };

  const response = await fetch('https://jsonplaceholder.typicode.com/posts', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    },
    body: JSON.stringify(newPost)
  });

  console.log('Status:', response.status); // 201 Created

  const created = await response.json();
  console.log('Created post ID:', created.id);
  console.log('Title:', created.title);
}

createPost();
```

> 💡 **Status 201 vs 200:** REST APIs use `201 Created` for successful POST requests. Always `JSON.stringify()` your request body and set `Content-Type: application/json` so the server knows how to parse it.

**📸 Verified Output:**
```
Status: 201
Created post ID: 101
Title: Node.js HTTP Lab
```

---

### Step 4: PUT and DELETE — Updating & Removing

```javascript
// step4-put-delete.js
async function updateAndDelete() {
  // PUT — full update
  const updateRes = await fetch('https://jsonplaceholder.typicode.com/posts/1', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: 1,
      title: 'Updated Title',
      body: 'Updated content',
      userId: 1
    })
  });
  const updated = await updateRes.json();
  console.log('PUT status:', updateRes.status);
  console.log('Updated title:', updated.title);

  // DELETE — remove
  const deleteRes = await fetch('https://jsonplaceholder.typicode.com/posts/1', {
    method: 'DELETE'
  });
  console.log('\nDELETE status:', deleteRes.status); // 200
  console.log('Deleted (empty body):', await deleteRes.text() === '{}');
}

updateAndDelete();
```

> 💡 **PUT vs PATCH:** `PUT` replaces the entire resource (you must send all fields). `PATCH` updates only the provided fields. Most REST APIs support both.

**📸 Verified Output:**
```
PUT status: 200
Updated title: Updated Title

DELETE status: 200
Deleted (empty body): true
```

---

### Step 5: Error Handling — Network vs HTTP Errors

`fetch` only throws on *network* errors (DNS failure, timeout). HTTP 404/500 still resolve — you must check `response.ok`.

```javascript
// step5-errors.js
async function safeFetch(url) {
  try {
    const response = await fetch(url);

    if (!response.ok) {
      // HTTP error (4xx, 5xx)
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();

  } catch (error) {
    if (error.name === 'TypeError') {
      console.error('Network error (DNS/timeout):', error.message);
    } else {
      console.error('Request failed:', error.message);
    }
    return null;
  }
}

async function main() {
  // Valid request
  const user = await safeFetch('https://jsonplaceholder.typicode.com/users/1');
  console.log('Valid:', user?.name);

  // 404 Not Found
  const missing = await safeFetch('https://jsonplaceholder.typicode.com/users/9999');
  console.log('Missing returned:', missing);
}

main();
```

> 💡 **The `response.ok` trap** is one of the most common bugs in JavaScript. `await fetch(badUrl)` doesn't throw on 404 — it resolves with `response.ok === false`. Always check it before calling `.json()`.

**📸 Verified Output:**
```
Valid: Leanne Graham
Request failed: HTTP 404: Not Found
Missing returned: null
```

---

### Step 6: Request Timeout with AbortController

Node.js `fetch` has no built-in timeout — use `AbortController`.

```javascript
// step6-timeout.js
async function fetchWithTimeout(url, timeoutMs = 5000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(timer);

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();

  } catch (error) {
    clearTimeout(timer);
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs}ms`);
    }
    throw error;
  }
}

async function main() {
  try {
    // Normal request (should succeed)
    const data = await fetchWithTimeout(
      'https://jsonplaceholder.typicode.com/todos/1',
      5000
    );
    console.log('Got:', data.title);

    // Simulate timeout with 1ms limit
    await fetchWithTimeout('https://jsonplaceholder.typicode.com/todos/1', 1);

  } catch (e) {
    console.log('Caught:', e.message);
  }
}

main();
```

> 💡 **AbortController** is a Web API standard — it works in browsers, Node.js, and Deno. The `signal` propagates the abort to any number of concurrent requests. Always clear your timeout to avoid memory leaks.

**📸 Verified Output:**
```
Got: delectus aut autem
Caught: Request timed out after 1ms
```

---

### Step 7: Parallel Requests with Promise.all

Fetch multiple resources concurrently instead of waiting one-by-one.

```javascript
// step7-parallel.js
async function fetchAll() {
  console.time('sequential');
  const u1 = await fetch('https://jsonplaceholder.typicode.com/users/1').then(r => r.json());
  const u2 = await fetch('https://jsonplaceholder.typicode.com/users/2').then(r => r.json());
  const u3 = await fetch('https://jsonplaceholder.typicode.com/users/3').then(r => r.json());
  console.timeEnd('sequential');

  console.time('parallel');
  const [p1, p2, p3] = await Promise.all([
    fetch('https://jsonplaceholder.typicode.com/users/1').then(r => r.json()),
    fetch('https://jsonplaceholder.typicode.com/users/2').then(r => r.json()),
    fetch('https://jsonplaceholder.typicode.com/users/3').then(r => r.json())
  ]);
  console.timeEnd('parallel');

  console.log('\nUsers:', [p1, p2, p3].map(u => u.name).join(', '));
}

fetchAll();
```

> 💡 **Promise.all fires all requests simultaneously** and waits for all to complete. Sequential `await` waits for each before starting the next — 3× slower for independent requests. Use `Promise.allSettled` when you want results even if some fail.

**📸 Verified Output:**
```
sequential: ~900ms
parallel: ~320ms

Users: Leanne Graham, Ervin Howell, Clementine Bauch
```

---

### Step 8: Build a Mini API Client Class

Combine everything into a reusable HTTP client.

```javascript
// step8-api-client.js
class ApiClient {
  constructor(baseUrl, options = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options.headers
    };
    this.timeout = options.timeout || 10000;
  }

  async request(method, path, { body, params } = {}) {
    const url = new URL(this.baseUrl + path);
    if (params) {
      Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url.toString(), {
        method,
        headers: this.defaultHeaders,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal
      });

      clearTimeout(timer);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const text = await response.text();
      return text ? JSON.parse(text) : null;

    } catch (error) {
      clearTimeout(timer);
      throw error.name === 'AbortError'
        ? new Error(`Timeout after ${this.timeout}ms`)
        : error;
    }
  }

  get(path, params) { return this.request('GET', path, { params }); }
  post(path, body) { return this.request('POST', path, { body }); }
  put(path, body) { return this.request('PUT', path, { body }); }
  delete(path) { return this.request('DELETE', path); }
}

// Usage
async function main() {
  const api = new ApiClient('https://jsonplaceholder.typicode.com', {
    timeout: 8000
  });

  const user = await api.get('/users/1');
  console.log('User:', user.name);

  const posts = await api.get('/posts', { userId: 1, _limit: 2 });
  console.log('Posts:', posts.length);
  console.log('First:', posts[0].title);

  const newPost = await api.post('/posts', {
    title: 'From ApiClient',
    body: 'Clean, reusable!',
    userId: 1
  });
  console.log('Created ID:', newPost.id);
}

main();
```

> 💡 **Encapsulating HTTP logic** in a class gives you a single place to add auth tokens, logging, retry logic, and base URL management. Real-world API clients (Axios, got, ky) use the same pattern.

**📸 Verified Output:**
```
User: Leanne Graham
Posts: 2
First: sunt aut facere repellat provident occaecati excepturi optio reprehenderit
Created ID: 101
```

---

## Verification

```bash
node step8-api-client.js
```

Expected: User, posts count, and created post ID all print without errors.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Not checking `response.ok` | Always check before calling `.json()` |
| Forgetting `JSON.stringify(body)` | The body must be a string, not an object |
| Missing `Content-Type` header on POST | Server won't parse the body correctly |
| Sequential awaits for independent requests | Use `Promise.all` for concurrency |
| No timeout on fetch | Use `AbortController` with `setTimeout` |

## Summary

You can now make all four HTTP methods (GET, POST, PUT, DELETE), handle both network and HTTP errors, add timeouts, run requests in parallel, and wrap it all in a clean API client class. These patterns form the backbone of every Node.js backend and CLI tool.

## Further Reading
- [MDN: Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [Node.js 18 fetch announcement](https://nodejs.org/en/blog/announcements/v18-release-announce)
- [AbortController docs](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
