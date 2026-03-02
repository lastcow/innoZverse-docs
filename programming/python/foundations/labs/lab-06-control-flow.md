# Lab 6: Control Flow — Conditionals & Loops

## 🎯 Objective
Master Python's decision-making structures (if/elif/else) and loops (for, while) — the logic that drives every real program.

## 📚 Background
Control flow determines the **order** in which code executes. Without it, programs would just run top-to-bottom and stop. Conditionals let code make decisions; loops let code repeat. Python's syntax is cleaner than most languages — no curly braces, just indentation. Python also has unique features like `for/else`, `while/else`, and the ternary expression.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 5: Dictionaries

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Basic if/elif/else

```python
temperature = 22  # Celsius

if temperature < 0:
    status = "Freezing"
elif temperature < 10:
    status = "Cold"
elif temperature < 20:
    status = "Cool"
elif temperature < 30:
    status = "Comfortable"
else:
    status = "Hot"

print(f"{temperature}°C is: {status}")

# Multiple conditions with and/or
age = 25
has_id = True

if age >= 18 and has_id:
    print("Access granted")
elif age >= 18 and not has_id:
    print("Show ID please")
else:
    print("Access denied — underage")
```

**📸 Verified Output:**
```
22°C is: Comfortable
Access granted
```

> 💡 Python evaluates `elif` chains top-to-bottom and stops at the first `True` condition. Always put more specific conditions first, general conditions last.

### Step 2: Ternary Expression (One-Line If)

```python
# Traditional
x = 10
if x > 0:
    label = "positive"
else:
    label = "non-positive"
print(label)

# Ternary (Pythonic one-liner)
label = "positive" if x > 0 else "non-positive"
print(label)

# Nested ternary (use sparingly — readability first)
score = 75
grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "F"
print(f"Score {score} → Grade {grade}")

# Common use: default value
user_input = ""
name = user_input if user_input else "Anonymous"
print(f"Hello, {name}!")
```

**📸 Verified Output:**
```
positive
positive
Score 75 → Grade C
Hello, Anonymous!
```

### Step 3: for Loop Fundamentals

```python
# Loop over a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(f"  - {fruit}")

# Loop with range()
print("\nCounting:")
for i in range(5):        # 0,1,2,3,4
    print(i, end=" ")
print()

for i in range(2, 10, 2): # Start, stop, step (even numbers)
    print(i, end=" ")
print()

# Countdown
for i in range(5, 0, -1):
    print(i, end=" ")
print("Go!")
```

**📸 Verified Output:**
```
  - apple
  - banana
  - cherry

Counting:
0 1 2 3 4 
2 4 6 8 
5 4 3 2 1 Go!
```

### Step 4: enumerate() and zip()

```python
# enumerate() — get index AND value
fruits = ["apple", "banana", "cherry"]
for i, fruit in enumerate(fruits, start=1):
    print(f"{i}. {fruit}")

print()

# zip() — loop over multiple lists together
names = ["Alice", "Bob", "Charlie"]
scores = [95, 87, 92]
grades = ["A", "B+", "A-"]

for name, score, grade in zip(names, scores, grades):
    print(f"{name:10}: {score} ({grade})")
```

**📸 Verified Output:**
```
1. apple
2. banana
3. cherry

Alice     : 95 (A)
Bob       : 87 (B+)
Charlie   : 92 (A-)
```

> 💡 `enumerate()` is preferred over `for i in range(len(list))` — it's more Pythonic and less error-prone. `zip()` stops at the shortest sequence.

### Step 5: while Loop

```python
# Basic while
count = 0
while count < 5:
    print(f"count = {count}")
    count += 1

print("Done!")
print()

# While with user validation simulation
attempts = 0
max_attempts = 3
correct_pin = "1234"
test_inputs = ["9999", "0000", "1234"]  # Simulated user inputs

for test_input in test_inputs:
    attempts += 1
    if test_input == correct_pin:
        print(f"✅ PIN correct on attempt {attempts}!")
        break
    elif attempts >= max_attempts:
        print(f"❌ Too many failed attempts. Locked.")
        break
    else:
        print(f"❌ Wrong PIN ({attempts}/{max_attempts})")
```

**📸 Verified Output:**
```
count = 0
count = 1
count = 2
count = 3
count = 4
Done!

❌ Wrong PIN (1/3)
❌ Wrong PIN (2/3)
✅ PIN correct on attempt 3!
```

