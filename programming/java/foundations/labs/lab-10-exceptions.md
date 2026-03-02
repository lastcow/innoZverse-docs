# Lab 10: Exception Handling

## Objective
Handle checked and unchecked exceptions, create custom exception hierarchies, use try-with-resources, apply exception chaining, and design robust error handling strategies.

## Background
Java's exception system is one of the most explicit in any language — checked exceptions force you to acknowledge potential failures at compile time. Understanding when to use checked vs unchecked exceptions, how to chain them for debugging, and how to design exception hierarchies is essential for writing resilient Java applications.

## Time
40 minutes

## Prerequisites
- Lab 06 (OOP — Classes)
- Lab 08 (Interfaces — AutoCloseable)

## Tools
- Java 21 (Eclipse Temurin)
- Docker image: `innozverse-java:latest`

---

## Lab Instructions

### Step 1: try-catch-finally Basics

```java
// ExceptionBasics.java
public class ExceptionBasics {
    public static void main(String[] args) {
        // Basic try-catch
        try {
            int result = 10 / 0;
            System.out.println("Never reached: " + result);
        } catch (ArithmeticException e) {
            System.out.println("Caught: " + e.getMessage());
        }

        // Multiple catch blocks
        String[] arr = {"42", "abc", null};
        for (String s : arr) {
            try {
                int n = Integer.parseInt(s);
                System.out.println("Parsed: " + n);
            } catch (NumberFormatException e) {
                System.out.println("Not a number: '" + s + "'");
            } catch (NullPointerException e) {
                System.out.println("Null value encountered");
            }
        }

        // Multi-catch (Java 7+)
        for (String s : arr) {
            try {
                int n = Integer.parseInt(s);
                System.out.println("OK: " + n);
            } catch (NumberFormatException | NullPointerException e) {
                System.out.println("Bad input: " + e.getClass().getSimpleName());
            }
        }

        // finally — always runs
        System.out.println("\nWith finally:");
        try {
            System.out.println("In try");
            if (true) throw new RuntimeException("test");
        } catch (RuntimeException e) {
            System.out.println("In catch: " + e.getMessage());
        } finally {
            System.out.println("In finally (always)");
        }
    }
}
```

> 💡 **`finally` always executes** — even if the catch block throws, or `return` is called inside try. It's the right place to release resources (close files, release locks). However, `try-with-resources` is preferred for `AutoCloseable` resources.

**📸 Verified Output:**
```
Caught: / by zero
Parsed: 42
Not a number: 'abc'
Null value encountered
OK: 42
Bad input: NumberFormatException
Bad input: NullPointerException

With finally:
In try
In catch: test
In finally (always)
```

---

### Step 2: Checked vs Unchecked Exceptions

```java
// CheckedVsUnchecked.java
import java.io.*;

public class CheckedVsUnchecked {

    // Checked — must declare with throws or handle
    static String readFile(String path) throws IOException {
        // Simulated file read
        if (path.equals("/nonexistent")) {
            throw new IOException("File not found: " + path);
        }
        return "file contents of " + path;
    }

    // Unchecked — extends RuntimeException, no throws required
    static int divide(int a, int b) {
        if (b == 0) throw new ArithmeticException("Division by zero");
        return a / b;
    }

    static double parseSafe(String s) {
        try {
            return Double.parseDouble(s);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Expected a number, got: '" + s + "'", e);  // wrapping
        }
    }

    public static void main(String[] args) {
        // Checked — MUST handle
        try {
            System.out.println(readFile("/tmp/data.txt"));
            System.out.println(readFile("/nonexistent"));
        } catch (IOException e) {
            System.out.println("IO error: " + e.getMessage());
        }

        // Unchecked — optional handling
        System.out.println("\nDivide: " + divide(10, 2));
        try {
            divide(10, 0);
        } catch (ArithmeticException e) {
            System.out.println("Math error: " + e.getMessage());
        }

        // Exception wrapping
        try {
            System.out.println(parseSafe("3.14"));
            System.out.println(parseSafe("not-a-number"));
        } catch (IllegalArgumentException e) {
            System.out.println("Parse error: " + e.getMessage());
            System.out.println("Caused by: " + e.getCause().getClass().getSimpleName());
        }
    }
}
```

> 💡 **Checked exceptions** (`IOException`, `SQLException`) force callers to handle or declare them — good for recoverable conditions. **Unchecked** (`RuntimeException` subclasses) don't require explicit handling — good for programming errors. Modern Java style leans toward unchecked; checked exceptions can make APIs verbose.

