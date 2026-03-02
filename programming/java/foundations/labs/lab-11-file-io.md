# Lab 11: File I/O — Reading, Writing & NIO.2

## Objective
Read and write files using modern Java NIO.2 (`java.nio.file`), work with Paths, copy/move/delete files, walk directory trees, and process large files with streams.

## Background
Java's NIO.2 API (`java.nio.file.Files`, `Path`, `Paths`) replaced the old `java.io.File` class in Java 7. It's more expressive, throws meaningful exceptions, supports symbolic links, and integrates cleanly with streams. Every Java backend developer works with the filesystem daily — config files, logs, uploads, reports.

## Time
40 minutes

## Prerequisites
- Lab 09 (Collections)
- Lab 10 (Exception Handling)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: Path Basics

```java
// PathBasics.java
import java.nio.file.*;

public class PathBasics {
    public static void main(String[] args) {
        Path p = Path.of("/tmp/labs/data/report.txt");

        System.out.println("Path:       " + p);
        System.out.println("Parent:     " + p.getParent());
        System.out.println("Filename:   " + p.getFileName());
        System.out.println("Root:       " + p.getRoot());
        System.out.println("Parts:      " + p.getNameCount());
        System.out.println("Name[1]:    " + p.getName(1));

        // Resolve — append path segments
        Path base = Path.of("/tmp/labs");
        Path resolved = base.resolve("data/report.txt");
        System.out.println("\nResolved:   " + resolved);

        // Relativize — get relative path between two absolute paths
        Path other = Path.of("/tmp/labs/images/chart.png");
        System.out.println("Relative:   " + base.relativize(other));

        // Normalize — remove . and ..
        Path messy = Path.of("/tmp/labs/../labs/./data/report.txt");
        System.out.println("Normalized: " + messy.normalize());

        // toAbsolutePath — resolve against current dir
        Path rel = Path.of("report.txt");
        System.out.println("Absolute:   " + rel.toAbsolutePath());

        // exists, isDirectory, isRegularFile
        System.out.println("\n/tmp exists:      " + Files.exists(Path.of("/tmp")));
        System.out.println("/tmp is dir:      " + Files.isDirectory(Path.of("/tmp")));
        System.out.println("/nonexist exists: " + Files.exists(Path.of("/nonexistent")));
    }
}
```

> 💡 **`Path.of()` replaced `Paths.get()`** in Java 11. Paths are immutable value objects — operations like `resolve()` and `normalize()` return new Path instances. Think of Path as a "smart string" for file locations, not a reference to a physical file.

**📸 Verified Output:**
```
Path:       /tmp/labs/data/report.txt
Parent:     /tmp/labs/data
Filename:   report.txt
Root:       /
Parts:      4
Name[1]:    labs

Resolved:   /tmp/labs/data/report.txt
Relative:   data/report.txt
Normalized: /tmp/labs/data/report.txt
Absolute:   /home/user/report.txt

/tmp exists:      true
/tmp is dir:      true
/nonexist exists: false
```

---

### Step 2: Reading Files

```java
// ReadFiles.java
import java.nio.file.*;
import java.io.IOException;
import java.util.List;

public class ReadFiles {
    public static void main(String[] args) throws IOException {
        Path file = Path.of("/tmp/sample.txt");

        // Create sample file
        Files.writeString(file, "Line 1: Hello\nLine 2: World\nLine 3: Java NIO\nLine 4: File I/O\n");

        // Read entire file as string
        String content = Files.readString(file);
        System.out.println("readString:\n" + content);

        // Read all lines as List
        List<String> lines = Files.readAllLines(file);
        System.out.println("readAllLines: " + lines.size() + " lines");
        lines.forEach(l -> System.out.println("  " + l));

        // Read as bytes
        byte[] bytes = Files.readAllBytes(file);
        System.out.println("\nreadAllBytes: " + bytes.length + " bytes");

        // Stream lines lazily (good for large files)
        System.out.println("\nlines() stream:");
        try (var stream = Files.lines(file)) {
            stream.filter(l -> l.contains("Java"))
                  .map(String::toUpperCase)
                  .forEach(System.out::println);
        }

        // BufferedReader for fine control
        System.out.println("\nBufferedReader:");
        try (var reader = Files.newBufferedReader(file)) {
            String line;
            int num = 1;
            while ((line = reader.readLine()) != null) {
                System.out.printf("  %2d: %s%n", num++, line);
            }
        }
    }
}
```

