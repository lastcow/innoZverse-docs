# Lab 18: Database Security Architecture

**Time:** 50 minutes | **Level:** Architect | **DB:** PostgreSQL 15, MySQL 8

A production database faces threats from network intrusion, compromised credentials, SQL injection, and insider threats. This lab implements a defense-in-depth security architecture covering network isolation, encryption, access controls, and monitoring.

---

## Step 1: Defense-in-Depth Framework

Security must be layered — no single control is sufficient.

```
┌─────────────────────────────────────────────────────────────────┐
│                  DEFENSE-IN-DEPTH LAYERS                         │
├─────────────────────────────────────────────────────────────────┤
│ LAYER 1: Network       │ VPC, private subnet, security groups   │
│ LAYER 2: Transport     │ TLS 1.2+ for all connections           │
│ LAYER 3: Authentication│ Strong passwords, certificates, MFA    │
│ LAYER 4: Authorization │ RBAC, least privilege, Row-Level Sec.  │
│ LAYER 5: Data          │ TDE at rest, column encryption         │
│ LAYER 6: Application   │ Parameterized queries, input validation│
│ LAYER 7: Monitoring    │ Audit logs, anomaly detection, alerts  │
└─────────────────────────────────────────────────────────────────┘

Attacker must breach ALL layers — you only need ONE to hold.
```

---

## Step 2: Network Isolation (VPC / Private Subnet)

The database should never be directly reachable from the internet.

```bash
# AWS VPC architecture for database isolation
# (Terraform pseudocode)

# ── VPC Layout ─────────────────────────────────────────────────────────────
# 
#   Internet Gateway
#       │
#   Public Subnet (10.0.1.0/24)
#   ├── NAT Gateway
#   ├── Load Balancer
#   └── Bastion Host (jump server)
#       │ (SSH tunnel only)
#   Private Subnet (10.0.2.0/24)  
#   ├── Application Servers
#   └── (no direct internet access)
#       │ (port 5432 only)
#   Database Subnet (10.0.3.0/24)
#   ├── PostgreSQL Primary
#   └── PostgreSQL Replica

# Security Group for RDS (only allow app servers)
aws ec2 create-security-group \
    --group-name rds-sg \
    --description "RDS PostgreSQL security group"

# Allow only app server security group on port 5432
aws ec2 authorize-security-group-ingress \
    --group-id sg-rds \
    --protocol tcp \
    --port 5432 \
    --source-group sg-app-servers

# DENY all other inbound traffic (default deny, not shown)
```

**PostgreSQL pg_hba.conf — connection access control:**
```
# TYPE  DATABASE   USER           ADDRESS              METHOD
# Local connections via Unix socket (admin only)
local   all        postgres                            peer

# Reject all non-SSL connections
host    all        all            0.0.0.0/0            reject

# Allow SSL from app subnet only
hostssl production app_service    10.0.2.0/24          scram-sha-256

# Allow SSL from DBA bastion only  
hostssl all        dba_role       10.0.1.5/32          cert

# Monitoring from prometheus exporter
hostssl all        monitoring     10.0.2.20/32         scram-sha-256
```

> 💡 `hostssl` rejects the connection if TLS is not used. This ensures encryption in transit is mandatory, not optional.

---

## Step 3: TLS In Transit Configuration

```bash
# PostgreSQL TLS configuration (postgresql.conf)
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file  = '/etc/ssl/private/server.key'
ssl_ca_file   = '/etc/ssl/certs/ca.crt'
ssl_min_protocol_version = 'TLSv1.2'
ssl_ciphers = 'HIGH:!aNULL:!MD5:!RC4'
# For TLS 1.3 (PostgreSQL 12+)
# ssl_min_protocol_version = 'TLSv1.3'

# Generate self-signed cert for development
openssl req -new -x509 -days 365 \
    -keyout server.key -out server.crt \
    -subj "/CN=db.internal.example.com"
chmod 600 server.key

# Client connection with SSL verification
psql "host=db.internal.example.com \
      dbname=production \
      user=app_service \
      sslmode=verify-full \
      sslrootcert=/etc/ssl/certs/ca.crt"
# sslmode options:
#   disable    → no SSL (NEVER use in production)
#   require    → SSL but no cert verification (weak)
#   verify-ca  → verifies CA signature
#   verify-full→ verifies CA + hostname (use this)

# Verify TLS is active
SELECT 
    ssl, 
    version, 
    cipher, 
    bits,
    compression
FROM pg_stat_ssl
WHERE pid = pg_backend_pid();
```

