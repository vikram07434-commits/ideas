"""
Smart Invest Agent — Main Entry Point
Runs the agent loop: fetch data → generate signals → risk check → execute
Integrates: data feeds, scoring, risk, telegram, dashboard, persistence
"""

import time
import signal
import sys
import threading
from datetime import datetime
from core import SmartInvestAgent, AssetClass, SystemState, TradeSignal
from strategies import MomentumStrategy, MeanReversionStrategy, DCAStrategy
from data_feeds import YahooFinanceFeed, CoinDCXFeed, DataAggregator
from telegram_bot import TelegramBot
from persistence import Database
from config import (
    ENVIRONMENT, ALLOWED_STOCKS, ALLOWED_CRYPTO, CAPITAL
)

PRICE_FETCH_INTERVAL = 300  # 5 minutes between price fetches (avoid API abuse)
SIGNAL_PROCESS_INTERVAL = 300  # 5 minutes between signal processing
TELEGRAM_POLL_INTERVAL = 10  # 10 seconds between Telegram checks


class Agent:
    def __init__(self):
        # Persistence
        self.db = Database()

        # Telegram
        self.telegram = TelegramBot()

        # Core agent with telegram wired in
        self.agent = SmartInvestAgent()
        self.agent.risk_engine.telegram = self.telegram

        # Load persisted state
        self._restore_state()

        # Strategies
        self.momentum = MomentumStrategy(lookback_days=20)
        self.mean_reversion = MeanReversionStrategy(lookback_days=20)
        self.dca = DCAStrategy(interval_days=7, amount_per_interval=2500)

        # Data feeds
        self.data = DataAggregator()

        # Timing
        self.last_price_fetch = 0
        self.last_signal_process = 0
        self.last_telegram_poll = 0

        # State
        self.running = False

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _restore_state(self):
        """Load positions and risk state from SQLite."""
        saved_positions = self.db.load_open_positions()
        if saved_positions:
            self.agent.positions = saved_positions
            print(f"  Restored {len(saved_positions)} open positions from database")

        risk_state = self.db.load_risk_state()
        if risk_state:
            self.agent.risk_engine.portfolio_value = risk_state["portfolio_value"]
            self.agent.risk_engine.peak_value = risk_state["peak_value"]
            self.agent.risk_engine.daily_pnl = risk_state["daily_pnl"]
            self.agent.risk_engine.weekly_pnl = risk_state["weekly_pnl"]
            self.agent.risk_engine.monthly_pnl = risk_state["monthly_pnl"]
            state_val = risk_state.get("state", "paper")
            self.agent.risk_engine.state = SystemState(state_val)
            print(f"  Restored risk state: ₹{risk_state['portfolio_value']:,.0f}, state={state_val}")

    def start(self):
        print("=" * 60)
        print("  SMART INVEST AGENT")
        print(f"  Mode: {ENVIRONMENT.upper()}")
        print(f"  Capital: ₹{self.agent.risk_engine.portfolio_value:,.0f}")
        print(f"  Positions: {len(self.agent.positions)}")
        print(f"  Started: {datetime.utcnow().isoformat()}Z")
        print("=" * 60)

        if ENVIRONMENT != "paper":
            print("\n⚠️  LIVE MODE — not yet supported, falling back to PAPER")

        print("\n📝 PAPER MODE — no real money at risk")
        self.agent.state = SystemState.PAPER

        # Start dashboard in background thread
        self._start_dashboard_thread()

        # Notify via Telegram
        self.telegram.send("🟢 Smart Invest Agent started (paper mode)", "success")

        self.running = True
        self._run_loop()

    def _start_dashboard_thread(self):
        """Start Flask dashboard in a daemon thread."""
        try:
            from dashboard import start_dashboard
            thread = threading.Thread(
                target=start_dashboard,
                args=(self.agent,),
                daemon=True,
            )
            thread.start()
            print("  Dashboard: http://127.0.0.1:5050")
        except Exception as e:
            print(f"  Dashboard failed to start: {e}")

    def _run_loop(self):
        """Main agent loop — fetch prices, process signals, handle commands."""
        cycle = 0
        while self.running:
            cycle += 1
            now = time.time()

            try:
                # Fetch prices (every 5 minutes)
                if now - self.last_price_fetch >= PRICE_FETCH_INTERVAL:
                    self._update_prices()
                    self.last_price_fetch = now

                # Process signals (every 5 minutes, offset from price fetch)
                if now - self.last_signal_process >= SIGNAL_PROCESS_INTERVAL:
                    if self.last_price_fetch > 0:  # Only after first price fetch
                        self._process_signals()
                        self.last_signal_process = now

                # Poll Telegram commands (every 10 seconds)
                if now - self.last_telegram_poll >= TELEGRAM_POLL_INTERVAL:
                    self._handle_telegram()
                    self.last_telegram_poll = now

                # Update position prices and check stop-losses
                self._check_positions()

                # Persist state periodically
                self.db.save_risk_state(self.agent.risk_engine)

                # Brief sleep to avoid CPU spin
                time.sleep(5)

            except KeyboardInterrupt:
                self._shutdown(None, None)
            except Exception as e:
                print(f"❌ ERROR in cycle {cycle}: {e}")
                self.agent.audit.record(
                    event_type="error",
                    actor="system",
                    before={},
                    after={"error": str(e)},
                    reason="Unhandled exception in main loop",
                )
                time.sleep(30)

    def _update_prices(self):
        """Fetch current prices for all watched assets."""
        print(f"\n[{datetime.utcnow().strftime('%H:%M:%S')}] Fetching prices...")

        # Stocks via Yahoo Finance
        for symbol in ALLOWED_STOCKS:
            price = self.data.yahoo.get_current_price(symbol, "indian_stock")
            if price and price > 0:
                self.momentum.update_price(symbol, price)
                self.mean_reversion.update_price(symbol, price)
                self.agent.risk_engine.update_price_history(symbol, price)
                self.db.update_position_price(symbol, price)
                print(f"  {symbol}: ₹{price:.2f}")
            time.sleep(1)  # Rate limit Yahoo

        # Crypto via CoinDCX (free, no rate limit issues)
        for symbol in ALLOWED_CRYPTO:
            price = self.data.coindcx.get_current_price(symbol)
            if price and price > 0:
                self.momentum.update_price(symbol, price)
                self.mean_reversion.update_price(symbol, price)
                self.agent.risk_engine.update_price_history(symbol, price)
                self.db.update_position_price(symbol, price)
                print(f"  {symbol}: ₹{price:,.2f}")

    def _process_signals(self):
        """Run strategies and process signals through risk engine."""
        signals_generated = 0

        # Stock signals
        for symbol in ALLOWED_STOCKS:
            prices = self.momentum.price_history.get(symbol, [])
            if not prices:
                continue
            current = prices[-1]

            for strategy in [self.momentum, self.mean_reversion, self.dca]:
                sig = strategy.generate_signal(symbol, AssetClass.ETF, current)
                if sig:
                    signals_generated += 1
                    self._execute_signal(sig)

        # Crypto signals
        for symbol in ALLOWED_CRYPTO:
            prices = self.momentum.price_history.get(symbol, [])
            if not prices:
                continue
            current = prices[-1]

            for strategy in [self.momentum, self.mean_reversion, self.dca]:
                sig = strategy.generate_signal(symbol, AssetClass.CRYPTO, current)
                if sig:
                    signals_generated += 1
                    self._execute_signal(sig)

        if signals_generated > 0:
            print(f"  Processed {signals_generated} signals")

    def _execute_signal(self, signal: TradeSignal):
        """Pass signal through risk engine and execute if approved."""
        approved, reason = self.agent.risk_engine.check_signal(signal, self.agent.positions)

        self.agent.audit.record(
            event_type="signal",
            actor="system",
            before={"positions": len(self.agent.positions)},
            after={"approved": approved, "reason": reason},
            reason=signal.reason,
        )

        if not approved:
            print(f"  ❌ {signal.symbol} {signal.action}: {reason}")
            return

        # Paper execution
        quantity = self.agent.risk_engine._calculate_quantity(signal)
        print(f"  ✅ PAPER {signal.action.upper()} {quantity:.4f} {signal.symbol} @ ₹{signal.price:.2f}")

        if signal.action == "buy":
            from core import Position
            position = Position(
                symbol=signal.symbol,
                asset_class=signal.asset_class,
                quantity=quantity,
                entry_price=signal.price,
                entry_time=datetime.utcnow(),
                stop_loss=signal.price * 0.99,
                take_profit=signal.price * 1.05,
                current_price=signal.price,
            )
            self.agent.positions.append(position)
            self.db.save_position(position)
            self.db.record_trade(signal.symbol, signal.asset_class.value, "buy",
                                 quantity, signal.price, signal.reason)
            self.telegram.send_trade_alert(signal.symbol, "buy", quantity,
                                           signal.price, signal.reason)

    def _check_positions(self):
        """Check stop-losses and take-profits on open positions."""
        for pos in self.agent.positions[:]:
            if pos.current_price <= 0:
                continue

            # Stop-loss hit
            if pos.current_price <= pos.stop_loss:
                pnl = (pos.current_price - pos.entry_price) * pos.quantity
                print(f"  🛑 STOP-LOSS: {pos.symbol} @ ₹{pos.current_price:.2f} (loss: ₹{pnl:.0f})")
                self.agent.positions.remove(pos)
                self.db.close_position(pos.symbol)
                self.db.record_trade(pos.symbol, pos.asset_class.value, "sell",
                                     pos.quantity, pos.current_price, "stop-loss", pnl)
                self.agent.risk_engine.update_pnl(pnl)
                self.telegram.send_trade_alert(pos.symbol, "sell (stop-loss)",
                                               pos.quantity, pos.current_price,
                                               f"Stop-loss hit. P&L: ₹{pnl:.0f}")

            # Take-profit hit
            elif pos.current_price >= pos.take_profit:
                pnl = (pos.current_price - pos.entry_price) * pos.quantity
                print(f"  🎯 TAKE-PROFIT: {pos.symbol} @ ₹{pos.current_price:.2f} (gain: ₹{pnl:.0f})")
                self.agent.positions.remove(pos)
                self.db.close_position(pos.symbol)
                self.db.record_trade(pos.symbol, pos.asset_class.value, "sell",
                                     pos.quantity, pos.current_price, "take-profit", pnl)
                self.agent.risk_engine.update_pnl(pnl)
                self.telegram.send_trade_alert(pos.symbol, "sell (take-profit)",
                                               pos.quantity, pos.current_price,
                                               f"Target hit. P&L: ₹{pnl:.0f}")

    def _handle_telegram(self):
        """Poll and handle Telegram commands."""
        commands = self.telegram.poll_commands()
        for cmd in commands:
            response = self.telegram.handle_command(cmd["command"], cmd.get("args", []), self.agent)
            self.telegram.send(response)

    def _shutdown(self, signum, frame):
        """Graceful shutdown — persist everything."""
        print("\n\n🛑 SHUTTING DOWN...")
        self.running = False

        # Save state
        self.db.save_risk_state(self.agent.risk_engine)

        # Save daily snapshot
        health = self.agent.health_check()
        self.db.save_daily_snapshot(
            portfolio_value=health["portfolio_value"],
            daily_pnl=health["daily_pnl"],
            peak_value=health["peak_value"],
            drawdown_pct=health["drawdown_pct"],
            open_positions=health["open_positions"],
        )

        self.db.close()
        self.agent.audit.record(
            event_type="shutdown",
            actor="system",
            before={"state": self.agent.state.value},
            after={"state": "stopped"},
            reason="Signal received" if signum else "Manual stop",
        )

        self.telegram.send("🔴 Smart Invest Agent stopped", "medium")
        print("✅ State saved to database. Goodbye.")
        sys.exit(0)


if __name__ == "__main__":
    agent = Agent()
    agent.start()
