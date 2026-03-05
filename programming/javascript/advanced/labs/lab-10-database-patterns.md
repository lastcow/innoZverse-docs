# Lab 10: Database Patterns

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Master database patterns with Node.js: Knex.js query builder, ORM patterns (Sequelize/Prisma concepts), connection pooling, transactions, migrations, seeds, and the Repository pattern.

---

## Step 1: Setup Knex with SQLite

```bash
cd /tmp && npm init -y --quiet
npm install knex better-sqlite3
```

```javascript
const knex = require('knex')({
  client: 'better-sqlite3',
  connection: { filename: ':memory:' }, // In-memory for testing
  useNullAsDefault: true,
  pool: {
    min: 1,
    max: 5,
    afterCreate: (conn, done) => {
      // Enable WAL mode for better concurrent reads
      conn.pragma('journal_mode = WAL');
      conn.pragma('foreign_keys = ON');
      done(null, conn);
    }
  },
  debug: false
});

module.exports = knex;
```

---

## Step 2: Migrations

```javascript
const knex = require('./db');

// Create migrations programmatically
async function runMigrations() {
  // Users table
  await knex.schema.createTableIfNotExists('users', (table) => {
    table.increments('id').primary();
    table.string('name', 100).notNullable();
    table.string('email', 255).unique().notNullable();
    table.enum('role', ['admin', 'user', 'guest']).defaultTo('user');
    table.boolean('active').defaultTo(true);
    table.timestamps(true, true); // created_at, updated_at
  });

  // Posts table with foreign key
  await knex.schema.createTableIfNotExists('posts', (table) => {
    table.increments('id').primary();
    table.string('title', 255).notNullable();
    table.text('content');
    table.boolean('published').defaultTo(false);
    table.integer('author_id').unsigned().references('id').inTable('users').onDelete('CASCADE');
    table.json('tags').defaultTo('[]');
    table.timestamps(true, true);
  });

  // Comments table
  await knex.schema.createTableIfNotExists('comments', (table) => {
    table.increments('id').primary();
    table.text('body').notNullable();
    table.integer('post_id').unsigned().references('id').inTable('posts').onDelete('CASCADE');
    table.integer('user_id').unsigned().references('id').inTable('users').onDelete('SET NULL');
    table.timestamps(true, true);
  });

  console.log('Migrations complete');
}
```

---

## Step 3: Seeds

```javascript
async function seedDatabase(knex) {
  await knex('users').insert([
    { name: 'Alice Admin', email: 'alice@example.com', role: 'admin' },
    { name: 'Bob User', email: 'bob@example.com', role: 'user' },
    { name: 'Charlie', email: 'charlie@example.com', role: 'user' }
  ]);

  const [alice, bob] = await knex('users').select('id').orderBy('id');

  await knex('posts').insert([
    { title: 'Getting Started', content: 'Hello World!', published: true, author_id: alice.id, tags: '["intro","beginner"]' },
    { title: 'Advanced Tips', content: 'Pro stuff here', published: true, author_id: alice.id, tags: '["advanced"]' },
    { title: 'Draft Post', content: 'WIP...', published: false, author_id: bob.id, tags: '[]' }
  ]);

  console.log('Seeds complete');
}
```

---

## Step 4: Query Builder Patterns

```javascript
async function queries(knex) {
  // Basic SELECT
  const users = await knex('users').select('id', 'name', 'email').where('active', true);
  console.log('Users:', users.length);

  // WHERE clauses
  const admins = await knex('users').where({ role: 'admin', active: true });
  const recent = await knex('posts')
    .where('published', true)
    .where('created_at', '>', '2024-01-01')
    .orderBy('created_at', 'desc')
    .limit(10);

  // JOIN
  const postsWithAuthors = await knex('posts')
    .select('posts.*', 'users.name as author_name', 'users.email as author_email')
    .join('users', 'posts.author_id', '=', 'users.id')
    .where('posts.published', true);

  console.log('Published posts:', postsWithAuthors.map(p => `${p.title} by ${p.author_name}`));

  // Subquery
  const usersWithPosts = await knex('users')
    .whereExists(
      knex('posts').select('id').whereRaw('posts.author_id = users.id')
    );

  // Aggregates
  const stats = await knex('posts')
    .select('users.name')
    .count('posts.id as post_count')
    .sum(knex.raw('CASE WHEN posts.published THEN 1 ELSE 0 END AS published_count'))
    .join('users', 'posts.author_id', 'users.id')
    .groupBy('users.id', 'users.name')
    .orderBy('post_count', 'desc');

  console.log('Author stats:', stats);

  // Raw queries (when needed)
  const raw = await knex.raw(
    'SELECT * FROM users WHERE email LIKE ? LIMIT ?',
    ['%@example.com', 5]
  );
  console.log('Raw query results:', raw.length ?? raw.rows?.length);
}
```

---

## Step 5: Transactions

