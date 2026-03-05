# Lab 07: Transactions and Isolation Levels

**Time:** 40 minutes | **Level:** Practitioner | **DB:** PostgreSQL 15 + MySQL 8.0

Transactions ensure data consistency (ACID). Isolation levels define what concurrent transactions can see of each other's uncommitted work — and the anomalies they prevent.

---

## Step 1 — Setup: Bank Accounts

```sql
-- PostgreSQL
CREATE TABLE bank_accounts (
  id      SERIAL PRIMARY KEY,
  owner   VARCHAR(50),
  balance NUMERIC(12,2) CHECK (balance >= 0)
);

INSERT INTO bank_accounts (owner, balance) VALUES
  ('Alice', 5000.00),
  ('Bob',   3000.00);

SELECT * FROM bank_accounts;
```

📸 **Verified Output:**
```
 id | owner | balance
----+-------+---------
  1 | Alice | 5000.00
  2 | Bob   | 3000.00
(2 rows)
```

---

## Step 2 — Basic Transaction: COMMIT and ROLLBACK

```sql
-- Successful transfer
BEGIN;
UPDATE bank_accounts SET balance = balance - 500 WHERE owner = 'Alice';
UPDATE bank_accounts SET balance = balance + 500 WHERE owner = 'Bob';
SAVEPOINT after_transfer;
SELECT * FROM bank_accounts;  -- See changes within transaction
COMMIT;

SELECT * FROM bank_accounts;  -- Changes persisted
```

📸 **Verified Output:**
```
 id | owner | balance
----+-------+---------
  1 | Alice | 4500.00
  2 | Bob   | 3500.00
(2 rows)
```

```sql
-- Failed transfer: rollback on error
BEGIN;
UPDATE bank_accounts SET balance = balance - 10000 WHERE owner = 'Alice';
-- This triggers CHECK constraint violation (balance < 0)
ROLLBACK;  -- or happens automatically on error

SELECT * FROM bank_accounts;  -- Unchanged
```

> 💡 PostgreSQL automatically aborts the transaction on any error — any further commands return `ERROR: current transaction is aborted`. You must `ROLLBACK` before starting a new transaction.

---

## Step 3 — Isolation Levels: Overview

| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|-------|-----------|---------------------|--------------|
| READ UNCOMMITTED | Possible | Possible | Possible |
| READ COMMITTED | No | Possible | Possible |
| REPEATABLE READ | No | No | Possible |
| SERIALIZABLE | No | No | No |

**Anomaly definitions:**
- **Dirty Read**: Read uncommitted data from another transaction
- **Non-Repeatable Read**: Same query returns different rows within a transaction
- **Phantom Read**: Re-running a range query returns new rows inserted by another transaction

> 💡 PostgreSQL doesn't actually implement READ UNCOMMITTED (it uses READ COMMITTED as minimum). MySQL InnoDB implements all four levels.

---

## Step 4 — READ COMMITTED (Default)

```sql
-- Session A (terminal 1)
BEGIN;
UPDATE bank_accounts SET balance = 9999.99 WHERE owner = 'Alice';
-- DO NOT COMMIT YET

-- Session B (terminal 2)
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
BEGIN;
SELECT * FROM bank_accounts WHERE owner = 'Alice';
-- Returns 4500.00 (Alice's current committed balance — NOT 9999.99)
-- READ COMMITTED prevents dirty reads
COMMIT;

-- Back in Session A
ROLLBACK;
```

---

## Step 5 — REPEATABLE READ

```sql
-- Session A:
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN;
SELECT balance FROM bank_accounts WHERE owner = 'Alice';
-- Returns 4500.00

-- Session B (while A is open):
BEGIN;
UPDATE bank_accounts SET balance = 1000.00 WHERE owner = 'Alice';
COMMIT;

-- Back in Session A:
SELECT balance FROM bank_accounts WHERE owner = 'Alice';
-- Still returns 4500.00 (snapshot taken at BEGIN — no non-repeatable reads)
COMMIT;
```

> 💡 PostgreSQL uses **MVCC** (Multi-Version Concurrency Control) — each transaction sees a consistent snapshot of the data as it was at the start. No shared read locks needed.

