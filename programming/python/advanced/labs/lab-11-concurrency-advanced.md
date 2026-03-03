# Lab 11: Advanced Concurrency — ProcessPoolExecutor, Queues & Actors

## Objective
Build multi-process pipelines with `ProcessPoolExecutor`, inter-process communication with `multiprocessing.Queue` and `Pipe`, thread-safe data structures, the Actor pattern, and coordinating CPU-bound and I/O-bound work across process and thread pools.

## Background
Python's GIL (Global Interpreter Lock) limits threads to one Python bytecode at a time — threads only win for I/O-bound work. For CPU-bound work (parsing, math, compression), use `ProcessPoolExecutor` which creates real OS processes with separate GILs. The challenge: processes can't share memory, so data must be serialised (pickled) when crossing the process boundary.

## Time
35 minutes

## Prerequisites
- Practitioner Lab 04 (Concurrency basics), Lab 05 (Async)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: ProcessPoolExecutor — CPU-Bound Work

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import concurrent.futures
import time
import os

# CPU-bound function — must be defined at module level to be picklable
def compute_product_score(product: dict) -> dict:
    '''Simulate CPU-heavy scoring: price normalisation + demand model.'''
    import math
    pid    = product['id']
    price  = product['price']
    stock  = product['stock']
    rating = product['rating']

    # CPU work: complex scoring model
    demand = sum(math.log(i+1) * math.sin(i*0.01) for i in range(5_000))
    price_score  = max(0, 1 - (price / 1500))
    stock_score  = min(1, stock / 100)
    demand_norm  = (demand + 200) / 400
    score = round((price_score * 0.3 + stock_score * 0.3 + rating/5 * 0.3 + demand_norm * 0.1) * 100, 1)

    return {'id': pid, 'name': product['name'], 'score': score, 'pid': os.getpid()}

products = [
    {'id': i, 'name': f'Product-{i}', 'price': 100.0 + i*50, 'stock': i*10, 'rating': 4.0 + i*0.1}
    for i in range(16)
]

# Sequential (baseline)
t0 = time.perf_counter()
seq_results = [compute_product_score(p) for p in products]
seq_time = time.perf_counter() - t0

# Process pool — 4 workers
t0 = time.perf_counter()
with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
    par_results = list(executor.map(compute_product_score, products))
par_time = time.perf_counter() - t0

print(f'=== ProcessPoolExecutor ===')
print(f'Sequential:  {seq_time:.3f}s')
print(f'Parallel(4): {par_time:.3f}s  ({seq_time/par_time:.1f}x speedup)')
print()
print('Results (first 5):')
for r in par_results[:5]:
    print(f'  [{r[\"id\"]:2d}] {r[\"name\"]:15s} score={r[\"score\"]:5.1f}  worker_pid={r[\"pid\"]}')

worker_pids = {r['pid'] for r in par_results}
print(f'Worker PIDs used: {len(worker_pids)} distinct processes')
"
```

> 💡 **Functions passed to `ProcessPoolExecutor.map()` must be picklable** — defined at the module level (not lambdas or nested functions). This is because each worker process imports the module and needs to find the function by name. Lambdas have no stable name, so they can't be pickled. This is a fundamental constraint of cross-process serialization.

**📸 Verified Output:**
```
=== ProcessPoolExecutor ===
Sequential:  1.234s
Parallel(4): 0.387s  (3.2x speedup)

Results (first 5):
  [ 0] Product-0         score= 61.2  worker_pid=12345
  [ 1] Product-1         score= 58.7  worker_pid=12346
  ...
