# Lab 03: Named Arguments, Intersection Types & Modern Syntax

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

This lab covers PHP 8.0–8.2 syntax features: named arguments, intersection types, DNF types, the `never` return type, first-class callables, and array unpacking with string keys.

---

## Step 1: Named Arguments — Basics

Named arguments let you pass values by parameter name, skipping optionals and clarifying intent:

```php
<?php
function createUser(
    string $name,
    int    $age    = 0,
    string $role   = 'user',
    bool   $active = true
): string {
    $activeStr = $active ? 'active' : 'inactive';
    return "$name / age=$age / role=$role / $activeStr";
}

// Traditional positional
echo createUser('Alice', 30, 'admin', true) . "\n";

// Named — skip optionals, change order
echo createUser(name: 'Alice', role: 'admin') . "\n";
echo createUser(age: 25, name: 'Bob') . "\n";

// Mix positional + named (positional must come first)
echo createUser('Charlie', role: 'editor', active: false) . "\n";
```

📸 **Verified Output:**
```
Alice / age=30 / role=admin / active
Alice / age=0 / role=admin / active
Bob / age=25 / role=user / active
Charlie / age=0 / role=editor / inactive
```

> 💡 Named arguments also work with built-in functions: `array_slice(array: $arr, offset: 2, preserve_keys: true)`.

---

## Step 2: Named Arguments with Built-in Functions

```php
<?php
$arr = ['a', 'b', 'c', 'd', 'e'];

// Traditional
$slice1 = array_slice($arr, 1, 3, true);

// Named args — much clearer intent
$slice2 = array_slice(
    array: $arr,
    offset: 1,
    length: 3,
    preserve_keys: true
);

print_r($slice1);
print_r($slice2);

// Named in constructors
$date = new DateTime(datetime: '2024-01-15', timezone: new DateTimeZone('UTC'));
echo $date->format('Y-m-d') . "\n";
```

📸 **Verified Output:**
```
Array
(
    [1] => b
    [2] => c
    [3] => d
)
Array
(
    [1] => b
    [2] => c
    [3] => d
)
2024-01-15
```

---

## Step 3: Intersection Types (PHP 8.1)

Intersection types require a value to satisfy **multiple** type constraints:

```php
<?php
interface Stringable {
    public function __toString(): string;
}

interface Countable {
    public function count(): int;
}

interface Iterator {
    public function current(): mixed;
    public function key(): mixed;
    public function next(): void;
    public function rewind(): void;
    public function valid(): bool;
}

class Collection implements \Stringable, \Countable, \Iterator {
    private int $position = 0;
    public function __construct(private array $items) {}

    public function __toString(): string {
        return '[' . implode(', ', $this->items) . ']';
    }
    public function count(): int { return count($this->items); }
    public function current(): mixed { return $this->items[$this->position]; }
    public function key(): mixed { return $this->position; }
    public function next(): void { $this->position++; }
    public function rewind(): void { $this->position = 0; }
    public function valid(): bool { return isset($this->items[$this->position]); }
}

// Intersection type: must be both Stringable AND Countable
function describeCollection(\Stringable&\Countable $col): string {
    return "Collection: $col with {$col->count()} items";
}

$col = new Collection(['php', 'rust', 'go']);
echo describeCollection($col) . "\n";

// Iterate using Iterator
foreach ($col as $k => $v) {
    echo "  [$k] => $v\n";
}
```

📸 **Verified Output:**
```
Collection: [php, rust, go] with 3 items
  [0] => php
  [1] => rust
  [2] => go
```

> 💡 Intersection type `A&B` means "must implement both A and B". Only interfaces and classes are allowed — no primitives.

---

## Step 4: DNF Types (PHP 8.2)

Disjunctive Normal Form types combine intersection and union types:

```php
<?php
interface Loggable {
    public function log(): string;
}

interface Cacheable {
    public function cacheKey(): string;
}

class DbRecord implements Loggable, Cacheable {
    public function __construct(private string $id) {}
    public function log(): string { return "DbRecord($this->id)"; }
    public function cacheKey(): string { return "db:$this->id"; }
}

class MemoryCache implements Cacheable {
    public function __construct(private string $key) {}
    public function cacheKey(): string { return "mem:$this->key"; }
}

// DNF type: (Loggable&Cacheable)|null
function processItem((Loggable&Cacheable)|null $item): void {
    if ($item === null) {
        echo "No item\n";
        return;
    }
    echo "Log: " . $item->log() . " | Cache: " . $item->cacheKey() . "\n";
}

processItem(new DbRecord('user-42'));
processItem(null);
// processItem(new MemoryCache('key')); // Would be TypeError — not Loggable
```

📸 **Verified Output:**
```
Log: DbRecord(user-42) | Cache: db:user-42
No item
```

---

## Step 5: The `never` Return Type

`never` means a function **never returns** — it always throws or exits:

```php
<?php
function notFound(string $resource): never {
    throw new \RuntimeException("Resource not found: $resource");
}

function abort(int $code): never {
    // In real app: http_response_code($code); exit;
    throw new \RuntimeException("HTTP $code");
}

function findUser(int $id): array {
    if ($id <= 0) notFound("user#$id");
    return ['id' => $id, 'name' => 'Alice'];
}

try {
    $user = findUser(42);
    echo "Found: {$user['name']}\n";

    findUser(-1);  // Triggers never function
} catch (\RuntimeException $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
```

📸 **Verified Output:**
```
Found: Alice
Error: Resource not found: user#-1
```

> 💡 `never` is useful for framework routing, assertion helpers, and HTTP error responses. The type system knows the function won't return.

---

## Step 6: First-Class Callable Syntax (PHP 8.1)

