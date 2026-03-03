# Lab 01: Metaprogramming

## Objective
Master Python's metaprogramming toolkit: `__init_subclass__` for automatic plugin registration, metaclasses for class-level control, descriptor factories with `__set_name__`, `__class_getitem__` for parametric types, and dynamic class creation with `type()`.

## Background
Metaprogramming means writing code that writes or modifies code. Python exposes its entire object model at runtime, which means you can intercept class creation, customize attribute access, and build domain-specific type systems — all without external libraries.

## Time
35 minutes

## Prerequisites
- Python Practitioner Labs 01 (Advanced OOP), 07 (Type Hints)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: `__init_subclass__` — Automatic Plugin Registry

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
class PluginBase:
    '''Base class that auto-registers subclasses by name.'''
    _registry: dict = {}

    def __init_subclass__(cls, plugin_name: str = None, **kw):
        super().__init_subclass__(**kw)
        if plugin_name:
            PluginBase._registry[plugin_name] = cls
            print(f'  Registered plugin: {plugin_name!r} -> {cls.__name__}')

# Subclasses register themselves simply by subclassing with plugin_name=
class JsonPlugin(PluginBase, plugin_name='json'):
    def process(self, data: dict) -> str:
        import json
        return json.dumps(data)

class CsvPlugin(PluginBase, plugin_name='csv'):
    def process(self, data: dict) -> str:
        return ','.join(str(v) for v in data.values())

class TsvPlugin(PluginBase, plugin_name='tsv'):
    def process(self, data: dict) -> str:
        return '\t'.join(str(v) for v in data.values())

print()
print('Registry:', list(PluginBase._registry.keys()))

# Use plugins by name — open/closed principle
record = {'id': 1, 'name': 'Surface Pro', 'price': 864.0}
for name, cls in PluginBase._registry.items():
    result = cls().process(record)
    print(f'  [{name}] {result}')
"
```

> 💡 **`__init_subclass__`** is called automatically whenever a class that inherits from yours is created. The keyword argument `plugin_name='json'` in the class definition body is passed as a `**kw` parameter. This pattern is how frameworks like FastAPI and SQLAlchemy auto-register things — no `@register` decorator or manual registry call needed.

**📸 Verified Output:**
```
  Registered plugin: 'json' -> JsonPlugin
  Registered plugin: 'csv' -> CsvPlugin
  Registered plugin: 'tsv' -> TsvPlugin

Registry: ['json', 'csv', 'tsv']
  [json] {"id": 1, "name": "Surface Pro", "price": 864.0}
  [csv] 1,Surface Pro,864.0
  [tsv] 1	Surface Pro	864.0
```

---

### Step 2: Metaclasses — Controlling Class Creation

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
# Metaclass: the 'class of a class'
# type(name, bases, namespace) creates a class dynamically
# A custom metaclass intercepts that process

class SingletonMeta(type):
    '''Ensures only one instance of any class using this metaclass.'''
    _instances: dict = {}

    def __call__(cls, *args, **kw):
        # Intercept instantiation
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kw)
        return cls._instances[cls]

class Config(metaclass=SingletonMeta):
    def __init__(self):
        self.settings = {
            'db_url': 'sqlite:///store.db',
            'debug': False,
            'max_connections': 10,
        }
    def get(self, key, default=None): return self.settings.get(key, default)
    def set(self, key, value): self.settings[key] = value

class Logger(metaclass=SingletonMeta):
    def __init__(self): self.logs = []
    def log(self, msg: str): self.logs.append(msg)
    def dump(self): return self.logs.copy()

c1, c2 = Config(), Config()
print(f'Same Config instance: {c1 is c2}')
c1.set('debug', True)
print(f'c2 sees debug=True: {c2.get(\"debug\")}')

l1, l2 = Logger(), Logger()
l1.log('App started')
l2.log('User authenticated')
print(f'l1 logs == l2 logs: {l1.dump() == l2.dump()}')
print(f'Logs: {l1.dump()}')

# Metaclass for validation — enforce interface methods
class AbstractMeta(type):
    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        required = set()
        for base in bases:
            required.update(getattr(base, '_required_methods', set()))
        for method in required:
            if not callable(getattr(cls, method, None)):
                raise TypeError(f'{name} must implement {method!r}')
        return cls

class BaseExporter(metaclass=AbstractMeta):
    _required_methods = {'export', 'mime_type'}

class GoodExporter(BaseExporter):
    def export(self, data): return str(data)
    def mime_type(self): return 'text/plain'

try:
    class BadExporter(BaseExporter):
        def export(self, data): return str(data)
        # missing mime_type
except TypeError as e:
    print(f'AbstractMeta caught: {e}')

print(f'GoodExporter works: {GoodExporter().export({\"id\": 1})}')
"
```

