#!/usr/bin/env python3
"""
Backtesting engine for trading strategies.
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any


class IndicatorCalculator:
    """Calculates technical indicators."""

    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return prices.rolling(window=period).mean()


class RuleEngine:
    """Evaluates strategy rules to determine allocations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.underlying_symbol = config["underlying_symbol"]
        self.calculation = config.get("calculation")  # Optional
        self.rules = config["rules"]

    def evaluate_rules(self, data: pd.DataFrame, date_idx: int) -> Dict[str, float]:
        """
        Evaluate rules for a given date and return target allocation.

        Args:
            data: DataFrame with price data
            date_idx: Index of current date in data

        Returns:
            Dict of ticker -> percentage allocation
        """
        # If no calculation is needed (buy-and-hold style), just return the rule allocation
        if not self.calculation:
            # For strategies without calculations, just return the first rule's allocation
            if self.rules:
                rule = self.rules[0]
                return self._parse_allocation(rule.get("ticker"))
            return {}

        # Calculate indicator for technical analysis strategies
        if self.calculation["type"] == "SMA":
            period = self.calculation["period"]
            if date_idx < period - 1:
                return {}  # Not enough data

            prices = data["Close"][: date_idx + 1]
            indicator_value = IndicatorCalculator.calculate_sma(prices, period).iloc[-1]
            current_price = data["Close"].iloc[date_idx]

            # Calculate deviation (current - SMA) / SMA
            deviation = (current_price - indicator_value) / indicator_value
        else:
            raise ValueError(
                f"Unsupported calculation type: {self.calculation['type']}"
            )

        # Evaluate rules in order
        for rule in self.rules:
            if "min_threshold" in rule and "max_threshold" in rule:
                # Between rule with interpolation
                min_thresh = rule["min_threshold"]
                max_thresh = rule["max_threshold"]

                if min_thresh <= deviation <= max_thresh:
                    # Interpolate between min and max allocations
                    if "ticker_min" in rule and "ticker_max" in rule:
                        ticker_min = rule["ticker_min"]
                        ticker_max = rule["ticker_max"]
                        scaling_func = rule.get("scaling_function", "linear")

                        # Calculate interpolation factor
                        if max_thresh == min_thresh:
                            factor = 0.5  # Edge case
                        else:
                            raw_factor = (deviation - min_thresh) / (
                                max_thresh - min_thresh
                            )
                            factor = self._apply_scaling_function(
                                raw_factor, scaling_func
                            )

                        # Create interpolated allocation
                        interpolated = {}
                        if ticker_min == ticker_max:
                            # Same ticker, allocate 100%
                            interpolated[ticker_min] = 100.0
                        else:
                            # Different tickers, interpolate between them
                            interpolated[ticker_min] = 100.0 * (1 - factor)
                            interpolated[ticker_max] = 100.0 * factor

                        return interpolated

            elif "max_threshold" in rule:
                # Below rule
                if deviation <= rule["max_threshold"]:
                    return self._parse_allocation(rule.get("ticker"))

            elif "min_threshold" in rule:
                # Above rule
                if deviation >= rule["min_threshold"]:
                    return self._parse_allocation(rule.get("ticker"))

        # Default: no allocation
        return {}

    def _apply_scaling_function(self, factor: float, scaling_func: str) -> float:
        """
        Apply scaling function to interpolation factor.

        Args:
            factor: Raw interpolation factor (0-1)
            scaling_func: Scaling function name

        Returns:
            Scaled factor
        """
        if scaling_func == "linear":
            return factor
        else:
            raise ValueError(f"Unsupported scaling function: {scaling_func}")

    def _parse_allocation(self, allocation_value) -> Dict[str, float]:
        """
        Parse allocation value into dictionary format.

        Args:
            allocation_value: Either a ticker string, "cash", or allocation dict

        Returns:
            Dict of ticker -> percentage
        """
        if isinstance(allocation_value, str):
            if allocation_value == "cash":
                # Special case: 100% cash allocation
                return {"cash": 100.0}
            else:
                # Simple ticker string -> 100% allocation
                return {allocation_value: 100.0}
        elif isinstance(allocation_value, dict):
            # Already in dict format (for future percentage support)
            return allocation_value
        else:
            return {}


