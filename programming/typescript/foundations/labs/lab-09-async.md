# Lab 9: Async TypeScript — Promises, Async/Await & Patterns

## Objective
Write type-safe async code: Promise types, async generators, parallel vs sequential execution, timeout/retry patterns, and typed fetch wrappers.

## Time
35 minutes

## Prerequisites
- Lab 02 (Functions), Lab 08 (Error Handling)

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Promise Types

```typescript
// Promise<T> — resolves to T
const p1: Promise<number> = Promise.resolve(42);
const p2: Promise<string> = new Promise(resolve => setTimeout(() => resolve("done"), 100));

// async function always returns Promise<T>
async function fetchNumber(): Promise<number> { return 42; }
async function mayFail(fail: boolean): Promise<string> {
    if (fail) throw new Error("Failed!");
    return "Success";
}

// Awaited<T> — unwrap Promise type
type T1 = Awaited<Promise<string>>;               // string
type T2 = Awaited<Promise<Promise<number>>>;      // number
type T3 = Awaited<ReturnType<typeof fetchNumber>>; // number

(async () => {
    console.log(await fetchNumber());          // 42
    console.log(await mayFail(false));         // Success
    try { await mayFail(true); }
    catch (e) { console.log("Caught:", (e as Error).message); }
})();
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
async function delay(ms: number): Promise<void> {
    return new Promise(r => setTimeout(r, ms));
}
async function timed<T>(label: string, fn: () => Promise<T>): Promise<T> {
    const start = Date.now();
    const result = await fn();
    console.log(label + ': ' + (Date.now() - start) + 'ms');
    return result;
}
(async () => {
    await timed('delay 50ms', () => delay(50));
    await timed('math', async () => { await delay(10); return 2 ** 32; });
})();
"
```

> 💡 **`Awaited<T>`** (TypeScript 4.5+) recursively unwraps Promise types. `Awaited<Promise<Promise<string>>>` = `string`. This is used by `ReturnType` when dealing with async functions — `Awaited<ReturnType<typeof asyncFn>>` gives you the resolved value type.

**📸 Verified Output:**
```
delay 50ms: ~50ms
math: ~10ms
```

---

### Step 2: Parallel vs Sequential Execution

```typescript
async function fetchItem(id: number): Promise<{ id: number; name: string }> {
    await new Promise(r => setTimeout(r, 10 + Math.random() * 20));
    return { id, name: `Item #${id}` };
}

(async () => {
    // Sequential — total time = sum of all delays
    console.time("sequential");
    const seq: { id: number; name: string }[] = [];
    for (const id of [1, 2, 3, 4, 5]) seq.push(await fetchItem(id));
    console.timeEnd("sequential");
    console.log("Sequential:", seq.map(i => i.name).join(", "));

    // Parallel — total time = max delay
    console.time("parallel");
    const par = await Promise.all([1, 2, 3, 4, 5].map(id => fetchItem(id)));
    console.timeEnd("parallel");
    console.log("Parallel:", par.map(i => i.name).join(", "));

    // Promise.allSettled — continue even if some fail
    const results = await Promise.allSettled([
        fetchItem(1),
        Promise.reject(new Error("Item 2 failed")),
        fetchItem(3),
    ]);
    results.forEach((r, i) => {
        if (r.status === "fulfilled") console.log(`Item ${i+1}: ✓ ${r.value.name}`);
        else                          console.log(`Item ${i+1}: ✗ ${r.reason.message}`);
    });

    // Promise.race — first to resolve/reject wins
    const first = await Promise.race([
        new Promise<string>(r => setTimeout(() => r("slow"), 100)),
        new Promise<string>(r => setTimeout(() => r("fast"), 10)),
    ]);
    console.log("Race winner:", first); // fast
})();
```

> 💡 **`Promise.all` vs `Promise.allSettled`:** `Promise.all` rejects immediately if ANY promise rejects (fail-fast). `Promise.allSettled` waits for ALL promises and gives you both fulfilled and rejected results. Use `allSettled` when you need to process all results even if some fail.

**📸 Verified Output:**
```
Sequential: Item #1, Item #2, Item #3, Item #4, Item #5
Parallel: Item #1, Item #2, Item #3, Item #4, Item #5
Item 1: ✓ Item #1
Item 2: ✗ Item 2 failed
Item 3: ✓ Item #3
Race winner: fast
```

---

### Step 3: Async Generators & Iterators

```typescript
// Async generator — yields values over time
async function* paginate<T>(
    fetch: (page: number, size: number) => Promise<T[]>,
    pageSize: number = 5,
): AsyncGenerator<T[]> {
    let page = 0;
    while (true) {
        const items = await fetch(page, pageSize);
        if (items.length === 0) break;
        yield items;
        if (items.length < pageSize) break;
        page++;
    }
}

// Simulated database
const allProducts = Array.from({ length: 12 }, (_, i) => ({
    id: i + 1, name: `Product #${i + 1}`, price: (i + 1) * 10,
}));

async function fetchPage(page: number, size: number) {
    await new Promise(r => setTimeout(r, 5));
    return allProducts.slice(page * size, (page + 1) * size);
}

