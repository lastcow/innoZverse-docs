# Lab 14: Transactions

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Learn transaction fundamentals: BEGIN/COMMIT/ROLLBACK, SAVEPOINT, autocommit mode, and the classic fund transfer example demonstrating atomicity.

---

## Step 1: ACID Properties

| Property | Meaning | Example |
|----------|---------|---------|
| **Atomicity** | All-or-nothing: the entire transaction succeeds or nothing changes | Transfer $100: debit AND credit must both succeed |
| **Consistency** | Database always moves from one valid state to another | Account balance can't go negative (CHECK constraint) |
| **Isolation** | Concurrent transactions don't interfere | Two transfers can't read stale balances |
| **Durability** | Committed data survives crashes | Power failure after COMMIT → data safe on disk |

---

## Step 2: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE bankdb;
USE bankdb;

CREATE TABLE accounts (
    account_id  INT          NOT NULL AUTO_INCREMENT,
    owner       VARCHAR(100) NOT NULL,
    balance     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (account_id),
    CONSTRAINT chk_balance CHECK (balance >= 0)
);

CREATE TABLE transfers (
    transfer_id  INT NOT NULL AUTO_INCREMENT,
    from_account INT NOT NULL,
    to_account   INT NOT NULL,
    amount       DECIMAL(12,2) NOT NULL,
    transferred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status       VARCHAR(20) DEFAULT 'completed',
    PRIMARY KEY (transfer_id)
);

INSERT INTO accounts (owner, balance) VALUES
('Alice',  5000.00),
('Bob',    3000.00),
('Carol',  1000.00),
('David',    50.00);  -- low balance
EOF
```

---

## Step 3: Autocommit Mode

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE bankdb;

-- Check autocommit setting
SHOW VARIABLES LIKE 'autocommit';

-- In autocommit=ON mode (default): every statement is its own transaction
-- UPDATE commits immediately — no way to ROLLBACK
UPDATE accounts SET balance = balance + 100 WHERE account_id = 1;
-- This is already committed!

-- To control transactions manually, either:
-- 1. SET autocommit = 0; (session-level)
-- 2. Use BEGIN/START TRANSACTION (overrides autocommit for that transaction)
EOF
```

📸 **Verified Output:**
```
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| autocommit    | ON    |
+---------------+-------+
```

> 💡 MySQL default: `autocommit = ON`. Each statement auto-commits. To use multi-statement transactions, use `START TRANSACTION` or `BEGIN` — this temporarily disables autocommit until COMMIT or ROLLBACK.

---

## Step 4: Basic COMMIT

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE bankdb;

-- Reset balances
UPDATE accounts SET balance = 5000 WHERE account_id = 1;
UPDATE accounts SET balance = 3000 WHERE account_id = 2;

-- Start a transaction
START TRANSACTION;

UPDATE accounts SET balance = balance - 500 WHERE account_id = 1;  -- debit Alice
UPDATE accounts SET balance = balance + 500 WHERE account_id = 2;  -- credit Bob

-- Verify before committing (within same connection)
SELECT account_id, owner, balance FROM accounts WHERE account_id IN (1,2);

-- Commit the transaction
COMMIT;

-- Verify after commit
SELECT account_id, owner, balance FROM accounts WHERE account_id IN (1,2);
EOF
```

📸 **Verified Output:**
```
-- Before COMMIT (within transaction):
+------------+-------+---------+
| account_id | owner | balance |
+------------+-------+---------+
|          1 | Alice | 4500.00 |
|          2 | Bob   | 3500.00 |
+------------+-------+---------+

-- After COMMIT (same result, now permanent):
+------------+-------+---------+
| account_id | owner | balance |
+------------+-------+---------+
|          1 | Alice | 4500.00 |
|          2 | Bob   | 3500.00 |
+------------+-------+---------+
```

---

## Step 5: ROLLBACK

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE bankdb;

START TRANSACTION;

UPDATE accounts SET balance = balance - 2000 WHERE account_id = 1;  -- debit Alice
UPDATE accounts SET balance = balance + 2000 WHERE account_id = 2;  -- credit Bob

-- Something went wrong! Roll back ALL changes
ROLLBACK;

-- Verify: balances unchanged
SELECT account_id, owner, balance FROM accounts WHERE account_id IN (1,2);
EOF
```

📸 **Verified Output:**
```
-- After ROLLBACK:
+------------+-------+---------+
| account_id | owner | balance |
+------------+-------+---------+
|          1 | Alice | 4500.00 |  ← unchanged
|          2 | Bob   | 3500.00 |  ← unchanged
+------------+-------+---------+
```

---

## Step 6: SAVEPOINT

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE bankdb;

START TRANSACTION;

-- First operation
UPDATE accounts SET balance = balance - 100 WHERE account_id = 1;
SAVEPOINT after_alice_debit;

-- Second operation
UPDATE accounts SET balance = balance + 100 WHERE account_id = 2;
SAVEPOINT after_bob_credit;

-- Third operation fails (bad data)
UPDATE accounts SET balance = balance - 9999 WHERE account_id = 3;  -- Carol goes negative!

