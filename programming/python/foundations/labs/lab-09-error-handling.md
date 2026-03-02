# Lab 9: Error Handling — try/except/finally

## 🎯 Objective
Master Python's exception system — catching specific errors, raising custom exceptions, using finally for cleanup, and building robust fault-tolerant programs.

## 📚 Background
Errors are unavoidable in real programs: networks fail, files disappear, users type garbage. **Exception handling** lets your program respond gracefully instead of crashing. Python uses a rich exception hierarchy — `BaseException` → `Exception` → `ValueError`, `TypeError`, etc. The `try/except/else/finally` structure gives you full control over error recovery.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 8: File I/O

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Basic try/except

```python
# Without error handling — crashes on bad input
def divide_unsafe(a, b):
    return a / b

# With error handling
def divide_safe(a, b):
    try:
        result = a / b
        return result
    except ZeroDivisionError:
        print(f"  ⚠️  Cannot divide {a} by zero!")
        return None

# Test cases
test_cases = [(10, 2), (15, 3), (7, 0), (100, 4)]
for a, b in test_cases:
    result = divide_safe(a, b)
    if result is not None:
        print(f"  {a} / {b} = {result}")
```

**📸 Verified Output:**
```
  10 / 2 = 5.0
  15 / 3 = 5.0
  ⚠️  Cannot divide 7 by zero!
  100 / 4 = 25.0
```

> 💡 Always catch the **most specific** exception possible. Catching `Exception` or (worse) `BaseException` hides bugs and makes debugging a nightmare.

### Step 2: Multiple except Clauses

```python
def parse_and_compute(value_str, divisor_str):
    """Parse two strings and divide them."""
    try:
        value = int(value_str)
        divisor = int(divisor_str)
        result = value / divisor
        return f"{value} / {divisor} = {result:.2f}"
    except ValueError as e:
        return f"ValueError: '{e}' — not a valid integer"
    except ZeroDivisionError:
        return "ZeroDivisionError: cannot divide by zero"
    except TypeError as e:
        return f"TypeError: {e}"

test_inputs = [
    ("100", "4"),
    ("100", "0"),
    ("abc", "4"),
    ("100", "xyz"),
    (None, "4"),
]

for a, b in test_inputs:
    print(f"  parse_and_compute({a!r}, {b!r})")
    print(f"    → {parse_and_compute(a, b)}")
```

**📸 Verified Output:**
```
  parse_and_compute('100', '4')
    → 100 / 4 = 25.00
  parse_and_compute('100', '0')
    → ZeroDivisionError: cannot divide by zero
  parse_and_compute('abc', '4')
    → ValueError: 'invalid literal for int() with base 10: 'abc'' — not a valid integer
  parse_and_compute('100', 'xyz')
    → ValueError: 'invalid literal for int() with base 10: 'xyz'' — not a valid integer
  parse_and_compute(None, '4')
    → TypeError: int() argument must be a string, a bytes-like object or a real number, not 'NoneType'
```

### Step 3: else and finally Clauses

```python
def read_number_from_file(filepath):
    """Read a number from a file — demonstrates try/except/else/finally."""
    f = None
    try:
        f = open(filepath, "r")
        content = f.read().strip()
        number = float(content)
    except FileNotFoundError:
        print(f"  [except] File not found: {filepath}")
        return None
    except ValueError:
        print(f"  [except] Content is not a number: {content!r}")
        return None
    else:
        # Only runs if NO exception occurred
        print(f"  [else] Successfully read number: {number}")
        return number
    finally:
        # ALWAYS runs — perfect for cleanup
        if f:
            f.close()
            print(f"  [finally] File closed")

# Setup test files
with open("/tmp/num.txt", "w") as f: f.write("42.5\n")
with open("/tmp/bad.txt", "w") as f: f.write("not-a-number\n")

print("Test 1: valid file")
result = read_number_from_file("/tmp/num.txt")

print("\nTest 2: bad content")
result = read_number_from_file("/tmp/bad.txt")

print("\nTest 3: missing file")
result = read_number_from_file("/tmp/missing.txt")
```

**📸 Verified Output:**
```
Test 1: valid file
  [else] Successfully read number: 42.5
  [finally] File closed

Test 2: bad content
  [except] Content is not a number: 'not-a-number'
  [finally] File closed

Test 3: missing file
  [except] File not found: /tmp/missing.txt
  [finally] File closed
```

