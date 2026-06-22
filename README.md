# Trading Tools and Datasets Suite

A comprehensive suite for developing, backtesting, and visualizing trading strategies using historical market data.

## Inspiration

This project was inspired by an interview with Mallik (@RealTQQQTrader), a systematic trader who specializes in leveraged ETF strategies. In the interview, Mallik discusses his trading philosophy and automated trading systems that operate without manual intervention.

**Key Interview**: [Systematic Trading with Mallik](https://youtu.be/pBS5vrqrUjk?si=IvUNjqhRPm7ermRP) - Twitter: [@RealTQQQTrader](https://x.com/RealTQQQTrader)

Mallik's automated system "whitelight" is available on Collective2: https://collective2.com/details/141158577

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

3. Import base data:
   Place CSV files in `data/real_tickers/` or use `scripts/dataset_importer.py` programmatically

## Project Structure

```
├── data/
│   ├── real_tickers/     # Historical price data (CSV)
│   └── simulations/      # Portfolio simulation results (CSV)
│       └── {date_range}_{capital}/ # Subfolders with simulation + HTML files
├── scripts/              # Command-line interface scripts
│   ├── run_simulation.py # Multi-strategy simulation runner
│   ├── dataset_importer.py # Dataset import utilities
│   └── action_card.py    # Standalone weekly TQQQ hedged-DCA action card (stdlib only)
├── src/northbound/       # Main library package
│   ├── __init__.py       # Package initialization
│   ├── backtester.py     # Backtesting engine
│   ├── visualizer.py     # Performance visualization
│   └── data_manager.py   # Polygon API integration
├── strategy_configs/     # Strategy configuration files (JSON)
├── portfolio_configs/    # Portfolio configuration files (JSON)
├── portfolio-calculator/ # Mobile portfolio rebalancing calculator
│   ├── index.html        # Calculator interface
│   ├── calculator.js     # Calculation logic
│   └── styles.css        # Mobile styling
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

# All files saved in: data/simulations/2020-06-01_2025-06-30_10000/
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
# Get allocations using portfolio configuration
python3 scripts/get_allocations.py --portfolio-config

# Get allocations for multiple strategies with portfolio percentages
python3 scripts/get_allocations.py qqq_sma_50:60 qqq_sma_50_gradient:40

# Single strategy
python3 scripts/get_allocations.py qqq:100
```

**Arguments**:

- `--portfolio-config`: Use portfolio configuration from `portfolio_configs/current_portfolio.json`
- `strategy:percentage`: Strategy name and portfolio percentage (required when not using --portfolio-config, multiple allowed)

**Outputs**: Formatted table showing individual strategy allocations and final portfolio allocation

#### Weekly TQQQ Hedged-DCA Action Card

**Purpose**: A standalone, low-touch weekly tool for a simplified two-pillar take on leveraged-ETF accumulation: a throttled DCA into TQQQ plus an exposure-ramped protective-put hedge. It prints a once-a-week "action card" telling you how much TQQQ to buy and whether to buy or roll a protective put. It is meant to be run on a weekly cadence and acted on by hand in a few minutes.

**Standalone**: Unlike the simulation and allocation tools above, this script needs no virtual environment, no `requirements.txt`, and no Polygon.io key. It uses only the Python standard library plus the free Yahoo Finance chart API.

**Command**:

```bash
python3 scripts/action_card.py
```

**How it works**:

- Pulls QQQ and TQQQ prices and QQQ's 200-day SMA from Yahoo Finance.
- Throttles the weekly buy by how far QQQ sits from its 200-day SMA (buy more on dips, less when extended).
- Sizes the protective-put hedge by exposure: 0% coverage while TQQQ is under half your cash reserve, ramping linearly to a 50% coverage cap as TQQQ grows to match and then exceed the reserve.
- Reads your current position (shares, reserve, puts) from a state file and prints the recommended actions.

**State file**: Reads `tqqq-state.json` from `$TQQQ_VAULT` (default `~/Nexus/`). This file holds your real position and is intentionally git-ignored, so it is never committed. Point `TQQQ_VAULT` elsewhere on other machines.

**Configuration**: Edit the `CONFIG` block at the top of the script (base weekly amount, throttled vs flat, hedge ramp thresholds, put tenor and roll rule).

**Read-only**: The script never places a trade. It only prints recommendations; you place every order yourself.

**Example output**:

```
=== TQQQ Action Card  2026-06-22 ===
QQQ $740.62 | 200d SMA $628.63 | +17.8% vs SMA  ->  Tier: Extended (0.5x)
TQQQ $82.87

1) DCA  : Buy $250 of TQQQ  ~=  3 shares @ $82.87  (= $249)
2) HEDGE: No position yet -> initiate when ready; no hedge needed.

Reserve after buy: $99751
(Recommendation only. Place trades yourself, then reply with what you did.)
```

#### Portfolio Rebalancing Calculator

**Purpose**: Mobile-friendly calculator to determine buy/sell amounts for portfolio rebalancing

**Location**: `portfolio-calculator/index.html` (can be deployed to GitHub Pages)

**Features**:

- Copy/paste allocations directly from daily emails
- Input current holdings in dollars
- Calculates exact trade amounts needed
- Shows final expected portfolio balances
- Mobile-optimized interface
- Works offline once loaded

**Usage**:

1. Open `portfolio-calculator/index.html` in browser or deploy to GitHub Pages
2. Copy allocation block from daily email
3. Paste into "Copy from Email" section
4. Input current dollar holdings
5. Click "Calculate Rebalancing"

#### Automated Daily Emails

**Purpose**: Get daily portfolio allocation emails automatically via GitHub Actions

**Setup**: Follow `GitHub_Actions_Email_Setup.md` for complete instructions

**Features**:

- Runs Monday-Friday at NYSE open (9:30 AM ET)
- Emails personalized allocation recommendations
- Completely free using GitHub Actions
- Configurable strategies and recipients

#### Data Management

**Import Data**: Use `scripts/dataset_importer.py` programmatically or manually place CSV files in `data/real_tickers/`

**Backfill Data**: Use `src/data_manager.py` programmatically to update historical data via Polygon.io API

### Python API Usage

All components can also be used programmatically in Python:

```python
# Import from the northbound package
from northbound import Backtester, PerformanceVisualizer, backfill_all_tickers

# Dataset importing (from scripts)
from scripts.dataset_importer import import_single_dataset
import_single_dataset("/path/to/data.csv", "TICKER", "data")

# Backtesting
backtester = Backtester("strategy_configs/strategy.json")
results = backtester.run_simulation(start_date="2018-01-01")
backtester.save_results(results, "results.csv")

# Data backfilling
backfill_all_tickers("data")

# Visualization
viz = PerformanceVisualizer()
viz.compare_strategies(["results.csv"], "data/real_tickers/SPY.csv")
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