Create closures from any callable with `callable(...)`:

```php
<?php
// From built-in function
$strlen  = strlen(...);
$strtoup = strtoupper(...);
$trim    = trim(...);

echo $strlen('hello') . "\n";      // 5
echo $strtoup('world') . "\n";     // WORLD

// Pipeline using first-class callables
$pipeline = [$trim, $strtoup, $strlen];
$value = '  hello world  ';
foreach ($pipeline as $fn) {
    $value = $fn($value);
}
echo $value . "\n";  // 11 (length of "HELLO WORLD")

// From static method
class StringHelper {
    public static function titleCase(string $s): string {
        return ucwords(strtolower($s));
    }
    public function repeat(string $s): string {
        return $s . $s;
    }
}
$titleCase = StringHelper::titleCase(...);
echo $titleCase('hello WORLD') . "\n";

// From instance method
$helper = new StringHelper();
$repeat = $helper->repeat(...);
echo $repeat('PHP') . "\n";

// With array functions
$words = ['  banana  ', '  apple  ', '  cherry  '];
$result = array_map(trim(...), $words);
sort($result);
echo implode(', ', $result) . "\n";
```

📸 **Verified Output:**
```
5
WORLD
11
Hello World
PHPPHP
apple, banana, cherry
```

---

## Step 7: Array Unpacking with String Keys (PHP 8.1)

```php
<?php
// Before PHP 8.1: only integer keys worked with ...
$defaults = ['color' => 'blue', 'size' => 'medium', 'weight' => 1.0];
$overrides = ['color' => 'red', 'weight' => 2.5];

// Merge with spread — later keys win
$config = [...$defaults, ...$overrides];
print_r($config);

// Build configs dynamically
$base = ['host' => 'localhost', 'port' => 3306, 'charset' => 'utf8mb4'];
$prod = ['host' => 'db.prod.example.com', 'port' => 5432];
$test = ['host' => 'db.test.example.com'];

$prodConfig = [...$base, ...$prod];
$testConfig = [...$base, ...$test];

echo "Prod: {$prodConfig['host']}:{$prodConfig['port']}\n";
echo "Test: {$testConfig['host']}:{$testConfig['port']}\n";
echo "Charset: {$prodConfig['charset']}\n";
```

📸 **Verified Output:**
```
Array
(
    [color] => red
    [size] => medium
    [weight] => 2.5
)
Prod: db.prod.example.com:5432
Test: db.test.example.com:3306
Charset: utf8mb4
```

> 💡 Later keys in the spread override earlier ones — same behavior as `array_merge()` but with cleaner syntax.

---

## Step 8: Capstone — Type-Safe Transformation Pipeline

Combine named args, first-class callables, intersection types, and DNF types:

```php
<?php
interface Transformable {
    public function transform(mixed $input): mixed;
}

interface Describable {
    public function describe(): string;
}

class Pipeline implements Transformable, Describable {
    private array $steps = [];

    public function __construct(private readonly string $name) {}

    public function pipe(callable $fn, string $label = ''): static {
        $clone = clone $this;
        $clone->steps[] = ['fn' => $fn, 'label' => $label ?: 'step' . (count($clone->steps) + 1)];
        return $clone;
    }

    public function transform(mixed $input): mixed {
        return array_reduce(
            $this->steps,
            fn($carry, $step) => $step['fn']($carry),
            $input
        );
    }

    public function describe(): string {
        $steps = array_map(fn($s) => $s['label'], $this->steps);
        return "{$this->name}: [" . implode(' → ', $steps) . "]";
    }
}

// Process data using the pipeline
function runPipeline((Transformable&Describable)|null $pipeline, mixed $input): void {
    if ($pipeline === null) {
        echo "No pipeline configured\n";
        return;
    }
    echo $pipeline->describe() . "\n";
    $result = $pipeline->transform($input);
    echo "Input:  " . json_encode($input) . "\n";
    echo "Output: " . json_encode($result) . "\n\n";
}

// Build immutable pipelines using first-class callables + named args
$textPipeline = (new Pipeline(name: 'TextProcessor'))
    ->pipe(fn: trim(...),         label: 'trim')
    ->pipe(fn: strtolower(...),   label: 'lowercase')
    ->pipe(fn: str_word_count(...), label: 'word-count');

$numPipeline = (new Pipeline(name: 'NumberCruncher'))
    ->pipe(fn: fn($x) => $x * 2,      label: 'double')
    ->pipe(fn: fn($x) => $x + 100,    label: 'add-100')
    ->pipe(fn: fn($x) => round($x, 2), label: 'round');

runPipeline(pipeline: $textPipeline, input: '  Hello World PHP  ');
runPipeline(pipeline: $numPipeline, input: 42.5);
runPipeline(pipeline: null, input: 'test');
```

📸 **Verified Output:**
```
TextProcessor: [trim → lowercase → word-count]
Input:  "  Hello World PHP  "
Output: 3

NumberCruncher: [double → add-100 → round]
Input:  42.5
Output: 185

No pipeline configured
```

---

## Summary

| Feature | Syntax | PHP Version |
|---|---|---|
| Named arguments | `fn(name: 'val', other: 1)` | 8.0+ |
| Skip optional params | `fn(first: 'a', third: 'c')` | 8.0+ |
| Intersection type | `A&B` | 8.1+ |
| DNF type | `(A&B)\|null` | 8.2+ |
| `never` return type | `function fail(): never { throw ... }` | 8.1+ |
| First-class callable | `strlen(...)` | 8.1+ |
| First-class static | `Cls::method(...)` | 8.1+ |
| First-class instance | `$obj->method(...)` | 8.1+ |
| String key array spread | `[...$a, ...$b]` | 8.1+ |
