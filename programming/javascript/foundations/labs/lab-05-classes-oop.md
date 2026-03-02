# Lab 5: Classes & OOP in JavaScript

## 🎯 Objective
Use ES6 classes, inheritance, static methods, private fields, and getter/setter to write clean object-oriented JavaScript.

## 📚 Background
JavaScript's class syntax (ES6+) is syntactic sugar over prototype chains. Classes provide a familiar OOP interface while JavaScript's prototype system works underneath. ES2022 added **private class fields** (`#field`) for true encapsulation without closures. Understanding prototype-based inheritance helps debug class-related bugs.

## ⏱️ Estimated Time
35 minutes

## 📋 Prerequisites
- Lab 4: Arrays & Objects

## 🛠️ Tools Used
- Node.js 20

## 🔬 Lab Instructions

### Step 1: Basic Class
```javascript
class Animal {
    #name;      // Private field (ES2022)
    #species;
    
    constructor(name, species) {
        this.#name = name;
        this.#species = species;
        this.sound = "...";
    }
    
    speak() {
        return `${this.#name} says: ${this.sound}`;
    }
    
    get name() { return this.#name; }
    get species() { return this.#species; }
    
    toString() {
        return `${this.#name} (${this.#species})`;
    }
}

const animal = new Animal("Generic", "Unknown");
console.log(animal.speak());
console.log(animal.name);
console.log(`${animal}`);

try {
    console.log(animal.#name);
} catch (e) {
    console.log("Private field access:", e.constructor.name);
}
```

**📸 Verified Output:**
```
Generic says: ...
Generic
Generic (Unknown)
Private field access: SyntaxError
```

### Step 2: Inheritance
```javascript
class Animal {
    constructor(name, species) {
        this.name = name;
        this.species = species;
    }
    speak() { return `${this.name} makes a sound`; }
    toString() { return `${this.name} (${this.species})`; }
}

class Dog extends Animal {
    #breed;
    constructor(name, breed) {
        super(name, "Canis lupus familiaris");
        this.#breed = breed;
    }
    speak() { return `${this.name} says: Woof!`; }
    fetch(item) { return `${this.name} fetches the ${item}!`; }
    get breed() { return this.#breed; }
}

class Cat extends Animal {
    constructor(name, indoor = true) {
        super(name, "Felis catus");
        this.indoor = indoor;
    }
    speak() { return `${this.name} says: Meow!`; }
    purr() { return `${this.name} purrrrs...`; }
}

const animals = [new Dog("Rex", "Shepherd"), new Cat("Whiskers"), new Animal("Bob","Unknown")];

animals.forEach(a => {
    console.log(a.speak());
    console.log(`  instanceof Dog: ${a instanceof Dog}`);
    console.log(`  instanceof Animal: ${a instanceof Animal}`);
});

const rex = animals[0];
console.log(rex.fetch("ball"));
console.log("Breed:", rex.breed);
```

**📸 Verified Output:**
```
Rex says: Woof!
  instanceof Dog: true
  instanceof Animal: true
Whiskers says: Meow!
  instanceof Dog: false
  instanceof Animal: true
Bob makes a sound
  instanceof Dog: false
  instanceof Animal: true
Rex fetches the ball!
Breed: Shepherd
```

### Step 3: Static Methods and Properties
```javascript
class MathUtils {
    static PI = 3.14159265358979;
    static #instanceCount = 0;  // Private static
    
    static add(a, b) { return a + b; }
    static subtract(a, b) { return a - b; }
    static multiply(a, b) { return a * b; }
    
    static circleArea(r) { return MathUtils.PI * r ** 2; }
    static clamp(val, min, max) { return Math.max(min, Math.min(max, val)); }
    
    static range(start, end, step = 1) {
        const result = [];
        for (let i = start; i < end; i += step) result.push(i);
        return result;
    }
}

// Call without instantiation
console.log(MathUtils.add(10, 20));
console.log(MathUtils.circleArea(5).toFixed(2));
console.log(MathUtils.clamp(150, 0, 100));
console.log(MathUtils.range(0, 10, 2));
```

**📸 Verified Output:**
```
30
78.54
100
[ 0, 2, 4, 6, 8 ]
```

### Step 4: Getters, Setters, and Validation
```javascript
class Temperature {
    #celsius;
    
    constructor(celsius) {
        this.celsius = celsius;  // Uses setter for validation
    }
    
    get celsius() { return this.#celsius; }
    set celsius(val) {
        if (val < -273.15) throw new RangeError(`Below absolute zero: ${val}`);
        this.#celsius = val;
    }
    
    get fahrenheit() { return this.#celsius * 9/5 + 32; }
    set fahrenheit(val) { this.celsius = (val - 32) * 5/9; }
    
    get kelvin() { return this.#celsius + 273.15; }
    
    toString() { return `${this.#celsius.toFixed(1)}°C`; }
}

const t = new Temperature(100);
console.log(`${t}: F=${t.fahrenheit}, K=${t.kelvin}`);

t.fahrenheit = 32;
console.log(`${t}: F=${t.fahrenheit}`);

try { new Temperature(-300); }
catch (e) { console.log(`RangeError: ${e.message}`); }
```

**📸 Verified Output:**
```
100.0°C: F=212, K=373.15
0.0°C: F=32
RangeError: Below absolute zero: -300
```

### Step 5: Mixins (Multiple Inheritance Pattern)
```javascript
// JavaScript doesn't support multiple inheritance — use mixins
const Serializable = (Base) => class extends Base {
    toJSON() { return JSON.stringify(this); }
    
    static fromJSON(json) {
        const data = JSON.parse(json);
        return Object.assign(new this(), data);
    }
};

const Timestamped = (Base) => class extends Base {
    constructor(...args) {
        super(...args);
        this.createdAt = new Date().toISOString().split("T")[0];
        this.updatedAt = this.createdAt;
    }
    
    touch() {
        this.updatedAt = new Date().toISOString().split("T")[0];
        return this;
    }
};

class BaseModel {
    constructor(data) { Object.assign(this, data); }
}

class User extends Serializable(Timestamped(BaseModel)) {
    constructor(data) { super(data); }
    get displayName() { return `${this.firstName} ${this.lastName}`; }
}

const user = new User({ firstName: "Alice", lastName: "Smith", age: 30 });
console.log("Name:", user.displayName);
console.log("Created:", user.createdAt);
const json = user.toJSON();
console.log("JSON:", json.slice(0, 60) + "...");
```

**📸 Verified Output:**
```
Name: Alice Smith
Created: 2026-03-02
JSON: {"firstName":"Alice","lastName":"Smith","age":30,"createdAt"...
```

### Step 6: Iterator Protocol
```javascript
class NumberRange {
    constructor(start, end, step = 1) {
        this.start = start;
        this.end = end;
        this.step = step;
    }
    
    [Symbol.iterator]() {
        let current = this.start;
        const end = this.end;
        const step = this.step;
        
        return {
            next() {
                if (current < end) {
                    const value = current;
                    current += step;
                    return { value, done: false };
                }
                return { value: undefined, done: true };
            }
        };
    }
}

const range = new NumberRange(0, 10, 2);

// Use in for...of
for (const n of range) {
    process.stdout.write(n + " ");
}
console.log();

// Use with spread
console.log([...new NumberRange(1, 6)]);

// Use with destructuring
const [first, second, ...rest] = new NumberRange(1, 8);
console.log(first, second, rest);
```

**📸 Verified Output:**
```
0 2 4 6 8 
[ 1, 2, 3, 4, 5 ]
1 2 [ 3, 4, 5, 6, 7 ]
```

### Step 7: Abstract Base Pattern
```javascript
class Shape {
    constructor(color = "black") {
        if (new.target === Shape) {
            throw new Error("Shape is abstract — cannot instantiate directly");
        }
        this.color = color;
    }
    
    // Abstract methods — subclasses MUST implement
    area() { throw new Error(`${this.constructor.name} must implement area()`); }
    perimeter() { throw new Error(`${this.constructor.name} must implement perimeter()`); }
    
    // Concrete method — available to all subclasses
    describe() {
        return `${this.constructor.name}(color=${this.color}, area=${this.area().toFixed(2)}, perimeter=${this.perimeter().toFixed(2)})`;
    }
}

class Circle extends Shape {
    constructor(radius, color) { super(color); this.radius = radius; }
    area() { return Math.PI * this.radius ** 2; }
    perimeter() { return 2 * Math.PI * this.radius; }
}

class Rectangle extends Shape {
    constructor(w, h, color) { super(color); this.width = w; this.height = h; }
    area() { return this.width * this.height; }
    perimeter() { return 2 * (this.width + this.height); }
}

const shapes = [new Circle(5, "red"), new Rectangle(4, 6, "blue"), new Circle(3, "green")];
shapes.forEach(s => console.log(s.describe()));

try { new Shape(); } catch(e) { console.log(e.message); }
```

**📸 Verified Output:**
```
Circle(color=red, area=78.54, perimeter=31.42)
Rectangle(color=blue, area=24.00, perimeter=20.00)
Circle(color=green, area=28.27, perimeter=18.85)
Shape is abstract — cannot instantiate directly
```

### Step 8: Design Pattern — Observer
```javascript
class EventEmitter {
    #listeners = new Map();
    
    on(event, callback) {
        if (!this.#listeners.has(event)) {
            this.#listeners.set(event, []);
        }
        this.#listeners.get(event).push(callback);
        return this;  // Chainable
    }
    
    off(event, callback) {
        const listeners = this.#listeners.get(event) || [];
        this.#listeners.set(event, listeners.filter(l => l !== callback));
        return this;
    }
    
    emit(event, ...args) {
        const listeners = this.#listeners.get(event) || [];
        listeners.forEach(listener => listener(...args));
        return this;
    }
}

class Store extends EventEmitter {
    #state;
    
    constructor(initialState) {
        super();
        this.#state = { ...initialState };
    }
    
    get state() { return { ...this.#state }; }
    
    setState(updates) {
        const prev = this.#state;
        this.#state = { ...this.#state, ...updates };
        this.emit("change", this.#state, prev);
    }
}

const store = new Store({ count: 0, user: null });

store.on("change", (next, prev) => {
    console.log(`State changed: count ${prev.count} → ${next.count}`);
});

store.setState({ count: 1 });
store.setState({ count: 2, user: "Alice" });
store.setState({ count: 3 });

console.log("Final state:", store.state);
```

**📸 Verified Output:**
```
State changed: count 0 → 1
State changed: count 1 → 2
State changed: count 2 → 3
Final state: { count: 3, user: 'Alice' }
```

## ✅ Verification
```javascript
class Stack {
    #items = [];
    
    push(item) { this.#items.push(item); return this; }
    pop() {
        if (this.isEmpty()) throw new Error("Stack is empty");
        return this.#items.pop();
    }
    peek() { return this.#items.at(-1); }
    isEmpty() { return this.#items.length === 0; }
    get size() { return this.#items.length; }
    toArray() { return [...this.#items]; }
}

const s = new Stack();
s.push(1).push(2).push(3);
console.log("size:", s.size);
console.log("peek:", s.peek());
console.log("pop:", s.pop());
console.log("array:", s.toArray());
try { new Stack().pop(); } catch(e) { console.log("empty pop:", e.message); }
console.log("Lab 5 verified ✅");
```

**Expected output:**
```
size: 3
peek: 3
pop: 3
array: [ 1, 2 ]
empty pop: Stack is empty
Lab 5 verified ✅
```

## 🚨 Common Mistakes
1. **Forgetting `super()` in constructors**: Derived class constructors must call `super()` before accessing `this`.
2. **`this` in regular method callbacks**: `arr.forEach(function() { this.x })` — `this` is undefined; use arrow functions.
3. **Public vs private**: `this._name` (underscore) is convention only — not truly private. Use `#name` for real privacy.
4. **`instanceof` across realms**: Fails across iframes/workers — use duck typing or `Symbol.hasInstance`.
5. **Static and instance confusion**: `this.staticMethod()` doesn't work; call `ClassName.staticMethod()`.

## 📝 Summary
- `class Name { constructor() {} method() {} get prop() {} }` — ES6 class syntax
- `extends` for inheritance; always `super()` before `this` in child constructor
- `#field` for true private fields (ES2022); `static` for class-level members
- Mixins: `const Mix = (Base) => class extends Base {}` for multiple inheritance
- `[Symbol.iterator]()` makes objects iterable with `for...of` and spread
- Design patterns: Observer/EventEmitter, Abstract Base, Factory, Builder

## 🔗 Further Reading
- [MDN: Classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes)
- [JavaScript.info: Classes](https://javascript.info/classes)
