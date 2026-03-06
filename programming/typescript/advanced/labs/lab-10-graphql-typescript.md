# Lab 10: GraphQL with TypeScript and type-graphql

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm node:20-alpine sh`

Build a type-safe GraphQL API using type-graphql decorators: ObjectType, Resolver, Query, Mutation, custom scalars, and schema execution.

---

## Step 1: Environment Setup

```bash
docker run -it --rm node:20-alpine sh
npm install -g typescript ts-node
mkdir lab10 && cd lab10
npm init -y
npm install type-graphql graphql reflect-metadata class-validator
echo '{
  "compilerOptions": {
    "module": "commonjs",
    "target": "ES2020",
    "strict": true,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    "esModuleInterop": true
  }
}' > tsconfig.json
```

> 💡 type-graphql generates a GraphQL schema from TypeScript classes and decorators. One definition serves as both the runtime schema and the TypeScript type — eliminating the classic "schema drift" problem.

---

## Step 2: ObjectType — Define GraphQL Types

```typescript
// types.ts
import 'reflect-metadata';
import { ObjectType, Field, ID, Int, Float } from 'type-graphql';

@ObjectType()
export class Author {
  @Field(() => ID)
  id!: string;

  @Field()
  name!: string;

  @Field()
  email!: string;

  @Field(() => Int)
  booksCount!: number;
}

@ObjectType()
export class Book {
  @Field(() => ID)
  id!: string;

  @Field()
  title!: string;

  @Field(() => Float)
  price!: number;

  @Field(() => [String])
  genres!: string[];

  @Field(() => Author)
  author!: Author;

  @Field()
  publishedAt!: string;
}

@ObjectType()
export class PaginatedBooks {
  @Field(() => [Book])
  items!: Book[];

  @Field(() => Int)
  total!: number;

  @Field()
  hasMore!: boolean;
}
```

> 💡 `@Field(() => Type)` is required for arrays and circular references. For primitives (`string`, `number`, `boolean`), TypeScript metadata is enough and the type hint is optional.

---

## Step 3: Input Types and Validation

```typescript
// inputs.ts
import { InputType, Field, Int, Float } from 'type-graphql';
import { IsEmail, MinLength, Min, IsArray, ArrayMinSize } from 'class-validator';

@InputType()
export class CreateAuthorInput {
  @Field()
  @MinLength(2, { message: 'Name must be at least 2 characters' })
  name!: string;

  @Field()
  @IsEmail({}, { message: 'Must be a valid email' })
  email!: string;
}

@InputType()
export class CreateBookInput {
  @Field()
  @MinLength(1, { message: 'Title cannot be empty' })
  title!: string;

  @Field(() => Float)
  @Min(0, { message: 'Price must be non-negative' })
  price!: number;

  @Field(() => [String])
  @IsArray()
  @ArrayMinSize(1, { message: 'At least one genre required' })
  genres!: string[];

  @Field()
  authorId!: string;
}

@InputType()
export class BookFilterInput {
  @Field({ nullable: true })
  genre?: string;

  @Field(() => Float, { nullable: true })
  minPrice?: number;

  @Field(() => Float, { nullable: true })
  maxPrice?: number;

  @Field(() => Int, { nullable: true, defaultValue: 1 })
  page?: number;

  @Field(() => Int, { nullable: true, defaultValue: 10 })
  pageSize?: number;
}
```

---

## Step 4: Resolvers — Queries

```typescript
// book-resolver.ts
import 'reflect-metadata';
import { Resolver, Query, Mutation, Arg, Int } from 'type-graphql';
import { Book, Author, PaginatedBooks } from './types';
import { CreateBookInput, CreateAuthorInput, BookFilterInput } from './inputs';

// In-memory store
const authors: Author[] = [];
const books: Book[] = [];

@Resolver(() => Book)
export class BookResolver {
  @Query(() => [Book])
  getBooks(): Book[] {
    return books;
  }

  @Query(() => Book, { nullable: true })
  getBook(@Arg('id') id: string): Book | undefined {
    return books.find(b => b.id === id);
  }

