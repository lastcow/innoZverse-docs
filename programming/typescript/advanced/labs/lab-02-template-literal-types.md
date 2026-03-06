# Lab 02: Template Literal Types

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Template literal type interpolation, string intrinsic types, extracting parts with `infer`, typed event names, CSS property type safety.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab-adv02 && cd /lab-adv02
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

## Step 2: Basic Template Literal Types

```typescript
// Combine string literal types
type Greeting = `Hello, ${string}!`;
const g: Greeting = 'Hello, World!';

// Cross-product of unions
type Color = 'red' | 'green' | 'blue';
type Shade = 'light' | 'dark';
type ColorShade = `${Shade}-${Color}`;
// 'light-red' | 'light-green' | 'light-blue' | 'dark-red' | ...

// Event handler names
type EventName = 'click' | 'focus' | 'blur' | 'change';
type Handler = `on${Capitalize<EventName>}`;
// 'onClick' | 'onFocus' | 'onBlur' | 'onChange'

type Getter<T extends string> = `get${Capitalize<T>}`;
type Setter<T extends string> = `set${Capitalize<T>}`;

type NameAccessors = Getter<'name'> | Setter<'name'>;
// 'getName' | 'setName'

const shade: ColorShade = 'dark-blue';
const handler: Handler = 'onClick';
const accessor: NameAccessors = 'getName';
console.log(shade, handler, accessor);
```

---

## Step 3: String Intrinsic Utilities

```typescript
// Built-in string manipulation types
type Upper = Uppercase<'hello world'>;        // 'HELLO WORLD'
type Lower = Lowercase<'HELLO WORLD'>;        // 'hello world'
type Cap   = Capitalize<'hello world'>;       // 'Hello world'
type Uncap = Uncapitalize<'Hello World'>;     // 'hello World'

// Combine with generics
function toUpperCaseKey<T extends string>(key: T): Uppercase<T> {
  return key.toUpperCase() as Uppercase<T>;
}

function toCamelCase<T extends string>(s: T): Uncapitalize<T> {
  const r = s.charAt(0).toLowerCase() + s.slice(1);
  return r as Uncapitalize<T>;
}

console.log(toUpperCaseKey('hello'));   // HELLO
console.log(toCamelCase('HelloWorld')); // helloWorld

// Generate SCREAMING_SNAKE_CASE
type ToSnakeCase<S extends string> =
  S extends `${infer Head}${infer Tail}`
    ? Head extends Uppercase<Head>
      ? `_${Lowercase<Head>}${ToSnakeCase<Tail>}`
      : `${Head}${ToSnakeCase<Tail>}`
    : S;

type Snaked = ToSnakeCase<'helloWorld'>;  // 'hello_world'
type Snaked2 = ToSnakeCase<'myEventName'>; // 'my_event_name'
```

---

## Step 4: Extracting Parts with infer

```typescript
// Extract prefix/suffix
type ExtractAfter<S extends string, Prefix extends string> =
  S extends `${Prefix}${infer Rest}` ? Rest : never;

type ExtractBefore<S extends string, Suffix extends string> =
  S extends `${infer Before}${Suffix}` ? Before : never;

type AfterOn = ExtractAfter<'onClick', 'on'>;    // 'Click'
type BeforeClick = ExtractBefore<'onClick', 'Click'>; // 'on'

// Extract route parameters
type RouteParams<T extends string> =
  T extends `${string}:${infer Param}/${infer Rest}`
    ? Param | RouteParams<`/${Rest}`>
    : T extends `${string}:${infer Param}`
      ? Param
      : never;

type UserParams = RouteParams<'/users/:userId/posts/:postId'>;
// 'userId' | 'postId'

type ArticleParams = RouteParams<'/blog/:year/:month/:slug'>;
// 'year' | 'month' | 'slug'

// Type-safe route builder
function buildRoute<T extends string>(
  template: T,
  params: Record<RouteParams<T>, string | number>
): string {
  let result: string = template;
  for (const [key, val] of Object.entries(params)) {
    result = result.replace(`:${key}`, String(val));
  }
  return result;
}

const url = buildRoute('/users/:userId/posts/:postId', {
  userId: 42,
  postId: 'hello-world',
});
console.log(url); // /users/42/posts/hello-world
```

---

## Step 5: Typed Event Names Pattern

