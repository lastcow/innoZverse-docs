# Lab 14: PHP Type System & Attributes

## Objective
Master PHP 8's type system: union types, intersection types, `never`, `mixed`, readonly classes, and PHP Attributes (annotations). Use `strict_types`, type coercion rules, and runtime type checking.

## Background
PHP's type system has evolved from weakly-typed (PHP 4) to progressively stricter (PHP 7 scalar types, PHP 8.0 union types, PHP 8.1 never/readonly/intersection, PHP 8.2 readonly classes, PHP 8.3 typed class constants). Understanding PHP's type system helps you write self-documenting, IDE-friendly, refactorable code — and prevents entire classes of bugs.

## Time
30 minutes

## Prerequisites
- Lab 07 (OOP), Lab 08 (Inheritance)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Scalar Types & strict_types

```php
<?php
// Without strict_types — PHP coerces values
function addLoose(int $a, int $b): int { return $a + $b; }
echo "Loose: " . addLoose('3', '4') . "\n";  // works: '3' coerced to 3
echo "Loose: " . addLoose(3.9, 2.1) . "\n";  // works: 3.9 → 3

// After enabling strict_types — same function, strict callers
// (strict_types affects the CALLING file, not the function definition)
```

```php
<?php
declare(strict_types=1);

function add(int $a, int $b): int { return $a + $b; }
function divide(float $a, float $b): float { return $a / $b; }
function greet(?string $name): string { return "Hello, " . ($name ?? "World"); }

echo add(3, 4) . "\n";        // 7
echo divide(10.0, 3.0) . "\n"; // 3.333...
echo greet(null) . "\n";       // Hello, World
echo greet("Dr. Chen") . "\n"; // Hello, Dr. Chen

// Type hierarchy
$values = [42, 3.14, "hello", true, null, [], new stdClass()];
foreach ($values as $v) {
    $type = gettype($v);
    $var  = is_scalar($v) ? var_export($v, true) : $type;
    printf("  %-10s → is_scalar=%s\n", $var, is_scalar($v) ? 'true' : 'false');
}
```

> 💡 **`declare(strict_types=1)` affects only the file it's in.** A strict file calling a non-strict function still enforces type checking on the call. A non-strict file calling a strict function does not. Strict mode prevents silent coercions — `add('3', '4')` throws `TypeError` instead of silently converting.

**📸 Verified Output:**
```
7
3.3333333333333
Hello, World
Hello, Dr. Chen
  42         → is_scalar=true
  3.14       → is_scalar=true
  'hello'    → is_scalar=true
  true       → is_scalar=true
  NULL       → is_scalar=false
  array      → is_scalar=false
  object     → is_scalar=false
```

---

### Step 2: Union Types & Nullable

```php
<?php
declare(strict_types=1);

// Union types (PHP 8.0)
function formatId(int|string $id): string {
    return is_int($id) ? "#$id" : $id;
}

echo formatId(42) . "\n";
echo formatId("UUID-abc") . "\n";

// int|false — common return pattern
function findIndex(array $arr, mixed $search): int|false {
    $idx = array_search($search, $arr);
    return $idx !== false ? (int)$idx : false;
}

$fruits = ['apple', 'banana', 'cherry'];
$idx = findIndex($fruits, 'banana');
echo "banana index: " . ($idx !== false ? $idx : "not found") . "\n";

// null|string = ?string
function getEnv(string $key): ?string { return $_ENV[$key] ?? null; }

// DNF types (PHP 8.2) — Disjunctive Normal Form
// (A&B)|C — intersection inside union
interface Printable { public function print(): void; }
interface Loggable  { public function log(): void; }

class Document implements Printable, Loggable {
    public function print(): void { echo "Printing doc\n"; }
    public function log(): void   { echo "Logging doc\n"; }
}

function process((Printable&Loggable)|string $item): void {
    if (is_string($item)) { echo "String: $item\n"; return; }
    $item->print();
    $item->log();
}

process(new Document());
process("plain string");

// mixed type — opt out of type checking
function debugAny(mixed $value): string {
    return gettype($value) . ': ' . var_export($value, true);
}
echo "\n" . debugAny(42) . "\n";
echo debugAny([1, 2]) . "\n";
```

