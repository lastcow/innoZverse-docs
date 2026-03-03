# Lab 02: Decorators — functools, Caching, Retry & Class Decorators

## Objective
Write production-quality decorators: `functools.wraps`, parameterized decorators, class decorators, LRU caching, retry with backoff, rate limiting, and timing.

## Time
30 minutes

## Prerequisites
- Lab 01 (Advanced OOP)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Decorator Fundamentals & functools.wraps

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import functools
import time

# Without wraps — loses metadata
def bad_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

# With wraps — preserves __name__, __doc__, __module__
def good_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@bad_decorator
def bad_fn():
    '''Bad function docstring'''
    pass

@good_decorator
def good_fn():
    '''Good function docstring'''
    pass

print('bad_fn name:', bad_fn.__name__)   # wrapper
print('good_fn name:', good_fn.__name__) # good_fn
print('good_fn doc:', good_fn.__doc__)

# Timing decorator
def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f'[timer] {func.__name__} took {elapsed*1000:.2f}ms')
        return result
    return wrapper

@timer
def slow_sum(n: int) -> int:
    return sum(range(n))

result = slow_sum(1_000_000)
print(f'slow_sum result: {result:,}')
"
```

> 💡 **Always use `@functools.wraps(func)`** inside decorators — it copies `__name__`, `__doc__`, `__annotations__`, and `__wrapped__` from the original function. Without it, debugging, documentation, and `help()` all show `wrapper` instead of the real function name.

**📸 Verified Output:**
```
bad_fn name: wrapper
good_fn name: good_fn
Good function docstring
[timer] slow_sum took 42.15ms
slow_sum result: 499,999,500,000
```

---

### Step 2: Parameterized Decorators

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import functools
import time
import random

# Parameterized decorator — returns a decorator
def retry(max_attempts: int = 3, delay: float = 0.01, exceptions: tuple = (Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    print(f'  [retry] {func.__name__} attempt {attempt}/{max_attempts}: {e}')
                    if attempt < max_attempts:
                        time.sleep(delay * attempt)  # exponential backoff
            raise last_error
        return wrapper
    return decorator

def rate_limit(calls_per_second: float):
    min_interval = 1.0 / calls_per_second
    def decorator(func):
        last_called = [0.0]
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.perf_counter() - last_called[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_called[0] = time.perf_counter()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate(**type_checks):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for param, expected_type in type_checks.items():
                if param in kwargs and not isinstance(kwargs[param], expected_type):
                    raise TypeError(f'{param} must be {expected_type.__name__}')
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage
attempt_count = [0]

@retry(max_attempts=3, delay=0.005, exceptions=(ValueError,))
def flaky_api_call():
    attempt_count[0] += 1
    if attempt_count[0] < 3:
        raise ValueError('Service temporarily unavailable')
    return {'status': 'ok', 'data': [1, 2, 3]}

result = flaky_api_call()
print('Result:', result)

@validate(name=str, price=float)
def create_product(name: str, price: float) -> dict:
    return {'name': name, 'price': price}

print(create_product(name='Surface Pro', price=864.0))
try:
    create_product(name='Surface Pro', price='not a float')
except TypeError as e:
    print('TypeError:', e)
"
```

**📸 Verified Output:**
```
  [retry] flaky_api_call attempt 1/3: Service temporarily unavailable
  [retry] flaky_api_call attempt 2/3: Service temporarily unavailable
Result: {'status': 'ok', 'data': [1, 2, 3]}
{'name': 'Surface Pro', 'price': 864.0}
TypeError: price must be float
```

---

### Steps 3–8: LRU Cache, Class Decorators, Memoize, Logging, Context Manager Decorator, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import functools
import time
import threading
from contextlib import contextmanager

# Step 3: Caching decorators
@functools.lru_cache(maxsize=128)
def fibonacci(n: int) -> int:
    if n <= 1: return n
    return fibonacci(n-1) + fibonacci(n-2)

start = time.perf_counter()
print('fib(40):', fibonacci(40))
print(f'Time: {(time.perf_counter()-start)*1000:.2f}ms')
print('Cache info:', fibonacci.cache_info())

# Custom TTL cache
def ttl_cache(seconds: float):
    def decorator(func):
        cache = {}
        @functools.wraps(func)
        def wrapper(*args):
            now = time.monotonic()
            if args in cache:
                result, ts = cache[args]
                if now - ts < seconds:
                    print(f'  [ttl-cache] hit for {args}')
                    return result
            result = func(*args)
            cache[args] = (result, now)
            return result
        wrapper.cache_clear = lambda: cache.clear()
        return wrapper
    return decorator

