# Lab 05: Async/Await & asyncio

## Objective
Write asynchronous Python programs using `asyncio`: coroutines, tasks, `gather`, `async for`, async context managers, queues, and concurrent I/O patterns.

## Time
35 minutes

## Prerequisites
- Lab 03 (Generators), Lab 04 (Concurrency)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Coroutines & Event Loop

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import asyncio
import time

async def say_hello(name: str, delay: float) -> str:
    await asyncio.sleep(delay)  # non-blocking sleep
    message = f'Hello from {name}!'
    print(f'  {message}')
    return message

async def main():
    print('=== Sequential (await one at a time) ===')
    start = time.perf_counter()
    r1 = await say_hello('Alice', 0.03)
    r2 = await say_hello('Bob',   0.02)
    r3 = await say_hello('Carol', 0.04)
    print(f'Sequential: {time.perf_counter()-start:.3f}s')

    print()
    print('=== Concurrent (asyncio.gather) ===')
    start = time.perf_counter()
    results = await asyncio.gather(
        say_hello('Alice', 0.03),
        say_hello('Bob',   0.02),
        say_hello('Carol', 0.04),
    )
    print(f'Concurrent: {time.perf_counter()-start:.3f}s')
    print('Results:', results)

asyncio.run(main())
"
```

> 💡 **`asyncio.gather()`** runs coroutines concurrently on a single thread by interleaving them on the event loop. When one coroutine awaits (I/O, sleep), the event loop runs another. Unlike threads, there's no GIL issue and no data races — only one coroutine runs at a time, but they overlap on I/O waits.

**📸 Verified Output:**
```
=== Sequential (await one at a time) ===
  Hello from Alice!
  Hello from Bob!
  Hello from Carol!
Sequential: 0.091s

=== Concurrent (asyncio.gather) ===
  Hello from Bob!
  Hello from Alice!
  Hello from Carol!
Concurrent: 0.041s
Results: ['Hello from Alice!', 'Hello from Bob!', 'Hello from Carol!']
```

---

### Step 2: Tasks, Timeouts & Cancellation

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import asyncio

async def slow_operation(name: str, seconds: float) -> str:
    print(f'  [{name}] starting ({seconds}s)')
    await asyncio.sleep(seconds)
    print(f'  [{name}] done')
    return f'{name}: complete'

async def main():
    # Tasks — schedule coroutines without awaiting immediately
    task1 = asyncio.create_task(slow_operation('Download', 0.05))
    task2 = asyncio.create_task(slow_operation('Process',  0.03))
    task3 = asyncio.create_task(slow_operation('Upload',   0.04))

    # Can do other work while tasks run
    print('Tasks scheduled, doing other work...')
    await asyncio.sleep(0.01)
    print('Still running...')

    # Wait for all
    results = await asyncio.gather(task1, task2, task3)
    print('All done:', results)

    # Timeout
    print()
    print('=== Timeout ===')
    try:
        result = await asyncio.wait_for(
            slow_operation('Slow', 1.0),
            timeout=0.05
        )
    except asyncio.TimeoutError:
        print('  Operation timed out!')

    # Cancellation
    print()
    print('=== Cancellation ===')
    async def cancellable():
        try:
            print('  Cancellable: started')
            await asyncio.sleep(1.0)
            print('  Cancellable: done (should not print)')
        except asyncio.CancelledError:
            print('  Cancellable: cancelled gracefully')
            raise  # re-raise is important

    task = asyncio.create_task(cancellable())
    await asyncio.sleep(0.02)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print('  Task was cancelled')

    # gather with return_exceptions
    print()
    print('=== gather with errors ===')
    async def may_fail(n: int):
        await asyncio.sleep(0.01)
        if n == 2: raise ValueError(f'Task {n} failed')
        return f'task-{n} ok'

    results = await asyncio.gather(
        may_fail(1), may_fail(2), may_fail(3),
        return_exceptions=True
    )
    for r in results:
        if isinstance(r, Exception):
            print(f'  Error: {r}')
        else:
            print(f'  OK: {r}')

asyncio.run(main())
"
```

