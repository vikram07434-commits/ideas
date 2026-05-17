"""
Smart Invest Agent — Broker Integrations
Handles API connections to Angel One (stocks) and CoinDCX (crypto)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import os


@dataclass
class OrderResult:
    order_id: str
    symbol: str
    action: str
    quantity: float
    price: float
    status: str  # "filled", "pending", "rejected", "cancelled"
    timestamp: datetime
    fees: float = 0.0
    slippage: float = 0.0


class BrokerBase(ABC):
    """Base class for all broker integrations."""

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def get_balance(self) -> float:
        pass

    @abstractmethod
    def get_positions(self) -> list[dict]:
        pass

    @abstractmethod
    def place_order(self, symbol: str, action: str, quantity: float, price: float) -> OrderResult:
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        pass

    @abstractmethod
    def get_price(self, symbol: str) -> float:
        pass


class AngelOneBroker(BrokerBase):
    """
    Angel One SmartAPI integration for Indian stocks/ETFs.
    Free API, no monthly cost.
    Docs: https://smartapi.angelone.in/docs
    """

    def __init__(self):
        self.api_key = os.getenv("ANGEL_ONE_API_KEY")
        self.client_id = os.getenv("ANGEL_ONE_CLIENT_ID")
        self.password = os.getenv("ANGEL_ONE_PASSWORD")
        self.totp_secret = os.getenv("ANGEL_ONE_TOTP")
        self.session = None

    def connect(self) -> bool:
        try:
            from SmartApi import SmartConnect
            self.session = SmartConnect(api_key=self.api_key)
            totp = self._generate_totp()
            data = self.session.generateSession(self.client_id, self.password, totp)
            return data["status"]
        except ImportError:
            print("SmartApi package not installed. Run: pip install smartapi-python")
            return False
        except Exception as e:
            print(f"Angel One connection failed: {e}")
            return False

    def get_balance(self) -> float:
        if not self.session:
            return 0.0
        try:
            rms = self.session.rmsLimit()
            return float(rms["data"]["availablecash"])
        except Exception:
            return 0.0

    def get_positions(self) -> list[dict]:
        if not self.session:
            return []
        try:
            positions = self.session.position()
            return positions.get("data", []) or []
        except Exception:
            return []

    def place_order(self, symbol: str, action: str, quantity: float, price: float) -> OrderResult:
        if not self.session:
            return OrderResult("", symbol, action, quantity, price, "rejected", datetime.utcnow())

        order_params = {
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": self._get_token(symbol),
            "transactiontype": "BUY" if action == "buy" else "SELL",
            "exchange": "NSE",
            "ordertype": "LIMIT",  # NEVER market orders (RISK-PROTOCOLS 3.1)
            "producttype": "DELIVERY",  # Cash only, no margin
            "duration": "DAY",  # DAY only (RISK-PROTOCOLS 3.1)
            "price": str(price),
            "quantity": str(int(quantity)),
        }

        try:
            result = self.session.placeOrder(order_params)
            return OrderResult(
                order_id=result["data"]["orderid"],
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                status="pending",
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            print(f"Order failed: {e}")
            return OrderResult("", symbol, action, quantity, price, "rejected", datetime.utcnow())

    def cancel_order(self, order_id: str) -> bool:
        if not self.session:
            return False
        try:
            self.session.cancelOrder(order_id, "NORMAL")
            return True
        except Exception:
            return False

    def get_price(self, symbol: str) -> float:
        if not self.session:
            return 0.0
        try:
            data = self.session.ltpData("NSE", symbol, self._get_token(symbol))
            return float(data["data"]["ltp"])
        except Exception:
            return 0.0

    def _generate_totp(self) -> str:
        import pyotp
        return pyotp.TOTP(self.totp_secret).now()

    def _get_token(self, symbol: str) -> str:
        # Symbol token mapping (needs to be loaded from Angel One's instrument list)
        # TODO: Load from instruments master file
        tokens = {
            "NIFTYBEES": "2885",
            "BANKBEES": "16704",
            "ITBEES": "13751",
            "GOLDBEES": "16705",
        }
        return tokens.get(symbol, "")


class CoinDCXBroker(BrokerBase):
    """
    CoinDCX API integration for crypto trading.
    Free API, no monthly cost.
    Docs: https://docs.coindcx.com/
    """

    BASE_URL = "https://api.coindcx.com"

    def __init__(self):
        self.api_key = os.getenv("COINDCX_API_KEY")
        self.api_secret = os.getenv("COINDCX_API_SECRET")

    def connect(self) -> bool:
        try:
            import requests
            resp = requests.get(f"{self.BASE_URL}/exchange/ticker")
            return resp.status_code == 200
        except Exception:
            return False

    def get_balance(self) -> float:
        import hmac, hashlib, json, time, requests

        timestamp = str(int(time.time() * 1000))
        body = {"timestamp": timestamp}
        payload = json.dumps(body, separators=(",", ":"))
        signature = hmac.new(
            self.api_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        headers = {
            "X-AUTH-APIKEY": self.api_key,
            "X-AUTH-SIGNATURE": signature,
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(f"{self.BASE_URL}/exchange/v1/users/balances", headers=headers, data=payload)
            balances = resp.json()
            inr_balance = next((b for b in balances if b["currency"] == "INR"), None)
            return float(inr_balance["balance"]) if inr_balance else 0.0
        except Exception:
            return 0.0

    def get_positions(self) -> list[dict]:
        # Same auth pattern as get_balance
        # Returns non-zero crypto holdings
        return []  # TODO: implement

    def place_order(self, symbol: str, action: str, quantity: float, price: float) -> OrderResult:
        import hmac, hashlib, json, time, requests

        timestamp = str(int(time.time() * 1000))
        body = {
            "side": "buy" if action == "buy" else "sell",
            "order_type": "limit_order",  # NEVER market (RISK-PROTOCOLS)
            "market": f"{symbol}INR",
            "price_per_unit": str(price),
            "total_quantity": str(quantity),
            "timestamp": timestamp,
        }

        payload = json.dumps(body, separators=(",", ":"))
        signature = hmac.new(
            self.api_secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        headers = {
            "X-AUTH-APIKEY": self.api_key,
            "X-AUTH-SIGNATURE": signature,
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(f"{self.BASE_URL}/exchange/v1/orders/create", headers=headers, data=payload)
            data = resp.json()
            return OrderResult(
                order_id=data.get("id", ""),
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                status="pending" if data.get("id") else "rejected",
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            return OrderResult("", symbol, action, quantity, price, "rejected", datetime.utcnow())

    def cancel_order(self, order_id: str) -> bool:
        # TODO: implement cancel via API
        return False

    def get_price(self, symbol: str) -> float:
        import requests
        try:
            resp = requests.get(f"{self.BASE_URL}/exchange/ticker")
            tickers = resp.json()
            pair = f"{symbol}INR"
            ticker = next((t for t in tickers if t["market"] == pair), None)
            return float(ticker["last_price"]) if ticker else 0.0
        except Exception:
            return 0.0
