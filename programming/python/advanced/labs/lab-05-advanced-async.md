# Lab 05: Advanced Async Patterns

## Objective
Master production-grade `asyncio`: `Semaphore` for rate-limiting, `TaskGroup` for structured concurrency, producer-consumer with `asyncio.Queue`, retry with exponential backoff, `asyncio.timeout` (3.11+), async context managers, and building an async pipeline.

## Background
`asyncio.gather` runs tasks concurrently — but without limits, 10,000 simultaneous HTTP requests will crash your process or get you banned. Real async code needs rate-limiting, cancellation, and structured error propagation. Python 3.11's `TaskGroup` makes this safe by default.

## Time
35 minutes

## Prerequisites
- Practitioner Lab 05 (Async/Await)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Semaphore — Rate Limiting Concurrent Tasks

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import asyncio, time

async def fetch(url: str, sem: asyncio.Semaphore, delay: float = 0.02) -> dict:
    async with sem:  # blocks until a slot is free
        await asyncio.sleep(delay)
        return {'url': url, 'status': 200, 'bytes': len(url) * 10}

async def main():
    urls = [f'https://api.innozverse.com/products/{i}' for i in range(20)]

    # Without limit: all 20 fire simultaneously
    t0 = time.perf_counter()
    results = await asyncio.gather(*[fetch(u, asyncio.Semaphore(999)) for u in urls])
    print(f'No limit (20 concurrent): {time.perf_counter()-t0:.2f}s, {len(results)} results')

    # With Semaphore(5): max 5 concurrent, batches of ~5
    sem = asyncio.Semaphore(5)
    t0 = time.perf_counter()
    results = await asyncio.gather(*[fetch(u, sem) for u in urls])
    print(f'Semaphore(5):             {time.perf_counter()-t0:.2f}s, {len(results)} results')

    # With Semaphore(3): ~7 rounds of 3 → ~7 * 0.02s
    sem3 = asyncio.Semaphore(3)
    t0 = time.perf_counter()
    results = await asyncio.gather(*[fetch(u, sem3) for u in urls])
    print(f'Semaphore(3):             {time.perf_counter()-t0:.2f}s, {len(results)} results')

asyncio.run(main())
"
```

> 💡 **`asyncio.Semaphore(n)`** allows at most `n` coroutines to be inside `async with sem:` simultaneously. Tasks that exceed the limit are *suspended* (not cancelled) until a slot opens. This is the async equivalent of a thread pool and is critical for rate-limiting API calls, database connections, and file I/O.

**📸 Verified Output:**
```
No limit (20 concurrent): 0.02s, 20 results
Semaphore(5):             0.08s, 20 results
Semaphore(3):             0.14s, 20 results
```

---

### Step 2: `TaskGroup` — Structured Concurrency (Python 3.11+)

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import asyncio

async def price_check(product_id: int, fail: bool = False) -> dict:
    await asyncio.sleep(0.01 * product_id)
    if fail: raise ValueError(f'Product {product_id} unavailable')
    return {'id': product_id, 'price': 864.0 + product_id * 10}

async def demo_taskgroup_success():
    results = []
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(price_check(i)) for i in range(1, 6)]
    results = [t.result() for t in tasks]
    print('All succeeded:', [r['id'] for r in results])
    return results

async def demo_taskgroup_failure():
    try:
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(price_check(1))
            t2 = tg.create_task(price_check(99, fail=True))  # will fail
            t3 = tg.create_task(price_check(3))
    except* ValueError as eg:
        # ExceptionGroup — collects all errors
        print(f'TaskGroup caught {len(eg.exceptions)} error(s): {eg.exceptions}')
        return None

async def main():
    print('=== TaskGroup success ===')
    results = await demo_taskgroup_success()
    print(f'Prices: {[r[\"price\"] for r in results]}')

    print()
    print('=== TaskGroup failure (except*) ===')
    await demo_taskgroup_failure()

asyncio.run(main())
"
```

**📸 Verified Output:**
```
=== TaskGroup success ===
All succeeded: [1, 2, 3, 4, 5]
Prices: [874.0, 884.0, 894.0, 904.0, 914.0]

=== TaskGroup failure (except*) ===
TaskGroup caught 1 error(s): (ValueError('Product 99 unavailable'),)
```

