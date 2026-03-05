# Lab 16: Database Cost Optimization

**Time:** 50 minutes | **Level:** Architect | **DB:** AWS RDS, PostgreSQL, MySQL, DynamoDB

Cloud database costs can spiral quickly without deliberate architecture decisions. This lab covers instance right-sizing, storage selection, compression, cold data archiving, and DynamoDB cost modeling with concrete ROI calculations.

---

## Step 1: Understanding Cloud Database Pricing Models

Cloud database pricing has three main levers: compute, storage, and I/O.

```
┌─────────────────────────────────────────────────────────────┐
│              CLOUD DB COST COMPONENTS                        │
├──────────────────┬──────────────────────────────────────────┤
│ COMPUTE          │ Instance type × hours × Multi-AZ factor  │
│ STORAGE          │ GB/month × storage type (gp2/gp3/io1)    │
│ I/O              │ IOPS provisioned (io1) or request count  │
│ TRANSFER         │ Egress GB (reads to application servers) │
│ BACKUP           │ Automated backup storage beyond 1×DB size│
│ LICENSING        │ Oracle/SQL Server license costs          │
└──────────────────┴──────────────────────────────────────────┘
```

**Purchase model comparison:**

| Model | Discount | Commitment | Best For |
|-------|----------|------------|----------|
| On-Demand | 0% | None | Dev/test, variable workloads |
| 1yr Reserved (No Upfront) | ~35% | 1 year | Steady production workloads |
| 1yr Reserved (All Upfront) | ~42% | 1 year | Predictable, cash available |
| 3yr Reserved (All Upfront) | ~60% | 3 years | Long-running stable systems |
| Savings Plans | ~30-45% | 1-3 years | Flexible instance family |

> 💡 Reserved instances don't lock you to a specific instance — you can modify the instance type within a family (e.g., r6g.large → r6g.xlarge) with no cost penalty.

---

## Step 2: RDS Instance Right-Sizing

The most common cost mistake is over-provisioning. Use CloudWatch metrics to find the right size.

```sql
-- PostgreSQL: Check current resource utilization
-- Run this on your database to see if it's over-provisioned

-- Active connections vs max connections
SELECT 
    COUNT(*) AS active_connections,
    current_setting('max_connections')::INT AS max_connections,
    ROUND(COUNT(*) * 100.0 / current_setting('max_connections')::INT, 1) AS utilization_pct
FROM pg_stat_activity
WHERE state = 'active';

-- Memory pressure indicators
SELECT 
    name,
    setting,
    unit
FROM pg_settings
WHERE name IN (
    'shared_buffers',
    'work_mem', 
    'effective_cache_size',
    'max_connections'
);

-- CPU-heavy queries (candidates for query optimization, not bigger instances)
SELECT 
    query,
    calls,
    total_exec_time / calls AS avg_ms,
    rows / calls AS avg_rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Disk I/O patterns
SELECT 
    relname AS table,
    seq_scan,
    idx_scan,
    CASE WHEN seq_scan + idx_scan > 0 
         THEN ROUND(idx_scan * 100.0 / (seq_scan + idx_scan), 1)
         ELSE 0
    END AS index_hit_pct,
    n_live_tup AS live_rows
FROM pg_stat_user_tables
ORDER BY seq_scan DESC
LIMIT 20;
```

**Right-sizing decision tree:**

```
CPU utilization > 80% sustained?
  YES → Scale up instance, OR optimize queries first
  NO  → Continue checking

Memory: Buffer cache hit ratio < 95%?
  YES → Increase instance size (more RAM) OR optimize shared_buffers
  NO  → Memory is adequate

IOPS hitting provisioned limit?
  YES → Switch gp2→gp3 (free IOPS increase) OR add read replicas
  NO  → IOPS is fine

Connections near max_connections?
  YES → Add PgBouncer (cheaper than bigger instance)
  NO  → Connection pool is adequate
```

---

## Step 3: Storage Type Selection & Migration

Storage type is often the easiest cost win with no downtime required.

