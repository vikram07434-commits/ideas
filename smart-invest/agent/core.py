"""
Smart Invest Agent — Core Engine
Handles: signal processing, risk checks, order execution
"""

import time
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
from config import (
    CAPITAL, CIRCUIT_BREAKERS, POSITION_LIMITS,
    TRADING_BLACKOUT, ALLOWED_STOCKS, ALLOWED_CRYPTO, FORBIDDEN
)


class SystemState(Enum):
    ACTIVE = "active"
    PAPER = "paper"
    HALTED = "halted"
    KILLED = "killed"


class AssetClass(Enum):
    STOCK = "stock"
    ETF = "etf"
    CRYPTO = "crypto"


@dataclass
class Position:
    symbol: str
    asset_class: AssetClass
    quantity: float
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    current_price: float = 0.0

    @property
    def pnl(self) -> float:
        return (self.current_price - self.entry_price) * self.quantity

    @property
    def pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0
        return (self.current_price - self.entry_price) / self.entry_price


@dataclass
class TradeSignal:
    symbol: str
    asset_class: AssetClass
    action: str  # "buy" or "sell"
    price: float
    reason: str
    confidence: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RiskEngine:
    """Enforces RISK-PROTOCOLS.md — the bible. No exceptions."""

    def __init__(self, portfolio_value: float):
        self.portfolio_value = portfolio_value
        self.peak_value = portfolio_value
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.monthly_pnl = 0.0
        self.last_loss_time: Optional[datetime] = None
        self.trades_after_loss = 0
        self.state = SystemState.PAPER  # ALWAYS start paper

    def check_signal(self, signal: TradeSignal, positions: list[Position]) -> tuple[bool, str]:
        """Returns (approved, reason). If not approved, trade MUST NOT execute."""

        # Kill switch check
        if self.state == SystemState.KILLED:
            return False, "KILL SWITCH ACTIVE — no trading until manual restart"

        if self.state == SystemState.HALTED:
            return False, "System halted — waiting for cooldown to expire"

        # Forbidden asset check
        if signal.symbol in FORBIDDEN:
            return False, f"FORBIDDEN: {signal.symbol} is on the banned list"

        # Asset whitelist check
        if signal.asset_class == AssetClass.CRYPTO and signal.symbol not in ALLOWED_CRYPTO:
            return False, f"BLOCKED: {signal.symbol} not in allowed crypto list"

        if signal.asset_class in (AssetClass.STOCK, AssetClass.ETF) and signal.symbol not in ALLOWED_STOCKS:
            return False, f"BLOCKED: {signal.symbol} not in allowed stocks list"

        # Position size check (max 5% of portfolio per position)
        position_value = signal.price * self._calculate_quantity(signal)
        max_position = self.portfolio_value * POSITION_LIMITS["single_position_max_pct"]
        if position_value > max_position:
            return False, f"POSITION TOO LARGE: ₹{position_value:.0f} > max ₹{max_position:.0f}"

        # Concentration check
        asset_class_exposure = sum(
            p.current_price * p.quantity for p in positions
            if p.asset_class == signal.asset_class
        )
        max_class = self.portfolio_value * POSITION_LIMITS["single_asset_class_max_pct"]
        if asset_class_exposure + position_value > max_class:
            return False, f"ASSET CLASS LIMIT: {signal.asset_class.value} exposure would exceed 40%"

        # Trading blackout check
        if signal.asset_class != AssetClass.CRYPTO:
            if not self._is_trading_hours_safe():
                return False, "BLACKOUT: within 15min of market open/close"

        # Anti-revenge trading (Chapter 7.1)
        if self.last_loss_time:
            hours_since_loss = (datetime.utcnow() - self.last_loss_time).total_seconds() / 3600
            if hours_since_loss < 24:
                return False, f"COOLDOWN: {24 - hours_since_loss:.1f}h remaining after loss"

        # Anti-FOMO check would go here (needs price history)

        # Circuit breaker checks
        if abs(self.daily_pnl) >= self.portfolio_value * CIRCUIT_BREAKERS["daily_loss_pct"]:
            self.state = SystemState.HALTED
            return False, "CIRCUIT BREAKER: daily loss limit hit — halted 24h"

        return True, "APPROVED"

    def update_pnl(self, pnl_change: float):
        """Update running P&L and check circuit breakers."""
        self.daily_pnl += pnl_change
        self.weekly_pnl += pnl_change
        self.monthly_pnl += pnl_change
        self.portfolio_value += pnl_change

        if self.portfolio_value > self.peak_value:
            self.peak_value = self.portfolio_value

        # Drawdown check
        drawdown = (self.peak_value - self.portfolio_value) / self.peak_value
        if drawdown >= CIRCUIT_BREAKERS["total_drawdown_pct"]:
            self.state = SystemState.KILLED
            self._trigger_kill_switch()

        if pnl_change < 0:
            self.last_loss_time = datetime.utcnow()
            self.trades_after_loss = 0

    def _trigger_kill_switch(self):
        """KILL SWITCH — close everything, alert everything."""
        # TODO: Close all positions at market
        # TODO: Cancel all pending orders
        # TODO: Send Telegram alert
        # TODO: Send SMS alert
        # TODO: Log the event
        print("🚨 KILL SWITCH TRIGGERED — ALL TRADING STOPPED")

    def _is_trading_hours_safe(self) -> bool:
        """Check if we're outside the 15-min blackout zones."""
        now = datetime.now()
        market_open = now.replace(hour=9, minute=15, second=0)
        market_close = now.replace(hour=15, minute=30, second=0)

        buffer = timedelta(minutes=TRADING_BLACKOUT["market_open_buffer_min"])

        if now < market_open + buffer:
            return False
        if now > market_close - buffer:
            return False
        return True

    def _calculate_quantity(self, signal: TradeSignal) -> float:
        """Calculate position size respecting all limits."""
        max_value = self.portfolio_value * POSITION_LIMITS["single_position_max_pct"]
        return max_value / signal.price if signal.price > 0 else 0


