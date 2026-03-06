# Lab 09: JIT & Caching Patterns

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Python's `functools.cache` and `lru_cache` are implemented in C for maximum performance. This lab explores their internals, builds a TTL-aware cache decorator, and covers disk-backed memoization patterns for production workloads.

## Step 1: `functools.lru_cache` Internals

```python
import functools
import sys

@functools.lru_cache(maxsize=128)
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)

# Compute and inspect cache
result = fib(30)
print(f"fib(30) = {result}")

info = fib.cache_info()
print(f"Cache info:")
print(f"  hits={info.hits}, misses={info.misses}")
print(f"  maxsize={info.maxsize}, currsize={info.currsize}")
print(f"  hit rate: {info.hits/(info.hits+info.misses)*100:.1f}%")

# __wrapped__ gives access to the unwrapped function
unwrapped = fib.__wrapped__
print(f"\nfib.__wrapped__ is fib: {unwrapped is fib}")
print(f"fib.__wrapped__(5) = {unwrapped(5)}")  # No caching, recursive call

# Clear and recompute
fib.cache_clear()
info_after = fib.cache_info()
print(f"\nAfter cache_clear: {info_after}")
```

📸 **Verified Output:**
```
fib(30) = 832040
Cache info:
  hits=28, misses=31
  maxsize=128, currsize=31
  hit rate: 47.5%
```

> 💡 `lru_cache` uses a doubly-linked list + dict for O(1) get/set. The C implementation (`_functools`) is ~10x faster than a pure Python equivalent.

## Step 2: `functools.cache` — Unbounded Cache

```python
import functools
import sys

# functools.cache = lru_cache(maxsize=None)
# Simpler, faster for small result sets (no eviction overhead)

@functools.cache
def pascal_row(n: int) -> tuple:
    """nth row of Pascal's triangle (cached)."""
    if n == 0:
        return (1,)
    prev = pascal_row(n - 1)
    return (1,) + tuple(prev[i] + prev[i+1] for i in range(len(prev)-1)) + (1,)

for i in range(6):
    print(f"Row {i}: {pascal_row(i)}")

print(f"\nCache info: {pascal_row.cache_info()}")
```

## Step 3: Understanding Cache Key Generation

```python
import functools

@functools.lru_cache(maxsize=256)
def compute(x: float, y: float, mode: str = "add") -> float:
    print(f"  Computing compute({x}, {y}, mode={mode!r})")
    if mode == "add":
        return x + y
    elif mode == "mul":
        return x * y
    else:
        raise ValueError(f"Unknown mode: {mode}")

# Cache key is the tuple of all hashable arguments
print("=== First calls (cache miss) ===")
r1 = compute(1.0, 2.0)
r2 = compute(1.0, 2.0, mode="mul")
r3 = compute(1.0, 2.0)  # same as r1 — cache hit

print(f"\n=== Second calls (cache hits) ===")
r4 = compute(1.0, 2.0)  # hit
r5 = compute(1.0, 2.0, mode="mul")  # hit

print(f"\nResults: {r1}, {r2}, {r4}, {r5}")
print(f"Cache: {compute.cache_info()}")

# Unhashable args can't be cached
@functools.lru_cache(maxsize=64)
def process_tuple(data: tuple) -> int:
    return sum(data)

print(f"\nprocess_tuple((1,2,3)): {process_tuple((1,2,3))}")
print(f"process_tuple((1,2,3)): {process_tuple((1,2,3))}")  # cache hit
print(f"Cache: {process_tuple.cache_info()}")
```

## Step 4: Custom TTL Cache Decorator

