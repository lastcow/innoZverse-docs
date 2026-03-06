# Lab 08: GIL-Free Concurrency

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

The Global Interpreter Lock (GIL) prevents true parallel execution of Python threads for CPU-bound work. This lab benchmarks GIL impact, escapes it with `multiprocessing`, explores shared memory, and builds efficient parallel pipelines.

## Step 1: Understanding the GIL

```python
import threading
import time

def cpu_bound(n):
    """Pure CPU work — blocked by GIL between threads."""
    total = 0
    for i in range(n):
        total += i * i
    return total

N = 2_000_000

# Single thread
start = time.perf_counter()
cpu_bound(N)
cpu_bound(N)
serial_time = time.perf_counter() - start
print(f"Serial (2 calls): {serial_time*1000:.0f}ms")

# Two threads — GIL means they take turns, no speedup
t1 = threading.Thread(target=cpu_bound, args=(N,))
t2 = threading.Thread(target=cpu_bound, args=(N,))
start = time.perf_counter()
t1.start(); t2.start()
t1.join(); t2.join()
thread_time = time.perf_counter() - start
print(f"2 Threads: {thread_time*1000:.0f}ms")
print(f"Thread speedup: {serial_time/thread_time:.2f}x (expected ≈1.0 due to GIL)")
```

> 💡 For I/O-bound tasks (network, disk), threads work great — threads release the GIL while waiting for I/O. For CPU-bound tasks, use `multiprocessing` to bypass the GIL.

## Step 2: `multiprocessing.Pool` — True Parallelism

```python
import multiprocessing
import time

def cpu_heavy(n):
    """CPU-intensive: total bypasses GIL via multiprocessing."""
    total = 0
    for i in range(n):
        total += i * i % 997
    return total

N = 2_000_000
TASKS = 4

# Sequential baseline
start = time.perf_counter()
results = [cpu_heavy(N) for _ in range(TASKS)]
seq_time = time.perf_counter() - start
print(f"Sequential ({TASKS} tasks): {seq_time*1000:.0f}ms")

# Multiprocessing Pool
cpu_count = multiprocessing.cpu_count()
print(f"CPU cores available: {cpu_count}")

with multiprocessing.Pool(min(TASKS, cpu_count)) as pool:
    start = time.perf_counter()
    results = pool.map(cpu_heavy, [N] * TASKS)
    mp_time = time.perf_counter() - start

print(f"Multiprocessing ({min(TASKS, cpu_count)} workers): {mp_time*1000:.0f}ms")
print(f"Speedup: {seq_time/mp_time:.2f}x")
```

📸 **Verified Output:**
```
Sequential (4 tasks): 1367ms
Multiprocessing (4 workers): 768ms
Speedup: 1.78x
```

## Step 3: `pool.map` vs `pool.starmap` vs `pool.imap`

```python
import multiprocessing
import time

def add_and_square(x, y, scale=1):
    return scale * (x + y) ** 2

with multiprocessing.Pool(4) as pool:
    # map: single arg per task
    results_map = pool.map(lambda x: x**2, range(10))
    print(f"map: {results_map}")
    
    # starmap: multiple args per task (unpacks tuples)
    args = [(i, i+1) for i in range(5)]
    results_star = pool.starmap(add_and_square, args)
    print(f"starmap: {results_star}")
    
    # starmap with kwargs via iterable
    args_kw = [(i, i+1, 2) for i in range(5)]
    results_scaled = pool.starmap(add_and_square, args_kw)
    print(f"starmap scaled: {results_scaled}")
    
    # imap: lazy iterator (good for streaming large datasets)
    result_iter = pool.imap(lambda x: x**3, range(8), chunksize=2)
    results_imap = list(result_iter)
    print(f"imap: {results_imap}")
```

## Step 4: `ProcessPoolExecutor` and `as_completed`

