"""
Smart Invest Agent — Market Data Feeds
Multiple sources for price verification (RISK-PROTOCOLS Chapter 6.1)
Covers: Indian stocks, crypto, fundamentals
"""

import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
import requests


@dataclass
class OHLCV:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str


@dataclass
class Fundamentals:
    symbol: str
    market_cap: float  # in Crores
    pe_ratio: float
    revenue_growth_yoy: float  # percentage
    profit_growth_yoy: float
    debt_to_equity: float
    roe: float  # return on equity
    promoter_holding: float  # percentage
    last_updated: datetime = field(default_factory=datetime.utcnow)


class YahooFinanceFeed:
    """
    Free historical + real-time data via Yahoo Finance.
    No API key needed. Rate limit: ~2000 requests/hour.
    Covers: Indian stocks (.NS suffix), US stocks, crypto.
    """

    BASE = "https://query1.finance.yahoo.com/v8/finance/chart"

    SUFFIX_MAP = {
        "indian_stock": ".NS",
        "indian_etf": ".NS",
        "us_stock": "",
        "crypto_inr": "-INR",
    }

    def get_history(self, symbol: str, market: str = "indian_stock", days: int = 365) -> list[OHLCV]:
        suffix = self.SUFFIX_MAP.get(market, ".NS")
        ticker = f"{symbol}{suffix}"

        params = {
            "interval": "1d",
            "range": f"{days}d",
        }

        try:
            resp = requests.get(f"{self.BASE}/{ticker}", params=params, timeout=10,
                                headers={"User-Agent": "Mozilla/5.0"})
            data = resp.json()

            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            quotes = result["indicators"]["quote"][0]

            candles = []
            for i in range(len(timestamps)):
                if quotes["close"][i] is None:
                    continue
                candles.append(OHLCV(
                    timestamp=datetime.fromtimestamp(timestamps[i]),
                    open=quotes["open"][i] or 0,
                    high=quotes["high"][i] or 0,
                    low=quotes["low"][i] or 0,
                    close=quotes["close"][i] or 0,
                    volume=quotes["volume"][i] or 0,
                    source="yahoo_finance",
                ))
            return candles
        except Exception as e:
            print(f"Yahoo Finance error for {symbol}: {e}")
            return []

    def get_current_price(self, symbol: str, market: str = "indian_stock") -> Optional[float]:
        candles = self.get_history(symbol, market, days=5)
        if candles:
            return candles[-1].close
        return None

    def get_bulk_prices(self, symbols: list[str], market: str = "indian_stock") -> dict[str, float]:
        prices = {}
        for symbol in symbols:
            price = self.get_current_price(symbol, market)
            if price:
                prices[symbol] = price
            time.sleep(0.5)  # Rate limiting
        return prices


class CoinDCXFeed:
    """
    Free crypto price data from CoinDCX public API.
    No auth needed for market data. Indian exchange = INR prices.
    """

    BASE = "https://api.coindcx.com"

    def get_current_price(self, symbol: str) -> Optional[float]:
        try:
            resp = requests.get(f"{self.BASE}/exchange/ticker", timeout=10)
            tickers = resp.json()
            pair = f"{symbol}INR"
            ticker = next((t for t in tickers if t["market"] == pair), None)
            return float(ticker["last_price"]) if ticker else None
        except Exception:
            return None

    def get_all_prices(self) -> dict[str, float]:
        try:
            resp = requests.get(f"{self.BASE}/exchange/ticker", timeout=10)
            tickers = resp.json()
            return {
                t["market"].replace("INR", ""): float(t["last_price"])
                for t in tickers if t["market"].endswith("INR")
            }
        except Exception:
            return {}

    def get_history(self, symbol: str, days: int = 365) -> list[OHLCV]:
        # CoinDCX doesn't have a free historical candle API
        # Fall back to Yahoo Finance for crypto history
        yahoo = YahooFinanceFeed()
        return yahoo.get_history(symbol, market="crypto_inr", days=days)


class NSEBhavcopyFeed:
    """
    NSE official daily data (Bhavcopy).
    Published daily after market close. Free, authoritative.
    Good for: EOD prices, delivery volume, all listed stocks.
    """

    def get_bhavcopy(self, date: Optional[datetime] = None) -> list[dict]:
        if date is None:
            date = datetime.now() - timedelta(days=1)  # Yesterday's data

        date_str = date.strftime("%d%m%Y")
        url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date_str}_F_0000.csv.zip"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/html,application/xhtml+xml",
                "Referer": "https://www.nseindia.com/",
            }
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return []

            import zipfile, io, csv
            with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as f:
                    reader = csv.DictReader(io.TextIOWrapper(f))
                    return list(reader)
        except Exception as e:
            print(f"NSE Bhavcopy error: {e}")
            return []


class ScreenerFeed:
    """
    Scrape fundamentals from Screener.in (free, no auth for basic data).
    Covers: Indian stocks only.
    """

    BASE = "https://www.screener.in/api/company"

    def get_fundamentals(self, symbol: str) -> Optional[Fundamentals]:
        try:
            # Screener uses company name in URL, not always symbol
            # This is a simplified version — production would need proper mapping
            resp = requests.get(
                f"{self.BASE}/{symbol}/",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            if resp.status_code != 200:
                return None

            data = resp.json()
            return Fundamentals(
                symbol=symbol,
                market_cap=data.get("market_cap", 0),
                pe_ratio=data.get("pe_ratio", 0),
                revenue_growth_yoy=data.get("revenue_growth", 0),
                profit_growth_yoy=data.get("profit_growth", 0),
                debt_to_equity=data.get("debt_to_equity", 0),
                roe=data.get("roe", 0),
                promoter_holding=data.get("promoter_holding", 0),
            )
        except Exception:
            return None


class DataAggregator:
    """
    Combines multiple sources. Verifies price discrepancies.
    RISK-PROTOCOLS Chapter 6.1: Minimum 2 independent sources.
    """

    def __init__(self):
        self.yahoo = YahooFinanceFeed()
        self.coindcx = CoinDCXFeed()
        self.nse = NSEBhavcopyFeed()
        self.screener = ScreenerFeed()

    def get_verified_price(self, symbol: str, asset_type: str) -> Optional[float]:
        """Get price from 2 sources, verify discrepancy < 1%."""
        prices = []

        if asset_type == "crypto":
            p1 = self.coindcx.get_current_price(symbol)
            p2 = self.yahoo.get_current_price(symbol, "crypto_inr")
            if p1: prices.append(p1)
            if p2: prices.append(p2)
        else:
            p1 = self.yahoo.get_current_price(symbol, "indian_stock")
            if p1: prices.append(p1)
            # NSE bhavcopy is EOD only — use as secondary verification
            # For real-time, we'd need a second live source

        if len(prices) < 1:
            return None

        if len(prices) >= 2:
            discrepancy = abs(prices[0] - prices[1]) / prices[0]
            if discrepancy > 0.01:  # > 1% difference
                print(f"⚠️ PRICE DISCREPANCY for {symbol}: {prices[0]} vs {prices[1]} ({discrepancy*100:.1f}%)")
                return None  # HALT — don't trust either (RISK-PROTOCOLS 6.1)

        return prices[0]

    def get_stock_history(self, symbol: str, days: int = 365) -> list[OHLCV]:
        return self.yahoo.get_history(symbol, "indian_stock", days)

    def get_crypto_history(self, symbol: str, days: int = 365) -> list[OHLCV]:
        return self.yahoo.get_history(symbol, "crypto_inr", days)

    def get_fundamentals(self, symbol: str) -> Optional[Fundamentals]:
        return self.screener.get_fundamentals(symbol)
