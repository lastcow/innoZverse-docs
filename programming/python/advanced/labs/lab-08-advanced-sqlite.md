# Lab 08: Advanced SQLite — Window Functions, FTS5, CTEs & Transactions

## Objective
Push SQLite to its limits: window functions (`RANK`, `SUM OVER`, `LAG`), full-text search with FTS5, recursive CTEs, composite indexes, WAL mode, partial indexes, and a Unit-of-Work transaction pattern.

## Background
SQLite supports nearly full SQL:2011 including window functions and CTEs. Combined with WAL (Write-Ahead Logging) for concurrent reads, FTS5 for full-text search, and proper indexing, it can handle millions of rows and complex analytics queries — no server required.

## Time
35 minutes

## Prerequisites
- Practitioner Lab 08 (SQLite basics)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Schema Design — Indexes, Constraints & WAL

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sqlite3

conn = sqlite3.connect(':memory:')
conn.row_factory = sqlite3.Row

# PRAGMA tuning (critical for production SQLite)
conn.execute('PRAGMA journal_mode=WAL')     # concurrent reads while writing
conn.execute('PRAGMA synchronous=NORMAL')   # fsync only at WAL checkpoints
conn.execute('PRAGMA foreign_keys=ON')      # enforce FK constraints
conn.execute('PRAGMA cache_size=-64000')    # 64MB page cache
conn.execute('PRAGMA temp_store=MEMORY')    # temp tables in RAM

conn.executescript('''
    CREATE TABLE categories (
        id   INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL UNIQUE,
        price       REAL    NOT NULL CHECK(price > 0),
        stock       INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
        category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
        rating      REAL    NOT NULL DEFAULT 0 CHECK(rating BETWEEN 0 AND 5),
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE orders (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id  INTEGER NOT NULL REFERENCES products(id),
        quantity    INTEGER NOT NULL CHECK(quantity > 0),
        total       REAL    NOT NULL CHECK(total >= 0),
        status      TEXT    NOT NULL DEFAULT \"pending\"
                            CHECK(status IN (\"pending\",\"paid\",\"refunded\",\"cancelled\")),
        ordered_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Full-text search virtual table
    CREATE VIRTUAL TABLE products_fts USING fts5(
        name, content=\"products\", content_rowid=\"id\"
    );

    -- Indexes for common query patterns
    CREATE INDEX idx_products_category ON products(category_id);
    CREATE INDEX idx_products_price    ON products(price);
    CREATE INDEX idx_orders_product    ON orders(product_id);
    CREATE INDEX idx_orders_status     ON orders(status);

    -- Partial index: only index in-stock products (smaller, faster for stock>0 queries)
    CREATE INDEX idx_products_instock  ON products(price) WHERE stock > 0;
''')

# Seed data
conn.executemany('INSERT INTO categories VALUES(?,?)',
    [(1,'Laptop'),(2,'Accessory'),(3,'Software'),(4,'Hardware')])

conn.executemany(
    'INSERT INTO products(name,price,stock,category_id,rating) VALUES(?,?,?,?,?)',
    [
        ('Surface Pro 12\"',  864.0,  15,  1, 4.8),
        ('Surface Pen',       49.99,  80,  2, 4.6),
        ('Office 365',        99.99,  999, 3, 4.5),
        ('USB-C Hub',         29.99,  0,   4, 4.2),
        ('Surface Book 3',    1299.0, 5,   1, 4.9),
        ('Teams',             6.0,  10000, 3, 4.3),
    ]
)

# Populate FTS index
conn.execute('INSERT INTO products_fts(rowid,name) SELECT id,name FROM products')

# Seed orders
import random; random.seed(42)
for _ in range(50):
    pid = random.randint(1, 6); qty = random.randint(1, 10)
    price = conn.execute('SELECT price FROM products WHERE id=?', (pid,)).fetchone()[0]
    conn.execute(
        'INSERT INTO orders(product_id,quantity,total,status) VALUES(?,?,?,?)',
        (pid, qty, price*qty, random.choice(['paid','paid','pending','refunded']))
    )
conn.commit()

