# Java Advanced

Master advanced Java 21: reflection internals, virtual threads, cryptography, NIO, ForkJoin, sealed ADTs, annotation frameworks, and capstone production service design.

{% hint style="info" %}
**Prerequisites:** Complete Java Practitioner before starting Advanced labs.
{% endhint %}

## Quick Start

{% tabs %}
{% tab title="🐳 Docker (Recommended)" %}
```bash
docker pull zchencow/innozverse-java:latest
docker run --rm zchencow/innozverse-java:latest java --version
```
{% endtab %}
{% tab title="🐧 Linux / macOS" %}
```bash
sdk install java 21.0.3-tem   # SDKMAN
java --version                 # requires Java 21+
```
{% endtab %}
{% tab title="🪟 Windows" %}
```powershell
winget install EclipseAdoptium.Temurin.21.JDK
java --version
```
{% endtab %}
{% endtabs %}

## Labs

<table data-view="cards">
<thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead>
<tbody>
<tr><td><strong>Lab 01</strong><br>Dynamic Proxies</td><td>Proxy.newProxyInstance, MethodHandles, type tokens</td><td><a href="labs/lab-01-dynamic-proxy-reflection.md">lab-01</a></td></tr>
<tr><td><strong>Lab 02</strong><br>Virtual Threads</td><td>Executors.newVirtualThreadPerTaskExecutor, pinning</td><td><a href="labs/lab-02-virtual-threads.md">lab-02</a></td></tr>
<tr><td><strong>Lab 03</strong><br>Advanced Generics</td><td>ImmutableList, PECS wildcards, type erasure</td><td><a href="labs/lab-03-advanced-generics.md">lab-03</a></td></tr>
<tr><td><strong>Lab 04</strong><br>Design Patterns</td><td>Decorator, Chain of Responsibility, Visitor, Template</td><td><a href="labs/lab-04-design-patterns-advanced.md">lab-04</a></td></tr>
<tr><td><strong>Lab 05</strong><br>Advanced JDBC</td><td>Window functions, CTEs, upsert, JSON extract</td><td><a href="labs/lab-05-advanced-jdbc.md">lab-05</a></td></tr>
<tr><td><strong>Lab 06</strong><br>Cryptography</td><td>SHA-256, HMAC, AES-256-GCM, RSA, SecureRandom</td><td><a href="labs/lab-06-cryptography.md">lab-06</a></td></tr>
<tr><td><strong>Lab 07</strong><br>NIO Channels</td><td>ByteBuffer, FileChannel scatter/gather, MappedByteBuffer</td><td><a href="labs/lab-07-nio-channels.md">lab-07</a></td></tr>
<tr><td><strong>Lab 08</strong><br>ForkJoinPool</td><td>RecursiveTask, RecursiveAction, work stealing</td><td><a href="labs/lab-08-forkjoin.md">lab-08</a></td></tr>
<tr><td><strong>Lab 09</strong><br>Serialization</td><td>ObjectOutputStream, binary protocol, GZIP</td><td><a href="labs/lab-09-serialization.md">lab-09</a></td></tr>
<tr><td><strong>Lab 10</strong><br>Performance</td><td>String, collections, stream vs loop, memoization</td><td><a href="labs/lab-10-performance.md">lab-10</a></td></tr>
<tr><td><strong>Lab 11</strong><br>Advanced Concurrency</td><td>Semaphore, ReadWriteLock, BlockingQueue, Phaser</td><td><a href="labs/lab-11-advanced-concurrency.md">lab-11</a></td></tr>
<tr><td><strong>Lab 12</strong><br>Annotation Frameworks</td><td>@RestController/@GetMapping runtime scanner</td><td><a href="labs/lab-12-annotation-driven-frameworks.md">lab-12</a></td></tr>
<tr><td><strong>Lab 13</strong><br>Records & Sealed</td><td>Compact constructor, withers, sealed ADTs, deconstruction</td><td><a href="labs/lab-13-records-sealed-deep-dive.md">lab-13</a></td></tr>
<tr><td><strong>Lab 14</strong><br>Text Blocks</td><td>Text blocks, String.formatted, regex named groups</td><td><a href="labs/lab-14-text-blocks-strings.md">lab-14</a></td></tr>
<tr><td><strong>Lab 15</strong><br>🏆 Capstone</td><td>Production order service — all techniques combined</td><td><a href="labs/lab-15-capstone.md">lab-15</a></td></tr>
</tbody>
</table>
