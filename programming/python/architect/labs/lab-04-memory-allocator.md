# Lab 04: Memory Allocator & GC

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

CPython uses a layered memory allocator (pymalloc) on top of the system allocator, with a cyclic garbage collector for reference cycles. This lab covers `tracemalloc` for memory profiling, the `gc` module internals, and `weakref` for cache patterns.

## Step 1: CPython Memory Architecture

```python
import sys

# CPython pymalloc: arenas → pools → blocks
# - Arenas: 256 KB chunks allocated from OS
# - Pools: 4 KB within arenas, one size class per pool
# - Blocks: fixed-size within pools (8, 16, 24, ... 512 bytes)
# Objects > 512 bytes go directly to the system allocator

# getsizeof returns the object's own memory (not referenced objects)
data = [1, 2, 3, 4, 5]
print(f"List (5 ints) getsizeof: {sys.getsizeof(data)} bytes")
print(f"  Note: doesn't include the ints themselves")

# Recursive size calculation
def deep_sizeof(obj, seen=None):
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(deep_sizeof(k, seen) + deep_sizeof(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set)):
        size += sum(deep_sizeof(item, seen) for item in obj)
    return size

nested = {'users': [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]}
print(f"\nNested dict getsizeof: {sys.getsizeof(nested)} bytes")
print(f"Nested dict deep_sizeof: {deep_sizeof(nested)} bytes")
```

> 💡 `sys.getsizeof` only counts the container's own memory, not the objects it references. Use a recursive traversal for true memory cost.

## Step 2: `tracemalloc` — Memory Profiling

```python
import tracemalloc
import sys

tracemalloc.start()

# Allocate some objects
data = [list(range(1000)) for _ in range(100)]
strings = ["hello world" * 100 for _ in range(50)]
dicts = [{str(i): i for i in range(100)} for _ in range(20)]

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics("lineno")

print("Top 5 memory allocations:")
for stat in top_stats[:5]:
    print(stat)

current, peak = tracemalloc.get_traced_memory()
print(f"\nCurrent: {current/1024:.1f} KB, Peak: {peak/1024:.1f} KB")
tracemalloc.stop()
```

📸 **Verified Output:**
```
Top 5 memory allocations:
<string>:7: size=3109 KiB, count=74501, average=43 B
<string>:9: size=163 KiB, count=2021, average=83 B
<string>:8: size=816 B, count=2, average=408 B
Current: 3275.2 KB, Peak: 3275.6 KB
```

## Step 3: Snapshot Comparison

```python
import tracemalloc

tracemalloc.start()

snapshot1 = tracemalloc.take_snapshot()

# Do some allocations
cache = {}
for i in range(10000):
    cache[f"key_{i}"] = {"value": i, "data": list(range(10))}

snapshot2 = tracemalloc.take_snapshot()

# Compare snapshots
stats = snapshot2.compare_to(snapshot1, "lineno")
print("Memory growth:")
for stat in stats[:5]:
    print(f"  {stat}")

tracemalloc.stop()
```

## Step 4: `gc` Module — Cyclic Garbage Collector

CPython's reference counting can't handle cycles. The `gc` module handles them:

```python
import gc

# Create a reference cycle
class Node:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None
    
    def __repr__(self):
        return f"Node({self.name!r})"

# Cycle: parent → child → parent
parent = Node("root")
child = Node("child")
parent.children.append(child)
child.parent = parent

# Even after del, cycle keeps both alive
del parent, child

gc.collect()  # Force cycle collection
print(f"GC stats: {gc.get_count()}")  # (gen0, gen1, gen2)

# Find objects tracked by GC
class Tracked:
    pass

t = Tracked()
tracked_objects = gc.get_objects()
tracked_count = sum(1 for obj in tracked_objects if isinstance(obj, Tracked))
print(f"Tracked instances: {tracked_count}")

# GC thresholds (when each generation is collected)
print(f"GC thresholds: {gc.get_threshold()}")  # (700, 10, 10)
```

> 💡 The three-generation GC assumes: objects that survive collection 0 are likely long-lived. Gen 0 is collected frequently, gen 2 rarely.

## Step 5: `gc.get_referrers` — Finding What Holds References

```python
import gc, sys

class ExpensiveResource:
    def __init__(self, name):
        self.name = name

resource = ExpensiveResource("database_connection")

# Find what refers to our object
referrers = gc.get_referrers(resource)
print(f"Referrers of resource ({len(referrers)}):")
for ref in referrers:
    if isinstance(ref, dict):
        print(f"  dict (likely local vars): {list(ref.keys())[:5]}")
    elif isinstance(ref, list):
        print(f"  list with {len(ref)} items")
    else:
        print(f"  {type(ref).__name__}: {ref!r:.50s}")
```

## Step 6: `weakref` — Cache Without Preventing Collection