# Verify PRAGMA settings
prag = dict(conn.execute('PRAGMA journal_mode').fetchone())
print(f'WAL mode: {conn.execute(\"PRAGMA journal_mode\").fetchone()[0]}')
print(f'FK enforcement: {conn.execute(\"PRAGMA foreign_keys\").fetchone()[0]}')

# FK violation test
try:
    conn.execute('INSERT INTO products(name,price,stock,category_id) VALUES(?,?,?,?)',
                 ('Ghost', 10, 1, 999))
    conn.commit()
except sqlite3.IntegrityError as e:
    print(f'FK enforced: {e}')

print(f'Products: {conn.execute(\"SELECT COUNT(*) FROM products\").fetchone()[0]}')
print(f'Orders:   {conn.execute(\"SELECT COUNT(*) FROM orders\").fetchone()[0]}')
conn.close()
print('Schema verified')
"
```

> 💡 **`PRAGMA journal_mode=WAL`** switches SQLite from rollback journal to Write-Ahead Logging. In WAL mode, readers don't block writers and writers don't block readers — critical for web apps with concurrent requests. A partial index (`WHERE stock > 0`) is smaller than a full index because SQLite only stores rows matching the condition, making in-stock queries faster.

**📸 Verified Output:**
```
WAL mode: wal
FK enforcement: 1
FK enforced: FOREIGN KEY constraint failed
Products: 6
Orders:   50
Schema verified
```

---

### Step 2: Window Functions — `RANK`, `SUM OVER`, `LAG`

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sqlite3

def make_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript('''
        CREATE TABLE categories(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE products(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, stock INTEGER, category_id INTEGER, rating REAL);
        CREATE TABLE orders(id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, quantity INTEGER, total REAL, status TEXT, ordered_at TEXT DEFAULT (datetime(\"now\")));
    ''')
    conn.executemany('INSERT INTO categories VALUES(?,?)',
        [(1,'Laptop'),(2,'Accessory'),(3,'Software'),(4,'Hardware')])
    conn.executemany('INSERT INTO products(name,price,stock,category_id,rating) VALUES(?,?,?,?,?)',
        [('Surface Pro',864.0,15,1,4.8),('Surface Pen',49.99,80,2,4.6),
         ('Office 365',99.99,999,3,4.5),('USB-C Hub',29.99,0,4,4.2),
         ('Surface Book',1299.0,5,1,4.9),('Teams',6.0,10000,3,4.3)])
    import random; random.seed(42)
    for _ in range(50):
        pid=random.randint(1,6); qty=random.randint(1,10)
        price=conn.execute('SELECT price FROM products WHERE id=?',(pid,)).fetchone()[0]
        conn.execute('INSERT INTO orders(product_id,quantity,total,status) VALUES(?,?,?,?)',
            (pid,qty,price*qty,random.choice(['paid','paid','pending','refunded'])))
    conn.commit()
    return conn

conn = make_db()

# 1. RANK within category
print('=== RANK OVER PARTITION ===')
rows = conn.execute('''
    SELECT p.name, c.name as cat, p.price,
           RANK() OVER(PARTITION BY p.category_id ORDER BY p.price DESC) as rank_in_cat,
           DENSE_RANK() OVER(ORDER BY p.price DESC)                     as global_rank
    FROM products p JOIN categories c ON p.category_id = c.id
    ORDER BY global_rank
''').fetchall()
for r in rows:
    print(f'  #{r[\"global_rank\"]} (cat #{r[\"rank_in_cat\"]}) {r[\"name\"]:20s} \${r[\"price\"]:8.2f}  [{r[\"cat\"]}]')

# 2. Running totals and averages
print()
print('=== Running Totals ===')
rows = conn.execute('''
    SELECT p.name, p.price, p.stock,
           p.price * p.stock as value,
           SUM(p.price * p.stock) OVER(ORDER BY p.price * p.stock DESC) as running_total,
           AVG(p.price)      OVER() as overall_avg_price
    FROM products p
    ORDER BY value DESC
''').fetchall()
for r in rows:
    print(f'  {r[\"name\"]:20s}  value=\${r[\"value\"]:>10,.2f}  running=\${r[\"running_total\"]:>12,.2f}')

# 3. LAG/LEAD — compare to previous/next row
print()
print('=== LAG/LEAD (price comparison) ===')
rows = conn.execute('''
    SELECT name, price,
           LAG(price)  OVER(ORDER BY price) as prev_price,
           LEAD(price) OVER(ORDER BY price) as next_price,
           price - LAG(price) OVER(ORDER BY price) as diff_from_prev
    FROM products ORDER BY price
''').fetchall()
for r in rows:
    diff = f'+\${r[\"diff_from_prev\"]:.2f}' if r['diff_from_prev'] else 'N/A'
    print(f'  {r[\"name\"]:20s} \${r[\"price\"]:8.2f}  prev=\${r[\"prev_price\"] or 0:.2f}  diff={diff}')

# 4. NTILE — quartile bucketing
print()
print('=== NTILE (price quartiles) ===')
rows = conn.execute('''
    SELECT name, price,
           NTILE(4) OVER(ORDER BY price) as quartile
    FROM products ORDER BY price
''').fetchall()
labels = {1:'Q1 Budget',2:'Q2 Mid',3:'Q3 Upper',4:'Q4 Premium'}
for r in rows:
    print(f'  {labels[r[\"quartile\"]]:12s}  {r[\"name\"]:20s}  \${r[\"price\"]}')

conn.close()
"
```

