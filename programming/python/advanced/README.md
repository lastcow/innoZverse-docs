# Python Advanced

Master production-grade Python: metaprogramming, memory management, high-performance computing, cryptography, and advanced architecture patterns.

{% hint style="info" %}
**Prerequisites:** Complete Python Practitioner before starting Advanced labs.
{% endhint %}

## Quick Start

{% tabs %}
{% tab title="🐳 Docker (Recommended)" %}
```bash
docker pull zchencow/innozverse-python:latest
docker run --rm zchencow/innozverse-python:latest python3 --version
```
{% endtab %}
{% tab title="🐧 Linux / macOS" %}
```bash
python3 --version   # requires 3.12+
pip install numpy pandas fastapi uvicorn pydantic pytest requests rich
```
{% endtab %}
{% endtabs %}

## Labs

<table data-view="cards">
<thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead>
<tbody>
<tr><td><strong>Lab 01</strong><br>Metaprogramming</td><td>Metaclasses, <code>__init_subclass__</code>, type factory</td><td><a href="labs/lab-01-metaprogramming.md">lab-01</a></td></tr>
<tr><td><strong>Lab 02</strong><br>AST & Bytecode</td><td>ast.parse, NodeTransformer, dis, compile</td><td><a href="labs/lab-02-ast-bytecode.md">lab-02</a></td></tr>
<tr><td><strong>Lab 03</strong><br>Memory Management</td><td>tracemalloc, __slots__, WeakValueDictionary, GC</td><td><a href="labs/lab-03-memory-management.md">lab-03</a></td></tr>
<tr><td><strong>Lab 04</strong><br>Profiling & Performance</td><td>cProfile, timeit, memoization, numpy vs Python</td><td><a href="labs/lab-04-profiling-performance.md">lab-04</a></td></tr>
<tr><td><strong>Lab 05</strong><br>Advanced Async</td><td>Semaphore, TaskGroup, producer-consumer, retry</td><td><a href="labs/lab-05-advanced-async.md">lab-05</a></td></tr>
<tr><td><strong>Lab 06</strong><br>ctypes & Binary</td><td>struct, binary file format, ctypes.Structure, TLV</td><td><a href="labs/lab-06-ctypes-binary.md">lab-06</a></td></tr>
<tr><td><strong>Lab 07</strong><br>Cryptography</td><td>hashlib, HMAC, PBKDF2, secrets, signed tokens</td><td><a href="labs/lab-07-cryptography.md">lab-07</a></td></tr>
<tr><td><strong>Lab 08</strong><br>Advanced SQLite</td><td>Window functions, FTS5, CTEs, WAL, JSON</td><td><a href="labs/lab-08-advanced-sqlite.md">lab-08</a></td></tr>
<tr><td><strong>Lab 09</strong><br>numpy Advanced</td><td>Broadcasting, einsum, vectorize, linear algebra</td><td><a href="labs/lab-09-numpy-advanced.md">lab-09</a></td></tr>
<tr><td><strong>Lab 10</strong><br>pandas Advanced</td><td>MultiIndex, time series, pipe(), ETL pipeline</td><td><a href="labs/lab-10-pandas-advanced.md">lab-10</a></td></tr>
<tr><td><strong>Lab 11</strong><br>Concurrency Advanced</td><td>ProcessPool, Actor pattern, BoundedBuffer, hybrid</td><td><a href="labs/lab-11-concurrency-advanced.md">lab-11</a></td></tr>
<tr><td><strong>Lab 12</strong><br>Plugin Architecture</td><td>DI container, importlib, versioned plugins</td><td><a href="labs/lab-12-plugin-architecture.md">lab-12</a></td></tr>
<tr><td><strong>Lab 13</strong><br>Serialization</td><td>JSON encoder/decoder, pickle, struct frames, base64</td><td><a href="labs/lab-13-serialization-protocols.md">lab-13</a></td></tr>
<tr><td><strong>Lab 14</strong><br>Networking</td><td>Raw TCP, framing, urllib HTTP, asyncio streams</td><td><a href="labs/lab-14-networking-sockets.md">lab-14</a></td></tr>
<tr><td><strong>Lab 15</strong><br>🏆 Capstone</td><td>Production data service — all techniques combined</td><td><a href="labs/lab-15-capstone.md">lab-15</a></td></tr>
</tbody>
</table>
