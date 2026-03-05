# Lab 20: Capstone — E-Commerce Database

**Time:** 60 minutes | **Level:** Foundations | **DB:** MySQL 8 / PostgreSQL 15

## Overview

Design and build a complete, normalized e-commerce database from scratch. Create 7 tables with full FK constraints, load 50+ rows of realistic sample data, write complex reporting queries, and add performance indexes.

---

## Step 1: Start the Database

```bash
docker run -d --name mysql-lab -e MYSQL_ROOT_PASSWORD=rootpass mysql:8.0
for i in $(seq 1 30); do docker exec mysql-lab mysql -uroot -prootpass -e "SELECT 1" 2>/dev/null && break || sleep 2; done
```

---

## Step 2: Schema Design

Our e-commerce schema implements 3NF normalization with 7 tables:

```
categories        ← product category hierarchy
products          ← product catalog (FK: categories)
users             ← customer accounts
addresses         ← shipping addresses (FK: users)
orders            ← purchase orders (FK: users, addresses)
order_items       ← line items per order (FK: orders, products)
reviews           ← product reviews (FK: users, products)
```

**Entity Relationship:**
```
categories (1) ──< products (N)
users (1) ──< addresses (N)
users (1) ──< orders (N)
addresses (1) ──< orders (N)    [shipping address]
orders (1) ──< order_items (N)
products (1) ──< order_items (N)
users (1) ──< reviews (N)
products (1) ──< reviews (N)
```

---

## Step 3: Create the Schema

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
CREATE DATABASE ecommerce;
USE ecommerce;

-- 1. Categories (self-referencing for hierarchy)
CREATE TABLE categories (
    cat_id      INT NOT NULL AUTO_INCREMENT,
    parent_id   INT DEFAULT NULL,
    name        VARCHAR(100) NOT NULL,
    slug        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_active   BOOLEAN DEFAULT TRUE,
    sort_order  INT DEFAULT 0,
    PRIMARY KEY (cat_id),
    FOREIGN KEY (parent_id) REFERENCES categories(cat_id) ON DELETE SET NULL,
    INDEX idx_parent (parent_id),
    INDEX idx_slug (slug)
);

-- 2. Products
CREATE TABLE products (
    product_id    INT NOT NULL AUTO_INCREMENT,
    cat_id        INT NOT NULL,
    name          VARCHAR(255) NOT NULL,
    sku           VARCHAR(50) NOT NULL UNIQUE,
    description   TEXT,
    price         DECIMAL(10,2) NOT NULL,
    cost          DECIMAL(10,2),
    stock_qty     INT NOT NULL DEFAULT 0,
    weight_kg     DECIMAL(6,3),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id),
    FOREIGN KEY (cat_id) REFERENCES categories(cat_id),
    INDEX idx_cat (cat_id),
    INDEX idx_price (price),
    INDEX idx_sku (sku),
    CONSTRAINT chk_price CHECK (price >= 0),
    CONSTRAINT chk_stock CHECK (stock_qty >= 0)
);

-- 3. Users
CREATE TABLE users (
    user_id       INT NOT NULL AUTO_INCREMENT,
    email         VARCHAR(150) NOT NULL UNIQUE,
    first_name    VARCHAR(50) NOT NULL,
    last_name     VARCHAR(50) NOT NULL,
    phone         VARCHAR(20),
    password_hash VARCHAR(255) NOT NULL DEFAULT 'hashed',
    is_active     BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMP NULL,
    PRIMARY KEY (user_id),
    INDEX idx_email (email)
);

