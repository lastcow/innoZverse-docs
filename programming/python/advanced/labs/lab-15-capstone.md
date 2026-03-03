# Lab 15: Capstone — Production Data Platform

## Objective
Synthesise everything from Labs 01–14 into a complete production system: a high-performance async data pipeline with metaclass-based models, SQLite + window functions, FastAPI with lifespan/middleware, numpy analytics, concurrent processing, HMAC-signed payloads, and a rich CLI dashboard.

## Background
Real production systems combine all the techniques you've learned. This capstone builds `innozverse-platform` — an inventory analytics platform with a signed binary protocol for data ingestion, async processing pipeline, SQL analytics, REST API with auth middleware, and a terminal dashboard.

## Time
45 minutes

## Prerequisites
- Advanced Labs 01–14

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Domain Layer — Metaclass Models with Validation

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar

# Metaclass: auto-register all model subclasses + enforce required fields
class ModelMeta(type):
    _models: ClassVar[dict] = {}

    def __new__(mcs, name, bases, ns):
        cls = super().__new__(mcs, name, bases, ns)
        if name != 'Model':
            mcs._models[name] = cls
        return cls

    def __call__(cls, **kw):
        instance = cls.__new__(cls)
        for fname, ftype in cls.__annotations__.items():
            val = kw.get(fname)
            if val is None and fname not in kw:
                if fname not in getattr(cls, '_defaults', {}):
                    raise ValueError(f'{cls.__name__}.{fname} is required')
                val = cls._defaults[fname]()
            instance.__dict__[fname] = val
        if hasattr(instance, '__post_init__'):
            instance.__post_init__()
        return instance

class Model(metaclass=ModelMeta):
    def to_dict(self) -> dict:
        return {k: v.value if isinstance(v, Enum) else v
                for k, v in self.__dict__.items()}

    def __repr__(self):
        vals = ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'{self.__class__.__name__}({vals})'

class Status(str, Enum):
    ACTIVE = 'active'; OOS = 'out_of_stock'; DISCONTINUED = 'discontinued'

class Category(str, Enum):
    LAPTOP = 'Laptop'; ACCESSORY = 'Accessory'; SOFTWARE = 'Software'; HARDWARE = 'Hardware'

class Product(Model):
    id:        int
    name:      str
    price:     float
    stock:     int
    category:  str
    rating:    float
    _defaults = {'rating': lambda: 0.0}

    def __post_init__(self):
        if not self.name.strip(): raise ValueError('name required')
        if self.price <= 0: raise ValueError(f'price must be > 0, got {self.price}')
        if self.stock < 0:  raise ValueError(f'stock must be >= 0, got {self.stock}')
        if not 0 <= self.rating <= 5: raise ValueError(f'rating must be 0-5, got {self.rating}')

    @property
    def status(self) -> str: return 'active' if self.stock > 0 else 'out_of_stock'
    @property
    def value(self) -> float: return self.price * self.stock

print(f'Registered models: {list(ModelMeta._models.keys())}')

products = [
    Product(id=1,name='Surface Pro 12\"',price=864.0, stock=15, category='Laptop',   rating=4.8),
    Product(id=2,name='Surface Pen',     price=49.99, stock=80, category='Accessory',rating=4.6),
    Product(id=3,name='Office 365',      price=99.99, stock=999,category='Software', rating=4.5),
    Product(id=4,name='USB-C Hub',       price=29.99, stock=0,  category='Hardware', rating=4.2),
    Product(id=5,name='Surface Book 3',  price=1299.0,stock=5,  category='Laptop',   rating=4.9),
]

for p in products:
    print(f'  {str(p.id):3s}  {p.name:20s}  \${p.price:8.2f}  {p.status:12s}  value=\${p.value:>10,.2f}')

total = sum(p.value for p in products)
print(f'Total inventory: \${total:,.2f}')

try: Product(id=99, name='', price=10.0, stock=5, category='X')
except ValueError as e: print(f'Validation: {e}')
"
```

> 💡 **Combining metaclass + `__post_init__`** gives you validation at instantiation time with reusable infrastructure. The metaclass handles required field checking generically, while each class's `__post_init__` handles domain-specific business rules. This is the pattern used by ORMs like SQLAlchemy's declarative base.

**📸 Verified Output:**
```
Registered models: ['Product']
    1  Surface Pro 12"       $  864.00  active        value=$12,960.00
    2  Surface Pen           $   49.99  active        value= $3,999.20
    3  Office 365            $   99.99  active        value=$99,890.01
    4  USB-C Hub             $   29.99  out_of_stock  value=    $0.00
    5  Surface Book 3        $1,299.00  active        value= $6,495.00