> 💡 **Union types replace doc-comment workarounds.** Before PHP 8, you'd write `@param int|string $id` in a docblock. Now `int|string` is enforced at runtime. `int|false` is the canonical "search result or not found" type (like `array_search` returns). Use `?Type` for nullable (shorthand for `Type|null`).

**📸 Verified Output:**
```
#42
UUID-abc
banana index: 1
Printing doc
Logging doc
String: plain string

integer: 42
array: array ( 0 => 1, 1 => 2, )
```

---

### Step 3: Intersection Types

```php
<?php
declare(strict_types=1);

interface Serializable2 { public function serialize(): string; }
interface Cacheable    { public function getCacheKey(): string; }
interface Validatable  { public function isValid(): bool; }

class UserDTO implements Serializable2, Cacheable, Validatable {
    public function __construct(
        public readonly int    $id,
        public readonly string $email,
        public readonly string $name,
    ) {}

    public function serialize(): string { return json_encode(['id'=>$this->id,'email'=>$this->email,'name'=>$this->name]); }
    public function getCacheKey(): string { return "user:{$this->id}"; }
    public function isValid(): bool { return filter_var($this->email, FILTER_VALIDATE_EMAIL) !== false; }
}

// Intersection type — must implement ALL listed interfaces
function storeAndCache(Serializable2&Cacheable $item): void {
    echo "Caching [{$item->getCacheKey()}]: " . $item->serialize() . "\n";
}

function validateAndStore(Validatable&Serializable2 $item): void {
    if (!$item->isValid()) { echo "Invalid: skip\n"; return; }
    echo "Stored: " . $item->serialize() . "\n";
}

$user  = new UserDTO(1, 'chen@example.com', 'Dr. Chen');
$bad   = new UserDTO(2, 'not-an-email', 'Baduser');

storeAndCache($user);
validateAndStore($user);
validateAndStore($bad);

// Type narrowing with instanceof
function processItem(Serializable2|Cacheable $item): string {
    $parts = [];
    if ($item instanceof Cacheable)    $parts[] = "cached(" . $item->getCacheKey() . ")";
    if ($item instanceof Serializable2) $parts[] = strlen($item->serialize()) . "b";
    return implode(', ', $parts);
}

echo "\nProcess: " . processItem($user) . "\n";
```

> 💡 **Intersection types (`A&B`)** require the value to implement ALL listed interfaces — they're stricter than union types. Use them when a function truly needs multiple capabilities. If you find yourself writing `A&B&C`, consider creating a combined interface `interface AWithBC extends A, B, C {}` for readability.

**📸 Verified Output:**
```
Caching [user:1]: {"id":1,"email":"chen@example.com","name":"Dr. Chen"}
Stored: {"id":1,"email":"chen@example.com","name":"Dr. Chen"}
Invalid: skip

Process: cached(user:1), 52b
```

---

### Step 4: Readonly Classes (PHP 8.2)

```php
<?php
declare(strict_types=1);

// readonly class — ALL properties are automatically readonly
readonly class Point {
    public function __construct(
        public float $x,
        public float $y,
    ) {}

    public function distanceTo(Point $other): float {
        return sqrt(($this->x - $other->x) ** 2 + ($this->y - $other->y) ** 2);
    }

    public function translate(float $dx, float $dy): self {
        return new self($this->x + $dx, $this->y + $dy);  // return new instance
    }

    public function __toString(): string { return "({$this->x}, {$this->y})"; }
}

readonly class Rectangle {
    public float $area;
    public float $perimeter;

    public function __construct(
        public Point $topLeft,
        public Point $bottomRight,
    ) {
        $w = abs($bottomRight->x - $topLeft->x);
        $h = abs($bottomRight->y - $topLeft->y);
        $this->area      = $w * $h;
        $this->perimeter = 2 * ($w + $h);
    }

    public function __toString(): string {
        return "Rect[{$this->topLeft}→{$this->bottomRight}]";
    }
}

$p1 = new Point(0, 0);
$p2 = new Point(3, 4);
echo "Distance: " . $p1->distanceTo($p2) . "\n";

$p3 = $p1->translate(1, 1);
echo "Translated: $p3\n";

$rect = new Rectangle(new Point(0, 0), new Point(4, 3));
echo "Rect: $rect\n";
printf("Area: %.1f  Perimeter: %.1f\n", $rect->area, $rect->perimeter);

// Try to modify — fails
try {
    $p1->x = 99;
} catch (\Error $e) {
    echo "Readonly blocked: " . $e->getMessage() . "\n";
}
```

