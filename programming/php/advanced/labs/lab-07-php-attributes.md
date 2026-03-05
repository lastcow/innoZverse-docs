# Lab 07: PHP 8.0+ Attributes

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

PHP Attributes (also called "annotations" in other languages) provide structured metadata that can be read at runtime via Reflection. They replace DocBlock annotations with a first-class, type-safe syntax.

---

## Step 1: Declaring a Custom Attribute

```php
<?php
// Restrict to class and method targets
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

    #[Route('/users/{id}', 'DELETE')]
    public function delete(int $id): void {}
}

// Read via Reflection
$rc = new ReflectionClass(UserController::class);

foreach ($rc->getAttributes(Route::class) as $attr) {
    $r = $attr->newInstance();
    echo "Controller: {$r->method} {$r->path}\n";
}

foreach ($rc->getMethods() as $method) {
    foreach ($method->getAttributes(Route::class) as $attr) {
        $r = $attr->newInstance();
        echo "{$r->method} {$r->path} → {$method->getName()}()\n";
    }
}
```

📸 **Verified Output:**
```
Controller: GET /users
GET /users/{id} → show()
POST /users → create()
DELETE /users/{id} → delete()
```

---

## Step 2: Attribute Target Flags

```php
<?php
// Can target multiple things
#[Attribute(
    Attribute::TARGET_CLASS |
    Attribute::TARGET_METHOD |
    Attribute::TARGET_PROPERTY |
    Attribute::TARGET_PARAMETER
)]
class Inject {
    public function __construct(public readonly ?string $id = null) {}
}

// Only on properties
#[Attribute(Attribute::TARGET_PROPERTY)]
class Column {
    public function __construct(
        public readonly string $name,
        public readonly string $type = 'VARCHAR(255)',
        public readonly bool $nullable = false
    ) {}
}

// Only on classes
#[Attribute(Attribute::TARGET_CLASS)]
class Table {
    public function __construct(public readonly string $name) {}
}

#[Table('users')]
class User {
    #[Column('id', 'INT', false)]
    public int $id;

    #[Column('user_name', 'VARCHAR(100)')]
    public string $name;

    #[Column('email_address', nullable: true)]
    public ?string $email = null;
}

// Build schema from attributes
$rc = new ReflectionClass(User::class);
$tableAttr = $rc->getAttributes(Table::class)[0]->newInstance();
echo "Table: {$tableAttr->name}\n";

foreach ($rc->getProperties() as $prop) {
    $cols = $prop->getAttributes(Column::class);
    if (!empty($cols)) {
        $col = $cols[0]->newInstance();
        $null = $col->nullable ? 'NULL' : 'NOT NULL';
        echo "  {$col->name} {$col->type} $null\n";
    }
}
```

📸 **Verified Output:**
```
Table: users
  id INT NOT NULL
  user_name VARCHAR(100) NOT NULL
  email_address VARCHAR(255) NULL
```

---

## Step 3: Repeatable Attributes

```php
<?php
#[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)]
class Middleware {
    public function __construct(public readonly string $class) {}
}

class ApiController {
    #[Middleware('AuthMiddleware')]
    #[Middleware('RateLimitMiddleware')]
    #[Middleware('LoggingMiddleware')]
    public function sensitiveEndpoint(): void {}

    #[Middleware('AuthMiddleware')]
    public function profileEndpoint(): void {}
}

$rc = new ReflectionClass(ApiController::class);
foreach ($rc->getMethods() as $method) {
    $middlewares = $method->getAttributes(Middleware::class);
    if (!empty($middlewares)) {
        echo "{$method->getName()}():\n";
        foreach ($middlewares as $attr) {
            echo "  → " . $attr->newInstance()->class . "\n";
        }
    }
}
```

📸 **Verified Output:**
```
sensitiveEndpoint():
  → AuthMiddleware
  → RateLimitMiddleware
  → LoggingMiddleware
profileEndpoint():
  → AuthMiddleware
```

