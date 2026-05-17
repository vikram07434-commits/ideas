"""
Smart Invest Agent — Stock Universe Scanner
Discovers investment candidates from the entire NSE market.
Filters by market cap, volume, sector, and basic sanity checks.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from data_feeds import DataAggregator, OHLCV, Fundamentals


@dataclass
class StockCandidate:
    symbol: str
    name: str
    sector: str
    market_cap_cr: float
    avg_daily_volume: int
    current_price: float
    score: float = 0.0  # Filled by scoring engine


# NSE sectors that align with growth + safety
ALLOWED_SECTORS = [
    "Information Technology",
    "Financial Services",
    "Consumer Goods",
    "Pharma",
    "Auto",
    "Energy",
    "Metals",
    "Infrastructure",
]

# Minimum criteria to even CONSIDER a stock
MINIMUM_CRITERIA = {
    "market_cap_cr": 5000,       # > ₹5,000 Cr (no small caps)
    "avg_daily_volume": 100_000, # At least 1 lakh shares daily (liquidity)
    "min_trading_days": 250,     # At least 1 year of history (RISK-PROTOCOLS 8.4)
    "min_price": 50,             # No penny stocks
    "max_price": 50000,          # Avoid stocks where 1 share > position limit
}

# Nifty 100 components — large cap, liquid, safe starting universe
NIFTY_100 = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK",
    "LT", "HCLTECH", "AXISBANK", "ASIANPAINT", "MARUTI",
    "SUNPHARMA", "TITAN", "BAJFINANCE", "DMART", "NESTLEIND",
    "WIPRO", "ULTRACEMCO", "ONGC", "NTPC", "POWERGRID",
    "TATAMOTORS", "M&M", "ADANIENT", "TECHM", "HDFCLIFE",
    "BAJAJFINSV", "TATASTEEL", "JSWSTEEL", "INDUSINDBK", "GRASIM",
    "DIVISLAB", "DRREDDY", "CIPLA", "EICHERMOT", "BPCL",
    "COALINDIA", "SBILIFE", "BRITANNIA", "GODREJCP", "DABUR",
    "HEROMOTOCO", "APOLLOHOSP", "TATACONSUM", "UPL", "VEDL",
]

# AI/Tech focused stocks (user's interest area)
AI_TECH_STOCKS = [
    "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM",
    "LTIM", "PERSISTENT", "COFORGE", "MPHASIS", "ROUTE",
    "TATAELXSI", "KPITTECH", "HAPPSTMNDS", "ZENSAR", "BIRLASOFT",
]

# US stocks accessible via INDmoney/Vested (fractional shares)
US_AI_STOCKS = [
    "NVDA", "GOOGL", "MSFT", "META", "AMZN",
    "AMD", "TSM", "AVGO", "AAPL", "CRM",
]


class UniverseScanner:
    """Scans market to find investment candidates."""

    def __init__(self):
        self.data = DataAggregator()
        self.candidates: list[StockCandidate] = []

    def scan_nifty100(self) -> list[StockCandidate]:
        """Scan Nifty 100 stocks — safest universe for ₹50K."""
        candidates = []
        for symbol in NIFTY_100:
            candidate = self._evaluate_candidate(symbol, "indian_stock")
            if candidate:
                candidates.append(candidate)
        self.candidates = candidates
        return candidates

    def scan_ai_tech(self) -> list[StockCandidate]:
        """Scan AI/IT sector specifically."""
        candidates = []
        for symbol in AI_TECH_STOCKS:
            candidate = self._evaluate_candidate(symbol, "indian_stock")
            if candidate:
                candidates.append(candidate)
        self.candidates = candidates
        return candidates

    def scan_us_ai(self) -> list[StockCandidate]:
        """Scan US AI stocks (for future international integration)."""
        candidates = []
        for symbol in US_AI_STOCKS:
            candidate = self._evaluate_candidate(symbol, "us_stock")
            if candidate:
                candidates.append(candidate)
        self.candidates = candidates
        return candidates

    def _evaluate_candidate(self, symbol: str, market: str) -> Optional[StockCandidate]:
        """Check if a stock passes minimum criteria."""
        try:
            history = self.data.yahoo.get_history(symbol, market, days=30)
            if len(history) < 20:
                return None  # Not enough recent data

            current_price = history[-1].close
            avg_volume = sum(c.volume for c in history) / len(history)

            # Minimum criteria filters
            if current_price < MINIMUM_CRITERIA["min_price"]:
                return None
            if current_price > MINIMUM_CRITERIA["max_price"]:
                return None
            if avg_volume < MINIMUM_CRITERIA["avg_daily_volume"]:
                return None

            return StockCandidate(
                symbol=symbol,
                name=symbol,  # TODO: map to full name
                sector="",    # TODO: map to sector
                market_cap_cr=0,  # Filled by fundamentals
                avg_daily_volume=int(avg_volume),
                current_price=current_price,
            )
        except Exception:
            return None

    def get_top_candidates(self, n: int = 10) -> list[StockCandidate]:
        """Return top N candidates sorted by score (after scoring engine runs)."""
        return sorted(self.candidates, key=lambda c: c.score, reverse=True)[:n]
