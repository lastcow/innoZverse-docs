# Lab 4: Lists, Tuples & Sets

## 🎯 Objective
Master Python's three sequence/collection types: lists (mutable sequences), tuples (immutable sequences), and sets (unique unordered collections).

## 📚 Background
Python has rich built-in collection types. **Lists** store ordered mutable sequences. **Tuples** store ordered immutable sequences (faster, safer for fixed data). **Sets** store unique unordered items with O(1) membership tests. Each excels in different scenarios.

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
print(fruits)
print(fruits[0])     # First: apple
print(fruits[-1])    # Last: cherry
print(fruits[1:3])   # Slice
print(len(fruits))   # 3
print(type(fruits))
```

**📸 Verified Output:**
```
['apple', 'banana', 'cherry']
apple
cherry
['banana', 'cherry']
3
<class 'list'>
```

### Step 2: Modifying Lists
```python
fruits = ["apple", "banana"]
fruits.append("cherry")
fruits.insert(1, "blueberry")
fruits.extend(["date", "fig"])
print(fruits)

fruits.remove("banana")
last = fruits.pop()
print(fruits)
print(f"Popped: {last}")
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
print(f"sorted:  {sorted(nums)}")
print(f"min: {min(nums)}, max: {max(nums)}, sum: {sum(nums)}")
print(f"count 1: {nums.count(1)}")

nums.sort()
print(f"in-place: {nums}")
nums.reverse()
print(f"reversed: {nums}")
```

**📸 Verified Output:**
```
sorted:  [1, 1, 2, 3, 4, 5, 6, 9]
min: 1, max: 9, sum: 31
count 1: 2
in-place: [1, 1, 2, 3, 4, 5, 6, 9]
reversed: [9, 6, 5, 4, 3, 2, 1, 1]
```

### Step 4: Tuples (Immutable)
```python
point = (3, 4)
rgb = (255, 128, 0)
single = (42,)   # Comma makes it a tuple

print(point)
x, y = point     # Unpacking
print(f"x={x}, y={y}")

try:
    point[0] = 99
except TypeError as e:
    print(f"TypeError: {e}")

# Tuples in collections
coords = [(0, 0), (1, 2), (3, 4)]
print(coords)
```

**📸 Verified Output:**
```
(3, 4)
x=3, y=4
TypeError: 'tuple' object does not support item assignment
[(0, 0), (1, 2), (3, 4)]
```

> 💡 Tuples are immutable — safer for data that shouldn't change (coordinates, RGB values, database records). They're also ~30% faster than lists for iteration.

### Step 5: Sets
```python
s1 = {1, 2, 3, 4, 5}
s2 = {4, 5, 6, 7, 8}

print(f"union:        {sorted(s1 | s2)}")
print(f"intersection: {sorted(s1 & s2)}")
print(f"difference:   {sorted(s1 - s2)}")
print(f"symmetric:    {sorted(s1 ^ s2)}")

dupes = [1, 2, 2, 3, 3, 3, 4]
unique = sorted(set(dupes))
print(f"unique: {unique}")

print(999 in set(range(1000)))  # O(1) membership
```

**📸 Verified Output:**
```
union:        [1, 2, 3, 4, 5, 6, 7, 8]
intersection: [4, 5]
difference:   [1, 2, 3]
symmetric:    [1, 2, 3, 6, 7, 8]
unique: [1, 2, 3, 4]
True
```

### Step 6: List Comprehensions
```python
# Traditional
squares = []
for i in range(1, 6):
    squares.append(i ** 2)
print(squares)

# Comprehension (Pythonic)
squares = [i**2 for i in range(1, 6)]
print(squares)

# With filter
evens = [i for i in range(20) if i % 2 == 0]
print(evens)

words = ["hello", "world", "python"]
print([w.upper() for w in words])
```

**📸 Verified Output:**
```
[1, 4, 9, 16, 25]
[1, 4, 9, 16, 25]
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
['HELLO', 'WORLD', 'PYTHON']
```

### Step 7: Nested Lists (Matrix)
```python
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
print(matrix[1][2])   # Row 1, Col 2: 6

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

### Step 8: When to Use Each
```python
# List: ordered, mutable, allows duplicates
cart = ["apple", "banana", "apple"]
cart.append("cherry")

# Tuple: fixed/immutable data
point = (10.5, 20.3)
color = (255, 0, 128)

# Set: unique items, fast membership
visited = {"google.com", "python.org"}
visited.add("github.com")

print(f"Cart: {cart}")
print(f"Point: {point}")
print(f"Visited {len(visited)} sites")
print(f"python.org visited: {'python.org' in visited}")
```

**📸 Verified Output:**
```
Cart: ['apple', 'banana', 'apple', 'cherry']
Point: (10.5, 20.3)
Visited 3 sites
python.org visited: True
```

## ✅ Verification
```python
data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
unique_sorted = sorted(set(data))
squares = [x**2 for x in unique_sorted]
print(f"Unique: {unique_sorted}")
print(f"Squares: {squares}")
print("Lab 4 verified ✅")
```

**Expected output:**
```
Unique: [1, 2, 3, 4, 5, 6, 9]
Squares: [1, 4, 9, 16, 25, 36, 81]
Lab 4 verified ✅
```

## 🚨 Common Mistakes
- `(42)` is just `42` — use `(42,)` for single-element tuple
- `list.sort()` returns `None`; `sorted()` returns new list
- Sets are unordered — don't rely on order
- `b = a` makes alias; use `b = a.copy()` or `b = list(a)` to copy

## 📝 Summary
- **List `[]`**: ordered, mutable, duplicates allowed — for sequences
- **Tuple `()`**: ordered, immutable — for fixed records, function returns
- **Set `{}`**: unordered, unique, O(1) membership — for deduplication
- List comprehensions are concise and Pythonic
- `sorted()` returns new list; `.sort()` modifies in place

## 🔗 Further Reading
- [Python Docs: Data Structures](https://docs.python.org/3/tutorial/datastructures.html)
- [Real Python: Lists vs Tuples](https://realpython.com/python-lists-and-tuples/)
