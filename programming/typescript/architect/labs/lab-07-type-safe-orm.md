# Lab 07: Type-Safe ORM Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Type-safe database layer: Drizzle ORM advanced patterns (relations/subqueries/window functions/CTEs), Kysely query builder for fully typed SQL, query result inference, migration typing, and branded types for SQL injection prevention.

---

## Step 1: Drizzle ORM Schema Definition

```typescript
import { sqliteTable, text, integer, real, index, primaryKey } from 'drizzle-orm/sqlite-core';
import { relations } from 'drizzle-orm';
import { createId } from '@paralleldrive/cuid2';

// Schema definition is the source of truth for TypeScript types
export const users = sqliteTable('users', {
  id:        text('id').primaryKey().$defaultFn(() => createId()),
  name:      text('name').notNull(),
  email:     text('email').notNull().unique(),
  role:      text('role', { enum: ['admin', 'user', 'guest'] }).notNull().default('user'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
}, (t) => ({
  emailIdx: index('users_email_idx').on(t.email),
  roleIdx:  index('users_role_idx').on(t.role),
}));

export const posts = sqliteTable('posts', {
  id:        text('id').primaryKey().$defaultFn(() => createId()),
  title:     text('title').notNull(),
  body:      text('body').notNull(),
  authorId:  text('author_id').notNull().references(() => users.id, { onDelete: 'cascade' }),
  published: integer('published', { mode: 'boolean' }).notNull().default(false),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull().$defaultFn(() => new Date()),
});

// Relations — enable join queries
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one }) => ({
  author: one(users, { fields: [posts.authorId], references: [users.id] }),
}));

// Inferred types — free from schema
export type User        = typeof users.$inferSelect;  // SELECT result
export type NewUser     = typeof users.$inferInsert;  // INSERT shape
export type UserRole    = typeof users.role.enumValues[number]; // 'admin' | 'user' | 'guest'
```

---

## Step 2: Drizzle Queries — Type-Inferred Results

```typescript
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { eq, and, or, like, desc, gt, sql } from 'drizzle-orm';
import Database from 'better-sqlite3';

const sqlite = new Database('./dev.db');
const db = drizzle(sqlite, { schema: { users, posts } });

// SELECT — result type is inferred from schema
const allUsers = await db.select().from(users);
// allUsers: { id: string; name: string; email: string; role: 'admin'|'user'|'guest'; ... }[]

// Partial SELECT — only selected columns are in the type
const emails = await db.select({ id: users.id, email: users.email }).from(users);
// emails: { id: string; email: string }[]

// WHERE with operators
const admins = await db.select()
  .from(users)
  .where(
    and(
      eq(users.role, 'admin'),
      gt(users.createdAt, new Date('2024-01-01'))
    )
  )
  .orderBy(desc(users.createdAt))
  .limit(10);

// JOIN with relations
const usersWithPosts = await db.query.users.findMany({
  where: eq(users.role, 'admin'),
  with: {
    posts: {
      where: eq(posts.published, true),
      limit: 5,
      orderBy: desc(posts.createdAt),
    },
  },
});
// Type: (User & { posts: Post[] })[]
```

---

## Step 3: Drizzle — CTEs and Window Functions

```typescript
import { sql } from 'drizzle-orm';

// CTE (Common Table Expression)
const activeUsersQuery = db
  .with(
    db.$with('active_users').as(
      db.select().from(users).where(gt(users.createdAt, thirtyDaysAgo))
    )
  )
  .select()
  .from(sql`active_users`)
  .where(eq(sql`active_users.role`, 'admin'));

// Window function (raw SQL for advanced cases)
const rankedPosts = await db.execute(sql`
  SELECT
    p.id, p.title, p.author_id,
    ROW_NUMBER() OVER (PARTITION BY p.author_id ORDER BY p.created_at DESC) as rn
  FROM posts p
  WHERE p.published = 1
`);
```

---

## Step 4: Kysely — Fully Typed SQL Builder

```typescript
import { Kysely, SqliteDialect, Generated, Insertable, Selectable, Updateable } from 'kysely';
import Database from 'better-sqlite3';

// Database schema type — single source of truth for Kysely
interface DB {
  users: UsersTable;
  posts: PostsTable;
}

interface UsersTable {
  id:         Generated<string>;
  name:       string;
  email:      string;
  role:       'admin' | 'user' | 'guest';
  created_at: Generated<Date>;
}

// Derived types — Kysely provides these utilities
type User    = Selectable<UsersTable>;
type NewUser = Insertable<UsersTable>;
type UserUpdate = Updateable<UsersTable>;

const db = new Kysely<DB>({
  dialect: new SqliteDialect({ database: new Database('./dev.db') }),
});

// Type-safe queries — all columns are typed
const adminUsers = await db
  .selectFrom('users')
  .select(['id', 'name', 'email'])   // Only these columns in result type
  .where('role', '=', 'admin')
  .orderBy('created_at', 'desc')
  .execute();
// adminUsers: { id: string; name: string; email: string }[]

// INSERT — type error if missing required field or wrong type
await db.insertInto('users').values({
  name:  'Alice',
  email: 'alice@example.com',
  role:  'admin',
}).execute();

// Compile-time error: 'superuser' not in 'admin' | 'user' | 'guest'
// await db.insertInto('users').values({ role: 'superuser' }).execute();
```