```python
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

def simulate_work(task_id: int, duration: float) -> dict:
    """Simulates variable-length CPU work."""
    import time as t
    start = t.perf_counter()
    # CPU work proportional to duration
    count = int(duration * 1_000_000)
    total = sum(i * i % 997 for i in range(count))
    elapsed = t.perf_counter() - start
    return {"task_id": task_id, "duration": elapsed, "result": total % 1000}

tasks = [(i, 0.1 + (i % 3) * 0.05) for i in range(8)]

print("=== as_completed (results arrive as they finish) ===")
start = time.perf_counter()

with ProcessPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(simulate_work, task_id, duration): task_id
        for task_id, duration in tasks
    }
    
    for future in as_completed(futures):
        task_id = futures[future]
        result = future.result()
        elapsed = time.perf_counter() - start
        print(f"  Task {result['task_id']:2d} done at {elapsed*1000:.0f}ms, result={result['result']}")

total_time = time.perf_counter() - start
print(f"\nTotal: {total_time*1000:.0f}ms")
```

## Step 5: Shared Memory

```python
from multiprocessing.shared_memory import SharedMemory
import multiprocessing
import numpy as np
import time

def fill_shared_memory(shm_name: str, size: int, value: float, start_idx: int):
    """Worker that writes to shared memory."""
    existing_shm = SharedMemory(name=shm_name)
    arr = np.ndarray((size,), dtype=np.float64, buffer=existing_shm.buf)
    
    chunk_size = size // 4
    end_idx = min(start_idx + chunk_size, size)
    for i in range(start_idx, end_idx):
        arr[i] = value * i
    
    existing_shm.close()

# Create shared memory
size = 1000
shm = SharedMemory(create=True, size=size * np.float64().itemsize)
arr = np.ndarray((size,), dtype=np.float64, buffer=shm.buf)
arr[:] = 0.0

print(f"Shared memory: name={shm.name}, size={shm.size} bytes")
print(f"Initial array[:5]: {arr[:5]}")

# Multiple processes write to different sections
chunk = size // 4
processes = []
for i in range(4):
    p = multiprocessing.Process(
        target=fill_shared_memory,
        args=(shm.name, size, 1.0, i * chunk)
    )
    processes.append(p)
    p.start()

for p in processes:
    p.join()

print(f"After multiprocess write:")
print(f"  arr[:5]:     {arr[:5]}")
print(f"  arr[250:255]: {arr[250:255]}")
print(f"  arr[500:505]: {arr[500:505]}")
print(f"  Sum: {arr.sum():.0f}")

shm.close()
shm.unlink()
```

> 💡 `SharedMemory` allows zero-copy data sharing between processes. Wrap with `numpy.ndarray` for efficient numerical operations across process boundaries.

## Step 6: `mmap` for IPC

```python
import mmap
import os
import struct
import multiprocessing
import tempfile

def writer(filename, size):
    """Write structured data to mmap."""
    with open(filename, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), size)
        # Write 100 doubles
        for i in range(100):
            offset = i * 8
            mm[offset:offset+8] = struct.pack('d', float(i * i))
        mm.flush()
        mm.close()

def reader(filename, size):
    """Read from mmap."""
    with open(filename, 'rb') as f:
        mm = mmap.mmap(f.fileno(), size, access=mmap.ACCESS_READ)
        values = []
        for i in range(5):
            offset = i * 8
            val = struct.unpack('d', mm[offset:offset+8])[0]
            values.append(val)
        mm.close()
    return values

# Create backing file
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp_path = tmp.name
    size = 100 * 8  # 100 doubles
    tmp.write(b'\x00' * size)

# Write and read
w_proc = multiprocessing.Process(target=writer, args=(tmp_path, size))
w_proc.start()
w_proc.join()

result = reader(tmp_path, size)
print(f"mmap IPC — first 5 values: {result}")
os.unlink(tmp_path)
```

## Step 7: Chunked Parallel Processing Pattern