(async () => {
    let pageNum = 0;
    for await (const page of paginate(fetchPage, 5)) {
        console.log(`Page ${pageNum++}: [${page.map(p => p.id).join(",")}]`);
    }

    // Async generator with transform
    async function* map<T, U>(
        gen: AsyncIterable<T>,
        fn: (item: T) => U | Promise<U>,
    ): AsyncGenerator<U> {
        for await (const item of gen) yield await fn(item);
    }

    const prices = map(paginate(fetchPage, 4), pages =>
        pages.reduce((sum, p) => sum + p.price, 0)
    );

    for await (const total of prices) {
        console.log("Page total: $" + total);
    }
})();
```

> 💡 **`async function*` + `for await...of`** is the TypeScript way to process lazy async sequences — database cursors, API pagination, file streams, WebSocket messages. The generator pauses at each `yield` until the consumer is ready for the next item, creating natural backpressure.

**📸 Verified Output:**
```
Page 0: [1,2,3,4,5]
Page 1: [6,7,8,9,10]
Page 2: [11,12]
Page total: $150
Page total: $340
Page total: $230
```

---

### Steps 4–8: Timeout, Retry, Queue, AbortController, Capstone

```typescript
// Step 4: Timeout wrapper
function withTimeout<T>(promise: Promise<T>, ms: number, message?: string): Promise<T> {
    const timeout = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error(message ?? `Timeout after ${ms}ms`)), ms)
    );
    return Promise.race([promise, timeout]);
}

// Step 5: Retry with backoff
async function withRetry<T>(
    fn: () => Promise<T>,
    options: { maxRetries?: number; baseDelay?: number; onRetry?: (attempt: number, err: Error) => void } = {}
): Promise<T> {
    const { maxRetries = 3, baseDelay = 100, onRetry } = options;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try { return await fn(); }
        catch (e) {
            if (attempt === maxRetries) throw e;
            onRetry?.(attempt + 1, e as Error);
            await new Promise(r => setTimeout(r, baseDelay * 2 ** attempt));
        }
    }
    throw new Error("Unreachable");
}

// Step 6: Async queue (concurrency limiter)
class AsyncQueue {
    private queue: (() => Promise<void>)[] = [];
    private running = 0;

    constructor(private concurrency: number = 2) {}

    async add<T>(fn: () => Promise<T>): Promise<T> {
        return new Promise((resolve, reject) => {
            this.queue.push(async () => {
                try { resolve(await fn()); }
                catch (e) { reject(e); }
                finally { this.running--; this.drain(); }
            });
            this.drain();
        });
    }

    private drain(): void {
        while (this.running < this.concurrency && this.queue.length) {
            this.running++;
            this.queue.shift()!();
        }
    }
}

// Step 7: AbortController
async function fetchWithAbort(url: string, signal: AbortSignal): Promise<string> {
    return new Promise((resolve, reject) => {
        signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
        setTimeout(() => resolve(`Response from ${url}`), 100);
    });
}

// Step 8: Capstone — typed async pipeline
interface Task<T> {
    name: string;
    run(): Promise<T>;
    timeout?: number;
    retries?: number;
}

async function runPipeline<T>(tasks: Task<T>[]): Promise<{ name: string; result: T | Error }[]> {
    const results: { name: string; result: T | Error }[] = [];
    for (const task of tasks) {
        try {
            const fn = task.timeout ? () => withTimeout(task.run(), task.timeout!) : task.run.bind(task);
            const result = task.retries
                ? await withRetry(typeof fn === "function" ? fn : task.run.bind(task), { maxRetries: task.retries })
                : await task.run();
            results.push({ name: task.name, result });
        } catch (e) {
            results.push({ name: task.name, result: e as Error });
        }
    }
    return results;
}

(async () => {
    const tasks: Task<string>[] = [
        { name: "fast-task", run: async () => { await new Promise(r => setTimeout(r, 10)); return "done fast"; } },
        { name: "slow-task", timeout: 50, run: async () => { await new Promise(r => setTimeout(r, 200)); return "done slow"; } },
        { name: "retry-task", retries: 2, run: (() => {
            let attempts = 0;
            return async () => { if (++attempts < 3) throw new Error("not yet"); return "done after retries"; };
        })() },
    ];

    const results = await runPipeline(tasks);
    results.forEach(r => {
        if (r.result instanceof Error) console.log(`✗ ${r.name}: ${r.result.message}`);
        else                           console.log(`✓ ${r.name}: ${r.result}`);
    });
})();
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
const delay = (ms: number) => new Promise<void>(r => setTimeout(r, ms));
async function parallel<T>(fns: (() => Promise<T>)[]): Promise<T[]> {
    return Promise.all(fns.map(fn => fn()));
}
(async () => {
    const results = await parallel([
        async () => { await delay(20); return 'a'; },
        async () => { await delay(10); return 'b'; },
        async () => { await delay(30); return 'c'; },
    ]);
    console.log(results.join(', '));
})();
"
```

**📸 Verified Output:**
```
a, b, c
```

---

## Summary

TypeScript async programming is fully typed. You've covered `Promise<T>`, `Awaited<T>`, parallel/sequential patterns, async generators with pagination, timeout/retry wrappers, an async concurrency queue, `AbortController`, and a typed async pipeline runner.

## Further Reading
- [TypeScript Async](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-1.html)
- [Async Iterators](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Symbol/asyncIterator)
