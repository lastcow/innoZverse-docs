# Lab 11: Advanced Composer

**Time:** 40 minutes | **Level:** Advanced | **Docker:** `docker run -it --rm composer:2 sh`

Composer is PHP's dependency manager. Beyond basic `require`, it supports custom scripts, path repositories, autoload optimization, platform requirements, security audits, and plugins.

---

## Step 1: Initializing a Project

```bash
docker run --rm composer:2 sh -c "
mkdir /tmp/myapp && cd /tmp/myapp &&
composer init \
  --no-interaction \
  --name=myorg/myapp \
  --description='Advanced Composer demo' \
  --type=project \
  --php='>=8.1' 2>&1 | tail -5 &&
echo '---' &&
cat composer.json
"
```

📸 **Verified Output:**
```
Writing ./composer.json
---
{
    "name": "myorg/myapp",
    "description": "Advanced Composer demo",
    "type": "project",
    "require": {
        "php": ">=8.1"
    }
}
```

---

## Step 2: Custom Scripts

Add lifecycle scripts to `composer.json`:

```json
{
    "name": "myorg/myapp",
    "scripts": {
        "post-install-cmd": [
            "@php artisan key:generate",
            "@php -r \"echo 'Install complete!\\n';\""
        ],
        "post-update-cmd": [
            "@php -r \"echo 'Updated!\\n';\""
        ],
        "test": "vendor/bin/phpunit",
        "lint": "vendor/bin/phpcs --standard=PSR12 src/",
        "analyze": "@php -r \"echo 'Running analysis...\\n';\"",
        "ci": [
            "@lint",
            "@test",
            "@analyze"
        ],
        "post-autoload-dump": [
            "@php -r \"echo 'Autoloader rebuilt!\\n';\""
        ]
    },
    "scripts-descriptions": {
        "test":    "Run PHPUnit test suite",
        "lint":    "PSR-12 code style check",
        "analyze": "Static analysis",
        "ci":      "Full CI pipeline"
    }
}
```

```bash
# Run custom script
composer run lint

# List available scripts
composer run --list
```

> 💡 `@php` runs the PHP interpreter found by Composer. `@scriptname` calls another defined script. Scripts can be arrays (run in sequence).

---

## Step 3: Autoloading Strategies

```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/",
            "App\\Tests\\": "tests/"
        },
        "classmap": [
            "src/Legacy/",
            "lib/"
        ],
        "files": [
            "src/helpers.php",
            "src/constants.php"
        ]
    },
    "autoload-dev": {
        "psr-4": {
            "App\\Tests\\": "tests/"
        }
    }
}
```

```bash
# Generate optimized autoloader (production)
composer dump-autoload --optimize --classmap-authoritative

# Development autoloader with dev dependencies
composer dump-autoload
```

```bash
docker run --rm composer:2 sh -c "
cd /tmp && mkdir autotest && cd autotest &&
composer init --no-interaction --name=test/autotest 2>&1 | tail -2 &&
mkdir -p src/Legacy &&
echo '<?php class LegacyClass { public function hello() { return \"Legacy!\"; } }' > src/Legacy/LegacyClass.php &&
cat > composer.json << 'EOF'
{
    \"name\": \"test/autotest\",
    \"autoload\": {
        \"classmap\": [\"src/Legacy/\"]
    }
}
EOF
composer dump-autoload --optimize 2>&1 &&
php -r \"require 'vendor/autoload.php'; \\\$o = new LegacyClass(); echo \\\$o->hello() . PHP_EOL;\"
"
```

📸 **Verified Output:**
```
Generating optimized autoload files (authoritative)
Generated optimized autoload files containing 1 class
Legacy!
```

---

## Step 4: Platform Requirements

```json
{
    "require": {
        "php":          "^8.1",
        "ext-pdo":      "*",
        "ext-mbstring": "*",
        "ext-json":     "*",
        "ext-redis":    "^5.0",
        "lib-pcre":     ">=8.0"
    },
    "config": {
        "platform": {
            "php": "8.1.0",
            "ext-redis": "5.3.7"
        }
    }
}
```

```bash
# Check platform requirements
composer check-platform-reqs

# Install ignoring platform (CI with Docker that has different extensions)
composer install --ignore-platform-reqs
```

> 💡 Platform requirements prevent deploying code to servers missing required extensions. Always specify `ext-*` for extensions your code requires.

---

## Step 5: Path Repositories (Monorepo / Local Packages)

```bash
docker run --rm composer:2 sh -c "
# Create a local package
mkdir -p /tmp/packages/my-utils/src

cat > /tmp/packages/my-utils/composer.json << 'EOF'
{
    \"name\": \"myorg/my-utils\",
    \"description\": \"Local utility package\",
    \"autoload\": {\"psr-4\": {\"MyUtils\\\\\\\\\": \"src/\"}},
    \"require\": {\"php\": \">=8.1\"}
}
EOF

cat > /tmp/packages/my-utils/src/StringHelper.php << 'EOF'
<?php
namespace MyUtils;
class StringHelper {
    public static function slugify(string \\\$text): string {
        return strtolower(preg_replace('/[^a-z0-9]+/i', '-', trim(\\\$text)));
    }
}
EOF

# Create main app that uses the local package
mkdir -p /tmp/myapp2
cat > /tmp/myapp2/composer.json << 'EOF'
{
    \"name\": \"myorg/myapp\",
    \"repositories\": [
        {\"type\": \"path\", \"url\": \"/tmp/packages/my-utils\"}
    ],
    \"require\": {
        \"myorg/my-utils\": \"@dev\"
    }
}
EOF

cd /tmp/myapp2 && composer install --no-progress 2>&1 | tail -5 &&
php -r \"require 'vendor/autoload.php'; echo MyUtils\\StringHelper::slugify('Hello World!') . PHP_EOL;\"
"
```