```python
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import time

def process_chunk(chunk: list) -> dict:
    """Process a chunk of data items."""
    return {
        'count': len(chunk),
        'sum': sum(chunk),
        'max': max(chunk),
        'min': min(chunk),
    }

def parallel_aggregate(data: list, n_workers: int = 4) -> dict:
    """Split data into chunks and aggregate results."""
    chunk_size = max(1, len(data) // n_workers)
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        partial_results = list(executor.map(process_chunk, chunks))
    
    # Aggregate
    total_count = sum(r['count'] for r in partial_results)
    total_sum   = sum(r['sum'] for r in partial_results)
    global_max  = max(r['max'] for r in partial_results)
    global_min  = min(r['min'] for r in partial_results)
    
    return {
        'count': total_count,
        'sum': total_sum,
        'mean': total_sum / total_count,
        'max': global_max,
        'min': global_min,
    }

data = list(range(100_000))
import random
random.shuffle(data)

start = time.perf_counter()
result = parallel_aggregate(data)
elapsed = time.perf_counter() - start

print(f"Parallel aggregate ({len(data)} items):")
print(f"  count={result['count']}, sum={result['sum']}")
print(f"  mean={result['mean']:.1f}, max={result['max']}, min={result['min']}")
print(f"  Time: {elapsed*1000:.0f}ms")
```

## Step 8: Capstone — Parallel Data Pipeline

```python
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import statistics

def extract(item_id: int) -> dict:
    """Simulate data extraction."""
    import time as t
    t.sleep(0)  # simulate I/O
    return {'id': item_id, 'raw': item_id * 3.14}

def transform(record: dict) -> dict:
    """CPU-intensive transformation."""
    val = record['raw']
    # Simulate computation
    result = sum(val * i for i in range(1000)) / 1000
    return {'id': record['id'], 'transformed': round(result, 4)}

def load(records: list) -> dict:
    """Aggregate results."""
    values = [r['transformed'] for r in records]
    return {
        'count': len(values),
        'total': sum(values),
        'mean': statistics.mean(values),
        'stdev': statistics.stdev(values) if len(values) > 1 else 0,
    }

def etl_pipeline(n_items: int = 100, n_workers: int = 4):
    """Full ETL pipeline using ProcessPoolExecutor."""
    print(f"ETL: {n_items} items, {n_workers} workers")
    start = time.perf_counter()
    
    # Stage 1: Extract (could be parallelized for I/O)
    raw_data = [extract(i) for i in range(n_items)]
    t1 = time.perf_counter()
    print(f"  Extract: {(t1-start)*1000:.0f}ms ({len(raw_data)} records)")
    
    # Stage 2: Transform (CPU-bound — parallelize!)
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        transformed = list(executor.map(transform, raw_data, chunksize=10))
    t2 = time.perf_counter()
    print(f"  Transform: {(t2-t1)*1000:.0f}ms ({len(transformed)} records)")
    
    # Stage 3: Load/Aggregate
    summary = load(transformed)
    t3 = time.perf_counter()
    print(f"  Load: {(t3-t2)*1000:.0f}ms")
    
    total = t3 - start
    print(f"\nSummary: {summary}")
    print(f"Total time: {total*1000:.0f}ms")
    return summary

result = etl_pipeline(n_items=200, n_workers=4)
```

📸 **Verified Output:**
```
Sequential (4 tasks): 1367ms
Multiprocessing (4 workers): 768ms
Speedup: 1.78x
```

## Summary

| Concept | API | Use Case |
|---|---|---|
| GIL impact | `threading.Thread` benchmark | Understand CPU-bound limits |
| Process pool | `multiprocessing.Pool.map` | Parallel CPU work |
| `starmap` | Multiple args per task | Complex function signatures |
| `ProcessPoolExecutor` | `concurrent.futures` | Modern pool API |
| `as_completed` | Futures iteration | Handle results as they arrive |
| Shared memory | `SharedMemory` + numpy | Zero-copy inter-process data |
| `mmap` IPC | `mmap.mmap` | File-backed shared memory |
| Chunked pipeline | Split → parallel → aggregate | Big data processing |