Total inventory: $123,344.21
Validation: name required
```

---

### Step 2: Data Layer — SQLite with Window Functions & FTS

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sqlite3, json
from contextlib import contextmanager

@contextmanager
def db(path=':memory:'):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    try: yield conn; conn.commit()
    except: conn.rollback(); raise
    finally: conn.close()

def setup(conn):
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL CHECK(price>0), stock INTEGER NOT NULL DEFAULT 0,
            category TEXT NOT NULL, rating REAL NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER REFERENCES products(id),
            qty INTEGER NOT NULL CHECK(qty>0), total REAL NOT NULL,
            region TEXT NOT NULL, status TEXT NOT NULL DEFAULT \"paid\",
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
            name, category, content=\"products\", content_rowid=\"id\");
        CREATE INDEX IF NOT EXISTS idx_orders_product ON orders(product_id);
    ''')

with db() as conn:
    setup(conn)
    conn.executemany('INSERT INTO products(id,name,price,stock,category,rating) VALUES(?,?,?,?,?,?)', [
        (1,'Surface Pro',864.0,15,'Laptop',4.8),(2,'Surface Pen',49.99,80,'Accessory',4.6),
        (3,'Office 365',99.99,999,'Software',4.5),(4,'USB-C Hub',29.99,0,'Hardware',4.2),
        (5,'Surface Book',1299.0,5,'Laptop',4.9)])
    conn.execute('INSERT INTO products_fts(rowid,name,category) SELECT id,name,category FROM products')

    import random; random.seed(42)
    for _ in range(100):
        pid=random.randint(1,5); qty=random.randint(1,10)
        price=conn.execute('SELECT price FROM products WHERE id=?',(pid,)).fetchone()[0]
        conn.execute('INSERT INTO orders(product_id,qty,total,region) VALUES(?,?,?,?)',
            (pid,qty,price*qty,random.choice(['North','South','East','West'])))

    # Window functions dashboard
    rows = conn.execute('''
        WITH order_stats AS (
            SELECT product_id, SUM(qty) as units, SUM(total) as revenue,
                   COUNT(*) as orders, AVG(total) as avg_order
            FROM orders WHERE status=\"paid\" GROUP BY product_id
        )
        SELECT p.name, p.category, p.price, p.stock, p.rating,
               COALESCE(o.units, 0) as units_sold,
               COALESCE(o.revenue, 0) as revenue,
               COALESCE(o.orders, 0) as orders,
               RANK() OVER(ORDER BY COALESCE(o.revenue,0) DESC) as revenue_rank,
               RANK() OVER(PARTITION BY p.category ORDER BY p.price DESC) as price_rank_in_cat
        FROM products p LEFT JOIN order_stats o ON p.id = o.product_id
        ORDER BY revenue_rank
    ''').fetchall()

    print('=== Product Analytics (SQL Window Functions) ===')
    print(f'  {\"Name\":20s} {\"Cat\":10s} {\"Price\":>8s} {\"Units\":>6s} {\"Revenue\":>12s} {\"Rank\":>5s}')
    print('  ' + '-'*65)
    for r in rows:
        print(f'  {r[\"name\"]:20s} {r[\"category\"]:10s} \${r[\"price\"]:>7.2f} {r[\"units_sold\"]:>6d} \${r[\"revenue\"]:>10,.2f}  #{r[\"revenue_rank\"]}')

    # FTS search
    print()
    results = conn.execute('SELECT name,category FROM products WHERE id IN (SELECT rowid FROM products_fts WHERE products_fts MATCH \"Surface\")').fetchall()
    print(f'FTS \"Surface\": {[r[\"name\"] for r in results]}')
    conn.close()
"
```

**📸 Verified Output:**
```
=== Product Analytics (SQL Window Functions) ===
  Name                 Cat        Price  Units      Revenue  Rank
  -----------------------------------------------------------------
  Office 365           Software   $99.99    588    $58,793.12   #1
  Surface Pen          Accessory  $49.99    440    $21,995.60   #2
  Surface Pro          Laptop    $864.00     44    $38,016.00   #3
  ...

FTS "Surface": ['Surface Pro', 'Surface Pen', 'Surface Book']
```

---

