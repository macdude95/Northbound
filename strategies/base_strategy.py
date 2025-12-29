from abc import ABC, abstractmethod
from typing import Dict, List
import pandas as pd


class BaseStrategy(ABC):
    """
    Abstract base class for trading strategies based on QQQ movements.

    Strategies should implement the decide_positions method to determine
    allocations to TQQQ and SQQQ based on QQQ data.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def decide_positions(
        self, qqq_data: pd.DataFrame, current_date: str
    ) -> Dict[str, float]:
        """
        Decide positions for TQQQ and SQQQ based on QQQ data up to current_date.

        Args:
            qqq_data: DataFrame with QQQ historical data (columns: date, open, high, low, close, volume)
            current_date: Current date string (YYYY-MM-DD)

        Returns:
            Dict with 'TQQQ' and 'SQQQ' keys, values are position sizes
            (e.g., {'TQQQ': 0.7, 'SQQQ': 0.3} means 70% TQQQ, 30% SQQQ)
            Values should sum to 1.0 (fully invested) or less (cash position)
        """
        pass

    def get_name(self) -> str:
        """Return strategy name."""
        return self.name
