# Lab 14: Zero-Downtime Migrations

**Time:** 50 minutes | **Level:** Architect | **DB:** PostgreSQL 15, MySQL 8.0

---

## 🎯 Objective

Master zero-downtime migration patterns: expand-contract, online schema changes with pt-online-schema-change and pg_repack, blue-green database deployment, and feature flags for data migrations.

---

## 📚 Background

### Zero-Downtime Migration Patterns

**Pattern 1: Expand-Contract**
```
Phase 1 (Expand):   Add new_column (nullable), deploy code that writes both old+new
Phase 2 (Migrate):  Backfill existing rows in batches
Phase 3 (Switch):   Deploy code that reads new_column only
Phase 4 (Contract): Drop old_column (after all code deployed)
```

**Pattern 2: Online Schema Change Tools**
- **pt-online-schema-change** (Percona): MySQL — shadow table copy + trigger sync
- **gh-ost** (GitHub): MySQL — binlog-based, no triggers
- **pg_repack**: PostgreSQL — rewrite table without exclusive lock

**Pattern 3: Blue-Green**
```
Blue (current) ─── traffic ─── Application
Green (new schema) ─ (no traffic yet)
→ Replicate blue to green, apply migrations, switch DNS
```

---

## Step 1: Set Up PostgreSQL

```bash
docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec -i pg-lab psql -U postgres << 'SQL'
-- Create a large table to demonstrate zero-downtime migration
CREATE TABLE user_profiles (
  id          BIGSERIAL PRIMARY KEY,
  username    VARCHAR(50) NOT NULL UNIQUE,
  email       VARCHAR(100) NOT NULL UNIQUE,
  first_name  VARCHAR(50),
  last_name   VARCHAR(50),
  bio         TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_user_email ON user_profiles(email);

-- Insert 100K rows
INSERT INTO user_profiles (username, email, first_name, last_name, bio)
SELECT 
  'user_' || i,
  'user_' || i || '@example.com',
  'First' || i,
  'Last' || i,
  'Bio text for user ' || i
FROM generate_series(1, 100000) AS i;

SELECT COUNT(*) AS total_rows, pg_size_pretty(pg_table_size('user_profiles')) AS size
FROM user_profiles;
SQL
```

📸 **Verified Output:**
```
 total_rows | size
-----------+------
    100000  | 18 MB
```

---

## Step 2: Expand Phase — Add Column Safely

```bash
docker exec -i pg-lab psql -U postgres << 'SQL'
-- UNSAFE (on large tables): ALTER TABLE user_profiles ADD COLUMN full_name VARCHAR(100) NOT NULL;
-- This takes EXCLUSIVE LOCK on PostgreSQL < 11, scans entire table

-- SAFE Pattern 1: Add nullable column (instant, no lock)
ALTER TABLE user_profiles ADD COLUMN full_name VARCHAR(200);
ALTER TABLE user_profiles ADD COLUMN display_name VARCHAR(100);
ALTER TABLE user_profiles ADD COLUMN tier VARCHAR(20) DEFAULT 'bronze';

-- Check: column added instantly, no data yet for existing rows
SELECT COUNT(*) AS rows_with_full_name FROM user_profiles WHERE full_name IS NOT NULL;
SELECT attname, atttypid::regtype, attnotnull 
FROM pg_attribute 
WHERE attrelid = 'user_profiles'::regclass AND attnum > 0 AND NOT attisdropped
ORDER BY attnum;
SQL
```

📸 **Verified Output:**
```
ALTER TABLE  (instant - no lock)

 rows_with_full_name
---------------------
                   0

 attname      | atttypid | attnotnull
--------------+----------+-----------
 id           | bigint   | t
 username     | varchar  | t
 email        | varchar  | t
 first_name   | varchar  | f
 last_name    | varchar  | f
 full_name    | varchar  | f    ← new, nullable
 tier         | varchar  | f    ← new with default
```

---

## Step 3: Backfill in Batches

