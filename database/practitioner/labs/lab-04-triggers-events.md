# Lab 04: Triggers and Events

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MySQL 8.0 + PostgreSQL 15

Triggers are database callbacks that fire automatically on `INSERT`, `UPDATE`, or `DELETE`. Events (MySQL) and pg_cron (PostgreSQL) schedule periodic tasks without external cron jobs.

---

## Step 1 — Setup: Orders and Audit Table

**MySQL:**
```sql
USE labdb;

CREATE TABLE IF NOT EXISTS audit_log (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  table_name  VARCHAR(50),
  action      VARCHAR(20),
  record_id   INT,
  changed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  details     TEXT
);
```

**PostgreSQL:**
```sql
CREATE TABLE audit_log (
  id         SERIAL PRIMARY KEY,
  table_name TEXT,
  action     TEXT,
  record_id  INT,
  old_data   JSONB,
  new_data   JSONB,
  changed_at TIMESTAMP DEFAULT NOW()
);
```

---

## Step 2 — MySQL: AFTER INSERT Trigger

```sql
-- File: trigger_insert.sql
USE labdb;
CREATE TRIGGER orders_after_insert
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
  INSERT INTO audit_log (table_name, action, record_id, details)
  VALUES (
    'orders',
    'INSERT',
    NEW.id,
    CONCAT('Customer: ', NEW.customer, ', Total: $', NEW.total)
  );
END
```

```bash
mysql -uroot -prootpass labdb < trigger_insert.sql
```

```sql
-- Test it
INSERT INTO orders (customer, product, quantity, unit_price, total)
VALUES ('Dave', 'Widget C', 4, 19.99, 79.96);

SELECT * FROM audit_log;
```

📸 **Verified Output:**
```
id  table_name  action  record_id  changed_at           details
1   orders      INSERT  6          2026-03-05 15:53:14  Customer: Dave, Total: $79.96
```

> 💡 `NEW.column` refers to the incoming row in INSERT/UPDATE triggers. `OLD.column` refers to the row being replaced or deleted.

---

## Step 3 — MySQL: BEFORE UPDATE Trigger

```sql
CREATE TRIGGER orders_before_update
BEFORE UPDATE ON orders
FOR EACH ROW
BEGIN
  -- Prevent price from decreasing by more than 50%
  IF NEW.unit_price < OLD.unit_price * 0.5 THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Price reduction exceeds 50% limit';
  END IF;
  -- Auto-recalculate total
  SET NEW.total = NEW.quantity * NEW.unit_price;
END
```

```sql
-- Test: this should succeed
UPDATE orders SET unit_price = 18.00 WHERE id = 6;

-- Test: this should fail
UPDATE orders SET unit_price = 5.00 WHERE id = 6;
-- Error: Price reduction exceeds 50% limit
```

> 💡 BEFORE triggers can modify `NEW` values before the row is written. AFTER triggers fire after the row is written and cannot change it.

---

## Step 4 — MySQL: AFTER DELETE Trigger + Soft Delete

```sql
CREATE TABLE orders_deleted (
  id         INT,
  customer   VARCHAR(100),
  product    VARCHAR(100),
  total      DECIMAL(10,2),
  deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TRIGGER orders_after_delete
AFTER DELETE ON orders
FOR EACH ROW
BEGIN
  INSERT INTO orders_deleted (id, customer, product, total)
  VALUES (OLD.id, OLD.customer, OLD.product, OLD.total);

  INSERT INTO audit_log (table_name, action, record_id, details)
  VALUES ('orders', 'DELETE', OLD.id,
          CONCAT('Deleted: ', OLD.customer, ' - ', OLD.product));
END
```

---

## Step 5 — MySQL: Event Scheduler

```sql
-- Enable the scheduler
SET GLOBAL event_scheduler = ON;

-- Create a daily cleanup event
CREATE EVENT IF NOT EXISTS cleanup_old_audit_logs
ON SCHEDULE EVERY 1 DAY
STARTS NOW()
DO
BEGIN
  DELETE FROM audit_log
  WHERE changed_at < NOW() - INTERVAL 30 DAY;
END;

-- View events
SHOW EVENTS\G

-- Disable event
ALTER EVENT cleanup_old_audit_logs DISABLE;
```

> 💡 The MySQL Event Scheduler is equivalent to cron for database tasks — no external scheduler needed. Check `SELECT @@event_scheduler;` to confirm it's `ON`.

---

## Step 6 — PostgreSQL: Trigger Function + CREATE TRIGGER