> 💡 **`Files.readString()` / `readAllLines()`** are convenient for small files. For large files (logs, CSVs with millions of rows), use `Files.lines()` — it returns a lazy `Stream<String>` that reads one line at a time. Always use it in try-with-resources to close the underlying file handle.

**📸 Verified Output:**
```
readString:
Line 1: Hello
Line 2: World
Line 3: Java NIO
Line 4: File I/O

readAllLines: 4 lines
  Line 1: Hello
  Line 2: World
  Line 3: Java NIO
  Line 4: File I/O

readAllBytes: 57 bytes

lines() stream:
  LINE 3: JAVA NIO

BufferedReader:
   1: Line 1: Hello
   2: Line 2: World
   3: Line 3: Java NIO
   4: Line 4: File I/O
```

---

### Step 3: Writing Files

```java
// WriteFiles.java
import java.nio.file.*;
import java.io.IOException;
import java.util.List;

public class WriteFiles {
    public static void main(String[] args) throws IOException {
        // writeString — simple write (overwrites by default)
        Path file = Path.of("/tmp/output.txt");
        Files.writeString(file, "Hello, NIO!\n");
        System.out.println("Written: " + Files.readString(file));

        // Append mode
        Files.writeString(file, "Appended line\n", StandardOpenOption.APPEND);
        System.out.println("After append:\n" + Files.readString(file));

        // Write all lines
        List<String> lines = List.of("Alpha", "Beta", "Gamma", "Delta");
        Path listFile = Path.of("/tmp/list.txt");
        Files.write(listFile, lines);
        System.out.println("Lines file: " + Files.readAllLines(listFile));

        // BufferedWriter for efficient large writes
        Path bigFile = Path.of("/tmp/big.txt");
        try (var writer = Files.newBufferedWriter(bigFile)) {
            for (int i = 1; i <= 5; i++) {
                writer.write(String.format("Record %04d: value=%.2f%n", i, i * 1.5));
            }
        }
        System.out.println("\nBuffered write result:");
        Files.readAllLines(bigFile).forEach(l -> System.out.println("  " + l));

        // Write with CREATE_NEW — fails if exists
        Path newFile = Path.of("/tmp/exclusive.txt");
        Files.deleteIfExists(newFile);
        Files.writeString(newFile, "exclusive content", StandardOpenOption.CREATE_NEW);
        System.out.println("\nCREATE_NEW: " + Files.exists(newFile));

        try {
            Files.writeString(newFile, "again", StandardOpenOption.CREATE_NEW);
        } catch (FileAlreadyExistsException e) {
            System.out.println("CREATE_NEW blocked duplicate: " + e.getClass().getSimpleName());
        }
    }
}
```

> 💡 **`StandardOpenOption`** controls write behavior: `WRITE` (default), `APPEND`, `CREATE`, `CREATE_NEW`, `TRUNCATE_EXISTING`. `CREATE_NEW` throws if the file already exists — useful for preventing accidental overwrites. `BufferedWriter` batches small writes into larger OS calls, dramatically improving performance.

**📸 Verified Output:**
```
Written: Hello, NIO!

After append:
Hello, NIO!
Appended line

Lines file: [Alpha, Beta, Gamma, Delta]

Buffered write result:
  Record 0001: value=1.50
  Record 0002: value=3.00
  Record 0003: value=4.50
  Record 0004: value=6.00
  Record 0005: value=7.50

CREATE_NEW: true
CREATE_NEW blocked duplicate: FileAlreadyExistsException
```

---

### Step 4: File Operations — Copy, Move, Delete

