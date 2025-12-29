import pandas as pd
from typing import Dict
from .base_strategy import BaseStrategy


class MomentumStrategy(BaseStrategy):
    """
    Simple momentum strategy: Go long TQQQ when QQQ is trending up,
    go long SQQQ when QQQ is trending down.
    """

    def __init__(self, lookback_days: int = 5):
        super().__init__(f"Momentum_{lookback_days}d")
        self.lookback_days = lookback_days

    def decide_positions(
        self, qqq_data: pd.DataFrame, current_date: str
    ) -> Dict[str, float]:
        # Get data up to current date
        current_idx = qqq_data[qqq_data["date"] <= current_date].index[-1]
        start_idx = max(0, current_idx - self.lookback_days)

        if start_idx == current_idx:
            # Not enough data, hold cash
            return {"TQQQ": 0.0, "SQQQ": 0.0}

        # Calculate momentum (recent close vs lookback close)
        recent_close = qqq_data.loc[current_idx, "close"]
        lookback_close = qqq_data.loc[start_idx, "close"]

        if recent_close > lookback_close:
            # QQQ trending up, go long TQQQ
            return {"TQQQ": 1.0, "SQQQ": 0.0}
        else:
            # QQQ trending down, go long SQQQ
            return {"TQQQ": 0.0, "SQQQ": 1.0}


class BuyAndHoldTQQQ(BaseStrategy):
    """
    Simple buy and hold TQQQ strategy for comparison.
    """

    def __init__(self):
        super().__init__("Buy_Hold_TQQQ")

    def decide_positions(
        self, qqq_data: pd.DataFrame, current_date: str
    ) -> Dict[str, float]:
        return {"TQQQ": 1.0, "SQQQ": 0.0}


class BuyAndHoldQQQ(BaseStrategy):
    """
    Simple buy and hold QQQ strategy for comparison.
    Note: This strategy doesn't use TQQQ/SQQQ positions, but we need to return the dict format.
    The backtester will need to handle QQQ positions separately.
    """

    def __init__(self):
        super().__init__("Buy_Hold_QQQ")

    def decide_positions(
        self, qqq_data: pd.DataFrame, current_date: str
    ) -> Dict[str, float]:
        # For QQQ strategy, we'll use TQQQ field to represent QQQ position
        # This is a bit of a hack, but allows us to compare QQQ to leveraged ETFs
        return {"TQQQ": 1.0, "SQQQ": 0.0}  # Will be interpreted as QQQ position


class RollingAverageStrategy(BaseStrategy):
    """
    Strategy based on 50-day rolling average of QQQ.
    If QQQ is above its 50-day MA, allocate to TQQQ.
    If below, allocate to SQQQ.
    Uses a sliding scale based on distance from MA.
    """

    def __init__(self, ma_period: int = 50):
        super().__init__(f"50d_MA_Strategy")
        self.ma_period = ma_period

    def decide_positions(
        self, qqq_data: pd.DataFrame, current_date: str
    ) -> Dict[str, float]:
        # Need at least ma_period days of data
        if len(qqq_data) < self.ma_period:
            return {"TQQQ": 0.0, "SQQQ": 0.0}  # Hold cash if not enough data

        # Calculate 50-day moving average
        qqq_data_copy = qqq_data.copy()
        qqq_data_copy["ma"] = (
            qqq_data_copy["close"]
            .rolling(window=self.ma_period, min_periods=self.ma_period)
            .mean()
        )

        # Get current price and MA
        current_row = qqq_data_copy.iloc[-1]
        current_price = current_row["close"]
        current_ma = current_row["ma"]

        if pd.isna(current_ma):
            return {"TQQQ": 0.0, "SQQQ": 0.0}  # Not enough data for MA

        # Calculate deviation from MA (as percentage)
        deviation_pct = (current_price - current_ma) / current_ma

        # Allocate based on deviation
        # If significantly above MA (>5%), go 100% TQQQ
        # If significantly below MA (<-5%), go 100% SQQQ
        # Otherwise, scale linearly between -5% and +5%
        if deviation_pct > 0.05:
            tqqq_allocation = 1.0
            sqqq_allocation = 0.0
        elif deviation_pct < -0.05:
            tqqq_allocation = 0.0
            sqqq_allocation = 1.0
        else:
            # Linear interpolation between -5% and +5%
            # At 0% deviation: 50% TQQQ, 50% SQQQ
            # At +5% deviation: 100% TQQQ, 0% SQQQ
            # At -5% deviation: 0% TQQQ, 100% SQQQ
            tqqq_allocation = 0.5 + (deviation_pct / 0.05) * 0.5
            sqqq_allocation = 1.0 - tqqq_allocation

        return {"TQQQ": tqqq_allocation, "SQQQ": sqqq_allocation}