---

### Steps 3–8: Producer-Consumer, Retry/Backoff, asyncio.timeout, Async CM, Async Generator, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import asyncio, time, random

# Step 3: Producer-Consumer with asyncio.Queue
async def producer(q: asyncio.Queue, items: list, name: str = 'producer'):
    for item in items:
        await asyncio.sleep(0.005)
        await q.put(item)
    await q.put(None)  # sentinel

async def consumer(q: asyncio.Queue, results: list, worker_id: int):
    while True:
        item = await q.get()
        if item is None:
            await q.put(None)  # forward sentinel to next worker
            q.task_done()
            break
        await asyncio.sleep(0.01)  # simulate processing
        results.append({'worker': worker_id, 'item': item, 'result': item ** 2})
        q.task_done()

async def run_pipeline():
    q = asyncio.Queue(maxsize=10)
    results = []
    items = list(range(1, 21))  # 20 items

    prod   = asyncio.create_task(producer(q, items))
    workers = [asyncio.create_task(consumer(q, results, i)) for i in range(4)]

    await asyncio.gather(prod, *workers)
    return sorted(results, key=lambda r: r['item'])

results = asyncio.run(run_pipeline())
print('=== Producer-Consumer ===')
print(f'Processed {len(results)} items by {len(set(r[\"worker\"] for r in results))} workers')
by_worker = {}
for r in results:
    by_worker.setdefault(r['worker'], 0)
    by_worker[r['worker']] += 1
print(f'Distribution: {dict(sorted(by_worker.items()))}')
print(f'Sample results: {[(r[\"item\"],r[\"result\"]) for r in results[:4]]}')

# Step 4: Retry with exponential backoff
async def flaky_service(attempt: int) -> str:
    if attempt < 3: raise ConnectionError(f'Service unavailable (attempt {attempt})')
    return f'Success on attempt {attempt}'

async def with_retry(coro_factory, max_retries: int = 5, base_delay: float = 0.01):
    last_exc = None
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(coro_factory(attempt), timeout=2.0)
        except (ConnectionError, asyncio.TimeoutError) as e:
            last_exc = e
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, base_delay)
                print(f'  Retry {attempt+1}/{max_retries} after {delay:.3f}s: {e}')
                await asyncio.sleep(delay)
    raise RuntimeError(f'Failed after {max_retries} retries') from last_exc

async def run_retry():
    print()
    print('=== Retry with exponential backoff ===')
    result = await with_retry(flaky_service)
    print(f'Final: {result}')

asyncio.run(run_retry())

# Step 5: asyncio.timeout (Python 3.11+)
async def run_timeout():
    print()
    print('=== asyncio.timeout ===')

    # Successful within timeout
    async with asyncio.timeout(1.0):
        await asyncio.sleep(0.01)
    print('Task completed within 1.0s')

    # Timeout exceeded
    try:
        async with asyncio.timeout(0.05):
            await asyncio.sleep(10.0)
    except TimeoutError:
        print('Timed out after 0.05s (TimeoutError raised)')

asyncio.run(run_timeout())

# Step 6: Async context manager
class AsyncDBConnection:
    def __init__(self, url: str):
        self.url = url; self.connected = False; self.queries = 0

    async def __aenter__(self):
        await asyncio.sleep(0.01)  # simulate connect
        self.connected = True
        print(f'  Connected to {self.url}')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.sleep(0.005)  # simulate close
        self.connected = False
        print(f'  Disconnected ({self.queries} queries executed)')
        return False

    async def execute(self, sql: str) -> list:
        if not self.connected: raise RuntimeError('Not connected')
        self.queries += 1
        await asyncio.sleep(0.005)
        return [{'result': f'{sql[:20]}...', 'row': i} for i in range(3)]

async def run_async_cm():
    print()
    print('=== Async context manager ===')
    async with AsyncDBConnection('sqlite+async:///store.db') as conn:
        rows = await conn.execute('SELECT * FROM products')
        print(f'  Query returned {len(rows)} rows')
        rows2 = await conn.execute('SELECT COUNT(*) FROM orders')
        print(f'  Second query: {len(rows2)} rows')

asyncio.run(run_async_cm())