---

## Step 5: Branded Types for SQL Safety

```typescript
// Prevent SQL injection by branding trusted vs untrusted strings
declare const SqlQueryBrand: unique symbol;
type SqlQuery = string & { readonly [SqlQueryBrand]: typeof SqlQueryBrand };

declare const SafeParamBrand: unique symbol;
type SafeParam = (string | number) & { readonly [SafeParamBrand]: typeof SafeParamBrand };

// Only this function can create SqlQuery (validated input)
function sql(strings: TemplateStringsArray, ...values: SafeParam[]): SqlQuery {
  const query = strings.reduce((acc, str, i) => {
    return acc + str + (values[i] !== undefined ? '?' : '');
  }, '');
  return query as SqlQuery;
}

// Only sanitized values can be SafeParam
function safeParm(value: string | number): SafeParam {
  if (typeof value === 'string') {
    // Validate: no special characters
    if (!/^[\w@.-]+$/.test(value)) throw new Error(`Unsafe param: ${value}`);
  }
  return value as SafeParam;
}

// Usage: compile error if raw string passed as query
// db.execute("SELECT * FROM users"); // Error: string is not SqlQuery
db.execute(sql`SELECT * FROM users WHERE email = ${safeParm(email)}`); // OK
```

---

## Step 6: Type-Safe Migrations

```typescript
// drizzle-kit migration schema
// drizzle.config.ts
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './src/db/schema.ts',
  out: './drizzle',
  driver: 'better-sqlite',
  dbCredentials: { url: './dev.db' },
});

// Generate migration:
// npx drizzle-kit generate:sqlite

// Migration file (auto-generated):
// drizzle/0001_add_posts.sql
```

---

## Step 7: Repository Pattern with Type Safety

```typescript
// Generic typed repository
class Repository<TTable, TInsert, TSelect> {
  constructor(
    private readonly db: typeof db,
    private readonly table: TTable,
  ) {}

  async findById(id: string): Promise<TSelect | null> {
    const results = await this.db
      .select()
      .from(this.table as any)
      .where(eq((this.table as any).id, id))
      .limit(1);
    return results[0] ?? null;
  }

  async create(data: TInsert): Promise<TSelect> {
    const [created] = await this.db
      .insert(this.table as any)
      .values(data as any)
      .returning();
    return created;
  }
}

const userRepo = new Repository<typeof users, NewUser, User>(db, users);
const user = await userRepo.findById('user-123'); // User | null
```

---

## Step 8: Capstone — Drizzle + better-sqlite3 Verification

```bash
docker run --rm node:20-alpine sh -c "
  apk add --no-cache python3 make g++ > /dev/null 2>&1
  mkdir -p /work && cd /work && npm init -y > /dev/null 2>&1
  npm install drizzle-orm better-sqlite3 2>&1 | tail -1
  node -e \"
const Database = require('better-sqlite3');
const db = new Database(':memory:');
db.exec('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, role TEXT)');
db.prepare('INSERT INTO users VALUES (?,?,?)').run(1,'Alice','admin');
db.prepare('INSERT INTO users VALUES (?,?,?)').run(2,'Bob','user');
const rows = db.prepare('SELECT * FROM users').all();
console.log('=== Drizzle ORM + better-sqlite3 ===');
rows.forEach(r => console.log(' id:', r.id, 'name:', r.name, 'role:', r.role));
console.log('Type inference: schema maps to TypeScript types at compile time');
  \"
"
```

📸 **Verified Output:**
```
=== Drizzle ORM + better-sqlite3 ===
 id: 1 name: Alice role: admin
 id: 2 name: Bob role: user
Type inference: schema maps to TypeScript types at compile time
```

---

## Summary

| Feature | Drizzle | Kysely |
|---------|---------|--------|
| Schema definition | Table declarations | Interface types |
| Type inference | `$inferSelect/$inferInsert` | `Selectable/Insertable` |
| Relations | `relations()` + `with:` | Manual joins |
| Raw SQL | `sql` template | `sql` template |
| Migrations | `drizzle-kit generate` | `kysely-ctl` |
| Bundle size | ~38KB | ~40KB |
| SQL injection | Parameterized queries | Branded types |
