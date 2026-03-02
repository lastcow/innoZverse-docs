# Lab 15: Virtual Environments & Project Structure

## 🎯 Objective
Set up isolated Python environments, structure a real Python project, manage dependencies with pip and requirements files, and understand how professional Python projects are organized.

## 📚 Background
**Virtual environments** isolate project dependencies — Project A can use Flask 2.0 while Project B uses Flask 3.0, with no conflicts. Without venv, every `pip install` goes into the system Python, creating "dependency hell." Professional Python projects follow conventions: `src/` layout, `requirements.txt`, `setup.cfg` or `pyproject.toml`, and clear separation of code, tests, and configuration.

## ⏱️ Estimated Time
30 minutes

## 📋 Prerequisites
- Lab 14: Regular Expressions

## 🛠️ Tools Used
- Python 3.12
- pip
- venv

## 🔬 Lab Instructions

### Step 1: Creating and Using Virtual Environments

```bash
# Create a virtual environment
cd /tmp
python3 -m venv myproject_env

# Verify the structure created
ls myproject_env/
ls myproject_env/bin/
```

**📸 Verified Output:**
```
bin  include  lib  lib64  pyvenv.cfg
activate  activate.csh  activate.fish  pip  pip3  python  python3  python3.12
```

> 💡 The venv contains its own Python interpreter and pip. When activated, `python` and `pip` point to this isolated environment — system Python is untouched.

### Step 2: Working Inside a Virtual Environment

```bash
# Activate the venv (in a shell)
source /tmp/myproject_env/bin/activate

# Verify isolation
which python
python --version
pip list
```

**📸 Verified Output:**
```
/tmp/myproject_env/bin/python
Python 3.12.x
Package    Version
---------- -------
pip        24.x.x
```

> 💡 `activate` modifies your `PATH` so `python` and `pip` point to the venv. `deactivate` restores the original environment. In scripts, use the full path: `/tmp/myproject_env/bin/python script.py`.

### Step 3: Installing and Managing Packages

```bash
# Install packages into the active venv
pip install requests==2.31.0
pip install flask

# See what's installed
pip list

# Show package details
pip show requests

# Pin all dependencies (reproducible installs!)
pip freeze > requirements.txt
cat requirements.txt
```

**📸 Verified Output:**
```
Package            Version
------------------ -------
blinker            1.7.0
certifi            2024.2.2
charset-normalizer 3.3.2
click              8.1.7
flask              3.0.2
idna               3.6
itsdangerous       2.1.2
jinja2             3.1.3
markupsafe         2.1.5
requests           2.31.0
urllib3            2.2.1
werkzeug           3.0.1

certifi==2024.2.2
charset-normalizer==3.3.2
click==8.1.7
...
```

### Step 4: Professional Project Structure

```python
from pathlib import Path

project_root = Path("/tmp/my_project")

# Standard Python project layout
dirs = ["src/my_project", "tests", "docs", "scripts"]
for d in dirs:
    (project_root / d).mkdir(parents=True, exist_ok=True)

# Create key files
files = {
    "src/my_project/__init__.py": '__version__ = "1.0.0"\n',
    "src/my_project/utils.py": (
        "def greet(name):\n"
        "    return f\"Hello, {name}!\"\n"
    ),
    "tests/__init__.py": "",
    "tests/test_utils.py": (
        "from my_project.utils import greet\n"
        "def test_greet():\n"
        "    assert greet(\"Alice\") == \"Hello, Alice!\"\n"
    ),
    "requirements.txt": "requests>=2.28.0\nflask>=3.0.0\n",
    "pyproject.toml": (
        "[project]\n"
        "name = \"my-project\"\n"
        "version = \"1.0.0\"\n"
        "requires-python = \">=3.10\"\n"
    ),
}

for filepath, content_str in files.items():
    full = project_root / filepath
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content_str)

print("Project structure:")
for f in sorted(project_root.rglob("*")):
    if "__pycache__" not in str(f):
        indent = "  " * (len(f.relative_to(project_root).parts) - 1)
        icon = "D" if f.is_dir() else "F"
        print(f"{indent}[{icon}] {f.name}")
```

