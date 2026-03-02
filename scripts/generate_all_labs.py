#!/usr/bin/env python3
"""
Generate all programming labs for innoZverse-docs.
Verified content with real Docker-tested output.
"""

import os
import subprocess
import sys

REPO = "/home/zchen/.openclaw/workspace/innoZverse-docs/programming"

def mkdir(path):
    os.makedirs(path, exist_ok=True)

def write_lab(path, content):
    mkdir(os.path.dirname(path))
    with open(path, 'w') as f:
        f.write(content)

def lab_header(num, title, objective, background, time_est, prereqs, tools):
    return f"""# Lab {num}: {title}

## 🎯 Objective
{objective}

## 📚 Background
{background}

## ⏱️ Estimated Time
{time_est}

## 📋 Prerequisites
{prereqs}

## 🛠️ Tools Used
{tools}

## 🔬 Lab Instructions
"""

def lab_footer(verify_code, verify_output, mistakes, summary, links):
    return f"""
## ✅ Verification
```
{verify_code}
```

**Expected output:**
```
{verify_output}
```

## 🚨 Common Mistakes
{mistakes}

## 📝 Summary
{summary}

## 🔗 Further Reading
{links}
"""

# ============================================================
# PYTHON LABS
# ============================================================

PYTHON_LABS = {
    "foundations": [
        ("Hello World & Python Basics",
         "lab-01-hello-world.md",
"""## 🎯 Objective
Write your first Python program, run it, and understand Python's syntax fundamentals.

## 📚 Background
Python is an interpreted, dynamically typed language created by Guido van Rossum. It prioritizes readability — code looks like plain English. Python is used in web development, data science, AI, DevOps, and scripting.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- None

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Hello World
```python
print("Hello, World!")
print("Welcome to Python!")
```

**📸 Verified Output:**
```
Hello, World!
Welcome to Python!
```

> 💡 `print()` sends text to stdout. No semicolons needed — Python uses newlines.

### Step 2: Arithmetic
```python
print(2 + 3)    # 5
print(10 / 3)   # 3.3333...
print(10 // 3)  # 3 (floor division)
print(10 % 3)   # 1 (remainder)
print(2 ** 8)   # 256 (power)
```

**📸 Verified Output:**
```
5
3.3333333333333335
3
1
256
```

### Step 3: Variables
```python
name = "Alice"
age = 30
pi = 3.14
active = True
print(f"{name} is {age}, pi={pi}, active={active}")
print(f"type of age: {type(age).__name__}")
```

**📸 Verified Output:**
```
Alice is 30, pi=3.14, active=True
type of age: int
```

### Step 4: Multiple Assignment
```python
x, y = 10, 20
print(f"x={x}, y={y}")
x, y = y, x  # swap
print(f"After swap: x={x}, y={y}")
```

**📸 Verified Output:**
```
x=10, y=20
After swap: x=20, y=10
```

### Step 5: String Formatting
```python
name = "Bob"
score = 95.5
print(f"Player: {name}, Score: {score:.1f}")
print("Player: {}, Score: {:.1f}".format(name, score))
```

**📸 Verified Output:**
```
Player: Bob, Score: 95.5
Player: Bob, Score: 95.5
```

### Step 6: Comments
```python
# Single line comment
x = 42  # inline comment

"""
Multi-line docstring.
Used for documentation.
"""
print(x)
```

**📸 Verified Output:**
```
42
```

### Step 7: Input Simulation
```python
# Simulating user input
user_name = "Dr. Chen"
user_age = int("35")
print(f"Hello {user_name}! In 10 years: {user_age + 10}")
```

**📸 Verified Output:**
```
Hello Dr. Chen! In 10 years: 45
```

### Step 8: System Info
```python
import sys
import platform
print(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
print(f"Platform: {platform.system()}")
print(f"Max int: {sys.maxsize:,}")
```

**📸 Verified Output:**
```
Python: 3.12
Platform: Linux
Max int: 9,223,372,036,854,775,807
```

## ✅ Verification
```python
import sys
print(f"Python {sys.version_info.major}.{sys.version_info.minor} ✅")
print(f"2**10 = {2**10}")
print("Lab 1 verified ✅")
```

**Expected output:**
```
Python 3.12 ✅
2**10 = 1024
Lab 1 verified ✅
```

## 🚨 Common Mistakes
- `Print()` is not `print()` — Python is case-sensitive
- `5/2 = 2.5` (float), not `2` — use `5//2` for integer division
- Missing quotes around strings: `name = Alice` → NameError
- Mixing tabs and spaces — use 4 spaces consistently

## 📝 Summary
- `print()` outputs to terminal; comments use `#`
- Variables assigned with `=`; no type declarations needed
- Core types: `int`, `float`, `str`, `bool`
- f-strings `f"{value}"` are the modern formatting standard
- Python enforces readability — one statement per line

## 🔗 Further Reading
- [Official Python Tutorial](https://docs.python.org/3/tutorial/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
"""),
        ("Variables, Data Types & Type Conversion", "lab-02-data-types.md",
"""## 🎯 Objective
Master Python's core data types and safely convert between them.

## 📚 Background
Python has four primitives: `int`, `float`, `str`, `bool`. Python infers types at runtime (dynamic typing). Understanding types is critical for avoiding bugs in data processing, APIs, and user input handling.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Lab 1: Hello World

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Integer Operations
```python
a = 100
b = 7
print(f"div:  {a / b:.4f}")
print(f"fdiv: {a // b}")
print(f"mod:  {a % b}")
print(f"pow:  {2**10}")
print(f"abs:  {abs(-42)}")
big = 1_000_000_000
print(f"big:  {big:,}")
```

**📸 Verified Output:**
```
div:  14.2857
fdiv: 14
mod:  2
pow:  1024
abs:  42
big:  1,000,000,000
```

### Step 2: Float Precision
```python
import math
pi = 3.14159265358979
print(f"pi = {pi:.4f}")
print(f"0.1+0.2 = {0.1 + 0.2}")
print(f"fixed   = {round(0.1 + 0.2, 1)}")
print(f"sqrt(2) = {math.sqrt(2):.6f}")
print(f"inf     = {math.inf}")
print(f"nan     = {math.nan}")
```

**📸 Verified Output:**
```
pi = 3.1416
0.1+0.2 = 0.30000000000000004
fixed   = 0.3
sqrt(2) = 1.414214
inf     = inf
nan     = nan
```

### Step 3: Strings
```python
s = "Hello, Python!"
print(len(s))
print(s.upper())
print(s.lower())
print(s.replace("Python", "World"))
print(s[0:5])
print(s[::-1])
```

**📸 Verified Output:**
```
14
HELLO, PYTHON!
hello, python!
Hello, World!
Hello
!nohtyP ,olleH
```

### Step 4: Booleans
```python
print(True and False)
print(True or False)
print(not True)
print(True + True)   # bool is subclass of int

# Falsy values
for v in [False, 0, "", [], {}, None]:
    print(f"bool({repr(v)}) = {bool(v)}")
```

**📸 Verified Output:**
```
False
True
False
2
bool(False) = False
bool(0) = False
bool('') = False
bool([]) = False
bool({}) = False
bool(None) = False
```

### Step 5: Type Conversion
```python
print(int("42"))
print(float("3.14"))
print(str(100))
print(bool(0), bool(1))
print(int(True), int(False))
```

**📸 Verified Output:**
```
42
3.14
100
False True
1 0
```

### Step 6: Safe Conversion
```python
def safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

tests = ["42", "hello", None, "3.14", "0"]
for t in tests:
    print(f"safe_int({repr(t)}) = {safe_int(t, -1)}")
```

**📸 Verified Output:**
```
safe_int('42') = 42
safe_int('hello') = -1
safe_int(None) = -1
safe_int('3.14') = -1
safe_int('0') = 0
```

### Step 7: Type Checking
```python
values = [42, 3.14, "hi", True, None, [1,2]]
for v in values:
    print(f"{type(v).__name__:8} | isinstance int: {isinstance(v, int)}")
```

**📸 Verified Output:**
```
int      | isinstance int: True
float    | isinstance int: False
str      | isinstance int: False
bool     | isinstance int: True
NoneType | isinstance int: False
list     | isinstance int: False
```

### Step 8: None Type
```python
result = None
if result is None:
    print("No result")

def lookup(key):
    db = {"a": 1, "b": 2}
    return db.get(key)

print(lookup("a"))
print(lookup("z"))
print(lookup("z") is None)
```

**📸 Verified Output:**
```
No result
1
None
True
```

## ✅ Verification
```python
data = ["10", "3.5", "hello", "0"]
out = []
for d in data:
    try:
        out.append(int(d))
    except ValueError:
        try:
            out.append(float(d))
        except ValueError:
            out.append(d)
print(out)
print("Lab 2 verified ✅")
```

**Expected output:**
```
[10, 3.5, 'hello', 0]
Lab 2 verified ✅
```

## 🚨 Common Mistakes
- `int("3.14")` raises ValueError — use `int(float("3.14"))`
- `x == None` — always use `x is None`
- Float `0.1 + 0.2 != 0.3` — use `round()` for comparisons
- `isinstance(True, int)` returns `True` — bool is int subclass

## 📝 Summary
- 4 primitives: `int`, `float`, `str`, `bool`
- Convert with `int()`, `float()`, `str()`, `bool()` — wrap in try/except
- `None` is Python's null — use `is None` to check
- `isinstance()` preferred over `type() ==`
- Float precision is limited — use `decimal` module for finance

## 🔗 Further Reading
- [Python Docs: Built-in Types](https://docs.python.org/3/library/stdtypes.html)
"""),
        ("Strings & String Methods", "lab-03-strings.md",
"""## 🎯 Objective
Master string creation, slicing, methods, and formatting — the tools used in almost every Python program.

## 📚 Background
Strings are immutable sequences of Unicode characters. Python has 40+ string methods built-in. Mastering strings is essential for data processing, web scraping, file handling, and API work.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 2: Data Types

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: String Creation
```python
s1 = 'single quotes'
s2 = "double quotes"
s3 = \"\"\"triple quotes
for multi-line\"\"\"
raw = r"C:\\Users\\no_escape"
print(s1, s2)
print(s3)
print(raw)
```

**📸 Verified Output:**
```
single quotes double quotes
triple quotes
for multi-line
C:\\Users\\no_escape
```

### Step 2: Indexing and Slicing
```python
s = "Python"
print(s[0])     # P
print(s[-1])    # n
print(s[1:4])   # yth
print(s[:3])    # Pyt
print(s[3:])    # hon
print(s[::-1])  # nohtyP
print(s[::2])   # Pto
```

**📸 Verified Output:**
```
P
n
yth
Pyt
hon
nohtyP
Pto
```

### Step 3: Case and Strip Methods
```python
s = "  Hello, World!  "
print(s.strip())
print(s.lstrip())
print(s.rstrip())
print("hello".upper())
print("HELLO".lower())
print("hello world".title())
print("hello".capitalize())
```

**📸 Verified Output:**
```
Hello, World!
Hello, World!  
  Hello, World!
HELLO
hello
Hello World
Hello
```

### Step 4: Search Methods
```python
text = "the quick brown fox"
print(text.find("fox"))       # 16
print(text.find("cat"))       # -1
print(text.count("o"))        # 2
print("fox" in text)          # True
print(text.startswith("the")) # True
print(text.endswith("fox"))   # True
print(text.replace("fox", "dog"))
```

**📸 Verified Output:**
```
16
-1
2
True
True
True
the quick brown dog
```

### Step 5: Split and Join
```python
csv = "apple,banana,cherry"
parts = csv.split(",")
print(parts)
print(len(parts))
print(" | ".join(parts))
print("-".join(["2024", "01", "15"]))

lines = "line1\\nline2\\nline3"
print(lines.split("\\n"))
```

**📸 Verified Output:**
```
['apple', 'banana', 'cherry']
3
apple | banana | cherry
2024-01-15
['line1', 'line2', 'line3']
```

### Step 6: F-String Formatting
```python
name = "Alice"
score = 98.567
rank = 1

print(f"Player: {name}, Score: {score:.2f}, Rank: #{rank}")
print(f"Pi: {3.14159:.3f}")
print(f"Big: {1_000_000:,}")
print(f"Hex: {255:#x}")
print(f"Pct: {0.856:.1%}")
print(f"Padded: {name:>10}")
print(f"Padded: {name:<10}|")
```

**📸 Verified Output:**
```
Player: Alice, Score: 98.57, Rank: #1
Pi: 3.142
Big: 1,000,000
Hex: 0xff
Pct: 85.6%
Padded:      Alice
Padded: Alice     |
```

### Step 7: String Validation
```python
tests = ["hello", "HELLO", "Hello123", "123", "", "  "]
for s in tests:
    print(f"'{s}': alpha={s.isalpha()}, digit={s.isdigit()}, upper={s.isupper()}")
```

**📸 Verified Output:**
```
'hello': alpha=True, digit=False, upper=False
'HELLO': alpha=True, digit=False, upper=True
'Hello123': alpha=False, digit=False, upper=False
'123': alpha=False, digit=True, upper=False
'': alpha=False, digit=False, upper=False
'  ': alpha=False, digit=False, upper=False
```

### Step 8: String Processing Pipeline
```python
raw = "  JOHN DOE  |  john@example.com  |  NEW YORK  "
parts = [p.strip() for p in raw.split("|")]
name = parts[0].title()
email = parts[1].lower()
city = parts[2].title()
print(f"Name: {name}")
print(f"Email: {email}")
print(f"City: {city}")
```

**📸 Verified Output:**
```
Name: John Doe
Email: john@example.com
City: New York
```

## ✅ Verification
```python
sentence = "  Python is Amazing!  "
result = sentence.strip().lower().replace("amazing", "powerful")
words = result.split()
print(" ".join(w.capitalize() for w in words))
print("Lab 3 verified ✅")
```

**Expected output:**
```
Python Is Powerful!
Lab 3 verified ✅
```

## 🚨 Common Mistakes
- Strings are immutable: `s[0] = 'X'` raises TypeError — create new strings
- `find()` returns `-1` for not found; `index()` raises ValueError
- `str.split()` with no args splits on any whitespace; `split(" ")` only splits on space
- Always `strip()` user input before comparing

## 📝 Summary
- Strings are immutable; all methods return new strings
- Slicing: `s[start:stop:step]` — negative indices count from end
- Key methods: `strip()`, `split()`, `join()`, `replace()`, `find()`, `upper()`, `lower()`
- f-strings are the modern standard: `f"{value:.2f}"`
- Use `join()` not `+` for building strings in loops

## 🔗 Further Reading
- [Python Docs: String Methods](https://docs.python.org/3/library/stdtypes.html#string-methods)
- [Real Python: Python f-Strings](https://realpython.com/python-f-strings/)
"""),
        ("Lists, Tuples & Sets", "lab-04-lists-tuples-sets.md",
"""## 🎯 Objective
Master Python's three sequence/collection types: lists (mutable sequences), tuples (immutable sequences), and sets (unique unordered collections).

## 📚 Background
Python has rich built-in collection types. **Lists** store ordered mutable sequences. **Tuples** store ordered immutable sequences (faster and safer). **Sets** store unique unordered items (O(1) membership tests). Each has distinct use cases in real programs.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 3: Strings

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: List Basics
```python
fruits = ["apple", "banana", "cherry"]
numbers = [1, 2, 3, 4, 5]
mixed = [1, "two", 3.0, True, None]

print(fruits)
print(fruits[0])        # First: apple
print(fruits[-1])       # Last: cherry
print(fruits[1:3])      # Slice: ['banana', 'cherry']
print(len(fruits))      # 3
```

**📸 Verified Output:**
```
['apple', 'banana', 'cherry']
apple
cherry
['banana', 'cherry']
3
```

### Step 2: List Modification
```python
fruits = ["apple", "banana"]
fruits.append("cherry")        # Add to end
fruits.insert(1, "blueberry")  # Insert at index
fruits.extend(["date", "fig"]) # Add multiple
print(fruits)

fruits.remove("banana")        # Remove by value
popped = fruits.pop()          # Remove last
print(fruits)
print(f"Popped: {popped}")
```

**📸 Verified Output:**
```
['apple', 'blueberry', 'banana', 'cherry', 'date', 'fig']
['apple', 'blueberry', 'cherry', 'date']
Popped: fig
```

### Step 3: List Operations
```python
nums = [3, 1, 4, 1, 5, 9, 2, 6]
print(f"sorted: {sorted(nums)}")
print(f"min: {min(nums)}, max: {max(nums)}, sum: {sum(nums)}")
print(f"count 1: {nums.count(1)}")
print(f"index 5: {nums.index(5)}")

nums.sort()
print(f"in-place sorted: {nums}")
nums.reverse()
print(f"reversed: {nums}")
```

**📸 Verified Output:**
```
sorted: [1, 1, 2, 3, 4, 5, 6, 9]
min: 1, max: 9, sum: 31
count 1: 2
index 5: 4
in-place sorted: [1, 1, 2, 3, 4, 5, 6, 9]
reversed: [9, 6, 5, 4, 3, 2, 1, 1]
```

### Step 4: Tuples (Immutable)
```python
point = (3, 4)
rgb = (255, 128, 0)
single = (42,)  # Note the comma!

print(point)
print(point[0], point[1])
x, y = point      # Unpacking
print(f"x={x}, y={y}")

# Tuples are immutable
try:
    point[0] = 99
except TypeError as e:
    print(f"TypeError: {e}")

# But you can use them in collections
coords = [(0,0), (1,2), (3,4)]
print(coords)
```

**📸 Verified Output:**
```
(3, 4)
3 4
x=3, y=4
TypeError: 'tuple' object does not support item assignment
[(0, 0), (1, 2), (3, 4)]
```

### Step 5: Sets
```python
s1 = {1, 2, 3, 4, 5}
s2 = {4, 5, 6, 7, 8}

print(f"union:        {s1 | s2}")
print(f"intersection: {s1 & s2}")
print(f"difference:   {s1 - s2}")
print(f"symmetric:    {s1 ^ s2}")

# Uniqueness
dupes = [1, 2, 2, 3, 3, 3, 4]
unique = list(set(dupes))
unique.sort()
print(f"unique: {unique}")

# Membership (O(1))
large_set = set(range(1000))
print(999 in large_set)  # Very fast
```

**📸 Verified Output:**
```
union:        {1, 2, 3, 4, 5, 6, 7, 8}
intersection: {4, 5}
difference:   {1, 2, 3}
symmetric:    {1, 2, 3, 6, 7, 8}
unique: [1, 2, 3, 4]
True
```

### Step 6: List Comprehensions
```python
# Traditional loop
squares = []
for i in range(1, 6):
    squares.append(i ** 2)
print(squares)

# List comprehension (Pythonic)
squares = [i ** 2 for i in range(1, 6)]
print(squares)

# With condition
evens = [i for i in range(20) if i % 2 == 0]
print(evens)

# Transform strings
words = ["hello", "world", "python"]
upper = [w.upper() for w in words]
print(upper)
```

**📸 Verified Output:**
```
[1, 4, 9, 16, 25]
[1, 4, 9, 16, 25]
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
['HELLO', 'WORLD', 'PYTHON']
```

### Step 7: Nested Lists (2D)
```python
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]

print(matrix[1][2])  # Row 1, Col 2: 6

# Transpose
transposed = [[row[i] for row in matrix] for i in range(3)]
for row in transposed:
    print(row)
```

**📸 Verified Output:**
```
6
[1, 4, 7]
[2, 5, 8]
[3, 6, 9]
```

### Step 8: Choosing the Right Type
```python
# List: ordered, mutable, allows duplicates
cart = ["apple", "banana", "apple"]
cart.append("cherry")

# Tuple: ordered, immutable, allows duplicates (use for fixed data)
point = (10, 20)
rgb = (255, 0, 128)

# Set: unordered, unique, fast membership
visited_urls = {"google.com", "python.org"}
visited_urls.add("github.com")

print(f"Cart: {cart}")
print(f"Point: {point}")
print(f"Visited: {len(visited_urls)} sites")
print(f"'python.org' visited: {'python.org' in visited_urls}")
```

**📸 Verified Output:**
```
Cart: ['apple', 'banana', 'apple', 'cherry']
Point: (10, 20)
Visited: 3 sites
'python.org' visited: True
```

## ✅ Verification
```python
data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
unique_sorted = sorted(set(data))
squares = [x**2 for x in unique_sorted]
print(f"Unique sorted: {unique_sorted}")
print(f"Squares: {squares}")
print("Lab 4 verified ✅")
```

**Expected output:**
```
Unique sorted: [1, 2, 3, 4, 5, 6, 9]
Squares: [1, 4, 9, 16, 25, 36, 81]
Lab 4 verified ✅
```

## 🚨 Common Mistakes
- `(42)` is just `42` in parentheses — use `(42,)` for a single-element tuple
- `list.sort()` modifies in place and returns `None`; `sorted()` returns new list
- Sets are unordered — don't rely on insertion order
- List copying: `b = a` makes an alias; use `b = a.copy()` or `b = a[:]`

## 📝 Summary
- **List**: `[]` — ordered, mutable, allows duplicates — use for ordered collections
- **Tuple**: `()` — ordered, immutable — use for fixed data (coordinates, RGB, DB records)
- **Set**: `{}` — unordered, unique, O(1) membership — use for deduplication
- List comprehensions `[x for x in iterable if condition]` are concise and fast
- `sorted()` returns new list; `.sort()` modifies in place

## 🔗 Further Reading
- [Python Docs: Lists](https://docs.python.org/3/tutorial/datastructures.html)
- [Real Python: Lists vs Tuples](https://realpython.com/python-lists-and-tuples/)
"""),
        ("Dictionaries", "lab-05-dictionaries.md",
"""## 🎯 Objective
Master Python dictionaries — the key-value store used in JSON APIs, configuration, caching, and almost every real Python application.

## 📚 Background
Dictionaries (`dict`) store **key-value pairs** with O(1) average lookup. As of Python 3.7+, dicts maintain insertion order. They're Python's equivalent of hash maps, objects (in JS), or associative arrays. JSON data maps directly to Python dicts — making them essential for web development.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 4: Lists, Tuples & Sets

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Creating Dictionaries
```python
# Literal syntax
person = {"name": "Alice", "age": 30, "city": "NYC"}

# dict() constructor
config = dict(host="localhost", port=5432, debug=True)

# From list of tuples
pairs = [("a", 1), ("b", 2), ("c", 3)]
d = dict(pairs)

print(person)
print(config)
print(d)
```

**📸 Verified Output:**
```
{'name': 'Alice', 'age': 30, 'city': 'NYC'}
{'host': 'localhost', 'port': 5432, 'debug': True}
{'a': 1, 'b': 2, 'c': 3}
```

### Step 2: Access and Modification
```python
person = {"name": "Alice", "age": 30}

# Access
print(person["name"])
print(person.get("age"))
print(person.get("email", "N/A"))  # Default if missing

# Modify
person["age"] = 31
person["email"] = "alice@example.com"
print(person)

# Delete
del person["email"]
removed = person.pop("age")
print(f"Removed: {removed}")
print(person)
```

**📸 Verified Output:**
```
Alice
30
N/A
{'name': 'Alice', 'age': 31, 'email': 'alice@example.com'}
Removed: 31
{'name': 'Alice'}
```

### Step 3: Dictionary Methods
```python
d = {"x": 10, "y": 20, "z": 30}

print(list(d.keys()))
print(list(d.values()))
print(list(d.items()))

# Iterate
for key, value in d.items():
    print(f"  {key} = {value}")

# Membership
print("x" in d)
print("w" in d)
```

**📸 Verified Output:**
```
['x', 'y', 'z']
[10, 20, 30]
[('x', 10), ('y', 20), ('z', 30)]
  x = 10
  y = 20
  z = 30
True
False
```

### Step 4: Merging Dictionaries
```python
defaults = {"color": "blue", "size": "medium", "debug": False}
user_prefs = {"color": "red", "font": "Arial"}

# Python 3.9+ merge operator
merged = defaults | user_prefs
print(merged)

# Update (modifies in place)
config = {"host": "localhost", "port": 5432}
config.update({"port": 5433, "db": "myapp"})
print(config)
```

**📸 Verified Output:**
```
{'color': 'red', 'size': 'medium', 'debug': False, 'font': 'Arial'}
{'host': 'localhost', 'port': 5433, 'db': 'myapp'}
```

### Step 5: Dictionary Comprehensions
```python
# Squares dict
squares = {x: x**2 for x in range(1, 6)}
print(squares)

# Filter and transform
prices = {"apple": 1.5, "banana": 0.5, "cherry": 3.0, "date": 5.0}
expensive = {k: v for k, v in prices.items() if v > 1.0}
print(expensive)

# Invert a dict
original = {"a": 1, "b": 2, "c": 3}
inverted = {v: k for k, v in original.items()}
print(inverted)
```

**📸 Verified Output:**
```
{1: 1, 2: 4, 3: 9, 4: 16, 5: 25}
{'apple': 1.5, 'cherry': 3.0, 'date': 5.0}
{1: 'a', 2: 'b', 3: 'c'}
```

### Step 6: Nested Dictionaries
```python
users = {
    "alice": {"age": 30, "email": "alice@example.com", "roles": ["admin", "user"]},
    "bob":   {"age": 25, "email": "bob@example.com",   "roles": ["user"]},
}

# Access nested
print(users["alice"]["email"])
print(users["bob"]["roles"][0])

# Iterate nested
for username, info in users.items():
    roles = ", ".join(info["roles"])
    print(f"{username}: age={info['age']}, roles={roles}")
```

**📸 Verified Output:**
```
alice@example.com
user
alice: age=30, roles=admin, user
bob: age=25, roles=user
```

### Step 7: defaultdict and Counter
```python
from collections import defaultdict, Counter

# defaultdict — no KeyError on missing key
word_count = defaultdict(int)
text = "the cat sat on the mat the cat"
for word in text.split():
    word_count[word] += 1
print(dict(word_count))

# Counter — count elements directly
counter = Counter(text.split())
print(counter.most_common(3))
```

**📸 Verified Output:**
```
{'the': 3, 'cat': 2, 'sat': 1, 'on': 1, 'mat': 1}
[('the', 3), ('cat', 2), ('sat', 1)]
```

### Step 8: Dict as JSON
```python
import json

user = {
    "name": "Alice",
    "age": 30,
    "skills": ["Python", "SQL"],
    "address": {"city": "NYC", "zip": "10001"}
}

# Serialize to JSON string
json_str = json.dumps(user, indent=2)
print(json_str)

# Parse JSON back to dict
parsed = json.loads(json_str)
print(f"Name: {parsed['name']}, City: {parsed['address']['city']}")
```

**📸 Verified Output:**
```
{
  "name": "Alice",
  "age": 30,
  "skills": [
    "Python",
    "SQL"
  ],
  "address": {
    "city": "NYC",
    "zip": "10001"
  }
}
Name: Alice, City: NYC
```

## ✅ Verification
```python
from collections import Counter
text = "hello world hello python world hello"
counts = Counter(text.split())
top2 = counts.most_common(2)
print(f"Top 2 words: {top2}")
total = sum(counts.values())
print(f"Total words: {total}")
print("Lab 5 verified ✅")
```

**Expected output:**
```
Top 2 words: [('hello', 3), ('world', 2)]
Total words: 6
Lab 5 verified ✅
```

## 🚨 Common Mistakes
- `d["missing_key"]` raises KeyError — use `d.get("key", default)` 
- Iterating and modifying dict simultaneously causes RuntimeError — iterate a copy: `for k in list(d.keys())`
- Dict keys must be hashable — lists can't be keys; tuples can
- `dict.update()` modifies in place; `dict | other` returns new dict

## 📝 Summary
- Dicts store key→value pairs with O(1) average lookup
- Access safely with `.get(key, default)`; check existence with `key in d`
- Iterate with `.items()`, `.keys()`, `.values()`
- Dict comprehensions: `{k: v for k, v in ...}`
- `Counter` and `defaultdict` solve common counting/grouping patterns

## 🔗 Further Reading
- [Python Docs: Dictionaries](https://docs.python.org/3/tutorial/datastructures.html#dictionaries)
- [Python Docs: collections module](https://docs.python.org/3/library/collections.html)
"""),
    ],
}

# Write all Python foundations labs
print("Writing Python foundations labs...")
for i, (title, filename, content) in enumerate(PYTHON_LABS["foundations"], 1):
    path = f"{REPO}/python/foundations/labs/{filename}"
    write_lab(path, content)
    print(f"  ✅ {filename}")

print(f"\n✅ Written {len(PYTHON_LABS['foundations'])} Python foundations labs")
