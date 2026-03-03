# Lab 6: File I/O & NIO.2

## Objective
Master Java file operations using `java.nio.file`: `Path`, `Files`, `Files.walk`, `Files.lines`, `BufferedReader`/`Writer`, CSV read/write, directory trees, copy/move/delete, and file attributes.

## Background
Java NIO.2 (`java.nio.file`) replaced the legacy `java.io.File` API in Java 7. `Path` is immutable and composable; `Files` provides static utilities that are cleaner and more powerful than `File` methods. `Files.lines()` returns a lazy `Stream<String>` — perfect for processing large files without loading them entirely into memory.

## Time
25 minutes

## Prerequisites
- Lab 05 (Concurrency)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Write CSV, read with `Files.lines`, directory tree, BufferedWriter report, copy/move, attributes, Capstone

```bash
cat > /tmp/Lab06.java << 'JAVAEOF'
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.stream.*;

public class Lab06 {
    record Product(int id, String name, double price, int stock) {
        static Product fromCsv(String line) {
            var parts = line.split(",");
            return new Product(Integer.parseInt(parts[0].trim()),
                parts[1].trim(), Double.parseDouble(parts[2].trim()), Integer.parseInt(parts[3].trim()));
        }
        String toCsv() { return id + "," + name + "," + price + "," + stock; }
    }

    public static void main(String[] args) throws Exception {
        Path tmp = Files.createTempDirectory("innozverse_lab06");
        Path csvFile    = tmp.resolve("products.csv");
        Path reportFile = tmp.resolve("report.txt");

        var products = List.of(
            new Product(1, "Surface Pro",  864.0, 15),
            new Product(2, "Surface Pen",   49.99, 80),
            new Product(3, "Office 365",    99.99, 999),
            new Product(4, "USB-C Hub",     29.99, 0),
            new Product(5, "Surface Book", 1299.0, 5)
        );

        // Write CSV
        var lines = new ArrayList<String>();
        lines.add("id,name,price,stock");
        products.forEach(p -> lines.add(p.toCsv()));
        Files.write(csvFile, lines, StandardCharsets.UTF_8);
        System.out.println("Written: " + csvFile.getFileName() + " (" + Files.size(csvFile) + " bytes)");

        // Read CSV with Files.lines (lazy stream)
        List<Product> loaded;
        try (var stream = Files.lines(csvFile, StandardCharsets.UTF_8)) {
            loaded = stream.skip(1).map(Product::fromCsv).toList();
        }
        System.out.println("Loaded " + loaded.size() + " products:");
        loaded.forEach(p -> System.out.printf("  %d  %-15s $%8.2f  stock=%d%n", p.id(), p.name(), p.price(), p.stock()));

        // NIO.2 directory tree
        Path subDir = tmp.resolve("reports/2026");
        Files.createDirectories(subDir);
        Files.writeString(subDir.resolve("march.txt"), "March report\nRevenue: $123,344.21");

        System.out.println("\nDirectory tree:");
        try (var walk = Files.walk(tmp)) {
            walk.forEach(p -> System.out.println("  " + tmp.relativize(p)));
        }

        // BufferedWriter report
        try (var writer = new BufferedWriter(new FileWriter(reportFile.toFile()))) {
            writer.write("=== innoZverse Inventory Report ===\n");
            for (var p : loaded) {
                writer.write(String.format("%-20s $%8.2f  qty=%-5d  value=$%,.2f%n",
                    p.name(), p.price(), p.stock(), p.price() * p.stock()));
            }
            double total = loaded.stream().mapToDouble(p -> p.price() * p.stock()).sum();
            writer.write(String.format("%nTotal inventory value: $%,.2f%n", total));
        }

        System.out.println("\nReport:");
        Files.readAllLines(reportFile).forEach(l -> System.out.println("  " + l));

        // Copy and attributes
        Path backup = tmp.resolve("products_backup.csv");
        Files.copy(csvFile, backup, StandardCopyOption.REPLACE_EXISTING);
        System.out.println("\nCopied: " + backup.getFileName() + " (" + Files.size(backup) + " bytes)");

        var attrs = Files.readAttributes(csvFile, "basic:size,lastModifiedTime");
        System.out.println("Attrs: " + attrs);

        // Cleanup
        try (var walk = Files.walk(tmp)) {
            walk.sorted(Comparator.reverseOrder()).forEach(p -> { try { Files.delete(p); } catch (IOException e) {} });
        }
        System.out.println("\nCleanup done. Dir exists: " + Files.exists(tmp));
    }
}
JAVAEOF
docker run --rm -v /tmp/Lab06.java:/tmp/Lab06.java zchencow/innozverse-java:latest sh -c "javac /tmp/Lab06.java -d /tmp && java -cp /tmp Lab06"
```

> 💡 **`Files.lines()` returns a lazy stream** — it reads the file line-by-line as you consume the stream, not all at once. Always wrap it in `try-with-resources` so the underlying file handle is closed when the stream terminates. For large log files or CSVs (millions of rows), this is the memory-efficient approach.

**📸 Verified Output:**
```
Written: products.csv (133 bytes)
Loaded 5 products:
  1  Surface Pro     $  864.00  stock=15
  2  Surface Pen     $   49.99  stock=80
  3  Office 365      $   99.99  stock=999
  4  USB-C Hub       $   29.99  stock=0
  5  Surface Book    $ 1299.00  stock=5

Directory tree:
  
  products.csv
  reports
  reports/2026
  reports/2026/march.txt

Report:
  === innoZverse Inventory Report ===
  Surface Pro          $  864.00  qty=15     value=$12,960.00
  ...
  Total inventory value: $123,344.21

Copied: products_backup.csv (133 bytes)
Cleanup done. Dir exists: false
```

---

## Summary

| API | Purpose |
|-----|---------|
| `Path.of("...")` / `Paths.get(...)` | Create path object |
| `Files.write(path, lines)` | Write all lines |
| `Files.readAllLines(path)` | Read all lines into `List<String>` |
| `Files.lines(path)` | Lazy `Stream<String>` |
| `Files.createDirectories(path)` | Create dir tree |
| `Files.walk(path)` | Recursive directory stream |
| `Files.copy(src, dst, options)` | Copy file |
| `Files.size(path)` | File size in bytes |

## Further Reading
- [NIO.2 Tutorial](https://docs.oracle.com/javase/tutorial/essential/io/fileio.html)
- [Files JavaDoc](https://docs.oracle.com/en/java/docs/api/java.base/java/nio/file/Files.html)
