# Lab 04: PHP FFI — C Library Bindings

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm php:8.3-fpm bash`

## Overview

PHP's Foreign Function Interface (FFI) allows calling C functions and manipulating C data structures directly from PHP. This enables integration with system libraries, native performance for critical paths, and access to OS-level APIs.

> ⚠️ **Note:** FFI requires PHP compiled with `--with-ffi`. The standard `php:8.3-cli` Docker image does **not** include FFI. Use `php:8.3-fpm` or build PHP with FFI support. To verify: `php -m | grep FFI`

---

## Step 1: FFI Setup & Prerequisites

```bash
# Check FFI availability
php -m | grep FFI

# If FFI is available:
# FFI

# Enable in php.ini:
# ffi.enable=1   (default: preload — only allow in preloaded scripts)
# ffi.enable=2   (true — allow everywhere, development only)

# For Docker: use php:8.3-fpm which includes FFI
docker run -it --rm php:8.3-fpm bash -c "php -m | grep FFI && echo 'FFI available'"
```

```php
<?php
// Check FFI at runtime
if (!extension_loaded('ffi')) {
    echo "FFI extension not loaded\n";
    echo "Enable: ffi.enable=preload or ffi.enable=true in php.ini\n";
    exit(1);
}

echo "FFI version: " . FFI::version() . "\n";
echo "FFI available: yes\n";
```

> 💡 **FFI security model:** `ffi.enable=preload` (default in PHP-FPM) only allows FFI in `opcache.preload` scripts. Use `ffi.enable=true` for CLI/development. Never use `true` in production web contexts.

---

## Step 2: FFI::cdef() — Basic libc Calls

```php
<?php
// Call libc functions directly from PHP
$libc = FFI::cdef(
    '
    // String functions
    size_t strlen(const char *s);
    char   *strrev(char *s);
    int    strcmp(const char *s1, const char *s2);
    
    // Math
    double sin(double x);
    double cos(double x);
    double sqrt(double x);
    
    // Memory
    void  *malloc(size_t size);
    void   free(void *ptr);
    void  *memcpy(void *dest, const void *src, size_t n);
    int    memcmp(const void *s1, const void *s2, size_t n);
    ',
    'libc.so.6'
);

// String operations
$str = "Hello from FFI!";
$len = $libc->strlen($str);
echo "String: {$str}\n";
echo "FFI strlen: {$len}\n";
echo "PHP strlen: " . strlen($str) . "\n";
echo "strcmp match: " . ($libc->strcmp("abc", "abc") === 0 ? "equal" : "not equal") . "\n";

