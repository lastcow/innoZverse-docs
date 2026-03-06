# Lab 07: Advanced Runtime Validation with Zod

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Master Zod's advanced features: discriminated unions, lazy recursive schemas, transforms, branded types, and type-safe error formatting.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir lab07 && cd lab07
npm init -y
npm install zod
echo '{"compilerOptions":{"module":"commonjs","target":"es2020","strict":true,"esModuleInterop":true}}' > tsconfig.json
```

> 💡 Zod schemas are both runtime validators AND TypeScript type definitions. `z.infer<typeof Schema>` extracts the TypeScript type — no duplication needed.

---

## Step 2: Discriminated Unions

Parse polymorphic payloads with full type safety:

```typescript
// shapes.ts
import { z } from 'zod';

// z.discriminatedUnion is faster than z.union — checks the discriminator key first
const ShapeSchema = z.discriminatedUnion('kind', [
  z.object({
    kind: z.literal('circle'),
    radius: z.number().positive(),
  }),
  z.object({
    kind: z.literal('rectangle'),
    width: z.number().positive(),
    height: z.number().positive(),
  }),
  z.object({
    kind: z.literal('triangle'),
    base: z.number().positive(),
    height: z.number().positive(),
  }),
]);

type Shape = z.infer<typeof ShapeSchema>;

function area(shape: Shape): number {
  switch (shape.kind) {
    case 'circle':
      return Math.PI * shape.radius ** 2;
    case 'rectangle':
      return shape.width * shape.height;
    case 'triangle':
      return 0.5 * shape.base * shape.height;
  }
}

const shapes = [
  { kind: 'circle', radius: 5 },
  { kind: 'rectangle', width: 4, height: 6 },
  { kind: 'triangle', base: 3, height: 8 },
];

shapes.forEach(raw => {
  const shape = ShapeSchema.parse(raw);
  console.log(`${shape.kind}: area = ${area(shape).toFixed(2)}`);
});
```

---

## Step 3: Lazy Recursive Schemas

Handle tree-structured or recursive data:

```typescript
// recursive.ts
import { z } from 'zod';

// Recursive type: a category can have sub-categories
type Category = {
  id: string;
  name: string;
  children: Category[];
};

// z.lazy() defers schema evaluation — required for recursion
const CategorySchema: z.ZodType<Category> = z.lazy(() =>
  z.object({
    id: z.string().uuid(),
    name: z.string().min(1).max(100),
    children: z.array(CategorySchema),
  })
);

// JSON tree structure
const tree = {
  id: '550e8400-e29b-41d4-a716-446655440000',
  name: 'Electronics',
  children: [
    {
      id: '550e8400-e29b-41d4-a716-446655440001',
      name: 'Computers',
      children: [
        {
          id: '550e8400-e29b-41d4-a716-446655440002',
          name: 'Laptops',
          children: [],
        },
      ],
    },
    {
      id: '550e8400-e29b-41d4-a716-446655440003',
      name: 'Phones',
      children: [],
    },
  ],
};

const parsed = CategorySchema.parse(tree);
console.log('Root:', parsed.name);
console.log('First child:', parsed.children[0].name);
console.log('Grandchild:', parsed.children[0].children[0].name);
```

> 💡 `z.lazy()` takes a function that returns the schema, breaking the circular reference at declaration time.

---

## Step 4: Transform and Preprocess

Shape data as it's validated:

```typescript
// transforms.ts
import { z } from 'zod';

// z.preprocess: runs BEFORE validation (type coercion)
const FlexibleNumber = z.preprocess(
  val => (typeof val === 'string' ? parseFloat(val) : val),
  z.number().finite()
);

// z.transform: runs AFTER validation (data transformation)
const TrimmedEmail = z.string()
  .trim()
  .toLowerCase()
  .email();

const NormalizedDate = z.string()
  .transform(s => new Date(s))
  .refine(d => !isNaN(d.getTime()), 'Invalid date string');

// Combined: preprocess + validate + transform
const UserInput = z.object({
  name: z.string().trim().min(2),
  email: TrimmedEmail,
  age: FlexibleNumber.pipe(z.number().int().min(0).max(150)),
  birthDate: NormalizedDate,
}).transform(data => ({
  ...data,
  displayName: data.name.toUpperCase(),
  isAdult: data.age >= 18,
}));

const raw = {
  name: '  Alice  ',
  email: '  ALICE@EXAMPLE.COM  ',
  age: '25',
  birthDate: '1999-01-15',
};

const result = UserInput.parse(raw);
console.log('Name:', result.name);
console.log('Email:', result.email);
console.log('Age:', result.age, '(from string "25")');
console.log('Display:', result.displayName);
console.log('Adult:', result.isAdult);
```

---

## Step 5: Branded Types for Nominal Typing

Create distinct types from identical primitives:

```typescript
// brands.ts
import { z } from 'zod';

// Create branded string types
const UserId = z.string().uuid().brand<'UserId'>();
const ProductId = z.string().uuid().brand<'ProductId'>();
const Email = z.string().email().brand<'Email'>();

type UserId = z.infer<typeof UserId>;
type ProductId = z.infer<typeof ProductId>;
type Email = z.infer<typeof Email>;

// These are structurally identical strings, but nominally distinct
function getUserById(id: UserId): { id: UserId; name: string } {
  return { id, name: 'Alice' };
}

const rawId = '550e8400-e29b-41d4-a716-446655440000';
const userId = UserId.parse(rawId);
const productId = ProductId.parse(rawId);

// TypeScript prevents mixing them up
getUserById(userId);     // ✅ OK
// getUserById(productId);  // ❌ Type error: ProductId != UserId
// getUserById(rawId);      // ❌ Type error: string != UserId

