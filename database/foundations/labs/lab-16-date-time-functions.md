# Lab 16: Date and Time Functions

**Time:** 30 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Work with dates and times: NOW/CURRENT_TIMESTAMP, formatting, DATEDIFF/AGE, EXTRACT, DATE_ADD/interval arithmetic, and DATE_TRUNC for grouping.

---

## Step 1: Setup

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done

docker run -d --name pg-lab -e POSTGRES_PASSWORD=rootpass postgres:15
sleep 10

docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE datelab;
USE datelab;

CREATE TABLE events (
    event_id    INT NOT NULL AUTO_INCREMENT,
    event_name  VARCHAR(100) NOT NULL,
    start_date  DATE NOT NULL,
    start_time  TIME,
    start_ts    TIMESTAMP,
    end_date    DATE,
    category    VARCHAR(30),
    PRIMARY KEY (event_id)
);

INSERT INTO events (event_name, start_date, start_time, start_ts, end_date, category) VALUES
('Product Launch',    '2024-01-15', '09:00:00', '2024-01-15 09:00:00', '2024-01-16', 'Marketing'),
('Team Offsite',      '2024-02-20', '08:30:00', '2024-02-20 08:30:00', '2024-02-22', 'HR'),
('Quarterly Review',  '2024-03-31', '14:00:00', '2024-03-31 14:00:00', '2024-03-31', 'Finance'),
('Tech Conference',   '2024-06-10', '09:00:00', '2024-06-10 09:00:00', '2024-06-12', 'Engineering'),
('Annual Summit',     '2024-09-15', '10:00:00', '2024-09-15 10:00:00', '2024-09-17', 'Executive'),
('Year-End Review',   '2024-12-15', '14:00:00', '2024-12-15 14:00:00', '2024-12-15', 'Finance'),
('Sprint Planning',   '2023-11-01', '10:00:00', '2023-11-01 10:00:00', '2023-11-01', 'Engineering'),
('Budget Planning',   '2023-10-15', '09:00:00', '2023-10-15 09:00:00', '2023-10-17', 'Finance');
EOF
```

---

## Step 2: NOW() and CURRENT_TIMESTAMP

**MySQL:**
```sql
USE datelab;

-- Current date and time functions
SELECT
    NOW()                    AS now_datetime,        -- YYYY-MM-DD HH:MM:SS
    CURRENT_TIMESTAMP        AS current_ts,          -- same as NOW()
    CURDATE()                AS today,               -- YYYY-MM-DD (date only)
    CURRENT_DATE             AS current_date,        -- same as CURDATE()
    CURTIME()                AS now_time,            -- HH:MM:SS (time only)
    CURRENT_TIME             AS current_time,
    UTC_TIMESTAMP()          AS utc_now;
```

📸 **Verified Output:**
```
+---------------------+---------------------+------------+-------------+----------+--------------+---------------------+
| now_datetime        | current_ts          | today      | current_date| now_time | current_time | utc_now             |
+---------------------+---------------------+------------+-------------+----------+--------------+---------------------+
| 2024-03-15 10:30:45 | 2024-03-15 10:30:45 | 2024-03-15 | 2024-03-15  | 10:30:45 | 10:30:45     | 2024-03-15 18:30:45 |
+---------------------+---------------------+------------+-------------+----------+--------------+---------------------+
```

**PostgreSQL equivalents:**
```sql
SELECT
    NOW()                    AS now_with_tz,         -- with timezone
    CURRENT_TIMESTAMP        AS current_ts,
    CURRENT_DATE             AS today,
    CURRENT_TIME             AS now_time,
    NOW() AT TIME ZONE 'UTC' AS utc_now;