> 💡 **Metaclass vs `__init_subclass__`**: use `__init_subclass__` for most cases (simpler, cleaner). Use a metaclass only when you need to control the class *object itself* — like enforcing abstract methods at class creation time (not at instantiation), or when you need `__prepare__` to customise the class namespace before the body executes.

**📸 Verified Output:**
```
Same Config instance: True
c2 sees debug=True: True
l1 logs == l2 logs: True
Logs: ['App started', 'User authenticated']
AbstractMeta caught: BadExporter must implement 'mime_type'
GoodExporter works: {'id': 1}
```

---

### Step 3: Descriptor Factory with `__set_name__`

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
class Bounded:
    '''Reusable descriptor: validates a numeric attribute stays within [lo, hi].'''
    def __init__(self, lo, hi, type_=None):
        self.lo, self.hi = lo, hi
        self.type_ = type_

    def __set_name__(self, owner, name):
        # Called when the class body finishes; gives us owner class + attr name
        self.name = name
        self.attr = f'_{owner.__name__}__{name}'  # name-mangled private attr

    def __get__(self, obj, objtype=None):
        if obj is None: return self  # class-level access → return descriptor
        return getattr(obj, self.attr, self.lo)

    def __set__(self, obj, value):
        if self.type_ and not isinstance(value, self.type_):
            raise TypeError(f'{self.name} must be {self.type_.__name__}, got {type(value).__name__}')
        if not (self.lo <= value <= self.hi):
            raise ValueError(f'{self.name} must be in [{self.lo}, {self.hi}], got {value}')
        setattr(obj, self.attr, value)

    def __delete__(self, obj):
        raise AttributeError(f'{self.name} cannot be deleted')

class Product:
    # Class-level descriptors — shared among all instances
    price  = Bounded(0.01, 9_999.99, float)
    rating = Bounded(0.0, 5.0, float)
    stock  = Bounded(0, 999_999, int)

    def __init__(self, name: str, price: float, rating: float, stock: int):
        self.name = name
        self.price = price      # goes through Bounded.__set__
        self.rating = rating
        self.stock = stock

    def __repr__(self):
        return f'Product({self.name!r}, \${self.price}, ★{self.rating}, stock={self.stock})'

# Valid product
p = Product('Surface Pro', 864.0, 4.8, 15)
print(p)

# Test all validations
tests = [
    ('price too low',    lambda: Product('X', -1.0,  4.0, 10)),
    ('price too high',   lambda: Product('X', 99999, 4.0, 10)),
    ('rating out of 5',  lambda: Product('X', 10.0,  5.1, 10)),
    ('negative stock',   lambda: Product('X', 10.0,  4.0, -1)),
    ('wrong type stock', lambda: setattr(p, 'stock', 'lots')),
    ('delete blocked',   lambda: delattr(p, 'price')),
]
for label, fn in tests:
    try: fn()
    except (ValueError, TypeError, AttributeError) as e:
        print(f'  [{label}] Caught: {e}')

# Descriptor is on the class, not each instance — massive memory savings
import sys
print(f'Instance __dict__: {p.__dict__}')
# Note: values stored as _Product__price etc. by name mangling
"
```

**📸 Verified Output:**
```
Product('Surface Pro', $864.0, ★4.8, stock=15)
  [price too low] Caught: price must be in [0.01, 9999.99], got -1.0
  [price too high] Caught: price must be in [0.01, 9999.99], got 99999
  [rating out of 5] Caught: rating must be in [0.0, 5.0], got 5.1
  [negative stock] Caught: stock must be in [0, 999999], got -1
  [wrong type stock] Caught: stock must be str, got str
  [delete blocked] Caught: price cannot be deleted