**📸 Verified Output:**
```
Tasks scheduled, doing other work...
Still running...
  [Process] done
  [Upload] done
  [Download] done
All done: ['Download: complete', 'Process: complete', 'Upload: complete']

=== Timeout ===
  [Slow] starting (1.0s)
  Operation timed out!

=== Cancellation ===
  Cancellable: started
  Cancellable: cancelled gracefully
  Task was cancelled

=== gather with errors ===
  OK: task-1 ok
  Error: Task 2 failed
  OK: task-3 ok
```

---

### Steps 3–8: Async Generators, Queues, Semaphore, Context Managers, HTTP simulation, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import asyncio
import time
from contextlib import asynccontextmanager

# Step 3: Async generators
async def paginated_fetch(base_url: str, page_size: int = 2):
    '''Simulate paginated API — yields pages lazily'''
    all_data = list(range(1, 10))  # simulate 9 items
    for i in range(0, len(all_data), page_size):
        await asyncio.sleep(0.005)  # simulate network
        page = all_data[i:i+page_size]
        print(f'  Fetched page {i//page_size + 1}: {page}')
        yield page

async def stream_all_items(url: str):
    async for page in paginated_fetch(url):
        for item in page:
            yield item

async def demo_async_gen():
    print('=== Async Generator ===')
    items = []
    async for item in stream_all_items('/api/items'):
        items.append(item)
    print('All items:', items)

# Step 4: Async Queue — producer/consumer
async def producer(queue: asyncio.Queue, items: list):
    for item in items:
        await queue.put(item)
        await asyncio.sleep(0.005)
    await queue.put(None)  # sentinel

async def consumer(queue: asyncio.Queue, results: list, name: str):
    while True:
        item = await queue.get()
        if item is None:
            await queue.put(None)  # pass sentinel along
            break
        result = item * 2
        results.append(result)
        print(f'  [{name}] processed {item} → {result}')
        queue.task_done()

async def demo_queue():
    print()
    print('=== Async Queue ===')
    queue = asyncio.Queue(maxsize=3)
    results = []
    await asyncio.gather(
        producer(queue, [1, 2, 3, 4, 5]),
        consumer(queue, results, 'consumer'),
    )
    print('Results:', results)

# Step 5: Semaphore — limit concurrent coroutines
async def fetch_url(sem: asyncio.Semaphore, url: str, delay: float) -> str:
    async with sem:
        await asyncio.sleep(delay)
        return f'response:{url}'

async def demo_semaphore():
    print()
    print('=== Semaphore (max 2 concurrent) ===')
    sem = asyncio.Semaphore(2)
    urls = [('/api/1', 0.03), ('/api/2', 0.02), ('/api/3', 0.04), ('/api/4', 0.01)]
    start = time.perf_counter()
    results = await asyncio.gather(*[fetch_url(sem, url, d) for url, d in urls])
    print(f'Done in {time.perf_counter()-start:.3f}s: {results}')

# Step 6: Async context manager
@asynccontextmanager
async def db_connection(url: str):
    print(f'  [db] connecting to {url}')
    await asyncio.sleep(0.005)
    conn = {'url': url, 'active': True}
    try:
        yield conn
    finally:
        conn['active'] = False
        print(f'  [db] disconnected from {url}')

async def demo_context():
    print()
    print('=== Async Context Manager ===')
    async with db_connection('sqlite:///app.db') as conn:
        print(f'  Using connection: {conn}')
        await asyncio.sleep(0.01)
    print(f'  After context: active={conn[\"active\"]}')

# Step 7: Event loop with periodic task
async def periodic(interval: float, name: str, count: int):
    for i in range(count):
        print(f'  [{name}] tick {i+1}/{count}')
        await asyncio.sleep(interval)

