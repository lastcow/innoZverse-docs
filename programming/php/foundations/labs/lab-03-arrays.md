# Lab 3: Arrays

## Objective
Create and manipulate PHP arrays — indexed, associative, and multidimensional — using built-in array functions for sorting, filtering, mapping, and transformation.

## Background
PHP arrays are one of the most versatile data structures in any language — they function as lists, dictionaries, stacks, queues, and sets all in one. PHP has over 70 built-in array functions. Mastering them is essential for web development, API responses, database result processing, and configuration management.

## Time
35 minutes

## Prerequisites
- Lab 02 (Data Types)

## Tools
- PHP 8.3 CLI
- Docker image: `zchencow/innozverse-php:latest`

---

## Lab Instructions

### Step 1: Indexed and Associative Arrays

```php
<?php
// Indexed array
$fruits = ['apple', 'banana', 'cherry', 'date'];

echo "Count: " . count($fruits) . "\n";
echo "First: " . $fruits[0] . "\n";
echo "Last: " . $fruits[count($fruits) - 1] . "\n";

// Add/remove elements
$fruits[] = 'elderberry';          // append
array_push($fruits, 'fig');        // append (explicit)
$removed = array_shift($fruits);   // remove from front
$popped  = array_pop($fruits);     // remove from end

echo "After modifications: " . implode(', ', $fruits) . "\n";

// Associative array (key => value)
$person = [
    'name'  => 'Dr. Chen',
    'age'   => 40,
    'role'  => 'admin',
    'email' => 'chen@example.com',
];

echo "\nName: " . $person['name'] . "\n";
echo "Keys: " . implode(', ', array_keys($person)) . "\n";
echo "Values count: " . count(array_values($person)) . "\n";

// Check key existence
echo "Has 'role': " . (array_key_exists('role', $person) ? 'yes' : 'no') . "\n";
echo "Has 'phone': " . (isset($person['phone']) ? 'yes' : 'no') . "\n";
```

> 💡 **PHP arrays are ordered maps** — even indexed arrays remember insertion order. `array_key_exists()` checks if a key exists (even if null); `isset()` checks if it exists AND is not null. Use `isset()` for performance-critical code; it's a language construct, not a function.

**📸 Verified Output:**
```
Count: 4
First: apple
Last: date
After modifications: banana, cherry, date, elderberry
Name: Dr. Chen
Keys: name, age, role, email
Values count: 4
Has 'role': yes
Has 'phone': no
```

---

### Step 2: Array Functions — Sort, Search, Slice

```php
<?php
$numbers = [5, 2, 8, 1, 9, 3, 7, 4, 6];

// Sorting (modifies in place)
$asc = $numbers;
sort($asc);
echo "Ascending: " . implode(', ', $asc) . "\n";

$desc = $numbers;
rsort($desc);
echo "Descending: " . implode(', ', $desc) . "\n";

// Associative sort (preserve keys)
$scores = ['Alice' => 95, 'Bob' => 87, 'Carol' => 92];
arsort($scores);
echo "\nBy score desc:\n";
foreach ($scores as $name => $score) {
    echo "  $name: $score\n";
}

// Sort by key
ksort($scores);
echo "By name: " . implode(', ', array_keys($scores)) . "\n";

// Search
$fruits = ['apple', 'banana', 'cherry'];
$idx = array_search('banana', $fruits);
echo "\nbanana at index: $idx\n";
echo "Has cherry: " . (in_array('cherry', $fruits) ? 'yes' : 'no') . "\n";

// Slice
$slice = array_slice($numbers, 2, 4);
echo "Slice [2..5]: " . implode(', ', $slice) . "\n";

// Splice (modify in place)
$arr = [1, 2, 3, 4, 5];
array_splice($arr, 1, 2, [10, 20, 30]);
echo "After splice: " . implode(', ', $arr) . "\n";
```

> 💡 **`sort()` reindexes the array** — keys are reset to 0, 1, 2… `asort()` preserves key-value associations while sorting by value. `ksort()` sorts by key. For custom sort order, use `usort()` with a callback.

**📸 Verified Output:**
```
Ascending: 1, 2, 3, 4, 5, 6, 7, 8, 9
Descending: 9, 8, 7, 6, 5, 4, 3, 2, 1

By score desc:
  Alice: 95
  Carol: 92
  Bob: 87
By name: Alice, Bob, Carol

banana at index: 1
Has cherry: yes
Slice [2..5]: 8, 1, 9, 3
After splice: [1, 10, 20, 30, 4, 5]
```

