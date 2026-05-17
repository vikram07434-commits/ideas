"""
Smart Invest Agent — Persistence Layer
SQLite storage for positions, trades, P&L, and system state.
Survives restarts. Single source of truth for local state.
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional
from core import Position, AssetClass, SystemState


DB_PATH = "smart_invest.db"


class Database:
    """SQLite persistence — positions, trades, and state survive restarts."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                entry_time TEXT NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                current_price REAL DEFAULT 0,
                status TEXT DEFAULT 'open'
            );

            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                asset_class TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                reason TEXT,
                pnl REAL DEFAULT 0,
                status TEXT DEFAULT 'executed'
            );

            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                portfolio_value REAL NOT NULL,
                daily_pnl REAL NOT NULL,
                peak_value REAL NOT NULL,
                drawdown_pct REAL NOT NULL,
                open_positions INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS system_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        self.conn.commit()

    # --- Positions ---

    def save_position(self, p: Position) -> int:
        cur = self.conn.execute("""
            INSERT INTO positions (symbol, asset_class, quantity, entry_price,
                entry_time, stop_loss, take_profit, current_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')
        """, (p.symbol, p.asset_class.value, p.quantity, p.entry_price,
              p.entry_time.isoformat(), p.stop_loss, p.take_profit, p.current_price))
        self.conn.commit()
        return cur.lastrowid

    def close_position(self, symbol: str):
        self.conn.execute(
            "UPDATE positions SET status = 'closed' WHERE symbol = ? AND status = 'open'",
            (symbol,))
        self.conn.commit()

    def update_position_price(self, symbol: str, price: float):
        self.conn.execute(
            "UPDATE positions SET current_price = ? WHERE symbol = ? AND status = 'open'",
            (price, symbol))
        self.conn.commit()

    def load_open_positions(self) -> list[Position]:
        rows = self.conn.execute(
            "SELECT * FROM positions WHERE status = 'open'"
        ).fetchall()

        positions = []
        for r in rows:
            positions.append(Position(
                symbol=r["symbol"],
                asset_class=AssetClass(r["asset_class"]),
                quantity=r["quantity"],
                entry_price=r["entry_price"],
                entry_time=datetime.fromisoformat(r["entry_time"]),
                stop_loss=r["stop_loss"],
                take_profit=r["take_profit"],
                current_price=r["current_price"],
            ))
        return positions

    # --- Trades ---

    def record_trade(self, symbol: str, asset_class: str, action: str,
                     quantity: float, price: float, reason: str, pnl: float = 0):
        self.conn.execute("""
            INSERT INTO trades (timestamp, symbol, asset_class, action, quantity, price, reason, pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (datetime.utcnow().isoformat(), symbol, asset_class, action, quantity, price, reason, pnl))
        self.conn.commit()

    def get_recent_trades(self, limit: int = 10) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_trade_stats(self) -> dict:
        total = self.conn.execute("SELECT COUNT(*) FROM trades WHERE action='sell'").fetchone()[0]
        wins = self.conn.execute("SELECT COUNT(*) FROM trades WHERE action='sell' AND pnl > 0").fetchone()[0]
        return {
            "total_trades": total,
            "winning_trades": wins,
            "win_rate": wins / total * 100 if total > 0 else 0,
        }

    # --- Daily Snapshots ---

    def save_daily_snapshot(self, portfolio_value: float, daily_pnl: float,
                            peak_value: float, drawdown_pct: float, open_positions: int):
        date = datetime.utcnow().strftime("%Y-%m-%d")
        self.conn.execute("""
            INSERT OR REPLACE INTO daily_snapshots (date, portfolio_value, daily_pnl,
                peak_value, drawdown_pct, open_positions)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date, portfolio_value, daily_pnl, peak_value, drawdown_pct, open_positions))
        self.conn.commit()

    def get_snapshots(self, days: int = 30) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM daily_snapshots ORDER BY date DESC LIMIT ?", (days,)
        ).fetchall()
        return [dict(r) for r in rows]

    # --- System State ---

    def save_state(self, key: str, value):
        self.conn.execute("""
            INSERT OR REPLACE INTO system_state (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, json.dumps(value), datetime.utcnow().isoformat()))
        self.conn.commit()

    def load_state(self, key: str, default=None):
        row = self.conn.execute(
            "SELECT value FROM system_state WHERE key = ?", (key,)
        ).fetchone()
        if row:
            return json.loads(row["value"])
        return default

    def save_risk_state(self, risk_engine):
        """Persist risk engine state across restarts."""
        state = {
            "portfolio_value": risk_engine.portfolio_value,
            "peak_value": risk_engine.peak_value,
            "daily_pnl": risk_engine.daily_pnl,
            "weekly_pnl": risk_engine.weekly_pnl,
            "monthly_pnl": risk_engine.monthly_pnl,
            "state": risk_engine.state.value,
        }
        self.save_state("risk_engine", state)

    def load_risk_state(self) -> Optional[dict]:
        return self.load_state("risk_engine")

    def close(self):
        self.conn.close()
