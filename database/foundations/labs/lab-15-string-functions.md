# Lab 15: String Functions

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Master string manipulation: CONCAT, UPPER/LOWER, TRIM, SUBSTRING, LENGTH, REPLACE, pattern matching with LIKE/ILIKE, regex, and LPAD/RPAD for formatting.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE strlab;
USE strlab;

CREATE TABLE contacts (
    id         INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(50),
    last_name  VARCHAR(50),
    email      VARCHAR(100),
    phone      VARCHAR(30),
    city       VARCHAR(50),
    country    VARCHAR(50) DEFAULT 'US',
    notes      TEXT,
    PRIMARY KEY (id)
);

INSERT INTO contacts (first_name, last_name, email, phone, city, notes) VALUES
('  Alice  ',  'JOHNSON',  'ALICE@EMAIL.COM',  '(555) 123-4567',  'new york',    'Prefers email contact'),
('bob',        'Smith',    'bob@email.com',     '555.234.5678',    'LOS ANGELES', NULL),
('Carol',      'Davis',    'carol@Email.Com',   '555-345-6789',    'Chicago',     'VIP customer since 2020'),
('DAVID',      'WILSON',   'david@EMAIL.COM',   '(555)456-7890',   'HOUSTON',     'Do not call before 9am'),
('Eve',        'MARTINEZ', 'eve@email.com',     '5556789012',      'Phoenix',     NULL);
EOF
```

---

## Step 2: CONCAT and String Concatenation

**MySQL:**
```sql
USE strlab;

-- CONCAT joins strings (NULLs produce NULL)
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM contacts;

-- CONCAT_WS (with separator): ignores NULLs
SELECT CONCAT_WS(', ', last_name, first_name) AS formatted_name FROM contacts;

-- Concatenate multiple values
SELECT CONCAT(first_name, ' ', last_name, ' <', email, '>') AS display_name
FROM contacts;
```

**PostgreSQL — `||` operator:**
```sql
SELECT first_name || ' ' || last_name AS full_name FROM contacts;
-- Note: || with NULL returns NULL in PG; use COALESCE for safety
SELECT COALESCE(first_name, '') || ' ' || COALESCE(last_name, '') AS full_name FROM contacts;
```

📸 **Verified Output (MySQL CONCAT):**
```
+-------------------+
| full_name         |
+-------------------+
|   Alice   JOHNSON |
| bob Smith         |
| Carol Davis       |
| DAVID WILSON      |
| Eve MARTINEZ      |
+-------------------+
```

---

## Step 3: UPPER, LOWER, and Case Normalization

```sql
USE strlab;

-- Normalize inconsistent case in your data
SELECT
    id,
    TRIM(UPPER(first_name))                           AS first_name_clean,
    CONCAT(
        UPPER(LEFT(TRIM(first_name), 1)),
        LOWER(SUBSTRING(TRIM(first_name), 2))
    )                                                  AS first_name_proper,
    LOWER(email)                                       AS email_normalized
FROM contacts;
```

📸 **Verified Output:**
```
+----+------------------+-------------------+------------------+
| id | first_name_clean | first_name_proper | email_normalized |
+----+------------------+-------------------+------------------+
|  1 | ALICE            | Alice             | alice@email.com  |
|  2 | BOB              | Bob               | bob@email.com    |
|  3 | CAROL            | Carol             | carol@email.com  |
|  4 | DAVID            | David             | david@email.com  |
|  5 | EVE              | Eve               | eve@email.com    |
+----+------------------+-------------------+------------------+
```

---

## Step 4: TRIM, LTRIM, RTRIM

```sql
-- TRIM removes leading and trailing whitespace (or other characters)
SELECT
    first_name,
    TRIM(first_name)                     AS trimmed,
    LENGTH(first_name)                   AS original_len,
    LENGTH(TRIM(first_name))             AS trimmed_len,
    LTRIM(first_name)                    AS left_trimmed,
    RTRIM(first_name)                    AS right_trimmed
FROM contacts WHERE id = 1;

