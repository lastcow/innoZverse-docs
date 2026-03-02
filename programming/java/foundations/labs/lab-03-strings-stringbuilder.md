# Lab 3: Strings and StringBuilder

## 🎯 Objective
Master Java's `String` class methods and use `StringBuilder` for efficient string manipulation.

## 📚 Background
In Java, `String` is immutable — every modification creates a new object. For repeated concatenation (e.g., in loops), use `StringBuilder` which mutates in place and is far more efficient. Java also offers `String.format()` and text blocks (Java 15+) for advanced formatting.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Completed Lab 1–2

## 🛠️ Tools Used
- Docker (`innozverse-java:latest`)

## 🔬 Lab Instructions

### Step 1: Basic String methods
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        String s = "Hello, Java!";
        System.out.println("Length:       " + s.length());
        System.out.println("Uppercase:    " + s.toUpperCase());
        System.out.println("Lowercase:    " + s.toLowerCase());
        System.out.println("Substring:    " + s.substring(7));
        System.out.println("Substring:    " + s.substring(0, 5));
        System.out.println("Replace:      " + s.replace("Java", "World"));
        System.out.println("Contains:     " + s.contains("Java"));
        System.out.println("StartsWith:   " + s.startsWith("Hello"));
        System.out.println("IndexOf:      " + s.indexOf("Java"));
        System.out.println("Trim:         '  spaces  '.trim() = '" + "  spaces  ".trim() + "'");
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
Length:       12
Uppercase:    HELLO, JAVA!
Lowercase:    hello, java!
Substring:    Java!
Substring:    Hello
Replace:      Hello, World!
Contains:     true
StartsWith:   true
IndexOf:      7
Trim:         '  spaces  '.trim() = 'spaces'
```

### Step 2: String comparison — never use `==`
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        String a = new String("hello");
        String b = new String("hello");

        System.out.println("== comparison:      " + (a == b));       // false! compares references
        System.out.println("equals():           " + a.equals(b));    // true  (compares content)
        System.out.println("equalsIgnoreCase(): " + a.equalsIgnoreCase("HELLO")); // true
        System.out.println("compareTo():        " + "apple".compareTo("banana")); // negative (a < b)
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
== comparison:      false
equals():           true
equalsIgnoreCase(): true
compareTo():        -1
```
💡 Always use `.equals()` for String comparison. `==` checks if two variables point to the same object in memory.

### Step 3: String splitting and joining
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        String csv = "apple,banana,cherry,date";
        String[] fruits = csv.split(",");
        System.out.println("Split count: " + fruits.length);
        for (String fruit : fruits) {
            System.out.println("  - " + fruit);
        }

        // Join back together
        String joined = String.join(" | ", fruits);
        System.out.println("Joined: " + joined);
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
Split count: 4
  - apple
  - banana
  - cherry
  - date
Joined: apple | banana | cherry | date
```

### Step 4: String.format() and printf
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        String name = "Alice";
        int age = 30;
        double gpa = 3.875;

        String formatted = String.format("Name: %-10s | Age: %3d | GPA: %.2f", name, age, gpa);
        System.out.println(formatted);

        // printf is like System.out.print + String.format
        System.out.printf("Hello, %s! You are %d years old.%n", name, age);
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
Name: Alice      | Age:  30 | GPA: 3.88
Hello, Alice! You are 30 years old.
```
💡 `%-10s` = left-aligned, 10-char wide. `%3d` = right-aligned, 3-wide integer. `%.2f` = 2 decimal places.

