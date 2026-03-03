# Lab 14: Advanced TypeScript Patterns

## Objective
Implement production TypeScript patterns: Builder, Observer, Command, Strategy, Repository with generics, type-safe event emitter, and the Fluent Builder pattern.

## Time
35 minutes

## Prerequisites
- Lab 04 (Classes), Lab 06 (Generics)

## Tools
- Docker image: `zchencow/innozverse-ts:latest`

---

## Lab Instructions

### Step 1: Fluent Builder Pattern

```typescript
// Immutable fluent builder using generics
class QueryBuilder<T extends Record<string, unknown>> {
    private conditions: string[] = [];
    private _limit?: number;
    private _offset?: number;
    private _orderBy?: { field: keyof T; direction: "ASC" | "DESC" };
    private _fields?: (keyof T)[];

    constructor(private table: string) {}

    select(...fields: (keyof T)[]): this {
        this._fields = fields;
        return this;
    }

    where(field: keyof T, op: "=" | ">" | "<" | ">=" | "<=" | "LIKE", value: unknown): this {
        this.conditions.push(`${String(field)} ${op} ${JSON.stringify(value)}`);
        return this;
    }

    limit(n: number): this { this._limit = n; return this; }
    offset(n: number): this { this._offset = n; return this; }

    orderBy(field: keyof T, direction: "ASC" | "DESC" = "ASC"): this {
        this._orderBy = { field, direction };
        return this;
    }

    build(): string {
        const fields = this._fields?.map(String).join(", ") ?? "*";
        let sql = `SELECT ${fields} FROM ${this.table}`;
        if (this.conditions.length) sql += ` WHERE ${this.conditions.join(" AND ")}`;
        if (this._orderBy) sql += ` ORDER BY ${String(this._orderBy.field)} ${this._orderBy.direction}`;
        if (this._limit)  sql += ` LIMIT ${this._limit}`;
        if (this._offset) sql += ` OFFSET ${this._offset}`;
        return sql;
    }
}

interface Product { id: number; name: string; price: number; category: string; stock: number; }

const query = new QueryBuilder<Product>("products")
    .select("id", "name", "price")
    .where("category", "=", "Laptop")
    .where("price", "<", 1000)
    .orderBy("price", "DESC")
    .limit(10)
    .offset(0)
    .build();

console.log("SQL:", query);
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
class HttpRequestBuilder {
    private url = '';
    private method = 'GET';
    private headers: Record<string,string> = {};
    private body?: string;
    setUrl(u: string): this { this.url = u; return this; }
    setMethod(m: string): this { this.method = m; return this; }
    setHeader(k: string, v: string): this { this.headers[k] = v; return this; }
    setBody(b: unknown): this { this.body = JSON.stringify(b); return this; }
    build() { return { url: this.url, method: this.method, headers: this.headers, body: this.body }; }
}
const req = new HttpRequestBuilder()
    .setUrl('https://api.example.com/products')
    .setMethod('POST')
    .setHeader('Content-Type', 'application/json')
    .setBody({ name: 'Surface Pro', price: 864 })
    .build();
console.log(req.method, req.url);
console.log('Headers:', Object.keys(req.headers).join(', '));
"
```

> 💡 **`keyof T` in Builder** ensures you can only reference actual properties of the target type. `where("invalid_column", ...)` would be a compile error. This makes the query builder safe — misspelled column names are caught at development time, not at runtime when the query fails.

**📸 Verified Output:**
```
POST https://api.example.com/products
Headers: Content-Type
```

---

### Step 2: Observer / Event Emitter Pattern

```typescript
type Listener<T> = (event: T) => void | Promise<void>;

class TypedEventEmitter<Events extends Record<string, unknown>> {
    private listeners = new Map<keyof Events, Listener<unknown>[]>();

    on<K extends keyof Events>(event: K, listener: Listener<Events[K]>): () => void {
        if (!this.listeners.has(event)) this.listeners.set(event, []);
        this.listeners.get(event)!.push(listener as Listener<unknown>);
        return () => this.off(event, listener);  // return unsubscribe function
    }

    off<K extends keyof Events>(event: K, listener: Listener<Events[K]>): void {
        const list = this.listeners.get(event);
        if (list) this.listeners.set(event, list.filter(l => l !== listener));
    }

    once<K extends keyof Events>(event: K, listener: Listener<Events[K]>): void {
        const wrapper = (e: Events[K]) => { listener(e); this.off(event, wrapper); };
        this.on(event, wrapper);
    }

    async emit<K extends keyof Events>(event: K, data: Events[K]): Promise<void> {
        const list = this.listeners.get(event) ?? [];
        await Promise.all(list.map(fn => fn(data)));
    }
}

// Typed events
type ShopEvents = {
    "product:created": { id: number; name: string; price: number };
    "order:placed":    { orderId: number; userId: number; total: number };
    "payment:success": { orderId: number; amount: number };
    "payment:failed":  { orderId: number; reason: string };
};

const emitter = new TypedEventEmitter<ShopEvents>();

const unsub = emitter.on("product:created", ({ name, price }) => {
    console.log(`New product: ${name} at $${price}`);
});

emitter.on("order:placed", async ({ orderId, total }) => {
    console.log(`Order #${orderId}: $${total}`);
});

