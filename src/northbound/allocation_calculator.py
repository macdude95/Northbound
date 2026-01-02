#!/usr/bin/env python3
"""
Live allocation calculator for trading strategies.
Calculates current portfolio allocations based on latest market data.
"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional


class IndicatorCalculator:
    """Calculates technical indicators."""

    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average for the latest available data."""
        if len(prices) < period:
            return None
        return prices.tail(period).mean()


class RuleEngine:
    """Evaluates strategy rules to determine allocations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.underlying_symbol = config["underlying_symbol"]
        self.calculation = config.get("calculation")  # Optional
        self.rules = config["rules"]

    def evaluate_current_allocation(
        self, current_price: float, price_history: pd.Series
    ) -> Dict[str, float]:
        """
        Evaluate rules for current market conditions and return target allocation.

        Args:
            current_price: Current price of underlying asset
            price_history: Historical prices for indicator calculation

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
            indicator_value = IndicatorCalculator.calculate_sma(price_history, period)

            if indicator_value is None:
                return {}  # Not enough data

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


class AllocationCalculator:
    """Calculates live portfolio allocations for trading strategies."""

    def __init__(self, datasets_dir: str = "datasets"):
        self.datasets_dir = datasets_dir

    def load_strategy_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate strategy configuration."""
        with open(config_path, "r") as f:
            config = json.load(f)

        # Basic validation
        required_fields = ["name", "underlying_symbol", "rules"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Config missing required field: {field}")

        return config

    def get_latest_prices(self, tickers: List[str]) -> Dict[str, float]:
        """
        Get the latest available prices for given tickers.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dict of ticker -> latest price
        """
        prices = {}

        for ticker in tickers:
            ticker_path = os.path.join(
                self.datasets_dir, "real_tickers", f"{ticker}.csv"
            )

            if os.path.exists(ticker_path):
                df = pd.read_csv(ticker_path)
                if not df.empty:
                    # Get the most recent price
                    latest_row = df.iloc[-1]
                    prices[ticker] = float(latest_row["Close"])
            else:
                print(f"Warning: No data found for {ticker}")

        return prices

    def get_price_history(self, ticker: str, periods: int = 200) -> pd.Series:
        """
        Get recent price history for indicator calculation.

        Args:
            ticker: Ticker symbol
            periods: Number of recent periods to return

        Returns:
            Series of closing prices
        """
        ticker_path = os.path.join(self.datasets_dir, "real_tickers", f"{ticker}.csv")

        if os.path.exists(ticker_path):
            df = pd.read_csv(ticker_path)
            if not df.empty:
                return df["Close"].tail(periods)

        return pd.Series()

    def calculate_allocation(self, strategy_config: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate current allocation for a strategy.

        Args:
            strategy_config: Strategy configuration dictionary

        Returns:
            Dict of ticker -> percentage allocation
        """
        # Get required tickers
        tickers = set([strategy_config["underlying_symbol"]])

        # Add all tickers that might be allocated
        for rule in strategy_config["rules"]:
            for ticker_field in ["ticker", "ticker_min", "ticker_max"]:
                if ticker_field in rule:
                    ticker = rule[ticker_field]
                    if ticker != "cash":
                        tickers.add(ticker)

        # Get latest prices
        prices = self.get_latest_prices(list(tickers))

        if not prices:
            return {}

        # Create rule engine and calculate allocation
        rule_engine = RuleEngine(strategy_config)
        underlying_symbol = strategy_config["underlying_symbol"]

        if underlying_symbol in prices:
            current_price = prices[underlying_symbol]
            price_history = self.get_price_history(underlying_symbol)

            allocation = rule_engine.evaluate_current_allocation(
                current_price, price_history
            )

            return allocation

        return {}

    def calculate_multi_strategy_allocation(
        self, strategy_allocations: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Calculate combined allocation across multiple strategies.

        Args:
            strategy_allocations: Dict of strategy_name -> portfolio_percentage

        Returns:
            Dict of ticker -> final portfolio percentage
        """
        final_allocation = {}

        for strategy_name, portfolio_percentage in strategy_allocations.items():
            config_path = f"strategy_configs/{strategy_name}.json"

            if not os.path.exists(config_path):
                print(f"Warning: Strategy config not found: {config_path}")
                continue

            try:
                config = self.load_strategy_config(config_path)
                strategy_alloc = self.calculate_allocation(config)

                # Scale by portfolio percentage and add to final allocation
                for ticker, percentage in strategy_alloc.items():
                    scaled_percentage = percentage * (portfolio_percentage / 100.0)

                    if ticker in final_allocation:
                        final_allocation[ticker] += scaled_percentage
                    else:
                        final_allocation[ticker] = scaled_percentage

            except Exception as e:
                print(f"Error calculating allocation for {strategy_name}: {e}")
                continue

        # Round to reasonable precision and remove near-zero allocations
        cleaned_allocation = {}
        for ticker, percentage in final_allocation.items():
            if percentage >= 0.01:  # Keep allocations >= 0.01%
                cleaned_allocation[ticker] = round(percentage, 2)

        return cleaned_allocation
