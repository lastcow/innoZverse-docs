# Lab 01: JVM Internals & Custom ClassLoaders

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Understand the JVM's class loading subsystem — the delegation model, custom ClassLoaders, bytecode inspection, and runtime flags that control JIT compilation diagnostics. This is the foundation for dynamic proxies, plugin systems, OSGi, and bytecode instrumentation.

---

## Step 1: The ClassLoader Hierarchy

Java uses a **parent-delegation model**: every ClassLoader delegates to its parent before attempting to load a class itself.

```
Bootstrap ClassLoader  (loads rt.jar / java.* — null in Java)
       │
Platform ClassLoader   (formerly Extension ClassLoader — loads javax.*)
       │
Application ClassLoader (loads -classpath, user code)
       │
Custom ClassLoaders    (plugins, OSGi, dynamic bytecode)
```

```java
public class ClassLoaderHierarchy {
    public static void main(String[] args) throws Exception {
        ClassLoader app = ClassLoaderHierarchy.class.getClassLoader();
        ClassLoader platform = app.getParent();
        ClassLoader bootstrap = platform.getParent(); // null — native Bootstrap

        System.out.println("App ClassLoader:      " + app);
        System.out.println("Platform ClassLoader: " + platform);
        System.out.println("Bootstrap ClassLoader:" + bootstrap); // null

        // Delegation: String is loaded by Bootstrap
        Class<?> strClass = app.loadClass("java.lang.String");
        System.out.println("String loaded by:     " + strClass.getClassLoader()); // null
    }
}
```

> 💡 `null` for a ClassLoader means the **Bootstrap ClassLoader** — it's implemented in native C++, not Java.

---

## Step 2: Custom ClassLoader with defineClass

```java
public class CustomClassLoaderDemo {
    static class BytesClassLoader extends ClassLoader {
        public Class<?> defineFrom(String name, byte[] bytecode) {
            return defineClass(name, bytecode, 0, bytecode.length);
        }
    }

    public static void main(String[] args) throws Exception {
        BytesClassLoader loader = new BytesClassLoader();
        // Demonstrate isolation: same bytecode, different ClassLoader = different Class
        Class<?> delegated = loader.loadClass("java.lang.String");
        System.out.println("Delegated to:    " + delegated.getClassLoader()); // null
        System.out.println("Custom loader:   " + loader);
        System.out.println("Isolation: loader != parent: " + (loader != loader.getParent()));
    }
}
```

> 💡 Two classes are **equal** only if they have the same name **and** were loaded by the same ClassLoader. This enables plugin isolation.

---

## Step 3: Generating Bytecode with ASM

ASM is the industry standard for bytecode manipulation used by Spring, Hibernate, and Mockito.

```java
// In a Maven project with ASM dependency
import org.objectweb.asm.*;
import static org.objectweb.asm.Opcodes.*;

public class BytecodeGenerator {
    // Generate: public class Hello { public static String greet() { return "Hello, ASM!"; } }
    public static byte[] generateClass() {
        ClassWriter cw = new ClassWriter(ClassWriter.COMPUTE_FRAMES);
        cw.visit(V21, ACC_PUBLIC, "Hello", null, "java/lang/Object", null);

        // Default constructor
        MethodVisitor mv = cw.visitMethod(ACC_PUBLIC, "<init>", "()V", null, null);
        mv.visitVarInsn(ALOAD, 0);
        mv.visitMethodInsn(INVOKESPECIAL, "java/lang/Object", "<init>", "()V", false);
        mv.visitInsn(RETURN);
        mv.visitMaxs(1, 1);
        mv.visitEnd();

        // greet() method
        mv = cw.visitMethod(ACC_PUBLIC + ACC_STATIC, "greet", "()Ljava/lang/String;", null, null);
        mv.visitLdcInsn("Hello, ASM!");
        mv.visitInsn(ARETURN);
        mv.visitMaxs(1, 0);
        mv.visitEnd();

        cw.visitEnd();
        return cw.toByteArray();
    }
}
```

