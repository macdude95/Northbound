import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime


def visualize_qqq():
    # Connect to database
    conn = sqlite3.connect("stocks.db")
    cursor = conn.cursor()

    # Query QQQ data
    cursor.execute(
        """
        SELECT date, close
        FROM aggregates
        WHERE ticker = 'QQQ'
        ORDER BY date
    """
    )

    data = cursor.fetchall()
    conn.close()

    if not data:
        print("No QQQ data found in database.")
        return

    # Extract dates and prices
    dates = []
    prices = []
    for row in data:
        date_str, price = row
        # Convert date string to datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        dates.append(date_obj)
        prices.append(price)

    # Create the plot
    plt.figure(figsize=(12, 6))
    plt.plot(dates, prices, linewidth=1, color="blue")
    plt.title("QQQ Stock Price Over Time")
    plt.xlabel("Date")
    plt.ylabel("Close Price ($)")
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Show the plot
    plt.show()


if __name__ == "__main__":
    visualize_qqq()