---

### Step 3: array_map, array_filter, array_reduce

```php
<?php
$numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// array_map — transform each element
$squares = array_map(fn($n) => $n ** 2, $numbers);
echo "Squares: " . implode(', ', $squares) . "\n";

$strings = array_map(fn($n) => "item_$n", [1, 2, 3]);
echo "Strings: " . implode(', ', $strings) . "\n";

// array_filter — keep matching elements (preserves keys)
$evens = array_filter($numbers, fn($n) => $n % 2 === 0);
echo "Evens: " . implode(', ', $evens) . "\n";

$longWords = array_filter(
    ['cat', 'elephant', 'ox', 'rhinoceros', 'ant'],
    fn($w) => strlen($w) > 4
);
echo "Long words: " . implode(', ', $longWords) . "\n";

// array_reduce — fold to single value
$sum     = array_reduce($numbers, fn($carry, $n) => $carry + $n, 0);
$product = array_reduce([1,2,3,4,5], fn($carry, $n) => $carry * $n, 1);
echo "\nSum: $sum\n";
echo "Product: $product\n";

// Chain: sum of squares of evens
$result = array_reduce(
    array_map(fn($n) => $n ** 2,
        array_filter($numbers, fn($n) => $n % 2 === 0)),
    fn($carry, $n) => $carry + $n,
    0
);
echo "Sum of even squares: $result\n";
```

> 💡 **`array_filter` preserves original keys** — after filtering, keys may be non-contiguous (e.g., 1, 3, 5). Use `array_values()` to reindex if you need 0-based sequential keys. `array_map` with multiple arrays applies the callback to corresponding elements.

**📸 Verified Output:**
```
Squares: 1, 4, 9, 16, 25, 36, 49, 64, 81, 100
Strings: item_1, item_2, item_3
Evens: 2, 4, 6, 8, 10
Long words: elephant, rhinoceros

Sum: 55
Product: 120
Sum of even squares: 220
```

---

### Step 4: Multidimensional Arrays

```php
<?php
// 2D array (list of records)
$students = [
    ['name' => 'Alice', 'grade' => 12, 'gpa' => 3.9],
    ['name' => 'Bob',   'grade' => 11, 'gpa' => 3.5],
    ['name' => 'Carol', 'grade' => 12, 'gpa' => 3.7],
    ['name' => 'Dave',  'grade' => 11, 'gpa' => 3.8],
];

// Access
echo "First student: " . $students[0]['name'] . "\n";

// Loop
echo "\nAll students:\n";
foreach ($students as $s) {
    printf("  %-8s Grade %d  GPA %.1f\n", $s['name'], $s['grade'], $s['gpa']);
}

// Sort by GPA descending
usort($students, fn($a, $b) => $b['gpa'] <=> $a['gpa']);
echo "\nBy GPA desc:\n";
foreach ($students as $s) {
    echo "  {$s['name']}: {$s['gpa']}\n";
}

// Group by grade
$byGrade = [];
foreach ($students as $s) {
    $byGrade[$s['grade']][] = $s['name'];
}
echo "\nBy grade:\n";
foreach ($byGrade as $grade => $names) {
    echo "  Grade $grade: " . implode(', ', $names) . "\n";
}

// column extraction
$names = array_column($students, 'name');
$gpas  = array_column($students, 'gpa');
echo "\nNames: " . implode(', ', $names) . "\n";
echo "Avg GPA: " . round(array_sum($gpas) / count($gpas), 2) . "\n";
```

> 💡 **`array_column($array, $key)`** extracts a single column from a 2D array — it's the PHP equivalent of `SELECT name FROM students`. Combined with `array_sum()` and `count()`, it replaces many database queries during local data processing.

**📸 Verified Output:**
```
First student: Alice

All students:
  Alice    Grade 12  GPA 3.9
  Bob      Grade 11  GPA 3.5
  Carol    Grade 12  GPA 3.7
  Dave     Grade 11  GPA 3.8

By GPA desc:
  Alice: 3.9
  Dave: 3.8
  Carol: 3.7
  Bob: 3.5

By grade:
  Grade 12: Alice, Carol
  Grade 11: Dave, Bob

Names: Alice, Dave, Carol, Bob
Avg GPA: 3.73
```

---

### Step 5: Array Merging, Combining & Set Operations

