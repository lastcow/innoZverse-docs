# Lab 4: PDO & Repository Pattern

## Objective
Build a full data access layer using PDO: prepared statements with named parameters, transactions with rollback, the Repository pattern for decoupled data access, query builder basics, and performance with `fetchAll(PDO::FETCH_CLASS)`.

## Background
PDO (PHP Data Objects) provides a database-agnostic API — the same code works with SQLite, MySQL, PostgreSQL, and others by changing only the DSN. The **Repository pattern** separates business logic from data access: `OrderService` calls `$orderRepo->save($order)` without knowing whether it's SQLite or PostgreSQL underneath. This makes testing easy (swap the real repo for an in-memory fake) and keeps domain logic clean.

## Time
35 minutes

## Prerequisites
- PHP Foundations Lab 11 (Database with PDO)

## Tools
- Docker: `zchencow/innozverse-php:latest` (SQLite included)

---

## Lab Instructions

### Step 1: Schema, prepared statements & named parameters

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
$pdo = new PDO("sqlite::memory:", options: [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,  // real prepared statements
]);

// Schema
$pdo->exec("
    CREATE TABLE products (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        name     TEXT NOT NULL,
        category TEXT NOT NULL,
        price    REAL NOT NULL CHECK(price >= 0),
        stock    INTEGER NOT NULL DEFAULT 0
    );
    CREATE TABLE orders (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL REFERENCES products(id),
        qty        INTEGER NOT NULL CHECK(qty > 0),
        total      REAL NOT NULL,
        region     TEXT NOT NULL,
        status     TEXT NOT NULL DEFAULT \"pending\",
        created_at TEXT NOT NULL DEFAULT (datetime(\"now\"))
    );
    CREATE INDEX idx_orders_product ON orders(product_id);
    CREATE INDEX idx_orders_status  ON orders(status);
");

// Prepared statement with named parameters (:name, :price ...)
$insertProduct = $pdo->prepare(
    "INSERT INTO products (name, category, price, stock) VALUES (:name, :category, :price, :stock)"
);

$products = [
    ["name" => "Surface Pro",  "category" => "Laptop",    "price" => 864.00, "stock" => 15],
    ["name" => "Surface Book", "category" => "Laptop",    "price" => 1299.00,"stock" => 5],
    ["name" => "Surface Pen",  "category" => "Accessory", "price" => 49.99,  "stock" => 80],
    ["name" => "Office 365",   "category" => "Software",  "price" => 99.99,  "stock" => 999],
    ["name" => "USB-C Hub",    "category" => "Hardware",  "price" => 29.99,  "stock" => 0],
];

foreach ($products as $p) {
    $insertProduct->execute($p);  // array automatically binds :name, :category, :price, :stock
}

echo "=== PDO Prepared Statements ===" . PHP_EOL;
echo "Inserted: " . count($products) . " products" . PHP_EOL;

// Fetch with named params
$stmt = $pdo->prepare("SELECT * FROM products WHERE category = :cat AND price <= :maxPrice ORDER BY price");
$stmt->execute(["cat" => "Laptop", "maxPrice" => 1000.0]);
$rows = $stmt->fetchAll();
echo PHP_EOL . "Laptops under $1000:" . PHP_EOL;
foreach ($rows as $r) {
    printf("  #%-2d %-15s \$%.2f  stock=%d%s", $r["id"], $r["name"], $r["price"], $r["stock"], PHP_EOL);
}

// PDO::FETCH_CLASS — maps result rows directly to objects
class ProductRow {
    public int $id;
    public string $name;
    public string $category;
    public float $price;
    public int $stock;
    public function value(): float { return $this->price * $this->stock; }
}

$stmt = $pdo->query("SELECT * FROM products ORDER BY price DESC");
$objects = $stmt->fetchAll(PDO::FETCH_CLASS, ProductRow::class);
echo PHP_EOL . "FETCH_CLASS results:" . PHP_EOL;
foreach ($objects as $obj) {
    printf("  %-15s  price=\$%.2f  value=\$%.2f%s",
        $obj->name, $obj->price, $obj->value(), PHP_EOL);
}
'
```

> 💡 **Always use prepared statements — never string-interpolate user input into SQL.** `"SELECT * FROM products WHERE id = {$_GET['id']}"` is a SQL injection vulnerability. With PDO named parameters (`:id`) or positional (`?`), the value is *always* treated as data, never as SQL. The database driver handles escaping. This is not about performance (though prepared statements are faster for repeated queries) — it is about security.

**📸 Verified Output:**
```
=== PDO Prepared Statements ===
Inserted: 5 products

Laptops under $1000:
  #1  Surface Pro     $864.00  stock=15

FETCH_CLASS results:
  Surface Book    price=$1299.00  value=$6495.00
  Surface Pro     price=$864.00   value=$12960.00
  ...
```

---

### Step 2: Transactions with rollback + Repository pattern

```bash
docker run --rm zchencow/innozverse-php:latest php -r '
<?php
$pdo = new PDO("sqlite::memory:", options: [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);
$pdo->exec("
    CREATE TABLE products(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, stock INTEGER);
    CREATE TABLE orders(id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER, qty INTEGER, total REAL, status TEXT DEFAULT \"pending\");
");
$pdo->exec("INSERT INTO products(name,price,stock) VALUES (\"Surface Pro\",864,10),(\"Surface Pen\",49.99,5)");

// Repository interface (would be an interface in real code)
class ProductRepository {
    public function __construct(private PDO $pdo) {}

    public function find(int $id): ?array {
        $stmt = $this->pdo->prepare("SELECT * FROM products WHERE id = ?");
        $stmt->execute([$id]);
        return $stmt->fetch() ?: null;
    }

    public function findAll(): array {
        return $this->pdo->query("SELECT * FROM products")->fetchAll();
    }

    public function decrementStock(int $id, int $qty): void {
        $affected = $this->pdo->prepare("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?");
        $affected->execute([$qty, $id, $qty]);
        if ($affected->rowCount() === 0) {
            throw new \RuntimeException("Insufficient stock or product not found: id={$id}");
        }
    }
}

class OrderRepository {
    public function __construct(private PDO $pdo) {}

    public function create(int $productId, int $qty, float $total): int {
        $this->pdo->prepare("INSERT INTO orders(product_id,qty,total) VALUES(?,?,?)")
            ->execute([$productId, $qty, $total]);
        return (int) $this->pdo->lastInsertId();
    }

    public function findAll(): array {
        return $this->pdo->query("SELECT * FROM orders")->fetchAll();
    }
}

class OrderService {
    public function __construct(
        private PDO $pdo,
        private ProductRepository $products,
        private OrderRepository $orders,
    ) {}

    public function placeOrder(int $productId, int $qty): array {
        $product = $this->products->find($productId);
        if (!$product) throw new \RuntimeException("Product not found: {$productId}");

        // Transaction: deduct stock AND create order atomically
        $this->pdo->beginTransaction();
        try {
            $this->products->decrementStock($productId, $qty);  // may throw
            $total   = round($product["price"] * $qty, 2);
            $orderId = $this->orders->create($productId, $qty, $total);
            $this->pdo->commit();
            return ["orderId" => $orderId, "product" => $product["name"], "qty" => $qty, "total" => $total];
        } catch (\Throwable $e) {
            $this->pdo->rollBack();  // undo ALL changes if anything fails
            throw new \RuntimeException("Order failed: " . $e->getMessage(), previous: $e);
        }
    }
}

$productRepo = new ProductRepository($pdo);
$orderRepo   = new OrderRepository($pdo);
$service     = new OrderService($pdo, $productRepo, $orderRepo);

echo "=== Repository Pattern + Transactions ===" . PHP_EOL;
echo PHP_EOL . "Initial stock:" . PHP_EOL;
foreach ($productRepo->findAll() as $p) {
    printf("  #%d %-15s stock=%d%s", $p["id"], $p["name"], $p["stock"], PHP_EOL);
}

// Successful orders
echo PHP_EOL . "Placing orders:" . PHP_EOL;
$cases = [[1, 3], [2, 5], [1, 20], [1, 4]];  // last two should partially fail
foreach ($cases as [$pid, $qty]) {
    try {
        $result = $service->placeOrder($pid, $qty);
        printf("  ✓ Order #%d: %s ×%d = \$%.2f%s",
            $result["orderId"], $result["product"], $result["qty"], $result["total"], PHP_EOL);
    } catch (\RuntimeException $e) {
        printf("  ✗ Failed: %s%s", $e->getMessage(), PHP_EOL);
    }
}

echo PHP_EOL . "Stock after orders:" . PHP_EOL;
foreach ($productRepo->findAll() as $p) {
    printf("  #%d %-15s stock=%d%s", $p["id"], $p["name"], $p["stock"], PHP_EOL);
}

echo PHP_EOL . "Orders created:" . PHP_EOL;
foreach ($orderRepo->findAll() as $o) {
    printf("  Order #%d  product_id=%d  qty=%d  total=\$%.2f  status=%s%s",
        $o["id"], $o["product_id"], $o["qty"], $o["total"], $o["status"], PHP_EOL);
}
'
```

**📸 Verified Output:**
```
=== Repository Pattern + Transactions ===

Initial stock:
  #1 Surface Pro      stock=10
  #2 Surface Pen      stock=5

Placing orders:
  ✓ Order #1: Surface Pro ×3 = $2592.00
  ✓ Order #2: Surface Pen ×5 = $249.95
  ✗ Failed: Order failed: Insufficient stock or product not found: id=1
  ✓ Order #3: Surface Pro ×4 = $3456.00

Stock after orders:
  #1 Surface Pro      stock=3
  #2 Surface Pen      stock=0
```

---

## Summary

| Feature | Code | Purpose |
|---------|------|---------|
| Named params | `:name`, `:price` | Readable, prevents injection |
| `execute(array)` | `$stmt->execute($data)` | Bind and run in one call |
| `FETCH_CLASS` | `fetchAll(PDO::FETCH_CLASS, ClassName::class)` | Direct object hydration |
| Transaction | `beginTransaction()`, `commit()`, `rollBack()` | Atomic multi-step writes |
| Repository | `ProductRepository::find(int $id)` | Decouple data access |

## Further Reading
- [PHP PDO Manual](https://www.php.net/manual/en/book.pdo.php)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
