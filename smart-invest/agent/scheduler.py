"""
Smart Invest Agent — Scheduler
Handles periodic tasks: market scans, rebalancing, reports.
Uses APScheduler (lightweight, no Redis dependency for ₹50K phase).
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime


class AgentScheduler:
    """
    Scheduled jobs:
    - Every 1 min: health check + price update (market hours only)
    - Every 5 min: reconcile positions with broker
    - Every day 9:30 AM: morning scan (find opportunities)
    - Every day 3:45 PM: EOD summary
    - Every Saturday 10 AM: weekly report + rebalance check
    - Every 1st of month: monthly review
    """

    def __init__(self, agent, telegram):
        self.agent = agent
        self.telegram = telegram
        self.scheduler = BackgroundScheduler()

    def setup(self):
        # Market hours price updates (Mon-Fri, 9:15 AM - 3:30 PM IST)
        self.scheduler.add_job(
            self.agent._update_prices,
            CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/1"),
            id="price_update",
            name="Price Update",
        )

        # Crypto prices (24/7)
        self.scheduler.add_job(
            self._update_crypto_prices,
            CronTrigger(minute="*/5"),
            id="crypto_update",
            name="Crypto Price Update",
        )

        # Morning scan — find today's opportunities
        self.scheduler.add_job(
            self._morning_scan,
            CronTrigger(day_of_week="mon-fri", hour=9, minute=20),
            id="morning_scan",
            name="Morning Market Scan",
        )

        # Process signals (after market settles)
        self.scheduler.add_job(
            self.agent._process_signals,
            CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/5"),
            id="signal_processing",
            name="Signal Processing",
        )

        # Reconciliation (every 5 min during market hours)
        self.scheduler.add_job(
            self._reconcile,
            CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/5"),
            id="reconciliation",
            name="Position Reconciliation",
        )

        # EOD summary
        self.scheduler.add_job(
            self._eod_summary,
            CronTrigger(day_of_week="mon-fri", hour=15, minute=45),
            id="eod_summary",
            name="End of Day Summary",
        )

        # Weekly report (Saturday 10 AM)
        self.scheduler.add_job(
            self._weekly_report,
            CronTrigger(day_of_week="sat", hour=10, minute=0),
            id="weekly_report",
            name="Weekly Report",
        )

        # Monthly review (1st of every month)
        self.scheduler.add_job(
            self._monthly_review,
            CronTrigger(day=1, hour=10, minute=0),
            id="monthly_review",
            name="Monthly Review",
        )

    def start(self):
        self.setup()
        self.scheduler.start()
        print("📅 Scheduler started — all jobs registered")

    def stop(self):
        self.scheduler.shutdown()

    def _update_crypto_prices(self):
        """Update crypto prices (runs 24/7)."""
        from config import ALLOWED_CRYPTO
        from data_feeds import CoinDCXFeed

        feed = CoinDCXFeed()
        for symbol in ALLOWED_CRYPTO:
            price = feed.get_current_price(symbol)
            if price:
                self.agent.momentum.update_price(symbol, price)
                self.agent.mean_reversion.update_price(symbol, price)

    def _morning_scan(self):
        """Scan market for today's top opportunities."""
        from scanner import UniverseScanner
        from scoring import ScoringEngine

        scanner = UniverseScanner()
        candidates = scanner.scan_ai_tech()  # Start with AI/IT stocks

        engine = ScoringEngine()
        buy_list = engine.get_buy_list(candidates, max_picks=3)

        if buy_list:
            msg = "*Morning Scan Results*\n\n"
            for score in buy_list:
                msg += f"*{score.symbol}*: {score.total_score:.0f}/100 ({score.verdict})\n"
                for r in score.reasons[:2]:
                    msg += f"  • {r}\n"
                msg += "\n"
            self.telegram.send(msg, "normal")
        else:
            self.telegram.send("Morning scan: No stocks pass BUY threshold today.", "medium")

    def _reconcile(self):
        """Verify our position records match broker's records."""
        # TODO: compare self.agent.positions with broker.get_positions()
        # If mismatch → HALT (RISK-PROTOCOLS 6.2)
        pass

    def _eod_summary(self):
        """Send end-of-day P&L summary via Telegram."""
        health = self.agent.health_check()

        best = max(self.agent.positions, key=lambda p: p.pnl_pct, default=None)
        worst = min(self.agent.positions, key=lambda p: p.pnl_pct, default=None)

        self.telegram.send_daily_summary(
            portfolio_value=health["portfolio_value"],
            daily_pnl=health["daily_pnl"],
            open_positions=health["open_positions"],
            best_performer=f"{best.symbol} (+{best.pnl_pct*100:.1f}%)" if best else "N/A",
            worst_performer=f"{worst.symbol} ({worst.pnl_pct*100:.1f}%)" if worst else "N/A",
        )

    def _weekly_report(self):
        """Weekly performance report + rebalance check."""
        from rebalancer import PortfolioRebalancer

        health = self.agent.health_check()

        # Check if rebalancing needed
        rebalancer = PortfolioRebalancer()
        drift = rebalancer.check_drift(self.agent.positions, health["portfolio_value"] * 0.1)

        needs_rebalance = any(d.get("overweight") or d.get("underweight") for d in drift.values())

        strategy_health = {
            "Momentum": 75,  # TODO: calculate real health scores
            "Mean Reversion": 70,
            "DCA": 90,
        }

        self.telegram.send_weekly_report(
            portfolio_value=health["portfolio_value"],
            weekly_pnl=self.agent.risk_engine.weekly_pnl,
            trades_executed=0,  # TODO: count from audit log
            win_rate=0,  # TODO: calculate from trade history
            strategy_health=strategy_health,
        )

        if needs_rebalance:
            self.telegram.send("📊 *Rebalance needed* — allocation has drifted >5% from target.", "medium")

        # Reset weekly counter
        self.agent.risk_engine.weekly_pnl = 0

    def _monthly_review(self):
        """Monthly review reminder."""
        self.telegram.send(
            "*Monthly Review Due*\n\n"
            "Check:\n"
            "• Are all strategies still performing?\n"
            "• Any strategy underperforming buy-and-hold?\n"
            "• Tax planning — any LTCG harvesting opportunities?\n"
            "• Regulatory changes?\n\n"
            "Reply /status for current state.",
            "medium"
        )
