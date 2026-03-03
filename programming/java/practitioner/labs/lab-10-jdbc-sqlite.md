# Lab 10: JDBC & SQLite — Transactional Persistence

## Objective
Use JDBC with SQLite to build a transactional product/order system: schema creation, parameterized `PreparedStatement`, batch inserts, transactions with rollback, `JOIN` queries, aggregate SQL, and a simple Repository pattern.

## Background
JDBC (Java Database Connectivity) is Java's standard API for relational database access. `PreparedStatement` prevents SQL injection by separating SQL structure from data. Transactions (`setAutoCommit(false)` + `commit()`/`rollback()`) ensure atomicity — either all operations in a unit succeed, or none do.

## Time
30 minutes

## Prerequisites
- Lab 09 (Testing)

## Tools
- Docker: `zchencow/innozverse-java:latest`
- SQLite JDBC (downloaded via Maven during lab)

---

## Lab Instructions

### Steps 1–8: Schema, batch insert, transactional order, JOIN query, aggregate SQL, Repository, rollback, Capstone

```bash
# Download sqlite-jdbc (one-time)
docker run --rm zchencow/innozverse-java:latest sh -c "
mvn dependency:get \
  -Dartifact=org.xerial:sqlite-jdbc:3.47.0.0 \
  -Dmaven.repo.local=/tmp/repo -q 2>/dev/null && \
echo 'JDBC ready: ' && ls /tmp/repo/org/xerial/sqlite-jdbc/3.47.0.0/*.jar"
```

```bash
cat > /tmp/Lab10.java << 'JAVAEOF'
import java.sql.*;
import java.util.*;

public class Lab10 {
    record Product(int id, String name, String category, double price, int stock) {}

    static Connection connect() throws SQLException {
        return DriverManager.getConnection("jdbc:sqlite::memory:");
    }

    static void setupSchema(Connection conn) throws SQLException {
        conn.setAutoCommit(false);
        try (var st = conn.createStatement()) {
            st.executeUpdate("""
                CREATE TABLE products(
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL, price REAL NOT NULL CHECK(price>0),
                    stock INTEGER NOT NULL DEFAULT 0)
                """);
            st.executeUpdate("""
                CREATE TABLE orders(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER REFERENCES products(id),
                    qty INTEGER NOT NULL CHECK(qty>0), total REAL NOT NULL,
                    placed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
                """);
            st.executeUpdate("CREATE INDEX idx_orders_product ON orders(product_id)");
        }
        conn.commit();
    }

    static void seed(Connection conn) throws SQLException {
        var sql = "INSERT INTO products(id,name,category,price,stock) VALUES(?,?,?,?,?)";
        try (var ps = conn.prepareStatement(sql)) {
            Object[][] data = {
                {1,"Surface Pro","Laptop",864.0,15},{2,"Surface Pen","Accessory",49.99,80},
                {3,"Office 365","Software",99.99,999},{4,"USB-C Hub","Hardware",29.99,0},
                {5,"Surface Book","Laptop",1299.0,5}
            };
            for (var row : data) {
                ps.setInt(1,(int)row[0]); ps.setString(2,(String)row[1]);
                ps.setString(3,(String)row[2]); ps.setDouble(4,(double)row[3]);
                ps.setInt(5,(int)row[4]); ps.addBatch();
            }
            int[] counts = ps.executeBatch();
            conn.commit();
            System.out.println("Seeded: " + counts.length + " products");
        }
    }

    static void placeOrder(Connection conn, int productId, int qty) throws SQLException {
        conn.setAutoCommit(false);
        try {
            try (var ps = conn.prepareStatement("SELECT name,price,stock FROM products WHERE id=?")) {
                ps.setInt(1, productId);
                var rs = ps.executeQuery();
                if (!rs.next()) throw new SQLException("Product " + productId + " not found");
                String name = rs.getString("name");
                double price = rs.getDouble("price");
                int stock = rs.getInt("stock");
                if (stock < qty) throw new SQLException("Insufficient stock for " + name + ": " + stock + " < " + qty);
                double total = price * qty;
                try (var ps2 = conn.prepareStatement("UPDATE products SET stock=stock-? WHERE id=?")) {
                    ps2.setInt(1, qty); ps2.setInt(2, productId); ps2.executeUpdate();
                }
                try (var ps3 = conn.prepareStatement("INSERT INTO orders(product_id,qty,total) VALUES(?,?,?)")) {
                    ps3.setInt(1, productId); ps3.setInt(2, qty); ps3.setDouble(3, total); ps3.executeUpdate();
                }
                conn.commit();
                System.out.printf("  \u2713 Order: %dx%s $%.2f (stock->%d)%n", qty, name, total, stock-qty);
            }
        } catch (SQLException e) {
            conn.rollback();
            System.out.println("  \u2717 Rolled back: " + e.getMessage());
        }
    }

    static void report(Connection conn) throws SQLException {
        System.out.println("\n=== Inventory ===");
        try (var rs = conn.createStatement().executeQuery(
                "SELECT id,name,category,price,stock FROM products ORDER BY price DESC")) {
            while (rs.next())
                System.out.printf("  %d  %-15s %-10s $%8.2f  stock=%d%n",
                    rs.getInt("id"), rs.getString("name"), rs.getString("category"),
                    rs.getDouble("price"), rs.getInt("stock"));
        }
        System.out.println("\n=== Category Summary ===");
        try (var rs = conn.createStatement().executeQuery(
                "SELECT category, COUNT(*) n, SUM(price*stock) value FROM products GROUP BY category")) {
            while (rs.next())
                System.out.printf("  %-12s count=%d  value=$%,.2f%n",
                    rs.getString("category"), rs.getInt("n"), rs.getDouble("value"));
        }
        System.out.println("\n=== Orders (JOIN) ===");
        try (var rs = conn.createStatement().executeQuery(
                "SELECT o.id, p.name, o.qty, o.total FROM orders o JOIN products p ON p.id=o.product_id")) {
            while (rs.next())
                System.out.printf("  #%d  %s  qty=%d  total=$%.2f%n",
                    rs.getInt("id"), rs.getString("name"), rs.getInt("qty"), rs.getDouble("total"));
        }
    }

    public static void main(String[] args) throws Exception {
        Class.forName("org.sqlite.JDBC");
        try (var conn = connect()) {
            setupSchema(conn);
            seed(conn);
            System.out.println("\n--- Orders ---");
            placeOrder(conn, 1, 3);
            placeOrder(conn, 2, 10);
            placeOrder(conn, 4, 1);   // OOS - rollback
            placeOrder(conn, 99, 1);  // not found - rollback
            report(conn);
        }
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab10.java:/tmp/Lab10.java zchencow/innozverse-java:latest sh -c "
mvn dependency:get -Dartifact=org.xerial:sqlite-jdbc:3.47.0.0 -Dmaven.repo.local=/tmp/repo -q 2>/dev/null
JDBC=/tmp/repo/org/xerial/sqlite-jdbc/3.47.0.0/sqlite-jdbc-3.47.0.0.jar
javac -cp \$JDBC /tmp/Lab10.java -d /tmp && java -cp /tmp:\$JDBC Lab10"
```

