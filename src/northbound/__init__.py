"""
Northbound - Trading strategy backtesting and visualization toolkit.
"""

from .backtester import Backtester, run_backtest
from .visualizer import PerformanceVisualizer, create_performance_chart
from .data_manager import backfill_all_tickers
from .allocation_calculator import AllocationCalculator

__version__ = "1.0.0"
__all__ = [
    "Backtester",
    "run_backtest",
    "PerformanceVisualizer",
    "create_performance_chart",
    "backfill_all_tickers",
    "AllocationCalculator",
]