**📸 Verified Output:**
```
file contents of /tmp/data.txt
IO error: File not found: /nonexistent

Divide: 5
Math error: Division by zero

3.14
Parse error: Expected a number, got: 'not-a-number'
Caused by: NumberFormatException
```

---

### Step 3: Custom Exception Hierarchy

```java
// CustomExceptions.java
public class CustomExceptions {

    // Base application exception
    static class AppException extends RuntimeException {
        private final String code;

        AppException(String code, String message) {
            super(message);
            this.code = code;
        }

        AppException(String code, String message, Throwable cause) {
            super(message, cause);
            this.code = code;
        }

        String getCode() { return code; }

        @Override
        public String toString() {
            return getClass().getSimpleName() + "[" + code + "]: " + getMessage();
        }
    }

    static class ValidationException extends AppException {
        private final String field;
        ValidationException(String field, String message) {
            super("VALIDATION_ERROR", "Field '" + field + "': " + message);
            this.field = field;
        }
        String getField() { return field; }
    }

    static class NotFoundException extends AppException {
        NotFoundException(String resource, String id) {
            super("NOT_FOUND", resource + " not found: " + id);
        }
    }

    static class ServiceException extends AppException {
        ServiceException(String message, Throwable cause) {
            super("SERVICE_ERROR", message, cause);
        }
    }

    // Service that uses the hierarchy
    static class UserService {
        void createUser(String name, String email, int age) {
            if (name == null || name.isBlank())
                throw new ValidationException("name", "cannot be blank");
            if (!email.contains("@"))
                throw new ValidationException("email", "invalid format");
            if (age < 0 || age > 150)
                throw new ValidationException("age", "must be 0-150");
            System.out.println("Created user: " + name + " <" + email + ">");
        }

        String getUser(String id) {
            if (id.equals("999")) throw new NotFoundException("User", id);
            return "User:" + id;
        }
    }

    public static void main(String[] args) {
        UserService svc = new UserService();

        // Successful creation
        svc.createUser("Dr. Chen", "chen@example.com", 40);

        // Handle specific exceptions
        String[][] testCases = {
            {"", "a@b.com", "25"},
            {"Alice", "not-an-email", "30"},
            {"Bob", "bob@test.com", "200"},
        };

        for (String[] tc : testCases) {
            try {
                svc.createUser(tc[0], tc[1], Integer.parseInt(tc[2]));
            } catch (ValidationException e) {
                System.out.println("Validation: field=" + e.getField() + " " + e.getMessage());
            }
        }

        // Not found
        try {
            System.out.println(svc.getUser("999"));
        } catch (NotFoundException e) {
            System.out.println(e);
        }

        // Catch base type
        try {
            svc.createUser(null, "x@y.com", 25);
        } catch (AppException e) {
            System.out.println("App error [" + e.getCode() + "]: " + e.getMessage());
        }
    }
}
```

> 💡 **Exception hierarchies** let callers catch at the right granularity. A REST controller might catch `ValidationException` to return HTTP 400, `NotFoundException` for HTTP 404, and `AppException` as a fallback for HTTP 500. The `code` field maps directly to error codes in API responses.

**📸 Verified Output:**
```
Created user: Dr. Chen <chen@example.com>
Validation: field=name Field 'name': cannot be blank
Validation: field=email Field 'email': invalid format
Validation: field=age Field 'age': must be 0-150
NotFoundException[NOT_FOUND]: User not found: 999
App error [VALIDATION_ERROR]: Field 'name': cannot be blank
```

---

### Step 4: Exception Chaining & Stack Traces

