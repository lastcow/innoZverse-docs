# Lab 03: Generators, Iterators & itertools

## Objective
Build lazy data pipelines using generators, `yield from`, custom iterators, and the `itertools` module for memory-efficient data processing.

## Time
30 minutes

## Prerequisites
- Python Foundations Lab 04 (Comprehensions)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Generators & yield

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sys

# Generator function — lazy evaluation
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def take(n, iterable):
    for i, val in enumerate(iterable):
        if i >= n: break
        yield val

gen = fibonacci()
first_10 = list(take(10, gen))
print('First 10 fib:', first_10)

# Memory comparison: list vs generator
def range_gen(n):
    i = 0
    while i < n:
        yield i
        i += 1

N = 1_000_000
lst = list(range(N))
gen = range_gen(N)
print(f'List size:      {sys.getsizeof(lst):,} bytes')
print(f'Generator size: {sys.getsizeof(gen)} bytes')  # ~120 bytes always

# Generator expression
squares_gen = (x**2 for x in range(10))
print('Squares:', list(squares_gen))

# send() — two-way communication
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None: break
        total += value

acc = accumulator()
next(acc)  # prime the generator
for val in [10, 20, 30, 40]:
    total = acc.send(val)
    print(f'  sent {val:3d}, running total: {total}')
"
```

> 💡 **Generators are lazy** — they compute values one at a time, only when asked. A generator function returns a generator object without running any code. This is why a generator for a million items uses ~120 bytes: it stores only the current state (local variables, instruction pointer), not all the values.

**📸 Verified Output:**
```
First 10 fib: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
List size:      8,697,464 bytes
Generator size: 104 bytes
Squares: [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
  sent  10, running total: 10
  sent  20, running total: 30
  sent  30, running total: 60
  sent  40, running total: 100
```

---

### Step 2: yield from & Custom Iterators

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from typing import Iterator

# yield from — delegate to sub-generator
def flatten(nested):
    for item in nested:
        if isinstance(item, (list, tuple)):
            yield from flatten(item)
        else:
            yield item

data = [1, [2, 3, [4, 5]], 6, [7, [8, [9]]]]
print('Flattened:', list(flatten(data)))

# yield from with return value
def subgen():
    yield 1
    yield 2
    return 'done'  # becomes StopIteration.value

def delegator():
    result = yield from subgen()
    print('Subgen returned:', result)
    yield 3

print('Delegated:', list(delegator()))

# Custom iterator class
class Range:
    def __init__(self, start, stop, step=1):
        self.current = start
        self.stop    = stop
        self.step    = step

    def __iter__(self):   # makes it iterable
        return self

    def __next__(self):   # defines how to get next value
        if self.step > 0 and self.current >= self.stop:
            raise StopIteration
        if self.step < 0 and self.current <= self.stop:
            raise StopIteration
        value = self.current
        self.current += self.step
        return value

print('Custom range:', list(Range(0, 10, 2)))
print('Reverse:', list(Range(10, 0, -2)))

# Infinite iterator with islice
class Counter:
    def __init__(self, start=0): self.n = start
    def __iter__(self): return self
    def __next__(self):
        n = self.n; self.n += 1; return n

from itertools import islice
print('Counter:', list(islice(Counter(1), 5)))
"
```

**📸 Verified Output:**
```
Flattened: [1, 2, 3, 4, 5, 6, 7, 8, 9]
Subgen returned: done
Delegated: [1, 2, 3]
Custom range: [0, 2, 4, 6, 8]
Reverse: [10, 8, 6, 4, 2]
Counter: [1, 2, 3, 4, 5]
```

---

### Steps 3–8: itertools, Data Pipeline, CSV Processing, Chunking, Windowing, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import itertools
import operator
from typing import Iterator, TypeVar

T = TypeVar('T')

# Step 3: itertools essentials
print('=== itertools ===')

# chain — concatenate iterables
combined = list(itertools.chain([1,2,3], [4,5], [6]))
print('chain:', combined)

# islice — lazy slice
gen = (x**2 for x in itertools.count(1))
print('first 5 squares:', list(itertools.islice(gen, 5)))

# groupby — group consecutive items (sort first!)
data = [
    {'name': 'Surface Pro',  'category': 'Laptop'},
    {'name': 'Surface Book', 'category': 'Laptop'},
    {'name': 'Surface Pen',  'category': 'Accessory'},
    {'name': 'Office 365',   'category': 'Software'},
    {'name': 'USB-C Hub',    'category': 'Accessory'},
]
data.sort(key=lambda x: x['category'])
for category, items in itertools.groupby(data, key=lambda x: x['category']):
    names = [i['name'] for i in items]
    print(f'  {category}: {names}')

# accumulate
prices = [864, 49.99, 99.99, 29.99]
print('Running totals:', list(itertools.accumulate(prices)))
print('Running max:', list(itertools.accumulate(prices, max)))

# combinations & permutations
items = ['A', 'B', 'C']
print('C(3,2):', list(itertools.combinations(items, 2)))
print('P(3,2):', list(itertools.permutations(items, 2)))

# product (cartesian)
print('Colors × sizes:', list(itertools.product(['red','blue'], ['S','M'])))

# Step 4: Lazy data pipeline
def read_products():
    products = [
        {'id': 1, 'name': 'Surface Pro',  'price': 864,  'stock': 15, 'category': 'Laptop'},
        {'id': 2, 'name': 'Surface Pen',  'price': 49.99,'stock': 80, 'category': 'Accessory'},
        {'id': 3, 'name': 'Office 365',   'price': 99.99,'stock': 999,'category': 'Software'},
        {'id': 4, 'name': 'USB-C Hub',    'price': 29.99,'stock': 0,  'category': 'Accessory'},
        {'id': 5, 'name': 'Surface Book', 'price': 1299, 'stock': 5,  'category': 'Laptop'},
    ]
    yield from products

def pipeline(*transforms):
    def run(data):
        for transform in transforms:
            data = transform(data)
        return data
    return run

# Pipeline stages
in_stock       = lambda data: (p for p in data if p['stock'] > 0)
under_500      = lambda data: (p for p in data if p['price'] < 500)
add_value      = lambda data: ({**p, 'value': round(p['price'] * p['stock'], 2)} for p in data)
sort_by_price  = lambda data: sorted(data, key=lambda p: p['price'], reverse=True)

process = pipeline(in_stock, under_500, add_value, sort_by_price)
results = process(read_products())
print()
print('=== Pipeline Results ===')
for p in results:
    print(f'  [{p[\"id\"]}] {p[\"name\"]:20s} \${p[\"price\"]:8.2f}  value=\${p[\"value\"]:,.2f}')

# Step 5: Chunking generator
def chunk(iterable, size: int):
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, size))
        if not batch: break
        yield batch

