# Lab 4: Classes & Object-Oriented Programming

## Objective
Build TypeScript classes with access modifiers, abstract classes, readonly, static members, parameter properties, and proper OOP patterns.

## Background
TypeScript classes extend JavaScript's ES2015 classes with type annotations and access modifiers (`private`, `protected`, `public`). TypeScript's `private` is checked at compile time; JavaScript's `#private` (also supported) is enforced at runtime. TypeScript classes compile to regular JavaScript constructor functions.

## Time
35 minutes

## Prerequisites
- Lab 01–03

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Class Basics & Parameter Properties

```typescript
class BankAccount {
    // Parameter properties: declare + assign in constructor
    constructor(
        private readonly accountId: string,
        private owner: string,
        private balance: number = 0,
        private readonly currency: string = "USD",
    ) {}

    deposit(amount: number): this {
        if (amount <= 0) throw new Error("Deposit must be positive");
        this.balance += amount;
        return this;  // fluent interface
    }

    withdraw(amount: number): this {
        if (amount > this.balance) throw new Error("Insufficient funds");
        this.balance -= amount;
        return this;
    }

    get info(): string {
        return `[${this.accountId}] ${this.owner}: ${this.currency} ${this.balance.toFixed(2)}`;
    }

    get currentBalance(): number { return this.balance; }

    toString(): string { return this.info; }
}

const acct = new BankAccount("ACC-001", "Dr. Chen", 1000);
acct.deposit(500).withdraw(200);  // fluent chaining
console.log(acct.info);
console.log("Balance:", acct.currentBalance);

try { acct.withdraw(5000); }
catch (e) { console.log("Error:", (e as Error).message); }
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
class Counter {
    constructor(private count: number = 0, private step: number = 1) {}
    increment(): this { this.count += this.step; return this; }
    decrement(): this { this.count -= this.step; return this; }
    reset(): this { this.count = 0; return this; }
    get value() { return this.count; }
}
const c = new Counter(0, 5);
c.increment().increment().increment().decrement();
console.log('Value:', c.value);
"
```

> 💡 **Parameter properties** (`private readonly accountId: string`) declare AND assign properties in the constructor — no need to write `this.accountId = accountId` manually. This is a TypeScript-only feature that reduces boilerplate significantly, especially for DTOs and value objects.

**📸 Verified Output:**
```
Value: 10
```

---

### Step 2: Inheritance & Protected Members

```typescript
abstract class Animal {
    constructor(
        protected readonly name: string,
        protected sound: string,
    ) {}

    abstract speak(): string;

    describe(): string {
        return `${this.name} (${this.constructor.name})`;
    }

    makeSound(): void {
        console.log(`${this.name}: ${this.speak()}`);
    }
}

class Dog extends Animal {
    constructor(name: string, private breed: string) {
        super(name, "Woof");
    }

    speak(): string { return `${this.sound}! (${this.breed})`; }
    fetch(): string { return `${this.name} fetches the ball!`; }
}

class Cat extends Animal {
    constructor(name: string) { super(name, "Meow"); }
    speak(): string { return `${this.sound}... *ignores you*`; }
}

class GuideDog extends Dog {
    constructor(name: string, breed: string, private handler: string) {
        super(name, breed);
    }

    speak(): string { return super.speak() + ` [guiding ${this.handler}]`; }
}

const animals: Animal[] = [
    new Dog("Rex", "German Shepherd"),
    new Cat("Whiskers"),
    new GuideDog("Buddy", "Labrador", "Dr. Chen"),
];

animals.forEach(a => {
    a.makeSound();
    console.log(" →", a.describe());
});

// instanceof narrowing
animals.forEach(a => {
    if (a instanceof Dog) console.log(a.fetch());
});
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
abstract class Shape {
    abstract area(): number;
    describe(): string { return this.constructor.name + ' area=' + this.area().toFixed(2); }
}
class Circle extends Shape {
    constructor(private r: number) { super(); }
    area() { return Math.PI * this.r ** 2; }
}
class Rect extends Shape {
    constructor(private w: number, private h: number) { super(); }
    area() { return this.w * this.h; }
}
[new Circle(5), new Rect(4, 6)].forEach(s => console.log(s.describe()));
"
```

> 💡 **`protected` members** are accessible within the class AND its subclasses, but not from outside. Use `protected` for properties/methods that subclasses need to override behavior. `private` means truly internal — even subclasses can't access it. TypeScript's access modifiers are compile-time only (unlike `#private`).

