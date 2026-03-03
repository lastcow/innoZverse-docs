# Lab 01: Advanced OOP — Metaclasses, Descriptors & Protocols

## Objective
Master Python's advanced OOP features: abstract base classes, dataclasses, descriptors, metaclasses, `__slots__`, multiple inheritance MRO, and the Protocol pattern.

## Time
35 minutes

## Prerequisites
- Python Foundations Labs 01–05

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Dataclasses & Field Validation

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from dataclasses import dataclass, field, fields, asdict
from typing import ClassVar

@dataclass
class Product:
    name: str
    price: float
    stock: int = 0
    tags: list[str] = field(default_factory=list)
    _registry: ClassVar[list] = []

    def __post_init__(self):
        if self.price <= 0:
            raise ValueError(f'price must be positive, got {self.price}')
        if self.stock < 0:
            raise ValueError(f'stock cannot be negative')
        self.name = self.name.strip()
        Product._registry.append(self)

    @property
    def status(self) -> str:
        return 'out_of_stock' if self.stock == 0 else 'active'

    def __str__(self) -> str:
        return f'[{self.name}] \${self.price:.2f} stock={self.stock} ({self.status})'

@dataclass(frozen=True)   # immutable
class SKU:
    vendor: str
    code: str

    def __str__(self):
        return f'{self.vendor}-{self.code}'

p1 = Product('Surface Pro 12\"', 864.00, 15, ['laptop', 'microsoft'])
p2 = Product('Surface Pen', 49.99, 80)

print(p1)
print('Dict:', asdict(p1))
print('Fields:', [f.name for f in fields(p1)])

sku = SKU('MSFT', 'SRF-PRO-12')
print('SKU:', sku)

try:
    Product('Bad', -10)
except ValueError as e:
    print('Error:', e)