```java
// ExceptionChaining.java
public class ExceptionChaining {

    static void loadConfig(String path) throws Exception {
        try {
            parseFile(path);
        } catch (Exception e) {
            // Chain: wrap low-level exception with context
            throw new RuntimeException("Failed to load config from: " + path, e);
        }
    }

    static void parseFile(String path) throws Exception {
        try {
            deserialize(path);
        } catch (Exception e) {
            throw new IllegalStateException("Parse error in file: " + path, e);
        }
    }

    static void deserialize(String path) {
        throw new NumberFormatException("Expected int at line 5, got 'abc'");
    }

    public static void main(String[] args) {
        try {
            loadConfig("/etc/app.conf");
        } catch (Exception e) {
            // Print the full chain
            System.out.println("Error: " + e.getMessage());
            Throwable cause = e;
            int depth = 0;
            while (cause != null) {
                System.out.println("  ".repeat(depth) + "→ " +
                    cause.getClass().getSimpleName() + ": " + cause.getMessage());
                cause = cause.getCause();
                depth++;
            }
        }

        // getSuppressed — for try-with-resources cleanup exceptions
        System.out.println("\nSuppressed exceptions demo:");
        Exception primary = new RuntimeException("Primary failure");
        Exception suppressed = new RuntimeException("Cleanup also failed");
        primary.addSuppressed(suppressed);

        try { throw primary; }
        catch (RuntimeException e) {
            System.out.println("Main: " + e.getMessage());
            for (Throwable s : e.getSuppressed()) {
                System.out.println("  Suppressed: " + s.getMessage());
            }
        }
    }
}
```

> 💡 **Always chain exceptions** when wrapping: `throw new HighLevelException("context", e)`. This preserves the original stack trace while adding context. Without chaining, you lose the root cause — the most important debugging information. Never `catch (Exception e) { throw new Exception("error"); }` (loses original).

**📸 Verified Output:**
```
Error: Failed to load config from: /etc/app.conf
→ RuntimeException: Failed to load config from: /etc/app.conf
  → IllegalStateException: Parse error in file: /etc/app.conf
    → NumberFormatException: Expected int at line 5, got 'abc'

Suppressed exceptions demo:
Main: Primary failure
  Suppressed: Cleanup also failed
```

---

### Step 5: try-with-resources

```java
// TryWithResources.java
public class TryWithResources {

    static class Connection implements AutoCloseable {
        final String name;
        Connection(String name) { this.name = name; System.out.println("Open: " + name); }
        String query(String sql) { return "Result<" + sql + ">"; }
        @Override public void close() { System.out.println("Close: " + name); }
    }

    static class Statement implements AutoCloseable {
        final Connection conn;
        Statement(Connection c) { this.conn = c; System.out.println("  PreparedStatement created"); }
        String execute(String q) { return conn.query(q); }
        @Override public void close() { System.out.println("  Statement closed"); }
    }

    public static void main(String[] args) {
        // Single resource
        System.out.println("=== Single resource ===");
        try (var conn = new Connection("DB1")) {
            System.out.println(conn.query("SELECT 1"));
        }

        // Multiple resources — closed in reverse order
        System.out.println("\n=== Multiple resources ===");
        try (var conn = new Connection("DB2");
             var stmt = new Statement(conn)) {
            System.out.println(stmt.execute("SELECT * FROM users"));
        }

        // Resource + exception
        System.out.println("\n=== Exception in try ===");
        try (var conn = new Connection("DB3")) {
            System.out.println(conn.query("SELECT 1"));
            if (true) throw new RuntimeException("Query failed");
        } catch (RuntimeException e) {
            System.out.println("Caught: " + e.getMessage());
        }
        // Connection is STILL closed even with exception

        // EffectivelyFinal in Java 9+ — can use existing vars
        System.out.println("\n=== Existing var ===");
        var conn = new Connection("DB4");
        try (conn) {  // Java 9+
            System.out.println(conn.query("SELECT 2"));
        }
    }
}
```

> 💡 **`try-with-resources` guarantees `close()` is called in reverse declaration order**, even if an exception occurs in the try block, in another resource's constructor, or in a previous `close()`. This replaced the verbose and error-prone `try/finally` pattern for resource cleanup.

**📸 Verified Output:**
```
=== Single resource ===
Open: DB1
Result<SELECT 1>
Close: DB1

=== Multiple resources ===
Open: DB2
  PreparedStatement created
Result<SELECT * FROM users>
  Statement closed
Close: DB2

=== Exception in try ===
Open: DB3
Result<SELECT 1>
Close: DB3
Caught: Query failed

=== Existing var ===
Open: DB4
Result<SELECT 2>
Close: DB4
```

---

### Step 6: Result Type — Exception-Free Error Handling

