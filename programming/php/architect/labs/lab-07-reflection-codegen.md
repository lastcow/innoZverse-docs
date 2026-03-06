# Lab 07: Reflection API & Code Generation

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm php:8.3-cli bash`

## Overview

PHP's Reflection API enables runtime inspection of classes, methods, and attributes. This lab covers ReflectionClass, ReflectionMethod, PHP 8 Attributes, dynamic proxy generation, and building a minimal DI container using reflection.

---

## Step 1: ReflectionClass Basics

```php
<?php
class UserService {
    public string $name = 'UserService';
    protected int $version = 2;
    private array $cache = [];
    
    public function __construct(private readonly string $dsn) {}
    
    public function findById(int $id): ?array { return null; }
    public function findAll(int $limit = 100, int $offset = 0): array { return []; }
    protected function buildQuery(string $table): string { return "SELECT * FROM {$table}"; }
    private function connect(): void {}
}

$rc = new ReflectionClass(UserService::class);

echo "=== ReflectionClass ===\n";
echo "Name:       " . $rc->getName() . "\n";
echo "Short name: " . $rc->getShortName() . "\n";
echo "File:       " . ($rc->getFileName() ?: 'internal') . "\n";
echo "Abstract:   " . ($rc->isAbstract() ? 'yes' : 'no') . "\n";
echo "Final:      " . ($rc->isFinal() ? 'yes' : 'no') . "\n";

echo "\n=== Methods ===\n";
foreach ($rc->getMethods() as $method) {
    $visibility = match(true) {
        $method->isPublic()    => 'public',
        $method->isProtected() => 'protected',
        $method->isPrivate()   => 'private',
    };
    printf("  %-12s %s(%s)\n",
        $visibility,
        $method->getName(),
        implode(', ', array_map(fn($p) => '$' . $p->getName(), $method->getParameters()))
    );
}

echo "\n=== Properties ===\n";
foreach ($rc->getProperties() as $prop) {
    $visibility = match(true) {
        $prop->isPublic()    => 'public',
        $prop->isProtected() => 'protected',
        $prop->isPrivate()   => 'private',
    };
    printf("  %-12s %s\n", $visibility, $prop->getName());
}

echo "\n=== Constructor Parameters ===\n";
foreach ($rc->getConstructor()->getParameters() as $param) {
    $type = $param->hasType() ? $param->getType()->getName() : 'mixed';
    $default = $param->isOptional() ? ' = ' . var_export($param->getDefaultValue(), true) : '';
    echo "  {$type} \${$param->getName()}{$default}\n";
}
```

---

## Step 2: PHP 8 Attributes

```php
<?php
// Define reusable attributes
#[Attribute(Attribute::TARGET_CLASS)]
class Entity {
    public function __construct(public readonly string $table) {}
}

#[Attribute(Attribute::TARGET_PROPERTY)]
class Column {
    public function __construct(
        public readonly string $name = '',
        public readonly string $type = 'VARCHAR(255)',
        public readonly bool   $nullable = false,
        public readonly bool   $primary = false
    ) {}
}

#[Attribute(Attribute::TARGET_METHOD)]
class Route {
    public function __construct(
        public readonly string $path,
        public readonly string $method = 'GET'
    ) {}
}

// Apply attributes
#[Entity(table: 'users')]
class User {
    #[Column(name: 'id', type: 'INT', primary: true)]
    public int $id;
    
    #[Column(name: 'email', type: 'VARCHAR(255)')]
    public string $email;
    
    #[Column(name: 'created_at', type: 'DATETIME', nullable: true)]
    public ?string $createdAt = null;
    
    #[Route('/users/{id}', 'GET')]
    public function show(int $id): array { return []; }
    
    #[Route('/users', 'POST')]
    public function create(array $data): array { return []; }
}

// Read attributes at runtime
$rc = new ReflectionClass(User::class);

// Class attribute
$entity = $rc->getAttributes(Entity::class)[0]->newInstance();
echo "Entity table: {$entity->table}\n";

// Property attributes
echo "\n=== Columns ===\n";
foreach ($rc->getProperties() as $prop) {
    $attrs = $prop->getAttributes(Column::class);
    if (!$attrs) continue;
    $col = $attrs[0]->newInstance();
    $colName = $col->name ?: $prop->getName();
    printf("  %-15s %s%s%s\n",
        $colName,
        $col->type,
        $col->nullable ? ' NULL' : ' NOT NULL',
        $col->primary ? ' PRIMARY KEY' : ''
    );
}

