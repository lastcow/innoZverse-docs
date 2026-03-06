# Lab 03: Descriptor Protocol

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Descriptors are the mechanism behind Python's `property`, `classmethod`, `staticmethod`, and attribute access. Mastering the descriptor protocol lets you build reusable validation frameworks, ORM-style field definitions, and lazy computed properties.

## Step 1: The Descriptor Protocol

A descriptor is any object defining `__get__`, `__set__`, or `__delete__`:

```python
class Descriptor:
    def __get__(self, obj, objtype=None):
        print(f"__get__: obj={obj}, objtype={objtype}")
        return 42
    
    def __set__(self, obj, value):
        print(f"__set__: value={value}")
    
    def __delete__(self, obj):
        print(f"__delete__")

class MyClass:
    attr = Descriptor()

mc = MyClass()
_ = mc.attr       # triggers __get__
mc.attr = 10      # triggers __set__
del mc.attr       # triggers __delete__

# Class-level access
_ = MyClass.attr  # __get__ with obj=None
```

> 💡 When accessed on the class (`MyClass.attr`), `obj` is `None` and `objtype` is `MyClass`. This lets descriptors return themselves when accessed via the class.

## Step 2: Data vs Non-Data Descriptors

```python
class DataDescriptor:
    """Has both __get__ and __set__ — overrides instance __dict__."""
    def __get__(self, obj, objtype=None):
        if obj is None: return self
        return obj.__dict__.get('_data_val', 'default')
    
    def __set__(self, obj, value):
        obj.__dict__['_data_val'] = value

class NonDataDescriptor:
    """Only __get__ — instance __dict__ takes priority."""
    def __get__(self, obj, objtype=None):
        if obj is None: return self
        return "from descriptor"

class Demo:
    data = DataDescriptor()
    non_data = NonDataDescriptor()

d = Demo()
print("=== Data Descriptor ===")
d.data = "set via descriptor"
print(d.data)  # "set via descriptor" (goes through __set__)

print("\n=== Non-Data Descriptor ===")
print(d.non_data)  # "from descriptor"
d.__dict__['non_data'] = "from instance dict"
print(d.non_data)  # "from instance dict" (instance wins!)
print(d.__dict__)
```