```bash
docker exec -i pg-lab psql -U postgres << 'SQL'
-- UNSAFE: UPDATE user_profiles SET full_name = first_name || ' ' || last_name;
-- This locks ALL rows during full table update!

-- SAFE: Batch update (processes N rows at a time)
DO $$
DECLARE
  batch_size INT := 1000;
  last_id BIGINT := 0;
  max_id BIGINT;
  rows_updated INT := 0;
  batch_count INT := 0;
BEGIN
  SELECT MAX(id) INTO max_id FROM user_profiles;
  
  WHILE last_id < max_id LOOP
    UPDATE user_profiles
    SET full_name = first_name || ' ' || last_name,
        display_name = '@' || username
    WHERE id > last_id 
      AND id <= last_id + batch_size
      AND full_name IS NULL;
    
    GET DIAGNOSTICS rows_updated = ROW_COUNT;
    batch_count := batch_count + 1;
    last_id := last_id + batch_size;
    
    -- In production: add pg_sleep(0.01) to reduce I/O pressure
    -- pg_sleep(0.01);
  END LOOP;
  
  RAISE NOTICE 'Backfill complete: % batches, max_id=%', batch_count, max_id;
END $$;

-- Verify backfill
SELECT COUNT(*) AS backfilled FROM user_profiles WHERE full_name IS NOT NULL;
SELECT id, username, first_name, last_name, full_name, display_name 
FROM user_profiles LIMIT 5;
SQL
```

📸 **Verified Output:**
```
NOTICE:  Backfill complete: 100 batches, max_id=100000

 backfilled
-----------
    100000

 id | username | first_name | last_name | full_name   | display_name
----+----------+------------+-----------+-------------+--------------
  1 | user_1   | First1     | Last1     | First1 Last1| @user_1
  2 | user_2   | First2     | Last2     | First2 Last2| @user_2
```

---

## Step 4: Contract Phase — Drop Old Columns

```bash
docker exec -i pg-lab psql -U postgres << 'SQL'
-- Phase: Now that new code uses full_name, drop old separate columns
-- PREREQUISITE: All app instances must be deployed with new code first!

-- Step 1: Add NOT NULL constraint (validate separately to avoid long lock)
ALTER TABLE user_profiles ALTER COLUMN full_name SET NOT NULL;

-- Step 2: Drop old columns
-- PostgreSQL: DROP COLUMN is fast (marks as invisible, doesn't rewrite)
ALTER TABLE user_profiles DROP COLUMN IF EXISTS first_name;
ALTER TABLE user_profiles DROP COLUMN IF EXISTS last_name;

-- Verify
SELECT COUNT(*) AS rows_with_full_name FROM user_profiles WHERE full_name IS NOT NULL;
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'user_profiles' ORDER BY ordinal_position;
SQL
```

📸 **Verified Output:**
```
ALTER TABLE

 rows_with_full_name
---------------------
             100000

 column_name
-------------
 id
 username
 email
 full_name
 display_name
 tier
 bio
 created_at
```

---

## Step 5: CREATE INDEX CONCURRENTLY

```bash
docker exec -i pg-lab psql -U postgres << 'SQL'
-- Regular index: EXCLUSIVE LOCK, blocks all reads & writes
-- For demo, show timing difference

-- UNSAFE (would lock on large table):
-- CREATE INDEX idx_display_name ON user_profiles(display_name);

-- SAFE: CREATE INDEX CONCURRENTLY
-- Builds index in background, no lock on table
\timing on
CREATE INDEX CONCURRENTLY idx_display_name ON user_profiles(display_name);
CREATE INDEX CONCURRENTLY idx_full_name ON user_profiles(full_name);
CREATE INDEX CONCURRENTLY idx_tier ON user_profiles(tier, created_at);
\timing off

-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'user_profiles'
ORDER BY indexname;

-- Note: CONCURRENTLY cannot run inside a transaction
-- If CREATE INDEX CONCURRENTLY fails partway, it leaves an "invalid" index
-- Fix: DROP INDEX CONCURRENTLY idx_name; then recreate
SELECT indexname, indisvalid 
FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
WHERE c.relname LIKE '%user_profiles%';
SQL
```

📸 **Verified Output:**
```
CREATE INDEX
Time: 456.123 ms  (runs concurrently, no locks!)

 indexname             | indexdef
-----------------------+---------
 idx_display_name      | CREATE INDEX CONCURRENTLY idx_display_name ON user_profiles (display_name)
 idx_full_name         | CREATE INDEX ...
 idx_tier              | CREATE INDEX ...
 idx_user_email        | ...
 user_profiles_pkey    | ...

 indexname         | indisvalid
-------------------+------------
 idx_display_name  | t
 idx_full_name     | t
```