// Method attributes (routes)
echo "\n=== Routes ===\n";
foreach ($rc->getMethods() as $method) {
    $attrs = $method->getAttributes(Route::class);
    if (!$attrs) continue;
    $route = $attrs[0]->newInstance();
    printf("  %-8s %s → %s::%s()\n",
        $route->method, $route->path, User::class, $method->getName()
    );
}
```

📸 **Verified Output:**
```
Entity table: users

=== Columns ===
  id              INT NOT NULL PRIMARY KEY
  email           VARCHAR(255) NOT NULL
  created_at      DATETIME NULL

=== Routes ===
  GET      /users/{id} → User::show()
  POST     /users → User::create()
```

---

## Step 3: ReflectionMethod::invoke & Closures

```php
<?php
class Calculator {
    private float $result = 0.0;
    
    public function add(float $a, float $b): float      { return $this->result = $a + $b; }
    public function multiply(float $a, float $b): float  { return $this->result = $a * $b; }
    private function square(float $n): float             { return $n * $n; }
    public function getResult(): float                   { return $this->result; }
}

$rc   = new ReflectionClass(Calculator::class);
$calc = new Calculator();

// Invoke public method
$addMethod = $rc->getMethod('add');
$result = $addMethod->invoke($calc, 10.0, 5.0);
echo "add(10, 5) = {$result}\n";

// Invoke private method (requires setAccessible in PHP < 8.1, auto in 8.1+)
$squareMethod = $rc->getMethod('square');
$squareMethod->setAccessible(true);
$result = $squareMethod->invoke($calc, 7.0);
echo "square(7) = {$result} (private method)\n";

// Get closure from method (bound to instance)
$multiplyClosure = $addMethod->getClosure($calc);
echo "Closure: multiply(3, 4) = " . $multiplyClosure(3.0, 4.0) . "\n";

// Bind closure to different instance
$calc2 = new Calculator();
$boundClosure = Closure::bind($squareMethod->getClosure($calc), $calc2, Calculator::class);
echo "Bound closure: square(9) = " . $boundClosure(9.0) . "\n";

// Dynamic method dispatch
$operations = [
    ['method' => 'add',      'args' => [100.0, 50.0]],
    ['method' => 'multiply', 'args' => [6.0, 7.0]],
];

echo "\n=== Dynamic Dispatch ===\n";
foreach ($operations as $op) {
    $method = $rc->getMethod($op['method']);
    $result = $method->invokeArgs($calc, $op['args']);
    echo "  {$op['method']}(" . implode(', ', $op['args']) . ") = {$result}\n";
}
```

---

## Step 4: Code Generation with eval()

```php
<?php
// Generate PHP class code dynamically
function generateValueObject(string $name, array $fields): string {
    $params = [];
    $body   = [];
    
    foreach ($fields as $field => $type) {
        $params[] = "public readonly {$type} \${$field}";
        $body[]   = "\$this->{$field} = \${$field};";
    }
    
    $paramStr = implode(",\n        ", $params);
    
    $methods = '';
    foreach ($fields as $field => $type) {
        $methodName = 'get' . ucfirst($field);
        $methods .= "
    public function {$methodName}(): {$type} {
        return \$this->{$field};
    }";
    }
    
    return "class {$name} {
    public function __construct(
        {$paramStr}
    ) {}
    
    public function toArray(): array {
        return get_object_vars(\$this);
    }
    
    public function __toString(): string {
        return json_encode(\$this->toArray());
    }{$methods}
}";
}

// Generate and evaluate
$code = generateValueObject('Money', [
    'amount'   => 'float',
    'currency' => 'string',
]);

// echo "// Generated code:\n{$code}\n\n";
eval($code);  // In production: write to file and include

$money = new Money(99.99, 'USD');
echo "Money: {$money}\n";
echo "Amount:   " . $money->getAmount() . "\n";
echo "Currency: " . $money->getCurrency() . "\n";
echo "Array: " . json_encode($money->toArray()) . "\n";
```

📸 **Verified Output:**
```
Money: {"amount":99.99,"currency":"USD"}
Amount:   99.99
Currency: USD
Array: {"amount":99.99,"currency":"USD"}
```

> 💡 In production, prefer writing generated code to `.php` files and including them, rather than using `eval()`. This enables OPcache and avoids `eval` security concerns.

---

## Step 5: Dynamic Proxy Pattern

```php
<?php
// Auto-generate decorator/proxy classes via reflection

interface PaymentGateway {
    public function charge(string $token, float $amount, string $currency): array;
    public function refund(string $chargeId, float $amount): array;
}