class PortfolioSimulator:
    """Simulates portfolio performance using closing prices only (simplified approach)."""

    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.portfolio_value = initial_capital
        self.previous_allocation = {}  # Track previous allocation for return calc

    def calculate_daily_return(
        self,
        target_allocation: Dict[str, float],
        current_prices: Dict[str, float],
        previous_prices: Dict[str, float],
    ) -> float:
        """
        Calculate daily return using closing prices only (simplified approach).

        Args:
            target_allocation: Target allocation percentages
            current_prices: Current day's closing prices
            previous_prices: Previous day's closing prices

        Returns:
            Daily return as decimal
        """
        if not previous_prices:
            return 0.0  # First day, no return

        # Calculate weighted return based on target allocation
        daily_return = 0.0

        for ticker, percentage in target_allocation.items():
            if ticker == "cash":
                continue  # Cash earns 0 return
            elif ticker in current_prices and ticker in previous_prices:
                # Calculate return for this ticker
                prev_price = previous_prices[ticker]
                curr_price = current_prices[ticker]
                ticker_return = (
                    (curr_price - prev_price) / prev_price if prev_price != 0 else 0
                )
                daily_return += ticker_return * (percentage / 100)

        return daily_return

    def update_portfolio_value(self, daily_return: float) -> float:
        """Update portfolio value based on daily return."""
        self.portfolio_value *= 1 + daily_return
        return self.portfolio_value

    def get_portfolio_value(self) -> float:
        """Get current portfolio value."""
        return self.portfolio_value