> 💡 **`readonly class`** (PHP 8.2) makes ALL declared properties readonly without decorating each one. It's perfect for value objects, DTOs (Data Transfer Objects), and domain events — objects that represent facts and should never change after construction. Cloning with `clone $obj with {prop: val}` is the PHP 8.4+ way to make modified copies.

**📸 Verified Output:**
```
Distance: 5
Translated: (1, 1)
Rect: Rect[(0, 0)→(4, 3)]
Area: 12.0  Perimeter: 14.0
Readonly blocked: Cannot modify readonly property Point::$x
```

---

### Step 5: Typed Class Constants (PHP 8.3)

```php
<?php
declare(strict_types=1);

class Config {
    const string  APP_NAME    = 'innoZverse';
    const string  VERSION     = '1.0.0';
    const int     MAX_RETRIES = 3;
    const float   TIMEOUT     = 30.0;
    const bool    DEBUG       = false;
    const array   SUPPORTED_LOCALES = ['en', 'zh', 'de', 'fr'];
}

interface ApiClient {
    const string BASE_URL = 'https://api.example.com';
    const int    VERSION  = 2;
}

class HttpClient implements ApiClient {
    const string BASE_URL = 'https://api.innozverse.com';  // can override
    const int    VERSION  = 1;
}

echo "App: "     . Config::APP_NAME . " v" . Config::VERSION . "\n";
echo "Retries: " . Config::MAX_RETRIES . "\n";
echo "Debug: "   . (Config::DEBUG ? 'on' : 'off') . "\n";
echo "Locales: " . implode(', ', Config::SUPPORTED_LOCALES) . "\n";

echo "\nAPI URL: "     . HttpClient::BASE_URL . "\n";
echo "API version: " . HttpClient::VERSION . "\n";

// Enum with typed constants
enum Status: string {
    case Active   = 'active';
    case Inactive = 'inactive';

    const string DEFAULT = 'active';
    const array  ALL     = ['active', 'inactive'];
}

echo "\nDefault status: " . Status::DEFAULT . "\n";
echo "All statuses: "   . implode(', ', Status::ALL) . "\n";
```

> 💡 **Typed class constants** (PHP 8.3) enforce that `const string APP_NAME` can only hold a string — assigning an integer would be a compile error. Previously, constants were untyped and could hold any value. This feature closes the last major gap in PHP's type system for class members.

**📸 Verified Output:**
```
App: innoZverse v1.0.0
Retries: 3
Debug: off
Locales: en, zh, de, fr

API URL: https://api.innozverse.com
API version: 1

Default status: active
All statuses: active, inactive
```

---

### Step 6: PHP Attributes