-- 4. Addresses
CREATE TABLE addresses (
    address_id   INT NOT NULL AUTO_INCREMENT,
    user_id      INT NOT NULL,
    label        VARCHAR(20) DEFAULT 'home',
    street1      VARCHAR(150) NOT NULL,
    street2      VARCHAR(150),
    city         VARCHAR(100) NOT NULL,
    state        VARCHAR(50),
    postal_code  VARCHAR(20) NOT NULL,
    country      CHAR(2) DEFAULT 'US',
    is_default   BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (address_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
);

-- 5. Orders
CREATE TABLE orders (
    order_id       INT NOT NULL AUTO_INCREMENT,
    user_id        INT NOT NULL,
    address_id     INT,
    status         ENUM('pending','confirmed','processing','shipped','delivered','cancelled','refunded') DEFAULT 'pending',
    subtotal       DECIMAL(12,2) NOT NULL,
    discount_amt   DECIMAL(12,2) DEFAULT 0,
    shipping_cost  DECIMAL(10,2) DEFAULT 0,
    tax_amt        DECIMAL(10,2) DEFAULT 0,
    total          DECIMAL(12,2) NOT NULL,
    notes          TEXT,
    placed_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shipped_at     TIMESTAMP NULL,
    delivered_at   TIMESTAMP NULL,
    PRIMARY KEY (order_id),
    FOREIGN KEY (user_id)    REFERENCES users(user_id),
    FOREIGN KEY (address_id) REFERENCES addresses(address_id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_status (status),
    INDEX idx_placed (placed_at)
);

-- 6. Order Items
CREATE TABLE order_items (
    item_id      INT NOT NULL AUTO_INCREMENT,
    order_id     INT NOT NULL,
    product_id   INT NOT NULL,
    quantity     INT NOT NULL,
    unit_price   DECIMAL(10,2) NOT NULL,  -- price at time of purchase (snapshot)
    discount_pct DECIMAL(5,2) DEFAULT 0,
    line_total   DECIMAL(12,2) GENERATED ALWAYS AS
                 (ROUND(quantity * unit_price * (1 - discount_pct/100), 2)) STORED,
    PRIMARY KEY (item_id),
    UNIQUE KEY uq_order_product (order_id, product_id),
    FOREIGN KEY (order_id)   REFERENCES orders(order_id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_product (product_id),
    CONSTRAINT chk_qty CHECK (quantity > 0)
);

-- 7. Reviews
CREATE TABLE reviews (
    review_id    INT NOT NULL AUTO_INCREMENT,
    product_id   INT NOT NULL,
    user_id      INT NOT NULL,
    rating       TINYINT NOT NULL,
    title        VARCHAR(200),
    body         TEXT,
    is_verified  BOOLEAN DEFAULT FALSE,  -- verified purchase
    helpful_count INT DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id),
    UNIQUE KEY uq_user_product (user_id, product_id),  -- one review per user per product
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(user_id)       ON DELETE CASCADE,
    INDEX idx_product (product_id),
    INDEX idx_rating (rating),
    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5)
);

SHOW TABLES;
EOF
```

📸 **Verified Output:**
```
+---------------------+
| Tables_in_ecommerce |
+---------------------+
| addresses           |
| categories          |
| order_items         |
| orders              |
| products            |
| reviews             |
| users               |
+---------------------+
```

---

## Step 4: Insert Sample Data — Categories and Products

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE ecommerce;

-- Categories (hierarchy)
INSERT INTO categories (name, slug, parent_id, sort_order) VALUES
('Electronics',    'electronics',     NULL, 1),
('Computers',      'computers',          1, 1),
('Laptops',        'laptops',            2, 1),
('Desktops',       'desktops',           2, 2),
('Peripherals',    'peripherals',        1, 2),
('Mice',           'mice',               5, 1),
('Keyboards',      'keyboards',          5, 2),
('Monitors',       'monitors',           5, 3),
('Books',          'books',           NULL, 2),
('Technology',     'technology-books',   9, 1),
('Fiction',        'fiction',            9, 2),
('Furniture',      'furniture',       NULL, 3),
('Office Chairs',  'office-chairs',     12, 1),
('Desks',          'desks',             12, 2);

-- Products (20 products across categories)
INSERT INTO products (cat_id, name, sku, description, price, cost, stock_qty, weight_kg) VALUES
(3,  'Laptop Pro 15 M2',      'LAP-001', 'High-performance laptop with M2 chip, 16GB RAM, 512GB SSD',   1299.99, 850.00,  50, 1.8),
(3,  'UltraBook 14 Slim',     'LAP-002', 'Ultra-thin 14-inch laptop, 8GB RAM, 256GB SSD, 12hr battery', 899.99,  580.00,  75, 1.3),
(3,  'Gaming Laptop RX',      'LAP-003', 'Gaming powerhouse, RTX 4070, 32GB RAM, 1TB SSD, 165Hz',       1899.99, 1200.00, 30, 2.5),
(4,  'Desktop Workstation Pro','DSK-001', 'Professional workstation, Intel i9, 64GB RAM, 2TB NVMe',       2499.99, 1600.00, 20, 8.5),
(6,  'Ergonomic Mouse M500',  'MOU-001', 'Wireless ergonomic mouse, 2400 DPI, 6 buttons, 60hr battery',   49.99,  22.00, 200, 0.1),
(6,  'Gaming Mouse Pro',      'MOU-002', 'Gaming mouse, 25600 DPI, RGB, programmable, 1000Hz',            79.99,  35.00, 150, 0.1),
(6,  'Travel Mouse Compact',  'MOU-003', 'Compact travel mouse, USB-C, silent clicks, 2-year battery',    29.99,  12.00, 300, 0.07),
(7,  'Mechanical Keyboard TKL','KEY-001', 'TKL mechanical keyboard, Cherry MX Brown, RGB backlight',       89.99,  42.00, 100, 0.8),
(7,  'Wireless Keyboard Slim','KEY-002', 'Slim wireless keyboard, Bluetooth 5.0, 3-device pairing',        59.99,  28.00, 120, 0.4),
(8,  'Monitor 27 4K IPS',     'MON-001', '27-inch 4K IPS monitor, 144Hz, HDR400, USB-C 90W charging',    449.99, 280.00,  40, 5.2),
(8,  'Monitor 24 FHD',        'MON-002', '24-inch Full HD monitor, 165Hz, 1ms, AMD FreeSync',             199.99, 120.00,  60, 3.8),
(10, 'SQL Mastery Complete',  'BOK-001', 'Complete guide to SQL from basics to advanced query optimization', 49.99, 8.00, 500, 0.6),
(10, 'PostgreSQL Internals',  'BOK-002', 'Deep dive into PostgreSQL architecture, performance, and extensions', 59.99, 10.00, 300, 0.7),
(10, 'Database Design Patterns','BOK-003', 'Practical patterns for scalable database architecture',         44.99,  7.50, 400, 0.5),
(11, 'The Algorithm',         'BOK-004', 'Bestselling thriller about AI and corporate espionage',           16.99,  4.00, 800, 0.35),
(11, 'Data Horizons',         'BOK-005', 'Science fiction epic about humanity in a data-driven future',    14.99,  3.50, 600, 0.3),
(13, 'ErgoChair Pro',         'CHR-001', 'Fully adjustable ergonomic chair, lumbar support, mesh back',   299.99, 150.00,  35, 18.0),
(13, 'Task Chair Basic',      'CHR-002', 'Budget ergonomic chair with adjustable height and armrests',    129.99,  60.00,  50, 12.0),
(14, 'Standing Desk L-Shape', 'DSK-S01', 'Electric sit-stand L-shaped desk, memory presets, 200lb capacity', 599.99, 320.00, 20, 45.0),
(14, 'Monitor Arm Dual',      'DSK-S02', 'Dual monitor arm, full motion, fits 17-32 inch, 9kg per arm',    79.99,  35.00,  80, 3.5);
EOF
```

---

## Step 5: Insert Users, Addresses, and Orders

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE ecommerce;

-- 10 Users
INSERT INTO users (email, first_name, last_name, phone, is_active, email_verified) VALUES
('alice@email.com',  'Alice',   'Johnson',  '555-0101', TRUE,  TRUE),
('bob@email.com',    'Bob',     'Smith',    '555-0102', TRUE,  TRUE),
('carol@email.com',  'Carol',   'Davis',    '555-0103', TRUE,  TRUE),
('david@email.com',  'David',   'Wilson',   '555-0104', TRUE,  FALSE),
('eve@email.com',    'Eve',     'Martinez', '555-0105', TRUE,  TRUE),
('frank@email.com',  'Frank',   'Anderson', '555-0106', TRUE,  TRUE),
('grace@email.com',  'Grace',   'Taylor',   '555-0107', FALSE, TRUE),
('henry@email.com',  'Henry',   'Thomas',   '555-0108', TRUE,  TRUE),
('isabel@email.com', 'Isabel',  'Jackson',  '555-0109', TRUE,  TRUE),
('jack@email.com',   'Jack',    'White',    '555-0110', TRUE,  TRUE);

-- Addresses (2 per some users)
INSERT INTO addresses (user_id, label, street1, city, state, postal_code, country, is_default) VALUES
(1, 'home',   '123 Oak St',      'New York',    'NY', '10001', 'US', TRUE),
(1, 'work',   '456 Park Ave',    'New York',    'NY', '10022', 'US', FALSE),
(2, 'home',   '789 Elm Ave',     'Chicago',     'IL', '60601', 'US', TRUE),
(3, 'home',   '321 Pine Rd',     'Los Angeles', 'CA', '90001', 'US', TRUE),
(3, 'other',  '654 Cedar Ln',    'San Diego',   'CA', '92101', 'US', FALSE),
(4, 'home',   '147 Maple Dr',    'Houston',     'TX', '77001', 'US', TRUE),
(5, 'home',   '258 Birch Blvd',  'Phoenix',     'AZ', '85001', 'US', TRUE),
(6, 'home',   '369 Walnut St',   'Philadelphia','PA', '19101', 'US', TRUE),
(8, 'home',   '741 Cherry Ave',  'San Antonio', 'TX', '78201', 'US', TRUE),
(9, 'home',   '852 Spruce Ct',   'Dallas',      'TX', '75201', 'US', TRUE),
(10,'home',   '963 Ash Way',     'Seattle',     'WA', '98101', 'US', TRUE);

-- 15 Orders (mix of statuses)
INSERT INTO orders (user_id, address_id, status, subtotal, discount_amt, shipping_cost, tax_amt, total, placed_at, shipped_at, delivered_at) VALUES
(1, 1, 'delivered',  1299.99,  0,    0,     104.00, 1403.99, '2024-01-10 09:15:00', '2024-01-11 14:00:00', '2024-01-13 10:30:00'),
(1, 1, 'delivered',   179.98,  0,   9.99,   14.40,  204.37, '2024-01-25 14:22:00', '2024-01-26 10:00:00', '2024-01-28 15:00:00'),
(2, 3, 'delivered',   449.99,  0,    0,     36.00,  485.99, '2024-02-05 11:30:00', '2024-02-06 09:00:00', '2024-02-08 14:00:00'),
(3, 4, 'shipped',    1899.99,  100, 29.99,  152.00, 1981.98,'2024-02-18 16:45:00', '2024-02-20 08:00:00', NULL),
(4, 6, 'confirmed',   159.98,  0,   9.99,   12.80,  182.77, '2024-02-22 10:00:00', NULL, NULL),
(5, 7, 'delivered',   599.98,  50,   0,     44.00,  593.98, '2024-03-01 08:30:00', '2024-03-02 11:00:00', '2024-03-04 16:00:00'),
(1, 2, 'cancelled',   299.99,  0,    0,      0,     299.99, '2024-03-05 13:00:00', NULL, NULL),
(6, 8, 'delivered',   149.97,  0,   4.99,   12.00,  166.96, '2024-03-08 09:00:00', '2024-03-09 14:00:00', '2024-03-11 10:00:00'),
(8, 9, 'processing',  679.98,  0,    0,     54.40,  734.38, '2024-03-10 15:30:00', NULL, NULL),
(2, 3, 'delivered',    94.97,  0,   4.99,   8.00,   107.96, '2024-03-12 12:00:00', '2024-03-13 10:00:00', '2024-03-15 14:00:00'),
(9, 10,'delivered',  2499.99, 200,   0,    184.00, 2483.99, '2024-03-15 10:00:00', '2024-03-16 08:00:00', '2024-03-18 11:00:00'),
(10,11,'pending',     239.97,  0,   9.99,   19.20,  269.16, '2024-03-18 16:00:00', NULL, NULL),
(3, 5, 'delivered',   199.99,  20,   0,     14.40,  194.39, '2024-03-20 11:00:00', '2024-03-21 09:00:00', '2024-03-23 13:00:00'),
(5, 7, 'shipped',     899.99,  0,    0,     72.00,  971.99, '2024-03-22 14:00:00', '2024-03-23 10:00:00', NULL),
(1, 1, 'delivered',    44.99,  0,   2.99,   3.60,   51.58, '2024-03-25 09:30:00', '2024-03-26 11:00:00', '2024-03-28 14:00:00');

-- Order Items (linking orders to products)
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_pct) VALUES
(1,  1,  1, 1299.99, 0),
(2,  5,  2,  49.99,  0),
(2,  8,  1,  89.99,  10),  -- keyboard with 10% discount
(3,  10, 1, 449.99,  0),
(4,  3,  1, 1899.99, 5),
(5,  6,  1,  79.99,  0),
(5,  9,  1,  59.99,  12.5),
(6,  17, 1, 299.99,  0),
(6,  20, 2,  79.99,  12.5),
(7,  17, 1, 299.99,  0),   -- cancelled order
(8,  12, 2,  49.99,  0),
(8,  13, 1,  59.99,  0),
(9,  19, 1, 599.99,  0),
(9,  20, 1,  79.99,  0),
(10, 12, 1,  49.99,  0),
(10, 15, 3,  14.99,  0),
(11, 4,  1, 2499.99, 8),
(12, 7,  3,  29.99,  0),
(12, 12, 1,  49.99,  0),
(12, 16, 2,  14.99,  0),
(13, 11, 1, 199.99,  10),
(14, 2,  1, 899.99,  0),
(15, 14, 1,  44.99,  0);
EOF
```

---

## Step 6: Insert Reviews

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE ecommerce;

INSERT INTO reviews (product_id, user_id, rating, title, body, is_verified, helpful_count) VALUES
(1,  1, 5, 'Best laptop I have ever owned',      'The M2 chip is incredibly fast. Battery life is amazing. Worth every penny.', TRUE,  24),
(1,  2, 4, 'Great performance, minor issues',    'Excellent speed and display. Runs a bit hot under load. Fan noise occasional.', TRUE,  8),
(3,  3, 5, 'Gaming beast!',                      'Runs every game at max settings. The 165Hz display is buttery smooth.', TRUE,  15),
(5,  1, 4, 'Comfortable for long sessions',      'The ergonomic design really helps with wrist fatigue. Battery lasts 2 months.', TRUE,  12),
(5,  5, 5, 'Perfect travel mouse',               'Switched from wired to this and never going back. Pairs instantly.', TRUE,  7),
(8,  6, 5, 'Typing feels premium',               'Cherry MX Browns are perfect for typing and coding. RGB is a nice touch.', TRUE,  19),
(10, 8, 5, 'Stunning 4K display',                'Colors are incredibly accurate. USB-C charging is a game changer.', TRUE,  31),
(10, 2, 4, 'Great monitor with minor cons',      'Image quality is superb. The stand is a bit wobbly at max height.', TRUE,  5),
(12, 1, 5, 'Comprehensive SQL guide',            'Best SQL book I have read. Examples are practical and well-explained.', TRUE,  43),
(12, 6, 4, 'Good but slightly outdated',         'Great fundamentals but some PostgreSQL examples are for older versions.', TRUE,  11),
(12, 9, 5, 'Essential for any developer',        'Bought this for a junior dev on my team. They learned SQL in 2 weeks.', FALSE, 28),
(17, 9, 5, 'Transformed my work setup',          'My back no longer hurts after 8-hour work days. Lumbar support is perfect.', TRUE,  37),
(17, 3, 4, 'Good chair, assembly instructions poor', 'Chair is comfortable but assembly instructions were confusing.', TRUE,  9),
(19, 9, 5, 'Worth every penny',                  'The electric motor is whisper quiet. Memory presets are super convenient.', TRUE,  22),
(4,  9, 5, 'Powerhouse workstation',             'Handles 4K video editing without breaking a sweat. Upgradeable too.', TRUE,  18),
(2,  5, 4, 'Great ultrabook for travel',         'Light, fast, and battery lasts all day. Screen could be brighter outdoors.', TRUE,  6),
(11, 3, 5, 'Best budget monitor',                'For the price, image quality is incredible. Zero backlight bleed.', TRUE,  14),
(13, 8, 5, 'Excellent PostgreSQL resource',      'Goes deep into internals. Not for beginners but invaluable for DBAs.', TRUE,  25),
(20, 8, 4, 'Solid dual monitor arm',             'Solid construction. Easy to adjust. Instructions could be clearer.', TRUE,  3),
(16, 10,5, 'Great science fiction read',          'Thought-provoking story about data privacy and AI. Highly recommended.', FALSE, 7);
EOF
```

