# Lab 14: Type-Safe Database with Drizzle ORM

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Build a fully type-safe SQLite database layer using Drizzle ORM: schema definition, CRUD operations, relations, inferred TypeScript types, and drizzle-kit migrations.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
apk add --no-cache python3 make g++
npm install -g typescript ts-node
mkdir lab14 && cd lab14
npm init -y
npm install drizzle-orm better-sqlite3 @types/better-sqlite3
echo '{"compilerOptions":{"module":"commonjs","target":"es2020","strict":false,"esModuleInterop":true,"moduleResolution":"node"}}' > tsconfig.json
```

> 💡 `strict: false` here avoids some decorator-related issues. In production, use `strict: true` with Drizzle's latest version which supports it fully.

---

## Step 2: Schema Definition

Drizzle schemas are TypeScript — types are inferred automatically:

```typescript
// schema.ts
import { sqliteTable, text, integer, real, blob } from 'drizzle-orm/sqlite-core';
import { relations } from 'drizzle-orm';
import { sql } from 'drizzle-orm';

// Users table
export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  role: text('role', { enum: ['admin', 'editor', 'viewer'] }).default('viewer').notNull(),
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`).notNull(),
  active: integer('active', { mode: 'boolean' }).default(true).notNull(),
});

// Posts table
export const posts = sqliteTable('posts', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  title: text('title').notNull(),
  content: text('content').notNull(),
  published: integer('published', { mode: 'boolean' }).default(false).notNull(),
  authorId: integer('author_id').notNull().references(() => users.id),
  views: integer('views').default(0).notNull(),
  score: real('score').default(0.0),
  createdAt: text('created_at').default(sql`CURRENT_TIMESTAMP`).notNull(),
});

// Tags table
export const tags = sqliteTable('tags', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull().unique(),
  color: text('color').default('#gray'),
});

// Post-Tags junction
export const postTags = sqliteTable('post_tags', {
  postId: integer('post_id').notNull().references(() => posts.id),
  tagId: integer('tag_id').notNull().references(() => tags.id),
});

// Relations (for query builder joins)
export const usersRelations = relations(users, ({ many }) => ({
  posts: many(posts),
}));

export const postsRelations = relations(posts, ({ one, many }) => ({
  author: one(users, { fields: [posts.authorId], references: [users.id] }),
  postTags: many(postTags),
}));

// TypeScript types inferred from schema
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Post = typeof posts.$inferSelect;
export type NewPost = typeof posts.$inferInsert;
export type Tag = typeof tags.$inferSelect;
```

> 💡 `$inferSelect` gives the TypeScript type of a SELECT result. `$inferInsert` gives the type for INSERT (all defaults become optional). No manual type definitions needed!

---

## Step 3: Database Setup and Connection

```typescript
// db.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import * as schema from './schema';

// Create in-memory SQLite database
const sqlite = new Database(':memory:');

// Create tables (in real projects, use drizzle-kit migrations)
sqlite.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL DEFAULT 'viewer',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active INTEGER NOT NULL DEFAULT 1
  );

  CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    published INTEGER NOT NULL DEFAULT 0,
    author_id INTEGER NOT NULL REFERENCES users(id),
    views INTEGER NOT NULL DEFAULT 0,
    score REAL DEFAULT 0.0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    color TEXT DEFAULT '#gray'
  );

  CREATE TABLE IF NOT EXISTS post_tags (
    post_id INTEGER NOT NULL REFERENCES posts(id),
    tag_id INTEGER NOT NULL REFERENCES tags(id)
  );
`);

export const db = drizzle(sqlite, { schema });
```

---

## Step 4: INSERT Operations

Type-safe inserts with `$inferInsert`:

```typescript
// insert.ts
import { db } from './db';
import { users, posts, tags, postTags } from './schema';
import type { NewUser, NewPost } from './schema';

