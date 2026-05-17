"""
Smart Invest Agent — Main Entry Point
Runs the agent loop: fetch data → generate signals → risk check → execute
"""

import time
import signal
import sys
from datetime import datetime
from core import SmartInvestAgent, AssetClass, SystemState
from strategies import MomentumStrategy, MeanReversionStrategy, DCAStrategy
from brokers import AngelOneBroker, CoinDCXBroker
from config import ENVIRONMENT, HEALTH_CHECK_INTERVAL_SEC, ALLOWED_STOCKS, ALLOWED_CRYPTO


class Agent:
    def __init__(self):
        self.agent = SmartInvestAgent()
        self.momentum = MomentumStrategy(lookback_days=20)
        self.mean_reversion = MeanReversionStrategy(lookback_days=20)
        self.dca = DCAStrategy(interval_days=7, amount_per_interval=2500)

        # Brokers
        self.stock_broker = AngelOneBroker()
        self.crypto_broker = CoinDCXBroker()

        # State
        self.running = False

        # Graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def start(self):
        print("=" * 60)
        print("  SMART INVEST AGENT")
        print(f"  Mode: {ENVIRONMENT.upper()}")
        print(f"  Capital: ₹{self.agent.risk_engine.portfolio_value:,.0f}")
        print(f"  Started: {datetime.utcnow().isoformat()}Z")
        print("=" * 60)

        if ENVIRONMENT != "paper":
            print("\n⚠️  LIVE MODE — connecting to brokers...")
            if not self.stock_broker.connect():
                print("❌ Angel One connection failed — falling back to PAPER")
                self.agent.state = SystemState.PAPER
            if not self.crypto_broker.connect():
                print("❌ CoinDCX connection failed — falling back to PAPER")
                self.agent.state = SystemState.PAPER
        else:
            print("\n📝 PAPER MODE — no real money at risk")
            self.agent.state = SystemState.PAPER

        self.running = True
        self._run_loop()

    def _run_loop(self):
        """Main agent loop."""
        cycle = 0
        while self.running:
            cycle += 1
            print(f"\n--- Cycle {cycle} | {datetime.utcnow().strftime('%H:%M:%S')} UTC ---")

            try:
                # Fetch prices and update strategies
                self._update_prices()

                # Generate and process signals
                self._process_signals()

                # Health check
                health = self.agent.health_check()
                if health["drawdown_pct"] > 10:
                    print(f"⚠️  DRAWDOWN WARNING: {health['drawdown_pct']:.1f}%")

                # Wait for next cycle
                time.sleep(HEALTH_CHECK_INTERVAL_SEC)

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
                time.sleep(30)  # Brief pause before retry

    def _update_prices(self):
        """Fetch current prices for all watched assets."""
        for symbol in ALLOWED_STOCKS:
            if ENVIRONMENT == "paper":
                price = self._get_paper_price(symbol)
            else:
                price = self.stock_broker.get_price(symbol)

            if price > 0:
                self.momentum.update_price(symbol, price)
                self.mean_reversion.update_price(symbol, price)

        for symbol in ALLOWED_CRYPTO:
            if ENVIRONMENT == "paper":
                price = self._get_paper_price(symbol)
            else:
                price = self.crypto_broker.get_price(symbol)

            if price > 0:
                self.momentum.update_price(symbol, price)
                self.mean_reversion.update_price(symbol, price)

    def _process_signals(self):
        """Run all strategies and process signals through risk engine."""

        # Stock signals
        for symbol in ALLOWED_STOCKS:
            prices = self.momentum.price_history.get(symbol, [])
            if not prices:
                continue
            current = prices[-1]

            for strategy in [self.momentum, self.mean_reversion, self.dca]:
                sig = strategy.generate_signal(symbol, AssetClass.ETF, current)
                if sig:
                    self.agent.process_signal(sig)

        # Crypto signals
        for symbol in ALLOWED_CRYPTO:
            prices = self.momentum.price_history.get(symbol, [])
            if not prices:
                continue
            current = prices[-1]

            for strategy in [self.momentum, self.mean_reversion, self.dca]:
                sig = strategy.generate_signal(symbol, AssetClass.CRYPTO, current)
                if sig:
                    self.agent.process_signal(sig)

    def _get_paper_price(self, symbol: str) -> float:
        """Get price for paper trading (uses free API, no auth needed)."""
        import requests

        try:
            if symbol in ALLOWED_CRYPTO:
                resp = requests.get(
                    f"https://api.coindcx.com/exchange/ticker",
                    timeout=5
                )
                tickers = resp.json()
                pair = f"{symbol}INR"
                ticker = next((t for t in tickers if t["market"] == pair), None)
                return float(ticker["last_price"]) if ticker else 0.0
            else:
                # For Indian ETFs in paper mode, use a free price source
                # NSE doesn't have a free API, so we'll use a workaround
                # TODO: integrate with a free Indian stock price API
                return 0.0
        except Exception:
            return 0.0

    def _shutdown(self, signum, frame):
        """Graceful shutdown — log and stop."""
        print("\n\n🛑 SHUTTING DOWN — saving state...")
        self.running = False
        self.agent.audit.record(
            event_type="shutdown",
            actor="system",
            before={"state": self.agent.state.value},
            after={"state": "stopped"},
            reason="Signal received" if signum else "Manual stop",
        )
        print("✅ State saved. Goodbye.")
        sys.exit(0)


if __name__ == "__main__":
    agent = Agent()
    agent.start()