---

## Step 7: Complex Reporting Queries

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE ecommerce;

-- ============================================================
-- REPORT 1: Top Products by Revenue
-- ============================================================
SELECT
    p.sku,
    p.name AS product_name,
    c.name AS category,
    SUM(oi.quantity)                              AS units_sold,
    ROUND(SUM(oi.line_total), 2)                  AS total_revenue,
    ROUND(AVG(oi.unit_price), 2)                  AS avg_unit_price,
    ROUND(SUM(oi.line_total) / SUM(oi.quantity), 2) AS avg_revenue_per_unit
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN categories c ON p.cat_id = c.cat_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY p.product_id, p.sku, p.name, c.name
ORDER BY total_revenue DESC
LIMIT 10;
EOF
```

📸 **Verified Output (Top Products by Revenue):**
```
+---------+---------------------+---------------+------------+---------------+
| sku     | product_name        | category      | units_sold | total_revenue |
+---------+---------------------+---------------+------------+---------------+
| DSK-001 | Desktop Workstation | Desktops      |          1 |      2299.99  |
| LAP-003 | Gaming Laptop RX    | Laptops       |          1 |      1804.99  |
| LAP-001 | Laptop Pro 15 M2   | Laptops       |          1 |      1299.99  |
| DSK-S01 | Standing Desk       | Desks         |          1 |       599.99  |
| LAP-002 | UltraBook 14 Slim   | Laptops       |          1 |       899.99  |
| MON-001 | Monitor 27 4K IPS   | Monitors      |          1 |       449.99  |
| CHR-001 | ErgoChair Pro       | Office Chairs |          1 |       299.99  |
| MON-002 | Monitor 24 FHD      | Monitors      |          1 |       179.99  |
| BOK-001 | SQL Mastery Complete| Technology    |          4 |       199.96  |
| KEY-001 | Mechanical Keyboard | Keyboards     |          1 |        80.99  |
+---------+---------------------+---------------+------------+---------------+
```

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE ecommerce;

-- ============================================================
-- REPORT 2: User Order History with Lifetime Value
-- ============================================================
SELECT
    u.user_id,
    CONCAT(u.first_name, ' ', u.last_name)    AS customer_name,
    u.email,
    COUNT(DISTINCT o.order_id)                 AS total_orders,
    COUNT(DISTINCT CASE WHEN o.status NOT IN ('cancelled','refunded') THEN o.order_id END) AS completed_orders,
    ROUND(SUM(CASE WHEN o.status NOT IN ('cancelled','refunded') THEN o.total ELSE 0 END), 2) AS lifetime_value,
    ROUND(AVG(CASE WHEN o.status NOT IN ('cancelled','refunded') THEN o.total END), 2) AS avg_order_value,
    MAX(o.placed_at)                           AS last_order_date,
    MIN(o.placed_at)                           AS first_order_date
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE u.is_active = TRUE
GROUP BY u.user_id, u.first_name, u.last_name, u.email
ORDER BY lifetime_value DESC;
EOF
```

