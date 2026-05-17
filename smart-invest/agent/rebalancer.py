"""
Smart Invest Agent — Portfolio Rebalancer
Keeps allocations in check. Sells overweight, buys underweight.
Tax-aware: holds >1 year for LTCG benefit where possible.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from core import Position, AssetClass, TradeSignal
from config import ALLOCATION, CAPITAL, POSITION_LIMITS


@dataclass
class RebalanceAction:
    symbol: str
    asset_class: AssetClass
    action: str  # "buy" or "sell"
    amount_inr: float
    reason: str
    tax_impact: str  # "STCG" or "LTCG" or "none"


# Indian tax rules (2026)
TAX_RULES = {
    "stcg_stock": 0.20,      # Short-term capital gains (stocks, < 1 year): 20%
    "ltcg_stock": 0.125,     # Long-term (> 1 year, > ₹1.25L gains): 12.5%
    "stcg_crypto": 0.30,     # Crypto: flat 30% regardless of holding period
    "ltcg_crypto": 0.30,     # Same for crypto — no LTCG benefit
    "ltcg_exempt_limit": 125000,  # First ₹1.25L of LTCG is tax-free
}


class PortfolioRebalancer:
    """
    Monitors allocation drift and generates corrective actions.
    Runs at: weekly cadence (per RISK-PROTOCOLS 7.4)
    """

    def __init__(self, target_allocation: dict = None):
        self.target = target_allocation or ALLOCATION
        self.drift_threshold = 0.05  # Rebalance if any class drifts > 5% from target

    def check_drift(self, positions: list[Position], cash_balance: float) -> dict:
        """Calculate current allocation vs target."""
        total_value = cash_balance + sum(p.current_price * p.quantity for p in positions)

        if total_value == 0:
            return {}

        # Calculate current allocation by asset class
        current = {"stocks": 0, "crypto": 0, "cash": cash_balance, "opportunity": 0}

        for p in positions:
            value = p.current_price * p.quantity
            if p.asset_class in (AssetClass.STOCK, AssetClass.ETF):
                current["stocks"] += value
            elif p.asset_class == AssetClass.CRYPTO:
                current["crypto"] += value

        # Convert to percentages
        current_pct = {k: v / total_value for k, v in current.items()}

        # Calculate drift
        drift = {}
        for asset_class, target_pct in self.target.items():
            actual_pct = current_pct.get(asset_class, 0)
            drift[asset_class] = {
                "target_pct": target_pct * 100,
                "actual_pct": actual_pct * 100,
                "drift_pct": (actual_pct - target_pct) * 100,
                "overweight": actual_pct > target_pct + self.drift_threshold,
                "underweight": actual_pct < target_pct - self.drift_threshold,
            }

        return drift

    def generate_rebalance_actions(self, positions: list[Position],
                                   cash_balance: float) -> list[RebalanceAction]:
        """Generate buy/sell actions to restore target allocation."""
        drift = self.check_drift(positions, cash_balance)
        total_value = cash_balance + sum(p.current_price * p.quantity for p in positions)
        actions = []

        for asset_class, d in drift.items():
            if asset_class == "cash":
                continue  # Don't "buy" cash

            if d["overweight"]:
                # Need to sell some
                excess_pct = (d["actual_pct"] - d["target_pct"]) / 100
                sell_amount = excess_pct * total_value

                # Find positions to sell (prefer LTCG-eligible)
                sell_positions = self._pick_positions_to_sell(
                    positions, asset_class, sell_amount
                )
                for symbol, amount, tax in sell_positions:
                    actions.append(RebalanceAction(
                        symbol=symbol,
                        asset_class=self._map_asset_class(asset_class),
                        action="sell",
                        amount_inr=amount,
                        reason=f"Rebalance: {asset_class} overweight by {d['drift_pct']:.1f}%",
                        tax_impact=tax,
                    ))

            elif d["underweight"]:
                # Need to buy more
                deficit_pct = (d["target_pct"] - d["actual_pct"]) / 100
                buy_amount = deficit_pct * total_value

                if buy_amount > cash_balance * 0.5:
                    buy_amount = cash_balance * 0.5  # Never use more than 50% of cash at once

                if buy_amount > 0:
                    actions.append(RebalanceAction(
                        symbol=f"[BEST_{asset_class.upper()}]",  # Scoring engine picks actual stock
                        asset_class=self._map_asset_class(asset_class),
                        action="buy",
                        amount_inr=buy_amount,
                        reason=f"Rebalance: {asset_class} underweight by {abs(d['drift_pct']):.1f}%",
                        tax_impact="none",
                    ))

        return actions

    def _pick_positions_to_sell(self, positions: list[Position],
                                asset_class: str, target_amount: float) -> list[tuple]:
        """
        Pick which positions to sell. Tax-aware:
        - Prefer selling LTCG positions (held > 1 year) over STCG
        - Prefer selling winners over losers (avoid locking in losses)
        """
        relevant = []
        for p in positions:
            if asset_class == "stocks" and p.asset_class in (AssetClass.STOCK, AssetClass.ETF):
                relevant.append(p)
            elif asset_class == "crypto" and p.asset_class == AssetClass.CRYPTO:
                relevant.append(p)

        # Sort: LTCG-eligible first (held > 1 year), then by profit (winners first)
        now = datetime.utcnow()
        one_year = timedelta(days=365)

        def sort_key(p):
            is_ltcg = (now - p.entry_time) > one_year
            profit = p.pnl_pct
            return (-int(is_ltcg), -profit)  # LTCG first, then highest profit

        relevant.sort(key=sort_key)

        sells = []
        remaining = target_amount
        for p in relevant:
            if remaining <= 0:
                break
            position_value = p.current_price * p.quantity
            sell_value = min(position_value, remaining)
            tax_type = "LTCG" if (now - p.entry_time) > one_year else "STCG"
            sells.append((p.symbol, sell_value, tax_type))
            remaining -= sell_value

        return sells

    def _map_asset_class(self, class_name: str) -> AssetClass:
        mapping = {"stocks": AssetClass.STOCK, "crypto": AssetClass.CRYPTO}
        return mapping.get(class_name, AssetClass.STOCK)

    def calculate_tax_liability(self, actions: list[RebalanceAction],
                                positions: list[Position]) -> dict:
        """Estimate tax impact of rebalance actions."""
        stcg_total = 0
        ltcg_total = 0

        for action in actions:
            if action.action != "sell":
                continue

            # Find the position
            pos = next((p for p in positions if p.symbol == action.symbol), None)
            if not pos:
                continue

            gain = action.amount_inr * pos.pnl_pct  # Approximate gain from this sale

            if pos.asset_class == AssetClass.CRYPTO:
                stcg_total += gain * TAX_RULES["stcg_crypto"]
            elif action.tax_impact == "LTCG":
                taxable = max(0, gain - TAX_RULES["ltcg_exempt_limit"])
                ltcg_total += taxable * TAX_RULES["ltcg_stock"]
            else:
                stcg_total += gain * TAX_RULES["stcg_stock"]

        return {
            "stcg_tax": stcg_total,
            "ltcg_tax": ltcg_total,
            "total_tax": stcg_total + ltcg_total,
            "note": "Estimates only — consult CA for actual filing",
        }
