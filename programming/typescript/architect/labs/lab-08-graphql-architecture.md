# Lab 08: Type-Safe GraphQL Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `node:20-alpine`

## Overview

Type-safe GraphQL with Pothos schema builder (code-first), GraphQL Yoga server, DataLoader for N+1 prevention, generated types via graphql-code-generator, and gql.tada for type-safe client queries.

---

## Step 1: Pothos — Code-First Schema Builder

```typescript
import SchemaBuilder from '@pothos/core';

interface Types {
  Objects: {
    User:  User;
    Post:  Post;
    Query: {};
  };
  Scalars: {
    Date: { Input: Date; Output: Date };
  };
  Context: {
    userId: string;
    db: Database;
    loaders: DataLoaders;
  };
}

const builder = new SchemaBuilder<Types>({});

// Define types — fully inferred from TypeScript interfaces
builder.objectType('User', {
  description: 'A registered user',
  fields: (t) => ({
    id:    t.exposeString('id'),
    name:  t.exposeString('name'),
    email: t.exposeString('email'),
    // Computed field
    displayName: t.field({
      type: 'String',
      resolve: (user) => `${user.name} <${user.email}>`,
    }),
    // Relation — loaded via DataLoader
    posts: t.field({
      type: ['Post'],
      resolve: (user, _args, ctx) => ctx.loaders.postsByUserId.load(user.id),
    }),
  }),
});
```

---

## Step 2: Queries and Mutations

```typescript
builder.queryType({
  fields: (t) => ({
    user: t.field({
      type: 'User',
      nullable: true,
      args: { id: t.arg.string({ required: true }) },
      resolve: (_parent, { id }, ctx) => ctx.db.users.findById(id),
    }),

    users: t.field({
      type: ['User'],
      args: {
        limit:  t.arg.int({ defaultValue: 10 }),
        offset: t.arg.int({ defaultValue: 0 }),
        role:   t.arg({ type: UserRoleEnum, required: false }),
      },
      resolve: (_parent, { limit, offset, role }, ctx) =>
        ctx.db.users.findMany({ limit, offset, where: role ? { role } : undefined }),
    }),
  }),
});

builder.mutationType({
  fields: (t) => ({
    createUser: t.field({
      type: 'User',
      args: {
        input: t.arg({ type: CreateUserInput, required: true }),
      },
      resolve: async (_parent, { input }, ctx) => {
        // Zod validation
        const validated = CreateUserSchema.parse(input);
        return ctx.db.users.create(validated);
      },
    }),
  }),
});

const schema = builder.toSchema();
```

---

## Step 3: DataLoader — N+1 Prevention

```typescript
import DataLoader from 'dataloader';

// Without DataLoader: 1 + N queries
// Query { users { posts } } → 1 users query + N post queries

// With DataLoader: 2 queries total (batch + cache)
interface DataLoaders {
  postsByUserId: DataLoader<string, Post[]>;
  userById:      DataLoader<string, User | null>;
}

function createLoaders(db: Database): DataLoaders {
  return {
    // Batch: collect all user IDs in one tick, then fetch in one query
    postsByUserId: new DataLoader<string, Post[]>(
      async (userIds: readonly string[]) => {
        const posts = await db.posts.findByUserIds([...userIds]);
        // Group by userId — must return same length array as keys
        return userIds.map(id => posts.filter(p => p.authorId === id));
      },
      {
        cache: true,         // Cache within request (per-request instance)
        maxBatchSize: 100,   // Max IDs per batch
      }
    ),

    userById: new DataLoader<string, User | null>(
      async (ids: readonly string[]) => {
        const users = await db.users.findByIds([...ids]);
        const userMap = new Map(users.map(u => [u.id, u]));
        return ids.map(id => userMap.get(id) ?? null);
      }
    ),
  };
}

// Create loaders per request (not global — to avoid cache leaks)
app.use('/graphql', (req) => {
  const loaders = createLoaders(db);
  return yoga.handle(req, { db, loaders, userId: req.user?.id });
});
```

---

## Step 4: GraphQL Yoga Server

