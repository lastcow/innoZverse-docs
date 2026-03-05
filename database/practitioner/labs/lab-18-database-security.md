# Lab 18: Database Security

**Time:** 40 minutes | **Level:** Practitioner | **DB:** MySQL 8.0 + PostgreSQL 15

Database security encompasses authentication (who you are), authorization (what you can do), and data protection (row-level isolation, encryption). Misconfigured databases are the #1 source of data breaches.

---

## Step 1 — MySQL: CREATE USER and Password Policies

```sql
-- Create users with strong passwords
CREATE USER 'app_user'@'%'        IDENTIFIED BY 'AppPass123!';
CREATE USER 'readonly_user'@'%'   IDENTIFIED BY 'ReadOnly123!';
CREATE USER 'report_user'@'localhost' IDENTIFIED BY 'Report123!';

-- Require SSL connection
CREATE USER 'secure_user'@'%'
  IDENTIFIED BY 'SecurePass123!'
  REQUIRE SSL;

-- Password policy: expire after 90 days
CREATE USER 'audit_user'@'%'
  IDENTIFIED BY 'AuditPass123!'
  PASSWORD EXPIRE INTERVAL 90 DAY;

-- View users
SELECT user, host, plugin, account_locked, password_expired
FROM mysql.user
WHERE user NOT IN ('root','mysql.sys','mysql.infoschema','mysql.session');
```

---

## Step 2 — MySQL: GRANT and REVOKE

```sql
-- GRANT: specific permissions
GRANT SELECT ON labdb.* TO 'readonly_user'@'%';
GRANT SELECT, INSERT, UPDATE ON labdb.orders TO 'app_user'@'%';
GRANT ALL PRIVILEGES ON labdb.* TO 'app_user'@'%';  -- full access to labdb

-- Column-level grants
GRANT SELECT (id, customer, total) ON labdb.orders TO 'report_user'@'localhost';

-- SHOW GRANTS
SHOW GRANTS FOR 'readonly_user'@'%';
```

📸 **Verified Output:**
```
Grants for readonly_user@%
GRANT USAGE ON *.* TO `readonly_user`@`%`
GRANT SELECT ON `labdb`.* TO `readonly_user`@`%`
```

```sql
-- REVOKE: remove specific permissions
REVOKE INSERT, UPDATE ON labdb.orders FROM 'app_user'@'%';
SHOW GRANTS FOR 'app_user'@'%';

-- Apply changes immediately
FLUSH PRIVILEGES;

-- Drop user
DROP USER IF EXISTS 'audit_user'@'%';
```

---

## Step 3 — MySQL 8: Roles

```sql
-- Create roles
CREATE ROLE 'reader', 'writer', 'admin';

-- Grant permissions to roles
GRANT SELECT ON labdb.* TO 'reader';
GRANT SELECT, INSERT, UPDATE, DELETE ON labdb.* TO 'writer';
GRANT ALL PRIVILEGES ON labdb.* TO 'admin';

-- Assign roles to users
GRANT 'reader' TO 'readonly_user'@'%';
GRANT 'writer' TO 'app_user'@'%';

-- Set default roles (active without SET ROLE)
SET DEFAULT ROLE 'reader' TO 'readonly_user'@'%';
SET DEFAULT ROLE 'writer' TO 'app_user'@'%';

-- Check role members
SELECT * FROM information_schema.APPLICABLE_ROLES
WHERE GRANTEE IN ("'readonly_user'@'%'", "'app_user'@'%'");

-- Activate a role in a session
SET ROLE 'admin';
SELECT CURRENT_ROLE();
SET ROLE NONE;
```

> 💡 MySQL 8 roles work like "permission templates" — change the role and all role members immediately get updated permissions. No need to re-grant each user individually.

---

## Step 4 — PostgreSQL: CREATE ROLE and GRANT

