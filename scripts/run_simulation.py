#!/usr/bin/env python3
"""
Run multiple trading strategy simulations with organized folder structure.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Add src directory to path so we can import northbound package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def run_multiple_strategies(
    strategy_names: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    capital: float = 10000.0,
) -> str:
    """
    Run multiple strategy backtests and create visualizations.

    Args:
        strategy_names: List of strategy names (e.g., ['qqq', 'qqq_momentum_simple'])
        start_date: Start date for simulation
        end_date: End date for simulation
        capital: Starting capital

    Returns:
        Path to the simulation folder
    """
    # Convert strategy names to full config file paths
    config_files = [f"strategy_configs/{name}.json" for name in strategy_names]
    # Create subfolder name
    start_str = start_date or "full"
    end_str = end_date or "full"
    capital_str = str(int(capital))
    subfolder_name = f"{start_str}_{end_str}_{capital_str}"
    subfolder_path = f"data/simulations/{subfolder_name}"

    print(f"Running simulations in: {subfolder_path}")

    # Run each strategy backtest
    for config_file in config_files:
        print(f"\nRunning backtest for {config_file}...")
        try:
            from northbound.backtester import Backtester

            # Create backtester instance and run simulation
            backtester = Backtester(config_file)
            strategy_results, simulation_results = backtester.run_simulation(
                start_date=start_date, end_date=end_date, initial_capital=capital
            )

            # Ensure subfolder exists
            os.makedirs(subfolder_path, exist_ok=True)

            # Save results in subfolder
            config_name = Path(config_file).stem
            strategy_path = f"{subfolder_path}/{config_name}.csv"
            backtester.save_results(
                (strategy_results, simulation_results), strategy_path, strategy_path
            )

            print(f"✓ Completed backtest for {config_name}")

        except Exception as e:
            print(f"✗ Error running {config_file}: {e}")
            continue

    # Collect ALL CSV files in the subfolder for comprehensive visualization
    simulation_files = []
    if os.path.exists(subfolder_path):
        for file in os.listdir(subfolder_path):
            if file.endswith(".csv") and not file.startswith("strategy_allocations_"):
                csv_path = os.path.join(subfolder_path, file)
                simulation_files.append(csv_path)

    # Create visualization if we have multiple strategies
    if len(simulation_files) >= 2:
        print(f"\nCreating visualization for {len(simulation_files)} strategies...")

        # Import here to avoid circular imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
        from northbound.visualizer import PerformanceVisualizer

        viz = PerformanceVisualizer()
        viz.compare_strategies(simulation_files)

        html_path = f"{subfolder_path}/strategy_comparison.html"
        if os.path.exists(html_path):
            print(f"Visualization saved: {html_path}")

    return subfolder_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run multiple strategy simulations")
    parser.add_argument(
        "strategy_names",
        nargs="+",
        help="Strategy names (e.g., qqq qqq_momentum_simple)",
    )
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--capital", type=float, default=10000.0, help="Starting capital"
    )

    args = parser.parse_args()

    folder_path = run_multiple_strategies(
        args.strategy_names, args.start_date, args.end_date, args.capital
    )

    print(f"\nAll results saved in: {folder_path}")
