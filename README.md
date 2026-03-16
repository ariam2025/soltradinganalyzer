# 📊 SOL Trading Analyzer

A Python-based TradingView-style analysis tool for **SOL/USDT Binance Futures** that computes key technical levels, generates live price charts, and monitors liquidation cluster proximity alerts.

> ⚠️ **Disclaimer:** This project is for educational and informational purposes only. It is not financial advice. Crypto trading carries significant risk of capital loss.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📈 **Live Price Charts** | Candlestick chart with Bollinger Bands, SMAs, RSI subplot |
| 🎯 **Key Level Detection** | Auto-detects support & resistance from recent price structure |
| ⚡ **Liquidation Alerts** | Real-time proximity alerts to major long/short liquidation clusters |
| 🧠 **Setup Evaluation** | Bias detection (Bullish/Bearish/Neutral) using RSI, MACD, Stoch, ADX |
| 🖥️ **CLI Interface** | Simple command-line usage with multiple modes |
| 🔁 **Multi-Timeframe** | Supports 1m, 5m, 15m, 1h, 4h, 1d analysis |

---

## 📂 Project Structure

```
sol-trading-analyzer/
├── main.py                 # CLI entry point
├── requirements.txt        # Python dependencies
├── .gitignore
├── src/
│   ├── analyzer.py         # OHLCV fetch, indicators, setup evaluation
│   ├── chart.py            # Chart generation (matplotlib)
│   ├── alerts.py           # Liquidation proximity monitor
│   └── config.py           # Constants and configuration
├── charts/                 # Generated chart PNGs (auto-created)
├── alerts/                 # Alert logs (auto-created)
└── tests/
    └── test_analyzer.py    # Unit tests
```

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/sol-trading-analyzer.git
cd sol-trading-analyzer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run analysis

```bash
# Default 15m analysis + chart
python main.py

# 4h timeframe analysis
python main.py --tf 4h

# 1h analysis, skip chart
python main.py --tf 1h --no-chart

# Chart only (no text report)
python main.py --chart-only

# One-shot liquidation check
python main.py --check-liq

# Start continuous liq monitor (checks every 30s)
python main.py --monitor
```

---

## 📊 Sample Output

```
╔══════════════════════════════════════════════════════╗
║           SOL/USDT — TRADING ANALYSIS REPORT        ║
╚══════════════════════════════════════════════════════╝

  Timestamp   : 2025-03-15 10:25:00 UTC
  Price       : $87.9300
  Bias        : 🟡 NEUTRAL

┌─────────────────── INDICATORS ────────────────────────
│  RSI 14      : 49.3
│  MACD        : Bearish ▼
│  Stoch K     : 36.8
│  ADX         : 26.3
│  Above SMA20 : ❌
│  Above SMA50 : ❌
│  BB Upper    : $90.1200
│  BB Lower    : $85.4800
└───────────────────────────────────────────────────────

┌─────────────────── KEY LEVELS ────────────────────────
│  Trigger     : $88.0600   ← Long entry above this
│  Target      : $89.3810   ← First profit zone
│  Invalidation: $86.4800   ← Exit/abort if lost
└───────────────────────────────────────────────────────

┌──────────────── LIQUIDATION ZONES ────────────────────
│  Long Liq    : $87.0 (6.7B) 🟠 Downside magnet
│  Short Liq   : $89.0 (5.5B) 🟣 Upside target
└───────────────────────────────────────────────────────
```

---

## ⚙️ Configuration

Edit `src/config.py` to customize:

```python
# Update liquidation levels manually (source: Coinglass, Hyblock, etc.)
MANUAL_LIQ_LEVELS = {
    "long_liq":  {"price": 87.00, "size_b": 6.7},
    "short_liq": {"price": 89.00, "size_b": 5.5},
}

# Alert proximity threshold (%)
# e.g. 0.5 means alert when price is within 0.5% of a liq level
ALERT_COOLDOWN_SECONDS = 300
```

---

## 📉 Indicators Computed

| Indicator | Period | Usage |
|---|---|---|
| SMA | 20, 50, 200 | Trend direction |
| Bollinger Bands | 20, ±2σ | Volatility / squeeze detection |
| RSI | 14 | Momentum / overbought-oversold |
| MACD | 12/26/9 | Momentum crossovers |
| Stochastic | 14/3 | Short-term reversals |
| ADX | 14 | Trend strength |
| ATR | 14 | Volatility measure |

---

## 🔔 Liquidation Alert Monitor

The monitor checks price proximity to configured liquidation levels every 30 seconds:

```bash
python main.py --monitor
```

Example alert output:
```
=======================================================
⚠️  LIQUIDATION PROXIMITY ALERT
=======================================================
  Type       : LONG LIQ 🟠
  Current    : $87.4800
  Liq Level  : $87.00 (6.7B)
  Distance   : 0.551% ABOVE liq zone
  Time       : 2025-03-15 10:30:00 UTC
=======================================================
```

Alerts are also saved to `alerts/alerts.log`.

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---

## 📦 Dependencies

- `requests` — Binance Futures API calls
- `pandas` — Data manipulation
- `numpy` — Numerical computations
- `matplotlib` — Chart generation

No API key required — uses Binance Futures **public endpoints only**.

---

## 🗺️ Roadmap

- [ ] Telegram/Discord alert integration
- [ ] Multi-asset support (BTC, ETH, etc.)
- [ ] Automated backtesting module
- [ ] Coinglass API integration for live liquidation data
- [ ] Web dashboard (Flask/Streamlit)

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first to discuss what you'd like to change.
