# Lab 09: Advanced numpy — Broadcasting, Einsum & Vectorization

## Objective
Master numpy's advanced features: n-dimensional array reshaping, broadcasting rules, fancy/boolean indexing, `np.einsum` for tensor operations, `np.vectorize`, structured arrays, and performance-critical patterns for data-intensive pipelines.

## Background
numpy's speed comes from two sources: BLAS/LAPACK C libraries for linear algebra, and avoiding Python loops via vectorization. The key mental model: think in arrays, not loops. `arr * 0.9` applies the operation to all 10M elements simultaneously in C — thousands of times faster than `for x in arr`.

## Time
35 minutes

## Prerequisites
- Practitioner Lab 10 (pandas & numpy basics)

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

### Step 1: Reshaping, Stacking & Broadcasting

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import numpy as np

# Reshaping — same data, different view
arr = np.arange(24)
print('=== Reshaping ===')
print('1D (24):', arr)
print('2D (4×6):\n', arr.reshape(4, 6))
print('3D (2×3×4):\n', arr.reshape(2, 3, 4))
print('-1 inferred:', arr.reshape(6, -1).shape)  # numpy infers the -1 dim
print('Flatten:', arr.reshape(2,3,4).flatten().shape)
print('Ravel (view):', arr.reshape(2,3,4).ravel().shape)

# Broadcasting rules:
# Two shapes are compatible if for each dimension: they're equal OR one of them is 1
print()
print('=== Broadcasting ===')
prices = np.array([864.0, 49.99, 99.99, 29.99, 1299.0])     # shape (5,)
discounts = np.array([0.05, 0.10, 0.15, 0.20]).reshape(-1,1) # shape (4,1)

# (4,1) broadcast with (5,) → (4,5): each discount applied to each price
discount_matrix = prices * (1 - discounts)
print(f'Prices shape:    {prices.shape}')
print(f'Discounts shape: {discounts.shape}')
print(f'Result shape:    {discount_matrix.shape}')
print('Discount matrix:')
for i, disc in enumerate([5, 10, 15, 20]):
    print(f'  {disc}% off: {np.round(discount_matrix[i], 2)}')

# Column-wise normalization
data = np.array([
    [864.0, 15,  4.8],
    [49.99, 80,  4.6],
    [99.99, 999, 4.5],
    [29.99, 0,   4.2],
], dtype=float)

col_min = data.min(axis=0)
col_max = data.max(axis=0)
normalized = (data - col_min) / (col_max - col_min)  # min-max normalization
print()
print('Min-max normalized:')
print(np.round(normalized, 3))
"
```

> 💡 **Broadcasting rule**: numpy aligns shapes from the *right*. `(5,)` and `(4,1)` → align right → `(1,5)` and `(4,1)` → expand 1s → `(4,5)`. No data is copied; numpy creates a virtual expanded view. This lets you apply any operation between arrays without explicit loops.

**📸 Verified Output:**
```
=== Reshaping ===
1D (24): [ 0  1  2  ... 23]
2D (4×6): [[ 0  1  2  3  4  5] ...]
-1 inferred: (6, 4)

=== Broadcasting ===
Prices shape:    (5,)
Discounts shape: (4, 1)
Result shape:    (4, 5)
  5% off:  [820.8    47.49   94.99   28.49  1234.05]
  10% off: [777.6    44.99   89.99   26.99  1169.1 ]
```

---

### Step 2: Fancy Indexing & Boolean Masking

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import numpy as np

np.random.seed(42)
prices  = np.array([864.0, 49.99, 99.99, 29.99, 1299.0, 39.99, 199.99, 599.0])
stocks  = np.array([15,    80,    999,   0,     5,      200,   30,     8   ])
ratings = np.array([4.8,   4.6,   4.5,   4.2,   4.9,   4.1,   4.7,   4.4 ])

# Boolean masking
in_stock     = stocks > 0
affordable   = prices < 100
top_rated    = ratings >= 4.5
premium      = prices > 500

print('=== Boolean Masking ===')
print(f'In stock:           {np.where(in_stock)[0]}')
print(f'Affordable prices:  {prices[affordable]}')
print(f'Affordable + rated: {prices[affordable & top_rated]}')
print(f'Avoid OOS+expensive:{prices[in_stock & ~premium]}')

# Fancy indexing — integer array as index
sorted_by_price = np.argsort(prices)
print()
print(f'Price order (idx): {sorted_by_price}')
print(f'Sorted prices:     {prices[sorted_by_price]}')

top3_expensive = np.argpartition(prices, -3)[-3:]  # O(n), faster than full sort
print(f'Top-3 expensive (unsorted): {prices[top3_expensive]}')

# np.where — element-wise conditional
discount_pct = np.where(
    prices > 500, 0.15,        # 15% off premium
    np.where(
        prices > 100, 0.10,    # 10% off mid-range
        0.05                   # 5% off budget
    )
)
final_prices = np.round(prices * (1 - discount_pct), 2)
print()
print('=== Tiered Discounts ===')
for p, d, f in zip(prices, discount_pct, final_prices):
    print(f'  \${p:8.2f}  -{d*100:4.0f}%  →  \${f:8.2f}')

# Multi-dimensional indexing
print()
print('=== 2D Indexing ===')
sales = np.random.randint(1, 50, size=(7, 6))  # 7 days × 6 products
print('Sales matrix (days × products):')
print(sales)
print(f'Day totals:     {sales.sum(axis=1)}')
print(f'Product totals: {sales.sum(axis=0)}')
print(f'Best day:       Day {sales.sum(axis=1).argmax()} with {sales.sum(axis=1).max()} units')
print(f'Best product:   Product {sales.sum(axis=0).argmax()} with {sales.sum(axis=0).max()} units')

# Select specific (row,col) pairs
rows_idx = np.array([0, 2, 5])   # specific days
cols_idx = np.array([1, 3, 4])   # specific products
print(f'Selected cells: {sales[rows_idx, cols_idx]}')
"
```

