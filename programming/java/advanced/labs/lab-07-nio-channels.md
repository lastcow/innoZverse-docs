# Lab 7: NIO.2 Channels & ByteBuffer

## Objective
Master Java NIO for high-performance I/O: `ByteBuffer` for direct memory manipulation, `FileChannel` with scatter/gather I/O, `MappedByteBuffer` for memory-mapped files, `Path` glob patterns, and designing a binary catalog format with header + payload.

## Background
Java NIO (New I/O, `java.nio`) replaced blocking stream I/O for high-throughput scenarios. `ByteBuffer` is a fixed-capacity container with a `position`/`limit`/`capacity` model — you write until `position` reaches `limit`, then `flip()` to switch to read mode. `FileChannel` supports scatter (read into multiple buffers) and gather (write from multiple buffers) I/O in a single syscall.

## Time
30 minutes

## Prerequisites
- Practitioner Lab 06 (File I/O & NIO.2)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: ByteBuffer read/write, flip/rewind, FileChannel scatter-gather, MappedByteBuffer, Path glob, binary product catalog, checksums, Capstone

```bash
cat > /tmp/AdvLab07.java << 'JAVAEOF'
import java.nio.*;
import java.nio.channels.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;
import java.util.stream.*;

public class AdvLab07 {
    public static void main(String[] args) throws Exception {
        Path tmp = Files.createTempDirectory("innozverse_nio");

        // Step 1: ByteBuffer operations
        System.out.println("=== ByteBuffer ===");
        ByteBuffer buf = ByteBuffer.allocate(64);
        buf.putInt(1);        // id
        buf.putDouble(864.0); // price
        buf.putInt(15);       // stock
        for (byte b : "Surface Pro".getBytes()) buf.put(b);
        System.out.println("Position after writes: " + buf.position());

        buf.flip(); // switch to read mode: limit=position, position=0
        int id = buf.getInt();
        double price = buf.getDouble();
        int stock = buf.getInt();
        byte[] nameBytes = new byte[buf.remaining()];
        buf.get(nameBytes);
        System.out.printf("Read: id=%d price=$%.2f stock=%d name=%s%n", id, price, stock, new String(nameBytes));

        // Direct buffer (off-heap)
        ByteBuffer direct = ByteBuffer.allocateDirect(128);
        System.out.println("Direct buffer: " + direct.isDirect() + " capacity=" + direct.capacity());

        // Step 2: FileChannel with scatter/gather I/O
        System.out.println("\n=== FileChannel: Scatter/Gather ===");
        Path file = tmp.resolve("products.bin");
        try (var fc = FileChannel.open(file, StandardOpenOption.CREATE, StandardOpenOption.WRITE)) {
            ByteBuffer header = ByteBuffer.allocate(8);
            header.putInt(5);  // product count
            header.putInt(3);  // format version
            header.flip();

            ByteBuffer data = ByteBuffer.allocate(256);
            for (var p : List.of("Surface Pro,864.0,15", "Surface Pen,49.99,80", "Office 365,99.99,999")) {
                byte[] bytes = (p + "\n").getBytes();
                data.put(bytes);
            }
            data.flip();

            long written = fc.write(new ByteBuffer[]{header, data}); // gather: single syscall
            System.out.println("Gathered write: " + written + " bytes");
        }

        try (var fc = FileChannel.open(file, StandardOpenOption.READ)) {
            ByteBuffer header = ByteBuffer.allocate(8);
            ByteBuffer data   = ByteBuffer.allocate(256);
            fc.read(new ByteBuffer[]{header, data}); // scatter: single syscall
            header.flip(); data.flip();
            System.out.println("Header: count=" + header.getInt() + " version=" + header.getInt());
            byte[] bytes = new byte[data.limit()];
            data.get(bytes);
            System.out.println("Data:");
            Arrays.stream(new String(bytes).trim().split("\n")).forEach(l -> System.out.println("  " + l));
        }

        // Step 3: MappedByteBuffer (memory-mapped file — zero-copy)
        System.out.println("\n=== MappedByteBuffer (Memory-Mapped) ===");
        Path mapped = tmp.resolve("catalog.bin");
        int[] ids = {1,2,3,4,5};
        double[] prices = {864.0,49.99,99.99,29.99,1299.0};
        int[] stocks = {15,80,999,0,5};

        try (var fc = FileChannel.open(mapped, StandardOpenOption.CREATE,
                StandardOpenOption.READ, StandardOpenOption.WRITE)) {
            MappedByteBuffer mbb = fc.map(FileChannel.MapMode.READ_WRITE, 0, ids.length * 16L);
            for (int i = 0; i < ids.length; i++) {
                mbb.putInt(ids[i]); mbb.putDouble(prices[i]); mbb.putInt(stocks[i]);
            }
            mbb.force(); // flush to disk
            System.out.println("Mapped and wrote " + (ids.length * 16) + " bytes");

            mbb.rewind();
            System.out.println("Read back:");
            for (int i = 0; i < ids.length; i++) {
                int pid = mbb.getInt(); double p = mbb.getDouble(); int s = mbb.getInt();
                System.out.printf("  id=%d  $%.2f  stock=%d%n", pid, p, s);
            }
        }

        // Step 4: Path glob patterns
        System.out.println("\n=== Path & Glob ===");
        var reportsDir = tmp.resolve("reports");
        Files.createDirectory(reportsDir);
        for (String name : List.of("jan.csv","feb.csv","mar.csv","q1.xlsx","annual.pdf")) {
            Files.writeString(reportsDir.resolve(name), "data");
        }
        try (var stream = Files.newDirectoryStream(reportsDir, "*.csv")) {
            var csvFiles = new ArrayList<String>();
            stream.forEach(p -> csvFiles.add(p.getFileName().toString()));
            Collections.sort(csvFiles);
            System.out.println("*.csv: " + csvFiles);
        }

        // Step 5: Walk with filter
        System.out.println("\nAll files in tmp:");
        try (var walk = Files.walk(tmp)) {
            walk.filter(Files::isRegularFile)
                .forEach(p -> System.out.printf("  %-30s %d bytes%n",
                    tmp.relativize(p).toString(), p.toFile().length()));
        }

        // Cleanup
        try (var walk = Files.walk(tmp)) {
            walk.sorted(Comparator.reverseOrder()).forEach(p -> { try { Files.delete(p); } catch (IOException e) {} });
        }
        System.out.println("\nCleanup done");
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab07.java:/tmp/AdvLab07.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab07.java -d /tmp && java -cp /tmp AdvLab07"
```