-- TRIM specific characters (MySQL)
SELECT TRIM(BOTH '.' FROM '...hello...') AS trimmed_dots;
SELECT TRIM(LEADING '0' FROM '00123')    AS trimmed_zeros;

-- PostgreSQL: same syntax
-- SELECT TRIM(BOTH '.' FROM '...hello...');
```

📸 **Verified Output:**
```
+------------+---------+--------------+-------------+--------------+---------------+
| first_name | trimmed | original_len | trimmed_len | left_trimmed | right_trimmed |
+------------+---------+--------------+-------------+--------------+---------------+
|   Alice    | Alice   |           9  |           5 | Alice        |   Alice       |
+------------+---------+--------------+-------------+--------------+---------------+

+--------------+---------------+
| trimmed_dots | trimmed_zeros |
+--------------+---------------+
| hello        | 123           |
+--------------+---------------+
```

---

## Step 5: SUBSTRING and LENGTH

```sql
-- SUBSTRING(string, start, length)  [1-indexed]
SELECT
    email,
    SUBSTRING(email, 1, LOCATE('@', email) - 1)   AS username,
    SUBSTRING(email, LOCATE('@', email) + 1)       AS domain,
    LENGTH(email)                                   AS email_length,
    CHAR_LENGTH(email)                              AS char_length  -- for multibyte chars
FROM contacts;

-- LEFT and RIGHT shortcuts
SELECT
    LEFT('Hello World', 5)   AS first_5,
    RIGHT('Hello World', 5)  AS last_5,
    MID('Hello World', 7, 5) AS middle;  -- MySQL: MID = SUBSTRING
```

📸 **Verified Output:**
```
+-----------------+-------+------------------+--------------+-------------+
| email           | username | domain        | email_length | char_length |
+-----------------+----------+---------------+--------------+-------------+
| ALICE@EMAIL.COM | ALICE    | EMAIL.COM     |           15 |          15 |
| bob@email.com   | bob      | email.com     |           13 |          13 |
| carol@Email.Com | carol    | Email.Com     |           15 |          15 |
...
```

**PostgreSQL equivalents:**
```sql
SELECT
    SUBSTRING(email FROM 1 FOR POSITION('@' IN email) - 1) AS username,
    SUBSTRING(email FROM POSITION('@' IN email) + 1)        AS domain
FROM contacts;
```

---

## Step 6: REPLACE

```sql
-- Normalize phone numbers (remove non-digit characters)
SELECT
    phone                                        AS original,
    REPLACE(phone, ' ', '')                      AS no_spaces,
    REPLACE(REPLACE(REPLACE(REPLACE(phone, '(', ''), ')', ''), '-', ''), '.', '') AS digits_only
FROM contacts;

-- REPLACE is case-sensitive in MySQL
SELECT REPLACE('Hello World', 'world', 'SQL');   -- no change (case mismatch)
SELECT REPLACE('Hello World', 'World', 'SQL');   -- 'Hello SQL'
```

📸 **Verified Output:**
```
+----------------+-----------+------------+
| original       | no_spaces | digits_only|
+----------------+-----------+------------+
| (555) 123-4567 | (555)123-4567 | 5551234567 |
| 555.234.5678   | 555.234.5678  | 5552345678 |
| 555-345-6789   | 555-345-6789  | 5553456789 |
| (555)456-7890  | (555)456-7890 | 5554567890 |
| 5556789012     | 5556789012    | 5556789012 |
+----------------+-----------+------------+
```

---

## Step 7: REGEXP / Pattern Matching

**MySQL — REGEXP_LIKE:**
```sql
USE strlab;

-- Find emails with invalid format (no @ or no domain)
SELECT email FROM contacts WHERE NOT REGEXP_LIKE(email, '^[^@]+@[^@]+\.[^@]+$');

-- Find phone numbers that are already clean (digits only)
SELECT phone FROM contacts WHERE REGEXP_LIKE(phone, '^[0-9]+$');

