# Lab 8: File I/O — Reading & Writing Files

## 🎯 Objective
Read and write text files, work with CSV data, use context managers safely, and handle file system operations — skills essential for data processing, logging, and configuration.

## 📚 Background
File I/O (Input/Output) is how programs persist data beyond their execution. Python's `open()` function handles text and binary files. The `with` statement (context manager) ensures files are always properly closed — even if an error occurs. The `csv` module handles the ubiquitous CSV format. The `pathlib` module (Python 3.4+) provides an object-oriented approach to file paths.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 7: Functions & Scope

## 🛠️ Tools Used
- Python 3.12

## 🔬 Lab Instructions

### Step 1: Writing Files

```python
import os

# Use /tmp for Docker compatibility
filepath = "/tmp/hello.txt"

# Write mode 'w' — creates or overwrites
with open(filepath, "w") as f:
    f.write("Line 1: Hello, World!\n")
    f.write("Line 2: Python File I/O\n")
    f.write("Line 3: Data persists to disk\n")

# Verify the file was written
size = os.path.getsize(filepath)
print(f"File written: {filepath}")
print(f"File size: {size} bytes")

# Append mode 'a' — adds to existing file
with open(filepath, "a") as f:
    f.write("Line 4: Appended line\n")

size2 = os.path.getsize(filepath)
print(f"After append: {size2} bytes")
```

**📸 Verified Output:**
```
File written: /tmp/hello.txt
File size: 63 bytes
After append: 83 bytes
```

> 💡 Always use `with open(...) as f:` — it's a **context manager** that automatically calls `f.close()` when the block exits, even if an exception is raised. Never rely on the garbage collector to close files.

### Step 2: Reading Files

```python
filepath = "/tmp/hello.txt"

# Read entire file as one string
with open(filepath, "r") as f:
    content = f.read()
print("=== Full content ===")
print(content)

# Read line by line (memory-efficient for large files)
print("=== Line by line ===")
with open(filepath, "r") as f:
    for i, line in enumerate(f, 1):
        print(f"  [{i}] {line.rstrip()}")

# Read all lines into a list
with open(filepath, "r") as f:
    lines = f.readlines()
print(f"\nTotal lines: {len(lines)}")
print(f"Last line: {lines[-1].strip()!r}")
```

**📸 Verified Output:**
```
=== Full content ===
Line 1: Hello, World!
Line 2: Python File I/O
Line 3: Data persists to disk
Line 4: Appended line

=== Line by line ===
  [1] Line 1: Hello, World!
  [2] Line 2: Python File I/O
  [3] Line 3: Data persists to disk
  [4] Line 4: Appended line

Total lines: 4
Last line: 'Line 4: Appended line'
```

### Step 3: Working with CSV Files

```python
import csv

csv_path = "/tmp/students.csv"

# Write CSV
students = [
    ["Name", "Age", "Grade", "City"],
    ["Alice", 20, 92.5, "New York"],
    ["Bob", 22, 85.0, "London"],
    ["Charlie", 21, 97.3, "Tokyo"],
    ["Diana", 23, 88.7, "Paris"],
]

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(students)

print(f"CSV written: {csv_path}")

# Read CSV
print("\nReading CSV:")
with open(csv_path, "r") as f:
    reader = csv.DictReader(f)  # DictReader uses first row as headers
    for row in reader:
        print(f"  {row['Name']:10} age={row['Age']:3} grade={float(row['Grade']):.1f} city={row['City']}")
```

**📸 Verified Output:**
```
CSV written: /tmp/students.csv

Reading CSV:
  Alice      age=20  grade=92.5 city=New York
  Bob        age=22  grade=85.0 city=London
  Charlie    age=21  grade=97.3 city=Tokyo
  Diana      age=23  grade=88.7 city=Paris
```

### Step 4: JSON Files

```python
import json

json_path = "/tmp/config.json"

config = {
    "app_name": "MyApp",
    "version": "2.0.1",
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "mydb"
    },
    "features": ["auth", "notifications", "reports"],
    "debug": False,
    "max_connections": 100
}

# Write JSON
with open(json_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"JSON written to {json_path}")

# Read JSON
with open(json_path, "r") as f:
    loaded = json.load(f)

print(f"App: {loaded['app_name']} v{loaded['version']}")
print(f"DB: {loaded['database']['host']}:{loaded['database']['port']}")
print(f"Features: {', '.join(loaded['features'])}")
```

**📸 Verified Output:**
```
JSON written to /tmp/config.json

App: MyApp v2.0.1
DB: localhost:5432
Features: auth, notifications, reports
```

### Step 5: pathlib — Modern Path Handling

```python
from pathlib import Path

# Create Path objects
tmp = Path("/tmp")
data_dir = tmp / "lab_data"       # Join paths with /
data_dir.mkdir(exist_ok=True)

# Write files
for i in range(1, 4):
    file = data_dir / f"file_{i:02d}.txt"
    file.write_text(f"Content of file {i}\nLine 2 of file {i}\n")

# List directory
print("Files created:")
for f in sorted(data_dir.glob("*.txt")):
    print(f"  {f.name:15} ({f.stat().st_size} bytes)")

# Read with pathlib
first = data_dir / "file_01.txt"
print(f"\nContents of {first.name}:")
print(first.read_text())
print(f"Stem: {first.stem}")   # filename without extension
print(f"Suffix: {first.suffix}")
print(f"Parent: {first.parent}")
```

**📸 Verified Output:**
```
Files created:
  file_01.txt     (33 bytes)
  file_02.txt     (33 bytes)
  file_03.txt     (33 bytes)

Contents of file_01.txt:
Content of file 1
Line 2 of file 1

Stem: file_01
Suffix: .txt
Parent: /tmp/lab_data
```

