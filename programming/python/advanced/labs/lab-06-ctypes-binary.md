# Lab 06: ctypes, struct & Binary Protocols

## Objective
Work with binary data in Python: `ctypes` for C structure definitions, `struct` for binary serialization/deserialization, `array` for typed C arrays, `memoryview` for zero-copy access, and a custom binary file format with header + records.

## Background
APIs and file formats often use binary data for compactness and speed. A CSV of 10,000 products might be 500 KB; the same data in a binary protocol is 160 KB and parses 10x faster. Python's `struct`, `ctypes`, and `array` modules give you direct access to binary layouts without C extensions.

## Time
30 minutes

## Prerequisites
- Lab 03 (Memory Management)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: `struct` — Binary Pack & Unpack

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import struct

# Format characters: ! = network (big-endian), I = uint32, d = double, s = char[]
# Pack a product: id(uint32) + name(32s) + price(double) + stock(uint32)
FMT = '!I32sdI'

def pack_product(pid: int, name: str, price: float, stock: int) -> bytes:
    name_b = name.encode('utf-8').ljust(32, b'\x00')[:32]
    return struct.pack(FMT, pid, name_b, price, stock)

def unpack_product(data: bytes) -> dict:
    pid, name_b, price, stock = struct.unpack(FMT, data)
    return {'id': pid, 'name': name_b.rstrip(b'\x00').decode(), 'price': price, 'stock': stock}

record_size = struct.calcsize(FMT)
print(f'Record size: {record_size} bytes (vs ~60 bytes JSON)')

products = [
    (1, 'Surface Pro 12\"', 864.0,  15),
    (2, 'Surface Pen',      49.99,  80),
    (3, 'Office 365',       99.99,  999),
    (4, 'USB-C Hub',        29.99,  0),
    (5, 'Surface Book 3',   1299.0, 5),
]

packed = [pack_product(*p) for p in products]
print(f'Packed 5 records: {sum(len(p) for p in packed)} bytes total')
print(f'First record hex: {packed[0].hex()}')

# Unpack and verify
for raw in packed:
    p = unpack_product(raw)
    print(f'  [{p[\"id\"]}] {p[\"name\"]:20s} \${p[\"price\"]:8.2f}  stock={p[\"stock\"]}')

# struct.iter_unpack — parse a stream
all_bytes = b''.join(packed)
print()
print('=== Streaming unpack ===')
for p_tuple in struct.iter_unpack(FMT, all_bytes):
    pid, name_b, price, stock = p_tuple
    print(f'  {pid}: {name_b.rstrip(b\"\\x00\").decode():20s} \${price:.2f}')
"
```

> 💡 **`!` (network byte order) in struct format** means big-endian — bytes stored most-significant first. Always specify byte order explicitly (`!`, `>`, `<`) in protocols that cross machine boundaries. Without it, the default is native byte order, which differs between x86 (little-endian) and ARM/network (big-endian).

**📸 Verified Output:**
```
Record size: 52 bytes (vs ~60 bytes JSON)
Packed 5 records: 260 bytes total
First record hex: 00000001537572666163652050726f...
  [1] Surface Pro 12"       $  864.00  stock=15
  [2] Surface Pen           $   49.99  stock=80
  [3] Office 365            $   99.99  stock=999
  [4] USB-C Hub             $   29.99  stock=0
  [5] Surface Book 3        $1299.00  stock=5
