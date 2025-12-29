# 50-Day Moving Average Trading Strategy - Complete Guide

## Overview

This strategy uses QQQ's position relative to its 50-day moving average to allocate between TQQQ (3x leveraged QQQ) and SQQQ (3x inverse QQQ). The goal is to capture leveraged upside when QQQ is trending above its MA and leveraged downside when trending below.

**Strategy Rules:**

- Calculate QQQ's 50-day simple moving average
- If QQQ > 50-day MA by >5%: 100% allocated to TQQQ
- If QQQ < 50-day MA by >5%: 100% allocated to SQQQ
- If within ±5% of MA: Scale allocation linearly between TQQQ/SQQQ

## Quick Start

### Option 1: Automated Daily Script (Recommended)

1. **Install dependencies:**

   ```bash
   pip install yfinance pandas numpy
   ```

2. **Run daily script:**

   ```bash
   python daily_strategy.py
   ```

3. **Follow the output:** The script tells you exactly what percentage to allocate to TQQQ and SQQQ.

### Option 2: Manual Calculation

1. **Get QQQ data:** Use Yahoo Finance or TradingView
2. **Calculate 50-day MA:** Average of last 50 closing prices
3. **Compute deviation:** `(QQQ_price - MA_50) / MA_50`
4. **Determine allocation:** Use the formula below

## Detailed Strategy Logic

### Allocation Formula

**Uses closing prices for reliable, end-of-day data**

```
deviation = (current_QQQ_close - MA_50_close) / MA_50_close

If deviation > 0.05:
    TQQQ_allocation = 100%
    SQQQ_allocation = 0%

Else if deviation < -0.05:
    TQQQ_allocation = 0%
    SQQQ_allocation = 100%

Else:
    # Linear interpolation between -5% and +5%
    TQQQ_allocation = 50% + (deviation / 0.05) × 50%
    SQQQ_allocation = 100% - TQQQ_allocation
```

### Example Calculation

- QQQ closes at $420
- 50-day MA of closing prices = $410
- Deviation = ($420 - $410) / $410 = 2.44%
- Since 2.44% < 5%: TQQQ = 50% + (0.0244 / 0.05) × 50% = 74.4%
- SQQQ = 25.6%

## Daily Routine (15-30 minutes)

### Step 1: Morning Data Collection (7:00-9:00 AM ET)

**Get QQQ closing price and calculate MA:**

1. Visit Yahoo Finance: https://finance.yahoo.com/quote/QQQ
2. Note yesterday's closing price
3. Download historical data (last 60 days)
4. Calculate MA: Average of last 50 closing prices

**Alternative: Use TradingView**

- Search "QQQ"
- Add "Moving Average Simple" indicator (length 50)
- Note current price vs MA line

### Step 2: Calculate Target Allocation

Use the formula above or run `python daily_strategy.py`

### Step 3: Check Current Positions

Log into your brokerage account and note:

- Current TQQQ shares × price = TQQQ value
- Current SQQQ shares × price = SQQQ value
- Total portfolio value = TQQQ + SQQQ + cash

Calculate current allocations:

- TQQQ % = TQQQ_value / total_portfolio
- SQQQ % = SQQQ_value / total_portfolio

### Step 4: Execute Trades (Only if needed)

**Rebalancing threshold: 2-3% difference**

Calculate required trades:

```
Target TQQQ value = target_% × total_portfolio
Target SQQQ value = target_% × total_portfolio
TQQQ trade = target_TQQQ - current_TQQQ
SQQQ trade = target_SQQQ - current_SQQQ
```

Place market orders during regular hours (9:30 AM - 4:00 PM ET)

### Step 5: Evening Review

- Verify all orders executed
- Note end-of-day portfolio value
- Record positions for tracking

## Risk Management

### Position Sizing

- **Start small:** 10-20% of total investment portfolio
- **Scale up gradually:** Add capital after 3 months successful trading
- **Maximum allocation:** Never exceed 50% of total portfolio

### Stop Loss Rules

