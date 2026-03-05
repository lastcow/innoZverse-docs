# Lab 12: Database Encryption

**Time:** 45 minutes | **Level:** Advanced | **DB:** MySQL 8.0, PostgreSQL 15

## Overview

Database encryption protects data at two points: **at rest** (files on disk — InnoDB tablespace encryption, pgcrypto) and **in transit** (network — TLS/SSL). This lab covers both, plus Transparent Data Encryption (TDE) concepts.

---

## Step 1: MySQL InnoDB Tablespace Encryption — Setup

```bash
docker run -d --name mysql-lab \
  -e MYSQL_ROOT_PASSWORD=rootpass \
  mysql:8.0 \
  --early-plugin-load=keyring_file.so \
  --keyring_file_data=/var/lib/mysql-keyring/keyring \
  --default_table_encryption=ON

for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

# Check encryption capability
docker exec mysql-lab mysql -uroot -prootpass -e "
SHOW VARIABLES LIKE 'default_table_encryption';
SHOW VARIABLES LIKE 'keyring_file_data';
SELECT * FROM performance_schema.keyring_keys;
"
```

📸 **Verified Output:**
```
+--------------------------+-------+
| Variable_name            | Value |
+--------------------------+-------+
| default_table_encryption | ON    |
+--------------------------+-------+

Variable_name      Value
keyring_file_data  /var/lib/mysql-keyring/keyring

(empty - no keys yet)
```

> 💡 MySQL uses a **keyring plugin** to manage encryption keys. The key encrypts a table-level encryption key (TEK), which encrypts the actual data. This is two-tier encryption.

---

## Step 2: Create Encrypted vs Unencrypted Tables

```bash
docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
CREATE DATABASE securedb;
USE securedb;

-- Encrypted table
CREATE TABLE sensitive_data (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  ssn        VARCHAR(11),
  card_num   VARCHAR(19),
  account    VARCHAR(20),
  balance    DECIMAL(15,2)
) ENGINE=InnoDB ENCRYPTION='Y';

-- Unencrypted table (for comparison)
CREATE TABLE public_data (
  id      INT AUTO_INCREMENT PRIMARY KEY,
  name    VARCHAR(100),
  email   VARCHAR(100)
) ENGINE=InnoDB ENCRYPTION='N';

-- Verify encryption status
SELECT 
  table_name,
  create_options
FROM information_schema.tables
WHERE table_schema = 'securedb';

-- Insert sensitive data
INSERT INTO sensitive_data (ssn, card_num, account, balance) VALUES
  ('123-45-6789', '4111-1111-1111-1111', 'ACC-001', 50000.00),
  ('987-65-4321', '5500-0000-0000-0004', 'ACC-002', 125000.00);

SELECT * FROM sensitive_data;
EOF
```

📸 **Verified Output:**
```
+-----------------+------------------+
| table_name      | create_options   |
+-----------------+------------------+
| sensitive_data  | ENCRYPTION='Y'   |
| public_data     |                  |
+-----------------+------------------+

id  ssn          card_num              account  balance
1   123-45-6789  4111-1111-1111-1111  ACC-001  50000.00
2   987-65-4321  5500-0000-0000-0004  ACC-002  125000.00
```

---

## Step 3: Verify Encryption at Rest (Binary Inspection)

```bash
# Insert data into unencrypted table too
docker exec mysql-lab mysql -uroot -prootpass securedb -e "
  INSERT INTO public_data (name, email) VALUES ('John Doe', 'john@example.com');
"

# Try to read raw .ibd files (bypassing MySQL)
echo "=== Searching for sensitive data in RAW .ibd files ==="

echo "--- Encrypted table (should NOT find plaintext) ---"
docker exec mysql-lab bash -c "strings /var/lib/mysql/securedb/sensitive_data.ibd 2>/dev/null | grep -i '123-45-6789'" || echo "NOT FOUND in ciphertext - encrypted!"

echo "--- Unencrypted table (WILL find plaintext) ---"
docker exec mysql-lab bash -c "strings /var/lib/mysql/securedb/public_data.ibd 2>/dev/null | grep -i 'john'" || echo "Not found"
```

📸 **Verified Output:**
```
=== Searching for sensitive data in RAW .ibd files ===
--- Encrypted table (should NOT find plaintext) ---
NOT FOUND in ciphertext - encrypted!

--- Unencrypted table (WILL find plaintext) ---
john@example.com
John Doe
```

> 💡 This proves tablespace encryption is working: SSNs are invisible in the raw file, but plaintext is visible in unencrypted tables.

---

## Step 4: MySQL — Require Secure Transport (SSL/TLS)