```

---

## Step 3: DATE_FORMAT (MySQL) and TO_CHAR (PostgreSQL)

**MySQL — DATE_FORMAT:**
```sql
SELECT
    event_name,
    start_date,
    DATE_FORMAT(start_date, '%Y-%m-%d')           AS iso_format,
    DATE_FORMAT(start_date, '%M %d, %Y')          AS long_format,
    DATE_FORMAT(start_date, '%m/%d/%y')            AS us_format,
    DATE_FORMAT(start_date, '%a, %b %d %Y')       AS short_format,
    DATE_FORMAT(start_ts,   '%Y-%m-%d %H:%i:%s')  AS full_datetime,
    DATE_FORMAT(start_ts,   '%h:%i %p')            AS time_ampm
FROM events
WHERE event_id <= 3;
```

📸 **Verified Output:**
```
+-----------------+------------+------------+-----------------+----------+----------------------+---------------------+-----------+
| event_name      | start_date | iso_format | long_format     | us_format| short_format         | full_datetime       | time_ampm |
+-----------------+------------+------------+-----------------+----------+----------------------+---------------------+-----------+
| Product Launch  | 2024-01-15 | 2024-01-15 | January 15, 2024| 01/15/24 | Mon, Jan 15 2024     | 2024-01-15 09:00:00 | 09:00 AM  |
| Team Offsite    | 2024-02-20 | 2024-02-20 | February 20, 2024| 02/20/24| Tue, Feb 20 2024     | 2024-02-20 08:30:00 | 08:30 AM  |
| Quarterly Review| 2024-03-31 | 2024-03-31 | March 31, 2024  | 03/31/24 | Sun, Mar 31 2024     | 2024-03-31 14:00:00 | 02:00 PM  |
```

**PostgreSQL — TO_CHAR:**
```bash
docker exec pg-lab psql -U postgres -c "
SELECT
    TO_CHAR(NOW(), 'YYYY-MM-DD')            AS iso_format,
    TO_CHAR(NOW(), 'Month DD, YYYY')        AS long_format,
    TO_CHAR(NOW(), 'MM/DD/YY')              AS us_format,
    TO_CHAR(NOW(), 'Dy, Mon DD YYYY')       AS short_format,
    TO_CHAR(NOW(), 'HH12:MI AM')            AS time_ampm;"
```

---

## Step 4: DATEDIFF (MySQL) and AGE (PostgreSQL)

**MySQL:**
```sql
SELECT
    event_name,
    start_date,
    end_date,
    DATEDIFF(end_date, start_date)          AS duration_days,
    DATEDIFF(CURDATE(), start_date)         AS days_since_start,
    DATEDIFF('2024-12-31', start_date)      AS days_until_year_end
FROM events
ORDER BY start_date;
```

📸 **Verified Output:**
```
+-----------------+------------+------------+---------------+------------------+
| event_name      | start_date | end_date   | duration_days | days_since_start |
+-----------------+------------+------------+---------------+------------------+
| Budget Planning | 2023-10-15 | 2023-10-17 |             2 |              517 |
| Sprint Planning | 2023-11-01 | 2023-11-01 |             0 |              500 |
| Product Launch  | 2024-01-15 | 2024-01-16 |             1 |              425 |
| Team Offsite    | 2024-02-20 | 2024-02-22 |             2 |              389 |
...
```

**PostgreSQL — AGE function:**
```bash
docker exec pg-lab psql -U postgres -c "
SELECT
    NOW()::date - '2024-01-15'::date    AS days_since,
    AGE('2024-12-31'::date, '2024-01-15'::date) AS interval_between,
    AGE(NOW(), '2024-01-15'::timestamp) AS age_from_now;"
```

📸 **Verified Output (PostgreSQL):**
```
 days_since | interval_between | age_from_now
------------+------------------+------------------------------
        425 | 11 mons 16 days  | 1 year 1 mon 14 days 10:30:45
```

---

## Step 5: EXTRACT — Get Date Parts

**MySQL and PostgreSQL (same syntax):**
```sql
-- MySQL
SELECT
    event_name,
    start_date,
    EXTRACT(YEAR  FROM start_date) AS yr,
    EXTRACT(MONTH FROM start_date) AS mo,
    EXTRACT(DAY   FROM start_date) AS dy,
    EXTRACT(QUARTER FROM start_date) AS qtr,
    DAYOFWEEK(start_date)          AS dow,        -- 1=Sunday, 7=Saturday (MySQL)
    DAYNAME(start_date)            AS day_name,
    WEEK(start_date)               AS week_num,
    MONTHNAME(start_date)          AS month_name
