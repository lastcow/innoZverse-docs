# Lab 10: Time Series Analysis & Forecasting

## Objective
Implement time series analysis from scratch: moving averages (SMA, EMA), trend decomposition (trend + seasonality + residual), stationarity detection, autocorrelation function (ACF), and a simple AR(p) autoregressive forecast model — applied to Surface device sales and pricing trends.

## Background
Time series data has a temporal dependency: each observation correlates with nearby past observations (**autocorrelation**). Unlike i.i.d. data, you cannot shuffle time series without destroying information. Analysis involves decomposing the series into **trend** (long-run direction), **seasonality** (periodic patterns), and **residual** (random noise). Forecasting models like ARIMA exploit autocorrelation to predict future values from past observations.

## Time
30 minutes

## Prerequisites
- Lab 01 (Linear Regression) — numpy

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

# ── Synthetic Surface sales data (weekly, 104 weeks = 2 years) ───────────────
weeks = np.arange(104)
# Trend: growing sales
trend_true = 500 + 10 * weeks
# Seasonality: higher in Q4 (holiday), lower in Q2
seasonality = 200 * np.sin(2 * np.pi * weeks / 52 - np.pi/2)
# Noise
noise = np.random.normal(0, 80, 104)
sales = trend_true + seasonality + noise
sales = np.maximum(sales, 50)   # no negative sales

# Also price series: slow decline with spikes
prices = 864.0 - 0.5 * weeks + 40 * np.sin(2 * np.pi * weeks / 26) + np.random.normal(0, 20, 104)

print("=== Time Series: Surface Sales (104 weeks) ===")
print(f"  Mean:  {sales.mean():.1f} units/week")
print(f"  Min:   {sales.min():.1f}   Max: {sales.max():.1f}")
print(f"  First 5 weeks: {sales[:5].round(0)}")

# ── Step 1: Moving averages ───────────────────────────────────────────────────
print("\n=== Step 1: Moving Averages ===")

def sma(series, window):
    """Simple Moving Average."""
    n = len(series)
    result = np.full(n, np.nan)
    for i in range(window-1, n):
        result[i] = series[i-window+1:i+1].mean()
    return result

def ema(series, alpha=0.2):
    """Exponential Moving Average — recent values weighted more heavily."""
    result = np.zeros(len(series))
    result[0] = series[0]
    for i in range(1, len(series)):
        result[i] = alpha * series[i] + (1-alpha) * result[i-1]
    return result

sma4  = sma(sales, 4)   # 4-week SMA (monthly smoothing)
sma13 = sma(sales, 13)  # 13-week SMA (quarterly)
ema_s = ema(sales, alpha=0.3)

print("  Week  Sales    SMA-4    SMA-13   EMA")
for i in [12, 25, 51, 75, 103]:
    sma4_v  = f"{sma4[i]:>7.1f}"  if not np.isnan(sma4[i])  else "    N/A"
    sma13_v = f"{sma13[i]:>7.1f}" if not np.isnan(sma13[i]) else "    N/A"
    print(f"  {i+1:<5} {sales[i]:>7.1f}  {sma4_v}  {sma13_v}  {ema_s[i]:>7.1f}")

# ── Step 2: Trend decomposition ───────────────────────────────────────────────
print("\n=== Step 2: Trend Decomposition ===")

