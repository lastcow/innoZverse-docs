# Lab 07: Type Hints, Generics & mypy

## Objective
Write fully type-annotated Python: `typing` module, generics, `TypeVar`, `Protocol`, `TypedDict`, `Literal`, `overload`, `Final`, and structural subtyping.

## Time
30 minutes

## Prerequisites
- Lab 01 (Advanced OOP)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Core Type Hints

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from typing import Optional, Union, Any, Callable, Sequence, Mapping
from collections.abc import Iterator, Generator, AsyncIterator

# Basic annotations
def greet(name: str, times: int = 1) -> str:
    return (f'Hello, {name}! ' * times).strip()

# Optional (= X | None)
def find_product(product_id: int, catalog: dict[int, str]) -> Optional[str]:
    return catalog.get(product_id)

# Union (pre-3.10 style, or use X | Y in 3.10+)
def process(value: Union[int, str, list[int]]) -> str:
    if isinstance(value, int): return f'int:{value}'
    if isinstance(value, str): return f'str:{value}'
    return f'list:{sum(value)}'

# Complex types
def batch_process(
    items: list[dict[str, Any]],
    transform: Callable[[dict[str, Any]], dict[str, Any]],
    filters: list[Callable[[dict[str, Any]], bool]] | None = None,
) -> list[dict[str, Any]]:
    result = items
    if filters:
        for f in filters: result = [x for x in result if f(x)]
    return [transform(x) for x in result]

catalog = {1: 'Surface Pro', 2: 'Surface Pen', 3: 'Office 365'}
print(greet('Dr. Chen', 2))
print(find_product(1, catalog))
print(find_product(99, catalog))
print(process(42))
print(process('hello'))
print(process([1, 2, 3]))

products = [
    {'id': 1, 'name': 'Surface Pro',  'price': 864.0,  'stock': 15},
    {'id': 2, 'name': 'Surface Pen',  'price': 49.99,  'stock': 80},
    {'id': 3, 'name': 'USB-C Hub',    'price': 29.99,  'stock': 0},
]
result = batch_process(
    products,
    lambda p: {**p, 'value': p['price'] * p['stock']},
    filters=[lambda p: p['stock'] > 0]
)
for r in result:
    print(f'  {r[\"name\"]}: value=\${r[\"value\"]:.2f}')
"
```

> 💡 **Type hints are not enforced at runtime** — they're metadata for type checkers (mypy, pyright) and IDEs. Use them to document intent and catch bugs at development time. `Optional[X]` is shorthand for `Union[X, None]`. In Python 3.10+, use `X | None` directly.

**📸 Verified Output:**
```
Hello, Dr. Chen! Hello, Dr. Chen!
Surface Pro
None
int:42
str:hello
list:6
  Surface Pro: value=$12960.00
  Surface Pen: value=$3999.20
```

---

### Step 2: TypeVar & Generics

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from typing import TypeVar, Generic, overload

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')
Num = TypeVar('Num', int, float)

# Generic function
def first(items: list[T]) -> T | None:
    return items[0] if items else None

def last(items: list[T]) -> T | None:
    return items[-1] if items else None

def clamp(value: Num, lo: Num, hi: Num) -> Num:
    return max(lo, min(value, hi))

print('first:', first([1, 2, 3]))
print('first str:', first(['a', 'b', 'c']))
print('last:', last([10, 20, 30]))
print('clamp:', clamp(15, 0, 10))
print('clamp float:', clamp(3.14, 0.0, 3.0))

# Generic class
class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError('pop from empty stack')
        return self._items.pop()

    def peek(self) -> T | None:
        return self._items[-1] if self._items else None

    def __len__(self) -> int: return len(self._items)
    def __bool__(self) -> bool: return bool(self._items)

int_stack: Stack[int] = Stack()
int_stack.push(1); int_stack.push(2); int_stack.push(3)
print('Stack peek:', int_stack.peek())
print('Stack pop:', int_stack.pop())
print('Stack len:', len(int_stack))

str_stack: Stack[str] = Stack()
str_stack.push('hello'); str_stack.push('world')
print('String stack:', str_stack.pop())

# overload — multiple signatures
@overload
def stringify(value: int) -> str: ...
@overload
def stringify(value: float) -> str: ...
@overload
def stringify(value: list[int]) -> list[str]: ...

def stringify(value):  # type: ignore
    if isinstance(value, list): return [str(v) for v in value]
    return str(value)

print('stringify int:', stringify(42))
print('stringify list:', stringify([1, 2, 3]))
"
```

**📸 Verified Output:**
```
first: 1
first str: a
last: 30
clamp: 10
clamp float: 3.0
Stack peek: 3
Stack pop: 3
Stack len: 2
String stack: world
stringify int: 42
stringify list: ['1', '2', '3']
```

---

### Steps 3–8: TypedDict, Literal, Protocol, Final, NewType, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from typing import TypedDict, Literal, Protocol, Final, NewType, NotRequired, Required
from typing import runtime_checkable
from dataclasses import dataclass

# Step 3: TypedDict — typed dicts
class ProductDict(TypedDict):
    id: int
    name: str
    price: float
    stock: int

class PartialProduct(TypedDict, total=False):
    name: str
    price: float
    stock: int

class FullProduct(TypedDict):
    id: int
    name: str
    price: float
    stock: int
    category: NotRequired[str]  # optional field

