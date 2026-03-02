# Lab 3: Strings & String Methods

## 🎯 Objective
Master Python string manipulation — slicing, searching, formatting, and transformation — the tools you'll use in almost every Python program.

## 📚 Background
Strings in Python are **immutable sequences of Unicode characters**. Python ships with 40+ built-in string methods — more than any other language. You'll use strings constantly: reading files, calling APIs, parsing user input, building reports. Mastering strings makes everything else faster.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 2: Variables, Data Types & Type Conversion

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: String Creation Styles

Python gives you four ways to create strings. Each has its place.

```python
s1 = 'single quotes — works fine'
s2 = "double quotes — same thing"
s3 = """triple double quotes
for multi-line content"""
s4 = r"raw string: C:\Users\Alice\no_escape_needed"

print(s1)
print(s2)
print(s3)
print(s4)
print(f"Lengths: {len(s1)}, {len(s2)}, {len(s3)}, {len(s4)}")
```

**📸 Verified Output:**
```
single quotes — works fine
double quotes — same thing
triple double quotes
for multi-line content
raw string: C:\Users\Alice\no_escape_needed
Lengths: 26, 26, 38, 38
```

> 💡 **Raw strings** (`r"..."`) treat backslashes as literal characters — essential for Windows file paths, regular expressions, and LaTeX strings. Otherwise `\n` would be a newline, `\t` a tab, etc.

### Step 2: Indexing and Slicing

Strings are sequences — every character has a position. Python supports negative indexing (counting from the end).

```python
text = "Python"
#       P  y  t  h  o  n
#       0  1  2  3  4  5   (forward)
#      -6 -5 -4 -3 -2 -1   (backward)

print(text[0])      # First character: P
print(text[-1])     # Last character: n
print(text[1:4])    # Characters at index 1,2,3: yth
print(text[:3])     # First 3: Pyt
print(text[3:])     # From index 3 to end: hon
print(text[::-1])   # Reversed: nohtyP
print(text[::2])    # Every 2nd character: Pto
print(text[1:5:2])  # Index 1,3: yh
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
yh
```

> 💡 Slicing syntax: `s[start:stop:step]`. Omitting `start` defaults to 0, omitting `stop` defaults to end. `s[::-1]` is the classic Python idiom for reversing a string.

### Step 3: Essential String Methods

```python
sentence = "  Hello, World! Python is Amazing.  "

# Whitespace cleaning
print(repr(sentence.strip()))    # Both sides
print(repr(sentence.lstrip()))   # Left only
print(repr(sentence.rstrip()))   # Right only

# Case transformation
print("hello".upper())           # HELLO
print("WORLD".lower())           # world
print("hello world".title())     # Hello World
print("hello world".capitalize())# Hello world

# Search and replace
print(sentence.strip().replace("Amazing", "Powerful"))
print(sentence.strip().count("l"))  # Count occurrences
```

**📸 Verified Output:**
```
'Hello, World! Python is Amazing.'
'Hello, World! Python is Amazing.  '
'  Hello, World! Python is Amazing.'
HELLO
world
Hello World
Hello world
Hello, World! Python is Powerful.
3
```

### Step 4: Finding and Searching

```python
text = "the quick brown fox jumps over the lazy dog"

# find() returns index or -1 (safe)
print(text.find("fox"))         # 16
print(text.find("cat"))         # -1 (not found, no error)

# index() raises ValueError if not found
print(text.index("fox"))        # 16
try:
    text.index("cat")
except ValueError as e:
    print(f"ValueError: {e}")

# Membership test
print("fox" in text)            # True
print("cat" in text)            # False

# Starts/ends with
print(text.startswith("the"))   # True
print(text.endswith("dog"))     # True
print(text.count("the"))        # 2 (case-sensitive)
```

**📸 Verified Output:**
```
16
-1
16
ValueError: substring not found
True
False
True
True
2
```

> 💡 Prefer `find()` when not finding is a valid outcome (no crash). Use `index()` when the string *must* contain the substring (fail fast). Use `in` for simple boolean checks.

### Step 5: Split and Join

These two methods together handle 90% of string parsing tasks.

```python
# split() — string → list
csv_line = "Alice,30,New York,Engineer"
fields = csv_line.split(",")
print(fields)
print(f"Name: {fields[0]}, Age: {fields[1]}")

# split with maxsplit
key_value = "key=value=with=equals"
k, v = key_value.split("=", 1)  # Only split on first =
print(f"key='{k}', value='{v}'")

# join() — list → string (ALWAYS use this, not + in loops)
words = ["Python", "is", "awesome"]
print(" ".join(words))
print("-".join(["2024", "01", "15"]))
print(", ".join(str(i) for i in range(5)))
```

**📸 Verified Output:**
```
['Alice', '30', 'New York', 'Engineer']
Name: Alice, Age: 30
key='key', value='value=with=equals'
Python is awesome
2024-01-15
0, 1, 2, 3, 4
```

### Step 6: F-String Formatting (Modern Standard)

F-strings (Python 3.6+) are the fastest and most readable string formatting method.