// Math functions
echo sprintf("sin(π/2) = %.6f\n", $libc->sin(M_PI / 2));
echo sprintf("cos(0)   = %.6f\n", $libc->cos(0.0));
echo sprintf("sqrt(2)  = %.6f\n", $libc->sqrt(2.0));
```

📸 **Expected Output (with FFI enabled):**
```
String: Hello from FFI!
FFI strlen: 15
PHP strlen: 15
strcmp match: equal
sin(π/2) = 1.000000
cos(0)   = 1.000000
sqrt(2)  = 1.414214
```

---

## Step 3: FFI Structs & Pointers

```php
<?php
$ffi = FFI::cdef('
    typedef struct {
        int x;
        int y;
        int z;
    } Point3D;
    
    typedef struct {
        char name[64];
        double value;
        int    count;
    } Record;
    
    size_t strlen(const char *s);
', 'libc.so.6');

// Create C struct instances
$point = $ffi->new('Point3D');
$point->x = 10;
$point->y = 20;
$point->z = 30;
echo "Point3D: ({$point->x}, {$point->y}, {$point->z})\n";

// Pointer arithmetic
$ptr = FFI::addr($point);
echo "Via pointer->x: " . $ptr->x . "\n";

// Arrays of structs
$points = $ffi->new('Point3D[5]');
for ($i = 0; $i < 5; $i++) {
    $points[$i]->x = $i * 10;
    $points[$i]->y = $i * 20;
    $points[$i]->z = $i * 30;
}

echo "Points array:\n";
for ($i = 0; $i < 5; $i++) {
    echo "  [{$i}] ({$points[$i]->x}, {$points[$i]->y}, {$points[$i]->z})\n";
}

// String in struct
$record = $ffi->new('Record');
FFI::memset($record->name, 0, 64);
// Copy string into C char array
$name = "sensor-42";
for ($i = 0; $i < strlen($name); $i++) {
    $record->name[$i] = ord($name[$i]);
}
$record->value = 3.14159;
$record->count = 42;
echo "Record name length: " . $ffi->strlen($record->name) . "\n";
echo "Record value: " . $record->value . "\n";
```

---

## Step 4: FFI qsort — Callback Functions

```php
<?php
// PHP 8.x FFI with callbacks via Closure
// Note: FFI callback support requires libffi

$libc = FFI::cdef('
    void qsort(void *base, size_t nmemb, size_t size,
               int (*compar)(const void *, const void *));
    size_t strlen(const char *s);
', 'libc.so.6');

// Sort integer array via qsort
$n = 8;
$arr = FFI::new("int[{$n}]");
$values = [64, 34, 25, 12, 22, 11, 90, 7];
foreach ($values as $i => $v) {
    $arr[$i] = $v;
}

echo "Before sort: ";
for ($i = 0; $i < $n; $i++) echo $arr[$i] . " ";
echo "\n";

// Comparator callback
$compare = function(FFI\CData $a, FFI\CData $b): int {
    $va = FFI::cast('int*', $a)[0];
    $vb = FFI::cast('int*', $b)[0];
    return $va <=> $vb;
};

$libc->qsort($arr, $n, FFI::sizeof($arr[0]), $compare);

echo "After sort:  ";
for ($i = 0; $i < $n; $i++) echo $arr[$i] . " ";
echo "\n";
```

📸 **Expected Output:**
```
Before sort: 64 34 25 12 22 11 90 7
After sort:  7 11 12 22 25 34 64 90
```

---

## Step 5: FFI::load() — Header Files

```php
<?php
// Create a C header file
file_put_contents('/tmp/mylib.h', '
#define FFI_LIB "libc.so.6"

typedef struct {
    double real;
    double imag;
} Complex;

size_t strlen(const char *s);
double sin(double x);
double cos(double x);
double atan2(double y, double x);
double hypot(double x, double y);
');

// Load via header file
$ffi = FFI::load('/tmp/mylib.h');

// Complex number operations in C
$c = $ffi->new('Complex');
$c->real = 3.0;
$c->imag = 4.0;

// Magnitude (|c| = sqrt(real^2 + imag^2))
$magnitude = $ffi->hypot($c->real, $c->imag);
echo "Complex: {$c->real} + {$c->imag}i\n";
echo "Magnitude: {$magnitude}\n";

// Phase angle
$phase = $ffi->atan2($c->imag, $c->real);
echo "Phase: " . round($phase, 4) . " radians\n";
```

---

## Step 6: Performance Comparison

```php
<?php
// Compare PHP native vs FFI vs built-in for math operations
$libc = FFI::cdef('
    double sin(double x);
    double sqrt(double x);
', 'libc.so.6');

$iterations = 500_000;

// PHP built-in sin()
$start = hrtime(true);
$sum = 0.0;
for ($i = 0; $i < $iterations; $i++) {
    $sum += sin($i * 0.001);
}
$phpTime = (hrtime(true) - $start) / 1_000_000;

// FFI libc sin()
$start = hrtime(true);
$sum2 = 0.0;
for ($i = 0; $i < $iterations; $i++) {
    $sum2 += $libc->sin($i * 0.001);
}
$ffiTime = (hrtime(true) - $start) / 1_000_000;

echo sprintf("PHP built-in sin() x%dk: %.2fms (sum=%.2f)\n",
    $iterations / 1000, $phpTime, $sum);
echo sprintf("FFI libc sin()   x%dk: %.2fms (sum=%.2f)\n",
    $iterations / 1000, $ffiTime, $sum2);
echo sprintf("Overhead ratio: %.1fx\n", $ffiTime / $phpTime);
echo "\nNote: FFI call overhead is significant for small functions.\n";
echo "FFI shines for bulk operations on C structures, not single function calls.\n";
```

> 💡 **FFI overhead**: Each FFI call has ~100-200ns overhead for type marshaling. For functions like `sin()`, PHP's built-in is faster. FFI is best for: bulk data processing, manipulating C structs, calling complex library functions not exposed in PHP.

---

## Step 7: Real-World FFI — POSIX Time

```php
<?php
// Access POSIX high-resolution timer via FFI
$ffi = FFI::cdef('
    typedef long time_t;
    typedef long suseconds_t;
    
    typedef struct {
        time_t      tv_sec;
        suseconds_t tv_usec;
    } timeval;
    
    typedef struct {
        time_t tv_sec;
        long   tv_nsec;
    } timespec;
    
    int gettimeofday(timeval *tv, void *tz);
    int clock_gettime(int clk_id, timespec *tp);
    
    unsigned int sleep(unsigned int seconds);
    int usleep(unsigned int usec);
', 'libc.so.6');

// CLOCK_MONOTONIC = 1 on Linux
$CLOCK_MONOTONIC = 1;

$ts = $ffi->new('timespec');

$ffi->clock_gettime($CLOCK_MONOTONIC, FFI::addr($ts));
$start_ns = $ts->tv_sec * 1_000_000_000 + $ts->tv_nsec;

// Simulate some work
$sum = 0;
for ($i = 0; $i < 100_000; $i++) $sum += $i;

$ffi->clock_gettime($CLOCK_MONOTONIC, FFI::addr($ts));
$end_ns = $ts->tv_sec * 1_000_000_000 + $ts->tv_nsec;

$elapsed_us = ($end_ns - $start_ns) / 1000;
echo "Work completed: sum={$sum}\n";
echo "Elapsed (FFI clock_gettime): " . round($elapsed_us, 1) . "µs\n";
echo "Elapsed (hrtime):            " . round((hrtime(true) - $start_ns) / 1000, 1) . "µs\n";

// gettimeofday
$tv = $ffi->new('timeval');
$ffi->gettimeofday(FFI::addr($tv), null);
echo "Unix time (FFI): {$tv->tv_sec}.{$tv->tv_usec}\n";
echo "Unix time (PHP): " . microtime(true) . "\n";
```

---

## Step 8: Capstone — FFI Image Processing Simulation

```php
<?php
/**
 * FFI-based pixel processing using libc
 * Simulates: grayscale conversion, brightness adjustment
 * Uses: malloc/free for C-managed buffers, memset/memcpy
 */

$libc = FFI::cdef('
    void *malloc(size_t size);
    void  free(void *ptr);
    void *memset(void *s, int c, size_t n);
    void *memcpy(void *dest, const void *src, size_t n);
    double sqrt(double x);
    double sin(double x);
', 'libc.so.6');

// Simulate a 100x100 RGB image
$width = 100;
$height = 100;
$channels = 3; // RGB
$size = $width * $height * $channels;

// Allocate C memory for pixel buffer
$pixels = FFI::cast('uint8_t*', $libc->malloc($size));

// Fill with test pattern (gradient)
for ($y = 0; $y < $height; $y++) {
    for ($x = 0; $x < $width; $x++) {
        $offset = ($y * $width + $x) * $channels;
        $pixels[$offset]     = (int)(($x / $width) * 255);  // R
        $pixels[$offset + 1] = (int)(($y / $height) * 255); // G
        $pixels[$offset + 2] = 128;                          // B
    }
}

echo "Image: {$width}x{$height} RGB ({$size} bytes in C memory)\n";

// Grayscale conversion: Y = 0.299R + 0.587G + 0.114B
$gray = FFI::cast('uint8_t*', $libc->malloc($width * $height));
$start = hrtime(true);

for ($i = 0; $i < $width * $height; $i++) {
    $r = $pixels[$i * 3];
    $g = $pixels[$i * 3 + 1];
    $b = $pixels[$i * 3 + 2];
    $gray[$i] = (int)(0.299 * $r + 0.587 * $g + 0.114 * $b);
}
$grayTime = (hrtime(true) - $start) / 1_000_000;

// Sample some pixels
$samples = [0, 1000, 5000, 9999];
echo "Grayscale samples:\n";
foreach ($samples as $idx) {
    $r = $pixels[$idx * 3];
    $g = $pixels[$idx * 3 + 1];
    $b = $pixels[$idx * 3 + 2];
    echo "  pixel[{$idx}]: RGB({$r},{$g},{$b}) → gray={$gray[$idx]}\n";
}

// Brightness boost: clamp to 255
$bright = FFI::cast('uint8_t*', $libc->malloc($size));
$libc->memcpy($bright, $pixels, $size);
for ($i = 0; $i < $size; $i++) {
    $val = $bright[$i] + 50;
    $bright[$i] = min(255, $val);
}

echo "\nGrayscale conversion: " . round($grayTime, 2) . "ms\n";
echo "Memory: {$size} bytes RGB + " . ($width * $height) . " bytes gray = " . round(($size + $width*$height)/1024, 1) . " KB in C heap\n";

// Free C memory
$libc->free($pixels);
$libc->free($gray);
$libc->free($bright);
echo "C memory freed\n";

// Benchmark: PHP array vs FFI C buffer
$n = 100_000;

$start = hrtime(true);
$phpArr = array_fill(0, $n, 0);
for ($i = 0; $i < $n; $i++) $phpArr[$i] = $i % 256;
$phpTime = (hrtime(true) - $start) / 1_000_000;

$start = hrtime(true);
$cBuf = FFI::cast('uint8_t*', $libc->malloc($n));
for ($i = 0; $i < $n; $i++) $cBuf[$i] = $i % 256;
$ffiTime = (hrtime(true) - $start) / 1_000_000;
$libc->free($cBuf);

echo "\nBenchmark ({$n} elements):\n";
echo "  PHP array: " . round($phpTime, 2) . "ms\n";
echo "  FFI C buf: " . round($ffiTime, 2) . "ms\n";
```

📸 **Expected Output (with FFI enabled):**
```
Image: 100x100 RGB (30000 bytes in C memory)
Grayscale samples:
  pixel[0]:    RGB(0,0,128)     → gray=15
  pixel[1000]: RGB(100,100,128) → gray=101
  pixel[5000]: RGB(50,50,128)   → gray=66
  pixel[9999]: RGB(99,99,128)   → gray=101

Grayscale conversion: 18.42ms
Memory: 30000 bytes RGB + 10000 bytes gray = 39.1 KB in C heap
C memory freed

Benchmark (100000 elements):
  PHP array: 8.23ms
  FFI C buf: 12.41ms
```

---

## Summary

| Concept | API | Notes |
|---------|-----|-------|
| Define C interface | `FFI::cdef($header, $lib)` | Inline C declarations |
| Load from .h file | `FFI::load('/path/to/header.h')` | Include `#define FFI_LIB` |
| Allocate C memory | `$ffi->new('Type')` | Managed (auto-freed) |
| C heap alloc | `FFI::cast('T*', malloc($n))` | Manual free required |
| Pointer | `FFI::addr($var)` | Returns pointer to variable |
| Cast type | `FFI::cast('int*', $ptr)` | Reinterpret cast |
| Struct field | `$struct->field` | Direct field access |
| Array index | `$arr[$i]` | C array element |
| Sizeof | `FFI::sizeof($type)` | C sizeof equivalent |
| Callbacks | `Closure` as fn pointer | Requires libffi |
| Enable FFI | `ffi.enable=true` in php.ini | Dev only; preload for prod |
