"""
Unit tests for SOL Trading Analyzer core modules.
Run with: python -m pytest tests/ -v
"""

import sys
import os
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from analyzer import compute_indicators, compute_key_levels, evaluate_setup
from alerts import LiqAlert


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_dummy_df(n: int = 250, base_price: float = 88.0) -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame for testing."""
    np.random.seed(42)
    closes = base_price + np.cumsum(np.random.randn(n) * 0.5)
    highs = closes + np.random.rand(n) * 0.5
    lows = closes - np.random.rand(n) * 0.5
    opens = closes + np.random.randn(n) * 0.2
    volumes = np.random.rand(n) * 1_000_000 + 500_000

    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=n, freq="15min"),
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })
    return df


# ─── Indicator Tests ──────────────────────────────────────────────────────────

class TestComputeIndicators:
    def setup_method(self):
        self.df = compute_indicators(make_dummy_df())

    def test_rsi_range(self):
        rsi = self.df["rsi"].dropna()
        assert (rsi >= 0).all() and (rsi <= 100).all(), "RSI must be 0–100"

    def test_bollinger_bands_order(self):
        valid = self.df.dropna(subset=["bb_upper", "bb_lower", "sma_20"])
        assert (valid["bb_upper"] >= valid["sma_20"]).all(), "BB upper must be >= SMA20"
        assert (valid["sma_20"] >= valid["bb_lower"]).all(), "SMA20 must be >= BB lower"

    def test_macd_columns_exist(self):
        for col in ["macd", "macd_signal", "macd_hist"]:
            assert col in self.df.columns, f"Missing column: {col}"

    def test_adx_positive(self):
        adx = self.df["adx"].dropna()
        assert (adx >= 0).all(), "ADX must be non-negative"

    def test_stoch_range(self):
        stoch = self.df["stoch_k"].dropna()
        assert (stoch >= 0).all() and (stoch <= 100).all(), "Stoch must be 0–100"

    def test_sma_columns_exist(self):
        for col in ["sma_20", "sma_50", "sma_200"]:
            assert col in self.df.columns

    def test_no_all_nan_columns(self):
        key_cols = ["rsi", "macd", "stoch_k", "adx", "bb_upper"]
        for col in key_cols:
            assert not self.df[col].isna().all(), f"{col} is all NaN"


# ─── Key Level Tests ──────────────────────────────────────────────────────────

class TestComputeKeyLevels:
    def setup_method(self):
        raw = make_dummy_df()
        self.df = compute_indicators(raw)
        self.levels = compute_key_levels(self.df)

    def test_returns_dict_with_keys(self):
        assert "resistance" in self.levels
        assert "support" in self.levels

    def test_resistance_above_support(self):
        if self.levels["resistance"] and self.levels["support"]:
            assert min(self.levels["resistance"]) > min(self.levels["support"]), \
                "Resistance should generally be above support"

    def test_max_5_levels_each(self):
        assert len(self.levels["resistance"]) <= 5
        assert len(self.levels["support"]) <= 5

    def test_levels_are_floats(self):
        for r in self.levels["resistance"]:
            assert isinstance(r, float)
        for s in self.levels["support"]:
            assert isinstance(s, float)


# ─── Setup Evaluation Tests ───────────────────────────────────────────────────

class TestEvaluateSetup:
    def setup_method(self):
        raw = make_dummy_df()
        self.df = compute_indicators(raw)
        self.levels = compute_key_levels(self.df)
        self.setup = evaluate_setup(self.df, self.levels)

    def test_bias_valid(self):
        assert self.setup["bias"] in ("BULLISH", "BEARISH", "NEUTRAL")

    def test_trigger_above_invalidation(self):
        assert self.setup["trigger"] > self.setup["invalidation"], \
            "Trigger must be above invalidation"

    def test_target_above_trigger(self):
        assert self.setup["target"] > self.setup["trigger"], \
            "Target must be above trigger"

    def test_required_keys_present(self):
        required = ["price", "bias", "rsi", "macd_bullish", "stoch_k",
                    "adx", "trigger", "invalidation", "target", "timestamp"]
        for key in required:
            assert key in self.setup, f"Missing key: {key}"

    def test_rsi_range(self):
        assert 0 <= self.setup["rsi"] <= 100


# ─── Alert Tests ──────────────────────────────────────────────────────────────

class TestLiqAlert:
    def setup_method(self):
        self.monitor = LiqAlert(proximity_pct=1.0)

    def test_alert_triggered_near_level(self):
        # Price very close to long liq level ($87)
        alerts = self.monitor.check_proximity(87.20)
        assert len(alerts) > 0, "Should trigger alert near $87"

    def test_no_alert_far_from_level(self):
        alerts = self.monitor.check_proximity(92.00)
        assert len(alerts) == 0, "No alert expected far from liq levels"

    def test_cooldown_prevents_repeat(self):
        self.monitor.check_proximity(87.10)  # First trigger
        alerts = self.monitor.check_proximity(87.10)  # Immediate repeat
        assert len(alerts) == 0, "Cooldown should prevent repeated alerts"

    def test_format_alert_contains_price(self):
        alerts = self.monitor.check_proximity(87.20)
        if alerts:
            msg = self.monitor.format_alert(alerts[0])
            assert "$87" in msg

    def test_alert_has_required_fields(self):
        alerts = self.monitor.check_proximity(87.10)
        if alerts:
            required = ["type", "price", "liq_price", "size_b", "distance_pct",
                        "direction", "timestamp"]
            for field in required:
                assert field in alerts[0], f"Missing field: {field}"
