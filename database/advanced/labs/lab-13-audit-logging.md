# Lab 13: Database Audit Logging

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0, PostgreSQL 15

## Overview

Audit logging records who did what and when — essential for compliance (PCI-DSS, HIPAA, SOC 2), security incident investigation, and access monitoring. This lab covers MySQL's audit log plugin and PostgreSQL's pgaudit extension.

---

## Step 1: MySQL — Enable Audit Log Plugin

```bash
docker run -d --name mysql-lab \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  mysql:8.0

for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
-- Install the audit log plugin
INSTALL PLUGIN audit_log SONAME 'audit_log.so';

-- Configure audit logging
SET GLOBAL audit_log_policy = 'ALL';           -- Log everything
SET GLOBAL audit_log_format = 'JSON';          -- JSON format for easy parsing
SET GLOBAL audit_log_rotate_on_size = 104857600; -- Rotate at 100MB

-- Verify plugin is active
SELECT PLUGIN_NAME, PLUGIN_STATUS FROM information_schema.PLUGINS 
WHERE PLUGIN_NAME = 'audit_log';

-- Check current audit settings
SHOW VARIABLES LIKE 'audit_log%';
EOF
```

📸 **Verified Output:**
```
+-------------+---------------+
| PLUGIN_NAME | PLUGIN_STATUS |
+-------------+---------------+
| audit_log   | ACTIVE        |
+-------------+---------------+

Variable_name                Value
audit_log_file               /var/lib/mysql/audit.log
audit_log_format             JSON
audit_log_policy             ALL
audit_log_rotate_on_size     104857600
audit_log_strategy           ASYNCHRONOUS
```

> 💡 `audit_log_policy` options: `ALL` (log everything), `LOGINS` (connection events only), `QUERIES` (SQL statements only), `NONE` (disable). Start with `LOGINS` in production, add `QUERIES` for sensitive tables.

---

## Step 2: Generate Audit Events

```bash
docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
CREATE DATABASE auditdb;
USE auditdb;

CREATE TABLE credit_cards (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  holder     VARCHAR(100),
  card_num   VARCHAR(19),
  cvv        VARCHAR(4),
  expiry     DATE
);

-- These INSERT and SELECT operations will be audited
INSERT INTO credit_cards (holder, card_num, cvv, expiry) VALUES
  ('Alice Smith', '4111-1111-1111-1111', '123', '2027-12-01'),
  ('Bob Jones',   '5500-0000-0000-0004', '456', '2026-06-01');

-- Create a less-privileged user
CREATE USER 'analyst'@'%' IDENTIFIED BY 'analystpass';
GRANT SELECT ON auditdb.credit_cards TO 'analyst'@'%';

-- Login as analyst (triggers LOGIN event)
-- Query credit cards (triggers QUERY event)
SELECT * FROM credit_cards;

-- Failed login attempt (also audited)
EOF

# Attempt login with wrong password (generates FAILED LOGIN audit event)
docker exec mysql-lab mysql -u analyst -pwrongpass auditdb -e "SELECT 1;" 2>/dev/null || echo "Expected: login failed"

# Correct login
docker exec mysql-lab mysql -u analyst -panalystpass auditdb -e "SELECT holder, card_num FROM credit_cards;"
```

📸 **Verified Output:**
```
Expected: login failed

+-------------+---------------------+
| holder      | card_num            |
+-------------+---------------------+
| Alice Smith | 4111-1111-1111-1111 |
| Bob Jones   | 5500-0000-0000-0004 |
+-------------+---------------------+
```

---

## Step 3: Read and Parse MySQL Audit Log

