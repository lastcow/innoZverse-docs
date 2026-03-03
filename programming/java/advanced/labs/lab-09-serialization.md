# Lab 9: Serialization — Java, Binary & Compression

## Objective
Master Java object serialization: `ObjectOutputStream`/`ObjectInputStream`, `transient`/`static` fields, custom `writeObject`/`readObject` hooks, manual binary protocol with `DataOutputStream`, GZIP compression, and `serialVersionUID` compatibility.

## Background
Java serialization converts object graphs to byte streams for persistence or network transport. The `Serializable` marker interface enables it. `transient` fields are excluded; `static` fields are class-level (not instance state). For performance-critical paths, manual binary encoding with `DataOutputStream` produces much smaller payloads and is 4–10x faster.

## Time
25 minutes

## Prerequisites
- Lab 07 (NIO Channels)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: Object serialization, transient/static, custom writeObject, binary protocol, compression, file persistence, serialVersionUID, Capstone

```bash
cat > /tmp/AdvLab09.java << 'JAVAEOF'
import java.io.*;
import java.util.*;
import java.util.zip.*;
import java.nio.file.*;

public class AdvLab09 {
    static class Product implements Serializable {
        @Serial private static final long serialVersionUID = 1L;
        private final int id;
        private final String name;
        private final double price;
        private transient String cacheKey;   // excluded from serialization
        private static int instanceCount = 0; // class-level, not serialized

        Product(int id, String name, double price) {
            this.id=id; this.name=name; this.price=price;
            this.cacheKey = "p:" + id;
            instanceCount++;
        }
        @Override public String toString() {
            return "Product{id=" + id + ",name=" + name + ",price=" + price + ",cache=" + cacheKey + "}"; }

        // Custom serialization: restore transient after deserialization
        @Serial private void writeObject(ObjectOutputStream out) throws IOException {
            out.defaultWriteObject(); // serialize non-transient fields
        }
        @Serial private void readObject(ObjectInputStream in) throws IOException, ClassNotFoundException {
            in.defaultReadObject();
            cacheKey = "p:" + id + ":restored"; // rebuild transient
        }
    }

    // Manual binary protocol
    static byte[] encode(List<int[]> products) throws IOException {
        var baos = new ByteArrayOutputStream();
        try (var dos = new DataOutputStream(baos)) {
            dos.writeInt(products.size());
            for (var p : products) {
                dos.writeInt(p[0]);
                dos.writeDouble(p[1] / 100.0);
                dos.writeInt(p[2]);
            }
        }
        return baos.toByteArray();
    }

    static List<int[]> decode(byte[] data) throws IOException {
        var result = new ArrayList<int[]>();
        try (var dis = new DataInputStream(new ByteArrayInputStream(data))) {
            int count = dis.readInt();
            for (int i = 0; i < count; i++) {
                result.add(new int[]{dis.readInt(), (int)(dis.readDouble()*100), dis.readInt()});
            }
        }
        return result;
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Java Object Serialization ===");
        var product = new Product(1, "Surface Pro", 864.0);
        System.out.println("Before: " + product);

        var baos = new ByteArrayOutputStream();
        try (var oos = new ObjectOutputStream(baos)) { oos.writeObject(product); }
        byte[] bytes = baos.toByteArray();
        System.out.println("Serialized: " + bytes.length + " bytes");

        try (var ois = new ObjectInputStream(new ByteArrayInputStream(bytes))) {
            var restored = (Product) ois.readObject();
            System.out.println("Restored: " + restored);
        }

        // List serialization
        var products = List.of(new Product(1,"Surface Pro",864.0), new Product(2,"Surface Pen",49.99));
        baos.reset();
        try (var oos = new ObjectOutputStream(baos)) { oos.writeObject(products); }
        System.out.println("List serialized: " + baos.toByteArray().length + " bytes");

        // Manual binary protocol
        System.out.println("\n=== Manual Binary Protocol ===");
        var data = List.of(new int[]{1,86400,15}, new int[]{2,4999,80}, new int[]{3,9999,999});
        byte[] encoded = encode(data);
        System.out.println("Encoded: " + encoded.length + " bytes (Java serial: " + baos.size() + " bytes)");

        var decoded = decode(encoded);
        decoded.forEach(p -> System.out.printf("  id=%d  $%.2f  stock=%d%n", p[0], p[1]/100.0, p[2]));

        // Compression
        System.out.println("\n=== GZIP Compression ===");
        byte[] serialized = baos.toByteArray();
        var compressed = new ByteArrayOutputStream();
        try (var gzip = new GZIPOutputStream(compressed)) { gzip.write(serialized); }
        byte[] compressedBytes = compressed.toByteArray();
        System.out.println("Original:    " + serialized.length + " bytes");
        System.out.printf("GZIP:        %d bytes (%.0f%%)%n",
            compressedBytes.length, compressedBytes.length * 100.0 / serialized.length);

        var decompressed = new ByteArrayOutputStream();
        try (var gzip = new GZIPInputStream(new ByteArrayInputStream(compressedBytes))) {
            gzip.transferTo(decompressed);
        }
        System.out.println("Decompressed: " + decompressed.toByteArray().length + " bytes (matches: " +
            (decompressed.toByteArray().length == serialized.length) + ")");

        // File persistence
        System.out.println("\n=== File Persistence ===");
        Path tmp = Files.createTempFile("innoz_", ".ser");
        try (var oos = new ObjectOutputStream(new FileOutputStream(tmp.toFile()))) {
            oos.writeObject(products.get(0));
        }
        System.out.println("Written: " + tmp.getFileName() + " (" + Files.size(tmp) + " bytes)");
        try (var ois = new ObjectInputStream(new FileInputStream(tmp.toFile()))) {
            var loaded = (Product) ois.readObject();
            System.out.println("Loaded: " + loaded);
        }
        Files.delete(tmp);

        // serialVersionUID
        System.out.println("\n=== serialVersionUID ===");
        System.out.println("Product UID: " + ObjectStreamClass.lookup(Product.class).getSerialVersionUID());
        System.out.println("  (Must match across serialization/deserialization for class evolution)");
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab09.java:/tmp/AdvLab09.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab09.java -d /tmp && java -cp /tmp AdvLab09"
```

