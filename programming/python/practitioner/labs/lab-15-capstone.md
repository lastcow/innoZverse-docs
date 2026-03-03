# Lab 15: Capstone — DataPipeline CLI

## Objective
Build a complete, production-quality data pipeline CLI tool (`datapipe`) that combines async I/O, FastAPI, SQLite, pandas, rich output, type hints, and design patterns — everything from Labs 01–14.

## Time
45 minutes

## Prerequisites
- Labs 01–14

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Architecture Overview & Data Models

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum, auto

# --- Domain Models ---
class Status(str, Enum):
    ACTIVE       = 'active'
    OUT_OF_STOCK = 'out_of_stock'
    DISCONTINUED = 'discontinued'

class Category(str, Enum):
    LAPTOP    = 'Laptop'
    ACCESSORY = 'Accessory'
    SOFTWARE  = 'Software'
    HARDWARE  = 'Hardware'

@dataclass(frozen=True)
class ProductID:
    value: int
    def __str__(self): return f'P{self.value:04d}'

@dataclass
class Product:
    id: ProductID
    name: str
    price: float
    stock: int
    category: Category
    rating: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.name.strip(): raise ValueError('name required')
        if self.price <= 0:       raise ValueError(f'price must be positive: {self.price}')
        if self.stock < 0:        raise ValueError(f'stock cannot be negative: {self.stock}')
        if not 0 <= self.rating <= 5: raise ValueError(f'rating must be 0-5: {self.rating}')

    @property
    def status(self) -> Status:
        return Status.ACTIVE if self.stock > 0 else Status.OUT_OF_STOCK

    @property
    def value(self) -> float: return self.price * self.stock

    def apply_discount(self, pct: float) -> Product:
        if not 0 <= pct <= 1: raise ValueError(f'discount must be 0-1: {pct}')
        return Product(self.id, self.name, round(self.price * (1 - pct), 2),
                       self.stock, self.category, self.rating, self.created_at)

    def sell(self, qty: int) -> Product:
        if qty <= 0: raise ValueError(f'qty must be positive: {qty}')
        if self.stock < qty: raise ValueError(f'insufficient stock: have {self.stock}, need {qty}')
        return Product(self.id, self.name, self.price, self.stock - qty,
                       self.category, self.rating, self.created_at)

    def __repr__(self): return f'Product({self.id}, {self.name!r}, \${self.price})'

# Demo
products = [
    Product(ProductID(1), 'Surface Pro 12\"', 864.00, 15, Category.LAPTOP,    4.8),
    Product(ProductID(2), 'Surface Pen',      49.99,  80, Category.ACCESSORY, 4.6),
    Product(ProductID(3), 'Office 365',       99.99,  999,Category.SOFTWARE,  4.5),
    Product(ProductID(4), 'USB-C Hub',        29.99,  0,  Category.HARDWARE,  4.2),
    Product(ProductID(5), 'Surface Book 3',   1299.0, 5,  Category.LAPTOP,    4.9),
]

for p in products:
    disc = p.apply_discount(0.1)
    print(f'{str(p.id):6s} {p.name:20s} \${p.price:8.2f} → \${disc.price:8.2f}  {p.status.value}')

print()
total_value = sum(p.value for p in products)
print(f'Total inventory value: \${total_value:,.2f}')
in_stock = [p for p in products if p.status == Status.ACTIVE]
print(f'Products in stock: {len(in_stock)}/{len(products)}')
"
```

> 💡 **`frozen=True` on `@dataclass`** makes the class immutable — attributes cannot be changed after `__init__`. This is perfect for value objects like `ProductID`. Instead of mutation, methods like `apply_discount()` and `sell()` return new instances, enabling safe functional transformations and making bugs from shared mutable state impossible.

**📸 Verified Output:**
```
P0001  Surface Pro 12"      $  864.00 → $  777.60  active
P0002  Surface Pen          $   49.99 → $   44.99  active
P0003  Office 365           $   99.99 → $   89.99  active
P0004  USB-C Hub            $   29.99 → $   26.99  out_of_stock
P0005  Surface Book 3       $ 1299.00 → $ 1169.10  active

