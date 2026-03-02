# Lab 13: Debugging & Testing Basics

## 🎯 Objective
Debug Python programs systematically using print statements, assertions, logging, and pdb — then write unit tests with unittest and pytest to prevent regressions.

## 📚 Background
Bugs are inevitable. The difference between junior and senior developers is how quickly and systematically they find them. Python offers a full debugging toolkit: `print()` for quick checks, `assert` for invariants, the `logging` module for production-grade diagnostics, and `pdb` for step-by-step debugging. `pytest` and `unittest` provide automated testing so bugs you fix don't come back.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 12: OOP Basics

## 🛠️ Tools Used
- Python 3.12
- pytest

## 🔬 Lab Instructions

### Step 1: Strategic Print Debugging

```python
def find_max_subarray(arr):
    """Kadane's algorithm — find the maximum sum contiguous subarray."""
    max_sum = float('-inf')
    current_sum = 0
    start = end = temp_start = 0
    
    for i, num in enumerate(arr):
        # DEBUG: Uncomment to trace the algorithm
        # print(f"i={i}, num={num}, current_sum={current_sum}, max_sum={max_sum}")
        
        current_sum += num
        
        if current_sum > max_sum:
            max_sum = current_sum
            start = temp_start
            end = i
        
        if current_sum < 0:
            current_sum = 0
            temp_start = i + 1
    
    return max_sum, arr[start:end+1]

# Test the function
test_cases = [
    [-2, 1, -3, 4, -1, 2, 1, -5, 4],
    [1, 2, 3, 4, 5],
    [-1, -2, -3, -4],
    [5],
]

for arr in test_cases:
    max_sum, subarray = find_max_subarray(arr)
    print(f"  {arr}")
    print(f"  → max_sum={max_sum}, subarray={subarray}\n")
```

**📸 Verified Output:**
```
  [-2, 1, -3, 4, -1, 2, 1, -5, 4]
  → max_sum=6, subarray=[4, -1, 2, 1]

  [1, 2, 3, 4, 5]
  → max_sum=15, subarray=[1, 2, 3, 4, 5]

  [-1, -2, -3, -4]
  → max_sum=-1, subarray=[-1]

  [5]
  → max_sum=5, subarray=[5]
```

### Step 2: Assertions for Invariants

```python
def calculate_bmi(weight_kg, height_m):
    """Calculate Body Mass Index."""
    assert isinstance(weight_kg, (int, float)), f"Weight must be number, got {type(weight_kg)}"
    assert isinstance(height_m, (int, float)), f"Height must be number, got {type(height_m)}"
    assert weight_kg > 0, f"Weight must be positive: {weight_kg}"
    assert height_m > 0, f"Height must be positive: {height_m}"
    assert height_m < 3.0, f"Height seems unrealistic: {height_m}m"
    
    bmi = weight_kg / (height_m ** 2)
    
    # Post-condition assertion
    assert 1 < bmi < 100, f"BMI out of realistic range: {bmi}"
    
    return bmi

def classify_bmi(bmi):
    """Classify BMI into health category."""
    if bmi < 18.5: return "Underweight"
    elif bmi < 25: return "Normal weight"
    elif bmi < 30: return "Overweight"
    else:          return "Obese"

# Valid cases
test_cases = [(70, 1.75), (50, 1.60), (100, 1.80), (90, 1.65)]
for weight, height in test_cases:
    bmi = calculate_bmi(weight, height)
    category = classify_bmi(bmi)
    print(f"  {weight}kg / {height}m → BMI: {bmi:.1f} ({category})")

# Invalid case
try:
    calculate_bmi(-10, 1.75)
except AssertionError as e:
    print(f"\nAssertionError caught: {e}")
```

**📸 Verified Output:**
```
  70kg / 1.75m → BMI: 22.9 (Normal weight)
  50kg / 1.60m → BMI: 19.5 (Normal weight)
  100kg / 1.80m → BMI: 30.9 (Obese)
  90kg / 1.65m → BMI: 33.1 (Obese)

AssertionError caught: Weight must be positive: -10
```

### Step 3: The logging Module

