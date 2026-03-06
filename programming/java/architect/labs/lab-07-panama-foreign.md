# Lab 07: Project Panama — Foreign Function & Memory API

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

Project Panama's Foreign Function & Memory (FFM) API replaces JNI with a safe, ergonomic way to call native code and manage off-heap memory. Use `MemorySegment`, `Arena`, `Linker`, and `MemoryLayout` to call C functions directly from Java 21.

---

## Step 1: FFM API Overview

```
Project Panama FFM replaces JNI:
  JNI (old):                      FFM (Java 21):
  - Write C header                - No C code needed
  - Compile native library        - Direct downcall via Linker
  - Load with System.loadLibrary  - Arena manages memory lifetime
  - Fragile, error-prone          - Type-safe MemoryLayout
  - Cannot be verified by JVM     - Verified by JVM

Core classes:
  MemorySegment  — a bounded region of memory (on-heap or off-heap)
  Arena          — controls lifetime of off-heap memory segments
  Linker         — creates handles to call native functions
  SymbolLookup   — finds native symbols by name
  MemoryLayout   — describes C struct/array memory layout
  ValueLayout    — describes primitive C type layout
```

---

## Step 2: Arena and MemorySegment

```java
import java.lang.foreign.*;

public class ArenaDemo {
    public static void main(String[] args) {
        // Confined Arena — single-thread, scope-bound
        try (Arena arena = Arena.ofConfined()) {
            // Allocate 64 bytes of native memory
            MemorySegment segment = arena.allocate(64);
            
            System.out.println("Segment address: " + segment.address());
            System.out.println("Segment size: " + segment.byteSize() + " bytes");
            System.out.println("isNative: " + segment.isNative());
            
            // Write and read individual bytes
            segment.set(ValueLayout.JAVA_BYTE, 0, (byte) 42);
            segment.set(ValueLayout.JAVA_INT, 4, 12345);
            segment.set(ValueLayout.JAVA_LONG, 8, 9876543210L);
            
            byte b = segment.get(ValueLayout.JAVA_BYTE, 0);
            int i = segment.get(ValueLayout.JAVA_INT, 4);
            long l = segment.get(ValueLayout.JAVA_LONG, 8);
            
            System.out.println("Read byte: " + b);
            System.out.println("Read int:  " + i);
            System.out.println("Read long: " + l);
        } // Arena closes → memory freed automatically
        
        // Shared Arena — multi-thread safe
        try (Arena shared = Arena.ofShared()) {
            MemorySegment seg = shared.allocate(ValueLayout.JAVA_DOUBLE);
            seg.set(ValueLayout.JAVA_DOUBLE, 0, 3.14159);
            System.out.println("Double: " + seg.get(ValueLayout.JAVA_DOUBLE, 0));
        }
        
        // Global Arena — manual lifetime management
        // MemorySegment global = Arena.global().allocate(128);
        // global.address(); // lives until JVM exits
    }
}
```

> 💡 **Arena types:** `ofConfined()` (single-thread), `ofShared()` (multi-thread), `ofAuto()` (GC-managed), `global()` (never freed).

---

## Step 3: Calling strlen via Linker

```java
import java.lang.foreign.*;
import java.lang.invoke.*;
import java.nio.charset.StandardCharsets;

public class LinkerDemo {
    public static void main(String[] args) throws Throwable {
        // Get native linker for this platform (Linux/macOS/Windows)
        Linker linker = Linker.nativeLinker();
        SymbolLookup stdlib = linker.defaultLookup();
        
        // Create downcall handle: strlen(const char*) → size_t
        MethodHandle strlen = linker.downcallHandle(
            stdlib.find("strlen").orElseThrow(),
            FunctionDescriptor.of(
                ValueLayout.JAVA_LONG,  // return: size_t
                ValueLayout.ADDRESS     // param: const char*
            )
        );
        
        try (Arena arena = Arena.ofConfined()) {
            // Allocate C string (null-terminated)
            byte[] bytes = "Hello, Panama!".getBytes(StandardCharsets.UTF_8);
            MemorySegment cStr = arena.allocate(bytes.length + 1); // +1 for null terminator
            for (int i = 0; i < bytes.length; i++) {
                cStr.set(ValueLayout.JAVA_BYTE, i, bytes[i]);
            }
            // byte at bytes.length is already 0 (null terminator)
            
            long len = (long) strlen.invoke(cStr);
            System.out.println("strlen(\"Hello, Panama!\") = " + len); // 14
        }
    }
}
```

```bash
javac --enable-preview --release 21 LinkerDemo.java -d /tmp 2>&1 | grep -v Note
java --enable-preview --enable-native-access=ALL-UNNAMED -cp /tmp LinkerDemo
```

---

## Step 4: MemoryLayout — C Struct Mapping