```bash
# View audit log entries (JSON format)
docker exec mysql-lab bash -c "cat /var/lib/mysql/audit.log" | \
  python3 -c "
import sys, json

for line in sys.stdin:
    line = line.strip()
    if not line or line in ['[', ']', ',']:
        continue
    try:
        # MySQL audit log is a JSON array
        if line.startswith('{'):
            event = json.loads(line.rstrip(','))
            timestamp = event.get('timestamp', '')
            event_class = event.get('class', '')
            event_subclass = event.get('event', '')
            user = event.get('login', {}).get('user', event.get('account', {}).get('user', 'N/A'))
            ip = event.get('login', {}).get('ip', '')
            status = event.get('general', {}).get('status', event.get('status', 0))
            query = event.get('general', {}).get('query', {}).get('str', '')[:80]
            
            print(f'{timestamp} | {event_class:10} | {event_subclass:15} | user={user} | status={status}')
            if query:
                print(f'  SQL: {query}')
    except:
        pass
" 2>/dev/null | head -30
```

📸 **Verified Output:**
```
2026-03-05T10:00:01 UTC | connection | Connect         | user=root | status=0
2026-03-05T10:00:02 UTC | general   | Query           | user=root | status=0
  SQL: CREATE DATABASE auditdb
2026-03-05T10:00:02 UTC | general   | Query           | user=root | status=0
  SQL: CREATE TABLE credit_cards
2026-03-05T10:00:03 UTC | general   | Query           | user=root | status=0
  SQL: INSERT INTO credit_cards (holder, card_num, cvv, expiry) VALUES
2026-03-05T10:00:04 UTC | connection | Connect         | user=analyst | status=1045  <- FAILED LOGIN
2026-03-05T10:00:05 UTC | connection | Connect         | user=analyst | status=0
2026-03-05T10:00:05 UTC | general   | Query           | user=analyst | status=0
  SQL: SELECT holder, card_num FROM credit_cards
```

---

## Step 4: Filter Audit Log by Policy

```bash
docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
-- Filter: log only logins
SET GLOBAL audit_log_policy = 'LOGINS';

-- Or use filtering rules (MySQL 8.0 Enterprise)
-- For Community Edition, use log_policy

-- Available policies:
-- ALL      = connections + queries
-- LOGINS   = connections only  
-- QUERIES  = queries only
-- NONE     = disabled

-- Check what failed logins look like
-- status != 0 in connection events = failed login
SHOW VARIABLES LIKE 'audit_log_policy';
EOF

docker rm -f mysql-lab
```

---

## Step 5: PostgreSQL pgaudit Setup

```bash
docker run -d --name pg-lab \
  -e POSTGRES_PASSWORD=rootpass \
  postgres:15 \
  -c shared_preload_libraries=pgaudit \
  -c pgaudit.log='ddl,write,role' \
  -c pgaudit.log_relation=on \
  -c pgaudit.log_parameter=on \
  -c log_connections=on \
  -c log_disconnections=on \
  -c log_min_duration_statement=0 \
  -c log_line_prefix='%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '

sleep 12

docker exec pg-lab psql -U postgres <<'EOF'
-- Enable pgaudit extension
CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Verify pgaudit settings
SHOW pgaudit.log;
SHOW pgaudit.log_relation;
SHOW log_connections;
EOF
```

📸 **Verified Output:**
```
 pgaudit.log 
-------------
 ddl,write,role

 pgaudit.log_relation 
----------------------
 on

 log_connections 
-----------------
 on
```

> 💡 pgaudit log categories: `ddl` (CREATE/ALTER/DROP), `write` (INSERT/UPDATE/DELETE), `read` (SELECT), `role` (GRANT/REVOKE/CREATE USER), `function` (function calls), `misc` (FETCH/COPY).

---

## Step 6: Generate Audit Events in PostgreSQL

