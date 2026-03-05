# 🌱 Foundations — Database Labs

> **Learn to think in tables, rows, and relationships.**
> From your first SQL query to designing normalized databases — every concept taught hands-on with real engines.

**Technologies:** MySQL 8.0, PostgreSQL 15

---

## 🚀 Start Here → [Lab 01: Intro to Relational Databases](labs/lab-01-intro-relational-databases.md)

---

## 📋 Lab Index

| # | Lab | DB | Topics |
|---|-----|----|--------|
| 01 | [Intro to Relational Databases](labs/lab-01-intro-relational-databases.md) | MySQL 8 | Relational model, tables, rows, SQL intro, Docker setup |
| 02 | [Creating Databases and Tables](labs/lab-02-creating-databases-tables.md) | MySQL 8 | CREATE DATABASE, CREATE TABLE, data types, constraints |
| 03 | [Inserting and Querying Data](labs/lab-03-inserting-querying-data.md) | MySQL 8 | INSERT, SELECT, basic WHERE, LIMIT |
| 04 | [Filtering and Sorting](labs/lab-04-filtering-sorting.md) | MySQL 8 | WHERE, AND/OR, IN, BETWEEN, ORDER BY, LIMIT/OFFSET |
| 05 | [Aggregate Functions](labs/lab-05-aggregate-functions.md) | MySQL 8 | COUNT, SUM, AVG, MIN, MAX, GROUP BY, HAVING |
| 06 | [INNER JOIN](labs/lab-06-inner-join.md) | MySQL 8 | INNER JOIN, table aliases, multi-table queries |
| 07 | [Outer Joins](labs/lab-07-outer-joins.md) | MySQL 8 | LEFT/RIGHT/FULL OUTER JOIN, NULL handling in joins |
| 08 | [Subqueries](labs/lab-08-subqueries.md) | MySQL 8 | Scalar subqueries, IN, EXISTS, correlated subqueries |
| 09 | [Views](labs/lab-09-views.md) | MySQL 8 | CREATE VIEW, updatable views, security benefits |
| 10 | [Database Design & Normalization](labs/lab-10-database-design-normalization.md) | MySQL 8 | ERD, 1NF/2NF/3NF, functional dependencies |
| 11 | [Primary Keys, Foreign Keys & Constraints](labs/lab-11-primary-keys-foreign-keys-constraints.md) | MySQL 8 | PK, FK, UNIQUE, CHECK, NOT NULL, CASCADE |
| 12 | [Indexes Basics](labs/lab-12-indexes-basics.md) | MySQL 8 | CREATE INDEX, EXPLAIN, B-tree, composite indexes |
| 13 | [UPDATE and DELETE](labs/lab-13-update-delete.md) | MySQL 8 | UPDATE, DELETE, TRUNCATE, safe update patterns |
| 14 | [Transactions](labs/lab-14-transactions.md) | MySQL 8 | BEGIN/COMMIT/ROLLBACK, ACID properties, savepoints |
| 15 | [String Functions](labs/lab-15-string-functions.md) | MySQL 8 | CONCAT, SUBSTRING, UPPER/LOWER, REPLACE, LIKE, REGEXP |
| 16 | [Date and Time Functions](labs/lab-16-date-time-functions.md) | MySQL 8 | NOW(), DATE_FORMAT, DATEDIFF, DATE_ADD, EXTRACT |
| 17 | [NULL Handling](labs/lab-17-null-handling.md) | MySQL 8 | IS NULL, COALESCE, NULLIF, IFNULL, NULL in aggregations |
| 18 | [PostgreSQL JSONB & Arrays](labs/lab-18-postgresql-jsonb-arrays.md) | PostgreSQL 15 | JSONB operators, arrays, GIN indexes |
| 19 | [MySQL Specific Features](labs/lab-19-mysql-specific-features.md) | MySQL 8 | AUTO_INCREMENT, ENUM, SET, JSON functions, CTEs |
| 20 | [Capstone: E-Commerce Database](labs/lab-20-capstone-ecommerce-database.md) | MySQL 8 | Full e-commerce schema: products, orders, users, inventory |

---

## 🗂️ Learning Path

### Week 1: SQL Basics (Labs 1–7)
Start here if you've never written SQL. You'll go from installing MySQL to writing multi-table JOIN queries.

### Week 2: Intermediate SQL (Labs 8–14)
Subqueries, views, database design, normalization, and transactions — the skills that separate junior from mid-level.

### Week 3: Advanced SQL + Design (Labs 15–20)
Functions, NULL handling, PostgreSQL, and the capstone e-commerce project.

---

## 🛠️ Setup

```bash
# Install Docker (required for all labs)
docker run -d --name mysql-lab \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  mysql:8.0

# Wait for MySQL to start
for i in $(seq 1 30); do
  docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2
done

echo "MySQL ready!"
```