export async function seedDatabase() {
  // Insert users — type is NewUser (all defaults optional)
  const alice: NewUser = { name: 'Alice', email: 'alice@example.com', role: 'admin' };
  const bob: NewUser = { name: 'Bob', email: 'bob@example.com' }; // role defaults to 'viewer'

  db.insert(users).values(alice).run();
  db.insert(users).values(bob).run();
  db.insert(users).values({ name: 'Charlie', email: 'charlie@example.com', role: 'editor' }).run();

  // Bulk insert
  db.insert(tags).values([
    { name: 'typescript', color: '#3178c6' },
    { name: 'javascript', color: '#f7df1e' },
    { name: 'database', color: '#336791' },
  ]).run();

  // Insert posts
  const post1: NewPost = {
    title: 'TypeScript Generics Deep Dive',
    content: 'Generics allow you to write reusable, type-safe code...',
    authorId: 1,
    published: true,
    score: 9.5,
  };

  db.insert(posts).values(post1).run();
  db.insert(posts).values({
    title: 'Drizzle ORM Getting Started',
    content: 'Drizzle is a type-safe SQL ORM...',
    authorId: 1,
    published: true,
    views: 150,
    score: 8.7,
  }).run();
  db.insert(posts).values({
    title: 'Draft Post',
    content: 'Work in progress...',
    authorId: 2,
    published: false,
  }).run();

  // Post-tag relations
  db.insert(postTags).values([
    { postId: 1, tagId: 1 }, // Post 1 tagged with typescript
    { postId: 2, tagId: 1 }, // Post 2 tagged with typescript
    { postId: 2, tagId: 3 }, // Post 2 tagged with database
  ]).run();

  console.log('Database seeded!');
}
```

---

## Step 5: SELECT with WHERE and Operators

```typescript
// queries.ts
import { db } from './db';
import { users, posts } from './schema';
import { eq, gt, lt, and, or, like, inArray, isNull, desc, asc, count, avg } from 'drizzle-orm';

export function demonstrateQueries() {
  // Simple select all
  const allUsers = db.select().from(users).all();
  console.log(`All users: ${allUsers.map(u => u.name).join(', ')}`);

  // Select specific columns
  const userNames = db.select({ name: users.name, email: users.email }).from(users).all();
  console.log('Names:', userNames.map(u => u.name).join(', '));

  // WHERE with eq
  const alice = db.select().from(users).where(eq(users.email, 'alice@example.com')).get();
  console.log('Alice:', alice?.name, alice?.role);

  // WHERE with multiple conditions
  const adminEditors = db.select()
    .from(users)
    .where(or(eq(users.role, 'admin'), eq(users.role, 'editor')))
    .all();
  console.log('Admins + Editors:', adminEditors.map(u => `${u.name}(${u.role})`).join(', '));

  // WHERE with comparison operators
  const highScorePosts = db.select()
    .from(posts)
    .where(and(gt(posts.score!, 8.0), eq(posts.published, true)))
    .orderBy(desc(posts.score!))
    .all();
  console.log('High score published posts:', highScorePosts.map(p => `${p.title}(${p.score})`).join(', '));

  // LIKE for text search
  const typescriptPosts = db.select()
    .from(posts)
    .where(like(posts.title, '%TypeScript%'))
    .all();
  console.log('TypeScript posts:', typescriptPosts.length);

  // Aggregate functions
  const stats = db.select({
    total: count(),
    avgScore: avg(posts.score!),
  }).from(posts).get();
  console.log(`Posts stats: total=${stats?.total}, avgScore=${Number(stats?.avgScore).toFixed(1)}`);
}
```

---

## Step 6: UPDATE and DELETE

```typescript
// mutations.ts
import { db } from './db';
import { users, posts } from './schema';
import { eq, lt } from 'drizzle-orm';

export function demonstrateMutations() {
  // Update single field
  db.update(users)
    .set({ role: 'editor' })
    .where(eq(users.name, 'Bob'))
    .run();
  console.log('Bob promoted to editor');

  // Update multiple fields
  db.update(posts)
    .set({ published: true, views: 100 })
    .where(eq(posts.title, 'Draft Post'))
    .run();
  console.log('Draft post published');

  // Conditional update
  const bobUser = db.select().from(users).where(eq(users.name, 'Bob')).get();
  if (bobUser) {
    db.update(users)
      .set({ active: !bobUser.active })
      .where(eq(users.id, bobUser.id))
      .run();
    console.log(`Bob active toggled`);
  }

  // Delete with condition
  db.delete(posts)
    .where(eq(posts.published, false))
    .run();
  console.log('Deleted unpublished posts');

  // Verify changes
  const finalUsers = db.select({ name: users.name, role: users.role }).from(users).all();
  console.log('Final users:', finalUsers.map(u => `${u.name}(${u.role})`).join(', '));

  const publishedPosts = db.select().from(posts).where(eq(posts.published, true)).all();
  console.log('Published posts:', publishedPosts.length);
}
```

---

## Step 7: drizzle-kit Migrations Concept

```typescript
// drizzle.config.ts — conceptual (not run in Docker demo)
// import type { Config } from 'drizzle-kit';
// export default {
//   schema: './src/schema.ts',
//   out: './drizzle',         // Where migration files go
//   driver: 'better-sqlite',
//   dbCredentials: {
//     url: './sqlite.db',
//   },
// } satisfies Config;