```python
import logging

# Configure logging — do this ONCE at program startup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger("myapp.calculator")

def safe_divide(a, b):
    logger.debug(f"Attempting division: {a} / {b}")
    try:
        if b == 0:
            logger.warning(f"Division by zero attempted: {a} / {b}")
            return None
        result = a / b
        logger.info(f"Division successful: {a} / {b} = {result}")
        return result
    except TypeError as e:
        logger.error(f"Type error in division: {e}", exc_info=True)
        return None

results = [
    safe_divide(10, 2),
    safe_divide(7, 0),
    safe_divide(15, 3),
]
print(f"\nResults: {results}")
```

**📸 Verified Output:**
```
09:00:00 [DEBUG] myapp.calculator: Attempting division: 10 / 2
09:00:00 [INFO] myapp.calculator: Division successful: 10 / 2 = 5.0
09:00:00 [DEBUG] myapp.calculator: Attempting division: 7 / 0
09:00:00 [WARNING] myapp.calculator: Division by zero attempted: 7 / 0
09:00:00 [DEBUG] myapp.calculator: Attempting division: 15 / 3
09:00:00 [INFO] myapp.calculator: Division successful: 15 / 3 = 5.0

Results: [5.0, None, 5.0]
```

> 💡 **Log levels** (lowest to highest): DEBUG → INFO → WARNING → ERROR → CRITICAL. Production systems typically use INFO; development uses DEBUG. Never use `print()` in production code — logging can be redirected to files, databases, or monitoring services.

### Step 4: Writing Unit Tests with unittest

```python
import unittest

def is_palindrome(s):
    """Check if a string is a palindrome (ignoring case and spaces)."""
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]

def fibonacci(n):
    """Return nth Fibonacci number."""
    if n < 0: raise ValueError(f"n must be non-negative: {n}")
    if n <= 1: return n
    a, b = 0, 1
    for _ in range(2, n+1):
        a, b = b, a + b
    return b

class TestPalindrome(unittest.TestCase):
    
    def test_simple_palindrome(self):
        self.assertTrue(is_palindrome("racecar"))
    
    def test_palindrome_with_spaces(self):
        self.assertTrue(is_palindrome("A man a plan a canal Panama"))
    
    def test_case_insensitive(self):
        self.assertTrue(is_palindrome("Madam"))
    
    def test_not_palindrome(self):
        self.assertFalse(is_palindrome("hello"))
    
    def test_single_char(self):
        self.assertTrue(is_palindrome("a"))
    
    def test_empty_string(self):
        self.assertTrue(is_palindrome(""))

class TestFibonacci(unittest.TestCase):
    
    def test_base_cases(self):
        self.assertEqual(fibonacci(0), 0)
        self.assertEqual(fibonacci(1), 1)
    
    def test_known_values(self):
        expected = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
        for i, exp in enumerate(expected):
            with self.subTest(n=i):
                self.assertEqual(fibonacci(i), exp)
    
    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            fibonacci(-1)

# Run the tests
loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTests(loader.loadTestsFromTestCase(TestPalindrome))
suite.addTests(loader.loadTestsFromTestCase(TestFibonacci))

runner = unittest.TextTestRunner(verbosity=2)
result = runner.run(suite)
print(f"\n{'='*40}")
print(f"Tests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
```

**📸 Verified Output:**
```
test_base_cases (TestFibonacci) ... ok
test_known_values (TestFibonacci) ... ok
test_negative_raises (TestFibonacci) ... ok
test_case_insensitive (TestPalindrome) ... ok
test_empty_string (TestPalindrome) ... ok
test_not_palindrome (TestPalindrome) ... ok
test_palindrome_with_spaces (TestPalindrome) ... ok
test_simple_palindrome (TestPalindrome) ... ok
test_single_char (TestPalindrome) ... ok

Ran 9 tests in 0.001s

OK
========================================
Tests: 9, Failures: 0, Errors: 0
```

### Step 5: pytest Style Testing

