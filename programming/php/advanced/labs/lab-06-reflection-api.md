# Lab 06: Reflection API & Dependency Injection

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

PHP's Reflection API allows introspecting classes, methods, properties, and attributes at runtime. This enables powerful patterns like dependency injection containers, ORMs, and serialization frameworks.

---

## Step 1: ReflectionClass Basics

```php
<?php
class UserService {
    public function __construct(
        private readonly string $name,
        private int $age = 30
    ) {}

    public function greet(): string { return 'Hello ' . $this->name; }

    #[\Deprecated('Use greet() instead')]
    public function hello(): string { return $this->greet(); }
}

$rc = new ReflectionClass(UserService::class);

echo "Class: "     . $rc->getName() . "\n";
echo "Short name: " . $rc->getShortName() . "\n";
echo "Abstract: "   . ($rc->isAbstract() ? 'yes' : 'no') . "\n";
echo "Final: "      . ($rc->isFinal() ? 'yes' : 'no') . "\n";

echo "\nMethods:\n";
foreach ($rc->getMethods() as $method) {
    $vis = $method->isPublic() ? 'public' : ($method->isProtected() ? 'protected' : 'private');
    echo "  $vis {$method->getName()}()\n";
}
```

📸 **Verified Output:**
```
Class: UserService
Short name: UserService
Abstract: no
Final: no

Methods:
  public __construct()
  public greet()
  public hello()
```

---

## Step 2: Inspecting Properties

```php
<?php
class UserService {
    public function __construct(
        private readonly string $name,
        private int $age = 30
    ) {}
    public function greet(): string { return 'Hello ' . $this->name; }
}

$rc = new ReflectionClass(UserService::class);

echo "Properties:\n";
foreach ($rc->getProperties() as $prop) {
    $vis = $prop->isPublic() ? 'public' : ($prop->isProtected() ? 'protected' : 'private');
    $ro  = $prop->isReadOnly() ? ' readonly' : '';
    echo "  $vis$ro {$prop->getType()} \${$prop->getName()}\n";
}

echo "\nConstructor parameters:\n";
$ctor = $rc->getConstructor();
foreach ($ctor->getParameters() as $param) {
    $optional = $param->isOptional() ? ' [optional=' . json_encode($param->getDefaultValue()) . ']' : '';
    echo "  \${$param->getName()}: {$param->getType()}$optional\n";
}
```

📸 **Verified Output:**
```
Properties:
  private readonly string $name
  private int $age

Constructor parameters:
  $name: string
  $age: int [optional=30]
```

---

## Step 3: Invoking Methods via Reflection

```php
<?php
class Calculator {
    private float $memory = 0;

    public function add(float $a, float $b): float { return $a + $b; }
    public function multiply(float $a, float $b): float { return $a * $b; }
    private function storeMemory(float $value): void { $this->memory = $value; }
    public function getMemory(): float { return $this->memory; }
}

$rc  = new ReflectionClass(Calculator::class);
$obj = $rc->newInstance();

// Invoke public method
$add = $rc->getMethod('add');
$result = $add->invoke($obj, 3.5, 4.5);
echo "add(3.5, 4.5) = $result\n";

// Invoke private method (make accessible)
$store = $rc->getMethod('storeMemory');
$store->setAccessible(true);
$store->invoke($obj, 42.0);
echo "Memory: " . $obj->getMemory() . "\n";

// Dynamic method dispatch
$methods = ['add' => [10, 20], 'multiply' => [3, 7]];
foreach ($methods as $methodName => $args) {
    $m = $rc->getMethod($methodName);
    echo "$methodName(" . implode(', ', $args) . ") = " . $m->invoke($obj, ...$args) . "\n";
}
```

📸 **Verified Output:**
```
add(3.5, 4.5) = 8
Memory: 42
add(10, 20) = 30
multiply(3, 7) = 21
```

> 💡 `setAccessible(true)` bypasses visibility — use only in test code or framework internals.

---

## Step 4: Reading Attributes via Reflection

