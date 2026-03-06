# Lab 11: Zod Runtime Validation

**Time:** 30 minutes | **Level:** Practitioner | **Docker:** `docker run -it --rm node:20-alpine sh`

Zod schemas: string/number/object/array/enum/union/discriminatedUnion/lazy/transform/refine, `z.infer<>`, parse vs safeParse, ZodError formatting.

---

## Step 1: Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir /lab11 && cd /lab11
npm init -y
npm install zod
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

## Step 2: Basic Primitives

```typescript
import { z } from 'zod';

// Primitive schemas
const StringSchema = z.string();
const NumberSchema = z.number();
const BooleanSchema = z.boolean();
const DateSchema = z.date();

// With constraints
const NameSchema = z.string().min(1).max(100).trim();
const AgeSchema = z.number().int().min(0).max(150);
const EmailSchema = z.string().email();
const UrlSchema = z.string().url();
const UuidSchema = z.string().uuid();
const PortSchema = z.number().int().min(1).max(65535);

// Parse (throws on failure)
console.log(NameSchema.parse('  Alice  '));  // 'Alice' (trimmed)
console.log(AgeSchema.parse(25));

// Infer TypeScript types from schemas
type Name = z.infer<typeof NameSchema>;  // string
type Age = z.infer<typeof AgeSchema>;    // number
```

---

## Step 3: Object Schemas

```typescript
const UserSchema = z.object({
  id: z.number().int().positive(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(['admin', 'user', 'guest']).default('user'),
  age: z.number().int().min(0).max(150).optional(),
  tags: z.array(z.string()).default([]),
  createdAt: z.date().optional(),
});

// Infer TypeScript type
type User = z.infer<typeof UserSchema>;

// Parse — throws ZodError on failure
const user = UserSchema.parse({
  id: 1,
  name: 'Alice',
  email: 'alice@example.com',
  // role defaults to 'user', tags defaults to []
});
console.log(user.role, user.tags);  // user []

// Derived schemas
const UpdateUserSchema = UserSchema.partial();   // all optional
const CreateUserSchema = UserSchema.omit({ id: true, createdAt: true });
const PublicUserSchema = UserSchema.pick({ id: true, name: true, role: true });

type UpdateUser = z.infer<typeof UpdateUserSchema>;
type CreateUser = z.infer<typeof CreateUserSchema>;
```

---

## Step 4: SafeParse & Error Formatting

```typescript
// safeParse — returns { success, data } | { success, error }
const result = UserSchema.safeParse({
  id: -1,        // must be positive
  name: '',      // min length 1
  email: 'not-an-email',
  role: 'superadmin',  // not in enum
});

if (!result.success) {
  console.log('Validation errors:');
  result.error.issues.forEach(issue => {
    console.log(`  [${issue.path.join('.')}] ${issue.message}`);
  });
  // Structured error format
  const formatted = result.error.format();
  console.log('Formatted:', JSON.stringify(formatted, null, 2));
}

// Type-safe error handling
type ParseResult<T> = { ok: true; data: T } | { ok: false; errors: z.ZodIssue[] };

function parseUser(raw: unknown): ParseResult<User> {
  const r = UserSchema.safeParse(raw);
  if (r.success) return { ok: true, data: r.data };
  return { ok: false, errors: r.error.issues };
}
```

---

## Step 5: Union & Discriminated Union

```typescript
// Union
const StringOrNumber = z.union([z.string(), z.number()]);
const result2 = StringOrNumber.parse('hello');  // string
const result3 = StringOrNumber.parse(42);       // number

// Discriminated union (faster, clearer errors)
const ShapeSchema = z.discriminatedUnion('kind', [
  z.object({ kind: z.literal('circle'), radius: z.number().positive() }),
  z.object({ kind: z.literal('rect'), w: z.number().positive(), h: z.number().positive() }),
  z.object({ kind: z.literal('triangle'), base: z.number(), height: z.number() }),
]);

type Shape = z.infer<typeof ShapeSchema>;

const shape = ShapeSchema.parse({ kind: 'circle', radius: 5 });
console.log(shape.kind);  // circle

function area(s: Shape): number {
  switch (s.kind) {
    case 'circle': return Math.PI * s.radius ** 2;
    case 'rect': return s.w * s.h;
    case 'triangle': return 0.5 * s.base * s.height;
  }
}
console.log(area({ kind: 'rect', w: 4, h: 6 }));  // 24
```