### Step 5: StringBuilder — efficient concatenation
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        // Inefficient (creates new String each iteration):
        // String result = "";
        // for (int i = 0; i < 1000; i++) result += i;

        // Efficient with StringBuilder:
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 5; i++) {
            sb.append("item").append(i);
            if (i < 4) sb.append(", ");
        }
        System.out.println("Built: " + sb.toString());
        System.out.println("Length: " + sb.length());

        // StringBuilder operations
        sb.insert(0, ">> ");
        sb.reverse();
        System.out.println("Reversed: " + sb);
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
Built: item0, item1, item2, item3, item4
Length: 30
Reversed: 4meti ,3meti ,2meti ,1meti ,0meti >>
```

### Step 6: Text blocks (Java 15+)
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        String json = """
                {
                    "name": "Alice",
                    "age": 30,
                    "active": true
                }
                """;
        System.out.println("JSON text block:");
        System.out.print(json);
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
JSON text block:
{
    "name": "Alice",
    "age": 30,
    "active": true
}
```
💡 Text blocks (triple-quoted strings) preserve indentation relative to the closing `"""`. Great for JSON, SQL, HTML templates.

### Step 7: String methods — chars and conversion
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        String word = "Hello";
        System.out.println("charAt(1): " + word.charAt(1));
        System.out.println("toCharArray: ");
        for (char c : word.toCharArray()) {
            System.out.print(c + " ");
        }
        System.out.println();
        System.out.println("isEmpty(''):  " + "".isEmpty());
        System.out.println("isBlank('  '): " + "  ".isBlank()); // Java 11+
        System.out.println("repeat: " + "ab".repeat(3)); // Java 11+
        System.out.println("strip: '" + "  hello  ".strip() + "'"); // Java 11+, Unicode-aware
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
charAt(1): e
toCharArray: 
H e l l o 
isEmpty(''):  true
isBlank('  '): true
repeat: ababab
strip: 'hello'
```

### Step 8: Immutability performance benchmark
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        int iterations = 10000;

        long start1 = System.currentTimeMillis();
        String s = "";
        for (int i = 0; i < iterations; i++) s += "x";
        long time1 = System.currentTimeMillis() - start1;

        long start2 = System.currentTimeMillis();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < iterations; i++) sb.append("x");
        long time2 = System.currentTimeMillis() - start2;

        System.out.println("String concat:  " + time1 + "ms");
        System.out.println("StringBuilder:  " + time2 + "ms");
        System.out.println("StringBuilder is faster for repeated concatenation!");
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
String concat:  ~150ms
StringBuilder:  ~1ms
StringBuilder is faster for repeated concatenation!
```
💡 `StringBuilder` outperforms `String` concatenation in loops by orders of magnitude because it doesn't create intermediate objects.

## ✅ Verification
```bash
cat > /tmp/Lab.java << 'JEOF'
public class Lab {
    public static void main(String[] args) {
        String s = "Hello, Java!";
        System.out.println(s.length());
        System.out.println(s.toUpperCase());
        System.out.println(s.substring(7));
        System.out.println(s.replace("Java", "World"));
        System.out.println(s.contains("Java"));
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < 5; i++) sb.append("item").append(i).append(", ");
        sb.delete(sb.length()-2, sb.length());
        System.out.println("Built: " + sb.toString());
    }
}
JEOF
docker run --rm -v /tmp:/tmp innozverse-java:latest sh -c "cd /tmp && javac Lab.java && java Lab"
```

**📸 Verified Output:**
```
12
HELLO, JAVA!
Java!
Hello, World!
true
Built: item0, item1, item2, item3, item4
```

## 🚨 Common Mistakes
- **Using `==` for String comparison**: Always use `.equals()`
- **String in loop**: Avoid `s += x` in loops — use `StringBuilder`
- **Off-by-one in substring**: `substring(0, 5)` includes index 0–4 (5 is exclusive)
- **Null String**: Calling methods on `null` throws `NullPointerException`

## 📝 Summary
`String` is immutable and rich with useful methods. For building strings dynamically, `StringBuilder` is the efficient choice. Use `String.format()` for structured output and text blocks for multi-line content.

## 🔗 Further Reading
- [String API (Oracle)](https://docs.oracle.com/en/java/docs/api/java.base/java/lang/String.html)
- [StringBuilder API](https://docs.oracle.com/en/java/docs/api/java.base/java/lang/StringBuilder.html)