```sql
-- PostgreSQL: everything is a ROLE (users are roles with LOGIN)
CREATE ROLE readonly_role;
CREATE ROLE analyst_role;
CREATE ROLE admin_role;

-- Create users (roles with LOGIN privilege)
CREATE USER app_user      WITH PASSWORD 'AppPass123!'  LOGIN;
CREATE USER analyst_user  WITH PASSWORD 'AnalystPass!' LOGIN;

-- Connection limit
CREATE USER limited_user  WITH PASSWORD 'LimitedPass!' LOGIN CONNECTION LIMIT 5;

-- Grant schema and table permissions
GRANT CONNECT ON DATABASE postgres TO app_user, analyst_user;
GRANT USAGE   ON SCHEMA public TO readonly_role, analyst_role;
GRANT SELECT  ON ALL TABLES IN SCHEMA public TO readonly_role;
GRANT SELECT, INSERT, UPDATE ON products, sales TO analyst_role;

-- Grant future tables too (new tables inherit permissions)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO readonly_role;

-- Assign roles to users
GRANT readonly_role TO app_user;
GRANT analyst_role  TO analyst_user;

-- Check roles
SELECT rolname, rolsuper, rolcreatedb, rolcanlogin, rolconnlimit
FROM pg_roles
WHERE rolname IN ('readonly_role','analyst_role','app_user','analyst_user');
```

📸 **Verified Output:**
```
    rolname    | rolsuper | rolcreatedb | rolcanlogin | rolconnlimit
---------------+----------+-------------+-------------+--------------
 readonly_role | f        | f           | f           |           -1
 analyst_role  | f        | f           | f           |           -1
 app_user      | f        | f           | t           |           -1
 analyst_user  | f        | f           | t           |           -1
(4 rows)
```

---

## Step 5 — PostgreSQL: Row-Level Security (RLS)

RLS filters rows at the database level — users can only see/modify rows they're permitted to.

```sql
CREATE TABLE user_data (
  id         SERIAL PRIMARY KEY,
  owner      TEXT,
  secret_info TEXT
);

INSERT INTO user_data (owner, secret_info) VALUES
  ('alice', 'Alice secret: bank_account=12345'),
  ('bob',   'Bob secret: salary=95000'),
  ('alice', 'Alice note: password_hint=cat');

-- Enable Row Level Security
ALTER TABLE user_data ENABLE ROW LEVEL SECURITY;

-- Create policy: users only see their own rows
CREATE POLICY user_isolation ON user_data
  USING (owner = current_user);

-- Superuser bypasses RLS (use FORCE for testing)
ALTER TABLE user_data FORCE ROW LEVEL SECURITY;

-- Test as superuser (still sees all due to superuser bypass)
SELECT * FROM user_data;

-- Verify RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables WHERE tablename = 'user_data';
```

📸 **Verified Output:**
```
 tablename | rowsecurity
-----------+-------------
 user_data | t
```

```sql
-- More granular policy: allow reads, restrict writes
CREATE POLICY user_select ON user_data
  FOR SELECT USING (owner = current_user);

CREATE POLICY user_insert ON user_data
  FOR INSERT WITH CHECK (owner = current_user);

CREATE POLICY user_update ON user_data
  FOR UPDATE USING (owner = current_user)
  WITH CHECK (owner = current_user);

-- Admin bypass policy
CREATE POLICY admin_all ON user_data
  USING (current_user = 'postgres');
```

---

## Step 6 — PostgreSQL: Column-Level Security

```sql
CREATE TABLE salary_data (
  id         SERIAL PRIMARY KEY,
  employee   TEXT,
  department TEXT,
  salary     NUMERIC(12,2),
  ssn        TEXT  -- sensitive
);

INSERT INTO salary_data VALUES
  (1, 'Alice', 'Tech',    90000, '123-45-6789'),
  (2, 'Bob',   'Finance', 85000, '987-65-4321');

-- Grant SELECT on all columns except salary and ssn
GRANT SELECT (id, employee, department) ON salary_data TO readonly_role;
-- readonly_role cannot query: SELECT salary FROM salary_data → ERROR

-- Revoke column permission
REVOKE SELECT (ssn) ON salary_data FROM readonly_role;
```