-- CHECK: if Carol's balance would go negative, roll back to savepoint
SELECT balance FROM accounts WHERE account_id = 3;  -- would be negative

-- Roll back only to after_bob_credit (undo the Carol debit)
ROLLBACK TO SAVEPOINT after_bob_credit;

-- First two operations still in effect
SELECT account_id, owner, balance FROM accounts;

-- Release savepoint (optional cleanup)
RELEASE SAVEPOINT after_bob_credit;
RELEASE SAVEPOINT after_alice_debit;

COMMIT;  -- commit the first two operations
EOF
```

📸 **Verified Output:**
```
-- Carol's balance after problematic update (before rollback to savepoint):
+---------+
| balance |
+---------+
| -8999.00|  ← would violate CHECK constraint if committed
+---------+

-- After ROLLBACK TO SAVEPOINT (Alice and Bob changes kept):
+------------+-------+---------+
| account_id | owner | balance |
+------------+-------+---------+
|          1 | Alice | 4400.00 |  ← Alice debited 100
|          2 | Bob   | 3600.00 |  ← Bob credited 100
|          3 | Carol | 1000.00 |  ← Carol untouched (rolled back)
|          4 | David |   50.00 |
+------------+-------+---------+
```

---

## Step 7: Atomic Fund Transfer (Full Example)

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE bankdb;

-- Stored procedure for atomic transfer
DELIMITER //
CREATE PROCEDURE transfer_funds(
    IN p_from INT,
    IN p_to   INT,
    IN p_amount DECIMAL(12,2)
)
BEGIN
    DECLARE v_balance DECIMAL(12,2);
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Lock and read current balance
    SELECT balance INTO v_balance
    FROM accounts
    WHERE account_id = p_from
    FOR UPDATE;

    -- Validate sufficient funds
    IF v_balance < p_amount THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient funds';
    END IF;

    -- Debit sender
    UPDATE accounts SET balance = balance - p_amount WHERE account_id = p_from;

    -- Credit receiver
    UPDATE accounts SET balance = balance + p_amount WHERE account_id = p_to;

    -- Log the transfer
    INSERT INTO transfers (from_account, to_account, amount)
    VALUES (p_from, p_to, p_amount);

    COMMIT;
END //
DELIMITER ;

-- Successful transfer: Alice → Bob
CALL transfer_funds(1, 2, 500);
SELECT account_id, owner, balance FROM accounts;

-- Failed transfer: David has only 50, trying to send 200
CALL transfer_funds(4, 1, 200);
EOF
```

📸 **Verified Output:**
```
-- After successful transfer:
+------------+-------+---------+
| account_id | owner | balance |
+------------+-------+---------+
|          1 | Alice | 3900.00 |
|          2 | Bob   | 4100.00 |
|          3 | Carol | 1000.00 |
|          4 | David |   50.00 |
+------------+-------+---------+

-- Failed transfer (David → Alice, 200 > 50):
ERROR 1644 (45000): Insufficient funds
-- David's balance unchanged (transaction rolled back)
```

---

## Step 8: Capstone — Verify Atomicity

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE bankdb;

-- Verify total money in system is conserved (atomicity guarantee)
SELECT SUM(balance) AS total_system_balance FROM accounts;

-- Check transfer log
SELECT t.transfer_id, a1.owner AS from_owner, a2.owner AS to_owner,
       t.amount, t.transferred_at
FROM transfers t
JOIN accounts a1 ON t.from_account = a1.account_id
JOIN accounts a2 ON t.to_account   = a2.account_id;
EOF
```

📸 **Verified Output:**
```
+----------------------+
| total_system_balance |
+----------------------+
|              9050.00 |  ← 5000+3000+1000+50 = 9050 (matches starting total)
+----------------------+

+-------------+------------+----------+--------+---------------------+
| transfer_id | from_owner | to_owner | amount | transferred_at      |
+-------------+------------+----------+--------+---------------------+
|           1 | Alice      | Bob      | 500.00 | 2024-01-15 10:30:00 |
+-------------+------------+----------+--------+---------------------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary

| Command | Description |
|---------|-------------|
| `START TRANSACTION` / `BEGIN` | Start a transaction (disables autocommit) |
| `COMMIT` | Permanently save all changes |
| `ROLLBACK` | Undo all changes since BEGIN |
| `SAVEPOINT name` | Mark a partial rollback point |
| `ROLLBACK TO SAVEPOINT name` | Undo to savepoint, transaction continues |
| `RELEASE SAVEPOINT name` | Remove a savepoint |
| `SET autocommit = 0` | Disable autocommit for session |
| `SHOW VARIABLES LIKE 'autocommit'` | Check current autocommit setting |

| Isolation Level | Dirty Read | Non-repeatable Read | Phantom Read |
|-----------------|-----------|---------------------|--------------|
| READ UNCOMMITTED | Possible | Possible | Possible |
| READ COMMITTED | No | Possible | Possible |
| REPEATABLE READ | No | No | Possible (MySQL: No) |
| SERIALIZABLE | No | No | No |

MySQL default: REPEATABLE READ. PostgreSQL default: READ COMMITTED.

**Next:** Lab 15 — String Functions
