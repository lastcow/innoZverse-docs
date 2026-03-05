# Lab 01: Introduction to Relational Databases

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

In this lab you will understand the relational model, compare RDBMS to flat files, spin up MySQL 8 and PostgreSQL 15 with Docker, and run your first SQL commands.

---

## Step 1: The Relational Model

A **relational database** organizes data into **tables** (relations). Each table has:

| Concept | Description | Example |
|---------|-------------|---------|
| **Table** | A named collection of related data | `employees` |
| **Row** (tuple) | One record in the table | A single employee |
| **Column** (attribute) | A named field with a data type | `first_name VARCHAR(50)` |
| **Primary Key** | Uniquely identifies each row | `employee_id INT` |
| **Foreign Key** | Links to another table's PK | `department_id → departments.id` |

### RDBMS vs Flat Files

| Feature | Flat File (CSV) | RDBMS |
|---------|----------------|-------|
| Data integrity | None | Constraints enforced |
| Relationships | Manual (error-prone) | Foreign keys |
| Concurrent access | Dangerous | ACID transactions |
| Querying | Line-by-line parsing | SQL — set-based operations |
| Scalability | Poor | Indexing, partitioning |

> 💡 **Flat files** like CSVs are fine for small, single-use datasets. Once you need integrity, joins, or concurrent writes — you need an RDBMS.

---

## Step 2: Start MySQL 8 with Docker

```bash
# Pull and run MySQL 8
docker run -d \
  --name mysql-lab \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  mysql:8.0

# Wait until MySQL is ready (up to 60 seconds)
for i in $(seq 1 30); do
  docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2
done
echo "MySQL is ready!"
```

📸 **Verified Output:**
```
mysql: [Warning] Using a password on the command line interface can be insecure.
+---+
| 1 |
+---+
| 1 |
+---+
MySQL is ready!
```

---

## Step 3: Connect to MySQL and Explore

```bash
docker exec -it mysql-lab mysql -uroot -prootpass
```

Inside the MySQL shell:

```sql
-- Check version
SELECT VERSION();

-- List all databases
SHOW DATABASES;
```

📸 **Verified Output:**
```
+-----------+
| VERSION() |
+-----------+
| 8.0.36    |
+-----------+

+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
```

> 💡 The built-in databases (`mysql`, `information_schema`, etc.) are system databases. Never drop them.

---

## Step 4: Start PostgreSQL 15 with Docker

Open a **new terminal** (keep MySQL running):

```bash
# Pull and run PostgreSQL 15
docker run -d \
  --name pg-lab \
  -e POSTGRES_PASSWORD=rootpass \
  postgres:15

# Wait for PostgreSQL to be ready
sleep 10
docker exec pg-lab psql -U postgres -c "SELECT 1"
echo "PostgreSQL is ready!"
```

📸 **Verified Output:**
```
 ?column?
----------
        1
(1 row)

PostgreSQL is ready!
```

---

## Step 5: Connect to PostgreSQL and Explore

```bash
docker exec -it pg-lab psql -U postgres
```

Inside the psql shell:

```sql
-- Check version
SELECT VERSION();

-- List all databases (psql meta-command)
\l
```

📸 **Verified Output:**
```
                                                   version
--------------------------------------------------------------------------------------------------------------
 PostgreSQL 15.6 on x86_64-pc-linux-gnu, compiled by gcc (Debian 12.2.0-14) 12.2.0, 64-bit
(1 row)

                                                 List of databases
   Name    |  Owner   | Encoding |  Collate   |   Ctype    |   ICU Locale   | Locale Provider |   Access privileges
-----------+----------+----------+------------+------------+----------------+-----------------+-----------------------
 postgres  | postgres | UTF8     | en_US.utf8 | en_US.utf8 |                | libc            |
 template0 | postgres | UTF8     | en_US.utf8 | en_US.utf8 |                | libc            | =c/postgres          +
           |          |          |            |            |                |                 | postgres=CTc/postgres
 template1 | postgres | UTF8     | en_US.utf8 | en_US.utf8 |                | libc            | =c/postgres          +
           |          |          |            |            |                |                 | postgres=CTc/postgres
(3 rows)
```

> 💡 `\l` is a **psql meta-command** (not SQL). It lists databases. Use `\q` to quit psql, `\h` for SQL help, `\?` for meta-command help.

---

## Step 6: Key SQL Meta-Commands Comparison

| Action | MySQL | PostgreSQL |
|--------|-------|------------|
| List databases | `SHOW DATABASES;` | `\l` |
| Use a database | `USE dbname;` | `\c dbname` |
| List tables | `SHOW TABLES;` | `\dt` |
| Describe a table | `DESCRIBE tablename;` | `\d tablename` |
| Quit | `quit` or `exit` | `\q` |
| Show version | `SELECT VERSION();` | `SELECT VERSION();` |

---

## Step 7: Run a Cross-DB Comparison Query

**MySQL:**
```sql
SELECT VERSION(), USER(), NOW(), DATABASE();
```

📸 **Verified Output (MySQL):**
```
+-----------+----------------+---------------------+------------+
| VERSION() | USER()         | NOW()               | DATABASE() |
+-----------+----------------+---------------------+------------+
| 8.0.36    | root@localhost | 2024-01-15 10:30:00 | NULL       |
+-----------+----------------+---------------------+------------+
```

**PostgreSQL:**
```sql
SELECT VERSION(), CURRENT_USER, NOW(), CURRENT_DATABASE();
```

📸 **Verified Output (PostgreSQL):**
```
 version                                    | current_user |              now              | current_database
--------------------------------------------+--------------+-------------------------------+-----------------
 PostgreSQL 15.6 on x86_64-pc-linux-gnu... | postgres     | 2024-01-15 10:30:00.123456+00 | postgres
```

---

## Step 8: Capstone — Design a Conceptual Schema

Based on what you've learned, design a conceptual schema for a **Library Management System**.

Identify the tables, columns, and relationships:

```
Tables:
  books        (book_id PK, title, isbn, publication_year)
  authors      (author_id PK, first_name, last_name, birth_year)
  book_authors (book_id FK→books, author_id FK→authors)  ← many-to-many
  members      (member_id PK, name, email, join_date)
  loans        (loan_id PK, book_id FK→books, member_id FK→members, loan_date, return_date)

Relationships:
  books ←→ authors  (many-to-many via book_authors)
  members → loans   (one-to-many)
  books → loans     (one-to-many)
```

Now sketch why this is better than a flat CSV:
- No repeated author data for multi-author books
- `loans` can track due dates with foreign key integrity
- Querying "all books by Author X" is a single JOIN — not string parsing

**Cleanup:**
```bash
docker rm -f mysql-lab pg-lab
```

---

## Summary

| Topic | Key Takeaway |
|-------|-------------|
| Relational model | Tables, rows, columns, keys — set-based thinking |
| RDBMS vs flat files | Integrity, relationships, concurrency, SQL |
| MySQL 8 Docker | `docker run -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0` |
| PostgreSQL 15 Docker | `docker run -e POSTGRES_PASSWORD=rootpass postgres:15` |
| MySQL connect | `mysql -uroot -prootpass` → `SHOW DATABASES;` |
| PostgreSQL connect | `psql -U postgres` → `\l` |
| Version check | `SELECT VERSION();` (both DBs) |

**Next:** Lab 02 — Creating Databases and Tables