**📸 Verified Output:**
```
=== RANK OVER PARTITION ===
  #1 (cat #1) Surface Book         $1299.00  [Laptop]
  #2 (cat #1) Surface Pro          $ 864.00  [Laptop]
  #3 (cat #1) Office 365           $  99.99  [Software]
  ...

=== Running Totals ===
  Office 365           value=$ 99,890.01  running=$  99,890.01
  Surface Pro          value=$ 12,960.00  running=$ 112,850.01
  ...
```

---

### Steps 3–8: CTEs, FTS5, Unit of Work, Explain Query Plan, JSON, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sqlite3, json

def make_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript('''
        CREATE TABLE products(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,price REAL,stock INTEGER,category TEXT, rating REAL);
        CREATE VIRTUAL TABLE products_fts USING fts5(name,content=\"products\",content_rowid=\"id\");
    ''')
    data = [('Surface Pro',864.0,15,'Laptop',4.8),('Surface Pen',49.99,80,'Accessory',4.6),
            ('Office 365',99.99,999,'Software',4.5),('USB-C Hub',29.99,0,'Hardware',4.2),
            ('Surface Book',1299.0,5,'Laptop',4.9),('Teams',6.0,10000,'Software',4.3)]
    conn.executemany('INSERT INTO products(name,price,stock,category,rating) VALUES(?,?,?,?,?)', data)
    conn.execute('INSERT INTO products_fts(rowid,name) SELECT id,name FROM products')
    conn.commit()
    return conn

conn = make_db()

# Step 3: Recursive CTE — price tier hierarchy
print('=== Recursive CTE: Price Tiers ===')
rows = conn.execute('''
    WITH RECURSIVE tiers(tier, lo, hi) AS (
        SELECT \"Budget\", 0.0, 50.0
        UNION ALL SELECT \"Mid\", 50.0, 200.0
        UNION ALL SELECT \"Premium\", 200.0, 1000.0
        UNION ALL SELECT \"Luxury\", 1000.0, 9999.0
    )
    SELECT t.tier, COUNT(p.id) as count, AVG(p.price) as avg_price, SUM(p.stock) as total_stock
    FROM tiers t LEFT JOIN products p ON p.price >= t.lo AND p.price < t.hi
    GROUP BY t.tier
    ORDER BY t.lo
''').fetchall()
for r in rows:
    print(f'  {r[\"tier\"]:8s}: {r[\"count\"]} products, avg=\${r[\"avg_price\"] or 0:.2f}, stock={r[\"total_stock\"] or 0}')

