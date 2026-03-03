# PHP Foundations

> **Start here.** Foundations takes you from your first `echo` to a fully functional REST API — no PHP experience required. 15 hands-on labs, each building on the last, covering the core language features you'll use every day.

***

{% hint style="info" %}
**Prerequisites:** Basic programming literacy in any language (variables, loops, functions). No prior PHP experience needed. Docker must be installed — see the [PHP space overview](../) for setup instructions.
{% endhint %}

***

## 🗺️ Lab Overview

| # | Lab | Key Concepts | Time |
|---|-----|-------------|------|
| 01 | **Hello World & CLI** | Variables, `echo`, CLI args (`$argv`) | 20 min |
| 02 | **Data Types** | `int`, `float`, `string`, `bool`, `null`, type juggling | 25 min |
| 03 | **Arrays** | Indexed, associative, nested, array functions | 30 min |
| 04 | **Control Flow** | `if` / `match` / `switch`, loops, `break` / `continue` | 30 min |
| 05 | **Functions & Closures** | Typed params, arrow functions, higher-order functions | 35 min |
| 06 | **Strings & Regex** | `sprintf`, PCRE, `preg_replace`, `preg_match` | 35 min |
| 07 | **OOP Classes** | Constructor promotion, enums, `readonly`, traits | 40 min |
| 08 | **Inheritance** | `extends`, interfaces, polymorphism, `Iterator` | 35 min |
| 09 | **Error Handling** | `try` / `catch`, custom exceptions, `finally` | 30 min |
| 10 | **File I/O** | `file_get_contents`, `fopen`, CSV, JSON files | 30 min |
| 11 | **Database (PDO/SQLite)** | CRUD, prepared statements, transactions | 35 min |
| 12 | **JSON & APIs** | `json_encode` / `json_decode`, HTTP client, REST | 35 min |
| 13 | **Namespaces & Autoloading** | PSR-4, Composer, `autoload` | 30 min |
| 14 | **Type System** | Union types, intersection types, `readonly`, attributes | 30 min |
| 15 | **Capstone REST API** | Full CRUD REST API with SQLite & routing | 60 min |

**Total estimated time: ~8 hours** across 15 labs.

***

## 🚀 Start Here

{% hint style="info" %}
**Begin with Lab 01.** Each lab is self-contained but designed to be completed in order. Labs 01–06 cover the core language; Labs 07–10 introduce OOP and I/O; Labs 11–14 cover real-world integrations; Lab 15 is the capstone.
{% endhint %}

➡️ **[Lab 01 — Hello World & CLI](labs/lab-01-hello-world.md)**

Start by running your first PHP script from the command line, working with variables, and reading CLI arguments. You'll learn how the PHP interpreter works and set the foundation for everything that follows.

***

## 📋 Lab Descriptions

### Labs 1–6: Language Core

**Lab 01 — Hello World & CLI** `20 min`
Your first PHP script. Learn how to print output with `echo` and `print`, declare variables, and read command-line arguments via `$argv`. Covers the PHP interpreter invocation and basic script structure.

**Lab 02 — Data Types** `25 min`
PHP's eight primitive types: `int`, `float`, `string`, `bool`, `null`, `array`, `object`, `callable`. Understand type juggling, `strict_types`, casting, and the difference between loose (`==`) and strict (`===`) comparison.

**Lab 03 — Arrays** `30 min`
PHP arrays are ordered maps. Master indexed arrays, associative arrays, nested arrays, and the standard library: `array_map`, `array_filter`, `array_reduce`, `usort`, `array_slice`, `array_merge`.

**Lab 04 — Control Flow** `30 min`
Conditional logic with `if/elseif/else`, the `match` expression (strict, no fallthrough), `switch`, and all loop forms: `for`, `foreach`, `while`, `do-while`. Use `break` and `continue` effectively.

**Lab 05 — Functions & Closures** `35 min`
Define typed functions, use default parameters, return types, and variadic args. Write closures with `use`, arrow functions (`fn() =>`), and pass functions as first-class values to higher-order functions.

**Lab 06 — Strings & Regex** `35 min`
String manipulation: `strlen`, `str_replace`, `substr`, `trim`, `explode`, `implode`. Format output with `sprintf` and `printf`. Write PCRE patterns for `preg_match`, `preg_match_all`, and `preg_replace`.

### Labs 7–10: OOP & I/O

**Lab 07 — OOP Classes** `40 min`
PHP 8 OOP: constructor property promotion, `readonly` properties, backed enums (`Status::Active`), traits for code reuse. Write clean data classes with minimal boilerplate.

**Lab 08 — Inheritance** `35 min`
`extends` and method overriding, `abstract` classes, interface contracts, polymorphism in practice. Implement the `Iterator` interface to make custom objects work with `foreach`.

**Lab 09 — Error Handling** `30 min`
`try` / `catch` / `finally` flow, exception hierarchy, creating custom exception classes, chaining exceptions with `$previous`. Best practices: catch what you handle, let the rest bubble up.

**Lab 10 — File I/O** `30 min`
Read and write files with `file_get_contents` / `file_put_contents`, handle streams with `fopen` / `fclose`, parse CSV with `fgetcsv`, and encode/decode JSON files.

### Labs 11–14: Real-World Integrations

**Lab 11 — Database (PDO/SQLite)** `35 min`
Connect to SQLite via PDO. Perform CRUD operations with prepared statements (preventing SQL injection). Use transactions for atomic updates. Map rows to PHP objects.

**Lab 12 — JSON & APIs** `35 min`
Encode PHP data to JSON and decode JSON responses. Make HTTP requests with `file_get_contents` + stream context or `curl`. Consume a public REST API and process the response.

**Lab 13 — Namespaces & Autoloading** `30 min`
Organize code with namespaces (`namespace App\Models`). Set up Composer with `composer.json`, configure PSR-4 autoloading, and use `use` statements to import classes cleanly.

**Lab 14 — Type System** `30 min`
PHP 8's advanced types: union types (`int|string`), intersection types (`Countable&Iterator`), `never` return type, `mixed`, `readonly` classes (PHP 8.2), and PHP 8.3 typed class constants. Use `#[Attribute]` for metadata.

### Lab 15: Capstone

**Lab 15 — Capstone REST API** `60 min`
Build a complete CRUD REST API from scratch — no framework. Features: URL routing, JSON request/response, PDO/SQLite persistence, input validation, HTTP status codes, error responses. Ties together every concept from Labs 01–14.

***

## 🔗 What's Next?

After completing Foundations, move on to [**PHP Practitioner**](../practitioner/) where you'll build the same kind of APIs using Laravel — with authentication, migrations, queues, and test coverage.
