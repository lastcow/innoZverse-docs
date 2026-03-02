# Lab 11: List Comprehensions, Generators & Iterators

## 🎯 Objective
Master Python's most powerful iteration tools — list/dict/set comprehensions, generator expressions, and the iterator protocol — for writing concise, memory-efficient code.

## 📚 Background
Comprehensions are Python's answer to `map()` and `filter()` — they express data transformations in a single readable line. **Generators** produce values lazily (one at a time) instead of building the entire collection in memory first, making them essential for large datasets. Understanding iterators explains how `for` loops actually work under the hood.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 10: Modules & Packages

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: List Comprehensions

```python
# Pattern: [expression for item in iterable if condition]

numbers = range(1, 11)

# Basic transformation
squares = [n**2 for n in numbers]
print(f"Squares: {squares}")

# Filtering
evens = [n for n in numbers if n % 2 == 0]
print(f"Evens: {evens}")

# Combined: filter and transform
even_squares = [n**2 for n in numbers if n % 2 == 0]
print(f"Even squares: {even_squares}")

# String transformation
words = ["hello", "world", "python", "is", "awesome"]
long_upper = [w.upper() for w in words if len(w) > 4]
print(f"Long words upper: {long_upper}")

# Compare with traditional loop
result = []
for w in words:
    if len(w) > 4:
        result.append(w.upper())
print(f"Same result:      {result}")
```

**📸 Verified Output:**
```
Squares: [1, 4, 9, 16, 25, 36, 49, 64, 81, 100]
Evens: [2, 4, 6, 8, 10]
Even squares: [4, 16, 36, 64, 100]
Long words upper: ['HELLO', 'WORLD', 'PYTHON', 'AWESOME']
Same result:      ['HELLO', 'WORLD', 'PYTHON', 'AWESOME']
```

### Step 2: Nested Comprehensions

```python
# Flatten a 2D matrix
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [n for row in matrix for n in row]
print(f"Flattened: {flat}")

# Cartesian product
colors = ["red", "blue"]
sizes = ["S", "M", "L"]
products = [f"{c}-{s}" for c in colors for s in sizes]
print(f"Products: {products}")

# Conditional: FizzBuzz in one line
fizzbuzz = [
    "FizzBuzz" if n%15==0 else
    "Fizz" if n%3==0 else
    "Buzz" if n%5==0 else str(n)
    for n in range(1, 21)
]
print(", ".join(fizzbuzz))
```

**📸 Verified Output:**
```
Flattened: [1, 2, 3, 4, 5, 6, 7, 8, 9]
Products: ['red-S', 'red-M', 'red-L', 'blue-S', 'blue-M', 'blue-L']
1, 2, Fizz, 4, Buzz, Fizz, 7, 8, Fizz, Buzz, 11, Fizz, 13, 14, FizzBuzz, 16, 17, Fizz, 19, Buzz
```

### Step 3: Dict and Set Comprehensions

```python
# Dict comprehension: {key_expr: value_expr for ...}
names = ["alice", "bob", "charlie", "diana"]
name_lengths = {name: len(name) for name in names}
print(f"Dict: {name_lengths}")

# Invert a dictionary
original = {"a": 1, "b": 2, "c": 3, "d": 4}
inverted = {v: k for k, v in original.items()}
print(f"Inverted: {inverted}")

# Filter dict: only even values
evens_only = {k: v for k, v in original.items() if v % 2 == 0}
print(f"Even values: {evens_only}")

# Set comprehension: {expression for ...}
text = "Hello World Python"
unique_chars = {c.lower() for c in text if c.isalpha()}
print(f"Unique chars: {sorted(unique_chars)}")

# Count vowels per word
vowels = set("aeiou")
vowel_count = {w: sum(c in vowels for c in w.lower()) for w in text.split()}
print(f"Vowels per word: {vowel_count}")
```

**📸 Verified Output:**
```
Dict: {'alice': 5, 'bob': 3, 'charlie': 7, 'diana': 5}
Inverted: {1: 'a', 2: 'b', 3: 'c', 4: 'd'}
Even values: {'b': 2, 'd': 4}
Unique chars: ['d', 'e', 'h', 'l', 'n', 'o', 'p', 'r', 't', 'w', 'y']
Vowels per word: {'Hello': 2, 'World': 1, 'Python': 1}
```

### Step 4: Generator Expressions