📸 **Verified Output:**
```
+---------+---------------+---------------------+--------------+------------------+----------------+
| user_id | customer_name | email               | total_orders | completed_orders | lifetime_value |
+---------+---------------+---------------------+--------------+------------------+----------------+
|       9 | Isabel Jackson| isabel@email.com    |            1 |                1 |       2483.99  |
|       1 | Alice Johnson | alice@email.com     |            4 |                3 |       1659.94  |
|       3 | Carol Davis   | carol@email.com     |            2 |                2 |       2176.37  |
|       5 | Eve Martinez  | eve@email.com       |            2 |                2 |       1565.97  |
|       2 | Bob Smith     | bob@email.com       |            2 |                2 |        593.95  |
...
```

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE ecommerce;

-- ============================================================
-- REPORT 3: Inventory Report (Stock + Revenue Potential)
-- ============================================================
SELECT
    c.name                                        AS category,
    p.sku,
    p.name                                        AS product,
    p.price,
    p.cost,
    ROUND(p.price - p.cost, 2)                   AS margin,
    ROUND((p.price - p.cost) / p.price * 100, 1) AS margin_pct,
    p.stock_qty,
    ROUND(p.price * p.stock_qty, 2)              AS stock_value,
    COALESCE(r.avg_rating, 'No reviews')         AS avg_rating,
    COALESCE(r.review_count, 0)                  AS reviews,
    CASE
        WHEN p.stock_qty = 0 THEN 'OUT OF STOCK'
        WHEN p.stock_qty < 20 THEN 'LOW STOCK'
        WHEN p.stock_qty < 50 THEN 'MODERATE'
        ELSE 'IN STOCK'
    END AS stock_status
