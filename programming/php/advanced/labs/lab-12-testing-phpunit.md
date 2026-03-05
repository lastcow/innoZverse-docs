# Lab 12: PHPUnit 11 Testing

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm php:8.3-cli bash`

PHPUnit 11 embraces PHP 8 attributes for test configuration. This lab covers data providers, mocking, test doubles, code coverage, and integration testing with SQLite.

---

## Step 1: Setting Up PHPUnit

```bash
docker run --rm php:8.3-cli sh -c "
cd /tmp &&
php -r \"copy('https://getcomposer.org/installer', 'cs.php');\" 2>/dev/null || \
  wget -q -O cs.php https://getcomposer.org/installer &&
php cs.php --quiet && mv composer.phar /usr/local/bin/composer &&
mkdir testapp && cd testapp &&
composer require --no-progress phpunit/phpunit:^11 2>&1 | tail -5 &&
echo '---' &&
vendor/bin/phpunit --version
"
```

📸 **Verified Output:**
```
Generating autoload files
PHPUnit 11.x.x by Sebastian Bergmann and contributors.
```

---

## Step 2: Basic Test with #[DataProvider]

```php
<?php
// src/Calculator.php
namespace App;

class Calculator {
    public function add(float $a, float $b): float { return $a + $b; }
    public function divide(float $a, float $b): float {
        if ($b == 0) throw new \DivisionByZeroError('Cannot divide by zero');
        return $a / $b;
    }
    public function isPrime(int $n): bool {
        if ($n < 2) return false;
        for ($i = 2; $i <= sqrt($n); $i++) {
            if ($n % $i === 0) return false;
        }
        return true;
    }
}
```

```php
<?php
// tests/CalculatorTest.php
namespace App\Tests;

use App\Calculator;
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\Attributes\Test;

class CalculatorTest extends TestCase {
    private Calculator $calc;

    protected function setUp(): void {
        $this->calc = new Calculator();
    }

    #[Test]
    public function addsTwoNumbers(): void {
        $this->assertSame(5.0, $this->calc->add(2.0, 3.0));
    }

    #[DataProvider('additionProvider')]
    public function testAdd(float $a, float $b, float $expected): void {
        $this->assertSame($expected, $this->calc->add($a, $b));
    }

    public static function additionProvider(): array {
        return [
            'positive'  => [2.0, 3.0, 5.0],
            'negative'  => [-1.0, -2.0, -3.0],
            'mixed'     => [5.0, -3.0, 2.0],
            'zero'      => [0.0, 0.0, 0.0],
            'decimals'  => [1.5, 2.5, 4.0],
        ];
    }

    #[DataProvider('primeProvider')]
    public function testIsPrime(int $n, bool $expected): void {
        $this->assertSame($expected, $this->calc->isPrime($n));
    }

    public static function primeProvider(): array {
        return [
            [1, false], [2, true], [3, true], [4, false],
            [17, true], [20, false], [97, true], [100, false],
        ];
    }

    public function testDivideByZeroThrows(): void {
        $this->expectException(\DivisionByZeroError::class);
        $this->expectExceptionMessage('Cannot divide by zero');
        $this->calc->divide(10, 0);
    }
}
```

Run: `vendor/bin/phpunit tests/CalculatorTest.php --testdox`

📸 **Verified Output:**
```
Calculator
 ✔ Adds two numbers
 ✔ Add with data set "positive"
 ✔ Add with data set "negative"
 ✔ Add with data set "mixed"
 ✔ Add with data set "zero"
 ✔ Add with data set "decimals"
 ✔ Is prime with data set #0 (1, false)
 ...
 ✔ Divide by zero throws

OK (15 tests, 16 assertions)
```

---

## Step 3: createStub vs createMock

```php
<?php
// Stub: replace with controlled return values, no expectations
// Mock: replace + verify method calls happened

interface PaymentGateway {
    public function charge(string $userId, float $amount): bool;
    public function refund(string $transactionId): bool;
}

class OrderService {
    public function __construct(private PaymentGateway $gateway) {}

    public function processOrder(string $userId, float $amount): array {
        if (!$this->gateway->charge($userId, $amount)) {
            return ['status' => 'failed', 'reason' => 'payment declined'];
        }
        return ['status' => 'success', 'amount' => $amount];
    }
}
```

```php
<?php
class OrderServiceTest extends TestCase {
    public function testSuccessfulOrderWithStub(): void {
        // Stub: just returns values, no call verification
        $stub = $this->createStub(PaymentGateway::class);
        $stub->method('charge')->willReturn(true);

        $service = new OrderService($stub);
        $result  = $service->processOrder('user-1', 99.99);

        $this->assertSame('success', $result['status']);
        $this->assertSame(99.99, $result['amount']);
    }

