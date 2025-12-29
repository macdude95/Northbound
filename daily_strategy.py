#!/usr/bin/env python3
"""
Daily 50-Day MA Strategy Calculator
Run this script daily to get TQQQ/SQQQ allocation instructions.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
import sys
import os


def get_qqq_data(days=60):
    """Fetch QQQ historical data from Yahoo Finance."""
    try:
        qqq = yf.Ticker("QQQ")
        # Get data for the last 60 trading days (to calculate 50-day MA)
        end_date = datetime.now()
        start_date = end_date - timedelta(
            days=days * 2
        )  # Extra days for weekends/holidays

        data = qqq.history(start=start_date, end=end_date, interval="1d")
        return data
    except Exception as e:
        print(f"Error fetching QQQ data from Yahoo Finance: {e}")
        print("Falling back to local database...")
        return get_qqq_data_from_db()


def get_qqq_data_from_db():
    """Fallback: Get QQQ data from local database."""
    try:
        db_path = "stocks.db"
        if not os.path.exists(db_path):
            print("Error: stocks.db not found. Please run data collection first.")
            sys.exit(1)

        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(
            "SELECT date, close FROM aggregates WHERE ticker='QQQ' ORDER BY date DESC LIMIT 60",
            conn,
        )
        conn.close()

        if df.empty:
            print("Error: No QQQ data in database.")
            sys.exit(1)

        # Convert to format expected by calculation
        df["Date"] = pd.to_datetime(df["date"])
        df.set_index("Date", inplace=True)
        df = df.rename(columns={"close": "Close"})
        return df.sort_index()
    except Exception as e:
        print(f"Error reading from database: {e}")
        sys.exit(1)


def calculate_target_allocation(qqq_data):
    """Calculate target TQQQ/SQQQ allocation based on 50-day MA strategy."""
    try:
        # Calculate 50-day moving average using CLOSING prices
        ma_50 = qqq_data["Close"].rolling(window=50, min_periods=50).mean()

        # Get latest data (using CLOSING price)
        current_price = qqq_data["Close"].iloc[-1]
        current_ma = ma_50.iloc[-1]

        if pd.isna(current_ma):
            print("Warning: Not enough data for 50-day MA calculation.")
            print("Need at least 50 trading days of data.")
            return None, None

        # Calculate deviation
        deviation_pct = (current_price - current_ma) / current_ma

        # Determine allocation based on strategy rules
        if deviation_pct > 0.05:
            tqqq_allocation = 1.0
            sqqq_allocation = 0.0
            strategy = "Strong Bull (100% TQQQ)"
        elif deviation_pct < -0.05:
            tqqq_allocation = 0.0
            sqqq_allocation = 1.0
            strategy = "Strong Bear (100% SQQQ)"
        else:
            # Linear interpolation between -5% and +5%
            tqqq_allocation = 0.5 + (deviation_pct / 0.05) * 0.5
            sqqq_allocation = 1.0 - tqqq_allocation
            strategy = "Neutral Zone"

        return {
            "tqqq_pct": tqqq_allocation,
            "sqqq_pct": sqqq_allocation,
            "strategy": strategy,
            "current_price": current_price,
            "ma_50": current_ma,
            "deviation_pct": deviation_pct,
        }, qqq_data

    except Exception as e:
        print(f"Error calculating allocation: {e}")
        return None, None


def get_current_positions():
    """Optionally get current positions from user input."""
    print("\n" + "=" * 50)
    print("CURRENT POSITION INPUT (Optional)")
    print("=" * 50)

    try:
        total_value = input(
            "Enter your current total portfolio value for this strategy (or press Enter to skip): "
        ).strip()
        if not total_value:
            return None

        total_value = float(total_value)

        tqqq_value = input("Enter current TQQQ position value (or 0): ").strip()
        tqqq_value = float(tqqq_value) if tqqq_value else 0.0

        sqqq_value = input("Enter current SQQQ position value (or 0): ").strip()
        sqqq_value = float(sqqq_value) if sqqq_value else 0.0

        cash = total_value - tqqq_value - sqqq_value

        return {
            "total_value": total_value,
            "tqqq_value": tqqq_value,
            "sqqq_value": sqqq_value,
            "cash": cash,
            "tqqq_pct": tqqq_value / total_value if total_value > 0 else 0,
            "sqqq_pct": sqqq_value / total_value if total_value > 0 else 0,
        }

    except ValueError as e:
        print(f"Invalid input: {e}")
        return None


def generate_trading_instructions(allocation, current_positions=None):
    """Generate specific buy/sell instructions."""
    if not allocation or not current_positions:
        return None

    print("\n" + "=" * 50)
    print("TRADING INSTRUCTIONS")
    print("=" * 50)

    total_value = current_positions["total_value"]
    target_tqqq = allocation["tqqq_pct"] * total_value
    target_sqqq = allocation["sqqq_pct"] * total_value

    current_tqqq = current_positions["tqqq_value"]
    current_sqqq = current_positions["sqqq_value"]
    current_tqqq_pct = current_positions["tqqq_pct"]
    current_sqqq_pct = current_positions["sqqq_pct"]

    # Calculate trades needed
    tqqq_trade = target_tqqq - current_tqqq
    sqqq_trade = target_sqqq - current_sqqq

    print(f"Total Portfolio Value: ${total_value:,.2f}")
    print(f"Current TQQQ: {current_tqqq_pct:.1%} (${current_tqqq:,.2f})")
    print(f"Current SQQQ: {current_sqqq_pct:.1%} (${current_sqqq:,.2f})")

    print("\nRequired Trades:")
    if abs(tqqq_trade) > 1:  # Only show if difference > $1
        action = "BUY" if tqqq_trade > 0 else "SELL"
        print(f"TQQQ: {action} ${abs(tqqq_trade):,.2f}")

    if abs(sqqq_trade) > 1:  # Only show if difference > $1
        action = "BUY" if sqqq_trade > 0 else "SELL"
        print(f"SQQQ: {action} ${abs(sqqq_trade):,.2f}")

    # Check if rebalancing is needed
    rebalance_threshold = 0.02  # 2% threshold
    current_tqqq_pct = current_positions["tqqq_pct"]
    current_sqqq_pct = current_positions["sqqq_pct"]

    tqqq_diff = abs(current_tqqq_pct - allocation["tqqq_pct"])
    sqqq_diff = abs(current_sqqq_pct - allocation["sqqq_pct"])

    if tqqq_diff < rebalance_threshold and sqqq_diff < rebalance_threshold:
        print("\n✅ NO TRADING NEEDED - Current allocation is within 2% of target")
    else:
        print("\n⚠️  REBALANCING RECOMMENDED - Execute the trades above")

    return {
        "tqqq_trade": tqqq_trade,
        "sqqq_trade": sqqq_trade,
        "target_tqqq": target_tqqq,
        "target_sqqq": target_sqqq,
    }


def main():
    print("🚀 Daily 50-Day MA Strategy Calculator")
    print("=" * 50)

    # Get QQQ data
    print("📊 Fetching QQQ data...")
    qqq_data = get_qqq_data()

    if qqq_data.empty:
        print("❌ Error: Could not fetch QQQ data.")
        sys.exit(1)

    print(f"✅ Retrieved {len(qqq_data)} days of QQQ data")
    print(f"Latest QQQ Price: ${qqq_data['Close'].iloc[-1]:.2f}")

    # Calculate target allocation
    print("\n🧮 Calculating target allocation...")
    allocation, qqq_data = calculate_target_allocation(qqq_data)

    if not allocation:
        print("❌ Error: Could not calculate allocation.")
        sys.exit(1)

    # Display results
    print("\n" + "=" * 50)
    print("STRATEGY RESULTS")
    print("=" * 50)
    print(f"QQQ Price: ${allocation['current_price']:.2f}")
    print(f"50-Day MA: ${allocation['ma_50']:.2f}")
    print(f"Deviation from MA: {allocation['deviation_pct']:.1%}")
    print(f"Strategy Signal: {allocation['strategy']}")

    print("\nTarget Allocation:")
    print(f"TQQQ: {allocation['tqqq_pct']:.1%}")
    print(f"SQQQ: {allocation['sqqq_pct']:.1%}")

    # Get current positions and generate instructions
    current_positions = get_current_positions()
    if current_positions:
        generate_trading_instructions(allocation, current_positions)

    # Summary
    print("\n" + "=" * 50)
    print("DAILY SUMMARY")
    print("=" * 50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"QQQ Price: ${allocation['current_price']:.2f}")
    print(f"50-Day MA: ${allocation['ma_50']:.2f}")
    print(f"Deviation: {allocation['deviation_pct']:.1%}")
    print(
        f"Target: {allocation['tqqq_pct']:.1%} TQQQ / {allocation['sqqq_pct']:.1%} SQQQ"
    )

    print("\n💡 Remember:")
    print("• Only trade if allocation differs by more than 2-3%")
    print("• Consider transaction costs ($0-5 per trade)")
    print("• This is not financial advice - DYOR!")


if __name__ == "__main__":
    # Check if yfinance is available
    try:
        import yfinance as yf
    except ImportError:
        print("❌ Error: yfinance not installed.")
        print("Install with: pip install yfinance")
        sys.exit(1)

    main()
