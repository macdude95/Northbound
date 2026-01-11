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
        self.calculations = config["calculations"]  # New format only
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
        return self._evaluate_multi_condition_rules(current_price, price_history)

    def _evaluate_multi_condition_rules(
        self, current_price: float, price_history: pd.Series
    ) -> Dict[str, float]:
        """Evaluate rules using new multi-condition format."""
        # Calculate all indicators
        indicators = {}
        for calc in self.calculations:
            calc_name = calc["name"]
            calc_type = calc["type"]

            if calc_type == "SMA":
                period = calc["period"]
                if len(price_history) < period:
                    indicators[calc_name] = None  # Not enough data
                    continue

                sma_value = IndicatorCalculator.calculate_sma(price_history, period)
                if sma_value is not None:
                    # Calculate deviation from SMA: (current - SMA) / SMA
                    indicators[calc_name] = (current_price - sma_value) / sma_value

            elif calc_type == "EMA":
                period = calc["period"]
                if len(price_history) < period:
                    indicators[calc_name] = None  # Not enough data
                    continue

                # Calculate EMA
                ema_value = price_history.ewm(span=period, adjust=False).mean().iloc[-1]
                # Calculate deviation from EMA: (current - EMA) / EMA
                indicators[calc_name] = (current_price - ema_value) / ema_value

            elif calc_type == "RSI":
                period = calc.get("period", 14)
                if (
                    len(price_history) < period + 1
                ):  # Need extra data for RSI calculation
                    indicators[calc_name] = None
                    continue

                # Simple RSI calculation
                delta = price_history.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                indicators[calc_name] = rsi.iloc[-1]

            else:
                raise ValueError(f"Unsupported calculation type: {calc_type}")

        # Evaluate rules with conditions
        for rule in self.rules:
            if "conditions" not in rule:
                continue  # Skip legacy rules

            conditions = rule["conditions"]
            logic = rule.get("logic", "AND")

            # Evaluate all conditions
            condition_results = []
            for condition in conditions:
                calc_name = condition["calculation"]
                operator = condition["operator"]
                threshold = condition["threshold"]

                if indicators.get(calc_name) is None:
                    condition_results.append(False)  # Not enough data
                    continue

                indicator_value = indicators[calc_name]

                # Evaluate condition
                if operator == ">":
                    result = indicator_value > threshold
                elif operator == "<":
                    result = indicator_value < threshold
                elif operator == ">=":
                    result = indicator_value >= threshold
                elif operator == "<=":
                    result = indicator_value <= threshold
                elif operator == "==":
                    result = (
                        abs(indicator_value - threshold) < 1e-6
                    )  # Floating point comparison
                else:
                    raise ValueError(f"Unsupported operator: {operator}")

                condition_results.append(result)

            # Combine conditions with logic
            if logic == "AND":
                rule_triggered = all(condition_results)
            elif logic == "OR":
                rule_triggered = any(condition_results)
            else:
                raise ValueError(f"Unsupported logic: {logic}")

            if rule_triggered:
                return self._parse_allocation(rule.get("ticker"))

        return {}

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

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir

    def load_strategy_config(self, config_path: str) -> Dict[str, Any]:
        """Load and validate strategy configuration."""
        with open(config_path, "r") as f:
            config = json.load(f)

        # Basic validation
        required_fields = ["name", "underlying_symbol", "calculations", "rules"]
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
            ticker_path = os.path.join(self.data_dir, "real_tickers", f"{ticker}.csv")

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
        ticker_path = os.path.join(self.data_dir, "real_tickers", f"{ticker}.csv")

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