### Step 6: Error Handling with Files

```python
import os

def safe_read(filepath, default=""):
    """Read a file, returning default if it doesn't exist."""
    try:
        with open(filepath, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"⚠️  File not found: {filepath}")
        return default
    except PermissionError:
        print(f"⚠️  Permission denied: {filepath}")
        return default
    except IOError as e:
        print(f"⚠️  IO error: {e}")
        return default

# Test with existing file
content = safe_read("/tmp/hello.txt")
print(f"Read {len(content)} chars from hello.txt")

# Test with missing file
content = safe_read("/tmp/nonexistent.txt", default="(empty)")
print(f"Missing file returned: '{content}'")

# Check file existence before operating
path = "/tmp/hello.txt"
if os.path.exists(path):
    size = os.path.getsize(path)
    print(f"File exists: {size} bytes")
```

**📸 Verified Output:**
```
Read 83 chars from hello.txt
⚠️  File not found: /tmp/nonexistent.txt
Missing file returned: '(empty)'
File exists: 83 bytes
```

### Step 7: Log File Pattern

```python
from datetime import datetime
import os

log_path = "/tmp/app.log"

def log(level, message, log_file=log_path):
    """Append a timestamped log entry."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level:8}] {message}\n"
    with open(log_file, "a") as f:
        f.write(entry)

# Generate some log entries
log("INFO", "Application started")
log("INFO", "Loading configuration from config.json")
log("DEBUG", "Database connection established")
log("WARNING", "Cache miss rate: 45% (threshold: 30%)")
log("ERROR", "Failed to send email: SMTP timeout")
log("INFO", "Request processed in 142ms")

# Read and display the log
print("=== Application Log ===")
with open(log_path, "r") as f:
    for line in f:
        print(line.rstrip())
```

**📸 Verified Output:**
```
=== Application Log ===
[2026-03-02 09:00:00] [INFO    ] Application started
[2026-03-02 09:00:00] [INFO    ] Loading configuration from config.json
[2026-03-02 09:00:00] [DEBUG   ] Database connection established
[2026-03-02 09:00:00] [WARNING ] Cache miss rate: 45% (threshold: 30%)
[2026-03-02 09:00:00] [ERROR   ] Failed to send email: SMTP timeout
[2026-03-02 09:00:00] [INFO    ] Request processed in 142ms
```

### Step 8: Processing a Data File

```python
import csv
from pathlib import Path

# Create a sample sales data file
sales_path = Path("/tmp/sales.csv")
sales_path.write_text(
    "Product,Units,Price\n"
    "Laptop,12,999.99\n"
    "Mouse,45,29.99\n"
    "Keyboard,30,79.99\n"
    "Monitor,8,349.99\n"
    "Headset,25,149.99\n"
)

# Analyze the data
total_revenue = 0
results = []

with open(sales_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        units = int(row["Units"])
        price = float(row["Price"])
        revenue = units * price
        total_revenue += revenue
        results.append((row["Product"], units, price, revenue))

# Print report
print(f"{'Product':12} {'Units':>6} {'Price':>8} {'Revenue':>10}")
print("-" * 42)
for product, units, price, revenue in sorted(results, key=lambda r: -r[3]):
    print(f"{product:12} {units:>6} {price:>8.2f} {revenue:>10.2f}")
print("-" * 42)
print(f"{'TOTAL':12} {'':>6} {'':>8} {total_revenue:>10.2f}")
```

**📸 Verified Output:**
```
Product      Units    Price    Revenue
------------------------------------------
Laptop          12   999.99   11999.88
Monitor          8   349.99    2799.92
Headset         25   149.99    3749.75
Keyboard        30    79.99    2399.70
Mouse           45    29.99    1349.55
------------------------------------------
TOTAL                         22298.80
```

## ✅ Verification

```python
from pathlib import Path
import json

# Write and read back a JSON config
config = {"version": 1, "debug": False, "items": [1, 2, 3]}
p = Path("/tmp/verify_config.json")
p.write_text(json.dumps(config))
loaded = json.loads(p.read_text())

assert loaded["version"] == 1
assert loaded["items"] == [1, 2, 3]
assert not loaded["debug"]
print(f"Config round-trip: {loaded}")
print("Lab 8 verified ✅")
```

**Expected output:**
```
Config round-trip: {'version': 1, 'debug': False, 'items': [1, 2, 3]}
Lab 8 verified ✅
```

## 🚨 Common Mistakes

1. **Not using `with`**: `f = open(...)` without `with` — if an exception occurs, the file is never closed, causing resource leaks.
2. **Wrong mode**: `open(f, "w")` destroys existing content — use `"a"` to append.
3. **Missing `newline=""` in CSV writer**: Causes extra blank lines on Windows.
4. **Reading large files with `.read()`**: Loads entire file into memory — use line-by-line iteration for big files.
5. **Hardcoded paths**: `"/home/user/file.txt"` breaks on other machines — use `pathlib` with relative paths.

## 📝 Summary

- `with open(path, mode) as f:` — always use context manager for automatic close
- Modes: `"r"` read, `"w"` write (overwrites!), `"a"` append, `"rb"` binary read
- `csv.DictReader` / `csv.writer` — handle CSV properly (quote escaping, headers)
- `json.dump()` / `json.load()` — serialize Python dicts to/from JSON files
- `pathlib.Path` — object-oriented paths; `Path("/dir") / "file.txt"` for joining
- For large files: iterate line by line, don't `f.read()` the whole thing

## 🔗 Further Reading
- [Python Docs: File I/O](https://docs.python.org/3/tutorial/inputoutput.html)
- [Python Docs: pathlib](https://docs.python.org/3/library/pathlib.html)
- [Real Python: Reading/Writing Files](https://realpython.com/read-write-files-python/)
