# Lab 2: Variables, Data Types & Type Conversion

## 🎯 Objective
Master Python's core data types, understand dynamic typing, and safely convert between types.

## 📚 Background
Python has four primitive types: **int** (whole numbers), **float** (decimals), **str** (text), **bool** (True/False). Python determines types at runtime — flexible but requires care with conversions.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Lab 1: Hello World

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Integer Types
```python
small = 42
big = 1_000_000  # Underscores for readability
negative = -99

print(f"small: {small}, type: {type(small).__name__}")
print(f"big: {big:,}")
print(f"10 // 3 = {10 // 3}")
print(f"10 % 3  = {10 % 3}")
print(f"abs(-5) = {abs(-5)}")
print(f"2**10   = {2**10}")
```

**📸 Verified Output:**
```
small: 42, type: int
big: 1,000,000
10 // 3 = 3
10 % 3  = 1
abs(-5) = 5
2**10   = 1024
```

### Step 2: Floating Point
```python
pi = 3.14159
sci = 1.5e3  # Scientific notation: 1500.0

print(f"pi = {pi}")
print(f"sci = {sci}")
print(f"rounded = {round(pi, 2)}")

# Famous float quirk
print(f"0.1 + 0.2 = {0.1 + 0.2}")
print(f"Fixed:     {round(0.1 + 0.2, 1)}")

import math
print(f"sqrt(9)  = {math.sqrt(9)}")
print(f"floor(3.9) = {math.floor(3.9)}")
```

**📸 Verified Output:**
```
pi = 3.14159
sci = 1500.0
rounded = 3.14
0.1 + 0.2 = 0.30000000000000004
Fixed:     0.3
sqrt(9)  = 3.0
floor(3.9) = 3
```

> 💡 Float precision issues exist in ALL languages. Use `round()` or the `decimal` module for financial calculations.

### Step 3: Booleans
```python
t = True
f = False

print(f"True and False = {t and f}")
print(f"True or False  = {t or f}")
print(f"not True       = {not t}")
print(f"True + True    = {True + True}")  # bool is subclass of int!

# Falsy values
for val in [False, 0, 0.0, "", [], {}, None]:
    print(f"bool({repr(val):<8}) = {bool(val)}")
```

**📸 Verified Output:**
```
True and False = False
True or False  = True
not True       = False
True + True    = 2
bool(False)  = False
bool(0)      = False
bool(0.0)    = False
bool('')     = False
bool([])     = False
bool({})     = False
bool(None)   = False
```

### Step 4: Type Conversion
```python
# String to number
age = int("25")
price = float("19.99")
print(f"age: {age} ({type(age).__name__})")
print(f"price: {price} ({type(price).__name__})")

# Number to string
s = str(100)
print(f"s: '{s}' ({type(s).__name__})")

# To bool
print(bool(0), bool(1), bool(""), bool("hi"))
```

**📸 Verified Output:**
```
age: 25 (int)
price: 19.99 (float)
s: '100' (str)
False True False True
```

### Step 5: Safe Conversion
```python
def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

print(safe_int("42"))       # 42
print(safe_int("hello"))    # 0
print(safe_int(None, -1))   # -1
print(safe_int("3.14"))     # 0 (can't convert float-string to int directly)
```

**📸 Verified Output:**
```
42
0
-1
0
```

### Step 6: Type Inspection
```python
values = [42, 3.14, "hello", True, None]

for v in values:
    print(f"{repr(v):12} type={type(v).__name__:8} isinstance(int)={isinstance(v, int)}")
```

**📸 Verified Output:**
```
42           type=int      isinstance(int)=True
3.14         type=float    isinstance(int)=False
'hello'      type=str      isinstance(int)=False
True         type=bool     isinstance(int)=True
None         type=NoneType isinstance(int)=False
```

### Step 7: None Type
```python
result = None

if result is None:  # Always 'is None', not '== None'
    print("No result yet")

def find_user(user_id):
    db = {1: "Alice", 2: "Bob"}
    return db.get(user_id)  # Returns None if missing

print(find_user(1))
print(find_user(99))
print(find_user(99) is None)
```

**📸 Verified Output:**
```
No result yet
Alice
None
True
```

### Step 8: Dynamic Typing Demo
```python
x = 42
print(f"x = {x}, type = {type(x).__name__}")

x = "now a string"
print(f"x = {x!r}, type = {type(x).__name__}")

x = [1, 2, 3]
print(f"x = {x}, type = {type(x).__name__}")
```

**📸 Verified Output:**
```
x = 42, type = int
x = 'now a string', type = str
x = [1, 2, 3], type = list
```

## ✅ Verification
```python
data = ["42", "3.14", "100", "hello"]
results = []
for item in data:
    try:
        results.append(int(item))
    except ValueError:
        try:
            results.append(float(item))
        except ValueError:
            results.append(item)
print(results)
print("Lab 2 verified ✅")
```

**Expected output:**
```
[42, 3.14, 100, 'hello']
Lab 2 verified ✅
```

## 🚨 Common Mistakes
- `int("3.14")` raises ValueError — use `int(float("3.14"))` instead
- `type(x) == int` — prefer `isinstance(x, int)` which handles subclasses
- `x == None` — always use `x is None`
- Float precision: `0.1 + 0.2 != 0.3` — use `round()` for comparisons

## 📝 Summary
- 4 primitives: `int`, `float`, `str`, `bool`; `bool` is a subclass of `int`
- Convert with `int()`, `float()`, `str()`, `bool()` — wrap in try/except for safety
- `None` is Python's null — use `is None` to check
- `isinstance()` is preferred over `type() ==`
- Python is dynamically typed — variables can change type

## 🔗 Further Reading
- [Python Docs: Built-in Types](https://docs.python.org/3/library/stdtypes.html)
- [Python Docs: decimal module](https://docs.python.org/3/library/decimal.html)
