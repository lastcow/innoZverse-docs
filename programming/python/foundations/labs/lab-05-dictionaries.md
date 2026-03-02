# Lab 5: Dictionaries

## 🎯 Objective
Master Python dictionaries — the key-value store used in JSON, config files, caching, and almost every real Python application.

## 📚 Background
Dictionaries store **key-value pairs** with O(1) average lookup. Python 3.7+ dicts maintain insertion order. JSON maps directly to Python dicts — making them essential for web APIs. The `collections` module extends dicts with `Counter` and `defaultdict`.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 4: Lists, Tuples & Sets

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Creating Dictionaries
```python
person = {"name": "Alice", "age": 30, "city": "NYC"}
config = dict(host="localhost", port=5432, debug=True)
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

print(person["name"])
print(person.get("age"))
print(person.get("email", "N/A"))   # Safe default

person["age"] = 31
person["email"] = "alice@example.com"
print(person)

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

### Step 3: Iterating Dictionaries
```python
d = {"x": 10, "y": 20, "z": 30}

print(list(d.keys()))
print(list(d.values()))
print(list(d.items()))

for key, value in d.items():
    print(f"  {key} = {value}")

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

merged = defaults | user_prefs    # Python 3.9+ merge operator
print(merged)

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
squares = {x: x**2 for x in range(1, 6)}
print(squares)

prices = {"apple": 1.5, "banana": 0.5, "cherry": 3.0, "date": 5.0}
expensive = {k: v for k, v in prices.items() if v > 1.0}
print(expensive)

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
    "alice": {"age": 30, "roles": ["admin", "user"]},
    "bob":   {"age": 25, "roles": ["user"]},
}

print(users["alice"]["roles"][0])

for username, info in users.items():
    roles = ", ".join(info["roles"])
    print(f"{username}: age={info['age']}, roles={roles}")
```

**📸 Verified Output:**
```
admin
alice: age=30, roles=admin, user
bob: age=25, roles=user
```

### Step 7: Counter and defaultdict
```python
from collections import defaultdict, Counter

word_count = defaultdict(int)
text = "the cat sat on the mat the cat"
for word in text.split():
    word_count[word] += 1
print(dict(word_count))

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

json_str = json.dumps(user, indent=2)
print(json_str)

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
print(f"Top 2: {counts.most_common(2)}")
print(f"Total words: {sum(counts.values())}")
print("Lab 5 verified ✅")
```

**Expected output:**
```
Top 2: [('hello', 3), ('world', 2)]
Total words: 6
Lab 5 verified ✅
```

## 🚨 Common Mistakes
- `d["missing"]` raises KeyError — use `d.get("key", default)` for safe access
- Modifying dict while iterating → RuntimeError — iterate `list(d.keys())`
- Dict keys must be hashable — lists can't be keys, but tuples can
- `dict.update()` modifies in place; `d | other` returns new dict (Python 3.9+)

## 📝 Summary
- Dicts: key-value pairs with O(1) lookup; ordered since Python 3.7
- Safe access: `.get(key, default)`; existence check: `key in d`
- Iterate: `.items()`, `.keys()`, `.values()`
- Dict comprehensions: `{k: v for k, v in iterable}`
- `Counter` for counting, `defaultdict` for grouping

## 🔗 Further Reading
- [Python Docs: Dictionaries](https://docs.python.org/3/tutorial/datastructures.html#dictionaries)
- [Python Docs: collections](https://docs.python.org/3/library/collections.html)
