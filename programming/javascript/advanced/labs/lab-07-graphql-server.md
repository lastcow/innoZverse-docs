# Lab 07: GraphQL Server

**Time:** 30 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

## Overview

Build a GraphQL API with `graphql-js`: SDL schema, resolvers, context, DataLoader (N+1 problem), subscriptions, error handling, and introspection.

---

## Step 1: Setup

```bash
cd /tmp && npm init -y --quiet
npm install graphql
```

---

## Step 2: Schema Definition Language (SDL)

```javascript
const { buildSchema } = require('graphql');

const schema = buildSchema(`
  # Scalar types
  scalar DateTime
  scalar JSON

  # Enums
  enum Role { ADMIN USER GUEST }
  enum SortOrder { ASC DESC }

  # Types
  type User {
    id: ID!
    name: String!
    email: String!
    role: Role!
    posts: [Post!]!
    createdAt: String
  }

  type Post {
    id: ID!
    title: String!
    content: String!
    published: Boolean!
    author: User!
    tags: [String!]!
  }

  # Input types
  input CreateUserInput {
    name: String!
    email: String!
    role: Role = USER
  }

  input PostFilter {
    published: Boolean
    authorId: ID
    tags: [String!]
  }

  # Query and Mutation
  type Query {
    user(id: ID!): User
    users(role: Role, limit: Int = 10, offset: Int = 0): [User!]!
    post(id: ID!): Post
    posts(filter: PostFilter, sortBy: String, order: SortOrder): [Post!]!
  }

  type Mutation {
    createUser(input: CreateUserInput!): User!
    updateUser(id: ID!, input: CreateUserInput!): User
    deleteUser(id: ID!): Boolean!
    publishPost(id: ID!): Post
  }
`);
```

---

## Step 3: Resolvers & Root Value

```javascript
const { graphql, buildSchema } = require('graphql');

const schema = buildSchema(`
  type User { id: ID! name: String! email: String! role: String! }
  type Post { id: ID! title: String! authorId: ID! published: Boolean! }
  type Query {
    user(id: ID!): User
    users: [User!]!
    post(id: ID!): Post
    posts(authorId: ID): [Post!]!
  }
  type Mutation {
    createUser(name: String!, email: String!): User!
    publishPost(id: ID!): Post
  }
`);

// In-memory data store
const db = {
  users: [
    { id: '1', name: 'Alice', email: 'alice@example.com', role: 'ADMIN' },
    { id: '2', name: 'Bob', email: 'bob@example.com', role: 'USER' }
  ],
  posts: [
    { id: '1', title: 'Getting Started', authorId: '1', published: true },
    { id: '2', title: 'Advanced Tips', authorId: '1', published: false },
    { id: '3', title: 'Bob\'s Post', authorId: '2', published: true }
  ],
  nextUserId: 3
};

const rootValue = {
  // Queries
  user: ({ id }) => db.users.find(u => u.id === id) ?? null,
  users: () => db.users,
  post: ({ id }) => db.posts.find(p => p.id === id) ?? null,
  posts: ({ authorId }) => authorId
    ? db.posts.filter(p => p.authorId === authorId)
    : db.posts,

  // Mutations
  createUser: ({ name, email }) => {
    const user = { id: String(db.nextUserId++), name, email, role: 'USER' };
    db.users.push(user);
    return user;
  },
  publishPost: ({ id }) => {
    const post = db.posts.find(p => p.id === id);
    if (!post) return null;
    post.published = true;
    return post;
  }
};

// Execute queries
(async () => {
  const r1 = await graphql({
    schema,
    source: '{ users { id name } }',
    rootValue
  });
  console.log('Users:', JSON.stringify(r1.data));

  const r2 = await graphql({
    schema,
    source: '{ user(id: "1") { name email } }',
    rootValue
  });
  console.log('User:', JSON.stringify(r2.data));

  const r3 = await graphql({
    schema,
    source: 'mutation { createUser(name: "Charlie", email: "c@ex.com") { id name } }',
    rootValue
  });
  console.log('Created:', JSON.stringify(r3.data));
})();
```

---

## Step 4: Context and DataLoader (N+1 Problem)

```javascript
const { graphql, buildSchema } = require('graphql');

// DataLoader implementation (without the npm package)
class DataLoader {
  #batchFn; #cache = new Map(); #queue = [];

  constructor(batchFn) { this.#batchFn = batchFn; }

  async load(key) {
    if (this.#cache.has(key)) return this.#cache.get(key);

    return new Promise((resolve, reject) => {
      this.#queue.push({ key, resolve, reject });
      if (this.#queue.length === 1) {
        Promise.resolve().then(() => this.#dispatch());
      }
    });
  }

  async #dispatch() {
    const batch = this.#queue.splice(0);
    const keys = batch.map(item => item.key);
    try {
      const results = await this.#batchFn(keys);
      batch.forEach(({ key, resolve }, i) => {
        this.#cache.set(key, results[i]);
        resolve(results[i]);
      });
    } catch (err) {
      batch.forEach(({ reject }) => reject(err));
    }
  }
}

// Without DataLoader: N+1 queries
// GET /posts -> 3 posts
// GET /user/1, GET /user/1, GET /user/2 -> 3 user queries (2 duplicates!)

// With DataLoader: batched
// GET /posts -> 3 posts
// GET /users/[1,2] -> 1 batched user query!

// Create loaders per request (in context)
function createContext(db) {
  return {
    db,
    loaders: {
      user: new DataLoader(async (ids) => {
        console.log(`BatchLoad users: [${ids}]`); // Verify batching!
        const users = ids.map(id => db.users.find(u => u.id === id) ?? null);
        return users;
      })
    }
  };
}
```

