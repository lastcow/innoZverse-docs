# Lab 08: Deadlocks — Detection and Prevention

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MySQL 8.0 + PostgreSQL 15

A deadlock occurs when two transactions each hold a lock the other needs, creating a circular wait. Both databases detect and resolve deadlocks automatically — but understanding them lets you prevent them.

---

## Step 1 — How Deadlocks Occur

```
Transaction A                    Transaction B
─────────────────────────────    ─────────────────────────────
LOCK row 1 (success)             LOCK row 2 (success)
LOCK row 2 → WAITING             LOCK row 1 → WAITING
             ↑                                ↑
             └──────── DEADLOCK ──────────────┘
```

The database's deadlock detector finds the cycle and aborts the transaction with lower cost (or younger start time).

---

## Step 2 — MySQL Deadlock Settings

```sql
-- Check deadlock detection (default: ON)
SELECT @@innodb_deadlock_detect;
-- 1 = ON (immediate detection)

-- Lock wait timeout
SELECT @@innodb_lock_wait_timeout;
-- 50 seconds default

-- In high-throughput systems, you might set:
SET GLOBAL innodb_lock_wait_timeout = 5;

-- View recent deadlock
SHOW ENGINE INNODB STATUS\G
-- Look for: LATEST DETECTED DEADLOCK section
```

📸 **Verified Output:**
```
@@innodb_deadlock_detect  @@innodb_lock_wait_timeout
1                         50
```

---

## Step 3 — Intentional Deadlock Demo (MySQL)

Run these in two simultaneous MySQL sessions:

```sql
-- Setup
USE labdb;
CREATE TABLE IF NOT EXISTS accounts (
  id      INT PRIMARY KEY,
  name    VARCHAR(50),
  balance DECIMAL(12,2)
);
INSERT INTO accounts VALUES (1,'Alice',1000), (2,'Bob',2000)
  ON DUPLICATE KEY UPDATE name=name;

-- SESSION A: run first
START TRANSACTION;
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;  -- Lock row 1
-- (pause here — wait for Session B to lock row 2)
SELECT * FROM accounts WHERE id = 2 FOR UPDATE;  -- Will DEADLOCK

-- SESSION B: run after Session A has row 1 locked
START TRANSACTION;
SELECT * FROM accounts WHERE id = 2 FOR UPDATE;  -- Lock row 2
SELECT * FROM accounts WHERE id = 1 FOR UPDATE;  -- Causes DEADLOCK
-- One of these will fail with:
-- ERROR 1213: Deadlock found when trying to get lock; try restarting transaction
```

> 💡 When MySQL detects a deadlock, it rolls back the **smaller** transaction (fewer undo log records). Your application should catch error 1213 and retry.

---

## Step 4 — MySQL: Reading INNODB STATUS

```sql
SHOW ENGINE INNODB STATUS\G
```

The **LATEST DETECTED DEADLOCK** section shows:
```
LATEST DETECTED DEADLOCK
------------------------
*** (1) TRANSACTION:
TRANSACTION 421, ACTIVE 5 sec starting index read
...
LOCK WAIT 2 lock struct(s), heap size 1136, 1 row lock(s)
LOCK BLOCKING MySQL thread id: 12 ...

*** (2) TRANSACTION:
TRANSACTION 422, ACTIVE 3 sec starting index read
...

*** WE ROLL BACK TRANSACTION (2)
```

```sql
-- Track lock waits in real time
SELECT
  r.trx_id waiting_trx_id,
  r.trx_mysql_thread_id waiting_thread,
  r.trx_query waiting_query,
  b.trx_id blocking_trx_id,
  b.trx_mysql_thread_id blocking_thread
FROM information_schema.innodb_lock_waits w
JOIN information_schema.innodb_trx b ON b.trx_id = w.blocking_trx_id
JOIN information_schema.innodb_trx r ON r.trx_id = w.requesting_trx_id;
```

---

## Step 5 — PostgreSQL: Detecting Locks

```sql
-- Current lock holders and waiters
SELECT pid, wait_event_type, wait_event, state, query
FROM pg_stat_activity
WHERE state != 'idle'
  AND pid != pg_backend_pid();

-- Detailed lock view
SELECT
  locktype,
  relation::regclass AS table_name,
  mode,
  granted,
  pid
FROM pg_locks
WHERE relation IS NOT NULL;
```

📸 **Verified Output:**
```
 locktype | table_name |      mode       | granted | pid
----------+------------+-----------------+---------+------
 relation | pg_locks   | AccessShareLock | t       | 1234
```

```sql
-- Find who is blocking whom
SELECT
  blocked.pid     AS blocked_pid,
  blocked.query   AS blocked_query,
  blocker.pid     AS blocker_pid,
  blocker.query   AS blocker_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocker
  ON blocker.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE cardinality(pg_blocking_pids(blocked.pid)) > 0;
```

---