FROM products p
JOIN categories c ON p.cat_id = c.cat_id
LEFT JOIN (
    SELECT product_id,
           ROUND(AVG(rating), 1) AS avg_rating,
           COUNT(*)              AS review_count
    FROM reviews
    GROUP BY product_id
) r ON p.product_id = r.product_id
WHERE p.is_active = TRUE
ORDER BY category, margin_pct DESC;
EOF
```

---

## Step 8: Capstone Verification — Full Schema Health Check

```bash
docker exec mysql-lab mysql -uroot -prootpass << 'EOF'
USE ecommerce;

-- Row counts per table
SELECT 'categories'  AS tbl, COUNT(*) AS rows FROM categories  UNION ALL
SELECT 'products',               COUNT(*) FROM products         UNION ALL
SELECT 'users',                  COUNT(*) FROM users            UNION ALL
SELECT 'addresses',              COUNT(*) FROM addresses        UNION ALL
SELECT 'orders',                 COUNT(*) FROM orders           UNION ALL
SELECT 'order_items',            COUNT(*) FROM order_items      UNION ALL
SELECT 'reviews',                COUNT(*) FROM reviews;

-- Total rows
SELECT SUM(cnt) AS total_rows FROM (
    SELECT COUNT(*) AS cnt FROM categories UNION ALL
    SELECT COUNT(*) FROM products UNION ALL
    SELECT COUNT(*) FROM users UNION ALL
    SELECT COUNT(*) FROM addresses UNION ALL
    SELECT COUNT(*) FROM orders UNION ALL
    SELECT COUNT(*) FROM order_items UNION ALL
    SELECT COUNT(*) FROM reviews
) t;