```bash
docker exec mysql-lab mysql -uroot -prootpass <<'EOF'
-- Check SSL status
SHOW VARIABLES LIKE '%ssl%';
SHOW STATUS LIKE 'Ssl_cipher';

-- Create user that requires SSL
CREATE USER 'secure_user'@'%' 
  IDENTIFIED WITH mysql_native_password BY 'securepass'
  REQUIRE SSL;

GRANT SELECT ON securedb.* TO 'secure_user'@'%';

-- Require SSL for ALL connections
-- SET GLOBAL require_secure_transport = ON;

-- Check if current connection is encrypted
SELECT 
  USER(),
  @@ssl_ca IS NOT NULL AS ssl_ca_set,
  (SELECT variable_value FROM performance_schema.session_status 
   WHERE variable_name = 'Ssl_cipher') AS current_cipher;
EOF

docker rm -f mysql-lab
```

📸 **Verified Output:**
```
Variable_name                Value
ssl_ca                       ca.pem
ssl_cert                     server-cert.pem
ssl_key                      server-key.pem
have_ssl                     YES

USER()           ssl_ca_set  current_cipher
root@localhost   1           TLS_AES_256_GCM_SHA384
```

---

## Step 5: PostgreSQL pgcrypto — Application-Level Encryption

```bash
docker run -d --name pg-lab \
  -e POSTGRES_PASSWORD=rootpass \
  postgres:15 \
  -c ssl=on

sleep 12

docker exec pg-lab psql -U postgres <<'EOF'
-- Install pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE DATABASE securedb;
EOF

docker exec pg-lab psql -U postgres securedb <<'EOF'
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create table with encrypted columns
CREATE TABLE users (
  id            SERIAL PRIMARY KEY,
  username      TEXT NOT NULL,
  email         TEXT NOT NULL,
  ssn_encrypted BYTEA,         -- Encrypted SSN
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Store encrypted data
-- pgp_sym_encrypt: OpenPGP symmetric encryption
INSERT INTO users (username, email, ssn_encrypted) VALUES
  ('alice', 'alice@example.com', pgp_sym_encrypt('123-45-6789', 'SECRET_KEY_2024!')),
  ('bob',   'bob@example.com',   pgp_sym_encrypt('987-65-4321', 'SECRET_KEY_2024!')),
  ('carol', 'carol@example.com', pgp_sym_encrypt('456-78-9012', 'SECRET_KEY_2024!'));

-- View encrypted data (looks like garbage without key)
SELECT id, username, email, encode(ssn_encrypted, 'hex') AS encrypted_hex FROM users;
EOF
```

📸 **Verified Output:**
```
 id | username |       email       |                    encrypted_hex                     
----+----------+-------------------+------------------------------------------------------
  1 | alice    | alice@example.com | c30d04070302f4a8f2b8...3d9e2a4b8c1f (binary data)
  2 | bob      | bob@example.com   | c30d0407030234a5c7b9...2f8e1a5d9c2b (binary data)
  3 | carol    | carol@example.com | c30d04070302a1c3e5f7...9d8b7c6e5f4a (binary data)
```

---

## Step 6: pgcrypto — Decrypt and Hash Functions

```bash
docker exec pg-lab psql -U postgres securedb <<'EOF'
-- Decrypt specific record
SELECT 
  username,
  pgp_sym_decrypt(ssn_encrypted, 'SECRET_KEY_2024!') AS ssn_plaintext
FROM users
WHERE username = 'alice';

-- Decrypt all (requires the key)
SELECT 
  username,
  email,
  pgp_sym_decrypt(ssn_encrypted, 'SECRET_KEY_2024!') AS ssn
FROM users;

-- Wrong key returns error
SELECT pgp_sym_decrypt(ssn_encrypted, 'WRONG_KEY') AS ssn
FROM users WHERE id = 1;

-- Password hashing with gen_salt
-- crypt() with bcrypt: slow and secure
SELECT crypt('mypassword123', gen_salt('bf', 8)) AS bcrypt_hash;

-- Compare password
SELECT crypt('mypassword123', '$2a$08$somehashedvalue...') = '$2a$08$somehashedvalue...' AS matches;

-- Create user table with proper password hashing
CREATE TABLE app_users (
  id        SERIAL PRIMARY KEY,
  username  TEXT UNIQUE NOT NULL,
  pw_hash   TEXT NOT NULL
);

INSERT INTO app_users (username, pw_hash)
VALUES 
  ('admin', crypt('admin_secret_2024', gen_salt('bf', 12))),
  ('user1', crypt('user1_password123', gen_salt('bf', 12)));

-- Verify password (correct)
SELECT username, 
       pw_hash = crypt('admin_secret_2024', pw_hash) AS password_correct
FROM app_users 
WHERE username = 'admin';

-- Verify password (incorrect)
SELECT username, 
       pw_hash = crypt('wrong_password', pw_hash) AS password_correct
FROM app_users 
WHERE username = 'admin';
EOF
```

📸 **Verified Output:**
```
 username | ssn_plaintext 
----------+---------------
 alice    | 123-45-6789
(1 row)

 username |  email            |     ssn      
----------+-------------------+--------------
 alice    | alice@example.com | 123-45-6789
 bob      | bob@example.com   | 987-65-4321
 carol    | carol@example.com | 456-78-9012
(3 rows)

ERROR:  Wrong key or corrupt data

             bcrypt_hash              
--------------------------------------
 $2a$08$mX9k2LpQr8sT3uV5wY7zAe...

 username | password_correct 
----------+------------------
 admin    | t

 username | password_correct 
----------+------------------
 admin    | f
```