---

## Step 5: Error Handling

```javascript
const { graphql, buildSchema, GraphQLError } = require('graphql');

// GraphQL errors
function createError(message, code, statusCode = 400, extensions = {}) {
  return new GraphQLError(message, {
    extensions: { code, statusCode, ...extensions }
  });
}

const resolvers = {
  user: ({ id }, context) => {
    const user = context.db.users.find(u => u.id === id);
    if (!user) {
      throw createError(`User ${id} not found`, 'NOT_FOUND', 404);
    }
    return user;
  },

  createUser: ({ name, email }, context) => {
    if (!email.includes('@')) {
      throw createError('Invalid email format', 'VALIDATION_ERROR', 400, { field: 'email' });
    }
    if (context.db.users.some(u => u.email === email)) {
      throw createError('Email already exists', 'CONFLICT', 409);
    }
    // ... create user
  }
};

// Error formatting
function formatError(err) {
  const { code = 'INTERNAL', statusCode = 500 } = err.extensions ?? {};
  return {
    message: err.message,
    code,
    statusCode,
    locations: err.locations,
    path: err.path
  };
}
```

---

## Step 6: Introspection

```javascript
const { graphql, buildSchema, getIntrospectionQuery } = require('graphql');

// Introspection — discover schema at runtime
const schema = buildSchema(`
  type Query { hello: String greet(name: String!): String }
`);

const root = {
  hello: () => 'Hello World!',
  greet: ({ name }) => `Hello ${name}!`
};

(async () => {
  // Execute introspection query
  const introspectionResult = await graphql({
    schema,
    source: getIntrospectionQuery()
  });

  const types = introspectionResult.data.__schema.types
    .filter(t => !t.name.startsWith('__'))
    .map(t => `${t.kind}: ${t.name}`);
  console.log('Schema types:', types);

  // Simpler type listing
  const result = await graphql({
    schema,
    source: `{
      __schema {
        queryType { name }
        types { name kind }
      }
    }`
  });
  const queryTypes = result.data.__schema.types
    .filter(t => !t.name.startsWith('_'))
    .map(t => t.name);
  console.log('User-defined types:', queryTypes);
})();
```

---

## Step 7: Subscriptions Concept

```javascript
// Subscriptions for real-time updates
const { buildSchema } = require('graphql');

const schema = buildSchema(`
  type Subscription {
    messageAdded(channelId: ID!): Message!
    userStatusChanged: UserStatus!
  }

  type Message { id: ID! content: String! userId: ID! channelId: ID! }
  type UserStatus { userId: ID! online: Boolean! }
  type Query { _unused: Boolean }
`);

// In practice, subscriptions use AsyncIterator
// Example with graphql-subscriptions package:
/*
const { PubSub } = require('graphql-subscriptions');
const pubsub = new PubSub();

const resolvers = {
  Subscription: {
    messageAdded: {
      subscribe: (_, { channelId }) =>
        pubsub.asyncIterator(`MESSAGE_ADDED:${channelId}`)
    }
  },
  Mutation: {
    addMessage: (_, { content, channelId }, { userId }) => {
      const message = { id: uuid(), content, userId, channelId };
      pubsub.publish(`MESSAGE_ADDED:${channelId}`, { messageAdded: message });
      return message;
    }
  }
};
*/

console.log('Subscriptions require WebSocket transport (graphql-ws or subscriptions-transport-ws)');
```

---

## Step 8: Capstone — Full GraphQL Demo

```bash
docker run --rm node:20-alpine sh -c "
cd /tmp && npm init -y --quiet > /dev/null && npm install graphql --quiet > /dev/null 2>&1
node -e '
const { graphql, buildSchema } = require(\"/tmp/node_modules/graphql\");
const schema = buildSchema(\`type Query { hello: String greet(name: String!): String }\`);
const root = { hello: () => \"Hello World!\", greet: ({name}) => \"Hello \" + name + \"!\" };
(async () => {
  const r = await graphql({ schema, source: \"{ hello greet(name: \\\"Alice\\\") }\", rootValue: root });
  console.log(JSON.stringify(r.data));
})();
'" 2>/dev/null
```

📸 **Verified Output:**
```
{"hello":"Hello World!","greet":"Hello Alice!"}
```

---

## Summary

| GraphQL Concept | SDL | Purpose |
|----------------|-----|---------|
| Type | `type User { id: ID! }` | Define data shape |
| Query | `type Query { user(id: ID!): User }` | Read operations |
| Mutation | `type Mutation { createUser: User! }` | Write operations |
| Subscription | `type Subscription { msgAdded: Msg }` | Real-time events |
| Input | `input CreateUser { name: String! }` | Mutation arguments |
| Enum | `enum Role { ADMIN USER }` | Fixed value set |
| DataLoader | `new DataLoader(batchFn)` | Batch + cache lookups |
| Context | 3rd resolver arg | Request-scoped data |
| Introspection | `__schema`, `__type` | Schema discovery |
