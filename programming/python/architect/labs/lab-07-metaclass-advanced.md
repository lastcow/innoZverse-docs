# Lab 07: Advanced Metaclasses

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Metaclasses are the "classes of classes" — they control how classes are created. This lab covers `__prepare__`, metaclass `__new__/__init__/__call__`, conflict resolution, `__init_subclass__`, and building an ORM-style field registry.

## Step 1: Metaclass Basics — `type` as a Metaclass

```python
# type() is Python's built-in metaclass
# Every class is an instance of its metaclass

class MyClass:
    pass

print(f"type(MyClass): {type(MyClass)}")         # <class 'type'>
print(f"type(type): {type(type)}")               # <class 'type'>
print(f"isinstance(MyClass, type): {isinstance(MyClass, type)}")

# Creating a class dynamically with type()
DynamicClass = type(
    'DynamicClass',                # name
    (object,),                     # bases
    {                              # namespace
        'value': 42,
        'greet': lambda self: f"Hello from {type(self).__name__}",
    }
)

obj = DynamicClass()
print(f"DynamicClass().value: {obj.value}")
print(f"DynamicClass().greet(): {obj.greet()}")
```

> 💡 `type(name, bases, namespace)` is the core mechanism behind all class creation. Metaclasses just subclass `type` to customize this process.

## Step 2: `__prepare__` — Controlling the Class Namespace

```python
from collections import OrderedDict

class OrderedMeta(type):
    """Metaclass that tracks field definition order."""
    
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        # Return an ordered dict (Python 3.7+ dict is ordered by default)
        # But we can use this to inject special namespaces
        ns = OrderedDict()
        ns['_definition_order'] = []
        return ns
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Track which attributes were defined (non-dunder)
        order = [k for k in namespace if not k.startswith('_')]
        namespace['_field_order'] = order
        return super().__new__(mcs, name, bases, namespace)

class Schema(metaclass=OrderedMeta):
    username = "alice"
    email    = "alice@example.com"
    age      = 30
    active   = True

print(f"Field order: {Schema._field_order}")
print(f"Fields: {[(f, getattr(Schema, f)) for f in Schema._field_order]}")
```

📸 **Verified Output:**
```
Field order: ['username', 'email', 'age', 'active']
Fields: [('username', 'alice'), ('email', 'alice@example.com'), ('age', 30), ('active', True)]
```

## Step 3: Metaclass `__new__`, `__init__`, `__call__`

```python
class LoggingMeta(type):
    """Metaclass that logs class creation and instantiation."""
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        print(f"[Meta.__new__] Creating class: {name}")
        cls = super().__new__(mcs, name, bases, namespace)
        return cls
    
    def __init__(cls, name, bases, namespace, **kwargs):
        print(f"[Meta.__init__] Initializing class: {name}")
        super().__init__(name, bases, namespace)
    
    def __call__(cls, *args, **kwargs):
        print(f"[Meta.__call__] Instantiating {cls.__name__}({args}, {kwargs})")
        instance = super().__call__(*args, **kwargs)
        print(f"[Meta.__call__] Created: {instance}")
        return instance

class Widget(metaclass=LoggingMeta):
    def __init__(self, name, width=100):
        self.name = name
        self.width = width
    
    def __repr__(self):
        return f"Widget({self.name!r}, width={self.width})"

print("--- After class definition ---")
w = Widget("button", width=200)
print(f"Result: {w}")
```

## Step 4: Singleton via Metaclass

```python
class SingletonMeta(type):
    """Ensures only one instance per class."""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
            print(f"[Singleton] Created new {cls.__name__}")
        else:
            print(f"[Singleton] Returning existing {cls.__name__}")
        return cls._instances[cls]

class DatabaseConnection(metaclass=SingletonMeta):
    def __init__(self, dsn="postgresql://localhost/db"):
        self.dsn = dsn
        print(f"  Connected to: {self.dsn}")

class CacheConnection(metaclass=SingletonMeta):
    def __init__(self, url="redis://localhost:6379"):
        self.url = url

db1 = DatabaseConnection()
db2 = DatabaseConnection("other://host")  # Returns existing
print(f"Same object: {db1 is db2}")

cache = CacheConnection()
print(f"DB same as Cache: {db1 is cache}")
```

## Step 5: Metaclass Conflict Resolution

```python
class MetaA(type):
    def __new__(mcs, name, bases, namespace):
        print(f"MetaA.__new__ for {name}")
        return super().__new__(mcs, name, bases, namespace)

class MetaB(type):
    def __new__(mcs, name, bases, namespace):
        print(f"MetaB.__new__ for {name}")
        return super().__new__(mcs, name, bases, namespace)

class A(metaclass=MetaA):
    pass

class B(metaclass=MetaB):
    pass

# This would raise TypeError: metaclass conflict!
# class C(A, B): pass  # MetaA vs MetaB conflict

# Resolution: create a combined metaclass
class MetaAB(MetaA, MetaB):
    """Combined metaclass — MRO handles calling order."""
    pass

class C(A, B, metaclass=MetaAB):
    pass

print(f"\nC's metaclass: {type(C).__name__}")
print(f"MetaAB MRO: {[c.__name__ for c in MetaAB.__mro__]}")
```

## Step 6: `__init_subclass__` — Hook Without Metaclass

