"""
Smart Invest Agent — Configuration
Capital: ₹50,000 (test phase)
"""

CAPITAL = 50_000  # INR total allocation
CASH_RESERVE_PCT = 0.10  # 10% always liquid

# Allocation splits
ALLOCATION = {
    "stocks": 0.50,      # ₹25,000 — Indian stocks / Nifty IT
    "crypto": 0.30,      # ₹15,000 — BTC, ETH only
    "opportunity": 0.10, # ₹5,000  — for strong signals
    "cash": 0.10,        # ₹5,000  — never touch
}

# Circuit breakers (from RISK-PROTOCOLS.md Chapter 1.3)
CIRCUIT_BREAKERS = {
    "single_trade_loss_pct": 0.01,    # 1% of portfolio → auto-close
    "daily_loss_pct": 0.02,           # 2% → halt 24h
    "weekly_loss_pct": 0.05,          # 5% → halt 7 days
    "monthly_loss_pct": 0.08,         # 8% → halt + full review
    "total_drawdown_pct": 0.15,       # 15% from peak → KILL SWITCH
}

# Position limits (from RISK-PROTOCOLS.md Chapter 1.2)
POSITION_LIMITS = {
    "single_position_max_pct": 0.05,  # 5% of portfolio per position
    "single_asset_class_max_pct": 0.40,
    "single_strategy_max_pct": 0.50,
}

# Broker configs (API keys loaded from .env)
BROKERS = {
    "angel_one": {
        "name": "Angel One SmartAPI",
        "asset_types": ["stocks", "etf"],
        "api_cost": 0,
        "min_order": 1,
    },
    "coindcx": {
        "name": "CoinDCX",
        "asset_types": ["crypto"],
        "api_cost": 0,
        "min_order": 100,  # ₹100 minimum
    },
}

# Allowed assets (start conservative — RISK-PROTOCOLS Chapter 8 Rule #4)
ALLOWED_STOCKS = [
    "NIFTYBEES",   # Nifty 50 ETF
    "BANKBEES",    # Bank Nifty ETF
    "ITBEES",      # Nifty IT ETF (AI/tech exposure)
    "GOLDBEES",    # Gold ETF (hedge)
]

ALLOWED_CRYPTO = [
    "BTC",   # Bitcoin — 15+ years history
    "ETH",   # Ethereum — 8+ years history
]

# Forbidden (until we graduate from ₹50K test phase)
FORBIDDEN = [
    "leverage",
    "margin",
    "futures",
    "options",
    "meme_coins",
    "new_tokens",     # < 6 months history
    "penny_stocks",
]

# Timing rules (from RISK-PROTOCOLS.md Chapter 3.2)
TRADING_BLACKOUT = {
    "market_open_buffer_min": 15,   # no trades first 15 min
    "market_close_buffer_min": 15,  # no trades last 15 min
}

# Alerting
ALERTS = {
    "telegram": True,
    "email": False,   # enable later
    "sms": False,     # enable later
}

# System
ENVIRONMENT = "paper"  # Start in paper trading mode ALWAYS
RECONCILIATION_INTERVAL_SEC = 300  # 5 minutes
HEALTH_CHECK_INTERVAL_SEC = 60     # 1 minute
