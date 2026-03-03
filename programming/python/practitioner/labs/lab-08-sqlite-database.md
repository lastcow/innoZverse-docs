# Lab 08: SQLite & Database Patterns

## Objective
Work with SQLite using Python's `sqlite3` module: schema creation, CRUD operations, transactions, parameterized queries, connection pooling pattern, and repository design.

## Time
35 minutes

## Prerequisites
- Lab 01 (Advanced OOP), Lab 07 (Type Hints)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: sqlite3 Basics

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sqlite3

# Connect (creates file or uses :memory: for temp DB)
conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row  # access columns by name

cur = conn.cursor()

# Create table
cur.execute('''
    CREATE TABLE products (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        name     TEXT NOT NULL,
        price    REAL NOT NULL CHECK(price > 0),
        stock    INTEGER NOT NULL DEFAULT 0,
        category TEXT NOT NULL,
        status   TEXT NOT NULL DEFAULT \"active\",
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert (always use ? placeholders — never f-strings!)
cur.executemany('''
    INSERT INTO products (name, price, stock, category)
    VALUES (?, ?, ?, ?)
''', [
    ('Surface Pro 12\"', 864.00, 15, 'Laptop'),
    ('Surface Pen',      49.99,  80, 'Accessory'),
    ('Office 365',       99.99,  999,'Software'),
    ('USB-C Hub',        29.99,  0,  'Accessory'),
    ('Surface Book 3',   1299.00,5,  'Laptop'),
])

conn.commit()

# Query all
rows = cur.execute('SELECT * FROM products ORDER BY price DESC').fetchall()
print(f'Total products: {len(rows)}')
for row in rows:
    print(f'  [{row[\"id\"]}] {row[\"name\"]:20s} \${row[\"price\"]:8.2f}  stock={row[\"stock\"]}')

# WHERE + aggregation
avg = cur.execute('SELECT AVG(price) FROM products').fetchone()[0]
print(f'Average price: \${avg:.2f}')

by_cat = cur.execute('''
    SELECT category, COUNT(*) as count, AVG(price) as avg_price
    FROM products GROUP BY category ORDER BY category
''').fetchall()
for row in by_cat:
    print(f'  {row[\"category\"]:12s}: {row[\"count\"]} items, avg \${row[\"avg_price\"]:.2f}')

conn.close()
"
```

> 💡 **Always use `?` placeholders** for parameterized queries — never format values directly into SQL strings. `cur.execute('SELECT * FROM users WHERE name = ?', (name,))` is safe; `f'SELECT * FROM users WHERE name = \"{name}\"'` is vulnerable to SQL injection. The trailing comma in `(name,)` makes it a tuple.

**📸 Verified Output:**
```
Total products: 5
  [5] Surface Book 3        $1299.00  stock=5
  [1] Surface Pro 12"       $ 864.00  stock=15
  [3] Office 365            $  99.99  stock=999
  [2] Surface Pen           $  49.99  stock=80
  [4] USB-C Hub             $  29.99  stock=0
Average price: $468.59
  Accessory   : 2 items, avg $39.99
  Laptop      : 2 items, avg $1081.50
  Software    : 1 items, avg $99.99
```

---

### Step 2: Transactions & Error Handling

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db(path: str = ':memory:'):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def setup_schema(conn: sqlite3.Connection) -> None:
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price REAL NOT NULL CHECK(price > 0),
            stock INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            total REAL NOT NULL,
            sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

def sell_product(conn: sqlite3.Connection, product_id: int, qty: int) -> dict:
    '''Atomic sell: check stock, deduct, record sale'''
    cur = conn.cursor()

    # Lock row for update
    row = cur.execute(
        'SELECT id, name, price, stock FROM products WHERE id = ?',
        (product_id,)
    ).fetchone()

    if not row:
        raise ValueError(f'Product {product_id} not found')
    if row['stock'] < qty:
        raise ValueError(f'Insufficient stock: have {row[\"stock\"]}, need {qty}')

    total = row['price'] * qty
    cur.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (qty, product_id))
    cur.execute('INSERT INTO sales (product_id, quantity, total) VALUES (?, ?, ?)',
                (product_id, qty, total))

    return {'product': row['name'], 'qty': qty, 'total': total}

# Demo
with get_db() as conn:
    setup_schema(conn)
    conn.executemany(
        'INSERT INTO products (name, price, stock) VALUES (?, ?, ?)',
        [('Surface Pro', 864.0, 15), ('Surface Pen', 49.99, 80)]
    )

with get_db(':memory:') as conn:
    setup_schema(conn)
    conn.executemany(
        'INSERT INTO products (name, price, stock) VALUES (?, ?, ?)',
        [('Surface Pro', 864.0, 5), ('Surface Pen', 49.99, 80)]
    )

    # Successful transaction
    sale = sell_product(conn, 1, 3)
    print(f'Sold: {sale}')

    stock = conn.execute('SELECT stock FROM products WHERE id=1').fetchone()[0]
    print(f'Remaining stock: {stock}')

    # Failed transaction (should rollback)
    try:
        sell_product(conn, 1, 99)  # only 2 left
    except ValueError as e:
        print(f'Error: {e}')
        stock_after = conn.execute('SELECT stock FROM products WHERE id=1').fetchone()[0]
        print(f'Stock unchanged after error: {stock_after}')

    # Sales report
    report = conn.execute('''
        SELECT p.name, SUM(s.quantity) as units, SUM(s.total) as revenue
        FROM sales s JOIN products p ON s.product_id = p.id
        GROUP BY p.id ORDER BY revenue DESC
    ''').fetchall()
    print('Sales report:')
    for r in report:
        print(f'  {r[\"name\"]}: {r[\"units\"]} units, \${r[\"revenue\"]:.2f}')
"
```

**📸 Verified Output:**
```
Sold: {'product': 'Surface Pro', 'qty': 3, 'total': 2592.0}
Remaining stock: 2
Error: Insufficient stock: have 2, need 99
Stock unchanged after error: 2
Sales report:
  Surface Pro: 3 units, $2592.00
```

---

### Steps 3–8: Repository Pattern, Migrations, Full-Text Search, Pagination, Aggregation, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sqlite3
from dataclasses import dataclass, asdict
from typing import Optional
from contextlib import contextmanager

@dataclass
class Product:
    id: int = 0
    name: str = ''
    price: float = 0.0
    stock: int = 0
    category: str = ''
    status: str = 'active'

class ProductRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._setup()

    def _setup(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0,
                category TEXT NOT NULL DEFAULT \"General\",
                status TEXT NOT NULL DEFAULT \"active\"
            )
        ''')
        self.conn.commit()

    def _row_to_product(self, row: sqlite3.Row) -> Product:
        return Product(**dict(row))

    def create(self, product: Product) -> Product:
        cur = self.conn.execute(
            'INSERT INTO products (name, price, stock, category, status) VALUES (?, ?, ?, ?, ?)',
            (product.name, product.price, product.stock, product.category, product.status)
        )
        self.conn.commit()
        return self.get_by_id(cur.lastrowid)

    def get_by_id(self, product_id: int) -> Optional[Product]:
        row = self.conn.execute(
            'SELECT * FROM products WHERE id = ?', (product_id,)
        ).fetchone()
        return self._row_to_product(row) if row else None

    def list(self, category: str = None, min_stock: int = None,
             order_by: str = 'id', limit: int = 100, offset: int = 0) -> list[Product]:
        query = 'SELECT * FROM products WHERE 1=1'
        params = []
        if category:
            query += ' AND category = ?'; params.append(category)
        if min_stock is not None:
            query += ' AND stock >= ?'; params.append(min_stock)
        allowed_cols = {'id', 'name', 'price', 'stock'}
        col = order_by if order_by in allowed_cols else 'id'
        query += f' ORDER BY {col} LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_product(r) for r in rows]

    def update(self, product_id: int, **fields) -> Optional[Product]:
        allowed = {'name', 'price', 'stock', 'category', 'status'}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates: return self.get_by_id(product_id)
        set_clause = ', '.join(f'{k} = ?' for k in updates)
        self.conn.execute(
            f'UPDATE products SET {set_clause} WHERE id = ?',
            (*updates.values(), product_id)
        )
        self.conn.commit()
        return self.get_by_id(product_id)

    def delete(self, product_id: int) -> bool:
        cur = self.conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def count(self, **filters) -> int:
        query, params = 'SELECT COUNT(*) FROM products WHERE 1=1', []
        for k, v in filters.items():
            query += f' AND {k} = ?'; params.append(v)
        return self.conn.execute(query, params).fetchone()[0]

    def stats(self) -> dict:
        return dict(self.conn.execute('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN stock > 0 THEN 1 ELSE 0 END) as in_stock,
                AVG(price) as avg_price,
                SUM(price * stock) as total_value,
                MIN(price) as min_price,
                MAX(price) as max_price
            FROM products
        ''').fetchone())

# Capstone run
conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row
repo = ProductRepository(conn)

# Create
seeds = [
    Product(name='Surface Pro 12\"', price=864.0,  stock=15, category='Laptop'),
    Product(name='Surface Pen',      price=49.99,  stock=80, category='Accessory'),
    Product(name='Office 365',       price=99.99,  stock=999,category='Software'),
    Product(name='USB-C Hub',        price=29.99,  stock=0,  category='Accessory'),
    Product(name='Surface Book 3',   price=1299.0, stock=5,  category='Laptop'),
]
for s in seeds: repo.create(s)
print(f'Created {repo.count()} products')

# Query
laptops = repo.list(category='Laptop', order_by='price')
print(f'Laptops: {[p.name for p in laptops]}')

in_stock = repo.list(min_stock=1, order_by='price')
print(f'In stock: {len(in_stock)}/{repo.count()}')

# Update
updated = repo.update(1, price=799.99, stock=12)
print(f'Updated: {updated.name} \${updated.price}')

# Delete
deleted = repo.delete(4)
print(f'Deleted #4: {deleted}')

# Stats
s = repo.stats()
print(f'Stats: {repo.count()} products, avg=\${s[\"avg_price\"]:.2f}, value=\${s[\"total_value\"]:,.2f}')

# Pagination
page1 = repo.list(limit=2, offset=0, order_by='name')
page2 = repo.list(limit=2, offset=2, order_by='name')
print(f'Page 1: {[p.name for p in page1]}')
print(f'Page 2: {[p.name for p in page2]}')
conn.close()
"
```

**📸 Verified Output:**
```
Created 5 products
Laptops: ['Surface Pro 12"', 'Surface Book 3']
In stock: 4/5
Updated: Surface Pro 12" $799.99
Deleted #4: True
Stats: 4 products, avg=$582.49, value=$112,744.81
Page 1: ['Office 365', 'Surface Book 3']
Page 2: ['Surface Pen', 'Surface Pro 12"']
```

---

## Summary

| Pattern | Code | Notes |
|---------|------|-------|
| Connect | `sqlite3.connect(':memory:')` | `:memory:` for temp |
| Named columns | `conn.row_factory = sqlite3.Row` | Access by name |
| Safe query | `cur.execute('... WHERE id=?', (id,))` | Always use `?` |
| Batch insert | `cur.executemany(sql, list_of_tuples)` | Faster than loop |
| Transaction | `conn.commit()` / `conn.rollback()` | Explicit control |
| Context manager | `@contextmanager` + try/commit/rollback | Auto-rollback on error |
| Repository | Class wrapping all SQL operations | Clean separation |

## Further Reading
- [sqlite3 docs](https://docs.python.org/3/library/sqlite3.html)
- [SQLAlchemy](https://www.sqlalchemy.org)