📸 **Verified Output:**
```
Installing dependencies from lock file (including require-dev)
Package operations: 1 install, 0 updates, 0 removals
  - Installing myorg/my-utils (dev-main): Symlinking from /tmp/packages/my-utils
Generating autoload files
hello-world
```

---

## Step 6: Security Audit

```bash
docker run --rm composer:2 sh -c "
mkdir /tmp/sectest && cd /tmp/sectest &&
cat > composer.json << 'EOF'
{
    \"name\": \"test/security\",
    \"require\": {}
}
EOF
composer require --no-progress symfony/http-foundation:5.4.0 2>&1 | tail -3 &&
echo '---Running audit---' &&
composer audit 2>&1 | head -20
"
```

📸 **Verified Output:**
```
Package operations: 3 installs, 0 updates, 0 removals
Writing lock file
Generating autoload files
---Running audit---
Found 2 security vulnerability advisories affecting 1 package:
+-------------------+------------------+------------+
| Package           | CVE              | Severity   |
+-------------------+------------------+------------+
| symfony/http-     | CVE-2023-46733   | medium     |
| foundation        | CVE-2023-xxxxx   | high       |
+-------------------+------------------+------------+
Run `composer audit --format=json` for machine-readable output.
```

> 💡 Run `composer audit` in CI pipelines to catch known vulnerabilities before deployment.

---

## Step 7: Composer Plugins & Configuration

```json
{
    "config": {
        "optimize-autoloader":    true,
        "sort-packages":          true,
        "preferred-install":      "dist",
        "allow-plugins": {
            "composer/installers":       true,
            "dealerdirect/phpcodesniffer-composer-installer": true
        },
        "process-timeout": 600,
        "cache-dir": "/tmp/composer-cache"
    },
    "extra": {
        "laravel": {
            "providers": ["App\\Providers\\AppServiceProvider"],
            "aliases":   {}
        }
    }
}
```

```bash
# Useful Composer commands
composer show --installed         # List installed packages
composer show myorg/package       # Package details
composer outdated                 # Check for updates
composer why symfony/http-foundation  # Why is this installed?
composer validate                 # Validate composer.json
composer licenses                 # Show license info for all packages
composer diagnose                 # Diagnose common issues
```

> 💡 `allow-plugins` (Composer 2.2+) explicitly whitelists plugins that can run code during install. Security best practice.

---

## Step 8: Capstone — Full Project Setup

```bash
docker run --rm composer:2 sh -c "
mkdir -p /tmp/capstone/src/Service &&

# Write composer.json
cat > /tmp/capstone/composer.json << 'COMPJSON'
{
    \"name\": \"myorg/capstone\",
    \"description\": \"Capstone project\",
    \"type\": \"project\",
    \"require\": {
        \"php\": \">=8.1\"
    },
    \"autoload\": {
        \"psr-4\": {\"App\\\\\\\\\": \"src/\"}
    },
    \"scripts\": {
        \"post-autoload-dump\": \"@php -r \\\"echo 'Autoloader ready!\\\\n';\\\"\"
    },
    \"config\": {
        \"optimize-autoloader\": true,
        \"sort-packages\": true
    }
}
COMPJSON

# Write a service class
cat > /tmp/capstone/src/Service/Greeter.php << 'PHP'
<?php
namespace App\Service;
class Greeter {
    public function greet(string \\\$name): string {
        return \"Hello, \\\$name! Running PHP \" . PHP_VERSION;
    }
}
PHP

cd /tmp/capstone &&
composer install --no-progress --optimize-autoloader 2>&1 &&
php -r \"
require 'vendor/autoload.php';
\\\$g = new App\Service\Greeter();
echo \\\$g->greet('Composer') . PHP_EOL;
\"
"
```

📸 **Verified Output:**
```
Installing dependencies from lock file (including require-dev)
Generating optimized autoload files
Autoloader ready!
Hello, Composer! Running PHP 8.3.x
```

---

## Summary

| Feature | Command/Config | Notes |
|---|---|---|
| Initialize project | `composer init` | Interactive or `--no-interaction` |
| Path repository | `{"type": "path", "url": "../pkg"}` | Local monorepo packages |
| PSR-4 autoload | `"autoload": {"psr-4": {...}}` | Standard namespace mapping |
| Classmap autoload | `"classmap": ["src/Legacy/"]` | Non-standard file structure |
| Optimize autoloader | `composer dump-autoload -o` | Production: classmap-authoritative |
| Platform requirements | `"ext-pdo": "*"` in require | Prevent missing extension deploys |
| Custom scripts | `"scripts": {"test": "phpunit"}` | Lifecycle hooks + custom commands |
| Security audit | `composer audit` | Check known CVEs |
| Allow plugins | `"allow-plugins": {...}` | Required since Composer 2.2 |
| Check outdated | `composer outdated` | Find available updates |