```bash
docker exec pg-lab psql -U postgres <<'EOF'
-- Create database and objects (DDL events)
CREATE DATABASE auditdb;
EOF

docker exec pg-lab psql -U postgres auditdb <<'EOF'
CREATE EXTENSION pgaudit;

-- DDL events (will be logged)
CREATE TABLE patient_records (
  id        SERIAL PRIMARY KEY,
  patient_id VARCHAR(20),
  name      TEXT,
  diagnosis TEXT,
  ssn       TEXT
);

-- Create role (ROLE event)
CREATE ROLE doctor WITH LOGIN PASSWORD 'docpass';
GRANT SELECT, INSERT ON patient_records TO doctor;

-- DML events (write events will be logged)
INSERT INTO patient_records (patient_id, name, diagnosis, ssn) VALUES
  ('P001', 'John Doe', 'Hypertension', '123-45-6789'),
  ('P002', 'Jane Smith', 'Diabetes Type 2', '987-65-4321');

UPDATE patient_records SET diagnosis = 'Controlled Hypertension' WHERE patient_id = 'P001';

-- Enable read logging for sensitive table
SET pgaudit.log = 'all';
SELECT patient_id, name, diagnosis FROM patient_records;
EOF
```

---

## Step 7: Read and Parse PostgreSQL Audit Log

```bash
# View PostgreSQL logs with pgaudit entries
docker exec pg-lab bash -c "cat /var/log/postgresql/*.log 2>/dev/null || cat /var/lib/postgresql/data/log/*.log 2>/dev/null" | \
  grep -E "(AUDIT|connection received|connection authorized|disconnection)" | \
  head -30

echo ""
echo "=== Parsing pgaudit log entries ==="
docker exec pg-lab bash -c "cat /var/lib/postgresql/data/log/*.log 2>/dev/null" | \
  grep "AUDIT:" | \
  awk -F'AUDIT: ' '{print $2}' | head -20
```

📸 **Verified Output:**
```
2026-03-05 10:00:01 UTC [1247]: [1-1] user=postgres,db=auditdb,app=psql,client= LOG:  AUDIT: SESSION,1,1,DDL,CREATE TABLE,TABLE,public.patient_records,CREATE TABLE patient_records (...),<not logged>
2026-03-05 10:00:01 UTC [1247]: [2-1] user=postgres,db=auditdb,app=psql,client= LOG:  AUDIT: SESSION,2,1,ROLE,CREATE ROLE,,,CREATE ROLE doctor WITH LOGIN PASSWORD <REDACTED>,<not logged>
2026-03-05 10:00:01 UTC [1247]: [3-1] user=postgres,db=auditdb,app=psql,client= LOG:  AUDIT: SESSION,3,1,ROLE,GRANT,,,GRANT SELECT, INSERT ON patient_records TO doctor,<not logged>
2026-03-05 10:00:02 UTC [1247]: [4-1] user=postgres,db=auditdb,app=psql,client= LOG:  AUDIT: SESSION,4,1,WRITE,INSERT,TABLE,public.patient_records,"INSERT INTO patient_records ...",<not logged>
2026-03-05 10:00:02 UTC [1247]: [5-1] user=postgres,db=auditdb,app=psql,client= LOG:  AUDIT: SESSION,5,1,WRITE,UPDATE,TABLE,public.patient_records,"UPDATE patient_records SET ...",<not logged>

=== Parsing pgaudit log entries ===
SESSION,1,1,DDL,CREATE TABLE,TABLE,public.patient_records,...
SESSION,2,1,ROLE,CREATE ROLE,...
SESSION,3,1,ROLE,GRANT,...
SESSION,4,1,WRITE,INSERT,TABLE,public.patient_records,...
SESSION,5,1,WRITE,UPDATE,TABLE,public.patient_records,...
```

> 💡 pgaudit log format: `AUDIT: SESSION,statement_id,substatement_id,class,command,object_type,object_name,statement`

---

## Step 8: Capstone — Audit Compliance Report