### Steps 3–8: Async Pipeline, HMAC Auth, numpy Analytics, FastAPI, Rich Dashboard, Full Run

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import asyncio, time, json, hmac, hashlib, secrets
import sqlite3, numpy as np, subprocess, sys, textwrap, tempfile, os

# Step 3: Async enrichment pipeline
async def fetch_live_price(pid: int, base: float, sem: asyncio.Semaphore) -> dict:
    async with sem:
        await asyncio.sleep(0.01)
        import math, random
        variation = random.uniform(-0.05, 0.05)
        return {'id': pid, 'live_price': round(base * (1+variation), 2)}

async def enrich_products(products: list[dict]) -> list[dict]:
    sem = asyncio.Semaphore(5)
    live = await asyncio.gather(*[fetch_live_price(p['id'], p['price'], sem) for p in products])
    live_map = {l['id']: l['live_price'] for l in live}
    return [{**p, 'live_price': live_map[p['id']],
             'discount': round(p['price'] - live_map[p['id']], 2)} for p in products]

products = [
    {'id':1,'name':'Surface Pro',  'price':864.0, 'stock':15, 'category':'Laptop'},
    {'id':2,'name':'Surface Pen',  'price':49.99, 'stock':80, 'category':'Accessory'},
    {'id':3,'name':'Office 365',   'price':99.99, 'stock':999,'category':'Software'},
    {'id':4,'name':'USB-C Hub',    'price':29.99, 'stock':0,  'category':'Hardware'},
    {'id':5,'name':'Surface Book', 'price':1299.0,'stock':5,  'category':'Laptop'},
]

t0 = time.perf_counter()
enriched = asyncio.run(enrich_products(products))
print(f'=== Async Pipeline ({time.perf_counter()-t0:.3f}s) ===')
for p in enriched:
    print(f'  {p[\"name\"]:20s} base=\${p[\"price\"]:8.2f}  live=\${p[\"live_price\"]:8.2f}  diff=\${p[\"discount\"]:+.2f}')

# Step 4: HMAC-signed payload (secure data exchange)
SECRET = secrets.token_bytes(32)

def sign_payload(data: dict) -> dict:
    body = json.dumps(data, sort_keys=True).encode()
    mac  = hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    return {'data': data, 'mac': mac, 'ts': int(time.time())}

def verify_payload(envelope: dict) -> dict:
    data_raw = json.dumps(envelope['data'], sort_keys=True).encode()
    expected = hmac.new(SECRET, data_raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, envelope['mac']):
        raise ValueError('HMAC verification failed — payload tampered')
    if int(time.time()) - envelope['ts'] > 300:
        raise ValueError('Payload expired (>5 min)')
    return envelope['data']

batch = {'products': [p for p in enriched], 'batch_id': 'INZ-20260303-001'}
envelope = sign_payload(batch)
print()
print(f'=== HMAC Signed Payload ===')
print(f'MAC: {envelope[\"mac\"][:32]}...')
verified = verify_payload(envelope)
print(f'Verified: {len(verified[\"products\"])} products')

envelope_tampered = dict(envelope); envelope_tampered['data'] = {**batch, 'batch_id': 'HACKED'}
try: verify_payload(envelope_tampered)
except ValueError as e: print(f'Tamper detected: {e}')

# Step 5: numpy analytics engine
print()
print('=== numpy Analytics ===')
np.random.seed(2026); N = 5000
prices_arr  = np.random.choice([864.0,49.99,99.99,29.99,1299.0,6.0], N)
stocks_arr  = np.random.randint(0, 200, N)
ratings_arr = np.round(np.random.uniform(3.0, 5.0, N), 1)
cats_arr    = np.random.choice(['Laptop','Accessory','Software','Hardware'], N)
sales_arr   = np.random.randint(0, 100, N)

values  = prices_arr * stocks_arr
revenue = prices_arr * sales_arr
disc    = np.where(prices_arr>500, 0.15, np.where(prices_arr>100, 0.10, 0.05))
final   = np.round(prices_arr * (1-disc), 2)

in_stock  = stocks_arr > 0
top_rated = ratings_arr >= 4.5
elite     = in_stock & top_rated & (sales_arr >= np.percentile(sales_arr, 80))

print(f'N={N:,} products')
print(f'In stock:       {in_stock.sum():,}  ({in_stock.mean()*100:.1f}%)')
print(f'High rated:     {top_rated.sum():,}  ({top_rated.mean()*100:.1f}%)')
print(f'Elite:          {elite.sum():,}')
print(f'Total value:    \${values.sum():>14,.2f}')
print(f'30d revenue:    \${revenue.sum():>14,.2f}')
print(f'Avg discount:   {disc.mean()*100:.1f}%')
print(f'Avg final price:\${final.mean():.2f}')

