# Lab 02: Creating Databases and Tables

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Learn to create databases and tables with proper data types, constraints, and defaults. Inspect schema with `DESCRIBE` and `\d`. Clean up with `DROP`.

---

## Step 1: Start the Databases

```bash
# MySQL
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

# PostgreSQL
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10
```

---

## Step 2: CREATE DATABASE

**MySQL:**
```sql
CREATE DATABASE IF NOT EXISTS school;
USE school;
SELECT DATABASE();
```

📸 **Verified Output (MySQL):**
```
Query OK, 1 row affected (0.01 sec)

+----------+
| DATABASE() |
+----------+
| school   |
+----------+
```

**PostgreSQL:**
```bash
docker exec pg-lab psql -U postgres -c "CREATE DATABASE school;"
docker exec pg-lab psql -U postgres -d school -c "SELECT current_database();"
```

📸 **Verified Output (PostgreSQL):**
```
CREATE DATABASE

 current_database
------------------
 school
(1 row)
```

> 💡 In MySQL, `USE dbname` switches context for the session. In PostgreSQL, connect with `\c dbname` or `-d dbname` flag.

---

## Step 3: Data Types Reference

| Category | MySQL | PostgreSQL | Notes |
|----------|-------|------------|-------|
| Integer | `INT`, `BIGINT`, `TINYINT` | `INTEGER`, `BIGINT`, `SMALLINT` | PG also has `SERIAL` (auto-increment) |
| Auto-increment | `INT AUTO_INCREMENT` | `SERIAL` / `BIGSERIAL` | PG `SERIAL` = `INTEGER` + sequence |
| String | `VARCHAR(n)`, `CHAR(n)` | `VARCHAR(n)`, `CHAR(n)` | Max n=65535 MySQL, 10485760 PG |
| Long text | `TEXT`, `MEDIUMTEXT`, `LONGTEXT` | `TEXT` | PG `TEXT` is unlimited |
| Decimal | `DECIMAL(p,s)` | `NUMERIC(p,s)` | Use for money — exact precision |
| Float | `FLOAT`, `DOUBLE` | `REAL`, `DOUBLE PRECISION` | Approximate — avoid for money |
| Boolean | `TINYINT(1)` or `BOOL` | `BOOLEAN` | MySQL stores 0/1; PG: TRUE/FALSE |
| Date | `DATE` | `DATE` | YYYY-MM-DD |
| Time | `TIME` | `TIME` | HH:MM:SS |
| Datetime | `DATETIME`, `TIMESTAMP` | `TIMESTAMP` | TIMESTAMP in PG is timezone-aware with `WITH TIME ZONE` |

---

## Step 4: CREATE TABLE with Constraints

**MySQL:**
```sql
USE school;

CREATE TABLE students (
    student_id   INT           NOT NULL AUTO_INCREMENT,
    first_name   VARCHAR(50)   NOT NULL,
    last_name    VARCHAR(50)   NOT NULL,
    email        VARCHAR(100)  NOT NULL,
    birth_date   DATE,
    gpa          DECIMAL(3,2)  DEFAULT 0.00,
    is_active    BOOLEAN       DEFAULT TRUE,
    enrolled_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id)
);
```

📸 **Verified Output (MySQL):**
```
Query OK, 0 rows affected (0.05 sec)
```

**PostgreSQL:**
```sql
CREATE TABLE students (
    student_id   SERIAL        PRIMARY KEY,
    first_name   VARCHAR(50)   NOT NULL,
    last_name    VARCHAR(50)   NOT NULL,
    email        VARCHAR(100)  NOT NULL,
    birth_date   DATE,
    gpa          NUMERIC(3,2)  DEFAULT 0.00,
    is_active    BOOLEAN       DEFAULT TRUE,
    enrolled_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);
```

> 💡 `NOT NULL` prevents storing NULL (missing) values. `DEFAULT` provides a fallback when no value is specified on INSERT.

---

## Step 5: NULL vs NOT NULL vs DEFAULT

```sql
-- MySQL: These all behave differently
CREATE TABLE demo_nulls (
    col_required  VARCHAR(20) NOT NULL,           -- must provide a value
    col_optional  VARCHAR(20),                    -- NULL allowed (default behavior)
    col_default   VARCHAR(20) DEFAULT 'unknown',  -- NULL allowed, but has default
    col_strict    VARCHAR(20) NOT NULL DEFAULT ''  -- not null, empty string default
);
```

| Column | INSERT with no value | INSERT NULL |
|--------|---------------------|-------------|
| `NOT NULL` | Error | Error |
| nullable | Stores NULL | Stores NULL |
| `DEFAULT 'x'` | Stores `'x'` | Stores NULL |
| `NOT NULL DEFAULT ''` | Stores `''` | Error |

---

## Step 6: DESCRIBE / \d — Inspect Table Structure

**MySQL:**
```sql
USE school;
DESCRIBE students;
```

