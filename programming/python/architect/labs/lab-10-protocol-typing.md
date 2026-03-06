# Lab 10: Protocol & Advanced Typing

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Python's `typing.Protocol` enables structural subtyping ("duck typing" with static type checking). This lab covers `Protocol`, `ParamSpec`, `TypeVarTuple`, `Concatenate`, variance, and `overload` for building type-safe, flexible APIs.

## Step 1: `typing.Protocol` — Structural Subtyping

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Drawable(Protocol):
    def draw(self) -> str: ...
    def area(self) -> float: ...

class Circle:
    def __init__(self, radius: float):
        self.radius = radius
    def draw(self) -> str:
        return f"Circle(r={self.radius})"
    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2

class Square:
    def __init__(self, side: float):
        self.side = side
    def draw(self) -> str:
        return f"Square(s={self.side})"
    def area(self) -> float:
        return self.side ** 2

# No inheritance needed — structural compatibility!
shapes = [Circle(5), Square(4)]
for shape in shapes:
    print(f"{shape.draw()}: area={shape.area():.2f}")
    print(f"  isinstance(Drawable): {isinstance(shape, Drawable)}")
```

📸 **Verified Output:**
```
Circle(r=5): area=78.54
  isinstance(Drawable): True
Square(s=4): area=16.00
  isinstance(Drawable): True
```

> 💡 `@runtime_checkable` allows `isinstance()` checks at runtime. Without it, `Protocol` is only checked by static type checkers like mypy. Note: runtime checks only verify method existence, not signatures.

## Step 2: Protocol with `__call__`

```python
from typing import Protocol

class Transformer(Protocol):
    def __call__(self, data: list) -> list: ...

class Sorter:
    def __call__(self, data: list) -> list:
        return sorted(data)

class Reverser:
    def __call__(self, data: list) -> list:
        return list(reversed(data))

class Deduplicator:
    def __call__(self, data: list) -> list:
        seen = set()
        return [x for x in data if not (x in seen or seen.add(x))]

def apply_pipeline(data: list, transformers: list) -> list:
    result = data
    for t in transformers:
        result = t(result)
    return result

data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
pipeline = [Deduplicator(), Sorter()]
result = apply_pipeline(data, pipeline)
print(f"Original: {data}")
print(f"Pipeline result: {result}")

# Lambda also satisfies Transformer protocol (has __call__)
pipeline2 = [lambda x: [i * 2 for i in x], Sorter()]
result2 = apply_pipeline([3, 1, 4, 1, 5], pipeline2)
print(f"Doubled+sorted: {result2}")
```

## Step 3: Generic Protocols

```python
from typing import Protocol, TypeVar, Generic

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')

class Repository(Protocol[T]):
    """Generic repository protocol — database agnostic."""
    def get(self, id: int) -> T: ...
    def save(self, entity: T) -> None: ...
    def delete(self, id: int) -> None: ...
    def list_all(self) -> list[T]: ...

class User:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
    def __repr__(self):
        return f"User(id={self.id}, name={self.name!r})"

class InMemoryUserRepo:
    """Implements Repository[User] structurally."""
    
    def __init__(self):
        self._data: dict[int, User] = {}
    
    def get(self, id: int) -> User:
        return self._data[id]
    
    def save(self, entity: User) -> None:
        self._data[entity.id] = entity
    
    def delete(self, id: int) -> None:
        del self._data[id]
    
    def list_all(self) -> list[User]:
        return list(self._data.values())

def create_users(repo: Repository, names: list[str]) -> list[User]:
    """Works with any Repository[User] implementation."""
    users = [User(i, name) for i, name in enumerate(names, 1)]
    for user in users:
        repo.save(user)
    return users

repo = InMemoryUserRepo()
users = create_users(repo, ["Alice", "Bob", "Charlie"])
print(f"Saved users: {repo.list_all()}")
print(f"Get user 2: {repo.get(2)}")
repo.delete(2)
print(f"After delete: {repo.list_all()}")
```

## Step 4: Covariant and Contravariant TypeVar

```python
from typing import TypeVar, Generic, Protocol

# Covariant: Producer[Cat] is subtype of Producer[Animal]
# (you can use a Cat producer where Animal producer is expected)
T_co = TypeVar('T_co', covariant=True)