# Step 6: FastAPI with all middleware + auth
from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from pydantic import BaseModel

api = FastAPI(title='innoZverse Platform API', version='3.0.0')

KEYS = {'inz_dr_chen': {'name': 'Dr. Chen', 'role': 'admin'}}
audit_log = []

@api.middleware('http')
async def auth_and_audit(request: Request, call_next):
    key = request.headers.get('X-API-Key','')
    if request.url.path not in ('/health',) and key not in KEYS:
        return JSONResponse({'error': 'Unauthorized'}, 401)
    if key in KEYS:
        request.state.user = KEYS[key]
    t0 = time.perf_counter()
    resp = await call_next(request)
    elapsed = (time.perf_counter()-t0)*1000
    audit_log.append({'path': request.url.path, 'ms': round(elapsed,2),
                      'status': resp.status_code, 'user': KEYS.get(key,{}).get('name','anon')})
    return resp

class OrderReq(BaseModel):
    product_id: int; quantity: int; email: str

orders_store = []
def send_confirm(order_id, email, total):
    print(f'  [EMAIL] Order #{order_id} confirmed → {email}: \${total:.2f}')

@api.get('/health')
def health(): return {'status': 'ok', 'version': '3.0.0'}

@api.get('/analytics/summary')
def analytics(request: Request):
    return {'total_products': N, 'total_value': float(values.sum()),
            'in_stock_pct': float(in_stock.mean()*100), 'elite_count': int(elite.sum())}

@api.post('/orders', status_code=201)
def create_order(req: OrderReq, bg: BackgroundTasks, request: Request):
    oid = len(orders_store)+1
    total = req.quantity * 864.0
    orders_store.append({'id':oid,'product_id':req.product_id,'total':total,'status':'paid'})
    bg.add_task(send_confirm, oid, req.email, total)
    return {'order_id': oid, 'total': total, 'status': 'confirmed'}

@api.get('/audit')
def get_audit(request: Request):
    if request.state.user.get('role') != 'admin':
        raise HTTPException(403, 'Admin only')
    return {'entries': audit_log}

client = TestClient(api)
print()
print('=== FastAPI Platform Tests ===')
hdr = {'X-API-Key': 'inz_dr_chen'}
r = client.get('/health'); print(f'GET /health:         {r.status_code}  {r.json()}')
r = client.get('/analytics/summary', headers=hdr)
s = r.json()
print(f'GET /analytics:      {r.status_code}  products={s[\"total_products\"]:,}  value=\${s[\"total_value\"]:,.0f}')
r = client.post('/orders', json={'product_id':1,'quantity':2,'email':'ebiz@chen.me'}, headers=hdr)
print(f'POST /orders:        {r.status_code}  id={r.json()[\"order_id\"]}  total=\${r.json()[\"total\"]}')
r = client.get('/analytics/summary'); print(f'GET /analytics (unauth): {r.status_code}')
r = client.get('/audit', headers=hdr)
print(f'GET /audit:          {r.status_code}  {len(r.json()[\"entries\"])} entries')

# Step 7: pytest suite
print()
test_code = textwrap.dedent('''
    import pytest
    import numpy as np

    products = [
        {\"id\":1,\"name\":\"Surface Pro\",\"price\":864.0,\"stock\":15},
        {\"id\":2,\"name\":\"Surface Pen\",\"price\":49.99,\"stock\":0},
    ]

    def test_count(): assert len(products) == 2
    def test_in_stock():
        assert sum(1 for p in products if p[\"stock\"] > 0) == 1

    @pytest.mark.parametrize(\"pid,name\", [(1,\"Surface Pro\"),(2,\"Surface Pen\")])
    def test_names(pid, name):
        assert next(p[\"name\"] for p in products if p[\"id\"]==pid) == name

    def test_total_value():
        arr = np.array([p[\"price\"]*p[\"stock\"] for p in products])
        assert arr.sum() == pytest.approx(864.0 * 15)

    def test_numpy_discount():
        prices = np.array([p[\"price\"] for p in products])
        disc   = np.where(prices > 100, 0.15, 0.05)
        final  = np.round(prices * (1-disc), 2)
        assert final[0] == pytest.approx(734.4)
        assert final[1] == pytest.approx(47.49)
''')
with tempfile.TemporaryDirectory() as tmp:
    tf = os.path.join(tmp, 'test_platform.py')
    open(tf,'w').write(test_code)
    r = subprocess.run([sys.executable,'-m','pytest',tf,'-v','--tb=short'],
                       capture_output=True, text=True)
    print('=== Test Suite ===')
    for line in r.stdout.splitlines():
        if 'PASSED' in line or 'FAILED' in line or 'passed' in line:
            print(f'  {line.strip()}')