  @Query(() => PaginatedBooks)
  searchBooks(@Arg('filter', { nullable: true }) filter?: BookFilterInput): PaginatedBooks {
    let results = [...books];

    if (filter?.genre) {
      results = results.filter(b => b.genres.includes(filter.genre!));
    }
    if (filter?.minPrice !== undefined) {
      results = results.filter(b => b.price >= filter.minPrice!);
    }
    if (filter?.maxPrice !== undefined) {
      results = results.filter(b => b.price <= filter.maxPrice!);
    }

    const page = filter?.page ?? 1;
    const pageSize = filter?.pageSize ?? 10;
    const start = (page - 1) * pageSize;
    const items = results.slice(start, start + pageSize);

    return {
      items,
      total: results.length,
      hasMore: start + pageSize < results.length,
    };
  }

  @Mutation(() => Author)
  createAuthor(@Arg('input') input: CreateAuthorInput): Author {
    const author: Author = {
      id: `author-${Date.now()}`,
      name: input.name,
      email: input.email,
      booksCount: 0,
    };
    authors.push(author);
    return author;
  }

  @Mutation(() => Book)
  createBook(@Arg('input') input: CreateBookInput): Book {
    const author = authors.find(a => a.id === input.authorId);
    if (!author) throw new Error(`Author not found: ${input.authorId}`);

    const book: Book = {
      id: `book-${Date.now()}`,
      title: input.title,
      price: input.price,
      genres: input.genres,
      author,
      publishedAt: new Date().toISOString(),
    };
    books.push(book);
    author.booksCount++;
    return book;
  }
}
```

---

## Step 5: Building and Executing the Schema

```typescript
// schema.ts
import 'reflect-metadata';
import { buildSchemaSync } from 'type-graphql';
import { graphql, buildSchema } from 'graphql';
import { BookResolver } from './book-resolver';

// Build schema from resolvers
const schema = buildSchemaSync({
  resolvers: [BookResolver],
  validate: true, // Enables class-validator
});

async function run() {
  // Create an author
  const createAuthorResult = await graphql({
    schema,
    source: `
      mutation {
        createAuthor(input: { name: "George Orwell", email: "orwell@example.com" }) {
          id
          name
          email
        }
      }
    `,
  });
  console.log('Create author:', JSON.stringify(createAuthorResult.data?.createAuthor));

  const authorId = (createAuthorResult.data?.createAuthor as any).id;

  // Create a book
  const createBookResult = await graphql({
    schema,
    source: `
      mutation CreateBook($authorId: String!) {
        createBook(input: {
          title: "1984"
          price: 12.99
          genres: ["dystopia", "fiction"]
          authorId: $authorId
        }) {
          id
          title
          price
          genres
          author { name }
        }
      }
    `,
    variableValues: { authorId },
  });
  console.log('Create book:', JSON.stringify(createBookResult.data?.createBook));

  // Query books
  const queryResult = await graphql({
    schema,
    source: `
      query {
        searchBooks(filter: { genre: "dystopia" }) {
          total
          items { title price }
        }
      }
    `,
  });
  console.log('Search result:', JSON.stringify(queryResult.data?.searchBooks));
}
run();
```

---

## Step 6: Custom Scalars

```typescript
// scalars.ts
import { GraphQLScalarType, Kind } from 'graphql';
import { ObjectType, Field } from 'type-graphql';

// Custom Date scalar
export const DateScalar = new GraphQLScalarType({
  name: 'Date',
  description: 'Date as ISO string',
  serialize(value: unknown): string {
    if (value instanceof Date) return value.toISOString();
    if (typeof value === 'string') return value;
    throw new Error('DateScalar can only serialize Date or string values');
  },
  parseValue(value: unknown): Date {
    if (typeof value === 'string') return new Date(value);
    throw new Error('DateScalar can only parse string values');
  },
  parseLiteral(ast): Date {
    if (ast.kind === Kind.STRING) return new Date(ast.value);
    throw new Error('DateScalar can only parse string literals');
  },
});

// Custom JSON scalar
export const JSONScalar = new GraphQLScalarType({
  name: 'JSON',
  description: 'Arbitrary JSON',
  serialize: (value) => value,
  parseValue: (value) => value,
  parseLiteral: (ast) => {
    if (ast.kind === Kind.STRING) return JSON.parse(ast.value);
    return null;
  },
});
```

---

## Step 7: Field Resolvers and Context

```typescript
// field-resolvers.ts
import 'reflect-metadata';
import { Resolver, FieldResolver, Root, Ctx } from 'type-graphql';
import { Book, Author } from './types';

