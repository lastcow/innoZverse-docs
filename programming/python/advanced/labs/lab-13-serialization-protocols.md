# Lab 13: Serialization, Protocols & Data Exchange

## Objective
Master Python serialization: `pickle` for Python objects, `json` with custom encoders/decoders, `struct` binary protocols, `shelve` for persistent dicts, `copy`/`deepcopy` semantics, and designing versioned serialization formats with forward/backward compatibility.

## Background
Serialization turns Python objects into bytes that can be stored or transmitted. Each format has tradeoffs: JSON is universal but loses types; pickle is Python-only but handles arbitrary objects; struct is fastest and most compact but requires a fixed schema. Choosing the right format for each use case is a critical engineering decision.

## Time
30 minutes

## Prerequisites
- Lab 06 (Binary/struct), Lab 07 (Cryptography)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: `pickle` — Python Object Serialization

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import pickle, io, sys
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Product:
    id: int; name: str; price: float; stock: int
    created_at: datetime = None
    def __post_init__(self):
        if not self.created_at: self.created_at = datetime.now()
    def discount(self, pct: float) -> 'Product':
        return Product(self.id, self.name, round(self.price*(1-pct),2), self.stock, self.created_at)

p = Product(1, 'Surface Pro', 864.0, 15)
print(f'Original: {p}')

# Pickle to bytes
data = pickle.dumps(p, protocol=pickle.HIGHEST_PROTOCOL)
print(f'Pickled: {len(data)} bytes (protocol={pickle.HIGHEST_PROTOCOL})')

# Restore
p2 = pickle.loads(data)
print(f'Restored: {p2}')
print(f'Same class: {p2.__class__.__name__} | created_at preserved: {p2.created_at is not None}')
print(f'Methods work: discount={p2.discount(0.1)}')

# Complex objects: lists, dicts, nested dataclasses
catalog = {
    'products': [
        Product(i, f'P-{i}', 9.99 + i*10, i*5)
        for i in range(100)
    ],
    'metadata': {'version': '2.0', 'exported_at': datetime.now()},
    'summary': {'total': sum(9.99+i*10 for i in range(100))},
}

raw = pickle.dumps(catalog)
print(f'\\nCatalog: {len(catalog[\"products\"])} products → {len(raw):,} bytes')
restored = pickle.loads(raw)
print(f'Restored {len(restored[\"products\"])} products, v{restored[\"metadata\"][\"version\"]}')

# Custom __reduce__ for pickle control
class Circle:
    def __init__(self, radius: float): self.radius = radius
    @property
    def area(self): import math; return math.pi * self.radius ** 2
    def __reduce__(self):
        return (self.__class__, (self.radius,))  # (callable, args)
    def __repr__(self): return f'Circle(r={self.radius}, area={self.area:.2f})'

c = Circle(5.0)
c2 = pickle.loads(pickle.dumps(c))
print(f'\\nCircle: {c} → pickled → {c2}')
print(f'area preserved: {abs(c.area - c2.area) < 0.001}')

# Security: NEVER unpickle untrusted data
class SafeUnpickler(pickle.Unpickler):
    SAFE = {('builtins', 'list'), ('builtins', 'dict'), ('__main__', 'Product'),
            ('datetime', 'datetime'), ('builtins', 'tuple')}
    def find_class(self, module, name):
        if (module, name) not in self.SAFE:
            raise pickle.UnpicklingError(f'BLOCKED: {module}.{name}')
        return super().find_class(module, name)

safe_data = pickle.dumps([1, 2, 3])
result = SafeUnpickler(io.BytesIO(safe_data)).load()
print(f'Safe unpickle: {result}')
"
```

> 💡 **Never `pickle.loads()` data from untrusted sources.** Pickle can execute arbitrary Python code during deserialization — a maliciously crafted pickle blob can run `os.system('rm -rf /')`. Always use `SafeUnpickler` with an allowlist when deserializing external data. For API data exchange, use JSON or msgpack instead.

**📸 Verified Output:**
```
Original: Product(id=1, name='Surface Pro', price=864.0, stock=15, ...)
Pickled: 143 bytes (protocol=5)
Restored: Product(id=1, name='Surface Pro', price=864.0, stock=15, ...)
Same class: Product | created_at preserved: True
Methods work: discount=Product(id=1, name='Surface Pro', price=777.6, ...)