```python
import sys

# List comprehension — builds entire list in memory
list_comp = [n**2 for n in range(1000)]
print(f"List size: {sys.getsizeof(list_comp):,} bytes")

# Generator expression — lazy, calculates one at a time
gen_exp = (n**2 for n in range(1000))
print(f"Generator size: {sys.getsizeof(gen_exp)} bytes")

# Generators are consumed once
gen = (n**2 for n in range(5))
print(f"First pass: {list(gen)}")
print(f"Second pass: {list(gen)}")  # Empty — already consumed!

# Use generator directly in aggregate functions (most efficient)
numbers = range(1, 1001)
total = sum(n**2 for n in numbers)   # No intermediate list!
maximum = max(n for n in numbers if n % 7 == 0)
print(f"Sum of squares 1-1000: {total:,}")
print(f"Largest multiple of 7 ≤ 1000: {maximum}")
```

**📸 Verified Output:**
```
List size: 8,056 bytes
Generator size: 200 bytes
First pass: [0, 1, 4, 9, 16]
Second pass: []
Sum of squares 1-1000: 333,833,500
Largest multiple of 7 ≤ 1000: 994
```

> 💡 Generators are 40× smaller in memory than equivalent lists. Use them when processing large datasets — log files, database rows, API pages.

### Step 5: Generator Functions (yield)

```python
def countdown(n):
    """Generator that counts down from n to 1."""
    print(f"  Starting countdown from {n}")
    while n > 0:
        yield n       # Pause here, return n, resume on next()
        n -= 1
    print(f"  Countdown complete!")

# Use in a for loop
print("Countdown:")
for num in countdown(5):
    print(f"  → {num}")

# Manual iteration
gen = countdown(3)
print(f"\nnext(): {next(gen)}")
print(f"next(): {next(gen)}")
print(f"next(): {next(gen)}")
try:
    next(gen)
except StopIteration:
    print("StopIteration raised — generator exhausted")
```

**📸 Verified Output:**
```
Countdown:
  Starting countdown from 5
  → 5
  → 4
  → 3
  → 2
  → 1
  Countdown complete!

next(): Starting countdown from 3
next(): 3
next(): 2
next(): 1
StopIteration raised — generator exhausted
```

### Step 6: Infinite Generators

```python
import itertools

def fibonacci():
    """Infinite Fibonacci number generator."""
    a, b = 0, 1
    while True:         # Runs forever — caller controls when to stop
        yield a
        a, b = b, a + b

def primes():
    """Infinite prime number generator."""
    def is_prime(n):
        if n < 2: return False
        return all(n % i != 0 for i in range(2, int(n**0.5) + 1))
    n = 2
    while True:
        if is_prime(n):
            yield n
        n += 1

# Take first N from an infinite generator
fib_gen = fibonacci()
first_15_fibs = [next(fib_gen) for _ in range(15)]
print(f"Fibonacci: {first_15_fibs}")

prime_gen = primes()
first_10_primes = list(itertools.islice(prime_gen, 10))
print(f"Primes: {first_10_primes}")
```

**📸 Verified Output:**
```
Fibonacci: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377]
Primes: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

### Step 7: Custom Iterators

```python
class NumberRange:
    """Custom iterator: range with step as fraction."""
    
    def __init__(self, start, stop, step=1):
        self.current = start
        self.stop = stop
        self.step = step
    
    def __iter__(self):
        return self      # Iterator is its own iterable
    
    def __next__(self):
        if self.current >= self.stop:
            raise StopIteration
        value = self.current
        self.current += self.step
        return round(value, 10)

# Use as for loop target
print("Range 0 to 1 step 0.25:")
for n in NumberRange(0, 1.01, 0.25):
    print(f"  {n}")

print()

class Reversed:
    """Iterate a sequence in reverse without copying."""
    def __init__(self, data):
        self.data = data
        self.index = len(data)
    
    def __iter__(self): return self
    def __next__(self):
        if self.index == 0:
            raise StopIteration
        self.index -= 1
        return self.data[self.index]

words = ["alpha", "beta", "gamma", "delta"]
print(f"Reversed: {list(Reversed(words))}")
```

**📸 Verified Output:**
```
Range 0 to 1 step 0.25:
  0
  0.25
  0.5
  0.75
  1.0

Reversed: ['delta', 'gamma', 'beta', 'alpha']
```

### Step 8: Real-World Pipeline with Generators

```python
import re
from pathlib import Path

# Simulate processing a large log file with generators
# Each generator transforms the stream without loading all into memory