## Step 6 — PostgreSQL: Deadlock Demo

```sql
-- Setup
CREATE TABLE IF NOT EXISTS pgaccounts (
  id      INT PRIMARY KEY,
  name    VARCHAR(50),
  balance NUMERIC(12,2)
);
INSERT INTO pgaccounts VALUES (1,'Alice',1000),(2,'Bob',2000)
  ON CONFLICT DO NOTHING;
```

Run in **two separate psql sessions simultaneously**:

```sql
-- SESSION A:
BEGIN;
UPDATE pgaccounts SET balance = balance - 100 WHERE id = 1;  -- Lock id=1
-- Wait...
UPDATE pgaccounts SET balance = balance + 100 WHERE id = 2;  -- Deadlock

-- SESSION B:
BEGIN;
UPDATE pgaccounts SET balance = balance - 100 WHERE id = 2;  -- Lock id=2
-- Wait...
UPDATE pgaccounts SET balance = balance + 100 WHERE id = 1;  -- Deadlock
```

One session receives:
```
ERROR:  deadlock detected
DETAIL:  Process 1234 waits for ShareLock on transaction 567;
         blocked by process 5678.
         Process 5678 waits for ShareLock on transaction 568;
         blocked by process 1234.
HINT:  See server log for query details.
```

> 💡 PostgreSQL `deadlock_timeout` (default 1s) is how long to wait before checking for deadlocks. Lower it for fast-fail; raise it to reduce overhead.

---

## Step 7 — Deadlock Prevention Strategies

### Strategy 1: Lock Ordering Convention
Always acquire locks in a consistent order (e.g., always lock by ID ascending):

```sql
-- BAD: inconsistent order causes deadlocks
-- Tx A: lock 1, then lock 2
-- Tx B: lock 2, then lock 1

-- GOOD: always lock in ascending ID order
BEGIN;
-- Sort IDs first in application code, then lock in order
SELECT * FROM pgaccounts WHERE id IN (1, 2) ORDER BY id FOR UPDATE;
-- This executes as: lock id=1, then lock id=2 — same order for everyone
UPDATE pgaccounts SET balance = balance - 100 WHERE id = 1;
UPDATE pgaccounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

### Strategy 2: Minimize Transaction Duration

```sql
-- BAD: long transaction holds locks
BEGIN;
SELECT * FROM pgaccounts FOR UPDATE;
-- ... application does slow computation ...
UPDATE pgaccounts SET ...;
COMMIT;  -- locks held for minutes

-- GOOD: compute first, lock last
-- Do computation outside transaction
BEGIN;
UPDATE pgaccounts SET balance = computed_value WHERE id = 1;
COMMIT;  -- locks held for milliseconds
```

### Strategy 3: Use Advisory Locks

```sql
-- Application-level lock, no table lock needed
SELECT pg_try_advisory_lock(12345);  -- returns true if acquired
-- ... critical section ...
SELECT pg_advisory_unlock(12345);
```

---

## Step 8 — Capstone: Transfer Function with Deadlock Prevention

```sql
CREATE OR REPLACE FUNCTION safe_transfer_ordered(
  p_from_id INT,
  p_to_id   INT,
  p_amount  NUMERIC
)
RETURNS TEXT LANGUAGE plpgsql AS $$
DECLARE
  v_first_id  INT := LEAST(p_from_id, p_to_id);
  v_second_id INT := GREATEST(p_from_id, p_to_id);
BEGIN
  -- Always lock in ascending ID order — prevents deadlocks
  PERFORM * FROM pgaccounts WHERE id = v_first_id  FOR UPDATE;
  PERFORM * FROM pgaccounts WHERE id = v_second_id FOR UPDATE;

  UPDATE pgaccounts SET balance = balance - p_amount WHERE id = p_from_id;
  UPDATE pgaccounts SET balance = balance + p_amount WHERE id = p_to_id;

  RETURN FORMAT('Transferred %s from %s to %s', p_amount, p_from_id, p_to_id);
EXCEPTION
  WHEN serialization_failure OR deadlock_detected THEN
    RAISE NOTICE 'Deadlock or serialization failure — caller should retry';
    RETURN 'RETRY';
END;
$$;

SELECT safe_transfer_ordered(1, 2, 250.00);
SELECT * FROM pgaccounts;
```

---

## Summary

| Topic | MySQL | PostgreSQL |
|-------|-------|-----------|
| Deadlock detection | Automatic, immediate | After `deadlock_timeout` (1s) |
| Victim choice | Smaller transaction | Youngest/cheapest |
| View deadlock | `SHOW ENGINE INNODB STATUS` | Server log + `pg_stat_activity` |
| Error code | 1213 | `deadlock_detected` |
| Lock timeout | `innodb_lock_wait_timeout` | `lock_timeout` GUC |
| Prevention | Lock ordering, short Tx | Lock ordering, advisory locks |