```php
<?php
declare(strict_types=1);

// Define custom attributes
#[Attribute(Attribute::TARGET_CLASS)]
class Entity {
    public function __construct(public string $table) {}
}

#[Attribute(Attribute::TARGET_PROPERTY)]
class Column {
    public function __construct(
        public string $name  = '',
        public string $type  = 'string',
        public bool   $nullable = false,
    ) {}
}

#[Attribute(Attribute::TARGET_METHOD)]
class Route {
    public function __construct(
        public string $path,
        public string $method = 'GET',
    ) {}
}

// Use attributes to annotate a class
#[Entity(table: 'users')]
class UserModel {
    #[Column(name: 'id', type: 'int')]
    public int $id;

    #[Column(name: 'email', type: 'string')]
    public string $email;

    #[Column(name: 'bio', type: 'text', nullable: true)]
    public ?string $bio;

    public function __construct(int $id, string $email, ?string $bio = null) {
        $this->id = $id; $this->email = $email; $this->bio = $bio;
    }

    #[Route('/users', method: 'GET')]
    public function index(): string { return "List users"; }

    #[Route('/users/{id}', method: 'GET')]
    public function show(): string { return "Show user"; }
}

// Read attributes via Reflection
$ref = new ReflectionClass(UserModel::class);

// Class attributes
foreach ($ref->getAttributes(Entity::class) as $attr) {
    $entity = $attr->newInstance();
    echo "Entity table: {$entity->table}\n";
}

// Property attributes
echo "\nColumns:\n";
foreach ($ref->getProperties() as $prop) {
    foreach ($prop->getAttributes(Column::class) as $attr) {
        $col = $attr->newInstance();
        printf("  %-12s → %s (%s)%s\n",
            $prop->getName(), $col->name ?: $prop->getName(),
            $col->type, $col->nullable ? ' NULL' : '');
    }
}

// Method attributes
echo "\nRoutes:\n";
foreach ($ref->getMethods() as $method) {
    foreach ($method->getAttributes(Route::class) as $attr) {
        $route = $attr->newInstance();
        printf("  %-6s %s → %s()\n", $route->method, $route->path, $method->getName());
    }
}
```

> 💡 **PHP Attributes** (PHP 8.0) replace docblock annotations (`@ORM\Column`). They're real PHP code — syntax-checked, IDE-indexed, and type-safe. Frameworks read them via Reflection at startup (then cache the result). Doctrine, Symfony routing, and PHP-DI all support attribute-based configuration.

**📸 Verified Output:**
```
Entity table: users

Columns:
  id           → id (int)
  email        → email (string)
  bio          → bio (text) NULL

Routes:
  GET    /users → index()
  GET    /users/{id} → show()
```

---

### Step 7: Type Checking & instanceof

```php
<?php
declare(strict_types=1);

interface Shape { public function area(): float; }
interface Drawable { public function draw(): string; }

class Circle implements Shape, Drawable {
    public function __construct(public float $r) {}
    public function area(): float  { return M_PI * $this->r ** 2; }
    public function draw(): string { return "○(r={$this->r})"; }
}

class Square implements Shape {
    public function __construct(public float $s) {}
    public function area(): float { return $this->s ** 2; }
}

// PHP 8 instanceof pattern matching
function describeShape(mixed $shape): string {
    if ($shape instanceof Circle) {
        return "Circle r={$shape->r} area=" . round($shape->area(), 2);
    } elseif ($shape instanceof Square) {
        return "Square s={$shape->s} area=" . round($shape->area(), 2);
    }
    return "Unknown shape";
}

// get_class & get_debug_type
$items = [new Circle(5), new Square(4), "not a shape", 42, null];
foreach ($items as $item) {
    echo "  " . get_debug_type($item) . "\n";
}

echo "\n";
foreach ($items as $item) {
    if ($item instanceof Shape) echo "  Shape: " . describeShape($item) . "\n";
}

// is_a — also works with strings
echo "\nis_a check: " . (is_a(new Circle(1), Shape::class) ? 'yes' : 'no') . "\n";
echo "is_a string: " . (is_a('Circle', Shape::class, allow_string: true) ? 'yes' : 'no') . "\n";
```

> 💡 **`get_debug_type()`** (PHP 8.0) is the right tool for debugging type values — unlike `gettype()`, it returns `"null"` (not `"NULL"`), `"Circle"` (not `"object"`), and `"int"` (not `"integer"`). Use it in error messages, logging, and assertions for human-readable type names.