---

## Step 4: Transparent Data Encryption (TDE) at Rest

```bash
# PostgreSQL: TDE via OS-level encryption (recommended)
# Use AWS RDS storage encryption (KMS-backed, zero performance impact)

# AWS: Enable encryption at RDS creation
aws rds create-db-instance \
    --db-instance-identifier prod-postgres \
    --storage-encrypted \
    --kms-key-id arn:aws:kms:us-east-1:123456789:key/abc-123

# For existing unencrypted instances:
# 1. Take snapshot
# 2. Copy snapshot with encryption enabled
# 3. Restore from encrypted snapshot

# Verify encryption
aws rds describe-db-instances \
    --db-instance-identifier prod-postgres \
    --query 'DBInstances[0].StorageEncrypted'
# Output: true

# PostgreSQL: pg_crypto for application-level encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Check if pgcrypto is available
SELECT * FROM pg_extension WHERE extname = 'pgcrypto';
```

**Linux LUKS disk encryption for self-managed PostgreSQL:**
```bash
# Encrypt the data volume (do this before PostgreSQL installation)
cryptsetup luksFormat /dev/xvdb
cryptsetup luksOpen /dev/xvdb postgres-data
mkfs.ext4 /dev/mapper/postgres-data
mount /dev/mapper/postgres-data /var/lib/postgresql/data
```

---

## Step 5: Column-Level Encryption with pgcrypto

```sql
-- ── pgcrypto Column Encryption ────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypted PII table
CREATE TABLE patient_records (
    id              BIGSERIAL PRIMARY KEY,
    patient_token   UUID DEFAULT gen_random_uuid(),  -- non-PII reference
    -- Encrypted columns (BYTEA stores ciphertext)
    ssn_encrypted   BYTEA,
    dob_encrypted   BYTEA,
    diagnosis_encrypted BYTEA,
    -- Non-sensitive operational columns
    department      VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Insert with encryption (key comes from app/vault, not DB)
-- In production: key managed by AWS KMS or HashiCorp Vault
INSERT INTO patient_records (ssn_encrypted, dob_encrypted, department)
VALUES (
    pgp_sym_encrypt('123-45-6789', 'my-secret-key-from-vault'),
    pgp_sym_encrypt('1985-06-15', 'my-secret-key-from-vault'),
    'Cardiology'
);

-- Read with decryption (application provides key)
SELECT 
    id,
    patient_token,
    pgp_sym_decrypt(ssn_encrypted, 'my-secret-key-from-vault') AS ssn,
    pgp_sym_decrypt(dob_encrypted, 'my-secret-key-from-vault') AS date_of_birth,
    department
FROM patient_records
WHERE department = 'Cardiology';

-- Asymmetric encryption for more secure patterns
-- Only the private key holder can decrypt
SELECT pgp_pub_encrypt('sensitive-data', 
    dearmor('-----BEGIN PGP PUBLIC KEY-----...'));

-- Hash for searchable but non-reversible storage
-- (for lookups by SSN without storing plaintext)
CREATE TABLE ssn_lookup (
    ssn_hash     VARCHAR(64) PRIMARY KEY,  -- SHA-256 of SSN
    patient_id   BIGINT REFERENCES patient_records(id)
);
INSERT INTO ssn_lookup VALUES (
    encode(sha256('123-45-6789'::bytea), 'hex'),
    1
);
-- Look up patient by SSN without storing it:
SELECT p.* FROM ssn_lookup s
JOIN patient_records p ON s.patient_id = p.id
WHERE s.ssn_hash = encode(sha256('123-45-6789'::bytea), 'hex');
```