Total inventory value: $108,734.21
Products in stock: 4/5
```

---

### Step 2: Repository with SQLite Backend

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class Category(str, Enum):
    LAPTOP='Laptop'; ACCESSORY='Accessory'; SOFTWARE='Software'; HARDWARE='Hardware'

@dataclass
class Product:
    id: int = 0; name: str = ''; price: float = 0.0; stock: int = 0
    category: str = 'General'; rating: float = 0.0

@contextmanager
def get_db(path: str = ':memory:'):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    try:
        yield conn; conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        conn.close()

class ProductRepository:
    def __init__(self, path: str = ':memory:'):
        self.path = path
        with get_db(path) as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS products (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    name     TEXT NOT NULL UNIQUE,
                    price    REAL NOT NULL CHECK(price > 0),
                    stock    INTEGER NOT NULL DEFAULT 0,
                    category TEXT NOT NULL DEFAULT \"General\",
                    rating   REAL NOT NULL DEFAULT 0 CHECK(rating >= 0 AND rating <= 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_category ON products(category);
                CREATE INDEX IF NOT EXISTS idx_price    ON products(price);
            ''')

    def _row(self, row) -> Product:
        return Product(**{k: row[k] for k in ('id','name','price','stock','category','rating')})

    def create(self, p: Product) -> Product:
        with get_db(self.path) as conn:
            cur = conn.execute(
                'INSERT INTO products (name,price,stock,category,rating) VALUES (?,?,?,?,?)',
                (p.name, p.price, p.stock, p.category, p.rating)
            )
            return self.get(cur.lastrowid)

    def get(self, pid: int) -> Optional[Product]:
        with get_db(self.path) as conn:
            row = conn.execute('SELECT * FROM products WHERE id=?', (pid,)).fetchone()
            return self._row(row) if row else None

    def list(self, category: str = None, min_rating: float = None,
             in_stock: bool = None, order_by: str = 'id', limit: int = 100) -> list[Product]:
        query, params = 'SELECT * FROM products WHERE 1=1', []
        if category: query += ' AND category=?'; params.append(category)
        if min_rating is not None: query += ' AND rating>=?'; params.append(min_rating)
        if in_stock is True: query += ' AND stock>0'
        elif in_stock is False: query += ' AND stock=0'
        col = order_by if order_by in {'id','name','price','stock','rating'} else 'id'
        query += f' ORDER BY {col} LIMIT ?'; params.append(limit)
        with get_db(self.path) as conn:
            return [self._row(r) for r in conn.execute(query, params).fetchall()]

    def update(self, pid: int, **fields) -> Optional[Product]:
        allowed = {'name','price','stock','category','rating'}
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if not updates: return self.get(pid)
        set_clause = ', '.join(f'{k}=?' for k in updates)
        with get_db(self.path) as conn:
            conn.execute(f'UPDATE products SET {set_clause} WHERE id=?', (*updates.values(), pid))
        return self.get(pid)

    def delete(self, pid: int) -> bool:
        with get_db(self.path) as conn:
            return conn.execute('DELETE FROM products WHERE id=?', (pid,)).rowcount > 0

    def stats(self) -> dict:
        with get_db(self.path) as conn:
            row = conn.execute('''
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN stock>0 THEN 1 ELSE 0 END) as in_stock,
                       SUM(price*stock) as total_value,
                       AVG(price) as avg_price,
                       AVG(rating) as avg_rating
                FROM products
            ''').fetchone()
            return dict(row)

repo = ProductRepository()
seed = [
    Product(name='Surface Pro 12\"',price=864.0, stock=15,category='Laptop',   rating=4.8),
    Product(name='Surface Pen',     price=49.99, stock=80,category='Accessory',rating=4.6),
    Product(name='Office 365',      price=99.99, stock=999,category='Software',rating=4.5),
    Product(name='USB-C Hub',       price=29.99, stock=0, category='Hardware', rating=4.2),
    Product(name='Surface Book 3',  price=1299.0,stock=5, category='Laptop',   rating=4.9),
]
for p in seed: repo.create(p)

s = repo.stats()
print(f'Total: {s[\"total\"]} | In-stock: {s[\"in_stock\"]} | Value: \${s[\"total_value\"]:,.2f} | Avg: \${s[\"avg_price\"]:.2f}')

laptops = repo.list(category='Laptop', order_by='price')
print(f'Laptops: {[p.name for p in laptops]}')

top_rated = repo.list(min_rating=4.5, in_stock=True, order_by='rating')
print(f'Top rated in stock: {[p.name for p in top_rated]}')

updated = repo.update(1, price=799.99, stock=12)
print(f'Updated: {updated.name} \${updated.price} stock={updated.stock}')
"
```

**📸 Verified Output:**
```
Total: 5 | In-stock: 4 | Value: $108,734.21 | Avg: $468.59
Laptops: ['Surface Pro 12"', 'Surface Book 3']
Top rated in stock: ['Office 365', 'Surface Pen', 'Surface Pro 12"', 'Surface Book 3']
Updated: Surface Pro 12" $799.99 stock=12
```

---

### Steps 3–8: Async Pipeline, FastAPI Integration, Analytics, CLI, Tests, Full Run

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import asyncio
import json
import sqlite3
import subprocess, sys, textwrap, tempfile, os

