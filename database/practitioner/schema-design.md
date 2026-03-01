# Schema Design & Normalization

## Database Normalization

### 1NF — First Normal Form
- Each column has atomic values
- No repeating groups

```sql
-- ❌ Violates 1NF
CREATE TABLE orders (
    id INT,
    items VARCHAR(500)  -- "Surface Pro, Xbox, Keyboard" (multiple values in one field)
);

-- ✅ 1NF
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT
);
```

### 2NF — No Partial Dependencies
All non-key columns depend on the **whole** primary key.

### 3NF — No Transitive Dependencies
Non-key columns depend only on the primary key, not on other non-key columns.

## Common Design Patterns

### One-to-Many

```sql
-- One user has many orders
CREATE TABLE users (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE orders (
    id INT PRIMARY KEY,
    user_id INT REFERENCES users(id),
    total DECIMAL(10,2)
);
```

### Many-to-Many

```sql
-- Many products in many orders
CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100), price DECIMAL(10,2));
CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, total DECIMAL(10,2));

-- Junction table
CREATE TABLE order_items (
    order_id INT REFERENCES orders(id),
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
```

### Self-Referencing (Hierarchical)

```sql
CREATE TABLE categories (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    parent_id INT REFERENCES categories(id)  -- NULL = top-level
);

-- Example data
INSERT INTO categories VALUES (1, 'Electronics', NULL);
INSERT INTO categories VALUES (2, 'Computers', 1);
INSERT INTO categories VALUES (3, 'Surface', 2);
```

## Choosing SQL vs NoSQL

| Criteria | SQL (PostgreSQL/MySQL) | NoSQL (MongoDB/Redis) |
|----------|----------------------|----------------------|
| Data structure | Fixed schema | Flexible/dynamic |
| Relationships | Complex joins | Embedded documents |
| Consistency | ACID guaranteed | Eventual consistency |
| Scaling | Vertical (mostly) | Horizontal |
| Best for | Financial, inventory | User profiles, catalogs |
