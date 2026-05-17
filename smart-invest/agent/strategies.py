"""
Smart Invest Agent — Signal Strategies
Each strategy generates buy/sell signals based on market data.
All strategies must pass RISK-PROTOCOLS before execution.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from core import TradeSignal, AssetClass


class MomentumStrategy:
    """
    Simple momentum: buy when price crosses above 20-day moving average,
    sell when it crosses below. Battle-tested, well-understood.

    Why this works for ₹50K test phase:
    - No leverage needed
    - Works on ETFs and crypto
    - Clear entry/exit rules (no emotion)
    - Backtestable with free data
    """

    def __init__(self, lookback_days: int = 20):
        self.lookback_days = lookback_days
        self.price_history: dict[str, list[float]] = {}

    def update_price(self, symbol: str, price: float):
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(price)
        # Keep only what we need
        self.price_history[symbol] = self.price_history[symbol][-(self.lookback_days + 5):]

    def generate_signal(self, symbol: str, asset_class: AssetClass, current_price: float) -> Optional[TradeSignal]:
        history = self.price_history.get(symbol, [])

        if len(history) < self.lookback_days:
            return None  # Not enough data yet

        ma = sum(history[-self.lookback_days:]) / self.lookback_days
        prev_price = history[-2] if len(history) >= 2 else current_price

        # Buy signal: price crosses ABOVE moving average
        if prev_price <= ma and current_price > ma:
            return TradeSignal(
                symbol=symbol,
                asset_class=asset_class,
                action="buy",
                price=current_price,
                reason=f"Momentum: price {current_price:.2f} crossed above {self.lookback_days}d MA {ma:.2f}",
                confidence=0.6,
            )

        # Sell signal: price crosses BELOW moving average
        if prev_price >= ma and current_price < ma:
            return TradeSignal(
                symbol=symbol,
                asset_class=asset_class,
                action="sell",
                price=current_price,
                reason=f"Momentum: price {current_price:.2f} crossed below {self.lookback_days}d MA {ma:.2f}",
                confidence=0.6,
            )

        return None


class MeanReversionStrategy:
    """
    Buy when price drops significantly below average (oversold),
    sell when it reverts to mean. Works well for range-bound assets.

    Entry: price < MA - 2*stddev (oversold)
    Exit: price returns to MA (mean reversion)
    """

    def __init__(self, lookback_days: int = 20, entry_std: float = 2.0):
        self.lookback_days = lookback_days
        self.entry_std = entry_std
        self.price_history: dict[str, list[float]] = {}

    def update_price(self, symbol: str, price: float):
        if symbol not in self.price_history:
            self.price_history[symbol] = []
        self.price_history[symbol].append(price)
        self.price_history[symbol] = self.price_history[symbol][-(self.lookback_days + 5):]

    def generate_signal(self, symbol: str, asset_class: AssetClass, current_price: float) -> Optional[TradeSignal]:
        history = self.price_history.get(symbol, [])

        if len(history) < self.lookback_days:
            return None

        prices = history[-self.lookback_days:]
        ma = sum(prices) / len(prices)
        variance = sum((p - ma) ** 2 for p in prices) / len(prices)
        std = variance ** 0.5

        if std == 0:
            return None

        lower_band = ma - (self.entry_std * std)
        upper_band = ma + (self.entry_std * std)

        # Buy when oversold
        if current_price < lower_band:
            return TradeSignal(
                symbol=symbol,
                asset_class=asset_class,
                action="buy",
                price=current_price,
                reason=f"Mean reversion: price {current_price:.2f} below lower band {lower_band:.2f}",
                confidence=0.65,
            )

        # Sell when reverted above upper band
        if current_price > upper_band:
            return TradeSignal(
                symbol=symbol,
                asset_class=asset_class,
                action="sell",
                price=current_price,
                reason=f"Mean reversion: price {current_price:.2f} above upper band {upper_band:.2f}",
                confidence=0.6,
            )

        return None


class DCAStrategy:
    """
    Dollar Cost Averaging — systematic buying at fixed intervals.
    Not sexy, but mathematically proven to reduce timing risk.

    For ₹50K: invest ₹2,500 per week into target assets.
    This ensures we don't go all-in at the wrong time.
    """

    def __init__(self, interval_days: int = 7, amount_per_interval: float = 2500):
        self.interval_days = interval_days
        self.amount = amount_per_interval
        self.last_buy: dict[str, datetime] = {}

    def generate_signal(self, symbol: str, asset_class: AssetClass, current_price: float) -> Optional[TradeSignal]:
        now = datetime.utcnow()
        last = self.last_buy.get(symbol)

        if last and (now - last) < timedelta(days=self.interval_days):
            return None  # Not time yet

        self.last_buy[symbol] = now

        return TradeSignal(
            symbol=symbol,
            asset_class=asset_class,
            action="buy",
            price=current_price,
            reason=f"DCA: scheduled buy ₹{self.amount} of {symbol}",
            confidence=0.8,  # High confidence — DCA is strategy-agnostic
        )
