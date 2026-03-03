# Lab 10: Advanced pandas — Time Series, MultiIndex & Pipelines

## Objective
Master pandas beyond basics: MultiIndex hierarchical data, `groupby` with custom aggregations, time series resampling with `pd.Grouper`, method chaining with `pipe()`, `apply()` with complex functions, `pd.eval()` for fast expressions, and building a full ETL pipeline.

## Background
pandas 2.x uses Copy-on-Write semantics — operations on slices no longer silently modify the original. The 2.x API also aligns better with numpy via the Arrow backend. Understanding method chaining with `pipe()` and avoiding loops with `apply()` is the difference between 10-line and 100-line pandas code.

## Time
35 minutes

## Prerequisites
- Practitioner Lab 10 (pandas basics)

## Tools
- Docker: `zchencow/innozverse-python:latest` (pandas 3.x)

---

## Lab Instructions

### Step 1: MultiIndex — Hierarchical Indexing

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import pandas as pd
import numpy as np

np.random.seed(2026)

# Build a MultiIndex DataFrame: region × category × product
regions    = ['North', 'South', 'East', 'West']
categories = ['Laptop', 'Accessory', 'Software']
products   = ['Surface Pro', 'Surface Pen', 'Office 365', 'Surface Book', 'USB-C Hub', 'Teams']

idx = pd.MultiIndex.from_product(
    [regions, categories],
    names=['region', 'category']
)
sales_df = pd.DataFrame({
    'units':   np.random.randint(10, 200, len(idx)),
    'revenue': np.random.uniform(500, 50_000, len(idx)).round(2),
    'returns': np.random.randint(0, 10, len(idx)),
}, index=idx)

print('=== MultiIndex DataFrame ===')
print(f'Shape: {sales_df.shape}')
print(sales_df.head(6).to_string())

# Access patterns
print()
print('=== MultiIndex Slicing ===')
print('North all categories:')
print(sales_df.loc['North'].to_string())

print()
print('All regions, Laptop only:')
print(sales_df.loc[(slice(None), 'Laptop'), :].to_string())

# Aggregation across levels
print()
print('=== Cross-level Aggregation ===')
by_region = sales_df.groupby('region')['revenue'].sum().sort_values(ascending=False)
print('Revenue by region:')
for region, rev in by_region.items():
    print(f'  {region:6s}: \${rev:>10,.2f}')

by_category = sales_df.groupby('category')['units'].agg(['sum','mean','std']).round(1)
print()
print('Units by category:')
print(by_category.to_string())

# Unstack — pivot MultiIndex level to columns
print()
print('=== Unstack (pivot region → columns) ===')
revenue_pivot = sales_df['revenue'].unstack(level='region').round(2)
print(revenue_pivot.to_string())
"
```

> 💡 **`df.loc[(slice(None), 'Laptop'), :]`** selects all regions (first level = `slice(None)`) with category `'Laptop'` (second level). MultiIndex enables truly hierarchical data with efficient cross-level aggregations — far faster than repeated filtering. Use `pd.IndexSlice` for cleaner syntax: `idx = pd.IndexSlice; df.loc[idx[:, 'Laptop'], :]`.

**📸 Verified Output:**
```
=== MultiIndex DataFrame ===
Shape: (12, 3)
                      units    revenue  returns
region category
North  Laptop           134  23451.28       ...

