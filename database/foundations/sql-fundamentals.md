# SQL Fundamentals

SQL (Structured Query Language) is the standard language for relational databases.

## Core Operations (CRUD)

```sql
-- CREATE
INSERT INTO users (name, email, age) VALUES ('Alice', 'alice@example.com', 30);
INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com');

-- READ
SELECT * FROM users;
SELECT name, email FROM users WHERE age > 25;
SELECT * FROM users ORDER BY name ASC LIMIT 10;

-- UPDATE
UPDATE users SET age = 31 WHERE email = 'alice@example.com';
UPDATE users SET status = 'active' WHERE created_at > '2026-01-01';

-- DELETE
DELETE FROM users WHERE email = 'alice@example.com';
DELETE FROM users WHERE status = 'inactive' AND last_login < '2025-01-01';
```

## Filtering & Operators

```sql
-- Comparison
WHERE age = 30
WHERE age != 30
WHERE age > 25 AND age < 40
WHERE age BETWEEN 25 AND 40
WHERE age IN (25, 30, 35)
WHERE name LIKE 'Al%'        -- Starts with "Al"
WHERE name LIKE '%son'       -- Ends with "son"
WHERE email IS NULL
WHERE email IS NOT NULL
```

## Aggregate Functions

```sql
SELECT COUNT(*) FROM users;
SELECT COUNT(DISTINCT country) FROM users;
SELECT AVG(price) FROM products;
SELECT SUM(quantity) FROM order_items WHERE order_id = 100;
SELECT MIN(price), MAX(price) FROM products WHERE category = 'Surface Pro';

-- GROUP BY
SELECT category, COUNT(*) as count, AVG(price) as avg_price
FROM products
GROUP BY category
HAVING COUNT(*) > 10
ORDER BY avg_price DESC;
```

## JOINs

```sql
-- INNER JOIN (only matching rows)
SELECT u.name, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- LEFT JOIN (all from left, matching from right)
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;

-- Multiple JOINs
SELECT u.name, p.name as product, oi.quantity
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.created_at > '2026-01-01';
```

## Subqueries & CTEs

```sql
-- Subquery
SELECT name FROM users
WHERE id IN (SELECT user_id FROM orders WHERE total > 500);

-- CTE (Common Table Expression) — cleaner
WITH high_value_customers AS (
    SELECT user_id, SUM(total) as lifetime_value
    FROM orders
    GROUP BY user_id
    HAVING SUM(total) > 1000
)
SELECT u.name, h.lifetime_value
FROM users u
JOIN high_value_customers h ON u.id = h.user_id
ORDER BY h.lifetime_value DESC;
```
