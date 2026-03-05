# Lab 05: Prototypes & Classes

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master JavaScript's prototype chain, `Object.create`, modern class syntax with private fields, static methods, inheritance with `extends`/`super`, Symbol.iterator, and Mixin patterns.

---

## Step 1: Prototype Chain

```javascript
// Every object has a prototype (except Object.prototype)
const animal = {
  breathe() { return `${this.name} breathes`; },
  toString() { return `[Animal: ${this.name}]`; }
};

const dog = Object.create(animal);
dog.name = 'Rex';
dog.bark = function() { return `${this.name} barks!`; };

console.log(dog.breathe()); // Rex breathes (inherited)
console.log(dog.bark());    // Rex barks!
console.log(dog.toString()); // [Animal: Rex]
console.log(Object.getPrototypeOf(dog) === animal); // true

// Prototype chain lookup
console.log(dog.hasOwnProperty('name'));    // true (own property)
console.log(dog.hasOwnProperty('breathe')); // false (inherited)
console.log('breathe' in dog);              // true (searches chain)

// Viewing the chain
let obj = dog;
while (obj) {
  console.log(Object.getOwnPropertyNames(obj));
  obj = Object.getPrototypeOf(obj);
}
```

---

## Step 2: Object.create and Prototypal Inheritance

```javascript
// Object.create — explicit prototype inheritance
function createShape(color = 'black') {
  const shape = Object.create(createShape.prototype);
  shape.color = color;
  return shape;
}
createShape.prototype = {
  constructor: createShape,
  describe() { return `A ${this.color} ${this.type}`; },
  toJSON() { return { type: this.type, color: this.color }; }
};

function createCircle(radius, color) {
  const circle = Object.create(createShape.prototype);
  circle.type = 'circle';
  circle.radius = radius;
  circle.color = color;
  circle.area = function() { return Math.PI * this.radius ** 2; };
  return circle;
}

const c = createCircle(5, 'red');
console.log(c.describe());         // A red circle
console.log(c.area().toFixed(2)); // 78.54

// Object.create(null) — no prototype (pure hash map)
const lookup = Object.create(null);
lookup['constructor'] = 'safe';
lookup['toString'] = 'also safe';
// No prototype pollution possible
```

---

## Step 3: Class Syntax

```javascript
class Rectangle {
  // Class field (public)
  type = 'rectangle';

  constructor(width, height) {
    this.width = width;
    this.height = height;
  }

  // Method
  area() { return this.width * this.height; }
  perimeter() { return 2 * (this.width + this.height); }

  // Getter/Setter
  get aspectRatio() { return this.width / this.height; }
  set dimensions({ width, height }) {
    if (width <= 0 || height <= 0) throw new RangeError('Dimensions must be positive');
    this.width = width;
    this.height = height;
  }

  // Static method — called on class, not instances
  static createSquare(size) { return new Rectangle(size, size); }
  static compare(r1, r2) { return r1.area() - r2.area(); }

  toString() { return `Rectangle(${this.width}x${this.height})`; }
}

const rect = new Rectangle(4, 6);
console.log(rect.area());      // 24
console.log(rect.perimeter()); // 20
console.log(rect.aspectRatio); // 0.666...

const square = Rectangle.createSquare(5);
console.log(square.toString()); // Rectangle(5x5)
console.log(Rectangle.compare(rect, square)); // 24-25 = -1
```

---

## Step 4: Private Fields & Methods

```javascript
class BankAccount {
  // Private fields (truly private in modern JS)
  #balance;
  #owner;
  #transactions = [];
  static #totalAccounts = 0;

  constructor(owner, initialBalance = 0) {
    this.#owner = owner;
    this.#balance = initialBalance;
    BankAccount.#totalAccounts++;
  }

  // Private method
  #recordTransaction(type, amount) {
    this.#transactions.push({
      type, amount,
      balance: this.#balance,
      at: new Date().toISOString()
    });
  }

  deposit(amount) {
    if (amount <= 0) throw new RangeError('Amount must be positive');
    this.#balance += amount;
    this.#recordTransaction('deposit', amount);
    return this;
  }

  withdraw(amount) {
    if (amount > this.#balance) throw new Error('Insufficient funds');
    this.#balance -= amount;
    this.#recordTransaction('withdrawal', amount);
    return this;
  }

  get balance() { return this.#balance; }
  get owner() { return this.#owner; }
  get history() { return [...this.#transactions]; }
  static get totalAccounts() { return BankAccount.#totalAccounts; }
}

const acc = new BankAccount('Alice', 1000);
acc.deposit(500).withdraw(200);
console.log(acc.balance);             // 1300
console.log(acc.history.length);      // 2
console.log(BankAccount.totalAccounts); // 1
// acc.#balance; // SyntaxError — truly private
```

---

## Step 5: Inheritance with extends/super