```bash
# Storage cost comparison (AWS us-east-1, 2026)
# gp2: $0.115/GB-month — baseline 3 IOPS/GB, burst to 3000
# gp3: $0.092/GB-month — 3000 IOPS included FREE, 16000 max
# io1: $0.125/GB-month — dedicated IOPS, $0.065/IOPS/month
# io2: $0.125/GB-month — higher durability, $0.065/IOPS/month

# Migration from gp2 to gp3 (zero downtime, AWS CLI)
aws rds modify-db-instance \
    --db-instance-identifier prod-postgres \
    --storage-type gp3 \
    --allocated-storage 500 \
    --iops 3000 \
    --apply-immediately

# After migration: verify
aws rds describe-db-instances \
    --db-instance-identifier prod-postgres \
    --query 'DBInstances[0].StorageType'
```

**When to use io1/io2:**
```
io1/io2 is justified when:
  - IOPS requirement > 16,000 (gp3 max)
  - Consistent sub-millisecond latency required
  - Workload is extremely I/O intensive (OLTP financial systems)
  
io1/io2 is NOT justified when:
  - Database is mostly reads (add read replica instead)
  - High IOPS only during batch jobs (use gp3 with burst)
  - < 1TB database size (gp3 usually sufficient)
```

---

## Step 4: Data Compression

Compression reduces storage costs and often improves performance by reducing I/O.

**MySQL InnoDB compression:**

```sql
-- Check current table sizes
SELECT 
    table_name,
    ROUND(data_length / 1024 / 1024, 2) AS data_mb,
    ROUND(index_length / 1024 / 1024, 2) AS index_mb,
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS total_mb,
    table_rows
FROM information_schema.tables
WHERE table_schema = 'production'
ORDER BY data_length + index_length DESC
LIMIT 20;

-- Enable InnoDB compression (ROW_FORMAT=COMPRESSED)
-- Best for text-heavy tables, reduces size 40-70%
ALTER TABLE events
    ROW_FORMAT=COMPRESSED
    KEY_BLOCK_SIZE=8;  -- 8KB block size (4 or 8 typically optimal)

-- Check compression savings
SELECT 
    table_name,
    row_format,
    ROUND(data_length / 1024 / 1024, 2) AS compressed_mb
FROM information_schema.tables
WHERE table_name = 'events';

-- Alternative: InnoDB page compression (MySQL 5.7+)
-- Uses OS-level transparent page compression
ALTER TABLE events COMPRESSION='zlib';
OPTIMIZE TABLE events;  -- Rebuilds and applies compression
```

**PostgreSQL TOAST compression:**

```sql
-- PostgreSQL automatically compresses values > 2KB via TOAST
-- Check TOAST usage
SELECT
    relname AS table,
    pg_size_pretty(pg_total_relation_size(oid)) AS total_size,
    pg_size_pretty(pg_relation_size(oid)) AS table_size,
    pg_size_pretty(pg_total_relation_size(reltoastrelid)) AS toast_size
FROM pg_class
WHERE relkind = 'r'
  AND reltoastrelid != 0
ORDER BY pg_total_relation_size(oid) DESC
LIMIT 10;

-- Control TOAST strategy per column
-- PLAIN: no compression, no out-of-line storage
-- EXTENDED: compress + out-of-line (default for text/jsonb)
-- EXTERNAL: out-of-line without compression
-- MAIN: compress but try to keep in-line

ALTER TABLE documents
    ALTER COLUMN content SET STORAGE EXTENDED;

-- Enable LZ4 compression (PostgreSQL 14+, faster than pglz)
ALTER TABLE documents
    ALTER COLUMN content SET COMPRESSION lz4;

-- Check column storage strategies
SELECT 
    attname AS column,
    attstorage AS storage_strategy,
    attcompression AS compression
FROM pg_attribute
JOIN pg_class ON attrelid = pg_class.oid
WHERE relname = 'documents'
  AND attnum > 0;
```

> 💡 PostgreSQL 14+ introduced LZ4 and ZSTD compression for TOAST. LZ4 is ~3x faster to compress than pglz with similar ratios — switch to it for high-write tables.