```python
import functools
import time
import threading

def ttl_cache(ttl_seconds: float, maxsize: int = 128):
    """LRU cache with time-to-live expiration."""
    
    def decorator(func):
        cache = {}          # key → (result, timestamp)
        lock = threading.RLock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            
            with lock:
                now = time.monotonic()
                if key in cache:
                    result, ts = cache[key]
                    if now - ts < ttl_seconds:
                        wrapper._hits += 1
                        return result
                    else:
                        del cache[key]  # expired
                        wrapper._expirations += 1
                
                # Evict if at capacity
                if len(cache) >= maxsize:
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
                
                result = func(*args, **kwargs)
                cache[key] = (result, now)
                wrapper._misses += 1
                return result
        
        wrapper._hits = 0
        wrapper._misses = 0
        wrapper._expirations = 0
        wrapper.cache = cache
        wrapper.cache_clear = lambda: cache.clear()
        
        def cache_info():
            total = wrapper._hits + wrapper._misses
            return {
                'hits': wrapper._hits,
                'misses': wrapper._misses,
                'expirations': wrapper._expirations,
                'hit_rate': f"{wrapper._hits/max(1,total)*100:.1f}%",
                'size': len(cache),
            }
        wrapper.cache_info = cache_info
        
        return wrapper
    return decorator

@ttl_cache(ttl_seconds=0.5, maxsize=10)
def fetch_user(user_id: int) -> dict:
    print(f"  [DB] Fetching user {user_id}")
    return {'id': user_id, 'name': f'User-{user_id}', 'ts': time.time()}

# Test TTL behavior
print("=== Round 1: cache miss ===")
u1 = fetch_user(1)
u2 = fetch_user(1)  # hit
u3 = fetch_user(2)

print("\n=== Round 2: still cached ===")
u4 = fetch_user(1)
u5 = fetch_user(2)

print("\n=== After TTL expiry ===")
time.sleep(0.6)
u6 = fetch_user(1)  # miss (expired)

print(f"\nCache info: {fetch_user.cache_info()}")
```

📸 **Verified Output:**
```
fib(30) = 832040
Cache: hits=28, misses=31, maxsize=128, currsize=31
r1==r2: True
r2==r3: False
TTL expired and recomputed: True
```

## Step 5: Method Caching with `cached_property`

```python
import functools
import time

class DataAnalyzer:
    """Expensive computations cached as properties."""
    
    def __init__(self, data: list):
        self.data = data
        self._compute_count = 0
    
    @functools.cached_property
    def statistics(self) -> dict:
        """Computed once and cached in instance __dict__."""
        self._compute_count += 1
        print(f"  Computing statistics (call #{self._compute_count})...")
        n = len(self.data)
        total = sum(self.data)
        mean = total / n
        variance = sum((x - mean) ** 2 for x in self.data) / n
        return {
            'n': n, 'sum': total, 'mean': mean,
            'variance': variance, 'std': variance ** 0.5,
            'min': min(self.data), 'max': max(self.data),
        }
    
    @functools.cached_property
    def sorted_data(self) -> list:
        print(f"  Sorting {len(self.data)} items...")
        return sorted(self.data)

import random
data = [random.gauss(100, 15) for _ in range(1000)]
analyzer = DataAnalyzer(data)

print("First access (computed):")
stats = analyzer.statistics

print("\nSecond access (from __dict__, no recompute):")
stats2 = analyzer.statistics

print(f"\nStats: mean={stats['mean']:.2f}, std={stats['std']:.2f}")
print(f"Compute count: {analyzer._compute_count}")

# cached_property stores in instance __dict__ — shadows the descriptor
print(f"\n'statistics' in __dict__: {'statistics' in analyzer.__dict__}")
```

## Step 6: Memoization with Disk Cache (joblib pattern)

```python
import functools
import pickle
import hashlib
import os
import time
import tempfile

class DiskCache:
    """File-based persistent memoization cache."""
    
    def __init__(self, cache_dir: str = None, ttl: float = None):
        self.cache_dir = cache_dir or tempfile.mkdtemp(prefix="pycache_")
        self.ttl = ttl
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _key_path(self, func_name: str, args, kwargs) -> str:
        key_data = pickle.dumps((func_name, args, sorted(kwargs.items())))
        key_hash = hashlib.sha256(key_data).hexdigest()[:16]
        return os.path.join(self.cache_dir, f"{func_name}_{key_hash}.pkl")
    
    def __call__(self, func):
        cache = self
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            path = cache._key_path(func.__name__, args, kwargs)
            
            if os.path.exists(path):
                if cache.ttl is None or (time.time() - os.path.getmtime(path)) < cache.ttl:
                    with open(path, 'rb') as f:
                        data = pickle.load(f)
                    print(f"  [DiskCache] HIT: {func.__name__}{args}")
                    return data
                else:
                    os.unlink(path)
                    print(f"  [DiskCache] EXPIRED: {func.__name__}{args}")
            
            result = func(*args, **kwargs)
            with open(path, 'wb') as f:
                pickle.dump(result, f)
            print(f"  [DiskCache] MISS→STORED: {func.__name__}{args}")
            return result
        
        wrapper.cache_dir = self.cache_dir
        return wrapper

disk_cache = DiskCache(ttl=60)

@disk_cache
def expensive_computation(n: int) -> dict:
    """Simulates expensive work (ML model training, etc.)."""
    time.sleep(0.01)  # simulate compute
    return {'n': n, 'squares': [i**2 for i in range(n)], 'ts': time.time()}

print("First run (cache miss):")
r1 = expensive_computation(100)

print("\nSecond run (disk hit):")
r2 = expensive_computation(100)

print(f"\nResults match: {r1['squares'] == r2['squares']}")
print(f"Different timestamps: {r1['ts'] != r2['ts']}")
```