```javascript
class Animal {
  #name;
  #sound;

  constructor(name, sound) {
    this.#name = name;
    this.#sound = sound;
  }

  speak() { return `${this.#name} says ${this.#sound}!`; }
  get name() { return this.#name; }

  toString() { return `[${this.constructor.name}: ${this.#name}]`; }
}

class Dog extends Animal {
  #breed;

  constructor(name, breed) {
    super(name, 'Woof'); // Must call super() before accessing this
    this.#breed = breed;
  }

  fetch(item) { return `${this.name} fetches the ${item}!`; }
  get breed() { return this.#breed; }

  // Override parent method
  speak() {
    return `${super.speak()} (${this.#breed})`;
  }
}

class GuideDog extends Dog {
  #owner;
  constructor(name, breed, owner) {
    super(name, breed);
    this.#owner = owner;
  }
  guide() { return `${this.name} guides ${this.#owner}`; }
}

const d = new Dog('Rex', 'Labrador');
const g = new GuideDog('Buddy', 'Golden', 'Alice');

console.log(d.speak());   // Rex says Woof! (Labrador)
console.log(d.fetch('ball')); // Rex fetches the ball!
console.log(g.guide());   // Buddy guides Alice
console.log(g instanceof Dog);    // true
console.log(g instanceof Animal); // true
```

---

## Step 6: Symbol.iterator

```javascript
class Range {
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
        if (current <= end) {
          const value = current;
          current += step;
          return { value, done: false };
        }
        return { value: undefined, done: true };
      },
      [Symbol.iterator]() { return this; } // Iterable iterators
    };
  }
}

const range = new Range(1, 10, 2);
console.log([...range]);           // [1, 3, 5, 7, 9]
for (const n of range) process.stdout.write(n + ' '); // 1 3 5 7 9
console.log();
const [first, second, ...rest] = range;
console.log(first, second, rest); // 1 3 [5, 7, 9]
```

---

## Step 7: Mixin Pattern

```javascript
// Mixins — composing behaviors without deep inheritance
const Serializable = (Base) => class extends Base {
  serialize() { return JSON.stringify(this); }
  static deserialize(json) { return Object.assign(new this(), JSON.parse(json)); }
};

const Validatable = (Base) => class extends Base {
  validate() {
    const errors = [];
    if (this.constructor.schema) {
      for (const [field, rules] of Object.entries(this.constructor.schema)) {
        if (rules.required && !this[field]) errors.push(`${field} is required`);
        if (rules.maxLength && this[field]?.length > rules.maxLength)
          errors.push(`${field} exceeds max length`);
      }
    }
    return errors;
  }
  isValid() { return this.validate().length === 0; }
};

const Timestamped = (Base) => class extends Base {
  constructor(...args) {
    super(...args);
    this.createdAt = new Date().toISOString();
  }
};

class User extends Timestamped(Serializable(Validatable(class {}))) {
  static schema = {
    name: { required: true, maxLength: 50 },
    email: { required: true }
  };

  constructor(name, email) {
    super();
    this.name = name;
    this.email = email;
  }
}

const user = new User('Alice', 'alice@example.com');
console.log(user.isValid());  // true
console.log(typeof user.createdAt); // string
const json = user.serialize();
console.log(JSON.parse(json).name); // Alice
```

---

## Step 8: Capstone — Animal Kingdom

```javascript
class Animal {
  #name; #energy;
  constructor(name, energy = 100) {
    this.#name = name; this.#energy = energy;
  }
  eat(food) { this.#energy += 10; return `${this.#name} eats ${food}`; }
  get name() { return this.#name; }
  get energy() { return this.#energy; }
  toString() { return `[${this.constructor.name}: ${this.#name}]`; }
}
class Dog extends Animal {
  #breed;
  constructor(name, breed) { super(name); this.#breed = breed; }
  speak() { return `${this.name} barks!`; }
  [Symbol.iterator]() {
    const props = [this.name, this.#breed];
    let i = 0;
    return { next: () => i < props.length ? {value: props[i++], done: false} : {done: true} };
  }
}
const d = new Dog('Rex', 'Lab');
console.log(d.speak());
console.log([...d]);
console.log(d instanceof Animal);
```

**Run verification:**
```bash
docker run --rm node:20-alpine sh -c "node -e '
class Animal {
  #name;
  constructor(name) { this.#name = name; }
  get name() { return this.#name; }
  speak() { return \`\${this.#name} makes a sound\`; }
  static create(name) { return new Animal(name); }
}
class Dog extends Animal {
  constructor(name, breed) { super(name); this.breed = breed; }
  speak() { return \`\${this.name} barks!\`; }
  [Symbol.iterator]() {
    const props = [this.name, this.breed]; let i = 0;
    return { next: () => i < props.length ? {value: props[i++], done: false} : {done: true} };
  }
}
const d = new Dog(\"Rex\", \"Lab\");
console.log(d.speak());
console.log([...d]);
console.log(d instanceof Animal);
'"
```

📸 **Verified Output:**
```
Rex barks!
[ 'Rex', 'Lab' ]
true
```

---

## Summary

| Feature | Syntax | Notes |
|---------|--------|-------|
| Prototype chain | `Object.getPrototypeOf(obj)` | Foundation of JS inheritance |
| Object.create | `Object.create(proto)` | Pure prototypal inheritance |
| Class fields | `field = value` | Public class fields |
| Private fields | `#field` | Truly private, not accessible outside |
| Static | `static method()` | Called on class, not instances |
| Inheritance | `class B extends A` | `super()` required in constructor |
| Symbol.iterator | `[Symbol.iterator]()` | Makes objects iterable |
| Mixins | `(Base) => class extends Base` | Composable behaviors |
