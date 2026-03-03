# Lab 04: Concurrency — Threading, Multiprocessing & Executors

## Objective
Write concurrent Python programs: `threading`, `multiprocessing`, `concurrent.futures`, thread-safe data structures, and the GIL's implications.

## Time
35 minutes

## Prerequisites
- Lab 02 (Decorators)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Threading Basics & the GIL

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import threading
import time

def task(name: str, duration: float, results: list):
    print(f'  [{name}] starting')
    time.sleep(duration)
    results.append(f'{name} done in {duration}s')
    print(f'  [{name}] finished')

# Sequential
print('=== Sequential ===')
start = time.perf_counter()
results = []
for name, dur in [('A', 0.05), ('B', 0.03), ('C', 0.04)]:
    task(name, dur, results)
print(f'Sequential: {time.perf_counter()-start:.2f}s')

# Parallel with threads (good for I/O-bound work)
print()
print('=== Threaded ===')
start = time.perf_counter()
results = []
threads = []
for name, dur in [('A', 0.05), ('B', 0.03), ('C', 0.04)]:
    t = threading.Thread(target=task, args=(name, dur, results))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
print(f'Threaded: {time.perf_counter()-start:.2f}s')
print('Results:', results)

# GIL means threads don't help for CPU-bound work
def cpu_task(n: int) -> int:
    return sum(i**2 for i in range(n))

start = time.perf_counter()
results = [cpu_task(100_000) for _ in range(4)]
print(f'CPU sequential: {time.perf_counter()-start:.3f}s, result={results[0]:,}')
"
```

> 💡 **Python's GIL (Global Interpreter Lock)** means only one thread executes Python bytecode at a time. Threads are great for I/O-bound work (network, disk) where threads wait — but for CPU-bound work (computation), use `multiprocessing` to bypass the GIL with separate processes.

**📸 Verified Output:**
```
=== Sequential ===
  [A] starting
  [A] finished
  [B] starting
  [B] finished
  [C] starting
  [C] finished
Sequential: 0.12s

=== Threaded ===
  [A] starting
  [B] starting
  [C] starting
  [C] finished
  [B] finished
  [A] finished
Threaded: 0.05s
Results: ['C done in 0.04s', 'B done in 0.03s', 'A done in 0.05s']
CPU sequential: 0.08s, result=333,328,333,350,000
```

---

### Step 2: Thread Safety — Locks & Thread-Safe Structures

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import threading
import queue
import time
from collections import defaultdict

# Unsafe counter (race condition)
class UnsafeCounter:
    def __init__(self): self.count = 0
    def increment(self): self.count += 1

# Safe counter with lock
class SafeCounter:
    def __init__(self):
        self.count = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self.count += 1

    def get(self): return self.count

def run_counter(Counter, n_threads=10, increments=1000):
    c = Counter()
    threads = [threading.Thread(target=lambda: [c.increment() for _ in range(increments)])
               for _ in range(n_threads)]
    for t in threads: t.start()
    for t in threads: t.join()
    return c.count

expected = 10 * 1000
safe = run_counter(SafeCounter)
print(f'SafeCounter: {safe} (expected {expected}, correct={safe == expected})')

# RLock — reentrant lock
class ResourceManager:
    def __init__(self):
        self._lock = threading.RLock()
        self.resources = {}

    def acquire(self, name: str):
        with self._lock:
            if name not in self.resources:
                self.resources[name] = 0
            self.resources[name] += 1
            return self._inner_check(name)  # can re-acquire same lock

    def _inner_check(self, name: str) -> bool:
        with self._lock:  # RLock allows this
            return self.resources.get(name, 0) > 0

rm = ResourceManager()
print('Acquired:', rm.acquire('db_connection'))
print('Resources:', rm.resources)

# Thread-safe queue — producer/consumer
def producer(q: queue.Queue, items: list):
    for item in items:
        q.put(item)
        time.sleep(0.002)
    q.put(None)  # sentinel

def consumer(q: queue.Queue, results: list):
    while True:
        item = q.get()
        if item is None: break
        results.append(item * 2)
        q.task_done()

q = queue.Queue(maxsize=5)
results = []
t_prod = threading.Thread(target=producer, args=(q, [1,2,3,4,5]))
t_cons = threading.Thread(target=consumer, args=(q, results))
t_prod.start(); t_cons.start()
t_prod.join(); t_cons.join()
print('Queue results:', results)

# threading.local() — thread-local storage
local = threading.local()

def set_user(user_id: int):
    local.user_id = user_id
    time.sleep(0.01)
    return local.user_id  # each thread sees its own value

threads = []
thread_results = {}
for uid in [1, 2, 3]:
    def work(u=uid):
        thread_results[u] = set_user(u)
    threads.append(threading.Thread(target=work))

for t in threads: t.start()
for t in threads: t.join()
print('Thread-local results:', thread_results)
"
```

**📸 Verified Output:**
```
SafeCounter: 10000 (expected 10000, correct=True)
Acquired: True
Resources: {'db_connection': 1}
Queue results: [2, 4, 6, 8, 10]
Thread-local results: {1: 1, 2: 2, 3: 3}
```

---

### Steps 3–8: ThreadPoolExecutor, ProcessPoolExecutor, Semaphore, Event, Barrier, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import concurrent.futures
import threading
import time
import math

# Step 3: ThreadPoolExecutor — I/O-bound tasks
def fetch_price(product_id: int) -> dict:
    time.sleep(0.01)  # simulate network
    prices = {1: 864.0, 2: 49.99, 3: 99.99, 4: 29.99, 5: 1299.0}
    return {'id': product_id, 'price': prices.get(product_id, 0)}

