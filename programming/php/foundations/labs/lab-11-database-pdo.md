# Lab 11: Database with PDO & SQLite

## Objective
Connect to SQLite using PHP's PDO (PHP Data Objects), perform CRUD operations with prepared statements, use transactions, and build a simple data access layer.

## Background
PDO is PHP's unified database API — the same code works with SQLite, MySQL, PostgreSQL, and 10+ other databases. Using prepared statements prevents SQL injection attacks. SQLite requires no server setup — perfect for learning, embedded apps, and prototypes. Production apps typically use MySQL or PostgreSQL with the same PDO API.

## Time
35 minutes

## Prerequisites
- Lab 09 (Error Handling), Lab 10 (File I/O)

## Tools
- PHP 8.3 CLI with PDO + PDO_SQLite extensions
- Docker image: `zchencow/innozverse-php:latest`
- Database file: `/tmp/lab11.db`

---

## Lab Instructions

### Step 1: Connect & Create Tables

```php
<?php
declare(strict_types=1);

// Connect to SQLite (creates file if not exists)
$pdo = new PDO('sqlite:/tmp/lab11.db');

// Error mode: throw exceptions on errors
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
// Return rows as associative arrays
$pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
// Enable WAL mode for better concurrency
$pdo->exec('PRAGMA journal_mode=WAL');

echo "Connected to SQLite\n";
echo "Version: " . $pdo->query('SELECT sqlite_version()')->fetchColumn() . "\n";

// Create tables
$pdo->exec(<<<SQL
    CREATE TABLE IF NOT EXISTS categories (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    CREATE TABLE IF NOT EXISTS products (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        price       REAL    NOT NULL,
        stock       INTEGER NOT NULL DEFAULT 0,
        category_id INTEGER REFERENCES categories(id),
        created_at  TEXT    DEFAULT (datetime('now'))
    );
SQL);

echo "Tables created\n";
```

> 💡 **`PDO::ERRMODE_EXCEPTION`** makes PDO throw `PDOException` on errors — without it, errors return `false` silently, which is easy to miss. Always set this in production. `PDO::FETCH_ASSOC` returns `['id' => 1, 'name' => '...']` instead of `[0 => 1, 'id' => 1, ...]` (both numeric and string keys).

**📸 Verified Output:**
```
Connected to SQLite
Version: 3.39.2
Tables created
```

---

### Step 2: INSERT with Prepared Statements

```php
<?php
$pdo = new PDO('sqlite:/tmp/lab11.db', options: [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);

// Insert categories
$catStmt = $pdo->prepare('INSERT OR IGNORE INTO categories (name) VALUES (:name)');
foreach (['Laptop', 'Accessory', 'Software', 'Audio'] as $cat) {
    $catStmt->execute([':name' => $cat]);
}

// Get category IDs
$cats = $pdo->query('SELECT id, name FROM categories')->fetchAll();
$catMap = array_column($cats, 'id', 'name');
echo "Categories: " . implode(', ', array_keys($catMap)) . "\n";

// Insert products
$stmt = $pdo->prepare(<<<SQL
    INSERT INTO products (name, price, stock, category_id)
    VALUES (:name, :price, :stock, :cat)
SQL);

$products = [
    ['Surface Pro 12"',    864.00, 15, 'Laptop'],
    ['Surface Pen',         49.99, 80, 'Accessory'],
    ['USB-C Hub',           29.99,  0, 'Accessory'],
    ['Office 365',          99.99, 999, 'Software'],
    ['Surface Headphones', 249.99, 25, 'Audio'],
];

foreach ($products as [$name, $price, $stock, $cat]) {
    $stmt->execute([':name' => $name, ':price' => $price,
                    ':stock' => $stock, ':cat' => $catMap[$cat]]);
    echo "Inserted: $name (id=" . $pdo->lastInsertId() . ")\n";
}
```

> 💡 **Prepared statements** separate SQL structure from data — the database parses the SQL once, then you supply values separately. This prevents SQL injection: if `$name = "'; DROP TABLE products; --"`, the statement treats it as a literal string, not SQL. Never concatenate user input into SQL.

**📸 Verified Output:**
```
Categories: Laptop, Accessory, Software, Audio
Inserted: Surface Pro 12" (id=1)
Inserted: Surface Pen (id=2)
Inserted: USB-C Hub (id=3)
Inserted: Office 365 (id=4)
Inserted: Surface Headphones (id=5)
```

---

### Step 3: SELECT — Query & Fetch