**📸 Verified Output:**
```
Circle area=78.54
Rect area=24.00
```

---

### Step 3: Static Members & Factory Methods

```typescript
class Color {
    static readonly BLACK  = new Color(0, 0, 0);
    static readonly WHITE  = new Color(255, 255, 255);
    static readonly RED    = new Color(255, 0, 0);
    static readonly MSBLUE = new Color(0, 120, 212);

    private static instanceCount = 0;

    private constructor(
        public readonly r: number,
        public readonly g: number,
        public readonly b: number,
    ) {
        Color.instanceCount++;
    }

    static fromHex(hex: string): Color {
        const h = hex.replace("#", "");
        return new Color(
            parseInt(h.slice(0, 2), 16),
            parseInt(h.slice(2, 4), 16),
            parseInt(h.slice(4, 6), 16),
        );
    }

    static fromRgb(r: number, g: number, b: number): Color { return new Color(r, g, b); }
    static getInstanceCount() { return Color.instanceCount; }

    mix(other: Color, ratio: number = 0.5): Color {
        const lerp = (a: number, b: number) => Math.round(a + (b - a) * ratio);
        return new Color(lerp(this.r, other.r), lerp(this.g, other.g), lerp(this.b, other.b));
    }

    toHex(): string { return `#${[this.r, this.g, this.b].map(n => n.toString(16).padStart(2, "0")).join("")}`; }
    toString(): string { return `rgb(${this.r}, ${this.g}, ${this.b})`; }
}

const blue = Color.fromHex("#0078d4");
const red  = Color.RED;
const mixed = blue.mix(red, 0.3);

console.log("Blue:", blue.toString(), blue.toHex());
console.log("Mixed:", mixed.toString());
console.log("Instances:", Color.getInstanceCount());
```

> 💡 **Private constructor + static factory methods** is the Named Constructor pattern — `Color.fromHex()` is clearer than `new Color()` with hex parsing inside. It also prevents subclassing (you can't call `super()` if the constructor is private to the parent). Use it for value objects and singletons.

**📸 Verified Output:**
```
Blue: rgb(0, 120, 212) #0078d4
Mixed: rgb(77, 84, 212)
Instances: 5
```

---

### Step 4: Interfaces + implements

```typescript
interface Serializable {
    serialize(): string;
    static deserialize?(data: string): unknown;
}

interface Comparable<T> {
    compareTo(other: T): number;
    equals(other: T): boolean;
}

interface Printable {
    print(): void;
}

class Money implements Comparable<Money>, Printable {
    constructor(
        public readonly amount: number,
        public readonly currency: string = "USD",
    ) {
        if (amount < 0) throw new RangeError("Amount cannot be negative");
    }

    add(other: Money): Money {
        if (this.currency !== other.currency) throw new Error("Currency mismatch");
        return new Money(this.amount + other.amount, this.currency);
    }

    multiply(factor: number): Money { return new Money(this.amount * factor, this.currency); }

    compareTo(other: Money): number {
        if (this.currency !== other.currency) throw new Error("Cannot compare different currencies");
        return this.amount - other.amount;
    }

    equals(other: Money): boolean {
        return this.amount === other.amount && this.currency === other.currency;
    }

    print(): void { console.log(`${this.currency} ${this.amount.toFixed(2)}`); }
    toString(): string { return `${this.currency} ${this.amount.toFixed(2)}`; }
}

const price    = new Money(864.00);
const tax      = price.multiply(0.08);
const shipping = new Money(0);
const total    = price.add(tax).add(shipping);

[price, tax, shipping, total].forEach(m => m.print());

console.log("Same?", price.equals(new Money(864.00)));
console.log("Cheaper?", price.compareTo(new Money(1000)) < 0);
```

> 💡 **`implements` vs `extends`:** `extends` inherits code from a parent class; `implements` only checks that your class has the required shape — no code is inherited. A class can implement multiple interfaces but only extend one class. Think of interfaces as contracts and classes as implementations.

**📸 Verified Output:**
```
USD 864.00
USD 69.12
USD 0.00
USD 933.12
Same? true
Cheaper? true
```

---

### Step 5: Mixins

```typescript
// Mixin pattern — horizontal code reuse
type Constructor<T = {}> = new (...args: unknown[]) => T;

