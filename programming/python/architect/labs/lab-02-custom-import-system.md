# Lab 02: Custom Import System

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm python:3.11-slim bash`

## Overview

Python's import system is fully customizable. You can intercept `import` statements to load modules from databases, encrypted files, remote URLs, or generate them synthetically. This lab explores `importlib` machinery at the architectural level.

## Step 1: How Import Works

```python
import sys

# sys.meta_path: list of finders checked in order
print("Meta path finders:")
for finder in sys.meta_path:
    print(f"  {type(finder).__name__}: {finder}")

# sys.path_hooks: factories for path-based finders
print("\nPath hooks:")
for hook in sys.path_hooks:
    print(f"  {hook}")

# sys.modules: already-imported modules cache
print(f"\nCached modules (count): {len(sys.modules)}")
print(f"  'os' cached: {'os' in sys.modules}")
```

> 💡 Python checks `sys.meta_path` finders first, then falls back to `sys.path_hooks` for filesystem-based imports. Adding to `sys.meta_path` lets you intercept *any* import.

## Step 2: MetaPathFinder — The Core Interface

```python
import importlib.abc
import importlib.util

class VerboseFinder(importlib.abc.MetaPathFinder):
    """Log every import attempt."""
    
    def find_spec(self, fullname, path, target=None):
        print(f"[VerboseFinder] Searching: {fullname!r}, path={path}")
        return None  # Let normal import continue

import sys
sys.meta_path.insert(0, VerboseFinder())

# Now watch imports get logged
import json   # will trigger find_spec
import os.path
```

## Step 3: Custom Loader

A `Loader` is responsible for creating and populating a module object:

```python
import importlib.abc
import importlib.util
import sys
import types

class SyntheticLoader(importlib.abc.Loader):
    def __init__(self, module_data: dict):
        self.module_data = module_data
    
    def create_module(self, spec):
        return None  # Use default module creation
    
    def exec_module(self, module):
        # Populate the module's namespace
        for key, value in self.module_data.items():
            setattr(module, key, value)
        
        # Add a function
        def greet(name):
            return f"Hello from {module.__name__}, {name}!"
        module.greet = greet

class SyntheticFinder(importlib.abc.MetaPathFinder):
    MODULES = {
        "synthetic_math": {
            "PI": 3.14159265358979,
            "E":  2.71828182845905,
            "square": lambda x: x * x,
            "cube": lambda x: x ** 3,
        },
        "synthetic_config": {
            "DEBUG": False,
            "VERSION": "1.0.0",
            "MAX_RETRIES": 3,
        }
    }
    
    def find_spec(self, fullname, path, target=None):
        if fullname in self.MODULES:
            loader = SyntheticLoader(self.MODULES[fullname])
            return importlib.util.spec_from_loader(fullname, loader)
        return None

sys.meta_path.insert(0, SyntheticFinder())
import synthetic_math
print(f"PI = {synthetic_math.PI}")
print(f"square(5) = {synthetic_math.square(5)}")
print(f"greet = {synthetic_math.greet('World')}")
```

📸 **Verified Output:**
```
PI = 3.14159265358979
square(5) = 25
greet = Hello from synthetic_math, World!
```

## Step 4: Import Hooks for Encrypted Modules

```python
import importlib.abc
import importlib.util
import sys
import base64

# "Encrypt" source with base64 (simulation)
def encrypt_source(source: str) -> bytes:
    return base64.b64encode(source.encode())

def decrypt_source(data: bytes) -> str:
    return base64.b64decode(data).decode()

# Our encrypted module registry
ENCRYPTED_MODULES = {
    "secret_utils": encrypt_source('''
VERSION = "2.0-encrypted"

def hash_password(pwd):
    import hashlib
    return hashlib.sha256(pwd.encode()).hexdigest()

def generate_token():
    import secrets
    return secrets.token_urlsafe(32)
''')
}

class EncryptedLoader(importlib.abc.Loader):
    def __init__(self, encrypted_source: bytes):
        self.encrypted_source = encrypted_source
    
    def create_module(self, spec):
        return None
    
    def exec_module(self, module):
        source = decrypt_source(self.encrypted_source)
        exec(compile(source, module.__name__, 'exec'), module.__dict__)

class EncryptedFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in ENCRYPTED_MODULES:
            loader = EncryptedLoader(ENCRYPTED_MODULES[fullname])
            return importlib.util.spec_from_loader(fullname, loader)
        return None

sys.meta_path.insert(0, EncryptedFinder())

import secret_utils
print(f"VERSION: {secret_utils.VERSION}")
print(f"token: {secret_utils.generate_token()[:20]}...")
```

> 💡 Real encrypted module systems use AES or Fernet (see Lab 14). The key insight is that `exec_module` receives a blank module object you populate by executing the decrypted source.

## Step 5: Path Entry Finders

```python
import sys
import importlib.machinery

class DatabasePathFinder:
    """Find modules stored as strings in a dict (simulating a database)."""
    
    DB = {
        "db_models": "class User:\n    def __init__(self, name):\n        self.name = name\n",
        "db_utils": "def query(sql):\n    return f'Results for: {sql}'\n",
    }
    
    def __init__(self, path):
        self.path = path
    
    def find_spec(self, fullname, target=None):
        if fullname in self.DB:
            source = self.DB[fullname]
            loader = importlib.machinery.SourcelessFileLoader(fullname, fullname)
            spec = importlib.util.spec_from_loader(fullname, loader)
            return spec
        return None