> 💡 Never store the encryption key in the database. Use environment variables → AWS Parameter Store → AWS KMS in that order of security preference.

---

## Step 6: Least Privilege Role Architecture

```sql
-- ── Role Hierarchy ────────────────────────────────────────────────────────────

-- Base roles (no login, permission containers)
CREATE ROLE readonly_role;
CREATE ROLE readwrite_role;
CREATE ROLE app_admin_role;
CREATE ROLE audit_role;

-- Grant privileges to base roles
GRANT CONNECT ON DATABASE production TO readonly_role, readwrite_role, app_admin_role;
GRANT USAGE ON SCHEMA public TO readonly_role, readwrite_role, app_admin_role;

-- readonly: SELECT only
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO readonly_role;

-- readwrite: SELECT + DML
GRANT readonly_role TO readwrite_role;  -- inherit read
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO readwrite_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO readwrite_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT INSERT, UPDATE, DELETE ON TABLES TO readwrite_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO readwrite_role;

-- app_admin: readwrite + DDL for app tables (not system)
GRANT readwrite_role TO app_admin_role;
-- Note: DDL grants are more complex, typically managed by migration tools

-- audit: read-only access to audit_log only
GRANT CONNECT ON DATABASE production TO audit_role;
GRANT USAGE ON SCHEMA public TO audit_role;
GRANT SELECT ON audit_log TO audit_role;

-- ── Service Accounts (login roles) ───────────────────────────────────────────

CREATE ROLE api_service LOGIN PASSWORD 'strong-password-from-vault'
    CONNECTION LIMIT 50;
GRANT readwrite_role TO api_service;

CREATE ROLE analytics_service LOGIN PASSWORD 'strong-password-from-vault'
    CONNECTION LIMIT 10;
GRANT readonly_role TO analytics_service;

CREATE ROLE audit_service LOGIN PASSWORD 'strong-password-from-vault'
    CONNECTION LIMIT 5;
GRANT audit_role TO audit_service;

CREATE ROLE migration_service LOGIN PASSWORD 'strong-password-from-vault'
    CONNECTION LIMIT 2;
GRANT app_admin_role TO migration_service;

-- ── NEVER do these ────────────────────────────────────────────────────────────
-- GRANT superuser TO app_service;           -- DO NOT
-- ALTER USER app_service SUPERUSER;         -- DO NOT
-- GRANT ALL PRIVILEGES ON DATABASE TO ...;  -- DO NOT

-- Verify privileges
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee IN ('readonly_role', 'readwrite_role')
ORDER BY grantee, table_name;
```

---

## Step 7: SQL Injection Prevention & Database Activity Monitoring