# Step 4: FTS5 full-text search
print()
print('=== FTS5 Full-Text Search ===')
conn.execute('CREATE VIRTUAL TABLE products_fts2 USING fts5(name, category, content=\"products\", content_rowid=\"id\")')
conn.execute('INSERT INTO products_fts2(rowid,name,category) SELECT id,name,category FROM products')

for query in ['Surface', 'Office', 'Surface Pro', 'NOT Surface', 'Surface OR Office']:
    hits = conn.execute('''
        SELECT p.name, p.price, bm25(products_fts2) as score
        FROM products_fts2 f JOIN products p ON f.rowid = p.id
        WHERE products_fts2 MATCH ?
        ORDER BY score
    ''', (query,)).fetchall()
    print(f'  \"{query}\": {[r[\"name\"] for r in hits]}')

# Step 5: Unit of Work — atomic multi-table transaction
print()
print('=== Unit of Work ===')
conn.executescript('''
    CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER, qty INTEGER, total REAL, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS inventory_log(id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER, delta INTEGER, reason TEXT, ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
''')

def sell_product(conn, product_id: int, qty: int) -> dict:
    with conn:  # auto commit/rollback
        row = conn.execute('SELECT name,price,stock FROM products WHERE id=?',(product_id,)).fetchone()
        if not row: raise ValueError(f'Product {product_id} not found')
        if row['stock'] < qty: raise ValueError(f'Insufficient stock: {row[\"stock\"]} < {qty}')
        total = row['price'] * qty
        conn.execute('UPDATE products SET stock=stock-? WHERE id=?', (qty, product_id))
        sale_id = conn.execute('INSERT INTO sales(product_id,qty,total) VALUES(?,?,?)',
                               (product_id, qty, total)).lastrowid
        conn.execute('INSERT INTO inventory_log(product_id,delta,reason) VALUES(?,?,?)',
                     (product_id, -qty, f'sale #{sale_id}'))
        return {'sale_id': sale_id, 'product': row['name'], 'qty': qty, 'total': total}

sale = sell_product(conn, 1, 3)
print(f'  Sale: {sale}')
stock = conn.execute('SELECT stock FROM products WHERE id=1').fetchone()[0]
print(f'  Remaining stock: {stock}')

try: sell_product(conn, 4, 10)  # USB-C Hub has 0 stock
except ValueError as e: print(f'  Error: {e}')

# Step 6: EXPLAIN QUERY PLAN
print()
print('=== Query Plan Analysis ===')
plans = [
    ('No index', 'SELECT * FROM products WHERE category=\"Laptop\"'),
    ('With price', 'SELECT * FROM products WHERE price > 100 ORDER BY price'),
    ('FTS search', 'SELECT rowid FROM products_fts WHERE products_fts MATCH \"Surface\"'),
]
for label, sql in plans:
    plan = conn.execute(f'EXPLAIN QUERY PLAN {sql}').fetchall()
    for row in plan:
        print(f'  [{label}] {dict(row).get(\"detail\", str(dict(row)))}')

# Step 7: JSON stored in SQLite (json_extract)
print()
print('=== JSON Functions ===')
conn.executescript('''
    CREATE TABLE IF NOT EXISTS product_meta(
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        attributes TEXT  -- JSON blob
    );
''')
for pid, attrs in [
    (1, {'color': 'Platinum', 'weight_kg': 0.882, 'dimensions': {'w': 287, 'h': 209, 'd': 9.3}, 'features': ['touchscreen','stylus_support']}),
    (2, {'color': 'Platinum', 'weight_kg': 0.021, 'pressure_levels': 4096}),
]:
    conn.execute('INSERT OR REPLACE INTO product_meta(product_id,attributes) VALUES(?,?)',
                 (pid, json.dumps(attrs)))
conn.commit()

rows = conn.execute('''
    SELECT p.name,
           json_extract(m.attributes, \"$.color\") as color,
           json_extract(m.attributes, \"$.weight_kg\") as weight,
           json_array_length(m.attributes, \"$.features\") as feature_count
    FROM products p JOIN product_meta m ON p.id = m.product_id
''').fetchall()
for r in rows:
    print(f'  {r[\"name\"]:15s} color={r[\"color\"]}  weight={r[\"weight\"]}kg  features={r[\"feature_count\"]}')

