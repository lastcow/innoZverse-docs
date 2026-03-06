# Lab 04: Decorators

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Class, method, property, and parameter decorators. Decorator factories. Real-world logging and validation decorators.

---

## Step 1: Setup with experimentalDecorators

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab04 && cd /lab04
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "moduleResolution": "node",
    "strict": true,
    "esModuleInterop": true,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": false
  }
}
EOF
```

> 💡 `experimentalDecorators: true` enables the legacy Stage 2 decorator syntax. TypeScript 5.0+ also supports the new TC39 Stage 3 decorators, but `experimentalDecorators` remains widely used.

---

## Step 2: Class Decorator

```typescript
// class-decorator.ts
function Sealed(constructor: Function): void {
  Object.seal(constructor);
  Object.seal(constructor.prototype);
}

function Singleton<T extends { new(...args: any[]): {} }>(constructor: T) {
  let instance: InstanceType<T> | null = null;
  return class extends constructor {
    constructor(...args: any[]) {
      super(...args);
      if (instance) return instance;
      instance = this as any;
    }
  } as T;
}

@Sealed
class Config {
  host = 'localhost';
  port = 3000;
}

@Singleton
class Database {
  id = Math.random();
  connect(): string { return `Connected (${this.id.toFixed(4)})`; }
}

const db1 = new Database();
const db2 = new Database();
console.log(db1 === db2);       // true
console.log(db1.connect());
```

---

## Step 3: Method Decorator

```typescript
function Log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const original = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`[LOG] ${propertyKey}(${args.join(', ')})`);
    const result = original.apply(this, args);
    console.log(`[LOG] ${propertyKey} => ${JSON.stringify(result)}`);
    return result;
  };
  return descriptor;
}

function Memoize(target: any, key: string, desc: PropertyDescriptor) {
  const cache = new Map<string, any>();
  const orig = desc.value;
  desc.value = function (...args: any[]) {
    const k = JSON.stringify(args);
    if (cache.has(k)) { console.log(`[CACHE] ${key} hit`); return cache.get(k); }
    const result = orig.apply(this, args);
    cache.set(k, result);
    return result;
  };
}

class MathService {
  @Log
  add(a: number, b: number): number { return a + b; }

  @Memoize
  fibonacci(n: number): number {
    if (n <= 1) return n;
    return this.fibonacci(n - 1) + this.fibonacci(n - 2);
  }
}

const svc = new MathService();
svc.add(3, 4);
const fib = svc.fibonacci(10);
console.log('fib(10):', fib);
```

---

## Step 4: Property Decorator

```typescript
function Validate(min: number, max: number) {
  return function (target: any, propertyKey: string) {
    let value: number;
    Object.defineProperty(target, propertyKey, {
      get() { return value; },
      set(newVal: number) {
        if (newVal < min || newVal > max) {
          throw new RangeError(`${propertyKey} must be between ${min} and ${max}`);
        }
        value = newVal;
      },
      enumerable: true,
      configurable: true,
    });
  };
}

function ReadOnly(target: any, key: string) {
  Object.defineProperty(target, key, {
    writable: false,
    configurable: false,
  });
}

class Person {
  @Validate(0, 150)
  age!: number;

  constructor(public name: string, age: number) {
    this.age = age;
  }
}

const p = new Person('Alice', 30);
console.log(p.age);  // 30
try {
  p.age = 200;       // throws RangeError
} catch (e: any) {
  console.log(e.message);
}
```

---

## Step 5: Parameter Decorator

```typescript
const paramMetadata = new Map<string, number[]>();

function Required(target: any, methodKey: string, paramIndex: number) {
  const existing = paramMetadata.get(methodKey) ?? [];
  existing.push(paramIndex);
  paramMetadata.set(methodKey, existing);
}

function ValidateParams(target: any, key: string, desc: PropertyDescriptor) {
  const orig = desc.value;
  desc.value = function (...args: any[]) {
    const required = paramMetadata.get(key) ?? [];
    for (const idx of required) {
      if (args[idx] === null || args[idx] === undefined) {
        throw new Error(`Parameter at index ${idx} of '${key}' is required`);
      }
    }
    return orig.apply(this, args);
  };
}

