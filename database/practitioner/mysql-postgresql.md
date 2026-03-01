# MySQL & PostgreSQL

## MySQL

```bash
# Connect
mysql -u root -p
mysql -u user -p dbname -h hostname

# Database operations
CREATE DATABASE innozverse;
USE innozverse;
SHOW DATABASES;
SHOW TABLES;
DESCRIBE users;
```

```sql
-- Create table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user', 'guest') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- Full-text search
ALTER TABLE products ADD FULLTEXT(name, description);
SELECT * FROM products WHERE MATCH(name, description) AGAINST('Surface Pro' IN BOOLEAN MODE);
```

```bash
# Backup & restore
mysqldump -u root -p dbname > backup.sql
mysqldump -u root -p --all-databases > all_backup.sql
mysql -u root -p dbname < backup.sql
```

## PostgreSQL

```bash
# Connect
psql -U postgres
psql -U user -d dbname -h hostname

# Meta-commands
\l              # List databases
\c dbname       # Connect to database
\dt             # List tables
\d tablename    # Describe table
\du             # List users
\q              # Quit
```

```sql
-- PostgreSQL-specific features
-- UUID primary key
CREATE TABLE products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    metadata JSONB,                        -- Native JSON support
    tags TEXT[],                           -- Array type
    created_at TIMESTAMPTZ DEFAULT NOW()   -- Timezone-aware
);

-- JSON queries
SELECT name, metadata->>'color' as color FROM products
WHERE metadata @> '{"brand": "Microsoft"}';

-- Array operations
SELECT * FROM products WHERE 'gaming' = ANY(tags);

-- Window functions
SELECT name, price,
    RANK() OVER (ORDER BY price DESC) as price_rank,
    AVG(price) OVER () as avg_price
FROM products;
```

```bash
# Backup
pg_dump dbname > backup.sql
pg_dump -Fc dbname > backup.dump    # Custom format (faster)
pg_restore -d dbname backup.dump    # Restore
```
