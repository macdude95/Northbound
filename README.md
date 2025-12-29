# Northbound

A Python project for fetching, storing, and analyzing stock market data with automated trading strategies for leveraged ETFs (TQQQ/SQQQ) based on QQQ's 50-day moving average. Uses opening prices for optimal performance as discovered through extensive backtesting.

## Features

- Fetch daily stock aggregates (bars) for given tickers
- Store data locally in SQLite database for historical accumulation
- Support for QQQ, TQQQ, and SQQQ tickers with historical data back to 2010
- Visualize price data with matplotlib charts
- **NEW:** Trading strategy framework for QQQ-based strategies using TQQQ and SQQQ
- Backtesting engine with performance metrics (Sharpe ratio, max drawdown, etc.)
- Strategy comparison tools and visualizations
- Easy to extend for additional data types and strategies

## Setup

1. Create virtual environment: `python3 -m venv venv`
2. Activate: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set your Polygon.io API key in `.env` file
5. Initialize database: `python init_db.py`
6. Fetch data: `python stock_fetcher.py AAPL` (example for Apple stock)
7. Import historical CSV data: `python csv_import.py <TICKER> <CSV_FILE_PATH>` (e.g., for QQQ, TQQQ, SQQQ)
8. Visualize data: `python plot_stocks.py` (charts price history for QQQ, TQQQ, SQQQ)

## Trading Strategy Framework

Create and backtest trading strategies based on QQQ movements using TQQQ (3x leveraged) and SQQQ (3x inverse) ETFs.

### Creating a Strategy

1. Create a new strategy class in the `strategies/` folder that inherits from `BaseStrategy`
2. Implement the `decide_positions()` method to return position allocations based on QQQ data

Example strategy structure:

```python
from strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def decide_positions(self, qqq_data, current_date):
        # Analyze QQQ data and return positions
        return {'TQQQ': 0.7, 'SQQQ': 0.3}  # 70% TQQQ, 30% SQQQ
```

### Built-in Strategies

- `MomentumStrategy`: Go long TQQQ when QQQ trending up, SQQQ when trending down
- `BuyAndHoldTQQQ`: Simple buy and hold TQQQ strategy
- `BuyAndHoldSQQQ`: Simple buy and hold SQQQ strategy

### Backtesting Strategies

Run backtests and compare strategy performance:

```bash
python compare_strategies.py
```

This will:

- Run backtests for all built-in strategies
- Display performance metrics (total return, Sharpe ratio, max drawdown)
- Show comparative charts of portfolio value over time

### Custom Date Ranges

Modify the `main()` function in `compare_strategies.py` to specify date ranges:

```python
results = backtester.compare_strategies(strategies, start_date="2020-01-01", end_date="2023-12-31")
```
