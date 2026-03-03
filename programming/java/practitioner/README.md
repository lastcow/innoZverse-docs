# Java — Practitioner Level

> 15 labs covering intermediate Java 21: generics, streams, functional interfaces, concurrency, file I/O, JDBC, design patterns, reflection, enums, and a full capstone order platform.

## Labs

| # | Lab | Key Skills |
|---|-----|-----------|
| 01 | [Generics & Collections](labs/lab-01-generics-collections.md) | Bounded types, PECS wildcards, `TreeMap`, `PriorityQueue`, `computeIfAbsent` |
| 02 | [Streams & Lambdas](labs/lab-02-streams-lambdas.md) | `filter/map/flatMap/reduce`, `Collectors.groupingBy`, `partitioningBy`, `toMap` |
| 03 | [Functional Interfaces](labs/lab-03-functional-interfaces.md) | `Function`, `Predicate`, `Optional`, composition, method references |
| 04 | [Exception Handling](labs/lab-04-exception-handling.md) | Custom hierarchy, multi-catch, `Result<T>` sealed type, `finally` |
| 05 | [Concurrency](labs/lab-05-concurrency.md) | `ExecutorService`, `CompletableFuture`, `ConcurrentHashMap`, CAS |
| 06 | [File I/O & NIO.2](labs/lab-06-file-io-nio.md) | `Path`, `Files.lines`, `Files.walk`, `BufferedWriter`, file attributes |
| 07 | [Java 21 Features](labs/lab-07-java21-features.md) | Records, sealed interfaces, pattern matching switch, text blocks |
| 08 | [Design Patterns](labs/lab-08-design-patterns.md) | Builder, Factory, Observer (EventBus), Strategy |
| 09 | [Testing](labs/lab-09-testing.md) | assertEquals, assertApprox, assertThrows, parametrized tests |
| 10 | [JDBC & SQLite](labs/lab-10-jdbc-sqlite.md) | `PreparedStatement`, batch insert, transactions, JOIN queries |
| 11 | [HTTP Client](labs/lab-11-http-client.md) | `java.net.http`, GET/POST, async parallel, retry/backoff |
| 12 | [Reflection & Annotations](labs/lab-12-reflection-annotations.md) | `@Retention`, `@Target`, SQL generator, generic repository |
| 13 | [Interfaces Advanced](labs/lab-13-interfaces-advanced.md) | Default/static/private methods, composition, template method |
| 14 | [Advanced Enums](labs/lab-14-enums-advanced.md) | State machine, abstract methods, `EnumSet`, `EnumMap`, exhaustive switch |
| 15 | [Capstone — Order Platform](labs/lab-15-capstone.md) | All patterns: records + sealed + enums + concurrency + streams + events |

## Prerequisites

- Java Foundations Labs 01–15 (all)
- Java 21 (Eclipse Temurin) — `zchencow/innozverse-java:latest`

## Run Any Lab

```bash
docker pull zchencow/innozverse-java:latest

# Inline code
docker run --rm zchencow/innozverse-java:latest sh -c "
cat > /tmp/Main.java << 'EOF'
public class Main {
  public static void main(String[] args) {
    System.out.println(\"Java \" + Runtime.version());
  }
}
EOF
javac /tmp/Main.java -d /tmp && java -cp /tmp Main"

# From file
docker run --rm -v /tmp/MyLab.java:/tmp/MyLab.java zchencow/innozverse-java:latest \
  sh -c "javac /tmp/MyLab.java -d /tmp && java -cp /tmp MyLab"
```
