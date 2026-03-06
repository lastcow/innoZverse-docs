# Lab 02: GraalVM Native & Polyglot JVM

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Explore GraalVM's key innovations: native image compilation via SubstrateVM, the Truffle language framework, and polyglot execution. While `native-image` requires the GraalVM JDK, all conceptual demos run on Temurin via the ScriptEngine/Nashorn fallback or JavaScript-free equivalents.

---

## Step 1: AOT vs JIT — The Core Tradeoff

```
Traditional JIT (HotSpot):
  Source → Bytecode → Interpreter → JIT Profile → C2 Optimized
  Startup: slow, Peak throughput: very high, Memory: moderate

GraalVM Native (AOT):
  Source → Bytecode → GraalVM Compiler → Native Binary
  Startup: <50ms (no JVM bootstrap), Memory: -60%, Throughput: lower peak

GraalVM JIT (Graal compiler on JVM):
  Same as HotSpot but uses Graal C++ → Java compiler
  Better partial escape analysis, speculative optimizations
```

| Metric | HotSpot JIT | GraalVM Native |
|--------|-------------|----------------|
| Startup time | 500ms–2s | 5–50ms |
| Memory (RSS) | ~150MB | ~30MB |
| Peak throughput | ★★★★★ | ★★★☆☆ |
| Dynamic features | Full | Restricted |

> 💡 Native image is ideal for **Lambda functions, CLI tools, microservices** where startup matters. Use JIT for **long-running services** needing peak throughput.

---

## Step 2: GraalVM Compiler Architecture

```
GraalVM Compiler Pipeline:
  Java Bytecode
       │
  ┌────▼─────────────────┐
  │  Graal IR (Graph)    │  — High-level, SSA form
  │  HIR → MIR → LIR    │  — Lowering phases
  └────┬─────────────────┘
       │ Optimizations:
       │  - Partial escape analysis
       │  - Speculative inlining
       │  - Loop transformations
       ▼
  Native Machine Code
```

```java
// Understanding GraalVM compiler behavior
public class GraalCompilerDemo {
    // Partial escape analysis: object never escapes → stack allocate
    public static int noEscape() {
        int[] arr = new int[4]; // GraalVM: stack allocated!
        arr[0] = 1; arr[1] = 2; arr[2] = 3; arr[3] = 4;
        return arr[0] + arr[1] + arr[2] + arr[3];
    }

    // Speculative inlining: virtual call inlined if monomorphic
    interface Compute { int run(int x); }
    static int applyTwice(Compute c, int x) { return c.run(c.run(x)); }

    public static void main(String[] args) {
        // Warm up for JIT
        for (int i = 0; i < 100_000; i++) {
            noEscape();
            applyTwice(x -> x * 2, i);
        }
        System.out.println("noEscape() = " + noEscape());
        System.out.println("applyTwice(x*2, 5) = " + applyTwice(x -> x * 2, 5));
        System.out.println("GraalVM compiler demo complete");
    }
}
```

---

## Step 3: SubstrateVM Reflection Configuration

Native image requires explicit reflection configuration — all reflective access must be declared at build time.

```json
// reflect-config.json
[
  {
    "name": "com.example.MyService",
    "allDeclaredConstructors": true,
    "allPublicMethods": true,
    "allDeclaredFields": true
  },
  {
    "name": "com.example.MyDto",
    "allDeclaredFields": true,
    "allPublicConstructors": true
  }
]
```

```bash
# Build native image with reflection config
native-image \
  -H:ReflectionConfigurationFiles=reflect-config.json \
  -H:ResourceConfigurationFiles=resource-config.json \
  --no-fallback \
  --initialize-at-build-time=com.example.Config \
  -jar myapp.jar \
  myapp-native

# Common native-image flags:
# --no-fallback         — fail if native not possible (no JVM fallback)
# --static              — fully static binary (no libc dependency)
# -H:+ReportExceptionStackTraces — better error messages
# --trace-class-initialization=com.example.Config
```