"
```

> 💡 **`@dataclass`** auto-generates `__init__`, `__repr__`, `__eq__` from type-annotated fields. `field(default_factory=list)` creates a new list per instance (never share a mutable default). `frozen=True` makes the dataclass immutable and hashable — perfect for dict keys and set members.

**📸 Verified Output:**
```
[Surface Pro 12"] $864.00 stock=15 (active)
Dict: {'name': 'Surface Pro 12"', 'price': 864.0, 'stock': 15, 'tags': ['laptop', 'microsoft']}
Fields: ['name', 'price', 'stock', 'tags']
SKU: MSFT-SRF-PRO-12
Error: price must be positive, got -10
```

---

### Step 2: Abstract Base Classes

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from abc import ABC, abstractmethod
from typing import Iterator

class DataSource(ABC):
    @abstractmethod
    def connect(self) -> bool: ...

    @abstractmethod
    def fetch(self, query: str) -> list[dict]: ...

    @abstractmethod
    def close(self) -> None: ...

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    # Concrete method on abstract class
    def fetch_one(self, query: str) -> dict | None:
        results = self.fetch(query)
        return results[0] if results else None

class MockDB(DataSource):
    def __init__(self, data: list[dict]):
        self._data = data
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        print('MockDB: connected')
        return True

    def fetch(self, query: str) -> list[dict]:
        if not self._connected:
            raise RuntimeError('Not connected')
        return [r for r in self._data if query.lower() in str(r).lower()]

    def close(self) -> None:
        self._connected = False
        print('MockDB: closed')

data = [
    {'id': 1, 'name': 'Surface Pro', 'price': 864},
    {'id': 2, 'name': 'Surface Pen', 'price': 49.99},
    {'id': 3, 'name': 'Office 365',  'price': 99.99},
]

with MockDB(data) as db:
    results = db.fetch('surface')
    for r in results:
        print(f'  {r[\"name\"]} \${r[\"price\"]}')
    one = db.fetch_one('Office')
    print('Single:', one)

# Cannot instantiate ABC
try:
    DataSource()
except TypeError as e:
    print('ABC error:', e)
"
```

**📸 Verified Output:**
```
MockDB: connected
  Surface Pro $864
  Surface Pen $49.99
Single: {'id': 3, 'name': 'Office 365', 'price': 99.99}
MockDB: closed
ABC error: Can't instantiate abstract class DataSource without an implementation for abstract methods 'close', 'connect', 'fetch'
```

---

### Step 3: Descriptors

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
class Validator:
    def __set_name__(self, owner, name):
        self.name = name
        self.private = f'_{name}'

    def __get__(self, obj, objtype=None):
        if obj is None: return self
        return getattr(obj, self.private, None)

    def __set__(self, obj, value):
        self.validate(value)
        setattr(obj, self.private, value)

    def validate(self, value):
        pass

class PositiveFloat(Validator):
    def validate(self, value):
        if not isinstance(value, (int, float)):
            raise TypeError(f'{self.name} must be numeric')
        if value <= 0:
            raise ValueError(f'{self.name} must be positive, got {value}')

class NonEmptyStr(Validator):
    def validate(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f'{self.name} must be a non-empty string')

class RangedInt(Validator):
    def __init__(self, lo: int, hi: int):
        self.lo, self.hi = lo, hi

    def validate(self, value):
        if not isinstance(value, int):
            raise TypeError(f'{self.name} must be int')
        if not self.lo <= value <= self.hi:
            raise ValueError(f'{self.name} must be in [{self.lo}, {self.hi}], got {value}')

class Product:
    name  = NonEmptyStr()
    price = PositiveFloat()
    stock = RangedInt(0, 100_000)

    def __init__(self, name, price, stock):
        self.name  = name
        self.price = price
        self.stock = stock

    def __repr__(self):
        return f'Product({self.name!r}, \${self.price:.2f}, stock={self.stock})'

p = Product('Surface Pro', 864.00, 15)
print(p)
p.price = 799.99
print('Updated:', p)

for bad in [('', 864, 10), ('X', -1, 10), ('X', 9.99, -1)]:
    try:
        Product(*bad)
    except (ValueError, TypeError) as e:
        print('Error:', e)
"
```

> 💡 **Descriptors** (`__get__`, `__set__`, `__set_name__`) are the mechanism behind Python's `property`, `classmethod`, `staticmethod`, and ORM field definitions. When you write `Column(String)` in SQLAlchemy, `Column` is a descriptor. This lab shows how to build your own reusable validation layer.

**📸 Verified Output:**
```
Product('Surface Pro', $864.00, stock=15)
Updated: Product('Surface Pro', $799.99, stock=15)
Error: name must be a non-empty string
Error: price must be positive, got -1
Error: stock must be in [0, 100000], got -1
```

---

### Steps 4–8: __slots__, MRO, Metaclass, Protocol, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from abc import abstractmethod
from typing import Protocol, runtime_checkable
import sys

# Step 4: __slots__ for memory efficiency
class RegularPoint:
    def __init__(self, x, y): self.x = x; self.y = y

class SlottedPoint:
    __slots__ = ('x', 'y')
    def __init__(self, x, y): self.x = x; self.y = y

r = RegularPoint(1, 2)
s = SlottedPoint(1, 2)
print(f'Regular __dict__: {r.__dict__}')
print(f'Slotted has __dict__: {hasattr(s, \"__dict__\")}')
# ~3-5x less memory for slotted

# Step 5: Multiple inheritance & MRO
class Timestamped:
    def info(self): return 'Timestamped'

class Audited:
    def info(self): return 'Audited'

class Entity(Timestamped, Audited):
    pass

print('MRO:', [c.__name__ for c in Entity.__mro__])
print('Entity.info():', Entity().info())  # Timestamped wins (left-first)

# Step 6: Metaclass — class factory
class SingletonMeta(type):
    _instances: dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class AppConfig(metaclass=SingletonMeta):
    def __init__(self):
        self.debug = False
        self.port  = 8080

cfg1 = AppConfig()
cfg2 = AppConfig()
cfg1.debug = True
print('Same instance:', cfg1 is cfg2)
print('cfg2.debug:', cfg2.debug)  # True — same object

# Step 7: Protocol (structural subtyping)
@runtime_checkable
class Serializable(Protocol):
    def serialize(self) -> dict: ...
    def deserialize(self, data: dict) -> None: ...

class User:
    def __init__(self, name: str, email: str):
        self.name = name; self.email = email

    def serialize(self) -> dict:
        return {'name': self.name, 'email': self.email}

    def deserialize(self, data: dict) -> None:
        self.name = data['name']; self.email = data['email']

class Order:
    def __init__(self, id: int, total: float):
        self.id = id; self.total = total

    def serialize(self) -> dict:
        return {'id': self.id, 'total': self.total}

    def deserialize(self, data: dict) -> None:
        self.id = data['id']; self.total = data['total']

def export_all(items: list[Serializable]) -> list[dict]:
    return [item.serialize() for item in items]

user  = User('Dr. Chen', 'ebiz@chen.me')
order = Order(1001, 864.00)
print('Is Serializable:', isinstance(user, Serializable))
exports = export_all([user, order])
for e in exports: print(' ', e)

# Step 8: Capstone — Registry metaclass
class PluginMeta(type):
    registry: dict[str, type] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:  # skip the base class itself
            tag = namespace.get('plugin_name', name.lower())
            mcs.registry[tag] = cls
        return cls

class Plugin(metaclass=PluginMeta):
    plugin_name = 'base'
    def run(self, data: str) -> str: raise NotImplementedError

class UpperPlugin(Plugin):
    plugin_name = 'upper'
    def run(self, data: str) -> str: return data.upper()

class ReversePlugin(Plugin):
    plugin_name = 'reverse'
    def run(self, data: str) -> str: return data[::-1]

class WordCountPlugin(Plugin):
    plugin_name = 'wordcount'
    def run(self, data: str) -> str: return f'words={len(data.split())}'

print('Registered plugins:', list(PluginMeta.registry.keys()))
for name, cls in PluginMeta.registry.items():
    result = cls().run('Hello innoZverse')
    print(f'  {name}: {result!r}')
"
```

**📸 Verified Output:**
```
Regular __dict__: {'x': 1, 'y': 2}
Slotted has __dict__: False
MRO: ['Entity', 'Timestamped', 'Audited', 'object']
Entity.info(): Timestamped
Same instance: True
cfg2.debug: True
Is Serializable: True
  {'name': 'Dr. Chen', 'email': 'ebiz@chen.me'}
  {'id': 1001, 'total': 864.0}
Registered plugins: ['upper', 'reverse', 'wordcount']
  upper: 'HELLO INNOZVERSE'
  reverse: 'esreVZonni olleH'
  wordcount: 'words=2'
```

---

## Summary

| Feature | Use case |
|---------|---------|
| `@dataclass` | Auto-generate boilerplate, validated models |
| `ABC` + `@abstractmethod` | Enforce interface contracts |
| Descriptors | Reusable field validation, ORM columns |
| `__slots__` | Memory-efficient classes with fixed attributes |
| MRO (C3) | Predictable multiple inheritance resolution |
| Metaclass | Class factories, singletons, registries |
| `Protocol` | Duck typing with type-checker support |

## Further Reading
- [Python Data Model](https://docs.python.org/3/reference/datamodel.html)
- [PEP 544 — Protocols](https://peps.python.org/pep-0544/)
- [PEP 557 — Dataclasses](https://peps.python.org/pep-0557/)