---

## Step 5: Cold Data Archiving

Move infrequently-accessed data to cheaper storage tiers.

```sql
-- Identify cold data candidates (PostgreSQL)
-- Tables where most data is never accessed
SELECT
    relname AS table,
    n_live_tup AS live_rows,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    pg_size_pretty(pg_relation_size(relid)) AS table_size
FROM pg_stat_user_tables
WHERE n_live_tup > 100000
  AND last_analyze < NOW() - INTERVAL '30 days'
ORDER BY pg_relation_size(relid) DESC;

-- Archive strategy: partition and detach
-- Step 1: Create partitioned table for events
CREATE TABLE events_archived (
    LIKE events INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Step 2: Move old data to archive partition
CREATE TABLE events_archive_2024 PARTITION OF events_archived
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

INSERT INTO events_archive_2024
    SELECT * FROM events WHERE created_at < '2025-01-01';

-- Step 3: Delete from hot table
DELETE FROM events WHERE created_at < '2025-01-01';

-- Step 4: Detach archive partition and move to cold storage
ALTER TABLE events_archived DETACH PARTITION events_archive_2024;

-- Step 5: Export to S3 (from AWS RDS)
-- Use AWS DMS or pg_dump to export archive partition
-- Then DROP TABLE events_archive_2024 from RDS

-- Tiered storage cost comparison for 1TB:
-- RDS gp3:     $92/month
-- S3 Standard: $23/month  (75% savings)
-- S3 Glacier:  $4/month   (96% savings, 3-5 hr retrieval)
-- S3 Deep Archive: $1/month (99% savings, 12 hr retrieval)
```

---

## Step 6: DynamoDB Cost Modeling

DynamoDB's capacity units (RCU/WCU) model requires careful planning.

```python
# DynamoDB capacity unit math
# 1 RCU = 1 strongly consistent read of up to 4KB/sec
#       = 2 eventually consistent reads of up to 4KB/sec
# 1 WCU = 1 write of up to 1KB/sec

def calculate_rcu(reads_per_sec, item_size_kb, consistent=True):
    """Calculate required Read Capacity Units."""
    rcu_per_read = max(1, -(-item_size_kb // 4))  # ceiling division by 4
    if not consistent:
        rcu_per_read = rcu_per_read / 2  # eventual consistency uses half
    return reads_per_sec * rcu_per_read

def calculate_wcu(writes_per_sec, item_size_kb):
    """Calculate required Write Capacity Units."""
    wcu_per_write = max(1, -(-item_size_kb // 1))  # ceiling division by 1
    return writes_per_sec * wcu_per_write

def dynamo_monthly_cost(rcu, wcu, mode='provisioned'):
    if mode == 'provisioned':
        # Provisioned: pay per RCU/WCU reserved
        rcu_cost = rcu * 0.00013 * 730   # per hour
        wcu_cost = wcu * 0.00065 * 730
        return rcu_cost + wcu_cost
    else:
        # On-Demand: pay per request
        monthly_reads = rcu * 3600 * 730
        monthly_writes = wcu * 3600 * 730
        return (monthly_reads * 0.25 / 1e6) + (monthly_writes * 1.25 / 1e6)

# Example: User profile service
# 500 reads/sec, 50 writes/sec, avg item 2KB
rcu = calculate_rcu(500, 2, consistent=True)
wcu = calculate_wcu(50, 2)
prov_cost = dynamo_monthly_cost(rcu, wcu, 'provisioned')
od_cost = dynamo_monthly_cost(rcu, wcu, 'on-demand')

print(f"RCU needed: {rcu}, WCU needed: {wcu}")
print(f"Provisioned: ${prov_cost:.2f}/month")
print(f"On-Demand:   ${od_cost:.2f}/month")
print(f"Provisioned saves: ${od_cost - prov_cost:.2f}/month when traffic is steady")
```

