# Lab 1: Hello World & PHP Basics

## 🎯 Objective
Learn to write your first PHP program, understand PHP syntax, use `echo` for output, and work with variables.

## 📚 Background
PHP (Hypertext Preprocessor) is a widely-used server-side scripting language. PHP code is embedded within `<?php` and `?>` tags. Variables start with `$` and are dynamically typed, meaning you don't need to declare their type upfront.

## ⏱️ Estimated Time
20 minutes

## 📋 Prerequisites
- Basic understanding of programming concepts
- Docker installed and `innozverse-php:latest` image available

## 🛠️ Tools Used
- PHP 8.3 CLI
- Docker (`innozverse-php:latest`)

---

## 🔬 Lab Instructions

### Step 1: Your First PHP Script

Create a file `/tmp/lab01.php`:

```php
<?php
echo "Hello, World!\n";
```

Run it:
```bash
docker run --rm -v /tmp:/tmp innozverse-php:latest php /tmp/lab01.php
```

**📸 Verified Output:**
```
Hello, World!
```

💡 `echo` outputs text to the screen. The `\n` is a newline character.

---

### Step 2: Variables

```php
<?php
$name = "PHP";
$version = 8.3;
$year = 2025;

echo "Language: $name\n";
echo "Version: $version\n";
echo "Year: $year\n";
```

**📸 Verified Output:**
```
Language: PHP
Version: 8.3
Year: 2025
```

💡 Variables are prefixed with `$`. PHP is loosely typed — no type declaration needed.

---

### Step 3: Variable Types and `var_dump`

```php
<?php
$str    = "Hello";
$int    = 42;
$float  = 3.14;
$bool   = true;
$null   = null;

var_dump($str);
var_dump($int);
var_dump($float);
var_dump($bool);
var_dump($null);
```

**📸 Verified Output:**
```
string(5) "Hello"
int(42)
float(3.14)
bool(true)
NULL
```

💡 `var_dump()` shows both the type and value — great for debugging.

---

### Step 4: String Concatenation

```php
<?php
$first = "Hello";
$last  = "World";

// Method 1: concatenation with .
$full = $first . ", " . $last . "!";
echo $full . "\n";

// Method 2: string interpolation
echo "$first, $last!\n";

// Method 3: complex expressions in strings
$count = 5;
echo "There are {$count} items\n";
```

**📸 Verified Output:**
```
Hello, World!
Hello, World!
There are 5 items
```

---

### Step 5: Constants

```php
<?php
define("APP_NAME", "InnoZverse");
define("MAX_USERS", 1000);

const VERSION = "1.0.0";

echo APP_NAME . "\n";
echo MAX_USERS . "\n";
echo VERSION . "\n";
```

**📸 Verified Output:**
```
InnoZverse
1000
1.0.0
```

💡 Constants don't use `$` and cannot be changed after definition.

---

### Step 6: PHP Comments

```php
<?php
// Single-line comment

# Also a single-line comment

/*
 * Multi-line comment
 * Useful for documentation
 */

$x = 10; // Inline comment

echo $x . "\n";

/**
 * PHPDoc comment — used for documentation
 * @param string $name
 * @return string
 */
function greet(string $name): string {
    return "Hello, $name!";
}

echo greet("Developer") . "\n";
```

**📸 Verified Output:**
```
10
Hello, Developer!
```

---

### Step 7: Print and Printf

```php
<?php
print("Using print\n");  // print is similar to echo but returns 1

$price  = 9.99;
$qty    = 3;
$total  = $price * $qty;

printf("Price: $%.2f x %d = $%.2f\n", $price, $qty, $total);

// sprintf returns a string
$msg = sprintf("Total cost: $%05.2f", $total);
echo $msg . "\n";
```

**📸 Verified Output:**
```
Using print
Price: $9.99 x 3 = $29.97
Total cost: $29.97
```

---

### Step 8: A Complete Mini Program

```php
<?php
$name    = "Alice";
$age     = 30;
$city    = "New York";
$salary  = 75000.50;

echo "=== User Profile ===\n";
echo "Name:   $name\n";
echo "Age:    $age years\n";
echo "City:   $city\n";
printf("Salary: $%,.2f\n", $salary);
echo "Adult:  " . ($age >= 18 ? "Yes" : "No") . "\n";
echo "Born:   " . (date("Y") - $age) . "\n";
```

**📸 Verified Output:**
```
=== User Profile ===
Name:   Alice
Age:    30 years
City:   New York
Salary: $75,000.50
Adult:  Yes
Born:   1996
```

---

## ✅ Verification

Run all snippets through Docker successfully. Confirm:
- `echo` outputs text
- Variables hold different types
- String interpolation works with `"$var"` and `"{$var}"`
- Constants are defined with `define()` or `const`

## 🚨 Common Mistakes

| Mistake | Fix |
|--------|-----|
| Forgetting `$` on variables | Always prefix variables with `$` |
| Using single quotes for interpolation | Use double quotes: `"Hello $name"` |
| Missing semicolons | Every statement must end with `;` |
| `<?` without `php` | Use full `<?php` opening tag |

## 📝 Summary

- PHP scripts begin with `<?php`
- Variables start with `$` and are dynamically typed
- Use `echo` or `print` for output
- String interpolation works in double-quoted strings
- `var_dump()` shows type and value
- Constants use `define()` or `const`

## 🔗 Further Reading

- [PHP Manual: Basic Syntax](https://www.php.net/manual/en/language.basic-syntax.php)
- [PHP Variables](https://www.php.net/manual/en/language.variables.basics.php)
- [PHP echo](https://www.php.net/manual/en/function.echo.php)
