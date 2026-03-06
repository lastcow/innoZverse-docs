# Lab 08: Advanced Classes

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Abstract classes, access modifiers, parameter properties, override keyword, class expressions, mixins pattern.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab08 && cd /lab08
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true
  }
}
EOF
```

---

## Step 2: Abstract Classes

```typescript
// Abstract classes cannot be instantiated directly
abstract class Animal {
  constructor(public readonly name: string) {}
  
  // Abstract method — subclass MUST implement
  abstract sound(): string;
  abstract move(): string;
  
  // Concrete method — shared behavior
  describe(): string {
    return `${this.name} goes ${this.sound()} and ${this.move()}`;
  }
}

class Dog extends Animal {
  sound(): string { return 'Woof'; }
  move(): string { return 'runs'; }
}

class Bird extends Animal {
  sound(): string { return 'Tweet'; }
  move(): string { return 'flies'; }
}

// const a = new Animal('test'); // Error! Cannot instantiate abstract class
const dog = new Dog('Rex');
const bird = new Bird('Tweety');
console.log(dog.describe());   // Rex goes Woof and runs
console.log(bird.describe());  // Tweety goes Tweet and flies
```

---

## Step 3: Access Modifiers

```typescript
class BankAccount {
  public readonly id: string;          // readable anywhere, immutable
  public owner: string;                // readable/writable anywhere
  protected balance: number;           // accessible in class + subclasses
  private _transactions: string[] = []; // only in this class
  #pin: number;                        // JS private field (truly private)

  constructor(owner: string, initialBalance: number, pin: number) {
    this.id = Math.random().toString(36).slice(2);
    this.owner = owner;
    this.balance = initialBalance;
    this.#pin = pin;
  }

  deposit(amount: number): void {
    this.balance += amount;
    this._transactions.push(`+${amount}`);
  }

  getBalance(pin: number): number {
    if (pin !== this.#pin) throw new Error('Invalid PIN');
    return this.balance;
  }

  getHistory(): string[] { return [...this._transactions]; }
}

class SavingsAccount extends BankAccount {
  private interestRate: number;

  constructor(owner: string, balance: number, pin: number, rate: number) {
    super(owner, balance, pin);
    this.interestRate = rate;
  }

  addInterest(): void {
    const interest = this.balance * this.interestRate;  // protected access
    this.deposit(interest);
    console.log(`Interest added: ${interest.toFixed(2)}`);
  }
}

const acct = new SavingsAccount('Alice', 1000, 1234, 0.05);
acct.deposit(500);
acct.addInterest();
console.log('Balance:', acct.getBalance(1234));
console.log('History:', acct.getHistory());
```

---

## Step 4: Parameter Properties

```typescript
// Shorthand: declare AND assign in constructor
class Point {
  constructor(
    public readonly x: number,
    public readonly y: number,
  ) {}

  distanceTo(other: Point): number {
    return Math.sqrt((this.x - other.x) ** 2 + (this.y - other.y) ** 2);
  }

  toString(): string { return `(${this.x}, ${this.y})`; }
}

class Rectangle {
  constructor(
    private readonly origin: Point,
    public readonly width: number,
    public readonly height: number,
  ) {}

  area(): number { return this.width * this.height; }
  perimeter(): number { return 2 * (this.width + this.height); }
}

const p1 = new Point(0, 0);
const p2 = new Point(3, 4);
console.log(`Distance: ${p1.distanceTo(p2)}`);  // 5

const rect = new Rectangle(p1, 4, 6);
console.log(`Area: ${rect.area()}, Perimeter: ${rect.perimeter()}`);
```

---

## Step 5: Override Keyword

```typescript
class Shape {
  area(): number { return 0; }
  toString(): string { return `Shape(area=${this.area()})`; }
}

class Circle extends Shape {
  constructor(private radius: number) { super(); }
  
  override area(): number { return Math.PI * this.radius ** 2; }
  override toString(): string { return `Circle(r=${this.radius}, area=${this.area().toFixed(2)})`; }
}

class Square extends Shape {
  constructor(private side: number) { super(); }
  