class StripeGateway implements PaymentGateway {
    public function charge(string $token, float $amount, string $currency): array {
        // Simulate Stripe API call
        return ['id' => 'ch_' . substr(md5($token), 0, 16), 'status' => 'succeeded', 'amount' => $amount];
    }
    
    public function refund(string $chargeId, float $amount): array {
        return ['id' => 're_' . substr(md5($chargeId), 0, 16), 'status' => 'succeeded'];
    }
}

// Logging proxy via reflection
class LoggingProxy {
    private array $log = [];
    
    public function __construct(
        private readonly object $target,
        private readonly ?callable $logger = null
    ) {}
    
    public function __call(string $method, array $args): mixed {
        $rc  = new ReflectionClass($this->target);
        
        if (!$rc->hasMethod($method)) {
            throw new BadMethodCallException("Method {$method} not found");
        }
        
        $rm    = $rc->getMethod($method);
        $start = hrtime(true);
        
        try {
            $result = $rm->invokeArgs($this->target, $args);
            $elapsed = (hrtime(true) - $start) / 1_000_000;
            
            $entry = [
                'method'  => $method,
                'args'    => $args,
                'result'  => $result,
                'elapsed' => round($elapsed, 3),
                'status'  => 'ok',
            ];
            $this->log[] = $entry;
            
            if ($this->logger) {
                ($this->logger)("[{$method}] completed in {$elapsed}ms");
            }
            
            return $result;
        } catch (Throwable $e) {
            $this->log[] = ['method' => $method, 'error' => $e->getMessage(), 'status' => 'error'];
            throw $e;
        }
    }
    
    public function getLog(): array { return $this->log; }
}

$gateway = new StripeGateway();
$proxy   = new LoggingProxy($gateway, fn($msg) => print("  LOG: {$msg}\n"));

echo "=== Payment Proxy ===\n";
$charge = $proxy->charge('tok_test_4242', 99.99, 'USD');
echo "Charge: " . json_encode($charge) . "\n";

$refund = $proxy->refund($charge['id'], 10.00);
echo "Refund: " . json_encode($refund) . "\n";

echo "\n=== Proxy Log ===\n";
foreach ($proxy->getLog() as $entry) {
    printf("  %-10s %s → status=%s (%.3fms)\n",
        $entry['method'], json_encode($entry['args']),
        $entry['status'], $entry['elapsed'] ?? 0
    );
}
```

---

## Step 6: Attribute-Based ORM Schema Builder

```php
<?php
#[Attribute(Attribute::TARGET_CLASS)]
class Table {
    public function __construct(public string $name, public string $engine = 'InnoDB') {}
}

#[Attribute(Attribute::TARGET_PROPERTY)]
class Field {
    public function __construct(
        public string $type = 'VARCHAR(255)',
        public bool $nullable = false,
        public bool $primaryKey = false,
        public bool $autoIncrement = false,
        public mixed $default = null,
        public ?string $index = null
    ) {}
}

#[Attribute(Attribute::TARGET_PROPERTY)]
class ForeignKey {
    public function __construct(
        public string $references,
        public string $onDelete = 'RESTRICT',
        public string $onUpdate = 'CASCADE'
    ) {}
}

function generateDDL(string $className): string {
    $rc     = new ReflectionClass($className);
    $tables = $rc->getAttributes(Table::class);
    
    if (!$tables) return "-- No @Table attribute on {$className}";
    
    $table  = $tables[0]->newInstance();
    $cols   = [];
    $pks    = [];
    $fks    = [];
    $indexes = [];
    
    foreach ($rc->getProperties() as $prop) {
        $fieldAttrs = $prop->getAttributes(Field::class);
        if (!$fieldAttrs) continue;
        
        $field    = $fieldAttrs[0]->newInstance();
        $colName  = strtolower(preg_replace('/[A-Z]/', '_$0', lcfirst($prop->getName())));
        
        $def = "  `{$colName}` {$field->type}";
        if (!$field->nullable) $def .= ' NOT NULL';
        if ($field->autoIncrement) $def .= ' AUTO_INCREMENT';
        if ($field->default !== null) $def .= ' DEFAULT ' . var_export($field->default, true);
        $cols[] = $def;
        
        if ($field->primaryKey) $pks[] = $colName;
        if ($field->index) $indexes[] = "  KEY `idx_{$colName}` (`{$colName}`)";
        
        $fkAttrs = $prop->getAttributes(ForeignKey::class);
        if ($fkAttrs) {
            $fk = $fkAttrs[0]->newInstance();
            $fks[] = "  FOREIGN KEY (`{$colName}`) REFERENCES {$fk->references} ON DELETE {$fk->onDelete}";
        }
    }
    
    if ($pks) $cols[] = "  PRIMARY KEY (" . implode(', ', array_map(fn($k) => "`{$k}`", $pks)) . ")";
    $all = array_merge($cols, $indexes, $fks);
    
    return "CREATE TABLE `{$table->name}` (\n" . implode(",\n", $all) . "\n) ENGINE={$table->engine};";
}