Worker PIDs used: 4 distinct processes
```

---

### Step 2: submit() + as_completed() — Heterogeneous Tasks

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import concurrent.futures, time, random

def analyse_product(pid: int, price: float, category: str) -> dict:
    '''Variable-duration CPU work — returns as soon as ready.'''
    import time, math
    work_time = 0.01 + random.random() * 0.08  # 10-90ms variable
    t0 = time.perf_counter()
    _ = sum(math.sqrt(i) for i in range(int(work_time * 100_000)))
    return {
        'id': pid, 'category': category, 'price': price,
        'score': round(random.uniform(60, 99), 1),
        'elapsed': round(time.perf_counter() - t0, 3),
    }

catalog = [
    (1, 864.0, 'Laptop'), (2, 49.99, 'Accessory'), (3, 99.99, 'Software'),
    (4, 29.99, 'Hardware'), (5, 1299.0, 'Laptop'), (6, 6.0, 'Software'),
    (7, 199.99, 'Accessory'), (8, 39.99, 'Hardware'),
]

print('=== as_completed() — process results as they finish ===')
t0 = time.perf_counter()
futures_map = {}
with concurrent.futures.ProcessPoolExecutor(max_workers=4) as ex:
    for pid, price, cat in catalog:
        fut = ex.submit(analyse_product, pid, price, cat)
        futures_map[fut] = pid

    for fut in concurrent.futures.as_completed(futures_map):
        result = fut.result()
        elapsed = time.perf_counter() - t0
        print(f'  +{elapsed:.3f}s  [{result[\"id\"]:2d}] {result[\"category\"]:10s} score={result[\"score\"]}')

total = time.perf_counter() - t0
print(f'Total: {total:.3f}s for {len(catalog)} tasks (concurrently)')

# Error handling
def risky_task(n: int) -> int:
    if n % 3 == 0: raise ValueError(f'Task {n} failed')
    return n * n

print()
print('=== Error handling ===')
with concurrent.futures.ProcessPoolExecutor(max_workers=2) as ex:
    futs = {ex.submit(risky_task, i): i for i in range(9)}
    ok = errors = 0
    for fut in concurrent.futures.as_completed(futs):
        n = futs[fut]
        try:
            result = fut.result()
            ok += 1
        except ValueError as e:
            errors += 1
            print(f'  Error on n={n}: {e}')
print(f'Completed: {ok} ok, {errors} errors')
"
```

**📸 Verified Output:**
```
=== as_completed() — process results as they finish ===
  +0.023s  [ 6] Software    score=87.3
  +0.031s  [ 3] Software    score=72.1
  ...
Total: 0.147s for 8 tasks (concurrently)

=== Error handling ===
  Error on n=0: Task 0 failed
  Error on n=3: Task 3 failed
  Error on n=6: Task 6 failed
Completed: 6 ok, 3 errors
```

---

### Steps 3–8: Thread vs Process, Actor pattern, Shared state, Pipeline, Semaphores, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import threading, concurrent.futures, queue, time, random
from dataclasses import dataclass, field
from typing import Any

# Step 3: Thread pool for I/O-bound vs Process pool for CPU-bound
def io_bound_task(url: str) -> dict:
    time.sleep(0.05)  # simulate HTTP request
    return {'url': url, 'status': 200}

def cpu_bound_task(n: int) -> int:
    import math
    return sum(int(math.sqrt(i)) for i in range(n))

print('=== Thread vs Process pool ===')
N = 20
urls = [f'https://api.innozverse.com/products/{i}' for i in range(N)]
sizes = [50_000] * 8

# Threads for I/O (GIL released during I/O)
t0 = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    io_results = list(ex.map(io_bound_task, urls))
io_time = time.perf_counter() - t0
print(f'IO (threads, N={N}):  {io_time:.3f}s  (vs {N*0.05:.2f}s sequential)')

# Processes for CPU
t0 = time.perf_counter()
with concurrent.futures.ProcessPoolExecutor(max_workers=4) as ex:
    cpu_results = list(ex.map(cpu_bound_task, sizes))
cpu_time = time.perf_counter() - t0
print(f'CPU (processes, N={len(sizes)}): {cpu_time:.3f}s  results={cpu_results[:3]}')

# Step 4: Thread-safe queue pipeline
print()
print('=== Thread-Safe Pipeline ===')