```php
<?php
#[Attribute(Attribute::TARGET_CLASS | Attribute::TARGET_METHOD)]
class Route {
    public function __construct(
        public readonly string $path,
        public readonly string $method = 'GET'
    ) {}
}

#[Route('/users')]
class UserController {
    #[Route('/users/{id}', 'GET')]
    public function show(int $id): void {}

    #[Route('/users', 'POST')]
    public function create(): void {}
}

$rc = new ReflectionClass(UserController::class);

// Class-level attributes
foreach ($rc->getAttributes(Route::class) as $attr) {
    $route = $attr->newInstance();
    echo "Controller base: {$route->method} {$route->path}\n";
}

// Method-level attributes
foreach ($rc->getMethods() as $method) {
    foreach ($method->getAttributes(Route::class) as $attr) {
        $route = $attr->newInstance();
        echo "{$route->method} {$route->path} → {$method->getName()}()\n";
    }
}
```

📸 **Verified Output:**
```
Controller base: GET /users
GET /users/{id} → show()
POST /users → create()
```

---

## Step 5: Dynamic Proxy Pattern

```php
<?php
interface Logger {
    public function log(string $message): void;
}

class ConsoleLogger implements Logger {
    public function log(string $message): void {
        echo "[LOG] $message\n";
    }
}

// Proxy using __call magic + reflection
class LoggingProxy {
    private \ReflectionClass $reflection;

    public function __construct(private object $target) {
        $this->reflection = new \ReflectionClass($target);
    }

    public function __call(string $name, array $args): mixed {
        $method = $this->reflection->getMethod($name);

        // Before
        $params = array_map(fn($p) => $p->getName(), $method->getParameters());
        $argStr = implode(', ', array_map(
            fn($k, $v) => $params[$k] . '=' . json_encode($v),
            array_keys($args), $args
        ));
        echo "→ Calling {$name}($argStr)\n";

        $start = microtime(true);
        $result = $method->invoke($this->target, ...$args);
        $elapsed = round((microtime(true) - $start) * 1000, 3);

        echo "← {$name} returned in {$elapsed}ms\n";
        return $result;
    }
}

class UserRepository {
    public function findById(int $id): array {
        return ['id' => $id, 'name' => 'Alice', 'email' => 'alice@example.com'];
    }
    public function save(array $user): bool {
        return true;
    }
}

$repo = new LoggingProxy(new UserRepository());
$user = $repo->findById(42);
echo "Got: {$user['name']}\n";
$repo->save(['id' => 43, 'name' => 'Bob']);
```

📸 **Verified Output:**
```
→ Calling findById(id=42)
← findById returned in 0.001ms
Got: Alice
→ Calling save(user={"id":43,"name":"Bob"})
← save returned in 0.001ms
```

---

## Step 6: Reflection for Cloning & Deep Copy

```php
<?php
class Config {
    private array $data = [];
    private bool $locked = false;

    public function set(string $key, mixed $value): void {
        if ($this->locked) throw new \RuntimeException("Config is locked");
        $this->data[$key] = $value;
    }

    public function get(string $key): mixed {
        return $this->data[$key] ?? null;
    }
}

// Clone and modify private property via reflection
$original = new Config();
$original->set('db', 'mysql://localhost');
$original->set('cache', 'redis://localhost');

$clone = clone $original;

// Force-unlock the clone via reflection
$rc = new ReflectionClass($clone);
$lockedProp = $rc->getProperty('locked');
$lockedProp->setAccessible(true);
$lockedProp->setValue($clone, false);

$dataProp = $rc->getProperty('data');
$dataProp->setAccessible(true);
$data = $dataProp->getValue($clone);
$data['db'] = 'pgsql://prod-server';
$dataProp->setValue($clone, $data);

echo "Original DB: " . $original->get('db') . "\n";
echo "Clone DB:    " . $clone->get('db') . "\n";
echo "Original cache: " . $original->get('cache') . "\n";
echo "Clone cache:    " . $clone->get('cache') . "\n";
```

📸 **Verified Output:**
```
Original DB: mysql://localhost
Clone DB:    pgsql://prod-server
Original cache: redis://localhost
Clone cache:    redis://localhost
```

---

## Step 7: Constructor Parameter Inspection

