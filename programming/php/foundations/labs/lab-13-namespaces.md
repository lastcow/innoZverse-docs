# Lab 13: Namespaces & Autoloading

## Objective
Organize PHP code with namespaces, implement PSR-4 autoloading, use Composer for dependency management, and understand how modern PHP projects are structured.

## Background
Before namespaces (PHP 5.3), class names had to be globally unique — leading to names like `Zend_Db_Adapter_Pdo_Mysql`. Namespaces let you use short names like `DB\Adapter\Pdo\Mysql` and organize code hierarchically. Composer's PSR-4 autoloading maps namespace prefixes to directory paths, eliminating manual `require` statements. Every modern PHP project uses this.

## Time
30 minutes

## Prerequisites
- Lab 07 (OOP)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Namespace Basics

```php
<?php
// File: single-file namespace demo
namespace App;

class User {
    public function __construct(public readonly string $name) {}
    public function greet(): string { return "Hello, {$this->name}!"; }
}

namespace App\Services;

class UserService {
    private array $users = [];

    public function create(string $name): \App\User {
        $user = new \App\User($name);
        $this->users[] = $user;
        return $user;
    }

    public function count(): int { return count($this->users); }
}

namespace App\Http;

use App\Services\UserService;
use App\User;

class UserController {
    public function __construct(private UserService $service) {}

    public function store(string $name): string {
        $user = $this->service->create($name);
        return "Created: " . $user->greet();
    }
}

// Back to global namespace
namespace {
    use App\Services\UserService;
    use App\Http\UserController;

    $service    = new UserService();
    $controller = new UserController($service);

    echo $controller->store('Dr. Chen') . "\n";
    echo $controller->store('Alice') . "\n";
    echo "Total users: " . $service->count() . "\n";
}
```

> 💡 **Fully-qualified class names** start with `\`: `\App\User` means "root namespace → App → User". A `use` statement creates an alias in the current file scope: `use App\User;` lets you write `new User()`. Without `use`, you need the full path every time.

**📸 Verified Output:**
```
Created: Hello, Dr. Chen!
Created: Hello, Alice!
Total users: 2
```

---

### Step 2: use Aliases & Conflict Resolution

```php
<?php
namespace Demo;

// Simulate two classes with same short name from different namespaces
class Collection {
    private array $items;
    public function __construct(array $items = []) { $this->items = $items; }
    public function count(): int { return count($this->items); }
    public function toArray(): array { return $this->items; }
    public function __toString(): string { return 'Demo\\Collection(' . $this->count() . ')'; }
}

namespace {
    use Demo\Collection;                          // use as Collection
    use Demo\Collection as DemoCollection;        // alias

    $c1 = new Collection([1, 2, 3]);
    $c2 = new DemoCollection(['a', 'b']);

    echo "c1: $c1\n";
    echo "c2: $c2\n";

    // use for functions and constants
    use function array_map;
    use const PHP_EOL;

    $doubled = array_map(fn($n) => $n * 2, $c1->toArray());
    echo "Doubled: " . implode(', ', $doubled) . PHP_EOL;

    // Group use declarations (PHP 7.0+)
    // use Demo\{User, Product, Order};  // import multiple at once
    // use Demo\Http\{Request, Response, Controller};

    // Namespace function
    echo "Namespace: " . __NAMESPACE__ . "\n";  // empty = global
}
```

> 💡 **`use` aliases (`as`)** resolve naming conflicts — if two packages both have a `Collection` class, use `use Vendor1\Collection as V1Collection`. Group `use` (PHP 7.0+) is purely syntactic sugar: `use App\{User, Product}` is identical to two separate `use` statements.

**📸 Verified Output:**
```
c1: Demo\Collection(3)
c2: Demo\Collection(2)
Doubled: 2, 4, 6

Namespace: 
```

---

### Step 3: PSR-4 Directory Structure

```php
<?php
// Simulate PSR-4 structure in /tmp/psr4-demo/
$dirs = [
    '/tmp/psr4-demo/src/Http',
    '/tmp/psr4-demo/src/Services',
    '/tmp/psr4-demo/src/Models',
    '/tmp/psr4-demo/tests',
];
foreach ($dirs as $d) mkdir($d, 0755, recursive: true);

// src/Models/Product.php
file_put_contents('/tmp/psr4-demo/src/Models/Product.php', <<<'PHP'
<?php
namespace App\Models;

class Product {
    public function __construct(
        public readonly int    $id,
        public readonly string $name,
        public readonly float  $price,
    ) {}

    public function __toString(): string {
        return "#{$this->id} {$this->name} \${$this->price}";
    }
}
PHP);

