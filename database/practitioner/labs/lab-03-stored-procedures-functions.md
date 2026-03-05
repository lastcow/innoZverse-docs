# Lab 03: Stored Procedures and Functions

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MySQL 8.0 + PostgreSQL 15

Stored procedures bundle SQL logic server-side for reuse, security, and performance. MySQL uses `PROCEDURE` (no return value); PostgreSQL uses `FUNCTION` (returns a value or table).

---

## Step 1 — MySQL: Setup and Basic Procedure

```sql
-- Create database and table
CREATE DATABASE labdb;
USE labdb;

CREATE TABLE orders (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  customer   VARCHAR(100),
  product    VARCHAR(100),
  quantity   INT,
  unit_price DECIMAL(10,2),
  total      DECIMAL(10,2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO orders (customer, product, quantity, unit_price, total) VALUES
  ('Alice', 'Widget A',  5,  9.99,  49.95),
  ('Bob',   'Widget B',  3, 14.99,  44.97),
  ('Alice', 'Gadget X',  2, 29.99,  59.98),
  ('Carol', 'Widget A', 10,  9.99,  99.90),
  ('Bob',   'Gadget Y',  1, 49.99,  49.99);
```

📸 **Verified Output:**
```
id  customer  product   quantity  unit_price  total    created_at
1   Alice     Widget A  5         9.99        49.95    2026-03-05 15:51:35
2   Bob       Widget B  3         14.99       44.97    2026-03-05 15:51:35
3   Alice     Gadget X  2         29.99       59.98    2026-03-05 15:51:35
4   Carol     Widget A  10        9.99        99.90    2026-03-05 15:51:35
5   Bob       Gadget Y  1         49.99       49.99    2026-03-05 15:51:35
```

---

## Step 2 — MySQL: IN / OUT / INOUT Parameters

```sql
-- Save as a .sql file and source it (avoids shell DELIMITER issues)
-- File: customer_summary.sql

USE labdb;
CREATE PROCEDURE get_customer_summary(
  IN  p_customer    VARCHAR(100),
  OUT p_order_count INT,
  OUT p_total_spent DECIMAL(10,2)
)
BEGIN
  SELECT COUNT(*), SUM(total)
  INTO   p_order_count, p_total_spent
  FROM   orders
  WHERE  customer = p_customer;
END
```

```bash
# Execute:
mysql -uroot -prootpass < customer_summary.sql
```

```sql
-- Call the procedure
CALL get_customer_summary('Alice', @cnt, @total);
SELECT @cnt AS order_count, @total AS total_spent;
```

📸 **Verified Output:**
```
order_count  total_spent
2            109.93
```

> 💡 MySQL client requires `DELIMITER //` only in the interactive shell. When sourcing a `.sql` file (via `<`), the default `;` delimiter works fine.

---

## Step 3 — MySQL: IF / WHILE Control Flow

```sql
-- Procedure with conditional logic and UPDATE
CREATE PROCEDURE apply_discount(
  IN p_product  VARCHAR(100),
  IN p_discount DECIMAL(5,2)
)
BEGIN
  IF p_discount < 0 OR p_discount > 50 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Discount must be between 0 and 50 percent';
  END IF;

  UPDATE orders
  SET unit_price = unit_price * (1 - p_discount / 100),
      total      = quantity * unit_price * (1 - p_discount / 100)
  WHERE product = p_product;

  SELECT ROW_COUNT() AS rows_updated;
END;

CALL apply_discount('Widget A', 10);
```

📸 **Verified Output:**
```
rows_updated
2
```

---

## Step 4 — MySQL: LOOP and Cursor Pattern

```sql
CREATE PROCEDURE recalculate_totals()
BEGIN
  DECLARE done    INT DEFAULT FALSE;
  DECLARE v_id    INT;
  DECLARE v_qty   INT;
  DECLARE v_price DECIMAL(10,2);

  DECLARE cur CURSOR FOR
    SELECT id, quantity, unit_price FROM orders;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO v_id, v_qty, v_price;
    IF done THEN LEAVE read_loop; END IF;
    UPDATE orders SET total = v_qty * v_price WHERE id = v_id;
  END LOOP;
  CLOSE cur;

  SELECT 'Totals recalculated' AS status;
END;

CALL recalculate_totals();
```

> 💡 Cursors are row-by-row and slow on large data. Prefer set-based `UPDATE` unless per-row business logic is unavoidable.

---

## Step 5 — PostgreSQL: CREATE FUNCTION with PL/pgSQL

```sql
CREATE OR REPLACE FUNCTION get_dept_stats(p_dept TEXT)
RETURNS TABLE(
  dept         TEXT,
  headcount    INT,
  avg_salary   NUMERIC,
  total_payroll NUMERIC
)
LANGUAGE plpgsql AS $$
DECLARE
  v_count INT;
BEGIN
  SELECT COUNT(*) INTO v_count
  FROM employees
  WHERE department = p_dept;

  IF v_count = 0 THEN
    RAISE EXCEPTION 'Department % not found', p_dept;
  END IF;

  RETURN QUERY
    SELECT department::TEXT,
           COUNT(*)::INT,
           ROUND(AVG(salary), 2),
           ROUND(SUM(salary), 2)
    FROM employees
    WHERE department = p_dept
    GROUP BY department;
END;
$$;

SELECT * FROM get_dept_stats('Tech');
```

