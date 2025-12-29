# Northbound

A Python project for fetching and storing stock market data from Polygon.io APIs.

## Features

- Fetch daily stock aggregates (bars) for given tickers
- Store data locally in SQLite database for historical accumulation
- Support for QQQ, TQQQ, and SQQQ tickers with historical data back to 2010
- Visualize price data with matplotlib charts
- Easy to extend for additional data types

## Setup

1. Create virtual environment: `python3 -m venv venv`
2. Activate: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Set your Polygon.io API key in `.env` file
5. Initialize database: `python init_db.py`
6. Fetch data: `python stock_fetcher.py AAPL` (example for Apple stock)
7. Import historical CSV data: `python csv_import.py <TICKER> <CSV_FILE_PATH>` (e.g., for QQQ, TQQQ, SQQQ)
8. Visualize data: `python visualize.py [TICKER]` (charts price history; defaults to comparing QQQ, TQQQ, SQQQ)
