"""
Smart Invest Agent — Runnable Backtest
Downloads 10 years of Nifty 50 data and validates the momentum strategy.

Run: python run_backtest.py

This answers THE fundamental question:
"Does the 20-day MA crossover on NIFTYBEES beat buy-and-hold over 10 years?"

If it doesn't pass, the strategy cannot go live (RISK-PROTOCOLS Chapter 2.1).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from data_feeds import YahooFinanceFeed, OHLCV
from backtest import BacktestEngine


def download_nifty_data(years: int = 10) -> list[OHLCV]:
    """Download Nifty 50 index data from Yahoo Finance."""
    print(f"Downloading {years} years of Nifty 50 data...")
    feed = YahooFinanceFeed()
    days = years * 365
    data = feed.get_history("^NSEI", market="indian_stock", days=days)

    if not data:
        # Fallback: try NIFTYBEES ETF
        print("  ^NSEI failed, trying NIFTYBEES...")
        data = feed.get_history("NIFTYBEES", market="indian_stock", days=days)

    if not data:
        print("❌ Failed to download data. Check internet connection.")
        sys.exit(1)

    print(f"  Downloaded {len(data)} trading days")
    print(f"  Period: {data[0].timestamp.strftime('%Y-%m-%d')} to {data[-1].timestamp.strftime('%Y-%m-%d')}")
    print(f"  Price range: ₹{min(c.close for c in data):,.0f} — ₹{max(c.close for c in data):,.0f}")
    return data


def momentum_strategy(prices: list[float], current_price: float) -> str:
    """20-day moving average crossover. The simplest trend-following strategy."""
    if len(prices) < 21:
        return None

    ma20 = sum(prices[-20:]) / 20
    prev_price = prices[-2]

    # Buy when price crosses above MA
    if prev_price <= ma20 and current_price > ma20:
        return "buy"

    # Sell when price crosses below MA
    if prev_price >= ma20 and current_price < ma20:
        return "sell"

    return None


def mean_reversion_strategy(prices: list[float], current_price: float) -> str:
    """Buy when oversold (2 std below mean), sell when reverted."""
    if len(prices) < 20:
        return None

    window = prices[-20:]
    ma = sum(window) / len(window)
    std = (sum((p - ma)**2 for p in window) / len(window)) ** 0.5

    if std == 0:
        return None

    lower = ma - 2 * std
    upper = ma + 2 * std

    if current_price < lower:
        return "buy"
    if current_price > upper:
        return "sell"

    return None


def buy_and_hold_benchmark(data: list[OHLCV], capital: float = 50_000) -> dict:
    """Simple benchmark: buy on day 1, hold forever."""
    entry_price = data[0].close
    exit_price = data[-1].close
    years = len(data) / 252

    total_return = (exit_price - entry_price) / entry_price
    annual_return = ((1 + total_return) ** (1 / years) - 1) if years > 0 else 0
    final_capital = capital * (1 + total_return)

    # Calculate max drawdown
    peak = data[0].close
    max_dd = 0
    for candle in data:
        if candle.close > peak:
            peak = candle.close
        dd = (peak - candle.close) / peak
        if dd > max_dd:
            max_dd = dd

    return {
        "strategy": "Buy & Hold (Benchmark)",
        "total_return_pct": total_return * 100,
        "annual_return_pct": annual_return * 100,
        "final_capital": final_capital,
        "max_drawdown_pct": max_dd * 100,
        "years": years,
    }


def print_result(result, benchmark):
    """Pretty-print backtest result vs benchmark."""
    print(f"\n{'='*70}")
    print(f"  STRATEGY: {result.strategy_name}")
    print(f"{'='*70}")
    print(f"  Period: {result.start_date.strftime('%Y-%m-%d')} → {result.end_date.strftime('%Y-%m-%d')}")
    print(f"  Initial: ₹{result.initial_capital:,.0f} → Final: ₹{result.final_capital:,.0f}")
    print(f"")
    print(f"  {'Metric':<25} {'Strategy':<15} {'Buy&Hold':<15} {'Verdict'}")
    print(f"  {'-'*25} {'-'*15} {'-'*15} {'-'*10}")

    strat_ret = result.total_return_pct
    bench_ret = benchmark["total_return_pct"]
    print(f"  {'Total Return':<25} {strat_ret:>+12.1f}%  {bench_ret:>+12.1f}%  {'✅' if strat_ret > bench_ret else '❌'}")

    strat_ann = result.annual_return_pct
    bench_ann = benchmark["annual_return_pct"]
    print(f"  {'Annual Return':<25} {strat_ann:>+12.1f}%  {bench_ann:>+12.1f}%  {'✅' if strat_ann > bench_ann else '❌'}")

    print(f"  {'Sharpe Ratio':<25} {result.sharpe_ratio:>12.2f}   {'N/A':<15}{'✅' if result.sharpe_ratio >= 1.0 else '❌'} (need >1.0)")

    strat_dd = result.max_drawdown_pct
    bench_dd = benchmark["max_drawdown_pct"]
    print(f"  {'Max Drawdown':<25} {strat_dd:>12.1f}%  {bench_dd:>12.1f}%  {'✅' if strat_dd < 20 else '❌'} (need <20%)")

    print(f"  {'Win Rate':<25} {result.win_rate:>12.1f}%")
    print(f"  {'Total Trades':<25} {result.total_trades:>12}")
    print(f"  {'Profit Factor':<25} {result.profit_factor:>12.2f}")
    print(f"  {'Worst Day':<25} {result.worst_day_pct:>+12.2f}%")
    print(f"  {'Best Day':<25} {result.best_day_pct:>+12.2f}%")

    print(f"\n  {'─'*70}")
    if result.passed:
        print(f"  ✅ PASSED — Strategy meets RISK-PROTOCOLS requirements")
    else:
        print(f"  ❌ FAILED — Cannot deploy this strategy")
        for reason in result.failure_reasons:
            print(f"     • {reason}")
    print(f"  {'─'*70}\n")


def main():
    print("\n" + "="*70)
    print("  SMART INVEST — STRATEGY VALIDATION")
    print("  Running against RISK-PROTOCOLS.md Chapter 2.1 requirements")
    print("="*70 + "\n")

    # Download data
    data = download_nifty_data(years=10)

    if len(data) < 252 * 3:
        print(f"⚠️  Only {len(data)} days available ({len(data)/252:.1f} years)")
        print("  Need at least 3 years for meaningful results")
        if len(data) < 252:
            print("❌ Insufficient data. Exiting.")
            sys.exit(1)

    # Benchmark
    benchmark = buy_and_hold_benchmark(data)
    print(f"\n📊 Benchmark (Buy & Hold Nifty 50):")
    print(f"   Return: {benchmark['total_return_pct']:+.1f}% total ({benchmark['annual_return_pct']:+.1f}%/year)")
    print(f"   Max Drawdown: {benchmark['max_drawdown_pct']:.1f}%")
    print(f"   Final: ₹{benchmark['final_capital']:,.0f} from ₹50,000")

    # Run backtests
    engine = BacktestEngine(initial_capital=50_000)

    print("\n" + "-"*70)
    print("  TESTING: 20-Day Momentum Crossover")
    print("-"*70)
    momentum_result = engine.run_backtest(momentum_strategy, data, "20-Day Momentum Crossover")
    print_result(momentum_result, benchmark)

    print("-"*70)
    print("  TESTING: Mean Reversion (Bollinger Bands)")
    print("-"*70)
    mr_result = engine.run_backtest(mean_reversion_strategy, data, "Mean Reversion (2σ)")
    print_result(mr_result, benchmark)

    # Full validation for the best performer
    best = momentum_result if momentum_result.total_return_pct > mr_result.total_return_pct else mr_result
    print("\n" + "="*70)
    print(f"  FULL VALIDATION SUITE: {best.strategy_name}")
    print("="*70)

    strategy_fn = momentum_strategy if best == momentum_result else mean_reversion_strategy
    validation = engine.full_validation(strategy_fn, data, best.strategy_name)

    # Final summary
    print("\n" + "="*70)
    print("  FINAL VERDICT")
    print("="*70)

    beats_benchmark = best.total_return_pct > benchmark["total_return_pct"]
    all_passed = validation["passed"]

    print(f"\n  Best strategy: {best.strategy_name}")
    print(f"  Beats buy-and-hold: {'✅ YES' if beats_benchmark else '❌ NO'}")
    print(f"  Passes all protocols: {'✅ YES' if all_passed else '❌ NO'}")

    if beats_benchmark and all_passed:
        print(f"\n  🎉 STRATEGY APPROVED for paper trading!")
        print(f"  Next step: 6 months paper trading before live deployment")
    elif beats_benchmark and not all_passed:
        print(f"\n  ⚠️  Strategy beats benchmark but fails protocol checks.")
        print(f"  Need to tune parameters or pick a different strategy.")
    else:
        print(f"\n  ❌ Strategy does NOT beat simple buy-and-hold.")
        print(f"  Recommendation: Use DCA into Nifty 50 ETF instead.")
        print(f"  Buy-and-hold returned {benchmark['annual_return_pct']:+.1f}%/year — hard to beat!")

    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