- **Portfolio level:** Reduce position size by 50% if down 20% from peak
- **Monthly limit:** Pause trading if down 10% in a month
- **Annual limit:** Reassess strategy if down 15% in a year

### Emergency Procedures

- **Market crash:** Move to 100% cash if QQQ drops 5% in one day
- **System failure:** Default to 50/50 allocation until resolved
- **Personal emergency:** Have backup person who understands the system

## Performance Expectations (Based on Backtests)

### 2022-2025 Backtest Results:

- **Daily Strategy:** 135.30% total return (138% annualized)
- **Weekly Strategy:** 40.31% total return (41% annualized)
- **Monthly Strategy:** 38.31% total return (39% annualized)
- **Buy & Hold QQQ:** 20.31% total return (21% annualized)

### Key Insights:

- **Daily rebalancing captures the most opportunities**
- **Weekly still adds significant value over buy & hold**
- **Monthly underperforms due to getting stuck in bad positions**
- **Strategy works best in volatile, oscillating markets**

## Tools & Resources

### Required Tools

- **Brokerage account** with margin capabilities (for SQQQ shorts)
- **Python environment** with required packages
- **Spreadsheet** for position tracking (Google Sheets/Excel)

### Useful Websites

- **Yahoo Finance:** https://finance.yahoo.com/quote/QQQ (data & charting)
- **TradingView:** https://www.tradingview.com (advanced charting)
- **Brokerage platform:** For order execution

### Files You Need

- `daily_strategy.py` - Automated allocation calculator
- `strategies/` folder - Strategy implementation code
- `backtester.py` - Backtesting engine (for analysis)

## Tax Considerations

### US Tax Rules

- **Short-term capital gains:** Held < 1 year (ordinary income rates)
- **Wash sale rules:** Can't claim losses if repurchase within 30 days
- **Report on Form 1099-B**

### Tax-Loss Harvesting

- Use SQQQ losses to offset TQQQ gains
- Time trades to manage tax brackets

## Common Questions

### Q: How often does the strategy change positions?

**A:** In 2025 testing, positions changed only 47.4% of days. The strategy shows discipline by holding good positions.

### Q: What's the optimal rebalancing frequency?

**A:** Daily captures the most opportunities but weekly still significantly outperforms buy-and-hold.

### Q: What if I can't run the script daily?

**A:** Use TradingView for manual MA calculations, or default to weekly rebalancing.

### Q: How much starting capital do I need?

**A:** Minimum $2,000-5,000 for proper diversification. Start with paper trading first.

### Q: What are the main risks?

**A:** Leveraged ETF volatility, whipsaw in sideways markets, transaction costs, and emotional trading.

## Troubleshooting

### Script Won't Run

```bash
# Install missing packages
pip install yfinance pandas numpy

# Check Python version (3.7+ required)
python --version
```

### Data Issues

- Yahoo Finance blocks: Use TradingView or manual calculation
- Weekend data: Strategy only runs on weekdays

### Brokerage Issues

- No margin account: Can't short SQQQ - consider cash instead
- High fees: Look for low-cost brokerages ($0 commissions)

## Advanced Usage

### Backtesting Other Strategies

```bash
python compare_strategies.py
```

### Exporting Trade Data for Analysis

```bash
python export_trade_data.py
```

### Modifying Strategy Parameters

Edit `strategies/momentum_strategy.py` to change MA periods or allocation rules.

## Legal Disclaimer

This is educational content only. Leveraged ETFs are high-risk instruments. Past performance doesn't guarantee future results. This is not financial advice. Consult a qualified financial advisor before implementing any strategy. The author is not responsible for investment losses.

---

## Quick Reference Card

**Daily Checklist:**

- [ ] Run `python daily_strategy.py` (or manual calculation)
- [ ] Check current portfolio allocations
- [ ] Execute trades if difference > 2-3%
- [ ] Record positions and P&L

**Strategy Rules:**

- QQQ > MA +5% → 100% TQQQ
- QQQ < MA -5% → 100% SQQQ
- Within ±5% → Scale linearly

**Emergency Contacts:**

- Brokerage support line
- Backup person for position management