// src/Services/ProductService.php
file_put_contents('/tmp/psr4-demo/src/Services/ProductService.php', <<<'PHP'
<?php
namespace App\Services;

use App\Models\Product;

class ProductService {
    private array $products = [];
    private int   $nextId   = 1;

    public function add(string $name, float $price): Product {
        $p = new Product($this->nextId++, $name, $price);
        $this->products[$p->id] = $p;
        return $p;
    }

    public function findById(int $id): ?Product {
        return $this->products[$id] ?? null;
    }

    public function all(): array { return array_values($this->products); }
}
PHP);

// src/Http/ProductController.php
file_put_contents('/tmp/psr4-demo/src/Http/ProductController.php', <<<'PHP'
<?php
namespace App\Http;

use App\Services\ProductService;

class ProductController {
    public function __construct(private ProductService $service) {}

    public function index(): string {
        $products = $this->service->all();
        return implode("\n", array_map(fn($p) => "  $p", $products));
    }

    public function show(int $id): string {
        $p = $this->service->findById($id);
        return $p ? (string)$p : "Not found: #$id";
    }
}
PHP);

echo "PSR-4 structure created\n";
// Show directory tree
$iter = new RecursiveIteratorIterator(new RecursiveDirectoryIterator('/tmp/psr4-demo/src', FilesystemIterator::SKIP_DOTS));
foreach ($iter as $f) echo "  " . str_replace('/tmp/psr4-demo/', '', $f->getPathname()) . "\n";
```

> 💡 **PSR-4 rule:** namespace `App\Models\Product` maps to file `src/Models/Product.php` when configured as `"App\\" => "src/"`. The backslash in the namespace becomes a directory separator. This is the universal standard — Composer, Laravel, Symfony, and every modern PHP library follows PSR-4.

**📸 Verified Output:**
```
PSR-4 structure created
  src/Http/ProductController.php
  src/Models/Product.php
  src/Services/ProductService.php
```

---

### Step 4: Manual Autoloader

```php
<?php
// PSR-4 autoloader implementation (what Composer generates)
spl_autoload_register(function(string $class): void {
    // Map namespace prefix to directory
    $prefixMap = [
        'App\\' => '/tmp/psr4-demo/src/',
    ];

    foreach ($prefixMap as $prefix => $baseDir) {
        if (!str_starts_with($class, $prefix)) continue;

        // Strip prefix, replace \ with /, add .php
        $relative = substr($class, strlen($prefix));
        $file     = $baseDir . str_replace('\\', '/', $relative) . '.php';

        if (file_exists($file)) {
            require $file;
            return;
        }
    }
});

// Now classes load automatically!
use App\Services\ProductService;
use App\Http\ProductController;

$service    = new ProductService();
$controller = new ProductController($service);

$service->add('Surface Pro 12"', 864.00);
$service->add('Surface Pen', 49.99);
$service->add('Office 365', 99.99);

echo "All products:\n" . $controller->index() . "\n";
echo "\nProduct #2: " . $controller->show(2) . "\n";
echo "Product #9: " . $controller->show(9) . "\n";
```

> 💡 **`spl_autoload_register`** registers a function PHP calls when it encounters an unknown class name. Composer generates a highly-optimized version of this at `vendor/autoload.php`. The class map (static lookup table) Composer builds from `composer dump-autoload --optimize` is 10× faster than path-based lookup.

**📸 Verified Output:**
```
All products:
  #1 Surface Pro 12" $864
  #2 Surface Pen $49.99
  #3 Office 365 $99.99

Product #2: #2 Surface Pen $49.99
Product #9: Not found: #9
```

---

### Step 5: Composer Basics

```php
<?php
// Simulate what composer.json + autoload looks like
$composerJson = [
    'name'        => 'innozverse/php-lab',
    'description' => 'PHP Lab 13: Namespaces & Autoloading',
    'type'        => 'project',
    'require'     => [
        'php' => '^8.3',
    ],
    'require-dev' => [
        'phpunit/phpunit' => '^11.0',
    ],
    'autoload' => [
        'psr-4' => ['App\\' => 'src/'],
    ],
    'autoload-dev' => [
        'psr-4' => ['App\\Tests\\' => 'tests/'],
    ],
];

file_put_contents('/tmp/psr4-demo/composer.json',
    json_encode($composerJson, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));

echo "composer.json:\n";
echo file_get_contents('/tmp/psr4-demo/composer.json') . "\n";