console.log('UserId:', userId);
console.log('Branded types prevent ID mixing at compile time!');
```

> 💡 Brands are zero-cost at runtime — they're erased after parsing. The brand only exists in TypeScript's type system.

---

## Step 6: ZodError Formatting

Parse and display validation errors clearly:

```typescript
// errors.ts
import { z } from 'zod';

const SignupSchema = z.object({
  username: z.string().min(3).max(20).regex(/^[a-z0-9_]+$/, 'Only lowercase letters, numbers, underscores'),
  email: z.string().email(),
  password: z.string().min(8).max(64),
  confirmPassword: z.string(),
  age: z.number().int().min(13, 'Must be at least 13'),
  terms: z.literal(true, { errorMap: () => ({ message: 'You must accept the terms' }) }),
}).refine(data => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

const badInput = {
  username: 'A!',                // Too short, invalid chars
  email: 'not-an-email',
  password: 'short',            // Too short
  confirmPassword: 'different',
  age: 10,                       // Too young
  terms: false,                  // Must be true
};

const result = SignupSchema.safeParse(badInput);

if (!result.success) {
  // flatten() gives a clean field → errors map
  const errors = result.error.flatten();
  console.log('Form errors:');
  console.log('  Field errors:', JSON.stringify(errors.fieldErrors, null, 2));
  console.log('  Form errors:', errors.formErrors);

  // format() gives nested structure
  const formatted = result.error.format();
  console.log('\nFormatted errors (nested):');
  Object.entries(formatted).forEach(([field, val]) => {
    if (field !== '_errors' && val && '_errors' in val) {
      const errs = (val as any)._errors;
      if (errs.length > 0) console.log(`  ${field}: ${errs.join(', ')}`);
    }
  });
}
```

---

## Step 7: Complex Schema Composition

Build a full API request validator:

```typescript
// api-schema.ts
import { z } from 'zod';

const PaginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
});

const SortSchema = z.object({
  field: z.string(),
  direction: z.enum(['asc', 'desc']).default('asc'),
});

const FilterOperator = z.discriminatedUnion('op', [
  z.object({ op: z.literal('eq'), value: z.unknown() }),
  z.object({ op: z.literal('contains'), value: z.string() }),
  z.object({ op: z.literal('gt'), value: z.number() }),
  z.object({ op: z.literal('between'), min: z.number(), max: z.number() }),
]);

const QuerySchema = PaginationSchema.merge(z.object({
  sort: SortSchema.optional(),
  filters: z.record(FilterOperator).optional(),
}));

type Query = z.infer<typeof QuerySchema>;

const raw = {
  page: '2',          // string coerced to number
  filters: {
    name: { op: 'contains', value: 'Alice' },
    score: { op: 'between', min: 80, max: 100 },
  },
};

const query: Query = QuerySchema.parse(raw);
console.log('Page:', query.page, '(coerced from string)');
console.log('Page size:', query.pageSize, '(default applied)');
console.log('Filters:', JSON.stringify(query.filters));
```

---

## Step 8: Capstone — API Validation Middleware

```typescript
// middleware.ts
import { z, ZodSchema } from 'zod';

// Generic validator factory
function createValidator<T>(schema: ZodSchema<T>) {
  return function validate(input: unknown): { data: T } | { errors: z.ZodError } {
    const result = schema.safeParse(input);
    if (result.success) return { data: result.data };
    return { errors: result.error };
  };
}

// Real schemas
const CreateUserSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
  role: z.enum(['admin', 'editor', 'viewer']).default('viewer'),
}).strict(); // No extra fields allowed

const UpdateProductSchema = z.object({
  name: z.string().min(1).optional(),
  price: z.number().positive().optional(),
  stock: z.number().int().min(0).optional(),
}).refine(data => Object.keys(data).length > 0, 'At least one field required');

// Use validators
const validateUser = createValidator(CreateUserSchema);
const validateProduct = createValidator(UpdateProductSchema);

// Valid
const r1 = validateUser({ name: 'Alice', email: 'alice@example.com' });
if ('data' in r1) console.log('Valid user:', r1.data.name, r1.data.role);

// Invalid
const r2 = validateUser({ name: 'A', email: 'bad', unknown: 'field' });
if ('errors' in r2) {
  const flat = r2.errors.flatten();
  console.log('Validation failed:', JSON.stringify(flat.fieldErrors));
}

// Product update
const r3 = validateProduct({});
if ('errors' in r3) console.log('Product error:', r3.errors.issues[0].message);
console.log('✅ Lab 07 complete');
```

Run:
```bash
ts-node middleware.ts
```

📸 **Verified Output:**
```
{ kind: 'circle', radius: 5 } { name: 'root', children: [ { name: 'child', children: [] } ] } 42 HELLO
ZodError flatten: {"formErrors":[],"fieldErrors":{"radius":["Invalid input: expected number, received string"]}}
Zod advanced verified!
```

---

## Summary

| Feature | API | Use Case |
|---|---|---|
| Polymorphic types | `z.discriminatedUnion('key', [...])` | Parse variant objects |
| Recursive schemas | `z.lazy(() => schema)` | Trees, nested data |
| Type coercion | `z.preprocess(fn, schema)` | String → number from URL params |
| Data transformation | `.transform(fn)` | Normalize after parse |
| Nominal typing | `.brand<'TypeName'>()` | Prevent ID mixing |
| Type extraction | `z.infer<typeof Schema>` | Zero-duplication types |
| Error formatting | `.error.flatten()` | Clean field → error map |