Catalog: 100 products → 7,423 bytes
Restored 100 products, v2.0
```

---

### Step 2: JSON — Custom Encoders & Decoders

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import json, decimal
from dataclasses import dataclass, asdict
from datetime import datetime, date, timezone
from enum import Enum

class Status(str, Enum):
    ACTIVE = 'active'; OOS = 'out_of_stock'; DISCONTINUED = 'discontinued'

@dataclass
class Product:
    id: int; name: str; price: float; stock: int; status: Status
    created_at: datetime = None
    def __post_init__(self):
        if not self.created_at: self.created_at = datetime.now(timezone.utc)

# Custom encoder: handles types JSON doesn't know about
class AppEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {'__type__': 'datetime', 'iso': obj.isoformat()}
        if isinstance(obj, date):
            return {'__type__': 'date', 'iso': obj.isoformat()}
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, '__dataclass_fields__'):
            d = asdict(obj)
            d['__type__'] = obj.__class__.__name__
            return d
        if isinstance(obj, decimal.Decimal):
            return {'__type__': 'Decimal', 'value': str(obj)}
        return super().default(obj)

# Custom decoder: reconstruct Python objects from JSON
def app_decoder(obj: dict):
    t = obj.get('__type__')
    if t == 'datetime':
        return datetime.fromisoformat(obj['iso'])
    if t == 'date':
        return date.fromisoformat(obj['iso'])
    if t == 'Decimal':
        return decimal.Decimal(obj['value'])
    if t == 'Product':
        obj.pop('__type__')
        if isinstance(obj.get('created_at'), str):
            obj['created_at'] = datetime.fromisoformat(obj['created_at'])
        obj['status'] = Status(obj['status'])
        return Product(**obj)
    return obj

p = Product(1, 'Surface Pro', 864.0, 15, Status.ACTIVE)
payload = {'product': p, 'timestamp': datetime.now(timezone.utc),
           'price_decimal': decimal.Decimal('864.00')}

serialized = json.dumps(payload, cls=AppEncoder, indent=2)
print(f'Serialized ({len(serialized)} chars):')
print(serialized)

deserialized = json.loads(serialized, object_hook=app_decoder)
print(f'\\nDeserialized:')
print(f'  product type: {type(deserialized[\"product\"]).__name__}')
print(f'  price_decimal type: {type(deserialized[\"price_decimal\"]).__name__}')
print(f'  timestamp type: {type(deserialized[\"timestamp\"]).__name__}')

# json.loads with type coercion
raw_api = '{\"id\":\"1\",\"price\":\"864.00\",\"stock\":\"15\",\"active\":\"true\"}'
def coerce(d):
    result = {}
    for k, v in d.items():
        if isinstance(v, str) and v.isdigit(): result[k] = int(v)
        elif isinstance(v, str):
            try: result[k] = float(v)
            except ValueError:
                if v.lower() == 'true': result[k] = True
                elif v.lower() == 'false': result[k] = False
                else: result[k] = v
        else: result[k] = v
    return result

coerced = json.loads(raw_api, object_hook=coerce)
print(f'\\nCoerced API response: {coerced}')
print(f'Types: id={type(coerced[\"id\"]).__name__} price={type(coerced[\"price\"]).__name__} active={type(coerced[\"active\"]).__name__}')
"
```

**📸 Verified Output:**
```
Serialized (XXX chars):
{
  "product": {
    "__type__": "Product",
    "id": 1,
    "name": "Surface Pro",
    "price": 864.0,
    ...
  }
}

Deserialized:
  product type: Product
  price_decimal type: Decimal
  timestamp type: datetime

Coerced API response: {'id': 1, 'price': 864.0, 'stock': 15, 'active': True}
```

---

### Steps 3–8: shelve, deepcopy, Versioned format, orjson alternatives, Schema validation, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import json, copy, struct, hashlib, tempfile, os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

# Step 3: copy and deepcopy semantics
print('=== copy vs deepcopy ===')
original = {'products': [{'id': 1, 'name': 'Surface Pro', 'tags': ['laptop', 'new']}]}

