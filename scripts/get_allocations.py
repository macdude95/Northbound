#!/usr/bin/env python3
"""
Get current portfolio allocations for trading strategies.
Run daily to determine what percentage to allocate to each ticker.
"""

import os
import sys
from datetime import datetime
from typing import Dict

# Add src directory to path so we can import northbound package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def parse_strategy_allocation(arg: str) -> tuple[str, float]:
    """
    Parse strategy:percentage argument.

    Args:
        arg: String in format "strategy_name:percentage"

    Returns:
        Tuple of (strategy_name, percentage)
    """
    try:
        strategy_name, percentage_str = arg.split(":")
        percentage = float(percentage_str)
        if percentage < 0 or percentage > 100:
            raise ValueError("Percentage must be between 0 and 100")
        return strategy_name, percentage
    except ValueError as e:
        raise ValueError(
            f"Invalid strategy allocation format: {arg}. Use 'strategy_name:percentage'"
        )


def format_allocation_table(
    strategy_allocations: Dict[str, Dict[str, float]],
    final_allocation: Dict[str, float],
) -> str:
    """
    Format allocation information into a readable table.

    Args:
        strategy_allocations: Dict of strategy_name -> {ticker: percentage}
        final_allocation: Dict of ticker -> final_percentage

    Returns:
        Formatted string table
    """
    output = []
    output.append(f"Portfolio Allocations for {datetime.now().strftime('%Y-%m-%d')}")
    output.append("=" * 60)

    # Individual strategy allocations
    for strategy_name, allocation in strategy_allocations.items():
        # Find the percentage this strategy gets in portfolio
        portfolio_pct = None
        for arg in sys.argv[1:]:
            if ":" in arg:
                strat, pct = parse_strategy_allocation(arg)
                if strat == strategy_name:
                    portfolio_pct = pct
                    break

        if portfolio_pct is not None:
            output.append(f"\n{strategy_name} ({portfolio_pct}% of portfolio):")

            if allocation:
                for ticker, percentage in sorted(allocation.items()):
                    output.append(f"  - {ticker}: {percentage:.2f}%")
            else:
                output.append("  (No allocation)")

    # Final portfolio allocation
    output.append(f"\n{'Final Portfolio Allocation:'}")
    output.append("-" * 30)

    if final_allocation:
        for ticker, percentage in sorted(final_allocation.items()):
            output.append(f"- {ticker}: {percentage:.2f}%")
    else:
        output.append("(No allocations)")

    return "\n".join(output)


def main():
    """Main function to get current allocations."""
    if len(sys.argv) < 2:
        print(
            "Usage: python3 scripts/get_allocations.py strategy1:percentage strategy2:percentage ..."
        )
        print(
            "Example: python3 scripts/get_allocations.py qqq_momentum_simple:60 qqq_momentum_gradient:40"
        )
        sys.exit(1)

    try:
        from northbound import AllocationCalculator

        # Parse command line arguments
        strategy_allocations = {}
        for arg in sys.argv[1:]:
            if ":" in arg:
                strategy_name, percentage = parse_strategy_allocation(arg)
                strategy_allocations[strategy_name] = percentage

        if not strategy_allocations:
            print("Error: No valid strategy:percentage arguments provided")
            sys.exit(1)

        # Calculate allocations
        calculator = AllocationCalculator()

        # Get individual strategy allocations for display
        individual_allocations = {}
        for strategy_name in strategy_allocations.keys():
            config_path = f"strategy_configs/{strategy_name}.json"
            if os.path.exists(config_path):
                config = calculator.load_strategy_config(config_path)
                individual_allocations[strategy_name] = calculator.calculate_allocation(
                    config
                )
            else:
                print(f"Warning: Strategy config not found: {config_path}")
                individual_allocations[strategy_name] = {}

        # Calculate final combined allocation
        final_allocation = calculator.calculate_multi_strategy_allocation(
            strategy_allocations
        )

        # Display results
        output = format_allocation_table(individual_allocations, final_allocation)
        print(output)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