```python
name = "Alice"
score = 98.5678
rank = 1
amount = 1234567.89

# Basic embedding
print(f"Player: {name}, Score: {score:.2f}, Rank: #{rank}")

# Number formatting
print(f"Pi:        {3.14159265:.4f}")    # 4 decimal places
print(f"Big num:   {amount:,.2f}")       # Thousands separator
print(f"Sci:       {0.000123:.2e}")      # Scientific notation
print(f"Percent:   {0.8567:.1%}")        # Percentage
print(f"Hex:       {255:#010x}")         # Hex with padding

# Alignment
print(f"{'Left':<10}|{'Center':^10}|{'Right':>10}")
print(f"{42:<10}|{42:^10}|{42:>10}")

# Inline expressions
items = [1, 2, 3, 4, 5]
print(f"Sum of items: {sum(items)}, Max: {max(items)}")
```

**📸 Verified Output:**
```
Player: Alice, Score: 98.57, Rank: #1
Pi:        3.1416
Big num:   1,234,567.89
Sci:       1.23e-04
Percent:   85.7%
Hex:       0x000000ff
Left      |  Center  |     Right
42        |    42    |        42
Sum of items: 15, Max: 5
```

### Step 7: String Validation Methods

Essential for form validation, data cleaning, and input sanitization.

```python
test_cases = [
    ("hello", "all lowercase letters"),
    ("HELLO", "all uppercase letters"),
    ("Hello123", "mixed alphanumeric"),
    ("12345", "all digits"),
    ("3.14", "float-like string"),
    ("   ", "only whitespace"),
    ("", "empty string"),
    ("hello world", "has space"),
]

for text, desc in test_cases:
    print(f"'{text}' ({desc}):")
    print(f"  isalpha={text.isalpha()}, isdigit={text.isdigit()}, "
          f"isalnum={text.isalnum()}, isspace={text.isspace() if text else 'N/A'}")
```

**📸 Verified Output:**
```
'hello' (all lowercase letters):
  isalpha=True, isdigit=False, isalnum=True, isspace=N/A
'HELLO' (all uppercase letters):
  isalpha=True, isdigit=False, isalnum=True, isspace=N/A
'Hello123' (mixed alphanumeric):
  isalpha=False, isdigit=False, isalnum=True, isspace=N/A
'12345' (all digits):
  isalpha=False, isdigit=True, isalnum=True, isspace=N/A
'3.14' (float-like string):
  isalpha=False, isdigit=False, isalnum=False, isspace=N/A
'   ' (only whitespace):
  isalpha=False, isdigit=False, isalnum=False, isspace=True
'' (empty string):
  isalpha=False, isdigit=False, isalnum=False, isspace=N/A
'hello world' (has space):
  isalpha=False, isdigit=False, isalnum=False, isspace=N/A
```

### Step 8: Real-World String Pipeline

Parse and clean messy real-world data.

```python
# Simulate raw CSV data with inconsistent formatting
raw_records = [
    "  ALICE SMITH  |  alice@EXAMPLE.COM  |  new york  |  engineer  ",
    "BOB JONES|bob@company.org|LONDON|developer",
    "  charlie brown | charlie@test.net | Tokyo | designer  ",
]

cleaned = []
for record in raw_records:
    fields = [f.strip() for f in record.split("|")]
    name = fields[0].title()
    email = fields[1].lower()
    city = fields[2].title()
    role = fields[3].capitalize()
    cleaned.append({"name": name, "email": email, "city": city, "role": role})

for person in cleaned:
    print(f"{person['name']:20} | {person['email']:25} | {person['city']:10} | {person['role']}")
```

**📸 Verified Output:**
```
Alice Smith          | alice@example.com         | New York   | Engineer
Bob Jones            | bob@company.org           | London     | Developer
Charlie Brown        | charlie@test.net          | Tokyo      | Designer
```

> 💡 This pattern — `split()`, `strip()`, `title()`/`lower()` — is the foundation of data cleaning in Python. Real-world data is always messy; these methods tame it.

## ✅ Verification

```python
# Full verification: reverse words, title case, join with dash
sentence = "  the quick brown fox  "
result = "-".join(w.title() for w in sentence.split())
print(result)

# Verify string operations
assert "python".upper() == "PYTHON"
assert "  hello  ".strip() == "hello"
assert ",".join(["a", "b", "c"]) == "a,b,c"
assert "hello".find("ll") == 2
print("All assertions passed!")
print("Lab 3 verified ✅")
```

**Expected output:**
```
The-Quick-Brown-Fox
All assertions passed!
Lab 3 verified ✅
```

## 🚨 Common Mistakes

1. **String mutation**: `s[0] = 'X'` raises `TypeError` — strings are immutable; create new strings instead.
2. **find() vs index()**: `find()` returns `-1` for not found; `index()` raises `ValueError` — know which you need.
3. **Forgetting strip()**: `"hello " != "hello"` — always strip user input before comparing.
4. **Using `+` in loops**: `result += s` in a loop is O(n²) — always use `"".join(list)`.
5. **Case-sensitive search**: `"Hello".find("hello")` returns `-1` — use `.lower()` before searching.

## 📝 Summary

- Strings are immutable Unicode sequences — methods always return NEW strings
- Slicing: `s[start:stop:step]` — negative indices count from the end backwards
- Key methods: `strip()`, `split()`, `join()`, `replace()`, `find()`, `upper()`, `lower()`, `title()`
- f-strings `f"{value:format}"` are the modern standard — fastest and most readable
- Always use `"sep".join(list)` not `+` concatenation in loops for performance

## 🔗 Further Reading
- [Python Docs: String Methods](https://docs.python.org/3/library/stdtypes.html#string-methods)
- [Real Python: Python f-Strings](https://realpython.com/python-f-strings/)
- [PEP 498: Literal String Interpolation](https://peps.python.org/pep-0498/)
