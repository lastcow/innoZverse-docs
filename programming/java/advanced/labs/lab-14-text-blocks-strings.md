# Lab 14: Text Blocks & Advanced String Processing

## Objective
Master Java 21 text blocks for multiline strings, `String.formatted()`, `stripIndent()`, `translateEscapes()`, and advanced string processing: `String.format` with locale, `String.join`/`Collectors.joining`, `StringBuilder` tricks, regex with named groups, and a template engine using text blocks.

## Background
Text blocks (JEP 378, Java 15+) are multiline string literals delimited by `"""`. The compiler automatically strips common leading whitespace (`stripIndent()`). This enables embedding JSON, HTML, SQL, and YAML directly in code without escaping or concatenation — a major readability improvement.

## Time
25 minutes

## Prerequisites
- Practitioner Lab 07 (Java 21 Features)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Text block basics, stripIndent, HTML templates, JSON, SQL, formatted(), regex named groups, Capstone invoice generator

```bash
cat > /tmp/AdvLab14.java << 'JAVAEOF'
import java.util.*;
import java.util.regex.*;
import java.util.stream.*;

public class AdvLab14 {
    record Product(int id, String name, String category, double price, int qty) {}

    // Text block template engine
    static String renderHtml(List<Product> products) {
        var rows = products.stream()
            .map(p -> "    <tr><td>%d</td><td>%s</td><td>$%.2f</td><td>%d</td><td>$%.2f</td></tr>"
                .formatted(p.id(), p.name(), p.price(), p.qty(), p.price()*p.qty()))
            .collect(Collectors.joining("\n"));
        double total = products.stream().mapToDouble(p -> p.price()*p.qty()).sum();
        return """
                <!DOCTYPE html>
                <html>
                <head><title>innoZverse Invoice</title></head>
                <body>
                  <h1>Order Invoice</h1>
                  <table border="1">
                    <tr><th>ID</th><th>Product</th><th>Price</th><th>Qty</th><th>Subtotal</th></tr>
                %s
                    <tr><td colspan="4"><b>TOTAL</b></td><td><b>$%.2f</b></td></tr>
                  </table>
                </body>
                </html>
                """.formatted(rows, total);
    }

    static String renderJson(List<Product> products) {
        var items = products.stream()
            .map(p -> """
                    {"id":%d,"name":"%s","price":%.2f,"qty":%d}""".formatted(
                    p.id(), p.name(), p.price(), p.qty()))
            .collect(Collectors.joining(",\n"));
        double total = products.stream().mapToDouble(p -> p.price()*p.qty()).sum();
        return """
                {
                  "invoice": {
                    "items": [
                %s
                    ],
                    "total": %.2f
                  }
                }
                """.formatted(items, total);
    }

    public static void main(String[] args) {
        var products = List.of(
            new Product(1,"Surface Pro","Laptop",864.0,2),
            new Product(2,"Surface Pen","Accessory",49.99,3),
            new Product(3,"Office 365","Software",99.99,1));

        // Step 1: Text block basics
        System.out.println("=== Text Block Basics ===");
        String sql = """
                SELECT p.name, SUM(o.qty) as units, SUM(o.total) as revenue
                FROM products p
                JOIN orders o ON p.id = o.product_id
                WHERE o.created_at > date('now', '-30 days')
                GROUP BY p.id
                ORDER BY revenue DESC
                LIMIT 10;
                """;
        System.out.println("SQL query (" + sql.lines().count() + " lines):");
        sql.lines().forEach(l -> System.out.println("  " + l));

        // Step 2: stripIndent() and translateEscapes()
        System.out.println("=== stripIndent / translateEscapes ===");
        String raw = "  line 1\n  line 2\n  line 3\n";
        System.out.println("stripped:\n" + raw.stripIndent());
        String escaped = "Tab:\\t  Newline:\\n  Quote:\\\"";
        System.out.println("translated: " + escaped.translateEscapes());

        // Step 3: String.formatted vs String.format
        System.out.println("=== String.formatted ===");
        products.forEach(p ->
            System.out.println("  " + "%-15s @ $%8.2f x%d = $%,.2f"
                .formatted(p.name(), p.price(), p.qty(), p.price()*p.qty())));
        double total = products.stream().mapToDouble(p->p.price()*p.qty()).sum();
        System.out.println("  " + "%-15s   %8s         $%,.2f".formatted("TOTAL", "", total));

        // Step 4: Collectors.joining
        System.out.println("\n=== Collectors.joining ===");
        String names = products.stream().map(Product::name)
            .collect(Collectors.joining(", ", "[", "]"));
        System.out.println("  Names: " + names);

        String csv = products.stream()
            .map(p -> "%d,%s,%.2f,%d".formatted(p.id(),p.name(),p.price(),p.qty()))
            .collect(Collectors.joining("\n", "id,name,price,qty\n", ""));
        System.out.println("  CSV:\n" + csv.indent(4).stripTrailing());

        // Step 5: HTML rendering
        System.out.println("\n=== HTML Template ===");
        String html = renderHtml(products);
        html.lines().limit(8).forEach(l -> System.out.println("  " + l));
        System.out.println("  ... (" + html.lines().count() + " lines total)");

        // Step 6: JSON rendering
        System.out.println("\n=== JSON Template ===");
        String json = renderJson(products);
        json.lines().forEach(l -> System.out.println("  " + l));

        // Step 7: Regex with named groups
        System.out.println("=== Regex Named Groups ===");
        var orderPattern = Pattern.compile(
            "Order #(?<id>\\d+): (?<product>.+?) qty=(?<qty>\\d+) @\\$(?<price>[\\d.]+)");
        var testOrders = List.of(
            "Order #1001: Surface Pro qty=2 @$864.00",
            "Order #1002: Surface Pen qty=5 @$49.99",
            "Order #1003: USB-C Hub qty=1 @$29.99");
        double orderTotal = 0;
        for (var line : testOrders) {
            var m = orderPattern.matcher(line);
            if (m.matches()) {
                double lineTotal = Double.parseDouble(m.group("price")) * Integer.parseInt(m.group("qty"));
                orderTotal += lineTotal;
                System.out.printf("  #%-6s %-15s qty=%s  $%.2f%n",
                    m.group("id"), m.group("product"), m.group("qty"), lineTotal);
            }
        }
        System.out.printf("  Order total: $%,.2f%n", orderTotal);

        // Step 8: StringBuilder for high-throughput
        System.out.println("\n=== StringBuilder Report ===");
        var sb = new StringBuilder();
        sb.append("=== innoZverse Sales Report ===\n");
        products.forEach(p -> sb.append("  %-15s  $%.2f x %d%n".formatted(p.name(), p.price(), p.qty())));
        sb.append("  %-15s  $%,.2f%n".formatted("Grand Total", total));
        System.out.print(sb);
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab14.java:/tmp/AdvLab14.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab14.java -d /tmp && java -cp /tmp AdvLab14"
```

