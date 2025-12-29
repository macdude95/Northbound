import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from polygon import RESTClient
import sqlite3

# Load environment variables
load_dotenv()
API_KEY = os.getenv("POLYGON_API_KEY")


def fetch_and_store_aggregates(ticker, start_date_str=None, days=None):
    if not API_KEY:
        print("Error: POLYGON_API_KEY not found in .env file")
        return

    # Initialize Polygon client
    client = RESTClient(API_KEY)

    # Calculate date range
    end_date = datetime.now()
    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    elif days:
        start_date = end_date - timedelta(days=days)
    else:
        # Default to last 30 days for regular updates
        start_date = end_date - timedelta(days=30)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    try:
        # Fetch aggregates (1 day bars)
        aggs = client.get_aggs(
            ticker=ticker.upper(),
            multiplier=1,
            timespan="day",
            from_=start_str,
            to=end_str,
        )

        if not aggs:
            print(f"No data found for {ticker}")
            return

        # Connect to database
        conn = sqlite3.connect("stocks.db")
        cursor = conn.cursor()

        # Insert data (skip duplicates due to UNIQUE constraint)
        inserted_count = 0
        for agg in aggs:
            date_str = datetime.fromtimestamp(agg.timestamp / 1000).strftime("%Y-%m-%d")

            try:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO aggregates
                    (ticker, date, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        ticker.upper(),
                        date_str,
                        agg.open,
                        agg.high,
                        agg.low,
                        agg.close,
                        agg.volume,
                    ),
                )
                if cursor.rowcount > 0:
                    inserted_count += 1
            except sqlite3.Error as e:
                print(f"Error inserting data for {date_str}: {e}")

        conn.commit()
        conn.close()

        print(f"Successfully inserted {inserted_count} new records for {ticker}")

    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python stock_fetcher.py <TICKER> [START_DATE]")
        print("START_DATE format: YYYY-MM-DD (optional, defaults to last 30 days)")
        sys.exit(1)

    ticker = sys.argv[1]
    start_date = sys.argv[2] if len(sys.argv) == 3 else None
    fetch_and_store_aggregates(ticker, start_date_str=start_date)


if __name__ == "__main__":
    main()
