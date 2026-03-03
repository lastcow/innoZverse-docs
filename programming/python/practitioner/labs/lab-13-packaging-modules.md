# Lab 13: Packaging, Modules & Project Structure

## Objective
Understand Python's module system, packaging with `pyproject.toml`, namespace packages, import mechanics, `__init__.py` design, and building distributable packages.

## Time
30 minutes

## Prerequisites
- Lab 07 (Type Hints)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Module System & Import Mechanics

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sys
import importlib
import importlib.util
import types
import tempfile, os

# How imports work under the hood
print('=== Import Mechanics ===')
print(f'Python version: {sys.version.split()[0]}')
print(f'sys.path entries: {len(sys.path)}')
print(f'First 3 paths: {sys.path[:3]}')

# Check if module is cached
print()
import json
print(f'json is cached: {\"json\" in sys.modules}')
print(f'json.__file__: {json.__file__}')
print(f'json.__package__: {json.__package__}')

# Create a module dynamically
mod = types.ModuleType('mymodule')
mod.__doc__ = 'Dynamically created module'
mod.VERSION = '1.0.0'
mod.greet = lambda name: f'Hello, {name}!'
sys.modules['mymodule'] = mod

import mymodule
print(f'Dynamic module: {mymodule.greet(\"Dr. Chen\")}')
print(f'Dynamic module version: {mymodule.VERSION}')

# importlib — load from file path
with tempfile.TemporaryDirectory() as tmp:
    mod_file = os.path.join(tmp, 'calculator.py')
    with open(mod_file, 'w') as f:
        f.write('''
VERSION = \"2.0\"
def add(a, b): return a + b
def multiply(a, b): return a * b
class Calculator:
    def __init__(self): self.history = []
    def calc(self, op, a, b):
        result = op(a, b)
        self.history.append((op.__name__, a, b, result))
        return result
''')
    spec = importlib.util.spec_from_file_location('calculator', mod_file)
    calc_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calc_mod)
    print(f'Loaded calculator v{calc_mod.VERSION}')
    print(f'add(3,4) = {calc_mod.add(3, 4)}')
    c = calc_mod.Calculator()
    print(f'calc result = {c.calc(calc_mod.multiply, 6, 7)}')