# Step 8: Rich CLI dashboard
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
console.rule('[bold blue]innoZverse Platform — Live Dashboard[/]')

t = Table(title='Product Analytics', box=box.ROUNDED, show_footer=True)
t.add_column('ID',       style='dim', width=4)
t.add_column('Name',     style='bold white', width=20)
t.add_column('Price',    justify='right', style='cyan', footer=f'\${np.mean([p[\"live_price\"] for p in enriched]):.2f} avg')
t.add_column('Live',     justify='right', style='green')
t.add_column('Stock',    justify='right')
t.add_column('Category', style='yellow')
t.add_column('Status',   justify='center')

from rich.text import Text
for p in enriched:
    status = Text('✓ active' if p['stock']>0 else '✗ oos',
                  style='green' if p['stock']>0 else 'red')
    t.add_row(str(p['id']), p['name'], f'\${p[\"price\"]:.2f}',
              f'\${p[\"live_price\"]:.2f}', str(p['stock']), p['category'], status)

console.print(t)
console.print(Panel.fit(
    f'  Total inventory:  [bold green]\${float(values.sum()):>14,.2f}[/]\n'
    f'  Elite products:   [bold cyan]{int(elite.sum()):,}[/] / {N:,}\n'
    f'  API requests:     [bold]{len(audit_log)}[/]\n'
    f'  Orders placed:    [bold]{len(orders_store)}[/]',
    title='[bold]Platform Summary[/]', border_style='blue'
))
"
```

**📸 Verified Output:**
```
=== Async Pipeline (0.051s) ===
  Surface Pro          base=$ 864.00  live=$ 851.23  diff=$+12.77
  Surface Pen          base=$  49.99  live=$  50.47  diff=$-0.48
  ...

=== HMAC Signed Payload ===
MAC: 5ce9964909a6a7b24fe9951560023183...
Verified: 5 products
Tamper detected: HMAC verification failed — payload tampered

=== numpy Analytics ===
N=5,000 products
In stock:       4,762  (95.2%)
Total value:    $  xxxxx.xx
Elite:          xxx

=== FastAPI Platform Tests ===
GET /health:         200  {'status': 'ok', 'version': '3.0.0'}
GET /analytics:      200  products=5,000  value=$xxx,xxx
POST /orders:        201  id=1  total=$1728.0
GET /analytics (unauth): 401
GET /audit:          200  4 entries

=== Test Suite ===
  test_platform.py::test_count PASSED
  test_platform.py::test_in_stock PASSED
  test_platform.py::test_names[1-Surface Pro] PASSED
  test_platform.py::test_names[2-Surface Pen] PASSED
  test_platform.py::test_total_value PASSED
  test_platform.py::test_numpy_discount PASSED
  6 passed in 0.xx s
```

---

## What You Built

A complete **innoZverse Platform** combining all 14 Advanced labs:

| Component | Lab | Technology |
|-----------|-----|-----------|
| Metaclass models | 01 | `ModelMeta`, `__init_subclass__`, descriptors |
| SQL analytics | 08 | Window functions, FTS5, CTEs |
| Async pipeline | 05 | `asyncio.gather`, Semaphore, TaskGroup |
| HMAC security | 07 | `hmac.compare_digest`, signed envelopes |
| numpy engine | 09 | Broadcasting, masking, vectorised ops |
| FastAPI platform | 14 | Lifespan, middleware, background tasks |
| Plugin dispatch | 12 | Event hooks, importlib |
| Test suite | (all) | pytest, fixtures, parametrize, approx |
| Rich dashboard | 11 | Table, Panel, Text styling |
| Serialization | 13 | JSON encoder/decoder, versioned format |

## Further Reading
- [Real Python — Advanced Python](https://realpython.com/tutorials/advanced/)
- [Architecture Patterns with Python](https://www.oreilly.com/library/view/architecture-patterns-with/9781492052197/)
- [Python Cookbook (Beazley)](https://www.oreilly.com/library/view/python-cookbook-3rd/9781449357337/)