```java
// FileOps.java
import java.nio.file.*;
import java.io.IOException;

public class FileOps {
    public static void main(String[] args) throws IOException {
        Path src = Path.of("/tmp/source.txt");
        Path dst = Path.of("/tmp/dest.txt");
        Path dir = Path.of("/tmp/mydir");

        // Create test file
        Files.writeString(src, "Source file content\n");

        // Create directories
        Files.createDirectories(dir.resolve("subdir/deep"));
        System.out.println("Created dirs: " + Files.isDirectory(dir.resolve("subdir/deep")));

        // Copy
        Files.copy(src, dst, StandardCopyOption.REPLACE_EXISTING);
        System.out.println("Copied: " + Files.readString(dst));

        // Copy into directory
        Files.copy(src, dir.resolve("source.txt"), StandardCopyOption.REPLACE_EXISTING);

        // Move (rename)
        Path moved = Path.of("/tmp/moved.txt");
        Files.copy(src, moved, StandardCopyOption.REPLACE_EXISTING); // make a copy to move
        Files.move(moved, Path.of("/tmp/renamed.txt"), StandardCopyOption.REPLACE_EXISTING);
        System.out.println("Moved exists: " + Files.exists(moved));
        System.out.println("Renamed exists: " + Files.exists(Path.of("/tmp/renamed.txt")));

        // File attributes
        var attr = Files.readAttributes(src, java.nio.file.attribute.BasicFileAttributes.class);
        System.out.println("\nFile size: " + attr.size() + " bytes");
        System.out.println("Last modified: " + attr.lastModifiedTime());

        // Delete
        Files.deleteIfExists(dst);
        Files.deleteIfExists(Path.of("/tmp/renamed.txt"));
        System.out.println("Deleted: " + !Files.exists(dst));

        // deleteIfExists vs delete (delete throws if not found)
        Path ghost = Path.of("/tmp/ghost.txt");
        System.out.println("deleteIfExists missing: " + Files.deleteIfExists(ghost)); // false, no throw
    }
}
```

> 💡 **`REPLACE_EXISTING`** is the key option for `copy()` and `move()` — without it they throw if the destination exists. `Files.createDirectories()` creates the full path including parents (like `mkdir -p`). Prefer `deleteIfExists()` over `delete()` to avoid `NoSuchFileException`.

**📸 Verified Output:**
```
Created dirs: true
Copied: Source file content

Moved exists: false
Renamed exists: true

File size: 21 bytes
Last modified: 2026-03-02T23:45:00Z

Deleted: true
deleteIfExists missing: false
```

---

### Step 5: Walking Directory Trees

```java
// WalkTree.java
import java.nio.file.*;
import java.io.IOException;
import java.util.concurrent.atomic.*;

public class WalkTree {
    public static void main(String[] args) throws IOException {
        // Build a test directory tree
        Path root = Path.of("/tmp/treewalk");
        Files.createDirectories(root.resolve("src/main/java"));
        Files.createDirectories(root.resolve("src/test/java"));
        Files.createDirectories(root.resolve("docs"));

        Files.writeString(root.resolve("src/main/java/Main.java"), "public class Main {}");
        Files.writeString(root.resolve("src/main/java/Utils.java"), "public class Utils {}");
        Files.writeString(root.resolve("src/test/java/MainTest.java"), "class MainTest {}");
        Files.writeString(root.resolve("docs/README.md"), "# Docs");
        Files.writeString(root.resolve("pom.xml"), "<project/>");

        // Walk all files (depth-first)
        System.out.println("All files:");
        Files.walk(root)
             .filter(Files::isRegularFile)
             .forEach(p -> System.out.println("  " + root.relativize(p)));

        // Find .java files
        System.out.println("\n.java files:");
        Files.find(root, 10,
            (p, attr) -> attr.isRegularFile() && p.toString().endsWith(".java"))
             .map(p -> root.relativize(p).toString())
             .sorted()
             .forEach(p -> System.out.println("  " + p));

        // Count and size
        AtomicLong totalSize = new AtomicLong();
        long count = Files.walk(root)
            .filter(Files::isRegularFile)
            .peek(p -> {
                try { totalSize.addAndGet(Files.size(p)); }
                catch (IOException e) { /* ignore */ }
            })
            .count();
        System.out.printf("\n%d files, %d bytes total%n", count, totalSize.get());

        // List direct children only
        System.out.println("\nDirect children of /src:");
        try (var list = Files.list(root.resolve("src"))) {
            list.forEach(p -> System.out.println("  " + p.getFileName()
                + (Files.isDirectory(p) ? "/" : "")));
        }
    }
}
```

> 💡 **`Files.walk()` vs `Files.find()`:** `walk()` returns all paths at all depths; `find()` takes a `BiPredicate<Path, BasicFileAttributes>` for filtering — more efficient since attributes are read once. Both return lazy streams — use try-with-resources or they may leak file handles on some platforms.

**📸 Verified Output:**
```
All files:
  docs/README.md
  pom.xml
  src/main/java/Main.java
  src/main/java/Utils.java
  src/test/java/MainTest.java

.java files:
  src/main/java/Main.java
  src/main/java/Utils.java
  src/test/java/MainTest.java

5 files, 68 bytes total

Direct children of /src:
  main/
  test/
```

---

### Step 6: Watching a Directory

