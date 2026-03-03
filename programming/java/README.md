# Java

> **Write once, run anywhere.** Java powers Android, enterprise backends, financial systems, and cloud-native microservices. The #1 language for large-scale backend engineering — with 30 years of ecosystem maturity and modern features from Java 21.

***

## 🗺️ Learning Path

<table data-view="cards">
  <thead>
    <tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>🌱 Foundations</strong></td>
      <td>15 labs from Hello World to a full inventory system. OOP, generics, streams, concurrency, NIO.2.</td>
      <td><a href="foundations/">foundations/</a></td>
    </tr>
    <tr>
      <td><strong>⚙️ Practitioner</strong></td>
      <td>Spring Boot REST APIs, JPA/Hibernate, JUnit 5, Docker, Maven/Gradle, design patterns.</td>
      <td><a href="practitioner/">practitioner/</a></td>
    </tr>
    <tr>
      <td><strong>🚀 Advanced</strong></td>
      <td>Microservices, reactive programming, Kafka, Redis, GraalVM native image, observability.</td>
      <td><a href="advanced/">advanced/</a></td>
    </tr>
  </tbody>
</table>

***

## 📋 Foundations — 15 Labs

{% tabs %}
{% tab title="Labs 1–5: Basics" %}
| # | Lab | Topics |
|---|-----|--------|
| 1 | [Hello World & JVM](foundations/labs/lab-01-hello-world.md) | compile, JVM, classpath, primitives |
| 2 | [Variables & Primitives](foundations/labs/lab-02-variables-primitives.md) | int/double/char/boolean, casting, overflow |
| 3 | [Strings & StringBuilder](foundations/labs/lab-03-strings-stringbuilder.md) | immutability, methods, formatting, regex |
| 4 | [Arrays](foundations/labs/lab-04-arrays.md) | 1D/2D arrays, sorting, Arrays utility |
| 5 | [Control Flow & Recursion](foundations/labs/lab-05-control-flow.md) | switch expressions, loops, binary search |
{% endtab %}

{% tab title="Labs 6–9: OOP" %}
| # | Lab | Topics |
|---|-----|--------|
| 6 | [OOP — Classes](foundations/labs/lab-06-oop-classes.md) | encapsulation, records, Builder pattern |
| 7 | [Inheritance & Polymorphism](foundations/labs/lab-07-inheritance.md) | extends, override, sealed classes |
| 8 | [Interfaces](foundations/labs/lab-08-interfaces.md) | functional interfaces, Strategy, Observer |
| 9 | [Collections](foundations/labs/lab-09-collections.md) | ArrayList, HashMap, HashSet, PriorityQueue |
{% endtab %}

{% tab title="Labs 10–15: Modern Java" %}
| # | Lab | Topics |
|---|-----|--------|
| 10 | [Exception Handling](foundations/labs/lab-10-exceptions.md) | hierarchy, chaining, Result type |
| 11 | [File I/O — NIO.2](foundations/labs/lab-11-file-io.md) | Path, Files.walk, WatchService |
| 12 | [Generics](foundations/labs/lab-12-generics.md) | bounds, wildcards, PECS |
| 13 | [Streams & Lambdas](foundations/labs/lab-13-streams.md) | filter/map/collect, groupingBy, parallel |
| 14 | [Concurrency](foundations/labs/lab-14-concurrency.md) | ExecutorService, CompletableFuture, virtual threads |
| 15 | [Capstone — Inventory](foundations/labs/lab-15-capstone.md) | all concepts, CLI app, CSV persistence |
{% endtab %}
{% endtabs %}

***

## ⚡ Java 21 Highlights

{% hint style="info" %}
All labs use **Java 21 LTS** — the most feature-rich Java release ever. Key modern features used throughout:
{% endhint %}

