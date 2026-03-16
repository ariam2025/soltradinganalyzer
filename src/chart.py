"""
Chart Generator — Plots price action with indicators and key levels.
Uses matplotlib. Saves PNG to /charts directory.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
from datetime import datetime
from config import Config


def plot_analysis(df: pd.DataFrame, setup: dict, levels: dict, filename: str = None) -> str:
    """
    Generate a TradingView-style analysis chart with:
    - Candlestick price action
    - Bollinger Bands
    - SMAs (20, 50)
    - Key support/resistance levels
    - Liquidation zones
    - RSI subplot

    Args:
        df: OHLCV DataFrame with indicators
        setup: Setup dict from analyzer.evaluate_setup()
        levels: Key levels dict from analyzer.compute_key_levels()
        filename: Output filename (auto-generated if None)

    Returns:
        Path to saved chart PNG
    """
    os.makedirs(Config.CHART_DIR, exist_ok=True)

    if filename is None:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
        filename = f"SOL_analysis_{ts}.png"

    filepath = os.path.join(Config.CHART_DIR, filename)

    # Use last 100 candles for readability
    plot_df = df.tail(100).copy().reset_index(drop=True)

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(16, 10),
        gridspec_kw={"height_ratios": [3, 1]},
        facecolor="#0d1117"
    )
    fig.subplots_adjust(hspace=0.08)

    # --- Candlesticks ---
    for i, row in plot_df.iterrows():
        color = "#26a69a" if row["close"] >= row["open"] else "#ef5350"
        ax1.plot([i, i], [row["low"], row["high"]], color=color, linewidth=0.8)
        ax1.add_patch(plt.Rectangle(
            (i - 0.3, min(row["open"], row["close"])),
            0.6,
            abs(row["close"] - row["open"]),
            color=color
        ))

    # --- Bollinger Bands ---
    ax1.plot(plot_df.index, plot_df["bb_upper"], color="#90caf9", linewidth=0.8,
             linestyle="--", label="BB Upper", alpha=0.7)
    ax1.plot(plot_df.index, plot_df["sma_20"], color="#90caf9", linewidth=0.8,
             linestyle="-", label="SMA 20", alpha=0.5)
    ax1.plot(plot_df.index, plot_df["bb_lower"], color="#90caf9", linewidth=0.8,
             linestyle="--", alpha=0.7)
    ax1.fill_between(plot_df.index, plot_df["bb_upper"], plot_df["bb_lower"],
                     alpha=0.05, color="#90caf9")

    # --- SMA 50 ---
    ax1.plot(plot_df.index, plot_df["sma_50"], color="#ffd54f", linewidth=1.0,
             label="SMA 50", alpha=0.8)

    # --- Key Resistance Levels ---
    for r in levels.get("resistance", []):
        if plot_df["low"].min() < r < plot_df["high"].max() * 1.02:
            ax1.axhline(y=r, color="#ef5350", linewidth=0.9, linestyle="--", alpha=0.8)
            ax1.text(len(plot_df) - 1, r, f"  R ${r:.2f}", color="#ef5350",
                     fontsize=7.5, va="center")

    # --- Key Support Levels ---
    for s in levels.get("support", []):
        if plot_df["low"].min() * 0.98 < s < plot_df["high"].max():
            ax1.axhline(y=s, color="#26a69a", linewidth=0.9, linestyle="--", alpha=0.8)
            ax1.text(len(plot_df) - 1, s, f"  S ${s:.2f}", color="#26a69a",
                     fontsize=7.5, va="center")

    # --- Liquidation Zones ---
    liq = Config.MANUAL_LIQ_LEVELS
    long_liq_price = liq["long_liq"]["price"]
    short_liq_price = liq["short_liq"]["price"]

    ax1.axhline(y=long_liq_price, color="#ff6f00", linewidth=1.2,
                linestyle=":", alpha=0.9)
    ax1.text(2, long_liq_price, f" Long Liq ${long_liq_price} ({liq['long_liq']['size_b']}B)",
             color="#ff6f00", fontsize=7.5, va="bottom")

    ax1.axhline(y=short_liq_price, color="#ab47bc", linewidth=1.2,
                linestyle=":", alpha=0.9)
    ax1.text(2, short_liq_price, f" Short Liq ${short_liq_price} ({liq['short_liq']['size_b']}B)",
             color="#ab47bc", fontsize=7.5, va="bottom")

    # --- Trigger & Invalidation ---
    ax1.axhline(y=setup["trigger"], color="#fff176", linewidth=1.0, linestyle="-.", alpha=0.9)
    ax1.text(2, setup["trigger"], f" Trigger ${setup['trigger']:.2f}",
             color="#fff176", fontsize=7.5, va="bottom")

    ax1.axhline(y=setup["invalidation"], color="#ff8a65", linewidth=1.0, linestyle="-.", alpha=0.9)
    ax1.text(2, setup["invalidation"], f" Invalidation ${setup['invalidation']:.2f}",
             color="#ff8a65", fontsize=7.5, va="top")

    # --- Price label ---
    current_price = setup["price"]
    ax1.annotate(f"${current_price:.2f}", xy=(len(plot_df) - 1, current_price),
                 xytext=(len(plot_df) + 1, current_price),
                 fontsize=9, color="white", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.2", facecolor="#1f2937", edgecolor="white"))

    # --- Bias badge ---
    bias_color = {"BULLISH": "#26a69a", "BEARISH": "#ef5350", "NEUTRAL": "#ffd54f"}
    ax1.text(0.01, 0.97, f"● {setup['bias']}",
             transform=ax1.transAxes, fontsize=11, fontweight="bold",
             color=bias_color.get(setup["bias"], "white"), va="top")

    ax1.text(0.01, 0.91,
             f"RSI {setup['rsi']} | ADX {setup['adx']} | Stoch {setup['stoch_k']}",
             transform=ax1.transAxes, fontsize=8, color="#aaaaaa", va="top")

    ax1.set_facecolor("#0d1117")
    ax1.tick_params(colors="gray", labelsize=8)
    ax1.spines[:].set_color("#1f2937")
    ax1.set_title(f"SOL/USDT — Analysis Chart  |  {setup['timestamp']}",
                  color="white", fontsize=11, pad=10)
    ax1.legend(loc="upper left", fontsize=7, facecolor="#1f2937",
               labelcolor="white", framealpha=0.6)
    ax1.set_xlim(-1, len(plot_df) + 5)

    # --- RSI Subplot ---
    ax2.plot(plot_df.index, plot_df["rsi"], color="#ce93d8", linewidth=1.2, label="RSI 14")
    ax2.axhline(70, color="#ef5350", linewidth=0.6, linestyle="--", alpha=0.6)
    ax2.axhline(50, color="gray", linewidth=0.5, linestyle="--", alpha=0.4)
    ax2.axhline(30, color="#26a69a", linewidth=0.6, linestyle="--", alpha=0.6)
    ax2.fill_between(plot_df.index, plot_df["rsi"], 50,
                     where=(plot_df["rsi"] > 50), alpha=0.15, color="#26a69a")
    ax2.fill_between(plot_df.index, plot_df["rsi"], 50,
                     where=(plot_df["rsi"] < 50), alpha=0.15, color="#ef5350")
    ax2.set_ylim(0, 100)
    ax2.set_facecolor("#0d1117")
    ax2.tick_params(colors="gray", labelsize=8)
    ax2.spines[:].set_color("#1f2937")
    ax2.set_ylabel("RSI", color="gray", fontsize=8)
    ax2.set_xlim(-1, len(plot_df) + 5)

    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches="tight", facecolor="#0d1117")
    plt.close()

    print(f"[CHART] Saved → {filepath}")
    return filepath
