"""
Smart Invest Agent — Scoring & Ranking Engine
Scores every candidate stock on 4 dimensions, ranks them, picks the best.
This is the BRAIN that decides "which stocks to buy from 10 good options."
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
from data_feeds import DataAggregator, OHLCV, Fundamentals
from scanner import StockCandidate


@dataclass
class ScoreBreakdown:
    symbol: str
    momentum_score: float   # 0-100
    quality_score: float    # 0-100
    risk_score: float       # 0-100 (higher = safer)
    timing_score: float     # 0-100
    total_score: float      # Weighted composite
    verdict: str            # "STRONG BUY", "BUY", "HOLD", "AVOID"
    reasons: list[str]      # Why this score


# Weights — how much each dimension matters
WEIGHTS = {
    "momentum": 0.25,
    "quality": 0.30,   # Quality weighted highest — safety first
    "risk": 0.25,      # Risk = capital protection
    "timing": 0.20,
}

# Score thresholds for action
THRESHOLDS = {
    "strong_buy": 80,
    "buy": 65,
    "hold": 50,
    "avoid": 0,  # Below 50 = don't touch
}


class ScoringEngine:
    """
    Scores stocks across 4 dimensions. Only stocks scoring > 65 get bought.
    This ensures we never buy garbage just because "momentum looks good."
    """

    def __init__(self):
        self.data = DataAggregator()

    def score_candidate(self, candidate: StockCandidate, history: list[OHLCV],
                        fundamentals: Optional[Fundamentals] = None) -> ScoreBreakdown:
        """Score a single stock candidate."""

        momentum = self._score_momentum(history)
        quality = self._score_quality(fundamentals)
        risk = self._score_risk(history)
        timing = self._score_timing(history)

        total = (
            momentum * WEIGHTS["momentum"] +
            quality * WEIGHTS["quality"] +
            risk * WEIGHTS["risk"] +
            timing * WEIGHTS["timing"]
        )

        # Determine verdict
        if total >= THRESHOLDS["strong_buy"]:
            verdict = "STRONG BUY"
        elif total >= THRESHOLDS["buy"]:
            verdict = "BUY"
        elif total >= THRESHOLDS["hold"]:
            verdict = "HOLD"
        else:
            verdict = "AVOID"

        reasons = self._generate_reasons(momentum, quality, risk, timing, history, fundamentals)

        return ScoreBreakdown(
            symbol=candidate.symbol,
            momentum_score=momentum,
            quality_score=quality,
            risk_score=risk,
            timing_score=timing,
            total_score=total,
            verdict=verdict,
            reasons=reasons,
        )

    def rank_candidates(self, candidates: list[StockCandidate]) -> list[ScoreBreakdown]:
        """Score all candidates and return sorted by total score (best first)."""
        scores = []

        for candidate in candidates:
            history = self.data.get_stock_history(candidate.symbol, days=365)
            if len(history) < 50:  # Need minimum history
                continue

            fundamentals = self.data.get_fundamentals(candidate.symbol)
            score = self.score_candidate(candidate, history, fundamentals)
            candidate.score = score.total_score
            scores.append(score)

        return sorted(scores, key=lambda s: s.total_score, reverse=True)

    def get_buy_list(self, candidates: list[StockCandidate], max_picks: int = 3) -> list[ScoreBreakdown]:
        """Return only stocks that pass the BUY threshold, limited to top N."""
        ranked = self.rank_candidates(candidates)
        buyable = [s for s in ranked if s.total_score >= THRESHOLDS["buy"]]
        return buyable[:max_picks]

    # --- Scoring Dimensions ---

    def _score_momentum(self, history: list[OHLCV]) -> float:
        """How strong is the uptrend? (0-100)"""
        if len(history) < 50:
            return 0

        score = 0
        closes = [c.close for c in history]
        volumes = [c.volume for c in history]

        current = closes[-1]

        # Price above 20-day MA? (+25)
        ma20 = sum(closes[-20:]) / 20
        if current > ma20:
            score += 25

        # Price above 50-day MA? (+25)
        ma50 = sum(closes[-50:]) / 50
        if current > ma50:
            score += 25

        # Volume trending up? (recent 10d avg > 30d avg) (+20)
        vol_10d = sum(volumes[-10:]) / 10
        vol_30d = sum(volumes[-30:]) / 30
        if vol_10d > vol_30d:
            score += 20

        # Positive return last 30 days? (+15)
        ret_30d = (closes[-1] - closes[-30]) / closes[-30]
        if ret_30d > 0:
            score += 15

        # Consistently green (>60% of last 20 days were up)? (+15)
        up_days = sum(1 for i in range(-20, 0) if closes[i] > closes[i-1])
        if up_days >= 12:
            score += 15

        return min(score, 100)

    def _score_quality(self, fundamentals: Optional[Fundamentals]) -> float:
        """How good is the company? (0-100)"""
        if fundamentals is None:
            return 50  # Neutral if no data (don't penalize, don't reward)

        score = 0

        # Large market cap (> ₹50,000 Cr)? (+20)
        if fundamentals.market_cap > 50000:
            score += 20
        elif fundamentals.market_cap > 10000:
            score += 10

        # Profitable (PE > 0 means profits exist)? (+20)
        if 0 < fundamentals.pe_ratio < 50:
            score += 20
        elif fundamentals.pe_ratio > 50:
            score += 5  # Overvalued but at least profitable

        # Revenue growing? (+20)
        if fundamentals.revenue_growth_yoy > 10:
            score += 20
        elif fundamentals.revenue_growth_yoy > 0:
            score += 10

        # Low debt? (+20)
        if fundamentals.debt_to_equity < 0.5:
            score += 20
        elif fundamentals.debt_to_equity < 1.0:
            score += 10

        # Good ROE (> 15%)? (+20)
        if fundamentals.roe > 15:
            score += 20
        elif fundamentals.roe > 10:
            score += 10

        return min(score, 100)

    def _score_risk(self, history: list[OHLCV]) -> float:
        """How SAFE is this stock? Higher = safer. (0-100)"""
        if len(history) < 50:
            return 0

        score = 0
        closes = [c.close for c in history]

        # Low volatility? (daily std dev < 2%) (+25)
        daily_returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        volatility = (sum(r**2 for r in daily_returns[-30:]) / 30) ** 0.5
        if volatility < 0.02:
            score += 25
        elif volatility < 0.03:
            score += 15

        # Max drawdown last year < 20%? (+25)
        peak = closes[0]
        max_dd = 0
        for price in closes:
            if price > peak:
                peak = price
            dd = (peak - price) / peak
            if dd > max_dd:
                max_dd = dd
        if max_dd < 0.20:
            score += 25
        elif max_dd < 0.30:
            score += 15

        # No single-day crash > 5% in last 30 days? (+25)
        recent_returns = daily_returns[-30:]
        worst_day = min(recent_returns) if recent_returns else 0
        if worst_day > -0.05:
            score += 25
        elif worst_day > -0.10:
            score += 15

        # Sufficient liquidity (avg volume > 500K)? (+25)
        avg_vol = sum(c.volume for c in history[-30:]) / 30
        if avg_vol > 500_000:
            score += 25
        elif avg_vol > 100_000:
            score += 15

        return min(score, 100)

    def _score_timing(self, history: list[OHLCV]) -> float:
        """Is NOW a good time to buy? (0-100)"""
        if len(history) < 50:
            return 0

        score = 0
        closes = [c.close for c in history]
        current = closes[-1]

        # RSI not overbought (< 70)? (+30)
        rsi = self._calculate_rsi(closes, period=14)
        if rsi < 70:
            score += 30
        if rsi < 30:  # Oversold = great timing
            score += 20

        # Not at all-time high? (+25)
        ath = max(closes)
        if current < ath * 0.95:  # At least 5% below ATH
            score += 25

        # Pulled back from recent high (buy the dip)? (+25)
        recent_high = max(closes[-20:])
        if current < recent_high * 0.95:  # 5%+ pullback
            score += 25

        # Not in a parabolic spike (< 20% gain in 7 days)? (+20)
        if len(closes) >= 7:
            week_return = (current - closes[-7]) / closes[-7]
            if week_return < 0.20:  # RISK-PROTOCOLS 7.2: anti-FOMO
                score += 20

        return min(score, 100)

    # --- Helpers ---

    def _calculate_rsi(self, prices: list[float], period: int = 14) -> float:
        """Relative Strength Index — measures overbought/oversold."""
        if len(prices) < period + 1:
            return 50  # Neutral

        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _generate_reasons(self, momentum: float, quality: float, risk: float,
                          timing: float, history: list[OHLCV],
                          fundamentals: Optional[Fundamentals]) -> list[str]:
        """Human-readable explanation of why the score is what it is."""
        reasons = []

        if momentum >= 75:
            reasons.append("Strong uptrend — price above key moving averages")
        elif momentum < 40:
            reasons.append("Weak momentum — no clear trend")

        if quality >= 75:
            reasons.append("High quality company — profitable, growing, low debt")
        elif quality < 40:
            reasons.append("Quality concerns — check fundamentals manually")

        if risk >= 75:
            reasons.append("Low risk — stable price, good liquidity, small drawdowns")
        elif risk < 40:
            reasons.append("HIGH RISK — volatile, illiquid, or large recent drawdown")

        if timing >= 75:
            reasons.append("Good entry point — not overbought, pullback opportunity")
        elif timing < 40:
            reasons.append("Bad timing — overbought or at highs, wait for pullback")

        return reasons