| Feature | Since | Used In |
|---------|-------|---------|
| **Records** | Java 16 | Lab 6, 9, 12, 15 |
| **Sealed interfaces** | Java 17 | Lab 7, 15 |
| **Pattern matching `instanceof`** | Java 16 | Lab 5, 7 |
| **Switch expressions** | Java 14 | Lab 5, 7, 8 |
| **Text blocks** | Java 15 | Lab 5 |
| **`var` type inference** | Java 10 | Lab 12 |
| **Virtual threads (Loom)** | Java 21 | Lab 14 |
| **Record patterns** | Java 21 | Lab 7, 12 |

***

## 🐳 Docker Quick Start

{% hint style="info" %}
All labs run inside Docker — no local Java install needed. Install Docker first, then pull the lab image.
{% endhint %}

### 1. Install Docker

{% tabs %}
{% tab title="Ubuntu / Debian" %}
```bash
# Remove old versions
sudo apt remove docker docker-engine docker.io containerd runc 2>/dev/null

# Install via official script (quickest)
curl -fsSL https://get.docker.com | sh

# Add your user to the docker group (no sudo needed)
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker --version
```
{% endtab %}

{% tab title="macOS" %}
```bash
# Option 1: Docker Desktop (GUI + CLI)
# Download from https://www.docker.com/products/docker-desktop/
# Or install via Homebrew:
brew install --cask docker

# Launch Docker Desktop from Applications, then verify
docker --version
```
{% endtab %}

{% tab title="Windows" %}
```powershell
# Option 1: Docker Desktop with WSL 2 backend (recommended)
# Download from https://www.docker.com/products/docker-desktop/

# Option 2: winget
winget install Docker.DockerDesktop

# Verify in PowerShell or Command Prompt
docker --version
```
{% endtab %}

{% tab title="RHEL / Fedora / CentOS" %}
```bash
# Fedora
sudo dnf install docker-ce docker-ce-cli containerd.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER

# Verify
docker --version
```
{% endtab %}
{% endtabs %}

{% hint style="warning" %}
After adding your user to the `docker` group on Linux, **log out and back in** (or run `newgrp docker`) for the change to take effect.
{% endhint %}

### 2. Pull the Java Lab Image

```bash
# Pull the pre-built Java 21 lab image from Docker Hub
docker pull zchencow/innozverse-java:latest

# Verify the image is ready
docker run --rm zchencow/innozverse-java:latest java --version
```

**Expected output:**
```
openjdk 21.0.10 2026-01-20 LTS
OpenJDK Runtime Environment Temurin-21.0.10+7 (build 21.0.10+7-LTS)
OpenJDK 64-Bit Server VM (build 21.0.10+7-LTS, mixed mode, sharing)
```

### 3. Run Your First Java Program

```bash
# One-liner Hello World
docker run --rm zchencow/innozverse-java:latest \
  sh -c 'echo "class H{public static void main(String[]a){System.out.println(\"Hello, Java 21!\");}}" > H.java && javac H.java && java H'

# Compile and run a local file
docker run --rm -v $(pwd):/app -w /app zchencow/innozverse-java:latest \
  sh -c "javac Main.java && java Main"

# Interactive REPL (JShell)
docker run --rm -it zchencow/innozverse-java:latest jshell
```

***

## 📊 Java vs the Ecosystem

| Use Case | Java Tool |
|----------|-----------|
| REST APIs | Spring Boot 3 |
| Persistence | JPA + Hibernate / Spring Data |
| Build | Maven / Gradle |
| Testing | JUnit 5 + Mockito |
| Containerization | Docker + Jib |
| Observability | Micrometer + Prometheus |
| Native binaries | GraalVM |

***

## 🔗 Resources

- [Oracle Java 21 Docs](https://docs.oracle.com/en/java/javase/21/)
- [Effective Java, 3rd Ed. — Joshua Bloch](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)
- [Spring Boot Reference](https://spring.io/projects/spring-boot)
- [Baeldung Java Tutorials](https://www.baeldung.com)
- [OpenJDK JEPs](https://openjdk.org/jeps/0)