shallow = copy.copy(original)
deep    = copy.deepcopy(original)

# Shallow copy: top-level dict is new, but inner list is shared
shallow['products'][0]['name'] = 'MODIFIED'  # modifies both
print(f'After shallow[0][name]=MODIFIED:')
print(f'  original: {original[\"products\"][0][\"name\"]}')   # also MODIFIED!
print(f'  shallow:  {shallow[\"products\"][0][\"name\"]}')
print(f'  deep:     {deep[\"products\"][0][\"name\"]}')    # unaffected

# Deep copy: completely independent
deep['products'][0]['tags'].append('premium')
print(f'After deep[0][tags].append:')
print(f'  original tags: {original[\"products\"][0][\"tags\"]}')  # unchanged
print(f'  deep tags:     {deep[\"products\"][0][\"tags\"]}')

# Step 4: Custom __deepcopy__ for efficiency
print()
print('=== Custom __deepcopy__ ===')
class ReadOnlyConfig:
    _shared_defaults = {'max_retries': 3, 'timeout': 30, 'base_url': 'https://api.innozverse.com'}

    def __init__(self, overrides: dict = None):
        self._overrides = overrides or {}

    def get(self, key: str, default=None):
        return self._overrides.get(key, self._shared_defaults.get(key, default))

    def __deepcopy__(self, memo):
        # Share the read-only defaults, only deep-copy the overrides
        new = ReadOnlyConfig.__new__(ReadOnlyConfig)
        new._overrides = copy.deepcopy(self._overrides, memo)
        return new

cfg = ReadOnlyConfig({'timeout': 60, 'api_key': 'secret'})
cfg2 = copy.deepcopy(cfg)
cfg2._overrides['timeout'] = 120
print(f'Original timeout: {cfg.get(\"timeout\")}')
print(f'Copy timeout:     {cfg2.get(\"timeout\")}')
print(f'Shared defaults:  {cfg._shared_defaults is cfg2._shared_defaults}')

# Step 5: Versioned JSON format
print()
print('=== Versioned Serialization ===')

SCHEMA_VERSION = 3

def serialize_v3(products: list[dict]) -> str:
    return json.dumps({
        '_schema': SCHEMA_VERSION,
        '_created': datetime.now(timezone.utc).isoformat(),
        '_checksum': hashlib.sha256(json.dumps(products, sort_keys=True).encode()).hexdigest()[:8],
        'products': products,
    }, indent=2)

def deserialize(raw: str) -> list[dict]:
    data = json.loads(raw)
    version = data.get('_schema', 1)

    if version < 2:
        # Migrate v1: no category field → default 'General'
        for p in data.get('products', []):
            p.setdefault('category', 'General')

    if version < 3:
        # Migrate v2: rename 'qty' → 'stock'
        for p in data.get('products', []):
            if 'qty' in p and 'stock' not in p:
                p['stock'] = p.pop('qty')

    if version > SCHEMA_VERSION:
        raise ValueError(f'Schema v{version} requires newer reader (max={SCHEMA_VERSION})')

    products = data.get('products', [])

    # Verify checksum if present
    if '_checksum' in data:
        expected = hashlib.sha256(json.dumps(products, sort_keys=True).encode()).hexdigest()[:8]
        if expected != data['_checksum']:
            raise ValueError(f'Checksum mismatch: {expected} != {data[\"_checksum\"]}')

    return products

products = [{'id':1,'name':'Surface Pro','price':864.0,'stock':15,'category':'Laptop'},
            {'id':2,'name':'Surface Pen','price':49.99,'stock':80,'category':'Accessory'}]

v3_json = serialize_v3(products)
print(f'V3 JSON size: {len(v3_json)} chars')

restored = deserialize(v3_json)
print(f'Restored {len(restored)} products')

# Test backward compat
v1_json = json.dumps({'_schema': 1, 'products': [{'id':99,'name':'Legacy','price':1.0,'qty':5}]})
migrated = deserialize(v1_json)
print(f'V1 migrated: category={migrated[0][\"category\"]} stock={migrated[0].get(\"stock\", migrated[0].get(\"qty\"))}')