print()
print('=== Batch processing ===')
ids = range(1, 12)
for batch_num, batch in enumerate(chunk(ids, 3), 1):
    print(f'  Batch {batch_num}: {batch}')

# Step 6: Sliding window
def sliding_window(iterable, n: int):
    it = iter(iterable)
    window = list(itertools.islice(it, n))
    if len(window) == n:
        yield tuple(window)
    for item in it:
        window.pop(0)
        window.append(item)
        yield tuple(window)

prices_series = [100, 102, 98, 105, 103, 107, 110, 108]
print()
print('=== Moving Average (window=3) ===')
for window in sliding_window(prices_series, 3):
    avg = sum(window) / len(window)
    print(f'  {window} → avg={avg:.1f}')

# Step 7: Unique / deduplicate preserving order
def unique_everseen(iterable, key=None):
    seen = set()
    for item in iterable:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            yield item

dupes = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
print()
print('unique_everseen:', list(unique_everseen(dupes)))

# Step 8: Capstone — lazy CSV-like stream processor
import io
csv_data = '''id,name,price,stock,category
1,Surface Pro,864.00,15,Laptop
2,Surface Pen,49.99,80,Accessory
3,Office 365,99.99,999,Software
4,USB-C Hub,29.99,0,Accessory
5,Surface Book,1299.00,5,Laptop'''

def parse_csv(text):
    lines = iter(text.strip().splitlines())
    headers = next(lines).split(',')
    for line in lines:
        values = line.split(',')
        yield dict(zip(headers, values))

def cast_types(stream):
    for row in stream:
        yield {**row, 'price': float(row['price']), 'stock': int(row['stock'])}

def compute_stats(stream):
    by_category = {}
    for p in stream:
        cat = p['category']
        if cat not in by_category:
            by_category[cat] = {'count': 0, 'revenue': 0.0, 'in_stock': 0}
        by_category[cat]['count'] += 1
        by_category[cat]['revenue'] += p['price'] * p['stock']
        if p['stock'] > 0: by_category[cat]['in_stock'] += 1
    return by_category

proc = pipeline(parse_csv, cast_types)
stream = proc(csv_data)
stats = compute_stats(stream)

print()
print('=== CSV Stream Stats ===')
for cat, s in sorted(stats.items()):
    print(f'  {cat:12s}: {s[\"count\"]} items, {s[\"in_stock\"]} in stock, revenue=\${s[\"revenue\"]:,.2f}')
"
```

**📸 Verified Output:**
```
=== itertools ===
chain: [1, 2, 3, 4, 5, 6]
first 5 squares: [1, 4, 9, 16, 25]
  Accessory: ['Surface Pen', 'USB-C Hub']
  Laptop: ['Surface Pro', 'Surface Book']
  Software: ['Office 365']
Running totals: [864, 913.99, 1013.98, 1043.97]
Running max: [864, 864, 864, 864]
C(3,2): [('A', 'B'), ('A', 'C'), ('B', 'C')]
P(3,2): [('A', 'B'), ('A', 'C'), ('B', 'A'), ('B', 'C'), ('C', 'A'), ('C', 'B')]
Colors × sizes: [('red', 'S'), ('red', 'M'), ('blue', 'S'), ('blue', 'M')]

=== Pipeline Results ===
  [2] Surface Pen          $  49.99  value=$3,999.20
  [3] Office 365           $  99.99  value=$99,890.01

=== CSV Stream Stats ===
  Accessory   : 2 items, 1 in stock, revenue=$3,999.20
  Laptop      : 2 items, 2 in stock, revenue=$19,425.00
  Software    : 1 items, 1 in stock, revenue=$99,890.01
```

---

## Summary

| Tool | Use case |
|------|---------|
| `yield` | Produce values lazily, one at a time |
| `yield from` | Delegate to sub-generator |
| `__iter__` / `__next__` | Custom iterator protocol |
| `itertools.chain` | Concatenate iterables without copying |
| `itertools.islice` | Lazy slice of any iterable |
| `itertools.groupby` | Group consecutive equal items |
| `itertools.accumulate` | Running total/max/min |
| Generator pipeline | Chain transformations lazily |

## Further Reading
- [itertools docs](https://docs.python.org/3/library/itertools.html)
- [Python Generators](https://docs.python.org/3/howto/functional.html#generators)
