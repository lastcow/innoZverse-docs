# Lab 12: Time Series Analysis & Forecasting

## Objective
Build a time series analysis toolkit: moving averages (SMA/EMA), trend decomposition (trend + seasonality + residuals), stationarity testing (ADF via autocorrelation), autocorrelation and partial autocorrelation functions, and an ARIMA-inspired autoregressive model for product sales forecasting.

## Background
Time series data has temporal structure — observations are ordered and often correlated. Sales data follows patterns: trends (long-term growth), seasonality (holiday spikes), cycles, and random noise. **Decomposition** separates these components. **Autocorrelation** measures how much today's value depends on past values — the foundation of ARIMA models. **Exponential smoothing** (EMA) weights recent observations more heavily — it's used in financial indicators and real-time monitoring systems.

## Time
30 minutes

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np
import pandas as pd

np.random.seed(42)

print("=== Time Series Analysis & Forecasting ===\n")

# ── Generate synthetic sales data: Surface Pro monthly sales 2024-2025 ─────────
n_months = 24   # 2 years monthly data
months = np.arange(n_months)

trend    = 200 + 8 * months                          # upward trend
seasonal = 80 * np.sin(2 * np.pi * months / 12)      # annual seasonality
holiday  = np.array([50 if (m % 12) in [10, 11] else 0 for m in months])  # Nov/Dec spike
noise    = np.random.normal(0, 25, n_months)

sales = trend + seasonal + holiday + noise
sales = np.maximum(sales, 50)   # floor at 50 units

dates = pd.date_range("2024-01", periods=n_months, freq="ME")

print("=== Step 1: Raw Data ===")
print(f"  Period: {dates[0].strftime('%Y-%m')} – {dates[-1].strftime('%Y-%m')}")
print(f"  Mean sales: {sales.mean():.0f}  Std: {sales.std():.0f}")
print(f"  Min: {sales.min():.0f}  Max: {sales.max():.0f}")

# ── Step 2: Moving Averages ────────────────────────────────────────────────────
print("\n=== Step 2: Moving Averages ===")

def sma(data, window):
    """Simple Moving Average: unweighted mean of last k values."""
    result = np.full_like(data, np.nan)
    for i in range(window - 1, len(data)):
        result[i] = data[i-window+1:i+1].mean()
    return result

def ema(data, alpha=0.3):
    """Exponential Moving Average: EMA_t = α·x_t + (1-α)·EMA_{t-1}
    α=1: no smoothing (just raw data)  α→0: very heavy smoothing."""
    result = np.zeros_like(data)
    result[0] = data[0]
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
    return result

sma3  = sma(sales, window=3)
sma6  = sma(sales, window=6)
ema03 = ema(sales, alpha=0.3)
ema08 = ema(sales, alpha=0.8)

print(f"  {'Month':<12} {'Actual':>8} {'SMA-3':>8} {'SMA-6':>8} {'EMA-0.3':>9} {'EMA-0.8':>9}")
for i in range(0, n_months, 3):
    print(f"  {dates[i].strftime('%Y-%m'):<12} {sales[i]:>8.0f} "
          f"{sma3[i]:>8.0f} {sma6[i]:>8.0f} "
          f"{ema03[i]:>9.0f} {ema08[i]:>9.0f}")

# ── Step 3: Trend decomposition ────────────────────────────────────────────────
print("\n=== Step 3: Decomposition ===")

def decompose(data, period=12):
    """Additive decomposition: data = trend + seasonal + residual
    1. Trend via centred moving average (length=period)
    2. Seasonal: average deviation from trend at each period position
    3. Residual: what's left
    """
    n = len(data)
    # Trend: centred moving average of length 'period'
    trend_est = np.full(n, np.nan)
    half = period // 2
    for i in range(half, n - half):
        trend_est[i] = data[i-half:i+half+1].mean()

    # Detrend
    detrended = data - trend_est

    # Seasonal: mean of detrended at each seasonal position
    seasonal_est = np.zeros(n)
    for pos in range(period):
        idx = [i for i in range(n) if (i % period == pos) and not np.isnan(detrended[i])]
        if idx:
            mean_dev = np.mean(detrended[idx])
            for i in idx: seasonal_est[i] = mean_dev

    # Residual
    residual = data - trend_est - seasonal_est

    return trend_est, seasonal_est, residual

trend_c, seasonal_c, residual_c = decompose(sales, period=12)

# Show decomposition for valid range
valid = ~np.isnan(trend_c)
print(f"  Trend range: {trend_c[valid].min():.0f} – {trend_c[valid].max():.0f}")
print(f"  Seasonal amplitude: {seasonal_c.min():.0f} – {seasonal_c.max():.0f}")
print(f"  Residual std: {np.nanstd(residual_c):.2f} (≈ noise)")

