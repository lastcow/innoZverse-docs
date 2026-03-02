# Java Foundations

**15 labs** from your first `Hello World` to a complete inventory system using OOP, streams, generics, concurrency, and NIO.2.

| # | Lab | Key Concepts |
|---|-----|-------------|
| 1 | [Hello World & Java Basics](labs/lab-01-hello-world.md) | compile, JVM, main method, System.out |
| 2 | [Variables & Primitives](labs/lab-02-variables-primitives.md) | int, double, char, boolean, casting |
| 3 | [Strings & StringBuilder](labs/lab-03-strings-stringbuilder.md) | String methods, immutability, StringBuilder |
| 4 | [Arrays](labs/lab-04-arrays.md) | arrays, 2D arrays, Arrays utility, sorting |
| 5 | [Control Flow & Recursion](labs/lab-05-control-flow.md) | switch expressions, loops, recursion, FizzBuzz |
| 6 | [OOP — Classes & Encapsulation](labs/lab-06-oop-classes.md) | fields, constructors, records, Builder pattern |
| 7 | [Inheritance & Polymorphism](labs/lab-07-inheritance.md) | extends, override, super, sealed classes |
| 8 | [Interfaces & Abstract Classes](labs/lab-08-interfaces.md) | interface, default/static methods, functional, Strategy/Observer |
| 9 | [Collections](labs/lab-09-collections.md) | ArrayList, HashSet, HashMap, PriorityQueue |
| 10 | [Exception Handling](labs/lab-10-exceptions.md) | checked/unchecked, custom hierarchy, chaining, Result type |
| 11 | [File I/O — NIO.2](labs/lab-11-file-io.md) | Path, Files, walk, WatchService, log analyzer |
| 12 | [Generics](labs/lab-12-generics.md) | type parameters, bounds, wildcards, PECS, repository |
| 13 | [Streams & Lambdas](labs/lab-13-streams.md) | filter/map/collect, groupingBy, flatMap, parallel, sales pipeline |
| 14 | [Concurrency Basics](labs/lab-14-concurrency.md) | threads, ExecutorService, CompletableFuture, virtual threads |
| 15 | [Capstone — Inventory System](labs/lab-15-capstone.md) | all concepts combined, CLI app, CSV persistence |

**Runtime:** Java 21 (Eclipse Temurin) · **Docker:** `innozverse-java:latest`

## 🐳 Quick Start
```bash
docker run --rm innozverse-java:latest java -e 'class H{public static void main(String[]a){System.out.println("Hello, Java 21!");}}'
```