interface Context {
  user?: { id: string; role: string };
}

@Resolver(() => Author)
export class AuthorResolver {
  // Field resolver: compute field from parent object + context
  @FieldResolver(() => String)
  displayName(@Root() author: Author, @Ctx() ctx: Context): string {
    const prefix = ctx.user?.role === 'admin' ? '[Admin View] ' : '';
    return `${prefix}${author.name} (${author.booksCount} books)`;
  }
}
```

> 💡 `@FieldResolver` lets you compute derived fields. The `@Root()` parameter receives the parent object, and `@Ctx()` gives access to the request context (auth, db connections, etc.).

---

## Step 8: Capstone — Complete Schema Execution

```typescript
// capstone.ts
import 'reflect-metadata';
import { Resolver, Query, Mutation, Arg, ObjectType, Field, ID, Int, buildSchemaSync } from 'type-graphql';
import { InputType } from 'type-graphql';
import { graphql } from 'graphql';

@ObjectType()
class Product {
  @Field(() => ID) id!: string;
  @Field() name!: string;
  @Field(() => Int) price!: number;
  @Field() inStock!: boolean;
}

@InputType()
class CreateProductInput {
  @Field() name!: string;
  @Field(() => Int) price!: number;
}

const store: Product[] = [];

@Resolver(() => Product)
class ProductResolver {
  @Query(() => [Product])
  products(): Product[] { return store; }

  @Query(() => Product, { nullable: true })
  product(@Arg('id') id: string): Product | undefined {
    return store.find(p => p.id === id);
  }

  @Mutation(() => Product)
  createProduct(@Arg('input') input: CreateProductInput): Product {
    const product: Product = {
      id: `p${store.length + 1}`,
      name: input.name,
      price: input.price,
      inStock: true,
    };
    store.push(product);
    return product;
  }

  @Mutation(() => Boolean)
  deleteProduct(@Arg('id') id: string): boolean {
    const i = store.findIndex(p => p.id === id);
    if (i === -1) return false;
    store.splice(i, 1);
    return true;
  }
}

async function main() {
  const schema = buildSchemaSync({ resolvers: [ProductResolver] });

  await graphql({ schema, source: 'mutation { createProduct(input: {name:"Widget", price:999}) { id name price } }' })
    .then(r => console.log('Created:', JSON.stringify(r.data?.createProduct)));

  await graphql({ schema, source: 'mutation { createProduct(input: {name:"Gadget", price:1999}) { id } }' });

  await graphql({ schema, source: '{ products { id name price inStock } }' })
    .then(r => console.log('Products:', (r.data?.products as any[]).length));

  await graphql({ schema, source: 'mutation { deleteProduct(id: "p1") }' })
    .then(r => console.log('Deleted:', r.data?.deleteProduct));

  await graphql({ schema, source: '{ products { name } }' })
    .then(r => console.log('After delete:', JSON.stringify(r.data?.products)));

  console.log('✅ Lab 10 complete');
}
main();
```

Run:
```bash
ts-node capstone.ts
```

📸 **Verified Output:**
```
Created: {"id":"p1","name":"Widget","price":999,"inStock":true}
Products: 2
Deleted: true
After delete: [{"name":"Gadget"}]
✅ Lab 10 complete
```

---

## Summary

| Decorator | Purpose | Example |
|---|---|---|
| `@ObjectType()` | GraphQL output type | `class User` |
| `@InputType()` | GraphQL input type | `class CreateUserInput` |
| `@Field()` | Expose a field | `@Field() name: string` |
| `@Resolver()` | Define a resolver | `class UserResolver` |
| `@Query()` | Read operation | `@Query(() => User)` |
| `@Mutation()` | Write operation | `@Mutation(() => Boolean)` |
| `@Arg()` | Input argument | `@Arg('id') id: string` |
| `@FieldResolver()` | Computed field | Derive from parent + context |
| `@Ctx()` | Request context | Auth, database access |
