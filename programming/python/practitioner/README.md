# Python — Practitioner Level

> 15 labs covering real-world Python engineering: async I/O, type-safe APIs, data pipelines, design patterns, and CLI tooling.

## Labs

| # | Lab | Key Skill |
|---|-----|-----------|
| 01 | [Advanced OOP](labs/lab-01-advanced-oop.md) | Metaclasses, descriptors, Protocol, ABC |
| 02 | [Decorators](labs/lab-02-decorators.md) | Parameterized, class-based, lru_cache, retry |
| 03 | [Generators & itertools](labs/lab-03-generators-itertools.md) | yield from, lazy pipelines, groupby |
| 04 | [Concurrency](labs/lab-04-concurrency.md) | threading, Lock, ThreadPoolExecutor |
| 05 | [Async / Await](labs/lab-05-async-await.md) | asyncio.gather, tasks, async generators |
| 06 | [Testing with pytest](labs/lab-06-testing-pytest.md) | Fixtures, parametrize, mocking |
| 07 | [Type Hints & Generics](labs/lab-07-type-hints.md) | TypeVar, Generic, TypedDict, Protocol |
| 08 | [SQLite & Database](labs/lab-08-sqlite-database.md) | sqlite3, transactions, Repository pattern |
| 09 | [REST APIs — FastAPI](labs/lab-09-fastapi.md) | Pydantic, dependency injection, TestClient |
| 10 | [Data Processing](labs/lab-10-data-processing.md) | pandas groupby/merge, numpy vectorized ops |
| 11 | [CLI Tools](labs/lab-11-cli-tools.md) | argparse subcommands, rich tables/panels |
| 12 | [Design Patterns](labs/lab-12-design-patterns.md) | Singleton, Factory, Observer, Command |
| 13 | [Packaging & Modules](labs/lab-13-packaging-modules.md) | pyproject.toml, __init__.py, importlib |
| 14 | [Context Managers & Protocols](labs/lab-14-context-managers-protocols.md) | Dunder methods, descriptors, __slots__ |
| 15 | [Capstone — DataPipeline](labs/lab-15-capstone.md) | Async + FastAPI + SQLite + pandas + pytest |

## Prerequisites

- Python Foundations (Labs 01–15) or equivalent experience
- Basic familiarity with: OOP, functions, file I/O, exceptions

## Run All Labs

```bash
docker pull zchencow/innozverse-python:latest

# Run any lab's code block:
docker run --rm zchencow/innozverse-python:latest python3 -c "<paste code here>"
```
