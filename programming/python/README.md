# Python

> **The most versatile language on Earth.** Data science, web APIs, automation, AI, scripting — Python does it all with clean, readable syntax. Start with `print("Hello")` and end up building production ML pipelines.

---

## 📚 Learning Path

<table data-view="cards">
  <thead>
    <tr>
      <th></th>
      <th></th>
      <th data-hidden data-card-target data-type="content-ref"></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>🟢 Foundations</strong></td>
      <td>Variables, functions, OOP, file I/O, regex, error handling — 15 verified labs</td>
      <td><a href="foundations/">foundations</a></td>
    </tr>
    <tr>
      <td><strong>🔵 Practitioner</strong></td>
      <td>Decorators, async/await, type hints, SQLite, FastAPI, pandas, design patterns — 15 labs</td>
      <td><a href="practitioner/">practitioner</a></td>
    </tr>
    <tr>
      <td><strong>🟠 Advanced</strong></td>
      <td>Microservices, ML pipelines, packaging, performance profiling — coming soon</td>
      <td><a href="advanced/">advanced</a></td>
    </tr>
  </tbody>
</table>

---

## 🐳 Quick Start

{% tabs %}
{% tab title="🐳 Docker (Recommended)" %}
```bash
# Pull the verified image
docker pull zchencow/innozverse-python:latest

# Run any Python snippet
docker run --rm zchencow/innozverse-python:latest \
  python3 -c "print('Hello from Python 3.12!')"

# Interactive REPL
docker run --rm -it zchencow/innozverse-python:latest python3
```

**Included packages:** `fastapi 0.135` · `pydantic 2.12` · `pandas 3.0` · `numpy 2.4` · `pytest 9.0` · `requests 2.32` · `uvicorn 0.41` · `rich`
{% endtab %}

{% tab title="🐧 Ubuntu / Debian" %}
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv

# Create isolated environment
python3 -m venv .venv && source .venv/bin/activate

# Install lab packages
pip install fastapi pydantic pandas numpy pytest requests uvicorn rich

python3 --version    # Python 3.12+
```
{% endtab %}

{% tab title="🍎 macOS" %}
```bash
# Install via Homebrew
brew install python@3.12

python3 -m venv .venv && source .venv/bin/activate
pip install fastapi pydantic pandas numpy pytest requests uvicorn rich

python3 --version
```
{% endtab %}

{% tab title="🪟 Windows" %}
```powershell
# Download Python 3.12 from python.org
# Then in PowerShell:
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install fastapi pydantic pandas numpy pytest requests uvicorn rich

python --version
```
{% endtab %}
{% endtabs %}

---

## 🟢 Foundations — 15 Labs

Core Python skills, all verified on Python 3.12.

| Lab | Topic | Key Concepts |
|-----|-------|-------------|
| 01 | Hello World & Basics | Variables, types, f-strings, REPL |
| 02 | Control Flow | if/elif, for, while, comprehensions |
| 03 | Functions & Scope | args, kwargs, closures, LEGB |
| 04 | Data Structures | list, dict, set, tuple, deque |
| 05 | Strings & Regex | str methods, `re` module, groups |
| 06 | File I/O | open, pathlib, JSON, CSV |
| 07 | Error Handling | try/except, custom exceptions, finally |
| 08 | OOP Basics | class, `__init__`, inheritance, `super()` |
| 09 | OOP Advanced | `@property`, `@classmethod`, `@staticmethod` |
| 10 | Modules & stdlib | `os`, `sys`, `datetime`, `collections` |
| 11 | Comprehensions | list/dict/set/gen expressions |
| 12 | Decorators Intro | `@wraps`, simple wrappers |
| 13 | Iterators & Generators | `yield`, `next()`, `iter()` |
| 14 | Context Managers | `with`, `__enter__`/`__exit__` |
| 15 | Capstone | CLI task manager, file persistence |

---

## 🔵 Practitioner — 15 Labs

Real-world Python engineering with advanced patterns.

| Lab | Topic | Key Concepts |
|-----|-------|-------------|
| 01 | Advanced OOP | Metaclasses, descriptors, Protocol, ABC, `__slots__` |
| 02 | Decorators | Parameterized, class decorators, `lru_cache`, retry/rate-limit |
| 03 | Generators & itertools | `yield from`, lazy pipelines, `chain`, `groupby`, `combinations` |
| 04 | Concurrency | `threading`, `Lock`, `ThreadPoolExecutor`, `ProcessPoolExecutor` |
| 05 | Async / Await | `asyncio.gather`, tasks, timeouts, async generators, `asyncio.Queue` |
| 06 | Testing with pytest | Fixtures, parametrize, `unittest.mock`, `AsyncMock`, `pytest.approx` |
| 07 | Type Hints & Generics | `TypeVar`, `Generic[T]`, `TypedDict`, `Literal`, `Protocol`, `Final` |
| 08 | SQLite & Database | `sqlite3`, parameterized queries, transactions, Repository pattern |
| 09 | REST APIs — FastAPI | Pydantic models, dependency injection, `TestClient`, background tasks |
| 10 | Data Processing | `pandas` groupby/merge/pivot, `numpy` vectorized ops, time series |
| 11 | CLI Tools | `argparse` subcommands, `rich` tables/progress/panels, logging |
| 12 | Design Patterns | Singleton, Factory, Observer, Strategy, Command, Builder, Composite |
| 13 | Packaging & Modules | `pyproject.toml`, `__init__.py`, lazy imports, `importlib` |
| 14 | Context Mgrs & Protocols | `__dunder__` deep-dive, descriptor protocol, `@total_ordering` |
| 15 | Capstone — DataPipeline | Async pipeline + SQLite + FastAPI + pandas + rich CLI + pytest |

{% hint style="success" %}
**All Practitioner labs verified** inside `zchencow/innozverse-python:latest` (Python 3.12.12). Every code block produces the exact output shown.
{% endhint %}

---

## 🛠 Lab Environment

```bash
# Verify your environment
docker run --rm zchencow/innozverse-python:latest python3 -c "
import sys, fastapi, pydantic, pandas, numpy, pytest
print(f'Python:  {sys.version.split()[0]}')
print(f'FastAPI: {fastapi.__version__}')
print(f'Pydantic:{pydantic.__version__}')
print(f'pandas:  {pandas.__version__}')
print(f'numpy:   {numpy.__version__}')
print(f'pytest:  {pytest.__version__}')
"
```

Expected output:
```
Python:   3.12.12
FastAPI:  0.135.1
Pydantic: 2.12.5
pandas:   3.0.1
numpy:    2.4.2
pytest:   9.0.2
```

---

## 🔗 Resources

- [Python 3.12 Docs](https://docs.python.org/3/)
- [Real Python Tutorials](https://realpython.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [pandas User Guide](https://pandas.pydata.org/docs/user_guide/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Docker Hub: zchencow/innozverse-python](https://hub.docker.com/r/zchencow/innozverse-python)