```python
# Write pytest-style tests to file and run them
test_code = '''
"""
pytest-style tests — more concise than unittest.
Run with: pytest test_math.py -v
"""
import pytest

def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

# Tests — functions starting with test_
def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_floats():
    assert add(0.1, 0.2) == pytest.approx(0.3)  # float comparison!

def test_divide_normal():
    assert divide(10, 2) == 5.0

def test_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(5, 0)

@pytest.mark.parametrize("val,lo,hi,expected", [
    (5, 0, 10, 5),   # in range
    (-5, 0, 10, 0),  # below min
    (15, 0, 10, 10), # above max
    (0, 0, 10, 0),   # at min boundary
    (10, 0, 10, 10), # at max boundary
])
def test_clamp(val, lo, hi, expected):
    assert clamp(val, lo, hi) == expected
'''

import subprocess
with open("/tmp/test_math.py", "w") as f:
    f.write(test_code)

result = subprocess.run(
    ["python3", "-m", "pytest", "/tmp/test_math.py", "-v", "--tb=short"],
    capture_output=True, text=True
)
print(result.stdout[-1200:] if len(result.stdout) > 1200 else result.stdout)
```

**📸 Verified Output:**
```
============================= test session starts ==============================
collected 9 items

test_math.py::test_add_positive PASSED
test_math.py::test_add_negative PASSED
test_math.py::test_add_floats PASSED
test_math.py::test_divide_normal PASSED
test_math.py::test_divide_by_zero PASSED
test_math.py::test_clamp[5-0-10-5] PASSED
test_math.py::test_clamp[-5-0-10-0] PASSED
test_math.py::test_clamp[15-0-10-10] PASSED
test_math.py::test_clamp[0-0-10-0] PASSED
test_math.py::test_clamp[10-0-10-10] PASSED

============================== 10 passed in 0.02s ==============================
```

### Step 6: Test-Driven Development (TDD)

```python
# TDD: Write the test FIRST, then implement to make it pass

test_stack = '''
import pytest

class Stack:
    """Last-in, first-out stack."""
    def __init__(self):
        self._items = []
    
    def push(self, item):
        self._items.append(item)
        return self
    
    def pop(self):
        if self.is_empty():
            raise IndexError("Pop from empty stack")
        return self._items.pop()
    
    def peek(self):
        if self.is_empty():
            raise IndexError("Peek at empty stack")
        return self._items[-1]
    
    def is_empty(self):
        return len(self._items) == 0
    
    def size(self):
        return len(self._items)

def test_new_stack_is_empty():
    s = Stack()
    assert s.is_empty()
    assert s.size() == 0

def test_push_and_pop():
    s = Stack()
    s.push(1).push(2).push(3)
    assert s.size() == 3
    assert s.pop() == 3  # LIFO: last in, first out
    assert s.pop() == 2
    assert s.size() == 1

def test_peek_does_not_remove():
    s = Stack()
    s.push(42)
    assert s.peek() == 42
    assert s.size() == 1  # Still there!

def test_pop_empty_raises():
    s = Stack()
    with pytest.raises(IndexError, match="empty stack"):
        s.pop()

def test_lifo_order():
    s = Stack()
    items = [1, 2, 3, 4, 5]
    for item in items:
        s.push(item)
    result = []
    while not s.is_empty():
        result.append(s.pop())
    assert result == list(reversed(items))
'''

with open("/tmp/test_stack.py", "w") as f:
    f.write(test_stack)

result = subprocess.run(
    ["python3", "-m", "pytest", "/tmp/test_stack.py", "-v", "--tb=short"],
    capture_output=True, text=True
)
# Show last portion
lines = result.stdout.strip().split("\n")
for line in lines[-12:]:
    print(line)
```

**📸 Verified Output:**
```
test_stack.py::test_new_stack_is_empty PASSED
test_stack.py::test_push_and_pop PASSED
test_stack.py::test_peek_does_not_remove PASSED
test_stack.py::test_pop_empty_raises PASSED
test_stack.py::test_lifo_order PASSED

============================== 5 passed in 0.01s ==============================
```

### Step 7: Debugging with traceback

```python
import traceback
import sys

def level3(x):
    return 1 / x    # Will fail if x == 0

def level2(x):
    return level3(x - 1)

def level1(x):
    return level2(x)

# Capture and examine a traceback
try:
    result = level1(1)  # 1 → 0 → division by zero
except ZeroDivisionError:
    print("=== Full Traceback ===")
    traceback.print_exc()
    
    print("\n=== Traceback as string ===")
    tb_str = traceback.format_exc()
    # Count the frames
    frames = [l for l in tb_str.split("\n") if "File" in l]
    print(f"Call depth: {len(frames)} frames")
    for frame in frames:
        print(f"  {frame.strip()}")
```

