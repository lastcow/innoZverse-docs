# Lab 2: Variables, Primitives, and Type Casting

## 🎯 Objective
Understand Java's primitive data types, variable declaration, and type casting between numeric types.

## 📚 Background
Java has 8 primitive types: `byte`, `short`, `int`, `long`, `float`, `double`, `char`, and `boolean`. Unlike objects, primitives are stored directly in memory. Understanding when to use each type and how to safely cast between them is fundamental to Java programming.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Completed Lab 1 (Hello World)
- Basic understanding of data types

## 🛠️ Tools Used
- Docker (`innozverse-java:latest`)
- `javac`, `java`

## 🔬 Lab Instructions

### Step 1: Declare and use integer types
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        byte  b = 127;           // -128 to 127
        short s = 32767;         // -32,768 to 32,767
        int   i = 2_147_483_647; // ~2.1 billion (underscores for readability)
        long  l = 9_223_372_036_854_775_807L; // L suffix for long literals

        System.out.println("byte:  " + b);
        System.out.println("short: " + s);
        System.out.println("int:   " + i);
        System.out.println("long:  " + l);
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
byte:  127
short: 32767
int:   2147483647
long:  9223372036854775807
```

### Step 2: Floating-point and boolean types
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        float  f = 3.14f;       // f suffix required for float literals
        double d = 3.141592653589793; // default floating-point type
        boolean flag = true;
        char    c = 'A';        // Unicode character (16-bit)

        System.out.println("float:   " + f);
        System.out.println("double:  " + d);
        System.out.println("boolean: " + flag);
        System.out.println("char:    " + c + " (code: " + (int) c + ")");
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
float:   3.14
double:  3.141592653589793
boolean: true
char:    A (code: 65)
```
💡 `float` has ~7 decimal digits of precision; `double` has ~15. Always use `double` unless memory is critical.

### Step 3: Widening (implicit) type conversion
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        // Widening: smaller type → larger type (automatic, no data loss)
        int    i = 1000;
        long   l = i;       // int → long (widening)
        double d = l;       // long → double (widening)

        System.out.println("int    → long:   " + l);
        System.out.println("long   → double: " + d);
        System.out.println("Types: safe widening, no cast needed");
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
int    → long:   1000
long   → double: 1000.0
Types: safe widening, no cast needed
```

### Step 4: Narrowing (explicit) type casting
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        // Narrowing: larger type → smaller type (requires explicit cast, may lose data)
        double d = 9.99;
        int    i = (int) d;   // Truncates decimal part (not rounded!)
        byte   b = (byte) 300; // 300 > 127, overflow causes wrapping

        System.out.println("double 9.99 → int: " + i);     // 9
        System.out.println("int 300 → byte:    " + b);     // 44 (300 - 256)
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
double 9.99 → int: 9
int 300 → byte:    44
```
💡 `(int) 9.99` truncates to `9`, not rounds to `10`. Use `Math.round()` to round.

### Step 5: Arithmetic and integer overflow
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        int max = Integer.MAX_VALUE;
        System.out.println("Max int: " + max);
        System.out.println("Max int + 1: " + (max + 1)); // Overflow!

        // Safe: use long
        long safeAdd = (long) max + 1;
        System.out.println("Safe with long: " + safeAdd);

        // Integer division truncates
        System.out.println("7 / 2 = " + (7 / 2));         // 3 (not 3.5)
        System.out.println("7.0 / 2 = " + (7.0 / 2));     // 3.5
        System.out.println("7 % 2 = " + (7 % 2));          // 1 (remainder)
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
Max int: 2147483647
Max int + 1: -2147483648
Safe with long: 2147483648
7 / 2 = 3
7.0 / 2 = 3.5
7 % 2 = 1
```

### Step 6: String conversion and parsing
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        // Convert primitives to String
        int num = 42;
        String s1 = String.valueOf(num);
        String s2 = Integer.toString(num);
        String s3 = "" + num; // Concatenation trick

        // Parse String to primitives
        int    parsed  = Integer.parseInt("123");
        double parsedD = Double.parseDouble("3.14");

        System.out.println("int → String: '" + s1 + "'");
        System.out.println("Parsed int:   " + parsed);
        System.out.println("Parsed double: " + parsedD);

        // Constants
        System.out.println("Integer.MAX_VALUE: " + Integer.MAX_VALUE);
        System.out.println("Double.MAX_VALUE:  " + Double.MAX_VALUE);
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
int → String: '42'
Parsed int:   123
Parsed double: 3.14
Integer.MAX_VALUE: 2147483647
Double.MAX_VALUE:  1.7976931348623157E308
```

### Step 7: `var` — local variable type inference (Java 10+)
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        var message = "Hello";    // inferred as String
        var count   = 42;          // inferred as int
        var pi      = 3.14;        // inferred as double

        System.out.println(message + " — count=" + count + ", pi=" + pi);
        System.out.println("Types are still static — var just infers them");
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
Hello — count=42, pi=3.14
Types are still static — var just infers them
```

### Step 8: Final variables (constants)
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    static final double PI = 3.14159265358979;
    static final int MAX_USERS = 1000;

    public static void main(String[] args) {
        final int localConst = 99; // local constant
        System.out.println("PI = " + PI);
        System.out.println("MAX_USERS = " + MAX_USERS);
        System.out.println("localConst = " + localConst);
        // localConst = 100; // Would cause compile error: cannot assign to final variable
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
PI = 3.14159265358979
MAX_USERS = 1000
localConst = 99
```

## ✅ Verification
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        int i = 42;
        double d = i;           // widening
        int back = (int) 9.99;  // narrowing
        System.out.println("i=" + i + " d=" + d + " back=" + back);
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:** `i=42 d=42.0 back=9`

## 🚨 Common Mistakes
- **Missing `L` suffix**: `long x = 9999999999` → compile error; use `9999999999L`
- **Missing `f` suffix**: `float x = 3.14` → compile error; use `3.14f`
- **Integer overflow**: `int + 1` silently wraps around; cast to `long` for large numbers
- **Casting truncates**: `(int) 9.9` is `9`, not `10`

## 📝 Summary
Java's 8 primitive types cover integers (`byte`/`short`/`int`/`long`), floats (`float`/`double`), text (`char`), and logic (`boolean`). Widening conversions are automatic; narrowing requires explicit casts. Use `final` for constants and `var` for type inference.

## 🔗 Further Reading
- [Java Primitive Data Types (Oracle)](https://docs.oracle.com/javase/tutorial/java/nutsandbolts/datatypes.html)
- [Type Casting in Java](https://docs.oracle.com/javase/tutorial/java/nutsandbolts/datatypes.html)