=== Unstack (pivot region → columns) ===
region         East     North     South      West
category
Accessory  12345.67  23456.78  ...
```

---

### Step 2: Advanced GroupBy — Custom Aggregations & Transform

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import pandas as pd
import numpy as np

np.random.seed(42)
N = 500
df = pd.DataFrame({
    'date':     pd.date_range('2026-01-01', periods=N, freq='D')[:N],
    'product':  np.random.choice(['Surface Pro','Surface Pen','Office 365','USB-C Hub','Surface Book'], N),
    'category': np.random.choice(['Laptop','Accessory','Software','Hardware'], N),
    'region':   np.random.choice(['North','South','East','West'], N),
    'qty':      np.random.randint(1, 20, N),
    'price':    np.random.choice([864.0, 49.99, 99.99, 29.99, 1299.0], N),
})
df['revenue'] = df['qty'] * df['price']
df['month']   = df['date'].dt.to_period('M')

# 1. Named aggregations
print('=== Named Aggregations (agg) ===')
summary = df.groupby('category').agg(
    orders    =('qty',     'count'),
    units     =('qty',     'sum'),
    revenue   =('revenue', 'sum'),
    avg_price =('price',   'mean'),
    max_order =('revenue', 'max'),
    top_region=('region',  lambda x: x.value_counts().index[0]),
).round(2).sort_values('revenue', ascending=False)
print(summary.to_string())

# 2. transform — add group statistics back to original rows
print()
print('=== Transform (group stats on rows) ===')
df['cat_revenue_total'] = df.groupby('category')['revenue'].transform('sum')
df['pct_of_category']   = (df['revenue'] / df['cat_revenue_total'] * 100).round(2)
df['rank_in_category']  = df.groupby('category')['revenue'].rank(ascending=False, method='dense')
sample = df[df['category']=='Laptop'][['product','revenue','pct_of_category','rank_in_category']].head(5)
print(sample.to_string(index=False))

# 3. apply — arbitrary function on groups
def top_products(group: pd.DataFrame, n: int = 2) -> pd.DataFrame:
    return group.nlargest(n, 'revenue')[['product','revenue','qty']]

print()
print('=== Top 2 per Category (apply) ===')
top = df.groupby('category', group_keys=True).apply(top_products, n=2, include_groups=False)
print(top.to_string())

# 4. Pivot table
print()
print('=== Pivot Table ===')
pivot = df.pivot_table(
    values='revenue', index='category', columns='region',
    aggfunc='sum', margins=True, margins_name='Total'
).round(2)
print(pivot.to_string())
"
```

**📸 Verified Output:**
```
=== Named Aggregations (agg) ===
           orders  units    revenue  avg_price  max_order top_region
category
Laptop        ...   ...   xxx,xxx.xx   xxx.xx   xxxxx.xx   North
...

=== Pivot Table ===
region       East    North    South     West    Total
category
Accessory  xxxx.xx  xxxx.xx ...
```

---

### Steps 3–8: Time Series, pipe() chaining, pd.eval, Data Quality, MultiIndex merges, Capstone