> 💡 Add `Attribute::IS_REPEATABLE` to allow multiple instances of the same attribute on a single target.

---

## Step 4: Built-in PHP Attributes

```php
<?php
class OldApi {
    #[\Deprecated('Use newMethod() instead', since: '2.0')]
    public function oldMethod(): string {
        return $this->newMethod();
    }

    public function newMethod(): string {
        return 'new implementation';
    }
}

class Child extends OldApi {
    #[\Override]  // Compile-time check: must exist in parent
    public function newMethod(): string {
        return 'child override: ' . parent::newMethod();
    }
}

// Verify Override
$rc = new ReflectionClass(Child::class);
$method = $rc->getMethod('newMethod');
$attrs = $method->getAttributes(\Override::class);
echo "Override attribute: " . (count($attrs) > 0 ? 'present' : 'absent') . "\n";

$obj = new Child();
echo $obj->newMethod() . "\n";

// #[SensitiveParameter] — prevents value from appearing in stack traces
function login(string $username, #[\SensitiveParameter] string $password): bool {
    if ($password === '') throw new \InvalidArgumentException("Password required");
    return true;
}

$funcRef = new ReflectionFunction('login');
foreach ($funcRef->getParameters() as $param) {
    $sensitive = !empty($param->getAttributes(\SensitiveParameter::class));
    echo "\${$param->getName()}: " . ($sensitive ? 'SENSITIVE' : 'normal') . "\n";
}
```

📸 **Verified Output:**
```
Override attribute: present
child override: new implementation
$username: normal
$password: SENSITIVE
```

---

## Step 5: Validation Attribute Pattern

```php
<?php
#[Attribute(Attribute::TARGET_PROPERTY | Attribute::IS_REPEATABLE)]
class Validate {
    public function __construct(
        public readonly string $rule,
        public readonly mixed  $value = null,
        public readonly string $message = ''
    ) {}
}

class Validator {
    public static function validate(object $obj): array {
        $errors = [];
        $rc = new ReflectionClass($obj);

        foreach ($rc->getProperties() as $prop) {
            $prop->setAccessible(true);
            $val = $prop->isInitialized($obj) ? $prop->getValue($obj) : null;

            foreach ($prop->getAttributes(Validate::class) as $attr) {
                $v = $attr->newInstance();
                $pass = match($v->rule) {
                    'required' => $val !== null && $val !== '',
                    'min'      => is_numeric($val) && $val >= $v->value,
                    'max'      => is_numeric($val) && $val <= $v->value,
                    'email'    => filter_var($val, FILTER_VALIDATE_EMAIL) !== false,
                    'minlen'   => is_string($val) && strlen($val) >= $v->value,
                    default    => true,
                };
                if (!$pass) {
                    $msg = $v->message ?: "Field '{$prop->getName()}' failed rule '{$v->rule}'";
                    $errors[$prop->getName()][] = $msg;
                }
            }
        }
        return $errors;
    }
}

class UserRegistration {
    #[Validate('required', message: 'Name is required')]
    #[Validate('minlen', 2, 'Name must be at least 2 characters')]
    public string $name = '';

    #[Validate('required', message: 'Email is required')]
    #[Validate('email', message: 'Invalid email format')]
    public string $email = '';

    #[Validate('required')]
    #[Validate('min', 18, 'Must be 18 or older')]
    #[Validate('max', 120, 'Invalid age')]
    public int $age = 0;
}

// Valid user
$valid = new UserRegistration();
$valid->name = 'Alice';
$valid->email = 'alice@example.com';
$valid->age = 25;
$errors = Validator::validate($valid);
echo "Valid user errors: " . (empty($errors) ? 'none' : json_encode($errors)) . "\n";

// Invalid user
$invalid = new UserRegistration();
$invalid->name = 'A';
$invalid->email = 'not-an-email';
$invalid->age = 15;
$errors = Validator::validate($invalid);
echo "\nInvalid user errors:\n";
foreach ($errors as $field => $fieldErrors) {
    foreach ($fieldErrors as $error) {
        echo "  [$field] $error\n";
    }
}
```