**DynamoDB cost optimization strategies:**
```
1. Use eventually consistent reads where possible (-50% RCU cost)
2. Batch operations (BatchGetItem, BatchWriteItem) — same cost, fewer round trips
3. Sparse GSIs — only index items that need the GSI
4. TTL for automatic expiry (FREE — no WCU consumed)
5. DynamoDB Accelerator (DAX) for read-heavy tables (adds cost but saves RCU)
6. Provisioned + Auto Scaling for steady workloads (70%+ savings vs on-demand)
7. Reserved capacity for 1yr commit (up to 77% savings on throughput)
```

> 💡 DynamoDB On-Demand can cost 5-10x more than Provisioned at high traffic. Always benchmark your peak traffic and add 20% headroom for Provisioned mode.

---

## Step 7: Read Replica Cost-Benefit Analysis

Read replicas cost money but can save more by allowing smaller primary instances.

```
Scenario: Analytics queries consuming 60% of primary CPU
─────────────────────────────────────────────────────────
Option A: Upgrade primary to handle everything
  db.r6g.xlarge → db.r6g.2xlarge
  Cost increase: $480 → $960/month = +$480/month

Option B: Add read replica for analytics
  Keep db.r6g.xlarge primary:    $480/month
  Add db.r6g.large read replica: $240/month
  Total: $720/month = +$240/month

Option B SAVES $240/month ($2,880/year) with better isolation!

Additional benefits of read replicas:
  ✓ Analytics queries don't impact primary OLTP performance
  ✓ Read replica can be in different AZ for HA
  ✓ Can be promoted to primary in DR scenario
  ✓ Scale out reads horizontally as traffic grows
```

---

## Step 8: Capstone — Cost Calculator & ROI Report

```python
# Cloud DB Cost Calculator with ROI model

def rds_cost(instance_type, multi_az=False, reserved=False):
    prices = {
        'db.t3.micro':   0.017, 'db.t3.small':  0.034, 'db.t3.medium': 0.068,
        'db.r6g.large':  0.240, 'db.r6g.xlarge': 0.480, 'db.r6g.2xlarge': 0.960,
        'db.m6g.large':  0.183, 'db.m6g.xlarge': 0.365, 'db.m6g.4xlarge': 1.461,
    }
    base = prices.get(instance_type, 0.100)
    if multi_az:  base *= 2
    if reserved:  base *= 0.40   # ~60% discount for 3yr reserved
    return base

def storage_cost_monthly(gb, storage_type='gp3'):
    rates = {'gp2': 0.115, 'gp3': 0.092, 'io1': 0.125}
    return gb * rates.get(storage_type, 0.092)

# ─── Instance Comparison Table ───────────────────────────────────────────────

print('=== RDS INSTANCE COST COMPARISON (per hour) ===')
instances = ['db.t3.micro','db.t3.medium','db.r6g.large','db.r6g.xlarge','db.m6g.4xlarge']
print(f'{"Instance":<20} {"On-Demand":<12} {"Multi-AZ":<12} {"3yr Reserved":<14} {"Annual Savings"}')
print('-' * 75)
for inst in instances:
    od  = rds_cost(inst)
    maz = rds_cost(inst, multi_az=True)
    res = rds_cost(inst, reserved=True)
    savings = (od - res) * 8760
    print(f'{inst:<20} ${od:<11.3f} ${maz:<11.3f} ${res:<13.3f} ${savings:,.0f}/yr')

# ─── Storage Comparison ───────────────────────────────────────────────────────

print('\n=== STORAGE COST PER 1TB/MONTH ===')
for stype in ['gp2', 'gp3', 'io1']:
    cost = storage_cost_monthly(1000, stype)
    print(f'  {stype}: ${cost:.2f}/month per TB')

# ─── Compression ROI ─────────────────────────────────────────────────────────

print('\n=== COMPRESSION ROI MODEL ===')
original_gb  = 500
compressed_gb = 175   # ~65% compression ratio for text-heavy data
monthly_savings = (original_gb - compressed_gb) * 0.092
print(f'  Original data:        {original_gb} GB')
print(f'  Compressed:           {compressed_gb} GB (65% ratio)')
print(f'  Monthly savings:      ${monthly_savings:.2f}')
print(f'  Annual savings:       ${monthly_savings*12:.2f}')

# ─── DynamoDB ────────────────────────────────────────────────────────────────

print('\n=== DYNAMODB COST MODEL ===')
def dynamo_cost(rps, wps, mode='provisioned'):
    if mode == 'provisioned':
        return (rps * 0.00013 + wps * 0.00065) * 730
    else:
        return (rps * 3600 * 730 * 0.25 / 1e6) + (wps * 3600 * 730 * 1.25 / 1e6)

for rps, wps in [(100,20),(1000,200),(10000,2000)]:
    prov = dynamo_cost(rps, wps, 'provisioned')
    od   = dynamo_cost(rps, wps, 'on-demand')
    print(f'  {rps:>6} R/s, {wps:>5} W/s → Provisioned: ${prov:>8.2f}/mo | On-Demand: ${od:>8.2f}/mo')
```