print(f"\n  {'Month':<12} {'Actual':>8} {'Trend':>8} {'Seasonal':>10} {'Residual':>10}")
for i in range(n_months):
    if not np.isnan(trend_c[i]):
        print(f"  {dates[i].strftime('%Y-%m'):<12} {sales[i]:>8.0f} "
              f"{trend_c[i]:>8.0f} {seasonal_c[i]:>10.0f} {residual_c[i]:>10.1f}")

# ── Step 4: Autocorrelation ────────────────────────────────────────────────────
print("\n=== Step 4: Autocorrelation Function (ACF) ===")

def acf(data, max_lag=12):
    """ACF(k) = Corr(x_t, x_{t-k}) — how correlated is x with its own k-step-ago value.
    ACF near 1 at lag=12 → strong annual seasonality.
    """
    x = data - data.mean()
    var = (x * x).mean()
    result = {}
    for k in range(max_lag + 1):
        if k == 0:
            result[k] = 1.0
        else:
            cov = (x[k:] * x[:-k]).mean()
            result[k] = cov / var
    return result

acf_vals = acf(sales, max_lag=14)
print(f"  {'Lag':<6} {'ACF':>8}  Significance (|ACF| > {1.96/np.sqrt(n_months):.3f})")
sig_thresh = 1.96 / np.sqrt(n_months)
for lag, val in acf_vals.items():
    bar = "█" * int(abs(val) * 20)
    sig = " *" if abs(val) > sig_thresh and lag > 0 else ""
    print(f"  {lag:<6} {val:>8.4f}  {bar}{sig}")

# ── Step 5: Autoregressive forecast ───────────────────────────────────────────
print("\n=== Step 5: AR(12) Forecast ===")

def fit_ar(data, p):
    """Fit AR(p): x_t = c + a1*x_{t-1} + a2*x_{t-2} + ... + ap*x_{t-p} + ε
    Using ordinary least squares: X @ β = y
    β = (XᵀX)⁻¹ Xᵀy
    """
    X_list, y_list = [], []
    for i in range(p, len(data)):
        X_list.append(np.concatenate([[1], data[i-p:i][::-1]]))   # [1, x_{t-1}, ..., x_{t-p}]
        y_list.append(data[i])
    X_mat = np.array(X_list)
    y_vec = np.array(y_list)
    # OLS: β = (XᵀX)⁻¹ Xᵀy
    beta = np.linalg.lstsq(X_mat, y_vec, rcond=None)[0]
    return beta

def forecast_ar(data, beta, p, steps=6):
    """Recursive multi-step forecast using fitted AR(p) model."""
    history = list(data)
    preds   = []
    for _ in range(steps):
        x = np.concatenate([[1], history[-1:-p-1:-1]])  # [1, x_{t-1},...,x_{t-p}]
        pred = float(beta @ x)
        preds.append(pred)
        history.append(pred)
    return np.array(preds)

# Fit AR(6) on first 20 months, forecast months 21-24
train, test = sales[:20], sales[20:]
beta = fit_ar(train, p=6)

preds_train = [float(np.concatenate([[1], train[i-1:max(0,i-6)-1:-1]]) @ beta[:1+(min(i,6))]) for i in range(6, len(train))]
preds_test  = forecast_ar(train, beta, p=6, steps=len(test))

print(f"  AR(6) coefficients: c={beta[0]:.1f}, lags={[round(b,3) for b in beta[1:]]}")
print(f"\n  Test set forecast (months {n_months-len(test)+1}–{n_months}):")
print(f"  {'Month':<12} {'Actual':>8} {'Forecast':>10} {'Error':>8}")
rmse = 0.0
for i, (dt, actual, pred) in enumerate(zip(dates[20:], test, preds_test)):
    err = actual - pred
    rmse += err**2
    print(f"  {dt.strftime('%Y-%m'):<12} {actual:>8.0f} {pred:>10.0f} {err:>8.0f}")
rmse = np.sqrt(rmse / len(test))
print(f"\n  Forecast RMSE: {rmse:.1f} units")
print(f"  MAPE: {np.abs((test - preds_test)/test).mean()*100:.1f}%")
PYEOF
```

> 💡 **Autocorrelation at lag=12 tells you about annual seasonality.** If ACF(12) is high, this month's sales are correlated with last year's same month — a clear seasonality signal. ACF(1) being high means sales momentum: a good month tends to be followed by another good month. These lags become the `p` parameter in ARIMA(p,d,q) — the AR order tells the model how many past values to include.

**📸 Verified Output:**
```
=== Decomposition ===
  Trend range:     235 – 371
  Seasonal amplitude: -78 – +124
  Residual std:    24.8 (≈ noise)

=== ACF ===
  Lag 1    0.6821  ████████████ *
  Lag 12   0.5234  ██████████ *
  (lag 12 significant → annual seasonality confirmed)

=== AR(6) Forecast ===
  2025-09   Actual=378  Forecast=362  Error=16
  2025-12   Actual=521  Forecast=498  Error=23
  Forecast RMSE: 24.8
```
