# Trading Tools and Datasets Suite Technical Design

## Architecture Overview

The suite consists of four main components: datasets management, strategy configuration, backtesting simulator, and performance visualizer. All components operate on CSV data files and JSON configuration files.

## System Architecture

```
External Data Sources ──► Downloads/Files ──► Polygon.io API
(investing.com CSVs)       (*.csv)             (for backfilling)
       │                        │                        │
       ▼                        ▼                        ▼
dataset_importer.py ──────────────────────────────────► data_manager.py
• Import/clean        datasets/real_tickers/           • Backfill API
• Format convert      *.csv                            • Gap detection
• ~/Downloads                                           • Rate limiting
       │                                                      │
       ▼                                                      ▼
datasets/real_tickers/ ◄── configs/*.json ───► run_simulation.py
*.csv (initial)             (strategy configs)    • Main interface
                                                  • Orchestrates backtesting
                                                  • Generates visualizations
                                                         │
                                                         ▼
                                    ┌─────────────────┬─────────────────┐
                                    │                 │                 │
                                    ▼                 ▼                 ▼
                            datasets/strategy_allocations/ datasets/simulations/ visualizer.py
                            *.csv (allocations)  {date}_{capital}/      • Plotly charts
                                               ├── *.csv (P&L)      • Comparisons
                                               └── *.html           • Interactive
```

## Component Interactions

### Data Flow:

1. **dataset_importer.py** → `datasets/real_tickers/` (initial data import)
2. **data_manager.py** → `datasets/real_tickers/` (data updates)
3. **run_simulation.py** ← `configs/` + `datasets/real_tickers/`
4. **run_simulation.py** → calls `backtester.py` → `datasets/strategy_allocations/` + `datasets/simulations/`
5. **run_simulation.py** → calls `visualizer.py` → saves HTML in simulation subfolders

### Dependencies:

- **dataset_importer**: Reads from `~/Downloads/`, writes to `datasets/real_tickers/`
- **data_manager**: Requires Polygon.io API key, updates `datasets/real_tickers/`
- **run_simulation.py**: Main orchestrator, calls backtester and visualizer classes
- **backtester.py**: Core backtesting engine (no CLI)
- **visualizer.py**: Chart generation engine (no CLI)

## Data Formats

### CSV Data Files

- **Real Ticker CSVs**: Standard OHLCV format
  - Columns: Date, Open, High, Low, Close, Volume
  - Date format: YYYY-MM-DD
- **Strategy Performance CSVs**:
  - Columns: Date, Strategy_Value, Allocation_JSON, Actions
  - Allocation_JSON: JSON string of allocation percentages
  - Actions: Description of trades/rebalancing performed

### JSON Configuration Files

- **Strategy Config Schema**:

```json
{
  "name": "string",
  "underlying_symbol": "string",
  "calculation": {
    "type": "SMA",
    "period": number
  },
  "rules": [
    {
      "max_threshold?": number,
      "min_threshold?": number,
      "ticker?": "string" | "cash",
      "ticker_min?": "string" | "cash",
      "ticker_max?": "string" | "cash",
      "scaling_function?": "linear"
    }
  ]
}
```

## Folder Structure

```
project/
├── datasets/
│   ├── real_tickers/
│   │   ├── AAPL.csv
│   │   └── QQQ.csv
│   ├── strategy_allocations/
│   │   ├── strategy1.csv
│   │   └── strategy2.csv
│   └── simulations/
│       ├── 2020-01-01_2025-12-31_10000/
│       │   ├── strategy1.csv
│       │   ├── strategy2.csv
│       │   └── strategy_comparison.html
│       └── 2020-06-01_2025-06-30_10000/
│           └── ...
├── scripts/                 # CLI scripts (separated from library)
│   ├── run_simulation.py    # Main CLI interface
│   └── dataset_importer.py  # Data import CLI
├── src/northbound/          # Library package
│   ├── __init__.py          # Package exports
│   ├── backtester.py        # Core backtesting logic
│   ├── visualizer.py        # Chart generation
│   └── data_manager.py      # API integration
├── strategy_configs/
│   ├── strategy1.json
│   └── strategy2.json
├── docs/
└── README.md
```

## Component Specifications

### Backtester Validation

The backtester performs comprehensive config validation before execution:

- **Required Fields**: Checks for name, underlying_symbol, calculation, rules
- **Calculation Support**: Validates indicator types (SMA only currently)
- **Ticker Existence**: Verifies underlying symbol and all traded tickers exist in datasets
- **Scaling Functions**: Ensures scaling_function is supported (linear only)
- **Threshold Coverage**: Rules must provide complete coverage with no gaps
- **Explicit Cash**: Cash must be explicitly allocated in at least one rule

Invalid configs produce clear error messages to help users fix issues.

### 1. Data Manager

- **Backfilling Logic**:
  - Compare last date in CSV with current date
  - Call Polygon API for missing dates
  - Handle API pagination and rate limits
  - Detect gaps and prompt for manual data when API insufficient
- **Data Validation**:
  - Verify CSV headers match expected format
  - Check date continuity and sorting
  - Validate numeric data types

### 2. Strategy Engine

- **Indicator Calculations**:
  - SMA: Rolling average of close prices over specified period
  - Future: RSI, MACD, etc.
- **Rule Evaluation**:
  - Calculate deviation: (current_price - indicator) / indicator
  - Match against thresholds in rule order
  - For between rules: interpolate allocations using configurable scaling functions
- **Allocation Processing**:
  - Parse allocation objects into portfolio weights
  - Handle cash as implicit remainder to 100%

### 3. Backtesting Simulator

- **Execution Flow**:
  1. Load config and validate
  2. Load required CSV data (underlying + allocation tickers)
  3. Calculate strategy allocations over full available data range
  4. Filter for simulation date range and initialize portfolio
  5. For each date in simulation range:
     - Get allocation from pre-calculated strategy results
     - Rebalance portfolio to match target allocation
     - Record portfolio value and state
  6. Export strategy allocations (full range) to strategy_allocations/ CSV
  7. Export portfolio simulation results (specified range) to simulations/ CSV
- **Data Separation**:
  - Strategy CSVs: Date, Allocation (decisions over full available data)
  - Simulation CSVs: Date, Portfolio_Value, Cash, Positions (state for specific parameters)
  - Simulation filenames: `{strategy}_{start_date}_{end_date}_{capital}.csv`
- **Rebalancing Logic**:
  - Calculate current vs target positions
  - Execute trades assuming perfect fills
  - Update cash and holdings
  - Track transaction costs (initially zero)

### 4. Visualizer

- **Chart Generation**:
  - Use matplotlib/plotly for interactive charts
  - Normalize starting values for comparison
  - Support date range filtering
- **Data Loading**:
  - Read multiple CSVs simultaneously
  - Handle missing dates gracefully
  - Calculate percentage returns

## API Integration

### Polygon.io API

- **Endpoints Used**:
  - Historical aggregates: `/v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`
  - Daily bars: multiplier=1, timespan=day
- **Authentication**: API key via environment variable
- **Rate Limiting**: Handle 429 responses with exponential backoff
- **Data Mapping**: Convert API response to CSV format

## Error Handling

- **Config Validation**: JSON schema validation for configs
- **Data Validation**: Check CSV integrity and date ranges
- **API Errors**: Retry logic with user notifications
- **Simulation Errors**: Log issues without stopping execution

## Performance Considerations

- **Memory Usage**: Load only required date ranges
- **Processing Speed**: Vectorized calculations where possible
- **Scalability**: Support for large datasets (1000+ days, multiple tickers)