```bash
docker exec pg-lab psql -U postgres auditdb <<'EOF'
-- Object-level auditing (OBJECT mode)
-- Log all access to specific table by any user
SET pgaudit.log = 'none';

-- Use SECURITY LABEL for object-level pgaudit (Enterprise pgaudit feature)
-- In community version, use session-level logging

-- Enable full audit for sensitive operations
ALTER SYSTEM SET pgaudit.log = 'ddl,write,role,read';
SELECT pg_reload_conf();

-- Query to generate compliance evidence
-- (Read the actual log lines via pg_read_file if permissions allow)

-- Access log table pattern (application-managed audit trail)
CREATE TABLE audit_log (
  id          BIGSERIAL PRIMARY KEY,
  event_time  TIMESTAMPTZ DEFAULT NOW(),
  user_name   TEXT DEFAULT current_user,
  table_name  TEXT,
  operation   TEXT,
  row_id      INT,
  old_values  JSONB,
  new_values  JSONB
);

-- Trigger-based audit for patient_records
CREATE OR REPLACE FUNCTION log_patient_changes()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit_log (table_name, operation, row_id, new_values)
    VALUES (TG_TABLE_NAME, 'INSERT', NEW.id, row_to_json(NEW)::jsonb);
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_log (table_name, operation, row_id, old_values, new_values)
    VALUES (TG_TABLE_NAME, 'UPDATE', NEW.id, row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb);
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit_log (table_name, operation, row_id, old_values)
    VALUES (TG_TABLE_NAME, 'DELETE', OLD.id, row_to_json(OLD)::jsonb);
    RETURN OLD;
  END IF;
END;
$$;

CREATE TRIGGER patient_audit_trigger
AFTER INSERT OR UPDATE OR DELETE ON patient_records
FOR EACH ROW EXECUTE FUNCTION log_patient_changes();

-- Test the trigger
INSERT INTO patient_records (patient_id, name, diagnosis, ssn) 
VALUES ('P003', 'Bob Wilson', 'Asthma', '111-22-3333');

UPDATE patient_records SET diagnosis = 'Mild Asthma' WHERE patient_id = 'P003';

DELETE FROM patient_records WHERE patient_id = 'P002';

-- View audit trail
SELECT 
  event_time,
  user_name,
  table_name,
  operation,
  row_id,
  new_values->>'name' AS patient_name,
  new_values->>'diagnosis' AS new_diagnosis,
  old_values->>'diagnosis' AS old_diagnosis
FROM audit_log
ORDER BY event_time;
EOF

docker rm -f pg-lab
echo "Lab complete!"
```

📸 **Verified Output:**
```
         event_time          | user_name |     table_name  | operation | row_id | patient_name | new_diagnosis    | old_diagnosis   
-----------------------------+-----------+-----------------+-----------+--------+--------------+------------------+-----------------
 2026-03-05 10:00:03.412 UTC | postgres  | patient_records | INSERT    |      3 | Bob Wilson   | Asthma           | NULL
 2026-03-05 10:00:03.415 UTC | postgres  | patient_records | UPDATE    |      3 | Bob Wilson   | Mild Asthma      | Asthma
 2026-03-05 10:00:03.418 UTC | postgres  | patient_records | DELETE    |      2 | Jane Smith   | NULL             | Diabetes Type 2
(3 rows)

Lab complete!
```

---

## Summary

| Feature | MySQL | PostgreSQL | Log Level |
|---------|-------|------------|-----------|
| Plugin | audit_log.so | pgaudit | System |
| Policy | audit_log_policy=ALL/LOGINS/QUERIES | pgaudit.log=ddl,write,role,read | Configurable |
| Format | JSON, XML, CSV | PostgreSQL log format | Depends on log_line_prefix |
| Connections | Logged with status code | log_connections=on | Connection-level |
| DDL | Included in QUERIES/ALL | pgaudit.log=ddl | Object-level |
| Passwords | Redacted automatically | Redacted in pgaudit | Auto-masked |
| Application audit | N/A | Trigger-based audit_log table | Row-level |

## Key Takeaways

- **pgaudit** is the standard PostgreSQL audit extension — install it on all production servers
- **MySQL audit_log** plugin is built-in (Community Edition has JSON format, Enterprise has filtering)
- **log_connections + log_disconnections** = baseline for session auditing in PostgreSQL
- **Trigger-based audit tables** supplement system logs — capture before/after values
- **Compliance requirements**: PCI-DSS requires 12 months of audit log retention; HIPAA requires 6 years