  override area(): number { return this.side ** 2; }
}

// override keyword ensures the method exists in parent
// If parent doesn't have the method, TypeScript errors

const shapes: Shape[] = [new Circle(5), new Square(4)];
shapes.forEach(s => console.log(s.toString()));
```

---

## Step 6: Mixins Pattern

```typescript
// Mixin: a class factory that adds behavior
type Constructor<T = {}> = new (...args: any[]) => T;

function Timestamped<Base extends Constructor>(base: Base) {
  return class extends base {
    createdAt = new Date();
    updatedAt = new Date();
    touch(): void { this.updatedAt = new Date(); }
  };
}

function Activatable<Base extends Constructor>(base: Base) {
  return class extends base {
    isActive = false;
    activate(): void { this.isActive = true; }
    deactivate(): void { this.isActive = false; }
  };
}

function Serializable<Base extends Constructor>(base: Base) {
  return class extends base {
    serialize(): string { return JSON.stringify(this); }
    static deserialize<T>(json: string): T { return JSON.parse(json) as T; }
  };
}

class User {
  constructor(public name: string, public email: string) {}
}

// Combine mixins
const TimestampedActivatableUser = Timestamped(Activatable(Serializable(User)));

const user = new TimestampedActivatableUser('Alice', 'alice@example.com');
user.activate();
user.touch();

console.log(user.name, user.isActive);
console.log(user.serialize());
```

---

## Step 7: Class Expressions

```typescript
// Classes as values
const createValidator = (pattern: RegExp) =>
  class {
    validate(s: string): boolean { return pattern.test(s); }
    message = `Must match ${pattern.source}`;
  };

const EmailValidator = createValidator(/^[^@]+@[^@]+\.[^@]+$/);
const PhoneValidator = createValidator(/^\+?[\d\s-]{7,15}$/);

const ev = new EmailValidator();
console.log(ev.validate('user@example.com'));  // true
console.log(ev.validate('invalid'));           // false

// Self-referential class type
function withId<T extends Constructor>(base: T) {
  return class extends base {
    readonly id: string = Math.random().toString(36).slice(2);
  };
}

const IdUser = withId(User);
const u = new IdUser('Bob', 'bob@example.com');
console.log(u.id, u.name);
```

---

## Step 8: Capstone — Animal Kingdom

```typescript
// Save as lab08-capstone.ts
abstract class Animal {
  abstract sound(): string;
  describe(): string { return `I make sound: ${this.sound()}`; }
}

class Dog extends Animal {
  sound(): string { return 'Woof'; }
}

type Constructor<T = {}> = new (...args: any[]) => T;
function Serializable<Base extends Constructor>(base: Base) {
  return class extends base {
    serialize(): string { return JSON.stringify(this); }
  };
}

class Point {
  constructor(public x: number, public y: number) {}
}

const SerializablePoint = Serializable(Point);
const sp = new SerializablePoint(1, 2);

const dog = new Dog();
console.log(dog.describe());
console.log(sp.serialize());
console.log('Classes OK');
```

Run:
```bash
ts-node -P tsconfig.json lab08-capstone.ts
```

📸 **Verified Output:**
```
I make sound: Woof
{"x":1,"y":2}
Classes OK
```

---

## Summary

| Feature | Syntax | Purpose |
|---------|--------|---------|
| Abstract class | `abstract class A` | Force subclass to implement |
| Abstract method | `abstract fn(): T` | Must be overridden |
| Public | `public x` | Default, accessible anywhere |
| Protected | `protected x` | Class + subclasses |
| Private | `private x` | Class only (TS-level) |
| JS Private | `#x` | Truly private (runtime) |
| Readonly | `readonly x` | Immutable after init |
| Parameter property | `constructor(public x: T)` | Declare + assign shorthand |
| Override | `override fn()` | Ensure parent has method |
| Mixin | `function M<B>(base: B)` | Composable class behaviors |