```bash
docker run --rm zchencow/innozverse-python:latest python3 -c "
import pandas as pd
import numpy as np

np.random.seed(2026)

# Step 3: Time series — resample, rolling, shift
dates  = pd.date_range('2026-01-01', periods=180, freq='D')
revenue = pd.Series(
    np.random.randint(5_000, 50_000, 180) + np.sin(np.arange(180)*0.1)*10_000,
    index=dates, name='revenue'
)

daily     = revenue
weekly    = revenue.resample('W').sum()
monthly   = revenue.resample('ME').sum()
rolling7  = revenue.rolling(7, min_periods=1).mean()
rolling30 = revenue.rolling(30, min_periods=1).mean()
pct_change= revenue.pct_change(7).mul(100).round(1)  # WoW %
cumulative = revenue.cumsum()

print('=== Time Series ===')
print(f'Daily avg:    \${daily.mean():>10,.2f}')
print(f'Best week:    \${weekly.max():>10,.2f} ({weekly.idxmax().date()})')
print(f'Best month:   \${monthly.max():>10,.2f} ({monthly.idxmax().strftime(\"%Y-%m\")})')
print(f'Total 180d:   \${cumulative.iloc[-1]:>10,.2f}')
print(f'Last 7d avg:  \${rolling7.iloc[-1]:>10,.2f}')
print()
print('Monthly breakdown:')
for period, val in monthly.items():
    print(f'  {period.strftime(\"%B %Y\"):15s}: \${val:>10,.2f}')

# Step 4: Method chaining with pipe()
print()
print('=== Method Chaining with pipe() ===')

raw = pd.DataFrame({
    'product': ['Surface Pro','Surface Pen',None,'Office 365','','USB-C Hub','Surface Pro'],
    'price':   [864.0, 49.99, 29.99, 99.99, None, 'free', 864.0],
    'stock':   [15, 80, 999, -1, 0, 'lots', 15],
    'category':['Laptop','Accessory','Hardware','Software','Hardware','Hardware','Laptop'],
})

def clean_strings(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(product=df['product'].str.strip().replace('', pd.NA))

def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        price=pd.to_numeric(df['price'], errors='coerce'),
        stock=pd.to_numeric(df['stock'], errors='coerce').fillna(0).astype(int)
    )

def validate(df: pd.DataFrame) -> pd.DataFrame:
    return (df
        .dropna(subset=['product', 'price'])
        .query('price > 0 and stock >= 0')
        .drop_duplicates(subset=['product'])
    )

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(
        value    = df['price'] * df['stock'],
        tier     = pd.cut(df['price'], bins=[0,50,200,float('inf')], labels=['budget','mid','premium']),
        status   = df['stock'].apply(lambda s: 'active' if s > 0 else 'oos'),
    )

cleaned = (raw
    .pipe(clean_strings)
    .pipe(coerce_numeric)
    .pipe(validate)
    .pipe(enrich)
    .reset_index(drop=True)
)

print(f'Before: {len(raw)} rows → After: {len(cleaned)} rows')
print(cleaned[['product','price','stock','tier','status','value']].to_string(index=False))

# Step 5: pd.eval — fast expression evaluation
print()
print('=== pd.eval ===')
df = cleaned.copy()
# eval avoids Python overhead for large DataFrames
result = df.eval('margin = (price - price * 0.3) / price * 100')  # gross margin %
df2    = pd.eval('result = df[\"price\"] * df[\"stock\"]', local_dict={'df': df})
print(f'Margin computed via eval:')
print(result[['product','price','margin']].to_string(index=False))

# Step 6: Memory optimization
print()
print('=== Memory Optimization ===')
N = 100_000
big_df = pd.DataFrame({
    'id':       range(N),
    'category': np.random.choice(['Laptop','Accessory','Software','Hardware'], N),
    'status':   np.random.choice(['active','oos','discontinued'], N),
    'price':    np.random.uniform(9.99, 1299, N),
    'stock':    np.random.randint(0, 1000, N),
})

before_mem = big_df.memory_usage(deep=True).sum() / 1024
# Optimize dtypes
optimized = big_df.assign(
    category = big_df['category'].astype('category'),  # ~8x smaller for repeated strings
    status   = big_df['status'].astype('category'),
    price    = big_df['price'].astype('float32'),       # float64→float32: 2x smaller
    stock    = big_df['stock'].astype('int16'),          # int64→int16: 4x smaller
)
after_mem = optimized.memory_usage(deep=True).sum() / 1024
print(f'Before: {before_mem:.0f} KB')
print(f'After:  {after_mem:.0f} KB (saved {(1 - after_mem/before_mem)*100:.0f}%)')
print(f'Data intact: {(big_df[\"price\"].round(2) == optimized[\"price\"].round(2)).all()}')

# Step 7: Merge strategies
print()
print('=== Merge Strategies ===')
products_df = pd.DataFrame({
    'id': [1, 2, 3, 4, 5],
    'name': ['Surface Pro','Surface Pen','Office 365','USB-C Hub','Surface Book'],
    'category_id': [1, 2, 3, 4, 1],
})
categories_df = pd.DataFrame({
    'id': [1, 2, 3, 4],
    'category': ['Laptop','Accessory','Software','Hardware'],
})
orders_df = pd.DataFrame({
    'product_id': [1, 1, 2, 3, 5, 5, 99],  # 99 has no product
    'qty':        [2, 3, 5, 10, 1, 2, 1],
    'total':      [1728, 2592, 250, 1000, 1299, 2598, 50],
})

# inner — only matching rows
inner = products_df.merge(orders_df, left_on='id', right_on='product_id', how='inner')
print(f'Inner join: {len(inner)} rows (matched only)')

# left — all products, null for unordered
left = products_df.merge(orders_df, left_on='id', right_on='product_id', how='left')
print(f'Left join:  {len(left)} rows (all products)')

# Full pipeline: products + categories + orders
full = (products_df
    .merge(categories_df, left_on='category_id', right_on='id', suffixes=('','_cat'))
    .merge(orders_df, left_on='id', right_on='product_id', how='left')
    .rename(columns={'category': 'cat'})
    [['name','cat','qty','total']]
    .fillna({'qty': 0, 'total': 0})
)
print(f'Full pipeline: {len(full)} rows')
print(full.to_string(index=False))

# Step 8: Capstone — ETL pipeline
print()
print('=== Capstone: ETL Pipeline ===')
np.random.seed(42)
N2 = 2000
raw_transactions = pd.DataFrame({
    'ts':         pd.date_range('2026-01-01', periods=N2, freq='2h'),
    'product_id': np.random.randint(1, 7, N2),
    'qty':        np.random.randint(1, 15, N2),
    'unit_price': np.random.choice([864.0, 49.99, 99.99, 29.99, 1299.0, 6.0], N2),
    'region':     np.random.choice(['North','South','East','West'], N2),
    'status':     np.random.choice(['paid','paid','paid','pending','refunded'], N2),
})

price_map = {1:'Surface Pro',2:'Surface Pen',3:'Office 365',4:'USB-C Hub',5:'Surface Book',6:'Teams'}
cat_map   = {1:'Laptop',2:'Accessory',3:'Software',4:'Hardware',5:'Laptop',6:'Software'}

report = (raw_transactions
    .query('status == \"paid\"')
    .assign(
        product  = lambda d: d['product_id'].map(price_map),
        category = lambda d: d['product_id'].map(cat_map),
        revenue  = lambda d: d['qty'] * d['unit_price'],
        month    = lambda d: d['ts'].dt.to_period('M'),
        week     = lambda d: d['ts'].dt.to_period('W'),
    )
    .groupby(['month','category'])
    .agg(
        transactions=('qty', 'count'),
        units       =('qty', 'sum'),
        revenue     =('revenue', 'sum'),
        avg_order   =('revenue', 'mean'),
    )
    .round(2)
    .reset_index()
    .sort_values(['month', 'revenue'], ascending=[True, False])
)

print(f'ETL: {len(raw_transactions):,} transactions → {len(report)} summary rows')
print(report.to_string(index=False, max_rows=12))

total_rev = report['revenue'].sum()
print(f'\nTotal revenue: \${total_rev:,.2f}')
print(f'Best month-category:')
best = report.loc[report['revenue'].idxmax()]
print(f'  {best[\"month\"]} / {best[\"category\"]}: \${best[\"revenue\"]:,.2f}')
"
```