```java
import java.lang.foreign.*;

public class MemoryLayoutDemo {
    public static void main(String[] args) throws Exception {
        // C struct: struct Point { double x; double y; }
        StructLayout pointLayout = MemoryLayout.structLayout(
            ValueLayout.JAVA_DOUBLE.withName("x"),
            ValueLayout.JAVA_DOUBLE.withName("y")
        );
        System.out.println("Point size:   " + pointLayout.byteSize() + " bytes");
        System.out.println("x offset:     " + pointLayout.byteOffset(MemoryLayout.PathElement.groupElement("x")));
        System.out.println("y offset:     " + pointLayout.byteOffset(MemoryLayout.PathElement.groupElement("y")));
        
        // C struct with padding: struct Padded { int id; double value; }
        // int = 4 bytes, then 4 bytes padding, then double = 8 bytes
        StructLayout paddedLayout = MemoryLayout.structLayout(
            ValueLayout.JAVA_INT.withName("id"),
            MemoryLayout.paddingLayout(4), // alignment padding
            ValueLayout.JAVA_DOUBLE.withName("value")
        );
        System.out.println("Padded size:  " + paddedLayout.byteSize() + " bytes");
        System.out.println("value offset: " + paddedLayout.byteOffset(MemoryLayout.PathElement.groupElement("value")));
        
        // Array layout: double[4]
        SequenceLayout arrayLayout = MemoryLayout.sequenceLayout(4, ValueLayout.JAVA_DOUBLE);
        System.out.println("double[4] size: " + arrayLayout.byteSize() + " bytes");
        
        // Use VarHandle for type-safe field access
        var xHandle = pointLayout.varHandle(MemoryLayout.PathElement.groupElement("x"));
        var yHandle = pointLayout.varHandle(MemoryLayout.PathElement.groupElement("y"));
        
        try (Arena arena = Arena.ofConfined()) {
            MemorySegment point = arena.allocate(pointLayout);
            xHandle.set(point, 0L, 3.0);
            yHandle.set(point, 0L, 4.0);
            double x = (double) xHandle.get(point, 0L);
            double y = (double) yHandle.get(point, 0L);
            System.out.printf("Point(%g, %g) distance = %g%n", x, y, Math.sqrt(x*x + y*y));
        }
    }
}
```

---

## Step 5: Full strlen via FFM API (Verified)

```java
import java.lang.foreign.*;
import java.lang.invoke.*;
import java.nio.charset.StandardCharsets;

public class Main {
    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();
        SymbolLookup stdlib = linker.defaultLookup();
        
        MethodHandle strlen = linker.downcallHandle(
            stdlib.find("strlen").orElseThrow(),
            FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS)
        );
        
        try (Arena arena = Arena.ofConfined()) {
            byte[] bytes1 = "Hello, Panama!".getBytes(StandardCharsets.UTF_8);
            MemorySegment str1 = arena.allocate(bytes1.length + 1);
            for (int i = 0; i < bytes1.length; i++) str1.set(ValueLayout.JAVA_BYTE, i, bytes1[i]);
            
            long len1 = (long) strlen.invoke(str1);
            System.out.println("strlen(Hello, Panama!) = " + len1);
            
            MemoryLayout pointLayout = MemoryLayout.structLayout(
                ValueLayout.JAVA_DOUBLE.withName("x"),
                ValueLayout.JAVA_DOUBLE.withName("y")
            );
            System.out.println("Point struct layout size: " + pointLayout.byteSize() + " bytes");
            System.out.println("FFM API strlen via native Linker: SUCCESS");
        }
    }
}
```

```bash
javac --enable-preview --release 21 /tmp/Main.java -d /tmp 2>/dev/null
java --enable-preview --enable-native-access=ALL-UNNAMED -cp /tmp Main
```

📸 **Verified Output:**
```
strlen(Hello, Panama!) = 14
Point struct layout size: 16 bytes
FFM API strlen via native Linker: SUCCESS
```

---

## Step 6: Calling qsort via FFM

```java
import java.lang.foreign.*;
import java.lang.invoke.*;

public class QsortDemo {
    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();
        SymbolLookup stdlib = linker.defaultLookup();
        
        // void qsort(void *base, size_t nmemb, size_t size,
        //            int (*compar)(const void *, const void *))
        MethodHandle qsort = linker.downcallHandle(
            stdlib.find("qsort").orElseThrow(),
            FunctionDescriptor.ofVoid(
                ValueLayout.ADDRESS,  // base
                ValueLayout.JAVA_LONG, // nmemb
                ValueLayout.JAVA_LONG, // size
                ValueLayout.ADDRESS   // comparator function pointer
            )
        );
        
        // Create comparator: int cmp(const int* a, const int* b) { return *a - *b; }
        MethodHandle cmpHandle = MethodHandles.lookup().findStatic(
            QsortDemo.class, "compareInts",
            MethodType.methodType(int.class, MemorySegment.class, MemorySegment.class)
        );
        
        FunctionDescriptor cmpDesc = FunctionDescriptor.of(
            ValueLayout.JAVA_INT, ValueLayout.ADDRESS, ValueLayout.ADDRESS
        );
        
        try (Arena arena = Arena.ofConfined()) {
            MemorySegment comparator = linker.upcallStub(cmpHandle, cmpDesc, arena);
            
            int[] data = {5, 2, 8, 1, 9, 3};
            MemorySegment arr = arena.allocate((long) data.length * ValueLayout.JAVA_INT.byteSize());
            for (int i = 0; i < data.length; i++) {
                arr.set(ValueLayout.JAVA_INT, (long) i * 4, data[i]);
            }
            
            qsort.invoke(arr, (long) data.length, 4L, comparator);
            
            System.out.print("qsort result: ");
            for (int i = 0; i < data.length; i++) {
                System.out.print(arr.get(ValueLayout.JAVA_INT, (long) i * 4) + " ");
            }
            System.out.println();
        }
    }
    
    static int compareInts(MemorySegment a, MemorySegment b) {
        return Integer.compare(
            a.get(ValueLayout.JAVA_INT, 0),
            b.get(ValueLayout.JAVA_INT, 0)
        );
    }
}
```

