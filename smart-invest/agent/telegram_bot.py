"""
Smart Invest Agent — Telegram Bot
Alerts + manual control. Your eyes and hands into the system.

Commands:
  /status    — Portfolio value, P&L, system state
  /positions — All open positions
  /kill      — Emergency kill switch
  /pause     — Pause trading (keep positions)
  /resume    — Resume trading
  /score SYMBOL — Get score breakdown for a stock
  /history   — Last 10 trades
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional


class TelegramBot:
    """Sends alerts and receives commands via Telegram."""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = 0

    def send(self, message: str, priority: str = "normal"):
        """Send a message. Priority affects formatting."""
        if not self.token or not self.chat_id:
            print(f"[TELEGRAM OFF] {message}")
            return

        prefix = {
            "critical": "🚨 CRITICAL",
            "high": "⚠️ HIGH",
            "medium": "ℹ️",
            "normal": "",
            "success": "✅",
        }.get(priority, "")

        text = f"{prefix} {message}" if prefix else message

        try:
            requests.post(f"{self.base_url}/sendMessage", json={
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }, timeout=10)
        except Exception as e:
            print(f"Telegram send failed: {e}")

    def send_trade_alert(self, symbol: str, action: str, quantity: float,
                         price: float, reason: str):
        msg = (
            f"*{action.upper()}* {symbol}\n"
            f"Qty: {quantity:.4f}\n"
            f"Price: ₹{price:,.2f}\n"
            f"Reason: {reason}"
        )
        self.send(msg, "normal")

    def send_circuit_breaker(self, trigger: str, value: float, limit: float):
        msg = (
            f"*CIRCUIT BREAKER TRIGGERED*\n"
            f"Trigger: {trigger}\n"
            f"Value: {value:.2f}%\n"
            f"Limit: {limit:.2f}%\n"
            f"Action: Trading HALTED"
        )
        self.send(msg, "critical")

    def send_kill_switch(self, reason: str, portfolio_value: float, drawdown_pct: float):
        msg = (
            f"*🚨 KILL SWITCH ACTIVATED 🚨*\n\n"
            f"Reason: {reason}\n"
            f"Portfolio: ₹{portfolio_value:,.0f}\n"
            f"Drawdown: {drawdown_pct:.1f}%\n\n"
            f"ALL POSITIONS CLOSED\n"
            f"ALL TRADING STOPPED\n"
            f"Manual restart required after 30-day review"
        )
        self.send(msg, "critical")

    def send_daily_summary(self, portfolio_value: float, daily_pnl: float,
                           open_positions: int, best_performer: str,
                           worst_performer: str):
        pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
        msg = (
            f"*Daily Summary* {datetime.now().strftime('%d %b %Y')}\n\n"
            f"Portfolio: ₹{portfolio_value:,.0f}\n"
            f"Day P&L: {pnl_emoji} ₹{daily_pnl:,.0f} ({daily_pnl/portfolio_value*100:.2f}%)\n"
            f"Open positions: {open_positions}\n"
            f"Best: {best_performer}\n"
            f"Worst: {worst_performer}"
        )
        self.send(msg, "success" if daily_pnl >= 0 else "medium")

    def send_weekly_report(self, portfolio_value: float, weekly_pnl: float,
                           trades_executed: int, win_rate: float,
                           strategy_health: dict):
        health_text = "\n".join(f"  {k}: {v}/100" for k, v in strategy_health.items())
        msg = (
            f"*Weekly Report*\n\n"
            f"Portfolio: ₹{portfolio_value:,.0f}\n"
            f"Week P&L: ₹{weekly_pnl:,.0f}\n"
            f"Trades: {trades_executed}\n"
            f"Win rate: {win_rate:.0f}%\n\n"
            f"*Strategy Health:*\n{health_text}"
        )
        self.send(msg, "normal")

    def poll_commands(self) -> list[dict]:
        """Check for incoming commands from user."""
        if not self.token:
            return []

        try:
            resp = requests.get(f"{self.base_url}/getUpdates", params={
                "offset": self.last_update_id + 1,
                "timeout": 5,
            }, timeout=10)

            data = resp.json()
            if not data.get("ok"):
                return []

            commands = []
            for update in data.get("result", []):
                self.last_update_id = update["update_id"]
                msg = update.get("message", {})
                text = msg.get("text", "")
                if text.startswith("/"):
                    commands.append({
                        "command": text.split()[0],
                        "args": text.split()[1:],
                        "from": msg.get("from", {}).get("first_name", "Unknown"),
                    })

            return commands
        except Exception:
            return []

    def handle_command(self, command: str, args: list[str], agent) -> str:
        """Process a command and return response text."""

        if command == "/status":
            health = agent.health_check()
            return (
                f"*System Status*\n"
                f"State: {health['state']}\n"
                f"Portfolio: ₹{health['portfolio_value']:,.0f}\n"
                f"Peak: ₹{health['peak_value']:,.0f}\n"
                f"Drawdown: {health['drawdown_pct']:.1f}%\n"
                f"Daily P&L: ₹{health['daily_pnl']:,.0f}\n"
                f"Positions: {health['open_positions']}"
            )

        elif command == "/positions":
            if not agent.positions:
                return "No open positions."
            lines = []
            for p in agent.positions:
                pnl = p.pnl
                emoji = "🟢" if pnl >= 0 else "🔴"
                lines.append(f"{emoji} {p.symbol}: {p.quantity:.4f} @ ₹{p.entry_price:.2f} | P&L: ₹{pnl:.0f}")
            return "*Open Positions*\n" + "\n".join(lines)

        elif command == "/kill":
            agent.risk_engine.state = "killed"
            agent.risk_engine._trigger_kill_switch()
            return "🚨 KILL SWITCH ACTIVATED. All trading stopped."

        elif command == "/pause":
            agent.risk_engine.state = "halted"
            return "⏸️ Trading paused. Positions remain open."

        elif command == "/resume":
            agent.risk_engine.state = "active"
            return "▶️ Trading resumed."

        elif command == "/score" and args:
            symbol = args[0].upper()
            return f"Scoring {symbol}... (not yet connected to scoring engine)"

        elif command == "/history":
            return "Last 10 trades: (not yet implemented)"

        else:
            return (
                "*Available commands:*\n"
                "/status — System status\n"
                "/positions — Open positions\n"
                "/kill — Emergency stop\n"
                "/pause — Pause trading\n"
                "/resume — Resume trading\n"
                "/score SYMBOL — Score a stock\n"
                "/history — Recent trades"
            )