```javascript
async function transactionExamples(knex) {
  // Simple transaction
  await knex.transaction(async (trx) => {
    const [userId] = await trx('users').insert({ name: 'Dave', email: 'dave@example.com' });
    await trx('posts').insert({
      title: 'My First Post',
      author_id: userId,
      published: true
    });
    // Both committed together
  });

  // Transaction with rollback on error
  try {
    await knex.transaction(async (trx) => {
      await trx('users').update({ active: false }).where('id', 999); // 0 rows
      const count = await trx('users').count('id as cnt').first();
      if (count.cnt < 0) throw new Error('Constraint violated');
      // This throw would rollback
    });
  } catch (e) {
    console.log('Transaction rolled back:', e.message);
  }

  // Savepoints (nested transactions)
  await knex.transaction(async (outerTrx) => {
    await outerTrx('users').update({ active: true }).where('role', 'user');

    try {
      await outerTrx.transaction(async (innerTrx) => {
        await innerTrx('users').update({ role: 'admin' }).where('id', 9999);
        throw new Error('Rollback inner only');
      });
    } catch {
      // Inner rolled back, outer continues
    }

    // Outer transaction still commits
  });

  console.log('Transaction examples complete');
}
```

---

## Step 6: Repository Pattern

```javascript
class UserRepository {
  #db;

  constructor(db) { this.#db = db; }

  async findById(id) {
    return this.#db('users').where({ id }).first() ?? null;
  }

  async findByEmail(email) {
    return this.#db('users').where({ email }).first() ?? null;
  }

  async findAll({ role, active = true, limit = 10, offset = 0 } = {}) {
    let query = this.#db('users').where({ active });
    if (role) query = query.where({ role });
    return query.select('id', 'name', 'email', 'role').limit(limit).offset(offset);
  }

  async create(data) {
    const [id] = await this.#db('users').insert(data);
    return this.findById(id);
  }

  async update(id, data) {
    await this.#db('users').where({ id }).update({ ...data, updated_at: new Date() });
    return this.findById(id);
  }

  async delete(id) {
    const deleted = await this.#db('users').where({ id }).delete();
    return deleted > 0;
  }

  async count(filters = {}) {
    const result = await this.#db('users').where(filters).count('id as cnt').first();
    return result.cnt;
  }

  // Transaction-aware methods
  withTransaction(trx) {
    return new UserRepository(trx);
  }
}
```

---

## Step 7: Connection Pooling

```javascript
// Knex manages a connection pool automatically
// Configure for production:
const productionConfig = {
  client: 'pg',
  connection: process.env.DATABASE_URL,
  pool: {
    min: 2,          // Minimum connections to keep alive
    max: 10,         // Maximum concurrent connections
    acquireTimeoutMillis: 30000,  // Wait max 30s for a connection
    idleTimeoutMillis: 600000,    // Close connections idle for 10min
    reapIntervalMillis: 1000,     // Check for idle connections every 1s

    afterCreate: (conn, done) => {
      conn.query('SET timezone="UTC";', err => done(err, conn));
    }
  },
  acquireConnectionTimeout: 10000
};

// Monitor pool health
async function poolStats(knex) {
  const pool = knex.client.pool;
  return {
    numUsed: pool.numUsed(),
    numFree: pool.numFree(),
    numPendingAcquires: pool.numPendingAcquires(),
    max: pool.max,
    min: pool.min
  };
}
```

---

## Step 8: Capstone — Full Demo

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && npm init -y --quiet > /dev/null
npm install knex better-sqlite3 --quiet > /dev/null 2>&1
node -e '
const knex = require(\"/tmp/node_modules/knex\")({
  client: \"better-sqlite3\",
  connection: { filename: \":memory:\" },
  useNullAsDefault: true
});
(async () => {
  await knex.schema.createTable(\"users\", t => {
    t.increments(\"id\"); t.string(\"name\").notNullable();
    t.string(\"email\").unique().notNullable(); t.timestamps(true, true);
  });
  await knex(\"users\").insert([
    { name: \"Alice\", email: \"alice@ex.com\" },
    { name: \"Bob\", email: \"bob@ex.com\" }
  ]);
  const users = await knex(\"users\").select(\"*\");
  console.log(\"Users:\", users.map(u => u.name));
  await knex.transaction(async trx => {
    await trx(\"users\").insert({ name: \"Charlie\", email: \"charlie@ex.com\" });
    const count = await trx(\"users\").count(\"id as cnt\").first();
    console.log(\"Count in tx:\", count.cnt);
  });
  await knex.destroy();
  console.log(\"Done\");
})();
'" 2>/dev/null
```

📸 **Verified Output:**
```
Users: [ 'Alice', 'Bob' ]
Count in tx: 3
Done
```

---

## Summary

| Pattern | Knex API | Use Case |
|---------|----------|----------|
| Schema migration | `knex.schema.createTable()` | Database versioning |
| Seeds | `knex('table').insert()` | Test data setup |
| Query builder | `knex('t').select().where().join()` | Type-safe queries |
| Transactions | `knex.transaction(async trx => {})` | Atomic operations |
| Raw queries | `knex.raw('SQL', [params])` | Complex queries |
| Connection pool | `pool: { min, max }` | Production config |
| Repository | Class wrapping DB calls | Testable data layer |
| Eager loading | `.join()` or separate queries + map | N+1 prevention |