---

## Step 6: Transform & Refine

```typescript
// transform — parse AND transform the value
const TrimmedString = z.string().transform(s => s.trim());
const NumberFromString = z.string().transform(s => Number(s));
const DateFromString = z.string().datetime().transform(s => new Date(s));

console.log(TrimmedString.parse('  hello  '));  // 'hello'
console.log(NumberFromString.parse('42'));      // 42

// refine — custom validation logic
const PasswordSchema = z
  .string()
  .min(8)
  .refine(s => /[A-Z]/.test(s), 'Must contain uppercase')
  .refine(s => /[0-9]/.test(s), 'Must contain number')
  .refine(s => /[^a-zA-Z0-9]/.test(s), 'Must contain special char');

const ConfirmPassword = z.object({
  password: z.string().min(8),
  confirm: z.string(),
}).refine(data => data.password === data.confirm, {
  message: 'Passwords do not match',
  path: ['confirm'],
});

const pr = PasswordSchema.safeParse('Passw0rd!');
console.log('Password valid:', pr.success);

const cr = ConfirmPassword.safeParse({ password: 'abc12345', confirm: 'abc12345X' });
if (!cr.success) console.log('Confirm error:', cr.error.issues[0].message);
```

---

## Step 7: Lazy (Recursive Schemas)

```typescript
// Recursive schemas need z.lazy()
interface Category {
  id: number;
  name: string;
  children: Category[];
}

const CategorySchema: z.ZodType<Category> = z.lazy(() =>
  z.object({
    id: z.number(),
    name: z.string(),
    children: z.array(CategorySchema),
  })
);

const category = CategorySchema.parse({
  id: 1,
  name: 'Electronics',
  children: [
    { id: 2, name: 'Phones', children: [] },
    { id: 3, name: 'Laptops', children: [
      { id: 4, name: 'Gaming', children: [] }
    ]},
  ],
});

console.log(category.name, category.children.length);  // Electronics 2
console.log(category.children[1].children[0].name);    // Gaming
```

---

## Step 8: Capstone — Full Validation

```typescript
// Save as lab11-capstone.ts
import { z } from 'zod';

const UserSchema = z.object({
  id: z.number().int().positive(),
  name: z.string().min(1),
  email: z.string().email(),
  role: z.enum(['admin', 'user', 'guest']).default('user'),
});
type User = z.infer<typeof UserSchema>;

const result = UserSchema.safeParse({ id: 1, name: 'Alice', email: 'alice@example.com' });
if (result.success) console.log('Valid user:', result.data.name, result.data.role);

const bad = UserSchema.safeParse({ id: -1, name: '', email: 'not-email' });
if (!bad.success) console.log('Errors:', bad.error.issues.length);

console.log('Zod OK');
```

Run:
```bash
ts-node -P tsconfig.json lab11-capstone.ts
```

📸 **Verified Output:**
```
Valid user: Alice user
Errors: 3
Zod OK
```

---

## Summary

| Zod API | Description |
|---------|-------------|
| `z.string().email()` | Email validation |
| `z.number().int().min(0)` | Integer with minimum |
| `z.object({...})` | Object schema |
| `z.array(schema)` | Array of schema |
| `z.enum([...])` | Enum values |
| `z.union([...])` | Multiple valid types |
| `z.discriminatedUnion(key, [...])` | Tagged union |
| `z.lazy(() => schema)` | Recursive schema |
| `.transform(fn)` | Parse + transform |
| `.refine(fn, msg)` | Custom validation |
| `.parse(data)` | Throws on failure |
| `.safeParse(data)` | Returns `{ success, data/error }` |
| `z.infer<typeof Schema>` | Derive TypeScript type |
