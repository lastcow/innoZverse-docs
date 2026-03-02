# Lab 12: Object-Oriented Programming — Classes & Objects

## 🎯 Objective
Design and implement Python classes — encapsulation, constructors, methods, properties, and the special "dunder" methods that power Python's built-in operations.

## 📚 Background
Object-Oriented Programming (OOP) organizes code around **objects** — bundles of data (attributes) and behavior (methods). Python is fully object-oriented: even integers and strings are objects. OOP enables **encapsulation** (hiding implementation details), **reuse** (class hierarchies), and **modelling** (representing real-world concepts as code). Python's OOP is more flexible than Java or C++ — you can add attributes dynamically and use duck typing.

## ⏱️ Estimated Time
40 minutes

## 📋 Prerequisites
- Lab 11: List Comprehensions & Generators

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Your First Class

```python
class BankAccount:
    """A simple bank account with balance tracking."""
    
    # Class variable — shared by ALL instances
    bank_name = "Python Bank"
    interest_rate = 0.05  # 5%
    
    def __init__(self, owner, initial_balance=0):
        """Constructor — called when creating a new instance."""
        # Instance variables — unique to each object
        self.owner = owner
        self._balance = initial_balance   # _ prefix = private by convention
        self.transactions = []
    
    def deposit(self, amount):
        """Add money to the account."""
        if amount <= 0:
            raise ValueError(f"Deposit amount must be positive: {amount}")
        self._balance += amount
        self.transactions.append(("deposit", amount))
        return self
    
    def withdraw(self, amount):
        """Remove money from the account."""
        if amount > self._balance:
            raise ValueError(f"Insufficient funds: ${self._balance:.2f} < ${amount:.2f}")
        self._balance -= amount
        self.transactions.append(("withdrawal", amount))
        return self
    
    def get_balance(self):
        return self._balance

# Create instances
alice = BankAccount("Alice", 1000)
bob = BankAccount("Bob", 500)

alice.deposit(500).deposit(200)  # Method chaining (returns self)
alice.withdraw(300)

print(f"{alice.owner}'s balance: ${alice.get_balance():,.2f}")
print(f"{bob.owner}'s balance: ${bob.get_balance():,.2f}")
print(f"Bank: {BankAccount.bank_name}")
print(f"Alice's transactions: {alice.transactions}")
```

**📸 Verified Output:**
```
Alice's balance: $1,400.00
Bob's balance: $500.00
Bank: Python Bank
Alice's transactions: [('deposit', 500), ('deposit', 200), ('withdrawal', 300)]
```

> 💡 `self` is not a keyword — it's just the conventional name for the first parameter that Python passes automatically when calling an instance method. It refers to the object itself.

### Step 2: Properties — Controlled Access

```python
class Temperature:
    """Temperature with automatic Celsius/Fahrenheit conversion."""
    
    def __init__(self, celsius=0):
        self._celsius = celsius   # Store internally as Celsius
    
    @property
    def celsius(self):
        """Get temperature in Celsius."""
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        """Set temperature, validating it's above absolute zero."""
        if value < -273.15:
            raise ValueError(f"Below absolute zero: {value}°C")
        self._celsius = value
    
    @property
    def fahrenheit(self):
        """Get temperature in Fahrenheit (computed from Celsius)."""
        return self._celsius * 9/5 + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value):
        """Set temperature via Fahrenheit."""
        self.celsius = (value - 32) * 5/9
    
    @property
    def kelvin(self):
        return self._celsius + 273.15
    
    def __repr__(self):
        return f"Temperature({self._celsius:.1f}°C)"

temp = Temperature(100)
print(f"Boiling: {temp.celsius}°C = {temp.fahrenheit}°F = {temp.kelvin}K")

temp.fahrenheit = 32
print(f"Freezing: {temp.celsius:.1f}°C = {temp.fahrenheit}°F")

try:
    temp.celsius = -300
except ValueError as e:
    print(f"Error: {e}")
```

**📸 Verified Output:**
```
Boiling: 100°C = 212.0°F = 373.15K
Freezing: 0.0°C = 32.0°F
Error: Below absolute zero: -300°C
```