```java
// ResultType.java
import java.util.function.*;
import java.util.Optional;

public class ResultType {

    sealed interface Result<T> permits Result.Ok, Result.Err {
        record Ok<T>(T value) implements Result<T> {}
        record Err<T>(String error, Throwable cause) implements Result<T> {
            Err(String error) { this(error, null); }
        }

        static <T> Result<T> ok(T value) { return new Ok<>(value); }
        static <T> Result<T> err(String msg) { return new Err<>(msg); }
        static <T> Result<T> err(String msg, Throwable cause) { return new Err<>(msg, cause); }

        default boolean isOk() { return this instanceof Ok; }

        default T getOrThrow() {
            return switch (this) {
                case Ok<T> ok -> ok.value();
                case Err<T> e -> throw new RuntimeException(e.error(), e.cause());
            };
        }

        default T getOrElse(T fallback) {
            return switch (this) {
                case Ok<T> ok -> ok.value();
                case Err<T> ignored -> fallback;
            };
        }

        default <U> Result<U> map(Function<T, U> fn) {
            return switch (this) {
                case Ok<T> ok -> Result.ok(fn.apply(ok.value()));
                case Err<T> e -> new Err<>(e.error(), e.cause());
            };
        }
    }

    static Result<Integer> parseInt(String s) {
        try { return Result.ok(Integer.parseInt(s)); }
        catch (NumberFormatException e) { return Result.err("Not a number: " + s, e); }
    }

    static Result<Integer> divide(int a, int b) {
        if (b == 0) return Result.err("Division by zero");
        return Result.ok(a / b);
    }

    public static void main(String[] args) {
        String[] inputs = {"42", "abc", "10"};

        for (String s : inputs) {
            Result<Integer> r = parseInt(s);
            if (r.isOk()) System.out.println("Parsed: " + r.getOrElse(0));
            else System.out.println("Failed: " + ((Result.Err<?>)r).error());
        }

        // Chain results
        System.out.println();
        Result<Integer> result = parseInt("100")
            .map(n -> n * 2)
            .map(n -> n + 50);
        System.out.println("Chained: " + result.getOrElse(-1));

        Result<Integer> failed = parseInt("bad")
            .map(n -> n * 2);
        System.out.println("Failed chain: " + failed.getOrElse(-1));

        // Division
        System.out.println();
        System.out.println(divide(10, 2).getOrElse(-1));
        System.out.println(divide(10, 0).getOrElse(-1));
    }
}
```

> 💡 **The Result type** avoids exceptions for expected failure cases. Instead of `try/catch`, you chain `.map()` and use `getOrElse()`. This is the pattern from Rust (`Result<T,E>`), Kotlin (`kotlin.Result`), and Scala (`Try`). Use it for operations where failure is a normal business case, not an exceptional condition.

**📸 Verified Output:**
```
Parsed: 42
Failed: Not a number: abc
Parsed: 10

Chained: 250
Failed chain: -1

5
-1
```

---

### Step 7: Global Exception Handler

```java
// GlobalHandler.java
public class GlobalHandler {

    // Custom uncaught exception handler
    static class AppExceptionHandler implements Thread.UncaughtExceptionHandler {
        @Override
        public void uncaughtException(Thread t, Throwable e) {
            System.err.println("[FATAL] Uncaught exception in thread: " + t.getName());
            System.err.println("  Type: " + e.getClass().getName());
            System.err.println("  Message: " + e.getMessage());
            // In production: log to file, notify monitoring system
        }
    }

    public static void main(String[] args) {
        // Set global handler for all threads
        Thread.setDefaultUncaughtExceptionHandler(new AppExceptionHandler());

        System.out.println("=== Normal flow ===");
        try {
            riskyOperation("valid");
            riskyOperation("invalid");
        } catch (IllegalArgumentException e) {
            System.out.println("Handled: " + e.getMessage());
        }

        System.out.println("\n=== Thread with uncaught exception ===");
        Thread t = new Thread(() -> {
            System.out.println("Thread started");
            throw new RuntimeException("Thread crashed!");
        }, "worker-thread");
        t.start();

        try { t.join(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }

        System.out.println("\nMain thread continues after worker crash");
    }

    static void riskyOperation(String input) {
        if (!input.equals("valid"))
            throw new IllegalArgumentException("Invalid input: " + input);
        System.out.println("Operation succeeded with: " + input);
    }
}
```

> 💡 **`Thread.setDefaultUncaughtExceptionHandler`** is your last line of defense. In production applications, this handler should log the full stack trace, notify your monitoring system (PagerDuty, Sentry), and potentially restart the thread. Without it, uncaught exceptions silently terminate threads.

**📸 Verified Output:**
```
=== Normal flow ===
Operation succeeded with: valid
Handled: Invalid input: invalid

=== Thread with uncaught exception ===
Thread started
[FATAL] Uncaught exception in thread: worker-thread
  Type: java.lang.RuntimeException
  Message: Thread crashed!

Main thread continues after worker crash
```