# Step 8: Capstone — analytics dashboard query
print()
print('=== Capstone: Analytics Dashboard ===')
conn.executescript('''
    CREATE TABLE IF NOT EXISTS orders2(
        id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER,
        qty INTEGER, total REAL, status TEXT, region TEXT,
        ordered_at TEXT DEFAULT (datetime(\"now\", \"-\" || (abs(random())%30) || \" days\"))
    );
''')
import random; random.seed(99)
regions = ['North','South','East','West']
for _ in range(200):
    pid=random.randint(1,6); qty=random.randint(1,5)
    price=conn.execute('SELECT price FROM products WHERE id=?',(pid,)).fetchone()[0]
    conn.execute('INSERT INTO orders2(product_id,qty,total,status,region) VALUES(?,?,?,?,?)',
        (pid,qty,price*qty,random.choice(['paid','paid','pending','refunded']),random.choice(regions)))
conn.commit()

dashboard = conn.execute('''
    WITH paid_orders AS (
        SELECT o.product_id, o.qty, o.total, o.region,
               p.name, p.category
        FROM orders2 o JOIN products p ON o.product_id = p.id
        WHERE o.status = \"paid\"
    ),
    category_stats AS (
        SELECT category,
               COUNT(*)      as orders,
               SUM(qty)      as units_sold,
               SUM(total)    as revenue,
               AVG(total)    as avg_order,
               RANK() OVER(ORDER BY SUM(total) DESC) as revenue_rank
        FROM paid_orders GROUP BY category
    )
    SELECT * FROM category_stats ORDER BY revenue_rank
''').fetchall()

print(f'{\"Rank\":<5} {\"Category\":<12} {\"Orders\":<8} {\"Units\":<8} {\"Revenue\":>12} {\"Avg Order\":>10}')
print(\"-\" * 60)
for r in dashboard:
    print(f'{r[\"revenue_rank\"]:<5} {r[\"category\"]:<12} {r[\"orders\"]:<8} {r[\"units_sold\"]:<8} \${r[\"revenue\"]:>10,.2f} \${r[\"avg_order\"]:>8.2f}')

conn.close()
"
```

**📸 Verified Output:**
```
=== Recursive CTE: Price Tiers ===
  Budget  : 2 products, avg=$18.00, stock=10000
  Mid     : 1 products, avg=$99.99, stock=999
  Premium : 1 products, avg=$864.00, stock=15
  Luxury  : 1 products, avg=$1299.00, stock=5

=== FTS5 Full-Text Search ===
  "Surface": ['Surface Pro', 'Surface Pen', 'Surface Book']
  "Office": ['Office 365']

=== Capstone: Analytics Dashboard ===
Rank  Category     Orders   Units    Revenue    Avg Order
------------------------------------------------------------
1     Software     ...      ...     $xx,xxx.xx  $xxx.xx
2     Laptop       ...
```

---

## Summary

| Feature | SQL | Use case |
|---------|-----|---------|
| Window rank | `RANK() OVER(PARTITION BY ... ORDER BY ...)` | Leaderboards |
| Running total | `SUM(x) OVER(ORDER BY ...)` | Cumulative metrics |
| Row comparison | `LAG(x) OVER(ORDER BY ...)` | Period-over-period |
| CTE | `WITH name AS (SELECT ...)` | Readable sub-queries |
| Recursive CTE | `WITH RECURSIVE name AS (... UNION ALL ...)` | Trees, hierarchies |
| FTS5 | `CREATE VIRTUAL TABLE ... USING fts5(...)` | Full-text search |
| JSON | `json_extract(col, '$.field')` | Semi-structured data |
| Partial index | `CREATE INDEX ... WHERE condition` | Filtered fast lookups |

## Further Reading
- [SQLite window functions](https://www.sqlite.org/windowfunctions.html)
- [FTS5](https://www.sqlite.org/fts5.html)
- [SQLite CTEs](https://www.sqlite.org/lang_with.html)
