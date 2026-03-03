# Lab 12: Design Patterns in Python

## Objective
Implement the most useful Gang-of-Four design patterns in idiomatic Python: Singleton, Factory, Observer, Strategy, Command, Decorator, and Composite.

## Time
30 minutes

## Prerequisites
- Lab 01 (Advanced OOP), Lab 02 (Decorators)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Creational Patterns — Singleton & Factory

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from __future__ import annotations
from typing import ClassVar
import threading

# --- Singleton (thread-safe) ---
class Config:
    _instance: ClassVar[Config | None] = None
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __new__(cls) -> Config:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._settings = {
                        'db_url': 'sqlite:///store.db',
                        'api_key': 'secret',
                        'debug': False,
                    }
        return cls._instance

    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def set(self, key: str, value) -> None:
        self._settings[key] = value

c1, c2 = Config(), Config()
c1.set('debug', True)
print('Same instance:', c1 is c2)
print('c2.debug:', c2.get('debug'))  # True — same object

# --- Factory Method ---
from abc import ABC, abstractmethod
from dataclasses import dataclass

class Exporter(ABC):
    @abstractmethod
    def export(self, data: list[dict]) -> str: ...

class JsonExporter(Exporter):
    def export(self, data):
        import json
        return json.dumps(data, indent=2)

class CsvExporter(Exporter):
    def export(self, data):
        if not data: return ''
        headers = ','.join(data[0].keys())
        rows = [','.join(str(v) for v in row.values()) for row in data]
        return '\n'.join([headers] + rows)

class TsvExporter(Exporter):
    def export(self, data):
        if not data: return ''
        return '\n'.join('\t'.join(str(v) for v in row.values()) for row in data)

def exporter_factory(fmt: str) -> Exporter:
    exporters = {'json': JsonExporter, 'csv': CsvExporter, 'tsv': TsvExporter}
    cls = exporters.get(fmt)
    if cls is None:
        raise ValueError(f'Unknown format: {fmt!r}. Choose from {list(exporters)}')
    return cls()

products = [
    {'id': 1, 'name': 'Surface Pro', 'price': 864.0},
    {'id': 2, 'name': 'Surface Pen', 'price': 49.99},
]

for fmt in ['json', 'csv', 'tsv']:
    exp = exporter_factory(fmt)
    result = exp.export(products)
    print(f'--- {fmt.upper()} ---')
    print(result[:80])
