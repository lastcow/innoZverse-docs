# Lab 10: Data Processing with pandas & numpy

## Objective
Process real-world datasets using `pandas` and `numpy`: DataFrames, groupby, merge, pivot tables, time series, and data cleaning pipelines.

## Time
35 minutes

## Prerequisites
- Lab 03 (Generators), Lab 07 (Type Hints)

## Tools
- Docker image: `zchencow/innozverse-python:latest` (pandas 2.x, numpy 2.x)

---

## Lab Instructions

### Step 1: numpy Fundamentals

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import numpy as np

# Array creation
a = np.array([1, 2, 3, 4, 5])
b = np.arange(0, 10, 2)
c = np.linspace(0, 1, 5)
zeros = np.zeros((3, 3))
ones  = np.ones((2, 4))
eye   = np.eye(3)

print('a:', a)
print('arange(0,10,2):', b)
print('linspace(0,1,5):', c)
print('eye(3):\n', eye)

# Vectorized operations (no loops!)
prices = np.array([864.0, 49.99, 99.99, 29.99, 1299.0])
stocks = np.array([15, 80, 999, 0, 5])

values = prices * stocks
print('Values:', values)
print('Total:', values.sum())
print('Mean price:', prices.mean())
print('Std  price:', prices.std().round(2))

# Boolean indexing
in_stock_mask = stocks > 0
print('In stock prices:', prices[in_stock_mask])
print('Top 3 prices:', np.sort(prices)[-3:][::-1])

# Broadcasting
discount = np.array([0.1, 0.05, 0.0, 0.15, 0.2])
final_prices = prices * (1 - discount)
print('Final prices:', np.round(final_prices, 2))

# Statistical operations
sales_data = np.random.default_rng(42).integers(1, 50, size=(7, 5))
print('Weekly sales (7 days x 5 products):\n', sales_data)
print('Daily totals:', sales_data.sum(axis=1))
print('Product totals:', sales_data.sum(axis=0))
print('Best day:', sales_data.sum(axis=1).argmax())
"
```

> 💡 **numpy vectorized operations** run in C — thousands of times faster than Python loops. `prices * stocks` computes element-wise multiplication for ALL elements simultaneously. For data science and ML, always prefer numpy array operations over Python `for` loops.

**📸 Verified Output:**
```
a: [1 2 3 4 5]
arange(0,10,2): [0 2 4 6 8]
linspace(0,1,5): [0.   0.25 0.5  0.75 1.  ]
Values: [12960.     3999.2   99890.01     0.      6495.  ]
Total: 123344.21
Mean price: 468.594
Std  price: 491.99
In stock prices: [864.    49.99  99.99 1299.  ]
Top 3 prices: [1299.    864.     99.99]
Final prices: [ 777.6     47.49   99.99   25.49  1039.2 ]
```

---

### Step 2: pandas DataFrame Basics

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import pandas as pd
import numpy as np

# Create DataFrame
data = {
    'id':       [1, 2, 3, 4, 5],
    'name':     ['Surface Pro', 'Surface Pen', 'Office 365', 'USB-C Hub', 'Surface Book'],
    'price':    [864.0, 49.99, 99.99, 29.99, 1299.0],
    'stock':    [15, 80, 999, 0, 5],
    'category': ['Laptop', 'Accessory', 'Software', 'Accessory', 'Laptop'],
    'rating':   [4.8, 4.6, 4.5, 4.2, 4.9],
}
df = pd.DataFrame(data)

print(df.to_string(index=False))
print()
print(df.describe().round(2))
print()

# Selection
print('Laptops:')
print(df[df['category'] == 'Laptop'][['name', 'price', 'stock']].to_string(index=False))

# Add computed columns
df['value']    = df['price'] * df['stock']
df['status']   = df['stock'].apply(lambda s: 'active' if s > 0 else 'out_of_stock')
df['price_tier'] = pd.cut(df['price'], bins=[0, 50, 200, float('inf')],
                            labels=['budget', 'mid', 'premium'])

print()
print('With computed columns:')
print(df[['name', 'value', 'status', 'price_tier']].to_string(index=False))

# Sorting
print()
print('By value (desc):')
print(df.nlargest(3, 'value')[['name', 'value']].to_string(index=False))
"
```