class AuditLog:
    """Immutable audit trail — RISK-PROTOCOLS Chapter 6.3"""

    def __init__(self, log_file: str = "audit.jsonl"):
        self.log_file = log_file

    def record(self, event_type: str, actor: str, before: dict, after: dict, reason: str):
        import json
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "actor": actor,
            "before": before,
            "after": after,
            "reason": reason,
        }
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")


class SmartInvestAgent:
    """Main agent — orchestrates signals, risk, and execution."""

    def __init__(self):
        self.risk_engine = RiskEngine(CAPITAL)
        self.positions: list[Position] = []
        self.audit = AuditLog()
        self.state = SystemState.PAPER

    def process_signal(self, signal: TradeSignal):
        """Process an incoming trade signal through the full pipeline."""

        # Step 1: Risk check (non-negotiable)
        approved, reason = self.risk_engine.check_signal(signal, self.positions)

        self.audit.record(
            event_type="signal_received",
            actor="system",
            before={"positions": len(self.positions)},
            after={"approved": approved, "reason": reason},
            reason=signal.reason,
        )

        if not approved:
            print(f"❌ REJECTED: {signal.symbol} {signal.action} — {reason}")
            return

        # Step 2: Execute (paper or live)
        if self.state == SystemState.PAPER:
            self._paper_execute(signal)
        else:
            self._live_execute(signal)

    def _paper_execute(self, signal: TradeSignal):
        """Simulate execution for paper trading."""
        quantity = self.risk_engine._calculate_quantity(signal)
        print(f"📝 PAPER: {signal.action.upper()} {quantity:.4f} {signal.symbol} @ ₹{signal.price:.2f}")
        print(f"   Reason: {signal.reason}")

        if signal.action == "buy":
            position = Position(
                symbol=signal.symbol,
                asset_class=signal.asset_class,
                quantity=quantity,
                entry_price=signal.price,
                entry_time=datetime.utcnow(),
                stop_loss=signal.price * 0.99,   # 1% stop (from circuit breaker)
                take_profit=signal.price * 1.05,  # 5% target (conservative)
                current_price=signal.price,
            )
            self.positions.append(position)

    def _live_execute(self, signal: TradeSignal):
        """Execute via broker API — only when NOT in paper mode."""
        # TODO: Implement Angel One SmartAPI integration
        # TODO: Implement CoinDCX API integration
        raise NotImplementedError("Live trading not yet implemented — PAPER MODE ONLY")

    def health_check(self) -> dict:
        """System health status — RISK-PROTOCOLS Chapter 5.1"""
        return {
            "state": self.state.value,
            "portfolio_value": self.risk_engine.portfolio_value,
            "peak_value": self.risk_engine.peak_value,
            "drawdown_pct": (self.risk_engine.peak_value - self.risk_engine.portfolio_value) / self.risk_engine.peak_value * 100,
            "daily_pnl": self.risk_engine.daily_pnl,
            "open_positions": len(self.positions),
            "timestamp": datetime.utcnow().isoformat(),
        }