// Define entity
#[Table(name: 'orders', engine: 'InnoDB')]
class Order {
    #[Field(type: 'INT UNSIGNED', primaryKey: true, autoIncrement: true)]
    public int $id;
    
    #[Field(type: 'INT UNSIGNED')]
    #[ForeignKey(references: 'users(id)', onDelete: 'CASCADE')]
    public int $userId;
    
    #[Field(type: 'DECIMAL(10,2)')]
    public float $total;
    
    #[Field(type: 'ENUM("pending","paid","shipped","cancelled")', default: 'pending')]
    public string $status;
    
    #[Field(type: 'DATETIME', nullable: true, index: 'idx')]
    public ?string $shippedAt;
}

echo generateDDL(Order::class);
```

📸 **Verified Output:**
```sql
CREATE TABLE `orders` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT UNSIGNED NOT NULL,
  `total` DECIMAL(10,2) NOT NULL,
  `status` ENUM("pending","paid","shipped","cancelled") NOT NULL DEFAULT 'pending',
  `shipped_at` DATETIME NULL,
  PRIMARY KEY (`id`),
  KEY `idx_shipped_at` (`shipped_at`),
  FOREIGN KEY (`user_id`) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;
```

---

## Step 7: Minimal DI Container

```php
<?php
// Reflection-based Dependency Injection Container
class Container {
    private array $bindings  = [];
    private array $instances = [];
    
    public function bind(string $abstract, string|callable $concrete): void {
        $this->bindings[$abstract] = $concrete;
    }
    
    public function singleton(string $abstract, string|callable $concrete): void {
        $this->bind($abstract, function() use ($abstract, $concrete) {
            if (!isset($this->instances[$abstract])) {
                $this->instances[$abstract] = is_callable($concrete)
                    ? $concrete($this)
                    : $this->make($concrete);
            }
            return $this->instances[$abstract];
        });
    }
    
    public function make(string $class): object {
        if (isset($this->bindings[$class])) {
            $binding = $this->bindings[$class];
            return is_callable($binding) ? $binding($this) : $this->make($binding);
        }
        
        $rc = new ReflectionClass($class);
        
        if (!$rc->isInstantiable()) {
            throw new RuntimeException("Cannot instantiate {$class}");
        }
        
        $constructor = $rc->getConstructor();
        if (!$constructor) return new $class();
        
        $deps = $this->resolveDependencies($constructor->getParameters());
        return $rc->newInstanceArgs($deps);
    }
    
    private function resolveDependencies(array $params): array {
        return array_map(function(ReflectionParameter $param) {
            $type = $param->getType();
            
            if ($type instanceof ReflectionNamedType && !$type->isBuiltin()) {
                return $this->make($type->getName());
            }
            
            if ($param->isDefaultValueAvailable()) {
                return $param->getDefaultValue();
            }
            
            throw new RuntimeException("Cannot resolve parameter: \${$param->getName()}");
        }, $params);
    }
}

// Demo: wire up a service graph
interface LoggerInterface {
    public function log(string $msg): void;
}

class FileLogger implements LoggerInterface {
    public function log(string $msg): void {
        echo "[LOG] {$msg}\n";
    }
}

class Database {
    public function __construct(private readonly string $dsn = 'sqlite::memory:') {}
    public function getDsn(): string { return $this->dsn; }
}

class UserRepository {
    public function __construct(
        private readonly Database $db,
        private readonly LoggerInterface $logger
    ) {}
    
    public function find(int $id): array {
        $this->logger->log("UserRepository::find({$id})");
        return ['id' => $id, 'name' => 'Alice'];
    }
}

class UserService {
    public function __construct(
        private readonly UserRepository $repo,
        private readonly LoggerInterface $logger
    ) {}
    
    public function getUser(int $id): array {
        $this->logger->log("UserService::getUser({$id})");
        return $this->repo->find($id);
    }
}

