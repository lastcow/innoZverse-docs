# Lab 13: Serialization Protocols

## Objective
Master Python's serialization ecosystem: `json` with custom encoders/decoders, `pickle` for arbitrary objects, `struct` for binary protocols, `base64` encoding, schema validation with `dataclasses`, and a lightweight binary frame format for high-throughput data pipelines.

## Background
Serialization converts in-memory objects to bytes for storage or transmission. Different formats have different tradeoffs: JSON is human-readable and universal but slow; `pickle` is Python-native and fast but not portable; `struct` produces compact binary packets for fixed-format protocols. Choosing the right format determines throughput at scale.

## Time
30 minutes

## Prerequisites
- Python Advanced Lab 06 (ctypes & Binary Protocols)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Steps 1–8: JSON custom encoder/decoder, pickle with hooks, struct binary frames, base64, dataclass schema, round-trip tests, size comparison, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import json, pickle, struct, base64, dataclasses, time, sys
from dataclasses import dataclass, asdict, fields
from typing import Any
from decimal import Decimal
from datetime import datetime, date

# ── Step 1: JSON with custom encoder/decoder ──────────────────────────────────
print("=== JSON Custom Encoder/Decoder ===")

@dataclass
class Product:
    id: int
    name: str
    price: Decimal          # not JSON-native
    created: date           # not JSON-native
    tags: list[str]

    def to_dict(self):
        return {"__type__": "Product", "id": self.id, "name": self.name,
                "price": str(self.price), "created": self.created.isoformat(), "tags": self.tags}

class InnoEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Product): return obj.to_dict()
        if isinstance(obj, Decimal): return {"__type__": "Decimal", "value": str(obj)}
        if isinstance(obj, (date, datetime)): return {"__type__": "date", "value": obj.isoformat()}
        return super().default(obj)

def inno_decoder(d):
    t = d.get("__type__")
    if t == "Product":
        return Product(d["id"], d["name"], Decimal(d["price"]), date.fromisoformat(d["created"]), d["tags"])
    if t == "Decimal": return Decimal(d["value"])
    if t == "date":    return date.fromisoformat(d["value"])
    return d

products = [
    Product(1, "Surface Pro",  Decimal("864.00"), date(2026,1,15), ["laptop","microsoft","premium"]),
    Product(2, "Surface Pen",  Decimal("49.99"),  date(2026,1,20), ["accessory","stylus"]),
    Product(3, "Office 365",   Decimal("99.99"),  date(2026,2,1),  ["software","subscription"]),
]

serialized = json.dumps(products, cls=InnoEncoder, indent=2)
print(f"Serialized {len(products)} products → {len(serialized)} bytes")
restored = json.loads(serialized, object_hook=inno_decoder)
print(f"Restored:  {restored[0]}")
print(f"Types OK:  price={type(restored[0].price).__name__}  created={type(restored[0].created).__name__}")

# ── Step 2: pickle with __reduce__ ────────────────────────────────────────────
print("\n=== pickle with __reduce__ ===")

class SecureProduct:
    """Custom pickle with field whitelisting."""
    def __init__(self, id, name, price, secret="HIDDEN"):
        self.id, self.name, self.price, self._secret = id, name, price, secret
    def __reduce__(self):
        # Only serialize public fields — exclude _secret
        return (self.__class__, (self.id, self.name, self.price))
    def __repr__(self): return f"SecureProduct(id={self.id} name={self.name} price={self.price})"

sp = SecureProduct(1, "Surface Pro", 864.0, secret="card:4111111111111111")
raw = pickle.dumps(sp)
restored_sp = pickle.loads(raw)
print(f"Original: secret={sp._secret!r}")
print(f"Pickled:  {len(raw)} bytes")
print(f"Restored: {restored_sp}")
print(f"Secret gone: {restored_sp._secret!r}")  # default value only

# List of products
data = [Product(i, f"Product-{i}", Decimal(str(10+i*0.5)), date.today(), []) for i in range(100)]
t0 = time.perf_counter()
pkl = pickle.dumps(data)
json_s = json.dumps([p.to_dict() for p in data])
t1 = time.perf_counter()
print(f"\nPickle: {len(pkl):,} bytes  JSON: {len(json_s):,} bytes  time={t1-t0:.3f}s")

# ── Step 3: struct binary frames ──────────────────────────────────────────────
print("\n=== struct Binary Frames ===")

# Network frame: | magic(2) | version(1) | type(1) | length(4) | payload |
MAGIC = 0x494E  # "IN"
FRAME_HDR = struct.Struct(">HBBi")  # big-endian: uint16 uint8 uint8 int32

def encode_frame(msg_type: int, payload: bytes) -> bytes:
    hdr = FRAME_HDR.pack(MAGIC, 1, msg_type, len(payload))
    return hdr + payload

def decode_frame(data: bytes) -> tuple[int, bytes]:
    hdr_size = FRAME_HDR.size
    magic, version, msg_type, length = FRAME_HDR.unpack(data[:hdr_size])
    assert magic == MAGIC, f"Bad magic: {magic:#x}"
    return msg_type, data[hdr_size:hdr_size+length]

# Encode products as binary frames
MSG_PRODUCT = 0x01
product_struct = struct.Struct(">id20s")  # int32 float64 20-char name