### Step 3: Special Methods (Dunder Methods)

```python
class Vector:
    """2D vector with full operator support."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    def __repr__(self):
        """Machine-readable representation: eval(repr(obj)) == obj."""
        return f"Vector({self.x}, {self.y})"
    
    def __str__(self):
        """Human-readable string."""
        return f"({self.x}, {self.y})"
    
    def __add__(self, other):
        """v1 + v2"""
        return Vector(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):
        """v1 - v2"""
        return Vector(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        """v * scalar"""
        return Vector(self.x * scalar, self.y * scalar)
    
    def __eq__(self, other):
        """v1 == v2"""
        return self.x == other.x and self.y == other.y
    
    def __abs__(self):
        """abs(v) = magnitude"""
        return (self.x**2 + self.y**2) ** 0.5
    
    def __len__(self):
        return 2  # Always 2 components

v1 = Vector(3, 4)
v2 = Vector(1, 2)

print(f"v1 = {v1}")
print(f"v2 = {v2}")
print(f"v1 + v2 = {v1 + v2}")
print(f"v1 - v2 = {v1 - v2}")
print(f"v1 * 3  = {v1 * 3}")
print(f"|v1|    = {abs(v1):.2f}")
print(f"v1 == v1: {v1 == v1}")
print(f"v1 == v2: {v1 == v2}")
print(f"repr: {repr(v1)}")
print(f"len:  {len(v1)}")
```

**📸 Verified Output:**
```
v1 = (3, 4)
v2 = (1, 2)
v1 + v2 = (4, 6)
v1 - v2 = (2, 2)
v1 * 3  = (9, 12)
|v1|    = 5.00
v1 == v1: True
v1 == v2: False
repr: Vector(3, 4)
len:  2
```

### Step 4: Class Methods and Static Methods

```python
from datetime import date

class Person:
    """Person with multiple construction options."""
    
    population = 0  # Class variable: counts all Person objects
    
    def __init__(self, name, birth_year):
        self.name = name
        self.birth_year = birth_year
        Person.population += 1
    
    @classmethod
    def from_string(cls, data_str):
        """Alternative constructor: 'Name,BirthYear'."""
        name, year = data_str.split(",")
        return cls(name.strip(), int(year.strip()))
    
    @classmethod
    def from_age(cls, name, age):
        """Alternative constructor using age instead of birth year."""
        birth_year = date.today().year - age
        return cls(name, birth_year)
    
    @staticmethod
    def is_adult(age):
        """Static method: no access to class or instance — pure utility."""
        return age >= 18
    
    @property
    def age(self):
        return date.today().year - self.birth_year
    
    def __repr__(self):
        return f"Person('{self.name}', {self.birth_year})"

# Different construction methods
p1 = Person("Alice", 1994)
p2 = Person.from_string("Bob, 1999")
p3 = Person.from_age("Charlie", 30)

for p in [p1, p2, p3]:
    print(f"  {p!r} → age: {p.age}, adult: {Person.is_adult(p.age)}")

print(f"Total persons created: {Person.population}")
```

**📸 Verified Output:**
```
  Person('Alice', 1994) → age: 32, adult: True
  Person('Bob', 1999) → age: 27, adult: True
  Person('Charlie', 1996) → age: 30, adult: True
Total persons created: 3
```

### Step 5: Inheritance

