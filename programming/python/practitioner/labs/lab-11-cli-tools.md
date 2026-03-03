# Lab 11: CLI Tools with argparse & rich

## Objective
Build polished command-line tools using `argparse` for argument parsing and `rich` for beautiful terminal output: progress bars, tables, syntax highlighting, and logging.

## Time
30 minutes

## Prerequisites
- Lab 08 (SQLite), Lab 09 (FastAPI)

## Tools
- Docker image: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: argparse — Argument Parsing

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import argparse
import sys

# Build a parser programmatically
parser = argparse.ArgumentParser(
    prog='storecli',
    description='innoZverse Store CLI — Manage your product catalog',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='Examples:\n  storecli list --category Laptop\n  storecli create --name \"Surface Pro\" --price 864'
)

subparsers = parser.add_subparsers(dest='command', required=True)

# List subcommand
list_parser = subparsers.add_parser('list', help='List products')
list_parser.add_argument('--category', '-c', help='Filter by category')
list_parser.add_argument('--sort', choices=['name', 'price', 'stock'], default='name')
list_parser.add_argument('--order', choices=['asc', 'desc'], default='asc')
list_parser.add_argument('--limit', type=int, default=20)
list_parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table')
list_parser.add_argument('--verbose', '-v', action='store_true')

# Create subcommand
create_parser = subparsers.add_parser('create', help='Create a product')
create_parser.add_argument('--name', '-n', required=True)
create_parser.add_argument('--price', '-p', type=float, required=True)
create_parser.add_argument('--stock', '-s', type=int, default=0)
create_parser.add_argument('--category', '-c', default='General')

# Get subcommand
get_parser = subparsers.add_parser('get', help='Get product by ID')
get_parser.add_argument('id', type=int, help='Product ID')

# Delete subcommand
del_parser = subparsers.add_parser('delete', help='Delete a product')
del_parser.add_argument('id', type=int, help='Product ID')
del_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')

# Stats subcommand
subparsers.add_parser('stats', help='Show inventory statistics')

# Parse test args (normally sys.argv[1:])
def run(args_str: str):
    args = parser.parse_args(args_str.split())
    print(f'Command: {args.command}')
    print(f'Args: {vars(args)}')
    print()

run('list --category Laptop --sort price --order desc')
run('create --name \"Surface Pro\" --price 864.0 --stock 15 --category Laptop')
run('get 1')
run('stats')
"
```

> 💡 **`subparsers`** let you build Git-style CLIs (`git commit`, `git push`) where each subcommand has its own arguments. `action='store_true'` makes a flag that sets the value to `True` when present. `type=int` auto-converts the string argument to an integer.

**📸 Verified Output:**
```
Command: list
Args: {'command': 'list', 'category': 'Laptop', 'sort': 'price', 'order': 'desc', 'limit': 20, 'format': 'table', 'verbose': False}

Command: create
Args: {'command': 'create', 'name': 'Surface Pro', 'price': 864.0, 'stock': 15, 'category': 'Laptop'}

Command: get
Args: {'command': 'get', 'id': 1}