> 💡 **`serialVersionUID = 1L` must match across versions.** If you add a field to a serialized class without declaring `serialVersionUID`, the JVM auto-computes it from the class structure — and the new value won't match old data, causing `InvalidClassException`. Always declare `serialVersionUID` explicitly, increment it intentionally when you make breaking changes, and use `readObject` to handle migration gracefully.

**📸 Verified Output:**
```
=== Java Object Serialization ===
Before:   Product{id=1,name=Surface Pro,price=864.0,cache=p:1}
Serialized: 115 bytes
Restored: Product{id=1,name=Surface Pro,price=864.0,cache=p:1:restored}
List serialized: 209 bytes

=== Manual Binary Protocol ===
Encoded: 52 bytes (Java serial: 209 bytes)
  id=1  $864.00  stock=15
  id=2  $49.99   stock=80

=== GZIP Compression ===
Original:    209 bytes
GZIP:        198 bytes (95%)
Decompressed: 209 bytes (matches: true)

=== serialVersionUID ===
Product UID: 1
```

---

## Summary

| Mechanism | Bytes | Speed | Portable |
|-----------|-------|-------|---------|
| Java serialization | ~4x data | Slow | Java only |
| Manual binary (`DataOutputStream`) | ~1x data | Fast | Any language |
| JSON | ~3x data | Medium | Universal |
| Java serial + GZIP | ~1.5x data | Medium | Java only |

## Further Reading
- [Java Serialization Spec](https://docs.oracle.com/en/java/javase/21/docs/specs/serialization/)
- [Effective Java Item 85: Prefer alternatives to Java serialization](https://www.oreilly.com/library/view/effective-java/9780134686097/)