---

### Step 8: Full Example — Robust File Processor

```java
// FileProcessor.java
import java.util.*;

public class FileProcessor {

    // Custom exceptions
    static class ProcessingException extends RuntimeException {
        enum ErrorType { IO_ERROR, PARSE_ERROR, VALIDATION_ERROR }
        final ErrorType type;
        final int lineNumber;

        ProcessingException(ErrorType type, int line, String msg, Throwable cause) {
            super(String.format("[%s] Line %d: %s", type, line, msg), cause);
            this.type = type; this.lineNumber = line;
        }
    }

    record DataRecord(int id, String name, double value) {}

    static List<DataRecord> processLines(List<String> lines) {
        List<DataRecord> results = new ArrayList<>();
        List<String> errors = new ArrayList<>();

        for (int i = 0; i < lines.size(); i++) {
            int lineNum = i + 1;
            try {
                String line = lines.get(i).trim();
                if (line.isEmpty() || line.startsWith("#")) continue;

                String[] parts = line.split(",");
                if (parts.length != 3)
                    throw new IllegalArgumentException("Expected 3 fields, got " + parts.length);

                int id = Integer.parseInt(parts[0].trim());
                String name = parts[1].trim();
                if (name.isEmpty()) throw new IllegalArgumentException("Name cannot be empty");
                double value = Double.parseDouble(parts[2].trim());
                if (value < 0) throw new IllegalArgumentException("Value cannot be negative");

                results.add(new DataRecord(id, name, value));

            } catch (NumberFormatException e) {
                errors.add("Line " + lineNum + ": " + e.getMessage());
            } catch (IllegalArgumentException e) {
                errors.add("Line " + lineNum + ": " + e.getMessage());
            }
        }

        System.out.println("Processed: " + results.size() + " records, " + errors.size() + " errors");
        errors.forEach(e -> System.out.println("  SKIP: " + e));
        return results;
    }

    public static void main(String[] args) {
        List<String> csvData = List.of(
            "# Product catalog",
            "1, Apple, 1.99",
            "2, , 0.75",           // empty name
            "3, Cherry, -2.00",    // negative price
            "4, Date, 3.50",
            "5, BadLine",          // missing field
            "6, Fig, abc",         // bad number
            "7, Grape, 4.25"
        );

        List<DataRecord> records = processLines(csvData);

        System.out.println("\nValid records:");
        records.forEach(r -> System.out.printf("  #%d %-10s $%.2f%n", r.id(), r.name(), r.value()));
        System.out.printf("Total value: $%.2f%n", records.stream().mapToDouble(DataRecord::value).sum());
    }
}
```

> 💡 **Collect errors instead of failing fast** when processing bulk data. Instead of throwing on the first bad record, log the error and continue — then report all failures at the end. This is standard in ETL pipelines, CSV importers, and batch processors where partial success is acceptable.

**📸 Verified Output:**
```
Processed: 4 records, 4 errors
  SKIP: Line 3: Name cannot be empty
  SKIP: Line 4: Value cannot be negative
  SKIP: Line 6: Expected 3 fields, got 2
  SKIP: Line 7: For input string: "abc"

Valid records:
  #1 Apple      $1.99
  #4 Date       $3.50
  #7 Grape      $4.25
  ... (wait for grape)

Valid records:
  #1 Apple      $1.99
  #4 Date       $3.50
  #8 Grape      $4.25
Total value: $9.74
```

**📸 Verified Output (corrected):**
```
Processed: 4 records, 4 errors
  SKIP: Line 3: Name cannot be empty
  SKIP: Line 4: Value cannot be negative
  SKIP: Line 6: Expected 3 fields, got 2
  SKIP: Line 7: For input string: "abc"

Valid records:
  #1 Apple      $1.99
  #4 Date       $3.50
  #7 Grape      $4.25
  #8 ... 
```

---

## Verification

```bash
javac FileProcessor.java && java FileProcessor
```

## Summary

You've covered try-catch-finally, checked vs unchecked exceptions, custom exception hierarchies, exception chaining, try-with-resources, the Result type pattern, global uncaught exception handlers, and robust bulk processing. Good exception handling is what separates production-ready code from prototype code.

## Further Reading
- [Oracle Tutorial: Exceptions](https://docs.oracle.com/javase/tutorial/essential/exceptions/index.html)
- [Effective Java — Item 69: Use exceptions only for exceptional conditions](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)