emitter.once("payment:success", ({ orderId, amount }) => {
    console.log(`Payment received for #${orderId}: $${amount}`);
});

(async () => {
    await emitter.emit("product:created", { id: 1, name: "Surface Pro", price: 864 });
    await emitter.emit("order:placed", { orderId: 1001, userId: 1, total: 864 });
    await emitter.emit("payment:success", { orderId: 1001, amount: 864 });
    await emitter.emit("payment:success", { orderId: 1002, amount: 99 }); // once = not fired

    unsub(); // remove listener
    await emitter.emit("product:created", { id: 2, name: "Surface Pen", price: 49 }); // silent
})();
```

> 💡 **Returning an unsubscribe function** from `on()` is the modern pattern (React hooks use this). The alternative is `emitter.off(event, listener)` but it requires keeping a reference to the exact function. The returned `() => void` closure captures the reference, so callers don't need to.

**📸 Verified Output:**
```
New product: Surface Pro at $864
Order #1001: $864
Payment received for #1001: $864
```

---

### Steps 3–8: Command, Strategy, Repository, Proxy, State Machine, Capstone

```typescript
// Step 3: Command Pattern — undo/redo
interface Command {
    execute(): void;
    undo(): void;
    description: string;
}

class CommandHistory {
    private history: Command[] = [];
    private redoStack: Command[] = [];

    execute(cmd: Command): void {
        cmd.execute();
        this.history.push(cmd);
        this.redoStack = [];
        console.log(`  [exec] ${cmd.description}`);
    }

    undo(): void {
        const cmd = this.history.pop();
        if (!cmd) { console.log("  [undo] Nothing to undo"); return; }
        cmd.undo();
        this.redoStack.push(cmd);
        console.log(`  [undo] ${cmd.description}`);
    }

    redo(): void {
        const cmd = this.redoStack.pop();
        if (!cmd) { console.log("  [redo] Nothing to redo"); return; }
        cmd.execute();
        this.history.push(cmd);
        console.log(`  [redo] ${cmd.description}`);
    }
}

class TextDocument {
    private lines: string[] = [];
    addLine(text: string): void { this.lines.push(text); }
    removeLine(): string | undefined { return this.lines.pop(); }
    toString(): string { return this.lines.join("\n"); }
}

const doc = new TextDocument();
const history = new CommandHistory();

const addLine = (text: string): Command => ({
    description: `Add line: "${text}"`,
    execute: () => doc.addLine(text),
    undo: () => doc.removeLine(),
});

history.execute(addLine("Hello, TypeScript!"));
history.execute(addLine("Second line"));
history.execute(addLine("Third line"));
history.undo();
history.redo();
console.log("Document:\n" + doc.toString());

// Step 4: Strategy Pattern
interface SortStrategy<T> {
    sort(arr: T[], compareFn?: (a: T, b: T) => number): T[];
    name: string;
}

function bubbleSort<T>(): SortStrategy<T> {
    return {
        name: "BubbleSort",
        sort(arr, cmp = (a: T, b: T) => (a < b ? -1 : a > b ? 1 : 0)) {
            const result = [...arr];
            for (let i = 0; i < result.length - 1; i++)
                for (let j = 0; j < result.length - i - 1; j++)
                    if (cmp(result[j], result[j+1]) > 0)
                        [result[j], result[j+1]] = [result[j+1], result[j]];
            return result;
        }
    };
}

function nativeSort<T>(): SortStrategy<T> {
    return {
        name: "NativeSort",
        sort: (arr, cmp) => [...arr].sort(cmp),
    };
}

class Sorter<T> {
    constructor(private strategy: SortStrategy<T>) {}
    setStrategy(s: SortStrategy<T>): void { this.strategy = s; }
    sort(arr: T[], cmp?: (a: T, b: T) => number): T[] {
        console.log(`Using ${this.strategy.name}`);
        return this.strategy.sort(arr, cmp);
    }
}

const nums = [5, 2, 8, 1, 9, 3];
const sorter = new Sorter<number>(nativeSort());
console.log("Native:", sorter.sort(nums).join(", "));
sorter.setStrategy(bubbleSort());
console.log("Bubble:", sorter.sort(nums).join(", "));

// Step 5: Generic Repository with specification pattern
interface Spec<T> { isSatisfiedBy(item: T): boolean; }

class AndSpec<T> implements Spec<T> {
    constructor(private a: Spec<T>, private b: Spec<T>) {}
    isSatisfiedBy(item: T): boolean { return this.a.isSatisfiedBy(item) && this.b.isSatisfiedBy(item); }
}

class InMemoryRepo<T extends { id: number }> {
    protected items: T[] = [];
    private nextId = 1;