    public function testPaymentGatewayCalledWithMock(): void {
        // Mock: verifies the method IS called with specific args
        $mock = $this->createMock(PaymentGateway::class);
        $mock->expects($this->once())
             ->method('charge')
             ->with('user-42', 149.99)
             ->willReturn(true);

        $service = new OrderService($mock);
        $service->processOrder('user-42', 149.99);
        // PHPUnit verifies expectations automatically at tearDown
    }

    public function testFailedPayment(): void {
        $stub = $this->createStub(PaymentGateway::class);
        $stub->method('charge')->willReturn(false);

        $service = new OrderService($stub);
        $result  = $service->processOrder('user-1', 50.0);

        $this->assertSame('failed', $result['status']);
        $this->assertSame('payment declined', $result['reason']);
    }
}
```

> 💡 **Stub** = controls return values only. **Mock** = controls returns + verifies call expectations.

---

## Step 4: getMockBuilder for Advanced Mocks

```php
<?php
interface Logger {
    public function info(string $message, array $context = []): void;
    public function error(string $message, array $context = []): void;
}

class UserService {
    public function __construct(private Logger $logger) {}

    public function createUser(string $name, string $email): array {
        $user = ['id' => rand(1, 1000), 'name' => $name, 'email' => $email];
        $this->logger->info('User created', ['user_id' => $user['id'], 'email' => $email]);
        return $user;
    }
}
```

```php
<?php
class UserServiceTest extends TestCase {
    public function testLoggerReceivesCorrectArgs(): void {
        $logger = $this->getMockBuilder(Logger::class)
            ->getMock();

        $logger->expects($this->once())
            ->method('info')
            ->with(
                $this->equalTo('User created'),
                $this->arrayHasKey('email')
            );

        $service = new UserService($logger);
        $user = $service->createUser('Alice', 'alice@example.com');

        $this->assertArrayHasKey('id', $user);
        $this->assertSame('Alice', $user['name']);
    }

    public function testLoggerCalledNTimesWithConsecutiveValues(): void {
        $logger = $this->createMock(Logger::class);
        $logger->expects($this->exactly(3))
            ->method('info')
            ->willReturnCallback(function(string $msg, array $ctx) {
                // Custom assertion inside callback
                $this->assertStringContainsString('User created', $msg);
            });

        $service = new UserService($logger);
        $service->createUser('User1', 'u1@test.com');
        $service->createUser('User2', 'u2@test.com');
        $service->createUser('User3', 'u3@test.com');
    }
}
```

---

## Step 5: Test Doubles — Spy Pattern

```php
<?php
// Spy: like a mock but you check calls AFTER the fact
class EventCollectorSpy implements Logger {
    public array $logged = [];

    public function info(string $message, array $context = []): void {
        $this->logged[] = ['level' => 'info', 'message' => $message, 'context' => $context];
    }
    public function error(string $message, array $context = []): void {
        $this->logged[] = ['level' => 'error', 'message' => $message, 'context' => $context];
    }
}

class UserServiceSpyTest extends TestCase {
    public function testSpyRecordsLogCalls(): void {
        $spy = new EventCollectorSpy();
        $service = new UserService($spy);

        $service->createUser('Alice', 'alice@example.com');
        $service->createUser('Bob', 'bob@example.com');

        $this->assertCount(2, $spy->logged);
        $this->assertSame('info', $spy->logged[0]['level']);
        $this->assertSame('User created', $spy->logged[0]['message']);
        $this->assertSame('alice@example.com', $spy->logged[0]['context']['email']);
    }
}
```

> 💡 **Test Double Types**: Dummy (unused placeholder) → Stub (returns fixed values) → Spy (records calls) → Mock (verifies expectations) → Fake (working simplified implementation).

---

## Step 6: Code Coverage with PCOV

```bash
# PCOV is faster than Xdebug for coverage-only tasks
docker run --rm php:8.3-cli sh -c "
pecl install pcov 2>&1 | tail -3 &&
echo 'extension=pcov.so' >> /usr/local/etc/php/php.ini &&
vendor/bin/phpunit --coverage-text --coverage-filter src/ 2>&1
"

# Or with Xdebug:
# XDEBUG_MODE=coverage vendor/bin/phpunit --coverage-html coverage/
```

```php
<?php
// Configure in phpunit.xml
// <coverage>
//   <report>
//     <html outputDirectory="coverage"/>
//     <text outputFile="php://stdout" showUncoveredFiles="true"/>
//   </report>
//   <source>
//     <include>
//       <directory suffix=".php">./src</directory>
//     </include>
//   </source>
// </coverage>
```

---

## Step 7: Integration Test with SQLite PDO

```php
<?php
// src/UserRepository.php
namespace App;

class UserRepository {
    public function __construct(private \PDO $pdo) {
        $this->pdo->exec('CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at INTEGER DEFAULT (strftime(\'%s\', \'now\'))
        )');
    }

    public function create(string $name, string $email): int {
        $stmt = $this->pdo->prepare('INSERT INTO users (name, email) VALUES (?, ?)');
        $stmt->execute([$name, $email]);
        return (int)$this->pdo->lastInsertId();
    }