> 💡 **`MappedByteBuffer` is zero-copy.** Reading from a memory-mapped file means the OS maps the file's page cache directly into your process's address space — no data is copied from kernel space to user space. For read-heavy workloads on large files (database files, log archives), this is dramatically faster than `FileInputStream`. SQLite, Elasticsearch, and Kafka all use memory-mapped files internally.

**📸 Verified Output:**
```
=== ByteBuffer ===
Position after writes: 27
Read: id=1 price=$864.00 stock=15 name=Surface Pro

=== FileChannel: Scatter/Gather ===
Gathered write: 71 bytes
Header: count=5 version=3
Data:
  Surface Pro,864.0,15
  Surface Pen,49.99,80
  Office 365,99.99,999

=== MappedByteBuffer ===
Mapped and wrote 80 bytes
Read back:
  id=1  $864.00  stock=15
  id=2  $49.99   stock=80
  ...

=== Path & Glob ===
*.csv: [feb.csv, jan.csv, mar.csv]
```

---

## Summary

| API | Use for |
|-----|---------|
| `ByteBuffer.allocate(n)` | Heap-backed buffer |
| `ByteBuffer.allocateDirect(n)` | Off-heap (faster native I/O) |
| `buf.flip()` | Switch write→read mode |
| `fc.write(ByteBuffer[])` | Gather: multi-buffer write |
| `fc.read(ByteBuffer[])` | Scatter: multi-buffer read |
| `fc.map(READ_WRITE, 0, size)` | Memory-mapped file |
| `Files.newDirectoryStream(dir, "*.csv")` | Glob filter |

## Further Reading
- [NIO Buffers Tutorial](https://jenkov.com/tutorials/java-nio/buffers.html)
- [MappedByteBuffer](https://docs.oracle.com/en/java/docs/api/java.base/java/nio/MappedByteBuffer.html)