> 💡 `linker.upcallStub()` creates a C function pointer from a Java `MethodHandle` — this is how callbacks work in FFM.

---

## Step 7: Off-Heap Buffer Pattern

```java
import java.lang.foreign.*;
import java.nio.*;

public class OffHeapBufferDemo {
    public static void main(String[] args) {
        // Traditional ByteBuffer (off-heap, but no lifetime management)
        ByteBuffer nioBuffer = ByteBuffer.allocateDirect(1024);
        nioBuffer.putInt(0, 42);
        System.out.println("NIO direct buffer: " + nioBuffer.getInt(0));
        
        // FFM MemorySegment (off-heap, Arena lifetime control)
        try (Arena arena = Arena.ofConfined()) {
            MemorySegment seg = arena.allocate(1024);
            
            // Write a C-style string array
            String[] names = {"Alice", "Bob", "Charlie"};
            MemorySegment[] ptrs = new MemorySegment[names.length];
            for (int i = 0; i < names.length; i++) {
                byte[] b = names[i].getBytes();
                ptrs[i] = arena.allocate(b.length + 1);
                for (int j = 0; j < b.length; j++) ptrs[i].set(ValueLayout.JAVA_BYTE, j, b[j]);
            }
            System.out.println("Allocated " + names.length + " C strings in Arena");
            System.out.println("MemorySegment isNative: " + seg.isNative());
            System.out.println("MemorySegment byteSize: " + seg.byteSize());
        }
        // All Arena memory freed here
        System.out.println("Arena closed — native memory reclaimed");
    }
}
```

---

## Step 8: Capstone — Complete FFM Demo

```bash
# Run the full Panama demo
cat > /tmp/Panama.java << 'EOF'
import java.lang.foreign.*;
import java.lang.invoke.*;
import java.nio.charset.StandardCharsets;

public class Panama {
    public static void main(String[] args) throws Throwable {
        Linker linker = Linker.nativeLinker();
        MethodHandle strlen = linker.downcallHandle(
            linker.defaultLookup().find("strlen").orElseThrow(),
            FunctionDescriptor.of(ValueLayout.JAVA_LONG, ValueLayout.ADDRESS)
        );
        
        String[] testStrings = {"Hello", "World", "Project Panama!", ""};
        
        try (Arena arena = Arena.ofConfined()) {
            for (String s : testStrings) {
                byte[] bytes = s.getBytes(StandardCharsets.UTF_8);
                MemorySegment cStr = arena.allocate(bytes.length + 1);
                for (int i = 0; i < bytes.length; i++) {
                    cStr.set(ValueLayout.JAVA_BYTE, i, bytes[i]);
                }
                long len = (long) strlen.invoke(cStr);
                System.out.printf("strlen(\"%s\") = %d%n", s, len);
            }
        }
        
        // Layout demo
        StructLayout rect = MemoryLayout.structLayout(
            ValueLayout.JAVA_DOUBLE.withName("width"),
            ValueLayout.JAVA_DOUBLE.withName("height")
        );
        System.out.println("Rectangle layout: " + rect.byteSize() + " bytes");
        System.out.println("FFM API: SUCCESS");
    }
}
EOF
javac --enable-preview --release 21 /tmp/Panama.java -d /tmp 2>/dev/null
java --enable-preview --enable-native-access=ALL-UNNAMED -cp /tmp Panama
```

---

## Summary

| Concept | Class/API | Purpose |
|---|---|---|
| Memory segment | `MemorySegment` | Bounded native/heap memory |
| Memory lifetime | `Arena` | Scope-bound allocation |
| Native call | `Linker.downcallHandle()` | Java → C function |
| C callback | `Linker.upcallStub()` | C → Java function pointer |
| Struct layout | `MemoryLayout.structLayout()` | C struct mapping |
| Value layout | `ValueLayout.JAVA_INT` etc. | Primitive C types |
| Field access | `MemoryLayout.varHandle()` | Type-safe field read/write |
| Symbol lookup | `SymbolLookup` | Find native function by name |