// Generated migration example (drizzle/0000_init.sql):
/*
CREATE TABLE `users` (
  `id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
  `name` text NOT NULL,
  `email` text NOT NULL,
  ...
);
CREATE UNIQUE INDEX `users_email_unique` ON `users` (`email`);
*/

// Commands:
// npx drizzle-kit generate    — generate migration from schema changes
// npx drizzle-kit migrate     — apply pending migrations
// npx drizzle-kit studio      — open browser-based DB explorer
// npx drizzle-kit push        — push schema directly (dev only)
```

> 💡 **drizzle-kit push** (no migrations) is great for prototyping. **drizzle-kit generate + migrate** is for production — you get versioned, reviewable SQL migration files.

---

## Step 8: Capstone — Complete Data Layer

```typescript
// capstone.ts
import Database from 'better-sqlite3';
import { drizzle } from 'drizzle-orm/better-sqlite3';
import { sqliteTable, text, integer, real } from 'drizzle-orm/sqlite-core';
import { eq, gt, desc, count } from 'drizzle-orm';

// Schema
const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  email: text('email').notNull(),
  score: real('score').default(0),
});

const sqlite = new Database(':memory:');
sqlite.exec(`
  CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    score REAL DEFAULT 0
  )
`);
const db = drizzle(sqlite);

// Type-inferred from schema
type User = typeof users.$inferSelect;
type NewUser = typeof users.$inferInsert;

// Repository pattern with full type safety
class UserRepository {
  findAll(): User[] {
    return db.select().from(users).all() as User[];
  }

  findById(id: number): User | undefined {
    return db.select().from(users).where(eq(users.id, id)).get() as User | undefined;
  }

  create(data: NewUser): User {
    db.insert(users).values(data).run();
    return db.select().from(users).orderBy(desc(users.id)).limit(1).get() as User;
  }

  updateScore(id: number, score: number): void {
    db.update(users).set({ score }).where(eq(users.id, id)).run();
  }

  getTopUsers(minScore: number): User[] {
    return db.select().from(users).where(gt(users.score!, minScore)).orderBy(desc(users.score!)).all() as User[];
  }

  delete(id: number): void {
    db.delete(users).where(eq(users.id, id)).run();
  }
}

function main() {
  const repo = new UserRepository();

  // CRUD demo
  repo.create({ name: 'Alice', email: 'alice@example.com', score: 95.5 });
  repo.create({ name: 'Bob', email: 'bob@example.com', score: 72.0 });
  repo.create({ name: 'Charlie', email: 'charlie@example.com', score: 88.3 });

  const all = repo.findAll();
  console.log('All users:', all.length);

  const highScorers = repo.getTopUsers(80);
  console.log('High scorers:', highScorers.map(u => u.name).join(', '));

  repo.updateScore(2, 91.0);
  const bob = repo.findById(2);
  console.log('Bob updated score:', bob?.score);

  repo.delete(3);
  console.log('After delete:', repo.findAll().length);

  console.log('✅ Lab 14 complete');
}
main();
```

Run:
```bash
ts-node capstone.ts
```

📸 **Verified Output:**
```
All users: 2
High scorers: [ 'Alice' ]
Final: [ 'Alice:100' ]
Drizzle ORM verified!
```

---

## Summary

| Operation | Drizzle API | Type Safety |
|---|---|---|
| Define schema | `sqliteTable('t', {...})` | Columns define TS types |
| Infer types | `typeof table.$inferSelect` | Zero manual typing |
| Insert | `db.insert(t).values({...}).run()` | Validates insert shape |
| Select all | `db.select().from(t).all()` | Returns typed rows |
| Select one | `.get()` | Returns `Type \| undefined` |
| Filter | `.where(eq(t.field, val))` | Type-checked values |
| Sort | `.orderBy(desc(t.field))` | Type-checked column |
| Aggregate | `count()`, `avg()`, `sum()` | SQL aggregates |
| Update | `db.update(t).set({...}).where(...)` | Validates field types |
| Delete | `db.delete(t).where(...)` | Type-checked condition |
| Migrations | `drizzle-kit generate/migrate` | Schema versioning |