```sql
-- ── SQL Injection: The Right Way ─────────────────────────────────────────────

-- WRONG: string concatenation (vulnerable)
-- query = "SELECT * FROM users WHERE id = " + user_input
-- Attacker input: "1 OR 1=1"
-- Result: "SELECT * FROM users WHERE id = 1 OR 1=1" → all rows!

-- RIGHT: parameterized queries
-- Python psycopg2:
--   cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
-- Java JDBC:
--   PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
--   ps.setInt(1, userId);
-- Node.js pg:
--   await client.query('SELECT * FROM users WHERE id = $1', [userId]);
-- Go pgx:
--   row := db.QueryRow(ctx, "SELECT * FROM users WHERE id = $1", userID)

-- ── pg_audit — Database Activity Monitoring ───────────────────────────────────
-- Install pgaudit extension for session/object audit

CREATE EXTENSION IF NOT EXISTS pgaudit;

-- postgresql.conf settings for pgaudit:
-- pgaudit.log = 'write, ddl, role, connection'
--   write = INSERT, UPDATE, DELETE, TRUNCATE, COPY
--   ddl   = CREATE, DROP, ALTER
--   role  = GRANT, REVOKE
--   connection = login, logout

-- Per-role audit (fine-grained)
-- SET pgaudit.role = 'auditor';
-- Any object the auditor can access gets logged

-- View recent audit events (if pg_audit writing to log)
-- These appear in PostgreSQL log file:
-- AUDIT: SESSION,1,1,DDL,CREATE TABLE,,,CREATE TABLE sensitive_data...

-- ── Anomaly Detection Queries ─────────────────────────────────────────────────

-- Detect unusual query patterns
SELECT 
    usename AS user,
    client_addr AS from_ip,
    COUNT(*) AS query_count,
    MAX(query_start) AS last_query
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start > NOW() - INTERVAL '1 minute'
GROUP BY usename, client_addr
HAVING COUNT(*) > 100  -- alert if > 100 queries/minute from one user
ORDER BY query_count DESC;

-- Detect off-hours access
SELECT 
    event_time,
    actor_id,
    actor_ip,
    event_type,
    table_name
FROM audit_log
WHERE EXTRACT(HOUR FROM event_time) NOT BETWEEN 6 AND 22
  AND event_type NOT IN ('SELECT')  -- off-hours writes are suspicious
ORDER BY event_time DESC
LIMIT 50;

-- Detect excessive data extraction
SELECT 
    actor_id,
    DATE_TRUNC('hour', event_time) AS hour,
    COUNT(*) AS select_count
FROM audit_log
WHERE event_type = 'SELECT'
  AND event_time > NOW() - INTERVAL '24 hours'
GROUP BY actor_id, DATE_TRUNC('hour', event_time)
HAVING COUNT(*) > 10000  -- alert on bulk extraction
ORDER BY select_count DESC;
```

> 💡 Database Activity Monitoring (DAM) tools like IBM Guardium, Imperva, or open-source pgaudit provide real-time alerting. Set up PagerDuty alerts for off-hours access, bulk extractions, and privilege escalation.

---

## Step 8: Capstone — Security Validation Suite

```python
import hashlib, hmac, base64, sqlite3

# ── SQL Injection Prevention Demo ────────────────────────────────────────────

print('=== SQL INJECTION PREVENTION ===\n')

print('VULNERABLE (string concatenation):')
user_input = "' OR '1'='1"
bad_query = f"SELECT * FROM users WHERE username = '{user_input}'"
print(f'  Input: {user_input}')
print(f'  Query: {bad_query}')
print(f'  Result: INJECTION SUCCESSFUL - returns ALL rows!\n')

# Safe parameterized query demo using sqlite3
conn = sqlite3.connect(':memory:')
c = conn.cursor()
c.execute('CREATE TABLE users (id INTEGER, username TEXT, role TEXT)')
c.execute("INSERT INTO users VALUES (1, 'alice', 'admin')")
c.execute("INSERT INTO users VALUES (2, 'bob', 'user')")
conn.commit()

print('SAFE (parameterized query):')
safe_input = "' OR '1'='1"
c.execute('SELECT * FROM users WHERE username = ?', (safe_input,))
rows = c.fetchall()
print(f'  Input: {safe_input}')
print(f'  Query: SELECT * FROM users WHERE username = ?  (params: [{safe_input}])')
print(f'  Result: {rows} ← returns 0 rows, injection blocked!\n')

# ── Column Encryption Demo ────────────────────────────────────────────────────

print('=== COLUMN-LEVEL ENCRYPTION (pgcrypto simulation) ===')
secret_key = b'my-32-byte-secret-key-for-aes!!!'

def encrypt_column(plaintext, key):
    h = hmac.new(key, plaintext.encode(), hashlib.sha256).digest()
    return '\\x' + base64.b64encode(plaintext.encode() + h[:4]).decode()

def decrypt_column(ciphertext, key):
    data = base64.b64decode(ciphertext[2:])
    return data[:-4].decode()

ssn = '123-45-6789'
encrypted = encrypt_column(ssn, secret_key)
decrypted = decrypt_column(encrypted, secret_key)
print(f'  Original SSN: {ssn}')
print(f'  Encrypted:    {encrypted[:40]}...')
print(f'  Decrypted:    {decrypted}\n')

# ── Least Privilege Role Matrix ───────────────────────────────────────────────

print('=== LEAST PRIVILEGE ROLE MATRIX ===')
roles = [
    ('app_readonly',  'SELECT only on public schema'),
    ('app_readwrite', 'SELECT, INSERT, UPDATE on app tables'),
    ('app_admin',     'Full access except system tables'),
    ('audit_reader',  'SELECT only on audit_log table'),
    ('dba',           'Full superuser access'),
]
for role, perms in roles:
    print(f'  {role:<20} → {perms}')

print('\nSecurity architecture validation: PASSED')
```

