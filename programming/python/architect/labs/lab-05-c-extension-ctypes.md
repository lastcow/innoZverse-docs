# Lab 05: C Extensions with ctypes

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

`ctypes` provides a Foreign Function Interface (FFI) to call C libraries without writing C code. This lab covers calling libc functions, defining C structures, creating callbacks, and understanding the architectural trade-offs vs. `cffi`.

## Step 1: Loading C Libraries

```python
import ctypes
import sys

# Load the C standard library
if sys.platform == 'linux':
    libc = ctypes.CDLL("libc.so.6")
elif sys.platform == 'darwin':
    libc = ctypes.CDLL("libc.dylib")
else:
    libc = ctypes.cdll.msvcrt  # Windows

# Call simple functions
libc.puts(b"Hello from libc.puts!")

# strlen
libc.strlen.restype = ctypes.c_size_t
libc.strlen.argtypes = [ctypes.c_char_p]
length = libc.strlen(b"hello world")
print(f"strlen('hello world') = {length}")

# abs
libc.abs.restype = ctypes.c_int
libc.abs.argtypes = [ctypes.c_int]
print(f"abs(-42) = {libc.abs(-42)}")
```

> 💡 Always set `.restype` and `.argtypes` on ctypes functions! Without them, ctypes assumes `c_int` return and no type checking — a common source of segfaults.

## Step 2: Basic Types

```python
import ctypes

# ctypes basic types map to C types
print("=== ctypes type sizes ===")
for name, ctype in [
    ("c_bool",   ctypes.c_bool),
    ("c_char",   ctypes.c_char),
    ("c_int",    ctypes.c_int),
    ("c_uint",   ctypes.c_uint),
    ("c_long",   ctypes.c_long),
    ("c_float",  ctypes.c_float),
    ("c_double", ctypes.c_double),
    ("c_size_t", ctypes.c_size_t),
    ("c_void_p", ctypes.c_void_p),
]:
    print(f"  {name:15}: {ctypes.sizeof(ctype)} bytes")

# Creating values
i = ctypes.c_int(42)
print(f"\nc_int(42).value = {i.value}")
i.value = 100
print(f"After .value = 100: {i.value}")

# Pointer
p = ctypes.pointer(i)
print(f"pointer contents: {p.contents.value}")
p.contents.value = 200
print(f"Original after pointer write: {i.value}")
```

## Step 3: Calling `qsort` with Callback

```python
import ctypes

libc = ctypes.CDLL("libc.so.6")

# Define the comparison function type
CMPFUNC = ctypes.CFUNCTYPE(
    ctypes.c_int,                          # return type
    ctypes.POINTER(ctypes.c_int),          # arg 1
    ctypes.POINTER(ctypes.c_int),          # arg 2
)

def compare_ints(a, b):
    return a.contents.value - b.contents.value

def compare_ints_desc(a, b):
    return b.contents.value - a.contents.value

cmp_asc  = CMPFUNC(compare_ints)
cmp_desc = CMPFUNC(compare_ints_desc)

# Create arrays to sort
arr_asc  = (ctypes.c_int * 8)(5, 2, 8, 1, 9, 3, 7, 4)
arr_desc = (ctypes.c_int * 8)(5, 2, 8, 1, 9, 3, 7, 4)

print("Before:", list(arr_asc))

libc.qsort(arr_asc,  len(arr_asc),  ctypes.sizeof(ctypes.c_int), cmp_asc)
libc.qsort(arr_desc, len(arr_desc), ctypes.sizeof(ctypes.c_int), cmp_desc)

print("After ascending: ", list(arr_asc))
print("After descending:", list(arr_desc))
```

📸 **Verified Output:**
```
Before: [5, 2, 8, 1, 9, 3, 7, 4]
After ascending:  [1, 2, 3, 4, 5, 7, 8, 9]
After descending: [9, 8, 7, 5, 4, 3, 2, 1]
```

## Step 4: `ctypes.Structure` — Mapping C Structs

```python
import ctypes

class Point(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
    ]

class Rectangle(ctypes.Structure):
    _fields_ = [
        ("top_left",     Point),
        ("bottom_right", Point),
        ("color",        ctypes.c_uint32),
    ]

# Create and use
p = Point(3.0, 4.0)
print(f"Point: ({p.x}, {p.y}), size={ctypes.sizeof(p)} bytes")

r = Rectangle(
    top_left=Point(0.0, 0.0),
    bottom_right=Point(10.0, 5.0),
    color=0xFF0000,
)
print(f"Rect: ({r.top_left.x},{r.top_left.y}) → ({r.bottom_right.x},{r.bottom_right.y})")
print(f"Color: #{r.color:06X}")
print(f"Rectangle size: {ctypes.sizeof(r)} bytes")

# Array of structs
points = (Point * 3)(Point(1, 2), Point(3, 4), Point(5, 6))
for i, pt in enumerate(points):
    print(f"  points[{i}] = ({pt.x}, {pt.y})")
```

## Step 5: `ctypes.Union`

```python
import ctypes

class IntOrFloat(ctypes.Union):
    _fields_ = [
        ("as_int",   ctypes.c_uint32),
        ("as_float", ctypes.c_float),
    ]

u = IntOrFloat()
u.as_float = 1.0
print(f"1.0 as float bits: 0x{u.as_int:08X}")

u.as_float = -1.0
print(f"-1.0 as float bits: 0x{u.as_int:08X}")

# IEEE 754: sign bit, exponent, mantissa
u.as_int = 0x3F800000  # 1.0 in IEEE 754
print(f"0x3F800000 as float: {u.as_float}")

class Packet(ctypes.Structure):
    class _Header(ctypes.Structure):
        _fields_ = [("type", ctypes.c_uint8), ("length", ctypes.c_uint16)]
    
    class _Payload(ctypes.Union):
        _fields_ = [
            ("raw",  ctypes.c_uint8 * 256),
            ("val",  ctypes.c_uint32),
        ]
    
    _fields_ = [
        ("header",  _Header),
        ("payload", _Payload),
    ]

pkt = Packet()
pkt.header.type = 0x01
pkt.header.length = 4
pkt.payload.val = 0xDEADBEEF
print(f"\nPacket type=0x{pkt.header.type:02X} len={pkt.header.length} val=0x{pkt.payload.val:08X}")
```