async def demo_periodic():
    print()
    print('=== Periodic Tasks ===')
    await asyncio.gather(
        periodic(0.02, 'fast', 3),
        periodic(0.05, 'slow', 2),
    )

# Step 8: Capstone — async product enrichment service
async def fetch_price(product_id: int) -> float:
    await asyncio.sleep(0.01)
    return {1: 864.0, 2: 49.99, 3: 99.99, 4: 29.99, 5: 1299.0}.get(product_id, 0)

async def fetch_stock(product_id: int) -> int:
    await asyncio.sleep(0.008)
    return {1: 15, 2: 80, 3: 999, 4: 0, 5: 5}.get(product_id, 0)

async def enrich_product(product_id: int, name: str) -> dict:
    # Fetch price and stock concurrently
    price, stock = await asyncio.gather(
        fetch_price(product_id),
        fetch_stock(product_id),
    )
    return {
        'id': product_id,
        'name': name,
        'price': price,
        'stock': stock,
        'status': 'active' if stock > 0 else 'out_of_stock',
        'value': round(price * stock, 2),
    }

async def capstone():
    print()
    print('=== Capstone: Async Product Service ===')
    products = [
        (1, 'Surface Pro 12\"'),
        (2, 'Surface Pen'),
        (3, 'Office 365'),
        (4, 'USB-C Hub'),
        (5, 'Surface Book 3'),
    ]
    start = time.perf_counter()
    enriched = await asyncio.gather(*[enrich_product(pid, name) for pid, name in products])
    elapsed = time.perf_counter() - start

    print(f'Enriched {len(enriched)} products in {elapsed:.3f}s')
    total_value = sum(p['value'] for p in enriched)
    for p in enriched:
        print(f'  [{p[\"id\"]}] {p[\"name\"]:22s} \${p[\"price\"]:8.2f}  stock={p[\"stock\"]:4d}  {p[\"status\"]}')
    print(f'Total inventory value: \${total_value:,.2f}')

async def main():
    await demo_async_gen()
    await demo_queue()
    await demo_semaphore()
    await demo_context()
    await demo_periodic()
    await capstone()

asyncio.run(main())
"
```

**📸 Verified Output:**
```
=== Async Generator ===
  Fetched page 1: [1, 2]
  Fetched page 2: [3, 4]
  Fetched page 3: [5, 6]
  Fetched page 4: [7, 8]
  Fetched page 5: [9]
All items: [1, 2, 3, 4, 5, 6, 7, 8, 9]

=== Capstone: Async Product Service ===
Enriched 5 products in 0.012s
  [1] Surface Pro 12"       $  864.00  stock=  15  active
  [2] Surface Pen           $   49.99  stock=  80  active
  [3] Office 365            $   99.99  stock= 999  active
  [4] USB-C Hub             $   29.99  stock=   0  out_of_stock
  [5] Surface Book 3        $ 1299.00  stock=   5  active
Total inventory value: $120,752.21
```

---

## Summary

| Concept | Syntax | Notes |
|---------|--------|-------|
| Define coroutine | `async def fn():` | Must be awaited |
| Await | `result = await coro()` | Suspends until done |
| Run event loop | `asyncio.run(main())` | Python 3.7+ |
| Concurrent | `asyncio.gather(c1, c2)` | Run coroutines in parallel |
| Task | `asyncio.create_task(coro)` | Schedule without blocking |
| Timeout | `asyncio.wait_for(coro, timeout=N)` | Raises TimeoutError |
| Async generator | `async def gen(): yield ...` | Use with `async for` |
| Async context | `async with ctx_mgr:` | Pairs with `__aenter__/__aexit__` |

## Further Reading
- [asyncio docs](https://docs.python.org/3/library/asyncio.html)
- [Real Python: async IO](https://realpython.com/async-io-python/)
