import sqlite3
import pandas as pd
from typing import List, Dict, Any
from strategies.base_strategy import BaseStrategy
import numpy as np


class Backtester:
    """
    Backtesting engine for trading strategies on leveraged ETFs.
    """

    def __init__(self, db_path: str = "stocks.db"):
        self.db_path = db_path
        self.data_cache = {}

    def load_data(self, tickers: List[str]) -> Dict[str, pd.DataFrame]:
        """
        Load historical data for given tickers from database.
        """
        if tickers[0] in self.data_cache:
            return {ticker: self.data_cache[ticker] for ticker in tickers}

        conn = sqlite3.connect(self.db_path)

        data = {}
        for ticker in tickers:
            df = pd.read_sql_query(
                "SELECT date, open, high, low, close, volume FROM aggregates WHERE ticker = ? ORDER BY date",
                conn,
                params=(ticker.upper(),),
            )
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            data[ticker] = df
            self.data_cache[ticker] = df

        conn.close()
        return data

    def run_backtest(
        self, strategy: BaseStrategy, start_date: str = None, end_date: str = None
    ) -> Dict[str, Any]:
        """
        Run backtest for a strategy.

        Returns dict with:
        - dates: list of dates
        - portfolio_values: list of portfolio values over time
        - daily_returns: list of daily returns
        - positions: list of position dicts over time
        - metrics: performance metrics
        """
        # Load data
        data = self.load_data(["QQQ", "TQQQ", "SQQQ"])
        qqq_data = data["QQQ"]
        tqqq_data = data["TQQQ"]
        sqqq_data = data["SQQQ"]

        # Filter date range
        if start_date:
            qqq_data = qqq_data[
                qqq_data["date"] >= pd.to_datetime(start_date)
            ].reset_index(drop=True)
        if end_date:
            qqq_data = qqq_data[
                qqq_data["date"] <= pd.to_datetime(end_date)
            ].reset_index(drop=True)

        # Find common dates where all tickers have data
        tqqq_dates = set(tqqq_data["date"])
        sqqq_dates = set(sqqq_data["date"])
        qqq_dates = set(qqq_data["date"])

        common_dates = sorted(list(qqq_dates & tqqq_dates & sqqq_dates))

        # Filter all data to common dates
        qqq_data = qqq_data[qqq_data["date"].isin(common_dates)].reset_index(drop=True)
        tqqq_data = tqqq_data[tqqq_data["date"].isin(common_dates)].reset_index(
            drop=True
        )
        sqqq_data = sqqq_data[sqqq_data["date"].isin(common_dates)].reset_index(
            drop=True
        )

        # Sort by date
        qqq_data = qqq_data.sort_values("date").reset_index(drop=True)
        tqqq_data = tqqq_data.sort_values("date").reset_index(drop=True)
        sqqq_data = sqqq_data.sort_values("date").reset_index(drop=True)

        all_dates = qqq_data["date"].tolist()

        # Initialize backtest
        portfolio_value = 10000.0  # Start with $10,000
        portfolio_values = [portfolio_value]
        daily_returns = [0.0]
        positions_history = []

        # Run backtest day by day
        for i in range(1, len(all_dates)):
            current_date = all_dates[i].strftime("%Y-%m-%d")

            # Get strategy positions
            positions = strategy.decide_positions(qqq_data.iloc[: i + 1], current_date)
            positions_history.append(positions)

            # Calculate daily return based on positions using CLOSING prices
            if strategy.get_name() == "Buy_Hold_QQQ":
                # For QQQ strategy, use QQQ returns directly
                qqq_prev = qqq_data.loc[i - 1, "close"]
                qqq_curr = qqq_data.loc[i, "close"]
                daily_return = (qqq_curr - qqq_prev) / qqq_prev if qqq_prev != 0 else 0
            else:
                # For leveraged ETF strategies, use TQQQ/SQQQ returns
                tqqq_prev = tqqq_data.loc[i - 1, "close"]
                tqqq_curr = tqqq_data.loc[i, "close"]
                sqqq_prev = sqqq_data.loc[i - 1, "close"]
                sqqq_curr = sqqq_data.loc[i, "close"]

                tqqq_return = (
                    (tqqq_curr - tqqq_prev) / tqqq_prev if tqqq_prev != 0 else 0
                )
                sqqq_return = (
                    (sqqq_curr - sqqq_prev) / sqqq_prev if sqqq_prev != 0 else 0
                )

                daily_return = (
                    positions.get("TQQQ", 0) * tqqq_return
                    + positions.get("SQQQ", 0) * sqqq_return
                )

            # Update portfolio value
            portfolio_value *= 1 + daily_return
            portfolio_values.append(portfolio_value)
            daily_returns.append(daily_return)

        # Calculate metrics
        total_return = (portfolio_values[-1] - portfolio_values[0]) / portfolio_values[
            0
        ]
        annual_return = total_return / (
            len(all_dates) / 252
        )  # Assuming 252 trading days per year

        # Sharpe ratio (assuming 0% risk-free rate)
        excess_returns = np.array(daily_returns) - 0.0
        sharpe_ratio = (
            np.sqrt(252) * excess_returns.mean() / excess_returns.std()
            if excess_returns.std() > 0
            else 0
        )

        # Maximum drawdown
        peak = portfolio_values[0]
        max_drawdown = 0
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

        metrics = {
            "total_return": total_return,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "final_value": portfolio_values[-1],
            "start_value": portfolio_values[0],
        }

        return {
            "dates": [d.strftime("%Y-%m-%d") for d in all_dates],
            "portfolio_values": portfolio_values,
            "daily_returns": daily_returns,
            "positions": positions_history,
            "metrics": metrics,
            "strategy_name": strategy.get_name(),
        }

    def compare_strategies(
        self,
        strategies: List[BaseStrategy],
        start_date: str = None,
        end_date: str = None,
    ) -> Dict[str, Dict]:
        """
        Run backtests for multiple strategies and return comparison results.
        """
        results = {}
        for strategy in strategies:
            results[strategy.get_name()] = self.run_backtest(
                strategy, start_date, end_date
            )
        return results