> 💡 **Priority order:** data descriptors > instance `__dict__` > non-data descriptors. `property` is a data descriptor. Regular functions are non-data descriptors (that's how methods work!).

## Step 3: `__set_name__` — Automatic Name Binding

```python
class Field:
    """Self-naming descriptor — knows its attribute name after class creation."""
    
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = f"_{name}"
        print(f"Field bound: {owner.__name__}.{name}")
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)
    
    def __set__(self, obj, value):
        setattr(obj, self.private_name, value)

class Config:
    host = Field()
    port = Field()
    debug = Field()

# Output from __set_name__ at class definition time
c = Config()
c.host = "localhost"
c.port = 8080
c.debug = True
print(f"{c.host}:{c.port} debug={c.debug}")
```

📸 **Verified Output:**
```
Field bound: Config.host
Field bound: Config.port
Field bound: Config.debug
localhost:8080 debug=True
```

## Step 4: Typed Descriptor Validation Framework

```python
class TypedDescriptor:
    def __init__(self, expected_type, min_val=None, max_val=None):
        self.expected_type = expected_type
        self.min_val = min_val
        self.max_val = max_val
        self.name = None
        self.private = None

    def __set_name__(self, owner, name):
        self.name = name
        self.private = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private, None)

    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} must be {self.expected_type.__name__}, "
                f"got {type(value).__name__}"
            )
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"{self.name} must be >= {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"{self.name} must be <= {self.max_val}")
        setattr(obj, self.private, value)

class Employee:
    name   = TypedDescriptor(str)
    age    = TypedDescriptor(int, min_val=18, max_val=100)
    salary = TypedDescriptor(float, min_val=0.0)

    def __init__(self, name, age, salary):
        self.name = name
        self.age = age
        self.salary = salary

e = Employee("Alice", 30, 75000.0)
print(f"Employee: {e.name}, age={e.age}, salary={e.salary}")

try:
    e.age = 15
except ValueError as ex:
    print(f"ValueError: {ex}")

try:
    e.name = 123
except TypeError as ex:
    print(f"TypeError: {ex}")
```

📸 **Verified Output:**
```
Employee: Alice, age=30, salary=75000.0
ValueError: age must be >= 18
TypeError: name must be str, got int
```

## Step 5: `property` Internals

`property` is itself implemented as a data descriptor:

```python
class LazyProperty:
    """Computed once, cached forever — a non-data descriptor becomes data after first access."""
    
    def __init__(self, func):
        self.func = func
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        # Compute and store in instance dict (shadows this descriptor next time)
        value = self.func(obj)
        obj.__dict__[self.name] = value  # instance dict now shadows descriptor
        return value

class DataProcessor:
    def __init__(self, data):
        self.data = data
    
    @LazyProperty
    def statistics(self):
        print("Computing statistics (expensive!)...")
        return {
            'sum': sum(self.data),
            'mean': sum(self.data) / len(self.data),
            'max': max(self.data),
            'min': min(self.data),
        }

dp = DataProcessor([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
print(dp.statistics)  # Computes once
print(dp.statistics)  # Returns cached value (no "Computing...")
print(dp.statistics)  # Still cached
```

## Step 6: `classmethod` and `staticmethod` as Descriptors

```python
# Reimplement classmethod as a descriptor
class MyClassMethod:
    def __init__(self, func):
        self.func = func
    
    def __get__(self, obj, objtype=None):
        if objtype is None:
            objtype = type(obj)
        # Return a bound version with class as first arg
        def method(*args, **kwargs):
            return self.func(objtype, *args, **kwargs)
        return method

# Reimplement staticmethod as a descriptor
class MyStaticMethod:
    def __init__(self, func):
        self.func = func
    
    def __get__(self, obj, objtype=None):
        return self.func  # No binding at all

class Counter:
    count = 0
    
    @MyClassMethod
    def increment(cls, by=1):
        cls.count += by
        return cls.count
    
    @MyStaticMethod
    def validate(value):
        return isinstance(value, int) and value > 0

Counter.increment(5)
print(f"Count: {Counter.count}")
Counter.increment()
print(f"Count: {Counter.count}")
print(f"validate(3): {Counter.validate(3)}")
print(f"validate(-1): {Counter.validate(-1)}")
```

## Step 7: `__slots__` vs `__dict__` Storage

```python
import sys

class WithDict:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class WithSlots:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Memory comparison
with_dict = WithDict(1, 2)
with_slots = WithSlots(1, 2)

print(f"WithDict size: {sys.getsizeof(with_dict)} bytes")
print(f"WithSlots size: {sys.getsizeof(with_slots)} bytes")
print(f"WithDict has __dict__: {hasattr(with_dict, '__dict__')}")
print(f"WithSlots has __dict__: {hasattr(with_slots, '__dict__')}")

# WithSlots saves memory: no per-instance dict
# Slot descriptors are visible on the class
print("\nSlot descriptors:")
for name in ['x', 'y']:
    desc = WithSlots.__dict__[name]
    print(f"  {name}: {type(desc).__name__}")

# Benchmark: 100k instances
import time
N = 100_000

start = time.perf_counter()
objs_dict = [WithDict(i, i+1) for i in range(N)]
dict_time = time.perf_counter() - start

start = time.perf_counter()
objs_slots = [WithSlots(i, i+1) for i in range(N)]
slots_time = time.perf_counter() - start

print(f"\n100k instances:")
print(f"  WithDict: {dict_time*1000:.1f}ms")
print(f"  WithSlots: {slots_time*1000:.1f}ms")
```

## Step 8: Capstone — Full Validation Framework

```python
from typing import Any, Callable, Optional, Type

class ValidatedField:
    """Production-quality descriptor with multiple validators."""
    
    def __init__(self, field_type: Type, *validators: Callable, default=None, required=True):
        self.field_type = field_type
        self.validators = validators
        self.default = default
        self.required = required
        self.name = None
        self.private = None
    
    def __set_name__(self, owner, name):
        self.name = name
        self.private = f"_vf_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private, self.default)
    
    def __set__(self, obj, value):
        if value is None and not self.required:
            setattr(obj, self.private, None)
            return
        if not isinstance(value, self.field_type):
            raise TypeError(
                f"Field '{self.name}': expected {self.field_type.__name__}, "
                f"got {type(value).__name__}"
            )
        for validator in self.validators:
            validator(self.name, value)
        setattr(obj, self.private, value)

def min_length(n):
    def validate(name, val):
        if len(val) < n:
            raise ValueError(f"'{name}' must have length >= {n}")
    return validate

def in_range(lo, hi):
    def validate(name, val):
        if not (lo <= val <= hi):
            raise ValueError(f"'{name}' must be in [{lo}, {hi}]")
    return validate

def positive(name, val):
    if val <= 0:
        raise ValueError(f"'{name}' must be positive")

class Product:
    name  = ValidatedField(str, min_length(2))
    price = ValidatedField(float, positive, in_range(0.01, 999999.99))
    qty   = ValidatedField(int, positive, in_range(1, 10000))
    sku   = ValidatedField(str, min_length(4), required=False)
    
    def __init__(self, name, price, qty, sku=None):
        self.name = name
        self.price = price
        self.qty = qty
        self.sku = sku

# Valid product
p = Product("Widget Pro", 29.99, 100, sku="WGT-001")
print(f"Product: {p.name} @ ${p.price} (qty={p.qty}, sku={p.sku})")

# Validation failures
tests = [
    ("X", 29.99, 100),      # name too short
    ("Widget", -5.0, 100),  # negative price
    ("Widget", 29.99, 0),   # zero qty
]

for args in tests:
    try:
        Product(*args)
    except (TypeError, ValueError) as e:
        print(f"Validation error: {e}")
```

📸 **Verified Output (descriptor validation):**
```
Employee: Alice, age=30, salary=75000.0
ValueError: age must be >= 18
TypeError: name must be str, got int
```

## Summary

| Concept | Mechanism | Use Case |
|---|---|---|
| Data descriptor | `__get__` + `__set__` | Validated attributes |
| Non-data descriptor | `__get__` only | Methods, lazy properties |
| `__set_name__` | Called at class creation | Self-naming fields |
| `property` internals | Data descriptor | Computed attributes |
| `classmethod` | Non-data descriptor with binding | Factory methods |
| `__slots__` | Slot descriptors | Memory optimization |
| Validation framework | `TypedDescriptor` + validators | ORM/Pydantic-like models |