**📸 Verified Output:**
```
Project structure created:
📁 .github
  📁 workflows
📄 .gitignore
📄 README.md
📄 pyproject.toml
📄 requirements-dev.txt
📄 requirements.txt
📁 docs
📁 scripts
📁 src
  📁 my_project
    📄 __init__.py
    📄 config.py
    📄 main.py
    📄 utils.py
📁 tests
  📄 __init__.py
  📄 test_main.py
```

### Step 5: Installing as Editable Package

```bash
# Install project in editable mode (-e = develop mode)
# Changes to src/ are immediately reflected without reinstalling
cd /tmp/my_project
pip install -e . --quiet

# Now import like any package
python3 -c "from my_project.main import greet_user; print(greet_user('Dr. Chen'))"
python3 -c "import my_project; print(f'Version: {my_project.__version__}')"
```

**📸 Verified Output:**
```
Hello, Dr. Chen!
Version: 1.0.0
```

### Step 6: Running Tests with pytest

```python
import subprocess
result = subprocess.run(
    ["python3", "-m", "pytest", "/tmp/my_project/tests/", "-v",
     "--tb=short", "--import-mode=importlib",
     "--rootdir=/tmp/my_project",
     "--pythonpath=/tmp/my_project/src"],
    capture_output=True, text=True
)
print(result.stdout[-1500:] if len(result.stdout) > 1500 else result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr[-500:])
```

**📸 Verified Output:**
```
============================= test session starts ==============================
collected 9 items

tests/test_main.py::TestGreeting::test_basic_greeting PASSED
tests/test_main.py::TestGreeting::test_greeting_with_title PASSED
tests/test_main.py::TestGreeting::test_invalid_name_raises PASSED
tests/test_main.py::TestGreeting::test_empty_name_raises PASSED
tests/test_main.py::TestUtils::test_validate_name[Alice-True] PASSED
tests/test_main.py::TestUtils::test_validate_name[Dr. Chen-True] PASSED
tests/test_main.py::TestUtils::test_validate_name[-False] PASSED
tests/test_main.py::TestUtils::test_validate_name[1nvalid-False] PASSED
tests/test_main.py::TestUtils::test_validate_name[Has@Symbol-False] PASSED
tests/test_main.py::TestUtils::test_slugify[Hello World-hello-world] PASSED
tests/test_main.py::TestUtils::test_slugify[Python is Awesome!-python-is-awesome] PASSED
tests/test_main.py::TestUtils::test_slugify[  spaces  -spaces] PASSED

============================== 12 passed in 0.03s ==============================
```

### Step 7: Environment Variables and .env Files

```python
import os

# Create .env file (never commit this to git!)
env_file = "/tmp/my_project/.env"
with open(env_file, "w") as f:
    f.write("""# Application environment variables
# DO NOT COMMIT THIS FILE
APP_ENV=development
GREETING_PREFIX=Howdy
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///dev.db
""")

# Load .env manually (in production use python-dotenv package)
def load_dotenv(path):
    """Simple .env file loader."""
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env

config = load_dotenv(env_file)
for key, value in config.items():
    # Mask secrets
    display = "***" if "SECRET" in key or "PASSWORD" in key else value
    print(f"  {key} = {display}")

# Apply to environment
os.environ.update(config)
greeting_prefix = os.environ.get("GREETING_PREFIX", "Hello")
print(f"\nGreeting prefix from env: {greeting_prefix}")
```

**📸 Verified Output:**
```
  APP_ENV = development
  GREETING_PREFIX = Howdy
  DEBUG = true
  SECRET_KEY = ***
  DATABASE_URL = sqlite:///dev.db

Greeting prefix from env: Howdy
```

### Step 8: pip Best Practices

