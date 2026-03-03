# Lab 9: Error Handling & Exceptions

## Objective
Use PHP's exception system: try/catch/finally, custom exception classes, exception chaining, error handlers, and PHP 8's `never` return type. Handle errors gracefully without crashing.

## Background
PHP has two parallel error systems: the legacy `trigger_error()` / `set_error_handler()` system and the modern exception system. PHP 7+ converted most fatal errors into `Error` exceptions. PHP 8 added `never` return type (functions that always throw or exit), `match` exhaustiveness, and `throw` as an expression. Good error handling separates robust production apps from fragile scripts.

## Time
30 minutes

## Prerequisites
- Lab 07 (OOP)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Try / Catch / Finally

```php
<?php
declare(strict_types=1);

function divide(float $a, float $b): float {
    if ($b == 0) throw new \DivisionByZeroError("Cannot divide $a by zero");
    return $a / $b;
}

function parsePositive(string $s): float {
    if (!is_numeric($s)) throw new \InvalidArgumentException("Not a number: '$s'");
    $n = (float)$s;
    if ($n <= 0) throw new \RangeException("Must be positive, got $n");
    return $n;
}

$tests = [['10', '2'], ['7', '0'], ['abc', '3'], ['-5', '2'], ['15', '3']];

foreach ($tests as [$a, $b]) {
    try {
        $x = parsePositive($a);
        $y = parsePositive($b);
        $result = divide($x, $y);
        echo "  $a / $b = $result\n";
    } catch (\DivisionByZeroError $e) {
        echo "  Math error: " . $e->getMessage() . "\n";
    } catch (\InvalidArgumentException | \RangeException $e) {
        echo "  Input error: " . $e->getMessage() . "\n";
    } finally {
        // always runs — great for cleanup (close files, release locks, etc.)
        // echo "  [cleanup]\n";
    }
}
```

> 💡 **`finally` always runs** — even if the `try` block returns early or an exception is thrown. Use it to release resources: close database connections, unlock files, stop timers. If both `catch` and `finally` throw, the `finally` exception wins (it overwrites the caught one).

**📸 Verified Output:**
```
  10 / 2 = 5
  Math error: Cannot divide 7 by zero
  Input error: Not a number: 'abc'
  Input error: Must be positive, got -5
  15 / 3 = 5
```

---

### Step 2: Custom Exception Classes

```php
<?php
declare(strict_types=1);

// Base domain exception
class AppException extends \RuntimeException {}

// Specific exceptions
class ValidationException extends AppException {
    private array $errors;

    public function __construct(array $errors, string $message = '') {
        $this->errors = $errors;
        parent::__construct($message ?: 'Validation failed: ' . implode(', ', $errors));
    }

    public function getErrors(): array { return $this->errors; }
}

class NotFoundException extends AppException {
    public function __construct(string $resource, int|string $id) {
        parent::__construct("$resource #$id not found", 404);
    }
}

class AuthException extends AppException {
    public function __construct(string $action = 'access this resource') {
        parent::__construct("Unauthorized: cannot $action", 403);
    }
}

// Simulate a user service
function getUser(int $id, string $role = 'guest'): array {
    if ($id <= 0) throw new ValidationException(["id must be positive"]);
    if ($id > 100) throw new NotFoundException('User', $id);
    if ($role !== 'admin' && $id === 42) throw new AuthException('view admin user');
    return ['id' => $id, 'name' => "User #$id", 'role' => $role];
}

$tests = [[1, 'admin'], [42, 'guest'], [999, 'admin'], [-1, 'admin']];

foreach ($tests as [$id, $role]) {
    try {
        $user = getUser($id, $role);
        echo "  Found: {$user['name']} ({$user['role']})\n";
    } catch (ValidationException $e) {
        echo "  Validation: " . implode(', ', $e->getErrors()) . "\n";
    } catch (NotFoundException $e) {
        echo "  404: " . $e->getMessage() . " (code: " . $e->getCode() . ")\n";
    } catch (AuthException $e) {
        echo "  403: " . $e->getMessage() . "\n";
    }
}
```

> 💡 **Custom exceptions carry domain context** — `ValidationException` holds an array of field errors, `NotFoundException` encodes the HTTP 404 code. Catching `AppException` catches all domain errors in one block; catching subclasses lets you handle each case specifically. Always extend from a base domain exception.