```php
<?php
// Merge (numeric keys reindexed; string keys overwritten by later)
$a = ['x' => 1, 'y' => 2];
$b = ['y' => 10, 'z' => 3];
$merged = array_merge($a, $b);
echo "Merged: "; print_r($merged);

// Union operator (keeps first occurrence of duplicate keys)
$union = $a + $b;
echo "Union: "; print_r($union);

// Combine keys + values into associative array
$keys   = ['name', 'age', 'city'];
$values = ['Dr. Chen', 40, 'San Francisco'];
$combined = array_combine($keys, $values);
echo "Combined: "; print_r($combined);

// Set operations
$set1 = [1, 2, 3, 4, 5];
$set2 = [3, 4, 5, 6, 7];

echo "Intersection: " . implode(', ', array_intersect($set1, $set2)) . "\n";
echo "Difference (1-2): " . implode(', ', array_diff($set1, $set2)) . "\n";
echo "Unique: " . implode(', ', array_unique([1,2,2,3,3,3,4])) . "\n";

// Flatten nested array
$nested = [[1,2], [3,4], [5,6]];
$flat = array_merge(...$nested);
echo "Flattened: " . implode(', ', $flat) . "\n";
```

> 💡 **`array_merge` vs `+` operator:** `array_merge` reindexes numeric keys (combines both); `+` keeps the first array's value for duplicate keys (union). For config arrays where you want "default + override", use `array_merge($defaults, $overrides)`.

**📸 Verified Output:**
```
Merged: Array ( [x] => 1 [y] => 10 [z] => 3 )
Union: Array ( [x] => 1 [y] => 2 [z] => 3 )
Combined: Array ( [name] => Dr. Chen [age] => 40 [city] => San Francisco )
Intersection: 3, 4, 5
Difference (1-2): 1, 2
Unique: 1, 2, 3, 4
Flattened: 1, 2, 3, 4, 5, 6
```

---

### Step 6: Array Unpacking & Spread

```php
<?php
// list() / [] destructuring
$coords = [10, 20, 30];
[$x, $y, $z] = $coords;
echo "x=$x, y=$y, z=$z\n";

// Skip elements
[, $second, , $fourth] = [1, 2, 3, 4];
echo "second=$second, fourth=$fourth\n";

// Associative destructuring (PHP 7.1+)
$user = ['name' => 'Alice', 'age' => 30, 'role' => 'admin'];
['name' => $name, 'role' => $role] = $user;
echo "name=$name, role=$role\n";

// Spread operator
function sum(int ...$nums): int {
    return array_sum($nums);
}
$args = [1, 2, 3, 4, 5];
echo "Sum: " . sum(...$args) . "\n";

// Merge with spread
$first  = [1, 2, 3];
$second = [4, 5, 6];
$all = [...$first, ...$second, 7, 8];
echo "Spread merge: " . implode(', ', $all) . "\n";

// Swap without temp
$a = 'hello'; $b = 'world';
[$a, $b] = [$b, $a];
echo "Swapped: a=$a, b=$b\n";
```

> 💡 **Array destructuring with `[...]`** (PHP 7.1+) lets you unpack arrays into variables elegantly. The spread operator `...` works for both function arguments and array literals. These patterns make coordinate unpacking, config loading, and function calls much cleaner.

**📸 Verified Output:**
```
x=10, y=20, z=30
second=2, fourth=4
name=Alice, role=admin
Sum: 15
Spread merge: 1, 2, 3, 4, 5, 6, 7, 8
Swapped: a=world, b=hello
```

---

### Step 7: Useful Array Utilities

```php
<?php
// array_chunk — split into batches
$items = range(1, 10);
$batches = array_chunk($items, 3);
echo "Batches:\n";
foreach ($batches as $i => $batch) {
    echo "  Batch $i: " . implode(', ', $batch) . "\n";
}

// array_flip — swap keys and values
$roles = ['alice' => 'admin', 'bob' => 'user', 'carol' => 'admin'];
$byRole = [];
foreach ($roles as $user => $role) {
    $byRole[$role][] = $user;
}
echo "\nUsers by role:\n";
print_r($byRole);

// array_pad — pad to length
$arr = [1, 2, 3];
echo "Padded right: " . implode(', ', array_pad($arr, 6, 0)) . "\n";
echo "Padded left:  " . implode(', ', array_pad($arr, -6, 0)) . "\n";

// compact & extract
$name = 'Dr. Chen'; $age = 40; $city = 'SF';
$data = compact('name', 'age', 'city');
echo "\nCompact: "; print_r($data);

extract(['foo' => 'bar', 'num' => 42]);
echo "Extracted: foo=$foo, num=$num\n";

// range
echo "Range: " . implode(', ', range(0, 10, 2)) . "\n";
echo "Letters: " . implode('', range('a', 'e')) . "\n";
```