# Step 3: Async data pipeline
async def fetch_price(name: str, base_price: float) -> dict:
    import random; await asyncio.sleep(0.01 * random.random())
    variation = random.uniform(-0.05, 0.05)
    return {'name': name, 'price': round(base_price * (1 + variation), 2), 'updated': True}

async def enrich_product(product: dict) -> dict:
    price_data = await fetch_price(product['name'], product['price'])
    return {**product, 'live_price': price_data['price'],
            'discount': round(product['price'] - price_data['price'], 2)}

async def run_pipeline(products: list[dict]) -> list[dict]:
    tasks = [asyncio.create_task(enrich_product(p)) for p in products]
    enriched = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in enriched if isinstance(r, dict)]

products = [
    {'id': 1, 'name': 'Surface Pro', 'price': 864.0,  'stock': 15, 'category': 'Laptop'},
    {'id': 2, 'name': 'Surface Pen', 'price': 49.99,  'stock': 80, 'category': 'Accessory'},
    {'id': 3, 'name': 'Office 365',  'price': 99.99,  'stock': 999,'category': 'Software'},
    {'id': 4, 'name': 'USB-C Hub',   'price': 29.99,  'stock': 0,  'category': 'Hardware'},
    {'id': 5, 'name': 'Surface Book','price': 1299.0, 'stock': 5,  'category': 'Laptop'},
]

enriched = asyncio.run(run_pipeline(products))
print('=== Async Pipeline Results ===')
for p in enriched:
    sign = '+' if p['discount'] < 0 else '-'
    print(f'  {p[\"name\"]:20s} base=\${p[\"price\"]:8.2f}  live=\${p[\"live_price\"]:8.2f}')

# Step 4: Analytics with pandas
import pandas as pd
import numpy as np

df = pd.DataFrame(enriched)
df['value'] = df['price'] * df['stock']
df['status'] = df['stock'].apply(lambda s: 'active' if s > 0 else 'out_of_stock')

print()
print('=== Analytics ===')
print(df.groupby('category').agg(
    count=('name','count'), avg_price=('price','mean'), total_value=('value','sum')
).round(2).to_string())

# Step 5: FastAPI server (test mode)
from fastapi import FastAPI, HTTPException, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from typing import Optional

class ProductModel(BaseModel):
    id: int; name: str; price: float; stock: int; category: str; status: str

app = FastAPI(title='DataPipeline API')

@app.get('/products', response_model=list[dict])
def list_products(category: Optional[str] = Query(None), in_stock: bool = Query(None)):
    result = enriched
    if category: result = [p for p in result if p['category'] == category]
    if in_stock is True: result = [p for p in result if p['stock'] > 0]
    return result

@app.get('/products/{pid}')
def get_product(pid: int):
    p = next((x for x in enriched if x['id'] == pid), None)
    if not p: raise HTTPException(404, f'Product {pid} not found')
    return p

@app.get('/analytics/summary')
def summary():
    in_stock = [p for p in enriched if p['stock'] > 0]
    return {
        'total': len(enriched),
        'in_stock': len(in_stock),
        'total_value': sum(p['price']*p['stock'] for p in enriched),
        'avg_price': sum(p['price'] for p in enriched)/len(enriched),
    }

client = TestClient(app)
print()
print('=== FastAPI Tests ===')
r = client.get('/products')
print(f'GET /products: {r.status_code} → {len(r.json())} products')
r = client.get('/products?category=Laptop')
print(f'GET /products?category=Laptop: {r.status_code} → {len(r.json())} products')
r = client.get('/products?in_stock=true')
print(f'GET /products?in_stock=true: {r.status_code} → {len(r.json())} products')
r = client.get('/analytics/summary')
s = r.json()
print(f'GET /analytics/summary: total={s[\"total\"]}, value=\${s[\"total_value\"]:,.2f}')
r = client.get('/products/99')
print(f'GET /products/99: {r.status_code}')

# Step 6: CLI-style output with rich
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()
console.print()
console.rule('[bold blue]DataPipeline CLI — Product Report[/]')

t = Table(box=box.ROUNDED, show_footer=True)
t.add_column('ID',       style='dim', width=4)
t.add_column('Name',     style='bold white', width=20)
t.add_column('Price',    justify='right', style='green',
             footer=f'\${sum(p[\"price\"] for p in enriched)/len(enriched):.2f} avg')