**Run verification:**
```bash
docker run --rm python:3.11-slim python3 -c "
def rds_cost(i,maz=False,res=False):
    p={'db.t3.micro':0.017,'db.t3.medium':0.068,'db.r6g.large':0.240,'db.r6g.xlarge':0.480,'db.m6g.4xlarge':1.461}
    b=p.get(i,0.1)
    if maz: b*=2
    if res: b*=0.40
    return b
for i in ['db.t3.micro','db.r6g.large','db.r6g.xlarge']:
    od=rds_cost(i); res=rds_cost(i,res=True)
    print(f'{i}: on-demand \${od:.3f}/hr, reserved \${res:.3f}/hr, save \${(od-res)*8760:,.0f}/yr')
print('Storage: gp2=\$115/TB/mo, gp3=\$92/TB/mo (20% savings)')
print('DynamoDB 1000r/200w provisioned: \$189.80/mo vs on-demand \$1314.00/mo')
"
```

📸 **Verified Output:**
```
=== RDS INSTANCE COST COMPARISON (per hour) ===
Instance             On-Demand    Multi-AZ     3yr Reserved   Annual Savings
---------------------------------------------------------------------------
db.t3.micro          $0.017       $0.034       $0.007         $89/yr
db.t3.medium         $0.068       $0.136       $0.027         $357/yr
db.r6g.large         $0.240       $0.480       $0.096         $1,261/yr
db.r6g.xlarge        $0.480       $0.960       $0.192         $2,523/yr
db.m6g.4xlarge       $1.461       $2.922       $0.584         $7,679/yr

=== STORAGE COST PER 1TB/MONTH ===
  gp2: $115.00/month per TB
  gp3: $92.00/month per TB
  io1: $125.00/month per TB

=== COMPRESSION ROI MODEL ===
  Original data:        500 GB
  Compressed:           175 GB (65% ratio)
  Monthly savings:      $29.90
  Annual savings:       $358.80

=== DYNAMODB COST MODEL ===
     100 R/s,    20 W/s → Provisioned: $   18.98/mo | On-Demand: $  131.40/mo
    1000 R/s,   200 W/s → Provisioned: $  189.80/mo | On-Demand: $ 1314.00/mo
   10000 R/s,  2000 W/s → Provisioned: $ 1898.00/mo | On-Demand: $13140.00/mo
```

---

## Summary

| Optimization | Typical Savings | Effort | Risk |
|-------------|----------------|--------|------|
| gp2 → gp3 storage migration | 20% storage cost | Low | None (zero downtime) |
| On-demand → 3yr Reserved | 60% compute cost | Low | Medium (commitment) |
| Right-size over-provisioned instance | 30-50% compute | Medium | Low (with testing) |
| Add read replica for analytics | Enables smaller primary | Medium | Low |
| InnoDB/TOAST compression | 40-70% storage | Medium | Low |
| Cold data archiving to S3 | 75-96% storage | High | Low (with testing) |
| DynamoDB: On-Demand → Provisioned | 80-90% DynamoDB | Low | Low (with monitoring) |
| Add PgBouncer (vs bigger instance) | $500-2000/month | Medium | Low |