# Contravariant: Consumer[Animal] is subtype of Consumer[Cat]  
# (you can use an Animal consumer where Cat consumer is expected)
T_contra = TypeVar('T_contra', contravariant=True)

class Producer(Protocol[T_co]):
    def produce(self) -> T_co: ...

class Consumer(Protocol[T_contra]):
    def consume(self, item: T_contra) -> None: ...

class Animal:
    def speak(self): return "..."

class Cat(Animal):
    def speak(self): return "meow"

class CatFactory:
    def produce(self) -> Cat:
        return Cat()

class AnimalConsumer:
    def consume(self, item: Animal) -> None:
        print(f"Consuming: {item.speak()}")

# Covariance: CatFactory satisfies Producer[Animal]
# (Cat is subtype of Animal → Producer[Cat] <: Producer[Animal])
factory: CatFactory = CatFactory()
animal = factory.produce()
print(f"Produced: {animal.speak()}")

# Contravariance: AnimalConsumer satisfies Consumer[Cat]
# (Animal is supertype of Cat → Consumer[Animal] <: Consumer[Cat])
consumer: AnimalConsumer = AnimalConsumer()
consumer.consume(Cat())
```

## Step 5: `ParamSpec` — Preserving Callable Signatures

```python
from typing import Callable, TypeVar, ParamSpec
import functools

P = ParamSpec('P')
R = TypeVar('R')

def log_calls(func: Callable[P, R]) -> Callable[P, R]:
    """Decorator that preserves the original function's signature."""
    
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"Calling {func.__name__}({args}, {kwargs})")
        result = func(*args, **kwargs)
        print(f"  → {result!r}")
        return result
    
    return wrapper