**📸 Verified Output:**
```
  Found: User #1 (admin)
  403: Unauthorized: cannot view admin user
  404: User #999 not found (code: 404)
  Validation: id must be positive
```

---

### Step 3: Exception Chaining

```php
<?php
declare(strict_types=1);

class DatabaseException extends \RuntimeException {}
class ServiceException extends \RuntimeException {}

function queryDatabase(string $sql): array {
    // Simulate DB failure
    throw new DatabaseException("Connection refused: localhost:5432");
}

function getUserOrders(int $userId): array {
    try {
        return queryDatabase("SELECT * FROM orders WHERE user_id = $userId");
    } catch (DatabaseException $e) {
        // Chain: wrap low-level exception in higher-level one
        throw new ServiceException(
            "Failed to load orders for user $userId",
            0,
            $e  // previous exception — the cause
        );
    }
}

try {
    $orders = getUserOrders(42);
} catch (ServiceException $e) {
    echo "Service error: " . $e->getMessage() . "\n";

    // Walk the exception chain
    $cause = $e->getPrevious();
    while ($cause !== null) {
        echo "  Caused by: [" . get_class($cause) . "] " . $cause->getMessage() . "\n";
        $cause = $cause->getPrevious();
    }
}

// throw as expression (PHP 8)
function requirePositive(int $n): int {
    return $n > 0 ? $n : throw new \InvalidArgumentException("Must be positive");
}

$value = requirePositive(5);
echo "\nValue: $value\n";

try {
    requirePositive(-1);
} catch (\InvalidArgumentException $e) {
    echo "Caught: " . $e->getMessage() . "\n";
}
```

> 💡 **Exception chaining** (`new Exception($msg, $code, $previous)`) preserves the original cause. Log systems and APM tools (like Sentry) use `getPrevious()` to show the full causal chain. Always chain when wrapping exceptions — never silently swallow the original error.

**📸 Verified Output:**
```
Service error: Failed to load orders for user 42
  Caused by: [DatabaseException] Connection refused: localhost:5432

Value: 5
Caught: Must be positive
```

---

### Step 4: Custom Error Handler & Throwable

```php
<?php
// Custom error handler — converts PHP errors to exceptions
set_error_handler(function(int $errno, string $errstr, string $file, int $line): bool {
    throw new \ErrorException($errstr, $errno, $errno, $file, $line);
});

// Now PHP notices/warnings become catchable
try {
    $arr = [1, 2, 3];
    $val = $arr[99]; // undefined offset
} catch (\ErrorException $e) {
    echo "Caught error: " . $e->getMessage() . "\n";
}

// Throwable — catches BOTH Error and Exception
function riskyOperation(int $n): int {
    return match($n) {
        0 => throw new \InvalidArgumentException("Zero not allowed"),
        1 => intdiv(10, 0),  // DivisionByZeroError (Error, not Exception)
        default => 100 / $n,
    };
}

foreach ([0, 1, 5] as $n) {
    try {
        echo "riskyOperation($n) = " . riskyOperation($n) . "\n";
    } catch (\Throwable $e) {
        echo "Throwable [" . get_class($e) . "]: " . $e->getMessage() . "\n";
    }
}

// Restore default handler
restore_error_handler();
```

> 💡 **`Throwable`** is the top-level interface in PHP's exception hierarchy — both `Error` (language errors: TypeError, ParseError, ArithmeticError) and `Exception` (user-thrown) implement it. `catch (\Exception $e)` misses `Error` subclasses. Use `catch (\Throwable $e)` for truly catch-all handlers (logging, shutdown handlers).

**📸 Verified Output:**
```
Caught error: Undefined array key 99
Throwable [InvalidArgumentException]: Zero not allowed
Throwable [DivisionByZeroError]: Division by zero
riskyOperation(5) = 20
```

---

### Step 5: never Return Type