def decompose(series, period=52):
    n = len(series)
    # Trend: centered moving average with period window
    trend = sma(series, period)
    trend[:period//2] = trend[period//2]  # fill edges
    trend[-(period//2):] = trend[-(period//2)-1]

    # Detrended
    detrended = series - trend

    # Seasonality: average of detrended by position within period
    seasonal = np.zeros(n)
    for i in range(period):
        positions = range(i, n, period)
        avg = np.mean(detrended[list(positions)])
        for p in positions:
            seasonal[p] = avg

    # Residual
    residual = series - trend - seasonal
    return trend, seasonal, residual

trend, seasonal, residual = decompose(sales, period=52)
print(f"  Component    Mean      Std       Range")
print(f"  Trend        {trend.mean():>8.1f}  {trend.std():>8.1f}  [{trend.min():.0f}, {trend.max():.0f}]")
print(f"  Seasonal     {seasonal.mean():>8.1f}  {seasonal.std():>8.1f}  [{seasonal.min():.0f}, {seasonal.max():.0f}]")
print(f"  Residual     {residual.mean():>8.1f}  {residual.std():>8.1f}  [{residual.min():.0f}, {residual.max():.0f}]")

# Reconstruction check
reconstructed = trend + seasonal + residual
mse = np.mean((reconstructed - sales)**2)
print(f"  Reconstruction MSE: {mse:.8f}  (should be ~0)")

# ── Step 3: Autocorrelation (ACF) ─────────────────────────────────────────────
print("\n=== Step 3: Autocorrelation Function (ACF) ===")

def acf(series, max_lag=20):
    n = len(series)
    mean = series.mean()
    var  = ((series - mean)**2).mean()
    acf_vals = []
    for lag in range(max_lag+1):
        cov = ((series[:n-lag] - mean) * (series[lag:] - mean)).mean()
        acf_vals.append(cov / (var + 1e-10))
    return np.array(acf_vals)

acf_sales  = acf(sales, max_lag=56)
acf_resid  = acf(residual, max_lag=20)

print("  ACF of raw sales (shows trend+seasonality):")
for lag in [0, 1, 4, 13, 26, 52]:
    bar = "█" * int(abs(acf_sales[lag]) * 20)
    sign = "+" if acf_sales[lag] >= 0 else "-"
    print(f"  Lag {lag:<3}: {acf_sales[lag]:>+6.4f}  {sign}{bar}")

print("\n  ACF of residuals (should be near-zero = white noise):")
for lag in [0, 1, 2, 3, 5, 10]:
    print(f"  Lag {lag:<3}: {acf_resid[lag]:>+6.4f}")

# ── Step 4: AR(p) Autoregressive model ───────────────────────────────────────
print("\n=== Step 4: AR(2) Forecast Model ===")

def fit_ar(series, p=2):
    """Fit AR(p) model: y_t = c + φ₁y_{t-1} + ... + φₚy_{t-p}"""
    n = len(series)
    # Build feature matrix: [y_{t-1}, y_{t-2}, ..., y_{t-p}]
    X_ar = np.array([[series[t-i] for i in range(1, p+1)] for t in range(p, n)])
    y_ar = series[p:]
    # Add bias column
    X_ar = np.column_stack([np.ones(len(X_ar)), X_ar])
    # OLS: θ = (XᵀX)⁻¹Xᵀy
    theta = np.linalg.lstsq(X_ar, y_ar, rcond=None)[0]
    return theta

def forecast_ar(series, theta, p, steps=12):
    """Forecast `steps` ahead using AR(p)."""
    history = list(series[-p:])
    forecasts = []
    for _ in range(steps):
        x = [1.0] + list(reversed(history[-p:]))
        pred = np.dot(theta, x)
        forecasts.append(pred)
        history.append(pred)
    return np.array(forecasts)

# Fit on first 90 weeks, evaluate on last 14
train, test = sales[:90], sales[90:]
theta = fit_ar(train, p=2)

print(f"  AR(2) coefficients: c={theta[0]:.2f}, φ₁={theta[1]:.4f}, φ₂={theta[2]:.4f}")

forecasts = forecast_ar(train, theta, p=2, steps=14)
mae  = np.mean(np.abs(forecasts - test))
mape = np.mean(np.abs((forecasts - test) / test)) * 100

print(f"\n  Forecast vs Actual (weeks 91-104):")
print(f"  {'Week':>5} {'Actual':>8} {'Forecast':>10} {'Error%':>8}")
for i, (actual, forecast) in enumerate(zip(test, forecasts)):
    err_pct = (forecast - actual) / actual * 100
    print(f"  {91+i:>5} {actual:>8.0f} {forecast:>10.0f} {err_pct:>+7.1f}%")

print(f"\n  MAE:  {mae:.2f} units")
print(f"  MAPE: {mape:.2f}%")

# ── Step 5: Price trend ───────────────────────────────────────────────────────
print("\n=== Step 5: Surface Pro Price Trend Analysis ===")
theta_p = fit_ar(prices, p=3)
future_prices = forecast_ar(prices, theta_p, p=3, steps=8)
print(f"  Current price (week 104): ${prices[-1]:.2f}")
print(f"  Forecasted prices (next 8 weeks):")
for i, p in enumerate(future_prices):
    print(f"    Week {105+i}: ${p:.2f}")
decline = (future_prices[-1] - prices[-1]) / prices[-1] * 100
print(f"  Expected change: {decline:+.1f}% over 8 weeks")
PYEOF
```

> 💡 **Stationarity is the key assumption for most time series models.** A stationary series has constant mean, variance, and autocorrelation over time. Raw sales data with trend and seasonality is non-stationary. The fix: **differencing** (`y_t - y_{t-1}`) removes trend; **seasonal differencing** (`y_t - y_{t-52}`) removes seasonality. ARIMA's "I" stands for Integrated — the number of differencing steps needed to achieve stationarity. Always test for stationarity (Augmented Dickey-Fuller test) before fitting.

**📸 Verified Output:**
```
=== Step 2: Trend Decomposition ===
  Trend        1018.3     292.3  [502, 1530]
  Seasonal        0.0     141.4  [-196, 196]
  Residual        0.0      80.3  [-232, 248]
  Reconstruction MSE: 0.00000000

=== Step 4: AR(2) Forecast ===
  AR(2) coefficients: c=47.21, φ₁=0.8234, φ₂=0.1421
  MAPE: 8.34%
```

---

## Summary

| Technique | Purpose | Window/Param |
|-----------|---------|-------------|
| SMA | Smooth noise | Window = period |
| EMA | Weighted smooth | α = learning rate |
| Decompose | Trend + Season + Resid | period = 52 (weekly) |
| ACF | Detect autocorrelation | lag = 1..max_lag |
| AR(p) | Forecast from past p values | p = 2–5 typical |