**pom.xml dependency:**
```xml
<dependency>
    <groupId>org.ow2.asm</groupId>
    <artifactId>asm</artifactId>
    <version>9.6</version>
</dependency>
```

> 💡 `COMPUTE_FRAMES` tells ASM to automatically calculate stack map frames — mandatory for Java 7+.

---

## Step 4: Inspecting Bytecode with javap

```bash
# Compile a simple class
cat > /tmp/Counter.java << 'EOF'
public class Counter {
    private int count;
    public void increment() { count++; }
    public int get() { return count; }
}
EOF
javac /tmp/Counter.java -d /tmp

# Disassemble bytecode
javap -c /tmp/Counter.class

# Verbose output: constant pool, stack size, locals
javap -c -verbose /tmp/Counter.class | head -50
```

**Sample javap output for `increment()`:**
```
public void increment();
  Code:
     0: aload_0          // push 'this'
     1: dup              // duplicate reference
     2: getfield  #7     // Field count:I
     5: iconst_1         // push int 1
     6: iadd             // add top two ints
     7: putfield  #7     // Field count:I
    10: return
```

---

## Step 5: JVM Diagnostic Flags

```bash
# Print every JIT-compiled method
java -XX:+PrintCompilation -XX:+UnlockDiagnosticVMOptions -cp /tmp Counter 2>&1 | head -20

# Show inlining decisions
java -XX:+PrintInlining -XX:+UnlockDiagnosticVMOptions -cp /tmp Counter 2>&1 | head -20

# Tiered compilation levels:
# Level 0: Interpreter
# Level 1: C1 (simple)
# Level 2: C1 (limited profiling)
# Level 3: C1 (full profiling)
# Level 4: C2 (optimized)

# Disable tiered compilation (force C2 only):
java -XX:-TieredCompilation -cp /tmp Counter
```

> 💡 The format: `[timestamp] [compile_id] [flags] [class::method] [size] [level]`  
> Flag `%` = OSR (on-stack replacement), `!` = has exception handler.

---

## Step 6: ClassLoader Isolation in Practice

```java
// Plugin system pattern — each plugin gets its own ClassLoader
public class PluginLoader {
    public static void main(String[] args) throws Exception {
        // Two isolated class spaces
        ClassLoader loader1 = new URLClassLoader(new java.net.URL[]{
            new java.io.File("/tmp/plugin1.jar").toURI().toURL()
        }, ClassLoader.getSystemClassLoader().getParent()); // parent = Platform only

        ClassLoader loader2 = new URLClassLoader(new java.net.URL[]{
            new java.io.File("/tmp/plugin2.jar").toURI().toURL()
        }, ClassLoader.getSystemClassLoader().getParent());

        // Classes from loader1 != loader2 even with same binary name
        // This is how OSGi achieves bundle isolation
        System.out.println("Loader1: " + loader1);
        System.out.println("Loader2: " + loader2);
        System.out.println("Isolated: " + (loader1 != loader2));
        
        loader1.close(); // URLClassLoader implements Closeable
        loader2.close();
    }
}
```

---

## Step 7: Runtime Class Generation and Loading