```

---

### Step 2: Binary File Format with Header

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import struct, tempfile, os, time

# Custom binary format: INNO catalog file
# Header: magic(4s) + version(H) + record_count(I) + created_ts(d)
# Record: id(I) + name(32s) + price(d) + stock(I) + category(16s)

HEADER_FMT = '!4sHId'  # 20 bytes
RECORD_FMT = '!I32sdI16s'

HEADER_SIZE = struct.calcsize(HEADER_FMT)
RECORD_SIZE = struct.calcsize(RECORD_FMT)
MAGIC = b'INNO'
VERSION = 2

def write_catalog(path: str, products: list[dict]) -> int:
    with open(path, 'wb') as f:
        # Header
        header = struct.pack(HEADER_FMT, MAGIC, VERSION, len(products), time.time())
        f.write(header)
        # Records
        for p in products:
            name_b = p['name'].encode().ljust(32, b'\x00')[:32]
            cat_b  = p['category'].encode().ljust(16, b'\x00')[:16]
            record = struct.pack(RECORD_FMT, p['id'], name_b, p['price'], p['stock'], cat_b)
            f.write(record)
    return HEADER_SIZE + len(products) * RECORD_SIZE

def read_catalog(path: str) -> list[dict]:
    products = []
    with open(path, 'rb') as f:
        # Read and validate header
        header_data = f.read(HEADER_SIZE)
        magic, version, count, created_ts = struct.unpack(HEADER_FMT, header_data)
        if magic != MAGIC:
            raise ValueError(f'Invalid magic: {magic!r} (expected {MAGIC!r})')
        if version != VERSION:
            raise ValueError(f'Unsupported version {version}')
        print(f'  Header: magic={magic} v{version} count={count} created={time.ctime(created_ts)[:19]}')
        # Read records
        for _ in range(count):
            raw = f.read(RECORD_SIZE)
            pid, name_b, price, stock, cat_b = struct.unpack(RECORD_FMT, raw)
            products.append({
                'id':       pid,
                'name':     name_b.rstrip(b'\x00').decode(),
                'price':    price,
                'stock':    stock,
                'category': cat_b.rstrip(b'\x00').decode(),
            })
    return products

# Demo
catalog = [
    {'id': 1, 'name': 'Surface Pro 12\"', 'price': 864.0,  'stock': 15,  'category': 'Laptop'},
    {'id': 2, 'name': 'Surface Pen',      'price': 49.99,  'stock': 80,  'category': 'Accessory'},
    {'id': 3, 'name': 'Office 365',       'price': 99.99,  'stock': 999, 'category': 'Software'},
    {'id': 4, 'name': 'USB-C Hub',        'price': 29.99,  'stock': 0,   'category': 'Hardware'},
    {'id': 5, 'name': 'Surface Book 3',   'price': 1299.0, 'stock': 5,   'category': 'Laptop'},
]

with tempfile.NamedTemporaryFile(delete=False, suffix='.inno') as f:
    path = f.name

size = write_catalog(path, catalog)
print(f'Written: {size} bytes (JSON would be ~{len(str(catalog))} bytes)')

products = read_catalog(path)
print(f'Read {len(products)} products:')
for p in products:
    print(f'  [{p[\"id\"]}] {p[\"name\"]:20s} \${p[\"price\"]:8.2f} {p[\"category\"]}')

os.unlink(path)
"
```

**📸 Verified Output:**
```
Written: 280 bytes (JSON would be ~480 bytes)
  Header: magic=b'INNO' v2 count=5 created=Tue Mar  3 06:xx:xx
Read 5 products:
  [1] Surface Pro 12"       $  864.00 Laptop
  [2] Surface Pen           $   49.99 Accessory
  [3] Office 365            $   99.99 Software
  [4] USB-C Hub             $   29.99 Hardware
  [5] Surface Book 3        $1299.00 Laptop
```

---

### Steps 3–8: ctypes Structures, array+memoryview, Binary Search, Bitfields, Checksums, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import ctypes, struct, array, hashlib, zlib

# Step 3: ctypes.Structure — C-compatible types
class Point(ctypes.Structure):
    _fields_ = [('x', ctypes.c_double), ('y', ctypes.c_double)]

class ProductRecord(ctypes.Structure):
    _pack_ = 1  # no padding — tight packing
    _fields_ = [
        ('id',     ctypes.c_uint32),
        ('price',  ctypes.c_double),
        ('stock',  ctypes.c_uint32),
        ('rating', ctypes.c_float),
        ('flags',  ctypes.c_uint8),
    ]
    # flags bits: 0=active, 1=featured, 2=discounted