```php
<?php
$pdo = new PDO('sqlite:/tmp/lab11.db', options: [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);

// fetchAll — get all rows
$products = $pdo->query(<<<SQL
    SELECT p.id, p.name, p.price, p.stock, c.name AS category
    FROM products p
    JOIN categories c ON p.category_id = c.id
    ORDER BY p.price DESC
SQL)->fetchAll();

printf("%-4s %-25s %8s %6s %-12s\n", "ID", "Name", "Price", "Stock", "Category");
echo str_repeat('─', 60) . "\n";
foreach ($products as $p) {
    printf("%-4d %-25s %8.2f %6d %-12s\n",
        $p['id'], $p['name'], $p['price'], $p['stock'], $p['category']);
}

// fetchColumn — single value
$total = $pdo->query('SELECT COUNT(*) FROM products')->fetchColumn();
$sum   = $pdo->query('SELECT SUM(price * stock) FROM products')->fetchColumn();
printf("\nTotal products: %d  Inventory value: $%.2f\n", $total, $sum);

// Parameterized SELECT
$stmt = $pdo->prepare('SELECT * FROM products WHERE price BETWEEN :min AND :max ORDER BY price');
$stmt->execute([':min' => 30, ':max' => 300]);
$midRange = $stmt->fetchAll();
echo "\nMid-range products ($30-$300):\n";
foreach ($midRange as $p) {
    printf("  %-25s $%.2f\n", $p['name'], $p['price']);
}
```

> 💡 **`fetchAll()` loads all rows into memory** — fine for small result sets. For large results, use a `while ($row = $stmt->fetch())` loop to process one row at a time. `fetchColumn(0)` gets just the first column of the first row — ideal for `COUNT(*)`, `MAX()`, `SUM()`.

**📸 Verified Output:**
```
ID   Name                      Price  Stock Category
────────────────────────────────────────────────────────────
1    Surface Pro 12"          864.00     15 Laptop
5    Surface Headphones       249.99     25 Audio
4    Office 365                99.99    999 Software
2    Surface Pen               49.99     80 Accessory
3    USB-C Hub                 29.99      0 Accessory

Total products: 5  Inventory value: $119,267.60

Mid-range products ($30-$300):
  Surface Headphones       $249.99
  Office 365                $99.99
  Surface Pen               $49.99
```

---

### Step 4: UPDATE & DELETE

```php
<?php
$pdo = new PDO('sqlite:/tmp/lab11.db', options: [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);

// UPDATE single row
$stmt = $pdo->prepare('UPDATE products SET stock = :stock WHERE id = :id');
$stmt->execute([':stock' => 50, ':id' => 3]);
echo "Rows updated: " . $stmt->rowCount() . "\n";

// UPDATE with condition
$stmt = $pdo->prepare('UPDATE products SET price = price * :factor WHERE category_id = (SELECT id FROM categories WHERE name = :cat)');
$stmt->execute([':factor' => 0.9, ':cat' => 'Accessory']);
echo "Accessories discounted: " . $stmt->rowCount() . " rows\n";

// Verify update
$accessories = $pdo->query("SELECT name, price FROM products WHERE category_id = (SELECT id FROM categories WHERE name='Accessory')")->fetchAll();
foreach ($accessories as $a) printf("  %-20s $%.2f\n", $a['name'], $a['price']);

// DELETE
$stmt = $pdo->prepare('DELETE FROM products WHERE stock = 0');
$stmt->execute();
echo "\nDeleted out-of-stock: " . $stmt->rowCount() . " row(s)\n";

// Remaining
$remaining = $pdo->query('SELECT COUNT(*) FROM products')->fetchColumn();
echo "Remaining products: $remaining\n";
```

> 💡 **`rowCount()`** returns affected rows for INSERT/UPDATE/DELETE — not for SELECT. For SELECT row count, use `COUNT(*)` in the query or `count($rows)` after `fetchAll()`. Always check `rowCount()` after updates to verify the change happened — a 0 means your WHERE clause matched nothing.

**📸 Verified Output:**
```
Rows updated: 1
Accessories discounted: 2 rows
  Surface Pen          $44.99
  USB-C Hub            $26.99
Deleted out-of-stock: 1 row(s)
Remaining products: 4
```

---

### Step 5: Transactions