```python
import weakref
import gc

class HeavyObject:
    def __init__(self, data):
        self.data = data
        print(f"Created HeavyObject({len(data)} items)")
    
    def __del__(self):
        print(f"Destroyed HeavyObject")

# WeakValueDictionary: cache that doesn't prevent GC
cache = weakref.WeakValueDictionary()

def get_heavy_object(key, size=1000):
    obj = cache.get(key)
    if obj is None:
        obj = HeavyObject(list(range(size)))
        cache[key] = obj
        print(f"Cache miss: created {key}")
    else:
        print(f"Cache hit: {key}")
    return obj

# First calls create objects
obj1 = get_heavy_object("dataset_a", 1000)
obj2 = get_heavy_object("dataset_a")  # cache hit

print(f"\nCache size: {len(cache)}")

# Letting go of the reference → GC can collect
del obj1, obj2
gc.collect()

print(f"After del + gc.collect, cache size: {len(cache)}")

# Next call recreates
obj3 = get_heavy_object("dataset_a", 1000)  # cache miss again
```

## Step 7: Memory Leak Detection Pattern

```python
import tracemalloc
import gc
import functools

def detect_memory_leaks(func, iterations=5):
    """Run func multiple times and check if memory grows."""
    tracemalloc.start()
    gc.collect()
    
    measurements = []
    for i in range(iterations):
        func()
        gc.collect()
        snapshot = tracemalloc.take_snapshot()
        stats = snapshot.statistics("filename")
        total = sum(s.size for s in stats)
        measurements.append(total)
        print(f"  Iteration {i+1}: {total/1024:.1f} KB")
    
    tracemalloc.stop()
    
    growth = measurements[-1] - measurements[0]
    print(f"\nMemory growth over {iterations} iterations: {growth/1024:.1f} KB")
    if abs(growth) < 10 * 1024:  # < 10 KB growth
        print("✓ No significant leak detected")
    else:
        print("⚠ Potential memory leak!")
    return measurements

# Good function (no leak)
def well_behaved():
    data = [i ** 2 for i in range(1000)]
    return sum(data)

print("Testing well_behaved function:")
detect_memory_leaks(well_behaved)
```

## Step 8: Capstone — Memory Profiler Decorator

```python
import tracemalloc
import functools
import gc
import sys

class MemoryProfiler:
    """Context manager and decorator for memory profiling."""
    
    def __init__(self, name="operation", top_n=5):
        self.name = name
        self.top_n = top_n
        self.snapshot_before = None
        self.snapshot_after = None
    
    def __enter__(self):
        gc.collect()
        tracemalloc.start()
        self.snapshot_before = tracemalloc.take_snapshot()
        return self
    
    def __exit__(self, *args):
        self.snapshot_after = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        stats = self.snapshot_after.compare_to(self.snapshot_before, "lineno")
        
        net_growth = sum(s.size_diff for s in stats)
        print(f"\n[MemoryProfiler] {self.name}")
        print(f"  Net growth: {net_growth / 1024:.2f} KB")
        print(f"  Peak: {peak / 1024:.2f} KB")
        
        positive_stats = [s for s in stats if s.size_diff > 0][:self.top_n]
        if positive_stats:
            print(f"  Top {self.top_n} allocations:")
            for stat in positive_stats:
                print(f"    {stat}")
    
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with MemoryProfiler(func.__name__, self.top_n):
                return func(*args, **kwargs)
        return wrapper

# As context manager
with MemoryProfiler("data processing"):
    result = {str(i): list(range(100)) for i in range(500)}
    del result

# As decorator
@MemoryProfiler(top_n=3)
def process_data(n):
    return [{"id": i, "data": list(range(50))} for i in range(n)]

rows = process_data(1000)
print(f"\nResult count: {len(rows)}")
```

📸 **Verified Output (tracemalloc):**
```
Top 5 memory allocations:
<string>:7: size=3109 KiB, count=74501, average=43 B
<string>:9: size=163 KiB, count=2021, average=83 B
<string>:8: size=816 B, count=2, average=408 B
Current: 3275.2 KB, Peak: 3275.6 KB
```

## Summary

| Concept | API | Use Case |
|---|---|---|
| Object size | `sys.getsizeof` | Memory estimation |
| Deep size | Custom recursive traversal | True allocation cost |
| Memory profiling | `tracemalloc.start/take_snapshot` | Find memory hogs |
| Snapshot comparison | `snapshot.compare_to` | Detect memory growth |
| Cycle collection | `gc.collect`, `gc.get_count` | Force GC, diagnose cycles |
| Reference tracing | `gc.get_referrers` | Find what keeps objects alive |
| Weak caches | `weakref.WeakValueDictionary` | Cache without preventing GC |
| Leak detection | `tracemalloc` + multiple iterations | CI/CD memory regression tests |