> 💡 **Always use `PreparedStatement`, never `Statement` with string concatenation.** `PreparedStatement` sends the SQL structure to the database driver separately from the data values, so user-supplied data can never be interpreted as SQL commands. `conn.prepareStatement("... WHERE id=?")` followed by `ps.setInt(1, id)` is the correct pattern — the `?` is a placeholder, not string substitution.

**📸 Verified Output:**
```
Seeded: 5 products

--- Orders ---
  ✓ Order: 3xSurface Pro $2592.00 (stock->12)
  ✓ Order: 10xSurface Pen $499.90 (stock->70)
  ✗ Rolled back: Insufficient stock for USB-C Hub: 0 < 1
  ✗ Rolled back: Product 99 not found

=== Inventory ===
  5  Surface Book    Laptop     $ 1299.00  stock=5
  1  Surface Pro     Laptop     $  864.00  stock=12
  3  Office 365      Software   $   99.99  stock=999
  2  Surface Pen     Accessory  $   49.99  stock=70
  4  USB-C Hub       Hardware   $   29.99  stock=0

=== Category Summary ===
  Accessory    count=1  value=$3,499.30
  Hardware     count=1  value=$0.00
  Laptop       count=2  value=$16,863.00
  Software     count=1  value=$99,890.01

=== Orders (JOIN) ===
  #1  Surface Pro  qty=3  total=$2592.00
  #2  Surface Pen  qty=10  total=$499.90
```

---

## Summary

| JDBC concept | API |
|--------------|-----|
| Connect | `DriverManager.getConnection(url)` |
| Create statement | `conn.prepareStatement(sql)` |
| Set parameters | `ps.setInt(1, val)`, `ps.setString(2, val)` |
| Execute query | `ps.executeQuery()` → `ResultSet` |
| Execute update | `ps.executeUpdate()` → rows affected |
| Batch insert | `ps.addBatch()` + `ps.executeBatch()` |
| Transaction | `setAutoCommit(false)` + `commit()`/`rollback()` |

## Further Reading
- [JDBC Tutorial](https://docs.oracle.com/javase/tutorial/jdbc/)
- [SQLite JDBC](https://github.com/xerial/sqlite-jdbc)