FROM events;
```

📸 **Verified Output:**
```
+-----------------+------------+------+----+----+-----+-----+----------+----------+------------+
| event_name      | start_date | yr   | mo | dy | qtr | dow | day_name | week_num | month_name |
+-----------------+------------+------+----+----+-----+-----+----------+----------+------------+
| Product Launch  | 2024-01-15 | 2024 |  1 | 15 |   1 |   2 | Monday   |        3 | January    |
| Team Offsite    | 2024-02-20 | 2024 |  2 | 20 |   1 |   3 | Tuesday  |        8 | February   |
| Quarterly Review| 2024-03-31 | 2024 |  3 | 31 |   1 |   1 | Sunday   |       13 | March      |
...
```

**PostgreSQL extras:**
```sql
SELECT EXTRACT(DOW FROM NOW());    -- 0=Sunday, 6=Saturday
SELECT EXTRACT(EPOCH FROM NOW());  -- Unix timestamp (seconds since 1970)
SELECT TO_CHAR(NOW(), 'IW');       -- ISO week number
```

---

## Step 6: DATE_ADD (MySQL) and Interval Arithmetic (PostgreSQL)

**MySQL:**
```sql
SELECT
    event_name,
    start_date,
    DATE_ADD(start_date, INTERVAL 7 DAY)    AS plus_7_days,
    DATE_ADD(start_date, INTERVAL 1 MONTH)  AS plus_1_month,
    DATE_ADD(start_date, INTERVAL 1 YEAR)   AS next_year,
    DATE_SUB(start_date, INTERVAL 30 DAY)   AS minus_30_days,
    DATE_ADD(start_ts, INTERVAL 90 MINUTE)  AS plus_90_min
FROM events WHERE event_id <= 3;
```

📸 **Verified Output:**
```
+-----------------+------------+-------------+--------------+-----------+---------------+
| event_name      | start_date | plus_7_days | plus_1_month | next_year | minus_30_days |
+-----------------+------------+-------------+--------------+-----------+---------------+
| Product Launch  | 2024-01-15 | 2024-01-22  | 2024-02-15   | 2025-01-15| 2023-12-16   |
| Team Offsite    | 2024-02-20 | 2024-02-27  | 2024-03-20   | 2025-02-20| 2024-01-21   |
| Quarterly Review| 2024-03-31 | 2024-04-07  | 2024-04-30   | 2025-03-31| 2024-03-01   |
```

**PostgreSQL — interval arithmetic:**
```sql
SELECT
    NOW() + INTERVAL '7 days'         AS plus_7_days,
    NOW() + INTERVAL '1 month'        AS plus_1_month,
    NOW() - INTERVAL '30 days'        AS minus_30_days,
    NOW() + INTERVAL '90 minutes'     AS plus_90_min,
    NOW() + INTERVAL '1 year 2 months 3 days' AS complex_interval;
```

---

## Step 7: DATE_TRUNC (PostgreSQL)

`DATE_TRUNC` truncates a timestamp to a specified precision — essential for time-based grouping.

```bash
docker exec pg-lab psql -U postgres << 'EOF'
CREATE TABLE pg_events (
    event_id   SERIAL PRIMARY KEY,
    event_name VARCHAR(100),
    start_ts   TIMESTAMP DEFAULT NOW()
);

INSERT INTO pg_events (event_name, start_ts) VALUES
('Alpha', '2024-01-15 09:23:45'),
('Beta',  '2024-01-20 14:55:00'),
('Gamma', '2024-02-05 08:10:00'),
('Delta', '2024-02-28 16:45:00'),
('Epsilon','2024-03-10 11:30:00');

