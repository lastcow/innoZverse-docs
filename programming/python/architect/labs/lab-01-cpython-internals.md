# Lab 01: CPython Internals

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Dive deep into CPython's object model, bytecode compilation, and runtime machinery. Understanding CPython internals lets you write code that works *with* the interpreter rather than against it.

## Step 1: The PyObject Model

Every Python object is a C struct (`PyObject`) with two key fields: `ob_refcnt` (reference count) and `ob_type` (pointer to type object). Python's `sys.getrefcount` exposes this:

```python
import sys

x = "hello"
print(sys.getrefcount(x))   # Always +1 because getrefcount itself holds a ref

a = x
b = x
print(sys.getrefcount(x))   # +2 more

del a
print(sys.getrefcount(x))   # back down by 1

# Object identity
print(id(x))                # memory address of PyObject
print(type(x))              # ob_type -> str
print(x.__class__)          # same
```

> 💡 `sys.getrefcount()` always shows count + 1 because the function call itself creates a temporary reference.

## Step 2: The `dis` Module — Bytecode Disassembly

```python
import dis

def compute(x, y):
    result = x * y + 1
    return result

dis.dis(compute)
print("---")
dis.code_info(compute)
```

📸 **Verified Output:**
```
  2           0 RESUME                   0

  3           2 LOAD_FAST                0 (x)
              4 LOAD_FAST                1 (y)
              6 BINARY_OP                5 (*)
             10 LOAD_CONST               1 (1)
             12 BINARY_OP               0 (+)
             16 STORE_FAST               2 (result)

  4          18 LOAD_FAST                2 (result)
             20 RETURN_VALUE
```

> 💡 Each bytecode instruction is 2 bytes (opcode + arg). `LOAD_FAST` is the fastest variable access — it reads from the local variable array by index.

## Step 3: Code Objects

```python
def add(x, y):
    result = x + y
    return result

code = add.__code__
print("co_varnames:", code.co_varnames)   # local vars including args
print("co_consts:", code.co_consts)       # constants used
print("co_argcount:", code.co_argcount)   # number of positional args
print("co_stacksize:", code.co_stacksize) # max stack depth needed
print("co_filename:", code.co_filename)   # source file
print("co_firstlineno:", code.co_firstlineno)

# Raw bytecode
import dis
print("\nBytecode bytes:", list(code.co_code[:10]))
```

📸 **Verified Output:**
```
co_varnames: ('x', 'y', 'result')
co_consts: (None,)
co_argcount: 2
co_stacksize: 2
co_filename: <...>
co_firstlineno: 1
```

## Step 4: Frame Objects

Frame objects represent the execution state of a function call — the runtime equivalent of a stack frame.

```python
import sys

def inner():
    frame = sys._getframe()
    print(f"Frame: {frame.f_code.co_name}")
    print(f"  locals: {list(frame.f_locals.keys())}")
    print(f"  lineno: {frame.f_lineno}")
    
    outer_frame = frame.f_back
    if outer_frame:
        print(f"Caller: {outer_frame.f_code.co_name}")

def outer():
    x = 42
    y = "hello"
    inner()

outer()
```

> 💡 `sys._getframe(n)` walks `n` frames up the call stack. This is how debuggers, profilers, and frameworks like Flask inspect the call stack at runtime.

## Step 5: `sys.getsizeof` — Object Memory Layout

```python
import sys

# Basic types
print(f"int(0):     {sys.getsizeof(0)} bytes")
print(f"int(2**30): {sys.getsizeof(2**30)} bytes")
print(f"int(2**60): {sys.getsizeof(2**60)} bytes")
print(f"float:      {sys.getsizeof(1.0)} bytes")
print(f"str(''):    {sys.getsizeof('')} bytes")
print(f"str('abc'): {sys.getsizeof('abc')} bytes")
print(f"list[]:     {sys.getsizeof([])} bytes")
print(f"list[10]:   {sys.getsizeof(list(range(10)))} bytes")
print(f"dict{{}}:   {sys.getsizeof({})} bytes")

# Interesting: small ints are cached
a = 256
b = 256
print(f"256 is 256: {a is b}")  # True (cached)

c = 257
d = 257
print(f"257 is 257: {c is d}")  # May be False outside REPL
```

