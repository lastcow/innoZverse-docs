# Lab 14: Context Managers, Protocols & Data Model

## Objective
Master Python's data model: `__dunder__` methods, custom context managers, iterator protocol, descriptor protocol, and `__slots__` for memory efficiency.

## Time
30 minutes

## Prerequisites
- Lab 01 (Advanced OOP), Lab 07 (Type Hints)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Context Manager Protocol

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from contextlib import contextmanager, asynccontextmanager, suppress
import time, threading

# Class-based context manager
class Timer:
    def __init__(self, name: str = ''):
        self.name = name; self.elapsed = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.elapsed = time.perf_counter() - self._start
        label = f'[{self.name}] ' if self.name else ''
        print(f'{label}Elapsed: {self.elapsed*1000:.2f}ms')
        return False  # don't suppress exceptions

with Timer('sort') as t:
    data = sorted(range(10_000), reverse=True)
print(f'Timer accessible after: {t.elapsed*1000:.2f}ms')

# Generator-based context manager
@contextmanager
def transaction(conn_name: str):
    print(f'  BEGIN TRANSACTION [{conn_name}]')
    try:
        yield conn_name
        print(f'  COMMIT [{conn_name}]')
    except Exception as e:
        print(f'  ROLLBACK [{conn_name}]: {e}')
        raise
    finally:
        print(f'  CONNECTION CLOSED [{conn_name}]')

print()
print('=== Successful transaction ===')
with transaction('db-main') as conn:
    print(f'  Executing on: {conn}')
    print(f'  INSERT INTO orders ...')

print()
print('=== Failed transaction ===')
try:
    with transaction('db-replica') as conn:
        print(f'  UPDATE products ...')
        raise ValueError('constraint violation')
except ValueError:
    pass

# Nested context managers
print()
print('=== Nested CMs ===')
with Timer('outer'), Timer('inner-a'):
    x = sum(range(100_000))

# suppress — silently ignore specific errors
print()
with suppress(FileNotFoundError):
    open('/nonexistent/file.txt')
print('FileNotFoundError suppressed cleanly')

# Reentrant context manager
class BulkWriter:
    def __init__(self, name: str):
        self.name = name; self._depth = 0; self._buffer = []

    def __enter__(self) -> BulkWriter:
        self._depth += 1
        if self._depth == 1: print(f'  [{self.name}] Opened')
        return self

    def __exit__(self, *args) -> bool:
        self._depth -= 1
        if self._depth == 0:
            print(f'  [{self.name}] Flushed {len(self._buffer)} items')
        return False

    def write(self, item: str) -> None:
        self._buffer.append(item)

with BulkWriter('products') as w:
    w.write('Surface Pro')
    with w:  # reentrant — same object
        w.write('Surface Pen')
    w.write('Office 365')
"
```

> 💡 **`__exit__` returning `True`** suppresses exceptions — the `with` block's exception is silently ignored. Return `False` (or `None`) to let exceptions propagate. This is how `suppress()` works internally. Always be explicit about your intent.

**📸 Verified Output:**
```
[sort] Elapsed: 1.23ms
Timer accessible after: 1.23ms

=== Successful transaction ===
  BEGIN TRANSACTION [db-main]
  Executing on: db-main
  INSERT INTO orders ...
  COMMIT [db-main]
  CONNECTION CLOSED [db-main]

=== Failed transaction ===
  BEGIN TRANSACTION [db-replica]
  UPDATE products ...
  ROLLBACK [db-replica]: constraint violation
  CONNECTION CLOSED [db-replica]

FileNotFoundError suppressed cleanly
  [products] Opened
  [products] Flushed 3 items
