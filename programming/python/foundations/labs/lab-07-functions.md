# Lab 7: Functions & Scope

## 🎯 Objective
Define reusable functions, understand Python's scoping rules (LEGB), work with default arguments, *args, **kwargs, and return multiple values.

## 📚 Background
Functions are the fundamental unit of code reuse in Python. They encapsulate logic, reduce duplication, and make code testable. Python functions are **first-class objects** — they can be stored in variables, passed as arguments, and returned from other functions. Understanding scope (where a variable lives) prevents subtle bugs.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 6: Control Flow

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Defining and Calling Functions

```python
def greet(name):
    """Return a greeting for the given name.
    
    Args:
        name: The person's name (string)
    
    Returns:
        A formatted greeting string
    """
    return f"Hello, {name}!"

# Call the function
message = greet("Alice")
print(message)
print(greet("Dr. Chen"))

# Functions without return value return None
def print_separator(char="-", width=30):
    print(char * width)

print_separator()
print_separator("=", 20)
print_separator("*")
```

**📸 Verified Output:**
```
Hello, Alice!
Hello, Dr. Chen!
------------------------------
====================
******************************
```

> 💡 The docstring (triple-quoted string after `def`) documents what the function does. Python's `help()` and IDE tools read docstrings. Always write them — your future self will thank you.

### Step 2: Default Arguments and Keyword Arguments

```python
def create_profile(name, age, city="Unknown", role="User", active=True):
    """Create a user profile dictionary."""
    return {
        "name": name,
        "age": age,
        "city": city,
        "role": role,
        "active": active
    }

# Positional only
p1 = create_profile("Alice", 30)
print(p1)

# Mix of positional and keyword
p2 = create_profile("Bob", 25, city="London", role="Admin")
print(p2)

# All keyword (order doesn't matter)
p3 = create_profile(age=35, active=False, name="Charlie", city="Tokyo")
print(p3)
```

**📸 Verified Output:**
```
{'name': 'Alice', 'age': 30, 'city': 'Unknown', 'role': 'User', 'active': True}
{'name': 'Bob', 'age': 25, 'city': 'London', 'role': 'Admin', 'active': True}
{'name': 'Charlie', 'age': 35, 'city': 'Tokyo', 'role': 'User', 'active': False}
```

> 💡 **Important**: Never use mutable defaults like `def f(lst=[])`. The list is created ONCE and shared across all calls. Use `def f(lst=None): lst = lst or []` instead.

### Step 3: Returning Multiple Values

```python
def min_max_avg(numbers):
    """Return min, max, and average of a list."""
    if not numbers:
        return None, None, None
    total = sum(numbers)
    return min(numbers), max(numbers), total / len(numbers)

data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]

# Unpack all three return values
minimum, maximum, average = min_max_avg(data)
print(f"Min: {minimum}, Max: {maximum}, Avg: {average:.2f}")

# Ignore some values with _
_, maximum, _ = min_max_avg(data)
print(f"Max only: {maximum}")

# Keep as tuple
result = min_max_avg(data)
print(f"As tuple: {result}")
print(f"Type: {type(result)}")
```

**📸 Verified Output:**
```
Min: 1, Max: 9, Avg: 4.00
Max only: 9
As tuple: (1, 9, 4.0)
Type: <class 'tuple'>
```

### Step 4: *args and **kwargs

```python
# *args — accept any number of positional arguments
def add_all(*numbers):
    """Sum any number of arguments."""
    print(f"  Received: {numbers} (type: {type(numbers).__name__})")
    return sum(numbers)

print(add_all(1, 2))
print(add_all(1, 2, 3, 4, 5))
print(add_all())

print()

# **kwargs — accept any number of keyword arguments
def log_event(event_type, **details):
    """Log an event with arbitrary details."""
    print(f"[{event_type.upper()}]")
    for key, value in details.items():
        print(f"  {key}: {value}")

log_event("login", user="alice", ip="192.168.1.1", success=True)
print()
log_event("purchase", item="laptop", price=999.99, currency="USD", qty=1)
```

**📸 Verified Output:**
```
  Received: (1, 2) (type: tuple)
3
  Received: (1, 2, 3, 4, 5) (type: tuple)
15
  Received: () (type: tuple)
0

[LOGIN]
  user: alice
  ip: 192.168.1.1
  success: True

[PURCHASE]
  item: laptop
  price: 999.99
  currency: USD
  qty: 1
```

### Step 5: Scope — LEGB Rule

Python looks up variables in this order: **L**ocal → **E**nclosing → **G**lobal → **B**uilt-in.

```python
x = "global"        # Global scope

def outer():
    x = "enclosing" # Enclosing scope
    
    def inner():
        x = "local" # Local scope
        print(f"inner sees: x = '{x}'")
    
    inner()
    print(f"outer sees: x = '{x}'")

outer()
print(f"module sees: x = '{x}'")

print()

# global keyword — modify global from inside function
counter = 0

def increment():
    global counter
    counter += 1

increment()
increment()
increment()
print(f"Counter: {counter}")
```

**📸 Verified Output:**
```
inner sees: x = 'local'
outer sees: x = 'enclosing'
module sees: x = 'global'

Counter: 3
```