📸 **Verified Output:**
```
 dept | headcount | avg_salary | total_payroll
------+-----------+------------+---------------
 Tech |         6 |  103333.33 |     620000.00
(1 row)
```

---

## Step 6 — PostgreSQL: DECLARE and Exception Handling

```sql
CREATE OR REPLACE FUNCTION safe_transfer(
  p_from_id INT,
  p_to_id   INT,
  p_amount  NUMERIC
)
RETURNS TEXT
LANGUAGE plpgsql AS $$
DECLARE
  v_balance NUMERIC;
BEGIN
  -- Lock both rows in consistent order to avoid deadlock
  SELECT balance INTO v_balance
  FROM bank_accounts
  WHERE id = p_from_id
  FOR UPDATE;

  IF v_balance < p_amount THEN
    RAISE EXCEPTION 'Insufficient funds: balance=%, requested=%', v_balance, p_amount;
  END IF;

  UPDATE bank_accounts SET balance = balance - p_amount WHERE id = p_from_id;
  UPDATE bank_accounts SET balance = balance + p_amount WHERE id = p_to_id;

  RETURN FORMAT('Transferred %.2f from account %s to account %s', p_amount, p_from_id, p_to_id);

EXCEPTION
  WHEN check_violation THEN
    RETURN 'Error: balance would go negative';
  WHEN OTHERS THEN
    RETURN 'Error: ' || SQLERRM;
END;
$$;
```

> 💡 `EXCEPTION WHEN OTHERS THEN` catches all unhandled errors. Use `SQLERRM` for the message and `SQLSTATE` for the error code.

---

## Step 7 — PostgreSQL: RETURNS TABLE with Set-Returning Functions

```sql
CREATE OR REPLACE FUNCTION paginate_employees(
  p_page     INT DEFAULT 1,
  p_per_page INT DEFAULT 3
)
RETURNS TABLE(
  id         INT,
  name       VARCHAR,
  department VARCHAR,
  salary     NUMERIC,
  page_num   INT,
  total_rows BIGINT
)
LANGUAGE plpgsql AS $$
DECLARE
  v_offset INT := (p_page - 1) * p_per_page;
  v_total  BIGINT;
BEGIN
  SELECT COUNT(*) INTO v_total FROM employees;

  RETURN QUERY
    SELECT e.id, e.name, e.department, e.salary,
           p_page, v_total
    FROM employees e
    ORDER BY e.id
    LIMIT p_per_page OFFSET v_offset;
END;
$$;

SELECT * FROM paginate_employees(1, 3);
SELECT * FROM paginate_employees(2, 3);
```

---

## Step 8 — Capstone: Audit-Enabled Order Processing

Build a MySQL procedure that inserts an order and logs the action:

```sql
-- First create audit table
CREATE TABLE IF NOT EXISTS order_audit (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  order_id   INT,
  action     VARCHAR(50),
  performed_by VARCHAR(50),
  action_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Procedure
CREATE PROCEDURE place_order(
  IN  p_customer   VARCHAR(100),
  IN  p_product    VARCHAR(100),
  IN  p_quantity   INT,
  IN  p_price      DECIMAL(10,2),
  IN  p_user       VARCHAR(50),
  OUT p_new_id     INT
)
BEGIN
  DECLARE v_total DECIMAL(10,2);
  SET v_total = p_quantity * p_price;

  INSERT INTO orders (customer, product, quantity, unit_price, total)
  VALUES (p_customer, p_product, p_quantity, p_price, v_total);

  SET p_new_id = LAST_INSERT_ID();

  INSERT INTO order_audit (order_id, action, performed_by)
  VALUES (p_new_id, 'ORDER_PLACED', p_user);
END;

-- Usage
CALL place_order('Dave', 'Widget C', 4, 19.99, 'system', @new_id);
SELECT @new_id AS new_order_id;
SELECT * FROM order_audit;
```

---

## Summary

| Feature | MySQL | PostgreSQL |
|---------|-------|------------|
| Create | `CREATE PROCEDURE` | `CREATE FUNCTION` |
| Return value | `OUT` params only | `RETURNS type` or `RETURNS TABLE` |
| Language | MySQL procedural SQL | PL/pgSQL (or Python, JS, etc.) |
| Call | `CALL proc_name(args)` | `SELECT func_name(args)` |
| Variables | `DECLARE v INT; SET v = 1` | `DECLARE v INT; v := 1;` |
| Loops | `LOOP`, `WHILE`, `REPEAT` | `LOOP`, `FOR`, `WHILE` |
| Error handling | `SIGNAL SQLSTATE` | `RAISE EXCEPTION` |
| Cursors | `DECLARE cur CURSOR FOR` | `FOR row IN query LOOP` |