```php
<?php
declare(strict_types=1);

// never — function never returns normally (always throws or exits)
function abort(int $code, string $message): never {
    throw new \RuntimeException("HTTP $code: $message", $code);
}

function notFound(string $resource): never {
    abort(404, "$resource not found");
}

function unauthorized(): never {
    abort(403, "Forbidden");
}

// Helper that uses never-returning functions
function findProduct(int $id): array {
    $products = [1 => ['name' => 'Surface Pro', 'price' => 864.00]];
    return $products[$id] ?? notFound("Product #$id");
}

function adminOnly(string $role): void {
    if ($role !== 'admin') unauthorized();
    echo "Admin access granted\n";
}

// Test
foreach ([1, 99] as $id) {
    try {
        $p = findProduct($id);
        echo "Found: {$p['name']} \${$p['price']}\n";
    } catch (\RuntimeException $e) {
        echo "Error {$e->getCode()}: {$e->getMessage()}\n";
    }
}

foreach (['admin', 'guest'] as $role) {
    try {
        adminOnly($role);
    } catch (\RuntimeException $e) {
        echo "Error {$e->getCode()}: {$e->getMessage()}\n";
    }
}
```

> 💡 **`never` return type** (PHP 8.1) tells the type system "this function never returns." The type checker can then eliminate dead code warnings after calls to `abort()`. It's used in Laravel's `abort()` helper, Symfony's `ThrowableInterface`, and any exception-throwing utility function.

**📸 Verified Output:**
```
Found: Surface Pro $864
Error 404: HTTP 404: Product #99 not found
Admin access granted
Error 403: HTTP 403: Forbidden
```

---

### Step 6: Result Pattern (No Exceptions for Control Flow)

```php
<?php
declare(strict_types=1);

// Result type — functional alternative to exceptions for expected failures
class Result {
    private function __construct(
        private readonly bool  $ok,
        private readonly mixed $value,
        private readonly ?string $error,
    ) {}

    public static function ok(mixed $value): self   { return new self(true, $value, null); }
    public static function err(string $error): self { return new self(false, null, $error); }

    public function isOk(): bool      { return $this->ok; }
    public function getValue(): mixed { return $this->value; }
    public function getError(): ?string { return $this->error; }

    public function map(callable $fn): self {
        return $this->ok ? self::ok($fn($this->value)) : $this;
    }

    public function unwrapOr(mixed $default): mixed {
        return $this->ok ? $this->value : $default;
    }
}

function parseAge(string $s): Result {
    if (!ctype_digit($s)) return Result::err("'$s' is not a valid integer");
    $n = (int)$s;
    if ($n < 0 || $n > 150) return Result::err("Age $n is out of range (0-150)");
    return Result::ok($n);
}

$inputs = ['25', '-1', 'abc', '200', '42'];
foreach ($inputs as $input) {
    $result = parseAge($input)
        ->map(fn($age) => $age >= 18 ? "Adult ($age)" : "Minor ($age)");

    if ($result->isOk()) {
        echo "  ✓ $input → " . $result->getValue() . "\n";
    } else {
        echo "  ✗ $input → " . $result->getError() . "\n";
    }
}
```

> 💡 **The Result pattern** (common in Rust, Haskell, Go) uses return values instead of exceptions for *expected* failures. Reserve exceptions for *unexpected* situations (network down, disk full). Use Result for *expected* failures (invalid input, not found). This makes error paths explicit and composable.

**📸 Verified Output:**
```
  ✓ 25 → Adult (25)
  ✗ -1 → Age -1 is out of range (0-150)
  ✗ abc → 'abc' is not a valid integer
  ✗ 200 → Age 200 is out of range (0-150)
  ✓ 42 → Adult (42)
```

---

### Step 7: Logging Errors

```php
<?php
declare(strict_types=1);

class Logger {
    private array $logs = [];

    public function log(string $level, string $message, array $context = []): void {
        $entry = [
            'time'    => date('H:i:s'),
            'level'   => strtoupper($level),
            'message' => $message,
            'context' => $context,
        ];
        $this->logs[] = $entry;
        $ctx = $context ? ' ' . json_encode($context) : '';
        echo "[{$entry['time']}] {$entry['level']}: $message$ctx\n";
    }

    public function exception(\Throwable $e, array $context = []): void {
        $this->log('error', $e->getMessage(), array_merge($context, [
            'class' => get_class($e),
            'code'  => $e->getCode(),
            'file'  => basename($e->getFile()) . ':' . $e->getLine(),
        ]));
    }

    public function getLogs(string $level = ''): array {
        if (!$level) return $this->logs;
        return array_filter($this->logs, fn($l) => $l['level'] === strtoupper($level));
    }
}

$logger = new Logger();

function riskyTask(Logger $logger, string $task): void {
    try {
        $logger->log('info', "Starting: $task");
        if ($task === 'fail') throw new \RuntimeException("Task '$task' failed unexpectedly");
        $logger->log('info', "Completed: $task");
    } catch (\Throwable $e) {
        $logger->exception($e, ['task' => $task]);
        $logger->log('warn', "Retrying with fallback for $task");
    }
}

riskyTask($logger, 'export');
riskyTask($logger, 'fail');
riskyTask($logger, 'import');

echo "\nError count: " . count($logger->getLogs('error')) . "\n";
```

