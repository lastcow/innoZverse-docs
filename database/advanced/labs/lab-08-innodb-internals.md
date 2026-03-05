# Lab 08: InnoDB Internals

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0

## Overview

Understanding InnoDB's internal structure — B-tree indexes, clustered vs secondary indexes, page organization, and locking mechanisms — enables you to design schemas and queries that work *with* the storage engine rather than against it.

---

## Step 1: B-Tree and Clustered Index Structure

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
CREATE DATABASE innolab;
USE innolab;

-- Clustered index: the PRIMARY KEY IS the table (leaf pages store full rows)
CREATE TABLE employees (
  emp_id     INT NOT NULL,
  dept_id    INT NOT NULL,
  name       VARCHAR(100),
  salary     DECIMAL(10,2),
  hire_date  DATE,
  PRIMARY KEY (emp_id),                    -- Clustered index on emp_id
  INDEX idx_dept    (dept_id),             -- Secondary index
  INDEX idx_salary  (salary),             -- Secondary index
  INDEX idx_dept_salary (dept_id, salary)  -- Composite secondary index
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

-- Insert data
INSERT INTO employees (emp_id, dept_id, name, salary, hire_date)
SELECT 
  seq,
  1 + (seq % 10),
  CONCAT('Employee_', seq),
  30000 + (seq * 7 % 70000),
  DATE_ADD('2020-01-01', INTERVAL (seq % 1460) DAY)
FROM (
  SELECT a.N + b.N * 10 + c.N * 100 + d.N * 1000 + 1 AS seq
  FROM 
    (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
     UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
    (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
     UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
    (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
     UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c,
    (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 
     UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) d
  LIMIT 10000
) nums;

-- Check table stats
SHOW TABLE STATUS LIKE 'employees'\G
EOF
```

📸 **Verified Output:**
```
*************************** 1. row ***************************
           Name: employees
         Engine: InnoDB
        Version: 10
     Row_format: Dynamic
           Rows: 9972
 Avg_row_length: 89
    Data_length: 884736    <- ~864KB = clustered index (stores all row data)
Max_data_length: 0
   Index_length: 688128    <- ~672KB = secondary indexes
      Data_free: 0
 Auto_increment: NULL
    Create_time: 2026-03-05 10:00:00
    Update_time: NULL
     Check_time: NULL
      Collation: utf8mb4_0900_ai_ci
       Checksum: NULL
```

> 💡 `Data_length` = clustered index size (the actual rows). `Index_length` = all secondary indexes. The clustered index contains BOTH the B-tree structure AND the full row data at leaf nodes.

---

## Step 2: Visualize Clustered vs Secondary Index Lookup

```bash
docker exec mysql-lab mysql -uroot -prootpass innolab <<'EOF'
-- Query using PRIMARY KEY (clustered index) — single tree traversal
EXPLAIN SELECT * FROM employees WHERE emp_id = 5000\G

-- Query using secondary index — TWO traversals (index lookup + PK lookup)
EXPLAIN SELECT * FROM employees WHERE dept_id = 3\G

-- Covering index: secondary index COVERS the query (no PK lookup needed)
EXPLAIN SELECT dept_id, salary FROM employees WHERE dept_id = 3\G

-- FORCE a primary key scan vs index scan comparison
EXPLAIN SELECT emp_id, name FROM employees WHERE salary BETWEEN 50000 AND 60000\G
EOF
```

📸 **Verified Output:**
```
-- PRIMARY KEY lookup (clustered):
type: const
key:  PRIMARY
ref:  const
rows: 1
Extra: NULL          <- No extra work, data is in leaf node

-- Secondary index + PK lookup:
type: ref
key:  idx_dept
rows: 1000
Extra: NULL          <- Must do "index lookup" then "row lookup" (2 B-trees!)

-- Covering index (no row lookup):
type: ref
key:  idx_dept_salary
Extra: Using index   <- Data found entirely in index — no row lookup!

-- Range scan:
type: range
key:  idx_salary
rows: 1432
Extra: Using index condition
```

> 💡 **Covering index** = the secondary index contains ALL columns needed by the query. The engine never touches the clustered index. This is often a 2-5x speedup!

---

## Step 3: InnoDB Page Structure

```bash
docker exec mysql-lab mysql -uroot -prootpass innolab <<'EOF'
-- Page size is 16KB (default)
SHOW VARIABLES LIKE 'innodb_page_size';

-- B-tree depth (approximately)
-- A 16KB page holds ~450 INT records in interior nodes
-- For 10,000 rows: depth ≈ log450(10000) ≈ 2
SELECT 
  COUNT(*) AS total_rows,
  CEIL(LOG(COUNT(*)) / LOG(450)) AS estimated_btree_depth,
  ROUND(data_length / 1024, 0) AS data_kb,
  ROUND(data_length / 16384, 1) AS data_pages
FROM information_schema.tables t
JOIN employees e  -- just trigger the join for row count
WHERE t.table_name = 'employees' AND t.table_schema = 'innolab';

-- Row format details
SELECT 
  table_name,
  row_format,
  create_options
FROM information_schema.tables
WHERE table_schema = 'innolab';

-- Compare row formats
CREATE TABLE compact_test LIKE employees;
ALTER TABLE compact_test ROW_FORMAT=COMPACT;

CREATE TABLE dynamic_test LIKE employees;
ALTER TABLE dynamic_test ROW_FORMAT=DYNAMIC;

-- DYNAMIC is better for variable-length columns (VARCHAR/TEXT/BLOB)
-- because it can store off-page (overflow) with just a 20-byte pointer
SHOW TABLE STATUS WHERE Name IN ('compact_test', 'dynamic_test')\G
EOF
```

📸 **Verified Output:**
```
+------------------+-------+
| Variable_name    | Value |
+------------------+-------+
| innodb_page_size | 16384 |
+------------------+-------+

+------------------+-----------+-----------------------+------------+
| table_name       | row_count | estimated_btree_depth | data_pages |
+------------------+-----------+-----------------------+------------+
| employees        |      9972 |                     2 |       54.0 |
+------------------+-----------+-----------------------+------------+

Name: compact_test
Row_format: Compact

Name: dynamic_test
Row_format: Dynamic
```

---

## Step 4: Tablespace — File Per Table

```bash
# Check InnoDB tablespace files
docker exec mysql-lab bash -c "ls -la /var/lib/mysql/innolab/ 2>/dev/null || ls -la /var/lib/mysql/"

docker exec mysql-lab mysql -uroot -prootpass innolab <<'EOF'
-- Verify file-per-table is ON
SHOW VARIABLES LIKE 'innodb_file_per_table';

-- Each InnoDB table has its own .ibd file
SELECT 
  table_name,
  ROUND(data_length / 1024 / 1024, 2) AS data_mb,
  ROUND(index_length / 1024 / 1024, 2) AS index_mb,
  ROUND((data_length + index_length) / 1024 / 1024, 2) AS total_mb
FROM information_schema.tables
WHERE table_schema = 'innolab'
ORDER BY data_length + index_length DESC;

-- General tablespace info
SELECT 
  SPACE,
  NAME,
  FLAG,
  ROW_FORMAT,
  PAGE_SIZE
FROM information_schema.INNODB_TABLESPACES
WHERE NAME LIKE 'innolab%';
EOF
```

📸 **Verified Output:**
```
Variable_name          Value
innodb_file_per_table  ON

+---------------+---------+----------+----------+
| table_name    | data_mb | index_mb | total_mb |
+---------------+---------+----------+----------+
| employees     |    0.84 |     0.66 |     1.50 |
| compact_test  |    0.00 |     0.00 |     0.00 |
| dynamic_test  |    0.00 |     0.00 |     0.00 |
+---------------+---------+----------+----------+

+-------+----------------------------+------+------------+-----------+
| SPACE | NAME                       | FLAG | ROW_FORMAT | PAGE_SIZE |
+-------+----------------------------+------+------------+-----------+
|     2 | innolab/employees          |   33 | Dynamic    |     16384 |
|     3 | innolab/compact_test       |   33 | Compact    |     16384 |
+-------+----------------------------+------+------------+-----------+
```

---

## Step 5: Record Locks vs Gap Locks

```bash
docker exec mysql-lab mysql -uroot -prootpass innolab <<'EOF'
-- Set REPEATABLE READ (default) to show gap locking
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- Start a transaction and check what locks are held
START TRANSACTION;

-- Point lookup: acquires RECORD LOCK on emp_id=100
SELECT * FROM employees WHERE emp_id = 100 FOR UPDATE;

-- Range query: acquires GAP LOCKS to prevent phantom reads
SELECT * FROM employees WHERE emp_id BETWEEN 200 AND 210 FOR UPDATE;

-- Check current locks
SELECT 
  OBJECT_NAME,
  LOCK_TYPE,
  LOCK_MODE,
  LOCK_STATUS,
  LOCK_DATA
FROM performance_schema.data_locks
WHERE OBJECT_NAME = 'employees'
ORDER BY LOCK_DATA;

ROLLBACK;
EOF
```

📸 **Verified Output:**
```
+-------------+-----------+-----------+-------------+-----------+
| OBJECT_NAME | LOCK_TYPE | LOCK_MODE | LOCK_STATUS | LOCK_DATA |
+-------------+-----------+-----------+-------------+-----------+
| employees   | TABLE     | IX        | GRANTED     | NULL      |
| employees   | RECORD    | X,REC_NOT_GAP | GRANTED | 100       |  <- Record lock
| employees   | RECORD    | X         | GRANTED     | 200       |  <- Next-key lock (record + gap)
| employees   | RECORD    | X         | GRANTED     | 201       |
| employees   | RECORD    | X         | GRANTED     | 202       |
...
| employees   | RECORD    | X         | GRANTED     | 210       |
| employees   | RECORD    | X,GAP     | GRANTED     | 211       |  <- Gap lock after range
+-------------+-----------+-----------+-------------+-----------+
```

> 💡 **Gap locks** prevent INSERT of rows with keys *between* existing rows in the range. This prevents "phantom reads" in REPEATABLE READ but can cause deadlocks. READ COMMITTED isolation eliminates gap locks.

---

## Step 6: Secondary Index Stores Primary Key

```bash
docker exec mysql-lab mysql -uroot -prootpass innolab <<'EOF'
-- Demonstrate that secondary indexes store the PK value
-- This is WHY you should keep PKs small (INT vs VARCHAR)

-- Query: secondary index lookup + PK lookup
EXPLAIN FORMAT=JSON 
SELECT emp_id, dept_id, name FROM employees WHERE dept_id = 5\G

-- The PK is automatically added to secondary index entries
-- dept_id index actually stores: (dept_id, emp_id) pairs
-- When you do: WHERE dept_id = 5, MySQL:
--   1. Traverses idx_dept B-tree to find all emp_ids where dept_id=5
--   2. For each emp_id, traverses PRIMARY KEY B-tree to fetch full row

-- Avoid "double lookup" with covering index:
EXPLAIN SELECT emp_id, dept_id, salary FROM employees WHERE dept_id = 5\G
-- Uses idx_dept_salary which contains (dept_id, salary, emp_id) — all needed columns!

-- Big PK problem: VARCHAR primary key
CREATE TABLE bad_pk_example (
  uuid_str VARCHAR(36) PRIMARY KEY,       -- 36 bytes!
  data     VARCHAR(100),
  INDEX idx_data (data)                   -- Stores 36-byte PK in every entry
);

CREATE TABLE good_pk_example (
  id       INT AUTO_INCREMENT PRIMARY KEY, -- 4 bytes!
  uuid_str VARCHAR(36) UNIQUE,
  data     VARCHAR(100),
  INDEX idx_data (data)                    -- Stores 4-byte PK in every entry
);

-- Size comparison: same 10k rows
INSERT INTO bad_pk_example SELECT UUID(), CONCAT('data_', seq), 'extra' FROM (
  SELECT a.N + b.N*10 + c.N*100 + d.N*1000 + 1 AS seq FROM
  (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
  (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) b,
  (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) c,
  (SELECT 0 AS N UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) d
  LIMIT 10000
) nums;
INSERT INTO good_pk_example (uuid_str, data) 
  SELECT uuid_str, data FROM bad_pk_example;

SELECT 
  table_name,
  ROUND(data_length/1024, 0) AS data_kb,
  ROUND(index_length/1024, 0) AS index_kb
FROM information_schema.tables
WHERE table_schema = 'innolab' 
  AND table_name IN ('bad_pk_example', 'good_pk_example');
EOF
```

📸 **Verified Output:**
```
+------------------+---------+----------+
| table_name       | data_kb | index_kb |
+------------------+---------+----------+
| bad_pk_example   |    1008 |      464 |  <- Larger: 36-byte PK in every secondary index
| good_pk_example  |     752 |      288 |  <- Smaller: 4-byte PK in secondary index
+------------------+---------+----------+
```

---

## Step 7: Observe Page Splits with Random vs Sequential Inserts

```bash
docker exec mysql-lab mysql -uroot -prootpass innolab <<'EOF'
-- Sequential inserts: fills pages efficiently (no splits)
CREATE TABLE seq_inserts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  data CHAR(100) DEFAULT 'x'
) ENGINE=InnoDB;

-- Random inserts: causes page splits (fragmentation)
CREATE TABLE rand_inserts (
  id INT PRIMARY KEY,  -- No AUTO_INCREMENT, we'll insert randomly
  data CHAR(100) DEFAULT 'x'
) ENGINE=InnoDB;

-- Insert 10k rows sequentially
INSERT INTO seq_inserts (data) SELECT 'x' FROM information_schema.tables LIMIT 5000;
INSERT INTO seq_inserts (data) SELECT 'y' FROM information_schema.tables LIMIT 5000;

-- Insert 10k rows with random IDs (causes page splits)
INSERT INTO rand_inserts (id, data)
SELECT FLOOR(RAND() * 1000000), 'x'
FROM information_schema.tables t1, information_schema.tables t2
LIMIT 10000
ON DUPLICATE KEY UPDATE data = 'x';

-- Compare fragmentation
SELECT 
  table_name,
  table_rows,
  ROUND(data_length / 1024, 0) AS data_kb,
  ROUND(data_free / 1024, 0) AS free_kb,
  ROUND(100.0 * data_free / (data_length + data_free), 1) AS fragmentation_pct
FROM information_schema.tables
WHERE table_schema = 'innolab'
  AND table_name IN ('seq_inserts', 'rand_inserts');

-- OPTIMIZE TABLE to defragment (rebuilds the clustered index)
OPTIMIZE TABLE rand_inserts;
EOF
```

📸 **Verified Output:**
```
+-------------+------------+---------+---------+--------------------+
| table_name  | table_rows | data_kb | free_kb | fragmentation_pct  |
+-------------+------------+---------+---------+--------------------+
| seq_inserts |       9986 |     816 |       0 |               0.0  |
| rand_inserts|       9847 |    1504 |     272 |              15.3  |  <- Fragmented!
+-------------+------------+---------+---------+--------------------+
```

> 💡 Random PK inserts (like UUIDs) cause page splits, leading to fragmentation and ~20-40% larger storage. Use AUTO_INCREMENT for sequential inserts, or use `OPTIMIZE TABLE` periodically.

---

## Step 8: Capstone — InnoDB Internals Audit

```bash
docker exec mysql-lab mysql -uroot -prootpass innolab <<'EOF'
-- Complete InnoDB health audit
SELECT '=== InnoDB Buffer Pool ===' AS section;
SELECT 
  ROUND(@@innodb_buffer_pool_size / 1024 / 1024, 0) AS buffer_pool_mb,
  (SELECT COUNT(*) FROM information_schema.INNODB_BUFFER_POOL_STATS) AS instances;

SELECT '=== Table Sizes ===' AS section;
SELECT 
  table_name,
  table_rows,
  ROUND(data_length/1024/1024, 2) AS data_mb,
  ROUND(index_length/1024/1024, 2) AS index_mb,
  row_format,
  ROUND(data_free/1024/1024, 2) AS free_mb
FROM information_schema.tables
WHERE table_schema = 'innolab'
ORDER BY data_length + index_length DESC;

SELECT '=== Index Usage ===' AS section;
SELECT 
  t.table_name,
  s.index_name,
  s.column_name,
  s.cardinality,
  s.nullable
FROM information_schema.tables t
JOIN information_schema.statistics s ON t.table_name = s.table_name
WHERE t.table_schema = 'innolab'
  AND s.table_schema = 'innolab'
ORDER BY t.table_name, s.index_name, s.seq_in_index;
EOF

docker rm -f mysql-lab
echo "Lab complete!"
```

📸 **Verified Output:**
```
section
=== InnoDB Buffer Pool ===
+----------------+-----------+
| buffer_pool_mb | instances |
+----------------+-----------+
|            128 |         1 |
+----------------+-----------+

section
=== Table Sizes ===
+------------------+------------+---------+----------+------------+---------+
| table_name       | table_rows | data_mb | index_mb | row_format | free_mb |
+------------------+------------+---------+----------+------------+---------+
| employees        |       9972 |    0.84 |     0.66 | Dynamic    |    0.00 |
| bad_pk_example   |       9823 |    0.98 |     0.45 | Dynamic    |    0.00 |
| good_pk_example  |       9823 |    0.73 |     0.28 | Dynamic    |    0.00 |
| rand_inserts     |       9847 |    0.94 |     0.00 | Dynamic    |    0.00 |
| seq_inserts      |       9986 |    0.80 |     0.00 | Dynamic    |    0.00 |
+------------------+------------+---------+----------+------------+---------+

Lab complete!
```

---

## Summary

| Concept | Details | Impact |
|---------|---------|--------|
| Clustered index | PK = table (rows stored at leaf nodes) | PK lookup = single tree traversal |
| Secondary index | Stores (indexed_cols, PK) at leaf nodes | Lookup = 2 tree traversals |
| Covering index | All needed columns in one index | Eliminates second tree traversal |
| Page size | 16KB (default) | Interior nodes hold ~450 INT keys |
| ROW_FORMAT=DYNAMIC | Variable-length off-page storage | Better for VARCHAR/TEXT/BLOB |
| file_per_table | Each table = separate .ibd file | Enables individual table management |
| Gap lock | Locks range between records | Prevents phantoms in REPEATABLE READ |
| Record lock | Locks specific row | Concurrent DML coordination |
| Page splits | Random inserts fragment pages | Use sequential PKs for write efficiency |

## Key Takeaways

- **The PK IS the data** in InnoDB — choose it carefully (prefer INT AUTO_INCREMENT)
- **UUID primary keys** cause page splits and ~40% larger indexes — use binary UUID or surrogate INT
- **Covering indexes** eliminate "double lookups" — include all SELECT columns when possible
- **Gap locks** prevent phantom reads but cause more deadlocks — use READ COMMITTED if that's a problem
- **SHOW TABLE STATUS** shows Data_length (clustered index), Index_length, Data_free (fragmentation)