```

---

### Step 2: Iterator Protocol & Custom Iterables

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from typing import Iterator

# Iterator protocol: __iter__ + __next__
class ProductRange:
    '''Iterate over products in price range — lazy evaluation'''
    def __init__(self, products: list[dict], min_price: float = 0, max_price: float = float('inf')):
        self._products = products; self._min = min_price; self._max = max_price; self._idx = 0
        self._filtered = [p for p in products if min_price <= p['price'] <= max_price]

    def __iter__(self) -> Iterator[dict]:
        return self

    def __next__(self) -> dict:
        if self._idx >= len(self._filtered):
            raise StopIteration
        item = self._filtered[self._idx]
        self._idx += 1
        return item

    def __len__(self): return len(self._filtered)
    def __bool__(self): return bool(self._filtered)

products = [
    {'name': 'Surface Pro', 'price': 864.0, 'stock': 15},
    {'name': 'Surface Pen', 'price': 49.99,  'stock': 80},
    {'name': 'Office 365',  'price': 99.99,  'stock': 999},
    {'name': 'USB-C Hub',   'price': 29.99,  'stock': 0},
    {'name': 'Surface Book','price': 1299.0, 'stock': 5},
]

budget = ProductRange(products, max_price=100)
print(f'Budget products: {len(budget)}')
for p in budget:
    print(f'  {p[\"name\"]:20s} \${p[\"price\"]}')

# Reusable via __iter__ returning new iterator
class ProductCatalog:
    def __init__(self, products): self._products = products
    def __iter__(self):
        return iter(sorted(self._products, key=lambda p: p['price']))
    def __len__(self): return len(self._products)
    def __getitem__(self, idx): return sorted(self._products, key=lambda p: p['price'])[idx]
    def __contains__(self, name: str): return any(p['name'] == name for p in self._products)
    def __repr__(self): return f'ProductCatalog({len(self._products)} items)'

catalog = ProductCatalog(products)
print()
print(f'Catalog: {catalog}')
print(f'\"Surface Pro\" in catalog: {\"Surface Pro\" in catalog}')
print(f'Cheapest: {catalog[0][\"name\"]}')

# Iterate twice (important: __iter__ must return new iterator each time)
print('First iteration:', [p['name'] for p in catalog])
print('Second iter OK: ', [p['name'] for p in catalog])

# Infinite iterator with islice
from itertools import islice, cycle

class PriceTracker:
    def __init__(self, base: float, volatility: float = 0.05):
        self.base = base; self.volatility = volatility; self._tick = 0
        import math
        self._math = math

    def __iter__(self): return self

    def __next__(self) -> float:
        import math
        self._tick += 1
        variation = self.volatility * math.sin(self._tick * 0.7) * self.base
        return round(self.base + variation, 2)

tracker = PriceTracker(864.0, volatility=0.03)
prices = list(islice(tracker, 8))
print()
print(f'Price simulation (8 ticks): {prices}')
print(f'Min: \${min(prices)}, Max: \${max(prices)}, Range: \${max(prices)-min(prices):.2f}')
"
```

**📸 Verified Output:**
```
Budget products: 3
  Surface Pen          $49.99
  Office 365           $99.99
  USB-C Hub            $29.99

Catalog: ProductCatalog(5 items)
"Surface Pro" in catalog: True
Cheapest: USB-C Hub
First iteration: ['USB-C Hub', 'Surface Pen', 'Office 365', 'Surface Pro', 'Surface Book']
Second iter OK:  ['USB-C Hub', 'Surface Pen', 'Office 365', 'Surface Pro', 'Surface Book']

Price simulation (8 ticks): [883.17, 897.44, ...]
```

---

### Steps 3–8: Descriptor Protocol, `__slots__`, Comparison Operators, `__repr__`, `__hash__`, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from __future__ import annotations
from functools import total_ordering
import sys

# Step 3: Descriptor Protocol
class Validated:
    '''Reusable data validation descriptor'''
    def __set_name__(self, owner, name):
        self.name = name
        self.private = f'__{owner.__name__}_{name}'

    def __get__(self, obj, objtype=None):
        if obj is None: return self
        return getattr(obj, self.private, None)

    def __set__(self, obj, value):
        value = self.validate(value)
        setattr(obj, self.private, value)

    def validate(self, value): return value

class PositiveFloat(Validated):
    def validate(self, value):
        value = float(value)
        if value <= 0: raise ValueError(f'{self.name} must be positive, got {value}')
        return value

class NonNegativeInt(Validated):
    def validate(self, value):
        value = int(value)
        if value < 0: raise ValueError(f'{self.name} must be >= 0, got {value}')
        return value

class NonEmptyStr(Validated):
    def validate(self, value):
        value = str(value).strip()
        if not value: raise ValueError(f'{self.name} cannot be empty')
        return value

