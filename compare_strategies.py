#!/usr/bin/env python3
"""
Compare multiple trading strategies with visualization
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from backtester import Backtester
from strategies.momentum_strategy import (
    BuyAndHoldQQQ,
    BuyAndHoldTQQQ,
    BuyAndHoldSQQQ,
    RollingAverageStrategy,
    WeeklyRollingAverageStrategy,
    MonthlyRollingAverageStrategy,
)


def plot_strategy_comparison(results, title="Strategy Performance Comparison"):
    """Plot portfolio values over time for multiple strategies."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # Plot portfolio values
    for strategy_name, result in results.items():
        dates = [datetime.strptime(d, "%Y-%m-%d") for d in result["dates"]]
        values = result["portfolio_values"]

        ax1.plot(dates, values, label=strategy_name, linewidth=2)

    ax1.set_title(f"{title} - Portfolio Value", fontsize=14)
    ax1.set_xlabel("Date", fontsize=12)
    ax1.set_ylabel("Portfolio Value ($)", fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale("log")  # Use log scale to show all strategies

    # Format x-axis
    ax1.xaxis.set_major_locator(mdates.YearLocator(base=1))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    # Plot metrics comparison
    strategy_names = list(results.keys())
    total_returns = [
        results[name]["metrics"]["total_return"] * 100 for name in strategy_names
    ]
    sharpe_ratios = [
        results[name]["metrics"]["sharpe_ratio"] for name in strategy_names
    ]
    max_drawdowns = [
        results[name]["metrics"]["max_drawdown"] * 100 for name in strategy_names
    ]

    x = range(len(strategy_names))
    width = 0.25

    ax2.bar(
        [i - width for i in x],
        total_returns,
        width,
        label="Total Return (%)",
        alpha=0.8,
    )
    ax2.bar(x, sharpe_ratios, width, label="Sharpe Ratio", alpha=0.8)
    ax2.bar(
        [i + width for i in x],
        max_drawdowns,
        width,
        label="Max Drawdown (%)",
        alpha=0.8,
    )

    ax2.set_title("Performance Metrics Comparison", fontsize=14)
    ax2.set_xlabel("Strategy", fontsize=12)
    ax2.set_ylabel("Value", fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(strategy_names, rotation=45, ha="right")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


def print_strategy_metrics(results):
    """Print detailed metrics for each strategy."""
    print("\n" + "=" * 80)
    print("STRATEGY PERFORMANCE METRICS")
    print("=" * 80)

    for strategy_name, result in results.items():
        metrics = result["metrics"]
        print(f"\n{strategy_name}:")
        print(f"  Total Return:     {metrics['total_return']*100:.2f}%")
        print(f"  Annual Return:    {metrics['annual_return']*100:.2f}%")
        print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:.3f}")
        print(f"  Max Drawdown:     {metrics['max_drawdown']*100:.2f}%")
        print(f"  Final Value:      ${metrics['final_value']:,.2f}")
        print(f"  Start Value:      ${metrics['start_value']:,.2f}")


def main():
    # Initialize backtester
    backtester = Backtester()

    # Define strategies to test
    strategies = [
        BuyAndHoldQQQ(),
        BuyAndHoldTQQQ(),
        BuyAndHoldSQQQ(),
        RollingAverageStrategy(),
        WeeklyRollingAverageStrategy(),
        MonthlyRollingAverageStrategy(),
    ]

    strategy_names = [
        "Buy_Hold_QQQ",
        "Buy_Hold_TQQQ",
        "Buy_Hold_SQQQ",
        "50d_MA_Strategy",
        "50d_MA_Weekly",
        "50d_MA_Monthly",
    ]

    # Choose date range
    print("Select date range for comparison:")
    print("1. 2018-2022")
    print("2. 2022-2025")
    print("3. 2025 only")
    print("4. Custom dates")

    choice = input("Enter choice (1-4): ").strip()

    if choice == "1":
        start_date = "2018-01-01"
        end_date = "2022-12-31"
        title = "Strategy Performance: 2018-2022"
    elif choice == "2":
        start_date = "2022-01-01"
        end_date = "2025-12-31"
        title = "Strategy Performance: 2022-2025"
    elif choice == "3":
        start_date = "2025-01-01"
        end_date = None
        title = "Strategy Performance: 2025"
    else:
        start_date = input("Start date (YYYY-MM-DD): ").strip()
        end_date = input("End date (YYYY-MM-DD or Enter for latest): ").strip() or None
        title = f"Strategy Performance: {start_date} to {end_date or 'Latest'}"

    print(f"\n🧮 Running backtests for {title}...")

    # Run backtests
    results = backtester.compare_strategies(
        strategies, start_date=start_date, end_date=end_date
    )

    # Create results dict with proper names
    named_results = {}
    for i, (name, result) in enumerate(zip(strategy_names, results.values())):
        named_results[name] = result

    # Print metrics
    print_strategy_metrics(named_results)

    # Plot comparison
    plot_strategy_comparison(named_results, title)


if __name__ == "__main__":
    main()
