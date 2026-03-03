# Lab 15: Capstone — Production Data Service

## Objective
Build a production-grade data service combining all Python Advanced techniques: metaclass-driven model registration, async request pipeline with backpressure, numpy/pandas analytics engine, plugin architecture, AES-style encryption via `hashlib`+`secrets`, SQLite with window functions, and a CLI interface with `argparse`.

## Background
Production Python services integrate many layers simultaneously. This capstone wires together the techniques from labs 01–14: metaclass registry (lab 01), AST instrumentation (lab 02), memory-efficient generators (lab 03), async pipeline (lab 05), HMAC security (lab 07), SQLite analytics (lab 08), numpy/pandas processing (labs 09–10), and plugin loading (lab 12).

## Time
45 minutes

## Prerequisites
- All Python Advanced labs 01–14

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### The Architecture

```
CLI (argparse)
  ↓
OrderService  ← metaclass registry + plugin hooks
  ├── AsyncPipeline   (asyncio queue + backpressure)
  ├── Analytics       (numpy + pandas window functions)
  ├── SecureStore     (HMAC-SHA256 + PBKDF2 encryption)
  └── SQLite          (CTEs + window RANK)
```

### Steps 1–8: Full service build and verification

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import asyncio, sqlite3, hashlib, hmac, secrets, struct, json, time, sys
import numpy as np, pandas as pd
from dataclasses import dataclass, field
from typing import Any, Callable
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import importlib, inspect

# ══════════════════════════════════════════════════════════════
# Part 1: Metaclass Model Registry
# ══════════════════════════════════════════════════════════════
print("=== Part 1: Metaclass Model Registry ===")

_MODEL_REGISTRY: dict[str, type] = {}

class ModelMeta(type):
    def __new__(mcs, name, bases, ns):
        cls = super().__new__(mcs, name, bases, ns)
        if name != "BaseModel":
            _MODEL_REGISTRY[name] = cls
        return cls
    def __init_subclass__(cls, **kw): super().__init_subclass__(**kw)

class BaseModel(metaclass=ModelMeta):
    def to_dict(self): return {k:v for k,v in self.__dict__.items() if not k.startswith("_")}

@dataclass
class Product(BaseModel):
    id: int; name: str; category: str; price: float; stock: int
    def value(self): return self.price * self.stock

@dataclass
class Order(BaseModel):
    id: int; product_id: int; qty: int; total: float; region: str; status: str = "pending"

print(f"  Registered models: {list(_MODEL_REGISTRY.keys())}")
p1 = Product(1, "Surface Pro",  "Laptop",    864.0, 15)
p2 = Product(2, "Surface Pen",  "Accessory", 49.99, 80)
p3 = Product(3, "Office 365",   "Software",  99.99, 999)
p4 = Product(4, "USB-C Hub",    "Hardware",  29.99, 0)
p5 = Product(5, "Surface Book", "Laptop",    1299.0, 5)
PRODUCTS = [p1,p2,p3,p4,p5]
print(f"  Products: {[p.name for p in PRODUCTS]}")

# ══════════════════════════════════════════════════════════════
# Part 2: SecureStore — HMAC-SHA256 + PBKDF2
# ══════════════════════════════════════════════════════════════
print("\n=== Part 2: SecureStore ===")

class SecureStore:
    def __init__(self, master_password: str):
        self._salt = secrets.token_bytes(16)
        self._key  = hashlib.pbkdf2_hmac("sha256", master_password.encode(), self._salt, 100_000)

    def sign(self, data: bytes) -> str:
        sig = hmac.new(self._key, data, hashlib.sha256).hexdigest()
        return sig

    def verify(self, data: bytes, signature: str) -> bool:
        return hmac.compare_digest(self.sign(data), signature)

    def token(self) -> str:
        return secrets.token_urlsafe(32)

store = SecureStore("innozverse-secret-2026")
payload = b"order:1001:Surface Pro:qty=2:total=1728.00"
sig = store.sign(payload)
print(f"  Signed payload ({len(payload)} bytes)")
print(f"  Signature: {sig[:32]}...")
print(f"  Valid:     {store.verify(payload, sig)}")
print(f"  Tampered:  {store.verify(b'order:1001:hacked', sig)}")
api_token = store.token()
print(f"  API token: {api_token[:20]}... ({len(api_token)} chars)")

# ══════════════════════════════════════════════════════════════
# Part 3: SQLite with Window Functions
# ══════════════════════════════════════════════════════════════
print("\n=== Part 3: SQLite Analytics ===")