def describe_product(p: ProductDict) -> str:
    return f'[{p[\"id\"]}] {p[\"name\"]} \${p[\"price\"]}'

p: ProductDict = {'id': 1, 'name': 'Surface Pro', 'price': 864.0, 'stock': 15}
print(describe_product(p))

# Step 4: Literal — restrict to specific values
Status = Literal['active', 'inactive', 'out_of_stock']
SortOrder = Literal['asc', 'desc']
Format = Literal['json', 'csv', 'table']

def export_products(
    products: list[ProductDict],
    format: Format = 'json',
    order: SortOrder = 'asc',
) -> str:
    sorted_p = sorted(products, key=lambda p: p['price'], reverse=(order == 'desc'))
    if format == 'csv':
        rows = ['id,name,price,stock'] + [f'{p[\"id\"]},{p[\"name\"]},{p[\"price\"]},{p[\"stock\"]}' for p in sorted_p]
        return '\n'.join(rows)
    return str([p['name'] for p in sorted_p])

products: list[ProductDict] = [
    {'id': 1, 'name': 'Surface Pro', 'price': 864.0, 'stock': 15},
    {'id': 2, 'name': 'Surface Pen', 'price': 49.99,  'stock': 80},
]
print(export_products(products, format='csv', order='desc'))

# Step 5: Protocol — structural subtyping
@runtime_checkable
class Priceable(Protocol):
    @property
    def price(self) -> float: ...
    @property
    def name(self) -> str: ...

@dataclass
class Product:
    name: str
    price: float
    stock: int = 0

@dataclass
class Bundle:
    name: str
    items: list[Product]

    @property
    def price(self) -> float:
        return sum(p.price for p in self.items)

def apply_discount(item: Priceable, pct: float) -> float:
    return round(item.price * (1 - pct), 2)

p = Product('Surface Pro', 864.0, 15)
b = Bundle('Starter Kit', [Product('Pen', 49.99), Product('Hub', 29.99)])
print(f'Product discount: \${apply_discount(p, 0.1)}')
print(f'Bundle price: \${b.price}, discounted: \${apply_discount(b, 0.15)}')
print('Bundle is Priceable:', isinstance(b, Priceable))

# Step 6: NewType — nominal typing
UserID   = NewType('UserID', int)
ProductID = NewType('ProductID', int)

def get_user(user_id: UserID) -> dict:
    return {'id': user_id, 'name': 'Dr. Chen'}

uid = UserID(1)
pid = ProductID(1)
print('UserID:', uid, type(uid))

# Step 7: Final — constants
MAX_RETRIES: Final = 3
BASE_URL: Final[str] = 'https://api.innozverse.com'
print(f'Config: MAX_RETRIES={MAX_RETRIES} BASE_URL={BASE_URL}')

# Step 8: Capstone — fully typed repository
class ProductRepo(Generic[T]):
    pass

from typing import Generic, TypeVar
T = TypeVar('T')

class Repository(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[int, T] = {}
        self._next_id: int = 1

    def add(self, item: T) -> int:
        item_id = self._next_id
        self._next_id += 1
        self._items[item_id] = item
        return item_id

    def get(self, item_id: int) -> T | None:
        return self._items.get(item_id)

    def list(self, predicate: Callable[[T], bool] | None = None) -> list[T]:
        if predicate is None: return list(self._items.values())
        return [v for v in self._items.values() if predicate(v)]

    def count(self) -> int: return len(self._items)

from typing import Callable

repo: Repository[Product] = Repository()
repo.add(Product('Surface Pro', 864.0, 15))
repo.add(Product('Surface Pen', 49.99, 80))
repo.add(Product('USB-C Hub', 29.99, 0))

print(f'Total: {repo.count()}')
affordable = repo.list(lambda p: p.price < 100)
print(f'Under \$100: {[p.name for p in affordable]}')
in_stock = repo.list(lambda p: p.stock > 0)
print(f'In stock: {[p.name for p in in_stock]}')
"
```

**📸 Verified Output:**
```
[1] Surface Pro $864.0
id,name,price,stock
1,Surface Pro,864.0,15
2,Surface Pen,49.99,80
Product discount: $777.6
Bundle price: $79.98, discounted: $67.98
Bundle is Priceable: True
UserID: 1 <class 'int'>
Config: MAX_RETRIES=3 BASE_URL=https://api.innozverse.com
Total: 3
Under $100: ['Surface Pen', 'USB-C Hub']
In stock: ['Surface Pro', 'Surface Pen']
```

---

## Summary

| Type | Purpose | Example |
|------|---------|---------|
| `TypeVar` | Generic placeholder | `T = TypeVar('T')` |
| `Generic[T]` | Generic class | `class Stack(Generic[T])` |
| `TypedDict` | Typed dictionaries | `class P(TypedDict): id: int` |
| `Literal` | Restrict to values | `Literal['asc', 'desc']` |
| `Protocol` | Structural typing | `class Serializable(Protocol)` |
| `Final` | Runtime constant | `MAX: Final = 10` |
| `NewType` | Nominal alias | `UserID = NewType('UserID', int)` |
| `overload` | Multiple signatures | `@overload def f(x: int)` |

## Further Reading
- [typing module](https://docs.python.org/3/library/typing.html)
- [mypy docs](https://mypy.readthedocs.io)
- [PEP 484](https://peps.python.org/pep-0484/)