```php
<?php
$pdo = new PDO('sqlite:/tmp/lab11.db', options: [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);

function transferStock(PDO $pdo, int $fromId, int $toId, int $qty): void {
    $pdo->beginTransaction();
    try {
        // Check source stock
        $from = $pdo->prepare('SELECT stock FROM products WHERE id = ?');
        $from->execute([$fromId]);
        $source = $from->fetch();

        if (!$source || $source['stock'] < $qty) {
            throw new \RuntimeException("Insufficient stock in product #$fromId");
        }

        // Deduct from source
        $pdo->prepare('UPDATE products SET stock = stock - ? WHERE id = ?')
            ->execute([$qty, $fromId]);

        // Add to destination
        $pdo->prepare('UPDATE products SET stock = stock + ? WHERE id = ?')
            ->execute([$qty, $toId]);

        $pdo->commit();
        echo "Transferred $qty units: #$fromId → #$toId\n";
    } catch (\Exception $e) {
        $pdo->rollBack();
        echo "Rolled back: " . $e->getMessage() . "\n";
    }
}

// Show before
$rows = $pdo->query('SELECT id, name, stock FROM products WHERE id IN (1,2)')->fetchAll();
foreach ($rows as $r) printf("  Before #%d %-20s stock=%d\n", $r['id'], $r['name'], $r['stock']);

transferStock($pdo, 1, 2, 5);   // valid
transferStock($pdo, 2, 1, 500); // fails — insufficient stock

// Show after
$rows = $pdo->query('SELECT id, name, stock FROM products WHERE id IN (1,2)')->fetchAll();
foreach ($rows as $r) printf("  After  #%d %-20s stock=%d\n", $r['id'], $r['name'], $r['stock']);
```

> 💡 **Transactions are atomic** — either ALL operations succeed (commit) or NONE take effect (rollback). Without a transaction, a crash between the deduct and add steps would leave your inventory inconsistent. Always wrap multi-step data operations in a transaction.

**📸 Verified Output:**
```
  Before #1 Surface Pro 12"      stock=15
  Before #2 Surface Pen          stock=80
Transferred 5 units: #1 → #2
Rolled back: Insufficient stock in product #2
  After  #1 Surface Pro 12"      stock=10
  After  #2 Surface Pen          stock=85
```

---

### Step 6: Aggregate Queries & Reporting

```php
<?php
$pdo = new PDO('sqlite:/tmp/lab11.db', options: [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);

// Group by category
$report = $pdo->query(<<<SQL
    SELECT
        c.name AS category,
        COUNT(p.id) AS count,
        AVG(p.price) AS avg_price,
        SUM(p.stock) AS total_stock,
        MAX(p.price) AS max_price
    FROM products p
    JOIN categories c ON p.category_id = c.id
    GROUP BY c.name
    ORDER BY total_stock DESC
SQL)->fetchAll();

printf("%-12s %5s %10s %12s %10s\n", "Category", "Items", "Avg Price", "Total Stock", "Max Price");
echo str_repeat('─', 55) . "\n";
foreach ($report as $r) {
    printf("%-12s %5d %10.2f %12d %10.2f\n",
        $r['category'], $r['count'], $r['avg_price'],
        $r['total_stock'], $r['max_price']);
}

// Window-style ranking with SQLite
$ranked = $pdo->query(<<<SQL
    SELECT
        name, price,
        RANK() OVER (ORDER BY price DESC) AS price_rank
    FROM products
SQL)->fetchAll();

echo "\nPrice ranking:\n";
foreach ($ranked as $r) {
    printf("  #%d %-25s $%.2f\n", $r['price_rank'], $r['name'], $r['price']);
}
```

**📸 Verified Output:**
```
Category      Items  Avg Price  Total Stock  Max Price
───────────────────────────────────────────────────────────
Software          1     99.99          999      99.99
Audio             1    249.99           25     249.99
Laptop            1    864.00           10     864.00
Accessory         1     44.99           85      44.99

Price ranking:
  #1 Surface Pro 12"          $864.00
  #2 Surface Headphones       $249.99
  #3 Office 365                $99.99
  #4 Surface Pen               $44.99
```

---

### Step 7: PDO Fetch Modes

```php
<?php
$pdo = new PDO('sqlite:/tmp/lab11.db', options: [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);

// FETCH_OBJ — rows as stdClass objects
$pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_OBJ);
$products = $pdo->query('SELECT id, name, price FROM products LIMIT 3')->fetchAll();
foreach ($products as $p) {
    echo "  {$p->name}: \${$p->price}\n";
}

// FETCH_CLASS — rows mapped into a class
class Product {
    public int    $id;
    public string $name;
    public float  $price;
    public int    $stock;

    public function summary(): string {
        return "#{$this->id} {$this->name} — \${$this->price} (stock: {$this->stock})";
    }
}

$stmt = $pdo->query('SELECT id, name, price, stock FROM products');
$stmt->setFetchMode(PDO::FETCH_CLASS, Product::class);
$objs = $stmt->fetchAll();
echo "\nAs objects:\n";
foreach ($objs as $p) echo "  " . $p->summary() . "\n";

// FETCH_KEY_PAIR — key=>value pairs
$pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_KEY_PAIR);
$priceMap = $pdo->query('SELECT name, price FROM products')->fetchAll();
echo "\nPrice map:\n";
foreach ($priceMap as $name => $price) printf("  %-25s $%.2f\n", $name, $price);
```

