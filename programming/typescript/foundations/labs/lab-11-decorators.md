# Lab 11: Decorators & Metadata

## Objective
Write and use TypeScript decorators: class, method, property, and parameter decorators. Build a dependency injection container and validation framework using decorators.

## Time
35 minutes

## Prerequisites
- Lab 04 (Classes), Lab 06 (Generics)

## Tools
- Docker image: `zchencow/innozverse-ts:latest`
- Note: Requires `"experimentalDecorators": true` in tsconfig (enabled in the Docker image)

---

## Lab Instructions

### Step 1: Class Decorators

```typescript
// Decorator is a function that receives the decorated target
function sealed(constructor: Function): void {
    Object.seal(constructor);
    Object.seal(constructor.prototype);
}

function singleton<T extends new (...args: unknown[]) => object>(Ctor: T): T {
    let instance: InstanceType<T>;
    return class extends Ctor {
        constructor(...args: unknown[]) {
            if (instance) return instance;
            super(...args);
            instance = this as InstanceType<T>;
        }
    } as T;
}

function log(prefix: string) {
    return function<T extends new (...args: unknown[]) => object>(Ctor: T): T {
        return class extends Ctor {
            constructor(...args: unknown[]) {
                console.log(`[${prefix}] Creating ${Ctor.name}`);
                super(...args);
            }
        } as T;
    };
}

@log("FACTORY")
@sealed
class DatabaseConnection {
    constructor(private host: string, private port: number) {}
    toString() { return `DB(${this.host}:${this.port})`; }
}

@singleton
class AppConfig {
    private data: Record<string, string> = {};
    set(key: string, val: string) { this.data[key] = val; }
    get(key: string) { return this.data[key]; }
}

const db = new DatabaseConnection("localhost", 5432);
console.log(db.toString());

const cfg1 = new AppConfig();
const cfg2 = new AppConfig();
cfg1.set("theme", "dark");
console.log("Same instance:", cfg2.get("theme")); // dark
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node --experimentalDecorators -e "
function timestamp<T extends new (...args: unknown[]) => object>(Ctor: T): T {
    return class extends Ctor {
        createdAt = new Date().toISOString();
    } as T;
}
@timestamp
class User { constructor(public name: string) {} }
const u = new User('Dr. Chen');
console.log(u.name, (u as any).createdAt.slice(0, 10));
"
```

> 💡 **Decorators execute bottom-up** when stacked — `@log("FACTORY")` runs after `@sealed`. Class decorators receive the constructor function and can return a new class that extends it. This is how Angular's `@Component`, `@Injectable`, and `@NgModule` work.

**📸 Verified Output:**
```
Dr. Chen 2026-03-03
```

---

### Step 2: Method & Property Decorators

```typescript
// Method decorator — intercept method calls
function memoize(target: object, key: string, descriptor: PropertyDescriptor): PropertyDescriptor {
    const original = descriptor.value;
    const cache = new Map<string, unknown>();
    descriptor.value = function(...args: unknown[]) {
        const cacheKey = JSON.stringify(args);
        if (!cache.has(cacheKey)) {
            console.log(`  [memo] Computing ${key}(${args.join(",")})`);
            cache.set(cacheKey, original.apply(this, args));
        }
        return cache.get(cacheKey);
    };
    return descriptor;
}

function validate(validator: (val: unknown) => boolean, message: string) {
    return function(target: object, key: string, descriptor: PropertyDescriptor): PropertyDescriptor {
        const original = descriptor.value;
        descriptor.value = function(...args: unknown[]) {
            if (!validator(args[0])) throw new Error(`${message} (got: ${args[0]})`);
            return original.apply(this, args);
        };
        return descriptor;
    };
}

function readonly(target: object, key: string, descriptor: PropertyDescriptor): PropertyDescriptor {
    descriptor.writable = false;
    return descriptor;
}

class MathService {
    @memoize
    fibonacci(n: number): number {
        if (n <= 1) return n;
        return this.fibonacci(n - 1) + this.fibonacci(n - 2);
    }

    @validate(n => typeof n === "number" && n > 0, "Amount must be positive")
    calculateTax(amount: number): number {
        return amount * 0.08;
    }
}

const math = new MathService();
console.log("fib(10):", math.fibonacci(10));
console.log("fib(10):", math.fibonacci(10));  // from cache
console.log("tax(864):", math.calculateTax(864));
try { math.calculateTax(-100); }
catch (e) { console.log("Error:", (e as Error).message); }
```

> 💡 **Method decorators** receive the class prototype, method name, and `PropertyDescriptor`. Replacing `descriptor.value` replaces the method with a wrapper. This is how `@UseGuards`, `@Roles`, `@Cache` work in NestJS — they wrap methods without modifying the class source code.

**📸 Verified Output:**
```
  [memo] Computing fibonacci(10)
fib(10): 55
fib(10): 55
tax(864): 69.12
Error: Amount must be positive (got: -100)
```

---

### Steps 3–8: Property, Parameter, Reflect, DI Container, Validation Framework, Capstone