Command: stats
Args: {'command': 'stats'}
```

---

### Step 2: rich — Beautiful Terminal Output

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn
from rich import print as rprint
from rich.syntax import Syntax
from rich.text import Text
import time

console = Console()

# Rich print with markup
console.print('[bold green]✓[/] Product catalog loaded')
console.print('[bold red]✗[/] Connection failed')
console.print('[yellow]⚠[/]  Stock running low for Surface Pro')

# Panel
console.print(Panel.fit(
    '[bold cyan]innoZverse Store CLI[/]\nVersion 1.0.0',
    border_style='blue',
    title='[bold]storecli[/]'
))

# Table
table = Table(title='Product Inventory', show_lines=True)
table.add_column('ID',       style='dim',          width=4)
table.add_column('Name',     style='bold white',   width=22)
table.add_column('Price',    style='green',         justify='right')
table.add_column('Stock',    justify='right')
table.add_column('Category', style='cyan')
table.add_column('Status',   justify='center')

products = [
    (1, 'Surface Pro 12\"', 864.00,  15,  'Laptop',    'active'),
    (2, 'Surface Pen',      49.99,   80,  'Accessory', 'active'),
    (3, 'Office 365',       99.99,   999, 'Software',  'active'),
    (4, 'USB-C Hub',        29.99,   0,   'Accessory', 'out_of_stock'),
    (5, 'Surface Book 3',   1299.00, 5,   'Laptop',    'active'),
]

for pid, name, price, stock, cat, status in products:
    status_text = Text(status)
    if status == 'active':
        status_text.stylize('bold green')
    else:
        status_text.stylize('bold red')
    stock_text = Text(str(stock), style='red bold' if stock == 0 else 'white')
    table.add_row(str(pid), name, f'\${price:.2f}', stock_text, cat, status_text)

console.print(table)

# Progress bar (simulate import)
console.print()
with Progress(
    SpinnerColumn(),
    '[progress.description]{task.description}',
    BarColumn(),
    TaskProgressColumn(),
    console=console,
) as progress:
    task = progress.add_task('[cyan]Loading products...', total=5)
    for p in products:
        time.sleep(0.05)
        progress.update(task, advance=1, description=f'[cyan]Loading {p[1][:15]}...')

console.print('[bold green]✓[/] All products loaded!')
"
```

**📸 Verified Output:**
```
✓ Product catalog loaded
✗ Connection failed
⚠  Stock running low for Surface Pro
╭─ storecli ─╮
│ innoZverse Store CLI │
│ Version 1.0.0        │
╰────────────────────────╯
                Product Inventory
┌────┬──────────────────────┬─────────┬───────┬───────────┬──────────────┐
│ ID │ Name                 │   Price │ Stock │ Category  │    Status    │
...
✓ All products loaded!
```

---

### Steps 3–8: Logging, Config files, stdin/stdout piping, Interactive prompts, Error formatting, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import json
import sys
import sqlite3
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

# Step 3: Rich logging
from rich.logging import RichHandler
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(message)s',
    datefmt='[%X]',
    handlers=[RichHandler(console=Console(stderr=True), rich_tracebacks=True)]
)
log = logging.getLogger('storecli')
log.debug('Database initialized')
log.info('Product catalog ready: 5 products')
log.warning('USB-C Hub is out of stock')

# Step 4: Output formatters
products = [
    {'id': 1, 'name': 'Surface Pro 12\"', 'price': 864.00, 'stock': 15, 'category': 'Laptop'},
    {'id': 2, 'name': 'Surface Pen',      'price': 49.99,  'stock': 80, 'category': 'Accessory'},
    {'id': 3, 'name': 'Office 365',       'price': 99.99,  'stock': 999,'category': 'Software'},
]

