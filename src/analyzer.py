"""
SOL Trading Analyzer — Main Module
Fetches price data, computes key levels, and evaluates setups.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional
from config import Config


def fetch_ohlcv(symbol: str = "SOLUSDT", interval: str = "15m", limit: int = 200) -> pd.DataFrame:
    """
    Fetch OHLCV data from Binance Futures public API.

    Args:
        symbol: Trading pair (e.g. SOLUSDT)
        interval: Candlestick interval (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles to fetch (max 1500)

    Returns:
        DataFrame with OHLCV + computed indicators
    """
    url = f"{Config.BASE_URL}/fapi/v1/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        raw = response.json()
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch OHLCV data: {e}")
        return pd.DataFrame()

    df = pd.DataFrame(raw, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_vol", "trades", "taker_buy_base",
        "taker_buy_quote", "ignore"
    ])

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    df = df[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    df = compute_indicators(df)
    return df


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add RSI, Bollinger Bands, MACD, Stochastic, ADX, and SMAs.
    """
    # --- SMAs ---
    df["sma_20"] = df["close"].rolling(20).mean()
    df["sma_50"] = df["close"].rolling(50).mean()
    df["sma_200"] = df["close"].rolling(200).mean()

    # --- Bollinger Bands (20, 2) ---
    bb_std = df["close"].rolling(20).std()
    df["bb_upper"] = df["sma_20"] + 2 * bb_std
    df["bb_lower"] = df["sma_20"] - 2 * bb_std

    # --- RSI (14) ---
    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = 100 - (100 / (1 + rs))

    # --- MACD (12, 26, 9) ---
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # --- Stochastic (14, 3) ---
    low14 = df["low"].rolling(14).min()
    high14 = df["high"].rolling(14).max()
    df["stoch_k"] = 100 * (df["close"] - low14) / (high14 - low14).replace(0, np.nan)
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()

    # --- ADX (14) ---
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["close"].shift()),
            abs(df["low"] - df["close"].shift())
        )
    )
    df["atr"] = df["tr"].rolling(14).mean()
    df["+dm"] = np.where((df["high"] - df["high"].shift()) > (df["low"].shift() - df["low"]),
                          np.maximum(df["high"] - df["high"].shift(), 0), 0)
    df["-dm"] = np.where((df["low"].shift() - df["low"]) > (df["high"] - df["high"].shift()),
                          np.maximum(df["low"].shift() - df["low"], 0), 0)
    df["+di"] = 100 * df["+dm"].rolling(14).mean() / df["atr"].replace(0, np.nan)
    df["-di"] = 100 * df["-dm"].rolling(14).mean() / df["atr"].replace(0, np.nan)
    dx = 100 * abs(df["+di"] - df["-di"]) / (df["+di"] + df["-di"]).replace(0, np.nan)
    df["adx"] = dx.rolling(14).mean()

    return df


def compute_key_levels(df: pd.DataFrame, lookback: int = 50) -> dict:
    """
    Identify support and resistance levels from recent price structure.

    Returns:
        Dictionary with support and resistance level lists
    """
    recent = df.tail(lookback)
    highs = recent["high"].values
    lows = recent["low"].values

    # Simple pivot detection
    resistances = []
    supports = []

    for i in range(2, len(highs) - 2):
        if highs[i] == max(highs[i-2:i+3]):
            resistances.append(round(highs[i], 4))
        if lows[i] == min(lows[i-2:i+3]):
            supports.append(round(lows[i], 4))

    # Cluster nearby levels within 0.3%
    def cluster_levels(levels: list, threshold: float = 0.003) -> list:
        if not levels:
            return []
        levels = sorted(set(levels))
        clustered = [levels[0]]
        for lvl in levels[1:]:
            if (lvl - clustered[-1]) / clustered[-1] > threshold:
                clustered.append(lvl)
        return clustered

    return {
        "resistance": cluster_levels(resistances)[-5:],
        "support": cluster_levels(supports)[:5]
    }


def evaluate_setup(df: pd.DataFrame, levels: dict, liq_levels: Optional[dict] = None) -> dict:
    """
    Evaluate the current trading setup based on indicators and levels.

    Returns:
        Dictionary with bias, trigger, invalidation, targets, and signal details
    """
    latest = df.iloc[-1]
    price = latest["close"]

    # Indicator signals
    rsi = latest["rsi"]
    macd_bull = latest["macd_hist"] > 0
    stoch = latest["stoch_k"]
    adx = latest["adx"]
    above_sma20 = price > latest["sma_20"]
    above_sma50 = price > latest["sma_50"]

    bullish_signals = sum([
        rsi > 55,
        macd_bull,
        stoch > 50,
        above_sma20,
        above_sma50
    ])

    # Bias
    if bullish_signals >= 4:
        bias = "BULLISH"
    elif bullish_signals <= 1:
        bias = "BEARISH"
    else:
        bias = "NEUTRAL"

    # Nearest levels
    resistances = [r for r in levels["resistance"] if r > price]
    supports = [s for s in levels["support"] if s < price]

    trigger = min(resistances) if resistances else round(price * 1.005, 4)
    invalidation = max(supports) if supports else round(price * 0.995, 4)
    target = round(trigger * 1.015, 4)

    # Liq context
    liq_note = ""
    if liq_levels:
        long_liq = liq_levels.get("long_liq", {})
        short_liq = liq_levels.get("short_liq", {})
        if long_liq:
            liq_note += f"  Long liq cluster: ${long_liq.get('price')} (${long_liq.get('size_b')}B)\n"
        if short_liq:
            liq_note += f"  Short liq cluster: ${short_liq.get('price')} (${short_liq.get('size_b')}B)\n"

    return {
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "symbol": "SOL/USDT",
        "price": price,
        "bias": bias,
        "rsi": round(rsi, 2),
        "macd_bullish": macd_bull,
        "stoch_k": round(stoch, 2),
        "adx": round(adx, 2),
        "above_sma20": above_sma20,
        "above_sma50": above_sma50,
        "trigger": trigger,
        "invalidation": invalidation,
        "target": target,
        "liq_note": liq_note,
        "bb_upper": round(latest["bb_upper"], 4),
        "bb_lower": round(latest["bb_lower"], 4),
    }
