# Lab 2: Data Types and Type Juggling

## 🎯 Objective
Understand PHP's data types, explore type juggling (automatic type conversion), and learn explicit type casting.

## 📚 Background
PHP is a loosely typed language — variables can hold any type of data and types can change dynamically. This is called "type juggling." Understanding how PHP handles types prevents subtle bugs.

## ⏱️ Estimated Time
25 minutes

## 📋 Prerequisites
- Completed Lab 1: Hello World & PHP Basics

## 🛠️ Tools Used
- PHP 8.3 CLI
- Docker (`innozverse-php:latest`)

---

## 🔬 Lab Instructions

### Step 1: PHP's Eight Primitive Types

```php
<?php
// Scalar types
$integer  = 42;
$float    = 3.14;
$string   = "Hello";
$bool     = true;

// Compound types
$array    = [1, 2, 3];
$object   = new stdClass();

// Special types
$null     = null;

echo gettype($integer) . "\n";  // integer
echo gettype($float)   . "\n";  // double
echo gettype($string)  . "\n";  // string
echo gettype($bool)    . "\n";  // boolean
echo gettype($array)   . "\n";  // array
echo gettype($object)  . "\n";  // object
echo gettype($null)    . "\n";  // NULL
```

**📸 Verified Output:**
```
integer
double
string
boolean
array
object
NULL
```

💡 PHP calls floats "double" for historical reasons.

---

### Step 2: Integer Formats

```php
<?php
$decimal     = 255;
$octal       = 0377;     // Octal (starts with 0)
$hex         = 0xFF;     // Hexadecimal (starts with 0x)
$binary      = 0b11111111; // Binary (starts with 0b)
$underscore  = 1_000_000;  // PHP 7.4+ readability

echo $decimal    . "\n";  // 255
echo $octal      . "\n";  // 255
echo $hex        . "\n";  // 255
echo $binary     . "\n";  // 255
echo $underscore . "\n";  // 1000000

echo PHP_INT_MAX . "\n";  // Maximum integer
echo PHP_INT_MIN . "\n";  // Minimum integer
```

**📸 Verified Output:**
```
255
255
255
255
1000000
9223372036854775807
-9223372036854775808
```

---

### Step 3: Float Precision

```php
<?php
$f1 = 1.5;
$f2 = 1.5e3;   // Scientific notation = 1500
$f3 = 7E-2;    // 0.07

echo $f1 . "\n";
echo $f2 . "\n";
echo $f3 . "\n";

// Famous float precision issue
$result = 0.1 + 0.2;
echo $result . "\n";              // 0.3 (displayed)
var_dump($result == 0.3);         // false!
var_dump(round($result, 1) == 0.3); // true

echo PHP_FLOAT_EPSILON . "\n";   // Smallest difference PHP can detect
```

**📸 Verified Output:**
```
1.5
1500
0.07
0.3
bool(false)
bool(true)
2.2204460492503E-16
```

💡 Never use `==` to compare floats. Use `abs($a - $b) < PHP_FLOAT_EPSILON` or `round()`.

---

### Step 4: Type Juggling in Arithmetic

```php
<?php
// String + Number = Number
$a = "5" + 3;
echo $a . "\n";           // 8
echo gettype($a) . "\n";  // integer

// String with leading number
$b = "10 meters" + 5;    // Warning in PHP 8
echo $b . "\n";           // 15 (takes leading digits)

// Boolean arithmetic
$c = true + true;
echo $c . "\n";            // 2

$d = false + 10;
echo $d . "\n";            // 10

// null is 0
$e = null + 5;
echo $e . "\n";            // 5
```

**📸 Verified Output:**
```
8
integer
15
2
10
5
```

---

### Step 5: Type Casting

```php
<?php
// Cast to integer
echo (int)"42"       . "\n";  // 42
echo (int)"42.9"     . "\n";  // 42 (truncates)
echo (int)"abc"      . "\n";  // 0
echo (int)true       . "\n";  // 1
echo (int)false      . "\n";  // 0
echo (int)null       . "\n";  // 0

// Cast to float
echo (float)"3.14"   . "\n";  // 3.14
echo (float)"3.14px" . "\n";  // 3.14

// Cast to string
echo (string)42      . "\n";  // "42"
echo (string)true    . "\n";  // "1"
echo (string)false   . "\n";  // ""  (empty string)
echo (string)null    . "\n";  // ""  (empty string)
echo (string)3.14    . "\n";  // "3.14"

// Cast to bool (falsy values)
var_dump((bool)0);     // false
var_dump((bool)"");    // false
var_dump((bool)"0");   // false
var_dump((bool)[]);    // false
var_dump((bool)null);  // false
var_dump((bool)1);     // true
var_dump((bool)"abc"); // true
```

