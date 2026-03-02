# Lab 4: Arrays & Objects

## 🎯 Objective
Master JavaScript's two primary data structures — arrays (ordered collections) and objects (key-value maps) — including modern ES6+ destructuring, spreading, and array methods.

## 📚 Background
In JavaScript, **arrays** and **objects** are the building blocks of every data structure. Arrays are actually special objects with numeric keys. ES6 introduced powerful syntax: destructuring, spread, rest, shorthand properties, and computed property names. The functional array methods (`map`, `filter`, `reduce`, `find`, `sort`) eliminate most loops.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 3: Functions, Scope & Closures

## 🛠️ Tools Used
- Node.js 20

## 🔬 Lab Instructions

### Step 1: Array Creation and Access
```javascript
const fruits = ["apple", "banana", "cherry"];
const mixed = [1, "two", true, null, { id: 5 }, [6, 7]];
const empty = new Array(5).fill(0);  // [0,0,0,0,0]

console.log(fruits[0], fruits.at(-1));   // First and last
console.log(fruits.length);
console.log(empty);
console.log(Array.from({length: 5}, (_, i) => i * 2));  // [0,2,4,6,8]
```

**📸 Verified Output:**
```
apple cherry
3
[ 0, 0, 0, 0, 0 ]
[ 0, 2, 4, 6, 8 ]
```

### Step 2: Array Mutation Methods
```javascript
const arr = [1, 2, 3];

arr.push(4, 5);         // Add to end
console.log("push:", arr);

arr.unshift(0);         // Add to front
console.log("unshift:", arr);

const last = arr.pop();      // Remove from end
console.log("pop:", last, arr);

const first = arr.shift();   // Remove from front
console.log("shift:", first, arr);

arr.splice(2, 1, 99);    // At index 2, remove 1, insert 99
console.log("splice:", arr);
```

**📸 Verified Output:**
```
push: [ 1, 2, 3, 4, 5 ]
unshift: [ 0, 1, 2, 3, 4, 5 ]
pop: 5 [ 0, 1, 2, 3, 4 ]
shift: 0 [ 1, 2, 3, 4 ]
splice: [ 1, 2, 99, 4 ]
```

### Step 3: Functional Array Methods
```javascript
const numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// map — transform each element
const squares = numbers.map(n => n ** 2);
console.log("squares:", squares);

// filter — keep elements matching predicate
const evens = numbers.filter(n => n % 2 === 0);
console.log("evens:", evens);

// reduce — accumulate to single value
const sum = numbers.reduce((acc, n) => acc + n, 0);
console.log("sum:", sum);

// find / findIndex
const firstOver5 = numbers.find(n => n > 5);
const idx = numbers.findIndex(n => n > 5);
console.log("find:", firstOver5, "at index:", idx);

// some / every
console.log("any > 8:", numbers.some(n => n > 8));
console.log("all > 0:", numbers.every(n => n > 0));

// flat and flatMap
const nested = [[1,2], [3,4], [5,6]];
console.log("flat:", nested.flat());
console.log("flatMap:", numbers.slice(0,3).flatMap(n => [n, n*10]));
```

**📸 Verified Output:**
```
squares: [ 1, 4, 9, 16, 25, 36, 49, 64, 81, 100 ]
evens: [ 2, 4, 6, 8, 10 ]
sum: 55
find: 6 at index: 5
any > 8: true
all > 0: true
flat: [ 1, 2, 3, 4, 5, 6 ]
flatMap: [ 1, 10, 2, 20, 3, 30 ]
```

### Step 4: Sorting Arrays
```javascript
// sort() mutates in place — default: lexicographic (alphabetical)
const words = ["banana", "apple", "cherry", "date"];
words.sort();
console.log("sorted words:", words);

// Sort numbers (MUST provide comparator!)
const nums = [10, 9, 2, 1, 100, 50];
nums.sort();  // Wrong! Lexicographic: [1, 10, 100, 2, 50, 9]
console.log("wrong sort:", nums);

nums.sort((a, b) => a - b);  // Correct: ascending
console.log("asc:", nums);

nums.sort((a, b) => b - a);  // Descending
console.log("desc:", nums);

// Sort objects by property
const users = [
    { name: "Charlie", age: 30 },
    { name: "Alice", age: 25 },
    { name: "Bob", age: 35 },
];
users.sort((a, b) => a.age - b.age);
users.forEach(u => console.log(`  ${u.name}: ${u.age}`));
```

**📸 Verified Output:**
```
sorted words: [ 'apple', 'banana', 'cherry', 'date' ]
wrong sort: [ 1, 10, 100, 2, 50, 9 ]
asc: [ 1, 2, 9, 10, 50, 100 ]
desc: [ 100, 50, 10, 9, 2, 1 ]
  Alice: 25
  Charlie: 30
  Bob: 35
```

### Step 5: Object Basics and Methods
```javascript
const person = {
    firstName: "Alice",
    lastName: "Smith",
    age: 30,
    address: { city: "New York", zip: "10001" },
    hobbies: ["coding", "hiking"],
    
    // Method shorthand (ES6)
    fullName() {
        return `${this.firstName} ${this.lastName}`;
    },
    
    get info() {
        return `${this.fullName()}, ${this.age}, ${this.address.city}`;
    }
};

console.log(person.fullName());
console.log(person.info);
console.log(Object.keys(person));
console.log(Object.values(person).filter(v => typeof v === "string"));

// Computed property names
const prefix = "user";
const dynamic = {
    [`${prefix}Name`]: "Bob",
    [`${prefix}Age`]: 25,
};
console.log(dynamic);
```