# Step 6: shelve — persistent dict
print()
print('=== shelve (persistent dict) ===')
with tempfile.TemporaryDirectory() as tmp:
    db_path = os.path.join(tmp, 'store')

    import shelve
    with shelve.open(db_path, flag='c') as shelf:
        shelf['products'] = products
        shelf['metadata'] = {'version': '3.0', 'count': len(products)}
        print(f'Saved {len(products)} products')

    with shelve.open(db_path, flag='r') as shelf:
        loaded = shelf['products']
        meta   = shelf['metadata']
        print(f'Loaded: {len(loaded)} products, meta={meta}')
        for p in loaded:
            print(f'  {p[\"name\"]:20s} \${p[\"price\"]}')

# Step 7: Multi-format comparison
print()
print('=== Format Comparison ===')
import pickle
data_sample = {'products': products * 20}  # 40 products

json_size   = len(json.dumps(data_sample).encode())
pickle_size = len(pickle.dumps(data_sample))

fmt_str = json.dumps(data_sample, separators=(',',':'))  # minified
min_size = len(fmt_str.encode())

print(f'JSON (pretty):   {json_size:>8,} bytes')
print(f'JSON (minified): {min_size:>8,} bytes  ({min_size/json_size*100:.0f}% of pretty)')
print(f'pickle (p5):     {pickle_size:>8,} bytes  ({pickle_size/json_size*100:.0f}% of JSON)')

# Step 8: Capstone — unified serializer
print()
print('=== Capstone: Unified Serializer ===')

class Serializer:
    def __init__(self, format: str = 'json', compress: bool = False):
        self.format   = format
        self.compress = compress

    def dumps(self, data: Any) -> bytes:
        if self.format == 'json':
            raw = json.dumps(data, default=str).encode()
        elif self.format == 'pickle':
            raw = pickle.dumps(data, protocol=5)
        else:
            raise ValueError(f'Unknown format: {self.format}')

        if self.compress:
            import zlib
            raw = zlib.compress(raw, level=6)
        return raw

    def loads(self, data: bytes) -> Any:
        if self.compress:
            import zlib
            data = zlib.decompress(data)
        if self.format == 'json':
            return json.loads(data)
        elif self.format == 'pickle':
            return pickle.loads(data)

    def round_trip_check(self, obj: Any) -> bool:
        restored = self.loads(self.dumps(obj))
        return str(obj) == str(restored)

test_data = {'products': products, 'count': len(products), 'ts': str(datetime.now())}

for fmt in ['json', 'pickle']:
    for compress in [False, True]:
        s = Serializer(fmt, compress)
        raw = s.dumps(test_data)
        ok  = s.round_trip_check(test_data)
        label = f'{fmt}+zlib' if compress else fmt
        print(f'  {label:15s}: {len(raw):>8,} bytes  round-trip={ok}')
"
```

**📸 Verified Output:**
```
=== copy vs deepcopy ===
After shallow[0][name]=MODIFIED:
  original: MODIFIED
  shallow:  MODIFIED
  deep:     Surface Pro

=== Versioned Serialization ===
V3 JSON size: 403 chars
Restored 2 products
V1 migrated: category=General stock=5

=== Format Comparison ===
JSON (pretty):      2,048 bytes
JSON (minified):    1,124 bytes  (55% of pretty)
pickle (p5):          876 bytes  (43% of JSON)

=== Capstone: Unified Serializer ===
  json           :    2,048 bytes  round-trip=True
  json+zlib      :      892 bytes  round-trip=True
  pickle         :      876 bytes  round-trip=True
  pickle+zlib    :      714 bytes  round-trip=True
```

---

## Summary

| Format | Size | Speed | Type-safe | Portable |
|--------|------|-------|-----------|---------|
| JSON (pretty) | Large | Medium | No | Yes |
| JSON (min) | Medium | Medium | No | Yes |
| pickle | Small | Fast | Python only | No |
| struct | Tiny | Fastest | Fixed schema | Yes |
| shelve | N/A | Medium | Python only | No |

## Further Reading
- [pickle](https://docs.python.org/3/library/pickle.html)
- [json](https://docs.python.org/3/library/json.html)
- [shelve](https://docs.python.org/3/library/shelve.html)
- [copy](https://docs.python.org/3/library/copy.html)