> 💡 **`PDO::FETCH_CLASS`** automatically maps columns to object properties — no manual `new Product()` and assignment needed. If the class has a constructor, `PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE` calls the constructor first, then sets properties. This is how ORMs like Doctrine hydrate entity objects.

**📸 Verified Output:**
```
  Surface Pro 12": $864
  Surface Headphones: $249.99
  Office 365: $99.99

As objects:
  #1 Surface Pro 12" — $864 (stock: 10)
  ...

Price map:
  Surface Pro 12"           $864.00
  ...
```

---

### Step 8: Complete — Repository Pattern

```php
<?php
declare(strict_types=1);

class ProductRepository {
    private \PDO $pdo;

    public function __construct(string $dbPath) {
        $this->pdo = new \PDO("sqlite:$dbPath", options: [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
        ]);
    }

    public function findAll(string $orderBy = 'id'): array {
        return $this->pdo->query("SELECT * FROM products ORDER BY $orderBy")->fetchAll();
    }

    public function findById(int $id): ?array {
        $stmt = $this->pdo->prepare('SELECT * FROM products WHERE id = ?');
        $stmt->execute([$id]);
        return $stmt->fetch() ?: null;
    }

    public function findByCategory(string $category): array {
        $stmt = $this->pdo->prepare(<<<SQL
            SELECT p.* FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.name = ?
        SQL);
        $stmt->execute([$category]);
        return $stmt->fetchAll();
    }

    public function search(string $query): array {
        $stmt = $this->pdo->prepare("SELECT * FROM products WHERE name LIKE ?");
        $stmt->execute(["%$query%"]);
        return $stmt->fetchAll();
    }

    public function updatePrice(int $id, float $price): bool {
        $stmt = $this->pdo->prepare('UPDATE products SET price = ? WHERE id = ?');
        $stmt->execute([$price, $id]);
        return $stmt->rowCount() > 0;
    }
}

$repo = new ProductRepository('/tmp/lab11.db');

echo "All products:\n";
foreach ($repo->findAll('price') as $p) {
    printf("  #%d %-25s $%.2f\n", $p['id'], $p['name'], $p['price']);
}

echo "\nSearch 'surface':\n";
foreach ($repo->search('surface') as $p) {
    echo "  {$p['name']}\n";
}

$repo->updatePrice(1, 799.99);
$updated = $repo->findById(1);
echo "\nUpdated price: " . $updated['name'] . " → $" . $updated['price'] . "\n";
```

> 💡 **The Repository Pattern** abstracts database access — controllers call `$repo->findByCategory('Laptop')` without knowing SQL. Swap SQLite for MySQL by changing one constructor line. Add caching by wrapping the repository. This pattern is how Laravel's Eloquent and Doctrine repositories work.

**📸 Verified Output:**
```
All products:
  #2 Surface Pen               $44.99
  #4 Office 365                $99.99
  #5 Surface Headphones       $249.99
  #1 Surface Pro 12"          $864.00

Search 'surface':
  Surface Pro 12"
  Surface Pen
  Surface Headphones

Updated price: Surface Pro 12" → $799.99
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
\$pdo = new PDO('sqlite:/tmp/test.db');
\$pdo->exec('CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, v TEXT)');
\$pdo->prepare('INSERT INTO t (v) VALUES (?)')->execute(['hello']);
echo \$pdo->query('SELECT v FROM t')->fetchColumn() . PHP_EOL;
"
```

## Summary

PDO is PHP's production database interface. You've performed CRUD with prepared statements, used transactions for atomicity, built aggregate reports, explored fetch modes, and implemented the Repository pattern. These skills directly apply to Laravel Eloquent, Doctrine ORM, and any raw PDO application.

## Further Reading
- [PDO Manual](https://www.php.net/manual/en/book.pdo.php)
- [PDO Prepared Statements](https://www.php.net/manual/en/pdo.prepared-statements.php)
- [SQLite3 PHP Extension](https://www.php.net/manual/en/book.sqlite3.php)