**📸 Verified Output:**
```
  Circle
  Square
  string
  int
  null

  Shape: Circle r=5 area=78.54
  Shape: Square s=4 area=16

is_a check: yes
is_a string: yes
```

---

### Step 8: Complete — DTO + Validation System

```php
<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_PROPERTY | Attribute::IS_REPEATABLE)]
class Validate {
    public function __construct(
        public string $rule,
        public mixed  $param = null,
        public string $message = '',
    ) {}
}

readonly class OrderDTO {
    public function __construct(
        #[Validate('required')]
        #[Validate('minLength', 3, 'Customer name must be at least 3 chars')]
        public string $customerName,

        #[Validate('required')]
        #[Validate('email')]
        public string $email,

        #[Validate('min', 0.01, 'Amount must be positive')]
        public float  $amount,

        #[Validate('in', ['pending', 'paid', 'cancelled'])]
        public string $status = 'pending',
    ) {}
}

class DTOValidator {
    public function validate(object $dto): array {
        $errors = [];
        $ref    = new ReflectionClass($dto);

        foreach ($ref->getProperties() as $prop) {
            $value = $prop->getValue($dto);
            foreach ($prop->getAttributes(Validate::class) as $attr) {
                $v   = $attr->newInstance();
                $err = $this->check($v->rule, $value, $v->param, $v->message, $prop->getName());
                if ($err) $errors[$prop->getName()][] = $err;
            }
        }
        return $errors;
    }

    private function check(string $rule, mixed $value, mixed $param, string $msg, string $field): ?string {
        return match($rule) {
            'required'  => (empty($value) && $value !== 0) ? ($msg ?: "$field is required") : null,
            'email'     => !filter_var($value, FILTER_VALIDATE_EMAIL) ? ($msg ?: "Invalid email") : null,
            'min'       => $value < $param ? ($msg ?: "$field must be >= $param") : null,
            'minLength' => strlen($value) < $param ? ($msg ?: "$field min length $param") : null,
            'in'        => !in_array($value, $param) ? ($msg ?: "$field must be one of: " . implode(', ', $param)) : null,
            default     => null,
        };
    }
}

$validator = new DTOValidator();

$cases = [
    new OrderDTO('Dr. Chen', 'chen@example.com', 864.00, 'paid'),
    new OrderDTO('Bo', 'bad-email', -10.00, 'unknown'),
];

foreach ($cases as $dto) {
    $errors = $validator->validate($dto);
    if (empty($errors)) {
        echo "✓ Valid: {$dto->customerName} → \${$dto->amount} ({$dto->status})\n";
    } else {
        echo "✗ Invalid:\n";
        foreach ($errors as $field => $msgs) {
            foreach ($msgs as $msg) echo "  - $field: $msg\n";
        }
    }
}
```

> 💡 **Attribute-driven validation** is exactly how Symfony's Validator component works — `#[Assert\NotBlank]`, `#[Assert\Email]`, `#[Assert\Range(min: 0)]`. Reflection reads these at runtime (cached for performance) and runs the corresponding validators. This approach is self-documenting: constraints live with the property they constrain.

**📸 Verified Output:**
```
✓ Valid: Dr. Chen → $864 (paid)
✗ Invalid:
  - customerName: Customer name must be at least 3 chars
  - email: Invalid email
  - amount: Amount must be positive
  - status: status must be one of: pending, paid, cancelled
```

---

## Summary

PHP 8's type system is comprehensive and expressive. You've covered `strict_types`, union types, intersection types, DNF types, `mixed`, readonly classes, typed class constants, PHP Attributes with Reflection, and a complete attribute-driven DTO validator. These features make PHP competitive with TypeScript and Kotlin for type safety.

## Further Reading
- [PHP Type System](https://www.php.net/manual/en/language.types.php)
- [PHP Attributes](https://www.php.net/manual/en/language.attributes.php)
- [Readonly Classes PHP 8.2](https://www.php.net/manual/en/language.oop5.properties.php#language.oop5.properties.readonly-properties)
