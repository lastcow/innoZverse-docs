# Lab 1: Hello World & Python Basics

## 🎯 Objective
Write and run your first Python program, understand the Python interpreter, and learn the basic building blocks of the language.

## 📚 Background
Python is an interpreted, high-level programming language created by Guido van Rossum in 1991. It's now the world's most popular language for data science, web development, and automation. Python code reads almost like English — making it ideal for beginners and experts alike.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- None — this is your first lab!

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Your First Python Program
```python
print("Hello, World!")
print("Welcome to Python 3.12")
```

**📸 Verified Output:**
```
Hello, World!
Welcome to Python 3.12
```

> 💡 `print()` is Python's built-in function for output. Unlike C or Java, no semicolons — Python uses newlines to end statements.

### Step 2: Comments
```python
# This is a single-line comment

"""
This is a multi-line string / docstring.
Used to document files, classes, and functions.
"""

x = 42  # The answer to everything
print(x)
```

**📸 Verified Output:**
```
42
```

### Step 3: Python as a Calculator
```python
print(2 + 3)     # Addition:       5
print(10 - 4)    # Subtraction:    6
print(3 * 7)     # Multiplication: 21
print(15 / 4)    # Division:       3.75 (always float)
print(15 // 4)   # Floor division: 3
print(15 % 4)    # Modulo:         3
print(2 ** 8)    # Exponent:       256
```

**📸 Verified Output:**
```
5
6
21
3.75
3
3
256
```

> 💡 `/` always returns float in Python 3. Use `//` for integer division. `**` is the power operator.

### Step 4: Variables
```python
name = "Alice"
age = 30
height = 1.75
is_student = False

print(f"Name: {name}")
print(f"Age: {age}")
print(f"Type of age: {type(age)}")
print(f"Type of name: {type(name)}")
```

**📸 Verified Output:**
```
Name: Alice
Age: 30
Type of age: <class 'int'>
Type of name: <class 'str'>
```

> 💡 Python is **dynamically typed** — no need to declare types. `f"..."` is an f-string for embedding variables in text.

### Step 5: Multiple Assignment and Swap
```python
x, y, z = 1, 2, 3
print(x, y, z)

a, b = 10, 20
print(f"Before: a={a}, b={b}")
a, b = b, a   # Swap without temp variable!
print(f"After:  a={a}, b={b}")
```

**📸 Verified Output:**
```
1 2 3
Before: a=10, b=20
After:  a=20, b=10
```

### Step 6: Print Function Options
```python
# Custom separator
print("apple", "banana", "cherry", sep=", ")

# No newline at end
print("Same ", end="")
print("line!")

# Multiple values
print("Sum:", 3 + 4, "Product:", 3 * 4)
```

**📸 Verified Output:**
```
apple, banana, cherry
Same line!
Sum: 7 Product: 12
```

### Step 7: Getting System Info
```python
import sys
import platform

print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")
print(f"Platform: {platform.system()}")
print(f"Max integer: {sys.maxsize:,}")
```

**📸 Verified Output:**
```
Python version: 3.12
Platform: Linux
Max integer: 9,223,372,036,854,775,807
```

### Step 8: Python's Philosophy
```python
# Python emphasizes readability
# Bad (C-style):
x=10;y=20;z=x+y;print(z)

# Good (Pythonic):
x = 10
y = 20
z = x + y
print(z)
```

**📸 Verified Output:**
```
30
30
```

> 💡 Both work, but Python style (PEP 8) uses spaces around operators and one statement per line. Readable code is maintainable code.

## ✅ Verification
```python
import sys
print(f"Python {sys.version_info.major}.{sys.version_info.minor} ✅")
print(f"2**10 = {2**10}")
print("Lab 1 verified ✅")
```

## 🚨 Common Mistakes
- Mixing tabs and spaces — use 4 spaces consistently
- `Print()` vs `print()` — Python is case-sensitive
- `5/2` returns `2.5` not `2` — use `5//2` for integer division
- Forgetting quotes around strings: `name = Alice` → `NameError`

## 📝 Summary
- `print()` outputs to the terminal; `#` starts a comment
- Variables assigned with `=`; no type declarations needed
- Core types: `int`, `float`, `str`, `bool`
- f-strings `f"{value}"` are the modern formatting standard
- Python enforces readability — clean code is Pythonic code

## 🔗 Further Reading
- [Official Python Tutorial](https://docs.python.org/3/tutorial/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