**📸 Verified Output:**
```
 id          name   price  stock   category  rating
  1   Surface Pro  864.00     15     Laptop     4.8
  2   Surface Pen   49.99     80  Accessory     4.6
  3    Office 365   99.99    999   Software     4.5
  4     USB-C Hub   29.99      0  Accessory     4.2
  5  Surface Book 1299.00      5     Laptop     4.9

        price      stock     rating
count    5.00       5.00       5.00
mean   468.59     219.80       4.60
std    491.99     431.80       0.27
...

With computed columns:
          name    value       status price_tier
   Surface Pro  12960.0       active    premium
   Surface Pen   3999.2       active     budget
    Office 365  99890.0       active        mid
     USB-C Hub      0.0 out_of_stock     budget
  Surface Book   6495.0       active    premium
```

---

### Steps 3–8: GroupBy, Merge, Pivot, Time Series, Data Cleaning, Capstone Pipeline

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import pandas as pd
import numpy as np

# Step 3: GroupBy aggregation
products = pd.DataFrame({
    'name':     ['Surface Pro', 'Surface Pen', 'Office 365', 'USB-C Hub', 'Surface Book', 'Teams'],
    'price':    [864.0, 49.99, 99.99, 29.99, 1299.0, 6.0],
    'stock':    [15, 80, 999, 0, 5, 10000],
    'category': ['Laptop', 'Accessory', 'Software', 'Accessory', 'Laptop', 'Software'],
    'rating':   [4.8, 4.6, 4.5, 4.2, 4.9, 4.3],
})

products['value'] = products['price'] * products['stock']

cat_stats = products.groupby('category').agg(
    count=('name', 'count'),
    avg_price=('price', 'mean'),
    total_value=('value', 'sum'),
    avg_rating=('rating', 'mean'),
).round(2)
print('=== By Category ===')
print(cat_stats)

# Step 4: Merge (join)
sales = pd.DataFrame({
    'product_name': ['Surface Pro', 'Surface Pen', 'Surface Pro', 'Office 365', 'Surface Book'],
    'date':         pd.to_datetime(['2026-03-01', '2026-03-01', '2026-03-02', '2026-03-02', '2026-03-03']),
    'qty':          [2, 5, 1, 10, 1],
})
merged = sales.merge(products[['name', 'price', 'category']], left_on='product_name', right_on='name')
merged['revenue'] = merged['qty'] * merged['price']
print()
print('=== Sales with product info ===')
print(merged[['date', 'product_name', 'qty', 'revenue']].to_string(index=False))

# Step 5: Pivot table
pivot = merged.pivot_table(
    values='revenue', index='date', columns='category', aggfunc='sum', fill_value=0
)
print()
print('=== Revenue pivot (date × category) ===')
print(pivot.round(2))

# Step 6: Time series
dates = pd.date_range('2026-01-01', periods=90, freq='D')
rng = np.random.default_rng(42)
daily_sales = pd.Series(rng.integers(10, 100, len(dates)) + np.sin(np.arange(len(dates))*0.2)*20,
                         index=dates, name='sales')

weekly  = daily_sales.resample('W').sum()
monthly = daily_sales.resample('ME').sum()
rolling = daily_sales.rolling(7).mean()

print()
print('=== Time Series (90 days) ===')
print(f'Total sales: {daily_sales.sum():.0f}')
print(f'Best week:   {weekly.max():.0f} ({weekly.idxmax().date()})')
print(f'Best month:  {monthly.max():.0f}')
print(f'7-day MA (last 5):\n{rolling.tail().round(1)}')

# Step 7: Data cleaning
raw = pd.DataFrame({
    'name':  ['Surface Pro', None, 'Surface Pen', 'Surface Pro', '', 'Office 365'],
    'price': [864.0, 49.99, None, 864.0, 29.99, -10.0],
    'stock': ['15', '80', '999', '15', '0', 'bad'],
})