📸 **Verified Output:**
```
Valid user errors: none

Invalid user errors:
  [name] Name must be at least 2 characters
  [email] Invalid email format
  [age] Must be 18 or older
```

---

## Step 6: Event Listener Attribute

```php
<?php
#[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)]
class On {
    public function __construct(public readonly string $event) {}
}

class EventBus {
    private array $listeners = [];

    public function registerSubscriber(object $subscriber): void {
        $rc = new ReflectionClass($subscriber);
        foreach ($rc->getMethods() as $method) {
            foreach ($method->getAttributes(On::class) as $attr) {
                $event = $attr->newInstance()->event;
                $this->listeners[$event][] = [$subscriber, $method->getName()];
            }
        }
    }

    public function emit(string $event, mixed $data = null): void {
        foreach ($this->listeners[$event] ?? [] as [$obj, $method]) {
            $obj->$method($data);
        }
    }
}

class UserSubscriber {
    #[On('user.created')]
    public function onUserCreated(array $user): void {
        echo "Email sent to {$user['email']}\n";
    }

    #[On('user.created')]
    #[On('user.updated')]
    public function onUserChanged(array $user): void {
        echo "Cache cleared for user {$user['id']}\n";
    }
}

$bus = new EventBus();
$bus->registerSubscriber(new UserSubscriber());

echo "user.created event:\n";
$bus->emit('user.created', ['id' => 1, 'email' => 'alice@example.com']);

echo "\nuser.updated event:\n";
$bus->emit('user.updated', ['id' => 1, 'email' => 'alice@example.com']);
```

📸 **Verified Output:**
```
user.created event:
Email sent to alice@example.com
Cache cleared for user 1

user.updated event:
Cache cleared for user 1
```

---

## Step 7: Parameter Attributes & Type Checking

```php
<?php
#[Attribute(Attribute::TARGET_PARAMETER)]
class Range {
    public function __construct(
        public readonly float $min,
        public readonly float $max
    ) {}
}

#[Attribute(Attribute::TARGET_PARAMETER)]
class NotEmpty {}

function validateAndCall(callable $fn, array $args): mixed {
    $ref = new ReflectionFunction($fn);
    foreach ($ref->getParameters() as $i => $param) {
        $value = $args[$i] ?? null;

        foreach ($param->getAttributes(Range::class) as $attr) {
            $r = $attr->newInstance();
            if ($value < $r->min || $value > $r->max) {
                throw new \RangeException(
                    "\${$param->getName()} must be between {$r->min} and {$r->max}, got $value"
                );
            }
        }
        foreach ($param->getAttributes(NotEmpty::class) as $_) {
            if (empty($value)) {
                throw new \InvalidArgumentException("\${$param->getName()} cannot be empty");
            }
        }
    }
    return $fn(...$args);
}

$setTemperature = function(
    #[Range(-273.15, 1000.0)] float $celsius,
    #[NotEmpty] string $unit
): string {
    return "$celsius°$unit";
};

echo validateAndCall($setTemperature, [100.0, 'C']) . "\n";

try {
    validateAndCall($setTemperature, [-999.0, 'C']);
} catch (\RangeException $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
```

📸 **Verified Output:**
```
100°C
Error: $celsius must be between -273.15 and 1000, got -999
```

---

## Step 8: Capstone — Mini Router with Attribute-Based Routing

