"""
Liquidation Level Alert System
Monitors price proximity to key liquidation clusters and triggers alerts.
"""

import time
import requests
from datetime import datetime
from config import Config


class LiqAlert:
    """
    Monitors SOL price and fires alerts when price approaches
    known liquidation clusters.
    """

    def __init__(self, proximity_pct: float = 0.5):
        """
        Args:
            proximity_pct: Alert when price is within this % of a liq level
        """
        self.proximity_pct = proximity_pct / 100
        self._last_alert: dict[str, float] = {}
        self.liq_levels = Config.MANUAL_LIQ_LEVELS

    def get_current_price(self, symbol: str = "SOLUSDT") -> float:
        """Fetch latest mark price from Binance Futures."""
        url = f"{Config.BASE_URL}/fapi/v1/ticker/price"
        try:
            resp = requests.get(url, params={"symbol": symbol}, timeout=5)
            resp.raise_for_status()
            return float(resp.json()["price"])
        except Exception as e:
            print(f"[ERROR] Price fetch failed: {e}")
            return 0.0

    def check_proximity(self, price: float) -> list[dict]:
        """
        Check if current price is near any liquidation cluster.

        Returns:
            List of triggered alerts with level info
        """
        now = time.time()
        triggered = []

        for key, level in self.liq_levels.items():
            liq_price = level["price"]
            size_b = level["size_b"]
            distance = abs(price - liq_price) / liq_price

            if distance <= self.proximity_pct:
                # Cooldown check
                last = self._last_alert.get(key, 0)
                if now - last < Config.ALERT_COOLDOWN_SECONDS:
                    continue

                self._last_alert[key] = now
                direction = "BELOW" if liq_price < price else "ABOVE"
                liq_type = "LONG LIQ 🟠" if key == "long_liq" else "SHORT LIQ 🟣"

                alert = {
                    "type": liq_type,
                    "price": price,
                    "liq_price": liq_price,
                    "size_b": size_b,
                    "distance_pct": round(distance * 100, 3),
                    "direction": direction,
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                }
                triggered.append(alert)

        return triggered

    def format_alert(self, alert: dict) -> str:
        """Format alert for console/log output."""
        return (
            f"\n{'='*55}\n"
            f"⚠️  LIQUIDATION PROXIMITY ALERT\n"
            f"{'='*55}\n"
            f"  Type       : {alert['type']}\n"
            f"  Current    : ${alert['price']:.4f}\n"
            f"  Liq Level  : ${alert['liq_price']:.2f} ({alert['size_b']}B)\n"
            f"  Distance   : {alert['distance_pct']}% {alert['direction']} liq zone\n"
            f"  Time       : {alert['timestamp']}\n"
            f"{'='*55}\n"
        )

    def monitor(self, interval_seconds: int = 30, max_cycles: int = None):
        """
        Continuous monitoring loop.

        Args:
            interval_seconds: How often to check (default 30s)
            max_cycles: Stop after N cycles (None = run forever)
        """
        print(f"\n[MONITOR] Starting liquidation alert monitor...")
        print(f"[MONITOR] Proximity threshold: {self.proximity_pct * 100}%")
        print(f"[MONITOR] Checking every {interval_seconds}s\n")

        cycles = 0
        while True:
            if max_cycles and cycles >= max_cycles:
                break

            price = self.get_current_price()
            if price > 0:
                alerts = self.check_proximity(price)
                if alerts:
                    for alert in alerts:
                        msg = self.format_alert(alert)
                        print(msg)
                        self._log_alert(alert)
                else:
                    ts = datetime.utcnow().strftime("%H:%M:%S")
                    liq = self.liq_levels
                    dist_long = round(abs(price - liq["long_liq"]["price"]) / price * 100, 2)
                    dist_short = round(abs(price - liq["short_liq"]["price"]) / price * 100, 2)
                    print(
                        f"[{ts}] SOL ${price:.4f} | "
                        f"Long Liq ${liq['long_liq']['price']} ({dist_long}% away) | "
                        f"Short Liq ${liq['short_liq']['price']} ({dist_short}% away)"
                    )

            cycles += 1
            time.sleep(interval_seconds)

    def _log_alert(self, alert: dict, log_file: str = "alerts/alerts.log"):
        """Append alert to log file."""
        import os
        os.makedirs("alerts", exist_ok=True)
        with open(log_file, "a") as f:
            f.write(self.format_alert(alert))
            f.write("\n")


def run_single_check(symbol: str = "SOLUSDT") -> None:
    """Quick one-shot check — useful for testing or cron jobs."""
    monitor = LiqAlert(proximity_pct=1.0)
    price = monitor.get_current_price(symbol)
    if price > 0:
        alerts = monitor.check_proximity(price)
        print(f"Current price: ${price:.4f}")
        if alerts:
            for a in alerts:
                print(monitor.format_alert(a))
        else:
            print("No liquidation proximity alerts at this time.")