class Backtester:
    """Main backtesting engine."""

    def __init__(self, config_path: str, datasets_dir: str = "datasets"):
        self.config_path = config_path
        self.datasets_dir = datasets_dir
        self.config = None
        self.rule_engine = None
        self.portfolio = None
        self.results = []

    def load_config(self) -> None:
        """Load and validate strategy configuration."""
        with open(self.config_path, "r") as f:
            self.config = json.load(f)

        # Validate configuration
        self.validate_config(self.config_path)

        self.rule_engine = RuleEngine(self.config)

    def validate_config(self, config_path: str) -> None:
        """
        Validate strategy configuration for correctness.

        Args:
            config_path: Path to config file (for error messages)

        Raises:
            ValueError: If configuration is invalid
        """
        config = self.config

        # Check required top-level fields
        required_fields = ["name", "underlying_symbol", "rules"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Config missing required field: {field}")

        # Validate calculation (optional)
        if "calculation" in config:
            calculation = config["calculation"]
            if not isinstance(calculation, dict):
                raise ValueError("calculation must be a dictionary")

            calc_type = calculation.get("type")
            if calc_type not in ["SMA"]:
                raise ValueError(
                    f"Unsupported calculation type: {calc_type}. Supported: SMA"
                )

            if calc_type == "SMA":
                if "period" not in calculation:
                    raise ValueError("SMA calculation requires 'period' field")
                if (
                    not isinstance(calculation["period"], int)
                    or calculation["period"] <= 0
                ):
                    raise ValueError("SMA period must be a positive integer")

        # Check underlying symbol exists
        underlying_symbol = config["underlying_symbol"]
        ticker_path = os.path.join(
            self.datasets_dir, "real_tickers", f"{underlying_symbol}.csv"
        )
        if not os.path.exists(ticker_path):
            raise ValueError(
                f"Underlying symbol '{underlying_symbol}' not found in datasets/real_tickers/"
            )

        # Validate rules
        rules = config["rules"]
        if not isinstance(rules, list) or len(rules) == 0:
            raise ValueError("rules must be a non-empty list")

        # Collect all tickers used in rules
        all_tickers = set()
        threshold_ranges = []

        for i, rule in enumerate(rules):
            # Check rule structure
            if not isinstance(rule, dict):
                raise ValueError(f"Rule {i} must be a dictionary")

            # Collect tickers from this rule
            for ticker_field in ["ticker", "ticker_min", "ticker_max"]:
                if ticker_field in rule:
                    ticker = rule[ticker_field]
                    if ticker != "cash":
                        all_tickers.add(ticker)
                        # Check ticker exists in datasets
                        ticker_path = os.path.join(
                            self.datasets_dir, "real_tickers", f"{ticker}.csv"
                        )
                        if not os.path.exists(ticker_path):
                            raise ValueError(
                                f"Ticker '{ticker}' in rule {i} not found in datasets/real_tickers/"
                            )

            # Validate scaling function
            if "scaling_function" in rule:
                scaling_func = rule["scaling_function"]
                if scaling_func not in ["linear"]:
                    raise ValueError(
                        f"Unsupported scaling function '{scaling_func}' in rule {i}. Supported: linear"
                    )

            # For strategies without calculation, rules don't need thresholds
            if "calculation" not in config:
                continue

            # Collect threshold ranges for coverage check (only for technical analysis strategies)
            min_thresh = rule.get("min_threshold")
            max_thresh = rule.get("max_threshold")

            if min_thresh is not None and max_thresh is not None:
                # Between rule
                if min_thresh >= max_thresh:
                    raise ValueError(
                        f"Rule {i}: min_threshold ({min_thresh}) must be < max_threshold ({max_thresh})"
                    )
                threshold_ranges.append((min_thresh, max_thresh))
            elif max_thresh is not None:
                # Below rule
                threshold_ranges.append((float("-inf"), max_thresh))
            elif min_thresh is not None:
                # Above rule
                threshold_ranges.append((min_thresh, float("inf")))
            else:
                raise ValueError(
                    f"Rule {i} must have at least one threshold (min_threshold or max_threshold)"
                )

        # Check threshold coverage - ensure no gaps
        threshold_ranges.sort()

        # Check for gaps between ranges
        for i in range(len(threshold_ranges) - 1):
            current_max = threshold_ranges[i][1]
            next_min = threshold_ranges[i + 1][0]
            if current_max < next_min:
                raise ValueError(
                    f"Gap in threshold coverage between {current_max} and {next_min}. Rules must provide complete coverage."
                )

        print(f"✓ Config validation passed for {config_path}")

    def load_data(self) -> Dict[str, pd.DataFrame]:
        """Load required price data."""
        data = {}

        # Load underlying data
        underlying_path = os.path.join(
            self.datasets_dir, "real_tickers", f"{self.config['underlying_symbol']}.csv"
        )
        if os.path.exists(underlying_path):
            data[self.config["underlying_symbol"]] = pd.read_csv(underlying_path)
        else:
            raise FileNotFoundError(f"Underlying data not found: {underlying_path}")

        # Load all tickers that might be allocated
        allocated_tickers = set()
        for rule in self.config["rules"]:
            # Check for ticker strings
            if "ticker" in rule:
                allocated_tickers.add(rule["ticker"])
            if "ticker_min" in rule:
                allocated_tickers.add(rule["ticker_min"])
            if "ticker_max" in rule:
                allocated_tickers.add(rule["ticker_max"])

            # Also check for legacy allocation objects (for backwards compatibility)
            for alloc_key in ["allocation", "allocation_min", "allocation_max"]:
                if alloc_key in rule:
                    alloc_value = rule[alloc_key]
                    if isinstance(alloc_value, dict):
                        allocated_tickers.update(alloc_value.keys())
                    elif isinstance(alloc_value, str):
                        allocated_tickers.add(alloc_value)

        # Remove cash from tickers
        allocated_tickers.discard("cash")

        for ticker in allocated_tickers:
            if ticker not in data:
                ticker_path = os.path.join(
                    self.datasets_dir, "real_tickers", f"{ticker}.csv"
                )
                if os.path.exists(ticker_path):
                    data[ticker] = pd.read_csv(ticker_path)
                else:
                    print(f"Warning: Data not found for {ticker}, skipping")

        return data

    def run_simulation(
        self,
        start_date: str = None,
        end_date: str = None,
        initial_capital: float = 10000.0,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run the backtest simulation.

        Args:
            start_date: Start date for simulation (YYYY-MM-DD)
            end_date: End date for simulation (YYYY-MM-DD)
            initial_capital: Starting portfolio value

        Returns:
            Tuple of (strategy_results, simulation_results)
            - strategy_results: Full date range allocations
            - simulation_results: Specified date range with portfolio state
        """
        if not self.config:
            self.load_config()

        data = self.load_data()
        underlying_data = data[self.config["underlying_symbol"]]

        # Calculate strategy allocations over FULL available data
        strategy_results = []
        for idx, row in underlying_data.iterrows():
            current_date = row["Date"]

            # Get prices for all tickers on this date
            prices = {}
            for ticker, df in data.items():
                date_row = df[df["Date"] == current_date]
                if not date_row.empty:
                    prices[ticker] = float(date_row["Close"].iloc[0])

            if not prices:
                continue

            # Evaluate rules for strategy allocation
            target_allocation = self.rule_engine.evaluate_rules(underlying_data, idx)

            strategy_result = {
                "Date": current_date,
                "Allocation": target_allocation.copy(),
            }

            strategy_results.append(strategy_result)

        strategy_df = pd.DataFrame(strategy_results)

        # Filter for simulation date range
        simulation_data = underlying_data.copy()
        if start_date:
            simulation_data = simulation_data[simulation_data["Date"] >= start_date]
        if end_date:
            simulation_data = simulation_data[simulation_data["Date"] <= end_date]

        simulation_data = simulation_data.reset_index(drop=True)

        # Run portfolio simulation over specified date range
        self.portfolio = PortfolioSimulator(initial_capital)

        simulation_results = []
        previous_prices = {}

        for idx, row in simulation_data.iterrows():
            current_date = row["Date"]

            # Get prices for all tickers on this date
            current_prices = {}
            for ticker, df in data.items():
                date_row = df[df["Date"] == current_date]
                if not date_row.empty:
                    current_prices[ticker] = float(date_row["Close"].iloc[0])

            if not current_prices:
                continue

            # Get allocation for this date from strategy results
            date_allocation = {}
            date_row = strategy_df[strategy_df["Date"] == current_date]
            if not date_row.empty:
                # Parse the JSON string back to dict
                alloc_str = date_row["Allocation"].iloc[0]
                if isinstance(alloc_str, str):
                    date_allocation = eval(alloc_str)
                else:
                    date_allocation = alloc_str

            # Calculate daily return using closing prices only
            daily_return = self.portfolio.calculate_daily_return(
                date_allocation, current_prices, previous_prices
            )

            # Update portfolio value
            portfolio_value = self.portfolio.update_portfolio_value(daily_return)

            # Record results
            simulation_result = {
                "Date": current_date,
                "Strategy_Name": self.config["name"],
                "Portfolio_Value": portfolio_value,
                "Daily_Return": daily_return,
            }

            simulation_results.append(simulation_result)

            # Store current prices for next iteration
            previous_prices = current_prices.copy()

        return strategy_df, pd.DataFrame(simulation_results)

    def save_results(
        self, results_tuple, strategy_path: str, simulation_path: str = None
    ) -> None:
        """Save strategy allocations and simulation results to separate CSV files."""
        if isinstance(results_tuple, tuple):
            strategy_df, simulation_df = results_tuple
        else:
            # Legacy support
            strategy_df = results_tuple
            simulation_df = None

        # Save strategy allocation data
        strategy_output = strategy_df.copy()
        strategy_output["Allocation"] = strategy_output["Allocation"].apply(json.dumps)
        strategy_output.to_csv(strategy_path, index=False)
        print(f"Strategy allocations saved to {strategy_path}")

        # Save simulation results (portfolio state) if path provided and data exists
        if simulation_path and simulation_df is not None:
            simulation_output = simulation_df.copy()
            simulation_output.to_csv(simulation_path, index=False)
            print(f"Simulation results saved to {simulation_path}")


def run_backtest(
    config_path: str,
    strategy_path: str,
    simulation_path: str = None,
    base_path: str = None,
    **kwargs,
) -> str:
    """
    Run a backtest from config file.

    Args:
        config_path: Path to strategy config JSON
        strategy_path: Path to save strategy allocations CSV
        simulation_path: Optional path to save simulation results CSV
        base_path: Base path for the simulation run (for HTML saving)
        **kwargs: Additional arguments for run_simulation

    Returns:
        Base path where results were saved
    """
    backtester = Backtester(config_path)
    strategy_results, simulation_results = backtester.run_simulation(**kwargs)
    backtester.save_results(
        (strategy_results, simulation_results), strategy_path, simulation_path
    )
    return base_path or os.path.dirname(strategy_path)