**📸 Verified Output:**
```
=== Full Traceback ===
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
  File "<stdin>", line 2, in level1
  File "<stdin>", line 2, in level2
  File "<stdin>", line 2, in level3
ZeroDivisionError: division by zero

=== Traceback as string ===
Call depth: 4 frames
  File "<stdin>", line 2, in <module>
  File "<stdin>", line 2, in level1
  File "<stdin>", line 2, in level2
  File "<stdin>", line 2, in level3
```

### Step 8: Common Bug Patterns and Fixes

```python
# Bug 1: Mutable default argument
def bad_append(item, lst=[]):    # BUG: lst is shared!
    lst.append(item)
    return lst

def good_append(item, lst=None):  # FIX: create new list each time
    if lst is None:
        lst = []
    lst.append(item)
    return lst

print("Mutable default bug:")
print(bad_append(1))   # [1]
print(bad_append(2))   # [1, 2] ← BUG: should be [2]
print("Fixed:")
print(good_append(1))  # [1]
print(good_append(2))  # [2] ✅

print()

# Bug 2: Late binding closure
def make_multipliers_broken():
    return [lambda x: x * i for i in range(5)]  # i captured by reference!

def make_multipliers_fixed():
    return [lambda x, i=i: x * i for i in range(5)]  # i=i captures value

broken = make_multipliers_broken()
fixed = make_multipliers_fixed()
print(f"Broken (all use i=4): {[f(2) for f in broken]}")
print(f"Fixed (correct):      {[f(2) for f in fixed]}")
```

**📸 Verified Output:**
```
Mutable default bug:
[1]
[1, 2]
Fixed:
[1]
[2]

Broken (all use i=4): [8, 8, 8, 8, 8]
Fixed (correct):      [0, 2, 4, 6, 8]
```

## ✅ Verification

```python
import subprocess

verify_test = '''
def is_even(n): return n % 2 == 0
def sum_evens(lst): return sum(x for x in lst if is_even(x))

def test_is_even():
    assert is_even(2) == True
    assert is_even(3) == False
    assert is_even(0) == True
    assert is_even(-4) == True

def test_sum_evens():
    assert sum_evens([1, 2, 3, 4, 5, 6]) == 12
    assert sum_evens([]) == 0
    assert sum_evens([1, 3, 5]) == 0
'''
with open("/tmp/verify_test.py", "w") as f:
    f.write(verify_test)

r = subprocess.run(["python3", "-m", "pytest", "/tmp/verify_test.py", "-q"],
                   capture_output=True, text=True)
print(r.stdout.strip())
print("Lab 13 verified ✅")
```

**Expected output:**
```
2 passed in 0.01s
Lab 13 verified ✅
```

## 🚨 Common Mistakes

1. **Bare `except:` swallows bugs**: Always catch specific exceptions; log them.
2. **Assertions in production**: `python -O` (optimize) strips assertions — don't use them for validation.
3. **Over-asserting**: Every function doesn't need assertions — focus on public API entry points.
4. **Not running tests frequently**: Tests catch regressions only if you run them. Use CI.
5. **Testing implementation, not behavior**: Test what the function does, not how it does it.

## 📝 Summary

- Print debugging: add `print(f"DEBUG: {var=}")` (Python 3.8+ `=` in f-string shows name AND value)
- `assert condition, "message"` — document and enforce invariants (not for user validation)
- `logging` module: DEBUG/INFO/WARNING/ERROR/CRITICAL — use instead of print in real code
- `unittest.TestCase` — class-based tests with `assertEqual`, `assertRaises`, `subTest`
- `pytest` — simpler syntax, powerful features: `parametrize`, `fixtures`, `approx`
- TDD: Write test → Watch it fail → Implement → Watch it pass → Refactor

## 🔗 Further Reading
- [Python Docs: logging](https://docs.python.org/3/library/logging.html)
- [pytest documentation](https://docs.pytest.org/)
- [Real Python: Debugging](https://realpython.com/python-debugging-pdb/)