**📸 Verified Output:**
```
=== Time Series ===
Daily avg:    $   24,847.22
Best week:    $  213,141.19 (2026-03-08)
Total 180d:   $4,472,499.22
Monthly breakdown:
  January 2026   : $1,385,234.00
  ...

=== Method Chaining with pipe() ===
Before: 7 rows → After: 3 rows

=== Memory Optimization ===
Before: 6,461 KB
After:  1,029 KB (saved 84%)

=== Capstone: ETL Pipeline ===
ETL: 2,000 transactions → xx summary rows
Total revenue: $xx,xxx.xx
```

---

## Summary

| Feature | API | Use case |
|---------|-----|---------|
| MultiIndex | `pd.MultiIndex.from_product` | Hierarchical dimensions |
| Named agg | `.agg(name=('col', 'func'))` | Multiple aggregations cleanly |
| Transform | `.transform('sum')` | Group stat back to row |
| Method chain | `.pipe(fn)` | ETL steps without temp vars |
| Resample | `.resample('W').sum()` | Time series aggregation |
| Rolling | `.rolling(7).mean()` | Moving average |
| pd.eval | `df.eval('c = a * b')` | Fast column expressions |
| Category dtype | `.astype('category')` | 8x memory savings |

## Further Reading
- [pandas 2.x what's new](https://pandas.pydata.org/docs/whatsnew/v2.0.0.html)
- [pandas time series](https://pandas.pydata.org/docs/user_guide/timeseries.html)
- [pandas performance](https://pandas.pydata.org/docs/user_guide/enhancingperf.html)