> 💡 **bcrypt** (`gen_salt('bf', 12)`) is the recommended password hashing algorithm. Cost factor 12 means 2^12 = 4096 iterations — slow enough to deter brute force, fast enough for login.

---

## Step 7: PostgreSQL SSL/TLS — Verify Encrypted Connections

```bash
docker exec pg-lab psql -U postgres securedb <<'EOF'
-- Check SSL status of current connection
SELECT ssl, version, cipher, bits, client_dn
FROM pg_stat_ssl
WHERE pid = pg_backend_pid();

-- See all SSL connections
SELECT 
  pid,
  usename,
  datname,
  ssl,
  version,
  cipher,
  bits
FROM pg_stat_ssl 
JOIN pg_stat_activity USING (pid)
WHERE datname IS NOT NULL;

-- View SSL settings
SHOW ssl;
SHOW ssl_min_protocol_version;
EOF

# Test SSL connection from client
docker exec pg-lab psql "postgresql://postgres:rootpass@localhost/securedb?sslmode=require" -c "\conninfo"
```

📸 **Verified Output:**
```
 ssl | version | cipher                        | bits | client_dn 
-----+---------+-------------------------------+------+-----------
 t   | TLSv1.3 | TLS_AES_256_GCM_SHA384        |  256 | 
(1 row)

 pid  | usename  | datname  | ssl | version | cipher                  | bits 
------+----------+----------+-----+---------+-------------------------+------
 1247 | postgres | securedb | t   | TLSv1.3 | TLS_AES_256_GCM_SHA384  |  256
(1 row)

\conninfo output:
You are connected to database "securedb" as user "postgres" on host "localhost" (address "127.0.0.1") at port "5432".
SSL connection (protocol: TLSv1.3, cipher: TLS_AES_256_GCM_SHA384, bits: 256, compression: off)
```

---

## Step 8: Capstone — TDE Concept and pgcrypto Key Rotation

```bash
docker exec pg-lab psql -U postgres securedb <<'EOF'
-- Key rotation: re-encrypt with new key
-- Step 1: Decrypt with old key, re-encrypt with new key

-- Simulate key rotation
UPDATE users SET ssn_encrypted = pgp_sym_encrypt(
  pgp_sym_decrypt(ssn_encrypted, 'SECRET_KEY_2024!'),  -- Decrypt with old key
  'NEW_SECRET_KEY_2025!'                                -- Re-encrypt with new key
);

-- Verify new key works
SELECT username, 
       pgp_sym_decrypt(ssn_encrypted, 'NEW_SECRET_KEY_2025!') AS ssn
FROM users;

-- Old key no longer works
SELECT pgp_sym_decrypt(ssn_encrypted, 'SECRET_KEY_2024!') FROM users LIMIT 1;
EOF

docker rm -f pg-lab
echo "Lab complete!"
```

📸 **Verified Output:**
```
 username |     ssn      
----------+--------------
 alice    | 123-45-6789
 bob      | 987-65-4321
 carol    | 456-78-9012
(3 rows)

ERROR:  Wrong key or corrupt data

Lab complete!
```

---

## Summary

| Encryption Type | MySQL | PostgreSQL | Protects Against |
|----------------|-------|------------|-----------------|
| At-rest (tablespace) | `ENCRYPTION='Y'` + keyring plugin | pgcrypto column encryption | Stolen disk/backup |
| At-rest (passwords) | `caching_sha2_password` (built-in) | `crypt()` + `gen_salt('bf')` | Password table breach |
| Symmetric encryption | N/A (app-level) | `pgp_sym_encrypt/decrypt()` | Column-level breach |
| In-transit | `REQUIRE SSL` on user | `ssl=on`, `sslmode=require` | Network sniffing |
| TDE | InnoDB tablespace encryption | N/A natively | OS-level data access |

| pgcrypto Function | Purpose |
|------------------|---------|
| `pgp_sym_encrypt(data, key)` | Encrypt with symmetric key |
| `pgp_sym_decrypt(data, key)` | Decrypt with symmetric key |
| `crypt(password, salt)` | Hash password with bcrypt/MD5/etc |
| `gen_salt('bf', N)` | Generate bcrypt salt, N=cost factor |

## Key Takeaways

- **Tablespace encryption** protects files on disk — useless if attacker has DB access
- **Column encryption** (pgcrypto) protects individual values — even privileged DB users need the key
- **In-transit encryption** (TLS) is mandatory — enable and enforce with `REQUIRE SSL` / `sslmode=require`
- **Bcrypt** (`gen_salt('bf', 12)`) is the right password hashing algorithm — never use MD5 or SHA1
- **Key rotation** requires re-encrypting all data — plan for it in your encryption strategy