```sql
-- Trigger functions return TRIGGER type
CREATE OR REPLACE FUNCTION log_employee_changes()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit_log(table_name, action, record_id, new_data)
    VALUES (TG_TABLE_NAME, 'INSERT', NEW.id, row_to_json(NEW)::JSONB);
    RETURN NEW;

  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_log(table_name, action, record_id, old_data, new_data)
    VALUES (TG_TABLE_NAME, 'UPDATE', NEW.id,
            row_to_json(OLD)::JSONB, row_to_json(NEW)::JSONB);
    RETURN NEW;

  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit_log(table_name, action, record_id, old_data)
    VALUES (TG_TABLE_NAME, 'DELETE', OLD.id, row_to_json(OLD)::JSONB);
    RETURN OLD;
  END IF;
END;
$$;

-- Attach trigger to table
CREATE TRIGGER employee_audit
AFTER INSERT OR UPDATE OR DELETE ON employees
FOR EACH ROW EXECUTE FUNCTION log_employee_changes();
```

> 💡 PostgreSQL separates the trigger function (logic) from the trigger (attachment). One function can be reused across multiple tables.

---

## Step 7 — PostgreSQL: Test Trigger and INSTEAD OF on Views

```sql
-- Test the trigger
UPDATE employees SET salary = salary * 1.1 WHERE id = 7;

SELECT table_name, action, record_id,
       old_data->>'salary' AS old_sal,
       new_data->>'salary' AS new_sal
FROM audit_log;
```

📸 **Verified Output:**
```
 table_name | action | record_id | old_sal  | new_sal
------------+--------+-----------+----------+----------
 employees  | UPDATE |         7 | 70000.00 | 77000.00
(1 row)
```

```sql
-- INSTEAD OF trigger on a view
CREATE VIEW active_employees AS
  SELECT id, name, department, salary
  FROM employees WHERE salary > 80000;

CREATE OR REPLACE FUNCTION instead_of_update_view()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  UPDATE employees SET salary = NEW.salary WHERE id = NEW.id;
  RETURN NEW;
END;
$$;

CREATE TRIGGER active_employees_update
INSTEAD OF UPDATE ON active_employees
FOR EACH ROW EXECUTE FUNCTION instead_of_update_view();

-- Now updating the view works
UPDATE active_employees SET salary = 160000 WHERE id = 2;
```

---

## Step 8 — Capstone: Inventory Trigger System

Build a trigger that automatically decrements stock when an order is placed:

```sql
-- PostgreSQL version
CREATE TABLE inventory (
  product_id   INT PRIMARY KEY,
  product_name VARCHAR(100),
  stock_qty    INT CHECK (stock_qty >= 0)
);

CREATE TABLE order_items (
  id         SERIAL PRIMARY KEY,
  product_id INT REFERENCES inventory(product_id),
  qty        INT,
  ordered_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO inventory VALUES (1,'Widget A',100),(2,'Widget B',50),(3,'Gadget X',25);

CREATE OR REPLACE FUNCTION deduct_inventory()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  UPDATE inventory
  SET stock_qty = stock_qty - NEW.qty
  WHERE product_id = NEW.product_id;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Product % not found', NEW.product_id;
  END IF;

  RETURN NEW;
EXCEPTION
  WHEN check_violation THEN
    RAISE EXCEPTION 'Insufficient stock for product %', NEW.product_id;
END;
$$;

CREATE TRIGGER deduct_on_order
AFTER INSERT ON order_items
FOR EACH ROW EXECUTE FUNCTION deduct_inventory();

-- Test
INSERT INTO order_items (product_id, qty) VALUES (1, 10);
SELECT * FROM inventory WHERE product_id = 1;
-- stock_qty = 90
```

---

## Summary

| Concept | MySQL | PostgreSQL |
|---------|-------|------------|
| Trigger timing | `BEFORE` / `AFTER` | `BEFORE` / `AFTER` / `INSTEAD OF` |
| Trigger events | `INSERT` / `UPDATE` / `DELETE` | `INSERT` / `UPDATE` / `DELETE` / `TRUNCATE` |
| Row reference | `NEW`, `OLD` | `NEW`, `OLD` |
| Modify before write | `BEFORE` + `SET NEW.col` | `BEFORE` + `NEW.col := val` |
| Raise error | `SIGNAL SQLSTATE '45000'` | `RAISE EXCEPTION '...'` |
| Scheduling | `CREATE EVENT ... ON SCHEDULE` | pg_cron extension |
| View triggers | Not supported | `INSTEAD OF` on views |