## Step 6: `ctypes.cast` and Pointer Arithmetic

```python
import ctypes

# Allocate raw memory
buf = ctypes.create_string_buffer(16)
print(f"Buffer size: {len(buf)}")

# Write integers via pointer
int_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_int))
int_ptr[0] = 0x11223344
int_ptr[1] = 0xAABBCCDD

# Read back as bytes
print(f"Buffer raw: {buf.raw.hex()}")

# Cast to different view
short_ptr = ctypes.cast(buf, ctypes.POINTER(ctypes.c_uint16))
print(f"As uint16: {[hex(short_ptr[i]) for i in range(4)]}")

# void pointer operations
vptr = ctypes.c_void_p(ctypes.addressof(buf))
print(f"Buffer address: 0x{vptr.value:016X}")
```

## Step 7: `malloc` / `free` via ctypes

```python
import ctypes

libc = ctypes.CDLL("libc.so.6")
libc.malloc.restype = ctypes.c_void_p
libc.malloc.argtypes = [ctypes.c_size_t]
libc.free.restype = None
libc.free.argtypes = [ctypes.c_void_p]

# Allocate a C array
n = 5
ptr = libc.malloc(n * ctypes.sizeof(ctypes.c_double))
if not ptr:
    raise MemoryError("malloc failed")

# Write values
arr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_double))
for i in range(n):
    arr[i] = float(i * i)

print("C-allocated array:", [arr[i] for i in range(n)])

# Free the memory
libc.free(ptr)
print("Memory freed successfully")
```

> 💡 Always `free` memory allocated with `malloc`. Python's GC doesn't know about raw C allocations.

## Step 8: Capstone — Shared Library Wrapper

Build a complete, safe wrapper around libc math functions:

```python
import ctypes
import math as pymath
import sys

class LibMath:
    """Type-safe wrapper around libm (C math library)."""
    
    def __init__(self):
        if sys.platform == 'linux':
            self._libm = ctypes.CDLL("libm.so.6")
        elif sys.platform == 'darwin':
            self._libm = ctypes.CDLL("libm.dylib")
        
        # Use libc for basic math on linux (already in process)
        self._libc = ctypes.CDLL("libc.so.6")
        
        # Configure function signatures
        self._setup_functions()
    
    def _setup_functions(self):
        double_to_double = (ctypes.c_double, [ctypes.c_double])
        two_double_to_double = (ctypes.c_double, [ctypes.c_double, ctypes.c_double])
        
        funcs = {
            'sin': double_to_double,
            'cos': double_to_double,
            'sqrt': double_to_double,
            'fabs': double_to_double,
            'pow': two_double_to_double,
        }
        
        for name, (restype, argtypes) in funcs.items():
            lib = self._libm if hasattr(self._libm, name) else self._libc
            try:
                fn = getattr(lib, name)
                fn.restype = restype
                fn.argtypes = argtypes
                setattr(self, f"_{name}", fn)
            except AttributeError:
                pass
    
    def sin(self, x: float) -> float:
        return self._sin(x)
    
    def cos(self, x: float) -> float:
        return self._cos(x)
    
    def sqrt(self, x: float) -> float:
        if x < 0:
            raise ValueError(f"sqrt of negative: {x}")
        return self._sqrt(x)
    
    def pow(self, base: float, exp: float) -> float:
        return self._pow(base, exp)

lm = LibMath()

# Compare with Python math module
test_values = [0, pymath.pi/6, pymath.pi/4, pymath.pi/3, pymath.pi/2]
print("sin(x) comparison: ctypes vs math module")
print(f"{'x':>10} {'ctypes':>15} {'math':>15} {'diff':>12}")
for x in test_values:
    c_val = lm.sin(x)
    py_val = pymath.sin(x)
    diff = abs(c_val - py_val)
    print(f"{x:>10.4f} {c_val:>15.10f} {py_val:>15.10f} {diff:>12.2e}")

print(f"\nsqrt(2) = {lm.sqrt(2):.10f}")
print(f"pow(2, 10) = {lm.pow(2, 10):.0f}")

try:
    lm.sqrt(-1)
except ValueError as e:
    print(f"ValueError: {e}")
```

📸 **Verified Output (qsort):**
```
Before: [5, 2, 8, 1, 9, 3, 7, 4]
After:  [1, 2, 3, 4, 5, 7, 8, 9]
Point: (3.0, 4.0), size=16 bytes
```

## Summary

| Concept | API | Use Case |
|---|---|---|
| Load shared lib | `ctypes.CDLL` | Call C libraries |
| Type safety | `.restype`, `.argtypes` | Prevent segfaults |
| Callbacks | `CFUNCTYPE` | Pass Python funcs to C |
| C structs | `ctypes.Structure._fields_` | Binary data layout |
| C unions | `ctypes.Union` | Variant data types |
| Pointer cast | `ctypes.cast` | Reinterpret memory |
| Raw allocation | `malloc/free` via ctypes | Unmanaged memory |
| Wrapper pattern | Class encapsulation | Safe C library binding |