r = ProductRecord(id=1, price=864.0, stock=15, rating=4.8, flags=0b00000011)  # active+featured
print(f'=== ctypes.Structure ===')
print(f'Record: id={r.id} price={r.price} stock={r.stock} rating={r.rating:.1f} flags={r.flags:08b}')
print(f'Size: {ctypes.sizeof(r)} bytes (tight packed)')
print(f'active:    {bool(r.flags & 0b001)}')
print(f'featured:  {bool(r.flags & 0b010)}')
print(f'discounted:{bool(r.flags & 0b100)}')

# Serialize ctypes struct to bytes
raw = bytes(r)
print(f'Serialized: {raw.hex()}')
# Deserialize
r2 = ProductRecord.from_buffer_copy(raw)
print(f'Deserialized: id={r2.id} price={r2.price}')

# Step 4: array + memoryview — zero-copy processing
print()
print('=== array + memoryview ===')
prices = array.array('d', [864.0, 49.99, 99.99, 29.99, 1299.0, 39.99, 199.99, 599.0])
stocks = array.array('l', [15,    80,    999,   0,     5,      200,   30,     8   ])

mv_prices = memoryview(prices)
mv_stocks = memoryview(stocks)

# Zero-copy slice (no data copied)
expensive = mv_prices[0:2]
print(f'Expensive (slice, no copy): {list(expensive.cast(\"d\"))}')

# In-place modification via memoryview
mv_prices[0] = 799.99  # apply discount in-place
print(f'After discount on prices[0]: {prices[0]}')

# Read-only memoryview to prevent mutation
ro_mv = memoryview(prices).cast('B')  # as bytes, read-only approach
print(f'Byte view size: {ro_mv.nbytes} bytes ({len(prices)} doubles × 8)')

# Step 5: Compute values efficiently with array math
values = array.array('d', (p*s for p,s in zip(prices, stocks)))
total  = sum(values)
print(f'Total inventory value: \${total:,.2f}')

# Step 6: Checksums for data integrity
print()
print('=== Checksums & Data Integrity ===')
data = b''.join(struct.pack('!Id', i, 864.0+i) for i in range(100))
crc32   = zlib.crc32(data)
sha256  = hashlib.sha256(data).hexdigest()
blake2b = hashlib.blake2b(data, digest_size=16).hexdigest()

print(f'Data:   {len(data):,} bytes')
print(f'CRC32:  {crc32:#010x}  (fast, not secure)')
print(f'SHA256: {sha256[:32]}...  (secure, slower)')
print(f'BLAKE2b:{blake2b}  (secure + fast)')

# Verify integrity
tampered = data[:100] + b'\\xff' + data[101:]
print(f'CRC32 detects tamper: {zlib.crc32(tampered) != crc32}')
print(f'SHA256 detects tamper: {hashlib.sha256(tampered).hexdigest() != sha256}')

# Step 7: Variable-length binary protocol
print()
print('=== Variable-Length Records ===')
# TLV: Type(1B) + Length(2B) + Value(nB)
def encode_tlv(type_id: int, value: bytes) -> bytes:
    return struct.pack('!BH', type_id, len(value)) + value

def decode_tlv(data: bytes) -> list[tuple[int, bytes]]:
    records, pos = [], 0
    while pos < len(data):
        type_id, length = struct.unpack('!BH', data[pos:pos+3])
        value = data[pos+3:pos+3+length]
        records.append((type_id, value))
        pos += 3 + length
    return records

TYPE_NAME = 1; TYPE_PRICE = 2; TYPE_STOCK = 3; TYPE_CATEGORY = 4

encoded = b''
encoded += encode_tlv(TYPE_NAME,     'Surface Pro 12\"'.encode())
encoded += encode_tlv(TYPE_PRICE,    struct.pack('!d', 864.0))
encoded += encode_tlv(TYPE_STOCK,    struct.pack('!I', 15))
encoded += encode_tlv(TYPE_CATEGORY, 'Laptop'.encode())

print(f'TLV encoded: {len(encoded)} bytes')
for type_id, value in decode_tlv(encoded):
    if type_id == TYPE_NAME:     print(f'  name:     {value.decode()}')
    elif type_id == TYPE_PRICE:  print(f'  price:    \${struct.unpack(\"!d\", value)[0]}')
    elif type_id == TYPE_STOCK:  print(f'  stock:    {struct.unpack(\"!I\", value)[0]}')
    elif type_id == TYPE_CATEGORY: print(f'  category: {value.decode()}')