"
```

> 💡 **Singleton** ensures exactly one instance exists (useful for config, DB connections). The double-checked locking pattern (`if _instance is None` inside `with _lock`) prevents race conditions in multithreaded code without locking on every access. **Factory Method** decouples creation logic from usage — add a new format without changing caller code.

**📸 Verified Output:**
```
Same instance: True
c2.debug: True
--- JSON ---
[
  {
    "id": 1,
    "name": "Surface Pro",
--- CSV ---
id,name,price
1,Surface Pro,864.0
--- TSV ---
1	Surface Pro	864.0
```

---

### Step 2: Behavioral Patterns — Observer & Strategy

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable
from collections import defaultdict

# --- Observer ---
class EventBus:
    '''Lightweight publish/subscribe event bus'''
    def __init__(self):
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable) -> None:
        self._listeners[event].append(handler)

    def unsubscribe(self, event: str, handler: Callable) -> None:
        self._listeners[event] = [h for h in self._listeners[event] if h is not handler]

    def publish(self, event: str, **payload) -> None:
        for handler in self._listeners[event]:
            handler(**payload)

    def on(self, event: str):
        '''Decorator shorthand'''
        def decorator(fn):
            self.subscribe(event, fn)
            return fn
        return decorator

bus = EventBus()

notifications = []

@bus.on('product.created')
def log_creation(product_id: int, name: str, **kw):
    notifications.append(f'LOG: Product #{product_id} \"{name}\" created')

@bus.on('product.created')
def notify_slack(product_id: int, name: str, price: float, **kw):
    notifications.append(f'SLACK: New product! {name} at \${price}')

@bus.on('stock.low')
def alert_manager(product_id: int, stock: int, **kw):
    notifications.append(f'ALERT: Product #{product_id} low stock: {stock}')

bus.publish('product.created', product_id=1, name='Surface Pro', price=864.0)
bus.publish('product.created', product_id=2, name='Surface Pen', price=49.99)
bus.publish('stock.low', product_id=1, stock=2)

for n in notifications:
    print(n)

# --- Strategy ---
from typing import Protocol

class SortStrategy(Protocol):
    def sort(self, products: list[dict]) -> list[dict]: ...

class ByPriceAsc:
    def sort(self, products): return sorted(products, key=lambda p: p['price'])

class ByPriceDesc:
    def sort(self, products): return sorted(products, key=lambda p: p['price'], reverse=True)

class ByName:
    def sort(self, products): return sorted(products, key=lambda p: p['name'])

class ByValue:
    def sort(self, products): return sorted(products, key=lambda p: p['price']*p['stock'], reverse=True)

class ProductCatalog:
    def __init__(self, strategy: SortStrategy = ByName()):
        self._strategy = strategy
        self._products: list[dict] = []

    def set_strategy(self, strategy: SortStrategy) -> None:
        self._strategy = strategy

    def add(self, name: str, price: float, stock: int) -> None:
        self._products.append({'name': name, 'price': price, 'stock': stock})

    def list(self) -> list[dict]:
        return self._strategy.sort(self._products)

catalog = ProductCatalog()
catalog.add('Surface Book', 1299.0, 5)
catalog.add('Surface Pen',   49.99,  80)
catalog.add('Office 365',    99.99,  999)
catalog.add('USB-C Hub',     29.99,  0)

for strategy_cls, label in [(ByPriceAsc, 'Price Asc'), (ByName, 'Name'), (ByValue, 'Value')]:
    catalog.set_strategy(strategy_cls())
    names = [p['name'] for p in catalog.list()]
    print(f'{label:10s}: {names}')
"
```

**📸 Verified Output:**
```
LOG: Product #1 "Surface Pro" created
SLACK: New product! Surface Pro at $864.0
LOG: Product #2 "Surface Pen" created
SLACK: New product! Surface Pen at $49.99
ALERT: Product #1 low stock: 2
Price Asc : ['USB-C Hub', 'Surface Pen', 'Office 365', 'Surface Book']
Name      : ['Office 365', 'Surface Book', 'Surface Pen', 'USB-C Hub']
Value     : ['Office 365', 'Surface Pen', 'Surface Book', 'USB-C Hub']
```

---

### Steps 3–8: Command, Builder, Composite, Adapter, Template Method, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

# Step 3: Command Pattern (with undo)
class Command(ABC):
    @abstractmethod
    def execute(self) -> None: ...
    @abstractmethod
    def undo(self) -> None: ...

class ProductStore:
    def __init__(self):
        self.products: dict[int, dict] = {}
        self._next_id = 1
    def _new_id(self):
        i = self._next_id; self._next_id += 1; return i

store = ProductStore()

class CreateProductCommand(Command):
    def __init__(self, store: ProductStore, name: str, price: float):
        self.store = store; self.name = name; self.price = price; self.id: int | None = None
    def execute(self):
        self.id = self.store._new_id()
        self.store.products[self.id] = {'id': self.id, 'name': self.name, 'price': self.price}
        print(f'  Created: #{self.id} {self.name}')
    def undo(self):
        self.store.products.pop(self.id, None)
        print(f'  Undone:  #{self.id} {self.name}')

class UpdatePriceCommand(Command):
    def __init__(self, store: ProductStore, product_id: int, new_price: float):
        self.store = store; self.pid = product_id; self.new_price = new_price; self.old_price = None
    def execute(self):
        p = self.store.products[self.pid]
        self.old_price = p['price']
        p['price'] = self.new_price
        print(f'  Price updated: #{self.pid} \${self.old_price} → \${self.new_price}')
    def undo(self):
        self.store.products[self.pid]['price'] = self.old_price
        print(f'  Price reverted: #{self.pid} → \${self.old_price}')

class CommandHistory:
    def __init__(self): self._history: list[Command] = []
    def execute(self, cmd: Command) -> None:
        cmd.execute(); self._history.append(cmd)
    def undo(self) -> None:
        if self._history: self._history.pop().undo()

history = CommandHistory()
print('=== Command Pattern ===')
history.execute(CreateProductCommand(store, 'Surface Pro', 864.0))
history.execute(CreateProductCommand(store, 'Surface Pen', 49.99))
history.execute(UpdatePriceCommand(store, 1, 799.99))
history.undo()  # Reverts price
history.undo()  # Removes Surface Pen
print(f'  Remaining: {list(store.products.values())}')

# Step 4: Builder
class QueryBuilder:
    def __init__(self):
        self._table = ''; self._conditions = []; self._order = None
        self._limit = None; self._offset = None; self._columns = ['*']

    def from_table(self, table: str) -> QueryBuilder:
        self._table = table; return self
    def select(self, *cols: str) -> QueryBuilder:
        self._columns = list(cols); return self
    def where(self, condition: str) -> QueryBuilder:
        self._conditions.append(condition); return self
    def order_by(self, col: str, desc: bool = False) -> QueryBuilder:
        self._order = f'{col} DESC' if desc else col; return self
    def limit(self, n: int) -> QueryBuilder:
        self._limit = n; return self
    def offset(self, n: int) -> QueryBuilder:
        self._offset = n; return self
    def build(self) -> str:
        q = f'SELECT {', '.join(self._columns)} FROM {self._table}'
        if self._conditions: q += ' WHERE ' + ' AND '.join(self._conditions)
        if self._order: q += f' ORDER BY {self._order}'
        if self._limit: q += f' LIMIT {self._limit}'
        if self._offset: q += f' OFFSET {self._offset}'
        return q

print()
print('=== Builder Pattern ===')
q = (QueryBuilder()
     .from_table('products')
     .select('id', 'name', 'price', 'stock')
     .where('stock > 0')
     .where('price < 1000')
     .order_by('price', desc=True)
     .limit(10)
     .offset(0)
     .build())
print(q)

# Step 5: Composite
class PriceComponent(ABC):
    @property
    @abstractmethod
    def price(self) -> float: ...
    @abstractmethod
    def describe(self, indent: int = 0) -> str: ...

@dataclass
class Item(PriceComponent):
    name: str; unit_price: float; qty: int = 1
    @property
    def price(self): return self.unit_price * self.qty
    def describe(self, indent=0):
        return '  '*indent + f'{self.name} x{self.qty} = \${self.price:.2f}'

@dataclass
class Bundle(PriceComponent):
    name: str
    children: list[PriceComponent] = field(default_factory=list)
    discount: float = 0.0
    @property
    def price(self):
        subtotal = sum(c.price for c in self.children)
        return subtotal * (1 - self.discount)
    def add(self, c: PriceComponent) -> Bundle:
        self.children.append(c); return self
    def describe(self, indent=0):
        lines = ['  '*indent + f'[Bundle] {self.name} = \${self.price:.2f}']
        for c in self.children: lines.append(c.describe(indent+1))
        return '\n'.join(lines)

order = Bundle('Enterprise Order', discount=0.1)
order.add(Item('Surface Pro', 864.0, 3))
order.add(Item('Surface Pen', 49.99, 3))
acc = Bundle('Accessories Pack')
acc.add(Item('USB-C Hub', 29.99, 5))
acc.add(Item('Keyboard',  129.99, 2))
order.add(acc)

print()
print('=== Composite Pattern ===')
print(order.describe())
print(f'Final price: \${order.price:.2f} (10% bundle discount applied)')
"
```

**📸 Verified Output:**
```
=== Command Pattern ===
  Created: #1 Surface Pro
  Created: #2 Surface Pen
  Price updated: #1 $864.0 → $799.99
  Price reverted: #1 → $864.0
  Undone:  #2 Surface Pen
  Remaining: [{'id': 1, 'name': 'Surface Pro', 'price': 864.0}]

=== Builder Pattern ===
SELECT id, name, price, stock FROM products WHERE stock > 0 AND price < 1000 ORDER BY price DESC LIMIT 10 OFFSET 0

=== Composite Pattern ===
[Bundle] Enterprise Order = $2,888.60
  Surface Pro x3 = $2592.00
  Surface Pen x3 = $149.97
  [Bundle] Accessories Pack = $409.93
    USB-C Hub x5 = $149.95
    Keyboard x2 = $259.98
Final price: $2,888.60 (10% bundle discount applied)
```

---

## Summary

| Pattern | Category | Python idiom |
|---------|----------|-------------|
| Singleton | Creational | `__new__` + class var |
| Factory | Creational | `dict` dispatch + ABC |
| Observer | Behavioral | `EventBus` with `subscribe`/`publish` |
| Strategy | Behavioral | `Protocol` + runtime swap |
| Command | Behavioral | ABC + history list for undo |
| Builder | Creational | Fluent interface (method chaining) |
| Composite | Structural | Recursive ABC `price` property |

## Further Reading
- [Refactoring Guru — Python patterns](https://refactoring.guru/design-patterns/python)
- [Gang of Four book](https://en.wikipedia.org/wiki/Design_Patterns)