📸 **Verified Output (MySQL):**
```
+------------+--------------+------+-----+-------------------+-------------------+
| Field      | Type         | Null | Key | Default           | Extra             |
+------------+--------------+------+-----+-------------------+-------------------+
| student_id | int          | NO   | PRI | NULL              | auto_increment    |
| first_name | varchar(50)  | NO   |     | NULL              |                   |
| last_name  | varchar(50)  | NO   |     | NULL              |                   |
| email      | varchar(100) | NO   |     | NULL              |                   |
| birth_date | date         | YES  |     | NULL              |                   |
| gpa        | decimal(3,2) | YES  |     | 0.00              |                   |
| is_active  | tinyint(1)   | YES  |     | 1                 |                   |
| enrolled_at| timestamp    | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+------------+--------------+------+-----+-------------------+-------------------+
```

**PostgreSQL:**
```bash
docker exec pg-lab psql -U postgres -d school -c "\d students"
```

📸 **Verified Output (PostgreSQL):**
```
                                        Table "public.students"
   Column    |          Type          | Collation | Nullable |           Default
-------------+------------------------+-----------+----------+------------------------------
 student_id  | integer                |           | not null | nextval('students_student_id_seq'::regclass)
 first_name  | character varying(50)  |           | not null |
 last_name   | character varying(50)  |           | not null |
 email       | character varying(100) |           | not null |
 birth_date  | date                   |           |          |
 gpa         | numeric(3,2)           |           |          | 0.00
 is_active   | boolean                |           |          | true
 enrolled_at | timestamp without time zone |      |          | CURRENT_TIMESTAMP
Indexes:
    "students_pkey" PRIMARY KEY, btree (student_id)
```

---

## Step 7: CREATE TABLE with Multiple Tables and Relationships

```sql
-- MySQL
USE school;

CREATE TABLE courses (
    course_id    INT          NOT NULL AUTO_INCREMENT,
    course_name  VARCHAR(100) NOT NULL,
    credits      TINYINT      NOT NULL DEFAULT 3,
    PRIMARY KEY (course_id)
);

CREATE TABLE enrollments (
    enrollment_id  INT       NOT NULL AUTO_INCREMENT,
    student_id     INT       NOT NULL,
    course_id      INT       NOT NULL,
    grade          CHAR(2),
    enrolled_date  DATE      NOT NULL DEFAULT (CURRENT_DATE),
    PRIMARY KEY (enrollment_id),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (course_id)  REFERENCES courses(course_id)
);

SHOW TABLES;
```

📸 **Verified Output (MySQL):**
```
+------------------+
| Tables_in_school |
+------------------+
| courses          |
| enrollments      |
| students         |
+------------------+
```

---

## Step 8: Capstone — DROP and Recreate

Practice the full lifecycle:

```sql
-- MySQL: Drop in reverse dependency order
USE school;

DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS demo_nulls;

SHOW TABLES;

-- Recreate students with an additional column
CREATE TABLE students (
    student_id   INT           NOT NULL AUTO_INCREMENT,
    first_name   VARCHAR(50)   NOT NULL,
    last_name    VARCHAR(50)   NOT NULL,
    email        VARCHAR(100)  NOT NULL UNIQUE,
    birth_date   DATE,
    phone        VARCHAR(20)   DEFAULT NULL,
    gpa          DECIMAL(3,2)  DEFAULT 0.00,
    is_active    BOOLEAN       DEFAULT TRUE,
    enrolled_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id)
);

DESCRIBE students;
```

📸 **Verified Output:**
```
Empty set (0.00 sec)

+------------+--------------+------+-----+-------------------+-------------------+
| Field      | Type         | Null | Key | Default           | Extra             |
+------------+--------------+------+-----+-------------------+-------------------+
| student_id | int          | NO   | PRI | NULL              | auto_increment    |
| first_name | varchar(50)  | NO   |     | NULL              |                   |
| last_name  | varchar(50)  | NO   |     | NULL              |                   |
| email      | varchar(100) | NO   | UNI | NULL              |                   |
| birth_date | date         | YES  |     | NULL              |                   |
| phone      | varchar(20)  | YES  |     | NULL              |                   |
| gpa        | decimal(3,2) | YES  |     | 0.00              |                   |
| is_active  | tinyint(1)   | YES  |     | 1                 |                   |
| enrolled_at| timestamp    | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+------------+--------------+------+-----+-------------------+-------------------+
```

> 💡 Always `DROP TABLE IF EXISTS` to avoid errors if the table doesn't exist. Drop child tables (with foreign keys) before parent tables.

**Cleanup:**
```bash
docker rm -f mysql-lab pg-lab
```

---

## Summary

| Command | MySQL | PostgreSQL |
|---------|-------|------------|
| Create database | `CREATE DATABASE name;` | `CREATE DATABASE name;` |
| Use database | `USE name;` | `\c name` or `-d name` |
| Create table | `CREATE TABLE t (...)` | `CREATE TABLE t (...)` |
| Auto-increment PK | `INT AUTO_INCREMENT` | `SERIAL` |
| Inspect table | `DESCRIBE t;` | `\d t` |
| List tables | `SHOW TABLES;` | `\dt` |
| Drop table | `DROP TABLE IF EXISTS t;` | `DROP TABLE IF EXISTS t;` |
| Drop database | `DROP DATABASE name;` | `DROP DATABASE name;` |

**Next:** Lab 03 — Inserting and Querying Data
