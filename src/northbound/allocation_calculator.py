#!/usr/bin/env python3
"""
Live allocation calculator for trading strategies.
Calculates current portfolio allocations based on latest market data.
"""

import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
API_CALL_DELAY_SECONDS = float(os.getenv("API_CALL_DELAY_SECONDS", "2.0"))


class PolygonClient:
    """Client for Polygon.io API using official SDK."""

    def __init__(self, api_key: str):
        try:
            from polygon import RESTClient
            import time

            self.client = RESTClient(api_key)
            self.time = time
        except ImportError:
            raise ImportError(
                "polygon-api-client package required. Install with: pip install polygon-api-client"
            )

    def _api_call_delay(self):
        """Add configurable delay between API calls to avoid rate limiting."""
        if API_CALL_DELAY_SECONDS > 0:
            print(f"[DEBUG] API call delay: sleeping {API_CALL_DELAY_SECONDS}s")
            self.time.sleep(API_CALL_DELAY_SECONDS)

    def get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the latest available price for a ticker.
        Uses most recent closing price from historical data since real-time may not be available.

        Args:
            ticker: Stock symbol

        Returns:
            Latest available closing price or None if not available
        """
        try:
            # Get most recent day's data (last 5 days to ensure we get the latest)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=5)

            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")

            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=from_date,
                to=to_date,
                limit=5,  # Just need the most recent
            )

            if aggs:
                # Return the most recent closing price
                latest_agg = max(aggs, key=lambda x: x.timestamp)
                return latest_agg.close

        except Exception as e:
            print(f"Error fetching latest price for {ticker}: {e}")

        return None

    def get_recent_data(
        self, ticker: str, periods: int = 200
    ) -> tuple[float, pd.Series]:
        """
        Get recent data for a ticker - returns both latest price and historical series.

        Args:
            ticker: Ticker symbol
            periods: Number of recent periods to return in history

        Returns:
            Tuple of (latest_price, historical_series)
            latest_price: Most recent closing price
            historical_series: Series of last 'periods' closing prices
        """
        try:
            # Get recent data (last 200 days to ensure we have enough history)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=max(200, periods))

            from_date = start_date.strftime("%Y-%m-%d")
            to_date = end_date.strftime("%Y-%m-%d")

            print(
                f"[DEBUG] API call: get_aggs(ticker={ticker}, from={from_date}, to={to_date})"
            )

            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=1,
                timespan="day",
                from_=from_date,
                to=to_date,
                limit=500,  # Should be plenty for recent data
            )

            print(f"[DEBUG] API response: {len(aggs) if aggs else 0} records")

            if not aggs:
                print(f"[DEBUG] No data returned from API for {ticker}")
                return None, pd.Series()

            # Convert to DataFrame and extract data
            data = []
            for agg in aggs:
                data.append(
                    {
                        "Date": pd.Timestamp.fromtimestamp(
                            agg.timestamp / 1000
                        ).strftime("%Y-%m-%d"),
                        "Close": agg.close,
                    }
                )

            df = pd.DataFrame(data)

            if df.empty:
                print(f"[DEBUG] DataFrame is empty after conversion for {ticker}")
                return None, pd.Series()

            # Get latest price (most recent)
            latest_price = df["Close"].iloc[-1]

            # Get historical series (last 'periods' prices)
            historical_series = df["Close"].tail(periods)

            print(f"[DEBUG] Successfully processed {len(df)} records for {ticker}")
            return latest_price, historical_series

        except Exception as e:
            print(f"[DEBUG] Exception occurred for {ticker}: {type(e).__name__}: {e}")
            import traceback

            print(f"[DEBUG] Full traceback:\n{traceback.format_exc()}")
            return None, pd.Series()

    def get_price_history(self, ticker: str, periods: int = 200) -> pd.Series:
        """
        Get recent price history for indicator calculation.
        DEPRECATED: Use get_recent_data() instead for better efficiency.

        Args:
            ticker: Ticker symbol
            periods: Number of recent periods to return

        Returns:
            Series of closing prices
        """
        _, history = self.get_recent_data(ticker, periods)
        return history


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

    def __init__(self, data_dir: str = "data", debug: bool = False):
        self.data_dir = data_dir
        self.debug = debug

        # Initialize Polygon client for API calls
        if POLYGON_API_KEY:
            self.polygon_client = PolygonClient(POLYGON_API_KEY)
        else:
            raise ValueError("POLYGON_API_KEY not found in environment variables")

    def _debug_log(self, message: str, *args):
        """Log debug messages if debug mode is enabled."""
        if self.debug:
            print(f"[DEBUG] {message}", *args)

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
        Get the latest available prices for given tickers using Polygon API.
        Does NOT fall back to CSV data - requires fresh API data.

        Args:
            tickers: List of ticker symbols

        Returns:
            Dict of ticker -> latest price

        Raises:
            RuntimeError: If any price cannot be fetched from API
        """
        self._debug_log(f"Getting latest prices for tickers: {tickers}")
        prices = {}

        for ticker in tickers:
            self._debug_log(f"Fetching price for {ticker}...")

            price = self.polygon_client.get_latest_price(ticker)
            if price is not None:
                prices[ticker] = price
                self._debug_log(f"✓ API price for {ticker}: ${price}")
            else:
                error_msg = (
                    f"Failed to fetch latest price for {ticker} from Polygon API"
                )
                self._debug_log(f"✗ {error_msg}")
                raise RuntimeError(error_msg)

        self._debug_log(f"Final prices: {prices}")
        return prices

    def get_price_history(self, ticker: str, periods: int = 200) -> pd.Series:
        """
        Get recent price history for indicator calculation using Polygon API.
        Does NOT fall back to CSV data - requires fresh API data.

        Args:
            ticker: Ticker symbol
            periods: Number of recent periods to return

        Returns:
            Series of closing prices

        Raises:
            RuntimeError: If price history cannot be fetched from API
        """
        self._debug_log(f"Getting price history for {ticker} ({periods} periods)...")

        history = self.polygon_client.get_price_history(ticker, periods)
        if not history.empty:
            self._debug_log(f"✓ API history for {ticker}: {len(history)} data points")
            return history

        error_msg = f"Failed to fetch price history for {ticker} from Polygon API"
        self._debug_log(f"✗ {error_msg}")
        raise RuntimeError(error_msg)

    def calculate_allocation(self, strategy_config: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate current allocation for a strategy.

        Args:
            strategy_config: Strategy configuration dictionary

        Returns:
            Dict of ticker -> percentage allocation
        """
        strategy_name = strategy_config.get("name", "unknown")
        self._debug_log(f"Calculating allocation for strategy: {strategy_name}")

        # Get required tickers
        tickers = set([strategy_config["underlying_symbol"]])

        # Add all tickers that might be allocated
        for rule in strategy_config["rules"]:
            for ticker_field in ["ticker", "ticker_min", "ticker_max"]:
                if ticker_field in rule:
                    ticker = rule[ticker_field]
                    if isinstance(ticker, dict):
                        # Handle percentage allocations: extract ticker symbols
                        for alloc_ticker in ticker.keys():
                            if alloc_ticker != "cash":
                                tickers.add(alloc_ticker)
                    elif ticker != "cash":
                        tickers.add(ticker)

        self._debug_log(f"Required tickers: {list(tickers)}")

        # Get data for underlying symbol (both price and history in one call)
        rule_engine = RuleEngine(strategy_config)
        underlying_symbol = strategy_config["underlying_symbol"]

        self._debug_log(f"Fetching data for underlying symbol: {underlying_symbol}")
        current_price, price_history = self.polygon_client.get_recent_data(
            underlying_symbol
        )

        if current_price is None:
            error_msg = f"Failed to fetch current price for {underlying_symbol} from Polygon API"
            self._debug_log(f"✗ {error_msg}")
            raise RuntimeError(error_msg)

        if price_history.empty:
            error_msg = f"Failed to fetch price history for {underlying_symbol} from Polygon API"
            self._debug_log(f"✗ {error_msg}")
            raise RuntimeError(error_msg)

        self._debug_log(f"✓ Current price for {underlying_symbol}: ${current_price}")
        self._debug_log(f"✓ Price history length: {len(price_history)}")

        # Get prices for allocation tickers (if different from underlying)
        allocation_tickers = set()
        for rule in strategy_config["rules"]:
            for ticker_field in ["ticker", "ticker_min", "ticker_max"]:
                if ticker_field in rule:
                    ticker = rule[ticker_field]
                    if isinstance(ticker, dict):
                        # Handle percentage allocations: extract ticker symbols
                        for alloc_ticker in ticker.keys():
                            if (
                                alloc_ticker != "cash"
                                and alloc_ticker != underlying_symbol
                            ):
                                allocation_tickers.add(alloc_ticker)
                    elif ticker != "cash" and ticker != underlying_symbol:
                        allocation_tickers.add(ticker)

        if allocation_tickers:
            # Add delay before fetching allocation ticker data
            self.polygon_client._api_call_delay()

            self._debug_log(
                f"Fetching prices for allocation tickers: {list(allocation_tickers)}"
            )
            # For allocation tickers, we only need current prices
            prices = {}
            for ticker in allocation_tickers:
                price, _ = self.polygon_client.get_recent_data(ticker, periods=1)
                if price is not None:
                    prices[ticker] = price
                else:
                    error_msg = f"Failed to fetch price for allocation ticker {ticker}"
                    self._debug_log(f"✗ {error_msg}")
                    raise RuntimeError(error_msg)

            self._debug_log(f"✓ Allocation ticker prices: {prices}")

        allocation = rule_engine.evaluate_current_allocation(
            current_price, price_history
        )

        self._debug_log(f"Final allocation: {allocation}")
        return allocation

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

    def debug_test_allocation(self, strategy_name: str) -> Dict[str, float]:
        """
        Debug test method to calculate allocation with full debug output.

        Args:
            strategy_name: Name of the strategy to test (without .json extension)

        Returns:
            Dict of ticker -> percentage allocation
        """
        print(f"\n{'='*60}")
        print(f"DEBUG TEST: {strategy_name}")
        print(f"{'='*60}")

        # Enable debug mode
        original_debug = self.debug
        self.debug = True

        try:
            config_path = f"strategy_configs/{strategy_name}.json"
            config = self.load_strategy_config(config_path)
            allocation = self.calculate_allocation(config)

            print(f"\n{'='*60}")
            print(f"FINAL RESULT: {allocation}")
            print(f"{'='*60}\n")

            return allocation
        finally:
            # Restore original debug setting
            self.debug = original_debug