```typescript
// Create a fully typed event system using template literals
type EventMap = {
  'user:created': { id: number; name: string };
  'user:updated': { id: number; changes: Record<string, unknown> };
  'user:deleted': { id: number };
  'post:created': { postId: number; title: string };
  'post:viewed':  { postId: number; viewerId: number };
};

// Extract all event categories
type EventCategory = {
  [K in keyof EventMap]: K extends `${infer Cat}:${string}` ? Cat : never
}[keyof EventMap];
// 'user' | 'post'

// Events for a specific category
type CategoryEvents<Cat extends string> = {
  [K in keyof EventMap]: K extends `${Cat}:${string}` ? K : never
}[keyof EventMap];

type UserEvents = CategoryEvents<'user'>;
// 'user:created' | 'user:updated' | 'user:deleted'

class EventBus {
  private handlers = new Map<string, Function[]>();

  on<K extends keyof EventMap>(event: K, handler: (data: EventMap[K]) => void): void {
    const list = this.handlers.get(event) ?? [];
    list.push(handler);
    this.handlers.set(event, list);
  }

  emit<K extends keyof EventMap>(event: K, data: EventMap[K]): void {
    (this.handlers.get(event) ?? []).forEach(h => h(data));
  }
}

const bus = new EventBus();
bus.on('user:created', ({ id, name }) => console.log(`New user: ${name} (${id})`));
bus.emit('user:created', { id: 1, name: 'Alice' });
```

---

## Step 6: CSS Property Type Safety

```typescript
// CSS value types using template literals
type CSSUnit = 'px' | 'em' | 'rem' | 'vh' | 'vw' | '%';
type CSSValue = `${number}${CSSUnit}` | 'auto' | 'inherit' | 'initial';
type CSSColor = `#${string}` | `rgb(${number}, ${number}, ${number})` | string;

// CSS property mapping
type CSSProperties = {
  width?: CSSValue;
  height?: CSSValue;
  margin?: CSSValue;
  padding?: CSSValue;
  color?: CSSColor;
  backgroundColor?: CSSColor;
  fontSize?: CSSValue;
  fontWeight?: `${number}` | 'bold' | 'normal' | 'lighter';
};

const styles: CSSProperties = {
  width: '100px',
  height: '50vh',
  color: '#ff0000',
  backgroundColor: 'rgb(0, 0, 255)',
  fontSize: '1.5rem',
  fontWeight: '700',
};

console.log(JSON.stringify(styles, null, 2));

// Typed CSS variable names
type CSSVar<T extends string> = `--${T}`;
type ThemeVar = CSSVar<'primary-color' | 'secondary-color' | 'font-size'>;
const cssVar: ThemeVar = '--primary-color';
console.log(cssVar);
```

---

## Step 7: SQL Query Builder Types

```typescript
// Type-safe SQL column selection
type TableSchema = {
  users: { id: number; name: string; email: string; createdAt: Date };
  posts: { id: number; title: string; content: string; userId: number };
};

type TableName = keyof TableSchema;
type ColumnOf<T extends TableName> = keyof TableSchema[T] & string;
type QualifiedColumn<T extends TableName> = `${T}.${ColumnOf<T>}`;

type UserColumn = QualifiedColumn<'users'>;
// 'users.id' | 'users.name' | 'users.email' | 'users.createdAt'

function selectFrom<T extends TableName>(
  table: T,
  columns: ColumnOf<T>[]
): string {
  return `SELECT ${columns.join(', ')} FROM ${table}`;
}

const query = selectFrom('users', ['id', 'name', 'email']);
console.log(query); // SELECT id, name, email FROM users
// selectFrom('users', ['invalid']); // TS error!
```

---

## Step 8: Capstone — Full Template Literal Demo

```typescript
// Save as lab-adv02-capstone.ts
type EventName2 = 'click' | 'focus' | 'blur';
type Handler2 = `on${Capitalize<EventName2>}`;

type Getter2<T extends string> = `get${Capitalize<T>}`;
type Setter2<T extends string> = `set${Capitalize<T>}`;
type Accessors2<T extends string> = Getter2<T> | Setter2<T>;
type NameAccessors2 = Accessors2<'name'>;

type ExtractRouteParams<T extends string> =
  T extends `${infer Start}:${infer Param}/${infer Rest}`
    ? Param | ExtractRouteParams<Rest>
    : T extends `${infer Start}:${infer Param}`
    ? Param
    : never;

type Params = ExtractRouteParams<'/users/:id/posts/:postId'>;

const h2: Handler2 = 'onClick';
const a2: NameAccessors2 = 'getName';
console.log(h2, a2);
console.log('Template literals OK');
```

Run:
```bash
ts-node -P tsconfig.json lab-adv02-capstone.ts
```

📸 **Verified Output:**
```
onClick getName
Template literals OK
```

---

## Summary

| Feature | Syntax | Result |
|---------|--------|--------|
| Template literal | `` `${A}${B}` `` | String combination |
| Uppercase | `Uppercase<'hello'>` | `'HELLO'` |
| Lowercase | `Lowercase<'HELLO'>` | `'hello'` |
| Capitalize | `Capitalize<'hello'>` | `'Hello'` |
| Uncapitalize | `Uncapitalize<'Hello'>` | `'hello'` |
| infer in template | `` `prefix${infer Rest}` `` | Extract suffix |
| Cross product | `` `${A \| B}${C \| D}` `` | All combinations |
| Route params | Recursive infer | Type-safe routing |
