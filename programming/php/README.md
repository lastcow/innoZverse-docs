# PHP

> **The web's most deployed language.** PHP powers over 75% of the web — from WordPress to Facebook's HHVM lineage. PHP 8.3 brings a mature type system, fibers, enums, and JIT compilation that make it a serious choice for APIs, CLIs, and full-stack web development.

***

## 🗺️ Learning Path

<table data-view="cards">
  <thead>
    <tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>🌱 Foundations</strong></td>
      <td>15 labs from Hello World to a full REST API. OOP, PDO, Composer, namespaces, type system.</td>
      <td><a href="foundations/">foundations/</a></td>
    </tr>
    <tr>
      <td><strong>⚙️ Practitioner</strong></td>
      <td>Laravel / Slim REST APIs, Eloquent ORM, PHPUnit, queues, Docker, PSR standards.</td>
      <td><a href="practitioner/">practitioner/</a></td>
    </tr>
    <tr>
      <td><strong>🚀 Advanced</strong></td>
      <td>Async with Fibers, Swoole/ReactPHP, Redis, message queues, DDD, performance tuning.</td>
      <td><a href="advanced/">advanced/</a></td>
    </tr>
    <tr>
      <td><strong>🏆 Expert</strong></td>
      <td>PHP internals, extension authoring, JIT profiling, C FFI, opcache optimization, Zend Engine.</td>
      <td><a href="expert/">expert/</a></td>
    </tr>
  </tbody>
</table>

***

## ⚡ PHP 8.3 Highlights

{% hint style="info" %}
All labs use **PHP 8.3** — the latest stable release with the most powerful type system PHP has ever had. Key modern features used throughout:
{% endhint %}

| Feature | Since | Description |
|---------|-------|-------------|
| **Readonly classes** | PHP 8.2 | All properties readonly by default |
| **Typed class constants** | PHP 8.3 | `const string VERSION = '1.0';` |
| **`json_validate()`** | PHP 8.3 | Validate JSON without decoding |
| **Fibers** | PHP 8.1 | Cooperative multitasking / async primitives |
| **Enums** | PHP 8.1 | Native backed and pure enumerations |
| **`match` expression** | PHP 8.0 | Strict, exhaustive switch replacement |
| **Named arguments** | PHP 8.0 | `array_slice(array: $a, offset: 1)` |
| **Constructor promotion** | PHP 8.0 | `public function __construct(public string $name)` |
| **Union types** | PHP 8.0 | `int\|string` type declarations |
| **Nullsafe operator** | PHP 8.0 | `$user?->getProfile()?->getAvatar()` |

***

## 🐳 Docker Quick Start

{% hint style="info" %}
All labs run inside Docker — no local PHP install needed. Install Docker first, then pull the lab image.
{% endhint %}

### 1. Install Docker

{% tabs %}
{% tab title="Ubuntu/Debian" %}
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

{% tab title="Alpine" %}
```sh
# Install Docker on Alpine Linux
apk add docker docker-cli

# Enable and start the service
rc-update add docker default
service docker start

# Add your user to the docker group
addgroup $USER docker

# Verify
docker --version
```
{% endtab %}
{% endtabs %}

{% hint style="info" %}
After adding your user to the `docker` group on Linux, **log out and back in** (or run `newgrp docker`) for the change to take effect.
{% endhint %}

### 2. Pull the PHP Lab Image

```bash
# Pull the pre-built PHP 8.3 lab image from Docker Hub
docker pull zchencow/innozverse-php:latest

# Verify the image is ready
docker run --rm zchencow/innozverse-php:latest php --version
```

**Expected output:**
```
PHP 8.3.x (cli) (built: ...)
Copyright (c) The PHP Group
Zend Engine v4.3.x
```

### 3. Run the Interactive PHP Shell

```bash
# Launch the interactive PHP REPL
docker run --rm -it zchencow/innozverse-php:latest php -a

# Run a local PHP file
docker run --rm -v $(pwd):/app -w /app zchencow/innozverse-php:latest php script.php

# One-liner Hello World
docker run --rm zchencow/innozverse-php:latest php -r 'echo "Hello, PHP 8.3!\n";'
```

***

## 📚 What You'll Learn

### 🌱 Foundations
Start from zero. Master PHP syntax, OOP fundamentals, the type system, PDO/SQLite, Composer, and PSR-4 autoloading. Build a full REST API by Lab 15. No prior PHP experience required — just basic programming literacy.

### ⚙️ Practitioner
Go framework-native. Build production-quality REST APIs with Laravel or Slim, manage databases with Eloquent, write reliable tests with PHPUnit, and containerize your apps with Docker Compose.

### 🚀 Advanced
Unlock PHP's concurrency model. Work with Fibers for async I/O, Swoole/ReactPHP event loops, Redis caching, RabbitMQ queues, and apply Domain-Driven Design to complex PHP systems.

### 🏆 Expert
Dive into PHP internals. Write C extensions, profile JIT output, inspect opcache, use the C FFI, and understand the Zend Engine well enough to contribute upstream or build high-performance infrastructure.

{% hint style="info" %}
**New to PHP?** Start with `Foundations → Lab 01`. Each lab builds on the last — don't skip ahead. The capstone (Lab 15) ties everything together into a working REST API you can deploy.
{% endhint %}

***

## 🔗 Resources

- [PHP 8.3 Official Docs](https://www.php.net/manual/en/)
- [PHP: The Right Way](https://phptherightway.com/)
- [Composer — PHP Dependency Manager](https://getcomposer.org/)
- [Laravel Documentation](https://laravel.com/docs)
- [PSR Standards (PHP-FIG)](https://www.php-fig.org/psr/)
- [PHP Internals Book](https://www.phpinternalsbook.com/)