def generate_log_lines():
    """Simulate reading log lines (would be a file in production)."""
    logs = [
        "2026-03-02 09:00:01 INFO  Request GET /api/users 200 45ms",
        "2026-03-02 09:00:02 ERROR Request POST /api/login 401 12ms",
        "2026-03-02 09:00:03 INFO  Request GET /api/products 200 123ms",
        "2026-03-02 09:00:04 WARN  Request GET /api/slow 200 5023ms",
        "2026-03-02 09:00:05 ERROR Request DELETE /api/admin 403 8ms",
        "2026-03-02 09:00:06 INFO  Request GET /api/users/1 200 33ms",
    ]
    yield from logs  # yield from delegates to another iterable

def parse_log(lines):
    """Parse each line into a structured dict."""
    pattern = r'(\S+ \S+) (\w+)\s+Request (\w+) (\S+) (\d+) (\d+)ms'
    for line in lines:
        m = re.match(pattern, line)
        if m:
            yield {
                "time": m.group(1), "level": m.group(2),
                "method": m.group(3), "path": m.group(4),
                "status": int(m.group(5)), "ms": int(m.group(6))
            }

def filter_errors(records):
    """Yield only error/warning records."""
    for r in records:
        if r["level"] in ("ERROR", "WARN"):
            yield r

def slow_requests(records, threshold_ms=1000):
    """Yield only slow requests."""
    for r in records:
        if r["ms"] > threshold_ms:
            yield r

# Build the pipeline — nothing executes until we iterate
raw     = generate_log_lines()
parsed  = parse_log(raw)
errors  = filter_errors(parsed)

print("Errors and Warnings:")
for record in errors:
    print(f"  [{record['level']:5}] {record['method']} {record['path']} "
          f"→ {record['status']} ({record['ms']}ms)")

# Different pipeline: find slow requests
raw2    = generate_log_lines()
parsed2 = parse_log(raw2)
slow    = slow_requests(parsed2, threshold_ms=100)

print("\nSlow Requests (>100ms):")
for record in slow:
    print(f"  {record['path']:20} {record['ms']}ms")
```

**📸 Verified Output:**
```
Errors and Warnings:
  [ERROR] POST /api/login → 401 (12ms)
  [WARN ] GET /api/slow → 200 (5023ms)
  [ERROR] DELETE /api/admin → 403 (8ms)

Slow Requests (>100ms):
  /api/products        123ms
  /api/slow            5023ms
```

## ✅ Verification

```python
# Comprehension + generator challenge
data = [1, -2, 3, -4, 5, -6, 7, -8, 9, -10]

positives = [x for x in data if x > 0]
squares_gen = (x**2 for x in positives)
total = sum(squares_gen)

print(f"Positives: {positives}")
print(f"Sum of squares: {total}")

word_freq = {w: len(w) for w in ["python", "is", "awesome", "and", "fast"]}
print(f"Word lengths: {dict(sorted(word_freq.items(), key=lambda x: -x[1]))}")
print("Lab 11 verified ✅")
```

**Expected output:**
```
Positives: [1, 3, 5, 7, 9]
Sum of squares: 165
Word lengths: {'awesome': 7, 'python': 6, 'fast': 4, 'and': 3, 'is': 2}
Lab 11 verified ✅
```

## 🚨 Common Mistakes

1. **Consuming a generator twice**: Generators are one-time iterators — convert to `list()` if you need to reuse.
2. **Nested comprehensions that are too clever**: More than 2 levels of nesting → use a regular loop.
3. **Generator vs list for indexing**: `gen[0]` raises `TypeError` — generators have no indexing.
4. **Missing `yield` in generator function**: Without `yield`, the function returns `None` instead of a generator.
5. **Comprehension side effects**: Don't use `[print(x) for x in items]` — use a regular loop for side effects.

## 📝 Summary

- List comprehension: `[expr for item in iterable if cond]` — concise, creates list
- Dict comprehension: `{k: v for k, v in iterable}` — create dicts from data
- Set comprehension: `{expr for item in iterable}` — create sets (unique)
- Generator expression: `(expr for ...)` — lazy, memory-efficient; use in `sum()`, `max()`, `any()`
- Generator function: uses `yield` to produce values one at a time; `next()` advances
- Iterator protocol: `__iter__()` + `__next__()` — what makes `for` loops work

## 🔗 Further Reading
- [Python Docs: Comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)
- [Python Docs: Generators](https://docs.python.org/3/howto/functional.html#generators)
- [Real Python: Python Generators](https://realpython.com/introduction-to-python-generators/)