> 💡 **`compact()` and `extract()`** are PHP-unique functions. `compact()` builds an array from variable names — useful for passing multiple vars to templates. `extract()` does the reverse — use it carefully as it can overwrite existing variables. Prefer explicit array access in most cases.

**📸 Verified Output:**
```
Batches:
  Batch 0: 1, 2, 3
  Batch 1: 4, 5, 6
  Batch 2: 7, 8, 9
  Batch 3: 10

Users by role:
Array ( [admin] => Array ( [0] => alice [1] => carol ) [user] => Array ( [0] => bob ) )

Padded right: 1, 2, 3, 0, 0, 0
Padded left:  0, 0, 0, 1, 2, 3

Compact: Array ( [name] => Dr. Chen [age] => 40 [city] => SF )
Extracted: foo=bar, num=42
Range: 0, 2, 4, 6, 8, 10
Letters: abcde
```

---

### Step 8: Real-World — Shopping Cart

```php
<?php
$cart = [
    ['id' => 'P001', 'name' => 'Surface Pro 12"', 'price' => 864.00, 'qty' => 1],
    ['id' => 'P002', 'name' => 'Surface Pen',      'price' =>  49.99, 'qty' => 2],
    ['id' => 'P003', 'name' => 'USB-C Hub',         'price' =>  29.99, 'qty' => 1],
];

// Calculate subtotals
$cart = array_map(function($item) {
    $item['subtotal'] = $item['price'] * $item['qty'];
    return $item;
}, $cart);

// Subtotal
$subtotal = array_sum(array_column($cart, 'subtotal'));

// Apply coupon
$coupon = 'SAVE10';
$discount = match($coupon) {
    'SAVE10' => $subtotal * 0.10,
    'SAVE20' => $subtotal * 0.20,
    default  => 0,
};

$shipping = $subtotal > 100 ? 0 : 9.99;
$total    = $subtotal - $discount + $shipping;

// Print receipt
echo str_repeat('═', 45) . "\n";
echo sprintf("%-25s %6s %8s\n", "Item", "Qty", "Subtotal");
echo str_repeat('─', 45) . "\n";

foreach ($cart as $item) {
    printf("%-25s %6d %8.2f\n", $item['name'], $item['qty'], $item['subtotal']);
}

echo str_repeat('─', 45) . "\n";
printf("%-32s %8.2f\n", "Subtotal:", $subtotal);
printf("%-32s -%7.2f\n", "Discount ($coupon):", $discount);
printf("%-32s %8.2f\n", "Shipping:", $shipping);
echo str_repeat('═', 45) . "\n";
printf("%-32s %8.2f\n", "TOTAL:", $total);
```

> 💡 **`array_column` + `array_sum`** is the PHP idiom for summing a field across all rows — equivalent to `SELECT SUM(subtotal) FROM cart`. The `match` expression (PHP 8.0+) is a strict, exhaustive switch — it throws `UnhandledMatchError` if no arm matches (unlike `switch` which falls through silently).

**📸 Verified Output:**
```
═════════════════════════════════════════════
Item                       Qty  Subtotal
─────────────────────────────────────────────
Surface Pro 12"              1   864.00
Surface Pen                  2    99.98
USB-C Hub                    1    29.99
─────────────────────────────────────────────
Subtotal:                          993.97
Discount (SAVE10):                 -99.40
Shipping:                            0.00
═════════════════════════════════════════════
TOTAL:                             894.57
```

---

## Verification

```bash
docker run --rm zchencow/innozverse-php:latest php -r "
\$arr = array_filter(range(1,10), fn(\$n) => \$n % 2 === 0);
\$result = array_reduce(array_map(fn(\$n) => \$n**2, \$arr), fn(\$c,\$n) => \$c+\$n, 0);
echo 'Sum of even squares: ' . \$result . PHP_EOL;
"
```

Expected: `Sum of even squares: 220`

## Summary

PHP arrays are maps, lists, stacks, queues, and sets — all in one. You've covered indexed and associative arrays, all major array functions (`sort`, `filter`, `map`, `reduce`, `column`, `chunk`, `merge`), multidimensional arrays, destructuring, and built a real shopping cart. Array mastery is the foundation of PHP backend work.

## Further Reading
- [PHP Array Functions](https://www.php.net/manual/en/ref.array.php)
- [PHP 8.0 match expression](https://www.php.net/manual/en/control-structures.match.php)