    add(item: Omit<T, "id">): T {
        const entity = { ...item, id: this.nextId++ } as T;
        this.items.push(entity);
        return entity;
    }

    find(spec: Spec<T>): T[] { return this.items.filter(i => spec.isSatisfiedBy(i)); }
    findAll(): T[] { return [...this.items]; }
    count(spec?: Spec<T>): number { return spec ? this.find(spec).length : this.items.length; }
}

type ProdItem = { id: number; name: string; price: number; stock: number };
const repo = new InMemoryRepo<ProdItem>();

repo.add({ name: "Surface Pro", price: 864, stock: 15 });
repo.add({ name: "Surface Pen", price: 49.99, stock: 80 });
repo.add({ name: "USB-C Hub", price: 29.99, stock: 0 });
repo.add({ name: "Office 365", price: 99.99, stock: 999 });

const inStock:   Spec<ProdItem> = { isSatisfiedBy: p => p.stock > 0 };
const affordable: Spec<ProdItem> = { isSatisfiedBy: p => p.price < 100 };
const both = new AndSpec(inStock, affordable);

console.log("\nIn stock + affordable:");
repo.find(both).forEach(p => console.log(`  ${p.name} $${p.price}`));

// Step 6: Proxy Pattern
function createLoggingProxy<T extends object>(target: T, label: string): T {
    return new Proxy(target, {
        get(obj, prop) {
            const val = (obj as Record<string | symbol, unknown>)[prop as string];
            if (typeof val === "function") {
                return (...args: unknown[]) => {
                    console.log(`[${label}] ${String(prop)}(${args.map(a => JSON.stringify(a)).join(", ")})`);
                    return val.apply(obj, args);
                };
            }
            return val;
        }
    });
}

const service = { greet: (name: string) => `Hello, ${name}!`, add: (a: number, b: number) => a + b };
const logged = createLoggingProxy(service, "Service");
console.log(logged.greet("Dr. Chen"));
console.log(logged.add(3, 4));

// Steps 7–8: Capstone — Type-safe state machine
type State = "idle" | "loading" | "success" | "error";
type Event2 =
    | { type: "FETCH"; url: string }
    | { type: "SUCCESS"; data: unknown }
    | { type: "FAILURE"; message: string }
    | { type: "RESET" };

type Transitions = {
    [S in State]?: {
        [E in Event2["type"]]?: State;
    };
};

const transitions: Transitions = {
    idle:    { FETCH: "loading" },
    loading: { SUCCESS: "success", FAILURE: "error" },
    success: { RESET: "idle", FETCH: "loading" },
    error:   { RESET: "idle", FETCH: "loading" },
};

class StateMachine {
    private state: State = "idle";
    private log: string[] = [];

    send(event: Event2): State {
        const nextState = transitions[this.state]?.[event.type];
        if (!nextState) {
            console.log(`  [ignored] ${event.type} in ${this.state}`);
            return this.state;
        }
        console.log(`  ${this.state} --[${event.type}]--> ${nextState}`);
        this.state = nextState;
        this.log.push(`${event.type}:${nextState}`);
        return this.state;
    }

    getState(): State { return this.state; }
    getLog(): string[] { return this.log; }
}

const machine = new StateMachine();
machine.send({ type: "FETCH", url: "/api/products" });
machine.send({ type: "SUCCESS", data: [{ id: 1 }] });
machine.send({ type: "FETCH", url: "/api/users" });
machine.send({ type: "FAILURE", message: "Timeout" });
machine.send({ type: "RESET" });
console.log("Final state:", machine.getState());
console.log("Log:", machine.getLog().join(", "));
```

```bash
docker run --rm zchencow/innozverse-ts:latest ts-node -e "
// Observer pattern
type Subscriber<T> = (val: T) => void;
class Subject<T> {
    private subs: Subscriber<T>[] = [];
    private _val: T;
    constructor(init: T) { this._val = init; }
    subscribe(fn: Subscriber<T>) { this.subs.push(fn); return () => { this.subs = this.subs.filter(s => s !== fn); }; }
    set value(v: T) { this._val = v; this.subs.forEach(s => s(v)); }
    get value() { return this._val; }
}
const price = new Subject(864);
const unsub = price.subscribe(v => console.log('Price changed to:', v));
price.value = 799;
price.value = 849;
unsub();
price.value = 900; // no output — unsubscribed
"
```

**📸 Verified Output:**
```
Price changed to: 799
Price changed to: 849
```

---

## Summary

TypeScript patterns elevate code quality dramatically. You've implemented a type-safe fluent QueryBuilder, typed EventEmitter with unsubscribe, Command pattern with undo/redo, Strategy pattern, Specification pattern for filtering, logging Proxy, and a typed state machine. These patterns are in Angular, NestJS, RxJS, and every large TypeScript codebase.

## Further Reading
- [TypeScript Design Patterns](https://refactoring.guru/design-patterns/typescript)
- [RxJS Observables](https://rxjs.dev)
- [XState — TypeScript state machines](https://xstate.js.org)