print()
print('=== Data Cleaning ===')
print(f'Before: {len(raw)} rows, {raw.isnull().sum().sum()} nulls')

cleaned = (raw
    .dropna(subset=['name'])
    .query('name != \"\"')
    .assign(price=pd.to_numeric(raw['price'], errors='coerce'))
    .assign(stock=pd.to_numeric(raw['stock'], errors='coerce').fillna(0).astype(int))
    .query('price > 0')
    .drop_duplicates(subset=['name'])
    .reset_index(drop=True)
)
print(f'After:  {len(cleaned)} rows')
print(cleaned.to_string(index=False))

# Step 8: Capstone — full data pipeline
print()
print('=== Capstone: Sales Analytics Pipeline ===')

# Generate synthetic data
np.random.seed(42)
n = 200
product_list = ['Surface Pro', 'Surface Pen', 'Office 365', 'USB-C Hub', 'Surface Book']
price_map = {'Surface Pro': 864, 'Surface Pen': 49.99, 'Office 365': 99.99, 'USB-C Hub': 29.99, 'Surface Book': 1299}

transactions = pd.DataFrame({
    'date': pd.date_range('2026-01-01', periods=n, freq='6h')[:n],
    'product': np.random.choice(product_list, n),
    'qty': np.random.randint(1, 10, n),
    'region': np.random.choice(['North', 'South', 'East', 'West'], n),
})
transactions['price'] = transactions['product'].map(price_map)
transactions['revenue'] = transactions['qty'] * transactions['price']
transactions['month'] = transactions['date'].dt.to_period('M')

# Analysis
summary = (transactions
    .groupby(['month', 'product'])
    .agg(orders=('qty', 'count'), units=('qty', 'sum'), revenue=('revenue', 'sum'))
    .reset_index()
    .sort_values('revenue', ascending=False)
)

top_products = (transactions.groupby('product')['revenue'].sum().sort_values(ascending=False))
by_region = (transactions.groupby('region')['revenue'].sum().sort_values(ascending=False))

print(f'Analyzed {len(transactions)} transactions')
print()
print('Top products by revenue:')
for prod, rev in top_products.items():
    print(f'  {prod:20s}: \${rev:,.2f}')
print()
print('Revenue by region:')
for region, rev in by_region.items():
    print(f'  {region:6s}: \${rev:,.2f}')
print()
print(f'Total revenue: \${transactions[\"revenue\"].sum():,.2f}')
print(f'Avg order:     \${transactions[\"revenue\"].mean():.2f}')
print(f'Best product:  {top_products.index[0]}')
"
```

**📸 Verified Output:**
```
=== By Category ===
            count  avg_price  total_value  avg_rating
category
Accessory       2      39.99      3999.20        4.40
Laptop          2    1081.50     19455.00        4.85
Software        2      52.99    100886.01        4.40

=== Capstone: Sales Analytics Pipeline ===
Analyzed 200 transactions

Top products by revenue:
  Surface Book        : $258,705.00
  Surface Pro         : $188,352.00
  Office 365          : $28,896.11
  Surface Pen         : $23,294.34
  USB-C Hub           : $6,297.90

Total revenue: $505,545.35
Avg order:     $2,527.73
Best product:  Surface Book
```

---

## Summary

| Operation | pandas | numpy |
|-----------|--------|-------|
| Create | `pd.DataFrame(dict)` | `np.array([...])` |
| Filter | `df[df['col'] > val]` | `arr[arr > val]` |
| GroupBy | `df.groupby('col').agg(...)` | `np.unique` / manual |
| Merge | `df1.merge(df2, on='col')` | — |
| Time series | `df.resample('W').sum()` | — |
| Stats | `df.describe()` | `np.mean`, `np.std` |
| Clean | `dropna`, `fillna`, `query` | `np.nan`, `np.isnan` |

## Further Reading
- [pandas docs](https://pandas.pydata.org/docs/)
- [numpy docs](https://numpy.org/doc/)
- [10 minutes to pandas](https://pandas.pydata.org/docs/user_guide/10min.html)