### Step 6: break, continue, pass

```python
# break — exit loop immediately
print("break demo:")
for i in range(10):
    if i == 5:
        break
    print(i, end=" ")
print(f"\nStopped at {i}")

print()

# continue — skip current iteration
print("continue demo (skip evens):")
for i in range(10):
    if i % 2 == 0:
        continue
    print(i, end=" ")
print()

print()

# pass — do nothing placeholder
for i in range(5):
    if i == 3:
        pass  # TODO: handle this case
    else:
        print(i, end=" ")
print()
```

**📸 Verified Output:**
```
break demo:
0 1 2 3 4 
Stopped at 5

continue demo (skip evens):
1 3 5 7 9 

0 1 2 4 
```

### Step 7: Nested Loops

```python
# Multiplication table (3x3)
print("Multiplication Table:")
for i in range(1, 4):
    for j in range(1, 4):
        print(f"{i*j:4}", end="")
    print()

print()

# Nested loop with break (searching 2D)
grid = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9],
]
target = 5
found = False

for row_idx, row in enumerate(grid):
    for col_idx, val in enumerate(row):
        if val == target:
            print(f"Found {target} at row={row_idx}, col={col_idx}")
            found = True
            break
    if found:
        break
```

**📸 Verified Output:**
```
Multiplication Table:
   1   2   3
   4   5   6
   7   8   9

Found 5 at row=1, col=1
```

### Step 8: Comprehension with Conditions

```python
# List comprehension with if
numbers = range(1, 21)
evens = [n for n in numbers if n % 2 == 0]
print(f"Evens: {evens}")

# FizzBuzz (classic interview question)
fizzbuzz = []
for n in range(1, 16):
    if n % 15 == 0:
        fizzbuzz.append("FizzBuzz")
    elif n % 3 == 0:
        fizzbuzz.append("Fizz")
    elif n % 5 == 0:
        fizzbuzz.append("Buzz")
    else:
        fizzbuzz.append(str(n))

print(", ".join(fizzbuzz))

# Comprehension version
result = ["FizzBuzz" if n%15==0 else "Fizz" if n%3==0 else "Buzz" if n%5==0 else str(n)
          for n in range(1, 16)]
print(", ".join(result))
```

**📸 Verified Output:**
```
Evens: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
1, 2, Fizz, 4, Buzz, Fizz, 7, 8, Fizz, Buzz, 11, Fizz, 13, 14, FizzBuzz
1, 2, Fizz, 4, Buzz, Fizz, 7, 8, Fizz, Buzz, 11, Fizz, 13, 14, FizzBuzz
```

## ✅ Verification

```python
# Prime number finder using nested loops
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

primes = [n for n in range(2, 50) if is_prime(n)]
print(f"Primes < 50: {primes}")
print(f"Count: {len(primes)}")
print("Lab 6 verified ✅")
```

**Expected output:**
```
Primes < 50: [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47]
Count: 15
Lab 6 verified ✅
```

## 🚨 Common Mistakes

1. **Infinite while loop**: Always ensure the loop condition eventually becomes `False` or has a `break`.
2. **Off-by-one in range()**: `range(n)` gives `0..n-1`; `range(1, n+1)` gives `1..n`.
3. **Modifying a list while iterating**: Causes skipped elements — iterate a copy: `for item in list(my_list)`.
4. **Using `=` instead of `==` in conditions**: `if x = 5` is a SyntaxError in Python (assignment, not comparison).
5. **Deep nesting**: More than 3 levels of nesting is hard to read — use functions to break it up.

## 📝 Summary

- `if/elif/else` chains: evaluated top-to-bottom, first match wins
- Ternary: `value_if_true if condition else value_if_false`
- `for item in iterable` — Python's primary loop; works on any iterable
- `enumerate(iterable, start=0)` gives index+value pairs
- `zip(a, b)` loops two iterables together
- `break` exits the loop; `continue` skips to next iteration; `pass` does nothing
- Prefer comprehensions for simple transformations; use regular loops for complex logic

## 🔗 Further Reading
- [Python Docs: Control Flow](https://docs.python.org/3/tutorial/controlflow.html)
- [Real Python: Python for Loops](https://realpython.com/python-for-loop/)