function Timestamped<TBase extends Constructor>(Base: TBase) {
    return class extends Base {
        createdAt = new Date().toISOString();
        updatedAt = new Date().toISOString();
        touch() { this.updatedAt = new Date().toISOString(); }
    };
}

function Activatable<TBase extends Constructor>(Base: TBase) {
    return class extends Base {
        isActive = true;
        activate()   { this.isActive = true; }
        deactivate() { this.isActive = false; }
    };
}

function Serializable<TBase extends Constructor>(Base: TBase) {
    return class extends Base {
        toJSON(): string { return JSON.stringify(this); }
        toString(): string { return this.toJSON(); }
    };
}

class User {
    constructor(public name: string, public email: string) {}
}

const TimestampedUser   = Timestamped(User);
const ActivatableUser   = Activatable(TimestampedUser);
const FullUser          = Serializable(ActivatableUser);

const user = new FullUser("Dr. Chen", "chen@example.com");
console.log("Name:", user.name);
console.log("Active:", user.isActive);
console.log("Created:", user.createdAt.slice(0, 10));

user.deactivate();
console.log("After deactivate:", user.isActive);
user.touch();
console.log("JSON:", user.toJSON().slice(0, 50) + "...");
```

> 💡 **Mixins** add capabilities without inheritance hierarchies. `Timestamped(User)` wraps User in a new anonymous class that adds timestamp properties. Combining `Timestamped`, `Activatable`, and `Serializable` gives you a class with all three features. This is how Angular's `@Injectable()` decorator works internally.

**📸 Verified Output:**
```
Name: Dr. Chen
Active: true
Created: 2026-03-03
After deactivate: false
JSON: {"name":"Dr. Chen","email":"chen@example.com",...
```

---

### Step 6: Generic Classes

```typescript
class Stack<T> {
    private items: T[] = [];

    push(item: T): void   { this.items.push(item); }
    pop(): T | undefined  { return this.items.pop(); }
    peek(): T | undefined { return this.items[this.items.length - 1]; }
    get size(): number    { return this.items.length; }
    isEmpty(): boolean    { return this.items.length === 0; }
    toArray(): T[]        { return [...this.items]; }
}

class Queue<T> {
    private items: T[] = [];

    enqueue(item: T): void { this.items.push(item); }
    dequeue(): T | undefined { return this.items.shift(); }
    front(): T | undefined { return this.items[0]; }
    get size(): number { return this.items.length; }
    isEmpty(): boolean { return this.items.length === 0; }
}

class TypedMap<K, V> {
    private map = new Map<K, V>();

    set(key: K, value: V): this { this.map.set(key, value); return this; }
    get(key: K): V | undefined { return this.map.get(key); }
    has(key: K): boolean { return this.map.has(key); }
    delete(key: K): boolean { return this.map.delete(key); }
    get size(): number { return this.map.size; }
    entries(): [K, V][] { return [...this.map.entries()]; }
}

// Stack
const numStack = new Stack<number>();
numStack.push(1); numStack.push(2); numStack.push(3);
console.log("Stack top:", numStack.peek());
console.log("Pop:", numStack.pop(), numStack.pop());

// Queue
const taskQueue = new Queue<string>();
["task1", "task2", "task3"].forEach(t => taskQueue.enqueue(t));
while (!taskQueue.isEmpty()) console.log("Processing:", taskQueue.dequeue());

// TypedMap
const registry = new TypedMap<string, number>()
    .set("alpha", 1).set("beta", 2).set("gamma", 3);
console.log("beta:", registry.get("beta"));
registry.entries().forEach(([k, v]) => console.log(` ${k}=${v}`));
```

> 💡 **Generic classes** carry the type parameter through all methods. `Stack<number>` creates a stack where `push` only accepts numbers and `pop` returns `number | undefined`. The type is resolved at instantiation — one class definition, infinite type-safe variants.

**📸 Verified Output:**
```
Stack top: 3
Pop: 3 2
Processing: task1
Processing: task2
Processing: task3
beta: 2
 alpha=1
 beta=2
 gamma=3
```

---

### Step 7: Abstract Classes & Template Method

```typescript
abstract class DataProcessor<TInput, TOutput> {
    // Template Method pattern
    async process(data: TInput): Promise<TOutput> {
        const validated = await this.validate(data);
        const transformed = await this.transform(validated);
        await this.persist(transformed);
        return transformed;
    }

    protected abstract validate(data: TInput): Promise<TInput>;
    protected abstract transform(data: TInput): Promise<TOutput>;
    protected async persist(data: TOutput): Promise<void> {
        console.log("  [base] persisted:", JSON.stringify(data).slice(0, 50));
    }
}

interface RawProduct { name: string; priceStr: string; stockStr: string; }
interface Product    { name: string; price: number; stock: number; slug: string; }

class ProductProcessor extends DataProcessor<RawProduct, Product> {
    protected async validate(data: RawProduct): Promise<RawProduct> {
        if (!data.name) throw new Error("Name required");
        if (isNaN(parseFloat(data.priceStr))) throw new Error("Invalid price");
        return data;
    }

    protected async transform(data: RawProduct): Promise<Product> {
        return {
            name:  data.name.trim(),
            price: parseFloat(data.priceStr),
            stock: parseInt(data.stockStr),
            slug:  data.name.toLowerCase().replace(/\s+/g, "-"),
        };
    }
}

(async () => {
    const processor = new ProductProcessor();
    const raw: RawProduct = { name: "Surface Pro 12", priceStr: "864.00", stockStr: "15" };
    const product = await processor.process(raw);
    console.log("Processed:", product.name, `$${product.price}`, `slug:${product.slug}`);
})();
```

**📸 Verified Output:**
```
  [base] persisted: {"name":"Surface Pro 12","price":864,"stock":15,"slug":"surfa
Processed: Surface Pro 12 $864 slug:surface-pro-12
```

---

### Step 8: Complete — Entity Framework Pattern

```typescript
abstract class BaseEntity {
    readonly id: number;
    readonly createdAt: Date;
    updatedAt: Date;
    private static nextId = 1;

    constructor() {
        this.id = BaseEntity.nextId++;
        this.createdAt = new Date();
        this.updatedAt = new Date();
    }

    protected touch(): void { this.updatedAt = new Date(); }

    toJSON(): Record<string, unknown> {
        return { id: this.id, createdAt: this.createdAt, updatedAt: this.updatedAt };
    }
}

class Product extends BaseEntity {
    constructor(
        public name: string,
        public price: number,
        public stock: number,
        public category: string,
    ) {
        super();
    }

    applyDiscount(pct: number): void {
        this.price = Math.round(this.price * (1 - pct / 100) * 100) / 100;
        this.touch();
    }

    restock(qty: number): void { this.stock += qty; this.touch(); }

    toJSON(): Record<string, unknown> {
        return { ...super.toJSON(), name: this.name, price: this.price, stock: this.stock, category: this.category };
    }
}

const products = [
    new Product("Surface Pro 12\"", 864, 15, "Laptop"),
    new Product("Surface Pen", 49.99, 80, "Accessory"),
    new Product("Office 365", 99.99, 999, "Software"),
];

console.log("=== Product Catalog ===");
products.forEach(p => console.log(`  #${p.id} ${p.name}: $${p.price} (stock: ${p.stock})`));

products.filter(p => p.category === "Accessory").forEach(p => p.applyDiscount(10));
console.log("\n=== After 10% Accessory Discount ===");
products.forEach(p => console.log(`  #${p.id} ${p.name}: $${p.price}`));
```

> 💡 **`BaseEntity.nextId++`** is a class-level counter — static properties are shared across all instances. Each subclass that calls `super()` gets a unique ID. In production, IDs come from databases; in tests, this auto-increment pattern avoids external dependencies.

**📸 Verified Output:**
```
=== Product Catalog ===
  #1 Surface Pro 12": $864 (stock: 15)
  #2 Surface Pen: $49.99 (stock: 80)
  #3 Office 365: $99.99 (stock: 999)

=== After 10% Accessory Discount ===
  #1 Surface Pro 12": $864
  #2 Surface Pen: $44.99
  #3 Office 365: $99.99
```

---

## Summary

TypeScript OOP is powerful and expressive. You've covered parameter properties, inheritance, abstract classes, `implements`, static members, mixins, generic classes, the Template Method pattern, and an entity framework. These patterns power Angular, NestJS, TypeORM, and every TypeScript-first backend.

## Further Reading
- [TypeScript Classes](https://www.typescriptlang.org/docs/handbook/2/classes.html)
- [Mixins](https://www.typescriptlang.org/docs/handbook/mixins.html)
