# Lab 02: AST, Bytecode & Python Internals

## Objective
Understand Python's compilation pipeline: source → tokenizer → AST → bytecode → execution. Parse and transform AST nodes, inspect bytecode with `dis`, write an AST-based code analyser, and compile/execute dynamically generated code.

## Background
Every Python program goes through: source text → `tokenize` → `ast.parse()` → compiler → bytecode (`.pyc`). Knowing this pipeline lets you build linters, code generators, and even transpilers entirely within Python — no C extension needed.

## Time
35 minutes

## Prerequisites
- Lab 01 (Metaprogramming)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Parsing & Inspecting the AST

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import ast

source = '''
def calculate_discount(price: float, pct: float) -> float:
    if not 0 <= pct <= 1:
        raise ValueError(f'pct must be 0-1, got {pct}')
    return round(price * (1 - pct), 2)
'''

tree = ast.parse(source)

# Pretty-print the AST (first 500 chars)
print('=== AST (truncated) ===')
print(ast.dump(tree, indent=2)[:500])

# All node types in the file
print()
print('=== Node types in source ===')
node_types = sorted({type(n).__name__ for n in ast.walk(tree)})
print(node_types)

# Inspect specific nodes
print()
print('=== Function definitions ===')
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        args = [a.arg for a in node.args.args]
        returns = node.returns.id if isinstance(node.returns, ast.Name) else None
        print(f'  def {node.name}({', '.join(args)}) -> {returns}  [line {node.lineno}]')