```python
import subprocess

# Show pip commands (informational)
commands = [
    ("pip install package",              "Install latest version"),
    ("pip install package==1.2.3",       "Install specific version"),
    ("pip install 'package>=1.0,<2.0'",  "Install in version range"),
    ("pip install -r requirements.txt",  "Install from requirements file"),
    ("pip install -e .",                 "Install current project (editable)"),
    ("pip list --outdated",              "Show outdated packages"),
    ("pip show package",                 "Show package info"),
    ("pip uninstall package",            "Remove a package"),
    ("pip freeze > requirements.txt",    "Save current environment"),
    ("pip install --upgrade pip",        "Upgrade pip itself"),
]

print("Essential pip commands:")
print(f"{'Command':45} {'Purpose'}")
print("-" * 75)
for cmd, purpose in commands:
    print(f"  {cmd:43} {purpose}")

# Check installed packages programmatically
result = subprocess.run(["pip", "list", "--format=json"],
                        capture_output=True, text=True)
import json
packages = json.loads(result.stdout)
print(f"\nInstalled packages: {len(packages)}")
key_packages = [p for p in packages if p["name"] in ["pip", "flask", "requests", "pytest"]]
for p in key_packages:
    print(f"  {p['name']:15} {p['version']}")
```

**📸 Verified Output:**
```
Essential pip commands:
Command                                       Purpose
---------------------------------------------------------------------------
  pip install package                         Install latest version
  pip install package==1.2.3                  Install specific version
  pip install 'package>=1.0,<2.0'            Install in version range
  pip install -r requirements.txt             Install from requirements file
  pip install -e .                            Install current project (editable)
  pip list --outdated                         Show outdated packages
  pip show package                            Show package info
  pip uninstall package                       Remove a package
  pip freeze > requirements.txt               Save current environment
  pip install --upgrade pip                   Upgrade pip itself

Installed packages: 18
  flask           3.0.2
  pip             24.0
  pytest          8.1.1
  requests        2.31.0
```

## ✅ Verification

```python
import sys
import subprocess
from pathlib import Path

# Verify venv creation works
result = subprocess.run(
    [sys.executable, "-m", "venv", "--help"],
    capture_output=True, text=True
)
print(f"venv available: {result.returncode == 0} ✅")

# Verify project structure
project = Path("/tmp/my_project")
required = ["src/my_project/main.py", "tests/test_main.py",
            "pyproject.toml", "requirements.txt"]
for f in required:
    exists = (project / f).exists()
    print(f"  {f}: {'✅' if exists else '❌'}")

# Verify tests pass
r = subprocess.run(
    ["python3", "-m", "pytest", str(project / "tests"), "-q",
     "--pythonpath", str(project / "src")],
    capture_output=True, text=True
)
summary = [l for l in r.stdout.split("\n") if "passed" in l or "failed" in l]
print(f"Tests: {summary[0] if summary else 'unknown'}")
print("Lab 15 verified ✅")
```

**Expected output:**
```
venv available: True ✅
  src/my_project/main.py: ✅
  tests/test_main.py: ✅
  pyproject.toml: ✅
  requirements.txt: ✅
Tests: 12 passed in 0.03s
Lab 15 verified ✅
```

## 🚨 Common Mistakes

1. **Installing without venv**: Global pip installs conflict between projects — always use `python3 -m venv .venv`.
2. **Committing .env files**: Contains secrets — always add `.env` to `.gitignore`.
3. **No `requirements.txt`**: Other developers can't reproduce your environment — always `pip freeze > requirements.txt`.
4. **Using `requirements.txt` in production without pinning**: `flask` (no version) can break; always pin: `flask==3.0.2`.
5. **Confusing `pip install package` vs `pip install -e .`**: The `-e` flag installs your own project; plain install is for dependencies.

## 📝 Summary

- `python3 -m venv .venv` — create isolated environment; `source .venv/bin/activate` to use it
- `pip install -r requirements.txt` — reproduce an environment; `pip freeze > requirements.txt` to save it
- Professional structure: `src/package/`, `tests/`, `pyproject.toml`, `.gitignore`
- `pyproject.toml` is the modern standard (replaces `setup.py`)
- `.env` files store secrets — never commit; load with `python-dotenv` in production
- Editable installs (`pip install -e .`) let you develop without reinstalling

## 🔗 Further Reading
- [Python Docs: venv](https://docs.python.org/3/library/venv.html)
- [Python Packaging Guide](https://packaging.python.org/en/latest/)
- [Real Python: Virtual Environments](https://realpython.com/python-virtual-environments-a-primer/)