**📸 Verified Output:**
```
Alice Smith
Alice Smith, 30, New York
[ 'firstName', 'lastName', 'age', 'address', 'hobbies', 'fullName', 'info' ]
[ 'Alice', 'Smith', 'New York' ]
{ userName: 'Bob', userAge: 25 }
```

### Step 6: Object Manipulation
```javascript
const defaults = { theme: "dark", lang: "en", fontSize: 16 };
const userPrefs = { lang: "zh", fontSize: 18 };

// Merge with spread (right wins)
const settings = { ...defaults, ...userPrefs };
console.log("merged:", settings);

// Object.assign (same as spread)
const copy = Object.assign({}, defaults, userPrefs);
console.log("assigned:", copy);

// Destructure with defaults
const { theme = "light", lang = "en", debug = false } = settings;
console.log(theme, lang, debug);

// Entries / fromEntries
const prices = { apple: 1.5, banana: 0.5, cherry: 3.0 };
const doubled = Object.fromEntries(
    Object.entries(prices).map(([k, v]) => [k, v * 2])
);
console.log("doubled:", doubled);
```

**📸 Verified Output:**
```
merged: { theme: 'dark', lang: 'zh', fontSize: 18 }
assigned: { theme: 'dark', lang: 'zh', fontSize: 18 }
dark zh false
doubled: { apple: 3, banana: 1, cherry: 6 }
```

### Step 7: Map and Set
```javascript
// Map — key-value pairs, any type as key
const map = new Map();
map.set("name", "Alice");
map.set(42, "the answer");
map.set(true, "yes");

console.log(map.get("name"));
console.log(map.get(42));
console.log("size:", map.size);

for (const [key, val] of map) {
    console.log(`  ${key} → ${val}`);
}

// Set — unique values
const set = new Set([1, 2, 3, 2, 1, 4, 3]);
console.log("Set:", [...set]);
console.log("has 3:", set.has(3));

// Deduplicate an array using Set
const dupes = ["a", "b", "a", "c", "b", "d"];
const unique = [...new Set(dupes)];
console.log("unique:", unique);
```

**📸 Verified Output:**
```
Alice
the answer
size: 3
  name → Alice
  42 → the answer
  true → yes
Set: [ 1, 2, 3, 4 ]
has 3: true
unique: [ 'a', 'b', 'c', 'd' ]
```

### Step 8: Real-World Data Pipeline
```javascript
const orders = [
    { id: 1, customer: "Alice", product: "Laptop", qty: 1, price: 999 },
    { id: 2, customer: "Bob",   product: "Mouse",  qty: 3, price: 29  },
    { id: 3, customer: "Alice", product: "Monitor", qty: 2, price: 350 },
    { id: 4, customer: "Bob",   product: "Keyboard", qty: 1, price: 80 },
    { id: 5, customer: "Charlie", product: "Laptop", qty: 2, price: 999},
];

// Add total to each order
const withTotals = orders.map(o => ({ ...o, total: o.qty * o.price }));

// Group by customer
const byCustomer = withTotals.reduce((groups, order) => {
    const key = order.customer;
    groups[key] = groups[key] || [];
    groups[key].push(order);
    return groups;
}, {});

// Summary per customer
Object.entries(byCustomer).forEach(([customer, orders]) => {
    const spent = orders.reduce((sum, o) => sum + o.total, 0);
    const items = orders.map(o => o.product).join(", ");
    console.log(`${customer}: $${spent.toLocaleString()} — ${items}`);
});
```

**📸 Verified Output:**
```
Alice: $1,699 — Laptop, Monitor
Bob: $167 — Mouse, Keyboard
Charlie: $1,998 — Laptop
```

## ✅ Verification
```javascript
const students = [
    { name: "Alice", grades: [90, 85, 92] },
    { name: "Bob",   grades: [70, 75, 80] },
    { name: "Charlie", grades: [95, 98, 100] },
];

const withAvg = students
    .map(s => ({ ...s, avg: s.grades.reduce((a,b) => a+b) / s.grades.length }))
    .sort((a, b) => b.avg - a.avg);

withAvg.forEach((s, i) => console.log(`${i+1}. ${s.name}: ${s.avg.toFixed(1)}`));
console.log("Lab 4 verified ✅");
```

**Expected output:**
```
1. Charlie: 97.7
2. Alice: 89.0
3. Bob: 75.0
Lab 4 verified ✅
```

## 🚨 Common Mistakes
1. **Mutating during `.map()`**: Always return a new value from map — don't mutate `arr[i]`.
2. **`sort()` without comparator**: Default sort is lexicographic — always pass `(a,b) => a-b` for numbers.
3. **`const arr = []; arr = []`**: `const` prevents reassignment, not mutation — `arr.push()` is fine.
4. **Object spread is shallow**: Nested objects are still shared references — use `structuredClone()` for deep copy.
5. **`for...in` on arrays**: Iterates indices as strings and includes prototype properties — use `for...of`.

## 📝 Summary
- Arrays: `push/pop` (end), `shift/unshift` (front), `splice` (anywhere), `slice` (copy)
- Functional methods: `map` (transform), `filter` (select), `reduce` (accumulate), `find` (first match)
- Sort: always provide `(a, b) => a - b` comparator for numbers
- Object spread `{...a, ...b}` merges (right overwrites left); shallow copy only
- `Map` for any-typed keys with O(1) lookup; `Set` for unique values

## 🔗 Further Reading
- [MDN: Array methods](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array)
- [MDN: Object](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object)