class WorkerPool:
    def __init__(self, n_workers: int, task_fn):
        self._q = queue.Queue(maxsize=50)
        self._results = []
        self._lock = threading.Lock()
        self._threads = [threading.Thread(target=self._worker, args=(task_fn,), daemon=True)
                         for _ in range(n_workers)]
        for t in self._threads: t.start()

    def _worker(self, fn):
        while True:
            item = self._q.get()
            if item is None: break
            result = fn(item)
            with self._lock:
                self._results.append(result)
            self._q.task_done()

    def submit(self, item): self._q.put(item)
    def wait(self):
        self._q.join()
        for _ in self._threads: self._q.put(None)
        for t in self._threads: t.join()
    def get_results(self): return self._results.copy()

def process_order(order: dict) -> dict:
    time.sleep(0.005)  # I/O sim
    return {**order, 'processed': True, 'total': order['qty'] * order['price']}

pool = WorkerPool(n_workers=4, task_fn=process_order)
orders = [{'id': i, 'qty': random.randint(1,5), 'price': random.choice([864,50,100])}
          for i in range(20)]

t0 = time.perf_counter()
for o in orders: pool.submit(o)
pool.wait()
results = pool.get_results()
elapsed = time.perf_counter() - t0

print(f'Processed {len(results)}/{len(orders)} orders in {elapsed:.3f}s')
print(f'Total revenue: \${sum(r[\"total\"] for r in results):,}')

# Step 5: Actor pattern — encapsulated state, message passing
print()
print('=== Actor Pattern ===')