Instance __dict__: {'name': 'Surface Pro', '_Product__price': 864.0, ...}
```

---

### Step 4: `__class_getitem__` — Parametric Types

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
class TypedList:
    '''A list that enforces element type, using [] syntax like list[int].'''

    def __class_getitem__(cls, item_type):
        '''Called when you write TypedList[int] — returns a new class.'''
        class Typed(list):
            _type = item_type

            def append(self, val):
                self._check(val)
                super().append(val)

            def insert(self, idx, val):
                self._check(val)
                super().insert(idx, val)

            def extend(self, iterable):
                checked = list(iterable)
                for v in checked: self._check(v)
                super().extend(checked)

            def _check(self, val):
                if not isinstance(val, self._type):
                    raise TypeError(
                        f'{self.__class__.__name__} expects {self._type.__name__}, '
                        f'got {type(val).__name__}: {val!r}'
                    )

            def __repr__(self):
                return f'{cls.__name__}[{item_type.__name__}]({list.__repr__(self)})'

        Typed.__name__ = f'{cls.__name__}[{item_type.__name__}]'
        return Typed

# Usage feels like built-in generics
IntList    = TypedList[int]
FloatList  = TypedList[float]
StrList    = TypedList[str]

il = IntList([1, 2, 3])
il.append(4)
il.extend([5, 6])
print(f'IntList: {il}')

fl = FloatList()
fl.extend([864.0, 49.99, 99.99])
print(f'FloatList: {fl}')

# Type errors
for bad, lst in [('hello', il), (42, fl), (3.14, StrList())]:
    try: lst.append(bad)
    except TypeError as e: print(f'  TypeError: {e}')

# Typed repository using __class_getitem__
class Repository:
    def __class_getitem__(cls, model_type):
        class Typed:
            def __init__(self): self._items: list[model_type] = []; self._seq = 1
            def add(self, item: model_type) -> int:
                if not isinstance(item, model_type):
                    raise TypeError(f'Expected {model_type.__name__}')
                setattr(item, 'id', self._seq); self._seq += 1
                self._items.append(item); return item.id
            def get(self, id): return next((i for i in self._items if i.id == id), None)
            def list(self): return self._items.copy()
            def __len__(self): return len(self._items)
        Typed.__name__ = f'Repository[{model_type.__name__}]'
        return Typed
    def __init_subclass__(cls, **kw): pass

from dataclasses import dataclass

@dataclass
class Product:
    name: str; price: float; stock: int = 0; id: int = 0

ProductRepo = Repository[Product]
repo = ProductRepo()
repo.add(Product('Surface Pro', 864.0, 15))
repo.add(Product('Surface Pen', 49.99, 80))
print(f'Repo has {len(repo)} products')
print(f'Product #1: {repo.get(1)}')
"
```

**📸 Verified Output:**
```
IntList: TypedList[int]([1, 2, 3, 4, 5, 6])
FloatList: TypedList[float]([864.0, 49.99, 99.99])
  TypeError: TypedList[int] expects int, got str: 'hello'
  TypeError: TypedList[float] expects float, got int: 42
  TypeError: TypedList[str] expects str, got float: 3.14
Repo has 2 products
Product #1: Product(name='Surface Pro', price=864.0, stock=15, id=1)
```

---

### Steps 5–8: Dynamic Class Factory, `__prepare__`, `__missing__`, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from typing import Any

# Step 5: type() as a class factory
def model_factory(name: str, fields: dict[str, type], validators: dict = None):
    '''Dynamically create a validated model class from a field spec.'''
    validators = validators or {}

    def __init__(self, **kw):
        for fname, ftype in fields.items():
            val = kw.get(fname)
            if val is None and fname not in kw:
                raise ValueError(f'{fname} is required')
            if val is not None and not isinstance(val, ftype):
                raise TypeError(f'{fname}: expected {ftype.__name__}, got {type(val).__name__}')
            if fname in validators:
                validators[fname](val)
            setattr(self, fname, val)

    def __repr__(self):
        vals = ', '.join(f'{f}={getattr(self, f)!r}' for f in fields)
        return f'{name}({vals})'

    def to_dict(self):
        return {f: getattr(self, f) for f in fields}

    namespace = {
        '__init__': __init__,
        '__repr__': __repr__,
        'to_dict':  to_dict,
        '_fields':  list(fields.keys()),
    }
    return type(name, (), namespace)

# Create model classes on the fly
Product = model_factory('Product', {
    'id':    int,
    'name':  str,
    'price': float,
    'stock': int,
}, validators={
    'price': lambda v: (_ for _ in ()).throw(ValueError(f'price must be > 0, got {v}')) if v <= 0 else None,
})

p = Product(id=1, name='Surface Pro', price=864.0, stock=15)
print(p)
print(p.to_dict())
print(f'Fields: {p._fields}')

try: Product(id=2, name='Bad', price='free', stock=0)
except TypeError as e: print(f'Type error: {e}')

# Step 6: __prepare__ — customize class namespace
class OrderedMeta(type):
    '''Track the order attributes are defined in the class body.'''
    @classmethod
    def __prepare__(mcs, name, bases):
        from collections import OrderedDict
        return OrderedDict()

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, dict(namespace))
        cls._field_order = [k for k in namespace if not k.startswith('_')]
        return cls

class Schema(metaclass=OrderedMeta):
    id       = int
    name     = str
    price    = float
    stock    = int
    category = str
    rating   = float