---

## Step 7 — pg_hba.conf and SSL Concepts

**pg_hba.conf** (PostgreSQL Host-Based Authentication) controls who can connect:

```
# TYPE  DATABASE  USER        ADDRESS         METHOD
local   all       postgres                    peer
host    all       all         127.0.0.1/32    scram-sha-256
host    mydb      app_user    10.0.0.0/8      scram-sha-256
host    all       all         0.0.0.0/0       reject
hostssl all       secure_user 0.0.0.0/0       scram-sha-256
```

Authentication methods:
| Method | Description |
|--------|-------------|
| `trust` | No password (dev only!) |
| `password` | Plaintext (never use) |
| `md5` | MD5 hash (legacy) |
| `scram-sha-256` | Modern secure (recommended) |
| `peer` | OS username must match |
| `cert` | TLS client certificate |

```sql
-- In PostgreSQL: check SSL status
SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid();

-- Force SSL in connection string:
-- psql "host=dbserver sslmode=require dbname=mydb user=myuser"
```

---

## Step 8 — Capstone: Secure Multi-Tenant Database

```sql
-- Multi-tenant SaaS: each tenant only sees their data

CREATE TABLE tenants (
  id   INT PRIMARY KEY,
  name TEXT,
  slug TEXT UNIQUE
);

CREATE TABLE tenant_data (
  id         SERIAL PRIMARY KEY,
  tenant_id  INT REFERENCES tenants(id),
  data_key   TEXT,
  data_value TEXT
);

INSERT INTO tenants VALUES (1,'Acme Corp','acme'), (2,'TechCo','techco');
INSERT INTO tenant_data (tenant_id, data_key, data_value) VALUES
  (1,'config','acme_setting_1'),
  (1,'secret','acme_api_key_xyz'),
  (2,'config','techco_setting_1'),
  (2,'secret','techco_api_key_abc');

-- Enable RLS
ALTER TABLE tenant_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_data FORCE ROW LEVEL SECURITY;

-- Set current tenant via session variable
SET app.current_tenant_id = '1';

-- RLS policy using session variable
CREATE POLICY tenant_isolation ON tenant_data
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::INT);

-- Test: tenant 1 can only see their rows
SET app.current_tenant_id = '1';
SELECT * FROM tenant_data;
-- Only rows with tenant_id = 1

SET app.current_tenant_id = '2';
SELECT * FROM tenant_data;
-- Only rows with tenant_id = 2

-- Summary of security applied
SELECT schemaname, tablename, rowsecurity, forcerowsecurity
FROM pg_tables
WHERE tablename IN ('user_data', 'tenant_data', 'salary_data');
```

---

## Summary

| Feature | MySQL | PostgreSQL |
|---------|-------|-----------|
| Create user | `CREATE USER 'u'@'h' IDENTIFIED BY 'p'` | `CREATE USER u WITH PASSWORD 'p'` |
| Grant table | `GRANT SELECT ON db.tbl TO u@h` | `GRANT SELECT ON tbl TO role` |
| Grant DB | `GRANT ALL ON db.* TO u@h` | `GRANT CONNECT ON DATABASE db TO u` |
| Roles | MySQL 8+: `CREATE ROLE r` | `CREATE ROLE r` (native) |
| Column grants | `GRANT SELECT (col1,col2) ON tbl` | `GRANT SELECT (col) ON tbl` |
| Row-level security | Not built-in (use views) | `ALTER TABLE t ENABLE ROW LEVEL SECURITY` |
| View grants | `SHOW GRANTS FOR u@h` | `\dp` or `pg_roles` + `information_schema` |
| Auth config | `mysql.user` table | `pg_hba.conf` file |