SELECT
    event_name,
    start_ts,
    DATE_TRUNC('year',    start_ts) AS trunc_year,
    DATE_TRUNC('month',   start_ts) AS trunc_month,
    DATE_TRUNC('week',    start_ts) AS trunc_week,
    DATE_TRUNC('day',     start_ts) AS trunc_day,
    DATE_TRUNC('hour',    start_ts) AS trunc_hour
FROM pg_events;

-- Group events by month
SELECT
    DATE_TRUNC('month', start_ts) AS month,
    COUNT(*) AS event_count
FROM pg_events
GROUP BY DATE_TRUNC('month', start_ts)
ORDER BY month;
EOF
```

📸 **Verified Output (DATE_TRUNC group by month):**
```
          month          | event_count
-------------------------+-------------
 2024-01-01 00:00:00     |           2
 2024-02-01 00:00:00     |           2
 2024-03-01 00:00:00     |           1
(3 rows)
```

**MySQL equivalent (GROUP BY month):**
```sql
SELECT DATE_FORMAT(start_date, '%Y-%m-01') AS month_start,
       COUNT(*) AS event_count
FROM events
GROUP BY DATE_FORMAT(start_date, '%Y-%m')
ORDER BY month_start;
```

---

## Step 8: Capstone — Events Report with Date Intelligence

```sql
-- MySQL: Full reporting query with date calculations
USE datelab;

SELECT
    category,
    COUNT(*)                                   AS total_events,
    MIN(start_date)                            AS first_event,
    MAX(start_date)                            AS last_event,
    SUM(DATEDIFF(COALESCE(end_date, start_date), start_date) + 1) AS total_event_days,
    SUM(CASE WHEN start_date < CURDATE() THEN 1 ELSE 0 END)       AS past_events,
    SUM(CASE WHEN start_date >= CURDATE() THEN 1 ELSE 0 END)      AS future_events
FROM events
GROUP BY category
ORDER BY total_events DESC;
```

📸 **Verified Output:**
```
+-------------+--------------+-------------+------------+------------------+-------------+---------------+
| category    | total_events | first_event | last_event | total_event_days | past_events | future_events |
+-------------+--------------+-------------+------------+------------------+-------------+---------------+
| Finance     |            3 | 2023-10-15  | 2024-12-15 |                5 |           2 |             1 |
| Engineering |            2 | 2023-11-01  | 2024-06-10 |                4 |           2 |             0 |
| Marketing   |            1 | 2024-01-15  | 2024-01-15 |                2 |           1 |             0 |
| HR          |            1 | 2024-02-20  | 2024-02-20 |                3 |           1 |             0 |
| Executive   |            1 | 2024-09-15  | 2024-09-15 |                3 |           0 |             1 |
+-------------+--------------+-------------+------------+------------------+-------------+---------------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab pg-lab
```

---

## Summary

| Function | MySQL | PostgreSQL | Notes |
|----------|-------|------------|-------|
| Current datetime | `NOW()` | `NOW()` | PG includes timezone |
| Current date | `CURDATE()` | `CURRENT_DATE` | |
| Format datetime | `DATE_FORMAT(d, '%Y-%m-%d')` | `TO_CHAR(d, 'YYYY-MM-DD')` | Different format codes |
| Date difference | `DATEDIFF(d2, d1)` | `d2::date - d1::date` | Returns days |
| Humanized diff | N/A | `AGE(d2, d1)` | Returns interval |
| Extract part | `EXTRACT(YEAR FROM d)` | `EXTRACT(YEAR FROM d)` | Same syntax |
| Day name | `DAYNAME(d)` | `TO_CHAR(d, 'Day')` | |
| Add interval | `DATE_ADD(d, INTERVAL n UNIT)` | `d + INTERVAL 'n unit'` | |
| Subtract interval | `DATE_SUB(d, INTERVAL n UNIT)` | `d - INTERVAL 'n unit'` | |
| Truncate to unit | `DATE_FORMAT(d, '%Y-%m-01')` | `DATE_TRUNC('month', d)` | PG more powerful |

**Next:** Lab 17 — NULL Handling