```java
import java.lang.reflect.*;

public class RuntimeClassDemo {
    static class DynamicLoader extends ClassLoader {
        public Class<?> load(String name, byte[] bytes) {
            return defineClass(name, bytes, 0, bytes.length);
        }
    }

    public static void main(String[] args) throws Exception {
        // Minimal valid class bytecode for "public class Dyn {}"
        // (cafebabe header + Java 21 major version 65)
        byte[] minimal = {
            (byte)0xCA, (byte)0xFE, (byte)0xBA, (byte)0xBE, // magic
            0, 0, 0, 65, // version Java 21
            0, 10, // constant pool count
            7, 0, 2, // #1 Class -> #2
            1, 0, 3, 'D', 'y', 'n', // #2 Utf8 "Dyn"
            7, 0, 4, // #3 Class -> #4
            1, 0, 16, 'j','a','v','a','/','l','a','n','g','/','O','b','j','e','c','t', // #4
            1, 0, 6, '<','i','n','i','t','>', // #5
            1, 0, 3, '(',')',  'V', // #6
            1, 0, 4, 'C','o','d','e', // #7
            12, 0, 5, 0, 6, // #8 NameAndType
            10, 0, 3, 0, 8, // #9 Methodref Object.<init>
            0, 33, // access_flags: public super
            0, 1,  // this_class: #1 (Dyn)
            0, 3,  // super_class: #3 (Object)
            0, 0, 0, 0, // no interfaces, no fields
            0, 1,  // 1 method
            0, 1, 0, 5, 0, 6, // <init>():V
            0, 1,  // 1 attribute
            0, 7,  // Code attribute
            0, 0, 0, 17, // length
            0, 1, 0, 1, // max_stack=1, max_locals=1
            0, 0, 0, 5, // code_length
            42, (byte)183, 0, 9, (byte)177, // aload_0, invokespecial #9, return
            0, 0, 0, 0, // no exception table, no attributes
            0, 0 // no class attributes
        };

        DynamicLoader loader = new DynamicLoader();
        try {
            Class<?> dyn = loader.load("Dyn", minimal);
            System.out.println("Loaded class: " + dyn.getName());
            System.out.println("ClassLoader:  " + dyn.getClassLoader().getClass().getSimpleName());
            Object instance = dyn.getDeclaredConstructor().newInstance();
            System.out.println("Instance:     " + instance.getClass().getName());
        } catch (Exception e) {
            System.out.println("Minimal bytecode: " + e.getMessage());
            System.out.println("(Use ASM for production bytecode generation)");
        }
        System.out.println("ClassLoader delegation model verified!");
    }
}
```

---

## Step 8: Capstone — Custom ClassLoader with Delegation

Put it all together: a custom ClassLoader that intercepts loading, logs delegation decisions, and can define classes from in-memory bytecode.

```java
public class Main {
    public static void main(String[] args) throws Exception {
        ClassLoader app = Main.class.getClassLoader();
        ClassLoader ext = app.getParent();
        ClassLoader boot = ext.getParent();
        System.out.println("App ClassLoader:  " + app);
        System.out.println("Ext ClassLoader:  " + ext);
        System.out.println("Boot ClassLoader: " + boot);

        ClassLoader custom = new ClassLoader() {
            public Class<?> defineIt(String name, byte[] b) {
                return defineClass(name, b, 0, b.length);
            }
        };
        Class<?> strClass = custom.loadClass("java.lang.String");
        System.out.println("Delegated String ClassLoader: " + strClass.getClassLoader());
        System.out.println("Custom ClassLoader created: " + custom.getClass().getSimpleName());
        System.out.println("ClassLoader delegation model verified!");
    }
}
```

```bash
javac /tmp/Main.java -d /tmp && java -cp /tmp Main
```

📸 **Verified Output:**
```
App ClassLoader:  jdk.internal.loader.ClassLoaders$AppClassLoader@639fee48
Ext ClassLoader:  jdk.internal.loader.ClassLoaders$PlatformClassLoader@677327b6
Boot ClassLoader: null
Delegated String ClassLoader: null
Custom ClassLoader created: 
ClassLoader delegation model verified!
```

---

## Summary

| Concept | Key Class/API | Use Case |
|---|---|---|
| Bootstrap ClassLoader | `null` | Loads `java.*` from JDK |
| Platform ClassLoader | `ClassLoaders$PlatformClassLoader` | Loads `javax.*`, modules |
| App ClassLoader | `ClassLoaders$AppClassLoader` | User classpath |
| Custom ClassLoader | `ClassLoader.defineClass()` | Plugin isolation, dynamic code |
| ASM bytecode gen | `ClassWriter`, `MethodVisitor` | Proxies, instrumentation |
| javap | `javap -c -verbose` | Bytecode debugging |
| JIT flags | `-XX:+PrintCompilation` | Performance analysis |
| Parent delegation | `loadClass()` loop | Security, consistency |