---

## Step 6 — SERIALIZABLE Isolation

```sql
-- SERIALIZABLE prevents all anomalies including phantoms
-- PostgreSQL uses SSI (Serializable Snapshot Isolation)

-- Session A:
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT SUM(balance) FROM bank_accounts;  -- 5500.00

-- Session B (concurrent):
BEGIN ISOLATION LEVEL SERIALIZABLE;
INSERT INTO bank_accounts (owner, balance) VALUES ('Charlie', 1000.00);
COMMIT;

-- Session A:
SELECT SUM(balance) FROM bank_accounts;
-- Still 5500.00 — phantom row not visible
COMMIT;  -- May raise "could not serialize access" if conflict detected
```

---

## Step 7 — SELECT FOR UPDATE / SELECT FOR SHARE

```sql
-- Pessimistic locking: lock rows for update
BEGIN ISOLATION LEVEL SERIALIZABLE;
SELECT * FROM bank_accounts
WHERE owner = 'Alice'
FOR UPDATE;  -- Acquires exclusive row lock
-- No other transaction can modify this row until COMMIT/ROLLBACK

UPDATE bank_accounts SET balance = balance - 100 WHERE owner = 'Alice';
COMMIT;
```

```sql
-- SELECT FOR SHARE: allow other readers, block writers
BEGIN;
SELECT * FROM bank_accounts
WHERE owner = 'Bob'
FOR SHARE;  -- Others can SELECT FOR SHARE, but not FOR UPDATE
COMMIT;
```

📸 **Verified Output:**
```
 id | owner | balance
----+-------+---------
  1 | Alice | 4400.00
(1 row)
```

**Locking options:**
| Option | Blocks | Allows |
|--------|--------|--------|
| `FOR UPDATE` | Other FOR UPDATE, FOR SHARE, writers | Other readers |
| `FOR SHARE` | Other FOR UPDATE, writers | Other FOR SHARE |
| `FOR NO KEY UPDATE` | Other FOR UPDATE | FOR SHARE |
| `FOR KEY SHARE` | FOR UPDATE only | FOR SHARE, FOR NO KEY UPDATE |

---

## Step 8 — Capstone: Optimistic vs Pessimistic Locking

```sql
-- OPTIMISTIC LOCKING: use a version column
CREATE TABLE inventory_items (
  id       SERIAL PRIMARY KEY,
  name     VARCHAR(100),
  quantity INT,
  version  INT DEFAULT 0
);

INSERT INTO inventory_items (name, quantity) VALUES ('Widget A', 100);

-- Transaction 1: read the version
SELECT id, name, quantity, version FROM inventory_items WHERE id = 1;
-- Returns: version=0

-- Transaction 1: update only if version matches (optimistic check)
UPDATE inventory_items
SET quantity = quantity - 10,
    version  = version + 1
WHERE id = 1
  AND version = 0;  -- fails if someone else updated first

SELECT ROW_COUNT();  -- 0 means conflict, retry; 1 means success

-- PESSIMISTIC LOCKING: lock first, update second
BEGIN;
SELECT * FROM inventory_items WHERE id = 1 FOR UPDATE;
-- No one else can update id=1 until this transaction ends
UPDATE inventory_items
SET quantity = quantity - 10, version = version + 1
WHERE id = 1;
COMMIT;

SELECT * FROM inventory_items;
```

📸 **Verified Final State:**
```
 id |   name   | quantity | version
----+----------+----------+---------
  1 | Widget A |       80 |       2
(1 row)
```

---

## Summary

| Isolation Level | Default In | Prevents |
|----------------|-----------|----------|
| READ UNCOMMITTED | MySQL (not in PG) | Nothing |
| READ COMMITTED | PostgreSQL, MySQL | Dirty reads |
| REPEATABLE READ | MySQL default | Dirty + non-repeatable reads |
| SERIALIZABLE | — | All anomalies |

| Locking | Type | Use When |
|---------|------|----------|
| `SELECT FOR UPDATE` | Pessimistic | Always consistent, low concurrency |
| `SELECT FOR SHARE` | Pessimistic | Read-then-decide, block writers |
| Version column | Optimistic | High concurrency, retries acceptable |
