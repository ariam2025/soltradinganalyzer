"""
Configuration constants for SOL Trading Analyzer.
"""


class Config:
    # Binance Futures public API (no auth required)
    BASE_URL = "https://fapi.binance.com"

    # Default trading pair
    SYMBOL = "SOLUSDT"

    # Timeframes available
    TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]

    # Liquidation level thresholds (USD billions)
    LIQ_ALERT_THRESHOLD_B = 1.0   # alert if cluster >= $1B

    # Alert cooldown in seconds (avoid repeated alerts)
    ALERT_COOLDOWN_SECONDS = 300

    # Chart output directory
    CHART_DIR = "charts"

    # Key manual liquidation levels for SOL (update as needed)
    MANUAL_LIQ_LEVELS = {
        "long_liq": {"price": 87.00, "size_b": 6.7},
        "short_liq": {"price": 89.00, "size_b": 5.5},
    }

    # RSI thresholds
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    RSI_NEUTRAL_LOW = 45
    RSI_NEUTRAL_HIGH = 55