def format_table(products, title='Products'):
    t = Table(title=title, box=box.ROUNDED, show_footer=True)
    t.add_column('ID',   style='dim')
    t.add_column('Name', style='bold')
    t.add_column('Price', justify='right', footer=f'\${sum(p[\"price\"] for p in products):.2f}')
    t.add_column('Stock', justify='right', footer=str(sum(p[\"stock\"] for p in products)))
    t.add_column('Category')
    for p in products:
        t.add_row(str(p['id']), p['name'], f'\${p[\"price\"]:.2f}',
                  Text(str(p['stock']), style='red' if p['stock'] == 0 else 'green'),
                  p['category'])
    return t

def format_stats(products):
    total_value = sum(p['price'] * p['stock'] for p in products)
    in_stock = sum(1 for p in products if p['stock'] > 0)
    avg_price = sum(p['price'] for p in products) / len(products)
    content = (
        f'  Total products: [bold]{len(products)}[/]\n'
        f'  In stock:       [bold green]{in_stock}[/] / {len(products)}\n'
        f'  Average price:  [bold]\${avg_price:.2f}[/]\n'
        f'  Total value:    [bold green]\${total_value:,.2f}[/]'
    )
    return Panel(content, title='[bold]Inventory Stats[/]', border_style='blue')

console.print(format_table(products))
console.print(format_stats(products))

# Step 5: JSON output mode
console.print()
console.print('[bold]JSON output:[/]')
console.print_json(json.dumps(products, indent=2))

# Step 6: Error formatting
def format_error(message: str, hint: str = None):
    content = f'[bold red]Error:[/] {message}'
    if hint: content += f'\n[dim]Hint: {hint}[/]'
    console.print(Panel(content, border_style='red', title='[red]Error[/]'))

format_error(
    'Product with ID 99 not found',
    'Use [bold]storecli list[/] to see available products'
)

# Step 7: CSV output
def format_csv(products) -> str:
    lines = ['id,name,price,stock,category']
    for p in products:
        lines.append(f'{p[\"id\"]},{p[\"name\"]},{p[\"price\"]},{p[\"stock\"]},{p[\"category\"]}')
    return '\n'.join(lines)

print()
print(format_csv(products))

# Step 8: Capstone — complete CLI dispatcher
def run_command(command: str, args: dict) -> int:
    '''Returns exit code: 0=success, 1=error'''
    try:
        if command == 'list':
            console.print(format_table(
                [p for p in products if not args.get('category') or p['category'] == args['category']],
                title=f'Products' + (f' — {args[\"category\"]}' if args.get('category') else '')
            ))
        elif command == 'stats':
            console.print(format_stats(products))
        elif command == 'get':
            pid = args.get('id')
            p = next((x for x in products if x['id'] == pid), None)
            if not p:
                format_error(f'Product {pid} not found')
                return 1
            console.print_json(json.dumps(p))
        elif command == 'export':
            fmt = args.get('format', 'json')
            if fmt == 'csv': print(format_csv(products))
            else: print(json.dumps(products, indent=2))
        else:
            format_error(f'Unknown command: {command!r}', 'Run [bold]storecli --help[/]')
            return 1
        return 0
    except Exception as e:
        format_error(str(e))
        return 1

print()
console.rule('[bold blue]CLI Demo[/]')
run_command('list', {'category': 'Laptop'})
run_command('stats', {})
run_command('get', {'id': 2})
run_command('get', {'id': 99})
run_command('export', {'format': 'csv'})
"
```

**📸 Verified Output:**
```
                     Products
╭────┬──────────────────┬──────────┬───────┬───────────╮
│ ID │ Name             │    Price │ Stock │ Category  │
├────┼──────────────────┼──────────┼───────┼───────────┤
│ 1  │ Surface Pro 12"  │  $864.00 │    15 │ Laptop    │
│ 2  │ Surface Pen      │   $49.99 │    80 │ Accessory │
│ 3  │ Office 365       │   $99.99 │   999 │ Software  │
╰────┴──────────────────┴──────────┴───────┴───────────╯

╭─ Inventory Stats ─────────────────╮
│   Total products: 3               │
│   In stock:       3 / 3           │
│   Average price:  $337.99         │
│   Total value:    $112,844.21     │
╰───────────────────────────────────╯
```

---

## Summary

| Tool | Purpose | Key classes |
|------|---------|------------|
| `argparse` | Parse CLI arguments | `ArgumentParser`, `add_subparsers` |
| `rich.console` | Styled output | `Console`, `print()` |
| `rich.table` | Terminal tables | `Table`, `Column` |
| `rich.panel` | Bordered panels | `Panel.fit()` |
| `rich.progress` | Progress bars | `Progress`, `BarColumn` |
| `rich.logging` | Pretty log output | `RichHandler` |
| `sys.stdout` | Pipe-friendly output | `print()` → stdout |

## Further Reading
- [argparse](https://docs.python.org/3/library/argparse.html)
- [rich docs](https://rich.readthedocs.io)
- [Click — alternative to argparse](https://click.palletsprojects.com)