```typescript
import { createYoga } from 'graphql-yoga';
import { createServer } from 'node:http';

const yoga = createYoga({
  schema,
  context: async ({ request }) => {
    const token = request.headers.get('Authorization')?.split(' ')[1];
    const user = token ? await verifyJWT(token) : null;
    return {
      userId: user?.id,
      db,
      loaders: createLoaders(db),
    };
  },
  plugins: [
    // Depth limit — prevent deeply nested queries
    useDepthLimit({ maxDepth: 8 }),
    // Rate limiting
    useRateLimiter({ limit: 100, window: '1m' }),
    // Persisted queries — only allow known queries in production
    process.env.NODE_ENV === 'production' && usePersistedOperations({
      getPersistedOperation: (hash) => persistedQueryStore.get(hash),
    }),
  ].filter(Boolean),
  landingPage: process.env.NODE_ENV !== 'production',
});

const server = createServer(yoga);
server.listen(4000, () => console.log('GraphQL server: http://localhost:4000/graphql'));
```

---

## Step 5: Type-Safe Client with gql.tada

```typescript
// gql.tada: generates types from schema at build time (no codegen step)
import { initGraphQLTada } from 'gql.tada';
import type { introspection } from './graphql-env.d.ts';

const graphql = initGraphQLTada<{ introspection: introspection }>();

// Query — result type is inferred from the query string itself
const GetUserQuery = graphql(`
  query GetUser($id: String!) {
    user(id: $id) {
      id
      name
      email
      posts {
        id
        title
      }
    }
  }
`);

// ResultOf<typeof GetUserQuery> =
// { user: { id: string; name: string; email: string; posts: { id: string; title: string }[] } | null }

const result = await client.query(GetUserQuery, { id: '123' });
// result.data?.user?.posts[0].title — fully typed!
```

---

## Step 6: graphql-code-generator

```yaml
# codegen.yml
schema: 'http://localhost:4000/graphql'
documents: 'src/**/*.graphql'
generates:
  src/generated/graphql.ts:
    plugins:
      - typescript
      - typescript-operations
      - typescript-react-apollo   # if using Apollo Client
    config:
      strictScalars: true
      scalars:
        Date: string
        UUID: string
      nonOptionalTypename: true
      enumsAsTypes: true
```

```bash
npx graphql-codegen --config codegen.yml
# Generates:
# - TypeScript types for all schema types
# - Typed hooks: useGetUserQuery, useCreateUserMutation
# - Result types inferred from each query document
```

---

## Step 7: Input Validation at Schema Level

```typescript
import { ZodError } from 'zod';
import { GraphQLError } from 'graphql';

// Error plugin: convert Zod errors to GraphQL errors
const useZodValidation = (): Plugin => ({
  onResolverCalled: ({ resolverFn }) => {
    return async ({ result }) => {
      if (result instanceof ZodError) {
        throw new GraphQLError('Validation failed', {
          extensions: {
            code: 'VALIDATION_ERROR',
            issues: result.issues.map(i => ({
              path:    i.path.join('.'),
              message: i.message,
            })),
          },
        });
      }
    };
  },
});
```

---

## Step 8: Capstone — GraphQL Schema Execution

```bash
docker run --rm node:20-alpine sh -c "
  mkdir -p /work && cd /work && npm init -y > /dev/null 2>&1
  npm install graphql 2>&1 | tail -1
  node gql.js
"
```

*(gql.js runs the schema execution)*

📸 **Verified Output:**
```
=== GraphQL Schema Execution ===
  1 Alice alice@example.com
  2 Bob bob@example.com
Pothos builder: type-safe schema building with full TypeScript inference
```

---

## Summary

| Feature | Tool | Benefit |
|---------|------|---------|
| Code-first schema | Pothos | Types inferred from TS |
| N+1 prevention | DataLoader | Batch + cache per request |
| Server | GraphQL Yoga | Modern, pluggable |
| Type-safe client | gql.tada | No codegen step needed |
| Code generation | graphql-code-generator | Typed hooks + operations |
| Validation | Zod in resolvers | Runtime + type safety |
| Depth limit | Yoga plugin | DoS prevention |
| Persisted queries | Yoga plugin | Production security |