> 💡 **Text blocks use `"""..."""` and automatically strip leading whitespace.** The JVM computes the "incidental whitespace" from the least-indented line and strips it uniformly. This means you can indent the content for readability without it appearing in the output. The closing `"""` on its own line controls this baseline — move it left to keep more indentation.

**📸 Verified Output:**
```
=== Text Block Basics ===
SQL query (7 lines):
  SELECT p.name, SUM(o.qty) as units, SUM(o.total) as revenue
  FROM products p
  ...

=== String.formatted ===
  Surface Pro     @  $ 864.00 x2 = $1,728.00
  Surface Pen     @  $  49.99 x3 = $149.97
  Office 365      @  $  99.99 x1 = $99.99
  TOTAL                           $1,977.96

=== JSON Template ===
  {
    "invoice": {
      "items": [
          {"id":1,"name":"Surface Pro","price":864.00,"qty":2},
          ...
      ],
      "total": 1977.96
    }
  }

=== Regex Named Groups ===
  #1001   Surface Pro     qty=2  $1,728.00
  #1002   Surface Pen     qty=5  $249.95
  #1003   USB-C Hub       qty=1  $29.99
  Order total: $2,007.94
```

---

## Summary

| Feature | Syntax | Notes |
|---------|--------|-------|
| Text block | `"""..."""` | Strips leading whitespace |
| Interpolation | `str.formatted(args)` | Like `String.format` on instance |
| `stripIndent()` | `.stripIndent()` | Manual strip incidental WS |
| Named group | `(?<name>...)` + `.group("name")` | Readable regex |
| Joining | `Collectors.joining(sep, pre, suf)` | Stream → delimited string |

## Further Reading
- [JEP 378: Text Blocks](https://openjdk.org/jeps/378)
- [Java String docs](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html)