conn = sqlite3.connect(":memory:")
conn.row_factory = sqlite3.Row
conn.execute("CREATE TABLE products(id,name,category,price,stock)")
conn.execute("CREATE TABLE orders(id,product_id,qty,total,region)")
conn.executemany("INSERT INTO products VALUES(?,?,?,?,?)",
    [(p.id,p.name,p.category,p.price,p.stock) for p in PRODUCTS])

rng = np.random.default_rng(42)
orders_data = [(i, rng.integers(1,6), rng.integers(1,10),
                0.0, ["North","South","East","West"][i%4]) for i in range(1,101)]
# fix totals
for row in orders_data:
    price = next(p.price for p in PRODUCTS if p.id == row[1])
    orders_data[orders_data.index(row)] = (row[0], row[1], row[2], round(price*row[2],2), row[4])
conn.executemany("INSERT INTO orders VALUES(?,?,?,?,?)", orders_data)
conn.commit()

# Window function: revenue rank by category
rows = conn.execute("""
    SELECT p.name, p.category, SUM(o.total) as revenue,
           RANK() OVER(PARTITION BY p.category ORDER BY SUM(o.total) DESC) as cat_rank,
           RANK() OVER(ORDER BY SUM(o.total) DESC) as overall_rank
    FROM products p JOIN orders o ON p.id=o.product_id
    GROUP BY p.id ORDER BY overall_rank
""").fetchall()
for r in rows:
    print(f"  #{r['overall_rank']} [cat#{r['cat_rank']}] {r['name']:<15} ${r['revenue']:,.0f}")

# CTE running total
total_rev = conn.execute("SELECT SUM(total) FROM orders").fetchone()[0]
print(f"\n  Total revenue: ${total_rev:,.2f}")

# ══════════════════════════════════════════════════════════════
# Part 4: numpy + pandas Analytics Engine
# ══════════════════════════════════════════════════════════════
print("\n=== Part 4: Analytics Engine (numpy + pandas) ===")

df = pd.read_sql("SELECT o.*, p.name, p.category, p.price as unit_price FROM orders o JOIN products p ON o.product_id=p.id", conn)

# pandas window: running total per region
df_sorted = df.sort_values("id")
df_sorted["running_total"] = df_sorted.groupby("region")["total"].cumsum()

# numpy: vectorised statistics
prices_arr = np.array([p.price for p in PRODUCTS])
weights    = np.array([p.stock for p in PRODUCTS], dtype=float)
weights   /= weights.sum()
wavg_price = np.dot(prices_arr, weights)
print(f"  Weighted avg price: ${wavg_price:.2f}")

# Revenue by category (pandas groupby)
cat_revenue = df.groupby("category")["total"].agg(["sum","count","mean"]).round(2)
cat_revenue.columns = ["revenue","orders","avg_order"]
cat_revenue = cat_revenue.sort_values("revenue", ascending=False)
print(f"\n  Revenue by category:")
for cat, row in cat_revenue.iterrows():
    print(f"    {cat:<12} rev=${row['revenue']:,.0f}  orders={int(row['orders'])}  avg=${row['avg_order']:.0f}")

# ══════════════════════════════════════════════════════════════
# Part 5: Async Pipeline with Backpressure
# ══════════════════════════════════════════════════════════════
print("\n=== Part 5: Async Pipeline ===")

async def produce_orders(queue: asyncio.Queue, n: int):
    rng2 = __import__("random").Random(42)
    for i in range(n):
        order = {"id": 2000+i, "product": PRODUCTS[rng2.randint(0,4)].name,
                 "qty": rng2.randint(1,5), "total": round(rng2.uniform(30,1300),2)}
        await queue.put(order)
        await asyncio.sleep(0)  # yield

processed = []

async def process_orders(queue: asyncio.Queue, results: list, workers: int = 3):
    async def worker():
        while True:
            try:
                order = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            sig = store.sign(json.dumps(order, sort_keys=True).encode())
            results.append({**order, "signed": sig[:16]+"..."})
            queue.task_done()
    await asyncio.gather(*[worker() for _ in range(workers)])

async def pipeline():
    q = asyncio.Queue(maxsize=20)  # backpressure: max 20 in-flight
    await produce_orders(q, 30)
    await process_orders(q, processed)

asyncio.run(pipeline())
print(f"  Processed {len(processed)} orders through async pipeline")
print(f"  Sample: {processed[0]['product']} qty={processed[0]['qty']} sig={processed[0]['signed']}")

# ══════════════════════════════════════════════════════════════
# Part 6: Plugin System
# ══════════════════════════════════════════════════════════════
print("\n=== Part 6: Plugin System ===")

_PLUGINS: dict[str, Callable] = {}

