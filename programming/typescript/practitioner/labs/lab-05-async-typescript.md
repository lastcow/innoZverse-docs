# Lab 05: Async TypeScript

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Typed Promises, async/await error typing, Promise.all tuples, async generators, AbortController, and typed EventEmitter.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab05 && cd /lab05
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "lib": ["ES2020"]
  }
}
EOF
```

---

## Step 2: Typed Promises

```typescript
// typed-promises.ts
interface User { id: number; name: string; email: string }
interface Post { id: number; title: string; userId: number }

function fetchUser(id: number): Promise<User> {
  return new Promise((resolve, reject) => {
    if (id <= 0) reject(new Error('Invalid ID'));
    setTimeout(() => resolve({ id, name: 'Alice', email: 'alice@example.com' }), 10);
  });
}

function fetchPost(id: number): Promise<Post> {
  return Promise.resolve({ id, title: 'Hello TypeScript', userId: 1 });
}

// Promise chaining with types
fetchUser(1)
  .then(user => {
    console.log('User:', user.name);
    return fetchPost(1);  // TypeScript knows this returns Promise<Post>
  })
  .then(post => console.log('Post:', post.title))
  .catch((err: Error) => console.error(err.message));
```

---

## Step 3: Async/Await with Error Typing

```typescript
// TypeScript doesn't type catch errors — use unknown
async function getUser(id: number): Promise<User | null> {
  try {
    return await fetchUser(id);
  } catch (err: unknown) {
    if (err instanceof Error) console.error(err.message);
    return null;
  }
}

// Result type pattern for better error handling
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function safeGetUser(id: number): Promise<Result<User>> {
  try {
    const user = await fetchUser(id);
    return { ok: true, value: user };
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err : new Error(String(err)) };
  }
}

async function main1() {
  const result = await safeGetUser(1);
  if (result.ok) console.log('Got user:', result.value.name);
  else console.error('Error:', result.error.message);
}

main1();
```

---

## Step 4: Promise.all with Typed Tuples

```typescript
async function main2() {
  // TypeScript infers a tuple type from the array
  const [user, post] = await Promise.all([
    fetchUser(1),
    fetchPost(1),
  ]);
  // user: User, post: Post — correctly typed!
  console.log(user.name, post.title);

  // Promise.allSettled
  const results = await Promise.allSettled([
    fetchUser(1),
    fetchUser(-1),  // will reject
    fetchPost(1),
  ]);

  results.forEach((r, i) => {
    if (r.status === 'fulfilled') console.log(`[${i}] OK:`, JSON.stringify(r.value));
    else console.log(`[${i}] Error:`, r.reason.message);
  });

  // Promise.race with type
  const fastest = await Promise.race([fetchUser(1), fetchUser(2)]);
  console.log('Fastest:', fastest.name);
}

main2();
```

---

## Step 5: Async Generators

```typescript
async function* paginate<T>(
  fetcher: (page: number) => Promise<T[]>,
  totalPages: number
): AsyncGenerator<T[], void, unknown> {
  for (let page = 1; page <= totalPages; page++) {
    const items = await fetcher(page);
    yield items;
  }
}

async function* range(start: number, end: number): AsyncGenerator<number> {
  for (let i = start; i <= end; i++) {
    yield i;
  }
}

async function* take<T>(gen: AsyncGenerator<T>, count: number): AsyncGenerator<T> {
  let taken = 0;
  for await (const item of gen) {
    if (taken++ >= count) return;
    yield item;
  }
}

async function main3() {
  // Collect from async generator
  const nums: number[] = [];
  for await (const n of range(1, 5)) nums.push(n);
  console.log('range:', nums.join(','));  // 1,2,3,4,5

  // Paginated fetch simulation
  const fetchPage = async (page: number): Promise<string[]> =>
    [`item-${page}-1`, `item-${page}-2`];

  for await (const page of paginate(fetchPage, 3)) {
    console.log('Page:', page);
  }
}

main3();
```

---

## Step 6: AbortController with Types

```typescript
async function fetchWithTimeout<T>(
  fn: (signal: AbortSignal) => Promise<T>,
  timeoutMs: number
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fn(controller.signal);
  } finally {
    clearTimeout(timer);
  }
}

async function main4() {
  const result = await fetchWithTimeout(
    async (signal) => {
      // Simulate async operation that respects abort
      return new Promise<string>((resolve, reject) => {
        const t = setTimeout(() => resolve('done'), 50);
        signal.addEventListener('abort', () => {
          clearTimeout(t);
          reject(new Error('Aborted'));
        });
      });
    },
    1000
  );
  console.log('Result:', result);
}

main4();
```

---

## Step 7: Typed EventEmitter

```typescript
type EventMap = {
  data: { payload: string; timestamp: number };
  error: Error;
  end: void;
};

class TypedEmitter<Events extends Record<string, any>> {
  private listeners = new Map<keyof Events, Function[]>();

  on<K extends keyof Events>(event: K, listener: (data: Events[K]) => void): this {
    const list = this.listeners.get(event) ?? [];
    list.push(listener);
    this.listeners.set(event, list);
    return this;
  }

  emit<K extends keyof Events>(event: K, data: Events[K]): this {
    const list = this.listeners.get(event) ?? [];
    list.forEach(l => l(data));
    return this;
  }

  off<K extends keyof Events>(event: K, listener: Function): this {
    const list = (this.listeners.get(event) ?? []).filter(l => l !== listener);
    this.listeners.set(event, list);
    return this;
  }
}

const emitter = new TypedEmitter<EventMap>();
emitter.on('data', ({ payload, timestamp }) => {
  console.log(`Data [${timestamp}]:`, payload);
});
emitter.on('error', (err) => console.error('Error:', err.message));
emitter.emit('data', { payload: 'hello', timestamp: Date.now() });
emitter.emit('error', new Error('something failed'));
```

---

## Step 8: Capstone — Async Pipeline

```typescript
// Save as lab05-capstone.ts
interface User { id: number; name: string; }

async function fetchUser(id: number): Promise<User> {
  return new Promise(resolve => setTimeout(() => resolve({ id, name: 'Alice' }), 10));
}

async function* range(start: number, end: number): AsyncGenerator<number> {
  for (let i = start; i <= end; i++) yield i;
}

async function main() {
  const user = await fetchUser(1);
  console.log('user:', user.name);

  const [a, b] = await Promise.all([fetchUser(1), fetchUser(2)]);
  console.log('users:', a.name, b.name);

  const nums: number[] = [];
  for await (const n of range(1, 5)) nums.push(n);
  console.log('range:', nums.join(','));
}

main();
```

Run:
```bash
ts-node -P tsconfig.json lab05-capstone.ts
```

📸 **Verified Output:**
```
user: Alice
users: Alice Alice
range: 1,2,3,4,5
```

---

## Summary

| Concept | Pattern | Notes |
|---------|---------|-------|
| Typed Promise | `Promise<User>` | Generic type parameter |
| Catch error | `catch(err: unknown)` | Always `unknown`, check instanceof |
| Result type | `{ ok: true; value: T } \| { ok: false; error: E }` | Safer than throwing |
| Promise.all tuple | `const [a, b] = await Promise.all([...])` | Tuple type inferred |
| Async generator | `async function*(): AsyncGenerator<T>` | Lazy async sequences |
| AbortController | `controller.signal` | Timeout/cancel |
| Typed emitter | `on<K extends keyof Events>` | Type-safe events |