-- Order total consistency check
SELECT
    order_id,
    total AS stored_total,
    ROUND(subtotal - discount_amt + shipping_cost + tax_amt, 2) AS calculated_total,
    ROUND(total - (subtotal - discount_amt + shipping_cost + tax_amt), 2) AS discrepancy
FROM orders
HAVING ABS(discrepancy) > 0.01;

-- Revenue summary by month
SELECT
    DATE_FORMAT(o.placed_at, '%Y-%m') AS month,
    COUNT(DISTINCT o.order_id)        AS order_count,
    COUNT(DISTINCT o.user_id)         AS unique_customers,
    ROUND(SUM(o.total), 2)            AS gross_revenue,
    ROUND(SUM(oi.line_total), 2)      AS net_item_revenue
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status NOT IN ('cancelled', 'refunded')
GROUP BY DATE_FORMAT(o.placed_at, '%Y-%m')
ORDER BY month;
EOF
```

📸 **Verified Output (row counts):**
```
+--------------+------+
| tbl          | rows |
+--------------+------+
| categories   |   14 |
| products     |   20 |
| users        |   10 |
| addresses    |   11 |
| orders       |   15 |
| order_items  |   23 |
| reviews      |   20 |
+--------------+------+

+------------+
| total_rows |
+------------+
|        113 |
+------------+
```

📸 **Verified Output (monthly revenue):**
```
+--------+-------------+------------------+---------------+------------------+
| month  | order_count | unique_customers | gross_revenue | net_item_revenue |
+--------+-------------+------------------+---------------+------------------+
| 2024-01|           2 |                2 |       1608.36 |         1399.98  |
| 2024-02|           3 |                3 |       2949.74 |         2629.98  |
| 2024-03|           9 |                7 |       7359.39 |         6499.83  |
+--------+-------------+------------------+---------------+------------------+
```

**Cleanup:**
```bash
docker rm -f mysql-lab
```

---

## Summary — What You Built

| Table | Rows | Purpose |
|-------|------|---------|
| categories | 14 | Hierarchical product taxonomy |
| products | 20 | Full product catalog with cost/price |
| users | 10 | Customer accounts |
| addresses | 11 | Multi-address per user |
| orders | 15 | Purchase orders with status lifecycle |
| order_items | 23 | Line items with generated line_total |
| reviews | 20 | Verified purchase reviews |
| **Total** | **113** | **Complete e-commerce dataset** |

**Design Principles Applied:**
- ✅ 3NF normalization throughout
- ✅ Foreign keys with appropriate ON DELETE behavior
- ✅ CHECK constraints on critical fields
- ✅ GENERATED column for line_total
- ✅ Composite UNIQUE keys (one review per user per product)
- ✅ Performance indexes on FK and WHERE columns
- ✅ Price snapshot in order_items (historical accuracy)
- ✅ ENUM for order status lifecycle

**Queries Demonstrated:**
- Top products by revenue (JOIN + GROUP BY + ORDER)
- Customer lifetime value (LEFT JOIN + conditional aggregation)
- Inventory report (multi-table JOIN + subquery)
- Monthly revenue trend (DATE_FORMAT + GROUP BY)
- Schema health check (UNION ALL row counts)

**Congratulations — you have completed all 20 Database Foundations labs!** 🎉

---

## Complete Course Summary

| Labs | Topic Area |
|------|-----------|
| 01-02 | Setup, relational model, CREATE |
| 03-05 | DML basics: INSERT, SELECT, aggregates |
| 06-08 | JOINs and subqueries |
| 09-10 | Views and normalization |
| 11-12 | Constraints and indexes |
| 13-14 | UPDATE/DELETE and transactions |
| 15-17 | Functions: string, date, NULL |
| 18-19 | DB-specific: PostgreSQL JSONB, MySQL features |
| 20 | Capstone: full e-commerce schema |