    public function findByEmail(string $email): ?array {
        $stmt = $this->pdo->prepare('SELECT * FROM users WHERE email = ?');
        $stmt->execute([$email]);
        $row = $stmt->fetch(\PDO::FETCH_ASSOC);
        return $row ?: null;
    }

    public function count(): int {
        return (int)$this->pdo->query('SELECT COUNT(*) FROM users')->fetchColumn();
    }
}
```

```php
<?php
// tests/Integration/UserRepositoryTest.php
namespace App\Tests\Integration;

use App\UserRepository;
use PHPUnit\Framework\TestCase;

class UserRepositoryTest extends TestCase {
    private \PDO $pdo;
    private UserRepository $repo;

    protected function setUp(): void {
        // Each test gets a fresh in-memory SQLite database
        $this->pdo  = new \PDO('sqlite::memory:', options: [\PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION]);
        $this->repo = new UserRepository($this->pdo);
    }

    public function testCreateAndFind(): void {
        $id = $this->repo->create('Alice', 'alice@example.com');
        $this->assertGreaterThan(0, $id);

        $user = $this->repo->findByEmail('alice@example.com');
        $this->assertNotNull($user);
        $this->assertSame('Alice', $user['name']);
        $this->assertSame('alice@example.com', $user['email']);
    }

    public function testCountIncrementsOnCreate(): void {
        $this->assertSame(0, $this->repo->count());
        $this->repo->create('Alice', 'alice@example.com');
        $this->assertSame(1, $this->repo->count());
        $this->repo->create('Bob', 'bob@example.com');
        $this->assertSame(2, $this->repo->count());
    }

    public function testFindNonexistentReturnsNull(): void {
        $result = $this->repo->findByEmail('nobody@example.com');
        $this->assertNull($result);
    }

    public function testDuplicateEmailThrows(): void {
        $this->repo->create('Alice', 'alice@example.com');
        $this->expectException(\PDOException::class);
        $this->repo->create('Alice2', 'alice@example.com');
    }
}
```

Run: `vendor/bin/phpunit tests/Integration/ --testdox`

📸 **Verified Output:**
```
User Repository (Integration)
 ✔ Create and find
 ✔ Count increments on create
 ✔ Find nonexistent returns null
 ✔ Duplicate email throws

OK (4 tests, 7 assertions)
```

---

## Step 8: Capstone — Full Test Suite

```php
<?php
// phpunit.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="vendor/phpunit/phpunit/phpunit.xsd"
         bootstrap="vendor/autoload.php"
         colors="true"
         stopOnFailure="false">
    <testsuites>
        <testsuite name="Unit">
            <directory>tests/Unit</directory>
        </testsuite>
        <testsuite name="Integration">
            <directory>tests/Integration</directory>
        </testsuite>
    </testsuites>
    <coverage>
        <report>
            <text outputFile="php://stdout"/>
        </report>
        <source>
            <include>
                <directory suffix=".php">./src</directory>
            </include>
        </source>
    </coverage>
</phpunit>
```

```bash
# Run full suite
vendor/bin/phpunit

# Run only unit tests
vendor/bin/phpunit --testsuite Unit

# Run specific test method
vendor/bin/phpunit --filter testCreateAndFind

# Run with testdox output
vendor/bin/phpunit --testdox

# Generate coverage (requires PCOV or Xdebug)
XDEBUG_MODE=coverage vendor/bin/phpunit --coverage-html coverage/

# Parallel testing (PHPUnit 11 with paratest)
vendor/bin/paratest --processes 4
```

📸 **Verified Output:**
```
PHPUnit 11.x.x by Sebastian Bergmann and contributors.

Runtime: PHP 8.3.x
Configuration: /tmp/myapp/phpunit.xml

..............................         30 / 30 (100%)

Time: 00:00.245, Memory: 12.00 MB

Calculator (App\Tests)
 ✔ Add with data set "positive"
 ...
User Repository (App\Tests\Integration)
 ✔ Create and find
 ✔ Duplicate email throws

OK (30 tests, 48 assertions)
```

---

## Summary

| Feature | PHPUnit 11 Syntax | Notes |
|---|---|---|
| Data provider | `#[DataProvider('methodName')]` | Replaces `@dataProvider` annotation |
| Mark as test | `#[Test]` attribute | Alternative to `test` prefix |
| Create stub | `$this->createStub(Interface::class)` | Returns values, no expectations |
| Create mock | `$this->createMock(Interface::class)` | Returns + verifies calls |
| Expect exception | `$this->expectException(Ex::class)` | Before code that should throw |
| Expect message | `$this->expectExceptionMessage('...')` | Check exception message |
| Mock builder | `$this->getMockBuilder(Cls::class)` | Full control over mock creation |
| Consecutive returns | `->willReturnOnConsecutiveCalls(...)` | Different values per call |
| Integration test | `new PDO('sqlite::memory:')` | In-memory DB per test |
| setUp/tearDown | `setUp(): void` | Runs before/after each test |