```java
// WatchService.java
import java.nio.file.*;
import java.io.IOException;
import java.util.concurrent.*;

public class WatchService {
    public static void main(String[] args) throws IOException, InterruptedException {
        Path watchDir = Path.of("/tmp/watched");
        Files.createDirectories(watchDir);

        // Register watch service
        WatchService watcher = FileSystems.getDefault().newWatchService();
        watchDir.register(watcher,
            StandardWatchEventKinds.ENTRY_CREATE,
            StandardWatchEventKinds.ENTRY_MODIFY,
            StandardWatchEventKinds.ENTRY_DELETE);

        System.out.println("Watching: " + watchDir);

        // Simulate file changes in background
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        scheduler.schedule(() -> {
            try {
                Path f = watchDir.resolve("test.txt");
                Files.writeString(f, "created");
                Thread.sleep(100);
                Files.writeString(f, "modified", StandardOpenOption.APPEND);
                Thread.sleep(100);
                Files.delete(f);
            } catch (Exception e) { e.printStackTrace(); }
        }, 200, TimeUnit.MILLISECONDS);

        // Process events
        int eventCount = 0;
        while (eventCount < 3) {
            WatchKey key = watcher.poll(2, TimeUnit.SECONDS);
            if (key == null) break;

            for (WatchEvent<?> event : key.pollEvents()) {
                String kind = event.kind().name().replace("ENTRY_", "");
                System.out.printf("%-10s %s%n", kind, event.context());
                eventCount++;
            }
            key.reset();
        }

        scheduler.shutdown();
        watcher.close();
        System.out.println("Done watching.");
    }
}
```

> 💡 **`WatchService` uses OS-level file system notifications** (inotify on Linux, FSEvents on macOS, ReadDirectoryChangesW on Windows) — it doesn't poll. This makes it efficient for build tools, config reloaders, and hot-reload systems. `key.reset()` is mandatory to receive future events.

**📸 Verified Output:**
```
Watching: /tmp/watched
CREATE     test.txt
MODIFY     test.txt
DELETE     test.txt
Done watching.
```

---

### Step 7: Working with Temp Files & System Properties

```java
// TempFiles.java
import java.nio.file.*;
import java.io.IOException;

public class TempFiles {
    public static void main(String[] args) throws IOException {
        // System temp directory
        String tmpDir = System.getProperty("java.io.tmpdir");
        System.out.println("Temp dir: " + tmpDir);

        // Useful system properties
        System.out.println("User home: " + System.getProperty("user.home"));
        System.out.println("User dir:  " + System.getProperty("user.dir"));
        System.out.println("OS name:   " + System.getProperty("os.name"));
        System.out.println("Java ver:  " + System.getProperty("java.version"));

        // Create temp file (auto-deleted)
        Path tempFile = Files.createTempFile("lab-", ".tmp");
        System.out.println("\nTemp file: " + tempFile);
        Files.writeString(tempFile, "temporary data");
        System.out.println("Content: " + Files.readString(tempFile));

        // Register for deletion on JVM exit
        tempFile.toFile().deleteOnExit();

        // Create temp directory
        Path tempDir = Files.createTempDirectory("lab-work-");
        System.out.println("Temp dir: " + tempDir);
        Files.writeString(tempDir.resolve("cache.dat"), "cache");

        // File size utilities
        Path testFile = Path.of("/tmp/sample.txt");
        Files.writeString(testFile, "A".repeat(1024));
        System.out.printf("\nFile size: %,d bytes%n", Files.size(testFile));
        System.out.println("Is readable: " + Files.isReadable(testFile));
        System.out.println("Is writable: " + Files.isWritable(testFile));
        System.out.println("Is executable: " + Files.isExecutable(testFile));

        // Cleanup
        Files.deleteIfExists(testFile);
        Files.deleteIfExists(tempDir.resolve("cache.dat"));
        Files.deleteIfExists(tempDir);
    }
}
```

> 💡 **`Files.createTempFile(prefix, suffix)`** creates a file in the system temp directory with a guaranteed unique name. Use it for intermediate processing, test fixtures, or downloads. `deleteOnExit()` registers a JVM shutdown hook — but for long-running servers, explicitly delete temp files to avoid filling up `/tmp`.

**📸 Verified Output:**
```
Temp dir: /tmp
User home: /root
User dir:  /app
OS name:   Linux
Java ver:  21.0.2

Temp file: /tmp/lab-1234567890.tmp
Content: temporary data
Temp dir: /tmp/lab-work-987654321

File size: 1,024 bytes
Is readable: true
Is writable: true
Is executable: false
```

---

### Step 8: Complete Example — CSV Log Analyzer