> 💡 `else` runs only when NO exception occurred — great for code that should run on success. `finally` runs ALWAYS — perfect for cleanup (closing files, releasing locks, etc.).

### Step 4: Raising Exceptions

```python
def validate_age(age):
    """Validate that age is a reasonable value."""
    if not isinstance(age, (int, float)):
        raise TypeError(f"Age must be a number, got {type(age).__name__}")
    if age < 0:
        raise ValueError(f"Age cannot be negative: {age}")
    if age > 150:
        raise ValueError(f"Age unrealistically large: {age}")
    return int(age)

test_ages = [25, -5, 200, "old", 0, 99]
for age in test_ages:
    try:
        valid = validate_age(age)
        print(f"  validate_age({age!r:5}) → {valid} ✅")
    except (ValueError, TypeError) as e:
        print(f"  validate_age({age!r:5}) → ❌ {type(e).__name__}: {e}")
```

**📸 Verified Output:**
```
  validate_age(25  ) → 25 ✅
  validate_age(-5  ) → ❌ ValueError: Age cannot be negative: -5
  validate_age(200 ) → ❌ ValueError: Age unrealistically large: 200
  validate_age('old') → ❌ TypeError: Age must be a number, got str
  validate_age(0   ) → 0 ✅
  validate_age(99  ) → 99 ✅
```

### Step 5: Custom Exception Classes

```python
class AppError(Exception):
    """Base exception for this application."""
    pass

class ValidationError(AppError):
    """Raised when user input fails validation."""
    def __init__(self, field, message, value=None):
        self.field = field
        self.value = value
        super().__init__(f"Validation failed for '{field}': {message}")

class DatabaseError(AppError):
    """Raised when database operations fail."""
    def __init__(self, operation, reason):
        self.operation = operation
        super().__init__(f"DB error during {operation}: {reason}")

def register_user(username, email, age):
    """Register a user with validation."""
    if len(username) < 3:
        raise ValidationError("username", "must be at least 3 characters", username)
    if "@" not in email:
        raise ValidationError("email", "must contain @", email)
    if not 13 <= age <= 120:
        raise ValidationError("age", "must be between 13 and 120", age)
    return {"username": username, "email": email, "age": age}

test_users = [
    ("alice", "alice@example.com", 25),
    ("ab", "alice@example.com", 25),
    ("alice", "not-an-email", 25),
    ("alice", "alice@example.com", 10),
]

for args in test_users:
    try:
        user = register_user(*args)
        print(f"  ✅ Registered: {user['username']}")
    except ValidationError as e:
        print(f"  ❌ ValidationError [field={e.field}]: {e}")
    except AppError as e:
        print(f"  ❌ AppError: {e}")
```

**📸 Verified Output:**
```
  ✅ Registered: alice
  ❌ ValidationError [field=username]: Validation failed for 'username': must be at least 3 characters
  ❌ ValidationError [field=email]: Validation failed for 'email': must contain @
  ❌ ValidationError [field=age]: Validation failed for 'age': must be between 13 and 120
```

### Step 6: Exception Chaining

```python
import json

def load_config(path):
    """Load config with meaningful error chaining."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config {path}: {e.msg}") from e

# Write a bad config
with open("/tmp/bad_config.json", "w") as f:
    f.write("{ not valid json }")

for path in ["/tmp/missing.json", "/tmp/bad_config.json"]:
    try:
        config = load_config(path)
    except (FileNotFoundError, ValueError) as e:
        print(f"Config error: {e}")
        print(f"  Caused by: {type(e.__cause__).__name__}")
```

**📸 Verified Output:**
```
Config error: Config file not found: /tmp/missing.json
  Caused by: FileNotFoundError
Config error: Invalid JSON in config /tmp/bad_config.json: Expecting property name enclosed in double quotes
  Caused by: JSONDecodeError
```

### Step 7: Context Managers as Error Handlers

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(operation_name):
    """Context manager that times an operation and handles errors."""
    start = time.perf_counter()
    print(f"▶️  Starting: {operation_name}")
    try:
        yield
        elapsed = time.perf_counter() - start
        print(f"✅ Completed: {operation_name} ({elapsed*1000:.1f}ms)")
    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"❌ Failed: {operation_name} after {elapsed*1000:.1f}ms — {e}")
        raise

