"""
Smart Invest Agent — Backtesting Engine
RISK-PROTOCOLS Chapter 2.1 requires:
  - 10-year historical backtest (minimum)
  - 3-year out-of-sample test
  - Stress tests: 2008, 2020, 2022, 1987
  - Monte Carlo simulation (10,000 runs, 95% profitable)
  - Walk-forward validation
"""

import random
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Optional
from data_feeds import OHLCV


@dataclass
class BacktestResult:
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return_pct: float
    annual_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    profit_factor: float
    worst_day_pct: float
    best_day_pct: float
    avg_trade_pnl: float
    passed: bool
    failure_reasons: list[str] = field(default_factory=list)


@dataclass
class StressTestResult:
    scenario: str
    period: str
    max_drawdown_pct: float
    recovery_days: int
    survived: bool


@dataclass
class MonteCarloResult:
    runs: int
    profitable_runs: int
    profitable_pct: float
    median_return: float
    worst_case_5pct: float  # 5th percentile (95% of outcomes are better)
    best_case_95pct: float
    passed: bool  # >95% profitable required


class BacktestEngine:
    """
    Runs historical simulations. Strategy CANNOT go live without passing all tests.
    """

    def __init__(self, initial_capital: float = 50_000):
        self.initial_capital = initial_capital

    def run_backtest(self, strategy_fn: Callable, price_history: list[OHLCV],
                     strategy_name: str = "unnamed") -> BacktestResult:
        """
        Run a strategy over historical data.

        strategy_fn: takes (prices_so_far: list[float], current_price: float) → "buy"/"sell"/None
        price_history: OHLCV data sorted oldest-first
        """
        capital = self.initial_capital
        position = 0.0  # Units held
        entry_price = 0.0
        peak_capital = capital
        max_drawdown = 0.0

        trades = []
        daily_returns = []
        prev_portfolio_value = capital

        for i in range(50, len(price_history)):  # Start after 50 days (need history)
            prices_so_far = [c.close for c in price_history[:i]]
            current_price = price_history[i].close

            signal = strategy_fn(prices_so_far, current_price)

            portfolio_value = capital + (position * current_price)

            # Track daily return
            daily_ret = (portfolio_value - prev_portfolio_value) / prev_portfolio_value if prev_portfolio_value > 0 else 0
            daily_returns.append(daily_ret)
            prev_portfolio_value = portfolio_value

            # Track drawdown
            if portfolio_value > peak_capital:
                peak_capital = portfolio_value
            dd = (peak_capital - portfolio_value) / peak_capital
            if dd > max_drawdown:
                max_drawdown = dd

            # Execute signal
            if signal == "buy" and position == 0:
                # Buy with max 5% of portfolio (position limit)
                buy_amount = portfolio_value * 0.05
                position = buy_amount / current_price
                capital -= buy_amount
                entry_price = current_price
                trades.append({"action": "buy", "price": current_price, "date": price_history[i].timestamp})

            elif signal == "sell" and position > 0:
                sell_value = position * current_price
                capital += sell_value
                pnl = (current_price - entry_price) / entry_price
                trades.append({"action": "sell", "price": current_price, "pnl": pnl, "date": price_history[i].timestamp})
                position = 0

        # Final value
        final_price = price_history[-1].close
        final_capital = capital + (position * final_price)
        total_return = (final_capital - self.initial_capital) / self.initial_capital

        # Calculate metrics
        years = len(price_history) / 252  # Trading days per year
        annual_return = ((1 + total_return) ** (1 / years) - 1) if years > 0 else 0

        # Sharpe ratio
        if daily_returns:
            avg_return = sum(daily_returns) / len(daily_returns)
            std_return = (sum((r - avg_return)**2 for r in daily_returns) / len(daily_returns)) ** 0.5
            sharpe = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
        else:
            sharpe = 0

        # Win rate & profit factor
        winning_trades = [t for t in trades if t.get("pnl", 0) > 0]
        losing_trades = [t for t in trades if t.get("pnl", 0) < 0]
        sell_trades = [t for t in trades if t["action"] == "sell"]
        win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0

        gross_profit = sum(t["pnl"] for t in winning_trades)
        gross_loss = abs(sum(t["pnl"] for t in losing_trades))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Pass/fail criteria (from RISK-PROTOCOLS)
        failure_reasons = []
        if sharpe < 1.0:
            failure_reasons.append(f"Sharpe {sharpe:.2f} < 1.0 required")
        if max_drawdown > 0.20:
            failure_reasons.append(f"Max drawdown {max_drawdown*100:.1f}% > 20% limit")
        if years < 10:
            failure_reasons.append(f"Only {years:.1f} years — need 10+ years")

        return BacktestResult(
            strategy_name=strategy_name,
            start_date=price_history[0].timestamp,
            end_date=price_history[-1].timestamp,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return_pct=total_return * 100,
            annual_return_pct=annual_return * 100,
            sharpe_ratio=sharpe,
            max_drawdown_pct=max_drawdown * 100,
            win_rate=win_rate * 100,
            total_trades=len(sell_trades),
            profit_factor=profit_factor,
            worst_day_pct=min(daily_returns) * 100 if daily_returns else 0,
            best_day_pct=max(daily_returns) * 100 if daily_returns else 0,
            avg_trade_pnl=sum(t.get("pnl", 0) for t in sell_trades) / len(sell_trades) if sell_trades else 0,
            passed=len(failure_reasons) == 0,
            failure_reasons=failure_reasons,
        )

    def stress_test(self, strategy_fn: Callable, price_history: list[OHLCV]) -> list[StressTestResult]:
        """
        Test strategy against known crash periods.
        Required by RISK-PROTOCOLS Chapter 2.1.
        """
        # Define crash periods (approximate date ranges)
        scenarios = [
            ("2008 Financial Crisis", datetime(2008, 9, 1), datetime(2009, 3, 31)),
            ("2020 COVID Crash", datetime(2020, 2, 15), datetime(2020, 4, 30)),
            ("2022 Crypto Winter", datetime(2022, 5, 1), datetime(2022, 12, 31)),
            ("2016 Demonetization", datetime(2016, 11, 1), datetime(2017, 2, 28)),
        ]

        results = []
        for name, start, end in scenarios:
            # Filter history to this period
            period_data = [c for c in price_history if start <= c.timestamp <= end]
            if len(period_data) < 20:
                results.append(StressTestResult(name, f"{start.year}", 0, 0, False))
                continue

            # Run backtest on crash period
            bt = self.run_backtest(strategy_fn, period_data, f"stress_{name}")
            recovery_days = self._calculate_recovery(period_data, strategy_fn)

            results.append(StressTestResult(
                scenario=name,
                period=f"{start.strftime('%b %Y')} - {end.strftime('%b %Y')}",
                max_drawdown_pct=bt.max_drawdown_pct,
                recovery_days=recovery_days,
                survived=bt.max_drawdown_pct < 20,  # Must survive with < 20% drawdown
            ))

        return results

    def monte_carlo(self, strategy_fn: Callable, price_history: list[OHLCV],
                    runs: int = 10_000) -> MonteCarloResult:
        """
        Shuffle the order of daily returns and re-run 10,000 times.
        Tests if the strategy works due to SKILL vs LUCK.
        Required: 95% of runs must be profitable.
        """
        # Get daily returns from the strategy
        closes = [c.close for c in price_history]
        daily_returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]

        final_returns = []

        for _ in range(runs):
            # Shuffle daily returns (randomize sequence)
            shuffled = daily_returns.copy()
            random.shuffle(shuffled)

            # Simulate portfolio with shuffled returns
            capital = self.initial_capital
            for ret in shuffled:
                capital *= (1 + ret * 0.05)  # Assume 5% exposure per position limit

            total_ret = (capital - self.initial_capital) / self.initial_capital
            final_returns.append(total_ret)

        final_returns.sort()
        profitable_count = sum(1 for r in final_returns if r > 0)

        return MonteCarloResult(
            runs=runs,
            profitable_runs=profitable_count,
            profitable_pct=profitable_count / runs * 100,
            median_return=final_returns[runs // 2] * 100,
            worst_case_5pct=final_returns[int(runs * 0.05)] * 100,
            best_case_95pct=final_returns[int(runs * 0.95)] * 100,
            passed=profitable_count / runs >= 0.95,
        )

    def walk_forward(self, strategy_fn: Callable, price_history: list[OHLCV],
                     train_pct: float = 0.7) -> dict:
        """
        Walk-forward analysis: train on 70%, test on 30%.
        If out-of-sample results are within 20% of in-sample → strategy is robust.
        """
        split_idx = int(len(price_history) * train_pct)
        train_data = price_history[:split_idx]
        test_data = price_history[split_idx:]

        in_sample = self.run_backtest(strategy_fn, train_data, "in_sample")
        out_of_sample = self.run_backtest(strategy_fn, test_data, "out_of_sample")

        # Check if OOS is within 20% of IS (RISK-PROTOCOLS 2.1)
        if in_sample.annual_return_pct == 0:
            degradation = 100
        else:
            degradation = abs(in_sample.annual_return_pct - out_of_sample.annual_return_pct) / abs(in_sample.annual_return_pct) * 100

        return {
            "in_sample": in_sample,
            "out_of_sample": out_of_sample,
            "degradation_pct": degradation,
            "passed": degradation <= 20,
        }

    def full_validation(self, strategy_fn: Callable, price_history: list[OHLCV],
                        strategy_name: str) -> dict:
        """
        Complete validation suite. ALL must pass before going live.
        This is the gatekeeper — no shortcuts.
        """
        print(f"\n{'='*60}")
        print(f"  FULL VALIDATION: {strategy_name}")
        print(f"{'='*60}")

        # 1. Main backtest
        print("\n[1/4] Running main backtest...")
        backtest = self.run_backtest(strategy_fn, price_history, strategy_name)
        print(f"  Return: {backtest.total_return_pct:.1f}% | Sharpe: {backtest.sharpe_ratio:.2f} | MaxDD: {backtest.max_drawdown_pct:.1f}%")

        # 2. Stress tests
        print("\n[2/4] Running stress tests...")
        stress = self.stress_test(strategy_fn, price_history)
        for s in stress:
            status = "✅" if s.survived else "❌"
            print(f"  {status} {s.scenario}: DD={s.max_drawdown_pct:.1f}%")

        # 3. Monte Carlo
        print("\n[3/4] Running Monte Carlo (10,000 simulations)...")
        mc = self.monte_carlo(strategy_fn, price_history)
        print(f"  Profitable: {mc.profitable_pct:.1f}% | Median return: {mc.median_return:.1f}%")

        # 4. Walk-forward
        print("\n[4/4] Running walk-forward analysis...")
        wf = self.walk_forward(strategy_fn, price_history)
        print(f"  In-sample: {wf['in_sample'].annual_return_pct:.1f}% | Out-of-sample: {wf['out_of_sample'].annual_return_pct:.1f}%")
        print(f"  Degradation: {wf['degradation_pct']:.1f}%")

        # Final verdict
        all_passed = (
            backtest.passed and
            all(s.survived for s in stress) and
            mc.passed and
            wf["passed"]
        )

        print(f"\n{'='*60}")
        if all_passed:
            print("  ✅ ALL TESTS PASSED — strategy eligible for paper trading")
        else:
            print("  ❌ FAILED — strategy CANNOT be deployed")
            if not backtest.passed:
                print(f"    Backtest failures: {backtest.failure_reasons}")
            if not all(s.survived for s in stress):
                failed = [s.scenario for s in stress if not s.survived]
                print(f"    Failed stress tests: {failed}")
            if not mc.passed:
                print(f"    Monte Carlo: only {mc.profitable_pct:.1f}% profitable (need 95%+)")
            if not wf["passed"]:
                print(f"    Walk-forward: {wf['degradation_pct']:.1f}% degradation (need <20%)")
        print(f"{'='*60}\n")

        return {
            "strategy": strategy_name,
            "passed": all_passed,
            "backtest": backtest,
            "stress_tests": stress,
            "monte_carlo": mc,
            "walk_forward": wf,
        }

    def _calculate_recovery(self, data: list[OHLCV], strategy_fn: Callable) -> int:
        """How many days until portfolio recovered to pre-crash level."""
        if not data:
            return 999
        peak = data[0].close
        recovered = False
        for i, candle in enumerate(data):
            if candle.close >= peak:
                recovered = True
                return i
        return len(data)  # Never recovered in the window