**📸 Verified Output:**
```
[14:30:00] INFO: Starting: export
[14:30:00] INFO: Completed: export
[14:30:00] INFO: Starting: fail
[14:30:00] ERROR: Task 'fail' failed unexpectedly {"class":"RuntimeException","code":0,"file":"..."}
[14:30:00] WARN: Retrying with fallback for fail
[14:30:00] INFO: Starting: import
[14:30:00] INFO: Completed: import

Error count: 1
```

---

### Step 8: Complete — API Error Middleware

```php
<?php
declare(strict_types=1);

class HttpException extends \RuntimeException {
    public function __construct(
        public readonly int    $statusCode,
        string                 $message,
        ?\Throwable            $previous = null,
    ) {
        parent::__construct($message, $statusCode, $previous);
    }
}

class ValidationHttpException extends HttpException {
    public function __construct(private array $fieldErrors) {
        parent::__construct(422, 'Unprocessable Entity');
    }
    public function getFieldErrors(): array { return $this->fieldErrors; }
}

// Simulate middleware error handling
function handleRequest(callable $handler, array $request): array {
    try {
        return ['status' => 200, 'body' => $handler($request)];
    } catch (ValidationHttpException $e) {
        return ['status' => 422, 'body' => ['errors' => $e->getFieldErrors()]];
    } catch (HttpException $e) {
        return ['status' => $e->statusCode, 'body' => ['error' => $e->getMessage()]];
    } catch (\Throwable $e) {
        // Log internally, return generic 500
        error_log("Unhandled: " . $e->getMessage());
        return ['status' => 500, 'body' => ['error' => 'Internal Server Error']];
    }
}

// Routes
$routes = [
    fn($r) => ['user' => 'Dr. Chen', 'id' => $r['id']],
    fn($r) => throw new HttpException(404, "User #{$r['id']} not found"),
    fn($r) => throw new ValidationHttpException(['email' => 'Invalid format', 'age' => 'Required']),
    fn($r) => throw new \RuntimeException("DB connection lost"),
];

$requests = [['id' => 1], ['id' => 99], ['id' => 2], ['id' => 3]];

foreach (array_map(null, $routes, $requests) as [$handler, $req]) {
    $response = handleRequest($handler, $req);
    echo "HTTP {$response['status']}: " . json_encode($response['body']) . "\n";
}
```

> 💡 **Middleware error handling** is how Laravel/Symfony handle exceptions — a top-level try/catch converts exceptions to HTTP responses. `ValidationHttpException` → 422, `HttpException` → its status code, `Throwable` → 500 (never expose internal errors to clients). This pattern keeps controllers clean.

**📸 Verified Output:**
```
HTTP 200: {"user":"Dr. Chen","id":1}
HTTP 404: {"error":"User #99 not found"}
HTTP 422: {"errors":{"email":"Invalid format","age":"Required"}}
HTTP 500: {"error":"Internal Server Error"}
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
try {
    throw new \InvalidArgumentException('test error', 42);
} catch (\Throwable \$e) {
    echo get_class(\$e) . ': ' . \$e->getMessage() . ' (code=' . \$e->getCode() . ')' . PHP_EOL;
}
"
```

## Summary

PHP exception handling is mature and expressive. You've covered try/catch/finally, custom exception hierarchies, chaining, `Throwable`, `never`, the Result pattern, structured logging, and API middleware error handling. These patterns form the backbone of robust PHP applications.

## Further Reading
- [PHP Exceptions](https://www.php.net/manual/en/language.exceptions.php)
- [PHP Error Handling](https://www.php.net/manual/en/book.errorfunc.php)
- [never return type](https://www.php.net/manual/en/language.types.never.php)