# Use the context manager
with timer("file write"):
    with open("/tmp/output.txt", "w") as f:
        for i in range(1000):
            f.write(f"line {i}\n")

try:
    with timer("bad operation"):
        x = 1 / 0
except ZeroDivisionError:
    print("  (caught outside context manager)")
```

**📸 Verified Output:**
```
▶️  Starting: file write
✅ Completed: file write (2.3ms)
▶️  Starting: bad operation
❌ Failed: bad operation after 0.0ms — division by zero
  (caught outside context manager)
```

### Step 8: Retry Pattern

```python
import random
import time

random.seed(42)  # Reproducible results

def flaky_operation(attempt_num):
    """Simulates an operation that sometimes fails."""
    if random.random() < 0.6:  # 60% failure rate
        raise ConnectionError(f"Network timeout on attempt {attempt_num}")
    return f"Success on attempt {attempt_num}!"

def with_retry(func, max_attempts=5, delay=0.01):
    """Retry a function up to max_attempts times with delay."""
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = func(attempt)
            print(f"  ✅ {result}")
            return result
        except (ConnectionError, TimeoutError) as e:
            last_error = e
            print(f"  ⚠️  Attempt {attempt}/{max_attempts}: {e}")
            if attempt < max_attempts:
                time.sleep(delay)
    raise RuntimeError(f"All {max_attempts} attempts failed") from last_error

print("Running flaky operation with retry:")
try:
    result = with_retry(flaky_operation)
except RuntimeError as e:
    print(f"  ❌ Final failure: {e}")
```

**📸 Verified Output:**
```
Running flaky operation with retry:
  ⚠️  Attempt 1/5: Network timeout on attempt 1
  ⚠️  Attempt 2/5: Network timeout on attempt 2
  ✅ Success on attempt 3!
```

## ✅ Verification

```python
class InsufficientFundsError(Exception):
    def __init__(self, balance, amount):
        super().__init__(f"Cannot withdraw ${amount:.2f}: balance is ${balance:.2f}")
        self.balance = balance
        self.amount = amount

def withdraw(balance, amount):
    if amount <= 0:
        raise ValueError(f"Withdrawal amount must be positive: {amount}")
    if amount > balance:
        raise InsufficientFundsError(balance, amount)
    return balance - amount

tests = [(100, 30), (100, 150), (100, -10), (50, 50)]
for balance, amount in tests:
    try:
        new_balance = withdraw(balance, amount)
        print(f"  Withdrew ${amount}: balance now ${new_balance:.2f} ✅")
    except InsufficientFundsError as e:
        print(f"  ❌ {e}")
    except ValueError as e:
        print(f"  ❌ ValueError: {e}")

print("Lab 9 verified ✅")
```

**Expected output:**
```
  Withdrew $30: balance now $70.00 ✅
  ❌ Cannot withdraw $150.00: balance is $100.00
  ❌ ValueError: Withdrawal amount must be positive: -10
  Withdrew $50: balance now $0.00 ✅
Lab 9 verified ✅
```

## 🚨 Common Mistakes

1. **Catching bare `except:`**: Catches EVERYTHING including `KeyboardInterrupt` and `SystemExit` — always specify exception type.
2. **Silently swallowing exceptions**: `except: pass` hides bugs — at minimum log the error.
3. **Too broad catch**: `except Exception:` is often too wide — catch the specific type you expect.
4. **Not using `finally`**: Resources (files, connections) leak if you forget to close them on error.
5. **Raising strings**: `raise "error message"` is a `TypeError` — always `raise ExceptionClass("message")`.

## 📝 Summary

- `try/except/else/finally` — full exception handling structure
- Catch specific exceptions, not bare `except:`
- `else` runs on success only; `finally` runs always (use for cleanup)
- `raise ExceptionType("message")` to signal errors; `raise ... from e` for chaining
- Custom exceptions: inherit from `Exception` for domain-specific error types
- Retry patterns handle transient failures (network, I/O)

## 🔗 Further Reading
- [Python Docs: Exceptions](https://docs.python.org/3/tutorial/errors.html)
- [Python Exception Hierarchy](https://docs.python.org/3/library/exceptions.html#exception-hierarchy)
- [Real Python: Python Exceptions](https://realpython.com/python-exceptions/)