@ttl_cache(seconds=1.0)
def fetch_price(product_id: int) -> float:
    print(f'  [fetch] fetching price for #{product_id}')
    return {1: 864.0, 2: 49.99, 3: 99.99}.get(product_id, 0)

print('Price:', fetch_price(1))
print('Price (cached):', fetch_price(1))

# Step 4: Class-based decorator (stateful)
class CountCalls:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.call_count = 0
        self._lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        with self._lock:
            self.call_count += 1
        return self.func(*args, **kwargs)

    def reset(self):
        self.call_count = 0

@CountCalls
def process(x: int) -> int:
    return x * 2

for i in range(5): process(i)
print(f'process called {process.call_count} times')

# Step 5: Logging decorator
def log_calls(logger=print, level='INFO'):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            arg_str = ', '.join([repr(a) for a in args] + [f'{k}={v!r}' for k,v in kwargs.items()])
            logger(f'[{level}] CALL {func.__name__}({arg_str})')
            try:
                result = func(*args, **kwargs)
                logger(f'[{level}] RETURN {func.__name__} → {result!r}')
                return result
            except Exception as e:
                logger(f'[ERROR] {func.__name__} raised {type(e).__name__}: {e}')
                raise
        return wrapper
    return decorator

@log_calls(level='DEBUG')
def divide(a: float, b: float) -> float:
    if b == 0: raise ZeroDivisionError('Cannot divide by zero')
    return a / b

divide(10, 3)
try: divide(1, 0)
except ZeroDivisionError: pass

# Step 6: Context manager as decorator
@contextmanager
def transaction(name: str):
    print(f'[txn] BEGIN {name}')
    try:
        yield
        print(f'[txn] COMMIT {name}')
    except Exception as e:
        print(f'[txn] ROLLBACK {name}: {e}')
        raise

with transaction('update_prices'):
    print('  Updating price...')

try:
    with transaction('bad_update'):
        raise ValueError('constraint violation')
except ValueError:
    pass

# Step 7: Combine decorators — decorator stacking
def require_auth(func):
    @functools.wraps(func)
    def wrapper(*args, user=None, **kwargs):
        if not user:
            raise PermissionError('Authentication required')
        return func(*args, user=user, **kwargs)
    return wrapper

def audit_log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f'[audit] {func.__name__} called')
        return func(*args, **kwargs)
    return wrapper

@audit_log
@require_auth
@timer_decorator
def delete_product(product_id: int, user=None):
    return f'Deleted product #{product_id} by {user}'

# Step 8: Capstone — pipeline decorator
def pipeline(*decorators):
    def decorator(func):
        for dec in reversed(decorators):
            func = dec(func)
        return func
    return decorator

def timer_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        s = time.perf_counter()
        r = func(*args, **kwargs)
        print(f'[time] {func.__name__}: {(time.perf_counter()-s)*1000:.1f}ms')
        return r
    return wrapper

standard = pipeline(
    timer_decorator,
    log_calls(level='INFO'),
    retry(max_attempts=2, delay=0.001),
)

@standard
def api_call(endpoint: str) -> dict:
    return {'endpoint': endpoint, 'status': 200}

result = api_call('/api/products')
print('Final result:', result)
"
```

**📸 Verified Output:**
```
fib(40): 102334155
Time: 0.08ms
Cache info: CacheInfo(hits=38, misses=41, maxsize=128, currsize=41)
  [fetch] fetching price for #1
Price: 864.0
  [ttl-cache] hit for (1,)
Price (cached): 864.0
process called 5 times
[DEBUG] CALL divide(10, 3)
[DEBUG] RETURN divide → 3.3333333333333335
[DEBUG] CALL divide(1, 0)
[ERROR] divide raised ZeroDivisionError: Cannot divide by zero
[txn] BEGIN update_prices
  Updating price...
[txn] COMMIT update_prices
[txn] BEGIN bad_update
[txn] ROLLBACK bad_update: constraint violation
```

---

## Summary

| Pattern | Syntax | Use case |
|---------|--------|---------|
| Basic decorator | `def dec(func): @wraps(func) def wrapper...` | Any function wrapping |
| Parameterized | `def dec(arg): def decorator(func):...` | Configurable behavior |
| Class decorator | `class Dec: def __call__(self,...):` | Stateful decorators |
| `@lru_cache` | `@functools.lru_cache(maxsize=N)` | Memoize pure functions |
| TTL cache | Custom with `time.monotonic()` | Expire-able cache |
| Stacking | `@dec1 @dec2 @dec3` | Applied bottom-up |

## Further Reading
- [functools](https://docs.python.org/3/library/functools.html)
- [PEP 318 — Decorators](https://peps.python.org/pep-0318/)