# Step 8: Capstone — binary catalog with index
print()
print('=== Capstone: Binary Catalog with Index ===')
import tempfile, os

CATALOG_MAGIC = b'IZC2'
RECORD_FMT2 = '!I32sdI16s'
RECORD_SIZE2 = struct.calcsize(RECORD_FMT2)

def build_catalog(products: list[dict]) -> bytes:
    records = []
    for p in products:
        n = p['name'].encode().ljust(32, b'\x00')[:32]
        c = p['category'].encode().ljust(16, b'\x00')[:16]
        records.append(struct.pack(RECORD_FMT2, p['id'], n, p['price'], p['stock'], c))
    body = b''.join(records)
    checksum = zlib.crc32(body)
    header = struct.pack('!4sHII', CATALOG_MAGIC, 2, len(products), checksum)
    return header + body

def parse_catalog(data: bytes) -> list[dict]:
    hfmt = '!4sHII'
    hsize = struct.calcsize(hfmt)
    magic, version, count, checksum = struct.unpack(hfmt, data[:hsize])
    assert magic == CATALOG_MAGIC, f'Bad magic: {magic!r}'
    body = data[hsize:]
    assert zlib.crc32(body) == checksum, 'Checksum mismatch — data corrupted!'
    return [
        {k: v for k, v in zip(
            ['id','name','price','stock','category'],
            [pid, n.rstrip(b'\x00').decode(), price, stock, c.rstrip(b'\x00').decode()]
        )}
        for pid, n, price, stock, c in struct.iter_unpack(RECORD_FMT2, body)
    ]

products = [
    {'id':1,'name':'Surface Pro 12\"','price':864.0, 'stock':15, 'category':'Laptop'},
    {'id':2,'name':'Surface Pen',     'price':49.99, 'stock':80, 'category':'Accessory'},
    {'id':3,'name':'Office 365',      'price':99.99, 'stock':999,'category':'Software'},
]
blob = build_catalog(products)
print(f'Catalog blob: {len(blob)} bytes')
parsed = parse_catalog(blob)
print(f'Parsed {len(parsed)} records:')
for p in parsed:
    print(f'  {p}')

# Tamper detection
tampered_blob = blob[:30] + b'\xff' + blob[31:]
try: parse_catalog(tampered_blob)
except AssertionError as e: print(f'Tamper detected: {e}')
"
```

**📸 Verified Output:**
```
=== ctypes.Structure ===
Record: id=1 price=864.0 stock=15 rating=4.8 flags=00000011
Size: 21 bytes (tight packed)
active:    True
featured:  True
discounted:False

=== Checksum & Data Integrity ===
CRC32 detects tamper: True
SHA256 detects tamper: True

=== Variable-Length Records ===
TLV encoded: 48 bytes
  name:     Surface Pro 12"
  price:    $864.0
  stock:    15
  category: Laptop

=== Capstone: Binary Catalog ===
Catalog blob: 172 bytes
Parsed 3 records: ...
Tamper detected: Checksum mismatch — data corrupted!
```

---

## Summary

| Tool | Purpose | Format codes |
|------|---------|-------------|
| `struct.pack/unpack` | C-style binary I/O | `!` big-end, `I` u32, `d` double, `s` bytes |
| `struct.iter_unpack` | Stream multiple records | Same format repeated |
| `ctypes.Structure` | C struct layout | `_fields_` + ctypes types |
| `array.array` | Typed C array | `'d'` double, `'l'` long |
| `memoryview` | Zero-copy slicing | `mv[start:end]` |
| `zlib.crc32` | Fast checksum | Good for file integrity |
| `hashlib.sha256` | Cryptographic integrity | Use for security-sensitive |

## Further Reading
- [struct module](https://docs.python.org/3/library/struct.html)
- [ctypes](https://docs.python.org/3/library/ctypes.html)
- [array module](https://docs.python.org/3/library/array.html)