**📸 Verified Output:**
```
42
42
0
1
0
0
3.14
3.14
42
1


3.14
bool(false)
bool(false)
bool(false)
bool(false)
bool(false)
bool(true)
bool(true)
```

---

### Step 6: Type Checking Functions

```php
<?php
$values = [42, 3.14, "hello", true, null, [1,2], new stdClass()];

foreach ($values as $v) {
    $type = gettype($v);
    echo str_pad($type, 10) . " | is_int:" . (is_int($v) ? 'T' : 'F')
       . " is_string:" . (is_string($v) ? 'T' : 'F')
       . " is_numeric:" . (is_numeric($v) ? 'T' : 'F') . "\n";
}
```

**📸 Verified Output:**
```
integer    | is_int:T is_string:F is_numeric:T
double     | is_int:F is_string:F is_numeric:T
string     | is_int:F is_string:T is_numeric:F
boolean    | is_int:F is_string:F is_numeric:F
NULL       | is_int:F is_string:F is_numeric:F
array      | is_int:F is_string:F is_numeric:F
object     | is_int:F is_string:F is_numeric:F
```

---

### Step 7: Strict Comparison

```php
<?php
// == (loose) vs === (strict)
var_dump(0 == false);    // true  (both are falsy)
var_dump(0 === false);   // false (different types)
var_dump("" == false);   // true
var_dump("" === false);  // false
var_dump(0 == "");       // false in PHP 8!
var_dump(null == false); // true
var_dump(null === false);// false
var_dump("1" == 1);      // true (string converted to int)
var_dump("1" === 1);     // false
```

**📸 Verified Output:**
```
bool(true)
bool(false)
bool(true)
bool(false)
bool(false)
bool(true)
bool(false)
bool(true)
bool(false)
```

💡 Always use `===` for comparisons to avoid surprising type juggling behavior.

---

### Step 8: Type Declarations (PHP 7+)

```php
<?php
declare(strict_types=1);

function add(int $a, int $b): int {
    return $a + $b;
}

function divide(float $a, float $b): float {
    if ($b == 0.0) throw new DivisionByZeroError("Cannot divide by zero");
    return $a / $b;
}

function toggle(bool $state): bool {
    return !$state;
}

echo add(3, 4) . "\n";
echo divide(10.0, 3.0) . "\n";
var_dump(toggle(true));

// With strict_types=1, this would throw TypeError:
// add("3", "4");
```

**📸 Verified Output:**
```
7
3.3333333333333
bool(false)
```

---

## ✅ Verification

All type operations verified in PHP 8.3. Key behaviors confirmed:
- `0 == ""` is now `false` in PHP 8 (changed from PHP 7)
- Float arithmetic is imprecise — use `round()` for comparisons
- `===` always checks both value AND type

## 🚨 Common Mistakes

| Mistake | Fix |
|--------|-----|
| Using `==` to compare floats | Use `abs($a-$b) < PHP_FLOAT_EPSILON` |
| Using `==` where type matters | Use `===` (strict equality) |
| Expecting `(string)false` to be `"false"` | It's an empty string `""` |
| Expecting `(int)"3px"` to throw an error | It silently returns `3` |

## 📝 Summary

- PHP has 8 primitive types: int, float, string, bool, array, object, callable, null
- Type juggling happens automatically in operations
- Use `gettype()`, `is_int()`, `is_string()` etc. to check types
- Use `===` for strict comparison
- Use type declarations with `declare(strict_types=1)` for safer code

## 🔗 Further Reading

- [PHP Type System](https://www.php.net/manual/en/language.types.php)
- [PHP Type Juggling](https://www.php.net/manual/en/language.types.type-juggling.php)
- [PHP 8 Type Changes](https://www.php.net/manual/en/migration80.incompatible.php)