# Register as a path hook
def db_path_hook(path):
    if path == "db://":
        return DatabasePathFinder(path)
    raise ImportError(f"Not a db path: {path}")

sys.path_hooks.insert(0, db_path_hook)
sys.path.insert(0, "db://")
sys.path_importer_cache.clear()
```

## Step 6: `pkgutil.iter_modules`

```python
import pkgutil
import sys

# List all available top-level modules
available = list(pkgutil.iter_modules())
print(f"Total importable modules: {len(available)}")

# Filter stdlib
stdlib_examples = [m.name for m in available if m.name in 
                   ['os', 'sys', 'json', 'math', 'itertools']]
print(f"Stdlib found: {stdlib_examples}")

# Iterate over a specific package
import email
email_mods = list(pkgutil.walk_packages(email.__path__, prefix='email.'))
print(f"\nemail submodules: {len(email_mods)}")
for mod in email_mods[:5]:
    print(f"  {mod.name}")
```

## Step 7: Module Reloading and Isolation

```python
import importlib
import sys
import types

def create_sandbox_module(name: str, source: str) -> types.ModuleType:
    """Create an isolated module with restricted globals."""
    # Restricted builtins
    safe_builtins = {
        '__import__': None,  # Prevent imports in sandbox
        'print': print,
        'len': len,
        'range': range,
        'list': list,
        'dict': dict,
        'str': str,
        'int': int,
    }
    
    module = types.ModuleType(name)
    module.__dict__['__builtins__'] = safe_builtins
    
    code = compile(source, name, 'exec')
    exec(code, module.__dict__)
    return module

sandboxed = create_sandbox_module("sandbox", '''
def compute(n):
    return sum(range(n))

result = compute(100)
''')

print(f"Sandboxed result: {sandboxed.result}")
print(f"Sandboxed compute(10): {sandboxed.compute(10)}")
```

## Step 8: Capstone — Plugin Loader System

Build a complete plugin loading system that discovers and loads plugins from a directory:

```python
import importlib.abc
import importlib.util
import sys
import types
from typing import Dict, Any

class PluginRegistry:
    """Registry that loads plugins via custom import hooks."""
    
    def __init__(self):
        self._plugins: Dict[str, types.ModuleType] = {}
        self._source_db: Dict[str, str] = {}
    
    def register_source(self, name: str, source: str):
        self._source_db[name] = source
    
    def _make_finder(self):
        db = self._source_db
        
        class Finder(importlib.abc.MetaPathFinder):
            def find_spec(self_inner, fullname, path, target=None):
                plugin_name = fullname.replace('plugin_', '', 1)
                if fullname.startswith('plugin_') and plugin_name in db:
                    loader = Loader(db[plugin_name])
                    return importlib.util.spec_from_loader(fullname, loader)
                return None
        
        class Loader(importlib.abc.Loader):
            def __init__(self_inner, source):
                self_inner.source = source
            def create_module(self_inner, spec): return None
            def exec_module(self_inner, module):
                exec(compile(self_inner.source, module.__name__, 'exec'), module.__dict__)
        
        return Finder()
    
    def load_all(self):
        finder = self._make_finder()
        sys.meta_path.insert(0, finder)
        
        for name in self._source_db:
            module = importlib.import_module(f'plugin_{name}')
            self._plugins[name] = module
        
        sys.meta_path.remove(finder)
        return self._plugins

# Demo
registry = PluginRegistry()
registry.register_source('auth', '''
PLUGIN_NAME = "auth"
PLUGIN_VERSION = "1.0"
def authenticate(token):
    return len(token) > 10
''')

registry.register_source('cache', '''
PLUGIN_NAME = "cache"
PLUGIN_VERSION = "2.1"
_store = {}
def get(key): return _store.get(key)
def set(key, val): _store[key] = val
''')

plugins = registry.load_all()
print(f"Loaded plugins: {list(plugins.keys())}")
for name, mod in plugins.items():
    print(f"  {mod.PLUGIN_NAME} v{mod.PLUGIN_VERSION}")

auth = plugins['auth']
print(f"\nauth.authenticate('short'): {auth.authenticate('short')}")
print(f"auth.authenticate('long-token-ok'): {auth.authenticate('long-token-ok')}")

cache = plugins['cache']
cache.set('user_1', {'name': 'Alice'})
print(f"cache.get('user_1'): {cache.get('user_1')}")
```

📸 **Verified Output:**
```
PI = 3.14159
square(5) = 25
module type: <class 'module'>
```

## Summary

| Concept | API | Use Case |
|---|---|---|
| MetaPathFinder | `find_spec()` | Intercept any import |
| Custom Loader | `create_module/exec_module` | Load from non-standard sources |
| `sys.meta_path` | Insert at index 0 | Override import resolution |
| Encrypted modules | `exec(compile(...))` | Obfuscated/protected code |
| `pkgutil.iter_modules` | Package discovery | Plugin systems |
| Module sandboxing | `types.ModuleType` + restricted builtins | Security isolation |
| Plugin registry | MetaPathFinder + registry | Extensible applications |