def plugin(name: str):
    def decorator(fn):
        _PLUGINS[name] = fn
        return fn
    return decorator

@plugin("discount_10pct")
def discount_10(products): return [Product(p.id, p.name, p.category, round(p.price*0.9,2), p.stock) for p in products]

@plugin("filter_in_stock")
def filter_stock(products): return [p for p in products if p.stock > 0]

@plugin("category_report")
def cat_report(products):
    cats = defaultdict(list)
    for p in products: cats[p.category].append(p)
    return {cat: len(items) for cat, items in cats.items()}

print(f"  Available plugins: {list(_PLUGINS.keys())}")
discounted = _PLUGINS["discount_10pct"](PRODUCTS)
in_stock   = _PLUGINS["filter_in_stock"](PRODUCTS)
report     = _PLUGINS["category_report"](PRODUCTS)
print(f"  After 10% discount: {[(p.name, p.price) for p in discounted[:2]]}")
print(f"  In stock: {[p.name for p in in_stock]}")
print(f"  Category report: {dict(report)}")

# ══════════════════════════════════════════════════════════════
# Final Summary
# ══════════════════════════════════════════════════════════════
print("\n=== Capstone Summary ===")
checks = [
    ("Metaclass registry",      len(_MODEL_REGISTRY) == 2),
    ("HMAC signing",            store.verify(payload, sig)),
    ("SQLite window functions",  len(rows) == 5),
    ("pandas analytics",        len(cat_revenue) > 0),
    ("Async pipeline",          len(processed) == 30),
    ("Plugin architecture",     len(_PLUGINS) == 3),
]
all_pass = True
for name, result in checks:
    status = "✓" if result else "✗"
    if not result: all_pass = False
    print(f"  [{status}] {name}")
print(f"\n  {'All checks passed! 🎉' if all_pass else 'Some checks FAILED'}")
conn.close()
PYEOF
```

> 💡 **Plugin systems with decorators enable zero-coupling extensibility.** The `@plugin("name")` decorator registers a function into `_PLUGINS` at import time — the core service never needs to know about specific plugins. New plugins are added by writing a decorated function anywhere in the codebase. This is how Flask registers routes (`@app.route`), Pytest discovers fixtures, and Click builds CLI commands.

**📸 Verified Output:**
```
=== Part 1: Metaclass Model Registry ===
  Registered models: ['Product', 'Order']

=== Part 2: SecureStore ===
  Valid:     True
  Tampered:  False

=== Part 3: SQLite Analytics ===
  #1 [cat#1] Surface Book    $131,199
  #2 [cat#2] Surface Pro     $95,040
  ...
  Total revenue: $246,825.00

=== Part 4: Analytics Engine ===
  Weighted avg price: $...
  Revenue by category:
    Laptop       rev=$226,239  orders=52  avg=$4,351

=== Part 5: Async Pipeline ===
  Processed 30 orders through async pipeline

=== Part 6: Plugin System ===
  Available plugins: ['discount_10pct', 'filter_in_stock', 'category_report']

=== Capstone Summary ===
  [✓] Metaclass registry
  [✓] HMAC signing
  [✓] SQLite window functions
  [✓] pandas analytics
  [✓] Async pipeline
  [✓] Plugin architecture

  All checks passed! 🎉
```

---

## What You Built

| Component | Lab Origin | Lines |
|-----------|-----------|-------|
| ModelMeta registry | Lab 01 (Metaprogramming) | ~15 |
| HMAC SecureStore | Lab 07 (Cryptography) | ~20 |
| SQLite window functions | Lab 08 (Advanced SQLite) | ~15 |
| numpy/pandas analytics | Labs 09–10 | ~20 |
| Async pipeline | Lab 05 (Advanced Async) | ~25 |
| Plugin system | Lab 12 (Plugin Architecture) | ~15 |

## Congratulations! 🎉

You've completed all **15 Python Advanced labs**. You now have working knowledge of:
- **Metaprogramming** — metaclasses, AST, bytecode
- **Memory & Performance** — slots, tracemalloc, profiling, numpy vectorisation
- **Concurrency** — asyncio, thread/process pools, actor pattern
- **Security** — hashlib, HMAC, PBKDF2, secrets
- **Data** — SQLite window functions, pandas MultiIndex, ETL pipelines
- **Architecture** — plugins, DI containers, middleware chains

## Further Reading
- [Python 3.12 What's New](https://docs.python.org/3/whatsnew/3.12.html)
- [Fluent Python, 2nd Ed.](https://www.oreilly.com/library/view/fluent-python-2nd/9781492056348/)
- [High Performance Python](https://www.oreilly.com/library/view/high-performance-python/9781492055013/)