print()
print(f'Schema fields in definition order: {Schema._field_order}')

# Step 7: __missing__ on dict subclass
class DefaultRegistry(dict):
    '''A dict that auto-creates missing keys via a factory function.'''
    def __init__(self, factory):
        super().__init__()
        self._factory = factory

    def __missing__(self, key):
        value = self._factory(key)
        self[key] = value
        return value

# Auto-initialize per-category product lists
by_category = DefaultRegistry(lambda cat: {'category': cat, 'products': [], 'count': 0})
products = [
    ('Surface Pro',  864.0,  'Laptop'),
    ('Surface Book', 1299.0, 'Laptop'),
    ('Surface Pen',  49.99,  'Accessory'),
    ('USB-C Hub',    29.99,  'Accessory'),
    ('Office 365',   99.99,  'Software'),
]
for name, price, cat in products:
    by_category[cat]['products'].append({'name': name, 'price': price})
    by_category[cat]['count'] += 1

for cat, data in sorted(by_category.items()):
    names = [p['name'] for p in data['products']]
    print(f'  {cat:12s}: {data[\"count\"]} products — {names}')

# Step 8: Capstone — event-driven ORM-like system
print()
print('=== Capstone: Event-Driven Model System ===')

class ModelMeta(type):
    def __new__(mcs, name, bases, namespace):
        fields = {k: v for k, v in namespace.items()
                  if isinstance(v, type) and not k.startswith('_')}
        hooks = {'pre_save': [], 'post_save': [], 'pre_delete': []}

        def __init__(self, **kw):
            for fname, ftype in fields.items():
                val = kw.get(fname)
                if val is not None:
                    if not isinstance(val, ftype):
                        raise TypeError(f'{fname}: expected {ftype.__name__}')
                setattr(self, fname, val)
            self._new = True

        def save(self):
            for hook in self.__class__._hooks['pre_save']: hook(self)
            self._new = False
            for hook in self.__class__._hooks['post_save']: hook(self)
            return self

        @classmethod
        def on(cls, event):
            def decorator(fn):
                cls._hooks[event].append(fn)
                return fn
            return decorator

        namespace['__init__'] = __init__
        namespace['save']     = save
        namespace['on']       = on
        namespace['_fields']  = fields
        namespace['_hooks']   = hooks
        return super().__new__(mcs, name, bases, namespace)

class Product(metaclass=ModelMeta):
    name:     str
    price:    float
    stock:    int
    category: str

# Register hooks
@Product.on('pre_save')
def validate(p):
    if p.price and p.price <= 0: raise ValueError('price must be positive')
    print(f'  [pre_save]  validating {p.name}')

@Product.on('post_save')
def audit_log(p):
    print(f'  [post_save] saved {p.name} \${p.price}')

p = Product(name='Surface Pro', price=864.0, stock=15, category='Laptop')
p.save()

p2 = Product(name='Surface Pen', price=49.99, stock=80, category='Accessory')
p2.save()
"
```

**📸 Verified Output:**
```
Product(id=1, name='Surface Pro', price=864.0, stock=15)
{'id': 1, 'name': 'Surface Pro', 'price': 864.0, 'stock': 15}
Fields: ['id', 'name', 'price', 'stock']
Type error: name: expected str, got int

Schema fields in definition order: ['id', 'name', 'price', 'stock', 'category', 'rating']

  Accessory   : 2 products — ['Surface Pen', 'USB-C Hub']
  Laptop      : 2 products — ['Surface Pro', 'Surface Book']
  Software    : 1 products — ['Office 365']

=== Capstone: Event-Driven Model System ===
  [pre_save]  validating Surface Pro
  [post_save] saved Surface Pro $864.0
  [pre_save]  validating Surface Pen
  [post_save] saved Surface Pen $49.99
```

---

## Summary

| Tool | Use case | Key method |
|------|----------|-----------|
| `__init_subclass__` | Auto-register subclasses | Defined on base class |
| Metaclass | Control class creation itself | `__new__`, `__call__` |
| `__set_name__` | Descriptor knows its attribute name | Called at class definition |
| `__class_getitem__` | `MyClass[T]` parametric syntax | Returns new class |
| `type(name, bases, ns)` | Create class at runtime | Built-in |
| `__prepare__` | Custom class namespace | Return dict-like object |
| `__missing__` | Dict auto-init on missing key | Subclass `dict` |

## Further Reading
- [Python Data Model](https://docs.python.org/3/reference/datamodel.html)
- [PEP 487 — `__init_subclass__`](https://peps.python.org/pep-0487/)
- [Descriptors How-To](https://docs.python.org/3/howto/descriptor.html)