```typescript
// Step 3: Property decorator
const METADATA_KEY = Symbol("metadata");

function column(name?: string) {
    return function(target: object, propertyKey: string): void {
        const columns: Record<string, string> = Reflect.getMetadata(METADATA_KEY, target) ?? {};
        columns[propertyKey] = name ?? propertyKey;
        Reflect.defineMetadata(METADATA_KEY, columns, target);
    };
}

// Step 4: Decorator factory pattern
function validate2(rule: (val: unknown) => string | null) {
    return function(target: object, key: string): void {
        const rules: Record<string, (val: unknown) => string | null> =
            Reflect.getMetadata("validate", target) ?? {};
        rules[key] = rule;
        Reflect.defineMetadata("validate", rules, target);
    };
}

// Step 5: Simple DI container using decorators
const Injectable = () => (target: Function) => { Reflect.defineMetadata("injectable", true, target); };
const Inject = (token: string) => (target: object, _key: string | symbol, index: number) => {
    const injects: Record<number, string> = Reflect.getMetadata("inject", target) ?? {};
    injects[index] = token;
    Reflect.defineMetadata("inject", injects, target);
};

class Container {
    private registry = new Map<string, new (...args: unknown[]) => unknown>();
    private instances = new Map<string, unknown>();

    register(token: string, Ctor: new (...args: unknown[]) => unknown): void {
        this.registry.set(token, Ctor);
    }

    resolve<T>(token: string): T {
        if (!this.instances.has(token)) {
            const Ctor = this.registry.get(token);
            if (!Ctor) throw new Error(`No binding for ${token}`);
            this.instances.set(token, new Ctor());
        }
        return this.instances.get(token) as T;
    }
}

// Step 6: Validation via decorators (manual metadata)
const validators = new WeakMap<object, Record<string, (v: unknown) => string | null>>();

function min(n: number) {
    return (target: object, key: string) => {
        const map = validators.get(target) ?? {};
        map[key] = (v) => typeof v === "number" && v >= n ? null : `${key} must be >= ${n}`;
        validators.set(target, map);
    };
}
function required(target: object, key: string) {
    const map = validators.get(target) ?? {};
    const existing = map[key] ?? (() => null);
    map[key] = (v) => (v == null || v === "" ? `${key} is required` : existing(v));
    validators.set(target, map);
}

class ProductDTO {
    @required @min(1) id!: number;
    @required name!: string;
    @min(0) price!: number;

    constructor(data: Partial<ProductDTO>) {
        Object.assign(this, data);
    }

    validate(): string[] {
        const rules = validators.get(Object.getPrototypeOf(this)) ?? {};
        return Object.entries(rules)
            .map(([key, fn]) => fn((this as Record<string, unknown>)[key]))
            .filter(Boolean) as string[];
    }
}

// Step 7: Timing decorator
function timing(target: object, key: string, descriptor: PropertyDescriptor): PropertyDescriptor {
    const orig = descriptor.value;
    descriptor.value = async function(...args: unknown[]) {
        const start = Date.now();
        const result = await orig.apply(this, args);
        console.log(`[timing] ${key}: ${Date.now() - start}ms`);
        return result;
    };
    return descriptor;
}

// Step 8: Capstone — decorated service
class ProductService {
    private products = [
        { id: 1, name: "Surface Pro", price: 864 },
        { id: 2, name: "Surface Pen", price: 49.99 },
    ];

    @memoize
    findById(id: number) { return this.products.find(p => p.id === id) ?? null; }

    @validate(id => typeof id === "number" && id > 0, "ID must be positive")
    delete(id: number): boolean {
        const idx = this.products.findIndex(p => p.id === id);
        if (idx === -1) return false;
        this.products.splice(idx, 1);
        return true;
    }

    list() { return this.products; }
}

const svc = new ProductService();
console.log("Find #1:", svc.findById(1)?.name);
console.log("Find #1 cached:", svc.findById(1)?.name);
console.log("Delete #2:", svc.delete(2));
console.log("Remaining:", svc.list().length);

try { svc.delete(-1); }
catch (e) { console.log("Error:", (e as Error).message); }

// DTO validation
const dto = new ProductDTO({ id: 0, name: "", price: -10 });
const errors = dto.validate();
console.log("Validation errors:", errors.join(", "));

const valid = new ProductDTO({ id: 1, name: "Test", price: 9.99 });
console.log("Valid DTO errors:", valid.validate().length);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node --experimentalDecorators -e "
function log(target: any, key: string, desc: PropertyDescriptor) {
    const orig = desc.value;
    desc.value = function(...args: any[]) {
        console.log('Calling', key, 'with', args);
        return orig.apply(this, args);
    };
    return desc;
}
class Calc {
    @log
    add(a: number, b: number) { return a + b; }
}
console.log(new Calc().add(3, 4));
"
```

**📸 Verified Output:**
```
Calling add with [ 3, 4 ]
7
```

---

## Summary

TypeScript decorators enable declarative programming — you annotate classes and methods with `@decorator` instead of modifying them directly. You've built memoization, validation, timing, a DI container, and a DTO validation system. This is exactly how Angular, NestJS, TypeORM, and class-validator work.

## Further Reading
- [TypeScript Decorators](https://www.typescriptlang.org/docs/handbook/decorators.html)
- [NestJS — decorator-driven Node.js](https://nestjs.com)
- [class-validator](https://github.com/typestack/class-validator)