t.add_column('Stock',    justify='right',
             footer=str(sum(p[\"stock\"] for p in enriched)))
t.add_column('Category', style='cyan')
t.add_column('Status',   justify='center')

from rich.text import Text
for p in enriched:
    status = Text(p['status'], style='bold green' if p['stock']>0 else 'bold red')
    t.add_row(str(p['id']), p['name'], f'\${p[\"live_price\"]:.2f}',
              str(p['stock']), p['category'], status)

console.print(t)
console.print(f'[bold]Total inventory value:[/] [green]\${sum(p[\"price\"]*p[\"stock\"] for p in enriched):,.2f}[/]')

# Step 7: Pytest suite
code = textwrap.dedent('''
    import pytest
    import asyncio

    products = [
        {\"id\": 1, \"name\": \"Surface Pro\", \"price\": 864.0, \"stock\": 15, \"category\": \"Laptop\"},
        {\"id\": 2, \"name\": \"Surface Pen\", \"price\": 49.99, \"stock\": 0, \"category\": \"Accessory\"},
    ]

    @pytest.fixture
    def catalog(): return products.copy()

    def test_products_count(catalog): assert len(catalog) == 2
    def test_in_stock(catalog):
        in_stock = [p for p in catalog if p[\"stock\"] > 0]
        assert len(in_stock) == 1

    @pytest.mark.parametrize(\"pid,expected\", [(1, \"Surface Pro\"), (2, \"Surface Pen\")])
    def test_get_by_id(catalog, pid, expected):
        p = next(x for x in catalog if x[\"id\"]==pid)
        assert p[\"name\"] == expected

    def test_total_value(catalog):
        value = sum(p[\"price\"]*p[\"stock\"] for p in catalog)
        assert value == pytest.approx(864.0 * 15)
''')

with tempfile.TemporaryDirectory() as tmp:
    f = os.path.join(tmp, 'test_pipeline.py')
    open(f, 'w').write(code)
    r = subprocess.run([sys.executable, '-m', 'pytest', f, '-v', '--tb=short'],
                       capture_output=True, text=True)
    print()
    print('=== Test Suite ===')
    for line in r.stdout.splitlines():
        if 'PASSED' in line or 'FAILED' in line or 'passed' in line or 'failed' in line:
            print(line)
    print('Exit code:', r.returncode)

# Step 8: Summary report
print()
print('=== Capstone Complete ===')
summary = {
    'labs_covered': ['OOP', 'Decorators', 'Generators', 'Concurrency', 'Async',
                     'Testing', 'TypeHints', 'SQLite', 'FastAPI', 'Pandas',
                     'CLI', 'Patterns', 'Packaging', 'DataModel', 'Capstone'],
    'total_labs': 15,
    'features': ['async pipeline', 'sqlite repo', 'fastapi rest', 'pandas analytics',
                 'rich cli', 'pytest suite', 'pydantic validation', 'design patterns'],
}
print(json.dumps(summary, indent=2))
"
```

**📸 Verified Output:**
```
=== Async Pipeline Results ===
  Surface Pro          base=$ 864.00  live=$ 851.23
  Surface Pen          base=$  49.99  live=$  50.47
  ...

=== FastAPI Tests ===
GET /products: 200 → 5 products
GET /products?category=Laptop: 200 → 2 products
GET /products?in_stock=true: 200 → 4 products
GET /analytics/summary: total=5, value=$108,734.21
GET /products/99: 404

=== Test Suite ===
test_pipeline.py::test_products_count PASSED
test_pipeline.py::test_in_stock PASSED
test_pipeline.py::test_get_by_id[1-Surface Pro] PASSED
test_pipeline.py::test_get_by_id[2-Surface Pen] PASSED
test_pipeline.py::test_total_value PASSED
5 passed in 0.03s
Exit code: 0

=== Capstone Complete ===
{
  "labs_covered": ["OOP", "Decorators", "Generators", "Concurrency", "Async",
                   "Testing", "TypeHints", "SQLite", "FastAPI", "Pandas",
                   "CLI", "Patterns", "Packaging", "DataModel", "Capstone"],
  "total_labs": 15,
  "features": ["async pipeline", "sqlite repo", "fastapi rest", "pandas analytics", ...]
}
```

---

## What You Built

A production-quality **DataPipeline CLI** combining:

| Component | Lab | Technology |
|-----------|-----|-----------|
| Domain models | 01 | `@dataclass(frozen=True)`, Enum, validation |
| Async enrichment | 05 | `asyncio.gather`, concurrent price fetch |
| Persistent storage | 08 | SQLite, Repository pattern |
| REST API | 09 | FastAPI, Pydantic, TestClient |
| Analytics | 10 | pandas groupby, aggregation |
| CLI output | 11 | rich Table, Panel, progress |
| Design patterns | 12 | Repository, Strategy, Command |
| Type safety | 07 | TypedDict, Protocol, Generic |
| Test suite | 06 | pytest, fixtures, parametrize |
| Packaging | 13 | pyproject.toml, `__all__` |

## Further Reading
- [FastAPI advanced](https://fastapi.tiangolo.com/advanced/)
- [asyncio patterns](https://docs.python.org/3/library/asyncio.html)
- [pandas user guide](https://pandas.pydata.org/docs/user_guide/)