class MonthlyRollingAverageStrategy(BaseStrategy):
    """
    Strategy based on 50-day rolling average of QQQ, but rebalanced monthly.
    Only adjusts positions at the end of each month based on that month's average conditions.
    Holds the same allocation throughout each month.
    """

    def __init__(self, ma_period: int = 50):
        super().__init__(f"50d_MA_Monthly")
        self.ma_period = ma_period
        self.current_allocation = {"TQQQ": 0.0, "SQQQ": 0.0}  # Start with cash
        self.last_month = None

    def decide_positions(
        self, qqq_data: pd.DataFrame, current_date: str
    ) -> Dict[str, float]:
        # Need at least ma_period days of data
        if len(qqq_data) < self.ma_period:
            return {"TQQQ": 0.0, "SQQQ": 0.0}  # Hold cash if not enough data

        # Parse current date to get month
        current_dt = pd.to_datetime(current_date)
        current_month = current_dt.strftime("%Y-%m")

        # Only recalculate allocation at month end or if this is the first time
        if self.last_month != current_month:
            # Calculate 50-day moving average
            qqq_data_copy = qqq_data.copy()
            qqq_data_copy["ma"] = (
                qqq_data_copy["close"]
                .rolling(window=self.ma_period, min_periods=self.ma_period)
                .mean()
            )

            # Get current price and MA
            current_row = qqq_data_copy.iloc[-1]
            current_price = current_row["close"]
            current_ma = current_row["ma"]

            if pd.isna(current_ma):
                self.current_allocation = {
                    "TQQQ": 0.0,
                    "SQQQ": 0.0,
                }  # Not enough data for MA
            else:
                # Calculate deviation from MA (as percentage)
                deviation_pct = (current_price - current_ma) / current_ma

                # Allocate based on deviation (same logic as daily strategy)
                if deviation_pct > 0.05:
                    tqqq_allocation = 1.0
                    sqqq_allocation = 0.0
                elif deviation_pct < -0.05:
                    tqqq_allocation = 0.0
                    sqqq_allocation = 1.0
                else:
                    tqqq_allocation = 0.5 + (deviation_pct / 0.05) * 0.5
                    sqqq_allocation = 1.0 - tqqq_allocation

                self.current_allocation = {
                    "TQQQ": tqqq_allocation,
                    "SQQQ": sqqq_allocation,
                }

            self.last_month = current_month

        # Return the current monthly allocation
        return self.current_allocation


class WeeklyRollingAverageStrategy(BaseStrategy):
    """
    Strategy based on 50-day rolling average of QQQ, but rebalanced weekly.
    Only adjusts positions at the start of each week based on that week's conditions.
    Holds the same allocation throughout each week.
    """

    def __init__(self, ma_period: int = 50):
        super().__init__(f"50d_MA_Weekly")
        self.ma_period = ma_period
        self.current_allocation = {"TQQQ": 0.0, "SQQQ": 0.0}  # Start with cash
        self.last_week = None

    def decide_positions(
        self, qqq_data: pd.DataFrame, current_date: str
    ) -> Dict[str, float]:
        # Need at least ma_period days of data
        if len(qqq_data) < self.ma_period:
            return {"TQQQ": 0.0, "SQQQ": 0.0}  # Hold cash if not enough data

        # Parse current date to get week
        current_dt = pd.to_datetime(current_date)
        current_week = current_dt.strftime("%Y-%U")  # Year-week format

        # Only recalculate allocation at start of new week or if this is the first time
        if self.last_week != current_week:
            # Calculate 50-day moving average
            qqq_data_copy = qqq_data.copy()
            qqq_data_copy["ma"] = (
                qqq_data_copy["close"]
                .rolling(window=self.ma_period, min_periods=self.ma_period)
                .mean()
            )

            # Get current price and MA
            current_row = qqq_data_copy.iloc[-1]
            current_price = current_row["close"]
            current_ma = current_row["ma"]

            if pd.isna(current_ma):
                self.current_allocation = {
                    "TQQQ": 0.0,
                    "SQQQ": 0.0,
                }  # Not enough data for MA
            else:
                # Calculate deviation from MA (as percentage)
                deviation_pct = (current_price - current_ma) / current_ma

                # Allocate based on deviation (same logic as daily strategy)
                if deviation_pct > 0.05:
                    tqqq_allocation = 1.0
                    sqqq_allocation = 0.0
                elif deviation_pct < -0.05:
                    tqqq_allocation = 0.0
                    sqqq_allocation = 1.0
                else:
                    tqqq_allocation = 0.5 + (deviation_pct / 0.05) * 0.5
                    sqqq_allocation = 1.0 - tqqq_allocation

                self.current_allocation = {
                    "TQQQ": tqqq_allocation,
                    "SQQQ": sqqq_allocation,
                }

            self.last_week = current_week

        # Return the current weekly allocation
        return self.current_allocation


class BuyAndHoldSQQQ(BaseStrategy):
    """
    Simple buy and hold SQQQ strategy for comparison.
    """

    def __init__(self):
        super().__init__("Buy_Hold_SQQQ")

    def decide_positions(
        self, qqq_data: pd.DataFrame, current_date: str
    ) -> Dict[str, float]:
        return {"TQQQ": 0.0, "SQQQ": 1.0}