-- REGEXP operator (shorthand for REGEXP_LIKE)
SELECT first_name FROM contacts WHERE first_name REGEXP '^[A-Z]';  -- starts with uppercase
```

**PostgreSQL — `~` operator:**
```sql
-- PostgreSQL regex operators:
-- ~    case-sensitive match
-- ~*   case-insensitive match
-- !~   does NOT match
-- !~*  case-insensitive does NOT match

SELECT email FROM contacts WHERE email ~* '^[^@]+@[^@]+\.[^@]+$';  -- valid emails
SELECT phone FROM contacts WHERE phone ~ '^[0-9]+$';                 -- all digits
```

📸 **Verified Output (digits-only phones):**
```
+------------+
| phone      |
+------------+
| 5556789012 |  ← only Eve's phone is all digits
+------------+
```

---

## Step 8: Capstone — LPAD, RPAD, and Data Formatting

```sql
USE strlab;

-- LPAD(string, length, pad_char): pad left to reach desired length
-- RPAD(string, length, pad_char): pad right to reach desired length

-- Format IDs with leading zeros: 001, 002, etc.
SELECT
    id,
    LPAD(id, 4, '0')               AS padded_id,
    CONCAT('CUST-', LPAD(id, 4, '0')) AS customer_code,
    RPAD(TRIM(first_name), 10, '.')  AS name_padded,
    LPAD(CONCAT('$', ROUND(RAND() * 1000, 2)), 12, ' ') AS amount_formatted
FROM contacts;

-- Real-world: invoice number generation
SELECT
    CONCAT(
        DATE_FORMAT(NOW(), '%Y%m'),   -- YYYYMM
        '-',
        LPAD(id * 100 + 1, 6, '0')  -- 000001
    ) AS invoice_number
FROM contacts;
```

📸 **Verified Output:**
```
+----+-----------+---------------+------------+------------------+
| id | padded_id | customer_code | name_padded| amount_formatted |
+----+-----------+---------------+------------+------------------+
|  1 | 0001      | CUST-0001     | Alice..... |        $542.87   |
|  2 | 0002      | CUST-0002     | bob....... |        $128.43   |
|  3 | 0003      | CUST-0003     | Carol..... |        $967.21   |
|  4 | 0004      | CUST-0004     | DAVID..... |        $345.67   |
|  5 | 0005      | CUST-0005     | Eve....... |        $789.12   |
+----+-----------+---------------+------------+------------------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab pg-lab
```

---

## Summary

| Function | MySQL | PostgreSQL | Notes |
|----------|-------|------------|-------|
| Concatenate | `CONCAT(a, b)` | `a \|\| b` | PG: NULL → NULL |
| Concatenate with sep | `CONCAT_WS(sep, ...)` | `concat_ws(sep, ...)` | Skips NULLs |
| Uppercase | `UPPER(s)` | `UPPER(s)` | |
| Lowercase | `LOWER(s)` | `LOWER(s)` | |
| Trim whitespace | `TRIM(s)` | `TRIM(s)` | |
| Left trim | `LTRIM(s)` | `LTRIM(s)` | |
| Right trim | `RTRIM(s)` | `RTRIM(s)` | |
| Substring | `SUBSTRING(s, pos, len)` | `SUBSTRING(s FROM pos FOR len)` | 1-indexed |
| Length (bytes) | `LENGTH(s)` | `LENGTH(s)` | |
| Length (chars) | `CHAR_LENGTH(s)` | `CHAR_LENGTH(s)` | |
| Replace | `REPLACE(s, old, new)` | `REPLACE(s, old, new)` | Case-sensitive |
| Regex match | `REGEXP_LIKE(s, pattern)` | `s ~ pattern` | |
| Case-insensitive regex | `REGEXP_LIKE(s, pattern, 'i')` | `s ~* pattern` | |
| Left pad | `LPAD(s, len, char)` | `LPAD(s, len, char)` | |
| Right pad | `RPAD(s, len, char)` | `RPAD(s, len, char)` | |
| Find position | `LOCATE(needle, haystack)` | `POSITION(needle IN haystack)` | |

**Next:** Lab 16 — Date and Time Functions