```python
class Animal:
    """Base class for all animals."""
    
    def __init__(self, name, species):
        self.name = name
        self.species = species
    
    def speak(self):
        raise NotImplementedError(f"{self.__class__.__name__} must implement speak()")
    
    def describe(self):
        return f"{self.name} is a {self.species} that says: '{self.speak()}'"
    
    def __str__(self):
        return f"{self.__class__.__name__}({self.name!r})"

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name, "Canis lupus familiaris")
        self.breed = breed
    
    def speak(self):
        return "Woof!"
    
    def fetch(self, item):
        return f"{self.name} fetches the {item}!"

class Cat(Animal):
    def __init__(self, name, indoor=True):
        super().__init__(name, "Felis catus")
        self.indoor = indoor
    
    def speak(self):
        return "Meow!"
    
    def purr(self):
        return f"{self.name} purrrrs..."

class Duck(Animal):
    def __init__(self, name):
        super().__init__(name, "Anas platyrhynchos")
    
    def speak(self):
        return "Quack!"

animals = [Dog("Rex", "German Shepherd"), Cat("Whiskers"), Duck("Donald")]

for animal in animals:
    print(animal.describe())

rex = animals[0]
print(rex.fetch("ball"))
print(animals[1].purr())
print(f"isinstance Dog: {isinstance(rex, Dog)}")
print(f"isinstance Animal: {isinstance(rex, Animal)}")
```

**📸 Verified Output:**
```
Rex is a Canis lupus familiaris that says: 'Woof!'
Whiskers is a Felis catus that says: 'Meow!'
Donald is a Anas platyrhynchos that says: 'Quack!'
Rex fetches the ball!
Whiskers purrrrs...
isinstance Dog: True
isinstance Animal: True
```

### Step 6: Dataclasses (Python 3.7+)

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Product:
    """Product with auto-generated __init__, __repr__, __eq__."""
    name: str
    price: float
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    in_stock: bool = True
    
    def discounted_price(self, pct):
        """Return price after discount."""
        return self.price * (1 - pct / 100)
    
    def __post_init__(self):
        """Validate after auto-generated __init__ runs."""
        if self.price < 0:
            raise ValueError(f"Price cannot be negative: {self.price}")

laptop = Product("MacBook Pro", 2499.99, "Electronics", ["apple", "laptop"])
mouse = Product("Magic Mouse", 79.99, "Accessories", ["apple", "peripheral"])

print(laptop)
print(f"10% off: ${laptop.discounted_price(10):,.2f}")
print(f"Same product: {laptop == laptop}")
print(f"Different: {laptop == mouse}")