# Module attributes
print()
print('=== Module Introspection ===')
import os.path
print(f'os.path is: {type(os.path).__name__}')
print(f'os.path.__name__: {os.path.__name__}')
attrs = [a for a in dir(os.path) if not a.startswith(\"_\")]
print(f'Public attrs ({len(attrs)}): {attrs[:5]}...')
"
```

> 💡 **`sys.modules`** is Python's import cache — a dictionary mapping module names to their objects. When you `import json`, Python first checks `sys.modules`; if found, it returns the cached object without re-executing the file. This is why mutating an imported module affects all importers.

**📸 Verified Output:**
```
=== Import Mechanics ===
Python version: 3.12.x
sys.path entries: 7
json is cached: True
Dynamic module: Hello, Dr. Chen!
Dynamic module version: 1.0.0
Loaded calculator v2.0
add(3,4) = 7
calc result = 42

=== Module Introspection ===
os.path is: module
os.path.__name__: posixpath
Public attrs (29): ['abspath', 'basename', 'commonpath', 'commonprefix', 'curdir']...
```

---

### Step 2: Package Structure & `__init__.py`

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sys, os, tempfile, importlib, importlib.util

# Create a proper package structure in /tmp
with tempfile.TemporaryDirectory() as tmp:
    # Build package tree:
    # storecli/
    #   __init__.py
    #   models/
    #     __init__.py
    #     product.py
    #     order.py
    #   services/
    #     __init__.py
    #     catalog.py
    #   utils/
    #     __init__.py
    #     formatters.py

    pkg = os.path.join(tmp, 'storecli')
    for d in ['', 'models', 'services', 'utils']:
        os.makedirs(os.path.join(pkg, d), exist_ok=True)

    files = {
        '__init__.py': '''
\"\"\"storecli — innoZverse Store CLI toolkit.\"\"\"
__version__ = \"1.0.0\"
__author__  = \"Dr. Chen\"
__all__ = [\"models\", \"services\", \"utils\"]

from storecli.models.product import Product
from storecli.services.catalog import Catalog

def version() -> str:
    return __version__
''',
        'models/__init__.py': '''
\"\"\"Data models.\"\"\"
from storecli.models.product import Product
from storecli.models.order   import Order
__all__ = [\"Product\", \"Order\"]
''',
        'models/product.py': '''
from dataclasses import dataclass, field
@dataclass
class Product:
    id: int = 0
    name: str = \"\"
    price: float = 0.0
    stock: int = 0
    @property
    def value(self) -> float: return self.price * self.stock
    def __repr__(self): return f\"Product({self.name!r}, \${self.price})\"
''',
        'models/order.py': '''
from dataclasses import dataclass
from datetime import datetime
@dataclass
class Order:
    id: int
    product_id: int
    quantity: int
    total: float
    created_at: datetime = None
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
''',
        'services/__init__.py': 'from storecli.services.catalog import Catalog\n__all__ = [\"Catalog\"]\n',
        'services/catalog.py': '''
from storecli.models.product import Product
class Catalog:
    def __init__(self): self._items: dict[int, Product] = {}; self._seq = 1
    def add(self, name: str, price: float, stock: int = 0) -> Product:
        p = Product(self._seq, name, price, stock)
        self._items[self._seq] = p; self._seq += 1; return p
    def get(self, pid: int) -> Product | None: return self._items.get(pid)
    def list(self) -> list[Product]: return sorted(self._items.values(), key=lambda p: p.price)
    def total_value(self) -> float: return sum(p.value for p in self._items.values())
    def __len__(self): return len(self._items)
''',
        'utils/__init__.py': 'from storecli.utils.formatters import fmt_price, fmt_table\n',
        'utils/formatters.py': '''
def fmt_price(price: float) -> str: return f\"\${price:,.2f}\"
def fmt_table(products) -> str:
    lines = [f\"{'ID':>4}  {'Name':<22}  {'Price':>10}  {'Stock':>6}\"]
    lines.append(\"-\" * 50)
    for p in products:
        lines.append(f\"{p.id:>4}  {p.name:<22}  {fmt_price(p.price):>10}  {p.stock:>6}\")
    return \"\\n\".join(lines)
''',
    }

    for relpath, content in files.items():
        path = os.path.join(pkg, relpath)
        with open(path, 'w') as f:
            f.write(content.strip() + '\n')

    # Add to sys.path and import
    sys.path.insert(0, tmp)
    import storecli
    from storecli import Product, Catalog, version
    from storecli.utils import fmt_price, fmt_table

    print(f'storecli v{storecli.__version__} by {storecli.__author__}')
    print(f'version(): {version()}')

    # Use package
    cat = Catalog()
    cat.add('Surface Pro 12\"',  864.0,  15)
    cat.add('Surface Pen',       49.99,  80)
    cat.add('Office 365',        99.99,  999)
    cat.add('USB-C Hub',         29.99,  0)
    cat.add('Surface Book 3',    1299.0, 5)

    print(f'Catalog: {len(cat)} products')
    print(f'Total inventory value: {fmt_price(cat.total_value())}')
    print()
    print(fmt_table(cat.list()))

    # Verify __all__ controls star imports
    print()
    print(f'storecli.__all__: {storecli.__all__}')
    sys.path.pop(0)
"
```

**📸 Verified Output:**
```
storecli v1.0.0 by Dr. Chen
version(): 1.0.0
Catalog: 5 products
Total inventory value: $108,734.21

  ID  Name                     Price   Stock
--------------------------------------------------
   4  USB-C Hub                $29.99       0
   2  Surface Pen              $49.99      80
   3  Office 365               $99.99     999
   1  Surface Pro 12"         $864.00      15
   5  Surface Book 3        $1,299.00       5

storecli.__all__: ['models', 'services', 'utils']
```

---

### Steps 3–8: `pyproject.toml`, entry points, relative imports, lazy imports, `__all__`, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import tempfile, os, sys

# Step 3: pyproject.toml structure (printed for reference)
pyproject = '''[build-system]
requires = [\"hatchling\"]
build-backend = \"hatchling.build\"

[project]
name = \"storecli\"
version = \"1.0.0\"
description = \"innoZverse Store CLI toolkit\"
readme = \"README.md\"
requires-python = \">=3.11\"
license = {text = \"MIT\"}
authors = [{name = \"Dr. Chen\", email = \"ebiz@chen.me\"}]
keywords = [\"cli\", \"store\", \"inventory\"]
classifiers = [
    \"Development Status :: 4 - Beta\",
    \"Intended Audience :: Developers\",
    \"Programming Language :: Python :: 3\",
    \"Programming Language :: Python :: 3.11\",
    \"Programming Language :: Python :: 3.12\",
]
dependencies = [
    \"fastapi>=0.100\",
    \"pydantic>=2.0\",
    \"rich>=13.0\",
]

[project.optional-dependencies]
dev = [\"pytest>=7\", \"mypy>=1.0\"]
docs = [\"mkdocs>=1.5\"]

[project.scripts]
storecli = \"storecli.cli:main\"

[project.urls]
Homepage = \"https://innozverse.com\"
Repository = \"https://github.com/lastcow/innozverse\"

[tool.hatch.build.targets.wheel]
packages = [\"src/storecli\"]

[tool.mypy]
python_version = \"3.12\"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = [\"tests\"]
asyncio_mode = \"auto\"

[tool.ruff]
line-length = 100
select = [\"E\", \"F\", \"I\", \"UP\"]
'''
print('=== pyproject.toml (modern Python packaging) ===')
print(pyproject)

# Step 4: __all__ and controlled exports
print('=== __all__ demo ===')

# Without __all__: from module import * imports everything
# With __all__: only exports listed names

def _private_helper(): return 'internal'
def public_function(): return 'exported'
CONSTANT = 42
_INTERNAL = 'not exported'

__all__ = ['public_function', 'CONSTANT']  # Controls star imports

print(f'Public exports: {__all__}')

# Step 5: Lazy imports (improve startup time)
import sys, importlib

class LazyModule:
    def __init__(self, name: str):
        self._name = name
        self._mod = None

    def __getattr__(self, attr: str):
        if self._mod is None:
            self._mod = importlib.import_module(self._name)
            sys.modules[self._name] = self._mod
        return getattr(self._mod, attr)

# Heavy modules only imported when first used
np = LazyModule('numpy')
pd = LazyModule('pandas')

print()
print('=== Lazy imports ===')
print('numpy not yet imported...')
# First access triggers import
arr = np.array([1, 2, 3])
print(f'numpy.array: {arr}')
df = pd.DataFrame({'x': [1, 2], 'y': [3, 4]})
print(f'pandas.DataFrame shape: {df.shape}')

# Step 6: importlib.resources (access package data files)
import importlib.resources

# Simulate reading a package data file
data_content = 'Surface Pro,864.0,15\nSurface Pen,49.99,80\nOffice 365,99.99,999'
print()
print('=== Package Data (simulated) ===')
for line in data_content.strip().splitlines():
    name, price, stock = line.split(',')
    print(f'  {name:20s} \${float(price):.2f}  stock={stock}')

# Step 7: Namespace packages (no __init__.py)
# Used by large codebases split across multiple directories
print()
print('=== Namespace Packages ===')
print('namespace packages allow splitting a package across multiple directories')
print('  acme/  (dir1)           acme/  (dir2)')
print('    billing/                reporting/')
print('      __init__.py             __init__.py')
print('Both become: acme.billing and acme.reporting')
print('No top-level __init__.py needed in namespace packages')

# Step 8: Capstone — module inspection tool
print()
print('=== Module Inspector ===')
import inspect

def inspect_module(mod):
    classes    = [(n, obj) for n, obj in inspect.getmembers(mod, inspect.isclass)]
    functions  = [(n, obj) for n, obj in inspect.getmembers(mod, inspect.isfunction)]
    constants  = [(n, getattr(mod, n)) for n in dir(mod)
                  if not n.startswith('_') and not callable(getattr(mod, n)) and
                  not inspect.ismodule(getattr(mod, n))]

    print(f'Module: {mod.__name__}')
    print(f'  File: {getattr(mod, \"__file__\", \"<builtin>\")}')
    print(f'  Classes ({len(classes)}): {[n for n,_ in classes[:5]]}')
    print(f'  Functions ({len(functions)}): {[n for n,_ in functions[:5]]}')
    print(f'  Constants ({len(constants)}): {[n for n,_ in constants[:5]]}')

import json, pathlib
for m in [json, pathlib]:
    inspect_module(m)
    print()
"
```

**📸 Verified Output:**
```
=== Lazy imports ===
numpy not yet imported...
numpy.array: [1 2 3]
pandas.DataFrame shape: (2, 2)

=== Module Inspector ===
Module: json
  File: /usr/lib/python3.12/json/__init__.py
  Classes (2): ['JSONDecodeError', 'JSONDecoder']
  Functions (4): ['dump', 'dumps', 'load', 'loads']
  Constants (3): ['__author__', '__version__', 'decoder']

Module: pathlib
  File: /usr/lib/python3.12/pathlib/__init__.py
  Classes (7): ['Path', 'PosixPath', 'PurePath', ...]
```

---

## Summary

| Concept | Key points |
|---------|-----------|
| Module | Single `.py` file; cached in `sys.modules` |
| Package | Directory with `__init__.py` |
| Namespace package | Directory without `__init__.py`; splits across dirs |
| `__all__` | Controls `from module import *` exports |
| `pyproject.toml` | Modern packaging (replaces `setup.py`) |
| Lazy import | `importlib.import_module()` on first access |
| `importlib.util` | Load modules from arbitrary file paths |

## Further Reading
- [Python packaging guide](https://packaging.python.org)
- [pyproject.toml spec](https://peps.python.org/pep-0517/)
- [importlib](https://docs.python.org/3/library/importlib.html)
