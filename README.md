# Trading Tools and Datasets Suite

A comprehensive suite for developing, backtesting, and visualizing trading strategies using historical market data.

## Setup

1. Create and activate virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Set up environment variables:
   Create a `.env` file with your Polygon.io API key:

```
POLYGON_API_KEY=your_api_key_here
```

3. Import base datasets:
   Place CSV files in `datasets/real_tickers/` or use `src/dataset_importer.py` programmatically

## Project Structure

```
├── datasets/
│   ├── real_tickers/     # Historical price data (CSV)
│   ├── strategy_allocations/ # Strategy allocation decisions (CSV)
│   └── simulations/      # Portfolio simulation results (CSV)
│       └── {date_range}_{capital}/ # Subfolders with simulation + HTML files
├── scripts/              # Command-line interface scripts
│   ├── run_simulation.py # Multi-strategy simulation runner
│   └── dataset_importer.py # Dataset import utilities
├── src/northbound/       # Main library package
│   ├── __init__.py       # Package initialization
│   ├── backtester.py     # Backtesting engine
│   ├── visualizer.py     # Performance visualization
│   └── data_manager.py   # Polygon API integration
├── strategy_configs/     # Strategy configuration files (JSON)
├── docs/
│   ├── Northbound_Product_Requirements.md # Product requirements
│   └── Northbound_Technical_Design.md     # Technical implementation details
└── README.md
```

## Usage

### Running Simulations

All simulation functionality is accessed through the main `run_simulation.py` script. First activate the virtual environment:

```bash
source venv/bin/activate
```

#### Run Multiple Strategy Simulations

**Purpose**: Run multiple strategies at once and generate comprehensive visualizations

**Command**:

```bash
# Run multiple strategies for a date range (just use strategy names)
python3 scripts/run_simulation.py qqq qqq_momentum_simple \
    --start-date 2020-06-01 --end-date 2025-06-30

# All files saved in: datasets/simulations/2020-06-01_2025-06-30_10000/
```

**Arguments**:

- `strategy_names`: Strategy names from strategy_configs/ folder (required, multiple allowed)
- `--start-date`: Start date (YYYY-MM-DD)
- `--end-date`: End date (YYYY-MM-DD)
- `--capital`: Starting capital (default: 10000)

**Outputs**: Creates subfolder with all strategy CSVs and comprehensive HTML visualization

#### Get Current Allocations

**Purpose**: Calculate current portfolio allocations for live trading (run daily)

**Command**:

```bash
# Get allocations for multiple strategies with portfolio percentages
python3 scripts/get_allocations.py qqq_momentum_simple:60 qqq_momentum_gradient:40

# Single strategy
python3 scripts/get_allocations.py qqq:100
```

**Arguments**:

- `strategy:percentage`: Strategy name and portfolio percentage (required, multiple allowed)

**Outputs**: Formatted table showing individual strategy allocations and final portfolio allocation

#### Automated Daily Emails

**Purpose**: Get daily portfolio allocation emails automatically via GitHub Actions

**Setup**: Follow `GitHub_Actions_Email_Setup.md` for complete instructions

**Features**:

- Runs Monday-Friday at NYSE open (9:30 AM ET)
- Emails personalized allocation recommendations
- Completely free using GitHub Actions
- Configurable strategies and recipients

#### Data Management

**Import Data**: Use `src/dataset_importer.py` programmatically or manually place CSV files in `datasets/real_tickers/`

**Backfill Data**: Use `src/data_manager.py` programmatically to update historical data via Polygon.io API

### Python API Usage

All components can also be used programmatically in Python:

```python
# Import from the northbound package
from northbound import Backtester, PerformanceVisualizer, backfill_all_tickers

# Dataset importing (from scripts)
from scripts.dataset_importer import import_single_dataset
import_single_dataset("/path/to/data.csv", "TICKER", "datasets")

# Backtesting
backtester = Backtester("strategy_configs/strategy.json")
results = backtester.run_simulation(start_date="2018-01-01")
backtester.save_results(results, "results.csv")

# Data backfilling
backfill_all_tickers("datasets")

# Visualization
viz = PerformanceVisualizer()
viz.compare_strategies(["results.csv"], "datasets/real_tickers/SPY.csv")
```

## Strategy Configuration

Strategies are defined in JSON format with:

- **underlying_symbol**: Ticker to calculate indicators on
- **calculation**: Technical indicator (currently SMA with period)
- **rules**: Allocation rules based on indicator thresholds

Rules support:

- Single threshold rules (above/below): `"ticker": "TICKER"` or `"ticker": "cash"`
- Between rules with interpolation: `"ticker_min": "TICKER/cash", "ticker_max": "TICKER/cash", "scaling_function": "linear"`
- Configurable scaling functions for smooth transitions (linear by default)
- Cash allocation using `"cash"` as the ticker value

**Example Config:**

```json
{
  "name": "QQQ Momentum Strategy",
  "underlying_symbol": "QQQ",
  "calculation": { "type": "SMA", "period": 50 },
  "rules": [
    { "max_threshold": -0.05, "ticker": "cash" },
    {
      "min_threshold": -0.02,
      "max_threshold": 0.02,
      "scaling_function": "linear",
      "ticker_min": "SQQQ",
      "ticker_max": "TQQQ"
    },
    { "min_threshold": 0.05, "ticker": "cash" }
  ]
}
```

## Features

- **Data Management**: Import from investing.com CSVs, backfill via Polygon.io API
- **Strategy Engine**: Configurable rules with SMA calculations and allocation interpolation
- **Backtesting**: Portfolio simulation with rebalancing and performance tracking
- **Visualization**: Interactive charts comparing strategies and benchmarks

## API Keys Required

- **Polygon.io**: For backfilling historical data (free tier available)

## Future Enhancements

- Additional technical indicators (RSI, MACD, etc.)
- Risk metrics and performance statistics
- Web-based configuration interface
- Real-time data integration