```php
<?php
function inspectConstructor(string $class): void {
    $rc = new ReflectionClass($class);
    $ctor = $rc->getConstructor();

    if ($ctor === null) {
        echo "$class has no constructor\n";
        return;
    }

    echo "$class constructor:\n";
    foreach ($ctor->getParameters() as $i => $param) {
        $type    = $param->getType()?->getName() ?? 'mixed';
        $default = $param->isOptional()
            ? ' = ' . json_encode($param->isDefaultValueAvailable() ? $param->getDefaultValue() : 'n/a')
            : ' (required)';
        $promoted = $param->isPromoted() ? ' [promoted]' : '';
        printf("  #%d \$%-15s : %-10s%s%s\n", $i, $param->getName(), $type, $default, $promoted);
    }
}

class DatabaseConnection {
    public function __construct(
        private string $host,
        private int    $port = 3306,
        private string $database = 'default',
        private bool   $ssl = false,
    ) {}
}

inspectConstructor(DatabaseConnection::class);
```

📸 **Verified Output:**
```
DatabaseConnection constructor:
  #0 $host            : string     (required) [promoted]
  #1 $port            : int        = 3306 [promoted]
  #2 $database        : string     = "default" [promoted]
  #3 $ssl             : bool       = false [promoted]
```

---

## Step 8: Capstone — Dependency Injection Container

```php
<?php
interface Cache {
    public function get(string $key): mixed;
    public function set(string $key, mixed $value): void;
}

class InMemoryCache implements Cache {
    private array $store = [];
    public function get(string $key): mixed { return $this->store[$key] ?? null; }
    public function set(string $key, mixed $value): void { $this->store[$key] = $value; }
}

class UserRepository {
    public function __construct(private Cache $cache) {}
    public function find(int $id): array {
        $key = "user:$id";
        if ($cached = $this->cache->get($key)) {
            echo "  [cache hit] user $id\n";
            return $cached;
        }
        $user = ['id' => $id, 'name' => 'User ' . $id];
        $this->cache->set($key, $user);
        echo "  [cache miss] loaded user $id\n";
        return $user;
    }
}

class UserService {
    public function __construct(private UserRepository $repo) {}
    public function getUser(int $id): array { return $this->repo->find($id); }
}

class Container {
    private array $bindings = [];
    private array $singletons = [];

    public function bind(string $abstract, string|callable $concrete): void {
        $this->bindings[$abstract] = $concrete;
    }

    public function make(string $class): object {
        if (isset($this->singletons[$class])) {
            return $this->singletons[$class];
        }

        // Check if there's a binding (interface → implementation)
        $concrete = $this->bindings[$class] ?? $class;
        if (is_callable($concrete)) {
            return $concrete($this);
        }

        $rc = new ReflectionClass($concrete);
        $ctor = $rc->getConstructor();

        if ($ctor === null) {
            return $rc->newInstance();
        }

        $deps = [];
        foreach ($ctor->getParameters() as $param) {
            $type = $param->getType();
            if ($type instanceof ReflectionNamedType && !$type->isBuiltin()) {
                $deps[] = $this->make($type->getName());
            } elseif ($param->isOptional()) {
                $deps[] = $param->getDefaultValue();
            } else {
                throw new \RuntimeException("Cannot resolve: \${$param->getName()} in $concrete");
            }
        }

        $instance = $rc->newInstanceArgs($deps);
        $this->singletons[$class] = $instance;
        return $instance;
    }
}

// Wire up
$container = new Container();
$container->bind(Cache::class, InMemoryCache::class);

$service = $container->make(UserService::class);
$user1 = $service->getUser(42);
$user2 = $service->getUser(42);  // Should hit cache
$user3 = $service->getUser(99);

echo "User 42: {$user1['name']}\n";
echo "User 99: {$user3['name']}\n";
```

📸 **Verified Output:**
```
  [cache miss] loaded user 42
  [cache hit] user 42
  [cache miss] loaded user 99
User 42: User 42
User 99: User 99
```

---

## Summary

| Class | Key Methods | Use Case |
|---|---|---|
| `ReflectionClass` | `getMethods()`, `getProperties()`, `getConstructor()`, `getAttributes()` | Inspect class structure |
| `ReflectionMethod` | `invoke()`, `getParameters()`, `setAccessible()` | Dynamic method calls |
| `ReflectionProperty` | `getValue()`, `setValue()`, `setAccessible()`, `isReadOnly()` | Access private state |
| `ReflectionParameter` | `getType()`, `isOptional()`, `getDefaultValue()`, `isPromoted()` | Constructor analysis |
| `ReflectionNamedType` | `getName()`, `isBuiltin()`, `allowsNull()` | Type-based injection |
| DI Container | Reflection + recursion | Auto-wire constructor deps |
| Proxy Pattern | `__call` + `ReflectionMethod` | Transparent decoration |