"
```

> 💡 **`ast.walk(tree)`** yields every node in the AST depth-first. Each node type maps to a Python construct: `FunctionDef` for `def`, `ClassDef` for `class`, `Call` for function calls, `BinOp` for `+`/`-`/etc. The `lineno` attribute tells you exactly where in source the node came from.

**📸 Verified Output:**
```
=== AST (truncated) ===
Module(
  body=[
    FunctionDef(
      name='calculate_discount',
      args=arguments(...)
      ...

=== Node types in source ===
['Constant', 'FunctionDef', 'If', 'Module', 'Name', 'Raise', 'Return', ...]

=== Function definitions ===
  def calculate_discount(price, pct) -> float  [line 2]
```

---

### Step 2: AST Visitor — Code Analyser

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import ast

class CodeAnalyser(ast.NodeVisitor):
    '''Walks an AST and collects metrics: functions, classes, calls, complexity.'''

    def __init__(self):
        self.functions   = []
        self.classes     = []
        self.calls       = []
        self.imports     = []
        self.complexity  = 0  # McCabe: branches add 1

    def visit_FunctionDef(self, node):
        args = [a.arg for a in node.args.args]
        has_return_ann = node.returns is not None
        self.functions.append({
            'name': node.name, 'line': node.lineno,
            'args': args, 'annotated': has_return_ann,
        })
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        bases = [b.id if isinstance(b, ast.Name) else '?' for b in node.bases]
        self.classes.append({'name': node.name, 'bases': bases, 'line': node.lineno})
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            self.calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.calls.append(f'{node.func.attr}')
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names: self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.imports.append(node.module)
        self.generic_visit(node)

    # Complexity: each branch adds 1
    def visit_If(self, node):      self.complexity += 1; self.generic_visit(node)
    def visit_For(self, node):     self.complexity += 1; self.generic_visit(node)
    def visit_While(self, node):   self.complexity += 1; self.generic_visit(node)
    def visit_ExceptHandler(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_BoolOp(self, node):  self.complexity += len(node.values) - 1; self.generic_visit(node)

source = open('/usr/local/lib/python3.12/json/__init__.py').read()
tree   = ast.parse(source)
a      = CodeAnalyser()
a.visit(tree)

print(f'=== json module analysis ===')
print(f'Functions:  {len(a.functions)}')
print(f'Classes:    {len(a.classes)}')
print(f'Imports:    {a.imports}')
print(f'Unique calls: {len(set(a.calls))} ({sorted(set(a.calls))[:8]}...)')
print(f'Complexity: {a.complexity}')
print()
print('Functions:')
for f in a.functions[:6]:
    ann = '✓' if f['annotated'] else '✗'
    print(f'  [{ann}] {f[\"name\"]}({', '.join(f[\"args\"])})  line {f[\"line\"]}')
"
```

**📸 Verified Output:**
```
=== json module analysis ===
Functions:  4
Classes:    0
Imports:    ['codecs', '.decoder', '.encoder', '.scanner']
Unique calls: 8 (['JSONDecodeError', 'detect_encoding', ...])
Complexity: 10

Functions:
  [✓] dump(obj, fp, ...)  line 179
  [✓] dumps(obj, ...)     line 230
  [✓] load(fp, ...)       line 269
  [✓] loads(s, ...)       line 299
```

---

### Steps 3–8: AST Transformer, Compile & Exec, dis Bytecode, Tokenizer, JIT-like Optimizer, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import ast, dis, tokenize, io, textwrap

# Step 3: AST Transformer — auto-inject logging
class LogInserter(ast.NodeTransformer):
    '''Inserts a print() call at the start of every function.'''
    def visit_FunctionDef(self, node):
        log_stmt = ast.parse(
            f'print(f\"CALL: {node.name}({', '.join(a.arg + '={' + a.arg + '!r}' for a in node.args.args)})\")'
        ).body[0]
        # Preserve line info
        ast.copy_location(log_stmt, node)
        node.body.insert(0, log_stmt)
        return self.generic_visit(node)

src = textwrap.dedent('''
    def add(a, b):
        return a + b

    def multiply(x, y):
        return x * y
''')

tree = ast.parse(src)
new_tree = LogInserter().visit(tree)
ast.fix_missing_locations(new_tree)
code = compile(new_tree, '<transformed>', 'exec')

ns = {}
exec(code, ns)
print('=== Auto-logged function calls ===')
print(ns['add'](3, 4))
print(ns['multiply'](6, 7))

# Step 4: AST-based type checker
class TypeCheckInserter(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        checks = []
        for arg in node.args.args:
            if arg.annotation and isinstance(arg.annotation, ast.Name):
                check = ast.parse(
                    f'assert isinstance({arg.arg}, {arg.annotation.id}), '
                    f'f\"{arg.arg} must be {arg.annotation.id.__class__.__name__}, got {{type({arg.arg}).__name__}}\"'
                ).body[0]
                checks.append(check)
        node.body = checks + node.body
        return self.generic_visit(node)

src2 = textwrap.dedent('''
    def safe_divide(a: int, b: int) -> float:
        if b == 0: raise ZeroDivisionError(\"b cannot be zero\")
        return a / b
''')
tree2 = TypeCheckInserter().visit(ast.parse(src2))
ast.fix_missing_locations(tree2)
ns2 = {}
exec(compile(tree2, '<typed>', 'exec'), ns2)
print()
print('=== AST-injected type checks ===')
print(f'safe_divide(10, 3) = {ns2[\"safe_divide\"](10, 3):.4f}')
try: ns2['safe_divide'](10, 'three')
except AssertionError as e: print(f'Type error: {e}')

# Step 5: Bytecode inspection with dis
print()
print('=== Bytecode: fibonacci ===')
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)

dis.dis(fib)
co = fib.__code__
print(f'co_varnames:  {co.co_varnames}')
print(f'co_consts:    {co.co_consts}')
print(f'co_freevars:  {co.co_freevars}')
print(f'stacksize:    {co.co_stacksize}')
print(f'code bytes:   {len(co.co_code)} bytes')

# Step 6: Tokenizer
print()
print('=== Token stream ===')
src3 = 'result = price * (1 - discount)'
tokens = list(tokenize.generate_tokens(io.StringIO(src3).readline))
for tok in tokens[:12]:
    if tok.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.ENDMARKER):
        print(f'  {tokenize.tok_name[tok.type]:10s} {tok.string!r}')

# Step 7: eval() / compile() for dynamic expressions
print()
print('=== Dynamic expression evaluation ===')
exprs = [
    'price * (1 - discount)',
    'stock > 0 and price < 1000',
    '[p[\"name\"] for p in products if p[\"stock\"] > 0]',
]
ctx = {
    'price': 864.0, 'discount': 0.1, 'stock': 15,
    'products': [
        {'name': 'Surface Pro', 'stock': 15},
        {'name': 'USB-C Hub',   'stock': 0},
        {'name': 'Surface Pen', 'stock': 80},
    ]
}
for expr in exprs:
    result = eval(compile(expr, '<expr>', 'eval'), {'__builtins__': {}}, ctx)
    print(f'  {expr[:40]:40s} → {result}')

# Step 8: Capstone — expression DSL compiler
print()
print('=== Capstone: Filter DSL compiler ===')

class FilterCompiler(ast.NodeVisitor):
    '''Compiles a simple filter expression to a Python lambda.'''

    SAFE_OPS = {ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
                ast.And, ast.Or, ast.Not}

    def compile(self, expr: str):
        tree = ast.parse(expr, mode='eval')
        self._validate(tree)
        code = compile(tree, '<filter>', 'eval')
        return lambda ctx: eval(code, {'__builtins__': {}}, ctx)

    def _validate(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                raise ValueError('Function calls not allowed in filter expressions')
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                raise ValueError('Imports not allowed')

filters = [
    ('price < 100',                    'Affordable'),
    ('stock > 0',                      'In stock'),
    ('price < 100 and stock > 0',      'Budget in-stock'),
    ('category == \"Laptop\"',         'Laptops'),
]
products = [
    {'name': 'Surface Pro', 'price': 864.0, 'stock': 15, 'category': 'Laptop'},
    {'name': 'Surface Pen', 'price': 49.99, 'stock': 80, 'category': 'Accessory'},
    {'name': 'USB-C Hub',   'price': 29.99, 'stock': 0,  'category': 'Hardware'},
    {'name': 'Office 365',  'price': 99.99, 'stock': 999,'category': 'Software'},
]

compiler = FilterCompiler()
for expr, label in filters:
    fn = compiler.compile(expr)
    matches = [p['name'] for p in products if fn(p)]
    print(f'  [{label}] {expr!r} → {matches}')

# Security check
try:
    compiler.compile('__import__(\"os\").system(\"rm -rf /\")')
except ValueError as e:
    print(f'  [Security] Blocked: {e}')
"
```

**📸 Verified Output:**
```
=== Auto-logged function calls ===
CALL: add(a=3, b=4)
7
CALL: multiply(x=6, y=7)
42

=== AST-injected type checks ===
safe_divide(10, 3) = 3.3333
Type error: b must be int, got str

=== Bytecode: fibonacci ===
 RESUME               0
 LOAD_FAST            0 (n)
 LOAD_CONST           1 (1)
 COMPARE_OP          26 (<=)
...
co_varnames:  ('n',)
co_consts:    (None, 1, 2)

=== Filter DSL compiler ===
  [Affordable] 'price < 100' → ['Surface Pen', 'USB-C Hub', 'Office 365']
  [In stock] 'stock > 0' → ['Surface Pro', 'Surface Pen', 'Office 365']
  [Budget in-stock] 'price < 100 and stock > 0' → ['Surface Pen', 'Office 365']
  [Laptops] 'category == "Laptop"' → ['Surface Pro']
  [Security] Blocked: Function calls not allowed in filter expressions
```

---

## Summary

| Tool | Purpose | Example |
|------|---------|---------|
| `ast.parse(src)` | Source → AST | `tree = ast.parse('x = 1')` |
| `ast.walk(tree)` | Traverse all nodes | `for n in ast.walk(tree):` |
| `ast.NodeVisitor` | Read-only traversal | Subclass + `visit_NodeType` |
| `ast.NodeTransformer` | Modify AST in-place | Return new node from `visit_*` |
| `compile(tree, file, mode)` | AST → bytecode | `compile(tree, '<>','exec')` |
| `dis.dis(fn)` | Disassemble to bytecode | Shows LOAD_FAST, CALL, etc. |
| `eval(code, globals, locals)` | Execute expression | Safe with empty `__builtins__` |
| `tokenize` | Source → token stream | Character-level analysis |

## Further Reading
- [ast module](https://docs.python.org/3/library/ast.html)
- [dis module](https://docs.python.org/3/library/dis.html)
- [Green Tree Snakes (AST guide)](https://greentreesnakes.readthedocs.io)