def retry(times: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Retry decorator preserving signature."""
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == times - 1:
                        raise
                    print(f"  Attempt {attempt+1} failed: {e}, retrying...")
        return wrapper
    return decorator

@log_calls
def add(x: int, y: int, *, scale: float = 1.0) -> float:
    return (x + y) * scale

@retry(3)
@log_calls
def flaky_operation(n: int) -> str:
    import random
    if random.random() < 0.3:
        raise ValueError("Random failure")
    return f"success({n})"

result = add(3, 4, scale=2.0)
print(f"\nadd result: {result}")
```

## Step 6: `TypeVarTuple` — Variadic Generics

```python
from typing import TypeVarTuple, Unpack, Generic, overload

Ts = TypeVarTuple('Ts')

# TypeVarTuple captures multiple types
# Useful for tuple-returning functions, zip-like operations

from typing import Tuple

def first_elements(*lists: Unpack[Ts]) -> tuple:
    """Return first element from each input list."""
    return tuple(lst[0] if lst else None for lst in lists)

result = first_elements([1, 2, 3], ["a", "b"], [True, False])
print(f"first_elements: {result}")

# Practical: type-safe map over tuple
def map_tuple(func, data: tuple) -> tuple:
    return tuple(func(x) for x in data)

nums = (1, 2, 3, 4, 5)
squared = map_tuple(lambda x: x**2, nums)
print(f"squared tuple: {squared}")
```

## Step 7: `overload` — Multiple Signatures

```python
from typing import overload, Union

@overload
def process(data: str) -> str: ...
@overload
def process(data: list) -> list: ...
@overload
def process(data: int) -> int: ...

def process(data):
    """Smart processor that handles multiple types."""
    if isinstance(data, str):
        return data.upper()
    elif isinstance(data, list):
        return [x * 2 for x in data]
    elif isinstance(data, int):
        return data ** 2
    else:
        raise TypeError(f"Unsupported type: {type(data)}")

print(f"process('hello'): {process('hello')}")
print(f"process([1,2,3]): {process([1,2,3])}")
print(f"process(5): {process(5)}")

# Overload with Protocol
class Stringifiable(Protocol):
    def to_string(self) -> str: ...
    def __str__(self) -> str: ...

class Temperature:
    def __init__(self, celsius: float):
        self.celsius = celsius
    
    def to_string(self) -> str:
        return f"{self.celsius}°C ({self.celsius * 9/5 + 32}°F)"
    
    def __str__(self) -> str:
        return self.to_string()

t = Temperature(100)
print(f"Temperature: {t}")
```

## Step 8: Capstone — Type-Safe Plugin Framework

```python
from typing import Protocol, TypeVar, Generic, Callable, runtime_checkable
from abc import abstractmethod
import functools

# Define protocols for plugin system
@runtime_checkable
class Validator(Protocol):
    def validate(self, data: dict) -> tuple[bool, list[str]]: ...
    def name(self) -> str: ...

@runtime_checkable  
class Processor(Protocol):
    def process(self, data: dict) -> dict: ...

@runtime_checkable
class Reporter(Protocol):
    def report(self, results: list[dict]) -> str: ...

T = TypeVar('T')

class Pipeline(Generic[T]):
    """Type-safe processing pipeline."""
    
    def __init__(self):
        self._validators: list[Validator] = []
        self._processors: list[Processor] = []
        self._reporters: list[Reporter] = []
    
    def add_validator(self, validator: Validator) -> 'Pipeline[T]':
        if not isinstance(validator, Validator):
            raise TypeError(f"Expected Validator, got {type(validator).__name__}")
        self._validators.append(validator)
        return self
    
    def add_processor(self, processor: Processor) -> 'Pipeline[T]':
        self._processors.append(processor)
        return self
    
    def add_reporter(self, reporter: Reporter) -> 'Pipeline[T]':
        self._reporters.append(reporter)
        return self
    
    def run(self, records: list[dict]) -> list[dict]:
        results = []
        errors = 0
        
        for record in records:
            # Validate
            all_valid = True
            for validator in self._validators:
                valid, msgs = validator.validate(record)
                if not valid:
                    print(f"  [INVALID] {validator.name()}: {msgs}")
                    all_valid = False
                    errors += 1
            
            if not all_valid:
                continue
            
            # Process
            processed = record.copy()
            for processor in self._processors:
                processed = processor.process(processed)
            
            results.append(processed)
        
        print(f"\nPipeline: {len(records)} in, {len(results)} out, {errors} errors")
        return results

# Concrete implementations (structural — no inheritance needed)
class RequiredFieldsValidator:
    def __init__(self, fields: list[str]):
        self._fields = fields
    
    def validate(self, data: dict) -> tuple[bool, list[str]]:
        missing = [f for f in self._fields if f not in data]
        return (len(missing) == 0), [f"Missing: {m}" for m in missing]
    
    def name(self) -> str:
        return f"RequiredFields({self._fields})"

class NormalizeProcessor:
    def process(self, data: dict) -> dict:
        result = {}
        for k, v in data.items():
            result[k.lower().strip()] = v.strip() if isinstance(v, str) else v
        return result

class EnrichProcessor:
    def process(self, data: dict) -> dict:
        return {**data, 'processed': True, 'ts': __import__('time').time()}

class SummaryReporter:
    def report(self, results: list[dict]) -> str:
        return f"Processed {len(results)} records successfully"

# Build and run pipeline
pipeline: Pipeline[dict] = Pipeline()
pipeline.add_validator(RequiredFieldsValidator(['name', 'email']))
pipeline.add_processor(NormalizeProcessor())
pipeline.add_processor(EnrichProcessor())
pipeline.add_reporter(SummaryReporter())

records = [
    {'name': '  Alice  ', 'email': 'alice@example.com'},
    {'name': 'Bob', 'email': 'bob@example.com'},
    {'email': 'orphan@example.com'},  # missing 'name'
    {'name': 'Carol', 'email': 'carol@example.com'},
]

results = pipeline.run(records)
for r in results:
    print(f"  {r['name']} <{r['email']}> processed={r['processed']}")
```

📸 **Verified Output:**
```
Circle(r=5): area=78.54
  isinstance(Drawable): True
Square(s=4): area=16.00
  isinstance(Drawable): True
```

## Summary

| Concept | API | Use Case |
|---|---|---|
| Structural typing | `Protocol` | Duck typing with type safety |
| Runtime checks | `@runtime_checkable` | `isinstance` with Protocol |
| Callable protocol | `Protocol.__call__` | Type-safe higher-order functions |
| Generic protocol | `Protocol[T]` | Type-parameterized interfaces |
| Covariance | `TypeVar(covariant=True)` | Producer types |
| Contravariance | `TypeVar(contravariant=True)` | Consumer types |
| `ParamSpec` | `P.args`, `P.kwargs` | Decorator signature preservation |
| `overload` | Multiple signatures | Type-aware dispatch |