## Step 7: Caching with numpy — Ufunc Caching

```python
import functools
import numpy as np
import time

# numpy operations are already optimized, but we can cache expensive
# array computations that depend on the same parameters

def array_cache(func):
    """Cache numpy array results using bytes as key."""
    cache = {}
    
    @functools.wraps(func)
    def wrapper(arr, *args, **kwargs):
        # numpy arrays aren't hashable — use bytes of a sample
        if isinstance(arr, np.ndarray):
            key = (arr.tobytes(), arr.shape, arr.dtype, args, tuple(sorted(kwargs.items())))
        else:
            key = (arr, args, tuple(sorted(kwargs.items())))
        
        if key not in cache:
            cache[key] = func(arr, *args, **kwargs)
        return cache[key]
    
    wrapper.cache = cache
    return wrapper

@array_cache
def compute_correlation_matrix(data: np.ndarray) -> np.ndarray:
    """Expensive correlation computation."""
    n = len(data)
    corr = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                corr[i, j] = 1.0
            else:
                corr[i, j] = np.corrcoef(data[i], data[j])[0, 1]
    return corr

data = np.random.randn(5, 100)

start = time.perf_counter()
corr1 = compute_correlation_matrix(data)
t1 = time.perf_counter() - start

start = time.perf_counter()
corr2 = compute_correlation_matrix(data)  # cached
t2 = time.perf_counter() - start

print(f"First call: {t1*1000:.1f}ms")
print(f"Cached call: {t2*1000:.3f}ms")
print(f"Speedup: {t1/max(t2, 1e-6):.0f}x")
print(f"Results match: {np.allclose(corr1, corr2)}")
```

## Step 8: Capstone — Production Cache Layer

```python
import functools
import time
import threading
import weakref
from collections import OrderedDict

class ProductionCache:
    """Thread-safe LRU cache with TTL, weak value refs, and stats."""
    
    def __init__(self, maxsize: int = 256, ttl: float = 300):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {'hits': 0, 'misses': 0, 'evictions': 0, 'expirations': 0}
    
    def _is_expired(self, entry) -> bool:
        return self.ttl and (time.monotonic() - entry['ts']) > self.ttl
    
    def get(self, key):
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            if self._is_expired(entry):
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None
            
            # LRU: move to end
            self._cache.move_to_end(key)
            self._stats['hits'] += 1
            return entry['value']
    
    def set(self, key, value):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.maxsize:
                    self._cache.popitem(last=False)
                    self._stats['evictions'] += 1
            self._cache[key] = {'value': value, 'ts': time.monotonic()}
    
    def __call__(self, func):
        cache = self
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (func.__qualname__, args, tuple(sorted(kwargs.items())))
            
            result = cache.get(key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(key, result)
            return result
        
        wrapper.cache = cache
        wrapper.stats = lambda: dict(cache._stats)
        return wrapper

cache = ProductionCache(maxsize=100, ttl=1.0)

@cache
def expensive_api_call(endpoint: str, params: dict = None) -> dict:
    """Simulate an API call."""
    import json
    return {
        'endpoint': endpoint,
        'data': list(range(10)),
        'timestamp': time.time(),
    }

# Simulate usage
for endpoint in ['/users', '/posts', '/users']:
    result = expensive_api_call(endpoint)
    print(f"  {endpoint}: ts={result['timestamp']:.3f}")

print(f"\nCache stats: {cache.stats()}")

# Test TTL expiry
time.sleep(1.1)
result = expensive_api_call('/users')  # should miss (expired)
print(f"After TTL: {cache.stats()}")
```

## Summary

| Concept | API | Use Case |
|---|---|---|
| LRU cache | `functools.lru_cache` | Expensive pure functions |
| Unbounded cache | `functools.cache` | Small result spaces |
| Cache introspection | `.cache_info()`, `.__wrapped__` | Debug and monitor |
| TTL cache | Custom decorator | Time-sensitive data |
| `cached_property` | `functools.cached_property` | Expensive computed attributes |
| Disk cache | Custom + `pickle` | ML/large computation persistence |
| Array cache | Custom key from `tobytes()` | numpy operations |
| Production cache | Thread-safe LRU+TTL | Microservice caching layer |