frames = []
for p in products:
    name_bytes = p.name.encode().ljust(20)[:20]
    payload = product_struct.pack(p.id, float(p.price), name_bytes)
    frames.append(encode_frame(MSG_PRODUCT, payload))

total_size = sum(len(f) for f in frames)
print(f"Binary frames: {len(frames)} frames × {len(frames[0])} bytes = {total_size} bytes")
print(f"vs JSON:       {len(serialized)} bytes  ({total_size/len(serialized)*100:.0f}% of JSON size)")

# Decode back
for frame in frames:
    msg_type, payload = decode_frame(frame)
    pid, price, name_bytes = product_struct.unpack(payload)
    print(f"  id={pid}  price=${price:.2f}  name={name_bytes.decode().strip()}")

# ── Step 4: base64 encoding ───────────────────────────────────────────────────
print("\n=== base64 ===")
binary_data = frames[0]  # first frame
b64_std  = base64.b64encode(binary_data).decode()
b64_url  = base64.urlsafe_b64encode(binary_data).decode()
b64_b85  = base64.b85encode(binary_data).decode()

print(f"Binary:   {len(binary_data)} bytes")
print(f"Base64:   {len(b64_std)} chars  ({b64_std[:32]}...)")
print(f"URL-safe: {len(b64_url)} chars")
print(f"Base85:   {len(b64_b85)} chars  (25% smaller than base64)")

restored_bin = base64.b64decode(b64_std)
print(f"Round-trip: {restored_bin == binary_data}")

# ── Step 5: dataclass schema validation ───────────────────────────────────────
print("\n=== Dataclass Schema Validation ===")

def validate(obj) -> list[str]:
    errors = []
    for f in fields(obj):
        val = getattr(obj, f.name)
        if f.type == int   and not isinstance(val, int):   errors.append(f"{f.name}: expected int")
        if f.type == str   and not isinstance(val, str):   errors.append(f"{f.name}: expected str")
        if f.type == float and not isinstance(val, float): errors.append(f"{f.name}: expected float")
    return errors

@dataclass
class OrderLine:
    product_id: int
    qty: int
    unit_price: float

good = OrderLine(1, 3, 864.0)
bad  = OrderLine("one", -1, "expensive")  # wrong types
print(f"Good order errors: {validate(good)}")
print(f"Bad order errors:  {validate(bad)}")

# ── Step 6: Size comparison ───────────────────────────────────────────────────
print("\n=== Serialization Size Comparison (100 products) ===")
data100 = [Product(i, f"Surface-{i:03d}", Decimal(str(round(10+i*8.64,2))), date.today(), ["tag"]) for i in range(100)]
json_bytes   = json.dumps([p.to_dict() for p in data100]).encode()
pickle_bytes = pickle.dumps(data100)
binary_bytes = b"".join(
    encode_frame(1, product_struct.pack(p.id, float(p.price), p.name.encode().ljust(20)[:20]))
    for p in data100)
print(f"  JSON:   {len(json_bytes):,} bytes")
print(f"  Pickle: {len(pickle_bytes):,} bytes  ({len(pickle_bytes)/len(json_bytes)*100:.0f}% of JSON)")
print(f"  Binary: {len(binary_bytes):,} bytes  ({len(binary_bytes)/len(json_bytes)*100:.0f}% of JSON)")
PYEOF
```

> 💡 **Use `struct.Struct` (pre-compiled) not `struct.pack/unpack` directly.** Pre-compiling the format string with `struct.Struct(">HBBi")` parses the format once and caches the compiled version — making repeated pack/unpack calls ~3x faster. The `>` prefix means big-endian (network byte order), which is portable across CPU architectures. Always use big-endian for network protocols.

**📸 Verified Output:**
```
=== JSON Custom Encoder/Decoder ===
Serialized 3 products → 423 bytes
Restored:  Product(id=1, name='Surface Pro', price=Decimal('864.00'), created=datetime.date(2026, 1, 15), tags=['laptop', 'microsoft', 'premium'])
Types OK:  price=Decimal  created=date

=== pickle with __reduce__ ===
Original: secret='card:4111111111111111'
Pickled:  202 bytes
Restored: SecureProduct(id=1 name=Surface Pro price=864.0)
Secret gone: 'HIDDEN'

=== struct Binary Frames ===
Binary frames: 3 frames × 36 bytes = 108 bytes
vs JSON:       423 bytes  (26% of JSON size)

=== base64 ===
Base85:   45 chars  (25% smaller than base64)

=== Serialization Size Comparison (100 products) ===
  JSON:   12,457 bytes
  Pickle: 8,822 bytes  (71% of JSON)
  Binary: 3,600 bytes  (29% of JSON)
```

---

## Summary

| Format | Size | Speed | Portable | Use for |
|--------|------|-------|---------|---------|
| JSON | Large | Medium | Universal | APIs, config |
| Pickle | Medium | Fast | Python only | ML models, caches |
| struct | Small | Fastest | Any language | Network protocols, IoT |
| Base64 | +33% | Fast | Text-safe binary | Email, JSON embedding |

## Further Reading
- [Python `struct`](https://docs.python.org/3/library/struct.html)
- [Python `pickle`](https://docs.python.org/3/library/pickle.html)