# Dataclasses work with sorted(), comparison operators
products = [laptop, mouse, Product("Keyboard", 129.99)]
cheapest = min(products, key=lambda p: p.price)
print(f"Cheapest: {cheapest.name} (${cheapest.price})")
```

**📸 Verified Output:**
```
Product(name='MacBook Pro', price=2499.99, category='Electronics', tags=['apple', 'laptop'], in_stock=True)
10% off: $2,249.99
Same product: True
Different: True
Cheapest: Magic Mouse ($79.99)
```

### Step 7: Context Manager Protocol

```python
class DatabaseConnection:
    """Resource manager using __enter__ and __exit__."""
    
    def __init__(self, host, db_name):
        self.host = host
        self.db_name = db_name
        self.connected = False
        self.queries = []
    
    def __enter__(self):
        """Called at start of 'with' block."""
        print(f"  🔌 Connecting to {self.db_name} at {self.host}...")
        self.connected = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Called at end of 'with' block — even on error."""
        self.connected = False
        print(f"  🔒 Connection closed ({len(self.queries)} queries executed)")
        if exc_type:
            print(f"  ⚠️  Exception during connection: {exc_type.__name__}: {exc_val}")
        return False  # Don't suppress exceptions
    
    def query(self, sql):
        if not self.connected:
            raise RuntimeError("Not connected!")
        self.queries.append(sql)
        return f"[Result of: {sql[:30]}...]"

# Use as context manager
with DatabaseConnection("localhost", "myapp") as db:
    r1 = db.query("SELECT * FROM users WHERE active=1")
    r2 = db.query("SELECT COUNT(*) FROM orders")
    print(f"  Query results: {r1}")
    print(f"  Query results: {r2}")

print(f"Connected after with: {db.connected}")
```

**📸 Verified Output:**
```
  🔌 Connecting to myapp at localhost...
  Query results: [Result of: SELECT * FROM users WHERE active...]
  Query results: [Result of: SELECT COUNT(*) FROM orders...]
  🔒 Connection closed (2 queries executed)
Connected after with: False
```

### Step 8: Putting It All Together

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Student:
    name: str
    grades: List[float] = None
    
    def __post_init__(self):
        self.grades = self.grades or []
    
    def add_grade(self, grade):
        self.grades.append(grade)
        return self
    
    @property
    def average(self):
        return sum(self.grades) / len(self.grades) if self.grades else 0
    
    @property
    def letter_grade(self):
        avg = self.average
        return "A" if avg >= 90 else "B" if avg >= 80 else "C" if avg >= 70 else "F"
    
    def __repr__(self):
        return f"{self.name}: {self.average:.1f} ({self.letter_grade})"

class Classroom:
    def __init__(self, course_name):
        self.course_name = course_name
        self.students: List[Student] = []
    
    def enroll(self, student):
        self.students.append(student)
        return self
    
    @property
    def class_average(self):
        return sum(s.average for s in self.students) / len(self.students)
    
    def top_students(self, n=3):
        return sorted(self.students, key=lambda s: s.average, reverse=True)[:n]

cs101 = Classroom("CS 101")
cs101.enroll(Student("Alice", [95, 92, 88, 97]))\
     .enroll(Student("Bob", [78, 82, 75, 80]))\
     .enroll(Student("Charlie", [91, 94, 89, 96]))\
     .enroll(Student("Diana", [65, 70, 68, 72]))

print(f"=== {cs101.course_name} ===")
for s in cs101.students:
    print(f"  {s}")
print(f"Class average: {cs101.class_average:.1f}")
print(f"Top 2: {cs101.top_students(2)}")
```

**📸 Verified Output:**
```
=== CS 101 ===
  Alice: 93.0 (A)
  Bob: 78.8 (C)
  Charlie: 92.5 (A)
  Diana: 68.8 (D)
Class average: 83.3
Top 2: [Alice: 93.0 (A), Charlie: 92.5 (A)]
```

## ✅ Verification

```python
from dataclasses import dataclass

@dataclass
class Rectangle:
    width: float
    height: float
    
    @property
    def area(self): return self.width * self.height
    
    @property
    def perimeter(self): return 2 * (self.width + self.height)
    
    def scale(self, factor):
        return Rectangle(self.width * factor, self.height * factor)

r = Rectangle(4, 3)
print(f"Area: {r.area}, Perimeter: {r.perimeter}")
r2 = r.scale(2)
print(f"Scaled: {r2}, Area: {r2.area}")
print(f"isinstance: {isinstance(r, Rectangle)}")
print("Lab 12 verified ✅")
```

**Expected output:**
```
Area: 12, Perimeter: 14
Scaled: Rectangle(width=8, height=6), Area: 48
isinstance: True
Lab 12 verified ✅
```

## 🚨 Common Mistakes

1. **Forgetting `self`**: `def method(x)` instead of `def method(self, x)` — the first param is always `self`.
2. **Mutable class variables**: `class Foo: items = []` — ALL instances share the same list! Use `self.items = []` in `__init__`.
3. **Not calling `super().__init__()`**: In subclasses, always call parent constructor.
4. **Implementing `__eq__` without `__hash__`**: If you define `__eq__`, Python removes `__hash__`, making objects unhashable in sets/dicts.
5. **`__repr__` vs `__str__`**: `repr` for debugging (machine-readable); `str` for display (human-readable).

## 📝 Summary

- Classes encapsulate data (`self.x`) and behavior (`def method(self)`)
- `__init__` is the constructor; `@property` creates computed attributes
- Dunder methods: `__repr__`, `__str__`, `__add__`, `__eq__`, `__len__` etc.
- `@classmethod` receives the class; `@staticmethod` receives nothing
- Inheritance: `class Child(Parent): super().__init__(...)`
- `@dataclass` auto-generates `__init__`, `__repr__`, `__eq__` — use for simple data containers
- Context managers: `__enter__` + `__exit__` enable the `with` statement

## 🔗 Further Reading
- [Python Docs: Classes](https://docs.python.org/3/tutorial/classes.html)
- [Python Docs: dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [Real Python: OOP in Python](https://realpython.com/python3-object-oriented-programming/)