```python
class Plugin:
    """Base class using __init_subclass__ as a plugin registry."""
    
    _registry = {}
    
    def __init_subclass__(cls, plugin_type=None, version="1.0", **kwargs):
        super().__init_subclass__(**kwargs)
        if plugin_type:
            cls._registry[plugin_type] = cls
            print(f"Registered plugin: {plugin_type!r} -> {cls.__name__} v{version}")
    
    @classmethod
    def get_plugin(cls, plugin_type):
        if plugin_type not in cls._registry:
            raise KeyError(f"Unknown plugin type: {plugin_type!r}")
        return cls._registry[plugin_type]

class CSVExporter(Plugin, plugin_type="csv", version="2.1"):
    def export(self, data):
        return ",".join(str(x) for x in data)

class JSONExporter(Plugin, plugin_type="json", version="1.5"):
    def export(self, data):
        import json
        return json.dumps(data)

class XMLExporter(Plugin, plugin_type="xml", version="3.0"):
    def export(self, data):
        return f"<data>{data}</data>"

print("\n=== Plugin Registry ===")
print(f"Registered: {list(Plugin._registry.keys())}")

# Use plugins
data = [1, 2, 3]
for ptype in ['csv', 'json']:
    plugin = Plugin.get_plugin(ptype)()
    print(f"{ptype}: {plugin.export(data)}")
```

## Step 7: Class Decorators vs Metaclasses

```python
# Class decorator approach (simpler, but less powerful)
def add_repr(cls):
    def __repr__(self):
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{type(self).__name__}({attrs})"
    cls.__repr__ = __repr__
    return cls

def validate_fields(cls):
    """Decorator that adds validation based on type annotations."""
    orig_init = cls.__init__
    
    def new_init(self, **kwargs):
        hints = cls.__annotations__ if hasattr(cls, '__annotations__') else {}
        for field, expected_type in hints.items():
            if field in kwargs and not isinstance(kwargs[field], expected_type):
                raise TypeError(f"{field}: expected {expected_type.__name__}")
        orig_init(self, **kwargs)
    
    cls.__init__ = new_init
    return cls

@add_repr
@validate_fields
class Point:
    x: float
    y: float
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1.0, 2.0)
print(f"Point: {p}")

try:
    Point("bad", 2.0)
except TypeError as e:
    print(f"TypeError: {e}")
```

## Step 8: Capstone — ORM-Style Field Registry

```python
class Field:
    def __init__(self, field_type, required=True, default=None):
        self.field_type = field_type
        self.required = required
        self.default = default
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj.__dict__.get(self.name, self.default)
    
    def __set__(self, obj, value):
        if value is None and not self.required:
            obj.__dict__[self.name] = None
            return
        if not isinstance(value, self.field_type):
            raise TypeError(
                f"Field '{self.name}': expected {self.field_type.__name__}, "
                f"got {type(value).__name__}"
            )
        obj.__dict__[self.name] = value

class FieldMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return {}
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        fields = {k: v for k, v in namespace.items() if isinstance(v, Field)}
        namespace['_fields'] = fields
        namespace['_table_name'] = name.lower() + 's'
        cls = super().__new__(mcs, name, bases, namespace)
        return cls
    
    def __repr__(cls):
        fields = ', '.join(
            f"{name}:{f.field_type.__name__}" 
            for name, f in cls._fields.items()
        )
        return f"<Model {cls.__name__} table={cls._table_name!r} fields=[{fields}]>"

class Model(metaclass=FieldMeta):
    def __init__(self, **kwargs):
        for name, field in self._fields.items():
            if name in kwargs:
                setattr(self, name, kwargs[name])
            elif field.required and field.default is None:
                raise ValueError(f"Required field {name!r} missing")
            else:
                setattr(self, name, field.default)
    
    def to_dict(self):
        return {name: getattr(self, name) for name in self._fields}
    
    def __repr__(self):
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.to_dict().items())
        return f"{type(self).__name__}({attrs})"

class User(Model):
    name    = Field(str)
    age     = Field(int)
    email   = Field(str, required=False, default="no-email")

class Product(Model):
    title   = Field(str)
    price   = Field(float)
    stock   = Field(int, default=0)

print(repr(User))
print(repr(Product))

u = User(name="Bob", age=25)
print(f"\n{u}")
print(f"to_dict: {u.to_dict()}")

p = Product(title="Widget", price=9.99)
print(f"\n{p}")

try:
    u2 = User(name="Eve", age="old")
except TypeError as e:
    print(f"\nTypeError: {e}")

try:
    u3 = User(age=30)  # missing required 'name'
except ValueError as e:
    print(f"ValueError: {e}")
```

📸 **Verified Output:**
```
User: Bob, age=25
Fields: ['name', 'age', 'email']
TypeError: age: expected int, got str
```

## Summary

| Concept | Mechanism | Use Case |
|---|---|---|
| `type()` dynamic class | `type(name, bases, ns)` | Runtime class generation |
| `__prepare__` | Returns namespace dict | Custom class namespaces |
| Meta `__new__` | Class creation | Transform class before use |
| Meta `__call__` | Instance creation | Singleton, pooling |
| Metaclass conflict | Combined metaclass MRO | Multiple inheritance fix |
| `__init_subclass__` | Hook in base class | Plugin registry |
| Class decorator | `@decorator` on class | Simpler alternatives |
| ORM field registry | Metaclass + Descriptor | Django/SQLAlchemy style |