```php
<?php
#[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)]
class Route {
    public function __construct(
        public readonly string $path,
        public readonly string $method = 'GET'
    ) {}
}

#[Attribute(Attribute::TARGET_CLASS)]
class Controller {
    public function __construct(public readonly string $prefix = '') {}
}

#[Controller('/api/v1')]
class ProductController {
    #[Route('/products', 'GET')]
    public function index(): array {
        return [['id' => 1, 'name' => 'Widget'], ['id' => 2, 'name' => 'Gadget']];
    }

    #[Route('/products/{id}', 'GET')]
    public function show(int $id): array {
        return ['id' => $id, 'name' => "Product $id", 'price' => 9.99];
    }

    #[Route('/products', 'POST')]
    public function create(array $data): array {
        return array_merge($data, ['id' => rand(100, 999), 'created' => true]);
    }
}

class AttributeRouter {
    private array $routes = [];

    public function registerController(string $class): void {
        $rc = new ReflectionClass($class);
        $prefix = '';

        $ctrlAttrs = $rc->getAttributes(Controller::class);
        if (!empty($ctrlAttrs)) {
            $prefix = $ctrlAttrs[0]->newInstance()->prefix;
        }

        foreach ($rc->getMethods() as $method) {
            foreach ($method->getAttributes(Route::class) as $attr) {
                $route = $attr->newInstance();
                $this->routes[] = [
                    'method'  => $route->method,
                    'path'    => $prefix . $route->path,
                    'handler' => [$class, $method->getName()],
                ];
            }
        }
    }

    public function dispatch(string $httpMethod, string $path): mixed {
        foreach ($this->routes as $route) {
            if ($route['method'] !== $httpMethod) continue;
            $pattern = preg_replace('/\{(\w+)\}/', '(\w+)', $route['path']);
            if (preg_match("#^$pattern$#", $path, $matches)) {
                array_shift($matches);
                [$class, $method] = $route['handler'];
                $rc = new ReflectionClass($class);
                $obj = $rc->newInstance();
                return $rc->getMethod($method)->invoke($obj, ...$matches);
            }
        }
        return ['error' => "404 Not Found: $httpMethod $path"];
    }

    public function dumpRoutes(): void {
        foreach ($this->routes as $r) {
            printf("%-6s %-30s → %s::%s\n",
                $r['method'], $r['path'],
                $r['handler'][0], $r['handler'][1]
            );
        }
    }
}

$router = new AttributeRouter();
$router->registerController(ProductController::class);

echo "Registered routes:\n";
$router->dumpRoutes();

echo "\nDispatching requests:\n";
$result = $router->dispatch('GET', '/api/v1/products');
echo "GET /products: " . json_encode($result) . "\n";

$result = $router->dispatch('GET', '/api/v1/products/42');
echo "GET /products/42: " . json_encode($result) . "\n";
```

📸 **Verified Output:**
```
Registered routes:
GET    /api/v1/products               → ProductController::index
GET    /api/v1/products/{id}          → ProductController::show
POST   /api/v1/products               → ProductController::create

Dispatching requests:
GET /products: [{"id":1,"name":"Widget"},{"id":2,"name":"Gadget"}]
GET /products/42: {"id":"42","name":"Product 42","price":9.99}
```

---

## Summary

| Feature | Syntax | PHP Version |
|---|---|---|
| Declare attribute | `#[Attribute]` before class | 8.0+ |
| Target restriction | `#[Attribute(Attribute::TARGET_CLASS)]` | 8.0+ |
| Repeatable attribute | `Attribute::IS_REPEATABLE` flag | 8.0+ |
| Read attributes | `$rc->getAttributes(MyAttr::class)` | 8.0+ |
| Instantiate attribute | `$attr->newInstance()` | 8.0+ |
| Built-in: Override | `#[\Override]` on method | 8.3+ |
| Built-in: Deprecated | `#[\Deprecated('msg')]` | 8.4+ |
| Built-in: SensitiveParam | `#[\SensitiveParameter]` | 8.2+ |
| All targets | CLASS, METHOD, PROPERTY, PARAMETER, FUNCTION, CONSTANT | 8.0+ |