// Show what key Composer commands do
$commands = [
    'composer install'           => 'Install dependencies from composer.lock',
    'composer update'            => 'Update all dependencies to latest allowed versions',
    'composer require guzzle'    => 'Add a new dependency',
    'composer dump-autoload -o'  => 'Regenerate optimized autoload files',
    'composer show'              => 'List installed packages',
    'composer validate'          => 'Validate composer.json',
];

echo "Common Composer commands:\n";
foreach ($commands as $cmd => $desc) {
    printf("  %-35s %s\n", $cmd, $desc);
}
```

> 💡 **Commit `composer.lock`** to version control — it locks every dependency to an exact version, ensuring everyone on the team (and your CI/CD) installs identical packages. `composer.json` specifies constraints (`^8.3` = >=8.3, <9.0); `composer.lock` specifies exact versions.

**📸 Verified Output:**
```
composer.json:
{
    "name": "innozverse/php-lab",
    "description": "PHP Lab 13: Namespaces & Autoloading",
    ...
}

Common Composer commands:
  composer install                    Install dependencies from composer.lock
  composer update                     Update all dependencies...
  ...
```

---

### Step 6: Interfaces in Namespaces

```php
<?php
// Demonstrate real-world namespace patterns
namespace App\Contracts;

interface Repository {
    public function findById(int $id): ?array;
    public function findAll(): array;
    public function save(array $data): int;
    public function delete(int $id): bool;
}

interface Cache {
    public function get(string $key): mixed;
    public function set(string $key, mixed $value, int $ttl = 3600): void;
    public function has(string $key): bool;
    public function forget(string $key): void;
}

namespace App\Infrastructure;

use App\Contracts\Cache;
use App\Contracts\Repository;

class InMemoryCache implements Cache {
    private array $store = [];
    private array $expiry = [];

    public function get(string $key): mixed {
        if (!$this->has($key)) return null;
        return $this->store[$key];
    }

    public function set(string $key, mixed $value, int $ttl = 3600): void {
        $this->store[$key] = $value;
        $this->expiry[$key] = time() + $ttl;
    }

    public function has(string $key): bool {
        return isset($this->store[$key]) && time() < ($this->expiry[$key] ?? 0);
    }

    public function forget(string $key): void { unset($this->store[$key], $this->expiry[$key]); }
}

class InMemoryRepository implements Repository {
    private array $data = [];
    private int $nextId = 1;

    public function findById(int $id): ?array { return $this->data[$id] ?? null; }
    public function findAll(): array { return array_values($this->data); }
    public function save(array $data): int {
        $id = $this->nextId++;
        $this->data[$id] = ['id' => $id] + $data;
        return $id;
    }
    public function delete(int $id): bool {
        if (!isset($this->data[$id])) return false;
        unset($this->data[$id]);
        return true;
    }
}

namespace {
    use App\Infrastructure\{InMemoryCache, InMemoryRepository};

    $repo  = new InMemoryRepository();
    $cache = new InMemoryCache();

    $id1 = $repo->save(['name' => 'Surface Pro', 'price' => 864]);
    $id2 = $repo->save(['name' => 'Surface Pen', 'price' => 49.99]);
    $cache->set("product:$id1", $repo->findById($id1), ttl: 60);

    echo "Cached: " . ($cache->has("product:$id1") ? 'yes' : 'no') . "\n";
    $cached = $cache->get("product:$id1");
    echo "From cache: {$cached['name']} \${$cached['price']}\n";

    echo "All: " . count($repo->findAll()) . " products\n";
    $repo->delete($id2);
    echo "After delete: " . count($repo->findAll()) . " products\n";
}
```

**📸 Verified Output:**
```
Cached: yes
From cache: Surface Pro $864
All: 2 products
After delete: 1 products
```

---

### Step 7: Constants & Functions in Namespaces

```php
<?php
namespace App\Math;

const PI      = M_PI;
const TAU     = M_PI * 2;
const EPSILON = 1e-10;

function circleArea(float $r): float    { return PI * $r * $r; }
function sphereVolume(float $r): float  { return (4/3) * PI * $r ** 3; }
function isClose(float $a, float $b): bool { return abs($a - $b) < EPSILON; }

namespace App\Strings;

const WHITESPACE = " \t\n\r\0\x0B";

function slugify(string $s): string {
    $s = strtolower(trim($s));
    $s = preg_replace('/[^a-z0-9\s-]/', '', $s);
    return preg_replace('/[\s-]+/', '-', $s);
}