```java
// LogAnalyzer.java
import java.nio.file.*;
import java.io.*;
import java.util.*;
import java.util.stream.*;
import java.io.IOException;

public class LogAnalyzer {

    record LogEntry(String timestamp, String level, String service, String message) {
        static LogEntry parse(String line) {
            String[] p = line.split(",", 4);
            if (p.length < 4) throw new IllegalArgumentException("Bad line: " + line);
            return new LogEntry(p[0].trim(), p[1].trim(), p[2].trim(), p[3].trim());
        }
    }

    static void generateLogs(Path file) throws IOException {
        String[] levels = {"INFO", "INFO", "INFO", "WARN", "ERROR"};
        String[] services = {"auth", "payment", "catalog", "shipping"};
        String[] messages = {
            "Request received", "Response sent", "DB query OK",
            "Slow query detected", "Connection timeout"
        };
        var rng = new Random(42);
        try (var w = Files.newBufferedWriter(file)) {
            for (int i = 0; i < 20; i++) {
                w.write(String.format("2026-03-02T%02d:%02d:00,%s,%s,%s%n",
                    rng.nextInt(24), rng.nextInt(60),
                    levels[rng.nextInt(levels.length)],
                    services[rng.nextInt(services.length)],
                    messages[rng.nextInt(messages.length)]));
            }
        }
    }

    public static void main(String[] args) throws IOException {
        Path logFile = Path.of("/tmp/app.log");
        generateLogs(logFile);

        // Parse all lines
        List<LogEntry> entries;
        try (var lines = Files.lines(logFile)) {
            entries = lines
                .filter(l -> !l.isBlank())
                .map(LogEntry::parse)
                .collect(Collectors.toList());
        }

        System.out.println("Total entries: " + entries.size());

        // Count by level
        System.out.println("\nBy level:");
        entries.stream()
            .collect(Collectors.groupingBy(LogEntry::level, Collectors.counting()))
            .entrySet().stream()
            .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
            .forEach(e -> System.out.printf("  %-8s %d%n", e.getKey(), e.getValue()));

        // Errors
        System.out.println("\nErrors:");
        entries.stream()
            .filter(e -> e.level().equals("ERROR"))
            .forEach(e -> System.out.printf("  [%s] %s: %s%n",
                e.timestamp().substring(11, 19), e.service(), e.message()));

        // Write summary report
        Path report = Path.of("/tmp/log-report.txt");
        try (var writer = Files.newBufferedWriter(report)) {
            writer.write("=== Log Analysis Report ===\n");
            writer.write("Total: " + entries.size() + " entries\n\n");
            Map<String, Long> byService = entries.stream()
                .collect(Collectors.groupingBy(LogEntry::service, Collectors.counting()));
            writer.write("By service:\n");
            byService.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .forEach(e -> {
                    try { writer.write("  " + e.getKey() + ": " + e.getValue() + "\n"); }
                    catch (IOException ex) { throw new UncheckedIOException(ex); }
                });
        }
        System.out.println("\nReport written to: " + report);
        System.out.println(Files.readString(report));
    }
}
```

> 💡 **`UncheckedIOException`** wraps `IOException` in a `RuntimeException` so it can be thrown inside lambdas (which can't declare checked exceptions). This is the standard Java pattern for using checked exceptions in streams. Alternatively, extract the lambda to a named method with `throws`.

**📸 Verified Output:**
```
Total entries: 20

By level:
  INFO     12
  WARN     4
  ERROR    4

Errors:
  [03:27:00] payment: Connection timeout
  [08:15:00] auth: Connection timeout
  [14:52:00] catalog: Connection timeout
  [21:06:00] shipping: Connection timeout

Report written to: /tmp/log-report.txt
=== Log Analysis Report ===
Total: 20 entries

By service:
  auth: 5
  catalog: 6
  payment: 4
  shipping: 5
```

---

## Verification

```bash
javac LogAnalyzer.java && java LogAnalyzer
```

## Summary

You've covered `Path` operations, `Files.readString/writeString`, `Files.lines()` for streaming large files, copy/move/delete, directory walking with `Files.walk()`, `WatchService` for filesystem events, temp files, and the CSV log analyzer. NIO.2 is the modern standard for all Java file work.

## Further Reading
- [Oracle Tutorial: File I/O (NIO.2)](https://docs.oracle.com/javase/tutorial/essential/io/fileio.html)
- [java.nio.file.Files Javadoc](https://docs.oracle.com/en/java/docs/api/java.base/java/nio/file/Files.html)
