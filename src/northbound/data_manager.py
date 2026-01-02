#!/usr/bin/env python3
"""
Data management utilities for the trading suite.
Handles data backfilling using Polygon.io API.
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")


class PolygonClient:
    """Client for Polygon.io API using official SDK."""

    def __init__(self, api_key: str):
        try:
            from polygon import RESTClient

            self.client = RESTClient(api_key)
        except ImportError:
            raise ImportError(
                "polygon-api-client package required. Install with: pip install polygon-api-client"
            )

    def get_aggregates(
        self,
        ticker: str,
        from_date: str,
        to_date: str,
        multiplier: int = 1,
        timespan: str = "day",
    ) -> pd.DataFrame:
        """
        Get aggregate bars for a ticker using Polygon SDK.

        Args:
            ticker: Stock symbol
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            multiplier: Size of the timespan multiplier
            timespan: Size of the time window (day, hour, minute, etc.)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Use Polygon SDK to get aggregates
            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=from_date,
                to=to_date,
                limit=50000,  # Get plenty of data
            )

            # Convert to DataFrame
            data = []
            for agg in aggs:
                data.append(
                    {
                        "Date": pd.Timestamp.fromtimestamp(
                            agg.timestamp / 1000
                        ).strftime(
                            "%Y-%m-%d"
                        ),  # Convert from milliseconds
                        "Open": agg.open,
                        "High": agg.high,
                        "Low": agg.low,
                        "Close": agg.close,
                        "Volume": agg.volume,
                    }
                )

            df = pd.DataFrame(data)
            if df.empty:
                print(f"No data returned from Polygon API for {ticker}")
                return pd.DataFrame()

            return df

        except Exception as e:
            error_msg = str(e)
            if "NOT_AUTHORIZED" in error_msg and "plan doesn't include" in error_msg:
                print(
                    f"❌ Polygon.io Free Tier Limitation: Historical aggregates data requires a paid plan"
                )
                print(f"   Upgrade at: https://polygon.io/pricing")
                print(
                    f"   For free historical data, use manual downloads from investing.com"
                )
            else:
                print(f"Error fetching aggregates for {ticker}: {e}")
            return pd.DataFrame()


def update_ticker_data(
    ticker: str, existing_csv_path: str, client: PolygonClient
) -> bool:
    """
    Update ticker data with recent data from Polygon API (free tier compatible).
    Fetches recent data (last 2 years) instead of trying to backfill old historical data.

    Args:
        ticker: Stock symbol to update
        existing_csv_path: Path to existing CSV file
        client: Polygon API client

    Returns:
        True if successful, False otherwise
    """
    # For free tier, fetch recent data (last 2 years) instead of trying to backfill
    # This avoids the historical data limitation
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years back

    from_date = start_date.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")

    print(f"Fetching recent {ticker} data from {from_date} to {to_date}")

    try:
        new_data = client.get_aggregates(ticker, from_date, to_date)

        if new_data.empty:
            print(f"No data available for {ticker}")
            return True

        # Load existing data if it exists
        if os.path.exists(existing_csv_path):
            existing_df = pd.read_csv(existing_csv_path)
            # Combine with new data
            combined_df = pd.concat([existing_df, new_data], ignore_index=True)
        else:
            combined_df = new_data

        # Remove duplicates and sort
        combined_df = combined_df.drop_duplicates(subset=["Date"], keep="last")
        combined_df = combined_df.sort_values("Date").reset_index(drop=True)

        # Save back to CSV
        combined_df.to_csv(existing_csv_path, index=False)
        print(f"Updated {ticker} with {len(new_data)} recent rows")

        return True

    except Exception as e:
        error_msg = str(e)
        if "NOT_AUTHORIZED" in error_msg and "plan doesn't include" in error_msg:
            print(
                f"❌ Polygon.io Free Tier Limitation: Historical aggregates data requires a paid plan"
            )
            print(f"   The free tier only supports recent data (last 2 years)")
            print(f"   Current data is sufficient for backtesting 2025")
        else:
            print(f"Error updating {ticker}: {e}")
        return False


def check_data_gaps(ticker: str, csv_path: str) -> tuple[bool, str]:
    """
    Check for gaps between existing data and API availability.

    Returns:
        (has_gap, message)
    """
    if not os.path.exists(csv_path):
        return True, f"CSV file for {ticker} does not exist."

    df = pd.read_csv(csv_path)
    if df.empty:
        return True, f"CSV file for {ticker} is empty."

    last_date = datetime.strptime(df["Date"].max(), "%Y-%m-%d")

    # Check if we can get recent data from Polygon (free tier compatible)
    client = PolygonClient(POLYGON_API_KEY)
    try:
        # Test with recent dates that free tier supports
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days

        test_data = client.get_aggregates(
            ticker,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            multiplier=1,
            timespan="day",
        )
        if test_data.empty:
            return (
                True,
                f"Unable to retrieve recent data for {ticker} from Polygon API. Manual download required from https://www.investing.com/",
            )
    except Exception as e:
        return (
            True,
            f"Error accessing Polygon API for {ticker}: {e}. Manual download required from https://www.investing.com/",
        )

    return False, ""


def backfill_all_tickers(data_dir: str, tickers: list[str] = None) -> None:
    """
    Backfill all tickers in the data directory.

    Args:
        data_dir: Path to data directory
        tickers: List of tickers to backfill (if None, finds all CSV files)
    """
    if not POLYGON_API_KEY:
        print("Error: POLYGON_API_KEY not found in environment variables")
        return

    client = PolygonClient(POLYGON_API_KEY)

    real_tickers_dir = os.path.join(data_dir, "real_tickers")

    if tickers is None:
        # Find all CSV files
        if os.path.exists(real_tickers_dir):
            tickers = [
                f.replace(".csv", "")
                for f in os.listdir(real_tickers_dir)
                if f.endswith(".csv")
            ]
        else:
            print(f"Directory {real_tickers_dir} does not exist")
            return

    for ticker in tickers:
        csv_path = os.path.join(real_tickers_dir, f"{ticker}.csv")

        # Check for gaps first
        has_gap, message = check_data_gaps(ticker, csv_path)
        if has_gap:
            print(f"Gap detected for {ticker}: {message}")
            continue

        # Update with recent data
        success = update_ticker_data(ticker, csv_path, client)
        if not success:
            print(f"Failed to update {ticker}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Backfill historical data using Polygon.io API"
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default="data",
        help="Path to data directory (default: data)",
    )
    parser.add_argument(
        "--tickers", nargs="*", help="Specific tickers to backfill (default: all)"
    )

    args = parser.parse_args()

    backfill_all_tickers(args.data_dir, args.tickers)