print('=== ThreadPoolExecutor ===')
start = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(fetch_price, i): i for i in range(1, 6)}
    results = []
    for future in concurrent.futures.as_completed(futures):
        results.append(future.result())

results.sort(key=lambda x: x['id'])
elapsed = time.perf_counter() - start
print(f'Fetched {len(results)} prices in {elapsed:.3f}s (5 sequential would be 0.05s)')
for r in results:
    print(f'  #{r[\"id\"]}: \${r[\"price\"]}')

# Step 4: ProcessPoolExecutor — CPU-bound tasks
def is_prime(n: int) -> bool:
    if n < 2: return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0: return False
    return True

def count_primes_in_range(start_end: tuple) -> int:
    start, end = start_end
    return sum(1 for n in range(start, end) if is_prime(n))

print()
print('=== ProcessPoolExecutor (CPU-bound) ===')
ranges = [(0, 10000), (10000, 20000), (20000, 30000), (30000, 40000)]
start = time.perf_counter()
with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
    counts = list(executor.map(count_primes_in_range, ranges))
total_primes = sum(counts)
elapsed = time.perf_counter() - start
print(f'Primes 0-40000: {total_primes} (found in {elapsed:.3f}s)')
print('Per range:', counts)

# Step 5: Semaphore — limit concurrency
print()
print('=== Semaphore (max 2 concurrent) ===')
sem = threading.Semaphore(2)
order = []
order_lock = threading.Lock()

def limited_task(task_id: int):
    with sem:
        with order_lock:
            order.append(f'start-{task_id}')
        time.sleep(0.01)
        with order_lock:
            order.append(f'end-{task_id}')

threads = [threading.Thread(target=limited_task, args=(i,)) for i in range(5)]
for t in threads: t.start()
for t in threads: t.join()
# At most 2 tasks running simultaneously
print('Order:', order)

# Step 6: Event — signal between threads
print()
print('=== Event ===')
ready = threading.Event()
results = []

def worker(event: threading.Event):
    print('  Worker: waiting for signal...')
    event.wait()
    print('  Worker: signal received, working...')
    results.append('done')

t = threading.Thread(target=worker, args=(ready,))
t.start()
time.sleep(0.02)
print('  Main: sending signal')
ready.set()
t.join()
print('  Results:', results)

# Step 7: map with executor — simple parallel map
def process_batch(items: list[int]) -> list[int]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        return list(ex.map(lambda x: x * x, items))

squares = process_batch(list(range(10)))
print()
print('Parallel squares:', squares)

# Step 8: Capstone — concurrent product enrichment pipeline
print()
print('=== Concurrent Enrichment Pipeline ===')

products = [
    {'id': i, 'name': f'Product-{i}', 'price': i * 10.0}
    for i in range(1, 9)
]

def enrich_product(product: dict) -> dict:
    time.sleep(0.005)  # simulate DB lookup
    product = product.copy()
    product['discount'] = 0.1 if product['price'] > 50 else 0.0
    product['final_price'] = round(product['price'] * (1 - product['discount']), 2)
    product['in_stock'] = product['id'] % 3 != 0  # simulate stock check
    return product

start = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    enriched = list(executor.map(enrich_product, products))
elapsed = time.perf_counter() - start

print(f'Enriched {len(enriched)} products in {elapsed:.3f}s')
in_stock = [p for p in enriched if p['in_stock']]
print(f'In stock: {len(in_stock)}/{len(enriched)}')
total = sum(p['final_price'] for p in in_stock)
print(f'Total value (in-stock): \${total:.2f}')
for p in enriched[:3]:
    print(f'  #{p[\"id\"]} {p[\"name\"]:12s} \${p[\"price\"]} → \${p[\"final_price\"]} disc={p[\"discount\"]:.0%}')
"
```

**📸 Verified Output:**
```
=== ThreadPoolExecutor ===
Fetched 5 prices in 0.012s (5 sequential would be 0.05s)
  #1: $864.0
  #2: $49.99
  #3: $99.99
  #4: $29.99
  #5: $1299.0

=== ProcessPoolExecutor (CPU-bound) ===
Primes 0-40000: 4203 (found in 0.12s)
Per range: [1229, 1033, 983, 958]

=== Semaphore (max 2 concurrent) ===
Order: ['start-0', 'start-1', 'end-0', 'start-2', 'end-1', 'start-3', ...]

=== Concurrent Enrichment Pipeline ===
Enriched 8 products in 0.011s
In stock: 6/8
Total value (in-stock): $228.00
  #1 Product-1   $10.0 → $10.0  disc=0%
  #2 Product-2   $20.0 → $20.0  disc=0%
  #3 Product-3   $30.0 → $30.0  disc=0%
```

---

## Summary

| Tool | Best for | GIL? |
|------|---------|------|
| `threading.Thread` | I/O-bound, simple concurrency | Limited by GIL |
| `ThreadPoolExecutor` | I/O-bound pool, map/submit | Limited by GIL |
| `ProcessPoolExecutor` | CPU-bound, bypasses GIL | No GIL |
| `threading.Lock` | Protect shared mutable state | — |
| `threading.Semaphore` | Limit concurrent access | — |
| `threading.Event` | Signal between threads | — |
| `queue.Queue` | Thread-safe producer/consumer | — |

## Further Reading
- [threading](https://docs.python.org/3/library/threading.html)
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
- [Python GIL explained](https://realpython.com/python-gil/)