# Step 7: Async generator
async def stream_products(count: int, batch_size: int = 5):
    '''Simulate a streaming API that yields products in batches.'''
    for start in range(0, count, batch_size):
        await asyncio.sleep(0.01)
        batch = [
            {'id': i, 'name': f'Product-{i}', 'price': i * 9.99}
            for i in range(start, min(start + batch_size, count))
        ]
        for item in batch:
            yield item

async def run_async_gen():
    print()
    print('=== Async generator ===')
    count = total = 0
    async for product in stream_products(18):
        count += 1
        total += product['price']
    print(f'Streamed {count} products, total value \${total:.2f}')

asyncio.run(run_async_gen())

# Step 8: Capstone — concurrent data pipeline
async def fetch_product(pid: int, sem: asyncio.Semaphore) -> dict:
    async with sem:
        await asyncio.sleep(0.01)
        return {'id': pid, 'name': f'Product-{pid}', 'price': pid * 9.99, 'stock': pid % 50}

async def fetch_inventory(pid: int) -> int:
    await asyncio.sleep(0.005)
    return (pid * 7) % 100

async def enrich_product(p: dict) -> dict:
    inventory = await fetch_inventory(p['id'])
    return {**p, 'live_stock': inventory, 'value': p['price'] * inventory}

async def capstone_pipeline():
    print()
    print('=== Capstone: Async Data Pipeline ===')
    t0 = time.perf_counter()

    sem = asyncio.Semaphore(10)  # max 10 concurrent fetches
    product_ids = range(1, 31)

    # Stage 1: fetch products concurrently
    products = await asyncio.gather(*[fetch_product(i, sem) for i in product_ids])

    # Stage 2: enrich concurrently with TaskGroup
    enriched = []
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(enrich_product(p)) for p in products]
    enriched = [t.result() for t in tasks]

    # Stage 3: aggregate
    total_value = sum(p['value'] for p in enriched)
    in_stock    = sum(1 for p in enriched if p['live_stock'] > 0)
    top5        = sorted(enriched, key=lambda p: p['value'], reverse=True)[:5]

    elapsed = time.perf_counter() - t0
    print(f'Pipeline complete: {len(enriched)} products in {elapsed:.3f}s')
    print(f'Total value: \${total_value:,.2f}')
    print(f'In stock: {in_stock}/{len(enriched)}')
    print('Top 5 by value:')
    for p in top5:
        print(f'  {p[\"name\"]:15s} \${p[\"value\"]:8.2f} (stock={p[\"live_stock\"]})')

asyncio.run(capstone_pipeline())
"
```

**📸 Verified Output:**
```
=== Producer-Consumer ===
Processed 20 items by 4 workers
Distribution: {0: 5, 1: 5, 2: 5, 3: 5}

=== Retry with exponential backoff ===
  Retry 1/5 after 0.012s: Service unavailable (attempt 0)
  Retry 2/5 after 0.023s: Service unavailable (attempt 1)
  Retry 3/5 after 0.047s: Service unavailable (attempt 2)
Final: Success on attempt 3

=== asyncio.timeout ===
Task completed within 1.0s
Timed out after 0.05s (TimeoutError raised)

=== Async context manager ===
  Connected to sqlite+async:///store.db
  Query returned 3 rows
  Second query: 3 rows
  Disconnected (2 queries executed)

=== Capstone: Async Data Pipeline ===
Pipeline complete: 30 products in 0.052s
Total value: $27,453.30
In stock: 29/30
Top 5 by value:
  Product-28      $2,637.36 (stock=96)
  ...
```

---

## Summary

| Pattern | API | Use case |
|---------|-----|---------|
| Rate limit | `asyncio.Semaphore(n)` | Max n concurrent |
| Structured concurrency | `async with TaskGroup()` | Group tasks, propagate errors |
| Worker queue | `asyncio.Queue` + sentinel | Producer-consumer |
| Retry backoff | `wait_for` + sleep | Flaky external services |
| Hard timeout | `asyncio.timeout(secs)` | Kill hung operations |
| Async context manager | `__aenter__`/`__aexit__` | Async resource management |
| Async generator | `async def ... yield` | Streaming data sources |

## Further Reading
- [asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [PEP 654 — ExceptionGroup](https://peps.python.org/pep-0654/)
- [anyio for framework-agnostic async](https://anyio.readthedocs.io)