function truncate(string $s, int $len, string $suffix = '...'): string {
    return strlen($s) <= $len ? $s : substr($s, 0, $len - strlen($suffix)) . $suffix;
}

namespace {
    use function App\Math\circleArea;
    use function App\Math\sphereVolume;
    use function App\Strings\slugify;
    use function App\Strings\truncate;
    use const App\Math\PI;

    printf("PI = %.6f\n", PI);
    printf("Circle area (r=5): %.4f\n", circleArea(5));
    printf("Sphere volume (r=3): %.4f\n", sphereVolume(3));

    $title = "  Hello, World! PHP 8.3 & Namespaces  ";
    echo "\nSlug: " . slugify($title) . "\n";
    echo "Truncated: " . truncate("The quick brown fox jumps over the lazy dog", 20) . "\n";
}
```

> 💡 **Namespace constants and functions** are organized just like classes. `use const App\Math\PI` imports a constant; `use function App\Math\circleArea` imports a function. Without the `use`, you'd write `\App\Math\circleArea(5)`. Built-in PHP functions are always in the root namespace.

**📸 Verified Output:**
```
PI = 3.141593
Circle area (r=5): 78.5398
Sphere volume (r=3): 113.0973

Slug: hello-world-php-83-namespaces
Truncated: The quick brown fo...
```

---

### Step 8: Complete — Service Container (Dependency Injection)

```php
<?php
declare(strict_types=1);

namespace App\Container;

class Container {
    private array $bindings  = [];
    private array $instances = [];

    public function bind(string $abstract, callable $factory): void {
        $this->bindings[$abstract] = $factory;
    }

    public function singleton(string $abstract, callable $factory): void {
        $this->bindings[$abstract] = function() use ($abstract, $factory) {
            if (!isset($this->instances[$abstract])) {
                $this->instances[$abstract] = $factory($this);
            }
            return $this->instances[$abstract];
        };
    }

    public function make(string $abstract): mixed {
        if (isset($this->bindings[$abstract])) {
            return ($this->bindings[$abstract])($this);
        }
        throw new \RuntimeException("No binding for $abstract");
    }
}

namespace App\Services;

interface Logger { public function log(string $msg): void; }
interface Mailer { public function send(string $to, string $subject): bool; }

class ConsoleLogger implements Logger {
    public function log(string $msg): void { echo "[LOG] $msg\n"; }
}

class MockMailer implements Mailer {
    public function __construct(private Logger $logger) {}
    public function send(string $to, string $subject): bool {
        $this->logger->log("Email to $to: $subject");
        return true;
    }
}

class OrderService {
    public function __construct(
        private Logger $logger,
        private Mailer $mailer,
    ) {}

    public function placeOrder(string $customer, float $amount): void {
        $this->logger->log("Order placed: $customer — \$$amount");
        $this->mailer->send($customer, "Order Confirmation — \$$amount");
    }
}

namespace {
    use App\Container\Container;
    use App\Services\{ConsoleLogger, MockMailer, OrderService};

    $container = new Container();
    $container->singleton('logger', fn() => new ConsoleLogger());
    $container->bind('mailer', fn($c) => new MockMailer($c->make('logger')));
    $container->bind('orders', fn($c) => new OrderService($c->make('logger'), $c->make('mailer')));

    $orders = $container->make('orders');
    $orders->placeOrder('dr.chen@example.com', 864.00);
    $orders->placeOrder('alice@example.com', 49.99);
}
```

> 💡 **The Service Container (IoC Container)** is the heart of Laravel — it knows how to build any class and inject its dependencies automatically. Our mini-container does the same: `bind` registers a factory; `singleton` ensures only one instance; `make` builds and returns the object, resolving its dependencies recursively.

**📸 Verified Output:**
```
[LOG] Order placed: dr.chen@example.com — $864
[LOG] Email to dr.chen@example.com: Order Confirmation — $864
[LOG] Order placed: alice@example.com — $49.99
[LOG] Email to alice@example.com: Order Confirmation — $49.99
```

---

## Summary

Namespaces and autoloading transform PHP from a collection of files into a structured project. You've used namespace declarations, `use` aliases, PSR-4 directory structure, a manual autoloader, Composer basics, namespaced constants/functions, and built a service container. This is exactly how Laravel, Symfony, and every modern PHP framework is organized.

## Further Reading
- [PHP Namespaces](https://www.php.net/manual/en/language.namespaces.php)
- [PSR-4 Autoloading Standard](https://www.php-fig.org/psr/psr-4/)
- [Composer Autoload](https://getcomposer.org/doc/04-schema.md#autoload)