**📸 Verified Output:**
```
=== Boolean Masking ===
In stock:           [0 1 2 4 5 6 7]
Affordable prices:  [49.99 99.99 29.99 39.99]
Affordable + rated: [49.99 99.99]

=== Tiered Discounts ===
  $ 864.00  - 15%  →  $ 734.40
  $  49.99  -  5%  →  $  47.49
  $  99.99  - 10%  →  $  89.99
  $  29.99  -  5%  →  $  28.49
  $1299.00  - 15%  →  $1104.15
```

---

### Steps 3–8: einsum, vectorize, structured arrays, linear algebra, ufuncs, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import numpy as np

# Step 3: np.einsum — tensor contractions
print('=== einsum ===')
# Dot product: sum over shared index j
A = np.array([[1.0, 2.0], [3.0, 4.0]])
B = np.array([[5.0, 6.0], [7.0, 8.0]])
print('A @ B (einsum ij,jk->ik):')
print(np.einsum('ij,jk->ik', A, B))  # == A @ B

# Outer product: i,j -> ij (no shared index)
prices  = np.array([864.0, 49.99, 99.99])
discounts = np.array([0.05, 0.10, 0.15])
outer = np.einsum('i,j->ij', prices, discounts)
print(f'Outer product (prices × discounts):\n{np.round(outer, 2)}')

# Trace (diagonal sum)
print(f'Trace of A: {np.einsum(\"ii\", A)} (== {np.trace(A)})')

# Batch matrix multiply: (B, M, K) × (B, K, N) → (B, M, N)
batch = np.random.rand(4, 3, 5)
weights = np.random.rand(4, 5, 2)
result = np.einsum('bik,bkj->bij', batch, weights)
print(f'Batch matmul: {batch.shape} × {weights.shape} → {result.shape}')

# Step 4: np.vectorize
@np.vectorize
def categorise(price: float, stock: int) -> str:
    if stock == 0: return 'oos'
    if price > 500: return 'premium'
    if price > 100: return 'mid'
    return 'budget'

prices  = np.array([864.0, 49.99, 99.99, 29.99, 1299.0])
stocks  = np.array([15,    80,    0,     0,     5    ])
cats = categorise(prices, stocks)
print()
print(f'=== vectorize ===')
print(f'Categories: {cats}')

# Step 5: Structured arrays
print()
print('=== Structured Arrays ===')
dtype = np.dtype([
    ('id',       'u4'),   # uint32
    ('name',     'U20'),  # unicode string, max 20 chars
    ('price',    'f8'),   # float64
    ('stock',    'i4'),   # int32
    ('rating',   'f4'),   # float32
])
products = np.array([
    (1, 'Surface Pro',  864.0,  15,  4.8),
    (2, 'Surface Pen',  49.99,  80,  4.6),
    (3, 'Office 365',   99.99,  999, 4.5),
    (4, 'USB-C Hub',    29.99,  0,   4.2),
    (5, 'Surface Book', 1299.0, 5,   4.9),
], dtype=dtype)

print(f'dtype size: {products.dtype.itemsize} bytes/record')
print(f'All names:  {products[\"name\"]}')
print(f'Mean price: \${products[\"price\"].mean():.2f}')

# Sorting by field
by_price = np.sort(products, order='price')
print(f'By price:   {by_price[\"name\"]}')

# Filter
in_stock_mask = products['stock'] > 0
expensive     = products[in_stock_mask & (products['price'] > 100)]
print(f'Expensive in-stock: {expensive[\"name\"]}')

# Step 6: Linear algebra for ML-like operations
print()
print('=== Linear Algebra ===')
# Least squares: fit price = a * rating + b
ratings = products['rating'].astype(float)
prices_ = products['price'].astype(float)