> 💡 Use `native-image-agent` to **auto-generate** configuration files:  
> `java -agentlib:native-image-agent=config-output-dir=META-INF/native-image -jar app.jar`

---

## Step 4: Truffle Language Framework Concepts

Truffle is GraalVM's framework for implementing high-performance language interpreters that **automatically get JIT compiled** via partial evaluation.

```java
// Conceptual Truffle language structure (requires graal-sdk dependency)
// TruffleLanguage — the language registration
// @TruffleLanguage.Registration(id = "mylang", name = "MyLang")
// class MyLanguage extends TruffleLanguage<MyContext> { ... }

// Node — AST node, the unit of interpretation
// class AddNode extends Node {
//     @Child ExprNode left, right;
//     int execute(VirtualFrame frame) {
//         return left.execute(frame) + right.execute(frame);
//     }
// }

// Key Truffle APIs:
// @Specialization — type-specialized fast paths
// @GenerateNodeFactory — generates factory classes
// CompilerDirectives.transferToInterpreter() — deoptimize
// LoopNode — Truffle loop nodes for OSR

public class TruffleConceptsDemo {
    public static void main(String[] args) {
        System.out.println("Truffle Architecture:");
        System.out.println("  TruffleLanguage → registers language with polyglot engine");
        System.out.println("  Node → AST interpretation unit, gets JIT compiled");
        System.out.println("  VirtualFrame → fast local variable access");
        System.out.println("  @Specialization → type-specialized execution paths");
        System.out.println("  LoopNode → enables on-stack replacement in loops");
        System.out.println();
        System.out.println("Languages on GraalVM via Truffle:");
        System.out.println("  - JavaScript (GraalJS)");
        System.out.println("  - Python (GraalPy)");
        System.out.println("  - Ruby (TruffleRuby)");
        System.out.println("  - R (FastR)");
        System.out.println("  - LLVM bitcode → C/C++/Rust interop");
    }
}
```

---

## Step 5: Polyglot API Concepts

```java
// GraalVM polyglot API (requires org.graalvm.sdk:graal-sdk)
// import org.graalvm.polyglot.*;

// try (Context ctx = Context.newBuilder("js", "python")
//         .allowAllAccess(true)
//         .build()) {
//
//     // Execute JavaScript
//     Value jsResult = ctx.eval("js", "6 * 7");
//     System.out.println(jsResult.asInt()); // 42
//
//     // Pass Java object to JS
//     ctx.getBindings("js").putMember("javaList", new ArrayList<>());
//     ctx.eval("js", "javaList.add(1); javaList.add(2);");
//
//     // Execute Python
//     Value pyResult = ctx.eval("python", "sum([1, 2, 3, 4, 5])");
//     System.out.println(pyResult.asInt()); // 15
// }

public class PolyglotConceptsDemo {
    public static void main(String[] args) {
        System.out.println("GraalVM Polyglot API:");
        System.out.println("  Context.create()    — create execution context");
        System.out.println("  ctx.eval(lang, src) — evaluate code in language");
        System.out.println("  Value.asInt()       — convert polyglot value");
        System.out.println("  getBindings(lang)   — share objects across languages");
        System.out.println("  allowAllAccess()    — permit Java interop");
    }
}
```

---

## Step 6: ScriptEngine Fallback on Temurin

Temurin 21 doesn't ship Nashorn but supports the ScriptEngine SPI. We demonstrate the polyglot concept using the expression evaluator pattern:

```java
import javax.script.*;
import java.util.*;

public class ScriptEngineDemo {
    public static void main(String[] args) throws Exception {
        ScriptEngineManager manager = new ScriptEngineManager();
        List<ScriptEngineFactory> factories = manager.getEngineFactories();
        
        System.out.println("Available script engines on this JVM:");
        if (factories.isEmpty()) {
            System.out.println("  (none built-in — GraalVM JS would add 'js'/'JavaScript')");
        }
        for (ScriptEngineFactory f : factories) {
            System.out.println("  " + f.getEngineName() + " — " + f.getLanguageName());
        }
        
        // Demonstrate eval via reflection/expression — pure Java polyglot pattern
        // When running on GraalVM:
        // ScriptEngine js = manager.getEngineByName("js");
        // js.eval("var result = 6 * 7; print('JS result: ' + result);");
        
        System.out.println("\nOn GraalVM JDK, add graalvm-js dependency:");
        System.out.println("  Context ctx = Context.create();");
        System.out.println("  Value v = ctx.eval(\"js\", \"6 * 7\");");
        System.out.println("  System.out.println(v.asInt()); // 42");
        System.out.println("\nPolyglot demo complete");
    }
}
```

📸 **Verified Output:**
```
Available script engines on this JVM:
  (none built-in — GraalVM JS would add 'js'/'JavaScript')

On GraalVM JDK, add graalvm-js dependency:
  Context ctx = Context.create();
  Value v = ctx.eval("js", "6 * 7");
  System.out.println(v.asInt()); // 42

Polyglot demo complete
```

---

## Step 7: Native Image Build Process

```bash
# Install GraalVM (not available in this Docker image, shown for reference)
sdk install java 21.0.2-graal   # via SDKMAN
# or: download from https://graalvm.github.io/native-build-tools/

# Simple native image build
cat > Hello.java << 'EOF'
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello, Native World!");
    }
}
EOF
javac Hello.java
native-image Hello hello-native

# Profile native image startup
time ./hello-native     # ~5ms
time java Hello         # ~200ms

# Native image size
ls -lh hello-native     # ~7MB vs 250MB JDK
```

---

## Step 8: Capstone — AOT Tradeoffs Analysis

```java
public class Main {
    public static void main(String[] args) {
        System.out.println("=== GraalVM vs HotSpot Decision Matrix ===");
        System.out.println();
        
        String[][] matrix = {
            {"Use Case", "Recommended JVM", "Reason"},
            {"AWS Lambda / serverless", "GraalVM Native", "Startup < 100ms required"},
            {"CLI tool", "GraalVM Native", "Instant startup, single binary"},
            {"Trading system", "HotSpot + C2", "Peak throughput, steady state"},
            {"Long-running microservice", "HotSpot", "JIT warmup pays off"},
            {"Kubernetes sidecar", "GraalVM Native", "Lower memory footprint"},
            {"Spring Boot (traditional)", "HotSpot", "Dynamic proxies, reflection"},
            {"Spring Boot 3 + AOT", "GraalVM Native", "Spring AOT mode supported"},
        };
        
        for (String[] row : matrix) {
            System.out.printf("%-35s %-25s %s%n", row[0], row[1], row[2]);
        }
        
        System.out.println();
        System.out.println("Reflection restrictions in native image:");
        System.out.println("  1. reflect-config.json — explicit reflection declaration");
        System.out.println("  2. resource-config.json — classpath resources");
        System.out.println("  3. proxy-config.json — dynamic proxy interfaces");
        System.out.println("  4. serialization-config.json — Java serialization");
        System.out.println();
        System.out.println("GraalVM native + Truffle architecture verified!");
    }
}
```

```bash
javac /tmp/Main.java -d /tmp && java -cp /tmp Main
```

---

## Summary

| Concept | Technology | Key Points |
|---|---|---|
| AOT compilation | `native-image` | Fast startup, restricted reflection |
| Truffle AST | `TruffleLanguage`, `Node` | Self-optimizing interpreter |
| Partial evaluation | Graal compiler | Truffle → native code |
| SubstrateVM | reflect-config.json | Build-time closed-world |
| Polyglot context | `Context.create()` | Cross-language objects |
| JIT vs AOT | HotSpot vs native | Throughput vs startup |
| native-image-agent | `-agentlib:` | Auto-generate configs |