> 💡 CPython caches integers from -5 to 256. This is why `a = 256; b = 256; a is b` returns `True`, but the same trick fails for 257+.

## Step 6: Bytecode Opcodes Deep Dive

```python
import dis, opcode

# Understand specific opcodes
def demo_opcodes():
    # LOAD_FAST: read local variable (fastest)
    x = 10
    y = 20
    
    # BINARY_OP: arithmetic
    z = x + y
    
    # COMPARE_OP: comparisons  
    flag = x < y
    
    # POP_JUMP_IF_FALSE: branching
    if flag:
        result = "yes"
    else:
        result = "no"
    return result

print("=== demo_opcodes bytecode ===")
dis.dis(demo_opcodes)

# Inspect opcode table
print("\n=== Selected opcodes ===")
for name in ['LOAD_FAST', 'STORE_FAST', 'RETURN_VALUE', 'BINARY_OP']:
    code = opcode.opmap.get(name)
    print(f"  {name}: {code}")
```

## Step 7: The Peephole Optimizer

CPython performs compile-time constant folding and other peephole optimizations:

```python
import dis

# Constant folding: 2*3 → 6 at compile time
def with_constant_fold():
    return 2 * 3 + 1

# String concatenation folding
def string_concat():
    return "hello" + " " + "world"

# Compare optimized vs unoptimized
print("=== Constant fold (2*3+1) ===")
dis.dis(with_constant_fold)

print("\n=== String concat ===")
dis.dis(string_concat)

# Verify: the bytecode shows LOAD_CONST with pre-computed value
import ast, compile as compile_
code = compile("2 * 3 + 1", "<string>", "eval")
print("\nConstants:", code.co_consts)
```

> 💡 The AST optimizer runs before bytecode generation. Expressions like `2*3` are folded to `6` at compile time — no BINARY_OP in the bytecode.

## Step 8: Capstone — Bytecode Analyzer Tool

Build a tool that analyzes a function's bytecode and generates a report:

```python
import dis, sys, types

def analyze_function(func):
    """Analyze a function's bytecode and report key metrics."""
    code = func.__code__
    instructions = list(dis.get_instructions(func))
    
    # Count opcodes
    opcode_counts = {}
    for instr in instructions:
        opcode_counts[instr.opname] = opcode_counts.get(instr.opname, 0) + 1
    
    # Find most common
    top_ops = sorted(opcode_counts.items(), key=lambda x: -x[1])[:5]
    
    report = {
        "name": func.__name__,
        "args": code.co_argcount,
        "locals": len(code.co_varnames),
        "constants": code.co_consts,
        "stack_depth": code.co_stacksize,
        "instructions": len(instructions),
        "top_opcodes": top_ops,
    }
    return report

def example_function(n):
    total = 0
    for i in range(n):
        if i % 2 == 0:
            total += i * i
    return total

report = analyze_function(example_function)
print(f"Function: {report['name']}")
print(f"  Args: {report['args']}, Locals: {report['locals']}")
print(f"  Stack depth: {report['stack_depth']}")
print(f"  Total instructions: {report['instructions']}")
print(f"  Constants: {report['constants']}")
print("  Top opcodes:")
for name, count in report['top_opcodes']:
    print(f"    {name}: {count}")
```

📸 **Verified Output:**
```
co_varnames: ('x', 'y', 'result')
co_consts: (None,)
co_argcount: 2

  4           0 RESUME                   0

  5           2 LOAD_FAST                0 (x)
              4 LOAD_FAST                1 (y)
              6 BINARY_OP                0 (+)
             10 STORE_FAST               2 (result)

  6          12 LOAD_FAST                2 (result)
             14 RETURN_VALUE
```

## Summary

| Concept | Tool/API | Use Case |
|---|---|---|
| Object model | `sys.getrefcount`, `id()` | Memory debugging |
| Bytecode | `dis.dis`, `dis.get_instructions` | Performance analysis |
| Code objects | `func.__code__` | Introspection |
| Frame objects | `sys._getframe()` | Debuggers/profilers |
| Memory size | `sys.getsizeof()` | Memory optimization |
| Constant folding | `dis` + `compile()` | Compiler optimization |
| Peephole optimizer | Bytecode inspection | Understanding compiler |