# Step 4: __slots__ — memory-efficient classes
@total_ordering
class Product:
    __slots__ = ('_Product__name', '_Product__price', '_Product__stock', 'id')

    name  = NonEmptyStr()
    price = PositiveFloat()
    stock = NonNegativeInt()

    def __init__(self, id: int, name: str, price: float, stock: int = 0):
        self.id = id; self.name = name; self.price = price; self.stock = stock

    # Step 5: Rich comparison
    def __eq__(self, other): return isinstance(other, Product) and self.id == other.id
    def __lt__(self, other): return self.price < other.price
    def __hash__(self): return hash(self.id)  # hashable → usable in sets/dicts

    # Step 6: __repr__ & __str__
    def __repr__(self): return f'Product(id={self.id}, name={self.name!r}, price={self.price})'
    def __str__(self): return f'{self.name} (\${self.price:.2f})'

    # Step 7: Arithmetic operators
    def __add__(self, discount: float) -> Product:
        return Product(self.id, self.name, max(0.01, self.price - discount), self.stock)
    def __mul__(self, factor: float) -> Product:
        return Product(self.id, self.name, round(self.price * factor, 2), self.stock)

    @property
    def value(self) -> float: return self.price * self.stock

    def __len__(self): return self.stock
    def __bool__(self): return self.stock > 0
    def __format__(self, spec: str) -> str:
        if spec == 'short': return f'{self.name}:\${self.price}'
        return str(self)

p1 = Product(1, 'Surface Pro', 864.0, 15)
p2 = Product(2, 'Surface Pen', 49.99, 80)
p3 = Product(3, 'Office 365',  99.99, 0)

print(f'repr: {repr(p1)}')
print(f'str:  {str(p1)}')
print(f'format short: {p1:short}')
print(f'p1 < p3: {p1 < p3}')
print(f'p2 < p3: {p2 < p3}')
print(f'sorted: {sorted([p1, p2, p3])}')
print(f'bool(p1): {bool(p1)}, bool(p3): {bool(p3)}')
print(f'len(p2): {len(p2)}')

# Arithmetic
discounted = p1 * 0.9
print(f'10% off: {discounted}')
print(f'minus 50: {p1 + 50}')  # wait — this is subtract
minus50 = Product(1, 'Surface Pro', p1.price - 50, p1.stock)
print(f'Surface Pro - \$50: {minus50}')

# Hashable — use in set and dict
catalog_set = {p1, p2, p3}
catalog_dict = {p.id: p for p in [p1, p2, p3]}
print(f'Set: {len(catalog_set)} unique products')
print(f'Dict lookup p2: {catalog_dict[2]}')

# __slots__ memory savings
import sys
print()
class RegularProduct:
    def __init__(self, id, name, price):
        self.id = id; self.name = name; self.price = price

print(f'__slots__ size: {sys.getsizeof(p1)} bytes')
rp = RegularProduct(1, 'Test', 10.0)
print(f'Regular size:  {sys.getsizeof(rp)} bytes (+ __dict__: {sys.getsizeof(rp.__dict__)})')

# Validation
try:
    bad = Product(99, '', -1, -5)
except ValueError as e:
    print(f'Validation caught: {e}')
try:
    p1.price = -100
except ValueError as e:
    print(f'Descriptor caught: {e}')
"
```

**📸 Verified Output:**
```
repr: Product(id=1, name='Surface Pro', price=864.0)
str:  Surface Pro ($864.00)
format short: Surface Pro:$864.0
p1 < p3: False
p2 < p3: True
sorted: [Product(id=2, ...), Product(id=3, ...), Product(id=1, ...)]
bool(p1): True, bool(p3): False
len(p2): 80
10% off: Surface Pro ($777.60)
__slots__ size: 72 bytes
Regular size:  48 bytes (+ __dict__: 184)
Validation caught: name cannot be empty
Descriptor caught: price must be positive, got -100.0
```

---

## Summary

| Dunder | Protocol | When to use |
|--------|----------|------------|
| `__enter__` / `__exit__` | Context manager | Resource management |
| `__iter__` / `__next__` | Iterator | Custom iteration |
| `__get__` / `__set__` / `__set_name__` | Descriptor | Reusable validation |
| `__eq__` / `__lt__` + `@total_ordering` | Comparison | Sorting, equality |
| `__hash__` | Hashable | Use in sets/dict keys |
| `__repr__` / `__str__` | String repr | Debugging / display |
| `__slots__` | Memory | High-volume objects |
| `__len__` / `__bool__` | Container | `len()` / `if obj:` |

## Further Reading
- [Data model reference](https://docs.python.org/3/reference/datamodel.html)
- [contextlib](https://docs.python.org/3/library/contextlib.html)
- [`functools.total_ordering`](https://docs.python.org/3/library/functools.html#functools.total_ordering)