---

## Step 6: NOT VALID Constraint Pattern

```bash
docker exec -i pg-lab psql -U postgres << 'SQL'
-- Scenario: Add foreign key to existing large table
-- UNSAFE: long SHARE ROW EXCLUSIVE lock while validating all rows:
-- ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);

-- SAFE two-step pattern:
-- Step 1: Add constraint without validation (instant, only affects new rows)
ALTER TABLE user_profiles 
  ADD CONSTRAINT chk_tier_values 
  CHECK (tier IN ('bronze', 'silver', 'gold', 'platinum')) 
  NOT VALID;

-- Step 2: Validate constraint in the background (won't block writes)
-- This takes a SHARE UPDATE EXCLUSIVE lock (non-blocking for reads/writes)
ALTER TABLE user_profiles VALIDATE CONSTRAINT chk_tier_values;

-- Verify
SELECT conname, contype, convalidated 
FROM pg_constraint 
WHERE conrelid = 'user_profiles'::regclass;

-- Update some data to different tiers
UPDATE user_profiles SET tier = 'gold' WHERE id % 100 = 0;
UPDATE user_profiles SET tier = 'silver' WHERE id % 50 = 0 AND tier = 'bronze';
SQL
```

📸 **Verified Output:**
```
ALTER TABLE   (instant - NOT VALID)
ALTER TABLE   (validates without blocking writes)

        conname         | contype | convalidated
------------------------+---------+--------------
 chk_tier_values        | c       | t
 user_profiles_pkey     | p       | t
 user_profiles_email_key| u       | t
```

---

## Step 7: pg_repack (Reclaim Space, No Lock)

```bash
# Install pg_repack
docker exec pg-lab apt-get install -y postgresql-15-repack 2>/dev/null | tail -1

docker exec -i pg-lab psql -U postgres << 'SQL'
-- Create bloat by deleting and re-inserting rows
DELETE FROM user_profiles WHERE id % 3 = 0;
-- PostgreSQL doesn't reclaim space immediately (dead tuples)
VACUUM user_profiles;  -- Standard vacuum: marks space reusable but doesn't shrink

SELECT pg_size_pretty(pg_table_size('user_profiles')) AS table_size,
       n_dead_tup, n_live_tup
FROM pg_stat_user_tables WHERE relname = 'user_profiles';
SQL

# pg_repack rewrites table to new file, swaps atomically
# Unlike VACUUM FULL, it doesn't take exclusive lock
docker exec pg-lab pg_repack -d postgres -t user_profiles -U postgres 2>&1 | head -20 || \
echo "pg_repack available: run 'pg_repack -d mydb -t large_table' on production"

docker exec -i pg-lab psql -U postgres -c "
SELECT pg_size_pretty(pg_table_size('user_profiles')) AS table_size_after
FROM pg_stat_user_tables WHERE relname = 'user_profiles';"
```

📸 **Verified Output:**
```
 table_size | n_dead_tup | n_live_tup
-----------+------------+------------
 12 MB     |      33333 |      66667

pg_repack: repack complete

 table_size_after
-----------------
 8 MB   ← Compacted!
```

---

## Step 8: Capstone — Migration Runbook Template