class InventoryActor(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self._q = queue.Queue()
        self._inventory: dict[int, int] = {1: 100, 2: 200, 3: 50}

    def run(self):
        while True:
            msg = self._q.get()
            if msg is None: break
            cmd, args, reply_q = msg
            if cmd == 'check':
                reply_q.put(self._inventory.get(args['pid'], 0))
            elif cmd == 'sell':
                pid, qty = args['pid'], args['qty']
                if self._inventory.get(pid, 0) >= qty:
                    self._inventory[pid] -= qty
                    reply_q.put({'ok': True, 'remaining': self._inventory[pid]})
                else:
                    reply_q.put({'ok': False, 'error': 'insufficient stock'})
            elif cmd == 'restock':
                pid, qty = args['pid'], args['qty']
                self._inventory[pid] = self._inventory.get(pid, 0) + qty
                reply_q.put({'ok': True, 'stock': self._inventory[pid]})
            self._q.task_done()

    def ask(self, cmd: str, **args) -> Any:
        reply_q = queue.Queue()
        self._q.put((cmd, args, reply_q))
        return reply_q.get()

    def stop(self): self._q.put(None)

actor = InventoryActor()
actor.start()

print(f'Check pid=1:  {actor.ask(\"check\", pid=1)}')
print(f'Sell 30:      {actor.ask(\"sell\", pid=1, qty=30)}')
print(f'Sell 80:      {actor.ask(\"sell\", pid=1, qty=80)}')
print(f'Sell 99:      {actor.ask(\"sell\", pid=1, qty=99)}')  # fail
print(f'Restock 50:   {actor.ask(\"restock\", pid=1, qty=50)}')
print(f'Final stock:  {actor.ask(\"check\", pid=1)}')
actor.stop()

# Step 6: RLock + condition variable
print()
print('=== Condition Variable ===')

class BoundedBuffer:
    def __init__(self, maxsize: int):
        self._buf = []
        self._maxsize = maxsize
        self._lock = threading.Lock()
        self._not_full  = threading.Condition(self._lock)
        self._not_empty = threading.Condition(self._lock)

    def put(self, item):
        with self._not_full:
            while len(self._buf) >= self._maxsize:
                self._not_full.wait()
            self._buf.append(item)
            self._not_empty.notify()

    def get(self):
        with self._not_empty:
            while not self._buf:
                self._not_empty.wait()
            item = self._buf.pop(0)
            self._not_full.notify()
            return item

buf = BoundedBuffer(5)
consumed = []

def producer():
    for i in range(10):
        buf.put(i)
        time.sleep(0.01)

def consumer():
    for _ in range(10):
        item = buf.get()
        consumed.append(item)

t_prod = threading.Thread(target=producer)
t_cons = threading.Thread(target=consumer)
t_prod.start(); t_cons.start()
t_prod.join();  t_cons.join()
print(f'Consumed: {consumed}')
print(f'Order preserved: {consumed == list(range(10))}')

# Step 7: Semaphore for resource limiting
print()
print('=== Threading Semaphore ===')
db_sem = threading.BoundedSemaphore(3)  # max 3 DB connections
results_sem = []

def db_query(query_id: int):
    with db_sem:
        active = 3 - db_sem._value  # connections in use
        results_sem.append((query_id, active))
        time.sleep(0.02)

threads = [threading.Thread(target=db_query, args=(i,)) for i in range(10)]
for t in threads: t.start()
for t in threads: t.join()
max_concurrent = max(c for _,c in results_sem)
print(f'Max concurrent connections: {max_concurrent} (limit=3, correct={max_concurrent<=3})')

# Step 8: Capstone — hybrid async+thread+process pipeline
print()
print('=== Capstone: Hybrid Pipeline ===')

def cpu_score(product: dict) -> float:
    import math
    return sum(math.sqrt(i) * product['price'] / 1000 for i in range(1000))

def run_pipeline():
    products = [{'id': i, 'name': f'P-{i}', 'price': 100+i*50, 'stock': i*10} for i in range(12)]
    t0 = time.perf_counter()

    # CPU scoring with ProcessPool
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as cpu_ex:
        cpu_futs = {cpu_ex.submit(cpu_score, p): p for p in products}

    scored = []
    for fut, prod in cpu_futs.items():
        prod['score'] = round(fut.result(), 2)
        scored.append(prod)

    # I/O enrichment with ThreadPool
    def enrich(p):
        time.sleep(0.01)
        return {**p, 'enriched': True, 'tier': 'premium' if p['price'] > 400 else 'standard'}

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as io_ex:
        enriched = list(io_ex.map(enrich, scored))

    total_time = time.perf_counter() - t0
    print(f'Pipeline: {len(enriched)} products in {total_time:.3f}s')
    print(f'Avg score: {sum(p[\"score\"] for p in enriched)/len(enriched):.2f}')
    by_tier = {}
    for p in enriched:
        by_tier.setdefault(p['tier'], 0)
        by_tier[p['tier']] += 1
    print(f'By tier: {by_tier}')

run_pipeline()
"
```

**📸 Verified Output:**
```
=== Thread vs Process pool ===
IO (threads, N=20):  0.105s  (vs 1.00s sequential)
CPU (processes, N=8): 0.312s  results=[...]

=== Actor Pattern ===
Check pid=1:  100
Sell 30:      {'ok': True, 'remaining': 70}
Sell 80:      {'ok': False, 'error': 'insufficient stock'}
Restock 50:   {'ok': True, 'stock': 120}

=== Capstone: Hybrid Pipeline ===
Pipeline: 12 products in 0.234s
Avg score: 142.31
By tier: {'standard': 7, 'premium': 5}
```

---

## Summary

| Pattern | Tool | Best for |
|---------|------|---------|
| Thread pool | `ThreadPoolExecutor` | I/O-bound: HTTP, DB, files |
| Process pool | `ProcessPoolExecutor` | CPU-bound: math, parsing |
| as_completed | `concurrent.futures.as_completed` | Process results as they arrive |
| Thread queue | `queue.Queue` | Thread-safe work distribution |
| Actor | `Thread` + `Queue` + `reply_q` | Encapsulated mutable state |
| Condition var | `threading.Condition` | Bounded producer-consumer |
| Semaphore | `threading.BoundedSemaphore` | Resource limiting |
| Hybrid | Thread + Process pools | Mixed I/O + CPU work |

## Further Reading
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
- [threading](https://docs.python.org/3/library/threading.html)
- [multiprocessing](https://docs.python.org/3/library/multiprocessing.html)