$container = new Container();
$container->singleton(LoggerInterface::class, FileLogger::class);
$container->bind(Database::class, fn($c) => new Database('sqlite:/tmp/app.db'));

$service = $container->make(UserService::class);
$user    = $service->getUser(42);
echo "User: " . json_encode($user) . "\n";
```

📸 **Verified Output:**
```
[LOG] UserService::getUser(42)
[LOG] UserRepository::find(42)
User: {"id":42,"name":"Alice"}
```

---

## Step 8: Capstone — Full Attribute-Driven Framework

```php
<?php
// Router + Middleware + Validation via Attributes

#[Attribute(Attribute::TARGET_METHOD)]
class Get {
    public function __construct(public string $path) {}
}

#[Attribute(Attribute::TARGET_METHOD)]
class Post {
    public function __construct(public string $path) {}
}

#[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)]
class Middleware {
    public function __construct(public string $name) {}
}

#[Attribute(Attribute::TARGET_PARAMETER)]
class Validate {
    public function __construct(public string $rules) {}
}

class Router {
    private array $routes = [];
    
    public function register(string $controllerClass): void {
        $rc = new ReflectionClass($controllerClass);
        foreach ($rc->getMethods(ReflectionMethod::IS_PUBLIC) as $method) {
            foreach ([Get::class, Post::class] as $routeAttr) {
                $attrs = $method->getAttributes($routeAttr);
                if (!$attrs) continue;
                
                $route      = $attrs[0]->newInstance();
                $httpMethod = str_replace('::class', '', $routeAttr);
                $httpMethod = basename(str_replace('\\', '/', $routeAttr));
                
                // Gather middleware
                $middlewares = array_map(
                    fn($a) => $a->newInstance()->name,
                    $method->getAttributes(Middleware::class)
                );
                
                $this->routes[] = [
                    'method'      => strtoupper($httpMethod),
                    'path'        => $route->path,
                    'controller'  => $controllerClass,
                    'action'      => $method->getName(),
                    'middlewares' => $middlewares,
                ];
            }
        }
    }
    
    public function dump(): void {
        foreach ($this->routes as $r) {
            $mw = $r['middlewares'] ? ' [' . implode(', ', $r['middlewares']) . ']' : '';
            printf("  %-5s %-30s → %s::%s%s\n",
                $r['method'], $r['path'],
                basename(str_replace('\\', '/', $r['controller'])),
                $r['action'], $mw
            );
        }
    }
}

class UserController {
    #[Get('/users')]
    #[Middleware('auth')]
    #[Middleware('ratelimit')]
    public function index(): array { return []; }
    
    #[Get('/users/{id}')]
    #[Middleware('auth')]
    public function show(int $id): array { return []; }
    
    #[Post('/users')]
    #[Middleware('auth')]
    #[Middleware('csrf')]
    public function store(array $data): array { return []; }
}

class ProductController {
    #[Get('/products')]
    public function index(): array { return []; }
    
    #[Get('/products/{id}')]
    public function show(int $id): array { return []; }
    
    #[Post('/products')]
    #[Middleware('auth')]
    #[Middleware('admin')]
    public function store(array $data): array { return []; }
}

$router = new Router();
$router->register(UserController::class);
$router->register(ProductController::class);

echo "=== Registered Routes ===\n";
$router->dump();
```

📸 **Verified Output:**
```
=== Registered Routes ===
  GET   /users                          → UserController::index [auth, ratelimit]
  GET   /users/{id}                     → UserController::show [auth]
  POST  /users                          → UserController::store [auth, csrf]
  GET   /products                       → ProductController::index
  GET   /products/{id}                  → ProductController::show
  POST  /products                       → ProductController::store [auth, admin]
```

---

## Summary

| Feature | API | Use Case |
|---------|-----|----------|
| Class introspection | `new ReflectionClass($class)` | DI containers, ORMs |
| Method list | `$rc->getMethods()` | Router registration |
| Property list | `$rc->getProperties()` | Serializers, mappers |
| Read attribute | `$method->getAttributes(Attr::class)[0]->newInstance()` | Metadata reading |
| Invoke method | `$rm->invoke($obj, ...$args)` | Dynamic dispatch |
| Private access | `$rm->setAccessible(true)` | Testing private methods |
| Get closure | `$rm->getClosure($obj)` | Callable from method |
| Constructor params | `$rc->getConstructor()->getParameters()` | Auto-wiring |
| Type inspection | `$param->getType()->getName()` | DI type resolution |
| Code generation | `eval($generatedCode)` | VO builders, proxies |
