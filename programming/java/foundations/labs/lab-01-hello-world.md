# Lab 1: Hello World — Compile and Run Java

## 🎯 Objective
Write, compile, and run your first Java program using the command line.

## 📚 Background
Java is a compiled, statically-typed language. Source code (`.java`) is compiled by `javac` into bytecode (`.class`), then executed by the Java Virtual Machine (JVM) via `java`. This compile-once, run-anywhere model is Java's core promise.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Docker installed
- Access to `innozverse-java:latest` Docker image

## 🛠️ Tools Used
- Docker (`innozverse-java:latest`)
- `javac` (Java compiler)
- `java` (JVM runtime)

## 🔬 Lab Instructions

### Step 1: Verify the Java environment
```bash
docker run --rm innozverse-java:latest java -version
```
💡 You should see the Java version (17+). The JVM is pre-installed in the Docker image.

### Step 2: Create your first Java source file
```bash
cat > /tmp/HelloWorld.java << 'EOF'
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        System.out.println("Welcome to Java programming!");
    }
}
EOF
```
💡 In Java, the **filename must match the public class name** exactly (case-sensitive).

### Step 3: Understand the anatomy of a Java program
```java
public class HelloWorld {          // Class declaration — matches filename
    public static void main(String[] args) {  // Entry point — JVM calls this
        System.out.println("Hello, World!");  // Print to stdout with newline
    }
}
```
- `public` — accessible from anywhere
- `static` — belongs to the class, not an instance
- `void` — returns nothing
- `String[] args` — command-line arguments array

### Step 4: Compile the Java source file
```bash
docker run --rm -v /tmp:/tmp innozverse-java:latest javac /tmp/HelloWorld.java
```
💡 This produces `/tmp/HelloWorld.class` — the bytecode file executed by the JVM.

### Step 5: Verify the class file was created
```bash
ls -la /tmp/HelloWorld.class
```

### Step 6: Run the compiled program
```bash
docker run --rm -v /tmp:/tmp innozverse-java:latest java -cp /tmp HelloWorld
```

**📸 Verified Output:**
```
Hello, World!
Welcome to Java programming!
```

### Step 7: Pass command-line arguments
```bash
cat > /tmp/HelloArgs.java << 'EOF'
public class HelloArgs {
    public static void main(String[] args) {
        if (args.length > 0) {
            System.out.println("Hello, " + args[0] + "!");
        } else {
            System.out.println("Hello, stranger!");
        }
    }
}
EOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "javac /tmp/HelloArgs.java && java -cp /tmp HelloArgs InnoZverse"
```

**📸 Verified Output:**
```
Hello, InnoZverse!
```

### Step 8: Compile and run in one command
```bash
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac HelloWorld.java && java HelloWorld"
```
💡 From Java 11+, you can also run single-file programs directly: `java HelloWorld.java` (no separate compile step needed for simple programs).

## ✅ Verification
Run the full verification:
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        System.out.println("Java version: " + System.getProperty("java.version"));
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
Hello, World!
Java version: 17.x.x
```

## 🚨 Common Mistakes
- **Filename mismatch**: `public class Foo` must be in `Foo.java` — not `foo.java` or `FOO.java`
- **Missing semicolons**: Every statement in Java ends with `;`
- **Running without compiling**: You must `javac` before `java`
- **Wrong classpath**: Use `-cp /tmp` when the `.class` file is in `/tmp`

## 📝 Summary
You've written, compiled, and run your first Java program. Key takeaways:
- Java source → `.java` files
- Compiled bytecode → `.class` files
- Run with `java ClassName` (no `.class` extension)
- Every Java program needs a `main` method as its entry point

## 🔗 Further Reading
- [Java Language Specification](https://docs.oracle.com/javase/specs/)
- [JVM Architecture Overview](https://docs.oracle.com/javase/8/docs/technotes/guides/vm/index.html)
- [OpenJDK Documentation](https://openjdk.org/)