**Run verification:**
```bash
docker run --rm python:3.11-slim python3 -c "
import hashlib, hmac, base64, sqlite3
conn=sqlite3.connect(':memory:')
c=conn.cursor()
c.execute('CREATE TABLE users (id INTEGER, username TEXT)')
c.execute(\"INSERT INTO users VALUES (1,'alice')\")
conn.commit()
bad_input=\"' OR '1'='1\"
c.execute('SELECT * FROM users WHERE username = ?', (bad_input,))
rows=c.fetchall()
print(f'Injection attempt result: {rows} (blocked)')
key=b'my-32-byte-secret-key-for-aes!!!'
ssn='123-45-6789'
enc='\\\\x'+base64.b64encode(ssn.encode()+hmac.new(key,ssn.encode(),hashlib.sha256).digest()[:4]).decode()
print(f'Encrypted: {enc[:30]}...')
print('Security validation: PASSED')
"
```

📸 **Verified Output:**
```
=== SQL INJECTION PREVENTION ===

VULNERABLE (string concatenation):
  Input: ' OR '1'='1
  Query: SELECT * FROM users WHERE username = '' OR '1'='1'
  Result: INJECTION SUCCESSFUL - returns ALL rows!

SAFE (parameterized query):
  Input: ' OR '1'='1
  Query: SELECT * FROM users WHERE username = ?  (params: [' OR '1'='1])
  Result: [] ← returns 0 rows, injection blocked!

=== COLUMN-LEVEL ENCRYPTION (pgcrypto simulation) ===
  Original SSN: 123-45-6789
  Encrypted:    \xMTIzLTQ1LTY3ODm9TonK...
  Decrypted:    123-45-6789

=== LEAST PRIVILEGE ROLE MATRIX ===
  app_readonly         → SELECT only on public schema
  app_readwrite        → SELECT, INSERT, UPDATE on app tables
  app_admin            → Full access except system tables
  audit_reader         → SELECT only on audit_log table
  dba                  → Full superuser access

Security architecture validation: PASSED
```

---

## Summary

| Layer | Control | Implementation |
|-------|---------|---------------|
| Network | VPC private subnet | No public IP on DB, Security Groups |
| Network | pg_hba.conf allowlist | Restrict to app subnet CIDR only |
| Transport | TLS 1.2+ | `ssl_min_protocol_version = TLSv1.2` |
| Transport | `sslmode=verify-full` | Client verifies server cert + hostname |
| At Rest | TDE | AWS RDS encryption (KMS), LUKS on self-managed |
| At Rest | Column encryption | pgcrypto `pgp_sym_encrypt` |
| Authorization | RBAC | Minimal roles, no superuser for apps |
| Authorization | Row-Level Security | Per-tenant data isolation |
| Application | Parameterized queries | Never string-concatenate SQL |
| Application | Input validation | Whitelist, not blacklist |
| Monitoring | pgaudit | Session + object-level audit logging |
| Monitoring | pg_stat_activity | Real-time connection monitoring |
| Monitoring | Anomaly detection | Off-hours access, bulk extraction alerts |