class UserService {
  @ValidateParams
  createUser(@Required name: string, @Required email: string, bio?: string): string {
    return `Created: ${name} <${email}>`;
  }
}

const us = new UserService();
console.log(us.createUser('Alice', 'alice@example.com'));
try {
  us.createUser('Bob', null as any);
} catch (e: any) {
  console.log(e.message);
}
```

---

## Step 6: Decorator Factories

```typescript
// Decorator factory = function that returns a decorator
function Throttle(ms: number) {
  return function (target: any, key: string, desc: PropertyDescriptor) {
    const orig = desc.value;
    let lastCall = 0;
    desc.value = function (...args: any[]) {
      const now = Date.now();
      if (now - lastCall < ms) {
        console.log(`[THROTTLE] ${key} throttled`);
        return;
      }
      lastCall = now;
      return orig.apply(this, args);
    };
  };
}

function Retry(times: number) {
  return function (target: any, key: string, desc: PropertyDescriptor) {
    const orig = desc.value;
    desc.value = async function (...args: any[]) {
      for (let i = 0; i < times; i++) {
        try { return await orig.apply(this, args); }
        catch (e) {
          if (i === times - 1) throw e;
          console.log(`[RETRY] ${key} attempt ${i + 1} failed`);
        }
      }
    };
  };
}

class ApiService {
  @Throttle(1000)
  search(query: string): void {
    console.log(`Searching: ${query}`);
  }
}

const api = new ApiService();
api.search('typescript');
api.search('decorators');  // throttled
```

---

## Step 7: Real-World Logging Decorator

```typescript
type LogLevel = 'debug' | 'info' | 'warn' | 'error';

function Logger(level: LogLevel = 'info') {
  return function (target: any, key: string, desc: PropertyDescriptor) {
    const orig = desc.value;
    const className = target.constructor.name;
    desc.value = async function (...args: any[]) {
      const start = Date.now();
      console.log(`[${level.toUpperCase()}] ${className}.${key} called`);
      try {
        const result = await orig.apply(this, args);
        const dur = Date.now() - start;
        console.log(`[${level.toUpperCase()}] ${className}.${key} completed in ${dur}ms`);
        return result;
      } catch (err: any) {
        console.log(`[ERROR] ${className}.${key} failed: ${err.message}`);
        throw err;
      }
    };
  };
}

class OrderService {
  @Logger('info')
  async processOrder(orderId: string): Promise<string> {
    await new Promise(r => setTimeout(r, 10));
    return `Order ${orderId} processed`;
  }
}

const os = new OrderService();
os.processOrder('ORD-001').then(console.log);
```

---

## Step 8: Capstone — Full Decorator Suite

```typescript
// Save as lab04-capstone.ts
function Log(target: any, key: string, desc: PropertyDescriptor) {
  const orig = desc.value;
  desc.value = function (...args: any[]) {
    console.log(`Calling ${key} with`, args);
    const result = orig.apply(this, args);
    console.log(`${key} returned`, result);
    return result;
  };
}

function Sealed(constructor: Function): void {
  Object.seal(constructor);
  Object.seal(constructor.prototype);
}

@Sealed
class Calculator {
  @Log
  add(a: number, b: number): number { return a + b; }

  @Log
  multiply(a: number, b: number): number { return a * b; }
}

const calc = new Calculator();
calc.add(3, 4);
calc.multiply(5, 6);
console.log('Decorators OK');
```

Run:
```bash
ts-node -P tsconfig.json lab04-capstone.ts
```

📸 **Verified Output:**
```
Calling add with [ 3, 4 ]
add returned 7
Calling multiply with [ 5, 6 ]
multiply returned 30
Decorators OK
```

---

## Summary

| Decorator Type | Signature | Use Case |
|----------------|-----------|----------|
| Class | `(constructor: Function)` | Seal, Singleton, metadata |
| Method | `(target, key, descriptor)` | Logging, caching, throttle |
| Property | `(target, key)` | Validation, readonly |
| Parameter | `(target, key, index)` | Validation metadata |
| Factory | `(options) => decorator` | Configurable decorators |