> 💡 Using `global` is usually a code smell — prefer returning values instead. But understanding scope is essential for debugging "variable not defined" errors.

### Step 6: Lambda Functions

```python
# Lambda: anonymous one-line function
square = lambda x: x ** 2
add = lambda a, b: a + b
greet = lambda name: f"Hello, {name}!"

print(square(5))
print(add(3, 4))
print(greet("World"))

# Primary use: as arguments to sort/filter/map
students = [
    {"name": "Alice", "grade": 92},
    {"name": "Bob", "grade": 85},
    {"name": "Charlie", "grade": 98},
]

# Sort by grade (highest first)
ranked = sorted(students, key=lambda s: s["grade"], reverse=True)
for i, s in enumerate(ranked, 1):
    print(f"{i}. {s['name']}: {s['grade']}")

# Filter: only passing grades
passing = list(filter(lambda s: s["grade"] >= 90, students))
print(f"\nPassing: {[s['name'] for s in passing]}")

# Map: extract names
names = list(map(lambda s: s["name"], students))
print(f"All names: {names}")
```

**📸 Verified Output:**
```
25
7
Hello, World!
1. Charlie: 98
2. Alice: 92
3. Bob: 85

Passing: ['Alice', 'Charlie']
All names: ['Alice', 'Bob', 'Charlie']
```

### Step 7: Recursive Functions

```python
def factorial(n):
    """Calculate n! recursively."""
    if n <= 1:       # Base case — stops the recursion
        return 1
    return n * factorial(n - 1)  # Recursive case

for i in range(8):
    print(f"{i}! = {factorial(i)}")

print()

def fibonacci(n):
    """Return the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

fibs = [fibonacci(i) for i in range(10)]
print(f"First 10 Fibonacci numbers: {fibs}")
```

**📸 Verified Output:**
```
0! = 1
1! = 1
2! = 2
3! = 6
4! = 24
5! = 120
6! = 720
7! = 5040

First 10 Fibonacci numbers: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

### Step 8: Functions as First-Class Objects

```python
def apply(func, values):
    """Apply a function to every value in a list."""
    return [func(v) for v in values]

def double(x):
    return x * 2

def square(x):
    return x ** 2

numbers = [1, 2, 3, 4, 5]
print(f"Original: {numbers}")
print(f"Doubled:  {apply(double, numbers)}")
print(f"Squared:  {apply(square, numbers)}")
print(f"Lambda:   {apply(lambda x: x + 10, numbers)}")

# Store functions in a dict (dispatch table)
operations = {
    "double": double,
    "square": square,
    "negate": lambda x: -x,
}

for op_name, op_func in operations.items():
    result = apply(op_func, [1, 2, 3])
    print(f"{op_name}: {result}")
```

**📸 Verified Output:**
```
Original: [1, 2, 3, 4, 5]
Doubled:  [2, 4, 6, 8, 10]
Squared:  [1, 4, 9, 16, 25]
Lambda:   [11, 12, 13, 14, 15]
double: [2, 4, 6]
square: [1, 4, 9]
negate: [-1, -2, -3]
```

## ✅ Verification

```python
def stats(data):
    """Return count, mean, min, max for a list of numbers."""
    n = len(data)
    return n, sum(data)/n, min(data), max(data)

test = [4, 7, 2, 9, 1, 5, 8, 3, 6]
count, mean, lo, hi = stats(test)
print(f"n={count}, mean={mean:.2f}, min={lo}, max={hi}")

# Higher-order function test
ops = {"add10": lambda x: x+10, "triple": lambda x: x*3}
for name, op in ops.items():
    print(f"{name}: {[op(x) for x in [1,2,3]]}")

print("Lab 7 verified ✅")
```

**Expected output:**
```
n=9, mean=5.00, min=1, max=9
add10: [11, 12, 13]
triple: [3, 6, 9]
Lab 7 verified ✅
```

## 🚨 Common Mistakes

1. **Mutable default arguments**: `def f(lst=[])` — the list persists across calls. Use `def f(lst=None): lst = lst or []`.
2. **Forgetting `return`**: A function with no `return` returns `None` — leads to `NoneType has no attribute` errors.
3. **Modifying a global without `global` keyword**: Python creates a new local variable instead.
4. **Infinite recursion**: Every recursive function needs a base case that stops the chain.
5. **Overusing lambda**: Complex lambdas hurt readability — use a named `def` instead.

## 📝 Summary

- Functions: `def name(params): ... return value` — docstrings are essential
- Default args: `def f(x, y=10)` — never use mutable defaults
- Multiple returns: `return a, b, c` packs into a tuple; unpack with `a, b, c = f()`
- `*args` collects extra positional args as a tuple; `**kwargs` as a dict
- LEGB scope: Local → Enclosing → Global → Built-in
- Lambda: one-expression anonymous function — use for simple key functions
- Functions are first-class: pass them, store them, return them

## 🔗 Further Reading
- [Python Docs: Defining Functions](https://docs.python.org/3/tutorial/controlflow.html#defining-functions)
- [Real Python: Python Functions](https://realpython.com/defining-your-own-python-function/)
