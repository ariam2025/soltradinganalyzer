#!/usr/bin/env python3
"""
SOL Trading Analyzer — CLI Entry Point

Usage:
    python main.py                  # Full analysis (15m default)
    python main.py --tf 4h          # Analysis on 4h timeframe
    python main.py --monitor        # Start liquidation alert monitor
    python main.py --chart-only     # Generate chart without printing report
    python main.py --check-liq      # One-shot liquidation proximity check
"""

import argparse
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from analyzer import fetch_ohlcv, compute_key_levels, evaluate_setup
from chart import plot_analysis
from alerts import LiqAlert, run_single_check
from config import Config


def print_report(setup: dict, levels: dict) -> None:
    """Print formatted analysis report to console."""
    bias_icon = {"BULLISH": "🟢", "BEARISH": "🔴", "NEUTRAL": "🟡"}.get(setup["bias"], "⚪")

    print(f"""
╔══════════════════════════════════════════════════════╗
║           SOL/USDT — TRADING ANALYSIS REPORT        ║
╚══════════════════════════════════════════════════════╝

  Timestamp   : {setup['timestamp']}
  Price       : ${setup['price']:.4f}
  Bias        : {bias_icon} {setup['bias']}

┌─────────────────── INDICATORS ────────────────────────
│  RSI 14      : {setup['rsi']}
│  MACD        : {'Bullish ▲' if setup['macd_bullish'] else 'Bearish ▼'}
│  Stoch K     : {setup['stoch_k']}
│  ADX         : {setup['adx']}
│  Above SMA20 : {'✅' if setup['above_sma20'] else '❌'}
│  Above SMA50 : {'✅' if setup['above_sma50'] else '❌'}
│  BB Upper    : ${setup['bb_upper']:.4f}
│  BB Lower    : ${setup['bb_lower']:.4f}
└───────────────────────────────────────────────────────

┌─────────────────── KEY LEVELS ────────────────────────
│  Trigger     : ${setup['trigger']:.4f}   ← Long entry above this
│  Target      : ${setup['target']:.4f}   ← First profit zone
│  Invalidation: ${setup['invalidation']:.4f}   ← Exit/abort if lost
└───────────────────────────────────────────────────────

┌─────────────────── STRUCTURE ─────────────────────────
│  Resistance  : {', '.join(f'${r}' for r in levels['resistance'][-3:])}
│  Support     : {', '.join(f'${s}' for s in levels['support'][:3])}
└───────────────────────────────────────────────────────

┌──────────────── LIQUIDATION ZONES ────────────────────
│  Long Liq    : ${Config.MANUAL_LIQ_LEVELS['long_liq']['price']} ({Config.MANUAL_LIQ_LEVELS['long_liq']['size_b']}B) 🟠 Downside magnet
│  Short Liq   : ${Config.MANUAL_LIQ_LEVELS['short_liq']['price']} ({Config.MANUAL_LIQ_LEVELS['short_liq']['size_b']}B) 🟣 Upside target
└───────────────────────────────────────────────────────

⚠️  This is not financial advice. Trade at your own risk.
""")


def main():
    parser = argparse.ArgumentParser(
        description="SOL Trading Analyzer — TradingView-style analysis tool"
    )
    parser.add_argument("--tf", default="15m", choices=Config.TIMEFRAMES,
                        help="Timeframe for analysis (default: 15m)")
    parser.add_argument("--symbol", default=Config.SYMBOL,
                        help="Trading pair (default: SOLUSDT)")
    parser.add_argument("--monitor", action="store_true",
                        help="Start continuous liquidation alert monitor")
    parser.add_argument("--check-liq", action="store_true",
                        help="One-shot liquidation proximity check")
    parser.add_argument("--chart-only", action="store_true",
                        help="Generate chart only, skip text report")
    parser.add_argument("--no-chart", action="store_true",
                        help="Skip chart generation")
    parser.add_argument("--limit", type=int, default=200,
                        help="Number of candles to fetch (default: 200)")
    args = parser.parse_args()

    # --- Liquidation monitor mode ---
    if args.monitor:
        monitor = LiqAlert(proximity_pct=0.5)
        monitor.monitor(interval_seconds=30)
        return

    # --- One-shot liq check ---
    if args.check_liq:
        run_single_check(args.symbol)
        return

    # --- Full analysis ---
    print(f"[INFO] Fetching {args.symbol} {args.tf} data...")
    df = fetch_ohlcv(symbol=args.symbol, interval=args.tf, limit=args.limit)

    if df.empty:
        print("[ERROR] No data returned. Check your internet connection.")
        sys.exit(1)

    levels = compute_key_levels(df)
    setup = evaluate_setup(df, levels, liq_levels=Config.MANUAL_LIQ_LEVELS)

    if not args.chart_only:
        print_report(setup, levels)

    if not args.no_chart:
        chart_path = plot_analysis(df, setup, levels)
        print(f"[INFO] Chart saved to: {chart_path}")


if __name__ == "__main__":
    main()