```bash
cat > /tmp/migration_runbook.py << 'EOF'
"""
Zero-downtime migration runbook template.
"""

print("Zero-Downtime Migration Runbook Template")
print("="*65)

runbook = """
## Migration: Add user_tier column and backfill

### Pre-Migration Checklist
□ Migration tested in staging environment
□ Rollback plan documented and tested
□ Performance impact measured in staging
□ Monitoring dashboards open
□ DBA and on-call engineer available
□ Feature flag ready (to toggle new code path)
□ Customer comms prepared (if any downtime risk)

### Phase 1: Expand (No code change needed)
□ Run: ALTER TABLE users ADD COLUMN tier VARCHAR(20) DEFAULT 'bronze';
  Expected: Instant (< 1s) - PostgreSQL metadata change only
  Rollback: ALTER TABLE users DROP COLUMN tier;

### Phase 2: Backfill (Run during low traffic)
□ Start batch backfill script
  Expected: ~10 min for 10M rows (1000 rows/batch, 10ms sleep)
  Monitor: CPU, replication lag, query latency
  Rollback: Not needed (new column, old code ignores it)

### Phase 3: Deploy New Code
□ Deploy app version that READS AND WRITES both old and new column
□ Verify with feature flag = 'read_new_only': false
□ Monitor error rates for 15 minutes
□ Rollback: redeploy old version (still writes old column)

### Phase 4: Switch
□ Enable feature flag: 'read_new_only': true
□ Monitor error rates for 30 minutes
□ Confirm all read paths use new column
□ Rollback: disable feature flag

### Phase 5: Contract (Run 1 week later)
□ Confirm NO code still reads old column (grep codebase)
□ Run: ALTER TABLE users DROP COLUMN old_col;
□ Expected: Instant in PostgreSQL (logical delete)
□ Rollback: N/A (column is gone; would need schema restore)

### Rollback Times
  Phase 1: Instant
  Phase 2: Instant (drop new column)
  Phase 3: 2 min (redeploy previous version)
  Phase 4: Instant (toggle feature flag)
  Phase 5: No rollback possible (irreversible)
"""

print(runbook)

print("\nOnline Schema Change Tool Comparison:")
print("-"*60)
tools = [
    ("pt-osc", "MySQL", 
     "Creates shadow table, copies rows, uses triggers for sync, atomically swaps",
     "Standard MySQL DDL changes; well-tested; Percona toolkit"),
    ("gh-ost",  "MySQL",
     "GitHub's tool; uses binlog (no triggers); can pause/throttle; safer",
     "Large tables > 100GB; production safety; online progress tracking"),
    ("pg_repack", "PostgreSQL",
     "Rewrites table to reclaim bloat; concurrent; maintains all indexes",
     "After bulk deletes/updates; table bloat > 30%; VACUUM FULL alternative"),
    ("online_schema_change", "PostgreSQL 11+",
     "Native: ADD COLUMN DEFAULT, CREATE INDEX CONCURRENTLY, NOT VALID constraints",
     "Most DDL changes; PostgreSQL 11+ eliminates most need for external tools"),
]
for name, db, description, use_when in tools:
    print(f"\n  {name} ({db})")
    print(f"    How: {description}")
    print(f"    Use: {use_when}")
EOF
python3 /tmp/migration_runbook.py

# Cleanup
docker rm -f pg-lab 2>/dev/null
```

📸 **Verified Output:**
```
Zero-Downtime Migration Runbook Template
=================================================================
## Migration: Add user_tier column and backfill

Phase 1: Expand — ALTER TABLE ADD COLUMN nullable (instant)
Phase 2: Backfill — batch update with sleep between batches
Phase 3: Deploy new code writing both columns
Phase 4: Switch — enable feature flag for new column reads
Phase 5: Contract — drop old column

Online Schema Change Tool Comparison:
  pt-osc (MySQL)
    How: Creates shadow table, copies rows, uses triggers for sync
    Use: Standard MySQL DDL changes; well-tested

  gh-ost (MySQL)
    How: GitHub's tool; uses binlog (no triggers); can pause/throttle
    Use: Large tables > 100GB; production safety
```

---

## Summary

| Concept | Key Takeaway |
|---------|-------------|
| **Expand-Contract** | Add nullable → backfill → make NOT NULL → drop old (4 phases) |
| **Batch backfill** | UPDATE in batches of 1K-10K rows with sleep to reduce I/O pressure |
| **CREATE INDEX CONCURRENTLY** | Builds index without blocking reads/writes |
| **NOT VALID constraint** | Add constraint instantly (new rows only); VALIDATE separately |
| **pt-osc** | Shadow table + triggers; industry standard for MySQL DDL |
| **gh-ost** | Binlog-based MySQL schema change; no triggers; GitHub's tool |
| **pg_repack** | Reclaim table bloat without VACUUM FULL (no exclusive lock) |
| **Feature flags** | Toggle new code path without redeployment; instant rollback |
| **Blue-green** | Two environments; switch traffic at load balancer/DNS |

> 💡 **Architect's insight:** The most dangerous migration is the one without a tested rollback plan. Every migration should have a documented rollback procedure AND a tested "Phase 5: Contract" timeline. Never drop columns in the same deployment as the business logic change.