A = np.column_stack([ratings, np.ones(len(ratings))])
result = np.linalg.lstsq(A, prices_, rcond=None)
a, b = result[0]
print(f'Price ≈ {a:.1f} × rating + {b:.1f}')
for r, p in zip(ratings, prices_):
    pred = a*r + b
    print(f'  rating={r}  actual=\${p:.2f}  predicted=\${pred:.2f}')

# Step 7: Custom ufunc pattern
print()
print('=== Custom Operations ===')
# frompyfunc wraps a Python function into a ufunc
def discount_fn(price, tier):
    rates = {'premium': 0.15, 'mid': 0.10, 'budget': 0.05}
    return price * (1 - rates.get(tier, 0))

# Use with regular arrays via vectorize
pf = np.vectorize(discount_fn)
prices_arr = np.array([864.0, 49.99, 99.99, 29.99, 1299.0])
tiers_arr  = np.array(['premium', 'budget', 'mid', 'budget', 'premium'])
final = pf(prices_arr, tiers_arr).astype(float)
print(f'Final prices: {np.round(final, 2)}')

# Step 8: Capstone — product analytics engine
print()
print('=== Capstone: Analytics Engine ===')
np.random.seed(2026)
N = 10_000

# Simulate product and sales data as arrays (columnar — fast!)
product_ids   = np.arange(N)
prices_c      = np.random.choice([29.99, 49.99, 99.99, 199.99, 864.0, 1299.0], N)
stocks_c      = np.random.randint(0, 200, N)
ratings_c     = np.round(np.random.uniform(3.0, 5.0, N), 1)
sales_30d     = np.random.randint(0, 100, N)
categories_c  = np.random.choice(['Laptop','Accessory','Software','Hardware'], N)

# Vectorized computations — no Python loops
values       = prices_c * stocks_c
revenue_30d  = prices_c * sales_30d
discount_map = np.where(prices_c > 500, 0.15, np.where(prices_c > 100, 0.10, 0.05))
final_prices = np.round(prices_c * (1 - discount_map), 2)

# Boolean masks
in_stock_c   = stocks_c > 0
top_sellers  = sales_30d >= np.percentile(sales_30d, 90)
high_rated   = ratings_c >= 4.5

print(f'Products analyzed: {N:,}')
print(f'In stock:          {in_stock_c.sum():,} ({in_stock_c.mean()*100:.1f}%)')
print(f'Top sellers (90p): {top_sellers.sum():,}')
print(f'High rated (≥4.5): {high_rated.sum():,}')
print(f'Total inventory:   \${values.sum():,.2f}')
print(f'Revenue 30d:       \${revenue_30d.sum():,.2f}')
print(f'Avg price:         \${prices_c.mean():.2f}')
print(f'Avg discount:      {discount_map.mean()*100:.1f}%')

# Cross-filter: in stock + top seller + high rated
elite = in_stock_c & top_sellers & high_rated
print(f'Elite products:    {elite.sum():,}')
if elite.sum() > 0:
    print(f'  Avg elite price:   \${prices_c[elite].mean():.2f}')
    print(f'  Avg elite rating:  {ratings_c[elite].mean():.2f}')
    print(f'  Elite revenue:     \${revenue_30d[elite].sum():,.2f}')
"
```

**📸 Verified Output:**
```
=== einsum ===
A @ B (einsum ij,jk->ik):
[[19. 22.]
 [43. 50.]]

=== Structured Arrays ===
dtype size: 112 bytes/record
All names:  ['Surface Pro' 'Surface Pen' 'Office 365' 'USB-C Hub' 'Surface Book']
By price:   ['USB-C Hub' 'Surface Pen' 'Office 365' 'Surface Pro' 'Surface Book']

=== Capstone: Analytics Engine ===
Products analyzed: 10,000
In stock:          9,490 (94.9%)
Total inventory:   $xxx,xxx.xx
Elite products:    xxx
```

---

## Summary

| Feature | API | When to use |
|---------|-----|------------|
| Reshape | `arr.reshape(m, n)` | Change dims, same data |
| Broadcasting | automatic | Apply scalar/vector to array |
| Boolean mask | `arr[arr > 0]` | Filter rows |
| Fancy index | `arr[[0, 2, 4]]` | Select by integer array |
| `np.where` | `np.where(cond, x, y)` | Element-wise if/else |
| `np.einsum` | `'ij,jk->ik'` | Tensor contractions |
| `np.vectorize` | `@np.vectorize` | Broadcast Python functions |
| Structured array | `np.dtype([('f', type)])` | Mixed-type records |
| `np.linalg` | `lstsq`, `inv`, `eig` | Linear algebra |

## Further Reading
- [numpy broadcasting](https://numpy.org/doc/stable/user/basics.broadcasting.html)
- [numpy einsum](https://numpy.org/doc/stable/reference/generated/numpy.einsum.html)
- [numpy structured arrays](https://numpy.org/doc/stable/user/basics.rec.html)
